"""Run only the authorized retired-assertion repair with the project source path."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TEST = "ck3_autonomous_player/tests/unit/test_m4_faction_gift_mcp_formal_config_12004.py"
SOURCE = "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
PREVIOUS = "docs/ck3-native-ai/evidence/war-daily-watch-v1-formal-cli-source-qualification-2026-10-19.json"
OUT = "docs/ck3-native-ai/evidence/war-daily-watch-v1-formal-cli-fixture-addendum-2026-10-19.json"
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()
NODE = TEST+"::McpFactionGiftFormalConfig12004Test::test_public_argv_reaches_native_constructor_and_normal_service"


def pin(path):
    body = (ROOT/path).read_bytes()
    return {"path": path, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def main():
    old = subprocess.check_output(["git", "show", "HEAD:"+TEST], cwd=ROOT)
    current = (ROOT/TEST).read_bytes()
    if old.replace(b"self.assertIs(driver.nonwar_only, False)",
                   b"self.assertIs(driver.allow_route_contact_high_speed_ab, False)", 1) != current:
        raise RuntimeError("more than the authorized independent assertion changed")
    if pin(SOURCE)["sha256"] != "c34e7d5454d0a877c83fd4969c734437208bc756fc5d2d3fdcbfae5e50462722":
        raise RuntimeError("production source changed after its software qualification")
    sys.path[:0] = [str(ROOT/"ck3_autonomous_player/src"), str(ROOT/"ck3_autonomous_player/tests/unit")]
    import pytest
    started = time.perf_counter_ns()
    result = int(pytest.main(["-q", "-p", "no:cacheprovider", "--tb=short", NODE]))
    elapsed = time.perf_counter_ns()-started
    if result:
        raise RuntimeError("single fixture node failed: "+str(result))
    previous = json.loads((ROOT/PREVIOUS).read_bytes())
    machine = subprocess.check_output([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"], cwd=ROOT, text=True).strip()
    report = {"schema": "xar.war-daily-watch-formal-cli-fixture-addendum.v1",
        "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SOURCE_READY_DEFAULT_OFF_LIVE_NOTRUN", "previous_immutable": pin(PREVIOUS),
        "candidate": pin(SOURCE), "test": pin(TEST), "producer": pin(SELF),
        "authorized_delta": {"line": 56, "before": "self.assertIs(driver.nonwar_only, False)",
            "after": "self.assertIs(driver.allow_route_contact_high_speed_ab, False)",
            "whole_test_other_bytes_equal": True,
            "reason": "Independent obsolete attribute conflicts with AGENTS retirement. Preserve prior RED/baseline record; no production compatibility field restored.",
            "preserved": "Original native class/formal flag/round/query/action/state/Service identity/stdout/endpoint assertions unchanged."},
        "single_node": {"node": NODE, "passed": 1, "exit_code": result,
            "pytest_call_wall_ns": elapsed,
            "preliminary_standalone_launch": "collection-only ModuleNotFoundError without PYTHONPATH; this runner supplies the source path, without further test edits"},
        "other_evidence": "Previous seven new CLI plus route3/LIFE1 PASS unchanged; no repeat broad matrix. Prior unrelated fixture failure now corrected by this one-node qualification.",
        "actions": {"Game_RPC": 0, "speed_changed": False, "current_C12_changed": False,
            "Driver_Service_war_helper_changes": 0, "builds": 0},
        "storage": {"limit_bytes": 32768, "previous_new_files_bytes": 20975,
            "production_net_bytes": 901, "existing_test_net_bytes": len(current)-len(old),
            "final_package_bytes": 0, "future_writes": 0, "allocated_bytes": None,
            "physical_credit": 0, "external_outputs_retained": 0}}
    for _ in range(8):
        body = (json.dumps(report, indent=2)+"\n").encode()
        total = 20975+901+(len(current)-len(old))+pin(SELF)["bytes"]+len(body)
        if total == report["storage"]["final_package_bytes"]:
            break
        report["storage"]["final_package_bytes"] = total
    if total > 32768:
        raise RuntimeError("32KiB source budget exceeded")
    with (ROOT/OUT).open("xb") as output:
        output.write(body)
    print(json.dumps({"receipt": pin(OUT), "candidate": pin(SOURCE),
        "fixture": pin(TEST), "final_package_bytes": total}, indent=2))


if __name__ == "__main__":
    main()
