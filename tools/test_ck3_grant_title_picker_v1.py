"""Offline grant request, holder proof, no-retry and registered MCP regression."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"ck3_autonomous_player/src"))
from xar_autoplayer.bridge import grant_title_picker_v1 as contract
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256, opening_binding
import ck3_native_profile_mcp as native

T=0x01001234
ACTOR=31254
RECIPIENT=65865

def snapshot():
    return {"revision":7,"native_revision":6,"paused":True,"map_ready":True,
        "date_raw":123456,"episode_run_id":"synthetic-episode",
        "played_character":{"character_id":ACTOR,"alive":True},
        "diagnostics":{"connection_generation":2,"hello":{"pid":999,
            "ck3_build_match":True,"game_adapter_id":"ck3-1.20.0.3-msvc-x64",
            "expected_ck3_version":"1.20.0.3","expected_ck3_sha256":EXE_SHA256}}}

def observation(*,visible=True,selected=True,holder=ACTOR):
    return {"available":True,"window_visible":visible,"window_binding_verified":visible,
        "rows_complete":visible,"native_can_send":True if visible else None,
        "warning_confirmation_required":False if visible else None,
        "rows":[{"title_full_id":T,"holder_character_full_id":holder,"selected":selected,"selectable":True}] if visible else [],
        "selected_title_full_ids":[T] if visible and selected else [],
        "requested_title_holders":[{"title_full_id":T,"available":True,"holder_character_full_id":holder}]}

def result(operation="send",*,transferred=False):
    r={k:v for k,v in opening_binding(snapshot()).items() if k!="episode_run_id"}
    r.update(schema=contract.SCHEMA,operation=operation,recipient_character_full_id=RECIPIENT,
        owner_thread_verified=True,frame_verified=True,source_abi_pins_verified=True,
        dispatch_invoked=operation!="query",native_call_completed=operation!="query",
        selection_verified=operation=="select",transfer_verified=transferred,
        before=observation(),after=observation(holder=RECIPIENT if transferred else ACTOR),
        status="holder_transfer_observed" if transferred else {"query":"observed","prepare":"prepared","select":"selection_observed","send":"pending"}[operation],
        unavailable_reason="",business_full_credit=False)
    return r

class Driver:
    def __init__(self,root,operation="send",transferred=False):
        self.current=snapshot();self.root=Path(root);self.calls=[]
        self.response=result(operation,transferred=transferred);self.error=None;self.after=None
        setattr(self,contract.PERMISSION,True)
    def _native_driver_state_path(self): return self.root/"native-state.json"
    def take_snapshot(self): return copy.deepcopy(self.current)
    def capabilities(self): return {"bridge_capabilities":["game.command."+op+"-grant-title-picker-v1" for op in contract.OPERATIONS]}
    def _execute_primitive_step(self,step,**kwargs):
        self.calls.append((step,kwargs))
        if self.error: raise self.error
        if self.after: self.after(self.current)
        return copy.deepcopy(self.response)

def execute(driver,operation="send",**kwargs):
    return contract.execute(driver,operation,RECIPIENT,expected_revision=driver.current["revision"],
        requested_title_full_ids=[T],expected_selected_title_full_ids=[T] if operation in {"send","select"} else [],**kwargs)

class ContractTests(unittest.TestCase):
    def test_preserves_full_generation_identity(self):
        self.assertEqual(contract.request_fields("send",RECIPIENT,[T],[T])["requested_title_full_ids"],str(T))
    def test_rejects_coerced_or_absent_full_ids(self):
        for value in (True,"12",12.0,-1,2**32-1,2**32):
            with self.subTest(value=value),self.assertRaises(ValueError): contract.full_id(value)
    def test_rejects_duplicate_and_unbounded_sets(self):
        for ids in ([T,T],list(range(65)),(T,)):
            with self.subTest(ids=ids),self.assertRaises(ValueError): contract.title_ids(ids)
    def test_send_requires_nonempty_complete_target_selection(self):
        for targets,selected in (([],[]),([T],[]),([],[T]),([T],[T+1])):
            with self.subTest(targets=targets,selected=selected),self.assertRaises(ValueError):
                contract.request_fields("send",RECIPIENT,targets,selected)
        with self.assertRaises(ValueError):contract.request_fields("query",0,[T],[])
    def test_query_and_prepare_cannot_assume_selection(self):
        for op in ("query","prepare"):
            with self.subTest(op=op),self.assertRaises(ValueError): contract.request_fields(op,RECIPIENT,[T],[T])
    def test_only_select_accepts_boolean_desired_state(self):
        for desired in (1,"true",None):
            with self.subTest(desired=desired),self.assertRaises(ValueError):
                contract.request_fields("select",RECIPIENT,[T],[],T,desired)
        with self.assertRaises(ValueError): contract.request_fields("query",RECIPIENT,[T],[],T,True)
    def normalize(self,r,op="send",selected=None,**kwargs):
        return contract.normalize_result(r,opening_binding(snapshot()),op,RECIPIENT,[T],
            ([T] if op in {"send","select"} else []) if selected is None else selected,**kwargs)
    def test_ack_only_remains_pending(self):
        self.assertEqual(self.normalize(result())["status"],"pending")
        self.assertFalse(self.normalize(result())["transfer_verified"])
    def test_transfer_needs_actual_full_holder_join(self):
        self.assertTrue(self.normalize(result(transferred=True))["transfer_verified"])
        for field,value in (("available",False),("holder_character_full_id",ACTOR)):
            r=result(transferred=True);r["after"]["requested_title_holders"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError): self.normalize(r)
    def test_transfer_rejects_false_before_qualification(self):
        for change in ("rows_complete","window_binding_verified","native_can_send","warning_confirmation_required"):
            r=result(transferred=True);r["before"][change]=True if change=="warning_confirmation_required" else False
            with self.subTest(change=change),self.assertRaises(ValueError): self.normalize(r)
    def test_transfer_rejects_wrong_before_holder(self):
        r=result(transferred=True);r["before"]["requested_title_holders"][0]["holder_character_full_id"]=RECIPIENT
        with self.assertRaises(ValueError): self.normalize(r)
    def test_transfer_rejects_missing_or_extra_holders(self):
        for holderrows in ([],observation()["requested_title_holders"]*2):
            r=result(transferred=True);r["after"]["requested_title_holders"]=holderrows
            with self.subTest(holderrows=holderrows),self.assertRaises(ValueError): self.normalize(r)
    def test_native_row_ids_and_selected_predicates_are_unique(self):
        for mode in ("duplicate","selected"):
            r=result();r["after"]["rows"]*=2 if mode=="duplicate" else 1
            if mode=="selected":r["after"]["selected_title_full_ids"]=[]
            with self.subTest(mode=mode),self.assertRaises(ValueError): self.normalize(r)
    def test_query_cannot_claim_dispatch_or_transfer(self):
        for field in ("dispatch_invoked","native_call_completed","transfer_verified","selection_verified"):
            r=result("query");r[field]=True
            with self.subTest(field=field),self.assertRaises(ValueError): self.normalize(r,"query")
    def test_hidden_query_has_no_window_or_predicate_credit(self):
        r=result("query");r["before"]=observation(visible=False);r["after"]=observation(visible=False)
        self.assertFalse(self.normalize(r,"query")["after"]["rows_complete"])
    def test_prepared_requires_actual_visible_complete_window(self):
        r=result("prepare");r["after"]=observation(visible=False)
        with self.assertRaises(ValueError): self.normalize(r,"prepare")
    def test_selection_requires_actual_complete_set(self):
        r=result("select");self.assertTrue(self.normalize(r,"select",title_id=T,desired_selected=True)["selection_verified"])
        r["after"]["rows"][0]["selected"]=False;r["after"]["selected_title_full_ids"]=[]
        with self.assertRaises(ValueError):self.normalize(r,"select",title_id=T,desired_selected=True)
    def test_frame_pins_booleans_and_product_credit_cannot_be_coerced(self):
        for field,value in (("frame_verified",1),("source_abi_pins_verified",False),("date_raw",True),("business_full_credit",True)):
            r=result(transferred=True);r[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.normalize(r)

class DriverTests(unittest.TestCase):
    def test_private_permission_required_before_read_or_submission(self):
        with tempfile.TemporaryDirectory() as root:
            d=Driver(root);setattr(d,contract.PERMISSION,False)
            with self.assertRaises(ValueError):execute(d)
            self.assertEqual(d.calls,[])
    def test_wrong_build_stale_revision_and_missing_capability_submit_nothing(self):
        for mode in ("build","revision","capability"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as root:
                d=Driver(root)
                if mode=="build":d.current["diagnostics"]["hello"]["expected_ck3_sha256"]="0"*64
                elif mode=="capability":d.capabilities=lambda:{"bridge_capabilities":[]}
                with self.assertRaises(ValueError):
                    if mode=="revision":contract.execute(d,"send",RECIPIENT,expected_revision=6,requested_title_full_ids=[T],expected_selected_title_full_ids=[T])
                    else:execute(d)
                self.assertEqual(d.calls,[])
    def test_query_is_readonly_and_makes_no_action_claim(self):
        with tempfile.TemporaryDirectory() as root:
            d=Driver(root,"query");r=execute(d,"query")
            self.assertEqual(len(d.calls),1);self.assertEqual(list(Path(root).iterdir()),[])
            self.assertFalse(r["uses_mouse"]);self.assertFalse(r["uses_keyboard"])
    def test_actual_transfer_resolves_exact_original_claim(self):
        with tempfile.TemporaryDirectory() as root:
            d=Driver(root,transferred=True);r=execute(d)
            self.assertTrue(r["transfer_verified"]);claim=Path(r["action_claim_path"])
            self.assertTrue(claim.with_suffix(".resolved.json").is_file())
            self.assertEqual(len(d.calls),1);self.assertIn("protocol_request_id",d.calls[0][1])
    def test_pending_send_is_latched_across_public_revisions(self):
        with tempfile.TemporaryDirectory() as root:
            d=Driver(root);r=execute(d);d.current["revision"]+=1
            with self.assertRaisesRegex(ValueError,"no retry"):execute(d)
            self.assertEqual(len(d.calls),1);self.assertFalse(Path(r["action_claim_path"]).with_suffix(".resolved.json").exists())
    def test_unknown_delivery_is_not_replayed(self):
        with tempfile.TemporaryDirectory() as root:
            d=Driver(root);d.error=TimeoutError("synthetic unknown")
            with self.assertRaises(TimeoutError):execute(d)
            d.error=None
            with self.assertRaisesRegex(ValueError,"no retry"):execute(d)
            self.assertEqual(len(d.calls),1)
    def test_changed_episode_after_dispatch_keeps_unknown_claim(self):
        with tempfile.TemporaryDirectory() as root:
            d=Driver(root,transferred=True);d.after=lambda state:state.update(date_raw=123457)
            with self.assertRaises(ValueError):execute(d)
            self.assertEqual(len(d.calls),1)
            self.assertEqual(len(list((Path(root)/"grant-title-picker-actions").glob("*.claim.json"))),1)
            self.assertEqual(list((Path(root)/"grant-title-picker-actions").glob("*.resolved.json")),[])
    def test_prepare_ui_receipt_is_separate_from_transfer(self):
        with tempfile.TemporaryDirectory() as root:
            d=Driver(root,"prepare");r=execute(d,"prepare")
            self.assertEqual(r["status"],"prepared");self.assertFalse(r["transfer_verified"])
            self.assertFalse(r["business_full_credit"])

class McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_old_inventories_and_explicit_four_tool_addition(self):
        from mcp import Client
        for kwargs,count in (({},21),({"confucian_readonly_tools":True},23),({"confucian_challenger_tools":True},24),
                             ({"grant_title_picker_tools":True},25),({"confucian_challenger_tools":True,"grant_title_picker_tools":True},28)):
            with self.subTest(kwargs=kwargs):
                async with Client(native.create_server(SimpleNamespace(),**kwargs)) as client:
                    tools=(await client.list_tools()).tools
                    self.assertEqual(len(tools),count)
                    for tool in tools:self.assertFalse(tool.input_schema["additionalProperties"])
    async def test_registered_inputs_reject_identity_coercion_and_unknown_fields(self):
        from mcp import Client
        calls=[]
        service=SimpleNamespace(grant_title_picker=lambda *args:(calls.append(args) or {"status":"fixture"}))
        async with Client(native.create_server(service,grant_title_picker_tools=True)) as client:
            name="ck3_send_profile_grant_title_picker_v1"
            for changed in ({"recipient_id":True},{"expected_selected_title_full_ids":[True]},
                            {"expected_selected_title_full_ids":[T,T]},{"expected_selected_title_full_ids":[]},
                            {"expected_revision":0},{"expected_revision":True},{"unexpected":True}):
                args={"recipient_id":RECIPIENT,"expected_selected_title_full_ids":[T],"expected_revision":7,**changed}
                with self.subTest(changed=changed):self.assertTrue((await client.call_tool(name,args)).is_error)
            self.assertEqual(calls,[])
            self.assertFalse((await client.call_tool(name,{"recipient_id":RECIPIENT,"expected_selected_title_full_ids":[T],"expected_revision":7})).is_error)
            self.assertEqual(calls,[("send",RECIPIENT,7,[T],[T])])
    def test_optin_cannot_be_truthy_nonboolean(self):
        for value in (1,"yes",None):
            with self.subTest(value=value),self.assertRaises(ValueError):native.create_server(SimpleNamespace(),grant_title_picker_tools=value)

if __name__=="__main__":unittest.main()
