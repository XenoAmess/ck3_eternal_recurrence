"""Strict raw government bit29 and first-Land312A950 minimum source contract."""
from __future__ import annotations

from .battle_context_source_inputs_contract import _availability, _boolean, _dict, _integer, _number, _string
from .battle_person_after_gated_tail_contract import _pc
from ..simulation.battle_person_following_312a950_12003 import (
    KNOWN_ZERO_STAGES_FOLLOWING_312A950_12003, following312a950_stage_selection_12003,
    emit_following_312a950_requests_12003,
)

_FIELD = "following_government_land_312a950"


def _start(value, field, fields):
    raw = _dict(value, field, {"status", "ready", "reason", *fields})
    status, ready, reason = _availability(raw, field)
    return raw, {"status": status, "ready": ready, "reason": reason}


def _words(raw, out, field, keys, bits=32, unsigned=False):
    for key in keys:
        out[key] = _number(raw[key], field + "." + key, bits, unsigned=unsigned)


def _strings(raw, out, field, keys):
    for key in keys:
        out[key] = _string(raw[key], field + "." + key, optional=True)


def _bools(raw, out, field, keys):
    for key in keys:
        out[key] = _boolean(raw[key], field + "." + key, optional=True)


def _government(value, field):
    raw, out = _start(value, field, {"selection", "selected_character_identity", "selection_native_index",
                                   "government_identity", "flags_raw_u32"})
    _strings(raw, out, field, ("selection", "selected_character_identity", "government_identity"))
    _words(raw, out, field, ("selection_native_index",))
    _words(raw, out, field, ("flags_raw_u32",), unsigned=True)
    if out["selection"] not in {None, "death_1d0_88", "living_1c0_3f8", "global_fallback_5d1e2a8"}:
        raise ValueError(field + " actual government source selection invalid")
    if out["selection_native_index"] is not None and out["selection_native_index"] < 0:
        raise ValueError(field + " government source ordinal must start at0")
    complete = (out["selection"] is not None and out["government_identity"] is not None
                and out["flags_raw_u32"] is not None and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " actual government readiness disagrees")
    return out


def _first_land(value, field):
    raw, out = _start(value, field, {"selection", "living_present", "death_present", "count_raw",
                                   "array_present", "full_id_raw"})
    _strings(raw, out, field, ("selection",))
    _bools(raw, out, field, ("living_present", "death_present", "array_present"))
    _words(raw, out, field, ("count_raw", "full_id_raw"))
    living, death, count = out["living_present"], out["death_present"], out["count_raw"]
    selection = "living_1c0" if living is True else (
        "death_1d0" if living is False and death is True else "none" if living is False and death is False else None)
    if out["selection"] != selection:
        raise ValueError(field + " firstLand living-first selection disagrees")
    if living is True and death is not None:
        raise ValueError(field + " live firstLand contains undemanded death source")
    if selection == "none":
        if count is not None or out["array_present"] is not None or out["full_id_raw"] != -1:
            raise ValueError(field + " absent firstLand must retain source ID-1 without header demand")
        complete = True
    elif selection in {"living_1c0", "death_1d0"} and count == 0:
        if out["array_present"] is not None or out["full_id_raw"] != -1:
            raise ValueError(field + " zero firstLand count must retain ID-1 without array demand")
        complete = True
    else:
        complete = (selection in {"living_1c0", "death_1d0"} and count is not None and count != 0
                    and out["array_present"] is True and out["full_id_raw"] is not None)
    if out["ready"] != (complete and out["reason"] is None):
        raise ValueError(field + " count!=0 firstDWORD readiness disagrees")
    return out


def _land(value, field, first):
    raw, out = _start(value, field, {"selection", "requested_full_id_raw", "selected_full_id_raw",
        "object_identity", "magic_u32", "full_id_raw", "admitted", "balance_raw_q64"})
    _strings(raw, out, field, ("selection", "object_identity"))
    _words(raw, out, field, ("requested_full_id_raw", "selected_full_id_raw", "full_id_raw"))
    _words(raw, out, field, ("magic_u32",), unsigned=True)
    _words(raw, out, field, ("balance_raw_q64",), 64)
    _bools(raw, out, field, ("admitted",))
    if out["selection"] not in {None, "registry_full_id_10", "native_fallback"}:
        raise ValueError(field + " Land resolution selection invalid")
    if first is not None and out["requested_full_id_raw"] not in {None, first["full_id_raw"]}:
        raise ValueError(field + " Land resolver requested a different full generation")
    if out["selection"] == "registry_full_id_10" and (
        out["requested_full_id_raw"] is None or out["selected_full_id_raw"] != out["requested_full_id_raw"]
    ):
        raise ValueError(field + " Land full-generation comparator disagrees")
    magic, full_id = out["magic_u32"], out["full_id_raw"]
    admitted = None if magic is None else False if magic != 0x4C616E64 else None if full_id is None else full_id != -1
    if out["admitted"] != admitted:
        raise ValueError(field + " actual Land magic/fullID admission disagrees")
    if magic != 0x4C616E64 and full_id is not None:
        raise ValueError(field + " Land magic rejection contains undemanded caller fullID")
    if admitted is not True and out["balance_raw_q64"] is not None:
        raise ValueError(field + " invalid Land contains undemanded balance")
    if admitted is True and out["selection"] == "registry_full_id_10" and full_id != out["selected_full_id_raw"]:
        raise ValueError(field + " caller Land fullID disagrees with indexed object")
    complete = (out["selection"] is not None and out["object_identity"] is not None and admitted is not None
                and (not admitted or out["balance_raw_q64"] is not None) and out["reason"] is None)
    if out["ready"] != complete:
        raise ValueError(field + " selected Land readiness disagrees")
    return out


def _mode3(value, field):
    raw, out = _start(value, field, {"income_q64", "index_raw_i32"})
    _words(raw, out, field, ("income_q64",), 64)
    _words(raw, out, field, ("index_raw_i32",))
    if (out["ready"] or out["income_q64"] is not None or out["index_raw_i32"] is not None
        or out["reason"] != "mode3_income_2bca580"):
        raise ValueError(field + " minimum requires precise unobserved mode3 income")
    return out


def _provider(value, field):
    raw, out = _start(value, field, {"provider_loaded", "count_raw", "selection", "definition_identity",
        "definition_magic_u32", "admitted", "pc"})
    _bools(raw, out, field, ("provider_loaded", "admitted"))
    _words(raw, out, field, ("count_raw",))
    _words(raw, out, field, ("definition_magic_u32",), unsigned=True)
    _strings(raw, out, field, ("selection", "definition_identity"))
    out["pc"] = _pc(raw["pc"], field + ".pc")
    if (out["ready"] or any(out[key] is not None for key in
        ("count_raw", "selection", "definition_identity", "definition_magic_u32", "admitted"))
        or any(out["pc"][key] is not None for key in ("property_identity", "property_block"))):
        raise ValueError(field + " missing mode3 classifier leaves all downstream provider inputs undemanded")
    return out


def normalize_following_government_land_312a950(value, field=_FIELD):
    if value is None:
        return None
    raw, out = _start(value, field, {"character_id", "government_source", "character_state_present",
        "first_land_source", "land_resolution", "mode3_classifier", "provider_selection", "stage_selection"})
    out["character_id"] = _integer(raw["character_id"], field + ".character_id", 32)
    _bools(raw, out, field, ("character_state_present",))
    _strings(raw, out, field, ("stage_selection",))
    out["government_source"] = _government(raw["government_source"], field + ".government_source")
    out["first_land_source"] = None if raw["first_land_source"] is None else _first_land(raw["first_land_source"], field + ".first_land_source")
    out["land_resolution"] = None if raw["land_resolution"] is None else _land(
        raw["land_resolution"], field + ".land_resolution", out["first_land_source"])
    out["mode3_classifier"] = None if raw["mode3_classifier"] is None else _mode3(raw["mode3_classifier"], field + ".mode3_classifier")
    out["provider_selection"] = None if raw["provider_selection"] is None else _provider(raw["provider_selection"], field + ".provider_selection")
    selection = following312a950_stage_selection_12003(out)
    if out["stage_selection"] != selection:
        raise ValueError(field + " ordered stage selection disagrees")
    if selection in {"government_bit29_false", "character_1b0_absent"}:
        if any(out[key] is not None for key in ("first_land_source", "land_resolution", "mode3_classifier", "provider_selection")):
            raise ValueError(field + " early knownzero contains undemanded later groups")
        if selection == "government_bit29_false" and out["character_state_present"] is not None:
            raise ValueError(field + " false bit29 contains undemanded Character1B0")
    if selection in {"first_land_invalid", "first_land_nonnegative"}:
        if out["mode3_classifier"] is not None or out["provider_selection"] is not None:
            raise ValueError(field + " invalid/nonnegative Land contains undemanded mode3/provider")
    if selection == "negative_land_mode3_income_unobserved":
        if out["mode3_classifier"] is None or out["provider_selection"] is None:
            raise ValueError(field + " negative Land must retain actual provider and precise classifier gap")
    complete = selection in KNOWN_ZERO_STAGES_FOLLOWING_312A950_12003 and out["reason"] is None
    if out["ready"] != complete:
        raise ValueError(field + " minimum readiness disagrees with four knownzero branches")
    return out


def emit_following_312a950_requests_from_current_source_inputs_12003(section):
    raw = None if section is None else section.get(_FIELD)
    leaf = normalize_following_government_land_312a950(raw)
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return emit_following_312a950_requests_12003(leaf)
