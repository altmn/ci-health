"""Offline tests of evaluation evidence handling; these do not run or grade a model."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("evaluate_skill", ROOT / "scripts/evaluate_skill.py")
evaluations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluations)


class SkillEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.staged = self.directory / "workspace/.agents/skills/ci-health"
        self.skill_text = "---\nname: ci-health\ndescription: Synthetic description\n---\n# CI Health\n"

    def trace(self, *, command=None, output=None, exit_code=0, complete=True):
        events = [{"type": "item.completed", "item": {"id": "tool-1", "type": "command_execution",
                   "command": command or f"cat {self.staged}/SKILL.md", "exit_code": exit_code,
                   "aggregated_output": self.skill_text if output is None else output}}]
        if complete:
            events.append({"type": "turn.completed", "usage": {}})
        return "\n".join(json.dumps(event) for event in events)

    def inspect(self, trace, returncode=0, timed_out=False):
        return evaluations.inspect_trace(trace, self.staged, self.skill_text, returncode, timed_out)

    def test_staged_successful_read_is_observed(self):
        result = self.inspect(self.trace())
        self.assertTrue(result["complete"])
        self.assertEqual(result["observation"], "staged-skill-read")
        self.assertEqual(result["read_item_ids"], ["tool-1"])

    def test_final_claim_failed_read_and_path_mention_do_not_prove_activation(self):
        inputs = [
            self.trace(output="File not found", exit_code=1),
            self.trace(output="The skill is available."),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "I used $ci-health"}}) + "\n" + json.dumps({"type": "turn.completed"}),
        ]
        for trace in inputs:
            with self.subTest(trace=trace):
                result = self.inspect(trace)
                self.assertEqual(result["observation"], "no-skill-read-observed")
                assessment = evaluations.assess({"activation": True, "allowed_changes": [], "review_checks": ["Review"]}, result, {}, {})
                self.assertEqual(assessment["activation_check"], "unknown")

    def test_other_installation_read_remains_unknown(self):
        for command in ("cat plugin-cache/ci-health/SKILL.md", "cat ~/.agents/skills/ci-health/SKILL.md",
                        "cat /other/workspace/.agents/skills/ci-health/SKILL.md",
                        "cd /other/workspace && cat .agents/skills/ci-health/SKILL.md",
                        "cat ignored;cd /other/workspace;cat .agents/skills/ci-health/SKILL.md",
                        "env -C /other/workspace cat .agents/skills/ci-health/SKILL.md",
                        "cat $SKILL_DIR/SKILL.md"):
            with self.subTest(command=command):
                result = self.inspect(self.trace(command=command))
                self.assertEqual(result["observation"], "other-or-unresolved-skill-read")
                assessment = evaluations.assess({"activation": True, "allowed_changes": [], "review_checks": ["Review"]}, result, {}, {})
                self.assertEqual(assessment["activation_check"], "unknown")

    def test_direct_relative_read_in_shell_wrapper_binds_staged_copy(self):
        for command in ("/bin/zsh -lc 'cat .agents/skills/ci-health/SKILL.md'",
                        "cat ./.agents/skills/ci-health/SKILL.md", f"cat '{self.staged}/SKILL.md'"):
            with self.subTest(command=command):
                self.assertEqual(self.inspect(self.trace(command=command))["observation"], "staged-skill-read")

    def test_absolute_path_mentions_and_compound_host_reads_do_not_bind(self):
        staged = self.staged / "SKILL.md"
        host = "/host-cache/ci-health/SKILL.md"
        for command in (f"echo {staged}; cat {host}", f"cat {host}; echo {staged}",
                        f"cat {host}\necho {staged}", f"echo {staged} && cat {host}",
                        f"cat {host} # comment\necho {staged}",
                        f"cat {host} # comment\r\necho {staged}",
                        f"/bin/zsh -lc 'cat {host} # comment\necho {staged}'",
                        f"/bin/zsh -lc 'echo {staged}; cat {host}'",
                        f"cd /other && cat {staged}", f"cat {host} > {staged}",
                        f"cat {host} | echo {staged}"):
            with self.subTest(command=command):
                result = self.inspect(self.trace(command=command))
                self.assertEqual(result["observation"], "other-or-unresolved-skill-read")
                self.assertEqual(evaluations.activation_assessment(result, True), "unknown")

    def test_preflight_reads_bind_only_the_matching_staged_skill(self):
        staged = self.staged.with_name("ci-health-preflight")
        body = "---\nname: ci-health-preflight\ndescription: Review synthetic changes\n---\n"
        for command, expected in (("cat .agents/skills/ci-health-preflight/SKILL.md", "staged-skill-read"),
                                  (f"cat {staged}/SKILL.md", "staged-skill-read"),
                                  ("cat .agents/skills/ci-health/SKILL.md", "other-or-unresolved-skill-read"),
                                  ("cat /another/.agents/skills/ci-health-preflight/SKILL.md", "other-or-unresolved-skill-read")):
            with self.subTest(command=command):
                observed = evaluations.inspect_trace(self.trace(command=command, output=body), staged, body, 0)
                self.assertEqual(observed["observation"], expected)

    def test_expected_skill_set_separates_routing_from_legacy_activation(self):
        case = {"activation": True, "expected_skills": ["ci-health-preflight"], "allowed_changes": [], "review_checks": ["Review"]}
        absent = self.inspect(self.trace(output="No read"))
        present = self.inspect(self.trace())
        result = evaluations.assess(case, absent, {}, {}, skill_traces={"ci-health": absent, "ci-health-preflight": present})
        self.assertEqual(result["activation_check"], "pass")
        self.assertEqual(result["activation_by_skill"], {"ci-health-preflight": "pass"})
        result = evaluations.assess(case, present, {}, {}, skill_traces={"ci-health": present, "ci-health-preflight": present})
        self.assertEqual(result["activation_check"], "pass")
        result = evaluations.assess(case, absent, {}, {}, skill_traces={"ci-health": absent, "ci-health-preflight": absent})
        self.assertEqual(result["activation_check"], "unknown")
        case.update(activation=False, expected_skills=[])
        result = evaluations.assess(case, present, {}, {}, skill_traces={"ci-health": present, "ci-health-preflight": absent})
        self.assertEqual(result["activation_check"], "fail")

    def test_incomplete_or_corrupt_trace_cannot_pass_negative_activation(self):
        case = {"activation": False, "allowed_changes": [], "review_checks": ["Review"]}
        for trace, code, timed_out in [(self.trace(complete=False), 0, False),
                                       (self.trace() + "\nnot-json", 0, False),
                                       (self.trace() + "\n[]", 0, False),
                                       (self.trace(), 1, False), (self.trace(), 0, True)]:
            with self.subTest(trace=trace, code=code, timed_out=timed_out):
                assessment = evaluations.assess(case, self.inspect(trace, code, timed_out), {}, {})
                self.assertEqual(assessment["activation_check"], "unknown")

    def test_negative_case_requires_complete_trace_without_skill_read(self):
        case = {"activation": False, "allowed_changes": [], "review_checks": ["Review"]}
        self.assertEqual(evaluations.assess(case, self.inspect(self.trace(output="Hello")), {}, {})["activation_check"], "pass")
        self.assertEqual(evaluations.assess(case, self.inspect(self.trace()), {}, {})["activation_check"], "fail")

    def test_unexpected_modifications_fail_scope_even_if_execution_failed(self):
        case = {"activation": True, "allowed_changes": ["workflow.yml"], "review_checks": ["Review"]}
        result = evaluations.assess(case, self.inspect(self.trace(), 1),
                                    {"workflow.yml": "old", "required-test.py": "old"},
                                    {"workflow.yml": "new", "extra.txt": "new"})
        self.assertEqual(result["scope_check"], "fail")
        self.assertEqual(result["unexpected_changed_files"], ["extra.txt", "required-test.py"])
        self.assertEqual(result["behavior_review"], "pending")

    def test_preparation_keeps_expectations_outside_agent_workspace(self):
        for case in evaluations.load_cases():
            with self.subTest(case=case["id"]):
                workspace, staged, before = evaluations.prepare_case(case, self.directory / case["id"])
                for name, source in evaluations.SKILLS.items():
                    copy = staged.with_name(name)
                    self.assertEqual((copy / "SKILL.md").read_bytes(), (source / "SKILL.md").read_bytes())
                    for resource in source.rglob("*"):
                        if resource.is_file() and "__pycache__" not in resource.parts and resource.suffix != ".pyc":
                            relative = resource.relative_to(source)
                            self.assertEqual((copy / relative).read_bytes(), resource.read_bytes())
                for name, content in case["files"].items():
                    self.assertEqual((workspace / name).read_text(), content)
                    self.assertEqual(before[name], evaluations.sha256(content.encode()))
                all_text = "\n".join(path.read_text() for path in workspace.rglob("*") if path.is_file() and ".git" not in path.parts)
                for check in case["review_checks"]:
                    self.assertNotIn(check, all_text)
                self.assertNotIn("review_checks", all_text)
                self.assertNotIn("expected_skills", all_text)
                self.assertNotIn(case["prompt"], all_text)

    def test_preparation_creates_task_branch_and_binds_environment_constraints(self):
        case = evaluations.load_cases()[0]
        workspace, staged, before = evaluations.prepare_case(case, self.directory / "case")
        branch = subprocess.run(["git", "-C", str(workspace), "symbolic-ref", "--short", "HEAD"],
                                check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(branch, "codex/skill-eval")
        self.assertEqual(before["AGENTS.md"], evaluations.sha256(evaluations.CONSTRAINTS.encode()))
        self.assertEqual((workspace / "AGENTS.md").read_text(), evaluations.CONSTRAINTS)

    def test_fixture_path_traversal_and_reserved_paths_are_rejected(self):
        original = json.loads(evaluations.CASES.read_text())
        for name in ("../escape", "/absolute", ".git", ".agents/skills/injected/SKILL.md", "AGENTS.md", "."):
            with self.subTest(name=name):
                original["cases"][0]["files"] = {name: "synthetic"}
                path = self.directory / "cases.json"
                path.write_text(json.dumps(original))
                with self.assertRaises(evaluations.EvaluationError):
                    evaluations.load_cases(path)

    def test_output_cannot_overwrite_or_enter_git(self):
        existing = self.directory / "existing"
        existing.mkdir()
        with self.assertRaises(evaluations.EvaluationError):
            evaluations.external_output(str(existing))
        with self.assertRaises(evaluations.EvaluationError):
            evaluations.external_output(str(ROOT / "evidence/new-eval"))

    def git_case(self):
        return {"id": "git-case", "category": "review", "activation": True,
                "prompt": "Review candidate changes relative to main without editing.",
                "allowed_changes": [], "review_checks": ["Inspect changed code"],
                "git": {"base_files": {"existing.txt": "base\n"}}, "files": {"existing.txt": "base\n"}}

    def test_git_preparation_preserves_all_candidate_layers_and_deletions(self):
        case = self.git_case()
        base = {"common.txt": "base\n", "old-name.txt": "retained content\n", "deleted.txt": "delete me\n"}
        head = {"common.txt": "base\n", "new-name.txt": "retained content\n", "committed.txt": "new commit\n"}
        index = {**head, "common.txt": "staged\n", "staged.txt": "new index\n"}
        final = {**index, "common.txt": "unstaged\n", "untracked.txt": "new workspace\n"}
        case.update(git={"base_files": base, "head_files": head, "index_files": index}, files=final)
        workspace, _, _ = evaluations.prepare_case(case, self.directory / "mixed")
        self.assertEqual(evaluations.git(workspace, "show", "main:common.txt").stdout, "base\n")
        self.assertEqual(evaluations.git(workspace, "show", "HEAD:common.txt").stdout, "base\n")
        self.assertEqual(evaluations.git(workspace, "show", ":common.txt").stdout, "staged\n")
        self.assertEqual((workspace / "common.txt").read_text(), "unstaged\n")
        self.assertEqual(evaluations.git(workspace, "ls-files", "--others", "--exclude-standard").stdout.splitlines(), ["untracked.txt"])
        self.assertEqual(set(evaluations.git(workspace, "diff", "--cached", "--name-only").stdout.splitlines()), {"common.txt", "staged.txt"})
        self.assertEqual(evaluations.git(workspace, "diff", "--name-only").stdout.splitlines(), ["common.txt"])
        changes = evaluations.git(workspace, "diff", "--name-status", "--find-renames", "main", "HEAD").stdout
        self.assertIn("D\tdeleted.txt", changes)
        self.assertIn("R100\told-name.txt\tnew-name.txt", changes)
        self.assertNotEqual(evaluations.git(workspace, "rev-parse", "main").stdout, evaluations.git(workspace, "rev-parse", "HEAD").stdout)

    def test_git_fixture_can_change_file_directory_shape_between_snapshots(self):
        case = self.git_case()
        case.update(git={"base_files": {"shape": "base\n"}, "head_files": {"shape/nested": "head\n"},
                         "index_files": {"shape": "index\n"}}, files={"shape/other": "workspace\n"})
        workspace, _, _ = evaluations.prepare_case(case, self.directory / "shape")
        self.assertEqual(evaluations.git(workspace, "show", "main:shape").stdout, "base\n")
        self.assertEqual(evaluations.git(workspace, "show", "HEAD:shape/nested").stdout, "head\n")
        self.assertEqual(evaluations.git(workspace, "show", ":shape").stdout, "index\n")
        self.assertEqual((workspace / "shape/other").read_text(), "workspace\n")

    def test_missing_base_ref_is_not_silently_created(self):
        case = self.git_case()
        case["git"]["base_ref"] = None
        workspace, _, _ = evaluations.prepare_case(case, self.directory / "missing")
        self.assertNotEqual(evaluations.git(workspace, "rev-parse", "--verify", "main", check=False).returncode, 0)
        self.assertIsNotNone(evaluations.git_state(workspace)["head"])

    def test_git_mutations_fail_scope_without_file_byte_changes(self):
        operations = {"stage": ("add", "existing.txt"), "commit": ("commit", "--quiet", "--allow-empty", "-m", "Unauthorized"),
                      "ref": ("branch", "unauthorized"), "detach": ("checkout", "--quiet", "--detach")}
        for name, arguments in operations.items():
            with self.subTest(operation=name):
                case = self.git_case()
                case["files"]["existing.txt"] = "working tree\n"
                workspace, _, before = evaluations.prepare_case(case, self.directory / name)
                git_before = evaluations.git_state(workspace)
                evaluations.git(workspace, *arguments)
                after = evaluations.snapshot(workspace)
                self.assertEqual(before, after)
                result = evaluations.assess(case, self.inspect(self.trace()), before, after,
                                            git_before=git_before, git_after=evaluations.git_state(workspace))
                self.assertEqual(result["scope_check"], "fail")
                self.assertTrue(result["git_changes"])

    def test_git_reads_do_not_invalidate_scope(self):
        case = self.git_case()
        workspace, _, before = evaluations.prepare_case(case, self.directory / "reads")
        initial = evaluations.git_state(workspace)
        evaluations.git(workspace, "status", "--short")
        evaluations.git(workspace, "diff", "main")
        result = evaluations.assess(case, self.inspect(self.trace()), before, evaluations.snapshot(workspace),
                                    git_before=initial, git_after=evaluations.git_state(workspace))
        self.assertEqual(result["scope_check"], "pass")

    def test_index_flags_are_scope_changes_without_file_or_blob_changes(self):
        for flag in ("--assume-unchanged", "--skip-worktree"):
            with self.subTest(flag=flag):
                case = self.git_case()
                workspace, _, before = evaluations.prepare_case(case, self.directory / flag.removeprefix("--"))
                state_before = evaluations.git_state(workspace)
                blobs_before = evaluations.git(workspace, "ls-files", "--stage", "-z").stdout
                evaluations.git(workspace, "update-index", flag, "existing.txt")
                self.assertEqual(blobs_before, evaluations.git(workspace, "ls-files", "--stage", "-z").stdout)
                self.assertEqual(before, evaluations.snapshot(workspace))
                result = evaluations.assess(case, self.inspect(self.trace()), before, before,
                                            git_before=state_before, git_after=evaluations.git_state(workspace))
                self.assertEqual(result["scope_check"], "fail")
                self.assertEqual(result["git_changes"], ["index"])

    def test_fixture_git_is_independent_of_host_signing_ignores_and_identity(self):
        settings = self.directory / "global-config"
        ignores = self.directory / "ignored"
        ignores.write_text("existing.txt\n")
        settings.write_text(f"[user]\n name = Private Host\n email = host@example.invalid\n[commit]\n gpgSign = true\n[core]\n excludesFile = {ignores}\n")
        with patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(settings), "GIT_DIR": str(self.directory / "absent"),
                                     "GIT_AUTHOR_NAME": "Private Override"}):
            workspace, _, _ = evaluations.prepare_case(self.git_case(), self.directory / "host-independent")
            self.assertEqual(evaluations.git(workspace, "show", "HEAD:existing.txt").stdout, "base\n")
            self.assertEqual(evaluations.git(workspace, "log", "-1", "--format=%an <%ae>").stdout.strip(),
                             "Synthetic Evaluator <evaluation@example.invalid>")

    def test_git_setup_and_expected_skills_are_validated(self):
        invalid = [
            {"git": []}, {"git": {"base_files": []}}, {"git": {"base_files": {}, "surprise": {}}},
            *({"git": {"base_files": {}, "base_ref": ref}} for ref in ("-bad", "HEAD", "codex/skill-eval", "bad..ref", "a.lock", "a//b", "a b", "a^b")),
            *({"git": {"base_files": {}, key: {path: "bad"}}} for key in ("base_files", "head_files", "index_files")
              for path in ("../escape", ".git/config", ".GIT/config", ".agents/injected", "AGENTS.md")),
            {"expected_skills": ["unrecognized"]}, {"expected_skills": ["ci-health", "ci-health"]},
            {"expected_skills": []}, {"expected_skills": "ci-health"},
            {"files": {"a": "file", "a/child": "conflict"}}, {"files": {"Case": "one", "case": "two"}},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                case = self.git_case()
                case.update(changes)
                manifest = self.directory / "invalid.json"
                manifest.write_text(json.dumps({"schema": "ci-health.skill-evals/v1", "cases": [case]}))
                with self.assertRaises(evaluations.EvaluationError):
                    evaluations.load_cases(manifest)


if __name__ == "__main__":
    unittest.main()
