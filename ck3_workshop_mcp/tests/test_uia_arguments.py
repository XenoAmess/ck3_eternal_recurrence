from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ck3_workshop_mcp import launcher_uia


ROOT = Path(__file__).resolve().parents[1]


class UiaKeyContractTests(unittest.TestCase):
    def test_power_shell_bridge_accepts_only_finite_navigation_tokens(self) -> None:
        script = (
            ROOT / "src" / "ck3_workshop_mcp" / "uia_bridge.ps1"
        ).read_text(encoding="utf-8-sig")
        match = re.search(r"\$Keys -notmatch '([^']+)'", script)
        self.assertIsNotNone(match)
        contract = re.compile(match.group(1))

        for token in ("ENTER", "HOME", "END", "UP", "DOWN", "TAB", "ESC"):
            self.assertIsNotNone(contract.fullmatch("{" + token + "}"), token)
        self.assertIsNotNone(contract.fullmatch("{DOWN}{END}{ENTER}"))
        for forbidden in ("A", "{A}", "{DELETE}", "{F4}", "%{F4}", "{ENTER}text"):
            self.assertIsNone(contract.fullmatch(forbidden), forbidden)

    def test_keys_passes_exact_hwnd_control_and_sequence_to_bridge(self) -> None:
        expected = {"ok": True, "action": "keys"}
        with patch.object(launcher_uia, "_run_bridge", return_value=expected) as run:
            actual = launcher_uia.keys(48123, "mod-combobox", "{DOWN}{END}{ENTER}")
        self.assertIs(actual, expected)
        run.assert_called_once_with(
            "keys",
            hwnd=48123,
            automation_id="mod-combobox",
            keys="{DOWN}{END}{ENTER}",
        )

    def test_keys_requires_exact_automation_id(self) -> None:
        with self.assertRaises(launcher_uia.UiaBridgeError):
            launcher_uia.keys(48123, "", "{ENTER}")


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class CallToolTextFileTests(unittest.TestCase):
    def test_text_file_overrides_json_text_and_reaches_official_client_call(self) -> None:
        from ck3_workshop_mcp import call_tool

        exact_text = "文" * 1024
        captured: dict[str, object] = {}

        class FakeClient:
            def __init__(self, server: object) -> None:
                captured["server"] = server

            async def __aenter__(self) -> "FakeClient":
                return self

            async def __aexit__(self, *args: object) -> None:
                return None

            async def call_tool(self, tool: str, arguments: dict[str, object]):
                captured["tool"] = tool
                captured["arguments"] = arguments
                return SimpleNamespace(
                    is_error=False,
                    structured_content={"ok": True},
                    content=[],
                )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            arguments_file = root / "arguments.json"
            arguments_file.write_text(
                json.dumps({"hwnd": 48123, "automation_id": "", "text": "stale"}),
                encoding="utf-8",
            )
            text_file = root / "description.bbcode"
            text_file.write_text(exact_text, encoding="utf-8")
            args = argparse.Namespace(
                provider="pdx-uia",
                cdp_url=None,
                state_dir=root / "state",
                tool="workshop_ui_set_text",
                arguments_file=arguments_file,
                text_file=text_file,
            )
            with (
                patch.object(call_tool, "create_service", return_value=object()),
                patch.object(call_tool, "create_server", return_value=object()),
                patch("mcp.Client", FakeClient),
            ):
                payload, status = asyncio.run(call_tool._call(args))

        self.assertEqual(status, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(captured["tool"], "workshop_ui_set_text")
        self.assertEqual(captured["arguments"]["text"], exact_text)
        self.assertEqual(len(captured["arguments"]["text"]), 1024)


if __name__ == "__main__":
    unittest.main()
