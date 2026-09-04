#!/usr/bin/env python3
"""Freeze the hash-bound b3i ABI-preserving trigger diagnostic live verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


DEFAULT_ATTEMPT_ROOT = Path(
    r"Z:\ck3_mod_rewrite_process_assets\zg361"
    r"\b3i-fecd2f2-trigger-abi-false-20260904-084813Z"
)
EXPECTED_SHA256 = {
    "diagnostic_manifest": "26f2a6bac8b245ec6ba5cb64fbcb2bbba1b9192f18c5a5a0ab3c975081da3bbd",
    "outer_report": "604e3ac5c880e0488166715f6d995a350070a11dcd1fc0adc15b385939f9ed9f",
    "cell_report": "a4f27bb4e883749b45dd69a59b7e69ef16175f57ff5d2cd837f045745323f9f7",
    "evidence_index": "fa7da9f16c4c823dcbf0df384d0ba2d83b1cf796c84a8dab539c5b82c1d3e0db",
    "final_error": "031d72f6ef1efbe171badc99cc0c7b9ea5d8d153e08ece62d57af9c87b60f539",
}
FORBIDDEN_LOG_PATTERNS = {
    "zero_argument_provider": re.compile(
        r"Scripted trigger should have no arguments", re.IGNORECASE
    ),
    "unknown_trigger": re.compile(r"Unknown trigger", re.IGNORECASE),
    "unknown_effect": re.compile(r"Unknown effect", re.IGNORECASE),
    "parser_error": re.compile(r"Parser Error", re.IGNORECASE),
}


class LiveVerdictError(ValueError):
    """The frozen live attempt does not satisfy the diagnostic evidence contract."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise LiveVerdictError(f"expected JSON object: {path}")
    return value


def _count_log_patterns(artifacts: Path) -> dict[str, int]:
    counts = {name: 0 for name in FORBIDDEN_LOG_PATTERNS}
    for path in sorted(artifacts.rglob("*.log")):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for name, pattern in FORBIDDEN_LOG_PATTERNS.items():
            counts[name] += len(pattern.findall(text))
    return counts


def build_verdict(
    attempt_root: Path,
    *,
    expected_sha256: Mapping[str, str] = EXPECTED_SHA256,
) -> dict[str, object]:
    attempt_root = attempt_root.resolve()
    artifacts = attempt_root / "artifacts-live"
    paths = {
        "diagnostic_manifest": attempt_root / "diagnostic-manifest.json",
        "outer_report": artifacts / "report.json",
        "cell_report": artifacts / "cell" / "report.json",
        "evidence_index": artifacts / "evidence-index.json",
        "final_error": artifacts / "cell" / "final_error.log",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise LiveVerdictError(f"required frozen evidence missing: {missing}")
    observed_sha256 = {name: _sha256(path) for name, path in paths.items()}
    if observed_sha256 != dict(expected_sha256):
        raise LiveVerdictError(
            f"frozen evidence identity mismatch: {observed_sha256!r}"
        )

    manifest = _load_json(paths["diagnostic_manifest"])
    report = _load_json(paths["outer_report"])
    cell_report = _load_json(paths["cell_report"])
    loader_gate = _load_json(artifacts / "cell" / "03_loader_gate.json")
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
    frontend = next(row for row in progress if row.get("stage") == "frontend")
    terminal = loader_gate.get("append_only_loader_stage")
    if not isinstance(terminal, dict):
        raise LiveVerdictError("loader gate lacks terminal stage")

    pattern_counts = _count_log_patterns(artifacts)
    final_error = paths["final_error"].read_text(
        encoding="utf-8-sig", errors="replace"
    )
    known_noise = {
        "unrecognized_loc_key": final_error.count("Unrecognized loc key"),
        "set_but_never_used": final_error.count("is set but is never used"),
        "used_but_never_set": final_error.count("is used but is never set"),
    }
    cell = report.get("cell")
    if not isinstance(cell, dict):
        raise LiveVerdictError("outer report lacks cell result")
    cleanup = cell.get("native_cleanup")
    if not isinstance(cleanup, dict):
        raise LiveVerdictError("outer report lacks native cleanup")
    session_report = cleanup.get("session_report")
    shutdown = (
        session_report.get("shutdown") if isinstance(session_report, dict) else None
    )
    checks = {
        "diagnostic_manifest_green": manifest.get("result") == "GREEN",
        "provider_inference_gate_green": bool(
            isinstance(manifest.get("checks"), dict)
            and manifest["checks"].get(
                "provider_parameter_inference_abi_preserved"
            )
            is True
        ),
        "outer_and_cell_expected_red": report.get("result") == "RED"
        and cell_report.get("result") == "RED",
        "first_303_exact": first_303.get("elapsed_seconds") == 123.635,
        "frontend_reached_exact": frontend.get("elapsed_seconds") == 127.688,
        "terminal_is_save_resume_red": terminal.get("state") == "save_resume_red"
        and terminal.get("reason_code") == "frontend_without_load_save"
        and terminal.get("elapsed_seconds") == 299.979,
        "all_material_error_patterns_absent": all(
            count == 0 for count in pattern_counts.values()
        ),
        "known_noise_counts_match": known_noise
        == {
            "unrecognized_loc_key": 952,
            "set_but_never_used": 13_992,
            "used_but_never_set": 90,
        },
        "cleanup_green": cleanup.get("result") == "GREEN",
        "ck3_process_count_zero": isinstance(shutdown, dict)
        and shutdown.get("job_active_processes_final") == 0,
        "protected_storage_unchanged": report.get("protected_storage_unchanged")
        is True,
    }
    verdict = {
        "schema_version": 1,
        "kind": "zg361_b3_trigger_body_abi_diagnostic_live_verdict",
        "result": "GREEN_EVIDENCE" if all(checks.values()) else "RED_EVIDENCE",
        "attempt_root": str(attempt_root),
        "evidence_sha256": observed_sha256,
        "timing_seconds": {
            "first_303_callbacks": first_303.get("elapsed_seconds"),
            "frontend": frontend.get("elapsed_seconds"),
            "terminal": terminal.get("elapsed_seconds"),
        },
        "terminal": {
            "state": terminal.get("state"),
            "reason_code": terminal.get("reason_code"),
            "full_acceptance_result": report.get("result"),
        },
        "material_error_pattern_counts_all_logs": pattern_counts,
        "known_nonterminal_noise": known_noise,
        "cleanup": {
            "result": cleanup.get("result"),
            "ck3_process_count": (
                shutdown.get("job_active_processes_final")
                if isinstance(shutdown, dict)
                else None
            ),
            "protected_storage_unchanged": report.get(
                "protected_storage_unchanged"
            ),
        },
        "checks": checks,
        "inference": {
            "confidence": "high",
            "at_least_one_original_trigger_body_contributes_to_r5_terminal_loader_red": True,
            "specific_trigger_identified": False,
            "specific_expression_identified": False,
            "candidate_trigger_still_possible": True,
            "exact_trigger_still_possible": True,
            "rationale": (
                "With provider ABI preserved and material/parser errors absent, "
                "replacing both original bodies by false stubs restored Frontend."
            ),
        },
        "claim_boundary": (
            "This is a diagnostic Frontend milestone, not Phase2 gameplay or full "
            "acceptance GREEN; the run ended frontend_without_load_save."
        ),
        "ck3_started_by_postprocessor": False,
    }
    if verdict["result"] != "GREEN_EVIDENCE":
        raise LiveVerdictError(f"live evidence checks failed: {checks!r}")
    return verdict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", type=Path, default=DEFAULT_ATTEMPT_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        verdict = build_verdict(args.attempt_root)
        if args.output.exists():
            raise LiveVerdictError(f"output already exists: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(verdict, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (LiveVerdictError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"RED: {type(error).__name__}: {error}")
        return 1
    print("GREEN_EVIDENCE: ABI-preserving false bodies restored Frontend")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
