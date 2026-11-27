# Optimization-focused CI audits

Use for a broad repository CI audit. A focused baseline, investigation, or requested edit needs only its relevant guidance.

## Establish relevance before collecting

Default to reducing avoidable CI work and improving useful feedback: repeated preparation and execution, test/build overhead, critical paths, queueing, cancellation, caching, resource use, and cost. Preserve required validation while investigating these opportunities. A general coverage, security, deployment-health, or operations review is a separate objective unless the user requests it or it is necessary to assess an optimization.

Investigate a task according to its contribution to the requested outcome. A failed staging cleanup, restore drill, or scheduled check can be consequential operationally without being a priority for CI optimization. Its red status, repetition, or accessible host is insufficient reason to follow it deeply. Note a consequential incidental discovery briefly with evidence and an appropriate follow-up; continue the optimization investigation. Conversely, a costly scheduled regression suite, a required freshness check, or a service failure causing CI retries can belong directly in scope. Classify by effect, not workflow name, trigger, or environment.

Start with workflow/source inspection and representative existing observations. Expand collection only when it can change a decision; a complete fleet census, live-platform audit, or multiweek baseline is not a prerequisite for reporting a source-supported opportunity. Keep collection and analysis proportional to likely impact and the user's requested deliverable. Missing observations remain unknown.

## Map delivery and clocks

Map candidate arrival to the outcome the user requested across workflow boundaries before choosing a remedy. Follow reusable workflows, event triggers, polling helpers, aggregate required verdicts, environment locks and result consumers. For example, PR checks may feed protected-push reuse, while staging smoke and retained checks feed a later publisher. Newly enforced correctness work can change this path; preserve its contract while investigating scheduling or reuse.

| Outcome | Start and finish evidence |
|---|---|
| PR feedback / actionable failure | Candidate push/event → actual required verdict / first trustworthy relevant failure; label run creation if it is the available proxy |
| Staging readiness | Protected merge/push → last required live smoke, identity, asset or telemetry check |
| Sealed release | Protected merge/push → actual release publication record, not preparation/job completion |
| Whole change cycle | PR arrival → requested terminal milestone, including merge wait |
| Runner demand | Actual deduplicated occupied job intervals across all attempts and outcomes; neither active CPU nor invoice |

Record UTC endpoints and source identities. Separate prerequisite, dispatch, approval, lock and eligible-queue waits; missing eligibility evidence cannot establish queue time. Configuration activation, artifact publication and production promotion are distinct milestones. Investigate only those relevant to the requested outcome.

## Discover consequential work

Identify the relevant event and workflow families, then make a bounded pass across the following optimization questions. Use evidence to choose depth: expensive, frequent, repeated, and critical-path work deserves attention first. Without timings, visible fanout, repeated commands, and nested loops are leads rather than measured rankings.

| Question | Evidence and reference |
|---|---|
| What delays a useful result or runs for obsolete candidates? | Dependencies, event fanout, waits, compatible capacity, cancellation; [orchestration.md](orchestration.md) |
| What actually executes, including repeated preparation? | Expanded commands, tool launches, generators, builds, harness phases; [execution.md](execution.md#expand-material-command-paths) |
| Which checks overlap, and which prove different contracts? | Test membership plus configuration, input/output identity, consumer closure; [selection-and-reuse.md](selection-and-reuse.md) |
| What amplifies demand or hides the benefit? | Retries, failures, cache/setup paths, resource contention, artifacts and remote services; relevant execution sections |
| What actually has to finish before the next useful decision? | False DAG edges, repeated proofs, cheaper equivalent checks, and eligibility to move work beyond the urgent path; [optimization.md](optimization.md#choose-the-highest-leverage-change) |
| What can the available numbers establish? | Physical consumption versus elapsed feedback, workload, sample and cost limits; [measurement.md](measurement.md) |

Do not let a reproducible timing baseline or a strong correctness finding replace command-level efficiency investigation. Compare relevant lanes for missing or inconsistent cancellation, caching, repeated setup, native rebuilds, and timeouts. Absence of repository configuration is evidence about that configuration, not proof of live overlap, lack of external caching, or an improvement's payoff. Preserve justified differences in trust, platform, quota, release evidence, and serial mutation.

For each material command family, retain a compact coverage row:

| Family/event | Command and wrappers | Work and lifecycle | Consumers | Evidence and gaps |
|---|---|---|---|---|
| Relevant workflow/lane | Actual command, modes, hooks, child calls | Input cardinality, applicable projects/loops, fixtures, setup/teardown and reporting | Required verdict, deployment or publisher | Source/discovery/profile/run evidence; sampling; unexamined path and next check |

Expand high-demand and critical paths beyond filenames or discovered test totals. Apply actual filters and nested dimensions; sum distinct groups. Use [browser-work.md](browser-work.md) for browser captures, inner loops and lifecycle tails. Configured work is not measured runtime. Reconcile this coverage record before concluding, including material commands no agent traced.

## Delegate and reconcile

When using agents, assign concrete optimization questions and command/workflow families, relevant references, evidence boundaries, and expected coverage. An execution assignment needs the execution reference; broad platform ownership alone can encourage unrelated operational investigation. Each agent should identify what it inspected, what it found, and material paths it did not trace.

Reconcile reports before concluding: resolve overlapping ownership, compare repeated work across lanes, and pursue consequential command paths that no agent examined. Delegate only when useful and available; the same reconciliation applies to a solo audit.

## Finish within the declared scope

Keep a compact coverage record for relevant workflow and command families. Distinguish **examined with findings**, **examined with no supported issue**, **not applicable with a reason**, and **unexamined with a limitation and next step**. State whether evidence is source inspection, observed execution, or controlled measurement, and identify representative sampling. This record describes audit coverage, separately from a finding's suspected/supported/confirmed/resolved status. It need not enumerate unrelated operational systems or every diagnostic hypothesis.

Lead with the most consequential supported opportunities, including changes to the work itself when the evidence warrants them. Describe the latency/demand mechanism, evidence strength, tradeoffs, and first validation. Distinguish work removed, moved to another stage, and completed sooner through more capacity. If the highest-impact lead is unmeasured, identify the smallest evidence collection that would change the priority. Keep incidental operational notes secondary and delimit material unexamined work.

Carry explicit targets and unresolved conditions into the [scenario acceptance ledger](experiments.md#scenario-acceptance-ledger) for optimization, preflight and shipping handoffs. Recompute the critical path after each major intervention: removing browser repetition may expose quality checks, setup or publication. Close only the observed accepted routes; a completed audit or a fast reuse route does not certify cold fallback or another terminal milestone.

For each unmet required scenario, hand off the smallest concrete next check: candidate/conditions, actual consumer and endpoint, exact inventory reconciliation, and the failure or missing-evidence behavior that must remain nonpassing. Identify the observation that closes the finding rather than merely restating the performance target. Keep that action in the final report.
