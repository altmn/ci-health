# Browser work beyond discovered tests

Use when a browser, shared fixture, route/content input, capture mode, worker setting or build/runtime path materially affects CI. Inspect the installed version and actual implementation. These are mechanisms to test, not universal claims that browsers, screenshots or more coverage are waste.

## Expand the operations actually configured

Follow workflow → command/configuration → applicable projects → fixture/test body → input catalog → reports and downstream consumers. Count navigations/reloads, contexts, readiness waits, captures, assertions and retries separately where they dominate. Sum distinct groups and multiply only nested dimensions. Discovery may already expand projects: do not multiply those entries by projects again. Record maximum configured retries separately from observed attempts.

Synthetic example, no retries:

| Group | Logical cases | Applicable projects | Inner work | Configured navigations |
|---|---|---|---|---|
| Basic behavior | 6 | 3 | One navigation | 18 |
| Catalog behavior | 2 | 2 | 4 routes × 2 themes per case/project | 32 |
| Engine-specific behavior | 1 | 1 | 3 routes | 3 |

Discovery has 23 test/project entries; the bodies configure 53 navigations. Increasing only the catalog to 7 routes leaves discovery at 23 entries and increases navigations to 77. Only that group's applicable projects and inner loops multiply. If every navigation also makes an unused capture, count that separately. These source-derived counts establish additional work, not elapsed time or redundant coverage. Distinct route behavior can justify the addition.

Content can increase full-page image size, tiling, encoding, comparison and report transfer without changing YAML or test totals. Trace page geometry, selected widths/states and consumers. An asserted visual comparison or required retained review artifact has value; an unasserted successful capture excluded from upload needs a different justification. Preserve accessibility, focus, hydration, layout and engine-specific protection when removing incidental work.

## Separate recording, retention and upload

Inspect three decisions independently: when bytes/work are produced, when files survive teardown, and which paths upload. Failure-only retained output does not establish failure-only execution. Playwright's `retain-on-failure` trace/video modes record passing runs before discarding them; `on-first-retry` records only the first retry, so supplies no first-failure recording when retries are disabled. Select modes for the diagnostic contract. [Recording modes](https://playwright.dev/docs/test-use-options#recording-options)

For a concrete version-specific example, Playwright v1.58.2 calls `captureTemporary` when a browser context closes; its `only-on-failure` condition permits temporary successful screenshots, while persistence depends on final failure. This follows the pinned implementation and is not a timeless claim about every release. Inspect the repository's pinned source or a small lifecycle probe before estimating overhead or replacing the fixture. [Pinned recorder implementation](https://github.com/microsoft/playwright/blob/v1.58.2/packages/playwright/src/index.ts)

If modifying diagnostics, inject failures in the test body, afterEach and timeout paths, including manually created contexts/pages. Verify the real report/upload retains useful evidence. Closed pages or failures after context teardown can prevent image capture; disclose those limits and preserve text diagnostics. Do not delete meaningful visual assertions to eliminate capture cost.

## Model setup, workers and tails

Trace actual fixture dependencies before installing engines. Request-only HTTP/SSR checks may need no browser; a fixture using a page or browser does. Check app build mode, install/link/lifecycle work, engine/system packages, image extraction, startup, close and reporting. A package-store cache does not establish an installed tree. A shared producer can remove repeated builds while introducing upload/download and a serial barrier; include both effects.

Replay the actual shard assignments with compatible duration weights and the longest indivisible case/file. Equal case counts can hide long inner loops. Playwright's default file-level split and `fullyParallel` test-level allocation differ; test-level distribution still does not equalize case durations. [Sharding behavior](https://playwright.dev/docs/test-sharding)

Worker reduction can restore isolation or resource stability and lengthen a serial tail. Worker growth can overload the app server, browser, memory or quota. Preserve the stability evidence and compare whole-path latency, repeated setup and occupied demand. Wider fanout can buy latency while increasing demand; describe that tradeoff explicitly.

## Observe readiness and shutdown

Prefer the behavior's observable state: enabled controls and verified focus, event/first-frame state, actual server readiness or publication identity. A fixed wait applied to every case multiplies cost and may conceal a race. Keep deliberate delays used to test hydration distinct from synchronization sleeps. Qualify a repair with a realistic defect; a valid implementation may remove a closed panel rather than keep it mounted.

Timestamp assertion completion, context/browser close, server termination, artifact transfer and post actions. Tests finishing does not establish the job is done. Preserve native failure logs and exact engine/OS/tool revisions; do not force success or shorten close timeouts to hide a shutdown failure. Measure capacity checks and cleanup too: image/SDK removal can repair disk exhaustion while creating a latency regression. Use bounded owned-scratch cleanup and retain the failed/over-budget attempts in the [acceptance ledger](experiments.md#scenario-acceptance-ledger).
