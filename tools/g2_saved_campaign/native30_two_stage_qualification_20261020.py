"""08B: build nine fixtures, separately register exact paths, then run nine.

No configuration, production rebuild, Game operation, or automatic elevation.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
BUILD = ROOT / "attempt08-build"
RUN = ROOT / "attempt08-run"
ADMIN = ROOT / "attempt08-admin"
SNAPSHOT = ROOT / "attempt07/production-manifest.ninja"
OWNER_BUILD = ROOT / "owner08-build/owner-spec"
OWNER_RUN = ROOT / "owner08-run/owner-spec"
OWNER_SID = "S-1-5-21-2908730481-166481001-1318755029-1001"
SCHEMA = "native30-two-stage-qualification-v1"
LABEL = "Native30 continuous hotspot tracking and idle realm overview"
SOURCE_COMMIT = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"

def require(value, text):
    if not value: raise RuntimeError(text)

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

Q = module("native30_immutable_07", HERE / "qualify_native30_fixture07_20261020.py")

def finite_load(path, cap=2*1024**2):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= cap, "bounded required JSON: "+str(path))
    return json.loads(path.read_bytes())

def close_handles(handles):
    for handle in reversed(handles): handle.Close()

def lease(base, path, handles):
    import win32file
    path = Path(path).resolve()
    handle = win32file.CreateFile(str(path), 0x80000000, 1, None, 3, 0x80, None)
    handles.append(handle)
    class Identity(ctypes.Structure):
        _fields_ = [("volume", ctypes.c_uint64), ("value", ctypes.c_ubyte*16)]
    identity = Identity()
    api = base.FileAPI()
    require(api.k.GetFileInformationByHandleEx(int(handle), 18, ctypes.byref(identity), ctypes.sizeof(identity)),
            "FileID unavailable")
    return {**base.pin(path), "file_id": {"volume_serial":str(identity.volume), "file_id":bytes(identity.value).hex()}}

def same_file(left, right):
    return (os.path.normcase(str(Path(left["path"]).resolve())) == os.path.normcase(str(Path(right["path"]).resolve()))
        and all(left[key] == right[key] for key in ("bytes", "sha256", "file_id")))

def capacity_identity(base, plan, card, args):
    require(card["status"] == "ADMITTED" and card["machine_id"] == base.machine(), "same-machine ADMITTED card")
    require(Path(card["root"]).resolve() == ROOT.resolve(), "same aggregate root")
    require(card["hard_bytes"] == 1610612736 and card["source_charge_cap_bytes"] == 100663296
        and card["metadata_charge_cap_bytes"] == 134217728 and card["TEMP_cap_bytes"] == 402653184,
        "unchanged aggregate/source96/metadata128/TEMP384")
    require(card["aggregate_includes_prior_retained"] is True and card["prior_retained_allocation_bytes"] == 706251512
        and card["new_reservation_bytes"] == 0, "prior retained included; no second reservation")
    require(type(card["jobs"]) is int and 1 <= card["jobs"] <= 4, "bounded workers")
    for key, expected in (("build_stage_root",BUILD),("run_stage_root",RUN),("admin_stage_root",ADMIN)):
        require(Path(card[key]).resolve() == expected.resolve(), "exact08B root: "+key)
    require(card["source_commit"] == SOURCE_COMMIT and base.digest(args.admission) == args.admission_sha256,
            "source704 and exact admission SHA")
    require(card["producer_sha256"] == base.digest(Path(__file__)) and card["plan_sha256"] == base.digest(args.plan),
            "producer/plan pins")
    require(card["minimum_free_bytes"] >= 2*1024**3 and card["quota_remaining_bytes"] >= card["hard_bytes"], "floor/quota")
    require(datetime.fromisoformat(card["deadline_utc"].replace("Z", "+00:00")) > datetime.now(timezone.utc), "expired")
    commit = card["implementation_commit"]
    for name in [*plan["helper_pins"], Path(__file__).relative_to(REPO).as_posix(), args.plan.resolve().relative_to(REPO).as_posix()]:
        require(hashlib.sha256(base.git("show",commit+":"+name)).hexdigest() == base.digest(REPO/name), "Git pin: "+name)

def card_check(base, plan, card, args):
    capacity_identity(base,plan,card,args)
    require(not (BUILD if args.phase == "build" else RUN).exists(), "new stage root must be absent")

def verify_seed(base, plan, state, handles):
    failed = finite_load(ROOT/"attempt07/RESULT.json")
    require(failed["status"] == "FAILED" and failed["error"] ==
        {"type":"AuxiliaryContractError","text":"original command exit 1"}
        and failed["owned_active_after"] == 0 and failed["future_writes"] == 0, "preserve exact07 FAILED")
    require(len(failed["phases"]) == 5 and all(r["returncode"] == 0 and r["owned_active_after"] == 0 for r in failed["phases"]),
        "only07 snapshot/NoWork/environment/build provenance is reusable")
    proof = finite_load(ROOT/"attempt07/snapshot-command-equivalence.json")
    require(proof["byte_identical"] is True and proof["original"]["sha256"] == proof["snapshot"]["sha256"],
            "07 expanded command equivalence")
    seed = lease(base,SNAPSHOT,handles)
    require(seed["sha256"] == state["manifest_inputs"]["manifest"]["sha256"], "retained snapshot differs from current original")
    for row in plan["seed_pins"]:
        actual = lease(base,row["path"],handles)
        require(actual["bytes"] == row["bytes"] and actual["sha256"] == row["sha256"], "07 seed changed")
    raw = (ROOT/"attempt07/production-no-work.log").read_text()
    Q.assert_no_work("\n".join(line for line in raw.splitlines() if not line.startswith("ninja: Entering directory")))
    return seed

def preflight(plan, card, handles, args=None):
    # Reuse the immutable read-only function, without changing any07 module globals.
    ref = plan["base_readonly_plan"]
    require(ref["path"] == "docs/ck3-native-ai/evidence/native30-fixture07-snapshot-plan-2026-10-20.json",
            "one exact prior plan")
    raw = (REPO/ref["path"]).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ref["sha256"] and plan["helper_pins"][ref["path"]] == ref["sha256"],
            "prior plan pinned and held by shared preflight")
    original = json.loads(raw)
    repair = {**plan,"prior_pins":original["prior_pins"]+plan["seed_pins"]}
    state = Q.preflight(repair,handles,card)
    base = state["base"]
    if args is not None: card_check(base,plan,card,args)
    snapshot = verify_seed(base,plan,state,handles)
    require(state["budget"].last["metadata"] + 16*base.MIB <= 128*base.MIB,
            "new evidence/two metadata roots/admin/close reserve exceeds metadata128")
    protected07 = [base.pin(path) for path in (ROOT/"attempt07").rglob("*") if path.is_file()]
    return state, snapshot, protected07

def exact_fixture_set(manifest, fixtures):
    expected = {str((ROOT/"build"/f["artifact"]).resolve()):f["target"] for f in fixtures}
    rows = manifest["files"]
    require(len(rows) == 9 and len(expected) == 9 and set(r["path"] for r in rows) == set(expected), "exact nine EXE paths")
    require(all(row["target"] == expected[row["path"]] and Path(row["path"]).suffix.lower() == ".exe" for row in rows),
            "nine declared targets; no DLL/interpreter/directory")
    require(len(set(row["path"].casefold() for row in rows)) == 9, "duplicate EXE")

def exe_leases(base, manifest, handles):
    result = []
    for row in manifest["files"]:
        value = lease(base,row["path"],handles)
        require(value["bytes"] == row["size"] and value["sha256"] == row["sha256"], "EXE differs from frozen manifest")
        result.append(value)
    return result

def settings_complete(settings):
    return isinstance(settings,dict) and set(settings) == {"ExclusionPath","ExclusionExtension","ExclusionProcess"} and all(
        isinstance(v,list) and all(isinstance(x,str) for x in v) for v in settings.values())

def verify_admin(receipt, manifest, build_ref, machine_id):
    require(receipt.get("machine_id") == machine_id, "admin receipt machine differs")
    require(receipt["schema"] == "native30-exact-nine-admin-registration-v1" and receipt["status"] == "verified"
        and receipt["actual_admin"] is True and receipt["actual_sid"] == OWNER_SID, "actual same-owner admin receipt")
    require(receipt["build_result"] == build_ref and receipt["manifest_sha256"] == hashlib.sha256(
        (BUILD/"project-exe-manifest.json").read_bytes()).hexdigest(), "admin build/manifest binding")
    before, after = receipt["before_settings"],receipt["after_settings"]
    require(settings_complete(before) and settings_complete(after), "complete same-client three-array settings")
    norm = lambda values:{os.path.normcase(os.path.normpath(v)) for v in values}
    require(norm(before["ExclusionPath"]) <= norm(after["ExclusionPath"]), "prior Path settings lost")
    require(all(set(before[k]) == set(after[k]) for k in ("ExclusionExtension","ExclusionProcess")), "non-path settings changed")
    expected = norm([r["path"] for r in manifest["files"]])
    require(expected <= norm(after["ExclusionPath"]) and expected == norm(receipt["verified_requested_paths"]), "all nine actual verified")
    inner = receipt["helper_receipt"]
    require(inner["status"] == "verified" and inner["admin_token"] is True
        and inner["observed_prior_settings_preserved"] is True, "original helper actual verified")
    require(inner["files"] == manifest["files"] and len(receipt["exe_bindings"]) == 9,
            "admin receipt exact nine files and identities")

def build_records(base):
    result = finite_load(BUILD/"RESULT.json")
    require(result.get("machine_id") == base.machine(), "build result machine differs")
    require(result["schema"] == SCHEMA and result["protocol_version"] == 1 and result["stage"] == "build_only"
        and result["status"] == "BUILD_READY_FOR_ADMIN" and result["owned_active_after"] == 0
        and result["future_writes"] == 0 and result["fixture_executions"] == 0, "build-only qualified closure")
    require(len(result["fixture_builds"]) == 9 and all(row["returncode"] == 0 and row["owned_active_after"] == 0
        for row in result["fixture_builds"]), "all nine actual successful builds")
    owner = finite_load(OWNER_BUILD/"CLOSED.json")
    require(owner.get("machine_id") == base.machine(), "build Task machine differs")
    require(owner["child_exit_code"] == 0 and owner["bootstrap_exit_code"] == 0 and owner["job_active_after_stage"] == 0
        and owner["forced_remaining_cleanup"] is False, "build Task root0/Job0")
    require(base.digest(BUILD/"project-exe-manifest.json") == result["project_exe_manifest"]["sha256"], "build manifest changed")
    manifest = finite_load(BUILD/"project-exe-manifest.json")
    return result,manifest

def verify_launch(launch, build_ref, admin_ref, machine_id):
    require(launch.get("machine_id") == machine_id, "admin launch machine differs")
    require(launch.get("schema") == "native30-exact-nine-admin-launch-v1"
        and launch.get("status") == "VERIFIED" and launch.get("settings_success") is True
        and type(launch.get("UAC_calls")) is int and launch["UAC_calls"] == 1
        and type(launch.get("actual_exit_code")) is int and launch["actual_exit_code"] == 0
        and type(launch.get("future_writes")) is int and launch["future_writes"] == 0,
        "administrator launch must be known successful and closed; late child result cannot qualify timeout")
    require(launch.get("build_result") == build_ref and launch.get("admin_result") == admin_ref,
            "launch build/admin result binding differs")

def run_handoff(base, args):
    # Finite closure check precedes shared production/EXE leases and every output write.
    result,manifest = build_records(base)
    build_ref,admin_ref = base.pin(BUILD/"RESULT.json"),base.pin(ADMIN/"RESULT.json")
    require(args.admin_receipt_sha256 and admin_ref["sha256"] == args.admin_receipt_sha256,
            "exact reviewed actual admin result SHA required")
    receipt = finite_load(ADMIN/"RESULT.json",4*base.MIB)
    verify_admin(receipt,manifest,build_ref,base.machine())
    require(type(receipt.get("future_writes")) is int and receipt["future_writes"] == 0,
            "administrator result not closed")
    verify_launch(finite_load(ADMIN/"LAUNCH-RESULT.json"),build_ref,admin_ref,base.machine())
    return result,manifest,receipt

def build_closed(base, state, handles):
    result,manifest = build_records(base)
    exact_fixture_set(manifest,state["old_plan"]["fixtures"])
    current = exe_leases(base,manifest,handles)
    require(len(current) == len(result["exe_bindings"]) and all(same_file(a,b) for a,b in zip(current,result["exe_bindings"])),
            "EXE FileID/bytes changed between stages; no automatic rebuild or registration")
    return result,manifest,current

def final_delivery(state, run_command, stage):
    base,resume,guard = state["base"],state["resume"],state["guard_module"]
    plan,build,source = state["old_plan"],state["build"],state["source"]
    dll,archive,map_file = (build/plan[k] for k in ("dll_artifact","runtime_artifact","map_artifact"))
    log = stage/"exports.log"
    run_command([state["tools"]["dumpbin"],"/exports",str(dll)],ROOT,log)
    import re
    exports = re.findall(r"^\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\w+)\s*$",log.read_text(),re.M)
    require(sorted(n for _,n in exports) == sorted(plan["exports"]), "five exports")
    require(all(s in map_file.read_text() for s in plan["required_map_symbols"]+
        ["?BindImage@player_heir_candidate_v1@ck3_12004"]), "required component map symbols")
    log = stage/"runtime-members.log"
    run_command([state["tools"]["lib"],"/LIST",str(archive)],ROOT,log)
    require(all(s in log.read_text() for s in plan["required_runtime_members"]), "component members")
    payloads,components = resume.archive_payloads(archive),[]
    for relative in plan["required_sources"]["xar_ck3_12002_runtime"]:
        path = (source/relative).resolve()
        rows = [r for r in Q.production_rows(state["current"],guard,["xar_ck3_12002_runtime"]) if Path(r["file"]).resolve() == path]
        require(len(rows) == 1, "one clean component source")
        output = guard.output_from_command(rows[0])
        output = output if output.is_absolute() else Path(rows[0]["directory"])/output
        identity = base.pin(output)
        members = [r for r in payloads if Path(r["name"]).name.lower() == output.name.lower()]
        require(len(members) == 1 and members[0]["bytes"] == identity["bytes"] and members[0]["sha256"] == identity["sha256"],
                "unique exact production component payload")
        components.append({"source":base.pin(path),"object":identity,"payload":members[0]})
    require(not list(build.rglob("*.pdb")) and not list(build.rglob("*.ilk")), "no PDB/ILK")
    return {"DLL":base.pin(dll),"runtime_archive":base.pin(archive),"map":base.pin(map_file),"exports":exports,
        "component_objects":components,"source_commit":SOURCE_COMMIT,"fixed_fixture":base.pin(Q.COPY),
        "native_build_label":LABEL,"native_build_label_is_metadata":True,"production_reused_from_attempt02":True,
        "prior_failures_requalified":False,"deployed":False,"actual_Game_provider_or_camera_qualification":"NOTRUN"}

def immutable(state, protected07):
    base = state["base"]
    require(all(base.digest(r["path"]) == r["sha256"] for r in state["pinned_outputs"]), "production changed")
    require(all(base.digest(r["path"]) == r["sha256"] for r in state["protected"]+protected07), "prior evidence changed")
    base.source_intact(ROOT,state["rows"])

def execute(args):
    import win32file
    handles = []
    try:
        plan,card = finite_load(args.plan),finite_load(args.admission)
        if args.phase == "run":
            guard_name = "tools/g2_saved_campaign/native30_resume_guard_20261019.py"
            require(hashlib.sha256((REPO/guard_name).read_bytes()).hexdigest() == plan["helper_pins"][guard_name],
                    "early handoff baseline loader pin")
            early_base = module("native30_08B_early_guard",REPO/guard_name).baseline()
            run_handoff(early_base,args)
        handles.append(win32file.CreateFile(str(args.plan),0x80000000,1,None,3,0x80,None))
        state,snapshot,protected07 = preflight(plan,card,handles,args)
        base,budget = state["base"],state["budget"]
        fixtures = state["old_plan"]["fixtures"]
        build_result,manifest,bindings = (None,None,None)
        if args.phase == "run":
            for path in (BUILD/"RESULT.json",BUILD/"project-exe-manifest.json",OWNER_BUILD/"CLOSED.json",
                         ADMIN/"RESULT.json",ADMIN/"LAUNCH-RESULT.json"):
                lease(base,path,handles)
            _,_,admin_receipt = run_handoff(base,args)
            build_result,manifest,bindings = build_closed(base,state,handles)
            require(all(same_file(a,b) for a,b in zip(bindings,admin_receipt["exe_bindings"])), "admin EXE identity differs")
        stage = BUILD if args.phase == "build" else RUN
        stage.mkdir(exist_ok=False)
        result = {"schema":SCHEMA,"protocol_version":1,"run_id":"native30-08B","stage":args.phase+"_only",
            "machine_id":card["machine_id"],"source_commit":SOURCE_COMMIT,"start_utc":base.utc(),"status":"FAILED",
            "plan":base.pin(args.plan),"admission":base.pin(args.admission),"phases":[],"command_attempts":[],
            "fixture_builds":[],"fixture_runs":[],"fixture_executions":0,"snapshot":snapshot,
            "prior07_FAILED":base.pin(ROOT/"attempt07/RESULT.json"),"production_recompiled":False,"Game_calls":0,"DLL_loaded":False}
        env = dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1")
        for name in ("CL","_CL_","LINK","CMAKE_BUILD_PARALLEL_LEVEL"): env.pop(name,None)
        temporary = stage/".msvc-temp/environment"
        temporary.mkdir(parents=True)
        env.update(TEMP=str(temporary),TMP=str(temporary))
        def run_command(command,cwd,log,timeout=1800):
            journal = {}
            result["command_attempts"].append(journal)
            phase = state["auxiliary"].run_owned(base,command,cwd,env,log,budget,state["binding"],timeout=timeout,state=journal)
            result["phases"].append(phase)
            return phase
        try:
            log = stage/"production-no-work.log"
            run_command([state["tools"]["ninja"],"-C",str(state["build"]),"-f",str(SNAPSHOT),"-n","-d","explain",*base.PRODUCTION],
                        state["build"],log)
            Q.assert_no_work("\n".join(v for v in log.read_text().splitlines() if not v.startswith("ninja: Entering directory")))
            base.write(stage/"input-summary.json",{"source_count":len(state["rows"]),"selected_rows":len(state["current"]["selected_compile_rows"]),
                "targets":len(state["current"]["targets"]),"production_rows":len(state["production"]),
                "production_leases":len(state["pinned_outputs"]),"regen_inputs":len(state["manifest_inputs"]["inputs"]),
                "configured_inputs":plan["configured_inputs_expected"],"snapshot":snapshot,"no_work":base.pin(log),
                "reference_current_graph":base.pin(ROOT/"attempt07/current-configured-graph.json"),"continuous_between_Tasks_lease_claim":False})
            if args.phase == "build":
                init = stage/"msvc-environment"
                init.mkdir()
                delta = init/"environment-delta.json"
                tool = ROOT/"source/tools/run_native_msvc.py"
                run_command([sys.executable,"-B",str(HERE/"native30_capture_msvc_environment_20261020.py"),
                    "--frozen-tool",str(tool),"--tool-sha",base.digest(tool),"--installation",str(Path(state["tools"]["vcvars64"]).parents[3]),
                    "--work",str(init),"--output",str(delta)],init,init/"initializer.log",180)
                values = finite_load(delta,512*1024)
                for name,path in values["tools"].items():
                    require(name in state["tools"] and base.digest(path) == base.digest(state["tools"][name]), "initialized tool changed")
                env.update(values["environment_delta"])
                require(not any(env.get(n) for n in ("CL","_CL_","LINK","CMAKE_BUILD_PARALLEL_LEVEL")), "unadmitted build flags")
                for number,fixture in enumerate(fixtures,1):
                    budget(256*base.MIB)
                    phase = run_command([state["tools"]["ninja"],"-C",str(state["build"]),"-f",str(SNAPSHOT),"-j",str(card["jobs"]),fixture["target"]],
                        state["build"],stage/("build-%02d.log"%number))
                    result["fixture_builds"].append(phase)
                    base.temp_closed(state["build"],stage)
                sys.path.insert(0,str(ROOT/"source/tools"))
                import register_project_exe_exclusions as defender
                manifest = defender.collect_manifest(REPO,state["source"],state["build"],"Release",[f["target"] for f in fixtures],"native30-08B")
                exact_fixture_set(manifest,fixtures)
                bindings = exe_leases(base,manifest,handles)
                base.write(stage/"project-exe-manifest.json",manifest)
                result.update(project_exe_manifest=base.pin(stage/"project-exe-manifest.json"),exe_bindings=bindings,status="BUILD_READY_FOR_ADMIN")
            else:
                result.update(build_result=base.pin(BUILD/"RESULT.json"),admin_result=base.pin(ADMIN/"RESULT.json"),
                    admin_launch_result=base.pin(ADMIN/"LAUNCH-RESULT.json"),exe_bindings=bindings)
                for number,fixture in enumerate(fixtures,1):
                    image = (state["build"]/fixture["artifact"]).resolve()
                    arguments = [v.replace("$MACHINE_ID",card["machine_id"]).replace("$OBSERVED_UTC",base.utc()) for v in fixture.get("args",[])]
                    log = stage/("fixture-%02d.log"%number)
                    result["fixture_executions"] += 1
                    phase = run_command([str(image),*arguments],state["build"],log,120)
                    result["fixture_runs"].append(phase)
                    if fixture.get("postcheck"):
                        require(fixture["postcheck"] in base.TOOLS,"frozen postchecker only")
                        run_command([sys.executable,"-B",str(ROOT/"source"/fixture["postcheck"]),str(log)],ROOT,stage/"layout-postcheck.log")
                capture = temporary/"actual-ninja-deps.txt"
                run_command([state["tools"]["ninja"],"-C",str(state["build"]),"-f",str(SNAPSHOT),"-t","deps"],state["build"],capture)
                base.write(stage/"actual-dependencies.json",base.dependencies(state["build"],capture,state["source"],state["old_plan"]["allowed_system_roots"]))
                capture.unlink()
                delivery = final_delivery(state,run_command,stage)
                delivery.update(build_result=base.pin(BUILD/"RESULT.json"),admin_result=base.pin(ADMIN/"RESULT.json"),
                    admin_launch_result=base.pin(ADMIN/"LAUNCH-RESULT.json"),run_result_path=str(stage/"RESULT.json"))
                base.write(stage/"production-delivery.json",delivery)
                result["status"] = "OFFLINE_QUALIFIED_NOT_DEPLOYED"
            immutable(state,protected07)
        except BaseException as error:
            result.update(status="FAILED",error={"type":type(error).__name__,"text":str(error)})
        finally:
            active = [r.get("owned_active_after") for r in result["command_attempts"]]
            result.update(end_utc=base.utc(),owned_active_after=sum(active) if all(type(v) is int for v in active) else None,
                future_writes=0 if all(v == 0 for v in active) else None,sampled_peak_eof=budget.peak_eof,sampled_peak_allocation=budget.peak_allocation)
            base.write(stage/"RESULT.json",result)
            inventory = base.inventory(ROOT,base.FileAPI())
            base.write(stage/"FILES-CLOSED.json",{"machine_id":card["machine_id"],"closed_utc":base.utc(),"future_writes":result["future_writes"],
                "files_before_this_manifest":inventory})
            final = budget()
            print(json.dumps({"result":base.pin(stage/"RESULT.json"),"closed":base.pin(stage/"FILES-CLOSED.json"),
                "aggregate_final_eof":final["eof"],"aggregate_final_allocation":final["allocation"],
                "future_writes":result["future_writes"],"owned_active_after":result["owned_active_after"]}))
        return 0 if result["status"] in ("BUILD_READY_FOR_ADMIN","OFFLINE_QUALIFIED_NOT_DEPLOYED") else 1
    finally: close_handles(handles)

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--phase",choices=("build","run"),required=True)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--admission",type=Path,required=True)
    parser.add_argument("--admission-sha256",required=True)
    parser.add_argument("--admin-receipt-sha256")
    parser.add_argument("--execute",action="store_true")
    args = parser.parse_args()
    require(os.name == "nt" and args.execute,"explicit Windows execution")
    return execute(args)

if __name__ == "__main__": raise SystemExit(main())
