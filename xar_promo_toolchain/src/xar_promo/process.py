"""Auditable, shell-free execution of external media programs.

Callers construct an immutable argv, choose an audit directory, and name any
partial artifacts that an interrupted program may leave behind. Every attempt
writes the command and captured standard streams. Failed attempts never remove
or rename partial artifacts, so later audits can inspect the exact bytes left by
the external program.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .errors import PromoToolchainError


class ProcessError(PromoToolchainError):
    """An external process attempt could not be completed successfully."""


class AuditCollisionError(ProcessError):
    """The requested audit directory already contains an execution record."""


@dataclass(frozen=True)
class CommandSpec:
    """A deterministic external command invocation."""

    argv: tuple[str, ...]
    label: str
    cwd: Path | None = None
    partial_artifacts: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        if not self.argv or not self.argv[0]:
            raise ValueError("command argv must contain a non-empty executable")
        if not self.label.strip():
            raise ValueError("command label must be non-empty")
        for argument in self.argv:
            if not isinstance(argument, str) or "\x00" in argument:
                raise ValueError("command arguments must be NUL-free strings")

    @classmethod
    def create(
        cls,
        argv: Sequence[str | os.PathLike[str]],
        *,
        label: str,
        cwd: Path | None = None,
        partial_artifacts: Sequence[Path] = (),
    ) -> "CommandSpec":
        return cls(
            tuple(command_token(value) for value in argv),
            label,
            None if cwd is None else Path(cwd),
            tuple(Path(value) for value in partial_artifacts),
        )


@dataclass(frozen=True)
class PartialArtifactSnapshot:
    path: Path
    exists: bool
    bytes: int | None

    def to_dict(self) -> dict[str, object]:
        return {"path": str(self.path), "exists": self.exists, "bytes": self.bytes}


@dataclass(frozen=True)
class CommandResult:
    spec: CommandSpec
    returncode: int | None
    stdout: str
    stderr: str
    status: str
    audit_directory: Path
    partial_artifacts: tuple[PartialArtifactSnapshot, ...]

    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded" and self.returncode == 0


class CommandFailedError(ProcessError):
    """A process started but returned a non-zero exit code."""

    def __init__(self, result: CommandResult):
        self.result = result
        super().__init__(
            f"{result.spec.label} failed with exit code {result.returncode}; "
            f"audit retained at {result.audit_directory}"
        )


class CommandStartError(ProcessError):
    """The process could not be started."""

    def __init__(self, result: CommandResult):
        self.result = result
        super().__init__(
            f"{result.spec.label} could not start; audit retained at "
            f"{result.audit_directory}: {result.stderr}"
        )


RunFunction = Callable[..., subprocess.CompletedProcess[str]]


def command_token(value: str | os.PathLike[str]) -> str:
    """Preserve string argv verbatim and serialize ``Path`` with ``/``.

    Forward-slash ``Path`` serialization is accepted by Windows media tools and
    keeps command plans and recorded sidecars stable across operating systems.
    """

    if isinstance(value, str):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    token = os.fspath(value)
    if not isinstance(token, str):
        raise ValueError("command path-like arguments must resolve to text")
    return token


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_new(path: Path, payload: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise AuditCollisionError(
            f"refusing to overwrite existing process audit material: {path}"
        ) from exc


def _snapshot(path: Path, cwd: Path | None) -> PartialArtifactSnapshot:
    effective = path if path.is_absolute() or cwd is None else cwd / path
    try:
        stat = effective.stat()
    except (FileNotFoundError, OSError):
        return PartialArtifactSnapshot(effective, False, None)
    is_file = effective.is_file()
    return PartialArtifactSnapshot(effective, is_file, stat.st_size if is_file else None)


def _write_result(result: CommandResult) -> None:
    _write_new(result.audit_directory / "stdout.txt", result.stdout.encode("utf-8"))
    _write_new(result.audit_directory / "stderr.txt", result.stderr.encode("utf-8"))
    _write_new(
        result.audit_directory / "result.json",
        _json_bytes(
            {
                "schema_version": 1,
                "status": result.status,
                "returncode": result.returncode,
                "stdout": "stdout.txt",
                "stderr": "stderr.txt",
                "partial_artifacts": [
                    item.to_dict() for item in result.partial_artifacts
                ],
            }
        ),
    )


def run_command(
    spec: CommandSpec,
    *,
    audit_directory: Path,
    environment: Mapping[str, str] | None = None,
    run: RunFunction | None = None,
) -> CommandResult:
    """Execute ``spec`` with ``shell=False`` and retain a complete audit.

    ``audit_directory`` may be an empty/prepared directory, but an existing
    ``command.json`` is an immutable-attempt collision. The environment is not
    serialized because it can contain credentials.
    """

    audit_directory = Path(audit_directory)
    audit_directory.mkdir(parents=True, exist_ok=True)
    _write_new(
        audit_directory / "command.json",
        _json_bytes(
            {
                "schema_version": 1,
                "label": spec.label,
                "argv": list(spec.argv),
                "cwd": None if spec.cwd is None else str(spec.cwd),
                "shell": False,
                "partial_artifacts": [str(path) for path in spec.partial_artifacts],
            }
        ),
    )

    runner = subprocess.run if run is None else run
    try:
        completed = runner(
            list(spec.argv),
            cwd=None if spec.cwd is None else os.fspath(spec.cwd),
            env=None if environment is None else dict(environment),
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        result = CommandResult(
            spec,
            None,
            "",
            f"{type(exc).__name__}: {exc}",
            "start_failed",
            audit_directory,
            tuple(_snapshot(path, spec.cwd) for path in spec.partial_artifacts),
        )
        _write_result(result)
        raise CommandStartError(result) from exc

    result = CommandResult(
        spec,
        int(completed.returncode),
        completed.stdout or "",
        completed.stderr or "",
        "succeeded" if completed.returncode == 0 else "failed",
        audit_directory,
        tuple(_snapshot(path, spec.cwd) for path in spec.partial_artifacts),
    )
    _write_result(result)
    if not result.succeeded:
        raise CommandFailedError(result)
    return result


__all__ = [
    "AuditCollisionError",
    "CommandFailedError",
    "CommandResult",
    "CommandSpec",
    "CommandStartError",
    "PartialArtifactSnapshot",
    "ProcessError",
    "command_token",
    "run_command",
]
