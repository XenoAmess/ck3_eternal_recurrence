"""Offline authorization/security oracles and generated graph checks, no CK3."""

from __future__ import annotations

from pathlib import Path
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import re
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch

from gen_school_consent import CHECKOUT, LOC, build_outputs, generate, native_admission
from school_consent_data import POLICY, BASELINE_COMMIT
from school_consent_model import ConsentController, Faith, Kind, Member, Rejected, School, World, quorum
from school_consent_callbacks import EventContext, dispatch
from native_admission_portable import validate_portable

# Read-only parser reuse. Run Python with -B so importing cannot create checkout
# bytecode. No importing build_release, runner, desktop, game or Steam helpers.
sys.path.insert(0, str(CHECKOUT / "tools"))
from extract_auto_upgrade_buildings import Block, parse_clausewitz


def fixture(*, native: bool = True) -> ConsentController:
    members = {"actor": Member("actor", "B", player=True), "b2": Member("b2", "B"), "b3": Member("b3", "B"),
               "receiver": Member("receiver", "A"), "a2": Member("a2", "A"), "a3": Member("a3", "A")}
    world = World({"A": School("A", "faith_a", ("t1", "t2", "t3")), "B": School("B", "faith_b", ("t4", "t5", "t6"))},
                  {"faith_a": Faith("faith_a", "A"), "faith_b": Faith("faith_b", "B")},
                  members, {"actor": 20000}, {"actor": 50000}, native_observed=native,
                  pair_divergence={("B", "A"): 25})
    # Explicit test double; never evidence that CK3 primitives work.
    return ConsentController(world, native_validator=lambda _world, _proposal: True)


def authorize(controller: ConsentController, proposal, *, consent_players: bool = True, signatures: bool = True):
    for electorate in proposal.electorates.values():
        for member in electorate:
            controller.vote(proposal, member, True, proposal.terms_revision)
    if consent_players:
        for player in proposal.affected_players:
            controller.consent_player(proposal, player, True)
    if signatures:
        controller.sign_school(proposal, proposal.moving_rite, proposal.actor)
        if proposal.receiving_faith:
            controller.sign_receiving(proposal, "receiver")


class ProposalTests(unittest.TestCase):
    def test_two_thirds_integer_boundary(self):
        for yes, total, expected in ((0, 0, False), (1, 2, False), (2, 3, True), (3, 5, False), (4, 6, True)):
            self.assertEqual(quorum(yes, total), expected)

    def test_no_npc_initiation(self):
        controller = fixture()
        with self.assertRaises(Rejected):
            controller.begin("b2", Kind.JOIN, "faith_a")

    def test_nomination_is_not_receiving_consent(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal, signatures=False)
        controller.sign_school(proposal, "B", "actor")
        with self.assertRaises(Rejected):
            controller.ready(proposal)

    def test_under_quorum_cannot_sign(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        controller.vote(proposal, "actor", True, 1)
        with self.assertRaises(Rejected):
            controller.sign_school(proposal, "B", "actor")

    def test_duplicate_ballot_rejected(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        controller.vote(proposal, "b2", True, 1)
        with self.assertRaises(Rejected):
            controller.vote(proposal, "b2", True, 1)

    def test_representative_must_have_voted_yes(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        for member in ("actor", "b2"):
            controller.vote(proposal, member, True, 1)
        controller.vote(proposal, "b3", False, 1)
        with self.assertRaises(Rejected):
            controller.sign_school(proposal, "B", "b3")

    def test_ballots_authorize_a_specific_nominee_not_any_scholar(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal, signatures=False)
        with self.assertRaises(Rejected):
            controller.sign_school(proposal, "B", "b2")

    def test_low_learning_player_still_must_consent(self):
        controller = fixture()
        controller.world.members["low"] = Member("low", "B", learning=2, player=True)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal, consent_players=False)
        controller.consent_player(proposal, "actor", True)
        with self.assertRaises(Rejected):
            controller.ready(proposal)
        controller.consent_player(proposal, "low", True)
        controller.ready(proposal)

    def test_affected_player_refusal_closes_round(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        controller.consent_player(proposal, "actor", False)
        self.assertEqual(proposal.phase, "rejected")
        self.assertEqual(controller.world.schools["B"].retry_until, POLICY.retry_days)

    def test_new_affected_player_invalidates_snapshot(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.members["new"] = Member("new", "B", learning=1, player=True)
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_same_count_replacement_elector_invalidates_snapshot(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.members["b3"].alive = False
        controller.world.members["b4"] = Member("b4", "B")
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_head_change_invalidates_even_matching_faith(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.faiths["faith_a"].head = "receiver"
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_terms_revision_not_interchangeable(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a", terms_revision=3)
        with self.assertRaises(Rejected):
            controller.vote(proposal, "actor", True, 2)

    def test_doctrine_change_after_consent_invalidates(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.faiths["faith_a"].core_doctrines = ("new_rule",)
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_different_core_doctrines_cannot_be_bought_away(self):
        controller = fixture()
        controller.world.faiths["faith_b"].core_doctrines = ("different_rule",)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        with self.assertRaisesRegex(Rejected, "same-core"):
            controller.commit(proposal)

    def test_same_main_doctrine_set_ignores_order_but_not_actual_membership(self):
        controller = fixture()
        controller.world.faiths["faith_a"].core_doctrines = ("clergy", "head")
        controller.world.faiths["faith_b"].core_doctrines = ("head", "clergy")
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.commit(proposal)
        self.assertEqual(controller.world.schools["B"].faith, "faith_a")

    def test_different_school_core_tenets_do_not_block_equal_main_doctrine_sets(self):
        controller = fixture()
        self.assertNotEqual(controller.world.schools["A"].core, controller.world.schools["B"].core)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.commit(proposal)
        self.assertEqual(controller.world.schools["B"].core, ("t4", "t5", "t6"))
        self.assertEqual(controller.world.schools["B"].faith, "faith_a")

    def test_two_different_heads_remain_incompatible_despite_consent(self):
        controller = fixture()
        controller.world.faiths["faith_b"].head = "b2"
        controller.world.faiths["faith_a"].head = "receiver"
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.consent_head(proposal, "source", "b2", True)
        controller.consent_head(proposal, "receiving", "receiver", True)
        with self.assertRaisesRegex(Rejected, "same-core"):
            controller.commit(proposal)

    def test_missing_native_acceptance_blocks_commit_without_mutation(self):
        controller = fixture(native=False)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        money_before = controller.world.gold["actor"]
        with self.assertRaisesRegex(Rejected, "not yet verified"):
            controller.commit(proposal)
        self.assertEqual(controller.world.schools["B"].faith, "faith_b")
        self.assertEqual(controller.world.gold["actor"], money_before)

    def test_pair_divergence_missing_or_at_threshold_blocks(self):
        for divergence in (None, 100, 125):
            controller = fixture()
            if divergence is None:
                controller.world.pair_divergence.clear()
            else:
                controller.world.pair_divergence[("B", "A")] = divergence
            proposal = controller.begin("actor", Kind.JOIN, "faith_a")
            authorize(controller, proposal)
            with self.assertRaises(Rejected):
                controller.commit(proposal)

    def test_costs_rechecked_at_commit(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.gold["actor"] = POLICY.join_gold - 1
        with self.assertRaises(Rejected):
            controller.commit(proposal)
        self.assertEqual(controller.world.schools["B"].faith, "faith_b")

    def test_rejection_has_finite_retry_then_new_round(self):
        controller = fixture()
        first = controller.begin("actor", Kind.JOIN, "faith_a")
        controller.consent_player(first, "actor", False)
        controller.world.day = POLICY.retry_days - 1
        with self.assertRaises(Rejected):
            controller.begin("actor", Kind.JOIN, "faith_a")
        controller.world.day += 1
        second = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assertEqual(second.serial, first.serial + 1)
        with self.assertRaises(Rejected):
            controller.vote(first, "b2", True, 1)

    def test_expired_authorization_cannot_be_reused(self):
        controller = fixture()
        first = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, first)
        controller.world.day = first.deadline
        with self.assertRaises(Rejected):
            controller.commit(first)
        second = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assertEqual(second.player_consents, set())
        self.assertTrue(all(not votes for votes in second.ballots.values()))

    def test_owner_death_invalidates_pending_signatures(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.members["actor"].alive = False
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_cooldown_follows_school_when_sponsor_changes(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.commit(proposal)
        controller.world.members["b2"].player = True
        with self.assertRaises(Rejected):
            controller.begin("b2", Kind.DETACH)

    def test_three_complete_cycles_use_current_dynamic_faith(self):
        controller = fixture()
        for cycle in range(3):
            join = controller.begin("actor", Kind.JOIN, "faith_a")
            authorize(controller, join)
            controller.commit(join)
            self.assertEqual(controller.world.faiths["faith_a"].main, "A")
            controller.world.day = controller.world.schools["B"].transition_until
            detach = controller.begin("actor", Kind.DETACH)
            authorize(controller, detach)
            dynamic = f"native_dynamic_{cycle}"
            controller.commit(detach, dynamic)
            self.assertEqual(controller.world.schools["B"].faith, dynamic)
            self.assertEqual(controller.world.faiths[dynamic].main, "B")
            controller.world.day = controller.world.schools["B"].transition_until
        self.assertEqual(len(controller.world.history), 6)
        self.assertEqual(controller.world.schools["B"].serial, 6)
        self.assertEqual(controller.world.history[-2]["old_faith"], "native_dynamic_1")

    def test_multi_rite_source_main_requires_separate_succession(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_b", ("u", "v", "w"))
        with self.assertRaises(Rejected):
            controller.begin("actor", Kind.JOIN, "faith_a")

    def test_eight_active_receiver_rites_each_need_their_own_quorum(self):
        controller = fixture()
        for index in range(7):
            identifier = f"C{index}"
            controller.world.schools[identifier] = School(identifier, "faith_a", ("u", "v", "w"))
            for voter in range(3):
                name = f"{identifier}_{voter}"
                controller.world.members[name] = Member(name, identifier)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        for identifier, electorate in proposal.electorates.items():
            for index, member in enumerate(sorted(electorate)):
                controller.vote(proposal, member, identifier != "C6" or index == 0, 1)
        for player in proposal.affected_players:
            controller.consent_player(proposal, player, True)
        controller.sign_school(proposal, "B", "actor")
        self.assertGreater(sum(sum(votes.values()) for identifier, votes in proposal.ballots.items() if identifier != "B"), 16)
        with self.assertRaisesRegex(Rejected, "Each active receiving rite"):
            controller.sign_receiving(proposal, "receiver")

    def test_seven_empty_templates_do_not_manufacture_votes_or_veto(self):
        controller = fixture()
        for index in range(7):
            identifier = f"C{index}"
            controller.world.schools[identifier] = School(identifier, "faith_a", ("u", "v", "w"))
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assertEqual(len(proposal.dormant_receivers), 7)
        authorize(controller, proposal)
        controller.commit(proposal)
        for identifier in proposal.dormant_receivers:
            self.assertEqual(proposal.ballots[identifier], {})
            self.assertNotIn(identifier, proposal.representative_signatures)
            self.assertEqual(controller.world.schools[identifier].faith, "faith_a")
        self.assertEqual(len(controller.world.history[-1]["dormant_excluded"]), 7)

    def test_active_zero_scholar_rite_needs_real_holder_or_teacher(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"))
        controller.world.members["low"] = Member("low", "C", learning=1)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assertNotIn("C", proposal.dormant_receivers)
        authorize(controller, proposal, signatures=False)
        controller.sign_school(proposal, "B", "actor")
        with self.assertRaises(Rejected):
            controller.sign_receiving(proposal, "receiver")
        with self.assertRaises(Rejected):
            controller.endorse_holder(proposal, "C", "low", True)

    def test_real_holder_endorsement_still_requires_all_players(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"), holder="low")
        controller.world.members["low"] = Member("low", "C", learning=1, player=True)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal, consent_players=False, signatures=False)
        controller.endorse_holder(proposal, "C", "low", True)
        controller.consent_player(proposal, "actor", True)
        with self.assertRaises(Rejected):
            controller.sign_receiving(proposal, "receiver")
        controller.consent_player(proposal, "low", True)
        controller.sign_school(proposal, "B", "actor")
        controller.sign_receiving(proposal, "receiver")
        controller.commit(proposal)
        self.assertEqual(proposal.ballots["C"], {})
        self.assertEqual(controller.world.history[-1]["holder_endorsements"], {"C": "low"})

    def test_county_without_characters_is_active_and_not_dormant(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"), county_count=1)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assertNotIn("C", proposal.dormant_receivers)
        authorize(controller, proposal, signatures=False)
        with self.assertRaises(Rejected):
            controller.sign_receiving(proposal, "receiver")

    def test_new_followers_in_dormant_rite_invalidate_the_round(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"))
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.members["new"] = Member("new", "C", learning=1)
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_receiver_member_changes_rite_with_same_totals_invalidates(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"))
        controller.world.members["c1"] = Member("c1", "C")
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.members["c1"].rite = "A"
        controller.world.members["a3"].rite = "C"
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_receiver_low_learning_player_is_affected(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"))
        controller.world.members["c1"] = Member("c1", "C")
        controller.world.members["low"] = Member("low", "C", learning=1, player=True)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal, consent_players=False)
        controller.consent_player(proposal, "actor", True)
        self.assertIn("low", proposal.affected_players)
        with self.assertRaises(Rejected):
            controller.commit(proposal)

    def test_receiving_rite_addition_invalidates_and_locks_are_released(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"))
        with self.assertRaises(Rejected):
            controller.commit(proposal)
        controller.cancel(proposal, rejected=False)
        self.assertIsNone(controller.world.schools["A"].proposal_owner)
        self.assertIsNone(controller.world.schools["B"].proposal_owner)

    def test_another_source_cannot_share_a_locked_receiving_council(self):
        controller = fixture()
        controller.begin("actor", Kind.JOIN, "faith_a")
        controller.world.faiths["faith_c"] = Faith("faith_c", "C")
        controller.world.schools["C"] = School("C", "faith_c", ("u", "v", "w"))
        controller.world.members["c1"] = Member("c1", "C", player=True)
        with self.assertRaisesRegex(Rejected, "Another round owns"):
            controller.begin("c1", Kind.JOIN, "faith_a")

    def test_receiver_own_affiliation_cooldown_does_not_veto_another_school(self):
        controller = fixture()
        controller.world.schools["A"].transition_until = 5000
        controller.world.schools["A"].retry_until = 2000
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.commit(proposal)
        self.assertEqual(controller.world.schools["B"].faith, "faith_a")

    def test_current_main_or_sole_rite_cannot_detach(self):
        controller = fixture()
        with self.assertRaises(Rejected):
            controller.begin("actor", Kind.DETACH)

    def test_old_head_refusal_does_not_veto_authorized_autonomy(self):
        controller = fixture()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.commit(proposal)
        controller.world.day = controller.world.schools["B"].transition_until
        controller.world.faiths["faith_a"].head = "receiver"
        detach = controller.begin("actor", Kind.DETACH)
        authorize(controller, detach)
        controller.consent_old_faith(detach, "receiver", False)
        controller.commit(detach, "new_unrecognized")
        self.assertFalse(controller.world.history[-1]["peaceful"])

    def test_detach_head_provisioning_not_silently_added(self):
        controller = fixture()
        join = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, join)
        controller.commit(join)
        controller.world.day = controller.world.schools["B"].transition_until
        controller.world.schools["B"].head_rule = "spiritual"
        detach = controller.begin("actor", Kind.DETACH)
        authorize(controller, detach)
        with self.assertRaises(Rejected):
            controller.commit(detach, "new_temporal")


class HeadRetirementRevisionTests(unittest.TestCase):
    def headed(self):
        controller = fixture()
        world = controller.world
        for identifier, head, title in (("faith_a", "receiver", "target-hof"), ("faith_b", "b2", "source-hof")):
            faith = world.faiths[identifier]
            faith.head = head
            faith.head_title = title
            faith.owned_head_title = True
            faith.head_title_owner = identifier
            faith.core_doctrines = ("doctrine_temporal_head",)
            world.titles[title] = head
        world.titles["b2-secular-property"] = "b2"
        world.schools["A"].head_rule = world.schools["B"].head_rule = "temporal"
        return controller

    def test_source_release_refusal_does_not_veto_authorized_owned_title_retirement(self):
        controller = self.headed()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.consent_head(proposal, "source", "b2", False)
        controller.consent_head(proposal, "receiving", "receiver", True)
        controller.commit(proposal)
        self.assertEqual(controller.world.retired_titles, {"source-hof"})
        self.assertEqual(controller.world.titles["b2-secular-property"], "b2")
        self.assertTrue(controller.world.members["b2"].alive)
        self.assertEqual(controller.world.schools["B"].retired_teacher, "b2")
        self.assertEqual(controller.world.faiths["faith_a"].head, "receiver")

    def test_unowned_title_cannot_be_retired_even_after_mandates(self):
        controller = self.headed()
        controller.world.faiths["faith_b"].owned_head_title = False
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.consent_head(proposal, "receiving", "receiver", True)
        with self.assertRaises(Rejected):
            controller.commit(proposal)
        self.assertEqual(controller.world.titles["source-hof"], "b2")

    def test_multi_rite_source_cannot_retire_shared_head(self):
        controller = self.headed()
        controller.world.schools["other"] = School("other", "faith_b", ("t7", "t8", "t9"))
        controller.world.faiths["faith_b"].main = "other"
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.consent_head(proposal, "receiving", "receiver", True)
        with self.assertRaises(Rejected):
            controller.commit(proposal)
        self.assertEqual(controller.world.titles["source-hof"], "b2")

    def test_missing_receiving_consent_still_blocks_title_retirement(self):
        controller = self.headed()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        with self.assertRaises(Rejected):
            controller.commit(proposal)
        self.assertFalse(controller.world.retired_titles)

    def test_head_title_reassignment_invalidates_snapshot(self):
        controller = self.headed()
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal)
        controller.world.titles["source-hof"] = "b3"
        with self.assertRaises(Rejected):
            controller.consent_head(proposal, "receiving", "receiver", True)

    def test_three_temporal_cycles_create_fresh_owned_titles_and_retire_exact_old_one(self):
        controller = self.headed()
        for cycle in range(3):
            join = controller.begin("actor", Kind.JOIN, "faith_a")
            authorize(controller, join)
            controller.consent_head(join, "receiving", "receiver", True)
            controller.commit(join)
            controller.world.day = controller.world.schools["B"].transition_until
            detach = controller.begin("actor", Kind.DETACH)
            authorize(controller, detach)
            controller.consent_old_faith(detach, "receiver", False)
            result = controller.commit(detach, f"dynamic_temporal_{cycle}")
            self.assertEqual(controller.world.faiths[result].head, "actor")
            self.assertEqual(controller.world.faiths[result].head_title_owner, result)
            self.assertEqual(controller.world.titles["b2-secular-property"], "b2")
            controller.world.day = controller.world.schools["B"].transition_until
        self.assertEqual(len(controller.world.retired_titles), 3)


class EventCallbackNonceTests(unittest.TestCase):
    def replacement_round(self, *, authorized=True):
        controller = fixture()
        old = controller.begin("actor", Kind.JOIN, "faith_a")
        context = EventContext.capture(old)
        controller.cancel(old, rejected=False)
        current = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, current, signatures=authorized)
        return controller, current, context

    def assert_stale_unchanged(self, controller, old, respondent, action, **kwargs):
        before = deepcopy((controller.world, controller.proposals, controller.callback_nonces))
        with self.assertRaisesRegex(Rejected, "another proposal generation"):
            dispatch(controller, old, respondent, action, **kwargs)
        self.assertEqual((controller.world, controller.proposals, controller.callback_nonces), before)

    def test_stale_prior_round_confirm_cannot_commit_current_authorized_round(self):
        controller, current, old = self.replacement_round()
        self.assert_stale_unchanged(controller, old, "actor", "commit")
        self.assertEqual(controller.world.schools["B"].faith, "faith_b")
        self.assertEqual(current.phase, "consent")

    def test_stale_term_dialog_and_review_cancel_cannot_close_new_round(self):
        for event in ("lyd.200", "lyd.220"):
            with self.subTest(event=event):
                controller, current, old = self.replacement_round()
                self.assert_stale_unchanged(controller, old, "actor", "cancel")
                self.assertEqual(controller.world.schools["A"].proposal_owner, "actor")
                self.assertEqual(controller.world.schools["B"].proposal_owner, "actor")

    def test_stale_source_sign_cannot_sign_current_unsigned_round(self):
        controller, current, old = self.replacement_round(authorized=False)
        self.assert_stale_unchanged(controller, old, "actor", "source_sign")
        self.assertEqual(current.representative_signatures, {})
        dispatch(controller, EventContext.capture(current), "actor", "source_sign")
        self.assertEqual(current.representative_signatures, {"B": "actor"})

    def test_stale_receiving_refusal_cannot_reject_new_signed_round(self):
        controller, current, old = self.replacement_round()
        self.assert_stale_unchanged(controller, old, "receiver", "receiving_refuse")
        self.assertEqual(controller.world.schools["B"].retry_until, 0)
        dispatch(controller, EventContext.capture(current), "receiver", "receiving_refuse")
        self.assertEqual(current.phase, "rejected")

    def test_stale_head_refusal_cannot_reject_new_round_but_current_refusal_can(self):
        controller = HeadRetirementRevisionTests().headed()
        old_round = controller.begin("actor", Kind.JOIN, "faith_a")
        old = EventContext.capture(old_round)
        controller.cancel(old_round, rejected=False)
        current = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, current)
        self.assert_stale_unchanged(controller, old, "receiver", "receiving_head_no")
        dispatch(controller, EventContext.capture(current), "receiver", "receiving_head_no")
        self.assertEqual(current.phase, "rejected")
        self.assertFalse(controller.world.retired_titles)

    def test_stale_holder_refusal_cannot_reject_new_round_but_current_refusal_can(self):
        controller = fixture()
        controller.world.schools["C"] = School("C", "faith_a", ("u", "v", "w"), county_count=1, holder="holder")
        controller.world.members["holder"] = Member("holder", "C", learning=1)
        prior = controller.begin("actor", Kind.JOIN, "faith_a")
        old = EventContext.capture(prior)
        controller.cancel(prior, rejected=False)
        current = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assert_stale_unchanged(controller, old, "holder", "holder_no", school="C")
        dispatch(controller, EventContext.capture(current), "holder", "holder_no", school="C")
        self.assertEqual(current.phase, "rejected")

    def test_all_ballot_signature_and_player_callbacks_reject_prior_generation(self):
        cases = (("actor", "source_vote_yes"), ("b2", "source_vote_no"),
                 ("receiver", "target_vote_yes"), ("a2", "target_vote_no"),
                 ("actor", "player_yes"), ("actor", "player_no"),
                 ("receiver", "receiving_sign"))
        for respondent, action in cases:
            with self.subTest(action=action):
                controller, current, old = self.replacement_round(authorized=False)
                self.assert_stale_unchanged(controller, old, respondent, action)

    def test_actor_nonce_prevents_cross_school_serial_collision(self):
        controller = fixture()
        prior = controller.begin("actor", Kind.JOIN, "faith_a")
        old = EventContext.capture(prior)
        controller.cancel(prior, rejected=False)
        controller.world.faiths["faith_c"] = Faith("faith_c", "C")
        controller.world.schools["C"] = School("C", "faith_c", ("u", "v", "w"))
        controller.world.members["actor"].rite = "C"
        current = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assertEqual(current.serial, prior.serial)  # Original rite-local collision.
        self.assertNotEqual(current.callback_nonce, prior.callback_nonce)
        self.assert_stale_unchanged(controller, old, "actor", "cancel")
        # Even a wrongly re-bound school with the old nonce is refused.
        self.assert_stale_unchanged(controller, replace(old, school="C"), "actor", "cancel")
        # The repaired generation also admits its own new vote/signature;
        # refusing every popup would hide the collision without fixing it.
        context = EventContext.capture(current)
        dispatch(controller, context, "actor", "source_vote_yes")
        dispatch(controller, context, "actor", "player_yes")
        dispatch(controller, context, "actor", "source_sign")
        self.assertEqual(current.representative_signatures, {"C": "actor"})

    def test_old_terms_same_generation_cannot_cancel_sign_or_commit(self):
        for action in ("cancel", "source_sign", "commit"):
            with self.subTest(action=action):
                controller = fixture()
                current = controller.begin("actor", Kind.JOIN, "faith_a")
                old_terms = EventContext.capture(current)
                current.terms_revision += 1
                self.assert_stale_unchanged(controller, old_terms, "actor", action)

    def test_current_round_sign_and_confirm_complete_real_model_migration(self):
        controller = fixture()
        current = controller.begin("actor", Kind.JOIN, "faith_a")
        context = EventContext.capture(current)
        for member in ("actor", "b2", "b3"):
            dispatch(controller, context, member, "source_vote_yes")
        for member in ("receiver", "a2", "a3"):
            dispatch(controller, context, member, "target_vote_yes")
        dispatch(controller, context, "actor", "player_yes")
        dispatch(controller, context, "actor", "source_sign")
        dispatch(controller, context, "receiver", "receiving_sign")
        self.assertEqual(dispatch(controller, context, "actor", "commit"), "faith_a")
        self.assertEqual(controller.world.schools["B"].faith, "faith_a")
        self.assertEqual(controller.world.gold["actor"], 20000 - POLICY.join_gold)
        self.assertEqual(current.phase, "committed")


    def test_current_cancel_and_direct_current_decision_need_no_old_context(self):
        controller, current, old = self.replacement_round()
        dispatch(controller, EventContext.capture(current), "actor", "cancel")
        self.assertIsNone(controller.world.schools["B"].proposal_owner)
        next_round = controller.begin("actor", Kind.JOIN, "faith_a")
        controller.cancel(next_round, rejected=False)  # Direct current decision.
        self.assertIsNone(controller.world.schools["A"].proposal_owner)

    def test_valid_context_does_not_authorize_another_character_to_commit_cancel_or_sign(self):
        for action in ("commit", "cancel", "source_sign"):
            with self.subTest(action=action):
                controller, current, old = self.replacement_round()
                before = deepcopy((controller.world, controller.proposals))
                with self.assertRaisesRegex(Rejected, "another character"):
                    dispatch(controller, EventContext.capture(current), "b2", action)
                self.assertEqual((controller.world, controller.proposals), before)

    def test_old_timeout_cannot_expire_new_round_and_current_timeout_can(self):
        controller, current, old = self.replacement_round()
        controller.world.day = current.deadline
        self.assert_stale_unchanged(controller, old, "actor", "expire")
        dispatch(controller, EventContext.capture(current), "actor", "expire")
        self.assertEqual(current.phase, "expired")
        self.assertIsNone(controller.world.schools["B"].proposal_owner)

    def test_old_source_head_and_peaceful_responses_do_not_mutate_later_round(self):
        for action in ("source_head_yes", "source_head_no", "peaceful_yes", "peaceful_no"):
            with self.subTest(action=action):
                controller = HeadRetirementRevisionTests().headed()
                prior = controller.begin("actor", Kind.JOIN, "faith_a")
                old = EventContext.capture(prior)
                controller.cancel(prior, rejected=False)
                current = controller.begin("actor", Kind.JOIN, "faith_a")
                self.assert_stale_unchanged(controller, old, "b2", action)

    def test_current_departing_head_refusal_preserves_authorized_round(self):
        controller = HeadRetirementRevisionTests().headed()
        current = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, current)
        context = EventContext.capture(current)
        dispatch(controller, context, "b2", "source_head_no")
        dispatch(controller, context, "receiver", "receiving_head_yes")
        dispatch(controller, context, "actor", "commit")
        self.assertEqual(current.phase, "committed")


class AllAffectedHumanPlayerTests(unittest.TestCase):
    def affected(self, rite):
        controller = fixture()
        # Models an affected landless/adventurer human, with low learning so it
        # does not silently add an elector or manufacture a mandate.
        controller.world.members["landless"] = Member("landless", rite, learning=1, player=True, landed=False)
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, proposal, consent_players=False)
        controller.consent_player(proposal, "actor", True)
        return controller, proposal

    def test_source_landless_player_nonresponse_blocks_join_until_explicit_consent(self):
        controller, proposal = self.affected("B")
        self.assertIn("landless", proposal.affected_players)
        self.assertNotIn("landless", proposal.electorates["B"])
        with self.assertRaisesRegex(Rejected, "All affected players"):
            controller.commit(proposal)
        self.assertEqual(controller.world.schools["B"].faith, "faith_b")
        controller.consent_player(proposal, "landless", True)
        self.assertEqual(controller.commit(proposal), "faith_a")

    def test_receiving_landless_player_nonresponse_blocks_join_until_explicit_consent(self):
        controller, proposal = self.affected("A")
        self.assertIn("landless", proposal.affected_players)
        self.assertNotIn("landless", proposal.electorates["A"])
        with self.assertRaisesRegex(Rejected, "All affected players"):
            controller.commit(proposal)
        self.assertEqual(controller.world.schools["B"].faith, "faith_b")
        controller.consent_player(proposal, "landless", True)
        self.assertEqual(controller.commit(proposal), "faith_a")

    def test_source_landless_player_refusal_closes_round_without_migration_or_cost(self):
        controller, proposal = self.affected("B")
        before = (controller.world.gold["actor"], controller.world.piety["actor"])
        dispatch(controller, EventContext.capture(proposal), "landless", "player_no")
        with self.assertRaises(Rejected):
            controller.commit(proposal)
        self.assertEqual(proposal.phase, "rejected")
        self.assertEqual(controller.world.schools["B"].faith, "faith_b")
        self.assertEqual((controller.world.gold["actor"], controller.world.piety["actor"]), before)

    def test_receiving_landless_player_refusal_closes_round_without_migration_or_cost(self):
        controller, proposal = self.affected("A")
        before = (controller.world.gold["actor"], controller.world.piety["actor"])
        dispatch(controller, EventContext.capture(proposal), "landless", "player_no")
        with self.assertRaises(Rejected):
            controller.commit(proposal)
        self.assertEqual(proposal.phase, "rejected")
        self.assertEqual(controller.world.schools["B"].faith, "faith_b")
        self.assertEqual((controller.world.gold["actor"], controller.world.piety["actor"]), before)

    def test_landless_player_is_in_detach_electorate_and_cannot_be_bypassed(self):
        controller = fixture()
        join = controller.begin("actor", Kind.JOIN, "faith_a")
        authorize(controller, join)
        controller.commit(join)
        controller.world.day = controller.world.schools["B"].transition_until
        controller.world.members["landless"] = Member("landless", "B", learning=1, player=True, landed=False)
        detach = controller.begin("actor", Kind.DETACH)
        authorize(controller, detach, consent_players=False)
        controller.consent_player(detach, "actor", True)
        with self.assertRaisesRegex(Rejected, "All affected players"):
            controller.commit(detach, "new_dynamic")
        dispatch(controller, EventContext.capture(detach), "landless", "player_no")
        self.assertNotIn("new_dynamic", controller.world.faiths)

    def test_initiator_still_requires_land_and_npc_elector_qualification_is_unchanged(self):
        controller = fixture()
        controller.world.members["b2"].landed = False
        proposal = controller.begin("actor", Kind.JOIN, "faith_a")
        self.assertIn("b2", proposal.electorates["B"])
        self.assertNotIn("b2", proposal.affected_players)
        controller.cancel(proposal, rejected=False)
        controller.world.members["actor"].landed = False
        with self.assertRaisesRegex(Rejected, "landed adult player"):
            controller.begin("actor", Kind.JOIN, "faith_a")



def walk(block: Block):
    for entry in block.entries:
        yield entry
        if isinstance(entry.value, Block):
            yield from walk(entry.value)


class GeneratedGraphTests(unittest.TestCase):
    def setUp(self):
        self.outputs = build_outputs()
        self.scripts = {relative: parse_clausewitz(payload.decode("utf-8-sig"))
                        for relative, payload in self.outputs.items() if relative.endswith(".txt")}

    def test_generated_bom_structure_and_determinism(self):
        self.assertEqual(self.outputs, build_outputs())
        self.assertEqual(len(self.outputs), 16)
        for relative, payload in self.outputs.items():
            self.assertTrue(payload.startswith(b"\xef\xbb\xbf"), relative)
            self.assertNotRegex(payload.decode("utf-8-sig"), r"@[A-Z_]+@")
        for path, ast in self.scripts.items():
            if path.startswith("common/scripted_effects/"):
                self.assertLessEqual(len(ast.entries), 10, path)

    def test_bilingual_keys_and_placeholders_match(self):
        placeholders = re.compile(r"\[[^\]\r\n]+\]|\$[^$\r\n]+\$")
        for key, (chinese, english) in LOC.items():
            self.assertEqual(sorted(placeholders.findall(chinese)), sorted(placeholders.findall(english)), key)

    def test_default_native_admission_is_closed(self):
        ast = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        entry = next(entry for entry in ast.entries if entry.key == "lyd_c2_native_admitted_trigger")
        self.assertEqual([(item.key, item.value) for item in entry.value.entries], [("always", "no")])

    def test_hash_binding_can_admit_a_synthetic_unit_receipt_without_claiming_flow_live(self):
        # A relocated copy of real permanent proof tests hash rejection without
        # mutating the original receipts or accepting an invented live schema.
        _, record = self.portable_record()
        with tempfile.TemporaryDirectory(prefix="lyd-admission-unit-") as directory:
            relocated = Path(directory)
            for item in record["evidence_refs"]:
                target = relocated / item["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(CHECKOUT / item["path"], target)
            receipt = relocated / "copied-unit-receipt.json"
            receipt.write_text(json.dumps(record), encoding="utf-8")
            with patch("gen_school_consent.CHECKOUT", relocated):
                admission = native_admission(receipt)
                self.assertTrue(admission["admitted"])
                self.assertEqual(admission["consent_flow_live"], "NOT_RUN")
                output = build_outputs(native_evidence=receipt)["common/scripted_triggers/lyd_c2_consent_triggers.txt"].decode("utf-8-sig")
                self.assertIn("lyd_c2_native_admitted_trigger = { always = yes }", output)
                artifact = relocated / record["evidence_refs"][0]["path"]
                artifact.write_bytes(artifact.read_bytes() + b"changed")
                with self.assertRaisesRegex(ValueError, "hash mismatch"):
                    build_outputs(native_evidence=receipt)

    def test_malformed_admission_cannot_silently_open_gate(self):
        with tempfile.TemporaryDirectory(prefix="lyd-admission-unit-") as directory:
            receipt = Path(directory) / "invalid.json"
            receipt.write_text(json.dumps({"status": "LIVE_VERIFIED"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                build_outputs(native_evidence=receipt)

    def test_receiving_mandate_is_per_rite_and_dormancy_never_awards_votes(self):
        triggers = self.outputs["common/scripted_triggers/lyd_c2_consent_triggers.txt"].decode("utf-8-sig")
        self.assertIn("lyd_c2_dormant_receiving_rite_trigger = { var:lyd_c2_target_followers = 0 rite_counties = 0 }", triggers)
        self.assertIn("lyd_c2_receiver_rite_quorum_trigger", triggers)
        setup = self.outputs["common/scripted_effects/lyd_c2_setup_effects.txt"].decode("utf-8-sig")
        self.assertIn("name = lyd_c2_dormant_rites", setup)
        self.assertIn("trigger_event = lyd.213", setup)
        snapshot = self.outputs["common/scripted_effects/lyd_c2_snapshot_effects.txt"].decode("utf-8-sig")
        self.assertIn("variable = lyd_c2_target_rites", snapshot)
        self.assertIn("var:lyd_c2_check_followers != var:lyd_c2_target_followers", snapshot)

    def test_no_once_flag_defines_or_unrelated_property_mutations(self):
        disallowed = {"set_global_variable", "add_global_flag", "set_up_dynamic_temporal_hof_title_effect",
                      "create_title", "set_government_type", "set_independent", "change_rite_divergence",
                      "add_realm_law_skip_effects", "set_county_faith", "set_county_rite"}
        for path, ast in self.scripts.items():
            self.assertFalse(path.startswith(("common/on_action/", "common/defines/")))
            self.assertFalse(disallowed & {entry.key for entry in walk(ast)}, path)

    def test_native_calls_exist_only_in_guarded_commit_helpers(self):
        calls = {}
        for path, ast in self.scripts.items():
            for definition in ast.entries:
                if not isinstance(definition.value, Block):
                    continue
                for entry in walk(definition.value):
                    if entry.key in {"set_parent_faith", "detach_rite_to_new_faith"}:
                        calls[entry.key] = (path, definition.key)
                        first = definition.value.entries[0]
                        self.assertEqual(first.key, "if")
                        limit = next(item.value for item in first.value.entries if item.key == "limit")
                        self.assertIn("lyd_c2_ready_to_confirm_trigger", {item.key for item in walk(limit)})
                        self.assertIn(("is_ai", "no"), {(item.key, item.value) for item in walk(limit) if isinstance(item.value, str)})
        self.assertEqual(set(calls), {"set_parent_faith", "detach_rite_to_new_faith"})

    def test_same_core_and_head_rules_remain_explicit(self):
        ast = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        keys = {entry.key for entry in walk(ast)}
        self.assertNotIn("has_same_core_doctrines", keys)
        self.assertIn("lyd_c2_same_main_doctrines_trigger", keys)
        self.assertIn("any_doctrine", keys)
        self.assertIn("rite_has_doctrine", keys)
        self.assertIn("var:lyd_c2_source_faith.religious_head", keys)
        text = self.outputs["common/scripted_effects/lyd_c2_commit_effects.txt"].decode("utf-8-sig")
        self.assertIn("main = no include_derived = no", text)

    def test_effective_main_doctrine_comparator_checks_both_difference_directions(self):
        ast = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        definition = next(e.value for e in ast.entries if e.key == "lyd_c2_same_main_doctrines_trigger")
        # Evaluate the actual authored Boolean/scope tree against distinct sets.
        # The test's Doctrine universe is deliberately separate from Tenet keys.
        def evaluate(block, current, previous, saved, source, target, universe):
            results = []
            for entry in block.entries:
                key, value = entry.key, entry.value
                if key in {"AND", "OR", "NOT"}:
                    children = [evaluate(Block([child]), current, previous, saved, source, target, universe)
                                for child in value.entries]
                    result = all(children) if key == "AND" else any(children) if key == "OR" else not all(children)
                elif key == "any_doctrine":
                    result = any(evaluate(value, doctrine, current, saved, source, target, universe) for doctrine in universe)
                elif key == "save_temporary_scope_as":
                    saved[value] = current
                    result = True
                elif key == "exists":
                    result = current in {"source", "target"} and value == "main_rite"
                elif key == "$TARGET$":
                    result = evaluate(value, "target", current, saved, source, target, universe)
                elif key.startswith("scope:"):
                    result = evaluate(value, saved[key.split(":", 1)[1].split(".", 1)[0]] + ".main", current,
                                      saved, source, target, universe)
                elif key == "rite_has_doctrine":
                    self.assertEqual(value, "prev")
                    result = previous in (source if current == "source.main" else target)
                else:
                    raise AssertionError(key)
                results.append(result)
            return all(results)
        cases = [({"head", "clergy"}, {"head", "clergy"}, True),
                 ({"head"}, {"head", "clergy"}, False),
                 ({"head", "clergy"}, {"head"}, False),
                 (set(), set(), True)]
        for source, target, expected in cases:
            with self.subTest(source=source, target=target):
                self.assertEqual(evaluate(definition, "source", None, {}, source, target, {"head", "clergy"}), expected)
        self.assertFalse({e.key for e in walk(definition)} & {"any_rite_tenet", "has_tenet_status", "rite_has_tenet"})

    def test_divergence_arguments_use_saved_rite_scopes_and_never_macro_variable_paths(self):
        expressions = []
        for path, ast in self.scripts.items():
            for entry in walk(ast):
                if "divergence(" in entry.key:
                    expressions.append((path, entry.key))
        self.assertEqual(len(expressions), 2)
        for path, expression in expressions:
            self.assertEqual(expression, '"divergence(scope:lyd_c2_native_target_main)"', path)
            self.assertNotIn("$", expression)
            self.assertNotIn(".var:", expression)
        trigger = self.outputs["common/scripted_triggers/lyd_c2_consent_triggers.txt"].decode("utf-8-sig")
        commit = self.outputs["common/scripted_effects/lyd_c2_commit_effects.txt"].decode("utf-8-sig")
        self.assertIn("var:lyd_c2_target_main = { save_temporary_scope_as = lyd_c2_native_target_main }", trigger)
        self.assertLess(commit.index("save_scope_as = lyd_c2_native_target_main"), commit.index("lyd_c2_retire_source_head_effect = yes"))
        self.assertLess(commit.index("save_scope_as = lyd_c2_native_target_main"), commit.index("set_parent_faith ="))

    def test_owned_retirement_is_guarded_before_migration_and_never_uses_empty_faith_guess(self):
        heads = self.scripts["common/scripted_effects/lyd_c2_head_effects.txt"]
        retirement = next(entry.value for entry in heads.entries if entry.key == "lyd_c2_retire_source_head_effect")
        self.assertIn("lyd_c2_source_retirement_trigger", {entry.key for entry in walk(retirement.entries[0].value.entries[0].value)})
        destroys = [entry.value for entry in walk(retirement) if entry.key == "destroy_title"]
        self.assertEqual(destroys, ["var:lyd_c2_source_head_title"])
        trigger = next(entry.value for entry in self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"].entries
                       if entry.key == "lyd_c2_source_retirement_trigger")
        self.assertIn("lyd_c2_single_rite_faith_trigger", {entry.key for entry in walk(trigger)})
        self.assertIn(("has_variable", "lyd_c2_owned_head_title"), {(entry.key, entry.value) for entry in walk(trigger) if isinstance(entry.value, str)})
        text = self.outputs["common/scripted_effects/lyd_c2_commit_effects.txt"].decode("utf-8-sig")
        self.assertLess(text.index("lyd_c2_retire_source_head_effect = yes"), text.index("set_parent_faith ="))
        self.assertNotIn("NOT = { any_faith_rite = { always = yes } }", text)

    def test_dynamic_faith_actor_and_other_authority_locks_are_preserved(self):
        text = self.outputs["common/scripted_triggers/lyd_c2_consent_triggers.txt"].decode("utf-8-sig")
        self.assertNotIn("lyd_can_use_school_trigger", text)
        self.assertIn("NOT = { has_variable = lyd_c3_proposal_owner }", text)
        self.assertNotIn("var:lyd_c2_source_head_yes = 1", text)
        self.assertIn("var:lyd_c2_target_head_yes = 1", text)
        actor = next(entry.value for entry in self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"].entries
                     if entry.key == "lyd_c2_actor_trigger")
        self.assertIn(("lyd_member_rite_trigger", "yes"),
                      {(entry.key, entry.value) for entry in actor.entries if isinstance(entry.value, str)})

    def test_shared_factory_guard_never_adds_unrelated_realm_law(self):
        text = self.outputs["common/scripted_effects/lyd_c3_head_factory.txt"].decode("utf-8-sig")
        self.assertIn("has_variable = lyd_c3_head_creation_authorized", text)
        self.assertIn("rite = faith.main_rite", text)
        self.assertNotIn("add_realm_law", text)
        self.assertNotIn("set_up_dynamic_temporal_hof_title_effect", text)
        self.assertEqual(text.count("create_dynamic_title ="), 1)

    def test_saved_scope_is_not_smuggled_into_trigger_or_random_selector(self):
        triggers = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        self.assertNotIn("save_scope_as", {entry.key for entry in walk(triggers)})
        for ast in self.scripts.values():
            for entry in walk(ast):
                if entry.key.startswith("random_") and isinstance(entry.value, Block):
                    self.assertNotIn("save_scope_as", {item.key for item in walk(entry.value)})

    def test_actual_bounded_binding_opens_only_primitive_gate_and_keeps_flow_unverified(self):
        binding = Path(__file__).resolve().parents[1] / "tools/reference/native-primitive-tracked-admission.json"
        result = native_admission(binding)
        self.assertTrue(result["admitted"])
        self.assertEqual(result["consent_flow_live"], "NOT_RUN")
        self.assertEqual(result["shared_narrow_head_factory_live"], "NOT_RUN")
        self.assertIn("NOT_CLAIMED", result["zero_error_acceptance"])

    def test_shared_migration_hooks_clear_only_role_metadata_without_c2_lock_mutation(self):
        text = self.outputs["common/scripted_effects/lyd_c3_migration_hooks.txt"].decode("utf-8-sig")
        ast = self.scripts["common/scripted_effects/lyd_c3_migration_hooks.txt"]
        self.assertFalse({entry.key for entry in walk(ast)} & {"set_parent_faith", "destroy_title", "set_religious_head_title"})
        removed = {entry.value for entry in walk(ast) if entry.key == "remove_variable"}
        self.assertFalse(any(str(value).startswith("lyd_c2_") for value in removed))
        commit = self.outputs["common/scripted_effects/lyd_c2_commit_effects.txt"].decode("utf-8-sig")
        self.assertLess(commit.index("lyd_c3_before_rite_migration_effect = yes"), commit.index("set_parent_faith ="))
        self.assertIn("lyd_c3_reconcile_faith_roles_effect = yes", commit)
        delegated = build_outputs(include_shared=False)
        self.assertEqual(len(delegated), 14)
        self.assertNotIn("common/scripted_effects/lyd_c3_head_factory.txt", delegated)
        self.assertNotIn("common/scripted_effects/lyd_c3_migration_hooks.txt", delegated)

    def test_every_event_has_player_entry_path(self):
        definitions = {}
        roots = set()
        for path, ast in self.scripts.items():
            for entry in ast.entries:
                if isinstance(entry.value, Block):
                    definitions[entry.key] = entry.value
                    if path.startswith(("common/decisions/", "common/character_interactions/")):
                        roots.add(entry.key)
        graph = {}
        for identifier, body in definitions.items():
            edges = set()
            for entry in walk(body):
                if entry.key in definitions:
                    edges.add(entry.key)
                if entry.key in {"trigger_event", "id"} and isinstance(entry.value, str) and entry.value in definitions:
                    edges.add(entry.value)
            graph[identifier] = edges
        reachable = set(roots)
        while True:
            expanded = reachable | {edge for node in reachable for edge in graph.get(node, set())}
            if expanded == reachable:
                break
            reachable = expanded
        self.assertTrue({identifier for identifier in definitions if re.fullmatch(r"lyd\.[0-9]+", identifier)} <= reachable)

    def test_old_callbacks_carry_serial_and_terms_and_new_round_clears_votes(self):
        triggers = self.outputs["common/scripted_triggers/lyd_c2_consent_triggers.txt"].decode("utf-8-sig")
        self.assertIn("var:lyd_c2_serial = scope:lyd_c2_event_serial", triggers)
        self.assertIn("var:lyd_c2_terms_revision = scope:lyd_c2_event_terms", triggers)
        setup = self.outputs["common/scripted_effects/lyd_c2_setup_effects.txt"].decode("utf-8-sig")
        self.assertIn("clear_variable_list = lyd_c2_source_electors", setup)
        self.assertIn("set_variable = { name = lyd_c2_source_yes value = 0 }", setup)

    def test_every_mutating_event_option_uses_effect_that_revalidates_context(self):
        expected = {
            "lyd.200": {"lyd_c2_event_cancel_round_effect"},
            "lyd.210": {"lyd_c2_source_vote_effect"},
            "lyd.211": {"lyd_c2_target_vote_effect"},
            "lyd.212": {"lyd_c2_player_yes_effect", "lyd_c2_player_no_effect"},
            "lyd.213": {"lyd_c2_holder_endorse_effect", "lyd_c2_event_holder_reject_effect"},
            "lyd.220": {"lyd_c2_event_sign_source_effect", "lyd_c2_event_commit_effect", "lyd_c2_event_cancel_round_effect"},
            "lyd.221": {"lyd_c2_sign_target_effect", "lyd_c2_event_target_reject_effect"},
            "lyd.222": {"lyd_c2_head_yes_effect", "lyd_c2_event_head_reject_effect"},
            "lyd.223": {"lyd_c2_source_head_reply_effect"},
            "lyd.224": {"lyd_c2_peaceful_permission_effect"},
            "lyd.229": {"lyd_c2_expire_round_effect"},
        }
        definitions = {entry.key: entry.value for path, ast in self.scripts.items()
                       if path.startswith("common/scripted_effects/")
                       for entry in ast.entries if isinstance(entry.value, Block)}
        event_ast = self.scripts["events/lyd_c2_consent_events.txt"]
        for event in event_ast.entries:
            if event.key not in expected:
                continue
            calls = {entry.key for entry in walk(event.value) if entry.key in definitions}
            self.assertEqual(calls, expected[event.key], event.key)
            for name in calls:
                effect = definitions[name]
                first = effect.entries[0]
                self.assertEqual(first.key, "if", name)
                guard = next(entry.value for entry in first.value.entries if entry.key == "limit")
                guard_keys = {entry.key for entry in walk(guard)}
                if name == "lyd_c2_expire_round_effect":
                    self.assertIn("var:lyd_c2_callback_nonce", guard_keys)
                    self.assertIn("var:lyd_c2_terms_revision", guard_keys)
                else:
                    self.assertTrue(guard_keys & {"lyd_c2_ballot_context_trigger", "lyd_c2_initiator_event_context_trigger",
                                                 "lyd_c2_source_ballot_trigger", "lyd_c2_target_ballot_trigger",
                                                 "lyd_c2_player_consent_trigger", "lyd_c2_holder_context_trigger"}, name)

    def test_actor_popup_guards_option_and_effect_while_direct_cancel_is_current(self):
        events = self.scripts["events/lyd_c2_consent_events.txt"]
        for event in events.entries:
            if event.key not in {"lyd.200", "lyd.220"}:
                continue
            trigger = next(entry.value for entry in event.value.entries if entry.key == "trigger")
            self.assertIn("lyd_c2_initiator_event_context_trigger", {entry.key for entry in walk(trigger)})
            for option in (entry.value for entry in event.value.entries if entry.key == "option"):
                keys = {entry.key for entry in walk(option)}
                if keys & {"lyd_c2_event_cancel_round_effect", "lyd_c2_event_sign_source_effect", "lyd_c2_event_commit_effect"}:
                    option_trigger = next(entry.value for entry in option.entries if entry.key == "trigger")
                    self.assertIn("lyd_c2_initiator_event_context_trigger", {entry.key for entry in walk(option_trigger)})
        decisions = self.scripts["common/decisions/lyd_c2_consent_decisions.txt"]
        cancel = next(entry.value for entry in decisions.entries if entry.key == "lyd_c2_cancel_proposal_decision")
        self.assertIn("lyd_c2_cancel_round_effect", {entry.key for entry in walk(cancel)})
        self.assertNotIn("lyd_c2_event_cancel_round_effect", {entry.key for entry in walk(cancel)})

    def test_persistent_nonce_and_school_are_bound_before_every_popup(self):
        setup = self.scripts["common/scripted_effects/lyd_c2_setup_effects.txt"]
        reset = next(entry.value for entry in setup.entries if entry.key == "lyd_c2_reset_round_effect")
        self.assertNotIn("lyd_c2_callback_nonce", {entry.value for entry in walk(reset) if entry.key == "remove_variable"})
        text = self.outputs["common/scripted_effects/lyd_c2_setup_effects.txt"].decode("utf-8-sig")
        self.assertLess(text.index("save_scope_value_as = { name = lyd_c2_event_nonce"), text.index("lyd_c2_collect_target_effect = yes"))
        self.assertIn("change_variable = { name = lyd_c2_callback_nonce add = 1 }", text)
        triggers = self.outputs["common/scripted_triggers/lyd_c2_consent_triggers.txt"].decode("utf-8-sig")
        self.assertIn("var:lyd_c2_moving_rite = scope:lyd_c2_event_school", triggers)
        self.assertIn("var:lyd_c2_callback_nonce = scope:lyd_c2_event_nonce", triggers)
        review = self.outputs["common/scripted_effects/lyd_c2_snapshot_effects.txt"].decode("utf-8-sig")
        self.assertIn("var:lyd_c2_moving_rite = { save_scope_as = lyd_c2_event_school }", review)
        self.assertIn("save_scope_value_as = { name = lyd_c2_event_nonce value = var:lyd_c2_callback_nonce }", review)
        self.assertNotIn("change_variable = { name = lyd_c2_callback_nonce", review)

    def test_saved_vote_and_player_records_do_not_block_a_colliding_new_rite_serial(self):
        # Evaluate just the actual generated scalar record-match AND block.
        # This is not an engine interpreter; it checks the persisted-token
        # boundary that separate per-Proposal Python ballot dicts do not cover.
        def matches(block, stored, values):
            results = []
            for entry in block.entries:
                if entry.key == "AND" and isinstance(entry.value, Block):
                    results.append(matches(entry.value, stored, values))
                elif entry.key == "has_variable":
                    results.append(entry.value in stored)
                elif entry.key.startswith("var:") and entry.operator == "=":
                    results.append(stored.get(entry.key[4:]) == values[entry.value])
                else:
                    self.fail(f"Unexpected record-match term: {entry}")
            return all(results)
        triggers = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        for name, prefix in (("lyd_c2_source_ballot_trigger", "vote"),
                             ("lyd_c2_target_ballot_trigger", "vote"),
                             ("lyd_c2_player_consent_trigger", "player")):
            with self.subTest(trigger=name):
                definition = next(entry.value for entry in triggers.entries if entry.key == name)
                duplicate = next(entry.value for entry in definition.entries if entry.key == "NOT"
                                 and any(term.key == "has_variable" and term.value == f"lyd_c2_{prefix}_owner"
                                         for term in walk(entry.value)))
                values = {"scope:lyd_c2_actor": "actor", "scope:lyd_c2_event_serial": 1,
                          "scope:lyd_c2_event_nonce": 2}
                old = {f"lyd_c2_{prefix}_owner": "actor", f"lyd_c2_{prefix}_serial": 1,
                       f"lyd_c2_{prefix}_nonce": 1}
                self.assertFalse(matches(duplicate, old, values))
                self.assertTrue(matches(duplicate, {**old, f"lyd_c2_{prefix}_nonce": 2}, values))
                old.pop(f"lyd_c2_{prefix}_nonce")  # Legacy persisted tokens.
                self.assertFalse(matches(duplicate, old, values))

    def test_signatures_require_a_vote_record_from_the_current_actor_nonce(self):
        triggers = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        source = next(entry.value for entry in triggers.entries if entry.key == "lyd_c2_source_mandate_trigger")
        self.assertIn(("var:lyd_c2_vote_nonce", "var:lyd_c2_callback_nonce"),
                      {(entry.key, entry.value) for entry in source.entries if isinstance(entry.value, str)})
        effects = self.scripts["common/scripted_effects/lyd_c2_vote_effects.txt"]
        receiving = next(entry.value for entry in effects.entries if entry.key == "lyd_c2_sign_target_effect")
        self.assertIn(("var:lyd_c2_vote_nonce", "scope:lyd_c2_event_nonce"),
                      {(entry.key, entry.value) for entry in walk(receiving) if isinstance(entry.value, str)})
        for name, variable in (("lyd_c2_source_vote_effect", "lyd_c2_vote_nonce"),
                               ("lyd_c2_target_vote_effect", "lyd_c2_vote_nonce"),
                               ("lyd_c2_player_yes_effect", "lyd_c2_player_nonce")):
            definition = next(entry.value for entry in effects.entries if entry.key == name)
            records = [entry.value for entry in walk(definition) if entry.key == "set_variable"]
            self.assertTrue(any({(term.key, term.value) for term in record.entries} ==
                                {("name", variable), ("value", "scope:lyd_c2_event_nonce")} for record in records), name)

    def test_ballot_auth_does_not_depend_on_optional_null_comparisons(self):
        ast = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        protected = {"lyd_c2_source_ballot_trigger", "lyd_c2_target_ballot_trigger", "lyd_c2_player_consent_trigger"}
        for definition in ast.entries:
            if definition.key in protected:
                self.assertTrue(all(entry.operator != "?=" for entry in walk(definition.value)), definition.key)
                self.assertIn("has_variable", {entry.key for entry in walk(definition.value)})

    def test_output_reproducibility_and_mismatch_detection(self):
        with tempfile.TemporaryDirectory(prefix="lyd-c2-offline-") as directory:
            destination = Path(directory)
            self.assertFalse(generate(destination)["mismatches"])
            self.assertFalse(generate(destination, check=True)["mismatches"])
            target = destination / "events/lyd_c2_consent_events.txt"
            target.write_bytes(target.read_bytes() + b"# drift\n")
            self.assertEqual(generate(destination, check=True)["mismatches"], ["events/lyd_c2_consent_events.txt"])

    def test_other_checkout_products_cannot_be_generation_targets(self):
        with self.assertRaises(ValueError):
            generate(CHECKOUT / "XenoAmess_s_Eternal_Recurrence")

    def test_read_only_generated_check_can_target_a_checkout_without_writing(self):
        actual = CHECKOUT / "mod_li_yu_dao"
        before = {path.relative_to(actual).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in actual.rglob("*") if path.is_file()}
        result = generate(actual, check=True, include_shared=False)
        after = {path.relative_to(actual).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in actual.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertIn(result["result"], {"PASS_OFFLINE_RENDER", "MISMATCH"})

    def test_all_affected_human_consent_paths_include_landless_players(self):
        triggers = self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"]
        consent = next(entry.value for entry in triggers.entries if entry.key == "lyd_c2_player_consent_trigger")
        self.assertNotIn("is_landed", {entry.key for entry in walk(consent)})
        actor = next(entry.value for entry in triggers.entries if entry.key == "lyd_c2_actor_trigger")
        self.assertIn(("is_landed", "yes"), {(entry.key, entry.value) for entry in walk(actor) if isinstance(entry.value, str)})
        setup = self.outputs["common/scripted_effects/lyd_c2_setup_effects.txt"].decode("utf-8-sig")
        refresh = self.outputs["common/scripted_effects/lyd_c2_snapshot_effects.txt"].decode("utf-8-sig")
        self.assertNotIn("is_landed", setup)
        self.assertNotIn("is_landed", refresh)

    def test_npc_electorate_policy_is_unchanged(self):
        # Freeze the original learning/alive/adult/incapacity rule, independently
        # of the human consent scope extension. No fallback to a local file.
        electorate = next(entry.value for entry in self.scripts["common/scripted_triggers/lyd_c2_consent_triggers.txt"].entries
                           if entry.key == "lyd_c2_elector_trigger")
        # The stable scalar policy is checked directly; consent filtering does
        # not introduce any landed/player condition into this electorate.
        self.assertNotIn("is_landed", {entry.key for entry in walk(electorate)})
        self.assertNotIn("is_ai", {entry.key for entry in walk(electorate)})
        self.assertIn(("learning", "15"), {(entry.key, entry.value) for entry in walk(electorate) if isinstance(entry.value, str)})

    def portable_record(self):
        path = Path(__file__).resolve().parents[1] / "tools/reference/native-primitive-tracked-admission.json"
        return path, json.loads(path.read_text(encoding="utf-8-sig"))

    def test_portable_proof_works_in_relocated_checkout_with_no_raw_save_or_game(self):
        path, record = self.portable_record()
        with tempfile.TemporaryDirectory(prefix="lyd-tracked-proof-only-") as directory:
            relocated = Path(directory)
            for item in record["evidence_refs"]:
                destination = relocated / item["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(CHECKOUT / item["path"], destination)
            result = validate_portable(path, record, relocated)
            self.assertTrue(result["admitted"])
            self.assertFalse(result["raw_save_rehashed_this_run"])
            self.assertEqual(result["consent_flow_live"], "NOT_RUN")
            self.assertEqual(result["revalidation_level"], "TRACKED_REPORT_AND_EXCERPTS_ONLY")

    def test_portable_proof_missing_file_never_uses_archived_external_fallback(self):
        path, record = self.portable_record()
        with tempfile.TemporaryDirectory(prefix="lyd-no-proof-") as directory:
            with self.assertRaises(FileNotFoundError):
                validate_portable(path, record, Path(directory))

    def test_portable_proof_changed_hash_fails_closed(self):
        path, record = self.portable_record()
        record["evidence_refs"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            validate_portable(path, record, CHECKOUT)

    def test_portable_proof_refuses_absolute_and_escaping_paths(self):
        for bad in ("C:/external/proof.json", "../outside.json"):
            path, record = self.portable_record()
            record["evidence_refs"][0]["path"] = bad
            with self.assertRaisesRegex(ValueError, "checkout"):
                validate_portable(path, record, CHECKOUT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
