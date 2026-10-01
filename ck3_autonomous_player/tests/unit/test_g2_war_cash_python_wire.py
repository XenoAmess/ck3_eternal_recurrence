"""Actual native cash and fees serializer outputs through the current MCP route."""

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
from xar_autoplayer.bridge.war_cash_private_transport_v1 import CURRENT_STEP, TERMINATION_PREFIX


def wire(name):
    return json.loads((FIXTURES / f"ck3_12002_war_cash_{name}.json").read_text(encoding="utf-8"))


class WarCashNativeWireDriver:
    command_timeout_seconds = 1.0
    allow_private_war_cash_query = True
    query_war_cash_current_resources_private_v1 = NativeHeadlessGameplayDriver.query_war_cash_current_resources_private_v1
    query_war_cash_termination_send_costs_private_v1 = NativeHeadlessGameplayDriver.query_war_cash_termination_send_costs_private_v1

    def __init__(self, value):
        self.value = value
        self.endpoint = self.state = self
        self.requests = []
        self.snapshot = {"paused": True, "map_ready": True,
                         "revision": value["snapshot_revision"] + 1,
                         "native_revision": value["snapshot_revision"],
                         "snapshot_id": "native:" + str(value["snapshot_revision"]),
                         "date_raw": value["date_raw"],
                         "played_character": {"character_id": value["played_character_id"], "alive": True},
                         "diagnostics": {"hello": {
                             "expected_ck3_version": CK3_12002.game_version,
                             "expected_ck3_sha256": CK3_12002.executable_sha256}}}

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        request = self.requests[-1]
        key = "war_cash_current_resources" if request["step"] == CURRENT_STEP else "war_cash_termination_send_costs"
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": {"step": request["step"], "accepted": True,
                           "status": self.value["status"], "private_build": True,
                           "read_only": True, "advertised": False,
                           key: deepcopy(self.value), "backend_id": "native-headless"}}


class WarCashPythonWireTests(unittest.TestCase):
    def test_actual_cpp_serializer_bytes(self):
        manifest = json.loads((FIXTURES / "ck3_12002_war_cash_python_provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["local_ck3_operations"], [])
        for row in manifest["fixtures"]:
            self.assertEqual(hashlib.sha256((FIXTURES / row["file"]).read_bytes()).hexdigest(), row["sha256"])

    def test_native_current_resource_rows_round_trip_once_across_all_wars(self):
        value = wire("current-resources-normal")
        driver = WarCashNativeWireDriver(value)
        result = driver.query_war_cash_current_resources_private_v1(expected_revision=72)
        self.assertEqual(result["military_expenses"], value["military_expenses"])
        self.assertEqual(result["current_treasury"], value["current_treasury"])
        self.assertEqual(result["player_monthly_net_income"], value["player_monthly_net_income"])
        self.assertEqual(result["military_expenses"]["current"]["source_scope"], "actor_owned_military_once_across_all_wars")
        self.assertFalse(result["military_expenses"]["current"]["future_war_cost_upper_ready"])
        self.assertEqual(len(driver.requests), 1)

    def test_real_zero_rate_is_distinct_from_partial_and_unavailable(self):
        for name in ("current-zero-normal", "partial-resources-normal", "drift-unavailable-normal"):
            value = wire(name)
            driver = WarCashNativeWireDriver(value)
            result = driver.query_war_cash_current_resources_private_v1(expected_revision=72)
            self.assertEqual(result["status"], value["status"])
            self.assertEqual(result["military_expenses"], value["military_expenses"])
            self.assertEqual(result["readiness"], value["readiness"])
            self.assertFalse(result["formal_action_ready"])

    def test_actual_zero_send_cost_does_not_become_total_immediate_cost(self):
        value = wire("termination-send-zero-normal")
        driver = WarCashNativeWireDriver(value)
        result = driver.query_war_cash_termination_send_costs_private_v1(expected_revision=72, war_id=value["war_id"], outcome=value["outcome"])
        self.assertEqual(result["generic_send_costs"], value["generic_send_costs"])
        self.assertIsNone(result["total_immediate_gold_cost_raw"])
        self.assertFalse(result["readiness"]["total_immediate_gold_cost_ready"])
        self.assertEqual(driver.requests[0]["step"], f'{TERMINATION_PREFIX}{value["war_id"]}-{value["outcome"]}')

    def test_actual_fee_read_failure_preserves_unavailable_reason(self):
        value = wire("termination-send-unavailable-normal")
        driver = WarCashNativeWireDriver(value)
        result = driver.query_war_cash_termination_send_costs_private_v1(expected_revision=72, war_id=value["war_id"], outcome=value["outcome"])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], value["unavailable_reason"])

    def test_new_observation_cli_flags_default_off(self):
        args = parser().parse_args([])
        self.assertFalse(args.private_war_cash_queries)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class WarCashMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_readonly_sdk_returns_actual_resource_and_fee_json(self):
        from mcp import Client

        driver = WarCashNativeWireDriver(wire("current-resources-normal"))
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            for name in ("ck3_query_war_cash_current_resources_private_v1", "ck3_query_war_cash_termination_send_costs_private_v1"):
                self.assertTrue(tools[name].annotations.read_only_hint)
            current = await client.call_tool("ck3_query_war_cash_current_resources_private_v1", {"expected_revision": 72})
            self.assertFalse(current.is_error)
            self.assertEqual(current.structured_content["military_expenses"], driver.value["military_expenses"])
            driver.value = wire("termination-send-zero-normal")
            fees = await client.call_tool("ck3_query_war_cash_termination_send_costs_private_v1", {"expected_revision": 72, "war_id": driver.value["war_id"], "outcome": driver.value["outcome"]})
            self.assertFalse(fees.is_error)
            self.assertIsNone(fees.structured_content["total_immediate_gold_cost_raw"])
            self.assertEqual(len(driver.requests), 2)


if __name__ == "__main__":
    unittest.main()
