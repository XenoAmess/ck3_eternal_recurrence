#!/usr/bin/env python3
"""Build a complete, content-addressed CoA web pack from an explicit CK3 root.

The repository owner explicitly authorized versioning and GitHub Pages distribution
of the original DDS material for this project on 2026-09-15.  The generated pack
keeps designer-registered resources distinct from unregistered auxiliary files and
adds a compact RGBA fit index so a browser can search the full registered library
without downloading and decoding every full-resolution DDS first.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import struct
import sys

from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTOPLAYER_SOURCE = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(AUTOPLAYER_SOURCE))

from xar_autoplayer.coat_of_arms_resources import (  # noqa: E402
    query_coat_of_arms_resource_catalog_v1,
    read_coat_of_arms_render_support_v1,
)


FIT_INDEX_RESOLUTION = 32
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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _winner_set_sha256(assets: list[dict[str, object]]) -> str:
    rows = [
        "\0".join(
            (
                str(item["kind"]),
                str(item["name"]),
                str(item["asset_sha256"]),
                str(item["source_relative_path"]),
            )
        )
        for item in assets
    ]
    return _sha256(("\n".join(rows) + "\n").encode("utf-8"))


def _catalog_items(game_root: Path, kind: str, include_hidden: bool) -> tuple[list[dict[str, object]], dict[str, object]]:
    items: list[dict[str, object]] = []
    offset = 0
    provenance: dict[str, object] | None = None
    while True:
        page = query_coat_of_arms_resource_catalog_v1(
            str(game_root), kind, visible_only=not include_hidden, offset=offset, limit=200
        )
        if provenance is None:
            provenance = dict(page["provenance"])
        items.extend(page["items"])
        next_offset = page["next_offset"]
        if next_offset is None:
            break
        offset = int(next_offset)
    if provenance is None:
        raise RuntimeError(f"empty catalog response for {kind}")
    return items, provenance


def _write_content_addressed(
    asset_directory: Path, data: bytes, extension: str = ".dds"
) -> tuple[str, str]:
    digest = _sha256(data)
    name = f"{digest.lower()}{extension}"
    destination = asset_directory / name
    if destination.exists():
        if destination.read_bytes() != data:
            raise RuntimeError(f"content-address collision at {destination}")
    else:
        destination.write_bytes(data)
    return f"assets/{name}", digest


def _dds_metadata(data: bytes) -> dict[str, object]:
    if len(data) < 128 or data[:4] != b"DDS " or int.from_bytes(data[4:8], "little") != 124:
        raise RuntimeError("asset is not a supported DDS container")
    four_cc = data[84:88]
    if four_cc in (b"DXT1", b"DXT5"):
        format_name = four_cc.decode("ascii")
    elif (
        four_cc == b"\0\0\0\0"
        and int.from_bytes(data[88:92], "little") == 32
        and int.from_bytes(data[92:96], "little") == 0x00FF0000
        and int.from_bytes(data[96:100], "little") == 0x0000FF00
        and int.from_bytes(data[100:104], "little") == 0x000000FF
        and int.from_bytes(data[104:108], "little") == 0xFF000000
    ):
        format_name = "BGRA8"
    else:
        raise RuntimeError("asset DDS format is outside the browser decoder contract")
    return {
        "width": int.from_bytes(data[16:20], "little"),
        "height": int.from_bytes(data[12:16], "little"),
        "format": format_name,
    }


def _entry_from_catalog(
    game_root: Path,
    asset_directory: Path,
    kind: str,
    item: dict[str, object],
) -> dict[str, object]:
    source = game_root / str(item["relative_path"])
    data = source.read_bytes()
    relative_url, digest = _write_content_addressed(asset_directory, data)
    if len(data) != int(item["asset_bytes"]) or digest != str(item["asset_sha256"]):
        raise RuntimeError(f"asset identity mismatch for {item['name']}")
    name = str(item["name"])
    return {
        "kind": kind,
        "name": name,
        "colors": int(item["colors"]),
        "visible": bool(item["visible"]),
        "category": item["category"],
        "url": relative_url,
        "asset_bytes": len(data),
        "asset_sha256": digest,
        "dds": _dds_metadata(data),
        "source_relative_path": Path(str(item["relative_path"])).as_posix(),
        "registration": "designer_manifest",
        # The exact native clipboard reader rejects high UTF-8 bytes. Keep every
        # registered asset in inventory/UI, but never auto-generate unpasteable code.
        "fit_eligible": name.isascii() and name.isprintable(),
    }


def _entry_from_path(
    game_root: Path,
    asset_directory: Path,
    kind: str,
    source: Path,
    *,
    colors: int,
    category: str,
    registration: str,
) -> dict[str, object]:
    data = source.read_bytes()
    relative_url, digest = _write_content_addressed(asset_directory, data)
    return {
        "kind": kind,
        "name": source.name,
        "colors": colors,
        "visible": False,
        "category": category,
        "url": relative_url,
        "asset_bytes": len(data),
        "asset_sha256": digest,
        "dds": _dds_metadata(data),
        "source_relative_path": source.relative_to(game_root).as_posix(),
        "registration": registration,
        "fit_eligible": False,
    }


def _shape_feature_record(encoded: bytes) -> bytes:
    pixel_count = FIT_INDEX_RESOLUTION * FIT_INDEX_RESOLUTION
    intensity: list[float] = []
    alpha_energy = 0.0
    color_energy = 0.0
    channel_sums = [0.0, 0.0, 0.0]
    for index in range(pixel_count):
        offset = index * 4
        red, green, blue, alpha_byte = encoded[offset:offset + 4]
        alpha = alpha_byte / 255
        channels = (red / 255, green / 255, blue / 255)
        value = alpha * max(channels)
        intensity.append(value)
        color_energy += value
        alpha_energy += alpha
        for channel_index, channel in enumerate(channels):
            channel_sums[channel_index] += alpha * channel
    if color_energy < alpha_energy * 0.05:
        intensity = [encoded[index * 4 + 3] / 255 for index in range(pixel_count)]

    minimum_x = FIT_INDEX_RESOLUTION
    minimum_y = FIT_INDEX_RESOLUTION
    maximum_x = -1
    maximum_y = -1
    weighted_x = 0.0
    weighted_y = 0.0
    total_weight = 0.0
    for y in range(FIT_INDEX_RESOLUTION):
        for x in range(FIT_INDEX_RESOLUTION):
            weight = intensity[y * FIT_INDEX_RESOLUTION + x]
            if weight < 0.04:
                continue
            minimum_x = min(minimum_x, x)
            minimum_y = min(minimum_y, y)
            maximum_x = max(maximum_x, x)
            maximum_y = max(maximum_y, y)
            weighted_x += (x + 0.5) * weight
            weighted_y += (y + 0.5) * weight
            total_weight += weight

    contour_sum = 0.0
    contour_samples = 0
    for y in range(FIT_INDEX_RESOLUTION):
        for x in range(FIT_INDEX_RESOLUTION):
            value = intensity[y * FIT_INDEX_RESOLUTION + x]
            if x + 1 < FIT_INDEX_RESOLUTION:
                contour_sum += abs(value - intensity[y * FIT_INDEX_RESOLUTION + x + 1])
                contour_samples += 1
            if y + 1 < FIT_INDEX_RESOLUTION:
                contour_sum += abs(value - intensity[(y + 1) * FIT_INDEX_RESOLUTION + x])
                contour_samples += 1

    if maximum_x < minimum_x or maximum_y < minimum_y:
        bounds = (0.0, 0.0, 1.0, 1.0)
        center = (0.5, 0.5)
        span = (1.0, 1.0)
        descriptor = [0.0] * (FIT_SHAPE_DESCRIPTOR_SIZE * FIT_SHAPE_DESCRIPTOR_SIZE)
    else:
        span_x = max(1, maximum_x - minimum_x + 1)
        span_y = max(1, maximum_y - minimum_y + 1)
        bounds = (
            minimum_x / FIT_INDEX_RESOLUTION,
            minimum_y / FIT_INDEX_RESOLUTION,
            (maximum_x + 1) / FIT_INDEX_RESOLUTION,
            (maximum_y + 1) / FIT_INDEX_RESOLUTION,
        )
        center = (
            weighted_x / total_weight / FIT_INDEX_RESOLUTION if total_weight > 0 else 0.5,
            weighted_y / total_weight / FIT_INDEX_RESOLUTION if total_weight > 0 else 0.5,
        )
        span = (span_x / FIT_INDEX_RESOLUTION, span_y / FIT_INDEX_RESOLUTION)
        descriptor = []
        for y in range(FIT_SHAPE_DESCRIPTOR_SIZE):
            source_y = min(maximum_y, max(
                minimum_y,
                int(minimum_y + (y + 0.5) * span_y / FIT_SHAPE_DESCRIPTOR_SIZE),
            ))
            for x in range(FIT_SHAPE_DESCRIPTOR_SIZE):
                source_x = min(maximum_x, max(
                    minimum_x,
                    int(minimum_x + (x + 0.5) * span_x / FIT_SHAPE_DESCRIPTOR_SIZE),
                ))
                descriptor.append(intensity[source_y * FIT_INDEX_RESOLUTION + source_x])

    scalars = (
        *bounds,
        *center,
        *span,
        alpha_energy / pixel_count,
        *(value / pixel_count for value in channel_sums),
        contour_sum / contour_samples if contour_samples else 0.0,
    )
    record = struct.pack(f"<{len(scalars)}d", *scalars) + struct.pack(
        f"<{len(descriptor)}f", *descriptor
    )
    if len(record) != FIT_FEATURE_RECORD_BYTES:
        raise RuntimeError("fit feature record size mismatch")
    return record


def _fit_index_bytes(
    game_root: Path, assets: list[dict[str, object]]
) -> tuple[bytes, bytes, list[int]]:
    output = bytearray()
    features = bytearray()
    asset_indices: list[int] = []
    for index, item in enumerate(assets):
        if item.get("fit_eligible") is not True:
            continue
        source = game_root / str(item["source_relative_path"])
        with Image.open(BytesIO(source.read_bytes())) as image:
            rgba = image.convert("RGBA").resize(
                (FIT_INDEX_RESOLUTION, FIT_INDEX_RESOLUTION), Image.Resampling.LANCZOS
            )
            encoded = rgba.tobytes("raw", "RGBA")
        expected = FIT_INDEX_RESOLUTION * FIT_INDEX_RESOLUTION * 4
        if len(encoded) != expected:
            raise RuntimeError(f"fit index record size mismatch for {item['name']}")
        output.extend(encoded)
        features.extend(_shape_feature_record(encoded))
        asset_indices.append(index)
    header = struct.pack(
        "<8s6I",
        b"CK3FIT2\0",
        2,
        len(asset_indices),
        FIT_INDEX_RESOLUTION,
        FIT_SHAPE_DESCRIPTOR_SIZE,
        len(FIT_SHAPE_SCALAR_FIELDS),
        FIT_FEATURE_RECORD_BYTES,
    )
    if len(header) != FIT_FEATURE_HEADER_BYTES:
        raise RuntimeError("fit feature header size mismatch")
    return bytes(output), header + bytes(features), asset_indices


def build_pack(game_root: Path, output: Path, emblem_limit: int, include_hidden: bool) -> dict[str, object]:
    game_root = game_root.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    temporary = output.with_name(f".{output.name}.building-{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"temporary output already exists: {temporary}")
    asset_directory = temporary / "assets"
    asset_directory.mkdir(parents=True)
    try:
        patterns, pattern_provenance = _catalog_items(game_root, "pattern", include_hidden)
        emblems, emblem_provenance = _catalog_items(game_root, "colored_emblem", include_hidden)
        selected_emblems = emblems if emblem_limit == 0 else emblems[:emblem_limit]
        assets: list[dict[str, object]] = []
        for kind, items in (("pattern", patterns), ("colored_emblem", selected_emblems)):
            for item in items:
                if item["asset_exists"] is not True:
                    raise RuntimeError(f"manifest asset is missing: {item['name']}")
                assets.append(_entry_from_catalog(game_root, asset_directory, kind, item))

        registered_colored_paths = {
            Path(str(item["relative_path"])).as_posix().casefold() for item in emblems
        }
        colored_root = game_root / "game" / "gfx" / "coat_of_arms" / "colored_emblems"
        auxiliary_colored_paths = sorted(
            (
                path for path in colored_root.rglob("*.dds")
                if path.relative_to(game_root).as_posix().casefold() not in registered_colored_paths
            ),
            key=lambda path: path.relative_to(game_root).as_posix().casefold(),
        )
        for path in auxiliary_colored_paths:
            assets.append(_entry_from_path(
                game_root, asset_directory, "auxiliary_colored_emblem", path,
                colors=3, category="unregistered-auxiliary", registration="unregistered_file",
            ))

        textured_root = game_root / "game" / "gfx" / "coat_of_arms" / "textured_emblems"
        textured_paths = sorted(
            textured_root.rglob("*.dds"),
            key=lambda path: path.relative_to(game_root).as_posix().casefold(),
        )
        for path in textured_paths:
            assets.append(_entry_from_path(
                game_root, asset_directory, "textured_emblem", path,
                colors=0, category="render-support", registration="render_support",
            ))

        render_support = read_coat_of_arms_render_support_v1(str(game_root))
        mask = dict(render_support["surface_mask"])
        mask_data = base64.b64decode(str(mask["asset_base64"]), validate=True)
        mask_url, mask_sha = _write_content_addressed(asset_directory, mask_data)
        mask_dds = dict(mask["dds"])
        assets.append(
            {
                "kind": "surface_mask",
                "name": Path(str(mask["relative_path"])).name,
                "colors": 0,
                "visible": False,
                "category": "render-support",
                "url": mask_url,
                "asset_bytes": len(mask_data),
                "asset_sha256": mask_sha,
                "dds": {
                    "width": int(mask_dds["width"]),
                    "height": int(mask_dds["height"]),
                    "format": str(mask_dds["format"]),
                },
                "source_relative_path": Path(str(mask["relative_path"])).as_posix(),
                "registration": "render_support",
                "fit_eligible": False,
            }
        )
        fit_bytes, fit_feature_bytes, fit_asset_indices = _fit_index_bytes(game_root, assets)
        fit_url, fit_sha = _write_content_addressed(asset_directory, fit_bytes, ".rgba")
        fit_feature_url, fit_feature_sha = _write_content_addressed(
            asset_directory, fit_feature_bytes, ".fit"
        )

        coa_root = game_root / "game" / "gfx" / "coat_of_arms"
        source_dds_paths = {
            path.relative_to(game_root).as_posix().casefold() for path in coa_root.rglob("*.dds")
        }
        included_dds_paths = {
            str(item["source_relative_path"]).casefold() for item in assets
        }
        complete_raw_tree = emblem_limit == 0 and include_hidden
        if complete_raw_tree and source_dds_paths != included_dds_paths:
            missing = sorted(source_dds_paths - included_dds_paths)
            extra = sorted(included_dds_paths - source_dds_paths)
            raise RuntimeError(f"raw CoA DDS coverage mismatch: missing={missing}, extra={extra}")
        source_identity = {
            "pattern_manifest_sha256": pattern_provenance["manifest_sha256"],
            "emblem_manifest_sha256": emblem_provenance["manifest_sha256"],
            "render_provenance": render_support["provenance"],
        }
        source_bytes = json.dumps(
            source_identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        source_manifest_sha256 = _sha256(source_bytes)
        named_colors = {
            str(item["name"]): [float(value) for value in item["rgb"]]
            for item in render_support["named_colors"]
        }
        build = str(render_support["ck3_build"])
        manifest = {
            "schema": "ck3-coa-web-asset-pack-v1",
            "schema_version": 1,
            "pack_id": (
                f"ck3-{build}-base-complete-{len(patterns)}p-{len(selected_emblems)}e-"
                f"{len(auxiliary_colored_paths)}aux"
                if complete_raw_tree else
                f"ck3-{build}-base-partial-{len(patterns)}p-{len(selected_emblems)}e"
            ),
            "ck3_build": build,
            "source_manifest_sha256": source_manifest_sha256,
            "named_colors": named_colors,
            "assets": assets,
            "fit_index": {
                "schema": "ck3-coa-fit-index-v2",
                "format": "RGBA8",
                "resolution": FIT_INDEX_RESOLUTION,
                "asset_indices": fit_asset_indices,
                "url": fit_url,
                "asset_bytes": len(fit_bytes),
                "asset_sha256": fit_sha,
                "features": {
                    "schema": "ck3-coa-shape-features-v1",
                    "format": "F64LE_SCALARS_F32LE_DESCRIPTOR",
                    "scalar_fields": list(FIT_SHAPE_SCALAR_FIELDS),
                    "descriptor_size": FIT_SHAPE_DESCRIPTOR_SIZE,
                    "header_bytes": FIT_FEATURE_HEADER_BYTES,
                    "record_bytes": FIT_FEATURE_RECORD_BYTES,
                    "url": fit_feature_url,
                    "asset_bytes": len(fit_feature_bytes),
                    "asset_sha256": fit_feature_sha,
                },
            },
            "inventory": {
                "complete_raw_tree": complete_raw_tree,
                "source_dds_total": len(source_dds_paths),
                "registered_patterns": len(patterns),
                "registered_colored_emblems": len(selected_emblems),
                "auxiliary_colored_emblems": len(auxiliary_colored_paths),
                "textured_emblems": len(textured_paths),
                "surface_masks": 1,
                "fit_eligible_registered": len(fit_asset_indices),
            },
            "vfs_receipt": {
                "schema": "ck3-coa-vfs-receipt-v1",
                "scope": "base_game_only",
                "resolution_policy": "single_source_no_conflicts",
                "load_configuration_sha256": None,
                "winner_set_sha256": _winner_set_sha256(assets),
                "resolved_asset_count": len(assets),
                "conflict_count": 0,
                "sources": [
                    {
                        "source_id": f"ck3-base-{build}",
                        "source_kind": "base_game",
                        "precedence_order": 0,
                        "source_identity_sha256": source_manifest_sha256,
                    }
                ],
                "native_precedence_evidence": {
                    "status": "scoped_passed",
                    "evidence_id": "vfs-winner-native-r22",
                    "direct_path_winner_rule": "later_enabled_source_wins",
                    "scope": "two enabled directory mods with one conflicting registered direct DDS path",
                    "uncovered": [
                        "base game versus mod precedence",
                        "DLC mount precedence",
                        "archive mod precedence",
                        "replace_path semantics",
                        "definition merge semantics",
                    ],
                },
            },
        }
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8")
        (temporary / "manifest.json").write_bytes(manifest_bytes)
        (temporary / "manifest.sha256").write_bytes(
            f"{_sha256(manifest_bytes)}  manifest.json\n".encode("ascii")
        )
        (temporary / "NOTICE.txt").write_text(
            "Generated from an explicit CK3 installation. The project owner confirmed this "
            "original DDS material as authorized for versioning and this repository's GitHub "
            "Pages deployment on 2026-09-15. This project-policy record does not transfer "
            "ownership of Paradox assets. The web application does not require CK3 at runtime.\n",
            encoding="utf-8",
        )
        temporary.rename(output)
        return {
            "output": str(output),
            "manifest_sha256": _sha256(manifest_bytes),
            "patterns": len(patterns),
            "colored_emblems": len(selected_emblems),
            "auxiliary_colored_emblems": len(auxiliary_colored_paths),
            "textured_emblems": len(textured_paths),
            "source_dds_total": len(source_dds_paths),
            "complete_raw_tree": complete_raw_tree,
            "fit_index_entries": len(fit_asset_indices),
            "fit_index_bytes": len(fit_bytes),
            "fit_feature_bytes": len(fit_feature_bytes),
            "unique_dds": len(list((output / "assets").glob("*.dds"))),
            "asset_bytes": sum(path.stat().st_size for path in (output / "assets").glob("*.dds")),
        }
    except BaseException as error:
        raise RuntimeError(f"asset pack build failed; partial files preserved at {temporary}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--emblem-limit", type=int, default=0,
        help="number of source-ordered emblems; 0 includes all (default: 0)",
    )
    parser.add_argument(
        "--include-hidden", action=argparse.BooleanOptionalAction, default=True,
        help="include hidden designer-manifest entries (default: true)",
    )
    arguments = parser.parse_args()
    if arguments.emblem_limit < 0 or arguments.emblem_limit > 4096:
        parser.error("--emblem-limit must be 0..4096")
    receipt = build_pack(
        arguments.game_root, arguments.output, arguments.emblem_limit, arguments.include_hidden
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
