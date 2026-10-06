"""Strict same-query current2920D60 selector, Rule43 operands and numeric leaf."""
from __future__ import annotations

from .battle_context_source_inputs_contract import _availability, _boolean, _dict, _integer, _number, _string
from .battle_person_diac_literal_numeric_contract import normalize_diac_literal_numeric_inputs_12003
from ..simulation.battle_person_rule43_diac_12003 import (
    evaluate_rule43_admission_inputs_12003, evaluate_rule43_node_inputs_12003,
    emit_following_diac_2920d60_requests_12003,
)

_NODE_FIELDS = {"path", "identity", "slot58_rva", "slot60_rva", "slotc8_rva",
    "children_count_raw", "children_array_present", "reference_arguments_count_raw",
    "reference_compare_raw", "nested_present", "children", "result", "reason"}
_RULE_FIELDS = {"input_character_full_id", "source_constructed_root_kind", "expected_validator_rva",
    "mode_raw", "provider_identity", "rule_identity", "registry_count_raw", "descriptor_selection",
    "loaded_validator_rva", "root_lookup_selection", "root_object_identity", "root_tag_raw",
    "root_full_id_raw", "root_valid", "nodes", "result", "reason"}
_SELECTION_STRINGS = ("source_character_identity", "lookup_selection", "diac_identity",
                     "early_character_lookup_selection")
_SELECTION_WORDS = ("requested_diac_id_raw", "diac_full_id_raw", "diac_owner_full_id_raw",
                   "rule_character_full_id_raw")
_SELECTION_FIELDS = {*_SELECTION_STRINGS, *_SELECTION_WORDS, "diac_tag_raw",
                     "diac_valid", "owner_matches", "rule", "reason"}


def _ordered(value, field):
    if not isinstance(value, list):
        raise ValueError(field + " must be an ordered occurrence list")
    return value


def _verdict(out, calculated, field):
    if out["result"] != calculated or (out["result"] is not None) != (out["reason"] is None):
        raise ValueError(field + " bounded verdict/reason disagrees with demanded raw inputs")


def _node(value, field, mode, path):
    raw = _dict(value, field, _NODE_FIELDS)
    out = {key: _string(raw[key], field + "." + key, optional=key != "path")
           for key in ("path", "identity", "reason")}
    if out["path"] != path:
        raise ValueError(field + " native occurrence path disagrees")
    for key in ("slot58_rva", "slot60_rva", "slotc8_rva"):
        out[key] = _number(raw[key], field + "." + key, 64, unsigned=True)
    for key in ("children_count_raw", "reference_arguments_count_raw"):
        out[key] = _number(raw[key], field + "." + key, 32)
    out["reference_compare_raw"] = _number(raw["reference_compare_raw"], field + ".reference_compare_raw", 8, unsigned=True)
    for key in ("children_array_present", "nested_present", "result"):
        out[key] = _boolean(raw[key], field + "." + key, optional=True)
    children = _ordered(raw["children"], field + ".children")
    reference = out["slotc8_rva"] == 0x3730940
    out["children"] = [_node(child, f"{field}.children[{i}]", mode,
        path + ("/reference" if reference else "/child" + str(i))) for i, child in enumerate(children)]
    if reference:
        if len(children) > 1 or (out["nested_present"] is not True and children):
            raise ValueError(field + " reference child demand disagrees")
    else:
        count = out["children_count_raw"]
        if children and (count is None or count <= 0 or len(children) > count):
            raise ValueError(field + " conjunction child prefix disagrees")
        for child in out["children"][:-1]:
            if child["result"] is not True:
                raise ValueError(field + " traversed a child after native short circuit")
    _verdict(out, evaluate_rule43_node_inputs_12003(out, mode), field)
    return out


def _rule(value, field):
    raw = _dict(value, field, _RULE_FIELDS)
    out = {"input_character_full_id": _integer(raw["input_character_full_id"], field + ".input_character_full_id", 32),
           "source_constructed_root_kind": _integer(raw["source_constructed_root_kind"], field + ".source_constructed_root_kind", 16, unsigned=True),
           "expected_validator_rva": _integer(raw["expected_validator_rva"], field + ".expected_validator_rva", 64, unsigned=True)}
    if out["source_constructed_root_kind"] != 4 or out["expected_validator_rva"] != 0x22565B0:
        raise ValueError(field + " source kind/expected validator differs from exact .3")
    for key in ("provider_identity", "rule_identity", "descriptor_selection",
                "root_lookup_selection", "root_object_identity", "reason"):
        out[key] = _string(raw[key], field + "." + key, optional=True)
    for key in ("registry_count_raw", "root_full_id_raw"):
        out[key] = _number(raw[key], field + "." + key, 32)
    out["root_tag_raw"] = _number(raw["root_tag_raw"], field + ".root_tag_raw", 32, unsigned=True)
    out["mode_raw"] = _number(raw["mode_raw"], field + ".mode_raw", 8, unsigned=True)
    out["loaded_validator_rva"] = _number(raw["loaded_validator_rva"], field + ".loaded_validator_rva", 64, unsigned=True)
    for key in ("root_valid", "result"):
        out[key] = _boolean(raw[key], field + "." + key, optional=True)
    count, selection = out["registry_count_raw"], out["descriptor_selection"]
    if selection is not None and (count is None or selection != ("registry_kind4" if count > 4 else "native_descriptor_fallback")):
        raise ValueError(field + " loaded descriptor selection disagrees")
    lookup = out["root_lookup_selection"]
    if lookup not in (None, "registry_full_generation", "native_fallback"):
        raise ValueError(field + " unknown full-generation selection")
    root = None
    if (out["loaded_validator_rva"] == out["expected_validator_rva"]
        and lookup is not None and out["root_object_identity"] is not None and out["root_tag_raw"] is not None):
        root = (False if out["root_tag_raw"] != 0x43686172 else
                None if out["root_full_id_raw"] is None else out["root_full_id_raw"] != -1)
    if root != out["root_valid"]:
        raise ValueError(field + " root selected tag/full-ID predicate disagrees")
    if lookup == "registry_full_generation" and out["root_full_id_raw"] is not None and out["root_full_id_raw"] != out["input_character_full_id"]:
        raise ValueError(field + " registry generation differs from raw root ID")
    nodes = _ordered(raw["nodes"], field + ".nodes")
    if len(nodes) > 1 or (root is not True and nodes):
        raise ValueError(field + " rule node demand disagrees with root admission")
    out["nodes"] = [_node(node, field + ".nodes[0]", out["mode_raw"], "rule43") for node in nodes]
    _verdict(out, evaluate_rule43_admission_inputs_12003(out), field)
    return out


def _selection(value, field):
    raw = _dict(value, field, _SELECTION_FIELDS)
    out = {key: _string(raw[key], field + "." + key, optional=True)
           for key in (*_SELECTION_STRINGS, "reason")}
    for key in _SELECTION_WORDS:
        out[key] = _number(raw[key], field + "." + key, 32)
    out["diac_tag_raw"] = _number(raw["diac_tag_raw"], field + ".diac_tag_raw", 32, unsigned=True)
    for key in ("diac_valid", "owner_matches"):
        out[key] = _boolean(raw[key], field + "." + key, optional=True)
    tag, full = out["diac_tag_raw"], out["diac_full_id_raw"]
    valid = None if tag is None else False if tag != 0x44696163 else None if full is None else full != -1
    if out["diac_valid"] != valid:
        raise ValueError(field + " Diac tag/full-ID predicate disagrees")
    if out["lookup_selection"] not in (None, "registry_full_generation", "native_fallback"):
        raise ValueError(field + " unknown Diac lookup route")
    if out["lookup_selection"] == "registry_full_generation" and full is not None and full != out["requested_diac_id_raw"]:
        raise ValueError(field + " Diac generation disagrees")
    out["rule"] = None if raw["rule"] is None else _rule(raw["rule"], field + ".rule")
    if out["rule"] is not None and (valid is not True or out["rule"]["input_character_full_id"] != out["rule_character_full_id_raw"]):
        raise ValueError(field + " rule input differs from selected Character18")
    return out


def normalize_following_diac_2920d60(value, field="following_diac_2920d60"):
    if value is None:
        return None
    raw = _dict(value, field, {"status", "ready", "reason", "character_id",
        "current_character_full_id_raw", "primary", "secondary", "selected_family", "numeric_inputs"})
    status, ready, reason = _availability(raw, field)
    out = {"status": status, "ready": ready, "reason": reason,
           "character_id": _integer(raw["character_id"], field + ".character_id", 32),
           "current_character_full_id_raw": _number(raw["current_character_full_id_raw"], field + ".current_character_full_id_raw", 32),
           "primary": _selection(raw["primary"], field + ".primary"),
           "secondary": None if raw["secondary"] is None else _selection(raw["secondary"], field + ".secondary"),
           "selected_family": _string(raw["selected_family"], field + ".selected_family", optional=True),
           "numeric_inputs": None if raw["numeric_inputs"] is None else normalize_diac_literal_numeric_inputs_12003(raw["numeric_inputs"])}
    actor = out["current_character_full_id_raw"]
    if actor is not None and actor != out["character_id"]:
        raise ValueError(field + " current Character18 differs from enclosing actor")
    primary, secondary = out["primary"], out["secondary"]
    primary_result = None if primary["rule"] is None else primary["rule"]["result"]
    proceed = primary["diac_valid"] is False or primary["diac_valid"] is True and primary_result is False
    family = None
    if primary["diac_valid"] is True and primary_result is True:
        family = "primary_620"
    if not proceed and secondary is not None:
        raise ValueError(field + " secondary read after unknown/accepted primary")
    if proceed and secondary is not None:
        if secondary["diac_valid"] is False:
            family = "none"
        elif secondary["diac_valid"] is True:
            owner = secondary["diac_owner_full_id_raw"]
            match = None if actor is None or owner is None else actor == owner
            if secondary["owner_matches"] != match:
                raise ValueError(field + " secondary owner comparison differs from raw DWORDs")
            result = None if secondary["rule"] is None else secondary["rule"]["result"]
            if match is False or match is True and result is False:
                family = "none"
            elif match is True and result is True:
                family = "secondary_658"
    if family != out["selected_family"]:
        raise ValueError(field + " native primary/secondary selection disagrees")
    numeric = out["numeric_inputs"]
    if family in (None, "none") and numeric is not None:
        raise ValueError(field + " unselected family published numeric inputs")
    if numeric is not None:
        scope = primary["diac_owner_full_id_raw"] if family == "primary_620" else actor
        if numeric["scope_character_full_id"] is not None and numeric["scope_character_full_id"] != scope:
            raise ValueError(field + " numeric scope differs from actual caller's full-ID source")
    complete = family == "none" or family in ("primary_620", "secondary_658") and numeric is not None and numeric["ready"]
    if ready != (complete and reason is None):
        raise ValueError(field + " bounded whole-source readiness disagrees")
    return out


def emit_following_diac_2920d60_requests_from_current_source_inputs_12003(section):
    leaf = normalize_following_diac_2920d60(None if section is None else section.get("following_diac_2920d60"))
    if leaf is None:
        raise ValueError("Required native input unavailable: following_diac_2920d60")
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError("following_diac_2920d60 character differs from source actor")
    return emit_following_diac_2920d60_requests_12003(leaf)
