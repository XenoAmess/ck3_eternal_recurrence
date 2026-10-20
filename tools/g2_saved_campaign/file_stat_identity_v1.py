"""One typed boundary for OS stat identities; no path lookup or unit guessing."""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Final, Literal, TypedDict

StatIdentitySchema = Literal["xar.file-stat-identity.os-ns-decimal.v1"]
SCHEMA: Final[StatIdentitySchema] = "xar.file-stat-identity.os-ns-decimal.v1"


class FileStatIdentityWireV1(TypedDict):
    bytes: int
    file_id: str
    mtime_ns: str


def _integer(value: object, *, unsigned: bool) -> int:
    if type(value) is not int or (unsigned and value < 0):
        raise ValueError("an exact OS integer is required")
    return value


def _decimal(value: object, *, unsigned: bool) -> str:
    pattern = r"(?:0|[1-9][0-9]*)" if unsigned else r"(?:0|-?[1-9][0-9]*)"
    if type(value) is not str or len(value) > 64 or re.fullmatch(pattern, value) is None:
        raise ValueError("canonical decimal text required; no hex or unit conversion")
    return value


@dataclass(frozen=True)
class FileStatIdentityV1:
    bytes: int
    file_id: str
    mtime_ns: str

    def __post_init__(self) -> None:
        _integer(self.bytes, unsigned=True)
        _decimal(self.file_id, unsigned=True)
        _decimal(self.mtime_ns, unsigned=False)

    def to_wire(self) -> FileStatIdentityWireV1:
        return {"bytes": self.bytes, "file_id": self.file_id, "mtime_ns": self.mtime_ns}


def normalize_file_stat_identity_v1(value: os.stat_result) -> FileStatIdentityV1:
    """Convert OS inode and Unix-epoch nanoseconds once, without assuming ID width."""
    if type(value) is not os.stat_result:
        raise ValueError("os.stat_result required; custody FILE_ID_INFO is a different contract")
    size = _integer(value.st_size, unsigned=True)
    inode = _integer(value.st_ino, unsigned=True)
    mtime = _integer(value.st_mtime_ns, unsigned=False)
    return FileStatIdentityV1(size, str(inode), str(mtime))


def parse_file_stat_identity_v1(
    value: object, *, schema: StatIdentitySchema
) -> FileStatIdentityV1:
    """Require the caller's explicit schema; never infer units from a number."""
    if type(schema) is not str or schema != SCHEMA:
        raise ValueError("explicit OS stat/ns-decimal schema required")
    if type(value) is not dict or set(value) != {"bytes", "file_id", "mtime_ns"}:
        raise ValueError("exact stat identity fields required")
    size: object = value["bytes"]
    inode: object = value["file_id"]
    mtime: object = value["mtime_ns"]
    return FileStatIdentityV1(
        _integer(size, unsigned=True), _decimal(inode, unsigned=True),
        _decimal(mtime, unsigned=False),
    )
