from __future__ import annotations

import unittest
from pathlib import Path

import validate_python_only


class PythonOnlyValidationTests(unittest.TestCase):
    def test_detects_legacy_variable_in_text_command_block(self) -> None:
        source = "```text\n$Runner script.py\n```\n"
        self.assertTrue(validate_python_only.fenced_block_findings("fixture.md", source))

    def test_preserves_other_shell_languages(self) -> None:
        source = "```bash\nprintf '%s\\n' \"$HOME\"\n```\n"
        self.assertEqual(validate_python_only.fenced_block_findings("fixture.md", source), [])

    def test_detects_unclosed_fence(self) -> None:
        self.assertTrue(validate_python_only.fenced_block_findings("fixture.md", "```text\npython tool.py\n"))

    def test_detects_constructed_legacy_command_name(self) -> None:
        source = f"```text\n{validate_python_only.LEGACY_COMMANDS[0]} game.exe\n```\n"
        self.assertTrue(validate_python_only.fenced_block_findings("fixture.md", source))

    def test_windows_ci_uses_explicit_cmd_shell(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1] / ".github/workflows/static-ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("defaults:\n      run:\n        shell: cmd", workflow.replace("\r\n", "\n"))
        self.assertNotIn("shell: " + validate_python_only.SHORT_ENGINE_NAME, workflow.casefold())


if __name__ == "__main__":
    unittest.main()
