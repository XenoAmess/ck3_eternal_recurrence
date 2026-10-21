"""Typed current saved consumers."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
from typing import Literal,Protocol
from tools.g2_saved_campaign.current_saved_basis_v1 import (
 BasisReaderV1,CurrentSavedBasisV1,ExactRefV1,JsonObject,JsonValue,json_value,
 SavedFrameV1,ValidatedCurrentSavedBasisV1,
 READONLY_COLD_FAILURE_EPOCH_SCHEMA,parse_readonly_cold_failure_epoch_v1,
 validate_readonly_cold_failure_evidence_v1,
 READONLY_COLD_FAILURE_QUALIFICATION_SCHEMA,ReadonlyColdFailureQualificationV1,
 parse_readonly_cold_failure_qualification_v1,
 decode_current_saved_basis_v1,digest,encode_current_saved_basis_v1,
 completed_body,evidence,exact_read,integer,json_object,need,
 parse_frame,parse_json,parse_ref,record,rows,text,utc,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import SCHEMA as STAT_SCHEMA,FileStatIdentityV1,parse_file_stat_identity_v1,normalize_file_stat_identity_v1
QUALIFICATION_SCHEMA="xar.current-saved-basis-qualification/v1"
CURRENT_INPUTS_SCHEMA="xar.current-saved-cold-inputs/v1"
PRELAUNCH_SCHEMA="xar.current-saved-cold-prelaunch/v1"
CURRENT_SAVED_COLD_KIND="current_saved_checkpoint_cold_verified_v1"
UINT64_MAX=(1 << 64) - 1
PID_MAX=(1 << 32) - 1
def _same_json(first:object,second:object)->bool:
 return json.dumps(json_value(first),sort_keys=True,allow_nan=False)==json.dumps(json_value(second),sort_keys=True,allow_nan=False)
def _same_path(first:str,second:str)->bool:
 return Path(first).resolve()==Path(second).resolve()
def _clone(value:object)->JsonObject:
 return json_object(value)
def _exact_null(row:dict[str,object],name:str)->None:
 need(name in row and row[name] is None,"required null: "+name)
def _birth(value:object,*,legacy_python:bool=False)->str:
 if legacy_python and type(value) is int:
  need(0 < value <=UINT64_MAX,'legacy Python FILETIME r')
  return str(value)
 result=text(value)
 need(re.fullmatch("[1-9][0-9]*",result) is not None
   and int(result) <=UINT64_MAX,'canonical FILETIME decim')
 return result
def _identity(value:object)->FileStatIdentityV1:
 return parse_file_stat_identity_v1(value,schema=STAT_SCHEMA)
def _review_identity(value:object)->FileStatIdentityV1:
 r=record(value,{"bytes","file_id","device","mtime_ns","links"})
 need(integer(r["links"],1)==1 and re.fullmatch("0|[1-9][0-9]*",text(r["device"])) is not None,"review identity")
 return _identity({k:r[k] for k in ("bytes","file_id","mtime_ns")})
def _ref_record(reader:BasisReaderV1,value:object,limit:int=262144)->dict[str,object]:
 return evidence(reader,parse_ref(value),limit)
def _clean(value:object)->JsonObject:
 out=_clone(value)
 row=record(out)
 for name in ("pending_cycle","pending_checkpoint","terminal"):
  _exact_null(row,name)
 for name in ("pending_natural_succession","pending_unsafe_route_halt"):
  need(name not in row or row[name] is None,"unsettled optional field: "+name)
 need(row.get("schema")=="g2.queue.cumulative-loop/v1","loop state schema")
 return out
class LocalBasisReaderV1:
 def stat(self,path:str)->FileStatIdentityV1:
  result=os.stat(path,follow_symlinks=False)
  need(not bool(getattr(result,"st_file_attributes",0) & 0x400),"reparse input denied")
  return normalize_file_stat_identity_v1(result)
 def read(self,reference:ExactRefV1,limit:int)->bytes:
  need(reference.bytes <=limit,"bounded source read")
  before=self.stat(reference.path)
  with Path(reference.path).open("rb") as stream:
   raw=stream.read(limit+1)
  need(len(raw) <=limit and self.stat(reference.path)==before,'source changed during re')
  return raw

 def read_driver_header(self,path:str,limit:int)->bytes:
  need(type(limit) is int and 0<limit<=16384,"bounded current header")
  before=self.stat(path)
  with Path(path).open("rb") as stream:raw=stream.read(limit)
  need(self.stat(path)==before,"Driver changed while reading header")
  return raw
 def process_identity(self,pid:int)->JsonObject:
  # Narrow read-only native boundary; explicit prototypes and checked outputs.
  import ctypes
  integer(pid,1,PID_MAX)
  kernel=ctypes.WinDLL("kernel32",use_last_error=True)
  kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];kernel.OpenProcess.restype=ctypes.c_void_p
  kernel.GetProcessTimes.argtypes=[ctypes.c_void_p,*([ctypes.POINTER(ctypes.c_ulonglong)]*4)];kernel.GetProcessTimes.restype=ctypes.c_int
  kernel.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)];kernel.QueryFullProcessImageNameW.restype=ctypes.c_int
  kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];kernel.WaitForSingleObject.restype=ctypes.c_ulong
  kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle.restype=ctypes.c_int
  handle=kernel.OpenProcess(0x101000,False,pid)
  need(bool(handle),"query process handle")
  try:
   need(kernel.WaitForSingleObject(handle,0)==258,"actual process running")
   birth=ctypes.c_ulonglong();exited=ctypes.c_ulonglong();user=ctypes.c_ulonglong();system=ctypes.c_ulonglong()
   need(bool(kernel.GetProcessTimes(handle,ctypes.byref(birth),ctypes.byref(exited),ctypes.byref(system),ctypes.byref(user))),"actual kernel birth")
   size=ctypes.c_ulong(32768);image=ctypes.create_unicode_buffer(size.value)
   need(bool(kernel.QueryFullProcessImageNameW(handle,0,image,ctypes.byref(size))) and kernel.WaitForSingleObject(handle,0)==258,"actual live process image")
   return {"pid":pid,"creation_filetime":_birth(str(birth.value)),"executable":text(image.value)}
  finally:kernel.CloseHandle(handle)

@dataclass(frozen=True,slots=True)
class BasisQualificationV1:
 machine_id:str
 observed_at_utc:str
 basis_ref:ExactRefV1
 driver_ref:ExactRefV1
 save_ref:ExactRefV1
 driver_identity_before:FileStatIdentityV1
 driver_identity_after:FileStatIdentityV1
 save_identity_before:FileStatIdentityV1
 save_identity_after:FileStatIdentityV1
 validator_source_ref:ExactRefV1
 driver_history_rows:int
 driver_body_reads:int
 canonical_checkpoint_validator_calls:int
 save_hash_reads:int
 def __post_init__(self)->None:
  text(self.machine_id)
  utc(self.observed_at_utc)
  integer(self.driver_history_rows,1)
  need(type(self.driver_body_reads) is int and self.driver_body_reads==1
    and type(self.canonical_checkpoint_validator_calls) is int
    and self.canonical_checkpoint_validator_calls==1
    and type(self.save_hash_reads) is int and self.save_hash_reads==1,
    'this qualification has o')
  need(self.driver_identity_before==self.driver_identity_after
    and self.save_identity_before==self.save_identity_after,
    'stable qualification ide')
 def to_wire(self)->JsonObject:
  return {"schema":QUALIFICATION_SCHEMA,"machine_id":self.machine_id,
   "observed_at_utc":self.observed_at_utc,"basis_ref":self.basis_ref.to_wire(),
   "driver_ref":self.driver_ref.to_wire(),"save_ref":self.save_ref.to_wire(),
   "driver_identity_before":json_object(self.driver_identity_before.to_wire()),
   "driver_identity_after":json_object(self.driver_identity_after.to_wire()),
   "save_identity_before":json_object(self.save_identity_before.to_wire()),
   "save_identity_after":json_object(self.save_identity_after.to_wire()),
   "validator_source_ref":self.validator_source_ref.to_wire(),
   "driver_history_rows":self.driver_history_rows,
   "driver_body_reads":self.driver_body_reads,
   "canonical_checkpoint_validator_calls":self.canonical_checkpoint_validator_calls,
   "save_hash_reads":self.save_hash_reads,
   "read_count_scope":"this_additional_qualification_only",
   "power_loss_durability":"not_asserted"}
def parse_basis_qualification_v1(value:object,*,expected_machine_id:str)->BasisQualificationV1|ReadonlyColdFailureQualificationV1:
 if record(value).get("schema")==READONLY_COLD_FAILURE_QUALIFICATION_SCHEMA:
  return parse_readonly_cold_failure_qualification_v1(value,expected_machine_id=expected_machine_id)
 row=record(value,{"schema","machine_id","observed_at_utc","basis_ref",
  "driver_ref","save_ref","driver_identity_before","driver_identity_after",
  "save_identity_before","save_identity_after","validator_source_ref",
  "driver_history_rows","driver_body_reads","canonical_checkpoint_validator_calls",
  "save_hash_reads","read_count_scope","power_loss_durability"})
 need(row["schema"]==QUALIFICATION_SCHEMA and row["machine_id"]==expected_machine_id
   and row["read_count_scope"]=="this_additional_qualification_only"
   and row["power_loss_durability"]=="not_asserted","qualification contract")
 return BasisQualificationV1(text(row["machine_id"]),utc(row["observed_at_utc"]),
  parse_ref(row["basis_ref"]),parse_ref(row["driver_ref"]),parse_ref(row["save_ref"]),
  _identity(row["driver_identity_before"]),_identity(row["driver_identity_after"]),
  _identity(row["save_identity_before"]),_identity(row["save_identity_after"]),
  parse_ref(row["validator_source_ref"]),integer(row["driver_history_rows"],1),
  integer(row["driver_body_reads"]),integer(row["canonical_checkpoint_validator_calls"]),
  integer(row["save_hash_reads"]))
def build_basis_qualification_v1(
 validated:ValidatedCurrentSavedBasisV1,*,basis_ref:ExactRefV1,
 reader:BasisReaderV1,observed_at_utc:str,
)->BasisQualificationV1:
 basis=validated.basis
 need(_same_json(parse_json(exact_read(reader,basis_ref,65536)),
   parse_json(encode_current_saved_basis_v1(basis))),
   'qualification binds exac')
 need(reader.stat(basis.refs.save.path)==basis.save_identity,
   'actual post-qualificatio')
 return BasisQualificationV1(basis.machine_id,observed_at_utc,basis_ref,
  basis.refs.driver,basis.refs.save,basis.driver_identity,basis.driver_identity,
  basis.save_identity,basis.save_identity,basis.refs.checkpoint_validator,
  validated.driver_history_rows,validated.driver_body_reads,
  validated.canonical_checkpoint_validator_calls,1)
@dataclass(frozen=True,slots=True)
class CurrentGameIdentityV1:
 pid:int
 creation_filetime:str
 creation_date:str
 def __post_init__(self)->None:
  integer(self.pid,1,PID_MAX)
  _birth(self.creation_filetime)
  text(self.creation_date)
 def to_wire(self)->JsonObject:
  return {"pid":self.pid,"creation_filetime":self.creation_filetime,
    "creation_date":self.creation_date}
 def to_ledger(self)->JsonObject:
  return {"pid":self.pid,"creation_date":self.creation_date}
def parse_current_game_identity_v1(value:object,*,legacy_python:bool=False)->CurrentGameIdentityV1:
 row=record(value)
 return CurrentGameIdentityV1(integer(row.get("pid"),1,PID_MAX),
  _birth(row.get("creation_filetime"),legacy_python=legacy_python),
  text(row.get("creation_date")))
@dataclass(frozen=True,slots=True)
class ClosedSdkProcessV1:
 role:Literal["sdk_queue","sdk_application"]
 pid:int
 creation_filetime:str
 executable:str
 exit_code:int
@dataclass(frozen=True,slots=True)
class ClosedEpochV1:
 closure_ref:ExactRefV1
 old_game:CurrentGameIdentityV1
 next_sequence:int
 sdk_processes:tuple[ClosedSdkProcessV1,...]
 observed_at_utc:str
 pipe_name:str
def _sdk_processes(value:object)->tuple[ClosedSdkProcessV1,...]:
 found:list[ClosedSdkProcessV1]=[]
 for item in rows(value):
  row=record(item)
  role=row.get("role")
  if role=="sdk_queue":
   role_name:Literal["sdk_queue","sdk_application"]="sdk_queue"
  elif role=="sdk_application":
   role_name="sdk_application"
  else:raise ValueError("exact SDK role")
  need(row.get("kernel_exit_observed") is True and type(row.get("wait_result")) is int
    and row["wait_result"]==0 and type(row.get("exit_code")) is int
    and row["exit_code"]==0 and "observation_error" in row
    and row["observation_error"] is None,'actual normal SDK kernel')
  found.append(ClosedSdkProcessV1(role_name,integer(row.get("pid"),1,PID_MAX),
   _birth(row.get("creation_filetime"),legacy_python=True),
   text(row.get("executable")),integer(row["exit_code"])))
 need(len(found)==2 and {item.role for item in found}=={"sdk_queue","sdk_application"}
   and len({(item.pid,item.creation_filetime) for item in found})==2,
   'two actual SDK generatio')
 return tuple(sorted(found,key=lambda item:item.role))
def _validate_task_closure(
 sources:dict[str,object],key:str,*,reader:BasisReaderV1,machine_id:str,
)->None:
 spec_ref=parse_ref(sources[key])
 spec=evidence(reader,spec_ref,16384)
 closed=_ref_record(reader,sources[key[:-5]+"_CLOSED"],16384)
 nonce=text(spec.get("nonce"))
 need(spec.get("machine_id")==machine_id==closed.get("machine_id")
   and closed.get("nonce")==nonce and closed.get("spec_sha256")==spec_ref.sha256
   and spec.get("task_name")=="XARG2ManagedOwner-"+nonce,
   'actual Task generation c')
 need(type(closed.get("job_active_after_stage")) is int and closed["job_active_after_stage"]==0
   and closed.get("forced_remaining_cleanup") is False
   and type(closed.get("bootstrap_exit_code")) is int
   and type(closed.get("child_exit_code")) is int
   and closed["bootstrap_exit_code"]==closed["child_exit_code"],"Task owned Job closed")
 matching=0
 for name,value in sources.items():
  if not name.endswith("UNREGISTER01.json"):
   continue
  outer=_ref_record(reader,value,16384)
  command=rows(outer.get("command"))
  if "--spec" not in command:
   continue
  index=command.index("--spec")
  if index+1 >=len(command) or not _same_path(text(command[index+1]),spec_ref.path):
   continue
  need(outer.get("machine_id")==machine_id and type(outer.get("returncode")) is int
    and outer["returncode"]==0,'actual Task unregister r')
  inner=record(parse_json(text(outer.get("stdout")).encode("utf-8")))
  actual=record(inner.get("actual"))
  need(inner.get("machine_id")==machine_id and inner.get("task_name")==spec["task_name"]
    and inner.get("operation")=="unregister" and actual.get("absent_after") is True,
    'actual Task absent after')
  matching+=1
 need(matching==1,'one exact Task unregiste')
def _closed_epoch(basis:CurrentSavedBasisV1,reader:BasisReaderV1)->ClosedEpochV1:
 closure=evidence(reader,basis.refs.closure,65536)
 if closure.get("schema")==READONLY_COLD_FAILURE_EPOCH_SCHEMA:
  epoch=parse_readonly_cold_failure_epoch_v1(closure,expected_machine_id=basis.machine_id)
  checked=validate_readonly_cold_failure_evidence_v1(epoch,reader=reader)
  business=checked.business_basis
  need(checked.driver_ref==basis.refs.driver and checked.driver_identity==basis.driver_identity
   and checked.save_ref==basis.refs.save and checked.save_identity==basis.save_identity
   and epoch.refs.driver_review==basis.refs.driver_close and epoch.refs.next==basis.refs.next
   and checked.next_sequence==basis.next_sequence and business.origin==basis.origin
   and business.frame==basis.frame and business.completed_cycles==basis.completed_cycles
   and _same_json(business.checkpoint,basis.checkpoint)
   and _same_json(business.campaign_goal_anchor,basis.campaign_goal_anchor)
   and checked.history_count==integer(basis.checkpoint.get("history_index"),1)+1,"qualified readonly failed epoch frontier")
  game=checked.old_game
  processes=tuple(ClosedSdkProcessV1(p.role,p.pid,p.creation_filetime,p.executable,p.exit_code) for p in checked.sdk_processes)
  return ClosedEpochV1(basis.refs.closure,CurrentGameIdentityV1(game.pid,game.creation_filetime,game.creation_date),
   checked.next_sequence,processes,epoch.observed_at_utc,checked.pipe_name)
 need(closure.get("schema")=="xar.A20-actual-saved-progress-closure/v1"
   and closure.get("machine_id")==basis.machine_id
   and closure.get("all_three_Tasks_actual_absent") is True,
   'recognized actual predec')
 need(integer(closure.get("settled_cycles_after"))==basis.completed_cycles
   and integer(closure.get("actual_final_date_raw"))==basis.frame.date_raw
   and integer(closure.get("next_sequence"),1)==basis.next_sequence
   and closure.get("historical_unknown10565_replayed") is False
   and closure.get("original_whole_wall_origin")==basis.origin.original_wall_origin_utc,
   'current closed progress ')
 source=record(closure.get("sources"))
 sdk=_ref_record(reader,source["ROOT-P37C23-OWNER-CLOSED.json"],16384)
 need(sdk.get("machine_id")==basis.machine_id
   and sdk.get("status")=="ACTUAL_BOTH_SDK_EXITS_OBSERVED" and sdk.get("normal") is True,
   "old SDK actual closure")
 processes=_sdk_processes(sdk.get("processes"))
 codes=rows(closure.get("SDK_exit_codes"))
 need(len(codes)==2 and all(type(v) is int and v==0 for v in codes) and closure.get("SDK_normal") is True,"SDK summary agrees")
 supervisor=_ref_record(reader,source["ROOT-FRESH-SUPERVISOR-CLOSED-C23-A15.json"],16384)
 actual_exit=_ref_record(reader,source["ROOT-ACTUAL-GAME-EXIT-C23.json"],16384)
 owned=record(supervisor.get("owned_cleanup"))
 phase=record(supervisor.get("known_preload_phase"))
 before=record(phase.get("before")); after=record(phase.get("after"))
 old_game=CurrentGameIdentityV1(integer(actual_exit.get("pid"),1,PID_MAX),
  _birth(actual_exit.get("creation_filetime"),legacy_python=True),
  text(owned.get("ck3_creation_date")))
 need(supervisor.get("machine_id")==basis.machine_id==actual_exit.get("machine_id")
   and actual_exit.get("kernel_signaled") is True
   and type(actual_exit.get("exit_code")) is int
   and integer(owned.get("job_active_processes_final"))==0
   and owned.get("tree_gone") is True and owned.get("cleanup_proven") is True
   and owned.get("ok") is True and rows(owned.get("contract_errors"))==[]
   and integer(owned.get("ck3_pid"),1)==old_game.pid
   and integer(owned.get("ck3_exit_code"))==integer(actual_exit["exit_code"])
   and integer(after.get("pid"),1)==integer(before.get("pid"),1)==old_game.pid
  and _birth(after.get("creation_filetime"),legacy_python=True)==old_game.creation_filetime
   and _birth(before.get("creation_filetime"),legacy_python=True)==old_game.creation_filetime,
   'actual old Game kernel/o')
 sdk_again=record(supervisor.get("sdk_actual_exit"))
 need(sdk_again.get("status")==sdk["status"]
   and _sdk_processes(sdk_again.get("processes"))==processes,
   'supervisor and SDK closu')
 for flag in ("forced_owned_job_cleanup","normal_wm_close_qualified"):
  need(type(actual_exit.get(flag)) is bool,'Game closure classificat')
 need(integer(closure.get("Game_exit_code"))==integer(actual_exit["exit_code"])
   and closure.get("Game_forced") is actual_exit["forced_owned_job_cleanup"]
   and closure.get("Game_normal_close_qualified") is actual_exit["normal_wm_close_qualified"]
   and integer(closure.get("Game_Job_active_final"))==0,
   'closure preserves forced')
 spec_keys=[key for key in source if key.endswith("_SPEC")]
 need(len(spec_keys)==3,'three actual predecessor')
 for key in spec_keys:
  _validate_task_closure(source,key,reader=reader,machine_id=basis.machine_id)
 release_key=next((key for key in source if "SCREEN" in key and "RELEASE" in key),None)
 need(release_key is not None,'actual screen release ev')
 if release_key is None:
  raise ValueError("screen release")
 release=_ref_record(reader,source[release_key],16384)
 need(release.get("machine_id")==basis.machine_id and type(release.get("returncode")) is int
   and release["returncode"]==0,'actual screen release re')
 released=record(parse_json(text(release.get("stdout")).encode("utf-8")))
 task=record(released.get("task"))
 keeper=record(supervisor.get("keeper"))
 need(released.get("ok") is True and task.get("state")=="done"
   and rows(task.get("resources"))==[] and task.get("task_id")==keeper.get("task_id")
   and keeper.get("thread_exited") is True and keeper.get("failure") is None
   and integer(task.get("last_sequence"),1)==integer(keeper.get("last_sequence"),1)+1,
   'actual stopped Keeper an')
 review=evidence(reader,basis.refs.driver_close,16384)
 driver=record(review.get("Driver")); save=record(review.get("SAVE"))
 need(review.get("machine_id")==basis.machine_id
   and review.get("schema")=="xar.A20-final-Driver-SAVE-review/v2"
   and review.get("status")=="CLOSED_DRIVER_FINAL_SAVE_MATCH"
   and parse_ref(driver.get("ref"))==basis.refs.driver
   and parse_ref(save.get("ref"))==basis.refs.save
   and _review_identity(driver.get("identity"))==basis.driver_identity
   and _review_identity(save.get("identity"))==basis.save_identity
   and integer(driver.get("format_version"))==2
   and integer(driver.get("command_history_count"),1)==integer(basis.checkpoint["history_index"],1),
   'actual corrected closed ')
 need(parse_ref(review.get("frozen_settled_Queue"))==basis.refs.settled_state
   and parse_ref(review.get("frozen_continuity_ledger"))==basis.refs.ledger
   and integer(record(review.get("actual_next")).get("next_sequence"),1)==basis.next_sequence,
   'Driver close actual stat')
 recorded=record(driver.get("recorded_identity"))
 need(integer(recorded.get("bridge_pid"),1)==old_game.pid
   and integer(recorded.get("episode_character_id"),1)==basis.frame.actor_character_id
   and recorded.get("episode_run_id")==basis.frame.episode_run_id
   and "session_binding" not in recorded,'actual Driver direct ide')
 return ClosedEpochV1(basis.refs.closure,old_game,basis.next_sequence,processes,
  utc(closure.get("observed_at_utc")),text(recorded.get("pipe_name")))
@dataclass(frozen=True,slots=True)
class CurrentSavedColdInputsV1:
 basis:CurrentSavedBasisV1
 seed:JsonObject
 governance:JsonObject
 checkpoint:JsonObject
 old_ledger:JsonObject
 closed_epoch:ClosedEpochV1
 basis_ref:ExactRefV1
 validation_ref:ExactRefV1
def project_current_saved_seed_v1(basis:CurrentSavedBasisV1,*,reader:BasisReaderV1)->JsonObject:
 seed=_clean(evidence(reader,basis.refs.seed))
 need(integer(seed.get("completed_cycles"))==basis.completed_cycles
   and integer(seed.get("start_date_raw"))==basis.origin.start_date_raw
   and parse_frame(seed.get("before"))==basis.frame
   and _same_json(seed.get("campaign_goal_anchor"),basis.campaign_goal_anchor),
   'one actual saved seed fr')
 checkpoint=record(seed.get("actual_saved_checkpoint"))
 need(checkpoint.get("status")=="saved" and checkpoint.get("path")==basis.checkpoint["path"]
   and integer(checkpoint.get("size"))==basis.checkpoint["size"]
   and checkpoint.get("sha256")==basis.checkpoint["sha256"]
   and integer(checkpoint.get("date_raw"))==basis.checkpoint["saved_date_raw"]
   and integer(checkpoint.get("history_index"))==basis.checkpoint["history_index"]
   and _same_json(checkpoint.get("succession_lifecycle"),basis.checkpoint["succession_lifecycle"])
   and integer(checkpoint.get("episode_character_id"))==basis.frame.actor_character_id
   and checkpoint.get("episode_run_id")==basis.frame.episode_run_id,
   'seed actual raw checkpoi')
 need(integer(record(seed.get("counts")).get("checkpoint_saved"))==basis.progress.checkpoint_count_after,
   'actual maintenance SAVE ')
 return seed
def _validated_immutable_inputs_v1(
 basis:CurrentSavedBasisV1,*,basis_ref:ExactRefV1,validation_ref:ExactRefV1,
 reader:BasisReaderV1,
)->CurrentSavedColdInputsV1:
 need(_same_json(parse_json(exact_read(reader,basis_ref,65536)),
   parse_json(encode_current_saved_basis_v1(basis))),
   'exact current saved basi')
 qualification=parse_basis_qualification_v1(
  evidence(reader,validation_ref,16384),expected_machine_id=basis.machine_id)
 need(qualification.basis_ref==basis_ref
   and qualification.driver_ref==basis.refs.driver and qualification.save_ref==basis.refs.save
   and qualification.validator_source_ref==basis.refs.checkpoint_validator
   and qualification.driver_identity_after==basis.driver_identity
   and qualification.save_identity_after==basis.save_identity,
   'actual one-read canonica')
 if isinstance(qualification,ReadonlyColdFailureQualificationV1):
  failure=parse_readonly_cold_failure_epoch_v1(evidence(reader,basis.refs.closure,65536),expected_machine_id=basis.machine_id)
  need(qualification.epoch_ref==basis.refs.closure and qualification.canonical_qualification_ref==failure.refs.canonical_qualification,'readonly failure qualification source')
 exact_read(reader,basis.refs.checkpoint_validator,65536)
 need(reader.stat(basis.refs.save.path)==basis.save_identity,
   'no Driver or SAVE identi')
 for name,reference in basis.refs.items():
  if name not in {"driver","save","checkpoint_validator"}:
   evidence(reader,reference,1048576)
 seed=project_current_saved_seed_v1(basis,reader=reader)
 governance=_clone(evidence(reader,basis.refs.governance))
 need("pending_cycle" in governance and governance["pending_cycle"] is None
   and integer(governance.get("completed_cycles"))==basis.completed_cycles,
   'current settled governan')
 ledger=_clone(evidence(reader,basis.refs.ledger))
 need(ledger.get("machine_id")==basis.machine_id
   and integer(ledger.get("last_settled_cycles"))==basis.progress.ledger_cycles
   and integer(ledger.get("last_settled_date_raw"))==basis.progress.ledger_date_raw
   and integer(ledger.get("start_date_raw"))==basis.origin.start_date_raw
   and integer(ledger.get("target_date_raw"))==basis.origin.target_date_raw
   and integer(ledger.get("target_days"))==basis.origin.target_days,'explicit original ledger')
 closed=_closed_epoch(basis,reader)
 return CurrentSavedColdInputsV1(basis,seed,governance,
  _clone(seed["actual_saved_checkpoint"]),ledger,closed,basis_ref,validation_ref)
def load_current_saved_inputs_v1(
 *,runtime_root:Path,expected_machine_id:str,
)->CurrentSavedColdInputsV1:
 reader=LocalBasisReaderV1()
 path=runtime_root / "ROOT-CURRENT-SAVED-INPUTS01.json"
 need(path.stat().st_size <=16384,"bounded current inputs")
 row=record(parse_json(path.read_bytes()),{"schema","machine_id","basis_ref","validation_ref"})
 need(row["schema"]==CURRENT_INPUTS_SCHEMA and row["machine_id"]==expected_machine_id,
   'explicit current machine')
 basis_ref=parse_ref(row["basis_ref"]); validation_ref=parse_ref(row["validation_ref"])
 basis=decode_current_saved_basis_v1(exact_read(reader,basis_ref,65536),
  expected_machine_id=expected_machine_id)
 return validate_current_saved_cold_inputs_v1(basis,basis_ref=basis_ref,
  validation_ref=validation_ref,reader=reader)
@dataclass(frozen=True, slots=True)
class CurrentSavedStatePathsV1:
 state_root:str
 profile_dir:str
 environment_manifest:str
 driver_state_path:str
 checkpoint_path:str
 def to_wire(self)->JsonObject:
  return {"state_root":self.state_root,"profile_dir":self.profile_dir,
   "environment_manifest":self.environment_manifest,
   "driver_state_path":self.driver_state_path,"checkpoint_path":self.checkpoint_path}

def derive_current_saved_state_paths_v1(basis:CurrentSavedBasisV1)->CurrentSavedStatePathsV1:
 """Derive the shared state from both qualified files, never from a new attempt."""
 driver=ntpath.normpath(text(basis.refs.driver.path))
 saved=ntpath.normpath(text(basis.refs.save.path))
 checkpoint=ntpath.normpath(text(basis.checkpoint.get("path")))
 need(all(ntpath.isabs(path) for path in (driver,saved,checkpoint)),"absolute shared state inputs")
 state=ntpath.dirname(ntpath.dirname(driver));profile=ntpath.join(state,"profile")
 need(ntpath.normcase(driver)==ntpath.normcase(ntpath.join(state,"native-session","driver-state.json"))
  and ntpath.normcase(saved)==ntpath.normcase(checkpoint)
  and ntpath.normcase(ntpath.dirname(checkpoint))==ntpath.normcase(ntpath.join(profile,"save games")),
  "Driver and checkpoint must share one existing state root")
 return CurrentSavedStatePathsV1(state,profile,ntpath.join(profile,"xar-autoplayer-environment.json"),driver,checkpoint)

def validate_current_saved_state_manifest_v1(basis:CurrentSavedBasisV1,manifest:object)->CurrentSavedStatePathsV1:
 paths=derive_current_saved_state_paths_v1(basis);row=record(manifest)
 need(row.get("machine_id")==basis.machine_id,"shared state manifest machine")
 for name,expected in (("state_dir",paths.state_root),("profile_dir",paths.profile_dir)):
  need(ntpath.normcase(ntpath.normpath(text(row.get(name))))==ntpath.normcase(expected),
   "shared state manifest path: "+name)
 lifecycle=record(basis.checkpoint.get("succession_lifecycle"))
 need(digest(row.get("environment_sha256"))==digest(lifecycle.get("environment_sha256")),
  "shared state manifest checkpoint environment")
 return paths

def build_current_saved_prelaunch_v1(
 basis:CurrentSavedBasisV1,*,basis_ref:ExactRefV1,validation_ref:ExactRefV1,
 environment_sha256:str,pipe_name:str,
)->JsonObject:
 digest(environment_sha256); text(pipe_name)
 return {"schema":PRELAUNCH_SCHEMA,"machine_id":basis.machine_id,
  "status":"CLOSED_CURRENT_SAVED_CHECKPOINT_VALIDATED",
  "basis_ref":basis_ref.to_wire(),"validation_ref":validation_ref.to_wire(),
  "checkpoint":_clone(basis.checkpoint),"environment_sha256":environment_sha256,
  "pipe_name":pipe_name,"original_wall_start_utc":basis.origin.original_wall_origin_utc,
  "completed_cycles":basis.completed_cycles,"date_raw":basis.frame.date_raw,
  "next_sequence":basis.next_sequence,"driver_close_ref":basis.refs.driver_close.to_wire(),
  "closure_ref":basis.refs.closure.to_wire(),"ordinary_cycle_credit":0,
  "game_day_credit":0,"original_actions_replayed":False,
  "power_loss_durability":"not_asserted"}
def cold_inputs_v1(
 admission:object,*,runtime_root:Path,expected_machine_id:str,
)->tuple[JsonObject,JsonObject,JsonObject,JsonObject,JsonObject]:
 row=record(admission)
 inputs=load_current_saved_inputs_v1(runtime_root=runtime_root,
  expected_machine_id=expected_machine_id)
 need(row.get("machine_id")==expected_machine_id
   and parse_ref(row.get("basis_ref"))==inputs.basis_ref
   and parse_ref(row.get("validation_ref"))==inputs.validation_ref
   and integer(row.get("next_sequence"),1)==inputs.basis.next_sequence,
   'cold admission uses one ')
 reader=LocalBasisReaderV1()
 pre=_clone(_ref_record(reader,row.get("cold_prelaunch"),16384))
 need(pre.get("schema")==PRELAUNCH_SCHEMA
   and pre.get("machine_id")==expected_machine_id
   and pre.get("status")=="CLOSED_CURRENT_SAVED_CHECKPOINT_VALIDATED"
   and _same_json(pre.get("checkpoint"),inputs.basis.checkpoint)
   and parse_ref(pre.get("basis_ref"))==inputs.basis_ref
   and parse_ref(pre.get("validation_ref"))==inputs.validation_ref
   and integer(pre.get("next_sequence"),1)==inputs.basis.next_sequence
   and pre.get("original_wall_start_utc")==inputs.basis.origin.original_wall_origin_utc,
   'actual generic prelaunch')
 return (_clone(inputs.seed),_clone(inputs.governance),_clone(inputs.checkpoint),
  pre,{"schema":"xar.current-saved-closed-epoch-view/v1","machine_id":expected_machine_id,
   "source_ref":inputs.basis.refs.closure.to_wire(),
   "old_Game":inputs.closed_epoch.old_game.to_wire(),
   "next_sequence":inputs.closed_epoch.next_sequence})
class SemanticFrameDecoderV1(Protocol):
 def __call__(
  self,body:JsonObject,*,semantic:Literal[True],expected_lifecycle:JsonObject,
 )->object:...
def bind_current_saved_opening_v1(
 inputs:CurrentSavedColdInputsV1,body:object,*,launch:CurrentGameIdentityV1,
 frame_decoder:SemanticFrameDecoderV1,
)->SavedFrameV1:
 row=_clone(body)
 life=inputs.checkpoint.get("succession_lifecycle")
 need(type(life) is dict,'current ordinary success')
 lifecycle=_clone(life)
 actual=parse_frame(frame_decoder(row,semantic=True,expected_lifecycle=lifecycle))
 basis=inputs.basis
 need(actual.date_raw==basis.frame.date_raw
   and actual.actor_character_id==basis.frame.actor_character_id
   and actual.episode_run_id==basis.frame.episode_run_id,
   'new Game SEM loads curre')
 diagnostics=record(row.get("diagnostics")); hello=record(diagnostics.get("hello"))
 need(integer(diagnostics.get("bridge_pid"),1,PID_MAX)==launch.pid
   and integer(hello.get("pid"),1,PID_MAX)==launch.pid
   and integer(diagnostics.get("connection_generation"),1)
==integer(hello.get("connection_generation"),1)
  and diagnostics.get("pipe_name")==inputs.closed_epoch.pipe_name
   and hello.get("ck3_build_match") is True
   and hello.get("game_adapter_id")=="ck3-1.20.0.4-msvc-x64"
   and hello.get("game_adapter_status")=="ready"
   and _same_json(row.get("campaign_goal"),basis.campaign_goal_anchor),
   'actual current Native/co')
 need("active_event" in row and row["active_event"] is None
   and "pending_character_interaction" in row and row["pending_character_interaction"] is None,
   'actual opening has no un')
 need((launch.pid,launch.creation_filetime) !=
   (inputs.closed_epoch.old_game.pid,inputs.closed_epoch.old_game.creation_filetime),
   'actual fresh Game genera')
 return actual
def project_current_saved_opening_v1(
 inputs:CurrentSavedColdInputsV1,opening:SavedFrameV1,*,semantic_response:ExactRefV1,
)->JsonObject:
 basis=inputs.basis
 need(opening.date_raw==basis.frame.date_raw
   and opening.actor_character_id==basis.frame.actor_character_id
   and opening.episode_run_id==basis.frame.episode_run_id,"current saved opening")
 changed=_clone(inputs.seed)
 changed["before"]=opening.to_wire()
 changed["before_metrics_response"]=semantic_response.path
 changed["before_source_kind"]="actual_cold_semantic_snapshot"
 changed["cold_session_opening"]={"frame":opening.to_wire(),
  "semantic_response":semantic_response.path,"ordinary_cycle_credit":0,"game_day_credit":0}
 need(_same_json(changed["counts"],inputs.seed["counts"])
   and changed["completed_cycles"]==basis.completed_cycles
   and changed["start_date_raw"]==basis.origin.start_date_raw,'cold observation has zer')
 return changed
@dataclass(frozen=True,slots=True)
class CurrentSavedFeederV1:
 inputs:CurrentSavedColdInputsV1
 warm_proof:WarmBoundProofV1
 admission:JsonObject
 opening:SavedFrameV1
 game:CurrentGameIdentityV1
 cold_bound_ref:ExactRefV1
 map_admission_ref:ExactRefV1
 def expected_transition(self)->JsonObject:
  basis=self.inputs.basis
  return {"machine_id":basis.machine_id,
   "evidence_id":CURRENT_SAVED_COLD_KIND+":"+self.inputs.basis_ref.sha256
+":"+self.cold_bound_ref.sha256,
   "source":{"basis_ref":self.inputs.basis_ref.to_wire(),
    "validation_ref":self.inputs.validation_ref.to_wire(),
    "old_ledger_ref":basis.refs.ledger.to_wire(),
    "cold_bound_ref":self.cold_bound_ref.to_wire(),
    "map_admission_ref":self.map_admission_ref.to_wire(),
    "feeder_source_ref":self.admission["feeder_source_ref"],
    "progress":basis.progress.to_wire(),"warm_bound":self.warm_proof.to_wire()},
   "basis_ref":self.inputs.basis_ref.to_wire(),
   "old_ledger_ref":basis.refs.ledger.to_wire(),
   "frame":self.opening.to_wire(),"game":self.game.to_wire(),
   "new_ordinary_cycle_credit":0,"game_day_credit":0,
   "original_actions_replayed":False,"window_origin_reset":False}
def validate_current_saved_feeder_v1(
 warm:WarmCurrentSavedFeederInputsV1,admission:object,*,reader:BasisReaderV1,
 current_next_sequence:int,
)->CurrentSavedFeederV1:
 inputs=warm.inputs;proof=warm.warm_proof
 need(reader.stat(inputs.basis.refs.driver.path)==proof.driver_identity and reader.stat(inputs.basis.refs.save.path)==inputs.basis.save_identity,"actual warm file identity")
 row=record(admission)
 need(parse_ref(row.get("actual_game_ref"))==proof.sources.actual_game_ref and parse_ref(row.get("cold_bound_ref"))==proof.sources.cold_bound_ref and parse_ref(row.get("cold_admission_ref"))==proof.sources.cold_admission_ref,"same qualified warm sources")
 basis=inputs.basis
 need(row.get("schema")=="xar.current-saved-feeder-admission/v1"
   and row.get("machine_id")==basis.machine_id
   and parse_ref(row.get("basis_ref"))==inputs.basis_ref
   and integer(row.get("first_control_sequence"),1)==integer(current_next_sequence,1)
   and current_next_sequence >=basis.next_sequence+2,
   'actual new FULL follows ')
 need(integer(row.get("ordinary_cycle_credit"))==0 and integer(row.get("game_day_credit"))==0
   and row.get("original_actions_replayed") is False and row.get("window_origin_reset") is False,
   'feeder admission adds no')
 cold_bound_ref=parse_ref(row.get("cold_bound_ref"))
 marker=evidence(reader,cold_bound_ref,65536)
 opening=parse_frame(marker.get("opening_frame"))
 need(marker.get("schema")=="xar.c23.normal-checkpoint-cold-bound/v1"
   and marker.get("machine_id")==basis.machine_id
   and integer(marker.get("completed_cycles"))==basis.completed_cycles
   and integer(marker.get("T0_date_raw"))==basis.origin.start_date_raw
   and _same_json(marker.get("checkpoint"),inputs.checkpoint)
   and integer(marker.get("new_ordinary_cycle_credit"))==0
   and marker.get("AUTO_or_MET_replayed") is False,
   'actual cold SEM/CAP-boun')
 need(opening.date_raw==basis.frame.date_raw
   and opening.actor_character_id==basis.frame.actor_character_id
   and opening.episode_run_id==basis.frame.episode_run_id,
   'current saved opening ac')
 game_raw=_ref_record(reader,row.get("actual_game_ref"),65536)
 game=parse_current_game_identity_v1(game_raw,legacy_python=True)
 need(game_raw.get("old_save_loaded") is True and game_raw.get("load_save_name")=="xar_checkpoint"
   and (game.pid,game.creation_filetime) !=
   (inputs.closed_epoch.old_game.pid,inputs.closed_epoch.old_game.creation_filetime),
   'actual new Game loaded t')
 cold=_ref_record(reader,row.get("cold_admission_ref"),65536)
 need(cold.get("machine_id")==basis.machine_id and parse_ref(cold.get("basis_ref"))==inputs.basis_ref and parse_ref(cold.get("validation_ref"))==inputs.validation_ref and parse_current_game_identity_v1(cold.get("new_Game"),legacy_python=True)==game,'cold admission provenanc')
 map_admission_ref=parse_ref(row.get("map_admission_ref"))
 current=evidence(reader,map_admission_ref,65536)
 need(current.get("status")=="GREEN" and current.get("reviewer")=="/root"
   and current.get("machine_id")==basis.machine_id
   and integer(current.get("game_pid"),1,PID_MAX)==game.pid
   and _birth(current.get("game_creation_filetime"),legacy_python=True)==game.creation_filetime
   and _same_json(current.get("actual_initial_frame"),opening.to_wire()),'actual Root map/Game adm')
 active=_clean(_ref_record(reader,row.get("active_state_ref"),65536))
 need(_same_json(active.get("before"),opening.to_wire()) and integer(active.get("completed_cycles"))==basis.completed_cycles
   and integer(active.get("start_date_raw"))==basis.origin.start_date_raw
   and _same_json(active.get("counts"),inputs.seed["counts"])
   and _same_json(active.get("actual_saved_checkpoint"),inputs.checkpoint)
   and _same_json(active.get("campaign_goal_anchor"),basis.campaign_goal_anchor),
   'cold opening active stat')
 return CurrentSavedFeederV1(inputs,proof,_clone(row),opening,game,cold_bound_ref,map_admission_ref)
def transition_current_saved_cold_v1(
 previous:object,details:object,*,verified:CurrentSavedFeederV1,
)->JsonObject:
 old=_clone(previous)
 need(_same_json(old,verified.inputs.old_ledger) and _same_json(details,verified.expected_transition()),
   'exact frozen predecessor')
 basis=verified.inputs.basis
 need(integer(old.get("window_id"),1) >=1
   and old.get("status") in ("running","complete","repair_required")
   and integer(old.get("start_date_raw"))==basis.origin.start_date_raw
   and integer(old.get("target_date_raw"))==basis.origin.target_date_raw
   and integer(old.get("last_settled_cycles"))==basis.progress.ledger_cycles
   and integer(old.get("last_settled_date_raw"))==basis.progress.ledger_date_raw,
   'original continuity orig')
 changed=_clone(old)
 changed.update(status="complete" if basis.frame.date_raw >=basis.origin.target_date_raw else "running",
  game_binding=verified.game.to_ledger(),latest_binding=verified.opening.to_wire(),
  last_settled_cycles=basis.completed_cycles,last_settled_date_raw=basis.frame.date_raw,
  cold_handoff_count=integer(old.get("cold_handoff_count",0))+1,
  last_current_saved_cold=verified.expected_transition(),
  last_settled_source=basis.refs.settled_full_response.to_wire(),
  current_saved_reconciliation={"progress":basis.progress.to_wire(),
   "already_settled_alignment_cycles":basis.completed_cycles - basis.progress.ledger_cycles,
   "already_settled_alignment_date_raw":basis.frame.date_raw - basis.progress.ledger_date_raw,
   "ordinary_cycle_credit":0,"game_day_credit":0,"original_actions_replayed":False})
 if "interruption" in old:
  changed["previous_interruption"]=old["interruption"]
 allowed={"status","game_binding","latest_binding","last_settled_cycles",
  "last_settled_date_raw","cold_handoff_count","last_current_saved_cold",
  "last_settled_source","current_saved_reconciliation","previous_interruption"}
 need(all(_same_json(changed.get(key),value) for key,value in old.items() if key not in allowed),
   'origin/window/unknown hi')
 return changed
def project_completed_maintenance_save_v1(
 state:object,save_row:object,*,semantic_response:ExactRefV1,
 save_response:ExactRefV1,
)->JsonObject:
 original=_clean(state)
 before=parse_frame(original.get("before"))
 result=completed_body(record(save_row),"ck3_save_checkpoint")
 checkpoint=_clone(result.get("checkpoint"))
 need(checkpoint.get("status")=="saved"
   and integer(checkpoint.get("date_raw"))==before.date_raw
   and integer(checkpoint.get("episode_character_id"),1)==before.actor_character_id
   and checkpoint.get("episode_run_id")==before.episode_run_id,
   'actual maintenance SAVE ')
 integer(checkpoint.get("history_index"),1); integer(checkpoint.get("size"),1)
 digest(checkpoint.get("sha256")); text(checkpoint.get("path"))
 counts=_clone(original.get("counts"))
 previous_count=integer(counts.get("checkpoint_saved"))
 calendar_value=original.get("checkpoint_calendar_v1")
 calendar={} if calendar_value is None else record(calendar_value)
 accounted=(_same_json(original.get("actual_saved_checkpoint"),checkpoint)
  and original.get("checkpoint_dirty_since_save") is False
  and calendar.get("last_saved_date_raw")==before.date_raw)
 changed=_clone(original)
 counts["checkpoint_saved"]=previous_count+(0 if accounted else 1)
 changed["counts"]=counts
 changed["checkpoint_calendar_v1"]={"last_saved_date_raw":before.date_raw,
  "actor_character_id":before.actor_character_id,"episode_run_id":before.episode_run_id,
  "war_ids":json_object({"value":calendar.get("war_ids")})["value"]}
 changed["checkpoint_dirty_since_save"]=False
 changed["checkpoint_due_after_readonly_chain"]=False
 changed["actual_saved_checkpoint"]=checkpoint
 changed["actual_saved_checkpoint_source"]={"global_turn":integer(original.get("completed_cycles")),
  "semantic_response":semantic_response.path,"save_response":save_response.path,
  "source_kind":"typed_maintenance_save","ordinary_cycle_credit":0}
 allowed={"counts","checkpoint_calendar_v1","checkpoint_dirty_since_save",
  "checkpoint_due_after_readonly_chain","actual_saved_checkpoint","actual_saved_checkpoint_source"}
 need(all(_same_json(changed.get(key),value) for key,value in original.items() if key not in allowed)
   and all(_same_json(counts.get(key),value) for key,value in record(original["counts"]).items()
     if key !="checkpoint_saved"),'SAVE projection changes ')
 return changed
def validate_current_saved_old_generations_v1(
 admission:object,launch:object,*,runtime_root:Path,expected_machine_id:str,
)->None:
 inputs=load_current_saved_inputs_v1(runtime_root=runtime_root,
  expected_machine_id=expected_machine_id)
 current=parse_current_game_identity_v1(launch,legacy_python=True)
 row=record(launch)
 need((current.pid,current.creation_filetime) !=
   (inputs.closed_epoch.old_game.pid,inputs.closed_epoch.old_game.creation_filetime)
   and row.get("old_save_loaded") is True and row.get("load_save_name")=="xar_checkpoint",
   'actual fresh Game genera')
 data=record(admission)
 admitted=parse_current_game_identity_v1(data.get("new_Game"),legacy_python=True)
 need(admitted==current,'cold admission actual Ga')
def validate_current_saved_runtime_source_v1(
 admission:object,freeze:object,*,runtime_root:Path,expected_machine_id:str,
)->None:
 row=record(admission); frozen=record(freeze)
 machine_id=text(row.get("machine_id"));need(machine_id==expected_machine_id,"source machine")
 inputs=load_current_saved_inputs_v1(runtime_root=runtime_root,expected_machine_id=machine_id)
 need(parse_ref(row.get("basis_ref"))==inputs.basis_ref
   and parse_ref(row.get("validation_ref"))==inputs.validation_ref,
   'runtime source belongs t')
 reader=LocalBasisReaderV1()
 actual=_ref_record(reader,row.get("sdk_freeze"),2097152)
 need(_same_json(actual,frozen) and text(row.get("business_source_commit"))==text(frozen.get("business_source_commit")),
   'actual current SDK freez')
 generation=integer(row.get("business_source_generation"),31,32)
 base=_ref_record(reader,row.get("sdk_base_ref"),1048576)
 anchor_ref=parse_ref(row.get("sdk_anchor_ref"))
 anchor=evidence(reader,anchor_ref,65536)
 need(anchor.get("schema")==f"xar.source{generation}.canonical-git-anchor/v1" and anchor.get("machine_id")==machine_id and anchor.get("commit")==base.get("business_source_commit"),"actual business anchor")
 need(base.get("source_root")==frozen.get("source_root")
   and base.get("business_source_commit")==frozen.get("business_source_commit")
   and _same_json(base.get(f"source{generation}_canonical_anchor"),anchor_ref.to_wire()),
   'current SDK manifest/anc')
def validate_current_saved_supervisor_business_v1(
 args:object,config:object,*,runtime_root:Path,expected_machine_id:str,
)->JsonObject:
 arg=record(args);cfg=record(record(config).get("cold_attempt"))
 inputs=load_current_saved_inputs_v1(runtime_root=runtime_root,
  expected_machine_id=expected_machine_id)
 need(arg.get("machine_id")==expected_machine_id==cfg.get("machine_id")
   and _same_path(text(arg.get("runtime_root")),str(runtime_root))
   and _same_path(text(cfg.get("runtime_root")),str(runtime_root))
   and parse_ref(cfg.get("basis_ref"))==inputs.basis_ref
   and parse_ref(cfg.get("validation_ref"))==inputs.validation_ref,
   'supervisor current machi')
 for name in ("attempt_nonce","task_nonce"):
  nonce=text(arg.get(name))
  need(re.fullmatch("[0-9a-f]{32}",nonce) is not None and cfg.get(name)==nonce,
    "fresh actual supervisor nonce: "+name)
 score=parse_campaign_score_junction_v1(cfg.get("campaign_score_junction"))
 validate_campaign_score_junction_source_v1(score,inputs.basis,runtime_root=runtime_root,reader=LocalBasisReaderV1())
 validate_campaign_score_junction_physical_v1(score,runtime_root=runtime_root,reader=LocalBasisReaderV1())
 return {"schema":"xar.current-saved-supervisor-business/v1","machine_id":expected_machine_id,
  "basis_ref":inputs.basis_ref.to_wire(),"validation_ref":inputs.validation_ref.to_wire(),
  "closure_ref":inputs.basis.refs.closure.to_wire(),
  "next_sequence":inputs.basis.next_sequence,"ordinary_cycle_credit":0,
  "game_day_credit":0,"original_actions_replayed":False}


def verify_current_saved_supervisor_attempt_v1(
 args:object,config:object,*,runtime_root:Path,expected_machine_id:str,
)->JsonObject:
 business=validate_current_saved_supervisor_business_v1(args,config,runtime_root=runtime_root,expected_machine_id=expected_machine_id)
 from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as _current_saved_preflight_v1
 arguments=record(args)
 prepared=_current_saved_preflight_v1.verify_current_saved_prepared_v1(
  runtime_root=runtime_root,expected_machine_id=expected_machine_id,
  expected_attempt_nonce=text(arguments.get("attempt_nonce")),
  expected_task_nonce=text(arguments.get("task_nonce")),reader=LocalBasisReaderV1())
 need(prepared.basis_ref==parse_ref(business["basis_ref"])
  and prepared.validation_ref==parse_ref(business["validation_ref"]),"Prepared belongs to current shared business inputs")
 return {**business,"schema":"xar.current-saved-supervisor-attempt/v2",
  "preflight_ref":prepared.preflight_ref.to_wire(),"prepared_stage":"OFFLINE_CONTRACT_PREPARED",
  "fresh_native_qualification":False,"full_loop_permitted":False}

def validate_current_saved_cold_owner_v1(plan_ref:ExactRefV1,quote_ref:ExactRefV1,*,reader:BasisReaderV1,expected_machine_id:str,metadata_overlay:dict[str,bytes]|None=None)->JsonObject:
 from tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1 import parse_plan_v1,parse_quote_v1,compose_v1
 plan_wire=evidence(reader,plan_ref,1048576)
 quote_wire=evidence(reader,quote_ref,1048576)
 plan=parse_plan_v1(plan_wire)
 quote=parse_quote_v1(quote_wire)
 need(plan_wire.get("machine_id")==expected_machine_id==quote_wire.get("machine_id"),"owner machine")
 producer_ref=parse_ref(plan_wire.get("producer_ref"))
 producer_rows=[item for item in plan.source_rows if item.relative_path=="tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py"]
 need(len(producer_rows)==1 and producer_rows[0].source_ref==producer_ref,"single current producer mapping")
 deployed_rows=[item for item in quote.files if item.relative_path==producer_rows[0].relative_path]
 need(len(deployed_rows)==1 and (deployed_rows[0].bytes,deployed_rows[0].sha256)==(producer_ref.bytes,producer_ref.sha256),"exact deployed producer copy mapping")
 actual_producer=Path(compose_v1.__code__.co_filename).resolve()
 deployed_producer=Path(deployed_rows[0].path).resolve()
 need(actual_producer in (Path(producer_ref.path).resolve(),deployed_producer),"current producer actual source or exact frozen copy origin")
 need(deployed_producer==Path(plan.runtime_root).joinpath(*producer_rows[0].relative_path.split("/")).resolve(),"confined deployed producer origin")
 exact_read(reader,producer_ref,131072)
 if actual_producer==deployed_producer:
  exact_read(reader,ExactRefV1(str(actual_producer),producer_ref.bytes,producer_ref.sha256),131072)
 recomposed=compose_v1(plan,plan_ref=plan_ref,metadata_overlay=metadata_overlay)
 need(_same_json(recomposed.quote.to_wire(),quote.to_wire()),'whole graph recompositio')
 for item in rows(quote_wire.get("files")):
  row=record(item)
  exact_read(reader,ExactRefV1(text(row.get("path")),integer(row.get("bytes")),digest(row.get("sha256"))),1048576)
 runtime_root=Path(text(plan_wire.get("runtime_root")))
 basis=decode_current_saved_basis_v1(exact_read(reader,plan.basis_ref,65536),expected_machine_id=expected_machine_id)
 inputs=validate_current_saved_cold_inputs_v1(basis,basis_ref=plan.basis_ref,validation_ref=plan.validation_ref,reader=reader)
 score=parse_campaign_score_junction_v1(quote_wire.get("campaign_score_junction"))
 validate_campaign_score_junction_source_v1(score,basis,runtime_root=runtime_root,reader=reader)
 return {"schema":"xar.current-saved-cold-owner-postguard/v1","machine_id":expected_machine_id,"plan_ref":plan_ref.to_wire(),"quote_ref":quote_ref.to_wire(),"basis_ref":inputs.basis_ref.to_wire(),"validation_ref":inputs.validation_ref.to_wire(),"runtime_root":str(runtime_root),"files_verified":len(rows(quote_wire.get("files"))),"canonical_entry_count":len(rows(quote_wire.get("canonical_entry_paths"))),"closure_count":len(rows(quote_wire.get("closure_entry_paths"))),"canonical_entry_limit":integer(quote_wire.get("canonical_entry_limit")),"runtime_sources_modified":False,"ordinary_cycle_credit":0,"game_day_credit":0,"original_actions_replayed":False}


def validate_current_saved_cold_inputs_v1(
 basis:CurrentSavedBasisV1,*,basis_ref:ExactRefV1,validation_ref:ExactRefV1,reader:BasisReaderV1,
)->CurrentSavedColdInputsV1:
 need(reader.stat(basis.refs.driver.path)==basis.driver_identity,"closed Driver identity")
 inputs=_validated_immutable_inputs_v1(basis,basis_ref=basis_ref,validation_ref=validation_ref,reader=reader)
 need(reader.stat(basis.refs.driver.path)==basis.driver_identity,"stable closed Driver identity")
 return inputs

class WarmRuntimeReaderV1(BasisReaderV1,Protocol):
 def read_driver_header(self,path:str,limit:int)->bytes:...
 def process_identity(self,pid:int)->JsonObject:...
@dataclass(frozen=True,slots=True)
class WarmSourceRefsV1:
 actual_game_ref:ExactRefV1
 sdk_pair_ref:ExactRefV1
 semantic_response_ref:ExactRefV1
 capabilities_response_ref:ExactRefV1
 cold_bound_ref:ExactRefV1
 cold_admission_ref:ExactRefV1
 def items(self)->tuple[tuple[str,ExactRefV1],...]:
  return (("actual_game_ref",self.actual_game_ref),("sdk_pair_ref",self.sdk_pair_ref),("semantic_response_ref",self.semantic_response_ref),("capabilities_response_ref",self.capabilities_response_ref),("cold_bound_ref",self.cold_bound_ref),("cold_admission_ref",self.cold_admission_ref))
 def to_wire(self)->JsonObject:
  return {key:ref.to_wire() for key,ref in self.items()}
@dataclass(frozen=True,slots=True)
class WarmSdkGenerationV1:
 role:Literal["sdk_queue","sdk_application"]
 pid:int
 creation_filetime:str
 executable:str
 def to_wire(self)->JsonObject:
  return {"role":self.role,"pid":self.pid,"creation_filetime":self.creation_filetime,"executable":self.executable}
@dataclass(frozen=True,slots=True)
class WarmBoundProofV1:
 machine_id:str
 basis_ref:ExactRefV1
 validation_ref:ExactRefV1
 closed_driver_ref:ExactRefV1
 closed_driver_identity:FileStatIdentityV1
 sources:WarmSourceRefsV1
 game:CurrentGameIdentityV1
 opening:SavedFrameV1
 sdk_generations:tuple[WarmSdkGenerationV1,...]
 connection_generation:int
 driver_identity:FileStatIdentityV1
 driver_header_sha256:str
 driver_header_bytes:int
 closed_driver_identity_replaced:bool
 observed_at_utc:str
 phase:Literal["warm_bound"]="warm_bound"
 def to_wire(self)->JsonObject:
  return {"schema":"xar.current-saved-warm-bound/v1","phase":self.phase,"machine_id":self.machine_id,"basis_ref":self.basis_ref.to_wire(),"validation_ref":self.validation_ref.to_wire(),"closed_driver_ref":self.closed_driver_ref.to_wire(),"closed_driver_identity":json_object(self.closed_driver_identity.to_wire()),"sources":self.sources.to_wire(),"game":self.game.to_wire(),"opening":self.opening.to_wire(),"sdk_generations":[v.to_wire() for v in self.sdk_generations],"connection_generation":self.connection_generation,"driver_identity":json_object(self.driver_identity.to_wire()),"driver_header_sha256":self.driver_header_sha256,"driver_header_bytes":self.driver_header_bytes,"driver_read_scope":"bounded_header_only_no_full_hash_or_history_validation","closed_driver_identity_replaced":self.closed_driver_identity_replaced,"closed_driver_reference_scope":"historical_closed_bytes_not_reverified_after_native_restore","observed_at_utc":self.observed_at_utc}
@dataclass(frozen=True,slots=True)
class WarmCurrentSavedFeederInputsV1:
 inputs:CurrentSavedColdInputsV1
 warm_proof:WarmBoundProofV1
 phase:Literal["warm_bound"]="warm_bound"
def parse_current_driver_header_v1(raw:bytes)->JsonObject:
 need(type(raw) is bytes and len(raw)<=16384,"bounded Driver header")
 index=raw.find(b',"command_history":')
 need(index>0,"SDK Driver header delimiter")
 head=record(parse_json(raw[:index]+b"}"),{"format_version","pipe_name","bridge_pid","episode_character_id","episode_run_id","last_checkpoint"})
 need(integer(head["format_version"])==2,"current Driver format")
 return _clone(head)
def _warm_frame(body:JsonObject,*,semantic:Literal[True],expected_lifecycle:JsonObject)->object:
 need(semantic is True and _same_json(body.get("succession_lifecycle"),expected_lifecycle),"current lifecycle")
 return SavedFrameV1(text(body.get("snapshot_id")),integer(body.get("revision"),1),integer(body.get("native_revision"),1),integer(body.get("date_raw")),integer(body.get("episode_character_id"),1),text(body.get("episode_run_id"))).to_wire()
def _utc_filetime_v1(value:object)->int:
 point=datetime.fromisoformat(utc(value).replace("Z","+00:00"))
 delta=point-datetime(1601,1,1,tzinfo=timezone.utc)
 return (delta.days*86400+delta.seconds)*10000000+delta.microseconds*10
def validate_warm_binding_v1(
 inputs:CurrentSavedColdInputsV1,*,sources:WarmSourceRefsV1,reader:WarmRuntimeReaderV1,runtime_root:Path,
)->WarmBoundProofV1:
 basis=inputs.basis;basis_ref=inputs.basis_ref;validation_ref=inputs.validation_ref
 expected={"actual_game_ref":"ROOT-ACTUAL-GAME-LAUNCH-C23.json","sdk_pair_ref":"ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json","semantic_response_ref":f"p37-responses/{basis.next_sequence:04d}-1-result.json","capabilities_response_ref":f"p37-responses/{basis.next_sequence+1:04d}-1-result.json","cold_bound_ref":"p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json","cold_admission_ref":"ROOT-P37C23-COLD-RESUME-ADMISSION.json"}
 for key,ref in sources.items():
  need(_same_path(ref.path,str(runtime_root/expected[key])),"actual warm source path")
 game_row=evidence(reader,sources.actual_game_ref)
 game=parse_current_game_identity_v1(game_row,legacy_python=True)
 game_now=reader.process_identity(game.pid)
 need(integer(game_now.get("pid"),1,PID_MAX)==game.pid and _birth(game_now.get("creation_filetime"),legacy_python=True)==game.creation_filetime,"current Game birth")
 command=rows(game_row.get("command"))
 need(game_row.get("machine_id")==basis.machine_id and bool(command) and _same_path(text(game_now.get("executable")),text(command[0])),"actual Game source image")
 pair=evidence(reader,sources.sdk_pair_ref)
 need(pair.get("machine_id")==basis.machine_id and pair.get("status")=="SDK_PAIR_HANDLES_RETAINED" and pair.get("rpc_started") is False,"actual current SDK pair")
 generations:list[WarmSdkGenerationV1]=[]
 for item in rows(pair.get("processes")):
  row=record(item);role=row.get("role")
  if role=="sdk_queue":kind:Literal["sdk_queue","sdk_application"]="sdk_queue"
  elif role=="sdk_application":kind="sdk_application"
  else:raise ValueError("SDK role")
  pid=integer(row.get("pid"),1,PID_MAX);birth=_birth(row.get("creation_filetime"),legacy_python=True);exe=text(row.get("executable"))
  now=reader.process_identity(pid)
  need(_birth(now.get("creation_filetime"),legacy_python=True)==birth and _same_path(text(now.get("executable")),exe),"actual SDK kernel generation")
  need(all((pid,birth)!=(old.pid,old.creation_filetime) for old in inputs.closed_epoch.sdk_processes),"fresh SDK generation")
  generations.append(WarmSdkGenerationV1(kind,pid,birth,exe))
 need(len(generations)==2 and {v.role for v in generations}=={"sdk_queue","sdk_application"} and len({v.pid for v in generations})==2,"two live SDK roles")
 semrow=evidence(reader,sources.semantic_response_ref,1048576);caprow=evidence(reader,sources.capabilities_response_ref,1048576)
 sem=_clone(completed_body(semrow,"ck3_take_semantic_snapshot_private_v1"));cap=completed_body(caprow,"ck3_get_capabilities")
 need(integer(record(semrow.get("request")).get("sequence"),1)==basis.next_sequence and integer(record(caprow.get("request")).get("sequence"),1)==basis.next_sequence+1,"actual SEM CAP sequence")
 opening=bind_current_saved_opening_v1(inputs,sem,launch=game,frame_decoder=_warm_frame)
 need(sem.get("map_ready") is True and sem.get("paused") is True,"saved opening paused map")
 control=record(cap.get("native_session_control"))
 need(control.get("configured") is True and control.get("restore_checkpoint") is True and control.get("driver_state_restored") is True and control.get("driver_state_restore_kind")=="cold_checkpoint" and control.get("episode_binding_state")=="active_resumed","actual canonical cold restore")
 for key in ("driver_state_error","cold_candidate_rejection"):
  _exact_null(control,key)
 need(integer(cap.get("episode_character_id"),1)==basis.frame.actor_character_id and cap.get("episode_run_id")==basis.frame.episode_run_id and cap.get("episode_identity_pending") is False and cap.get("one_life_terminal") is False,"current restored episode")
 diag=record(sem.get("diagnostics"));capdiag=record(cap.get("diagnostics"));hello=record(capdiag.get("hello"))
 generation=integer(diag.get("connection_generation"),1)
 need(integer(capdiag.get("bridge_pid"),1)==game.pid and integer(hello.get("pid"),1)==game.pid and integer(capdiag.get("connection_generation"),1)==generation==integer(hello.get("connection_generation"),1) and capdiag.get("pipe_name")==inputs.closed_epoch.pipe_name and hello.get("ck3_build_match") is True and hello.get("game_adapter_status")=="ready","same current native epoch")
 need(_same_path(text(control.get("driver_state_path")),basis.refs.driver.path),"actual current Driver path")
 material=record(cap.get("checkpoint_materialization"))
 need(material.get("configured") is True and _same_path(str(Path(text(material.get("save_dir")))/text(material.get("filename"))),basis.refs.save.path),"current checkpoint materialization")
 marker=evidence(reader,sources.cold_bound_ref,65536)
 moments=[_utc_filetime_v1(v) for v in (pair.get("at_utc"),semrow.get("started_at_utc"),semrow.get("ended_at_utc"),caprow.get("started_at_utc"),caprow.get("ended_at_utc"),marker.get("observed_at_utc"))]
 need(all(a<=b for a,b in zip(moments,moments[1:])) and all(int(v.creation_filetime)<=moments[1] for v in generations),"actual current SDK call order")
 need(marker.get("machine_id")==basis.machine_id and marker.get("schema")=="xar.c23.normal-checkpoint-cold-bound/v1" and _same_json(marker.get("opening_frame"),opening.to_wire()) and _same_json(marker.get("checkpoint"),inputs.checkpoint) and integer(marker.get("completed_cycles"))==basis.completed_cycles and integer(marker.get("T0_date_raw"))==basis.origin.start_date_raw and integer(marker.get("new_ordinary_cycle_credit"))==0 and marker.get("AUTO_or_MET_replayed") is False and _same_path(text(marker.get("semantic_response")),sources.semantic_response_ref.path),"actual bound checkpoint marker")
 cold=evidence(reader,sources.cold_admission_ref,65536)
 need(cold.get("machine_id")==basis.machine_id and parse_ref(cold.get("basis_ref"))==basis_ref and parse_ref(cold.get("validation_ref"))==validation_ref and parse_current_game_identity_v1(cold.get("new_Game"),legacy_python=True)==game,"bound current cold admission")
 before=reader.stat(basis.refs.driver.path)
 raw=reader.read_driver_header(basis.refs.driver.path,16384)
 head=parse_current_driver_header_v1(raw)
 need(reader.stat(basis.refs.driver.path)==before and reader.stat(basis.refs.save.path)==basis.save_identity,"stable warm Driver SAVE")
 need(head.get("pipe_name")==inputs.closed_epoch.pipe_name and integer(head.get("bridge_pid"),1)==game.pid and integer(head.get("episode_character_id"),1)==basis.frame.actor_character_id and head.get("episode_run_id")==basis.frame.episode_run_id and _same_json(head.get("last_checkpoint"),inputs.checkpoint),"current Driver CP and epoch")
 proof=WarmBoundProofV1(basis.machine_id,basis_ref,validation_ref,basis.refs.driver,basis.driver_identity,sources,game,opening,tuple(generations),generation,before,hashlib.sha256(raw).hexdigest(),len(raw),before!=basis.driver_identity,datetime.now(timezone.utc).isoformat())
 return proof
def validate_current_saved_warm_inputs_v1(
 basis:CurrentSavedBasisV1,*,basis_ref:ExactRefV1,validation_ref:ExactRefV1,
 sources:WarmSourceRefsV1,reader:WarmRuntimeReaderV1,runtime_root:Path,
)->WarmCurrentSavedFeederInputsV1:
 inputs=_validated_immutable_inputs_v1(basis,basis_ref=basis_ref,validation_ref=validation_ref,reader=reader)
 return WarmCurrentSavedFeederInputsV1(inputs,validate_warm_binding_v1(inputs,sources=sources,reader=reader,runtime_root=runtime_root))
def load_current_saved_warm_inputs_v1(*,runtime_root:Path,expected_machine_id:str)->WarmCurrentSavedFeederInputsV1:
 reader=LocalBasisReaderV1()
 def pin(path:Path,limit:int=1048576)->ExactRefV1:
  before=reader.stat(str(path))
  need(before.bytes<=limit,"small warm source")
  with path.open("rb") as stream:raw=stream.read(limit+1)
  need(reader.stat(str(path))==before and len(raw)==before.bytes,"stable warm source")
  return ExactRefV1(str(path),len(raw),hashlib.sha256(raw).hexdigest())
 entry=evidence(reader,pin(runtime_root/"ROOT-CURRENT-SAVED-INPUTS01.json"),16384)
 need(entry.get("schema")==CURRENT_INPUTS_SCHEMA and entry.get("machine_id")==expected_machine_id,"current warm machine")
 bref=parse_ref(entry.get("basis_ref"));vref=parse_ref(entry.get("validation_ref"))
 basis=decode_current_saved_basis_v1(exact_read(reader,bref,65536),expected_machine_id=expected_machine_id)
 sources=WarmSourceRefsV1(pin(runtime_root/"ROOT-ACTUAL-GAME-LAUNCH-C23.json"),pin(runtime_root/"ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json"),pin(runtime_root/f"p37-responses/{basis.next_sequence:04d}-1-result.json"),pin(runtime_root/f"p37-responses/{basis.next_sequence+1:04d}-1-result.json"),pin(runtime_root/"p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json"),pin(runtime_root/"ROOT-P37C23-COLD-RESUME-ADMISSION.json"))
 return validate_current_saved_warm_inputs_v1(basis,basis_ref=bref,validation_ref=vref,sources=sources,reader=reader,runtime_root=runtime_root)

def _score_u64_v1(value:object,minimum:int=0)->str:
 result=text(value)
 need(re.fullmatch("0|[1-9][0-9]*",result) is not None and minimum<=int(result)<=UINT64_MAX,"score directory uint64 decimal")
 return result
def _score_path_v1(value:str)->str:
 need(ntpath.isabs(text(value)),"absolute score path")
 return ntpath.normcase(ntpath.normpath(value))
@dataclass(frozen=True,slots=True)
class CampaignScoreJunctionV1:
 path:str
 exact_target:str
 must_verify_same_FileID:Literal[True]
 target_file_id:str
 target_device:str
 anchor_ref:ExactRefV1
 def __post_init__(self)->None:
  _score_path_v1(self.path);_score_path_v1(self.exact_target)
  need(self.must_verify_same_FileID is True,"score same FileID mandatory")
  _score_u64_v1(self.target_file_id,1);_score_u64_v1(self.target_device)
 def to_wire(self)->JsonObject:
  return {"path":self.path,"exact_target":self.exact_target,"must_verify_same_FileID":True,
   "target_file_id":self.target_file_id,"target_device":self.target_device,"anchor_ref":self.anchor_ref.to_wire()}
def parse_campaign_score_junction_v1(value:object)->CampaignScoreJunctionV1:
 r=record(value,{"path","exact_target","must_verify_same_FileID","target_file_id","target_device","anchor_ref"})
 need(r["must_verify_same_FileID"] is True,"score same FileID mandatory")
 return CampaignScoreJunctionV1(text(r["path"]),text(r["exact_target"]),True,
  _score_u64_v1(r["target_file_id"],1),_score_u64_v1(r["target_device"]),parse_ref(r["anchor_ref"]))
def campaign_score_directory_identity_v1(path:Path)->tuple[str,str]:
 st=os.stat(path,follow_symlinks=False)
 need(st.st_mode & 0o170000==0o040000 and not getattr(st,"st_file_attributes",0)&0x400,"score target ordinary directory")
 return _score_u64_v1(str(st.st_ino),1),_score_u64_v1(str(st.st_dev))
def validate_campaign_score_junction_source_v1(
 binding:CampaignScoreJunctionV1,basis:CurrentSavedBasisV1,*,runtime_root:Path,reader:BasisReaderV1,
)->None:
 expected=ntpath.join(ntpath.dirname(derive_current_saved_state_paths_v1(basis).state_root),"campaign-score")
 need(_score_path_v1(binding.path)==_score_path_v1(str(runtime_root/"campaign-score"))
  and _score_path_v1(binding.exact_target)==_score_path_v1(expected)
  and _score_path_v1(binding.anchor_ref.path)==_score_path_v1(ntpath.join(expected,"CAMPAIGN-ANCHOR.json")),"score path and shared state binding")
 before=campaign_score_directory_identity_v1(Path(binding.exact_target))
 need(before==(binding.target_file_id,binding.target_device),"score target identity")
 anchor=evidence(reader,binding.anchor_ref,16384)
 need(anchor.get("schema")=="xar.ck3.campaign-score-fixed-anchor/v1"
  and anchor.get("machine_id")==basis.machine_id
  and anchor.get("campaign_id")=="robert-first30-v20261019"
  and integer(anchor.get("founder_character_id"),1)==integer(record(basis.campaign_goal_anchor).get("origin_character_id"),1)
  and integer(anchor.get("start_date_raw"))==basis.origin.start_date_raw
  and integer(anchor.get("endpoint_date_raw"))==basis.origin.target_date_raw
  and anchor.get("fixed_across_ruler_and_sdk_changes") is True
  and integer(anchor.get("old_campaign_inputs_copied"),0,0)==0,"fixed score campaign source")
 utc(anchor.get("observed_at_utc"))
 need(campaign_score_directory_identity_v1(Path(binding.exact_target))==before,"score target stable during anchor validation")
def build_campaign_score_junction_v1(
 basis:CurrentSavedBasisV1,material_quote:object,*,runtime_root:Path,anchor_ref:ExactRefV1,reader:BasisReaderV1,
)->CampaignScoreJunctionV1:
 old=record(record(material_quote).get("campaign_score_junction"),{"path","exact_target","must_verify_same_FileID"})
 _score_path_v1(text(old["path"]))
 need(old["must_verify_same_FileID"] is True,"material score same FileID mandatory")
 target=text(old["exact_target"]);file_id,device=campaign_score_directory_identity_v1(Path(target))
 binding=CampaignScoreJunctionV1(str(runtime_root/"campaign-score"),target,True,file_id,device,anchor_ref)
 validate_campaign_score_junction_source_v1(binding,basis,runtime_root=runtime_root,reader=reader)
 return binding
def validate_campaign_score_junction_physical_v1(
 binding:CampaignScoreJunctionV1,*,runtime_root:Path,reader:BasisReaderV1,
)->None:
 need(_score_path_v1(binding.path)==_score_path_v1(str(runtime_root/"campaign-score"))
  and _score_path_v1(binding.anchor_ref.path)==_score_path_v1(ntpath.join(binding.exact_target,"CAMPAIGN-ANCHOR.json")),"physical score paths")
 target=Path(binding.exact_target);link=Path(binding.path)
 before=campaign_score_directory_identity_v1(target)
 need(before==(binding.target_file_id,binding.target_device),"physical score target identity")
 first=os.lstat(link)
 need(link.is_junction() and getattr(first,"st_reparse_tag",0)==0xA0000003,"score path must be real junction")
 need(os.path.samefile(link,target) and link.resolve(strict=True)==target.resolve(strict=True),"score junction exact target and same FileID")
 exact_read(reader,binding.anchor_ref,16384)
 last=os.lstat(link)
 need((first.st_ino,first.st_dev)==(last.st_ino,last.st_dev)
  and link.is_junction() and getattr(last,"st_reparse_tag",0)==0xA0000003
  and os.path.samefile(link,target) and link.resolve(strict=True)==target.resolve(strict=True)
  and campaign_score_directory_identity_v1(target)==before,"score junction and target stable")

def validate_current_saved_prepared_sdk_closure_v1(value:object,*,inputs:CurrentSavedColdInputsV1)->JsonObject:
 reader=LocalBasisReaderV1();reference=parse_ref(value)
 closure=evidence(reader,inputs.basis.refs.closure,65536)
 if closure.get("schema")==READONLY_COLD_FAILURE_EPOCH_SCHEMA:
  epoch=parse_readonly_cold_failure_epoch_v1(closure,expected_machine_id=inputs.basis.machine_id)
  expected=epoch.refs.sdk_closed
 else:
  need(closure.get("schema")=="xar.A20-actual-saved-progress-closure/v1","qualified SDK closure schema")
  expected=parse_ref(record(closure.get("sources")).get("ROOT-P37C23-OWNER-CLOSED.json"))
 need(inputs.closed_epoch.closure_ref==inputs.basis.refs.closure and reference==expected,"qualified exact SDK closed source")
 raw=evidence(reader,reference,16384)
 normal=all(p.exit_code==0 for p in inputs.closed_epoch.sdk_processes)
 need(raw.get("machine_id")==inputs.basis.machine_id
  and raw.get("status")=="ACTUAL_BOTH_SDK_EXITS_OBSERVED" and raw.get("normal") is normal,"qualified SDK closure classification")
 seen:set[str]=set()
 for value_row in rows(raw.get("processes")):
  row=record(value_row);role=text(row.get("role"))
  process=next((p for p in inputs.closed_epoch.sdk_processes if p.role==role),None)
  need(process is not None and role not in seen,"qualified SDK role")
  if process is None:raise ValueError("qualified SDK role")
  need(row.get("kernel_exit_observed") is True and integer(row.get("wait_result"),0,0)==0
   and "observation_error" in row and row["observation_error"] is None
   and integer(row.get("pid"),1,PID_MAX)==process.pid
   and _birth(row.get("creation_filetime"),legacy_python=True)==process.creation_filetime
   and text(row.get("executable"))==process.executable
   and integer(row.get("exit_code"))==process.exit_code,"qualified SDK kernel generation and exit")
  seen.add(role)
 need(seen=={"sdk_queue","sdk_application"},"both qualified SDK exits")
 processes:list[JsonValue]=[{"role":p.role,"pid":p.pid,"creation_filetime":p.creation_filetime,
  "executable":p.executable,"exit_code":p.exit_code,"kernel_exit_observed":True,
  "wait_result":0,"observation_error":None} for p in inputs.closed_epoch.sdk_processes]
 return {"schema":"xar.current-saved-qualified-sdk-closure/v1","machine_id":inputs.basis.machine_id,
  "source_ref":reference.to_wire(),"status":"ACTUAL_BOTH_SDK_EXITS_OBSERVED","normal":normal,"processes":processes}
