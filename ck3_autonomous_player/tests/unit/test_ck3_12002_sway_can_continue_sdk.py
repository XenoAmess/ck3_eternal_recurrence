"""Only the new actual 37-field native CanContinue packet increment."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from test_ck3_12002_sway_completion_sdk import ProtocolCompletionSdkDriver
from xar_autoplayer.bridge.mcp_server import create_server


FIXTURES = Path(__file__).resolve().parents[2] / "native_bridge/research/fixtures/ck3_12002_sway_can_continue"


def packet(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class SwayCanContinue12002SdkTest(unittest.IsolatedAsyncioTestCase):
    async def test_three_new_actual_packets_preserve_true_false_and_unobserved_null_through_the_protocol_sdk(self) -> None:
        from mcp import Client

        driver = ProtocolCompletionSdkDriver(packet("can-continue-true-wire.json"))
        driver.allow_private_active_scheme_sway_completion_query = True
        before = driver.take_snapshot()
        outputs = {}
        async with Client(create_server(driver)) as client:
            for name in packet("provenance.json")["payload_sha256"]:
                with self.subTest(packet=name):
                    driver.packet = packet(name)
                    native = driver.packet["result"]["sway_completion"]
                    received = await client.call_tool("ck3_query_active_scheme_sway_completion_private_v1", {
                        "expected_revision": before["revision"],
                        "target_character_id": native["target_character_id"],
                        "scheme_instance_id": native["scheme_instance_id"],
                    })
                    self.assertFalse(received.is_error, received.content)
                    actual = received.structured_content
                    self.assertEqual(driver.last_ingest, "command_result")
                    self.assertEqual({key: actual[key] for key in native}, native)
                    self.assertIs(actual["native_can_continue"], native["native_can_continue"])
                    self.assertEqual(actual["queried_native_revision"], native["snapshot_revision"])
                    self.assertFalse(actual["terminal_cause_observed"])
                    self.assertEqual(actual["terminal_cause"], "unknown")
                    outputs[name] = actual
        yes = outputs["can-continue-true-wire.json"]
        no = outputs["can-continue-false-wire.json"]
        terminal = outputs["can-continue-not-applicable-terminal-wire.json"]
        self.assertTrue(yes["native_can_continue_observed"])
        self.assertIs(yes["native_can_continue"], True)
        self.assertTrue(no["native_can_continue_observed"])
        self.assertIs(no["native_can_continue"], False)
        self.assertEqual(no["native_status_raw"], 0)
        self.assertFalse(no["native_terminal_state_observed"])
        self.assertFalse(terminal["native_can_continue_observed"])
        self.assertIsNone(terminal["native_can_continue"])
        self.assertTrue(terminal["native_terminal_state_observed"])
        self.assertEqual(len(driver.sent), 3)


if __name__ == "__main__":
    unittest.main()
