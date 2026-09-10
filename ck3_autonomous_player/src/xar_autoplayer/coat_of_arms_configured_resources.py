"""Read-only configured-mod CoA candidates without claiming engine merge."""

from __future__ import annotations

import base64
from collections import Counter
import hashlib
from pathlib import Path
from typing import Final

from .coat_of_arms_load_configuration import (
    query_coat_of_arms_load_configuration_v1,
)
from .coat_of_arms_resources import (
    CK3_COAT_OF_ARMS_RESOURCE_KINDS,
    CoatOfArmsResourceCatalogError,
    _designer_entries,
    _sha256,
)


_MAX_PAGE_SIZE: Final = 200
_MAX_CONFIGURED_MANIFESTS: Final = 512
_MAX_CONFIGURED_RESOURCES: Final = 20_000
_MAX_ASSET_BYTES: Final = 1024 * 1024
_KIND_DIRECTORIES: Final = {
    "pattern": (
        "pattern_assets",
        Path("gfx/coat_of_arms/patterns"),
    ),
    "colored_emblem": (
        "colored_emblem_assets",
        Path("gfx/coat_of_arms/colored_emblems"),
    ),
    "color": (
        "color_palette_definitions",
        None,
    ),
}


def _validate_catalog_arguments(
    kind: str,
    query: str | None,
    visible_only: bool,
    offset: int,
    limit: int,
) -> None:
    if kind not in CK3_COAT_OF_ARMS_RESOURCE_KINDS:
        raise ValueError("kind must be pattern, colored_emblem, or color")
    if query is not None and (not isinstance(query, str) or len(query) > 128):
        raise ValueError("query must be null or a string of at most 128 characters")
    if not isinstance(visible_only, bool):
        raise ValueError("visible_only must be boolean")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= _MAX_PAGE_SIZE
    ):
        raise ValueError(f"limit must be between 1 and {_MAX_PAGE_SIZE}")


def _candidate_id(
    load_sha256: str,
    descriptor_sha256: str,
    load_order: int,
    manifest_relative: str,
    manifest_sha256: str,
    resource_index: int,
    kind: str,
    name: str,
) -> str:
    identity = "\0".join(
        (
            load_sha256,
            descriptor_sha256,
            str(load_order),
            manifest_relative,
            manifest_sha256,
            str(resource_index),
            kind,
            name,
        )
    ).encode("utf-8")
    return hashlib.sha256(identity).hexdigest().upper()


def _direct_asset_path(
    root: Path,
    asset_directory: Path | None,
    name: str,
) -> Path | None:
    if asset_directory is None:
        return None
    candidate_name = Path(name)
    if (
        not name
        or candidate_name.name != name
        or "/" in name
        or "\\" in name
    ):
        return None
    return root / asset_directory / candidate_name


def _collect_configured_candidates(
    user_directory: str,
    kind: str,
) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    configuration = query_coat_of_arms_load_configuration_v1(user_directory)
    directory_key, asset_directory = _KIND_DIRECTORIES[kind]
    load_sha256 = str(configuration["provenance"]["load_configuration_sha256"])
    candidates: list[dict[str, object]] = []
    skipped_archives: list[dict[str, object]] = []
    manifest_count = 0
    for mod in configuration["mods"]:
        if mod["content_kind"] == "archive":
            skipped_archives.append(
                {
                    "load_order": mod["load_order"],
                    "registry_path": mod["registry_path"],
                    "name": mod["name"],
                }
            )
            continue
        content_root = Path(str(mod["content_root"])).resolve()
        source = mod["resource_candidates"][directory_key]
        for manifest_relative in source["txt"]:
            manifest_count += 1
            if manifest_count > _MAX_CONFIGURED_MANIFESTS:
                raise CoatOfArmsResourceCatalogError(
                    "configured CoA manifest count exceeds the v1 contract"
                )
            manifest = (content_root / Path(manifest_relative)).resolve()
            if not manifest.is_relative_to(content_root) or not manifest.is_file():
                raise CoatOfArmsResourceCatalogError(
                    "configured CoA manifest moved outside its projected source"
                )
            manifest_sha256 = _sha256(manifest)
            for resource_index, resource in enumerate(
                _designer_entries(kind, manifest)
            ):
                if len(candidates) >= _MAX_CONFIGURED_RESOURCES:
                    raise CoatOfArmsResourceCatalogError(
                        "configured CoA resource count exceeds the v1 contract"
                    )
                name = str(resource["name"])
                candidates.append(
                    {
                        "candidate_id": _candidate_id(
                            load_sha256,
                            str(mod["descriptor_sha256"]),
                            int(mod["load_order"]),
                            str(manifest_relative),
                            manifest_sha256,
                            resource_index,
                            kind,
                            name,
                        ),
                        "load_order": mod["load_order"],
                        "registry_path": mod["registry_path"],
                        "mod_name": mod["name"],
                        "descriptor_sha256": mod["descriptor_sha256"],
                        "content_root": str(content_root),
                        "manifest_relative_path": manifest_relative,
                        "manifest_bytes": manifest.stat().st_size,
                        "manifest_sha256": manifest_sha256,
                        "manifest_resource_index": resource_index,
                        "kind": kind,
                        **resource,
                        "asset_directory": (
                            asset_directory.as_posix()
                            if asset_directory is not None
                            else None
                        ),
                    }
                )
    return candidates, configuration, skipped_archives


def _catalog_item(candidate: dict[str, object]) -> dict[str, object]:
    root = Path(str(candidate["content_root"]))
    directory_value = candidate["asset_directory"]
    asset_directory = Path(str(directory_value)) if directory_value else None
    asset = _direct_asset_path(root, asset_directory, str(candidate["name"]))
    asset_exists = asset.is_file() if asset is not None else None
    return {
        key: value
        for key, value in candidate.items()
        if key not in {"content_root", "asset_directory"}
    } | {
        "asset_relative_path": (
            asset.relative_to(root).as_posix() if asset is not None else None
        ),
        "asset_exists": asset_exists,
        "asset_bytes": asset.stat().st_size if asset_exists else None,
        "asset_sha256": _sha256(asset) if asset_exists else None,
    }


def query_coat_of_arms_configured_resource_catalog_v1(
    user_directory: str,
    kind: str,
    *,
    query: str | None = None,
    visible_only: bool = True,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, object]:
    """Page configured directory-mod candidates without choosing a winner."""

    if not isinstance(user_directory, str) or not user_directory.strip():
        raise ValueError("user_directory must be a non-empty string")
    _validate_catalog_arguments(kind, query, visible_only, offset, limit)
    directory_key, _ = _KIND_DIRECTORIES[kind]
    candidates, configuration, skipped_archives = _collect_configured_candidates(
        user_directory, kind
    )
    name_counts = Counter(str(candidate["name"]) for candidate in candidates)
    needle = (query or "").casefold().strip()
    filtered = [
        candidate
        for candidate in candidates
        if (not visible_only or candidate["visible"] is True)
        and (
            not needle
            or needle in str(candidate["name"]).casefold()
            or needle in str(candidate["category"] or "").casefold()
            or needle in str(candidate["mod_name"] or "").casefold()
        )
    ]
    page = filtered[offset : offset + limit]
    items = []
    for source_index, candidate in enumerate(page, start=offset):
        item = _catalog_item(candidate)
        item["index"] = source_index
        item["same_name_configured_candidate_count"] = name_counts[
            str(candidate["name"])
        ]
        item["potential_configured_name_conflict"] = (
            item["same_name_configured_candidate_count"] > 1
        )
        items.append(item)
    next_offset = offset + len(page)
    has_more = next_offset < len(filtered)
    return {
        "schema": "ck3-coat-of-arms-configured-resource-catalog-v1",
        "schema_version": 1,
        "status": "indexed",
        "kind": kind,
        "query": query,
        "visible_only": visible_only,
        "offset": offset,
        "limit": limit,
        "total": len(filtered),
        "returned": len(items),
        "has_more": has_more,
        "next_offset": next_offset if has_more else None,
        "items": items,
        "skipped_archives": skipped_archives,
        "provenance": {
            "mode": "configured-directory-mod-candidates-static",
            "load_configuration_sha256": configuration["provenance"][
                "load_configuration_sha256"
            ],
            "enabled_mod_count": configuration["enabled_mod_count"],
            "manifest_count": sum(
                len(
                    mod["resource_candidates"][directory_key]["txt"]
                )
                for mod in configuration["mods"]
                if mod["content_kind"] == "directory"
            ),
            "configured_candidate_count": len(candidates),
            "archive_mods_skipped": len(skipped_archives),
            "base_game_resources_included": False,
            "engine_registration_observed": False,
            "resource_merge_applied": False,
            "load_order_precedence_applied": False,
        },
    }


def _dds_metadata(data: bytes) -> dict[str, object]:
    if len(data) < 128 or data[:4] != b"DDS ":
        raise CoatOfArmsResourceCatalogError("configured asset is not DDS")
    if int.from_bytes(data[4:8], "little") != 124:
        raise CoatOfArmsResourceCatalogError("configured DDS header is invalid")
    try:
        four_cc = data[84:88].decode("ascii")
    except UnicodeError as error:
        raise CoatOfArmsResourceCatalogError(
            "configured DDS FourCC is not ASCII"
        ) from error
    return {
        "width": int.from_bytes(data[16:20], "little"),
        "height": int.from_bytes(data[12:16], "little"),
        "mipmap_count": max(1, int.from_bytes(data[28:32], "little")),
        "four_cc": four_cc,
    }


def read_coat_of_arms_configured_resource_asset_v1(
    user_directory: str,
    kind: str,
    candidate_id: str,
) -> dict[str, object]:
    """Read one current-config manifest candidate by its opaque identity."""

    if not isinstance(user_directory, str) or not user_directory.strip():
        raise ValueError("user_directory must be a non-empty string")
    if kind not in {"pattern", "colored_emblem"}:
        raise ValueError("kind must be pattern or colored_emblem")
    if (
        not isinstance(candidate_id, str)
        or len(candidate_id) != 64
        or any(character not in "0123456789ABCDEF" for character in candidate_id)
    ):
        raise ValueError("candidate_id must be 64 uppercase hexadecimal characters")
    candidates, configuration, _ = _collect_configured_candidates(
        user_directory, kind
    )
    matches = [
        candidate
        for candidate in candidates
        if candidate["candidate_id"] == candidate_id
    ]
    if len(matches) != 1:
        raise CoatOfArmsResourceCatalogError(
            "candidate_id is not uniquely present in the current configuration"
        )
    candidate = matches[0]
    root = Path(str(candidate["content_root"]))
    asset = _direct_asset_path(
        root,
        Path(str(candidate["asset_directory"])),
        str(candidate["name"]),
    )
    if asset is None or not asset.is_file():
        raise CoatOfArmsResourceCatalogError(
            "configured manifest asset is missing or outside the direct asset contract"
        )
    size = asset.stat().st_size
    if not 128 <= size <= _MAX_ASSET_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "configured DDS size is outside the v1 asset contract"
        )
    data = asset.read_bytes()
    metadata = _dds_metadata(data)
    return {
        "schema": "ck3-coat-of-arms-configured-resource-asset-v1",
        "schema_version": 1,
        "status": "read",
        "kind": kind,
        "candidate_id": candidate_id,
        "name": candidate["name"],
        "colors": candidate["colors"],
        "visible": candidate["visible"],
        "category": candidate["category"],
        "load_order": candidate["load_order"],
        "registry_path": candidate["registry_path"],
        "mod_name": candidate["mod_name"],
        "asset_relative_path": asset.relative_to(root).as_posix(),
        "content_type": "application/octet-stream",
        "asset_bytes": size,
        "asset_sha256": hashlib.sha256(data).hexdigest().upper(),
        "asset_base64": base64.b64encode(data).decode("ascii"),
        "dds": metadata,
        "provenance": {
            "mode": "configured-directory-mod-manifest-candidate-static",
            "load_configuration_sha256": configuration["provenance"][
                "load_configuration_sha256"
            ],
            "descriptor_sha256": candidate["descriptor_sha256"],
            "manifest_relative_path": candidate["manifest_relative_path"],
            "manifest_sha256": candidate["manifest_sha256"],
            "engine_registration_observed": False,
            "resource_merge_applied": False,
            "load_order_precedence_applied": False,
        },
    }
