"""Construction-only current standalone admission sources; no test execution."""
from __future__ import annotations


def state(ready=False, reason="not_demanded", *, partial=False):
    return {"status": "available" if ready else "partial" if partial else "unavailable",
            "ready": ready, "unavailable_reason": "" if ready else reason}


def identity(kind, full_id=0):
    bases = {"army": 1000000, "unit": 2000000, "character": 3000000,
             "siege": 4000000, "war": 5000000}
    return f"native:{bases[kind] + (full_id & 0xFFFFFF) * 16}"


def operand_resolution(requested=None, *, kind="army", selected=None, fallback=False):
    if requested is None:
        return {**state(), "requested_full_id_u32": None, "registry_loaded": None,
                "registry_capacity_u32": None, "registry_index_u32": None,
                "indexed_identity": None, "indexed_full_id_u32": None,
                "selection": None, "used_fallback": None, "object_identity": None,
                "selected_full_id_u32": None, "selected_object_ready": False,
                "selected_full_id_read_ready": None}
    selected = requested if selected is None else selected
    return {**state(True), "requested_full_id_u32": requested,
            "registry_loaded": not fallback,
            "registry_capacity_u32": None if fallback else 2048,
            "registry_index_u32": requested & 0xFFFFFF,
            "indexed_identity": None if fallback else identity(kind, selected),
            "indexed_full_id_u32": None if fallback else selected,
            "selection": "native_fallback" if fallback else "registry_full_id",
            "used_fallback": fallback, "object_identity": identity(kind, selected),
            "selected_full_id_u32": selected, "selected_object_ready": True,
            "selected_full_id_read_ready": True}


def references(ids=None, *, data_identity="native:8000000"):
    if ids is None:
        return {**state(), "references_ready": False, "count_raw_i32": None,
                "data_identity": None, "data_present": None, "occurrences": [],
                "observed_occurrence_count": 0}
    complete = all(value is not None for value in ids)
    return {**state(complete, "raw_reference_element_unavailable", partial=not complete),
            "references_ready": complete, "count_raw_i32": len(ids),
            "data_identity": data_identity if ids else None,
            "data_present": True if ids else None,
            "occurrences": [{**state(value is not None, "raw_reference_element_unavailable"),
                             "native_index": index, "raw_full_id_u32": value}
                            for index, value in enumerate(ids)],
            "observed_occurrence_count": len(ids)}


def relation_lookup():
    return {**state(), "component_identity": None, "component_present": None,
            "table_data_identity": None, "table_data_present": None,
            "table_count_raw_i32": None, "target_character_full_id_raw_u32": None,
            "probes": [], "candidate_slot_index_i64": None, "selection": None,
            "default_relationship_identity": None, "default_relationship_present": None,
            "selected_relationship_identity": None, "selected_relationship_present": None,
            "selected_relationship_war_id_raw_u32": None}


def admission_gate():
    result = {**state(), "verdict": None}
    for name in ("original_army_unit_id_raw_u32", "original_unit_kind_raw_u32",
                 "original_unit_province_identity", "original_unit_province_present",
                 "original_province_identity_raw_u32", "selected_province_comparison_identity",
                 "selected_province_comparison_identity_raw_u32", "original_unit_counter_170_raw_i32",
                 "associated_army_id_raw_u32", "province_siege_id_raw_u32",
                 "province_counter_850_raw_i32", "associated_army_flag_1d4_raw_u8",
                 "associated_army_flag_1ec_raw_u8", "associated_army_unit_id_raw_u32",
                 "associated_unit_character_id_raw_u32", "province_character_id_73c_raw_u32",
                 "associated_character_full_id_raw_u32", "province_character_full_id_raw_u32",
                 "selected_war_ended_358_raw_u8"):
        result[name] = None
    for name in ("original_unit_resolution", "associated_army_resolution", "associated_unit_resolution",
                 "associated_character_resolution", "province_character_resolution", "selected_war_resolution"):
        result[name] = operand_resolution()
    result["relation_lookup"] = relation_lookup()
    return result


def pending_selection():
    result = {**state(), "probes": [], "suppression_references": references()}
    for name in ("entries_identity", "entries_present", "mask_raw_i32", "tail_distance_raw_u8",
                 "end_slot_raw_i32", "target_army_full_id_u32", "hash_raw_u32", "home_slot_i64",
                 "selected_physical_slot_i64", "selected_is_end_marker", "selected_control_raw_u8"):
        result[name] = None
    return result


def roster_occurrence(index, raw_id):
    result = {**state(), "native_index": index, "raw_full_id_u32": raw_id,
              "original_army_resolution": operand_resolution(), "gate": admission_gate(),
              "caller_unit_resolution": operand_resolution(), "siege_resolution": operand_resolution(),
              "pending_selection": pending_selection(), "original_arrg_references": references(),
              "arrg_occurrences": [], "army_append_ready": False, "arrg_append_ready": False}
    for name in ("caller_army_unit_id_raw_u32", "caller_province_identity", "caller_province_present",
                 "caller_used_province_fallback", "caller_province_siege_id_raw_u32", "siege_flag_44c_raw_u8",
                 "selected_army_full_id_raw_u32", "removal_contains_selected_army", "army_append",
                 "army_append_siege_full_id_u32", "army_append_full_id_u32", "arrg_append_full_ids_u32"):
        result[name] = None
    return result


def fnv(full_id):
    result = 0x811C9DC5
    for shift in (0, 8, 16, 24):
        result = ((result ^ ((full_id >> shift) & 255)) * 0x01000193) & 0xFFFFFFFF
    return result


def _true_gate(army, siege):
    gate = admission_gate()
    gate.update(state(True), verdict=True, original_army_unit_id_raw_u32=1000 + army,
                original_unit_resolution=operand_resolution(1000 + army, kind="unit"),
                original_unit_kind_raw_u32=0, original_unit_province_identity=f"native:{9000000 + army}",
                original_unit_province_present=True, original_province_identity_raw_u32=800 + army,
                selected_province_comparison_identity=f"native:{9000000 + army}",
                selected_province_comparison_identity_raw_u32=800 + army,
                original_unit_counter_170_raw_i32=0, associated_army_id_raw_u32=100 + army,
                associated_army_resolution=operand_resolution(100 + army), province_siege_id_raw_u32=siege,
                province_counter_850_raw_i32=1, associated_army_flag_1d4_raw_u8=0,
                associated_army_flag_1ec_raw_u8=0, associated_army_unit_id_raw_u32=1100 + army,
                associated_unit_resolution=operand_resolution(1100 + army, kind="unit"),
                associated_unit_character_id_raw_u32=101,
                associated_character_resolution=operand_resolution(101, kind="character"),
                province_character_id_73c_raw_u32=202,
                province_character_resolution=operand_resolution(202, kind="character"),
                associated_character_full_id_raw_u32=101, province_character_full_id_raw_u32=202,
                selected_war_resolution=operand_resolution(0x01000001, kind="war", selected=0xFFFFFFFF, fallback=True),
                selected_war_ended_358_raw_u8=0)
    relation = relation_lookup()
    relation.update(state(True), component_identity="native:9100000", component_present=True,
                    table_data_identity="native:9200000", table_data_present=True, table_count_raw_i32=3,
                    target_character_full_id_raw_u32=202,
                    probes=[{"native_index": 0, "kind": "pivot", "slot_index_i64": 1, "key_character_id_raw_u32": 202},
                            {"native_index": 1, "kind": "pivot", "slot_index_i64": 0, "key_character_id_raw_u32": 101},
                            {"native_index": 2, "kind": "candidate", "slot_index_i64": 1, "key_character_id_raw_u32": 202}],
                    candidate_slot_index_i64=1, selection="pair_map",
                    selected_relationship_identity="native:9300000", selected_relationship_present=True,
                    selected_relationship_war_id_raw_u32=0x01000001)
    gate["relation_lookup"] = relation
    return gate


def _admitted(index, raw_id, army, siege, arrgs, suppression):
    row = roster_occurrence(index, raw_id)
    row.update(state(True), original_army_resolution=operand_resolution(raw_id, selected=army, fallback=raw_id != army),
               gate=_true_gate(army, siege), caller_army_unit_id_raw_u32=1000 + army,
               caller_unit_resolution=operand_resolution(1000 + army, kind="unit"),
               caller_province_identity=f"native:{9000000 + army}", caller_province_present=True,
               caller_used_province_fallback=False, caller_province_siege_id_raw_u32=siege,
               siege_resolution=operand_resolution(siege, kind="siege"), siege_flag_44c_raw_u8=1,
               selected_army_full_id_raw_u32=army, removal_contains_selected_army=False,
               army_append_ready=True, army_append=True, army_append_siege_full_id_u32=siege,
               army_append_full_id_u32=army, arrg_append_ready=True,
               arrg_append_full_ids_u32=[value for value in arrgs if value not in suppression],
               original_arrg_references=references(arrgs, data_identity=f"native:{9400000 + army}"),
               arrg_occurrences=[{**state(True), "native_index": ordinal, "raw_full_id_u32": value,
                                  "pending_contains": value in suppression, "append": value not in suppression}
                                 for ordinal, value in enumerate(arrgs)])
    pending = pending_selection()
    home = fnv(army) & 7
    pending.update(state(True), entries_identity="native:9500000", entries_present=True, mask_raw_i32=7,
                   target_army_full_id_u32=army, hash_raw_u32=fnv(army), home_slot_i64=home,
                   probes=[{"native_index": 0, "physical_slot_i64": home, "distance_raw_u8": 1,
                            "control_raw_u8": 1, "key_raw_full_id_u32": army}],
                   selected_physical_slot_i64=home, selected_is_end_marker=False, selected_control_raw_u8=1,
                   suppression_references=references(suppression) if arrgs else references())
    row["pending_selection"] = pending
    if raw_id != army:
        row["original_army_resolution"].update(registry_loaded=True, registry_capacity_u32=32,
            indexed_identity=identity("army", army), indexed_full_id_u32=army)
    return row


def roster_admission_source():
    """Nonempty source-derived true stream with repeats, scope and fallback."""
    roster = [11, 11, 13, 0xFE00000E, 15]
    rows = [_admitted(0, 11, 11, 13, [100, 100, 200, 300], [200]),
            _admitted(1, 11, 11, 13, [100, 100, 200, 300], [200]),
            _admitted(2, 13, 13, 5, [400], []),
            _admitted(3, 0xFE00000E, 14, 2, [], [])]
    skip = roster_occurrence(4, 15)
    gate = _true_gate(15, 5)
    gate.update(verdict=False, province_character_id_73c_raw_u32=101,
                province_character_resolution=operand_resolution(101, kind="character"),
                province_character_full_id_raw_u32=101, relation_lookup=relation_lookup(),
                selected_war_resolution=operand_resolution(), selected_war_ended_358_raw_u8=None)
    skip.update(state(True), original_army_resolution=operand_resolution(15), gate=gate,
                army_append_ready=True, army_append=False, arrg_append_ready=True, arrg_append_full_ids_u32=[])
    rows.append(skip)
    return {**state(True), "schema_version": 1, "source": "native_current_daily_assault_roster_admission",
            "stage": "observed_current_standalone_2a99b40_admission",
            "manager_loaded": True, "manager_identity": "native:7000000",
            "original_roster": references(roster, data_identity="native:7100000"),
            "removal_queue": references([99], data_identity="native:7200000"), "occurrences": rows,
            "raw_roster_references_ready": True, "original_army_selections_ready": True,
            "army_appends_ready": True, "arrg_appends_ready": True, "conditional_admission_ready": True,
            "actual_next_callback_ready": False, "actual_tomorrow_roster_ready": False,
            "full_future_table_placement_ready": False, "full_daily_assault_ready": False}


def zero_roster_admission_source():
    source = roster_admission_source()
    source.update(original_roster=references([]), removal_queue=references(), occurrences=[])
    return source


def fallback_war_metadata_unavailable_source():
    source = roster_admission_source()
    for row in source["occurrences"][:4]:
        row["gate"]["selected_war_resolution"].update(
            state(False, "selected_fallback_full_id_metadata_unavailable", partial=True),
            selected_full_id_u32=None, selected_full_id_read_ready=False)
    return source


def partial_pending_admission_source(index=2):
    source = roster_admission_source()
    row = source["occurrences"][index]
    pending = pending_selection()
    pending.update(state(False, "pending_mask_unavailable", partial=True),
                   entries_identity="native:9500000", entries_present=True,
                   target_army_full_id_u32=row["army_append_full_id_u32"],
                   hash_raw_u32=fnv(row["army_append_full_id_u32"]))
    row.update(state(False, "pending_mask_unavailable", partial=True), pending_selection=pending,
               original_arrg_references=references(), arrg_occurrences=[],
               arrg_append_ready=False, arrg_append_full_ids_u32=None)
    source.update(state(False, "current_conditional_admission_inputs_incomplete", partial=True),
                  arrg_appends_ready=False, conditional_admission_ready=False)
    return source


def matched_suppression_with_unread_tail_source():
    source = roster_admission_source()
    for row in source["occurrences"][:2]:
        row["original_arrg_references"] = references([200])
        row["pending_selection"]["suppression_references"] = references([200, None])
        row["arrg_occurrences"] = [{**state(True), "native_index": 0, "raw_full_id_u32": 200,
                                    "pending_contains": True, "append": False}]
        row["arrg_append_full_ids_u32"] = []
    return source


def reused_queue_pointer_metadata_unavailable_source():
    """Approved count-matched old raw list; pointer metadata is independent."""
    source = roster_admission_source()
    source["removal_queue"].update(data_identity=None, data_present=None)
    return source


def partial_raw_roster_source(index=2):
    source = roster_admission_source()
    ids = [row["raw_full_id_u32"] for row in source["original_roster"]["occurrences"]]
    ids[index] = None
    source["original_roster"] = references(ids, data_identity="native:7100000")
    source["occurrences"][index] = roster_occurrence(index, None)
    source.update(state(False, "original_army_raw_reference_unavailable", partial=True),
                  raw_roster_references_ready=False, original_army_selections_ready=False,
                  army_appends_ready=False, arrg_appends_ready=False, conditional_admission_ready=False)
    return source
