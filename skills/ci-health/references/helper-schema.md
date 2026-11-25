# GitHub measurement helper: CLI, schemas and limits

The bundled `scripts/ci_health.py` uses Python 3.11+ standard library modules. Collection also needs an installed, already authenticated GitHub CLI (`gh`) and Git (`git`, used only to verify external output locations). It does not install software, sign in, request credentials, change workflows, rerun jobs, or download logs/artifacts. Its network operations are explicit GitHub API GETs through `gh`.

The helper measures **original workflow runs created in a UTC interval, with all attempts observed during capture**. This is a run-created cohort, not a complete activity/billing window or a per-candidate ledger. Multiple workflow runs can belong to one revision. A rerun of an older run is outside this cohort even if its execution occurs during the interval.

## Commands

Replace the helper path, repository and dates. Every `--out` must be a new absolute path outside all Git repositories, including ignored directories. All outputs must also be outside existing capture directories; nesting another capture/report would change their immutable file inventory. The helper refuses overwrites. Use one capture directory per collection and one new filename per report.

```bash
CI_HELPER='/absolute/path/to/ci-health/scripts/ci_health.py'

python3 "$CI_HELPER" collect \
  --repo OWNER/REPO \
  --start 2026-01-01T00:00:00Z \
  --end 2026-01-08T00:00:00Z \
  --out /absolute/private-evidence/baseline-capture

python3 "$CI_HELPER" summarize \
  /absolute/private-evidence/baseline-capture \
  --rates /absolute/private-evidence/rates.json \
  --evidence /absolute/private-evidence/baseline-evidence.json \
  --out /absolute/private-evidence/baseline-summary.json

python3 "$CI_HELPER" summarize \
  /absolute/private-evidence/candidate-capture \
  --rates /absolute/private-evidence/rates.json \
  --evidence /absolute/private-evidence/candidate-evidence.json \
  --out /absolute/private-evidence/candidate-summary.json

python3 "$CI_HELPER" compare \
  /absolute/private-evidence/baseline-summary.json \
  /absolute/private-evidence/candidate-summary.json \
  --out /absolute/private-evidence/comparison.json
```

`--rates` and `--evidence` are optional; without them, cost and workload equivalence remain unknown. `summarize` and `compare` default to JSON on stdout. If redirecting stdout yourself, you are responsible for choosing an external destination; prefer `--out` to enforce the policy.

`collect` also accepts `--host` (default `github.com`) and `--api-version` (default `2026-03-10`). Use an API version supported by the target deployment. Authentication remains with `gh`; private repository collection needs Actions read access. Billing permissions are not used because this helper does not collect billing exports.

Window boundaries must be whole-second UTC timestamps with `Z` or `+00:00`, and `start < end <= now`. The internal cohort is `[start,end)`. GitHub search ranges are inclusive, so the query uses `start..end-minus-one-second`; returned records are checked against the requested interval. Future collection windows are rejected before network access or file creation.

Exit status is `0` for a successful command and `2` for invalid inputs, failed/incomplete collection, or incomplete summarization. An incomplete capture remains available for diagnosis. `compare` requires complete input summaries. A successful comparison can still contain unsupported metrics or confounding flags; inspect the report, not only its exit status.

## Collection and immutability

1. Read run searches in UTC partitions. At `total_count >= 1000`, recursively split the partition. Reconcile child unique counts against the known parent count/lower bound; underflow (for example, deletion during extraction) is incomplete. A capped one-second partition aborts with an incomplete result.
2. Read every page and compare record/unique-ID counts with the API count. Changed counts, duplicate IDs, invalid identities, missing pages and HTTP failures are errors, not empty data.
3. For each run, read attempts `1..run_attempt` and every page of each attempt's jobs. Physical jobs are deduplicated by job ID. `observed_in_attempts` preserves membership when a successful job is carried into a partial rerun.
4. After reading **all** runs' attempts/jobs, perform a final pass rechecking each run's attempt number, status, conclusion and `updated_at`. This catches an early run changing while later runs were fetched. Changes, nonterminal work and missing execution intervals make the capture incomplete. Each run's recheck records its own observation cutoff. This is internal consistency at those per-run cutoffs, not a transactional GitHub snapshot at `capture_finished_at`; an additional rerun can occur after its recheck. Collect a new capture to observe it.
5. Write exclusive raw files, normalized data, a capture manifest and SHA-256 checksums. No existing capture is amended. Summarization verifies the complete file/checksum set, declared counts, cohort bounds, unique identities, job-to-attempt references and terminal completeness.

Transient HTTP 429/5xx and explicitly identified rate-limit 403 responses get at most four attempts with bounded 1/2/4-second backoff. This is **not Retry-After-aware**; a longer rate limit leaves an incomplete capture and should be retried later into a new directory. Other API errors stop collection. Each subprocess has a 90-second timeout. No unbounded background polling occurs.

```text
capture-directory/
  capture.json
  normalized.json
  raw/
    000001.json
    000002.json
    ...
  checksums.sha256
```

The helper does not overwrite these files; it does not make them filesystem-immutable or cryptographically authenticate GitHub. Checksums detect accidental modification, not a person who edits both data and checksums. Capture directories are created with private permissions and JSON files with mode `0600`; existing parent-directory/access policies still apply. Raw responses can contain private repository names, PR metadata, actor names and runner identifiers. Do not publish them with the skill or attach them to public issues without reviewing/redacting them.

## Capture schema

`capture.json` uses `ci-health.capture/v1`:

| Field | Meaning |
|---|---|
| `collector_version` | Helper release version; currently `0.1.2` |
| `definitions` | Metric contract; `run-created-cohort-demand/v1` |
| `cohort` | `run-created-half-open-all-observed-attempts` |
| `repository`, `host`, `api_version` | Explicit API target and version |
| `start_inclusive`, `end_exclusive` | Original run creation boundaries |
| `capture_started_at`, `capture_finished_at` | Local retrieval bookkeeping, not workflow clocks or an atomic as-of snapshot |
| `run_rechecks` | Per-run final observation timestamp and observed attempt/status/conclusion/update fields |
| `complete` | Required reads were internally consistent and observed work terminal at each run's final recheck |
| `issues` | Codes/details for incomplete collection |
| `counts` | Runs, attempts, deduplicated physical jobs and raw responses |

`normalized.json` contains `runs`, `attempts`, and `jobs`. Runs and attempt records retain their API metadata. Jobs retain ID/run/name/status/conclusion, execution timestamps, labels, runner identifiers, head SHA, steps and observed attempt membership. The raw envelope separately preserves request endpoint/query, observation time and original JSON body. No authorization headers or token values are deliberately captured.

Release versions describe the code release; schema/definition versions describe data compatibility. Compatible helper patch releases can share these schema versions. A change to cohort/metric meaning requires a new definitions version; comparison rejects mismatches.

## Summary semantics

The report uses `ci-health.summary/v1` and retains capture provenance, counts, issues, window, cost basis and one `run_rows` entry per original run. When a capture is incomplete, observed counts and known seconds remain useful diagnostics, but complete total demand and per-run totals are null. The entire incomplete capture is treated conservatively; no partial per-run total is advertised as complete.

- `runner_seconds`: sum of valid physical job `completed_at − started_at` across all observed attempts and outcomes. A carried-forward success is counted once. This is execution demand, not workflow elapsed time or eligible queue delay.
- Cancelled jobs contribute their observed consumed seconds. Their duration is censored relative to natural completion and appears in its own outcome distribution.
- Skipped jobs are not executed jobs, even when the API supplies placeholder timestamps. They have no duration observation. Their execution cost is zero because they did not execute; this does not invent a zero timing observation.
- Missing/invalid durations stay unknown or cause a validation error. Failed, timed-out, cancelled and successful durations have separate distributions.
- Steps have separate outcome counts/distributions. A skipped step is not a timing sample. Step intervals are not summed into workflow time; they can omit overhead or overlap.
- Distributions include `n`, mean, min/max and nearest-rank p50/p95 (`sorted_values[ceil(p*n)-1]`). Empty distributions have null statistics. Small N does not establish stable tail behavior.
- `executed_jobs` counts physical jobs with an execution start, excluding skipped jobs. Test retries inside a job are not separately observable and must be collected from test evidence.
- Per-run demand includes all attempts, so it answers cost/service per original workflow run, not per PR, tested revision or valid verdict. Obtain candidate mappings manually before reporting those other denominators.

The helper does not infer exact eligible queue, required-verdict, approval wait, retry admission, actual checked-out tree or billing timings from REST. In particular, `created_at`, `run_started_at`, and `updated_at` are not interchangeable clocks. Use separate event/provider/test evidence and the skill's measurement templates for these questions.

## Explicit rate-card schema

There are no default runner prices. Example inputs below are **invented**, not vendor rates:

```json
{
  "schema": "ci-health.rates/v1",
  "currency": "USD",
  "effective_date": "2026-01-01",
  "rates": [
    {
      "id": "example-linux",
      "labels_all": ["ubuntu-latest"],
      "labels_none": ["self-hosted"],
      "per_minute": "0.01",
      "quantum_seconds": 60,
      "minimum_seconds": 0
    }
  ]
}
```

Every entry needs a unique ID, a nonempty `labels_all`, a nonnegative per-minute price, a positive billing quantum, and an optional nonnegative minimum (default zero). Labels match exactly and case-sensitively. All `labels_all` must occur and no `labels_none` may occur. **Exactly one entry must match.** Overlapping entries are ambiguous, not priority ordered; unmatched/ambiguous jobs have unknown cost. Runner labels can be insufficient to identify a real billing SKU; leave that cost unknown until there is adequate mapping evidence.

The estimate's contract is:

```text
billable_seconds = ceil(max(observed_job_seconds, minimum_seconds)
                        / quantum_seconds) * quantum_seconds
estimated_job_cost = billable_seconds / 60 * per_minute
```

Thus the minimum is applied before rounding to the quantum. Pricing uses decimal arithmetic per job and JSON numeric totals. Estimates do not include storage, transfer, idle infrastructure, discounts, allowances, taxes, operations or different provider-meter boundaries. Record these separately. A provider with incompatible minimum/rounding semantics needs a separate estimator; do not force it into this schema.

`effective_date` documents the supplied rate-card snapshot. It does not automatically select historical prices by job date. Applying one card to both periods is an explicit constant-rate valuation. Using different cards is allowed but flagged as a combination of usage and price changes. Different currencies are never subtracted; no FX conversion is performed. `known_estimated_cost` is only the priced subset; `total_estimated_cost` is null if any executed job is unpriced or the capture is incomplete.

## Optional workload and pairing evidence

Evidence is supplied by the investigator, not inferred from PR titles or branch names:

```json
{
  "schema": "ci-health.evidence/v1",
  "runs": {
    "123456789": {
      "workload_label": "leaf-change-warm-linux",
      "pair_key": "replay-case-17",
      "tested_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "test_manifest_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    }
  }
}
```

Each field is optional for ordinary summarization. Run IDs outside the capture are rejected. Hashes must be full hexadecimal hashes (40/64 characters for the tested Git SHA, 64 for a SHA-256 manifest). `tested_sha` should come from the actual checkout; `test_manifest_sha256` should identify a canonical inventory of test/project/runtime/platform inputs. Pair labels are investigator declarations, not proof that hidden dependencies, environment or quality were equivalent.

Use `compare --paired` only for controlled replay. Within every stratum, both sides need identical unique pair-key sets and matching nonempty tested SHA/test-manifest hash. Missing pairs or incompatible evidence reject the paired comparison. Per-metric differences include expected/observed/missing pair counts and a `supported` flag; missing metric values or incompatible cost currency never produce a complete paired estimate. No significance test or automatic causal conclusion is made.

## Comparison contract

`compare` accepts complete compatible summaries for the same repository, host, cohort and definition version. Default strata are `workflow_path,event,runner_labels,workload_label`. `runner_labels` is the sorted union of labels observed across that run's jobs, not a verified hardware/image identity.

Before calculation, it validates the summary structure, literal `complete: true`, empty collection issues, unique positive run IDs, reconciled run/physical-job counts, rate-card currency, and finite nonnegative metrics. Job counts must be integers. Required metric fields must be present; explicit null values remain unknown and disable the affected comparison. Malformed summaries fail with exit status 2 before any comparison report is written. This structural validation accepts the existing v1 summary format, including 0.1.0 reports; it does not authenticate their source or detect consistently fabricated evidence. Retain the original checked captures.

Use `--strata workflow_path,event,workload_label`, for example, when runner labels intentionally change during the experiment; the report flags the omitted runner stratification. Explain the intended infrastructure change and retain its measurements separately. Allowed fields are precisely the four default fields. Unknown workload labels remain explicit null strata.

The report includes per-stratum counts, outcome counts, distributions, missing metric counts, changes in means, and means weighted by baseline run proportions:

```text
normalized_before = sum(baseline_weight[k] * mean_before[k])
normalized_after  = sum(baseline_weight[k] * mean_after[k])
relative_change   = normalized_after / normalized_before - 1
```

Any missing/new stratum makes the overall normalized comparison unsupported; no common-strata subset is silently renormalized. A missing metric disables normalization for that metric. Zero baselines yield an undefined/null relative change. Per-stratum results remain visible for diagnosis. Percentiles are never averaged across strata. Comparisons are observational unless declared paired inputs pass validation; neither mode proves that required checks, quality, queue behavior, workload size or deployment conditions were equivalent.

To distinguish usage changes from rate changes, re-summarize **both original captures with exactly the same rate-card content** and compare those new summaries. Keep separate summaries using the original period cards if actual-period valuations are also useful. The comparison identifies its cost basis, preserves input hashes, and keeps negative improvements.

## Required evidence outside this MVP

Before claiming that an optimization relieved overloaded CI, also record offered/admitted arrivals, eligible queue age, capacity and autoscale timelines, exact required-check verdicts, missing-verdict counts, cold/warm cache state, full-validation freshness and regression detection. Include old-run retries in a separate activity ledger and reconcile costs against provider billing at its supported grain. Use matched workload/arrival-trace experiments and the skill's acceptance/rollback checklist.

This helper deliberately does not parse provider invoices, install agents, change settings, collect sensitive logs, resolve arbitrary dependency graphs, generate a test selector, or operate a standing monitor. Its purpose is reproducible read-only evidence and explicit measurement limits.
