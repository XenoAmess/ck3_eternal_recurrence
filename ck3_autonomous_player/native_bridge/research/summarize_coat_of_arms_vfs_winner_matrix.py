"""Validate and compact a native CoA VFS winner report without base64 payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


EXPECTED_CASES = {
    "shared-conflict",
    "load-order-0-reference",
    "load-order-1-reference",
}
EXPECTED_DIAGNOSTICS = {
    ("shared-conflict", "load-order-0-reference"): False,
    ("shared-conflict", "load-order-1-reference"): True,
    ("load-order-0-reference", "load-order-1-reference"): False,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root is not an object: {path}")
    return value


def _validate_fixture(fixture: Path) -> dict[str, object]:
    receipt_path = fixture / "vfs-fixture-receipt.json"
    receipt = _load_json(receipt_path)
    _require(
        receipt.get("schema") == "ck3-coat-of-arms-vfs-fixture-v1",
        "fixture receipt schema mismatch",
    )
    enabled = receipt.get("enabled_mods")
    _require(
        enabled
        == ["mod/coa_vfs_fixture_first.mod", "mod/coa_vfs_fixture_second.mod"],
        "fixture enabled_mods order changed",
    )
    load_path = fixture / "dlc_load.json"
    _require(
        _sha256(load_path) == receipt.get("load_configuration_sha256"),
        "fixture dlc_load.json hash mismatch",
    )
    mods = receipt.get("mods")
    _require(isinstance(mods, list) and len(mods) == 2, "fixture mod count mismatch")
    compact_mods = []
    for load_order, value in enumerate(mods):
        _require(isinstance(value, dict), "fixture mod receipt is malformed")
        descriptor = fixture / str(enabled[load_order])
        manifest = Path(str(value.get("manifest_path")))
        _require(descriptor.is_file(), "fixture descriptor is missing")
        _require(manifest.is_file(), "fixture manifest is missing")
        _require(
            _sha256(descriptor) == value.get("descriptor_sha256"),
            "fixture descriptor hash mismatch",
        )
        _require(
            _sha256(manifest) == value.get("manifest_sha256"),
            "fixture manifest hash mismatch",
        )
        _require(
            value.get("source_dds_sha256") == value.get("shared_dds_sha256")
            == value.get("reference_dds_sha256"),
            "fixture shared/reference DDS byte identity mismatch",
        )
        compact_mods.append(
            {
                "load_order": load_order,
                "registry_path": enabled[load_order],
                "descriptor_sha256": value["descriptor_sha256"],
                "manifest_sha256": value["manifest_sha256"],
                "source_dds_sha256": value["source_dds_sha256"],
                "reference_name": value["reference_name"],
            }
        )
    _require(
        compact_mods[0]["source_dds_sha256"]
        != compact_mods[1]["source_dds_sha256"],
        "fixture references are not visually independent byte sources",
    )
    return {
        "receipt_bytes": receipt_path.stat().st_size,
        "receipt_sha256": _sha256(receipt_path),
        "load_configuration_sha256": receipt["load_configuration_sha256"],
        "shared_resource_name": receipt["shared_resource_name"],
        "enabled_mods": enabled,
        "mods": compact_mods,
    }


def summarize(report_path: Path, fixture: Path, artifact_dir: Path) -> dict[str, object]:
    report_path = report_path.resolve()
    fixture = fixture.resolve()
    artifact_dir = artifact_dir.resolve()
    report = _load_json(report_path)
    _require(report.get("ok") is True and report.get("error") is None, "native report is RED")
    _require(report.get("interaction_policy", {}).get("mcp_only") is True, "report is not MCP-only")
    _require(report.get("steam", {}).get("offline") is True, "Steam offline gate did not pass")
    cleanup = report.get("cleanup")
    _require(isinstance(cleanup, dict), "cleanup receipt is missing")
    _require(
        cleanup.get("cleanup_proven") is True and cleanup.get("tree_gone") is True,
        "managed CK3 cleanup was not proven",
    )
    sequence = report.get("sequence")
    _require(isinstance(sequence, dict) and sequence.get("ok") is True, "MCP sequence is RED")
    matrix = sequence.get("vfs_winner_matrix")
    _require(isinstance(matrix, dict), "VFS winner matrix is missing")
    _require(
        matrix.get("schema") == "ck3-coat-of-arms-vfs-winner-matrix-v1"
        and matrix.get("ok") is True
        and matrix.get("inferred_winner_load_order") == 1,
        "VFS winner matrix did not prove load order 1",
    )
    cases = matrix.get("cases")
    _require(isinstance(cases, list) and len(cases) == 3, "VFS case count mismatch")
    case_ids = {value.get("id") for value in cases if isinstance(value, dict)}
    _require(case_ids == EXPECTED_CASES, "VFS case identities changed")
    compact_cases = []
    for value in cases:
        _require(isinstance(value, dict) and value.get("ok") is True, "VFS case is RED")
        _require(
            all(value.get("checks", {}).values()),
            "VFS case has a failed apply/copy/capture check",
        )
        source = value.get("source")
        native_projection = value.get("native_copy_semantic_projection")
        _require(isinstance(source, dict), "VFS case source receipt is missing")
        _require(
            source.get("semantic_projection") == native_projection,
            "VFS case native Copy changed render-description semantics",
        )
        compact_cases.append(
            {
                "id": value["id"],
                "source": source,
                "native_copy_semantic_projection": native_projection,
                "checks": value["checks"],
            }
        )
    diagnostics = matrix.get("diagnostic_pairs")
    _require(isinstance(diagnostics, list) and len(diagnostics) == 3, "diagnostic pair count mismatch")
    compact_diagnostics = []
    for value in diagnostics:
        _require(isinstance(value, dict), "diagnostic pair is malformed")
        key = (value.get("first"), value.get("second"))
        _require(key in EXPECTED_DIAGNOSTICS, "unexpected diagnostic pair")
        expected = EXPECTED_DIAGNOSTICS[key]
        _require(
            value.get("expected_equivalent_within_capture_noise") is expected
            and value.get("equivalent_within_capture_noise") is expected
            and value.get("gate_passed") is True
            and value.get("comparable") is True,
            "diagnostic pair failed its preregistered gate",
        )
        compact_diagnostics.append(dict(value))

    crop_receipts = report.get("vfs_winner_native_crops")
    _require(isinstance(crop_receipts, list) and len(crop_receipts) == 3, "crop receipt count mismatch")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    compact_crops = []
    for value in crop_receipts:
        _require(isinstance(value, dict), "crop receipt is malformed")
        source = Path(str(value.get("path"))).resolve()
        _require(source.is_file(), "native crop is missing")
        _require(
            source.stat().st_size == value.get("bytes")
            and _sha256(source) == value.get("sha256"),
            "native crop bytes/hash mismatch",
        )
        destination = artifact_dir / f"{value['id']}.png"
        if destination.exists():
            _require(destination.read_bytes() == source.read_bytes(), "published crop differs")
        else:
            shutil.copy2(source, destination)
        compact_crops.append(
            {
                "id": value["id"],
                "path": destination.name,
                "bytes": destination.stat().st_size,
                "sha256": _sha256(destination),
                "payload_kind": value["payload_kind"],
            }
        )
    return {
        "schema": "ck3-coat-of-arms-vfs-winner-evidence-v1",
        "status": "passed",
        "created_at": report["created_at"],
        "repository_head": report["repository_head"],
        "exact_build": report["binary"],
        "interaction_policy": report["interaction_policy"],
        "steam": {"offline": True},
        "fixture": _validate_fixture(fixture),
        "predeclared_hypothesis": matrix["predeclared_hypothesis"],
        "inferred_winner_load_order": matrix["inferred_winner_load_order"],
        "capture_noise_thresholds": matrix["capture_noise_thresholds"],
        "cases": compact_cases,
        "diagnostic_pairs": compact_diagnostics,
        "native_crops": compact_crops,
        "cleanup": {
            "cleanup_proven": cleanup["cleanup_proven"],
            "tree_gone": cleanup["tree_gone"],
            "contract_errors": cleanup["contract_errors"],
        },
        "raw_report": {
            "path": str(report_path),
            "bytes": report_path.stat().st_size,
            "sha256": _sha256(report_path),
        },
        "elapsed_seconds": report["elapsed_seconds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary = summarize(args.report, args.fixture, args.artifact_dir)
    encoded = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        _require(args.output.is_file(), "summary output is missing")
        _require(args.output.read_text(encoding="utf-8") == encoded, "summary output is stale")
    else:
        if args.output.exists():
            raise FileExistsError(f"summary output already exists: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "output": str(args.output), "winner": 1}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
