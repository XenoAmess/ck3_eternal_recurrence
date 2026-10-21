"""A19 cold graph: exact A18 software input, new attempt and bounded requests."""
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
from typing import Literal, Protocol, TypedDict, cast
import prepare_source29_a17_cold_union_v1 as previous

__all__ = ["previous"]
Doc = dict[str, object]
Outputs = dict[Path, bytes]
class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str
class Dynamic(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> object: ...
def need(ok: bool, why: str) -> None:
    if not ok: raise ValueError("A19: "+why)
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
MACHINE=previous.MACHINE
P,O,OWN=previous.P,previous.O,Path(__file__).resolve().parent
PREVIOUS=P/"robert30-v20261019-campaign01/runtime-a18"
TARGET=PREVIOUS.with_name("runtime-a19")
PREP=O/"source31-a19-prep01"
SCREEN=TARGET/"ROOT-SCREEN-ADMISSION-C23-A15.json"
NATIVE32_ADAPTER_NAME="observer_journal_runtime_v1.py"
NATIVE32_EXTENSION_NAME="native32_mcp_extension_v1.py"
NATIVE32_OBSERVER_BINDING_NAME="ROOT-NATIVE32-PRODUCTION-BINDING01.json"
BASE_PIN=(62371,"046a38da99c1cfe9c223c15406f1c8cfbac588423058d2b512c8af4a7f469817")
CLOSURE_PIN=(5728,"d2bbaa8486da9188b28e4a2451150190e9a1a10db8db6ab76631a958a6dd847e")
REVIEW_PIN=(3513,"2d69655f677a8f464a2a836f3b64529c41b9429f2019d053713d94f258d5cf8d")
BASE_PLAN_PIN=(4449,"a2769b3fd893a4b77de003433979e1e6eac6bdac975e1f1ee0063e01636abf92")
PLACEMENT_PIN=(21022,"db99bbcf549059edd04af1a803628e5468d50cd0ef5f7478f59a1d7c6cb66ecb")
RUN_ID_PIN=(18126,"35602d8dda91af287e746bb4b693128f872d2a05e228186b6f97743ddac1672f")
class PlanV1(TypedDict):
    schema: Literal["xar.Source31-A19-complete-cold-input/v1"]
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
def parse_plan(value: object) -> PlanV1:
    row=record(value)
    need(set(row)==set(PlanV1.__annotations__),"single24-field plan")
    need(row["schema"]=="xar.Source31-A19-complete-cold-input/v1" and row["machine_id"]==MACHINE
         and row["execution_owner"]=="Root" and row["root_direct_execution_release"] is True,"Root machine branch")
    for key in ("attempt_nonce","task_nonce"):
        need(re.fullmatch("[0-9a-f]{32}",text(row[key])) is not None,"nonce")
    need(row["attempt_nonce"]!=row["task_nonce"],"independent nonce")
    need(datetime.fromisoformat(text(row["observed_at_utc"])).utcoffset() is not None,"aware time")
    need(Path(text(row["screen_admission_path"])).resolve()==SCREEN.resolve(),"new screen")
    out=dict(row)
    for key in set(row)-{"schema","machine_id","execution_owner","root_direct_execution_release",
                        "observed_at_utc","attempt_nonce","task_nonce","screen_admission_path"}:
        out[key]=refs(row[key])
    need(out["full_storage_ref"]==out["live_storage_ref"],"same current full")
    return cast(PlanV1,out)

class CapacityV1(TypedDict):
    D_free_floor_bytes: int
    Z_free_floor_bytes: int
class RuntimeAdmissionV1(TypedDict):
    schema: Literal["xar.Source31-A19-runtime-prepare-admission/v1"]
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
    need(row.get("schema")=="xar.Source31-A19-runtime-prepare-admission/v1"
         and type(expected_machine_id) is str and bool(expected_machine_id)
         and row.get("machine_id")==expected_machine_id and row.get("owner")=="Root"
         and row.get("status")=="ADMITTED" and row.get("root_direct_execution_release") is True
         and row.get("canonical_capacity_review_passed") is True,"A19 admitted Root capacity")
    need("hard_bytes" not in row and not ({"D_conservative_floor_bytes","Z_conservative_floor_bytes"}&set(capacity)),"no legacy aliases")
    return {"schema":"xar.Source31-A19-runtime-prepare-admission/v1","machine_id":expected_machine_id,
        "owner":"Root","status":"ADMITTED","root_direct_execution_release":True,"canonical_capacity_review_passed":True,
        "plan":refs(row.get("plan")),"quote":refs(row.get("quote")),"full_storage_ref":refs(row.get("full_storage_ref")),
        "runtime_hard_bytes":positive(row.get("runtime_hard_bytes")),
        "capacity":{"D_free_floor_bytes":positive(capacity.get("D_free_floor_bytes")),
                    "Z_free_floor_bytes":positive(capacity.get("Z_free_floor_bytes"))}}

def validate_closed_records_v1(closed_value: object, review_value: object) -> None:
    closed=record(closed_value);review=record(review_value)
    game=record(closed.get("Game"));exits=record(closed.get("SDK_actual_exits"))
    need(closed.get("schema")=="xar.A18-sdk-initialization-failure-closed/v1"
         and closed.get("status")=="A18_CLOSED_NO_RPC_NO_REPLAY" and closed.get("machine_id")==MACHINE
         and closed.get("Tasks_absent") is True and closed.get("screen118_released") is True,"actual A18 closure")
    need(uint(game.get("pid"),2**32-1)==155680 and game.get("creation_filetime")=="134370234373653579"
         and uint(game.get("exit_code"))==1 and game.get("forced_owned_job_cleanup") is True
         and uint(game.get("Job_active_final"))==0 and set(exits)=={"sdk_queue","sdk_application"}
         and all(uint(exits[k])==1 for k in exits),"actual Game/SDK exits")
    for key,expected in (("next_sequence",10569),("saved_cycles",4753),("saved_days",5429),
                         ("live_settled_cycles",4758),("pending_cycle",4759),("RPC_calls",0),("new_day_credit",0)):
        need(uint(closed.get(key))==expected,"closed "+key)
    rollback=record(closed.get("next_cold_rollback"))
    need(set(rollback)=={"cycles","days"} and uint(rollback["cycles"])==5 and uint(rollback["days"])==0
         and closed.get("old_request_replayed") is False,"unknown not replayed; five lost historical cycles")
    need(review.get("schema")=="xar.A18-current-Driver-SAVE-review/v1" and review.get("machine_id")==MACHINE
         and uint(review.get("Driver_history_rows"))==5281 and uint(review.get("live_settled_cycles"))==4758
         and uint(review.get("saved_cycles"))==4753 and uint(review.get("saved_game_days"))==5429
         and uint(review.get("new_RPCs"))==0 and uint(review.get("new_day_credit"))==0
         and review.get("old_unknown10565_replayed") is False,"actual review and retained history")
    pending=record(review.get("pending_cycle"))
    need(uint(pending.get("global_turn"))==4759 and uint(pending.get("auto_sequence"))==10565
         and pending.get("stage")=="auto_unsettled","retained unknown10565")
    need(uint(record(review.get("next_sequence")).get("next_sequence"))==10569,"actual unchanged NEXT")

def history_plan_v1(plan_value: object, base_plan_value: object) -> Doc:
    p=parse_plan(plan_value);old=record(base_plan_value)
    need(old.get("schema")=="xar.Source31-A18-complete-cold-input/v1"
         and old.get("machine_id")==MACHINE,"true historical A18 plan")
    need(p["sdk_base_ref"]==refs(old.get("sdk_base_ref"))
         and p["canonical_anchor_ref"]==refs(old.get("canonical_anchor_ref"))
         and p["native_binding_ref"]==refs(old.get("native_binding_ref"))
         and p["ledger_ref"]==refs(old.get("ledger_ref")),"same SDK/native/history, no relabel")
    need(p["attempt_nonce"] not in (old.get("attempt_nonce"),old.get("task_nonce"))
         and p["task_nonce"] not in (old.get("attempt_nonce"),old.get("task_nonce")),"new attempt")
    out={k:v for k,v in p.items() if k not in ("base_cold_plan_ref","base_producer_ref")}
    out.update(schema="xar.Source31-A18-complete-cold-input/v1",
               closure_ref=refs(old.get("closure_ref")),current_driver_review_ref=refs(old.get("current_driver_review_ref")))
    return out

def validate_closed_basis_v1(plan_value: object) -> Doc:
    p=parse_plan(plan_value)
    need(p["closure_ref"]==fixed(PREVIOUS/"ROOT-A18-ACTUAL-CLOSURE-INDEX01.json",CLOSURE_PIN)
         and p["current_driver_review_ref"]==fixed(PREVIOUS/"ROOT-A18-CURRENT-DRIVER-SAVE-REVIEW01.json",REVIEW_PIN),"exact new predecessor")
    closed=checked(p["closure_ref"],16384);review=checked(p["current_driver_review_ref"],16384)
    validate_closed_records_v1(closed,review)
    sources=record(closed["sources"])
    need(any(refs(v)==p["current_driver_review_ref"] for v in sources.values()),"review in closure source set")
    for value in sources.values(): read_ref(value,131072)
    need(uint(checked(p["current_next_ref"],16384).get("next_sequence"))==10569,"current NEXT")
    return closed

def function_source_v1(raw: str, name: str) -> str:
    nodes=[n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name]
    need(len(nodes)==1,"one actual function "+name)
    value=ast.get_source_segment(raw,nodes[0])
    need(value is not None,"source segment")
    return text(value)

def runtime_closure_source_v1(p: PlanV1) -> str:
    names=("need","record","uint","validate_closed_records_v1")
    raw=read_ref(p["union_producer"]).decode()
    prefix="from typing import Callable as _A19Callable\nDoc=dict[str,object]\nMACHINE="+repr(MACHINE)+"\n"
    prefix+="\n\n".join(function_source_v1(raw,n) for n in names)+"\n"
    prefix+="A19_CLOSURE_REF="+repr(json.loads(enc(p["closure_ref"])))+"\nA19_REVIEW_REF="+repr(json.loads(enc(p["current_driver_review_ref"])))+"\n"
    return prefix+'''
def validate_actual_A18_index_v1(reference: object, checked: _A19Callable[[object,int],dict[str,object]]) -> dict[str,object]:
    need(reference==A19_CLOSURE_REF,"new actual A18 authority")
    x=checked(reference,16384);r=checked(A19_REVIEW_REF,16384)
    validate_closed_records_v1(x,r)
    for value in record(x.get("sources")).values(): _a14_verify_exact_fact(value)
    return x
'''

def fresh_base_v1(plan_value: object) -> ModuleType:
    p=parse_plan(plan_value)
    need(p["base_producer_ref"]==fixed(OWN/"prepare_source31_a18_cold_union_v1.py",BASE_PIN)
         and p["base_cold_plan_ref"]==fixed(O/"source31-a18-prep01/A18-COLD-PLAN03.json",BASE_PLAN_PIN),"exact base software/history")
    raw=read_ref(p["base_producer_ref"]).decode()
    historical=history_plan_v1(p,checked(p["base_cold_plan_ref"],16384))
    module=load_verified_base_v1(p["base_producer_ref"])
    ns=vars(module)
    ns.update(TARGET=TARGET,PREP=PREP,SCREEN=SCREEN,A19_FILE=__file__)
    old_closed=dynamic(module,"_closed_v1")
    old_pre=dynamic(module,"_current_pre_v1")
    old_bridge=dynamic(module,"_bridge_v1")
    old_build=dynamic(module,"_build_sources_v1")
    def closed(unused: object) -> object:
        result=old_closed(historical);validate_closed_basis_v1(p);return result
    def pre(unused: object) -> object:
        pair=previous.pair(old_pre(historical));value=record(pair[0])
        current=checked(p["current_driver_review_ref"],16384)
        old_review=checked(refs(historical["current_driver_review_ref"]),16384)
        for key in ("Driver","SAVE"):
            need(refs(record(current[key])["ref"])==refs(record(old_review[key])["ref"])
                 and record(current[key])["identity"]==record(old_review[key])["identity"],"unchanged current "+key)
        need(current["last_checkpoint"]==value["checkpoint"],"same original checkpoint")
        value.update(actual_A18_closure=p["closure_ref"],actual_A18_driver_review=p["current_driver_review_ref"],
                     loaded_cycles=4753,retained_historical_cycles=4758,A18_RPC_credit=0)
        return value,enc(value)
    def bridge(unused: object, value: object) -> object:
        source=text(old_bridge(historical,record(value)))
        addition=runtime_closure_source_v1(p)
        source=one(source,"_A18_PRIOR_POST=",addition+"\n_A18_PRIOR_POST=")
        source+='''
_A19_PRIOR_POST=validate_post_sem_driver
def validate_post_sem_driver(pre:dict[str,object],close:dict[str,object],checked:_A19Callable[[object,int],dict[str,object]],verify_current_stat:bool=True)->bool:
    need(pre.get("actual_A18_closure")==A19_CLOSURE_REF and pre.get("actual_A18_driver_review")==A19_REVIEW_REF,"A19 current pre")
    validate_actual_A18_index_v1(A19_CLOSURE_REF,checked)
    return _A19_PRIOR_POST(pre,close,checked,verify_current_stat)
'''
        return source
    def build(unused: object, pre_value: object, old_value: object) -> object:
        result=previous.pair(old_build(historical,pre_value,old_value))
        sources={k:v for k,v in cast(dict[str,bytes],result[0]).items()}
        launcher="launch_ck3_p37c23_fresh_owner.py"
        candidates=[name for name,body in sources.items() if b"17179869184" in body]
        need(len(candidates)==1,"one original launcher artifact CLI")
        launcher=candidates[0]
        sources[launcher]=one(sources[launcher].decode(),"17179869184","2147483648").encode()
        queue="root_p37c23_full_planner_queue.py"
        candidates=[name for name,body in sources.items() if b"class FreshQueue:" in body]
        need(len(candidates)==1,"one real Queue")
        queue=candidates[0];sources[queue]=patch_full_budget_v1(sources[queue].replace(str(TARGET).encode(),str(PREVIOUS).encode())).replace(str(PREVIOUS).encode(),str(TARGET).encode())
        supervisor="root_native30_supervisor.py"
        candidates=[name for name,body in sources.items() if b"_A18_PRIOR_ATTEMPT=_validate_a15_attempt" in body]
        need(len(candidates)==1,"one supervisor current guard")
        supervisor=candidates[0];s=sources[supervisor].decode()
        marker="if __name__"
        addition='''
_A19_PRIOR_ATTEMPT=_validate_a15_attempt
def _validate_a15_attempt(args,config):
    value=_A19_PRIOR_ATTEMPT(args,config)
    closed=validate_actual_A18_index_v1(A19_CLOSURE_REF,_a03_checked)
    last=_a03_checked(closed["sources"]["ROOT-FRESH-SUPERVISOR-CLOSED-C23-A15.json"],16384)
    require(args.attempt_nonce not in (last["attempt_nonce"],last["task_nonce"]) and args.task_nonce not in (last["attempt_nonce"],last["task_nonce"]),"independent A19 nonces")
    return value
'''
        index=s.rfind(marker);need(index>=0,"supervisor main marker")
        sources[supervisor]=(s[:index]+addition+s[index:]).encode()
        feeders=[name for name,body in sources.items() if b"def old_basis(a:Admit)->Json:" in body]
        need(len(feeders)==1,"one original feeder")
        sources[feeders[0]]=patch_feeder_current_basis_v1(sources[feeders[0]],p["closure_ref"])
        for name,body in sources.items():
            if name.endswith(".py"):compile(body,name,"exec")
        return sources,result[1]
    ns.update(_closed_v1=closed,_current_pre_v1=pre,_bridge_v1=bridge,_build_sources_v1=build)
    factory=function_source_v1(raw,"_factory_v1")
    factory=one(factory,'"spec-supervisor-a18"','"spec-supervisor-a19"')
    factory=one(factory,"__file__=__file__)","__file__=A19_FILE)")
    exec(compile(factory,"<A19 exact factory projection>","exec"),ns)
    compose_source=function_source_v1(raw,"compose")
    compose_source=one(compose_source,'ref(__file__)==p["union_producer"]','ref(A19_FILE)==p["union_producer"]')
    exec(compile(compose_source,"<A19 exact producer projection>","exec"),ns)
    ns["_a19_history_plan"]=historical
    return module

def compose(plan_value: object, *, display_values: dict[str,bytes], display_review: Doc,
            companion_values: Outputs) -> tuple[Outputs,Doc]:
    p=parse_plan(plan_value);base=fresh_base_v1(p)
    need(ref(__file__)==p["union_producer"],"actual A19 producer")
    result=previous.pair(dynamic(base,"compose")(vars(base)["_a19_history_plan"],
        display_values=display_values,display_review=display_review,companion_values=companion_values))
    out=previous.outputs(result[0]);quote=record(result[1])
    need(len(out)==uint(quote["unique_files"])==145,"preserved complete145")
    quote.update(schema="xar.Source31-A19-complete-cold-quote/v1",producer=p["union_producer"],
        actual_A18_index=p["closure_ref"],current_driver_review=p["current_driver_review_ref"],
        base_producer=p["base_producer_ref"],base_cold_plan=p["base_cold_plan_ref"],
        launcher_artifact_cap_bytes=2147483648,full_generated_request_hard_limit=256,
        full_generated_request_soft_boundary=240,loaded_saved_cycles=4753,
        retained_historical_Driver_cycles=4758,A18_new_cycles=0,A18_RPC_calls=0,
        feeder_admission_additions={"prior_A18_index":p["closure_ref"]},
        placement_execution_source=fixed(OWN/"managed_desktop1_placement.py",PLACEMENT_PIN),
        placement_identity_source=fixed(OWN.parent/"ck3_live_run_id.py",RUN_ID_PIN))
    for key in ("placement_execution_source","placement_identity_source"):read_ref(quote[key],32768)
    return out,quote
def metadata_source(plan_value: object, source: str) -> str:
    p=parse_plan(plan_value);base=fresh_base_v1(p)
    value=text(dynamic(base,"metadata_source")(vars(base)["_a19_history_plan"],source))
    value=value.replace("ROOT-FINAL-SDK-FREEZE-P37C23-A19.json","ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")
    return one(value,"'native32_observer_binding':A18_NATIVE32_BINDING",
        "'native32_observer_binding':A18_NATIVE32_BINDING,'actual_A18_closure':A19_CLOSURE_REF")
def metadata_scope(plan_value: object, namespace: Doc, runtime: Path) -> None:
    p=parse_plan(plan_value);base=fresh_base_v1(p)
    dynamic(base,"metadata_scope")(vars(base)["_a19_history_plan"],namespace,runtime)
    namespace.update(A19_CLOSURE_REF=p["closure_ref"],A19_REVIEW_REF=p["current_driver_review_ref"])

def patch_full_budget_v1(raw: bytes) -> bytes:
    need((len(raw),sha(raw))==(276757,"2b20fbe74f5bd46f8f2cfcbfe833a6ae103aea613ac7d8d742a0f61d67f6295a"),"exact normalized Queue")
    helper = 'class _FullGeneratedBudgetOwnerV1(Protocol):\n    held_control: str | None\n    current_attempt: object | None\n\n    def guard(self, *, reserve: bool = True) -> None: ...\n\n\nclass _FullGeneratedBudgetV1:\n    def __init__(self, control_name: str, owner: _FullGeneratedBudgetOwnerV1) -> None:\n        if not isinstance(control_name, str) or not control_name:\n            raise ValueError("FULL budget requires its control filename")\n        self.control_name: str = control_name\n        self.owner: _FullGeneratedBudgetOwnerV1 = owner\n        self.count: int = 0\n\n    def before_write(self) -> None:\n        if self.owner.held_control != self.control_name:\n            return\n        if type(self.count) is not int or self.count < 0:\n            raise ValueError("FULL generated request counter changed")\n        self.owner.current_attempt = None\n        if self.count >= 256:\n            raise RuntimeError("FULL generated request budget exhausted before enqueue; no new RPC")\n        self.owner.guard()\n        self.count += 1\n\n    def should_finish(self) -> bool:\n        if type(self.count) is not int or self.count < 0:\n            raise ValueError("FULL generated request counter changed")\n        return self.owner.held_control == self.control_name and self.count >= 240\n\n\n_FULL_GENERATED_BUDGET_V1: _FullGeneratedBudgetV1 | None = None\n\n\ndef _begin_full_generated_budget_v1(\n    control_name: str, owner: _FullGeneratedBudgetOwnerV1,\n) -> _FullGeneratedBudgetV1:\n    global _FULL_GENERATED_BUDGET_V1\n    budget = _FullGeneratedBudgetV1(control_name, owner)\n    _FULL_GENERATED_BUDGET_V1 = budget\n    return budget\n\n\ndef _before_full_generated_write_v1(path: Path) -> None:\n    if path.parent == INBOX and _FULL_GENERATED_BUDGET_V1 is not None:\n        _FULL_GENERATED_BUDGET_V1.before_write()\n\n\n'
    changes=(
        ("import argparse\n","import argparse\nfrom typing import Protocol\n"),
        ("class FreshQueue:\n",helper+"class FreshQueue:\n"),
        ('        if len(payload) > limit:\n            raise ValueError("finite receipt bound exceeded: " + str(path))\n',
         '        if len(payload) > limit:\n            raise ValueError("finite receipt bound exceeded: " + str(path))\n        _before_full_generated_write_v1(path)\n'),
        ("        self.held_control = path.name\n        self.loop_count += 1",
         "        self.held_control = path.name\n        generated_budget = _begin_full_generated_budget_v1(path.name, self)\n        self.loop_count += 1"),
        ('                if isinstance(state.get("pending_unsafe_route_halt"), dict):\n',
         '                if (settled and state["pending_cycle"] is None and state["pending_checkpoint"] is None\n                        and generated_budget.should_finish()):\n                    break\n                if isinstance(state.get("pending_unsafe_route_halt"), dict):\n'),
        ('                pending = state["pending_cycle"]\n',
         '                if settled and state["pending_cycle"] is None and generated_budget.should_finish():\n                    break\n                pending = state["pending_cycle"]\n'))
    result=raw.decode()
    for before,after in changes: result=one(result,before,after)
    out=result.encode()
    need((len(out),sha(out))==(279022, '409adbf3476ffd5123d106320562a37fcda06736096a08e53dd1ee6c2f2206a4'),"exact bounded Queue postimage")
    compile(out,"<A19 bounded Queue>","exec")
    return out

def load_verified_base_v1(value: object) -> ModuleType:
    reference=refs(value)
    need(reference==fixed(OWN/"prepare_source31_a18_cold_union_v1.py",BASE_PIN),"exact base source")
    raw=read_ref(reference)
    module=ModuleType("_a19_exact_a18_"+uuid.uuid4().hex)
    module.__file__=reference["path"]
    sys.modules[module.__name__]=module
    exec(compile(raw,module.__file__,"exec"),vars(module))
    need(Path(text(module.__file__)).read_bytes()==raw,"extraction path matches verified bytes")
    return module

def build_plan(*, full_storage_ref: ExactRef, steam_native_state_ref: ExactRef,
        at_utc: datetime, attempt_nonce: str, task_nonce: str) -> PlanV1:
    base_plan_ref=fixed(O/"source31-a18-prep01/A18-COLD-PLAN03.json",BASE_PLAN_PIN)
    old=checked(base_plan_ref,16384)
    value:Doc={**old,"schema":"xar.Source31-A19-complete-cold-input/v1",
        "observed_at_utc":at_utc.isoformat(),"attempt_nonce":attempt_nonce,"task_nonce":task_nonce,
        "full_storage_ref":full_storage_ref,"live_storage_ref":full_storage_ref,
        "steam_native_state_ref":steam_native_state_ref,"union_producer":ref(__file__),
        "closure_ref":fixed(PREVIOUS/"ROOT-A18-ACTUAL-CLOSURE-INDEX01.json",CLOSURE_PIN),
        "current_driver_review_ref":fixed(PREVIOUS/"ROOT-A18-CURRENT-DRIVER-SAVE-REVIEW01.json",REVIEW_PIN),
        "current_next_ref":ref(refs(old["current_next_ref"])["path"]),
        "screen_admission_path":str(SCREEN),"base_cold_plan_ref":base_plan_ref,
        "base_producer_ref":fixed(OWN/"prepare_source31_a18_cold_union_v1.py",BASE_PIN)}
    return parse_plan(value)

def patch_feeder_current_basis_v1(raw: bytes, closure: ExactRef) -> bytes:
    source=raw.decode()
    source=one(source,"prior_A17_index:Ref;budget:Ref","prior_A17_index:Ref;prior_A18_index:Ref;budget:Ref")
    source=one(source,'"prior_A17_index","budget"','"prior_A17_index","prior_A18_index","budget"')
    source=one(source,"class Bootstrap(Protocol):",
        "class Bootstrap(Protocol):\n def validate_actual_A18_index_v1(self,r:Ref,checked:Callable[[Ref,int],Json])->object:...")
    source=one(source,"def old_basis(a:Admit)->Json:\n","def old_basis(a:Admit)->Json:\n"
        " need(a['prior_A18_index']==A19_CLOSURE_REF,'actual A18 zero-RPC closure')\n"
        " current=cast(Bootstrap,importlib.import_module('root_checkpoint_bootstrap_c23'))\n"
        " current.validate_actual_A18_index_v1(a['prior_A18_index'],checked)\n")
    source=one(source,"KIND='A18_SAVE10480_A17_rollback_verified'",
        "A19_CLOSURE_REF="+repr(json.loads(enc(closure)))+"\nKIND='A19_SAVE10480_A18_zero_RPC_rollback_verified'")
    source=one(source,"last_A18_SAVE10480_A17_rollback","last_A19_SAVE10480_A18_zero_RPC_rollback")
    source=one(source,'"prior_A17_index":a["prior_A17_index"],',
        '"prior_A17_index":a["prior_A17_index"],"prior_A18_index":a["prior_A18_index"],')
    compile(source,"<A19 exact feeder basis>","exec")
    return source.encode()
