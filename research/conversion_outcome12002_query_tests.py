#!/usr/bin/env python3
"""Actual current-state conversion outcome providers and mailbox, without CK3."""
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
        "ck3_12002.cpp", "ck3_12002_religion_context.cpp", "ck3_12002_actor_resources.cpp",
        "conversion_outcome12002_actor.cpp", "conversion_outcome12002_state.cpp",
        "conversion_outcome12002_query.cpp", "conversion_outcome12002_mailbox.cpp",
        "conversion_outcome12002_mailbox_test.cpp", "ck3_12002_query_mailbox.cpp",
        "main_thread_query_mailbox_v1.cpp", "protocol.cpp")]
    pins = sources + [native / "include/xar_bridge" / name for name in (
        "conversion_outcome12002_actor.hpp", "conversion_outcome12002_state.hpp",
        "conversion_outcome12002_query.hpp", "conversion_outcome12002_mailbox.hpp",
        "ck3_12002_religion_context.hpp", "ck3_12002_actor_resources.hpp",
        "ck3_12002_query_mailbox.hpp", "main_thread_query_mailbox_v1.hpp")]
    cases = ("current.json", "zero-target.json", "target-current.json",
             "actor-unavailable.json", "state-unavailable.json", "both-unavailable.json")
    runs = []
    for mode in ("Od", "O2"):
        target = output / mode
        target.mkdir(exist_ok=True)
        temp = target / "tmp"
        temp.mkdir(exist_ok=True)
        exe = target / "religion-conversion-outcome-test.exe"
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
        if build.returncode:
            raise RuntimeError("Compile failed: " + str(target / "build.log"))
        run = subprocess.run([str(exe), str(target)], cwd=target, env=environment,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        (target / "test.log").write_text(run.stdout + run.stderr, encoding="utf-8")
        if run.returncode:
            raise RuntimeError("Fixture failed: " + str(target / "test.log"))
        packets = {name: json.loads((target / name).read_text(encoding="utf-8")) for name in cases}
        for packet in packets.values():
            result = packet["result"]
            out = result["player_religion_conversion_outcome"]
            assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
            assert packet["request_id"] == 'religion-outcome"mailbox-fixture'
            assert result["step"] == "query-player-religion-conversion-outcome-v1"
            assert result["domain_key"] == "player_religion_conversion_outcome_v1"
            assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-conversion-outcome-v1"
            assert result["accepted"] and result["private_build"] and result["read_only"] and not result["advertised"]
            assert result["snapshot_revision"] == 901
            assert result["date_raw"] == out["date_raw"] == 53175816
            assert out["played_character_id"] == 0x03000004
            assert out["capture_epoch"] > 0 and out["capture_epoch"] != result["snapshot_revision"]
            assert out["schema"] == "ck3_12002_religion_conversion_outcome_v1"
            assert out["target_reached_is_identity_only"] and not out["conversion_causality_inferred"]
            assert result["status"] == ("observed" if out["available"] else "unavailable")
            for key in ("actor", "state"):
                component = out[key]
                assert component["date_raw"] == out["date_raw"]
                assert component["played_character_id"] == out["played_character_id"]
                assert component["capture_epoch"] == out["capture_epoch"]
            actor, state = out["actor"], out["state"]
            assert actor["current_religion"]["capture_epoch"] == out["capture_epoch"]
            assert state["requested_target_rite_id"] == out["target_rite_id"]
            assert state["flag_expiry_unit"] == "native_flag_updates"
            assert not state["is_conversion_gain"] and not actor["conversion_causality_inferred"]
        current = packets["current.json"]["result"]["player_religion_conversion_outcome"]
        actor, state = current["actor"], current["state"]
        assert current["available"] and current["target_rite_id"] == state["target_rite_id"] == 0x84000001
        assert current["target_reached"] is False
        assert actor["piety_raw"] == 0 and actor["gold_raw"] == -123456 and actor["prestige_raw"] == -7654321
        assert actor["raw_scale"] == state["raw_scale"] == 100000
        assert actor["current_religion"]["rite_id"] == 0
        assert actor["current_religion"]["faith_id"] == 0x83000003
        assert actor["current_religion"]["religion_id"] == 0x84000005
        assert actor["current_religion"]["faith_key"] == 'faith"key'
        assert actor["current_religion"]["spiritual_fulfillment_raw"] == state["spiritual_fulfillment_raw"] == 345678
        assert state["baseline_spiritual_fulfillment_raw"] == 456789 and state["knowledge_level_raw"] == 25000
        recency = state["faith_conversion_recently_converted"]
        assert recency == {"key_registered": True, "present": True, "timed": True,
            "expiry_counter_raw": 200, "current_counter_raw": 150, "remaining_updates": 50}
        memory = state["conversion_memory_recently_created"]
        assert memory["key_registered"] and memory["present"] is False and memory["timed"] is None
        assert memory["expiry_counter_raw"] is None and memory["remaining_updates"] is None
        recent = state["recent_convert"]
        assert recent["present"] and recent["timed"] is False and recent["expiry_counter_raw"] == -1
        assert recent["remaining_updates"] is None
        zero = packets["zero-target.json"]["result"]["player_religion_conversion_outcome"]
        assert zero["available"] and zero["target_reached"] and zero["target_rite_id"] == zero["state"]["target_rite_id"] == 0
        assert zero["state"]["knowledge_level_raw"] == 0
        reached = packets["target-current.json"]["result"]["player_religion_conversion_outcome"]
        assert reached["available"] and reached["target_reached"] and reached["actor"]["current_religion"]["rite_id"] == 0x84000001
        actor_failed = packets["actor-unavailable.json"]["result"]["player_religion_conversion_outcome"]
        assert not actor_failed["available"] and not actor_failed["actor"]["available"] and actor_failed["state"]["available"]
        assert actor_failed["actor"]["piety_raw"] is None and actor_failed["target_reached"] is None
        state_failed = packets["state-unavailable.json"]["result"]["player_religion_conversion_outcome"]
        assert not state_failed["available"] and state_failed["actor"]["available"] and not state_failed["state"]["available"]
        assert state_failed["state"]["knowledge_level_raw"] is None and state_failed["state"]["target_rite_id"] is None
        assert state_failed["target_reached"] is False
        both_failed = packets["both-unavailable.json"]["result"]["player_religion_conversion_outcome"]
        assert not both_failed["available"] and not both_failed["actor"]["available"] and not both_failed["state"]["available"]
        assert both_failed["target_reached"] is None
        assert not (target / "source-mismatch.json").exists() and not (target / "published-drift.json").exists()
        runs.append({"mode": mode, "stdout": run.stdout.strip(), "actual_wire_cases": len(packets),
            "wire_sha256": {name: digest(target / name) for name in cases}, "fixture_executable_sha256": digest(exe)})
        print(mode, run.stdout.strip())
    result = {"status": "GREEN", "readiness": "static-ready", "live_verified": False,
        "local_ck3_touched": False, "actual_native_core": True, "actual_actor_and_state_providers": True,
        "actual_mailbox_submit_drain_wait_reclaim": True, "actual_command_result_serializer": True,
        "fixture_native_callbacks": "Fixture-owned objects and native-shaped callbacks; no CK3 function calls",
        "fixture_executor_permit": "Existing primary permitted_executor; production named slot registration owned by root",
        "compiler": "MSVC /W4 /WX /Od and /O2", "runs": runs,
        "source_sha256": {str(path.relative_to(root)): digest(path) for path in pins}}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
