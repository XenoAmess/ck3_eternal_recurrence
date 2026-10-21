"""Finite Source30 ACK, marriage and source-epoch composition; Root executes Git."""
from __future__ import annotations
import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Literal, TypedDict
sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
sys.path.insert(0, str(OWN.parent))
import write_source27_canonical_ref_v1 as W
W.require(W.pin(W.read(Path(W.__file__).resolve(),32768)) ==
    {"bytes":24449,"sha256":"82833c6426defef8e405332f2ed513d8fe9665599019db3ae14305c874382f5c"},
    "reviewed Git primitive source changed")
MACHINE = W.MACHINE
PARENT = "d02d9907fa7a26ab60a6a75456fa276be78387c4"
PUBLIC_COMMIT = "9592cefdda846fc0242430d8fef1fef1f58c81a0"
REF = "refs/heads/campaign/robert-v20261021-source30-ack-marriage-01"
PREFIX = W.PREFIX
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O = P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
PREP = O/"source30-sdk-prep01"
SOURCE29_ANCHOR:W.FileRef = {"path":str(O/"source29-sdk-prep01/source29-canonical01/SOURCE29-CANONICAL-ANCHOR.json"),
    "bytes":8573,"sha256":"a815fd758008dabe940821595f67d66ce4f516161c7695556520272617709634"}
SOURCE29_BASE:W.FileRef = {"path":str(O/"source29-sdk-prep01/ROOT-FINAL-SDK-SOURCE29-BASE.json"),
    "bytes":401661,"sha256":"5fac2fc9180653d2b130765cc9648c79afa3f647d34646e7ea46a1b96d837d8d"}
PARENT_QUAL:W.FileRef = {"path":str(O/"source29-sdk-prep01/SOURCE29-ACTUAL-PACKAGE-QUALIFICATION01.json"),
    "bytes":7643,"sha256":"0a15e0f63a943e85ba7cb02e206cc5e75bbc50b49e4ccffd40c87d49f261b937"}
SDK = ("xar_autoplayer/bridge/native_driver.py","xar_autoplayer/family_marriage_formal_consumer.py",
    "xar_autoplayer/bridge/timeline_control_ack_v1.py","xar_autoplayer/successor_ui_pending_ledger_v1.py")
PUBLIC = SDK[:3]
EPOCH_ADDITIONS = ("bridge/timeline_control_ack_v1.py","family_marriage_formal_consumer.py","bridge/war_contract.py")
PUBLIC_PINS:dict[str,W.Pin] = {
    PUBLIC[0]:{"bytes":1656364,"sha256":"d55617497d60decc945e8475c8e87295b55253d9897bef4f750d0f205f298e17"},
    PUBLIC[1]:{"bytes":61603,"sha256":"c6d55a12b4450909641dbffe5b12e900878f29cde406aadd4a6d185bd78039b0"},
    PUBLIC[2]:{"bytes":2078,"sha256":"c57978c77bdb71af2fcd7294f1b3c7e552fb63117327aa5db502115b6336d940"}}
POST_PINS:dict[str,W.Pin] = {
    SDK[0]:{"bytes":1646969,"sha256":"9fa96d271e416b5b63ac22956c9f43db1acb7f483e9f97ad2b803693e63695d2"},
    SDK[1]:PUBLIC_PINS[PUBLIC[1]],SDK[2]:PUBLIC_PINS[PUBLIC[2]],
    SDK[3]:{"bytes":22748,"sha256":"419f99062ce9a960e86efeb0254abb65564ef7d08390ef620f050bd607b70b26"}}
class PublicInput(TypedDict):
    relative: str
    pin: W.Pin
class Plan(TypedDict):
    schema: Literal["xar.source30.canonical-plan/v1"]
    machine_id: str
    observed_at_utc: str
    review_at_utc: str
    parent: str
    ref: str
    target_tree: str
    public_source_commit: str
    public_inputs: list[PublicInput]
    source29_anchor: W.FileRef
    source29_BASE: W.FileRef
    qualifications: list[W.FileRef]
    source_file_count: int
    source_bytes: int
    complete_rows_JSON: W.Pin
    Git_object_quote: W.Quote

def parse_inputs(value: object) -> list[PublicInput]:
    result:list[PublicInput]=[]
    for value_item in W.sequence(value):
        d=W.keys(value_item,"relative pin")
        name=W.string(d["relative"])
        W.require(name in PUBLIC,"finite public input")
        result.append({"relative":name,"pin":W.parse_pin(d["pin"])})
    W.require(len(result)==3 and {v["relative"] for v in result}==set(PUBLIC)
        and all(v["pin"]==PUBLIC_PINS[v["relative"]] for v in result),"three exact frozen public inputs")
    return result

def parse_plan(value: object) -> Plan:
    d=W.keys(value,"schema machine_id observed_at_utc review_at_utc parent ref target_tree public_source_commit public_inputs source29_anchor source29_BASE qualifications source_file_count source_bytes complete_rows_JSON Git_object_quote")
    W.require(d["schema"]=="xar.source30.canonical-plan/v1","Source30 plan schema")
    q=W.keys(d["Git_object_quote"],"retained_upper largest_temporary_upper peak_upper object_count")
    return {"schema":"xar.source30.canonical-plan/v1","machine_id":W.string(d["machine_id"]),
        "observed_at_utc":W.string(d["observed_at_utc"]),"review_at_utc":W.string(d["review_at_utc"]),
        "parent":W.hexstr(d["parent"],40),"ref":W.string(d["ref"]),"target_tree":W.hexstr(d["target_tree"],40),
        "public_source_commit":W.hexstr(d["public_source_commit"],40),"public_inputs":parse_inputs(d["public_inputs"]),
        "source29_anchor":W.parse_ref(d["source29_anchor"]),"source29_BASE":W.parse_ref(d["source29_BASE"]),
        "qualifications":[W.parse_ref(v) for v in W.sequence(d["qualifications"])],
        "source_file_count":W.integer(d["source_file_count"]),"source_bytes":W.integer(d["source_bytes"]),
        "complete_rows_JSON":W.parse_pin(d["complete_rows_JSON"]),
        "Git_object_quote":{"retained_upper":W.integer(q["retained_upper"]),
            "largest_temporary_upper":W.integer(q["largest_temporary_upper"]),
            "peak_upper":W.integer(q["peak_upper"]),"object_count":W.integer(q["object_count"])}}

def sdk_names(plan: Plan) -> tuple[str,...]:
    W.require(plan["parent"]==PARENT,"Source30 parent")
    return SDK

def function_span(body: bytes,name: str) -> bytes:
    nodes=[n for n in ast.walk(ast.parse(body)) if isinstance(n,ast.FunctionDef) and n.name==name]
    W.require(len(nodes)==1 and nodes[0].end_lineno is not None,"one exact function")
    return b"".join(body.splitlines(keepends=True)[nodes[0].lineno-1:nodes[0].end_lineno])

def replace_once(body: bytes,before: bytes,after: bytes) -> bytes:
    W.require(body.count(before)==1,"unique exact byte seam")
    return body.replace(before,after,1)

def epoch_names(body: bytes) -> tuple[str,...]:
    function=[n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef) and n.name=="owner_source_epoch_v1"]
    W.require(len(function)==1,"one source epoch")
    assignments=[n for n in function[0].body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=="names" for t in n.targets)]
    W.require(len(assignments)==1,"one epoch names tuple")
    value:object=ast.literal_eval(assignments[0].value)
    if not isinstance(value,tuple) or not all(type(n) is str for n in value):
        raise ValueError("epoch tuple must contain strings")
    result:list[str]=[]
    for item in value:
        if not isinstance(item,str):raise ValueError("epoch name string")
        result.append(item)
    return tuple(result)

def build_sources(plan: Plan,git: W.Git) -> dict[str,bytes]:
    """Pure RAM: Git reads only; no working-tree public file is an authority."""
    parse_inputs(plan["public_inputs"])
    public={name:git.get("cat-file","blob",plan["public_source_commit"]+":"+PREFIX+name) for name in PUBLIC}
    W.require(all(W.pin(public[n])==PUBLIC_PINS[n] for n in PUBLIC),"committed public source inputs")
    old={name:git.get("cat-file","blob",PARENT+":"+PREFIX+name) for name in SDK if name!=SDK[2]}
    first=b'        timeline_control_ack = None\n        if step in {"pause-map", "resume-map"}:\n            from .timeline_control_ack_v1 import normalize_timeline_control_ack_v1\n            try:\n                timeline_control_ack = normalize_timeline_control_ack_v1(\n                    frame, expected_step=step, expected_request_id=request_id)\n            except ValueError as error:\n                raise BridgeUnavailableError(str(error)) from error\n'
    second=b'            if timeline_control_ack is not None:\n                projected.update(timeline_control_ack)\n'
    a=function_span(old[SDK[0]],"_execute_primitive_step")
    b=function_span(public[SDK[0]],"_execute_primitive_step")
    W.require(b.count(first)==b.count(second)==1 and b.replace(first,b"").replace(second,b"")==a,
        "ACK only two exact insertions in complete primitive function")
    native=replace_once(old[SDK[0]],a,b)
    a=function_span(old[SDK[1]],"_plan_existing_resolution")
    b=function_span(public[SDK[1]],"_plan_existing_resolution")
    helper=function_span(public[SDK[1]],"_without_action_bound_war_presentation")
    W.require(b.replace(b"_without_action_bound_war_presentation(plan)",b"plan")==a
        and b"def _without_action_bound_war_presentation(" not in old[SDK[1]],"marriage exact action-bound projection")
    family=replace_once(old[SDK[1]],a,helper+b"\n\n"+b)
    W.require(family==public[SDK[1]],"no additional family source differences")
    ending=b'             "bridge/driver.py")'
    suffix=b'             "bridge/driver.py",\n'+b"".join(('             "'+v+'",\n').encode() for v in EPOCH_ADDITIONS[:-1])+('             "'+EPOCH_ADDITIONS[-1]+'")').encode()
    epoch=replace_once(old[SDK[3]],ending,suffix)
    W.require(len(epoch_names(old[SDK[3]]))==36 and epoch_names(epoch)==(*epoch_names(old[SDK[3]]),*EPOCH_ADDITIONS)
        and len(set(epoch_names(epoch)))==39,"ordered source epoch 36 to 39")
    result={PREFIX+SDK[0]:native,PREFIX+SDK[1]:family,PREFIX+SDK[2]:public[SDK[2]],PREFIX+SDK[3]:epoch}
    for name,body in result.items():
        W.require(W.pin(body)==POST_PINS[name[len(PREFIX):]],"frozen Source30 output")
        compile(body,name,"exec",dont_inherit=True)
    return result

def _compose(plan: Plan,git: W.Git,verify: bool) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    W.require(plan["schema"]=="xar.source30.canonical-plan/v1" and plan["machine_id"]==MACHINE
        and plan["parent"]==PARENT and plan["ref"]==REF
        and plan["public_source_commit"]==PUBLIC_COMMIT,"Source30 plan identity")
    W.require(W.date(plan["observed_at_utc"])<=W.utc()<W.date(plan["review_at_utc"]),"plan time")
    W.require(plan["source29_anchor"]==SOURCE29_ANCHOR and plan["source29_BASE"]==SOURCE29_BASE,"fixed actual parent refs")
    anchor=W.obj(W.load(W.checked(plan["source29_anchor"])))
    base=W.obj(W.load(W.checked(plan["source29_BASE"])))
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
        "complete Source29 canonical inventory")
    out=build_sources(plan,git)
    W.require(SDK[2] not in rows,"ACK helper must be a new leaf")
    for name,body in out.items():
        relative=name[len(PREFIX):]
        rows[relative]={"relative":relative,**W.pin(body),"git_blob_sha1":W.oid("blob",body),"git_mode":"100644"}
    W.require(all("xar_autoplayer/"+name in rows
        for name in epoch_names(out[PREFIX+SDK[3]])),"epoch dependency closure")
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
        W.require(len(rows)==plan["source_file_count"]==1465 and set(out)=={PREFIX+n for n in sdk_names(plan)}
            and plan["source_bytes"]==sum(r["bytes"] for r in ordered)
            and plan["complete_rows_JSON"]==W.pin(W.canonical(ordered))
            and plan["target_tree"]==ids[""] and plan["Git_object_quote"]==quote,"Source30 rows/tree/quote")
    return out,ordered,trees,quote

def compose(plan: Plan,git: W.Git,repo: Path) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    return _compose(plan,git,True)

def prepare_plan_v1(*,public_source_commit: str,qualifications: list[W.FileRef],
        observed_at_utc: str,review_at_utc: str) -> Plan:
    """Read-only proposal. Execution requires separate evidence and a Root card."""
    plan:Plan={"schema":"xar.source30.canonical-plan/v1","machine_id":MACHINE,
        "observed_at_utc":observed_at_utc,"review_at_utc":review_at_utc,"parent":PARENT,"ref":REF,
        "target_tree":"0"*40,"public_source_commit":W.hexstr(public_source_commit,40),
        "public_inputs":[{"relative":n,"pin":PUBLIC_PINS[n]} for n in PUBLIC],
        "source29_anchor":SOURCE29_ANCHOR,"source29_BASE":SOURCE29_BASE,"qualifications":qualifications,
        "source_file_count":1465,"source_bytes":0,"complete_rows_JSON":{"bytes":0,"sha256":"0"*64},
        "Git_object_quote":{"retained_upper":0,"largest_temporary_upper":0,"peak_upper":0,"object_count":0}}
    git=W.Git(OWN.parents[2],PREP/"source30-canonical01")
    _,rows,trees,quote=_compose(plan,git,False)
    plan["source_bytes"]=sum(r["bytes"] for r in rows)
    plan["complete_rows_JSON"]=W.pin(W.canonical(rows))
    plan["target_tree"]=trees[-1][2]
    plan["Git_object_quote"]=quote
    _compose(plan,git,True)
    return plan

class CanonicalPatchRow(TypedDict):
    relative: str
    before_pin: W.Pin | None
    output_pin: W.Pin
    public_input: PublicInput | None
    public_source_commit: str

def canonical_patch_rows_v1(plan: Plan) -> list[CanonicalPatchRow]:
    base=W.obj(W.load(W.checked(plan["source29_BASE"])))
    before={W.string(W.obj(v)["relative"]):W.parse_pin(
        {k:W.obj(v)[k] for k in ("bytes","sha256")}) for v in W.sequence(base["files"])}
    return [{"relative":PREFIX+name,"before_pin":before.get(name),"output_pin":POST_PINS[name],
        "public_input":{"relative":name,"pin":PUBLIC_PINS[name]} if name in PUBLIC else None,
        "public_source_commit":plan["public_source_commit"]} for name in SDK]

def validate_qualifications_v1(plan: Plan) -> None:
    W.require(len(plan["qualifications"])==2 and PARENT_QUAL in plan["qualifications"],"parent and one Source30 qualification")
    W.checked(PARENT_QUAL)
    matches=0
    for item in plan["qualifications"]:
        if item==PARENT_QUAL:continue
        d=W.obj(W.load(W.checked(item)))
        W.require(d["schema"]=="xar.source30.composition-qualification/v1"
            and d["status"]=="OFFLINE_QUALIFIED_NOT_RUNTIME" and d["machine_id"]==MACHINE
            and W.date(d["observed_at_utc"])<=W.utc()
            and W.hexstr(d["public_source_commit"],40)==plan["public_source_commit"]
            and parse_inputs(d["public_inputs"])==plan["public_inputs"]
            and W.parse_ref(d["source29_anchor"])==SOURCE29_ANCHOR
            and W.parse_ref(d["source29_BASE"])==SOURCE29_BASE
            and W.parse_ref(d["parent_package_qualification"])==PARENT_QUAL
            and W.parse_pin(d["complete_rows_JSON"])==plan["complete_rows_JSON"]
            and W.hexstr(d["target_tree"],40)==plan["target_tree"]
            and W.integer(d["source_file_count"])==1465 and W.integer(d["epoch_count"])==39
            and W.integer(d["runtime_calls"])==W.integer(d["new_campaign_credit"])==0
            and d["RAM_composition_and_inverse_guards_passed"] is True
            and d["strict_and_strict_equality_passed"] is True,"Source30 qualification binding")
        pins:dict[str,W.Pin]={}
        for value in W.sequence(d["output_pins"]):
            row=W.keys(value,"relative bytes sha256")
            name=W.string(row["relative"])
            W.require(name not in pins,"duplicate qualification output")
            pins[name]=W.parse_pin({k:row[k] for k in ("bytes","sha256")})
        W.require(pins==POST_PINS,"four exact qualified outputs")
        matches+=1
    W.require(matches==1,"one Source30 composition qualification")
def execute_v1(*, plan_ref: W.FileRef, card_ref: W.FileRef) -> W.FileRef:
    """Single create-only Root execution. Failure consumes its anchor."""
    plan=parse_plan(W.load(W.checked(plan_ref)))
    card=W.obj(W.load(W.checked(card_ref)))
    W.require(card["schema"]=="xar.storage.Source30-root-canonical-Git.v1"
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
    W.require(anchor==metadata/"SOURCE30-CANONICAL-ANCHOR.json"
        and metadata==(PREP/"source30-canonical01").resolve()
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
    record:dict[str,object]={"schema":"xar.source30.canonical-git-anchor/v1","machine_id":MACHINE,
        "status":"RUNNING_OR_UNKNOWN","start_utc":W.utc().isoformat(),"execution_owner":"Root",
        "root_direct_execution_release":True,"parent":PARENT,"ref":REF,"writer":W.file_ref(OWN),
        "source_plan":plan_ref,"capacity_card":card_ref,"source_admission":source_ref,
        "actual_Source29_anchor":plan["source29_anchor"],"actual_Source29_BASE":plan["source29_BASE"],
        "Git_object_quote":quote,"runtime_calls":0,"SDK_export_calls":0,"push_calls":0,
        "index_or_tracked_worktree_mutations":0,"actual_loaded_provider":False,
        "canonical_patch_rows":canonical_patch_rows_v1(plan),"qualifications":plan["qualifications"],
        "public_source_commit":plan["public_source_commit"],"public_inputs":plan["public_inputs"],
        "source_epoch_count":39}
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
                data=b"Source30: typed timeline ACK and marriage display source epoch\n").strip().decode()
            commit_body=git.get("cat-file","commit",commit)
            header=commit_body.split(b"\n\n",1)[0].splitlines()
            W.require(len(commit_body)<=8192 and [v for v in header if v.startswith(b"parent ")]==[b"parent "+PARENT.encode()]
                and [v for v in header if v.startswith(b"tree ")]==[b"tree "+tree.encode()],"commit ancestry")
            record.update(commit=commit,tree=tree,output_pins=[r for r in rows if PREFIX+r["relative"] in out],
                source_file_count=len(rows),source_bytes=sum(r["bytes"] for r in rows),
                complete_rows_JSON=W.pin(W.canonical(rows)),charged_retained_objects_upper=charged)
            save()
            W.require(charged==quote["retained_upper"],"retained accounting")
            W.checked(plan["source29_anchor"]);guard()
            git.get("update-ref","--no-deref",REF,commit,"0"*40)
            W.require(git.get("rev-parse",REF).strip().decode()==commit,"ref readback")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED",end_utc=W.utc().isoformat(),future_writes=0)
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY",end_utc=W.utc().isoformat(),
                error={"type":type(error).__name__,"text":str(error)[:1024]})
            save();raise
        save()
    return W.file_ref(anchor)

