"""Actual .4 current all-phase occurrences; future callbacks remain conditional."""
from __future__ import annotations

from copy import deepcopy

FAMILY_KEY = "future_daily_supply_schedule_inputs_v1"
_I32 = ("current_date_raw_i32", "native_day_index_raw_i32", "selected_phase_index_i32")
_U32 = ("subject_army_id_u32", "subject_carmy_id_u32")
_FALSE = (
    "actual_future_callback_observed", "future_bucket_mutations_reconstructed",
    "full_daily_supply_transition_ready", "full_monthly_ready",
)
_KEYS = {
    "schema_version", "source", "stage", "status", "ready", "unavailable_reason",
    "current_date_storage_raw64", "secondary_identity", "phases", *_I32, *_U32, *_FALSE,
}
_PHASE_KEYS = {
    "phase_index_i32", "status", "ready", "unavailable_reason", "capacity_raw_i32",
    "count_raw_i32", "data_pointer_present", "matching_positions", "subject_occurrence_count_i32",
}


def _integer(value: object, bits: int, *, unsigned: bool = False) -> bool:
    lower, upper = (0, 1 << bits) if unsigned else (-(1 << (bits - 1)), 1 << (bits - 1))
    return type(value) is int and lower <= value < upper


def _reason(value: dict[str, object], *, phase: bool = False) -> None:
    status, ready, reason = value["status"], value["ready"], value["unavailable_reason"]
    statuses = {"available", "unavailable"} if phase else {"available", "partial", "unavailable"}
    if status not in statuses or type(ready) is not bool or ready != (status == "available"):
        raise ValueError("native future supply schedule readiness is malformed")
    if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError("native future supply schedule reason disagrees with readiness")


def normalize_future_daily_supply_schedule_inputs_v1(
    value: object, *, expected_army_id: int | None = None,
    expected_carmy_id: int | None = None,
) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError("native future supply schedule schema is malformed")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("native future supply schedule version is malformed")
    if value["source"] != "native_future_daily_supply_schedule_inputs_12004" or (
        value["stage"] != "observed_current_all_phase_schedule"
    ) or value["secondary_identity"] != "game_data_plus_2a548":
        raise ValueError("native future supply schedule source is malformed")
    if any(value[key] is not False for key in _FALSE):
        raise ValueError("current supply buckets cannot claim future callback or stage execution")
    _reason(value)
    for key in _I32:
        if value[key] is not None and not _integer(value[key], 32):
            raise ValueError(f"native future supply schedule {key} must be signed32 or null")
    for key in _U32:
        if value[key] is not None and not _integer(value[key], 32, unsigned=True):
            raise ValueError(f"native future supply schedule {key} must be full uint32 or null")
    date = value["current_date_storage_raw64"]
    if date is not None and not _integer(date, 64):
        raise ValueError("native future supply schedule date must be signed64 or null")
    for key, expected in (("subject_army_id_u32", expected_army_id),
                          ("subject_carmy_id_u32", expected_carmy_id)):
        if expected is not None and value[key] is not None and value[key] != (expected & 0xFFFFFFFF):
            raise ValueError("native future supply schedule subject differs from same-query row")
    phases = value["phases"]
    if not isinstance(phases, list) or len(phases) not in {0, 30}:
        raise ValueError("native future supply schedule must retain all30 phases or unavailable pre-capture")
    for index, phase in enumerate(phases):
        if not isinstance(phase, dict) or set(phase) != _PHASE_KEYS or (
            type(phase["phase_index_i32"]) is not int or phase["phase_index_i32"] != index
        ):
            raise ValueError("native future supply schedule phase order is malformed")
        _reason(phase, phase=True)
        for key in ("capacity_raw_i32", "count_raw_i32", "subject_occurrence_count_i32"):
            if phase[key] is not None and not _integer(phase[key], 32):
                raise ValueError(f"native future supply schedule phase {key} must be signed32 or null")
        present, positions = phase["data_pointer_present"], phase["matching_positions"]
        if present is not None and type(present) is not bool:
            raise ValueError("native future supply schedule data presence is malformed")
        if positions is not None and (
            not isinstance(positions, list) or any(not _integer(position, 32) or position < 0
                                                  for position in positions)
        ):
            raise ValueError("native future supply schedule positions must be original int32 indices")
        if phase["ready"]:
            count = phase["count_raw_i32"]
            if count is None or count < 0 or present is None or (count > 0 and not present) or positions is None:
                raise ValueError("native ready future supply schedule phase operands are incomplete")
            if phase["subject_occurrence_count_i32"] != len(positions) or (
                any(position >= count for position in positions)
                or any(left >= right for left, right in zip(positions, positions[1:]))
            ):
                raise ValueError("native future supply schedule must retain each original matching slot in order")
    if value["status"] != "unavailable":
        if len(phases) != 30 or any(value[key] is None for key in (*_I32, *_U32)) or date is None:
            raise ValueError("captured future supply schedule operands are incomplete")
        if value["selected_phase_index_i32"] != (value["native_day_index_raw_i32"] & 0xFFFFFFFF) % 30:
            raise ValueError("future supply schedule selects unsigned stored day modulo30")
        if value["ready"] != all(phase["ready"] for phase in phases):
            raise ValueError("future supply schedule all-phase readiness is malformed")
    elif phases:
        raise ValueError("unavailable pre-capture future supply schedule cannot contain phase rows")
    return deepcopy(value)
