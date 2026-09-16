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
