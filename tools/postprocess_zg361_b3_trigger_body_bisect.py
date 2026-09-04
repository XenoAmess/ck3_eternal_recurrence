#!/usr/bin/env python3
"""Freeze the paired V1/V2 live verdict for the r5 trigger-body bisection."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


DEFAULT_ROOT = Path(
    r"Z:\ck3_mod_rewrite_process_assets\zg361"
    r"\b3-r5-trigger-body-bisect-abi-8d2065c-20260904T093334Z"
)
EXPECTED_MANIFEST_SHA256 = (
    "1f1ae161d4a0731cce937399e654b828ba61482e951a59b0207428249c13b119"
)
EXPECTED_VARIANTS = {
    "v1": {
        "real": "zg361_p2c_m360_candidate_ready_trigger",
        "stub": "zg361_p2c_m360_frozen_manager_exact_trigger",
        "projection": "6a0cb0d2e89b9a02d35a042ebe75b9e67a11c4cbc72499828da2a1c3881da7e6",
        "outer_report": "76af1a504e2a3a04522647d58b51e4b73fb7626f7874cdbaa7d09259f2ee13f1",
        "cell_report": "08931e1ef33fc45f38723146f81b2cc4553dabd9db0db605e2e0b22a11bd587d",
        "evidence_index": "b2ae2b089eb27cc8ae26ecfd42b1f6a04e999d983098ceda311c9dc84bc8980c",
        "final_error": "b767b2c6cd70746e466e436aba5aa42847eb158292b00a7421ede402a1be1179",
        "first_303": 113.542,
        "frontend": 114.894,
        "terminal": 299.975,
        "terminal_state": "save_resume_red",
        "reason_code": "frontend_without_load_save",
        "terminal_quiet": 185.081,
        "noise": (952, 13_990, 90),
    },
    "v2": {
        "real": "zg361_p2c_m360_frozen_manager_exact_trigger",
        "stub": "zg361_p2c_m360_candidate_ready_trigger",
        "projection": "9967aed85411cf66d2056d53f99a52cbfc184c09c18a0404c90acb7d1c427762",
        "outer_report": "5d0c5767a434a4d290a03a96eedf191e0dd4a3a5bc2807eb67e25b3ed17fec7c",
        "cell_report": "40f797ceeeed7e587ccf62f4caf81ebf3864ae11258363ebe3f205668ae111e6",
        "evidence_index": "8c6bb7da730eb10a38e831439ca1410c66483e49a1f2cb51416612711e3540d1",
        "final_error": "be589d73fa88a36edc9c31c8eaa4f145d028e1b32a42bdf0babf0e73a24aefb5",
        "first_303": 120.403,
        "frontend": None,
        "terminal": 299.912,
        "terminal_state": "loader_stage_timeout",
        "reason_code": "loader_terminal_missing_after_database_callbacks",
        "terminal_quiet": 177.338,
        "noise": (952, 13_992, 90),
    },
}
MATERIAL_PATTERNS = {
    "zero_argument_provider": re.compile(
        r"Scripted trigger should have no arguments", re.IGNORECASE
    ),
    "unknown_trigger": re.compile(r"Unknown trigger", re.IGNORECASE),
    "unknown_effect": re.compile(r"Unknown effect", re.IGNORECASE),
    "parser_error": re.compile(r"Parser Error", re.IGNORECASE),
}


class BisectVerdictError(ValueError):
    """The frozen paired attempt does not satisfy its bisection contract."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise BisectVerdictError(f"expected JSON object: {path}")
    return value


def _log_counts(artifacts: Path) -> dict[str, int]:
    counts = {name: 0 for name in MATERIAL_PATTERNS}
    for path in sorted(artifacts.rglob("*.log")):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for name, pattern in MATERIAL_PATTERNS.items():
            counts[name] += len(pattern.findall(text))
    return counts


def _variant(
    root: Path,
    name: str,
    expected: Mapping[str, object],
    manifest_variant: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, bool]]:
    variant_root = root / name
    artifacts = variant_root / "artifacts-live"
    paths = {
        "projection": variant_root / "projection.json",
        "outer_report": artifacts / "report.json",
        "cell_report": artifacts / "cell" / "report.json",
        "evidence_index": artifacts / "evidence-index.json",
        "final_error": artifacts / "cell" / "final_error.log",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise BisectVerdictError(f"{name} evidence missing: {missing}")
    hashes = {label: _sha256(path) for label, path in paths.items()}
    expected_hashes = {label: str(expected[label]) for label in paths}
    if hashes != expected_hashes:
        raise BisectVerdictError(f"{name} evidence identity mismatch: {hashes!r}")

    report = _load(paths["outer_report"])
    cell_report = _load(paths["cell_report"])
    gate = _load(artifacts / "cell" / "03_loader_gate.json")
    terminal = gate.get("append_only_loader_stage")
    if not isinstance(terminal, dict):
        raise BisectVerdictError(f"{name} terminal stage missing")
    progress = [
        json.loads(line)
        for line in (
            artifacts / "cell" / "01_phase2_loader_stage_progress.jsonl"
        ).read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    first_303 = next(
        row for row in progress if row.get("database_callback_count") == 303
    )
    frontend_rows = [row for row in progress if row.get("stage") == "frontend"]
    frontend_elapsed = (
        frontend_rows[0].get("elapsed_seconds") if frontend_rows else None
    )
    material_counts = _log_counts(artifacts)
    final_error = paths["final_error"].read_text(
        encoding="utf-8-sig", errors="replace"
    )
    noise = {
        "unrecognized_loc_key": final_error.count("Unrecognized loc key"),
        "set_but_never_used": final_error.count("is set but is never used"),
        "used_but_never_set": final_error.count("is used but is never set"),
    }
    expected_noise = tuple(expected["noise"])
    cell = report.get("cell")
    cleanup = cell.get("native_cleanup") if isinstance(cell, dict) else None
    session = cleanup.get("session_report") if isinstance(cleanup, dict) else None
    shutdown = session.get("shutdown") if isinstance(session, dict) else None
    provider = manifest_variant.get("trigger_provider")
    checks = {
        "variant_static_green": manifest_variant.get("status") == "GREEN_NO_LAUNCH",
        "composition_real_matches": isinstance(provider, dict)
        and provider.get("real") == expected["real"]
        and provider.get("stub") == expected["stub"]
        and provider.get("real_matches_frozen_r5_a") is True
        and provider.get("stub_is_unconditionally_false") is True,
        "provider_abi_preserved": isinstance(provider, dict)
        and provider.get("definition_placeholder_sets_match_expected") is True
        and provider.get("provider_placeholder_set_matches_expected") is True,
        "reports_expected_red": report.get("result") == "RED"
        and cell_report.get("result") == "RED",
        "first_303_exact": first_303.get("elapsed_seconds")
        == expected["first_303"],
        "frontend_exact": frontend_elapsed == expected["frontend"],
        "terminal_exact": terminal.get("state") == expected["terminal_state"]
        and terminal.get("reason_code") == expected["reason_code"]
        and terminal.get("elapsed_seconds") == expected["terminal"]
        and terminal.get("quiet_seconds") == expected["terminal_quiet"],
        "material_patterns_absent": all(
            count == 0 for count in material_counts.values()
        ),
        "noise_counts_exact": tuple(noise.values()) == expected_noise,
        "cleanup_green": isinstance(cleanup, dict)
        and cleanup.get("result") == "GREEN",
        "ck3_process_count_zero": isinstance(shutdown, dict)
        and shutdown.get("job_active_processes_final") == 0,
        "protected_storage_unchanged": report.get("protected_storage_unchanged")
        is True,
    }
    evidence = {
        "composition": {
            "real": expected["real"],
            "stub": expected["stub"],
        },
        "sha256": hashes,
        "timing_seconds": {
            "first_303_callbacks": first_303.get("elapsed_seconds"),
            "frontend": frontend_elapsed,
            "terminal": terminal.get("elapsed_seconds"),
            "terminal_quiet": terminal.get("quiet_seconds"),
        },
        "terminal": {
            "state": terminal.get("state"),
            "reason_code": terminal.get("reason_code"),
            "full_acceptance_result": report.get("result"),
        },
        "material_pattern_counts_all_logs": material_counts,
        "known_nonterminal_noise": noise,
        "cleanup": {
            "result": cleanup.get("result") if isinstance(cleanup, dict) else None,
            "ck3_process_count": (
                shutdown.get("job_active_processes_final")
                if isinstance(shutdown, dict)
                else None
            ),
            "protected_storage_unchanged": report.get(
                "protected_storage_unchanged"
            ),
        },
    }
    return evidence, checks


def build_verdict(
    root: Path,
    *,
    expected_manifest_sha256: str = EXPECTED_MANIFEST_SHA256,
    expected_variants: Mapping[str, Mapping[str, object]] = EXPECTED_VARIANTS,
) -> dict[str, object]:
    root = root.resolve()
    manifest_path = root / "attempt-manifest.json"
    if not manifest_path.is_file():
        raise BisectVerdictError(f"attempt manifest missing: {manifest_path}")
    manifest_sha256 = _sha256(manifest_path)
    if manifest_sha256 != expected_manifest_sha256:
        raise BisectVerdictError(
            f"attempt manifest identity mismatch: {manifest_sha256}"
        )
    manifest = _load(manifest_path)
    variants = manifest.get("variants")
    if not isinstance(variants, dict) or set(variants) != {"v1", "v2"}:
        raise BisectVerdictError("attempt manifest must contain exactly V1 and V2")

    evidence: dict[str, object] = {}
    checks: dict[str, bool] = {
        "attempt_static_green": manifest.get("status") == "GREEN_NO_LAUNCH",
        "diagnostic_only": manifest.get("diagnostic_only") is True
        and manifest.get("production_candidate") is False,
        "same_frozen_r5_a": isinstance(manifest.get("frozen_r5_a"), dict)
        and manifest["frozen_r5_a"].get("source_tree_sha256")
        == "50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f",
        "paired_file_boundary": isinstance(manifest.get("invariants"), dict)
        and manifest["invariants"].get("changed_paths")
        == ["common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt"]
        and manifest["invariants"].get("unchanged_files_per_candidate") == 564,
    }
    for name in ("v1", "v2"):
        variant = variants[name]
        if not isinstance(variant, dict):
            raise BisectVerdictError(f"{name} manifest entry is invalid")
        evidence[name], variant_checks = _variant(
            root, name, expected_variants[name], variant
        )
        checks.update({f"{name}_{key}": value for key, value in variant_checks.items()})

    v1 = evidence["v1"]
    v2 = evidence["v2"]
    paired_inference_ready = (
        isinstance(v1, dict)
        and isinstance(v2, dict)
        and v1["timing_seconds"]["frontend"] == 114.894
        and v2["timing_seconds"]["frontend"] is None
    )
    checks["paired_outcome_diverges_at_frontend"] = paired_inference_ready
    verdict = {
        "schema_version": 1,
        "kind": "zg361_b3_trigger_body_bisect_live_verdict",
        "result": "GREEN_EVIDENCE" if all(checks.values()) else "RED_EVIDENCE",
        "root": str(root),
        "attempt_manifest_sha256": manifest_sha256,
        "variants": evidence,
        "checks": checks,
        "inference": {
            "confidence": "high",
            "candidate_ready_real_body_excluded": True,
            "frozen_manager_exact_real_body_or_call_structure_causal": True,
            "specific_expression_identified": False,
            "candidate_body_specific_cause": False,
            "rationale": (
                "V1 reached Frontend with candidate_ready real and exact false; "
                "V2 did not reach Frontend with candidate_ready false and exact real, "
                "while both preserved provider ABI and had zero material error patterns."
            ),
        },
        "claim_boundary": (
            "The exact trigger body/call structure is isolated, but no expression "
            "inside it is isolated; neither diagnostic run is full acceptance GREEN."
        ),
        "ck3_started_by_postprocessor": False,
    }
    if verdict["result"] != "GREEN_EVIDENCE":
        raise BisectVerdictError(f"paired evidence checks failed: {checks!r}")
    return verdict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        verdict = build_verdict(args.root)
        if args.output.exists():
            raise BisectVerdictError(f"output already exists: {args.output}")
        args.output.write_text(
            json.dumps(verdict, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (BisectVerdictError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"RED: {type(error).__name__}: {error}")
        return 1
    print("GREEN_EVIDENCE: candidate excluded; exact body/call structure isolated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
