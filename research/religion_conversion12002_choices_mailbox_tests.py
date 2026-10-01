#!/usr/bin/env python3
"""Actual conversion candidates/providers and mailbox fixture, without CK3."""
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_religion_conversion_faith.cpp", "ck3_12002_religion_conversion_rite.cpp",
        "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp", "protocol.cpp",
        "ck3_12002_religion_conversion_choices_mailbox.cpp", "ck3_12002_religion_conversion_choices_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "ck3_12002_religion_conversion_faith.hpp", "ck3_12002_religion_conversion_rite.hpp",
        "ck3_12002_religion_conversion_choices_mailbox.hpp", "ck3_12002_query_mailbox.hpp",
        "main_thread_query_mailbox_v1.hpp")]
    cases = ("choices.json", "empty.json", "faith-unavailable.json", "rites-unavailable.json",
             "both-unavailable.json")
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        exe = target / "religion-conversion-choices-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
            "/" + mode, "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            "/DXAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1",
            "/DXAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1", *map(str, sources),
            "/Fe:" + str(exe), "/link", "user32.lib"])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        environment = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=environment,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(exe), str(target)], cwd=target, env=environment,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        packets = {name: json.loads((target / name).read_text(encoding="utf-8")) for name in cases}
        for packet in packets.values():
            result = packet["result"]; out = result["player_religion_conversion_choices"]
            assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
            assert packet["request_id"] == 'religion-choices"mailbox-fixture'
            assert result["step"] == "query-player-religion-conversion-choices-v1"
            assert result["domain_key"] == "player_religion_conversion_choices_v1"
            assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-conversion-choices-v1"
            assert result["accepted"] and result["private_build"] and result["read_only"] and not result["advertised"]
            assert result["snapshot_revision"] == 801
            assert result["date_raw"] == out["date_raw"] == 53175816
            assert out["capture_epoch"] > 0 and out["capture_epoch"] != result["snapshot_revision"]
            assert out["played_character_id"] == 0x03000004
            assert out["schema"] == "ck3_12002_religion_conversion_choices_v1"
            assert out["membership_is_legality"] is False
            assert result["status"] == ("observed" if out["available"] else "unavailable")
            for key in ("faith_choices", "current_faith_rites"):
                component = out[key]
                assert component["date_raw"] == out["date_raw"]
                assert component["played_character_id"] == out["played_character_id"]
                assert component["capture_epoch"] == out["capture_epoch"]
        positive = packets["choices.json"]["result"]["player_religion_conversion_choices"]
        assert positive["faith_choices"]["choices"][1]["main_rite_id"] == 0x84000001
        assert positive["faith_choices"]["choices"][1]["faith_key"] == 'target"faith'
        assert positive["current_faith_rites"]["rite_ids"] == [0, 0xB0000003]
        assert positive["faith_choices"]["rule_only"] is True
        empty = packets["empty.json"]["result"]["player_religion_conversion_choices"]
        assert empty["available"] and empty["faith_choices"]["choices"] == [] and empty["current_faith_rites"]["rite_ids"] == []
        failed_faith = packets["faith-unavailable.json"]["result"]["player_religion_conversion_choices"]
        assert not failed_faith["available"] and not failed_faith["faith_choices"]["available"]
        assert failed_faith["faith_choices"]["current_faith_id"] is None and failed_faith["current_faith_rites"]["available"]
        failed_rites = packets["rites-unavailable.json"]["result"]["player_religion_conversion_choices"]
        assert not failed_rites["available"] and failed_rites["faith_choices"]["available"]
        assert not failed_rites["current_faith_rites"]["available"] and failed_rites["current_faith_rites"]["faith_id"] == 0xFFFFFFFF
        runs.append({"mode": mode, "stdout": run.stdout.strip(), "actual_wire_cases": len(packets),
            "wire_sha256": {name: digest(target / name) for name in cases}, "fixture_executable_sha256": digest(exe)})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_native_core": True, "actual_faith_and_rite_providers": True,
        "actual_mailbox_submit_drain_wait_reclaim": True, "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Fixture-owned native callbacks and objects; no CK3 function calls",
        "fixture_executor_permit": "Actual permitted_executor_religion_conversion_choices12002 named slot with fixture-owned memory",
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(path.relative_to(root)): digest(path) for path in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__": raise SystemExit(main())
