#!/usr/bin/env python3
"""Verify a frozen G2 native-callsite observer candidate without launching CK3."""

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
import zipfile

import pefile


EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
EXPECTED_SOURCE_COMMIT = "36fafd811b29bba11758d1ebc3929be8cbd4c9d4"
PRIVATE_MARKER = b"g2_truce_native_callsite_observer_v1"
ANCHORS = (
    (0x2EDAF01, bytes.fromhex("488D8E080100004D8B4728498BD7E8EC804900")),
    (0x2EDB58F, bytes.fromhex("488D8E080100004D8B442428498BD4E85D7A4900")),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def process_inventory() -> dict[str, list[int]]:
    result = {"ck3.exe": [], "ck3_probe.exe": []}
    completed = subprocess.run(
        ["tasklist.exe", "/FO", "CSV", "/NH"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for row in csv.reader(io.StringIO(completed.stdout)):
        if len(row) < 2:
            continue
        name = row[0].lower()
        if name not in result:
            continue
        try:
            result[name].append(int(row[1]))
        except ValueError:
            continue
    for values in result.values():
        values.sort()
    return result


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def verify(manifest_path: Path) -> dict[str, object]:
    manifest_path = manifest_path.expanduser().resolve()
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    candidate = manifest["candidate"]
    exact = manifest["exact_build"]
    run = manifest["run"]
    source = manifest["source"]
    files = {
        name: Path(value["path"]).expanduser().resolve()
        for name, value in candidate["files"].items()
    }
    expected_hashes = {
        name: str(value["sha256"]).upper()
        for name, value in candidate["files"].items()
    }
    actual_hashes = {
        name: sha256_file(path) if path.is_file() else None
        for name, path in files.items()
    }
    game_exe = Path(exact["executable_path"]).expanduser().resolve()
    game_data = game_exe.read_bytes()
    image = pefile.PE(data=game_data, fast_load=True)
    anchor_matches = []
    for rva, expected in ANCHORS:
        offset = image.get_offset_from_rva(rva)
        anchor_matches.append(game_data[offset : offset + len(expected)] == expected)

    private_data = files["private_dll"].read_bytes()
    default_data = files["default_dll"].read_bytes()
    source_zip = files["source_zip"]
    with zipfile.ZipFile(source_zip) as archive:
        names = set(archive.namelist())
        cmake = archive.read(
            "ck3_autonomous_player/native_bridge/CMakeLists.txt"
        ).decode("utf-8")
    private_option_default_off = bool(
        re.search(
            r"option\(\s*XAR_CK3_ENABLE_G2_TRUCE_NATIVE_CALLSITE_OBSERVER_V1"
            r".*?\sOFF\s*\)",
            cmake,
            re.DOTALL,
        )
    )
    direct_combination_rejected = (
        "XAR_CK3_ENABLE_G2_TRUCE_PRIVATE_CAPTURE_V1 AND" in cmake
        and "cannot be combined with direct evaluator capture" in cmake
    )
    required_source_files = {
        "ck3_autonomous_player/native_bridge/include/xar_bridge/"
        "g2_truce_native_callsite_observer_v1.hpp",
        "ck3_autonomous_player/native_bridge/src/"
        "g2_truce_native_callsite_observer_v1.cpp",
        "ck3_autonomous_player/native_bridge/research/"
        "g2_truce_native_callsite_observer_v1_abi.json",
    }
    inventory_before = process_inventory()
    attempt = Path(run["attempt_dir"]).expanduser().resolve()
    command = str(run["unique_powershell_command"])
    checks = {
        "source_commit_exact": source.get("commit") == EXPECTED_SOURCE_COMMIT,
        "all_frozen_files_exist": all(path.is_file() for path in files.values()),
        "all_frozen_hashes_match": actual_hashes == expected_hashes,
        "source_zip_contains_observer_contract": required_source_files <= names,
        "private_option_default_off_in_source": private_option_default_off,
        "direct_capture_combination_rejected": direct_combination_rejected,
        "private_marker_present": PRIVATE_MARKER in private_data,
        "default_marker_absent": PRIVATE_MARKER not in default_data,
        "game_executable_hash_matches": hashlib.sha256(game_data).hexdigest().upper()
        == EXPECTED_EXE_SHA256
        == str(exact["executable_sha256"]).upper(),
        "two_exact_anchors_match": anchor_matches == [True, True],
        "report_schema_frozen": manifest.get("report_schema")
        == "ck3_g2_truce_native_callsite_observer_live_acceptance",
        "heartbeat_schema_frozen": manifest.get("heartbeat_schema")
        == "g2_truce_native_callsite_observer_v1",
        "readiness_timeout_exactly_300": run.get("readiness_timeout_seconds")
        == 300,
        "total_timeout_exactly_420": run.get("timeout_seconds") == 420,
        "observation_timeout_exactly_60": run.get("observation_timeout_seconds")
        == 60,
        "fresh_attempt_absent": not attempt.exists(),
        "slot_empty_before_preflight": not inventory_before["ck3.exe"]
        and not inventory_before["ck3_probe.exe"],
        "unique_command_uses_project_venv": (
            "Z:\\ck3_mod_rewrite\\tools\\.venv\\Scripts\\python.exe" in command
        ),
        "unique_command_uses_passive_runner": (
            "run_g2_truce_native_callsite_observer_live.py" in command
        ),
        "unique_command_has_no_direct_capture_environment": (
            "XAR_CK3_G2_TRUCE_PRIVATE_CAPTURE" not in command
        ),
        "unique_command_has_no_war_or_context_action": all(
            token not in command.lower()
            for token in ("surrender", "white-peace", "enforce", "context-effect")
        ),
    }
    inventory_after = process_inventory()
    checks["preflight_did_not_launch_ck3"] = inventory_after == inventory_before
    checks["fresh_attempt_still_absent"] = not attempt.exists()
    return {
        "schema": "xar.ck3.g2_truce_native_callsite_observer_no_launch_preflight.v1",
        "status": "READY_TO_LIVE" if all(checks.values()) else "RED",
        "ok": all(checks.values()),
        "manifest_path": str(manifest_path),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest().upper(),
        "checks": checks,
        "actual_sha256": actual_hashes,
        "anchor_matches": anchor_matches,
        "process_inventory_before": inventory_before,
        "process_inventory_after": inventory_after,
        "boundaries": {
            "ck3_started": False,
            "direct_evaluator_enabled": False,
            "context_effect_executed": False,
            "mutation_executed": False,
            "public_abi_changed": False,
            "public_readiness_changed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.manifest)
    write_json_atomic(args.output.expanduser().resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
