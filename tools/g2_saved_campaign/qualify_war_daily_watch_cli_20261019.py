"""Seal three-function CLI delta and isolate an unchanged retired test failure."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
TEST = "ck3_autonomous_player/tests/unit/test_mcp_war_daily_watch_config_v1.py"
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()
OUT = "docs/ck3-native-ai/evidence/war-daily-watch-v1-formal-cli-source-qualification-2026-10-19.json"
NAMES = {"load_driver", "parser", "main"}


def pin(path):
    body = (ROOT/path).read_bytes()
    return {"path": path, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def main():
    old = subprocess.check_output(["git", "show", "HEAD:"+SOURCE], cwd=ROOT)
    before = ast.parse(old)
    after = ast.parse((ROOT/SOURCE).read_bytes())
    old_sha = hashlib.sha256(old).hexdigest()
    if old_sha != "a857d7267a58979da7a81d7bf25b277c1cfa6b5d48fc75b5094013f0faa20720":
        raise RuntimeError("reviewed master baseline changed")
    def remaining(tree):
        return ast.dump(ast.Module(body=[n for n in tree.body
            if not isinstance(n, ast.FunctionDef) or n.name not in NAMES], type_ignores=[]))
    if remaining(before) != remaining(after):
        raise RuntimeError("source extends outside load_driver/parser/main")
    subprocess.run(["git", "diff", "--check", "--", SOURCE], cwd=ROOT, check=True)
    sys.path[:0] = [str(ROOT/"ck3_autonomous_player/src"), str(ROOT/"ck3_autonomous_player/tests/unit")]
    from xar_autoplayer.bridge import mcp_server
    namespace = dict(vars(mcp_server))
    baseline_nodes = [n for n in before.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    exec(compile(ast.Module(body=baseline_nodes, type_ignores=[]), "<original-master-three-functions>", "exec"), namespace)
    fixture = importlib.import_module("test_m4_faction_gift_mcp_formal_config_12004")
    original_error = None
    with patch.object(mcp_server, "main", namespace["main"]):
        try:
            fixture.McpFactionGiftFormalConfig12004Test().test_public_argv_reaches_native_constructor_and_normal_service()
        except AttributeError as error:
            original_error = str(error)
    if original_error != "'NativeHeadlessGameplayDriver' object has no attribute 'nonwar_only'":
        raise RuntimeError("legacy failure was not reproduced on the unmodified baseline: "+str(original_error))
    machine = subprocess.check_output([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"], cwd=ROOT, text=True).strip()
    report = {
        "schema": "xar.war-daily-watch-formal-cli-source-qualification.v1",
        "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_evidence": "tools/ck3_live_run_id.py machine actual subprocess readback",
        "status": "SOURCE_WIRING_READY_DEFAULT_OFF_ACTUAL_C12_UNCHANGED",
        "master_baseline": {"path": SOURCE, "bytes": len(old), "sha256": old_sha},
        "candidate": pin(SOURCE), "test": pin(TEST), "producer": pin(SELF),
        "actual_C12_baseline_from_root_harness_review": {"bytes": 263022,
            "sha256": "1980c01abb14b2cb579bf3dba3bc1a58f9d4b89d7b8181db356a4b216b37e2b7",
            "Driver_bytes": 1619371,
            "Driver_sha256": "65888f480a9cc8187f37ad2c44d8592fbf2df0e1843090f47e277ec1b7d8b5f1"},
        "composition": [
            "Root must compose only these additions onto actual C12 mcp_server; do not adopt this whole master leaf or replace whole main/parser bodies.",
            "load_driver: add allow_war_daily_watch_v1:bool=False; exact-bool check; True requires factory=native-headless; add one keyword to original native constructor.",
            "parser: add --private-war-daily-watch-speed2-trial store_true (default False); no environment alias or route-speed change.",
            "main: require native-headless and stdio for that flag, then forward the bool into load_driver.",
            "Preserve every other argument, private/lifecycle guard, original type, route AB/hold readiness and startup order. Driver/Service/war helper are unchanged.",
            "No constructor import hook, monkeypatch or module:callable runtime replacement. Current C12 remains OFF."
        ],
        "offline_tests": {
            "command": "python -B -m pytest -q -p no:cacheprovider --tb=short test_mcp_war_daily_watch_config_v1.py test_mcp_route_contact_speed_config.py test_m4_lifestyle_mcp_formal_config_12004.py test_m4_faction_gift_mcp_formal_config_12004.py (under ck3_autonomous_player/tests/unit)",
            "actual_result": "11 passed, 1 failed in 7.12s, exit_code=1",
            "new_targeted_tests": "7 PASS: CLI default/ON; exact constructor kwargs; strict bool; non-native refusal; real main->constructor->Service with private flags; non-stdio refusal; existing lifecycle/initial-focus/route AB guards",
            "related_pass": "route configuration 3 PASS; lifestyle formal configuration 1 PASS",
            "legacy_failure": {"file": "test_m4_faction_gift_mcp_formal_config_12004.py:56",
                "error": original_error,
                "baseline_reproduced": True,
                "method": "Execute only original git-HEAD load_driver/parser/main AST definitions in a copied module namespace; temporarily patch test entry main in memory; original fixture uses no-Game endpoint. No source file restore or Game call.",
                "disposition": "Preserve failure. AGENTS retires nonwar_only; do not resurrect it or repair unrelated fixture in this task."},
            "diff_check": 0, "only_three_functions_changed_AST": True
        },
        "live": {"Game_RPC": 0, "Native_build": "NOTRUN", "current_SDK_or_flags_changed": False,
            "speed2_qualified": False, "next": "Root narrow composition, exact new freeze/normal warm qualification; actual trial only after separate authorization."},
        "storage": {"source_budget_bytes": 32768, "new_files": [TEST, SELF, OUT],
            "source_net_growth_bytes": pin(SOURCE)["bytes"]-len(old),
            "new_files_logical_bytes": 0, "allocated_bytes": None, "physical_credit_bytes": 0,
            "future_writes": 0, "external_outputs_retained": 0}
    }
    for _ in range(8):
        body = (json.dumps(report, indent=2)+"\n").encode()
        total = pin(TEST)["bytes"]+pin(SELF)["bytes"]+len(body)
        if total == report["storage"]["new_files_logical_bytes"]:
            break
        report["storage"]["new_files_logical_bytes"] = total
    if total+max(0,report["storage"]["source_net_growth_bytes"]) > 32768:
        raise RuntimeError("32KiB source budget exceeded")
    with (ROOT/OUT).open("xb") as output:
        output.write(body)
    print(json.dumps({"receipt": pin(OUT), "candidate": pin(SOURCE),
        "new_files_logical_bytes": total,
        "source_net_growth_bytes": report["storage"]["source_net_growth_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
