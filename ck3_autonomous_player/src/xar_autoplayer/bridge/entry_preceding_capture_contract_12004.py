"""Validate retained preceding-call facts owned by this BattleControl query."""

from __future__ import annotations

from copy import deepcopy


_QUERY_KEYS = {
    "schema", "configured", "installed", "request_filtered", "install_failure_flags",
    "latest_record_sequence", "overwritten_records", "full_entry", "records",
}
_RECORD_KEYS = {
    "record_sequence", "install_epoch", "offline_fixture", "original_returned",
    "identity_stable", "combat_identity", "combat_full_id_before", "combat_full_id_after",
    "caller_return_rva", "caller_return_slot", "original_begin", "original_completion",
    "raw_return_bits", "outer_invocation",
}
_EVENT_KEYS = {"clock_identity", "sequence", "thread_id"}


def _uint(value: object, bits: int, name: str) -> int:
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError(f"{name} must be an unsigned {bits}-bit integer")
    return value


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _event(value: object, name: str) -> None:
    if not isinstance(value, dict) or set(value) != _EVENT_KEYS:
        raise ValueError(f"{name} has an invalid event shape")
    _uint(value["clock_identity"], 64, name + ".clock_identity")
    _uint(value["sequence"], 64, name + ".sequence")
    if value["thread_id"] is not None:
        _uint(value["thread_id"], 32, name + ".thread_id")


def normalize_entry_preceding_capture_12004(
    value: object, *, expected_combat_id: int
) -> dict[str, object] | None:
    """Copy exact raw facts; installation, clocks and RAX imply no full Entry."""
    if value is None:
        return None
    if type(expected_combat_id) is not int or not -(1 << 31) <= expected_combat_id < 1 << 32:
        raise ValueError("expected_combat_id must retain a full DWORD identity")
    expected_full_id = expected_combat_id & 0xFFFFFFFF
    if expected_full_id == 0xFFFFFFFF:
        raise ValueError("expected_combat_id is the invalid sentinel")
    if not isinstance(value, dict) or set(value) != _QUERY_KEYS:
        raise ValueError("entry_preceding_capture_12004 has an invalid query shape")
    if value["schema"] != "xar.ck3.entry-preceding-capture-12004-v1":
        raise ValueError("entry_preceding_capture_12004 has an unknown schema")
    for key in ["configured", "installed", "request_filtered"]:
        _boolean(value[key], "entry_preceding_capture_12004." + key)
    if value["request_filtered"] is not True or value["full_entry"] is not False:
        raise ValueError("preceding capture must be query-filtered raw facts without full Entry")
    _uint(value["install_failure_flags"], 32, "preceding.install_failure_flags")
    latest = _uint(value["latest_record_sequence"], 64, "preceding.latest_record_sequence")
    _uint(value["overwritten_records"], 64, "preceding.overwritten_records")
    records = value["records"]
    if not isinstance(records, list) or len(records) > 128:
        raise ValueError("preceding.records must be a bounded owned journal copy")
    previous = 0
    for record in records:
        if not isinstance(record, dict) or set(record) != _RECORD_KEYS:
            raise ValueError("preceding record has an invalid shape")
        sequence = _uint(record["record_sequence"], 64, "preceding.record_sequence")
        if not previous < sequence <= latest:
            raise ValueError("preceding record ordinal contradicts the copied journal")
        previous = sequence
        _uint(record["install_epoch"], 64, "preceding.install_epoch")
        for key in ["offline_fixture", "original_returned", "identity_stable"]:
            _boolean(record[key], "preceding." + key)
        if record["original_returned"] is not True:
            raise ValueError("preceding journal publication requires the original return")
        for key in ["combat_identity", "caller_return_rva", "caller_return_slot", "raw_return_bits"]:
            _uint(record[key], 64, "preceding." + key)
        if record["combat_identity"] == 0:
            raise ValueError("preceding owned Combat identity is missing")
        before = _uint(record["combat_full_id_before"], 32, "preceding.combat_full_id_before")
        if before != expected_full_id:
            raise ValueError("preceding record is bound to another full Combat identity")
        after = record["combat_full_id_after"]
        if after is not None:
            _uint(after, 32, "preceding.combat_full_id_after")
            if after == 0xFFFFFFFF:
                raise ValueError("preceding after identity must preserve invalid as null")
        if record["identity_stable"] != (after is not None and before == after):
            raise ValueError("preceding identity stability contradicts the copied IDs")
        _event(record["original_begin"], "preceding.original_begin")
        _event(record["original_completion"], "preceding.original_completion")
        if record["outer_invocation"] is not None:
            raise ValueError("preceding call has no observed outer invocation")
    return deepcopy(value)
