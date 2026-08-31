"""Programmatic command handler for generic human-review package creation.

This module is intentionally a CLI-facing orchestration layer.  It reads an
already generated deliverable, storyboard JSON, and byte-bound ffprobe envelope, then
delegates planning and extraction to :mod:`xar_promo.review`.  It never imports
or invokes a sign-off operation: successful execution only creates a pending
human-review template and a byte-bound review-package manifest.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from .errors import PromoToolchainError
from .media import MediaProbeError, load_bound_media_probe
from .process import CommandResult, CommandSpec, run_command
from .review import (
    PENDING_REVIEW_STATE,
    ReviewFrame,
    ReviewPackagePlan,
    ReviewPlanError,
    execute_review_frame_plan,
    plan_review_package,
    write_review_template,
)


REVIEW_PACKAGE_KIND = "xar-promo-review-package"
REVIEW_PACKAGE_VERSION = 1
REVIEW_TEMPLATE_NAME = "review-template.json"
REVIEW_PACKAGE_NAME = "review-package.json"


class ReviewCommandError(PromoToolchainError):
    """Review command inputs or generated package material are invalid."""


@dataclass(frozen=True)
class ReviewCommandResult:
    """Read-only handler result suitable for CLI text or JSON presentation."""

    plan_only: bool
    state: str
    artifact_summary: Mapping[str, object]
    frames: tuple[ReviewFrame, ...]
    chapter_count: int
    command_results: tuple[CommandResult, ...] = ()
    template_path: Path | None = None
    package_path: Path | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.plan_only, bool):
            raise ReviewCommandError("plan_only must be a boolean")
        if self.plan_only:
            if self.state != "planned" or self.command_results:
                raise ReviewCommandError(
                    "plan-only result must be planned and contain no executions"
                )
            if self.template_path is not None or self.package_path is not None:
                raise ReviewCommandError(
                    "plan-only result must not claim written review material"
                )
        else:
            if self.state != PENDING_REVIEW_STATE:
                raise ReviewCommandError(
                    "executed review result must remain pending human review"
                )
            if self.template_path is None or self.package_path is None:
                raise ReviewCommandError(
                    "executed review result requires package and template paths"
                )
            if len(self.command_results) != len(self.frames):
                raise ReviewCommandError(
                    "executed review result must bind every frame command"
                )
            if any(not result.succeeded for result in self.command_results):
                raise ReviewCommandError(
                    "executed review result cannot contain a failed command"
                )
        if not isinstance(self.chapter_count, int) or self.chapter_count <= 0:
            raise ReviewCommandError("chapter_count must be a positive integer")
        if not self.frames:
            raise ReviewCommandError("review command result requires frame plans")
        if any(not isinstance(frame, ReviewFrame) for frame in self.frames):
            raise ReviewCommandError("frames must contain ReviewFrame values")
        object.__setattr__(
            self,
            "artifact_summary",
            MappingProxyType(dict(self.artifact_summary)),
        )

    def to_dict(self) -> dict[str, object]:
        """Return deterministic JSON-ready output without fabricating approval."""

        value: dict[str, object] = {
            "format_version": 1,
            "kind": "xar-promo-review-command-result",
            "state": self.state,
            "plan_only": self.plan_only,
            "writes_performed": not self.plan_only,
            "is_signoff": False,
            "approval_granted": False,
            "artifact": dict(self.artifact_summary),
            "chapter_count": self.chapter_count,
            "frame_plan": [_frame_plan_row(frame) for frame in self.frames],
        }
        if not self.plan_only:
            value["review_template"] = _required_path(
                self.template_path, "review template"
            ).as_posix()
            value["review_package"] = _required_path(
                self.package_path, "review package"
            ).as_posix()
            value["commands"] = [
                {
                    "label": result.spec.label,
                    "status": result.status,
                    "returncode": result.returncode,
                    "audit_directory": result.audit_directory.as_posix(),
                }
                for result in self.command_results
            ]
        return value


CommandRunner = Callable[..., CommandResult]


def run_review_command(
    *,
    ffmpeg: str | os.PathLike[str],
    deliverable_path: Path,
    storyboard_path: Path,
    probe_path: Path,
    output_directory: Path,
    audit_directory: Path,
    plan_only: bool = False,
    working_directory: Path | None = None,
    command_runner: CommandRunner = run_command,
) -> ReviewCommandResult:
    """Plan or materialize a pending human-review package.

    ``plan_only=True`` reads and validates the three declared inputs and returns
    only the artifact/frame extraction plan.  It performs no mkdir, command, or
    file write.  Execution mode retains the existing review module's exclusive
    outputs and failure materials, then writes a pending template and package
    manifest.  It never records a decision or sign-off.
    """

    if not isinstance(plan_only, bool):
        raise ReviewCommandError("plan_only must be a boolean")
    if not callable(command_runner):
        raise ReviewCommandError("command_runner must be callable")
    cwd = (
        None
        if working_directory is None
        else Path(working_directory).expanduser().resolve()
    )
    deliverable = _effective_path(Path(deliverable_path), cwd)
    storyboard_source = _effective_path(Path(storyboard_path), cwd)
    probe_source = _effective_path(Path(probe_path), cwd)
    output_root = _effective_path(Path(output_directory), cwd)
    audit_root = _effective_path(Path(audit_directory), cwd)

    storyboard = _read_storyboard(storyboard_source)
    probe = _read_probe(probe_source, deliverable)
    plan = plan_review_package(
        ffmpeg=ffmpeg,
        artifact_path=deliverable,
        probe=probe,
        storyboard_timeline=storyboard,
        output_directory=output_root,
        audit_directory=audit_root,
        working_directory=cwd,
    )
    if plan_only:
        return ReviewCommandResult(
            plan_only=True,
            state="planned",
            artifact_summary=plan.artifact_summary,
            frames=plan.frames,
            chapter_count=len(plan.chapters),
        )

    template_path = output_root / REVIEW_TEMPLATE_NAME
    package_path = output_root / REVIEW_PACKAGE_NAME
    _preflight_output(template_path, "review template")
    _preflight_output(package_path, "review package")

    def enforcing_runner(
        spec: CommandSpec, *, audit_directory: Path
    ) -> CommandResult:
        result = command_runner(spec, audit_directory=audit_directory)
        if not isinstance(result, CommandResult):
            raise ReviewCommandError(
                "review command runner must return a CommandResult"
            )
        if result.spec != spec or result.audit_directory != audit_directory:
            raise ReviewCommandError(
                "review command runner returned a result for a different command "
                "or audit directory"
            )
        if not result.succeeded:
            # A conforming run_command raises before this point.  This guard
            # prevents a permissive injected runner from promoting a partial.
            raise ReviewCommandError(
                f"review frame command did not succeed; material retained at "
                f"{result.audit_directory}"
            )
        return result

    # execute_review_frame_plan intentionally performs no cleanup.  Completed
    # frames, a failed frame's partial, and command audit directories therefore
    # remain inspectable if any command raises.
    results = execute_review_frame_plan(plan, command_runner=enforcing_runner)
    write_review_template(template_path, plan)
    package = _review_package_payload(
        plan,
        results,
        template_path=template_path,
        output_root=output_root,
    )
    _write_new_json(package_path, package)
    return ReviewCommandResult(
        plan_only=False,
        state=PENDING_REVIEW_STATE,
        artifact_summary=plan.artifact_summary,
        frames=plan.frames,
        chapter_count=len(plan.chapters),
        command_results=results,
        template_path=template_path,
        package_path=package_path,
    )


def _read_storyboard(
    path: Path,
) -> Mapping[str, Any] | Sequence[Mapping[str, Any]]:
    value = _read_json(path, "storyboard")
    if isinstance(value, Mapping):
        return value
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        if any(not isinstance(row, Mapping) for row in value):
            raise ReviewCommandError("storyboard array entries must be objects")
        return value
    raise ReviewCommandError("storyboard JSON must be an object or chapter array")


def _read_probe(path: Path, deliverable: Path):
    try:
        return load_bound_media_probe(path, media_path=deliverable).probe
    except MediaProbeError as exc:
        raise ReviewCommandError(
            f"invalid ffprobe JSON or unbound ffprobe envelope {path}: {exc}"
        ) from exc


def _read_json(path: Path, label: str) -> object:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ReviewCommandError(f"could not read {label} JSON {path}: {exc}") from exc
    try:
        return json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewCommandError(f"invalid {label} JSON {path}: {exc}") from exc


def _review_package_payload(
    plan: ReviewPackagePlan,
    results: tuple[CommandResult, ...],
    *,
    template_path: Path,
    output_root: Path,
) -> dict[str, object]:
    if len(results) != len(plan.frames):
        raise ReviewCommandError("review package is missing frame command results")
    if any(not result.succeeded for result in results):
        raise ReviewCommandError("review package cannot bind failed frame commands")
    template_record = _file_record(
        template_path,
        relative_to=output_root,
    )
    frame_rows: list[dict[str, object]] = []
    for frame, result in zip(plan.frames, results):
        record = _file_record(frame.final_output, relative_to=output_root)
        frame_rows.append(
            {
                **frame.to_dict(),
                **record,
                "command": {
                    "label": result.spec.label,
                    "status": result.status,
                    "returncode": result.returncode,
                    "audit_directory": result.audit_directory.as_posix(),
                },
            }
        )
    value: dict[str, object] = {
        "format_version": REVIEW_PACKAGE_VERSION,
        "kind": REVIEW_PACKAGE_KIND,
        "state": PENDING_REVIEW_STATE,
        "template_only": True,
        "is_signoff": False,
        "approval_granted": False,
        "artifact": dict(plan.artifact_summary),
        "timeline": {
            "chapters": [chapter.to_dict() for chapter in plan.chapters]
        },
        "review_template": template_record,
        "frames": frame_rows,
    }
    _validate_pending_package(value)
    return value


def _frame_plan_row(frame: ReviewFrame) -> dict[str, object]:
    return {
        **frame.to_dict(),
        "partial_path": frame.partial_output.as_posix(),
        "command": {
            "argv": list(frame.command.spec.argv),
            "cwd": (
                None
                if frame.command.spec.cwd is None
                else frame.command.spec.cwd.as_posix()
            ),
            "audit_directory": frame.command.audit_directory.as_posix(),
        },
    }


def _file_record(path: Path, *, relative_to: Path) -> dict[str, object]:
    target = Path(path)
    if not target.is_file():
        raise ReviewCommandError(f"review package file is missing: {target}")
    try:
        relative = target.relative_to(relative_to).as_posix()
    except ValueError as exc:
        raise ReviewCommandError(
            f"review package file escaped its output directory: {target}"
        ) from exc
    return {
        "path": relative,
        "bytes": target.stat().st_size,
        "sha256": _sha256_file(target),
    }


def _validate_pending_package(value: Mapping[str, object]) -> None:
    if (
        value.get("kind") != REVIEW_PACKAGE_KIND
        or value.get("state") != PENDING_REVIEW_STATE
        or value.get("template_only") is not True
        or value.get("is_signoff") is not False
        or value.get("approval_granted") is not False
    ):
        raise ReviewCommandError(
            "review package must remain pending and cannot grant approval"
        )


def _write_new_json(path: Path, value: Mapping[str, object]) -> None:
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ReviewCommandError(
            f"refusing to overwrite review package: {target}"
        ) from exc


def _preflight_output(path: Path, label: str) -> None:
    if path.exists():
        raise ReviewCommandError(f"refusing to overwrite {label}: {path}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise ReviewCommandError(f"could not hash review file {path}: {exc}") from exc
    return digest.hexdigest().upper()


def _effective_path(path: Path, cwd: Path | None) -> Path:
    return path if path.is_absolute() or cwd is None else cwd / path


def _required_path(value: Path | None, label: str) -> Path:
    if value is None:
        raise ReviewCommandError(f"{label} path is missing")
    return value


__all__ = [
    "REVIEW_PACKAGE_KIND",
    "REVIEW_PACKAGE_NAME",
    "REVIEW_PACKAGE_VERSION",
    "REVIEW_TEMPLATE_NAME",
    "ReviewCommandError",
    "ReviewCommandResult",
    "run_review_command",
]
