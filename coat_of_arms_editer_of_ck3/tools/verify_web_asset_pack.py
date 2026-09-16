#!/usr/bin/env python3
"""Verify a ck3-coa-web-asset-pack-v1 directory without reading or launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct


SHA256 = re.compile(r"^[0-9A-F]{64}$")
SAFE_URL = re.compile(r"^assets/[0-9a-f]{64}\.dds$")
SAFE_INDEX_URL = re.compile(r"^assets/[0-9a-f]{64}\.rgba$")
SAFE_FEATURE_URL = re.compile(r"^assets/[0-9a-f]{64}\.fit$")
FIT_SHAPE_DESCRIPTOR_SIZE = 18
FIT_SHAPE_SCALAR_FIELDS = (
    "content_min_x", "content_min_y", "content_max_x", "content_max_y",
    "content_center_x", "content_center_y", "content_span_x", "content_span_y",
    "alpha_energy", "red_energy", "green_energy", "blue_energy", "contour_energy",
)
FIT_FEATURE_HEADER_BYTES = 32
FIT_FEATURE_RECORD_BYTES = (
    len(FIT_SHAPE_SCALAR_FIELDS) * 8
    + FIT_SHAPE_DESCRIPTOR_SIZE * FIT_SHAPE_DESCRIPTOR_SIZE * 4
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def verify(pack_directory: Path) -> dict[str, object]:
    pack_directory = pack_directory.resolve()
    manifest_path = pack_directory / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    if not 2 <= len(manifest_bytes) <= 4 * 1024 * 1024:
        raise ValueError("manifest size is outside 2 B..4 MiB")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if manifest.get("schema") != "ck3-coa-web-asset-pack-v1" or manifest.get("schema_version") != 1:
        raise ValueError("unsupported manifest schema/version")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not 1 <= len(assets) <= 4096:
        raise ValueError("assets count is outside 1..4096")
    seen: set[tuple[str, str]] = set()
    surface_masks = 0
    totals = {
        "pattern": 0,
        "colored_emblem": 0,
        "auxiliary_colored_emblem": 0,
        "textured_emblem": 0,
        "surface_mask": 0,
    }
    total_bytes = 0
    source_paths: set[str] = set()
    for index, item in enumerate(assets):
        if not isinstance(item, dict):
            raise ValueError(f"assets[{index}] is not an object")
        kind = item.get("kind")
        name = item.get("name")
        if kind not in totals or not isinstance(name, str):
            raise ValueError(f"assets[{index}] kind/name is invalid")
        key = (kind, name)
        if key in seen:
            raise ValueError(f"duplicate logical asset: {kind}/{name}")
        seen.add(key)
        if kind == "surface_mask":
            surface_masks += 1
        source_relative_path = item.get("source_relative_path")
        if not isinstance(source_relative_path, str) or not source_relative_path or "\\" in source_relative_path:
            raise ValueError(f"assets[{index}] source_relative_path is invalid")
        source_relative = PurePosixPath(source_relative_path)
        if source_relative.is_absolute() or ".." in source_relative.parts:
            raise ValueError(f"assets[{index}] source_relative_path escapes the source root")
        source_key = source_relative_path.casefold()
        if source_key in source_paths:
            raise ValueError(f"duplicate physical source path: {source_relative_path}")
        source_paths.add(source_key)
        registration = item.get("registration")
        if registration not in {"designer_manifest", "unregistered_file", "render_support"}:
            raise ValueError(f"assets[{index}] registration is invalid")
        if not isinstance(item.get("fit_eligible"), bool):
            raise ValueError(f"assets[{index}] fit_eligible is invalid")
        url = item.get("url")
        expected_sha = item.get("asset_sha256")
        expected_bytes = item.get("asset_bytes")
        if not isinstance(url, str) or not SAFE_URL.fullmatch(url):
            raise ValueError(f"assets[{index}] URL is not content addressed")
        if not isinstance(expected_sha, str) or not SHA256.fullmatch(expected_sha):
            raise ValueError(f"assets[{index}] SHA-256 is invalid")
        relative = PurePosixPath(url)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"assets[{index}] URL escapes the pack")
        path = pack_directory.joinpath(*relative.parts).resolve()
        if pack_directory not in path.parents:
            raise ValueError(f"assets[{index}] path escapes the pack")
        data = path.read_bytes()
        if len(data) != expected_bytes or digest(data) != expected_sha:
            raise ValueError(f"assets[{index}] bytes/hash mismatch")
        if data[:4] != b"DDS " or int.from_bytes(data[4:8], "little") != 124:
            raise ValueError(f"assets[{index}] is not a DDS container")
        totals[kind] += 1
        total_bytes += len(data)
    if surface_masks != 1:
        raise ValueError("pack must contain exactly one surface_mask")
    vfs_receipt = manifest.get("vfs_receipt")
    if not isinstance(vfs_receipt, dict) or vfs_receipt.get("schema") != "ck3-coa-vfs-receipt-v1":
        raise ValueError("pack must contain a supported vfs_receipt")
    if vfs_receipt.get("resolved_asset_count") != len(assets):
        raise ValueError("vfs_receipt resolved_asset_count does not match assets")
    conflict_count = vfs_receipt.get("conflict_count")
    if not isinstance(conflict_count, int) or not 0 <= conflict_count <= 4096:
        raise ValueError("vfs_receipt conflict_count is invalid")
    sources = vfs_receipt.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 512:
        raise ValueError("vfs_receipt sources are invalid")
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"vfs_receipt sources[{index}] is not an object")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in source_ids:
            raise ValueError(f"vfs_receipt sources[{index}] source_id is invalid")
        source_ids.add(source_id)
        if source.get("source_kind") not in {"base_game", "dlc", "directory_mod", "archive_mod"}:
            raise ValueError(f"vfs_receipt sources[{index}] source_kind is invalid")
        if source.get("precedence_order") != index:
            raise ValueError("vfs_receipt sources must have contiguous precedence order")
        if not isinstance(source.get("source_identity_sha256"), str) or not SHA256.fullmatch(source["source_identity_sha256"]):
            raise ValueError(f"vfs_receipt sources[{index}] identity is invalid")
    scope = vfs_receipt.get("scope")
    policy = vfs_receipt.get("resolution_policy")
    load_sha256 = vfs_receipt.get("load_configuration_sha256")
    if scope == "base_game_only":
        if (
            len(sources) != 1
            or sources[0].get("source_kind") != "base_game"
            or policy != "single_source_no_conflicts"
            or load_sha256 is not None
            or conflict_count != 0
        ):
            raise ValueError("base_game_only vfs_receipt contract is inconsistent")
        if any(item.get("source_id") not in {None, sources[0]["source_id"]} for item in assets):
            raise ValueError("base_game_only asset source_id is not declared by the receipt")
    elif scope == "resolved_overlay":
        if (
            len(sources) < 2
            or not any(source.get("source_kind") != "base_game" for source in sources)
            or policy != "later_enabled_source_wins_direct_path"
            or not isinstance(load_sha256, str)
            or not SHA256.fullmatch(load_sha256)
        ):
            raise ValueError("resolved_overlay vfs_receipt contract is inconsistent")
        for index, item in enumerate(assets):
            if not isinstance(item.get("source_id"), str) or item["source_id"] not in source_ids:
                raise ValueError(f"resolved_overlay assets[{index}] source_id is not declared")
    else:
        raise ValueError("vfs_receipt scope is unsupported")
    winner_rows = [
        "\0".join(
            (
                str(item["kind"]),
                str(item["name"]),
                str(item["asset_sha256"]),
                *([str(item["source_id"])] if scope == "resolved_overlay" else []),
                str(item["source_relative_path"]),
            )
        )
        for item in assets
    ]
    winner_set_sha256 = digest(("\n".join(winner_rows) + "\n").encode("utf-8"))
    if vfs_receipt.get("winner_set_sha256") != winner_set_sha256:
        raise ValueError("vfs_receipt winner_set_sha256 does not bind the asset inventory")
    native_evidence = vfs_receipt.get("native_precedence_evidence")
    if not isinstance(native_evidence, dict):
        raise ValueError("vfs_receipt native precedence evidence is missing")
    evidence_status = native_evidence.get("status")
    winner_rule = native_evidence.get("direct_path_winner_rule")
    if evidence_status not in {"not_applicable", "scoped_passed", "unverified"}:
        raise ValueError("vfs_receipt native evidence status is invalid")
    if winner_rule not in {"not_applicable", "later_enabled_source_wins", "unverified"}:
        raise ValueError("vfs_receipt native evidence winner rule is invalid")
    if evidence_status == "scoped_passed" and (
        not isinstance(native_evidence.get("evidence_id"), str)
        or not native_evidence["evidence_id"]
        or winner_rule != "later_enabled_source_wins"
    ):
        raise ValueError("scoped VFS native evidence is incomplete")
    if not isinstance(native_evidence.get("scope"), str) or not native_evidence["scope"]:
        raise ValueError("vfs_receipt native evidence scope is invalid")
    uncovered = native_evidence.get("uncovered")
    if (
        not isinstance(uncovered, list)
        or len(uncovered) > 32
        or any(not isinstance(item, str) or not item for item in uncovered)
    ):
        raise ValueError("vfs_receipt uncovered list is invalid")
    fit_index = manifest.get("fit_index")
    if not isinstance(fit_index, dict):
        raise ValueError("pack must contain a fit_index")
    if fit_index.get("schema") not in {"ck3-coa-fit-index-v1", "ck3-coa-fit-index-v2"} or fit_index.get("format") != "RGBA8":
        raise ValueError("unsupported fit_index schema/format")
    resolution = fit_index.get("resolution")
    indices = fit_index.get("asset_indices")
    if not isinstance(resolution, int) or not 8 <= resolution <= 128:
        raise ValueError("fit_index resolution is invalid")
    if not isinstance(indices, list) or not indices or len(set(indices)) != len(indices):
        raise ValueError("fit_index asset_indices are invalid")
    for index in indices:
        if not isinstance(index, int) or not 0 <= index < len(assets):
            raise ValueError("fit_index references an out-of-range asset")
        item = assets[index]
        if item.get("fit_eligible") is not True or item.get("kind") not in {"pattern", "colored_emblem"}:
            raise ValueError("fit_index references a non-fit asset")
    expected_fit_indices = {
        index for index, item in enumerate(assets)
        if item.get("registration") == "designer_manifest" and item.get("fit_eligible") is True
    }
    if set(indices) != expected_fit_indices:
        raise ValueError("fit_index does not exactly cover all fit-eligible registered assets")
    index_url = fit_index.get("url")
    index_sha = fit_index.get("asset_sha256")
    expected_index_bytes = len(indices) * resolution * resolution * 4
    if not isinstance(index_url, str) or not SAFE_INDEX_URL.fullmatch(index_url):
        raise ValueError("fit_index URL is not content addressed")
    if not isinstance(index_sha, str) or not SHA256.fullmatch(index_sha):
        raise ValueError("fit_index SHA-256 is invalid")
    index_relative = PurePosixPath(index_url)
    index_path = pack_directory.joinpath(*index_relative.parts).resolve()
    index_data = index_path.read_bytes()
    if fit_index.get("asset_bytes") != expected_index_bytes:
        raise ValueError("fit_index declared byte count is invalid")
    if len(index_data) != expected_index_bytes or digest(index_data) != index_sha:
        raise ValueError("fit_index bytes/hash mismatch")

    feature_data = b""
    features = fit_index.get("features")
    if fit_index.get("schema") == "ck3-coa-fit-index-v2":
        if not isinstance(features, dict):
            raise ValueError("fit_index v2 must declare features")
        if (
            features.get("schema") != "ck3-coa-shape-features-v1"
            or features.get("format") != "F64LE_SCALARS_F32LE_DESCRIPTOR"
            or features.get("scalar_fields") != list(FIT_SHAPE_SCALAR_FIELDS)
            or features.get("descriptor_size") != FIT_SHAPE_DESCRIPTOR_SIZE
            or features.get("header_bytes") != FIT_FEATURE_HEADER_BYTES
            or features.get("record_bytes") != FIT_FEATURE_RECORD_BYTES
        ):
            raise ValueError("fit_index feature contract is invalid")
        feature_url = features.get("url")
        feature_sha = features.get("asset_sha256")
        expected_feature_bytes = FIT_FEATURE_HEADER_BYTES + len(indices) * FIT_FEATURE_RECORD_BYTES
        if not isinstance(feature_url, str) or not SAFE_FEATURE_URL.fullmatch(feature_url):
            raise ValueError("fit feature URL is not content addressed")
        if not isinstance(feature_sha, str) or not SHA256.fullmatch(feature_sha):
            raise ValueError("fit feature SHA-256 is invalid")
        feature_relative = PurePosixPath(feature_url)
        feature_path = pack_directory.joinpath(*feature_relative.parts).resolve()
        feature_data = feature_path.read_bytes()
        if features.get("asset_bytes") != expected_feature_bytes:
            raise ValueError("fit feature declared byte count is invalid")
        if len(feature_data) != expected_feature_bytes or digest(feature_data) != feature_sha:
            raise ValueError("fit feature bytes/hash mismatch")
        header = struct.unpack_from("<8s6I", feature_data)
        if header != (
            b"CK3FIT2\0", 2, len(indices), resolution, FIT_SHAPE_DESCRIPTOR_SIZE,
            len(FIT_SHAPE_SCALAR_FIELDS), FIT_FEATURE_RECORD_BYTES,
        ):
            raise ValueError("fit feature header does not match manifest")
        for record_index in range(len(indices)):
            record_offset = FIT_FEATURE_HEADER_BYTES + record_index * FIT_FEATURE_RECORD_BYTES
            scalars = struct.unpack_from(
                f"<{len(FIT_SHAPE_SCALAR_FIELDS)}d", feature_data, record_offset
            )
            descriptor = struct.unpack_from(
                f"<{FIT_SHAPE_DESCRIPTOR_SIZE * FIT_SHAPE_DESCRIPTOR_SIZE}f",
                feature_data,
                record_offset + len(FIT_SHAPE_SCALAR_FIELDS) * 8,
            )
            if any(not math.isfinite(value) or not 0 <= value <= 1 for value in (*scalars, *descriptor)):
                raise ValueError(f"fit feature record {record_index} contains an invalid value")
            if scalars[0] > scalars[2] or scalars[1] > scalars[3]:
                raise ValueError(f"fit feature record {record_index} has inverted bounds")
    elif features is not None:
        raise ValueError("fit_index v1 must not declare v2 features")

    inventory = manifest.get("inventory")
    if not isinstance(inventory, dict):
        raise ValueError("pack must contain an inventory")
    expected_inventory = {
        "registered_patterns": totals["pattern"],
        "registered_colored_emblems": totals["colored_emblem"],
        "auxiliary_colored_emblems": totals["auxiliary_colored_emblem"],
        "textured_emblems": totals["textured_emblem"],
        "surface_masks": totals["surface_mask"],
        "fit_eligible_registered": len(expected_fit_indices),
    }
    for name, expected in expected_inventory.items():
        if inventory.get(name) != expected:
            raise ValueError(f"inventory {name} does not match assets")
    if inventory.get("complete_raw_tree") is True and inventory.get("source_dds_total") != len(assets):
        raise ValueError("complete inventory source_dds_total does not match assets")
    return {
        "schema": "ck3-coa-web-asset-pack-verification-v1",
        "status": "green",
        "pack_directory": str(pack_directory),
        "pack_id": manifest.get("pack_id"),
        "ck3_build": manifest.get("ck3_build"),
        "manifest_bytes": len(manifest_bytes),
        "manifest_sha256": digest(manifest_bytes),
        "assets": len(assets),
        "asset_bytes": total_bytes,
        "fit_index_entries": len(indices),
        "fit_index_bytes": len(index_data),
        "fit_index_schema": fit_index.get("schema"),
        "fit_feature_bytes": len(feature_data),
        "complete_raw_tree": inventory.get("complete_raw_tree"),
        "source_dds_total": inventory.get("source_dds_total"),
        "vfs_scope": scope,
        "vfs_sources": len(sources),
        "vfs_conflicts": conflict_count,
        "vfs_winner_set_sha256": winner_set_sha256,
        "vfs_native_evidence": evidence_status,
        **totals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_directory", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.pack_directory), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
