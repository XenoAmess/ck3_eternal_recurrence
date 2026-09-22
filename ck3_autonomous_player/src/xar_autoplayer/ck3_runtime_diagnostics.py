"""Bounded read-only CK3 engine diagnostics for one configured profile."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

from .environment import sha256_file


ENGINE_DIAGNOSTICS_SCHEMA_V1 = "xar.ck3.engine-diagnostics/v1"
LOG_NAMES = (
    "error.log",
    "debug.log",
    "game.log",
    "system.log",
    "gui_warnings.log",
)
FINGERPRINT_LOG_NAMES = frozenset(
    {"error.log", "game.log", "gui_warnings.log"}
)
MAX_LOG_BYTES = 64 * 1024 * 1024
MAX_CRASH_TEXT_BYTES = 2 * 1024 * 1024
MAX_CRASH_PACKAGES = 32
MAX_FINGERPRINTS = 100
MAX_TAIL_LINES = 100
MAX_MILESTONES = 40
MAX_LINE_CHARS = 2_000
_ENGINE_LEVEL = re.compile(r"^\[[^\]]+\]\[([EFW])\]")
_CRASH_PACKAGE = re.compile(r"ck3_[0-9]{8}_[0-9]{6}\Z")
_MILESTONE_TERMS = (
    "initializing game",
    "game initialization",
    "main menu",
    "checksum",
    "loading map",
    "loaded map",
    "startup",
)
_SELECTED_META = frozenset(
    {
        "AppName",
        "AppVersion",
        "DateTime",
        "BuildType",
        "Platform",
        "Store",
        "Architecture",
        "OperatingSystem",
        "SystemLanguage",
        "SystemMemory",
        "GPUName",
        "GPUVendor",
        "GPUDedicatedMemory",
        "LaunchArguments",
    }
)


class Ck3DiagnosticsError(RuntimeError):
    """Configured engine diagnostics cannot be read within the fixed bounds."""


def _bounded_line(line: str) -> str:
    return line if len(line) <= MAX_LINE_CHARS else line[:MAX_LINE_CHARS] + "…"


def _engine_level(line: str) -> str | None:
    match = _ENGINE_LEVEL.match(line)
    return match.group(1) if match else None


def _fingerprint(line: str) -> str:
    value = re.sub(r"^\[[^\]]+\]\[[EFW]\]\s*", "", line, count=1)
    value = re.sub(r"0x[0-9A-Fa-f]+", "<hex>", value)
    value = re.sub(
        r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27,}\b",
        "<uuid>",
        value,
    )
    value = re.sub(r"\b\d+\b", "<n>", value)
    return _bounded_line(value)


def _read_bounded_text(path: Path, *, byte_limit: int, label: str) -> str:
    size = path.stat().st_size
    if size > byte_limit:
        raise Ck3DiagnosticsError(
            f"refusing to read oversized {label}: {size} > {byte_limit} bytes"
        )
    return path.read_text(encoding="utf-8", errors="replace")


class Ck3RuntimeDiagnosticsInspector:
    """Inspect fixed CK3 log/crash locations below a bootstrap-bound profile."""

    def __init__(self, profile_dir: str | Path) -> None:
        self.profile_dir = Path(profile_dir).resolve()

    def _assert_below_profile(self, path: Path) -> None:
        if not path.resolve().is_relative_to(self.profile_dir):
            raise Ck3DiagnosticsError("diagnostic artifact escapes configured profile")
        if path.is_symlink():
            raise Ck3DiagnosticsError("diagnostic artifact cannot be a symbolic link")

    def _log_record(
        self,
        path: Path,
        *,
        fingerprint_limit: int,
        tail_limit: int,
    ) -> dict[str, object]:
        if not path.is_file():
            return {"exists": False}
        self._assert_below_profile(path)
        text = _read_bounded_text(path, byte_limit=MAX_LOG_BYTES, label="CK3 log")
        lines = text.splitlines()
        nonempty = [line for line in lines if line.strip()]
        severity = {
            "fatal": sum(_engine_level(line) == "F" for line in lines),
            "error": sum(_engine_level(line) == "E" for line in lines),
            "warning": sum(_engine_level(line) == "W" for line in lines),
        }
        record: dict[str, object] = {
            "exists": True,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "line_count": len(lines),
            "nonempty_line_count": len(nonempty),
            "engine_severity_records": severity,
            "severity_count_semantics": "log records, not independent bugs",
            "milestones": [
                _bounded_line(line)
                for line in nonempty
                if any(term in line.casefold() for term in _MILESTONE_TERMS)
            ][-MAX_MILESTONES:],
            "tail": [_bounded_line(line) for line in nonempty[-tail_limit:]],
        }
        if path.name in FINGERPRINT_LOG_NAMES:
            counter: Counter[str] = Counter()
            samples: dict[str, str] = {}
            for line in nonempty:
                if _engine_level(line) is None:
                    continue
                fingerprint = _fingerprint(line)
                counter[fingerprint] += 1
                samples.setdefault(fingerprint, _bounded_line(line))
            ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
            record.update(
                {
                    "unique_fingerprint_count": len(ordered),
                    "fingerprints": [
                        {
                            "occurrences": count,
                            "fingerprint": fingerprint,
                            "sample": samples[fingerprint],
                        }
                        for fingerprint, count in ordered[:fingerprint_limit]
                    ],
                    "fingerprints_truncated": len(ordered) > fingerprint_limit,
                    "fingerprint_count_semantics": (
                        "normalized message groups, not confirmed independent bugs"
                    ),
                }
            )
        return record

    def _crash_record(self, package: Path) -> dict[str, object]:
        self._assert_below_profile(package)
        exception_path = package / "exception.txt"
        meta_path = package / "meta.yml"
        exception_text = (
            _read_bounded_text(
                exception_path,
                byte_limit=MAX_CRASH_TEXT_BYTES,
                label="crash exception text",
            )
            if exception_path.is_file()
            else ""
        )
        exception_lines = [
            line.strip() for line in exception_text.splitlines() if line.strip()
        ]
        headline = next(
            (
                _bounded_line(line)
                for line in exception_lines
                if line.startswith("Unhandled Exception")
            ),
            None,
        )
        stack_start = next(
            (
                index
                for index, line in enumerate(exception_lines)
                if line == "Stack Trace:"
            ),
            None,
        )
        stack_trace = (
            [
                _bounded_line(line)
                for line in exception_lines[stack_start + 1 : stack_start + 33]
            ]
            if stack_start is not None
            else []
        )
        meta: dict[str, str] = {}
        mods: list[str] = []
        if meta_path.is_file():
            meta_text = _read_bounded_text(
                meta_path,
                byte_limit=MAX_CRASH_TEXT_BYTES,
                label="crash metadata",
            )
            for line in meta_text.splitlines():
                match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line.strip())
                if not match:
                    continue
                key, raw_value = match.groups()
                value = _bounded_line(raw_value.strip().strip('"'))
                if key in _SELECTED_META:
                    meta[key] = value
                elif key.startswith("Mod_") and len(mods) < 256:
                    mods.append(value)
        tracked_files: dict[str, dict[str, object]] = {}
        for relative in (
            "exception.txt",
            "meta.yml",
            "minidump.dmp",
            "logs/error.log",
            "logs/debug.log",
            "logs/game.log",
        ):
            path = package / Path(relative)
            if path.is_file():
                self._assert_below_profile(path)
            tracked_files[relative] = {
                "exists": path.is_file(),
                "bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": sha256_file(path) if path.is_file() else None,
            }
        return {
            "package": package.name,
            "exception": {"headline": headline, "stack_trace": stack_trace},
            "meta": meta,
            "mods": mods,
            "files": tracked_files,
        }

    def query_engine_diagnostics_v1(
        self,
        *,
        fingerprint_limit: int = 50,
        tail_limit: int = 25,
    ) -> dict[str, object]:
        if not 1 <= fingerprint_limit <= MAX_FINGERPRINTS:
            raise ValueError(
                f"fingerprint_limit must be from 1 to {MAX_FINGERPRINTS}"
            )
        if not 1 <= tail_limit <= MAX_TAIL_LINES:
            raise ValueError(f"tail_limit must be from 1 to {MAX_TAIL_LINES}")
        log_root = self.profile_dir / "logs"
        logs = {
            name: self._log_record(
                log_root / name,
                fingerprint_limit=fingerprint_limit,
                tail_limit=tail_limit,
            )
            for name in LOG_NAMES
        }
        crash_root = self.profile_dir / "crashes"
        packages: list[Path] = []
        if crash_root.is_dir():
            packages = sorted(
                (
                    path
                    for path in crash_root.iterdir()
                    if path.is_dir() and _CRASH_PACKAGE.fullmatch(path.name)
                ),
                key=lambda item: item.name,
                reverse=True,
            )
        if len(packages) > MAX_CRASH_PACKAGES:
            raise Ck3DiagnosticsError(
                f"refusing to inspect more than {MAX_CRASH_PACKAGES} crash packages"
            )
        crashes = [self._crash_record(package) for package in packages]
        return {
            "schema": ENGINE_DIAGNOSTICS_SCHEMA_V1,
            "profile_dir": str(self.profile_dir),
            "fixed_log_names": list(LOG_NAMES),
            "logs": logs,
            "crashes": {
                "exists": crash_root.is_dir(),
                "package_count": len(crashes),
                "packages": crashes,
            },
            "path_argument_accepted": False,
            "regex_argument_accepted": False,
            "read_only": True,
        }
