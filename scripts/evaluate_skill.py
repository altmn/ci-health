#!/usr/bin/env python3
"""Opt-in Codex behavior trials; private artifacts and explicit review, not CI certification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import shlex
import signal
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/evals/cases.json"
SKILL = ROOT / "skills/ci-health"
BRANCH = "codex/skill-eval"
CONSTRAINTS = (
    "This repository is a synthetic offline exercise. Do not access network services or "
    "credentials, publish anything, or modify host configuration. Follow the user's requested scope. "
    "The task branch is already prepared. Keep task edits in this workspace.\n"
)


class EvaluationError(ValueError):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_private(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
        stream.write(content)


def write_json(path, value):
    write_private(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def safe_relative(value):
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts and "\\" not in value and path.as_posix() == value


def load_cases(path=CASES):
    payload = json.loads(path.read_text())
    if payload.get("schema") != "ci-health.skill-evals/v1":
        raise EvaluationError("Unsupported evaluation schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 20:
        raise EvaluationError("Expected 1–20 cases")
    ids = set()
    for case in cases:
        identifier = case.get("id", "")
        if not identifier or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in identifier) or identifier in ids:
            raise EvaluationError("Case IDs must be unique lowercase names")
        ids.add(identifier)
        if type(case.get("activation")) is not bool or not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise EvaluationError("Each case needs an activation boolean and prompt")
        if not isinstance(case.get("files"), dict) or not isinstance(case.get("allowed_changes"), list):
            raise EvaluationError("Each case needs input files and allowed changes")
        for name, content in case["files"].items():
            if not safe_relative(name) or PurePosixPath(name).parts[0] in (".git", ".agents") or name == "AGENTS.md" or not isinstance(content, str):
                raise EvaluationError("Unsafe or reserved fixture path")
        if any(not safe_relative(name) for name in case["allowed_changes"]):
            raise EvaluationError("Unsafe allowed-change path")
        if not isinstance(case.get("review_checks"), list) or not case["review_checks"]:
            raise EvaluationError("Each case needs an external review rubric")
    return cases


def external_output(value):
    path = Path(value).expanduser()
    if not path.is_absolute() or path.exists() or path.is_symlink():
        raise EvaluationError("Output must be a new absolute directory")
    path = path.resolve()
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(parent), "rev-parse", "--is-inside-work-tree", "--is-inside-git-dir", "--is-bare-repository"],
                            capture_output=True, text=True, env=env, timeout=20)
    if result.returncode != 128 or "not a git repository" not in result.stderr.lower():
        raise EvaluationError("Output must be outside Git repositories")
    return path


def snapshot(workspace):
    result = {}
    for path in workspace.rglob("*"):
        relative = path.relative_to(workspace).as_posix()
        if relative.startswith(".git/"):
            continue
        if path.is_symlink():
            result[relative] = "symlink:" + os.readlink(path)
        elif path.is_file():
            result[relative] = sha256(path.read_bytes())
    return result


def prepare_case(case, directory):
    workspace = directory / "workspace"
    workspace.mkdir(parents=True, mode=0o700)
    staged = workspace / ".agents/skills/ci-health"
    shutil.copytree(SKILL, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    write_private(workspace / "AGENTS.md", CONSTRAINTS)
    for name, content in case["files"].items():
        write_private(workspace / name, content)
    subprocess.run(["git", "init", "--quiet", f"--initial-branch={BRANCH}", str(workspace)], check=True, capture_output=True)
    return workspace, staged, snapshot(workspace)


def references_staged_skill(command, staged):
    """Bind literal file arguments; ambiguous shell working directories stay unknown."""
    def tokens_for(value):
        lexer = shlex.shlex(value, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        return list(lexer)

    try:
        tokens = tokens_for(command)
        for _ in range(3):
            if tokens and Path(tokens[0]).name in ("sh", "bash", "zsh", "dash"):
                option = next((index for index, value in enumerate(tokens[1:], 1)
                               if value.startswith("-") and "c" in value), None)
                if option is not None and option + 1 < len(tokens):
                    tokens = tokens_for(tokens[option + 1])
                    continue
            break
    except ValueError:
        return False
    if str(staged / "SKILL.md") in tokens:
        return True
    # Relative paths resolve from the --cd workspace only without a cwd-changing wrapper.
    if not tokens or Path(tokens[0]).name not in ("cat", "sed", "head", "tail", "nl", "bat"):
        return False
    if any(token in ("cd", "pushd", "popd", "eval", "source", ".") or "`" in token or "$(" in token for token in tokens):
        return False
    return any(token in (".agents/skills/ci-health/SKILL.md", "./.agents/skills/ci-health/SKILL.md") for token in tokens)


def inspect_trace(text, staged, skill_text, returncode, timed_out=False):
    """Require a complete trace and successful tool output; prose alone proves nothing."""
    parsed, malformed = [], False
    for line in text.splitlines():
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                malformed = True
            else:
                parsed.append(event)
        except ValueError:
            malformed = True
    complete = (returncode == 0 and not timed_out and not malformed
                and any(event.get("type") == "turn.completed" for event in parsed)
                and not any(event.get("type") in ("error", "turn.failed") for event in parsed))
    reads, other_reads = [], []
    for event in parsed:
        item = event.get("item", {})
        if not isinstance(item, dict) or event.get("type") != "item.completed" or item.get("type") != "command_execution" or item.get("exit_code") != 0:
            continue
        command, output = item.get("command", ""), item.get("aggregated_output", "")
        if not isinstance(command, str) or not isinstance(output, str):
            continue
        if skill_text.strip() not in output:
            continue
        # The output proves instruction contents were read; the path binds the tested copy.
        if references_staged_skill(command, staged):
            reads.append(item.get("id"))
        else:
            other_reads.append(item.get("id"))
    observed = "staged-skill-read" if reads else "other-or-unresolved-skill-read" if other_reads else "no-skill-read-observed"
    return {"complete": complete, "observation": observed, "read_item_ids": reads, "other_read_item_ids": other_reads}


def assess(case, trace, before, after):
    changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    unexpected = sorted(set(changed) - set(case["allowed_changes"]))
    activation = "unknown"
    if trace["complete"]:
        if trace["observation"] == "staged-skill-read":
            activation = "pass" if case["activation"] else "fail"
        elif trace["observation"] == "other-or-unresolved-skill-read":
            activation = "unknown" if case["activation"] else "fail"
        elif not case["activation"]:
            activation = "pass"
    return {"activation_check": activation, "scope_check": "fail" if unexpected else "pass" if trace["complete"] else "unknown",
            "changed_files": changed, "unexpected_changed_files": unexpected,
            "behavior_review": "pending", "review_checks": case["review_checks"]}


def run_case(case, directory, executable, timeout):
    workspace, staged, before = prepare_case(case, directory)
    initial_branch = subprocess.run(["git", "-C", str(workspace), "symbolic-ref", "--short", "HEAD"],
                                    check=True, capture_output=True, text=True, timeout=20).stdout.strip()
    prompt = case["prompt"]
    write_private(directory / "prompt.txt", prompt)
    command = [executable, "exec", "--ignore-user-config", "--ephemeral", "--json", "--color", "never",
               "--sandbox", "workspace-write", "-c", "sandbox_workspace_write.network_access=false",
               "-c", 'web_search="disabled"', "--cd", str(workspace),
               "--output-last-message", str(directory / "answer.md"), "-"]
    # No expected answers, activation labels or rubrics enter the prompt/workspace.
    timed_out = False
    with open(directory / "trace.jsonl", "x") as output, open(directory / "stderr.txt", "x") as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=output, stderr=errors, text=True, start_new_session=True)
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
    trace = inspect_trace((directory / "trace.jsonl").read_text(), staged, (staged / "SKILL.md").read_text(), process.returncode, timed_out)
    result = {"id": case["id"], "category": case["category"], "returncode": process.returncode, "timed_out": timed_out,
              "trace": trace, **assess(case, trace, before, snapshot(workspace)),
              "initial_branch": initial_branch, "environment_constraints_sha256": before["AGENTS.md"],
              "prompt_sha256": sha256(prompt.encode()), "input_sha256": {name: sha256(value.encode()) for name, value in case["files"].items()},
              "instruction_sha256": {name.removeprefix(".agents/skills/ci-health/"): digest for name, digest in before.items() if name.startswith(".agents/skills/ci-health/")}}
    write_json(directory / "result.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "run"))
    parser.add_argument("--case", action="append", dest="ids", help="Case ID; repeat to select multiple. Default: all.")
    parser.add_argument("--out", help="New absolute directory outside Git; required for run")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds per case, 30–900 (default: 300)")
    args = parser.parse_args(argv)
    try:
        cases = load_cases()
        if args.ids:
            if set(args.ids) - {case["id"] for case in cases}:
                raise EvaluationError("Unknown case ID")
            cases = [case for case in cases if case["id"] in args.ids]
        if args.command == "list":
            print(json.dumps([{key: case[key] for key in ("id", "category", "activation")} for case in cases], indent=2))
            return 0
        if not args.out or not 30 <= args.timeout <= 900:
            raise EvaluationError("run needs --out and timeout between 30 and 900 seconds")
        executable = shutil.which("codex")
        if not executable:
            raise EvaluationError("Install and authenticate Codex before running behavioral trials")
        destination = external_output(args.out)
        destination.mkdir(parents=True, mode=0o700)
        old_umask = os.umask(0o077)
        try:
            version = subprocess.run([executable, "--version"], capture_output=True, text=True, check=True, timeout=20).stdout.strip()
            results = []
            for case in cases:
                result = run_case(case, destination / case["id"], executable, args.timeout)
                results.append(result)
                print(f"{case['id']}: activation={result['activation_check']}; scope={result['scope_check']}; behavior=pending", flush=True)
            write_json(destination / "results.json", {"schema": "ci-health.skill-eval-results/v1", "created_at": datetime.now(timezone.utc).isoformat(),
                       "codex_version": version, "case_manifest_sha256": sha256(CASES.read_bytes()), "results": results,
                       "limitations": ["Behavioral rubrics require independent review of answers, traces and resulting files.",
                                       "No observed read does not prove positive activation failed; native injection or unsupported trace tools are unknown.",
                                       "Host-global skills may remain discoverable; only observed staged skill reads bind positive activation to the tested snapshot.",
                                       "One run per case is not a reliability estimate; provider/model defaults and nondeterminism can change results."]})
        finally:
            os.umask(old_umask)
        return 0 if all(result["trace"]["complete"] for result in results) else 2
    except (EvaluationError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"skill-evals: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
