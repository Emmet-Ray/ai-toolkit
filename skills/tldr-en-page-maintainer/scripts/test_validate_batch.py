from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate_batch.py")
SPEC = importlib.util.spec_from_file_location("validate_batch", MODULE_PATH)
assert SPEC and SPEC.loader
validate_batch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_batch
SPEC.loader.exec_module(validate_batch)


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class ValidateBatchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "pages/common").mkdir(parents=True)
        (self.repo / "pages/linux").mkdir(parents=True)
        (self.repo / "pages/common/existing.md").write_text(
            "# existing\n\n> Existing command.\n\n- Run it:\n\n`existing`\n",
            encoding="utf-8",
        )
        (self.repo / "pages/linux/sentinel.md").write_text(
            "# sentinel\n\n> Existing command.\n\n- Run it:\n\n`sentinel`\n",
            encoding="utf-8",
        )
        git(self.repo, "add", "pages")
        git(self.repo, "commit", "-qm", "seed")
        self.ref = "HEAD"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_inspect_normalizes_subcommands_and_finds_existing_pages(self) -> None:
        report = validate_batch.inspect_batch(
            self.repo, self.ref, ["existing", "new subcommand"]
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["commands"][0]["status"], "existing")
        self.assertEqual(
            report["commands"][0]["existing_pages"],
            ["pages/common/existing.md"],
        )
        self.assertEqual(report["commands"][1]["normalized"], "new-subcommand")
        self.assertEqual(report["commands"][1]["status"], "absent")

    def test_validate_accepts_a_well_formed_new_page_and_exact_scope(self) -> None:
        page = "pages/common/tool-subcommand.md"
        (self.repo / page).write_text(
            "# tool subcommand\n\n"
            "> Perform a useful task.\n"
            "> More information: <https://example.com/tool>.\n\n"
            "- Run the task:\n\n"
            "`tool subcommand {{value}}`\n",
            encoding="utf-8",
        )
        spec = validate_batch.PageSpec("create", page)
        report = validate_batch.validation_report(
            self.repo, self.ref, [spec], check_scope=True
        )
        self.assertTrue(report["ok"], report)

    def test_validate_rejects_operation_state_mismatch_and_bad_title(self) -> None:
        new_page = "pages/common/wrong-name.md"
        (self.repo / new_page).write_text(
            "# another name\n\n> Description.\n\n- Run it:\n\n`another-name`\n",
            encoding="utf-8",
        )
        report = validate_batch.validation_report(
            self.repo,
            self.ref,
            [
                validate_batch.PageSpec("create", "pages/common/existing.md"),
                validate_batch.PageSpec("create", new_page),
            ],
            check_scope=False,
        )
        failed_codes = {item["code"] for item in report["checks"] if not item["ok"]}
        self.assertIn("operation_target_state", failed_codes)
        self.assertIn("title_filename", failed_codes)

    def test_validate_accepts_a_disambiguation_suffix(self) -> None:
        page = "pages/common/tool.1.md"
        (self.repo / page).write_text(
            "# tool\n\n> Description.\n\n- Run it:\n\n`tool`\n",
            encoding="utf-8",
        )
        spec = validate_batch.PageSpec("create", page)
        report = validate_batch.validation_report(
            self.repo, self.ref, [spec], check_scope=True
        )
        self.assertTrue(report["ok"], report)

    def test_validate_accepts_an_updated_tracked_page(self) -> None:
        page = "pages/common/existing.md"
        (self.repo / page).write_text(
            "# existing\n\n> Existing command with current behavior.\n\n"
            "- Run it:\n\n`existing`\n",
            encoding="utf-8",
        )
        spec = validate_batch.PageSpec("update", page)

        report = validate_batch.validation_report(
            self.repo, self.ref, [spec], check_scope=True
        )

        self.assertTrue(report["ok"], report)

    def test_validate_accepts_a_staged_revision(self) -> None:
        page = "pages/common/existing.md"
        (self.repo / page).write_text(
            "# existing\n\n> An existing command.\n\n- Run it:\n\n`existing`\n",
            encoding="utf-8",
        )
        git(self.repo, "add", "--", page)
        spec = validate_batch.PageSpec("revise", page)

        report = validate_batch.validation_report(
            self.repo, self.ref, [spec], check_scope=True
        )

        self.assertTrue(report["ok"], report)

    def test_update_rejects_an_untracked_page(self) -> None:
        page = "pages/common/new.md"
        (self.repo / page).write_text(
            "# new\n\n> New command.\n\n- Run it:\n\n`new`\n",
            encoding="utf-8",
        )
        spec = validate_batch.PageSpec("update", page)

        report = validate_batch.validation_report(
            self.repo, self.ref, [spec], check_scope=False
        )

        failed_codes = {item["code"] for item in report["checks"] if not item["ok"]}
        self.assertIn("operation_target_state", failed_codes)

    def test_page_spec_requires_a_known_operation(self) -> None:
        with self.assertRaises(validate_batch.ValidationError):
            validate_batch.parse_page_spec("pages/common/existing.md")
        with self.assertRaises(validate_batch.ValidationError):
            validate_batch.parse_page_spec("edit:pages/common/existing.md")

    def test_validate_rejects_unknown_platform_and_extra_worktree_change(self) -> None:
        page = "pages/unknown/new.md"
        (self.repo / "pages/unknown").mkdir()
        (self.repo / page).write_text(
            "# new\n\n> Description.\n\n- Run it:\n\n`new`\n",
            encoding="utf-8",
        )
        (self.repo / "extra.txt").write_text("unexpected\n", encoding="utf-8")
        spec = validate_batch.PageSpec("create", page)
        report = validate_batch.validation_report(
            self.repo, self.ref, [spec], check_scope=True
        )
        failed_codes = {item["code"] for item in report["checks"] if not item["ok"]}
        self.assertIn("platform_directory", failed_codes)
        self.assertIn("worktree_scope", failed_codes)


if __name__ == "__main__":
    unittest.main()
