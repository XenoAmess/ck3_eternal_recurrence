"""One registered MCP compound for fresh preparation in the actual B scope."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from test_ordered_refill_besieging_assault_service import composed_row, MemoryRoute
from test_fixed_chunk0_preparation_service import preparation_row
from xar_autoplayer.bridge import army_prepare_ordered_besieging_refill_assembly
from xar_autoplayer.bridge import mcp_server


def outside_subject_packet(operand: dict | None, *, observed_fraction: int = 0,
                           target_ids_complete: bool = True) -> dict:
    packet = composed_row(0)
    # Only the actual B target is renamed; the subject DATA and scoped frame
    # continue to observe persistent50001/ArRg11001 with prepared148=0.
    family = packet["current_province_besieging_contributors_v1"]
    for occurrence in family["occurrences"]:
        for regiment in occurrence["regiments"]:
            regiment["army_regiment_id"] = 11002
            data = regiment["replenishment_records_v1"]
            data["army_regiment_id"] = 11002
            for record in data["records"]:
                record["persistent_regiment_id"] = 50002
                record["chunk_army_regiment_id"] = 11002
                record["persistent_prepared_replenishment_fraction_raw"] = observed_fraction
    inputs = packet["ordered_besieging_refill_inputs_v1"]
    inputs["target_army_regiment_ids"] = [11002]
    inputs["target_persistent_ids_complete"] = target_ids_complete
    if not target_ids_complete:
        inputs.update(status="partial", unavailable_reason="target_DATA_union_partial")
    for occurrence in inputs["persistent_occurrences"]:
        occurrence["persistent_regiment_id"] = 50002
    for persistent in inputs["persistent_regiments"]:
        persistent["persistent_regiment_id"] = 50002
        persistent["prepared_fraction_raw"] = observed_fraction
        for chunk in persistent["chunks"]:
            chunk["owner_persistent_regiment_id"] = 50002
            chunk["owner_resolved_full_id"] = 50002
            if chunk["army_regiment_id_raw"] == 11001:
                chunk["army_regiment_id_raw"] = 11002
            if chunk["associated_arrg_resolved_full_id"] == 11001:
                chunk["associated_arrg_resolved_full_id"] = 11002
            chunk["associated_army_raw_full_id"] = 30
            chunk["associated_army_resolved_full_id"] = 30
            chunk["associated_unit_raw_full_id"] = 31
            chunk["associated_unit_resolved_full_id"] = 31
    for refresh in inputs["refresh_occurrences"]:
        for target in refresh["regiments"]:
            target["raw_army_regiment_id"] = 11002
            target["army_regiment_id"] = 11002

    # A ready subject preparation cannot substitute for the absent/demanded
    # target50002 row, and does not select the general scoped entry mode.
    packet["fixed_chunk0_preparation_inputs_v1"] = {
        "source": "native_scoped_fixed_chunk0_preparation_inputs",
        "entry_kind": "current_frozen_context_preparation",
        "status": "available", "ready": True,
        "subject_army_id": 11, "subject_carmy_id": 12,
        "referenced_persistent_ids_complete": True, "unavailable_reason": None,
        "persistent_regiments": [preparation_row(
            50001, guard=0, magic=0, permission=False, fresh=10000)],
    }
    if operand is not None:
        rows = [operand]
        ready = target_ids_complete and all(row["ready"] for row in rows)
        packet["ordered_besieging_fixed_chunk0_preparation_inputs_v1"] = {
            "source": "native_ordered_besieging_fixed_chunk0_preparation_inputs",
            "entry_kind": "current_frozen_context_preparation",
            "scope_kind": "actual_ordered_besieging_target_physical_union",
            "source_scope_status": inputs["status"],
            "status": "available" if ready else "partial", "ready": ready,
            "subject_army_id": 11, "subject_carmy_id": 12, "province_id": 7,
            "target_persistent_ids_complete": target_ids_complete,
            "unavailable_reason": None if ready else "target_preparation_inputs_partial",
            "persistent_regiments": rows,
        }
    return packet


def empty_nonrefresh_packet() -> dict:
    packet = outside_subject_packet(preparation_row(
        50002, guard=0, magic=0, permission=False, fresh=10000))
    inputs = packet["ordered_besieging_refill_inputs_v1"]
    inputs["persistent_occurrences"] = []
    inputs["persistent_regiments"] = []
    inputs["refresh_occurrences"] = []
    preparation = packet["ordered_besieging_fixed_chunk0_preparation_inputs_v1"]
    preparation["persistent_regiments"] = []
    for occurrence in packet["current_province_besieging_contributors_v1"]["occurrences"]:
        for regiment in occurrence["regiments"]:
            regiment["replenishment_records_v1"] = None
    return packet


class FreshOrderedBPreparationMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_registered_fresh_B_scope_preparation_and_single_physical_consumer(self) -> None:
        outputs = {}
        previous_path = os.environ.get("XAR_FRESH_ORDERED_B_PREVIOUS_OUTPUT")
        previous_outputs = (json.loads(Path(previous_path).read_text(encoding="utf-8"))
                            if previous_path else {})
        service = MemoryRoute(composed_row(0))
        original_core = (
            army_prepare_ordered_besieging_refill_assembly
            .project_observed_prepared_ordered_physical_core_v1
        )
        input_basis = "same_capture_ordered_B_fixed_chunk0_conditional_preparation_ordered_occurrences"

        with patch.object(mcp_server, "GameplayBridgeService", return_value=service) as factory:
            driver = object()
            server = mcp_server.create_server(driver, profile_dir=None)
            factory.assert_called_once_with(driver)
            tools = {tool.name: tool for tool in await server.list_tools()}
            self.assertIn("ck3_query_army_strengths", tools)
            schema = tools["ck3_query_army_strengths"].input_schema
            mode = schema["properties"]["ordered_besieging_entry_mode"]
            self.assertEqual(mode["default"], "observed_prepared")
            self.assertEqual(mode["enum"], ["observed_prepared", "fixed_chunk0_prepare"])
            self.assertNotIn("ordered_besieging_entry_mode", schema.get("required", []))
            self.assertEqual(schema["properties"]["ordered_refill_entry_mode"]["default"],
                             "observed_prepared")
            if target := os.environ.get("XAR_FRESH_ORDERED_B_OUTPUT"):
                Path(target).with_name("registered-tool-schema.json").write_text(
                    json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

            async def query(name: str, packet: dict, *, fraction: int | None,
                            branch: str | None, row_ready: bool, preparation_ready: bool,
                            b: int | None, assault: int | None) -> dict:
                if name in previous_outputs:
                    cached = previous_outputs[name]
                    outputs[name] = cached
                    if target := os.environ.get("XAR_FRESH_ORDERED_B_OUTPUT"):
                        Path(target).write_text(
                            json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
                    return cached["same_input_conditional_ordered_refill_besieging_assault_v1"][0]
                before = deepcopy(packet)
                service.source = packet
                service.calls.clear()
                with patch.object(
                    army_prepare_ordered_besieging_refill_assembly,
                    "project_observed_prepared_ordered_physical_core_v1",
                    wraps=original_core,
                ) as core:
                    response = await server.call_tool("ck3_query_army_strengths", {
                        "army_ids": [11], "expected_revision": 42,
                        "ordered_besieging_entry_mode": "fixed_chunk0_prepare",
                    })
                    returned = response.structured_content
                    outputs[name] = returned
                    if target := os.environ.get("XAR_FRESH_ORDERED_B_OUTPUT"):
                        Path(target).write_text(
                            json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
                    self.assertFalse(response.is_error)
                    self.assertEqual(core.call_count, 1)
                    self.assertEqual(core.call_args.kwargs,
                                     {"prepared_input_basis": input_basis})
                    physical_inputs = core.call_args.args[0]
                    if branch is None:
                        self.assertEqual(physical_inputs["persistent_regiments"], [])
                        self.assertEqual(physical_inputs["persistent_occurrences"], [])
                    else:
                        self.assertEqual(physical_inputs["persistent_regiments"][0]
                                         ["persistent_regiment_id"], 50002)
                        self.assertEqual(physical_inputs["persistent_regiments"][0]
                                         ["prepared_fraction_raw"], fraction)

                self.assertEqual(packet, before)
                self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
                self.assertEqual(returned["status"], "available")
                self.assertEqual(returned["native_readiness"],
                                 {"current_strength": True, "full_monthly": False})
                self.assertEqual(returned["ordered_refill_entry_mode"], "observed_prepared")
                self.assertEqual(returned["ordered_besieging_entry_mode"], "fixed_chunk0_prepare")
                native = returned["army_strengths"][0]
                self.assertEqual(native["current_soldiers"], 160)
                self.assertEqual(native["maximum_soldiers"], 200)
                self.assertEqual(native["current_supply_change_monthly_raw"], 700000)
                for leaf in ("scoped_ordered_refill_inputs_v1",
                             "ordered_besieging_refill_inputs_v1",
                             "fixed_chunk0_preparation_inputs_v1",
                             "regiment_replenishment_records_v1"):
                    self.assertEqual(native[leaf], packet[leaf])
                self.assertEqual(native["ordered_besieging_fixed_chunk0_preparation_inputs_v1"],
                                 packet.get("ordered_besieging_fixed_chunk0_preparation_inputs_v1"))
                subject_data = native["regiment_replenishment_records_v1"][0]
                self.assertEqual(subject_data["army_regiment_id"], 11001)
                self.assertEqual([record["persistent_regiment_id"]
                                  for record in subject_data["records"]], [50001, 50001])
                self.assertEqual([record["persistent_prepared_replenishment_fraction_raw"]
                                  for record in subject_data["records"]], [0, 0])
                subject = returned["same_input_conditional_scoped_ordered_refill_current_v1"][0]
                self.assertEqual(subject["input_basis"], "same_capture_prepared148_ordered_occurrences")
                self.assertTrue(subject["conditional_raised_current_maximum_ready"])
                self.assertEqual(subject["conditional_current_soldiers"], 160)
                subject_preparation = returned["same_input_conditional_fixed_chunk0_preparation_v1"][0]
                self.assertTrue(subject_preparation["preparation_ready"])
                self.assertEqual(subject_preparation["persistent_regiments"][0]
                                 ["conditional_prepared_fraction_raw"], 10000)

                native_b = native["current_province_besieging_contributors_v1"]
                self.assertEqual(native_b["native_besieging_strength"], 640)
                self.assertEqual(native_b["native_assault_expected_loss"], 64)
                for observed, original in zip(native_b["occurrences"],
                        packet["current_province_besieging_contributors_v1"]["occurrences"], strict=True):
                    for regiment, source in zip(observed["regiments"], original["regiments"], strict=True):
                        self.assertEqual(regiment["army_regiment_id"], 11002)
                        self.assertEqual(regiment["current_soldiers"], 160)
                        self.assertEqual(regiment["replenishment_records_v1"],
                                         source["replenishment_records_v1"])

                result = returned["same_input_conditional_ordered_refill_besieging_assault_v1"][0]
                self.assertEqual(result["projection_kind"],
                                 "conditional_fixed_chunk0_prepare_ordered_besieging_assault")
                self.assertEqual(result["ordered_besieging_entry_mode"], "fixed_chunk0_prepare")
                self.assertEqual(result["input_basis"], input_basis)
                self.assertEqual(result["context_basis"],
                                 "held_nonphysical_native_army_unit_position_political_context")
                self.assertEqual(result["b_context_basis"], "held_nonphysical_B_context")
                self.assertEqual(result["preparation_context_basis"], "current_frozen_context_preparation")
                self.assertTrue(result["conditional_preparation_projected"])
                for flag in ("cache_write", "full_ordered_regular_refill", "actual_after",
                             "actual_replenishment", "actual_loss", "actual_effects",
                             "actual_post_stage_observed", "preparation_replayed",
                             "full_manager_replayed", "full_daily_assault_ready", "full_monthly_ready"):
                    self.assertFalse(result[flag])
                self.assertEqual(result["refill_ADDs_in_adapter"], 0)
                self.assertEqual(result["physical_core_invocations"], 1)
                self.assertEqual(result["native_besieging_strength"], 640)
                self.assertEqual(result["native_assault_expected_loss"], 64)
                self.assertEqual(result["conditional_besieging_strength_ready"], b is not None)
                self.assertEqual(result["conditional_assault_expected_loss_ready"], assault is not None)
                self.assertEqual(result["conditional_besieging_strength"], b)
                self.assertEqual(result["conditional_assault_expected_loss"], assault)
                preparation = returned["same_input_conditional_ordered_besieging_fixed_chunk0_preparation_v1"][0]
                self.assertEqual(preparation["preparation_ready"], preparation_ready)
                if branch is None:
                    self.assertEqual(result["preparation_join"], [])
                    self.assertEqual(preparation["persistent_regiments"], [])
                else:
                    self.assertEqual(len(result["preparation_join"]), 1)
                    joined = result["preparation_join"][0]
                    self.assertEqual(joined["persistent_regiment_id"], 50002)
                    self.assertEqual(joined["fixed_chunk_index"], 0)
                    self.assertEqual(joined["observed_prepared_fraction_raw"],
                                     packet["ordered_besieging_refill_inputs_v1"]
                                     ["persistent_regiments"][0]["prepared_fraction_raw"])
                    self.assertEqual(joined["conditional_prepared_fraction_raw"], fraction)
                    self.assertEqual(joined["preparation_ready"], row_ready)
                    self.assertEqual(joined["preparation_branch"], branch)
                    self.assertEqual(bool(joined["missing_inputs"]), not row_ready)
                    if preparation["persistent_regiments"]:
                        prepared = preparation["persistent_regiments"][0]
                        self.assertEqual(prepared["persistent_regiment_id"], 50002)
                        self.assertEqual(prepared["preparation_ready"], row_ready)
                        self.assertEqual(prepared["conditional_prepared_fraction_raw"], fraction)
                if b is None:
                    self.assertTrue(result["missing_inputs"])
                elif fraction is not None and fraction <= 0:
                    self.assertEqual([occurrence["writes"]
                                      for occurrence in result["physical_core"]["occurrences"]], [[], []])
                    self.assertEqual(result["final_physical_chunks"][0]["current_soldiers"], 80)
                    self.assertEqual(result["final_physical_chunks"][1]["current_soldiers"], 20)
                return result

            positive = await query("outside-subject-fresh-positive-observed-zero",
                outside_subject_packet(preparation_row(
                    50002, guard=0, magic=0, permission=False, fresh=10000)),
                fraction=10000, branch="ordinary_guard_bypass", row_ready=True,
                preparation_ready=True, b=800, assault=80)
            self.assertEqual([occurrence["persistent_regiment_id"]
                              for occurrence in positive["physical_core"]["occurrences"]], [50002, 50002])
            self.assertEqual([occurrence["stored_index"]
                              for occurrence in positive["physical_core"]["occurrences"]], [1, 3])
            self.assertEqual([occurrence["q_buffer"][0]
                              for occurrence in positive["physical_core"]["occurrences"]], [10, 10])
            self.assertEqual([occurrence["writes"][0]["after_current"]
                              for occurrence in positive["physical_core"]["occurrences"]], [90, 100])
            self.assertEqual([refresh["manager_stored_index"]
                              for refresh in positive["refresh_occurrences"]], [1, 3])
            self.assertEqual(len(positive["final_refreshed_regiments"]), 1)
            self.assertEqual(positive["final_refreshed_regiments"][0]["army_regiment_id"], 11002)
            self.assertEqual(positive["final_refreshed_regiments"][0]["current_soldiers"], 200)
            for refresh in positive["refresh_occurrences"]:
                for target in refresh["regiments"]:
                    self.assertEqual(target["army_regiment_id"], 11002)
                    self.assertEqual(len(target["refresh"]["record_contributions"]), 2)
            for occurrence in positive["besieging_occurrences"]:
                self.assertEqual([delta["delta_soldiers"] for delta in occurrence["deltas"]], [40, 40])

            zero_packet = outside_subject_packet(preparation_row(
                50002, guard=0, magic=0, permission=False, fresh=0), observed_fraction=10000)
            zero_inputs = zero_packet["ordered_besieging_refill_inputs_v1"]
            zero_inputs.update(status="partial", unavailable_reason="physical_context_partial")
            zero_inputs["persistent_regiments"][0]["chunks"][0]["origin_province_788_raw"] = None
            zero_preparation = zero_packet["ordered_besieging_fixed_chunk0_preparation_inputs_v1"]
            zero_preparation["source_scope_status"] = "partial"
            zero = await query("legal-zero-complete-target-IDs-unused-partial-physical-context", zero_packet,
                fraction=0, branch="ordinary_guard_bypass", row_ready=True,
                preparation_ready=True, b=640, assault=64)
            self.assertTrue(zero_inputs["target_persistent_ids_complete"])
            self.assertTrue(zero["ordered_physical_ready"])
            await query("permission-true-negative-no-ADD", outside_subject_packet(preparation_row(
                    50002, guard=0, magic=0x4744624F, permission=True, fresh=-3456),
                    observed_fraction=10000),
                fraction=-3456, branch="fixed_chunk0_permission_true", row_ready=True,
                preparation_ready=True, b=640, assault=64)
            missing = await query("missing-target-permission-no-cache-or-subject-substitution",
                outside_subject_packet(preparation_row(
                    50002, guard=0, magic=0x4744624F, permission=None, fresh=10000),
                    observed_fraction=10000),
                fraction=None, branch="unknown", row_ready=False,
                preparation_ready=False, b=None, assault=None)
            self.assertEqual(missing["preparation_join"][0]["missing_inputs"],
                             ["native_fixed_chunk0_can_replenish"])
            self.assertFalse(missing["ordered_physical_ready"])
            await query("known-permission-false-unused-fresh", outside_subject_packet(preparation_row(
                    50002, guard=0, magic=0x4744624F, permission=False, fresh=None),
                    observed_fraction=10000),
                fraction=0, branch="fixed_chunk0_permission_false", row_ready=True,
                preparation_ready=True, b=640, assault=64)
            incomplete_packet = outside_subject_packet(preparation_row(
                50002, guard=0, magic=0x4744624F, permission=True, fresh=10000),
                target_ids_complete=False)
            incomplete_packet["ordered_besieging_refill_inputs_v1"].update(
                status="partial", unavailable_reason="target_DATA_header_partial")
            for occurrence in incomplete_packet["current_province_besieging_contributors_v1"]["occurrences"]:
                for target in occurrence["regiments"]:
                    data = target["replenishment_records_v1"]
                    data.update(
                        native_data_record_count=3, status="partial", ready=False,
                        unavailable_reason="target_DATA_header_partial")
                    data["records"].append({
                        "status": "unavailable", "unavailable_reason": "target_DATA_raw_persistent_id_unavailable",
                        "record_index": 2, "persistent_regiment_id": -1, "chunk_index": 0,
                        "chunk_army_regiment_id": None, "current_soldiers": None,
                        "maximum_soldiers": None, "effective_current_soldiers": None,
                        "state_raw": None, "native_can_replenish": None,
                        "native_chunk_can_replenish": None,
                        "persistent_monthly_replenishment_fraction_raw": None,
                        "persistent_monthly_replenishment_fraction_scale": 100000,
                        "persistent_prepared_replenishment_fraction_raw": None,
                        "persistent_prepared_replenishment_fraction_scale": 100000,
                    })
            incomplete = await query("true-known-scalars-incomplete-target-DATA-header",
                incomplete_packet,
                fraction=10000, branch="fixed_chunk0_permission_true", row_ready=True,
                preparation_ready=False, b=None, assault=None)
            self.assertTrue(incomplete["ordered_physical_ready"])
            self.assertEqual([occurrence["writes"][0]["after_current"]
                              for occurrence in incomplete["physical_core"]["occurrences"]], [90, 100])
            absent = await query("absent-target-fresh-leaf-no-cache-or-subject-substitution",
                outside_subject_packet(None, observed_fraction=10000),
                fraction=None, branch="unavailable", row_ready=False,
                preparation_ready=False, b=None, assault=None)
            self.assertFalse(absent["ordered_physical_ready"])
            empty = await query("complete-empty-nonrefresh-without-target-DATA",
                empty_nonrefresh_packet(), fraction=None, branch=None, row_ready=True,
                preparation_ready=True, b=640, assault=64)
            self.assertTrue(empty["ordered_physical_ready"])
            self.assertEqual(empty["physical_core"]["occurrences"], [])
            self.assertEqual(empty["final_physical_chunks"], [])
            self.assertEqual(empty["refresh_occurrences"], [])


if __name__ == "__main__":
    unittest.main()
