"""Finite Source31 cached diagnostics, lean metadata and source-epoch composition; Root executes Git."""
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
PARENT = "2fd0412acf2357e8ee08ed8355e2a4a816ebfaef"
REF = "refs/heads/campaign/robert-v20261021-source31-cached-metadata-01"
PREFIX = W.PREFIX
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O = P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
PREP = O/"source31-sdk-prep01"
SOURCE30_ANCHOR:W.FileRef = {"path":str(O/"source30-sdk-prep01/source30-canonical01/SOURCE30-CANONICAL-ANCHOR.json"),
    "bytes":6671,"sha256":"71524c0b8757bcbf3d783d3a578b70649576b6b01ac603b8bf716b5529042ccf"}
SOURCE30_BASE:W.FileRef = {"path":str(O/"source30-sdk-prep01/ROOT-FINAL-SDK-SOURCE30-BASE.json"),
    "bytes":403040,"sha256":"5d159608105afa5ffe61169375158057a0fca84e707569bc08dbd0707bc8ed97"}
PARENT_QUAL:W.FileRef = {"path":str(O/"source30-sdk-prep01/SOURCE30-ACTUAL-DUAL-ORIGIN-QUALIFICATION01.json"),
    "bytes":3699,"sha256":"1f2ed2ed34ccdead14a8635b64350ce3077b9daf59a785726637916436f3bf2d"}
SDK = (
    "xar_autoplayer/bridge/native_driver.py",
    "xar_autoplayer/bridge/cached_native_clock_summary_v1.py",
    "xar_autoplayer/bridge/tactical_clock_diagnostics_v1.py",
    "xar_autoplayer/bridge/exact_clock_failure_diagnostic_v1.py",
    "xar_autoplayer/bridge/player_lifestyle_private_transport_v1.py",
    "xar_autoplayer/successor_ui_pending_ledger_v1.py",
)
PUBLIC = SDK[1:5]
EPOCH_ADDITIONS = (
    "bridge/cached_native_clock_summary_v1.py",
    "bridge/player_lifestyle_private_transport_v1.py",
)
POST_PINS:dict[str,W.Pin] = {
    "xar_autoplayer/bridge/native_driver.py": {
        "bytes":1648212,
        "sha256":"aa7ac3a8e696ae2e4b2c61775b943624a23be4fed15196a8f23bb8e70aed57f8",
    },
    "xar_autoplayer/bridge/cached_native_clock_summary_v1.py": {
        "bytes":13844,
        "sha256":"48dcdd3c13f396ab5b822826cc25f5113431b8240d8826b9776c9b5ed1e39802",
    },
    "xar_autoplayer/bridge/tactical_clock_diagnostics_v1.py": {
        "bytes":18793,
        "sha256":"6b0b46f07cebb762d761e8c9cf4acca891eed3307f79467fcd29204c2d2b0adf",
    },
    "xar_autoplayer/bridge/exact_clock_failure_diagnostic_v1.py": {
        "bytes":7892,
        "sha256":"0f8223d3ebba839f1ff209c5edd1b82dc6728f887d2adec0b3ddffc81028edce",
    },
    "xar_autoplayer/bridge/player_lifestyle_private_transport_v1.py": {
        "bytes":44468,
        "sha256":"2e2aa097f1da716fbdaf05c2d16f4482e57608d9ca5ea85dd589c318f1daa6a6",
    },
    "xar_autoplayer/successor_ui_pending_ledger_v1.py": {
        "bytes":22869,
        "sha256":"a448b2d0d2c8ef65ed90aa6059f852e848819dfcdc8c55dbbd5ad7bc0abc1311",
    },
}
PUBLIC_PINS:dict[str,W.Pin] = {name:POST_PINS[name] for name in PUBLIC}
class PublicInput(TypedDict):
    relative: str
    pin: W.Pin
class Plan(TypedDict):
    schema: Literal["xar.source31.canonical-plan/v1"]
    machine_id: str
    observed_at_utc: str
    review_at_utc: str
    parent: str
    ref: str
    target_tree: str
    public_source_commit: str
    public_inputs: list[PublicInput]
    source30_anchor: W.FileRef
    source30_BASE: W.FileRef
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
    W.require(len(result)==4 and {v["relative"] for v in result}==set(PUBLIC)
        and all(v["pin"]==PUBLIC_PINS[v["relative"]] for v in result),"four exact frozen public inputs")
    return result

def parse_plan(value: object) -> Plan:
    d=W.keys(value,"schema machine_id observed_at_utc review_at_utc parent ref target_tree public_source_commit public_inputs source30_anchor source30_BASE qualifications source_file_count source_bytes complete_rows_JSON Git_object_quote")
    W.require(d["schema"]=="xar.source31.canonical-plan/v1","Source31 plan schema")
    q=W.keys(d["Git_object_quote"],"retained_upper largest_temporary_upper peak_upper object_count")
    return {"schema":"xar.source31.canonical-plan/v1","machine_id":W.string(d["machine_id"]),
        "observed_at_utc":W.string(d["observed_at_utc"]),"review_at_utc":W.string(d["review_at_utc"]),
        "parent":W.hexstr(d["parent"],40),"ref":W.string(d["ref"]),"target_tree":W.hexstr(d["target_tree"],40),
        "public_source_commit":W.hexstr(d["public_source_commit"],40),"public_inputs":parse_inputs(d["public_inputs"]),
        "source30_anchor":W.parse_ref(d["source30_anchor"]),"source30_BASE":W.parse_ref(d["source30_BASE"]),
        "qualifications":[W.parse_ref(v) for v in W.sequence(d["qualifications"])],
        "source_file_count":W.integer(d["source_file_count"]),"source_bytes":W.integer(d["source_bytes"]),
        "complete_rows_JSON":W.parse_pin(d["complete_rows_JSON"]),
        "Git_object_quote":{"retained_upper":W.integer(q["retained_upper"]),
            "largest_temporary_upper":W.integer(q["largest_temporary_upper"]),
            "peak_upper":W.integer(q["peak_upper"]),"object_count":W.integer(q["object_count"])}}

def sdk_names(plan: Plan) -> tuple[str,...]:
    W.require(plan["parent"]==PARENT,"Source31 parent")
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

_CACHE_METHODS = ("_execute_battle_sentinel_advance","_advance_exact_day_with_sentinel")
_CACHE_EDITS:tuple[tuple[str,str,str],...] = (
("_execute_battle_sentinel_advance","                clock_diagnostics.finish(self, current)",'                clock_diagnostics.finish(self, current)\n                clock_diagnostics.capture_cached("wait_final", self.state)'),
("_execute_battle_sentinel_advance","                finally:\n                    for action in boundary_pause_actions:",'                finally:\n                    clock_diagnostics.capture_cached("pause_final", self.state)\n                    for action in boundary_pause_actions:'),
("_execute_battle_sentinel_advance",'                cleanup_error = f"{type(cleanup).__name__}: {cleanup}"\n            result = _battle_sentinel_step_result(','                cleanup_error = f"{type(cleanup).__name__}: {cleanup}"\n            clock_diagnostics.capture_cached("cleanup_final", self.state)\n            result = _battle_sentinel_step_result('),
("_execute_battle_sentinel_advance","            if boundary_pause_diagnostics is not None:",'            cached_summary = clock_diagnostics.cached_summary()\n            if cached_summary is not None:\n                result["cached_native_clock_summary_v1"] = cached_summary\n            if boundary_pause_diagnostics is not None:'),
("_advance_exact_day_with_sentinel","        diagnostic_action_start = len(actions)","        diagnostic_action_start = len(actions)\n        cached_clock = None"),
("_advance_exact_day_with_sentinel","            from .clock_observation_timing_v1 import (","            try:\n                from .cached_native_clock_summary_v1 import CachedNativeClockCollectorV1\n                cached_clock = CachedNativeClockCollectorV1.from_snapshot(current)\n            except Exception:\n                pass\n            from .clock_observation_timing_v1 import ("),
("_advance_exact_day_with_sentinel","                finish_clock_observation_v1(self, clock_observation, current)",'                finish_clock_observation_v1(self, clock_observation, current)\n                if cached_clock is not None:\n                    cached_clock.capture_current("wait_final", self.state)'),
("_advance_exact_day_with_sentinel","                self._pause_life_advance(\n                    cleanup_frame, actions\n                )",'                try:\n                    self._pause_life_advance(\n                        cleanup_frame, actions\n                    )\n                finally:\n                    if cached_clock is not None:\n                        cached_clock.capture_current("pause_final", self.state)'),
("_advance_exact_day_with_sentinel","            if war_daily_watch is not None:\n                raise StepPostconditionError(",'            if cached_clock is not None:\n                cached_clock.capture_current("cleanup_final", self.state)\n            if war_daily_watch is not None:\n                raise StepPostconditionError('),
("_advance_exact_day_with_sentinel","                        wait_progress=wait_progress_summary,\n                    )",'                        wait_progress=wait_progress_summary,\n                    )\n                    if cached_clock is not None:\n                        diagnostic["cached_native_clock_summary_v1"] = cached_clock.summary()'),
)

def rewrite_cached_driver_v1(raw: bytes,*,inverse: bool) -> bytes:
    original={name:function_span(raw,name) for name in _CACHE_METHODS}
    changed=dict(original)
    edits=tuple(reversed(_CACHE_EDITS)) if inverse else _CACHE_EDITS
    for name,before,after in edits:
        old,new=(after,before) if inverse else (before,after)
        changed[name]=replace_once(changed[name],old.encode(),new.encode())
    result=raw
    for name in _CACHE_METHODS:result=replace_once(result,original[name],changed[name])
    return result

def build_sources(plan: Plan,git: W.Git) -> dict[str,bytes]:
    """RAM-only composition; public Driver is never copied."""
    parse_inputs(plan["public_inputs"])
    W.require(git.get("rev-parse",plan["public_source_commit"]+"^{commit}").strip().decode()
        ==plan["public_source_commit"],"actual public input commit")
    result:dict[str,bytes]={}
    for name in PUBLIC:
        body=git.get("cat-file","blob",plan["public_source_commit"]+":"+PREFIX+name)
        W.require(W.pin(body)==PUBLIC_PINS[name],"committed sidecar input pin")
        result[PREFIX+name]=body
    old=git.get("cat-file","blob",PARENT+":"+PREFIX+SDK[0])
    W.require(W.pin(old)=={"bytes":1646969,"sha256":"9fa96d271e416b5b63ac22956c9f43db1acb7f483e9f97ad2b803693e63695d2"},"sealed Driver preimage")
    native=rewrite_cached_driver_v1(old,inverse=False)
    W.require(rewrite_cached_driver_v1(native,inverse=True)==old and len(native)-len(old)==1243,
        "cached Driver exact inverse and extent")
    for method in _CACHE_METHODS:
        body=function_span(native,method)
        call=b"clock_diagnostics.capture_cached" if method==_CACHE_METHODS[0] else b"cached_clock.capture_current"
        for phase in ("wait_final","pause_final","cleanup_final"):
            W.require(body.count(call+('("'+phase+'", self.state)').encode())==1,"six exact cache capture points")
    result[PREFIX+SDK[0]]=native
    name=SDK[-1]
    old=git.get("cat-file","blob",PARENT+":"+PREFIX+name)
    ending=b'             "bridge/war_contract.py")'
    suffix=b'             "bridge/war_contract.py",\n'+('             "'+EPOCH_ADDITIONS[0]+'",\n             "'+EPOCH_ADDITIONS[1]+'")').encode()
    epoch=replace_once(old,ending,suffix)
    W.require(len(epoch_names(old))==39 and epoch_names(epoch)==(*epoch_names(old),*EPOCH_ADDITIONS)
        and len(set(epoch_names(epoch)))==41,"ordered source epoch 39 to 41")
    result[PREFIX+name]=epoch
    for name,body in result.items():
        W.require(W.pin(body)==POST_PINS[name[len(PREFIX):]],"frozen Source31 output")
        compile(body,name,"exec",dont_inherit=True)
    return result

def _compose(plan: Plan,git: W.Git,verify: bool) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    W.require(plan["schema"]=="xar.source31.canonical-plan/v1" and plan["machine_id"]==MACHINE
        and plan["parent"]==PARENT and plan["ref"]==REF,"Source31 plan identity")
    W.require(W.date(plan["observed_at_utc"])<=W.utc()<W.date(plan["review_at_utc"]),"plan time")
    W.require(plan["source30_anchor"]==SOURCE30_ANCHOR and plan["source30_BASE"]==SOURCE30_BASE,"fixed actual parent refs")
    anchor=W.obj(W.load(W.checked(plan["source30_anchor"])))
    base=W.obj(W.load(W.checked(plan["source30_BASE"])))
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
    W.require(len(rows)==1465 and actual=={n:(r["git_mode"],r["git_blob_sha1"],r["bytes"]) for n,r in rows.items()},
        "complete Source30 canonical inventory")
    out=build_sources(plan,git)
    W.require(SDK[1] not in rows,"cached helper must be a new leaf")
    for name,body in out.items():
        relative=name[len(PREFIX):]
        rows[relative]={"relative":relative,**W.pin(body),"git_blob_sha1":W.oid("blob",body),"git_mode":"100644"}
    W.require(all("xar_autoplayer/"+name in rows
        for name in epoch_names(out[PREFIX+SDK[-1]])),"epoch dependency closure")
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
        W.require(len(rows)==plan["source_file_count"]==1466 and set(out)=={PREFIX+n for n in sdk_names(plan)}
            and plan["source_bytes"]==sum(r["bytes"] for r in ordered)
            and plan["complete_rows_JSON"]==W.pin(W.canonical(ordered))
            and plan["target_tree"]==ids[""] and plan["Git_object_quote"]==quote,"Source31 rows/tree/quote")
    return out,ordered,trees,quote

def compose(plan: Plan,git: W.Git,repo: Path) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    return _compose(plan,git,True)

def prepare_plan_v1(*,public_source_commit: str,qualifications: list[W.FileRef],
        observed_at_utc: str,review_at_utc: str) -> Plan:
    """Read-only proposal. Execution requires separate evidence and a Root card."""
    plan:Plan={"schema":"xar.source31.canonical-plan/v1","machine_id":MACHINE,
        "observed_at_utc":observed_at_utc,"review_at_utc":review_at_utc,"parent":PARENT,"ref":REF,
        "target_tree":"0"*40,"public_source_commit":W.hexstr(public_source_commit,40),
        "public_inputs":[{"relative":n,"pin":PUBLIC_PINS[n]} for n in PUBLIC],
        "source30_anchor":SOURCE30_ANCHOR,"source30_BASE":SOURCE30_BASE,"qualifications":qualifications,
        "source_file_count":1466,"source_bytes":0,"complete_rows_JSON":{"bytes":0,"sha256":"0"*64},
        "Git_object_quote":{"retained_upper":0,"largest_temporary_upper":0,"peak_upper":0,"object_count":0}}
    git=W.Git(OWN.parents[2],PREP/"source31-canonical01")
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
    base=W.obj(W.load(W.checked(plan["source30_BASE"])))
    before={W.string(W.obj(v)["relative"]):W.parse_pin(
        {k:W.obj(v)[k] for k in ("bytes","sha256")}) for v in W.sequence(base["files"])}
    return [{"relative":PREFIX+name,"before_pin":before.get(name),"output_pin":POST_PINS[name],
        "public_input":{"relative":name,"pin":PUBLIC_PINS[name]} if name in PUBLIC else None,
        "public_source_commit":plan["public_source_commit"]} for name in SDK]

def validate_qualifications_v1(plan: Plan) -> None:
    W.require(len(plan["qualifications"])==2 and PARENT_QUAL in plan["qualifications"],"parent and one Source31 qualification")
    W.checked(PARENT_QUAL)
    matches=0
    for item in plan["qualifications"]:
        if item==PARENT_QUAL:continue
        d=W.obj(W.load(W.checked(item)))
        W.require(d["schema"]=="xar.source31.composition-qualification/v1"
            and d["status"]=="OFFLINE_QUALIFIED_NOT_RUNTIME" and d["machine_id"]==MACHINE
            and W.date(d["observed_at_utc"])<=W.utc()
            and W.hexstr(d["public_source_commit"],40)==plan["public_source_commit"]
            and parse_inputs(d["public_inputs"])==plan["public_inputs"]
            and W.parse_ref(d["source30_anchor"])==SOURCE30_ANCHOR
            and W.parse_ref(d["source30_BASE"])==SOURCE30_BASE
            and W.parse_ref(d["parent_package_qualification"])==PARENT_QUAL
            and W.parse_pin(d["complete_rows_JSON"])==plan["complete_rows_JSON"]
            and W.hexstr(d["target_tree"],40)==plan["target_tree"]
            and W.integer(d["source_file_count"])==1466 and W.integer(d["epoch_count"])==41
            and W.integer(d["runtime_calls"])==W.integer(d["new_campaign_credit"])==0
            and d["RAM_composition_and_inverse_guards_passed"] is True
            and d["strict_and_strict_equality_passed"] is True,"Source31 qualification binding")
        pins:dict[str,W.Pin]={}
        for value in W.sequence(d["output_pins"]):
            row=W.keys(value,"relative bytes sha256")
            name=W.string(row["relative"])
            W.require(name not in pins,"duplicate qualification output")
            pins[name]=W.parse_pin({k:row[k] for k in ("bytes","sha256")})
        W.require(pins==POST_PINS,"six exact qualified outputs")
        matches+=1
    W.require(matches==1,"one Source31 composition qualification")
def execute_v1(*, plan_ref: W.FileRef, card_ref: W.FileRef) -> W.FileRef:
    """Single create-only Root execution. Failure consumes its anchor."""
    plan=parse_plan(W.load(W.checked(plan_ref)))
    card=W.obj(W.load(W.checked(card_ref)))
    W.require(card["schema"]=="xar.storage.Source31-root-canonical-Git.v1"
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
    W.require(anchor==metadata/"SOURCE31-CANONICAL-ANCHOR.json"
        and metadata==(PREP/"source31-canonical01").resolve()
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
    record:dict[str,object]={"schema":"xar.source31.canonical-git-anchor/v1","machine_id":MACHINE,
        "status":"RUNNING_OR_UNKNOWN","start_utc":W.utc().isoformat(),"execution_owner":"Root",
        "root_direct_execution_release":True,"parent":PARENT,"ref":REF,"writer":W.file_ref(OWN),
        "source_plan":plan_ref,"capacity_card":card_ref,"source_admission":source_ref,
        "actual_Source30_anchor":plan["source30_anchor"],"actual_Source30_BASE":plan["source30_BASE"],
        "Git_object_quote":quote,"runtime_calls":0,"SDK_export_calls":0,"push_calls":0,
        "index_or_tracked_worktree_mutations":0,"actual_loaded_provider":False,
        "canonical_patch_rows":canonical_patch_rows_v1(plan),"qualifications":plan["qualifications"],
        "public_source_commit":plan["public_source_commit"],"public_inputs":plan["public_inputs"],
        "source_epoch_count":41}
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
                data=b"Source31: bounded cached clock diagnostics and lean lifestyle metadata\n").strip().decode()
            commit_body=git.get("cat-file","commit",commit)
            header=commit_body.split(b"\n\n",1)[0].splitlines()
            W.require(len(commit_body)<=8192 and [v for v in header if v.startswith(b"parent ")]==[b"parent "+PARENT.encode()]
                and [v for v in header if v.startswith(b"tree ")]==[b"tree "+tree.encode()],"commit ancestry")
            record.update(commit=commit,tree=tree,output_pins=[r for r in rows if PREFIX+r["relative"] in out],
                source_file_count=len(rows),source_bytes=sum(r["bytes"] for r in rows),
                complete_rows_JSON=W.pin(W.canonical(rows)),charged_retained_objects_upper=charged)
            save()
            W.require(charged==quote["retained_upper"],"retained accounting")
            W.checked(plan["source30_anchor"]);guard()
            git.get("update-ref","--no-deref",REF,commit,"0"*40)
            W.require(git.get("rev-parse",REF).strip().decode()==commit,"ref readback")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED",end_utc=W.utc().isoformat(),future_writes=0)
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY",end_utc=W.utc().isoformat(),
                error={"type":type(error).__name__,"text":str(error)[:1024]})
            save();raise
        save()
    return W.file_ref(anchor)


