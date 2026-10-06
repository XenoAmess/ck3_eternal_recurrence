"""Exact-build selected declaration identity and independent CB cost observation."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from .declaration_contract import normalize_declarable_wars
from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12003, CK3_12004, require_exact_native_build


SCHEMA = "player_ordinary_holy_war_declaration_context_v1"
RESOURCE_KEYS = (
    "gold", "prestige", "piety", "renown", "influence", "herd", "treasury",
    "treasury_or_gold", "merit", "barter_goods",
)
ORDINARY_HOLY_WAR_KEYS = frozenset({
    "minor_religious_war", "religious_war", "major_religious_war",
})
SELECTED_FIELDS = frozenset({
    "target_character_id", "casus_belli_index", "casus_belli_key",
    "configuration_index", "claimant_character_id", "target_title_ids",
})
_FIELDS = {
    "schema", "read_only", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "public_revision", "native_revision",
    "date_raw", "played_character_id", "declaration_id", "selected_declaration",
    "context_actor_character_id", "context_recipient_character_id",
    "context_additional_role_character_id", "context_claimant_character_id",
    "recipient_uses_native_fallback", "additional_role_uses_native_fallback",
    "claimant_uses_native_fallback", "final_can_send", "cb_cost",
    "generic_interaction_cost_raw", "total_declaration_cost_raw", "total_cost_ready",
}
_ROLES = (
    "context_actor_character_id", "context_recipient_character_id",
    "context_additional_role_character_id", "context_claimant_character_id",
)
_FALLBACKS = (
    "recipient_uses_native_fallback", "additional_role_uses_native_fallback",
    "claimant_uses_native_fallback",
)
_COST_FIELDS = {
    "available", "unavailable_reason", "resource_keys", "resource_costs_raw", "raw_scale",
}


def _integer(value: object, name: str, minimum: int, maximum: int) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"native ordinary holy-war integer is malformed: {name}")


def _reason(value: object, *, available: bool, name: str) -> None:
    if ((available and value is not None)
            or (not available and (not isinstance(value, str) or not value))):
        raise ValueError(f"native ordinary holy-war availability reason is malformed: {name}")


def selected_ordinary_holy_war_declaration(
    snapshot: Mapping[str, object], declaration_id: str,
) -> dict[str, object]:
    """Use the existing declaration rows, preserving generation bits and title order."""
    rows = normalize_declarable_wars(snapshot.get("declarable_wars"))
    selected = next((row for row in rows if row["declaration_id"] == declaration_id), None)
    if selected is None:
        raise ValueError("selected ordinary holy-war declaration is absent from the current frame")
    if selected["casus_belli_key"] not in ORDINARY_HOLY_WAR_KEYS:
        raise ValueError("selected declaration is not an ordinary holy-war CB")
    for key in ("target_character_id", "casus_belli_index"):
        _integer(selected[key], key, 0, (1 << 31) - 1)
    for key in ("configuration_index", "claimant_character_id"):
        _integer(selected[key], key, -1, (1 << 31) - 1)
    for item in selected["target_title_ids"]:
        _integer(item, "target_title_ids[]", 0, (1 << 31) - 1)
    return {key: deepcopy(selected[key]) for key in SELECTED_FIELDS}


def normalize_player_ordinary_holy_war_declaration_context_v1(
    value: object, *, snapshot: Mapping[str, object], declaration_id: str,
    selected_declaration: Mapping[str, object],
) -> dict[str, object]:
    """Keep the CB-only quote distinct from unknown generic and total cost."""
    if (not isinstance(value, dict) or set(value) != _FIELDS
            or value["schema"] != SCHEMA or value["read_only"] is not True):
        raise ValueError("native ordinary holy-war declaration context schema is malformed")
    build = require_exact_native_build(value["game_version"], value["executable_sha256"])
    # The .4 factory's native proof is recorded in the dedicated 12004
    # declaration-context contract; DTO reuse does not alias an older SHA.
    if build not in (CK3_12003, CK3_12004) or build != private_native_build_identity(snapshot):
        raise ValueError("native ordinary holy-war declaration context belongs to another build")
    if type(value["available"]) is not bool:
        raise ValueError("native ordinary holy-war declaration context availability is malformed")
    _reason(value["unavailable_reason"], available=value["available"], name="context")
    for key in ("capture_epoch", "public_revision", "native_revision"):
        _integer(value[key], key, 1, (1 << 64) - 1)
    _integer(value["date_raw"], "date_raw", -(1 << 31), (1 << 31) - 1)
    _integer(value["played_character_id"], "played_character_id", -(1 << 31), (1 << 31) - 1)
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or value["played_character_id"] != actor.get("character_id")
            or value["date_raw"] != snapshot.get("date_raw")
            or value["public_revision"] != snapshot.get("revision")
            or value["native_revision"] != snapshot.get("native_revision")
            or value["declaration_id"] != declaration_id):
        raise ValueError("native ordinary holy-war declaration context differs from its queried frame")
    raw_selected = value["selected_declaration"]
    if not isinstance(raw_selected, dict) or set(raw_selected) != SELECTED_FIELDS:
        raise ValueError("native ordinary holy-war selected declaration identity is malformed")
    # Run the existing row contract as well: bool-as-int must not join equal to
    # a full native ID, and ordered title arrays must remain unchanged.
    canonical = selected_ordinary_holy_war_declaration(
        {"declarable_wars": [{**raw_selected, "declaration_id": declaration_id}]},
        declaration_id,
    )
    if canonical != dict(selected_declaration):
        raise ValueError("native ordinary holy-war selected declaration differs from the request")
    for key in _ROLES:
        if value[key] is not None:
            _integer(value[key], key, -(1 << 31), (1 << 31) - 1)
    for key in (*_FALLBACKS, "final_can_send"):
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native ordinary holy-war nullable flag is malformed: {key}")
    if value["available"]:
        if any(value[key] is None for key in (*_ROLES, *_FALLBACKS, "final_can_send")):
            raise ValueError("native ordinary holy-war context lost its actual native roles")
        # Native fallback changes the pointer passed into the scope evaluator;
        # it never rewrites the raw role ID into a current-player substitute.
    elif value["final_can_send"] is not None:
        raise ValueError("native ordinary holy-war unread final gate acquired an invented boolean")

    cost = value["cb_cost"]
    if not isinstance(cost, dict) or set(cost) != _COST_FIELDS or type(cost["available"]) is not bool:
        raise ValueError("native ordinary holy-war CB cost schema is malformed")
    _reason(cost["unavailable_reason"], available=cost["available"], name="cb_cost")
    if cost["resource_keys"] != list(RESOURCE_KEYS):
        raise ValueError("native ordinary holy-war CB resource order is malformed")
    _integer(cost["raw_scale"], "raw_scale", 100000, 100000)
    raw = cost["resource_costs_raw"]
    if cost["available"]:
        if not value["available"] or not isinstance(raw, list) or len(raw) != len(RESOURCE_KEYS):
            raise ValueError("native ordinary holy-war CB cost lost its selected native context or ten terms")
        for item in raw:
            _integer(item, "resource_costs_raw[]", -(1 << 63), (1 << 63) - 1)
    elif raw is not None:
        raise ValueError("native ordinary holy-war unread CB cost acquired an invented vector")
    if (value["generic_interaction_cost_raw"] is not None
            or value["total_declaration_cost_raw"] is not None
            or value["total_cost_ready"] is not False):
        raise ValueError("native ordinary holy-war CB quote was misrepresented as total declaration cost")
    return deepcopy(value)
