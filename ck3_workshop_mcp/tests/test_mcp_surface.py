from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from ck3_workshop_mcp.engine import WorkshopService
from ck3_workshop_mcp.providers import PdxLauncherReadOnlyProvider
from ck3_workshop_mcp.server import create_server
from ck3_workshop_mcp.wal import OperationStore


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class McpSurfaceTests(unittest.IsolatedAsyncioTestCase):
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
