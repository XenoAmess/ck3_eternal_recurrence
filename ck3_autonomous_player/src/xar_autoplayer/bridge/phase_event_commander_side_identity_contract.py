"""Optional same-query physical Side Commander full-ID equality for V2.

This readonly identity observation does not admit a native candidate or alter
precontact role, base input completeness, MC, trigger, selection or effects.
"""

from __future__ import annotations

import copy


PHASE_EVENT_COMMANDER_SIDE_IDENTITY_LEAF = "phase_event_commander_side_identity_v1"
PHASE_EVENT_COMMANDER_SIDE_IDENTITY_SCOPE = "v2_roster_current_physical_side_commander_identity"
PHASE_EVENT_COMMANDER_SIDE_IDENTITY_CK3_SHA256 = (
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
)
_UINT32_MAX = 0xFFFFFFFF
_ROOT_KEYS = {
    "schema_version", "scope", "status", "source_ck3_sha256",
    "commander_side_identity_source_closed", "native_candidate_admission_observed",
    "complete_phase_effects_ready", "unavailable_reason", "occurrences",
}
_ROW_KEYS = {
    "occurrence_index", "character_id", "source_public_cunit_id",
    "source_native_carmy_id", "encounter_role", "status", "unavailable_reason",
    "actual_physical_army_full_id_raw", "actual_selected_combat_full_id_raw",
    "source_active_combat", "attacker_membership_count", "defender_membership_count",
    "unique_physical_membership", "actual_side_index", "actual_side_role",
    "actual_side_parent_matches_selected_combat", "actual_side_commander_full_id_raw",
    "actual_side_commander_present", "full_id_equal",
}
_SIDE_FIELDS = (
    "actual_side_index", "actual_side_role", "actual_side_parent_matches_selected_combat",
    "actual_side_commander_full_id_raw", "actual_side_commander_present", "full_id_equal",
)


def _object(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} keys are malformed")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def _nullable_integer(value: object, name: str, minimum: int, maximum: int) -> int | None:
    return None if value is None else _integer(value, name, minimum, maximum)


def _nullable_bool(value: object, name: str) -> bool | None:
    if value is not None and type(value) is not bool:
        raise ValueError(f"{name} must be bool or null")
    return value


def _status_reason(row: dict[str, object], name: str, statuses: tuple[str, ...]) -> str:
    status, reason = row["status"], row["unavailable_reason"]
    if status not in statuses:
        raise ValueError(f"{name} status is malformed")
    if reason is not None and (type(reason) is not str or not reason):
        raise ValueError(f"{name} reason must be a nonempty string or null")
    if (status == "available") != (reason is None):
        raise ValueError(f"{name} status/reason differs")
    return status


def _expected_commanders(armies: list[dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    ordinal = 0
    for army in armies:
        commander = army.get("commander")
        if isinstance(commander, dict) and commander.get("status") == "available":
            result.append({
                "occurrence_index": ordinal, "character_id": commander["character_id"],
                "source_public_cunit_id": army["army_id"],
                "source_native_carmy_id": army["native_carmy_id"],
                "encounter_role": army["encounter_role"],
            })
            ordinal += 1
        knights = army.get("knights")
        members = knights.get("members") if isinstance(knights, dict) else None
        ordinal += len(members) if isinstance(members, list) else 0
    return result


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "schema_version": 1, "scope": PHASE_EVENT_COMMANDER_SIDE_IDENTITY_SCOPE,
        "status": "unavailable",
        "source_ck3_sha256": PHASE_EVENT_COMMANDER_SIDE_IDENTITY_CK3_SHA256,
        "commander_side_identity_source_closed": False,
        "native_candidate_admission_observed": False, "complete_phase_effects_ready": False,
        "unavailable_reason": f"phase_event_commander_side_identity_fragment_invalid: {reason}",
        "occurrences": [],
    }


def normalize_phase_event_commander_side_identity_v1(
    value: object, *, armies: list[dict[str, object]],
) -> dict[str, object] | None:
    """Normalize local true/false/unknown identity observations, preserving base gates."""
    if value is None:
        return None
    try:
        root = _object(value, _ROOT_KEYS, "root")
        if type(root["schema_version"]) is not int or root["schema_version"] != 1:
            raise ValueError("schema_version must be 1")
        if root["scope"] != PHASE_EVENT_COMMANDER_SIDE_IDENTITY_SCOPE:
            raise ValueError("scope is malformed")
        if root["source_ck3_sha256"] != PHASE_EVENT_COMMANDER_SIDE_IDENTITY_CK3_SHA256:
            raise ValueError("source is not the exact actual4 executable")
        root_status = _status_reason(root, "root", ("available", "partial", "unavailable"))
        closed = root["commander_side_identity_source_closed"]
        if type(closed) is not bool:
            raise ValueError("commander_side_identity_source_closed must be bool")
        for field in ("native_candidate_admission_observed", "complete_phase_effects_ready"):
            if root[field] is not False:
                raise ValueError(f"{field} must remain false")
        expected = _expected_commanders(armies)
        rows = root["occurrences"]
        if not isinstance(rows, list) or len(rows) != len(expected):
            raise ValueError("occurrences differ from the V2 Commander roster")
        available_count = 0
        for index, (raw_row, source) in enumerate(zip(rows, expected, strict=True)):
            row = _object(raw_row, _ROW_KEYS, f"occurrences[{index}]")
            status = _status_reason(row, f"occurrences[{index}]", ("available", "unavailable"))
            _integer(row["occurrence_index"], "occurrence_index", 0, 2**31 - 1)
            _integer(row["character_id"], "character_id", 0, _UINT32_MAX)
            _integer(row["source_public_cunit_id"], "source_public_cunit_id", -(2**31), 2**31 - 1)
            _nullable_integer(row["source_native_carmy_id"], "source_native_carmy_id", -(2**31), 2**31 - 1)
            if any(row[field] != observed for field, observed in source.items()):
                raise ValueError(f"occurrences[{index}] changes V2 Commander provenance")
            physical = _nullable_integer(row["actual_physical_army_full_id_raw"], "physical Army fullID", 0, _UINT32_MAX)
            combat = _nullable_integer(row["actual_selected_combat_full_id_raw"], "selected Combat fullID", 0, _UINT32_MAX)
            commander = _nullable_integer(row["actual_side_commander_full_id_raw"], "Side Commander fullID", 0, _UINT32_MAX)
            native_army = source["source_native_carmy_id"]
            physical_matches = (native_army is not None and native_army != -1
                                and physical is not None
                                and physical == (native_army & _UINT32_MAX))
            active = _nullable_bool(row["source_active_combat"], "source_active_combat")
            unique = _nullable_bool(row["unique_physical_membership"], "unique_physical_membership")
            parent = _nullable_bool(row["actual_side_parent_matches_selected_combat"], "Side parent match")
            present = _nullable_bool(row["actual_side_commander_present"], "Side Commander presence")
            equal = _nullable_bool(row["full_id_equal"], "full_id_equal")
            attacker = _nullable_integer(row["attacker_membership_count"], "attacker_membership_count", 0, _UINT32_MAX)
            defender = _nullable_integer(row["defender_membership_count"], "defender_membership_count", 0, _UINT32_MAX)
            side_index = _nullable_integer(row["actual_side_index"], "actual_side_index", 0, 1)
            if row["actual_side_role"] not in (None, "attacker", "defender"):
                raise ValueError("actual_side_role is malformed")
            expected_unique = None if attacker is None or defender is None else ((attacker > 0) != (defender > 0))
            if unique is not expected_unique:
                raise ValueError("uniqueness differs from observed physical side membership counts")
            if active is True and (not physical_matches or combat is None or combat == _UINT32_MAX):
                raise ValueError("active Combat lacks valid physical Army/full Combat operands")
            if active is not True:
                if any(row[field] is not None for field in (
                    "attacker_membership_count", "defender_membership_count",
                    "unique_physical_membership", *_SIDE_FIELDS,
                )):
                    raise ValueError("inactive/unread Combat must not supply Side/equality fields")
                if active is False and row["unavailable_reason"] != "physical_army_not_in_active_combat":
                    raise ValueError("measured inactive Combat requires its local reason")
            elif unique is True:
                expected_side = 0 if attacker > 0 else 1
                expected_role = "attacker" if expected_side == 0 else "defender"
                if side_index != expected_side or row["actual_side_role"] != expected_role:
                    raise ValueError("Side orientation differs from actual physical membership")
                expected_present = None if commander is None else commander != _UINT32_MAX
                if present is not expected_present:
                    raise ValueError("Commander presence differs from observed full raw ID")
            elif any(row[field] is not None for field in _SIDE_FIELDS):
                raise ValueError("nonunique/unread membership must not select a Side or equality")
            if equal is not None:
                if not (closed and active is True and unique is True and parent is True
                        and commander is not None):
                    raise ValueError("identity equality lacks source-qualified current Side operands")
                if equal is not (commander == source["character_id"]):
                    raise ValueError("identity equality differs from FULL uint32 CharacterID")
            if (status == "available") != (equal is not None):
                raise ValueError("available row must retain a measured true or false comparison")
            available_count += int(status == "available")
        expected_status = (
            "available" if available_count == len(rows)
            else "partial" if available_count else "unavailable"
        )
        if root_status != expected_status:
            raise ValueError("root status differs from local comparison availability")
        return copy.deepcopy(root)
    except (ValueError, KeyError, TypeError) as error:
        return _unavailable(str(error))
