"""Conditional26341B0 replay from the existing exact-.3 associated DATA query.

No native writer is executed. Every available query DATA record has chunk+10
equal to its valid ArRg ID, so2657EA0's unassociated cleanup cannot be reached.
This reports physical chunk changes, not future Army soldiers or actual loss.
"""
from __future__ import annotations

from typing import Mapping

SCALE = 100_000
_MASK64 = (1 << 64) - 1


def _signed(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def _div(numerator: int, denominator: int) -> int:
    if denominator == 0:
        raise ArithmeticError("native signed IDIV denominator is zero")
    q = abs(numerator) // abs(denominator)
    result = -q if (numerator < 0) != (denominator < 0) else q
    if not -(1 << 63) <= result < 1 << 63:
        raise ArithmeticError("native signed64 IDIV quotient overflow")
    return result


def _q_div(numerator: int, denominator: int) -> int:
    """2634286..4342 signed64 Q division, including its overflow branches."""
    i64 = lambda x: _signed(x, 64)
    if ((numerator + 0x53E2D6238DA3) & _MASK64) <= 0xA7C5AC471B46:
        return _div(i64(numerator * SCALE), denominator)
    if abs(denominator) >= 10_000_000_000:
        return _div(numerator, _div(denominator, SCALE))
    multiple = i64(_div(numerator, SCALE) * SCALE)
    remainder = i64(numerator - multiple)
    whole = _div(multiple, denominator)
    residual = multiple - whole * denominator
    return i64(i64(_div(i64(remainder * SCALE), denominator) +
                   _div(i64(residual * SCALE), denominator)) +
               i64(whole * SCALE))


def project_observed_writer_chunk_changes(
    army_strength: Mapping[str, object], writer_request: Mapping[str, object],
) -> dict[str, object]:
    """Replay one conditional writer request using the same observed frame.

    Requests for later stages require their own actual stage observations.
    Present DATA cannot stand in for post-supply or post-preferred writes.
    """
    regiment_id = writer_request.get("army_regiment_id")
    result: dict[str, object] = {
        "projection_kind": "conditional_associated_chunk_writeback",
        "source_contract_game_version": "1.20.0.3",
        "army_regiment_id": regiment_id,
        "input_basis": "same_frame_native_DATA_and_explicit_writer_request",
        "status": "unavailable", "chunk_writeback_ready": False,
        "actual_loss": False, "raised_regiment_current_after": None,
        "missing_inputs": [], "writes": [], "physical_chunks_after": [],
    }
    rows = army_strength.get("regiment_strengths", [])
    data_rows = army_strength.get("regiment_replenishment_records_v1", [])
    strength = next((row for row in rows if row.get("army_regiment_id") == regiment_id), None)
    data = next((row for row in data_rows if row.get("army_regiment_id") == regiment_id), None)
    if strength is None or data is None:
        result["missing_inputs"] = ["matching_native_regiment_and_DATA"]
        return result
    skipped = data.get("native_loss_writer_skipped")
    if type(skipped) is not bool:
        result["missing_inputs"] = ["native_loss_writer_skipped"]
        return result
    raw = writer_request.get("writer_quantity_raw")
    if type(raw) is not int or not -(1 << 63) <= raw < 1 << 63:
        raise ValueError("writer_quantity_raw must be signed64 Q100000")
    if writer_request.get("writer_quantity_scale") != SCALE:
        raise ValueError("writer_quantity_scale must be100000")
    if skipped:
        return {**result, "status": "available", "chunk_writeback_ready": True,
                "writer_skipped": True, "refresh_requested": False,
                "remaining_writer_quantity_raw": raw, "physical_current_delta": 0}
    records = data.get("records")
    if data.get("status") != "available" or not isinstance(records, list):
        result["missing_inputs"] = ["complete_available_DATA"]
        return result
    if any(row.get("chunk_army_regiment_id") != regiment_id for row in records):
        result["missing_inputs"] = ["observed_associated_chunk_army_regiment_id"]
        return result
    chunks: dict[tuple[int, int], dict[str, int]] = {}
    order: list[tuple[int, int]] = []
    for row in records:
        key = (row["persistent_regiment_id"], row["chunk_index"])
        values = {"current": row["current_soldiers"], "maximum": row["maximum_soldiers"], "state": row["state_raw"]}
        if any(type(value) is not int for value in values.values()):
            result["missing_inputs"] = ["complete_chunk_current_maximum_state"]
            return result
        if key in chunks and chunks[key] != values:
            raise ValueError("aliased DATA physical chunk inputs differ in the same frame")
        chunks[key] = values
        order.append(key)
    before = sum(chunk["current"] for chunk in chunks.values())
    remaining = raw
    writes: list[dict[str, object]] = []
    parent_current = strength.get("current_soldiers")
    if type(parent_current) is not int:
        result["missing_inputs"] = ["native_ArRg_current_soldiers"]
        return result
    if parent_current != 0:
        for pass_number in (1, 2):
            if pass_number == 2 and remaining < 0:
                break
            for index, key in enumerate(order):
                chunk = chunks[key]
                current = chunk["current"]
                effective = chunk["maximum"] if chunk["state"] == 3 and current == 0 else current
                if pass_number == 1 and effective == 0:
                    continue
                cap = _signed(effective * SCALE, 64)
                if pass_number == 1:
                    selected = cap if cap == 0 else min(_q_div(_signed(effective * raw, 64), cap), cap)
                    selected = min(selected, remaining)
                else:
                    selected = min(cap, remaining)
                new_current = _signed(current - _div(selected, SCALE), 32)
                # All available query records have association non−1, so the
                # setter retains this exact integer even when above maximum.
                chunk["current"] = new_current
                writes.append({"pass": pass_number, "record_index": index,
                               "persistent_regiment_id": key[0], "chunk_index": key[1],
                               "current_before": current, "effective_current": effective,
                               "selected_quantity_raw": selected, "current_after": new_current})
                remaining = _signed(remaining - selected, 64)
                if remaining <= 0:
                    break
    after = [{"persistent_regiment_id": key[0], "chunk_index": key[1],
              "current_soldiers": chunk["current"], "maximum_soldiers": chunk["maximum"]}
             for key, chunk in chunks.items()]
    return {**result, "status": "available", "chunk_writeback_ready": True,
            "writer_skipped": False, "refresh_requested": True,
            "writes": writes, "physical_chunks_after": after,
            "remaining_writer_quantity_raw": remaining,
            "physical_current_delta": sum(chunk["current"] for chunk in chunks.values()) - before}
