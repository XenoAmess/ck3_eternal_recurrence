from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta
import hashlib
import json
from pathlib import Path,PureWindowsPath
import re
from typing import Literal,TypedDict
TARGET="xar.native31.static-target/v1"
SCHEMA="xar.native31.source28-static-binding/v1"
STATIC="STATIC_SOURCE_BOUND_NOT_LOADED"
OFFLINE="OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
CALLS=frozenset(("XarCk3BridgeIdentity","XarCk3BridgePrepareStartup",
 "XarCk3BridgeStart","XarCk3BridgeStartWithPipe","XarCk3BridgeStop"))
DATA="XarRefillCoreCarrier12004"
class RefJSON(TypedDict):
  path:str; bytes:int; sha256:str
class LaunchValues(TypedDict):
  native_build_label:str; dll_sha256:str; git_head:str; dll:str; build_receipt:str
@dataclass(frozen=True,slots=True)
class FileRef:
  path:str; bytes:int; sha256:str
  def json(self)->RefJSON:
    return {"path":self.path,"bytes":self.bytes,"sha256":self.sha256}
@dataclass(frozen=True,slots=True)
class ColdGuards:
  native_bridge_after_saved_load:Literal[False]=False
  primary_never_resumed_before_prepare:Literal[True]=True
  remote_prepare_exit:Literal[1]=1
@dataclass(frozen=True,slots=True)
class TargetV1:
  metadata:FileRef; label:str; dll:FileRef; qualification:FileRef
  exports:tuple[tuple[str,int],...]
@dataclass(frozen=True,slots=True)
class BindingV1:
  status:Literal["STATIC_SOURCE_BOUND_NOT_LOADED"]
  target:TargetV1
  source_freeze:FileRef
  source_root:str; git_head:str; historical_native_sha256:str
  runtime_requirements:ColdGuards
  physical_sdk_revalidation_required:Literal[True]=True
  loaded_provider_issued:Literal[False]=False
def need(ok:bool,message:str)->None:
  if not ok:raise ValueError(message)
def obj(value:object,keys:frozenset[str]|None=None)->dict[str,object]:
  if not isinstance(value,dict): raise ValueError("object")
  result:dict[str,object]={}
  for key,item in value.items():
    if type(key) is not str: raise ValueError("string key")
    result[key]=item
  need(keys is None or frozenset(result)==keys,"fields")
  return result
def text(value:object)->str:
  if type(value) is not str or not value or "\0" in value: raise ValueError("text")
  return value
def utc(value:object)->str:
  result=text(value)
  need(datetime.fromisoformat(result).utcoffset()==timedelta(0),"UTC required")
  return result
def uint(value:object,maximum:int=2**53-1)->int:
  if type(value) is not int or not 0 <=value <=maximum: raise ValueError("int")
  return value
def sha(value:object)->str:
  result=text(value)
  need(re.fullmatch("[0-9a-f]{64}",result) is not None,"SHA256")
  return result
def absolute(value:object)->str:
  result=text(value)
  need(PureWindowsPath(result).is_absolute(),"absolute path")
  return str(Path(result).resolve())
def parse_ref(value:object)->FileRef:
  row=obj(value,frozenset(("path","bytes","sha256")))
  size=uint(row["bytes"])
  need(size > 0,"empty file ref")
  return FileRef(absolute(row["path"]),size,sha(row["sha256"]))
def content_ref(value:object)->FileRef:
  row=obj(value)
  return parse_ref({key:row[key] for key in ("path","bytes","sha256")})
def verified(ref:FileRef,*,capture:bool)->bytes:
  path=Path(ref.path)
  before=path.stat()
  need(before.st_size==ref.bytes and (not capture or ref.bytes <=1048576),
     "size/limit")
  digest=hashlib.sha256()
  retained=bytearray()
  with path.open("rb") as stream:
    for block in iter(lambda:stream.read(1048576),b""):
      digest.update(block)
      if capture:
        retained.extend(block)
  after=path.stat()
  need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
     (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),
     "changed")
  need(digest.hexdigest()==ref.sha256,"SHA")
  return bytes(retained)
def metadata(ref:FileRef)->dict[str,object]:
  value:object=json.loads(verified(ref,capture=True))
  return obj(value)
def rows(value:object)->list[dict[str,object]]:
  if type(value) is not list: raise ValueError("list")
  return [obj(item) for item in value]
def export_rows(value:object)->tuple[tuple[str,int],...]:
  result:list[tuple[str,int]]=[]
  seen:set[str]=set()
  for row in rows(value):
    name=text(row["name"])
    need(name not in seen and name in CALLS|{DATA},"export names")
    seen.add(name)
    raw=text(row["rva"])
    need(re.fullmatch("0x[0-9a-fA-F]+",raw) is not None,"hex RVA")
    rva=int(raw,16)
    need(0 < rva <=2**32-1 and row["forwarded"] is False,"RVA")
    need(row["executable"] is (name!=DATA),"export type")
    need(row["section"]==(".data" if name==DATA else ".text"),"section")
    result.append((name,rva))
  need(seen==CALLS|{DATA},"exports")
  return tuple(sorted(result))
def load_target(target_ref:RefJSON,*,machine_id:str)->TargetV1:
  ref=parse_ref(target_ref)
  row=obj(metadata(ref),frozenset(("schema","machine_id","status",
   "native_build_label","dll","qualification","observed_at_utc")))
  need(row["schema"]==TARGET and
   row["machine_id"]==text(machine_id) and
   row["status"]==OFFLINE,"target")
  utc(row["observed_at_utc"])
  dll=parse_ref(row["dll"])
  qualification=parse_ref(row["qualification"])
  q=metadata(qualification)
  need(q["schema"]=="xar.native31.independent-offline-production-qualification/v1" and
   q["machine_id"]==machine_id and q["status"]==row["status"] and
   q["runtime_qualified"] is False and q["source_unchanged"] is True and
   uint(q["Game_calls"])==0,"qualification")
  matches=[item for item in rows(q["outputs"]) if absolute(item["path"])==dll.path]
  need(len(matches)==1,"DLL output")
  output=matches[0]
  need(uint(output["bytes"])==dll.bytes and sha(output["sha256"])==dll.sha256,
   "DLL pin")
  verified(dll,capture=False)
  st=Path(dll.path).stat()
  need(str(st.st_ino)==text(output["file_id"]) and str(st.st_dev)==text(output["device"])
   and str(st.st_mtime_ns)==text(output["mtime_ns"]),"DLL identity")
  exports=export_rows(q["exports"])
  for key in ("postcheck","fixture"):
    verified(content_ref(q[key]),capture=False)
  need(uint(q["cpp_test_processes_passed"])==32 and
    uint(q["candidate_DLL_loads"])==0,"offline counts")
  return TargetV1(ref,text(row["native_build_label"]),dll,qualification,exports)
def bind(source:FileRef,target:TargetV1,machine_id:str)->BindingV1:
  freeze=metadata(source)
  need(freeze["schema"]=="root.ck3.final-sdk-freeze/v1" and
    freeze["status"]=="FINAL_SOURCE_FROZEN" and freeze["machine_id"]==machine_id,
    "source")
  return BindingV1("STATIC_SOURCE_BOUND_NOT_LOADED",target,source,
    absolute(freeze["source_root"]),text(freeze["git_head"]),
    sha(freeze["native_dll_sha256"]),ColdGuards())
def compose_binding(source_freeze:RefJSON,target_pin:RefJSON,*,
                    machine_id:str,observed_at_utc:str)->bytes:
  source=parse_ref(source_freeze)
  target=load_target(target_pin,machine_id=machine_id)
  bind(source,target,machine_id)
  value={"schema":SCHEMA,"machine_id":machine_id,
    "observed_at_utc":utc(observed_at_utc),"status":STATIC,
    "source_freeze":source.json(),"native_target":target.metadata.json(),
    "freeze_scope":"SDK_only_history_kept"}
  return json.dumps(value,sort_keys=True,separators=(",",":")).encode("utf-8")
def load_static_binding(binding_ref:RefJSON,*,machine_id:str)->BindingV1:
  row=obj(metadata(parse_ref(binding_ref)),frozenset(("schema","machine_id",
    "observed_at_utc","status","source_freeze","native_target","freeze_scope")))
  utc(row["observed_at_utc"])
  need(row["schema"]==SCHEMA and row["machine_id"]==text(machine_id) and
    row["status"]==STATIC and row["freeze_scope"]=="SDK_only_history_kept",
    "binding")
  source=parse_ref(row["source_freeze"])
  target=load_target(parse_ref(row["native_target"]).json(),machine_id=machine_id)
  return bind(source,target,machine_id)
def launch_values(binding:BindingV1)->LaunchValues:
  return {"native_build_label":binding.target.label,"dll_sha256":binding.target.dll.sha256,
   "git_head":binding.git_head,"dll":binding.target.dll.path,
   "build_receipt":binding.target.qualification.path}
