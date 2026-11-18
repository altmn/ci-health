# Validation

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
