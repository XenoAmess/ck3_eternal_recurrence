"""Actual nonwar family provider and caller packets through Python and MCP."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
FIXTURES = ROOT / "native_bridge/research/fixtures"

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002


def wire(name):
    return json.loads((FIXTURES / f"ck3_12002_family_obligations_{name}.json").read_text(encoding="utf-8"))


class FamilyNativeWireDriver:
    command_timeout_seconds = 1.0
    allow_private_family_obligations_query = True
    query_family_obligations_private_v1 = NativeHeadlessGameplayDriver.query_family_obligations_private_v1

    def __init__(self, packet):
        self.packet = packet
        self.endpoint = self.state = self
        self.requests = []
        frame = packet["result"]["frame"]
        self.snapshot = {"paused": True, "map_ready": True,
                         "revision": frame["snapshot_revision"] + 1,
                         "native_revision": frame["snapshot_revision"],
                         "snapshot_id": "native:" + str(frame["snapshot_revision"]),
                         "date_raw": frame["date_raw"],
                         "played_character": {"character_id": frame["played_character_id"], "alive": True},
                         "diagnostics": {"hello": {
                             "expected_ck3_version": CK3_12002.game_version,
                             "expected_ck3_sha256": CK3_12002.executable_sha256}}}

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        packet = deepcopy(self.packet)
        packet["request_id"] = request_id
        return packet


def request(packet):
    result = packet["result"]
    lineage = result["native_child_house_preview"]
    args = {"expected_revision": result["frame"]["snapshot_revision"] + 1,
            "subject_character_id": lineage["subject_character_id"],
            "candidate_character_id": lineage["candidate_character_id"],
            "request_matrilineal_option": lineage["requested_matrilineal_option"]}
    terms = result["betrothal_break_terms"]
    if terms["status"] != "not_requested":
        args["break_recipient_character_id"] = terms["requested_recipient_character_id"]
    return args


class FamilyObligationsPythonWireTests(unittest.TestCase):
    def test_actual_native_byte_provenance(self):
        manifest = json.loads((FIXTURES / "ck3_12002_family_obligations_python_provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["local_ck3_operations"], [])
        for row in manifest["fixtures"]:
            self.assertEqual(hashlib.sha256((FIXTURES / row["file"]).read_bytes()).hexdigest(), row["sha256"])

    def test_real_selected_option_preserves_native_effective_lineality(self):
        packet = wire("mailbox")
        driver = FamilyNativeWireDriver(packet)
        result = driver.query_family_obligations_private_v1(**request(packet))
        lineage = result["native_child_house_preview"]
        self.assertEqual(lineage, packet["result"]["native_child_house_preview"])
        self.assertTrue(lineage["selected_matrilineal_option"])
        self.assertFalse(lineage["effective_matrilineal_if_accepted"])
        self.assertEqual(result["betrothal_break_terms"]["status"], "not_requested")
        self.assertEqual(result["query_status"], "available")
        self.assertNotIn("ally_character_id", driver.requests[0])

    def test_real_negative_legality_and_null_lineage_remain_readable(self):
        packet = wire("terms")
        driver = FamilyNativeWireDriver(packet)
        result = driver.query_family_obligations_private_v1(**request(packet))
        self.assertEqual(result["native_child_house_preview"], packet["result"]["native_child_house_preview"])
        self.assertFalse(result["native_child_house_preview"]["complete_can_send"])
        self.assertIsNone(result["native_child_house_preview"]["house_id"])
        self.assertIsNone(result["native_child_house_preview"]["dynasty_id"])

    def test_send_prestige_zero_keeps_distinct_stock_break_penalty(self):
        packet = wire("terms")
        driver = FamilyNativeWireDriver(packet)
        terms = driver.query_family_obligations_private_v1(**request(packet))["betrothal_break_terms"]
        self.assertEqual(terms, packet["result"]["betrothal_break_terms"])
        self.assertEqual(terms["native_send_costs_raw"][1], 0)
        self.assertGreater(terms["native_send_costs_raw"][0], 0)
        self.assertLess(terms["outcome_resource_penalty"]["stock_prestige_effect_raw"], 0)
        self.assertFalse(terms["outcome_resource_penalty"]["effects_complete"])

    def test_family_cli_defaults_to_off(self):
        self.assertFalse(parser().parse_args([]).private_family_obligations_query)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class FamilyObligationsMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_calls_actual_nonwar_provider_packets(self):
        from mcp import Client

        packet = wire("mailbox")
        driver = FamilyNativeWireDriver(packet)
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            name = "ck3_query_family_obligations_private_v1"
            self.assertTrue(tools[name].annotations.read_only_hint)
            self.assertNotIn("ally_character_id", tools[name].input_schema["properties"])
            called = await client.call_tool(name, request(packet))
            self.assertFalse(called.is_error)
            self.assertEqual(called.structured_content["native_child_house_preview"], packet["result"]["native_child_house_preview"])
            driver.packet = wire("terms")
            called = await client.call_tool(name, request(driver.packet))
            self.assertFalse(called.is_error)
            self.assertEqual(called.structured_content["betrothal_break_terms"], driver.packet["result"]["betrothal_break_terms"])
            self.assertEqual(len(driver.requests), 2)


if __name__ == "__main__":
    unittest.main()
