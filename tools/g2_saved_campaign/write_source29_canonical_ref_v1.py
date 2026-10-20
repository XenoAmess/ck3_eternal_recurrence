"""Finite Source29 three-leaf canonical composition. Root alone executes Git."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Literal, TypedDict
sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
sys.path.insert(0,str(OWN.parent))
import write_source28_canonical_ref_v1 as PREVIOUS
import write_source27_canonical_ref_v1 as W
W.require(W.pin(W.read(Path(PREVIOUS.__file__).resolve(),32768)) ==
    {"bytes":23916,"sha256":"e5c806eee85e7e414fd7d49dccdd762f69f8b8b6024aae3acb1ebc027b6ce385"},
    "reviewed Source28 Git primitives changed")
W.require(W.pin(W.read(Path(W.__file__).resolve(),32768)) ==
    {"bytes":24449,"sha256":"82833c6426defef8e405332f2ed513d8fe9665599019db3ae14305c874382f5c"},
    "reviewed Git primitive source changed")
MACHINE = W.MACHINE
PARENT = "442beeae4676bad9a9d53cb7070a01f06e965761"
REF = "refs/heads/campaign/robert-v20261021-source29-war-readonly-01"
PREFIX = W.PREFIX
PERFORMANCE: Literal["xar_autoplayer/bridge/service.py"] = "xar_autoplayer/bridge/service.py"
SDKRelative = Literal["xar_autoplayer/bridge/native_driver.py",
    "xar_autoplayer/bridge/war_contract.py","xar_autoplayer/strategy.py","xar_autoplayer/bridge/service.py"]
SDK:tuple[SDKRelative,...] = ("xar_autoplayer/bridge/native_driver.py",
    "xar_autoplayer/bridge/war_contract.py","xar_autoplayer/strategy.py")
NAMES = tuple(PREFIX+n for n in SDK)
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O = P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
PREP = O/"source29-sdk-prep01"
SOURCE28_ANCHOR:W.FileRef = {"path":str(O/"source28-a12-prep01/source28-canonical01/SOURCE28-CANONICAL-ANCHOR.json"),
    "bytes":17555,"sha256":"3f0f25f46e6e0e9a260c9fa24b3c9ae2f9b7febeaf1c7d91c58b7c39f9b16dac"}
SOURCE28_BASE:W.FileRef = {"path":str(O/"source28-a12-prep01/ROOT-FINAL-SDK-SOURCE28-BASE.json"),
    "bytes":411438,"sha256":"0d903bb46616b91e4947ee838c64662ddcf3be14c89999bd1a5272f01c48f585"}
class Candidate(TypedDict):
    relative: SDKRelative
    before_pin: W.FileRef
    after_pin: W.FileRef
class PerformanceCandidate(TypedDict):
    manifest_ref: W.FileRef
    producer_ref: W.FileRef
    qualification_ref: W.FileRef

class Plan(TypedDict):
    schema: Literal["xar.source29.canonical-plan/v1"]
    machine_id: str
    observed_at_utc: str
    review_at_utc: str
    parent: str
    ref: str
    target_tree: str
    candidate_manifest: W.FileRef
    candidate_producer: W.FileRef
    source28_anchor: W.FileRef
    source28_BASE: W.FileRef
    qualifications: list[W.FileRef]
    performance_candidate: PerformanceCandidate | None
    source_file_count: int
    source_bytes: int
    complete_rows_JSON: W.Pin
    Git_object_quote: W.Quote

def parse_plan(value: object) -> Plan:
    d=W.keys(value,"schema machine_id observed_at_utc review_at_utc parent ref target_tree candidate_manifest candidate_producer source28_anchor source28_BASE qualifications performance_candidate source_file_count source_bytes complete_rows_JSON Git_object_quote")
    W.require(d["schema"]=="xar.source29.canonical-plan/v1","Source29 plan schema")
    q=W.keys(d["Git_object_quote"],"retained_upper largest_temporary_upper peak_upper object_count")
    performance=parse_performance(d["performance_candidate"])
    return {"schema":"xar.source29.canonical-plan/v1","machine_id":W.string(d["machine_id"]),
        "observed_at_utc":W.string(d["observed_at_utc"]),"review_at_utc":W.string(d["review_at_utc"]),
        "parent":W.hexstr(d["parent"],40),"ref":W.string(d["ref"]),"target_tree":W.hexstr(d["target_tree"],40),
        "candidate_manifest":W.parse_ref(d["candidate_manifest"]),"candidate_producer":W.parse_ref(d["candidate_producer"]),
        "source28_anchor":W.parse_ref(d["source28_anchor"]),"source28_BASE":W.parse_ref(d["source28_BASE"]),
        "qualifications":[W.parse_ref(v) for v in W.sequence(d["qualifications"])],
        "performance_candidate":performance,
        "source_file_count":W.integer(d["source_file_count"]),"source_bytes":W.integer(d["source_bytes"]),
        "complete_rows_JSON":W.parse_pin(d["complete_rows_JSON"]),
        "Git_object_quote":{"retained_upper":W.integer(q["retained_upper"]),
            "largest_temporary_upper":W.integer(q["largest_temporary_upper"]),
            "peak_upper":W.integer(q["peak_upper"]),"object_count":W.integer(q["object_count"])}}

def parse_performance(value: object) -> PerformanceCandidate | None:
    if value is None:return None
    d=W.keys(value,"manifest_ref producer_ref qualification_ref")
    return {"manifest_ref":W.parse_ref(d["manifest_ref"]),"producer_ref":W.parse_ref(d["producer_ref"]),
        "qualification_ref":W.parse_ref(d["qualification_ref"])}

def sdk_names(plan: Plan) -> tuple[str,...]:
    return (*SDK,PERFORMANCE) if plan["performance_candidate"] is not None else SDK

def relative(value: object) -> SDKRelative:
    for name in (*SDK,PERFORMANCE):
        if type(value) is str and value==name:return name
    raise ValueError("Source29 SDK path outside exact three")

def candidates(plan: Plan) -> list[Candidate]:
    d=W.obj(W.load(W.checked(plan["candidate_manifest"],1048576)))
    W.require(d["schema"]=="xar.Source28-war-only-candidate/v1" and d["status"]=="CANDIDATE_NOT_DEPLOYED"
        and d["machine_id"]==MACHINE and d["parent_commit"]==PARENT
        and W.parse_ref(d["source28_anchor"])==plan["source28_anchor"]
        and W.parse_ref(d["source28_BASE"])==plan["source28_BASE"]
        and W.parse_ref(d["producer_ref"])==plan["candidate_producer"],"candidate source lineage")
    W.require(W.date(d["observed_at_utc"])<=W.utc(),"candidate observation in future")
    W.checked(plan["candidate_producer"])
    result:list[Candidate]=[]
    for item in W.sequence(d["files"]):
        v=W.keys(item,"relative before_pin after_pin")
        result.append({"relative":relative(v["relative"]),
            "before_pin":W.parse_ref(v["before_pin"]),"after_pin":W.parse_ref(v["after_pin"])})
    W.require(len(result)==3 and {r["relative"] for r in result}==set(SDK),"three exact candidate leaves")
    performance=plan["performance_candidate"]
    if performance is not None:
        p=W.obj(W.load(W.checked(performance["manifest_ref"])))
        W.require(p["schema"]=="xar.Source28-lifestyle-snapshot-lean-candidate/v1"
            and p["status"]=="CANDIDATE_NOT_DEPLOYED" and p["machine_id"]==MACHINE
            and p["parent_commit"]==PARENT
            and W.parse_ref(p["source28_anchor"])==plan["source28_anchor"]
            and W.parse_ref(p["source28_BASE"])==plan["source28_BASE"]
            and W.parse_ref(p["producer_ref"])==performance["producer_ref"]
            and W.parse_ref(p["qualification_ref"])==performance["qualification_ref"]
            and performance["qualification_ref"] in plan["qualifications"]
            and W.date(p["observed_at_utc"])<=W.utc(),"performance candidate lineage")
        for ref in (performance["producer_ref"],performance["qualification_ref"],W.parse_ref(p["test_ref"])):
            W.checked(ref)
        values=W.sequence(p["files"])
        W.require(len(values)==1,"one performance SDK leaf")
        v=W.keys(values[0],"relative before_pin after_pin")
        name=relative(v["relative"])
        W.require(name==PERFORMANCE,"only metadata snapshot service")
        q=W.obj(W.load(W.checked(performance["qualification_ref"])))
        W.require(q["schema"]=="xar.Source28-lifestyle-snapshot-lean-qualification/v1"
            and q["status"]=="PASS" and q["machine_id"]==MACHINE
            and W.parse_ref(q["source28_anchor"])==plan["source28_anchor"]
            and W.parse_ref(q["source28_BASE"])==plan["source28_BASE"]
            and W.parse_ref(q["producer_ref"])==performance["producer_ref"]
            and W.parse_ref(q["test_ref"])==W.parse_ref(p["test_ref"])
            and W.parse_ref(q["before_pin"])==W.parse_ref(v["before_pin"])
            and W.parse_ref(q["after_pin"])==W.parse_ref(v["after_pin"])
            and W.integer(q["runtime_cases_passed"])==12
            and W.integer(q["new_campaign_credit"])==W.integer(q["runtime_calls"])==0
            and all(q[key] is True for key in ("frame_guards_preserved","json_roundtrip_equal",
                "native_query_count_unchanged","query_and_snapshot_exception_paths_preserved"))
            and q["actual_game_performance_measured"] is False,"qualified metadata-only performance candidate")
        result.append({"relative":name,"before_pin":W.parse_ref(v["before_pin"]),
            "after_pin":W.parse_ref(v["after_pin"])})
    return result


def _compose(plan: Plan,git: W.Git,verify: bool) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    W.require(plan["schema"]=="xar.source29.canonical-plan/v1" and plan["machine_id"]==MACHINE
        and plan["parent"]==PARENT and plan["ref"]==REF,"Source29 plan identity")
    W.require(W.date(plan["observed_at_utc"])<=W.utc()<W.date(plan["review_at_utc"]),"plan time")
    W.require(plan["source28_anchor"]==SOURCE28_ANCHOR and plan["source28_BASE"]==SOURCE28_BASE,"fixed actual Source28 refs")
    anchor=W.obj(W.load(W.checked(plan["source28_anchor"])))
    base=W.obj(W.load(W.checked(plan["source28_BASE"])))
    W.require(anchor["commit"]==base["business_source_commit"]==PARENT
        and anchor["status"]=="CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and base["machine_id"]==MACHINE and base["runtime_admitted"] is False
        and "canonical_preload_policy" not in base,"actual immutable parent")
    rows:dict[str,W.Row]={}
    for value in W.sequence(base["files"]):
        r=W.keys(value,"relative bytes sha256 git_blob_sha1 git_mode")
        row:W.Row={"relative":W.string(r["relative"]),"bytes":W.integer(r["bytes"]),
            "sha256":W.hexstr(r["sha256"],64),"git_blob_sha1":W.hexstr(r["git_blob_sha1"],40),"git_mode":W.string(r["git_mode"])}
        W.require(row["relative"] not in rows,"duplicate parent row")
        rows[row["relative"]]=row
    actual:dict[str,tuple[str,str,int]]={}
    for item in git.get("ls-tree","-r","-l","-z",PARENT,"--",PREFIX).split(b"\0"):
        if item:
            h,pathbytes=item.split(b"\t",1);mode,kind,value,size=h.split()
            W.require(kind==b"blob","ordinary SDK Git blobs required")
            actual[pathbytes.decode()[len(PREFIX):]]=(mode.decode(),value.decode(),int(size))
    W.require(len(rows)==1464 and actual=={n:(r["git_mode"],r["git_blob_sha1"],r["bytes"]) for n,r in rows.items()},
        "complete Source28 canonical inventory")
    out:dict[str,bytes]={}
    parent_root=Path(W.string(base["source_root"])).resolve()
    for candidate in candidates(plan):
        sdk_name=candidate["relative"];before=candidate["before_pin"]
        expected=rows[sdk_name]
        W.require(Path(before["path"]).resolve()==parent_root/sdk_name
            and before["bytes"]==expected["bytes"] and before["sha256"]==expected["sha256"],"candidate parent leaf pin")
        old=git.get("cat-file","blob",PARENT+":"+PREFIX+sdk_name)
        W.require(W.pin(old)=={"bytes":before["bytes"],"sha256":before["sha256"]},"Git preimage differs")
        body=W.checked(candidate["after_pin"],4194304)
        W.require(body!=old,"candidate is unchanged")
        compile(body,PREFIX+sdk_name,"exec",dont_inherit=True)
        out[PREFIX+sdk_name]=body
        rows[sdk_name]={"relative":sdk_name,**W.pin(body),"git_blob_sha1":W.oid("blob",body),"git_mode":"100644"}
    for qualification in plan["qualifications"]:W.checked(qualification)
    ordered=[rows[name] for name in sorted(rows)]
    dirs={""}
    for name in out:
        d=name.rpartition("/")[0]
        while d:dirs.add(d);d=d.rpartition("/")[0]
    ids={name:W.oid("blob",body) for name,body in out.items()}
    trees:list[W.Tree]=[]
    amounts=[W.upper("blob",len(body)) for body in out.values()]
    for d in sorted(dirs,key=lambda s:(s.count("/")+bool(s),s),reverse=True):
        e=W.entries(git.get("ls-tree","-z",PARENT+(":"+d if d else "^{tree}")))
        for name in out:
            parent,_,leaf=name.rpartition("/")
            if parent==d:e[leaf.encode()]=(b"100644",b"blob",ids[name])
        for child in dirs:
            if child and child.rpartition("/")[0]==d:
                e[child.rpartition("/")[2].encode()]=(b"040000",b"tree",ids[child])
        body=W.tree_body(e);ids[d]=W.oid("tree",body);trees.append((d,body,ids[d]))
        amounts.append(W.upper("tree",len(body)))
    amounts.append(W.upper("commit",8192))
    quote:W.Quote={"retained_upper":sum(amounts),"largest_temporary_upper":max(amounts),
        "peak_upper":sum(amounts)+max(amounts)+65536,"object_count":len(amounts)}
    if verify:
        W.require(len(rows)==plan["source_file_count"]==1464 and set(out)=={PREFIX+n for n in sdk_names(plan)}
            and plan["source_bytes"]==sum(r["bytes"] for r in ordered)
            and plan["complete_rows_JSON"]==W.pin(W.canonical(ordered))
            and plan["target_tree"]==ids[""] and plan["Git_object_quote"]==quote,"Source29 rows/tree/quote")
    return out,ordered,trees,quote

def compose(plan: Plan,git: W.Git,repo: Path) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    return _compose(plan,git,True)

def prepare_plan_v1(*,candidate_manifest: W.FileRef,candidate_producer: W.FileRef,
        qualifications: list[W.FileRef],performance_candidate: PerformanceCandidate | None,
        observed_at_utc: str,review_at_utc: str) -> Plan:
    """Read only; its returned proposal gives no Git or export permission."""
    performance_candidate=parse_performance(performance_candidate)
    plan:Plan={"schema":"xar.source29.canonical-plan/v1","machine_id":MACHINE,
        "observed_at_utc":observed_at_utc,"review_at_utc":review_at_utc,"parent":PARENT,"ref":REF,
        "target_tree":"0"*40,"candidate_manifest":candidate_manifest,"candidate_producer":candidate_producer,
        "source28_anchor":SOURCE28_ANCHOR,"source28_BASE":SOURCE28_BASE,"qualifications":qualifications,
        "performance_candidate":performance_candidate,
        "source_file_count":1464,"source_bytes":0,"complete_rows_JSON":{"bytes":0,"sha256":"0"*64},
        "Git_object_quote":{"retained_upper":0,"largest_temporary_upper":0,"peak_upper":0,"object_count":0}}
    git=W.Git(OWN.parents[2],PREP/"source29-canonical01")
    _,rows,trees,quote=_compose(plan,git,False)
    plan["source_bytes"]=sum(r["bytes"] for r in rows)
    plan["complete_rows_JSON"]=W.pin(W.canonical(rows))
    plan["target_tree"]=trees[-1][2]
    plan["Git_object_quote"]=quote
    _compose(plan,git,True)
    return plan

class CanonicalPatchRow(TypedDict):
    relative: str
    before_pin: W.Pin
    output_pin: W.Pin
    input_ref: W.FileRef

def canonical_patch_rows_v1(plan: Plan) -> list[CanonicalPatchRow]:
    return [{"relative":PREFIX+row["relative"],
        "before_pin":{"bytes":row["before_pin"]["bytes"],"sha256":row["before_pin"]["sha256"]},
        "output_pin":{"bytes":row["after_pin"]["bytes"],"sha256":row["after_pin"]["sha256"]},
        "input_ref":row["after_pin"]} for row in candidates(plan)]


def validate_qualifications_v1(plan: Plan) -> None:
    matches=0
    performance=plan["performance_candidate"]
    for item in plan["qualifications"]:
        d=W.obj(W.load(W.checked(item)))
        if d.get("schema")=="xar.Source28-war-only-candidate-qualification/v1":
            W.require(d["status"]=="OFFLINE_QUALIFIED_NOT_DEPLOYED" and d["machine_id"]==MACHINE
                and W.parse_ref(d["candidate_manifest"])==plan["candidate_manifest"]
                and W.parse_ref(d["producer_ref"])==plan["candidate_producer"],
                "war qualification must bind this candidate")
            W.require(performance is None or item!=performance["qualification_ref"],"distinct performance qualification")
            matches+=1
    W.require(matches==1,"one actual war candidate qualification required")
    if performance is not None:
        W.require(performance["qualification_ref"] in plan["qualifications"]
            and len(plan["qualifications"])>=2,"separate performance and war qualifications")

def execute_v1(*, plan_ref: W.FileRef, card_ref: W.FileRef) -> W.FileRef:
    """Single create-only Root execution. Failure consumes its anchor."""
    plan=parse_plan(W.load(W.checked(plan_ref)))
    card=W.obj(W.load(W.checked(card_ref)))
    W.require(card["schema"]=="xar.storage.Source29-root-canonical-Git.v1"
        and card["owner"]=="Root" and card["machine_id"]==MACHINE
        and card["status"]=="ADMITTED" and card["root_direct_execution_release"] is True,"Root release required")
    W.require(0<=(W.utc()-W.date(card["observed_at_utc"])).total_seconds()<=600,"fresh release")
    limit=min(W.date(card["review_at_utc"]),W.date(plan["review_at_utc"]))
    W.require(W.utc()<limit and W.parse_ref(card["writer"])==W.file_ref(OWN)
        and W.parse_ref(card["plan"])==plan_ref,"writer/plan admission")
    source_ref=W.parse_ref(card["source_admission"])
    source=W.obj(W.load(W.checked(source_ref)))
    W.require(source["machine_id"]==MACHINE,"same-machine source admission")
    repo=OWN.parents[2]
    W.require(subprocess.check_output([sys.executable,"-B",str(repo/"tools/ck3_live_run_id.py"),"machine"]).decode().strip()==MACHINE,"actual machine")
    metadata=Path(W.string(card["metadata_root"])).resolve()
    anchor=Path(W.string(card["future_anchor"])).resolve()
    W.require(anchor==metadata/"SOURCE29-CANONICAL-ANCHOR.json"
        and W.integer(card["anchor_hard_bytes"])==65536,"anchor scope")
    W.no_reparse(metadata)
    W.require(not anchor.exists() and not anchor.is_symlink(),"anchor consumed")
    capacity,budget=W.obj(card["capacity"]),W.obj(card["Git"])
    zfloor,dfloor=W.integer(capacity["Z_free_floor_bytes"]),W.integer(capacity["D_free_floor_bytes"])
    def guard() -> None:
        W.require(W.utc()<limit and shutil.disk_usage(repo).free>=zfloor
            and shutil.disk_usage(metadata.parent).free>=dfloor,"capacity/time lost")
    guard()
    git=W.Git(repo,metadata)
    common_raw=Path(os.fsdecode(git.get("rev-parse","--git-common-dir").strip()))
    common=(common_raw if common_raw.is_absolute() else repo/common_raw).resolve()
    W.no_reparse(common/"objects")
    W.require(common==(repo/".git").resolve()==Path(W.string(budget["root"])).resolve()
        and not (common/"objects/info/alternates").exists()
        and git.get("rev-parse","--show-object-format").strip()==b"sha1","Git object store")
    W.require(git.get("rev-parse",PARENT+"^{commit}").strip().decode()==PARENT,"actual parent")
    W.require(git.run("show-ref","--verify","--quiet",REF,allowed=(0,1))[0]==1
        and git.run("symbolic-ref","--quiet",REF,allowed=(0,1))[0]==1,"ref consumed")
    validate_qualifications_v1(plan)
    out,rows,trees,quote=compose(plan,git,repo)
    hard=W.integer(budget["hard_bytes"])
    W.require(W.integer(budget["peak_upper_bytes"])==quote["peak_upper"]<=hard
        and budget["prior_holds_retained"] is True,"Git budget")
    W.require(len(git.get("var","GIT_AUTHOR_IDENT"))+len(git.get("var","GIT_COMMITTER_IDENT"))<4096,"identity cap")
    metadata.mkdir(exist_ok=True)
    record:dict[str,object]={"schema":"xar.source29.canonical-git-anchor/v1","machine_id":MACHINE,
        "status":"RUNNING_OR_UNKNOWN","start_utc":W.utc().isoformat(),"execution_owner":"Root",
        "root_direct_execution_release":True,"parent":PARENT,"ref":REF,"writer":W.file_ref(OWN),
        "source_plan":plan_ref,"capacity_card":card_ref,"source_admission":source_ref,
        "actual_Source28_anchor":plan["source28_anchor"],"actual_Source28_BASE":plan["source28_BASE"],
        "Git_object_quote":quote,"runtime_calls":0,"SDK_export_calls":0,"push_calls":0,
        "index_or_tracked_worktree_mutations":0,"actual_loaded_provider":False,
        "canonical_patch_rows":canonical_patch_rows_v1(plan),"candidate_manifest":plan["candidate_manifest"],
        "candidate_producer":plan["candidate_producer"],"qualifications":plan["qualifications"],
        "performance_candidate":plan["performance_candidate"],
        "canonical_variant":"WAR_ONLY" if plan["performance_candidate"] is None else "WAR_AND_METADATA_SNAPSHOT"}
    charged=0
    with anchor.open("xb") as receipt:
        def save() -> None:
            body=W.canonical(record)+b"\n"
            W.require(len(body)<=65536,"anchor cap")
            receipt.seek(0);receipt.truncate();receipt.write(body);receipt.flush();os.fsync(receipt.fileno())
        def write(kind:str,size:int,*argv:str,data:bytes|None=None) -> bytes:
            nonlocal charged
            charge=W.upper(kind,size)
            W.require(charged+charge<=quote["retained_upper"]
                and charged+charge+quote["largest_temporary_upper"]+65536<=hard,"cumulative Git bound")
            guard();charged+=charge
            result:object=git.get(*argv,data=data)
            if not isinstance(result,bytes):raise TypeError("Git response must be bytes")
            return result
        save()
        try:
            for name,body in sorted(out.items()):
                W.require(write("blob",len(body),"hash-object","-w","--stdin",data=body).strip().decode()==W.oid("blob",body),"blob readback")
            for _,body,expected in trees:
                e=W.entries_tree(body)
                data=b"".join(m+b" "+k+b" "+h.encode()+b"\t"+n+b"\0" for n,(m,k,h) in sorted(e.items()))
                W.require(write("tree",len(body),"mktree","-z",data=data).strip().decode()==expected,"tree readback")
            tree=plan["target_tree"]
            diff={v.decode() for v in git.get("diff-tree","--no-commit-id","--name-only","-r","-z",PARENT,tree).split(b"\0") if v}
            W.require(diff=={PREFIX+n for n in sdk_names(plan)},"unowned path")
            for n,b in out.items(): W.require(git.get("cat-file","blob",tree+":"+n)==b,"exact content readback")
            commit=write("commit",8192,"commit-tree",tree,"-p",PARENT,
                data=b"Source29: bounded optional readonly war-query degradation\n").strip().decode()
            commit_body=git.get("cat-file","commit",commit)
            header=commit_body.split(b"\n\n",1)[0].splitlines()
            W.require(len(commit_body)<=8192 and [v for v in header if v.startswith(b"parent ")]==[b"parent "+PARENT.encode()]
                and [v for v in header if v.startswith(b"tree ")]==[b"tree "+tree.encode()],"commit ancestry")
            record.update(commit=commit,tree=tree,output_pins=[r for r in rows if PREFIX+r["relative"] in out],
                source_file_count=len(rows),source_bytes=sum(r["bytes"] for r in rows),
                complete_rows_JSON=W.pin(W.canonical(rows)),charged_retained_objects_upper=charged)
            save()
            W.require(charged==quote["retained_upper"],"retained accounting")
            W.checked(plan["source28_anchor"]);guard()
            git.get("update-ref","--no-deref",REF,commit,"0"*40)
            W.require(git.get("rev-parse",REF).strip().decode()==commit,"ref readback")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED",end_utc=W.utc().isoformat(),future_writes=0)
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY",end_utc=W.utc().isoformat(),
                error={"type":type(error).__name__,"text":str(error)[:1024]})
            save();raise
        save()
    return W.file_ref(anchor)
