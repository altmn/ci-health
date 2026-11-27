# Choose a CI Health workflow

The [starter prompts](../README.md#try-it) cover the common tasks. This guide preserves the detailed routing and evidence expectations without making them introductory product copy. The skill entrypoints remain the operational instructions.

## Audit, baseline, and validation

[CI Health](../skills/ci-health/SKILL.md) audits repository CI, establishes baselines, diagnoses bottlenecks, and validates proposed improvements. Findings distinguish suspected, supported, confirmed, and resolved. Audits investigate material commands and delivery gates, including inner test operations and preparation that test counts can hide.

The goal is fast, trustworthy feedback and sustainable throughput. Cost is a supporting metric. Operational checks belong in the investigation when they materially affect CI demand or useful feedback, or when explicitly requested. Scheduled work can consume substantial resources or supply required evidence. An unrelated cleanup or recovery failure does not automatically outrank CI optimization.

## Targeted improvement

[CI Health Optimize](../skills/ci-health-optimize/SKILL.md) addresses a specific bottleneck or latency goal in an existing pipeline, including during shipping. It investigates work that can be removed, reused, rebalanced, or moved to another validation stage. It edits when implementation is authorized.

The [optimization playbook](../skills/ci-health/references/optimization.md) includes a [Bun recipe](../skills/ci-health/references/bun-ci.md) for suitable JavaScript/TypeScript repositories. Preserve the [scenario acceptance ledger](../skills/ci-health/references/experiments.md#scenario-acceptance-ledger) through implementation and handoffs. Fast PR, reuse, cold fallback, staging, and release-publication observations qualify their own conditions. Failed, retried, and over-budget attempts remain evidence. Implementation completion and performance acceptance are different outcomes.

## Proposed-change review

[CI Health Preflight](../skills/ci-health-preflight/SKILL.md) follows a proposed change through tests, scripts, fixtures, configuration, and application inputs affecting CI, including changes outside workflow files. Confirmed material regressions require resolution or explicit acceptance under the caller's rules before shipping continues.

During shipping, an unqualified CI Health invocation routes to Preflight. Explicit audit, baseline, and diagnosis requests retain their scope; targeted improvements route to Optimize. An explicit preflight request can receive a brief no-impact review.

CI Health and Optimize support implicit selection. Preflight disables direct implicit invocation. Generic review or shipping alone does not select it for independent copy: ordinary inspection must establish changed CI execution before CI Health routes a CI-specific review. Source-scanned or otherwise consumed content may still affect execution. Selective automatic discovery remains an open limitation; see [known issues](known-issues.md).

For materially affected expensive paths, Preflight retains a compact before/after impact receipt bound to the candidate. It keeps supported risks and unverified budget conditions visible, refreshes inspection after relevant edits, and separates completed static review from timing qualification. Independent copy without execution impact stays brief.

Once selected during shipping, finish Preflight before the next origin push, including an early draft-PR push. The shipping workflow owns fixes, other reviews, tests, and publication; CI Health does not independently push or publish.

## Evidence limits

Physical resource demand and elapsed feedback differ from valid logical test evidence. Missing observations remain unknown. GitHub REST job intervals do not establish exact eligible queue time, checkout identity, required-verdict history, provider charges, or complete calendar-period activity. Run-created cohorts need supplemental ingestion for older runs retried in a period.

Before/after comparisons need compatible workloads and experimental evidence before causal claims. Incomplete captures, unknown rate mappings, failed attempts, and unmet acceptance conditions stay visible. Human review and representative observation remain necessary for required-check, selection, capacity, and production changes. No real-world savings are claimed for this new project.
