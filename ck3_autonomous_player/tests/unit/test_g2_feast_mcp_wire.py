"""Official MCP SDK to real driver wrappers using frozen native Feast wire."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_feast_wire import FixtureDriver, actual_wire
from test_activity_feast_guest_route_proof_private_transport import GuestRouteProofTransportTests
from test_activity_feast_guest_rule_provenance_private_transport import (
    Driver as ProvenanceDriver, payload as provenance_payload,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002, CK3_12003


COST_TOOL = "ck3_query_activity_stage5_feast_full_cost_private_v1"
POST_TOOL = "ck3_query_activity_feast_hosted_post_private_v1"
ROUTE_TOOL = "ck3_query_activity_feast_guest_route_proof_private_v1"
PROVENANCE_TOOL = "ck3_query_activity_feast_guest_rule_provenance_private_v1"


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


class GuestRouteWireDriver(FixtureDriver):
    """Local endpoint for the existing typed route-proof transport, with .3 hello."""

    allow_private_activity_feast_guest_route_proof_query = True

    def __init__(self):
        fixture = GuestRouteProofTransportTests()
        fixture.setUp()
        super().__init__(fixture.payload)
        self.snapshot["diagnostics"]["hello"] = {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256,
        }

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": self.requests[-1]["step"], "accepted": True,
                "status": "available", "private_build": True,
                "read_only": True, "advertised": False,
                "backend_id": "native-headless",
                "activity_feast_guest_route_proof": self.payload,
            },
        }


class GuestProvenanceWireDriver(ProvenanceDriver):
    """Existing membership envelope and endpoint with the actual .3 identity contract."""

    def take_snapshot(self) -> dict[str, object]:
        value = super().take_snapshot()
        value["diagnostics"] = {"hello": {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256,
        }}
        return value


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class FeastMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_named_provenance_reads_real_transport_positive_and_negative_membership(self):
        from mcp import Client

        for member in (True, False):
            with self.subTest(member=member):
                driver = GuestProvenanceWireDriver(provenance_payload(member=member))
                async with Client(create_server(driver)) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertIs(tools[PROVENANCE_TOOL].annotations.read_only_hint, True)
                    reply = await client.call_tool(PROVENANCE_TOOL, {
                        "expected_revision": 5,
                        "authored_rule_key": driver.native["authored_rule_key"],
                        "candidate_character_id": driver.native["candidate_character_id"],
                    })
                    self.assertFalse(reply.is_error)
                    observed = reply.structured_content
                    self.assertIs(observed["candidate_membership"], member)
                    self.assertEqual(observed["filtered_rule_character_ids"], driver.native["filtered_rule_character_ids"])
                    self.assertEqual(observed["exact_ck3_build"], CK3_12003.game_version)
                    self.assertEqual(observed["exe_sha256"], CK3_12003.executable_sha256)
                    self.assertEqual(observed["queried_snapshot_id"], observed["post_snapshot_id"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-activity-feast-guest-rule-provenance-v1")
                self.assertEqual(request["expected_revision"], driver.native["snapshot_revision"])
                self.assertEqual(request["expected_date_raw"], driver.native["date_raw"])
                self.assertEqual(request["expected_actor_character_id"], driver.native["actor_character_id"])
                self.assertEqual(request["authored_rule_key"], driver.native["authored_rule_key"])
                self.assertEqual(request["candidate_character_id"], driver.native["candidate_character_id"])
                self.assertNotIn("policy_approved", request)

    async def test_disabled_named_provenance_is_absent_from_sdk_discovery(self):
        from mcp import Client

        driver = GuestProvenanceWireDriver(provenance_payload())
        driver.allow_private_activity_feast_guest_rule_provenance_query = False
        async with Client(create_server(driver)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
        self.assertNotIn(PROVENANCE_TOOL, names)
        self.assertEqual(driver.sent, [])

    async def test_sdk_route_proof_uses_typed_transport_and_selected_build_identity(self):
        from mcp import Client

        driver = GuestRouteWireDriver()
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertIs(tools[ROUTE_TOOL].annotations.read_only_hint, True)
            reply = await client.call_tool(ROUTE_TOOL, {"expected_revision": 5})
            self.assertFalse(reply.is_error)
            proof = reply.structured_content
            self.assertEqual(proof["pre_invitation_candidate"], driver.payload["pre_invitation_candidate"])
            self.assertEqual(proof["selected_nonhost_rows"], [])
            self.assertIs(proof["native_guest_route_qualified"], False)
            self.assertEqual(proof["exact_ck3_build"], CK3_12003.game_version)
            self.assertEqual(proof["exe_sha256"], CK3_12003.executable_sha256)
            self.assertEqual(proof["queried_native_revision"], driver.payload["snapshot_revision"])
            self.assertEqual(proof["queried_snapshot_id"], proof["post_snapshot_id"])
        self.assertEqual(len(driver.requests), 1)
        request = driver.requests[0]
        self.assertEqual(request["step"], "query-activity-feast-stage5-guest-route-proof-v1-private")
        self.assertEqual(request["expected_revision"], driver.payload["snapshot_revision"])
        self.assertEqual(request["expected_date_raw"], driver.payload["date_raw"])
        self.assertEqual(request["expected_actor_character_id"], driver.payload["actor_character_id"])
        self.assertEqual(request["expected_planning_stage"], driver.payload["planning_stage"])
        self.assertEqual(request["expected_activity_key"], driver.payload["activity_key"])

    async def test_disabled_route_proof_is_absent_from_sdk_discovery(self):
        from mcp import Client

        driver = GuestRouteWireDriver()
        driver.allow_private_activity_feast_guest_route_proof_query = False
        async with Client(create_server(driver)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
        self.assertNotIn(ROUTE_TOOL, names)
        self.assertEqual(driver.requests, [])

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
