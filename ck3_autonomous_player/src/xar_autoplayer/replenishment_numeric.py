"""Pure same-input replenishment requests for the sealed CK3 1.20.0.3 core.

This projects observed full DATA operands at RVA 0x262C9D0. It does not
simulate dispatch, physical writeback, net army gain, or future preparation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict, cast

FRACTION_SCALE = 100_000
CHUNK_COUNT = 7


class FullDataRecord(TypedDict):
    status: Literal["available", "unavailable"]
    unavailable_reason: str | None
    record_index: int
    persistent_regiment_id: int
    chunk_index: int
    maximum_soldiers: int | None
    effective_current_soldiers: int | None
    persistent_prepared_replenishment_fraction_raw: int | None
    persistent_prepared_replenishment_fraction_scale: int
    native_chunk_can_replenish: bool | None


class FullDataSnapshot(TypedDict):
    army_regiment_id: int
    status: str
    native_data_record_count: int | None
    unavailable_reason: str | None
    records: list[FullDataRecord]


class ChunkCalculation(TypedDict):
    same_input_q: int
    effective_deficit: int
    native_core_chunk_qualifies: bool
    wrapped_product: int | None
    selected_scaled_numerator: int | None


class ChunkObservation(TypedDict):
    army_id: int
    army_regiment_id: int
    record_index: int
    status: Literal["available", "unavailable"]
    unavailable_reason: str | None
    calculation: ChunkCalculation | None


class PersistentOutput(TypedDict):
    persistent_regiment_id: int
    same_input_q_by_chunk: list[int | None]
    effective_deficit_by_chunk: list[int | None]
    status_by_chunk: list[str]
    observations_by_chunk: list[list[ChunkObservation]]
    all_seven_observed: bool


class SourceSnapshot(TypedDict):
    army_id: int
    army_regiment_id: int | None
    status: str
    native_data_record_count: int | None
    unavailable_reason: str | None


class ReplenishmentProjection(TypedDict):
    status: Literal["available", "partial", "unavailable"]
    source: Literal["same_input_native_262c9d0"]
    source_snapshots: list[SourceSnapshot]
    persistent_outputs: list[PersistentOutput]


def _signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def _signed_input(value: object, bits: int, name: str) -> int:
    if type(value) is not int or not -(1 << (bits - 1)) <= value < (1 << (bits - 1)):
        raise ValueError(f"{name} must be signed int{bits}")
    return value


def _trunc_zero(value: int, divisor: int) -> int:
    return value // divisor if value >= 0 else -((-value) // divisor)


def same_input_chunk_q(
    maximum_soldiers: int,
    effective_current_soldiers: int,
    prepared_fraction_raw: int,
    native_chunk_can_replenish: bool,
) -> ChunkCalculation:
    """Return the conditional request, including qualified native integer zero.

    Operands are the chunk maximum and prepared cache, not whole-regiment
    capacity, fresh monthly fraction, or the independent persistent predicate.
    """
    maximum = _signed_input(maximum_soldiers, 32, "maximum_soldiers")
    effective = _signed_input(effective_current_soldiers, 32, "effective_current_soldiers")
    prepared = _signed_input(prepared_fraction_raw, 64, "prepared_fraction_raw")
    if type(native_chunk_can_replenish) is not bool:
        raise ValueError("native_chunk_can_replenish must be bool")
    deficit = maximum - effective
    qualified = prepared > 0 and native_chunk_can_replenish and deficit > 0
    result: ChunkCalculation = {
        "same_input_q": 0,
        "effective_deficit": max(deficit, 0),
        "native_core_chunk_qualifies": qualified,
        "wrapped_product": None,
        "selected_scaled_numerator": None,
    }
    if qualified:
        product = _signed(maximum * prepared, 64)
        numerator = min(product, deficit * FRACTION_SCALE)
        result["same_input_q"] = _signed(_trunc_zero(numerator, FRACTION_SCALE), 32)
        result["wrapped_product"] = product
        result["selected_scaled_numerator"] = numerator
    return result


def _record_calculation(record: FullDataRecord) -> ChunkCalculation:
    if record.get("persistent_prepared_replenishment_fraction_scale") != FRACTION_SCALE:
        raise ValueError("prepared replenishment fraction scale must be 100000")
    predicate = record.get("native_chunk_can_replenish")
    if type(predicate) is not bool:
        raise ValueError("native_chunk_can_replenish must be bool")
    return same_input_chunk_q(
        _signed_input(record.get("maximum_soldiers"), 32, "maximum_soldiers"),
        _signed_input(record.get("effective_current_soldiers"), 32, "effective_current_soldiers"),
        _signed_input(record.get("persistent_prepared_replenishment_fraction_raw"), 64,
                      "prepared_fraction_raw"),
        predicate,
    )


def observed_persistent_outputs(
    army_rows: Sequence[Mapping[str, object]],
) -> list[PersistentOutput]:
    """Project normalized observations; repeated identities remain aliases.

    Null slots mean unobserved, unavailable, or differing observations. There
    is no sum across aliases, chunks, or armies. Raw source rows are retained
    separately by the existing army-strength query.
    """
    groups: dict[int, PersistentOutput] = {}
    for army in army_rows:
        snapshots = cast(Sequence[FullDataSnapshot],
                         army.get("regiment_replenishment_records_v1") or [])
        army_id = _signed_input(army["army_id"], 32, "army_id")
        for snapshot in snapshots:
            for record in snapshot["records"]:
                persistent_id = record["persistent_regiment_id"]
                ordinal = record["chunk_index"]
                if persistent_id == -1 or not 0 <= ordinal < CHUNK_COUNT:
                    continue
                group = groups.setdefault(persistent_id, {
                    "persistent_regiment_id": persistent_id,
                    "same_input_q_by_chunk": [None] * CHUNK_COUNT,
                    "effective_deficit_by_chunk": [None] * CHUNK_COUNT,
                    "status_by_chunk": ["unobserved"] * CHUNK_COUNT,
                    "observations_by_chunk": [[] for _ in range(CHUNK_COUNT)],
                    "all_seven_observed": False,
                })
                calculation = None
                status = record["status"]
                reason = record["unavailable_reason"]
                if status == "available":
                    try:
                        calculation = _record_calculation(record)
                    except ValueError as error:
                        status, reason = "unavailable", str(error)
                group["observations_by_chunk"][ordinal].append({
                    "army_id": army_id,
                    "army_regiment_id": snapshot["army_regiment_id"],
                    "record_index": record["record_index"],
                    "status": status,
                    "unavailable_reason": reason,
                    "calculation": calculation,
                })
    for group in groups.values():
        for ordinal, observations in enumerate(group["observations_by_chunk"]):
            if not observations:
                continue
            calculations = [item["calculation"] for item in observations]
            if any(item is None for item in calculations):
                group["status_by_chunk"][ordinal] = "unavailable"
            elif any(item != calculations[0] for item in calculations):
                group["status_by_chunk"][ordinal] = "conflicting_observations"
            else:
                calculation = calculations[0]
                if calculation is None:
                    continue
                group["status_by_chunk"][ordinal] = "available"
                group["same_input_q_by_chunk"][ordinal] = calculation["same_input_q"]
                group["effective_deficit_by_chunk"][ordinal] = calculation["effective_deficit"]
        group["all_seven_observed"] = all(
            status == "available" for status in group["status_by_chunk"]
        )
    return list(groups.values())


def project_observed_replenishment_v1(
    army_rows: Sequence[Mapping[str, object]],
) -> ReplenishmentProjection:
    """Preserve source coverage alongside same-input per-persistent requests."""
    snapshots: list[SourceSnapshot] = []
    for army in army_rows:
        army_id = _signed_input(army["army_id"], 32, "army_id")
        source_rows = cast(Sequence[FullDataSnapshot] | None,
                           army.get("regiment_replenishment_records_v1"))
        if source_rows is None:
            snapshots.append({
                "army_id": army_id, "army_regiment_id": None,
                "status": "unavailable", "native_data_record_count": None,
                "unavailable_reason": "regiment_replenishment_records_v1_not_published",
            })
        else:
            snapshots.extend({
                "army_id": army_id,
                "army_regiment_id": row["army_regiment_id"],
                "status": row["status"],
                "native_data_record_count": row["native_data_record_count"],
                "unavailable_reason": row["unavailable_reason"],
            } for row in source_rows)
    outputs = observed_persistent_outputs(army_rows)
    incomplete = any(row["status"] != "available" for row in snapshots) or any(
        status in {"unavailable", "conflicting_observations"}
        for group in outputs for status in group["status_by_chunk"]
    )
    status: Literal["available", "partial", "unavailable"] = "available"
    if incomplete:
        status = "partial" if any(
            row["status"] in {"available", "partial"} for row in snapshots
        ) else "unavailable"
    return {
        "status": status, "source": "same_input_native_262c9d0",
        "source_snapshots": snapshots, "persistent_outputs": outputs,
    }
