"""A14 complete cold graph, prepared in RAM; Root alone adopts or launches."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
from types import ModuleType, SimpleNamespace
from typing import Callable, Literal, Protocol, TypedDict, cast

sys.dont_write_bytecode=True
MACHINE="xenoamess-full-tower-eb9d2c1186"
OWN=Path(__file__).resolve().parent
P=Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O=P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
U13=P/"robert30-v20261019-campaign01/runtime-a13"
U14=U13.with_name("runtime-a14")
INDEX=U13/"ROOT-A13-ACTUAL-CLOSURE-INDEX01.json"
INDEX_PIN=(10767,"5cbc7d3483e00a6e7413e56fa7b59547b4d25738eea93919ce43e6b05bd23a45")
Doc=dict[str,object]
Outputs=dict[Path,bytes]
class ExactRef(TypedDict):
    path:str
    bytes:int
    sha256:str
class PlanV1(TypedDict):
    schema:Literal["xar.Source28-A14-complete-cold-input/v1"]
    machine_id:str
    execution_owner:Literal["Root"]
    root_direct_execution_release:Literal[True]
    observed_at_utc:str
    attempt_nonce:str
    task_nonce:str
    full_storage_ref:ExactRef
    live_storage_ref:ExactRef
    compact_base_ref:ExactRef
    canonical_anchor_ref:ExactRef
    union_producer:ExactRef
    stage_producer:ExactRef
    screen_admission_path:str
    actual_A13_closure_ref:ExactRef
    current_next_ref:ExactRef
    current_driver_review_ref:ExactRef
    cold_prelaunch_ref:ExactRef
    driver_review_ref:ExactRef
    environment_migration_ref:ExactRef
    steam_native_state_ref:ExactRef
    steam_native_sources:dict[str,ExactRef]
    native_target_ref:ExactRef
    native_binding_ref:ExactRef
    native_binding_helper_ref:ExactRef
    rich_sources:dict[str,ExactRef]
    native_sidecars:dict[str,ExactRef]
class Dynamic(Protocol):
    def __call__(self,*args:object,**kwargs:object)->object: ...
class Compose(Protocol):
    def __call__(self,plan:PlanV1,*,display_values:dict[str,bytes],
                 display_review:Doc,companion_values:Outputs)->object: ...
class Reader(Protocol):
    def __call__(self,reference:ExactRef,limit:int=1048576)->Doc: ...

def need(value:object,message:str)->None:
    if not value:raise ValueError("A14 cold: "+message)
def record(value:object)->Doc:
    if not isinstance(value,dict):raise ValueError("A14 cold: object")
    need(all(type(k) is str for k in value),"string fields")
    return cast(Doc,value)
def text(value:object)->str:
    if type(value) is not str or not value or "\0" in value:raise ValueError("A14 cold: text")
    return value
def uint(value:object)->int:
    if type(value) is not int or not 0<=value<2**53:raise ValueError("A14 cold: safe integer")
    return value
def ref_value(value:object)->ExactRef:
    d=record(value);need(set(d)=={"path","bytes","sha256"},"exact ref fields")
    path,size,digest=text(d["path"]),uint(d["bytes"]),text(d["sha256"])
    need(Path(path).is_absolute() and size>0 and re.fullmatch("[0-9a-f]{64}",digest),"absolute pinned ref")
    return {"path":path,"bytes":size,"sha256":digest}
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def enc(value:object)->bytes:
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()
def raw(path:Path|str,limit:int=1048576)->bytes:
    p=Path(path);before=p.stat()
    need(0<before.st_size<=limit,"bounded input")
    with p.open("rb") as stream:data=stream.read(limit+1)
    after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and len(data)==before.st_size,"input changed")
    return data
def ref(path:Path|str)->ExactRef:
    p=Path(path).resolve();data=raw(p)
    return {"path":str(p),"bytes":len(data),"sha256":sha(data)}
def verify_exact_bytes_ref(reference:ExactRef,limit:int=1048576)->bytes:
    item=ref_value(reference);data=raw(item["path"],limit)
    need((len(data),sha(data))==(item["bytes"],item["sha256"]),"exact input hash")
    return data

def checked(reference:ExactRef,limit:int=1048576)->Doc:
    value:object=json.loads(verify_exact_bytes_ref(reference,limit));return record(value)
def module(reference:ExactRef,name:str)->ModuleType:
    data=raw(reference["path"]);need(ref(reference["path"])==reference,"module pin")
    m=ModuleType(name);m.__file__=reference["path"];sys.modules[name]=m
    exec(compile(data,m.__file__,"exec"),vars(m));return m
def dynamic(m:ModuleType,name:str)->Dynamic:
    # One bounded legacy boundary: exact source origins/pins precede this check.
    fn:object=getattr(m,name);need(callable(fn),"legacy callable "+name)
    return cast(Dynamic,fn)
def function(m:ModuleType,name:str)->str:
    source=raw(text(m.__file__)).decode("utf-8-sig")
    nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name]
    need(len(nodes)==1,"one exact function "+name)
    return text(ast.get_source_segment(source,nodes[0]))
def one(source:str,before:str,after:str,count:int=1)->str:
    need(source.count(before)==count,"finite seam "+before[:64])
    return source.replace(before,after,count)
def bytes_map(value:object)->dict[str,bytes]:
    d=record(value);out:dict[str,bytes]={}
    for name,data in d.items():
        need(type(data) is bytes,"source bytes")
        out[name]=cast(bytes,data)
    return out
def outputs(value:object)->Outputs:
    if not isinstance(value,dict):raise ValueError("A14 cold: output map")
    out:Outputs={}
    for path,data in value.items():
        need(isinstance(path,Path) and type(data) is bytes,"Path/bytes outputs")
        out[cast(Path,path)]=cast(bytes,data)
    return out
def parse_plan(value:object)->PlanV1:
    d=record(value);need(set(d)==set(PlanV1.__annotations__),"exact plan fields")
    refs=("full_storage_ref","live_storage_ref","compact_base_ref","canonical_anchor_ref",
        "union_producer","stage_producer","actual_A13_closure_ref","current_next_ref",
        "current_driver_review_ref","cold_prelaunch_ref","driver_review_ref","environment_migration_ref",
        "steam_native_state_ref","native_target_ref","native_binding_ref","native_binding_helper_ref")
    for key in refs:ref_value(d[key])
    for key in ("schema","machine_id","execution_owner","observed_at_utc","attempt_nonce","task_nonce","screen_admission_path"):
        text(d[key])
    for key in ("steam_native_sources","rich_sources","native_sidecars"):
        for item in record(d[key]).values():ref_value(item)
    need(d["schema"]=="xar.Source28-A14-complete-cold-input/v1" and d["machine_id"]==MACHINE
         and d["execution_owner"]=="Root" and d["root_direct_execution_release"] is True,"Root plan")
    for key in ("attempt_nonce","task_nonce"):
        need(re.fullmatch("[0-9a-f]{32}",text(d[key])) is not None,"new nonce")
    need(d["attempt_nonce"]!=d["task_nonce"],"distinct nonces")
    return cast(PlanV1,d)
def _fresh(value:object)->None:
    at=datetime.fromisoformat(text(value).replace("Z","+00:00"))
    offset=at.utcoffset()
    need(offset is not None and offset.total_seconds()==0
         and -10<=(datetime.now(timezone.utc)-at).total_seconds()<=600,"fresh UTC")

def closure(plan:PlanV1)->Doc:
    need(Path(plan["actual_A13_closure_ref"]["path"]).resolve()==INDEX.resolve()
         and (plan["actual_A13_closure_ref"]["bytes"],plan["actual_A13_closure_ref"]["sha256"])==INDEX_PIN,
         "actual A13 closed authority")
    x=checked(plan["actual_A13_closure_ref"],16384)
    need(x["schema"]=="xar.C23-A13-pre-RPC-failure-closed/v1" and x["machine_id"]==MACHINE
         and x["SDK_actual_exits"] is None and x["SDK_actual_exit_status"]=="UNKNOWN_PAIR_NOT_PUBLISHED"
         and x["sdk_pair_published"] is False and x["SDK_dual_zero_qualified"] is False
         and x["no_SEM_CAP_gameplay"] is True and uint(x["NEXT"])==10538
         and uint(x["ordinary_cycle_credit"])==uint(x["new_game_days_credit"])==0
         and x["original_wall_origin_reset"] is False,"unknown SDK exits retained; no credit")
    facts=record(x["source_refs"]);need(len(facts)==27,"all actual A13 facts")
    for item in facts.values():verify_exact_bytes_ref(ref_value(item),65536)
    g=record(x["Game"]);need(uint(g["exit_code"])==1 and g["forced"] is True
         and uint(g["job_active_processes_final"])==0,"actual forced Game1/Job0")
    old={text(x[k]) for k in ("attempt_nonce","actual_supervisor_bootstrap_task_nonce",
                              "metadata_supervisor_task_nonce","actual_display_task_nonce")}
    need(plan["attempt_nonce"] not in old and plan["task_nonce"] not in old,"no consumed nonce reuse")
    current=checked(plan["current_next_ref"],16384)
    need(plan["current_next_ref"]==facts["NEXT-SEQUENCE-P37.json"]
         and uint(current["next_sequence"])==10538,"actual unchanged NEXT")
    return x

def state_guard(plan:PlanV1)->Doc:
    x=closure(plan);current=checked(plan["current_driver_review_ref"],16384)
    need(plan["current_driver_review_ref"]==record(x["source_refs"])["ROOT-A13-CURRENT-DRIVER-SAVE-REVIEW01.json"]
         and current["canonical_Driver_and_SAVE_bytes_unchanged"] is True
         and uint(current["copies_created"])==0 and uint(current["new_business_credit"])==0,"actual fresh current Driver/SAVE proof")
    need(Path(plan["cold_prelaunch_ref"]["path"]).resolve()==U13/"ROOT-C23-COLD-PRELAUNCH.json"
         and (plan["cold_prelaunch_ref"]["bytes"],plan["cold_prelaunch_ref"]["sha256"])==
         (8555,"ba00f401334c6b2b183cd9db1141e50a9b8f4993c6d51aa7ca253c575636195e"),"accepted d33 cold prelaunch")
    pre=checked(plan["cold_prelaunch_ref"],16384);review=checked(plan["driver_review_ref"],32768)
    need(pre["materialized_driver_review"]==plan["driver_review_ref"] and pre["environment_migration"]==plan["environment_migration_ref"]
         and review["checkpoint"]==pre["checkpoint"] and review["canonical_validation"]==pre["validation"],
         "existing d33 cold authority")
    rows=current["sources"];need(type(rows) is list and len(rows)==2,"Driver/SAVE proof pair")
    first=record(cast(list[object],rows)[0]);driver=ref_value(first["ref"]);ident=record(first["identity"])
    st=Path(driver["path"]).stat();old=record(review["driver_stat"])
    need(driver==pre["driver_state"] and first["stable_before_after"] is True
         and review["driver_stat_schema"]=="xar.file-stat-identity.os-ns-decimal.v1"
         and (st.st_size,str(st.st_ino),str(st.st_mtime_ns))==(old["size"],old["FileID"],old["mtime_ns"])
         and (st.st_size,str(st.st_ino),str(st.st_mtime_ns))==(ident["bytes"],ident["file_id"],ident["mtime_ns"]),
         "current same canonical Driver identity")
    need(record(current["wal"])=={"exists":False,"ref":None},"no WAL")
    need(checked(ref_value(current["environment_manifest"]),32768)["environment_sha256"]==pre["environment_sha256"],
         "unchanged ENV")
    for item in cast(list[object],pre["sidecars"]):need(checked(ref_value(item),65536).get("pending") is None,"no sidecar pending")
    need(ref(ref_value(pre["installed_settings"])["path"])==pre["installed_settings"],"prepared settings exact")
    return {"machine_id":MACHINE,"actual_A13_index":plan["actual_A13_closure_ref"],
        "current_driver_review":plan["current_driver_review_ref"],"cold_prelaunch":plan["cold_prelaunch_ref"],
        "actual_next_sequence":10538,"historical_saved_basis_next_sequence":10481,"Driver_SAVE_body_reads":0}

def closure_source(plan:PlanV1)->str:
    return "A14_INDEX: dict[str,object]="+repr(plan["actual_A13_closure_ref"])+"\n"+'''
from typing import Callable as _A14Callable,cast as _A14cast
def validate_actual_a13_index_v1(reference:object,checked:_A14Callable[[object,int],dict[str,object]])->dict[str,object]:
    require(reference==A14_INDEX,'actual A13 closed index')
    value=checked(reference,16384)
    require(value['schema']=='xar.C23-A13-pre-RPC-failure-closed/v1' and value['machine_id']==MACHINE
        and value['SDK_actual_exits'] is None and value['SDK_actual_exit_status']=='UNKNOWN_PAIR_NOT_PUBLISHED'
        and value['sdk_pair_published'] is False and value['SDK_dual_zero_qualified'] is False
        and value['no_SEM_CAP_gameplay'] is True and type(value['NEXT']) is int and value['NEXT']==10538
        and type(value['ordinary_cycle_credit']) is int and type(value['new_game_days_credit']) is int
        and value['ordinary_cycle_credit']==value['new_game_days_credit']==0
        and value['original_wall_origin_reset'] is False,'honest A13 preRPC closure')
    facts=value['source_refs'];require(type(facts) is dict,'A13 fact map')
    for item in _A14cast(dict[str,object],facts).values():_a14_verify_exact_fact(item)
    return value
def _a14_verify_exact_fact(item:object)->None:
    require(type(item) is dict,'exact raw fact ref')
    row=_A14cast(dict[str,object],item)
    require(set(row)=={'path','bytes','sha256'} and type(row['path']) is str
        and type(row['bytes']) is int and 0<row['bytes']<=65536
        and type(row['sha256']) is str,'bounded raw fact fields')
    path=Path(_A14cast(str,row['path']));before=path.stat()
    with path.open('rb') as stream:data=stream.read(65537)
    after=path.stat()
    require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
        and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
            (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'exact raw fact bytes')
'''

def patch_recording_bootstrap_loader_v1(source:bytes,strict_identity:str)->bytes:
    body=source.decode("utf-8")
    nodes=[n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef) and n.name=="_a10_helper"]
    need(len(nodes)==1,"one real verified bootstrap helper loader")
    segment=text(ast.get_source_segment(body,nodes[0]))
    before="    exec(compile(raw,str(p),'exec'),vars(module))\n    return module"
    after="    exec(compile(raw,str(p),'exec'),vars(module))\n    exec(compile("+repr(strict_identity)+",'A14-strict-current-recording','exec'),vars(module))\n    return module"
    changed=one(segment,before,after)
    result=one(body,segment,changed)
    need(result.replace(after,before,1)==body,"only postverification helper overlay")
    compile(result,"A14-recording-bootstrap-loader","exec")
    return result.encode()

def patch_recording_metadata_loader_v1(scope:Doc,runtime:Path,strict_identity:str)->None:
    loader_value=scope["_load"];need(callable(loader_value),"original helper loader")
    original_loader=cast(Dynamic,loader_value)
    target=runtime.resolve()/"root_c23_a03_source_abort_checkpoint_inputs.py"
    def load(path:object,digest:object,name:object)->object:
        result=original_loader(path,digest,name)
        need(isinstance(path,(str,Path)),"helper path")
        candidate=Path(cast(str|Path,path)).resolve()
        if candidate==target:
            need(isinstance(result,ModuleType),"actual helper module")
            exec(compile(strict_identity,"A14-recording-metadata","exec"),vars(cast(ModuleType,result)))
        return result
    scope["_load"]=load

def build_sources(plan:PlanV1,stage:ModuleType)->tuple[dict[str,bytes],Doc]:
    intake=record(dynamic(stage,"read_accepted_a13_sources_v1")(plan["current_next_ref"]))
    source=bytes_map(intake["source"]);names=record(vars(stage))["OPS14_NAMES"]
    need(type(names) is tuple,"five lookup names")
    rename={text(old):text(old).replace("A12","A14") for old in cast(tuple[object,...],names)}
    source=bytes_map(dynamic(stage,"owner_complete_v1")(source,rename))
    for name,data in tuple(source.items()):
        source[name]=data.replace(b"ROOT-FINAL-SDK-FREEZE-P37C23-A13.json",
                                 b"ROOT-FINAL-SDK-FREEZE-P37C23-A14.json")
    boot=source["root_checkpoint_bootstrap_c23.py"].decode()
    strict_identity=text(getattr(stage,"RECORDING_IDENTITY14"))
    boot=patch_recording_bootstrap_loader_v1(boot.encode(),strict_identity).decode()
    boot=one(boot,"if __name__ == '__main__':",closure_source(plan)+"\nif __name__ == '__main__':")
    source["root_checkpoint_bootstrap_c23.py"]=boot.encode()
    body=source["root_native30_supervisor_c23.py"].decode().replace("C23-A13","C23-A14")
    for before,after,count in (("args.attempt=='a13'","args.attempt=='a14'",1),
        ("value.get('attempt_id')=='a13'","value.get('attempt_id')=='a14'",1),
        ('choices=("a13",)','choices=("a14",)',1),('"attempt_id":"a13"','"attempt_id":"a14"',2),
        ("    _validate_a13_attempt(args, config)","    _validate_a14_attempt(args, config)",1)):
        body=one(body,before,after,count)
    extra=closure_source(plan)+'''
def _validate_a14_attempt(args,config):
    value=_validate_a13_attempt(args,config)
    closed=validate_actual_a13_index_v1(value['prior_failure_a13'],_a03_checked)
    old={closed[k] for k in ('attempt_nonce','actual_supervisor_bootstrap_task_nonce',
                            'metadata_supervisor_task_nonce','actual_display_task_nonce')}
    require(args.attempt_nonce not in old and args.task_nonce not in old,'fresh A14 nonces')
    return value
'''
    body=one(body,"def main(args):",extra+"\ndef main(args):")
    source["root_native30_supervisor_c23.py"]=body.encode()
    for name,data in source.items():
        if name.endswith(".py"):compile(data,name,"exec")
    q=checked(ref(O/"source28-a13-prep01/A13-ROOT-QUOTE02.json"),262144)
    oldreview=record(q["sources"])
    supplemental=cast(list[object],oldreview["supplemental_import_rows"])
    staging=cast(list[object],oldreview["staging_files"])
    review={"schema":"xar.A14-accepted-source-intake/v1","machine_id":MACHINE,"feeder":{},
        "runtime_source_output_names":sorted(source),
        "actual_source_rows":[ref(U13/name) for name in sorted(source)],
        "supplemental_import_rows":[ref(U13/Path(text(record(r)["path"])).name) for r in supplemental],
        "staging_files":[ref(U13/Path(text(record(r)["path"])).name) for r in staging],
        "actual_A13_index":plan["actual_A13_closure_ref"],"intake":intake["review"],"new_day_credit":0}
    return source,review

def _native(plan:PlanV1)->tuple[Doc,Doc,dict[str,int]]:
    helper=module(plan["native_binding_helper_ref"],"_a14_actual_native_binding")
    bound=dynamic(helper,"load_static_binding")(plan["native_binding_ref"],machine_id=MACHINE)
    values=record(dynamic(helper,"launch_values")(bound))
    target:object=getattr(bound,"target");exports:object=getattr(target,"exports")
    need(type(exports) is tuple,"qualified native exports")
    rvas:dict[str,int]={}
    for item in cast(tuple[object,...],exports):
        need(type(item) is tuple and len(cast(tuple[object,...],item))==2,"export pair")
        name,rva=cast(tuple[object,object],item)
        if text(name)!="XarRefillCoreCarrier12004":rvas[text(name)]=uint(rva)
    targetdoc=checked(plan["native_target_ref"],16384)
    binding=checked(plan["native_binding_ref"],16384)
    need(binding["source_freeze"]==plan["compact_base_ref"] and binding["native_target"]==plan["native_target_ref"]
         and targetdoc["native_build_label"]==values["native_build_label"],"same Source28/Native31 target")
    return values,targetdoc,rvas

def _legacy_result(value:object)->tuple[Outputs,Doc]:
    need(type(value) is tuple and len(cast(tuple[object,...],value))==2,"legacy result")
    pair=cast(tuple[object,object],value)
    return outputs(pair[0]),record(pair[1])

def compose(plan_value:object,*,display_values:dict[str,bytes],display_review:Doc,
            companion_values:Outputs)->tuple[Outputs,Doc]:
    plan=parse_plan(plan_value);_fresh(plan["observed_at_utc"])
    need(not U14.exists() and not (O/"tasks/spec-supervisor-a14").exists(),"fresh runtime and Task namespace")
    full=checked(plan["full_storage_ref"],65536)
    need(plan["full_storage_ref"]==plan["live_storage_ref"] and full["machine_id"]==MACHINE
         and full["status"]=="ADMITTED","one current full")
    deadline=text(full["review_at_utc"])
    need(datetime.now(timezone.utc)<datetime.fromisoformat(deadline),"finite full review")
    steam=checked(plan["steam_native_state_ref"],16384)
    _fresh(steam.get("observed_at_utc",steam.get("observation_ended_at_utc")))
    need(steam.get("status")=="offline" and steam.get("offline_mode") is True,"actual background offline")
    adapter_ref=ref(OWN/"prepare_decision_display_runtime_v1.py")
    helper_ref=ref(OWN/"prepare_rich_decision_graph_v1.py")
    need((adapter_ref["bytes"],adapter_ref["sha256"])==(4025,"ebec3aebd58679693ccd01da441389cb67b25650e51842ed6540b471ff542735")
         and (helper_ref["bytes"],helper_ref["sha256"])==(16215,"a9e6be79e020900137f3902d4333b725664ad281eb7e30e7a0e14c60adf6dfb7"),"qualified identity1300 preparation helpers")
    module(adapter_ref,"prepare_decision_display_runtime_v1")
    module(helper_ref,"prepare_rich_decision_graph_v1")
    stage=module(plan["stage_producer"],"_a14_final_stage")
    source,source_review=build_sources(plan,stage);state=state_guard(plan)
    native_values,native_target,rvas=_native(plan)
    rich={name:raw(item["path"]) for name,item in plan["rich_sources"].items()}
    sidecars={name:raw(item["path"]) for name,item in plan["native_sidecars"].items()}
    for group in (plan["rich_sources"],plan["native_sidecars"]):
        for item in group.values():need(ref(item["path"])==item,"qualified delta source pins")
    a13=importlib.import_module("prepare_source28_a13_union_v1")
    dynamic(a13,"source28_guard")(dict(plan))
    a05=importlib.import_module("prepare_c23_a05_union_v1")
    recipe=function(a05,"compose")
    recipe=text(dynamic(stage,"derive_owner_compose_v1")(recipe))
    recipe=recipe.replace("C23-A05","C23-A14").replace("C23-A04","C23-A13")
    recipe=recipe.replace("'a05'","'a14'").replace("spec-supervisor-a05","spec-supervisor-a14")
    recipe=recipe.replace("2026-10-20T06:30:00+00:00",deadline)
    recipe=recipe.replace("source26_canonical_anchor","source28_canonical_anchor").replace("xar.source26.","xar.source28.")
    recipe=one(recipe,"xar.C23-A14-union-prepare-input/v1","xar.Source28-A14-complete-cold-input/v1")
    recipe=one(recipe,"T5/name:raw(T4/name)",
        "T5/name:(cold_prelaunch_bytes if name=='ROOT-C23-COLD-PRELAUNCH.json' else raw(T4/name))")
    recipe=one(recipe,"    policy,six,replaced,display_values,display_review=apply_a14_policy_stage_v1(",
        "    policy['runtime_import_source_pins']=[original.target_ref(T5/Path(r['path']).name,source[Path(r['path']).name]) for r in source_review['supplemental_import_rows']+source_review['staging_files']]\n"
        "    policy,six,replaced,display_values,display_review=apply_a14_policy_stage_v1(")
    recipe=one(recipe,"final={**base,'attempt_id':'a14','canonical_preload_policy':policy_ref}",
        "final={**base,**native_freeze,'attempt_id':'a14','canonical_preload_policy':policy_ref}")
    recipe=one(recipe,"native=checked(ref(T4/'ROOT-NATIVE30-NATIVE-PIN-C23-A13.json'))",
        "native=dict(native_metadata)")
    recipe=one(recipe,"                prior_failure_a04=ref(O/'A04-FAILED-CLOSED-INDEX.json'),prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'))",
        "                prior_failure_a04=ref(O/'A04-FAILED-CLOSED-INDEX.json'),prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'),**prior_failures)")
    marker="        put(name.replace('-C23.','-C23-A14.'),value)"
    recipe=one(recipe,marker,"        value=bind_metadata(name,value,final_ref,native_ref)\n"+marker)
    recipe=one(recipe,"    return outputs,quote","    require(len(outputs)==144,'complete A14 144')\n    return outputs,quote")
    base=checked(plan["compact_base_ref"],524288);anchor=checked(plan["canonical_anchor_ref"],65536)
    old_native=checked(ref(U13/"ROOT-NATIVE30-NATIVE-PIN-C23-A13.json"),16384)
    dll=ref_value(native_target["dll"]);production=ref_value(native_target["qualification"])
    production_doc=checked(production,65536)
    build_plan=record(production_doc["plan"])
    build_input={key:build_plan[key] for key in ("path","bytes","sha256")}
    native_metadata={"schema":"xar.C23-Native31-compiled-cold-session/v1","machine_id":MACHINE,
        "status":"COMPILED_COLD_NATIVE_IDENTITY_PINNED_NO_RUNTIME","pipe_name":old_native["pipe_name"],
        "source_freeze":build_input,"source_freeze_role":"Native31_build_input_manifest",
        "source_overlay":production_doc["source_overlay"],"runtime_qualified":False,
        "native_build_label":native_values["native_build_label"],"dll":dll,"native_dll_path":dll["path"],
        "native_dll_bytes":dll["bytes"],"native_dll_sha256":dll["sha256"],"export_rvas":rvas,
        "delivery":production,"qualification":production,"actual_runtime_loaded":False,
        "actual_loaded_provider_issued":False,"source28_static_binding":plan["native_binding_ref"]}
    native_freeze={k:native_values[k] for k in ("native_build_label","dll_sha256","git_head")}
    native_freeze.update(native_dll_sha256=dll["sha256"],native_dll_bytes=dll["bytes"],
        native_dll_path=dll["path"],native_final_freeze=production,native31_binding=plan["native_binding_ref"])
    oldconfig=checked(ref(U13/"ROOT-LAUNCH-CONFIG-C23-A13.json"),16384)
    failures=dict(record(oldconfig["cold_attempt"]))
    prior_failures={k:v for k,v in failures.items() if k.startswith("prior_failure_a") and k not in
        {"prior_failure_a04","prior_failure_a04_unregistered"}}
    prior_failures["prior_failure_a13"]=plan["actual_A13_closure_ref"]
    def bind_metadata(name:object,value:object,freeze_ref:object,native_ref:object)->Doc:
        d=record(value);kind=text(name)
        if kind=="ROOT-LAUNCH-CONFIG-C23.json":
            d.update(native_values,dll_bytes=dll["bytes"],native_final_freeze=str(Path(production["path"]).resolve()),
                native_final_freeze_sha256=production["sha256"],build_receipt_sha256=production["sha256"],
                native_bridge_after_saved_load=False,steam_native_state=plan["steam_native_state_ref"],
                cold_prelaunch={"path":str(U14/"ROOT-C23-COLD-PRELAUNCH.json"),
                    "bytes":plan["cold_prelaunch_ref"]["bytes"],"sha256":plan["cold_prelaunch_ref"]["sha256"]})
        elif kind=="ROOT-CLEAN-SOURCE-FROZEN-C23.json":
            d.update(native_build_label=native_values["native_build_label"],dll_sha256=dll["sha256"],git_head=native_values["git_head"])
        elif kind=="ROOT-NATIVE30-SDK-BINDING-C23.json":
            d.update(status="NATIVE31_SDKC23_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",native_dll_sha256=dll["sha256"])
        return d
    original_value:object=getattr(a05,"original")
    need(isinstance(original_value,ModuleType),"original recipe module")
    original_module=cast(ModuleType,original_value)
    original=SimpleNamespace(**vars(original_module))
    a10=importlib.import_module("prepare_c23_a10_union_v1")
    ram_spec=function(a10,"ram_supervisor_spec")
    ram_spec=ram_spec.replace('"--attempt","a10"','"--attempt","a14"')
    environment:Doc=dict(vars(a05))
    environment.update(__file__=__file__,T4=U13,T5=U14,SOURCE26_PARENT=anchor["parent"],
        ref=ref,raw=raw,checked=checked,enc=enc,sha=sha,
        build_sources=lambda:(source,source_review),state_guard=lambda:state,original=original,
        cold_prelaunch_bytes=raw(plan["cold_prelaunch_ref"]["path"],16384),CONTROL_SEQUENCE=10540,
        native_metadata=native_metadata,native_freeze=native_freeze,prior_failures=prior_failures,
        bind_metadata=bind_metadata,
        apply_a14_policy_stage_v1=getattr(stage,"apply_a14_policy_stage_v1"),
        A14_QUALIFIED_RICH=rich,A14_NATIVE_SIDECARS=sidecars,A14_EXPORT_RVAS=rvas,
        A14_NATIVE_LABEL=native_values["native_build_label"])
    ram_scope:Doc=dict(vars(a10));ram_scope.update(U10=U14)
    ram_spec=one(ram_spec,'"--attempt-nonce",kw["attempt"],"--task-nonce",kw["task"]]',
        '"--attempt-nonce",kw["attempt"],"--task-nonce",kw["task"],"--steam-native-state",STEAM_REF["path"]]')
    ram_scope["STEAM_REF"]=plan["steam_native_state_ref"]
    exec(compile(ram_spec,"A14-typed-supervisor-spec","exec"),ram_scope)
    setattr(original,"_ram_spec",ram_scope["ram_supervisor_spec"])
    exec(compile(recipe,"A14-complete-cold144","exec"),environment)
    value:object=environment["compose"];need(callable(value),"complete compose")
    result,quote=_legacy_result(cast(Compose,value)(plan,display_values=display_values,
        display_review=display_review,companion_values=companion_values))
    quote.update(schema="xar.Source28-A14-complete-cold-quote/v1",actual_A13_index=plan["actual_A13_closure_ref"],
        current_driver_review=plan["current_driver_review_ref"],new_first_sequence=10538,saved_basis_next_sequence=10481,
        new_timing_enabled=False,control_probe_sequence=None,control_probe_output_path=None,
        unknown10534_credit=0,rollback_cycles=5,rollback_days=0,additional_rollback_since_A13=0,
        original_wall_origin_reset=False,native31_loaded_provider_issued=False)
    need(len(result)==144 and uint(quote["unique_files"])==144,"actual complete144")
    return result,quote

def cold_owner(inputs_value:object)->tuple[Outputs,Doc]:
    inputs=record(inputs_value)
    need(inputs.get("schema")=="xar.C23-A14-cold-owner-metadata-input/v1"
         and inputs.get("machine_id")==MACHINE,"actual A14 cold-owner inputs")
    plan_ref=ref_value(inputs["cold_graph_plan"])
    plan=parse_plan(checked(plan_ref,65536))
    stage=module(plan["stage_producer"],"_a14_cold_metadata_stage")
    a13=importlib.import_module("prepare_source28_a13_union_v1")
    a08=importlib.import_module("prepare_c23_a08_union_v1")
    def metadata_source(value:object)->str:
        source=text(dynamic(a13,"metadata_source")(text(value)))
        source=text(dynamic(stage,"derive_current_frontier_metadata_v1")(source,plan["current_next_ref"]))
        return text(dynamic(stage,"derive_cold_owner_v1")(source))
    def metadata_scope(value:object,runtime:object)->None:
        need(isinstance(value,dict) and isinstance(runtime,Path) and runtime.resolve()==U14.resolve(),
             "actual A14 metadata namespace")
        dynamic(a13,"metadata_scope")(value,runtime)
        patch_recording_metadata_loader_v1(record(value),cast(Path,runtime),text(getattr(stage,"RECORDING_IDENTITY14")))
    source=function(a08,"cold_owner").replace("A08","A14").replace("a08","a14")
    namespace:Doc=dict(vars(a08))
    namespace.update(U8=U14,T5=U14,metadata_source=metadata_source,metadata_scope=metadata_scope)
    exec(compile(source,"A14-existing-cold-owner","exec"),namespace)
    projected={k:v for k,v in inputs.items() if k!="cold_graph_plan"}
    callable_value:object=namespace["cold_owner"];need(callable(callable_value),"cold-owner factory")
    return _legacy_result(cast(Dynamic,callable_value)(projected))
