"""Bounded same-preview P return evidence; Q remains source inference only."""
from __future__ import annotations

RETURNS = (0x24E22B3, 0x24E22F1, 0x24E2348)
_FLAGS = ("hook_installed", "scope_entered", "same_thread", "order_valid", "native_predicate_returned")
_KEYS = {"schema_version", "source", "status", "unavailable_reason", *_FLAGS,
         "final_condition_passes", "ignored_foreign_calls", "ignored_nested_calls",
         "stages", "additional_native_predicate_calls", "neighbor_Q_observed"}


def normalize_county_predicate_trace_v1(value, *, parent):
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("county P trace schema is malformed")
    if (type(value["schema_version"]) is not int or value["schema_version"] != 1
            or value["source"] != "same_preview_native_P_returns_12004"):
        raise ValueError("county P trace source/version is malformed")
    for key in (*_FLAGS, "neighbor_Q_observed"):
        if type(value[key]) is not bool:
            raise ValueError("county P trace flags must be boolean")
    if (type(value["additional_native_predicate_calls"]) is not int
            or value["additional_native_predicate_calls"] != 0 or value["neighbor_Q_observed"]):
        raise ValueError("county P trace adds no calls and does not observe Q")
    for key in ("ignored_foreign_calls", "ignored_nested_calls"):
        if type(value[key]) is not int or not 0 <= value[key] < 1 << 32:
            raise ValueError("county P trace counts must be uint32")
    final = value["final_condition_passes"]
    if final is not None and type(final) is not bool:
        raise ValueError("county P trace final bool must be bool or null")
    if final is not None and final is not parent["native_condition_passes"]:
        raise ValueError("county P trace final bool differs from native parent")
    stages = value["stages"]
    if not isinstance(stages, list) or len(stages) != 3:
        raise ValueError("county P trace requires exactly three fixed stages")
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict) or set(stage) != {
                "call_count", "actual_caller_return_rva", "argument_identity_matched", "returned"}:
            raise ValueError("county P stage schema is malformed")
        count = stage["call_count"]
        if type(count) is not int or not 0 <= count < 1 << 32:
            raise ValueError("county P stage count must be uint32")
        for key in ("argument_identity_matched", "returned"):
            if stage[key] is not None and type(stage[key]) is not bool:
                raise ValueError("county P stage bool must be bool or null")
        actual = stage["actual_caller_return_rva"]
        if count == 0:
            if any(stage[k] is not None for k in ("actual_caller_return_rva", "argument_identity_matched", "returned")):
                raise ValueError("uncalled county P stage has no result or caller")
        elif type(actual) is not int or actual != RETURNS[index]:
            raise ValueError("county P stage actual native return source differs")
    ready = value["status"] == "available"
    if ready:
        if (value["unavailable_reason"] is not None or not all(value[k] for k in _FLAGS)
                or parent["status"] != "available" or parent["mode"] != 1
                or type(final) is not bool):
            raise ValueError("available county P trace requires complete same-preview mode1 evidence")
        for stage in stages:
            if stage["call_count"] > 1 or (stage["call_count"] == 1 and
                    (type(stage["returned"]) is not bool or stage["argument_identity_matched"] is not True)):
                raise ValueError("available county P stage requires one complete actual return")
        expected = (bool(parent["source_definition_1b_u8"] and parent["target_definition_1b_u8"]
                         and parent["source_county_present"] and parent["county_objects_differ"]),
                    stages[0]["returned"] is True and parent["target_county_present"],
                    stages[1]["returned"] is True and parent["target_county_magic_3e0_u32"] == 0x436F4461)
        if any((stage["call_count"] == 1) != reach for stage, reach in zip(stages, expected)):
            raise ValueError("county P trace does not cover the source-proven short-circuit order")
        if final and not all(stage["returned"] is True for stage in stages):
            raise ValueError("native true contradicts actual mode1 P returns")
    elif (value["status"] != "unavailable" or not isinstance(value["unavailable_reason"], str)
          or not value["unavailable_reason"]):
        raise ValueError("unavailable county P trace requires a reason")
    return {**value, "stages": [dict(stage) for stage in stages]}


def explain_county_predicate_trace_v1(parent):
    """No Move selector: expose one falsifiable branch fact or a bounded residual."""
    trace = parent.get("predicate_trace_v1")
    if trace is None:
        return {"status": "unavailable", "reason": "county_P_trace_absent", "Q_observed": False}
    trace = normalize_county_predicate_trace_v1(trace, parent=parent)
    if trace["status"] != "available":
        return {"status": "unavailable", "reason": trace["unavailable_reason"], "Q_observed": False}
    for label, stage in zip(("source_P", "target_P_first", "target_P_second"), trace["stages"]):
        if stage["returned"] is False:
            return {"status": "observed", "reason": label + "_returned_false",
                    "actual_caller_return_rva": stage["actual_caller_return_rva"], "Q_observed": False}
    if all(stage["returned"] is True for stage in trace["stages"]):
        return {"status": "source_inference", "reason": "P_chain_passed_final_true" if trace["final_condition_passes"]
                else "P_chain_passed_neighbor_chain_rejected", "Q_observed": False,
                "specific_neighbor_or_Q_result": None}
    return {"status": "observed", "reason": "P_chain_not_reached_or_stopped_at_common_gate", "Q_observed": False}
