#!/usr/bin/env python3
"""Freeze the hash-bound B3 exact-trigger explicit-AND live verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping, Sequence


DEFAULT_ATTEMPT_ROOT = Path(
    r"Z:\ck3_mod_rewrite_process_assets\zg361"
    r"\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z"
)
EXPECTED_SHA256 = {
    "attempt_manifest": "e07bf7605aeaf47d533f9c4cb28895fe3ecd7028ae32f92d6ed84c879f9a62d7",
    "projection_manifest": "241db7b5e2df451aadbfaeb4570b083c8563239bc0158530682b9a77da2f4acd",
    "outer_report": "f0abc5f24505019061b986db8992ca0ddd95c0d584c6c9f24b5d4bf6bb9b9b70",
    "evidence_index": "a6049d099759571921a5e81a0634517e25c91e5a0452aaba0d583041f6bfce5f",
    "cell_report": "9a9ae5c6f52aab6fc99f6d44d918c9556a8c43bcef25c430583097d8846b9e17",
    "final_error": "5acd90c8c74a82014abe065b33cb51d6bdef2df6298c0e83d9e296333b818a9d",
    "final_debug": "f2c69ee92d7b72106ec5e0629fa82b174c8526c4438aeab5b7001c055ace4296",
    "loader_gate": "0d21341e484550d8d67f28f36f9b20203b2b1df542dd43a29bf5f655b6370900",
    "loader_progress": "f79d5a1daa53be722fd68d716c563d51b01320e44e489d6d21c5f4fac92440ae",
}
EXPECTED_TIMING_SECONDS = {
    "first_303_callbacks": 123.801,
    "frontend": 125.965,
    "terminal": 299.845,
    "terminal_quiet": 173.88,
}
EXPECTED_NOISE = {
    "unrecognized_loc_key": 952,
    "set_but_never_used": 13_990,
    "used_but_never_set": 90,
}
EXPECTED_SOURCE_COMMIT = "4d3c284749f217aac1a2b291721ebd30a2c84a0a"
EXPECTED_BASE_TREE_SHA256 = (
    "50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f"
)
EXPECTED_CANDIDATE_TREE_SHA256 = (
    "d94c2d5d23e9ad254f4b20988fbf3c8e08408baa61070bd85f42b2d2fcbea35d"
)
EXPECTED_BASE_PROVIDER_SHA256 = (
    "ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7"
)
EXPECTED_CANDIDATE_PROVIDER_SHA256 = (
    "bb771a488fecc9fc131a20c562ab621d432414fa864e838c35d7e28520d7e411"
)
EXPECTED_CHANGED_PATH = (
    "common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt"
)
FORBIDDEN_LOG_PATTERNS = {
    "zero_argument_provider": re.compile(
        r"Scripted trigger should have no arguments", re.IGNORECASE
    ),
    "unknown_trigger": re.compile(r"Unknown trigger", re.IGNORECASE),
    "unknown_effect": re.compile(r"Unknown effect", re.IGNORECASE),
    "parser_error": re.compile(r"Parser Error", re.IGNORECASE),
}


class LiveVerdictError(ValueError):
    """The frozen attempt does not satisfy the explicit-AND live contract."""


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
    expected_timing: Mapping[str, float] = EXPECTED_TIMING_SECONDS,
    expected_noise: Mapping[str, int] = EXPECTED_NOISE,
) -> dict[str, object]:
    attempt_root = attempt_root.resolve()
    artifacts = attempt_root / "artifacts-live"
    paths = {
        "attempt_manifest": attempt_root / "attempt-manifest.json",
        "projection_manifest": attempt_root / "projection.json",
        "outer_report": artifacts / "report.json",
        "evidence_index": artifacts / "evidence-index.json",
        "cell_report": artifacts / "cell" / "report.json",
        "final_error": artifacts / "cell" / "final_error.log",
        "final_debug": artifacts / "cell" / "final_debug.log",
        "loader_gate": artifacts / "cell" / "03_loader_gate.json",
        "loader_progress": (
            artifacts / "cell" / "01_phase2_loader_stage_progress.jsonl"
        ),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise LiveVerdictError(f"required frozen evidence missing: {missing}")
    observed_sha256 = {name: _sha256(path) for name, path in paths.items()}
    if observed_sha256 != dict(expected_sha256):
        raise LiveVerdictError(
            f"frozen evidence identity mismatch: {observed_sha256!r}"
        )

    manifest = _load_json(paths["attempt_manifest"])
    projection = _load_json(paths["projection_manifest"])
    report = _load_json(paths["outer_report"])
    cell_report = _load_json(paths["cell_report"])
    loader_gate = _load_json(paths["loader_gate"])
    progress = [
        json.loads(line)
        for line in paths["loader_progress"]
        .read_text(encoding="utf-8-sig")
        .splitlines()
        if line.strip()
    ]
    first_303 = next(
        (row for row in progress if row.get("database_callback_count") == 303),
        None,
    )
    frontend = next((row for row in progress if row.get("stage") == "frontend"), None)
    terminal = loader_gate.get("append_only_loader_stage")
    if not isinstance(first_303, dict) or not isinstance(frontend, dict):
        raise LiveVerdictError("loader progress lacks first-303 or Frontend milestone")
    if not isinstance(terminal, dict):
        raise LiveVerdictError("loader gate lacks terminal stage")

    candidate = manifest.get("candidate")
    frozen = manifest.get("frozen_r5_a")
    if not isinstance(candidate, dict) or not isinstance(frozen, dict):
        raise LiveVerdictError("attempt manifest lacks candidate or frozen baseline")
    semantic = candidate.get("semantic_delta")
    delta = candidate.get("delta")
    base_provider = frozen.get("trigger_provider")
    candidate_provider = candidate.get("trigger_provider")
    if not all(
        isinstance(value, dict)
        for value in (semantic, base_provider, candidate_provider)
    ) or not isinstance(delta, list):
        raise LiveVerdictError("attempt manifest lacks the semantic delta ledger")

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
        raise LiveVerdictError("outer report lacks embedded cell result")
    cleanup = cell.get("native_cleanup")
    if not isinstance(cleanup, dict):
        raise LiveVerdictError("outer report lacks native cleanup")
    cleanup_checks = cleanup.get("checks")
    session = cleanup.get("session_report")
    shutdown = session.get("shutdown") if isinstance(session, dict) else None

    timings = {
        "first_303_callbacks": first_303.get("elapsed_seconds"),
        "frontend": frontend.get("elapsed_seconds"),
        "terminal": terminal.get("elapsed_seconds"),
        "terminal_quiet": terminal.get("quiet_seconds"),
    }
    checks = {
        "no_launch_candidate_identity_green": (
            manifest.get("kind")
            == "zg361_b3_exact_trigger_explicit_and_no_launch_candidate"
            and manifest.get("status") == "GREEN_NO_LAUNCH"
            and manifest.get("production_candidate") is True
            and manifest.get("source_commit") == EXPECTED_SOURCE_COMMIT
        ),
        "single_product_file_delta": (
            candidate.get("file_count") == 565
            and candidate.get("unchanged_file_count") == 564
            and len(delta) == 1
            and isinstance(delta[0], dict)
            and delta[0].get("path") == EXPECTED_CHANGED_PATH
            and candidate.get("only_expected_generated_file_changed") is True
        ),
        "base_and_candidate_tree_identity": (
            frozen.get("source_tree_sha256") == EXPECTED_BASE_TREE_SHA256
            and candidate.get("source_tree_sha256") == EXPECTED_CANDIDATE_TREE_SHA256
            and projection.get("source_tree_sha256")
            == EXPECTED_CANDIDATE_TREE_SHA256
        ),
        "same_small_two_definition_provider_boundary": (
            base_provider.get("bytes") == 16_712
            and base_provider.get("sha256") == EXPECTED_BASE_PROVIDER_SHA256
            and candidate_provider.get("bytes") == 16_786
            and candidate_provider.get("sha256")
            == EXPECTED_CANDIDATE_PROVIDER_SHA256
            and len(semantic.get("observed_placeholder_sets", {})) == 2
        ),
        "semantic_and_parameter_abi_preserved": (
            semantic.get("green") is True
            and semantic.get("single_variable")
            == "frozen_manager_exact_top_level_explicit_and_wrapper"
            and semantic.get("candidate_ready_byte_identical") is True
            and semantic.get("exact_conditions_byte_identical_after_unwrap") is True
            and semantic.get("exact_call_graph_unchanged") is True
            and semantic.get("false_stub_present") is False
            and semantic.get("definition_placeholder_sets_match_expected") is True
            and semantic.get("provider_placeholder_set_matches_expected") is True
        ),
        "outer_and_cell_expected_red": (
            report.get("result") == "RED"
            and cell_report.get("result") == "RED"
            and "reached frontend but did not enter Load Save/In Game"
            in str(cell_report.get("error_reason", ""))
            and cell_report.get("gameplay_acceptance_executed") is False
        ),
        "first_303_timing_exact": (
            timings["first_303_callbacks"] == expected_timing["first_303_callbacks"]
        ),
        "frontend_timing_exact": timings["frontend"] == expected_timing["frontend"],
        "terminal_is_frontend_without_load_save": (
            terminal.get("state") == "save_resume_red"
            and terminal.get("stage") == "frontend"
            and terminal.get("reason_code") == "frontend_without_load_save"
            and timings["terminal"] == expected_timing["terminal"]
            and timings["terminal_quiet"] == expected_timing["terminal_quiet"]
        ),
        "all_material_error_patterns_absent": all(
            count == 0 for count in pattern_counts.values()
        ),
        "known_noise_counts_match": known_noise == dict(expected_noise),
        "cleanup_all_checks_green": (
            cleanup.get("result") == "GREEN"
            and isinstance(cleanup_checks, dict)
            and bool(cleanup_checks)
            and all(value is True for value in cleanup_checks.values())
            and cleanup.get("failed_checks") == []
        ),
        "ck3_process_count_zero": (
            isinstance(shutdown, dict)
            and shutdown.get("job_active_processes_final") == 0
            and shutdown.get("tree_gone") is True
            and shutdown.get("cleanup_proven") is True
        ),
        "protected_and_product_sources_unchanged": (
            report.get("protected_storage_unchanged") is True
            and cell.get("runtime_trees_unchanged") is True
            and cell.get("source_tree_unchanged") is True
            and cell.get("runtime_source_tree_unchanged") is True
            and cell.get("phase2_product_source_tree_unchanged") is True
        ),
    }
    verdict = {
        "schema_version": 1,
        "kind": "zg361_b3_exact_trigger_explicit_and_live_verdict",
        "result": "GREEN_EVIDENCE" if all(checks.values()) else "RED_EVIDENCE",
        "attempt_root": str(attempt_root),
        "evidence_sha256": observed_sha256,
        "timing_seconds": timings,
        "terminal": {
            "state": terminal.get("state"),
            "stage": terminal.get("stage"),
            "reason_code": terminal.get("reason_code"),
            "full_acceptance_result": report.get("result"),
            "gameplay_acceptance_executed": cell_report.get(
                "gameplay_acceptance_executed"
            ),
        },
        "material_error_pattern_counts_all_logs": pattern_counts,
        "known_nonterminal_noise": known_noise,
        "cleanup": {
            "result": cleanup.get("result"),
            "all_checks_true": checks["cleanup_all_checks_green"],
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
            "exact_trigger_ast_shape_sensitivity_proven_for_frozen_projection": True,
            "explicit_and_wrapper_restored_frontend": True,
            "minimal_semantics_preserving_production_fix_supported": True,
            "file_size_root_cause_proven": False,
            "rationale": (
                "The same 16.7 KB, two-definition provider regained Frontend "
                "when the exact trigger's unchanged conjunction was nested under "
                "one explicit AND block."
            ),
        },
        "claim_boundary": (
            "GREEN_EVIDENCE closes only the B3 loader/AST-shape experiment. Full "
            "acceptance remains RED at frontend_without_load_save; no gameplay, "
            "B3-complete, T0-complete or footage claim is made."
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
    print("GREEN_EVIDENCE: explicit AND restored Frontend; full acceptance remains RED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
