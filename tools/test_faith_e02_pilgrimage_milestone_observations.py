"""Typed JSON boundary and persistence consumers; authored data, no live credit."""
from __future__ import annotations

from copy import deepcopy
import json
import math
import os
from pathlib import Path
import tempfile
import unittest

from tools.ck3_mod_acceptance_cases import faith_e02_pilgrimage_observations as m
from tools.ck3_mod_acceptance_cases import faith_e02_pilgrimage_adapter as adapter
from tools.ck3_mod_acceptance_cases import faith_e02_pilgrimage_journey as journey


def binding() -> m.MilestoneBinding:
    return {"run_id": "test-run", "machine_id": "test-machine", "actor_character_id": 1,
        "bridge_pid": 2, "connection_generation": 3, "episode_run_id": None}


def frame(revision: int = 1) -> m.JSONObject:
    return {"date_raw": 10, "revision": revision, "native_revision": 1, "episode_run_id": None,
        "played_character_piety": {"raw": 0, "scale": 100000}, "paused": True, "map_ready": True,
        "source": "injected-dll-named-pipe", "backend_id": "native-headless",
        "played_character": {"character_id": 1, "alive": True, "source": "native"},
        "diagnostics": {"bridge_pid": 2, "connection_generation": 3, "hello": {
            "pid": 2, "connection_generation": 3, "ck3_build_match": True,
            "game_adapter_id": "ck3-1.20.0.4-msvc-x64"}}}


def query(revision: int = 1) -> m.JSONObject:
    return {"schema": "authored-context", "read_only": True, "available": True,
        "date_raw": 10, "query_date_raw": 10, "played_character_id": 1, "capture_epoch": 1,
        "snapshot_revision": 1, "queried_revision": revision, "raw_scale": 100000,
        "spiritual_fulfillment_raw": 0, "rite_id": 0, "faith_id": 13, "faith_main_rite_id": 0,
        "player_piety_devotion_profile": {"available": True, "capture_epoch": 1,
            "date_raw": 10, "played_character_id": 1, "raw_scale": 100000,
            "current_devotion_total_raw": 0, "effective_level": 0},
        "player_spiritual_fulfillment_progress": {"available": True, "capture_epoch": 1,
            "date_raw": 10, "played_character_id": 1, "raw_scale": 100000,
            "current_fulfillment_raw": 0, "active_level_index": 0}}


class Client:
    def __init__(self, output: Path) -> None:
        self.output = output
        self.public_requests_used = 0
        self.public_requests_cap = 1024
        self.revision = 1
        self.query_count = 0

    def remaining(self) -> float:
        return 1000.0

    def guard(self, reserve: int) -> None:
        assert reserve == 120

    def snapshot(self, *, require_event_free: bool) -> object:
        assert require_event_free is False
        self.public_requests_used += 1
        return frame(self.revision)

    def execute_plan(self, steps: list[m.MilestoneReadStep], name: str) -> object:
        assert len(steps) == 1 and steps[0]["tool"] == m.RELIGION
        assert steps[0]["args"]["expected_revision"] == self.revision
        self.public_requests_used += 1
        self.query_count += 1
        value = query(self.revision)
        self.revision += 1
        rows: list[m.JSONValue] = [{"ok": True, "result": value, "after_snapshot": frame(self.revision)}]
        (self.output / (name + ".actual-results.json")).write_text(json.dumps(rows), encoding="utf-8")
        return rows

    def checkpoint(self, name: str, value: object) -> Path:
        path = self.output / (name + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        return path


class TypedMilestoneConsumers(unittest.TestCase):
    def test_real_journey_producer_preserves_more_than_eight_key_milestones_and_terminal(self) -> None:
        class EventClient(Client):
            active_instance: int | None = None

            def snapshot(self, *, require_event_free: bool) -> object:
                current = super().snapshot(require_event_free=require_event_free)
                assert isinstance(current, dict)
                current["active_event"] = (None if self.active_instance is None else
                                            {"instance_id": self.active_instance})
                return current

        configured = os.environ.get("P3_MILESTONE_TEST_TMP")
        parent = Path(configured) if configured else None
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            concrete = EventClient(Path(directory))
            controller = journey._Journey.__new__(journey._Journey)
            controller.context = {"run_id": "test-run", "case_contract": {
                "machine_id": "test-machine", "policy": {"quit_reserve_seconds": 120}}}
            controller.client = concrete
            controller.binding = binding()
            controller.prefix = "actual-hajj-producer-"
            controller.last_frame = frame()
            controller.result = {"milestone_observations": []}

            def accept(value: object, previous: object, *, same_date: bool) -> object:
                self.assertTrue(same_date)
                return value

            controller.frame = accept
            for instance, key in enumerate(sorted(journey.KEY_EVENTS), start=1):
                typed: m.JSONObject = {"schema": "current-event-window-context-v1", "status": "available",
                    "event_definition_key": key, "current_event_instance_id": instance,
                    "root_scope": {"status": "available", "raw_type_index": 4, "type_key": "character",
                        "typed_identity": {"status": "available", "kind": "character", "character_id": 1}}}
                concrete.active_instance = instance
                self.assertIsNotNone(controller.observe_milestone(key + "-" + str(instance) + "-window", event=typed))
                concrete.active_instance = None
                self.assertIsNotNone(controller.observe_milestone(key + "-" + str(instance) + "-consumed", event=typed))
            self.assertIsNotNone(controller.observe_milestone("terminal-91", identity={
                "activity_id": 91, "host_character_id": 1, "terminal_flags_observed": True,
                "native_completed": True, "native_invalidated": False}))
            rows = controller.result["milestone_observations"]
            self.assertEqual(len(rows), 21)
            self.assertTrue(all(row["status"] == "observed" for row in rows))
            self.assertTrue(rows[-1]["milestone"].endswith("terminal-91"))
            self.assertEqual(concrete.public_requests_used, 42)
            self.assertEqual(concrete.query_count, 21)
            for row in rows:
                persisted = json.loads(Path(row["evidence"]["path"]).read_text(encoding="utf-8"))
                self.assertEqual(persisted["status"], "observed")

    def test_repeated_windows_leave_one_bounded_slot_for_actual_terminal_identity(self) -> None:
        configured = os.environ.get("P3_MILESTONE_TEST_TMP")
        parent = Path(configured) if configured else None
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            concrete = Client(Path(directory))
            context: m.JSONObject = {"run_id": "test-run", "case_contract": {
                "machine_id": "test-machine", "policy": {"quit_reserve_seconds": 120}}}
            rows: list[m.MilestoneObservation] = []
            for index in range(30):
                m.observe_milestone(context, concrete, binding(), rows, "repeated-" + str(index))
            self.assertEqual(len(rows), 23)
            fake_terminal: m.JSONObject = {"activity_id": 91, "host_character_id": 1,
                "terminal_flags_observed": True, "native_completed": 1, "native_invalidated": False}
            self.assertEqual(m.observe_milestone(context, concrete, binding(), rows,
                "wrong-terminal", identity=fake_terminal), (None, None))
            self.assertEqual(concrete.public_requests_used, 46)
            terminal: m.JSONObject = {**fake_terminal, "native_completed": True}
            observed, latest = m.observe_milestone(context, concrete, binding(), rows,
                "terminal-91", identity=terminal)
            assert observed is not None and latest is not None
            self.assertEqual(observed["status"], "observed")
            self.assertEqual(len(rows), 24)
            self.assertEqual(concrete.public_requests_used, 48)
            self.assertEqual(m.observe_milestone(context, concrete, binding(), rows,
                "second-terminal", identity=terminal), (None, None))

    def test_four_trait_observation_reaches_filming_and_preserves_json(self) -> None:
        from ck3_autonomous_player.tests.unit.test_player_pilgrimage_traits import observation
        value = query()
        value.update(schema="ck3_12004_religion_context_v1", capture_epoch=2**53 + 1)
        value["player_pilgrimage_traits"] = m.json_value(observation())
        metrics = m.project_observation(binding(), frame(), value, frame(2))
        self.assertTrue(metrics["trait_experience"]["observed"])
        self.assertEqual(metrics["trait_experience"]["raw"], value["player_pilgrimage_traits"])
        self.assertEqual(m.json_value(json.loads(json.dumps(metrics))), m.json_value(metrics))
        raw = value["player_pilgrimage_traits"]
        assert isinstance(raw, dict)
        raw["played_character_id"] = True
        invalid = m.project_observation(binding(), frame(), value, frame(2))
        self.assertTrue(invalid["source_frame_bound"])
        self.assertFalse(invalid["trait_experience"]["observed"])
        self.assertEqual(invalid["trait_experience"]["unknown_reason"], "native_trait_observation_invalid")
        value["player_pilgrimage_traits"] = None
        null = m.project_observation(binding(), frame(), value, frame(2))
        self.assertEqual(null["field_presence"]["player_pilgrimage_traits"], "null")
        self.assertFalse(null["trait_experience"]["observed"])
        del value["player_pilgrimage_traits"]
        absent = m.project_observation(binding(), frame(), value, frame(2))
        self.assertEqual(absent["field_presence"]["player_pilgrimage_traits"], "missing")

    def test_actual_adapter_sibling_loader_imports_and_projects_typed_model(self) -> None:
        loaded = adapter.sibling(Path(m.__file__), "_test_actual_p3_milestone_sibling")
        metrics = loaded.project_observation(binding(), frame(), query(), frame(2))
        self.assertTrue(metrics["source_frame_bound"])
        self.assertTrue(metrics["piety"]["observed"])
        self.assertEqual(m.json_value(json.loads(json.dumps(metrics))), m.json_value(metrics))

    def test_actual_journey_loader_calls_collector_with_typed_model(self) -> None:
        configured = os.environ.get("P3_MILESTONE_TEST_TMP")
        parent = Path(configured) if configured else None
        if parent is not None:
            parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            controller = journey._Journey.__new__(journey._Journey)
            concrete = Client(Path(directory))
            controller.context = {"run_id": "test-run", "case_contract": {
                "machine_id": "test-machine", "policy": {"quit_reserve_seconds": 120}}}
            controller.client = concrete
            controller.binding = binding()
            controller.prefix = "actual-loader-"
            controller.last_frame = frame()
            controller.result = {"milestone_observations": []}

            def accept(value: object, previous: object, *, same_date: bool) -> object:
                self.assertTrue(same_date)
                return value

            controller.frame = accept
            latest = controller.observe_milestone("before-start")
            self.assertIsNotNone(latest)
            self.assertEqual(concrete.public_requests_used, 2)
            self.assertEqual(len(controller.result["milestone_observations"]), 1)

    def test_exact_integer_identity_revision_and_raw_reject_bool(self) -> None:
        for key in ("actor_character_id", "bridge_pid", "connection_generation"):
            bad: dict[str, object] = dict(binding())
            bad[key] = True
            with self.assertRaises(ValueError):
                m.parse_binding(bad)
        for key in ("snapshot_revision", "queried_revision", "date_raw", "capture_epoch", "spiritual_fulfillment_raw"):
            value = query()
            value[key] = True
            self.assertFalse(m.project_observation(binding(), frame(), value, frame(2))["source_frame_bound"])
        bad_frame = frame()
        bad_frame["played_character_piety"] = {"raw": False, "scale": 100000}
        self.assertFalse(m.project_observation(binding(), bad_frame, query(), frame(2))["piety"]["observed"])

    def test_missing_null_zero_and_empty_are_distinct_after_roundtrip(self) -> None:
        value = query()
        metrics = m.project_observation(binding(), frame(), value, frame(2))
        self.assertTrue(metrics["devotion_observed"])
        self.assertTrue(metrics["fulfillment_observed"])
        self.assertEqual(metrics["field_presence"]["spiritual_fulfillment_raw"], "value")
        raw = metrics["piety"]["before"]
        assert raw is not None
        self.assertEqual(raw["raw"], 0)
        self.assertIs(type(raw["raw"]), int)
        value["player_piety_devotion_profile"] = None
        del value["player_spiritual_fulfillment_progress"]
        value["spiritual_fulfillment_raw"] = None
        metrics = m.project_observation(binding(), frame(), value, frame(2))
        self.assertEqual(metrics["field_presence"]["player_piety_devotion_profile"], "null")
        self.assertEqual(metrics["field_presence"]["player_spiritual_fulfillment_progress"], "missing")
        self.assertEqual(metrics["field_presence"]["spiritual_fulfillment_raw"], "null")
        self.assertFalse(metrics["devotion_observed"])
        self.assertFalse(metrics["fulfillment_observed"])
        self.assertEqual(m.json_value(json.loads(json.dumps(metrics))), m.json_value(metrics))
        self.assertNotEqual(m.json_value({"field": []}), m.json_value({"field": None}))
        self.assertNotEqual(m.json_value({}), m.json_value({"field": None}))

    def test_malformed_json_fields_and_unavailable_profiles_do_not_gain_credit(self) -> None:
        for invalid_value in ((1, 2), {1: "bad-key"}, math.inf, {"field": {1}}):
            with self.assertRaises(ValueError):
                m.json_value(invalid_value)
        value = query()
        value["player_piety_devotion_profile"] = {"available": False, "capture_epoch": 1,
            "date_raw": 10, "played_character_id": 1, "current_devotion_total_raw": None,
            "effective_level": None, "unavailable_reason": "authored unavailable"}
        metrics = m.project_observation(binding(), frame(), value, frame(2))
        self.assertFalse(metrics["devotion_observed"])
        profile = metrics["devotion_profile_raw"]
        assert profile is not None
        self.assertIs(profile["current_devotion_total_raw"], None)
        self.assertIs(profile["available"], False)
        self.assertFalse(metrics["trait_experience"]["observed"])
        self.assertFalse(metrics["current_location"]["observed"])

    def test_real_collector_to_persisted_json_uses_same_contract_and_two_controls(self) -> None:
        configured = os.environ.get("P3_MILESTONE_TEST_TMP")
        parent = Path(configured) if configured else None
        if parent is not None:
            parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            concrete = Client(Path(directory))
            client: m.MilestoneClient = concrete
            rows: list[m.MilestoneObservation] = []
            context: m.JSONObject = {"run_id": "test-run", "case_contract": {
                "machine_id": "test-machine", "policy": {"quit_reserve_seconds": 120}}}
            observation, latest = m.observe_milestone(context, client, binding(), rows, "before-start")
            assert observation is not None and latest is not None
            self.assertEqual(observation["status"], "observed")
            self.assertEqual(concrete.public_requests_used, 2)
            self.assertEqual(concrete.query_count, 1)
            self.assertFalse(observation["rewards_paid_by_click_claimed"])
            self.assertFalse(observation["seventeen_slots_closed"])
            evidence = observation["evidence"]
            decoded = m.json_value(json.loads(Path(evidence["path"]).read_text(encoding="utf-8")))
            expected = deepcopy(observation)
            del expected["evidence"]
            self.assertEqual(decoded, m.json_value(expected))
            self.assertEqual(m.observe_milestone(context, client, binding(), rows, "before-start"), (None, None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
