# Preflight impact analysis

Use when a proposed change materially affects expensive CI execution. This is a bounded before/after review, not a requirement for historical collection or full-suite execution. Keep ordinary independent copy brief. Retain detailed receipts in the caller's chosen non-tracked evidence location; do not add private captures or candidate metadata to a public repository.

## Bind the reviewed state

Record the intended target, resolved merge base, HEAD, reviewed scope and exclusions. Include tracked committed/staged/unstaged changes and relevant non-ignored untracked inputs, with old/new paths for renames and deletions. A branch name or clean HEAD alone does not identify a dirty candidate.

Bind that state to a reproducible content identity: for example, base/HEAD plus a digest of the reviewed binary-capable tracked diff and a sorted manifest of relevant untracked paths, modes and content digests. Record symlink targets rather than following them into unrelated private content. An immutable snapshot that preserves equivalent information is also sufficient. Retain identities for relevant supporting inputs outside that snapshot. Honor an explicit caller scope and disclose excluded material inputs instead of silently broadening it.

Immediately before the next push, compare with the retained state. If a shared fixture changed after the first review, refresh that fixture's callers, consumers and affected work rows. A previous clean intermediate revision does not qualify the edited candidate. If only independent prose changed, update identity/scope and reuse completed rows. A ship helper reporting success does not establish that CI Health inspected these paths.

## Expand the actual work

Follow changed inputs through unchanged wrappers, lifecycle hooks, test bodies, fixtures and result consumers. For each family identify its event, effective command/mode, input cardinality, output and required consumer. Include generated inputs and source-scanning rules when imports alone do not capture dependency closure.

Use a sum of actual groups, multiplying only nested dimensions that really apply:

```text
group operations = applicable logical cases × inner states/routes × applicable projects × attempts
configured operations = sum of distinct groups
job work = preparation + execution + teardown + reporting + post work
required latency = longest valid dependency path, including relevant dispatch/queue/approval gaps
```

The first formula describes an operation when all listed dimensions apply to it; fixtures or launches may instead occur once per worker, suite or job. Count expensive navigations, reloads, screenshots, context launches, fixed waits and uploads at their actual scope. Apply project filters, conditional loops and skips. Discovery that already lists test/project entries must not be multiplied by projects again. Retry ceilings describe possible additional attempts, not evidence that every passing test executes them.

For example, three logical browser cases run in two applicable projects. An inner route loop grows from two to four routes: the discovery list remains six entries, while configured navigations rise from 12 to 24 per first attempt. Two separate request-only cases contribute two HTTP checks, not another browser-project multiplier. These counts establish work exposure; they do not establish elapsed seconds or waste. Distinct new behavior can justify the extra checks.

For changed browser/build/fanout paths include the relevant lifecycle: install/download/link, image pull/extraction, capacity checks, provenance verification, server readiness, tests, diagnostics, browser/context close, report transfer and post-action cleanup. Distinguish capture/recording from retention and upload: discarding passing artifacts can still leave success-path work. Inspect the pinned implementation when mode names do not resolve this. Preserve asserted visual comparisons, consumed review artifacts and useful first-failure diagnostics.

## Follow consumers and the existing budget

Trace before/after required evidence through native dependencies, reusable workflows, completion triggers, polling helpers, protected environments and release publishers. Record PR and protected-push routes separately, including valid-proof reuse and missing/invalid-proof fallback when affected. A strengthened aggregate gate may correctly add prerequisites; preserve its protection while identifying repeat work, false dependencies or safe preparation overlap.

Separate demand from elapsed feedback. More shards repeat fixed setup and can leave an indivisible file or inner loop as the tail. Fewer workers may repair resource contention while increasing the tail. A shared producer may avoid installs yet add upload/download, verification, extraction and a serial barrier. Report the tradeoff rather than assume any direction is universally efficient.

Use only an existing explicit budget and its actual start/finish clock. Staging readiness does not establish publication time; warm reuse does not qualify cold full fallback. Carry relevant conditions into the caller's [acceptance evidence](experiments.md). If a changed preparation now occupies a deployment lock, identify what can overlap safely and what remains serial.

A source-supported expensive addition with material budget exposure is a supported risk even before hosted timing exists. State what is known and which small check would close it. Conversely, new justified coverage and unknown timing alone are not defects. A numeric lower bound proves a miss only when observations and execution/concurrency assumptions apply to the actual required path; counts by themselves do not predict wall time. Keep inherited latency separate from attributable change findings.

## Retain a compact impact receipt

One row per materially affected expensive family is sufficient; share common candidate metadata. Do not fill unknown fields with zero.

| Field | Content |
|---|---|
| Candidate | Target/base, reviewed state identity, scope/exclusions |
| Path and exposure | Changed location → caller/command/fixture → consumer; affected events and terminal outcome |
| Before → after | Actual configured operations, setup/build/diagnostic/transfer multiplicity and relevant conditions |
| Timing/resources | Serial edges, slowest group, worker/capacity/cache assumptions; demand separate from latency |
| Protection | Distinct behavior retained, reused, or deliberately moved under existing authorization |
| Evidence | Source-derived, discovered, profiled, observed, or missing; inspected paths and material gaps |
| Disposition and closure | Finding status, smallest remedy/check, responsible caller/owner and exact remaining fix/validation/acceptance condition |

For example, a second shard can increase builds and engine installs from one to two, preserve complete membership, and leave the largest file intact. Without timings this is not a measured slowdown. If the change is proposed to meet a latency target, retain the repeated fixed cost and tail as a supported risk, then identify the needed producer/partition or hosted check. Do not conclude “no material findings; benchmark pending” while dropping that risk.

## Report a disposition that matches the evidence

| Disposition | Meaning and handoff |
|---|---|
| No relevant impact | No material CI execution consumer in the reviewed scope; brief response, no general recommendations |
| No material finding in completed scope | Relevant paths inspected without supported material concern; timing qualification remains separate |
| Supported risk | Concrete source/evidence supports material exposure, but outcome or magnitude remains unconfirmed; retain mechanism and closure condition under caller rules |
| Confirmed regression | Direct invariant violation or applicable observation establishes the regression; fix or explicit caller-process acceptance before next push |
| Incomplete inspection | Comparison or material path unavailable; identify missing coverage and avoid a clean verdict for that portion |

A review may contain different statuses for different families. Report the material unresolved ones without turning every uncertainty into a blocker. Preserve an unverified budget condition until its named scenario is observed or explicitly accepted under the caller's rules. Static inspection can finish while performance acceptance remains pending. Do not independently implement remedies, start broad experiments, push, deploy, delete shared caches or create another approval loop from review authorization.
