"""Synthetic generic decision dispatch, persistent no-replay and SDK regressions.

No CK3, DLL, desktop input or native callback is invoked by these tests.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import os
import tempfile
import unittest
import struct
import threading
from types import SimpleNamespace
from unittest.mock import patch

from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeNamedPipeServer
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256, opening_binding
from xar_autoplayer.bridge.ingame_decision_item_action_contract import SELECT_CAPABILITY, CONFIRM_CAPABILITY
from xar_autoplayer.bridge.ingame_decision_outcome_contract import (
    STEP, CAPABILITY, SCHEMA, validate_expected_outcome, actual_expected_event,
    actual_closed_decision_detail, outcome_frame_matches,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.event_window_context_contract import _EVENT_PROVENANCE_BY_BACKEND
from test_ingame_decision_item_actions import frame, model, ack, SyntheticDriver as SelectDriver, KEY as VIVHITE_KEY
from test_ingame_decisions_open_contract import SyntheticDriver as OpenDriver
from test_event_window_context_v1_bridge import _frame

KEY = "generic_decision_open_event"
EVENT_KEY = "generic_events.100"


def decision_model(binding, *, selected=True):
    result = model(binding, selected=selected)
    result["decision_key"] = KEY
    result["detail_decision_key"] = KEY if selected else ""
    return result


def outcome_ack(binding, outcome="event_window"):
    result = ack(binding, "confirm")
    result.update(schema=SCHEMA, step=STEP, action="confirm_outcome", decision_key=KEY,
                  expected_outcome=outcome,
                  expected_event_definition_key=EVENT_KEY if outcome == "event_window" else "",
                  no_blocking_modal_verified=True, native_call_completed=True,
                  before_actual_model=decision_model(binding))
    return result


def event_query(snapshot):
    context = _frame()
    context.update(snapshot_revision=snapshot["native_revision"], date_raw=snapshot["date_raw"],
                   current_event_instance_id=snapshot["active_event"]["instance_id"],
                   event_definition_key=EVENT_KEY,
                   root_scope={"status": "available", "raw_type_index": 4, "type_key": "character",
                               "subtype": 0, "typed_identity": {"status": "available", "kind": "character",
                                                               "character_id": 7001}},
                   saved_scopes=[],
                   provenance=deepcopy(_EVENT_PROVENANCE_BY_BACKEND["ck3-1.20.0.3-native-event-window-v1"]))
    context["options"][0]["effect_indicators"]["coverage"] = "played-character-event-icon-indicators-1.20.0.3-v1"
    context["options"][0]["effect_indicators"]["rows"] = []
    return {"current_event_window_context": context, "current_event_window_context_ready": True,
            "queried_revision": snapshot["revision"], "queried_native_revision": snapshot["native_revision"]}


def closed_tree(hidden=True):
    return {"schema": "ck3-native-gui-window-tree-inspection-v1", "window_kind": "decision_detail",
            "scope_root_name": "decisiondetail_view", "read_only": True, "root_available": True,
            "truncated": False, "widget_count": 1,
            "widgets": [{"child_path": "", "runtime_name": "decisiondetail_view", "effective_visible": not hidden}]}


class OutcomeDriver:
    confirm_ingame_decision_outcome_v1 = NativeHeadlessGameplayDriver.confirm_ingame_decision_outcome_v1
    def __init__(self, directory, outcome="event_window"):
        self.directory=Path(directory)
        self.frame=frame()
        self.frame.update(speed=3,active_event=None,pending_character_interaction=None)
        self.outcome=outcome
        self.native_ack=outcome_ack(opening_binding(self.frame),outcome)
        self.error=None
        self.after_mutation=None
        self.query_mutation=None
        self.submissions=[]
        self.queries=[]
        self.selected=True
        self.tree=closed_tree()
        self.records=[]
        self.caps={CAPABILITY, "game.command.query-ingame-decision-item-v1",
                   "game.command.query-current-event-window-context-v1", "game.command.inspect-gui-window-tree-v1",
                   "game.command.query-frontend-gui-route-v1"}
    def take_snapshot(self):return deepcopy(self.frame)
    def capabilities(self):return {"bridge_capabilities":sorted(self.caps)}
    def _native_driver_state_path(self):return self.directory/"driver-state.json"
    def _record_command(self,*args,**kwargs):self.records.append((args,kwargs))
    def query_ingame_decision_item_v1(self,key,**kwargs):
        self.queries.append(("model",key,kwargs))
        return decision_model(opening_binding(self.frame),selected=self.selected)
    def _execute_primitive_step(self,step,**kwargs):
        self.submissions.append((step,kwargs))
        if self.error:raise self.error
        self.frame.update(revision=self.frame["revision"]+1,native_revision=self.frame["native_revision"]+1,
                          snapshot_id="synthetic-generic-outcome-after")
        if self.outcome=="event_window":self.frame["active_event"]={"instance_id":200,"option_count":1}
        self.selected=False
        if self.after_mutation:self.after_mutation(self.frame)
        return deepcopy(self.native_ack)
    def query_current_event_window_context_v1(self,instance,**kwargs):
        self.queries.append(("event",instance,kwargs))
        result=event_query(self.frame)
        if self.query_mutation:self.query_mutation(result,self.frame)
        return result
    def inspect_gui_window_tree_v1(self,kind):
        self.queries.append(("tree",kind))
        return deepcopy(self.tree)


class MemoryPrimitiveOutcomeDriver(OutcomeDriver):
    """Run the actual primitive and production packet encoder into memory only."""
    _execute_primitive_step=NativeHeadlessGameplayDriver._execute_primitive_step
    _verify_idempotent_map_control_postcondition=NativeHeadlessGameplayDriver._verify_idempotent_map_control_postcondition
    def __init__(self,directory,outcome):
        super().__init__(directory,outcome)
        self._request_sequence=0
        self.command_timeout_seconds=.1
        self.packets=[]
        self.last_raw=None
        self.endpoint=SimpleNamespace(send=self.capture_request)
        self.state=SimpleNamespace(wait_for_command_result=lambda request_id,timeout:{"ok":True,"result":deepcopy(self.last_raw)})
    def capture_request(self,request):
        # No pipe is created or started. The actual production encoder runs
        # with its sole low-level write replaced by an in-memory collector.
        fake_pipe=SimpleNamespace(_write_lock=threading.Lock(),_current_handle=lambda:1)
        def collect(handle,packet):
            self.packets.append(bytes(packet))
            path=self.directory/f"actual-production-encoder-{len(self.packets):02d}.bin"
            with path.open("xb") as stream:stream.write(packet)
            with path.with_suffix(".json").open("x",encoding="utf-8") as stream:
                json.dump(json.loads(packet[4:]),stream,indent=2)
            return True
        with patch("xar_autoplayer.bridge.native_driver._write_all",side_effect=collect):
            NativeNamedPipeServer.send(fake_pipe,request)
        fields={key:value for key,value in request.items()
                if key not in {"type","protocol_version","request_id","step","expected_revision"}}
        self.last_raw=OutcomeDriver._execute_primitive_step(self,request["step"],
            request_fields=fields,protocol_request_id=request["request_id"],expected_revision=request["expected_revision"])


class OutcomeTests(unittest.TestCase):
    def directory(self):
        parent=os.environ.get("XAR_DECISION_OUTCOME_TEST_ARTIFACTS")
        if parent:Path(parent).mkdir(parents=True,exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="synthetic-outcome-",dir=parent))
    def call(self,driver):
        return driver.confirm_ingame_decision_outcome_v1(
            KEY,driver.outcome,expected_event_definition_key=EVENT_KEY if driver.outcome=="event_window" else None,
            expected_revision=driver.frame["revision"])
    def test_declared_outcome_is_closed_and_rejects_mixed_branch_arguments(self):
        self.assertEqual(validate_expected_outcome("event_window",EVENT_KEY),EVENT_KEY)
        self.assertEqual(validate_expected_outcome("decision_closed",None),"")
        for outcome,key in [("arbitrary",None),("event_window",None),("event_window","x;injected"),
                            ("event_window","event_namespace"),("decision_closed",EVENT_KEY),("decision_closed","")]:
            with self.subTest(outcome=outcome,key=key),self.assertRaises(ValueError):validate_expected_outcome(outcome,key)
    def test_actual_primitive_and_production_packet_encoder_preserve_closed_empty_key(self):
        for outcome in ("event_window","decision_closed"):
            with self.subTest(outcome=outcome):
                driver=MemoryPrimitiveOutcomeDriver(self.directory(),outcome)
                self.call(driver)
                self.assertEqual(len(driver.packets),1)
                packet=driver.packets[0]
                size=struct.unpack("<I",packet[:4])[0]
                self.assertEqual(size,len(packet)-4)
                payload=packet[4:]
                request=json.loads(payload)
                self.assertEqual(request["expected_revision"],7)
                self.assertEqual(request["decision_key"],KEY)
                self.assertEqual(request["expected_outcome"],outcome)
                self.assertEqual(request["expected_event_definition_key"],EVENT_KEY if outcome=="event_window" else "")
                self.assertEqual(set(request),{"type","protocol_version","request_id","step","expected_revision",
                                               "decision_key","expected_outcome","expected_event_definition_key",
                                               "expected_player_character_id","expected_game_pid","expected_connection_generation"})
                if outcome=="decision_closed":
                    self.assertIn(b'"expected_event_definition_key":""',payload)
                    self.assertNotIn(b'"expected_event_definition_key":null',payload)
    def test_event_requires_actual_later_namespace_instance_root_and_revision(self):
        driver=OutcomeDriver(self.directory())
        result=self.call(driver)
        self.assertEqual(len(driver.submissions),1)
        self.assertEqual(result["status"],"observed_current_event_window")
        self.assertFalse(result["native_ack"]["postcondition_verified"])
        self.assertTrue(result["postcondition_verified"])
        self.assertFalse(result["front_event_verified"])
        self.assertFalse(result["event_option_selection_authorized"])
        self.assertFalse(result["business_effects_verified"])
        self.assertFalse(result["full_product_acceptance_credit"])
        wire=driver.submissions[0][1]["request_fields"]
        self.assertEqual(set(wire),{"decision_key","expected_outcome","expected_event_definition_key",
                                    "expected_player_character_id","expected_game_pid","expected_connection_generation"})
        self.assertEqual(wire["decision_key"],KEY)
        self.assertEqual(wire["expected_event_definition_key"],EVENT_KEY)
        claim=Path(result["action_claim_path"])
        self.assertTrue(claim.with_suffix(".verified.json").is_file())
    def test_state_only_close_has_no_fabricated_event_or_business_pass(self):
        driver=OutcomeDriver(self.directory(),"decision_closed")
        result=self.call(driver)
        self.assertEqual(result["status"],"observed_decision_detail_closed")
        self.assertIsNone(result["snapshot_after"]["active_event"])
        self.assertEqual(result["expected_event_definition_key"],"")
        self.assertFalse(result["business_effects_verified"])
        self.assertFalse(any(q[0]=="event" for q in driver.queries))
    def test_after_hidden_decision_row_does_not_replace_actual_detail_census(self):
        for hidden in (False,True):
            with self.subTest(hidden=hidden):
                driver=OutcomeDriver(self.directory(),"decision_closed")
                driver.tree=closed_tree(hidden)
                original=driver.query_ingame_decision_item_v1
                def vanished_after(key,**kwargs):
                    if driver.submissions:
                        raise AssertionError("after row disappeared; its default detail flags must not be read as closure")
                    return original(key,**kwargs)
                driver.query_ingame_decision_item_v1=vanished_after
                if hidden:
                    result=self.call(driver)
                    self.assertEqual(result["status"],"observed_decision_detail_closed")
                else:
                    with patch("xar_autoplayer.bridge.native_driver.time.monotonic",side_effect=[0.0,6.0]):
                        with self.assertRaisesRegex(BridgeUnavailableError,"requested outcome"):self.call(driver)
                self.assertEqual(len(driver.submissions),1)
                self.assertEqual(len([q for q in driver.queries if q[0]=="model"]),1)
                self.assertEqual(len([q for q in driver.queries if q[0]=="tree"]),1)
    def test_closed_gui_observer_identity_dependency_is_required_before_dispatch(self):
        driver=OutcomeDriver(self.directory(),"decision_closed")
        driver.caps.remove("game.command.query-frontend-gui-route-v1")
        with self.assertRaises(UnsupportedStepError):self.call(driver)
        self.assertEqual(driver.submissions,[]);self.assertEqual(driver.queries,[])
    def test_actual_new_event_revision_and_resource_change_are_legitimate(self):
        driver=OutcomeDriver(self.directory())
        driver.after_mutation=lambda frame:frame["played_character"].update(gold={"raw":10000,"scale":1000})
        result=self.call(driver)
        self.assertEqual(result["snapshot_after"]["native_revision"],8)
        self.assertTrue(result["postcondition_verified"])
    def test_existing_event_or_pending_requires_zero_model_queries_or_dispatch(self):
        for key in ("active_event","pending_character_interaction"):
            with self.subTest(key=key):
                driver=OutcomeDriver(self.directory());driver.frame[key]={"instance_id":99}
                with self.assertRaises(BridgeUnavailableError):self.call(driver)
                self.assertEqual(driver.submissions,[]);self.assertEqual(driver.queries,[])
    def test_stale_revision_and_missing_capability_require_zero_dispatch(self):
        driver=OutcomeDriver(self.directory())
        with self.assertRaises(Exception):driver.confirm_ingame_decision_outcome_v1(KEY,"event_window",expected_event_definition_key=EVENT_KEY,expected_revision=2)
        self.assertEqual(driver.submissions,[])
        driver.caps.remove(CAPABILITY)
        with self.assertRaises(UnsupportedStepError):self.call(driver)
        self.assertEqual(driver.submissions,[])
    def test_actual_unselected_detail_rejects_before_claim(self):
        driver=OutcomeDriver(self.directory());driver.selected=False
        with self.assertRaisesRegex(BridgeUnavailableError,"selected detail"):self.call(driver)
        self.assertEqual(driver.submissions,[])
        self.assertFalse((driver.directory/"ingame-decision-item-actions").exists())
    def test_missing_ack_and_changed_outcome_cannot_retry_at_new_revision_reconnect(self):
        directory=self.directory();driver=OutcomeDriver(directory);driver.error=TimeoutError("synthetic lost native ACK")
        with self.assertRaises(TimeoutError):self.call(driver)
        self.assertEqual(len(driver.submissions),1)
        later=OutcomeDriver(directory,"decision_closed")
        later.frame["revision"]+=10;later.frame["native_revision"]+=10
        later.frame["diagnostics"]["connection_generation"]+=1
        with self.assertRaisesRegex(BridgeUnavailableError,"unresolved"):self.call(later)
        self.assertEqual(later.submissions,[]);self.assertEqual(later.queries,[])
    def test_native_ack_cannot_self_certify_or_change_the_echoed_outcome(self):
        for field,value in [("postcondition_verified",True),("verification_pending",False),
                            ("expected_event_definition_key","another_namespace.1"),("expected_outcome","decision_closed"),
                            ("receiver_qualified",False),("detail_actor_binding_verified",False),
                            ("no_blocking_modal_verified",False)]:
            with self.subTest(field=field):
                driver=OutcomeDriver(self.directory());driver.native_ack[field]=value
                with self.assertRaises(ValueError):self.call(driver)
                self.assertEqual(len(driver.submissions),1)
                self.assertFalse(any(q[0]=="event" for q in driver.queries))
    def test_later_key_instance_root_provenance_or_readiness_mismatch_is_not_opened(self):
        changes=[lambda r,f:r["current_event_window_context"].update(event_definition_key="other_events.100"),
                 lambda r,f:r["current_event_window_context"].update(current_event_instance_id=201),
                 lambda r,f:r["current_event_window_context"]["root_scope"]["typed_identity"].update(character_id=7002),
                 lambda r,f:r["current_event_window_context"]["provenance"].update(backend_id="fake-provider"),
                 lambda r,f:r.update(current_event_window_context_ready=False),
                 lambda r,f:r.update(queried_revision=100)]
        for mutation in changes:
            driver=OutcomeDriver(self.directory());driver.query_mutation=mutation
            with patch("xar_autoplayer.bridge.native_driver.time.monotonic",side_effect=[0.0,6.0]):
                with self.assertRaisesRegex(BridgeUnavailableError,"requested outcome"):self.call(driver)
            self.assertEqual(len(driver.submissions),1)
            self.assertEqual(len(list((driver.directory/"ingame-decision-item-actions").glob("*.verified.json"))),0)
    def test_connection_actor_date_speed_or_pause_drift_is_rejected_after_one_dispatch(self):
        changes=[lambda f:f["diagnostics"].update(connection_generation=2),
                 lambda f:f["played_character"].update(character_id=7002),
                 lambda f:f.update(date_raw=1235),lambda f:f.update(speed=5),lambda f:f.update(paused=False)]
        for mutation in changes:
            driver=OutcomeDriver(self.directory());driver.after_mutation=mutation
            with self.assertRaisesRegex(BridgeUnavailableError,"frame changed"):self.call(driver)
            self.assertEqual(len(driver.submissions),1)
    def test_state_branch_unexpected_event_or_visible_detail_is_red_no_retry(self):
        driver=OutcomeDriver(self.directory(),"decision_closed")
        driver.after_mutation=lambda f:f.update(active_event={"instance_id":200,"option_count":1})
        with self.assertRaisesRegex(BridgeUnavailableError,"unexpectedly opened an event"):self.call(driver)
        self.assertEqual(len(driver.submissions),1)
        driver=OutcomeDriver(self.directory(),"decision_closed");driver.tree=closed_tree(False)
        with patch("xar_autoplayer.bridge.native_driver.time.monotonic",side_effect=[0.0,6.0]):
            with self.assertRaisesRegex(BridgeUnavailableError,"requested outcome"):self.call(driver)
        self.assertEqual(len(driver.submissions),1)
    def test_closed_tree_absence_truncation_duplicate_and_wrong_scope_do_not_prove_close(self):
        self.assertTrue(actual_closed_decision_detail(closed_tree()))
        values=[]
        for key,value in [("root_available",False),("truncated",True),("scope_root_name","other_view"),("widget_count",2)]:
            value_tree=closed_tree();value_tree[key]=value;values.append(value_tree)
        value_tree=closed_tree();value_tree["widgets"]*=2;value_tree["widget_count"]=2;values.append(value_tree)
        for value in values:self.assertFalse(actual_closed_decision_detail(value))
    def test_direct_replay_without_fresh_selected_detail_fails_even_at_new_revision(self):
        driver=OutcomeDriver(self.directory(),"decision_closed")
        self.call(driver)
        with self.assertRaisesRegex(BridgeUnavailableError,"selected detail"):self.call(driver)
        self.assertEqual(len(driver.submissions),1)
    def test_actual_later_revision_and_fresh_selection_can_confirm_again(self):
        driver=OutcomeDriver(self.directory(),"decision_closed")
        self.call(driver)
        driver.selected=True
        driver.native_ack=outcome_ack(opening_binding(driver.frame),"decision_closed")
        result=self.call(driver)
        self.assertTrue(result["postcondition_verified"])
        self.assertEqual(len(driver.submissions),2)
        self.assertEqual(len(list((driver.directory/"ingame-decision-item-actions").glob("*.verified.json"))),2)
    def test_service_independently_rechecks_actual_outcome_and_refuses_business_overcredit(self):
        driver=OutcomeDriver(self.directory(),"decision_closed")
        original=driver.confirm_ingame_decision_outcome_v1
        def overcredit(*args,**kwargs):
            result=original(*args,**kwargs);result["business_effects_verified"]=True;return result
        driver.confirm_ingame_decision_outcome_v1=overcredit
        service=GameplayBridgeService(driver)
        with self.assertRaisesRegex(BridgeUnavailableError,"independent UI-outcome"):service.confirm_ingame_decision_outcome_v1(KEY,"decision_closed",expected_revision=1)
        self.assertEqual(len(driver.submissions),1)
    def test_open_unknown_result_blocks_a_changed_public_revision(self):
        directory=self.directory();driver=OpenDriver(directory,action_error=TimeoutError("synthetic lost opener ACK"))
        with self.assertRaises(TimeoutError):driver.open_ingame_decisions_v1()
        later=OpenDriver(directory);later.frame["revision"]=10;later.frame["native_revision"]=17
        later.frame["diagnostics"]["connection_generation"]=2
        with self.assertRaisesRegex(BridgeUnavailableError,"unresolved"):later.open_ingame_decisions_v1(expected_revision=10)
        self.assertEqual(later.submissions,[])
    def test_selected_unknown_result_blocks_a_changed_public_revision(self):
        directory=self.directory();driver=SelectDriver(directory,action_error=TimeoutError("synthetic lost selector ACK"))
        with self.assertRaises(TimeoutError):driver.select_ingame_decision_item_v1(VIVHITE_KEY)
        later=SelectDriver(directory);later.frame["revision"]=10;later.frame["native_revision"]=17
        later.frame["diagnostics"]["connection_generation"]=2
        with self.assertRaisesRegex(BridgeUnavailableError,"unresolved"):later.select_ingame_decision_item_v1(VIVHITE_KEY,expected_revision=10)
        self.assertEqual(later.submissions,[]);self.assertEqual(later.model_queries,[])
    def test_verified_open_and_select_can_use_a_fresh_revision_but_not_same_revision(self):
        for kind in ("open","select"):
            with self.subTest(kind=kind):
                directory=self.directory();driver=OpenDriver(directory) if kind=="open" else SelectDriver(directory)
                invoke=(lambda d,r:d.open_ingame_decisions_v1(expected_revision=r)) if kind=="open" else (lambda d,r:d.select_ingame_decision_item_v1(VIVHITE_KEY,expected_revision=r))
                invoke(driver,1)
                with self.assertRaisesRegex(BridgeUnavailableError,"already claimed"):invoke(driver,1)
                driver.frame["revision"]=2
                invoke(driver,2)
                self.assertEqual(len(driver.submissions),2)
    def test_tampered_verification_does_not_unlock_a_prior_unknown_action(self):
        driver=OutcomeDriver(self.directory(),"decision_closed")
        result=self.call(driver);path=Path(result["action_claim_path"]).with_suffix(".verified.json")
        verified=json.loads(path.read_text(encoding="utf-8"));verified["request_id"]="foreign-request"
        path.write_text(json.dumps(verified),encoding="utf-8")
        driver.selected=True
        with self.assertRaisesRegex(BridgeUnavailableError,"verification evidence is invalid"):self.call(driver)
        self.assertEqual(len(driver.submissions),1)
    def test_switching_between_generic_and_vivhite_cannot_replay_unknown_confirm(self):
        directory=self.directory();legacy=SelectDriver(directory,action="confirm",action_error=TimeoutError("unknown fixed Confirm"))
        with self.assertRaises(TimeoutError):legacy.confirm_ingame_decision_item_v1(VIVHITE_KEY,"vivhite_courtier")
        generic=OutcomeDriver(directory,"decision_closed");generic.frame["revision"]=2
        with self.assertRaisesRegex(BridgeUnavailableError,"unresolved"):
            generic.confirm_ingame_decision_outcome_v1(VIVHITE_KEY,"decision_closed",expected_revision=2)
        self.assertEqual(generic.submissions,[])
        directory=self.directory();generic=OutcomeDriver(directory,"decision_closed");generic.error=TimeoutError("unknown generic Confirm")
        with self.assertRaises(TimeoutError):self.call(generic)
        legacy=SelectDriver(directory,action="confirm");legacy.frame["revision"]=2
        with self.assertRaisesRegex(BridgeUnavailableError,"unresolved"):
            legacy.confirm_ingame_decision_item_v1(KEY,"vivhite_courtier",expected_revision=2)
        self.assertEqual(legacy.submissions,[])


class ProfileAdapterTests(unittest.TestCase):
    def setup_profile(self,root):
        from test_ck3_native_profile_mcp import service_fixture
        service,backend,driver,_,_=service_fixture(root)
        service.attach()
        driver.snapshot.update(native_revision=7,active_event=None,played_character={"character_id":7001,"alive":True})
        driver.snapshot["diagnostics"]["connection_generation"]=1
        calls=[]
        class Gameplay:
            def confirm_ingame_decision_outcome_v1(self,key,outcome,**kwargs):
                calls.append((key,outcome,kwargs))
                return {"schema":SCHEMA,"action":"confirm_outcome","decision_key":key,
                        "expected_outcome":outcome,"expected_event_definition_key":"",
                        "postcondition_verified":True,"verification_pending":False,
                        "business_effects_verified":False,"full_product_acceptance_credit":False,
                        "front_event_verified":False,"event_option_selection_authorized":False,
                        "snapshot_after":deepcopy(driver.snapshot),"later_actual_observation":closed_tree()}
        service._gameplay=Gameplay()
        service._postcondition_timeout_seconds=.01
        service._postcondition_poll_seconds=.001
        return service,backend,driver,calls
    def test_profile_closed_outcome_reads_actual_ui_observation_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            service,_,_,calls=self.setup_profile(Path(temporary))
            result=service.decision_action("confirm_outcome",7,decision_key=KEY,expected_outcome="decision_closed")
            self.assertEqual(result["status"],"native_gameplay_postcondition_verified")
            self.assertEqual(len(calls),1)
            self.assertFalse(result["result"]["business_effects_verified"])
            self.assertTrue(Path(result["receipt_path"]).is_file())
    def test_profile_ack_only_and_missing_or_wrong_observation_are_red_after_one_call(self):
        for mutation in (lambda r:r.update(postcondition_verified=False),
                         lambda r:r.pop("later_actual_observation"),
                         lambda r:r.update(later_actual_observation=closed_tree(False)),
                         lambda r:r.update(front_event_verified=True)):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temporary:
                service,_,_,calls=self.setup_profile(Path(temporary))
                original=service._gameplay.confirm_ingame_decision_outcome_v1
                def altered(*args,**kwargs):
                    result=original(*args,**kwargs);mutation(result);return result
                service._gameplay.confirm_ingame_decision_outcome_v1=altered
                result=service.decision_action("confirm_outcome",7,decision_key=KEY,expected_outcome="decision_closed")
                self.assertEqual(result["status"],"RED");self.assertEqual(len(calls),1)
    def test_profile_mixed_outcome_stale_revision_and_lease_guard_issue_zero_calls(self):
        for mode in ("mixed","stale","lease","foreground","offline"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                service,backend,_,calls=self.setup_profile(Path(temporary))
                if mode=="lease":backend.desktop.overrides["screen_lease_fresh"]=False
                elif mode=="foreground":backend.desktop.overrides["focus"]={"foreground_hwnd":999,"foreground_pid":999}
                elif mode=="offline":backend.desktop.overrides["steam_offline_flags"]=["0"]
                with self.assertRaises((ValueError,RuntimeError)):
                    service.decision_action("confirm_outcome",8 if mode=="stale" else 7,decision_key=KEY,
                                            expected_outcome="decision_closed",
                                            expected_event_definition_key=EVENT_KEY if mode=="mixed" else None)
                self.assertEqual(calls,[])


class DecisionSchemaTests(unittest.IsolatedAsyncioTestCase):
    async def test_profile_four_routes_have_closed_schema_and_reject_caller_identity(self):
        from mcp import Client
        import ck3_native_profile_mcp as native
        from test_ck3_native_profile_mcp import service_fixture
        with tempfile.TemporaryDirectory() as temporary:
            service,backend,_,_,_=service_fixture(Path(temporary))
            async with Client(native.create_server(service),cache=None) as client:
                tools={tool.name:tool for tool in (await client.list_tools()).tools}
                expected={"ck3_open_profile_decisions_v1":{"expected_revision"},
                          "ck3_query_profile_decision_item_v1":{"decision_key","expected_revision"},
                          "ck3_select_profile_decision_item_v1":{"decision_key","expected_revision"},
                          "ck3_confirm_profile_decision_outcome_v1":{"decision_key","expected_outcome","expected_revision","expected_event_definition_key"}}
                for name,properties in expected.items():
                    schema=tools[name].input_schema
                    self.assertFalse(schema["additionalProperties"])
                    self.assertEqual(set(schema["properties"]),properties)
                    args={"expected_revision":7}
                    if "decision_key" in properties:args["decision_key"]=KEY
                    if "expected_outcome" in properties:args["expected_outcome"]="decision_closed"
                    denied=await client.call_tool(name,{**args,"pid":999,"hwnd":555})
                    self.assertTrue(denied.is_error)
                denied=await client.call_tool("ck3_confirm_profile_decision_outcome_v1",{
                    "decision_key":KEY,"expected_outcome":"decision_closed","expected_revision":7,
                    "expected_event_definition_key":EVENT_KEY})
                self.assertTrue(denied.is_error)
                denied=await client.call_tool("ck3_confirm_profile_decision_outcome_v1",{
                    "decision_key":KEY,"expected_outcome":"event_window","expected_revision":7})
                self.assertTrue(denied.is_error)
                self.assertEqual(backend.injections,[])
    async def test_sdk_has_generic_closed_args_and_keeps_vivhite_literal(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        parent=os.environ.get("XAR_DECISION_OUTCOME_TEST_ARTIFACTS")
        if parent:Path(parent).mkdir(parents=True,exist_ok=True)
        directory=Path(tempfile.mkdtemp(prefix="sdk-outcome-",dir=parent))
        driver=OutcomeDriver(directory,"decision_closed")
        async with Client(create_server(driver),cache=None) as client:
            tools={tool.name:tool for tool in (await client.list_tools()).tools}
            generic=tools["ck3_confirm_ingame_decision_outcome_v1"].input_schema
            self.assertFalse(generic["additionalProperties"])
            self.assertEqual(set(generic["properties"]),{"decision_key","expected_outcome","expected_revision","expected_event_definition_key"})
            self.assertEqual(set(generic["properties"]["expected_outcome"]["enum"]),{"event_window","decision_closed"})
            old=tools["ck3_confirm_ingame_decision_item_v1"].input_schema
            self.assertEqual(old["properties"]["expected_window_kind"]["const"],"vivhite_courtier")
            args={"decision_key":KEY,"expected_outcome":"decision_closed","expected_revision":1}
            denied=await client.call_tool("ck3_confirm_ingame_decision_outcome_v1",{**args,"receiver_address":123})
            self.assertTrue(denied.is_error);self.assertEqual(driver.submissions,[])
            denied=await client.call_tool("ck3_confirm_ingame_decision_outcome_v1",{**args,"expected_outcome":"any_widget"})
            self.assertTrue(denied.is_error);self.assertEqual(driver.submissions,[])
            accepted=await client.call_tool("ck3_confirm_ingame_decision_outcome_v1",args)
            self.assertFalse(accepted.is_error,str(accepted));self.assertEqual(len(driver.submissions),1)


if __name__=="__main__":unittest.main()
