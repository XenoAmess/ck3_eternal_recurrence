"""Create-only plan/source proof; existing-input read preflight, no R writes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import native30_artifact_postcheck10_20261020 as p

REPO = p.REPO
DOC = REPO / "docs/ck3-native-ai/evidence"
PLAN = DOC / "native30-artifact-postcheck10-plan-2026-10-20.json"
PROOF = DOC / "native30-artifact-postcheck10-readonly-preflight-2026-10-20.json"
READY = DOC / "native30-artifact-postcheck10-source-ready-2026-10-20.json"
CARD = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE10-SOURCE48KiB-M6-SCRATCH-RETIRED01.json")
SEED_CARD = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE30-FUNCTIONAL09-SAMEAGGREGATE-META160MiB-ADMITTED01.json")
FILES = ["tools/g2_saved_campaign/" + v for v in (
    "native30_artifact_postcheck10_20261020.py", "test_native30_artifact_postcheck10_20261020.py",
    "seal_native30_artifact_postcheck10_20261020.py")] + [v.relative_to(REPO).as_posix() for v in (PLAN, PROOF, READY)]
CAP = 65536


def now():
    return datetime.now(timezone.utc).isoformat()


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def encode(body):
    return (json.dumps(body, indent=2) + "\n").encode()


def write(path, body):
    raw = encode(body)
    current = sum((REPO / r).stat().st_size for r in FILES if (REPO / r).exists())
    p.require(current + len(raw) <= CAP, "complete source48K")
    with path.open("xb") as output:
        output.write(raw)


def main():
    p.require(not any(path.exists() for path in (PLAN, PROOF, READY)), "new plan/proofs absent")
    p.require(not p.STAGE.exists() and not p.OWNER.parent.exists(), "new R roots absent")
    p.require(pin(CARD)["sha256"] == "672f7aa70c94a83843e15ce9327c09d82f89fbc51aa30f37a69e91dd86a37a9c", "source card pin")
    machine = subprocess.check_output(["py", "-B", str(REPO / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    p.require(machine == "xenoamess-full-tower-eb9d2c1186", "source machine")
    for name in FILES[:3]:
        compile((REPO / name).read_bytes(), name, "exec")
    plan = {
        "schema": "native30-artifact-postcheck10-plan-v1", "status": "SOURCE_ONLY_NOT_EXECUTION_ADMISSION",
        "machine_id": machine, "observed_at_utc": now(), "source_commit": p.SOURCE,
        "producer": pin(Path(p.__file__)), "source_files": FILES, "source_card": pin(CARD),
        "borrowed_refs_not_copied": [pin(p.F09_PATH), pin(p.F09.COMMON_PATH), pin(p.PLAN09)],
        "roots": {"aggregate": str(p.ROOT), "postcheck": str(p.STAGE), "owner": str(p.OWNER)},
        "phase": "artifact_postcheck_only", "future_stage_args": ["--plan", str(PLAN), "--admission", "<new exact card>",
            "--admission-sha256", "<fullSHA>", "--execute"],
        "caps": {"source_complete": CAP, "aggregate": 1610612736, "sourceR": 100663296,
                 "metadata": 167772160, "TEMP": 402653184, "new_metadata_including_owner": 8388608, "owner": 65536},
        "metadata_quote": {"old08_full": 131238080, "old08_admin_future_writes": None,
                           "old09_full": 16777216, "new10_full": 8388608, "combined": 156403904},
        "new_output_quote": {"inventory": 2097152, "tool_logs_and_summaries": 1048576,
                             "TEMP": 1048576, "owner_included": 65536, "hard": 8388608,
                             "no_binary_map_snapshot_command_log_copies": True},
        "reuse_authority": {"failed09_stays_FAILED": True, "exact_records": p.RECORD09,
            "only_reused_facts": "Nine exact original argv/exit0/Job0 + actual layout postchecker0 + NoWork + same build/9EXE bindings; new root1/bootstrap1/Job0 and Task absent confirmed.",
            "not_reused_as_PASS": "09 delivery/archive/map/source-final/last-EXE checks were not reached. New postcheck executes them independently."},
        "initial_reserve_correction": {"source_probe_original_RED": "00cb3d: unchanged Q.preflight currentMetadata+16MiB exceeds old128 after09 closed inventory; 0R writes, docs absent.",
            "source_path_probe_RED": "78808a: explicit Git-relative DATA leaf appended to the Native-only source root; corrected to frozen ROOT/source/Git-relative, no R writes.",
            "new_independent_glue": "Same prior-plan hash/helperpin/prior_pins/seed_pins/Q.Q.preflight/verify_seed/protected07/08seed/buildclosed/9identities, own reserve8 within private160 then old F09 private160 guard. Old Q/09/global state untouched."},
        "exports_contract": {"five_code_functions": list(p.FUNCTIONS), "one_DATA": p.DATA,
            "DATA_ordinal_for_this_artifact": 6, "DATA_RVA_for_this_artifact": p.DATA_RVA,
            "Directory_bytes": 2752, "alignment": 8, "raw_header": list(p.HEADER),
            "DATA_flags": "READ required, EXEC forbidden, WRITE permitted", "forwarders_ordinal_only_duplicates": "reject",
            "source_pins": p.SOURCE_PINS, "map_sha256": p.MAP_SHA,
            "no_callable_ability_or_installer_credit": True},
        "sequence": [
            "Exact Root-committed source/plan + fresh same-parent admission + new c0 SPEC direct Root release.",
            "Reacquire original09/08 closed refs, full5355/995/12/219+2globs/983 production leases and9EXE FileID+SHA. No continuous cross-Task custody claim.",
            "Fresh snapshot Ninja -n -d explain exactNoWork only; never build or execute project tests.",
            "PE64 AMD64 DLL six named exports, original5 executable functions, one exact nonEXEC DATA2752/header; stream map once for source/address/required symbols.",
            "Pinned MSVC lib /LIST, three unique exact clean runtime COFF payloads; noPDB/ILK; all production/source/prior evidence intact; final9EXE SHA/FileID and09 closed facts unchanged.",
            "New delivery and RESULT. Actual own Job0, new outer child/bootstrap0/Job0+Task absent separately reviewed before artifact qualification."],
        "contract": {"success_status": p.SUCCESS, "fixture_exec_this_phase": 0, "fixture_build_this_phase": 0,
            "only_external_tools": "Pinned Ninja dry-run and lib /LIST; no CMake/compiler or project EXE",
            "Defender_registration_pending": True, "OS_qualification": "UNKNOWN", "Game_camera_H": "NOTRUN",
            "prior_failures_requalified": False, "deployed": False},
        "future_writes": "source only; execution needs separate admission", "physical_credit_bytes": 0,
    }
    handles, started = [], now()
    try:
        # The existing09 card is only a readonly seed for the borrowed initial
        # input checks. It is explicitly NOT an admission to execute Native10.
        state, snapshot, protected, records, refs, bindings, original = p.preflight(
            plan, p.Q.finite_load(SEED_CARD), handles)
        dll = state["build"] / state["old_plan"]["dll_artifact"]
        with dll.open("rb") as stream:
            pe = p.inspect_pe_exports(stream)
        proof = {"schema": "native30-artifact10-readonly-source-preflight-v1", "machine_id": machine,
            "started_at_utc": started, "finished_at_utc": now(), "status": "READONLY_EXISTING_INPUTS_PASS",
            "execution_admission": False, "readonly_seed_card": pin(SEED_CARD),
            "producer": pin(Path(p.__file__)), "source_count": len(state["rows"]),
            "selected_rows": len(state["current"]["selected_compile_rows"]), "targets": len(state["current"]["targets"]),
            "production_leases": len(state["pinned_outputs"]), "regen_inputs": len(state["manifest_inputs"]["inputs"]),
            "nine_EXE_identities": len(bindings), "reused09_actual_runs": len(records["result"]["fixture_runs"]),
            "existing_DLL_PE_DATA": pe, "09_records": refs,
            "deferred_to_actual_postcheck_Task": ["fresh NoWork command", "full map/data-symbol and archive3payload checks", "final source/production/9EXE recheck", "new outer closure"],
            "R_writes": 0, "Task_calls": 0, "project_EXE_calls": 0, "UAC_calls": 0,
            "Game_calls": 0, "closed_input_handles_after": 0}
    finally:
        p.Q.close_handles(handles)
    write(PLAN, plan)
    write(PROOF, proof)
    files = [pin(REPO / name) for name in FILES if name != READY.relative_to(REPO).as_posix()]
    ready = {"schema": "native30-artifact-postcheck10-source-ready-v1", "status": "SOURCE_READY_NOT_EXECUTED",
        "machine_id": machine, "observed_at_utc": now(), "plan": pin(PLAN), "readonly_preflight": pin(PROOF),
        "tests": {"passed": 6, "failed": 0, "unittest_seconds": 0.001, "actual_output": "a32fad", "mock_CPP_qualification": False},
        "files_excluding_this_ready": files, "full_logical_bytes": 0, "hard_bytes": CAP,
        "future_writes": 0, "allocated_bytes": None, "owned_children": 0, "physical_credit_bytes": 0}
    for _ in range(4):
        ready["full_logical_bytes"] = sum(v["bytes"] for v in files) + len(encode(ready))
    write(READY, ready)
    print(json.dumps({"plan": pin(PLAN), "proof": pin(PROOF), "ready": pin(READY),
                      "full_logical_bytes": ready["full_logical_bytes"], "future_writes": 0}, indent=2))


def finalize_after_cap_red():
    """Append closure only: Root forbids repeating the completed read preflight."""
    supplement = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE10-SOURCE64KiB-SUPPLEMENT01.json")
    p.require(pin(supplement)["sha256"] == "698f9e9115a8f627dd767b3375029733dc8faca016a11d203b00767fa4eb666b", "source64 supplement")
    final_plan = DOC / "native30-artifact-postcheck10-plan-revision2-2026-10-20.json"
    p.require(PLAN.is_file() and not any(path.exists() for path in (PROOF, READY, final_plan)), "exact partial-plan state")
    p.require(not p.STAGE.exists() and not p.OWNER.parent.exists(), "no actual stage/owner")
    original = json.loads(PLAN.read_bytes())
    p.require(original["producer"] == pin(Path(p.__file__)), "post-readonly production source unchanged")
    FILES.append(final_plan.relative_to(REPO).as_posix())
    plan = {"schema": original["schema"], "revision": 2, "machine_id": original["machine_id"],
        "source_commit": p.SOURCE, "status": "SOURCE_ONLY_NOT_EXECUTION_ADMISSION", "producer": pin(Path(p.__file__)),
        "source_files": FILES, "original_partial_plan": pin(PLAN), "source64_supplement": pin(supplement),
        "full_source_cap_bytes": CAP, "roots": original["roots"], "phase": original["phase"],
        "future_stage_args": ["--plan", str(final_plan), "--admission", "<new exact card>",
                              "--admission-sha256", "<fullSHA>", "--execute"],
        "caps": {**original["caps"], "source_complete": CAP}, "metadata_quote": original["metadata_quote"],
        "protocol_contract": "All original partial-plan artifact/reuse/exports/sequence requirements remain. Only source cap/plan entrypoint corrected. Old Q/09 and71f8c6 stay unchanged.",
        "observed_at_utc": now()}
    proof = {"schema": "native30-artifact10-readonly-source-preflight-v1", "machine_id": original["machine_id"],
        "status": "READONLY_PRECHECK_RETURNED_PE_PASS_THEN_SOURCE_SEAL_CAP_RED",
        "control_flow_evidence": {"exec": "71f8c6", "duration_seconds": 9.7715523,
            "reached": "seal main115 write(PROOF,proof), after p.preflight and inspect_pe_exports returned",
            "exception": "RuntimeError complete source48K", "PLAN_written": True, "PROOF_READY_written": False,
            "actual_full_structured_preflight_payload": None,
            "payload_limit": "The read process ended before persisting its dict; do not invent actual counter values or timestamps from that lost RAM.",
            "tests_preserved": "a32fad six PASS/0.001s; not rerun"},
        "validated_by_returned_function_contract": ["same5355/995/12/219+2globs/983 and9originalEXE guards",
            "09 exactly bound nine closed argv/exit0/Job0/layout/noWork and failed outer Task absence",
            "actual existing DLL PE64 five code exports plus exact DATA RVA/2752/raw64 header/readable-nonEXEC"],
        "source_corrections": original["initial_reserve_correction"],
        "execution_admission": False, "preflight_or_matrix_repeated_after_cap_supplement": False,
        "R_writes": 0, "Task_calls": 0, "project_EXE_calls": 0, "UAC_calls": 0, "Game_calls": 0,
        "deferred": ["fresh NoWork command", "map/data-source and archive unique payload final checks", "final immutable/9identities", "new owner closure"]}
    write(final_plan, plan)
    write(PROOF, proof)
    refs = [pin(REPO / name) for name in FILES if name != READY.relative_to(REPO).as_posix()]
    ready = {"schema": "native30-artifact-postcheck10-source-ready-v1", "status": "SOURCE_READY_NOT_EXECUTED",
        "machine_id": original["machine_id"], "observed_at_utc": now(), "plan": pin(final_plan), "proof": pin(PROOF),
        "tests": {"passed": 6, "failed": 0, "unittest_seconds": 0.001, "actual_output": "a32fad", "new_CPP_credit": False},
        "files_excluding_this_ready": refs, "full_logical_bytes": 0, "hard_bytes": CAP,
        "future_writes": 0, "allocated_bytes": None, "owned_children": 0, "physical_credit_bytes": 0}
    for _ in range(4):
        ready["full_logical_bytes"] = sum(v["bytes"] for v in refs) + len(encode(ready))
    write(READY, ready)
    print(json.dumps({"plan": pin(final_plan), "proof": pin(PROOF), "ready": pin(READY),
        "full_logical_bytes": ready["full_logical_bytes"], "future_writes": 0}, indent=2))


if __name__ == "__main__":
    finalize_after_cap_red()
