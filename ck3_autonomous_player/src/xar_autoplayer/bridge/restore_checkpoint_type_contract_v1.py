"""Strict JSON identities shared by checkpoint restore consumers."""
from __future__ import annotations

from typing import TypedDict


class CheckpointIdentityV1(TypedDict):
    sha256: str
    size: int
    date_raw: int


class ProcessReplacementIdentityV1(TypedDict):
    previous_pid: int
    pid: int


def checkpoint_identity_v1(value: object) -> CheckpointIdentityV1 | None:
    if not isinstance(value, dict):
        return None
    digest: object = value.get("sha256")
    size: object = value.get("size")
    date_raw: object = value.get("date_raw")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
        or type(size) is not int
        or size <= 0
        or type(date_raw) is not int
    ):
        return None
    return {"sha256": digest, "size": size, "date_raw": date_raw}


def process_replacement_identity_v1(
    value: object,
) -> ProcessReplacementIdentityV1 | None:
    if not isinstance(value, dict):
        return None
    previous_pid: object = value.get("previous_pid")
    pid: object = value.get("pid")
    if (
        type(previous_pid) is not int
        or previous_pid <= 0
        or type(pid) is not int
        or pid <= 0
    ):
        return None
    return {"previous_pid": previous_pid, "pid": pid}


def same_nullable_integer_v1(value: object, expected: object) -> bool:
    """Keep null distinct while rejecting equal bool/float/IntEnum identities."""
    if expected is None:
        return value is None
    return type(value) is int and type(expected) is int and value == expected
