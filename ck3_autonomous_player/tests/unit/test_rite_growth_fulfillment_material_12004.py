"""New actual4 material consumer cases, with no live query or game action."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.rite_growth_material import (
    ENDING_FIELD, METRIC, STARTING_FIELD,
    capture_rite_growth_fulfillment_observation_v1,
    evaluate_rite_growth_material_postcondition_v1,
    plan_rite_growth_material_postcondition_v1,
    rite_growth_fulfillment_observation_v1,
)


def _snapshot(revision=7, native_revision=51):
    return {"snapshot_id": f"native:{native_revision}", "revision": revision,
        "native_revision": native_revision, "date_raw": 53265288,
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
        "diagnostics": {"hello": {"game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256}}}


def _query(snapshot, raw):
    return {"schema": "ck3_12004_religion_context_v1",
        "game_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "backend_id": CK3_12004.backend_id("player-religion-context-v1"),
        "domain_key": "player_religion_context_v1", "read_only": True,
        "available": True, "status": "observed", "unavailable_reason": None,
        "capture_epoch": 1000 + snapshot["native_revision"],
        "date_raw": snapshot["date_raw"], "played_character_id": 29829,
        "rite_id": 152, "faith_id": 23, "religion_id": 8, "faith_main_rite_id": 152,
        "faith_key": "catholic", "religion_key": "christianity",
        "faith_fervor_raw": 4336689, "spiritual_fulfillment_raw": raw, "raw_scale": 100000,
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": snapshot["revision"],
        "queried_native_revision": snapshot["native_revision"],
        "snapshot_revision": snapshot["native_revision"],
        "query_date_raw": snapshot["date_raw"]}


def _decision():
    # Reuse the known scope shape only as a synthetic actual4 consumer input.
    # The retained historical source artifact is not relabelled as current live.
    historical = Path(__file__).parent / "fixtures" / "rite_growth_event29_nine_scope_12003.json"
    context = json.loads(historical.read_text(encoding="utf-8"))["context"]
    context["provenance"]["backend_id"] = CK3_12004.backend_id("event-window-v1")
    context["snapshot_revision"] = 51
    for option in context["options"]:
        indicators = option.get("effect_indicators")
        if isinstance(indicators, dict) and isinstance(indicators.get("coverage"), str):
            indicators["coverage"] = indicators["coverage"].replace("1.20.0.3", "1.20.0.4")
    return recommend_registered_vanilla_event_option_v1(
        context, played_character_id=29829, snapshot_option_count=3, ck3_build="1.20.0.4")


def _case(start=0, end=125000):
    first, last = _snapshot(), _snapshot(8, 52)
    before = rite_growth_fulfillment_observation_v1(_query(first, start), snapshot=first)
    after = rite_growth_fulfillment_observation_v1(_query(last, end), snapshot=last)
    decision = _decision()
    expected = plan_rite_growth_material_postcondition_v1(
        decision, first["played_character"], religion_context=before,
        snapshot_id=first["snapshot_id"], revision=first["revision"],
        native_revision=first["native_revision"], date_raw=first["date_raw"])
    selection = {"postcondition_verified": True, "old_event_instance_id": 29,
        "new_event_instance_id": None, "selected_native_option_index": 0,
        "selected_option_number": 1,
        "starting_snapshot_id": first["snapshot_id"], "starting_revision": first["revision"],
        "ending_snapshot_id": last["snapshot_id"], "ending_revision": last["revision"],
        STARTING_FIELD: before, ENDING_FIELD: after}
    return decision, expected, selection


class RiteGrowthFulfillmentMaterial12004Tests(unittest.TestCase):
    def test_registered_actual4_choice_can_credit_independent_gain_from_valid_zero(self):
        decision, expected, selection = _case()
        self.assertEqual(decision["status"], "recommended")
        self.assertEqual(decision["selected_native_option_index"], 0)
        self.assertEqual(decision["campaign_utility_profile"]["objective_id"],
                         "continue_robert_campaign_with_current_rite_and_fulfillment")
        self.assertFalse(decision["semantic_decision_ready"])
        self.assertEqual(expected["status"], "ready")
        self.assertEqual(expected["metric"], METRIC)
        self.assertEqual(expected["starting_value"], 0)
        result = evaluate_rite_growth_material_postcondition_v1(expected, selection)
        self.assertEqual(result["status"], "verified_change")
        self.assertEqual(result["delta"], 125000)  # Not the authored base of five.
        self.assertTrue(result["material_change_observed"])

    def test_unchanged_clamped_value_has_no_material_credit_and_decrease_fails(self):
        for start, end, status, relation, changed in (
            (0, 0, "verified_no_change", True, False),
            (1000000, 1000000, "verified_no_change", True, False),
            (1000000, 900000, "failed", False, True),
            (-100000, 0, "verified_change", True, True),
        ):
            with self.subTest(start=start, end=end):
                _, expected, selection = _case(start, end)
                result = evaluate_rite_growth_material_postcondition_v1(expected, selection)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["relation_satisfied"], relation)
                self.assertEqual(result["material_change_observed"], changed)
                self.assertEqual(result["delta"], end - start)

    def test_query_requires_the_actual_player_date_scale_and_native_revision(self):
        first = _snapshot()
        for field, value in (
            ("spiritual_fulfillment_raw", None), ("spiritual_fulfillment_raw", True),
            ("raw_scale", 1), ("played_character_id", 30000),
            ("date_raw", first["date_raw"] + 24), ("snapshot_revision", first["revision"]),
            ("queried_revision", 8), ("faith_id", None), ("rite_id", None),
        ):
            with self.subTest(field=field, value=value):
                query = _query(first, 0)
                query[field] = value
                observation = rite_growth_fulfillment_observation_v1(query, snapshot=first)
                self.assertEqual(observation["status"], "unavailable")
                self.assertIsNone(observation["fulfillment_raw"])
                expected = plan_rite_growth_material_postcondition_v1(
                    _decision(), first["played_character"], religion_context=observation,
                    snapshot_id=first["snapshot_id"], revision=7, native_revision=51,
                    date_raw=first["date_raw"])
                self.assertEqual(expected["status"], "unavailable")

    def test_instance_advance_requires_same_identity_and_newer_independent_frame(self):
        _, expected, original = _case()
        for field, value in (
            ("character_id", 30000), ("date_raw", 53265312), ("faith_id", 24),
            ("rite_id", 153), ("native_revision", 51), ("revision", 7),
            ("capture_epoch", original[STARTING_FIELD]["capture_epoch"]),
        ):
            with self.subTest(field=field):
                selection = copy.deepcopy(original)
                selection[ENDING_FIELD][field] = value
                result = evaluate_rite_growth_material_postcondition_v1(expected, selection)
                self.assertEqual(result["status"], "failed")
                self.assertFalse(result["material_change_observed"])
        for field, value in (("postcondition_verified", False), ("new_event_instance_id", 29),
                             ("selected_native_option_index", 1), ("ending_revision", 7)):
            with self.subTest(field=field):
                selection = copy.deepcopy(original)
                selection[field] = value
                self.assertEqual(evaluate_rite_growth_material_postcondition_v1(
                    expected, selection)["status"], "failed")
        selection = copy.deepcopy(original)
        selection.pop(ENDING_FIELD)
        self.assertEqual(evaluate_rite_growth_material_postcondition_v1(
            expected, selection)["status"], "unavailable")

    def test_collector_calls_existing_query_once_without_submitting_an_action(self):
        first = _snapshot()

        class QueryOnlyDriver:
            def __init__(self):
                self.revisions = []

            def query_player_religion_context_private_v1(self, *, expected_revision):
                self.revisions.append(expected_revision)
                return _query(first, 0)

        driver = QueryOnlyDriver()
        observation = capture_rite_growth_fulfillment_observation_v1(driver, snapshot=first)
        self.assertEqual(driver.revisions, [7])
        self.assertEqual(observation["status"], "available")
        self.assertEqual(observation["fulfillment_raw"], 0)

        class UnavailableDriver:
            def query_player_religion_context_private_v1(self, *, expected_revision):
                raise BridgeUnavailableError("source unavailable")

        observation = capture_rite_growth_fulfillment_observation_v1(UnavailableDriver(), snapshot=first)
        self.assertEqual(observation["status"], "unavailable")
        self.assertIn("source unavailable", observation["unavailable_reason"])


if __name__ == "__main__":
    unittest.main()
