from __future__ import annotations
import copy
from pathlib import Path
import sys
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

if __name__=="__main__":unittest.main()
