"""Official MCP SDK to real driver wrappers using frozen native Feast wire."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from copy import deepcopy
import json
import os

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from test_ck3_12002_feast_wire import FixtureDriver, actual_wire
from test_activity_feast_guest_route_proof_private_transport import GuestRouteProofTransportTests
from test_activity_feast_guest_rule_provenance_private_transport import (
    Driver as ProvenanceDriver, payload as provenance_payload,
)
from test_activity_feast_guest_opinion_private_transport import (
    Driver as GuestOpinionDriver, snapshot as opinion_snapshot,
    payload as guest_opinion_payload,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002, CK3_12003
from xar_autoplayer.activity_feast_stage5_start_formal_consumer import (
    assess_feast_start_private_v1,
)


COST_TOOL = "ck3_query_activity_stage5_feast_full_cost_private_v1"
POST_TOOL = "ck3_query_activity_feast_hosted_post_private_v1"
ROUTE_TOOL = "ck3_query_activity_feast_guest_route_proof_private_v1"
PROVENANCE_TOOL = "ck3_query_activity_feast_guest_rule_provenance_private_v1"
INPUT_TOOL = "ck3_query_activity_feast_stage5_start_inputs_private_v1"
OPINION_TOOL = "ck3_query_activity_feast_guest_opinion_private_v1"
TARGET_ACTIVITY_ID = 83886111


def guest_opinion_sdk_payload():
    native = guest_opinion_payload()
    native["snapshot_revision"] = 4
    native["reward_opinion_modifiers"] = {
        "hosted_feast_opinion": {"status": "observed", "present": False, "value": None},
        "hosted_mediocre_feast_opinion": {"status": "observed", "present": False, "value": None},
        "impressed_opinion": {"status": "observed", "present": True, "value": 10},
    }
    return native


def observed_activity_target():
    return {
        "status": "observed", "activity_id": TARGET_ACTIVITY_ID,
        "guest_character_id": 32000, "host_character_id": 31000,
        "activity_type_key": "activity_feast",
        "native_completed": True, "native_invalidated": False,
        "attending_list_observed": True, "attending_count": 1,
        "target_in_attending_list": True, "character_record_observed": True,
        "character_activity_id": TARGET_ACTIVITY_ID,
        "character_activity_state_raw": 2,
        "character_record_matches_activity": True, "native_active_attendee": True,
    }


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


class OrdinaryInputWireDriver(FixtureDriver):
    """Actual compiled serializer inputs, using the production .3 driver method."""

    command_timeout_seconds = 1
    query_activity_feast_stage5_start_inputs_private_v1 = (
        NativeHeadlessGameplayDriver.query_activity_feast_stage5_start_inputs_private_v1
    )

    def __init__(self, payload):
        super().__init__(payload)
        self.snapshot["diagnostics"]["hello"] = {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256,
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


class GuestOpinionWireDriver(GuestOpinionDriver):
    """Actual production named-reader wire with .3 same-paused-frame identity."""

    def __init__(self, native):
        super().__init__(native)
        self.before = opinion_snapshot()
        self.before.update({"snapshot_id": "native:4", "native_revision": 4})
        self.before["diagnostics"] = {"hello": {
            "expected_ck3_version": CK3_12003.game_version,
            "expected_ck3_sha256": CK3_12003.executable_sha256,
        }}
        self.after = deepcopy(self.before)

    def take_snapshot(self):
        return deepcopy(self.before if not self.sent else self.after)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class FeastMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_guest_activity_target_default_sdk_call_preserves_old_wire(self):
        from mcp import Client

        for optional_arguments in ({}, {"activity_id": None}):
            with self.subTest(arguments=optional_arguments):
                native = guest_opinion_sdk_payload()
                driver = GuestOpinionWireDriver(native)
                async with Client(create_server(driver)) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    schema = tools[OPINION_TOOL].input_schema
                    self.assertEqual(set(schema["properties"]),
                                     {"expected_revision", "guest_character_id", "activity_id"})
                    self.assertEqual(set(schema["required"]),
                                     {"expected_revision", "guest_character_id"})
                    self.assertIsNone(schema["properties"]["activity_id"]["default"])
                    self.assertIs(tools[OPINION_TOOL].annotations.read_only_hint, True)
                    reply = await client.call_tool(OPINION_TOOL, {
                        "expected_revision": 5, "guest_character_id": 32000,
                        **optional_arguments,
                    })
                self.assertFalse(reply.is_error)
                observed = reply.structured_content
                self.assertNotIn("activity_target", observed)
                self.assertNotIn("activity_target_ready", observed)
                self.assertNotIn("activity_id", driver.sent[0])
                self.assertEqual(observed["reward_opinion_modifiers"], native["reward_opinion_modifiers"])
                self.assertEqual(observed["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(observed["exe_sha256"], CK3_12003.executable_sha256)
                self.assertEqual(observed["queried_snapshot_id"], observed["post_snapshot_id"])
                self.assertEqual(driver.sent[0]["expected_revision"], 4)
                self.assertEqual(len(driver.sent), 1)

    async def test_guest_activity_target_sdk_observes_member_empty_and_no_record(self):
        from mcp import Client

        current = observed_activity_target()
        empty = {**current, "attending_count": 0, "target_in_attending_list": False,
                 "character_activity_id": 0xFFFFFFFF, "character_activity_state_raw": 3,
                 "character_record_matches_activity": False, "native_active_attendee": False}
        no_record = {**empty, "character_record_observed": False,
                     "character_activity_id": None, "character_activity_state_raw": None,
                     "character_record_matches_activity": None, "native_active_attendee": None}
        different_activity = {**current, "character_activity_id": TARGET_ACTIVITY_ID + 1,
                              "character_record_matches_activity": False,
                              "native_active_attendee": False}
        different_state = {**current, "character_activity_state_raw": 1,
                           "native_active_attendee": False}
        for case, target in (("current", current), ("empty", empty),
                             ("no_record", no_record), ("different_activity", different_activity),
                             ("different_state", different_state)):
            with self.subTest(case=case):
                native = guest_opinion_sdk_payload()
                native["activity_target"] = target
                driver = GuestOpinionWireDriver(native)
                async with Client(create_server(driver)) as client:
                    reply = await client.call_tool(OPINION_TOOL, {
                        "expected_revision": 5, "guest_character_id": 32000,
                        "activity_id": TARGET_ACTIVITY_ID,
                    })
                self.assertFalse(reply.is_error)
                observed = reply.structured_content
                self.assertEqual(observed["activity_target"], target)
                self.assertIs(observed["activity_target_ready"], True)
                self.assertEqual(observed["reward_opinion_modifiers"], native["reward_opinion_modifiers"])
                self.assertEqual(observed["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(observed["exe_sha256"], CK3_12003.executable_sha256)
                self.assertEqual(observed["queried_snapshot_id"], observed["post_snapshot_id"])
                self.assertEqual(driver.sent[0]["activity_id"], TARGET_ACTIVITY_ID)
                self.assertEqual(driver.sent[0]["expected_revision"], 4)
                self.assertEqual(len(driver.sent), 1)
                self.assertNotIn("benefit_verified", observed)
                self.assertNotIn("attendance_verified", observed)

    async def test_guest_activity_target_sdk_rejects_unknown_or_mistyped_status(self):
        from mcp import Client

        for status in (False, "not_requested", "unrecognised_status"):
            with self.subTest(status=status):
                native = guest_opinion_sdk_payload()
                native["activity_target"] = {**observed_activity_target(), "status": status}
                driver = GuestOpinionWireDriver(native)
                async with Client(create_server(driver)) as client:
                    reply = await client.call_tool(OPINION_TOOL, {
                        "expected_revision": 5, "guest_character_id": 32000,
                        "activity_id": TARGET_ACTIVITY_ID,
                    })
                self.assertTrue(reply.is_error)
                self.assertEqual(len(driver.sent), 1)

    async def test_guest_activity_target_sdk_keeps_unavailable_independent_of_opinion(self):
        from mcp import Client

        for status in ("attending_list_unavailable", "character_record_unavailable"):
            with self.subTest(status=status):
                target = {key: None for key in observed_activity_target()}
                target.update(status=status, activity_id=TARGET_ACTIVITY_ID,
                              guest_character_id=32000)
                native = guest_opinion_sdk_payload()
                native["activity_target"] = target
                driver = GuestOpinionWireDriver(native)
                async with Client(create_server(driver)) as client:
                    reply = await client.call_tool(OPINION_TOOL, {
                        "expected_revision": 5, "guest_character_id": 32000,
                        "activity_id": TARGET_ACTIVITY_ID,
                    })
                self.assertFalse(reply.is_error)
                observed = reply.structured_content
                self.assertEqual(observed["status"], "observed")
                self.assertEqual(observed["guest_opinion_of_actor"], native["guest_opinion_of_actor"])
                self.assertEqual(observed["activity_target"], target)
                self.assertIs(observed["activity_target_ready"], False)
                self.assertIsNone(observed["activity_target"]["target_in_attending_list"])
                self.assertIsNone(observed["activity_target"]["native_active_attendee"])
                self.assertEqual(observed["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(driver.sent[0]["activity_id"], TARGET_ACTIVITY_ID)

        target["target_in_attending_list"] = False
        native["activity_target"] = target
        driver = GuestOpinionWireDriver(native)
        async with Client(create_server(driver)) as client:
            reply = await client.call_tool(OPINION_TOOL, {
                "expected_revision": 5, "guest_character_id": 32000,
                "activity_id": TARGET_ACTIVITY_ID,
            })
        self.assertTrue(reply.is_error)

    async def test_fixed_reward_modifiers_use_actual_native_wire_through_official_sdk(self):
        from mcp import Client

        path = os.environ.get("XAR_FEAST_REWARD_FIXTURE_WIRE")
        if path is None:
            self.skipTest("production named-reader wire is not configured")
        wires = json.loads(Path(path).read_text(encoding="utf-8"))
        for case, wire in wires.items():
            with self.subTest(case=case):
                driver = GuestOpinionWireDriver(wire)
                async with Client(create_server(driver)) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertIs(tools[OPINION_TOOL].annotations.read_only_hint, True)
                    self.assertEqual(set(tools[OPINION_TOOL].input_schema["properties"]),
                                     {"expected_revision", "guest_character_id", "activity_id"})
                    self.assertEqual(set(tools[OPINION_TOOL].input_schema["required"]),
                                     {"expected_revision", "guest_character_id"})
                    reply = await client.call_tool(OPINION_TOOL, {
                        "expected_revision": 5, "guest_character_id": 32000,
                    })
                    self.assertFalse(reply.is_error)
                    observed = reply.structured_content
                self.assertEqual(observed["reward_opinion_modifiers"], wire["reward_opinion_modifiers"])
                self.assertEqual(observed["guest_character_id"], 32000)
                self.assertEqual(observed["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(observed["exe_sha256"], CK3_12003.executable_sha256)
                self.assertEqual(observed["queried_snapshot_id"], observed["post_snapshot_id"])
                self.assertNotIn("benefit_verified", observed)
                self.assertNotIn("attendance_verified", observed)
                self.assertEqual(len(driver.sent), 1)
                self.assertEqual(driver.sent[0]["expected_revision"], 4)
                self.assertEqual(driver.sent[0]["guest_character_id"], 32000)
                self.assertEqual(driver.sent[0]["expected_actor_character_id"], 31000)
                self.assertNotIn("modifier_key", driver.sent[0])

    async def test_disabled_fixed_reward_query_is_absent_from_sdk_discovery(self):
        from mcp import Client

        path = os.environ.get("XAR_FEAST_REWARD_FIXTURE_WIRE")
        if path is None:
            self.skipTest("production named-reader wire is not configured")
        native = json.loads(Path(path).read_text(encoding="utf-8"))["absent_and_zero"]
        driver = GuestOpinionWireDriver(native)
        driver.allow_private_activity_feast_guest_opinion_query = False
        async with Client(create_server(driver)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
        self.assertNotIn(OPINION_TOOL, names)
        self.assertEqual(driver.sent, [])

    async def test_actual_ordinary_serializer_sdk_and_policy_keep_positive_negative_unavailable(self):
        from mcp import Client

        wires = actual_wire("ck3_12003_feast_ordinary_start_wire.json")
        budget = {
            "reserved_raw": {"gold": 0, "treasury": 0, "piety": 0, "barter_goods": 0},
            "peaceful_spend_allowed": True, "gold_floor_raw": 20000000,
            "active_war_count": 0, "war_cash_reserve_raw": None,
        }
        for index, wire in enumerate(wires):
            with self.subTest(case=index):
                driver = OrdinaryInputWireDriver(wire)
                async with Client(create_server(driver)) as client:
                    tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                    self.assertIs(tools[INPUT_TOOL].annotations.read_only_hint, True)
                    reply = await client.call_tool(INPUT_TOOL, {"expected_revision": 5})
                    self.assertFalse(reply.is_error)
                    inputs = reply.structured_content
                self.assertEqual(inputs["ordinary_guest_route"], wire["ordinary_guest_route"])
                self.assertEqual(inputs["exact_ck3_build"], CK3_12003.game_version)
                self.assertEqual(inputs["exe_sha256"], CK3_12003.executable_sha256)
                self.assertEqual(inputs["selected_nonhost_count"], 0)
                self.assertEqual(inputs["timely_positive_join_count"], 0)
                self.assertEqual(driver.requests[0]["expected_revision"], 11)
                self.assertEqual(len(driver.requests), 1)
                self.assertNotIn("policy_positive", driver.requests[0])
                assessment = assess_feast_start_private_v1(inputs, guest=None, budget=budget)
                self.assertEqual(assessment["decision"], "start" if index == 0 else "hold")
                if index == 0:
                    self.assertEqual(assessment["submit_reserve_raw"], [20000000, 0, 0, 0])
                    war_budget = {**budget, "active_war_count": 1}
                    held = assess_feast_start_private_v1(inputs, guest=None, budget=war_budget)
                    self.assertEqual(held["reason"], "war_cash_reserve_unobserved")
                elif index == 1:
                    self.assertEqual(inputs["ordinary_guest_route"]["status"], "observed")
                    self.assertIs(inputs["ordinary_guest_route"]["candidate_membership"], False)
                else:
                    self.assertEqual(inputs["ordinary_guest_route"]["status"], "unavailable")
                    self.assertIsNone(inputs["ordinary_guest_route"]["candidate_membership"])

    async def test_ordinary_wire_frame_disagreement_is_reported_as_sdk_error(self):
        from mcp import Client

        wire = deepcopy(actual_wire("ck3_12003_feast_ordinary_start_wire.json")[0])
        wire["ordinary_guest_route"]["candidate"]["date_raw"] += 24
        driver = OrdinaryInputWireDriver(wire)
        async with Client(create_server(driver)) as client:
            reply = await client.call_tool(INPUT_TOOL, {"expected_revision": 5})
        self.assertTrue(reply.is_error)
        self.assertEqual(len(driver.requests), 1)

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
