"""Portable real A19 parsers and original atomic consumer; no D assets or RPC."""
from __future__ import annotations
import ast
import contextlib
import copy
import io
import json
import sys
import types
import unittest
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Protocol, cast
import prepare_source31_a19_cold_union_v1 as m
import prepare_source31_a19_owner_metadata_v1 as owner

QUEUE_ATOMIC_BEFORE = 'def atomic_payload_v1(path, payload, *, replace=False, limit=REPLY_RESERVE):\n    with _control_span_v1("atomic_write"):\n        if not isinstance(payload, bytes):\n            raise TypeError(\'atomic payload must be bytes\')\n        if len(payload) > limit:\n            raise ValueError("finite receipt bound exceeded: " + str(path))\n        pending = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")\n        try:\n            with pending.open("xb") as stream:\n                stream.write(payload)\n                stream.flush()\n            if replace:\n                # Windows readers can briefly deny deletion during an atomic swap.\n                # Retry only the local file replacement, never an SDK/Game action.\n                deadline = time.monotonic() + 2.0\n                while True:\n                    try:\n                        os.replace(pending, path)\n                        break\n                    except PermissionError:\n                        if time.monotonic() >= deadline:\n                            raise\n                        time.sleep(.025)\n            else:\n                # Windows rename refuses an existing destination. No result is overwritten.\n                pending.rename(path)\n        finally:\n            pending.unlink(missing_ok=True)'

class Call(Protocol):
    def __call__(self,*args:object,**kwargs:object)->object: ...
def call(namespace:dict[str,object],name:str,*args:object,**kwargs:object)->object:
    value=namespace[name]
    if not callable(value):raise TypeError(name)
    return cast(Call,value)(*args,**kwargs)
def pin()->m.ExactRef:
    return {"path":str(Path(__file__).resolve()),"bytes":1,"sha256":"a"*64}
def plan()->m.Doc:
    result:m.Doc={key:pin() for key in m.PlanV1.__annotations__}
    result.update(schema="xar.Source31-A19-complete-cold-input/v1",machine_id=m.MACHINE,
        execution_owner="Root",root_direct_execution_release=True,observed_at_utc="2026-10-21T03:15:00+00:00",
        attempt_nonce="1"*32,task_nonce="2"*32,screen_admission_path=str(m.SCREEN))
    return result
def closed_pair()->tuple[m.Doc,m.Doc]:
    closed:m.Doc={"schema":"xar.A18-sdk-initialization-failure-closed/v1","status":"A18_CLOSED_NO_RPC_NO_REPLAY",
        "machine_id":m.MACHINE,"Tasks_absent":True,"screen118_released":True,
        "Game":{"pid":155680,"creation_filetime":"134370234373653579","exit_code":1,
            "forced_owned_job_cleanup":True,"Job_active_final":0},"SDK_actual_exits":{"sdk_queue":1,"sdk_application":1},
        "next_sequence":10569,"saved_cycles":4753,"saved_days":5429,"live_settled_cycles":4758,
        "pending_cycle":4759,"RPC_calls":0,"new_day_credit":0,"next_cold_rollback":{"cycles":5,"days":0},
        "old_request_replayed":False}
    review:m.Doc={"schema":"xar.A18-current-Driver-SAVE-review/v1","machine_id":m.MACHINE,
        "Driver_history_rows":5281,"live_settled_cycles":4758,"saved_cycles":4753,"saved_game_days":5429,
        "new_RPCs":0,"new_day_credit":0,"old_unknown10565_replayed":False,
        "pending_cycle":{"global_turn":4759,"auto_sequence":10565,"stage":"auto_unsettled"},
        "next_sequence":{"next_sequence":10569}}
    return closed,review
class Owner:
    def __init__(self)->None:
        self.held_control:str|None="FULL-test"
        self.current_attempt:object|None={"previous":"successful MET"}
        self.trace:list[str]=[]
    def guard(self,*,reserve:bool=True)->None:
        self.trace.append("guard")
class MemoryStream:
    def __init__(self,trace:list[str])->None:self.trace=trace
    def __enter__(self)->MemoryStream:self.trace.append("open");return self
    def __exit__(self,*args:object)->None:return None
    def write(self,payload:bytes)->int:self.trace.append("write");return len(payload)
    def flush(self)->None:self.trace.append("flush")
class MemoryPath:
    def __init__(self,parent:Path,name:str,trace:list[str])->None:
        self.parent,self.name,self.trace=parent,name,trace
    def with_name(self,name:str)->MemoryPath:return MemoryPath(self.parent,name,self.trace)
    def open(self,mode:str)->MemoryStream:
        if mode!="xb":raise ValueError(mode)
        return MemoryStream(self.trace)
    def rename(self,other:object)->None:self.trace.append("rename")
    def unlink(self,*,missing_ok:bool)->None:self.trace.append("unlink")
def atomic_namespace()->dict[str,object]:
    node=next(n for n in ast.parse(Path(m.__file__).read_text(encoding="utf-8")).body
              if isinstance(n,ast.FunctionDef) and n.name=="patch_full_budget_v1")
    assignment=next(n for n in ast.walk(node) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=="helper" for t in n.targets))
    helper=ast.literal_eval(assignment.value)
    if type(helper) is not str:raise TypeError("actual helper")
    ns:dict[str,object]={"Protocol":Protocol,"Path":Path,"INBOX":Path("software-inbox"),
        "REPLY_RESERVE":4096,"_control_span_v1":lambda unused:contextlib.nullcontext(),
        "uuid":__import__("uuid")}
    changes=next(n for n in ast.walk(node) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=="changes" for t in n.targets))
    permitted=(ast.Tuple,ast.Constant,ast.Name,ast.Add,ast.BinOp,ast.Load)
    if any(not isinstance(n,permitted) for n in ast.walk(changes.value)):
        raise ValueError("actual pure patch tuple only")
    value:object=eval(compile(ast.Expression(changes.value),"<actual producer changes>","eval"),
                      {"__builtins__":{},"helper":helper})
    if not isinstance(value,tuple):raise TypeError("patch tuple")
    pairs:list[tuple[str,str]]=[]
    for pair in value:
        if (not isinstance(pair,tuple) or len(pair)!=2
                or type(pair[0]) is not str or type(pair[1]) is not str):
            raise TypeError("exact source patch pair")
        if "finite receipt bound exceeded" in pair[0]:pairs.append((pair[0],pair[1]))
    if len(pairs)!=1:raise ValueError("one actual atomic hook")
    source=m.one(QUEUE_ATOMIC_BEFORE,*pairs[0])
    exec(compile(helper+"\n"+source,"<actual Queue atomic consumer>","exec"),ns)
    return ns
class A19Tests(unittest.TestCase):
    def test_plan_roundtrip(self)->None:
        valid=plan()
        self.assertEqual(m.parse_plan(json.loads(m.enc(valid))),m.parse_plan(valid))
        for key,value in (("schema","xar.Source31-A18-complete-cold-input/v1"),
            ("root_direct_execution_release",1),("observed_at_utc","2026-10-21T03:15:00"),
            ("attempt_nonce","x"*32),("screen_admission_path",str(m.PREVIOUS/"old.json"))):
            row=copy.deepcopy(valid);row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.parse_plan(row)
        for bad in (True,1.0,None,0,-1,2**53):
            row=copy.deepcopy(valid);r=m.record(row["sdk_base_ref"]);r["bytes"]=bad;row["sdk_base_ref"]=r
            with self.subTest(bad=bad),self.assertRaises(ValueError):m.parse_plan(row)
        for key in valid:
            row=copy.deepcopy(valid);row.pop(key)
            with self.subTest(missing=key),self.assertRaises(ValueError):m.parse_plan(row)
    def test_admission(self)->None:
        valid:m.Doc={"schema":"xar.Source31-A19-runtime-prepare-admission/v1","machine_id":m.MACHINE,
            "owner":"Root","status":"ADMITTED","root_direct_execution_release":True,
            "canonical_capacity_review_passed":True,"plan":pin(),"quote":pin(),"full_storage_ref":pin(),
            "runtime_hard_bytes":3145728,"capacity":{"D_free_floor_bytes":123,"Z_free_floor_bytes":456}}
        self.assertEqual(m.parse_runtime_admission_v1(valid,expected_machine_id=m.MACHINE),
            m.parse_runtime_admission_v1(json.loads(m.enc(valid)),expected_machine_id=m.MACHINE))
        for field in valid:
            row=copy.deepcopy(valid);row.pop(field)
            with self.subTest(missing=field),self.assertRaises(ValueError):m.parse_runtime_admission_v1(row,expected_machine_id=m.MACHINE)
        for bad in (True,1.0,0,-1,None,2**53):
            row=copy.deepcopy(valid);row["runtime_hard_bytes"]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):m.parse_runtime_admission_v1(row,expected_machine_id=m.MACHINE)
        for field,value in (("schema","xar.Source31-A18-runtime-prepare-admission/v1"),
                            ("hard_bytes",3145728),("canonical_capacity_review_passed",1)):
            row=copy.deepcopy(valid);row[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):m.parse_runtime_admission_v1(row,expected_machine_id=m.MACHINE)
    def test_closure_retained_history(self)->None:
        closed,review=closed_pair();m.validate_closed_records_v1(*json.loads(m.enc([closed,review])))
        for target,fields in ((closed,("next_sequence","saved_cycles","saved_days","RPC_calls")),
                              (review,("Driver_history_rows","saved_cycles","new_RPCs"))):
            for key in fields:
                for bad in (True,float(m.uint(target[key])),None):
                    c,r=copy.deepcopy((closed,review));(c if target is closed else r)[key]=bad
                    with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):m.validate_closed_records_v1(c,r)
        c=copy.deepcopy(closed);c["saved_cycles"]=4758
        with self.assertRaises(ValueError):m.validate_closed_records_v1(c,review)
    def test_explicit_history_view(self)->None:
        current=plan();old=copy.deepcopy(current)
        old.update(schema="xar.Source31-A18-complete-cold-input/v1",attempt_nonce="3"*32,task_nonce="4"*32,
                   closure_ref={**pin(),"sha256":"b"*64},current_driver_review_ref={**pin(),"sha256":"c"*64})
        frozen=copy.deepcopy(current)
        projected=m.history_plan_v1(current,old)
        self.assertEqual(current,frozen)
        self.assertEqual(projected["closure_ref"],old["closure_ref"])
        self.assertEqual(projected["task_nonce"],current["task_nonce"])
        self.assertEqual(projected["current_next_ref"],current["current_next_ref"])
    def test_exact_fresh_base(self)->None:
        reference=m.fixed(m.OWN/"prepare_source31_a18_cold_union_v1.py",m.BASE_PIN)
        first=m.load_verified_base_v1(reference);second=m.load_verified_base_v1(reference)
        self.assertIsNot(first,second)
        self.assertIs(sys.modules[first.__name__],first)
        source=m.read_ref(reference).decode()
        self.assertEqual(m.function_source_v1(source,"native32_source_stage_v2"),
            call(vars(first),"function_source_v1",first,"native32_source_stage_v2"))
        self.assertIn("from xar_autoplayer.bridge.mcp_server import _forbid_unknown_tool_arguments_v1",source)
        with self.assertRaises(ValueError):m.load_verified_base_v1({**reference,"sha256":"0"*64})
    def test_budget_actual_atomic(self)->None:
        ns=atomic_namespace();o=Owner()
        budget=call(ns,"_begin_full_generated_budget_v1","FULL-test",o)
        trace=o.trace;request=MemoryPath(Path("software-inbox"),"AUTO.json",trace)
        for count in range(256):
            call(ns,"atomic_payload_v1",request,b"{}")
            self.assertEqual(getattr(budget,"count"),count+1)
        self.assertEqual(trace.count("open"),256);self.assertLess(trace.index("guard"),trace.index("open"))
        self.assertIsNone(o.current_attempt);before=list(trace)
        with self.assertRaises(RuntimeError):call(ns,"atomic_payload_v1",request,b"{}")
        self.assertEqual(trace,before)
        o.held_control=None
        call(ns,"atomic_payload_v1",request,b"{}")
        self.assertEqual(getattr(budget,"count"),256)
        o.held_control="NEW";next_budget=call(ns,"_begin_full_generated_budget_v1","NEW",o)
        self.assertEqual(getattr(next_budget,"count"),0)
        class EqualCounter(IntEnum):
            LIMIT=240
        for bad in (True,1.0,-1,None,EqualCounter.LIMIT):
            setattr(next_budget,"count",bad)
            with self.subTest(bad=bad),self.assertRaises(ValueError):call(ns,"atomic_payload_v1",request,b"{}")
            with self.subTest(soft=bad),self.assertRaises(ValueError):
                call({"soft":getattr(next_budget,"should_finish")},"soft")
        setattr(next_budget,"count",240)
        self.assertIs(call({"soft":getattr(next_budget,"should_finish")},"soft"),True)
    def test_actual_runtime_json_boundary(self)->None:
        value=plan()
        value["union_producer"]=m.ref(m.__file__)
        value["closure_ref"]={**pin(),"sha256":"b"*64}
        value["current_driver_review_ref"]={**pin(),"sha256":"c"*64}
        parsed=m.parse_plan(value)
        closed,review=closed_pair()
        closed["sources"]={}
        def verified(reference:object,limit:int)->m.Doc:
            if reference==parsed["closure_ref"]:return closed
            if reference==parsed["current_driver_review_ref"]:return review
            raise ValueError("unexpected reference")
        def forbidden(value:object)->None:raise AssertionError("no source fact reached")
        ns:dict[str,object]={"_a14_verify_exact_fact":forbidden}
        exec(compile(m.runtime_closure_source_v1(parsed),"<actual A19 runtime JSON entry>","exec"),ns)
        self.assertEqual(call(ns,"validate_actual_A18_index_v1",parsed["closure_ref"],verified),closed)
        invalid_sources:tuple[object,...]=(None,[],True,1.0,3,"sources")
        for bad in invalid_sources:
            closed["sources"]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                call(ns,"validate_actual_A18_index_v1",parsed["closure_ref"],verified)
        closed.pop("sources")
        with self.assertRaises(ValueError):
            call(ns,"validate_actual_A18_index_v1",parsed["closure_ref"],verified)
    def test_real_owner_projection_name_binding_and_model(self)->None:
        from unittest.mock import patch
        captured:list[str]=[]
        original=m.function_source_v1
        def capture(raw:str,name:str)->str:
            captured.append(raw)
            result:object=original(raw,name)
            if type(result) is not str:raise TypeError("typed source")
            return result
        with patch.object(m,"function_source_v1",side_effect=capture):
            actual=owner._load_v1()
        value=plan();value["union_producer"]=m.ref(m.__file__)
        parsed=m.parse_plan(value)
        with patch.object(actual,"checked",return_value=parsed):
            with self.assertRaisesRegex(ValueError,"exact new predecessor"):
                m.dynamic(actual,"validate_source31_owner_basis_v1")({"cold_graph_plan":pin()},m)
        names:object=getattr(actual,"OUTPUT_NAMES")
        if not isinstance(names,tuple):raise TypeError("output names")
        self.assertEqual(names[0],"ROOT-C23-A19-COLD-OWNER-RECORDING-BINDING.json")
        self.assertNotIn("ROOT-C23-A19-ACTUAL-RECORDING-BINDING.json",names)
        tree=ast.parse(captured[-1])
        cold=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="cold_owner")
        scope=next(n for n in cold.body if isinstance(n,ast.FunctionDef) and n.name=="metadata_scope")
        assignments:list[ast.stmt]=[n for n in scope.body if isinstance(n,ast.Assign)]
        self.assertEqual(len(assignments),2)
        namespace:dict[str,object]={}
        env:dict[str,object]={"namespace":namespace,"OUTPUT_NAMES":names}
        exec(compile(ast.Module(body=assignments,type_ignores=[]),"<actual metadata model assignments>","exec"),env)
        self.assertEqual(namespace,{"BINDING_NAME":names[0],"OUTPUT_NAMES":names})
    def test_owner_literal_and_legacy_rejection(self)->None:
        module=owner._load_v1()
        self.assertEqual(getattr(module,"TARGET"),m.TARGET)
        self.assertIn("xar.C23-A19-cold-owner-metadata-input/v1",str(getattr(module,"OwnerInputV1").__annotations__))
        with self.assertRaises(ValueError):owner.parse_owner_inputs_v1({"schema":"xar.C23-A18-cold-owner-metadata-input/v1"},at_utc=datetime.now(timezone.utc))
if __name__=="__main__":unittest.main()
