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
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp", "religion_doctrine12002_tenet_rows.cpp",
        "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp",
        "protocol.cpp", "religion_doctrine12002_tenet_rows_mailbox.cpp",
        "religion_doctrine12002_tenet_rows_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "religion_doctrine12002_tenet_rows.hpp", "religion_doctrine12002_tenet_rows_mailbox.hpp",
        "ck3_12002_religion_context.hpp", "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp")]
    pins.append(native / "src/religion_doctrine12002_tenet_rows_test.cpp")
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        executable = target / "tenet-rows-mailbox-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
            "/" + mode, "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1=1",
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
        wire_paths = [target / name for name in ("current-main-personal.json", "known-empty-personal.json",
            "personal-without-rite.json", "tenet-state-unavailable.json")]
        packets = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in wire_paths}
        for packet in packets.values():
            result = packet["result"]
            context = result["player_religion_tenets"]
            assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
            assert packet["request_id"] == 'religion"mailbox-fixture'
            assert result["step"] == "query-player-religion-tenets-v1"
            assert result["domain_key"] == "player_religion_tenets_v1"
            assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-tenets-v1"
            assert result["accepted"] and result["private_build"] and result["read_only"]
            assert result["advertised"] is False and result["snapshot_revision"] == 701
            assert result["date_raw"] == context["date_raw"] == 53175816
            assert context["capture_epoch"] > 0 and context["capture_epoch"] != result["snapshot_revision"]
            assert context["played_character_id"] == 0x03000004
            assert result["status"] == ("observed" if context["available"] else "unavailable")
        current = packets["current-main-personal.json"]["result"]["player_religion_tenets"]
        assert current["current_rite"]["rite_id"] == 0 and current["faith_main_rite"]["rite_id"] == 0x82000002
        assert current["current_rite"]["core_tenets"] == [{"key":"tenet_4","current_rite_status":4}]
        assert current["personal_tenets"][0] == {"key":"tenet_0","current_rite_status":0}
        assert [x["current_rite_status"] for x in current["effective_tenet_states"]] == [4,3,0,1,2]
        empty = packets["known-empty-personal.json"]["result"]["player_religion_tenets"]
        assert empty["available"] and empty["personal_tenets_complete"] and empty["personal_tenets"] == []
        absent = packets["personal-without-rite.json"]["result"]["player_religion_tenets"]
        assert absent["available"] and absent["current_rite"] is None and absent["personal_tenets"][0]["current_rite_status"] is None
        missing = packets["tenet-state-unavailable.json"]["result"]["player_religion_tenets"]
        assert not missing["available"] and not missing["personal_tenets_complete"]
        assert missing["unavailable_reason"] == "tenet_state_unavailable"
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
            "actual_wire_sha256": {p.name: digest(p) for p in wire_paths},
            "fixture_executable_sha256": digest(executable)})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_native_core": True, "actual_tenet_rows_provider": True,
        "actual_mailbox_submit_drain_wait_reclaim": True, "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Synthetic objects and canonical getter behavior in owned fixture memory",
        "fixture_adapter_unwrap": "Bare GameAdapter identity branch only; no WorkerAdapter implementation substituted",
        "fixture_executor_permit": "Existing primary fixture permit with owned memory; deployed named permit is registered by central owner",
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(p.relative_to(root)): digest(p) for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
