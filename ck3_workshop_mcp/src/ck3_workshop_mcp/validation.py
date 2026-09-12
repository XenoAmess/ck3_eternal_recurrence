"""Local publication gates for descriptors and deterministic staging manifests."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import GateError
from .models import CK3_CONSUMER_APP_ID, OperationKind, PublicationPlan, sha256_file

_REMOTE_ID_RE = re.compile(r'^\s*remote_file_id\s*=\s*"?([0-9]+)"?\s*$', re.MULTILINE)


def _read_descriptor(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise GateError("BLOCKED_STAGING_MISMATCH", f"cannot read descriptor {path}: {error}") from error


def descriptor_remote_id(path: Path) -> str | None:
    match = _REMOTE_ID_RE.search(_read_descriptor(path))
    return match.group(1) if match else None


def validate_local_plan(plan: PublicationPlan) -> dict[str, Any]:
    """Validate all byte-bound local inputs without invoking a provider."""

    if plan.consumer_app_id != CK3_CONSUMER_APP_ID:
        raise GateError(
            "BLOCKED_APP_ID_MISMATCH",
            f"CK3 publication requires consumer_app_id {CK3_CONSUMER_APP_ID}",
        )

    paths = plan.resolved_paths()
    forbidden_item_ids = plan.effective_forbidden_item_ids
    staging = paths["staging_dir"]
    manifest_path = paths["staging_manifest"]
    outer = paths["outer_descriptor"]
    description = paths["description_path"]
    preview = paths["preview_path"]

    if not staging.is_dir():
        raise GateError("BLOCKED_STAGING_MISMATCH", f"staging directory does not exist: {staging}")
    if not manifest_path.is_file():
        raise GateError("BLOCKED_STAGING_MISMATCH", f"manifest does not exist: {manifest_path}")
    if sha256_file(manifest_path) != plan.staging_manifest_sha256:
        raise GateError("BLOCKED_STAGING_MISMATCH", "staging manifest SHA-256 does not match the plan")
    for path, expected, label in (
        (description, plan.description_sha256, "description"),
        (preview, plan.preview_sha256, "preview"),
    ):
        if not path.is_file() or sha256_file(path) != expected:
            raise GateError("BLOCKED_STAGING_MISMATCH", f"{label} bytes do not match the plan")

    inner = staging / "descriptor.mod"
    if not inner.is_file():
        raise GateError("BLOCKED_STAGING_MISMATCH", "staging has no descriptor.mod")
    inner_id = descriptor_remote_id(inner)
    if inner_id is not None:
        gate = (
            "BLOCKED_FORBIDDEN_UPSTREAM_ID"
            if inner_id in forbidden_item_ids
            else "BLOCKED_DESCRIPTOR_ID_MISMATCH"
        )
        raise GateError(gate, "staging descriptor.mod must not contain remote_file_id")

    if not outer.is_file():
        raise GateError("BLOCKED_DESCRIPTOR_ID_MISMATCH", f"outer descriptor does not exist: {outer}")
    outer_id = descriptor_remote_id(outer)
    if outer_id in forbidden_item_ids:
        raise GateError(
            "BLOCKED_FORBIDDEN_UPSTREAM_ID",
            f"outer descriptor targets forbidden upstream item {outer_id}",
        )
    if plan.target_item_id in forbidden_item_ids:
        raise GateError(
            "BLOCKED_FORBIDDEN_UPSTREAM_ID",
            f"plan targets forbidden upstream item {plan.target_item_id}",
        )
    if plan.operation is OperationKind.CREATE and outer_id is not None:
        raise GateError(
            "BLOCKED_DESCRIPTOR_ID_MISMATCH",
            "create requires an outer descriptor without remote_file_id",
        )
    if plan.operation is OperationKind.UPDATE and outer_id != plan.target_item_id:
        raise GateError(
            "BLOCKED_DESCRIPTOR_ID_MISMATCH",
            f"outer descriptor ID {outer_id!r} differs from plan ID {plan.target_item_id!r}",
        )

    manifest = _load_manifest(manifest_path)
    manifest_item_id = manifest.get("workshop_item_id")
    if manifest_item_id is not None:
        manifest_item_id = str(manifest_item_id)
        if manifest_item_id in forbidden_item_ids:
            raise GateError(
                "BLOCKED_FORBIDDEN_UPSTREAM_ID",
                f"manifest contains forbidden upstream item {manifest_item_id}",
            )
        if plan.operation is OperationKind.CREATE or manifest_item_id != plan.target_item_id:
            raise GateError(
                "BLOCKED_DESCRIPTOR_ID_MISMATCH",
                "manifest workshop_item_id does not agree with publication operation",
            )

    count = _validate_manifest_tree(staging, manifest)
    return {
        "staging_dir": str(staging),
        "manifest": str(manifest_path),
        "manifest_sha256": plan.staging_manifest_sha256,
        "file_count": count,
        "outer_item_id": outer_id,
        "manifest_item_id": manifest_item_id,
    }


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GateError("BLOCKED_STAGING_MISMATCH", f"invalid staging manifest: {error}") from error
    if not isinstance(value, dict) or not isinstance(value.get("files"), list):
        raise GateError("BLOCKED_STAGING_MISMATCH", "manifest must contain a files list")
    return value


def _validate_manifest_tree(staging: Path, manifest: dict[str, Any]) -> int:
    expected: dict[str, tuple[int, str]] = {}
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            raise GateError("BLOCKED_STAGING_MISMATCH", "invalid file entry in staging manifest")
        relative = entry["path"]
        if not isinstance(relative, str) or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
            raise GateError("BLOCKED_STAGING_MISMATCH", f"invalid manifest path: {relative!r}")
        if relative in expected:
            raise GateError("BLOCKED_STAGING_MISMATCH", f"duplicate manifest path: {relative}")
        size, digest = entry["size"], entry["sha256"]
        if not isinstance(size, int) or size < 0 or not isinstance(digest, str):
            raise GateError("BLOCKED_STAGING_MISMATCH", f"invalid manifest metadata: {relative}")
        expected[relative] = (size, digest)

    actual = {
        path.relative_to(staging).as_posix()
        for path in staging.rglob("*")
        if path.is_file()
    }
    if actual != set(expected):
        missing = sorted(set(expected) - actual)
        extra = sorted(actual - set(expected))
        raise GateError(
            "BLOCKED_STAGING_MISMATCH",
            f"staging tree differs from manifest; missing={missing}, extra={extra}",
        )
    for relative, (size, digest) in expected.items():
        path = staging / PurePosixPath(relative)
        if path.stat().st_size != size or sha256_file(path) != digest:
            raise GateError("BLOCKED_STAGING_MISMATCH", f"staging file mismatch: {relative}")
    return len(expected)
