#!/usr/bin/env python3
"""Verify a ck3-coa-web-asset-pack-v1 directory without reading or launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


SHA256 = re.compile(r"^[0-9A-F]{64}$")
SAFE_URL = re.compile(r"^assets/[0-9a-f]{64}\.dds$")


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
    totals = {"pattern": 0, "colored_emblem": 0, "surface_mask": 0}
    total_bytes = 0
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

