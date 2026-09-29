"""Contract choices for a verified split successor's default proposal."""

from __future__ import annotations

import copy
import unittest

from xar_autoplayer.guy_default_marriage_policy import (
    choose_specified_child_default_value,
    shortlist_specified_child_default_candidates,
)


def _legality() -> dict[str, object]:
    rows = []
    for candidate, recipient, age, accept, dynasty in (
            (37909, 34332, 18, 1000000, 1688),
            (39380, 30549, 10, 900000, 1445),
            (37571, 32897, 20, 2100000, 1807)):
        rows.append({"played_character_id": 29829,
                     "subject_character_id": 38988,
                     "candidate_character_id": candidate,
                     "recipient_matchmaker_character_id": recipient,
                     "heir_adult_measure_raw": 13,
                     "candidate_adult_measure_raw": age,
                     "candidate_dynasty_id": dynasty,
                     "recipient_ai_accept_raw": accept,
                     "recipient_answer_allows_send": True,
                     "complete_can_send": True})
    return {"schema": "xar.ck3.player-child-marriage-subject.v1",
            "status": "available", "player_child_verified": True,
            "native_revision": 3, "query_sequence": 1,
            "played_character_id": 29829, "subject_character_id": 38988,
            "adult_measure_raw": 13, "adult_threshold_raw": 16,
            "house_id": 174, "dynasty_id": 174,
            "betrothed_character_id": None, "primary_spouse_character_id": None,
            "spouse_character_ids": [], "native_legal_candidates": rows}


def _value(legal_row: dict[str, object]) -> dict[str, object]:
    candidate = legal_row["candidate_character_id"]
    age = legal_row["candidate_adult_measure_raw"]
    fertility = {"source": "native_marriage_fertility_input",
                 "extension_present": True, "native_gate_evaluated": True,
                 "native_gate_allows": True, "effective_raw": 50000}
    costs = {term: 0 for term in (
        "gold_raw", "prestige_raw", "piety_raw", "renown_raw",
        "influence_raw", "herd_raw", "treasury_raw",
        "treasury_or_gold_raw", "merit_raw", "barter_goods_raw")}
    costs.update({"raw_scale": 100000, "payer_role": "actor",
                  "application_timing": "on_send"})
    return {"schema": "xar.ck3.player-child-marriage-value.v1",
            "status": "available", "read_only": True,
            "request_matrilineal_option": False,
            "native_revision": 3, "legality_query_sequence": 1,
            "played_character_id": 29829, "subject_character_id": 38988,
            "candidate_character_id": candidate,
            "row": {"actor_character_id": 29829,
                    "heir_character_id": 38988,
                    "candidate_character_id": candidate,
                    "recipient_character_id": legal_row["recipient_matchmaker_character_id"],
                    "final_legality_sampled": True, "complete_can_send": True,
                    "recipient_answer_status_raw": 0,
                    "recipient_ai_accept_raw": legal_row["recipient_ai_accept_raw"],
                    "requested_matrilineal_option": False,
                    "matrilineal_option_selected": False,
                    "effective_matrilineal_if_accepted": False,
                    "predicted_outcome_if_accepted": "betrothal",
                    "grand_wedding_option_selected": False,
                    "heir_is_adult": False, "candidate_is_adult": age >= 16,
                    "heir_adult_measure_raw": 13,
                    "heir_adult_threshold_raw": 16,
                    "candidate_adult_measure_raw": age,
                    "candidate_adult_threshold_raw": 16,
                    "heir_native_fertility": {**fertility,
                                              "effective_raw": 40000},
                    "candidate_native_fertility": fertility,
                    "heir_house_id": 174, "heir_dynasty_id": 174,
                    "played_house_id": 174, "played_dynasty_id": 174,
                    "candidate_dynasty_id": legal_row["candidate_dynasty_id"],
                    "heir_betrothed_character_id": None,
                    "heir_primary_spouse_character_id": None,
                    "heir_spouse_character_ids": [],
                    "candidate_betrothed_character_id": None,
                    "candidate_primary_spouse_character_id": None,
                    "candidate_spouse_character_ids": [],
                    "generic_costs": costs,
                    "possible_alliance_pairs": [{
                        "would_attempt_if_accepted": False}]}}


class GuyDefaultMarriagePolicyTests(unittest.TestCase):
    def test_same_frame_three_values_choose_earlier_adult_partner(self) -> None:
        legality = _legality()
        self.assertEqual(shortlist_specified_child_default_candidates(legality),
                         [37909, 37571])
        values = [_value(row) for row in legality["native_legal_candidates"]]
        decision = choose_specified_child_default_value(
            legality, values, split_successor_verified=True)
        self.assertEqual(decision["status"], "selected")
        self.assertEqual(decision["selected_candidate_character_id"], 37909)
        self.assertEqual([row["reason"] for row in decision["evaluated"]], [
            "positive_early_split_successor_betrothal",
            "candidate_not_adult",
            "positive_early_split_successor_betrothal"])

    def test_missing_split_proof_or_native_fertility_cannot_authorize(self) -> None:
        legality = _legality()
        value = _value(legality["native_legal_candidates"][0])
        self.assertEqual(choose_specified_child_default_value(
            legality, [value], split_successor_verified=False)["status"],
            "no_positive_value")
        lost = copy.deepcopy(value)
        lost["row"]["candidate_native_fertility"]["native_gate_allows"] = False
        self.assertEqual(choose_specified_child_default_value(
            legality, [lost], split_successor_verified=True)["status"],
            "no_positive_value")


if __name__ == "__main__":
    unittest.main()
