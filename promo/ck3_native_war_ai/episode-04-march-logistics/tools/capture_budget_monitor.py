"""Stat-only limits for one explicitly owned camera directory; no media IO."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from collections.abc import Mapping
from typing import Protocol


class BudgetMonitor(Protocol):
    def __call__(self) -> dict[str, object]: ...


class OwnedJob(Protocol):
    def poll(self) -> int | None: ...
    def finish(self, *, receipt: Path, unsafe_marker: Path, timeout: int) -> dict[str, object]: ...
    def abort(self, *, receipt: Path, unsafe_marker: Path) -> dict[str, object]: ...


class CaptureBudgetFailure(RuntimeError):
    def __init__(self, facts: dict[str, object]) -> None:
        self.facts = dict(facts)
        super().__init__(str(facts))


def _raise_walk_error(error: OSError) -> None:
    raise error


@dataclass(frozen=True)
class CaptureByteBudget:
    root: Path
    raw: Path
    raw_soft_stop_bytes: int
    aggregate_soft_stop_bytes: int
    raw_ceiling_bytes: int
    aggregate_ceiling_bytes: int

    def __post_init__(self) -> None:
        for value in (self.raw_soft_stop_bytes, self.aggregate_soft_stop_bytes,
                      self.raw_ceiling_bytes, self.aggregate_ceiling_bytes):
            if type(value) is not int or value <= 0:
                raise ValueError("Positive integer byte limits required")
        if not (self.raw_soft_stop_bytes < self.raw_ceiling_bytes <= self.aggregate_ceiling_bytes
                and self.aggregate_soft_stop_bytes < self.aggregate_ceiling_bytes):
            raise ValueError("Explicit normal-finish headroom required")
        if not self.root.is_absolute() or not self.raw.is_absolute() or self.raw == self.root:
            raise ValueError("Explicit absolute camera root and raw path required")
        if not self.raw.is_relative_to(self.root) or self.root.parent == self.root:
            raise ValueError("Raw must be inside the dedicated camera root")
        if self.root.resolve() != self.root or self.raw.resolve() != self.raw:
            raise ValueError("Canonical paths without aliases required")

    def __call__(self) -> dict[str, object]:
        facts: dict[str, object] = {
            "camera_root": str(self.root), "raw": str(self.raw),
            "raw_soft_stop_bytes": self.raw_soft_stop_bytes,
            "aggregate_soft_stop_bytes": self.aggregate_soft_stop_bytes,
            "raw_ceiling_bytes": self.raw_ceiling_bytes,
            "aggregate_ceiling_bytes": self.aggregate_ceiling_bytes,
        }
        try:
            if not self.root.is_dir() or any(p.is_symlink() or p.is_junction() for p in (self.root, *self.root.parents)):
                raise ValueError("Camera root missing or symlinked")
            aggregate = 0
            raw_bytes = 0
            for directory, subdirs, filenames in os.walk(self.root, followlinks=False, onerror=_raise_walk_error):
                parent = Path(directory)
                if any((parent / name).is_symlink() or (parent / name).is_junction() for name in subdirs):
                    raise ValueError("Camera directory contains a symlink")
                for name in filenames:
                    path = parent / name
                    if path.is_symlink() or not path.is_file():
                        raise ValueError("Camera member is not a regular file")
                    size = path.stat().st_size
                    aggregate += size
                    if path == self.raw:
                        raw_bytes = size
            facts.update(raw_bytes=raw_bytes, aggregate_bytes=aggregate,
                         raw_hard_ceiling_exceeded=raw_bytes > self.raw_ceiling_bytes,
                         aggregate_hard_ceiling_exceeded=aggregate > self.aggregate_ceiling_bytes)
        except (OSError, ValueError) as error:
            facts.update(reason="budget_measurement_unavailable", error=repr(error))
            raise CaptureBudgetFailure(facts) from error
        if raw_bytes >= self.raw_soft_stop_bytes or aggregate >= self.aggregate_soft_stop_bytes:
            facts["reason"] = "raw_soft_stop" if raw_bytes >= self.raw_soft_stop_bytes else "aggregate_soft_stop"
            raise CaptureBudgetFailure(facts)
        facts["reason"] = "below_soft_limits"
        return facts


def from_capacity(root: Path, raw: Path, raw_ceiling: int,
                  capacity: Mapping[str, object]) -> CaptureByteBudget:
    """Bind the optional low-level monitor to an explicit window-take card."""
    value = capacity.get("capture_budget_monitor")
    if not isinstance(value, Mapping):
        raise ValueError("This budgeted take requires capture_budget_monitor capacity facts")
    fields: dict[str, object] = {}
    for key, member in value.items():
        if not isinstance(key, str):
            raise ValueError("Budget field names must be strings")
        fields[key] = member
    if fields.get("camera_root") != str(root) or fields.get("raw_path") != str(raw):
        raise ValueError("Capacity budget belongs to another camera root/raw")

    def byte_count(name: str) -> int:
        number = fields.get(name)
        if type(number) is not int:
            raise ValueError("Integer capacity byte field required: " + name)
        return number

    if byte_count("raw_ceiling_bytes") != raw_ceiling:
        raise ValueError("Raw ceiling differs from the existing admitted raw component")
    return CaptureByteBudget(root, raw, byte_count("raw_soft_stop_bytes"),
        byte_count("aggregate_soft_stop_bytes"), byte_count("raw_ceiling_bytes"),
        byte_count("aggregate_ceiling_bytes"))
