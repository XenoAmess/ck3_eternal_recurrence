"""Official MCP SDK to real driver wrappers using frozen native Feast wire."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_feast_wire import FixtureDriver, actual_wire
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002


COST_TOOL = "ck3_query_activity_stage5_feast_full_cost_private_v1"
POST_TOOL = "ck3_query_activity_feast_hosted_post_private_v1"


class NativeWrapperWireDriver(FixtureDriver):
    """Keep transport local while executing the production driver methods."""

    command_timeout_seconds = 1
    query_activity_stage5_feast_full_cost_private_v1 = (
        NativeHeadlessGameplayDriver.query_activity_stage5_feast_full_cost_private_v1
    )
    query_activity_feast_hosted_post_private_v1 = (
        NativeHeadlessGameplayDriver.query_activity_feast_hosted_post_private_v1
    )

    def select_frame(self, payload: dict[str, object]) -> None:
        replacement = FixtureDriver(payload)
        self.payload = replacement.payload
        self.snapshot = replacement.snapshot


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class FeastMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_read_tools_call_real_native_wrappers_with_actual_native_payloads(self):
        from mcp import Client

        fullcost = actual_wire("ck3_12002_feast_fullcost_wire.json")
        completed = actual_wire("ck3_12002_feast_hosted_post_wire.json")[1]
        driver = NativeWrapperWireDriver(fullcost)
        async with Client(create_server(driver)) as client:
            listed = {tool.name: tool for tool in (await client.list_tools()).tools}
            for name in (COST_TOOL, POST_TOOL):
                self.assertIn(name, listed)
                self.assertIs(listed[name].annotations.read_only_hint, True)
            cost = await client.call_tool(COST_TOOL, {"expected_revision": 5})
            self.assertFalse(cost.is_error)
            observed_cost = cost.structured_content
            self.assertEqual(observed_cost["resources"], fullcost["resources"])
            self.assertEqual(observed_cost["resources"]["piety"]["configured_cost_raw"], -100000)
            self.assertIs(observed_cost["final_can_start"], False)
            self.assertEqual(observed_cost["exe_sha256"], CK3_12002.executable_sha256)
            driver.select_frame(completed)
            post = await client.call_tool(POST_TOOL, {"expected_revision": 5})
            self.assertFalse(post.is_error)
            observed_post = post.structured_content
            self.assertEqual(observed_post["hosted_activities"], completed["hosted_activities"])
            self.assertIs(observed_post["hosted_activities"][0]["native_completed"], True)
            self.assertIs(observed_post["hosted_activities"][0]["native_invalidated"], False)
            self.assertEqual(observed_post["balances"], completed["balances"])
            self.assertEqual(observed_post["exact_ck3_build"], "1.20.0.2")
        self.assertEqual([row["step"] for row in driver.requests], [
            "query-activity-stage5-feast-full-cost-v1-private",
            "query-activity-feast-hosted-post-v1-private",
        ])
        self.assertEqual([row["expected_revision"] for row in driver.requests], [3, 12])
        self.assertEqual([row["expected_date_raw"] for row in driver.requests], [53219928, 53220000])

    async def test_disabled_private_queries_are_absent_from_sdk_discovery(self):
        from mcp import Client

        driver = NativeWrapperWireDriver(actual_wire("ck3_12002_feast_fullcost_wire.json"))
        driver.allow_private_activity_stage5_feast_full_cost_query = False
        driver.allow_private_activity_feast_stage5_start_query = False
        async with Client(create_server(driver)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
        self.assertNotIn(COST_TOOL, names)
        self.assertNotIn(POST_TOOL, names)
        self.assertEqual(driver.requests, [])


if __name__ == "__main__":
    unittest.main()
