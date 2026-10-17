from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import time
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.frontend_fixture_start_contract import (
    EXE_SHA256_12004, FAITH_E01_FRONTEND_TARGET, FAITH_E01_PROFILE_ID,
)


def load_harness():
    path = Path(__file__).resolve().parents[2] / "native_bridge/research/run_ck3_12002_mcp_live.py"
    spec = importlib.util.spec_from_file_location("scenario_fixture_host_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy():
    return {"schema": "ck3-frontend-fixture-start-policy-v2", "schema_version": 2,
        "profile_id": FAITH_E01_PROFILE_ID, "frontend_target": dict(FAITH_E01_FRONTEND_TARGET),
        "startup_event_admission": {"mode": "observe_only", "event_definition_key": "xar_faith_h01_prepare.1", "option_count": 2},
        "preparation": {"path": str(Path("preparation.json").resolve()), "sha256": "b" * 64},
        "post_start": {"government_key": "clan_government", "primary_title_tier_key": "empire", "independent": True},
        "required_log_markers": ["FAITH01 qualified"], "forbidden_log_markers": ["FAITH01 FAIL"]}


def submission(harness):
    target = FAITH_E01_FRONTEND_TARGET
    return {"schema": "ck3-frontend-fixture-scenario-start-submission-v1", "schema_version": 1,
        "profile_id": FAITH_E01_PROFILE_ID, "accepted": True, "status": "acknowledged_verification_pending",
        "pre_start_identity_proven": True, "postcondition_verified": False, "fixture_target_identity_proven": False,
        "requested_character_name_key": target["character_name_key"],
        "uses_ocr": False, "uses_keyboard": False, "uses_mouse": False,
        "policy_binding": harness.fixture_start_policy_binding(policy(), b"frozen actual policy"),
        "binding": {"bridge_pid": 71, "connection_generation": 2},
        "selected_candidate": {"schema": "ck3-frontend-selected-fixture-scenario-candidate-v1",
            "status": "ready", "read_only": True, "profile_id": FAITH_E01_PROFILE_ID,
            "selected_bookmark_key": target["bookmark_key"], "selected_character_name_key": target["character_name_key"],
            "selected_bookmark_group_key": target["bookmark_group_key"],
            "selected_character_government_key": target["government_key"],
            "selected_bookmark_start_date_raw": target["start_date_raw"]},
        "acknowledgement": {"step": "activate-frontend-start-selected-bookmark-faith-e01-v1",
            "accepted": True, "status": "acknowledged_verification_pending", "backend_id": "native-headless"}}


def log_counts(count):
    p = policy()
    return {"schema": "xar.ck3.engine-log-literals/v1", "log_name": "debug.log", "exists": True,
        "read_only": True, "case_sensitive": True, "matches": [
            {"literal": key, "line_count": count if key in p["required_log_markers"] else 0}
            for key in p["required_log_markers"] + p["forbidden_log_markers"]]}


def current_frame(epoch, startup=False):
    actual_actor = 123456789  # Observed full reference; never equated with history ID 34014.
    snapshot = {"map_ready": True, "paused": True, "active_event": None, "episode_projection": "native_campaign",
        "date_raw": FAITH_E01_FRONTEND_TARGET["start_date_raw"], "revision": 10, "native_revision": 4,
        "snapshot_id": "frame-10", "local_player_id": 1,
        "played_character": {"character_id": actual_actor, "alive": True, "source": "native"},
        "diagnostics": {"bridge_pid": 71, "connection_generation": 2, "connected": True,
            "hello": {"pid":71, "connection_generation":2, "game_adapter_id":"ck3-1.20.0.4-msvc-x64",
                "expected_ck3_version":"1.20.0.4", "expected_ck3_sha256":EXE_SHA256_12004, "ck3_build_match":True},
            "last_heartbeat": {"pid": 71,
            "snapshot_observer_12002": {"read_in_progress":False, "started_ms":1, "completed_ms":2},
            "main_thread_query_mailbox_v1": {"ready": True, "stamp_read_success": True,
                "pump_epochs": epoch, "owner_verified_pump_epochs": epoch, "owner_tid": 81, "current_tid": 81}}}}
    root = {"campaign_root_context_ready": True, "backend_id": "native-headless", "queried_revision": 10,
        "queried_native_revision": 4, "queried_snapshot_id": "frame-10", "date_raw": snapshot["date_raw"],
        "provenance": {"game_version": "1.20.0.4", "executable_sha256": EXE_SHA256_12004},
        "player_character_id": actual_actor, "player_character_alive": True, "government": {"key": "clan_government"},
        "primary_title": {"title_id": 503, "tier_raw": 5, "tier_key": "empire"}, "independent": True,
        "immediate_liege_character_id": None, "top_liege_character_id": actual_actor}
    if startup:
        snapshot["active_event"] = {"instance_id":917, "source":"native", "options":[
            {"option_number":1, "enabled":True, "text":"Save baseline first"},
            {"option_number":2, "enabled":True, "text":"Prepare mechanism experiment"}]}
    return snapshot, root


def event_packet(snapshot):
    return {"status":"available", "current_event_window_context_ready":True,
        "queried_snapshot_id":snapshot["snapshot_id"], "queried_revision":snapshot["revision"],
        "queried_native_revision":snapshot["native_revision"], "current_event_window_context":{
            "schema":"current-event-window-context-v1", "schema_version":1, "status":"available",
            "window_match_count":1, "current_event_instance_id":snapshot["active_event"]["instance_id"],
            "event_definition_key":"xar_faith_h01_prepare.1", "snapshot_revision":snapshot["native_revision"],
            "date_raw":snapshot["date_raw"], "provenance":{"backend_id":"ck3-1.20.0.4-native-event-window-v1"},
            "readiness": {"event_definition_identity_ready":True, "root_scope_ready":True, "option_presentation_ready":True},
            "root_scope":{"status":"available", "type_key":"character", "typed_identity":{
                "status":"available", "kind":"character", "character_id":snapshot["played_character"]["character_id"]}},
            "options":[{"rendered_index":index, "native_option_index":native, "shown":True, "enabled":True,
                "fallback":False, "cancel":False} for index,native in enumerate((2,5))]}}


class ScenarioHostBindingTests(unittest.TestCase):
    def test_observe_only_initial_plan_defaults_empty_and_rejects_actions_or_turns(self):
        harness = load_harness()
        args = SimpleNamespace(turns=0, plan=None)
        self.assertEqual(harness.observe_only_fixture_initial_plan(args), [])
        args.turns = 1
        with self.assertRaisesRegex(ValueError, "auto turns"):
            harness.observe_only_fixture_initial_plan(args)
        args.turns, args.plan = 0, Path("explicit-plan.json")
        for row in ({"tool":"ck3_select_event_option"}, {"tool":"ck3_save_checkpoint"},
                {"tool":"ck3_request_normal_exit_v1"}, {"kind":"advance_day", "days":1}):
            harness.load_plan = lambda path, row=row: [row]
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "read-only"):
                harness.observe_only_fixture_initial_plan(args)
        read = [{"tool":"ck3_take_snapshot"}, {"tool":"ck3_query_player_religion_context_v1"}]
        harness.load_plan = lambda path: read
        self.assertEqual(harness.observe_only_fixture_initial_plan(args), read)

    def test_v2_binding_preserves_hashes_and_exact_declared_target(self):
        harness = load_harness()
        result = harness.fixture_start_policy_binding(policy(), b"actual frozen bytes")
        self.assertEqual(result, {"policy_sha256": hashlib.sha256(b"actual frozen bytes").hexdigest(),
            "preparation_sha256": "b" * 64, "profile_id": FAITH_E01_PROFILE_ID,
            "frontend_target": FAITH_E01_FRONTEND_TARGET})
        result["frontend_target"]["bookmark_key"] = "mutated result"
        self.assertEqual(policy()["frontend_target"]["bookmark_key"], "bm_xar_faith_h01_867")

    def test_v1_binding_and_robert_tool_are_unchanged(self):
        harness = load_harness()
        previous = {"schema": "ck3-frontend-fixture-start-policy-v1", "preparation": {"sha256": "b" * 64}}
        self.assertEqual(harness.fixture_start_policy_binding(previous, b"legacy"),
            {"policy_sha256": hashlib.sha256(b"legacy").hexdigest(), "preparation_sha256": "b" * 64})
        self.assertEqual(harness.fixture_start_tool(previous), "ck3_submit_frontend_fixture_robert_start_v1")

    def test_v2_rejects_unapproved_profile_before_start_routing(self):
        harness = load_harness()
        for change in ("profile_id", "target"):
            value = policy()
            if change == "profile_id": value["profile_id"] = "arbitrary actor"
            else: value["frontend_target"]["character_name_key"] = "another actor"
            with self.subTest(change=change), self.assertRaises(ValueError):
                harness.fixture_start_tool(value)

    def test_v2_rejects_robert_submission_and_ack_as_postcondition_proof(self):
        harness = load_harness()
        value = submission(harness)
        value["schema"] = "ck3-frontend-fixture-robert-start-submission-v1"
        with self.assertRaises(ValueError):
            harness.require_fixture_policy_submission(value, policy())
        for field in ("postcondition_verified", "fixture_target_identity_proven"):
            value = submission(harness)
            value[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                harness.require_fixture_policy_submission(value, policy())


class ScenarioHostSubmissionTests(unittest.IsolatedAsyncioTestCase):
    async def test_v2_calls_only_scenario_tool_once_and_keeps_pending_evidence(self):
        harness, report = load_harness(), {}
        class Client:
            tools = {"ck3_submit_frontend_fixture_scenario_start_v1", "ck3_take_snapshot",
                "ck3_query_campaign_root_context_v1", "ck3_query_engine_log_literals_v1"}
            calls = []
            async def call(self, tool, args=None):
                self.calls.append(tool)
                if tool == "ck3_query_engine_log_literals_v1": return log_counts(0)
                self_state = report["frontend_fixture_start_submission"]
                if self_state["status"] != "REQUEST_WRITTEN_BEFORE_SUBMISSION":
                    raise AssertionError("Start not recorded before submission")
                return submission(harness)
        client = Client()
        result = await harness.submit_fixture_robert_once(client, policy(), report=report, write=lambda: None)
        self.assertFalse(result["postcondition_verified"])
        self.assertFalse(result["fixture_target_identity_proven"])
        self.assertEqual(client.calls, ["ck3_query_engine_log_literals_v1", "ck3_submit_frontend_fixture_scenario_start_v1"])
        with self.assertRaisesRegex(RuntimeError, "already attempted"):
            await harness.submit_fixture_robert_once(client, policy(), report=report, write=lambda: None)
        self.assertEqual(len(client.calls), 2)

    async def test_v2_lost_ack_does_not_fall_back_to_robert_or_replay(self):
        harness, report = load_harness(), {}
        class Client:
            tools = {"ck3_submit_frontend_fixture_scenario_start_v1", "ck3_submit_frontend_fixture_robert_start_v1",
                "ck3_take_snapshot", "ck3_query_campaign_root_context_v1", "ck3_query_engine_log_literals_v1"}
            starts = []
            async def call(self, tool, args=None):
                if tool == "ck3_query_engine_log_literals_v1": return log_counts(0)
                self.starts.append(tool)
                raise RuntimeError("lost ACK")
        client = Client()
        with self.assertRaisesRegex(RuntimeError, "lost ACK"):
            await harness.submit_fixture_robert_once(client, policy(), report=report, write=lambda: None)
        with self.assertRaisesRegex(RuntimeError, "already attempted"):
            await harness.submit_fixture_robert_once(client, policy(), report=report, write=lambda: None)
        self.assertEqual(client.starts, ["ck3_submit_frontend_fixture_scenario_start_v1"])
        self.assertFalse(report["frontend_fixture_start_submission"]["retry_allowed"])

    async def test_v2_wait_binds_actual_fullref_after_independent_owner_frames(self):
        harness, report = load_harness(), {}
        class Client:
            epoch = 1
            calls = []
            async def fresh(self): return current_frame(self.epoch, startup=True)[0]
            async def call(self, tool, args=None):
                self.calls.append(tool)
                if tool == "ck3_query_engine_log_literals_v1":
                    self.epoch += 1
                    return log_counts(1)
                if tool == "ck3_query_campaign_root_context_v1": return current_frame(self.epoch, startup=True)[1]
                if tool == "ck3_query_current_event_window_context_v1": return event_packet(current_frame(self.epoch, startup=True)[0])
                raise AssertionError("Post-Start must only observe")
        client = Client()
        state = await harness.wait_for_fixture_business_context(client, policy(), submission(harness), report=report,
            write=lambda: None, timeout=2, poll_interval=0)
        self.assertEqual(state["binding"]["actor_character_id"], 123456789)
        self.assertNotEqual(state["binding"]["actor_character_id"], 34014)
        self.assertEqual(state["binding"]["government_key"], "clan_government")
        self.assertGreaterEqual(len(state["observations"]), 3)
        self.assertFalse(state["fixture_target_identity_proven"])
        self.assertFalse(state["product_acceptance_proven"])
        self.assertFalse(state["startup_case"]["selection_attempted"])
        self.assertEqual(state["startup_case"]["status"], "OBSERVED_UNCHANGED_STARTUP_EVENT")
        self.assertNotIn("ck3_select_event_option", client.calls)
        report["frontend_fixture_start_policy_input"] = {"policy":policy(), "episode_projection":"native_campaign"}
        preserved = current_frame(client.epoch, startup=True)[0]
        self.assertTrue(harness.paused_map_readiness_admitted(preserved, report))
        preserved["active_event"]["instance_id"] += 1
        self.assertFalse(harness.paused_map_readiness_admitted(preserved, report))

    async def test_observe_only_rejects_wrong_definition_actor_options_and_changed_event(self):
        for fault in ("definition", "actor", "disabled", "frame", "changed_event"):
            with self.subTest(fault=fault):
                harness = load_harness()
                submitted = submission(harness)
                snapshot = current_frame(2, startup=True)[0]
                frame = harness.fixture_whole_root_admission_frame(snapshot, submitted, allow_active_event=True)
                frame.update(event_instance_id=917, owner_tid=81)
                state = {"first_startup_query_admission":{
                    "previous_frame":{**frame, "pump_epoch":1}, "current_frame":frame}}
                packet = event_packet(snapshot)
                context = packet["current_event_window_context"]
                if fault == "definition": context["event_definition_key"] = "unknown.1"
                if fault == "actor": context["root_scope"]["typed_identity"]["character_id"] = 34014
                if fault == "disabled": context["options"][1]["enabled"] = False
                if fault == "frame": context["snapshot_revision"] += 1
                class Client:
                    calls = []
                    async def call(self, tool, args=None):
                        self.calls.append(tool)
                        if tool != "ck3_query_current_event_window_context_v1":
                            raise AssertionError("Observation may not choose or advance")
                        return packet
                    async def fresh(self):
                        after = current_frame(3, startup=True)[0]
                        if fault == "changed_event": after["active_event"]["instance_id"] += 1
                        return after
                client = Client()
                with self.assertRaises(RuntimeError):
                    await harness.observe_fixture_scenario_startup_event(client, snapshot, submitted, policy(),
                        state=state, write=lambda:None, deadline=time.monotonic()+2)
                self.assertEqual(client.calls, ["ck3_query_current_event_window_context_v1"])
                self.assertFalse(state["startup_case"]["selection_attempted"])


if __name__ == "__main__":
    unittest.main()
