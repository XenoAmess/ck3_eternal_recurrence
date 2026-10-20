"""Create-only small source plan/proof; never materialize full generated leaves."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MACHINE = "xenoamess-full-tower-eb9d2c1186"
CARDS = (
    ("NATIVE-SDK-EXISTING-WAIT-PROGRESS-DIAGNOSTIC-SOURCE64KiB01.json", 2192,
     "5d12b9eb70baf3de0bc4f85ff184738dce886d3cd1b918ed3675fd792b06e256"),
    ("NATIVE-SDK-WAIT-PROGRESS64KiB-INPUT-OWNED8KiB-OVERLAY01.json", 2318,
     "64c67b3fee4e5b512518c30853098907b796dda2a2338ea0f035598b09f0cfff"),
)


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def seal(inputs, outputs, diff, report):
    storage = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01")
    cards = []
    for name, size, sha in CARDS:
        path = storage / name
        raw = path.read_bytes()
        value = json.loads(raw)
        if len(raw) != size or pin(raw)["sha256"] != sha or value["machine_id"] != MACHINE:
            raise ValueError("exact same-machine source card changed")
        cards.append({"path": str(path), **pin(raw)})
    now = datetime.now(timezone.utc).isoformat()
    source_rows = [{"path": str(p), **pin(p.read_bytes())} for p in sorted(ROOT.iterdir()) if p.is_file()]
    if any(p.name in {"DIFF.patch", "PLAN.json", "QUALIFICATION.json", "SOURCE-READY.json"} for p in ROOT.iterdir()):
        raise FileExistsError("small result must be create-only")
    plan = {
        "schema": "xar.exact-clock-wait-progress-source-plan.v1", "machine_id": MACHINE,
        "observed_at_utc": now, "status": "SOURCE_CANDIDATE_ONLY",
        "machine_id_source": "tools/ck3_live_run_id.py machine, execution ff6bba",
        "cards": cards, "immutable_commit": "6b55531b1d3a44ee73ab13ea40132556030f682e",
        "input_pins": {name: pin(raw) for name, raw in inputs.items()},
        "qualification_error_contract": report["contract"],
        "actual_large_Driver_Git_body_reads": 2,
        "input_payload_bytes_both_attempts": 3360926,
        "Git_input_logical_bytes_read": report["inputs_read_logical_bytes"],
        "other_preparation_provenance_reads": {"Source24_producer_bytes": 14942, "Source24_anchor_JSON_bytes": 6269},
        "source24_anchor": {"path": "docs/ck3-native-ai/evidence/source24-canonical-root-anchor-actual-2026-10-20.json",
                            "bytes": 6269, "sha256": "fb4f7ef4933d7e86f82b81e0824332a92f49ae5562c8337460b87efb8031a8f8"},
        "generated_RAM_outputs_ref": "QUALIFICATION.json/output_pins", "generated_full_leaf_disk_copies": 0,
        "new_helper_relative": "xar_autoplayer/bridge/exact_clock_wait_progress_v1.py",
        "patch_scope": report["changed_Driver_function_ASTs"],
        "source_hooks": {
            "ingest": "After accepted state.ingest; copy connection token under Condition, release before collector lock.",
            "wait": "Observe existing candidate only; unchanged state/wait AST.",
            "lifetime": "Original Arm generation: pre-resume start, finally retire/freeze before cleanup.",
            "DTO": "Builder/extractor v2 exact keyset; same typed error/cause/MCP API.",
        },
        "diagnostic_contract": {
            "max_progress_bytes": 2048, "max_original_error_DTO_bytes": 8192,
            "bucket_count": 8, "bucket_width_ms": 5000,
            "bucket_meaning": "Python receipt time; empty means unobserved, not idle.",
            "authority": "Counters: accepted heartbeat. Candidate: identity/date/revision/paused only.",
            "flags_bits": {"1": "identity missing", "2": "identity/connection boundary", "4": "field missing", "8": "counter reset", "16": "local clock regressed", "32": "optional callback error"},
            "unknowns": "No native event time/fresh actor proof; candidate identity changes only at observations. No stop credit.",
            "bounded_storage": "4 metric rows, 8 buckets, 2 candidate rows; per-receipt no IO/query/encoding.",
        },
        "unmodified": ["unowned functions", "NativeProtocolState", "wait predicate/deadline/count",
                       "status/stop/cleanup", "MCP", "Native"],
        "earlier_design_finding": "A candidate-only cannot resolve the single 30s gap; B authorized. No A final test credit.",
        "qualification_scope": "5 focused nodes; whole inverses; changed-function ASTs",
        "first_seal_RED": {"gross": 59449, "source_cap": 57344, "documents_written": 0,
                           "test_result_dict_lost": True, "process_exit": 1},
        "Root_repartition": {"source_cap_bytes": 65536, "scratch_bytes": 0, "new_reservation": 0},
        "candidate_adopted": False, "performance_or_clock_fix_credit": 0,
        "operations": {"new_snapshot_RPC_Native_Game_Task_UAC_build": 0, "SDK_exports": 0,
                       "Git_writes": 0, "scratch_bytes": 0, "full_leaf_disk_copies": 0},
        "source_files_before_small_results": source_rows, "diff": {"path": "DIFF.patch", **pin(diff)},
    }
    qualification = {"schema": "xar.exact-clock-wait-progress-qualification.v1", "machine_id": MACHINE,
                     "observed_at_utc": now, **report,
                     "actual_CPP_or_Game_qualification": False, "whole_old_matrix_rerun": False}
    status = "SOURCE_READY_NOT_ADOPTED" if not report["failures"] and not report["errors"] else "SOFTWARE_RED_NOT_READY"
    plan_raw, proof_raw = encode(plan), encode(qualification)
    ready = {"schema": "xar.exact-clock-wait-progress-source-ready.v1", "machine_id": MACHINE,
             "observed_at_utc": now, "status": status,
             "plan": {"path": "PLAN.json", **pin(plan_raw)},
             "qualification": {"path": "QUALIFICATION.json", **pin(proof_raw)},
             "diff": {"path": "DIFF.patch", **pin(diff)}, "tests": {k: report[k] for k in ("tests", "failures", "errors", "duration_seconds")},
             "candidate_outputs_ref": "QUALIFICATION.json/output_pins", "future_writes_after_seal": 0,
             "scratch_bytes": 0, "Game_performance_clock_fix_credit": 0,
             "owned_qualifier_process_exit": "must be observed by caller after this return; not preclaimed"}
    for _ in range(3):
        ready_raw = encode(ready)
        ready["complete_new_source_logical_bytes"] = sum(v["bytes"] for v in source_rows) + len(diff) + len(plan_raw) + len(proof_raw) + len(ready_raw)
    ready_raw = encode(ready)
    gross = sum(v["bytes"] for v in source_rows) + len(diff) + len(plan_raw) + len(proof_raw) + len(ready_raw)
    if gross > 65536:
        raise ValueError("new source64K / scratch0 cap: " + str(gross))
    for name, raw in (("DIFF.patch", diff), ("PLAN.json", plan_raw),
                      ("QUALIFICATION.json", proof_raw), ("SOURCE-READY.json", ready_raw)):
        with (ROOT / name).open("xb") as stream:
            stream.write(raw)
    return {"status": status, "machine_id": MACHINE,
            "tests": ready["tests"], "new_source_logical_bytes": gross,
            "scratch_bytes": 0, "allocated_bytes": None, "future_writes": 0,
            "artifacts": {name: {"path": str(ROOT / name), **pin(raw)} for name, raw in
                          (("PLAN.json", plan_raw), ("QUALIFICATION.json", proof_raw), ("SOURCE-READY.json", ready_raw), ("DIFF.patch", diff))},
            "outputs": report["output_pins"]}
