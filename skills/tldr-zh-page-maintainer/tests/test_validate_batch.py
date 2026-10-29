from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_batch.py"
SPEC = importlib.util.spec_from_file_location("validate_batch", SCRIPT)
assert SPEC and SPEC.loader
validate_batch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_batch
SPEC.loader.exec_module(validate_batch)


class ValidateBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary_directory.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Skill Test")
        self.git("config", "user.email", "skill-test@example.com")

        self.write_page("pages/common/demo.md", "Run a demo.")
        self.write_page("pages/common/existing.md", "Run an existing demo.")
        self.write_page("pages.zh/common/existing.md", "运行现有演示。")
        self.git("add", "--", "pages", "pages.zh")
        self.git("commit", "-m", "fixture")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def write_page(self, relative: str, description: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        command = path.stem
        path.write_text(
            f"# {command}\n\n> {description}\n\n- Show a file:\n\n"
            f"`{command} {{{{path/to/file}}}}`\n",
            encoding="utf-8",
        )

    def failures(self, report: dict[str, object]) -> set[str]:
        checks = report["checks"]
        assert isinstance(checks, list)
        return {check["code"] for check in checks if not check["ok"]}

    def test_resolve_reports_existing_target_without_rejecting_it(self) -> None:
        report = validate_batch.resolve_batch(self.repo, "HEAD", ["existing"])

        self.assertTrue(report["ok"])
        command = report["commands"][0]
        self.assertEqual(command["status"], "resolved")
        self.assertTrue(command["candidates"][0]["target_exists"])

    def test_create_accepts_an_untracked_target(self) -> None:
        self.write_page("pages.zh/common/demo.md", "运行演示。")
        pair = validate_batch.Pair(
            "create", "pages/common/demo.md", "pages.zh/common/demo.md"
        )

        report = validate_batch.validation_report(self.repo, [pair], True)

        self.assertTrue(report["ok"], self.failures(report))

    def test_sync_accepts_a_modified_tracked_target(self) -> None:
        self.write_page("pages.zh/common/existing.md", "运行已有演示。")
        pair = validate_batch.Pair(
            "sync", "pages/common/existing.md", "pages.zh/common/existing.md"
        )

        report = validate_batch.validation_report(self.repo, [pair], True)

        self.assertTrue(report["ok"], self.failures(report))

    def test_revise_accepts_a_staged_tracked_target(self) -> None:
        self.write_page("pages.zh/common/existing.md", "运行已有演示。")
        self.git("add", "--", "pages.zh/common/existing.md")
        pair = validate_batch.Pair(
            "revise", "pages/common/existing.md", "pages.zh/common/existing.md"
        )

        report = validate_batch.validation_report(self.repo, [pair], True)

        self.assertTrue(report["ok"], self.failures(report))

    def test_operation_must_match_target_state(self) -> None:
        create_existing = validate_batch.Pair(
            "create", "pages/common/existing.md", "pages.zh/common/existing.md"
        )
        self.write_page("pages.zh/common/demo.md", "运行演示。")
        sync_new = validate_batch.Pair(
            "sync", "pages/common/demo.md", "pages.zh/common/demo.md"
        )

        create_report = validate_batch.validation_report(
            self.repo, [create_existing], False
        )
        sync_report = validate_batch.validation_report(self.repo, [sync_new], False)

        self.assertIn("operation_target_state", self.failures(create_report))
        self.assertIn("operation_target_state", self.failures(sync_report))

    def test_pair_syntax_requires_a_known_operation(self) -> None:
        with self.assertRaises(validate_batch.ValidationError):
            validate_batch.parse_pair("pages/common/demo.md=pages.zh/common/demo.md")
        with self.assertRaises(validate_batch.ValidationError):
            validate_batch.parse_pair(
                "update:pages/common/demo.md=pages.zh/common/demo.md"
            )


if __name__ == "__main__":
    unittest.main()
