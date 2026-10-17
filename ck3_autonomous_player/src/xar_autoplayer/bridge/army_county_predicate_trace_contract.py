"""Bounded same-preview P return evidence; Q remains source inference only."""
from __future__ import annotations

RETURNS = (0x24E22B3, 0x24E22F1, 0x24E2348)
_FLAGS = ("hook_installed", "scope_entered", "same_thread", "order_valid", "native_predicate_returned")
_KEYS = {"schema_version", "source", "status", "unavailable_reason", *_FLAGS,
         "final_condition_passes", "ignored_foreign_calls", "ignored_nested_calls",
         "stages", "additional_native_predicate_calls", "neighbor_Q_observed"}


_REL_FLAGS = ("argument_identity_matched", "same_thread", "sampled_relation_available", "unknown_or_inputs")
_REL_OPTIONAL_BOOLS = ("identity_before_after_match", "returned",
                       "sampled_selected_war_used_fallback", "sampled_direct_war_matches_aux",
                       "sampled_direct_war_gate")
_REL_IDENTITIES = ("auxiliary_identity", "sampled_relation_identity", "sampled_selected_war_identity")
_REL_KEYS = {"schema_version", "source", "status", "unavailable_reason", "call_count",
             "actual_bridge_caller_return_rva", "receiver_full_id", "actor_full_id",
             "sampled_relation_full_war_id", "sampled_selected_war_byte_358_u8",
             "sampled_relation_unavailable_reason", *_REL_FLAGS, *_REL_OPTIONAL_BOOLS,
             *_REL_IDENTITIES}


def normalize_county_relation_inputs_v1(value, *, parent_stage=None):
    """Keep original relation AL separate from pure direct-War operand samples."""
    if not isinstance(value, dict) or set(value) != _REL_KEYS:
        raise ValueError("county relation inputs schema is malformed")
    if (type(value["schema_version"]) is not int or value["schema_version"] != 1
            or value["source"] != "native_original_relation_entry_return_12004"):
        raise ValueError("county relation inputs source/version is malformed")
    for key in _REL_FLAGS:
        if type(value[key]) is not bool:
            raise ValueError("county relation inputs flags must be boolean")
    if value["unknown_or_inputs"] is not True:
        raise ValueError("county relation unobserved OR inputs must stay unknown")
    for key in _REL_OPTIONAL_BOOLS:
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError("county relation optional flags must be bool or null")
    for keys, low, high in (
            (("call_count", "receiver_full_id", "actor_full_id"), 0, 1 << 32),
            (("actual_bridge_caller_return_rva",), 0, 1 << 64),
            (("sampled_relation_full_war_id",), -(1 << 31), 1 << 31),
            (("sampled_selected_war_byte_358_u8",), 0, 256)):
        for key in keys:
            item = value[key]
            if item is not None and (type(item) is not int or not low <= item < high):
                raise ValueError("county relation integer width is malformed: " + key)
    if value["call_count"] is None:
        raise ValueError("county relation call count must be uint32")
    for key in _REL_IDENTITIES:
        item = value[key]
        if item is not None:
            if (not isinstance(item, str) or not item.startswith("native:")
                    or not item[7:].isascii() or not item[7:].isdecimal()
                    or not 0 < int(item[7:]) < 1 << 64 or str(int(item[7:])) != item[7:]):
                raise ValueError("county relation identity must be canonical opaque native identity")
    if value["status"] == "available":
        if (value["unavailable_reason"] is not None or value["call_count"] != 1
                or value["argument_identity_matched"] is not True
                or value["same_thread"] is not True
                or value["identity_before_after_match"] is not True
                or any(value[key] is None for key in ("actual_bridge_caller_return_rva",
                                                        "receiver_full_id", "actor_full_id", "returned"))):
            raise ValueError("available county relation requires one stable original native return")
        if value["receiver_full_id"] == value["actor_full_id"] and value["returned"] is not False:
            raise ValueError("same FullID contradicts source-proven native immediate false")
        if parent_stage is not None and (parent_stage["call_count"] != 1
                or parent_stage["argument_identity_matched"] is not True
                or value["returned"] is not parent_stage["returned"]):
            raise ValueError("county relation actual return differs from enclosing tail P stage")
    elif (value["status"] != "unavailable" or not isinstance(value["unavailable_reason"], str)
          or not value["unavailable_reason"]):
        raise ValueError("unavailable county relation requires an actual reason")
    if value["sampled_relation_available"]:
        if (value["sampled_relation_unavailable_reason"] is not None
                or type(value["sampled_direct_war_gate"]) is not bool):
            raise ValueError("available pure relation sample requires its computed direct gate")
        if (value["sampled_relation_identity"] is None
                or value["sampled_relation_full_war_id"] is None):
            raise ValueError("available pure relation sample requires pair identity and full WarID")
        if (value["receiver_full_id"] is not None
                and value["receiver_full_id"] == value["actor_full_id"]):
            raise ValueError("same FullID native early return skips the pure relation sampler")
        selected_keys = ("sampled_selected_war_identity", "sampled_selected_war_used_fallback",
                         "sampled_selected_war_byte_358_u8", "sampled_direct_war_matches_aux")
        if value["sampled_relation_full_war_id"] == -1:
            if value["sampled_direct_war_gate"] is not False or any(
                    value[key] is not None for key in selected_keys):
                raise ValueError("sentinel pair WarID skips selected War and has false direct gate")
        else:
            if any(value[key] is None for key in selected_keys):
                raise ValueError("available direct War sample requires complete selected War operands")
            matches_aux = (value["auxiliary_identity"] is None
                           or value["auxiliary_identity"] == value["sampled_selected_war_identity"])
            if value["sampled_direct_war_matches_aux"] is not matches_aux:
                raise ValueError("sampled direct War auxiliary comparison disagrees with identities")
            direct_gate = value["sampled_selected_war_byte_358_u8"] == 0 and matches_aux
            if value["sampled_direct_war_gate"] is not direct_gate:
                raise ValueError("sampled direct War gate disagrees with raw selected War operands")
    elif (not isinstance(value["sampled_relation_unavailable_reason"], str)
          or not value["sampled_relation_unavailable_reason"]):
        raise ValueError("unavailable pure relation sample requires its own reason")
    if value["call_count"] == 0 and any(value[key] is not None for key in (
            "actual_bridge_caller_return_rva", "receiver_full_id", "actor_full_id", "auxiliary_identity", "returned")):
        raise ValueError("uncalled relation has no actual arguments or return")
    return dict(value)


def explain_county_relation_inputs_v1(value):
    """No Move selection and no invented AL values for unobserved OR calls."""
    leaf = normalize_county_relation_inputs_v1(value)
    result = {"status": "unavailable", "reason": leaf["unavailable_reason"],
              "source": leaf["source"], "actual_relation_returned": leaf["returned"],
              "receiver_full_id": leaf["receiver_full_id"], "actor_full_id": leaf["actor_full_id"],
              "unknown_or_inputs": True, "unknown_or_result": None,
              "direct_war_sample": {key: leaf[key] for key in (
                  "sampled_relation_available", "sampled_relation_unavailable_reason",
                  "sampled_relation_identity", "sampled_relation_full_war_id",
                  "sampled_selected_war_identity", "sampled_selected_war_used_fallback",
                  "sampled_selected_war_byte_358_u8", "sampled_direct_war_matches_aux",
                  "sampled_direct_war_gate")}}
    if leaf["status"] != "available":
        return result
    if (leaf["returned"] is False and leaf["sampled_relation_available"]
            and leaf["sampled_direct_war_gate"] is True):
        result["reason"] = "source_sample_contradiction"
        return result
    result["status"] = "observed"
    if leaf["receiver_full_id"] == leaf["actor_full_id"]:
        result["reason"] = "actual_relation_same_full_id_returned_false"
    else:
        result["reason"] = ("actual_relation_returned_false_with_distinct_full_ids"
                            if leaf["returned"] is False else
                            "actual_relation_returned_true_with_distinct_full_ids")
    return result


def _with_relation_explanations(result, trace):
    children = []
    for label, stage in zip(("source_P", "target_P_first", "target_P_second"), trace["stages"]):
        if "relation_inputs_v1" in stage:
            children.append({"stage": label, **explain_county_relation_inputs_v1(stage["relation_inputs_v1"])})
    return {**result, "relation_inputs_v1": children} if children else result



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
        stage_keys = {"call_count", "actual_caller_return_rva", "argument_identity_matched", "returned"}
        if not isinstance(stage, dict) or set(stage) not in (stage_keys, stage_keys | {"relation_inputs_v1"}):
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
        if "relation_inputs_v1" in stage:
            normalize_county_relation_inputs_v1(stage["relation_inputs_v1"], parent_stage=stage)
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
    return {**value, "stages": [{**stage, **({"relation_inputs_v1": dict(stage["relation_inputs_v1"])}
                if "relation_inputs_v1" in stage else {})} for stage in stages]}


def explain_county_predicate_trace_v1(parent):
    """No Move selector: expose one falsifiable branch fact or a bounded residual."""
    trace = parent.get("predicate_trace_v1")
    if trace is None:
        return {"status": "unavailable", "reason": "county_P_trace_absent", "Q_observed": False}
    trace = normalize_county_predicate_trace_v1(trace, parent=parent)
    if trace["status"] != "available":
        return _with_relation_explanations({"status": "unavailable", "reason": trace["unavailable_reason"], "Q_observed": False}, trace)
    for label, stage in zip(("source_P", "target_P_first", "target_P_second"), trace["stages"]):
        if stage["returned"] is False:
            return _with_relation_explanations({"status": "observed", "reason": label + "_returned_false",
                    "actual_caller_return_rva": stage["actual_caller_return_rva"], "Q_observed": False}, trace)
    if all(stage["returned"] is True for stage in trace["stages"]):
        return _with_relation_explanations({"status": "source_inference", "reason": "P_chain_passed_final_true" if trace["final_condition_passes"]
                else "P_chain_passed_neighbor_chain_rejected", "Q_observed": False,
                "specific_neighbor_or_Q_result": None}, trace)
    return _with_relation_explanations({"status": "observed", "reason": "P_chain_not_reached_or_stopped_at_common_gate", "Q_observed": False}, trace)
