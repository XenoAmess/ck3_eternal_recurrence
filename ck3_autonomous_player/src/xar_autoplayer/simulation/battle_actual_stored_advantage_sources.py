"""Immutable actual append rows; side sign is the only derived amount."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class StoredAdvantageRow:
    effect_key: str | None
    key_unavailable_reason: str | None
    contribution_raw: int


@dataclass(frozen=True)
class StoredAdvantageSide:
    side_index: int
    rows: tuple[StoredAdvantageRow, ...] | None
    unavailable_reason: str | None


@dataclass(frozen=True)
class ActualStoredAdvantageInputs:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    base_advantage_raw: int
    resolved_advantage_raw: int
    sides: tuple[StoredAdvantageSide, ...]


def adapt_actual_stored_advantage_sources(
    diagnostic: Mapping[str, object],
) -> ActualStoredAdvantageInputs | None:
    """Accept the independent qualified diagnostic produced by the service."""
    if diagnostic.get("current_frame_qualified") is not True:
        return None
    stored = diagnostic.get("stored_inputs")
    if stored is None:
        return None
    source = diagnostic["source"]
    sides = tuple(StoredAdvantageSide(
        side_index=side["side_index"],
        rows=None if side["rows"] is None else tuple(StoredAdvantageRow(
            row["effect_key"], row["key_unavailable_reason"], row["contribution_raw"],
        ) for row in side["rows"]),
        unavailable_reason=side["unavailable_reason"],
    ) for side in stored["sides"])
    return ActualStoredAdvantageInputs(
        combat_id=source["combat_id"], province_id=source["province_id"],
        snapshot_revision=source["snapshot_revision"], observed_date_raw=source["observed_date_raw"],
        base_advantage_raw=stored["base_advantage_raw"],
        resolved_advantage_raw=stored["resolved_advantage_raw"], sides=sides,
    )


def evaluate_actual_stored_advantage_sources(inputs: ActualStoredAdvantageInputs) -> dict[str, object]:
    sides = []
    for side in inputs.sides:
        rows = None if side.rows is None else [{
            "native_ordinal": ordinal,
            "effect_key": row.effect_key,
            "key_unavailable_reason": row.key_unavailable_reason,
            "retained_contribution_raw": row.contribution_raw,
            "signed_contribution_raw": row.contribution_raw if side.side_index == 0
                else ((-row.contribution_raw + (1 << 63)) % (1 << 64)) - (1 << 63),
        } for ordinal, row in enumerate(side.rows)]
        sides.append({"side_index": side.side_index, "ready": rows is not None,
                      "rows": rows, "unavailable_reason": side.unavailable_reason})
    return {
        "schema_version": 1, "mode": "actual_current_combat_stored_advantage_sources",
        "ready": all(side["ready"] for side in sides), "stored_values_ready": True,
        "scale": 100000, "combat_id": inputs.combat_id, "province_id": inputs.province_id,
        "snapshot_revision": inputs.snapshot_revision, "observed_date_raw": inputs.observed_date_raw,
        "base_advantage_raw": inputs.base_advantage_raw,
        "resolved_advantage_raw": inputs.resolved_advantage_raw, "sides": sides,
        "amount_source": "actual_stored_effect_ledger_row_8",
        "base_source": "actual_stored_combat_6C8",
        "resolved_source": "actual_stored_combat_710_at_last_native_resolve",
        "complete_advantage_ready": False, "base_reconstructed_from_rows": False,
        "historical_constructor_stage_observed": False, "future_contact_preview": False,
    }
