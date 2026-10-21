"""A20 cold successor. Existing Game/source closures are never rotated."""
from __future__ import annotations
import ast
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Callable, Literal, Protocol, TypedDict, cast
from file_stat_identity_v1 import SCHEMA,parse_file_stat_identity_v1
import prepare_source31_a19_cold_union_v1 as predecessor
previous=predecessor.previous

Doc = dict[str,object]
Outputs = dict[Path,bytes]
class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str
class Dynamic(Protocol):
    def __call__(self,*args:object,**kwargs:object)->object: ...
def need(ok: bool, why: str) -> None:
    if not ok: raise ValueError("A20: "+why)

def record(value: object) -> Doc:
    need(isinstance(value, dict), "object")
    result: Doc = {}
    if not isinstance(value, dict): raise ValueError("object")
    for key, item in value.items():
        need(type(key) is str, "text key")
        if not isinstance(key, str): raise ValueError("key")
        result[key] = item
    return result

def text(value: object) -> str:
    if type(value) is not str or not value: raise ValueError("nonempty text")
    return value

def uint(value: object, maximum: int = 2**53-1) -> int:
    if type(value) is not int or not 0 <= value <= maximum: raise ValueError("exact uint")
    return value

def sequence(value: object) -> list[object]:
    if not isinstance(value, list): raise ValueError("JSON list")
    return list(value)

def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

def enc(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False)+"\n").encode()

def refs(value: object) -> ExactRef:
    row=record(value)
    need(set(row)=={"path","bytes","sha256"}, "exact reference fields")
    p=text(row["path"]); n=uint(row["bytes"]); digest=text(row["sha256"])
    need(Path(p).is_absolute() and n>0 and re.fullmatch("[0-9a-f]{64}",digest) is not None,"reference domain")
    return {"path":p,"bytes":n,"sha256":digest}

def read_ref(value: object, limit: int = 1048576) -> bytes:
    r=refs(value); p=Path(r["path"]); before=p.stat()
    with p.open("rb") as f: raw=f.read(limit+1)
    after=p.stat()
    need(0<len(raw)<=limit and (len(raw),sha(raw))==(r["bytes"],r["sha256"])
         and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),"stable exact bytes")
    return raw

def checked(value: object, limit: int = 1048576) -> Doc:
    return record(json.loads(read_ref(value,limit)))

def ref(path: Path | str) -> ExactRef:
    p=Path(path).resolve(strict=True)
    with p.open("rb") as f: raw=f.read(1048577)
    need(0<len(raw)<=1048576,"bounded reference")
    return {"path":str(p),"bytes":len(raw),"sha256":sha(raw)}

def fixed(path: Path, pin: tuple[int,str]) -> ExactRef:
    return {"path":str(path),"bytes":pin[0],"sha256":pin[1]}

def one(source: str, before: str, after: str, count: int = 1) -> str:
    need(source.count(before)==count,"one reviewed seam: "+before[:70])
    return source.replace(before,after)

def dynamic(module: ModuleType, name: str) -> Dynamic:
    fn: object=getattr(module,name,None)
    need(callable(fn),"callable "+name)
    return cast(Dynamic,fn)

def function_source_v1(raw: str, name: str) -> str:
    nodes=[n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==name]
    need(len(nodes)==1,"one actual function "+name)
    value=ast.get_source_segment(raw,nodes[0])
    need(value is not None,"source segment")
    return text(value)
MACHINE=predecessor.MACHINE
P,O,OWN=predecessor.P,predecessor.O,Path(__file__).resolve().parent
PREVIOUS=P/"robert30-v20261019-campaign01/runtime-a19"
TARGET=PREVIOUS.with_name("runtime-a20")
PREP=O/"source31-a20-prep01"
SCREEN=TARGET/"ROOT-SCREEN-ADMISSION-C23-A15.json"
NATIVE32_ADAPTER_NAME=predecessor.NATIVE32_ADAPTER_NAME
NATIVE32_EXTENSION_NAME=predecessor.NATIVE32_EXTENSION_NAME
NATIVE32_OBSERVER_BINDING_NAME=predecessor.NATIVE32_OBSERVER_BINDING_NAME
PREDECESSOR_PIN=(27730,"4482c3a1190588acfce211c106a93ed93c15c26014574f10390be7d9c344b715")
PREFLIGHT_NAME="root_saved_campaign_preflight.py"
STAT_IDENTITY_PIN=(2642, 'b5c267b11d2b2b7933eec7a62092e29ec2e0d80a8342cab0c7818009385653d0')
class PlanV1(TypedDict):
    schema: Literal["xar.Source31-A20-complete-cold-input/v1"]
    machine_id: str
    execution_owner: Literal["Root"]
    root_direct_execution_release: Literal[True]
    observed_at_utc: str
    attempt_nonce: str
    task_nonce: str
    full_storage_ref: ExactRef
    live_storage_ref: ExactRef
    steam_native_state_ref: ExactRef
    union_producer: ExactRef
    stage_producer: ExactRef
    sdk_base_ref: ExactRef
    canonical_anchor_ref: ExactRef
    native_binding_ref: ExactRef
    closure_ref: ExactRef
    current_driver_review_ref: ExactRef
    ledger_ref: ExactRef
    current_next_ref: ExactRef
    screen_admission_path: str
    runtime_adapter_ref: ExactRef
    runtime_extension_ref: ExactRef
    base_cold_plan_ref: ExactRef
    base_producer_ref: ExactRef
    predecessor_plan_ref: ExactRef
    predecessor_producer_ref: ExactRef
    preflight_source_ref: ExactRef
    expected_next_sequence: int

def parse_plan(value:object)->PlanV1:
    row=record(value)
    need(set(row)==set(PlanV1.__annotations__),"single28-field A20 plan")
    need(row["schema"]=="xar.Source31-A20-complete-cold-input/v1"
         and row["machine_id"]==MACHINE and row["execution_owner"]=="Root"
         and row["root_direct_execution_release"] is True,"A20 Root machine")
    for key in ("attempt_nonce","task_nonce"):
        need(re.fullmatch("[0-9a-f]{32}",text(row[key])) is not None,"nonce")
    need(row["attempt_nonce"]!=row["task_nonce"],"independent nonces")
    need(datetime.fromisoformat(text(row["observed_at_utc"])).utcoffset() is not None,"aware time")
    need(Path(text(row["screen_admission_path"])).resolve()==SCREEN.resolve(),"new A20 screen")
    out=dict(row)
    ordinary={"schema","machine_id","execution_owner","root_direct_execution_release",
              "observed_at_utc","attempt_nonce","task_nonce","screen_admission_path","expected_next_sequence"}
    for key in set(row)-ordinary:
        out[key]=refs(row[key])
    out["expected_next_sequence"]=uint(row["expected_next_sequence"])
    need(uint(out["expected_next_sequence"])>10570,"actual post-bootstrap frontier")
    need(out["full_storage_ref"]==out["live_storage_ref"],"same current FULL")
    return cast(PlanV1,out)

class CapacityV1(TypedDict):
    D_free_floor_bytes: int
    Z_free_floor_bytes: int

class RuntimeAdmissionV1(TypedDict):
    schema: Literal["xar.Source31-A20-runtime-prepare-admission/v1"]
    machine_id: str
    owner: Literal["Root"]
    status: Literal["ADMITTED"]
    root_direct_execution_release: Literal[True]
    canonical_capacity_review_passed: Literal[True]
    plan: ExactRef
    quote: ExactRef
    full_storage_ref: ExactRef
    runtime_hard_bytes: int
    capacity: CapacityV1

def positive(value: object) -> int:
    result=uint(value);need(result>0,"positive safe integer");return result

def parse_runtime_admission_v1(value: object, *, expected_machine_id: str) -> RuntimeAdmissionV1:
    row=record(value);capacity=record(row.get("capacity"))
    need(row.get("schema")=="xar.Source31-A20-runtime-prepare-admission/v1"
         and type(expected_machine_id) is str and bool(expected_machine_id)
         and row.get("machine_id")==expected_machine_id and row.get("owner")=="Root"
         and row.get("status")=="ADMITTED" and row.get("root_direct_execution_release") is True
         and row.get("canonical_capacity_review_passed") is True,"A20 admitted Root capacity")
    need("hard_bytes" not in row and not ({"D_conservative_floor_bytes","Z_conservative_floor_bytes"}&set(capacity)),"no legacy aliases")
    return {"schema":"xar.Source31-A20-runtime-prepare-admission/v1","machine_id":expected_machine_id,
        "owner":"Root","status":"ADMITTED","root_direct_execution_release":True,"canonical_capacity_review_passed":True,
        "plan":refs(row.get("plan")),"quote":refs(row.get("quote")),"full_storage_ref":refs(row.get("full_storage_ref")),
        "runtime_hard_bytes":positive(row.get("runtime_hard_bytes")),
        "capacity":{"D_free_floor_bytes":positive(capacity.get("D_free_floor_bytes")),
                    "Z_free_floor_bytes":positive(capacity.get("Z_free_floor_bytes"))}}

def validate_closed_records_v1(closed_value:object,review_value:object,*,expected_next_sequence:int)->None:
    closed=record(closed_value);review=record(review_value)
    expected=uint(expected_next_sequence)
    need(expected>10570,"post SEM/CAP actual NEXT")
    need(closed.get("schema")=="xar.A19-readonly-bootstrap-closed/v1"
         and closed.get("status")=="A19_CLOSED_NO_FULL_NO_REPLAY"
         and closed.get("machine_id")==MACHINE
         and closed.get("Tasks_absent") is True
         and closed.get("screen120_released") is True,"actual A19 closed resource identity")
    game=record(closed.get("Game"));exits=record(closed.get("SDK_actual_exits"))
    need(0<uint(game.get("pid"),2**32-1)<2**32,"closed Game PID")
    birth=text(game.get("creation_filetime"))
    need(re.fullmatch("[1-9][0-9]*",birth) is not None and int(birth)<2**64,"closed Game FILETIME wire")
    uint(game.get("exit_code"),2**32-1)
    need(type(game.get("forced_owned_job_cleanup")) is bool
         and uint(game.get("Job_active_final"))==0,"actual Job closed")
    need(set(exits)=={"sdk_queue","sdk_application"},"actual SDK pair")
    for result in exits.values(): uint(result,2**32-1)
    for key,number in (("next_sequence",expected),("saved_cycles",4753),("saved_days",5429),
                       ("live_settled_cycles",4758),("pending_cycle",4759),("FULL_requests",0),
                       ("new_cycle_credit",0),("new_day_credit",0)):
        need(uint(closed.get(key))==number,"closed "+key)
    need(uint(closed.get("actual_A19_completed_cycles"))==4753
         and "actual_A19_pending_cycle" in closed and closed["actual_A19_pending_cycle"] is None
         and closed.get("pending_cycle_scope")=="retained_A17_unknown_AUTO10565_not_A19_active"
         and closed.get("feeder_launched") is False and closed.get("feeder_attach_occurred") is False,
         "actual loaded SAVE basis distinct from retained historical pending")
    sources=record(closed.get("sources"))
    need(0<len(sources)<=64,"bounded actual closed source set")
    for item in sources.values():refs(item)
    sem=record(closed.get("SEM"));cap=record(closed.get("CAP"));journal=record(closed.get("journal"))
    need(uint(sem.get("sequence"))+1==uint(cap.get("sequence"))
         and uint(cap.get("sequence"))+1==uint(journal.get("sequence"))
         and uint(journal.get("sequence"))+1==expected
         and sem.get("status")=="verified" and cap.get("status")=="verified_cold_checkpoint_active_resumed"
         and uint(closed.get("SDK_control_requests_completed"))==3,"actual three readonly control calls")
    for item in (sem,cap,journal):refs(item.get("result"))
    need(journal.get("status")=="postvalidation_failed"
         and uint(journal.get("actual_native_journal_requests"))==1
         and journal.get("native32_result_validated_present") is False
         and journal.get("drain_fence") is False and journal.get("absence_is_nonexecution_proof") is False,
         "original journal postvalidation failure preserved; no completion or drain inference")
    rollback=record(closed.get("next_cold_rollback"))
    need(set(rollback)=={"cycles","days"} and uint(rollback.get("cycles"))==5
         and uint(rollback.get("days"))==0 and closed.get("old_request_replayed") is False,
         "preserved unknown10565; five-cycle zero-day rollback")
    need(review.get("schema")=="xar.A19-current-Driver-SAVE-review/v1"
         and review.get("machine_id")==MACHINE
         and uint(review.get("saved_cycles"))==4753 and uint(review.get("saved_game_days"))==5429
         and uint(review.get("live_settled_cycles"))==4758
         and uint(review.get("new_day_credit"))==0
         and review.get("old_unknown10565_replayed") is False,"actual A19 current review")
    need(uint(review.get("Driver_history_rows"))>0,"actual observed Driver history, not monotonic across cold restore")
    need(uint(review.get("actual_A19_completed_cycles"))==4753
         and "actual_A19_loop_pending_cycle" in review and review["actual_A19_loop_pending_cycle"] is None
         and review.get("pending_cycle_scope")=="retained_A17_unknown_AUTO10565_not_current_A19",
         "actual A19 review loop is settled at saved4753")
    pending=record(review.get("pending_cycle"))
    need(uint(pending.get("global_turn"))==4759 and uint(pending.get("auto_sequence"))==10565
         and pending.get("stage")=="auto_unsettled","unresolved historical AUTO10565")
    need(uint(record(review.get("next_sequence")).get("next_sequence"))==expected,"review NEXT")
    for key in ("Driver","SAVE"):
        item=record(review.get(key))
        reference=refs(item.get("ref"))
        identity=parse_file_stat_identity_v1(item.get("identity"),schema=SCHEMA)
        need(identity.bytes==reference["bytes"],"one exact identity/ref byte count")
        need(item.get("stable_before_after") is True,"review stable "+key)

def validate_closed_basis_v1(plan_value:object)->Doc:
    p=parse_plan(plan_value)
    need(Path(p["closure_ref"]["path"]).resolve().parent==PREVIOUS.resolve()
         and Path(p["current_driver_review_ref"]["path"]).resolve().parent==PREVIOUS.resolve(),
         "actual new predecessor paths")
    closed=checked(p["closure_ref"],65536);review=checked(p["current_driver_review_ref"],32768)
    validate_closed_records_v1(closed,review,expected_next_sequence=p["expected_next_sequence"])
    need(refs(closed.get("current_driver_review"))==p["current_driver_review_ref"]
         and refs(closed.get("continuity_ledger"))==p["ledger_ref"]
         and refs(closed.get("current_next"))==p["current_next_ref"],"closed exact frontier inputs")
    need(uint(checked(p["current_next_ref"],16384).get("next_sequence"))==p["expected_next_sequence"],
         "current live NEXT equals closed NEXT")
    for value in record(closed.get("sources")).values(): read_ref(value,262144)
    return closed

def historical_plan_v1(plan_value:object)->Doc:
    p=parse_plan(plan_value)
    need(p["predecessor_producer_ref"]==fixed(OWN/"prepare_source31_a19_cold_union_v1.py",PREDECESSOR_PIN),
         "exact immutable A19 software")
    read_ref(p["predecessor_producer_ref"],32768)
    old=predecessor.parse_plan(checked(p["predecessor_plan_ref"],16384))
    need(old["union_producer"]==p["predecessor_producer_ref"]
         and old["sdk_base_ref"]==p["sdk_base_ref"] and old["canonical_anchor_ref"]==p["canonical_anchor_ref"]
         and old["native_binding_ref"]==p["native_binding_ref"] and old["ledger_ref"]==p["ledger_ref"]
         and old["base_producer_ref"]==p["base_producer_ref"]
         and old["base_cold_plan_ref"]==p["base_cold_plan_ref"],"unchanged Source31/Native32/history")
    need(p["attempt_nonce"] not in (old["attempt_nonce"],old["task_nonce"])
         and p["task_nonce"] not in (old["attempt_nonce"],old["task_nonce"]),"new A20 nonces")
    return dict(old)

def validate_canonical_preflight_v1(canonical_raw:bytes,*,expected:ExactRef)->None:
    need(type(canonical_raw) is bytes and 0<len(canonical_raw)<=65536,"bounded actual canonical preflight")
    pin=refs(expected)
    need((len(canonical_raw),sha(canonical_raw))==(pin["bytes"],pin["sha256"]),"actual canonical bytes")
    need(Path(pin["path"]).name==PREFLIGHT_NAME and Path(pin["path"]).parent.resolve()==OWN.resolve(),
         "canonical public preflight origin")
    tree=ast.parse(canonical_raw)
    names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    need({"build_saved_map_first_frame_v1","require_saved_campaign_visual","recover_zero_rpc_preflight"}<=names,
         "real canonical producer and consumers")
    compile(canonical_raw,PREFLIGHT_NAME,"exec")

def patch_preflight_source_v1(sources:dict[str,bytes],canonical_raw:bytes,*,expected:ExactRef)->dict[str,bytes]:
    validate_canonical_preflight_v1(canonical_raw,expected=expected)
    prior=sources.get(PREFLIGHT_NAME)
    need(type(prior) is bytes and prior is not None
         and len(prior)==20998 and sha(prior)=="6edccc9352b3ced85942a1e25e9761c29c1fd97d114aba859bc82b1b1df446e4",
         "exact accepted preflight preimage")
    result=dict(sources);result[PREFLIGHT_NAME]=canonical_raw
    return result

def load_verified_predecessor_v1(reference_value:object)->ModuleType:
    reference=refs(reference_value)
    need(reference==fixed(OWN/"prepare_source31_a19_cold_union_v1.py",PREDECESSOR_PIN),"exact A19 source")
    raw=read_ref(reference,32768)
    module=ModuleType("_a20_exact_a19_"+uuid.uuid4().hex)
    module.__file__=reference["path"];sys.modules[module.__name__]=module
    exec(compile(raw,module.__file__,"exec"),vars(module))
    need(Path(text(module.__file__)).read_bytes()==raw,"verified raw and extraction source same")
    return module

RUNTIME_SUFFIX_V1='\nimport re as _a20_re\ndef validate_actual_A19_index_v1(reference:object,checked:_A20Callable[[object,int],dict[str,object]])->dict[str,object]:\n    _a20_need(reference==A20_CLOSURE_REF,"actual A19 authority")\n    x=checked(reference,65536);r=checked(A20_REVIEW_REF,32768)\n    _a20_validate_closed_records_v1(x,r,expected_next_sequence=A20_NEXT)\n    for value in _a20_record(x.get("sources")).values():_a14_verify_exact_fact(value)\n    return x\n\n_A20_PRIOR_POST=validate_post_sem_driver\n_A20_PRIOR_VIEW=historical_saved_basis_view\n_A20_PRIOR_SEED=validate_saved_seed_a10\ndef validate_post_sem_driver(pre:dict[str,object],close:dict[str,object],\n        checked:_A20Callable[[object,int],dict[str,object]],verify_current_stat:bool=True)->bool:\n    _a20_need(type(verify_current_stat) is bool,"explicit current-stat branch")\n    validate_actual_A19_index_v1(A20_CLOSURE_REF,checked)\n    _A20_PRIOR_POST(checked(A20_HISTORICAL_PRE,32768),close,checked,False)\n    r=checked(A20_REVIEW_REF,32768)\n    _a20_need(pre==A20_CURRENT_PRE and pre.get("actual_A19_closure")==A20_CLOSURE_REF\n              and pre.get("actual_A19_driver_review")==A20_REVIEW_REF,"exact A20 current pre")\n    if verify_current_stat:\n        identity=_a20_record(_a20_record(r.get("Driver")).get("identity"))\n        s=Path(_a20_text(_a20_record(pre.get("driver_state")).get("path"))).stat()\n        _a20_need((s.st_size,str(s.st_ino),str(s.st_mtime_ns))==\n            (_a20_uint(identity.get("bytes")),_a20_text(identity.get("file_id")),\n             _a20_text(identity.get("mtime_ns"))),"actual current Driver identity")\n        sidecars=pre.get("sidecars")\n        _a20_need(isinstance(sidecars,list),"current sidecar list")\n        if not isinstance(sidecars,list):raise ValueError("sidecars")\n        for value in sidecars:_a20_need(checked(value,65536).get("pending") is None,"current sidecar pending")\n    return True\n\ndef historical_saved_basis_view(admission:dict[str,object])->dict[str,object]:\n    _a20_need(_a20_uint(admission.get("next_sequence"))==A20_NEXT,"actual A20 NEXT")\n    return _A20_PRIOR_VIEW({**admission,"next_sequence":10569})\n\ndef validate_saved_seed_a10(admission:dict[str,object],seed:dict[str,object],\n        original:dict[str,object],save:dict[str,object],semantic:dict[str,object],\n        governance:dict[str,object],*,checked:_A20Callable[[object,int],dict[str,object]],\n        projector:object=None)->bool:\n    _a20_need(_a20_uint(admission.get("next_sequence"))==A20_NEXT,"actual A20 seed NEXT")\n    return _A20_PRIOR_SEED({**admission,"next_sequence":10569},seed,original,save,semantic,governance,\n                         checked=checked,projector=projector)\n'
SUPERVISOR_SUFFIX_V1='\nfrom typing import Callable as _A20AttemptCallable,Protocol as _A20AttemptProtocol\nclass _A20AttemptArgsV1(_A20AttemptProtocol):\n    attempt_nonce:str\n    task_nonce:str\n_A20_PRIOR_ATTEMPT:_A20AttemptCallable[[_A20AttemptArgsV1,object],object]=_validate_a15_attempt\n_A20_READ_FACT:_A20AttemptCallable[[object,int],object]=_a03_checked\ndef _a20_checked_fact_v1(reference:object,limit:int)->dict[str,object]:\n    return _a20_record(_A20_READ_FACT(reference,limit))\ndef _validate_a15_attempt(args:_A20AttemptArgsV1,config:object)->dict[str,object]:\n    value=_a20_record(_A20_PRIOR_ATTEMPT(args,config))\n    closed=validate_actual_A19_index_v1(A20_CLOSURE_REF,_a20_checked_fact_v1)\n    matches=0\n    for item in _a20_record(closed.get("sources")).values():\n        proof=_a20_record(item)\n        if Path(_a20_text(proof.get("path"))).name=="ROOT-FRESH-SUPERVISOR-CLOSED-C23-A15.json":\n            matches+=1\n            old=_a20_checked_fact_v1(proof,32768)\n            cleanup=_a20_record(old.get("owned_cleanup"))\n            used={_a20_text(old.get("attempt_nonce")),_a20_text(old.get("task_nonce")),\n                  _a20_text(cleanup.get("nonce"))}\n            _a20_need(args.attempt_nonce not in used and args.task_nonce not in used,"independent A20 nonces")\n    _a20_need(matches==1,"one actual predecessor supervisor closure")\n    return value\n'

def _historical_a18_closed_v1(module:ModuleType)->Dynamic:
    source=read_ref(fixed(OWN/"prepare_source31_a18_cold_union_v1.py",predecessor.BASE_PIN)).decode()
    body=function_source_v1(source,"_closed_v1")
    body=one(body,"def _closed_v1(","def _a20_historical_closed_v1(")
    body=one(body,'next_value = checked(p["current_next_ref"], 16384)',
             'next_value = {"next_sequence":closed["next_sequence"]}')
    # This function validates immutable A17 history; the live NEXT is checked separately.
    exec(compile(body,"<A20 exact historical closed projection>","exec"),vars(module))
    return dynamic(module,"_a20_historical_closed_v1")

def _current_pre_source_v1(module:ModuleType,p:PlanV1)->Dynamic:
    source=read_ref(fixed(OWN/"prepare_source31_a18_cold_union_v1.py",predecessor.BASE_PIN)).decode()
    body=function_source_v1(source,"_current_pre_v1")
    body=one(body,"def _current_pre_v1(","def _a20_current_pre_v1(")
    body=one(body,'review = checked(p["current_driver_review_ref"], 16384)',
             'review = checked(A20_PLAN["current_driver_review_ref"], 32768)')
    body=one(body,'"xar.A17-current-Driver-SAVE-review/v1"','"xar.A19-current-Driver-SAVE-review/v1"')
    body=one(body,"== 5281","== A20_DRIVER_HISTORY",2)
    body=one(body,'ref(PREVIOUS / "ROOT-C23-COLD-PRELAUNCH.json")',
             'ref(A20_PREVIOUS / "ROOT-C23-COLD-PRELAUNCH.json")')
    body=one(body,"actual_next_sequence=10569","actual_next_sequence=A20_PLAN['expected_next_sequence']")
    body=one(body,'materialized_driver_review=p["current_driver_review_ref"]',
             'materialized_driver_review=A20_PLAN["current_driver_review_ref"]')
    body=one(body,"    return current, enc(current)",
             "    current.update(actual_A19_closure=A20_PLAN['closure_ref'],actual_A19_driver_review=A20_PLAN['current_driver_review_ref'])\n    return current, enc(current)")
    review=checked(p["current_driver_review_ref"],32768)
    vars(module).update(A20_PLAN=p,A20_PREVIOUS=PREVIOUS,
                        A20_DRIVER_HISTORY=uint(review["Driver_history_rows"]))
    exec(compile(body,"<A20 exact current Driver validator>","exec"),vars(module))
    return dynamic(module,"_a20_current_pre_v1")

def runtime_closure_source_v1(p:PlanV1,pre:Doc,*,historical_pre_ref:ExactRef)->str:
    raw=read_ref(p["union_producer"]).decode()
    shared=read_ref(fixed(OWN/"file_stat_identity_v1.py",STAT_IDENTITY_PIN),16384).decode()
    shared=one(shared,"from __future__ import annotations\n","")
    identity_names=("FileStatIdentityWireV1","FileStatIdentityV1","StatIdentitySchema","SCHEMA",
                    "_integer","_decimal","normalize_file_stat_identity_v1","parse_file_stat_identity_v1")
    for name in identity_names:
        shared=re.sub(r"\b"+name+r"\b","_a20_stat_"+name,shared)
    code="import re\nfrom pathlib import Path\nfrom typing import Callable as _A20Callable,TypedDict\nDoc=dict[str,object]\nclass _A20Ref(TypedDict):\n    path:str\n    bytes:int\n    sha256:str\nMACHINE="+repr(MACHINE)+"\n"
    code=shared+"\n"+code
    names=("need","record","text","uint","refs","validate_closed_records_v1")
    for name in names:
        part=function_source_v1(raw,name)
        for old in names:
            part=re.sub(r"\b"+old+r"\b","_a20_"+old,part)
        part=re.sub(r"\bExactRef\b","_A20Ref",part)
        part=re.sub(r"\bparse_file_stat_identity_v1\b","_a20_stat_parse_file_stat_identity_v1",part)
        part=re.sub(r"\bSCHEMA\b","_a20_stat_SCHEMA",part)
        code+=part+"\n"
    constants={"A20_CLOSURE_REF":p["closure_ref"],"A20_REVIEW_REF":p["current_driver_review_ref"],
               "A20_NEXT":p["expected_next_sequence"],"A20_CURRENT_PRE":pre,
               "A20_HISTORICAL_PRE":refs(historical_pre_ref)}
    annotations={"A20_CLOSURE_REF":"_A20Ref","A20_REVIEW_REF":"_A20Ref","A20_NEXT":"int",
                 "A20_CURRENT_PRE":"dict[str,object]","A20_HISTORICAL_PRE":"_A20Ref"}
    for name,value in sorted(constants.items()):
        code+=name+":"+annotations[name]+"="+repr(json.loads(enc(value)))+"\n"
    return code+RUNTIME_SUFFIX_V1

def parse_source_map_v1(value:object)->dict[str,bytes]:
    row=record(value)
    need(bool(row),"nonempty actual source map")
    result:dict[str,bytes]={}
    for name,raw in row.items():
        if type(raw) is not bytes:raise ValueError("exact source bytes: "+name)
        result[name]=raw
    return result

def fresh_base_v1(plan_value:object)->ModuleType:
    p=parse_plan(plan_value);old=historical_plan_v1(p)
    module=load_verified_predecessor_v1(p["predecessor_producer_ref"])
    # Only the fresh private software namespace changes. Historical file inputs remain exact.
    vars(module).update(TARGET=TARGET,PREP=PREP,SCREEN=SCREEN)
    projected=dict(old)
    for key in ("observed_at_utc","attempt_nonce","task_nonce","full_storage_ref","live_storage_ref",
                "steam_native_state_ref","screen_admission_path"):
        projected[key]=p[key]
    base_value=dynamic(module,"fresh_base_v1")(projected)
    need(isinstance(base_value,ModuleType),"real complete A18/A19 factory")
    if not isinstance(base_value,ModuleType): raise ValueError("module")
    base=base_value;namespace=vars(base)
    historical=record(namespace["_a19_history_plan"])
    historical["union_producer"]=p["union_producer"]
    historical["current_next_ref"]=p["current_next_ref"]
    namespace.update(A19_FILE=__file__,_a19_history_plan=historical)
    immutable_closed=_historical_a18_closed_v1(base)
    old_build=dynamic(base,"_build_sources_v1")
    old_bridge=dynamic(base,"_bridge_v1")
    historical_pre=checked(ref(PREVIOUS/"ROOT-C23-COLD-PRELAUNCH.json"),32768)
    def closed(unused:object)->object:
        result=immutable_closed(historical);validate_closed_basis_v1(p);return result
    namespace["_closed_v1"]=closed
    current_pre=_current_pre_source_v1(base,p)
    namespace["_current_pre_v1"]=current_pre
    def bridge(unused:object,value:object)->object:
        history_source=text(old_bridge(historical,historical_pre))
        current_source=runtime_closure_source_v1(p,record(value),historical_pre_ref=ref(PREVIOUS/"ROOT-C23-COLD-PRELAUNCH.json"))
        marker="_A20_PRIOR_POST="
        need(current_source.count(marker)==1,"one current runtime wrapper boundary")
        prefix,tail=current_source.split(marker,1)
        return one(history_source,"_A18_PRIOR_POST=",prefix+"\n_A18_PRIOR_POST=")+"\n"+marker+tail
    namespace["_bridge_v1"]=bridge
    def build(unused:object,pre_value:object,history_value:object)->object:
        result=predecessor.previous.pair(old_build(unused,pre_value,history_value))
        source=parse_source_map_v1(result[0])
        source=patch_preflight_source_v1(source,read_ref(p["preflight_source_ref"],65536),
                                         expected=p["preflight_source_ref"])
        queue="root_p37c23_sdk_queue.py"
        source[queue]=fix_native32_queue_machine_v1(source[queue],machine_id=p["machine_id"])
        supervisor="root_native30_supervisor_c23.py"
        body=source[supervisor].decode()
        body=one(body,"type(actual_next) is int and actual_next==10569",
                 "type(actual_next) is int and actual_next=="+str(p["expected_next_sequence"]))
        marker="if __name__";index=body.rfind(marker);need(index>=0,"supervisor main marker")
        body=body[:index]+SUPERVISOR_SUFFIX_V1+"\n"+body[index:]
        source[supervisor]=body.encode()
        feeder="launch_a10_saved10480_feeder01.py"
        source[feeder]=patch_feeder_basis_v1(source[feeder],p)
        for name,raw in source.items():
            if name.endswith(".py"):compile(raw,name,"exec")
        return source,result[1]
    namespace["_build_sources_v1"]=build
    # The original first-sequence and saved-basis migrations remain single, explicit adapters.
    raw18=read_ref(p["base_producer_ref"]).decode()
    factory=function_source_v1(raw18,"_factory_v1")
    factory=one(factory,repr('"new_first_sequence=10569"'),repr('"new_first_sequence='+str(p["expected_next_sequence"])+'"'))
    factory=one(factory,'"spec-supervisor-a18"','"spec-supervisor-a20"')
    factory=one(factory,"__file__=__file__)","__file__=A19_FILE)")
    exec(compile(factory,"<A20 exact complete factory>","exec"),namespace)
    return base

def compose(plan_value:object,*,display_values:dict[str,bytes],display_review:Doc,
            companion_values:Outputs)->tuple[Outputs,Doc]:
    p=parse_plan(plan_value)
    need(not TARGET.exists() and ref(__file__)==p["union_producer"],"absent new runtime and actual producer")
    base=fresh_base_v1(p)
    result=predecessor.previous.pair(dynamic(base,"compose")(vars(base)["_a19_history_plan"],
        display_values=display_values,display_review=display_review,companion_values=companion_values))
    out=predecessor.previous.outputs(result[0]);quote=record(result[1])
    need(len(out)==uint(quote["unique_files"])==145,"complete145")
    quote.update(schema="xar.Source31-A20-complete-cold-quote/v1",producer=p["union_producer"],
        actual_A19_index=p["closure_ref"],current_driver_review=p["current_driver_review_ref"],
        predecessor_producer=p["predecessor_producer_ref"],predecessor_plan=p["predecessor_plan_ref"],
        canonical_preflight=p["preflight_source_ref"],new_first_sequence=p["expected_next_sequence"],
        feeder_admission_additions={"prior_A18_index":predecessor.fixed(
            PREVIOUS.with_name("runtime-a18")/"ROOT-A18-ACTUAL-CLOSURE-INDEX01.json",predecessor.CLOSURE_PIN),
            "prior_A19_index":p["closure_ref"]},launcher_artifact_cap_bytes=2147483648,
        full_generated_request_hard_limit=256,full_generated_request_soft_boundary=240,
        unknown10565_credit=0,original_wall_origin_reset=False,copies_created=0,
        actual_A19_journal=checked(p["closure_ref"],65536)["journal"])
    quote["historical_A17_readonly_journal"]=quote.pop("consumed_readonly_journal")
    quote["continuity_ledger"]=p["ledger_ref"]
    quote["stat_identity_contract"]=fixed(OWN/"file_stat_identity_v1.py",STAT_IDENTITY_PIN)
    return out,quote


def metadata_frontier_v1(source: str, *, expected_next_sequence: int) -> str:
    """Advance four current owner slots after the original historical validator."""
    need(type(source) is str, "actual metadata source text")
    target = uint(expected_next_sequence)
    need(target > 10570, "current post-bootstrap frontier")
    functions = {node.name: node for node in ast.parse(source).body
                 if isinstance(node, ast.FunctionDef)}
    raw = source.encode("utf-8")
    lines = raw.splitlines(keepends=True)
    changes: list[tuple[int, int]] = []
    for name, count in (("_base", 1), ("saved_basis", 1), ("compose", 2)):
        function = functions.get(name)
        need(function is not None, "one metadata function: " + name)
        if function is None:
            raise ValueError("metadata function")
        nodes = [node for node in ast.walk(function)
                 if isinstance(node, ast.Constant) and type(node.value) is int
                 and node.value == 10569]
        need(len(nodes) == count, "four exact current frontier slots: " + name)
        for node in nodes:
            need(node.end_lineno is not None and node.end_col_offset is not None,
                 "exact metadata literal boundary")
            if node.end_lineno is None or node.end_col_offset is None:
                raise ValueError("metadata literal boundary")
            begin = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
            end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
            need(raw[begin:end] == b"10569", "original current metadata literal")
            changes.append((begin, end))
    for begin, end in sorted(changes, reverse=True):
        raw = raw[:begin] + str(target).encode() + raw[end:]
    result = raw.decode("utf-8")
    compile(result, "<A20 current owner metadata frontier>", "exec")
    return result

def metadata_history_plan_v1(plan_value: object, base: ModuleType) -> Doc:
    p = parse_plan(plan_value)
    historical = dict(record(vars(base)["_a19_history_plan"]))
    historical["current_next_ref"] = historical_plan_v1(p)["current_next_ref"]
    return historical

METADATA_LOADER_PIN = (25193, '0e2befdca7cac51f13d9d7e4e85a5d66e5dad159eb127457207a3160072db004')

def registered_metadata_scope_v1(base: ModuleType, historical: Doc,
                                 namespace: Doc, runtime: Path) -> None:
    """Register the exact deployed bootstrap during the original metadata chain."""
    import importlib
    import importlib.util
    legacy = importlib.import_module("prepare_source28_a13_union_v1")
    loader: object = getattr(getattr(getattr(legacy, "base", None), "old", None),
                             "prior", None)
    need(isinstance(loader, ModuleType), "actual legacy metadata loader")
    if not isinstance(loader, ModuleType):
        raise ValueError("metadata loader module")
    need(Path(text(getattr(loader, "__file__", None))).resolve()
         == (OWN / "prepare_c23_a05_union_v1.py").resolve(), "exact original loader path")
    read_ref(fixed(OWN / "prepare_c23_a05_union_v1.py", METADATA_LOADER_PIN), 32768)
    original = dynamic(loader, "_module")
    bootstrap = runtime / "root_checkpoint_bootstrap_c23.py"
    freeze = checked(ref(runtime / "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json"), 2097152)
    policy = checked(freeze["canonical_preload_policy"], 65536)
    need(policy.get("machine_id") == MACHINE, "deployed policy machine")
    rows = sequence(policy["entry_source_pins"])
    need(len(rows) == 47, "original complete entry policy")
    matches = [sequence(row) for row in rows
               if len(sequence(row)) == 2 and Path(text(sequence(row)[0])).resolve()
               == bootstrap.resolve()]
    need(len(matches) == 1, "one deployed bootstrap source pin")
    digest = text(matches[0][1])
    need(re.fullmatch("[0-9a-f]{64}", digest) is not None, "bootstrap source SHA")
    expected = ref(bootstrap)
    need(expected["sha256"] == digest, "bootstrap bytes match original source policy")
    def registered(path: Path, name: str) -> object:
        if path.resolve() != bootstrap.resolve():
            return original(path, name)
        need(name in ("_a10_actual_bootstrap_metadata", "_a12_actual_business_bridge",
                      "_a13_actual_bootstrap"), "original metadata module name")
        read_ref(expected, 262144)
        spec = importlib.util.spec_from_file_location(name, path)
        need(spec is not None and spec.loader is not None, "actual bootstrap module spec")
        if spec is None or spec.loader is None:
            raise ValueError("bootstrap loader")
        module = importlib.util.module_from_spec(spec)
        previous_module = sys.modules.get(name)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            if sys.modules.get(name) is module:
                if previous_module is None:
                    del sys.modules[name]
                else:
                    sys.modules[name] = previous_module
            raise
        return module
    setattr(loader, "_module", registered)
    try:
        dynamic(base, "metadata_scope")(historical, namespace, runtime)
    finally:
        setattr(loader, "_module", original)

METADATA_BEFORE_PIN = (36232, 'a34626ecd39c2e651f11abb8df2d04e636170f440ca9690962821ca53e878ff5')

class MetadataForwardV1(TypedDict):
    schema: Literal["xar.Source31-A20-metadata-forward/v1"]
    original_plan_ref: ExactRef
    original_quote_ref: ExactRef
    before_archive_ref: ExactRef
    after_producer_ref: ExactRef
    scope: Literal["postguard_and_owner_metadata_only"]
    graph_bytes_changed: Literal[False]

def validate_metadata_forward_v1(plan_value: object, quote_value: object) -> None:
    p = parse_plan(plan_value)
    quote = record(quote_value)
    forward = record(quote.get("metadata_forward"))
    need(set(forward) == set(MetadataForwardV1.__annotations__), "single metadata forward model")
    need(forward["schema"] == "xar.Source31-A20-metadata-forward/v1"
         and forward["scope"] == "postguard_and_owner_metadata_only"
         and forward["graph_bytes_changed"] is False, "metadata-only forward authority")
    original_plan_ref = refs(forward["original_plan_ref"])
    original_quote_ref = refs(forward["original_quote_ref"])
    archive = refs(forward["before_archive_ref"])
    after = refs(forward["after_producer_ref"])
    need(after == ref(__file__) and after == p["union_producer"], "actual repaired metadata producer")
    need(Path(archive["path"]).resolve()
         == (PREP / "A20-UNION-PRE-METADATA-FIX01.py").resolve(),
         "immutable original producer archive")
    old_plan = parse_plan(checked(original_plan_ref, 16384))
    old_quote = checked(original_quote_ref, 262144)
    original_producer = old_plan["union_producer"]
    need(Path(original_producer["path"]).resolve() == Path(after["path"]).resolve()
         and (archive["bytes"], archive["sha256"]) == METADATA_BEFORE_PIN
         and (original_producer["bytes"], original_producer["sha256"]) == METADATA_BEFORE_PIN,
         "preserved original deployment producer")
    read_ref(archive, 65536)
    expected_plan = dict(old_plan)
    expected_plan["union_producer"] = after
    need(enc(p) == enc(expected_plan), "only metadata producer changes in the plan")
    need(refs(old_quote["producer"]) == original_producer, "original complete graph authority")
    expected_quote = dict(old_quote)
    expected_quote.update(producer=after, observed_at_utc=quote.get("observed_at_utc"),
                          status="DEPLOYED_GRAPH_METADATA_FORWARD_NOT_RUNTIME_ADMITTED",
                          metadata_forward=forward)
    need(datetime.fromisoformat(text(quote.get("observed_at_utc"))).utcoffset() is not None,
         "aware metadata forward observation")
    need(enc(quote) == enc(expected_quote), "all original graph facts and 145 file pins unchanged")

def metadata_source(plan_value:object,source:str)->str:
    p=parse_plan(plan_value);validate_closed_basis_v1(p);base=fresh_base_v1(p)
    value=text(dynamic(base,"metadata_source")(metadata_history_plan_v1(p,base),source))
    value=metadata_frontier_v1(value,expected_next_sequence=p["expected_next_sequence"])
    value=value.replace("ROOT-FINAL-SDK-FREEZE-P37C23-A20.json","ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")
    return one(value,"'native32_observer_binding':A18_NATIVE32_BINDING",
               "'native32_observer_binding':A18_NATIVE32_BINDING,'actual_A19_closure':A20_CLOSURE_REF")

def metadata_scope(plan_value:object,namespace:Doc,runtime:Path)->None:
    p=parse_plan(plan_value);base=fresh_base_v1(p)
    registered_metadata_scope_v1(base,metadata_history_plan_v1(p,base),namespace,runtime)
    namespace.update(A20_CLOSURE_REF=p["closure_ref"],A20_REVIEW_REF=p["current_driver_review_ref"],
                     A20_NEXT=p["expected_next_sequence"])


def patch_feeder_basis_v1(raw:bytes,p:PlanV1)->bytes:
    source=raw.decode()
    source=one(source,"prior_A18_index:Ref;budget:Ref","prior_A18_index:Ref;prior_A19_index:Ref;budget:Ref")
    source=one(source,'"prior_A18_index","budget"','"prior_A18_index","prior_A19_index","budget"')
    source=one(source,"class Bootstrap(Protocol):",
        "class Bootstrap(Protocol):\n def validate_actual_A19_index_v1(self,r:Ref,checked:Callable[[Ref,int],Json])->object:...")
    source=one(source,"def old_basis(a:Admit)->Json:\n",
        "def old_basis(a:Admit)->Json:\n need(a['prior_A19_index']==A20_CLOSURE_REF,'actual A19 NoFULL closure')\n"
        " current=cast(Bootstrap,importlib.import_module('root_checkpoint_bootstrap_c23'))\n"
        " current.validate_actual_A19_index_v1(a['prior_A19_index'],checked)\n")
    source=one(source,"KIND='A19_SAVE10480_A18_zero_RPC_rollback_verified'",
        "A20_CLOSURE_REF="+repr(json.loads(enc(p["closure_ref"])))+
        "\nKIND='A20_SAVE10480_A19_readonly_rollback_verified'")
    source=one(source,"last_A19_SAVE10480_A18_zero_RPC_rollback","last_A20_SAVE10480_A19_readonly_rollback")
    source=one(source,'"prior_A18_index":a["prior_A18_index"],',
        '"prior_A18_index":a["prior_A18_index"],"prior_A19_index":a["prior_A19_index"],')
    compile(source,"<A20 exact feeder current basis>","exec")
    return source.encode()

def build_plan(*,full_storage_ref:ExactRef,steam_native_state_ref:ExactRef,at_utc:datetime,
        attempt_nonce:str,task_nonce:str,closure_ref:ExactRef,current_driver_review_ref:ExactRef,
        current_next_ref:ExactRef,ledger_ref:ExactRef,predecessor_plan_ref:ExactRef,
        preflight_source_ref:ExactRef)->PlanV1:
    old=predecessor.parse_plan(checked(predecessor_plan_ref,16384))
    closed=checked(closure_ref,65536)
    value:Doc={**old,"schema":"xar.Source31-A20-complete-cold-input/v1",
        "observed_at_utc":at_utc.isoformat(),"attempt_nonce":attempt_nonce,"task_nonce":task_nonce,
        "full_storage_ref":full_storage_ref,"live_storage_ref":full_storage_ref,
        "steam_native_state_ref":steam_native_state_ref,"union_producer":ref(__file__),
        "closure_ref":closure_ref,"current_driver_review_ref":current_driver_review_ref,
        "current_next_ref":current_next_ref,"ledger_ref":ledger_ref,
        "screen_admission_path":str(SCREEN),"predecessor_plan_ref":predecessor_plan_ref,
        "predecessor_producer_ref":fixed(OWN/"prepare_source31_a19_cold_union_v1.py",PREDECESSOR_PIN),
        "preflight_source_ref":preflight_source_ref,"expected_next_sequence":uint(closed.get("next_sequence"))}
    result=parse_plan(value);historical_plan_v1(result);validate_closed_basis_v1(result)
    return result


def fix_native32_queue_machine_v1(source:bytes,*,machine_id:str)->bytes:
    need(type(source) is bytes and type(machine_id) is str and machine_id==MACHINE,
         "verified target machine for the new Queue")
    tree=ast.parse(source)
    uses=[n for n in ast.walk(tree) if isinstance(n,ast.Name) and n.id=="MACHINE"]
    need(len(uses)==1 and isinstance(uses[0].ctx,ast.Load),"one original unbound MACHINE use")
    for node in ast.walk(tree):
        if isinstance(node,ast.arg):need(node.arg!="MACHINE","no shadowed machine argument")
        elif isinstance(node,ast.alias):
            need((node.asname or node.name.split(".")[0])!="MACHINE","no machine import alias")
    before="            machine_id=MACHINE)\n"
    after="            machine_id="+repr(machine_id)+")\n"
    result=one(source.decode(),before,after).encode()
    need(not any(isinstance(n,ast.Name) and n.id=="MACHINE" for n in ast.walk(ast.parse(result))),
         "machine reference is bound to actual new source bytes")
    compile(result,"<A20 exact Native32 Queue machine binding>","exec")
    return result
