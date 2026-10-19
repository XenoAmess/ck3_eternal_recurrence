"""Create-only source qualification; no SDK/Game/Native/test execution."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import prepare_candidate as producer

ROOT = Path(__file__).resolve().parent
MACHINE = "xenoamess-full-tower-eb9d2c1186"
CAP = 2097152
CARD = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE-A0-CLOCK-BOUNDED-DIAGNOSTIC-COMPLETE2MiB-SOURCE-COMMITMENT01.json")
CARD_SHA = "8813e186bcf63a6e1b89ca55903d90bdd46a51b348a03dd8dc0f38e436c1937a"


def ref(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode("utf-8")


def write_new(path, data):
    current = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    if current + len(data) > CAP:
        raise ValueError("source package cap exceeded")
    with path.open("xb") as stream:
        stream.write(data)


def main():
    if (ROOT / "PLAN.json").exists() or (ROOT / "SOURCE-READY.json").exists():
        raise FileExistsError("source qualification already sealed")
    card = ref(CARD)
    if card["sha256"] != CARD_SHA:
        raise ValueError("source admission changed")
    current_machine = subprocess.check_output(
        ["py", "-B", str(producer.REPO / "tools/ck3_live_run_id.py"), "machine"],
        cwd=producer.REPO, text=True).strip()
    if current_machine != MACHINE:
        raise ValueError("source machine differs from admitted machine")
    branches = []
    for name, edits, owner in (("native_driver.py", producer.DRIVER_EDITS, "_advance_exact_day_with_sentinel"),
                               ("mcp_server.py", producer.MCP_EDITS, "ck3_auto_turn")):
        before = producer.original(name)
        path = ROOT / "xar_autoplayer/bridge" / name
        after = path.read_bytes()
        if producer.transform(before, edits) != after or producer.transform(after, edits, reverse=True) != before:
            raise ValueError("RAM transform or full inverse mismatch")
        compile(after, str(path), "exec")
        # Exactly one named method is the only AST difference in each full blob.
        oldtree, newtree = ast.parse(before), ast.parse(after)
        oldnode = producer.function_node(before, owner)
        for parent in ast.walk(newtree):
            for _, value in ast.iter_fields(parent):
                if isinstance(value, list):
                    for index, child in enumerate(value):
                        if isinstance(child, ast.FunctionDef) and child.name == owner:
                            value[index] = oldnode
        if ast.dump(oldtree) != ast.dump(newtree):
            raise ValueError("unowned AST changed")
        branches.append({"file": name, "base_git_path": producer.PREFIX + name,
                         "before_bytes": len(before), "before_sha256": producer.sha(before),
                         "candidate": ref(path), "inverse_full_blob_equal": True,
                         "only_changed_function": owner, "other_ast_equal": True})
    now = datetime.now(timezone.utc).isoformat()
    plan = {
        "schema": "xar.a0-exact-clock-diagnostic-source-plan/v1", "status": "SOURCE_ONLY",
        "machine_id": MACHINE, "observed_at_utc": now, "root": str(ROOT),
        "base_business_commit": producer.BASE, "source_admission": card,
        "hard_source_bytes": CAP, "participating_full_blobs": branches,
        "production_intent": "Root-reviewed narrow AST composition into the same f198 baseline; these candidate files are not an adopted SDK.",
        "driver_scope": "Only the local map-not-paused error before normal sentinel query; a dedicated local flag prevents matching unrelated exceptions by message.",
        "behavior": {
            "original_error_text_and_cause_retained": True,
            "normal_calls_actions_and_result_unchanged": True,
            "other_errors_same_object_reraised": True,
            "war_daily_watch_existing_error_branch_unchanged": True,
            "cleanup_calls_and_order_unchanged": True,
            "new_native_queries": 0,
            "diagnostic_max_utf8_bytes": 8192,
            "is_error": True, "credit": 0, "never_replay": True,
            "normal_status_query_attempted": False, "stop_validation_attempted": False,
            "stored_frames": "starting and last wait frame plus fresh cleanup frame BEFORE pause/cancel; scalar allowlists only; owner/observer fields explicitly cached",
            "stored_actions": "at most4 rows before cleanup and4 cleanup rows from this invocation only; selected scalar ACK fields, no history/snapshot/action-body copy",
            "ack_missing_or_malformed_accepted": None,
            "diagnostic_generation_failure": "rethrow original error, no replacement error",
        },
        "mcp_scope": "The existing ck3_auto_turn BridgeUnavailableError handler projects exact typed schema as is_error; construction/native rejection/typed ROOT retry handling remains in order for other errors.",
        "wal_composition": {
            "other_owner": "/root/performance_python",
            "other_methods": ["__init__", "retain_succession_expectation_v1", "_try_persist_driver_state_wal_append_v1", "_persist_driver_state"],
            "overlap_with_this_method": False, "combined_future_sdk_authored": False,
        },
        "qualification_limits": ["Mocked I/O boundaries, actual candidate/baseline method AST and actual f198 exception class AST; installed mcp.types exercised.",
            "No Game/RPC/current Queue/src17 mutation, no new status query, no Native compilation or new DLL/EXE.",
            "No actual sentinel stop, timeout recovery, speedup or SDK adoption qualification.",
            "Structured diagnostic is an error receipt and grants no replay or progress credit.",
            "The F97 original missing Arm/cleanup/stop receipts remain missing; current status cannot backfill them."],
        "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0,
    }
    write_new(ROOT / "PLAN.json", encode(plan))
    files = [ref(p) for p in sorted(ROOT.rglob("*")) if p.is_file()]
    proof = {
        "schema": "xar.a0-exact-clock-diagnostic-source-ready/v1", "status": "SOURCE_READY_NOT_ADOPTED",
        "machine_id": MACHINE, "observed_at_utc": now, "base_business_commit": producer.BASE,
        "plan": ref(ROOT / "PLAN.json"), "source_admission": card,
        "tests": {"command": "py -B tools/g2_saved_campaign/candidates/a0_clock_diagnostic_20261020/test_candidate.py",
                  "final_count": 10, "final_pass": 10, "final_fail": 0, "duration_seconds": 13.424,
                  "actual_output_source": "exec session90579 output383e7a and completion12b474",
                  "earlier_count_before_helper_safety_refinement": 9,
                  "tests_not_reexecuted_by_sealer": True},
        "source_checks": {"full_input_pins": True, "full_inverse": True,
                          "full_candidate_syntax": True, "only_two_named_AST_spans": True},
        "files_excluding_this_proof": files, "proof_self_pin": "returned separately by sealer stdout",
        "full_logical_bytes_including_this_proof": 0, "hard_bytes": CAP,
        "allocated_bytes": None, "future_writes": 0, "owned_children_after_close": 0,
        "external_outputs": 0, "Game_RPC_CPP_EXE_SDK_adoption": "NOTRUN",
        "physical_credit_bytes": 0,
    }
    for _ in range(4):
        proof["full_logical_bytes_including_this_proof"] = sum(row["bytes"] for row in files) + len(encode(proof))
    encoded = encode(proof)
    if proof["full_logical_bytes_including_this_proof"] != sum(row["bytes"] for row in files) + len(encoded):
        raise ValueError("proof accounting did not converge")
    write_new(ROOT / "SOURCE-READY.json", encoded)
    print(json.dumps({"plan": ref(ROOT / "PLAN.json"), "ready": ref(ROOT / "SOURCE-READY.json"),
                      "full_logical_bytes": proof["full_logical_bytes_including_this_proof"],
                      "file_count": len(files) + 1, "future_writes": 0}, indent=2))


if __name__ == "__main__":
    main()
