from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

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


def current_frame(epoch):
    actual_actor = 123456789  # Observed full reference; never equated with history ID 34014.
    snapshot = {"map_ready": True, "paused": True, "active_event": None, "episode_projection": "native_campaign",
        "date_raw": FAITH_E01_FRONTEND_TARGET["start_date_raw"], "revision": 10, "native_revision": 4,
        "snapshot_id": "frame-10", "local_player_id": 1,
        "played_character": {"character_id": actual_actor, "alive": True, "source": "native"},
        "diagnostics": {"bridge_pid": 71, "connection_generation": 2, "last_heartbeat": {"pid": 71,
            "main_thread_query_mailbox_v1": {"ready": True, "stamp_read_success": True,
                "pump_epochs": epoch, "owner_verified_pump_epochs": epoch, "owner_tid": 81, "current_tid": 81}}}}
    root = {"campaign_root_context_ready": True, "backend_id": "native-headless", "queried_revision": 10,
        "queried_native_revision": 4, "queried_snapshot_id": "frame-10", "date_raw": snapshot["date_raw"],
        "provenance": {"game_version": "1.20.0.4", "executable_sha256": EXE_SHA256_12004},
        "player_character_id": actual_actor, "player_character_alive": True, "government": {"key": "clan_government"},
        "primary_title": {"title_id": 503, "tier_raw": 5, "tier_key": "empire"}, "independent": True,
        "immediate_liege_character_id": None, "top_liege_character_id": actual_actor}
    return snapshot, root


class ScenarioHostBindingTests(unittest.TestCase):
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
            async def fresh(self): return current_frame(self.epoch)[0]
            async def call(self, tool, args=None):
                if tool == "ck3_query_engine_log_literals_v1":
                    self.epoch += 1
                    return log_counts(1)
                if tool == "ck3_query_campaign_root_context_v1": return current_frame(self.epoch)[1]
                raise AssertionError("Post-Start must only observe")
        state = await harness.wait_for_fixture_business_context(Client(), policy(), submission(harness), report=report,
            write=lambda: None, timeout=2, poll_interval=0)
        self.assertEqual(state["binding"]["actor_character_id"], 123456789)
        self.assertNotEqual(state["binding"]["actor_character_id"], 34014)
        self.assertEqual(state["binding"]["government_key"], "clan_government")
        self.assertGreaterEqual(len(state["observations"]), 3)
        self.assertFalse(state["fixture_target_identity_proven"])
        self.assertFalse(state["product_acceptance_proven"])


if __name__ == "__main__":
    unittest.main()
