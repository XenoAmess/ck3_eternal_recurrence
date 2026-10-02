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

    def test_build_metadata_inherited_directory_is_not_an_engine_call(self) -> None:
        engine = validate_python_only.ENGINE_NAME
        directory = "C:/Windows/System32/Windows" + engine + "/v1.0/"
        for name in validate_python_only.ENVIRONMENT_METADATA_NAMES:
            with self.subTest(name=name):
                cleaned = validate_python_only.reference_text(name, directory + "lld-link.exe")
                self.assertNotIn(engine, cleaned.casefold())

    def test_metadata_engine_executable_still_rejected(self) -> None:
        engine = validate_python_only.ENGINE_NAME
        command = "C:/Windows/System32/Windows" + engine + "/v1.0/" + engine + ".exe -Command"
        cleaned = validate_python_only.reference_text("CMakeConfigureLog.yaml", command)
        self.assertIn(engine, cleaned.casefold())

    def test_environment_directory_exception_does_not_apply_to_code(self) -> None:
        engine = validate_python_only.ENGINE_NAME
        directory = "C:/Windows/System32/Windows" + engine + "/v1.0/"
        self.assertEqual(validate_python_only.reference_text("runner.py", directory), directory)

    def test_metadata_other_forbidden_references_remain_visible(self) -> None:
        source = validate_python_only.SHORT_ENGINE_NAME + " " + validate_python_only.FORBIDDEN_SUFFIXES[0]
        self.assertEqual(validate_python_only.reference_text("vs-environment-selected.json", source), source)


if __name__ == "__main__":
    unittest.main()
