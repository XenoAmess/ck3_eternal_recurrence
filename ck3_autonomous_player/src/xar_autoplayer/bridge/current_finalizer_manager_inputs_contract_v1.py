"""Strict same-frame CombatManager pending-sweep leaf.

This leaf observes manager row admission and manager+0x60 only. It does not
observe a later daily-row dispatch, native primary hostility, a finalizer call,
or a future Combat state. An absent parent key and an explicit null retain the
older battle-control wire shape and unavailability respectively.
"""

from __future__ import annotations


CURRENT_FINALIZER_MANAGER_INPUTS_V1_KEY = "current_finalizer_manager_inputs_v1"

_KEYS = {
    "source_combat_id",
    "combat_manager_row_admitted",
    "pending_suppression_sweep_raw",
    "pending_suppression_sweep",
}


def _signed_int32(value: object, field: str) -> int:
    if type(value) is not int or not -(2**31) <= value <= 2**31 - 1:
        raise ValueError(f"{field} must be a signed int32")
    return value


def _strict_bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field} must be a boolean")
    return value


def normalize_current_finalizer_manager_inputs_v1(
    value: object,
    *,
    expected_combat_id: int,
    field: str = "battle_control_snapshot.current_finalizer_manager_inputs_v1",
) -> dict[str, object] | None:
    """Retain genuine zero/false and reject inconsistent raw-to-bool mirrors."""
    expected = _signed_int32(expected_combat_id, "expected_combat_id")
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError(f"{field} has a malformed schema")
    combat_id = _signed_int32(value["source_combat_id"], f"{field}.source_combat_id")
    if combat_id != expected:
        raise ValueError(f"{field}.source_combat_id disagrees with battle frame")
    admitted = _strict_bool(
        value["combat_manager_row_admitted"], f"{field}.combat_manager_row_admitted"
    )
    raw = value["pending_suppression_sweep_raw"]
    if type(raw) is not int or not 0 <= raw <= 255:
        raise ValueError(f"{field}.pending_suppression_sweep_raw must be a uint8")
    pending = _strict_bool(
        value["pending_suppression_sweep"], f"{field}.pending_suppression_sweep"
    )
    if pending is not (raw != 0):
        raise ValueError(f"{field} pending-sweep raw/boolean mirror disagrees")
    return {
        "source_combat_id": combat_id,
        "combat_manager_row_admitted": admitted,
        "pending_suppression_sweep_raw": raw,
        "pending_suppression_sweep": pending,
    }
