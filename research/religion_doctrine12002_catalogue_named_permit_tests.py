#!/usr/bin/env python3
"""Verify only the new catalogue named executor admission/queue path in O2."""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path
import subprocess

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", required=True, type=Path)
    a = p.parse_args(); out = a.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parent.parent; native = root / "ck3_autonomous_player/native_bridge"
    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
    install = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / n for n in ("ck3_12002.cpp", "religion_doctrine12002_intrinsic.cpp",
        "religion_doctrine12002_catalogue.cpp", "ck3_12002_query_mailbox.cpp",
        "main_thread_query_mailbox_v1.cpp", "protocol.cpp", "religion_doctrine12002_catalogue_mailbox.cpp",
        "religion_doctrine12002_catalogue_named_permit_test.cpp")]
    pins = sources + [native / "src/religion_doctrine12002_catalogue_mailbox_test.cpp"] + [
        native / "include/xar_bridge" / n for n in (
        "religion_doctrine12002_catalogue.hpp", "religion_doctrine12002_catalogue_mailbox.hpp",
        "main_thread_query_mailbox_v1.hpp", "ck3_12002_query_mailbox.hpp")]
    defines = ["XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1=1",
               "XAR_CATALOGUE_MAILBOX_STANDALONE_ADAPTER=1"]
    temp = out / "tmp"; temp.mkdir(exist_ok=True); exe = out / "catalogue-named-permit-test.exe"
    command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/utf-8", "/O2",
        "/W4", "/WX", "/I" + str(native / "include"), *["/D" + v for v in defines],
        *map(str, sources), "/Fe:" + str(exe), "/link", "user32.lib"])
    batch = out / "build.cmd"
    batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' + command + '\nexit /b %errorlevel%\n', encoding="utf-8")
    build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=out,
        env=dict(os.environ, TEMP=str(temp), TMP=str(temp)), capture_output=True,
        text=True, encoding="utf-8", errors="replace")
    (out / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    if build.returncode: raise RuntimeError("Compile failed: " + str(out / "build.log"))
    run = subprocess.run([str(exe), str(out)], cwd=out, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=60)
    (out / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode: raise RuntimeError("Named fixture failed: " + str(out / "test.log"))
    packet_path = out / "named-loaded-catalogue.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"]
    result = packet["result"]; dto = result["player_religion_doctrine_catalogue"]
    assert result["step"] == "query-player-religion-doctrine-catalogue-v1" and result["read_only"]
    assert dto["available"] and dto["catalogue_complete"] and len(dto["rows"]) == 3
    assert dto["rows"][2]["doctrine_key"] == 'mod_custom_doctrine"信'
    assert result["snapshot_revision"] == 701 and dto["played_character_id"] == 0x03000004
    sha = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
    receipt = {"status": "GREEN", "readiness": "static-ready", "local_ck3_touched": False,
        "live_verified": False, "named_permit_only": True, "old_matrix_main_executed": False,
        "old_provider_tests_executed": False, "actual_mailbox_submit_drain_wait_reclaim": True,
        "actual_protocol1_command_result_serializer": True, "compiler": "MSVC /O2 /W4 /WX",
        "stdout": run.stdout.strip(), "actual_cpp_wire_cases": 1,
        "fixture_executor_permit": "permitted_executor_religion_doctrine_catalogue12002",
        "primary_permit": "null", "defines": defines,
        "fixture_adapter_unwrap": "Bare native adapter identity shim; no WorkerAdapter production substitute",
        "source_sha256": {str(x.relative_to(root)): sha(x) for x in pins},
        "wire_sha256": {packet_path.name: sha(packet_path)}, "fixture_executable_sha256": sha(exe)}
    (out / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(run.stdout.strip()); return 0

if __name__ == "__main__": raise SystemExit(main())
