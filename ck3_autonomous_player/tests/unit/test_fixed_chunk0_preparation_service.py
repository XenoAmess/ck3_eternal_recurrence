"""One production route compound for optional fixed physical chunk0 preparation."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from test_selected_refill_monthly_assembly_service import assembly_packet, MemoryRoute


def preparation_row(identity: int, *, guard: int | None, magic: int | None,
                    permission: bool | None, fresh: int | None) -> dict:
    complete = all(value is not None for value in (guard, magic, permission, fresh))
    return {
        "persistent_regiment_id": identity, "fixed_chunk_index": 0,
        "status": "available" if complete else "partial", "ready": complete,
        "unavailable_reason": None if complete else "preparation_operands_partial",
        "containing_guard_138_raw": guard, "containing_definition_magic_38": magic,
        "native_fixed_chunk0_can_replenish": permission,
        "fresh_fraction_raw": fresh, "fraction_scale": 100000,
    }


def preparation_packet(rows: list[dict] | None = None) -> dict:
    packet = assembly_packet()
    if rows is None:
        rows = [
            preparation_row(50001, guard=0, magic=0, permission=False, fresh=10000),
            preparation_row(50002, guard=0, magic=0x4744624F, permission=False, fresh=None),
        ]
    complete = all(row["ready"] for row in rows)
    packet["fixed_chunk0_preparation_inputs_v1"] = {
        "source": "native_scoped_fixed_chunk0_preparation_inputs",
        "entry_kind": "current_frozen_context_preparation",
        "status": "available" if complete else "partial", "ready": complete,
        "subject_army_id": 11, "subject_carmy_id": 12,
        "referenced_persistent_ids_complete": True,
        "unavailable_reason": None if complete else "persistent_preparation_operands_partial",
        "persistent_regiments": rows,
    }
    # Prepared148 is an observation of another stage, not the new fresh operand.
    # Keep every held alias consistent, while making arbitrary chunk permission
    # false so the ordinary guard bypass cannot accidentally depend on it.
    data_rows = list(packet["regiment_replenishment_records_v1"])
    for occurrence in packet["current_province_supply_contributors_v1"]["occurrences"]:
        data_rows.extend(regiment["replenishment_records_v1"]
                         for regiment in occurrence["regiments"]
                         if regiment["replenishment_records_v1"] is not None)
    for data in data_rows:
        for record in data["records"]:
            record["persistent_prepared_replenishment_fraction_raw"] = 0
            record["native_can_replenish"] = False
            record["native_chunk_can_replenish"] = False
    return packet


class FixedChunk0PreparationServiceTests(unittest.TestCase):
    def test_native_capture_short_circuits_and_independent_service_projection(self) -> None:
        outputs = {}

        def query(name: str, packet: dict) -> tuple[dict, dict]:
            before = deepcopy(packet)
            service = MemoryRoute(packet)
            result = service.query_army_strengths([11], expected_revision=42)
            outputs[name] = result
            if target := os.environ.get("XAR_FIXED_CHUNK0_PREPARATION_OUTPUT"):
                Path(target).write_text(
                    json.dumps(outputs, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
            self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(packet, before)
            self.assertEqual(result["status"], "available")
            self.assertEqual(result["scope_status"], "available")
            self.assertEqual(result["native_readiness"],
                             {"current_strength": True, "full_monthly": False})
            native = result["army_strengths"][0]
            self.assertEqual(native["current_soldiers"], packet["current_soldiers"])
            self.assertEqual(native["current_supply_raw"], packet["current_supply_raw"])
            self.assertEqual(native["regiment_replenishment_records_v1"],
                             packet["regiment_replenishment_records_v1"])
            self.assertEqual(native["fixed_chunk0_preparation_inputs_v1"],
                             packet.get("fixed_chunk0_preparation_inputs_v1"))
            value = result["same_input_conditional_fixed_chunk0_preparation_v1"][0]
            self.assertEqual((value["army_id"], value["native_carmy_id"]), (11, 12))
            self.assertEqual(value["input_basis"], "current_frozen_context_preparation")
            for projected in [value, *value["persistent_regiments"]]:
                for flag in ("actual_preparation", "cache_write", "full_ordered_regular_refill"):
                    self.assertFalse(projected[flag])
            return result, value

        result, value = query("ordinary-bypass-and-special-denial", preparation_packet())
        native = result["army_strengths"][0]["fixed_chunk0_preparation_inputs_v1"]
        self.assertEqual(native["status"], "partial")
        self.assertFalse(native["ready"])
        self.assertTrue(value["preparation_ready"])
        self.assertEqual(value["status"], "available")
        self.assertEqual(value["missing_inputs"], [])
        self.assertEqual([row["persistent_regiment_id"]
                          for row in value["persistent_regiments"]], [50001, 50002])
        ordinary, denied = value["persistent_regiments"]
        self.assertEqual(ordinary["conditional_prepared_fraction_raw"], 10000)
        self.assertEqual(ordinary["preparation_branch"], "ordinary_guard_bypass")
        self.assertFalse(ordinary["native_fixed_chunk0_can_replenish"])
        self.assertTrue(ordinary["preparation_ready"])
        observed = result["army_strengths"][0]["regiment_replenishment_records_v1"][0]["records"][0]
        self.assertEqual(observed["persistent_regiment_id"], 50001)
        self.assertEqual(observed["persistent_prepared_replenishment_fraction_raw"], 0)
        self.assertFalse(observed["native_chunk_can_replenish"])
        self.assertEqual(denied["conditional_prepared_fraction_raw"], 0)
        self.assertEqual(denied["preparation_branch"], "fixed_chunk0_permission_false")
        self.assertTrue(denied["preparation_ready"])
        self.assertFalse(denied["native_input_ready"])
        self.assertIsNone(denied["fresh_fraction_raw"])
        self.assertEqual(denied["missing_inputs"], [])

        negative = preparation_packet([
            preparation_row(50001, guard=0, magic=0x4744624F, permission=True, fresh=-3456),
            preparation_row(50002, guard=0, magic=0x4744624F, permission=False, fresh=None),
        ])
        _, value = query("permission-true-negative-fresh-retained", negative)
        self.assertTrue(value["preparation_ready"])
        row = value["persistent_regiments"][0]
        self.assertEqual(row["preparation_branch"], "fixed_chunk0_permission_true")
        self.assertEqual(row["conditional_prepared_fraction_raw"], -3456)
        self.assertTrue(row["preparation_ready"])

        missing = preparation_packet([
            preparation_row(50001, guard=0, magic=0x4744624F, permission=None, fresh=10000),
            preparation_row(50002, guard=0, magic=0x4744624F, permission=False, fresh=None),
        ])
        arbitrary = missing["regiment_replenishment_records_v1"][0]["records"][1]
        self.assertEqual(arbitrary["chunk_index"], 1)
        arbitrary["native_can_replenish"] = True
        for occurrence in missing["current_province_supply_contributors_v1"]["occurrences"]:
            for regiment in occurrence["regiments"]:
                data = regiment["replenishment_records_v1"]
                if data is not None:
                    for record in data["records"]:
                        if record["persistent_regiment_id"] == 50001 and record["chunk_index"] == 1:
                            record["native_can_replenish"] = True
        result, value = query("missing-fixed-permission-arbitrary-chunk1-is-insufficient", missing)
        self.assertTrue(result["army_strengths"][0]["regiment_replenishment_records_v1"][0]
                              ["records"][1]["native_can_replenish"])
        self.assertFalse(value["preparation_ready"])
        self.assertEqual(value["status"], "partial")
        row = value["persistent_regiments"][0]
        self.assertFalse(row["preparation_ready"])
        self.assertIsNone(row["conditional_prepared_fraction_raw"])
        self.assertEqual(row["missing_inputs"], ["native_fixed_chunk0_can_replenish"])
        self.assertTrue(value["persistent_regiments"][1]["preparation_ready"])
        self.assertEqual(value["persistent_regiments"][1]["conditional_prepared_fraction_raw"], 0)

        nonzero_guard = preparation_packet([
            preparation_row(50001, guard=7, magic=None, permission=False, fresh=None),
            preparation_row(50002, guard=0, magic=0x4744624F, permission=False, fresh=None),
        ])
        _, value = query("nonzero-guard-null-definition-unused-fresh", nonzero_guard)
        self.assertTrue(value["preparation_ready"])
        row = value["persistent_regiments"][0]
        self.assertFalse(row["native_input_ready"])
        self.assertIsNone(row["containing_definition_magic_38"])
        self.assertIsNone(row["fresh_fraction_raw"])
        self.assertEqual(row["preparation_branch"], "fixed_chunk0_permission_false")
        self.assertEqual(row["conditional_prepared_fraction_raw"], 0)
        self.assertEqual(row["missing_inputs"], [])

        legacy = preparation_packet()
        del legacy["fixed_chunk0_preparation_inputs_v1"]
        result, value = query("old-producer-optional-leaf-absent", legacy)
        self.assertIsNone(result["army_strengths"][0]["fixed_chunk0_preparation_inputs_v1"])
        self.assertFalse(value["preparation_ready"])
        self.assertEqual(value["status"], "unavailable")
        self.assertEqual(value["persistent_regiments"], [])
        self.assertEqual(value["missing_inputs"], [{
            "persistent_regiment_id": None, "inputs": ["fixed_chunk0_preparation_inputs_v1"]}])

        empty = preparation_packet([])
        empty.update(regiment_count=0, current_soldiers=0, maximum_soldiers=0,
                     regiment_strengths=[], regiment_replenishment_records_v1=[])
        del empty["current_province_supply_contributors_v1"]
        result, value = query("legitimate-empty-complete-DATA-scope", empty)
        self.assertTrue(result["army_strengths"][0]["fixed_chunk0_preparation_inputs_v1"]["ready"])
        self.assertTrue(value["referenced_persistent_ids_complete"])
        self.assertTrue(value["preparation_ready"])
        self.assertEqual(value["status"], "available")
        self.assertEqual(value["persistent_regiments"], [])
        self.assertEqual(value["missing_inputs"], [])


if __name__ == "__main__":
    unittest.main()
