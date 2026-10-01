#!/usr/bin/env python3
"""Exercise the actual numeric provider, owner mailbox and complete JSON path offline."""
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
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp", "religion_doctrine12002_numeric.cpp",
        "religion_doctrine12002_numeric_final.cpp",
        "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp", "protocol.cpp",
        "religion_doctrine12002_numeric_mailbox.cpp", "religion_doctrine12002_numeric_mailbox_test.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "religion_doctrine12002_numeric.hpp", "religion_doctrine12002_numeric_final.hpp",
        "religion_doctrine12002_numeric_mailbox.hpp",
        "ck3_12002_religion_context.hpp", "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp")]
    pins.extend((native / "src/religion_doctrine12002_numeric_test.cpp",
                 native / "src/religion_doctrine12002_numeric_final_test.cpp", Path(__file__)))
    target = output / "O2"
    target.mkdir(exist_ok=True)
    temp = target / "tmp"
    temp.mkdir(exist_ok=True)
    executable = target / "numeric-special-mailbox-test.exe"
    command = subprocess.list2cmdline(["cl.exe", "/nologo", "/std:c++20", "/EHsc",
        "/O2", "/W4", "/WX", "/utf-8", "/I" + str(native / "include"),
        "/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1=1",
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
        "current-versus-main.json", "known-zero-final.json", "minimum-unset.json",
        "legal-absent-faith.json", "legal-absent-main-rite.json", "native-threshold-unavailable.json")]
    packets = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in wire_paths}
    for packet in packets.values():
        result = packet["result"]
        context = result["player_religion_numeric_special_parameters"]
        final = result["faith_numeric_final"]
        assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
        assert packet["request_id"] == 'religion"mailbox-fixture'
        assert result["step"] == "query-player-religion-numeric-special-parameters-v1"
        assert result["domain_key"] == "player_religion_numeric_special_parameters_v1"
        assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-numeric-special-parameters-v1"
        assert result["accepted"] and result["private_build"] and result["read_only"] and not result["advertised"]
        assert result["snapshot_revision"] == 701
        assert result["date_raw"] == context["date_raw"] == 53175816
        assert context["capture_epoch"] > 0 and context["capture_epoch"] != result["snapshot_revision"]
        assert context["played_character_id"] == 0x03000004
        assert result["status"] == ("observed" if context["available"] else "unavailable")
        assert context["schema"] == "ck3_12002_rite_numeric_special_parameters_v1"
        assert context["supported_key_count"] == 5 and context["faith_numeric_consumer_source"] == "faith_main_rite"
        assert context["authored_presence_provenance_observed"] is False
        assert context["executable_sha256"] == result["executable_sha256"] == "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
        assert result["game_version"] == context["game_version"] == final["game_version"] == "1.20.0.2"
        assert final["schema"] == "ck3_12002_faith_numeric_final_v1"
        assert final["executable_sha256"] == context["executable_sha256"]
        assert final["capture_epoch"] == context["capture_epoch"]
        assert final["date_raw"] == context["date_raw"] and final["played_character_id"] == context["played_character_id"]
        assert final["scale"] == 100000 and final["unit"] == "fervor_points" and final["source"] == "faith_main_rite"
        if context["available"] and final["available"]:
            assert final["faith_id"] == context["faith_id"]
            assert final["current_rite_id"] == (None if context["current_rite"] is None else context["current_rite"]["rite_id"])
            assert final["main_rite_id"] == (None if context["faith_main_rite"] is None else context["faith_main_rite"]["rite_id"])
    key = "player_religion_numeric_special_parameters"
    current = packets["current-versus-main.json"]["result"][key]
    assert current["faith_id"] == 0x83000003
    assert current["current_rite"]["rite_id"] == 0 and current["faith_main_rite"]["rite_id"] == 0x82000002
    supported = {"minimum_fervor", "fervor_per_holy_site", "bonus_fervor_gain", "bonus_heresy_protection", "heresy_threshold"}
    for rite in (current["current_rite"], current["faith_main_rite"]):
        assert rite["observed_special_parameters_complete"] is True
        assert {p["key"] for p in rite["parameters"]} == supported
        assert all(p["state"] == "value" and p["unit"] for p in rite["parameters"])
    values = {p["key"]: p for p in current["current_rite"]["parameters"]}
    main_values = {p["key"]: p for p in current["faith_main_rite"]["parameters"]}
    assert values["minimum_fervor"]["raw"] == values["minimum_fervor"]["value"] == 0
    assert values["minimum_fervor"]["scale"] == values["bonus_heresy_protection"]["scale"] == 1
    assert values["fervor_per_holy_site"]["raw"] == 5000 and values["fervor_per_holy_site"]["value"] == 0.05
    assert values["bonus_fervor_gain"]["raw"] == 50000 and values["bonus_fervor_gain"]["value"] == 0.5
    assert values["heresy_threshold"]["raw"] == -500000 and values["heresy_threshold"]["value"] == -5
    assert main_values["minimum_fervor"]["value"] == 45 and main_values["heresy_threshold"]["value"] == 5
    initial_final = packets["current-versus-main.json"]["result"]["faith_numeric_final"]
    assert initial_final["available"] and initial_final["value_state"] == "value"
    assert initial_final["main_rite_adjustment_raw"] == 500000 and initial_final["native_define_raw"] == 2500000
    assert initial_final["final_heresy_threshold_raw"] == 3000000 and initial_final["final_heresy_threshold"] == 30
    zero = packets["known-zero-final.json"]["result"]["faith_numeric_final"]
    assert zero["available"] and zero["value_state"] == "value"
    assert zero["native_define_raw"] == -500000 and zero["main_rite_adjustment_raw"] == 500000
    assert zero["final_heresy_threshold_raw"] == zero["final_heresy_threshold"] == 0
    unset = packets["minimum-unset.json"]["result"][key]
    assert unset["available"] and unset["current_rite"]["parameters"][0]["raw"] == -1
    assert unset["current_rite"]["parameters"][0]["state"] == "unset"
    assert unset["current_rite"]["parameters"][0]["value"] is None
    assert packets["minimum-unset.json"]["result"]["faith_numeric_final"]["final_heresy_threshold"] == 30
    absent_faith = packets["legal-absent-faith.json"]["result"]
    assert absent_faith[key]["available"] and absent_faith[key]["current_rite"] is not None
    assert absent_faith["faith_numeric_final"]["available"] and absent_faith["faith_numeric_final"]["value_state"] == "legal_absent_faith"
    absent_main = packets["legal-absent-main-rite.json"]["result"]
    assert absent_main[key]["available"] and absent_main[key]["faith_main_rite"] is None
    assert absent_main["faith_numeric_final"]["available"] and absent_main["faith_numeric_final"]["value_state"] == "legal_absent_main_rite"
    for absent in (absent_faith, absent_main):
        assert absent["faith_numeric_final"]["final_heresy_threshold_raw"] is None
        assert absent["faith_numeric_final"]["final_heresy_threshold"] is None
    missing = packets["native-threshold-unavailable.json"]["result"]
    assert missing["status"] == "observed" and missing[key]["available"]
    assert not missing["faith_numeric_final"]["available"] and missing["faith_numeric_final"]["value_state"] == "unavailable"
    assert missing["faith_numeric_final"]["unavailable_reason"] == "native_threshold_unavailable"
    assert missing["faith_numeric_final"]["final_heresy_threshold_raw"] is None
    result = {
        "status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_native_core": True,
        "actual_numeric_special_parameters_provider": True,
        "actual_faith_numeric_final_provider": True,
        "actual_mailbox_submit_drain_wait_reclaim": True, "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Frozen numeric memory fixture and canonical final Threshold/native_define helpers; neither old main executed",
        "fixture_adapter_unwrap": "Bare GameAdapter identity branch only; no WorkerAdapter implementation substituted",
        "fixture_executor_permit": "Existing primary fixture permit with owned memory; central owner registers deployed named permit",
        "old_reader_checks_executed": False, "old_final_reader_checks_executed": False,
        "superseded_cache_only_39_checks_executed": False,
        "compiler": "MSVC /O2 /W4 /WX",
        "runs": [{"mode": "O2", "returncode": run.returncode, "stdout": run.stdout.strip(),
                  "actual_wire_sha256": {p.name: digest(p) for p in wire_paths},
                  "fixture_executable_sha256": digest(executable)}],
        "source_sha256": {str(p.relative_to(root)).replace("\\", "/"): digest(p) for p in pins},
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("O2", run.stdout.strip())
    print("GREEN six actual command_result packets parsed; local CK3 untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
