"""Map owned natural 2A97EB0 copies to the qualified conditional consumer.

The journal's group scalar is recorded by a child during the original call.
It remains a copied observation, rather than an entry B or a prior-write proof.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from xar_autoplayer.bridge.army_daily_assault_active_table_contract import (
    normalize_current_daily_assault_table_v1,
)
from xar_autoplayer.bridge.army_daily_assault_loss_inputs_contract import (
    normalize_current_daily_assault_loss_inputs_v1,
)

_BASIS = ("owned_natural_2A97EB0_entry; exact_post_date_phase_token_join; "
          "no_prior_write_or_full_B_assumption")


def _identity(value):
    return hex(value) if type(value) is int and 0 < value < 1 << 64 else None


def _i32(value):
    if value is None:
        return None
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _state(ready, reason):
    return {"status": "available" if ready else "partial", "ready": bool(ready),
            "unavailable_reason": None if ready else reason}


def _token(value):
    if not isinstance(value, Mapping):
        return None
    clock, sequence, thread = (value.get(key) for key in
                               ("clock_identity", "sequence", "thread_id"))
    if (type(clock) is int and 0 < clock < 1 << 64 and
            type(sequence) is int and 0 < sequence < 1 << 64 and
            type(thread) is int and 0 <= thread < 1 << 32):
        return clock, sequence, thread
    return None


def _ordered(left, right):
    a, b = _token(left), _token(right)
    return a is not None and b is not None and a[0] == b[0] and a[2] == b[2] and a[1] < b[1]


def _resolution(raw, requested):
    raw = raw if isinstance(raw, Mapping) else {}
    selected = raw.get("selected_full_id_u32")
    fallback = raw.get("used_fallback")
    object_identity = _identity(raw.get("object_identity"))
    copied_request = raw.get("requested_full_id_u32")
    ready = (requested is not None and copied_request == requested and
             object_identity is not None and type(selected) is int and
             type(fallback) is bool and (fallback or selected == requested))
    return {**_state(ready, "copied_resolution_or_exact_requested_generation_missing"),
            "requested_full_id_u32": requested, "registry_loaded": None,
            "registry_capacity_u32": None, "registry_index_u32": None,
            "indexed_identity": None, "indexed_full_id_u32": None,
            "selection": "native_fallback" if fallback is True else
                         "registry_full_id" if fallback is False else None,
            "used_fallback": fallback, "object_identity": object_identity,
            "selected_full_id_u32": selected}


def _regiment_map(rows, missing):
    result = {}
    for row in rows:
        requested = row["resolution"]["requested_full_id_u32"]
        if requested is not None:
            if requested in result:
                result[requested] = None
                missing.append(f"unambiguous_copied_regiment_request:{requested}")
            else:
                result[requested] = row
    return result


def _vector(raw, *, arrg, regiments, armies=()):
    army_rows = {row["native_index"]: row for row in armies}
    rows = []
    for index, full_id in enumerate(raw["ordered_full_ids_u32"]):
        source = regiments.get(full_id) if arrg else army_rows.get(index)
        source = source if source is not None else {}
        resolution = _resolution(source.get("resolution"), full_id)
        common = {"native_index": index, "raw_full_id_u32": full_id,
                  "resolution": resolution}
        if arrg:
            valid = source.get("identity_valid")
            kind = source.get("definition_type_raw_i32")
            current = source.get("current_soldiers")
            included = False if valid is False else kind <= 0 if valid is True and type(kind) is int else None
            ready = resolution["ready"] and included is not None and (not included or current is not None)
            common.update(magic_raw_u32=source.get("magic_raw_u32"), identity_valid=valid,
                          definition_identity=None, definition_type_raw_i32=kind,
                          current_raw_i32=current, denominator_included=included)
        else:
            ready = resolution["ready"]
        rows.append({**common, **_state(ready, "copied_occurrence_demanded_fields_missing")})
    count = raw["count_raw_i32"]
    references = (raw["references_complete"] is True and type(count) is int and count >= 0 and
                  count == len(rows) and all(row["raw_full_id_u32"] is not None for row in rows))
    ready = references and all(row["ready"] for row in rows)
    return {**_state(ready, "copied_ordered_reference_or_demanded_fields_missing"),
            "references_ready": references, "count_raw_i32": count,
            "data_identity": _identity(raw["data_identity"]),
            "data_present": None if raw["data_identity"] is None else raw["data_identity"] != 0,
            "occurrences": rows, "observed_occurrence_count": len(rows)}


def _table(raw, manager, regiments):
    controls = [{"physical_slot_i64": index, "control_raw_u8": value,
                 "unavailable_reason": None if value is not None else "copied_control_unread"}
                for index, value in enumerate(raw["physical_controls"])]
    groups = []
    for source in raw["groups"]:
        armies = _vector(source["armies"], arrg=False, regiments=regiments,
                         armies=source["army_occurrences"])
        arrgs = _vector(source["arrgs"], arrg=True, regiments=regiments)
        resolution = _resolution(source["siege_resolution"], source["siege_full_id_u32"])
        ready = (source["hash_raw_u32"] is not None and source["control_raw_u8"] is not None and
                 source["siege_full_id_u32"] is not None and resolution["ready"] and
                 armies["ready"] and arrgs["ready"])
        groups.append({**_state(ready, "copied_group_demanded_fields_missing"),
                       "native_index": source["native_index"], "physical_slot_i64": source["physical_slot_i64"],
                       "hash_raw_u32": source["hash_raw_u32"], "control_raw_u8": source["control_raw_u8"],
                       "siege_full_id_u32": source["siege_full_id_u32"], "siege_resolution": resolution,
                       "armies": armies, "arrgs": arrgs,
                       "denominator_ready": arrgs["references_ready"] and all(row["ready"] for row in arrgs["occurrences"])})
    end = raw["end_slot_raw_i32"]
    physical = (raw["controls_complete"] is True and type(end) is int and end >= 0 and
                len(controls) == end and all(row["control_raw_u8"] is not None for row in controls) and
                raw["end_marker_control_raw_u8"] not in (None, 0) and
                [row["physical_slot_i64"] for row in controls if row["control_raw_u8"] != 0] ==
                [row["physical_slot_i64"] for row in groups])
    occupied = raw["occupied_count_raw_i32"]
    count_matches = type(occupied) is int and occupied >= 0 and occupied == len(groups)
    references = (physical and count_matches and raw["raw_references_complete"] is True and
                  all(group["hash_raw_u32"] is not None and group["siege_full_id_u32"] is not None and
                      group["armies"]["references_ready"] and group["arrgs"]["references_ready"] for group in groups))
    header_fields = ("occupied_count_raw_i32", "mask_raw_i32", "tail_distance_raw_u8",
                     "load_factor_f32_bits_u32", "end_slot_raw_i32", "end_marker_control_raw_u8")
    header_ready = _identity(raw["entries_identity"]) is not None and all(raw[key] is not None for key in header_fields)
    ready = manager is not None and references and all(group["ready"] for group in groups)
    return normalize_current_daily_assault_table_v1({
        **_state(ready, "owned_consumer_entry_table_incomplete"), "schema_version": 1,
        "source": "native_current_daily_assault_table", "stage": "observed_current_daily_assault_table",
        "manager_loaded": manager is not None, "manager_identity": manager,
        "header": {**_state(header_ready, "copied_entry_header_incomplete"),
                   "entries_identity": _identity(raw["entries_identity"]),
                   "entries_present": None if raw["entries_identity"] is None else raw["entries_identity"] != 0,
                   **{key: raw[key] for key in header_fields}},
        "physical_controls": controls, "groups": groups, "observed_occupied_group_count": len(groups),
        "physical_scan_ready": physical and count_matches, "raw_groups_ready": references})


def _data(raw):
    selected = raw["resolution"]["selected_full_id_u32"]
    count = raw["data_count_raw_i32"]
    if type(selected) is not int or type(count) is not int or count < 0:
        return None
    # The old full-DATA family also demands refill predicates/fractions which
    # this observer never reads. Keep physical numbers nullable and unavailable.
    records = []
    for source in raw["data_records"]:
        full_id, ordinal = source["persistent_full_id_u32"], source["data_chunk_ordinal"]
        if type(full_id) is not int or type(ordinal) is not int:
            return None
        physical = source["physical"] or {}
        current, maximum, state = (physical.get(key) for key in
                                   ("current_soldiers", "maximum_soldiers", "state_raw_i32"))
        records.append({"status": "unavailable", "unavailable_reason": "refill_predicates_and_fractions_not_captured",
                        "record_index": source["native_index"], "persistent_regiment_id": _i32(full_id),
                        "chunk_index": ordinal, "current_soldiers": current, "maximum_soldiers": maximum,
                        "effective_current_soldiers": maximum if state == 3 and current == 0 else current,
                        "state_raw": state, "chunk_army_regiment_id": physical.get("army_regiment_id"),
                        "native_can_replenish": None, "native_chunk_can_replenish": None,
                        "persistent_monthly_replenishment_fraction_raw": None,
                        "persistent_prepared_replenishment_fraction_raw": None,
                        "persistent_monthly_replenishment_fraction_scale": 100000,
                        "persistent_prepared_replenishment_fraction_scale": 100000})
    complete = raw["data_complete"] is True and len(records) == count
    return {"army_regiment_id": _i32(selected), "source": "native_all_data_records",
            "status": "partial" if complete and records else "unavailable", "ready": False,
            "native_data_record_count": count, "unavailable_reason": "full_DATA_refill_operands_not_captured",
            "records": records, "native_loss_writer_skipped": raw["native_loss_writer_skipped"],
            "loss_writer_admission_unavailable_reason": None if raw["native_loss_writer_skipped"] is not None else
                                                        "copied_native_writer_admission_missing"}


def _loss_inputs(raw, regiments):
    groups = []
    for group in raw["groups"]:
        counts = []
        for army in group["army_occurrences"]:
            requested = army["resolution"]["requested_full_id_u32"]
            resolution = _resolution(army["resolution"], requested)
            roster = army["regiment_roster"]
            rows = []
            for index, full_id in enumerate(roster["ordered_full_ids_u32"]):
                regiment = regiments.get(full_id) or {}
                rows.append({"native_index": index, "raw_full_id_u32": full_id,
                             "resolution": _resolution(regiment.get("resolution"), full_id),
                             "identity_valid": regiment.get("identity_valid"),
                             "current_soldiers": regiment.get("current_soldiers"),
                             "maximum_soldiers": regiment.get("maximum_soldiers")})
            whole = army["native_whole_current_soldiers"]
            ready = (resolution["ready"] and type(whole) is int and roster["references_complete"] is True and
                     roster["count_raw_i32"] == len(rows) and all(
                         row["resolution"]["ready"] and row["identity_valid"] is not None for row in rows))
            counts.append({**_state(ready, "copied_whole_Army_count_or_roster_missing"),
                           "native_index": army["native_index"], "raw_full_id_u32": requested,
                           "resolution": resolution, "native_whole_current_soldiers": whole, "regiments": rows})
        groups.append({**_state(False, "entry_full_B_and_Siege_percentage_operands_not_captured"),
                       "native_index": group["native_index"], "physical_slot_i64": group["physical_slot_i64"],
                       "native_current_expected_loss": None, "province_magic_raw_u32": group["province_magic_raw_u32"],
                       "besieging_inputs_v1": None, "army_counts": counts})
    targets = []
    for raw_regiment in regiments.values():
        if raw_regiment is None:
            continue
        resolution = _resolution(raw_regiment["resolution"], raw_regiment["resolution"]["requested_full_id_u32"])
        targets.append({**_state(False, "complete_conditional_writer_DATA_context_not_captured"),
                        "resolution": resolution, "identity_valid": raw_regiment["identity_valid"],
                        "current_soldiers": raw_regiment["current_soldiers"],
                        "maximum_soldiers": raw_regiment["maximum_soldiers"],
                        "native_loss_writer_skipped": raw_regiment["native_loss_writer_skipped"],
                        "replenishment_records_v1": _data(raw_regiment)})
    return normalize_current_daily_assault_loss_inputs_v1({
        **_state(False, "prior_write_and_full_B_contract_not_captured"), "schema_version": 1,
        "source": "native_current_daily_assault_loss_inputs", "stage": "observed_current_daily_assault_table",
        "groups": groups, "target_regiments": targets})


def _stage(event, phase_record, missing):
    parent = event["parent"]
    admitted = (event["capture_stage"] == "natural_2A97EB0_entry_and_return" and
                parent["actual_entry_rva"] == 0x2A97EB0 and parent["caller_return_rva"] == 0x2A9A8EA and
                parent["exact_post_date_parent"] is True and event["current_session_guard"] is True and
                event["actual"] is True and event["original_called"] is True and event["original_returned"] is True and
                _identity(parent["manager_identity"]) is not None and
                _ordered(parent["phase_entry_event"], parent["entry_event"]) and
                _ordered(parent["entry_event"], event["returned_event"]))
    if not admitted:
        missing.append("exact_natural_consumer_entry_return_clock_thread_parent_binding")
    if not isinstance(phase_record, Mapping):
        missing.append("exact_post_date_phase_record")
        return None
    scope = phase_record["scope"]
    joined = (scope["observed"] is True and scope["phase"] == "post_date" and
              scope["actual_entry_rva"] == 0x2A9A570 and
              scope["primary_manager_identity"] == parent["manager_identity"] and
              scope["entry_event"] == parent["phase_entry_event"] and
              scope["date_raw"] == parent["date_raw"] and scope["absolute_day_raw"] == parent["absolute_day_raw"] and
              phase_record["original_called"] is True and phase_record["original_returned"] is True and
              _ordered(event["returned_event"], phase_record["returned_event"]))
    if not joined:
        missing.append("exact_post_date_phase_token_manager_date_join")
    if not admitted or not joined:
        return None
    clock, sequence, thread = _token(parent["entry_event"])
    return {"stage_id": f"actual_assault_consumer_entry_12004:{hex(clock)}:{sequence}:{thread}",
            "capture_id": f"army_phase_clock:{hex(clock)}:{sequence}:{thread}",
            "manager_identity": _identity(parent["manager_identity"]), "basis": _BASIS,
            "physical_overlay_complete_for_prior_writes": False,
            "cache_overlay_complete_for_prior_writes": False,
            "physical_chunks": [], "regiment_currents": [], "group_budget_outputs": [],
            "full_besieging_dependencies_captured": False,
            "entry_event": deepcopy(parent["entry_event"]),
            "phase_entry_event": deepcopy(parent["phase_entry_event"])}


def map_actual_assault_consumer_stage_12004(event, phase_record) -> dict:
    """Return private conditional inputs; preserve every partial copied fact.

    ``event`` is the strict 37b owned event, and ``phase_record`` is its exact
    33 post-date record or None. Current query families never fill historical
    operands. Only a complete empty entry census bypasses absent overlays.
    """
    if not isinstance(event, Mapping):
        return {"army": None, "stage": None, "missing": ["owned_actual_assault_consumer_event"]}
    missing = []
    regiments = _regiment_map(event["entry_regiments"], missing)
    manager = _identity(event["parent"]["manager_identity"])
    table = _table(event["entry_table"], manager, regiments)
    army = {"army_id": None, "current_daily_assault_table_v1": table,
            "current_daily_assault_loss_inputs_v1": _loss_inputs(event["entry_table"], regiments),
            "actual_assault_consumer_copied_input_12004": deepcopy(dict(event))}
    stage = _stage(event, phase_record, missing)
    empty = table["physical_scan_ready"] and table["header"]["occupied_count_raw_i32"] == 0 and not table["groups"]
    if not table["physical_scan_ready"]:
        missing.append("complete_owned_entry_physical_group_census")
    if not empty:
        missing.extend(("physical_overlay_complete_for_prior_writes", "cache_overlay_complete_for_prior_writes",
                        "complete_entry_group_Province_B_and_actual_Siege_context"))
    return {"army": army, "stage": stage, "missing": list(dict.fromkeys(missing))}
