"""Conditional, normal-return placement prefix for the exact .3 assault table.

Requests supply an already selected Army/Siege/ArRg append stream. This module
does not replay admission, earlier callbacks, allocator callbacks or a day tick.
The current observation remains separate from the explicitly staged model.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
import math
import struct


CONDITIONAL_PLACEMENT_STAGE_12003 = "conditional_pre_2A99B40_placement_state"
_ALLOCATOR_RVAS = {"armies": 0x54E0570, "arrgs": 0x54DEB68}


def _u32(value: object, name: str) -> None:
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"{name} must retain a full unsigned DWORD")


def _provenance(value: object) -> None:
    if not ((isinstance(value, Mapping) and bool(value))
            or (isinstance(value, str) and bool(value))):
        raise ValueError("Source provenance must be explicit nonempty text or a mapping")


@dataclass(frozen=True, slots=True)
class ExplicitDailyAssaultPlacementStage12003:
    """Bind the supplied current table to a conditional pre-placement baseline."""

    stage: str
    source_provenance: object

    def __post_init__(self) -> None:
        if self.stage != CONDITIONAL_PLACEMENT_STAGE_12003:
            raise ValueError("The input stage must explicitly identify the conditional placement baseline")
        _provenance(self.source_provenance)


@dataclass(frozen=True, slots=True)
class DailyAssaultPlacementRequest12003:
    """An explicit source-bound append request; admission is a supplied premise."""

    siege_full_id_u32: int
    army_full_id_u32: int
    arrg_full_ids_u32: tuple[int, ...]
    source_provenance: object

    def __post_init__(self) -> None:
        _u32(self.siege_full_id_u32, "siege_full_id_u32")
        _u32(self.army_full_id_u32, "army_full_id_u32")
        if not isinstance(self.arrg_full_ids_u32, tuple):
            raise ValueError("ArRg references must be an ordered tuple")
        for value in self.arrg_full_ids_u32:
            _u32(value, "arrg_full_ids_u32 occurrence")
        _provenance(self.source_provenance)


def _wrap_i32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _f32(value: float | int) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _load_growth_selected(count: int, mask: int, threshold_bits: int) -> bool:
    numerator, denominator = _f32(_wrap_i32(count + 1)), _f32(mask)
    if denominator == 0:
        ratio = math.nan if numerator == 0 else math.copysign(math.inf, numerator)
    else:
        ratio = _f32(numerator / denominator)
    threshold = struct.unpack("<f", struct.pack("<I", threshold_bits))[0]
    # COMISS/JA selects growth only for an ordered, strictly greater result.
    return ratio > threshold


def _full_id_hash(full_id: int) -> int:
    result = 0x811C9DC5
    for shift in (0, 8, 16, 24):
        result = ((result ^ ((full_id >> shift) & 0xFF)) * 0x01000193) & 0xFFFFFFFF
    return result


def _observed_group(group: Mapping) -> dict:
    result = {
        "physical_slot_i64": group["physical_slot_i64"],
        "hash_raw_u32": group["hash_raw_u32"],
        "control_raw_u8": group["control_raw_u8"],
        "siege_full_id_u32": group["siege_full_id_u32"],
        "source_kind": "conditional_baseline_from_observed_current_group",
        "source_ledger": [{"source": "observed_current_daily_assault_table",
                           "physical_slot_i64": group["physical_slot_i64"],
                           "native_index": group["native_index"]}],
        "allocator_provenance": {}, "reference_source_ledger": {},
    }
    for name, output in (("armies", "army_full_ids_u32"), ("arrgs", "arrg_full_ids_u32")):
        vector = group[name]
        result[output] = [row["raw_full_id_u32"] for row in vector["occurrences"]]
        result[name + "_references_ready"] = vector["references_ready"]
        result["reference_source_ledger"][name] = [
            {"source": "observed_current_vector_occurrence",
             "physical_slot_i64": group["physical_slot_i64"],
             "native_index": row["native_index"], "raw_full_id_u32": row["raw_full_id_u32"]}
            for row in vector["occurrences"]]
        result["allocator_provenance"][name] = {
            "kind": "actual_read_witness",
            "witness": deepcopy(vector.get("allocator_witness")),
        }
    return result


def _literal_allocators(source: str, upstream: dict | None = None) -> dict:
    return {name: {"kind": "source_derived_normal_return_literal_initializer",
                   "source": source, "expected_rva_u32": rva,
                   "actual_native_read": False,
                   "upstream_provenance": deepcopy(upstream.get(name)) if upstream else None}
            for name, rva in _ALLOCATOR_RVAS.items()}


def _matched_allocator(group: dict, name: str) -> bool:
    proof = group["allocator_provenance"][name]
    if proof["kind"] == "source_derived_normal_return_literal_initializer":
        return proof["expected_rva_u32"] == _ALLOCATOR_RVAS[name]
    witness = proof["witness"]
    return (isinstance(witness, Mapping)
            and witness.get("ready") is True
            and witness.get("actual_read_ready") is True
            and witness.get("matches_expected") is True
            and witness.get("expected_rva_u32") == _ALLOCATOR_RVAS[name])


def _references_ready(group: dict) -> bool:
    return group["armies_references_ready"] and group["arrgs_references_ready"]


def _append(group: dict, request: DailyAssaultPlacementRequest12003, index: int) -> None:
    group["army_full_ids_u32"].append(request.army_full_id_u32)
    group["arrg_full_ids_u32"].extend(request.arrg_full_ids_u32)
    group["reference_source_ledger"]["armies"].append({
        "source": "supplied_conditional_request", "request_index": index,
        "supplied_occurrence_index": 0, "raw_full_id_u32": request.army_full_id_u32,
    })
    group["reference_source_ledger"]["arrgs"].extend({
        "source": "supplied_conditional_request", "request_index": index,
        "supplied_occurrence_index": ordinal, "raw_full_id_u32": value,
    } for ordinal, value in enumerate(request.arrg_full_ids_u32))
    group["source_ledger"].append({"source": "2A99B40 ordered append premise",
                                    "request_index": index,
                                    "source_provenance": deepcopy(request.source_provenance)})


def _empty_group(slot: int, control: int, full_hash: int,
                 request: DailyAssaultPlacementRequest12003, index: int, branch: str) -> dict:
    return {
        "physical_slot_i64": slot, "hash_raw_u32": full_hash,
        "control_raw_u8": control, "siege_full_id_u32": request.siege_full_id_u32,
        "source_kind": "conditional_inserted_group",
        "army_full_ids_u32": [], "arrg_full_ids_u32": [],
        "armies_references_ready": True, "arrgs_references_ready": True,
        "source_ledger": [{"source": "2AA2030 logical empty insertion",
                           "branch": branch, "request_index": index,
                           "source_provenance": deepcopy(request.source_provenance)}],
        "reference_source_ledger": {"armies": [], "arrgs": []},
        "allocator_provenance": _literal_allocators(
            "2AA20BD..2AA2100" if branch == "direct_empty" else "2AA35C0"),
    }


def project_daily_assault_placement_prefix_12003(
    normalized_table: Mapping | None,
    requests: Sequence[DailyAssaultPlacementRequest12003], *,
    input_stage: ExplicitDailyAssaultPlacementStage12003,
) -> dict:
    """Model the continuous supported request prefix, without native mutation.

    Every modeled call is conditional on normal return. An unsupported request
    is left unapplied; earlier supported requests and current observations are
    retained. Literal allocators constructed within that prefix are source facts,
    separate from actual allocator reads on its observed baseline. No result
    identifies the actual next callback's state, roster, or complete day outcome.
    ``ready`` reports completion of the supplied request prefix; group census
    and complete reference readiness remain independently reported.
    """
    if not isinstance(input_stage, ExplicitDailyAssaultPlacementStage12003):
        raise ValueError("An explicit conditional placement stage is required")
    requests = tuple(requests)
    if any(not isinstance(row, DailyAssaultPlacementRequest12003) for row in requests):
        raise ValueError("Placement requests must retain their explicit source-bound type")
    if normalized_table is not None and (
            not isinstance(normalized_table, Mapping)
            or normalized_table.get("source") != "native_current_daily_assault_table"
            or normalized_table.get("stage") != "observed_current_daily_assault_table"):
        raise ValueError("Input must be the normalized genuine current table")
    ledger = [{"request_index": index, "siege_full_id_u32": row.siege_full_id_u32,
               "army_full_id_u32": row.army_full_id_u32,
               "arrg_full_ids_u32": list(row.arrg_full_ids_u32),
               "source_provenance": deepcopy(row.source_provenance),
               "status": "not_reached", "branch": None, "unavailable_reason": None,
               "probe_ledger": []} for index, row in enumerate(requests)]
    result = {
        "schema_version": 1, "source": "source_bound_daily_assault_placement_prefix",
        "source_contract_game_version": "1.20.0.3",
        "input_stage": {"stage": input_stage.stage,
                        "source_provenance": deepcopy(input_stage.source_provenance)},
        "normal_return_premise": True,
        "status": "unavailable", "ready": False, "unavailable_reason": None,
        "conditional_placement_ready": False,
        "actual_next_callback_ready": False, "full_future_table_placement_ready": False,
        "supplied_request_count": len(requests), "applied_request_count": 0,
        "stop_request_index": None, "stop_branch": None, "request_ledger": ledger,
        "observed_current_table": deepcopy(dict(normalized_table)) if normalized_table is not None else None,
        "projected_header": None, "projected_physical_controls": [], "projected_groups": [],
        "projected_physical_group_order_ready": False, "projected_groups_ready": False,
        "admission_replayed": False, "native_writes_executed": 0,
        "full_daily": False, "full_monthly": False,
    }
    if normalized_table is None:
        result["unavailable_reason"] = "current_daily_assault_table_unavailable"
        return result
    observed_header = normalized_table["header"]
    header = {field: observed_header[field] for field in (
        "occupied_count_raw_i32", "mask_raw_i32", "tail_distance_raw_u8",
        "load_factor_f32_bits_u32", "end_slot_raw_i32", "end_marker_control_raw_u8")}
    controls = {row["physical_slot_i64"]: row["control_raw_u8"]
                for row in normalized_table["physical_controls"]}
    groups = {row["physical_slot_i64"]: _observed_group(row) for row in normalized_table["groups"]}

    def stop(index: int, branch: str) -> None:
        result.update(stop_request_index=index, stop_branch=branch, unavailable_reason=branch)
        ledger[index].update(status="partial", branch=branch, unavailable_reason=branch)

    for index, request in enumerate(requests):
        row = ledger[index]
        mask = header["mask_raw_i32"]
        if mask is None:
            stop(index, "probe_mask_unobserved")
            break
        full_hash = _full_id_hash(request.siege_full_id_u32)
        slot, distance, hit = _wrap_i32(full_hash & (mask & 0xFFFFFFFF)), 1, False
        row.update(hash_raw_u32=full_hash, home_slot_i64=slot)
        while True:
            control = controls.get(slot)
            row["probe_ledger"].append({"physical_slot_i64": slot,
                                         "distance_raw_u8": distance, "control_raw_u8": control})
            if control is None:
                stop(index, "probe_control_unobserved")
                break
            if control < distance:
                break
            group = groups.get(slot)
            if group is None or group["siege_full_id_u32"] is None:
                stop(index, "probe_full_key_unobserved")
                break
            if group["siege_full_id_u32"] == request.siege_full_id_u32:
                hit = True
                break
            distance, slot = (distance + 1) & 0xFF, slot + 1
        if result["stop_request_index"] is not None:
            break
        row["destination_slot_i64"] = slot
        if hit:
            if not _references_ready(groups[slot]):
                stop(index, "key_hit_reference_lists_unobserved")
                break
            branch = "key_hit"
        else:
            tail = header["tail_distance_raw_u8"]
            if tail is None:
                stop(index, "probe_tail_distance_unobserved")
                break
            if distance > tail:
                stop(index, "growth_tail_distance")
                break
            count, threshold = header["occupied_count_raw_i32"], header["load_factor_f32_bits_u32"]
            if count is None or threshold is None:
                stop(index, "growth_load_inputs_unobserved")
                break
            load_growth = _load_growth_selected(count, mask, threshold)
            row["growth_ledger"] = {"distance_raw_u8": distance, "tail_distance_raw_u8": tail,
                                     "occupied_count_before_raw_i32": count,
                                     "occupied_plus_one_raw_i32": _wrap_i32(count + 1),
                                     "mask_raw_i32": mask, "load_factor_f32_bits_u32": threshold,
                                     "load_growth_selected": load_growth}
            if load_growth:
                stop(index, "growth_load_factor")
                break
            if controls[slot] == 0:
                branch = "direct_empty"
            else:
                next_control = controls.get(slot + 1)
                if next_control is None:
                    stop(index, "collision_next_control_unobserved")
                    break
                if next_control != 0:
                    stop(index, "general_carried_collision_unmodeled")
                    break
                old = groups.get(slot)
                if old is None or old["hash_raw_u32"] is None or old["siege_full_id_u32"] is None or not _references_ready(old):
                    stop(index, "collision_old_group_value_unobserved")
                    break
                if not all(_matched_allocator(old, name) for name in _ALLOCATOR_RVAS):
                    stop(index, "collision_allocator_unread_or_mismatched")
                    break
                branch = "immediate_next_empty_matched_allocators"
                moved = deepcopy(old)
                moved.update(physical_slot_i64=slot + 1, control_raw_u8=(old["control_raw_u8"] + 1) & 0xFF)
                moved["source_ledger"].append({"source": "2AA212A..2AA214D normal-return header transfer",
                                               "request_index": index, "from_physical_slot_i64": slot,
                                               "to_physical_slot_i64": slot + 1})
                moved["allocator_provenance"] = _literal_allocators("2AA2450", old["allocator_provenance"])
                groups[slot + 1] = moved
                controls[slot + 1] = moved["control_raw_u8"]
                row["relocated_group"] = {"from_physical_slot_i64": slot, "to_physical_slot_i64": slot + 1,
                                          "siege_full_id_u32": old["siege_full_id_u32"]}
            groups[slot] = _empty_group(slot, distance, full_hash, request, index, branch)
            controls[slot] = distance
            header["occupied_count_raw_i32"] = _wrap_i32(count + 1)
        _append(groups[slot], request, index)
        row.update(status="available", branch=branch)
        result["applied_request_count"] += 1

    complete = result["stop_request_index"] is None
    projected = [groups[slot] for slot in sorted(groups)]
    physical_order_ready = normalized_table["physical_scan_ready"] or (
        observed_header["occupied_count_raw_i32"] == 0 and not normalized_table["groups"]
        and normalized_table["raw_groups_ready"])
    result.update(status="available" if complete else "partial", ready=complete,
                  conditional_placement_ready=complete,
                  projected_header=header,
                  projected_physical_controls=[{"physical_slot_i64": slot, "control_raw_u8": controls[slot]}
                                               for slot in sorted(controls)],
                  projected_groups=projected,
                  projected_physical_group_order_ready=physical_order_ready,
                  projected_groups_ready=physical_order_ready and all(
                      _references_ready(group) and group["hash_raw_u32"] is not None
                      and group["siege_full_id_u32"] is not None
                      and group["control_raw_u8"] is not None for group in projected))
    return result
