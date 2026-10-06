"""ONE FIRST compiled native wire -> strict -> full service -> registered MCP.

The native producer emits exactly five fresh complete ArmyStrength rows. The
MCP SDK, registered callable, GameplayBridgeService, normalizer and current-day
projection are real. Only the driver snapshot/step envelope/world are synthetic.
Authoring this test does not provide fixture/live qualification.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

_PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.bridge.war_contract import (
    QUERY_ARMY_STRENGTHS_STEP,
    army_strength_query_status,
    normalize_army_strengths,
)

_LEAF = "current_disembark_penalty_v1"
_SOURCE = "native_current_disembark_penalty_days_12003"
_SAMPLE_NAMES = ("zero", "negative", "nonstock", "invalidArmy", "typeUnavailable")
_EXPECTED_DAYS = {"zero": 0, "negative": -1, "nonstock": 34}
_REVISION = 42
_NATIVE_REVISION = 7
_DATE_RAW = 10000


class _MemoryDriver:
    """Synthetic backend envelopes; no service/normalizer/projection override."""

    def __init__(self, row: dict[str, object]) -> None:
        self.row = row
        self.calls: list[tuple[str, int | None]] = []

    def take_snapshot(self) -> dict[str, object]:
        return {
            "paused": True,
            "revision": _REVISION,
            "native_revision": _NATIVE_REVISION,
            "date_raw": _DATE_RAW,
            "snapshot_id": "synthetic-current-disembark-FIRST-frame",
            "backend_id": "pure-memory-fixture",
            "player_armies": [{"army_id": self.row["army_id"]}],
            "active_wars": [],
            "diagnostics": {
                "hello": {
                    "game_version": CK3_12003.game_version,
                    "executable_sha256": CK3_12003.executable_sha256,
                }
            },
        }

    def capabilities(self) -> dict[str, object]:
        return {"action_steps": [QUERY_ARMY_STRENGTHS_STEP]}

    def execute_step(
        self, step: str, *, expected_revision: int | None = None,
    ) -> dict[str, object]:
        if step != QUERY_ARMY_STRENGTHS_STEP or expected_revision != _REVISION:
            raise AssertionError("The compound permits only its current army read")
        self.calls.append((step, expected_revision))
        return {
            "step": step,
            "accepted": True,
            "status": "available" if self.row["status"] == "available" else "partial",
            "query_sequence": 1,
            "army_strengths": [deepcopy(self.row)],
        }


class CurrentDisembarkPenaltyMcpCompoundTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_native_whole_wire_through_strict_full_service_registered_mcp(self) -> None:
        native_path = Path(os.environ["XAR_CURRENT_DISEMBARK_NATIVE_WIRE"])
        native_bytes = native_path.read_bytes()
        wire = json.loads(native_bytes.decode("utf-8-sig"))
        self.assertEqual(set(wire), {"schema_version", "samples"})
        self.assertIs(type(wire["schema_version"]), int)
        self.assertEqual(wire["schema_version"], 1)
        samples = wire["samples"]
        self.assertEqual(set(samples), set(_SAMPLE_NAMES))
        self.assertEqual(len(samples), 5)
        original_wire = deepcopy(wire)

        driver = _MemoryDriver(samples["zero"])
        # Actual SDK registration constructs the actual typed service. No SDK
        # stub, service factory patch or query/normalizer/projection patch is used.
        server = create_server(driver, profile_dir=None)
        tools = {tool.name: tool for tool in await server.list_tools()}
        self.assertIn("ck3_query_army_strengths", tools)
        schema = tools["ck3_query_army_strengths"].input_schema
        self.assertIn("army_ids", schema["properties"])
        self.assertIn("expected_revision", schema["properties"])
        self.assertIn("army_ids", schema.get("required", []))
        outputs: dict[str, object] = {}
        compatibility_outputs: dict[str, object] = {}

        async def query(name: str, raw_row: dict[str, object]) -> dict[str, object]:
            before = deepcopy(raw_row)
            self.assertEqual(raw_row["scope_role"], "player")
            self.assertEqual(raw_row["war_ids"], [])
            scope = [{
                "army_id": raw_row["army_id"],
                "scope_role": raw_row["scope_role"],
                "war_ids": raw_row["war_ids"],
            }]
            # Keep the native-produced row untouched for both independent strict
            # admission and the real service's own strict admission.
            strict = normalize_army_strengths([raw_row], expected_scope=scope)
            self.assertEqual(raw_row, before)
            driver.row = raw_row
            driver.calls.clear()
            response = await server.call_tool("ck3_query_army_strengths", {
                "army_ids": [raw_row["army_id"]], "expected_revision": _REVISION,
            })
            self.assertFalse(response.is_error, f"{name}: {response}")
            result = response.structured_content
            self.assertIsInstance(result, dict)
            self.assertEqual(driver.calls, [(QUERY_ARMY_STRENGTHS_STEP, _REVISION)])
            self.assertEqual(raw_row, before)
            self.assertEqual(result["status"], army_strength_query_status(strict))
            self.assertEqual(result["scope_status"], army_strength_query_status(strict))
            self.assertEqual(result["army_ids"], [raw_row["army_id"]])
            self.assertEqual(result["scope_army_ids"], [raw_row["army_id"]])
            returned_row = result["army_strengths"][0]
            # Service may add its established per-row pure projections; every
            # strict native field and aggregate must retain the original value.
            for key, value in strict[0].items():
                self.assertEqual(returned_row[key], value, f"{name}: {key}")
            if _LEAF in raw_row:
                self.assertEqual(strict[0][_LEAF], raw_row[_LEAF])
                self.assertEqual(returned_row[_LEAF], raw_row[_LEAF])
            else:
                self.assertNotIn(_LEAF, strict[0])
                self.assertNotIn(_LEAF, returned_row)

            projected = result[_LEAF][0]
            self.assertEqual(projected["army_id"], raw_row["army_id"])
            projection = projected["projection"]
            self.assertEqual(projection["observed_current_disembark_penalty"], raw_row.get(_LEAF))
            self.assertFalse(projection["future_route_landing_days_ready"])
            self.assertNotIn("active", projection)
            provenance = projection["source_provenance"]
            self.assertEqual(provenance["snapshot_id"], "synthetic-current-disembark-FIRST-frame")
            self.assertEqual(provenance["revision"], _REVISION)
            self.assertEqual(provenance["native_revision"], _NATIVE_REVISION)
            self.assertEqual(provenance["date_raw"], _DATE_RAW)
            self.assertEqual(provenance["game_version"], CK3_12003.game_version)
            self.assertEqual(provenance["executable_sha256"], CK3_12003.executable_sha256)
            return result

        for name in _SAMPLE_NAMES:
            row = samples[name]
            returned = await query(name, row)
            outputs[name] = returned
            projection = returned[_LEAF][0]["projection"]
            if row["status"] == "available":
                self.assertEqual((row["native_carmy_id"], row["current_soldiers"],
                                  row["maximum_soldiers"], row["ai_base_power_raw"]),
                                 (0x34000002, 20, 40, 4000000))
            if name in _EXPECTED_DAYS:
                self.assertEqual(row["status"], "available")
                leaf = row[_LEAF]
                self.assertEqual(set(leaf), {
                    "schema_version", "source", "status", "remaining_days", "unavailable_reason",
                })
                self.assertEqual(leaf["source"], _SOURCE)
                self.assertEqual(leaf["status"], "available")
                self.assertIs(type(leaf["remaining_days"]), int)
                self.assertEqual(leaf["remaining_days"], _EXPECTED_DAYS[name])
                self.assertIsNone(leaf["unavailable_reason"])
                self.assertTrue(projection["current_disembark_days_ready"])
                self.assertEqual(projection["remaining_days"], _EXPECTED_DAYS[name])
                self.assertIsNone(projection["unavailable_reason"])
            elif name == "invalidArmy":
                self.assertEqual(row["status"], "unavailable")
                self.assertIsNone(row["native_carmy_id"])
                self.assertEqual(row["unavailable_reason"], "native_carmy_not_found")
                self.assertNotIn(_LEAF, row)
                self.assertEqual(returned["status"], "partial")
                self.assertFalse(projection["current_disembark_days_ready"])
                self.assertIsNone(projection["remaining_days"])
                self.assertEqual(projection["unavailable_reason"], "current_disembark_penalty_not_published")
            else:
                self.assertEqual(row["status"], "available")
                leaf = row[_LEAF]
                self.assertEqual(leaf["status"], "unavailable")
                self.assertIsNone(leaf["remaining_days"])
                self.assertEqual(leaf["unavailable_reason"], "disembark_getter_not_bound")
                self.assertEqual(returned["status"], "available")
                self.assertFalse(projection["current_disembark_days_ready"])
                self.assertIsNone(projection["remaining_days"])
                self.assertEqual(projection["unavailable_reason"], "disembark_getter_not_bound")

        # A compatibility derivation from this new native row, not an old case
        # replay or a sixth native producer sample. Only the optional key differs.
        old_packet = deepcopy(samples["zero"])
        del old_packet[_LEAF]
        old_result = await query("old-packet-leaf-omission-derived", old_packet)
        old_projection = old_result[_LEAF][0]["projection"]
        self.assertEqual(old_result["status"], "available")
        self.assertNotIn(_LEAF, old_result["army_strengths"][0])
        self.assertFalse(old_projection["current_disembark_days_ready"])
        self.assertIsNone(old_projection["remaining_days"])
        self.assertEqual(old_projection["unavailable_reason"], "current_disembark_penalty_not_published")
        compatibility_outputs["old-packet-leaf-omission-derived"] = old_result
        self.assertEqual(wire, original_wire)
        self.assertEqual(native_path.read_bytes(), native_bytes)

        if target := os.environ.get("XAR_CURRENT_DISEMBARK_CASE_OUTPUT"):
            output = Path(target)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({
                "outcome": "GREEN",
                "qualification": "one fresh compiled whole-native wire/strict/actual typed service/actual SDK registered MCP compound; world and step envelopes synthetic",
                "actual_compound_cases": 1,
                "actual_new_native_samples": 5,
                "consumer_only_compatibility_derivations": 1,
                "actual_registered_mcp_calls": 6,
                "native_wire_path": str(native_path),
                "registered_tool_input_schema": schema,
                "outputs": outputs,
                "compatibility_outputs": compatibility_outputs,
                "live_queries": 0,
                "normal_days_added": 0,
                "saved_days_added": 0,
            }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
