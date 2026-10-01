#!/usr/bin/env python3
"""Verify only the numeric named executor admission/queue delta in O2."""
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
    install = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(install) / "VC/Auxiliary/Build/vcvars64.bat"
    sources = [native / "src" / name for name in (
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp", "religion_doctrine12002_numeric.cpp",
        "religion_doctrine12002_numeric_final.cpp", "ck3_12002_query_mailbox.cpp",
        "main_thread_query_mailbox_v1.cpp", "protocol.cpp", "religion_doctrine12002_numeric_mailbox.cpp",
        "religion_doctrine12002_numeric_named_permit_test.cpp")]
    frozen_fixture = native / "src/religion_doctrine12002_numeric_mailbox_test.cpp"
    pins = sources + [frozen_fixture, native / "src/religion_doctrine12002_numeric_test.cpp",
        native / "src/religion_doctrine12002_numeric_final_test.cpp", Path(__file__)] + [
        native / "include/xar_bridge" / name for name in (
        "religion_doctrine12002_numeric.hpp", "religion_doctrine12002_numeric_final.hpp",
        "religion_doctrine12002_numeric_mailbox.hpp", "ck3_12002_religion_context.hpp",
        "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp")]
    fixture_bytes = frozen_fixture.read_bytes()
    main_entry = b"int main("
    assert fixture_bytes.count(main_entry) == 1
    generated_dir = output / "temp"
    generated_dir.mkdir(exist_ok=True)
    generated = generated_dir / "religion_doctrine12002_numeric_named_permit_fixture.inc"
    generated.write_bytes(fixture_bytes.replace(main_entry,
        b"int NumericMailboxCombinedMatrixUnused(", 1))
    defines = ["XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1=1",
               "XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1"]
    temp = output / "tmp"
    temp.mkdir(exist_ok=True)
    executable = output / "numeric-named-permit-test.exe"
    command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/utf-8",
        "/O2", "/W4", "/WX", "/I" + str(native / "include"), "/I" + str(native / "src"),
        "/I" + str(generated_dir), *["/D" + value for value in defines], *map(str, sources),
        "/Fe:" + str(executable), "/link", "user32.lib"])
    batch = output / "build.cmd"
    batch.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b %errorlevel%\n' +
        command + "\nexit /b %errorlevel%\n", encoding="utf-8")
    environment = dict(os.environ, TEMP=str(temp), TMP=str(temp))
    build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=output, env=environment,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    if build.returncode:
        raise RuntimeError("Compile failed: " + str(output / "build.log"))
    run = subprocess.run([str(executable), str(output)], cwd=output, env=environment,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    (output / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise RuntimeError("Named fixture failed: " + str(output / "test.log"))
    packet_path = output / "named-current-versus-main.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"]
    result = packet["result"]
    context = result["player_religion_numeric_special_parameters"]
    final = result["faith_numeric_final"]
    assert result["step"] == "query-player-religion-numeric-special-parameters-v1" and result["read_only"]
    assert result["status"] == "observed" and result["snapshot_revision"] == 701
    assert context["available"] and final["available"] and final["value_state"] == "value"
    assert context["capture_epoch"] == final["capture_epoch"] > 0
    assert context["capture_epoch"] != result["snapshot_revision"]
    assert context["date_raw"] == final["date_raw"] == result["date_raw"] == 53175816
    assert context["played_character_id"] == final["played_character_id"] == 0x03000004
    assert context["faith_id"] == final["faith_id"] == 0x83000003
    assert context["current_rite"]["rite_id"] == final["current_rite_id"] == 0
    assert context["faith_main_rite"]["rite_id"] == final["main_rite_id"] == 0x82000002
    current_values = {p["key"]: p["raw"] for p in context["current_rite"]["parameters"]}
    main_values = {p["key"]: p["raw"] for p in context["faith_main_rite"]["parameters"]}
    assert current_values["heresy_threshold"] == -500000 and main_values["heresy_threshold"] == 500000
    assert final["source"] == "faith_main_rite" and final["main_rite_adjustment_raw"] == 500000
    assert final["native_define_raw"] == 2500000 and final["final_heresy_threshold_raw"] == 3000000
    assert final["final_heresy_threshold"] == 30
    receipt = {"status": "GREEN", "readiness": "static-ready", "local_ck3_touched": False,
        "live_verified": False, "named_permit_only": True, "primary_permit": "null",
        "fixture_executor_permit": "permitted_executor_religion_numeric_special_parameters12002",
        "old_numeric15_executed": False, "old_final10_executed": False,
        "old_mailbox39_executed": False, "old_combined31_executed": False,
        "actual_mailbox_submit_drain_wait_reclaim": True,
        "actual_numeric_special_parameters_provider": True, "actual_faith_numeric_final_provider": True,
        "actual_protocol1_command_result_serializer": True, "actual_cpp_wire_cases": 1,
        "compiler": "MSVC /O2 /W4 /WX", "stdout": run.stdout.strip(), "defines": defines,
        "fixture_adapter_unwrap": "Bare native adapter identity shim; no WorkerAdapter production substitute",
        "generated_fixture_change": "Only final int main( renamed to int NumericMailboxCombinedMatrixUnused(; all other template bytes unchanged",
        "generated_fixture_sha256": digest(generated),
        "source_sha256": {str(p.relative_to(root)).replace("\\", "/"): digest(p) for p in pins},
        "wire_sha256": {packet_path.name: digest(packet_path)},
        "fixture_executable_sha256": digest(executable)}
    (output / "result.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(run.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
