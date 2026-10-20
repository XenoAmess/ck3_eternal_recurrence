"""Typed, side-effect-free inputs for creating a finite Task owner attempt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OwnerRole = Literal["supervisor", "display_owner", "sdk_owner", "feeder", "native_build"]
StageArgs = tuple[str, ...] | list[str]


@dataclass(frozen=True, slots=True)
class OwnerPrepareInputsV1:
    machine_id: str
    role: OwnerRole
    stage_args: tuple[str, ...]
    pythonpath: str | None
    enable_driver_state_wal: bool


def _role(value: object) -> OwnerRole:
    if not isinstance(value, str):
        raise ValueError("exact admitted production role required")
    match value:
        case "supervisor":
            return "supervisor"
        case "display_owner":
            return "display_owner"
        case "sdk_owner":
            return "sdk_owner"
        case "feeder":
            return "feeder"
        case "native_build":
            return "native_build"
        case _:
            raise ValueError("exact admitted production role required")


def validate_owner_prepare_inputs_v1(
    *, machine_id: object, role: object, stage_args: object,
    pythonpath: object, enable_driver_state_wal: object,
) -> OwnerPrepareInputsV1:
    """Validate untrusted values before OS queries or create-only file writes.

    Only JSON-compatible lists and explicit tuples are argv collections. A
    string is one malformed collection, never a sequence of one-character args.
    """
    if not isinstance(machine_id, str) or not machine_id.strip() or "\0" in machine_id:
        raise ValueError("owner machine_id must be a nonempty string")
    owner_role = _role(role)
    if not isinstance(stage_args, (list, tuple)) or len(stage_args) > 128:
        raise ValueError("owner stage_args must be a bounded list or tuple of strings")
    arguments: list[str] = []
    for item in stage_args:
        if not isinstance(item, str) or "\0" in item:
            raise ValueError("owner stage_args must contain only strings without NUL")
        arguments.append(item)
    if pythonpath is not None and (not isinstance(pythonpath, str) or "\0" in pythonpath):
        raise ValueError("owner pythonpath must be a string or None")
    if type(enable_driver_state_wal) is not bool or (
        enable_driver_state_wal and owner_role != "sdk_owner"
    ):
        raise ValueError("WAL opt-in requires a boolean and the sdk_owner role")
    return OwnerPrepareInputsV1(machine_id=machine_id, role=owner_role,
        stage_args=tuple(arguments), pythonpath=pythonpath,
        enable_driver_state_wal=enable_driver_state_wal)
