"""Offline, deterministic release-bundle export.

The exporter copies an explicit allowlist from a release-ready run into a new
directory.  It never publishes, uploads, contacts a network service, mutates a
run manifest, or removes source/process material.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import ArtifactError, ManifestError
from .model import SourceRecord, portable_relative_path
from .project import load_document, validate_profile


FORMAT_VERSION = 1
BUNDLE_KIND = "xar_promo_release_bundle"
MANIFEST_NAME = "release-bundle-manifest.json"
ARTIFACT_CATEGORIES = frozenset(
    {"deliverable", "subtitle", "thumbnail", "sidecar", "audit"}
)
PROJECT_CONFIG_CATEGORY = "project-config"


class ExportError(ArtifactError):
    """A release bundle could not be exported without weakening its contract."""


@dataclass(frozen=True)
class ReleaseBundleItem:
    """One caller-selected output in the release allowlist."""

    category: str
    destination: str
    source_kind: str
    artifact_id: str | None = None
    expected_role: str | None = None

    @classmethod
    def artifact(
        cls,
        *,
        category: str,
        destination: str,
        artifact_id: str,
        expected_role: str,
    ) -> "ReleaseBundleItem":
        return cls(category, destination, "artifact", artifact_id, expected_role)

    @classmethod
    def project_config_snapshot(cls, *, destination: str) -> "ReleaseBundleItem":
        return cls(PROJECT_CONFIG_CATEGORY, destination, "project-config-snapshot")


@dataclass(frozen=True)
class ReleaseBundlePolicy:
    """The complete, explicit output allowlist supplied by the caller."""

    items: tuple[ReleaseBundleItem, ...]


@dataclass(frozen=True)
class _PreparedItem:
    policy: ReleaseBundleItem
    source: Path
    bytes: int
    sha256: str
    artifact: SourceRecord | None


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExportError(f"{context} must be a non-empty string")
    return value.strip()


def _relative(value: Any, context: str) -> str:
    try:
        return portable_relative_path(value, context)
    except ManifestError as exc:
        raise ExportError(str(exc)) from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _normalize_policy(policy: ReleaseBundlePolicy) -> tuple[ReleaseBundleItem, ...]:
    if not isinstance(policy, ReleaseBundlePolicy):
        raise ExportError("policy must be a ReleaseBundlePolicy")
    normalized: list[ReleaseBundleItem] = []
    for index, item in enumerate(policy.items):
        if not isinstance(item, ReleaseBundleItem):
            raise ExportError(f"policy.items[{index}] must be a ReleaseBundleItem")
        category = _string(item.category, f"policy.items[{index}].category")
        destination = _relative(item.destination, f"policy.items[{index}].destination")
        if destination.casefold() == MANIFEST_NAME.casefold():
            raise ExportError(f"{MANIFEST_NAME} is reserved for the generated manifest")
        if item.source_kind == "artifact":
            if category not in ARTIFACT_CATEGORIES:
                raise ExportError(f"unsupported artifact category: {category}")
            artifact_id = _string(item.artifact_id, f"policy.items[{index}].artifact_id")
            expected_role = _string(item.expected_role, f"policy.items[{index}].expected_role")
            normalized.append(
                ReleaseBundleItem(
                    category,
                    destination,
                    "artifact",
                    artifact_id,
                    expected_role,
                )
            )
        elif item.source_kind == "project-config-snapshot":
            if category != PROJECT_CONFIG_CATEGORY:
                raise ExportError(
                    "project-config-snapshot source must use category 'project-config'"
                )
            if item.artifact_id is not None or item.expected_role is not None:
                raise ExportError(
                    "project-config-snapshot item cannot declare artifact_id or expected_role"
                )
            normalized.append(
                ReleaseBundleItem(category, destination, "project-config-snapshot")
            )
        else:
            raise ExportError(f"unsupported source_kind: {item.source_kind!r}")

    if not normalized:
        raise ExportError("release policy must contain an explicit allowlist")
    destinations = [item.destination.casefold() for item in normalized]
    if len(destinations) != len(set(destinations)):
        raise ExportError("release policy contains duplicate destination paths")
    artifact_ids = [
        item.artifact_id for item in normalized if item.source_kind == "artifact"
    ]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise ExportError("release policy selects an artifact more than once")
    deliverables = [item for item in normalized if item.category == "deliverable"]
    if len(deliverables) != 1:
        raise ExportError("release policy must select exactly one deliverable")
    if sum(item.category == "thumbnail" for item in normalized) > 1:
        raise ExportError("release policy can select at most one thumbnail")
    if sum(item.category == PROJECT_CONFIG_CATEGORY for item in normalized) > 1:
        raise ExportError("release policy can select at most one project-config snapshot")
    return tuple(sorted(normalized, key=lambda item: item.destination.casefold()))


def _load_release_run(run_manifest_path: Path):
    try:
        loaded = load_document(run_manifest_path, check_files=True)
        validate_profile(loaded, "release")
    except (ArtifactError, ManifestError) as exc:
        raise ExportError(f"run is not release-ready: {exc}") from exc
    if loaded.run is None or loaded.bound_config is None:
        raise ExportError("release export requires a native RunManifest")
    return loaded


def _prepare_items(loaded, policy: tuple[ReleaseBundleItem, ...]) -> list[_PreparedItem]:
    run = loaded.run
    run_root = loaded.path.parent
    artifacts = {artifact.artifact_id: artifact for artifact in run.artifacts}
    latest_signoff = {signoff.artifact_id: signoff for signoff in run.signoffs}
    result: list[_PreparedItem] = []
    for item in policy:
        if item.source_kind == "project-config-snapshot":
            source = (run_root / Path(run.project_config.path)).resolve()
            result.append(
                _PreparedItem(
                    item,
                    source,
                    run.project_config.bytes,
                    run.project_config.sha256,
                    None,
                )
            )
            continue
        artifact = artifacts.get(item.artifact_id)
        if artifact is None:
            raise ExportError(f"allowlisted artifact was not found: {item.artifact_id}")
        if artifact.role != item.expected_role:
            raise ExportError(
                f"artifact {artifact.artifact_id!r} has role {artifact.role!r}, "
                f"not caller-required role {item.expected_role!r}"
            )
        if item.category == "deliverable":
            if artifact.role != "deliverable":
                raise ExportError("selected deliverable must have role='deliverable'")
            signoff = latest_signoff.get(artifact.artifact_id)
            if signoff is None or signoff.decision != "approved":
                raise ExportError(
                    f"selected deliverable {artifact.artifact_id!r} is not explicitly approved"
                )
        source = (run_root / Path(artifact.path)).resolve()
        result.append(
            _PreparedItem(item, source, artifact.bytes, artifact.sha256, artifact)
        )
    return result


def _output_row(item: _PreparedItem) -> dict[str, Any]:
    source: dict[str, Any]
    if item.artifact is None:
        source = {
            "kind": "project-config-snapshot",
            "bytes": item.bytes,
            "sha256": item.sha256,
        }
    else:
        source = {
            "kind": "run-artifact",
            "artifact_id": item.artifact.artifact_id,
            "role": item.artifact.role,
            "bytes": item.artifact.bytes,
            "sha256": item.artifact.sha256,
        }
    return {
        "category": item.policy.category,
        "path": item.policy.destination,
        "bytes": item.bytes,
        "sha256": item.sha256,
        "source": source,
    }


def export_release_bundle(
    run_manifest_path: Path,
    destination: Path,
    *,
    policy: ReleaseBundlePolicy,
) -> dict[str, Any]:
    """Export a release-ready run to one new, offline allowlisted directory."""

    run_path = run_manifest_path.expanduser().resolve()
    target = destination.expanduser().resolve()
    if target.exists():
        raise ExportError(f"refusing to overwrite existing release bundle: {target}")
    normalized_policy = _normalize_policy(policy)
    loaded = _load_release_run(run_path)
    prepared = _prepare_items(loaded, normalized_policy)

    # Recheck selected inputs immediately before copying.  Loading the run
    # already checked every preserved artifact and the bound config snapshot.
    for item in prepared:
        if not item.source.is_file():
            raise ExportError(f"allowlisted source was not found: {item.source}")
        if item.source.stat().st_size != item.bytes or _sha256_file(item.source) != item.sha256:
            raise ExportError(f"allowlisted source has hash drift: {item.source}")

    manifest = {
        "format_version": FORMAT_VERSION,
        "kind": BUNDLE_KIND,
        "source_run": {
            "run_id": loaded.run.run_id,
            "bytes": run_path.stat().st_size,
            "sha256": _sha256_file(run_path),
            "project_config_sha256": loaded.run.project_config.sha256,
        },
        "operations": {
            "network_used": False,
            "publish_performed": False,
            "source_material_mutated": False,
        },
        "files": [_output_row(item) for item in prepared],
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=target.parent, prefix=f".{target.name}.partial-"
    ) as temporary:
        staging = Path(temporary)
        for item in prepared:
            output = staging / Path(item.policy.destination)
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item.source, output)
            if output.stat().st_size != item.bytes or _sha256_file(output) != item.sha256:
                raise ExportError(f"copied release artifact failed verification: {output}")
        manifest_path = staging / MANIFEST_NAME
        with manifest_path.open("xb") as handle:
            handle.write(_json_bytes(manifest))
        verify_release_bundle(staging)
        try:
            staging.rename(target)
        except FileExistsError as exc:
            raise ExportError(f"refusing to overwrite existing release bundle: {target}") from exc
        except OSError as exc:
            raise ExportError(f"could not publish local release bundle directory: {exc}") from exc
    return manifest


def verify_release_bundle(directory: Path) -> dict[str, Any]:
    """Verify a self-contained export manifest and its exact output allowlist."""

    root = directory.expanduser().resolve()
    manifest_path = root / MANIFEST_NAME
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ExportError(f"release bundle manifest was not found: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ExportError(f"release bundle manifest is invalid JSON: {exc}") from exc
    except OSError as exc:
        raise ExportError(f"could not read release bundle manifest: {exc}") from exc
    if not isinstance(raw, dict):
        raise ExportError("release bundle manifest root must be an object")
    if set(raw) != {"format_version", "kind", "source_run", "operations", "files"}:
        raise ExportError("release bundle manifest fields do not match format v1")
    if raw["format_version"] != FORMAT_VERSION or raw["kind"] != BUNDLE_KIND:
        raise ExportError("release bundle manifest must declare format v1")
    operations = raw.get("operations")
    if operations != {
        "network_used": False,
        "publish_performed": False,
        "source_material_mutated": False,
    }:
        raise ExportError("release bundle operations declaration is invalid")
    files = raw.get("files")
    if not isinstance(files, list) or not files:
        raise ExportError("release bundle files must be a non-empty allowlist")
    paths: list[str] = []
    deliverable_count = 0
    for index, value in enumerate(files):
        if not isinstance(value, dict) or set(value) != {
            "category",
            "path",
            "bytes",
            "sha256",
            "source",
        }:
            raise ExportError(f"release bundle files[{index}] has invalid fields")
        category = _string(value["category"], f"files[{index}].category")
        if category not in ARTIFACT_CATEGORIES | {PROJECT_CONFIG_CATEGORY}:
            raise ExportError(f"files[{index}].category is unsupported")
        deliverable_count += category == "deliverable"
        relative = _relative(value["path"], f"files[{index}].path")
        if relative.casefold() == MANIFEST_NAME.casefold():
            raise ExportError("release file collides with the generated manifest")
        size = value["bytes"]
        digest = value["sha256"]
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ExportError(f"files[{index}].bytes must be a non-negative integer")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ExportError(f"files[{index}].sha256 is invalid")
        output = root / Path(relative)
        if not output.is_file():
            raise ExportError(f"release bundle file is missing: {relative}")
        if output.stat().st_size != size or _sha256_file(output) != digest.upper():
            raise ExportError(f"release bundle file has hash drift: {relative}")
        paths.append(relative)
    if deliverable_count != 1:
        raise ExportError("release bundle must contain exactly one deliverable")
    if paths != sorted(paths, key=str.casefold) or len(paths) != len(
        {path.casefold() for path in paths}
    ):
        raise ExportError("release bundle allowlist paths are not unique deterministic order")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    expected = set(paths) | {MANIFEST_NAME}
    if actual != expected:
        extras = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise ExportError(
            f"release bundle differs from its allowlist; extras={extras}; missing={missing}"
        )
    return raw


__all__ = [
    "ExportError",
    "MANIFEST_NAME",
    "ReleaseBundleItem",
    "ReleaseBundlePolicy",
    "export_release_bundle",
    "verify_release_bundle",
]
