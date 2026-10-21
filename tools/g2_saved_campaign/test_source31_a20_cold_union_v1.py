
"""Portable A20 contracts. Software fixtures confer no Game or Native runtime admission."""
from __future__ import annotations
import ast
import asyncio
import copy
from collections.abc import Coroutine
from datetime import datetime,timezone
from enum import IntEnum
import importlib.util
import json
from pathlib import Path
import sys
from types import CodeType,ModuleType
import unittest
from unittest.mock import patch
from typing import Callable,cast
import prepare_source31_a20_cold_union_v1 as m

HERE=Path(__file__).resolve().parent
class EqualInt(IntEnum):
    frontier=10572

def pin()->m.ExactRef:
    return m.ref(HERE/"prepare_source31_a19_cold_union_v1.py")

def plan()->m.PlanV1:
    value:m.Doc={key:pin() for key in m.PlanV1.__annotations__}
    value.update(schema="xar.Source31-A20-complete-cold-input/v1",machine_id=m.MACHINE,
        execution_owner="Root",root_direct_execution_release=True,
        observed_at_utc="2026-10-21T04:00:00+00:00",attempt_nonce="1"*32,task_nonce="2"*32,
        screen_admission_path=str(m.SCREEN),expected_next_sequence=10572,
        union_producer=pin())
    return m.parse_plan(value)

def closed_pair()->tuple[m.Doc,m.Doc]:
    item={"ref":pin(),"identity":{"bytes":pin()["bytes"],"file_id":str(2**53+1),"mtime_ns":str(2**63+1)},
          "stable_before_after":True}
    closed:m.Doc={"schema":"xar.A19-readonly-bootstrap-closed/v1",
        "status":"A19_CLOSED_NO_FULL_NO_REPLAY","machine_id":m.MACHINE,
        "Game":{"pid":123,"creation_filetime":str(2**53+7),"exit_code":1,
                "forced_owned_job_cleanup":True,"Job_active_final":0},
        "SDK_actual_exits":{"sdk_queue":0,"sdk_application":0},"Tasks_absent":True,
        "screen120_released":True,"next_sequence":10572,"saved_cycles":4753,"saved_days":5429,
        "live_settled_cycles":4758,"pending_cycle":4759,"FULL_requests":0,
        "new_cycle_credit":0,"new_day_credit":0,"old_request_replayed":False,
        "next_cold_rollback":{"cycles":5,"days":0},"sources":{"software":pin()},"actual_A19_completed_cycles":4753,
        "actual_A19_pending_cycle":None,"pending_cycle_scope":"retained_A17_unknown_AUTO10565_not_A19_active",
        "feeder_launched":False,"feeder_attach_occurred":False,"SDK_control_requests_completed":3,
        "SEM":{"sequence":10569,"status":"verified","result":pin()},
        "CAP":{"sequence":10570,"status":"verified_cold_checkpoint_active_resumed","result":pin()},
        "journal":{"sequence":10571,"status":"postvalidation_failed","result":pin(),
          "actual_native_journal_requests":1,"native32_result_validated_present":False,
          "drain_fence":False,"absence_is_nonexecution_proof":False}}
    review:m.Doc={"schema":"xar.A19-current-Driver-SAVE-review/v1","machine_id":m.MACHINE,
        "saved_cycles":4753,"saved_game_days":5429,"live_settled_cycles":4758,
        "new_day_credit":0,"old_unknown10565_replayed":False,"Driver_history_rows":5275,"actual_A19_completed_cycles":4753,
        "actual_A19_loop_pending_cycle":None,"pending_cycle_scope":"retained_A17_unknown_AUTO10565_not_current_A19",
        "pending_cycle":{"global_turn":4759,"auto_sequence":10565,"stage":"auto_unsettled"},
        "next_sequence":{"next_sequence":10572},"Driver":copy.deepcopy(item),"SAVE":copy.deepcopy(item)}
    return closed,review

def callback(value:object)->Callable[...,object]:
    if not callable(value):raise ValueError("callable software boundary")
    return value

async def invoke_async(function:Callable[...,object],*arguments:object)->None:
    result=function(*arguments)
    if not isinstance(result,Coroutine):raise ValueError("real coroutine required")
    await result

class A20Contracts(unittest.TestCase):
    def test_plan_json_and_exact_frontier(self)->None:
        value=plan()
        bad:object
        self.assertEqual(value,m.parse_plan(json.loads(m.enc(value))))
        for bad in (True,10572.0,EqualInt.frontier,None,-1,2**53,10569):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                m.parse_plan({**value,"expected_next_sequence":bad})
        for key in m.PlanV1.__annotations__:
            wrong=dict(value);wrong.pop(key)
            with self.subTest(missing=key),self.assertRaises(ValueError):m.parse_plan(wrong)
        for key in ("predecessor_plan_ref","predecessor_producer_ref","preflight_source_ref"):
            for bad in (None,[],True,{"path":str(HERE),"bytes":1.0,"sha256":"a"*64}):
                with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):
                    m.parse_plan({**value,key:bad})
        with self.assertRaises(ValueError):m.parse_plan({**value,"schema":"xar.Source31-A19-complete-cold-input/v1"})

    def test_runtime_admission_uses_new_single_contract(self)->None:
        value:m.Doc={"schema":"xar.Source31-A20-runtime-prepare-admission/v1","machine_id":m.MACHINE,
            "owner":"Root","status":"ADMITTED","root_direct_execution_release":True,
            "canonical_capacity_review_passed":True,"plan":pin(),"quote":pin(),"full_storage_ref":pin(),
            "runtime_hard_bytes":3*1024**2,"capacity":{"D_free_floor_bytes":12345,"Z_free_floor_bytes":67890}}
        def parse(value:object)->m.RuntimeAdmissionV1:
            return m.parse_runtime_admission_v1(value,expected_machine_id=m.MACHINE)
        self.assertEqual(parse(value),parse(json.loads(m.enc(value))))
        for key in m.RuntimeAdmissionV1.__annotations__:
            absent=dict(value);absent.pop(key)
            with self.subTest(missing=key),self.assertRaises(ValueError):parse(absent)
        for size_bad in (True,3.0,None,-1,2**53):
            with self.subTest(size=size_bad),self.assertRaises(ValueError):parse({**value,"runtime_hard_bytes":size_bad})
        for bad in ({**value,"hard_bytes":3},{**value,"schema":"xar.Source31-A19-runtime-prepare-admission/v1"},
                    {**value,"capacity":{"D_conservative_floor_bytes":1,"Z_free_floor_bytes":2}},
                    {**value,"canonical_capacity_review_passed":1}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):parse(bad)

    def test_actual_closure_shape_and_no_replay(self)->None:
        closed,review=closed_pair()
        for c,r in ((closed,review),(json.loads(m.enc(closed)),json.loads(m.enc(review)))):
            m.validate_closed_records_v1(c,r,expected_next_sequence=10572)
        for key in ("screen120_released","Tasks_absent","old_request_replayed","next_sequence",
                    "FULL_requests","new_cycle_credit","new_day_credit","next_cold_rollback","sources"):
            bad=copy.deepcopy(closed);bad.pop(key)
            with self.subTest(missing=key),self.assertRaises(ValueError):
                m.validate_closed_records_v1(bad,review,expected_next_sequence=10572)
        for key in ("next_sequence","saved_cycles","pending_cycle","FULL_requests"):
            for bad_value in (True,float(m.uint(closed[key])),None):
                bad={**closed,key:bad_value}
                with self.subTest(key=key,value=bad_value),self.assertRaises(ValueError):
                    m.validate_closed_records_v1(bad,review,expected_next_sequence=10572)
        for birth in (True,1.0,123,str(2**64),"00123","0"):
            bad=copy.deepcopy(closed);m.record(bad["Game"])
            game=dict(m.record(bad["Game"]));game["creation_filetime"]=birth;bad["Game"]=game
            with self.subTest(birth=birth),self.assertRaises(ValueError):
                m.validate_closed_records_v1(bad,review,expected_next_sequence=10572)
        with self.assertRaises(ValueError):
            m.validate_closed_records_v1({**closed,"screen119_released":True,"screen120_released":False},review,
                                        expected_next_sequence=10572)
        with self.assertRaises(ValueError):
            m.validate_closed_records_v1(closed,{**review,"old_unknown10565_replayed":True},
                                        expected_next_sequence=10572)

    def test_fresh_verified_software_ignores_cached_code(self)->None:
        exact=m.fixed(HERE/"prepare_source31_a19_cold_union_v1.py",m.PREDECESSOR_PIN)
        poison=ModuleType("prepare_source31_a19_cold_union_v1");poison.__file__="foreign"
        with patch.dict(sys.modules,{"prepare_source31_a19_cold_union_v1":poison}):
            first=m.load_verified_predecessor_v1(exact);second=m.load_verified_predecessor_v1(exact)
        self.assertIsNot(first,second);self.assertIsNot(vars(first),vars(second))
        self.assertEqual(Path(m.text(first.__file__)).read_bytes(),m.read_ref(exact))
        actual=m.function_source_v1(m.read_ref(exact).decode(),"fresh_base_v1")
        self.assertEqual(ast.dump(ast.parse(actual)),ast.dump(ast.parse(m.text(
            ast.get_source_segment(m.read_ref(exact).decode(),next(n for n in ast.parse(m.read_ref(exact)).body
                if isinstance(n,ast.FunctionDef) and n.name=="fresh_base_v1"))))))
        with self.assertRaises(ValueError):m.load_verified_predecessor_v1({**exact,"sha256":"a"*64})

    def test_real_canonical_source_bytes(self)->None:
        path=HERE/m.PREFLIGHT_NAME;raw=path.read_bytes();actual=m.ref(path)
        m.validate_canonical_preflight_v1(raw,expected=actual)
        for bad in ({**actual,"bytes":float(len(raw))},{**actual,"sha256":"a"*64},
                    {**actual,"path":str(HERE/"foreign.py")}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                m.validate_canonical_preflight_v1(raw,expected=cast(m.ExactRef,bad))
        with self.assertRaises(ValueError):
            m.patch_preflight_source_v1({m.PREFLIGHT_NAME:b"foreign"},raw,expected=actual)

    def test_real_native32_producer_no_ambient_machine(self)->None:
        root=HERE/"candidates/native32_runtime_journal_adapter_20261021"
        spec=importlib.util.spec_from_file_location("_a20_real_n32_fixture",root/"test_native32_runtime_journal_adapter_v1.py")
        if spec is None or spec.loader is None:raise ValueError("real existing test source")
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
        sys.path.insert(0,str(root))
        try:spec.loader.exec_module(module)
        finally:sys.path.remove(str(root))
        source=(root/"test_native32_runtime_journal_adapter_v1.py").read_text(encoding="utf-8")
        body=m.function_source_v1(source,"queue_fixture_v1")
        body=m.one(body,'"N": HERE, "MACHINE": MACHINE,','"N": HERE,')
        env=dict(vars(module));env["m"]=m;env["MACHINE"]=m.MACHINE
        with patch.object(module,"MACHINE",m.MACHINE):
            exec(compile(body,"<actual Native32 loop without ambient MACHINE>","exec"),env)
            with self.assertRaises(KeyError):
                asyncio.run(invoke_async(callback(env["queue_fixture_v1"]),self))
            body=m.one(body,'    exec(compile(projected,',
                '    projected=m.fix_native32_queue_machine_v1(projected,machine_id=m.MACHINE)\n    exec(compile(projected,')
            exec(compile(body,"<actual Native32 loop with source-bound machine>","exec"),env)
            asyncio.run(invoke_async(callback(env["queue_fixture_v1"]),self))
        original=m.text(getattr(module,"ORIGINAL_CONTROL_V1"))
        api=getattr(module,"api")
        projected=callback(getattr(api,"patch_queue_control_v1"))(original.encode(),
            production_binding_basename="NATIVE32-PRODUCTION-BINDING.json")
        if not isinstance(projected,bytes):raise ValueError("actual patch bytes")
        for bad in ("wrong-machine","",True,None):
            with self.subTest(machine=bad),self.assertRaises(ValueError):
                m.fix_native32_queue_machine_v1(projected,machine_id=cast(str,bad))
        fixed=m.fix_native32_queue_machine_v1(projected,machine_id=m.MACHINE)
        with self.assertRaises(ValueError):m.fix_native32_queue_machine_v1(fixed,machine_id=m.MACHINE)

    def test_closed_file_identity_uses_shared_contract(self)->None:
        closed,review=closed_pair()
        for identity in ({},{"bytes":True,"file_id":"1","mtime_ns":"1"},
                         {"bytes":float(pin()["bytes"]),"file_id":"1","mtime_ns":"1"},
                         {"bytes":pin()["bytes"],"file_id":1,"mtime_ns":"1"},
                         {"bytes":pin()["bytes"],"file_id":"01","mtime_ns":"1"},
                         {"bytes":pin()["bytes"],"file_id":"0x10","mtime_ns":"1"},
                         {"bytes":pin()["bytes"]+1,"file_id":"1","mtime_ns":"1"}):
            wrong=copy.deepcopy(review)
            driver=dict(m.record(wrong["Driver"]));driver["identity"]=identity;wrong["Driver"]=driver
            with self.subTest(identity=identity),self.assertRaises(ValueError):
                m.validate_closed_records_v1(closed,wrong,expected_next_sequence=10572)

    def test_cross_module_source_map_is_validated(self)->None:
        value={"accepted.py":b"pass\n"}
        result=m.parse_source_map_v1(value)
        self.assertEqual(result,value);self.assertIsNot(result,value)
        invalid:object
        for invalid in (None,[],{},{"x.py":"pass"},{1:b"pass"},{"x.py":bytearray(b"pass")},{"x.py":True}):
            with self.subTest(value=invalid),self.assertRaises(ValueError):
                m.parse_source_map_v1(invalid)

    def test_real_owner_projection_retains_distinct_outputs(self)->None:
        import prepare_source31_a20_owner_metadata_v1 as owner
        projected=owner._load_v1()
        names_value:object=getattr(projected,"OUTPUT_NAMES",None)
        if not isinstance(names_value,tuple):raise ValueError("real output tuple")
        names=tuple(m.text(item) for item in names_value)
        self.assertEqual(len(names),4)
        self.assertEqual(names[0],"ROOT-C23-A20-COLD-OWNER-RECORDING-BINDING.json")
        self.assertNotIn("ROOT-C23-A20-ACTUAL-RECORDING-BINDING.json",names)
        function=callback(getattr(projected,"cold_owner",None))
        if not hasattr(function,"__code__"):raise ValueError("real generated function")
        code:object=getattr(function,"__code__")
        if not isinstance(code,CodeType):raise ValueError("code")
        self.assertNotIn(10569,code.co_consts)
        with self.assertRaises(ValueError):
            owner.parse_owner_inputs_v1({},at_utc=datetime.now(timezone.utc))


    def test_current_owner_frontier_preserves_historical_slots(self)->None:
        source=("HISTORICAL=10569\n# 中文 byte offsets\n"
                "def _base(): return 10569\n"
                "def saved_basis(): return 10569\n"
                "def compose(): return 10569,10569\n")
        result=m.metadata_frontier_v1(source,expected_next_sequence=10572)
        scope:m.Doc={}
        exec(compile(result,"<metadata frontier consumer>","exec"),scope)
        self.assertEqual(scope["HISTORICAL"],10569)
        self.assertEqual(callback(scope["_base"])(),10572)
        self.assertEqual(callback(scope["saved_basis"])(),10572)
        self.assertEqual(callback(scope["compose"])(),(10572,10572))
        self.assertEqual(result,m.metadata_frontier_v1(source,
            expected_next_sequence=json.loads("10572")))
        for bad in (True,10572.0,EqualInt.frontier,10570,None):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                m.metadata_frontier_v1(source,expected_next_sequence=cast(int,bad))
        for wrong in (result,source.replace("10569,10569","10569"),
                      source.replace("def _base():","def foreign():")):
            with self.assertRaises(ValueError):
                m.metadata_frontier_v1(wrong,expected_next_sequence=10572)
        p=plan();base=ModuleType("metadata_history_boundary")
        current=pin();historical=dict(current,path=str(HERE/"historical-next.json"))
        original:m.Doc={"current_next_ref":current,"preserved":10538}
        vars(base)["_a19_history_plan"]=original
        with patch.object(m,"historical_plan_v1",return_value={"current_next_ref":historical}):
            projected=m.metadata_history_plan_v1(p,base)
        self.assertEqual(projected["current_next_ref"],historical)
        self.assertEqual(original["current_next_ref"],current)
        self.assertEqual(projected["preserved"],10538)


    def test_registered_metadata_loader_runs_actual_dataclass(self)->None:
        from importlib.abc import Loader
        class MemoryLoader(Loader):
            def create_module(self,spec:object)->None:return None
            def exec_module(self,module:ModuleType)->None:
                exec("from __future__ import annotations\nfrom dataclasses import dataclass\n"
                     "@dataclass(frozen=True)\nclass Evidence:\n    value:int\n"
                     "result=Evidence(7)\n",vars(module))
        loader=ModuleType("verified_legacy_loader")
        loader.__file__=str(m.OWN/"prepare_c23_a05_union_v1.py")
        original=lambda path,name:None
        vars(loader)["_module"]=original
        old=ModuleType("old");vars(old)["prior"]=loader
        layer=ModuleType("layer");vars(layer)["old"]=old
        legacy=ModuleType("legacy");vars(legacy)["base"]=layer
        base=ModuleType("actual_scope")
        names=("_a10_actual_bootstrap_metadata","_a12_actual_business_bridge","_a13_actual_bootstrap")
        modules:list[ModuleType]=[]
        def scope(history:object,namespace:object,runtime:object)->None:
            for name in names:
                value=m.dynamic(loader,"_module")(m.TARGET/"root_checkpoint_bootstrap_c23.py",name)
                if not isinstance(value,ModuleType):raise ValueError("actual module")
                modules.append(value)
        vars(base)["metadata_scope"]=scope
        row=[str(m.TARGET/"root_checkpoint_bootstrap_c23.py"),"a"*64]
        policy={"machine_id":m.MACHINE,"entry_source_pins":[row]*47}
        policy["entry_source_pins"]=[row]+[[str(HERE/str(i)),"b"*64] for i in range(46)]
        expected=dict(pin(),path=row[0],sha256="a"*64)
        saved={name:sys.modules.get(name) for name in names}
        try:
            with (
                patch("importlib.util.spec_from_file_location",side_effect=lambda name,path:importlib.util.spec_from_loader(name,MemoryLoader())),
                patch("importlib.import_module",return_value=legacy),
                patch.object(m,"ref",return_value=expected),
                patch.object(m,"read_ref",return_value=b"verified source boundary"),
                patch.object(m,"checked",side_effect=[{"canonical_preload_policy":pin()},policy]),
            ):
                m.registered_metadata_scope_v1(base,{}, {},m.TARGET)
            self.assertEqual(len(modules),3)
            for module in modules:self.assertEqual(getattr(getattr(module,"result"),"value"),7)
            self.assertIs(getattr(loader,"_module"),original)
        finally:
            for name,value in saved.items():
                if value is None:sys.modules.pop(name,None)
                else:sys.modules[name]=value


    def test_metadata_forward_preserves_original_graph_model(self)->None:
        p=plan();after=m.ref(m.__file__);p["union_producer"]=after
        before=dict(after,bytes=m.METADATA_BEFORE_PIN[0],sha256=m.METADATA_BEFORE_PIN[1])
        old=dict(p,union_producer=before)
        archive=dict(before,path=str(m.PREP/"A20-UNION-PRE-METADATA-FIX01.py"))
        forward={"schema":"xar.Source31-A20-metadata-forward/v1",
            "original_plan_ref":pin(),"original_quote_ref":dict(pin(),path=str(HERE/"quote")),
            "before_archive_ref":archive,"after_producer_ref":after,
            "scope":"postguard_and_owner_metadata_only","graph_bytes_changed":False}
        original:m.Doc={"producer":before,"files":[{"path":"original","bytes":7}]}
        q=dict(original,producer=after,metadata_forward=forward,
            status="DEPLOYED_GRAPH_METADATA_FORWARD_NOT_RUNTIME_ADMITTED",
            observed_at_utc="2026-10-21T05:00:00+00:00")
        def checked(value:object,limit:int=262144)->m.Doc:
            return old if value==pin() else original
        with patch.object(m,"checked",side_effect=checked),patch.object(m,"read_ref",return_value=b"source boundary"):
            m.validate_metadata_forward_v1(p,q)
            m.validate_metadata_forward_v1(json.loads(m.enc(p)),json.loads(m.enc(q)))
            wrong=copy.deepcopy(q);wrong["files"]=[]
            with self.assertRaises(ValueError):m.validate_metadata_forward_v1(p,wrong)

if __name__=="__main__":
    unittest.main()
