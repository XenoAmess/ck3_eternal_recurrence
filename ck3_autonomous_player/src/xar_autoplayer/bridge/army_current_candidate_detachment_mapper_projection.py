"""Initial current candidate mapper preview with no detach or lifecycle writes."""
from __future__ import annotations

from copy import deepcopy
from typing import Mapping

_REGI = 0x52656769
_INVALID = 0xFFFFFFFF


def _i32(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < 1 << 31


def _u32(value: object) -> bool:
    return type(value) is int and 0 <= value < 1 << 32


def _identity(value: object) -> bool:
    return type(value) is str and bool(value)


def _wrap_i32(value: int) -> int:
    return ((value + (1 << 31)) % (1 << 32)) - (1 << 31)


def _count(row: Mapping) -> dict:
    result = {"native_index": row.get("native_index"), "regi_identity": row.get("regi_identity"),
        "observed_count_base_128_raw_i32": row.get("count_base_128_raw_i32"),
        "count_ready": False, "signed_count_i32": None, "chunk_projections": [],
        "missing_inputs": [], "input_basis": "current_physical_Regi128_and_seven_chunks"}
    base = row.get("count_base_128_raw_i32")
    if not _i32(base):
        result["missing_inputs"].append("count_base_128_raw_i32")
    chunks = row.get("chunks")
    indexed = {item.get("physical_index"): item for item in chunks if isinstance(item, Mapping)} if isinstance(chunks, list) else {}
    total = base if _i32(base) else None
    for index in range(7):
        raw = indexed.get(index)
        item = {"physical_index": index, "delta_ready": False, "delta_i32": None,
                "branch": None, "missing_inputs": []}
        if not isinstance(raw, Mapping):
            item["missing_inputs"].append("physical_chunk")
        else:
            maximum, current, state = (raw.get(name) for name in
                ("maximum_00_raw_i32", "current_04_raw_i32", "state_18_raw_i32"))
            if not _i32(maximum):
                item["missing_inputs"].append("maximum_00_raw_i32")
            elif maximum == 0:
                item.update(delta_ready=True, delta_i32=0, branch="maximum_zero_skip")
            elif not _i32(current):
                item["missing_inputs"].append("current_04_raw_i32")
            elif current != 0:
                item.update(delta_ready=True, delta_i32=_wrap_i32(current - maximum),
                            branch="nonzero_current_difference")
            elif not _i32(state):
                item["missing_inputs"].append("state_18_raw_i32_for_zero_current")
            elif state == 3:
                item.update(delta_ready=True, delta_i32=0, branch="state3_zero_current_skip")
            else:
                item.update(delta_ready=True, delta_i32=_wrap_i32(-maximum), branch="zero_current_difference")
        if total is not None and item["delta_ready"]:
            total = _wrap_i32(total + item["delta_i32"])
        elif not item["delta_ready"]:
            total = None
        result["chunk_projections"].append(item)
        result["missing_inputs"].extend(f"chunks[{index}].{field}" for field in item["missing_inputs"])
    result.update(count_ready=total is not None, signed_count_i32=total)
    return result


def _mapper(row: Mapping, counts: Mapping, count_cache: dict) -> dict:
    result = {"native_index": row.get("native_index"), "arrg_identity": row.get("arrg_identity"),
        "kind_14c_raw_i32": row.get("kind_14c_raw_i32"), "data_count_raw_i32": row.get("data_count_raw_i32"),
        "source_requested_regi_full_id_u32": None, "selected_regi_identity_valid": None,
        "return_branch_ready": False, "return_selection_ready": False, "return_selection": None,
        "returned_regi_identity": None, "count_demanded": False, "count_input_index": None,
        "count_projection": None, "caller_state_ready": False, "returned_state_138_raw_i32": None,
        "state4_branch_admitted": None, "preview_ready": False, "missing_inputs": [],
        "observed_return_selection": row.get("return_selection"),
        "observed_returned_regi_identity": row.get("returned_regi_identity"),
        "observed_returned_regi_full_id_u32": row.get("returned_regi_full_id_u32"),
        "observed_returned_regi_magic_14_raw_u32": row.get("returned_regi_magic_14_raw_u32"),
        "input_basis": "source2A977A0_from_same_capture_raw_operands"}

    def missing(field):
        result["missing_inputs"].append(field)
        return result

    kind = row.get("kind_14c_raw_i32")
    if not _i32(kind):
        return missing("kind_14c_raw_i32")
    selected_identity = None
    choice = "native_fallback"
    if kind in (1, 4):
        size = row.get("data_count_raw_i32")
        if not _i32(size):
            return missing("data_count_raw_i32")
        if size == 0:
            requested = _INVALID
        else:
            requested = row.get("first_regi_full_id_u32")
            if not _u32(requested):
                return missing("first_data_record_regi_id_8_for_nonzero_count")
        result["source_requested_regi_full_id_u32"] = requested
        resolution = row.get("selected_regi_resolution")
        if not isinstance(resolution, Mapping):
            return missing("selected_regi_resolution")
        if resolution.get("requested_full_id_u32") != requested:
            return missing("selected_regi_resolution_actual_requested_full_id")
        selected_id = resolution.get("selected_full_id_u32")
        selected_identity = resolution.get("object_identity")
        magic = row.get("selected_regi_magic_14_raw_u32")
        if (_u32(magic) and magic != _REGI) or selected_id == _INVALID:
            valid = False
        elif magic == _REGI and _u32(selected_id):
            valid = True
        else:
            return missing("selected_regi_magic_14_and_full_id_10")
        result["selected_regi_identity_valid"] = valid
        if valid:
            if not _identity(selected_identity):
                return missing("selected_regi_physical_identity")
            choice = "selected_regi"
            if kind == 1:
                result["count_demanded"] = True
                count_index = row.get("count_input_index")
                result["count_input_index"] = count_index
                count_row = counts.get(count_index)
                if not isinstance(count_row, Mapping):
                    return missing("selected_kind1_count_input")
                if count_row.get("regi_identity") != selected_identity:
                    return missing("count_input_selected_physical_Regi_identity")
                if count_index not in count_cache:
                    count_cache[count_index] = _count(count_row)
                computed = count_cache[count_index]
                result["count_projection"] = deepcopy(computed)
                if not computed["count_ready"]:
                    result["missing_inputs"].extend("count." + name for name in computed["missing_inputs"])
                    return result
                if computed["signed_count_i32"] > 0:
                    choice = "native_fallback"
    result.update(return_branch_ready=True, return_selection=choice)
    returned = selected_identity if choice == "selected_regi" else row.get("fallback_regi_identity")
    if not _identity(returned):
        return missing("fallback_regi_identity" if choice == "native_fallback" else "selected_regi_physical_identity")
    result.update(return_selection_ready=True, returned_regi_identity=returned)
    # State138 is attributed to the actual returned pointer. Its extra ID/magic
    # are provenance fields and are never an identity gate in this caller.
    if row.get("returned_regi_identity") != returned:
        return missing("returned_state_capture_matches_source_selected_pointer")
    state = row.get("returned_state_138_raw_i32")
    if not _i32(state):
        return missing("returned_state_138_raw_i32")
    result.update(caller_state_ready=True, returned_state_138_raw_i32=state,
                  state4_branch_admitted=state == 4, preview_ready=True)
    return result


def project_current_candidate_detachment_mapper(inputs: Mapping | None) -> dict:
    """Preview every initial stored ArRg occurrence using shared physical snapshots."""
    result = {"projection_kind": "current_candidate_detachment_mapper_preview",
        "source_contract_game_version": "1.20.0.3", "native_mapper_rva": "0x2A977A0",
        "native_count_rva": "0x262BBC0", "input_basis": "initial_current_first_candidate_seed_only",
        "status": "unavailable", "initial_current_seed_ready": False,
        "selection_ready": False, "selection_branch": None, "roster_ready": False,
        "roster_count_raw_i32": None, "roster_data_present": None, "roster_data_identity": None,
        "candidate_reference_native_index": None, "candidate_pending_native_index": None,
        "candidate_raw_full_id_u32": None, "candidate_actual_full_id_u32": None,
        "candidate_army_identity": None, "occurrences": [], "mapper_results": [],
        "count_results": [], "missing_inputs": [], "actual_effects": False,
        "actual_detachment": False, "actual_post_stage": None,
        "future_drain_ready": False, "full_army_lifecycle_ready": False,
        "full_monthly_ready": False, "full_calendar_ready": False, "live": False,
        "native_writes_executed": 0}
    if not isinstance(inputs, Mapping):
        result["missing_inputs"].append("current_candidate_detachment_mapper_inputs_v1")
        return result
    for field in ("selection_ready", "selection_branch", "roster_count_raw_i32", "roster_data_present",
                  "roster_data_identity", "candidate_reference_native_index", "candidate_pending_native_index",
                  "candidate_raw_full_id_u32", "candidate_actual_full_id_u32", "candidate_army_identity"):
        result[field] = inputs.get(field)
    if inputs.get("selection_ready") is not True:
        result["missing_inputs"].append("initial_current_candidate_selection")
        return result
    if inputs.get("selection_branch") == "not_called":
        result.update(status="available", initial_current_seed_ready=True, roster_ready=True)
        return result
    if inputs.get("selection_branch") != "first_valid_current_receiver":
        result["missing_inputs"].append("initial_current_candidate_selection_branch")
        return result
    count = inputs.get("roster_count_raw_i32")
    if not _i32(count):
        result["missing_inputs"].append("roster_count_raw_i32")
        return result
    # This is an initial forward stored-index preview, not replay of the outer
    # native cursor whose original end and payload can be changed by cleanup.
    if count <= 0:
        result.update(status="available", initial_current_seed_ready=True, roster_ready=True)
        return result
    occurrences = inputs.get("occurrences")
    occurrences = occurrences if isinstance(occurrences, list) else []
    observed = {row.get("native_index"): row for row in occurrences if isinstance(row, Mapping)}
    mapper_rows = inputs.get("mappers")
    mapper_rows = mapper_rows if isinstance(mapper_rows, list) else []
    mappers = {row.get("native_index"): row for row in mapper_rows if isinstance(row, Mapping)}
    count_rows = inputs.get("count_inputs")
    count_rows = count_rows if isinstance(count_rows, list) else []
    counts = {row.get("native_index"): row for row in count_rows if isinstance(row, Mapping)}
    mapper_cache, count_cache = {}, {}
    roster_ready = (inputs.get("roster_data_present") is True
                    and sorted(observed) == list(range(count)))
    if inputs.get("roster_data_present") is not True:
        result["missing_inputs"].append("current_candidate_roster_data_pointer")
    for index in range(count):
        row = observed.get(index)
        item = {"native_index": index, "raw_full_id_u32": None,
                "resolved_arrg_identity": None, "mapper_index": None,
                "preview_ready": False, "mapper_projection": None, "missing_inputs": []}
        if not isinstance(row, Mapping):
            item["missing_inputs"].append("observed_raw_ArRg_occurrence")
        else:
            raw_id = row.get("raw_full_id_u32")
            item.update(raw_full_id_u32=raw_id, mapper_index=row.get("mapper_index"))
            resolution = row.get("resolution")
            identity = resolution.get("object_identity") if isinstance(resolution, Mapping) else None
            item["resolved_arrg_identity"] = identity
            if not _u32(raw_id):
                item["missing_inputs"].append("raw_full_id_u32")
                roster_ready = False
            elif not isinstance(resolution, Mapping) or resolution.get("ready") is not True or not _identity(identity):
                item["missing_inputs"].append("current_ArRg_registry_or_fallback_resolution")
            else:
                mapper_index = row.get("mapper_index")
                mapper_row = mappers.get(mapper_index)
                if not isinstance(mapper_row, Mapping):
                    item["missing_inputs"].append("physical_ArRg_mapper_snapshot")
                elif mapper_row.get("arrg_identity") != identity:
                    item["missing_inputs"].append("mapper_resolved_physical_ArRg_identity")
                else:
                    if mapper_index not in mapper_cache:
                        mapper_cache[mapper_index] = _mapper(mapper_row, counts, count_cache)
                    mapped = mapper_cache[mapper_index]
                    item.update(preview_ready=mapped["preview_ready"], mapper_projection=deepcopy(mapped))
                    item["missing_inputs"].extend(mapped["missing_inputs"])
        result["occurrences"].append(item)
        result["missing_inputs"].extend(f"occurrences[{index}].{name}" for name in item["missing_inputs"])
    result["mapper_results"] = list(mapper_cache.values())
    result["count_results"] = list(count_cache.values())
    ready = roster_ready and all(row["preview_ready"] for row in result["occurrences"])
    result.update(roster_ready=roster_ready, initial_current_seed_ready=ready,
                  status="available" if ready else "partial")
    return result
