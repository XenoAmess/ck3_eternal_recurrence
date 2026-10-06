"""New construction-only raw operands for the ordered pending-update compound."""
from __future__ import annotations

from copy import deepcopy

from daily_assault_roster_admission_fixture import (
    admission_gate, fnv, operand_resolution, references, roster_occurrence, state,
)


def resolution(requested=None, *, selected=None, fallback=False, kind="army"):
    out = operand_resolution(requested, selected=selected, fallback=fallback)
    if requested is not None:
        value = requested if selected is None else selected
        identity = f"native:{100000000 + {'army': 1, 'combat': 2, 'arrg': 3, 'contract': 4, 'persistent': 5, 'war': 6, 'unit': 7}[kind] * 1000000 + (value & 0xFFFFFF) * 16}"
        out["object_identity"] = identity
        if not fallback:
            out["indexed_identity"] = identity
    return out


def arrg(index, full_id, branch="current_zero"):
    out = {**state(True), "native_index": index, "raw_full_id_u32": full_id,
        "arrg_resolution": resolution(full_id, kind="arrg"), "current_38_raw_i32": 0,
        "contract_id_144_raw_u32": None, "contract_resolution": resolution(), "contract_flag_b9_raw_u8": None,
        "state_14c_raw_i32": None, "original_data_identity": None, "original_data_present": None,
        "first_persistent_id_raw_u32": None, "persistent_resolution": resolution(),
        "persistent_war_id_13c_raw_u32": None, "war_resolution": resolution(), "war_magic_0c_raw_u32": None,
        "append_to_pending": True, "append_full_id_u32": full_id}
    if branch == "current_zero":
        return out
    out.update(current_38_raw_i32=10, contract_id_144_raw_u32=200,
               contract_resolution=resolution(200, kind="contract"), contract_flag_b9_raw_u8=0,
               state_14c_raw_i32=0, append_to_pending=False, append_full_id_u32=None)
    if branch == "contract_nonzero":
        out.update(contract_flag_b9_raw_u8=1, state_14c_raw_i32=None, append_to_pending=True, append_full_id_u32=full_id)
    elif branch != "state_not_one":
        out.update(state_14c_raw_i32=1, original_data_identity="native:8800000", original_data_present=True,
                   first_persistent_id_raw_u32=300, persistent_resolution=resolution(300, kind="persistent"),
                   persistent_war_id_13c_raw_u32=0xFFFFFFFF)
        if branch != "persistent_sentinel":
            out["persistent_war_id_13c_raw_u32"] = 400
            out["war_resolution"] = resolution(400, kind="war")
            out["war_magic_0c_raw_u32"] = 0x5761725F
            if branch == "war_magic_invalid":
                out.update(war_magic_0c_raw_u32=0, append_to_pending=True, append_full_id_u32=full_id)
            elif branch == "war_full_id_invalid":
                out["war_resolution"] = resolution(400, selected=0xFFFFFFFF, fallback=True, kind="war")
                out.update(append_to_pending=True, append_full_id_u32=full_id)
    return out


def setup(target, ids=(), *, mode="existing"):
    home = fnv(target) & 7
    out = {**state(True), "entries_identity": "native:7700000", "entries_present": True,
        "mask_raw_i32": 7, "target_army_full_id_u32": target, "hash_raw_u32": fnv(target),
        "home_slot_i64": home, "terminal_physical_slot_i64": home,
        "probes": [{"native_index": 0, "physical_slot_i64": home, "distance_raw_u8": 1,
                    "control_raw_u8": 1, "key_raw_full_id_u32": target}],
        "existing_key": True, "existing_references": references(list(ids)),
        "map_count_raw_i32": None, "insertion_tail_raw_u8": None, "insertion_threshold_bits_u32": None}
    if mode != "existing":
        out.update(existing_key=False, existing_references=references(), map_count_raw_i32=0,
                   insertion_tail_raw_u8=4, insertion_threshold_bits_u32=0x3F800000)
        out["probes"][0].update(control_raw_u8=0, key_raw_full_id_u32=None)
        if mode == "collision":
            # target13 home1; key4 home1 then key7 home2/control1 is a genuine carried insertion arm.
            out["probes"][0].update(control_raw_u8=1, key_raw_full_id_u32=4)
            out["probes"].append({"native_index": 1, "physical_slot_i64": home + 1,
                "distance_raw_u8": 2, "control_raw_u8": 1, "key_raw_full_id_u32": None})
            out["terminal_physical_slot_i64"] = home + 1
    return out


def undemanded_setup():
    out = setup(13)
    out.update(state(), entries_identity=None, entries_present=None, mask_raw_i32=None,
               target_army_full_id_u32=None, hash_raw_u32=None, home_slot_i64=None,
               terminal_physical_slot_i64=None, probes=[], existing_key=None, existing_references=references())
    return out


def occurrence(index, target=13, *, pending_ids=(), setup_mode="existing", branches=None):
    branches = branches or ["current_zero", "persistent_sentinel"]
    selections = [arrg(i, 100 + i, branch) for i, branch in enumerate(branches)]
    return {**state(True), "native_index": index, "raw_full_id_u32": target,
        "original_army_resolution": resolution(target), "combat_id_128_raw_u32": 0xFFFFFFFF,
        "combat_resolution": resolution(0xFFFFFFFF, fallback=True, kind="combat"), "combat_magic_0c_raw_u32": 0,
        "army_counter_5c_raw_i32": 0, "pending_mutator_selected": True,
        "pending_setup": setup(target, pending_ids, mode=setup_mode),
        "original_arrg_references": references([100 + i for i in range(len(branches))]), "arrg_occurrences": selections}


def source(*, mode="existing", branches=None, pending_ids=(), roster=(13, 13), queue=(99, 99)):
    rows = [occurrence(i, target, pending_ids=pending_ids, setup_mode=mode, branches=branches) for i, target in enumerate(roster)]
    return {**state(True), "schema_version": 1, "source": "native_current_pre_date_pending_update_inputs",
        "stage": "observed_current_pre_date_pending_update_inputs", "manager_loaded": True,
        "manager_identity": "native:7000000", "original_roster": references(list(roster)),
        "removal_queue": references(list(queue)), "occurrences": rows,
        "raw_roster_references_ready": True, "source_operands_ready": True,
        "actual_pre_date_callback_ready": False, "actual_tomorrow_roster_ready": False,
        "full_daily_assault_ready": False, "full_monthly_ready": False}


def bypass_source(kind):
    out = source()
    for row in out["occurrences"]:
        row.update(pending_mutator_selected=False, pending_setup=undemanded_setup(),
                   original_arrg_references=references(), arrg_occurrences=[])
        if kind == "combat":
            row.update(combat_id_128_raw_u32=700, combat_resolution=resolution(700, kind="combat"),
                       combat_magic_0c_raw_u32=0x436F6D62, army_counter_5c_raw_i32=None)
        else:
            row["army_counter_5c_raw_i32"] = -3
    return out


def zero_source():
    out = source(roster=(), queue=())
    out["removal_queue"] = references()
    return out


def missing_context_source():
    out = zero_source()
    out.update(state(reason="game_data_unavailable"), manager_loaded=None, manager_identity=None,
               original_roster=references(), raw_roster_references_ready=False, source_operands_ready=False)
    return out


def later_partial_source():
    out = source()
    row = out["occurrences"][1]
    row.update(state(False, "subject_contract_b9_unavailable", partial=True))
    row["arrg_occurrences"][1]["contract_flag_b9_raw_u8"] = None
    row["arrg_occurrences"][1].update(state(False, "subject_contract_b9_unavailable", partial=True), append_to_pending=None)
    out.update(state(False, "source_operands_incomplete", partial=True), source_operands_ready=False)
    return out


def same_roster_standalone_source(leaf):
    """Same original occurrence frame, with real early Unit-kind false admission."""
    if leaf is None:
        return None
    rows = []
    for raw in leaf["original_roster"]["occurrences"]:
        row = roster_occurrence(raw["native_index"], raw["raw_full_id_u32"])
        row["original_army_resolution"] = resolution(raw["raw_full_id_u32"])
        gate = admission_gate()
        gate.update(state(True), verdict=False, original_army_unit_id_raw_u32=800,
                    original_unit_resolution=operand_resolution(800, kind="unit"), original_unit_kind_raw_u32=1)
        row.update(state(True), gate=gate, army_append_ready=True, army_append=False,
                   arrg_append_ready=True, arrg_append_full_ids_u32=[])
        rows.append(row)
    complete = leaf["original_roster"]["references_ready"]
    return {**state(complete, "original_roster_unavailable", partial=not complete), "schema_version": 1,
        "source": "native_current_daily_assault_roster_admission", "stage": "observed_current_standalone_2a99b40_admission",
        "manager_loaded": leaf["manager_loaded"], "manager_identity": leaf["manager_identity"],
        "original_roster": deepcopy(leaf["original_roster"]), "removal_queue": deepcopy(leaf["removal_queue"]),
        "occurrences": rows, "raw_roster_references_ready": complete, "original_army_selections_ready": complete,
        "army_appends_ready": complete, "arrg_appends_ready": complete, "conditional_admission_ready": complete,
        "actual_next_callback_ready": False, "actual_tomorrow_roster_ready": False,
        "full_future_table_placement_ready": False, "full_daily_assault_ready": False}
