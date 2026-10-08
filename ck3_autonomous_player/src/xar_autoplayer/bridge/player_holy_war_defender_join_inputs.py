"""Strict, read-only inputs from the native ordinary holy-war defender join set.

The owning declaration context supplies the exact .3/.4 identity and selected
declaration. A successfully observed native set remains available when an
individual faith or fervor getter fails. These inputs are not final join scores.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import NoReturn

from .version_identity import CK3_12003, CK3_12004


SCHEMA = "ck3_12003_holy_war_defender_join_inputs_v1"
SCHEMA12004 = "ck3_12004_holy_war_defender_join_inputs_v1"
DOMAIN_KEY = "player_holy_war_defender_join_inputs"
_FIELDS = frozenset({
    "schema", "read_only", "available", "unavailable_reason",
    "capture_epoch", "native_revision", "public_revision", "date_raw",
    "played_character_id", "declaration_id", "selected_declaration",
    "primary_attacker_character_id", "primary_defender_character_id",
    "primary_defender_faith_available",
    "primary_defender_faith_unavailable_reason", "primary_defender_rite_id",
    "primary_defender_faith_id", "cb_flags_raw", "defender_faith_can_join",
    "native_joiner_set_observed", "joiner_count", "joiners",
    "raw_scale", "unit", "is_final_join_score",
})
_ROW_FIELDS = frozenset({
    "character_id", "row_faith_available", "row_fervor_available",
    "unavailable_reason", "rite_id", "faith_id", "faith_fervor_raw",
    "matches_primary_defender_faith",
})
_SELECTED_FIELDS = frozenset({
    "target_character_id", "casus_belli_index", "casus_belli_key",
    "configuration_index", "claimant_character_id", "target_title_ids",
})
_ORDINARY_HOLY_WAR_KEYS = frozenset({
    "minor_religious_war", "religious_war", "major_religious_war",
})
_UINT32_MAX = (1 << 32) - 1
_UINT64_MAX = (1 << 64) - 1
_INT32_MIN = -(1 << 31)
_INT32_MAX = (1 << 31) - 1
_INT64_MIN = -(1 << 63)
_INT64_MAX = (1 << 63) - 1


def _fail(message: str) -> NoReturn:
    raise ValueError(f"{SCHEMA}: {message}")


def _object(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _fail(f"{name} must be an object")
    return value


def _integer(
    value: object, name: str, minimum: int, maximum: int, *, nullable: bool = False,
) -> int | None:
    if nullable and value is None:
        return None
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _boolean(value: object, name: str, *, nullable: bool = False) -> bool | None:
    if nullable and value is None:
        return None
    if type(value) is not bool:
        _fail(f"{name} must be a boolean")
    return value


def _reason(value: object, name: str, available: bool) -> None:
    if available:
        if value is not None:
            _fail(f"{name} must be null when available")
    elif not isinstance(value, str) or not value.strip():
        _fail(f"{name} must identify the unavailable stage")


def _selected(value: object, name: str) -> Mapping[str, object]:
    selected = _object(value, name)
    if set(selected) != _SELECTED_FIELDS:
        _fail(f"{name} has unexpected fields")
    for key in ("target_character_id", "casus_belli_index"):
        _integer(selected[key], f"{name}.{key}", 0, _INT32_MAX)
    for key in ("configuration_index", "claimant_character_id"):
        _integer(selected[key], f"{name}.{key}", -1, _INT32_MAX)
    if (not isinstance(selected["casus_belli_key"], str)
            or selected["casus_belli_key"] not in _ORDINARY_HOLY_WAR_KEYS):
        _fail(f"{name}.casus_belli_key must select an ordinary holy war")
    titles = selected["target_title_ids"]
    if not isinstance(titles, list):
        _fail(f"{name}.target_title_ids must be an ordered list")
    for ordinal, title in enumerate(titles):
        _integer(title, f"{name}.target_title_ids[{ordinal}]", 0, _INT32_MAX)
    return selected


def normalize_holy_war_defender_join_inputs(
    value: object, *, current_context: Mapping[str, object],
    snapshot: Mapping[str, object],
) -> dict[str, object]:
    """Bind the optional native sibling to its already normalized owner/frame."""
    inputs = _object(value, DOMAIN_KEY)
    context = _object(current_context, "current_context")
    observed_snapshot = _object(snapshot, "snapshot")
    if set(inputs) != _FIELDS:
        _fail("unexpected top-level fields")
    build = CK3_12004 if context.get("game_version") == CK3_12004.game_version else CK3_12003
    expected_schema = SCHEMA12004 if build == CK3_12004 else SCHEMA
    if inputs["schema"] != expected_schema:
        _fail("unexpected schema")
    if inputs["read_only"] is not True:
        _fail("read_only must be true")
    if type(inputs["raw_scale"]) is not int or inputs["raw_scale"] != 100000:
        _fail("raw_scale must be 100000")
    if inputs["unit"] != "fervor_points":
        _fail("unit must be fervor_points")
    if inputs["is_final_join_score"] is not False:
        _fail("is_final_join_score must be false")

    diagnostics = _object(observed_snapshot.get("diagnostics"), "snapshot.diagnostics")
    hello = _object(diagnostics.get("hello"), "snapshot.diagnostics.hello")
    for context_key, hello_key, expected in (
        ("game_version", "expected_ck3_version", build.game_version),
        ("executable_sha256", "expected_ck3_sha256", build.executable_sha256),
    ):
        if context.get(context_key) != expected or hello.get(hello_key) != expected:
            _fail(f"exact owner identity mismatch for {context_key}")

    for key in ("capture_epoch", "native_revision", "public_revision"):
        item = _integer(inputs[key], key, 1, _UINT64_MAX)
        owner_item = _integer(context.get(key), f"current_context.{key}", 1, _UINT64_MAX)
        if item != owner_item:
            _fail(f"{key} does not match the owning context")
    for child_key, snapshot_key in (
        ("native_revision", "native_revision"), ("public_revision", "revision"),
    ):
        snapshot_revision = _integer(
            observed_snapshot.get(snapshot_key), f"snapshot.{snapshot_key}", 1, _UINT64_MAX,
        )
        if inputs[child_key] != snapshot_revision:
            _fail(f"{child_key} does not match the snapshot")
    date_raw = _integer(inputs["date_raw"], "date_raw", _INT32_MIN, _INT32_MAX)
    if date_raw != context.get("date_raw") or date_raw != observed_snapshot.get("date_raw"):
        _fail("date_raw does not match the owning context and snapshot")
    _integer(context.get("date_raw"), "current_context.date_raw", _INT32_MIN, _INT32_MAX)
    _integer(observed_snapshot.get("date_raw"), "snapshot.date_raw", _INT32_MIN, _INT32_MAX)
    played_id = _integer(inputs["played_character_id"], "played_character_id", _INT32_MIN, _INT32_MAX)
    played = _object(observed_snapshot.get("played_character"), "snapshot.played_character")
    for owner, name in (
        (context.get("played_character_id"), "current_context.played_character_id"),
        (played.get("character_id"), "snapshot.played_character.character_id"),
    ):
        if played_id != _integer(owner, name, _INT32_MIN, _INT32_MAX):
            _fail("played_character_id does not match the owning context and snapshot")
    declaration_id = inputs["declaration_id"]
    if not isinstance(declaration_id, str) or not declaration_id:
        _fail("declaration_id must be a nonempty string")
    if declaration_id != context.get("declaration_id"):
        _fail("declaration_id does not match the owning context")
    selected = _selected(inputs["selected_declaration"], "selected_declaration")
    owner_selected = _selected(context.get("selected_declaration"), "current_context.selected_declaration")
    if selected != owner_selected:
        _fail("selected_declaration does not match the owning context")

    available = _boolean(inputs["available"], "available")
    set_observed = _boolean(inputs["native_joiner_set_observed"], "native_joiner_set_observed")
    if available is not set_observed:
        _fail("availability must describe observation of the complete native set")
    _reason(inputs["unavailable_reason"], "unavailable_reason", available)

    # The exact caller passes additional +0x2EC as attacker and recipient
    # +0x2DC as defender. The played character is a separate frame identity.
    roles_complete = True
    native_fallback = False
    for child_key, owner_key, fallback_key in (
        ("primary_attacker_character_id", "context_additional_role_character_id",
         "additional_role_uses_native_fallback"),
        ("primary_defender_character_id", "context_recipient_character_id",
         "recipient_uses_native_fallback"),
    ):
        role_id = _integer(inputs[child_key], child_key, 0, _UINT32_MAX, nullable=True)
        owner_id = _integer(context.get(owner_key), f"current_context.{owner_key}",
                            _INT32_MIN, _INT32_MAX, nullable=True)
        fallback = _boolean(context.get(fallback_key), f"current_context.{fallback_key}", nullable=True)
        # Native capture casts the owner's signed role field to uint32,
        # preserving its bits, including the fallback sentinel -1.
        if role_id is not None and (owner_id is None or role_id != (owner_id & _UINT32_MAX)):
            _fail(f"{child_key} does not match the actual owning role")
        roles_complete = roles_complete and role_id is not None and fallback is False
        native_fallback = native_fallback or fallback is True
    if set_observed and not roles_complete:
        _fail("observing a native set requires both actual, non-fallback receivers")
    if native_fallback and (available or set_observed):
        _fail("native role fallback cannot claim an observed joiner set")

    primary_faith_available = _boolean(
        inputs["primary_defender_faith_available"], "primary_defender_faith_available",
    )
    _reason(inputs["primary_defender_faith_unavailable_reason"],
            "primary_defender_faith_unavailable_reason", primary_faith_available)
    primary_rite = _integer(inputs["primary_defender_rite_id"], "primary_defender_rite_id",
                            0, _UINT32_MAX, nullable=True)
    primary_faith = _integer(inputs["primary_defender_faith_id"], "primary_defender_faith_id",
                             0, _UINT32_MAX, nullable=True)
    if primary_faith_available and (primary_rite is None or primary_faith is None):
        _fail("available primary defender faith requires both observed identities")

    flags = _integer(inputs["cb_flags_raw"], "cb_flags_raw", 0, _UINT32_MAX, nullable=True)
    can_join = _boolean(inputs["defender_faith_can_join"], "defender_faith_can_join", nullable=True)
    if flags is None:
        if can_join is not None:
            _fail("defender_faith_can_join requires loaded CB flags")
    elif can_join is not bool(flags & (1 << 15)):
        _fail("defender_faith_can_join does not match CB flag bit 15")
    if set_observed and flags is None:
        _fail("an observed set requires the actual CB branch flag")

    count = _integer(inputs["joiner_count"], "joiner_count", 0, _UINT32_MAX)
    rows = inputs["joiners"]
    if not isinstance(rows, list) or len(rows) != count:
        _fail("joiners must be the complete ordered list described by joiner_count")
    if not set_observed and rows:
        _fail("an unobserved native set must have no fabricated rows")
    if can_join is False and rows:
        _fail("the disabled native branch must have an empty set")
    for ordinal, value_row in enumerate(rows):
        name = f"joiners[{ordinal}]"
        row = _object(value_row, name)
        if set(row) != _ROW_FIELDS:
            _fail(f"{name} has unexpected fields")
        _integer(row["character_id"], f"{name}.character_id", 0, _UINT32_MAX)
        faith_available = _boolean(row["row_faith_available"], f"{name}.row_faith_available")
        fervor_available = _boolean(row["row_fervor_available"], f"{name}.row_fervor_available")
        rite_id = _integer(row["rite_id"], f"{name}.rite_id", 0, _UINT32_MAX, nullable=True)
        faith_id = _integer(row["faith_id"], f"{name}.faith_id", 0, _UINT32_MAX, nullable=True)
        fervor = _integer(row["faith_fervor_raw"], f"{name}.faith_fervor_raw",
                          _INT64_MIN, _INT64_MAX, nullable=True)
        if faith_available and (rite_id is None or faith_id is None):
            _fail(f"{name} available faith requires both observed identities")
        if fervor_available and (not faith_available or fervor is None):
            _fail(f"{name} available fervor requires observed faith and raw value")
        if not fervor_available and fervor is not None:
            _fail(f"{name} failed fervor must have a null raw value")
        _reason(row["unavailable_reason"], f"{name}.unavailable_reason",
                faith_available and fervor_available)
        matches = _boolean(row["matches_primary_defender_faith"],
                           f"{name}.matches_primary_defender_faith", nullable=True)
        if faith_available and primary_faith_available:
            if matches is not (faith_id == primary_faith):
                _fail(f"{name} faith match does not compare the observed FaithIDs")
        elif matches is not None:
            _fail(f"{name} faith match must be null while either faith identity is unavailable")

    return deepcopy(dict(inputs))
