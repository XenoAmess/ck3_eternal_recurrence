"""Programmatic command handler for the offline release-bundle exporter.

The public CLI maps arguments directly to :func:`handle_export_command` and
serializes the returned result without duplicating export policy.  Both
validation modes are read-only; only the normal export mode can create the
explicit destination directory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .export import (
    ExportError,
    ReleaseBundleItem,
    ReleaseBundlePolicy,
    _load_release_run,
    _normalize_policy,
    _prepare_items,
    export_release_bundle,
)


POLICY_FORMAT_VERSION = 1
POLICY_KIND = "xar_promo_release_export_policy"


class ExportPolicyError(ExportError):
    """An explicit release-export policy file is malformed or incomplete."""


@dataclass(frozen=True)
class ExportCommandResult:
    """JSON-ready success/failure result; exit codes are always 0 or 2."""

    exit_code: int
    status: str
    mode: str
    run_manifest: str
    destination: str
    policy_file: str
    release_validated: bool
    exported: bool
    selected_files: tuple[Mapping[str, Any], ...]
    manifest: Mapping[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "exit_code": self.exit_code,
            "status": self.status,
            "mode": self.mode,
            "run_manifest": self.run_manifest,
            "destination": self.destination,
            "policy_file": self.policy_file,
            "release_validated": self.release_validated,
            "exported": self.exported,
            "network_used": False,
            "publish_performed": False,
            "selected_files": [dict(row) for row in self.selected_files],
        }
        if self.manifest is not None:
            result["manifest"] = dict(self.manifest)
        if self.error is not None:
            result["error"] = self.error
        return result


def _read_policy_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ExportPolicyError(f"release export policy was not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ExportPolicyError(
            f"invalid release export policy JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ExportPolicyError(f"could not read release export policy {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExportPolicyError("release export policy JSON root must be an object")
    return value


def load_export_policy(path: Path) -> ReleaseBundlePolicy:
    """Parse a strict policy; artifact ids and roles are never inferred."""

    raw = _read_policy_object(path)
    if set(raw) != {"format_version", "kind", "items"}:
        raise ExportPolicyError(
            "release export policy fields must be format_version, kind, and items"
        )
    if raw["format_version"] != POLICY_FORMAT_VERSION or raw["kind"] != POLICY_KIND:
        raise ExportPolicyError(
            "release export policy must declare xar_promo_release_export_policy format v1"
        )
    rows = raw["items"]
    if not isinstance(rows, list):
        raise ExportPolicyError("release export policy items must be an array")
    items: list[ReleaseBundleItem] = []
    for index, value in enumerate(rows):
        if not isinstance(value, dict):
            raise ExportPolicyError(f"policy items[{index}] must be an object")
        source_kind = value.get("source_kind")
        if source_kind == "artifact":
            required = {
                "category",
                "destination",
                "source_kind",
                "artifact_id",
                "expected_role",
            }
            if set(value) != required:
                raise ExportPolicyError(
                    f"artifact policy items[{index}] must explicitly contain "
                    "category, destination, source_kind, artifact_id, and expected_role"
                )
            items.append(
                ReleaseBundleItem.artifact(
                    category=value["category"],
                    destination=value["destination"],
                    artifact_id=value["artifact_id"],
                    expected_role=value["expected_role"],
                )
            )
        elif source_kind == "project-config-snapshot":
            required = {"category", "destination", "source_kind"}
            if set(value) != required:
                raise ExportPolicyError(
                    f"project-config policy items[{index}] must contain only "
                    "category, destination, and source_kind"
                )
            items.append(
                ReleaseBundleItem(
                    value["category"],
                    value["destination"],
                    "project-config-snapshot",
                )
            )
        else:
            raise ExportPolicyError(
                f"policy items[{index}].source_kind must be explicit artifact or "
                "project-config-snapshot"
            )
    try:
        normalized = _normalize_policy(ReleaseBundlePolicy(tuple(items)))
    except ExportError as exc:
        raise ExportPolicyError(str(exc)) from exc
    return ReleaseBundlePolicy(normalized)


def _selected_rows(policy: ReleaseBundlePolicy) -> tuple[Mapping[str, Any], ...]:
    result = []
    for item in policy.items:
        row: dict[str, Any] = {
            "category": item.category,
            "destination": item.destination,
            "source_kind": item.source_kind,
        }
        if item.artifact_id is not None:
            row["artifact_id"] = item.artifact_id
        if item.expected_role is not None:
            row["expected_role"] = item.expected_role
        result.append(row)
    return tuple(result)


def _mode(*, dry_run: bool, validate_only: bool) -> str:
    if validate_only:
        return "validate-only"
    if dry_run:
        return "dry-run"
    return "export"


def handle_export_command(
    run_manifest: Path,
    destination: Path,
    policy_file: Path,
    *,
    dry_run: bool = False,
    validate_only: bool = False,
) -> ExportCommandResult:
    """Validate and optionally export, returning a structured 0/2 result.

    No exception representing a user/input failure crosses this handler.  It
    performs no network or publication action.  ``dry_run`` and
    ``validate_only`` perform the exact release/policy/source preflight without
    creating the destination or its parent.
    """

    try:
        run_path = Path(run_manifest).expanduser().resolve()
        target = Path(destination).expanduser().resolve()
        policy_path = Path(policy_file).expanduser().resolve()
    except (OSError, TypeError, ValueError) as exc:
        return ExportCommandResult(
            2,
            "RED",
            "invalid",
            str(run_manifest),
            str(destination),
            str(policy_file),
            False,
            False,
            (),
            error=f"invalid export command path: {exc}",
        )
    mode = _mode(dry_run=bool(dry_run), validate_only=bool(validate_only))
    if not isinstance(dry_run, bool) or not isinstance(validate_only, bool):
        return ExportCommandResult(
            2,
            "RED",
            mode,
            str(run_path),
            str(target),
            str(policy_path),
            False,
            False,
            (),
            error="dry_run and validate_only must be boolean",
        )
    if dry_run and validate_only:
        return ExportCommandResult(
            2,
            "RED",
            "invalid",
            str(run_path),
            str(target),
            str(policy_path),
            False,
            False,
            (),
            error="dry_run and validate_only are mutually exclusive",
        )

    release_validated = False
    selected: tuple[Mapping[str, Any], ...] = ()
    try:
        policy = load_export_policy(policy_path)
        selected = _selected_rows(policy)
        loaded = _load_release_run(run_path)
        release_validated = True
        _prepare_items(loaded, policy.items)
        if target.exists():
            raise ExportError(f"refusing to overwrite existing release bundle: {target}")
        if dry_run or validate_only:
            return ExportCommandResult(
                0,
                "GREEN",
                mode,
                str(run_path),
                str(target),
                str(policy_path),
                True,
                False,
                selected,
            )
        manifest = export_release_bundle(run_path, target, policy=policy)
        return ExportCommandResult(
            0,
            "GREEN",
            mode,
            str(run_path),
            str(target),
            str(policy_path),
            True,
            True,
            selected,
            manifest=manifest,
        )
    except ExportError as exc:
        return ExportCommandResult(
            2,
            "RED",
            mode,
            str(run_path),
            str(target),
            str(policy_path),
            release_validated,
            False,
            selected,
            error=str(exc),
        )


__all__ = [
    "ExportCommandResult",
    "ExportPolicyError",
    "POLICY_FORMAT_VERSION",
    "POLICY_KIND",
    "handle_export_command",
    "load_export_policy",
]
