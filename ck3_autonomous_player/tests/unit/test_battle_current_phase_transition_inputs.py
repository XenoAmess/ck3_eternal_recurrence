from __future__ import annotations

import copy
import unittest

from xar_autoplayer.bridge.battle_control_contract import (
    normalize_active_combat_resume_inputs_v1,
    normalize_battle_control_snapshot_v1,
)


KEY = "current_phase_transition_inputs_v1"


class CurrentPhaseTransitionInputChecks:
    """Focused helper suite; ordinary CI discovery requires no native artifact."""

    def __init__(self, document):
        self.document = document
        self._assertions = unittest.TestCase()

    def __getattr__(self, name):
        return getattr(self._assertions, name)

    def normalize(self, observation):
        frame = observation["battle_control_snapshot"]
        normalized = normalize_battle_control_snapshot_v1(
            frame, expected_subject_public_cunit_id=frame["subject_public_cunit_id"],
            expected_observed_date_raw=frame["observed_date_raw"],
            expected_snapshot_revision=frame["snapshot_revision"])
        self.assertEqual(normalized[KEY], observation["expected_phase_transition_inputs"])
        resume = normalize_active_combat_resume_inputs_v1(
            observation["active_resume_inputs"], parent=normalized)
        self.assertEqual(resume["observed"][KEY], normalized[KEY])
        self.assertIs(normalized["battle_control_ready"], True)
        return frame, normalized

    def check_actual_first_army_owner_and_current_timer_survive_formal_parser(self):
        self.assertEqual((self.document["schema_version"], self.document["actual"]), (1, 0))
        self.assertEqual(len(self.document["cases"]), 2)
        case = self.document["cases"][0]
        self.assertEqual(case["name"], "actual_first_army_and_current_timer")
        self.assertEqual(len(case["observations"]), 1)
        frame, normalized = self.normalize(case["observations"][0])
        block = normalized[KEY]
        self.assertEqual(block["minimum_elapsed_days"], 2)
        self.assertEqual(normalized["legality"]["elapsed_whole_days"], 2)
        self.assertEqual([row["side_index"] for row in block["sides"]], [0, 1])
        first, second = block["sides"]
        self.assertEqual(first["first_native_carmy_id"], 0x01000003)
        self.assertNotEqual(first["first_native_carmy_id"], frame["selected_native_carmy_id"])
        self.assertIs(first["owner_land_rule_allows"], False)
        self.assertIs(normalized["legality"]["landless_gate_allows_retreat"], True)
        self.assertIs(first["native_can_retreat"], False)
        self.assertIs(second["native_can_retreat"], False)
        self.assertIs(second["owner_land_rule_allows"], True)
        self.assertEqual([first[key] for key in ("disallowed", "allow_early", "skip_pursuit")],
                         [False, False, False])
        self.assertEqual([second[key] for key in ("disallowed", "allow_early", "skip_pursuit")],
                         [True, True, True])

    def check_zero_cache_lag_and_legacy_optional_shapes_remain_distinct(self):
        case = self.document["cases"][1]
        self.assertEqual(case["name"], "legal_zero_and_cache_lag")
        self.assertEqual(len(case["observations"]), 1)
        frame, normalized = self.normalize(case["observations"][0])
        block = normalized[KEY]
        self.assertEqual((block["forced_winner_raw"], block["result_start_date_raw"],
                          block["minimum_elapsed_days"]), (-1, 0, 0))
        self.assertEqual([row["stored_current_fighting_raw"] for row in block["sides"]], [0, 0])
        self.assertGreater(frame["attacker"]["levy_entries"][0]["current_fighting_raw"], 0)
        for row in block["sides"]:
            for key in ("disallowed", "allow_early", "skip_pursuit"):
                self.assertIs(row[key], False)
        self.assertIs(block["sides"][0]["native_can_retreat"], True)
        self.assertEqual(block["sides"][1]["first_native_carmy_id"], 0x01000002)
        self.assertIs(block["sides"][1]["native_can_retreat"], True)
        self.assertIs(block["sides"][1]["owner_land_rule_allows"], True)
        # Compatibility is a local legacy receipt shape, not an additional
        # native observation or fabricated production missing-binding frame.
        legacy = copy.deepcopy(frame)
        legacy.pop(KEY)
        legacy_normalized = normalize_battle_control_snapshot_v1(
            legacy, expected_subject_public_cunit_id=legacy["subject_public_cunit_id"],
            expected_observed_date_raw=legacy["observed_date_raw"],
            expected_snapshot_revision=legacy["snapshot_revision"])
        self.assertNotIn(KEY, legacy_normalized)
        old_resume = copy.deepcopy(case["observations"][0]["active_resume_inputs"])
        old_resume["observed"].pop(KEY)
        self.assertNotIn(KEY, normalize_active_combat_resume_inputs_v1(
            old_resume, parent=legacy_normalized)["observed"])
        # This is parser-only legacy optional shape compatibility, not an
        # observed native missing receiver or fallback branch.
        optional = copy.deepcopy(frame)
        optional[KEY] = None
        optional_normalized = normalize_battle_control_snapshot_v1(
            optional, expected_subject_public_cunit_id=optional["subject_public_cunit_id"],
            expected_observed_date_raw=optional["observed_date_raw"],
            expected_snapshot_revision=optional["snapshot_revision"])
        self.assertIsNone(optional_normalized[KEY])
        optional_resume = copy.deepcopy(case["observations"][0]["active_resume_inputs"])
        optional_resume["observed"][KEY] = None
        self.assertIsNone(normalize_active_combat_resume_inputs_v1(
            optional_resume, parent=optional_normalized)["observed"][KEY])


def make_phase_transition_suite(document):
    """Register only the two current scenarios against real reader wire data."""
    checks = CurrentPhaseTransitionInputChecks(document)
    return unittest.TestSuite(unittest.FunctionTestCase(getattr(checks, name), description=name)
        for name in (
            "check_actual_first_army_owner_and_current_timer_survive_formal_parser",
            "check_zero_cache_lag_and_legacy_optional_shapes_remain_distinct",
        ))
