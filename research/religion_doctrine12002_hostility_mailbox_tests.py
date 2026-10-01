#!/usr/bin/env python3
"""Exercise the actual read-only hostility mailbox/runtime/wrapper offline."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / "ck3_autonomous_player/native_bridge"
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installed = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp", "ck3_12002_query_mailbox.cpp",
        "main_thread_query_mailbox_v1.cpp", "protocol.cpp", "religion_doctrine12002_hostility.cpp",
        "religion_doctrine12002_hostility_mailbox.cpp", "religion_doctrine12002_hostility_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "ck3_12002.hpp", "ck3_12002_religion_context.hpp", "ck3_12002_query_mailbox.hpp",
        "main_thread_query_mailbox_v1.hpp", "religion_doctrine12002_hostility.hpp",
        "religion_doctrine12002_hostility_mailbox.hpp")]
    runs = []
    wire_names = ("asymmetric.json", "same-faith.json", "zero-target-id.json",
                  "target-unavailable.json", "native-sentinel.json")
    for mode in ("Od", "O2"):
        target = output / mode; target.mkdir(exist_ok=True)
        temp = target / "tmp"; temp.mkdir(exist_ok=True)
        executable = target / "hostility-mailbox-test.exe"
        command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/" + mode,
            "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
            "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1=1",
            "/DXAR_HOSTILITY_MAILBOX_STANDALONE_ADAPTER=1", *map(str, sources),
            "/Fe:" + str(executable), "/link", "user32.lib"])
        batch = target / "build.cmd"
        batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
            command + "\nexit /b %errorlevel%\n", encoding="utf-8")
        env = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=target, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        (target / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
        if build.returncode: raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(executable), str(target)], cwd=target, env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode: raise RuntimeError("Mailbox fixture failed: " + str(target / "test.log"))
        wire_paths = [target / name for name in wire_names]
        packets = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in wire_paths}
        for packet in packets.values():
            result = packet["result"]; inner = result["player_religion_hostility"]
            require(packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"], "Full protocol response")
            require(packet["request_id"] == 'hostility"mailbox-fixture', "Request ID escaping")
            require(result["step"] == "query-player-religion-hostility-v1" and
                    result["domain_key"] == "player_religion_hostility_v1" and
                    result["backend_id"] == "ck3-1.20.0.2-native-player-religion-hostility-v1", "Exact route identity")
            require(result["accepted"] and result["private_build"] and result["read_only"] and not result["advertised"], "Private read-only metadata")
            require(result["snapshot_revision"] == 701 and result["date_raw"] == inner["date_raw"] == 53175816,
                    "Published revision and actual frame date")
            require(inner["capture_epoch"] > 0 and inner["capture_epoch"] != result["snapshot_revision"] and
                    inner["played_character_id"] == 0x03000004, "Source is actual played actor / owner epoch")
            require(result["status"] == ("observed" if inner["available"] else "unavailable"), "Typed status follows actual provider")
        a = packets["asymmetric.json"]["result"]["player_religion_hostility"]
        require(a["target_rite_id"] == 0x83000002 and a["actor_rite_id"] != a["actor_main_rite_id"] and
                [a[k] for k in ("actor_rite_towards_target", "target_rite_towards_actor", "actor_faith_towards_target", "target_faith_towards_actor")] == [2, 0, 3, 1],
                "Four independent native directions and full target ID")
        require([a[k] for k in ("actor_rite_towards_target_key", "target_rite_towards_actor_key", "actor_faith_towards_target_key", "target_faith_towards_actor_key")] ==
                ["hostile", "righteous", "evil", "astray"], "Exact stock level labels")
        same = packets["same-faith.json"]["result"]["player_religion_hostility"]
        require(same["same_faith"] and same["actor_rite_id"] != same["target_rite_id"] and
                same["actor_faith_towards_target"] == 0, "Same Faith differs from same Rite")
        zero = packets["zero-target-id.json"]["result"]["player_religion_hostility"]
        require(zero["available"] and zero["target_rite_id"] == 0, "Required target 0 is legal")
        for name, reason in (("target-unavailable.json", "target_rite_unavailable"),
                             ("native-sentinel.json", "native_level_unavailable")):
            inner = packets[name]["result"]["player_religion_hostility"]
            require(not inner["available"] and inner["unavailable_reason"] == reason and
                    inner["actor_rite_towards_target"] is None and inner["actor_rite_towards_target_key"] is None,
                    "Unavailable is distinct from legal level 0")
        runs.append({"mode": mode, "returncode": run.returncode, "stdout": run.stdout.strip(),
            "actual_wire_cases": len(wire_paths), "actual_wire_sha256": {p.name: digest(p) for p in wire_paths},
            "fixture_executable_sha256": digest(executable)})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "war_research": False, "actual_native_core": True,
        "actual_hostility_provider": True, "actual_mailbox_submit_drain_wait_reclaim": True,
        "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Fixture-owned objects and ABI callbacks; no running CK3",
        "fixture_adapter_unwrap": "Bare GameAdapter identity branch only; no WorkerAdapter implementation substituted",
        "fixture_executor_permit": "Existing primary permit; named religion_hostility12002 registration belongs to central next increment",
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(p.relative_to(root)): digest(p) for p in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
