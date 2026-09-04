#!/usr/bin/env python3
"""Verify and freeze the current-pin private G2 evaluated-days live command.

This is a no-launch preflight.  It verifies every immutable input, the exact
evaluator bytes, the root/open_kaishek pin, candidate/default build options,
private binary markers, the cold checkpoint anchor, a fresh attempt path, and
an empty CK3/injector process inventory.  It then emits one PowerShell command
that runs exactly two read-only terms queries and always postprocesses the
private JSONL with the dedicated analyzer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable


RESEARCH_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RESEARCH_ROOT.parents[2]
DEFAULT_MANIFEST = (
    RESEARCH_ROOT
    / "fixtures"
    / "g2_evaluated_days_current_pin_live_manifest.json"
)
EXPECTED_SCHEMA = "xar.ck3.g2_evaluated_days_current_pin_live_manifest.v1"
PRIVATE_CAPTURE_SCHEMA = "xar.ck3.g2_truce_private_capture.v3"
PRIVATE_BOUNDARY_SCHEMA = "xar.ck3.g2_truce_private_evaluator_boundary.v1"
PRIVATE_CAPTURE_ENVIRONMENT = "XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH"

if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

import verify_g2_open_kaishek_compatibility as compatibility  # noqa: E402
import verify_raiktor_truce_evaluator_callsite_v1 as evaluator  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_hash(value: object, name: str) -> str:
    result = str(value).upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise ValueError(f"{name} must be a SHA-256")
    return result


def _resolve_repo_path(value: object, repo_root: Path) -> Path:
    path = Path(str(value)).expanduser()
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"capture manifest is unavailable: {error}") from error
    return _mapping(value, "manifest")


def validate_manifest_contract(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("unexpected capture manifest schema")
    if manifest.get("state") != "static-ready-waiting-for-exclusive-ck3-slot":
        raise ValueError("manifest is not waiting for the exclusive CK3 slot")
    identity = _mapping(manifest.get("identity"), "identity")
    if identity != {
        "war_id": 50_331_699,
        "character_id": 29_829,
        "date_raw": 53_223_936,
    }:
        raise ValueError("frozen G2 identity changed")
    timeouts = _mapping(manifest.get("timeouts"), "timeouts")
    if timeouts != {"readiness_seconds": 300, "session_seconds": 420}:
        raise ValueError("frozen timeouts changed")
    build = _mapping(manifest.get("build_contract"), "build_contract")
    if build != {
        "private_capture_option": "ON",
        "native_callsite_observer_option": "OFF",
        "preview_entry_observer_option": "OFF",
        "default_capture_option": "OFF",
        "private_capture_schema": PRIVATE_CAPTURE_SCHEMA,
        "boundary_schema": PRIVATE_BOUNDARY_SCHEMA,
    }:
        raise ValueError("private/default build contract changed")
    query = _mapping(manifest.get("query_contract"), "query_contract")
    expected_step = f"query-war-termination-terms-v1-{identity['war_id']}"
    if query != {
        "terms_query_count": 2,
        "allowed_gameplay_commands": [expected_step, expected_step],
        "mutation_commands": [],
        "time_advanced": False,
        "same_paused_frame": True,
    }:
        raise ValueError("read-only dual-query contract changed")
    capture = _mapping(manifest.get("capture_contract"), "capture_contract")
    if capture != {
        "group_count": 2,
        "rows_per_group": [
            "pre_call",
            "post_call_1",
            "post_call_2",
            PRIVATE_CAPTURE_SCHEMA,
        ],
        "exact_path": "root[7].default.children[1].children[0].children[0]",
        "truce_vtable_rva": "0x4461CA8",
        "duration_offset": "0x108",
        "evaluator_rva": "0x3373000",
        "requires_equal_nonnegative_results": True,
    }:
        raise ValueError("private capture contract changed")
    boundaries = _mapping(manifest.get("boundaries"), "boundaries")
    if not boundaries or any(value is not False for value in boundaries.values()):
        raise ValueError("static/readiness boundaries must all remain false")


def _driver_anchor(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    root = _mapping(value, "driver state")
    checkpoint = _mapping(root.get("last_checkpoint"), "last checkpoint")
    return {
        "format_version": root.get("format_version"),
        "pipe_name": root.get("pipe_name"),
        "episode_character_id": root.get("episode_character_id"),
        "episode_run_id": root.get("episode_run_id"),
        "last_checkpoint": {
            "sha256": str(checkpoint.get("sha256", "")).upper(),
            "date_raw": checkpoint.get("date_raw"),
            "episode_character_id": checkpoint.get("episode_character_id"),
            "episode_run_id": checkpoint.get("episode_run_id"),
        },
    }


def _cache_value(cache: str, name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}:[^=]+=(.*)$", cache)
    return match.group(1).strip() if match else None


def _process_inventory() -> dict[str, Any]:
    completed = subprocess.run(
        ["tasklist.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            (completed.stderr or completed.stdout).strip()
            or f"tasklist exited {completed.returncode}"
        )
    targets = {"ck3.exe", "xar_ck3_bridge_injector.exe"}
    counts = {name: 0 for name in sorted(targets)}
    for row in csv.reader(io.StringIO(completed.stdout)):
        if not row:
            continue
        name = row[0].strip().lower()
        if name in targets:
            counts[name] += 1
    return {"counts": counts, "all_zero": all(value == 0 for value in counts.values())}


def _ps_quote(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def build_commands(manifest: dict[str, Any], *, repo_root: Path) -> dict[str, str]:
    paths = _mapping(manifest["paths"], "paths")
    hashes = _mapping(manifest["sha256"], "sha256")
    identity = _mapping(manifest["identity"], "identity")
    timeouts = _mapping(manifest["timeouts"], "timeouts")
    python = Path(str(paths["python"])).resolve()
    runner = _resolve_repo_path(paths["runner"], repo_root)
    analyzer = _resolve_repo_path(paths["analyzer"], repo_root)
    attempt = Path(str(paths["fresh_attempt"])).resolve()
    sidecar = attempt / "g2-evaluated-days-private-v3.jsonl"
    runner_report = attempt / "report.json"
    analysis_report = attempt / "evaluated-days-private-analysis.json"
    runner_arguments = [
        python,
        "-B",
        runner,
        "--attempt-dir",
        attempt,
        "--source-checkpoint",
        paths["source_checkpoint"],
        "--source-driver-state",
        paths["source_driver_state"],
        "--expected-checkpoint-sha256",
        hashes["checkpoint"],
        "--expected-driver-state-sha256",
        hashes["driver_state"],
        "--game-dir",
        paths["game_dir"],
        "--bridge-dll",
        paths["bridge_dll"],
        "--bridge-injector",
        paths["bridge_injector"],
        "--war-id",
        identity["war_id"],
        "--expected-character-id",
        identity["character_id"],
        "--expected-date-raw",
        identity["date_raw"],
        "--timeout",
        timeouts["session_seconds"],
        "--readiness-timeout",
        timeouts["readiness_seconds"],
    ]
    analyzer_arguments = [
        python,
        "-B",
        analyzer,
        "--runner-report",
        runner_report,
        "--private-jsonl",
        sidecar,
        "--output",
        analysis_report,
        "--expected-war-id",
        identity["war_id"],
        "--expected-character-id",
        identity["character_id"],
        "--expected-date-raw",
        identity["date_raw"],
    ]
    runner_command = " ".join(["&", *(_ps_quote(item) for item in runner_arguments)])
    analyzer_command = " ".join(
        ["&", *(_ps_quote(item) for item in analyzer_arguments)]
    )
    combined = (
        "& { $env:"
        + PRIVATE_CAPTURE_ENVIRONMENT
        + " = "
        + _ps_quote(sidecar)
        + "; "
        + runner_command
        + "; $runnerExit = $LASTEXITCODE; "
        + analyzer_command
        + "; $analysisExit = $LASTEXITCODE; "
        + "Remove-Item Env:"
        + PRIVATE_CAPTURE_ENVIRONMENT
        + " -ErrorAction SilentlyContinue; "
        + "if ($analysisExit -eq 0) { exit 0 }; "
        + "Write-Error ('private analysis failed; runner exit=' + $runnerExit + "
        + " ', analysis exit=' + $analysisExit); exit $analysisExit }"
    )
    return {
        "runner": runner_command,
        "analyzer": analyzer_command,
        "combined": combined,
        "private_jsonl": str(sidecar),
        "runner_report": str(runner_report),
        "analysis_report": str(analysis_report),
    }


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def run_preflight(
    manifest_path: Path,
    report_path: Path,
    *,
    repo_root: Path = REPO_ROOT,
    process_inventory: Callable[[], dict[str, Any]] = _process_inventory,
    open_audit: Callable[..., dict[str, Any]] = compatibility.audit,
    evaluator_verify: Callable[[Path, Path], list[str]] = evaluator.verify,
) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    report_path = report_path.expanduser().resolve()
    if report_path.exists():
        raise FileExistsError(f"preflight report already exists: {report_path}")
    manifest = _load_manifest(manifest_path)
    validate_manifest_contract(manifest)
    paths = _mapping(manifest["paths"], "paths")
    expected = _mapping(manifest["sha256"], "sha256")
    identity = _mapping(manifest["identity"], "identity")
    attempt = Path(str(paths["fresh_attempt"])).expanduser().resolve()
    if report_path == attempt or attempt in report_path.parents:
        raise ValueError("preflight report must remain outside the future attempt")

    resolved = {
        "python": Path(str(paths["python"])).resolve(),
        "runner": _resolve_repo_path(paths["runner"], repo_root),
        "analyzer": _resolve_repo_path(paths["analyzer"], repo_root),
        "checkpoint": Path(str(paths["source_checkpoint"])).resolve(),
        "driver_state": Path(str(paths["source_driver_state"])).resolve(),
        "game_executable": Path(str(paths["game_dir"])).resolve()
        / "binaries"
        / "ck3.exe",
        "bridge_dll": Path(str(paths["bridge_dll"])).resolve(),
        "bridge_injector": Path(str(paths["bridge_injector"])).resolve(),
        "source_zip": Path(str(paths["source_zip"])).resolve(),
        "private_cmake_cache": Path(str(paths["private_cmake_cache"])).resolve(),
        "default_cmake_cache": Path(str(paths["default_cmake_cache"])).resolve(),
        "default_bridge_dll": Path(str(paths["default_bridge_dll"])).resolve(),
        "open_kaishek_jar": Path(str(paths["open_kaishek_jar"])).resolve(),
    }
    actual_hashes: dict[str, str | None] = {}
    for name, path in resolved.items():
        actual_hashes[name] = _sha256(path) if path.is_file() else None
    hash_checks = {
        name: actual_hashes[name] == _expected_hash(expected[name], name)
        for name in resolved
    }

    source_expected = _mapping(manifest["source_sha256"], "source_sha256")
    source_actual = {
        relative: (
            _sha256((repo_root / relative).resolve())
            if (repo_root / relative).is_file()
            else None
        )
        for relative in source_expected
    }
    source_checks = {
        relative: source_actual[relative]
        == _expected_hash(expected_hash, relative)
        for relative, expected_hash in source_expected.items()
    }

    private_cache = (
        resolved["private_cmake_cache"].read_text(encoding="utf-8-sig")
        if resolved["private_cmake_cache"].is_file()
        else ""
    )
    default_cache = (
        resolved["default_cmake_cache"].read_text(encoding="utf-8-sig")
        if resolved["default_cmake_cache"].is_file()
        else ""
    )
    private_bytes = (
        resolved["bridge_dll"].read_bytes()
        if resolved["bridge_dll"].is_file()
        else b""
    )
    default_bytes = (
        resolved["default_bridge_dll"].read_bytes()
        if resolved["default_bridge_dll"].is_file()
        else b""
    )
    anchor: dict[str, Any] = {}
    anchor_error: str | None = None
    try:
        anchor = _driver_anchor(resolved["driver_state"])
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        anchor_error = f"{type(error).__name__}: {error}"
    inventory_error: str | None = None
    try:
        inventory = process_inventory()
    except BaseException as error:
        inventory = {"counts": {}, "all_zero": False}
        inventory_error = f"{type(error).__name__}: {error}"
    open_report = open_audit(
        checkout=paths["open_kaishek_checkout"],
        require_checkout=True,
        require_clean=True,
    )
    evaluator_failures = evaluator_verify(
        resolved["game_executable"],
        repo_root
        / "ck3_autonomous_player"
        / "native_bridge"
        / "research"
        / "raiktor_truce_evaluator_callsite_v1_abi.json",
    )
    open_external = _mapping(open_report.get("external"), "open report external")
    last_checkpoint = _mapping(anchor.get("last_checkpoint"), "driver checkpoint")
    checks = {
        "all_input_hashes": all(hash_checks.values()),
        "all_candidate_source_hashes": all(source_checks.values()),
        "private_option_on": _cache_value(
            private_cache, "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1"
        )
        == "ON",
        "private_passive_observer_off": _cache_value(
            private_cache,
            "XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1",
        )
        == "OFF",
        "private_preview_observer_off": _cache_value(
            private_cache,
            "XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1",
        )
        == "OFF",
        "default_capture_off": _cache_value(
            default_cache, "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1"
        )
        == "OFF",
        "private_markers_present": PRIVATE_CAPTURE_SCHEMA.encode("ascii")
        in private_bytes
        and PRIVATE_BOUNDARY_SCHEMA.encode("ascii") in private_bytes
        and PRIVATE_CAPTURE_ENVIRONMENT.encode("utf-16le") in private_bytes,
        "default_markers_absent": PRIVATE_CAPTURE_SCHEMA.encode("ascii")
        not in default_bytes
        and PRIVATE_BOUNDARY_SCHEMA.encode("ascii") not in default_bytes,
        "driver_v2_identity": anchor.get("format_version") == 2
        and anchor.get("episode_character_id") == identity["character_id"]
        and last_checkpoint.get("episode_character_id") == identity["character_id"]
        and last_checkpoint.get("date_raw") == identity["date_raw"]
        and last_checkpoint.get("sha256") == expected["checkpoint"],
        "exact_evaluator_bytes": not evaluator_failures,
        "open_kaishek_static_compatibility": open_report.get("ok") is True
        and open_report.get("status") == "GREEN_STATIC"
        and open_external.get("head") == manifest["open_kaishek"]["commit"]
        and open_external.get("origin_main") == manifest["open_kaishek"]["commit"]
        and open_external.get("clean") is True,
        "exclusive_process_slot_empty": inventory.get("all_zero") is True,
        "future_attempt_absent": not attempt.exists(),
        "preflight_did_not_prepare_or_launch": True,
    }
    commands = build_commands(manifest, repo_root=repo_root)
    ok = all(checks.values()) and anchor_error is None and inventory_error is None
    payload = {
        "schema": "xar.ck3.g2_evaluated_days_current_pin_preflight.v1",
        "status": "ready-to-run" if ok else "red",
        "ok": ok,
        "ck3_started": False,
        "process_attached": False,
        "profile_prepared": False,
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "report": str(report_path),
        "attempt_dir": str(attempt),
        "actual_hashes": actual_hashes,
        "hash_checks": hash_checks,
        "source_hashes": source_actual,
        "source_checks": source_checks,
        "driver_anchor": anchor,
        "driver_anchor_error": anchor_error,
        "process_inventory": inventory,
        "process_inventory_error": inventory_error,
        "open_kaishek_audit": open_report,
        "evaluator_failures": evaluator_failures,
        "checks": checks,
        "query_contract": manifest["query_contract"],
        "capture_contract": manifest["capture_contract"],
        "boundaries": manifest["boundaries"],
        "artifacts": {
            "private_jsonl": commands["private_jsonl"],
            "runner_report": commands["runner_report"],
            "analysis_report": commands["analysis_report"],
        },
        "unique_powershell_command": commands["combined"],
    }
    _write_json_atomic(report_path, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = run_preflight(args.manifest, args.report)
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": payload["ok"],
                "status": payload["status"],
                "report": payload["report"],
                "unique_powershell_command": payload["unique_powershell_command"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
