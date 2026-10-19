"""Create only two small source-ready records; never prepares or runs a build."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
E = "docs/ck3-native-ai/evidence/"
T = "tools/g2_saved_campaign/"
ROOT = "D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01"
PACK = ("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/"
        "p51-fresh1066-v20261019-prepare01")
PLAN = E + "native30-resume-auxiliary-repair-plan-2026-10-19.json"
READY = E + "native30-resume-auxiliary-repair-source-ready-2026-10-19.json"
CODE = [T + name for name in (
    "build_native30_resume_20261019.py", "native30_resume_guard_20261019.py",
    "native30_msvc_auxiliary_policy_20261019.py", "native30_runtime_source_macro_restore_20261019.cmake",
    "test_native30_msvc_auxiliary_policy_20261019.py", "test_native30_resume_contract_20261019.py",
    "seal_native30_resume_source_20261019.py")]
RECORDS = [E + name for name in (
    "native30-configured-tree-macro-delta-2026-10-19.json",
    "native30-existing-config-output-inventory-2026-10-19.json",
    "native30-msvc-auxiliary-file-binding-2026-10-19.json")]

def pin(relative):
    body = (REPO / relative).read_bytes()
    return {"path": relative, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}

def write(relative, value):
    body = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()
    with (REPO / relative).open("xb") as output: output.write(body)
    return pin(relative)

def main():
    if any((REPO / relative).exists() for relative in (PLAN, READY)):
        raise RuntimeError("seal outputs must be absent; preserve prior records")
    machine = subprocess.run([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"],
        cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    if machine != "xenoamess-full-tower-eb9d2c1186": raise RuntimeError("wrong source-review machine")
    now = datetime.now(timezone.utc).isoformat()
    helper_paths = CODE[:4] + RECORDS + [T + "build_native30_wholeclean_20261019.py",
        E + "native30-wholeclean-producer-plan-2026-10-19.json",
        E + "native29-production-compile-macro-provenance-2026-10-19.json"]
    reference = lambda path: pin(path)
    plan = {
        "schema": "native30-separate-resume-source-plan-v1", "machine_id": machine,
        "observed_at_utc": now, "status": "SOURCE_READY_NOT_EXECUTION_ADMISSION",
        "root": ROOT, "attempt_root": ROOT + "/attempt02", "source_commit": "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747",
        "producer": reference(CODE[0]), "files": CODE + RECORDS + [PLAN, READY],
        "helper_pins": {path: pin(path)["sha256"] for path in helper_paths},
        "inventory": reference(RECORDS[1]), "auxiliary_binding": reference(RECORDS[2]),
        "overlay": reference(CODE[3]),
        "prior_closed_sha256": "5b9b052bc07c25fa55ef0c11186324257ef6b2cf099c5084eb6fdf175bdfd7c4",
        "budget": {"aggregate_hard_bytes": 1610612736, "source_charged_cap_bytes": 100663296,
            "metadata_cap_bytes": 83886080, "TEMP_cap_bytes": 402653184,
            "prior_retained_allocation_bytes": 117360240, "prior_retained_eof_bytes": 104821563,
            "new_independent_reservation_bytes": 0, "charge": "max(aggregate EOF, aggregate AllocationSize)",
            "model": "Old retained source/configuration/evidence plus all attempt02 and generated build writes coexist under the same original 1.5GiB hold. No prior-retained or helper-cleanup physical credit. Hard caps and phase reserve256MiB may stop a build; 1.5GiB is an admitted upper bound, not a measured future peak."},
        "protected": [ROOT + "/source", ROOT + "/evidence"],
        "mutable_after_new_release": [ROOT + "/build", ROOT + "/attempt02"],
        "reuse_contract": [
            "Actual immutable Git704 Native+four-tools freeze:5355 files/58356261 logical bytes; rehash and compare Git blobs before any write and after production/fixtures. No old Native26/29 objects or archive reuse.",
            "Actual selected graph has12 targets/995 compile rows;995 object outputs and23 artifacts absent. Preflight rechecks all absences and rejects binaries outside bounded identified CMake compiler probes.",
            "Before reconfigure, snapshot all selected old target descriptors/cache and the exact selected compile/link contract into attempt02. Old source and failed evidence remain byte-identical.",
            "One explicit CMAKE_PROJECT_INCLUDE deferred overlay appends the two M1-audited definitions only for runtime/src/ck3_12002.cpp. Reconfigure is necessary for those definitions; no probe-only Release reconfigure.",
            "After reconfigure enforce the original full macro/source/ABI guards, all original XAR/options/Release cache values, exact selected source set and argv. Only two unique /D additions on that one source are permitted; link/archive/artifact semantics stay identical.",
            "Runtime69 old definitions describe one representative TU, not all612 historical TUs. Other selected compile commands are preserved byte/order except the explicitly permitted two additions. No protocol XAR leakage."],
        "auxiliary_cleanup_contract": [
            "A retained root must be signaled and exit0 before a1s grace, then inspect only the newly created exact own Job, at most16 members.",
            "Validate all members first against actual compiler-directory canonical path+FileID(volume+128bit ID)+SHA256 for only vctip.exe/mspdbsrv.exe; retain process handles with birth and recheck IsProcessInJob before termination.",
            "Original root exit, forced helper termination and actual final Job0 are separate fields. Unknown member/changed membership/nonzero root/timeout is failure. No basename-only matching or global process enumeration.",
            "Failure may stop only that exact newly created Job. Backend initialization failure still takes this failure cleanup path. Cleanup failure keeps actual nonzero/unknown owned count and future-writesunknown, never a fabricated closed0.",
            "This new contract does not requalify old KeyboardInterrupt FAILED attempt. No hotpatch or old execute monkeypatch."],
        "pipeline": ["revalidate all committed code/source/tool/card pins and absent attempt02",
            "reconfigure with exact explicit overlay; FileAPI/full guards/995argv comparison",
            "build only bridge+runtime+protocol with<=4 BELOW_NORMAL workers/noMP; all TEMP root-owned",
            "after production root and ownJob exit, sequentially build/register exactEXE/readback/run each of the original9 fixtures; noALL/duplicateBridge",
            "actual Ninja dependency closure,5 exports,component members/payloads/map,immutable-source/evidence and noPDB/ILK checks",
            "new RESULT/FILES-CLOSED inventories aggregate root; preserve RED and stop after single failure"],
        "M3_artifacts": {"runtime_sources": ["src/ck3_12004_player_heir_candidate_v1.cpp",
            "src/campaign_player_heir_candidate_component12004_v1.cpp",
            "src/campaign_player_heir_candidate_component12004_v1_serializer.cpp"],
            "PUBLIC_defines_runtime_and_bridge": ["XAR_CK3_ENABLE_PLAYER_HEIR_CANDIDATE12004_V1=1",
                "XAR_CK3_ENABLE_CAMPAIGN_ROOT_PLAYER_HEIR_CANDIDATE12004_V1=1"],
            "archive": "Each fresh clean object selected exactly once; its sole named archive payload has identical byte length+SHA. No stub activation credit from names alone.",
            "map": "Original Read/ReadForCampaignRoot/AppendToCanonicalRoot plus BindImage. No new exports; actual loaded provider/H remainsunknown. Reuse unchanged prior4+19 Native/7+23SDK source audit, do not rerun whole matrix."},
        "additional_map_symbols": ["?BindImage@player_heir_candidate_v1@ck3_12004"],
        "new_admission_required_fields": ["status=ADMITTED", "machine_id", "root", "attempt_root",
            "hard_bytes=1610612736", "source_charge_cap_bytes=100663296", "jobs integer1..4",
            "source_commit=704bdd3362bdc282ed5f5f8cf31fd3f50b90d747", "implementation_commit=fullnewGitcommit",
            "producer_sha256", "plan_sha256", "aggregate_includes_prior_retained=true",
            "prior_retained_allocation_bytes=117360240", "new_reservation_bytes=0", "deadline_utc",
            "minimum_free_bytes>=2147483648 plus storage reserved growth", "quota_remaining_bytes>=hard_bytes"],
        "execute_argv_after_commit_card_and_Root_release": ["py", "-B", CODE[0], "--plan", PLAN,
            "--admission", "<new-exact-card-path>", "--admission-sha256", "<new-full-card-SHA256>", "--execute"],
        "prospective_Task": {"new_owner_spec_root": PACK + "/native30-build-owner02/owner-spec",
            "reuse_frozen_bootstrap": PACK + "/native30-build-owner01/interactive_task_owner_v1.py",
            "bootstrap_sha256": "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f",
            "role": "native_build", "stage": CODE[0], "stage_args": ["--plan", PLAN, "--admission",
                "<same-exact-card-path>", "--admission-sha256", "<same-full-card-SHA256>", "--execute"],
            "contract": "No spec/card placeholders written now. New absent owner-spec/new TaskName, same SID/session/InteractiveToken; bootstrap leases exact stage and admission. Native budgetroot may exist; producer alone requires attempt02absent. New owner metadata needs a separate bounded storage card. Root reads exact preparedspec before register/run release. No Task.Stop or blind retry."},
        "execution_limits": "CMake may generate/execute its compiler probes under child cap. Project fixture EXEs require exact existing Defender registration plus actual verified_requested_paths before execution. No new system setting, injector, Game/OBS/MCP access, DLL load, speed/SDK/flags change.",
        "CPlusPlus_qualification": "NOTRUN", "heavy_admission": "PENDING_NEW_AGGREGATE_CARD",
        "current_Runtime_changes": 0, "future_source_writes_after_seal": 0}
    plan_pin = write(PLAN, plan)
    pins = [pin(path) for path in CODE + RECORDS] + [plan_pin]
    proof = {"schema": "native30-resume-source-ready-v1", "machine_id": machine, "observed_at_utc": now,
        "identity_source": "Fresh tools/ck3_live_run_id.py machine; existing exact source/tool proofs carry same machine_id.",
        "status": "SOURCE_READY_CPP_NOTRUN_NO_TASK", "plan": plan_pin, "files_before_this_record": pins,
        "tests": {"command": "py -B -m unittest tools.g2_saved_campaign.test_native30_msvc_auxiliary_policy_20261019 tools.g2_saved_campaign.test_native30_resume_contract_20261019 -q",
            "last_actual_result": "43 PASS in0.028s", "tool_exec": "405836", "qualification": "Pure finite admission/argv/archive bytes and owned-cleanup mocks; no compiler, actual process termination or C++ business qualification.",
            "previous_actual_runs": ["16PASS0.001s/5d14db", "24PASS0.017s/45b58e", "42PASS0.018s/58659d"],
            "authoring_RED_preserved": ["3194c3 missing bracket SyntaxError, fixed before tests",
                "cb2b2b original full preflight RED missing2macros", "9585f3 macro projection missing hydration KeyError",
                "f37b83 unclassified ShowIncludes compilerprobe", "33a2ac bounded script projection limit"]},
        "independent_review": "M1 read-only exact704 include-chain review: these2main-TU definitions do not change shared layout/inline ABI; existing router/mailbox/Bridge source definitions unchanged. Scope limited to2macros, not612TU or actualCPP. M0 confirms frozen c0 native_build checks metadata root absence only; no budgetroot-absent requirement.",
        "historical_claims_preserved": "Original root exit0/configuredtrue did not close ownedJob; old attempt remainsFAILED. New cleanup explicitcontract is prospective. Old5355 immutable files and failed evidence remain protected.",
        "source_budget_hard_bytes": 131072, "old_stable_Task_helpers_not_charged_again": [
            reference(T + name) for name in ("prepare_native30_build_task_20261019.py",
            "inspect_native30_build_task_20261019.py", "diagnose_native30_owned_configure_20261019.py",
            "stop_native30_owned_configure_20261019.py")],
        "configure_or_build_started": False, "Task_prepared_or_registered": False,
        "Game_calls": 0, "DLL_loaded": False, "new_external_files": 0,
        "future_writes": 0, "allocated_bytes": None, "physical_credit_bytes": 0}
    ready_pin = write(READY, proof)
    gross = sum(row["bytes"] for row in pins) + ready_pin["bytes"]
    if gross > 131072: raise RuntimeError("repair package source cap exceeded: " + str(gross))
    print(json.dumps({"plan": plan_pin, "ready": ready_pin, "new_files": len(pins)+1,
        "gross_new_logical_bytes": gross, "future_writes": 0, "CPlusPlus": "NOTRUN"}))

if __name__ == "__main__": main()
