#!/usr/bin/env python3
"""Materialize hash-bound, diagnostic-only B1 startup bisect projections.

The pre-split B1 runtime file is generated and must not be edited for loader
experiments.  This historical helper consumes a frozen source tree containing
the exact 495,777-byte monolith; it does not accept the later canonical
two-file generator output.  It copies the exact 55-file safe-core product,
adds the original B1 event and Simplified Chinese localization files, and
replaces only selected *complete top-level* B1 effect bodies with no-op
definitions.  Every definition remains present, so a candidate can isolate
loader cost without introducing unknown scripted-effect names.

The output is disposable evidence.  A stubbed candidate can prove only a CK3
startup/load boundary; it can never certify B1 gameplay semantics or serve as
a release tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Iterable

from phase2_workforce_block_segments import find_blocks, parse_ranges, scan_line
from zg361_phase2_product_projection import (
    load_projection,
    materialize_projection,
    write_manifest,
)


EXPECTED_EFFECT_SHA256 = (
    "cdb388005ffeac6d332380e910fbbf929f49871047e118d047c63b8751c001b4"
)
EXPECTED_EVENT_SHA256 = (
    "6576ea63f654d2321620a026471390f147b90719d98f69feea34f4c5779e8543"
)
EXPECTED_LOC_SHA256 = (
    "00320692c35e9ed6ddb0d02f9d1d988876f22aa72b966a3247efd87f9adac938"
)

EFFECT_RELATIVE = Path(
    "common/scripted_effects/zg361_b1_runtime_effects.txt"
)
SPLIT_EFFECT_RELATIVE = Path(
    "common/scripted_effects/zg361_b1_runtime_effects_part2.txt"
)
EVENT_RELATIVE = Path("events/zg361_b1_runtime_events.txt")
LOC_RELATIVE = Path(
    "localization/simp_chinese/zg361_b1_l_simp_chinese.yml"
)
SCRIPT_DIRS = (
    Path("common/scripted_effects"),
    Path("common/scripted_triggers"),
    Path("common/script_values"),
)
CALL_RE = re.compile(
    r"\b(zg361_[A-Za-z0-9_]+_(?:effect|trigger|value))\s*="
)
EVENT_ID_RE = re.compile(r"\b(zg361b1\.\d+)\b")
LOC_DEF_RE = re.compile(r'^\s+([A-Za-z0-9_.-]+):(?:\d+)?\s+"', re.MULTILINE)
LOC_REF_RE = re.compile(
    r"^\s*(?:title|desc|name)\s*=\s*([A-Za-z0-9_.-]+)\s*$",
    re.MULTILINE,
)


class B1BisectError(ValueError):
    """The requested diagnostic projection is invalid or not reproducible."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def balanced_cut(blocks: list[dict[str, object]]) -> int:
    """Return the first index in the byte-balanced right arm."""

    if len(blocks) < 2:
        raise B1BisectError("at least two blocks are required for a half split")
    total = sum(int(block["bytes"]) for block in blocks)
    return min(
        range(1, len(blocks)),
        key=lambda index: abs(
            sum(int(block["bytes"]) for block in blocks[:index]) - total / 2
        ),
    )


def real_indices_for_mode(
    mode: str,
    blocks: list[dict[str, object]],
    ranges: str | None = None,
) -> list[int]:
    count = len(blocks)
    cut = balanced_cut(blocks)
    if mode == "all-stub":
        if ranges:
            raise B1BisectError("--real-ranges is valid only with --mode ranges")
        return []
    if mode == "left-real":
        if ranges:
            raise B1BisectError("--real-ranges is valid only with --mode ranges")
        return list(range(cut))
    if mode == "right-real":
        if ranges:
            raise B1BisectError("--real-ranges is valid only with --mode ranges")
        return list(range(cut, count))
    if mode == "ranges":
        if not ranges:
            raise B1BisectError("--mode ranges requires --real-ranges")
        return parse_ranges(ranges, count)
    if mode == "balanced-files":
        if ranges:
            raise B1BisectError("--real-ranges is valid only with --mode ranges")
        return list(range(count))
    raise B1BisectError(f"unsupported mode: {mode}")


def render_balanced_file_split(
    source: bytes,
) -> tuple[list[tuple[Path, bytes]], list[dict[str, object]]]:
    """Move the balanced right arm to a second file without changing bodies."""

    _header, blocks = find_blocks(source)
    cut = balanced_cut(blocks)
    cut_byte = int(blocks[cut]["start_byte"])
    first = source[:cut_byte]
    second = (
        b"\xef\xbb\xbf# DIAGNOSTIC FILE SPLIT - original generated bodies unchanged\r\n"
        + source[cut_byte:]
    )
    rows = [
        {
            **block,
            "body_mode": "real",
            "output_part": 1 if int(block["index"]) < cut else 2,
        }
        for block in blocks
    ]
    return [(EFFECT_RELATIVE, first), (SPLIT_EFFECT_RELATIVE, second)], rows


def render_effect_variant(
    source: bytes,
    real_indices: Iterable[int],
) -> tuple[bytes, list[dict[str, object]]]:
    """Replace non-selected complete blocks in-place with ``name = {}``."""

    _header, blocks = find_blocks(source)
    selected = set(real_indices)
    expected = set(range(len(blocks)))
    invalid = sorted(selected - expected)
    if invalid:
        raise B1BisectError(f"real block indices outside 0..{len(blocks) - 1}: {invalid}")
    output = source
    rows: list[dict[str, object]] = []
    for block in blocks:
        index = int(block["index"])
        rows.append(
            {
                **block,
                "body_mode": "real" if index in selected else "stub",
            }
        )
    # Work from the final byte offset backwards so earlier offsets stay exact.
    for block in reversed(blocks):
        index = int(block["index"])
        if index in selected:
            continue
        start = int(block["start_byte"])
        end = int(block["end_byte"])
        original = output[start:end]
        newline = (
            b"\r\n"
            if original.endswith(b"\r\n")
            else b"\n"
            if original.endswith(b"\n")
            else b""
        )
        replacement = f'{block["name"]} = {{}}'.encode("utf-8") + newline
        output = output[:start] + replacement + output[end:]
    return output, rows


def brace_balance(path: Path) -> tuple[int, bool]:
    text = path.read_text(encoding="utf-8-sig")
    depth = 0
    in_quote = False
    for line in text.splitlines(keepends=True):
        delta, in_quote = scan_line(line, in_quote)
        depth += delta
        if depth < 0:
            return depth, in_quote
    return depth, in_quote


def top_level_script_definitions(product: Path) -> set[str]:
    definitions: set[str] = set()
    for relative in SCRIPT_DIRS:
        root = product / relative
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.txt")):
            try:
                _header, blocks = find_blocks(path.read_bytes())
            except ValueError as error:
                raise B1BisectError(f"cannot scan top-level definitions in {path}: {error}") from error
            definitions.update(str(block["name"]) for block in blocks)
    return definitions


def selected_text_files(product: Path) -> list[Path]:
    suffixes = {".txt", ".gui", ".yml"}
    return sorted(
        path for path in product.rglob("*") if path.is_file() and path.suffix in suffixes
    )


def tree_rows(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def file_list_sha256(rows: Iterable[dict[str, object]]) -> str:
    payload = "\n".join(str(row["path"]) for row in rows) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def materialize(
    *,
    baseline: Path,
    b1_source: Path,
    output: Path,
    projection_name: str,
    mode: str,
    real_ranges: str | None,
) -> dict[str, Any]:
    baseline = baseline.resolve()
    b1_source = b1_source.resolve()
    output = output.resolve()
    if not baseline.is_dir():
        raise B1BisectError(f"safe-core baseline is missing: {baseline}")
    if not b1_source.is_dir():
        raise B1BisectError(f"B1 source root is missing: {b1_source}")
    if output.exists():
        raise B1BisectError(f"output already exists; use a new attempt path: {output}")
    for required in (EFFECT_RELATIVE, EVENT_RELATIVE, LOC_RELATIVE):
        if not (b1_source / required).is_file():
            raise B1BisectError(f"B1 source is missing: {required.as_posix()}")

    original_effect = (b1_source / EFFECT_RELATIVE).read_bytes()
    original_event = (b1_source / EVENT_RELATIVE).read_bytes()
    original_loc = (b1_source / LOC_RELATIVE).read_bytes()
    observed_inputs = {
        EFFECT_RELATIVE.as_posix(): sha256_bytes(original_effect),
        EVENT_RELATIVE.as_posix(): sha256_bytes(original_event),
        LOC_RELATIVE.as_posix(): sha256_bytes(original_loc),
    }
    expected_inputs = {
        EFFECT_RELATIVE.as_posix(): EXPECTED_EFFECT_SHA256,
        EVENT_RELATIVE.as_posix(): EXPECTED_EVENT_SHA256,
        LOC_RELATIVE.as_posix(): EXPECTED_LOC_SHA256,
    }
    if observed_inputs != expected_inputs:
        raise B1BisectError(
            f"B1 input identity changed: observed={observed_inputs}, expected={expected_inputs}"
        )

    _header, original_blocks = find_blocks(original_effect)
    real_indices = real_indices_for_mode(mode, original_blocks, real_ranges)
    if mode == "balanced-files":
        rendered_effect_parts, block_rows = render_balanced_file_split(original_effect)
    else:
        rendered_effect, block_rows = render_effect_variant(original_effect, real_indices)
        rendered_effect_parts = [(EFFECT_RELATIVE, rendered_effect)]

    source_root = output / "source"
    shutil.copytree(baseline, source_root)
    increment_files = [
        *rendered_effect_parts,
        (EVENT_RELATIVE, original_event),
        (LOC_RELATIVE, original_loc),
    ]
    for relative, data in increment_files:
        target = source_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    projection_path = output / "projection.json"
    manifest = write_manifest(
        source_root,
        projection_path,
        projection_name=projection_name,
    )
    # Loading first proves the just-written contract before either copy.
    load_projection(
        source_root,
        projection_name=projection_name,
        manifest_path=projection_path,
    )
    product_root = output / "product"
    receipt = materialize_projection(
        source_root,
        product_root,
        projection_name=projection_name,
        manifest_path=projection_path,
    )
    replay_root = output / "materialized-check"
    replay = materialize_projection(
        source_root,
        replay_root,
        projection_name=projection_name,
        manifest_path=projection_path,
    )
    write_json(output / "materialization.json", receipt)
    write_json(output / "materialization-replay.json", replay)

    materialized_effects = [
        (relative, product_root / relative, data)
        for relative, data in rendered_effect_parts
    ]
    rendered_blocks: list[dict[str, object]] = []
    for _relative, path, _data in materialized_effects:
        _rendered_header, part_blocks = find_blocks(path.read_bytes())
        rendered_blocks.extend(part_blocks)
    original_names = [str(row["name"]) for row in original_blocks]
    rendered_names = [str(row["name"]) for row in rendered_blocks]
    definitions = top_level_script_definitions(product_root)
    changed_text = "\n".join(
        [
            *(path.read_text(encoding="utf-8-sig") for _, path, _ in materialized_effects),
            (product_root / EVENT_RELATIVE).read_text(encoding="utf-8-sig"),
        ]
    )
    custom_calls = sorted(set(CALL_RE.findall(changed_text)))
    missing_calls = sorted(set(custom_calls) - definitions)

    event_path = product_root / EVENT_RELATIVE
    event_bytes = event_path.read_bytes()
    event_text = event_bytes.decode("utf-8-sig")
    _event_header, event_blocks = find_blocks(event_bytes)
    event_definitions = sorted(
        str(block["name"])
        for block in event_blocks
        if str(block["name"]).startswith("zg361b1.")
    )
    event_ids = sorted(set(EVENT_ID_RE.findall(changed_text)))
    missing_events = sorted(set(event_ids) - set(event_definitions))
    loc_text = (product_root / LOC_RELATIVE).read_text(encoding="utf-8-sig")
    loc_definitions = set(LOC_DEF_RE.findall(loc_text))
    loc_references = sorted(set(LOC_REF_RE.findall(event_text)))
    # Event option/title/description localization shares the event namespace.
    # A bare ``name = zg361_b1_*`` inside an effect is a variable name, not loc.
    b1_loc_references = [key for key in loc_references if key.startswith("zg361b1.")]
    missing_loc = sorted(set(b1_loc_references) - loc_definitions)

    text_files = selected_text_files(product_root)
    bom_missing = [
        path.relative_to(product_root).as_posix()
        for path in text_files
        if not path.read_bytes().startswith(b"\xef\xbb\xbf")
    ]
    unbalanced = []
    for path in text_files:
        if path.suffix == ".yml":
            continue
        depth, quoted = brace_balance(path)
        if depth != 0 or quoted:
            unbalanced.append(
                {
                    "path": path.relative_to(product_root).as_posix(),
                    "depth": depth,
                    "unterminated_quote": quoted,
                }
            )

    source_rows = tree_rows(source_root)
    product_rows = tree_rows(product_root)
    replay_rows = tree_rows(replay_root)
    checks = {
        "projection_replay": {
            "status": "GREEN" if source_rows == product_rows == replay_rows else "RED",
            "source_equals_product": source_rows == product_rows,
            "source_equals_replay": source_rows == replay_rows,
        },
        "effect_definition_surface": {
            "status": "GREEN" if original_names == rendered_names else "RED",
            "expected_count": len(original_names),
            "observed_count": len(rendered_names),
            "missing": sorted(set(original_names) - set(rendered_names)),
            "unexpected": sorted(set(rendered_names) - set(original_names)),
        },
        "changed_callable_closure": {
            "status": "GREEN" if not missing_calls else "RED",
            "references": len(custom_calls),
            "missing": missing_calls,
        },
        "event_closure": {
            "status": "GREEN" if not missing_events else "RED",
            "definitions": len(event_definitions),
            "referenced_ids": len(event_ids),
            "missing": missing_events,
        },
        "simp_chinese_localization_closure": {
            "status": "GREEN" if not missing_loc else "RED",
            "definitions": len(loc_definitions),
            "references": len(b1_loc_references),
            "missing": missing_loc,
        },
        "bom_and_braces": {
            "status": "GREEN" if not bom_missing and not unbalanced else "RED",
            "text_files": len(text_files),
            "bom_missing": bom_missing,
            "brace_unbalanced": unbalanced,
        },
    }
    failed_checks = sorted(
        name for name, value in checks.items() if value.get("status") != "GREEN"
    )
    effect_part_rows = [
        {
            "path": relative.as_posix(),
            "bytes": len(data),
            "sha256": sha256_bytes(data),
        }
        for relative, _path, data in materialized_effects
    ]
    block_manifest = {
        "schema_version": 1,
        "kind": "zg361_b1_effect_startup_bisect_blocks",
        "diagnostic_only": True,
        "mode": mode,
        "balanced_cut_before_index": balanced_cut(original_blocks),
        "original_effect": {
            "path": str((b1_source / EFFECT_RELATIVE).resolve()),
            "bytes": len(original_effect),
            "sha256": sha256_bytes(original_effect),
        },
        "rendered_effect": {
            "parts": effect_part_rows,
            "total_bytes": sum(int(row["bytes"]) for row in effect_part_rows),
            "combined_content_sha256": sha256_bytes(
                b"".join(data for _relative, _path, data in materialized_effects)
            ),
        },
        "real_indices": real_indices,
        "real_names": [original_names[index] for index in real_indices],
        "stub_indices": sorted(set(range(len(original_blocks))) - set(real_indices)),
        "stub_names": [
            original_names[index]
            for index in sorted(set(range(len(original_blocks))) - set(real_indices))
        ],
        "blocks": block_rows,
    }
    write_json(output / "block-manifest.json", block_manifest)

    preflight = {
        "schema_version": 1,
        "kind": "zg361_b1_effect_startup_bisect_preflight",
        "status": "GREEN_STATIC" if not failed_checks else "RED_STATIC",
        "diagnostic_only": True,
        "production_or_feature_certification": False,
        "canonical_source_modified": False,
        "mode": mode,
        "projection": projection_name,
        "candidate": {
            "source": str(source_root),
            "product": str(product_root),
            "file_count": len(product_rows),
            "bytes": sum(int(row["bytes"]) for row in product_rows),
            "source_tree_sha256": manifest["source_tree_sha256"],
            "formal_overlay_tree_sha256": manifest["formal_overlay_tree_sha256"],
            "file_list_sha256": manifest["file_list_sha256"],
            "projection_manifest": str(projection_path),
            "projection_manifest_sha256": sha256_file(projection_path),
            "effect_bytes": sum(int(row["bytes"]) for row in effect_part_rows),
            "effect_sha256": (
                effect_part_rows[0]["sha256"] if len(effect_part_rows) == 1 else None
            ),
            "effect_parts": effect_part_rows,
        },
        "baseline": {
            "path": str(baseline),
            "file_count": len(tree_rows(baseline)),
            "bytes": sum(path.stat().st_size for path in baseline.rglob("*") if path.is_file()),
        },
        "inputs": observed_inputs,
        "block_manifest": str((output / "block-manifest.json").resolve()),
        "block_manifest_sha256": sha256_file(output / "block-manifest.json"),
        "materialization": str((output / "materialization.json").resolve()),
        "materialization_sha256": sha256_file(output / "materialization.json"),
        "materialization_replay": str((output / "materialization-replay.json").resolve()),
        "materialization_replay_sha256": sha256_file(output / "materialization-replay.json"),
        "checks": checks,
        "failed_checks": failed_checks,
        "runtime": {
            "ck3_launch": "NOT_RUN",
            "live_status": "pending",
        },
        "limits": [
            "Stubbed effect bodies deliberately change gameplay semantics.",
            "A full-entry GREEN result certifies only this startup/load control.",
            "This tree must never be released or used as B1 feature evidence.",
        ],
    }
    write_json(output / "preflight.json", preflight)
    if failed_checks:
        raise B1BisectError(f"static preflight failed: {failed_checks}")
    return preflight


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument(
        "--b1-source",
        type=Path,
        required=True,
        help="frozen pre-split B1 source root containing the exact monolith",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--projection-name", required=True)
    parser.add_argument(
        "--mode",
        choices=("all-stub", "left-real", "right-real", "ranges", "balanced-files"),
        required=True,
    )
    parser.add_argument(
        "--real-ranges",
        help="comma-separated inclusive zero-based block ranges for --mode ranges",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = materialize(
            baseline=args.baseline,
            b1_source=args.b1_source,
            output=args.output,
            projection_name=args.projection_name,
            mode=args.mode,
            real_ranges=args.real_ranges,
        )
    except (B1BisectError, OSError, ValueError) as error:
        print(f"B1 effect bisect failed: {error}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
