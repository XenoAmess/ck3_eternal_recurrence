"""Strict actual Lege selector, owner header and two-PC inputs for2921020."""
from __future__ import annotations

from .battle_context_source_inputs_contract import (
    _availability, _boolean, _dict, _integer, _number, _properties,
    _properties_ready, _span, _string,
)
from .battle_person_after_gated_tail_contract import _pc, _pc_ready
from ..simulation.battle_person_following_2921020_12003 import (
    emit_following_2921020_requests_12003, emit_following_2921020_owner_requests_12003,
    emit_following_2921020_composite_requests_12003,
)

_FIELD = "following_2921020"
_WORDS = ("requested_full_id_raw", "selected_full_id_raw", "full_id_raw",
          "character_full_id_raw", "owner_full_id_raw")
_STRINGS = ("resolution_selection", "object_identity", "table_identity", "definition_identity",
            "tier_selection", "selected_row_identity")
_BOOLS = ("component_present", "admitted", "owner_matches", "owner_header_ready")
_FIELDS = {"status", "ready", "reason", "character_id", *_WORDS, *_STRINGS, *_BOOLS,
           "magic_u32", "rank_raw_i8", "owner_weighted_header", "owner_definition_blocks",
           "base_pc", "tier_pc", "composite_ready"}
_LATER = ("character_full_id_raw", "owner_full_id_raw", "owner_matches", "table_identity",
          "definition_identity", "rank_raw_i8", "tier_selection", "selected_row_identity",
          "owner_weighted_header", "owner_header_ready")


def _owner_ready(header, blocks):
    if header is None or header["count"] is None or header["reason"] is not None:
        return False
    count, rows = header["count"], header["rows"]
    if count <= 0:
        return rows == []
    by_identity = {row["definition_identity"]: row["properties"] for row in blocks}
    return (rows is not None and len(rows) == count and all(
        row["definition_identity"] is not None and row["weight_q64"] is not None
        and _properties_ready(by_identity.get(row["definition_identity"]))
        and by_identity[row["definition_identity"]]["reason"] is None for row in rows))


def _absent_pc(pc):
    return pc["property_identity"] is None and pc["property_block"] is None


def normalize_following_2921020(value, field=_FIELD):
    if value is None:
        return None
    raw = _dict(value, field, _FIELDS)
    status, ready, reason = _availability(raw, field)
    out = {"status": status, "ready": ready, "reason": reason,
           "character_id": _integer(raw["character_id"], field + ".character_id", 32)}
    for key in _WORDS:
        out[key] = _number(raw[key], field + "." + key, 32)
    for key in _STRINGS:
        out[key] = _string(raw[key], field + "." + key, optional=True)
    for key in _BOOLS:
        out[key] = _boolean(raw[key], field + "." + key, optional=True)
    out["magic_u32"] = _number(raw["magic_u32"], field + ".magic_u32", 32, unsigned=True)
    out["rank_raw_i8"] = _number(raw["rank_raw_i8"], field + ".rank_raw_i8", 8)
    out["composite_ready"] = _boolean(raw["composite_ready"], field + ".composite_ready")
    out["owner_weighted_header"] = _span(raw["owner_weighted_header"], field + ".owner_weighted_header")
    blocks = raw["owner_definition_blocks"]
    if not isinstance(blocks, list):
        raise ValueError(field + ".owner_definition_blocks must be a list")
    copied, identities = [], set()
    for i, row in enumerate(blocks):
        name = f"{field}.owner_definition_blocks[{i}]"
        item = _dict(row, name, {"definition_identity", "properties"})
        identity = _string(item["definition_identity"], name + ".definition_identity")
        if identity in identities:
            raise ValueError(name + " repeats physical Definition identity")
        identities.add(identity)
        copied.append({"definition_identity": identity, "properties": _properties(item["properties"], name + ".properties")})
    out["owner_definition_blocks"] = copied
    for key in ("base_pc", "tier_pc"):
        out[key] = _pc(raw[key], field + "." + key)
    selection = out["resolution_selection"]
    if selection not in {None, "registry_full_id_8", "native_fallback"}:
        raise ValueError(field + " unknown resolver selection")
    requested = out["requested_full_id_raw"]
    if out["component_present"] is False and requested not in {None, -1}:
        raise ValueError(field + " absent carrier must request full FFFFFFFF")
    if selection == "registry_full_id_8" and (requested is None or out["selected_full_id_raw"] != requested):
        raise ValueError(field + " full-generation registry selection disagrees")
    if selection != "registry_full_id_8" and out["selected_full_id_raw"] is not None:
        raise ValueError(field + " nonindexed resolver published selected generation")
    resolved = selection is not None and out["object_identity"] is not None
    magic, full = out["magic_u32"], out["full_id_raw"]
    admitted = None if not resolved or magic is None else False if magic != 0x4C656765 else None if full is None else full != -1
    if out["admitted"] != admitted:
        raise ValueError(field + " Lege magic/full-ID admission disagrees")
    if magic is not None and magic != 0x4C656765 and full is not None:
        raise ValueError(field + " rejected magic contains undemanded full-ID gate")
    if admitted is not True:
        if (any(out[key] is not None for key in _LATER) or copied
            or out["composite_ready"] or not all(_absent_pc(out[key]) for key in ("base_pc", "tier_pc"))):
            raise ValueError(field + " unadmitted object contains downstream operands")
        complete = admitted is False
    else:
        actor, owner = out["character_full_id_raw"], out["owner_full_id_raw"]
        if actor is not None and actor != out["character_id"]:
            raise ValueError(field + " actual Character18 disagrees with actor")
        match = actor == owner if actor is not None and owner is not None else None
        if out["owner_matches"] != match:
            raise ValueError(field + " owner comparison disagrees with full DWORDs")
        rank = out["rank_raw_i8"]
        tier = None if rank is None else "direct_rank_0_2" if 0 <= rank < 3 else "diagnostic_3f7ab90_outcome_unobserved"
        if out["tier_selection"] != tier:
            raise ValueError(field + " signed-byte tier/diagnostic selection disagrees")
        direct = (tier == "direct_rank_0_2" and out["table_identity"] is not None
                  and out["selected_row_identity"] is not None)
        if tier != "direct_rank_0_2" and out["selected_row_identity"] is not None:
            raise ValueError(field + " diagnostic rank cannot fabricate returned row")
        if tier == "diagnostic_3f7ab90_outcome_unobserved" and reason != "rank_diagnostic_3f7ab90_result":
            raise ValueError(field + " diagnostic rank must retain exact missing result")
        owner_demand = direct and match is True
        if not owner_demand:
            if out["owner_weighted_header"] is not None or copied or out["owner_header_ready"] is not None:
                raise ValueError(field + " undemanded owner header contains physical operands")
        else:
            header = out["owner_weighted_header"]
            if header is not None and header["selected_source"] != "selected_28":
                raise ValueError(field + " owner header selected a different physical source")
            if out["owner_header_ready"] != _owner_ready(header, copied):
                raise ValueError(field + " owner-header readiness disagrees")
        composite_demand = direct and match is not None and out["definition_identity"] is not None
        if not composite_demand and any(not _absent_pc(out[key]) for key in ("base_pc", "tier_pc")):
            raise ValueError(field + " unavailable getter/owner contains undemanded composite PCs")
        composite = composite_demand and _pc_ready(out["base_pc"]) and _pc_ready(out["tier_pc"])
        if out["composite_ready"] != composite:
            raise ValueError(field + " composite readiness disagrees with actual PCs")
        complete = composite and (match is False or out["owner_header_ready"] is True)
    if ready != (complete and reason is None):
        raise ValueError(field + " readiness disagrees with all demanded source inputs")
    return out


def _current(section):
    raw = None if section is None else section.get(_FIELD)
    leaf = normalize_following_2921020(raw)
    if leaf is None:
        raise ValueError("Required native input unavailable: " + _FIELD)
    if leaf["character_id"] != _integer(section.get("character_id"), "current_context_source_inputs.character_id", 32):
        raise ValueError(_FIELD + " character disagrees with source actor")
    return leaf, raw


def emit_following_2921020_requests_from_current_source_inputs_12003(section):
    leaf, raw = _current(section)
    return emit_following_2921020_requests_12003(leaf, actual_leaf=raw)


def emit_following_2921020_owner_requests_from_current_source_inputs_12003(section):
    leaf, raw = _current(section)
    return emit_following_2921020_owner_requests_12003(leaf, actual_leaf=raw)


def emit_following_2921020_composite_requests_from_current_source_inputs_12003(section):
    leaf, _ = _current(section)
    return emit_following_2921020_composite_requests_12003(leaf)
