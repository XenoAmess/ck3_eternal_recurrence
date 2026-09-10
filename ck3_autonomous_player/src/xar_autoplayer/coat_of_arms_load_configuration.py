"""Read-only MCP projection of CK3's configured mod list for CoA resources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Final

from .coat_of_arms_resources import (
    CoatOfArmsResourceCatalogError,
    _sha256,
    _tokenize,
)


_MAX_LOAD_CONFIGURATION_BYTES: Final = 1024 * 1024
_MAX_DESCRIPTOR_BYTES: Final = 1024 * 1024
_MAX_ENABLED_MODS: Final = 128
_MAX_CANDIDATE_FILES_PER_DIRECTORY: Final = 4096
_COA_DIRECTORIES: Final = {
    "pattern_assets": Path("gfx/coat_of_arms/patterns"),
    "colored_emblem_assets": Path("gfx/coat_of_arms/colored_emblems"),
    "textured_emblem_assets": Path("gfx/coat_of_arms/textured_emblems"),
    "color_palette_definitions": Path("gfx/coat_of_arms/color_palettes"),
    "emblem_layout_definitions": Path("gfx/coat_of_arms/emblem_layouts"),
    "coat_of_arms_definitions": Path("common/coat_of_arms/coat_of_arms"),
    "dynamic_definitions": Path("common/coat_of_arms/dynamic_definitions"),
    "options": Path("common/coat_of_arms/options"),
    "template_lists": Path("common/coat_of_arms/template_lists"),
}


_DescriptorEntries = tuple[tuple[str, str | None], ...]


def _scalar_values(entries: _DescriptorEntries, key: str) -> list[str]:
    return [
        value
        for entry_key, value in entries
        if entry_key == key and value is not None
    ]


def _single_scalar(
    entries: _DescriptorEntries,
    key: str,
) -> str | None:
    values = _scalar_values(entries, key)
    if len(values) > 1:
        raise CoatOfArmsResourceCatalogError(
            f"mod descriptor repeats scalar property {key}"
        )
    return values[0] if values else None


def _parse_descriptor(text: str) -> _DescriptorEntries:
    tokens = _tokenize(text)
    entries: list[tuple[str, str | None]] = []
    index = 0
    while index < len(tokens):
        key = tokens[index]
        if key.value in "{}=":
            raise CoatOfArmsResourceCatalogError(
                f"invalid descriptor key at {key.line}:{key.column}"
            )
        index += 1
        if index >= len(tokens) or tokens[index].value != "=":
            raise CoatOfArmsResourceCatalogError(
                f"expected '=' after descriptor key at {key.line}:{key.column}"
            )
        index += 1
        if index >= len(tokens):
            raise CoatOfArmsResourceCatalogError(
                "unexpected end of mod descriptor"
            )
        value = tokens[index]
        index += 1
        if value.value == "{":
            depth = 1
            while index < len(tokens) and depth:
                if tokens[index].value == "{":
                    depth += 1
                elif tokens[index].value == "}":
                    depth -= 1
                index += 1
            if depth:
                raise CoatOfArmsResourceCatalogError(
                    f"unterminated descriptor block at {value.line}:{value.column}"
                )
            entries.append((key.value, None))
        elif value.value in "}=":
            raise CoatOfArmsResourceCatalogError(
                f"invalid descriptor value at {value.line}:{value.column}"
            )
        else:
            entries.append((key.value, value.value))
    return tuple(entries)


def _read_descriptor(path: Path) -> _DescriptorEntries:
    if not path.is_file() or not 0 < path.stat().st_size <= _MAX_DESCRIPTOR_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "enabled mod descriptor is missing or outside the size contract"
    )
    try:
        return _parse_descriptor(path.read_text(encoding="utf-8-sig"))
    except UnicodeError as error:
        raise CoatOfArmsResourceCatalogError(
            "enabled mod descriptor is not UTF-8"
        ) from error


def _resolve_descriptor(user_root: Path, registry_path: str) -> Path:
    if not registry_path or Path(registry_path).is_absolute():
        raise CoatOfArmsResourceCatalogError(
            "enabled mod registry path must be relative to the CK3 user directory"
        )
    descriptor = (user_root / Path(registry_path.replace("/", "\\"))).resolve()
    if not descriptor.is_relative_to(user_root):
        raise CoatOfArmsResourceCatalogError(
            "enabled mod registry path escapes the CK3 user directory"
        )
    return descriptor


def _resolve_content_root(user_root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    candidate = Path(value.replace("/", "\\"))
    if not candidate.is_absolute():
        candidate = user_root / candidate
    return candidate.expanduser().resolve()


def _candidate_files(root: Path, directory: Path) -> dict[str, object]:
    target = root / directory
    if not target.is_dir():
        return {
            "relative_directory": directory.as_posix(),
            "directory_exists": False,
            "txt": [],
            "dds_count": 0,
        }
    files = sorted(
        (path for path in target.iterdir() if path.is_file()),
        key=lambda path: path.name.casefold(),
    )
    if len(files) > _MAX_CANDIDATE_FILES_PER_DIRECTORY:
        raise CoatOfArmsResourceCatalogError(
            f"CoA resource directory exceeds {_MAX_CANDIDATE_FILES_PER_DIRECTORY} files"
        )
    return {
        "relative_directory": directory.as_posix(),
        "directory_exists": True,
        "txt": [
            path.relative_to(root).as_posix()
            for path in files
            if path.suffix.casefold() == ".txt"
        ],
        "dds_count": sum(path.suffix.casefold() == ".dds" for path in files),
    }


def _mod_projection(
    user_root: Path,
    registry_path: str,
    load_order: int,
) -> dict[str, object]:
    descriptor = _resolve_descriptor(user_root, registry_path)
    entries = _read_descriptor(descriptor)
    path_value = _single_scalar(entries, "path")
    archive_value = _single_scalar(entries, "archive")
    if bool(path_value) == bool(archive_value):
        raise CoatOfArmsResourceCatalogError(
            "enabled mod descriptor must define exactly one of path or archive"
        )
    root = _resolve_content_root(user_root, path_value)
    archive = _resolve_content_root(user_root, archive_value)
    replace_paths = _scalar_values(entries, "replace_path")
    coa_replace_paths = [
        value
        for value in replace_paths
        if value.replace("\\", "/").strip("/").casefold().startswith(
            "gfx/coat_of_arms"
        )
    ]
    resource_candidates = {
        name: _candidate_files(root, relative)
        for name, relative in _COA_DIRECTORIES.items()
    } if root and root.is_dir() else {
        name: {
            "relative_directory": relative.as_posix(),
            "directory_exists": False,
            "txt": [],
            "dds_count": 0,
        }
        for name, relative in _COA_DIRECTORIES.items()
    }
    return {
        "load_order": load_order,
        "registry_path": registry_path.replace("\\", "/"),
        "descriptor_relative_path": descriptor.relative_to(user_root).as_posix(),
        "descriptor_bytes": descriptor.stat().st_size,
        "descriptor_sha256": _sha256(descriptor),
        "name": _single_scalar(entries, "name"),
        "version": _single_scalar(entries, "version"),
        "supported_version": _single_scalar(entries, "supported_version"),
        "remote_file_id": _single_scalar(entries, "remote_file_id"),
        "content_kind": "directory" if root else "archive",
        "content_root": str(root) if root else None,
        "content_root_exists": root.is_dir() if root else None,
        "archive_path": str(archive) if archive else None,
        "archive_exists": archive.is_file() if archive else None,
        "replace_paths": replace_paths,
        "coa_replace_paths": coa_replace_paths,
        "resource_candidates": resource_candidates,
    }


def query_coat_of_arms_load_configuration_v1(
    user_directory: str,
) -> dict[str, object]:
    """Project the ordered enabled-mod configuration without claiming VFS mount."""

    if not isinstance(user_directory, str) or not user_directory.strip():
        raise ValueError("user_directory must be a non-empty string")
    user_root = Path(user_directory).expanduser().resolve()
    load_path = user_root / "dlc_load.json"
    if not load_path.is_file() or not 0 < load_path.stat().st_size <= _MAX_LOAD_CONFIGURATION_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "user_directory lacks a bounded dlc_load.json"
        )
    try:
        raw = load_path.read_bytes()
        configuration = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CoatOfArmsResourceCatalogError(
            "dlc_load.json is not valid UTF-8 JSON"
        ) from error
    if not isinstance(configuration, dict):
        raise CoatOfArmsResourceCatalogError("dlc_load.json must be an object")
    enabled = configuration.get("enabled_mods")
    disabled_dlcs = configuration.get("disabled_dlcs", [])
    if (
        not isinstance(enabled, list)
        or any(not isinstance(value, str) for value in enabled)
        or len(enabled) > _MAX_ENABLED_MODS
    ):
        raise CoatOfArmsResourceCatalogError(
            f"enabled_mods must contain at most {_MAX_ENABLED_MODS} strings"
        )
    if not isinstance(disabled_dlcs, list) or any(
        not isinstance(value, str) for value in disabled_dlcs
    ):
        raise CoatOfArmsResourceCatalogError("disabled_dlcs must be a string list")
    mods = [
        _mod_projection(user_root, registry_path, index)
        for index, registry_path in enumerate(enabled)
    ]
    return {
        "schema": "ck3-coat-of-arms-load-configuration-v1",
        "schema_version": 1,
        "status": "configured",
        "enabled_mod_count": len(mods),
        "disabled_dlcs": disabled_dlcs,
        "mods": mods,
        "provenance": {
            "mode": "dlc-load-json-and-descriptor-static",
            "load_configuration_relative_path": "dlc_load.json",
            "load_configuration_bytes": len(raw),
            "load_configuration_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "load_configuration_mtime_ns": load_path.stat().st_mtime_ns,
            "launcher_database_used": False,
            "engine_mount_observed": False,
            "resource_merge_applied": False,
            "archive_resource_enumeration_supported": False,
            "candidate_scan_depth": "direct-files-only",
        },
    }
