# Qualify an optimization and measure its result

Use after identifying a supported bottleneck and before changing execution policy. Read [measurement.md](measurement.md) for collection and accounting definitions; use [selection-and-reuse.md](selection-and-reuse.md) when changing validation scope. The primary outcome is sustainable, timely, trustworthy feedback. Cost and total runner demand support that outcome.

## 1. Freeze the experiment contract

Write the hypothesis, mechanism, affected pools, baseline/candidate identities, primary metric, minimum useful effect, quality/latency/freshness limits, stopping rule and rollback owner **before** inspecting candidate results. Do not select favorable thresholds afterward.

Preserve the baseline's raw inputs, required-contract inventory, discovered/selected/executed test manifests, calculation version and missing-data report. Freeze a UTC `[start, end)` window and distinguish:

- **Activity:** resources consumed inside the window, including retries of older runs.
- **Revision cohort:** candidates admitted inside the window, followed through all attempts and outcomes.

Never compare activity totals from one arm against cohort totals from another. Keep superseded, unfinished, failed and cancelled populations visible under the same rules.

## 2. Use two complementary evaluations

| Evaluation | Establishes | Does not establish alone |
|---|---|---|
| Matched replay of representative revisions/workloads | Effect on setup, service demand, execution and proof completeness | Peak-hour queue improvement on a busy fleet |
| Production pilot or representative arrival trace | Effect on backlog, prioritization, autoscaling and required-verdict latency | Causal attribution if traffic, scope or infrastructure also changed |

Pair equivalent revisions/workloads. Interleave or randomize execution order; block by runner class, platform, cache state and workload size. Prevent one arm's cache writes from silently warming the other. Record tool/image/dependency drift. For coupled changes, report the bundle rather than inventing separate effects. [NIST paired observations](https://www.itl.nist.gov/div898/handbook/prc/section3/prc311.htm), [NIST randomized blocks](https://www.itl.nist.gov/div898/handbook/pri/section3/pri332.htm)

Include leaf changes, shared-code changes, lockfiles, test-only changes, global configuration, full/release validation, cold caches, platform-heavy work and peak periods. Keep new workload classes separate if no baseline counterpart exists.

## 3. Reject misleading comparisons

| Apparent gain | Check before accepting |
|---|---|
| Candidate finishes sooner | Did it fail early, time out, omit a shard or discover zero tests? |
| Lower weekly runner total | Did fewer revisions arrive or did the workload mix change? |
| Better p95 among completed jobs | Did old jobs remain queued, become cancelled or lose their verdict? |
| Fewer failures | Was required detection removed or first failures hidden by retries? |
| Faster cache hit | Include lookup, restore, validation, save, misses and recurring maintenance |
| Lower execution time | Was work shifted into queueing, preprocessing, another workflow or external service? |
| Same overall coverage percentage | Were distinct contracts, platforms, failure paths or assertions lost? |
| Cheaper runner | Did service slowdown increase busy-hour queueing and feedback tails? |

A cancelled or early-failing run contributes to resource and reliability accounting. Its truncated duration is not an equal completed-work speed measurement. Do not silently drop it; report separate comparable-completion and all-outcome views.

## 4. Analyze effects with uncertainty

Report baseline and candidate absolute values, differences, relative changes, sample counts, outcomes and uncertainty for:

- Mean occupied runner demand per comparable candidate, amplification and retry/supersession demand.
- Eligible queue p50/p95, oldest age, backlog growth/drain and useful verdict throughput.
- Required-verdict p50/p95, first actionable failure and unresolved-candidate count.
- First-pass reliability, missing proof, independent omission/false-green incidents and qualification freshness.
- Consistently metered or labelled estimated cost, including recurring audit/fallback/telemetry overhead.

Use means for additive demand calculations. Recompute quantiles from observations or compatible histograms; do not average daily or class p95s. [Google SRE monitoring](https://sre.google/workbook/monitoring/)

For paired data, analyze prespecified per-pair differences or ratios. Resample at a defensible independent unit, such as revisions/PRs or time blocks; sibling shards are not independent experiments. Preserve pairing during resampling. Tail claims need enough observations; a p99 from a few dozen successful runs is unstable. Avoid repeated peeking followed by stopping at the first favorable result.

Normalize **mean** demand or cost to declared baseline class weights when useful:

```text
before = sum(weight[k] * mean_before[k])
after  = sum(weight[k] * mean_after[k])
relative_change = after / before - 1
```

Weights sum to one and describe the same covered classes. A zero baseline makes the ratio undefined. State missing/new classes and confounders. This weighting does not remove unmeasured differences. For normalized tails, compare weighted distributions, not weighted class percentiles. Never divide organization-wide resources by commits from one repository.

### Demonstrate quality preservation rather than assume it

Specify a tolerable deterioration margin for each guardrail before running the experiment. For a harmful quantity such as latency or first-pass failure rate, define `difference = candidate − baseline`; acceptance requires enough evidence that its upper uncertainty bound stays within the chosen margin. A nonsignificant difference is not proof of noninferiority. Do not claim equivalence from a small sample with wide bounds.

Mandatory contract omission, stale proof and gate bypass are correctness failures, not tradeable average performance. For stochastic detection changes, use explicit risk policy and independent regression episodes; zero observed misses only describes the observed sample. Qualify selection and test deletion using the negative cases and full-suite comparisons in [selection-and-reuse.md](selection-and-reuse.md).

## 5. Validate overload and recovery

Use bounded ordinary/peak arrival traces within authorized test environments; synthetic workloads must not deploy or alter production fixtures unintentionally. Measure service-time inflation, downstream saturation, retry demand, autoscale delay, oldest queue age, throughput and post-burst drain time.

For a roughly homogeneous system, backlog `Q` drains approximately in `Q / (completion capacity − ongoing arrival rate)` when the denominator is positive. Keep units consistent and compare the estimate with observation. Priority classes, variable jobs and unavailable pools can invalidate the approximation.

Exercise runner loss, cold caches, temporary dependency outage, delayed report and missed scheduled validation. Verify bounded retries and continued progress for required broader validation under urgent load. An empty queue caused by discarded events is not recovery. [Google SRE cascading failures](https://sre.google/sre-book/addressing-cascading-failures/)

## 6. Roll out with explicit stop conditions

Proceed only within the user's authorized scope. Separate shadow observation, limited enforcement and expanded rollout. Keep rollback simple: preserve the previous configuration and identify the specific mechanism to disable.

Label stabilization separately, then collect matched business cycles with unchanged definitions/instrumentation. Reconcile metering when provider exports arrive. Accept only if required proof remains correct, the intended benefit meets its useful threshold, guardrails remain within limits and maintenance burden is acceptable.

Rollback/correct promptly for mandatory omissions, false greens, unsafe reuse or trust-boundary failures. For performance regression, use predeclared thresholds with context; avoid oscillating on noisy single runs. An inconclusive result supports more evidence or a simpler change, not a success claim. Preserve unsuccessful experiments and counterexamples.

## Compact records

### Experiment

```yaml
id: REPLACE
owner: REPLACE
confirmed_bottleneck_and_evidence: REPLACE
hypothesis_and_changed_mechanism: REPLACE
baseline_identity_and_data: REPLACE
candidate_identity_and_data: REPLACE
scope_pools_events_workload_strata: REPLACE
primary_metric_and_minimum_useful_effect: REPLACE
quality_latency_freshness_limits: REPLACE
noninferiority_margin_and_uncertainty_method: REPLACE
pairing_randomization_cache_controls: REPLACE
outcome_retry_supersession_inclusion_rules: REPLACE
sample_and_stopping_rule: REPLACE
negative_cases_and_expected_results: REPLACE
rollout_stages_and_authorized_scope: REPLACE
rollback_trigger_owner_and_procedure: REPLACE
```

### Decision scorecard

| Measure | Baseline | Candidate | Difference / uncertainty | Population / evidence |
|---|---|---|---|---|
| Peak arrivals and jobs/attempts per candidate | unknown | unknown | unknown | |
| Mean runner demand per candidate | unknown | unknown | unknown | |
| Queue p95, oldest age, drain time | unknown | unknown | unknown | |
| Required-verdict p50/p95 and unresolved count | unknown | unknown | unknown | |
| Valid verdict throughput | unknown | unknown | unknown | |
| First-pass reliability and retry demand | unknown | unknown | unknown | |
| Missing proof / confirmed omission incidents | unknown | unknown | unknown | |
| Full-validation freshness | unknown | unknown | unknown | |
| Recurring cost and audit overhead | unknown | unknown | unknown | |

Add raw-data location, analysis revision, completeness, negative-case results, remaining confounders and decision: **keep / expand pilot / inconclusive / revert**. Unknown is not zero.

## Maintain the result

During overload, watch arrivals/completions, oldest age, verdict coverage and retry demand by pool. Weekly, inspect new amplification, flaky signatures, critical waits and qualification freshness. After toolchain/image/graph changes, repeat relevant invalidation, selection, cold-start and gate challenges. Periodically requalify exclusions, quarantine and policy exceptions; expire temporary workarounds and record the next baseline identity.
