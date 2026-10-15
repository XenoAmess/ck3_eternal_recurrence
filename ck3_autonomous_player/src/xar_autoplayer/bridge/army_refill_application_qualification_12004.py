"""Qualify the evidence currently published for a natural regular-core event.

The existing producer observes callback entry/return, not the inline ADD. This
consumer deliberately has no successful path for instruction-local application
credit. A future writer producer needs its own source-bound transport contract.
"""
from __future__ import annotations

from collections.abc import Mapping


def qualify_regular_refill_application_12004(
    consumed: Mapping[str, object], *, exact_source: bool,
    observer_installed: bool,
) -> dict[str, object]:
    """Classify a normalized observed-phase record without changing its facts.

    ``raw_current_net`` is an arithmetic sum across unique physical seven-slot
    copies. It is neither gross positive ADD nor an Army/DATA aggregate. Journal
    continuity belongs to the caller's independently fenced observation window.
    """
    result: dict[str, object] = {
        "schema_version": 1,
        "source_contract_game_version": "1.20.0.4",
        "evidence_kind": "unavailable",
        "natural_core_return_observed": False,
        "subject_physical_net_ready": False,
        "raw_current_net": None,
        "raw_maximum_net": None,
        "unique_physical_objects": None,
        "actual_ADD_observed": False,
        "applied_positive_refill_soldiers": None,
        "no_ADD_proven": False,
        "toggle_effect_proven": False,
        "continuous_window_coverage_proven": False,
        "current_runtime_binding_proven": False,
        "conditional_projection_promoted": False,
        "missing_inputs": [],
    }
    missing: list[str] = []
    if exact_source is not True:
        missing.append("exact_actual4_query_source")
    if observer_installed is not True:
        missing.append("regular_core_observer_installed")
    if consumed.get("owned_original_return_observed") is not True:
        missing.append("independent_original_core_return")
    if missing:
        result["missing_inputs"] = missing
        return result
    result["natural_core_return_observed"] = True
    result["evidence_kind"] = "natural_core_return_only"
    raw = consumed.get("subject_raw_physical_delta_v1")
    if not isinstance(raw, Mapping) or raw.get("status") != "available":
        result["missing_inputs"] = ["complete_owned_subject_raw_physical_pair"]
        return result
    # These are the exact declarations of the existing raw-net consumer.
    # They cannot be overridden by a conditional projection or an extra flag.
    if (raw.get("basis") != "owned_same_core_entry_and_return_raw_physical_seven"
            or raw.get("actual_ADD_observed") is not False
            or raw.get("causal_attribution_ready") is not False
            or raw.get("conditional_entry_projection_used") is not False):
        result["missing_inputs"] = ["raw_pair_source_semantics"]
        return result
    objects = raw.get("physical_objects")
    if not isinstance(objects, list):
        result["missing_inputs"] = ["raw_pair_physical_objects"]
        return result
    seen: set[int] = set()
    current_net = maximum_net = 0
    for physical in objects:
        if not isinstance(physical, Mapping):
            missing.append("raw_pair_physical_object")
            break
        token = physical.get("physical_token")
        if type(token) is not int or token <= 0 or token in seen:
            missing.append("raw_pair_unique_physical_token")
            break
        seen.add(token)
        chunks = physical.get("chunks")
        if not isinstance(chunks, list) or len(chunks) != 7:
            missing.append("raw_pair_complete_physical_seven")
            break
        for index, chunk in enumerate(chunks):
            if not isinstance(chunk, Mapping) or chunk.get("physical_index") != index:
                missing.append("raw_pair_physical_slot_order")
                break
            first, last = chunk.get("before_raw"), chunk.get("returned_raw")
            if not isinstance(first, Mapping) or not isinstance(last, Mapping):
                missing.append("raw_pair_independent_endpoints")
                break
            for field, delta_key in (
                ("current_soldiers", "delta_current_soldiers"),
                ("maximum_soldiers", "delta_maximum_soldiers"),
            ):
                left, right = first.get(field), last.get(field)
                if (type(left) is not int or type(right) is not int
                        or not -(1 << 31) <= left < (1 << 31)
                        or not -(1 << 31) <= right < (1 << 31)
                        or type(chunk.get(delta_key)) is not int
                        or chunk[delta_key] != right - left):
                    missing.append("raw_pair_exact_signed_endpoint_difference")
                    break
            if missing:
                break
            current_net += chunk["delta_current_soldiers"]
            maximum_net += chunk["delta_maximum_soldiers"]
        if missing:
            break
    if missing:
        result["missing_inputs"] = list(dict.fromkeys(missing))
        return result
    result.update(
        evidence_kind="natural_core_subject_physical_net",
        subject_physical_net_ready=True,
        raw_current_net=current_net,
        raw_maximum_net=maximum_net,
        unique_physical_objects=len(seen),
        missing_inputs=["instruction_local_ADD_producer_not_published"],
    )
    return result
