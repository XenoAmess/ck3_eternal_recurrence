"""Finite Source32 route clock and wartime sway composition; Root alone mutates Git."""
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
PARENT = "12e81b52c736baec02a85f32098bae5bdaa66a31"
SOURCE_FILE_COUNT, EPOCH_COUNT, M6_CASE_COUNT, SOURCE_BYTES = 1468, 43, 8, 59336648
REF = "refs/heads/campaign/robert-v20261021-source32-route-window-clock-01"
PREFIX = W.PREFIX
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O = P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
PREP = O/"source32-sdk-prep01"
SOURCE31_ANCHOR:W.FileRef = {"path":str(O/"source31-sdk-prep01/source31-canonical01/SOURCE31-CANONICAL-ANCHOR.json"),
    "bytes":8409,"sha256":"1a93eaa6468518b8ba80fe3848b233291159b9b2bb449754ab4934602c09afc9"}
SOURCE31_BASE:W.FileRef = {"path":str(O/"source31-sdk-prep01/ROOT-FINAL-SDK-SOURCE31-BASE.json"),
    "bytes":406541,"sha256":"0bdcfc8eb9262daf4bd5f677bdca9445b40a7e7d668f13976f02b36633a54c4a"}
PARENT_QUAL:W.FileRef = {"path":str(O/"source31-sdk-prep01/SOURCE31-ACTUAL-DUAL-ORIGIN-QUALIFICATION01.json"),
    "bytes":4207,"sha256":"ae5976ef5ae24a0f2705eb8a7be7259cc314af3df563c1c53abf083e319c5ca3"}
SDK = ("xar_autoplayer/bridge/native_driver.py","xar_autoplayer/bridge/mcp_server.py",
    "xar_autoplayer/bridge/route_window_clock_v1.py","xar_autoplayer/successor_ui_pending_ledger_v1.py",
    "xar_autoplayer/ordinary_sway_schedule_v1.py","xar_autoplayer/bridge/ordinary_sway_service_v1.py",
    "xar_autoplayer/sway_formal_consumer.py","xar_autoplayer/bridge/war_stationary_sway_opportunity_v1.py")
NEW_LEAVES = (SDK[2],SDK[7])
PUBLIC = ("tools/g2_saved_campaign/prepare_route_window_clock_v1.py",
    "tools/g2_saved_campaign/test_prepare_route_window_clock_v1.py",
    "tools/g2_saved_campaign/prepare_wartime_sway_opportunity_v1.py",
    "tools/g2_saved_campaign/test_prepare_wartime_sway_opportunity_v1.py")
POST_PINS:dict[str,W.Pin] = {
 SDK[0]:{"bytes":1648649,"sha256":"15a1eca3cee4f79be51a4144258650822e49146c93b7a87257319f848928d06b"},
 SDK[1]:{"bytes":265427,"sha256":"3dec1f1f8d78bf1ed546fac429bf8f0e4f025448accbb4608094211a56f45632"},
 SDK[2]:{"bytes":2572,"sha256":"74d9b2faca2b7f78024366480ba45627eae73c3f5ca23514988d97fa1e3d9871"},
 SDK[3]:{"bytes":22978,"sha256":"03097a0aa73286682345f0d08f0623ba5a8fa5e999969e6e8e2e92c24f19ea98"},
 SDK[4]:{"bytes":10519,"sha256":"935cc226b486adc074242e963994503916ee28afbd8d6711bbffaf7a99338831"},
 SDK[5]:{"bytes":11559,"sha256":"7c1634beb6feb37b74ccab0a029f4eb38ec279c44bad58f3f7fde2884cb7584b"},
 SDK[6]:{"bytes":35522,"sha256":"85eb2fb33177630c2711bad20ca08c7c2d7dc8ede2f62a4181c10c7fbdbcdf0e"},
 SDK[7]:{"bytes":12348,"sha256":"56afdd886252c3f8130ae194e0cd3b1a27f9e1726394443145eaf06f05af8873"}}
PUBLIC_PINS:dict[str,W.Pin] = {
 PUBLIC[0]:{"bytes":25508,"sha256":"84a989f57b99296b6a78fb323311c87d05f378efa76263515276e5c751c84f6a"},
 PUBLIC[1]:{"bytes":11937,"sha256":"4344174ff46f4ed2033dd6a2205875af1a42b589c0c9a1af81167e59ecedaba5"},
 PUBLIC[2]:{"bytes":23966,"sha256":"cf038efbd4609df36478627880c04ffd605635dbbf5f20a5d57e8b66e65e8797"},
 PUBLIC[3]:{"bytes":22719,"sha256":"9432d12e9f3c692aaeadd8e307829fe9e5c8b3229830e882d89bc7d0df10f625"}}
QUALIFICATION_PIN:W.Pin = {"bytes":10772,"sha256":"a01d39208ac95408a490289e8a2c02ef42d44687e5f2f1d1359fb6b7e4f9e185"}
for name in PUBLIC:
    W.require(W.pin(W.read(OWN.parents[2]/name,32768))==PUBLIC_PINS[name],"frozen clock tool changed")
import prepare_route_window_clock_v1 as CLOCK
class PublicInput(TypedDict):
    relative: str
    pin: W.Pin
class Plan(TypedDict):
    schema: Literal["xar.source32.canonical-plan/v1"]
    machine_id: str
    observed_at_utc: str
    review_at_utc: str
    parent: str
    ref: str
    target_tree: str
    public_source_commit: str
    public_inputs: list[PublicInput]
    source31_anchor: W.FileRef
    source31_BASE: W.FileRef
    qualifications: list[W.FileRef]
    source_file_count: int
    source_bytes: int
    complete_rows_JSON: W.Pin
    Git_object_quote: W.Quote

def safe_integer(value: object) -> int:
    result:int=W.integer(value)
    W.require(result<=9007199254740991,"JSON safe integer required")
    return result

def safe_pin(value: object) -> W.Pin:
    result:W.Pin=W.parse_pin(value)
    safe_integer(result["bytes"])
    return result

def safe_ref(value: object) -> W.FileRef:
    result:W.FileRef=W.parse_ref(value)
    safe_integer(result["bytes"])
    return result

def parse_inputs(value: object) -> list[PublicInput]:
    result:list[PublicInput]=[]
    for value_item in W.sequence(value):
        d=W.keys(value_item,"relative pin")
        name=W.string(d["relative"])
        W.require(name in PUBLIC,"finite public input")
        result.append({"relative":name,"pin":safe_pin(d["pin"])})
    W.require(len(result)==4 and {v["relative"] for v in result}==set(PUBLIC)
        and all(v["pin"]==PUBLIC_PINS[v["relative"]] for v in result),"four exact frozen public tools")
    return result

def parse_plan(value: object) -> Plan:
    d=W.keys(value,"schema machine_id observed_at_utc review_at_utc parent ref target_tree public_source_commit public_inputs source31_anchor source31_BASE qualifications source_file_count source_bytes complete_rows_JSON Git_object_quote")
    W.require(d["schema"]=="xar.source32.canonical-plan/v1","Source32 plan schema")
    q=W.keys(d["Git_object_quote"],"retained_upper largest_temporary_upper peak_upper object_count")
    return {"schema":"xar.source32.canonical-plan/v1","machine_id":W.string(d["machine_id"]),
        "observed_at_utc":W.string(d["observed_at_utc"]),"review_at_utc":W.string(d["review_at_utc"]),
        "parent":W.hexstr(d["parent"],40),"ref":W.string(d["ref"]),"target_tree":W.hexstr(d["target_tree"],40),
        "public_source_commit":W.hexstr(d["public_source_commit"],40),"public_inputs":parse_inputs(d["public_inputs"]),
        "source31_anchor":safe_ref(d["source31_anchor"]),"source31_BASE":safe_ref(d["source31_BASE"]),
        "qualifications":[safe_ref(v) for v in W.sequence(d["qualifications"])],
        "source_file_count":safe_integer(d["source_file_count"]),"source_bytes":safe_integer(d["source_bytes"]),
        "complete_rows_JSON":safe_pin(d["complete_rows_JSON"]),
        "Git_object_quote":{"retained_upper":safe_integer(q["retained_upper"]),
            "largest_temporary_upper":safe_integer(q["largest_temporary_upper"]),
            "peak_upper":safe_integer(q["peak_upper"]),"object_count":safe_integer(q["object_count"])}}

def sdk_names(plan: Plan) -> tuple[str,...]:
    W.require(plan["parent"]==PARENT,"Source32 parent")
    return SDK



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
    """Compose sealed Source31 bytes; public runtime modules are never inputs."""
    parse_inputs(plan["public_inputs"])
    W.require(git.get("rev-parse",plan["public_source_commit"]+"^{commit}").strip().decode()
        ==plan["public_source_commit"],"actual public tool commit")
    for name in PUBLIC:
        body=git.get("cat-file","blob",plan["public_source_commit"]+":"+name)
        W.require(W.pin(body)==PUBLIC_PINS[name],"committed compositor/test pin")
    native=git.get("cat-file","blob",PARENT+":"+PREFIX+SDK[0])
    mcp=git.get("cat-file","blob",PARENT+":"+PREFIX+SDK[1])
    delta=CLOCK.compose_route_window_clock_v1(native,mcp)
    quote=CLOCK.route_window_clock_quote_v1(delta)
    W.require(quote["source31_commit"]==PARENT and quote["qualification"]==
        {"relative_path":"qualification/test_route_window_clock_candidate_v1.py",**QUALIFICATION_PIN}
        and quote["runtime_mutated"] is False and quote["game_executed"] is False
        and quote["live_high_speed_qualified"] is False,"finite offline clock delta")
    out={PREFIX+row.relative_path:row.payload for row in delta.sources if row.role=="production"}
    W.require(set(out)=={PREFIX+n for n in SDK[:3]},"exact three production payloads")
    old=git.get("cat-file","blob",PARENT+":"+PREFIX+SDK[3])
    W.require(W.pin(old)=={"bytes":22869,"sha256":"a448b2d0d2c8ef65ed90aa6059f852e848819dfcdc8c55dbbd5ad7bc0abc1311"},"sealed epoch preimage")
    ending=b'             "bridge/player_lifestyle_private_transport_v1.py")'
    suffix=b'             "bridge/player_lifestyle_private_transport_v1.py",\n             "bridge/route_window_clock_v1.py",\n             "bridge/war_stationary_sway_opportunity_v1.py")'
    epoch=replace_once(old,ending,suffix)
    W.require(len(epoch_names(old))==41 and epoch_names(epoch)==(*epoch_names(old),"bridge/route_window_clock_v1.py","bridge/war_stationary_sway_opportunity_v1.py")
        and len(set(epoch_names(epoch)))==EPOCH_COUNT,"ordered source epoch 41 to 43")
    out[PREFIX+SDK[3]]=epoch
    import prepare_wartime_sway_opportunity_v1 as M6
    inputs={name:git.get("cat-file","blob",PARENT+":"+PREFIX+name) for name in SDK[4:7]}
    sway=M6.compose_wartime_sway_opportunity_v1(inputs)
    W.require(set(sway)==set(SDK[4:]),"finite four M6 production leaves")
    out.update({PREFIX+name:body for name,body in sway.items()})
    for name,body in out.items():
        W.require(W.pin(body)==POST_PINS[name[len(PREFIX):]],"exact Source32 payload")
        compile(body,name,"exec",dont_inherit=True)
    return out

def _compose(plan: Plan,git: W.Git,verify: bool) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    W.require(plan["schema"]=="xar.source32.canonical-plan/v1" and plan["machine_id"]==MACHINE
        and plan["parent"]==PARENT and plan["ref"]==REF,"Source32 plan identity")
    W.require(W.date(plan["observed_at_utc"])<=W.utc()<W.date(plan["review_at_utc"]),"plan time")
    W.require(plan["source31_anchor"]==SOURCE31_ANCHOR and plan["source31_BASE"]==SOURCE31_BASE,"fixed actual parent refs")
    anchor=W.obj(W.load(W.checked(plan["source31_anchor"])))
    base=W.obj(W.load(W.checked(plan["source31_BASE"])))
    W.require(anchor["commit"]==base["business_source_commit"]==PARENT
        and anchor["status"]=="CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and base["machine_id"]==MACHINE and base["runtime_admitted"] is False
        and "canonical_preload_policy" not in base,"actual immutable parent")
    rows:dict[str,W.Row]={}
    for value in W.sequence(base["files"]):
        r=W.keys(value,"relative bytes sha256 git_blob_sha1 git_mode")
        row:W.Row={"relative":W.string(r["relative"]),"bytes":safe_integer(r["bytes"]),
            "sha256":W.hexstr(r["sha256"],64),"git_blob_sha1":W.hexstr(r["git_blob_sha1"],40),"git_mode":W.string(r["git_mode"])}
        W.require(row["relative"] not in rows,"duplicate parent row")
        rows[row["relative"]]=row
    actual:dict[str,tuple[str,str,int]]={}
    for item in git.get("ls-tree","-r","-l","-z",PARENT,"--",PREFIX).split(b"\0"):
        if item:
            h,pathbytes=item.split(b"\t",1);mode,kind,value,size=h.split()
            W.require(kind==b"blob","ordinary SDK Git blobs required")
            actual[pathbytes.decode()[len(PREFIX):]]=(mode.decode(),value.decode(),int(size))
    W.require(len(rows)==1466 and actual=={n:(r["git_mode"],r["git_blob_sha1"],r["bytes"]) for n,r in rows.items()},
        "complete Source31 canonical inventory")
    out=build_sources(plan,git)
    W.require(all(n not in rows for n in NEW_LEAVES),"two helpers must be new leaves")
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
        W.require(len(rows)==plan["source_file_count"]==SOURCE_FILE_COUNT and set(out)=={PREFIX+n for n in sdk_names(plan)}
            and plan["source_bytes"]==sum(r["bytes"] for r in ordered)
            and plan["complete_rows_JSON"]==W.pin(W.canonical(ordered))
            and plan["target_tree"]==ids[""] and plan["Git_object_quote"]==quote,"Source32 rows/tree/quote")
    return out,ordered,trees,quote

def compose(plan: Plan,git: W.Git,repo: Path) -> tuple[dict[str,bytes],list[W.Row],list[W.Tree],W.Quote]:
    return _compose(plan,git,True)

def prepare_plan_v1(*,public_source_commit: str,qualifications: list[W.FileRef],
        observed_at_utc: str,review_at_utc: str) -> Plan:
    """Read-only proposal. Execution requires separate evidence and a Root card."""
    plan:Plan={"schema":"xar.source32.canonical-plan/v1","machine_id":MACHINE,
        "observed_at_utc":observed_at_utc,"review_at_utc":review_at_utc,"parent":PARENT,"ref":REF,
        "target_tree":"0"*40,"public_source_commit":W.hexstr(public_source_commit,40),
        "public_inputs":[{"relative":n,"pin":PUBLIC_PINS[n]} for n in PUBLIC],
        "source31_anchor":SOURCE31_ANCHOR,"source31_BASE":SOURCE31_BASE,"qualifications":[safe_ref(v) for v in qualifications],
        "source_file_count":SOURCE_FILE_COUNT,"source_bytes":0,"complete_rows_JSON":{"bytes":0,"sha256":"0"*64},
        "Git_object_quote":{"retained_upper":0,"largest_temporary_upper":0,"peak_upper":0,"object_count":0}}
    git=W.Git(OWN.parents[2],PREP/"source32-canonical01")
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
    base=W.obj(W.load(W.checked(plan["source31_BASE"])))
    before={W.string(W.obj(v)["relative"]):safe_pin(
        {k:W.obj(v)[k] for k in ("bytes","sha256")}) for v in W.sequence(base["files"])}
    return [{"relative":PREFIX+name,"before_pin":before.get(name),"output_pin":POST_PINS[name],
        "public_input":{"relative":name,"pin":PUBLIC_PINS[name]} if name in PUBLIC else None,
        "public_source_commit":plan["public_source_commit"]} for name in SDK]

def validate_qualifications_v1(plan: Plan) -> None:
    W.require(len(plan["qualifications"])==2 and PARENT_QUAL in plan["qualifications"],"parent and one Source32 qualification")
    W.checked(PARENT_QUAL)
    matches=0
    for item in plan["qualifications"]:
        if item==PARENT_QUAL:continue
        d=W.obj(W.load(W.checked(item)))
        W.require(d["schema"]=="xar.source32.composition-qualification/v1"
            and d["status"]=="OFFLINE_QUALIFIED_NOT_RUNTIME" and d["machine_id"]==MACHINE
            and W.date(d["observed_at_utc"])<=W.utc()
            and W.hexstr(d["public_source_commit"],40)==plan["public_source_commit"]
            and parse_inputs(d["public_inputs"])==plan["public_inputs"]
            and safe_ref(d["source31_anchor"])==SOURCE31_ANCHOR
            and safe_ref(d["source31_BASE"])==SOURCE31_BASE
            and safe_ref(d["parent_package_qualification"])==PARENT_QUAL
            and safe_pin(d["complete_rows_JSON"])==plan["complete_rows_JSON"]
            and W.hexstr(d["target_tree"],40)==plan["target_tree"]
            and safe_integer(d["source_file_count"])==SOURCE_FILE_COUNT and safe_integer(d["epoch_count"])==EPOCH_COUNT
            and safe_integer(d["runtime_calls"])==safe_integer(d["new_campaign_credit"])==0
            and d["RAM_composition_and_exact_pins_passed"] is True
            and d["strict_and_strict_equality_passed"] is True
            and safe_pin(d["clock_qualification_payload"])==QUALIFICATION_PIN
            and safe_integer(d["clock_candidate_tests_passed"])==9
            and d["M6_producer_consumer_passed"] is True
            and safe_integer(d["M6_candidate_tests_passed"])==M6_CASE_COUNT,"Source32 qualification binding")
        pins:dict[str,W.Pin]={}
        for value in W.sequence(d["output_pins"]):
            row=W.keys(value,"relative bytes sha256")
            name=W.string(row["relative"])
            W.require(name not in pins,"duplicate qualification output")
            pins[name]=safe_pin({k:row[k] for k in ("bytes","sha256")})
        W.require(pins==POST_PINS,"eight exact qualified outputs")
        matches+=1
    W.require(matches==1,"one Source32 composition qualification")
def execute_v1(*, plan_ref: W.FileRef, card_ref: W.FileRef) -> W.FileRef:
    """Single Root execution; failure consumes its anchor."""
    plan=parse_plan(W.load(W.checked(plan_ref)))
    card=W.obj(W.load(W.checked(card_ref)))
    W.require(card["schema"]=="xar.storage.Source32-root-canonical-Git.v1"
        and card["owner"]=="Root" and card["machine_id"]==MACHINE
        and card["status"]=="ADMITTED" and card["root_direct_execution_release"] is True,"Root release required")
    W.require(0<=(W.utc()-W.date(card["observed_at_utc"])).total_seconds()<=600,"fresh release")
    limit=min(W.date(card["review_at_utc"]),W.date(plan["review_at_utc"]))
    W.require(W.utc()<limit and safe_ref(card["writer"])==W.file_ref(OWN)
        and safe_ref(card["plan"])==plan_ref,"writer/plan admission")
    source_ref=safe_ref(card["source_admission"])
    source=W.obj(W.load(W.checked(source_ref)))
    W.require(source["machine_id"]==MACHINE,"same-machine source admission")
    repo=OWN.parents[2]
    W.require(subprocess.check_output([sys.executable,"-B",str(repo/"tools/ck3_live_run_id.py"),"machine"]).decode().strip()==MACHINE,"actual machine")
    metadata=Path(W.string(card["metadata_root"])).resolve()
    anchor=Path(W.string(card["future_anchor"])).resolve()
    W.require(anchor==metadata/"SOURCE32-CANONICAL-ANCHOR.json"
        and metadata==(PREP/"source32-canonical01").resolve()
        and safe_integer(card["anchor_hard_bytes"])==65536,"anchor scope")
    W.no_reparse(metadata)
    W.require(not anchor.exists() and not anchor.is_symlink(),"anchor consumed")
    capacity,budget=W.obj(card["capacity"]),W.obj(card["Git"])
    zfloor,dfloor=safe_integer(capacity["Z_free_floor_bytes"]),safe_integer(capacity["D_free_floor_bytes"])
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
    hard=safe_integer(budget["hard_bytes"])
    W.require(safe_integer(budget["peak_upper_bytes"])==quote["peak_upper"]<=hard
        and budget["prior_holds_retained"] is True,"Git budget")
    W.require(len(git.get("var","GIT_AUTHOR_IDENT"))+len(git.get("var","GIT_COMMITTER_IDENT"))<4096,"identity cap")
    metadata.mkdir(exist_ok=True)
    record:dict[str,object]={"schema":"xar.source32.canonical-git-anchor/v1","machine_id":MACHINE,
        "status":"RUNNING_OR_UNKNOWN","start_utc":W.utc().isoformat(),"execution_owner":"Root",
        "root_direct_execution_release":True,"parent":PARENT,"ref":REF,"writer":W.file_ref(OWN),
        "source_plan":plan_ref,"capacity_card":card_ref,"source_admission":source_ref,
        "actual_Source31_anchor":plan["source31_anchor"],"actual_Source31_BASE":plan["source31_BASE"],
        "Git_object_quote":quote,"runtime_calls":0,"SDK_export_calls":0,"push_calls":0,
        "index_or_tracked_worktree_mutations":0,"actual_loaded_provider":False,
        "canonical_patch_rows":canonical_patch_rows_v1(plan),"qualifications":plan["qualifications"],
        "public_source_commit":plan["public_source_commit"],"public_inputs":plan["public_inputs"],
        "source_epoch_count":EPOCH_COUNT}
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
                data=b"Source32: route-window clock and bounded wartime sway opportunity\n").strip().decode()
            commit_body=git.get("cat-file","commit",commit)
            header=commit_body.split(b"\n\n",1)[0].splitlines()
            W.require(len(commit_body)<=8192 and [v for v in header if v.startswith(b"parent ")]==[b"parent "+PARENT.encode()]
                and [v for v in header if v.startswith(b"tree ")]==[b"tree "+tree.encode()],"commit ancestry")
            record.update(commit=commit,tree=tree,output_pins=[r for r in rows if PREFIX+r["relative"] in out],
                source_file_count=len(rows),source_bytes=sum(r["bytes"] for r in rows),
                complete_rows_JSON=W.pin(W.canonical(rows)),charged_retained_objects_upper=charged)
            save()
            W.require(charged==quote["retained_upper"],"retained accounting")
            W.checked(plan["source31_anchor"]);guard()
            git.get("update-ref","--no-deref",REF,commit,"0"*40)
            W.require(git.get("rev-parse",REF).strip().decode()==commit,"ref readback")
            record.update(status="CANONICAL_REF_CREATED_NOT_DEPLOYED",end_utc=W.utc().isoformat(),future_writes=0)
        except BaseException as error:
            record.update(status="FAILED_OR_UNKNOWN_DO_NOT_RETRY",end_utc=W.utc().isoformat(),
                error={"type":type(error).__name__,"text":str(error)[:1024]})
            save();raise
        save()
    return W.file_ref(anchor)


