"""Append the OFF-state replay correction; do not rewrite the original seal."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = "docs/ck3-native-ai/evidence/war-daily-watch-v1-software-qualification-2026-10-19.json"
OUT = "docs/ck3-native-ai/evidence/war-daily-watch-v1-replay-guard-addendum-2026-10-19.json"
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()


def pin(path):
    body = (ROOT/path).read_bytes()
    return {"path": path, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def main():
    previous = json.loads((ROOT/PREVIOUS).read_bytes())
    original = previous["source_pins"]
    current = [pin(value["path"]) for value in original[:3]]
    if current[0]["sha256"] != "a7c09a146cef8973f6a04919dfccba702475542f47fa53e7aa9038699014ff73":
        raise RuntimeError("Driver changed after the targeted qualification")
    if current[1] != original[1]:
        raise RuntimeError("helper changed")
    machine = subprocess.check_output([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"],
                                      cwd=ROOT, text=True).strip()
    doc = {"schema": "xar.war-daily-watch-replay-guard-addendum.v1",
        "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_evidence": "tools/ck3_live_run_id.py machine, actual subprocess readback",
        "previous_immutable_seal": pin(PREVIOUS), "source_pins": current, "producer": pin(SELF),
        "status": "SOFTWARE_READY_DEFAULT_OFF_LIVE_NOTRUN",
        "real_red": {"test": "test_restored_unknown_marker_blocks_generic_day_even_when_candidate_is_disabled",
            "result": "1 failed in 3.04s: BridgeUnavailableError not raised; disabled replacement could advance generic day"},
        "change": "Remove only the allow flag from the existing once-per-Driver restored-history check; its pending latch applies regardless of candidate enablement.",
        "history_handling": "Original history read under its lock, no copying/export, no Native RPC. No-marker default behavior is retained.",
        "targeted_pass": {"files": "ck3_autonomous_player/tests/unit/test_war_daily_watch_v1.py",
            "nodes": ["test_restored_unknown_marker_blocks_generic_day_even_when_candidate_is_disabled",
                "test_existing_history_persists_unknown_marker_and_blocks_a_restored_candidate",
                "test_default_off_and_constructor_requires_explicit_boolean"],
            "actual_result": "3 passed in 2.24s, exit_code=0", "diff_check": 0,
            "full_46_matrix_rerun": False},
        "native_build": "NOTRUN", "game_rpc": 0, "current_game_sdk_speed_changes": 0,
        "configuration": "allow_war_daily_watch_v1 remains False by default; fixed speed2 requires later live admission",
        "storage": {"source_limit_bytes": 65536, "original_package_logical_plus_net_bytes": 55103,
            "additional_test_bytes": current[2]["bytes"]-original[2]["bytes"],
            "additional_driver_net_bytes": current[0]["bytes"]-original[0]["bytes"],
            "new_addendum_producer_bytes": pin(SELF)["bytes"],
            "final_package_logical_plus_net_bytes": 0,
            "allocated_bytes": None, "physical_credit_bytes": 0, "external_output_bytes": 0,
            "future_writes_after_seal": 0}}
    for _ in range(8):
        body = (json.dumps(doc, ensure_ascii=False, indent=2)+"\n").encode()
        storage = doc["storage"]
        total = (55103+storage["additional_test_bytes"]+storage["additional_driver_net_bytes"]
                 +storage["new_addendum_producer_bytes"]+len(body))
        if total == storage["final_package_logical_plus_net_bytes"]:
            break
        storage["final_package_logical_plus_net_bytes"] = total
    if total > 65536:
        raise RuntimeError("source budget exceeded")
    with (ROOT/OUT).open("xb") as output:
        output.write(body)
    print(json.dumps({"receipt": pin(OUT), "source_pins": current,
        "final_package_logical_plus_net_bytes": total}, indent=2))


if __name__ == "__main__":
    main()
