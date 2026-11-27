# Validation

## Copy-only discovery candidate — unreleased

The proposed 0.4.1 update disables direct implicit Preflight invocation in host policy while retaining explicit requests and CI Health routing for established CI execution changes. This is a deliberate discovery-policy change. Independent content remains ordinary review; content consumed by generators, layouts or tests can still require a CI review.

Three fresh CLI repetitions reproduced unnecessary loading with 0.4.0. An initial wording-only candidate passed one repetition and failed two; it is not qualified. Subsequent paired trials of the host-policy candidate could not execute because CLI model usage was unavailable. These incomplete attempts are not behavioral passes. Four additional synthetic cases cover independent docs, translations, explicit copy review and source-scanned content; together with existing implicit CI-positive cases they define the pending qualification. Release and installation remain deferred until these fresh-session checks pass. Structural tests alone do not establish discovery behavior.

All 91 offline tests pass on Python 3.11.1 and 3.15.2. Package validation and build pass; the policy regression checks reject accidentally restoring implicit Preflight invocation or disabling implicit Audit/Optimize. `tests/trials/copy-discovery.json` preserves instruction/input hashes for six completed wording observations and sixteen unavailable suite attempts; final host-policy behavior remains unverified.

The offline suite exercises API pagination/window boundaries, attempt handling, accounting, missing states, cost mapping, comparison compatibility, and packaging. All inputs are synthetic. Tests do not contact GitHub or billable services.

The release validator checks the runtime allowlist, metadata, relative Markdown links, and selected private-path/credential patterns. It is not a comprehensive secret scanner or behavioral certification. An independent realistic skill trial complements these checks. Trial records below identify the actual instruction snapshot and observations; they must not be presented as proof of production savings or exhaustive detection safety.

## Initial validation — 2026-11-17

All 42 offline tests passed locally on Python 3.15.1: 36 measurement tests and six packaging tests. Package validation, two byte-identical repeated archive builds, CLI help/version, the skill-creator frontmatter validator, and whitespace checks passed. The GitHub workflow also runs the suite on minimum-supported Python 3.11 and current stable Python; inspect its actual check result for a release rather than inferring it from this local result.

Independent code review reproduced a paired-currency subtraction error, a rerun race during multi-run extraction, and loss of a known parent count during search partitioning. Each was corrected with a regression test before initial publication. Capture completeness is explicitly per-run observation consistency, not an atomic API snapshot.

Two independent agent simulations used only the skill, relevant references, and synthetic raw inputs. They wrote actual reports in isolated temporary workspaces with no network or live CI access. The evaluators were not given intended answers. Source inputs are `tests/scenarios/traffic.json` and `tests/scenarios/selection.json`; the instruction/input hashes and observed decisions are recorded in `tests/trials/initial.json` in the source checkout.

| Trial | Observed behavior | Review result |
|---|---|---|
| Traffic/capacity comparison | Rejected the claimed benefit: total demand fell with 75% less traffic; recorded demand per candidate rose 50%; capacity quadrupled; cancellation share rose; candidate capture was incomplete. Did not turn either the queue proxy or missing quality evidence into a causal conclusion. | Passed the intended measurement safeguards |
| Selected-only readiness | Rejected merge readiness: duplicate shard planning, missing C, invalid B/D reuse after dependency/runtime/environment changes, error-to-empty selection, permissive aggregate, and absent detection trials. Distinguished duplicate planning from proven duplicate physical execution. | Passed the intended proof-completeness safeguards |

The traffic trial was repeated against the final measurement instructions after clarifying the pricing formula. The selection trial's read instructions were unchanged through review. These are independent simulations, not Codex UI integration tests, statistical detection guarantees, or evidence of savings in a real overloaded CI installation. Any future instruction changes require review of whether the recorded trials still apply; hashes bind the records to the tested text.

Local plugin discovery and a live collector smoke test are separate release checks performed after source publication. Their results belong in release notes or delivery records. A tiny project CI run can test integration but cannot validate overload improvements.

## Review corrections — 2026-11-17

Version 0.1.1 adds strict external-summary validation and a source-only [repeatable skill evaluation suite](https://github.com/altmn/ci-health/blob/master/docs/skill-evaluations.md). All 61 offline tests passed locally: 44 measurement, six packaging, and eleven evaluation-recorder tests. Package validation/build and workflow syntax checks passed. Genuine summaries generated by the unchanged 0.1.0 helper retained the expected 50% comparison result; duplicate identities, contradictory counts, truthy nonboolean completeness, and invalid metrics were rejected with no output report. Independent code review also exercised 1,001 malformed JSON variants without an uncaught exception.

Five synthetic cases ran through Codex CLI 0.169.0 in disposable workspaces, with expected answers and review rubrics withheld. An independent agent reviewed the answers, tool traces, and resulting files. `tests/trials/review-hardening.json` records tested instruction/input hashes, conservative activation observations, environment hashes, and outcomes. Model defaults were used; the effective model identity was not exposed in the retained event stream. Raw traces and answers remain outside Git and the release archive.

| Case | Observed result |
|---|---|
| Direct invocation | All four behavior criteria passed. Staged references were used; an entrypoint read was not observable, so activation remains unknown. |
| Indirect audit | Staged entrypoint read observed. All four criteria passed, including separate eligible-queue uncertainty and unresolved backlog. |
| Unrelated request | Answered only the editing request; no tools or skill reads observed. Both criteria passed within that observable scope. |
| Missing inputs | All three criteria passed. Independent review confirmed the staged entrypoint read through a shell loop; conservative automated path binding remains unknown. |
| Narrow implementation, initial | Failed two criteria: the requested workspace stayed unchanged while a separate temporary copy was edited. Automated workspace scope alone did not establish task completion. |
| Narrow implementation, corrected environment | The runner prepared a task branch before sandboxed execution and required task edits to stay in that workspace. The unchanged prompt and rubric were repeated; only the requested timeout line changed in the intended workflow, and all three criteria passed. |

The initial narrow failure is retained. Its workspace began on `master`; the agent's claim that Git metadata was read-only was not demonstrated by a failed branch command in the trace. The correction supplies a prepared disposable task branch without prescribing the expected edit. A separate recorder correction prevents global or other-workspace skill paths from masquerading as staged reads; original traces were reinspected conservatively. Snapshot hashes do not mean every reference was read.

These trials establish observed behavior for the supplied cases, not activation reliability, production savings, cross-provider correctness, or live protection wiring. CodeQL analyzes Python and GitHub Actions on PRs, master updates and a weekly schedule; successful analysis uploads and any alerts are separate publication checks.

## Optimization focus — 2026-11-17

Version 0.1.2 makes unqualified audits optimization-first, with relevance-based operational investigation, nested command expansion, scoped completion reporting, and optional delegation reconciliation. All 64 offline tests passed on Python 3.15.1 and minimum-supported Python 3.11.1. The skill frontmatter validator and source link/privacy validation passed. Package regression tests now exercise actual ZIP/staging links and reject references present in source but omitted from the runtime allowlist.

Two new source-tree audit cases ran against frozen 0.1.1 and corrected instruction snapshots through Codex CLI 0.169.0. The five existing cases were also repeated against the correction with their definitions unchanged. Prompts, synthetic source and observations were provided without intended answers or rubrics. An independent reviewer inspected all nine answers, completed traces and final filesystem contents against each held-out criterion. `tests/trials/optimization-focus.json` records exact instruction/input/runner hashes, grades, observations and limitations. Model/provider defaults applied; effective model identity was not exposed in the retained event stream.

| Case population | Baseline observations | Corrected observations |
|---|---|---|
| Broad discovery audit | Five of eight criteria passed. Led with general assurance findings; omitted checker-process multiplicity and absent cancellation. | All eight passed. Led with fixed waits, repeated preparation/builds and test overlap; operational failures stayed secondary. |
| Broad audit control | All seven criteria passed. | All seven passed. Preserved distinct external validation, scheduled freshness, and stateful deployment serialization; qualified unmeasured opportunities. |
| Existing five cases | Not repeated against baseline in this comparison. | All sixteen criteria passed, including unchanged narrow-edit scope and measurement safeguards. |

All seven corrected runs passed independently reviewed filesystem scope and offline behavior. Only the authorized timeout line changed in the narrow-edit workspace. Staged entrypoint reads were observed for direct invocation, indirect activation and broad discovery; manual review also confirmed the missing-inputs loop read. Positive activation remains conservatively unknown for the narrow case and both control runs. Behavioral grades are separate from activation observations.

The baseline also kept operational failures secondary: this fixture did not reproduce the original operational detour. Both discovery answers encountered synthetic Git-index/global-ignore artifacts, which are trial-environment limitations rather than real project defects. Placeholder journey bodies and a declared quota policy establish configured work, not production quota behavior or savings. One run per case does not estimate reliability or demonstrate a causal improvement. Raw answers, traces and host paths remain private outside Git and runtime archives; no actual CI, operational system or billing data was used.

## Pre-push change review — 2026-11-18

Version 0.2.0 adds CI Health Preflight and change-review routing while retaining explicit broader audit requests. All 79 offline tests passed locally on Python 3.15.1 and minimum-supported Python 3.11.1. Both skill frontmatter checks and package validation passed. The package contains 26 allowlisted runtime files, including both entrypoints and UI metadata; archive/staging tests check their cross-skill references and deterministic packaging.

Fifteen synthetic cases ran through Codex CLI 0.169.0 against a frozen instruction snapshot: the seven existing case definitions were unchanged, and eight new cases exercised change-specific review and routing. Independent reviewers inspected every answer, successful tool trajectory, final files, and Git state against withheld criteria. A discovery-description correction then received six targeted trials. `tests/trials/preflight.json` records exact instruction/input/runner hashes, individual grades, and limitations. All 21 invocations completed; this alone is not a behavioral pass.

| Population | Independently reviewed result |
|---|---|
| Existing seven cases | 31/31 criteria passed; only the authorized timeout edit changed files. |
| Eight new cases, initial description | 32/33 passed. Detected added execution, followed application inputs, preserved distinct contracts, excluded legacy/general recommendations, and marked a missing base incomplete. The copy-only negative unnecessarily loaded preflight. |
| Six targeted cases, narrowed description | 21/22 passed. Positive routing and broad-audit precedence held. The same copy-only activation failure persisted; its response still reported no CI impact without general recommendations. |

The copy-only discovery failure is retained as a known limitation, not converted into a pass. Implicit selection remains model-dependent. No further descriptor changes or resampling were used to obtain a clean score. Automated positive activation is often unknown because reads used loops/compound commands or only references; manual staged-read observations are recorded separately. The provider/model defaults applied; effective model identity was not exposed in the retained event stream.

Independent code review found two recorder gaps: index snapshots omitted assume-unchanged/skip-worktree flags, and an absolute-path mention could be mistaken for a staged read. Both received regression tests. All fifteen original traces were reinspected with the corrected recorder; initial Git states were reconstructed and matched to the retained inputs before comparing index flags. All 21 file/Git scope checks passed, with no forbidden publication or network actions observed. The recorder correction did not rerun models; the six additional trials tested only the narrowed discovery description. The substantive preflight procedure was unchanged.

These are offline reviews, not proof of live pre-push enforcement or CI savings. The placeholder journey case does not validate removing real quota guards. Fresh installed-session discovery and exact packaged-file checks are delivery checks; neither guarantees implicit invocation on every future ship request. Raw captures remain private and outside release archives.

Ship review also reproduced a remaining reader-binding false positive when a shell comment consumed a newline before an echoed path. The recorder now rejects raw multiline commands before tokenization, with three additional rows in the existing adverse-command test. All 21 retained runs were reinspected against the final recorder without rerunning models; their file/Git scope outcomes and behavioral grades were unchanged. The trial record preserves the original and revised invocation runner hashes separately from the final reinspection hash.

## Audit helper corrections — 2026-11-25

Offline regressions reproduced two audit findings before repair: tracked and untracked permission-only changes received passing scope checks, and malformed evidence/API record types bypassed the helper's typed error path. The recorder now compares file types and permissions while retaining content-only instruction/environment hashes in receipts. The measurement helper validates record shapes before field access; malformed evidence files return status 2 without a report or traceback, and malformed API page elements preserve an incomplete capture and checksums.

All 84 offline tests passed on Python 3.15.2, including executable and non-executable permission changes, file-to-symlink replacement, receipt hash compatibility, malformed run/job records, and actual CLI evidence-shape cases with a valid-object control. No live model or authenticated API trial was run. Historical behavioral grades were not reissued or extended to changed bytes; these checks establish the corrected deterministic resource contracts only.

## Targeted CI optimization — 2026-11-25

The discovery trial compared a separate Optimize entrypoint with a CI Health variant that offered the same initial shared guidance through its existing entrypoint. Six targeted cases exercised direct and implicit requests, a scoped workflow edit, a selector with incomplete evidence, and moving compatibility checks off the staging path with explicit exposure policy. Six controls exercised broad audit, preflight, and unrelated or copy-only requests. The integrated variant ran three of the same prompts. The job dependency and cache cases used identical fixtures across variants. The Bun comparison used different bytes for `package.json` and `tests/public.test.ts`.

The initial separate entrypoint was observed in all six targeted cases and none of the six controls. Both variants handled the three tasks substantively. The integrated variant also read Preflight during the targeted DAG edit and omitted a useful-verdict timing limitation. Treat the results as observations from a small routing pilot. The Bun outcomes reflect different fixture inputs as well as different entrypoint layouts. The pilot leaves relative task quality, invocation reliability, and skill overhead unmeasured.

The initial shard plan omitted a policy for missing timings, one preflight report omitted the confirmed finding's shipping disposition, and a copy-only control opened Preflight unnecessarily. The shared shard recipe and preflight reporting instructions now make the missing outputs explicit. The revised snapshot passed all 50 behavioral criteria across six targeted cases and six controls, including the copy-only control. All workspace and Git scope checks passed across both snapshots and the integrated comparison.

Keep Optimize as a separate entrypoint in the development package. The revised run directly observed the exact optimizer in both implicit cases, the targeted request through CI Health, and the staging edit. Two explicit requests read the correct shared references without an observable entrypoint read. No control in either snapshot opened Optimize. These observations support including the entrypoint while leaving implicit routing reliability and native plugin discovery open. The sanitized receipt in `tests/trials/optimize-routing.json` identifies all 27 runs, artifact hashes, and individual grades.

In the staging trial, the local workflow change removed compatibility from staging prerequisites and retained compatibility for production against the same run's artifact. The checks exercised dependency and failure behavior offline. The sample's 894-second difference was between prerequisite completion times; staging readiness after the change was unmeasured.

The trials ran through Codex CLI 0.170.0 in disposable repositories with synthetic inputs and withheld rubrics. Reviewers compared the answers, exact staged text in traces, final files, and Git state. The effective model was unavailable. A full entrypoint body printed from its exact staged path counts as a manual observation even if a compound read reports a missing optional file. An observed shared reference alone leaves entrypoint activation unknown. This pilot used no live CI, deployments, or native plugin installation. Offline verification passed all 84 tests on Python 3.11.1 and 3.15.2. Package validation covered 30 runtime files and two local builds produced identical archive bytes.

## Workflow evidence and acceptance — 2026-11-26

Version 0.4.0 makes audit, preflight and optimization produce traceable work and acceptance records. Preflight binds materially expensive before/after work to the reviewed candidate and follows its consumers. Audit names delivery clocks and examined command paths. Optimize retains separate route, cache, proof, attempt and terminal-outcome conditions; source review, implementation and performance acceptance remain separate.

The corpus now has 32 synthetic cases. Twenty were exercised against the unchanged 0.3.0 instructions and the candidate using the same case inputs, with corrected controls repeated on both variants. Fifty-four completed CLI observations retain initial failures, fixture ambiguity and corrected repeats. Independent reviewers read answers, command trajectories, outputs and resulting file/Git state against withheld rubrics. The source-only receipt in `tests/trials/workflow-evidence.json` records tested instruction/input hashes, individual grades, answer/trace digests, corrections and limitations. Raw artifacts and private field evidence remain outside source and release archives.

| Latest relevant reviewed observations | Baseline | Candidate |
|---|---:|---:|
| Full rubric passes across 20 exercised cases | 17 | 19 |
| Retained rubric failures | 3 | 1 |
| False clean verdicts among seven new material-risk scenarios | 0 | 0 |

These aggregates combine relevant reviewed snapshots rather than one untouched final sweep. Both variants found the core material-risk mechanisms, so this sample does not establish increased regression recall or invocation reliability. The candidate improvements observed here concern execution receipts and complete acceptance handoffs. Both variants still unnecessarily loaded preflight for independent copy; this remains a failed discovery/proportionality control even though neither invented an impact or blocker. Twelve corpus cases were not rerun.

Trials exposed a contradictory shard recommendation, an omitted new-file timing policy, a missing stage validation/rollback handoff, incomplete audit next checks and an incomplete proof boundary plan. Instructions were corrected and affected paths repeated; original failures and a failed intermediate proof repeat remain recorded. A control's missing package wrapper was a fixture defect, not evidence of a false blocker: both ambiguous results were retained, then both variants passed the completed control. Preliminary browser fixtures also needed explicit engine selection; seven private pilot invocations (one completed and six interrupted) are excluded from qualification.

An additional paired three-step native-agent trial reviewed a cheap assertion, then a changed shared helper, then independent notes. Both variants refreshed the affected helper path, identified four-to-eight navigations and zero-to-eight unused captures, reused unaffected inspection and retained the unresolved concern after the notes edit. Candidate receipts additionally carried updated content fingerprints. Parent-checked final snapshots contained only the two expected fixture edits and unchanged Git state. This supplements the CLI trajectories; it is not an enforcement or reliability guarantee.

The measurement helper's 0.1.3 patch fixes reversed timestamp placeholders on runnerless, step-free skipped jobs. Five offline regressions cover those placeholders, skipped steps, contradictory runner/step evidence and invalid executed intervals. Invalid executed times still fail; ambiguous skipped execution is not silently priced free. API job IDs reissued across attempts still require separately documented reconciliation.

All 90 offline tests passed on Python 3.11.1 and 3.15.2. Package validation covers 32 runtime files, including both new conditional references. Deterministic build and extracted/staged-byte checks complement behavior review. Formal positive activation often remains unknown despite manually observed staged content. No live CI savings, installed-session discovery, protection wiring or universal latency bound is claimed.
