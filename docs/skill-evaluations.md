# Repeatable skill evaluations

The source checkout contains thirty-six synthetic cases in `tests/evals/cases.json`. Each has a user prompt, minimal raw inputs, permitted file changes and an outcome rubric. Rubrics and expected skill selections stay outside the evaluated workspace. The original twenty-one activation, scope, audit, preflight and optimization cases remain alongside eleven mechanism-focused cases and four copy-discovery boundary cases.

The repository audits require following workflows through nested tasks, preparation, tool launches, suite membership, and harnesses. One includes repeated work alongside conspicuous operational failures with little demonstrated CI impact. The control retains distinct validation configurations, stateful deployment serialization, and relevant scheduled qualification. Their rubrics assess prioritization and evidence-qualified remedies rather than counting findings. Source-only paths establish configured behavior, not observed physical execution or measured savings.

The preflight cases use real synthetic Git comparisons. They exercise explicit and implicit invocation, routing from CI Health during shipping, indirect application inputs, justified validation, missing comparison evidence, and an explicit broad audit during shipping. A mixed-state candidate includes committed, indexed, working-tree and untracked changes, with renamed and deleted files. Existing inefficient work and operational distractions test whether recommendations remain limited to the change.

Optimization cases exercise duration-weighted shard replay, removal of a false job dependency, handling of an unsafe selector, an optional Bun migration comparison, targeted optimization requested through CI Health during shipping, and moving a compatibility check off the staging path. Review unexpected Optimize reads in audit and preflight controls as well as missed reads in implicit positives.

The added corpus targets observed miss classes with synthetic source and observations:

| Cases | Evidence being tested |
|---|---|
| `preflight-browser-composite`, `preflight-asserted-capture-control` | Unchanged discovered inventory with larger inner loops; project filters; recording versus retention/upload; worker reduction; required consumers; useful asserted images as a control |
| `preflight-shard-fixed-cost` | Repeated provisioning and an indivisible file/test tail despite a larger matrix |
| `audit-terminal-fallback-ledger`, `optimize-terminal-fallback-ledger`, `optimize-terminal-control` | Actual publication versus staging; warm reuse versus missing-proof mixed/cold routes; first-attempt failures and green target misses; a successful nearby control |
| `preflight-resource-cleanup`, `preflight-resource-control` | Resource repair that adds a measured preparation regression versus bounded owned-scratch cleanup with accepted observations |
| `preflight-stale-review`, `preflight-inherited-guard-control` | A review fingerprint invalidated by a helper edit before the next draft push versus inherited browser latency outside a narrow guard change |
| `optimize-proof-original-age` | A possible authenticated proof chain that improperly renews full qualification age; negative checks at the actual resolver boundary |

The browser fixture supplies its capture implementation, so the review must establish behavior from code rather than assume a diagnostic mode's name determines its cost. Configured work is a sum across applicable groups: already expanded test/project inventories must not be multiplied by projects again. Controls should allow a completed static review without inventing a timing guarantee or manufacturing a blocker.

The copy-discovery controls distinguish a shipping mention from a CI task. `preflight-implicit-docs-copy` and `preflight-implicit-translation-copy` expect ordinary proportional review without loading CI-specific skills; the original `preflight-unrelated-copy` remains unchanged. `preflight-explicit-copy` requires honoring a named Preflight invocation and returning a brief no-impact result. `preflight-implicit-scanned-content` follows Markdown through a real source-scanning generator and downstream style check, preventing a filename-based exclusion. Preserve the original implicit script and route-data positives when changing descriptions or routing. Repeat the copy negatives and affected positives under comparable settings, inspect traces for unnecessary reads, and record final behavior separately from selection uncertainty.

Run the offline suite normally:

```bash
python3 -m unittest discover -s tests -v
```

Those tests verify the evaluation recorder's evidence handling and isolation. They do **not** run a model, establish activation quality or grade skill behavior.

## Run a behavioral trial

Use an already authenticated Codex CLI with `exec --ignore-user-config`, `--ephemeral` and JSON event output, plus Git and Python 3.11+. The runner does not sign in, copy credentials, change host configuration or choose a model. Model/provider defaults apply; record the effective model from the retained trace/stderr when interpreting results. Each invocation uses the provider and may consume usage, so these trials are opt-in and are not part of ordinary CI.

```bash
python3 scripts/evaluate_skill.py list
python3 scripts/evaluate_skill.py run \
  --case indirect-audit \
  --out /absolute/private-evidence/indirect-trial \
  --timeout 300
```

Omit `--case` to run all cases. Repeat `--case` to select a subset. The per-case deadline is bounded to 30–900 seconds. Use a new output directory outside every Git repository for every run. Raw traces, answers, workspaces and host paths remain private there. Do not commit them or attach them to public issues. A sanitized trial record may retain case IDs, tested hashes, actual observations, reviewer decisions and limitations.

The runner stages the complete skills under `.agents/skills/` in each isolated Git workspace on the `codex/skill-eval` task branch. The environment instructions identify that prepared branch and require task edits to stay in the workspace. The model gets skill metadata through discovery and receives only the user prompt, synthetic inputs and offline side-effect constraints. Workspace-write sandboxing permits local edits while the exercise disables shell network access and web search.

Cases may add a `git` fixture with complete `base_files`, `head_files`, and `index_files` snapshots; omitted head/index snapshots inherit the preceding state. For these cases, `files` is the complete final fixture working tree. `base_ref` defaults to `main`; null deliberately omits that ref for missing-base trials. Framework instructions and staged skills remain constant outside these fixture snapshots. Fixture construction uses synthetic identity and process-local Git configuration; it does not change host settings. Original cases retain their earlier setup.

User configuration is ignored for the subprocess, but host-global skills may remain discoverable. A read of another installed copy cannot establish activation of the staged instruction snapshot. Inspect such cases before drawing conclusions; do not change the user's installation or copy authentication files to make a trial pass.

## Interpret the evidence

Each case directory contains `prompt.txt`, `trace.jsonl`, `stderr.txt`, `answer.md` when produced, the final workspace, and `result.json`. The top-level `results.json` records CLI version, initial task branch, environment-constraint hash, source-input hashes, instruction hashes and limitations. Instruction hashes describe every staged skill file, not a claim that the agent read every reference. Use the trace to establish which resources were read. Exit 0 means all Codex turns completed; exit 2 means an invocation failed, timed out, produced incomplete evidence, or could not be prepared. Exit 0 is **not** a behavioral pass: inspect the automated checks and complete the rubric review.

- **Activation:** a positive check passes only when a completed successful command demonstrably reads the staged `SKILL.md` contents. An agent's claim to use the skill or a command merely naming the file is insufficient. Another installation, native injection without an observable read, truncated output, unsupported tool events or no positive read remains unknown. For the unrelated case, a complete trace without an observed skill read passes the scoped check; review the trace for unsupported/native loading before certifying non-activation.
- **Per-skill selection.** Legacy cases retain their CI Health activation check. For cases declaring `expected_skills`, a positive list requires those reads and an empty list checks for absence of observed reads of every staged skill. Review additional reads separately in positive cases. Correct scoped behavior can coexist with unknown activation or an unnecessary skill read. Retain those differences in the trial record.
- **Scope:** compare input and final file inventories (contents, regular-file permissions, and symlink identities) plus Git HEAD, refs, and index state. Unexpected additions, edits, permission changes, deletions, staging, commits or ref changes fail. Permitted file changes are not automatically correct changes; inspect their meaning. Final inventories do not establish the absence of transient or outside-workspace effects.
- **Behavior:** always starts pending. An independent reviewer reads the answer, tool trajectory and changed files against every case rubric, records pass/fail/unknown per criterion, and explains any failure. Do not grade by matching preferred wording or accept a model's self-report as evidence. `behavior_dimensions` is a pending review worksheet, not automated scoring: record evidence such as tool-item IDs, source locations, answer excerpts and resulting file checks before assigning a result. Use not-applicable for dimensions the scenario does not exercise.

Review the dimensions separately: material-regression recall, false clean verdicts, false blockers, inspection evidence, numeric honesty, scope discipline, candidate refresh and proof handling. A false clean means a confirmed regression or source-supported material risk was omitted or presented as no concern; unknown timing or justified extra coverage alone does not establish one. A false blocker means the review invents a mandatory stop for valid scoped work or treats an inherited problem as introduced. Report denominators and unknowns when calculating rates; do not average a control into material-regression recall or treat unreviewed results as passes.

Inspection evidence must show reading the material implementation and following it through real callers and consumers. Mentioning screenshots, caches or a budget in a final answer does not establish that inspection. Candidate identity must cover relevant dirty and untracked inputs, and a prior receipt applies only to the state actually reviewed.

For a conversational refresh trial, retain an initial completed review, then change a material shared helper and ask for readiness before the next draft push. Observe whether the reviewer refreshes affected paths and keeps unaffected inspection reusable. Pair this with an unrelated copy edit. The static `preflight-stale-review` fixture exercises a saved receipt mismatch; it alone does not establish multi-turn refresh behavior. Keep these trials in isolated private workspaces with held-out variants and frozen instruction/input hashes.

Repeat relevant cases after changes to descriptions, routing or workflow instructions. Compare observed behavior and resource usage across compatible host/model settings; retain failures and unknown results. One pass per scenario does not estimate reliability, prove cross-provider behavior, or validate live protection wiring. Broaden cases based on real failures rather than adding generic restrictions to the skill.

The workflow follows [OpenAI's skill testing guidance](https://developers.openai.com/plugins/build/skills#test-the-skill) and [evaluation guidance](https://developers.openai.com/blog/eval-skills). These source-only tools and fixtures are excluded from the runtime release archive.
