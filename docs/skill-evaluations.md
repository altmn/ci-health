# Repeatable skill evaluations

The source checkout contains fifteen synthetic cases in `tests/evals/cases.json`: the original seven audit, activation, missing-input and narrow-edit cases, plus eight preflight/routing cases. Each case has a user prompt, minimal raw inputs, permitted file changes and an outcome rubric. Rubrics and expected skill selections remain outside the evaluated workspace; they are not supplied to the agent.

The repository audits require following workflows through nested tasks, preparation, tool launches, suite membership, and harnesses. One includes repeated work alongside conspicuous operational failures with little demonstrated CI impact. The control retains distinct validation configurations, stateful deployment serialization, and relevant scheduled qualification. Their rubrics assess prioritization and evidence-qualified remedies rather than counting findings. Source-only paths establish configured behavior, not observed physical execution or measured savings.

The preflight cases use real synthetic Git comparisons. They exercise explicit and implicit invocation, routing from CI Health during shipping, indirect application inputs, justified validation, missing comparison evidence, and an explicit broad audit during shipping. A mixed-state candidate includes committed, indexed, working-tree and untracked changes, with renamed and deleted files. Existing inefficient work and operational distractions test whether recommendations remain limited to the change.

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

Omit `--case` to run all fifteen; repeat `--case` to select a subset. The per-case deadline is bounded to 30–900 seconds. Use a new output directory outside every Git repository for every run. Raw traces, answers, workspaces and host paths remain private there. Do not commit them or attach them to public issues. A sanitized trial record may retain case IDs, tested hashes, actual observations, reviewer decisions and limitations.

The runner stages both complete skills under `.agents/skills/` in each isolated Git workspace, already on the `codex/skill-eval` task branch. The environment instructions identify that prepared branch and require task edits to stay in the workspace; the model need not modify sandbox-protected Git metadata to begin its task. It passes only the user prompt, synthetic inputs and offline side-effect constraints. The model gets skill metadata through discovery; the runner does not preload skill bodies or tell indirect/negative cases which skill to select. Workspace-write sandboxing permits the narrow edit case, while shell network access and web search are disabled. This is an offline exercise, not authorization to use live tools or change CI settings.

Cases may add a `git` fixture with complete `base_files`, `head_files`, and `index_files` snapshots; omitted head/index snapshots inherit the preceding state. For these cases, `files` is the complete final fixture working tree. `base_ref` defaults to `main`; null deliberately omits that ref for missing-base trials. Framework instructions and staged skills remain constant outside these fixture snapshots. Fixture construction uses synthetic identity and process-local Git configuration; it does not change host settings. Original cases retain their earlier setup.

User configuration is ignored for the subprocess, but host-global skills may remain discoverable. A read of another installed copy cannot establish activation of the staged instruction snapshot. Inspect such cases before drawing conclusions; do not change the user's installation or copy authentication files to make a trial pass.

## Interpret the evidence

Each case directory contains `prompt.txt`, `trace.jsonl`, `stderr.txt`, `answer.md` when produced, the final workspace, and `result.json`. The top-level `results.json` records CLI version, initial task branch, environment-constraint hash, source-input hashes, instruction hashes and limitations. Instruction hashes describe every staged skill file, not a claim that the agent read every reference. Use the trace to establish which resources were read. Exit 0 means all Codex turns completed; exit 2 means an invocation failed, timed out, produced incomplete evidence, or could not be prepared. Exit 0 is **not** a behavioral pass: inspect the automated checks and complete the rubric review.

- **Activation:** a positive check passes only when a completed successful command demonstrably reads the staged `SKILL.md` contents. An agent's claim to use the skill or a command merely naming the file is insufficient. Another installation, native injection without an observable read, truncated output, unsupported tool events or no positive read remains unknown. For the unrelated case, a complete trace without an observed skill read passes the scoped check; review the trace for unsupported/native loading before certifying non-activation.
- **Per-skill selection:** legacy cases retain their CI Health activation check. New cases declare `expected_skills`; a positive list requires those reads while permitting an additional router read. An empty list checks for neither skill. Both skill observations and file hashes are recorded separately. Correct scoped behavior can coexist with unknown activation or an unnecessary skill read; retain those differences in the trial record.
- **Scope:** compare input and final filesystem inventories plus Git HEAD, refs, and index state. Unexpected additions, edits, deletions, staging, commits or ref changes fail. Permitted file changes are not automatically correct changes; inspect their meaning.
- **Behavior:** always starts pending. An independent reviewer reads the answer, tool trajectory and changed files against every case rubric, records pass/fail/unknown per criterion, and explains any failure. Do not grade by matching preferred wording or accept a model's self-report as evidence.

Repeat relevant cases after changes to descriptions, routing or workflow instructions. Compare observed behavior and resource usage across compatible host/model settings; retain failures and unknown results. One pass per scenario does not estimate reliability, prove cross-provider behavior, or validate live protection wiring. Broaden cases based on real failures rather than adding generic restrictions to the skill.

The workflow follows [OpenAI's skill testing guidance](https://developers.openai.com/plugins/build/skills#test-the-skill) and [evaluation guidance](https://developers.openai.com/blog/eval-skills). These source-only tools and fixtures are excluded from the runtime release archive.
