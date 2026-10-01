"""Actual native packets -> production driver wrappers -> in-memory MCP SDK."""

from __future__ import annotations

import unittest

from test_ck3_12002_realm_law_formal_wire import query_frame, receipt_frame, wire
from test_ck3_12002_sway_law_transport_wire import FixtureDriver, envelope, paused_frame
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class PacketSdkDriver(FixtureDriver):
    """Use real public wrapper functions without initializing any native pipe."""

    command_timeout_seconds = 30.0
    allow_private_realm_law_action = True
    allow_private_realm_law_paused_query = False
    query_realm_law_crown_action_private_v1 = NativeHeadlessGameplayDriver.query_realm_law_crown_action_private_v1
    submit_realm_law_crown_private_v1 = NativeHeadlessGameplayDriver.submit_realm_law_crown_private_v1
    query_realm_law_crown_receipt_private_v1 = NativeHeadlessGameplayDriver.query_realm_law_crown_receipt_private_v1
    query_active_scheme_sway_target_private_v1 = NativeHeadlessGameplayDriver.query_active_scheme_sway_target_private_v1
    submit_active_scheme_sway_private_v1 = NativeHeadlessGameplayDriver.submit_active_scheme_sway_private_v1
    query_active_scheme_sway_receipt_private_v1 = NativeHeadlessGameplayDriver.query_active_scheme_sway_receipt_private_v1


class SwayLaw12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_law_quote_submit_and_material_receipt_reach_the_production_sdk(self) -> None:
        from mcp import Client

        driver = PacketSdkDriver(wire("query"), query_frame())
        async with Client(create_server(driver)) as client:
            quote = await client.call_tool("ck3_query_realm_law_crown_action_private_v1", {
                "expected_revision": driver.snapshot["revision"],
            })
            self.assertFalse(quote.is_error)
            readback = quote.structured_content
            self.assertEqual(readback["proof_epoch"], wire("query")["observation"]["proof_epoch"])
            driver.reply = wire("submit-pending")
            ack = driver.reply["ack"]
            submitted = await client.call_tool("ck3_enact_realm_law_crown_private_v1", {
                "readback": readback, "law_key": ack["requested_law_key"],
                "budgets": {"prestige": 20000000}, "action_id": ack["submitted_request_id"],
            })
            self.assertFalse(submitted.is_error)
            self.assertFalse(submitted.structured_content["material_result"])
            self.assertEqual(submitted.structured_content["status"], "submitted_verification_pending")
            driver.reply = wire("receipt-enacted")
            native_receipt = driver.reply["receipt"]
            driver.snapshot = receipt_frame(native_receipt)
            received = await client.call_tool("ck3_query_realm_law_crown_receipt_private_v1", {
                "expected_revision": driver.snapshot["revision"],
                "submitted_request_id": native_receipt["submitted_request_id"],
            })
            self.assertFalse(received.is_error)
            self.assertTrue(received.structured_content["material_result"])
            self.assertEqual(received.structured_content["effective_law_key"], native_receipt["effective_law_key"])
            self.assertTrue(received.structured_content["resources_verified"])
            self.assertTrue(received.structured_content["succession_verified"])
        self.assertEqual(len(driver.sent), 3)

    async def test_sway_quote_submit_and_independent_instance_receipt_reach_the_production_sdk(self) -> None:
        from mcp import Client

        query = envelope("ck3_12002_sway_query_wire.json")
        value = query["active_scheme_sway"]
        driver = PacketSdkDriver(query, paused_frame(value))
        async with Client(create_server(driver)) as client:
            quote = await client.call_tool("ck3_query_active_scheme_sway_target_private_v1", {
                "expected_revision": driver.snapshot["revision"],
                "target_character_id": value["target_character_id"],
            })
            self.assertFalse(quote.is_error)
            readback = quote.structured_content
            self.assertEqual(readback["active_sway_instances"], [])
            driver.reply = envelope("ck3_12002_sway_submit_wire.json")
            action_id = driver.reply["active_scheme_sway_formal"]["action_id"]
            submitted = await client.call_tool("ck3_start_active_scheme_sway_private_v1", {
                "readback": readback, "action_id": action_id,
            })
            self.assertFalse(submitted.is_error)
            ack = submitted.structured_content
            self.assertEqual(ack["stage"], "submitted_verification_pending")
            self.assertTrue(ack["receipt_pending"])
            driver.reply = envelope("ck3_12002_sway_receipt_wire.json")
            received = await client.call_tool("ck3_query_active_scheme_sway_receipt_private_v1", {
                "target_character_id": value["target_character_id"], "action_id": action_id,
                "expected_revision": readback["queried_native_revision"],
                "pre_capture_epoch": ack["pre_capture_epoch"],
            })
            self.assertFalse(received.is_error)
            receipt = received.structured_content
            self.assertEqual(receipt["stage"], "applied")
            self.assertTrue(receipt["postcondition_verified"])
            self.assertEqual(receipt["scheme_instance_id"], driver.reply["active_scheme_sway_formal"]["scheme_instance_id"])
            self.assertNotIn("terminal", receipt)
        self.assertEqual(len(driver.sent), 3)


if __name__ == "__main__":
    unittest.main()
