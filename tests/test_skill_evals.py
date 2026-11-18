"""Offline tests of evaluation evidence handling; these do not run or grade a model."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

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
        case = evaluations.load_cases()[0]
        workspace, staged, before = evaluations.prepare_case(case, self.directory / "case")
        self.assertEqual((staged / "SKILL.md").read_bytes(), (evaluations.SKILL / "SKILL.md").read_bytes())
        self.assertIn("evidence.json", before)
        all_text = "\n".join(path.read_text() for path in workspace.rglob("*") if path.is_file() and ".git" not in path.parts)
        for check in case["review_checks"]:
            self.assertNotIn(check, all_text)
        self.assertNotIn("review_checks", all_text)
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


if __name__ == "__main__":
    unittest.main()
