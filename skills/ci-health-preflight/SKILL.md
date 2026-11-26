---
name: ci-health-preflight
description: Review CI-relevant diffs before push for inefficient execution and unnecessary complexity, including tests, scripts, configuration, and application inputs that change CI work. Skip ordinary copy or content edits with no CI execution impact.
---

# CI Health Preflight

Review whether the proposed change introduces or worsens material CI inefficiency or unnecessary complexity. Keep findings and recommendations specific to that change. Read unchanged code only to understand its execution path, requirements, and prior behavior. Existing inefficiency, unrelated operational failures, and general improvement ideas stay outside the report unless explicitly requested. Use [CI Health](../ci-health/SKILL.md) to diagnose existing CI problems and [CI Health Optimize](../ci-health-optimize/SKILL.md) for targeted improvements, including during shipping.

## Establish the candidate

Read repository instructions and honor the caller's explicit comparison, file scope, and reviewed candidate. Otherwise identify the intended target branch from the repository/caller context and resolve its merge base with HEAD. Compare that base with the current tracked working tree so committed, staged, and unstaged changes are included; inspect relevant non-ignored untracked files too. For example, `git diff <merge-base>` plus `git ls-files --others --exclude-standard` covers more than `git diff <base>...HEAD` alone. Account for old and new paths on renames and deletions. Do not assume the current branch's upstream is the PR target.

Record the resolved base, candidate state (including dirty/untracked changes), and any scope exclusions. If the comparison or a material execution path is unavailable, report the affected review as incomplete and identify the missing evidence. Do not substitute an empty diff, invent a clean verdict, fetch broad history, or expand into a repository audit. Missing timing telemetry alone does not prevent a completed static review.

## Follow the changed work

Start with changed hunks and trace only their material CI effects through callers, workflows, task wrappers, package/lifecycle scripts, fixtures, generated inventories, and runner configuration. Workflow files need not change: a route catalog, shared helper, dependency, or application behavior can multiply test work or trigger repeated preparation. Establish the old and new execution path before attributing a concern to the candidate.

Check the relevant mechanisms:

- Added jobs, triggers, matrix dimensions, nested loops, and repeated setup, compilation, tool/browser launches, or artifact transfers. Count configured multiplicity where the source supports it.
- Expensive end-to-end checks whose distinct behavior could be established at a cheaper layer, repeated assertions across equivalent states, and nonassertive demonstration screenshots or reports added to every CI run.
- Long scenarios, fixed waits, retry amplification, shared-state contention, and scheduling or concurrency changes that increase critical-path delay, demand, or instability.
- Newly serialized checks, worse shard tails, lost cancellation or invalidation, and work moved into the push-to-staging or required-verdict path. Identify which consumer needs each added prerequisite and whether equivalent evidence already exists.
- New selectors, caches, shards, planners, abstractions, and supporting machinery: identify the requirement they serve and whether a smaller solution satisfies it with less execution or maintenance cost.

Test growth alone is not waste. Distinct environments, boundaries, failure cases, and required contracts can justify additional work. Similar names or assertions do not establish redundant protection. More workers do not establish improvement without capacity and isolation evidence. Preserve meaningful assertions and detection; do not suggest removing tests merely to lower a count or meet an invented budget.

Use [execution guidance](../ci-health/references/execution.md#expand-material-command-paths) to trace a changed command, [optimization guidance](../ci-health/references/optimization.md#choose-the-highest-leverage-change) for a material scheduling or staging tradeoff, and [selection and reuse](../ci-health/references/selection-and-reuse.md) when membership or reused evidence changes. Keep each check anchored to the diff.

## Resolve evidence and report

Default to static inspection and existing local evidence. Use a small targeted check when it can resolve a material uncertainty. Do not automatically collect historical run cohorts, run full suites, start optimization experiments, or change files. Review authorization is not implementation authorization; the caller retains ownership of authorized fixes and validation.

Each finding needs a changed location, before/after execution path, concrete impact, supporting evidence, and the smallest useful remedy. Distinguish confirmed defects from supported risks and optional simplifications. Source-derived call counts are configured work, not observed executions, measured timing, or savings. Unknown runtime, resource headroom, and billing remain unknown.

Return the reviewed scope, material findings, and relevant limitations concisely. State the shipping disposition explicitly for a confirmed material regression: resolve it or obtain explicit user acceptance under the caller's rules before the next push. Advisory complexity concerns do not block. For incomplete inspection, state the missing coverage. With no material findings, say so briefly. When there is no relevant CI impact, report that without general recommendations.

## Cooperate with shipping

When selected in a ship workflow, finish before the next origin push, including any early draft-PR or CI-carry push. If an earlier push already happened, accurately describe this as reviewing the next push. Discovery is model-selected; this skill installs no hook and does not guarantee it runs on every ship.

Hand findings back to the caller's existing review, fix, and acceptance process. Do not replace its core/security reviews, create another ship loop, or independently push, publish, or change CI protection. Reuse completed inspection while its comparison, reviewed candidate, and relevant supporting inputs remain unchanged. After relevant edits, inspect the changed range and affected context before the next push; unrelated edits do not require another CI audit.
