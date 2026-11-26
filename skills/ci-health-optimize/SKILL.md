---
name: ci-health-optimize
description: Design or implement a targeted speed or cost improvement to an existing CI pipeline. Use for slow push-to-staging, wasted runner time, redundant jobs, shard tails, affected tests, or faster CI tooling. For broad audits, baselines, and pre-push diff reviews, use the corresponding CI Health workflow.
---

# CI Health Optimize

Shorten the time from push to a useful decision or a ready staging deployment. Remove avoidable work aggressively and judge the result against meaningful detection, reliability, and runner demand.

1. Read the relevant repository instructions and [optimization guidance](../ci-health/references/optimization.md). Trace the current job and command paths far enough to identify the real constraint, the exact candidate being tested, and where its required evidence is produced. For a broad audit or baseline, use [CI Health](../ci-health/SKILL.md). For a proposed-change review before push, use [CI Health Preflight](../ci-health-preflight/SKILL.md).
2. Compare the highest-leverage feasible remedies, including removing, reusing, or moving work, before adding capacity. Use the guidance applicable to the mechanism. A narrow change can proceed with narrow evidence. If observations are missing, pursue a source-proven improvement or gather the smallest useful evidence and label unmeasured gains as hypotheses.
3. Implement and verify an authorized improvement in the workspace. For advice or a trial plan, keep the workspace read-only. When a change affects detection or required evidence, qualify its failure paths and rollout before enforcing it. Apply explicit latency and detection targets to the relevant stage, and keep mandatory checks valid for their candidate and exposure.
4. Report what changed or is proposed, the time or demand mechanism, what was verified, what remains unknown, and the acceptance and rollback conditions. Claim a measured gain only from a comparable observation.
