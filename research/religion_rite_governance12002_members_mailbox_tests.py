#!/usr/bin/env python3
"""Member worker -> owner mailbox -> actual provider -> protocol wire; no CK3 access."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"
STEM = "religion_rite_governance12002_members_mailbox"
SOURCE_NAMES = ("ck3_12002.cpp", "religion_rite_governance12002_organization_members.cpp",
                "main_thread_query_mailbox_v1.cpp", "ck3_12002_query_mailbox.cpp",
                "protocol.cpp", STEM + ".cpp")
WIRE_NAMES = ("current-members.json", "known-empty.json", "title-unavailable.json", "legal-no-rite.json")
EXE_SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def developer_shell() -> Path:
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    require(bool(installed), "MSVC developer shell unavailable")
    return Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"


def batch(shell: Path, target: Path, command: list[str], tag: str) -> None:
    path = target / (tag + ".cmd")
    path.write_text('@echo off\ncall "' + str(shell) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
        subprocess.list2cmdline(command) + '\nexit /b %errorlevel%\n', encoding="utf-8")
    temp = target / "temp"; temp.mkdir(exist_ok=True)
    run = subprocess.run(["cmd.exe", "/d", "/c", str(path)], cwd=target,
        env=dict(os.environ, TEMP=str(temp), TMP=str(temp)), capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=180)
    (target / (tag + ".log")).write_text(run.stdout + run.stderr, encoding="utf-8")
    require(run.returncode == 0, "MSVC failed: " + str(target / (tag + ".log")))


def validate_wire(directory: Path) -> dict[str, str]:
    pins = {}
    for name in WIRE_NAMES:
        path = directory / name
        packet = json.loads(path.read_text(encoding="utf-8"))
        require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and
            packet["ok"] is True and packet["request_id"] == 'members"worker-fixture', "actual full protocol and escaped request")
        result = packet["result"]; out = result["player_rite_members"]
        require(result["step"] == "query-player-rite-members-v1" and result["domain_key"] == "player_rite_members_v1" and
            result["backend_id"] == "ck3-1.20.0.2-native-player-rite-members-v1" and result["accepted"] is True and
            result["private_build"] is True and result["read_only"] is True and result["advertised"] is False and
            result["game_version"] == "1.20.0.2" and result["executable_sha256"] == EXE_SHA and
            result["snapshot_revision"] == 701 and result["date_raw"] == 53175816, "actual transport result identity/frame")
        require(out["schema"] == "ck3_12002_rite_organization_members_v1" and out["game_version"] == "1.20.0.2" and
            out["executable_sha256"] == EXE_SHA and out["scope"] == "current_player_rite_and_its_faith" and
            out["date_raw"] == 53175816 and out["played_character_id"] == 0x03000004 and
            out["capture_epoch"] != 701, "actual native DTO frame and distinct owner epoch")
        unavailable = name == "title-unavailable.json"
        require(result["status"] == ("unavailable" if unavailable else "observed") and
            out["available"] is not unavailable, "known empty differs from unavailable native source")
        if name == "current-members.json":
            require(out["rite_id"] == 0x85000003 and out["faith_id"] == 0x83000002 and out["religion_id"] == 0x84000005 and
                out["faith_character_ids"] == [0x03000004, 0x87000005, 0x88000006] and
                out["rite_character_ids"] == [0x03000004, 0x88000006] and
                out["county_title_ids"] == [0x89000002], "actual full generation IDs and separate Faith/Rite scopes")
        elif name == "known-empty.json":
            require(out["faith_character_ids"] == out["rite_character_ids"] == out["county_title_ids"] == [] and
                out["unavailable_reason"] is None and out["rite_id"] == 0x85000003, "actual observed empty source")
        elif name == "title-unavailable.json":
            require(out["county_title_ids"] == [] and out["unavailable_reason"] == "county_title_unavailable",
                "actual collector source failure survives wire")
        else:
            require(out["rite_id"] is None and out["faith_id"] is None and out["religion_id"] is None and
                out["faith_character_ids"] == out["rite_character_ids"] == out["county_title_ids"] == [] and
                out["unavailable_reason"] is None, "actual legal no Rite remains available and null")
        pins[name] = sha(path)
    require(not (directory / "frame-changed.json").exists(), "changed owner frame must emit no success wire")
    rejection_path = directory / "frame-changed-rejection.json"
    rejection = json.loads(rejection_path.read_text(encoding="utf-8"))
    require(rejection["success_wire_emitted"] is False and rejection["mailbox_reclaimed"] is True and
        bool(rejection["failure"]), "actual owner post-read changed frame rejection and reclamation")
    pins[rejection_path.name] = sha(rejection_path)
    return pins


def run_mode(shell: Path, output: Path, mode: str) -> dict:
    target = output / mode; target.mkdir(parents=True, exist_ok=True)
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8", "/DNOMINMAX", "/" + mode,
        "/DXAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1=1", "/DXAR_RITE_MEMBERS_MAILBOX_STANDALONE_ADAPTER=1",
        "/I" + str(NATIVE / "include")]
    batch(shell, target, compiler + ["/c", "/MP16"] + [str(NATIVE / "src" / name) for name in SOURCE_NAMES], "compile")
    executable = target / "members-mailbox-test.exe"
    batch(shell, target, compiler + [str(NATIVE / "src" / (STEM + "_test.cpp"))] +
        [str(target / Path(name).with_suffix(".obj")) for name in SOURCE_NAMES] + ["User32.lib", "/Fe:" + str(executable)], "link")
    wire = target / "wire"; wire.mkdir(exist_ok=True)
    run = subprocess.run([str(executable), str(wire)], cwd=target, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=15)
    (target / "run.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    require(run.returncode == 0, "Actual member mailbox fixture failed: " + str(target / "run.log"))
    return {"mode": mode, "compile": "GREEN_W4_WX", "stdout": run.stdout.strip(),
        "executable_sha256": sha(executable), "actual_wire_sha256": validate_wire(wire)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve(); output.mkdir(parents=True, exist_ok=True)
    shell = developer_shell()
    pins = [NATIVE / "src" / name for name in SOURCE_NAMES + (STEM + "_test.cpp",)] + [
        NATIVE / "include/xar_bridge" / (STEM + ".hpp"), NATIVE / "src/religion_rite_governance12002_organization_members_test.cpp"]
    source_sha = {p.relative_to(ROOT).as_posix(): sha(p) for p in pins}
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda mode: run_mode(shell, output, mode), ("Od", "O2")))
    except Exception as error:
        attempt = {"status": "RED", "kind": "harness", "time_utc": datetime.now(timezone.utc).isoformat(),
            "error": str(error), "local_ck3_touched": False, "live_verified": False, "source_sha256": source_sha}
        attempts = list(output.glob("attempt-*.json"))
        (output / ("attempt-%03d.json" % (len(attempts) + 1))).write_text(json.dumps(attempt, indent=2) + "\n", encoding="utf-8")
        raise
    result = {"schema": "xar.ck3.religion-rite-members-mailbox-fixture/v1", "status": "GREEN",
        "time_utc": datetime.now(timezone.utc).isoformat(), "results": results, "source_sha256": source_sha,
        "first_component_matrix_repeated": False,
        "actual_pipeline": "worker TrySubmit -> owner ObservePumpDrain -> actual Core/member provider -> Wait/Reclaim -> command_result serializer -> Python JSON decoder",
        "native_collector_callbacks": "fixture-owned; existing exact-build PE proof reused",
        "mailbox_permit": "existing primary offline permitted_executor; central named permitted_executor_rite_members12002 pending",
        "dedicated_production_registration_tested": False, "local_ck3_touched": False,
        "live_verified": False, "readiness": "static-ready"}
    path = output / "result.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(path), "result_sha256": sha(path), "runs": [r["stdout"] for r in results]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
