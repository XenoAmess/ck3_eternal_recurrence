"""Immutable current getter resolution; no native refresh or future context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CurrentDynamicAdvantageSide:
    side_index: int
    current_roll_points: int
    selected_character_id_raw: int
    side_dynamic_total_raw: int | None
    unavailable_reason: str | None


@dataclass(frozen=True)
class ActualCurrentDynamicAdvantageInputs:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    base_advantage_raw: int
    stored_resolved_advantage_raw: int
    sides: tuple[CurrentDynamicAdvantageSide, ...]


def _wrap64(value: int) -> int:
    return ((value + (1 << 63)) % (1 << 64)) - (1 << 63)


def adapt_actual_current_dynamic_advantage(
    diagnostic: Mapping[str, object],
) -> ActualCurrentDynamicAdvantageInputs | None:
    if diagnostic.get("current_frame_qualified") is not True:
        return None
    current = diagnostic.get("current_inputs")
    if current is None:
        return None
    source = diagnostic["source"]
    return ActualCurrentDynamicAdvantageInputs(
        combat_id=source["combat_id"], province_id=source["province_id"],
        snapshot_revision=source["snapshot_revision"], observed_date_raw=source["observed_date_raw"],
        base_advantage_raw=current["base_advantage_raw"],
        stored_resolved_advantage_raw=current["stored_resolved_advantage_raw"],
        sides=tuple(CurrentDynamicAdvantageSide(
            side["side_index"], side["current_roll_points"], side["selected_character_id_raw"],
            side["side_dynamic_total_raw"], side["unavailable_reason"],
        ) for side in current["sides"]),
    )


def evaluate_actual_current_dynamic_advantage(
    inputs: ActualCurrentDynamicAdvantageInputs,
) -> dict[str, object]:
    sides = [{"side_index": side.side_index, "role": "attacker" if side.side_index == 0 else "defender",
              "ready": side.side_dynamic_total_raw is not None,
              "current_roll_points": side.current_roll_points,
              "selected_character_id_raw": side.selected_character_id_raw,
              "side_dynamic_total_raw": side.side_dynamic_total_raw,
              "unavailable_reason": side.unavailable_reason} for side in inputs.sides]
    ready = all(side["ready"] for side in sides)
    current = _wrap64(inputs.base_advantage_raw + inputs.sides[0].side_dynamic_total_raw
                      - inputs.sides[1].side_dynamic_total_raw) if ready else None
    return {
        "schema_version": 1, "mode": "actual_current_combat_direct_dynamic_advantage",
        "ready": ready, "stored_values_ready": True, "scale": 100000,
        "combat_id": inputs.combat_id, "province_id": inputs.province_id,
        "snapshot_revision": inputs.snapshot_revision, "observed_date_raw": inputs.observed_date_raw,
        "base_advantage_raw": inputs.base_advantage_raw,
        "stored_resolved_advantage_raw": inputs.stored_resolved_advantage_raw,
        "current_getter_resolution_raw": current,
        "matches_stored_resolved": current == inputs.stored_resolved_advantage_raw if ready else None,
        "current_minus_stored_raw": _wrap64(current - inputs.stored_resolved_advantage_raw) if ready else None,
        "sides": sides, "side_total_source": "actual_combat_258A470_null_explanation_sink",
        "roll_source": "actual_stored_combat_6D0_6D4",
        "selected_character_source": "actual_stored_combat_94_3DC_native_generation_or_fallback",
        "aggregate_source": "actual_cached_combat_side_110",
        "base_source": "actual_stored_combat_6C8",
        "stored_resolved_source": "actual_stored_combat_710_at_last_native_resolve",
        "native_state_refreshed": False, "historical_constructor_stage_observed": False,
        "future_contact_preview": False, "complete_forecast_ready": False,
    }
