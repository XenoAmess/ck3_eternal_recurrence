"""Typed, isolated A15 retry02 preparation. Old A15 bytes and outputs are immutable."""
from __future__ import annotations
import ast,hashlib,json,re,sys,types
from datetime import datetime,timezone,timedelta
from pathlib import Path
from types import ModuleType
from typing import Callable,Literal,Protocol,TypedDict,cast
sys.dont_write_bytecode=True
Doc=dict[str,object]
Outputs=dict[Path,bytes]
class ExactRef(TypedDict):
 path:str
 bytes:int
 sha256:str
class ScreenAdmissionV1(TypedDict):
 schema:Literal["xar.C23-root-resource-screen-admission/v3"]
 machine_id:str
 observed_at_utc:str
 status:Literal["ACQUIRED"]
 task_id:str
 sequence:int
 repo:str
 git_head:str
 reviewer:Literal["/root"]
 provenance:list[ExactRef]
class Dynamic(Protocol):
 def __call__(self,*args:object,**kwargs:object)->object:...
MACHINE="xenoamess-full-tower-eb9d2c1186"
OWN=Path(__file__).resolve().parent
P=Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O=P/"p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
FAILED_ROOT=P/"robert30-v20261019-campaign01/runtime-a15"
TARGET=FAILED_ROOT.with_name("runtime-a15-retry02")
PREP=O/"source28-a15-retry02-prep01"
TASK=O/"tasks/spec-supervisor-a15-retry02"
SCREEN=TARGET/"ROOT-SCREEN-ADMISSION-C23-A15.json"
BASE_REF:ExactRef={"path":str(OWN/"prepare_source28_a15_cold_union_v1.py"),"bytes":40441,
 "sha256":"59970eedc999d95929da86206358edaf26c68f6e8a439cdbdffa928b3340fb91"}
FAILED_REF:ExactRef={"path":str(FAILED_ROOT/"ROOT-A15-PREGAME-FAILURE-CLOSURE01.json"),"bytes":2193,
 "sha256":"737eaaaa0b7aaf98a355b1576e188cb1f0b316beb577ff73a6249b5ea38ae750"}
RELEASE_REF:ExactRef={"path":str(FAILED_ROOT/"ROOT-A15-SCREEN-RELEASE01.json"),"bytes":2182,
 "sha256":"c4201010752a11a6322b1cfc95113b2d0f70360b735279f9eb0ff44346de8379"}
def need(ok:bool,why:str)->None:
 if not ok:raise ValueError("A15 retry02: "+why)
def record(value:object)->Doc:
 need(type(value) is dict,"object required")
 row=cast(dict[object,object],value);need(all(type(k) is str for k in row),"text keys")
 return cast(Doc,value)
def text(value:object)->str:
 need(type(value) is str and bool(value),"nonempty text");return cast(str,value)
def sha(value:bytes)->str:return hashlib.sha256(value).hexdigest()
def enc(value:object)->bytes:return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
def ref_value(value:object)->ExactRef:
 r=record(value);need(set(r)=={"path","bytes","sha256"},"exact ref fields")
 p=text(r["path"]);n=r["bytes"];h=text(r["sha256"])
 need(Path(p).is_absolute() and type(n) is int and 0<n<=2**53-1 and re.fullmatch("[0-9a-f]{64}",h) is not None,"exact ref values")
 return {"path":p,"bytes":cast(int,n),"sha256":h}
def verify_exact_bytes_ref(value:object,limit:int=1048576)->bytes:
 r=ref_value(value);p=Path(r["path"]);a=p.stat()
 with p.open("rb") as f:b=f.read(limit+1)
 z=p.stat();need(0<len(b)<=limit and (len(b),sha(b))==(r["bytes"],r["sha256"]) and
 (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns),"actual bounded immutable ref")
 return b
def checked(value:object,limit:int=1048576)->Doc:return record(json.loads(verify_exact_bytes_ref(value,limit)))
def ref(path:Path|str)->ExactRef:
 p=Path(path).resolve(strict=True)
 with p.open("rb") as f:b=f.read(1048577)
 need(0<len(b)<=1048576,"bounded source")
 return {"path":str(p),"bytes":len(b),"sha256":sha(b)}
def one(source:str,before:str,after:str,count:int=1)->str:
 need(source.count(before)==count,"single accepted seam "+before[:72]);return source.replace(before,after)
def dynamic(module:ModuleType,name:str)->Dynamic:
 v:object=getattr(module,name,None);need(callable(v),"callable "+name);return cast(Dynamic,v)
def _sources(value:object)->dict[str,bytes]:
 r=record(value);need(all(type(v) is bytes for v in r.values()),"source bytes");return cast(dict[str,bytes],r)
def outputs(value:object)->Outputs:
 need(type(value) is dict,"Path bytes map")
 r=cast(dict[object,object],value);need(all(isinstance(k,Path) and type(v) is bytes for k,v in r.items()),"Path bytes entries")
 return cast(Outputs,value)
def parse_screen_admission_v1(value:object,*,machine_id:str,repo:Path,git_head:str,at_utc:datetime)->ScreenAdmissionV1:
 if type(value) is not dict:raise ValueError("screen object required")
 row=cast(dict[str,object],value)
 keys={"schema","machine_id","observed_at_utc","status","task_id","sequence","repo","git_head","reviewer","provenance"}
 if set(row)!=keys or any(type(k) is not str for k in row):raise ValueError("one screen field contract")
 if (row["schema"]!="xar.C23-root-resource-screen-admission/v3" or row["machine_id"]!=machine_id
  or row["status"]!="ACQUIRED" or row["reviewer"]!="/root"):raise ValueError("screen authority")
 for key in ("machine_id","observed_at_utc","task_id","repo","git_head"):
  if type(row[key]) is not str or not row[key]:raise ValueError("screen text field")
 sequence=row["sequence"]
 if type(sequence) is not int or not 0<sequence<=2**53-1:raise ValueError("screen exact positive sequence")
 if not Path(cast(str,row["repo"])).is_absolute() or Path(cast(str,row["repo"])).resolve()!=repo.resolve() or row["git_head"]!=git_head or re.fullmatch("[0-9a-f]{40}",git_head) is None:
  raise ValueError("screen actual checkout")
 observed=datetime.fromisoformat(cast(str,row["observed_at_utc"]).replace("Z","+00:00"))
 if (observed.tzinfo is None or observed.utcoffset()!=timedelta(0) or at_utc.tzinfo is None
  or at_utc.utcoffset()!=timedelta(0) or not 0<=(at_utc-observed).total_seconds()<=600):
  raise ValueError("screen current UTC")
 rows=row["provenance"]
 if type(rows) is not list or not 1<=len(cast(list[object],rows))<=8:raise ValueError("screen provenance refs")
 refs:list[ExactRef]=[]
 for item in cast(list[object],rows):
  if type(item) is not dict:raise ValueError("screen provenance object")
  r=cast(dict[str,object],item)
  if set(r)!={"path","bytes","sha256"}:raise ValueError("screen provenance fields")
  if (type(r["path"]) is not str or not Path(r["path"]).is_absolute()
   or type(r["bytes"]) is not int or not 0<r["bytes"]<=2**53-1
   or type(r["sha256"]) is not str or re.fullmatch("[0-9a-f]{64}",r["sha256"]) is None):
   raise ValueError("screen provenance values")
  refs.append({"path":r["path"],"bytes":r["bytes"],"sha256":r["sha256"]})
 return {"schema":"xar.C23-root-resource-screen-admission/v3","machine_id":machine_id,
  "observed_at_utc":cast(str,row["observed_at_utc"]),"status":"ACQUIRED","task_id":cast(str,row["task_id"]),
  "sequence":sequence,"repo":cast(str,row["repo"]),"git_head":git_head,"reviewer":"/root","provenance":refs}
def build_screen_admission_v1(*,sequence:int,task_id:str,repo:Path,git_head:str,observed_at_utc:datetime,
 provenance:list[ExactRef])->ScreenAdmissionV1:
 result={"schema":"xar.C23-root-resource-screen-admission/v3","machine_id":MACHINE,
  "observed_at_utc":observed_at_utc.isoformat(),"status":"ACQUIRED","task_id":task_id,
  "sequence":sequence,"repo":str(repo.resolve()),"git_head":git_head,"reviewer":"/root","provenance":provenance}
 for item in provenance:verify_exact_bytes_ref(item)
 return parse_screen_admission_v1(result,machine_id=MACHINE,repo=repo,git_head=git_head,at_utc=observed_at_utc)
def validate_pre_game_retry_v1()->Doc:
 failure=checked(FAILED_REF,16384);release=checked(RELEASE_REF,16384)
 need(failure["schema"]=="xar.C23-A15-zero-Game-prelaunch-closed/v1" and failure["machine_id"]==MACHINE
  and failure["Game_created"] is False and failure["SDK_started"] is False and failure["recorder_started"] is False
  and failure["Task_absent"] is True and failure["admitted_receipt_absent"] is True
  and failure["Game_launch_receipt_absent"] is True and type(failure["stage_exit_code"]) is int and failure["stage_exit_code"]==1
  and type(failure["days_added"]) is type(failure["cycles_added"]) is int and failure["days_added"]==failure["cycles_added"]==0,
  "actual preGame failure, no Game/SDK/day credit")
 for key in ("Task_closed","Task_stderr","Task_unregister","old_SPEC_preserved","NEXT"):verify_exact_bytes_ref(failure[key],16384)
 closed=checked(failure["Task_closed"],16384);need(type(closed["child_exit_code"]) is type(closed["bootstrap_exit_code"]) is int and closed["child_exit_code"]==closed["bootstrap_exit_code"]==1
  and type(closed["job_active_after_stage"]) is int and closed["job_active_after_stage"]==0 and closed["forced_remaining_cleanup"] is False,"actual consumed Task closure")
 operation=record(json.loads(text(release["stdout"])));task=record(operation["task"])
 need(release["machine_id"]==MACHINE and type(release["returncode"]) is int and release["returncode"]==0 and operation["ok"] is True
  and task["resources"]==[] and task["state"]=="done" and type(task["last_sequence"]) is int and task["last_sequence"]==7854,
  "actual released failed screen")
 current=checked(failure["NEXT"],16384)["next_sequence"]
 need(type(current) is int and current==10541,"unchanged actual frontier")
 return failure
def _external_literal_pins_v1(sources:dict[str,bytes],names:dict[str,object])->dict[str,tuple[int,str]]:
 need(len(names)==26,"actual external literal26")
 return {stem:(len(sources[stem+".py"]),sha(sources[stem+".py"])) for stem in names}
def _fragment()->str:
 source=Path(__file__).read_text(encoding="utf-8");nodes={n.name:n for n in ast.parse(source).body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
 names=("ExactRef","ScreenAdmissionV1","parse_screen_admission_v1")
 segments=[]
 for name in names:
  segment=ast.get_source_segment(source,nodes[name]);need(isinstance(segment,str),"actual shared screen definition");segments.append(cast(str,segment))
 return "from typing import Literal,TypedDict,cast\nfrom datetime import timedelta\n"+"\n\n".join(segments)+"\n"
_BASE:ModuleType|None=None
def _base()->ModuleType:
 global _BASE
 if _BASE is not None:return _BASE
 b=verify_exact_bytes_ref(BASE_REF);original=b.decode()
 tree=ast.parse(original);carry=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_carry")
 assignment=next(n for n in carry.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="newmap")
 segment=ast.get_source_segment(original,assignment)
 before='newmap={stem:sha(source[stem+".py"]) for stem in oldmap}'
 after='newmap=_a16_external_literal_pins_v1(source,oldmap)'
 need(segment==before,"accepted _carry literal assignment")
 projected=one(original,before,after)
 need(one(projected,after,before)==original,"reversible producer-only tuple fix")
 m=ModuleType("_a16_exact_a15");m.__file__=__file__;sys.modules[m.__name__]=m
 exec(compile(projected,BASE_REF["path"],"exec"),vars(m))
 setattr(m,"U15",TARGET);setattr(m,"PREP",PREP)
 setattr(m,"_a16_external_literal_pins_v1",_external_literal_pins_v1)
 old_parse=dynamic(m,"parse_plan");old_function=dynamic(m,"function");old_build=dynamic(m,"_build_sources");old_pre=dynamic(m,"_current_pre")
 def parse(value:object)->object:
  p=record(old_parse(value));need(Path(text(p["screen_admission_path"])).resolve()==SCREEN.resolve(),"screen inside retry root")
  failure=validate_pre_game_retry_v1();spec=checked(failure["old_SPEC_preserved"],16384)
  argv=spec["stage_args"];need(type(argv) is list,"old stage argv")
  a=cast(list[object],argv);old={spec["nonce"],a[a.index("--attempt-nonce")+1],a[a.index("--task-nonce")+1]}
  need(p["task_nonce"] not in old and p["attempt_nonce"] not in old,"new once-only attempt and Task nonces")
  return p
 def current_pre(plan:object)->object:
  value=old_pre(plan);need(type(value) is tuple and len(cast(tuple[object,...],value))==2,"current pre pair")
  pre=record(cast(tuple[object,object],value)[0]);p=record(plan)
  review=checked(p["current_driver_review_ref"],16384);rows=review["sources"]
  need(type(rows) is list and len(cast(list[object],rows))==2,"current Driver/SAVE review")
  driver=record(cast(list[object],rows)[0]);identity=record(driver["identity"])
  pre.update(actual_next_sequence=10541,driver_stat_schema=driver["identity_schema"],
   driver_stat={"size":identity["bytes"],"FileID":identity["file_id"],"mtime_ns":identity["mtime_ns"]})
  return pre,enc(pre)
 def function(mod:object,name:object)->str:
  result=text(old_function(mod,name))
  if name=="compose" and isinstance(mod,ModuleType) and Path(text(getattr(mod,"__file__",None))).name=="prepare_source28_a14_cold_union_v1.py":
   result=one(result,"spec-supervisor-a14","spec-supervisor-a15-retry02",2)
  return result
 def build(plan:object,pre:object)->object:
  value=old_build(plan,pre);need(type(value) is tuple and len(cast(tuple[object,...],value))==2,"build pair")
  pair=cast(tuple[object,object],value);source=_sources(pair[0]);review=record(pair[1]);name="root_native30_supervisor_c23.py"
  body=source[name].decode()
  before="    require(read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10538,'new A12 actual10538 once')"
  after="    actual_next=read(N/'NEXT-SEQUENCE-P37.json').get('next_sequence')\n    require(type(actual_next) is int and actual_next==10541,'actual retry02 current10541')"
  body=one(body,before,after)
  prefix="    clean, screen, config = map(read, (args.clean_source_freeze, args.screen_admission, args.launch_config))"
  body=one(body,prefix,prefix+"\n    screen=parse_screen_admission_v1(screen,machine_id=MACHINE,repo=Path(clean['repo']),git_head=clean['git_head'],at_utc=now())")
  body=one(body,"def main(args):",_fragment()+"\ndef main(args):")
  source[name]=body.encode();compile(source[name],name,"exec")
  review["preGame_retry"]={"failed_predecessor":FAILED_REF,"actual_screen_release":RELEASE_REF,
   "actual_failure":"main808 outside-root screen; no Game created","static_next_defect":"subsequent full original validation chain rejected stale10538; never a Game attempt",
   "original_stage_preserved":True,"historical_constants_preserved":True,"current_next":10541,"shared_screen_schema":"xar.C23-root-resource-screen-admission/v3"}
  return source,review
 setattr(m,"parse_plan",parse);setattr(m,"function",function);setattr(m,"_build_sources",build);setattr(m,"_current_pre",current_pre)
 _BASE=m;return m
def parse_plan(value:object)->Doc:return record(dynamic(_base(),"parse_plan")(value))
def compose(plan_value:object,*,display_values:dict[str,bytes],display_review:Doc,companion_values:Outputs)->tuple[Outputs,Doc]:
 value=dynamic(_base(),"compose")(plan_value,display_values=display_values,display_review=display_review,companion_values=companion_values)
 need(type(value) is tuple and len(cast(tuple[object,...],value))==2,"compose pair")
 pair=cast(tuple[object,object],value);out=outputs(pair[0]);quote=record(pair[1])
 quote["preGame_retry_of"]=FAILED_REF;quote["screen_contract"]="xar.C23-root-resource-screen-admission/v3"
 return out,quote
def module(value:object,name:str)->ModuleType:
 result=dynamic(_base(),"module")(value,name);need(isinstance(result,ModuleType),"module result")
 return cast(ModuleType,result)
def metadata_source(plan_value:object,source:str)->str:return text(dynamic(_base(),"metadata_source")(plan_value,source))
def metadata_scope(plan_value:object,namespace:Doc,runtime:Path)->None:
 dynamic(_base(),"metadata_scope")(plan_value,namespace,runtime)
def cold_owner(inputs_value:object)->tuple[Outputs,Doc]:
 value=dynamic(_base(),"cold_owner")(inputs_value);need(type(value) is tuple and len(cast(tuple[object,...],value))==2,"cold pair")
 pair=cast(tuple[object,object],value);return outputs(pair[0]),record(pair[1])
