---
name: ci-health-preflight
description: Review CI-relevant diffs before push for inefficient execution and unnecessary complexity, including tests, scripts, configuration, and application inputs that change CI work. Skip ordinary copy or content edits with no CI execution impact.
---

# CI Health Preflight

Review whether the proposed change introduces or worsens material CI inefficiency or unnecessary complexity. Keep findings and recommendations specific to that change. Read unchanged code only to understand its execution path, requirements, and prior behavior. Existing inefficiency, unrelated operational failures, and general improvement ideas stay outside the report unless explicitly requested. Use [CI Health](../ci-health/SKILL.md) to diagnose existing CI problems and [CI Health Optimize](../ci-health-optimize/SKILL.md) for targeted improvements, including during shipping.

## Establish the candidate

Read repository instructions and honor the caller's explicit comparison, file scope, and reviewed candidate. Otherwise identify the intended target branch from the repository/caller context and resolve its merge base with HEAD. Compare that base with the current tracked working tree so committed, staged, and unstaged changes are included; inspect relevant non-ignored untracked files too. For example, `git diff <merge-base>` plus `git ls-files --others --exclude-standard` covers more than `git diff <base>...HEAD` alone. Account for old and new paths on renames and deletions. Do not assume the current branch's upstream is the PR target.

Record the resolved target/base, HEAD, dirty/untracked state, scope exclusions, and a content fingerprint or retained immutable snapshot of the reviewed candidate. Use [candidate identity](../ci-health/references/preflight-impact.md#bind-the-reviewed-state) when the state is mutable. If the comparison or a material execution path is unavailable, mark that inspection incomplete and identify what is missing. Do not substitute an empty diff, invent a clean verdict, fetch broad history, or expand into an audit. Missing timing telemetry alone does not prevent completed static inspection.

## Follow the changed work

Start with changed hunks and trace only their material CI effects through callers, workflows, task wrappers, package/lifecycle scripts, fixtures, generated inventories, and runner configuration. Workflow files need not change: a route catalog, shared helper, dependency, layout, or source-scanned content can multiply unchanged tests or preparation. Establish the old and new execution path before attributing a concern to the candidate.

Check the relevant mechanisms:

- Added jobs, triggers, actual project filters, nested loops, fixture scope, and repeated setup, compilation, tool/browser launches, captures, or artifact transfers. Expand configured operations; discovered test counts can conceal inner work.
- Expensive end-to-end checks whose distinct behavior could be established at a cheaper layer, repeated assertions across equivalent states, and nonassertive demonstration screenshots or reports added to every CI run.
- Long scenarios, fixed waits, retry amplification, shared-state contention, and scheduling or concurrency changes that increase critical-path delay, demand, or instability.
- Newly serialized checks, worse shard tails, worker reductions, lost cancellation or invalidation, and work moved into required-verdict, staging, or requested publication paths. Trace effective consumers across workflows, polling helpers and environment locks; preserve strengthened correctness gates.
- New selectors, caches, shards, planners, abstractions, and supporting machinery: identify the requirement they serve and whether a smaller solution satisfies it with less execution or maintenance cost.

Test growth alone is not waste. Distinct environments, boundaries, failure cases, and required contracts can justify additional work. Similar names or assertions do not establish redundant protection. More workers do not establish improvement without capacity and isolation evidence. Preserve meaningful assertions and detection; do not suggest removing tests merely to lower a count or meet an invented budget.

For each materially affected expensive execution family, retain a compact [impact receipt](../ci-health/references/preflight-impact.md): changed location → command/fixture → consumer, old/new configured work, events/gates, lifecycle/resource assumptions, protected behavior, evidence, disposition and closure. Use its worked examples for nested work and budget exposure. Use [execution guidance](../ci-health/references/execution.md#expand-material-command-paths), [optimization guidance](../ci-health/references/optimization.md#choose-the-highest-leverage-change), and [selection and reuse](../ci-health/references/selection-and-reuse.md) as relevant. No-impact copy needs only a brief scope conclusion.

## Resolve evidence and report

Default to static inspection and existing local evidence. Use a small targeted check when it can resolve a material uncertainty. Do not automatically collect historical run cohorts, run full suites, start optimization experiments, or change files. Review authorization is not implementation authorization; the caller retains ownership of authorized fixes and validation.

Each finding needs a changed location, before/after path, concrete impact, evidence, and the smallest useful remedy. Source-derived counts are configured work, not observed executions, timing, or savings. Unknown runtime, resource headroom, and billing remain unknown. Evaluate aggregate demand separately from the slowest valid dependency path. If an existing time target applies, retain its exact endpoint, relevant cold/fallback conditions, remaining margin if known, and the evidence needed to qualify it.

Return scope/candidate, findings, limitations, and an explicit disposition: **no relevant impact**, **no material finding in completed scope**, **supported risk**, **confirmed regression**, or **incomplete inspection**. Keep source-supported material risks visible even when timing is unknown; name the validation/fix/acceptance condition handed to the caller. Added justified coverage or missing telemetry alone is not a regression. A completed static review does not certify a performance target. A confirmed material regression must be resolved or explicitly accepted under the caller's rules before the next push. Supported risks follow those existing rules; advisory complexity does not automatically block. Never summarize incomplete inspection or an unresolved material risk as no material findings. Keep a brief inherited-budget note when relevant, without attributing unchanged cost to the diff.

## Cooperate with shipping

When selected in a ship workflow, finish before the next origin push, including any early draft-PR or CI-carry push. If an earlier push already happened, accurately describe this as reviewing the next push. Discovery is model-selected; this skill installs no hook and does not guarantee it runs on every ship.

Hand receipts and unresolved acceptance conditions to the caller's existing review/fix process; retain them across handoffs. Do not replace core/security reviews, create another ship loop, or independently push, publish, delete caches, or change protection. A generic shipping helper is not this semantic review. Reuse stable rows, but after relevant edits refresh affected paths and candidate identity before the next push, including draft pushes. Unrelated no-impact edits need only an identity/scope update, not another audit.
