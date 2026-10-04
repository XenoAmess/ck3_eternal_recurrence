"""Strict production contract for the paused full-CombatID lifecycle query."""

from __future__ import annotations

from .public_unit_contract import (
    public_cunit_id as _public_cunit_id,
    public_cunit_ids as _public_cunit_ids,
)

from typing import Final

from .battle_native_owner_recall_inputs_contract import (
    normalize_battle_native_owner_recall_inputs_v1,
)


QUERY_BATTLE_TRANSITION_V1_CAPABILITY: Final = (
    "game.command.query-battle-transition-v1-N"
)
QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX: Final = (
    "query-battle-transition-v1-"
)
BATTLE_TRANSITION_V1_CONTRACT_STAGE: Final = (
    "production_exact_combat_lifecycle"
)

_STATUSES: Final = {
    "available",
    "combat_not_found",
    "state_changed",
    "unavailable",
}
_FIELDS: Final = {
    "schema_version",
    "contract_stage",
    "status",
    "battle_transition_ready",
    "snapshot_revision",
    "observed_date_raw",
    "combat_id",
    "province_id",
    "phase",
    "phase_raw",
    "phase_day",
    "winner_side",
    "winner_raw",
    "forced_winner_side",
    "forced_winner_raw",
    "finalized",
    "battle_result_id",
    "attacker_public_cunit_ids_in_stored_order",
    "defender_public_cunit_ids_in_stored_order",
}
_OPTIONAL_FIELDS: Final = {"current_observation", "native_owner_recall_inputs_v1"}
_CURRENT_OBSERVATION_FIELDS: Final = {
    "status",
    "unavailable_reason",
    "scale",
    "base_combat_width",
    "final_combat_width",
    "base_advantage_raw",
    "resolved_advantage_raw",
    "attacker",
    "defender",
}
_CURRENT_SIDE_RAW_FIELDS: Final = {
    "derived_current_fighting_raw",
    "derived_soft_casualties_raw",
    "derived_main_fighting_entry_hard_casualties_raw",
    "non_main_start_minus_current_minus_soft_raw",
    "participant_hard_total_raw",
}
_PHASES: Final = {0: "maneuver", 1: "main", 2: "pursuit", 3: "done"}
_WINNERS: Final = {-1: "none", 0: "attacker", 1: "defender"}


def _int(
    value: object,
    field: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{field} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _positive_int32(value: object, field: str) -> int:
    return _int(value, field, minimum=1, maximum=2**31 - 1)


def _optional_positive_int32(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _positive_int32(value, field)


def _full_component_id(value: object, field: str) -> int:
    result = _int(value, field, minimum=-(2**31), maximum=2**31 - 1)
    if result == -1:
        raise ValueError(f"{field} must not be the missing-ID sentinel")
    return result


def _optional_full_component_id(value: object, field: str) -> int | None:
    return None if value is None else _full_component_id(value, field)


def _ordered_ids(value: object, field: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result = [
        _positive_int32(row, f"{field}[{index}]")
        for index, row in enumerate(value)
    ]
    if len(set(result)) != len(result):
        raise ValueError(f"{field} must not contain duplicate full IDs")
    return result


def _current_side(value: object, field: str) -> dict[str, object]:
    fields = {*_CURRENT_SIDE_RAW_FIELDS, "participant_hard_ledger"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{field} must contain exactly the current side fields")
    result: dict[str, object] = {
        key: _int(value[key], f"{field}.{key}", minimum=0, maximum=2**63 - 1)
        for key in _CURRENT_SIDE_RAW_FIELDS
    }
    ledger = value["participant_hard_ledger"]
    if not isinstance(ledger, list):
        raise ValueError(f"{field}.participant_hard_ledger must be a list")
    normalized_ledger: list[dict[str, int]] = []
    for index, row in enumerate(ledger):
        row_field = f"{field}.participant_hard_ledger[{index}]"
        if not isinstance(row, dict) or set(row) != {
            "participant_character_id",
            "hard_casualties_raw",
        }:
            raise ValueError(f"{row_field} must contain exactly the ledger fields")
        normalized_ledger.append({
            "participant_character_id": _positive_int32(
                row["participant_character_id"],
                f"{row_field}.participant_character_id",
            ),
            "hard_casualties_raw": _int(
                row["hard_casualties_raw"],
                f"{row_field}.hard_casualties_raw",
                minimum=0,
                maximum=2**63 - 1,
            ),
        })
    if result["participant_hard_total_raw"] != sum(
        row["hard_casualties_raw"] for row in normalized_ledger
    ):
        raise ValueError(f"{field}.participant_hard_total_raw disagrees with ledger")
    result["participant_hard_ledger"] = normalized_ledger
    return result


def _current_observation(
    value: object, *, lifecycle_status: str
) -> dict[str, object] | None:
    field = "battle_transition_snapshot.current_observation"
    if value is None:
        return None
    if lifecycle_status != "available":
        raise ValueError(f"{field} requires an available lifecycle")
    if not isinstance(value, dict) or set(value) != _CURRENT_OBSERVATION_FIELDS:
        raise ValueError(f"{field} must contain exactly the current observation fields")
    status = value["status"]
    if not isinstance(status, str) or status not in {"available", "unavailable"}:
        raise ValueError(f"{field}.status is invalid")
    scale = _int(value["scale"], f"{field}.scale", minimum=100000, maximum=100000)
    if status == "unavailable":
        reason = value["unavailable_reason"]
        if not isinstance(reason, str) or not reason:
            raise ValueError(f"{field}.unavailable_reason must be nonempty")
        nullable = _CURRENT_OBSERVATION_FIELDS - {
            "status", "unavailable_reason", "scale"
        }
        if any(value[key] is not None for key in nullable):
            raise ValueError(f"{field} unavailable leaf invented current observations")
        return {**value, "scale": scale}
    if value["unavailable_reason"] is not None:
        raise ValueError(f"{field}.unavailable_reason must be null when available")
    return {
        **value,
        "scale": scale,
        "base_combat_width": _int(
            value["base_combat_width"], f"{field}.base_combat_width",
            minimum=0, maximum=2**31 - 1,
        ),
        "final_combat_width": _int(
            value["final_combat_width"], f"{field}.final_combat_width",
            minimum=0, maximum=2**31 - 1,
        ),
        "base_advantage_raw": _int(
            value["base_advantage_raw"], f"{field}.base_advantage_raw",
            minimum=-(2**63), maximum=2**63 - 1,
        ),
        "resolved_advantage_raw": _int(
            value["resolved_advantage_raw"], f"{field}.resolved_advantage_raw",
            minimum=-(2**63), maximum=2**63 - 1,
        ),
        "attacker": _current_side(value["attacker"], f"{field}.attacker"),
        "defender": _current_side(value["defender"], f"{field}.defender"),
    }


def query_battle_transition_v1_step(combat_id: int) -> str:
    combat_id = _full_component_id(combat_id, "combat_id")
    return f"{QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX}{combat_id}"


def parse_query_battle_transition_v1_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX
    ):
        return None
    suffix = step.removeprefix(QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX)
    if not suffix.isascii():
        return None
    try:
        value = int(suffix)
    except ValueError:
        return None
    return (
        value
        if -(2**31) <= value <= 2**31 - 1
        and value != -1
        and str(value) == suffix
        else None
    )


def normalize_battle_transition_v1(
    value: object,
    *,
    expected_combat_id: int,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one exact wire frame; reject omitted and invented state."""

    expected_combat_id = _full_component_id(
        expected_combat_id, "expected_combat_id"
    )
    expected_observed_date_raw = _int(
        expected_observed_date_raw,
        "expected_observed_date_raw",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    expected_snapshot_revision = _int(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    if (
        not isinstance(value, dict)
        or not _FIELDS <= set(value)
        or set(value) - _FIELDS - _OPTIONAL_FIELDS
    ):
        raise ValueError(
            "battle_transition_snapshot must contain the v1 fields and "
            "only supported optional fields"
        )
    if value.get("schema_version") != 1:
        raise ValueError("battle_transition_snapshot.schema_version must be 1")
    if value.get("contract_stage") != BATTLE_TRANSITION_V1_CONTRACT_STAGE:
        raise ValueError("battle_transition_snapshot.contract_stage is invalid")
    status = value.get("status")
    if not isinstance(status, str) or status not in _STATUSES:
        raise ValueError("battle_transition_snapshot.status is invalid")
    ready = value.get("battle_transition_ready")
    expected_ready = status in {"available", "combat_not_found"}
    if not isinstance(ready, bool) or ready is not expected_ready:
        raise ValueError(
            "battle_transition_snapshot.battle_transition_ready disagrees "
            "with status"
        )
    snapshot_revision = _int(
        value.get("snapshot_revision"),
        "battle_transition_snapshot.snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    observed_date_raw = _int(
        value.get("observed_date_raw"),
        "battle_transition_snapshot.observed_date_raw",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    combat_id = _full_component_id(
        value.get("combat_id"), "battle_transition_snapshot.combat_id"
    )
    if snapshot_revision != expected_snapshot_revision:
        raise ValueError("battle_transition_snapshot revision binding changed")
    if observed_date_raw != expected_observed_date_raw:
        raise ValueError("battle_transition_snapshot date binding changed")
    if combat_id != expected_combat_id:
        raise ValueError("battle_transition_snapshot CombatID binding changed")

    native_owner_recall_inputs = (
        {"native_owner_recall_inputs_v1": normalize_battle_native_owner_recall_inputs_v1(
            value["native_owner_recall_inputs_v1"], lifecycle_status=status
        )}
        if "native_owner_recall_inputs_v1" in value
        else {}
    )
    current_observation = (
        {"current_observation": _current_observation(
            value["current_observation"], lifecycle_status=status
        )}
        if "current_observation" in value
        else {}
    )

    attacker_ids = _public_cunit_ids(
        value.get("attacker_public_cunit_ids_in_stored_order"),
        "battle_transition_snapshot.attacker_public_cunit_ids_in_stored_order",
    )
    defender_ids = _public_cunit_ids(
        value.get("defender_public_cunit_ids_in_stored_order"),
        "battle_transition_snapshot.defender_public_cunit_ids_in_stored_order",
    )
    if set(attacker_ids) & set(defender_ids):
        raise ValueError("battle_transition_snapshot sides overlap")

    if status != "available":
        nullable = (
            "province_id",
            "phase",
            "phase_raw",
            "phase_day",
            "winner_side",
            "winner_raw",
            "forced_winner_side",
            "forced_winner_raw",
            "finalized",
            "battle_result_id",
        )
        if any(value.get(field) is not None for field in nullable):
            raise ValueError(
                "non-available battle_transition_snapshot invented lifecycle state"
            )
        if attacker_ids or defender_ids:
            raise ValueError(
                "non-available battle_transition_snapshot invented side state"
            )
        return {
            **value,
            **current_observation,
            **native_owner_recall_inputs,
            "attacker_public_cunit_ids_in_stored_order": attacker_ids,
            "defender_public_cunit_ids_in_stored_order": defender_ids,
        }

    province_id = _positive_int32(
        value.get("province_id"), "battle_transition_snapshot.province_id"
    )
    phase_raw = _int(
        value.get("phase_raw"),
        "battle_transition_snapshot.phase_raw",
        minimum=0,
        maximum=3,
    )
    phase = value.get("phase")
    if phase != _PHASES[phase_raw]:
        raise ValueError("battle_transition_snapshot phase pair is invalid")
    phase_day = _int(
        value.get("phase_day"),
        "battle_transition_snapshot.phase_day",
        minimum=0,
        maximum=2**31 - 1,
    )
    winner_raw = _int(
        value.get("winner_raw"),
        "battle_transition_snapshot.winner_raw",
        minimum=-1,
        maximum=1,
    )
    winner_side = value.get("winner_side")
    if winner_side != _WINNERS[winner_raw]:
        raise ValueError("battle_transition_snapshot winner pair is invalid")
    forced_winner_raw = _int(
        value.get("forced_winner_raw"),
        "battle_transition_snapshot.forced_winner_raw",
        minimum=-1,
        maximum=1,
    )
    forced_winner_side = value.get("forced_winner_side")
    if forced_winner_side != _WINNERS[forced_winner_raw]:
        raise ValueError(
            "battle_transition_snapshot forced-winner pair is invalid"
        )
    finalized = value.get("finalized")
    if not isinstance(finalized, bool):
        raise ValueError("battle_transition_snapshot.finalized must be boolean")
    battle_result_id = _optional_full_component_id(
        value.get("battle_result_id"),
        "battle_transition_snapshot.battle_result_id",
    )
    return {
        **value,
        **current_observation,
            **native_owner_recall_inputs,
        "province_id": province_id,
        "phase": phase,
        "phase_raw": phase_raw,
        "phase_day": phase_day,
        "winner_side": winner_side,
        "winner_raw": winner_raw,
        "forced_winner_side": forced_winner_side,
        "forced_winner_raw": forced_winner_raw,
        "finalized": finalized,
        "battle_result_id": battle_result_id,
        "attacker_public_cunit_ids_in_stored_order": attacker_ids,
        "defender_public_cunit_ids_in_stored_order": defender_ids,
    }
