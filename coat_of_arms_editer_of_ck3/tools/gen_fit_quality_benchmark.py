#!/usr/bin/env python3
"""Generate the deterministic Delta-Q real/synthetic benchmark manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PRODUCT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PRODUCT_ROOT.parent
PACK_ROOT = PRODUCT_ROOT / "public" / "asset-packs" / "ck3-1.19.0.6"
REAL_ROOT = REPO_ROOT / "docs" / "coat-of-arms-fit-artifacts" / "user-picture-corpus-v14-pareto-budget-1024"
NATIVE_SUMMARY = REPO_ROOT / "docs" / "coat-of-arms-fit-artifacts" / "user-picture-corpus-v14-native-r18" / "summary.json"
PRUNED_SUMMARY = REPO_ROOT / "docs" / "coat-of-arms-fit-artifacts" / "user-picture-corpus-v15-pruned-budget-1024" / "summary.json"
EVIDENCE_ROOT = REPO_ROOT / "docs" / "coat-of-arms-fit-artifacts" / "delta-q-benchmark-v1"
REAL_OUTPUT = EVIDENCE_ROOT / "baseline-manifest.json"
SYNTHETIC_OUTPUT = PRODUCT_ROOT / "src" / "data" / "fit-quality-synthetic-corpus-v1.json"

SEED = "ck3-coa-delta-q-synthetic-corpus-v1"
PALETTE = (
    (18, 52, 86), (32, 91, 63), (117, 25, 31), (151, 93, 24),
    (206, 176, 92), (224, 221, 205), (38, 37, 43), (93, 50, 117),
    (28, 116, 135), (173, 56, 91), (81, 111, 43), (132, 130, 128),
)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def digest(sample: int, field: str) -> bytes:
    return hashlib.sha256(f"{SEED}:{sample:03d}:{field}".encode("ascii")).digest()


def choose(items: list[dict[str, Any]], sample: int, field: str) -> dict[str, Any]:
    value = int.from_bytes(digest(sample, field)[:8], "big")
    return items[value % len(items)]


def color(sample: int, slot: int) -> str:
    value = int.from_bytes(digest(sample, f"color-{slot}")[:4], "big")
    red, green, blue = PALETTE[value % len(PALETTE)]
    return f"rgb {{ {red} {green} {blue} }}"


def bounded(sample: int, field: str, minimum: float, maximum: float, steps: int = 1000) -> float:
    value = int.from_bytes(digest(sample, field)[:4], "big") % (steps + 1)
    return round(minimum + (maximum - minimum) * value / steps, 6)


def build_real_manifest(asset_manifest_sha256: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for index in range(1, 8):
        case_id = f"picture-{index:02d}"
        directory = REAL_ROOT / case_id
        report_path = directory / "report.json"
        report = read_json(report_path)
        if report.get("schema") != "ck3-coa-user-picture-quality-evidence-v1":
            raise ValueError(f"unexpected report schema: {report_path}")
        if report.get("configuration", {}).get("userDrawInstanceBudget") != 1024:
            raise ValueError(f"unexpected budget: {report_path}")
        selected = report["paretoCandidates"][0]
        source_path = directory / selected["sourceFile"]
        preview_path = directory / selected["previewFile"]
        source_sha256 = sha256_file(source_path)
        preview_sha256 = sha256_file(preview_path)
        if source_sha256 != selected["sourceSha256"]:
            raise ValueError(f"source hash mismatch: {source_path}")
        if preview_sha256 != selected["previewSha256"]:
            raise ValueError(f"preview hash mismatch: {preview_path}")
        case = report["corpus"]["case"]
        cases.append({
            "id": case_id,
            "input": {
                "file": case["file"],
                "bytes": case["bytes"],
                "width": case["width"],
                "height": case["height"],
                "sha256": case["sha256"],
            },
            "selectedCandidate": {
                "index": selected["index"],
                "source": relative(source_path),
                "sourceSha256": source_sha256,
                "preview": relative(preview_path),
                "previewSha256": preview_sha256,
                "reconstructionMode": selected["reconstructionMode"],
                "textureNames": selected["textureNames"],
            },
            "legacyMetrics": report["metrics"],
            "counts": report["counts"],
            "report": relative(report_path),
            "reportSha256": sha256_file(report_path),
        })
    payload_sha256 = sha256_bytes(canonical_bytes(cases))
    return {
        "schema": "ck3-coa-fit-quality-real-baseline-v1",
        "assetPack": {
            "id": "ck3-1.19.0.6-base-complete",
            "manifestSha256": asset_manifest_sha256,
        },
        "budget": 1024,
        "caseCount": len(cases),
        "casesPayloadSha256": payload_sha256,
        "cases": cases,
        "nativeEvidence": {
            "status": "v14-quality-priority-passed-v15-prune-pending-mcp",
            "summary": relative(NATIVE_SUMMARY),
            "summarySha256": sha256_file(NATIVE_SUMMARY),
        },
        "prunedEvidence": {
            "status": "browser-passed-native-mcp-pending",
            "summary": relative(PRUNED_SUMMARY),
            "summarySha256": sha256_file(PRUNED_SUMMARY),
        },
    }


def build_synthetic_manifest(pack: dict[str, Any], asset_manifest_sha256: str) -> dict[str, Any]:
    assets = pack.get("assets")
    if not isinstance(assets, list):
        raise ValueError("asset manifest does not contain an assets list")
    patterns = sorted(
        (asset for asset in assets if asset.get("kind") == "pattern" and asset.get("fit_eligible") and asset.get("visible")),
        key=lambda asset: asset["name"],
    )
    emblems = sorted(
        (
            asset for asset in assets
            if asset.get("kind") == "colored_emblem"
            and asset.get("fit_eligible")
            and asset.get("visible")
            and asset.get("name") not in {"ce__empty_designer.dds", "ce_block_02.dds"}
        ),
        key=lambda asset: asset["name"],
    )
    if not patterns or len(emblems) < 32:
        raise ValueError("asset pack does not contain enough fit-eligible assets")

    samples: list[dict[str, Any]] = []
    for index in range(256):
        pattern = choose(patterns, index, "pattern")
        layer_count = 1 + digest(index, "layer-count")[0] % 3
        selected: list[dict[str, Any]] = []
        used_names: set[str] = set()
        for layer in range(layer_count):
            candidate = choose(emblems, index, f"emblem-{layer}")
            cursor = emblems.index(candidate)
            while candidate["name"] in used_names:
                cursor = (cursor + 1) % len(emblems)
                candidate = emblems[cursor]
            used_names.add(candidate["name"])
            selected.append(candidate)
        wrong = choose(emblems, index, "wrong-emblem")
        while wrong["name"] in used_names:
            wrong = emblems[(emblems.index(wrong) + 1) % len(emblems)]

        colored_emblems = []
        for layer, emblem in enumerate(selected):
            flip = -1 if digest(index, f"flip-{layer}")[0] % 2 else 1
            scale_x = bounded(index, f"scale-x-{layer}", 0.22, 1.05)
            mask_count = max(1, min(3, int(emblem.get("colors", 1))))
            colored_emblems.append({
                "texture": emblem["name"],
                "textureSha256": emblem["asset_sha256"],
                "colors": [color(index, layer * 3 + offset + 3) for offset in range(3)],
                "mask": list(range(1, mask_count + 1)),
                "instances": [{
                    "position": [
                        bounded(index, f"position-x-{layer}", 0.18, 0.82),
                        bounded(index, f"position-y-{layer}", 0.18, 0.82),
                    ],
                    "scale": [round(scale_x * flip, 6), bounded(index, f"scale-y-{layer}", 0.22, 1.05)],
                    "rotation": int.from_bytes(digest(index, f"rotation-{layer}")[:2], "big") % 24 * 15,
                    "depth": layer + 1,
                }],
            })
        sample_id = f"synthetic-{index + 1:03d}"
        samples.append({
            "id": sample_id,
            "split": "dev" if index < 192 else "holdout",
            "truth": {
                "outerKey": "coa",
                "parent": "",
                "pattern": pattern["name"],
                "patternSha256": pattern["asset_sha256"],
                "colors": [color(index, slot) for slot in range(3)],
                "coloredEmblems": colored_emblems,
                "texturedEmblems": [],
            },
            "wrongEmblem": {
                "texture": wrong["name"],
                "textureSha256": wrong["asset_sha256"],
            },
        })

    sample_payload_sha256 = sha256_bytes(canonical_bytes(samples))
    return {
        "schema": "ck3-coa-fit-quality-synthetic-corpus-v1",
        "generator": {
            "contract": "sha256-counter-no-prng-v1",
            "seed": SEED,
        },
        "assetPack": {
            "id": "ck3-1.19.0.6-base-complete",
            "manifestSha256": asset_manifest_sha256,
            "fitEligiblePatterns": len(patterns),
            "fitEligibleColoredEmblems": len(emblems),
        },
        "counts": {"total": 256, "dev": 192, "holdout": 64},
        "samplesPayloadSha256": sample_payload_sha256,
        "perturbationLadders": {
            "colorChannelDelta": [8, 24, 64],
            "positionDelta": [0.01, 0.04, 0.12],
            "scaleMultiplier": [1.02, 1.1, 1.3],
            "rotationDegrees": [2, 10, 45],
            "structure": ["drop-last-layer", "replace-primary-with-wrong-emblem"],
        },
        "samples": samples,
    }


def write_or_check(path: Path, payload: dict[str, Any], check: bool) -> None:
    rendered = canonical_bytes(payload)
    if check:
        if not path.is_file() or path.read_bytes() != rendered:
            raise SystemExit(f"generated benchmark is stale: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(rendered)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest_path = PACK_ROOT / "manifest.json"
    asset_manifest_sha256 = sha256_file(manifest_path)
    recorded_manifest_sha256 = (PACK_ROOT / "manifest.sha256").read_text(encoding="ascii").strip().split()[0].upper()
    if asset_manifest_sha256 != recorded_manifest_sha256:
        raise SystemExit("asset-pack manifest SHA-256 does not match manifest.sha256")
    pack = read_json(manifest_path)
    real = build_real_manifest(asset_manifest_sha256)
    synthetic = build_synthetic_manifest(pack, asset_manifest_sha256)
    write_or_check(REAL_OUTPUT, real, args.check)
    write_or_check(SYNTHETIC_OUTPUT, synthetic, args.check)
    action = "verified" if args.check else "generated"
    print(f"{action}: real={real['caseCount']} synthetic={synthetic['counts']['total']} "
          f"dev={synthetic['counts']['dev']} holdout={synthetic['counts']['holdout']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
