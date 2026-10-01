#!/usr/bin/env python3
"""One O2 production named outcome queue case; frozen matrices are reused."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
NATIVE = ROOT / "ck3_autonomous_player/native_bridge"
sys.path.insert(0, str(NATIVE / "research"))
from test_government_runtime_adapter_12002_standalone import run_batch
from test_government_runtime_adapter_bridge_binder_v1_standalone import visual_studio_developer_shell

SOURCES = (
    "ck3_12002.cpp", "ck3_12002_religion_context.cpp", "ck3_12002_actor_resources.cpp",
    "conversion_outcome12002_actor.cpp", "conversion_outcome12002_state.cpp",
    "conversion_outcome12002_query.cpp", "conversion_outcome12002_mailbox.cpp",
    "ck3_12002_query_mailbox.cpp", "main_thread_query_mailbox_v1.cpp", "protocol.cpp",
)
TEST = "r5_religion_conversion_outcome_named_test.cpp"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    output = args.artifacts.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "temp"
    temporary.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temporary)
    shell = visual_studio_developer_shell()
    compiler = ["cl.exe", "/nologo", "/std:c++20", "/EHsc", "/W4", "/WX", "/utf-8",
                "/DNOMINMAX", "/O2", "/DXAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1",
                "/DXAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1", "/I" + str(NATIVE / "include")]
    run_batch(command=compiler + ["/c", "/MP32"] + [str(NATIVE / "src" / name) for name in SOURCES],
              shell=shell, output=output, tag="compile")
    executable = output / "religion_conversion_outcome_named.exe"
    run_batch(command=compiler + [str(NATIVE / "src" / TEST)] +
              [str(output / Path(name).with_suffix(".obj")) for name in SOURCES] +
              ["User32.lib", "/Fe:" + str(executable)], shell=shell, output=output, tag="link")
    run = subprocess.run([str(executable), str(output)], cwd=output, capture_output=True,
                         text=True, encoding="utf-8", errors="replace", timeout=15)
    (output / "run.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise RuntimeError("Named queue failed: " + str(output / "run.log"))
    packet_path = output / "named-current.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    result = packet["result"]
    out = result["player_religion_conversion_outcome"]
    assert packet["type"] == "command_result" and packet["protocol_version"] == 1 and packet["ok"] is True
    assert packet["request_id"] == "religion-outcome-named-fixture"
    assert result["step"] == "query-player-religion-conversion-outcome-v1"
    assert result["domain_key"] == "player_religion_conversion_outcome_v1"
    assert result["backend_id"] == "ck3-1.20.0.2-native-player-religion-conversion-outcome-v1"
    assert result["accepted"] and result["private_build"] and result["read_only"] and not result["advertised"]
    assert result["snapshot_revision"] == 901 and out["capture_epoch"] == 3
    assert out["available"] and out["target_rite_id"] == 0x84000001 and out["target_reached"] is False
    assert out["target_reached_is_identity_only"] and not out["conversion_causality_inferred"]
    assert out["actor"]["piety_raw"] == 0 and out["actor"]["gold_raw"] == -123456
    assert out["state"]["faith_conversion_recently_converted"]["remaining_updates"] == 50
    receipt = {
        "schema": "xar.ck3.religion-conversion-outcome-named-permit/v1",
        "status": "GREEN", "readiness": "static-ready", "time_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(ROOT), "mode": "O2", "cases": 1, "stdout": run.stdout.strip(),
        "production_named_permit": "permitted_executor_religion_conversion_outcome12002",
        "primary_null_checked_before_and_after": True,
        "exact_named_callback_checked_before_and_after": True,
        "actual_pipeline": "worker Submit -> production named callback admission -> owner Drain -> actual actor/state providers -> Wait/Reclaim -> complete command_result",
        "fixture_native_callbacks": True, "live_verified": False, "ck3_accessed": False,
        "old_20_modified": False, "old_Od_O2_matrix_repeated": False, "provider_matrix_repeated": False,
        "executable_sha256": sha(executable), "actual_packet": str(packet_path), "actual_packet_sha256": sha(packet_path),
        "new_paths_sha256": {
            "ck3_autonomous_player/native_bridge/src/" + TEST: sha(NATIVE / "src" / TEST),
            "research/conversion_outcome12002_named_tests.py": sha(Path(__file__)),
        },
        "compiled_source_sha256": {"ck3_autonomous_player/native_bridge/src/" + name:
                                   sha(NATIVE / "src" / name) for name in SOURCES},
        "defines": ["XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1=1",
                    "XAR_RELIGION_MAILBOX_STANDALONE_ADAPTER=1"],
        "central_source_head_reported": "a07aca2cbd67bc42b4db7cc07ee5b762c029bd28",
        "report_fields": {
            "completed": "R5 exact production Outcome named callback admitted one real queued observation with primary null.",
            "tests": "One new O2 W4WX case; actual owner Drain/Wait/Reclaim and full protocol serializer. Frozen Od/O2 and provider matrices reused.",
            "readiness": "static-ready; native-shaped fixture, no CK3/live claim.",
            "red": "none in this new named queue attempt",
            "next": "Root final R5 freeze/commit/push and paused actual before/after conversion outcome observations.",
            "commit_push": "Root-owned Git; no Git, CK3, pipe, UI, Steam or war work by this worker.",
        },
    }
    receipt_path = output / "result.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "result": str(receipt_path), "result_sha256": sha(receipt_path),
                      "new_paths_sha256": receipt["new_paths_sha256"], "stdout": run.stdout.strip()}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
