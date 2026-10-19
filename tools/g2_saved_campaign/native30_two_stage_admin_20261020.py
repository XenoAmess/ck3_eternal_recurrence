"""One explicit OS-consented exact-nine registration; no broker installation."""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import stat
import sys
import time

HERE = Path(__file__).resolve().parent

def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

Q = module("native30_two_stage_admin_common",HERE/"native30_two_stage_qualification_20261020.py")

class FullSettingsClient:
    """Real one-client adapter; every paths read also observes all three arrays."""
    def __init__(self, client):
        self.client = client
        self.before = client.read_settings()
        self.after = self.before
        Q.require(Q.settings_complete(self.before),"complete administrator before settings")

    def read_paths(self):
        self.after = self.client.read_settings()
        Q.require(Q.settings_complete(self.after),"complete administrator settings read")
        Q.require(all(set(self.before[k]) == set(self.after[k]) for k in ("ExclusionExtension","ExclusionProcess")),
                  "Extension/Process changed; stop before another Add")
        norm = lambda values:{os.path.normcase(os.path.normpath(v)) for v in values}
        Q.require(norm(self.before["ExclusionPath"]) <= norm(self.after["ExclusionPath"]),"prior paths lost; stop")
        return self.after["ExclusionPath"]

    def add_path(self,path): return self.client.add_path(path)

def actual_owner_admin():
    c0 = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime/interactive_task_owner_c16.py")
    Q.require(hashlib.sha256(c0.read_bytes()).hexdigest() == "c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f","frozen identity reader")
    identity = module("native30_admin_identity_c0",c0).Windows().current()
    sid = identity["sid"]
    admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    Q.require(sid == Q.OWNER_SID,"same authorized owner SID required")
    return identity,admin

def begin_admin(base, identity, build_ref, manifest_sha256):
    # The launcher must have created this exact non-reparse directory for the owner.
    Q.require(Q.ADMIN.is_dir() and not (Q.ADMIN.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT),
              "actual administrator directory required; no reparse target")
    import win32security
    owner = win32security.GetFileSecurity(str(Q.ADMIN),win32security.OWNER_SECURITY_INFORMATION).GetSecurityDescriptorOwner()
    Q.require(win32security.ConvertSidToStringSid(owner) == Q.OWNER_SID,"administrator directory owner differs")
    Q.require(not (Q.ADMIN/"RESULT.json").exists() and not (Q.ADMIN/"LAUNCH-RESULT.json").exists(),
              "administrator attempt already finished or unknown; no repeat")
    birth = identity.get("creation_filetime") # frozen c0 identity() preserves FILETIME as decimal str.
    Q.require(type(identity.get("pid")) is int and identity["pid"] > 0
        and type(birth) is str and birth.isascii() and birth.isdecimal() and int(birth) > 0 and str(int(birth)) == birth
        and identity.get("sid") == Q.OWNER_SID,"actual administrator process identity required")
    marker = {"schema":"native30-exact-nine-admin-started-v1","machine_id":base.machine(),"utc":base.utc(),
        "identity":identity,"build_result":build_ref,"manifest_sha256":manifest_sha256,
        "unknown_future_prohibits_repeat":True}
    with (Q.ADMIN/"STARTED.json").open("x",encoding="utf-8") as stream:
        json.dump(marker,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
    return base.pin(Q.ADMIN/"STARTED.json")

def preserve_final_settings(result, client):
    if client is not None:
        try: client.read_paths()
        except BaseException as observed:
            result["final_read_error"] = {"type":type(observed).__name__,"text":str(observed)}
        finally:
            # Preserve actual arrays even when their validation fails; never promote status.
            result["before_settings"],result["after_settings"] = client.before,client.after

def elevated(args, state, plan, handles):
    base = state["base"]
    identity,admin = actual_owner_admin()
    Q.require(admin,"actual elevated owner required; no settings call attempted")
    built,manifest,bindings = Q.build_closed(base,state,handles)
    Q.require(base.digest(Q.BUILD/"RESULT.json") == args.build_result_sha256,"reviewed build result SHA")
    started = begin_admin(base,identity,base.pin(Q.BUILD/"RESULT.json"),base.digest(Q.BUILD/"project-exe-manifest.json"))
    sys.path.insert(0,str(Q.ROOT/"source/tools"))
    sys.path.insert(0,str(Q.REPO/"tools/project_exe_broker"))
    import register_project_exe_exclusions as helper
    from windows_adapter import SameAdminDefenderClient
    result = {"schema":"native30-exact-nine-admin-registration-v1","machine_id":base.machine(),
        "start_utc":base.utc(),"status":"settings_failed","actual_sid":identity["sid"],"actual_admin":admin,"started":started,
        "build_result":base.pin(Q.BUILD/"RESULT.json"),"manifest_sha256":base.digest(Q.BUILD/"project-exe-manifest.json"),
        "exe_bindings":bindings,"helper_receipt":None,"before_settings":None,"after_settings":None,
        "verified_requested_paths":[],"allowed_settings_operation":"ExclusionPath exact nine complete filenames only"}
    client = None
    try:
        client = FullSettingsClient(SameAdminDefenderClient())
        result["before_settings"] = client.before
        receipt = helper.register_manifest(manifest,Q.ADMIN/"helper-receipt.json",admin=True,client=client,
            manifest_bytes=(Q.BUILD/"project-exe-manifest.json").read_bytes())
        result["helper_receipt"] = receipt
        client.read_paths()
        result["after_settings"] = client.after
        result["verified_requested_paths"] = receipt.get("verified_requested_paths",[])
        result["status"] = "verified"
        Q.verify_admin(result,manifest,result["build_result"],base.machine())
        Q.require(all(Q.same_file(a,b) for a,b in zip(Q.exe_leases(base,manifest,handles),bindings)),"EXE changed during registration")
    except BaseException as error:
        result.update(status="settings_failed",error={"type":type(error).__name__,"text":str(error)})
        preserve_final_settings(result,client)
    finally:
        result.update(end_utc=base.utc(),future_writes=0)
        base.write(Q.ADMIN/"RESULT.json",result)
    return 0 if result["status"] == "verified" else 1

def launch(args,state,handles):
    base = state["base"]
    identity,admin = actual_owner_admin()
    Q.require(not admin,"launch is the explicit ordinary-owner OS consent path")
    Q.build_closed(base,state,handles)
    Q.require(base.digest(Q.BUILD/"RESULT.json") == args.build_result_sha256,"reviewed build result SHA")
    Q.require(not Q.ADMIN.exists(),"one new admin attempt; no resubmission")
    python = plan_python = Q.finite_load(args.plan)["admin_python"]
    current = Q.lease(base,python["path"],handles)
    Q.require(Q.same_file(current,plan_python),"qualified administrator interpreter changed")
    Q.ADMIN.mkdir(exist_ok=False)
    import pythoncom
    import win32api
    import win32event
    import win32process
    from win32com.shell import shell,shellcon
    pythoncom.CoInitialize()
    process = None
    result = {"schema":"native30-exact-nine-admin-launch-v1","machine_id":base.machine(),"start_utc":base.utc(),"operation":"one explicit ShellExecuteEx runas",
        "business_authorization":"AGENTS permanent exact project EXE exclusion; OS consent separately required",
        "build_result":base.pin(Q.BUILD/"RESULT.json"),"UAC_calls":0,"status":"FAILED_OR_UNKNOWN","settings_success":False}
    try:
        command = ["-I","-B",str(Path(__file__).resolve()),"--elevated","--plan",str(args.plan.resolve()),
            "--admission",str(args.admission.resolve()),"--admission-sha256",args.admission_sha256,
            "--build-result-sha256",args.build_result_sha256,"--execute"]
        result.update(python=current,argv=command,UAC_calls=1)
        child = shell.ShellExecuteEx(fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,lpVerb="runas",lpFile=python["path"],
            lpParameters=subprocess.list2cmdline(command),lpDirectory=str(Q.REPO),nShow=0)
        process = child["hProcess"]
        result["pid"] = win32process.GetProcessId(process)
        deadline = time.monotonic()+180
        while win32event.WaitForSingleObject(process,250) != win32event.WAIT_OBJECT_0:
            state["budget"]()
            if time.monotonic() >= deadline: raise TimeoutError("administrator process still running; do not terminate or resubmit")
        result["actual_exit_code"] = win32process.GetExitCodeProcess(process)
        receipt = Q.finite_load(Q.ADMIN/"RESULT.json",4*base.MIB)
        Q.verify_admin(receipt,Q.finite_load(Q.BUILD/"project-exe-manifest.json"),base.pin(Q.BUILD/"RESULT.json"),base.machine())
        Q.require(result["actual_exit_code"] == 0,"administrator actual nonzero exit")
        result.update(status="VERIFIED",settings_success=True,admin_result=base.pin(Q.ADMIN/"RESULT.json"))
    except BaseException as error:
        result["error"] = {"type":type(error).__name__,"text":str(error)}
    finally:
        if process is not None: win32api.CloseHandle(process)
        pythoncom.CoUninitialize()
        result.update(end_utc=base.utc(),future_writes=0 if "actual_exit_code" in result else None)
        base.write(Q.ADMIN/"LAUNCH-RESULT.json",result)
        print(json.dumps({"status":result["status"],"receipt":base.pin(Q.ADMIN/"LAUNCH-RESULT.json"),"settings_success":result["settings_success"]}))
    return 0 if result["status"] == "VERIFIED" else 1

def main():
    parser = argparse.ArgumentParser(__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--launch",action="store_true")
    choice.add_argument("--elevated",action="store_true")
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--admission",type=Path,required=True)
    parser.add_argument("--admission-sha256",required=True)
    parser.add_argument("--build-result-sha256",required=True)
    parser.add_argument("--execute",action="store_true")
    args = parser.parse_args()
    Q.require(os.name == "nt" and args.execute,"explicit Windows operation")
    handles = []
    try:
        plan,card = Q.finite_load(args.plan),Q.finite_load(args.admission)
        state,_,_ = Q.preflight(plan,card,handles)
        Q.capacity_identity(state["base"],plan,card,args)
        return launch(args,state,handles) if args.launch else elevated(args,state,plan,handles)
    finally: Q.close_handles(handles)

if __name__ == "__main__": raise SystemExit(main())
