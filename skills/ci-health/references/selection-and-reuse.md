# Selection, reusable evidence and test removal

Read this before omitting checks, changing shards, reusing build/test results, relaxing isolation, or deleting tests. Passing remaining work does not establish preserved protection. Treat planners, cache policies and aggregate gates as production code.

## Navigation

- [Inventory and shard invariants](#inventory-and-shard-invariants)
- [Qualify affected selection](#qualify-affected-selection)
- [Shadow evaluation and recall](#shadow-evaluation-and-recall)
- [Cache and result reuse](#cache-and-result-reuse)
- [Test removal and quarantine](#test-removal-and-quarantine)
- [Negative gate cases](#negative-gate-cases)

For profiling and symptom-level diagnosis, use [execution.md](execution.md), particularly E08–E10, E16, E24–E34 and E36.

## Inventory and shard invariants

For each event, identify required behavioral, platform, package/protocol, security, migration, installation and release contracts. Give each an owner and execution route. Deferring a check requires a defined route/deadline; it must not silently disappear.

Use a stable entry identity:

```text
(canonical test ID/path, project/configuration, runtime,
 operating system, architecture, feature set)
```

Keep retry attempts in a separate one-to-many ledger. They cannot generally be enumerated in a preplanned manifest and are not independent coverage entries. Distinguish files, individual cases, configurations and physical jobs. Runtime-generated cases need the strongest reliable pre-execution inventory plus final reconciliation.

Retain discovered, selected, omitted, scheduled, reused and reported inventories with reasons. Require:

```text
selected = scheduled union qualified_reuse
union(planned_shards) = scheduled
union(complete_execution_reports) = scheduled
for every i != j: shard[i] intersection shard[j] = empty
    except explicitly declared duplicate executions
```

Account for every required contract through execution, qualified reuse or an authorized not-applicable decision. Record not-applicable scope separately. A pairwise intersection check matters: an empty intersection across all shards can conceal duplicates between two shards. Missing terminal reports, crashed workers, collection failures and pending tests are incomplete evidence, never passes. Evaluate acceptable outcomes separately from membership; a report can exist and report failure.

## Qualify affected selection

Use this conservative decision procedure; it is a recommended design, not a description of any particular repository:

```text
invalid protected policy or planner -> block and explain
absent/truncated/inconsistent comparison -> broader approved run, or block
global input change or uncertain ownership -> complete affected owners;
    use full validation when boundaries are unknown
otherwise -> changed tests + known owners + transitive consumers
           + runtime/fixture/generated-input dependencies
           + mandatory smoke/security/platform/policy contracts
unexpected empty selection -> broader validation or block
```

A verified no-op has an explicit reason. A planner exception is not a no-op. If broader validation cannot fit immediately, queue it visibly or block; do not turn capacity pressure into a false green. Frequent fallbacks identify graph/ownership work.

Select the comparison base for the contract: PR base and actual tested merge candidate; merge-group combined tree; all changes since qualified main validation; or a restored graph's recorded revision. These may differ. Record exact references and fetch required history. Nx's affected-CI guidance recommends the latest successful main commit so earlier unvalidated changes are included. [Nx affected CI](https://nx.dev/docs/features/ci-features/affected)

Static imports, bounded graph traversal and observed runtime edges are incomplete models. Missing edges are not proof of independence. Challenge selection before granting it authority:

| Change/failure | Protection to demonstrate |
|---|---|
| Leaf source or changed test | Owner and changed tests selected |
| Shared source/test helper | Transitive consumers included; test-only changes can affect others |
| Dynamic imports, plugins, reflection, dependency injection | Explicit ownership covers relationships not captured statically |
| Fixtures, snapshots, runtime assets, templates or file reads | Reading tests selected without relying on import edges |
| Generator/schema/build script/compiler flags | Generated consumers and packaging/build contracts included |
| Lockfiles, workspace/root config, global setup, toolchain | Complete affected owners or global invalidation |
| Rename/delete, symlink, submodule, case-only change | Old/new identities and consumers handled |
| Platform, architecture, feature flag | Required execution configurations preserved |
| Selector/workflow change | Planner and gate independently validated |
| Missing history, failed API, truncated diff, corrupt graph | Broader approved run or block |
| No applicable change | Observable justified no-op |

Derive expected results from the behavioral contract, not the selector's output. Include realistic fault injection and historical regression replays. Root configuration legitimately selecting nearly everything is not automatically over-selection.

## Shadow evaluation and recall

1. Freeze the proposed subset before seeing outcomes. Keep historical features/graphs limited to information available at prediction time; train earlier and evaluate later.
2. Execute full validation on the same revision and compatible environment, comparing proposed inclusion with outcomes. Mozilla's shadow schedulers illustrate this approach. [Mozilla](https://hacks.mozilla.org/2020/07/testing-firefox-more-efficiently-with-machine-learning/)
3. Execute representative **selected-only** runs with realistic order, seeds, setup and isolation. Membership in the subset does not prove detection: removing neighboring tests can change collection, shared state or contention.
4. Preserve all full-only failures as suspected misses; classify product, test, infrastructure or unknown without discarding first-failure evidence. Historically flaky tests can reveal new regressions.
5. Roll out with an owner, miss/freshness policy, full audits, reserved audit capacity and rollback. Mandatory-contract omissions trigger correction or rollback.

Record metrics independently:

```text
membership recall = observed failing entries selected / observed failing entries
faulty-change detection recall = confirmed faulty changes actually caught
                              / confirmed faulty changes audited
omission fraction = omitted eligible entries / full eligible entries
data availability = complete qualified observations / intended observations
fallback rate = conservative fallbacks / selection decisions
```

Preserve configuration identity and avoid counting retries as independent entries. Predeclare outcome classification across attempts. Each recall is undefined when its denominator is zero, not 100%. Report actual subset execution detection separately from selection membership, and stratify by platform, owner and change/dependency class. A passing selected test can still be relevant validation. Overall accuracy or AUC on mostly passing cases does not establish regression recall or calibrated probabilities. [Predictive Test Selection](https://arxiv.org/abs/1810.05286)

For `N` independent representative faulty changes audited with zero misses, the exact one-sided 95% binomial upper miss bound is `1 - 0.05^(1/N)` (approximately `3/N` for large `N`). At 100 independent faulty changes, it is about 2.95%. Passing changes, repeated revisions of one bug and correlated planted mutations do not provide equivalent trials. Use exact sparse-event intervals and retain uncertainty about unrepresented changes. [NIST binomial intervals](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm)

Count planning, fallbacks, retries, full audits and maintenance in savings. Shadow mode retains full work and adds measurement overhead. For replacement audits with probability `a`, expected execution cost is `(1-a)*selected_cost + a*full_cost + observation_cost`. Additive audits require selected cost **plus** incremental audit cost. Price physical executions before averaging.

## Cache and result reuse

| Mechanism | Legitimate saving | Required qualification |
|---|---|---|
| Download cache | Transfer of identical packages | Integrity, compatibility, trust; installation may remain necessary |
| Build/task cache | Deterministic matching-input execution | Complete declared inputs/outputs and clean restoration |
| Dependency observation | Previously observed access relationships | Scope, completeness, version and provenance; missing edge is not independence |
| Successful-result reuse | Re-executing a still-valid contract | Entire relevant input closure, trusted producer, complete success, age and policy |
| Learned prediction | Proposed ranking/likelihood | Prospective detection evaluation; prediction is not successful execution |

For reusable results, bind source/tree, base where relevant, test/config inventory, dependencies, toolchain/runtime/platform, flags, relevant environment/external inputs, policy/selector version, producer, completion and artifact digest. State which changes can preserve validity. Source identity alone cannot represent changing security intelligence or external services; apply freshness deadlines where needed.

Verify identity **and** expected builder/parameters. Authentic provenance for the wrong commit/configuration is not valid proof, and provenance alone does not establish sufficient testing. [SLSA verification](https://slsa.dev/spec/v1.2/verifying-artifacts)

Qualify caches with input perturbations: compiler flag, transitive header, runtime/toolchain, schema, lockfile, test setup and environment value. Confirm invalidation or valid equivalent results as appropriate. Restore into empty output directories and compare clean execution; leftover files can mask incomplete entries. Maintain clean canaries. Bazel models action inputs/commands/environment; Turborepo assumes deterministic tasks for its known inputs. [Bazel](https://bazel.build/remote/caching), [Turborepo](https://turborepo.dev/docs/crafting-your-repository/caching)

Keep untrusted cache writers separate from privileged consumers. Do not store secrets in shared entries; GitHub fork PRs may read base-branch caches. Missing, cancelled, failed, incomplete, stale or unverifiable proof requires rerun or a nonpassing result. [GitHub cache access](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)

### Preserve the full qualification anchor

Treat full, partial and qualified-unchanged routes as different proof states. Example: full validation at time T0 anchors tree A. An engine-limited or isolated run at T1 can qualify only its declared subset. An unchanged route at T2 may link to the original full anchor when the complete relevant input closure remains equivalent, but must retain T0 and its freshness deadline. Neither partial execution nor reuse-only success creates a new full baseline or renews its age. Current checks outside the reused contract remain required.

Whole Git-tree equality can support source-content equivalence across different commit SHAs; also qualify producer event/repository, trusted policy, expected executed steps, current successful attempt, inventory, tool/runtime inputs and authenticated artifact identity/digest. Candidate-controlled flags cannot authorize omission of protected requirements. A skipped placeholder named “full” is not full execution. Generated inputs can depend on source-scanned docs/test strings, runtime reads and assets outside import graphs; include those inputs or demonstrate relevant generated-output equivalence.

Before executing a reused tool bundle, verify the expected producer and source-bound bytes, archive paths and links. A checksum shipped inside the same untrusted archive supplies no independent trust. Artifact listing alone does not establish successful consumption; any bounded transport retry must still verify the actual download and retain failed attempts. Missing, stale or partial full proof selects the approved full fallback or a nonpassing verdict, according to policy. Carry those distinct scenarios into the [acceptance ledger](experiments.md#scenario-acceptance-ledger).

When reviewing or changing anchor freshness, make the boundary checks concrete: a fresh complete original anchor with a valid chain permits reuse; a stale original behind recent partial/unchanged records, wrong tree, missing anchor, incomplete inventory or invalid future timestamp must not waive full qualification. Exercise the actual resolver and its protected fallback consumer; retain the observed result for each relevant case in the handoff.

## Test removal and quarantine

Slow runtime, similar names, unchanged line coverage, LOC ratios and no recent failures do not establish redundancy. For consolidation/deletion, record:

- Protected behavior, partitions, errors, platform and integration boundary.
- Old IDs and retained contract-owner/test IDs.
- Plausible or historical defect, with evidence retained checks fail on broken behavior and pass on correct behavior.
- Measured runtime/maintenance benefit and lost diagnostic precision.
- Contract-owner review and restoration route if audits find a gap.

Remove tautologies and demonstrated overlap while preserving independent negative cases, recovery, security and boundary behavior. Interpret surviving/equivalent/invalid mutants, timeouts and denominator changes; neither coverage nor mutation score alone authorizes deletion. [Stryker outcomes](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/)

Repair valuable flaky tests. Quarantine is an explicit temporary exception with owner, expiry, continued execution and necessary replacement protection. A passing retry does not prove the product correct; maintain first-pass and final-outcome metrics. Test-line budgets can expose growth, but do not prove what to remove.

## Negative gate cases

The aggregate must inspect actual prerequisite outcomes and expected inventory, not merely whether a reporting job ran.

| Condition | Required aggregate behavior |
|---|---|
| Trusted/current complete plan; all required execution succeeds | Pass |
| Explicit authorized not-applicable scope with reason | Pass with recorded scope |
| Complete reusable evidence meets validity policy | Pass with linked evidence |
| Failed/missing/malformed/wrong-revision/untrusted planner | Nonpassing despite downstream green jobs |
| Missing shard/report/entry or collection failure | Nonpassing |
| Required execution fails, times out or is cancelled | Nonpassing under the declared retry/exception policy |
| Unexpected zero-test result | Nonpassing until inapplicability is established |

Exercise these through a real candidate and actual protection rules, including fork, merge-group, schedule, failure and cancellation paths. Do not let PR-controlled code waive protected requirements by writing a selection flag. Provider job-level skips can appear successful while workflow-level skips leave required checks pending; validate semantics rather than relying on green display. [GitHub required-check troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)

Review the negative-test oracle too. Identify which inputs an attacker or ordinary producer can change and which authenticated invariants stay fixed. Exercise the actual resolver/download/consumer and required gate. Mutating an unused contents endpoint while holding an authenticated whole Git tree fixed does not demonstrate a wrong-tree bypass; reject that impossible or irrelevant oracle while retaining a feasible wrong-tree control. Record an invalid harness as such, rather than weakening valid source equality or adding an unnecessary production workaround.

Exceptions require visible reason, owner, scope and expiry/freshness rule. If protection or evidence is uncertain, preserve the broader required execution or block and explain the missing proof.
