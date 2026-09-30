"""Production collector coverage using the published #768 fixed-pair shape.

The pair identities match the observed Robert pair. New adult/final/cost fields
are contract fixtures, not claimed as an actual paused #768 readback.
"""

from copy import deepcopy
import unittest

from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import (
    _current_pair_actionability,
)
from xar_autoplayer.current_betrothal_fulfillment_proposal import (
    SUBMIT_STEP, build_current_betrothal_fulfillment_proposal,
)
from xar_autoplayer.m5_formal_proposal_collector import (
    SOURCE_SCHEMA, collect_m5_formal_proposals, plan_m5_formal_query_only,
)
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame


def _snapshot():
    return {"snapshot_id": "native:9", "revision": 10, "native_revision": 9,
            "date_raw": 53219952, "episode_run_id": "native-29829-2bc2d599f7f9",
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True},
            "played_character_gold": {"raw": 120644281, "scale": 100000},
            "active_wars": [], "player_armies": []}


def _relation():
    costs = {"raw_scale": 100000, "payer_role": "actor", "application_timing": "on_send",
             "gold_raw": 0, "prestige_raw": 0, "piety_raw": 0, "renown_raw": 0,
             "influence_raw": 0, "herd_raw": 0, "treasury_raw": 0,
             "treasury_or_gold_raw": 0, "merit_raw": 0, "barter_goods_raw": 0}
    value = _current_pair_actionability({
        "status": "available", "unavailable_reason": None,
        "actor_character_id": 29829, "heir_character_id": 38822,
        "partner_character_id": 38718, "recipient_character_id": 32897,
        "intermediary_character_id": 32897,
        "adult_readback_available": True, "heir_is_adult": True, "partner_is_adult": True,
        "heir_adult_measure_raw": 19, "partner_adult_measure_raw": 23,
        "heir_adult_threshold_raw": 18, "partner_adult_threshold_raw": 21,
        "ready_to_marry_betrothed": True, "final_legality_sampled": True,
        "complete_can_send": True, "recipient_acceptance_ready": True,
        "recipient_ai_accept_raw": 1000000, "recipient_answer_status_raw": 0,
        "generic_costs": costs, "effective_matrilineal_if_accepted": False,
        "predicted_outcome_if_accepted": "marriage",
    }, actor=29829, heir=38822, partner=38718)
    return {"schema": "xar.ck3.current-first-heir-relationship.v1",
            "native_revision": 9, "status": "available", "bilateral_verified": True,
            "heir_character_id": 38822, "betrothed_character_id": 38718,
            "primary_spouse_character_id": None, "spouse_character_ids": [],
            "betrothal_actionability": value}


def _plan(snapshot, relation):
    return {"policy": "one-life-turn-v1", "selected_step": SUBMIT_STEP,
            "current_betrothal_fulfillment": True,
            "current_betrothal_choice": {"resource_proposal":
                build_current_betrothal_fulfillment_proposal(
                    relation, snapshot, selected=True, reasons=[])
            }}


def _sources(snapshot, plan):
    frame = observed_frame(snapshot)
    return {"schema": SOURCE_SCHEMA, "status": "available", "read_only": True,
            "advertised": False, "frame": frame, "gold_reserve_raw": 20000000,
            "max_active_wars": 0,
            "existing_commitments": {"frame": frame, "gold_raw": 0,
                "pending_war_slots": 0, "army_ids": [], "ally_character_ids": [],
                "character_ids": [], "commitment_keys": []},
            "domains": {"marriage": {"plan": plan}}}


class CurrentBetrothalFulfillmentProposalTests(unittest.TestCase):
    def test_current_pair_reuses_existing_commitment_and_collects_one_proposal(self):
        snapshot, relation = _snapshot(), _relation()
        plan = _plan(snapshot, relation)
        resource = plan["current_betrothal_choice"]["resource_proposal"]
        self.assertEqual(resource["character_claims"], [29829, 32897, 38718, 38822])
        self.assertFalse(resource["resource_reservation_performed"])
        self.assertFalse(resource["existing_commitment"]["new_betrothal_commitment"])
        self.assertEqual(resource["existing_commitment"]["commitment_key"],
                         "first-heir-marriage:38822")
        collected = collect_m5_formal_proposals(snapshot=snapshot, sources=_sources(snapshot, plan))
        proposal = collected["dispatch"]["reservation"]
        self.assertEqual(len(collected["collected_candidate_ids"]), 1)
        self.assertEqual(proposal["commitments_after"]["character_ids"], [32897, 38718, 38822])
        self.assertEqual(proposal["commitments_after"]["commitment_keys"], ["first-heir-marriage:38822"])
        self.assertEqual(proposal["commitments_after"]["ally_character_ids"], [])
        self.assertIsNone(resource["alliance_established"])
        self.assertEqual(resource["mode"], "fulfill_existing_betrothal")

    def test_policy_hold_preserves_nonzero_and_unknown_costs(self):
        for costs in (None, {**_relation()["betrothal_actionability"]["generic_costs"],
                             "gold_raw": 3000000, "prestige_raw": -100000}):
            with self.subTest(costs=costs):
                relation = _relation()
                relation["betrothal_actionability"]["generic_costs"] = deepcopy(costs)
                resource = build_current_betrothal_fulfillment_proposal(
                    relation, _snapshot(), selected=False, reasons=["policy_hold"])
                self.assertFalse(resource["selected"])
                self.assertFalse(resource["formal_action_ready"])
                self.assertEqual(resource["reasons"], ["policy_hold"])
                self.assertEqual(resource["immediate_generic_costs"], costs)
                self.assertIsNone(resource["alliance_established"])
                self.assertEqual(resource["future_alliance_obligation"], "unknown")

    def test_formal_collector_routes_new_typed_step_without_ordinary_mode(self):
        snapshot = _snapshot()
        source = _sources(snapshot, _plan(snapshot, _relation()))

        class Driver:
            allow_private_family_marriage_formal_trial = True
            allow_private_faction_gift_formal_trial = False

            def __init__(self):
                self.source_reads = 0

            def take_snapshot(self):
                return deepcopy(snapshot)

            def query_m5_joint_proposal_sources_private_v1(self, **kwargs):
                self.source_reads += 1
                return deepcopy(source)

        driver = Driver()
        planned = plan_m5_formal_query_only(
            driver, {"revision": 10, "plan": {"policy": "one-life-turn-v1",
                "selected_step": "life-advance"}}, snapshot=snapshot,
            history=[], available_steps={SUBMIT_STEP})
        self.assertEqual(driver.source_reads, 1)
        self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
        self.assertEqual(planned["plan"]["phase"], "m5_joint_current_betrothal_typed_submit")
        self.assertTrue(planned["plan"]["current_betrothal_fulfillment"])
        self.assertEqual(planned["plan"]["current_betrothal_choice"]["resource_proposal"],
                         source["domains"]["marriage"]["plan"]["current_betrothal_choice"]["resource_proposal"])


if __name__ == "__main__":
    unittest.main()
