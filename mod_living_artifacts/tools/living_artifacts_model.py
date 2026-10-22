"""Shared contracts for the living-artifact generators and their consumers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Literal

Language = Literal["simp_chinese", "english"]
Rarity = Literal["common", "masterwork", "famed", "illustrious"]

SCHEMA_VERSION = 2
POSITIVE_SLOTS = 6
CURSE_SLOTS = 2
MAX_RANK = 3
MONTHLY_XP = 8
LIVING_NAME_PREFIX = "★"
FEEDING_XP: dict[Rarity, int] = {
    "common": 80, "masterwork": 200, "famed": 500, "illustrious": 1200,
}
CORE_CHECKPOINT_LIMIT = 3 + len(FEEDING_XP)
AFFIX_IDS = tuple(range(1, 13))
CURSE_IDS = tuple(range(1, 9))
PERSONAL_TYPES = (
    "helmet", "regalia", "armor", "primary_armament", "brooch", "miscellaneous", "journal",
)


def relative_path(value: object) -> str:
    """Reject noncanonical paths before they can reach a file operation."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Expected a canonical relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("Relative path cannot escape its root")
    return value


@dataclass(frozen=True)
class SourcePatch:
    """A reversible edit to a frozen vanilla definition; never edits the game."""

    relative_path: str
    expected_normalized_sha256: str
    replacements: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        relative_path(self.relative_path)
        if re.fullmatch(r"[a-f0-9]{64}", self.expected_normalized_sha256) is None:
            raise ValueError("Source patch requires a fixed normalized SHA-256")
        if not self.replacements:
            raise ValueError("Source patch must change at least one unique anchor")
        for before, after in self.replacements:
            if not before or before == after:
                raise ValueError("Source patch anchors must be nonempty changes")


@dataclass(frozen=True)
class RuntimeInventory:
    schema_version: Literal[1]
    paths: tuple[str, ...]

    @classmethod
    def parse(cls, value: object) -> RuntimeInventory:
        if not isinstance(value, dict) or set(value) != {"schema_version", "paths"}:
            raise ValueError("Runtime inventory fields mismatch")
        version = value["schema_version"]
        paths = value["paths"]
        if type(version) is not int or version != 1 or not isinstance(paths, list):
            raise ValueError("Runtime inventory schema/version mismatch")
        parsed = tuple(relative_path(path) for path in paths)
        if list(parsed) != sorted(set(parsed)) or "descriptor.mod" not in parsed or "thumbnail.png" not in parsed:
            raise ValueError("Runtime inventory must be sorted, unique and include product metadata")
        if len({path.casefold() for path in parsed}) != len(parsed):
            raise ValueError("Runtime inventory contains case collisions")
        return cls(1, parsed)

    def to_json(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "paths": list(self.paths)}
