"""Preserve both08B records; seal the actual c0 FILETIME string correction."""
import hashlib
import importlib.util
import json
from pathlib import Path
import time

REPO=Path(__file__).resolve().parents[2]
E="docs/ck3-native-ai/evidence/"
OLD=E+"native30-08B-two-stage-plan-revision2-2026-10-20.json"
PLAN=E+"native30-08B-two-stage-plan-revision3-2026-10-20.json"
NOTE=E+"native30-08B-c0-birth-correction-2026-10-20.json"
def pin(path):
    path=Path(path); raw=path.read_bytes()
    return {"path":str(path),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def rp(name): return {**pin(REPO/name),"path":name}
def encoded(value): return (json.dumps(value,ensure_ascii=False,indent=1)+"\n").encode()
def main():
    if any((REPO/p).exists() for p in (PLAN,NOTE)): raise RuntimeError("create-only correction records")
    old=json.loads((REPO/OLD).read_bytes())
    producer=REPO/old["producer"]["path"]
    spec=importlib.util.spec_from_file_location("native30_08B_birth_corrected",producer)
    q=importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
    sealer=Path(__file__).resolve().relative_to(REPO).as_posix()
    plan={**old,"revision":3,"producer":rp(old["producer"]["path"]),"admin_producer":rp(old["admin_producer"]["path"])}
    plan["helper_pins"][plan["admin_producer"]["path"]]=plan["admin_producer"]["sha256"]
    plan["files"]=list(dict.fromkeys(old["files"]+[sealer,PLAN,NOTE]))
    # The exact previous plan carries both historical three-document pin sets.
    plan.pop("preserved_revision1")
    plan["preserved_history_via"]=rp(OLD)
    plan["source_tests"]={"count":16,"seconds":0.038,"tool":"execa50a8e","scope":"pure mock/AST; actual c0 decimal FILETIME shape; no WMI/UAC"}
    plan["birth_interface"]={"source_sha256":"c0d76a7064996cafd7412f8f39ba2bb5c5cb6271627246b84e946c00bafb864f",
        "contract":"identity():305 creation_filetime=str(times[0].value); current():318-322 preserves it. Require canonical positive ASCII decimal str; preserve original identity. Rev2 int-only requirement rejected real input; not qualified."}
    for key in ("prospective_build_argv","prospective_admin_argv","prospective_run_argv"):
        plan[key]=[PLAN if v==OLD else v for v in plan[key]]
    handles=[]; begin=time.monotonic()
    try:
        q.require(all(not p.exists() for p in (q.BUILD,q.RUN,q.ADMIN,q.OWNER_BUILD.parent,q.OWNER_RUN.parent)),"08 roots absent")
        card=q.finite_load("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/NATIVE30-FIXTURE-ATTEMPT07-ADMITTED01.json")
        state,_,_=q.preflight(plan,card,handles)
        base=state["base"]; q.require(base.machine()==plan["machine_id"],"machine")
        note={"machine_id":base.machine(),"observed_at_utc":base.utc(),"status":"SOURCE_READY_CPP_UAC_NOTRUN",
            "previous_plan":rp(OLD),"changed_sources":[rp(p) for p in (plan["admin_producer"]["path"],
                "tools/g2_saved_campaign/test_native30_two_stage_20261020.py",sealer)],
            "tests":plan["source_tests"],"readonly_preflight_seconds":time.monotonic()-begin,
            "prior_seal":"exec57874d/510b96/8d65b9 preflight PASS, caps RED116469/115162/115873 before docs; dedup refs and serialize complete machine plan compactly; source/guards unchanged",
            "preflight":"5355source/995rows/12targets/219inputs+2globs/983production leases PASS; no output writes",
            "component_charges":state["budget"].last,"source_cap_bytes":114688,"future_writes":0,
            "allocated_bytes":None,"physical_credit_bytes":0}
    finally: q.close_handles(handles)
    raw=(json.dumps(plan,ensure_ascii=False,separators=(",",":"))+"\n").encode()
    note["plan"]={"path":PLAN,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
    data=encoded(note)
    gross=sum(rp(p)["bytes"] for p in plan["files"] if p not in (PLAN,NOTE))+len(raw)+len(data)
    q.require(gross<=114688,"complete source112KiB before write: "+str(gross))
    for name,value in ((PLAN,raw),(NOTE,data)):
        with (REPO/name).open("xb") as stream: stream.write(value)
    print(json.dumps({"plan":rp(PLAN),"addendum":rp(NOTE),"source_gross":gross,"future_writes":0}))
if __name__=="__main__": main()
