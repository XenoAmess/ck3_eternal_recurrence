#!/usr/bin/env python3
"""Run the actual current-Doctrine native mailbox and complete response path."""
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
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp",
        "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp", "protocol.cpp",
        "religion_doctrine12002_intrinsic.cpp", "religion_doctrine12002_rite.cpp",
        "religion_doctrine12002_tenet.cpp", "religion_doctrine12002_query.cpp",
        "religion_doctrine12002_mailbox.cpp", "religion_doctrine12002_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "ck3_12002_religion_context.hpp", "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp",
        "religion_doctrine12002_intrinsic.hpp", "religion_doctrine12002_rite.hpp",
        "religion_doctrine12002_tenet.hpp", "religion_doctrine12002_query.hpp",
        "religion_doctrine12002_mailbox.hpp")]
    pins.append(native / "src/religion_doctrine12002_query_test.cpp")
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        executable = target / "religion-doctrines-mailbox-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
            "/" + mode, "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1=1",
            *map(str, sources), "/Fe:" + str(executable), "/link", "user32.lib"])
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
        wire_paths = [target / name for name in ("current-scopes.json", "legal-zero-rite.json",
            "known-empty.json", "parameter-unavailable.json")]
        packets = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in wire_paths}
        for packet in packets.values():
            result = packet["result"]
            context = result["player_religion_doctrines"]
            if not (packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] and
                    result["step"] == "query-player-religion-doctrines-v1" and
                    result["domain_key"] == "player_religion_doctrines_v1" and
                    result["backend_id"] == "ck3-1.20.0.2-native-player-religion-doctrines-v1" and
                    result["accepted"] and result["private_build"] and result["read_only"] and
                    result["advertised"] is False and result["snapshot_revision"] == 701 and
                    result["date_raw"] == context["date_raw"] == 53175816 and
                    context["capture_epoch"] > 0 and context["capture_epoch"] != result["snapshot_revision"] and
                    context["played_character_id"] == 0x03000004 and
                    result["status"] == ("observed" if context["available"] else "unavailable")):
                raise ValueError("Actual C++ command_result envelope differs")
        positive = packets["current-scopes.json"]["result"]["player_religion_doctrines"]
        zero = packets["legal-zero-rite.json"]["result"]["player_religion_doctrines"]
        empty = packets["known-empty.json"]["result"]["player_religion_doctrines"]
        unavailable = packets["parameter-unavailable.json"]["result"]["player_religion_doctrines"]
        if not (positive["current_rite"]["rows"][0]["doctrine_key"] == 'doctrine_actor"礼' and
                positive["current_rite"]["rows"][0]["source"] == "rite_effective" and
                positive["faith_main_rite"]["rows"][0]["source"] == "faith_main_rite" and
                zero["available"] and zero["current_rite"]["rite_id"] == 0 and
                zero["boolean_parameters"]["current_rite"]["rite_id"] == 0 and
                empty["available"] and empty["current_rite"]["rows"] == [] and
                empty["faith_main_rite"]["rows"] == [] and
                not unavailable["available"] and
                unavailable["unavailable_reason"] == "boolean_parameters:parameter_key_unavailable"):
            raise ValueError("Actual complete C++ wire loses scope, zero, empty or unavailable semantics")
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
            "actual_wire_sha256": {path.name: digest(path) for path in wire_paths},
            "fixture_executable_sha256": digest(executable)})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_cross_provider_query": True,
        "actual_mailbox_submit_drain_wait_reclaim": True, "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Native-layout owned objects and canonical getter behavior in this fixture process",
        "fixture_adapter_unwrap": "Bare GameAdapter identity branch; WorkerAdapter is not simulated",
        "fixture_executor_permit": "Existing primary fixture permit; central named doctrine permit remains root-owned",
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {path.relative_to(root).as_posix(): digest(path) for path in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
