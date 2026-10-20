"""Pure core of the current A17 runtime admission; no I/O or admission action.

This projection checks fields shared by the publisher and adopter. It does not
replace the adopter's exact refs, current capacity, deadline or output guards.
The original card, including its other metadata, remains the caller's receipt.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from owner_response_contract_v1 import JsonObject, require_json_object_v1
from write_source27_canonical_ref_v1 import FileRef, parse_ref

MAX_SAFE_INTEGER = 2 ** 53 - 1


class ColdRuntimeCapacityCoreV1(TypedDict):
    D_free_floor_bytes: int
    Z_free_floor_bytes: int


class ColdRuntimeAdmissionCoreV1(TypedDict):
    schema: Literal["xar.Source29-A17-runtime-prepare-admission/v1"]
    machine_id: str
    owner: Literal["Root"]
    status: Literal["ADMITTED"]
    root_direct_execution_release: Literal[True]
    plan: FileRef
    quote: FileRef
    full_storage_ref: FileRef
    canonical_capacity_review_passed: Literal[True]
    runtime_hard_bytes: int
    capacity: ColdRuntimeCapacityCoreV1


def _positive_safe_integer(value: object, field: str) -> int:
    if type(value) is not int or not 0 < value <= MAX_SAFE_INTEGER:
        raise ValueError(field + " must be an exact positive safe integer")
    return value


def _reference(row: JsonObject, field: str) -> FileRef:
    try:
        reference = parse_ref(row.get(field))
    except (ValueError, RuntimeError) as error:
        raise ValueError(field + " must be an exact FileRef") from error
    _positive_safe_integer(reference["bytes"], field + ".bytes")
    if not Path(reference["path"]).is_absolute():
        raise ValueError(field + ".path must be absolute")
    return reference


def parse_cold_runtime_admission_core_v1(
    value: object, *, expected_machine_id: str,
) -> ColdRuntimeAdmissionCoreV1:
    """Validate the one current core field contract; never perform admission."""
    if type(expected_machine_id) is not str or not expected_machine_id:
        raise ValueError("expected_machine_id must be nonempty text")
    row = require_json_object_v1(value)
    if row.get("schema") != "xar.Source29-A17-runtime-prepare-admission/v1":
        raise ValueError("current runtime admission schema required")
    if row.get("machine_id") != expected_machine_id:
        raise ValueError("runtime admission machine differs")
    if row.get("owner") != "Root" or row.get("status") != "ADMITTED":
        raise ValueError("runtime admission requires Root and ADMITTED")
    if row.get("root_direct_execution_release") is not True:
        raise ValueError("root_direct_execution_release must be true")
    if row.get("canonical_capacity_review_passed") is not True:
        raise ValueError("canonical_capacity_review_passed must be true")
    if "hard_bytes" in row:
        raise ValueError("legacy hard_bytes is not a runtime_hard_bytes alias")
    capacity = require_json_object_v1(row.get("capacity"))
    if any(key in capacity for key in
           ("D_conservative_floor_bytes", "Z_conservative_floor_bytes")):
        raise ValueError("legacy capacity floor fields are not aliases")
    return {
        "schema": "xar.Source29-A17-runtime-prepare-admission/v1",
        "machine_id": expected_machine_id, "owner": "Root", "status": "ADMITTED",
        "root_direct_execution_release": True,
        "plan": _reference(row, "plan"), "quote": _reference(row, "quote"),
        "full_storage_ref": _reference(row, "full_storage_ref"),
        "canonical_capacity_review_passed": True,
        "runtime_hard_bytes": _positive_safe_integer(
            row.get("runtime_hard_bytes"), "runtime_hard_bytes"),
        "capacity": {
            "D_free_floor_bytes": _positive_safe_integer(
                capacity.get("D_free_floor_bytes"), "capacity.D_free_floor_bytes"),
            "Z_free_floor_bytes": _positive_safe_integer(
                capacity.get("Z_free_floor_bytes"), "capacity.Z_free_floor_bytes"),
        },
    }
