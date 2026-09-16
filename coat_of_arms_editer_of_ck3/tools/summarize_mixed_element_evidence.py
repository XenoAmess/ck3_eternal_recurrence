#!/usr/bin/env python3
"""Summarize mixed-native-element fitting and pure-tile ablations.

The browser corpus reports already contain the complete evaluated candidate
ledger.  This tool projects the comparable evidence into one deterministic,
reviewable receipt without rerunning the expensive fits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


TILE_TEXTURE = "ce_block_02.dds"


def _load_object(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value, raw


def _number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _textures(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be an array of texture names")
    return list(dict.fromkeys(value))


def _native_by_id(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = summary.get("cases")
    if not isinstance(cases, list):
        raise ValueError("native summary must contain a cases array")
    result: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("native summary case must contain a string id")
        result[case["id"]] = case
    return result


def _case_summary(path: Path, native: dict[str, Any]) -> dict[str, Any]:
    report, raw = _load_object(path)
    case = report.get("corpus", {}).get("case")
    provenance = report.get("provenance")
    metrics = report.get("metrics")
    pareto = report.get("paretoCandidates")
    integrity = report.get("integrity")
    if not isinstance(case, dict) or not isinstance(case.get("id"), str):
        raise ValueError(f"{path} has no corpus case id")
    if not isinstance(provenance, dict) or not isinstance(metrics, dict):
        raise ValueError(f"{path} has no provenance or metrics object")
    if not isinstance(pareto, list) or not pareto or not isinstance(pareto[0], dict):
        raise ValueError(f"{path} has no quality-priority Pareto candidate")
    if not isinstance(integrity, dict):
        raise ValueError(f"{path} has no integrity object")

    identifier = case["id"]
    candidate_losses = provenance.get("candidateLosses")
    if not isinstance(candidate_losses, list):
        raise ValueError(f"{path} has no candidate-loss ledger")
    comparable = [item for item in candidate_losses if isinstance(item, dict)]
    pure_tile = [
        item for item in comparable
        if _textures(item.get("textureNames"), f"{identifier} candidate textures") == [TILE_TEXTURE]
    ]
    if not pure_tile:
        raise ValueError(f"{path} has no pure-tile ablation")
    best_pure_tile = min(
        pure_tile,
        key=lambda item: (
            _number(item.get("totalLoss"), f"{identifier} pure-tile total loss"),
            _number(item.get("edgeLoss"), f"{identifier} pure-tile edge loss"),
            int(item.get("layers", 0)),
        ),
    )

    primary = pareto[0]
    primary_textures = _textures(primary.get("textureNames"), f"{identifier} primary textures")
    evaluated_textures = sorted({
        texture
        for item in comparable
        for texture in _textures(item.get("textureNames"), f"{identifier} candidate textures")
    })
    non_tile_evaluated = [texture for texture in evaluated_textures if texture != TILE_TEXTURE]
    non_tile_selected = [texture for texture in primary_textures if texture != TILE_TEXTURE]
    mixed_pareto = sum(
        1
        for item in pareto
        if isinstance(item, dict)
        and any(
            texture != TILE_TEXTURE
            for texture in _textures(item.get("textureNames"), f"{identifier} Pareto textures")
        )
    )

    total_loss = _number(metrics.get("totalLoss"), f"{identifier} total loss")
    edge_loss = _number(metrics.get("edgeLoss"), f"{identifier} edge loss")
    pure_total = _number(best_pure_tile.get("totalLoss"), f"{identifier} pure-tile total loss")
    pure_edge = _number(best_pure_tile.get("edgeLoss"), f"{identifier} pure-tile edge loss")
    total_gain = pure_total - total_loss
    edge_gain = pure_edge - edge_loss

    native_roundtrip = native.get("roundtrip")
    native_framebuffer = native.get("framebuffer")
    native_reapply = native.get("copy_reapply")
    if not isinstance(native_roundtrip, dict) or not isinstance(native_framebuffer, dict):
        raise ValueError(f"native evidence for {identifier} is incomplete")
    if not isinstance(native_reapply, dict) or not isinstance(native_reapply.get("framebuffer"), dict):
        raise ValueError(f"native Copy re-Apply evidence for {identifier} is incomplete")
    native_checks = native_roundtrip.get("checks")
    if not isinstance(native_checks, dict):
        raise ValueError(f"native round-trip checks for {identifier} are incomplete")
    native_counts_preserved = all(native_checks.get(key) is True for key in (
        "drawn_instance_count_preserved",
        "logical_layer_count_preserved",
        "colored_emblem_block_count_preserved",
    ))

    seam = provenance.get("nativeTileSeamValidation")
    seam_metrics = seam.get("metrics") if isinstance(seam, dict) else None
    seam_zero = bool(
        isinstance(seam_metrics, list)
        and seam_metrics
        and all(
            isinstance(item, dict)
            and item.get("backgroundLeakPixels") == 0
            and item.get("maximumLeakAmount") == 0
            for item in seam_metrics
        )
    )
    return {
        "id": identifier,
        "input": {
            "file": case.get("file"),
            "sha256": case.get("sha256"),
            "width": case.get("width"),
            "height": case.get("height"),
        },
        "reportReceipt": {
            "path": path.as_posix(),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
        },
        "qualityPriority": {
            "textures": primary_textures,
            "nonTileTextures": non_tile_selected,
            "drawnInstances": report.get("counts", {}).get("drawnInstances"),
            "totalLoss": total_loss,
            "edgeLoss": edge_loss,
            "reconstructionMode": primary.get("reconstructionMode"),
        },
        "bestPureTileAblation": {
            "mode": best_pure_tile.get("mode"),
            "textures": [TILE_TEXTURE],
            "drawnInstances": best_pure_tile.get("layers"),
            "totalLoss": pure_total,
            "edgeLoss": pure_edge,
        },
        "gainAgainstPureTile": {
            "totalLossAbsolute": total_gain,
            "totalLossRelative": total_gain / pure_total if pure_total else 0.0,
            "edgeLossAbsolute": edge_gain,
            "edgeLossRelative": edge_gain / pure_edge if pure_edge else 0.0,
            "improvesBoth": total_gain > 0 and edge_gain > 0,
        },
        "searchCoverage": {
            "evaluatedTextures": evaluated_textures,
            "evaluatedNonTileTextures": non_tile_evaluated,
            "mixedParetoCandidates": mixed_pareto,
            "paretoCandidates": len(pareto),
        },
        "browserGates": {
            "parseErrors": integrity.get("parseErrors"),
            "serializeParseExact": integrity.get("serializeParseExact"),
            "fitAndEditorPreviewByteIdentical": integrity.get("fitAndEditorPreviewByteIdentical"),
            "seamZeroAtAllMeasuredResolutions": seam_zero,
        },
        "nativeQualityPriorityGates": {
            "applyCopyInstanceAndBlockCountsPreserved": native_counts_preserved,
            "browserToNativePixelsPassed": native_framebuffer.get("ok"),
            "copyReapplyPixelsPassed": native_reapply["framebuffer"].get("ok"),
        },
    }


def summarize(corpus_root: Path, native_summary_path: Path) -> dict[str, Any]:
    native_summary, native_raw = _load_object(native_summary_path)
    native_cases = _native_by_id(native_summary)
    report_paths = sorted(corpus_root.glob("picture-*/report.json"))
    if not report_paths:
        raise ValueError(f"no picture reports under {corpus_root}")
    cases = []
    for path in report_paths:
        report, _ = _load_object(path)
        identifier = report.get("corpus", {}).get("case", {}).get("id")
        if not isinstance(identifier, str) or identifier not in native_cases:
            raise ValueError(f"no native case matches {path}")
        cases.append(_case_summary(path, native_cases[identifier]))

    mixed_primaries = [case for case in cases if case["qualityPriority"]["nonTileTextures"]]
    mixed_improvements = [case for case in mixed_primaries if case["gainAgainstPureTile"]["improvesBoth"]]
    all_browser = all(all(value is True or value == 0 for value in case["browserGates"].values()) for case in cases)
    all_native = all(all(value is True for value in case["nativeQualityPriorityGates"].values()) for case in cases)
    return {
        "schema": "ck3-coa-mixed-native-element-ablation-summary-v1",
        "corpusRoot": corpus_root.as_posix(),
        "nativeSummaryReceipt": {
            "path": native_summary_path.as_posix(),
            "bytes": len(native_raw),
            "sha256": hashlib.sha256(native_raw).hexdigest().upper(),
        },
        "contracts": {
            "comparison": "same input + scorer + renderer + resolution + surface mask",
            "pureTileTexture": TILE_TEXTURE,
            "qualityPriority": "first non-dominated candidate sorted by total loss",
        },
        "aggregate": {
            "cases": len(cases),
            "mixedQualityPriorityCases": len(mixed_primaries),
            "mixedQualityPriorityCasesImprovingTotalAndEdge": len(mixed_improvements),
            "casesWithMixedParetoCandidate": sum(case["searchCoverage"]["mixedParetoCandidates"] > 0 for case in cases),
            "browserGatesPassed": all_browser,
            "nativeQualityPriorityGatesPassed": all_native,
        },
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument("native_summary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary = summarize(args.corpus_root, args.native_summary)
    rendered = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"stale mixed-element summary: {args.output}")
        print(f"mixed-element summary is current: {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {len(summary['cases'])} cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
