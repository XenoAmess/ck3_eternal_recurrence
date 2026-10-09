from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE / "src"))
SPEC = importlib.util.spec_from_file_location("saved_startup_host_test", PACKAGE / "native_bridge/research/run_ck3_12002_mcp_live.py")
HOST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST)
SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
EXPECTED = {"actor_character_id":31254, "date_raw":37791000}
BINDING = {"bridge_pid":71, "connection_generation":2}
WANTED = {"event_definition_key":"fixture.control.20", "event_instance_id":121,
          "root_character_id":31254, **EXPECTED, "native_option_indices":[0]}
HANDLER = b'''def admit_saved_startup_event(context, snapshot, packet):
    return {**context["expected"], "proof":{"definition":packet["current_event_window_context"]["event_definition_key"]}, "business_pass":False}
'''


def snapshot(epoch=7, *, event=True):
    return {"snapshot_id":"saved-frame-3", "revision":3, "native_revision":3,
        "date_raw":EXPECTED["date_raw"], "paused":True, "map_ready":True,
        "episode_projection":"native_campaign", "local_player_id":1,
        "played_character":{"character_id":31254, "alive":True, "source":"native"},
        "active_event":{"instance_id":121, "source":"native", "options":[{"option_number":1, "enabled":True}]} if event else None,
        "diagnostics":{"connected":True, **BINDING,
            "hello":{"pid":71, "connection_generation":2, "game_adapter_id":"ck3-1.20.0.4-msvc-x64",
                "expected_ck3_version":"1.20.0.4", "expected_ck3_sha256":SHA,
                "ck3_build_match":True, "capabilities":["game.state.snapshot"]},
            "last_heartbeat":{"pid":71, "main_thread_query_mailbox_v1":{
                "ready":True, "stamp_read_success":True, "pump_epochs":epoch,
                "owner_verified_pump_epochs":epoch, "owner_tid":99, "current_tid":99},
                "snapshot_observer_12002":{"read_in_progress":False, "started_ms":100, "completed_ms":101}}}}


def packet():
    return {"status":"available", "current_event_window_context_ready":True,
        "queried_snapshot_id":"saved-frame-3", "queried_revision":3, "queried_native_revision":3,
        "current_event_window_context":{"schema":"current-event-window-context-v1", "schema_version":1,
            "status":"available", "window_match_count":1, "current_event_instance_id":121,
            "event_definition_key":WANTED["event_definition_key"], "snapshot_revision":3, "date_raw":EXPECTED["date_raw"],
            "provenance":{"backend_id":"ck3-1.20.0.4-native-event-window-v1"},
            "readiness":{"event_definition_identity_ready":True, "root_scope_ready":True, "option_presentation_ready":True},
            "root_scope":{"status":"available", "type_key":"character",
                "typed_identity":{"status":"available", "kind":"character", "character_id":31254}},
            "options":[{"rendered_index":0, "native_option_index":0, "shown":True,
                "enabled":True, "fallback":False, "cancel":False}]}}


def root():
    return {"campaign_root_context_ready":True, "backend_id":"native-headless",
        "queried_snapshot_id":"saved-frame-3", "queried_revision":3, "queried_native_revision":3,
        "date_raw":EXPECTED["date_raw"], "player_character_id":31254, "player_character_alive":True,
        "provenance":{"game_version":"1.20.0.4", "executable_sha256":SHA}}


class Client:
    def __init__(self, state_dir, *, event=True, context=None, root_value=None, after_change=None):
        self.args = SimpleNamespace(state_dir=state_dir)
        self.event = event
        self.context = context or packet()
        self.root_value = root_value or root()
        self.after_change = after_change
        self.frames = 0
        self.calls = []

    async def fresh(self):
        self.frames += 1
        value = snapshot(6+self.frames, event=self.event)
        if self.frames >= 4 and self.after_change:
            self.after_change(value)
        return value

    async def call(self, tool, args=None):
        self.calls.append((tool, copy.deepcopy(args)))
        if tool == "ck3_migration_pipe_diagnostics":
            return {"pipe":"fixture-pipe", "transport_error":None, "diagnostics":{
                "pipe_name":"fixture-pipe", "protocol_version":1, "transport_fatal_error":None,
                "last_error":None, "connected":True, "semantic_state_available":True,
                "rejected_state_snapshot_count":0, **BINDING, "hello":snapshot()["diagnostics"]["hello"]}}
        if tool == "ck3_query_campaign_root_context_v1":
            return copy.deepcopy(self.root_value)
        if tool == "ck3_query_current_event_window_context_v1":
            return copy.deepcopy(self.context)
        raise AssertionError("Saved startup admission must make observations only: " + tool)


class SavedStartupAdmissionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state = Path(self.temporary.name)
        self.handler = self.state / "startup_handler.py"
        self.contract = self.make_contract(HANDLER)

    def make_contract(self, source):
        self.handler.write_bytes(source)
        return {"schema":"ck3-saved-campaign-startup-case-contract-v1", "state_dir":str(self.state),
            "handler":{"path":str(self.handler), "bytes":len(source), "sha256":hashlib.sha256(source).hexdigest(),
                "function":"admit_saved_startup_event"}, "dependencies":[], "expected":copy.deepcopy(WANTED)}

    def report(self, *, contract=True):
        value = {"pipe":"fixture-pipe", "saved_campaign_launch":{
            "status":"ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED", "argv_admitted":True, "ck3_pid":71}}
        if contract:
            value["saved_campaign_startup_case_contract_input"] = {"contract":self.contract}
        return value

    async def wait(self, client, report):
        return await HOST.wait_for_saved_campaign(client, EXPECTED, report=report,
            write=lambda:None, timeout=1, managed_done=None, poll_interval=0)

    async def test_explicit_route_admits_actual_event_without_selection(self):
        client, report = Client(self.state), self.report()
        result = await self.wait(client, report)
        self.assertEqual([name for name,_ in client.calls], ["ck3_migration_pipe_diagnostics",
            "ck3_query_campaign_root_context_v1", "ck3_query_current_event_window_context_v1"])
        self.assertEqual(client.calls[-1][1], {"event_instance_id":121, "expected_revision":3})
        admission = result["binding"]["startup_event_admission"]
        self.assertEqual(admission["option_identities"], [{"option_number":1,"rendered_index":0,"native_option_index":0}])
        self.assertFalse(admission["selection_attempted"])
        self.assertFalse(admission["business_pass"])
        self.assertFalse(result["product_acceptance_proven"])
        self.assertEqual(report["readiness"]["active_event"]["instance_id"],121)
        self.assertFalse(report["readiness_guard"]["one_life_identity_fabricated"])
        self.assertGreater(result["first_startup_query_admission"]["current_frame"]["pump_epoch"],
                           result["first_startup_query_admission"]["previous_frame"]["pump_epoch"])

    async def test_default_saved_route_remains_event_free(self):
        self.assertIsNone(HOST.saved_campaign_admission_frame(snapshot(), EXPECTED, BINDING))
        self.assertIsNotNone(HOST.saved_campaign_admission_frame(snapshot(event=False), EXPECTED, BINDING))
        client = Client(self.state, event=False)
        result = await self.wait(client, self.report(contract=False))
        self.assertNotIn("startup_event_admission", result["binding"])
        self.assertEqual([name for name,_ in client.calls], ["ck3_migration_pipe_diagnostics", "ck3_query_campaign_root_context_v1"])

    async def test_real_current_root_binding_is_required_before_event_query(self):
        value = root(); value["player_character_id"] = 999
        client = Client(self.state, root_value=value)
        with self.assertRaisesRegex(ValueError,"living actor"):
            await self.wait(client,self.report())
        self.assertNotIn("ck3_query_current_event_window_context_v1",[name for name,_ in client.calls])

    async def test_wrong_event_root_option_or_native_frame_is_rejected(self):
        changes = [
            lambda p:p["current_event_window_context"].update(event_definition_key="another.1"),
            lambda p:p["current_event_window_context"].update(current_event_instance_id=122),
            lambda p:p["current_event_window_context"]["root_scope"]["typed_identity"].update(character_id=999),
            lambda p:p["current_event_window_context"]["options"][0].update(native_option_index=1),
            lambda p:p["current_event_window_context"]["readiness"].update(root_scope_ready=False),
            lambda p:p.update(queried_native_revision=4),
        ]
        for change in changes:
            with self.subTest(change=change):
                value=packet(); change(value); client=Client(self.state,context=value)
                with self.assertRaises(RuntimeError):
                    await self.wait(client,self.report())
                self.assertFalse(any("select" in name for name,_ in client.calls))

    async def test_event_query_and_proof_must_leave_full_native_frame_unchanged(self):
        for change in [lambda s:s["active_event"]["options"][0].update(enabled=False),
                       lambda s:s.update(date_raw=EXPECTED["date_raw"]+1),
                       lambda s:s["diagnostics"].update(bridge_pid=72)]:
            with self.subTest(change=change):
                with self.assertRaises((RuntimeError,ValueError)):
                    await self.wait(Client(self.state,after_change=change),self.report())

    async def test_bad_business_claim_or_identity_from_pinned_handler_is_rejected(self):
        for suffix in [b'proof["business_pass"] = True',b'proof["root_character_id"] = 999']:
            source = HANDLER.replace(b'return {',b'proof = {') + b'    '+suffix+b'\n    return proof\n'
            self.contract=self.make_contract(source)
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                await self.wait(Client(self.state),self.report())

    async def test_handler_pin_changed_or_state_mismatch_is_rejected(self):
        self.handler.write_bytes(HANDLER+b'\n# changed\n')
        with self.assertRaisesRegex(ValueError,"pin"):
            await self.wait(Client(self.state),self.report())
        self.contract=self.make_contract(HANDLER)
        self.contract["state_dir"]=str(self.state/"other")
        with self.assertRaisesRegex(ValueError,"actual fixture state"):
            await self.wait(Client(self.state),self.report())

    async def test_direct_event_admission_cannot_skip_two_owner_frames(self):
        client=Client(self.state)
        with self.assertRaisesRegex(RuntimeError,"two stable owner frames"):
            await HOST.admit_saved_startup_event(client,snapshot(),EXPECTED,BINDING,self.contract,
                state={},write=lambda:None,deadline=time.monotonic()+1,managed_done=None)
        self.assertEqual(client.calls,[])

    def test_cli_route_is_explicit_and_requires_saved_input(self):
        args=HOST.parser().parse_args([])
        self.assertIsNone(args.saved_campaign_startup_case_contract)
        args.saved_campaign_startup_case_contract=self.state/"contract.json"
        with self.assertRaises(SystemExit):
            HOST.validate_saved_campaign_options(args)

    def test_frontend_pure_handler_reply_remains_unchanged(self):
        source=b'def admit_saved_startup_event(context,snapshot,packet):\n    return {"event_instance_id":121,"option_number":1,"proof":{"ok":True},"business_pass":False}\n'
        contract=self.make_contract(source)
        contract.pop("expected")
        contract["schema"]="ck3-frontend-fixture-startup-case-contract-v1"
        proof=HOST.fixture_startup_case_proof(contract,snapshot(),packet(),self.state)
        self.assertEqual(proof["option_number"],1)
        self.assertFalse(proof["business_pass"])

    def test_actual_campaign_root_service_allows_a_paused_active_event(self):
        from ck3_autonomous_player.tests.unit import test_campaign_root_context_v1_bridge as fixture
        from xar_autoplayer.bridge.service import GameplayBridgeService
        class ActiveEventDriver(fixture._ServiceDriver):
            def take_snapshot(self):
                value=super().take_snapshot()
                value["active_event"]=snapshot()["active_event"]
                return value
        driver=ActiveEventDriver()
        result=GameplayBridgeService(driver).query_campaign_root_context_v1(expected_revision=fixture.PUBLIC_REVISION)
        self.assertTrue(result["campaign_root_context_ready"])
        self.assertEqual(result["queried_revision"],fixture.PUBLIC_REVISION)


if __name__ == "__main__":
    unittest.main()
