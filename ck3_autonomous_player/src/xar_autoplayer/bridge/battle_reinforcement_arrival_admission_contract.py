"""Strict current-state arrival admission nested in reinforcement v1.

The outer assignment/route contract is normalized first. This extension keeps
ordinary movement distinct from a native help override and never binds a
future CombatID. Ineligible incoming units may still expose current compatible
combats and a conditional joining side.
"""

from __future__ import annotations

from typing import Final, Mapping

from .public_unit_contract import public_cunit_id, public_cunit_ids


BATTLE_REINFORCEMENT_ARRIVAL_ADMISSION_V1_SCHEMA: Final = (
    "ck3.battle_reinforcement_arrival_admission.v1"
)
_FIELDS: Final = {
    "schema_version", "schema", "status", "unavailable_reason",
    "snapshot_revision", "observed_date_raw", "subject", "target",
    "eligibility_now", "raw_gates",
    "current_target_combat_ids_in_stored_order",
    "current_target_compatible_combat_ids_in_stored_order",
    "contact_if_now_selected_combat_id", "selected_combat_stored_index",
    "join_side", "current_attacker_public_cunit_ids_in_stored_order",
    "current_defender_public_cunit_ids_in_stored_order",
    "subject_current_participation_verified", "temporal_semantics",
    "future_binding",
}
_SUBJECT_FIELDS: Final = {
    "public_cunit_id", "native_carmy_id", "owner_character_id",
    "current_province_id", "active_combat_id",
}
_TARGET_FIELDS: Final = {"province_id", "provenance"}
_GATE_FIELDS: Final = {
    "province_contact_gate_enabled", "contact_game_mode_allows_contact",
    "unit_contact_state_raw", "unit_retreat_state_raw", "army_empty_for_contact",
}
_STATUSES: Final = {
    "available", "requires_paused", "subject_cunit_not_found",
    "target_province_not_found", "state_changed", "unavailable", "not_applicable",
}
_REASONS_BY_STATUS: Final = {
    "requires_paused": {"requires_paused"},
    "subject_cunit_not_found": {"subject_cunit_not_found"},
    "target_province_not_found": {"target_province_not_found"},
    "unavailable": {
        "arrival_bindings_unavailable", "snapshot_clock_mismatch",
        "subject_owner_unavailable", "combat_representative_unavailable",
        "reverse_join_side_unavailable", "arrival_read_failed",
    },
    "state_changed": {
        "army_backlink_mismatch", "subject_current_province_unavailable",
        "active_combat_identity_mismatch", "target_combat_array_unavailable",
        "target_combat_identity_mismatch", "active_combat_roster_unavailable",
        "subject_active_participation_unverified", "selected_combat_roster_unavailable",
        "arrival_observation_changed",
    },
}


def _object(value: object, name: str, fields: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the arrival admission v1 fields")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _optional_id(value: object, name: str) -> int | None:
    return None if value is None else _integer(value, name, 1, 2**31 - 1)


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be boolean")
    return value


def _combat_ids(value: object, name: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result = [_integer(item, f"{name}[{index}]", 1, 2**31 - 1)
              for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicate full IDs")
    return result


def normalize_battle_reinforcement_arrival_admission_v1(
    value: object,
    *,
    expected_selected_public_cunit_id: int,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
    selected_native_carmy_id: int | None,
    assignment: Mapping[str, object],
    route: Mapping[str, object],
) -> dict[str, object]:
    """Validate the independent nested group against its normalized outer frame."""
    expected_subject = public_cunit_id(
        expected_selected_public_cunit_id, "expected_selected_public_cunit_id"
    )
    row = _object(value, "arrival_admission", _FIELDS)
    if type(row["schema_version"]) is not int or row["schema_version"] != 1:
        raise ValueError("arrival_admission.schema_version must be 1")
    if row["schema"] != BATTLE_REINFORCEMENT_ARRIVAL_ADMISSION_V1_SCHEMA:
        raise ValueError("arrival_admission.schema is invalid")
    if row["status"] not in _STATUSES:
        raise ValueError("arrival_admission.status is invalid")
    available = row["status"] == "available"
    reason = row["unavailable_reason"]
    if row["status"] in {"available", "not_applicable"}:
        if reason is not None:
            raise ValueError("arrival_admission status requires a null reason")
    elif reason not in _REASONS_BY_STATUS[row["status"]]:
        raise ValueError("arrival_admission unavailable reason does not match its native status")
    revision = _integer(row["snapshot_revision"], "arrival_admission.snapshot_revision",
                        1, 2**64 - 1)
    date_raw = _integer(row["observed_date_raw"], "arrival_admission.observed_date_raw",
                        -(2**63), 2**63 - 1)
    if revision != expected_snapshot_revision or date_raw != expected_observed_date_raw:
        raise ValueError("arrival_admission crossed its outer native frame")
    if (row["temporal_semantics"] != "present_time_only_not_future_binding"
            or row["future_binding"] is not False):
        raise ValueError("arrival_admission cannot publish a future binding")

    subject = _object(row["subject"], "arrival_admission.subject", _SUBJECT_FIELDS)
    subject_id = public_cunit_id(subject["public_cunit_id"], "arrival_admission.subject.public_cunit_id")
    if subject_id != expected_subject:
        raise ValueError("arrival_admission subject binding changed")
    subject = {**subject, "public_cunit_id": subject_id}
    for field in _SUBJECT_FIELDS - {"public_cunit_id"}:
        subject[field] = _optional_id(subject[field], f"arrival_admission.subject.{field}")
    for field, expected in (
        ("native_carmy_id", selected_native_carmy_id),
        ("current_province_id", route["current_province_id"]),
        ("active_combat_id", assignment["active_combat_id"]),
    ):
        if available and subject[field] != expected:
            raise ValueError(f"arrival_admission.subject.{field} disagrees with its outer frame")

    target = _object(row["target"], "arrival_admission.target", _TARGET_FIELDS)
    target_id = _optional_id(target["province_id"], "arrival_admission.target.province_id")
    provenance = target["provenance"]
    if provenance not in {"native_help_override", "committed_route_final", "current_active_combat", "none"}:
        raise ValueError("arrival_admission target provenance is invalid")
    if (target_id is None) is not (provenance == "none"):
        raise ValueError("arrival_admission target and provenance disagree")
    active_id = assignment["active_combat_id"]
    help_target = assignment["assignment_target_province_id"]
    route_ids = route["route_province_ids"]
    expected_target = (
        (route["current_province_id"], "current_active_combat") if active_id is not None
        else (help_target, "native_help_override") if help_target is not None
        else (route_ids[-1], "committed_route_final") if route_ids
        else (None, "none")
    )
    if (available or row["status"] == "not_applicable" or target_id is not None):
        if (target_id, provenance) != expected_target:
            raise ValueError("arrival_admission target does not follow active/help/route precedence")

    eligibility = row["eligibility_now"]
    if eligibility not in {"eligible", "ineligible", "already_in_active_combat", "unavailable", "not_applicable"}:
        raise ValueError("arrival_admission eligibility_now is invalid")
    gates_value = row["raw_gates"]
    gates = None
    if gates_value is not None:
        gates = dict(_object(gates_value, "arrival_admission.raw_gates", _GATE_FIELDS))
        for field in {"province_contact_gate_enabled", "contact_game_mode_allows_contact", "army_empty_for_contact"}:
            gates[field] = _boolean(gates[field], f"arrival_admission.raw_gates.{field}")
        for field in {"unit_contact_state_raw", "unit_retreat_state_raw"}:
            gates[field] = _integer(gates[field], f"arrival_admission.raw_gates.{field}", -(2**31), 2**31 - 1)

    combat_ids = _combat_ids(row["current_target_combat_ids_in_stored_order"], "arrival_admission.current_target_combat_ids_in_stored_order")
    compatible_ids = _combat_ids(row["current_target_compatible_combat_ids_in_stored_order"], "arrival_admission.current_target_compatible_combat_ids_in_stored_order")
    if [item for item in combat_ids if item in set(compatible_ids)] != compatible_ids:
        raise ValueError("arrival_admission compatible combats must retain target stored order")
    selected_id = _optional_id(row["contact_if_now_selected_combat_id"], "arrival_admission.contact_if_now_selected_combat_id")
    selected_index = row["selected_combat_stored_index"]
    if selected_index is not None:
        selected_index = _integer(selected_index, "arrival_admission.selected_combat_stored_index", 0, 2**31 - 1)
        if selected_index >= len(combat_ids) or combat_ids[selected_index] != selected_id:
            raise ValueError("arrival_admission selected combat stored index disagrees")
    side = row["join_side"]
    if side not in {"none", "attacker", "defender"}:
        raise ValueError("arrival_admission joining side is invalid")
    attackers = public_cunit_ids(row["current_attacker_public_cunit_ids_in_stored_order"], "arrival_admission.current_attacker_public_cunit_ids_in_stored_order", unique=True)
    defenders = public_cunit_ids(row["current_defender_public_cunit_ids_in_stored_order"], "arrival_admission.current_defender_public_cunit_ids_in_stored_order", unique=True)
    if available and set(attackers) & set(defenders):
        raise ValueError("arrival_admission current side rosters overlap")
    verified = _boolean(row["subject_current_participation_verified"], "arrival_admission.subject_current_participation_verified")

    if available:
        if (side == "none") is not (selected_id is None):
            raise ValueError("arrival_admission joining side and selected combat disagree")
        if target_id is None or any(subject[field] is None for field in {"native_carmy_id", "owner_character_id", "current_province_id"}):
            raise ValueError("available arrival_admission lacks resolved identity or target")
        if active_id is not None:
            if eligibility != "already_in_active_combat" or selected_id != active_id or selected_index is None or gates is not None or not verified:
                raise ValueError("arrival_admission active participant must select its verified actual combat")
            own_roster = attackers if side == "attacker" else defenders
            if subject_id not in own_roster:
                raise ValueError("arrival_admission active subject is absent from its actual side roster")
        else:
            if gates is None or eligibility not in {"eligible", "ineligible"} or verified:
                raise ValueError("arrival_admission incoming subject requires current gates")
            eligible = (gates["province_contact_gate_enabled"] and gates["contact_game_mode_allows_contact"]
                        and gates["unit_contact_state_raw"] == 0
                        and gates["unit_retreat_state_raw"] <= 0 and not gates["army_empty_for_contact"])
            if (eligibility == "eligible") is not eligible:
                raise ValueError("arrival_admission eligibility disagrees with its raw gates")
            if selected_id != (compatible_ids[-1] if compatible_ids else None):
                raise ValueError("arrival_admission incoming selection must be the final compatible combat")
            if selected_id is not None and selected_index is None:
                raise ValueError("arrival_admission incoming selection lacks its stored index")
            if subject_id in attackers or subject_id in defenders:
                raise ValueError("arrival_admission incoming subject is already in the published roster")
        if selected_id is None and (attackers or defenders or selected_index is not None):
            raise ValueError("arrival_admission without a selected combat invented its roster")
    else:
        expected_eligibility = "not_applicable" if row["status"] == "not_applicable" else "unavailable"
        if eligibility != expected_eligibility:
            raise ValueError("arrival_admission unavailable status and eligibility disagree")
        # The native Fail() preserves observations reached before a failed
        # branch: gates, compatible rows, provisional selection and partial
        # rosters are evidence, not a complete current admission. Do not erase
        # those values or require a joining side that was never resolved.
        if row["status"] == "not_applicable" and (
            target_id is not None or gates is not None or combat_ids or compatible_ids
            or selected_id is not None or selected_index is not None
            or side != "none" or attackers or defenders or verified
        ):
            raise ValueError("not_applicable arrival_admission invented contact state")

    return {
        **row, "subject": subject, "target": {**target, "province_id": target_id},
        "raw_gates": gates, "current_target_combat_ids_in_stored_order": combat_ids,
        "current_target_compatible_combat_ids_in_stored_order": compatible_ids,
        "contact_if_now_selected_combat_id": selected_id,
        "selected_combat_stored_index": selected_index,
        "current_attacker_public_cunit_ids_in_stored_order": attackers,
        "current_defender_public_cunit_ids_in_stored_order": defenders,
    }
