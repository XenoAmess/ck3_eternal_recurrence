from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.m5_joint_shortlist import compare_m5_joint_shortlist
from xar_autoplayer.m5_observed_opportunity_selector import faction_gift_proposal


# These five distinct identities appeared in the R0082 native-final-legal read.
# Every value, resource amount, and gift row in this test is synthetic.
_FAMILY_IDS = [16778038, 16778252, 16778632, 16778730, 16778737]
_FRAME = {
    "played_character_id": 29829, "native_revision": 3,
    "date_raw": 53178264, "snapshot_id": "native:3",
    "revision": 4, "episode_run_id": "synthetic-m5-shortlist",
}


def _snapshot() -> dict[str, object]:
    return {
        **_FRAME, "paused": True, "map_ready": True,
        "played_character_gold": {"raw": 30_000_000, "scale": 100_000},
        "active_wars": [{"war_id": 16777231}],
        "player_armies": [{"army_id": 71, "controllable": True}],
    }


def _intake() -> dict[str, object]:
    return {
        **_FRAME, "policy": "g2-m5-same-frame-intake-v1",
        "first_heir_character_id": 38822,
        "family_legality_query_sequence": 1,
        "candidates": [
            {"candidate_id": f"first-heir-marriage:38822-{candidate_id}",
             "domain": "first_heir_marriage", "subject_character_id": 38822,
             "candidate_character_id": candidate_id, "native_rank": None}
            for candidate_id in _FAMILY_IDS
        ] + [{
            "candidate_id": "war:29097-11-0", "domain": "war",
            "target_character_id": 29097,
            "casus_belli_index": 11, "casus_belli_key": "claim_cb",
            "configuration_index": 0, "claimant_character_id": 29829,
            "target_title_ids": [2115],
        }],
    }


def _commitments() -> dict[str, object]:
    return {
        "frame": dict(_FRAME), "gold_raw": 0, "pending_war_slots": 0,
        "army_ids": [], "ally_character_ids": [],
        "character_ids": [], "commitment_keys": [],
    }


def _gift() -> dict[str, object]:
    return faction_gift_proposal(
        frame=_FRAME,
        candidate={"status": "selected", "choice": {
            "snapshot_revision": 3, "native_snapshot_revision": 3,
            "date_raw": _FRAME["date_raw"], "player_character_id": 29829,
            "source_faction_id": 801, "recipient_character_id": 41003,
            "gold_cost_raw": 2_000_000, "opinion_delta": 20,
            "minimum_gold_reserve_raw": 10_000_000,
        }},
    )


def _lifestyle() -> dict[str, object]:
    return {
        "schema": "xar.ck3.m5-observed-opportunity.v1",
        "frame": dict(_FRAME), "candidate_id": "lifestyle:perk:cutting_corners",
        "domain": "lifestyle", "source_policy": "synthetic-perk-policy-v1",
        "domain_policy_ready": True, "gold_cost_raw": 0,
        "minimum_gold_reserve_raw": 0,
        "projected_supply_margin_raw": None, "war_slot_claim": 0,
        "war_operation": None, "army_ids": [], "ally_character_ids": [],
        "character_ids": [],
        "commitment_keys": ["lifestyle-perk-point:stewardship"],
        "evidence": {"synthetic_test_only": True},
    }


def _quote(candidate: dict[str, object], *, benefit: int) -> dict[str, object]:
    family = candidate["domain"] == "first_heir_marriage"
    return {
        **_FRAME, "candidate_id": candidate["candidate_id"],
        "common_value_policy": "synthetic-shared-units-v1",
        "benefit_units": benefit, "war_cost_units": 0,
        "family_cost_units": 0, "diplomacy_cost_units": 0,
        "supply_cost_units": 0, "long_term_cost_units": 1,
        "gold_raw": 0, "projected_supply_margin_units": 0,
        "army_ids": [], "ally_character_ids": [],
        "character_ids": (
            [38822, candidate["candidate_character_id"]] if family else []
        ),
        "commitment_keys": (["heir-marriage:38822"] if family else []),
    }


def _args() -> dict[str, object]:
    return {
        "snapshot": _snapshot(), "intake": _intake(),
        "observed_proposals": [_gift()],
        "marriage_projection": {
            "schema": "xar.ck3.first-heir-candidate-alliance-projection.v1",
            "status": "available", "native_revision": 3,
            "legality_query_sequence": 1,
            "rows": [{
                "status": "available", "actor_character_id": 29829,
                "heir_character_id": 38822,
                "candidate_character_id": candidate_id,
            } for candidate_id in _FAMILY_IDS],
        },
        "war_current": {
            "status": "available", "read_only": True, "advertised": False,
            "queried_snapshot_id": "native:3", "queried_revision": 4,
            "queried_native_revision": 3, "date_raw": 53178264,
            "readiness": {"current_treasury_ready": True,
                          "current_raised_armies_ready": True,
                          "current_raised_supply_ready": True,
                          "future_supply_ready": False},
            "m5_war_primary_current": {
                "actor_character_id": 29829,
                "current_treasury": {"raw": 30_000_000, "scale": 100_000},
                "active_war_ids": [16777231],
                "actor_current_raised_supply": [{
                    "army_id": 71, "native_carmy_id": 71,
                    "owner_character_id": 29829,
                    "current_supply_raw": 3_000_000,
                    "current_supply_scale": 100_000,
                }],
                "declaration": {
                    "target_character_id": 29097,
                    "casus_belli_index": 11,
                    "casus_belli_key": "claim_cb",
                    "configuration_index": 0,
                    "claimant_character_id": 29829,
                    "target_title_ids": [2115],
                },
            },
        },
        "assessments": [], "existing_commitments": _commitments(),
        "gold_reserve_raw": 5_000_000, "max_active_wars": 1,
    }


class M5JointShortlistTests(unittest.TestCase):
    def test_unpriced_real_legal_ids_return_specific_missing_inputs(self) -> None:
        result = compare_m5_joint_shortlist(**_args())
        self.assertEqual(result["status"], "fewer_than_five_priced_legal_candidates")
        self.assertEqual(result["legal_candidate_count"], 7)
        self.assertEqual(result["priced_candidate_count"], 0)
        self.assertIn("alliance_value_and_long_term_obligation",
                      result["unpriced_candidates"][0]["needed"])
        self.assertIn("future_route_supply_campaign_cost_and_exit_terms",
                      result["unpriced_candidates"][5]["needed"])
        self.assertIsNone(result["selected_step"])

    def test_shared_value_selects_one_feasible_gift_over_war_and_family(self) -> None:
        args = _args()
        args["assessments"] = [
            _quote(row, benefit=index + 2)
            for index, row in enumerate(args["intake"]["candidates"][:5])
        ]
        gift = args["observed_proposals"][0]
        gift_quote = _quote(gift, benefit=10)
        gift_quote.update({
            "gold_raw": gift["gold_cost_raw"],
            "character_ids": gift["character_ids"],
            "commitment_keys": gift["commitment_keys"],
        })
        args["assessments"].append(gift_quote)
        result = compare_m5_joint_shortlist(**args)
        self.assertEqual(result["selected_candidate_id"], gift["candidate_id"])
        self.assertEqual(result["reservation"]["commitments_after"]["gold_raw"],
                         gift["gold_cost_raw"])
        self.assertEqual(result["reservation"]["commitments_after"]["pending_war_slots"], 0)
        self.assertIsNone(result["selected_step"])
        self.assertFalse(result["formal_action_ready"])

        args["existing_commitments"]["character_ids"] = [41003]
        second = compare_m5_joint_shortlist(**args)
        self.assertEqual(second["selected_candidate_id"],
                         args["assessments"][4]["candidate_id"])

    def test_observed_claims_and_common_value_scale_cannot_be_relabelled(self) -> None:
        args = _args()
        args["assessments"] = [
            _quote(row, benefit=3)
            for row in args["intake"]["candidates"][:5]
        ]
        gift = args["observed_proposals"][0]
        bad = _quote(gift, benefit=20)
        bad["gold_raw"] = 0
        bad["character_ids"] = gift["character_ids"]
        bad["commitment_keys"] = gift["commitment_keys"]
        args["assessments"].append(bad)
        with self.assertRaisesRegex(ValueError, "shared resource claims"):
            compare_m5_joint_shortlist(**args)
        args["assessments"].pop()
        args["assessments"][0]["common_value_policy"] = "other-policy-v1"
        with self.assertRaisesRegex(ValueError, "one explicit common-value policy"):
            compare_m5_joint_shortlist(**args)

    def test_current_private_readbacks_bound_priced_family_and_war(self) -> None:
        args = _args()
        args["assessments"] = [
            _quote(row, benefit=3)
            for row in args["intake"]["candidates"][:5]
        ]
        args["marriage_projection"]["rows"][0]["candidate_character_id"] = 999
        with self.assertRaisesRegex(ValueError, "five current projections"):
            compare_m5_joint_shortlist(**args)

        args = _args()
        args["assessments"] = [
            _quote(row, benefit=3)
            for row in args["intake"]["candidates"]
        ]
        args["war_current"]["m5_war_primary_current"]["current_treasury"]["raw"] += 1
        with self.assertRaisesRegex(ValueError, "current war resources crossed"):
            compare_m5_joint_shortlist(**args)

    def test_war_budget_supply_ally_and_perk_opportunity_change_choice(self) -> None:
        args = _args()
        args["observed_proposals"].append(_lifestyle())
        args["assessments"] = [
            _quote(row, benefit=3)
            for row in args["intake"]["candidates"][:5]
        ]
        war = _quote(args["intake"]["candidates"][5], benefit=20)
        war.update({
            "war_cost_units": 3, "supply_cost_units": 2,
            "long_term_cost_units": 4, "gold_raw": 7_000_000,
            "projected_supply_margin_units": 100_000,
            "army_ids": [71], "ally_character_ids": [41004],
            "commitment_keys": ["planned-war:29097-11-0"],
        })
        args["assessments"].append(war)
        perk = _quote(_lifestyle(), benefit=12)
        perk.update({
            "long_term_cost_units": 3,
            "commitment_keys": ["lifestyle-perk-point:stewardship"],
        })
        args["assessments"].append(perk)

        # One existing war fills the only slot; the ready perk has positive
        # shared value and does not consume an army, ally, or war slot.
        blocked = compare_m5_joint_shortlist(**args)
        self.assertEqual(blocked["selected_candidate_id"], perk["candidate_id"])
        reasons = {row["candidate_id"]: row["reason"]
                   for row in blocked["analysis"]["evaluated"]}
        self.assertEqual(reasons[war["candidate_id"]], "war_slot_budget")

        args["max_active_wars"] = 2
        open_war = compare_m5_joint_shortlist(**args)
        self.assertEqual(open_war["selected_candidate_id"], war["candidate_id"])
        self.assertEqual(open_war["reservation"]["commitments_after"]["pending_war_slots"], 1)
        self.assertFalse(open_war["current_war_resources"]["future_supply_ready"])

        args["existing_commitments"]["ally_character_ids"] = [41004]
        self.assertEqual(compare_m5_joint_shortlist(**args)["selected_candidate_id"],
                         perk["candidate_id"])
        args["existing_commitments"]["ally_character_ids"] = []
        war["projected_supply_margin_units"] = -1
        low_supply = compare_m5_joint_shortlist(**args)
        self.assertEqual(low_supply["selected_candidate_id"], perk["candidate_id"])
        self.assertEqual(
            next(row for row in low_supply["analysis"]["evaluated"]
                 if row["candidate_id"] == war["candidate_id"])["reason"],
            "projected_supply_deficit",
        )


if __name__ == "__main__":
    unittest.main()
