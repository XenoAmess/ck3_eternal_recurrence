from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from xar_autoplayer.declaration_objective_priority_v1 import native_declaration_objective_priority_v1
from xar_autoplayer.strategy import _preferred_native_declaration


FIXTURE = Path(__file__).parent / "fixtures/robert_v20261019_declaration_order_178_192.json"


class DeclarationObjectivePriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.actor = cls.fixture["actor_character_id"]
        cls.rows = [case["declaration"] for case in cls.fixture["cases"]]

    def own_claim(self):
        return deepcopy(next(row for row in self.rows if row["target_character_id"] == 33388))

    def test_actual_observed_subset_queries_actor_title_claim_first(self):
        # The missing-actor control preserves the old ordering, whose first
        # five observed targets were artifact wars despite a 'claim' name.
        old = _preferred_native_declaration(self.rows)
        current = _preferred_native_declaration(self.rows, actor_character_id=self.actor)
        self.assertEqual(old["target_character_id"], 29373)
        self.assertEqual(old["casus_belli_key"], "reclaim_relic_artifact_war")
        self.assertEqual(current["target_character_id"], 33388)
        self.assertEqual(current["claimant_character_id"], self.actor)
        self.assertEqual(current["target_title_ids"], [7219])

    def test_actual_0192_evaluated_objectives_keep_original_power_precedence(self):
        # These genuine native power results rank tributary26904 cheapest by
        # the old power lane. They do not establish campaign profitability.
        assessments = {case["result_assessment"]["target_character_id"]: case["result_assessment"]
                       for case in self.fixture["cases"]}
        legacy = _preferred_native_declaration(self.rows, war_entry_assessments=assessments)
        chosen = _preferred_native_declaration(self.rows, war_entry_assessments=assessments,
                                               actor_character_id=self.actor)
        self.assertEqual(legacy["target_character_id"], 26904)
        self.assertIs(chosen, legacy)
        # Choosing which target to study does not add an executable step or
        # invent permission, utility, victory or a resolved title transfer.
        self.assertIs(chosen, next(row for row in self.rows if row == chosen))
        self.assertNotIn("declare_admitted", chosen)
        self.assertNotIn("expected_title_transfer", chosen)

    def test_evaluated_bad_claim_cannot_starve_better_evaluated_fallback(self):
        claim = self.own_claim()
        other = next(row for row in self.rows if row["target_character_id"] == 26904)
        assessments = {case["result_assessment"]["target_character_id"]: case["result_assessment"]
                       for case in self.fixture["cases"]}
        claim_power, other_power = (assessments[row["target_character_id"]] for row in (claim, other))
        self.assertLess(claim_power["actor_power_base_raw"], claim_power["target_power_total_raw"])
        self.assertGreater(other_power["actor_power_base_raw"], other_power["target_power_total_raw"])
        chosen = _preferred_native_declaration([claim, other], war_entry_assessments=assessments,
                                               actor_character_id=self.actor)
        self.assertIs(chosen, other)

    def test_nonplayer_claim_is_not_promoted(self):
        row = self.own_claim()
        row["claimant_character_id"] = self.actor + 1
        self.assertEqual(native_declaration_objective_priority_v1(row, actor_character_id=self.actor), 1)

    def test_missing_or_invalid_claimant_title_or_source_is_not_promoted(self):
        mutations = [
            {"claimant_character_id": None}, {"claimant_character_id": True},
            {"target_title_ids": []}, {"target_title_ids": None},
            {"target_title_ids": [0]}, {"target_title_ids": [True]},
            {"target_title_ids": [7219, "7220"]}, {"source": "synthetic"},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                row = {**self.own_claim(), **mutation}
                self.assertEqual(native_declaration_objective_priority_v1(row, actor_character_id=self.actor), 1)
        for actor in (None, True, 0, -1, str(self.actor)):
            with self.subTest(actor=actor):
                self.assertEqual(native_declaration_objective_priority_v1(self.own_claim(), actor_character_id=actor), 1)

    def test_other_objectives_remain_available_with_original_relative_order(self):
        others = [row for row in self.rows if row["casus_belli_key"] != "claim_cb"]
        self.assertEqual(_preferred_native_declaration(others),
                         _preferred_native_declaration(others, actor_character_id=self.actor))
        for key in ("make_tributary_cb", "unreviewed_claim_cb", "reclaim_relic_artifact_war"):
            row = {**self.own_claim(), "casus_belli_key": key, "target_title_ids": []}
            self.assertEqual(native_declaration_objective_priority_v1(row, actor_character_id=self.actor), 1)
            self.assertIs(_preferred_native_declaration([row], actor_character_id=self.actor), row)

    def test_assessed_claims_still_use_existing_power_order(self):
        claims = [row for row in self.rows if row["casus_belli_key"] == "claim_cb"]
        assessments = {case["result_assessment"]["target_character_id"]: case["result_assessment"]
                       for case in self.fixture["cases"]}
        legacy = _preferred_native_declaration(claims, war_entry_assessments=assessments)
        current = _preferred_native_declaration(claims, war_entry_assessments=assessments,
                                                actor_character_id=self.actor)
        self.assertIs(current, legacy)


if __name__ == "__main__":
    unittest.main()
