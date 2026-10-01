#!/usr/bin/env python3
"""Run the real religion provider, mailbox and JSON response path offline."""
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
    parser.add_argument("--mode", choices=("Od", "O2"), help="Run only the selected compiler mode")
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
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp",
        "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp",
        "protocol.cpp", "ck3_12002_religion_mailbox.cpp",
        "ck3_12002_religion_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "ck3_12002_religion_context.hpp", "ck3_12002_religion_mailbox.hpp",
        "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp")]
    runs = []
    modes = (args.mode,) if args.mode else ("Od", "O2")
    for mode in modes:
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        executable = target / "religion-mailbox-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
            "/" + mode, "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1=1",
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
        wire_paths = [target / name for name in ("current-zero.json", "signed-values.json",
            "native-default.json", "legal-absent.json", "faith-unavailable.json", "fervor-unavailable.json")]
        packets = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in wire_paths}
        for packet in packets.values():
            result = packet["result"]
            context = result["player_religion_context"]
            assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
            assert packet["request_id"] == 'religion"mailbox-fixture'
            assert result["step"] == "query-player-religion-context-v1"
            assert result["domain_key"] == "player_religion_context_v1"
            assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-context-v1"
            assert result["accepted"] and result["private_build"] and result["read_only"]
            assert result["advertised"] is False and result["snapshot_revision"] == 701
            assert result["date_raw"] == context["date_raw"] == 53175816
            assert context["capture_epoch"] > 0 and context["capture_epoch"] != result["snapshot_revision"]
            assert context["played_character_id"] == 0x03000004 and context["raw_scale"] == 100000
            assert result["status"] == ("observed" if context["available"] else "unavailable")
        zero = packets["current-zero.json"]["result"]["player_religion_context"]
        assert zero["rite_id"] == zero["faith_fervor_raw"] == zero["spiritual_fulfillment_raw"] == 0
        assert zero["religion_id"] == 0x84000005 and zero["faith_id"] == 0x83000003
        assert zero["faith_main_rite_id"] != zero["rite_id"] and zero["faith_key"] == 'faith"信'
        assert zero["religion_key"] == "christianity_religion"
        signed = packets["signed-values.json"]["result"]["player_religion_context"]
        assert signed["faith_fervor_raw"] == -123456 and signed["spiritual_fulfillment_raw"] == 345678
        absent = packets["legal-absent.json"]["result"]["player_religion_context"]
        assert absent["available"] and absent["rite_id"] is None and absent["faith_fervor_raw"] is None
        missing = packets["faith-unavailable.json"]["result"]["player_religion_context"]
        assert not missing["available"] and missing["unavailable_reason"] == "faith_unavailable"
        assert missing["faith_fervor_raw"] is None and missing["rite_id"] is None
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
            "actual_wire_sha256": {p.name: digest(p) for p in wire_paths},
            "fixture_executable_sha256": digest(executable)})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_native_core": True, "actual_religion_provider": True,
        "actual_mailbox_submit_drain_wait_reclaim": True, "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Synthetic objects and canonical getter behavior in owned fixture memory",
        "fixture_adapter_unwrap": "Bare GameAdapter identity branch only; no WorkerAdapter implementation substituted",
        "fixture_executor_permit": "Actual permitted_executor_religion12002 named slot with fixture-owned memory",
        "compiler": "MSVC /W4 /WX " + " and ".join("/" + mode for mode in modes), "runs": runs,
        "source_sha256": {str(p.relative_to(root)): digest(p) for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
