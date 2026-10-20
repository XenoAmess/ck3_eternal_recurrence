"""Default OFF. Root-only, separately admitted, create-only Source26 Git writer.

No checkout/index/master/push/export/runtime/Task/Game operation is provided.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import prepare_source26_sdk_v1 as s
import write_source25_canonical_ref_v1 as prior
ROOT = s.REPO / "_runtime/source26-integration17"
ANCHOR = ROOT / "SOURCE26-CANONICAL-ANCHOR.json"
REF = "refs/heads/campaign/robert-v20261019-source26-unified-cold-01"
CARD_PIN = (4327,"530bb027b1832a39a29de60ac534b23ad60039b3ff545ad6fb341f009d35360e")
WRITER25_PIN = (20388,"be6a06bf5ca649d8554f883e37fbbebaa74040547dafa11623aa3f4558a449d0")
ANCHOR_HARD = 16384


def require(ok, why):
    if not ok: raise RuntimeError("Source26 writer: " + why)


def utc(): return datetime.now(timezone.utc).isoformat()
def oid(raw): return prior.oid(raw)


def main():
    p = argparse.ArgumentParser(__doc__)
    for name in ("source-card","git-card","plan"): p.add_argument("--"+name,type=Path)
    p.add_argument("--git-card-sha256")
    p.add_argument("--execute-root-writer",action="store_true")
    a = p.parse_args()
    if not a.execute_root_writer:
        print('{"status":"DISABLED","Git_mutations":0,"runtime_calls":0}'); return
    require(all((a.source_card,a.git_card,a.plan)) and re.fullmatch("[0-9a-f]{64}",a.git_card_sha256 or ""),"Root cards/plan required")
    source_raw = s.check(a.source_card.read_bytes(),CARD_PIN,"source qualification admission")
    source_card = json.loads(source_raw)
    require(source_card["schema"] == "xar.storage.A05-Source26-finite-source-qualification/v1"
        and source_card["machine_id"] == s.MACHINE and source_card["status"] == "SOURCE_AND_SYNTHETIC_QUALIFICATION_ADMITTED"
        and source_card["lanes"]["source26_writer"]["additional_source_hard_bytes"] == 32768,"source-only card differs")
    raw = a.git_card.read_bytes(); require(len(raw)<=65536 and s.pin(raw)["sha256"] == a.git_card_sha256,"Git card pin differs")
    card = json.loads(raw)
    require(card["schema"] == "xar.storage.Source26-root-canonical-Git.v1" and card["owner"] == "Root"
        and card["machine_id"] == s.MACHINE and card["status"] == "ADMITTED"
        and card["root_direct_execution_release"] is True and card["canonical_parent"] == s.BASE,"Root Git release differs")
    require(datetime.now(timezone.utc)<min(prior.deadline(source_card),prior.deadline(card)),"admission expired")
    for key,path in (("source_admission",a.source_card),("writer",Path(__file__)),("composer",Path(s.__file__)),("source_plan",a.plan)):
        prior.checked_file_ref(card[key],path)
    require(Path(card["integration_root"]).resolve() == ROOT.resolve() and Path(card["future_anchor"]).resolve() == ANCHOR.resolve()
        and card["anchor_hard_bytes"] == ANCHOR_HARD and card["metadata_hard_bytes"]>=ANCHOR_HARD,"future anchor differs")
    require(not ANCHOR.exists() and not ANCHOR.is_symlink(),"create-only anchor exists")
    s.check(Path(prior.__file__).read_bytes(),WRITER25_PIN,"frozen shared writer helpers")
    s.check(prior.NTFS.read_bytes(),prior.NTFS_PIN,"frozen metadata helper")
    spec = importlib.util.spec_from_file_location("source26_ntfs",prior.NTFS)
    ntfs = importlib.util.module_from_spec(spec); spec.loader.exec_module(ntfs)
    ntfs.no_reparse(ROOT)
    machine = subprocess.check_output([sys.executable,"-B","-X","utf8",str(s.REPO/"tools/ck3_live_run_id.py"),"machine"]).decode().strip()
    require(machine == s.MACHINE,"actual machine differs")
    floor = card["capacity"]["Z_conservative_floor_bytes"]
    require(type(floor) is int and floor>=0 and shutil.disk_usage(s.REPO).free>=floor,"coordinated fresh free floor unavailable")
    for key in ("GIT_DIR","GIT_WORK_TREE","GIT_COMMON_DIR","GIT_OBJECT_DIRECTORY","GIT_ALTERNATE_OBJECT_DIRECTORIES","GIT_INDEX_FILE"):
        require(not os.environ.get(key),"ambient Git redirect")
    env = dict(os.environ,GIT_NO_REPLACE_OBJECTS="1",GIT_TERMINAL_PROMPT="0")
    hooks = ROOT/"disabled-hooks-must-remain-absent"; require(not hooks.exists(),"unexpected hooks")
    prefix = ["git","-C",str(s.REPO),"-c","gc.auto=0","-c","maintenance.auto=false","-c","commit.gpgsign=false",
              "-c","i18n.commitEncoding=utf-8","-c","core.hooksPath="+str(hooks)]
    def command(*args,data=None,allowed=(0,)):
        r = subprocess.run(prefix+list(args),input=data,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        require(r.returncode in allowed,"Git "+args[0]+" failed: "+r.stderr[:512].decode(errors="replace"))
        require(len(r.stdout)<=2*1024**2 and len(r.stderr)<=65536,"Git output cap")
        return r.returncode,r.stdout
    def git(*args,data=None): return command(*args,data=data)[1]
    common = Path(os.fsdecode(git("rev-parse","--git-common-dir").strip()))
    common = common.resolve() if common.is_absolute() else (s.REPO/common).resolve()
    require(common==(s.REPO/".git").resolve()==Path(card["Git"]["root"]).resolve()
        and git("rev-parse","--show-object-format").strip()==b"sha1" and ntfs.ntfs_identity(common)["cluster_bytes"]==4096,"Git/NTFS root differs")
    require(oid(git("rev-parse",s.BASE+"^{commit}"))==s.BASE and oid(git("rev-parse",s.BASE_REF))==s.BASE,"actual parent differs")
    require(command("show-ref","--verify","--quiet",REF,allowed=(0,1))[0]==1
        and command("symbolic-ref","--quiet",REF,allowed=(0,1))[0]==1,"ref exists")
    plan = json.loads(a.plan.read_bytes())
    outputs,rows,report = s.compose(plan["origin_recipe"])
    quote = s.quote(outputs,rows)["Git"]
    require(all(plan[k]==report[k] for k in ("schema","machine_id","base","output","delta","epoch_names","epoch_inputs","source_epoch_detached_model"))
        and plan["Git_object_quote"]==quote,"reviewed composition differs")
    require(card["Git"]["peak_upper_bytes"]==quote["peak_upper"] and card["Git"]["hard_bytes"]>=quote["peak_upper"]
        and card["Git"]["prior_holds_retained"] is True,"Git peak/old holds differ")
    require(len(git("var","GIT_AUTHOR_IDENT"))+len(git("var","GIT_COMMITTER_IDENT"))<4096,"commit identities too large")
    parent = json.loads(s.ANCHOR.read_bytes())
    def parent_metadata():
        pairs = [(r["git_blob_sha1"],s.common.object_upper("blob",r["bytes"])) for r in sorted(parent["nine_output_pins"],key=lambda r:r["relative"])]
        for d,size in (("ck3_autonomous_player/src/xar_autoplayer/bridge",41245),("ck3_autonomous_player/src/xar_autoplayer",12717),
                       ("ck3_autonomous_player/src",41),("ck3_autonomous_player",1122),("",1565)):
            value=oid(git("rev-parse",s.BASE+(":"+d if d else "^{tree}")))
            require(int(git("cat-file","-s",value))==size,"parent tree size drift")
            pairs.append((value,s.common.object_upper("tree",size)))
        pairs.append((s.BASE,s.common.object_upper("commit",8192)))
        actual=[]
        for value,charge in pairs:
            info=ntfs.ntfs_identity(common/"objects"/value[:2]/value[2:])
            require(not info["directory"] and 0<=info["allocation_bytes"]<=charge,"parent object identity absent")
            actual.append({"oid":value,"charge":charge,**info})
        require(len(actual)==15 and s.pin(s.canonical(actual))==parent["exact_object_metadata"]["canonical_rows"],"parent fifteen exact identities drifted")
        return s.pin(s.canonical(actual))
    parent_pin=parent_metadata(); expected={r["relative"]:r for r in rows}
    changes={(s.PREFIX+n).encode():(expected[n]["git_mode"].encode(),b"blob",expected[n]["git_blob_sha1"].encode()) for n in outputs}
    ROOT.mkdir(exist_ok=True)
    record={"schema":"xar.source26.canonical-git-anchor/v1","machine_id":machine,"start_utc":utc(),"status":"RUNNING_OR_UNKNOWN",
        "execution_owner":"Root","root_direct_execution_release":True,"parent":s.BASE,"ref":REF,
        "source_commitment":s.file_pin(a.source_card),"capacity_card":s.file_pin(a.git_card),"writer":s.file_pin(Path(__file__)),
        "composer":s.file_pin(Path(s.__file__)),"source_plan":s.file_pin(a.plan),"actual_Source25_anchor":s.file_pin(s.ANCHOR),
        "Source25_fifteen_exact_metadata":parent_pin,"Git_object_quote":{k:v for k,v in quote.items() if k!="objects"},
        "Git_export_runtime_Task_Game_Native_RPC_calls_before_writer":0,"runtime_calls":0,"SDK_export_calls":0,
        "push_calls":0,"index_or_tracked_worktree_mutations":0,"actual_H":"unknown","actual_loaded_provider":False}
    with ANCHOR.open("xb") as receipt:
        def save():
            raw=(json.dumps(record,ensure_ascii=False,indent=2)+"\n").encode(); require(len(raw)<=ANCHOR_HARD,"anchor cap")
            receipt.seek(0);receipt.truncate();receipt.write(raw);receipt.flush();os.fsync(receipt.fileno())
        save(); charged=0; metadata=[]
        def write(kind,size,*args,data=None):
            nonlocal charged
            amount=s.common.object_upper(kind,size) if kind else 0
            require(charged+amount<=quote["retained_upper"] and charged+amount+quote["largest_temporary_upper"]+65536<=card["Git"]["hard_bytes"],"Git cumulative bound")
            require(shutil.disk_usage(s.REPO).free>=floor and datetime.now(timezone.utc)<min(prior.deadline(card),prior.deadline(source_card)),"admission lost before write")
            charged+=amount; result=git(*args,data=data)
            if kind:
                value=oid(result); path=common/"objects"/value[:2]/value[2:]
                if path.exists():
                    info=ntfs.ntfs_identity(path);require(not info["directory"] and 0<=info["allocation_bytes"]<=amount and info["bytes"]<=amount,"new object allocation bound")
                    metadata.append({"oid":value,"charge":amount,**info})
                else:
                    git("cat-file","-e",value);metadata.append({"oid":value,"charge":amount,"allocation_bytes":None,"loose_file_absent":True})
            return result
        try:
            for name,body in sorted(outputs.items()): require(oid(write("blob",len(body),"hash-object","-w","--stdin",data=body))==expected[name]["git_blob_sha1"],"written blob differs")
            def tree(old,pending,directory=b""):
                entries=s.common.tree_entries(old); groups={}
                for path,value in pending.items():
                    first,sep,rest=path.partition(b"/")
                    if sep:groups.setdefault(first,{})[rest]=value
                    else:
                        require(entries.get(first,(None,b"blob"))[1]==b"blob","leaf replaces tree");entries[first]=value
                for name,child in groups.items():
                    require(name in entries and entries[name][1]==b"tree","missing ancestor")
                    entries[name]=(b"040000",b"tree",tree(entries[name][2].decode(),child,directory+(b"/" if directory else b"")+name).encode())
                size=sum(len(mode.lstrip(b"0"))+1+len(name)+1+20 for name,(mode,kind,value) in entries.items())
                require(quote["tree_payloads"][directory.decode() or "<root>"]==size,"tree payload differs")
                body=b"".join(mode+b" "+kind+b" "+value+b"\t"+name+b"\0" for name,(mode,kind,value) in sorted(entries.items()))
                return oid(write("tree",size,"mktree","-z",data=body))
            tree_oid=tree(oid(git("rev-parse",s.BASE+"^{tree}")),changes)
            s.common.verify_tree(tree_oid,rows)
            diff={x for x in git("diff-tree","--no-commit-id","--name-only","-r","-z",s.BASE,tree_oid).split(b"\0") if x}
            require(diff==set(changes),"unowned changed path")
            for name,body in outputs.items():require(s.pin(git("cat-file","blob",tree_oid+":"+s.PREFIX+name))==s.pin(body),"new body readback differs")
            env.update(GIT_AUTHOR_DATE=utc(),GIT_COMMITTER_DATE=utc())
            commit=oid(write("commit",8192,"commit-tree",tree_oid,"-p",s.BASE,data=b"Source26: unified qualified Python deltas and bounded startup origin\n"))
            body=git("cat-file","commit",commit);heads=body.split(b"\n\n",1)[0].splitlines()
            require(len(body)<=8192 and [h for h in heads if h.startswith(b"parent ")]==[b"parent "+s.BASE.encode()]
                and [h for h in heads if h.startswith(b"tree ")]==[b"tree "+tree_oid.encode()],"single parent/tree differs")
            record.update(commit=commit,tree=tree_oid,output_pins=[expected[n] for n in sorted(outputs)],
                charged_retained_objects_upper=charged,exact_object_metadata={"count":len(metadata),"canonical_rows":s.pin(s.canonical(metadata)),
                "known_loose_allocated_bytes":sum(r["allocation_bytes"] or 0 for r in metadata),"allocation_unknown_count":sum(r["allocation_bytes"] is None for r in metadata)})
            save();require(parent_metadata()==parent_pin,"parent objects changed")
            write(None,0,"update-ref","--no-deref",REF,commit,"0"*40)
            require(oid(git("rev-parse",REF))==commit and charged==quote["retained_upper"],"ref/accounting differs")
            s.common.verify_tree(commit,rows);require(parent_metadata()==parent_pin,"parent identity changed after publication")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED",end_utc=utc(),future_writes=0,
                source_file_count=len(rows),source_bytes=sum(r["bytes"] for r in rows),complete_rows_JSON=s.pin(s.canonical(rows)),
                all_Git_mode_blob_size_verified=True,changed_SHA256_bodies_read_back=len(outputs),source_epoch_detached_model=report["source_epoch_detached_model"],
                source_epoch_actual_filesystem_authority=False,old_qualifications_reused_not_rerun=True)
        except BaseException as e:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY",end_utc=utc(),future_writes=None,error={"type":type(e).__name__,"text":str(e)[:1024]});save();raise
        save()
    print(json.dumps({"status":record["status"],"commit":commit,"tree":tree_oid,"anchor":s.file_pin(ANCHOR),"runtime_calls":0}))


if __name__ == "__main__": main()
