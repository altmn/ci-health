# Known issues and to-do list

## PF-01 — Selective automatic Preflight selection

**Status: open.** Version 0.4.0 can unnecessarily select Preflight for independent copy-only reviews. The unreleased 0.4.1 candidate disables direct implicit invocation to mitigate that failure. This also removes independent automatic selection for genuinely CI-relevant changes. Explicit Preflight requests and CI Health routing remain available; routing still depends on CI Health being selected and identifying the relevant execution path.

The mitigation is not a complete solution to selective automatic discovery. Clearer description wording alone failed repeated checks. Agent trials passed the scoped copy and CI-relevant cases, and actual prompt rendering confirmed default catalog suppression. Those observations do not establish reliable automatic selection or full fresh CLI/Desktop model-turn behavior. See the [validation record](validation.md#copy-only-discovery-candidate--unreleased) and [evaluation procedure](https://github.com/altmn/ci-health/blob/master/docs/skill-evaluations.md).

### To do

- Investigate a selective relevance gate or routing approach that avoids loading Preflight merely to determine whether it applies, while retaining automatic CI-relevant review where possible.
- Compare proposed approaches with the current explicit/routed mitigation in fresh host sessions. Include independent labels, documentation and translations, plus scripts, shared fixtures, route data and source-scanned content with real CI consumers.
- Verify explicit invocation, CI Health routing, actual host selection, proportional review effort and absence of false blockers. Preserve failed and inconclusive observations.
- Re-enable direct implicit invocation only after the negative and positive cases support that decision. Do not close this issue solely because the host flag suppresses discovery or a small agent sample passes.

**Closure criteria:** evidence supports selective automatic review of CI-relevant changes without unnecessary CI-skill loading for independent copy, with explicit/routed requests preserved and remaining host/model limits documented. Record tested versions, inputs, repetitions and observed failures before closing.

The release and installation hold remains in place; this tracker does not authorize publication.
