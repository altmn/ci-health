"""Offline fixtures protect accounting, collection completeness and comparisons."""

import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/ci-health/scripts/ci_health.py"
SPEC = importlib.util.spec_from_file_location("ci_health", SCRIPT)
ci = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
END = START + timedelta(hours=1)


def run(identity=1, created=START, attempts=1, outcome="success"):
    return {"id": identity, "created_at": ci.iso(created), "updated_at": ci.iso(created + timedelta(minutes=5)),
            "run_attempt": attempts, "status": "completed", "conclusion": outcome,
            "path": ".github/workflows/ci.yml", "event": "pull_request", "head_sha": "a" * 40}


def job(identity=10, run_id=1, seconds=30, outcome="success", labels=None):
    return {"id": identity, "run_id": run_id, "name": "test", "status": "completed", "conclusion": outcome,
            "started_at": ci.iso(START), "completed_at": ci.iso(START + timedelta(seconds=seconds)) if seconds is not None else None,
            "labels": labels if labels is not None else ["ubuntu-latest"], "steps": []}


class FakeAPI:
    def __init__(self, runs=None, jobs=None, capped=False, changed=False):
        self.runs = runs if runs is not None else [run()]
        self.jobs = jobs if jobs is not None else {(1, 1): [job()]}
        self.capped, self.changed = capped, changed
        self.requests = []

    def get(self, endpoint, params):
        self.requests.append((endpoint, dict(params)))
        parts = endpoint.split("/")
        if parts[-1] == "runs":
            lower, upper = map(ci.timestamp, params["created"].split(".."))
            if self.capped and upper - lower >= timedelta(seconds=1):
                return {"total_count": 1000, "workflow_runs": []}
            rows = [item for item in self.runs if lower <= ci.timestamp(item["created_at"]) <= upper]
            page = params.get("page", 1)
            return {"total_count": len(rows), "workflow_runs": copy.deepcopy(rows[(page-1)*100:page*100])}
        run_id = int(parts[5])
        original = next(item for item in self.runs if item["id"] == run_id)
        if "attempts" in parts:
            attempt = int(parts[7])
            if parts[-1] == "jobs":
                rows = self.jobs[(run_id, attempt)]
                page = params.get("page", 1)
                return {"total_count": len(rows), "jobs": copy.deepcopy(rows[(page-1)*100:page*100])}
            return {**copy.deepcopy(original), "run_attempt": attempt}
        result = copy.deepcopy(original)
        if self.changed:
            result["run_attempt"] += 1
        return result


def manifest(complete=True):
    return {"schema": ci.CAPTURE_SCHEMA, "definitions": ci.DEFINITIONS, "cohort": ci.COHORT,
            "repository": "owner/repo", "host": "github.com", "complete": complete,
            "start_inclusive": ci.iso(START), "end_exclusive": ci.iso(END), "capture_finished_at": ci.iso(END),
            "counts": {"runs": 1, "attempts": 1, "physical_jobs": 1, "raw_responses": 0}, "issues": []}


def rates():
    return {"schema": "ci-health.rates/v1", "currency": "USD", "effective_date": "2026-01-01",
            "rates": [{"id": "linux", "labels_all": ["ubuntu-latest"], "per_minute": "0.01", "quantum_seconds": 60, "minimum_seconds": 0}]}


def report(seconds=30, identity=1, event="pull_request", rate=None, evidence=None):
    item = run(identity)
    item["event"] = event
    return ci.summarize(manifest(), {"runs": [item], "attempts": [item], "jobs": [job(10+identity, identity, seconds)]}, rate, evidence)


class CollectionTests(unittest.TestCase):
    def capture(self, api, start=START, end=END):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        output = Path(temporary.name) / "capture"
        result = ci.Collector(api, output, "owner/repo", start, end).execute()
        return output, result

    def test_collects_all_attempts_deduplicates_carried_success(self):
        api = FakeAPI([run(attempts=2)], {(1, 1): [job(10, seconds=30), job(11, seconds=20, outcome="failure")],
                                              (1, 2): [job(10, seconds=30), job(12, seconds=15)]})
        output, result = self.capture(api)
        self.assertTrue(result["complete"])
        self.assertEqual(result["counts"]["physical_jobs"], 3)
        loaded, data = ci.load_capture(output)
        self.assertEqual(data["jobs"][0]["observed_in_attempts"], [1, 2])
        summary = ci.summarize(loaded, data)
        self.assertEqual(summary["demand"]["total_runner_seconds"], 65)
        self.assertEqual(summary["counts"]["jobs_by_outcome"], {"success": 2, "failure": 1})

    def test_fetches_every_job_page(self):
        api = FakeAPI(jobs={(1, 1): [job(identity=i) for i in range(201)]})
        _, result = self.capture(api)
        self.assertTrue(result["complete"])
        self.assertEqual(result["counts"]["physical_jobs"], 201)
        self.assertEqual([params["page"] for endpoint, params in api.requests if endpoint.endswith("/jobs")], [1, 2, 3])

    def test_capped_search_is_split_and_half_open_end_excluded(self):
        rows = [run(identity, START + timedelta(seconds=identity % 2)) for identity in range(1, 1001)]
        rows.append(run(1001, START + timedelta(seconds=2)))
        api = FakeAPI(rows, capped=True)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "raw").mkdir()
            collector = ci.Collector(api, output, "owner/repo", START, START + timedelta(seconds=2))
            collector.run_window(collector.start, collector.end)
            self.assertEqual(len(collector.runs), 1000)
            self.assertNotIn(1001, collector.runs)

    def test_split_search_reconciles_known_parent_count(self):
        rows = [run(identity, START + timedelta(seconds=identity % 2)) for identity in range(1, 1001)]
        class DeletedBetweenReads(FakeAPI):
            def get(self, endpoint, params):
                result = super().get(endpoint, params)
                if endpoint.endswith("/runs") and result["total_count"] >= 1000:
                    self.runs.pop()
                return result
        api = DeletedBetweenReads(rows)
        _, result = self.capture(api, end=START + timedelta(seconds=2))
        self.assertFalse(result["complete"])
        self.assertIn("underflow", result["issues"][0]["detail"])

    def test_one_second_search_cap_fails_loudly(self):
        class Capped(FakeAPI):
            def get(self, endpoint, params):
                return {"total_count": 1000, "workflow_runs": []}
        output, result = self.capture(Capped(), end=START + timedelta(seconds=1))
        self.assertFalse(result["complete"])
        self.assertIn("capped", result["issues"][0]["detail"])
        self.assertTrue((output / "checksums.sha256").exists())

    def test_changed_attempt_count_marks_capture_incomplete(self):
        _, result = self.capture(FakeAPI(changed=True))
        self.assertFalse(result["complete"])
        self.assertIn("run_changed", [item["code"] for item in result["issues"]])

    def test_final_pass_detects_earlier_run_change_during_later_fetch(self):
        class LateChange(FakeAPI):
            def get(self, endpoint, params):
                result = super().get(endpoint, params)
                if endpoint.endswith("/runs/2/attempts/1/jobs"):
                    self.runs[0]["run_attempt"] = 2
                return result
        api = LateChange([run(), run(2)], {(1, 1): [job()], (2, 1): [job(20, 2)]})
        _, result = self.capture(api)
        self.assertFalse(result["complete"])
        self.assertEqual(len(result["run_rechecks"]), 2)
        self.assertTrue(all(item["observed_at"] for item in result["run_rechecks"]))
        self.assertIn("run_changed", [item["code"] for item in result["issues"]])

    def test_missing_execution_end_preserved(self):
        output, result = self.capture(FakeAPI(jobs={(1, 1): [job(seconds=None)]}))
        self.assertFalse(result["complete"])
        summary = ci.summarize(*ci.load_capture(output))
        self.assertIsNone(summary["demand"]["total_runner_seconds"])
        self.assertEqual(summary["demand"]["jobs_missing_duration"], 1)
        self.assertIsNone(summary["run_rows"][0]["runner_seconds"])

    def test_runnerless_skipped_placeholder_bypasses_interval_validation(self):
        for labels in ([], ["ubuntu-latest"]):
            with self.subTest(labels=labels):
                skipped = job(seconds=-1, outcome="skipped", labels=labels)
                skipped.update(runner_id=0, runner_name="")
                output, result = self.capture(FakeAPI(jobs={(1, 1): [skipped]}))
                self.assertTrue(result["complete"])
                loaded, data = ci.load_capture(output)
                self.assertEqual(data["jobs"][0]["completed_at"], skipped["completed_at"])
                summary = ci.summarize(loaded, data, rates())
                self.assertEqual(summary["demand"]["total_runner_seconds"], 0)
                self.assertEqual(summary["demand"]["jobs_missing_duration"], 0)
                self.assertEqual(summary["run_rows"][0]["executed_jobs"], 0)
                self.assertEqual(summary["job_duration_seconds_by_outcome"]["skipped"]["n"], 0)
                self.assertEqual(summary["cost"]["total_estimated_cost"], 0)

    def test_skipped_step_placeholder_has_no_execution_interval(self):
        executed = job()
        executed["steps"] = [{"name": "conditional", "status": "completed", "conclusion": "skipped",
                              "started_at": ci.iso(START), "completed_at": ci.iso(START - timedelta(seconds=1))}]
        output, result = self.capture(FakeAPI(jobs={(1, 1): [executed]}))
        self.assertTrue(result["complete"])
        summary = ci.summarize(*ci.load_capture(output))
        self.assertEqual(summary["demand"]["total_runner_seconds"], 30)
        self.assertEqual(summary["counts"]["steps_by_outcome"], {"skipped": 1})
        self.assertEqual(summary["step_duration_seconds_by_outcome"]["skipped"]["n"], 0)

    def test_negative_executed_intervals_are_rejected_without_clamping(self):
        for negative_step in (False, True):
            with self.subTest(negative_step=negative_step):
                executed = job(seconds=30 if negative_step else -1)
                if negative_step:
                    executed["steps"] = [{"name": "test", "status": "completed", "conclusion": "success",
                                          "started_at": ci.iso(START), "completed_at": ci.iso(START - timedelta(seconds=1))}]
                output, result = self.capture(FakeAPI(jobs={(1, 1): [executed]}))
                self.assertFalse(result["complete"])
                self.assertIn("Negative execution duration", result["issues"][0]["detail"])
                with self.assertRaisesRegex(ci.MeasurementError, "Negative execution duration"):
                    ci.load_capture(output)

    def test_skipped_job_with_runner_or_steps_is_not_silently_free(self):
        evidence = ({"runner_id": 7}, {"runner_name": "allocated-runner"},
                    {"steps": [{"name": "conditional", "conclusion": "skipped"}]},
                    {"steps": [{"name": "test", "conclusion": "success"}]})
        for fields in evidence:
            with self.subTest(fields=fields):
                skipped = {**job(seconds=0, outcome="skipped"), **fields}
                output, result = self.capture(FakeAPI(jobs={(1, 1): [skipped]}))
                self.assertFalse(result["complete"])
                with self.assertRaisesRegex(ci.MeasurementError, "Skipped job"):
                    ci.load_capture(output)
                with self.assertRaisesRegex(ci.MeasurementError, "Skipped job"):
                    ci.price_job(skipped, rates())

    def test_skipped_step_still_requires_an_object(self):
        executed = job()
        executed["steps"] = ["skipped"]
        output, result = self.capture(FakeAPI(jobs={(1, 1): [executed]}))
        self.assertFalse(result["complete"])
        with self.assertRaisesRegex(ci.MeasurementError, "Invalid step record"):
            ci.load_capture(output)

    def test_partial_pagination_fails_loudly(self):
        class Partial(FakeAPI):
            def get(self, endpoint, params):
                response = super().get(endpoint, params)
                if endpoint.endswith("/jobs"):
                    response["total_count"] += 1
                return response
        _, result = self.capture(Partial())
        self.assertFalse(result["complete"])
        self.assertIn("pagination", result["issues"][0]["detail"])

    def test_malformed_api_records_finalize_incomplete_capture(self):
        for field in ("workflow_runs", "jobs"):
            for invalid in (None, [], "record", {"id": []}):
                with self.subTest(field=field, invalid=invalid):
                    class Malformed(FakeAPI):
                        def get(self, endpoint, params):
                            body = super().get(endpoint, params)
                            if field in body:
                                return {"total_count": 1, field: [invalid]}
                            return body
                    output, result = self.capture(Malformed())
                    self.assertFalse(result["complete"])
                    self.assertIn("collection_error", [item["code"] for item in result["issues"]])
                    loaded, _ = ci.load_capture(output)
                    self.assertFalse(loaded["complete"])
                    self.assertGreater(result["counts"]["raw_responses"], 0)
                    self.assertTrue((output / "checksums.sha256").exists())

    def test_cli_evidence_shapes_use_typed_error_without_report(self):
        capture, _ = self.capture(FakeAPI())
        evidence = capture.parent / "evidence.json"
        valid = {"schema": "ci-health.evidence/v1", "runs": {}}
        for index, value in enumerate(([], "evidence", 1, False, None, valid)):
            destination = capture.parent / f"report-{index}.json"
            evidence.write_text(json.dumps(value))
            result = subprocess.run([ci.sys.executable, "-B", str(SCRIPT), "summarize", str(capture),
                                     "--evidence", str(evidence), "--out", str(destination)],
                                    capture_output=True, text=True, timeout=20)
            with self.subTest(value=value):
                if value == valid:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(json.loads(destination.read_text())["complete"])
                else:
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertTrue(result.stderr.startswith("ci-health: "))
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertFalse(destination.exists())

    def test_capture_cannot_overwrite_or_pass_tampered_checksum(self):
        output, _ = self.capture(FakeAPI())
        original = ci.digest(output / "normalized.json")
        with self.assertRaises(FileExistsError):
            ci.Collector(FakeAPI(), output, "owner/repo", START, END).execute()
        self.assertEqual(ci.digest(output / "normalized.json"), original)
        (output / "normalized.json").write_text("{}")
        with self.assertRaisesRegex(ci.MeasurementError, "checksum failed"):
            ci.load_capture(output)

    def test_only_read_endpoints_no_logs_artifacts(self):
        api = FakeAPI()
        self.capture(api)
        self.assertTrue(all("/actions/runs" in endpoint for endpoint, _ in api.requests))
        self.assertFalse(any("logs" in endpoint or "artifacts" in endpoint for endpoint, _ in api.requests))

    def test_unlisted_raw_file_is_rejected(self):
        output, _ = self.capture(FakeAPI())
        (output / "raw/999999.json").write_text("{}")
        with self.assertRaisesRegex(ci.MeasurementError, "file set"):
            ci.load_capture(output)

    def test_structural_validation_rejects_orphan_job_even_with_new_checksum(self):
        output, _ = self.capture(FakeAPI())
        path = output / "normalized.json"
        data = json.loads(path.read_text())
        data["jobs"][0]["run_id"] = 999
        path.write_text(json.dumps(data))
        checksum = output / "checksums.sha256"
        lines = checksum.read_text().splitlines()
        checksum.write_text("\n".join(ci.digest(path) + "  normalized.json" if line.endswith("  normalized.json") else line for line in lines) + "\n")
        with self.assertRaisesRegex(ci.MeasurementError, "reference"):
            ci.load_capture(output)


class SummaryTests(unittest.TestCase):
    def test_cancelled_consumption_separate_from_success_latency(self):
        data = {"runs": [run()], "attempts": [], "jobs": [job(10, seconds=30), job(11, seconds=12, outcome="cancelled")]}
        summary = ci.summarize(manifest(), data)
        self.assertEqual(summary["demand"]["total_runner_seconds"], 42)
        self.assertEqual(summary["job_duration_seconds_by_outcome"]["success"]["mean"], 30)
        self.assertEqual(summary["job_duration_seconds_by_outcome"]["cancelled"]["mean"], 12)

    def test_skipped_job_not_executed_even_if_api_has_timestamps(self):
        skipped = job(outcome="skipped", seconds=0)
        summary = ci.summarize(manifest(), {"runs": [run()], "attempts": [], "jobs": [skipped]}, rates())
        self.assertEqual(summary["run_rows"][0]["executed_jobs"], 0)
        self.assertEqual(summary["job_duration_seconds_by_outcome"]["skipped"]["n"], 0)
        self.assertEqual(summary["cost"]["total_estimated_cost"], 0)

    def test_rounding_is_per_job_and_minimum_is_explicit(self):
        data = {"runs": [run()], "attempts": [], "jobs": [job(10, seconds=61), job(11, seconds=61)]}
        summary = ci.summarize(manifest(), data, rates())
        self.assertAlmostEqual(summary["cost"]["total_estimated_cost"], .04)
        card = rates()
        card["rates"][0]["minimum_seconds"] = 180
        self.assertAlmostEqual(ci.price_job(job(seconds=1), card)["amount"], .03)

    def test_missing_and_ambiguous_rates_stay_unknown(self):
        card = rates()
        card["rates"].append({**card["rates"][0], "id": "also-linux"})
        summary = report(rate=card)
        self.assertIsNone(summary["cost"]["total_estimated_cost"])
        self.assertEqual(summary["cost"]["status_counts"], {"ambiguous_rate": 1})
        self.assertEqual(ci.price_job(job(labels=["windows-latest"]), rates())["status"], "unmatched_rate")

    def test_negative_duration_and_invalid_rates_rejected(self):
        with self.assertRaisesRegex(ci.MeasurementError, "Negative"):
            ci.duration(job(seconds=-1))
        card = rates()
        card["rates"][0]["quantum_seconds"] = 0
        with self.assertRaises(ci.MeasurementError):
            ci.validate_rates(card)

    def test_no_rate_card_is_not_zero_cost(self):
        summary = report()
        self.assertIsNone(summary["cost"]["total_estimated_cost"])
        self.assertIsNone(summary["cost"]["known_estimated_cost"])

    def test_percentiles_nearest_rank_and_empty_unknown(self):
        result = ci.distribution([None, 1, 2, 3, 4, 5])
        self.assertEqual((result["n"], result["p50"], result["p95"]), (5, 3, 5))
        self.assertIsNone(ci.distribution([])["mean"])

    def test_evidence_cannot_silently_reference_wrong_capture(self):
        evidence = {"schema": "ci-health.evidence/v1", "runs": {"999": {"workload_label": "leaf"}}}
        with self.assertRaisesRegex(ci.MeasurementError, "outside"):
            report(evidence=evidence)


class CompareTests(unittest.TestCase):
    def test_baseline_weighted_means_and_outcome_counts(self):
        before, after = report(60, rate=rates()), report(30, rate=rates())
        result = ci.compare(before, after)
        self.assertEqual(result["baseline_weighted_means"]["runner_seconds"]["relative_change"], -.5)
        self.assertEqual(result["cost_basis"], "constant-rate estimate")
        self.assertEqual(result["stratum_results"][0]["before_outcomes"], {"success": 1})

    def test_missing_stratum_never_renormalizes_or_drops(self):
        before, after = report(60), report(30, event="push")
        result = ci.compare(before, after)
        self.assertEqual(len(result["stratum_results"]), 2)
        self.assertFalse(result["baseline_weighted_means"]["runner_seconds"]["supported"])
        self.assertIsNone(result["baseline_weighted_means"]["runner_seconds"]["after"])

    def test_missing_metric_disables_full_normalization(self):
        before, after = report(rate=rates()), report(rate=rates())
        after["run_rows"][0]["estimated_cost"] = None
        result = ci.compare(before, after)
        self.assertFalse(result["baseline_weighted_means"]["estimated_cost"]["supported"])

    def test_incompatible_and_incomplete_reports_rejected(self):
        before, after = report(), report()
        after["cohort"] = "activity"
        with self.assertRaisesRegex(ci.MeasurementError, "cohort"):
            ci.compare(before, after)
        after = report()
        after["complete"] = False
        with self.assertRaisesRegex(ci.MeasurementError, "complete"):
            ci.compare(before, after)

    def test_changed_currency_cannot_be_subtracted(self):
        card = rates()
        card["currency"] = "EUR"
        result = ci.compare(report(rate=rates()), report(rate=card))
        self.assertFalse(result["baseline_weighted_means"]["estimated_cost"]["supported"])

    def test_different_rates_flag_price_confounding(self):
        card = rates()
        card["rates"][0]["per_minute"] = "0.02"
        result = ci.compare(report(rate=rates()), report(rate=card))
        self.assertEqual(result["cost_basis"], "different/absent rate cards")
        self.assertTrue(any("constant-rate" in flag for flag in result["flags"]))

    def test_declared_pairs_require_matching_inputs(self):
        evidence = {"schema": "ci-health.evidence/v1", "runs": {"1": {
            "workload_label": "leaf", "pair_key": "case-1", "tested_sha": "a"*40, "test_manifest_sha256": "b"*64}}}
        before, after = report(60, evidence=evidence), report(30, evidence=evidence)
        result = ci.compare(before, after, paired=True)
        self.assertEqual(result["paired_differences"]["runner_seconds"]["mean"], -30)
        after["run_rows"][0]["tested_sha"] = "c"*40
        with self.assertRaisesRegex(ci.MeasurementError, "tested_sha"):
            ci.compare(before, after, paired=True)

    def test_empty_cohorts_cannot_claim_zero_change(self):
        capture = manifest()
        capture["counts"].update(runs=0, attempts=0, physical_jobs=0)
        empty = ci.summarize(capture, {"runs": [], "jobs": [], "attempts": []})
        result = ci.compare(empty, empty)
        self.assertFalse(result["baseline_weighted_means"]["runner_seconds"]["supported"])

    def test_paired_currency_mismatch_never_subtracts_money(self):
        evidence = {"schema": "ci-health.evidence/v1", "runs": {"1": {
            "pair_key": "case-1", "tested_sha": "a"*40, "test_manifest_sha256": "b"*64}}}
        card = rates()
        card["currency"] = "EUR"
        result = ci.compare(report(rate=rates(), evidence=evidence), report(rate=card, evidence=evidence), paired=True)
        money = result["paired_differences"]["estimated_cost"]
        self.assertIsNone(money["mean"])
        self.assertEqual(money["missing_pairs"], 1)
        self.assertFalse(money["supported"])

    def test_paired_metric_missingness_is_explicit(self):
        evidence = {"schema": "ci-health.evidence/v1", "runs": {"1": {
            "pair_key": "case-1", "tested_sha": "a"*40, "test_manifest_sha256": "b"*64}}}
        before, after = report(evidence=evidence), report(evidence=evidence)
        after["run_rows"][0]["runner_seconds"] = None
        result = ci.compare(before, after, paired=True)
        self.assertEqual(result["paired_differences"]["runner_seconds"]["missing_pairs"], 1)
        self.assertFalse(result["paired_differences"]["runner_seconds"]["supported"])

    def test_duplicate_run_cannot_inflate_reported_improvement(self):
        before, after = report(60), report(30)
        before["run_rows"].append({**before["run_rows"][0], "runner_seconds": 6000})
        with self.assertRaisesRegex(ci.MeasurementError, "count"):
            ci.compare(before, after)
        # Adjusting the counters still must not count one physical run twice.
        before["counts"].update(runs=2, attempts=2, physical_jobs=2, jobs_by_outcome={"success": 2})
        with self.assertRaisesRegex(ci.MeasurementError, "duplicate.*identity"):
            ci.compare(before, after)

    def test_complete_requires_boolean_true_and_no_issues(self):
        for value in (False, "false", "true", 1, [], None):
            with self.subTest(value=value):
                after = report()
                after["complete"] = value
                with self.assertRaisesRegex(ci.MeasurementError, "complete"):
                    ci.compare(report(), after)
        after = report()
        after["issues"] = [{"code": "missing_page"}]
        with self.assertRaisesRegex(ci.MeasurementError, "issues"):
            ci.compare(report(), after)

    def test_invalid_metrics_cannot_produce_supported_comparison(self):
        for field in ci.METRICS:
            for value in (-1, True, "30", float("nan"), float("inf"), -float("inf"), 10**400):
                with self.subTest(field=field, value=value):
                    after = report(rate=rates())
                    after["run_rows"][0][field] = value
                    with self.assertRaisesRegex(ci.MeasurementError, field):
                        ci.compare(report(rate=rates()), after)
        for value in (.5, 2):
            after = report()
            after["run_rows"][0]["executed_jobs"] = value
            with self.assertRaisesRegex(ci.MeasurementError, "executed_jobs"):
                ci.compare(report(), after)

    def test_invalid_counts_and_identities_are_rejected(self):
        for field, value in (("runs", 2), ("runs", True), ("attempts", 0),
                             ("physical_jobs", 2), ("raw_responses", -1)):
            with self.subTest(field=field, value=value):
                after = report()
                after["counts"][field] = value
                with self.assertRaises(ci.MeasurementError):
                    ci.compare(report(), after)
        for value in (0, -1, True, "1", []):
            with self.subTest(run_id=value):
                after = report()
                after["run_rows"][0]["run_id"] = value
                with self.assertRaisesRegex(ci.MeasurementError, "identity"):
                    ci.compare(report(), after)
        after = report()
        after["run_rows"][0]["physical_jobs"] = 2
        with self.assertRaisesRegex(ci.MeasurementError, "physical job count"):
            ci.compare(report(), after)

    def test_unknown_metrics_remain_unknown_after_json_roundtrip(self):
        before, after = report(60), report(30)
        for field in ci.METRICS:
            after["run_rows"][0][field] = None
        result = ci.compare(json.loads(json.dumps(before)), json.loads(json.dumps(after)))
        for field in ci.METRICS:
            self.assertFalse(result["baseline_weighted_means"][field]["supported"])
            self.assertIsNone(result["baseline_weighted_means"][field]["after"])

    def test_missing_or_malformed_structures_are_handled_errors(self):
        invalid = [[], None, "summary"]
        for field, value in (("run_rows", {}), ("run_rows", [None]), ("counts", []),
                             ("cost", []), ("window", []), ("repository", None), ("host", [])):
            item = report()
            item[field] = value
            invalid.append(item)
        for field in ("run_rows", "counts", "cost", "repository", "host"):
            item = report()
            del item[field]
            invalid.append(item)
        for item in invalid:
            with self.subTest(item=item):
                with self.assertRaises(ci.MeasurementError):
                    ci.compare(item, report())
        for field, value in (("outcome", []), ("runner_labels", [None]), ("pair_key", {}),
                             ("tested_sha", "short"), ("test_manifest_sha256", [])):
            item = report()
            item["run_rows"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ci.MeasurementError):
                ci.compare(report(), item)
        item = report()
        del item["run_rows"][0]["runner_seconds"]
        with self.assertRaisesRegex(ci.MeasurementError, "missing runner_seconds"):
            ci.compare(report(), item)

    def test_cost_currency_must_match_its_rate_card(self):
        after = report(rate=rates())
        after["cost"]["currency"] = "EUR"
        with self.assertRaisesRegex(ci.MeasurementError, "currency"):
            ci.compare(report(rate=rates()), after)

    def test_cli_rejects_malformed_summary_without_output_or_traceback(self):
        invalid = [[], {**report(), "complete": "false"}]
        duplicate = report()
        duplicate["run_rows"].append(dict(duplicate["run_rows"][0]))
        invalid.append(duplicate)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, after = root / "before.json", root / "after.json"
            before.write_text(json.dumps(report()))
            for item in invalid:
                after.write_text(json.dumps(item))
                with self.subTest(item=item), patch.object(ci.sys, "stderr", new_callable=io.StringIO) as errors, patch.object(ci.sys, "stdout", new_callable=io.StringIO) as output:
                    status = ci.main(["compare", str(before), str(after), "--out", str(root / "result.json")])
                self.assertEqual(status, 2)
                self.assertTrue(errors.getvalue().startswith("ci-health: "))
                self.assertNotIn("Traceback", errors.getvalue())
                self.assertEqual(output.getvalue(), "")
                self.assertFalse((root / "result.json").exists())


class SafetyTests(unittest.TestCase):
    def test_future_window_rejected_before_network_or_write(self):
        with patch.object(ci, "GitHub") as network, patch.object(ci.sys, "stderr", new_callable=io.StringIO):
            status = ci.main(["collect", "--repo", "owner/repo", "--start", "2098-01-01T00:00:00Z", "--end", "2099-01-01T00:00:00Z", "--out", "/tmp/ci-health-never-created"])
        self.assertEqual(status, 2)
        network.assert_not_called()

    def test_explicit_utc_boundaries(self):
        for invalid in ("2026-01-01", "2026-01-01T00:00:00-08:00", "2026-01-01T00:00:00.1Z"):
            with self.assertRaises(ci.MeasurementError):
                ci.timestamp(invalid, boundary=True)

    def test_output_in_git_is_rejected(self):
        response = subprocess.CompletedProcess([], 0, "true\nfalse\nfalse\n", "")
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(ci.subprocess, "run", return_value=response):
                with self.assertRaisesRegex(ci.MeasurementError, "outside every Git"):
                    ci.external_destination(Path(temporary) / "output")

    def test_outputs_cannot_be_nested_in_existing_capture(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "capture.json").write_text("{}")
            (root / "checksums.sha256").write_text("")
            with self.assertRaisesRegex(ci.MeasurementError, "nested inside"):
                ci.external_destination(root / "new-collection" / "capture")

    def test_gh_command_is_get_and_transient_retries_bounded(self):
        failure = subprocess.CompletedProcess([], 1, "", "gh: unavailable (HTTP 503)")
        with patch.object(ci.shutil, "which", return_value="/reviewed/gh"), patch.object(ci.subprocess, "run", return_value=failure) as invoke, patch.object(ci.time, "sleep"):
            with self.assertRaises(ci.MeasurementError):
                ci.GitHub().get("repos/owner/repo/actions/runs", {})
            self.assertEqual(invoke.call_count, 4)
            command = invoke.call_args.args[0]
            self.assertEqual(command[command.index("--method")+1], "GET")


if __name__ == "__main__":
    unittest.main()
