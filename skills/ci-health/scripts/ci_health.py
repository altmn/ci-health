#!/usr/bin/env python3
"""Read-only GitHub CI measurement. Python 3.11+, stdlib, authenticated gh."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

VERSION = "0.1.1"
CAPTURE_SCHEMA = "ci-health.capture/v1"
SUMMARY_SCHEMA = "ci-health.summary/v1"
COMPARE_SCHEMA = "ci-health.comparison/v1"
DEFINITIONS = "run-created-cohort-demand/v1"
COHORT = "run-created-half-open-all-observed-attempts"
API_VERSION = "2026-03-10"
STRATA = ("workflow_path", "event", "runner_labels", "workload_label")
METRICS = ("runner_seconds", "executed_jobs", "estimated_cost")


class MeasurementError(Exception):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp(value, *, boundary=False):
    if not isinstance(value, str):
        raise MeasurementError("Timestamp must be an ISO-8601 string with timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MeasurementError(f"Invalid timestamp: {value!r}") from exc
    if result.tzinfo is None:
        raise MeasurementError("Timestamps need an explicit timezone")
    if boundary and (result.utcoffset() != timedelta(0) or result.microsecond):
        raise MeasurementError("Window boundaries must be UTC whole seconds (Z or +00:00)")
    return result.astimezone(timezone.utc)


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def duration(record):
    if not record.get("started_at") or not record.get("completed_at"):
        return None
    result = (timestamp(record["completed_at"]) - timestamp(record["started_at"])).total_seconds()
    if result < 0:
        raise MeasurementError("Negative execution duration")
    return result


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MeasurementError(f"Cannot read JSON: {path}") from exc


def write_json(path, value):
    # Exclusive creation: neither a baseline nor a raw response can be overwritten.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def external_destination(path):
    """Verify an explicit absolute destination outside Git before any write."""
    requested = Path(path).expanduser()
    if not requested.is_absolute():
        raise MeasurementError("Output must be an absolute path outside Git")
    result = requested.resolve()
    if result.exists():
        raise MeasurementError(f"Refusing to overwrite existing output: {result}")
    if any((ancestor / "capture.json").is_file() and (ancestor / "checksums.sha256").is_file() for ancestor in result.parents):
        raise MeasurementError("Output must not be nested inside an immutable capture")
    parent = result.parent
    while not parent.exists():
        parent = parent.parent
    git = shutil.which("git")
    if not git:
        raise MeasurementError("git is needed to verify that output is outside a repository")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    check = subprocess.run(
        [git, "-C", str(parent), "rev-parse", "--is-inside-work-tree", "--is-inside-git-dir", "--is-bare-repository"],
        capture_output=True, text=True, env=environment, timeout=20,
    )
    if check.returncode == 0 and "true" in check.stdout.splitlines():
        raise MeasurementError("Output must be outside every Git repository (ignored is insufficient)")
    if check.returncode not in (0, 128) or (check.returncode == 128 and "not a git repository" not in check.stderr.lower()):
        raise MeasurementError("Could not verify output is outside Git")
    return result


class GitHub:
    def __init__(self, host="github.com", api_version=API_VERSION):
        self.executable = shutil.which("gh")
        if not self.executable:
            raise MeasurementError("Install GitHub CLI and authenticate it before collecting")
        self.host = host
        self.api_version = api_version

    def get(self, endpoint, parameters):
        command = [self.executable, "api", "--hostname", self.host, "--method", "GET",
                   "-H", "Accept: application/vnd.github+json",
                   "-H", f"X-GitHub-Api-Version: {self.api_version}", endpoint]
        for key, value in parameters.items():
            command.extend(["-f", f"{key}={value}"])
        for attempt in range(4):
            try:
                response = subprocess.run(command, text=True, capture_output=True, timeout=90)
            except subprocess.TimeoutExpired:
                if attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                raise MeasurementError("GitHub GET timed out after bounded retries") from None
            if response.returncode == 0:
                try:
                    return json.loads(response.stdout)
                except ValueError as exc:
                    raise MeasurementError("GitHub GET returned invalid JSON") from exc
            match = re.search(r"HTTP (\d{3})", response.stderr)
            status = int(match.group(1)) if match else None
            retryable = status in (429, 500, 502, 503, 504) or (status == 403 and "rate limit" in response.stderr.lower())
            if retryable and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            # Do not save arbitrary gh stderr, which can contain account information.
            raise MeasurementError(f"GitHub GET failed (HTTP {status or 'unknown'}); authenticate/check access or retry later")


class Collector:
    def __init__(self, api, output, repo, start, end, host="github.com", api_version=API_VERSION):
        self.api, self.output, self.repo = api, Path(output), repo
        self.start, self.end = start, end
        self.prefix = f"repos/{repo}/actions/runs"
        self.raw_counter = 0
        self.last_observed_at = None
        self.runs, self.attempts, self.jobs = {}, [], {}
        self.issues = []
        self.manifest = {
            "schema": CAPTURE_SCHEMA, "definitions": DEFINITIONS, "collector_version": VERSION,
            "cohort": COHORT, "repository": repo, "host": host, "api_version": api_version,
            "start_inclusive": iso(start), "end_exclusive": iso(end), "capture_started_at": utc_now(),
            "complete": False,
            "scope_note": "Run-created cohort; not complete period activity. Attempts observed at capture time only.",
        }

    def issue(self, code, detail):
        self.issues.append({"code": code, "detail": detail})

    def get(self, endpoint, parameters=None):
        parameters = parameters or {}
        body = self.api.get(endpoint, parameters)
        self.raw_counter += 1
        self.last_observed_at = utc_now()
        write_json(self.output / "raw" / f"{self.raw_counter:06d}.json", {
            "request": {"endpoint": endpoint, "parameters": parameters},
            "observed_at": self.last_observed_at, "body": body,
        })
        if not isinstance(body, dict):
            raise MeasurementError("Expected an API object")
        return body

    def pages(self, endpoint, field, parameters=None, first=None):
        params = dict(parameters or {}, per_page=100, page=1)
        first = first if first is not None else self.get(endpoint, params)
        count = first.get("total_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise MeasurementError("Missing or invalid total_count")
        records = []
        pages = max(1, math.ceil(count / 100))
        for page in range(1, pages + 1):
            body = first if page == 1 else self.get(endpoint, dict(params, page=page))
            values = body.get(field)
            if body.get("total_count") != count or not isinstance(values, list):
                raise MeasurementError("Pagination changed or returned an invalid page; recapture")
            records.extend(values)
        if len(records) != count or len({item.get("id") for item in records}) != count:
            raise MeasurementError("Incomplete/duplicate pagination; recapture")
        if any(not isinstance(item.get("id"), int) for item in records):
            raise MeasurementError("Missing record ID")
        return records

    def run_window(self, start, end):
        params = {"created": f"{iso(start)}..{iso(end - timedelta(seconds=1))}", "per_page": 100, "page": 1}
        first = self.get(self.prefix, params)
        count = first.get("total_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise MeasurementError("Invalid run search total_count")
        if count >= 1000:
            seconds = int((end - start).total_seconds())
            if seconds <= 1:
                raise MeasurementError("Run search capped at a one-second partition; capture is incomplete")
            middle = start + timedelta(seconds=seconds // 2)
            self.run_window(start, middle)
            self.run_window(middle, end)
            observed = sum(start <= timestamp(run["created_at"]) < end for run in self.runs.values())
            if observed < count:
                raise MeasurementError("Split search underflow: child inventories are smaller than the known parent count; recapture")
            return
        for run in self.pages(self.prefix, "workflow_runs", params, first):
            created = timestamp(run.get("created_at"))
            if not start <= created < end:
                raise MeasurementError("API returned a run outside the requested whole-second partition")
            previous = self.runs.get(run["id"])
            if previous is not None and previous != run:
                raise MeasurementError("Run metadata changed between partitions")
            self.runs[run["id"]] = run

    def add_job(self, job, run_id, attempt):
        if job.get("run_id") != run_id:
            raise MeasurementError("Job has a mismatched run_id")
        identity = job["id"]
        record = {key: job.get(key) for key in (
            "id", "run_id", "name", "status", "conclusion", "started_at", "completed_at",
            "labels", "runner_id", "runner_name", "runner_group_id", "head_sha", "steps",
        )}
        record["observed_in_attempts"] = [attempt]
        previous = self.jobs.get(identity)
        if previous:
            if any(previous[key] != record[key] for key in record if key != "observed_in_attempts"):
                self.issue("job_changed", f"Physical job {identity} changed during capture")
            memberships = sorted(set(previous["observed_in_attempts"] + [attempt]))
            record["observed_in_attempts"] = memberships
        self.jobs[identity] = record
        if job.get("status") != "completed":
            self.issue("nonterminal_job", f"Physical job {identity} was not complete")
        if job.get("conclusion") != "skipped" and duration(job) is None:
            self.issue("missing_job_duration", f"Physical job {identity} lacks a complete execution interval")

    def execute(self):
        self.output.mkdir(parents=True, mode=0o700, exist_ok=False)
        (self.output / "raw").mkdir(mode=0o700)
        try:
            self.run_window(self.start, self.end)
            for run_id, run in sorted(self.runs.items()):
                attempt_count = run.get("run_attempt")
                if not isinstance(attempt_count, int) or attempt_count < 1:
                    raise MeasurementError("Missing run_attempt; cannot enumerate complete history")
                for attempt in range(1, attempt_count + 1):
                    endpoint = f"{self.prefix}/{run_id}/attempts/{attempt}"
                    metadata = self.get(endpoint)
                    if metadata.get("id") != run_id or metadata.get("run_attempt") != attempt:
                        raise MeasurementError("Attempt response identity mismatch")
                    self.attempts.append(metadata)
                    if metadata.get("status") != "completed":
                        self.issue("nonterminal_attempt", f"Run {run_id} attempt {attempt} was not complete")
                    for job in self.pages(endpoint + "/jobs", "jobs"):
                        self.add_job(job, run_id, attempt)
            # Final pass catches earlier runs changing while later runs were read.
            # Each recheck is its own observation cutoff, not an atomic global snapshot.
            self.manifest["run_rechecks"] = []
            for run_id, run in sorted(self.runs.items()):
                latest = self.get(f"{self.prefix}/{run_id}")
                self.manifest["run_rechecks"].append({"run_id": run_id, "observed_at": self.last_observed_at,
                    "run_attempt": latest.get("run_attempt"), "status": latest.get("status"),
                    "conclusion": latest.get("conclusion"), "updated_at": latest.get("updated_at")})
                if any(latest.get(key) != run.get(key) for key in ("run_attempt", "status", "conclusion", "updated_at")):
                    self.issue("run_changed", f"Run {run_id} changed during capture; recapture")
                if latest.get("status") != "completed":
                    self.issue("nonterminal_run", f"Run {run_id} was not complete at recheck")
        except (MeasurementError, OSError, ValueError, TypeError, KeyError) as exc:
            self.issue("collection_error", str(exc))
        normalized = {"runs": list(self.runs.values()), "attempts": self.attempts, "jobs": list(self.jobs.values())}
        write_json(self.output / "normalized.json", normalized)
        self.manifest.update({
            "capture_finished_at": utc_now(), "complete": not self.issues, "issues": self.issues,
            "counts": {"runs": len(self.runs), "attempts": len(self.attempts), "physical_jobs": len(self.jobs), "raw_responses": self.raw_counter},
        })
        write_json(self.output / "capture.json", self.manifest)
        files = sorted(path for path in self.output.rglob("*") if path.is_file())
        with (self.output / "checksums.sha256").open("x", encoding="utf-8") as stream:
            for path in files:
                stream.write(f"{digest(path)}  {path.relative_to(self.output).as_posix()}\n")
        return self.manifest


def load_capture(path):
    root = Path(path).resolve()
    checksum_path = root / "checksums.sha256"
    try:
        lines = checksum_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise MeasurementError("Capture has no completed checksum manifest") from exc
    checked = set()
    for line in lines:
        try:
            expected, name = line.split("  ", 1)
        except ValueError as exc:
            raise MeasurementError("Invalid checksum entry") from exc
        target = (root / name).resolve()
        if not target.is_relative_to(root) or name in checked or not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise MeasurementError("Unsafe or duplicate checksum entry")
        if not target.is_file() or digest(target) != expected:
            raise MeasurementError(f"Capture checksum failed: {name}")
        checked.add(name)
    if not {"capture.json", "normalized.json"}.issubset(checked):
        raise MeasurementError("Checksum manifest omits required capture files")
    actual = {item.relative_to(root).as_posix() for item in root.rglob("*") if item.is_file() and item != checksum_path}
    if actual != checked:
        raise MeasurementError("Capture file set differs from checksum manifest")
    manifest, normalized = read_json(root / "capture.json"), read_json(root / "normalized.json")
    if manifest.get("schema") != CAPTURE_SCHEMA or manifest.get("definitions") != DEFINITIONS:
        raise MeasurementError("Unsupported capture schema/metric definitions")
    raw_files = {name for name in checked if re.fullmatch(r"raw/\d{6,}\.json", name)}
    if checked != raw_files | {"capture.json", "normalized.json"} or len(raw_files) != manifest.get("counts", {}).get("raw_responses"):
        raise MeasurementError("Raw response inventory/count does not match capture")
    validate_normalized(manifest, normalized)
    return manifest, normalized


def validate_normalized(manifest, data):
    """Reject inconsistent/corrupt inventories even if checksums were regenerated."""
    if manifest.get("cohort") != COHORT or not isinstance(manifest.get("complete"), bool):
        raise MeasurementError("Invalid capture cohort/completeness")
    if not isinstance(manifest.get("issues"), list) or (manifest["complete"] and manifest["issues"]):
        raise MeasurementError("Capture completeness contradicts issues")
    if not isinstance(data, dict) or any(not isinstance(data.get(key), list) for key in ("runs", "attempts", "jobs")):
        raise MeasurementError("Normalized capture needs runs, attempts and jobs arrays")
    start, end = timestamp(manifest["start_inclusive"], boundary=True), timestamp(manifest["end_exclusive"], boundary=True)
    if end <= start:
        raise MeasurementError("Invalid capture window")
    counts = manifest.get("counts", {})
    for key, records in (("runs", data["runs"]), ("attempts", data["attempts"]), ("physical_jobs", data["jobs"])):
        if counts.get(key) != len(records):
            raise MeasurementError(f"Normalized {key} count contradicts manifest")
    runs = {}
    for record in data["runs"]:
        if not isinstance(record, dict):
            raise MeasurementError("Invalid normalized run record")
        identity, attempt = record.get("id"), record.get("run_attempt")
        if type(identity) is not int or identity in runs or type(attempt) is not int or attempt < 1:
            raise MeasurementError("Invalid/duplicate run identity or attempt count")
        if not start <= timestamp(record.get("created_at")) < end:
            raise MeasurementError("Normalized run lies outside cohort")
        if manifest["complete"] and record.get("status") != "completed":
            raise MeasurementError("Complete capture contains nonterminal run")
        runs[identity] = record
    attempts = set()
    for record in data["attempts"]:
        if not isinstance(record, dict):
            raise MeasurementError("Invalid normalized attempt record")
        run_id, attempt = record.get("id"), record.get("run_attempt")
        if run_id not in runs or type(attempt) is not int or not 1 <= attempt <= runs[run_id]["run_attempt"] or (run_id, attempt) in attempts:
            raise MeasurementError("Invalid/duplicate attempt reference")
        if manifest["complete"] and record.get("status") != "completed":
            raise MeasurementError("Complete capture contains nonterminal attempt")
        attempts.add((run_id, attempt))
    if manifest["complete"] and attempts != {(identity, number) for identity, run in runs.items() for number in range(1, run["run_attempt"] + 1)}:
        raise MeasurementError("Complete capture omits attempts")
    rechecks = manifest.get("run_rechecks", [])
    if not isinstance(rechecks, list) or any(not isinstance(item, dict) for item in rechecks):
        raise MeasurementError("Invalid final run-recheck inventory")
    if manifest["complete"] and (len(rechecks) != len(runs) or {item.get("run_id") for item in rechecks} != set(runs)):
        raise MeasurementError("Complete capture omits final run rechecks")
    for check in rechecks:
        if check.get("run_id") not in runs:
            raise MeasurementError("Recheck refers to unknown run")
        timestamp(check.get("observed_at"))
        if manifest["complete"] and any(check.get(key) != runs[check["run_id"]].get(key) for key in ("run_attempt", "status", "conclusion", "updated_at")):
            raise MeasurementError("Complete capture contradicts final recheck")
    jobs = set()
    for record in data["jobs"]:
        if not isinstance(record, dict):
            raise MeasurementError("Invalid normalized job record")
        identity, run_id = record.get("id"), record.get("run_id")
        memberships = record.get("observed_in_attempts")
        if type(identity) is not int or identity in jobs or run_id not in runs:
            raise MeasurementError("Invalid/duplicate job or run reference")
        if not isinstance(memberships, list) or not memberships or any(type(number) is not int or (run_id, number) not in attempts for number in memberships):
            raise MeasurementError("Job refers to missing attempt")
        if not isinstance(record.get("labels"), list) or any(not isinstance(label, str) for label in record["labels"]):
            raise MeasurementError("Job labels must be an array of strings")
        if not isinstance(record.get("steps"), list):
            raise MeasurementError("Job steps must be an array")
        seconds = duration(record)
        if manifest["complete"] and (record.get("status") != "completed" or (record.get("conclusion") != "skipped" and seconds is None)):
            raise MeasurementError("Complete capture contains incomplete job execution")
        for step in record["steps"]:
            if not isinstance(step, dict):
                raise MeasurementError("Invalid step record")
            duration(step)
        jobs.add(identity)


def distribution(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return {"n": 0, "mean": None, "p50": None, "p95": None, "min": None, "max": None}
    def percentile(fraction):
        return values[max(0, math.ceil(fraction * len(values)) - 1)]
    return {"n": len(values), "mean": sum(values) / len(values), "p50": percentile(.5), "p95": percentile(.95), "min": values[0], "max": values[-1]}


def decimal_value(value, name, *, positive=False):
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise MeasurementError(f"Invalid rate-card {name}") from exc
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise MeasurementError(f"Invalid rate-card {name}")
    return result


def validate_rates(rates):
    if rates is None:
        return None
    if not isinstance(rates, dict) or rates.get("schema") != "ci-health.rates/v1" or not isinstance(rates.get("currency"), str) or not re.fullmatch(r"[A-Z]{3}", rates["currency"]):
        raise MeasurementError("Rate card needs ci-health.rates/v1 and a three-letter currency")
    try:
        datetime.strptime(rates["effective_date"], "%Y-%m-%d")
    except (KeyError, ValueError, TypeError) as exc:
        raise MeasurementError("Rate card needs effective_date YYYY-MM-DD") from exc
    entries = rates.get("rates")
    if not isinstance(entries, list) or not entries:
        raise MeasurementError("Rate card needs nonempty rates")
    identities = set()
    for rate in entries:
        if not isinstance(rate, dict):
            raise MeasurementError("Rate entries must be objects")
        identity = rate.get("id")
        if not isinstance(identity, str) or not identity or identity in identities:
            raise MeasurementError("Rates need unique nonempty IDs")
        identities.add(identity)
        for field in ("labels_all", "labels_none"):
            labels = rate.get(field, [])
            if not isinstance(labels, list) or any(not isinstance(value, str) for value in labels):
                raise MeasurementError("Rate labels must be arrays of strings")
        if not rate.get("labels_all"):
            raise MeasurementError("Every rate needs a nonempty labels_all selector")
        decimal_value(rate.get("per_minute"), "per_minute")
        decimal_value(rate.get("quantum_seconds"), "quantum_seconds", positive=True)
        decimal_value(rate.get("minimum_seconds", 0), "minimum_seconds")
    return rates


def price_job(job, rates):
    if job.get("conclusion") == "skipped":
        return {"amount": 0.0, "status": "not_executed", "rate_id": None}
    seconds = duration(job)
    if seconds is None:
        return {"amount": None, "status": "unknown_duration", "rate_id": None}
    if rates is None:
        return {"amount": None, "status": "no_rate_card", "rate_id": None}
    labels = set(job.get("labels") or [])
    matches = [entry for entry in rates["rates"] if set(entry["labels_all"]) <= labels and not set(entry.get("labels_none", [])) & labels]
    if len(matches) != 1:
        return {"amount": None, "status": "ambiguous_rate" if matches else "unmatched_rate", "rate_id": None}
    rate = matches[0]
    quantum = Decimal(str(rate["quantum_seconds"]))
    billable = max(Decimal(str(seconds)), Decimal(str(rate.get("minimum_seconds", 0))))
    billable = (billable / quantum).to_integral_value(rounding=ROUND_CEILING) * quantum
    amount = billable / Decimal(60) * Decimal(str(rate["per_minute"]))
    return {"amount": float(amount), "status": "estimated", "rate_id": rate["id"], "estimated_billable_seconds": float(billable)}


def validate_evidence(evidence, run_ids):
    if evidence is None:
        return {}
    if evidence.get("schema") != "ci-health.evidence/v1" or not isinstance(evidence.get("runs"), dict):
        raise MeasurementError("Evidence needs ci-health.evidence/v1 and a runs object")
    if set(evidence["runs"]) - {str(value) for value in run_ids}:
        raise MeasurementError("Evidence references runs outside this capture")
    for record in evidence["runs"].values():
        if not isinstance(record, dict):
            raise MeasurementError("Evidence run entries must be objects")
        if set(record) - {"workload_label", "pair_key", "tested_sha", "test_manifest_sha256"}:
            raise MeasurementError("Unknown evidence field")
        if any(not isinstance(value, str) or not value or len(value) > 1024 for value in record.values()):
            raise MeasurementError("Evidence values must be nonempty strings of at most 1024 characters")
        for field, pattern in (("tested_sha", r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}"), ("test_manifest_sha256", r"[a-fA-F0-9]{64}")):
            if field in record and not re.fullmatch(pattern, record[field]):
                raise MeasurementError(f"Evidence {field} must be a full hexadecimal hash")
    return evidence["runs"]


def summarize(manifest, data, rates=None, evidence=None):
    rates = validate_rates(rates)
    evidence = validate_evidence(evidence, [run["id"] for run in data["runs"]])
    jobs_by_run, job_outcomes, step_outcomes = defaultdict(list), defaultdict(list), defaultdict(list)
    outcome_counts, step_counts, price_counts = Counter(), Counter(), Counter()
    known_seconds, missing_seconds, known_cost, unknown_cost = 0.0, 0, 0.0, 0
    physical_ids = set()
    for job in data["jobs"]:
        if job["id"] in physical_ids:
            raise MeasurementError("Duplicate physical jobs in normalized capture")
        physical_ids.add(job["id"])
        jobs_by_run[job["run_id"]].append(job)
        outcome = job.get("conclusion") or job.get("status") or "unknown"
        outcome_counts[outcome] += 1
        skipped = outcome == "skipped"
        seconds = None if skipped else duration(job)
        if seconds is not None:
            known_seconds += seconds
            job_outcomes[outcome].append(seconds)
        elif not skipped:
            missing_seconds += 1
        price = price_job(job, rates)
        price_counts[price["status"]] += 1
        if price["amount"] is None:
            unknown_cost += 1
        else:
            known_cost += price["amount"]
        for step in job.get("steps") or []:
            step_outcome = step.get("conclusion") or step.get("status") or "unknown"
            step_counts[step_outcome] += 1
            value = None if step_outcome == "skipped" else duration(step)
            if value is not None:
                step_outcomes[step_outcome].append(value)
    rows = []
    for run in data["runs"]:
        jobs = jobs_by_run[run["id"]]
        values = [duration(job) for job in jobs if job.get("conclusion") != "skipped"]
        costs = [price_job(job, rates)["amount"] for job in jobs]
        declared = evidence.get(str(run["id"]), {})
        row = {"run_id": run["id"], "workflow_path": run.get("path"), "event": run.get("event"),
               "head_sha": run.get("head_sha"), "outcome": run.get("conclusion") or run.get("status"),
               "runner_labels": sorted({label for job in jobs for label in (job.get("labels") or [])}),
               "workload_label": declared.get("workload_label"), "pair_key": declared.get("pair_key"),
               "tested_sha": declared.get("tested_sha"), "test_manifest_sha256": declared.get("test_manifest_sha256"),
               "runner_seconds": sum(values) if all(value is not None for value in values) else None,
               "executed_jobs": sum(bool(job.get("started_at")) and job.get("conclusion") != "skipped" for job in jobs),
               "estimated_cost": sum(costs) if rates and all(value is not None for value in costs) else None,
               "physical_jobs": len(jobs)}
        if not manifest["complete"]:
            # Incomplete inventories cannot support complete per-run totals.
            row.update(runner_seconds=None, executed_jobs=None, estimated_cost=None)
        rows.append(row)
    return {
        "schema": SUMMARY_SCHEMA, "definitions": DEFINITIONS, "cohort": manifest["cohort"],
        "repository": manifest["repository"], "host": manifest["host"], "complete": manifest["complete"],
        "window": {key: manifest[key] for key in ("start_inclusive", "end_exclusive")},
        "capture_finished_at": manifest["capture_finished_at"], "issues": manifest["issues"],
        "counts": {**manifest["counts"], "jobs_by_outcome": dict(outcome_counts), "steps_by_outcome": dict(step_counts)},
        "demand": {"known_runner_seconds": known_seconds, "jobs_missing_duration": missing_seconds,
                   "total_runner_seconds": known_seconds if manifest["complete"] and not missing_seconds else None},
        "job_duration_seconds_by_outcome": {key: distribution(job_outcomes[key]) for key in outcome_counts},
        "step_duration_seconds_by_outcome": {key: distribution(step_outcomes[key]) for key in step_counts},
        "cost": {"kind": "rate-card estimate, not invoice", "currency": rates["currency"] if rates else None,
                 "rate_card": rates, "known_estimated_cost": known_cost if rates else None,
                 "unknown_cost_jobs": unknown_cost, "status_counts": dict(price_counts),
                 "total_estimated_cost": known_cost if rates and manifest["complete"] and not unknown_cost else None},
        "run_rows": rows,
        "limitations": ["Run-created cohort is not complete period activity or per-revision accounting.",
                        "All observed attempts are counted; future reruns require a new capture.",
                        "Cancelled execution durations are consumed time, censored for natural completion latency.",
                        "No exact eligible queue, required-verdict or billing timing is inferred from REST.",
                        "Nearest-rank percentiles; small samples do not establish stable tail behavior.",
                        "Strata and declared workload evidence do not prove causal equivalence."],
    }


def validate_summary(report):
    """Validate the comparison contract, including inventories and unknown values.

    Summaries are external JSON inputs, not authenticated capture evidence. This
    rejects contradictory/malformed records without claiming to verify their source.
    """
    if not isinstance(report, dict):
        raise MeasurementError("Summary must be an object")
    if report.get("schema") != SUMMARY_SCHEMA or report.get("definitions") != DEFINITIONS:
        raise MeasurementError("Unsupported summary schema/definitions")
    if report.get("cohort") != COHORT:
        raise MeasurementError("Unsupported summary cohort")
    if report.get("complete") is not True:
        raise MeasurementError("Comparison requires complete captures with complete=true")
    if report.get("issues") != []:
        raise MeasurementError("Summary completeness contradicts issues")
    for field, pattern in (("repository", r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"),
                           ("host", r"[A-Za-z0-9.-]+")):
        value = report.get(field)
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise MeasurementError(f"Invalid summary {field}")
    if any(part in (".", "..") for part in report["repository"].split("/")):
        raise MeasurementError("Invalid summary repository")
    window = report.get("window")
    if not isinstance(window, dict):
        raise MeasurementError("Summary needs a window object")
    start = timestamp(window.get("start_inclusive"), boundary=True)
    end = timestamp(window.get("end_exclusive"), boundary=True)
    if end <= start:
        raise MeasurementError("Invalid summary window")
    timestamp(report.get("capture_finished_at"))

    def count(value, name):
        if type(value) is not int or value < 0:
            raise MeasurementError(f"Summary {name} must be a nonnegative integer")

    def metric(value, name):
        if value is None:
            return  # Unknown observations must not become zero.
        try:
            valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
        except OverflowError:
            valid = False
        if not valid:
            raise MeasurementError(f"Summary {name} must be finite and nonnegative, or null")

    counts, rows, cost = report.get("counts"), report.get("run_rows"), report.get("cost")
    if not isinstance(counts, dict) or not isinstance(rows, list) or not isinstance(cost, dict):
        raise MeasurementError("Summary needs counts/cost objects and a run_rows array")
    for field in ("runs", "attempts", "physical_jobs", "raw_responses"):
        count(counts.get(field), f"counts.{field}")
    if counts["runs"] != len(rows) or counts["attempts"] < counts["runs"]:
        raise MeasurementError("Summary run/attempt counts contradict run_rows")
    for field in ("jobs_by_outcome", "steps_by_outcome"):
        outcomes = counts.get(field)
        if not isinstance(outcomes, dict):
            raise MeasurementError(f"Summary counts.{field} must be an object")
        for outcome, value in outcomes.items():
            if not isinstance(outcome, str) or not outcome:
                raise MeasurementError("Summary outcome names must be nonempty strings")
            count(value, f"counts.{field}")
    if sum(counts["jobs_by_outcome"].values()) != counts["physical_jobs"]:
        raise MeasurementError("Summary job outcome counts contradict physical_jobs")
    if "rate_card" not in cost or "currency" not in cost:
        raise MeasurementError("Summary cost needs rate_card and currency")
    card = validate_rates(cost["rate_card"])
    if cost["currency"] != (card["currency"] if card else None):
        raise MeasurementError("Summary currency contradicts its rate card")

    identities, physical_jobs = set(), 0
    for row in rows:
        if not isinstance(row, dict):
            raise MeasurementError("Summary run_rows entries must be objects")
        identity = row.get("run_id")
        if type(identity) is not int or identity <= 0 or identity in identities:
            raise MeasurementError("Invalid/duplicate summary run identity")
        identities.add(identity)
        for field in ("workflow_path", "event", "outcome", "workload_label", "pair_key"):
            value = row.get(field)
            if value is not None and (not isinstance(value, str) or not value):
                raise MeasurementError(f"Summary {field} must be a nonempty string or null")
        for field, pattern in (("tested_sha", r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}"),
                               ("test_manifest_sha256", r"[a-fA-F0-9]{64}")):
            value = row.get(field)
            if value is not None and (not isinstance(value, str) or not re.fullmatch(pattern, value)):
                raise MeasurementError(f"Summary {field} must be a full hexadecimal hash or null")
        labels = row.get("runner_labels")
        if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels) or len(set(labels)) != len(labels):
            raise MeasurementError("Summary runner_labels must be an array of unique strings")
        for field in METRICS:
            if field not in row:
                raise MeasurementError(f"Summary row is missing {field}; use null for unknown")
            metric(row[field], field)
        count(row.get("physical_jobs"), "physical_jobs")
        if row["executed_jobs"] is not None:
            count(row["executed_jobs"], "executed_jobs")
            if row["executed_jobs"] > row["physical_jobs"]:
                raise MeasurementError("Summary executed_jobs exceeds physical_jobs")
        if row["estimated_cost"] is not None and card is None:
            raise MeasurementError("Summary estimated_cost needs a rate card")
        physical_jobs += row["physical_jobs"]
    if physical_jobs != counts["physical_jobs"]:
        raise MeasurementError("Summary physical job count contradicts run_rows")


def compare(before, after, strata=STRATA, paired=False):
    for report in (before, after):
        validate_summary(report)
    for field in ("definitions", "cohort", "repository", "host"):
        if before.get(field) != after.get(field):
            raise MeasurementError(f"Incompatible comparison field: {field}")
    if not strata or len(set(strata)) != len(strata) or set(strata) - set(STRATA):
        raise MeasurementError(f"Strata must be distinct fields from {', '.join(STRATA)}")
    groups = []
    for report in (before, after):
        grouped = defaultdict(list)
        for row in report["run_rows"]:
            key = json.dumps([row.get(field) for field in strata], sort_keys=True)
            grouped[key].append(row)
        groups.append(grouped)
    a, b = groups
    keys = sorted(set(a) | set(b))
    results, flags = [], []
    if set(a) != set(b):
        flags.append("Missing/new strata: normalized overall comparisons are unsupported; none are silently dropped.")
    if not before["run_rows"] or not after["run_rows"]:
        flags.append("One or both cohorts are empty.")
    rate_a, rate_b = before["cost"].get("rate_card"), after["cost"].get("rate_card")
    constant_rates = rate_a is not None and rate_a == rate_b
    if not constant_rates:
        flags.append("Cost comparison is not constant-rate (or rates absent); re-summarize both with one rate card to isolate usage.")
    if "runner_labels" not in strata:
        flags.append("Runner labels are not stratified; infrastructure mix may confound results.")
    if not paired:
        flags.append("Observational comparison: workload labels do not establish equivalent tested inputs or causality.")
    if any(not row.get("workload_label") for report in (before, after) for row in report["run_rows"]):
        flags.append("Some workload labels are missing; workload equivalence remains unknown.")
    paired_deltas = defaultdict(list)
    paired_count = 0
    cost_comparable = bool(before["cost"].get("currency")) and before["cost"].get("currency") == after["cost"].get("currency")
    normalized = {metric: {"before": 0.0, "after": 0.0, "supported": bool(a) and set(a) == set(b)} for metric in METRICS}
    total_before = len(before["run_rows"])
    for key in keys:
        left, right = a.get(key, []), b.get(key, [])
        record = {"stratum": dict(zip(strata, json.loads(key))), "before_n": len(left), "after_n": len(right),
                  "before_outcomes": dict(Counter(row.get("outcome") for row in left)),
                  "after_outcomes": dict(Counter(row.get("outcome") for row in right)), "metrics": {}}
        if paired:
            if not left or not right:
                raise MeasurementError("Paired comparison needs identical strata and complete pair sets")
            pair_sets = []
            for rows in (left, right):
                entries = {}
                for row in rows:
                    if not row.get("pair_key") or row["pair_key"] in entries:
                        raise MeasurementError("Paired comparison needs nonempty unique pair_key within each stratum")
                    entries[row["pair_key"]] = row
                pair_sets.append(entries)
            if set(pair_sets[0]) != set(pair_sets[1]):
                raise MeasurementError("Paired comparison has missing pair keys")
            for pair_id in pair_sets[0]:
                paired_count += 1
                x, y = pair_sets[0][pair_id], pair_sets[1][pair_id]
                for field in ("tested_sha", "test_manifest_sha256"):
                    if not x.get(field) or x[field] != y.get(field):
                        raise MeasurementError(f"Paired input evidence missing/different: {field}")
                for metric in METRICS:
                    if (metric != "estimated_cost" or cost_comparable) and x.get(metric) is not None and y.get(metric) is not None:
                        paired_deltas[metric].append(y[metric] - x[metric])
        for metric in METRICS:
            dist_a = distribution([row.get(metric) for row in left])
            dist_b = distribution([row.get(metric) for row in right])
            comparable = bool(left and right) and dist_a["n"] == len(left) and dist_b["n"] == len(right)
            if metric == "estimated_cost" and not cost_comparable:
                comparable = False
            change = dist_b["mean"] - dist_a["mean"] if comparable else None
            record["metrics"][metric] = {"before": dist_a, "after": dist_b,
                "missing_before": len(left) - dist_a["n"], "missing_after": len(right) - dist_b["n"],
                "mean_change": change,
                "relative_mean_change": change / dist_a["mean"] if comparable and dist_a["mean"] else None}
            if not comparable:
                normalized[metric]["supported"] = False
            elif total_before:
                weight = len(left) / total_before
                normalized[metric]["before"] += weight * dist_a["mean"]
                normalized[metric]["after"] += weight * dist_b["mean"]
        results.append(record)
    for metric, record in normalized.items():
        if not record["supported"]:
            record.update(before=None, after=None, relative_change=None)
        else:
            record["relative_change"] = record["after"] / record["before"] - 1 if record["before"] else None
    return {"schema": COMPARE_SCHEMA, "definitions": DEFINITIONS, "unit": "original workflow run, all observed attempts",
            "mode": "declared paired input evidence" if paired else "observational",
            "strata": list(strata), "cost_basis": "constant-rate estimate" if constant_rates else "different/absent rate cards",
            "before_counts": before["counts"], "after_counts": after["counts"], "flags": flags,
            "stratum_results": results, "baseline_weighted_means": normalized,
            "paired_differences": {metric: {**distribution(paired_deltas[metric]), "expected_pairs": paired_count,
                "missing_pairs": paired_count - len(paired_deltas[metric]),
                "supported": bool(paired_count) and len(paired_deltas[metric]) == paired_count} for metric in METRICS} if paired else None,
            "limitations": ["No statistical significance or causal improvement is asserted.",
                            "Demand includes all outcomes; changed failure/cancellation mix can change means without faster equivalent work.",
                            "Compare missing verdicts, queue/feedback, quality and peak-load evidence separately.",
                            "Per-run means are not per-candidate costs when triggers duplicate work."]}


def emit(value, output=None, forbidden_roots=()):
    if output is None:
        print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))
        return
    path = external_destination(output)
    if any(path.is_relative_to(Path(root).resolve()) for root in forbidden_roots):
        raise MeasurementError("Do not write reports inside immutable captures")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    write_json(path, value)
    print(f"Wrote {path}", file=sys.stderr)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--version", action="version", version=VERSION)
    commands = result.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect", help="Capture a run-created UTC cohort with read-only gh GETs")
    collect.add_argument("--repo", required=True, help="OWNER/REPO")
    collect.add_argument("--start", required=True, help="Inclusive whole-second UTC timestamp")
    collect.add_argument("--end", required=True, help="Exclusive whole-second UTC timestamp")
    collect.add_argument("--out", required=True, help="New absolute directory outside Git")
    collect.add_argument("--host", default="github.com")
    collect.add_argument("--api-version", default=API_VERSION)
    summary = commands.add_parser("summarize", help="Verify and summarize a capture; default output is JSON stdout")
    summary.add_argument("capture")
    summary.add_argument("--rates", help="Explicit ci-health.rates/v1 JSON")
    summary.add_argument("--evidence", help="Optional ci-health.evidence/v1 JSON keyed by run ID")
    summary.add_argument("--out", help="New absolute JSON path outside Git and the capture")
    comparison = commands.add_parser("compare", help="Compare compatible complete summaries without causal claims")
    comparison.add_argument("baseline")
    comparison.add_argument("candidate")
    comparison.add_argument("--strata", default=",".join(STRATA))
    comparison.add_argument("--paired", action="store_true", help="Require matching declared SHA/test manifest evidence for every pair")
    comparison.add_argument("--out", help="New absolute JSON path outside Git")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "collect":
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo) or any(part in (".", "..") for part in args.repo.split("/")):
                raise MeasurementError("Repository must be OWNER/REPO")
            if not re.fullmatch(r"[A-Za-z0-9.-]+", args.host) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.api_version):
                raise MeasurementError("Invalid host or API version")
            start, end = timestamp(args.start, boundary=True), timestamp(args.end, boundary=True)
            if end <= start or end > datetime.now(timezone.utc):
                raise MeasurementError("Window must have start < end and a past/frozen end")
            destination = external_destination(args.out)
            api = GitHub(args.host, args.api_version)
            manifest = Collector(api, destination, args.repo, start, end, args.host, args.api_version).execute()
            print(json.dumps({"capture": str(destination), "complete": manifest["complete"], "issues": manifest["issues"]}, indent=2))
            return 0 if manifest["complete"] else 2
        if args.command == "summarize":
            manifest, data = load_capture(args.capture)
            report = summarize(manifest, data, read_json(args.rates) if args.rates else None, read_json(args.evidence) if args.evidence else None)
            report["provenance"] = {"capture_manifest_sha256": digest(Path(args.capture) / "capture.json"),
                "rate_file_sha256": digest(args.rates) if args.rates else None,
                "evidence_file_sha256": digest(args.evidence) if args.evidence else None}
            emit(report, args.out, (args.capture,))
            return 0 if report["complete"] else 2
        report = compare(read_json(args.baseline), read_json(args.candidate), tuple(args.strata.split(",")), args.paired)
        report["provenance"] = {"baseline_sha256": digest(args.baseline), "candidate_sha256": digest(args.candidate)}
        emit(report, args.out)
        return 0
    except (MeasurementError, OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"ci-health: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        sys.exit("ci-health requires Python 3.11 or later")
    sys.exit(main())
