# Repeatable skill evaluations

The source checkout contains five synthetic cases in `tests/evals/cases.json`: explicit invocation, indirect activation, an unrelated request, missing inputs, and a narrowly authorized workflow edit. Each case has a user prompt, minimal raw inputs, permitted file changes and an outcome rubric. The rubric is retained outside the evaluated workspace; it is not supplied to the agent.

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

Omit `--case` to run all five; repeat `--case` to select a subset. The per-case deadline is bounded to 30–900 seconds. Use a new output directory outside every Git repository for every run. Raw traces, answers, workspaces and host paths remain private there. Do not commit them or attach them to public issues. A sanitized trial record may retain case IDs, tested hashes, actual observations, reviewer decisions and limitations.

The runner stages the current complete skill under `.agents/skills/ci-health` in each isolated Git workspace, already on the `codex/skill-eval` task branch. The environment instructions identify that prepared branch and require task edits to stay in the workspace; the model need not modify sandbox-protected Git metadata to begin its task. It passes only the user prompt, synthetic inputs and offline side-effect constraints. The model gets skill metadata through discovery; the runner does not preload the skill body or tell indirect/negative cases which skill to select. Workspace-write sandboxing permits the narrow edit case, while shell network access and web search are disabled. This is an offline exercise, not authorization to use live tools or change CI settings.

User configuration is ignored for the subprocess, but host-global skills may remain discoverable. A read of another installed copy cannot establish activation of the staged instruction snapshot. Inspect such cases before drawing conclusions; do not change the user's installation or copy authentication files to make a trial pass.

## Interpret the evidence

Each case directory contains `prompt.txt`, `trace.jsonl`, `stderr.txt`, `answer.md` when produced, the final workspace, and `result.json`. The top-level `results.json` records CLI version, initial task branch, environment-constraint hash, source-input hashes, instruction hashes and limitations. Instruction hashes describe every staged skill file, not a claim that the agent read every reference. Use the trace to establish which resources were read. Exit 0 means all Codex turns completed; exit 2 means an invocation failed, timed out, produced incomplete evidence, or could not be prepared. Exit 0 is **not** a behavioral pass: inspect the automated checks and complete the rubric review.

- **Activation:** a positive check passes only when a completed successful command demonstrably reads the staged `SKILL.md` contents. An agent's claim to use the skill or a command merely naming the file is insufficient. Another installation, native injection without an observable read, truncated output, unsupported tool events or no positive read remains unknown. For the unrelated case, a complete trace without an observed skill read passes the scoped check; review the trace for unsupported/native loading before certifying non-activation.
- **Scope:** compare the input and final filesystem inventories. Unexpected additions, edits or deletions fail. Permitted changes are not automatically correct changes; inspect their meaning.
- **Behavior:** always starts pending. An independent reviewer reads the answer, tool trajectory and changed files against every case rubric, records pass/fail/unknown per criterion, and explains any failure. Do not grade by matching preferred wording or accept a model's self-report as evidence.

Repeat relevant cases after changes to descriptions, routing or workflow instructions. Compare observed behavior and resource usage across compatible host/model settings; retain failures and unknown results. One pass per scenario does not estimate reliability, prove cross-provider behavior, or validate live protection wiring. Broaden cases based on real failures rather than adding generic restrictions to the skill.

The workflow follows [OpenAI's skill testing guidance](https://developers.openai.com/plugins/build/skills#test-the-skill) and [evaluation guidance](https://developers.openai.com/blog/eval-skills). These source-only tools and fixtures are excluded from the runtime release archive.
