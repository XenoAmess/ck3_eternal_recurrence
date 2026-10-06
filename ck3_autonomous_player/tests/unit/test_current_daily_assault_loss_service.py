"""One production-service compound for interleaved current assault losses."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_current_daily_assault_table_service import (
    _state, current_daily_assault_source, resolution, vector,
)
from test_post_refill_besieging_current_service import (
    fixed_data, occurrence, query_with_fake_driver, regiment,
)
from test_post_refill_land_rate_service_join import row

RA, RP, RB, RI, RC, RD = 11001, 11002, 11003, 11004, 11005, 11006

EXPECTED = {
    "sequential": {"budgets": [116, 25], "second_B": 252,
        "requests": [[58, 24], [17, 8]], "RA_current": 20,
        "RA_physical": 10, "RP_current": 50, "RB_current": 80,
        "army_counts": [166, 150], "unused_preferred": 34},
    "residual": {"original_overflow": 100, "residual_request": 50},
    "queue": [12, 12, 0x80000005, 12],
    "wrapped": {"preferred_denominator": 4, "product": -32,
        "first_request": -8, "second_B": 432, "second_budget": 43},
    "parent_zero": {"requests": [0, 100], "first_refresh": 200},
}


def target(identity: int, current: int, maximum: int, data: dict | None,
           *, skipped: bool = False, valid: bool = True) -> dict:
    return {**_state(True), "resolution": resolution(identity, kind="arrg"),
        "identity_valid": valid, "current_soldiers": current if valid else None,
        "maximum_soldiers": maximum if valid else None,
        "native_loss_writer_skipped": skipped if valid else None,
        "replenishment_records_v1": deepcopy(data) if valid else None}


def count_regiment(index: int, identity: int, current: int, maximum: int) -> dict:
    return {"native_index": index, "raw_full_id_u32": identity,
        "resolution": resolution(identity, kind="arrg"), "identity_valid": True,
        "current_soldiers": current, "maximum_soldiers": maximum}


def b_family(baseline: int = 580, *, ra_current: int = 200,
             rp_current: int = 50, all_rows: bool = True) -> dict:
    rows = [regiment(0, RA, ra_current, 300, fixed_data(RA, 51001, 100, 150)),
            regiment(1, RA, ra_current, 300, fixed_data(RA, 51001, 100, 150)),
            regiment(2, RP, rp_current, 100, fixed_data(RP, 51002, rp_current, 100))]
    if all_rows:
        # RC's cached count remains50 even when its captured DATA alias is
        # changed by RA. This caller never refreshes the uncalled RC cache.
        rows += [regiment(3, RB, 80, 120, fixed_data(RB, 51003, 80, 120)),
                 regiment(4, RC, 50, 150, fixed_data(RC, 51001, 100, 150))]
    contributor = occurrence(0, 22, baseline, rows)
    contributor["native_carmy_id"] = 17
    return {"status": "available", "unavailable_reason": "", "province_id": 1,
        "native_province_unit_count": 1, "native_besieging_strength": baseline,
        "contributors_ready": True, "native_assault_expected_loss": 58,
        "assault_context": {"status": "available", "unavailable_reason": "",
            "has_active_siege": True, "siege_id": 2, "breach_level_raw": 1,
            "casualty_percentage_count": 3, "casualty_percentage_raw": 1000000},
        "occurrences": [contributor]}


def assault_packet() -> dict:
    source = row()
    table = current_daily_assault_source()
    table["groups"] = table["groups"][:2]
    table["groups"][0].update(armies=vector([12]),
        arrgs=vector([RA, RA, RP, RI], arrg=True, currents=[200, 200, None, None],
                    kinds=[0, 0, 1, None], magics=[0x41725267] * 3 + [0]))
    table["groups"][1].update(armies=vector([12]),
        arrgs=vector([RB, RA], arrg=True, currents=[80, 200], kinds=[0, 0]))
    table["header"]["occupied_count_raw_i32"] = 2
    table["physical_controls"][8]["control_raw_u8"] = 0
    table["observed_occupied_group_count"] = 2
    source["current_daily_assault_table_v1"] = table
    ra_data = fixed_data(RA, 51001, 100, 150)
    ra_data["native_data_record_count"] = 2
    ra_data["records"].append(deepcopy(ra_data["records"][0]))
    ra_data["records"][1]["record_index"] = 1
    army_rows = [count_regiment(0, RA, 200, 300),
                 count_regiment(1, RP, 50, 100), count_regiment(2, RB, 80, 120)]
    groups = []
    for index, group in enumerate(table["groups"]):
        family = b_family()
        if index == 0:
            family["assault_context"].update(siege_id=-2147483647, breach_level_raw=2,
                                              casualty_percentage_raw=2000000)
        groups.append({**_state(True), "native_index": index,
            "physical_slot_i64": group["physical_slot_i64"],
            "native_current_expected_loss": 116 if index == 0 else 58,
            "province_magic_raw_u32": 0x50726F76, "besieging_inputs_v1": family,
            "army_counts": [{**_state(True), "native_index": 0,
                "raw_full_id_u32": 12, "resolution": resolution(12, kind="army"),
                "native_whole_current_soldiers": 330, "regiments": deepcopy(army_rows)}]})
    source["current_daily_assault_loss_inputs_v1"] = {
        "schema_version": 1, "source": "native_current_daily_assault_loss_inputs",
        "stage": "observed_current_daily_assault_table", **_state(True), "groups": groups,
        "target_regiments": [target(RA, 200, 300, ra_data),
            target(RP, 50, 100, fixed_data(RP, 51002, 50, 100)),
            target(RI, 0, 0, None, valid=False), target(RB, 80, 120, None, skipped=True)]}
    return source


def all_currents(source: dict, identity: int, current: int) -> None:
    leaf = source["current_daily_assault_loss_inputs_v1"]
    for value in leaf["target_regiments"]:
        if value["resolution"]["selected_full_id_u32"] == identity:
            value["current_soldiers"] = current
    for table_group in source["current_daily_assault_table_v1"]["groups"]:
        for value in table_group["arrgs"]["occurrences"]:
            if value["raw_full_id_u32"] == identity and value["denominator_included"]:
                value["current_raw_i32"] = current
    for group in leaf["groups"]:
        for army in group["army_counts"]:
            for value in army["regiments"]:
                if value["raw_full_id_u32"] == identity:
                    value["current_soldiers"] = current


class CurrentDailyAssaultLossServiceTests(unittest.TestCase):
    def test_current_groups_interleave_writer_refresh_budget_and_raw_queue(self):
        outputs = {}

        def query(name, source):
            before = deepcopy(source)
            returned, driver = query_with_fake_driver(source)
            self.assertEqual(source, before)
            self.assertEqual(driver.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(returned["status"], "available")
            self.assertEqual(returned["native_readiness"],
                             {"current_strength": True, "full_monthly": False})
            item = returned["same_input_current_daily_assault_loss_v1"][0]
            self.assertEqual(item["army_id"], 11)
            value = item["projection"]
            for key in ("actual_loss", "actual_effects", "actual_daily_loss",
                        "full_daily_assault_ready", "full_regular_refill_ready",
                        "full_monthly_ready", "full_calendar_ready", "release_effects_ready"):
                self.assertFalse(value[key])
            self.assertIsNone(value["actual_post_stage"])
            self.assertIsNone(value["actual_post_physical_chunks"])
            self.assertIsNone(value["actual_post_regiment_currents"])
            self.assertEqual(value["native_writes_executed"], 0)
            outputs[name] = returned
            if destination := os.environ.get("XAR_DAILY_ASSAULT_FIRST_OUTPUT"):
                Path(destination).write_text(json.dumps(outputs, indent=2) + "\n", encoding="utf-8")
            return value

        value = query("sequential-duplicates-target-only-refresh", assault_packet())
        self.assertTrue(value["sequential_numeric_ready"])
        self.assertEqual(value["completed_group_count"], 2)
        self.assertEqual([g["conditional_budget"]["expected_loss"] for g in value["groups"]],
                         EXPECTED["sequential"]["budgets"])
        self.assertEqual(value["groups"][1]["conditional_budget"]["conditional_besieging_strength"], 252)
        self.assertEqual([[r["requested_loss_soldiers_i32"] for r in g["preferred"]["requests"]]
                          for g in value["groups"]], EXPECTED["sequential"]["requests"])
        self.assertEqual(value["groups"][0]["preferred"]["remaining_budget_i32"], 34)
        self.assertIsNone(value["groups"][0]["residual"])
        self.assertEqual([g["army_counts"][0]["conditional_whole_current_soldiers_i32"]
                          for g in value["groups"]], [166, 150])
        cached = {r["army_regiment_id"]: r for r in value["conditional_regiment_currents"]}
        self.assertEqual([cached[x]["current_soldiers"] for x in (RA, RP, RB)], [20, 50, 80])
        physical = {(r["persistent_regiment_id"], r["chunk_index"]): r
                    for r in value["conditional_physical_chunks"]}
        self.assertEqual(physical[51001, 0]["current_soldiers"], 10)
        self.assertTrue(value["groups"][1]["preferred"]["requests"][0]["writer_projection"]["writer_skipped"])

        residual = assault_packet()
        residual["current_daily_assault_loss_inputs_v1"]["groups"][0]["native_current_expected_loss"] = 500
        residual["current_daily_assault_loss_inputs_v1"]["groups"][0]["besieging_inputs_v1"][
            "assault_context"]["casualty_percentage_raw"] = 8620691
        value = query("original-overflow-flags0-positive-type", residual)
        self.assertTrue(value["sequential_numeric_ready"])
        first = value["groups"][0]
        self.assertEqual(first["preferred"]["original_overflow_i32"], 100)
        self.assertEqual([r["requested_loss_soldiers_i32"] for r in first["residual"]["requests"]], [0, 0, 50])
        self.assertEqual(first["residual"]["requests"][2]["army_regiment_id"], RP)

        skipped = assault_packet()
        skipped["current_daily_assault_loss_inputs_v1"]["target_regiments"][0].update(
            native_loss_writer_skipped=True, replenishment_records_v1=None)
        value = query("character-skip-no-DATA-no-cache-refresh", skipped)
        self.assertTrue(value["sequential_numeric_ready"])
        self.assertEqual([g["conditional_budget"]["expected_loss"] for g in value["groups"]], [116, 58])
        self.assertEqual(value["groups"][0]["preferred"]["remaining_budget_i32"], 0)

        missing = assault_packet()
        missing["current_daily_assault_loss_inputs_v1"]["target_regiments"][0].update(
            _state(False, "target_DATA_unreadable"), replenishment_records_v1=None)
        value = query("missing-used-DATA-prefix", missing)
        self.assertFalse(value["sequential_numeric_ready"])
        self.assertEqual(value["completed_group_count"], 0)
        self.assertFalse(value["groups"][0]["preferred"]["requests"][0]["writer_ready"])
        self.assertFalse(value["groups"][1]["sequential_entry_reached"])
        self.assertEqual(value["groups"][1]["native_current_expected_loss"], 58)

        percentage = assault_packet()
        percentage["current_daily_assault_loss_inputs_v1"]["groups"][1]["besieging_inputs_v1"][
            "assault_context"].update(status="unavailable", unavailable_reason="percentage_unreadable",
                                      casualty_percentage_raw=None)
        value = query("missing-next-loaded-percentage-keeps-first-group", percentage)
        self.assertFalse(value["sequential_numeric_ready"])
        self.assertEqual(value["completed_group_count"], 1)
        self.assertEqual(value["groups"][1]["conditional_budget"]["conditional_besieging_strength"], 252)
        self.assertIsNone(value["groups"][1]["conditional_budget"]["expected_loss"])

        invalid = assault_packet()
        leaf = invalid["current_daily_assault_loss_inputs_v1"]
        leaf["target_regiments"] = []
        for group in leaf["groups"]:
            group.update(_state(False, "unused_context"), native_current_expected_loss=None,
                         province_magic_raw_u32=0, besieging_inputs_v1=None)
        value = query("source-zero-invalid-Province-no-unused-DATA", invalid)
        self.assertTrue(value["sequential_numeric_ready"])
        self.assertEqual([g["conditional_budget"]["expected_loss"] for g in value["groups"]], [0, 0])
        self.assertTrue(all(g["preferred"] is None for g in value["groups"]))

        id_minus_one = assault_packet()
        id_minus_one["current_daily_assault_loss_inputs_v1"]["groups"][1]["besieging_inputs_v1"]["province_id"] = -1
        value = query("group-Province-magic-authority-over-metadata-id", id_minus_one)
        self.assertEqual(value["groups"][1]["conditional_budget"]["expected_loss"], 25)

        negative = assault_packet()
        negative["current_daily_assault_loss_inputs_v1"]["groups"][0]["native_current_expected_loss"] = -1
        value = query("negative-budget-enters-signed-cap-inner-stops", negative)
        self.assertEqual(value["groups"][0]["preferred"]["initial_cap_i32"], -1)
        self.assertEqual(value["groups"][0]["preferred"]["requests"], [])

        queued = assault_packet()
        table = queued["current_daily_assault_table_v1"]
        leaf = queued["current_daily_assault_loss_inputs_v1"]
        all_currents(queued, RP, 0)
        leaf["target_regiments"][1]["replenishment_records_v1"] = fixed_data(RP, 51002, 0, 100)
        table["groups"][0]["armies"] = vector([12, 12, 0x80000005])
        fallback = table["groups"][0]["armies"]["occurrences"][2]["resolution"]
        fallback.update(object_identity="army:12", selected_full_id_u32=12)
        leaf["groups"][0]["army_counts"] = []
        for ordinal, item in enumerate(table["groups"][0]["armies"]["occurrences"]):
            leaf["groups"][0]["army_counts"].append({**_state(True), "native_index": ordinal,
                "raw_full_id_u32": item["raw_full_id_u32"], "resolution": deepcopy(item["resolution"]),
                "native_whole_current_soldiers": 200, "regiments": [count_regiment(0, RA, 200, 300)]})
        leaf["groups"][1]["army_counts"][0].update(native_whole_current_soldiers=200,
            regiments=[count_regiment(0, RA, 200, 300)])
        for index, group in enumerate(leaf["groups"]):
            group["besieging_inputs_v1"] = b_family(400, rp_current=0, all_rows=False)
            group["besieging_inputs_v1"]["assault_context"]["casualty_percentage_raw"] = 10000000 if index == 0 else 1000000
            group["native_current_expected_loss"] = 400 if index == 0 else 40
        value = query("raw-queue-duplicates-fallback-selected-id-distinct", queued)
        self.assertTrue(value["sequential_numeric_ready"])
        self.assertEqual([r["raw_full_id_u32"] for r in value["ordered_queue_append_requests"]], EXPECTED["queue"])
        self.assertEqual(value["groups"][1]["conditional_budget"]["expected_loss"], 0)

        wrapped = assault_packet()
        all_currents(wrapped, RA, 2147483640)
        all_currents(wrapped, RP, 20)
        leaf = wrapped["current_daily_assault_loss_inputs_v1"]
        leaf["target_regiments"][1]["replenishment_records_v1"] = fixed_data(RP, 51002, 20, 100)
        for group in wrapped["current_daily_assault_table_v1"]["groups"]:
            for item in group["arrgs"]["occurrences"]:
                if item["raw_full_id_u32"] == RP:
                    item.update(definition_type_raw_i32=0, denominator_included=True, current_raw_i32=20)
        for index, group in enumerate(leaf["groups"]):
            group["besieging_inputs_v1"] = b_family(4, ra_current=2147483640, rp_current=20, all_rows=False)
            group["besieging_inputs_v1"]["assault_context"]["casualty_percentage_raw"] = 25000000 if index == 0 else 1000000
            group["native_current_expected_loss"] = 10 if index == 0 else 0
            group["army_counts"][0]["native_whole_current_soldiers"] = -2147483556
        value = query("wrap32-denominator-low32-product-negative-request", wrapped)
        self.assertTrue(value["sequential_numeric_ready"])
        first = value["groups"][0]["preferred"]
        self.assertEqual(first["denominator_i32"], 4)
        self.assertEqual(first["requests"][0]["wrapped_product_i32"], -32)
        self.assertEqual(first["requests"][0]["requested_loss_soldiers_i32"], -8)
        self.assertEqual(value["groups"][1]["conditional_budget"]["conditional_besieging_strength"], 432)
        self.assertEqual(value["groups"][1]["conditional_budget"]["expected_loss"], 43)

        parent_zero = assault_packet()
        all_currents(parent_zero, RA, 0)
        table = parent_zero["current_daily_assault_table_v1"]
        leaf = parent_zero["current_daily_assault_loss_inputs_v1"]
        table["groups"][0]["arrgs"] = vector([RA, RA, RD], arrg=True, currents=[0, 0, 10])
        table["groups"][0]["armies"] = vector([])
        leaf["groups"][0].update(native_current_expected_loss=5, besieging_inputs_v1=None, army_counts=[])
        leaf["target_regiments"].append(target(RD, 10, 10, fixed_data(RD, 51006, 10, 10)))
        leaf["groups"][1].update(native_current_expected_loss=None, province_magic_raw_u32=0,
                                  besieging_inputs_v1=None)
        leaf["groups"][1]["army_counts"][0]["native_whole_current_soldiers"] = 130
        value = query("parent-zero-still-refreshes-and-next-alias-rereads-cache", parent_zero)
        requests = value["groups"][0]["preferred"]["requests"]
        self.assertEqual([r["requested_loss_soldiers_i32"] for r in requests], [0, 100])
        self.assertEqual(requests[0]["writer_projection"]["writes"], [])
        self.assertEqual(requests[0]["writer_projection"]["conditional_raised_regiment_refresh"]["current_soldiers"], 200)
        self.assertEqual(requests[1]["current_before_call_i32"], 200)

        partial_reference = assault_packet()
        count = partial_reference["current_daily_assault_loss_inputs_v1"]["groups"][0]["army_counts"][0]
        count.update(_state(False, "roster_full_id_unreadable"))
        unresolved = {key: None for key in count["regiments"][0]["resolution"]}
        unresolved.update(_state(False, "roster_full_id_unreadable"))
        count["regiments"][0].update(raw_full_id_u32=None, resolution=unresolved, identity_valid=None)
        value = query("nullable-native-DWORD-stops-consumed-Army-count", partial_reference)
        self.assertTrue(value["groups"][0]["numeric_ready"])
        self.assertFalse(value["groups"][0]["queue_requests_ready"])
        self.assertFalse(value["groups"][1]["sequential_entry_reached"])

        empty = assault_packet()
        table = empty["current_daily_assault_table_v1"]
        table.update(groups=[], physical_controls=[], observed_occupied_group_count=0, physical_scan_ready=False)
        table["header"] = {key: None for key in table["header"]}
        table["header"].update(_state(False, "unused_empty_header"), occupied_count_raw_i32=0)
        del empty["current_daily_assault_loss_inputs_v1"]
        value = query("empty-current-table-without-unused-loss-family", empty)
        self.assertTrue(value["sequential_numeric_ready"])
        self.assertEqual(value["groups"], [])

        legacy = row()
        value = query("legacy-no-table-no-loss-family", legacy)
        self.assertFalse(value["sequential_numeric_ready"])
        self.assertEqual(value["missing_inputs"], ["current_daily_assault_table_v1"])


if __name__ == "__main__":
    unittest.main()
