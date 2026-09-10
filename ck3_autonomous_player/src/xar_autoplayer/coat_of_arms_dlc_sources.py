"""Exact-build installed DLC inventory for coat-of-arms source candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from .coat_of_arms_load_configuration import (
    _COA_DIRECTORIES,
    _candidate_files,
    _read_descriptor,
    _single_scalar,
)
from .coat_of_arms_resources import (
    CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD,
    CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256,
    CoatOfArmsResourceCatalogError,
    _sha256,
)


_MAX_DLC_DESCRIPTORS: Final = 128


def _content_root(game_content_root: Path, value: str | None) -> Path:
    if not value:
        raise CoatOfArmsResourceCatalogError("DLC descriptor has no content path")
    path = Path(value.replace("/", "\\"))
    if path.is_absolute():
        raise CoatOfArmsResourceCatalogError(
            "DLC descriptor content path must be relative to the game directory"
        )
    result = (game_content_root / path).resolve()
    if not result.is_relative_to(game_content_root):
        raise CoatOfArmsResourceCatalogError(
            "DLC descriptor content path escapes the game directory"
        )
    return result


def query_coat_of_arms_installed_dlc_sources_v1(
    game_directory: str,
) -> dict[str, object]:
    """List installed DLC trees that physically contain direct CoA candidates."""

    if not isinstance(game_directory, str) or not game_directory.strip():
        raise ValueError("game_directory must be a non-empty string")
    game_root = Path(game_directory).expanduser().resolve()
    executable = game_root / "binaries" / "ck3.exe"
    game_content_root = game_root / "game"
    dlc_root = game_content_root / "dlc"
    if not executable.is_file() or not dlc_root.is_dir():
        raise CoatOfArmsResourceCatalogError(
            "game_directory lacks the CK3 executable or DLC directory"
        )
    executable_sha256 = _sha256(executable)
    if executable_sha256 != CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256:
        raise CoatOfArmsResourceCatalogError(
            "CK3 executable does not match the frozen 1.19.0.6 DLC inventory build"
        )

    descriptors = sorted(
        dlc_root.glob("*/*.dlc"),
        key=lambda path: path.relative_to(game_content_root).as_posix().casefold(),
    )
    if len(descriptors) > _MAX_DLC_DESCRIPTORS:
        raise CoatOfArmsResourceCatalogError(
            "installed DLC descriptor count exceeds the v1 contract"
        )

    items: list[dict[str, object]] = []
    dlc_with_coa_candidates = 0
    total_txt_files = 0
    total_dds_files = 0
    for descriptor in descriptors:
        entries = _read_descriptor(descriptor)
        content_root = _content_root(
            game_content_root,
            _single_scalar(entries, "path"),
        )
        candidates = {
            name: _candidate_files(content_root, relative)
            for name, relative in _COA_DIRECTORIES.items()
        }
        txt_count = sum(len(value["txt"]) for value in candidates.values())
        dds_count = sum(int(value["dds_count"]) for value in candidates.values())
        has_coa_candidates = any(
            bool(value["directory_exists"])
            for value in candidates.values()
        )
        if has_coa_candidates:
            dlc_with_coa_candidates += 1
        total_txt_files += txt_count
        total_dds_files += dds_count
        items.append(
            {
                "descriptor_relative_path": descriptor.relative_to(
                    game_content_root
                ).as_posix(),
                "descriptor_bytes": descriptor.stat().st_size,
                "descriptor_sha256": _sha256(descriptor),
                "name": _single_scalar(entries, "name"),
                "localizable_name": _single_scalar(entries, "localizable_name"),
                "steam_id": _single_scalar(entries, "steam_id"),
                "content_relative_path": content_root.relative_to(
                    game_content_root
                ).as_posix(),
                "content_root_exists": content_root.is_dir(),
                "has_coa_candidates": has_coa_candidates,
                "coa_txt_file_count": txt_count,
                "coa_dds_file_count": dds_count,
                "resource_candidates": candidates,
            }
        )

    return {
        "schema": "ck3-coat-of-arms-installed-dlc-sources-v1",
        "schema_version": 1,
        "status": "indexed",
        "ck3_build": CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD,
        "installed_descriptor_count": len(items),
        "dlc_with_coa_candidates": dlc_with_coa_candidates,
        "coa_txt_file_count": total_txt_files,
        "coa_dds_file_count": total_dds_files,
        "items": items,
        "provenance": {
            "mode": "installed-dlc-direct-file-inventory-static",
            "executable_sha256": executable_sha256,
            "dlc_relative_directory": "game/dlc",
            "descriptor_pattern": "*/*.dlc",
            "candidate_scan_depth": "direct-files-only",
            "installed_files_observed": True,
            "store_entitlement_observed": False,
            "dlc_load_disabled_list_applied": False,
            "engine_mount_observed": False,
            "resource_merge_applied": False,
        },
    }
