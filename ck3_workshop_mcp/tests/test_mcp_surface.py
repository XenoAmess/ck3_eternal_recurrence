from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ck3_workshop_mcp.engine import WorkshopService
from ck3_workshop_mcp.providers import PdxLauncherReadOnlyProvider
from ck3_workshop_mcp.server import create_server
from ck3_workshop_mcp.wal import OperationStore


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class McpSurfaceTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_subscribe_forwards_target_and_preserves_partial(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as temporary:
            service = WorkshopService(OperationStore(Path(temporary)), PdxLauncherReadOnlyProvider())
            server = create_server(service, enable_native=True)
            partial = {"ok": False, "status": "partial", "item_id": "123456789", "app_id": 1158310,
                       "callback": {"callback_id": 1313, "item_id": "123456789", "result": 1}, "subscribed": False}
            with patch("ck3_workshop_mcp.steam_subscribe.subscribe", return_value=partial) as run:
                async with Client(server) as client:
                    tools = {t.name: t for t in (await client.list_tools()).tools}
                    self.assertFalse(tools["workshop_native_subscribe"].annotations.read_only_hint)
                    result = await client.call_tool("workshop_native_subscribe", {
                        "dll_path": "unused.dll", "item_id": "123456789", "app_id": 1158310,
                        "timeout_seconds": 180,
                    })
                    self.assertFalse(result.is_error)
                    self.assertEqual(partial, result.structured_content)
                    run.assert_called_once_with("unused.dll", "123456789", 1158310, 180)

    async def test_native_download_forwards_exact_target_and_preserves_unknown(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as temporary:
            service = WorkshopService(OperationStore(Path(temporary)), PdxLauncherReadOnlyProvider())
            server = create_server(service, enable_native=True)
            partial = {"ok": False, "status": "unknown", "item_id": "3182367229", "app_id": 1158310}
            with patch("ck3_workshop_mcp.steam_download.download", return_value=partial) as run:
                async with Client(server) as client:
                    tools = {t.name: t for t in (await client.list_tools()).tools}
                    self.assertFalse(tools["workshop_native_download"].annotations.read_only_hint)
                    result = await client.call_tool("workshop_native_download", {
                        "dll_path": "unused.dll", "item_id": "3182367229", "app_id": 1158310,
                        "timeout_seconds": 300, "expected_cache_path": "C:/fixture/3182367229",
                    })
                    self.assertFalse(result.is_error)
                    self.assertEqual(partial, result.structured_content)
                    run.assert_called_once_with("unused.dll", "3182367229", 1158310, 300, "C:/fixture/3182367229")

    async def test_native_preview_read_tool_forwards_exact_target_without_loading_dll(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as temporary:
            service = WorkshopService(OperationStore(Path(temporary)), PdxLauncherReadOnlyProvider())
            server = create_server(service, enable_native=True)
            frozen = {"schema": "ck3_workshop_mcp.steam_native.previews.v1", "ok": True,
                      "item_id": "3182367229", "app_id": 1158310, "previews": []}
            with patch("ck3_workshop_mcp.steam_native.previews", return_value=frozen) as read:
                async with Client(server) as client:
                    listed = await client.list_tools()
                    tools = {tool.name: tool for tool in listed.tools}
                    self.assertTrue(tools["workshop_native_previews"].annotations.read_only_hint)
                    self.assertFalse(tools["workshop_native_publish"].annotations.read_only_hint)
                    result = await client.call_tool("workshop_native_previews", {
                        "dll_path": "unused.dll", "item_id": "3182367229", "app_id": 1158310,
                    })
                    self.assertFalse(result.is_error)
                    self.assertEqual(frozen, result.structured_content)
                    read.assert_called_once_with("unused.dll", "3182367229", 1158310)

    async def test_official_client_lists_tools_and_resources(self) -> None:
        from mcp import Client

        with tempfile.TemporaryDirectory() as temporary:
            service = WorkshopService(
                OperationStore(Path(temporary)), PdxLauncherReadOnlyProvider()
            )
            server = create_server(service)
            async with Client(server) as client:
                listed = await client.list_tools()
                tools = {tool.name: tool for tool in listed.tools}
                self.assertEqual(
                    set(tools),
                    {
                        "workshop_capabilities",
                        "workshop_plan_create",
                        "workshop_begin_online_window",
                        "workshop_preflight",
                        "workshop_issue_submit_token",
                        "workshop_submit",
                        "workshop_operation_get",
                        "workshop_operation_events",
                        "workshop_restore_offline",
                        "workshop_recover_offline_obligations",
                    },
                )
                self.assertTrue(tools["workshop_capabilities"].annotations.read_only_hint)
                self.assertFalse(tools["workshop_submit"].annotations.read_only_hint)
                self.assertTrue(tools["workshop_submit"].annotations.destructive_hint)

                resources = await client.list_resources()
                self.assertIn(
                    "workshop://capabilities",
                    {str(resource.uri) for resource in resources.resources},
                )
                templates = await client.list_resource_templates()
                uris = {template.uri_template for template in templates.resource_templates}
                self.assertIn("workshop://operations/{operation_id}", uris)
                self.assertIn("workshop://operations/{operation_id}/events", uris)


if __name__ == "__main__":
    unittest.main()
