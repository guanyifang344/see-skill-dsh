import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "see" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import install_dsh
import onboard


class RemoveRuleTests(unittest.TestCase):
    def test_removes_rule_keeping_other_content(self) -> None:
        text = "保持简洁。\n\n" + onboard.SEE_AGENTS_RULE
        self.assertEqual(install_dsh.remove_rule_from(text), "保持简洁。\n")

    def test_rule_only_file_becomes_empty_string(self) -> None:
        # Regression: the old implementation returned "\n" when the file
        # contained only the rule, leaving a stray newline behind.
        self.assertEqual(install_dsh.remove_rule_from(onboard.SEE_AGENTS_RULE), "")

    def test_text_without_rule_is_untouched(self) -> None:
        self.assertEqual(install_dsh.remove_rule_from("无规则\n"), "无规则\n")

    def test_upsert_then_remove_round_trip(self) -> None:
        created = onboard.upsert_agents_rule("")
        self.assertTrue(onboard.agents_rule_installed(created))
        self.assertEqual(install_dsh.remove_rule_from(created), "")

    def test_copy_skill_replaces_stale_files(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory(prefix="see-copy-") as tmp:
            src = Path(tmp) / "src"
            dst = Path(tmp) / "dst"
            src.mkdir()
            dst.mkdir()
            (src / "SKILL.md").write_text("new", encoding="utf-8")
            (src / "scripts").mkdir()
            (src / "scripts" / "see.sh").write_text("new", encoding="utf-8")
            (dst / "SKILL.md").write_text("old", encoding="utf-8")
            (dst / "stale.py").write_text("old", encoding="utf-8")
            install_dsh.copy_skill(src, dst)
            self.assertEqual((dst / "SKILL.md").read_text(encoding="utf-8"), "new")
            self.assertFalse((dst / "stale.py").exists())

    def test_project_root_falls_back_to_start_without_git(self) -> None:
        with unittest.mock.patch("pathlib.Path.exists", return_value=False):
            self.assertEqual(install_dsh.project_root(Path("/tmp/x")), Path("/tmp/x"))


if __name__ == "__main__":
    unittest.main()
