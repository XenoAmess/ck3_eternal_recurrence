from __future__ import annotations

import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.frontend_fixture_start_contract import (
    EXE_SHA256, ROBERT_KEY, fixture_business_context_binding,
    load_bound_fixture_start_policy, require_fixture_frontend_build,
    require_fixture_start_submission, validate_fixture_start_policy,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.driver import BridgeUnavailableError, DevelopmentReportDriver
from xar_autoplayer.bridge import campaign_root_context_contract as campaign


def selected() -> dict:
    return {"schema": "ck3-frontend-selected-1066-feudal-candidate-v1", "status": "ready",
            "read_only": True, "selected_bookmark_key": "bm_1066_rags_to_riches",
            "selected_bookmark_group_key": "bm_group_1066", "selected_character_name_key": ROBERT_KEY,
            "selected_character_government_key": "feudal_government", "selected_bookmark_start_date_raw": 37791000}


def submission() -> dict:
    return {"schema": "ck3-frontend-fixture-robert-start-submission-v1", "schema_version": 1,
            "accepted": True, "status": "acknowledged_verification_pending", "pre_start_identity_proven": True,
            "postcondition_verified": False, "fixture_target_identity_proven": False,
            "requested_character_name_key": ROBERT_KEY, "uses_ocr": False, "uses_keyboard": False,
            "uses_mouse": False, "selected_candidate": selected(), "binding": {"bridge_pid": 71, "connection_generation": 2},
            "acknowledgement": {"step": "activate-frontend-start-selected-bookmark-v1", "accepted": True,
                                "status": "acknowledged_verification_pending", "backend_id": "native-headless"}}


def capabilities() -> dict:
    capability = "game.command.query-frontend-gui-route-v1"
    return {"backend_id": "native-headless", "mode": "native-headless", "source": "injected-dll-named-pipe",
            "visual_fallback": False, "bridge_capabilities": [capability],
            "diagnostics": {"connected": True, "bridge_pid": 71, "connection_generation": 2,
                "hello": {"pid": 71, "connection_generation": 2, "game_adapter_id": "ck3-1.20.0.3-msvc-x64",
                    "expected_ck3_version": "1.20.0.3", "expected_ck3_sha256": EXE_SHA256,
                    "game_adapter_status": "ready", "ck3_build_match": True, "capabilities": [capability]}}}


def policy() -> dict:
    return {"schema": "ck3-frontend-fixture-start-policy-v1", "schema_version": 1,
            "preparation": {"path": str(Path("preparation.json").resolve()), "sha256": "a" * 64},
            "profile_input_sha256": {"dlc_load.json": "a" * 64, "pdx_settings.txt": "b" * 64, "mod/fixture.mod": "c" * 64},
            "post_start": {"government_key": "celestial_government", "primary_title_tier_key": "hegemony", "independent": True},
            "required_log_markers": ["FIXTURE: qualified", "FIXTURE: switched"], "forbidden_log_markers": ["FIXTURE: FAIL"]}


def current(actor: int = 922, epoch: int = 7) -> tuple[dict, dict]:
    snapshot = {"map_ready": True, "paused": True, "episode_projection": "native_campaign", "date_raw": 37791000,
                "revision": 10, "native_revision": 4, "snapshot_id": "frame-10", "played_character": {"character_id": actor},
                "diagnostics": {"bridge_pid": 71, "connection_generation": 2,
                    "last_heartbeat": {"main_thread_query_mailbox_v1": {"pump_epochs": epoch}}}}
    root = {"campaign_root_context_ready": True, "backend_id": "native-headless", "queried_revision": 10,
            "queried_native_revision": 4, "queried_snapshot_id": "frame-10", "date_raw": 37791000,
            "provenance": {"game_version": "1.20.0.3", "executable_sha256": EXE_SHA256},
            "player_character_id": actor, "player_character_alive": True, "government": {"key": "celestial_government"},
            "primary_title": {"title_id": 503, "tier_raw": 6, "tier_key": "hegemony"}, "independent": True,
            "immediate_liege_character_id": None, "top_liege_character_id": actor}
    return snapshot, root


def fake_driver(directory: Path, *, needs_selection: bool = True, fail_step: str | None = None):
    driver = object.__new__(NativeHeadlessGameplayDriver)
    driver.episode_projection = "native_campaign"
    driver.frontend_fixture_start_policy_binding = {"policy_sha256": "a" * 64, "preparation_sha256": "b" * 64}
    driver.state_dir = directory
    driver._driver_state_lock = threading.RLock()
    driver.frontend_transition_timeout_seconds = 0.1
    driver.capabilities = capabilities
    driver.query_frontend_gui_route_v1 = lambda: {"route": "bookmarks"}
    driver.query_frontend_selected_1066_feudal_candidate_v1 = lambda **kwargs: selected()
    driver.take_snapshot = lambda: (_ for _ in ()).throw(AssertionError("must not invoke ordinary post-policy"))
    calls = []
    def execute(step, **kwargs):
        calls.append(step)
        if step == "probe-frontend-bookmark-model-v1":
            return {"candidate_identity_ready": True, "candidate_keys": ["other", ROBERT_KEY],
                    "supported_1066_candidate_index": 1, "selected_character_index": 0 if needs_selection else 1}
        records = [json.loads(row) for row in (directory / "frontend-fixture-start-requests.jsonl").read_text().splitlines()]
        before = "before-native-start-request" if step == "activate-frontend-start-selected-bookmark-v1" else "before-native-selection-request"
        if records[-1]["phase"] != before:
            raise AssertionError("native mutation was not durably recorded first")
        if step == fail_step:
            raise BridgeUnavailableError("lost ACK after possible native execution")
        return {"step": step, "accepted": True, "status": "acknowledged_verification_pending", "backend_id": "native-headless"}
    driver._execute_primitive_step = execute
    return driver, calls


class FixtureSubmissionTests(unittest.TestCase):
    def test_frontend_reconnect_after_model_query_rejects_before_any_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, calls = fake_driver(Path(directory))
            old = capabilities()
            new = copy.deepcopy(old)
            new["diagnostics"]["connection_generation"] = 3
            new["diagnostics"]["hello"]["connection_generation"] = 3
            responses = iter([old, new])
            driver.capabilities = lambda: next(responses)
            with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
                driver.submit_frontend_fixture_robert_start_v1()
            self.assertEqual(calls, ["probe-frontend-bookmark-model-v1"])

    def test_actual_selected_government_is_rechecked_before_start_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, calls = fake_driver(Path(directory), needs_selection=False)
            bad = selected()
            bad["selected_character_government_key"] = "celestial_government"
            driver.query_frontend_selected_1066_feudal_candidate_v1 = lambda **kwargs: bad
            with self.assertRaises(ValueError):
                driver.submit_frontend_fixture_robert_start_v1()
            self.assertEqual(calls, ["probe-frontend-bookmark-model-v1"])

    def test_wrong_actual_native_candidate_key_stops_before_selection_and_start(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, calls = fake_driver(Path(directory))
            original = driver._execute_primitive_step
            def wrong_model(step, **kwargs):
                value = original(step, **kwargs)
                value["candidate_keys"][1] = "bookmark_rags_to_riches_petty_king_murchad"
                return value
            driver._execute_primitive_step = wrong_model
            with self.assertRaises(BridgeUnavailableError):
                driver.submit_frontend_fixture_robert_start_v1()
            self.assertEqual(calls, ["probe-frontend-bookmark-model-v1"])

    def test_submission_receipt_rejects_ack_as_verified_or_fixture_target_proof(self):
        for field in ("postcondition_verified", "fixture_target_identity_proven"):
            value = submission()
            value[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                require_fixture_start_submission(value)

    def test_actual_driver_selects_robert_once_then_returns_pending_without_map_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, calls = fake_driver(Path(directory))
            result = driver.submit_frontend_fixture_robert_start_v1()
            self.assertEqual(calls, ["probe-frontend-bookmark-model-v1", "select-frontend-supported-1066-character-v1",
                                     "activate-frontend-start-selected-bookmark-v1"])
            self.assertFalse(result["postcondition_verified"])
            self.assertFalse(result["fixture_target_identity_proven"])
            with self.assertRaises(BridgeUnavailableError):
                driver.submit_frontend_fixture_robert_start_v1()
            self.assertEqual(len(calls), 3)

    def test_actual_driver_does_not_reselect_already_proven_robert(self):
        with tempfile.TemporaryDirectory() as directory:
            driver, calls = fake_driver(Path(directory), needs_selection=False)
            self.assertIsNone(driver.submit_frontend_fixture_robert_start_v1()["selection_acknowledgement"])
            self.assertEqual(len(calls), 2)

    def test_lost_selection_and_start_ack_refuse_same_and_reconnected_driver(self):
        for step in ("select-frontend-supported-1066-character-v1", "activate-frontend-start-selected-bookmark-v1"):
            with self.subTest(step=step), tempfile.TemporaryDirectory() as directory:
                driver, calls = fake_driver(Path(directory), fail_step=step)
                with self.assertRaises(BridgeUnavailableError):
                    driver.submit_frontend_fixture_robert_start_v1()
                before = list(calls)
                with self.assertRaises(BridgeUnavailableError):
                    driver.submit_frontend_fixture_robert_start_v1()
                self.assertEqual(calls, before)
                replacement, replacement_calls = fake_driver(Path(directory))
                with self.assertRaises(FileExistsError):
                    replacement.submit_frontend_fixture_robert_start_v1()
                self.assertEqual(replacement_calls, [])

    def test_no_explicit_policy_or_wrong_projection_reject_before_native_request(self):
        for bad in ("projection", "policy", "build"):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as directory:
                driver, calls = fake_driver(Path(directory))
                if bad == "projection":
                    driver.episode_projection = "one_life"
                elif bad == "policy":
                    driver.frontend_fixture_start_policy_binding = None
                else:
                    caps = capabilities()
                    caps["diagnostics"]["hello"]["expected_ck3_sha256"] = "0" * 64
                    driver.capabilities = lambda: caps
                with self.assertRaises((BridgeUnavailableError, ValueError)):
                    driver.submit_frontend_fixture_robert_start_v1()
                self.assertEqual(calls, [])

    def test_native_campaign_projection_keeps_actual_changed_actor_without_one_life_binding(self):
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.episode_projection = "native_campaign"
        driver._bind_episode_from_playable_snapshot = lambda *a, **k: (_ for _ in ()).throw(AssertionError("stock identity must not bind"))
        for actor in (311, 922):
            projected = driver._with_one_life_episode({"played_character": {"character_id": actor}, "map_ready": True})
            self.assertEqual(projected["played_character"]["character_id"], actor)
            self.assertEqual(projected["episode_projection"], "native_campaign")
            self.assertNotIn("episode_run_id", projected)


class FixturePolicyTests(unittest.TestCase):
    def test_policy_uses_actual_fixed_log_query_bounds_before_launch(self):
        for bad in ("length", "count"):
            value = policy()
            if bad == "length":
                value["required_log_markers"] = ["x" * 161]
            else:
                value["required_log_markers"] = [str(i) for i in range(16)]
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_fixture_start_policy(value)

    def make_bound_policy(self, directory: Path):
        profile = directory / "profile"
        inputs = {"dlc_load.json": b'{"enabled_mods":["mod/fixture.mod"]}', "pdx_settings.txt": b"settings",
                  "mod/fixture.mod": b'path="mod-content/fixture"', "mod-content/fixture/effect.txt": b"fixture effect"}
        for relative, raw in inputs.items():
            target = profile / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        preparation = directory / "preparation.json"
        preparation.write_bytes(b"exact preparation bytes")
        value = policy()
        value["preparation"] = {"path": str(preparation), "sha256": hashlib.sha256(preparation.read_bytes()).hexdigest()}
        value["profile_input_sha256"] = {relative: hashlib.sha256(raw).hexdigest() for relative, raw in inputs.items()}
        path = directory / "policy.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path, profile, value

    def test_bound_actual_preparation_configs_and_inventory_then_reject_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path, profile, value = self.make_bound_policy(Path(directory))
            self.assertEqual(load_bound_fixture_start_policy(path, profile)[0], value)
            (profile / "pdx_settings.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "bytes changed"):
                load_bound_fixture_start_policy(path, profile)

    def test_bound_empire_governments_require_matching_actual_business_context(self):
        for government_key in ("administrative_government", "meritocratic_government"):
            with self.subTest(government_key=government_key), tempfile.TemporaryDirectory() as directory:
                path, profile, value = self.make_bound_policy(Path(directory))
                value["post_start"] = {
                    "government_key": government_key, "primary_title_tier_key": "empire", "independent": True,
                }
                path.write_text(json.dumps(value), encoding="utf-8")
                bound, _ = load_bound_fixture_start_policy(path, profile)
                snapshot, root = current()
                root["government"]["key"] = government_key
                root["primary_title"].update(tier_raw=5, tier_key="empire")
                binding = fixture_business_context_binding(snapshot, root, bound, submission())
                self.assertEqual(binding["actor_character_id"], 922)
                self.assertEqual(binding["government_key"], government_key)
                self.assertFalse(binding["fixture_target_identity_proven"])
                root["government"]["key"] = "feudal_government"
                self.assertIsNone(fixture_business_context_binding(snapshot, root, bound, submission()))

    def test_extra_mounted_file_and_stale_log_each_reject_cold_profile(self):
        for bad in ("extra", "log", "preparation"):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as directory:
                path, profile, value = self.make_bound_policy(Path(directory))
                if bad == "extra":
                    (profile / "mod-content/fixture/extra.txt").write_bytes(b"extra")
                elif bad == "log":
                    (profile / "logs").mkdir()
                    (profile / "logs/debug.log").write_text("old fixture qualification")
                else:
                    Path(value["preparation"]["path"]).write_bytes(b"changed preparation")
                with self.assertRaises(ValueError):
                    load_bound_fixture_start_policy(path, profile)

    def test_closed_policy_rejects_guessed_native_actor_path_escape_and_unknown_fields(self):
        for field, value in (("native_actor_id", 29829), ("target_title_key", "h_china"), ("extra", True)):
            broken = policy()
            broken[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_fixture_start_policy(broken)
        broken = policy()
        broken["profile_input_sha256"]["../escape"] = "d" * 64
        with self.assertRaises(ValueError):
            validate_fixture_start_policy(broken)

    def test_duplicate_json_fields_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            path, profile, _ = self.make_bound_policy(Path(directory))
            path.write_text('{"schema":1,"schema":2}')
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_bound_fixture_start_policy(path, profile)


class FixtureBusinessContextTests(unittest.TestCase):
    def test_exact_actual_celestial_actor_bound_without_script_target_credit(self):
        snapshot, root = current()
        value = fixture_business_context_binding(snapshot, root, policy(), submission())
        self.assertEqual(value["actor_character_id"], 922)
        self.assertEqual(value["primary_title_id"], 503)
        self.assertFalse(value["fixture_target_identity_proven"])
        root["government"]["key"] = "feudal_government"
        self.assertIsNone(fixture_business_context_binding(snapshot, root, policy(), submission()))

    def test_identity_process_revision_date_projection_and_tier_inconsistency_fail(self):
        for bad in ("actor", "pid", "revision", "date", "projection", "tier", "alive", "pump"):
            snapshot, root = current()
            if bad == "actor": root["player_character_id"] = 999
            if bad == "pid": snapshot["diagnostics"]["bridge_pid"] = 72
            if bad == "revision": root["queried_revision"] = 11
            if bad == "date": snapshot["date_raw"] += 1
            if bad == "projection": snapshot["episode_projection"] = "one_life"
            if bad == "tier": root["primary_title"]["tier_raw"] = 5
            if bad == "alive": root["player_character_alive"] = False
            if bad == "pump": snapshot["diagnostics"]["last_heartbeat"] = {}
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                fixture_business_context_binding(snapshot, root, policy(), submission())

    def test_existing_exact_build_campaign_normalizer_admits_actual_celestial_baseline(self):
        frame = {"schema_version": 1, "status": "available", "snapshot_revision": 4, "date_raw": 37791000,
                 "local_player_id": 0, "player_character_id": 922, "player_character_alive": True,
                 "primary_title": {"title_id": 503, "tier_raw": 6, "tier_key": "hegemony"}, "capital_province_id": 81,
                 "immediate_liege_character_id": None, "top_liege_character_id": 922, "independent": True,
                 "government": {"key": "celestial_government", "flags": ["government_is_celestial"], "native_flag_count": 1},
                 "selected_game_rule_tokens": [], "native_selected_game_rule_token_count": 0,
                 "readiness": {key: True for key in campaign._BASELINE_12002_READINESS}, "unavailable_reason": None,
                 "provenance": copy.deepcopy(campaign._BASELINE_PROVENANCE_BY_BUILD["1.20.0.3"])}
        normalized = campaign.normalize_campaign_root_context_v1(frame, expected_date_raw=37791000, expected_snapshot_revision=4)
        self.assertTrue(normalized["readiness"]["ready"])
        self.assertEqual(normalized["government"]["key"], "celestial_government")


def load_harness():
    path = Path(__file__).resolve().parents[2] / "native_bridge/research/run_ck3_12002_mcp_live.py"
    spec = importlib.util.spec_from_file_location("fixture_start_test_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def log_counts(value):
    p = policy()
    return {"schema": "xar.ck3.engine-log-literals/v1", "log_name": "debug.log", "exists": True,
            "read_only": True, "case_sensitive": True, "matches": [
                {"literal": literal, "line_count": value if literal in p["required_log_markers"] else 0}
                for literal in p["required_log_markers"] + p["forbidden_log_markers"]]}


class FixtureHarnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_single_submission_ack_loss_is_recorded_and_never_replayed(self):
        harness, report = load_harness(), {}
        class Client:
            tools = {"ck3_submit_frontend_fixture_robert_start_v1", "ck3_take_snapshot", "ck3_query_campaign_root_context_v1", "ck3_query_engine_log_literals_v1"}
            starts = 0
            async def call(self, tool, *args):
                if tool == "ck3_query_engine_log_literals_v1": return log_counts(0)
                self.starts += 1
                raise RuntimeError("lost ACK")
        client = Client()
        with self.assertRaises(RuntimeError):
            await harness.submit_fixture_robert_once(client, policy(), report=report, write=lambda: None)
        with self.assertRaises(RuntimeError):
            await harness.submit_fixture_robert_once(client, policy(), report=report, write=lambda: None)
        self.assertEqual(client.starts, 1)
        self.assertFalse(report["frontend_fixture_start_submission"]["retry_allowed"])

    async def test_actual_actor_switch_waits_for_two_qualified_later_pump_observations(self):
        harness, report = load_harness(), {}
        class Client:
            index = 0
            starts = 0
            async def fresh(self):
                actor = 311 if self.index < 2 else 922
                return current(actor, 7 + self.index // 2)[0]
            async def call(self, tool, args=None):
                if tool == "ck3_query_campaign_root_context_v1":
                    actor = 311 if self.index < 2 else 922
                    root = current(actor, 7 + self.index // 2)[1]
                    if actor == 311: root["government"]["key"] = "feudal_government"
                    self.index += 1
                    return root
                if tool == "ck3_query_engine_log_literals_v1":
                    self.index += 1
                    return log_counts(1 if self.index > 2 else 0)
                raise AssertionError("post-Start must be read-only")
        state = await harness.wait_for_fixture_business_context(Client(), policy(), submission(), report=report,
            write=lambda: None, timeout=2, poll_interval=0)
        self.assertEqual(state["binding"]["actor_character_id"], 922)
        self.assertGreaterEqual(len(state["observations"]), 3)
        self.assertFalse(state["product_acceptance_proven"])
        self.assertFalse(state["fixture_target_identity_proven"])

    async def test_forbidden_marker_halts_without_start_retry(self):
        harness = load_harness()
        class Client:
            async def fresh(self): return current()[0]
            async def call(self, tool, args=None):
                if tool == "ck3_query_campaign_root_context_v1": return current()[1]
                value = log_counts(1)
                value["matches"][-1]["line_count"] = 1
                return value
        report = {}
        with self.assertRaisesRegex(RuntimeError, "forbidden"):
            await harness.wait_for_fixture_business_context(Client(), policy(), submission(), report=report,
                write=lambda: None, timeout=2, poll_interval=0)
        self.assertFalse(report["frontend_fixture_business_context"]["start_resubmitted"])


class FixtureMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_sdk_conditional_closed_tool_and_default_tool_list_unchanged(self):
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server
        with tempfile.TemporaryDirectory() as directory:
            default = DevelopmentReportDriver(Path(directory))
            async with Client(create_server(default)) as client:
                ordinary_names = {tool.name for tool in (await client.list_tools()).tools}
            self.assertNotIn("ck3_submit_frontend_fixture_robert_start_v1", ordinary_names)
            bound = DevelopmentReportDriver(Path(directory))
            bound.frontend_fixture_start_policy_binding = {"policy_sha256": "a" * 64}
            called = []
            bound.submit_frontend_fixture_robert_start_v1 = lambda: (called.append(1) or submission())
            async with Client(create_server(bound)) as client:
                listed = {tool.name: tool for tool in (await client.list_tools()).tools}
                self.assertEqual(set(listed) - ordinary_names, {"ck3_submit_frontend_fixture_robert_start_v1"})
                tool = listed["ck3_submit_frontend_fixture_robert_start_v1"]
                self.assertFalse(tool.annotations.idempotent_hint)
                self.assertFalse(tool.annotations.read_only_hint)
                self.assertEqual(tool.input_schema["properties"], {})
                self.assertFalse(tool.input_schema["additionalProperties"])
                rejected = await client.call_tool(tool.name, {"native_actor_id": 922})
                self.assertTrue(rejected.is_error)
                self.assertEqual(called, [])
                actual = await client.call_tool(tool.name, {})
                self.assertFalse(actual.is_error)
                self.assertFalse(actual.structured_content["postcondition_verified"])
                self.assertEqual(called, [1])


if __name__ == "__main__":
    unittest.main()
