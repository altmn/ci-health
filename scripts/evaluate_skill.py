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
import stat
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/evals/cases.json"
SKILL = ROOT / "skills/ci-health"
SKILLS = {name: ROOT / "skills" / name for name in ("ci-health", "ci-health-preflight")}
BRANCH = "codex/skill-eval"
CONSTRAINTS = (
    "This repository is a synthetic offline exercise. Do not access network services or "
    "credentials, publish anything, or modify host configuration. Follow the user's requested scope. "
    "The task branch is already prepared. Keep task edits in this workspace; do not stage, "
    "commit, or change Git references.\n"
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


def validate_files(files):
    if not isinstance(files, dict):
        raise EvaluationError("Fixture snapshots must be file mappings")
    folded = set()
    for name, content in files.items():
        if (not safe_relative(name) or "\0" in name
                or PurePosixPath(name).parts[0].casefold() in (".git", ".agents")
                or name.casefold() == "agents.md" or not isinstance(content, str)):
            raise EvaluationError("Unsafe or reserved fixture path")
        if name.casefold() in folded:
            raise EvaluationError("Case-colliding fixture paths")
        folded.add(name.casefold())
    if any(parent.as_posix().casefold() in folded for name in files for parent in PurePosixPath(name).parents if str(parent) != "."):
        raise EvaluationError("Conflicting fixture paths")


def valid_base_ref(value):
    # Keep fixtures to ordinary local branches, never option/refspec/revision syntax.
    return (isinstance(value, str) and value != BRANCH and bool(value)
            and all(part and part[0] not in ".-" and not part.endswith((".", ".lock"))
                    for part in value.split("/"))
            and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/ ." for c in value)
            and not any(token in value for token in ("..", " ", "//")) and value != "HEAD")


def load_cases(path=CASES):
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict) or payload.get("schema") != "ci-health.skill-evals/v1":
        raise EvaluationError("Unsupported evaluation schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 20:
        raise EvaluationError("Expected 1–20 cases")
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise EvaluationError("Each case must be an object")
        identifier = case.get("id", "")
        if not isinstance(identifier, str) or not identifier or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in identifier) or identifier in ids:
            raise EvaluationError("Case IDs must be unique lowercase names")
        ids.add(identifier)
        if type(case.get("activation")) is not bool or not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise EvaluationError("Each case needs an activation boolean and prompt")
        if not isinstance(case.get("files"), dict) or not isinstance(case.get("allowed_changes"), list):
            raise EvaluationError("Each case needs input files and allowed changes")
        validate_files(case["files"])
        if any(not safe_relative(name) or "\0" in name for name in case["allowed_changes"]):
            raise EvaluationError("Unsafe allowed-change path")
        if "expected_skills" in case:
            expected = case["expected_skills"]
            if (not isinstance(expected, list) or any(not isinstance(name, str) or name not in SKILLS for name in expected)
                    or len(set(expected)) != len(expected) or bool(expected) != case["activation"]):
                raise EvaluationError("Invalid expected skills")
        if "git" in case:
            setup = case["git"]
            if not isinstance(setup, dict) or "base_files" not in setup or set(setup) - {"base_files", "head_files", "index_files", "base_ref"}:
                raise EvaluationError("Invalid Git fixture setup")
            for name in ("base_files", "head_files", "index_files"):
                if name in setup:
                    validate_files(setup[name])
            base_ref = setup.get("base_ref", "main")
            if base_ref is not None and not valid_base_ref(base_ref):
                raise EvaluationError("Invalid fixture base ref")
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
            result[relative] = {"type": "symlink", "target": os.readlink(path),
                                "mode": stat.S_IMODE(path.lstat().st_mode)}
        elif path.is_file():
            result[relative] = {"type": "file", "sha256": sha256(path.read_bytes()),
                                "mode": stat.S_IMODE(path.stat().st_mode)}
    return result


def git_environment():
    """Do not import host Git identity, signing, excludes, hooks or routing into fixtures."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="Synthetic Evaluator", GIT_COMMITTER_NAME="Synthetic Evaluator",
               GIT_AUTHOR_EMAIL="evaluation@example.invalid", GIT_COMMITTER_EMAIL="evaluation@example.invalid",
               GIT_AUTHOR_DATE="2020-01-01T00:00:00Z", GIT_COMMITTER_DATE="2020-01-01T00:00:00Z")
    settings = {"core.excludesFile": os.devnull, "core.hooksPath": os.devnull,
                "commit.gpgSign": "false", "tag.gpgSign": "false"}
    env["GIT_CONFIG_COUNT"] = str(len(settings))
    for index, (key, value) in enumerate(settings.items()):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    return env


def git(workspace, *arguments, check=True):
    return subprocess.run(["git", "-C", str(workspace), *arguments], check=check, capture_output=True,
                          text=True, env=git_environment(), timeout=20)


def git_state(workspace):
    head = git(workspace, "rev-parse", "--verify", "HEAD", check=False)
    symbolic = git(workspace, "symbolic-ref", "--quiet", "HEAD", check=False)
    if head.returncode not in (0, 128) or symbolic.returncode not in (0, 1):
        raise EvaluationError("Cannot inspect evaluation Git state")
    return {"head": head.stdout.strip() if head.returncode == 0 else None,
            "symbolic_head": symbolic.stdout.strip() if symbolic.returncode == 0 else None,
            "refs": git(workspace, "for-each-ref", "--format=%(refname) %(objectname)").stdout.splitlines(),
            "index": git(workspace, "ls-files", "-v", "--stage", "-z").stdout.split("\0")[:-1],
            "reflog": git(workspace, "reflog", "show", "--all", "--format=%H %gD").stdout.splitlines()}


def replace_fixture(workspace, previous, files):
    for name in previous:
        target = workspace / name
        if target.is_file():
            target.unlink()
    # Remove empty old parents so snapshots can change files into directories and back.
    parents = {parent for name in previous for parent in (workspace / name).parents if parent.is_relative_to(workspace) and parent != workspace}
    for parent in sorted(parents, key=lambda path: len(path.parts), reverse=True):
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
    for name, content in files.items():
        write_private(workspace / name, content)


def prepare_case(case, directory):
    workspace = directory / "workspace"
    workspace.mkdir(parents=True, mode=0o700)
    staged = workspace / ".agents/skills/ci-health"
    for name, source in SKILLS.items():
        shutil.copytree(source, workspace / ".agents/skills" / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    write_private(workspace / "AGENTS.md", CONSTRAINTS)
    git(workspace, "init", "--quiet", f"--initial-branch={BRANCH}")
    setup = case.get("git")
    if setup is not None:
        base = setup["base_files"]
        head = setup.get("head_files", base)
        index = setup.get("index_files", head)
        replace_fixture(workspace, {}, base)
        git(workspace, "add", "--all", "--force")
        git(workspace, "commit", "--quiet", "-m", "Synthetic base")
        base_ref = setup.get("base_ref", "main")
        if base_ref is not None:
            git(workspace, "branch", base_ref)
        if head != base:
            replace_fixture(workspace, base, head)
            git(workspace, "add", "--all", "--force")
            git(workspace, "commit", "--quiet", "-m", "Synthetic candidate")
        replace_fixture(workspace, head, index)
        git(workspace, "add", "--all", "--force")
        replace_fixture(workspace, index, case["files"])
    else:
        replace_fixture(workspace, {}, case["files"])
    return workspace, staged, snapshot(workspace)


def references_staged_skill(command, staged):
    """Bind literal file arguments; ambiguous shell working directories stay unknown."""
    def tokens_for(value):
        if "\n" in value or "\r" in value:
            raise ValueError("Multiline commands cannot establish a direct read")
        lexer = shlex.shlex(value, posix=True, punctuation_chars=";&|()<>")
        lexer.whitespace_split = True
        lexer.whitespace = " \t\r"
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
    # Bind only a direct reader, not paths printed by echo or later compound commands.
    # Relative paths resolve from --cd only without a cwd-changing wrapper.
    if not tokens or Path(tokens[0]).name not in ("cat", "sed", "head", "tail", "nl", "bat"):
        return False
    if any(token in ("cd", "pushd", "popd", "eval", "source", ".") or "`" in token or "$(" in token
           or any(character in token for character in ";&|()<>\n\r") for token in tokens):
        return False
    relative = f".agents/skills/{staged.name}/SKILL.md"
    return any(token in (str(staged / "SKILL.md"), relative, "./" + relative) for token in tokens)


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


def activation_assessment(trace, expected):
    activation = "unknown"
    if trace["complete"]:
        if trace["observation"] == "staged-skill-read":
            activation = "pass" if expected else "fail"
        elif trace["observation"] == "other-or-unresolved-skill-read":
            activation = "unknown" if expected else "fail"
        elif not expected:
            activation = "pass"
    return activation


def assess(case, trace, before, after, *, skill_traces=None, git_before=None, git_after=None):
    changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    unexpected = sorted(set(changed) - set(case["allowed_changes"]))
    activation = activation_assessment(trace, case["activation"])
    by_skill = {"ci-health": activation}
    if "expected_skills" in case:
        if skill_traces is None:
            raise EvaluationError("Expected-skill cases require both skill observations")
        expected = case["expected_skills"]
        by_skill = {name: activation_assessment(skill_traces[name], bool(expected)) for name in (expected or SKILLS)}
        activation = "fail" if "fail" in by_skill.values() else "pass" if all(value == "pass" for value in by_skill.values()) else "unknown"
    git_changes = [] if git_before is None and git_after is None else sorted(
        key for key in set(git_before or {}) | set(git_after or {}) if (git_before or {}).get(key) != (git_after or {}).get(key))
    return {"activation_check": activation, "activation_by_skill": by_skill,
            "scope_check": "fail" if unexpected or git_changes else "pass" if trace["complete"] else "unknown",
            "changed_files": changed, "unexpected_changed_files": unexpected,
            "git_changes": git_changes,
            "behavior_review": "pending", "review_checks": case["review_checks"]}


def run_case(case, directory, executable, timeout):
    workspace, staged, before = prepare_case(case, directory)
    initial_branch = git(workspace, "symbolic-ref", "--short", "HEAD").stdout.strip()
    git_before = git_state(workspace)
    skill_texts = {name: (workspace / ".agents/skills" / name / "SKILL.md").read_text() for name in SKILLS}
    prompt = case["prompt"]
    write_private(directory / "prompt.txt", prompt)
    command = [executable, "exec", "--ignore-user-config", "--ephemeral", "--json", "--color", "never",
               "--sandbox", "workspace-write", "-c", "sandbox_workspace_write.network_access=false",
               "-c", 'web_search="disabled"', "--cd", str(workspace),
               "--output-last-message", str(directory / "answer.md"), "-"]
    # No expected answers, activation labels or rubrics enter the prompt/workspace.
    timed_out = False
    with open(directory / "trace.jsonl", "x") as output, open(directory / "stderr.txt", "x") as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=output, stderr=errors, text=True,
                                   start_new_session=True, env=git_environment())
        try:
            process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
    trace_text = (directory / "trace.jsonl").read_text()
    skill_traces = {name: inspect_trace(trace_text, workspace / ".agents/skills" / name,
                                      skill_texts[name],
                                      process.returncode, timed_out) for name in SKILLS}
    trace = skill_traces["ci-health"]
    try:
        git_after = git_state(workspace)
    except (EvaluationError, OSError, subprocess.SubprocessError) as exc:
        git_after = {"inspection_error": type(exc).__name__}
    instruction_hashes = {skill: {name.removeprefix(f".agents/skills/{skill}/"): record["sha256"] for name, record in before.items()
                                  if name.startswith(f".agents/skills/{skill}/")} for skill in SKILLS}
    result = {"id": case["id"], "category": case["category"], "returncode": process.returncode, "timed_out": timed_out,
              "trace": trace, "skill_traces": skill_traces,
              **assess(case, trace, before, snapshot(workspace), skill_traces=skill_traces, git_before=git_before, git_after=git_after),
              "git_state_before": git_before, "git_state_after": git_after,
              "initial_branch": initial_branch, "environment_constraints_sha256": before["AGENTS.md"]["sha256"],
              "prompt_sha256": sha256(prompt.encode()), "input_sha256": {name: sha256(value.encode()) for name, value in case["files"].items()},
              "instruction_sha256": instruction_hashes["ci-health"], "instruction_sha256_by_skill": instruction_hashes}
    if "git" in case:
        setup = case["git"]
        result["git_fixture_sha256"] = {name: {path: sha256(content.encode()) for path, content in files.items()}
                                        for name, files in (("base_files", setup["base_files"]),
                                                            ("head_files", setup.get("head_files", setup["base_files"])),
                                                            ("index_files", setup.get("index_files", setup.get("head_files", setup["base_files"]))))}
        result["base_ref"] = setup.get("base_ref", "main")
    if "expected_skills" in case:
        result["expected_skills"] = case["expected_skills"]
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
