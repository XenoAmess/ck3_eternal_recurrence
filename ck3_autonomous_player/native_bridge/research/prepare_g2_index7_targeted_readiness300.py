#!/usr/bin/env python3
"""Freeze and verify the one authorized index-7 readiness-300 live command.

This is a no-launch preflight.  It hashes immutable inputs, checks that the
instrumented DLL contains the private v2 capture markers, rejects a reused
attempt directory, and writes exactly one PowerShell launch command.  It does
not import or invoke the live runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


RESEARCH_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RESEARCH_ROOT.parents[2]
DEFAULT_MANIFEST = (
    RESEARCH_ROOT / "fixtures" / "g2_index7_targeted_readiness300_v1.json"
)
EXPECTED_SCHEMA = "xar.ck3.g2_index7_targeted_readiness300.v1"
EXPECTED_PRIVATE_SCHEMA = "xar.ck3.g2_truce_private_capture.v2"
EXPECTED_READINESS_TIMEOUT = 300.0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _expected_hash(value: object, name: str) -> str:
    result = str(value).upper()
    if re.fullmatch(r"[0-9A-F]{64}", result) is None:
        raise ValueError(f"{name} must be a SHA-256")
    return result


def _ps_quote(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _resolve_runner(path: str) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()


def validate_manifest_contract(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("unexpected manifest schema")
    timeouts = _mapping(manifest.get("timeouts"), "timeouts")
    if float(timeouts.get("readiness_seconds", -1)) != EXPECTED_READINESS_TIMEOUT:
        raise ValueError("readiness timeout must be exactly 300 seconds")
    if float(timeouts.get("session_seconds", -1)) <= EXPECTED_READINESS_TIMEOUT:
        raise ValueError("session timeout must exceed readiness timeout")
    private = _mapping(manifest.get("private_capture"), "private_capture")
    if private.get("schema") != EXPECTED_PRIVATE_SCHEMA:
        raise ValueError("private capture schema must remain v2")
    if private.get("root_index") != 7:
        raise ValueError("private capture must remain index7-only")
    boundaries = _mapping(manifest.get("boundaries"), "boundaries")
    expected_boundaries = {
        "index7_only": True,
        "duration_input_address_only": True,
        "evaluator_called": False,
        "mutation_enabled": False,
        "public_abi_changed": False,
        "readiness_changed": False,
        "production_shape_contract_changed": False,
        "preflight_launches_ck3": False,
    }
    if boundaries != expected_boundaries:
        raise ValueError("private/read-only boundaries changed")


def build_unique_command(manifest: dict[str, Any]) -> str:
    paths = _mapping(manifest["paths"], "paths")
    hashes = _mapping(manifest["sha256"], "sha256")
    identity = _mapping(manifest["identity"], "identity")
    timeouts = _mapping(manifest["timeouts"], "timeouts")
    private = _mapping(manifest["private_capture"], "private_capture")
    attempt = Path(str(paths["fresh_attempt"]))
    output = attempt / str(private["output_filename"])
    runner = _resolve_runner(str(paths["runner"]))
    arguments = [
        str(paths["python"]),
        str(runner),
        "--attempt-dir", str(attempt),
        "--source-checkpoint", str(paths["source_checkpoint"]),
        "--source-driver-state", str(paths["source_driver_state"]),
        "--expected-checkpoint-sha256", str(hashes["checkpoint"]),
        "--expected-driver-state-sha256", str(hashes["driver_state"]),
        "--game-dir", str(paths["game_dir"]),
        "--bridge-dll", str(paths["bridge_dll"]),
        "--bridge-injector", str(paths["bridge_injector"]),
        "--war-id", str(identity["war_id"]),
        "--expected-character-id", str(identity["character_id"]),
        "--expected-date-raw", str(identity["date_raw"]),
        "--timeout", str(int(float(timeouts["session_seconds"]))),
        "--readiness-timeout", str(int(float(timeouts["readiness_seconds"]))),
    ]
    invocation = " ".join(["&", *(_ps_quote(item) for item in arguments)])
    return (
        "& { $env:"
        + str(private["environment_variable"])
        + " = "
        + _ps_quote(output)
        + "; "
        + invocation
        + "; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }"
    )


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def run_preflight(manifest_path: Path, report_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    report_path = report_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be an object")
    validate_manifest_contract(manifest)
    paths = _mapping(manifest["paths"], "paths")
    expected = _mapping(manifest["sha256"], "sha256")
    runner = _resolve_runner(str(paths["runner"]))
    actual_paths = {
        "python": Path(str(paths["python"])),
        "runner": runner,
        "checkpoint": Path(str(paths["source_checkpoint"])),
        "driver_state": Path(str(paths["source_driver_state"])),
        "game_executable": Path(str(paths["game_dir"])) / "binaries" / "ck3.exe",
        "bridge_dll": Path(str(paths["bridge_dll"])),
        "bridge_injector": Path(str(paths["bridge_injector"])),
        "open_kaishek_preflight": Path(str(paths["open_kaishek_preflight"])),
    }
    actual_hashes = {name: _sha256(path) for name, path in actual_paths.items()}
    hash_checks = {
        name: actual_hashes[name] == _expected_hash(expected[name], name)
        for name in actual_paths
    }
    dll = actual_paths["bridge_dll"].read_bytes()
    runner_source = runner.read_text(encoding="utf-8")
    attempt = Path(str(paths["fresh_attempt"]))
    checks = {
        "readiness_timeout_exactly_300": float(manifest["timeouts"]["readiness_seconds"]) == 300.0,
        "fresh_attempt_absent": not attempt.exists(),
        "report_outside_attempt": report_path != attempt and attempt not in report_path.parents,
        "all_frozen_hashes_match": all(hash_checks.values()),
        "dll_private_schema_marker": EXPECTED_PRIVATE_SCHEMA.encode("ascii") in dll,
        "dll_private_environment_marker": "XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE_PATH".encode("utf-16le") in dll,
        "runner_accepts_readiness_timeout": 'parser.add_argument("--readiness-timeout"' in runner_source,
        "runner_default_is_300": "default=300.0" in runner_source,
        "preflight_did_not_launch_ck3": True,
    }
    command = build_unique_command(manifest)
    payload = {
        "schema": "xar.ck3.g2_index7_targeted_readiness300_preflight.v1",
        "status": "ready-to-run" if all(checks.values()) else "red",
        "ok": all(checks.values()),
        "ck3_started": False,
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "attempt_dir": str(attempt),
        "readiness_timeout_seconds": 300.0,
        "session_timeout_seconds": float(manifest["timeouts"]["session_seconds"]),
        "actual_hashes": actual_hashes,
        "hash_checks": hash_checks,
        "checks": checks,
        "boundaries": manifest["boundaries"],
        "unique_powershell_command": command,
    }
    if report_path.exists():
        raise FileExistsError(f"preflight report already exists: {report_path}")
    _write_json_atomic(report_path, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = run_preflight(args.manifest, args.report)
    except BaseException as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps({
        "ok": payload["ok"],
        "status": payload["status"],
        "report": str(args.report.resolve()),
        "unique_powershell_command": payload["unique_powershell_command"],
    }, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
