"""One registered MCP compound for explicit preparation and ordered refill."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from test_scoped_ordered_refill_service import MemoryRoute, row
from test_fixed_chunk0_preparation_service import preparation_row
from xar_autoplayer.bridge import army_prepare_scoped_ordered_refill_assembly
from xar_autoplayer.bridge import mcp_server


def prepared_packet(observed_fraction: int, operand: dict | None) -> dict:
    packet = row(fraction=observed_fraction)
    if operand is not None:
        complete = operand["ready"]
        packet["fixed_chunk0_preparation_inputs_v1"] = {
            "source": "native_scoped_fixed_chunk0_preparation_inputs",
            "entry_kind": "current_frozen_context_preparation",
            "status": "available" if complete else "partial", "ready": complete,
            "subject_army_id": 11, "subject_carmy_id": 12,
            "referenced_persistent_ids_complete": True,
            "unavailable_reason": None if complete else "persistent_preparation_operands_partial",
            "persistent_regiments": [operand],
        }
    return packet


class ExplicitPreparationScopedCoreMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_explicit_preparation_uses_one_ordered_core_without_observed_fallback(self) -> None:
        outputs = {}
        service = MemoryRoute(row())
        original_core = (
            army_prepare_scoped_ordered_refill_assembly
            .project_observed_prepared_ordered_physical_core_v1
        )
        input_basis = "same_capture_fixed_chunk0_conditional_preparation_ordered_occurrences"

        with patch.object(mcp_server, "GameplayBridgeService", return_value=service) as factory:
            driver = object()
            server = mcp_server.create_server(driver, profile_dir=None)
            factory.assert_called_once_with(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            self.assertIn("ck3_query_army_strengths", tools)
            schema = tools["ck3_query_army_strengths"].input_schema
            mode_schema = schema["properties"]["ordered_refill_entry_mode"]
            self.assertEqual(mode_schema["default"], "observed_prepared")
            self.assertEqual(mode_schema["enum"], ["observed_prepared", "fixed_chunk0_prepare"])
            self.assertNotIn("ordered_refill_entry_mode", schema.get("required", []))
            if target := os.environ.get("XAR_PREPARE_SCOPED_CORE_OUTPUT"):
                Path(target).with_name("registered-tool-schema.json").write_text(
                    json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

            async def query(name: str, packet: dict, *, fraction: int | None,
                            branch: str, ready: bool) -> dict:
                before = deepcopy(packet)
                service.source = packet
                service.calls.clear()
                with patch.object(
                    army_prepare_scoped_ordered_refill_assembly,
                    "project_observed_prepared_ordered_physical_core_v1",
                    wraps=original_core,
                ) as core:
                    response = await server.call_tool("ck3_query_army_strengths", {
                        "army_ids": [11], "expected_revision": 42,
                        "ordered_refill_entry_mode": "fixed_chunk0_prepare",
                    })
                    result = response.structured_content
                    outputs[name] = result
                    if target := os.environ.get("XAR_PREPARE_SCOPED_CORE_OUTPUT"):
                        Path(target).write_text(
                            json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
                    self.assertFalse(response.is_error)
                    self.assertEqual(core.call_count, 1)
                    self.assertEqual(core.call_args.kwargs,
                                     {"prepared_input_basis": input_basis})
                    self.assertEqual(core.call_args.args[0]["persistent_regiments"][0]
                                     ["prepared_fraction_raw"], fraction)

                self.assertEqual(packet, before)
                self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
                self.assertEqual(result["status"], "available")
                self.assertEqual(result["ordered_refill_entry_mode"], "fixed_chunk0_prepare")
                self.assertEqual(result["native_readiness"],
                                 {"current_strength": True, "full_monthly": False})
                native = result["army_strengths"][0]
                self.assertEqual(native["current_soldiers"], 160)
                self.assertEqual(native["maximum_soldiers"], 200)
                self.assertEqual(native["scoped_ordered_refill_inputs_v1"],
                                 packet["scoped_ordered_refill_inputs_v1"])
                self.assertEqual(native["regiment_replenishment_records_v1"],
                                 packet["regiment_replenishment_records_v1"])
                self.assertEqual(native["fixed_chunk0_preparation_inputs_v1"],
                                 packet.get("fixed_chunk0_preparation_inputs_v1"))
                observed = packet["scoped_ordered_refill_inputs_v1"]["persistent_regiments"][0]
                self.assertEqual(native["scoped_ordered_refill_inputs_v1"]
                                 ["persistent_regiments"][0]["prepared_fraction_raw"],
                                 observed["prepared_fraction_raw"])
                self.assertEqual([record["persistent_prepared_replenishment_fraction_raw"]
                                  for record in native["regiment_replenishment_records_v1"][0]
                                  ["records"]], [observed["prepared_fraction_raw"]] * 2)

                projected = result["same_input_conditional_scoped_ordered_refill_current_v1"][0]
                self.assertEqual(projected["projection_kind"],
                                 "conditional_fixed_chunk0_prepare_scoped_ordered_core")
                self.assertEqual(projected["ordered_refill_entry_mode"], "fixed_chunk0_prepare")
                self.assertEqual(projected["input_basis"], input_basis)
                self.assertEqual(projected["context_basis"],
                                 "held_nonphysical_native_army_unit_position_political_context")
                self.assertEqual(projected["preparation_context_basis"],
                                 "current_frozen_context_preparation")
                self.assertTrue(projected["conditional_preparation_projected"])
                for flag in ("cache_write", "preparation_replayed", "actual_after",
                             "actual_post_stage_observed", "full_manager_replayed",
                             "full_monthly_ready", "full_ordered_regular_refill"):
                    self.assertFalse(projected[flag])
                self.assertEqual(projected["ordered_core_ready"], ready)
                self.assertEqual(projected["conditional_raised_current_maximum_ready"], ready)
                self.assertEqual(len(projected["preparation_join"]), 1)
                joined = projected["preparation_join"][0]
                self.assertEqual(joined["persistent_regiment_id"], 50001)
                self.assertEqual(joined["fixed_chunk_index"], 0)
                self.assertEqual(joined["observed_prepared_fraction_raw"],
                                 observed["prepared_fraction_raw"])
                self.assertEqual(joined["conditional_prepared_fraction_raw"], fraction)
                self.assertEqual(joined["preparation_ready"], ready)
                self.assertEqual(joined["preparation_branch"], branch)
                self.assertEqual(bool(joined["missing_inputs"]), not ready)
                independent = result["same_input_conditional_fixed_chunk0_preparation_v1"][0]
                self.assertEqual(independent["input_basis"], "current_frozen_context_preparation")
                self.assertEqual(independent["preparation_ready"], ready)
                if independent["persistent_regiments"]:
                    self.assertEqual(independent["persistent_regiments"][0]
                                     ["conditional_prepared_fraction_raw"], fraction)
                if not ready:
                    self.assertIsNone(projected["conditional_current_soldiers"])
                    self.assertIsNone(projected["conditional_maximum_soldiers"])
                    self.assertTrue(projected["missing_inputs"])
                elif fraction is not None and fraction <= 0:
                    self.assertEqual(projected["conditional_current_soldiers"], 160)
                    self.assertEqual(projected["conditional_maximum_soldiers"], 200)
                    self.assertEqual([occurrence["writes"]
                                      for occurrence in projected["occurrences"]], [[], []])
                    self.assertEqual(projected["physical_chunks"][0]["current_soldiers"], 80)
                    self.assertEqual(projected["physical_chunks"][1]["current_soldiers"], 20)
                return projected

            positive = await query("fresh-positive-observed-zero", prepared_packet(0,
                preparation_row(50001, guard=0, magic=0, permission=False, fresh=10000)),
                fraction=10000, branch="ordinary_guard_bypass", ready=True)
            self.assertEqual(positive["conditional_current_soldiers"], 200)
            self.assertEqual(positive["conditional_maximum_soldiers"], 200)
            self.assertEqual([occurrence["persistent_regiment_id"]
                              for occurrence in positive["occurrences"]], [50001, 50001])
            self.assertEqual([occurrence["stored_index"]
                              for occurrence in positive["occurrences"]], [1, 3])
            self.assertEqual([occurrence["q_buffer"][0]
                              for occurrence in positive["occurrences"]], [10, 10])
            self.assertEqual([occurrence["writes"][0]["after_current"]
                              for occurrence in positive["occurrences"]], [90, 100])
            self.assertEqual([refresh["manager_stored_index"]
                              for refresh in positive["refresh_occurrences"]], [1, 3])
            for refresh in positive["refresh_occurrences"]:
                self.assertEqual(len(refresh["regiments"][0]["record_contributions"]), 2)

            await query("legal-fresh-zero-overrides-observed-positive", prepared_packet(10000,
                preparation_row(50001, guard=0, magic=0, permission=False, fresh=0)),
                fraction=0, branch="ordinary_guard_bypass", ready=True)
            await query("permission-true-negative-retained", prepared_packet(10000,
                preparation_row(50001, guard=0, magic=0x4744624F, permission=True, fresh=-3456)),
                fraction=-3456, branch="fixed_chunk0_permission_true", ready=True)
            missing = await query("missing-fixed-permission-cannot-borrow-observed-positive",
                prepared_packet(10000, preparation_row(
                    50001, guard=0, magic=0x4744624F, permission=None, fresh=10000)),
                fraction=None, branch="unknown", ready=False)
            self.assertEqual(missing["preparation_join"][0]["missing_inputs"],
                             ["native_fixed_chunk0_can_replenish"])
            await query("known-permission-false-unused-fresh", prepared_packet(10000,
                preparation_row(50001, guard=0, magic=0x4744624F, permission=False, fresh=None)),
                fraction=0, branch="fixed_chunk0_permission_false", ready=True)
            absent = await query("absent-preparation-cannot-borrow-observed-positive",
                prepared_packet(10000, None), fraction=None, branch="unavailable", ready=False)
            self.assertEqual(absent["preparation_join"][0]["missing_inputs"],
                             ["fixed_chunk0_preparation_inputs_v1:persistent_row"])


if __name__ == "__main__":
    unittest.main()
