#!/usr/bin/env python3
"""Resolve and materialize bounded Phase-2 product projections.

The Phase-2 source tree intentionally contains more runtime files than CK3 can
reliably parse in one startup while the new domains are being bisected.  This
module gives the isolated runner a deterministic, hash-bound projection
without deleting or mutating the broad development tree.

Projection manifests contain paths relative to a product root.  A manifest may
also contain ``projections`` (a catalog of named path lists), which lets one
catalog drive ``core``, ``workforce`` and other diagnostic groups.  Every
selected file is checked before it is copied; optional ``bytes`` and
``sha256`` fields become mandatory provenance checks when present.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
from typing import Any, Iterable


SCHEMA_VERSION = 1
MANIFEST_KIND = "zg361_phase2_product_projection"
CATALOG_KIND = "zg361_phase2_product_projection_catalog"
DEFAULT_PROJECTION = "broad"
CORE_PROJECTION = "core"
CORE_MANIFEST_NAME = "phase2_product_projection_core.json"

# Keep this in lock-step with run_zhongguo_acceptance's release projection.
SOURCE_ONLY_ROOTS = frozenset(
    {"artifacts", "docs", "fixtures", "images", "promo", "tools", "workshop"}
)
RUNTIME_ROOT_SUFFIXES = {
    "common": frozenset({".txt"}),
    "events": frozenset({".txt"}),
    "gfx": frozenset({".dds"}),
    "gui": frozenset({".gui", ".txt"}),
    "localization": frozenset({".yml"}),
}
ROOT_FILES = frozenset({"descriptor.mod", "thumbnail.png"})
SHA256_LENGTH = 64
FORBIDDEN_RUNTIME_PARTS = frozenset(
    {"acceptance", "fixture", "fixtures", "test", "tests"}
)


class ProductProjectionError(ValueError):
    """A projection manifest or source failed its typed contract."""


@dataclass(frozen=True)
class ProjectionEntry:
    path: str
    bytes: int | None = None
    sha256: str | None = None

    def as_dict(self) -> dict[str, object]:
        value: dict[str, object] = {"path": self.path}
        if self.bytes is not None:
            value["bytes"] = self.bytes
        if self.sha256 is not None:
            value["sha256"] = self.sha256
        return value


@dataclass(frozen=True)
class ProjectionSpec:
    name: str
    source_root: Path
    entries: tuple[ProjectionEntry, ...] = ()
    mode: str = "allowlist"
    manifest_path: Path | None = None
    source_tree_sha256: str | None = None
    # ``source_tree_sha256`` is the bootstrap snapshot digest (a map keyed by
    # path).  Formal launch reports also publish a list-oriented product-tree
    # digest; retain it as independent provenance instead of conflating the
    # two algorithms.
    formal_overlay_tree_sha256: str | None = None
    file_list_sha256: str | None = None
    description: str | None = None

    @property
    def is_broad(self) -> bool:
        return self.mode == "broad"

    def report_identity(self) -> dict[str, object]:
        return {
            "name": self.name,
            "mode": self.mode,
            "source_root": str(self.source_root),
            "manifest_path": (
                str(self.manifest_path) if self.manifest_path is not None else None
            ),
            "source_tree_sha256": self.source_tree_sha256,
            "formal_overlay_tree_sha256": self.formal_overlay_tree_sha256,
            "file_list_sha256": self.file_list_sha256,
            "description": self.description,
            "declared_file_count": len(self.entries) if not self.is_broad else None,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_path(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProductProjectionError(f"{label} path must be a non-empty string")
    # Manifests are portable and must never smuggle a host path or traversal
    # into the destination tree.
    raw = value.replace("\\", "/")
    raw_parts = raw.split("/")
    if "\x00" in raw or any(part in {"", ".", ".."} for part in raw_parts):
        raise ProductProjectionError(f"{label} path contains traversal or empty components: {value!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or raw.startswith("//"):
        raise ProductProjectionError(f"{label} path must be relative: {value!r}")
    normalized = path.as_posix()
    if normalized in {"README.md"} or normalized.split("/", 1)[0] in SOURCE_ONLY_ROOTS:
        raise ProductProjectionError(
            f"{label} path is source-only and cannot be mounted: {normalized}"
        )
    return normalized


def _runtime_path_allowed(relative: str) -> bool:
    path = PurePosixPath(relative)
    if len(path.parts) == 1:
        return relative in ROOT_FILES
    suffixes = RUNTIME_ROOT_SUFFIXES.get(path.parts[0])
    return suffixes is not None and path.suffix.lower() in suffixes


def _is_forbidden_runtime_path(relative: str) -> bool:
    """Reject acceptance/fixture/test payloads from a product projection."""

    for part in PurePosixPath(relative).parts:
        lowered = part.lower()
        stem = PurePosixPath(lowered).stem
        if lowered in FORBIDDEN_RUNTIME_PARTS:
            return True
        if "acceptance" in lowered or "fixture" in lowered:
            return True
        if stem.startswith("test_") or stem.endswith("_test") or "_test_" in stem:
            return True
    return False


def _parse_entry(value: object, *, index: int) -> ProjectionEntry:
    label = f"manifest entry {index}"
    if isinstance(value, str):
        path = _canonical_path(value, label=label)
        if not _runtime_path_allowed(path):
            raise ProductProjectionError(f"{label} is outside the runtime allowlist: {path}")
        if _is_forbidden_runtime_path(path):
            raise ProductProjectionError(f"{label} is a forbidden test/fixture path: {path}")
        return ProjectionEntry(path)
    if not isinstance(value, dict):
        raise ProductProjectionError(f"{label} must be a path string or object")
    allowed = {"path", "bytes", "size", "sha256"}
    unknown = set(value) - allowed
    if unknown:
        raise ProductProjectionError(
            f"{label} contains unknown fields: {sorted(unknown)}"
        )
    path = _canonical_path(value.get("path"), label=label)
    if not _runtime_path_allowed(path):
        raise ProductProjectionError(f"{label} is outside the runtime allowlist: {path}")
    if _is_forbidden_runtime_path(path):
        raise ProductProjectionError(f"{label} is a forbidden test/fixture path: {path}")
    raw_bytes = value.get("bytes", value.get("size"))
    if "bytes" in value and "size" in value and value["bytes"] != value["size"]:
        raise ProductProjectionError(f"{label} bytes and size fields disagree")
    if raw_bytes is not None and (
        isinstance(raw_bytes, bool) or not isinstance(raw_bytes, int) or raw_bytes < 0
    ):
        raise ProductProjectionError(f"{label} bytes must be a non-negative integer")
    raw_sha = value.get("sha256")
    if raw_sha is not None:
        if not isinstance(raw_sha, str) or len(raw_sha) != SHA256_LENGTH:
            raise ProductProjectionError(f"{label} sha256 must be 64 hexadecimal characters")
        try:
            int(raw_sha, 16)
        except ValueError as error:
            raise ProductProjectionError(f"{label} sha256 is not hexadecimal") from error
        raw_sha = raw_sha.lower()
    return ProjectionEntry(path, raw_bytes, raw_sha)


def _entries(value: object, *, label: str) -> tuple[ProjectionEntry, ...]:
    if not isinstance(value, list):
        raise ProductProjectionError(f"{label} must be a list")
    parsed = tuple(_parse_entry(item, index=index) for index, item in enumerate(value))
    paths = [entry.path for entry in parsed]
    if len(paths) != len(set(paths)):
        duplicates = sorted(path for path in set(paths) if paths.count(path) > 1)
        raise ProductProjectionError(f"{label} contains duplicate paths: {duplicates}")
    missing_required = sorted(ROOT_FILES - set(paths))
    if missing_required:
        raise ProductProjectionError(
            f"{label} must include required root files: {missing_required}"
        )
    return tuple(sorted(parsed, key=lambda entry: entry.path))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductProjectionError(f"cannot read projection manifest {path}: {error}") from error
    if not isinstance(value, dict):
        raise ProductProjectionError("projection manifest root must be an object")
    return value


def _source_tree_digest(source_root: Path, entries: Iterable[ProjectionEntry] | None = None) -> str:
    """Digest a deterministic source tree or selected entry set."""

    rows: dict[str, dict[str, object]] = {}
    if entries is None:
        for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
            if ".git" in path.relative_to(source_root).parts:
                continue
            relative = path.relative_to(source_root).as_posix()
            rows[relative] = {
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
    else:
        for entry in entries:
            path = source_root / PurePosixPath(entry.path)
            rows[entry.path] = {
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
    # This is intentionally the same snapshot digest used by the CK3
    # acceptance runners (dict[path] -> {size, sha256}), so a formal runtime
    # tree hash can be compared directly with historical GREEN evidence.
    canonical = json.dumps(rows, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def _formal_overlay_digest(entries: Iterable[ProjectionEntry]) -> str:
    """Digest rows with the formal product-tree ordering.

    The formal currentbridge artifact uses a sorted list of rows whose field
    order is ``path, bytes, sha256``.  Keeping this separate from
    :func:`_source_tree_digest` is important: the two resulting hashes are
    expected to differ even for the same 51 files.
    """

    rows: list[dict[str, object]] = []
    for entry in sorted(entries, key=lambda item: item.path):
        if entry.bytes is None or entry.sha256 is None:
            raise ProductProjectionError(
                "formal_overlay_tree_sha256 requires bytes and sha256 on every entry"
            )
        rows.append(
            {
                "path": entry.path,
                "bytes": entry.bytes,
                "sha256": entry.sha256,
            }
        )
    canonical = json.dumps(
        rows, ensure_ascii=True, sort_keys=False, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def _file_list_digest(entries: Iterable[ProjectionEntry]) -> str:
    paths = [entry.path for entry in sorted(entries, key=lambda item: item.path)]
    canonical = json.dumps(paths, ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )
    return hashlib.sha256(canonical).hexdigest()


def _optional_digest(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != SHA256_LENGTH:
        raise ProductProjectionError(f"{key} must be a 64-character hex string")
    try:
        int(value, 16)
    except ValueError as error:
        raise ProductProjectionError(f"{key} is not hexadecimal") from error
    return value.lower()


def _catalog_entries(payload: dict[str, Any], projection_name: str) -> tuple[ProjectionEntry, ...]:
    projections = payload.get("projections")
    if not isinstance(projections, dict):
        raise ProductProjectionError("projection catalog must contain a projections object")
    selected = projections.get(projection_name)
    if isinstance(selected, dict):
        if "files" not in selected:
            raise ProductProjectionError(
                f"projection catalog entry {projection_name!r} lacks files"
            )
        selected = selected["files"]
    return _entries(selected, label=f"projection {projection_name!r}")


def load_projection(
    source_root: Path,
    *,
    projection_name: str = DEFAULT_PROJECTION,
    manifest_path: Path | None = None,
) -> ProjectionSpec:
    """Resolve a named projection without touching the destination tree."""

    source_root = Path(source_root).resolve()
    if not source_root.is_dir():
        raise ProductProjectionError(f"product source is missing: {source_root}")
    name = str(projection_name or DEFAULT_PROJECTION).strip()
    if (
        not name
        or "\x00" in name
        or "/" in name
        or "\\" in name
        or name in {".", ".."}
    ):
        raise ProductProjectionError(f"projection name is malformed: {projection_name!r}")

    if name == DEFAULT_PROJECTION and manifest_path is None:
        return ProjectionSpec(name=name, source_root=source_root, mode="broad")

    selected_manifest = Path(manifest_path).resolve() if manifest_path is not None else None
    if manifest_path is not None and Path(manifest_path).is_symlink():
        raise ProductProjectionError(
            f"projection manifest must not be a symlink: {manifest_path}"
        )
    if selected_manifest is None and name == CORE_PROJECTION:
        selected_manifest = Path(__file__).with_name(CORE_MANIFEST_NAME).resolve()
    if selected_manifest is None:
        raise ProductProjectionError(
            f"projection {name!r} requires --product-projection-manifest"
        )
    payload = _read_json(selected_manifest)
    schema = payload.get("schema_version")
    if schema != SCHEMA_VERSION:
        raise ProductProjectionError(
            f"projection manifest schema_version must be {SCHEMA_VERSION}"
        )
    kind = payload.get("kind")
    if kind not in {MANIFEST_KIND, CATALOG_KIND}:
        raise ProductProjectionError(f"unsupported projection manifest kind: {kind!r}")
    if kind == CATALOG_KIND or "projections" in payload:
        entries = _catalog_entries(payload, name)
        description = None
        selected = payload.get("projections", {}).get(name)
        if isinstance(selected, dict) and isinstance(selected.get("description"), str):
            description = selected["description"]
        source_tree_sha256 = None
        formal_overlay_tree_sha256 = None
        file_list_sha256 = None
        if isinstance(selected, dict):
            source_tree_sha256 = _optional_digest(selected, "source_tree_sha256")
            formal_overlay_tree_sha256 = _optional_digest(
                selected, "formal_overlay_tree_sha256"
            )
            file_list_sha256 = _optional_digest(selected, "file_list_sha256")
    else:
        declared_name = payload.get("projection", name)
        if not isinstance(declared_name, str) or declared_name != name:
            raise ProductProjectionError(
                f"projection manifest name {declared_name!r} does not match requested {name!r}"
            )
        entries = _entries(payload.get("files"), label="manifest files")
        description = payload.get("description") if isinstance(payload.get("description"), str) else None
        source_tree_sha256 = _optional_digest(payload, "source_tree_sha256")
        formal_overlay_tree_sha256 = _optional_digest(
            payload, "formal_overlay_tree_sha256"
        )
        file_list_sha256 = _optional_digest(payload, "file_list_sha256")
    return ProjectionSpec(
        name=name,
        source_root=source_root,
        entries=entries,
        mode="allowlist",
        manifest_path=selected_manifest,
        source_tree_sha256=source_tree_sha256,
        formal_overlay_tree_sha256=formal_overlay_tree_sha256,
        file_list_sha256=file_list_sha256,
        description=description,
    )


def _broad_entries(source_root: Path) -> tuple[ProjectionEntry, ...]:
    selected: list[ProjectionEntry] = []
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(source_root).as_posix()
        if relative == "README.md" or relative.split("/", 1)[0] in SOURCE_ONLY_ROOTS:
            continue
        if path.is_symlink():
            if _runtime_path_allowed(relative):
                raise ProductProjectionError(
                    f"product source contains a symlinked runtime path: {relative}"
                )
            continue
        if not path.is_file():
            continue
        if not _runtime_path_allowed(relative):
            continue
        if _is_forbidden_runtime_path(relative):
            raise ProductProjectionError(
                f"product source contains a forbidden test/fixture runtime path: {relative}"
            )
        selected.append(
            ProjectionEntry(relative, path.stat().st_size, _sha256(path))
        )
    return tuple(selected)


def materialize_projection(
    source_root: Path,
    destination: Path,
    *,
    projection_name: str = DEFAULT_PROJECTION,
    manifest_path: Path | None = None,
    descriptor_override: bytes | None = None,
) -> dict[str, object]:
    """Copy one projection and return immutable mount provenance.

    The caller owns creation of the fresh destination directory.  Existing
    files are rejected to avoid silently merging two projections.  A
    ``descriptor_override`` is reserved for the acceptance runner's
    canonical-launcher descriptor recovery; the source descriptor is still
    hash-checked, while the supplied canonical bytes are what get mounted.
    """

    if descriptor_override is not None and not isinstance(
        descriptor_override, (bytes, bytearray)
    ):
        raise ProductProjectionError("descriptor_override must be bytes")
    if isinstance(descriptor_override, bytearray):
        descriptor_override = bytes(descriptor_override)

    spec = load_projection(
        source_root,
        projection_name=projection_name,
        manifest_path=manifest_path,
    )
    source_root = spec.source_root
    destination_input = Path(destination)
    if destination_input.is_symlink():
        raise ProductProjectionError(
            f"projection destination must not be a symlink: {destination_input}"
        )
    destination = destination_input.resolve()
    if destination == source_root or destination in source_root.parents or source_root in destination.parents:
        raise ProductProjectionError("projection source and destination must be disjoint")
    if destination.exists() and not destination.is_dir():
        raise ProductProjectionError(f"projection destination is not a directory: {destination}")
    if destination.exists() and any(destination.iterdir()):
        raise ProductProjectionError(f"projection destination is not empty: {destination}")
    try:
        entries = _broad_entries(source_root) if spec.is_broad else spec.entries
    except OSError as error:
        raise ProductProjectionError(f"cannot inspect product source: {error}") from error
    if not entries:
        raise ProductProjectionError("projection selects no runtime files")
    if spec.formal_overlay_tree_sha256 is not None:
        observed_formal = _formal_overlay_digest(entries)
        if observed_formal != spec.formal_overlay_tree_sha256:
            raise ProductProjectionError(
                "projection formal overlay tree hash does not match manifest: "
                f"{observed_formal} != {spec.formal_overlay_tree_sha256}"
            )
    if spec.file_list_sha256 is not None:
        observed_file_list = _file_list_digest(entries)
        if observed_file_list != spec.file_list_sha256:
            raise ProductProjectionError(
                "projection file-list hash does not match manifest: "
                f"{observed_file_list} != {spec.file_list_sha256}"
            )
    if spec.source_tree_sha256 is not None:
        try:
            observed_tree = _source_tree_digest(source_root, entries)
        except OSError as error:
            raise ProductProjectionError(
                f"cannot hash selected product source files: {error}"
            ) from error
        if observed_tree != spec.source_tree_sha256:
            raise ProductProjectionError(
                "projection source tree hash does not match manifest: "
                f"{observed_tree} != {spec.source_tree_sha256}"
            )
    # Verify every selected source before creating or modifying the destination
    # so a late mismatch cannot leave a deceptively partial mount behind.
    validated: list[tuple[ProjectionEntry, Path, int, str, bytes | None]] = []
    for entry in entries:
        relative = _canonical_path(entry.path, label="selected")
        if not _runtime_path_allowed(relative):
            raise ProductProjectionError(f"selected path is outside runtime allowlist: {relative}")
        if _is_forbidden_runtime_path(relative):
            raise ProductProjectionError(
                f"selected path is a forbidden test/fixture path: {relative}"
            )
        source = source_root / PurePosixPath(relative)
        if not source.is_file() or source.is_symlink():
            raise ProductProjectionError(f"selected projection file is missing or symlinked: {source}")
        try:
            source_bytes = source.read_bytes()
            size = source.stat().st_size
            digest = hashlib.sha256(source_bytes).hexdigest()
        except OSError as error:
            raise ProductProjectionError(
                f"cannot read selected projection file {source}: {error}"
            ) from error
        if entry.bytes is not None and size != entry.bytes:
            raise ProductProjectionError(
                f"projection byte count mismatch for {relative}: {size} != {entry.bytes}"
            )
        if entry.sha256 is not None and digest != entry.sha256:
            raise ProductProjectionError(
                f"projection SHA-256 mismatch for {relative}: {digest} != {entry.sha256}"
            )
        override_bytes = (
            descriptor_override if relative == "descriptor.mod" else None
        )
        try:
            if b"remote_file_id" in source_bytes and override_bytes is None:
                raise ProductProjectionError(
                    f"selected projection file contains Workshop identity: {relative}"
                )
        except OSError as error:
            raise ProductProjectionError(
                f"cannot inspect selected projection file {source}: {error}"
            ) from error
        validated.append((entry, source, size, digest, override_bytes))
    selected_paths = {entry.path for entry, _source, _size, _digest, _override in validated}
    missing = sorted(ROOT_FILES - selected_paths)
    if missing:
        raise ProductProjectionError(f"projection omitted required root files: {missing}")
    destination.mkdir(parents=True, exist_ok=True)
    observed: list[dict[str, object]] = []
    for entry, source, size, digest, override_bytes in validated:
        relative = entry.path
        target = destination / PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if override_bytes is None:
            shutil.copy2(source, target)
            observed_size = size
            observed_digest = digest
        else:
            target.write_bytes(override_bytes)
            observed_size = len(override_bytes)
            observed_digest = hashlib.sha256(override_bytes).hexdigest()
        observed.append(
            {"path": relative, "bytes": observed_size, "sha256": observed_digest}
        )
    tree_sha256 = _source_tree_digest(destination)
    manifest_sha256 = _sha256(spec.manifest_path) if spec.manifest_path is not None else None
    return {
        "schema_version": SCHEMA_VERSION,
        "name": spec.name,
        "projection": spec.name,
        "mode": spec.mode,
        "source_root": str(source_root),
        "destination": str(destination),
        "manifest_path": str(spec.manifest_path) if spec.manifest_path is not None else None,
        "manifest_sha256": manifest_sha256,
        "source_tree_sha256": spec.source_tree_sha256,
        "formal_overlay_tree_sha256": spec.formal_overlay_tree_sha256,
        "file_list_sha256": spec.file_list_sha256,
        "tree_sha256": tree_sha256,
        "file_count": len(observed),
        "bytes": sum(int(row["bytes"]) for row in observed),
        "files": observed,
    }


def write_manifest(source_root: Path, output: Path, *, projection_name: str = DEFAULT_PROJECTION) -> dict[str, object]:
    """Create a hash-bound manifest from an already prepared product tree."""

    source_root = Path(source_root).resolve()
    if not source_root.is_dir():
        raise ProductProjectionError(f"product source is missing: {source_root}")
    entries = _broad_entries(source_root)
    selected_paths = {entry.path for entry in entries}
    missing = sorted(ROOT_FILES - selected_paths)
    if missing:
        raise ProductProjectionError(f"product source is missing required root files: {missing}")
    if projection_name != DEFAULT_PROJECTION:
        # A generated standalone manifest is an explicit named group.  Callers
        # can generate one directly from each offline bisect directory.
        name = projection_name
    else:
        name = DEFAULT_PROJECTION
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "kind": MANIFEST_KIND,
        "projection": name,
        "description": "Hash-bound Phase2 product projection generated from a frozen source tree.",
        "source_tree_sha256": _source_tree_digest(source_root, entries),
        "formal_overlay_tree_sha256": _formal_overlay_digest(entries),
        "file_list_sha256": _file_list_digest(entries),
        "files": [entry.as_dict() for entry in entries],
    }
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--projection", default=DEFAULT_PROJECTION)
    args = parser.parse_args(argv)
    try:
        payload = write_manifest(args.source, args.output, projection_name=args.projection)
    except ProductProjectionError as error:
        print(f"projection manifest failed: {error}")
        return 2
    print(
        json.dumps(
            {
                "result": "GREEN",
                "projection": payload["projection"],
                "file_count": len(payload["files"]),
                "source_tree_sha256": payload["source_tree_sha256"],
                "output": str(Path(args.output).resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
