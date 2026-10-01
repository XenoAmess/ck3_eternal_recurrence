#!/usr/bin/env python3
"""Run the actual personal-parameter provider and owner queue offline once in /O2."""
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
        "religion_doctrine12002_personal_parameters.cpp", "religion_doctrine12002_tenet_rows.cpp",
        "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp", "protocol.cpp",
        "religion_doctrine12002_personal_parameters_mailbox.cpp",
        "religion_doctrine12002_personal_parameters_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "religion_doctrine12002_personal_parameters.hpp", "religion_doctrine12002_personal_parameters_mailbox.hpp",
        "religion_doctrine12002_tenet.hpp", "religion_doctrine12002_tenet_rows.hpp",
        "ck3_12002_religion_context.hpp", "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp")]
    pins.extend((native / "src/religion_doctrine12002_personal_parameters_test.cpp", Path(__file__)))
    target = output / "O2"
    target.mkdir(exist_ok=True)
    temp = target / "tmp"
    temp.mkdir(exist_ok=True)
    executable = target / "personal-parameters-mailbox-test.exe"
    command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
        "/O2", "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
        "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1=1",
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
    wire_paths = [target / name for name in (
        "personal-true-and-known-missing.json", "extension-absent.json", "empty-owned-tenets.json",
        "database-unavailable.json", "state-changed.json")]
    packets = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in wire_paths}
    for packet in packets.values():
        result = packet["result"]
        context = result["player_religion_personal_parameters"]
        assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
        assert packet["request_id"] == 'religion"mailbox-fixture'
        assert result["step"] == "query-player-religion-personal-parameters-v1"
        assert result["domain_key"] == "player_religion_personal_parameters_v1"
        assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-personal-parameters-v1"
        assert result["accepted"] and result["private_build"] and result["read_only"] and not result["advertised"]
        assert result["snapshot_revision"] == 701
        assert result["date_raw"] == context["date_raw"] == 53175816
        assert context["capture_epoch"] > 0 and context["capture_epoch"] != result["snapshot_revision"]
        assert context["played_character_id"] == 0x03000004
        assert result["status"] == ("observed" if context["available"] else "unavailable")
        assert context["schema"] == "ck3_12002_character_personal_parameters_v1"
        assert context["source"] == "character_personal_tenets"
        assert context["executable_sha256"] == result["executable_sha256"] == "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
        assert result["game_version"] == context["game_version"] == "1.20.0.2"
    key = "player_religion_personal_parameters"
    current = packets["personal-true-and-known-missing.json"]["result"][key]
    assert current["available"] and current["has_character_extension"]
    assert current["supported_keys_complete"] and current["personal_parameters_complete"] and current["personal_tenet_keys"]
    assert any(p["value"] is True for p in current["parameters"])
    assert any(p["value"] is False for p in current["parameters"])
    for name in ("extension-absent.json", "empty-owned-tenets.json"):
        observed = packets[name]["result"][key]
        assert observed["available"] and observed["supported_keys_complete"] and observed["personal_parameters_complete"]
        assert observed["personal_tenet_keys"] == [] and observed["parameters"]
        assert all(p["value"] is False for p in observed["parameters"])
        assert {p["key"] for p in observed["parameters"]} == {p["key"] for p in current["parameters"]}
    assert not packets["extension-absent.json"]["result"][key]["has_character_extension"]
    assert packets["empty-owned-tenets.json"]["result"][key]["has_character_extension"]
    for name, reason in (("database-unavailable.json", "parameter_registry_unavailable"), ("state-changed.json", "state_changed")):
        unavailable = packets[name]["result"][key]
        assert not unavailable["available"] and unavailable["unavailable_reason"] == reason
        assert not unavailable["supported_keys_complete"] and not unavailable["personal_parameters_complete"]
        assert unavailable["parameters"] == []
    record = {
        "status": "GREEN", "readiness": "static-ready", "live_verified": False, "local_ck3_touched": False,
        "actual_native_core": True, "actual_personal_parameters_provider": True,
        "frozen_provider_manifest": {
            "path": r"Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-doctrines\personal-parameters\delivery-result.json",
            "sha256": "bf5bafc634f0227610e34470fc9572e2e38b664621c895de1ff9a9022f83d72e"},
        "frozen_provider_receipt_sha256": "3ecaa82e1e08a7e3bc1a5c68e84c077fa65f7900c3ce4f6effe8b448aa918f21",
        "actual_mailbox_submit_drain_wait_reclaim": True, "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Frozen fixture-owned Character extension, personal Tenet definitions and native membership behavior",
        "fixture_adapter_unwrap": "Bare GameAdapter identity branch only; no WorkerAdapter implementation substituted",
        "fixture_executor_permit": "Existing primary fixture permit with owned memory; central owner registers deployed named permit",
        "old_reader_checks_executed": False, "compiler": "MSVC /O2 /W4 /WX",
        "runs": [{"mode": "O2", "returncode": run.returncode, "stdout": run.stdout.strip(),
                  "actual_wire_sha256": {p.name: digest(p) for p in wire_paths},
                  "fixture_executable_sha256": digest(executable)}],
        "source_sha256": {str(p.relative_to(root)).replace("\\", "/"): digest(p) for p in pins},
    }
    (output / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("O2", run.stdout.strip())
    print("GREEN five actual command_result packets parsed; local CK3 untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
