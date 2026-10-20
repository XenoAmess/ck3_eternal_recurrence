"""A15 cold continuation from immutable A14; preparation only, Root owns adoption."""
from __future__ import annotations
import ast,copy,hashlib,importlib,json,re,sys,types
from datetime import datetime,timezone
from pathlib import Path
from types import ModuleType,SimpleNamespace
from typing import Callable,Literal,Protocol,TypedDict,cast
sys.dont_write_bytecode=True
Doc=dict[str,object]
Outputs=dict[Path,bytes]
class ExactRef(TypedDict):
 path:str
 bytes:int
 sha256:str
class PlanV1(TypedDict):
 schema:Literal["xar.Source28-A15-complete-cold-input/v1"]
 machine_id:str
 execution_owner:Literal["Root"]
 root_direct_execution_release:Literal[True]
 observed_at_utc:str
 attempt_nonce:str
 task_nonce:str
 full_storage_ref:ExactRef
 live_storage_ref:ExactRef
 predecessor_plan:ExactRef
 predecessor_quote:ExactRef
 predecessor_prepared:ExactRef
 actual_A14_closure_ref:ExactRef
 current_driver_review_ref:ExactRef
 current_next_ref:ExactRef
 steam_native_state_ref:ExactRef
 union_producer:ExactRef
 stage_producer:ExactRef
 screen_admission_path:str
class Dynamic(Protocol):
 def __call__(self,*args:object,**kwargs:object)->object:...
class Compose(Protocol):
 def __call__(self,plan:object,*,display_values:dict[str,bytes],display_review:Doc,
              companion_values:Outputs)->object:...
MACHINE="xenoamess-full-tower-eb9d2c1186"
OWN=Path(__file__).resolve().parent
P=Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O=P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
U14=P/"robert30-v20261019-campaign01/runtime-a14"
U15=U14.with_name("runtime-a15")
PREP=O/"source28-a15-prep01"
BASE14=OWN/"prepare_source28_a14_cold_union_v1.py"
BASE14_PIN=(30879,"c1040668971efc3b68f1b6fb4b98c4d07cf94128c5f47f9b305ff19791459ede")
STAGE_PIN=(57134,"e17498d4b081bdf461756497a9a2d8195d92f080475fc01aeef9e92b91f22880")
PRIOR_PLAN=(7398,"22f5458d9ab215a65c66e5f628000a74c8fb613bf1802a4bd1d470d46c19de51")
PRIOR_QUOTE=(192100,"cbf5b20b52ff47b9ea884bbe060bed69640ace5202cf3d95ff9e9809b78a4782")
PRIOR_PREPARED=(44475,"15855fda6ec457b30c92ca49167c45d2b9614158ea063079ad934db1b48f6ab2")
def need(ok:bool,why:str)->None:
 if not ok:raise ValueError("A15: "+why)
def record(value:object)->Doc:
 need(isinstance(value,dict),"JSON object")
 out:Doc={}
 for k,v in cast(dict[object,object],value).items():
  need(type(k) is str,"JSON text key");out[cast(str,k)]=v
 return out
def text(value:object)->str:
 need(type(value) is str and bool(value),"nonempty text");return cast(str,value)
def uint(value:object,maximum:int=2**63-1)->int:
 need(type(value) is int and 0<=value<=maximum,"exact unsigned integer")
 return cast(int,value)
def decimal(value:object)->str:
 s=text(value);need(re.fullmatch(r"(?:0|[1-9][0-9]*)",s) is not None,"decimal wire identity")
 return s
def ref_value(value:object)->ExactRef:
 r=record(value);need(set(r)=={"path","bytes","sha256"},"exact ref keys")
 p=text(r["path"]);n=uint(r["bytes"],2**53-1);h=text(r["sha256"])
 need(n>0 and re.fullmatch("[0-9a-f]{64}",h) is not None and Path(p).is_absolute(),"exact ref")
 return {"path":p,"bytes":n,"sha256":h}
def raw(path:Path|str,limit:int=1048576)->bytes:
 with Path(path).open("rb") as stream:b=stream.read(limit+1)
 need(0<len(b)<=limit,"bounded nonempty source");return b
def sha(value:bytes)->str:return hashlib.sha256(value).hexdigest()
def enc(value:object)->bytes:return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
def ref(path:Path|str)->ExactRef:
 p=Path(path).resolve(strict=True);b=raw(p)
 return {"path":str(p),"bytes":len(b),"sha256":sha(b)}
def future(path:Path,value:bytes)->ExactRef:
 return {"path":str(path),"bytes":len(value),"sha256":sha(value)}
def verify_exact_bytes_ref(value:object,limit:int=1048576)->bytes:
 r=ref_value(value);p=Path(r["path"]);a=p.stat();b=raw(p,limit);z=p.stat()
 need((len(b),sha(b))==(r["bytes"],r["sha256"]) and
  (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns),"exact immutable bytes")
 return b
def checked(value:object,limit:int=1048576)->Doc:return record(json.loads(verify_exact_bytes_ref(value,limit)))
def one(source:str,before:str,after:str,count:int=1)->str:
 need(source.count(before)==count,"exact seam "+before[:80]);return source.replace(before,after)
def dynamic(module:ModuleType,name:str)->Dynamic:
 v:object=getattr(module,name,None);need(callable(v),"callable "+name);return cast(Dynamic,v)
def module(value:object,name:str)->ModuleType:
 r=ref_value(value);b=verify_exact_bytes_ref(r)
 m=ModuleType(name);m.__file__=r["path"];sys.modules[name]=m
 try:exec(compile(b,r["path"],"exec"),vars(m))
 except BaseException:sys.modules.pop(name,None);raise
 return m
def outputs(value:object)->Outputs:
 need(type(value) is dict,"output map");result:Outputs={}
 for k,v in cast(dict[object,object],value).items():
  need(isinstance(k,Path) and type(v) is bytes,"Path bytes output")
  result[cast(Path,k)]=cast(bytes,v)
 return result
def strings(value:object)->list[str]:
 need(type(value) is list,"text array");out:list[str]=[]
 for item in cast(list[object],value):out.append(text(item))
 return out
def function(source:ModuleType,name:str)->str:
 p=Path(text(getattr(source,"__file__",None)));body=raw(p).decode()
 nodes=[n for n in ast.parse(body).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 need(len(nodes)==1,"one source function "+name)
 result=ast.get_source_segment(body,nodes[0]);need(isinstance(result,str),"source span")
 return cast(str,result)
def parse_plan(value:object)->PlanV1:
 p=record(value);need(set(p)==set(PlanV1.__annotations__),"single A15 plan contract")
 need(p["schema"]=="xar.Source28-A15-complete-cold-input/v1" and p["machine_id"]==MACHINE
  and p["execution_owner"]=="Root" and p["root_direct_execution_release"] is True,"Root A15 plan")
 for name in ("attempt_nonce","task_nonce"):
  need(re.fullmatch("[0-9a-f]{32}",text(p[name])) is not None,"fresh nonce")
 need(p["attempt_nonce"]!=p["task_nonce"],"independent task/attempt")
 for name in ("observed_at_utc","screen_admission_path"):text(p[name])
 for name in set(p)-{"schema","machine_id","execution_owner","root_direct_execution_release",
  "observed_at_utc","attempt_nonce","task_nonce","screen_admission_path"}:ref_value(p[name])
 # A plan crosses JSON persistence before replay; embedded Python literals use one key order.
 return cast(PlanV1,record(json.loads(enc(p))))
def _pairs(value:object)->list[list[str]]:
 need(type(value) is list,"pair array");out:list[list[str]]=[]
 for item in cast(list[object],value):
  need(type(item) is list and len(cast(list[object],item))==2,"source pair")
  a=cast(list[object],item);out.append([text(a[0]),text(a[1])])
 return out

def _prior(p:PlanV1)->tuple[Doc,Doc,Doc]:
 for name,want in (("predecessor_plan",PRIOR_PLAN),("predecessor_quote",PRIOR_QUOTE),("predecessor_prepared",PRIOR_PREPARED)):
  r=p[cast(Literal["predecessor_plan","predecessor_quote","predecessor_prepared"],name)]
  need((r["bytes"],r["sha256"])==want,"immutable actual A14 "+name)
 old=checked(p["predecessor_plan"],16384);q=checked(p["predecessor_quote"],262144);done=checked(p["predecessor_prepared"],131072)
 need(done.get("machine_id")==MACHINE and q.get("machine_id")==MACHINE,"same-machine accepted A14")
 rows=q["files"];actual=done["outputs"]
 need(type(rows) is list and type(actual) is list and len(cast(list[object],rows))==144
  and [{k:record(v)[k] for k in ("path","bytes","sha256")} for v in cast(list[object],rows)]==actual,
  "actual accepted144 exact outputs")
 return old,q,done
def _intake(p:PlanV1)->tuple[dict[str,bytes],Doc,Doc]:
 _,q,_=_prior(p);names=strings(record(q["sources"])["runtime_source_output_names"])
 need(len(names)==len(set(names))==113,"actual accepted113")
 profile=checked(ref(U14/"ROOT-OBS-PROFILE-C23.json"),16384)
 config=Path(text(profile["config_root"]));name=text(profile["profile_name"])
 mutable={config/"basic/profiles"/name/"basic.ini",config/"basic/scenes"/(name+".json")}
 known:dict[Path,bytes]={};observations:list[ExactRef]=[]
 for item in cast(list[object],q["files"]):
  r=ref_value({k:record(item)[k] for k in ("path","bytes","sha256")});path=Path(r["path"])
  if path in mutable:observations.append(ref(path));continue
  if path==U14/"NEXT-SEQUENCE-P37.json":continue
  known[path]=verify_exact_bytes_ref(r)
 need(len(known)==141 and len(observations)==2,"141 immutable+two observed OBS+NEXT")
 source={name:known[U14/name] for name in names}
 f=record(json.loads(known[U14/"ROOT-FINAL-SDK-FREEZE-P37C23-A14.json"]))
 policy=checked(f["canonical_preload_policy"],65536)
 need(len(_pairs(policy["entry_source_pins"]))==47 and len(_pairs(policy["canonical_entry_source_pins"]))==8
  and len(record(policy["external_import_source_pins"]))==26 and len(cast(list[object],policy["runtime_import_source_pins"]))==23,"accepted47/8/26/23")
 for entry_path,digest in _pairs(policy["entry_source_pins"]):
  need(sha(known[Path(entry_path)])==digest,"accepted entry SHA")
 return source,q,policy
def _closed(p:PlanV1)->Doc:
 x=checked(p["actual_A14_closure_ref"],65536)
 need(x["machine_id"]==MACHINE and Path(p["actual_A14_closure_ref"]["path"]).parent==U14,"actual A14 closure")
 need(x["schema"]=="xar.C23-A14-local-full-preflight-failure-closed/v1"
  and x["status"]=="A14_CLOSED_LOCAL_FULL10540_ZERO_GAME_RPC" and x["SDK_pair_published"] is True
  and x["SDK_dual_zero"] is False and x["SDK_normal"] is False and x["Task_absent"] is True
  and x["screen_released"] is True and x["failed_FULL_replayed"] is False and x["unknown_AUTO10534_replayed"] is False,
  "actual abnormal closed A14, no replay")
 exits=record(x["SDK_actual_exits"]);g=record(x["Game"])
 need(set(exits)=={"sdk_queue","sdk_application"} and uint(exits["sdk_queue"])==1
  and uint(exits["sdk_application"])==0 and uint(g["exit_code"])==1
  and g["forced_owned_job_cleanup"] is True and uint(g["Job_active_final"])==0
  and uint(x["failed_FULL"])==10540 and uint(x["failed_FULL_Game_RPC_rows"])==0
  and uint(x["next_sequence"])==10541 and uint(x["completed_cycles"])==4753 and uint(x["saved_game_days"])==5429
  and uint(x["new_game_day_credit"])==uint(x["new_ordinary_cycle_credit"])==0,"closed 1/0, forced1/Job0, saved4753")
 facts=record(x["source_refs"]);need(len(facts)==35,"all35 facts")
 for r in facts.values():verify_exact_bytes_ref(r,131072)
 current=checked(p["current_next_ref"],16384)
 need(type(current.get("next_sequence")) is int and current["next_sequence"]==10541
  and p["current_next_ref"]==facts["NEXT-SEQUENCE-P37.json"],"10540 retained, actual next10541")
 return x
def _current_pre(p:PlanV1)->tuple[Doc,bytes]:
 old,_,_=_prior(p);pre=checked(old["cold_prelaunch_ref"],32768)
 r=checked(p["current_driver_review_ref"],16384)
 need(r["schema"]=="xar.C23-A14-current-Driver-SAVE-review/v1" and r["machine_id"]==MACHINE
  and r["Driver_changed_since_A13"] is True and r["SAVE_unchanged_since_A13"] is True
  and uint(r["copies_created"])==uint(r["new_business_credit"])==0 and record(r["wal"])["exists"] is False,
  "honest changed Driver, same SAVE, no WAL")
 rows=cast(list[object],r["sources"]);need(len(rows)==2,"actual Driver SAVE pair")
 first=record(rows[0]);d=ref_value(first["ref"]);ident=record(first["identity"]);s=Path(d["path"]).stat()
 need(first["identity_schema"]=="xar.file-stat-identity.os-ns-decimal.v1" and first["stable_before_after"] is True
  and (s.st_size,str(s.st_ino),str(s.st_mtime_ns))==(uint(ident["bytes"]),decimal(ident["file_id"]),decimal(ident["mtime_ns"])),
  "current canonical Driver identity")
 payload=record(json.loads(verify_exact_bytes_ref(d,41943040)))
 need(uint(payload["format_version"])==2 and len(cast(list[object],payload["command_history"]))==5272
  and payload["last_checkpoint"]==pre["checkpoint"],"actual full-v2 Driver and saved checkpoint")
 base=checked(old["compact_base_ref"],524288);root=Path(text(base["source_root"]));sys.path.insert(0,str(root))
 api=importlib.import_module("xar_autoplayer.cold_checkpoint_validator")
 origin=Path(text(getattr(api,"__file__",None))).resolve()
 need(origin==root/"xar_autoplayer/cold_checkpoint_validator.py","canonical validator import")
 entries=cast(list[object],base["files"]);found=[{"path":str(root/text(record(v)["relative"])),"bytes":uint(record(v)["bytes"]),"sha256":text(record(v)["sha256"])} for v in entries if (root/text(record(v)["relative"])).resolve()==origin]
 need(len(found)==1,"validator actual BASE pin");verify_exact_bytes_ref(found[0],1048576)
 manifest=checked(r["environment_manifest"],32768)
 validation=record(dynamic(api,"validate_cold_start_checkpoint_payload_for_pipe")(
  SimpleNamespace(profile_dir=Path(text(manifest["profile_dir"]))),text(payload["pipe_name"]),payload))
 need(validation==pre["validation"],"same canonical SAVE10480 cold semantics")
 refs:list[ExactRef]=[]
 for item in cast(list[object],pre["sidecars"]):
  oldref=ref_value(item);rr=ref(oldref["path"]);body=checked(rr,65536)
  need(body.get("pending") is None,"no current pending sidecar");refs.append(rr)
 need(len(refs)==4,"four current sidecars")
 current=copy.deepcopy(pre)
 current.update(driver_state=d,materialized_driver_review=p["current_driver_review_ref"],
  validation=validation,sidecars=refs,actual_A14_closure=p["actual_A14_closure_ref"])
 return current,enc(current)
def _frontier_source(stage:ModuleType,source:str,next_ref:ExactRef)->str:
 fn:object=getattr(stage,"derive_current_frontier_metadata_v1")
 need(isinstance(fn,types.FunctionType),"qualified frontier function")
 rebound=types.FunctionType(cast(types.FunctionType,fn).__code__,
  dict(cast(types.FunctionType,fn).__globals__,ACCEPTED_ROOT=U14))
 value:object=rebound(source,next_ref);return text(value)
def _carry(policy_value:object,out_value:object,source_value:object,dv_value:object,dr_value:object,
 source_review_value:object,target_value:object,*unused:object)->object:
 policy=record(policy_value);out=outputs(out_value)
 need(isinstance(source_value,dict) and isinstance(dv_value,dict) and target_value==U15,"carry namespace")
 source:dict[str,bytes]={}
 for k,v in cast(dict[object,object],source_value).items():
  need(type(k) is str and type(v) is bytes,"carried source bytes");source[cast(str,k)]=cast(bytes,v)
 dv:dict[str,bytes]={}
 for k,v in cast(dict[object,object],dv_value).items():
  need(type(k) is str and type(v) is bytes,"display source bytes");dv[cast(str,k)]=cast(bytes,v)
 dr=record(dr_value);review=record(source_review_value)
 prior_policy=record(review["accepted_policy"])
 entries=_pairs(prior_policy["entry_source_pins"]);canonical={Path(r[0]).name for r in _pairs(prior_policy["canonical_entry_source_pins"])}
 external=record(prior_policy["external_import_source_pins"])
 outer_name="root_c23_canonical_outer.py";body=source[outer_name].decode()
 nodes=[n for n in ast.parse(body).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="_C23_EXTERNAL_IMPORT_PINS"]
 need(len(nodes)==1,"one external map");oldmap=record(ast.literal_eval(nodes[0].value))
 need(set(oldmap)==set(external) and len(oldmap)==26,"original external26 names")
 newmap={stem:sha(source[stem+".py"]) for stem in oldmap}
 segment=ast.get_source_segment(body,nodes[0]);need(isinstance(segment,str),"external source segment")
 source[outer_name]=one(body,cast(str,segment),"_C23_EXTERNAL_IMPORT_PINS="+repr(newmap)).encode()
 # The caller's output dictionary is intentionally updated before the first seal.
 actual_out=cast(Outputs,out_value);actual_source=cast(dict[str,bytes],source_value)
 actual_source[outer_name]=source[outer_name];actual_out[U15/outer_name]=source[outer_name]
 complete=[[str(U15/Path(path).relative_to(U14)),sha(source[Path(path).relative_to(U14).as_posix()])] for path,_ in entries]
 eight=[r for r in complete if Path(r[0]).name in canonical]
 need(len(complete)==47 and len(eight)==8 and len(dv)==19,"carry47/8/19")
 imports=[future(U15/Path(ref_value(item)["path"]).relative_to(U14),source[Path(ref_value(item)["path"]).relative_to(U14).as_posix()]) for item in cast(list[object],prior_policy["runtime_import_source_pins"])]
 policy.update(entry_source_pins=complete,canonical_entry_source_pins=eight,
  external_import_source_pins={stem:future(U15/(stem+".py"),source[stem+".py"]) for stem in external},
  runtime_import_source_pins=imports)
 need(len(imports)==23,"original full import23")
 dr.update(root_source_count=47,canonical_source_count=8,external_source_count=26,runtime_import_count=23,
  final_complete_count=47,final_canonical_count=8,final_external_count=26,
  root_files=[dict(future(U15/Path(path).relative_to(U14),source[Path(path).relative_to(U14).as_posix()]),
   relative_path=Path(path).relative_to(U14).as_posix()) for path,_ in entries],runtime_or_Game_credit=False)
 review["A15_carry"]={"complete":47,"canonical":8,"external":26,"runtime_import":23,"display":19,"rich_delta_reapplied":False}
 cast(Doc,source_review_value).update(review)
 return policy,eight,complete,dv,dr

def _runtime_bridge(p:PlanV1,pre:Doc)->str:
 old,_,_=_prior(p)
 constants={"A15_CLOSED_REF":p["actual_A14_closure_ref"],"A15_REVIEW_REF":p["current_driver_review_ref"],
  "A15_HISTORICAL_PRE":old["cold_prelaunch_ref"],"A15_CURRENT_PRE":pre}
 header="\n".join(k+"="+repr(v) for k,v in constants.items())+"\n"
 return header+"""
from typing import Callable as _A15Callable,cast as _A15cast
def validate_actual_a14_index_v1(reference:object,checked:_A15Callable[[object,int],dict[str,object]])->dict[str,object]:
    require(reference==A15_CLOSED_REF,'actual A14 closed authority')
    x=checked(reference,65536)
    require(x['schema']=='xar.C23-A14-local-full-preflight-failure-closed/v1'
        and x['machine_id']==MACHINE and x['SDK_dual_zero'] is False and x['SDK_normal'] is False
        and x['Task_absent'] is True and x['screen_released'] is True,'actual abnormal closed A14')
    exits=x['SDK_actual_exits'];require(type(exits) is dict,'closed SDK pair')
    e=_A15cast(dict[str,object],exits)
    require(type(e['sdk_queue']) is type(e['sdk_application']) is int
        and e['sdk_queue']==1 and e['sdk_application']==0
        and type(x['failed_FULL']) is type(x['failed_FULL_Game_RPC_rows']) is int
        and x['failed_FULL']==10540 and x['failed_FULL_Game_RPC_rows']==0
        and x['failed_FULL_replayed'] is False and x['unknown_AUTO10534_replayed'] is False
        and type(x['next_sequence']) is int and x['next_sequence']==10541,'retained zero-RPC failed10540')
    facts=x['source_refs'];require(type(facts) is dict,'closed facts')
    for item in _A15cast(dict[str,object],facts).values():_a14_verify_exact_fact(item)
    return x
_A15_PRIOR_POST=validate_post_sem_driver
_A15_PRIOR_VIEW=historical_saved_basis_view
_A15_PRIOR_SEED=validate_saved_seed_a10
def validate_post_sem_driver(pre:dict[str,object],close:dict[str,object],checked:_A15Callable[[object,int],dict[str,object]],verify_current_stat:bool=True)->bool:
    if pre.get('actual_A14_closure')!=A15_CLOSED_REF:
        return bool(_A15_PRIOR_POST(pre,close,checked,verify_current_stat))
    validate_actual_a14_index_v1(A15_CLOSED_REF,checked)
    historic=checked(A15_HISTORICAL_PRE,32768)
    _A15_PRIOR_POST(historic,close,checked,False)
    r=checked(A15_REVIEW_REF,16384)
    require(r['schema']=='xar.C23-A14-current-Driver-SAVE-review/v1'
        and r['machine_id']==MACHINE and r['Driver_changed_since_A13'] is True
        and r['SAVE_unchanged_since_A13'] is True
        and pre==A15_CURRENT_PRE,'exact current A15 cold basis')
    if verify_current_stat:
        rows=_A15cast(list[object],r['sources']);row=_A15cast(dict[str,object],rows[0])
        identity=_A15cast(dict[str,object],row['identity']);driver=_A15cast(dict[str,object],pre['driver_state'])
        s=Path(_A15cast(str,driver['path'])).stat()
        require((s.st_size,str(s.st_ino),str(s.st_mtime_ns))==
            (identity['bytes'],identity['file_id'],identity['mtime_ns']),'current A15 Driver OS stat')
        for sidecar in _A15cast(list[object],pre['sidecars']):
            require(checked(sidecar,65536).get('pending') is None,'current sidecar pending')
    return True
def historical_saved_basis_view(admission:dict[str,object])->dict[str,object]:
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10541,
        'current10541 distinct from historical10538/10481')
    return _A15_PRIOR_VIEW({**admission,'next_sequence':10538})
def validate_saved_seed_a10(admission:dict[str,object],seed:dict[str,object],original:dict[str,object],
    save:dict[str,object],semantic:dict[str,object],governance:dict[str,object],*,
    checked:_A15Callable[[object,int],dict[str,object]],projector:object=None)->bool:
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10541,
        'actual A15 opening sequence')
    return bool(_A15_PRIOR_SEED({**admission,'next_sequence':10538},seed,original,
        save,semantic,governance,checked=checked,projector=projector))
"""
def _build_sources(p:PlanV1,pre:Doc)->tuple[dict[str,bytes],Doc]:
 source,q,policy=_intake(p);old,_,_=_prior(p)
 for name,b in tuple(source.items()):
  source[name]=b.replace(b"C23-A14",b"C23-A15")
 boot=source["root_checkpoint_bootstrap_c23.py"].decode()
 boot=one(boot,"if __name__ == '__main__':",_runtime_bridge(p,pre)+"\nif __name__ == '__main__':")
 source["root_checkpoint_bootstrap_c23.py"]=boot.encode()
 body=source["root_native30_supervisor_c23.py"].decode()
 for a,z,n in (("args.attempt=='a14'","args.attempt=='a15'",1),
  ("value.get('attempt_id')=='a14'","value.get('attempt_id')=='a15'",1),
  ('choices=("a14",)','choices=("a15",)',1),('"attempt_id":"a14"','"attempt_id":"a15"',2),
  ("    _validate_a14_attempt(args, config)","    _validate_a15_attempt(args, config)",1)):
  body=one(body,a,z,n)
 # The supervisor needs only the closed-index guard, not the Driver/history function aliases.
 bridge=_runtime_bridge(p,pre);begin=bridge.index("from typing import");end=bridge.index("_A15_PRIOR_POST")
 closure=bridge[:begin]+bridge[begin:end]
 extra=closure+"""
def _validate_a15_attempt(args,config):
    value=_validate_a14_attempt(args,config)
    closed=validate_actual_a14_index_v1(value['prior_failure_a14'],_a03_checked)
    old={closed[k] for k in ('actual_supervisor_bootstrap_task_nonce',
        'metadata_supervisor_task_nonce','actual_display_task_nonce','actual_feeder_task_nonce')}
    require(args.attempt_nonce not in old and args.task_nonce not in old,'new A15 nonces')
    return value
"""
 body=one(body,"def main(args):",extra+"\ndef main(args):")
 source["root_native30_supervisor_c23.py"]=body.encode()
 source["launch_a10_saved10480_feeder01.py"]=patch_feeder_v1(source["launch_a10_saved10480_feeder01.py"],p)
 for name,b in source.items():
  if name.endswith(".py"):compile(b,name,"exec")
 old_review=record(q["sources"])
 review={"schema":"xar.A15-accepted-source-carry/v1","machine_id":MACHINE,"feeder":{},
  "runtime_source_output_names":sorted(source),"actual_source_rows":[ref(U14/name) for name in sorted(source)],
  "supplemental_import_rows":old_review["supplemental_import_rows"],"staging_files":old_review["staging_files"],
  "actual_A14_index":p["actual_A14_closure_ref"],"new_day_credit":0,"accepted_policy":policy}
 return source,review
def _factory(p:PlanV1,pre:Doc,pre_raw:bytes)->tuple[ModuleType,Doc]:
 prior=module({"path":str(BASE14),"bytes":BASE14_PIN[0],"sha256":BASE14_PIN[1]},"_a15_pinned_a14")
 need((p["stage_producer"]["bytes"],p["stage_producer"]["sha256"])==STAGE_PIN,"pinned A14 qualified delta")
 stage=module(p["stage_producer"],"_a15_carry_stage")
 old,_,_=_prior(p);need(p["stage_producer"]==old["stage_producer"],"same qualified stage")
 projected=copy.deepcopy(old)
 projected.update(schema="xar.Source28-A15-complete-cold-input/v1",observed_at_utc=p["observed_at_utc"],
  attempt_nonce=p["attempt_nonce"],task_nonce=p["task_nonce"],full_storage_ref=p["full_storage_ref"],
  live_storage_ref=p["live_storage_ref"],union_producer=p["union_producer"],screen_admission_path=p["screen_admission_path"],
  steam_native_state_ref=p["steam_native_state_ref"],cold_prelaunch_ref=future(U15/"ROOT-C23-COLD-PRELAUNCH.json",pre_raw))
 original_derive=dynamic(stage,"derive_owner_compose_v1")
 def derive(value:object)->str:
  s=text(original_derive(value))
  s=one(s,"len(replaced)==44","len(replaced)==47")
  s=one(s,"len({x for x,h in replaced})==44","len({x for x,h in replaced})==47")
  s=one(s,"len(six)==6","len(six)==8")
  return one(s,"len(display_values)==18","len(display_values)==19")
 setattr(stage,"derive_owner_compose_v1",derive);setattr(stage,"apply_a14_policy_stage_v1",_carry)
 original_module=dynamic(prior,"module")
 def load(value:object,name:object)->ModuleType:
  if ref_value(value)==p["stage_producer"]:return stage
  v=original_module(value,name);need(isinstance(v,ModuleType),"loaded module");return cast(ModuleType,v)
 def raw_value(path:object,limit:object=1048576)->bytes:
  if Path(text(str(path))).resolve()==(U15/"ROOT-C23-COLD-PRELAUNCH.json").resolve():return pre_raw
  return raw(Path(text(str(path))),uint(limit))
 a05=importlib.import_module("prepare_c23_a05_union_v1")
 original_obj:object=getattr(a05,"original");need(isinstance(original_obj,ModuleType),"original module")
 original=ModuleType("_a15_original");vars(original).update(vars(cast(ModuleType,original_obj)))
 controls_obj:object=getattr(original,"controls");need(isinstance(controls_obj,ModuleType),"controls")
 controls=SimpleNamespace(**vars(cast(ModuleType,controls_obj)))
 _,_,old_policy=_intake(p);controls.SIX=tuple(Path(r[0]).name for r in _pairs(old_policy["canonical_entry_source_pins"]))
 setattr(original,"controls",controls)
 a05_copy=ModuleType("_a15_a05");vars(a05_copy).update(vars(a05));setattr(a05_copy,"original",original)
 def import_module(name:str)->ModuleType:
  return a05_copy if name=="prepare_c23_a05_union_v1" else importlib.import_module(name)
 namespace:Doc=dict(vars(prior));namespace.update(importlib=SimpleNamespace(import_module=import_module),__file__=__file__,U13=U14,U14=U15,module=load,raw=raw_value,
  parse_plan=lambda unused:projected,build_sources=lambda unused,unused_stage:_build_sources(p,pre),
  state_guard=lambda unused:{"machine_id":MACHINE,"actual_A14_index":p["actual_A14_closure_ref"],
   "current_driver_review":p["current_driver_review_ref"],"additional_rollback_cycles":0,"additional_rollback_days":0},
  A15_CURRENT_CLOSED_REF=p["actual_A14_closure_ref"])
 source=function(prior,"compose").replace("C23-A14","C23-A15").replace("Source28-A14","Source28-A15")
 source=source.replace("spec-supervisor-a14","spec-supervisor-a15").replace("'a14'","'a15'")
 source=one(source,'.replace("C23-A04","C23-A13")','.replace("C23-A04","C23-A14")')
 source=one(source,'U13/"ROOT-NATIVE30-NATIVE-PIN-C23-A13.json"','U13/"ROOT-NATIVE30-NATIVE-PIN-C23-A14.json"')
 source=one(source,"T4/'ROOT-NATIVE30-NATIVE-PIN-C23-A13.json'","T4/'ROOT-NATIVE30-NATIVE-PIN-C23-A14.json'")
 source=one(source,"CONTROL_SEQUENCE=10540","CONTROL_SEQUENCE=10543")
 source=one(source,"new_first_sequence=10538","new_first_sequence=10541")
 source=one(source,'U13/"ROOT-LAUNCH-CONFIG-C23-A13.json"','U13/"ROOT-LAUNCH-CONFIG-C23-A14.json"')
 source=one(source,'prior_failures["prior_failure_a13"]=plan["actual_A13_closure_ref"]',
  'prior_failures["prior_failure_a13"]=plan["actual_A13_closure_ref"]\n    prior_failures["prior_failure_a14"]=A15_CURRENT_CLOSED_REF')
 source=one(source,'"--attempt","a14"','"--attempt","a15"')
 exec(compile(source,"A15-accepted-cold-compose","exec"),namespace)
 made=ModuleType("_a15_finite_factory");vars(made).update(namespace)
 return made,projected
def compose(plan_value:object,*,display_values:dict[str,bytes],display_review:Doc,
 companion_values:Outputs)->tuple[Outputs,Doc]:
 p=parse_plan(plan_value);_closed(p);pre,pre_raw=_current_pre(p)
 need(not U15.exists() and ref(__file__)==p["union_producer"],"exact absent target and source")
 factory,projected=_factory(p,pre,pre_raw)
 value=dynamic(factory,"compose")(projected,display_values=display_values,display_review=display_review,companion_values=companion_values)
 need(type(value) is tuple and len(cast(tuple[object,...],value))==2,"compose tuple")
 pair=cast(tuple[object,object],value);out=outputs(pair[0]);quote=record(pair[1])
 nxt=verify_exact_bytes_ref(p["current_next_ref"],16384);out[U15/"NEXT-SEQUENCE-P37.json"]=nxt
 rows=cast(list[object],quote["files"])
 for item in rows:
  row=record(item);path=Path(text(row["path"]));b=out[path]
  row.update(bytes=len(b),sha256=sha(b))
  if path==U15/"NEXT-SEQUENCE-P37.json":
   row.update(mode="hardlink",source=p["current_next_ref"],allocation_upper=0)
  cast(dict[str,object],item).update(row)
 quote.update(schema="xar.Source28-A15-complete-cold-quote/v1",actual_A14_index=p["actual_A14_closure_ref"],
  current_driver_review=p["current_driver_review_ref"],new_first_sequence=10541,rollback_cycles=0,rollback_days=0,
  unknown10540_credit=0,original_wall_origin_reset=False,
  campaign_score_junction={"path":str(U15/"campaign-score"),"exact_target":str(P/"robert30-v20261019-campaign01/runtime/campaign-score"),"must_verify_same_FileID":True})
 quote["prerequisite_directories"]=strings(quote["prerequisite_directories"])+[str(U15/"campaign-score")]
 quote.update(logical_bytes=sum(map(len,out.values())),
  fresh_allocation_upper=sum(uint(record(r)["allocation_upper"]) for r in rows),
  immutable_hardlinks=sum(record(r)["mode"]=="hardlink" for r in rows),
  max_atomic_copy=max(((len(b)+4095)//4096)*4096 for b in out.values()),all_entry_rows=47)
 quote["prepare_peak_upper"]=sum(uint(quote[k]) for k in ("fresh_allocation_upper",
  "max_atomic_copy","future_owner_metadata_upper","control_probe_atomic_peak","intent_receipt_and_FS_upper"))
 need(len(out)==uint(quote["unique_files"])==144,"A15 complete144")
 return out,quote

def metadata_source(plan_value:object,source:str)->str:
 p=parse_plan(plan_value)
 a13=importlib.import_module("prepare_source28_a13_union_v1")
 stage=module(p["stage_producer"],"_a15_metadata_stage")
 value=text(dynamic(a13,"metadata_source")(source))
 value=_frontier_source(stage,value,p["current_next_ref"])
 return text(dynamic(stage,"derive_cold_owner_v1")(value))
def metadata_scope(plan_value:object,namespace:Doc,runtime:Path)->None:
 p=parse_plan(plan_value);need(runtime.resolve()==U15.resolve(),"A15 metadata runtime")
 a13=importlib.import_module("prepare_source28_a13_union_v1")
 dynamic(a13,"metadata_scope")(namespace,runtime)
 prior=module({"path":str(BASE14),"bytes":BASE14_PIN[0],"sha256":BASE14_PIN[1]},"_a15_recording_loader")
 stage=module(p["stage_producer"],"_a15_recording_stage")
 identity=text(getattr(stage,"RECORDING_IDENTITY14",None))
 dynamic(prior,"patch_recording_metadata_loader_v1")(namespace,runtime,identity)
def cold_owner(inputs_value:object)->tuple[Outputs,Doc]:
 inputs=record(inputs_value)
 need(inputs.get("schema")=="xar.C23-A15-cold-owner-metadata-input/v1"
  and inputs.get("machine_id")==MACHINE,"single A15 metadata contract")
 p=parse_plan(checked(inputs["cold_graph_plan"],16384))
 a08=importlib.import_module("prepare_c23_a08_union_v1")
 source=function(a08,"cold_owner").replace("A08","A15").replace("a08","a15")
 def bind_scope(value:object,runtime:object)->None:
  record(value);need(type(value) is dict and isinstance(runtime,Path),"actual mutable metadata globals")
  metadata_scope(p,cast(Doc,value),cast(Path,runtime))
 namespace:Doc=dict(vars(a08));namespace.update(U8=U15,T5=U15,
  metadata_source=lambda value:metadata_source(p,text(value)),metadata_scope=bind_scope)
 exec(compile(source,"A15-existing-cold-owner","exec"),namespace)
 value:object=namespace["cold_owner"];need(callable(value),"cold owner callable")
 result=cast(Dynamic,value)({k:v for k,v in inputs.items() if k!="cold_graph_plan"})
 need(type(result) is tuple and len(cast(tuple[object,...],result))==2,"metadata tuple")
 pair=cast(tuple[object,object],result);return outputs(pair[0]),record(pair[1])

CAMPAIGN_MAP_HELPER15="class CampaignMapFrameV1(TypedDict):\n snapshot_id:str\n revision:int\n native_revision:int\n date_raw:int\n actor_character_id:int\n episode_run_id:str\nclass CampaignMapAdmissionV1(TypedDict):\n machine_id:str\n status:Literal[\"GREEN\"]\n reviewer:Literal[\"/root\"]\n game_pid:int\n game_creation_filetime:int\n Game_map_visible:Literal[True]\n decision_text_visible:Literal[True]\n recording_session_id:str\n actual_initial_frame:CampaignMapFrameV1\n\ndef _campaign_map_record_v1(value:object)->Json:\n if not isinstance(value,dict):raise ValueError(\"campaign map object required\")\n result:Json={}\n for key,item in value.items():\n  if type(key) is not str:raise ValueError(\"campaign map text key required\")\n  result[key]=item\n return result\n\ndef _campaign_map_int_v1(value:object,maximum:int)->int:\n if type(value) is not int or not 0<value<maximum:\n  raise ValueError(\"campaign map exact positive integer required\")\n return value\n\ndef _campaign_map_text_v1(value:object)->str:\n if type(value) is not str or not value:\n  raise ValueError(\"campaign map nonempty text required\")\n return value\n\ndef _campaign_map_frame_v1(value:object)->CampaignMapFrameV1:\n row=_campaign_map_record_v1(value)\n need(set(row)=={\"snapshot_id\",\"revision\",\"native_revision\",\"date_raw\",\n  \"actor_character_id\",\"episode_run_id\"},\"campaign map frame fields\")\n return {\"snapshot_id\":_campaign_map_text_v1(row[\"snapshot_id\"]),\n  \"revision\":_campaign_map_int_v1(row[\"revision\"],2**64),\n  \"native_revision\":_campaign_map_int_v1(row[\"native_revision\"],2**64),\n  \"date_raw\":_campaign_map_int_v1(row[\"date_raw\"],2**64),\n  \"actor_character_id\":_campaign_map_int_v1(row[\"actor_character_id\"],2**64),\n  \"episode_run_id\":_campaign_map_text_v1(row[\"episode_run_id\"])}\n\ndef parse_campaign_map_admission_v1(value:object)->CampaignMapAdmissionV1:\n row=_campaign_map_record_v1(value)\n need(row.get(\"status\")==\"GREEN\" and row.get(\"reviewer\")==\"/root\"\n  and row.get(\"machine_id\")==MACHINE\n  and row.get(\"Game_map_visible\") is True\n  and row.get(\"decision_text_visible\") is True,\"campaign map actual Root review\")\n return {\"machine_id\":MACHINE,\"status\":\"GREEN\",\"reviewer\":\"/root\",\n  \"game_pid\":_campaign_map_int_v1(row.get(\"game_pid\"),2**32),\n  \"game_creation_filetime\":_campaign_map_int_v1(row.get(\"game_creation_filetime\"),2**64),\n  \"Game_map_visible\":True,\"decision_text_visible\":True,\n  \"recording_session_id\":_campaign_map_text_v1(row.get(\"recording_session_id\")),\n  \"actual_initial_frame\":_campaign_map_frame_v1(row.get(\"actual_initial_frame\"))}\n\ndef validate_campaign_map_admission_v1(\n map_ref:Ref,current:object,game:object,opening:object,binding:object)->None:\n path=Path(file_ref(map_ref)[\"path\"])\n need(path.name==\"ROOT-CAMPAIGN-MAP-ADMITTED-C23.json\"\n  and path.resolve()==(N/\"ROOT-CAMPAIGN-MAP-ADMITTED-C23.json\").resolve(),\n  \"canonical campaign map path\")\n admitted=parse_campaign_map_admission_v1(current)\n launch=_campaign_map_record_v1(game);record=_campaign_map_record_v1(binding)\n pid=_campaign_map_int_v1(launch.get(\"pid\"),2**32)\n birth=_campaign_map_int_v1(launch.get(\"creation_filetime\"),2**64)\n need(_campaign_map_int_v1(record.get(\"Game_pid\"),2**32)==pid\n  and _campaign_map_int_v1(record.get(\"Game_creation_filetime\"),2**64)==birth\n  and admitted[\"game_pid\"]==pid and admitted[\"game_creation_filetime\"]==birth\n  and admitted[\"recording_session_id\"]==_campaign_map_text_v1(record.get(\"session_id\"))\n  and admitted[\"actual_initial_frame\"]==_campaign_map_frame_v1(opening),\n  \"campaign map Game/recording/opening binding\")\n\n"
def patch_feeder_v1(source:bytes,p:PlanV1)->bytes:
 need((len(source),sha(source))==(17023,"d525404bec96675a5c3b85e0b022f8b540c17e9cf43ba1869adb5bff1bc657e5"),
  "actual immutable A14 feeder preimage")
 body=source.decode();closed=_closed(p);facts=record(closed["source_refs"])
 basis="""def old_basis(a:Admit)->Json:
 r=a["sources"]["old_ledger"]
 need(r==A15_LEDGER_REF and Path(r["path"]).resolve()!=LEDGER.resolve(),"immutable actual A14 ledger")
 old=checked(r);state=checked(a["sources"]["old_state"])
 need(a["sources"]["old_state"]==A15_STATE_REF and integer(old.get("window_id"))==2
  and old.get("status")=="repair_required" and integer(old.get("last_settled_cycles"))==4753
  and integer(old.get("last_settled_date_raw"))==53274624
  and integer(state.get("completed_cycles"))==4753 and obj(state.get("before")).get("date_raw")==53274624
  and all(state.get(k) is None for k in ("pending_cycle","pending_checkpoint","terminal",
   "pending_natural_succession","pending_unsafe_route_halt")),"clean4753 actual A14 basis")
 need(a["prior_A14_index"]==A15_CLOSURE_REF,"exact prior A14 closure")
 bootstrap=cast(Bootstrap,importlib.import_module("root_checkpoint_bootstrap_c23"))
 bootstrap.validate_actual_a14_index_v1(a["prior_A14_index"],checked)
 proof=checked(a["prior_A14_index"]);refs=obj(proof["source_refs"])
 need(proof["continuity_ledger"]==r and refs["p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json"]==a["sources"]["old_state"],
  "actual closed ledger/state relationship")
 failed=checked(file_ref(refs["p37-responses/10540-1-result.json"]));rpc=obj(failed.get("full_rpc_rows_v1"))
 need(failed.get("request")=={"sequence":10540,"command":"full_loop","arguments":{"max_turns":30}}
  and failed.get("original_response") is None and failed.get("replay_allowed") is False
  and integer(rpc.get("row_count"))==0 and all(integer(obj(v).get("count"))==0 for v in obj(rpc.get("tools")).values()),
  "failed10540 had no Game RPC and is never replayed")
 used={text(proof[k]) for k in ("actual_supervisor_bootstrap_task_nonce",
  "metadata_supervisor_task_nonce","actual_display_task_nonce","actual_feeder_task_nonce")}
 need(a["feeder_task_nonce"] not in used,"fresh A15 feeder nonce")
 return old
"""
 tree=ast.parse(body);n=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="old_basis")
 segment=ast.get_source_segment(body,n);need(isinstance(segment,str),"one old_basis source")
 body=one(body,cast(str,segment),basis.rstrip())
 body=one(body,"from typing import Callable,Protocol,TypedDict,cast","from typing import Callable,Literal,Protocol,TypedDict,cast")
 body=one(body,"def admitted(base:Feeder,sequence:int)->Json:",CAMPAIGN_MAP_HELPER15+"def admitted(base:Feeder,sequence:int)->Json:")
 body=one(body,' binding=obj(recording.get("binding"),"recording")\n',
  ' binding=obj(recording.get("binding"),"recording")\n validate_campaign_map_admission_v1(a["sources"]["map_admission"],current,game,opening,binding)\n')
 body=one(body," def validate_actual_a09_index_v1(self,r:Ref,checked:Callable[[Ref,int],Json])->object:...",
  " def validate_actual_a09_index_v1(self,r:Ref,checked:Callable[[Ref,int],Json])->object:...\n def validate_actual_a14_index_v1(self,r:Ref,checked:Callable[[Ref,int],Json])->object:...")
 body=one(body,"prior_A11_index:Ref;budget:Ref","prior_A11_index:Ref;prior_A14_index:Ref;budget:Ref")
 body=one(body,'"prior_A11_index","budget"','"prior_A11_index","prior_A14_index","budget"')
 body=one(body,'"prior_A09_index":a["sources"]["prior_A09_index"],',
  '"prior_A09_index":a["sources"]["prior_A09_index"],"prior_A14_index":a["prior_A14_index"],')
 body=body.replace("A12_LEDGER_REF","A15_LEDGER_REF").replace("A12_STATE_REF","A15_STATE_REF")
 changes={"KIND":"A15_SAVE10480_A14_zero_rpc_handoff_verified",
  "ROLLBACK":{"saved_cycles":4753,"A14_settled_cycles":4753,"cycles_lost":0,"settled_days_lost":0,
   "failed_FULL":10540,"failed_FULL_Game_RPC_rows":0,"unknown_AUTO":10534,"unknown_AUTO_credit":0},
  "A15_LEDGER_REF":closed["continuity_ledger"],
  "A15_STATE_REF":facts["p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json"]}
 for name,value in changes.items():
  nodes=[n for n in ast.parse(body).body if isinstance(n,ast.Assign) and len(n.targets)==1
   and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name]
  need(len(nodes)==1,"one typed feeder constant "+name)
  segment=ast.get_source_segment(body,nodes[0]);need(isinstance(segment,str),"literal assignment")
  body=one(body,cast(str,segment),name+"="+repr(value))
 body=one(body,"last_A12_SAVE10480_Source28_rollback","last_A15_SAVE10480_A14_zero_rpc_handoff")
 body="A15_CLOSURE_REF="+repr(p["actual_A14_closure_ref"])+"\n"+body
 compile(body,"A15-typed-feeder","exec");return body.encode()
