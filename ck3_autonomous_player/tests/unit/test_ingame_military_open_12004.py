"""Fixed semantic opening waits for actual visibility and never repeats an unknown action."""
from copy import deepcopy
from pathlib import Path
import os,tempfile,unittest
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.ingame_military_open_12004 import CAPABILITY,GUI_SHA256,STEP,open_fixed_military_window_12004


class FakeDriver:
    def __init__(self,path,lost=False):self.path=path;self.lost=lost;self.calls=0;self.reads=0
    def _native_driver_state_path(self):return self.path/"driver.json"
    def capabilities(self):return {"bridge_capabilities":[CAPABILITY]}
    def take_snapshot(self):
        return {"revision":7,"native_revision":7,"date_raw":53146848,"paused":True,"map_ready":True,
          "episode_run_id":"fixture-military-only","played_character":{"alive":True,"character_id":31254},
          "diagnostics":{"connection_generation":1,"hello":{"expected_ck3_version":"1.20.0.4",
             "expected_ck3_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
             "game_adapter_id":"ck3-1.20.0.4-msvc-x64","ck3_build_match":True,"pid":7240}}}
    def _execute_primitive_step(self,step,**kw):
        assert step==STEP and kw["request_fields"]["expected_player_character_id"]==31254
        self.calls+=1
        if self.lost:raise BridgeUnavailableError("synthetic lost ACK")
        return {"schema":"ck3-ingame-military-open-12004-v1","step":STEP,"game_version":"1.20.0.4",
          "executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
          "native_revision":7,"connection_generation":1,"game_pid":7240,"played_character_id":31254,"date_raw":53146848,
          "owner_thread_verified":True,"frame_verified":True,"source_abi_pins_verified":True,
          "gui_owner_binding_verified":True,"native_after_read":True,"before_visible":False,
          "dispatch_attempted":True,"dispatch_invoked":True,"native_handled":False,"topbar_tree_complete":True,
          "receiver_qualified":True,"native_after_visible":False,"native_after_tree_complete":True,
          "postcondition_verified":False,"verification_pending":True,"source_gui_sha256":GUI_SHA256,
          "business_model_available":False,"military_refill_action_available":False}
    def inspect_gui_window_tree_v1(self,kind):
        assert kind=="military";self.reads+=1
        return {"scope_root_name":"military_view","truncated":False,"root_available":True,
                "widgets":[{"child_path":"","runtime_name":"military_view","effective_visible":self.reads>=2}]}


class IngameMilitaryOpen12004Tests(unittest.TestCase):
    def test_pending_ack_requires_later_actual_visible_root_after_exactly_one_dispatch(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("XAR_REFILL_TEST_TEMP")) as directory:
            driver=FakeDriver(Path(directory));result=open_fixed_military_window_12004(driver,expected_revision=7)
            self.assertEqual(driver.calls,1);self.assertEqual(driver.reads,2)
            self.assertTrue(result["postcondition_verified"])
            self.assertFalse(result["native_ack"]["postcondition_verified"])
            self.assertFalse(result["military_refill_action_available"])
    def test_lost_ack_claim_survives_and_second_attempt_never_dispatches(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("XAR_REFILL_TEST_TEMP")) as directory:
            driver=FakeDriver(Path(directory),lost=True)
            for _ in range(2):
                with self.assertRaises(BridgeUnavailableError):open_fixed_military_window_12004(driver,expected_revision=7)
            self.assertEqual(driver.calls,1);self.assertEqual(driver.reads,0)
            self.assertEqual(len(list(Path(directory).rglob("*.claim.json"))),1)
