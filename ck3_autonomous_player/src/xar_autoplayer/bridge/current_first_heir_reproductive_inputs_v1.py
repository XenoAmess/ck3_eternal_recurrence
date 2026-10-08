"""Optional existing-query observation of the current heir's household inputs."""

from __future__ import annotations

from copy import deepcopy

from .driver import BridgeUnavailableError
from .player_child_marriage_value_private_transport import _native_fertility_input_valid

LEAF = "current_first_heir_reproductive_inputs_v1"


def validate_current_first_heir_reproductive_inputs_v1(
    value: object, *, actor: int, heir: int | None, native_revision: int,
    date_raw: int, relation: dict[str, object],
) -> dict[str, object]:
    """Retain native zero and signed raw values as independent readonly evidence."""
    if not isinstance(value, dict):
        raise BridgeUnavailableError("current household inputs are malformed")
    status, reason, rows = (value.get(key) for key in ("status", "unavailable_reason", "rows"))
    if (value.get("source") != "native_current_heir_household_inputs"
            or status not in {"available", "partial", "unavailable"}
            or (reason is not None if status == "available"
                else not isinstance(reason, str) or not reason)
            or value.get("native_revision") != native_revision
            or value.get("played_character_id") not in (None, actor)
            or value.get("heir_character_id") != heir
            or value.get("date_raw") not in (None, date_raw)
            or value.get("fertility_raw_scale") != 100000
            or not isinstance(rows, list)):
        raise BridgeUnavailableError("current household inputs crossed the native frame")
    if status == "unavailable":
        if rows:
            raise BridgeUnavailableError("unavailable household retains observed rows")
        return deepcopy(value)
    if (value.get("played_character_id") != actor or value.get("date_raw") != date_raw
            or relation.get("status") != "available" or heir is None):
        raise BridgeUnavailableError("available household lacks its current relation")
    expected: dict[int, list[str]] = {}

    def add(character_id: object, role: str) -> None:
        if type(character_id) is int and character_id > 0:
            roles = expected.setdefault(character_id, [])
            if role not in roles:
                roles.append(role)

    add(heir, "heir")
    add(relation.get("primary_spouse_character_id"), "primary_spouse")
    for character_id in relation.get("spouse_character_ids", []):
        add(character_id, "spouse")
    add(relation.get("betrothed_character_id"), "betrothed")
    if len(rows) != len(expected):
        raise BridgeUnavailableError("household receivers differ from the current relation")
    all_available = True
    for row, (character_id, roles) in zip(rows, expected.items()):
        if (not isinstance(row, dict) or row.get("character_id") != character_id
                or row.get("roles") != roles or row.get("status") not in {"available", "unavailable"}):
            raise BridgeUnavailableError("household receiver identity changed")
        if "native_pregnancy" in row:
            pregnancy = row["native_pregnancy"]
            if (not isinstance(pregnancy, dict)
                    or pregnancy.get("source") != "native_is_pregnant"
                    or pregnancy.get("status") not in {"available", "unavailable"}
                    or "unavailable_reason" not in pregnancy
                    or "is_pregnant" not in pregnancy):
                raise BridgeUnavailableError("native household pregnancy is malformed")
            if pregnancy["status"] == "available":
                if (pregnancy["unavailable_reason"] is not None
                        or type(pregnancy["is_pregnant"]) is not bool):
                    raise BridgeUnavailableError("available native pregnancy lacks its boolean")
            elif (pregnancy["is_pregnant"] is not None
                    or not isinstance(pregnancy["unavailable_reason"], str)
                    or not pregnancy["unavailable_reason"]):
                raise BridgeUnavailableError("unavailable native pregnancy became a boolean")
        available = row["status"] == "available"
        all_available = all_available and available
        if available:
            fertility = row.get("native_fertility")
            if (row.get("unavailable_reason") is not None
                    or type(row.get("age_measure_raw")) is not int
                    or not -2**15 <= row["age_measure_raw"] < 2**15
                    or type(row.get("sex_selector_raw")) is not int
                    or row["sex_selector_raw"] not in (0, 1)
                    or not _native_fertility_input_valid(fertility)
                    or not -2**63 <= fertility["effective_raw"] < 2**63):
                raise BridgeUnavailableError("observed household value is malformed")
        elif (not isinstance(row.get("unavailable_reason"), str)
                or not row["unavailable_reason"]
                or any(row.get(key) is not None for key in (
                    "age_measure_raw", "sex_selector_raw", "native_fertility"))):
            raise BridgeUnavailableError("unavailable household value became native zero")
    if (status == "available") is not all_available:
        raise BridgeUnavailableError("household availability disagrees with observed values")
    return deepcopy(value)
