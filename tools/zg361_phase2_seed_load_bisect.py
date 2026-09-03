#!/usr/bin/env python3
"""Materialize the frozen seed r3 all-effect-stub load diagnostic.

This tool is deliberately diagnostic-only.  It copies the exact 245-file
seed-entry r3 product, replaces only the 314 effects in the 68-file seed
overlay with same-name empty bodies, and writes a hash-bound projection plus
an exact replay.  It never edits the canonical mod and never launches CK3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from typing import Any, Mapping, Sequence

from phase2_b1_effect_bisect import render_effect_variant
from phase2_workforce_block_segments import find_blocks, scan_line
from zg361_phase2_product_projection import (
    ProductProjectionError,
    materialize_projection,
    write_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARENT_ROOT = (
    ROOT / "_runtime/phase2-seed-entry-production-closure-20260904-r3-final"
)
BOM = b"\xef\xbb\xbf"
EXPECTED_PARENT = {
    "files": 245,
    "bytes": 12_097_112,
    "formal_overlay_tree_sha256": "2a40ee35ec48f404c5d7d62f7377a42a2743b15719f8725a58e229fb0899c9aa",
    "source_tree_sha256": "6094e52cc25f17d6b163f0978beb0b095d4c55e8599c908020a9049765946908",
    "file_list_sha256": "9db65e55345a477087b3957ef480e3e16439e8ad9cff54c809ff5a25b4f9529c",
    "projection_sha256": "0eff8b4342a99bb56eb778adb495c89f2da02966164e16cd244ff965a535e3ef",
    "preflight_sha256": "770e2a1a7627c4f16e9dc5ff33243d92f6d4066b54a2617c9ac031f9675fc1ec",
    "contract_sha256": "90b5289812e259fe194164b5685f858abe2e3c3df0d767cede45173d2784c7ab",
    "overlay_files": 110,
    "overlay_bytes": 2_938_670,
    "effect_files": 68,
    "effect_definitions": 314,
    "event_files": 35,
    "event_definitions": 142,
    "court_position_files": 2,
    "localization_files": 5,
}
EXPECTED_GROUPS = {
    "ab": {"files": 11, "definitions": 75, "bytes": 678_684},
    "ac": {"files": 17, "definitions": 89, "bytes": 796_958},
    "ad": {"files": 13, "definitions": 63, "bytes": 729_407},
    "facts": {"files": 20, "definitions": 76, "bytes": 403_241},
    "al": {"files": 5, "definitions": 8, "bytes": 126_985},
    "root": {"files": 2, "definitions": 3, "bytes": 17_761},
}

ENDGAME_GROUP_CODES = {
    "ab": frozenset({"017", "018", "025a", "026", "027", "036", "037", "038", "039", "040", "041"}),
    "ac": frozenset({"008", "014a", "019", "020", "024a", "028a", "029", "030", "042", "043", "044", "045", "046a", "046b", "047", "048a", "048b"}),
    "ad": frozenset({"021", "022a", "031a", "032", "033a", "049", "050a", "050b", "051", "052", "053a", "053b", "054"}),
    "facts": frozenset({"009a", "010", "011", "012", "013", "014c", "015c"}),
    "al": frozenset({"014e", "023c", "035c", "061a", "061b"}),
    "root": frozenset({"001", "024d"}),
}
FACT_PREFIXES = (
    "zg361_phase2_central_002_",
    "zg361_workforce_ad_fact_",
    "zg361_workforce_appointment_fact_",
    "zg361_workforce_attribution_fact_",
    "zg361_workforce_exit_fact_",
    "zg361_workforce_remediation_fact_",
)
ENDGAME_RE = re.compile(r"^zg361_workforce_endgame_([0-9]{3}[a-z]?)_")


class SeedLoadBisectError(ValueError):
    """The frozen parent or diagnostic projection failed its contract."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SeedLoadBisectError(f"cannot read {path}: {error}") from error
    if not isinstance(payload, dict):
        raise SeedLoadBisectError(f"JSON root must be an object: {path}")
    return payload


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
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


def classify_effect_path(relative: str) -> str:
    name = PurePosixPath(relative).name
    if any(name.startswith(prefix) for prefix in FACT_PREFIXES):
        return "facts"
    match = ENDGAME_RE.match(name)
    if match:
        code = match.group(1)
        matches = [group for group, codes in ENDGAME_GROUP_CODES.items() if code in codes]
        if len(matches) == 1:
            return matches[0]
    raise SeedLoadBisectError(f"unclassified seed overlay effect shard: {relative}")


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise SeedLoadBisectError(f"frozen parent {label} is missing: {path}")
    observed = sha256_file(path)
    if observed != expected:
        raise SeedLoadBisectError(
            f"frozen parent {label} SHA drifted: {observed} != {expected}"
        )


def _definition_names(row: Mapping[str, object]) -> list[str]:
    value = row.get("definition_names")
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SeedLoadBisectError(f"invalid definition_names for {row.get('path')}")
    return value


def validate_parent(parent_root: Path = DEFAULT_PARENT_ROOT) -> dict[str, Any]:
    parent_root = parent_root.resolve()
    product = parent_root / "product"
    projection_path = parent_root / "projection.json"
    preflight_path = parent_root / "preflight.json"
    contract_path = parent_root / "closure-contract.json"
    if not product.is_dir():
        raise SeedLoadBisectError(f"frozen parent product is missing: {product}")
    _require_hash(projection_path, EXPECTED_PARENT["projection_sha256"], "projection")
    _require_hash(preflight_path, EXPECTED_PARENT["preflight_sha256"], "preflight")
    _require_hash(contract_path, EXPECTED_PARENT["contract_sha256"], "contract")
    projection = read_json(projection_path)
    preflight = read_json(preflight_path)
    contract = read_json(contract_path)
    rows = tree_rows(product)
    if len(rows) != EXPECTED_PARENT["files"] or sum(int(row["bytes"]) for row in rows) != EXPECTED_PARENT["bytes"]:
        raise SeedLoadBisectError("frozen parent product count/bytes drifted")
    if rows != projection.get("files"):
        raise SeedLoadBisectError("frozen parent product rows differ from projection")
    for key in ("formal_overlay_tree_sha256", "source_tree_sha256", "file_list_sha256"):
        if projection.get(key) != EXPECTED_PARENT[key]:
            raise SeedLoadBisectError(f"frozen parent projection {key} drifted")
    candidate = preflight.get("candidate")
    overlay = preflight.get("overlay")
    if not isinstance(candidate, dict) or not isinstance(overlay, dict):
        raise SeedLoadBisectError("frozen parent preflight lacks candidate/overlay")
    if candidate.get("expected_file_count") != EXPECTED_PARENT["files"] or candidate.get("expected_bytes") != EXPECTED_PARENT["bytes"] or candidate.get("formal_overlay_tree_sha256") != EXPECTED_PARENT["formal_overlay_tree_sha256"]:
        raise SeedLoadBisectError("frozen parent preflight candidate identity drifted")
    if overlay.get("file_count") != EXPECTED_PARENT["overlay_files"] or overlay.get("bytes") != EXPECTED_PARENT["overlay_bytes"]:
        raise SeedLoadBisectError("frozen parent overlay identity drifted")
    overlay_rows = overlay.get("files")
    if not isinstance(overlay_rows, list) or len(overlay_rows) != EXPECTED_PARENT["overlay_files"]:
        raise SeedLoadBisectError("frozen parent overlay rows drifted")
    parent_by_path = {str(row["path"]): row for row in rows}
    overlay_paths: set[str] = set()
    by_kind: dict[str, list[dict[str, object]]] = {}
    for raw in overlay_rows:
        if not isinstance(raw, dict):
            raise SeedLoadBisectError("frozen parent overlay row is not an object")
        row = dict(raw)
        relative = str(row.get("path"))
        if relative in overlay_paths:
            raise SeedLoadBisectError(f"duplicate frozen overlay path: {relative}")
        overlay_paths.add(relative)
        if parent_by_path.get(relative) != {
            "path": relative,
            "bytes": row.get("bytes"),
            "sha256": row.get("sha256"),
        }:
            raise SeedLoadBisectError(f"frozen overlay row differs from product: {relative}")
        by_kind.setdefault(str(row.get("kind")), []).append(row)
    expected_kinds = {
        "effect": (EXPECTED_PARENT["effect_files"], EXPECTED_PARENT["effect_definitions"]),
        "event": (EXPECTED_PARENT["event_files"], EXPECTED_PARENT["event_definitions"]),
        "court_position": (EXPECTED_PARENT["court_position_files"], 2),
        "localization": (EXPECTED_PARENT["localization_files"], 28),
    }
    if set(by_kind) != set(expected_kinds):
        raise SeedLoadBisectError(f"unexpected frozen overlay kinds: {sorted(by_kind)}")
    for kind, (files, definitions) in expected_kinds.items():
        if len(by_kind[kind]) != files or sum(int(row["definitions"]) for row in by_kind[kind]) != definitions:
            raise SeedLoadBisectError(f"frozen overlay {kind} cardinality drifted")
    # The copied contract is itself frozen, and its candidate must agree with the preflight.
    if contract.get("candidate", {}).get("formal_overlay_tree_sha256") != EXPECTED_PARENT["formal_overlay_tree_sha256"]:
        raise SeedLoadBisectError("frozen closure contract candidate identity drifted")
    return {
        "root": parent_root,
        "product": product,
        "projection_path": projection_path,
        "preflight_path": preflight_path,
        "contract_path": contract_path,
        "rows": rows,
        "overlay_rows": overlay_rows,
        "overlay_paths": overlay_paths,
        "by_kind": by_kind,
    }


def group_metadata(effect_rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    groups = {
        name: {"files": 0, "definitions": 0, "bytes": 0, "paths": []}
        for name in EXPECTED_GROUPS
    }
    for row in effect_rows:
        relative = str(row["path"])
        group = classify_effect_path(relative)
        value = groups[group]
        value["files"] = int(value["files"]) + 1
        value["definitions"] = int(value["definitions"]) + int(row["definitions"])
        value["bytes"] = int(value["bytes"]) + int(row["bytes"])
        value["paths"].append(relative)
    for group, expected in EXPECTED_GROUPS.items():
        observed = {key: groups[group][key] for key in ("files", "definitions", "bytes")}
        if observed != expected:
            raise SeedLoadBisectError(
                f"seed effect group {group} drifted: {observed} != {expected}"
            )
        groups[group]["paths"] = sorted(groups[group]["paths"])
    return groups


def brace_balance(path: Path) -> tuple[int, bool]:
    depth = 0
    quoted = False
    for line in path.read_text(encoding="utf-8-sig").splitlines(keepends=True):
        delta, quoted = scan_line(line, quoted)
        depth += delta
        if depth < 0:
            break
    return depth, quoted


def materialize(
    *,
    output: Path,
    projection_name: str,
    parent_root: Path = DEFAULT_PARENT_ROOT,
) -> dict[str, Any]:
    output = output.resolve()
    parent_root = parent_root.resolve()
    if output.exists():
        raise SeedLoadBisectError(f"output already exists; use a fresh path: {output}")
    if not projection_name or any(char in projection_name for char in "/\\\x00"):
        raise SeedLoadBisectError(f"projection name is malformed: {projection_name!r}")
    for forbidden in (parent_root, ROOT / "mod_zhongguo_style"):
        try:
            output.relative_to(forbidden.resolve())
        except ValueError:
            continue
        raise SeedLoadBisectError(f"output must not be inside immutable authority: {forbidden}")

    parent = validate_parent(parent_root)
    effect_rows = parent["by_kind"]["effect"]
    groups = group_metadata(effect_rows)
    output.mkdir(parents=True)
    source = output / "source"
    shutil.copytree(parent["product"], source)

    rendered_files: list[dict[str, object]] = []
    original_names: list[str] = []
    rendered_names: list[str] = []
    for row in sorted(effect_rows, key=lambda item: str(item["path"])):
        relative = str(row["path"])
        path = source / PurePosixPath(relative)
        original = path.read_bytes()
        _header, original_blocks = find_blocks(original)
        expected_names = _definition_names(row)
        observed_names = [str(block["name"]) for block in original_blocks]
        if observed_names != expected_names:
            raise SeedLoadBisectError(f"parent effect definition order drifted: {relative}")
        rendered, block_rows = render_effect_variant(original, [])
        path.write_bytes(rendered)
        _rendered_header, after_blocks = find_blocks(rendered)
        after_names = [str(block["name"]) for block in after_blocks]
        if after_names != observed_names:
            raise SeedLoadBisectError(f"stub rendering changed definition names: {relative}")
        original_names.extend(observed_names)
        rendered_names.extend(after_names)
        rendered_files.append(
            {
                "path": relative,
                "group": classify_effect_path(relative),
                "body_mode": "stub",
                "definitions": len(observed_names),
                "definition_names": observed_names,
                "original_bytes": len(original),
                "original_sha256": sha256_bytes(original),
                "rendered_bytes": len(rendered),
                "rendered_sha256": sha256_bytes(rendered),
                "blocks": [
                    {
                        "index": int(before["index"]),
                        "name": str(before["name"]),
                        "body_mode": "stub",
                        "original_bytes": int(before["bytes"]),
                        "original_sha256": str(before["sha256"]),
                        "rendered_bytes": int(after["bytes"]),
                        "rendered_sha256": str(after["sha256"]),
                    }
                    for before, after in zip(block_rows, after_blocks, strict=True)
                ],
            }
        )

    if len(original_names) != EXPECTED_PARENT["effect_definitions"] or original_names != rendered_names or len(set(rendered_names)) != len(rendered_names):
        raise SeedLoadBisectError("stubbed overlay definition surface is not unique and exact")

    parent_rows_by_path = {str(row["path"]): row for row in parent["rows"]}
    source_rows = tree_rows(source)
    source_by_path = {str(row["path"]): row for row in source_rows}
    if set(source_by_path) != set(parent_rows_by_path):
        raise SeedLoadBisectError("diagnostic path set differs from frozen parent")
    effect_paths = {str(row["path"]) for row in effect_rows}
    retained_paths = set(parent_rows_by_path) - effect_paths
    retained_mismatches = sorted(
        path for path in retained_paths if source_by_path[path] != parent_rows_by_path[path]
    )
    if retained_mismatches:
        raise SeedLoadBisectError(f"retained parent files changed: {retained_mismatches}")

    bom_missing: list[str] = []
    brace_errors: list[dict[str, object]] = []
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        if path.suffix.lower() not in {".txt", ".gui", ".yml"}:
            continue
        relative = path.relative_to(source).as_posix()
        if not path.read_bytes().startswith(BOM):
            bom_missing.append(relative)
        if path.suffix.lower() != ".yml":
            depth, quoted = brace_balance(path)
            if depth != 0 or quoted:
                brace_errors.append({"path": relative, "depth": depth, "quoted": quoted})
    if bom_missing or brace_errors:
        raise SeedLoadBisectError(f"BOM/brace gate failed: bom={bom_missing}, braces={brace_errors}")

    projection_path = output / "projection.json"
    try:
        manifest = write_manifest(source, projection_path, projection_name=projection_name)
        product = output / "product"
        replay = output / "materialized-check"
        receipt = materialize_projection(source, product, projection_name=projection_name, manifest_path=projection_path)
        replay_receipt = materialize_projection(source, replay, projection_name=projection_name, manifest_path=projection_path)
    except ProductProjectionError as error:
        raise SeedLoadBisectError(str(error)) from error
    write_json(output / "materialization.json", receipt)
    write_json(output / "materialization-replay.json", replay_receipt)
    product_rows = tree_rows(product)
    replay_rows = tree_rows(replay)
    if source_rows != product_rows or source_rows != replay_rows:
        raise SeedLoadBisectError("source/product/materialized-check rows differ")

    block_manifest = {
        "schema_version": 1,
        "kind": "zg361_phase2_seed_load_bisect_blocks",
        "mode": "all-effect-stub",
        "diagnostic_only": True,
        "forbidden_for_seed_release": True,
        "parent_formal_overlay_tree_sha256": EXPECTED_PARENT["formal_overlay_tree_sha256"],
        "groups": groups,
        "effect_files": rendered_files,
    }
    write_json(output / "block-manifest.json", block_manifest)
    preflight = {
        "schema_version": 1,
        "kind": "zg361_phase2_seed_load_bisect_preflight",
        "status": "GREEN_STATIC_DIAGNOSTIC",
        "mode": "all-effect-stub",
        "diagnostic_only": True,
        "forbidden_for_seed_release": True,
        "seed_or_feature_certification": False,
        "ck3_launch": "NOT_RUN",
        "parent": {
            "root": str(parent_root),
            "product": str(parent["product"]),
            **EXPECTED_PARENT,
        },
        "candidate": {
            "source": str(source),
            "product": str(product),
            "materialized_check": str(replay),
            "projection": projection_name,
            "files": len(source_rows),
            "bytes": sum(int(row["bytes"]) for row in source_rows),
            "source_tree_sha256": manifest["source_tree_sha256"],
            "formal_overlay_tree_sha256": manifest["formal_overlay_tree_sha256"],
            "file_list_sha256": manifest["file_list_sha256"],
            "projection_manifest_sha256": sha256_file(projection_path),
        },
        "selection": {
            "effect_files": len(effect_rows),
            "definitions": len(rendered_names),
            "stubbed_definitions": len(rendered_names),
            "real_definitions": 0,
            "groups": groups,
        },
        "checks": {
            "parent_identity": {"status": "GREEN"},
            "path_set": {"status": "GREEN", "same_as_parent": True, "files": len(source_rows)},
            "retained_byte_identity": {
                "status": "GREEN",
                "files": len(retained_paths),
                "inherited_incident_files": EXPECTED_PARENT["files"] - EXPECTED_PARENT["overlay_files"],
                "retained_overlay_events": EXPECTED_PARENT["event_files"],
                "retained_overlay_court_positions": EXPECTED_PARENT["court_position_files"],
                "retained_overlay_localization": EXPECTED_PARENT["localization_files"],
                "mismatches": [],
            },
            "definition_surface": {"status": "GREEN", "unique": True, "expected": EXPECTED_PARENT["effect_definitions"], "observed": len(rendered_names)},
            "bom_and_braces": {"status": "GREEN", "bom_missing": [], "brace_errors": []},
            "deterministic_materialization": {"status": "GREEN", "source_equals_product": True, "source_equals_replay": True},
        },
        "block_manifest": {
            "path": str((output / "block-manifest.json").resolve()),
            "sha256": sha256_file(output / "block-manifest.json"),
        },
        "runtime": {"live_status": "pending", "ck3_launch": "NOT_RUN"},
        "limits": [
            "All 314 selected effect bodies are empty diagnostic stubs.",
            "A CK3 GREEN result can certify only a startup/load boundary.",
            "This tree must never be used for seed capture, gameplay evidence, release, or Workshop upload.",
        ],
    }
    write_json(output / "preflight.json", preflight)
    return preflight


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--projection-name", required=True)
    parser.add_argument("--parent-root", type=Path, default=DEFAULT_PARENT_ROOT)
    parser.add_argument("--mode", choices=("all-effect-stub",), default="all-effect-stub")
    args = parser.parse_args(argv)
    try:
        report = materialize(
            output=args.output,
            projection_name=args.projection_name,
            parent_root=args.parent_root,
        )
    except (SeedLoadBisectError, OSError, ValueError) as error:
        print(f"RED: {error}")
        return 1
    candidate = report["candidate"]
    print(
        "GREEN_STATIC_DIAGNOSTIC: all-effect-stub "
        f"{candidate['files']} files / {candidate['bytes']} bytes / "
        f"formal SHA {candidate['formal_overlay_tree_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
