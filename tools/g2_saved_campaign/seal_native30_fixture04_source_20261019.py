"""Seal the prospective exact no-PDB repair; no Native or Task writes."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
E, T = "docs/ck3-native-ai/evidence/", "tools/g2_saved_campaign/"
R = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
N = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
P = N/"p51-fresh1066-v20261019-prepare01"
OWNER03 = P/"native30-build-owner03/owner-spec"
PLAN = E+"native30-fixture04-nopdb-plan-2026-10-19.json"
READY = E+"native30-fixture04-nopdb-source-ready-2026-10-19.json"
CODE = [T+name for name in ("qualify_native30_fixture04_20261019.py", "native30_fixture04_override_20261019.cmake",
    "test_native30_fixture04_nopdb_20261019.py", "seal_native30_fixture04_source_20261019.py")]
FIXTURE = "ck3_autonomous_player/native_bridge/src/camera_tracking_v1_test.cpp"

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def repo_pin(relative): return {**pin(REPO/relative), "path": relative}
def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=2)+"\n").encode()

def main():
    if any((REPO/name).exists() for name in (PLAN, READY)): raise RuntimeError("preserve all old records")
    machine = subprocess.run([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"], cwd=REPO,
                             check=True, capture_output=True, text=True).stdout.strip()
    if machine != "xenoamess-full-tower-eb9d2c1186": raise RuntimeError("wrong machine")
    now = datetime.now(timezone.utc).isoformat()
    spec = importlib.util.spec_from_file_location("fixture04_sealed", REPO/CODE[0])
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    class Base:
        @staticmethod
        def pin(path): return pin(path)
    actual_link = q.closed_link_proof(Base, R/"attempt02/actual-generated-commands.log")
    fileapi = R/"build/.cmake/api/v1/reply/target-xar_ck3_bridge-Release-cf7f76aeeefcc7c49fe9.json"
    predicted = [row["path"] for row in json.loads(fileapi.read_bytes())["artifacts"]]
    if predicted != ["xar_ck3_bridge.dll", "xar_ck3_bridge.lib", "xar_ck3_bridge.pdb"]:
        raise RuntimeError("unexpected actual bridge prediction")
    if (R/"build/xar_ck3_bridge.pdb").exists(): raise RuntimeError("actual PDB contradicts old no-debug contract")
    helper_paths = [CODE[1], FIXTURE] + [T+name for name in ("build_native30_resume_20261019.py",
        "native30_resume_guard_20261019.py", "native30_msvc_auxiliary_policy_20261019.py",
        "build_native30_wholeclean_20261019.py")] + [E+name for name in (
        "native30-wholeclean-producer-plan-2026-10-19.json", "native29-production-compile-macro-provenance-2026-10-19.json",
        "native30-existing-config-output-inventory-2026-10-19.json", "native30-msvc-auxiliary-file-binding-2026-10-19.json")]
    priors = [R/name for name in ("attempt02/RESULT.json", "attempt02/FILES-CLOSED.json",
        "attempt02/selected-fileapi-graph.json", "attempt02/runtime-source-macro-restore.cmake",
        "attempt02/actual-generated-commands.log", "evidence/FILES-CLOSED.json", "evidence/source-freeze.json")]
    priors += [OWNER03/"CLOSED.json", OWNER03/"stage.stderr.log"]
    plan = {"schema": "native30-fixture04-exact-nopdb-plan-v1", "machine_id": machine, "observed_at_utc": now,
        "status": "SOURCE_READY_NOT_EXECUTION_ADMISSION", "root": str(R), "attempt_root": str(R/"attempt04"),
        "producer": repo_pin(CODE[0]), "files": CODE+[PLAN, READY],
        "helper_pins": {name: repo_pin(name)["sha256"] for name in helper_paths}, "prior_pins": [pin(path) for path in priors],
        "inventory": E+"native30-existing-config-output-inventory-2026-10-19.json",
        "binding": E+"native30-msvc-auxiliary-file-binding-2026-10-19.json", "overlay": CODE[1],
        "failure03": {"actual_failed_target": "xar_ck3_bridge", "actual_predicted_missing": str(R/"build/xar_ck3_bridge.pdb"),
            "FileAPI": pin(fileapi), "predicted_artifacts": predicted,
            "actual_DLL_LIB_MAP_present_PDB_absent": "Exact bridge directory metadata observation cc91f3; old03 stderr1236B/40b29d... and ownerCLOSED745B/9f53... preserved",
            "root_cause": "8304 producer incorrectly required the FileAPI-predicted PDB despite the unchanged explicit no-debug/no-PDB contract. Implementation error; not a C++ or actual fixture failure.",
            "Native_attempt03_directory": "never created", "Native_RESULT": "does not exist; not fabricated",
            "Task": "actualstage1/bootstrap1/Job0 at18:12:44.134381Z, freshTasklast1 then exactunregister18:13:57.501581Z absent_aftertrue(tool5d152b)",
            "Native_configure_compile_fixture_calls": 0},
        "actual_closed_link_no_pdb": actual_link,
        "known_not_generated_policy": [
            "Only target xar_ck3_bridge and exact build-relative xar_ck3_bridge.pdb can be classified known_not_generated; must be absent both now and from prior closed inventory",
            "Actual immutable attempt02 command log must contain one unique bridge link line with exact /out and /pdb filenames; no DEBUG/DEBUGTYPE, explicit only INCREMENTAL:NO; all source/command SHA pins checked",
            "No generic suffix skip. Another missing predicted artifact or path outsidebuild stillfails. DLL/lib/map and every production object remain mandatory and leased. Actual PDB presencefails before reuse and at final whole-build noPDB/ILK check",
            "Record FileAPI prediction/sourcepin, actuallink linehash/options, current and prior absence in reuse/result receipts; predicted PDB is not listed as an actual retained file"],
        "original_source_and_success": {"Native_commit": "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747",
            "frozen_files": 5355, "production_objects": 977,
            "original_production_root0_Job0": "attempt02 three targets17:12:48.953768Z→17:26:03.216880Z; overall attempt02 remainsFAILED at fixture1 strcpy",
            "fixed_fixture": repo_pin(FIXTURE), "fixture_source_status": "Already committed367 memcpy sizeofliteral includingNUL; no additional CPP/production edits in04",
            "immutable": [str(R/"source"), str(R/"evidence"), str(R/"attempt02"), str(OWNER03)],
            "new_copy": str(R/"build/native30-fixture04/camera_tracking_v1_test.cpp")},
        "pipeline": ["Exact newcard/newimplementation/helperpins; absent attempt04 and new generated fixturecopy directory",
            "Verify5355Git/source hashes, successful production command evidence, actual FileAPI and every production argv/source",
            "Classify only evidenced exact predictedPDB as known_not_generated; verify977obj+DLL/lib/map names/EOF/timewindow against oldclosed inventory and freshly SHA/FileID-pin under readonly/no-delete leases",
            "Generate one fixed fixturecopy, deferred override only fixture1 TU while including original frozen attempt02 two-macro overlay",
            "UnchangedXAR/Release/options; graph/argv/link/artifact semantic equality except single fixture source/object paths; explicit production Ninja dry-run must say no work",
            "Only build fixture1 and remaining8 named fixtures sequentially; exact Defender actual verified_requested_paths before execution; layoutreport postchecker; noALL/duplicateBridge",
            "Actual Ninja dependencies,5exports,3component unique archivepayload identity,required Read/BindImage/campaign map symbols; wholebuild noPDB/ILK; production/source/oldfailed evidence unchanged",
            "NewRESULT/FILES-CLOSED under04; anyfailure stops/no replay. Readonly production handles prevent hidden recompilation/relink"],
        "identity_limits": "Fresh output SHA/FileID is first observed at reuse, not invented as an old historical hash. Prior closed name/EOF, successful command window1stolerance and protected custody bind provenance. All other03 safety/qualification gates retained.",
        "budget": {"same_aggregate_hard_bytes": 1610612736, "prior_retained_allocation_bytes": 659564464,
            "new_reservation_bytes": 0, "source_cap_bytes": 100663296, "metadata_cap_bytes": 83886080,
            "TEMP_cap_bytes": 402653184, "phase_reserve_bytes": 268435456, "jobs": "int1..4 BELOW_NORMAL/noMP",
            "charge": "oldretained+allnewwrites under max(aggregate EOF,AllocationSize)", "physical_credit_bytes": 0},
        "new_flat_card": ["ADMITTED/same machine/root/attempt_root04", "hard_bytes1610612736/source_charge_cap_bytes100663296/jobsstrictint1..4",
            "aggregate_includes_prior_retained=true/prior_retained_allocation_bytes659564464/new_reservation_bytes0",
            "source_commit704bdd3362bdc282ed5f5f8cf31fd3f50b90d747/implementation_commit fullnewcommit",
            "producer_sha256/plan_sha256/deadline_utc/freshminimum_free_bytes>=2GiBplusglobalfloor/quota_remaining_bytes>=hard"],
        "execution_argv_after_commit_card_and_Rootrelease": ["py", "-B", CODE[0], "--plan", PLAN,
            "--admission", "<new exact card>", "--admission-sha256", "<new fullSHA>", "--execute"],
        "new_Task": {"owner_spec": str(P/"native30-build-owner04/owner-spec"),
            "prepare_module": str(N/"robert30-v20261019-campaign01/runtime/interactive_task_owner_c16.py"),
            "bootstrap": str(P/"native30-build-owner01/interactive_task_owner_v1.py"),
            "both_source_SHA": "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f",
            "contract": "Existing independent c0module/c0bootstrap; noaf9/nocopy/nohardlink. Newmetadata card, create-only owner04/absentspec, native_build role, canonical backslashadmissionargv. Root directSPECread then register→readback→runonce. Actualexit/Job0 beforeunregister."},
        "qualification": "20finite softwarechecks only. No04 CMake/compiler/Defender/fixture/Game qualification. Need9actualfixtures+allartifact checks for offlinecandidate; loadedcamera/provider/H separate.",
        "Game_OBS_MCP_SDK_flags_changes": 0, "Native_or_Task_started": False, "future_source_writes_after_seal": 0}
    plan_data = encoded(plan)
    plan_pin = {"path": PLAN, "bytes": len(plan_data), "sha256": hashlib.sha256(plan_data).hexdigest()}
    pins = [repo_pin(path) for path in CODE]
    ready = {"schema": "native30-fixture04-source-ready-v1", "machine_id": machine, "observed_at_utc": now,
        "machine_identity_source": "Fresh tools/ck3_live_run_id.py machine", "status": "SOURCE_READY_CPP_NOTRUN",
        "plan": plan_pin, "sources": pins, "fixed_fixture_unchanged_input": repo_pin(FIXTURE),
        "tests": {"command": "py -B -m unittest tools.g2_saved_campaign.test_native30_fixture04_nopdb_20261019 -q",
            "actual": "20PASS/0.083s", "tool_exec": "c49790", "earlier": ["19PASS/0.086s/1faec0", "20PASS/0.087s/aec934"],
            "scope": "No-debug exactlink, predicted-vs-real PDB, missing DLL/lib, foreign/otherPDB, outsidebuild, actual closed command, AST equivalence for retained source/argv/final guards and admission. Pure tests; no compiler/process termination/Task/Defender or Game."},
        "03_failure_preserved": {"stderr": pin(OWNER03/"stage.stderr.log"), "CLOSED": pin(OWNER03/"CLOSED.json"),
            "Task_unregistered_tool": "5d152b", "Native_result_missing": "pre-mkdir failure; never synthesize one"},
        "source64KiB_cap": 65536, "CPP_changes": 0, "old_sources_modified": 0, "new_external_files": 0,
        "Task_or_Native_started": False, "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    ready_data = encoded(ready)
    gross = sum(row["bytes"] for row in pins)+len(plan_data)+len(ready_data)
    if gross > 65536: raise RuntimeError("source64KiB bound beforewrites: "+str(gross))
    for name, data in ((PLAN, plan_data), (READY, ready_data)):
        with (REPO/name).open("xb") as output: output.write(data)
    print(json.dumps({"plan": plan_pin, "ready": repo_pin(READY), "newfiles": 6,
                      "gross_new_logical_bytes": gross, "future_writes": 0, "CPP": "NOTRUN"}))

if __name__ == "__main__": main()
