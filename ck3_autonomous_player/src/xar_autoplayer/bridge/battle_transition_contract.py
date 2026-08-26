"""Strict production contract for the paused full-CombatID lifecycle query."""

from __future__ import annotations

from typing import Final


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


def query_battle_transition_v1_step(combat_id: int) -> str:
    combat_id = _positive_int32(combat_id, "combat_id")
    return f"{QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX}{combat_id}"


def parse_query_battle_transition_v1_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX
    ):
        return None
    suffix = step.removeprefix(QUERY_BATTLE_TRANSITION_V1_STEP_PREFIX)
    if not suffix.isascii() or not suffix.isdecimal() or suffix.startswith("0"):
        return None
    try:
        value = int(suffix)
    except ValueError:
        return None
    return value if 1 <= value <= 2**31 - 1 and str(value) == suffix else None


def normalize_battle_transition_v1(
    value: object,
    *,
    expected_combat_id: int,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one exact wire frame; reject omitted and invented state."""

    expected_combat_id = _positive_int32(
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
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError(
            "battle_transition_snapshot must contain exactly the v1 fields"
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
    combat_id = _positive_int32(
        value.get("combat_id"), "battle_transition_snapshot.combat_id"
    )
    if snapshot_revision != expected_snapshot_revision:
        raise ValueError("battle_transition_snapshot revision binding changed")
    if observed_date_raw != expected_observed_date_raw:
        raise ValueError("battle_transition_snapshot date binding changed")
    if combat_id != expected_combat_id:
        raise ValueError("battle_transition_snapshot CombatID binding changed")

    attacker_ids = _ordered_ids(
        value.get("attacker_public_cunit_ids_in_stored_order"),
        "battle_transition_snapshot.attacker_public_cunit_ids_in_stored_order",
    )
    defender_ids = _ordered_ids(
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
    battle_result_id = _optional_positive_int32(
        value.get("battle_result_id"),
        "battle_transition_snapshot.battle_result_id",
    )
    return {
        **value,
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
