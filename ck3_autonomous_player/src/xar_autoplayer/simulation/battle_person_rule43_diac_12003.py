"""Bounded current Rule43 Boolean projection and qualified Diac requests.

These functions mirror only source-closed loaded targets. They never call a
script evaluator or infer a full person/Entry preparation result.
"""
from __future__ import annotations

from .battle_person_diac_literal_numeric_12003 import emit_diac_literal_numeric_requests_12003


def evaluate_rule43_node_inputs_12003(node, mode):
    if node["identity"] is None or node["slot58_rva"] != 0x855AB0:
        return None
    if node["slot60_rva"] not in (0x9CFEC0, 0x9CFEE0):
        return None
    children = node["children"]
    if node["slotc8_rva"] == 0x372F780:
        if mode in (2, 4):
            return None
        count = node["children_count_raw"]
        if count is None or count < 0 or node["children_array_present"] is None:
            return None
        if count == 0:
            return True
        for child in children:
            result = evaluate_rule43_node_inputs_12003(child, mode)
            if result is None or result is False:
                return result
        return True if len(children) == count else None
    if node["slotc8_rva"] == 0x3730940:
        if node["reference_arguments_count_raw"] != 0 or node["nested_present"] is None:
            return None
        nested = False
        if node["nested_present"]:
            if not children:
                return None
            nested = evaluate_rule43_node_inputs_12003(children[0], mode)
            if nested is None:
                return None
        raw = node["reference_compare_raw"]
        return None if raw is None else raw == int(nested)
    return None


def evaluate_rule43_admission_inputs_12003(rule):
    if (rule["mode_raw"] is None or rule["provider_identity"] is None
        or rule["rule_identity"] is None or rule["loaded_validator_rva"] != 0x22565B0):
        return None
    root = rule["root_valid"]
    if root is False:
        return False
    if root is not True or not rule["nodes"]:
        return None
    return evaluate_rule43_node_inputs_12003(rule["nodes"][0], rule["mode_raw"])


def emit_following_diac_2920d60_requests_12003(leaf):
    if not leaf["ready"]:
        raise ValueError("Required native input unavailable: following_diac_2920d60:" + str(leaf["reason"]))
    if leaf["selected_family"] == "none":
        return ()
    return emit_diac_literal_numeric_requests_12003(leaf["numeric_inputs"])


def first_rule43_unknown_node_12003(rule):
    """Actual first demanded occurrence, retaining its loaded source pins."""
    if rule["result"] is not None:
        return None
    if not rule["nodes"]:
        return {"path": "root", "reason": rule["reason"],
                "loaded_validator_rva": rule["loaded_validator_rva"]}
    node = rule["nodes"][0]
    while node["children"] and node["children"][-1]["result"] is None:
        node = node["children"][-1]
    return {key: node[key] for key in ("path", "identity", "slot58_rva", "slot60_rva",
        "slotc8_rva", "children_count_raw", "reference_arguments_count_raw", "reason")}
