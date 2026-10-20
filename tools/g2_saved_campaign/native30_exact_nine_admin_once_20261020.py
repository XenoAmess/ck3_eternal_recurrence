"""Root-reviewed one-shot exact-nine registration. No broker, build or EXE run."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
R = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
OUT = Path("D:/codex-ck3-demos/2026-10-20-project-exe-admin-once01")
MANIFEST = R / "attempt08-build/project-exe-manifest.json"
MANIFEST_SHA = "f35cf135db1a564bcb55b3b5c932059deb4369d0e06fd4a5ff006b25d80e57a7"
BUILD_SHA = "847b6b54f7e544315507dd5c0aa91e0d1abf992cecadd73c1a4fe2f9c94d6c85"
SID = "S-1-5-21-2908730481-166481001-1318755029-1001"
MACHINE = "xenoamess-full-tower-eb9d2c1186"
PINS = {
 "tools/g2_saved_campaign/native30_two_stage_qualification_20261020.py":"8fff948b9f119a3341b9afc5fa69e094c8a8bea7868812dd20b0579da63a8fef",
 "tools/g2_saved_campaign/native30_two_stage_admin_20261020.py":"52561e0d2ae7e3116953168d29154f7c8b1a7cad2a01a6d67058d3eaa4dfae9b",
 "tools/g2_saved_campaign/native30_resume_guard_20261019.py":"97330a4086bf13df858708935226cb8f6838294c6f5ac51eec8ee2767b925e5d",
 "tools/g2_saved_campaign/qualify_native30_fixture07_20261020.py":"b22eb598dbfdc01359dd1e15c65132b0fbb37bab23840df3b15b2e8ce32df4ae",
 "tools/project_exe_broker/windows_adapter.py":"88eb97048190b3a0caf89941a77701dfd9c5434f0c5d32e1deda00056bcd9f82"}


def need(value, message):
    if not value: raise RuntimeError(message)


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path)
    return {"path":str(path.resolve()),"bytes":path.stat().st_size,"sha256":digest(path)}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def write_once(name, value):
    data = (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    used = sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())
    need(used+len(data) <= 4194304,"full evidence exceeds224KiB; no truncation")
    with (OUT/name).open("xb") as stream: stream.write(data)


def setup(args, handles):
    need(os.name == "nt" and args.execute,"explicit Windows operation required")
    need(digest(__file__) == args.source_sha256 and Path(__file__).stat().st_size <= 32768,"reviewed source pin/32KiB")
    need(digest(args.card) == args.card_sha256,"exact512KiB capacity card")
    card = json.loads(args.card.read_bytes())
    need(card["machine_id"] == MACHINE and card["complete_packet_hard_bytes"] == 8454144
        and Path(card["new_evidence_root"]).resolve() == OUT.resolve()
        and Path(card["source_path"]).resolve() == Path(__file__).resolve(),"exact machine/root/source capacity")
    need(datetime.fromisoformat(card["review_at_utc"]) > datetime.now(timezone.utc),"capacity card expired")
    for name, expected in PINS.items(): need(digest(REPO/name) == expected,"reviewed dependency changed: "+name)
    q = load("exact9_q",REPO/"tools/g2_saved_campaign/native30_two_stage_qualification_20261020.py")
    a = load("exact9_a",REPO/"tools/g2_saved_campaign/native30_two_stage_admin_20261020.py")
    base = load("exact9_guard",REPO/"tools/g2_saved_campaign/native30_resume_guard_20261019.py").baseline()
    need(base.machine() == MACHINE,"actual machine differs")
    for path in [Path(__file__),args.card,*[REPO/name for name in PINS]]: q.lease(base,path,handles)
    identity, admin = a.actual_owner_admin()
    need(identity["sid"] == SID,"same authorized owner required")
    return q,a,base,identity,admin


def products(q, base, handles):
    need(digest(R/"attempt08-build/RESULT.json") == BUILD_SHA and digest(MANIFEST) == MANIFEST_SHA,"frozen original build/manifest")
    plan_path = REPO/"docs/ck3-native-ai/evidence/native30-wholeclean-producer-plan-2026-10-19.json"
    need(digest(plan_path) == "d9a44fc874bd253425626712eb17131f6986de5db17b74c5200b53cea3932bdb","original nine target/argv plan")
    plan = json.loads(plan_path.read_bytes())
    for path in (R/"attempt08-build/RESULT.json",MANIFEST,R/"owner08-build/owner-spec/CLOSED.json",plan_path):
        q.lease(base,path,handles)
    _, manifest, bindings = q.build_closed(base,{"old_plan":plan},handles)
    need(len(manifest["files"]) == len(bindings) == 9,"exact nine source-bound EXEs")
    helper_path = R/"source/tools/register_project_exe_exclusions.py"
    need(digest(helper_path) == "67c6021fcd5af209f409957fe045cfbc890da4eda72baf9a5bdf5b0c58d4701b","original helper pin")
    q.lease(base,helper_path,handles)
    helper = load("exact9_original_helper",helper_path)
    need(helper.opted_in(REPO),"actual local project EXE opt-in required before UAC/Add")
    fresh = helper.collect_manifest(REPO,Path(manifest["source_dir"]),Path(manifest["build_dir"]),
                                    manifest["configuration"],manifest["requested_targets"],manifest["external_candidate"])
    need(fresh == manifest,"actual CMake provenance/EXE bytes changed")
    return manifest, bindings, helper


def verify(q, base, result, manifest):
    need(result["machine_id"] == MACHINE and result["actual_admin"] is True and result["actual_sid"] == SID,
         "actual same-owner administrator result")
    check = {**result,"schema":"native30-exact-nine-admin-registration-v1","helper_receipt":result["helper_summary"]}
    q.verify_admin(check,manifest,pin(R/"attempt08-build/RESULT.json"),MACHINE)
    need(result["status"] == "verified" and result["future_writes"] == 0,"actual closed settings verification")
    need(pin(OUT/"helper-receipt.json") == result["helper_receipt_ref"],"actual original helper receipt binding")


def admin(args,q,a,base,identity,is_admin,handles):
    need(is_admin,"--admin requires an already elevated owner; no self-elevation fallback")
    need(OUT.is_dir() and not OUT.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,"actual non-reparse attempt directory")
    import win32security
    owner = win32security.GetFileSecurity(str(OUT),win32security.OWNER_SECURITY_INFORMATION).GetSecurityDescriptorOwner()
    need(win32security.ConvertSidToStringSid(owner) == SID,"attempt directory owner differs")
    intent = json.loads((OUT/"LAUNCH-INTENT.json").read_bytes())
    need(intent["source_sha256"] == args.source_sha256 and intent["card_sha256"] == args.card_sha256
         and intent["machine_id"] == MACHINE and intent["manifest_sha256"] == MANIFEST_SHA,"one exact ordinary launch intent")
    need(not any((OUT/n).exists() for n in ("STARTED.json","RESULT.json","LAUNCH-RESULT.json")),"single-use attempt; no replay")
    manifest, bindings, helper = products(q,base,handles)
    write_once("STARTED.json",{"machine_id":MACHINE,"utc":base.utc(),"admin_identity":identity,
                              "source_sha256":args.source_sha256,"card_sha256":args.card_sha256})
    result = {"schema":"project-exact-nine-admin-once-v1","machine_id":MACHINE,"start_utc":base.utc(),
        "status":"settings_failed","actual_admin":True,"actual_sid":identity["sid"],"admin_identity":identity,
        "source":pin(__file__),"card":pin(args.card),"manifest_sha256":MANIFEST_SHA,
        "build_result":pin(R/"attempt08-build/RESULT.json"),"exe_bindings":bindings,
        "before_settings":None,"after_settings":None,"verified_requested_paths":[],"helper_summary":None}
    client = None
    try:
        sys.path.insert(0,str(REPO/"tools/project_exe_broker"))
        from windows_adapter import SameAdminDefenderClient
        client = a.FullSettingsClient(SameAdminDefenderClient())
        result["before_settings"] = client.before
        # Original helper can repeat full path arrays in nullable-return observations.
        # Reserve their complete worst-case bytes before the first Add; never truncate.
        need(12*len(json.dumps(client.before,ensure_ascii=False).encode())+32768 <= 4194304,
             "actual settings require larger evidence capacity; no Add attempted")
        receipt = helper.register_manifest(manifest,OUT/"helper-receipt.json",admin=True,client=client,
                                          manifest_bytes=MANIFEST.read_bytes())
        result["helper_receipt_ref"] = pin(OUT/"helper-receipt.json")
        result["helper_summary"] = {k:receipt.get(k) for k in
            ("status","admin_token","observed_prior_settings_preserved","files")}
        result["verified_requested_paths"] = receipt.get("verified_requested_paths",[])
        client.read_paths()
        result["after_settings"] = client.after
        result.update(status="verified",future_writes=0)
        verify(q,base,result,manifest)
        need(all(q.same_file(x,y) for x,y in zip(bindings,q.exe_leases(base,manifest,handles))),"EXE identities changed")
    except BaseException as error:
        result.update(status="settings_failed",error={"type":type(error).__name__,"text":str(error)})
        a.preserve_final_settings(result,client)
    finally:
        result.update(end_utc=base.utc(),future_writes=0)
        write_once("RESULT.json",result)
    return 0 if result["status"] == "verified" else 1


def launch(args,q,a,base,identity,is_admin,handles):
    need(not is_admin,"ordinary launch only; no alternate elevated route")
    need(not OUT.exists(),"fresh attempt must be absent; never reuse cancelled/unknown attempt")
    OUT.mkdir(exist_ok=False)
    write_once("LAUNCH-INTENT.json",{"machine_id":MACHINE,"utc":base.utc(),"ordinary_identity":identity,
        "source_sha256":args.source_sha256,"card_sha256":args.card_sha256,"manifest_sha256":MANIFEST_SHA,
        "one_UAC_only":True,"previous08_cancel_future_writes":None})
    result = {"schema":"project-exact-nine-admin-once-launch-v1","machine_id":MACHINE,"start_utc":base.utc(),
        "ordinary_identity":identity,"status":"FAILED_OR_UNKNOWN","UAC_calls":0,"settings_success":False,
        "source":pin(__file__),"card":pin(args.card),"manifest":pin(MANIFEST),"future_writes":None}
    process = None
    com = None
    try:
        manifest, bindings, _ = products(q,base,handles)
        result["exe_bindings"] = bindings
        identity_path=Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime/interactive_task_owner_c16.py")
        need(digest(identity_path)=="c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f","frozen process identity reader")
        q.lease(base,identity_path,handles)
        identity_reader=load("exact9_child_identity",identity_path).Windows()
        sys.path.insert(0,str(REPO/"tools/project_exe_broker"))
        from windows_adapter import SameAdminDefenderClient
        old_plan = REPO/"docs/ck3-native-ai/evidence/native30-08B-two-stage-plan-revision3-2026-10-20.json"
        need(digest(old_plan) == "6043fd5240c9adbaa90ff3c1d61dd3832550a668382d75af1bf59019a2aa150a","pinned interpreter plan")
        python = json.loads(old_plan.read_bytes())["admin_python"]
        need(q.same_file(q.lease(base,python["path"],handles),python),"qualified interpreter changed")
        import pythoncom,win32api,win32event,win32process
        from win32com.shell import shell,shellcon
        pythoncom.CoInitialize();com=pythoncom
        command=["-I","-B",str(Path(__file__).resolve()),"--admin","--card",str(args.card.resolve()),
                 "--card-sha256",args.card_sha256,"--source-sha256",args.source_sha256,"--execute"]
        result.update(argv=command,UAC_calls=1)
        child=shell.ShellExecuteEx(fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,lpVerb="runas",lpFile=python["path"],
            lpParameters=subprocess.list2cmdline(command),lpDirectory=str(REPO),nShow=0)
        process=child["hProcess"]
        result["child_identity"]=identity_reader.identity(process)
        deadline=time.monotonic()+180
        while win32event.WaitForSingleObject(process,250)!=win32event.WAIT_OBJECT_0:
            if time.monotonic()>=deadline:raise TimeoutError("admin still running; preserve unknown, no termination/retry")
        result["actual_exit_code"]=win32process.GetExitCodeProcess(process)
        actual=json.loads((OUT/"RESULT.json").read_bytes())
        verify(q,base,actual,manifest)
        need(result["actual_exit_code"]==0,"actual administrator exit was not zero")
        result.update(status="VERIFIED",settings_success=True,admin_result=pin(OUT/"RESULT.json"))
    except BaseException as error:
        result["error"]={"type":type(error).__name__,"text":str(error)}
    finally:
        if process is not None:win32api.CloseHandle(process)
        if com is not None:com.CoUninitialize()
        result.update(end_utc=base.utc(),future_writes=0 if "actual_exit_code" in result or result["UAC_calls"]==0 else None)
        write_once("LAUNCH-RESULT.json",result)
        print(json.dumps({"status":result["status"],"settings_success":result["settings_success"],"receipt":pin(OUT/"LAUNCH-RESULT.json")}))
    return 0 if result["status"]=="VERIFIED" else 1


def main():
    parser=argparse.ArgumentParser(__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--launch",action="store_true");group.add_argument("--admin",action="store_true")
    parser.add_argument("--card",type=Path,required=True);parser.add_argument("--card-sha256",required=True)
    parser.add_argument("--source-sha256",required=True);parser.add_argument("--execute",action="store_true")
    args=parser.parse_args();handles=[]
    try:
        q,a,base,identity,elevated=setup(args,handles)
        return admin(args,q,a,base,identity,elevated,handles) if args.admin else launch(args,q,a,base,identity,elevated,handles)
    finally:
        for handle in reversed(handles):handle.Close()


if __name__=="__main__":raise SystemExit(main())
