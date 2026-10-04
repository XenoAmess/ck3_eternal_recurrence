from __future__ import annotations
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.ingame_ui_contract import normalize_ui_result, validate_ui_request
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError
from xar_autoplayer.bridge.mcp_server import create_server

def snapshot():
    return {"revision":4,"native_revision":3,"snapshot_id":"native:3","date_raw":53146848,"paused":True,"map_ready":True,
            "episode_run_id":"offline-fixture-not-live","diagnostics":{"connection_generation":2},
            "played_character":{"character_id":29829,"alive":True}}

def result(kind="combat",operation="query",subject=0):
    return {"schema":"ck3-ingame-ui-window-v1","accepted":True,"available":True,
            "status":"observed" if operation=="query" else "acknowledged_verification_pending",
            "window_kind":kind,"window_name":{"character":"character_window","army":"army_window","combat":"combat_window","knights":"knight_view"}[kind],
            "requested_subject_id":subject,"window_exists":True,"effective_visible":True,"enabled":True,
            "subject_id_available":True,"current_subject_id":29829 if kind=="knights" else 16777218,
            "native_army_id":0,"owner_character_id":29829 if kind=="knights" else 0,
            "dispatch_invoked":operation!="query","verification_pending":operation!="query",
            "date_raw":53146848,"paused":True,"played_character_id":29829,"native_revision":3,"pump_epoch":14,"thread_id":77,
            "application_owner_thread_verified":True,"gui_owner_binding_verified":True,
            "gui_context_address":1001,"gui_owner_address":1002,"rng_owner_thread_id":0,"rng_owner_is_ui_admission_gate":False,
            "unavailable_reason":"","knights_list_scope":"military_eligible_not_active_combat_roster",
            "combat_knights_read_available":False,"left_knight_count":-1,"right_knight_count":-1,
            "left_knight_breakdown":"","right_knight_breakdown":"","combat_roster_full_ids_available":False,
            "hover_state_available":False,"hovered_widget_name":"","hovered_ui_side":"","hovered_combat_id":0,"hover_readback_is_pixels":False,
            "combat_geometry":{"available":False,"combat_id":0,"widget_count":0,"coordinate_space":"native_gui_absolute",
                "scope":"visible_widget_union_and_verified_stock_background_margins","stock_margin_source_verified":False,
                "stock_margin_source_sha256":"","content_inside_viewport":False,"fit_required":False,"readback_is_pixels":False,
                "full_panel_pixels_proven":False,"viewport":{"x":0,"y":0,"width":0,"height":0},
                "window_rect":{"x":0,"y":0,"width":0,"height":0},"content_union":{"x":0,"y":0,"width":0,"height":0},
                "proposed_translation":{"x":0,"y":0},"unavailable_reason":"offline_geometry_unavailable"},
            "native_backend_id":"ck3-1.19.0.6-native-ingame-ui-v1","game_version":"1.19.0.6",
            "executable_sha256":"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
            "tree":{"scope_root_name":{"character":"character_window","army":"army_window","combat":"combat_window","knights":"knight_view"}[kind],
                    "root_available":True,"truncated":False,"widget_count":1,"widgets":[{
                        "runtime_name":{"character":"character_window","army":"army_window","combat":"combat_window","knights":"knight_view"}[kind],
                        "child_path":"","depth":0,"child_count":0,"vtable_rva":72462416,"effective_visible":True,"enabled":True}]}}

class DriverFixture(NativeHeadlessGameplayDriver):
    def __init__(self, raw, ending=None):
        self.raw=raw;self.ending=ending;self.calls=[];self.records=[];self.reads=0
    def take_snapshot(self):
        self.reads+=1
        return copy.deepcopy(self.ending if self.reads>1 and self.ending is not None else snapshot())
    def _execute_primitive_step(self, step, **kwargs):
        self.calls.append((step,kwargs));return copy.deepcopy(self.raw)
    def _record_command(self,step,**kwargs):
        self.records.append((step,kwargs))
    def capabilities(self):
        return {"backend_id":"native-headless","bridge_capabilities":["game.command.navigate-ingame-ui-v1","game.command.query-ingame-ui-window-v1"],
                "action_steps":[]}

class PrimitiveUiFixture(DriverFixture):
    """Runs the real primitive and UI validation with explicit offline pipe stubs."""
    def __init__(self,raw,state_dir,*,native_ok=True):
        super().__init__(raw);self.state_dir=state_dir;self.sent=[];self._request_sequence=0
        self.command_timeout_seconds=1
        self.endpoint=SimpleNamespace(send=self.sent.append)
        self.state=SimpleNamespace(wait_for_command_result=lambda request_id,timeout: {
            "type":"command_result","request_id":request_id,"ok":native_ok,
            "result":copy.deepcopy(raw),"error":"offline original native rejection"})
    def _execute_primitive_step(self,step,**kwargs):
        return NativeHeadlessGameplayDriver._execute_primitive_step(self,step,**kwargs)

class IngameUiTests(unittest.TestCase):
    def normalize(self,value,kind="combat",operation="query",subject=0):
        return normalize_ui_result(value,operation=operation,kind=kind,subject_id=subject,native_revision=3,date_raw=53146848,actor_id=29829)
    def test_query_is_independent_owner_read_with_target_census(self):
        driver=DriverFixture(result());got=driver.query_ingame_ui_window_v1("combat",expected_revision=4)
        self.assertEqual(got["current_subject_id"],16777218)
        self.assertEqual(driver.calls[0][1]["request_fields"],{"window_kind":"combat","subject_id":0})
        self.assertFalse(got["verification_pending"])
    def test_action_ack_remains_pending(self):
        driver=DriverFixture(result("character","open_character",33437))
        got=driver.open_character_window_v1(33437,expected_revision=4)
        self.assertTrue(got["verification_pending"])
        self.assertEqual(driver.calls[0][1]["request_fields"]["subject_id"],33437)
    def test_bad_request_never_reaches_native(self):
        for kind,op,subject,rev in [("any","query",0,4),("knights","open_knights",33437,4),("character","open_character",True,4),
                                    ("combat","open_combat",0,4),("combat","open_combat",2**32-1,4),("army","select_army",18,True)]:
            with self.subTest(kind=kind,op=op,subject=subject),self.assertRaises(ValueError):validate_ui_request(op,kind,subject,rev)
    def test_public_unit_zero_and_signed_upper_bound_round_trip(self):
        for subject in (0, 2**31-1):
            raw=result("army","select_army",subject)
            raw["current_subject_id"]=subject
            raw["native_army_id"]=83
            driver=DriverFixture(raw)
            with self.subTest(subject=subject):
                got=driver.select_army_ui_v1(subject,expected_revision=4)
                self.assertEqual(got["current_subject_id"],subject)
                self.assertEqual(got["native_army_id"],83)
                self.assertTrue(got["verification_pending"])
                self.assertEqual(driver.calls[0][1]["request_fields"]["subject_id"],subject)
    def test_public_unit_invalid_requests_never_dispatch(self):
        for subject in (True, False, -1, 2**31, 2**32-1, 0.0, "0", None):
            driver=DriverFixture(result("army","select_army",0))
            with self.subTest(subject=subject),self.assertRaises(ValueError):
                driver.select_army_ui_v1(subject,expected_revision=4)
            self.assertFalse(driver.calls)
    def test_army_ui_result_preserves_native_army_domain_and_bounds_public_unit(self):
        raw=result("army","select_army",0)
        raw["current_subject_id"]=0
        raw["native_army_id"]=2**32-2
        self.assertEqual(self.normalize(raw,kind="army",operation="select_army",subject=0)["native_army_id"],2**32-2)
        for subject in (True, -1, 2**31, 2**32-1, 0.0, "0", None):
            changed=copy.deepcopy(raw);changed["current_subject_id"]=subject
            with self.subTest(subject=subject),self.assertRaises(ValueError):
                self.normalize(changed,kind="army",operation="select_army",subject=0)
    def test_stale_revision_never_dispatches(self):
        driver=DriverFixture(result())
        with self.assertRaises(PreSubmissionRevisionMismatchError):driver.query_ingame_ui_window_v1("combat",expected_revision=3)
        self.assertFalse(driver.calls)
    def test_changed_session_actor_date_and_connection_rejected(self):
        for key,value in [("date_raw",53146872),("episode_run_id","another-run"),("diagnostics",{"connection_generation":3}),
                          ("played_character",{"character_id":33437}),("map_ready",False)]:
            end=snapshot();end[key]=value;driver=DriverFixture(result(),end)
            with self.subTest(key=key),self.assertRaises(BridgeUnavailableError):driver.query_ingame_ui_window_v1("combat",expected_revision=4)
    def test_native_mismatched_ids_native_revision_date_and_actor_rejected(self):
        for key,value in [("requested_subject_id",18),("native_revision",4),("date_raw",53146872),("played_character_id",33437),
                          ("window_kind","character"),("paused",1),("pump_epoch",0),("thread_id",0)]:
            raw=result();raw[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)
    def test_query_cannot_be_action_ack(self):
        for key,value in [("dispatch_invoked",True),("verification_pending",True),("status","completed")]:
            raw=result();raw[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)
    def test_original_application_gui_binding_required_rng_owner_is_diagnostic(self):
        for rng in (0,77,999):
            raw=result();raw["rng_owner_thread_id"]=rng
            self.assertEqual(self.normalize(raw)["rng_owner_thread_id"],rng)
        for key,value in [("application_owner_thread_verified",False),("gui_owner_binding_verified",False),
                          ("gui_context_address",0),("gui_owner_address",0),("gui_context_address",True),
                          ("rng_owner_is_ui_admission_gate",True),("rng_owner_thread_id",2**32)]:
            raw=result();raw[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)
    def test_failed_identity_keeps_unmodified_raw_in_command_history(self):
        raw=result();raw.update(date_raw=0,available=False,accepted=False,status="unavailable",
                               unavailable_reason="application_paused_owner_stamp_unverified")
        driver=DriverFixture(raw)
        with self.assertRaisesRegex(ValueError,"date_raw"):
            driver.query_ingame_ui_window_v1("combat",expected_revision=4)
        saved=driver.records[-1][1]
        self.assertFalse(saved["ok"])
        self.assertEqual(saved["result"]["raw_native_ui_result"],raw)
        self.assertEqual(saved["result"]["raw_native_ui_result"]["date_raw"],0)
    def test_raw_native_return_is_create_only_before_validation(self):
        import json,hashlib
        with tempfile.TemporaryDirectory() as temp:
            driver=object.__new__(NativeHeadlessGameplayDriver);driver.state_dir=Path(temp)
            request={"step":"navigate-ingame-ui-v1","subject_id":33437,"expected_revision":3}
            frame={"ok":True,"result":{"date_raw":0,"unavailable_reason":"original native refusal"}}
            with patch("xar_autoplayer.bridge.native_driver.uuid.uuid4",return_value=SimpleNamespace(hex="fixed-offline-test")):
                receipt=driver._preserve_ingame_ui_native_frame(request,frame,snapshot())
                data=Path(receipt["path"]).read_bytes();saved=json.loads(data)
                self.assertEqual(saved["original_parsed_command_result"],frame)
                self.assertEqual(saved["validation_state"],"unvalidated")
                self.assertFalse(saved["wire_bytes_preserved"])
                self.assertEqual(receipt["sha256"],hashlib.sha256(data).hexdigest())
                with self.assertRaises(FileExistsError):driver._preserve_ingame_ui_native_frame(request,frame,snapshot())
                self.assertEqual(Path(receipt["path"]).read_bytes(),data)
    def test_real_primitive_preserves_native_body_before_binding_failure(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            raw=result();raw.update(date_raw=0,available=False,accepted=False,status="unavailable",
                                   unavailable_reason="original paused owner refusal")
            driver=PrimitiveUiFixture(raw,Path(temp))
            with self.assertRaisesRegex(ValueError,"date_raw"):
                driver.query_ingame_ui_window_v1("combat",expected_revision=4)
            files=list(Path(temp).rglob("native-ui-*.json"));self.assertEqual(len(files),1)
            saved=json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(saved["original_parsed_command_result"]["result"],raw)
            self.assertEqual(saved["request"],driver.sent[0])
            self.assertEqual(saved["actual_pre_submission_snapshot"]["date_raw"],53146848)
            self.assertEqual(saved["original_parsed_command_result"]["result"]["date_raw"],0)
    def test_real_primitive_native_command_red_also_preserved(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            driver=PrimitiveUiFixture(result(),Path(temp),native_ok=False)
            with self.assertRaisesRegex(Exception,"offline original native rejection"):
                driver.query_ingame_ui_window_v1("combat",expected_revision=4)
            saved=json.loads(next(Path(temp).rglob("native-ui-*.json")).read_text(encoding="utf-8"))
            self.assertIs(saved["original_parsed_command_result"]["ok"],False)
            self.assertEqual(len(driver.sent),1)
    def test_missing_or_invalid_evidence_directory_never_dispatches(self):
        driver=PrimitiveUiFixture(result(),None)
        with self.assertRaisesRegex(Exception,"state_dir"):
            driver.query_ingame_ui_window_v1("combat",expected_revision=4)
        self.assertFalse(driver.sent)
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/"not-a-directory";file.write_text("preserve me",encoding="utf-8")
            driver=PrimitiveUiFixture(result(),file)
            with self.assertRaises(OSError):driver.query_ingame_ui_window_v1("combat",expected_revision=4)
            self.assertFalse(driver.sent);self.assertEqual(file.read_text(encoding="utf-8"),"preserve me")
    def test_knights_explicit_owner_and_scope(self):
        self.normalize(result("knights"),kind="knights")
        for key,value in [("owner_character_id",33437),("current_subject_id",33437),("subject_id_available",False),
                          ("knights_list_scope","active_combat_roster")]:
            raw=result("knights");raw[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw,kind="knights")
    def test_truncated_window_census_retained_without_full_claim(self):
        raw=result();raw["tree"]["truncated"]=True
        self.assertTrue(self.normalize(raw)["tree"]["truncated"])
        raw["tree"]["scope_root_name"]="_root_"
        with self.assertRaises(ValueError):self.normalize(raw)
    def test_census_bound_and_availability_reason(self):
        raw=result();raw["tree"]["widget_count"]=513
        with self.assertRaises(ValueError):self.normalize(raw)

    def test_fit_action_uses_current_combat_only_and_still_pending(self):
        raw=result("combat","fit_combat_window",16777218);driver=DriverFixture(raw)
        got=driver.fit_combat_window_v1(16777218,expected_revision=4)
        self.assertTrue(got["verification_pending"])
        self.assertEqual(driver.calls[0][1]["request_fields"],{"window_kind":"combat","subject_id":16777218,"operation":"fit_combat_window"})
        self.assertFalse(got["combat_geometry"]["full_panel_pixels_proven"])

    def test_geometry_fit_bound_source_and_false_pixels_contract(self):
        raw=result();g=raw["combat_geometry"]
        g.update(available=True,combat_id=16777218,widget_count=1,stock_margin_source_verified=True,
            stock_margin_source_sha256="7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236",
            viewport={"x":0,"y":0,"width":2560,"height":1440},window_rect={"x":843,"y":1137,"width":875,"height":330},
            content_union={"x":820,"y":1120,"width":921,"height":364},proposed_translation={"x":0,"y":-44},
            content_inside_viewport=False,fit_required=True,unavailable_reason="")
        self.normalize(raw)
        for key,value in [("combat_id",2),("full_panel_pixels_proven",True),("readback_is_pixels",True),
                ("stock_margin_source_verified",False),("stock_margin_source_sha256","0"*64),
                ("content_inside_viewport",True),("fit_required",False),("widget_count",2)]:
            changed=copy.deepcopy(raw);changed["combat_geometry"][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(changed)
        for field,key,value in [("viewport","height",float("nan")),("viewport","x",True),
                ("content_union","width",3000),("content_union","height",2000),
                ("window_rect","y",900),("proposed_translation","y",-27)]:
            changed=copy.deepcopy(raw);changed["combat_geometry"][field][key]=value
            with self.subTest(field=field,key=key),self.assertRaises(ValueError):self.normalize(changed)
        changed=copy.deepcopy(raw);changed["tree"]["truncated"]=True
        with self.assertRaises(ValueError):self.normalize(changed)
        changed=copy.deepcopy(raw);changed["effective_visible"]=False;changed["tree"]["widgets"][0]["effective_visible"]=False
        with self.assertRaises(ValueError):self.normalize(changed)

    def test_fit_already_inside_is_no_dispatch_pending_not_full_pixels(self):
        raw=result("combat","fit_combat_window",16777218)
        raw.update(status="already_layout_fitted_verification_pending",dispatch_invoked=False)
        raw["combat_geometry"].update(available=True,combat_id=16777218,widget_count=1,stock_margin_source_verified=True,
            stock_margin_source_sha256="7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236",
            viewport={"x":0,"y":0,"width":2560,"height":1440},window_rect={"x":843,"y":1093,"width":875,"height":330},
            content_union={"x":820,"y":1076,"width":921,"height":364},proposed_translation={"x":0,"y":0},
            content_inside_viewport=True,fit_required=False,unavailable_reason="")
        self.normalize(raw,operation="fit_combat_window",subject=16777218)
        raw["dispatch_invoked"]=True
        with self.assertRaises(ValueError):self.normalize(raw,operation="fit_combat_window",subject=16777218)

    def test_unavailable_geometry_cannot_retain_coordinates_or_fit_claim(self):
        for field,key,value in [(None,"content_inside_viewport",True),(None,"fit_required",True),(None,"unavailable_reason",""),
                ("window_rect","width",875),("proposed_translation","y",-27)]:
            raw=result()
            if field:raw["combat_geometry"][field][key]=value
            else:raw["combat_geometry"][key]=value
            with self.subTest(field=field,key=key),self.assertRaises(ValueError):self.normalize(raw)

    def test_hover_ack_uses_fixed_side_and_remains_pending(self):
        driver=DriverFixture(result("combat","hover_right_knights",16777218))
        got=driver.hover_combat_knights_v1(16777218,"right",expected_revision=4)
        self.assertTrue(got["verification_pending"])
        self.assertEqual(driver.calls[0][1]["request_fields"]["operation"],"hover_right_knights")
        with self.assertRaises(ValueError):driver.hover_combat_knights_v1(16777218,"side1",expected_revision=4)

    def test_native_hover_is_bound_to_current_visible_full_combat(self):
        raw=result();raw.update(hover_state_available=True,hovered_widget_name="left_knights",hovered_ui_side="left",hovered_combat_id=16777218)
        self.normalize(raw)
        for key,value in [("hovered_combat_id",2),("hovered_widget_name","right_knights"),("effective_visible",False),
                          ("subject_id_available",False),("hover_readback_is_pixels",True),("hover_state_available",False)]:
            changed=copy.deepcopy(raw);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(changed)

    def test_original_count_breakdown_read_is_scoped_and_not_full_roster(self):
        raw=result();raw.update(combat_knights_read_available=True,left_knight_count=14,right_knight_count=13,
                                left_knight_breakdown="#T 原版文本\n人物 #!",right_knight_breakdown="原版文本")
        self.normalize(raw)
        for key,value in [("combat_roster_full_ids_available",True),("effective_visible",False),("subject_id_available",False),
                          ("left_knight_count",True),("left_knight_count",-1),("native_backend_id","fake"),("executable_sha256","0"*64)]:
            changed=copy.deepcopy(raw);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(changed)
        raw=result();raw.update(accepted=False,available=False,status="unavailable",unavailable_reason="native_read_unavailable")
        self.assertFalse(self.normalize(raw)["available"])
        raw["unavailable_reason"]=""
        with self.assertRaises(ValueError):self.normalize(raw)

class IngameUiMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_mcp_registration_query_and_strict_handle_negative_cases(self):
        from mcp import Client
        driver=DriverFixture(result());server=create_server(driver)
        async with Client(server) as client:
            names={t.name:t for t in (await client.list_tools()).tools}
            for tool in ["ck3_open_character_window_v1","ck3_select_army_ui_v1","ck3_open_combat_window_v1","ck3_open_knights_window_v1","ck3_query_ingame_ui_window_v1","ck3_hover_combat_knights_v1","ck3_fit_combat_window_v1"]:
                self.assertIn(tool,names)
            self.assertEqual(set(names["ck3_query_ingame_ui_window_v1"].input_schema["required"]),{"window_kind","expected_revision"})
            query=await client.call_tool("ck3_query_ingame_ui_window_v1",{"window_kind":"combat","expected_revision":4})
            self.assertFalse(query.is_error)
            self.assertEqual(query.structured_content["current_subject_id"],16777218)
            driver.raw=result("combat","hover_right_knights",16777218)
            hover=await client.call_tool("ck3_hover_combat_knights_v1",{"combat_id":16777218,"ui_side":"right","expected_revision":4})
            self.assertFalse(hover.is_error)
            self.assertTrue(hover.structured_content["verification_pending"])
            driver.raw=result("combat","fit_combat_window",16777218)
            fit=await client.call_tool("ck3_fit_combat_window_v1",{"combat_id":16777218,"expected_revision":4})
            self.assertFalse(fit.is_error)
            self.assertTrue(fit.structured_content["verification_pending"])
            count=len(driver.calls)
            for combat_id in [True,0,2**32-1,"16777218"]:
                failed=await client.call_tool("ck3_fit_combat_window_v1",{"combat_id":combat_id,"expected_revision":4})
                self.assertTrue(failed.is_error)
            for character_id in [True,0,2**32-1,"33437"]:
                failed=await client.call_tool("ck3_open_character_window_v1",{"character_id":character_id,"expected_revision":4})
                self.assertTrue(failed.is_error)
            for arguments in [{"window_kind":"unknown","expected_revision":4},{"window_kind":"combat","expected_revision":True}]:
                failed=await client.call_tool("ck3_query_ingame_ui_window_v1",arguments)
                self.assertTrue(failed.is_error)
            self.assertEqual(len(driver.calls),count)
            failed=await client.call_tool("ck3_hover_combat_knights_v1",{"combat_id":16777218,"ui_side":"side1","expected_revision":4})
            self.assertTrue(failed.is_error)
            self.assertEqual(len(driver.calls),count)
            generic=await client.call_tool("ck3_execute_step",{"step":"navigate-ingame-ui-v1","expected_revision":4})
            self.assertTrue(generic.is_error)
            self.assertEqual(len(driver.calls),count)

def current_snapshot():
    from xar_autoplayer.bridge.version_identity import CK3_12003
    value=snapshot()
    value["diagnostics"]["hello"]={"expected_ck3_version":CK3_12003.game_version,
        "expected_ck3_sha256":CK3_12003.executable_sha256}
    return value


def current_result(operation="query",subject=0,*,unopened=False):
    from xar_autoplayer.bridge.version_identity import CK3_12003
    value=result("army",operation,subject)
    value.update(native_backend_id=CK3_12003.backend_id("ingame-ui-v1"),
        game_version=CK3_12003.game_version,executable_sha256=CK3_12003.executable_sha256,
        current_subject_id=subject,native_army_id=83,
        owner_character_id_available=True,owner_character_id=29829)
    if unopened:
        value.update(window_exists=False,effective_visible=False,enabled=False,
            subject_id_available=False,current_subject_id=None,native_army_id=None,
            owner_character_id_available=False,owner_character_id=None)
        value["tree"].update(root_available=False,widget_count=0,widgets=[])
    return value


class CurrentUiDriverFixture(DriverFixture):
    def take_snapshot(self):
        self.reads+=1
        return copy.deepcopy(self.ending if self.reads>1 and self.ending is not None else current_snapshot())


class CurrentPrimitiveUiFixture(PrimitiveUiFixture):
    def take_snapshot(self):
        self.reads+=1
        return copy.deepcopy(self.ending if self.reads>1 and self.ending is not None else current_snapshot())


class CrozierArmyUiTests(unittest.TestCase):
    def normalize(self,value,operation="query",subject=0):
        from xar_autoplayer.bridge.version_identity import CK3_12003
        return normalize_ui_result(value,operation=operation,kind="army",subject_id=subject,
            native_revision=3,date_raw=53146848,actor_id=29829,expected_build=CK3_12003)

    def test_current_army_query_preserves_public_zero_as_observed_id(self):
        driver=CurrentUiDriverFixture(current_result())
        got=driver.query_ingame_ui_window_v1("army",expected_revision=4)
        self.assertEqual(got["current_subject_id"],0)
        self.assertEqual(got["native_army_id"],83)
        self.assertTrue(got["subject_id_available"])
        self.assertFalse(got["verification_pending"])
        self.assertFalse(got["dispatch_invoked"])

    def test_current_army_select_handles_zero_and_signed_upper_bound(self):
        for subject in (0,2**31-1):
            driver=CurrentUiDriverFixture(current_result("select_army",subject))
            with self.subTest(subject=subject):
                got=driver.select_army_ui_v1(subject,expected_revision=4)
                self.assertEqual(got["requested_subject_id"],subject)
                self.assertTrue(got["verification_pending"])
                self.assertEqual(driver.calls[0][1]["request_fields"]["subject_id"],subject)

    def test_unopened_current_army_select_is_pending_without_subject_or_census(self):
        driver=CurrentUiDriverFixture(current_result("select_army",0,unopened=True))
        got=driver.select_army_ui_v1(0,expected_revision=4)
        self.assertTrue(got["accepted"])
        self.assertTrue(got["dispatch_invoked"])
        self.assertTrue(got["verification_pending"])
        self.assertFalse(got["window_exists"])
        self.assertFalse(got["subject_id_available"])
        self.assertIsNone(got["current_subject_id"])
        self.assertIsNone(got["native_army_id"])
        self.assertFalse(got["tree"]["root_available"])
        self.assertEqual(got["tree"]["widget_count"],0)

    def test_unopened_select_cannot_claim_completed_or_readable_window(self):
        mutations=[("dispatch_invoked",False),("verification_pending",False),("status","completed"),
            ("status","already_visible_verification_pending"),("effective_visible",True),
            ("subject_id_available",True),("application_owner_thread_verified",False),("gui_owner_binding_verified",False)]
        for key,value in mutations:
            raw=current_result("select_army",0,unopened=True);raw[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.normalize(raw,"select_army",0)
        for key,value in [("root_available",True),("truncated",True),("scope_root_name","_root_")]:
            raw=current_result("select_army",0,unopened=True);raw["tree"][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw,"select_army",0)

    def test_query_cannot_reuse_unopened_action_ack(self):
        raw=current_result("select_army",0,unopened=True)
        with self.assertRaises(ValueError):self.normalize(raw)
        raw.update(accepted=False,available=False,dispatch_invoked=False,verification_pending=False,
            status="unavailable",unavailable_reason="window_not_yet_created")
        self.assertFalse(self.normalize(raw)["available"])

    def test_subject_null_requires_false_flag_and_keys_cannot_be_missing(self):
        raw=current_result();raw.update(subject_id_available=False,current_subject_id=None,native_army_id=None,
            owner_character_id_available=False,owner_character_id=None)
        self.assertIsNone(self.normalize(raw)["current_subject_id"])
        raw.update(current_subject_id=0,native_army_id=0)
        self.assertFalse(self.normalize(raw)["subject_id_available"])
        for key in ("current_subject_id","native_army_id"):
            changed=copy.deepcopy(raw);del changed[key]
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(changed)
        for field,value in [("current_subject_id",None),("native_army_id",None),
            ("current_subject_id",True),("current_subject_id",2**31),("current_subject_id",-1)]:
            changed=current_result();changed[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):self.normalize(changed)

    def test_current_selected_owner_zero_and_signed_int32_bound_are_actual_ids(self):
        for owner in (0,29829,2**31-1):
            raw=current_result();raw["owner_character_id"]=owner
            with self.subTest(owner=owner):
                got=self.normalize(raw)
                self.assertTrue(got["owner_character_id_available"])
                self.assertEqual(got["owner_character_id"],owner)

    def test_current_query_preserves_foreign_selected_owner(self):
        raw=current_result();raw["owner_character_id"]=33437
        driver=CurrentUiDriverFixture(raw)
        got=driver.query_ingame_ui_window_v1("army",expected_revision=4)
        self.assertEqual(got["played_character_id"],29829)
        self.assertEqual(got["owner_character_id"],33437)
        self.assertTrue(got["owner_character_id_available"])

    def test_select_ack_retains_prior_selection_and_foreign_actual_owner(self):
        raw=current_result("select_army",16777218)
        raw.update(current_subject_id=0,owner_character_id=33437)
        driver=CurrentUiDriverFixture(raw)
        got=driver.select_army_ui_v1(16777218,expected_revision=4)
        self.assertEqual(got["requested_subject_id"],16777218)
        self.assertEqual(got["current_subject_id"],0)
        self.assertEqual(got["owner_character_id"],33437)
        self.assertTrue(got["verification_pending"])

    def test_current_unavailable_owner_requires_explicit_null(self):
        raw=current_result();raw.update(owner_character_id_available=False,owner_character_id=None)
        self.assertIsNone(self.normalize(raw)["owner_character_id"])
        for owner in (0,29829,False,"",-1):
            changed=copy.deepcopy(raw);changed["owner_character_id"]=owner
            with self.subTest(owner=owner),self.assertRaises(ValueError):self.normalize(changed)

    def test_current_owner_flag_and_value_cannot_be_missing_or_malformed(self):
        for key in ("owner_character_id_available","owner_character_id"):
            raw=current_result();del raw[key]
            with self.subTest(missing=key),self.assertRaises(ValueError):self.normalize(raw)
        for flag in (None,0,1,"true",[],{}):
            raw=current_result();raw["owner_character_id_available"]=flag
            with self.subTest(flag=flag),self.assertRaises(ValueError):self.normalize(raw)
        for owner in (None,True,False,-1,2**31,2**32-1,"0",0.0):
            raw=current_result();raw["owner_character_id"]=owner
            with self.subTest(owner=owner),self.assertRaises(ValueError):self.normalize(raw)

    def test_owner_availability_cannot_claim_a_missing_selected_subject(self):
        raw=current_result();raw.update(subject_id_available=False,current_subject_id=None,native_army_id=None)
        with self.assertRaises(ValueError):self.normalize(raw)
        raw.update(owner_character_id_available=False,owner_character_id=None)
        self.assertFalse(self.normalize(raw)["owner_character_id_available"])

    def test_unopened_current_select_keeps_owner_unavailable_null(self):
        raw=current_result("select_army",0,unopened=True)
        got=self.normalize(raw,"select_army",0)
        self.assertFalse(got["owner_character_id_available"])
        self.assertIsNone(got["owner_character_id"])
        for owner in (0,29829):
            changed=copy.deepcopy(raw);changed["owner_character_id"]=owner
            with self.subTest(owner=owner),self.assertRaises(ValueError):self.normalize(changed,"select_army",0)

    def test_legacy_owner_numeric_contract_does_not_require_new_flag(self):
        raw=result("army")
        self.assertNotIn("owner_character_id_available",raw)
        got=normalize_ui_result(raw,operation="query",kind="army",subject_id=0,
            native_revision=3,date_raw=53146848,actor_id=29829)
        self.assertEqual(got["owner_character_id"],0)

    def test_current_mixed_owner_payload_preserves_original_failure_record(self):
        raw=current_result();raw.update(owner_character_id_available=False,owner_character_id=0)
        driver=CurrentUiDriverFixture(raw)
        with self.assertRaisesRegex(ValueError,"explicit null"):
            driver.query_ingame_ui_window_v1("army",expected_revision=4)
        self.assertEqual(len(driver.calls),1)
        self.assertFalse(driver.records[-1][1]["ok"])
        self.assertEqual(driver.records[-1][1]["result"]["raw_native_ui_result"],raw)


    def test_null_or_missing_request_never_dispatches(self):
        for subject in (None,True,False,-1,2**31,"0",0.0):
            driver=CurrentUiDriverFixture(current_result("select_army",0))
            with self.subTest(subject=subject),self.assertRaises(ValueError):driver.select_army_ui_v1(subject,expected_revision=4)
            self.assertFalse(driver.calls)

    def test_current_tree_uses_native_2048_bound_legacy_stays_512(self):
        for count in (512,513,2048,2049):
            raw=current_result();root=raw["tree"]["widgets"][0]
            raw["tree"].update(widget_count=count,widgets=[copy.deepcopy(root) for _ in range(count)])
            with self.subTest(current=count):
                if count<=2048:self.assertEqual(self.normalize(raw)["tree"]["widget_count"],count)
                else:
                    with self.assertRaises(ValueError):self.normalize(raw)
        for count in (512,513):
            raw=result("army");root=raw["tree"]["widgets"][0]
            raw["tree"].update(widget_count=count,widgets=[copy.deepcopy(root) for _ in range(count)])
            with self.subTest(legacy=count):
                if count==512:normalize_ui_result(raw,operation="query",kind="army",subject_id=0,native_revision=3,date_raw=53146848,actor_id=29829)
                else:
                    with self.assertRaises(ValueError):normalize_ui_result(raw,operation="query",kind="army",subject_id=0,native_revision=3,date_raw=53146848,actor_id=29829)

    def test_exact_current_tuple_cannot_accept_mixed_or_legacy_identity(self):
        from xar_autoplayer.bridge.version_identity import CK3_11906,CK3_12003
        for key,value in [("native_backend_id",CK3_11906.backend_id("ingame-ui-v1")),
            ("game_version",CK3_11906.game_version),("executable_sha256",CK3_11906.executable_sha256),
            ("executable_sha256","0"*64)]:
            raw=current_result();raw[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)
        raw=current_result();raw.update(native_backend_id=CK3_11906.backend_id("ingame-ui-v1"),
            game_version=CK3_11906.game_version,executable_sha256=CK3_11906.executable_sha256)
        with self.assertRaises(ValueError):self.normalize(raw)
        with self.assertRaises(ValueError):normalize_ui_result(current_result(),operation="query",kind="army",subject_id=0,native_revision=3,date_raw=53146848,actor_id=29829)
        raw=current_result();raw["executable_sha256"]=CK3_12003.executable_sha256.lower()
        self.assertTrue(self.normalize(raw)["available"])

    def test_current_nonarmy_routes_rejected_before_dispatch(self):
        requests=[("query","character",0),("query","combat",0),("query","knights",0),
            ("open_character","character",33437),("open_combat","combat",18),("open_knights","knights",0),
            ("fit_combat_window","combat",18),("hover_left_knights","combat",18)]
        for operation,kind,subject in requests:
            driver=CurrentUiDriverFixture(current_result())
            with self.subTest(operation=operation,kind=kind),self.assertRaises(ValueError):
                driver._ingame_ui_v1(operation,kind,subject,expected_revision=4)
            self.assertFalse(driver.calls)

    def test_prehello_mixed_unknown_or_unmigrated_build_never_dispatches(self):
        from xar_autoplayer.bridge.version_identity import CK3_12002,CK3_12003
        hellos=[None,{"expected_ck3_version":"1.20.0.3","expected_ck3_sha256":"0"*64},
            {"expected_ck3_version":"1.20.0.2","expected_ck3_sha256":CK3_12003.executable_sha256},
            {"expected_ck3_version":CK3_12002.game_version,"expected_ck3_sha256":CK3_12002.executable_sha256},
            {"expected_ck3_version":CK3_12003.game_version,"expected_ck3_sha256":CK3_12003.executable_sha256,"game_version":"1.19.0.6"},
            {"expected_ck3_version":CK3_12003.game_version,"expected_ck3_sha256":CK3_12003.executable_sha256,"executable_sha256":"0"*64}]
        for hello in hellos:
            before=current_snapshot();before["diagnostics"]["hello"]=hello
            driver=CurrentUiDriverFixture(current_result())
            with patch.object(driver,"take_snapshot",return_value=before),self.subTest(hello=hello),self.assertRaises(ValueError):
                driver.query_ingame_ui_window_v1("army",expected_revision=4)
            self.assertFalse(driver.calls)

    def test_missing_hello_can_only_accept_legacy_result(self):
        driver=DriverFixture(current_result())
        with self.assertRaises(ValueError):driver.query_ingame_ui_window_v1("army",expected_revision=4)
        self.assertEqual(driver.records[-1][1]["result"]["raw_native_ui_result"],current_result())
        self.assertTrue(DriverFixture(result("army")).query_ingame_ui_window_v1("army",expected_revision=4)["available"])

    def test_posthello_drop_or_build_change_keeps_raw_failure(self):
        from xar_autoplayer.bridge.version_identity import CK3_11906
        endings=[]
        dropped=current_snapshot();del dropped["diagnostics"]["hello"];endings.append(dropped)
        legacy=current_snapshot();legacy["diagnostics"]["hello"]={"expected_ck3_version":CK3_11906.game_version,
            "expected_ck3_sha256":CK3_11906.executable_sha256};endings.append(legacy)
        mixed=current_snapshot();mixed["diagnostics"]["hello"]["expected_ck3_sha256"]="0"*64;endings.append(mixed)
        for ending in endings:
            raw=current_result("select_army",0,unopened=True);driver=CurrentUiDriverFixture(raw,ending)
            with self.subTest(ending=ending),self.assertRaises((ValueError,BridgeUnavailableError)):
                driver.select_army_ui_v1(0,expected_revision=4)
            self.assertEqual(len(driver.calls),1)
            self.assertFalse(driver.records[-1][1]["ok"])
            self.assertEqual(driver.records[-1][1]["result"]["raw_native_ui_result"],raw)

    def test_explicit_legacy_hello_cannot_disappear_between_reads(self):
        from xar_autoplayer.bridge.version_identity import CK3_11906
        before=snapshot();before["diagnostics"]["hello"]={"expected_ck3_version":CK3_11906.game_version,
            "expected_ck3_sha256":CK3_11906.executable_sha256}
        driver=DriverFixture(result("army"))
        with patch.object(driver,"take_snapshot",side_effect=[before,snapshot()]),self.assertRaises(BridgeUnavailableError):
            driver.query_ingame_ui_window_v1("army",expected_revision=4)
        self.assertEqual(len(driver.calls),1)

    def test_current_real_primitive_retains_original_failed_result_once(self):
        import json
        for native_ok in (False,True):
            with tempfile.TemporaryDirectory() as temp:
                raw=current_result();raw["executable_sha256"]="0"*64
                driver=CurrentPrimitiveUiFixture(raw,Path(temp),native_ok=native_ok)
                with self.subTest(native_ok=native_ok),self.assertRaises(Exception):
                    driver.query_ingame_ui_window_v1("army",expected_revision=4)
                files=list(Path(temp).rglob("native-ui-*.json"));self.assertEqual(len(files),1)
                saved=json.loads(files[0].read_text(encoding="utf-8"))
                self.assertEqual(saved["original_parsed_command_result"]["result"],raw)
                self.assertIs(saved["original_parsed_command_result"]["ok"],native_ok)
                self.assertEqual(len(driver.sent),1)


HOVER_RECEIPT = "a" * 32
LEAVE_RECEIPT = "b" * 32


def army_tooltip_result(operation="query", subject=0, tooltip_kind="supply_state", *,
                        phase="cache", receipt=HOVER_RECEIPT, text="#T 补给状态#!\n-2.5%\n"):
    import hashlib
    value = current_result(operation, subject)
    value["verification_pending"] = True
    tooltip = {"schema":"ck3-army-tooltip-v1", "semantic_kind":tooltip_kind,
        "receipt_id":receipt, "action_owner_epoch":14, "later_owner_epoch":15 if operation == "query" else None,
        "cache_bytes_observed":False, "source_bound":True, "hover_matches_source":False,
        "active_stack_read":False, "active_count":None, "active_top_index":None,
        "active_top_locked":None, "active_root_available":False, "source_child_path":"0/2",
        "tooltip_text_child_path":None, "leave_observed":False,
        "status":"acknowledged_verification_pending", "unavailable_reason":"",
        "verification_pending":True, "gui_update_epoch":None, "text_refresh_verified":False,
        "rendered_verified":False, "available":False, "observed_cache":None}
    if phase == "cache":
        tooltip.update(cache_bytes_observed=True, hover_matches_source=True, active_stack_read=True,
            active_count=1, active_top_index=0, active_top_locked=False, active_root_available=True,
            tooltip_text_child_path="0/1", status="cache_observed_verification_pending",
            observed_cache={"text":text, "utf8_bytes":len(text.encode("utf-8")),
                "sha256":hashlib.sha256(text.encode("utf-8")).hexdigest()})
    elif phase == "leave":
        tooltip.update(active_stack_read=True, active_count=0, leave_observed=True,
            status="leave_observed_verification_pending")
    elif phase == "unavailable":
        value.update(accepted=False, available=False, status="unavailable", dispatch_invoked=False,
            verification_pending=False, unavailable_reason="offline_source_binding_changed")
        for key in ("receipt_id", "action_owner_epoch", "later_owner_epoch", "source_child_path"):
            tooltip[key] = None
        tooltip.update(source_bound=False, verification_pending=False, status="unavailable",
            unavailable_reason="offline_source_binding_changed")
    value["army_tooltip"] = tooltip
    return value


class ArmyTooltipTests(unittest.TestCase):
    def normalize(self, value, operation="query", subject=0, tooltip_kind="supply_state", receipt=HOVER_RECEIPT):
        from xar_autoplayer.bridge.version_identity import CK3_12003
        return normalize_ui_result(value, operation=operation, kind="army", subject_id=subject,
            native_revision=3, date_raw=53146848, actor_id=29829, expected_build=CK3_12003,
            army_tooltip_kind=tooltip_kind, army_tooltip_receipt=None if operation == "hover_army_tooltip" else receipt)

    def test_cache_bytes_are_exact_evidence_and_all_refresh_claims_remain_false(self):
        for text in ("", "#T 补给状态#!\n-2.5%\n", "  汉字\r\n尾行\n", "literal\\n#P +0.0#!"):
            raw=army_tooltip_result(text=text)
            raw["army_tooltip"]["observed_cache"]["sha256"]=raw["army_tooltip"]["observed_cache"]["sha256"].upper()
            with self.subTest(text=text):
                got=self.normalize(raw)
                self.assertEqual(got["army_tooltip"],raw["army_tooltip"])
                self.assertFalse(got["army_tooltip"]["available"])
                self.assertFalse(got["army_tooltip"]["text_refresh_verified"])
                self.assertFalse(got["army_tooltip"]["rendered_verified"])
                self.assertIsNone(got["army_tooltip"]["gui_update_epoch"])
                self.assertTrue(got["verification_pending"])

    def test_utf8_size_hash_and_complete_cache_keys_reject_mixed_text(self):
        for key,changed in (("text","changed"),("utf8_bytes",True),("utf8_bytes",0),("sha256","0"*64),("sha256",None)):
            raw=army_tooltip_result();raw["army_tooltip"]["observed_cache"][key]=changed
            with self.subTest(key=key,changed=changed),self.assertRaises(ValueError):self.normalize(raw)
        for cache in (None,{}, {"text":"", "utf8_bytes":0, "sha256":"0"*64, "pointer":100}):
            raw=army_tooltip_result();raw["army_tooltip"]["observed_cache"]=cache
            with self.subTest(cache=cache),self.assertRaises(ValueError):self.normalize(raw)

    def test_refresh_gui_epoch_available_and_boolean_claims_reject(self):
        for key,changed in (("available",True),("text_refresh_verified",True),("rendered_verified",True),
                ("gui_update_epoch",15),("verification_pending",False),("source_bound",1),("cache_bytes_observed",1)):
            raw=army_tooltip_result();raw["army_tooltip"][key]=changed
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)

    def test_source_stack_locked_root_and_visible_subject_must_match_actual_cache(self):
        for key,changed in (("source_bound",False),("hover_matches_source",False),("active_stack_read",False),
                ("active_count",None),("active_count",True),("active_top_index",1),("active_top_index",None),
                ("active_top_locked",True),("active_top_locked",None),("active_root_available",False),
                ("tooltip_text_child_path",None),("source_child_path","0//2"),("leave_observed",True)):
            raw=army_tooltip_result();raw["army_tooltip"][key]=changed
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)
        for key,changed in (("current_subject_id",1),("subject_id_available",False),("effective_visible",False)):
            raw=army_tooltip_result();raw[key]=changed
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)
        raw=army_tooltip_result();raw["tree"]["truncated"]=True
        with self.assertRaises(ValueError):self.normalize(raw)

    def test_query_requires_matching_lower_hex_receipt_and_later_application_epoch(self):
        for key,changed in (("receipt_id",LEAVE_RECEIPT),("receipt_id","A"*32),("receipt_id",None),
                ("action_owner_epoch",0),("action_owner_epoch",True),("later_owner_epoch",None),
                ("later_owner_epoch",14),("later_owner_epoch",True),("later_owner_epoch",2**64)):
            raw=army_tooltip_result();raw["army_tooltip"][key]=changed
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(raw)

    def test_action_ack_is_pending_and_leave_rotates_receipt(self):
        hover=army_tooltip_result("hover_army_tooltip",phase="ack")
        self.assertEqual(self.normalize(hover,"hover_army_tooltip")["army_tooltip"]["receipt_id"],HOVER_RECEIPT)
        leave=army_tooltip_result("leave_army_tooltip",phase="ack",receipt=LEAVE_RECEIPT)
        got=self.normalize(leave,"leave_army_tooltip")
        self.assertEqual(got["army_tooltip"]["receipt_id"],LEAVE_RECEIPT)
        self.assertIsNone(got["army_tooltip"]["active_count"])
        self.assertIsNone(got["army_tooltip"]["observed_cache"])
        leave["dispatch_invoked"]=False
        with self.assertRaises(ValueError):self.normalize(leave,"leave_army_tooltip")

    def test_later_leave_observation_keeps_null_cache_and_nullable_top_entry(self):
        raw=army_tooltip_result(phase="leave",receipt=LEAVE_RECEIPT)
        got=self.normalize(raw,receipt=LEAVE_RECEIPT)
        self.assertTrue(got["army_tooltip"]["leave_observed"])
        self.assertFalse(got["army_tooltip"]["cache_bytes_observed"])
        self.assertIsNone(got["army_tooltip"]["observed_cache"])
        self.assertEqual(got["army_tooltip"]["active_count"],0)
        self.assertIsNone(got["army_tooltip"]["active_top_index"])
        self.assertIsNone(got["army_tooltip"]["active_top_locked"])
        for key,changed in (("hover_matches_source",True),("leave_observed",False),("observed_cache",{})):
            bad=copy.deepcopy(raw);bad["army_tooltip"][key]=changed
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(bad,receipt=LEAVE_RECEIPT)

    def test_unavailable_clears_all_observations_and_receipt(self):
        raw=army_tooltip_result(phase="unavailable")
        self.assertFalse(self.normalize(raw)["army_tooltip"]["verification_pending"])
        for key,changed in (("receipt_id",HOVER_RECEIPT),("action_owner_epoch",14),("active_count",0),
                ("active_top_locked",False),("source_child_path",""),("observed_cache",{}),
                ("source_bound",True),("unavailable_reason",""),("verification_pending",True)):
            bad=copy.deepcopy(raw);bad["army_tooltip"][key]=changed
            with self.subTest(key=key),self.assertRaises(ValueError):self.normalize(bad)

    def test_request_receipt_kind_public_id_revision_are_strict_before_dispatch(self):
        for subject,kind,receipt,revision in ((True,"supply_state",HOVER_RECEIPT,4),(-1,"attrition",HOVER_RECEIPT,4),
                (2**31,"attrition",HOVER_RECEIPT,4),(0,"arbitrary",HOVER_RECEIPT,4),(0,True,HOVER_RECEIPT,4),
                (0,"attrition","A"*32,4),(0,"attrition","0x1000",4),(0,"attrition",None,4),
                (0,"attrition",True,4),(0,"attrition",HOVER_RECEIPT,True)):
            driver=CurrentUiDriverFixture(army_tooltip_result())
            with self.subTest(subject=subject,kind=kind,receipt=receipt,revision=revision),self.assertRaises(ValueError):
                driver.query_army_tooltip_v1(subject,kind,receipt,expected_revision=revision)
            self.assertFalse(driver.calls)
        with self.assertRaises(ValueError):validate_ui_request("hover_army_tooltip","army",0,4,
            army_tooltip_kind="attrition",army_tooltip_receipt=HOVER_RECEIPT)
        with self.assertRaises(ValueError):validate_ui_request("query","army",0,4,army_tooltip_receipt=HOVER_RECEIPT)

    def test_driver_wire_lifecycle_preserves_public_zero_and_returned_nonce(self):
        for subject in (0,16777218,2**31-1):
            for kind in ("supply_state","attrition"):
                with self.subTest(subject=subject,kind=kind):
                    driver=CurrentUiDriverFixture(army_tooltip_result("hover_army_tooltip",subject,kind,phase="ack"))
                    hovered=driver.hover_army_tooltip_v1(subject,kind,expected_revision=4)
                    self.assertEqual(driver.calls[-1][1]["request_fields"],{"window_kind":"army","subject_id":subject,
                        "operation":"hover_army_tooltip","army_tooltip_kind":kind})
                    driver.raw=army_tooltip_result(subject=subject,tooltip_kind=kind)
                    driver.query_army_tooltip_v1(subject,kind,hovered["army_tooltip"]["receipt_id"],expected_revision=4)
                    self.assertEqual(driver.calls[-1][0],"query-ingame-ui-window-v1")
                    self.assertEqual(driver.calls[-1][1]["request_fields"],{"window_kind":"army","subject_id":subject,
                        "army_tooltip_kind":kind,"army_tooltip_receipt":HOVER_RECEIPT})
                    driver.raw=army_tooltip_result("leave_army_tooltip",subject,kind,phase="ack",receipt=LEAVE_RECEIPT)
                    left=driver.leave_army_tooltip_v1(subject,kind,HOVER_RECEIPT,expected_revision=4)
                    self.assertEqual(left["army_tooltip"]["receipt_id"],LEAVE_RECEIPT)
                    driver.raw=army_tooltip_result(subject=subject,tooltip_kind=kind,phase="leave",receipt=LEAVE_RECEIPT)
                    driver.query_army_tooltip_v1(subject,kind,left["army_tooltip"]["receipt_id"],expected_revision=4)
                    self.assertEqual(driver.calls[-1][1]["request_fields"]["army_tooltip_receipt"],LEAVE_RECEIPT)

    def test_old_missing_hello_legacy_and_unmigrated_build_never_dispatch(self):
        from xar_autoplayer.bridge.version_identity import CK3_11906,CK3_12002
        samples=[snapshot()]
        for build in (CK3_11906,CK3_12002):
            before=current_snapshot();before["diagnostics"]["hello"]={"expected_ck3_version":build.game_version,
                "expected_ck3_sha256":build.executable_sha256};samples.append(before)
        for before in samples:
            driver=CurrentUiDriverFixture(army_tooltip_result())
            with patch.object(driver,"take_snapshot",return_value=before),self.subTest(before=before),self.assertRaises(ValueError):
                driver.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)
            self.assertFalse(driver.calls)

    def test_driver_exact_backend_and_existing_capability_gate_no_fallback(self):
        for capability in ({"backend_id":"desktop","bridge_capabilities":["game.command.query-ingame-ui-window-v1"]},
                {"backend_id":"native-headless","bridge_capabilities":[]}):
            driver=CurrentUiDriverFixture(army_tooltip_result())
            with patch.object(driver,"capabilities",return_value=capability),self.subTest(capability=capability),self.assertRaises(Exception):
                driver.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)
            self.assertFalse(driver.calls)

    def test_driver_post_session_connection_hello_changes_preserve_raw_failure(self):
        for key,changed in (("episode_run_id","other"),("date_raw",53146872),("played_character",{"character_id":33437}),
                ("diagnostics",{"connection_generation":3, "hello":current_snapshot()["diagnostics"]["hello"]})):
            end=current_snapshot();end[key]=changed
            raw=army_tooltip_result();driver=CurrentUiDriverFixture(raw,end)
            with self.subTest(key=key),self.assertRaises(BridgeUnavailableError):
                driver.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)
            self.assertEqual(driver.records[-1][1]["result"]["raw_native_ui_result"],raw)
        end=current_snapshot();del end["diagnostics"]["hello"]
        driver=CurrentUiDriverFixture(army_tooltip_result(),end)
        with self.assertRaises(BridgeUnavailableError):driver.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)

    def test_driver_invalid_return_keeps_unmodified_cache_in_history(self):
        raw=army_tooltip_result();raw["army_tooltip"]["observed_cache"]["sha256"]="0"*64
        driver=CurrentUiDriverFixture(raw)
        with self.assertRaises(ValueError):driver.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)
        self.assertEqual(driver.records[-1][1]["result"]["raw_native_ui_result"],raw)
        self.assertEqual(driver.records[-1][1]["result"]["raw_native_ui_result"]["army_tooltip"]["observed_cache"]["text"],raw["army_tooltip"]["observed_cache"]["text"])

    def test_real_primitive_retains_tooltip_failure_artifact(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            raw=army_tooltip_result();raw["army_tooltip"]["text_refresh_verified"]=True
            driver=CurrentPrimitiveUiFixture(raw,Path(temp))
            with self.assertRaises(ValueError):driver.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)
            saved=json.loads(next(Path(temp).rglob("native-ui-*.json")).read_text(encoding="utf-8"))
            self.assertEqual(saved["original_parsed_command_result"]["result"],raw)
            self.assertEqual(len(driver.sent),1)

    def test_ordinary_query_keeps_no_tooltip_and_no_pending_verification(self):
        from xar_autoplayer.bridge.version_identity import CK3_12003
        raw=current_result()
        self.assertFalse(normalize_ui_result(raw,operation="query",kind="army",subject_id=0,
            native_revision=3,date_raw=53146848,actor_id=29829,expected_build=CK3_12003)["verification_pending"])
        with self.assertRaises(ValueError):normalize_ui_result(army_tooltip_result(),operation="query",kind="army",subject_id=0,
            native_revision=3,date_raw=53146848,actor_id=29829,expected_build=CK3_12003)
        bad=army_tooltip_result();bad["verification_pending"]=False
        with self.assertRaises(ValueError):self.normalize(bad)

    def test_service_routes_exact_native_lifecycle_and_denies_other_builds(self):
        from xar_autoplayer.bridge.service import GameplayBridgeService
        driver=CurrentUiDriverFixture(army_tooltip_result("hover_army_tooltip",phase="ack"));service=GameplayBridgeService(driver)
        hover=service.hover_army_tooltip_v1(0,"supply_state",expected_revision=4)
        driver.raw=army_tooltip_result()
        service.query_army_tooltip_v1(0,"supply_state",hover["army_tooltip"]["receipt_id"],expected_revision=4)
        driver.raw=army_tooltip_result("leave_army_tooltip",phase="ack",receipt=LEAVE_RECEIPT)
        self.assertEqual(service.leave_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)["army_tooltip"]["receipt_id"],LEAVE_RECEIPT)
        legacy=DriverFixture(army_tooltip_result());legacy_service=GameplayBridgeService(legacy)
        with self.assertRaises(ValueError):legacy_service.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)
        self.assertFalse(legacy.calls)
        with patch.object(driver,"capabilities",return_value={"backend_id":"desktop","bridge_capabilities":["game.command.query-ingame-ui-window-v1"]}),self.assertRaises(Exception):
            service.query_army_tooltip_v1(0,"supply_state",HOVER_RECEIPT,expected_revision=4)


class ArmyTooltipMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_fixed_cold_registration_strict_schemas_and_real_service_lifecycle(self):
        from mcp import Client
        driver=CurrentUiDriverFixture(army_tooltip_result("hover_army_tooltip",phase="ack"))
        server=create_server(driver)
        self.assertEqual(driver.reads,0)
        async with Client(server) as client:
            names={tool.name:tool for tool in (await client.list_tools()).tools}
            self.assertEqual(driver.reads,0)
            for name in ("hover","leave","query"):
                schema=names[f"ck3_{name}_army_tooltip_v1"].input_schema
                required={"subject_army_id","tooltip_kind","expected_revision"}
                if name != "hover":required.add("action_receipt")
                self.assertEqual(set(schema["required"]),required)
                self.assertEqual(schema["properties"]["subject_army_id"]["minimum"],0)
                self.assertEqual(set(schema["properties"]["tooltip_kind"]["enum"]),{"supply_state","attrition"})
                self.assertFalse(any(key in schema["properties"] for key in ("pointer","path","rva","connection_generation","native_revision")))
                if name != "hover":self.assertEqual(schema["properties"]["action_receipt"]["pattern"],"^[0-9a-f]{32}$")
            args={"subject_army_id":0,"tooltip_kind":"supply_state","expected_revision":4}
            hover=await client.call_tool("ck3_hover_army_tooltip_v1",args)
            self.assertFalse(hover.is_error)
            receipt=hover.structured_content["army_tooltip"]["receipt_id"]
            self.assertEqual(receipt,HOVER_RECEIPT)
            driver.raw=army_tooltip_result()
            query=await client.call_tool("ck3_query_army_tooltip_v1",{**args,"action_receipt":receipt})
            self.assertFalse(query.is_error)
            self.assertTrue(query.structured_content["army_tooltip"]["cache_bytes_observed"])
            self.assertFalse(query.structured_content["army_tooltip"]["available"])
            self.assertTrue(query.structured_content["verification_pending"])
            driver.raw=army_tooltip_result("leave_army_tooltip",phase="ack",receipt=LEAVE_RECEIPT)
            leave=await client.call_tool("ck3_leave_army_tooltip_v1",{**args,"action_receipt":receipt})
            self.assertFalse(leave.is_error)
            rotated=leave.structured_content["army_tooltip"]["receipt_id"]
            self.assertEqual(rotated,LEAVE_RECEIPT)
            driver.raw=army_tooltip_result(phase="leave",receipt=rotated)
            after=await client.call_tool("ck3_query_army_tooltip_v1",{**args,"action_receipt":rotated})
            self.assertFalse(after.is_error)
            self.assertTrue(after.structured_content["army_tooltip"]["leave_observed"])
            count=len(driver.calls)
            for changes in ({"subject_army_id":True},{"subject_army_id":-1},{"tooltip_kind":"arbitrary"},
                    {"expected_revision":True},{"action_receipt":"A"*32},{"action_receipt":"0x1000"}):
                failed=await client.call_tool("ck3_query_army_tooltip_v1",{**args,"action_receipt":rotated,**changes})
                self.assertTrue(failed.is_error)
            self.assertEqual(len(driver.calls),count)

    async def test_registered_interface_is_not_legacy_tooltip_capability(self):
        from mcp import Client
        driver=DriverFixture(army_tooltip_result());server=create_server(driver)
        async with Client(server) as client:
            self.assertIn("ck3_query_army_tooltip_v1",{tool.name for tool in (await client.list_tools()).tools})
            failed=await client.call_tool("ck3_query_army_tooltip_v1",{"subject_army_id":0,"tooltip_kind":"attrition",
                "action_receipt":HOVER_RECEIPT,"expected_revision":4})
            self.assertTrue(failed.is_error)
            self.assertFalse(driver.calls)


if __name__=="__main__":unittest.main()
