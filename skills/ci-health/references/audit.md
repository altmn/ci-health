# Optimization-focused CI audits

Use for a broad repository CI audit. A focused baseline, investigation, or requested edit needs only its relevant guidance.

## Establish relevance before collecting

Default to reducing avoidable CI work and improving useful feedback: repeated preparation and execution, test/build overhead, critical paths, queueing, cancellation, caching, resource use, and cost. Preserve required validation while investigating these opportunities. A general coverage, security, deployment-health, or operations review is a separate objective unless the user requests it or it is necessary to assess an optimization.

Investigate a task according to its contribution to the requested outcome. A failed staging cleanup, restore drill, or scheduled check can be consequential operationally without being a priority for CI optimization. Its red status, repetition, or accessible host is insufficient reason to follow it deeply. Note a consequential incidental discovery briefly with evidence and an appropriate follow-up; continue the optimization investigation. Conversely, a costly scheduled regression suite, a required freshness check, or a service failure causing CI retries can belong directly in scope. Classify by effect, not workflow name, trigger, or environment.

Start with workflow/source inspection and representative existing observations. Expand collection only when it can change a decision; a complete fleet census, live-platform audit, or multiweek baseline is not a prerequisite for reporting a source-supported opportunity. Keep collection and analysis proportional to likely impact and the user's requested deliverable. Missing observations remain unknown.

## Discover consequential work

Identify the relevant event and workflow families, then make a bounded pass across the following optimization questions. Use evidence to choose depth: expensive, frequent, repeated, and critical-path work deserves attention first. Without timings, visible fanout, repeated commands, and nested loops are leads rather than measured rankings.

| Question | Evidence and reference |
|---|---|
| What delays a useful result or runs for obsolete candidates? | Dependencies, event fanout, waits, compatible capacity, cancellation; [orchestration.md](orchestration.md) |
| What actually executes, including repeated preparation? | Expanded commands, tool launches, generators, builds, harness phases; [execution.md](execution.md#expand-material-command-paths) |
| Which checks overlap, and which prove different contracts? | Test membership plus configuration, input/output identity, consumer closure; [selection-and-reuse.md](selection-and-reuse.md) |
| What amplifies demand or hides the benefit? | Retries, failures, cache/setup paths, resource contention, artifacts and remote services; relevant execution sections |
| What can the available numbers establish? | Physical consumption versus elapsed feedback, workload, sample and cost limits; [measurement.md](measurement.md) |

Do not let a reproducible timing baseline or a strong correctness finding replace command-level efficiency investigation. Compare relevant lanes for missing or inconsistent cancellation, caching, repeated setup, native rebuilds, and timeouts. Absence of repository configuration is evidence about that configuration, not proof of live overlap, lack of external caching, or an improvement's payoff. Preserve justified differences in trust, platform, quota, release evidence, and serial mutation.

## Delegate and reconcile

When using agents, assign concrete optimization questions and command/workflow families, relevant references, evidence boundaries, and expected coverage. An execution assignment needs the execution reference; broad platform ownership alone can encourage unrelated operational investigation. Each agent should identify what it inspected, what it found, and material paths it did not trace.

Reconcile reports before concluding: resolve overlapping ownership, compare repeated work across lanes, and pursue consequential command paths that no agent examined. Delegate only when useful and available; the same reconciliation applies to a solo audit.

## Finish within the declared scope

Keep a compact coverage record for relevant workflow and command families. Distinguish **examined with findings**, **examined with no supported issue**, **not applicable with a reason**, and **unexamined with a limitation and next step**. State whether evidence is source inspection, observed execution, or controlled measurement, and identify representative sampling. This record describes audit coverage, separately from a finding's suspected/supported/confirmed/resolved status. It need not enumerate unrelated operational systems or every diagnostic hypothesis.

Lead the report with the most consequential supported optimization opportunities, explaining their likely CI effect, evidence strength, guardrails, and next validation. State when impact cannot yet be ranked or quantified. An absence of measured savings does not erase demonstrated repeated commands; repeated commands alone do not establish avoidable work or savings. Keep incidental operational notes secondary. Clearly delimit any material in-scope work left unexamined; a completed scoped inspection is not a comprehensive audit or a validated improvement.
