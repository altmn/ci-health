# Measurement contract and baseline

Use this for baseline or post-change collection. For collector commands and exact machine-readable schemas, read [helper-schema.md](helper-schema.md). For experiment design and rollout decisions, use [experiments.md](experiments.md).

## Define what a number means

Freeze explicit repositories, workflow identities, events, UTC half-open bounds `[start,end)`, candidate identity, policy version, outcome filters, and exclusions. Distinguish PR head, tested merge candidate, and the tree actually checked out. Two to four representative weeks is a starting collection plan, not proof of statistical sufficiency. Include busy periods, failures, dependency changes, and warm/cold caches; extend or use matched replay when volume is low.

Keep two different ledgers:

- **Activity:** execution and resources inside a calendar interval, including retries of older runs. Intersect execution spans with the interval for utilization. Follow the provider's accounting boundaries for money.
- **Candidate cohort:** candidates admitted during the interval, followed through their attempts and outcomes. This measures how much demand and delay those changes created. GitHub's run-created cohort is only an approximation to candidate admission, especially for reruns and multiple workflows per candidate.

A run-created query cannot discover all execution activity in that period. Cohort totals can extend past the cohort's end. State the capture cutoff and unsettled population; do not call those totals a reconciled monthly bill.

## Minimum dashboard

| Measure | Definition | Interpretation trap |
|---|---|---|
| Arrivals | Distinct eligible candidates/hour, plus workflows and jobs/candidate | More jobs can be fanout rather than more changes |
| Useful throughput | Valid qualifications and actionable rejections/hour for distinct candidates | Infrastructure errors are neither |
| Eligible queue | Eligibility to allocation/start, by compatible pool | Prerequisite, approval, concurrency, and provisioning waits need separate clocks |
| Backlog | Eligible count, oldest age, age distribution; pending unresolved work | Completed-job percentiles hide starvation |
| Feedback | Admission to first actionable product failure; admission to all required valid evidence | Runner crash is not useful early failure; summing parallel jobs is wrong |
| Revision-to-green | Candidate admission to valid successful verdict across attempts | Include unresolved/superseded counts and waiting for retries |
| Final-revision readiness | Last submitted candidate to valid verdict | Complements all-revision demand; does not replace it |
| Service demand | Sum physical runner-seconds, allocated vCPU-seconds, by pool/SKU and outcome | Allocation is not active CPU usage; runner time is not wall time |
| Phase time | Checkout, restore, install, build, collection, tests, transfer, teardown | Overlapping phases do not add to elapsed duration |
| Resources | CPU/throttle, process-tree memory, OOM, disk/IO, network, service pressure | Parent RSS misses child processes; host and container limits differ |
| Capacity | Busy slot-seconds / usable offered slot-seconds, request-to-ready time, failed boots | Low utilization can mean routing mismatch; high utilization can worsen tails |
| Amplification | Attempts/initial job, test retries, obsolete runner-seconds, setup fraction | Retry and obsolete categories overlap; do not add their shares |
| Reliability | First-pass, retry-pass, product failure, infrastructure failure, unknown cause, missing verdict | Retry-pass alone does not prove a flaky test |
| Freshness/quality | Age and revision distance of full qualification; omitted regressions, escapes, required evidence | Latest green workflow may concern the wrong revision or only part of the suite |
| Cost | Metered or estimated amount, total and per candidate | Keep currency, rates, inclusion scope, and accounting basis explicit |

For each distribution retain raw observations, population and outcome filter, count, p50, and a tail such as p95. Use means for additive demand calculations. Do not average daily percentiles to obtain a weekly percentile. Small tail samples are unstable; give uncertainty rather than false precision. [Google SRE monitoring](https://sre.google/workbook/monitoring/)

Failed, cancelled, skipped, and incomplete work need separate populations. Include known consumption in total demand, but do not score cancellation as completed successful feedback. A cancelled interval is censored for successful-completion analysis. Missing timestamps are unknown, not zero. An SLO denominator must include eligible candidates that have exceeded the deadline without a verdict; document supersession policy and rate.

## Delivery clocks and acceptance

Name both endpoints before comparing latency. Candidate push/event → required verdict measures PR feedback; protected push/merge → last required live smoke and identity check measures staging readiness. If the requirement is a sealed release, follow the publisher through actual publication and verify the source-bound artifact. For GitHub releases, retain the release API's `published_at` and release/asset identity rather than substituting a tag, draft creation, preparation completion, or workflow finish. [Release API](https://docs.github.com/en/rest/releases/releases#get-a-release)

PR arrival → publication additionally includes time waiting for merge. Keep that whole change-cycle clock alongside PR and protected-push clocks when the user asks about the full experience. Label run-created proxies when push timestamps are unavailable. Configuration activation, staging, artifact publication and production promotion are separate outcomes; none implies another. An observed first-attempt success qualifies its named scenario, not an arbitrary future cloud worst case or a tail percentile. Carry missing scenarios and observed budget margin in the [acceptance ledger](experiments.md#scenario-acceptance-ledger).

## Evidence to retain

Keep append-only raw captures, normalized row data, calculation version, configuration snapshot, and a checksum inventory. A Markdown summary alone is not a reproducible baseline.

| Dataset | Identity and essential fields |
|---|---|
| Candidates | Repository, head/base/tested tree, event/admission origin, final/superseded state, required-policy hash |
| Runs/attempts | Physical run ID and attempt, stable workflow path/ID and hash, event, source SHA, status/conclusion, recorded timestamp origin |
| Jobs | Physical job ID; stable logical task and matrix; dependencies; eligible/start/end origins; pool, labels, image, architecture, cores/RAM; outcome |
| Steps | Job and phase ID, monotonic duration, exit status, nonoverlap model, transferred bytes, restore exact/prefix/miss and save time |
| Tests | Stable test ID including project/runtime/platform; separate execution attempt; discovered/selected/executed state, duration/outcome/seed, failure signature, manifest hash |
| Capacity/resources | Pool and sample time; queued/ready/running/offline counts, oldest age, provision events; process-tree/container telemetry and sampling overhead |
| Costs | Original accounting row, provider/SKU/unit/quantity/date/currency, amount, exact/estimated/allocated label, dated rate card |
| Quality | Failure episode classification, contract, first detection, retry evidence, quarantine owner/expiry, selector miss or escape, repair |

Record `git rev-parse HEAD` inside the job and hash effective configuration and inventories. API `head_sha`, branch name, or dispatch parameter cannot prove an overridden checkout tested that tree. Do not put secret values in fingerprints. Test-runner retries, job retries, and whole-workflow reruns are separate demand sources; only some appear in provider attempt counters.

Store raw evidence outside source control or in a verified ignored directory with appropriate access restrictions. An ignore rule does not make already tracked evidence private. Private repository names, branches, job labels, authors, and internal URLs may be sensitive even without logs.

## GitHub Actions collection

Use an existing authenticated `gh`; collecting private run/job records requires Actions read access. Billing permissions are separate. Start with `ci_health.py collect --help` and [helper-schema.md](helper-schema.md), choose an explicit evidence directory outside the repository, and preserve every capture. The helper only makes GET requests and does not download logs/artifacts or provision capacity.

The [workflow runs API](https://docs.github.com/en/rest/actions/workflow-runs) caps filtered searches at 1,000 results. A complete collector splits time windows at the cap, fetches every page, checks counts, filters boundaries locally, and deduplicates. Splitting cannot fix an unsplittable capped interval; report it incomplete. Retrieve each attempt from 1 through the captured attempt number and all pages of [attempt-specific jobs](https://docs.github.com/en/rest/actions/workflow-jobs). Deduplicate physical job IDs across partial reruns; successful jobs carried forward are not another execution.

Audit the physical identity assumption too. If different API job IDs repeat the same prior success interval across attempts, reconcile logical matrix identity, source, runner and step intervals against the attempt boundary before counting another execution. Equal names or coincident timestamps alone do not justify collapsing jobs. The bundled helper deduplicates by job ID; it does not resolve reissued IDs. Preserve its raw capture and disclose or correct such accounting separately with a reproducible mapping instead of advertising unverified totals as physical demand.

Exclude runnerless, step-free skipped placeholders before interpreting their synthetic intervals; a negative placeholder is not negative resource use. A skipped conclusion with runner/step evidence is contradictory and needs investigation. Negative intervals on executed jobs or executed steps remain invalid; never clamp them to zero. Keep raw provider records unchanged.

Retain each request's retrieval time and errors. Recheck attempts/status after extraction; concurrent reruns or status changes make a capture unsettled, and later reruns require a new immutable capture. An API-success response does not prove retention completeness. Preserve deletion, permission, and retention gaps explicitly. Use bounded retry/backoff for rate limits and temporary failures; stop on durable access errors or a collection budget limit.

**Do not fabricate clocks.** `created_at` is not a new admission timestamp for every rerun. `run_started_at` is not the trigger time. `updated_at` is not a documented immutable completion clock. Observed job `started_at`/`completed_at` intervals support an execution proxy, not exact provider billing intervals. Neither a generic run-start gap nor predecessor end subtraction establishes eligible queue delay. Collect queued/in-progress/completed events, dependency/approval/concurrency history, and autoscaler events; record event time, receipt time, and ingestion lag separately.

For a required verdict across partial reruns, assemble valid successes from previous attempts according to policy and add replacement outcomes. Resource accounting counts each physical execution once; proof assembly is a different calculation. Avoid the deprecated run/workflow `/timing` endpoints. [Deprecation notice](https://github.blog/changelog/2025-02-02-actions-get-workflow-usage-and-get-workflow-run-usage-endpoints-closing-down/)

## Measure inside execution and the runner pool

Use monotonic command spans and UTC correlation timestamps. Preserve the command's exit status through log pipelines. Observe child processes and post-job hooks. Failed optional telemetry should mark a telemetry gap while retaining the real test result; a missing required proof report must prevent qualification.

Separate framework test time from discovery, transforms, global fixtures, teardown, reporting, and uploads. Sample lightweight resource and capacity metrics first; profile diagnostic runs to reduce observer effects. Capture throttling and pressure as well as average utilization. [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)

At each compatible pool, retain periodic ready/running/offline/queued counts and oldest age. Split demand-to-provision-request from request-to-ready. A timeout inside the job cannot limit waiting before allocation; verify the provider's queue/provision timeout semantics. [Jenkins stage timeout semantics](https://www.jenkins.io/doc/book/pipeline/syntax/)

## Cost without misleading arithmetic

Price each physical execution before summing. With occupied duration `d`, quantum `q`, minimum billable seconds `m`, and rate per minute `r`:

```text
runner_minutes = sum(d / 60)
allocated_vCPU_minutes = sum(d * allocated_cores / 60)
estimated_compute = sum(ceil(max(d,m)/q)*q / 60 * r)
```

The helper applies the minimum before quantum rounding, as shown; verify that this matches the provider's rule and billing boundary, or calculate incompatible pricing separately. Record rate-card date, effective period, currency, SKU mapping, minimum, and quantum. Ambiguous or missing mapping produces unknown cost, not free execution. Label this job-interval estimate; retain provider-metered amounts separately. Current GitHub hosted pricing rounds per job to minutes, but verify the applicable service and deployment. [Runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)

Include recurring image preparation, idle provisioned self-hosted capacity, failed boots, storage, transfer, registries, remote builds, live API/model calls, and operations effort where relevant. Distinguish spend from labor/opportunity allocation. Quantify reduced demand even when commitments make the immediate bill unchanged. GitHub's [billing reports](https://docs.github.com/en/billing/reference/billing-reports) are aggregated exports; reconcile only at their supported grain.

For before/after, show observed-rate money and a common rate card to separate price effects from resource savings. Do not use a different set of recognized runner SKUs in each total without reporting coverage. Unknown rows may dominate the result.

## Freeze the baseline and repeat after the change

Suggested external evidence layout:

```text
baseline/
  manifest.json       # scope, clocks, definitions, capture cutoff, versions
  raw/                # immutable provider responses and billing exports
  normalized/         # rows and stable identities
  inventories/        # discovered, selected, scheduled, executed and reused proof
  timelines/          # queue, dependency, provisioning and critical path
  analysis/           # scripts, rate cards, environment/workload labels
  summary.md          # totals, distributions, unknowns, quality and confidence
  checksums.sha256
```

Record baseline and candidate source/workflow hashes, exact changes, runner capacity/image, worker/shard configuration, test manifest, cache state, external incidents, and required-check policy. Reapply the same definitions and collection rules after optimization. Keep raw observed results separate from normalized or modelled comparisons. If a workflow/job was renamed, supply a reviewed logical-identity mapping instead of treating names as equivalent automatically.

## Portable collection for other CI systems

Use native APIs/events and the same measurement contract; the bundled collector is GitHub-specific. GitLab: retain parent/child and retried jobs, runner tags, pending/resource-group waits, and artifacts before expiry. Jenkins: retain queue items, agent allocation, stage spans, executor inventory, and controller restarts. Buildkite/CircleCI/Azure: distinguish scheduled jobs, approvals, retries, provisioning, and compatible pool limits. Verify current timestamp and billing semantics in the deployment's official documentation; do not transplant GitHub field meanings.
