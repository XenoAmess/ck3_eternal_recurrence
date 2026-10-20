"""Source29 A17 cold continuation. Preparation only; Root owns all runtime writes."""
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
 schema:Literal["xar.Source29-A17-complete-cold-input/v1"]
 machine_id:str
 execution_owner:Literal["Root"]
 root_direct_execution_release:Literal[True]
 observed_at_utc:str
 attempt_nonce:str
 task_nonce:str
 full_storage_ref:ExactRef
 live_storage_ref:ExactRef
 steam_native_state_ref:ExactRef
 union_producer:ExactRef
 stage_producer:ExactRef
 sdk_base_ref:ExactRef
 canonical_anchor_ref:ExactRef
 native_binding_ref:ExactRef
 closure_ref:ExactRef
 current_driver_review_ref:ExactRef
 ledger_ref:ExactRef
 current_next_ref:ExactRef
 screen_admission_path:str
class Dynamic(Protocol):
 def __call__(self,*args:object,**kwargs:object)->object:...
MACHINE="xenoamess-full-tower-eb9d2c1186"
OWN=Path(__file__).resolve().parent
P=Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O=P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
PREVIOUS=P/"robert30-v20261019-campaign01/runtime-a15-retry02"
TARGET=PREVIOUS.with_name("runtime-a17")
PREP=O/"source29-a17-prep01"
SCREEN=TARGET/"ROOT-SCREEN-ADMISSION-C23-A15.json"
BASE_PATH=OWN/"prepare_source28_a16_cold_union_v1.py"
BASE_PIN=(15475,"a2ec1328771f5f25f827094e980d0b6b142b77f7e2af0dc11d50f112deba6598")
PRIOR_PREP=O/"source28-a15-retry02-prep01"
PLAN_PIN=(3644,"6ec4472ebf08faa91af46a6461f875c6ab00aa504d4f0a8fc58e6e239f579233")
QUOTE_PIN=(180070,"27daaa7d710f5db92c3ffcfab1279af7ff279ae1897cb8a0de069fcd6f83bd17")
CLOSURE_PIN=(14825,"a85b5098e7961828d50955c5b4d596d4202a13be37b0ec22cbb172f9c3bb4deb")
REVIEW_PIN=(4667,"6c9b769224e282ec6b86fa766c366fb0c231a35d777ba2777d42c3570c005371")
LEDGER_PIN=(21382,"4e5d039013f785f3f54dcad870e779db679840fe85e5160262312a0f62d176c2")
STATE_PIN=(9481,"a81dd8099724009f3de13acf5c9905cd67d47663654f5409b54be8974ac38cdd")
_BASE:ModuleType|None=None

def need(ok:bool,why:str)->None:
 if not ok:raise ValueError("A17: "+why)
def record(value:object)->Doc:
 if not isinstance(value,dict):raise ValueError("A17 object required")
 out:Doc={}
 for key,item in value.items():
  if type(key) is not str:raise ValueError("A17 text key required")
  out[key]=item
 return out
def text(value:object)->str:
 if type(value) is not str or not value:raise ValueError("A17 text required")
 return value
def uint(value:object,maximum:int=2**63-1)->int:
 if type(value) is not int or not 0<=value<=maximum:raise ValueError("A17 exact integer required")
 return value
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def enc(value:object)->bytes:
 return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def sequence(value:object)->list[object]:
 if type(value) is not list:raise ValueError("A17 JSON array required")
 return value
def refs(value:object)->ExactRef:
 r=record(value);need(set(r)=={"path","bytes","sha256"},"exact ref keys")
 path=text(r["path"]);size=uint(r["bytes"],2**53-1);digest=text(r["sha256"])
 need(Path(path).is_absolute() and size>0 and re.fullmatch("[0-9a-f]{64}",digest) is not None,"exact ref")
 return {"path":path,"bytes":size,"sha256":digest}
def read_ref(value:object,limit:int=1048576)->bytes:
 r=refs(value);p=Path(r["path"]);a=p.stat()
 with p.open("rb") as stream:raw=stream.read(limit+1)
 b=p.stat()
 need((len(raw),sha(raw))==(r["bytes"],r["sha256"]) and 0<len(raw)<=limit
  and (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns),"stable actual bytes")
 return raw
def checked(value:object,limit:int=1048576)->Doc:return record(json.loads(read_ref(value,limit)))
def ref(path:Path|str)->ExactRef:
 p=Path(path).resolve(strict=True)
 with p.open("rb") as stream:raw=stream.read(1048577)
 need(0<len(raw)<=1048576,"bounded ref")
 return {"path":str(p),"bytes":len(raw),"sha256":sha(raw)}
def fixed(path:Path,pin:tuple[int,str])->ExactRef:
 value=ref(path);need((value["bytes"],value["sha256"])==pin,"accepted historical pin "+path.name);return value
def one(source:str,before:str,after:str,count:int=1)->str:
 need(source.count(before)==count,"reviewed seam "+before[:80]);return source.replace(before,after)
def dynamic(module:ModuleType,name:str)->Dynamic:
 value:object=getattr(module,name,None);need(callable(value),"callable "+name)
 # This cast follows the explicit callable check at the isolated legacy-module boundary.
 return cast(Dynamic,value)
def load(value:object,name:str)->ModuleType:
 r=refs(value);raw=read_ref(r);module=ModuleType(name);module.__file__=r["path"]
 sys.modules[name]=module;exec(compile(raw,r["path"],"exec"),vars(module));return module
def outputs(value:object)->Outputs:
 need(isinstance(value,dict),"output map");out:Outputs={}
 for path,raw in cast(dict[object,object],value).items():
  need(isinstance(path,Path) and type(raw) is bytes,"Path bytes output")
  out[cast(Path,path)]=cast(bytes,raw)
 return out
def pair(value:object)->tuple[object,object]:
 need(type(value) is tuple and len(cast(tuple[object,...],value))==2,"result pair")
 return cast(tuple[object,object],value)
def pairs(value:object)->list[list[str]]:
 result:list[list[str]]=[]
 for value_row in sequence(value):
  row=sequence(value_row);need(len(row)==2,"source pair");result.append([text(row[0]),text(row[1])])
 return result
def parse_plan(value:object)->PlanV1:
 p=record(value);need(set(p)==set(PlanV1.__annotations__),"one A17 plan contract")
 need(p["schema"]=="xar.Source29-A17-complete-cold-input/v1" and p["machine_id"]==MACHINE
  and p["execution_owner"]=="Root" and p["root_direct_execution_release"] is True,"Root machine release")
 for key in ("attempt_nonce","task_nonce"):
  need(re.fullmatch("[0-9a-f]{32}",text(p[key])) is not None,"nonce")
 need(p["attempt_nonce"]!=p["task_nonce"],"independent nonces")
 datetime.fromisoformat(text(p["observed_at_utc"]))
 need(Path(text(p["screen_admission_path"])).resolve()==SCREEN.resolve(),"screen in new runtime")
 for key in set(p)-{"schema","machine_id","execution_owner","root_direct_execution_release",
  "observed_at_utc","attempt_nonce","task_nonce","screen_admission_path"}:refs(p[key])
 return cast(PlanV1,record(json.loads(enc(p))))

def history_view_v1(value:object)->Doc:
 view=record(value);need(type(view.get("next_sequence")) is int and view["next_sequence"]==10552,"current NEXT10552")
 return {**view,"next_sequence":10541}

def build_plan_v1(*,sdk_base_ref:ExactRef,canonical_anchor_ref:ExactRef,native_binding_ref:ExactRef,
 full_storage_ref:ExactRef,steam_native_state_ref:ExactRef,observed_at_utc:str,
 attempt_nonce:str,task_nonce:str)->PlanV1:
 closure=fixed(PREVIOUS/"ROOT-RETRY02-ACTUAL-CLOSURE-INDEX01.json",CLOSURE_PIN)
 closed=checked(closure,65536);historical=_history_plan()
 return parse_plan({"schema":"xar.Source29-A17-complete-cold-input/v1","machine_id":MACHINE,
  "execution_owner":"Root","root_direct_execution_release":True,"observed_at_utc":observed_at_utc,
  "attempt_nonce":attempt_nonce,"task_nonce":task_nonce,"full_storage_ref":full_storage_ref,
  "live_storage_ref":full_storage_ref,"steam_native_state_ref":steam_native_state_ref,
  "union_producer":ref(__file__),"stage_producer":historical["stage_producer"],
  "sdk_base_ref":sdk_base_ref,"canonical_anchor_ref":canonical_anchor_ref,"native_binding_ref":native_binding_ref,
  "closure_ref":closure,"current_driver_review_ref":closed["current_Driver_review"],
  "ledger_ref":closed["continuity_ledger"],"current_next_ref":ref(PREVIOUS/"NEXT-SEQUENCE-P37.json"),
  "screen_admission_path":str(SCREEN)})

def validate_source29_metadata_v1(base_value:object,anchor_value:object,historical_base_value:object,
 historical_anchor_ref:object,historical_base_ref:object,*,machine_id:str)->Doc:
 base=record(base_value);anchor=record(anchor_value);old=record(historical_base_value)
 need(base.get("schema")=="root.ck3.final-sdk-freeze/v1" and base.get("status")=="FINAL_SOURCE_FROZEN"
  and base.get("machine_id")==anchor.get("machine_id")==machine_id and base.get("runtime_admitted") is False
  and "canonical_preload_policy" not in base,"policy-free actual SDK BASE")
 need(anchor.get("schema")=="xar.source29.canonical-git-anchor/v1"
  and anchor.get("status")=="CANONICAL_REF_CREATED_NOT_DEPLOYED"
  and anchor.get("parent")=="442beeae4676bad9a9d53cb7070a01f06e965761"
  and anchor.get("actual_Source28_anchor")==historical_anchor_ref
  and anchor.get("actual_Source28_BASE")==historical_base_ref,"actual Source29 parent28")
 variant=anchor.get("canonical_variant");performance=anchor.get("performance_candidate")
 allowed={"xar_autoplayer/bridge/native_driver.py","xar_autoplayer/bridge/war_contract.py","xar_autoplayer/strategy.py"}
 if variant=="WAR_ONLY":need(performance is None,"war-only null performance")
 elif variant=="WAR_AND_METADATA_SNAPSHOT":
  candidate=record(performance);need(set(candidate)=={"manifest_ref","producer_ref","qualification_ref"},"performance exact refs")
  for item in candidate.values():refs(item)
  allowed.add("xar_autoplayer/bridge/service.py")
 else:raise ValueError("A17 Source29 finite variant")
 before={text(record(r)["relative"]):record(r) for r in sequence(old["files"])}
 rows=sequence(base["files"]);after={text(record(r)["relative"]):record(r) for r in rows}
 need(len(rows)==len(after)==1464 and set(before)==set(after),"complete unchanged SDK names")
 changed={name for name in after if after[name]!=before[name]}
 patches=sequence(anchor["output_pins"])
 need(changed==allowed=={text(record(r)["relative"]) for r in patches}
  and all(after[text(record(r)["relative"])]==record(r) for r in patches)
  and len(sequence(anchor["canonical_patch_rows"]))==len(allowed),"exact3/4 SDK diff")
 encoded=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
 need(anchor["complete_rows_JSON"]=={"bytes":len(encoded),"sha256":sha(encoded)}
  and uint(anchor["source_file_count"])==1464 and uint(anchor["source_bytes"])==sum(uint(record(r)["bytes"]) for r in rows)
  and base.get("business_source_commit")==anchor.get("commit")
  and base.get("source29_canonical_anchor") is not None,"actual full SDK row identity")
 return anchor

def _closed(p:PlanV1)->Doc:
 r=p["closure_ref"];need((r["bytes"],r["sha256"])==CLOSURE_PIN and Path(r["path"]).parent==PREVIOUS,"actual retry02 closure")
 x=checked(r,65536)
 need(x["schema"]=="xar.C23-retry02-war-readonly-failure-closed/v1" and x["machine_id"]==MACHINE
  and x["status"]=="RETRY02_CLOSED_FULL10543_AUTO10550_NATIVE_REJECTED" and x["Tasks_absent"] is True
  and x["screen115_released"] is True and x["SDK_normal"] is False and x["failed_AUTO_replayed"] is False
  and x["journal_completion_or_nonexecution_inferred"] is False,"closed failed attempt; no replay/fence")
 exits=record(x["SDK_actual_exits"]);game=record(x["Game"])
 need(exits=={"sdk_queue":1,"sdk_application":0} and type(exits["sdk_queue"]) is type(exits["sdk_application"]) is int
  and uint(game["exit_code"])==1 and game["forced_owned_job_cleanup"] is True and uint(game["Job_active_final"])==0,"actual1/0 Gameforced1/Job0")
 need(uint(x["failed_AUTO"])==10550 and uint(x["post_failure_readonly_journal"])==10551
  and uint(x["next_sequence"])==10552 and uint(x["saved_cycles"])==4753
  and uint(x["attempt_settled_cycles"])==4756 and uint(x["pending_cycle"])==4757
  and uint(x["pending_cycle_credit"])==uint(x["new_game_day_credit"])==0,"actual frontier/rollback")
 need(p["current_driver_review_ref"]==x["current_Driver_review"] and p["ledger_ref"]==x["continuity_ledger"],"actual current review/ledger")
 need((p["current_driver_review_ref"]["bytes"],p["current_driver_review_ref"]["sha256"])==REVIEW_PIN
  and (p["ledger_ref"]["bytes"],p["ledger_ref"]["sha256"])==LEDGER_PIN,"immutable fresh current basis")
 facts=record(x["source_refs"])
 for value in facts.values():read_ref(value,1048576)
 need(checked(p["current_next_ref"],16384).get("next_sequence")==10552
  and type(checked(p["current_next_ref"],16384).get("next_sequence")) is int,"current exact NEXT")
 ledger=checked(p["ledger_ref"],65536)
 need(ledger["status"]=="repair_required" and uint(ledger["last_settled_cycles"])==4756
  and uint(ledger["window_id"])==2,"preserve continuity wall/window")
 return x

WAR_OPTIONAL_QUEUE_V1="from typing import Literal,TypedDict\n\nclass WarOptionalQueueCreditV1(TypedDict):\n    schema:Literal[\"g2.queue.ordinary-result-credit/v1\"]\n    category:Literal[\"war_termination_optional_unavailable\"]\n    selected_step:str\n    service_status:Literal[\"executed\"]\n    result_status:Literal[\"unavailable\"]\n    typed_nonmaterial_observation:Literal[True]\n    primitive_accepted:Literal[False]\n    business_success_inferred:Literal[False]\n    submitted_pending:Literal[False]\n    replay_allowed:Literal[False]\n    resident_ui_only:Literal[False]\n    game_action_credit:Literal[False]\n    game_day_credit:Literal[False]\n    fresh_native_completion_proved:Literal[False]\n    source_frame:dict[str,object]\n\ndef _war_optional_object_v1(value:object)->dict[str,object]:\n    if not isinstance(value,dict):\n        raise ValueError(\"war optional Queue object required\")\n    out:dict[str,object]={}\n    for key,item in value.items():\n        if type(key) is not str:\n            raise ValueError(\"war optional Queue text key required\")\n        out[key]=item\n    return out\n\ndef _war_optional_uint_v1(value:object,maximum:int)->int:\n    if type(value) is not int or not 0<value<maximum:\n        raise ValueError(\"war optional Queue exact positive integer required\")\n    return value\n\ndef classify_source29_war_optional_v1(\n        body_value:object,*,initial_frame:object,current_frame:object,\n        game_pid:object)->WarOptionalQueueCreditV1|None:\n    from xar_autoplayer.bridge.war_contract import parse_war_termination_optional_unavailable_v1\n    body=_war_optional_object_v1(body_value)\n    inner=body.get(\"result\")\n    optional=parse_war_termination_optional_unavailable_v1(inner)\n    if optional is None:\n        return None\n    plan=_war_optional_object_v1(body.get(\"plan\"))\n    first=_war_optional_object_v1(initial_frame)\n    current=_war_optional_object_v1(current_frame)\n    selected=body.get(\"selected_step\")\n    if (body.get(\"status\")!=\"executed\" or type(selected) is not str\n            or selected!=plan.get(\"selected_step\") or selected!=optional[\"step\"]):\n        raise ValueError(\"war optional executed plan/step identity differs\")\n    source=optional[\"source_frame\"]\n    pid=_war_optional_uint_v1(game_pid,2**32)\n    if _war_optional_uint_v1(source[\"bridge_pid\"],2**32)!=pid:\n        raise ValueError(\"war optional belongs to another Game\")\n    first_actor=_war_optional_uint_v1(first.get(\"actor_character_id\"),2**64)\n    first_date=_war_optional_uint_v1(first.get(\"date_raw\"),2**64)\n    current_actor=_war_optional_uint_v1(current.get(\"actor_character_id\"),2**64)\n    current_date=_war_optional_uint_v1(current.get(\"date_raw\"),2**64)\n    episode=first.get(\"episode_run_id\")\n    if (type(episode) is not str or not episode\n            or current.get(\"episode_run_id\")!=episode\n            or source[\"episode_run_id\"]!=episode\n            or source[\"actor_character_id\"]!=first_actor\n            or source[\"actor_character_id\"]!=current_actor\n            or source[\"date_raw\"]<first_date\n            or source[\"date_raw\"]!=current_date):\n        raise ValueError(\"war optional actor/episode/current date differs\")\n    return {\"schema\":\"g2.queue.ordinary-result-credit/v1\",\n        \"category\":\"war_termination_optional_unavailable\",\"selected_step\":selected,\n        \"service_status\":\"executed\",\"result_status\":\"unavailable\",\n        \"typed_nonmaterial_observation\":True,\"primitive_accepted\":False,\n        \"business_success_inferred\":False,\"submitted_pending\":False,\n        \"replay_allowed\":False,\"resident_ui_only\":False,\"game_action_credit\":False,\n        \"game_day_credit\":False,\"fresh_native_completion_proved\":False,\n        \"source_frame\":_war_optional_object_v1(source)}\n\ndef verify_source29_war_optional_metrics_v1(\n        observation_value:object,before_value:object,after_value:object)->None:\n    observation=_war_optional_object_v1(observation_value)\n    if observation.get(\"category\")!=\"war_termination_optional_unavailable\":\n        return\n    before=_war_optional_object_v1(before_value)\n    after=_war_optional_object_v1(after_value)\n    source=_war_optional_object_v1(observation.get(\"source_frame\"))\n    for key in (\"actor_character_id\",\"date_raw\"):\n        original=_war_optional_uint_v1(before.get(key),2**64)\n        if (_war_optional_uint_v1(after.get(key),2**64)!=original\n                or _war_optional_uint_v1(source.get(key),2**64)!=original):\n            raise ValueError(\"paired metrics differ from readonly unavailable\")\n    episode=before.get(\"episode_run_id\")\n    if (type(episode) is not str or not episode or after.get(\"episode_run_id\")!=episode\n            or source.get(\"episode_run_id\")!=episode):\n        raise ValueError(\"paired metrics readonly episode differs\")\n"

QUEUE_CHECK_AFTER_BEFORE_V1='''            if observation is None:
                observation, self.governance_result_state, self.lifestyle_pending_focus = classifier(
'''
def patch_queue_war_optional_v1(source:bytes)->bytes:
 body=source.decode("utf-8");tree=ast.parse(body)
 need(not any(isinstance(n,ast.FunctionDef) and n.name=="classify_source29_war_optional_v1" for n in tree.body),"optional branch absent")
 marker="def classify_ordinary_auto_outcome_v1("
 body=one(body,marker,WAR_OPTIONAL_QUEUE_V1+"\n"+marker)
 call='''            if observation is None:
                observation = classify_source29_war_optional_v1(body,
                    initial_frame=self.initial_frame,
                    current_frame=ordinary_state.get("before"),game_pid=self.launch["pid"])
'''+QUEUE_CHECK_AFTER_BEFORE_V1
 body=one(body,QUEUE_CHECK_AFTER_BEFORE_V1,call)
 seam='                observation = pending["observation"]\n'
 body=one(body,seam,seam+'                verify_source29_war_optional_metrics_v1(observation,before,after)\n')
 compile(body,"A17-Queue-typed-optional","exec")
 return body.encode()

def _history_plan()->Doc:
 return checked(fixed(PRIOR_PREP/"A15-RETRY02-COLD-PLAN01.json",PLAN_PIN),16384)
def _accepted()->tuple[dict[str,bytes],Doc,Doc]:
 q=checked(fixed(PRIOR_PREP/"A15-RETRY02-COLD-QUOTE01.json",QUOTE_PIN),262144)
 names=[text(n) for n in sequence(record(q["sources"])["runtime_source_output_names"])]
 need(len(names)==len(set(names))==113,"actual113")
 profile=checked(ref(PREVIOUS/"ROOT-OBS-PROFILE-C23.json"),16384)
 config=Path(text(profile["config_root"]));name=text(profile["profile_name"])
 mutable={config/"basic/profiles"/name/"basic.ini",config/"basic/scenes"/(name+".json")}
 known:Outputs={};observed:list[ExactRef]=[]
 for item in sequence(q["files"]):
  row=record(item);r=refs({k:row[k] for k in ("path","bytes","sha256")});path=Path(r["path"])
  if path in mutable:observed.append(ref(path))
  elif path!=PREVIOUS/"NEXT-SEQUENCE-P37.json":known[path]=read_ref(r)
 need(len(known)==141 and len(observed)==2,"141immutable+2observedOBS+NEXT")
 source={name:known[PREVIOUS/name] for name in names}
 freeze=record(json.loads(known[PREVIOUS/"ROOT-FINAL-SDK-FREEZE-P37C23-A15.json"]))
 policy=checked(freeze["canonical_preload_policy"],65536)
 need(len(pairs(policy["entry_source_pins"]))==47 and len(pairs(policy["canonical_entry_source_pins"]))==8
  and len(record(policy["external_import_source_pins"]))==26
  and len(sequence(policy["runtime_import_source_pins"]))==23,"actual47/8/26/23")
 for entry_path,digest in pairs(policy["entry_source_pins"]):need(sha(known[Path(entry_path)])==digest,"actual accepted source")
 return source,q,policy

def _source29(p:PlanV1,historical:Doc)->Doc:
 oldbase=checked(historical["compact_base_ref"],524288)
 anchor=validate_source29_metadata_v1(checked(p["sdk_base_ref"],524288),
  checked(p["canonical_anchor_ref"],65536),oldbase,historical["canonical_anchor_ref"],
  historical["compact_base_ref"],machine_id=MACHINE)
 base=checked(p["sdk_base_ref"],524288)
 need(base["source29_canonical_anchor"]==p["canonical_anchor_ref"],"BASE exact actual anchor")
 return anchor

def _current_pre(p:PlanV1)->tuple[Doc,bytes]:
 from tools.g2_saved_campaign.file_stat_identity_v1 import SCHEMA,normalize_file_stat_identity_v1,parse_file_stat_identity_v1
 _closed(p);r=checked(p["current_driver_review_ref"],16384)
 need(r["schema"]=="xar.C23-retry02-current-Driver-SAVE-review/v1" and r["machine_id"]==MACHINE
  and uint(r["Driver_history_rows"])==5278 and record(r["wal"])["exists"] is False,"current retry02 full-v2")
 current=checked(ref(PREVIOUS/"ROOT-C23-COLD-PRELAUNCH.json"),16384)
 rows=sequence(r["sources"]);need(len(rows)==2,"Driver/SAVE pair")
 for item in rows:
  row=record(item);identity=parse_file_stat_identity_v1(row["identity"],schema=SCHEMA)
  need(row["identity_schema"]==SCHEMA and row["stable_before_after"] is True
   and normalize_file_stat_identity_v1(Path(refs(row["ref"])["path"]).stat())==identity,"current OS stat DTO")
 driver=refs(record(rows[0])["ref"]);payload=record(json.loads(read_ref(driver,41943040)))
 need(uint(payload["format_version"])==2 and len(sequence(payload["command_history"]))==5278
  and payload["last_checkpoint"]==current["checkpoint"]==r["last_checkpoint"],"same SAVE10480 checkpoint")
 base=checked(p["sdk_base_ref"],524288);root=Path(text(base["source_root"]));sys.path.insert(0,str(root))
 api=importlib.import_module("xar_autoplayer.cold_checkpoint_validator")
 origin=Path(text(getattr(api,"__file__",None))).resolve()
 need(origin==root/"xar_autoplayer/cold_checkpoint_validator.py","Source29 validator origin")
 rows_sdk=[record(v) for v in sequence(base["files"]) if record(v)["relative"]=="xar_autoplayer/cold_checkpoint_validator.py"]
 need(len(rows_sdk)==1,"canonical validator row")
 read_ref({"path":str(origin),"bytes":rows_sdk[0]["bytes"],"sha256":rows_sdk[0]["sha256"]})
 manifest=checked(r["environment_manifest"],32768)
 validated=record(dynamic(api,"validate_cold_start_checkpoint_payload_for_pipe")(
  SimpleNamespace(profile_dir=Path(text(manifest["profile_dir"]))),text(payload["pipe_name"]),payload))
 need(validated==current["validation"],"actual canonical SAVE cold semantics")
 sidecars:list[ExactRef]=[]
 for value in sequence(current["sidecars"]):
  fresh=ref(refs(value)["path"]);need(checked(fresh,65536).get("pending") is None,"current sidecar pending")
  sidecars.append(fresh)
 need(len(sidecars)==4,"four current sidecars")
 identity=record(record(rows[0])["identity"])
 current.update(driver_state=driver,materialized_driver_review=p["current_driver_review_ref"],
  validation=validated,sidecars=sidecars,actual_retry02_closure=p["closure_ref"],actual_next_sequence=10552,
  driver_stat_schema=SCHEMA,driver_stat={"size":identity["bytes"],"FileID":identity["file_id"],"mtime_ns":identity["mtime_ns"]},
  additional_rollback_cycles=3,additional_rollback_days=0,Driver_SAVE_body_reads=1)
 return current,enc(current)

def _bridge(p:PlanV1,pre:Doc)->str:
 historical=ref(PREVIOUS/"ROOT-C23-COLD-PRELAUNCH.json")
 header="A17_CLOSURE_REF="+repr(p["closure_ref"])+"\nA17_REVIEW_REF="+repr(p["current_driver_review_ref"])+"\n"
 header+="A17_HISTORICAL_PRE="+repr(historical)+"\nA17_CURRENT_PRE="+repr(pre)+"\n"
 return header+'''
from typing import Callable as _A17Callable
def validate_actual_retry02_index_v1(reference:object,checked:_A17Callable[[object,int],dict[str,object]])->dict[str,object]:
    require(reference==A17_CLOSURE_REF,'actual retry02 closed authority')
    x=checked(reference,65536)
    require(x['schema']=='xar.C23-retry02-war-readonly-failure-closed/v1'
        and x['machine_id']==MACHINE and x['Tasks_absent'] is True
        and x['screen115_released'] is True and x['SDK_normal'] is False
        and x['SDK_actual_exits']=={'sdk_queue':1,'sdk_application':0}
        and type(x['next_sequence']) is int and x['next_sequence']==10552
        and x['failed_AUTO']==10550 and x['post_failure_readonly_journal']==10551
        and x['failed_AUTO_replayed'] is False
        and x['journal_completion_or_nonexecution_inferred'] is False,'actual retry02 closed/no replay')
    for value in x['source_refs'].values():_a14_verify_exact_fact(value)
    return x
_A17_PRIOR_POST=validate_post_sem_driver
_A17_PRIOR_VIEW=historical_saved_basis_view
_A17_PRIOR_SEED=validate_saved_seed_a10
def validate_post_sem_driver(pre:dict[str,object],close:dict[str,object],checked:_A17Callable[[object,int],dict[str,object]],verify_current_stat:bool=True)->bool:
    if pre.get('actual_retry02_closure')!=A17_CLOSURE_REF:
        return _A17_PRIOR_POST(pre,close,checked,verify_current_stat)
    validate_actual_retry02_index_v1(A17_CLOSURE_REF,checked)
    _A17_PRIOR_POST(checked(A17_HISTORICAL_PRE,32768),close,checked,False)
    r=checked(A17_REVIEW_REF,16384)
    require(pre==A17_CURRENT_PRE and r['Driver_history_rows']==5278,'exact current A17 pre')
    if verify_current_stat:
        identity=r['sources'][0]['identity'];s=Path(pre['driver_state']['path']).stat()
        require((s.st_size,str(s.st_ino),str(s.st_mtime_ns))==
            (identity['bytes'],identity['file_id'],identity['mtime_ns']),'current Driver stat')
        for value in pre['sidecars']:require(checked(value,65536).get('pending') is None,'current sidecars')
    return True
def historical_saved_basis_view(admission:dict[str,object])->dict[str,object]:
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10552,'actual10552 not historical10541')
    return _A17_PRIOR_VIEW({**admission,'next_sequence':10541})
def validate_saved_seed_a10(admission:dict[str,object],seed:dict[str,object],original:dict[str,object],save:dict[str,object],semantic:dict[str,object],governance:dict[str,object],*,checked:_A17Callable[[object,int],dict[str,object]],projector:object=None)->bool:
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10552,'actual10552 seed')
    return _A17_PRIOR_SEED({**admission,'next_sequence':10541},seed,original,save,semantic,governance,
        checked=checked,projector=projector)
'''

FEEDER_BASIS_V1='''def old_basis(a:Admit)->Json:
 r=a['sources']['old_ledger']
 need(r==A17_LEDGER_REF and Path(r['path']).resolve()!=LEDGER.resolve(),'immutable retry02 ledger')
 need(a['sources']['old_state']==A17_STATE_REF and a['prior_retry02_index']==A17_CLOSURE_REF,'retry02 exact inputs')
 old=checked(r);state=checked(a['sources']['old_state']);pending=obj(state.get('pending_cycle'))
 need(integer(old.get('window_id'))==2 and old.get('status')=='repair_required'
  and integer(old.get('last_settled_cycles'))==4756 and integer(old.get('last_settled_date_raw'))==53274624
  and integer(state.get('completed_cycles'))==4756 and integer(obj(state.get('before')).get('date_raw'))==53274624
  and integer(pending.get('global_turn'))==4757 and integer(pending.get('auto_sequence'))==10550
  and pending.get('stage')=='auto_unsettled' and pending.get('before')==state.get('before')
  and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt')),'retry02 unsettled query')
 bootstrap=cast(Bootstrap,importlib.import_module('root_checkpoint_bootstrap_c23'))
 bootstrap.validate_actual_retry02_index_v1(a['prior_retry02_index'],checked)
 proof=checked(a['prior_retry02_index']);values=obj(proof['source_refs'])
 need(proof['continuity_ledger']==r and file_ref(values['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json'])==a['sources']['old_state']
  and integer(proof.get('failed_AUTO'))==10550 and integer(proof.get('post_failure_readonly_journal'))==10551
  and integer(proof.get('next_sequence'))==10552 and proof.get('failed_AUTO_replayed') is False
  and proof.get('journal_completion_or_nonexecution_inferred') is False
  and integer(proof.get('pending_cycle_credit'))==0,'retained failure/journal/NEXT')
 used={text(checked(file_ref(values[k])).get('nonce')) for k in ('Task/supervisor','Task/display','Task/feeder')}
 need(a['feeder_task_nonce'] not in used,'fresh A17 feeder nonce')
 return old
'''
def patch_feeder_retry02_v1(source:bytes,p:PlanV1)->bytes:
 body=source.decode();tree=ast.parse(body)
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="old_basis"]
 need(len(nodes)==1,"one old basis")
 old=ast.get_source_segment(body,nodes[0]);need(old is not None,"basis source")
 body=one(body,text(old),FEEDER_BASIS_V1.rstrip())
 body=one(body,"prior_A14_index:Ref;budget:Ref","prior_A14_index:Ref;prior_retry02_index:Ref;budget:Ref")
 body=one(body,'"prior_A14_index","budget"','"prior_A14_index","prior_retry02_index","budget"')
 body=one(body,"source28_anchor:Ref;","source28_anchor:Ref;source29_base:Ref;source29_anchor:Ref;")
 body=one(body,'"source28_anchor","prior_A11_index"','"source28_anchor","source29_base","source29_anchor","prior_A11_index"')
 body=one(body,'freeze=checked(file_ref(cold.get("sdk_freeze")));base=checked(a["source28_base"])',
  'historical=checked(a["source28_base"]);need(historical.get("source28_canonical_anchor")==a["source28_anchor"],"actual historical Source28")\n    freeze=checked(file_ref(cold.get("sdk_freeze")));base=checked(a["source29_base"])')
 body=one(body,'base.get("source28_canonical_anchor")==a["source28_anchor"]','base.get("source29_canonical_anchor")==a["source29_anchor"]')
 body=one(body,'class Bootstrap(Protocol):','class Bootstrap(Protocol):\n def validate_actual_retry02_index_v1(self,r:Ref,checked:Callable[[Ref,int],Json])->object:...')
 body=one(body,'"prior_A14_index":a["prior_A14_index"],','"prior_A14_index":a["prior_A14_index"],"prior_retry02_index":a["prior_retry02_index"],')
 body=one(body,"last_A15_SAVE10480_A14_zero_rpc_handoff","last_A17_SAVE10480_retry02_rollback")
 rollback={"saved_cycles":4753,"retry02_settled_cycles":4756,"cycles_lost":3,"settled_days_lost":0,
  "unknown_AUTO":10550,"unknown_AUTO_credit":0,"prior_unknown_AUTO":10534,"post_failure_readonly_journal":10551,"pending_global_turn":4757}
 for name,value in {"KIND":"A17_SAVE10480_retry02_rollback_verified","ROLLBACK":rollback}.items():
  node=next(n for n in ast.parse(body).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
  body=one(body,text(ast.get_source_segment(body,node)),name+"="+repr(value))
 state=fixed(PREVIOUS/"p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json",STATE_PIN)
 body="A17_CLOSURE_REF="+repr(p["closure_ref"])+"\nA17_LEDGER_REF="+repr(p["ledger_ref"])+"\nA17_STATE_REF="+repr(state)+"\n"+body
 compile(body,"A17-feeder","exec");return body.encode()

def _source29_runtime(p:PlanV1,historical:Doc)->str:
 own=Path(__file__).read_text(encoding="utf-8");tree=ast.parse(own)
 names=("need","record","text","uint","sha","sequence","refs","validate_source29_metadata_v1")
 fragment="from typing import TypedDict\nimport re\nclass ExactRef(TypedDict):\n path:str\n bytes:int\n sha256:str\nDoc=dict[str,object]\n"
 for name in names:
  node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
  fragment+=text(ast.get_source_segment(own,node))+"\n"
 for name in names:fragment=re.sub(r"\b"+name+r"\b","_a17_"+name,fragment)
 constants={"A17_BASE":p["sdk_base_ref"],"A17_ANCHOR":p["canonical_anchor_ref"],
  "A17_HISTORY_BASE":historical["compact_base_ref"],"A17_HISTORY_ANCHOR":historical["canonical_anchor_ref"],
  "A17_HISTORY_FREEZE":ref(PREVIOUS/"ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")}
 fragment+="\n".join(k+"="+repr(v) for k,v in constants.items())+"\n"
 return fragment+'''
from types import FunctionType as _A17FunctionType
_A17_PRIOR_ANCHOR=validate_source28_business_anchor
_A17_PRIOR_BUSINESS=_A17FunctionType(validate_source28_frozen_business.__code__,dict(globals()))
def validate_source28_business_anchor(anchor,checked):
    _A17_PRIOR_ANCHOR(checked(A17_HISTORY_ANCHOR,65536),checked)
    require(anchor==checked(A17_ANCHOR,65536),'actual Source29 anchor input')
    return _a17_validate_source29_metadata_v1(checked(A17_BASE,524288),anchor,
        checked(A17_HISTORY_BASE,524288),A17_HISTORY_ANCHOR,A17_HISTORY_BASE,machine_id=MACHINE)
def validate_source28_frozen_business(admission,freeze,checked):
    history=checked(A17_HISTORY_FREEZE,524288)
    old_anchor=checked(A17_HISTORY_ANCHOR,65536)
    old_admission={**admission,'business_anchor':A17_HISTORY_ANCHOR,'business_source_commit':old_anchor['commit']}
    _A17_PRIOR_BUSINESS(old_admission,history,checked)
    base=checked(A17_BASE,524288)
    anchor=_a17_validate_source29_metadata_v1(base,checked(A17_ANCHOR,65536),
        checked(A17_HISTORY_BASE,524288),A17_HISTORY_ANCHOR,A17_HISTORY_BASE,machine_id=MACHINE)
    require(admission['business_anchor']==A17_ANCHOR and freeze['files']==base['files']
        and freeze['business_source_commit']==admission['business_source_commit']==anchor['commit'],
        'actual Source29 admission/freeze')
    return anchor
'''
def _build_sources(p:PlanV1,pre:Doc,historical:Doc)->tuple[dict[str,bytes],Doc]:
 source,q,policy=_accepted()
 boot=source["root_checkpoint_bootstrap_c23.py"].decode()
 boot=one(boot,"if __name__ == '__main__':",_source29_runtime(p,historical)+_bridge(p,pre)+"\nif __name__ == '__main__':")
 source["root_checkpoint_bootstrap_c23.py"]=boot.encode()
 body=source["root_native30_supervisor_c23.py"].decode()
 body=one(body,"type(actual_next) is int and actual_next==10541","type(actual_next) is int and actual_next==10552")
 closure=_bridge(p,pre).split("_A17_PRIOR_POST=")[0]
 extension=closure+'''
_A17_PRIOR_ATTEMPT=_validate_a15_attempt
def _validate_a15_attempt(args,config):
    value=_A17_PRIOR_ATTEMPT(args,config)
    closed=validate_actual_retry02_index_v1(A17_CLOSURE_REF,_a03_checked)
    used={_a03_checked(closed['source_refs'][key],16384)['nonce']
        for key in ('Task/supervisor','Task/display','Task/feeder')}
    require(args.attempt_nonce not in used and args.task_nonce not in used,'independent A17 nonces')
    return value
'''
 body=one(body,"def main(args):",extension+"\ndef main(args):")
 source["root_native30_supervisor_c23.py"]=body.encode()
 source["root_p37c23_sdk_queue.py"]=patch_queue_war_optional_v1(source["root_p37c23_sdk_queue.py"])
 source["launch_a10_saved10480_feeder01.py"]=patch_feeder_retry02_v1(source["launch_a10_saved10480_feeder01.py"],p)
 for name,raw in source.items():
  if name.endswith(".py"):compile(raw,name,"exec")
 old_review=record(q["sources"])
 review={"schema":"xar.A17-accepted-source-carry/v1","machine_id":MACHINE,
  "runtime_source_output_names":sorted(source),"actual_source_rows":[ref(PREVIOUS/name) for name in sorted(source)],
  "supplemental_import_rows":old_review["supplemental_import_rows"],"staging_files":old_review["staging_files"],
  "actual_retry02_index":p["closure_ref"],"feeder":{},"accepted_policy":policy,"new_day_credit":0}
 return source,review

def _factory(p:PlanV1,pre:Doc,pre_raw:bytes)->tuple[ModuleType,Doc]:
 global _BASE
 template=load(fixed(BASE_PATH,BASE_PIN),"_a17_verified_a16")
 value=dynamic(template,"_base")();need(isinstance(value,ModuleType),"isolated historical factory")
 m=cast(ModuleType,value)
 oldplan=_history_plan();old_prior=dynamic(m,"_prior");h,q0,done=cast(tuple[object,object,object],old_prior(oldplan))
 history=record(h);_source29(p,history);_closed(p)
 _,q,policy=_accepted()
 setattr(m,"U14",PREVIOUS);setattr(m,"U15",TARGET);setattr(m,"PREP",PREP)
 setattr(m,"_prior",lambda unused:(history,q,done))
 setattr(m,"_intake",lambda unused:_accepted())
 setattr(m,"_build_sources",lambda unused,unused_pre:_build_sources(p,pre,history))
 a13=importlib.import_module("prepare_source28_a13_union_v1")
 proxy=ModuleType("_a17_historical_a13");vars(proxy).update(vars(a13))
 old_guard=dynamic(a13,"source28_guard")
 def business(unused:object)->object:
  old_guard(history);return _source29(p,history)
 setattr(proxy,"source28_guard",business)
 def import_module(name:str)->ModuleType:
  return proxy if name=="prepare_source28_a13_union_v1" else importlib.import_module(name)
 setattr(m,"importlib",SimpleNamespace(import_module=import_module))
 original_source=read_ref(getattr(template,"BASE_REF")).decode("utf-8")
 factory_node=next(n for n in ast.parse(original_source).body if isinstance(n,ast.FunctionDef) and n.name=="_factory")
 factory_source=text(ast.get_source_segment(original_source,factory_node))
 factory_source=one(factory_source," projected=copy.deepcopy(old)"," projected=copy.deepcopy(old)\n projected.update(compact_base_ref=p['sdk_base_ref'],canonical_anchor_ref=p['canonical_anchor_ref'],native_binding_ref=p['native_binding_ref'])")
 factory_source=one(factory_source,'source=one(source,"new_first_sequence=10538","new_first_sequence=10541")',
  'source=one(source,"new_first_sequence=10538","new_first_sequence=10552")')
 factory_source=one(factory_source,"'.replace(\"C23-A04\",\"C23-A14\")'","'.replace(\"C23-A04\",\"C23-A15\")'")
 factory_source=one(factory_source,'source=one(source,\'U13/"ROOT-NATIVE30-NATIVE-PIN-C23-A13.json"\',\'U13/"ROOT-NATIVE30-NATIVE-PIN-C23-A14.json"\')',
  'source=one(source,\'U13/"ROOT-NATIVE30-NATIVE-PIN-C23-A13.json"\',\'U13/"ROOT-NATIVE30-NATIVE-PIN-C23-A15.json"\')')
 factory_source=factory_source.replace("T4/'ROOT-NATIVE30-NATIVE-PIN-C23-A14.json'","T4/'ROOT-NATIVE30-NATIVE-PIN-C23-A15.json'")
 factory_source=factory_source.replace('U13/"ROOT-LAUNCH-CONFIG-C23-A14.json"','U13/"ROOT-LAUNCH-CONFIG-C23-A15.json"')
 factory_source=one(factory_source," return made,projected",
  " return made,projected")
 exec(compile(factory_source,"A17-factory","exec"),vars(m))
 original_function=dynamic(m,"function")
 def function(module:object,name:object)->str:
  result=text(original_function(module,name))
  if name=="compose" and isinstance(module,ModuleType) and Path(text(getattr(module,"__file__",None))).name=="prepare_source28_a14_cold_union_v1.py":
   result=one(result,"spec-supervisor-a15-retry02","spec-supervisor-a17",2)
   result=result.replace("source28_canonical_anchor","source29_canonical_anchor").replace("xar.source28.","xar.source29.")
   result=result.replace("source28_static_binding","source29_static_binding")
  return result
 setattr(m,"function",function)
 setattr(m,"__file__",__file__)
 internal:Doc={**p,"actual_A14_closure_ref":oldplan["actual_A14_closure_ref"]}
 result=pair(dynamic(m,"_factory")(internal,pre,pre_raw))
 need(isinstance(result[0],ModuleType),"finite factory");_BASE=m
 return cast(ModuleType,result[0]),record(result[1])

def compose(plan_value:object,*,display_values:dict[str,bytes],display_review:Doc,
 companion_values:Outputs)->tuple[Outputs,Doc]:
 p=parse_plan(plan_value);need(not TARGET.exists() and ref(__file__)==p["union_producer"],"exact absent new runtime/source")
 pre,raw=_current_pre(p);factory,projected=_factory(p,pre,raw)
 result=pair(dynamic(factory,"compose")(projected,display_values=display_values,
  display_review=display_review,companion_values=companion_values))
 out=outputs(result[0]);quote=record(result[1]);nxt=read_ref(p["current_next_ref"],16384)
 out[TARGET/"NEXT-SEQUENCE-P37.json"]=nxt
 for item in sequence(quote["files"]):
  row=record(item);path=Path(text(row["path"]));raw=out[path]
  row.update(bytes=len(raw),sha256=sha(raw))
  if path==TARGET/"NEXT-SEQUENCE-P37.json":row.update(mode="hardlink",source=p["current_next_ref"],allocation_upper=0)
  cast(dict[str,object],item).update(row)
 quote.update(schema="xar.Source29-A17-complete-cold-quote/v1",actual_retry02_index=p["closure_ref"],
  current_driver_review=p["current_driver_review_ref"],continuity_ledger=p["ledger_ref"],
  new_first_sequence=10552,rollback_cycles=3,rollback_days=0,unknown10550_credit=0,
  consumed_readonly_journal=10551,original_wall_origin_reset=False,
  body_reads_Driver_SAVE_hash=1,body_read_bytes_Driver=refs(pre["driver_state"])["bytes"],
  Driver_full_read_bytes=refs(pre["driver_state"])["bytes"],SAVE_body_reads=0,copies_created=0)
 quote["campaign_score_junction"]={"path":str(TARGET/"campaign-score"),"exact_target":str(P/"robert30-v20261019-campaign01/runtime/campaign-score"),"must_verify_same_FileID":True}
 directories=[text(v) for v in sequence(quote["prerequisite_directories"])]
 quote["prerequisite_directories"]=sorted(set(directories+[str(TARGET/"campaign-score")]))
 rows=sequence(quote["files"])
 quote.update(logical_bytes=sum(map(len,out.values())),fresh_allocation_upper=sum(uint(record(r)["allocation_upper"]) for r in rows),
  immutable_hardlinks=sum(record(r)["mode"]=="hardlink" for r in rows),max_atomic_copy=max((len(b)+4095)//4096*4096 for b in out.values()))
 quote["prepare_peak_upper"]=sum(uint(quote[k]) for k in ("fresh_allocation_upper","max_atomic_copy","future_owner_metadata_upper","control_probe_atomic_peak","intent_receipt_and_FS_upper"))
 need(len(out)==uint(quote["unique_files"])==144,"actual complete144")
 return out,quote

def metadata_source(plan_value:object,source:str)->str:
 p=parse_plan(plan_value);template=load(fixed(BASE_PATH,BASE_PIN),"_a17_metadata_a16")
 module=dynamic(template,"_base")();need(isinstance(module,ModuleType),"metadata base")
 setattr(module,"U14",PREVIOUS);setattr(module,"U15",TARGET)
 setattr(module,"parse_plan",lambda unused:{**p,"schema":"xar.Source28-A15-complete-cold-input/v1"})
 value=text(dynamic(cast(ModuleType,module),"metadata_source")(
  {**p,"schema":"xar.Source28-A15-complete-cold-input/v1"},source))
 value=value.replace("source28_canonical_anchor","source29_canonical_anchor").replace("xar.source28.","xar.source29.")
 need(value.count("ROOT-FINAL-SDK-FREEZE-P37C23-A17.json") in (0,1),"one optional legacy-contract freeze lookup")
 value=value.replace("ROOT-FINAL-SDK-FREEZE-P37C23-A17.json","ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")
 return one(value,"'source28_anchor':A12_SOURCE28_ANCHOR","'source28_anchor':A12_SOURCE28_ANCHOR,'source29_anchor':A17_SOURCE29_ANCHOR,'source29_base':A17_SOURCE29_BASE")

def metadata_scope(plan_value:object,namespace:Doc,runtime:Path)->None:
 p=parse_plan(plan_value);need(runtime==TARGET,"A17 deployed metadata namespace")
 template=load(fixed(BASE_PATH,BASE_PIN),"_a17_deployed_metadata_base")
 loaded=dynamic(template,"_base")();need(isinstance(loaded,ModuleType),"metadata loader")
 base=cast(ModuleType,loaded)
 setattr(base,"U14",PREVIOUS);setattr(base,"U15",TARGET)
 setattr(base,"parse_plan",lambda unused:{**p,"schema":"xar.Source28-A15-complete-cold-input/v1"})
 dynamic(base,"metadata_scope")(p,namespace,runtime)
 namespace.update(A17_SOURCE29_ANCHOR=p["canonical_anchor_ref"],A17_SOURCE29_BASE=p["sdk_base_ref"])

def patch_cold_owner_freeze_lookup_v1(source:str)->str:
 before="source=ast.get_source_segment(text,node).replace('A05','A17').replace('a05','a17')"
 return one(source,before+"\n    seam=",before+"\n    source=source.replace('ROOT-FINAL-SDK-FREEZE-P37C23-A17.json','ROOT-FINAL-SDK-FREEZE-P37C23-A15.json')\n    seam=")

def cold_owner(inputs_value:object)->tuple[Outputs,Doc]:
 inputs=record(inputs_value)
 need(inputs.get("schema")=="xar.C23-A17-cold-owner-metadata-input/v1" and inputs.get("machine_id")==MACHINE,"A17 cold owner")
 p=parse_plan(checked(inputs["cold_graph_plan"],16384))
 template=load(fixed(BASE_PATH,BASE_PIN),"_a17_cold_metadata_base")
 loaded=dynamic(template,"_base")();need(isinstance(loaded,ModuleType),"metadata base")
 base=cast(ModuleType,loaded)
 setattr(base,"U14",PREVIOUS);setattr(base,"U15",TARGET)
 setattr(base,"parse_plan",lambda unused:{**p,"schema":"xar.Source28-A15-complete-cold-input/v1"})
 a08=importlib.import_module("prepare_c23_a08_union_v1")
 source=text(dynamic(base,"function")(a08,"cold_owner")).replace("A08","A17").replace("a08","a17")
 source=patch_cold_owner_freeze_lookup_v1(source)
 def scope(value:object,runtime:object)->None:
  need(isinstance(value,dict) and runtime==TARGET,"metadata scope")
  metadata_scope(p,cast(Doc,value),cast(Path,runtime))
 namespace:Doc=dict(vars(a08));namespace.update(U8=TARGET,T5=TARGET,
  metadata_source=lambda value:metadata_source(p,text(value)),metadata_scope=scope)
 exec(compile(source,"A17-cold-owner","exec"),namespace)
 value:object=namespace["cold_owner"];need(callable(value),"cold metadata")
 result=pair(cast(Dynamic,value)({k:v for k,v in inputs.items() if k!="cold_graph_plan"}))
 return outputs(result[0]),record(result[1])

