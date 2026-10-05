"""Native emitted invitation receipt through the typed driver and registered MCP.

These are offline transport tests. No live ally invitation or war join is
claimed by this fixture.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
FIXTURES = Path(os.environ.get("XAR_CALL_ALLY_FIXTURE_DIR", ROOT / "native_bridge/research/fixtures"))

from xar_autoplayer.bridge.call_ally_to_war_private_action_v1 import SUBMIT_STEP
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.family_obligations_private_transport import STEP as QUERY_STEP
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


def packet(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class NativeFixtureDriver:
    allow_private_family_obligations_query = True
    command_timeout_seconds = 1.0
    query_family_obligations_private_v1 = NativeHeadlessGameplayDriver.query_family_obligations_private_v1
    submit_call_ally_to_war_private_v1 = NativeHeadlessGameplayDriver.submit_call_ally_to_war_private_v1

    def __init__(self):
        self.quote = packet("ck3_12003_call_ally_to_war_family_quote.json")
        self.receipt = packet("ck3_12003_call_ally_to_war_submit.json")
        native = self.receipt["result"]
        self.snapshot = {
            "snapshot_id": "call-ally-static-fixture",
            "revision": native["pre_native_revision"] + 1,
            "native_revision": native["pre_native_revision"],
            "date_raw": native["date_raw"], "paused": True, "map_ready": True,
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "diagnostics": {"hello": {"expected_ck3_version": native["game_version"],
                                      "expected_ck3_sha256": native["executable_sha256"]}},
        }
        self.endpoint = self.state = self
        self.requests: list[dict[str, object]] = []

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        request = self.requests[-1]
        source = self.quote if request["step"] == QUERY_STEP else self.receipt
        result = deepcopy(source)
        # Correlation alone changes in the native-produced serializer packets.
        result["request_id"] = request_id
        return result

    def arguments(self):
        source = self.receipt["result"]
        return {"expected_revision": self.snapshot["revision"],
                "war_id": source["war_id"],
                "recipient_character_id": source["recipient_character_id"]}


class CallAllyTransportTests(unittest.TestCase):
    def test_native_queued_receipt_is_pending_and_costs_remain_exact(self):
        driver = NativeFixtureDriver()
        result = driver.submit_call_ally_to_war_private_v1(**driver.arguments())
        emitted = driver.receipt["result"]
        self.assertTrue(result["submitted"])
        self.assertTrue(result["verification_pending"])
        self.assertFalse(result["material_result"])
        self.assertFalse(result["automatic_retry"])
        self.assertEqual(result["actual_send_cost_raw"], emitted["actual_send_cost_raw"])
        self.assertEqual([request["step"] for request in driver.requests], [QUERY_STEP, SUBMIT_STEP])
        self.assertEqual(driver.requests[-1]["expected_revision"], emitted["pre_native_revision"])
        self.assertEqual(driver.requests[-1]["expected_send_cost_raw"], emitted["actual_send_cost_raw"])
        self.assertEqual(driver.requests[-1]["war_id"], emitted["war_id"])
        self.assertEqual(driver.requests[-1]["recipient_character_id"], emitted["recipient_character_id"])
        self.assertNotIn("ally_joined", result)

    def test_unobserved_native_legality_remains_unavailable_without_native_send(self):
        driver = NativeFixtureDriver()
        row = driver.quote["result"]["alliance_obligations"]["first_wars"][0]
        row["native_complete_can_send"] = None
        with self.assertRaises(BridgeUnavailableError):
            driver.submit_call_ally_to_war_private_v1(**driver.arguments())
        self.assertEqual([request["step"] for request in driver.requests], [QUERY_STEP])

    def test_unsampled_rejected_receipt_stays_unsubmitted_without_zero_cost_claim(self):
        # A synthetic rejected envelope exercises the optional cost branch;
        # the successful transport test above uses unchanged native bytes.
        driver = NativeFixtureDriver()
        native = driver.receipt["result"]
        native.update(status="rejected", accepted=False, send_cost_sampled=False,
                      actual_send_cost_raw=None, selected_target_native_legal=False,
                      copied_context_identity_verified=False, reason="fixture rejection")
        result = driver.submit_call_ally_to_war_private_v1(**driver.arguments())
        self.assertFalse(result["submitted"])
        self.assertFalse(result["verification_pending"])
        self.assertFalse(result["material_result"])
        self.assertIsNone(result["actual_send_cost_raw"])
        self.assertFalse(result["automatic_retry"])
        self.assertEqual(len(driver.requests), 2)

    def test_stale_public_revision_never_sends(self):
        driver = NativeFixtureDriver()
        args = driver.arguments()
        args["expected_revision"] -= 1
        with self.assertRaises(BridgeUnavailableError):
            driver.submit_call_ally_to_war_private_v1(**args)
        self.assertEqual(driver.requests, [])


class CallAllyRegisteredMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_observed_native_refusal_retains_terms_without_submission(self):
        from mcp import Client

        driver = NativeFixtureDriver()
        row = driver.quote["result"]["alliance_obligations"]["first_wars"][0]
        # Synthetic diagnostic values exercise the changed .3 consumer only;
        # they do not claim a fresh native C88 capture or live war observation.
        row.update(
            native_complete_can_send=False,
            native_send_precheck_passed=False,
            native_send_setup_passed=True,
            native_send_availability_passed=True,
            native_send_pair_restriction_blocked=False,
            native_send_diplomatic_range_passed=True,
            native_send_already_considering_blocked=False,
            native_send_answer_status_raw=2,
            native_send_definition_gate_results=[True, False, True, True, True, True, True],
            native_first_failed_send_stage="definition_c88",
            native_c88_failure_description_status="observed",
            native_c88_failure_description_text="#N Receiver clause false#!\n#P Context true#!; UTF8: 对象",
        )
        expected_terms = deepcopy(row)
        async with Client(create_server(driver)) as client:
            response = await client.call_tool(
                "ck3_submit_call_ally_to_war_private_v1", driver.arguments())
        self.assertFalse(response.is_error, response.content)
        result = response.structured_content
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["reason"], "call_ally_native_complete_can_send_false")
        self.assertEqual(result["selected_native_terms"], expected_terms)
        self.assertEqual(result["quoted_send_cost_raw"], expected_terms["send_cost_raw"])
        self.assertEqual(result["result_source"], "native_family_query")
        self.assertTrue(result["read_only"])
        self.assertIsNone(result["request_id"])
        self.assertEqual(result["queried_revision"], driver.snapshot["revision"])
        self.assertEqual(result["queried_native_revision"], driver.snapshot["native_revision"])
        self.assertEqual(result["source_query_frame"], driver.quote["result"]["frame"])
        for key in ("accepted", "submitted", "material_result", "verification_pending",
                    "native_submit_attempted", "automatic_retry"):
            self.assertIs(result[key], False, key)
        self.assertNotIn("actual_send_cost_raw", result)
        self.assertNotIn("ally_joined", result)
        self.assertEqual([request["step"] for request in driver.requests], [QUERY_STEP])
        row["send_cost_raw"][0] += 1
        row["attacker_character_ids"].append(42)
        self.assertEqual(result["selected_native_terms"], expected_terms)

    async def test_registered_action_replays_native_packets_and_separates_ack_from_join(self):
        from mcp import Client

        driver = NativeFixtureDriver()
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            name = "ck3_submit_call_ally_to_war_private_v1"
            self.assertIn(name, tools)
            annotation = tools[name].annotations
            self.assertFalse(annotation is not None and annotation.read_only_hint is True)
            response = await client.call_tool(name, driver.arguments())
        self.assertFalse(response.is_error, response.content)
        result = response.structured_content
        self.assertEqual(result["status"], "receipt_pending")
        self.assertFalse(result["material_result"])
        self.assertEqual(result["war_id"], driver.receipt["result"]["war_id"])
        self.assertEqual(len(driver.requests), 2)

    async def test_existing_family_permit_controls_action_registration(self):
        from mcp import Client

        driver = NativeFixtureDriver()
        driver.allow_private_family_obligations_query = False
        async with Client(create_server(driver)) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
        self.assertNotIn("ck3_submit_call_ally_to_war_private_v1", names)
        self.assertEqual(driver.requests, [])


if __name__ == "__main__":
    unittest.main()
