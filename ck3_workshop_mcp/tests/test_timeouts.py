"""Offline defaults and real forwarding; no Steam DLL or network operations."""
from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import inspect
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from ck3_workshop_mcp import steam_download, steam_native
from ck3_workshop_mcp.timeouts import DEFAULT_WORKSHOP_TIMEOUT_SECONDS


class WorkshopTimeoutTests(unittest.TestCase):
    def test_callback_wait_can_finish_after_former_180_second_default(self):
        client = SimpleNamespace(utils=1, _run_callbacks=lambda: None,
            _is_call_completed=lambda *args: next(completion),
            _get_call_result=lambda *args: True)
        completion = iter([False, True])
        with patch.object(steam_native.time, "monotonic", side_effect=[0, 0, 600]), \
             patch.object(steam_native.time, "sleep") as sleep:
            result = steam_native._NativeClient._wait_for_result(
                client, 1, steam_native.SubmitItemUpdateResult, 3404)
        self.assertIsInstance(result, steam_native.SubmitItemUpdateResult)
        sleep.assert_called_once_with(0.05)

    def test_callback_default_still_expires_at_1800_without_redispatch(self):
        client = SimpleNamespace(utils=1, _run_callbacks=lambda: None,
            _is_call_completed=lambda *args: False)
        with patch.object(steam_native.time, "monotonic", side_effect=[0, 0, 1800]), \
             patch.object(steam_native.time, "sleep"):
            with self.assertRaises(steam_native.SteamNativeError) as caught:
                steam_native._NativeClient._wait_for_result(
                    client, 1, steam_native.SubmitItemUpdateResult, 3404)
        self.assertEqual(caught.exception.code, "API_CALL_RESULT_UNKNOWN")
        self.assertEqual(caught.exception.details["timeout_seconds"], 1800)

    def test_download_api_and_both_clis_share_default(self):
        self.assertEqual(DEFAULT_WORKSHOP_TIMEOUT_SECONDS, 1800)
        self.assertEqual(inspect.signature(steam_download.download).parameters[
            "timeout_seconds"].default, DEFAULT_WORKSHOP_TIMEOUT_SECONDS)
        args = steam_native._parser().parse_args([
            "download", "--dll", "unused.dll", "--item-id", "3182367229"])
        self.assertEqual(args.timeout_seconds, DEFAULT_WORKSHOP_TIMEOUT_SECONDS)
        with patch.object(steam_download, "_worker", return_value={"ok": True}) as worker, \
             redirect_stdout(StringIO()):
            self.assertEqual(steam_download.main([
                "--worker", "--dll", "unused.dll", "--item-id", "3182367229"]), 0)
        self.assertEqual(worker.call_args.args[0]["timeout_seconds"],
                         DEFAULT_WORKSHOP_TIMEOUT_SECONDS)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class WorkshopMcpTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_download_default_and_publish_three_field_signature(self):
        from mcp import Client
        from ck3_workshop_mcp.server import create_server, create_service
        with tempfile.TemporaryDirectory() as temporary:
            server = create_server(create_service(Path(temporary), "steam-native"),
                                   enable_native=True)
            with patch.object(steam_download, "download", return_value={"ok": True}) as download:
                async with Client(server) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertEqual(tools["workshop_native_download"].input_schema[
                        "properties"]["timeout_seconds"]["default"], DEFAULT_WORKSHOP_TIMEOUT_SECONDS)
                    self.assertEqual(set(tools["workshop_native_publish"].input_schema[
                        "properties"]), {"dll_path", "plan_file", "receipt_file"})
                    result = await client.call_tool("workshop_native_download", {
                        "dll_path": "unused.dll", "item_id": "3182367229"})
                self.assertFalse(result.is_error)
                download.assert_called_once_with("unused.dll", "3182367229", 1158310,
                                                  DEFAULT_WORKSHOP_TIMEOUT_SECONDS, None)


if __name__ == "__main__":
    unittest.main()
