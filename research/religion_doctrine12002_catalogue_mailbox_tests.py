#!/usr/bin/env python3
"""Run the actual new catalogue mailbox and full protocol packet once in O2."""
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
        "religion_doctrine12002_catalogue_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / n for n in (
        "religion_doctrine12002_catalogue.hpp", "religion_doctrine12002_catalogue_mailbox.hpp",
        "main_thread_query_mailbox_v1.hpp", "ck3_12002_query_mailbox.hpp")]
    temp = out / "tmp"; temp.mkdir(exist_ok=True); exe = out / "doctrine-catalogue-mailbox-test.exe"
    command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/utf-8", "/O2",
        "/W4", "/WX", "/I" + str(native / "include"),
        "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1=1",
        "/DXAR_CATALOGUE_MAILBOX_STANDALONE_ADAPTER=1", *map(str, sources), "/Fe:" + str(exe),
        "/link", "user32.lib"])
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
    if run.returncode: raise RuntimeError("Fixture failed: " + str(out / "test.log"))
    paths = [out / n for n in ("loaded-catalogue.json", "known-empty.json", "database-unavailable.json")]
    packets = {x.name: json.loads(x.read_text(encoding="utf-8")) for x in paths}
    for packet in packets.values():
        assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"]
        assert packet["request_id"] == 'catalogue"mailbox-fixture'
        result = packet["result"]; dto = result["player_religion_doctrine_catalogue"]
        assert result["step"] == "query-player-religion-doctrine-catalogue-v1"
        assert result["domain_key"] == "player_religion_doctrine_catalogue_v1"
        assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-doctrine-catalogue-v1"
        assert result["accepted"] and result["private_build"] and result["read_only"] and not result["advertised"]
        assert result["snapshot_revision"] == 701 and result["date_raw"] == dto["date_raw"] == 53175816
        assert dto["played_character_id"] == 0x03000004 and dto["capture_epoch"] > 0
        assert dto["capture_epoch"] != result["snapshot_revision"]
        assert result["status"] == ("observed" if dto["available"] else "unavailable")
    loaded = packets["loaded-catalogue.json"]["result"]["player_religion_doctrine_catalogue"]
    assert loaded["catalogue_complete"] and len(loaded["rows"]) == 3
    assert loaded["rows"][2]["doctrine_key"] == 'mod_custom_doctrine"信'
    assert loaded["source"] == loaded["rows"][2]["source"] == "loaded_doctrine_registry"
    absent = packets["database-unavailable.json"]["result"]["player_religion_doctrine_catalogue"]
    assert not absent["catalogue_complete"] and absent["unavailable_reason"] == "doctrine_database_unavailable"
    sha = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
    receipt = {"status": "GREEN", "readiness": "static-ready", "local_ck3_touched": False,
        "live_verified": False, "actual_provider": True, "actual_mailbox_submit_drain_wait_reclaim": True,
        "actual_protocol1_command_result_serializer": True, "compiler": "MSVC /O2 /W4 /WX",
        "stdout": run.stdout.strip(), "actual_cpp_wire_cases": len(paths),
        "fixture_executor_permit": "Existing offline primary permit; new central named slot separate",
        "fixture_adapter_unwrap": "Bare native adapter identity shim; no WorkerAdapter production substitute",
        "source_sha256": {str(x.relative_to(root)): sha(x) for x in pins},
        "wire_sha256": {x.name: sha(x) for x in paths}, "fixture_executable_sha256": sha(exe)}
    (out / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(run.stdout.strip()); return 0

if __name__ == "__main__": raise SystemExit(main())
