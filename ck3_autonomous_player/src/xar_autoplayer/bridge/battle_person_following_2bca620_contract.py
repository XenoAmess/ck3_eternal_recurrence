"""Strict minimum following2BCA620 balance/provider current-source receipt."""
from __future__ import annotations

from .battle_context_source_inputs_contract import _availability, _boolean, _dict, _integer, _number, _string
from .battle_person_after_gated_tail_contract import _pc, _pc_ready
from ..simulation.battle_person_following_2bca620_12003 import (
    following_2bca620_balance_classification_12003, following_2bca620_provider_selection_12003,
    emit_following_2bca620_requests_12003,
)

_FIELD = "following_2bca620"


def _start(value, field, fields):
    raw = _dict(value, field, {"status", "ready", "reason", *fields})
    status, ready, reason = _availability(raw, field)
    return raw, {"status": status, "ready": ready, "reason": reason}


def _balance(value, field):
    raw = _dict(value, field, {"component_present", "balance_raw_q64", "numeric_balance_q64", "reason"})
    out = {"component_present": _boolean(raw["component_present"], field + ".component_present", optional=True),
        "balance_raw_q64": _number(raw["balance_raw_q64"], field + ".balance_raw_q64", 64),
        "numeric_balance_q64": _number(raw["numeric_balance_q64"], field + ".numeric_balance_q64", 64),
        "reason": _string(raw["reason"], field + ".reason", optional=True)}
    present = out["component_present"]
    expected = out["balance_raw_q64"] if present is True else 0 if present is False else None
    if present is not True and out["balance_raw_q64"] is not None:
        raise ValueError(field + " absent/unknown component contains undemanded raw balance")
    if out["numeric_balance_q64"] != expected:
        raise ValueError(field + " numeric balance disagrees with actual1B0+100/known absence")
    return out


def _classifier(value, field, balance):
    raw, out = _start(value, field, {"selection", "index_raw_i32"})
    out["selection"] = _string(raw["selection"], field + ".selection", optional=True)
    out["index_raw_i32"] = _number(raw["index_raw_i32"], field + ".index_raw_i32", 32)
    selection, index = following_2bca620_balance_classification_12003(balance["numeric_balance_q64"])
    if (out["selection"], out["index_raw_i32"]) != (selection, index):
        raise ValueError(field + " minimum balance classifier disagrees")
    if selection == "negative_balance_income_unobserved" and out["reason"] != "negative_balance_income_2bca4e0":
        raise ValueError(field + " negative balance must retain precise unobserved income")
    complete = index == -1 and balance["reason"] is None and out["reason"] is None
    if out["ready"] != complete:
        raise ValueError(field + " classifier readiness disagrees")
    return out


def _provider(value, field, classifier):
    raw, out = _start(value, field, {"provider_loaded", "count_raw", "selection", "definition_identity",
        "definition_magic_u32", "admitted", "pc"})
    out["provider_loaded"] = _boolean(raw["provider_loaded"], field + ".provider_loaded", optional=True)
    out["count_raw"] = _number(raw["count_raw"], field + ".count_raw", 32)
    out["definition_magic_u32"] = _number(raw["definition_magic_u32"], field + ".definition_magic_u32", 32, unsigned=True)
    out["admitted"] = _boolean(raw["admitted"], field + ".admitted", optional=True)
    for key in ("selection", "definition_identity"):
        out[key] = _string(raw[key], field + "." + key, optional=True)
    out["pc"] = _pc(raw["pc"], field + ".pc")
    if classifier["index_raw_i32"] is None:
        if (any(out[key] is not None for key in ("count_raw", "selection", "definition_identity", "definition_magic_u32", "admitted"))
            or any(out["pc"][key] is not None for key in ("property_identity", "property_block"))):
            raise ValueError(field + " unavailable classifier contains undemanded provider inputs")
        selection = None
    elif out["provider_loaded"] is True:
        selection = following_2bca620_provider_selection_12003(classifier["index_raw_i32"], out["count_raw"])
    else:
        selection = None
        if out["count_raw"] is not None:
            raise ValueError(field + " unloaded provider contains count")
    if out["selection"] != selection:
        raise ValueError(field + " provider equality-before-fallback selection disagrees")
    magic = out["definition_magic_u32"]
    admitted = magic == 0x4744624F if selection is not None and magic is not None else None
    if out["admitted"] != admitted:
        raise ValueError(field + " selected Definition magic admission disagrees")
    if admitted is not True and any(out["pc"][key] is not None for key in ("property_identity", "property_block")):
        raise ValueError(field + " nonadmitted source contains undemanded PC40")
    complete = (classifier["ready"] and out["provider_loaded"] is True and selection is not None
        and out["definition_identity"] is not None and admitted is not None
        and (not admitted or _pc_ready(out["pc"])) and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " selected provider readiness disagrees")
    return out


def normalize_following_2bca620(value, field=_FIELD):
    if value is None:
        return None
    raw, out = _start(value, field, {"character_id", "balance_source", "classifier", "provider_selection"})
    out["character_id"] = _integer(raw["character_id"], field + ".character_id", 32)
    out["balance_source"] = _balance(raw["balance_source"], field + ".balance_source")
    out["classifier"] = _classifier(raw["classifier"], field + ".classifier", out["balance_source"])
    out["provider_selection"] = _provider(raw["provider_selection"], field + ".provider_selection", out["classifier"])
    if out["ready"] != (out["classifier"]["ready"] and out["provider_selection"]["ready"]):
        raise ValueError(field + " readiness disagrees with classifier and actual provider PC")
    return out


def emit_following_2bca620_requests_from_current_source_inputs_12003(section):
    raw = None if section is None else section.get(_FIELD)
    leaf = normalize_following_2bca620(raw)
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return emit_following_2bca620_requests_12003(leaf, actual_leaf=raw)
