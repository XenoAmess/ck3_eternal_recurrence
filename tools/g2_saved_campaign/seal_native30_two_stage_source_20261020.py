"""Freeze08B source and exercise all available read-only prerequisites."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[2]
T,E = "tools/g2_saved_campaign/","docs/ck3-native-ai/evidence/"
CODE = [T+name for name in ("native30_two_stage_qualification_20261020.py","native30_two_stage_admin_20261020.py",
    "test_native30_two_stage_20261020.py","seal_native30_two_stage_source_20261020.py")]
HISTORY = [E+name for name in ("native30-08B-two-stage-plan-2026-10-20.json",
    "native30-08B-readonly-preflight-2026-10-20.json","native30-08B-source-ready-2026-10-20.json")]
PLAN = E+"native30-08B-two-stage-plan-revision2-2026-10-20.json"
PROOF = E+"native30-08B-readonly-preflight-revision2-2026-10-20.json"
READY = E+"native30-08B-source-ready-revision2-2026-10-20.json"

def pin(path):
    path=Path(path)
    raw=path.read_bytes()
    return {"path":str(path),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def rp(path): return {**pin(REPO/path),"path":path}
def raw(value): return (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode()

def main():
    if any((REPO/p).exists() for p in (PLAN,PROOF,READY)): raise RuntimeError("preserve source records")
    spec=importlib.util.spec_from_file_location("native30_08B_seal",REPO/CODE[0])
    q=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    previous=json.loads((REPO/(E+"native30-fixture07-snapshot-plan-2026-10-20.json")).read_bytes())
    helper=dict(previous["helper_pins"])
    base_plan_ref=rp(E+"native30-fixture07-snapshot-plan-2026-10-20.json")
    helper[base_plan_ref["path"]]=base_plan_ref["sha256"]
    helper[T+"qualify_native30_fixture07_20261020.py"]="b22eb598dbfdc01359dd1e15c65132b0fbb37bab23840df3b15b2e8ce32df4ae"
    for name in (CODE[1],"tools/project_exe_broker/windows_adapter.py","tools/project_exe_broker/installer_core.py",
                 "tools/project_exe_broker/native_safety.py"):
        helper[name]=rp(name)["sha256"]
    seeds=[pin(q.ROOT/name) for name in ("attempt07/RESULT.json","attempt07/snapshot-command-equivalence.json",
        "attempt07/production-no-work.log","attempt07/snapshot-identity.json")]
    card_path=Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE30-FIXTURE-ATTEMPT07-ADMITTED01.json")
    card=json.loads(card_path.read_bytes())
    plan={"schema":"native30-08B-two-stage-plan-v1","revision":2,"machine_id":"xenoamess-full-tower-eb9d2c1186",
        "observed_at_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_NOT_EXECUTION_ADMISSION",
        "files":CODE+HISTORY+[PLAN,PROOF,READY],"preserved_revision1":[rp(p) for p in HISTORY],
        "producer":rp(CODE[0]),"admin_producer":rp(CODE[1]),
        "source_commit":q.SOURCE_COMMIT,"helper_pins":helper,"base_readonly_plan":base_plan_ref,
        "inventory":previous["inventory"],"binding":previous["binding"],"configured_inputs_expected":previous["configured_inputs_expected"],
        "seed_pins":seeds,"roots":{"aggregate":str(q.ROOT),"build":str(q.BUILD),"run":str(q.RUN),"admin":str(q.ADMIN),
            "owner_build":str(q.OWNER_BUILD),"owner_run":str(q.OWNER_RUN)},
        "snapshot_reused_readonly":str(q.SNAPSHOT),"copy_snapshot_or_commands":False,
        "protocol":{"schema":q.SCHEMA,"protocol_version":1,"run_id":"native30-08B",
            "build_status":"BUILD_READY_FOR_ADMIN","run_status":"OFFLINE_QUALIFIED_NOT_DEPLOYED",
            "admin_schema":"native30-exact-nine-admin-registration-v1",
            "leases":"Not continuous across Tasks. Admin and run reacquire SHA/FileID leases and reject drift; never rebuild/re-register silently."},
        "budget":{"same_aggregate_hard_bytes":1610612736,"prior_retained_allocation_bytes":706251512,"new_reservation_bytes":0,
            "source_cap_bytes":100663296,"metadata_cap_bytes":134217728,"TEMP_cap_bytes":402653184,
            "all_new_metadata_upper_bytes":16*1024**2,"including_two_owner_caps":2*65536,"including_admin_proof_cap":4*1024**2,
            "jobs":4,"priority":"BELOW_NORMAL","compiler_MP":False,"physical_credit":0},
        "execution":[
            "One new build-only c0 native_build Task after exactSPEC Rootrelease. Recheck5355/995/12/219+two physical globs/983production leases and exact failed07 seed; no old FAILED requalified. Reuse byte-identical07snapshot -f at original buildcwd; actual productionNoWork. Frozen MSVC initializer, sequential nine selected Ninja-f builds, no CMake or projectEXE execution. Freeze one current FileAPI exact9 EXE manifest and FileID/SHA bindings. Native result BUILD_READY_FOR_ADMIN plus actual outer root0/Job0, exactTaskunregister before admin handoff.",
             "After all9products and manifest are frozen, Root reviews concrete admin argv/buildRESULTSHA/receipt paths; sole operator coordinates runtime screen exclusive/checkpoint/recording boundary. One explicit ShellExecuteEx runas (no bypass, no desktop/global input). Same-owner actual admin first requires actual owner-SID non-reparse ADMIN directory, then creates STARTED exclusively with actual PID/birth/SID/machine/build/manifest before any WMI. Existing STARTED/RESULT/LAUNCH prevents re-entry; unknown future prohibits repeat Add/UAC. One real SameAdminDefenderClient observes all three arrays. Existing immutable register_manifest with real full-settings adapter only ExclusionPath exact9files. None/error/partial always fresh readback; preserve latest raw actual three arrays even if validation fails, with settings_failed/error distinct. No interpreter/directory/extension/process exclusion. Before/after and full9 verified actual receipt required; cancellation/timeout or unexpected process remains FAILED_OR_UNKNOWN with no run-only start.",
             "Run-only c0 native_build SPEC prepared only after actual admin result SHA and successful LAUNCH closure are available/reviewed. Before shared preflight, production/EXE leases or stage mkdir: finite build-only RESULT and Task CLOSED explicit same-machine/root0/Job0; admin receipt explicit same-machine and reviewed SHA, closed future0/exact9; LAUNCH explicit same-machine/schema VERIFIED/settings_success true/UAC_calls exactly1/actual_exit0/future0 with exact buildResult+adminResult refs. Timeout/unknown rejects even a late verified child RESULT. Shared fullpreflight then read-leases all five closure/manifest files and repeats identical handoff checks; all9 EXE SHA/FileID re-leases, registration/current identities equal. ProductionNoWork-f again; no fixture rebuild/second registration. Nine exact fixture argv including layout postchecker; dependency roots/five exports/three unique component archive payload/map symbols/noPDB/immutable original/source checks. Only full run root0/Job0+all9 execution0+actual adminverified permits OFFLINE_QUALIFIED_NOT_DEPLOYED delivery. No Game/load/Steam/provider/camera credit."],
        "prospective_build_argv":["py","-B",CODE[0],"--phase","build","--plan",PLAN,"--admission","<new exact card>","--admission-sha256","<SHA>","--execute"],
        "prospective_admin_argv":["<qualifiedPython>","-B",CODE[1],"--launch","--plan",PLAN,"--admission","<same card>","--admission-sha256","<SHA>","--build-result-sha256","<actual frozen buildresult SHA>","--execute"],
        "prospective_run_argv":["py","-B",CODE[0],"--phase","run","--plan",PLAN,"--admission","<same card>","--admission-sha256","<SHA>","--admin-receipt-sha256","<actual verified adminresult SHA>","--execute"],
        "metadata_roles":{"build":"native_build only --phase build","run":"native_build only --phase run; adminSHA mandatory"},
        "source_tests":{"count":16,"seconds":0.032,"tool":"exec00e412","scope":"pure mocks/AST only; no actual C++/WMI/UAC"},
        "future_source_writes_after_seal":0,"system_or_Task_or_R_writes":0}
    handles=[]
    started=datetime.now(timezone.utc).isoformat()
    begin=time.monotonic()
    try:
        q.require(all(not p.exists() for p in (q.BUILD,q.RUN,q.ADMIN,q.OWNER_BUILD.parent,q.OWNER_RUN.parent)),"all08 roots absent")
        state,snapshot,_=q.preflight(plan,card,handles)
        base=state["base"]
        q.require(base.machine()==plan["machine_id"],"machine")
        plan["admin_python"]=q.lease(base,Path(sys.executable),handles)
        measured=state["budget"].last
        quote=measured["metadata"]+plan["budget"]["all_new_metadata_upper_bytes"]
        plan["budget"].update(current_component_charges=measured,metadata_projected_upper_bytes=quote)
        proof={"schema":"native30-08B-readonly-preflight-v1","revision":2,"machine_id":base.machine(),"start_utc":started,
            "end_utc":base.utc(),"seconds":time.monotonic()-begin,"status":"ALL_EXISTING_INPUTS_PASS_FUTURE_NINE_NOT_BUILT",
            "source_count":len(state["rows"]),"selected_rows":len(state["current"]["selected_compile_rows"]),
            "targets":len(state["current"]["targets"]),"production_rows":len(state["production"]),
            "production_FileID_SHA_leases":len(state["pinned_outputs"]),"regen_inputs":len(state["manifest_inputs"]["inputs"]),
            "configured_inputs":plan["configured_inputs_expected"],"reused_snapshot":snapshot,
            "budget":plan["budget"],"admin_Python":plan["admin_python"],"lease_handles_closed":True,
            "future_stage_specific_gates":"Build9+Taskclosure+exact9manifest/UACactual3array+9identity/run9+final guard NOTRUN; no synthetic substitute.",
            "revision1_history":{"preserved":[rp(p) for p in HISTORY],
                "first_seal_failed_source_cap_bytes":69167,"first_seal_wrote_documents":False,
                "original_tests":"10PASS0.028s exec0e669e; after dedup10PASS0.034s exec99fa11",
                "review_findings":"run accepted child verified without known parent LAUNCH exit; failed after validation could lose raw arrays; explicit build/admin/launch machine gates missing. Revision1 not execution-ready."},
            "revision2_source_tests":plan["source_tests"],"R_Task_UAC_Game_mutations":0,"future_writes":0}
    finally: q.close_handles(handles)
    plan_raw,proof_raw=raw(plan),raw(proof)
    ref=lambda name,b:{"path":name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
    ready={"schema":"native30-08B-source-ready-v1","revision":2,"machine_id":plan["machine_id"],"status":"SOURCE_READY_CPP_UAC_NOTRUN",
        "sources":[rp(p) for p in CODE],"plan":ref(PLAN,plan_raw),"readonly_preflight":ref(PROOF,proof_raw),
        "preserved_revision1":[rp(p) for p in HISTORY],"source_tests":plan["source_tests"],"source_cap_bytes":98304,
        "future_writes":0,"allocated_bytes":None,"physical_credit_bytes":0}
    ready_raw=raw(ready)
    gross=sum(rp(p)["bytes"] for p in CODE+HISTORY)+len(plan_raw)+len(proof_raw)+len(ready_raw)
    q.require(gross<=98304,"complete source96KiB before write: "+str(gross))
    for name,value in ((PLAN,plan_raw),(PROOF,proof_raw),(READY,ready_raw)):
        with (REPO/name).open("xb") as stream: stream.write(value)
    print(json.dumps({"plan":rp(PLAN),"proof":rp(PROOF),"ready":rp(READY),"source_gross":gross,"future_writes":0}))

if __name__ == "__main__": main()
