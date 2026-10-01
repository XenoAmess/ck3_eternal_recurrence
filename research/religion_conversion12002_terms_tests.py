#!/usr/bin/env python3
"""Offline fixture: actual conversion terms and main-thread mailbox response."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_religion_conversion_rite.cpp",
        "ck3_12002_religion_conversion_cost.cpp", "ck3_12002_religion_conversion_terms.cpp",
        "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp", "protocol.cpp",
        "ck3_12002_religion_conversion_mailbox.cpp", "ck3_12002_religion_conversion_terms_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "ck3_12002_religion_conversion_rite.hpp", "ck3_12002_religion_conversion_cost.hpp",
        "ck3_12002_religion_conversion_terms.hpp", "ck3_12002_religion_conversion_mailbox.hpp",
        "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp")]
    cases = ("permitted.json", "native-rule-rejected.json", "piety-short.json",
             "current-rite.json", "target-unavailable.json", "cost-unavailable.json")
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        executable = target / "religion-conversion-terms-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
            "/" + mode, "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            "/DXAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1",
            "/DXAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1", *map(str, sources),
            "/Fe:" + str(executable), "/link", "user32.lib"])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        environment = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=environment,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode:
            raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target, env=environment,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        packets = {name: json.loads((target / name).read_text(encoding="utf-8")) for name in cases}
        for packet in packets.values():
            result = packet["result"]
            terms = result["player_religion_conversion_terms"]
            assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
            assert packet["request_id"] == 'religion-conversion"mailbox-fixture'
            assert result["step"] == "query-player-religion-conversion-terms-v1"
            assert result["domain_key"] == "player_religion_conversion_terms_v1"
            assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-conversion-terms-v1"
            assert result["accepted"] and result["private_build"] and result["read_only"]
            assert result["advertised"] is False and result["snapshot_revision"] == 701
            assert result["date_raw"] == terms["date_raw"] == 53175816
            assert terms["capture_epoch"] > 0 and terms["capture_epoch"] != result["snapshot_revision"]
            assert terms["played_character_id"] == 0x03000004
            assert terms["schema"] == "ck3_12002_religion_conversion_terms_v1"
            assert terms["native_blocker_text_available"] is False
            assert result["status"] == ("observed" if terms["available"] else "unavailable")
        permitted = packets["permitted.json"]["result"]["player_religion_conversion_terms"]
        assert permitted["can_convert"] is True
        assert permitted["cost"]["piety_points"] == 377 and permitted["cost"]["piety_cost_raw"] == 37_700_000
        rejected = packets["native-rule-rejected.json"]["result"]["player_religion_conversion_terms"]
        assert rejected["cost"]["can_afford_piety"] is True and rejected["can_convert"] is False
        short = packets["piety-short.json"]["result"]["player_religion_conversion_terms"]
        assert short["final_gate"]["validator_without_payment"] and short["final_gate"]["validator_with_payment"] is False
        assert short["can_convert"] is False
        current = packets["current-rite.json"]["result"]["player_religion_conversion_terms"]
        assert current["target_rite_id"] == 0 and current["can_convert"] is False
        for name in ("target-unavailable.json", "cost-unavailable.json"):
            absent = packets[name]["result"]["player_religion_conversion_terms"]
            assert absent["available"] is False and absent["can_convert"] is None
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
            "actual_wire_sha256": {name: digest(target / name) for name in cases},
            "fixture_executable_sha256": digest(executable)})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_native_core": True, "actual_conversion_components": True,
        "actual_terms_aggregate": True, "actual_mailbox_submit_drain_wait_reclaim": True,
        "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Synthetic native predicate/cost and objects in owned fixture memory",
        "fixture_executor_permit": "Existing primary permit; production needs central named conversion registration",
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(p.relative_to(root)): digest(p) for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
