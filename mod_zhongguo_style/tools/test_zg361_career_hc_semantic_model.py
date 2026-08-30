#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Behavioral L0 tests for Career/HC runtime objects and conservation."""

from __future__ import annotations

from dataclasses import replace
import unittest

from zg361_career_hc_semantic_model import (
    CK3_LIVE,
    DUAL_PAYMENT_IDS,
    EXPECTED_IDS,
    HC_DEST_A,
    HC_DEST_B,
    READINESS,
    SEMANTIC_SPECS,
    CapacityLedger,
    CapacityState,
    CareerHcSemanticRuntime,
    CaseIdentity,
    ObjectKind,
    ResultCode,
    Route,
    SemanticError,
)


def runtime() -> CareerHcSemanticRuntime:
    return CareerHcSemanticRuntime(CaseIdentity("duke-owner", "count-subject", 17, 301))


class RegistryTests(unittest.TestCase):
    def test_registry_is_exactly_the_frozen_forty_four_ids(self) -> None:
        self.assertEqual(tuple(sorted(SEMANTIC_SPECS)), EXPECTED_IDS)
        self.assertEqual(len(SEMANTIC_SPECS), 44)
        self.assertEqual(set(HC_DEST_A), set(range(98, 106)))
        self.assertEqual(set(HC_DEST_B), set(range(98, 106)))

    def test_every_id_has_typed_objects_distinct_routes_and_unique_consumer(self) -> None:
        consumers: set[str] = set()
        for mechanism_id, spec in SEMANTIC_SPECS.items():
            with self.subTest(mechanism_id=mechanism_id):
                self.assertTrue(spec.object_kinds)
                self.assertNotEqual(spec.a_state, spec.b_state)
                self.assertNotIn("receipt", spec.consumer_key)
                self.assertIn(f"m{mechanism_id:03d}", spec.consumer_key)
                self.assertNotIn(spec.consumer_key, consumers)
                consumers.add(spec.consumer_key)

    def test_registry_contains_real_career_and_hc_object_families(self) -> None:
        present = {
            kind
            for spec in SEMANTIC_SPECS.values()
            for kind in spec.object_kinds
        }
        self.assertEqual(present, set(ObjectKind))
        for required in (
            ObjectKind.VACANCY,
            ObjectKind.HC_SLOT,
            ObjectKind.CANDIDATE,
            ObjectKind.INCUMBENT,
            ObjectKind.SUCCESSION,
            ObjectKind.BACKFILL,
        ):
            self.assertIn(required, present)

    def test_readiness_does_not_claim_ck3_or_mcp_live(self) -> None:
        self.assertEqual(READINESS, "python-l0-reference-only")
        self.assertIs(CK3_LIVE, False)


class RouteAndIdentityTests(unittest.TestCase):
    def test_all_evidence_routes_create_bound_objects_and_invoke_consumers(self) -> None:
        state = runtime()
        for mechanism_id in EXPECTED_IDS:
            result = state.apply(
                state.token(mechanism_id),
                f"a-{mechanism_id:03d}",
                Route.EVIDENCE,
            )
            self.assertEqual(result.code, ResultCode.APPLIED)
        self.assertEqual(len(state.audit), 44)
        self.assertFalse(state.debts)
        for mechanism_id, spec in SEMANTIC_SPECS.items():
            record = state.records[mechanism_id]
            with self.subTest(mechanism_id=mechanism_id):
                self.assertEqual(record.identity, state.identity)
                self.assertEqual(record.state, spec.a_state)
                self.assertEqual(record.route, Route.EVIDENCE)
                self.assertEqual(record.consumer_key, spec.consumer_key)
                self.assertEqual(record.revision, 1)
                for kind in spec.object_kinds:
                    business_object = state.objects[f"{kind.value}:{mechanism_id:03d}"]
                    self.assertEqual(business_object.identity, state.identity)
                    if mechanism_id == 124 and kind is ObjectKind.CANDIDATE:
                        self.assertEqual(business_object.person_id, state.q_candidate_id)
                        self.assertNotEqual(business_object.person_id, state.identity.subject_id)
                    else:
                        self.assertEqual(business_object.person_id, state.identity.subject_id)
                    self.assertEqual(business_object.consumer_key, spec.consumer_key)
                    self.assertEqual(business_object.state, spec.a_state)
        state.assert_conserved()

    def test_all_political_routes_create_distinct_objects_and_real_debt(self) -> None:
        state = runtime()
        for mechanism_id in EXPECTED_IDS:
            state.apply(state.token(mechanism_id), f"b-{mechanism_id:03d}", Route.POLITICAL)
        for mechanism_id, spec in SEMANTIC_SPECS.items():
            with self.subTest(mechanism_id=mechanism_id):
                record = state.records[mechanism_id]
                self.assertEqual(record.state, spec.b_state)
                self.assertEqual(record.route, Route.POLITICAL)
                for kind in spec.object_kinds:
                    self.assertEqual(
                        state.objects[f"{kind.value}:{mechanism_id:03d}"].state,
                        spec.b_state,
                    )
        # B is a playable alternative, but its political shortcuts must leave
        # concrete debt on the mechanisms whose choice text promises it.
        for mechanism_id in (19, 20, 23, 25, 92, 96, 97, 106, 108, 112, 114, 116, 121, 124, 128):
            self.assertEqual(state.debts[mechanism_id], 1)
        state.assert_conserved()

    def test_all_defer_routes_create_only_debt_and_no_success_object_or_spend(self) -> None:
        state = runtime()
        opening_capacities = {
            key: ledger.snapshot() for key, ledger in state.capacities.items()
        }
        opening_resources = state.resources.snapshot()
        for mechanism_id in EXPECTED_IDS:
            state.apply(state.token(mechanism_id), f"c-{mechanism_id:03d}", Route.DEFER)
        self.assertFalse(state.objects)
        self.assertEqual(state.resources.snapshot(), opening_resources)
        self.assertEqual(
            {key: ledger.snapshot() for key, ledger in state.capacities.items()},
            opening_capacities,
        )
        self.assertEqual(state.debts, {mechanism_id: 1 for mechanism_id in EXPECTED_IDS})
        self.assertTrue(all(row.state == "deferred-with-debt" for row in state.records.values()))

    def test_duplicate_operation_is_an_exact_no_op(self) -> None:
        state = runtime()
        token = state.token(22)
        first = state.apply(token, "one-operation", Route.EVIDENCE)
        snapshot = state.snapshot()
        duplicate = state.apply(token, "one-operation", Route.POLITICAL)
        self.assertTrue(first.applied)
        self.assertFalse(duplicate.applied)
        self.assertEqual(duplicate.code, ResultCode.DUPLICATE)
        self.assertEqual(state.snapshot(), snapshot)

    def test_stale_owner_subject_cycle_case_and_revision_are_exact_no_ops(self) -> None:
        mutations = (
            {"owner_id": "other-owner"},
            {"subject_id": "other-subject"},
            {"cycle_serial": 18},
            {"case_serial": 302},
        )
        for index, mutation in enumerate(mutations):
            state = runtime()
            token = state.token(24)
            stale = replace(token, identity=replace(token.identity, **mutation))
            before = state.snapshot()
            result = state.apply(stale, f"stale-{index}", Route.EVIDENCE)
            self.assertEqual(result.code, ResultCode.STALE)
            self.assertEqual(state.snapshot(), before)
        state = runtime()
        token = state.token(24)
        state.apply(token, "first", Route.EVIDENCE)
        before = state.snapshot()
        result = state.apply(token, "new-serial-old-revision", Route.EVIDENCE)
        self.assertEqual(result.code, ResultCode.STALE)
        self.assertEqual(state.snapshot(), before)

    def test_invalid_id_route_and_serial_are_typed_red_without_mutation(self) -> None:
        state = runtime()
        before = state.snapshot()
        with self.assertRaises(SemanticError):
            state.token(999)
        with self.assertRaises(SemanticError):
            state.apply(state.token(19), "", Route.EVIDENCE)
        with self.assertRaises(SemanticError):
            state.apply(state.token(19), "bad-route", 9)  # type: ignore[arg-type]
        self.assertEqual(state.snapshot(), before)


class BusinessObjectTests(unittest.TestCase):
    def test_hc_slots_have_identity_preserving_terminal_states_and_conserve_eight(self) -> None:
        for route, expected in (
            (Route.EVIDENCE, HC_DEST_A),
            (Route.POLITICAL, HC_DEST_B),
        ):
            state = runtime()
            for mechanism_id in range(98, 106):
                state.apply(state.token(mechanism_id), f"hc-{route}-{mechanism_id}", route)
            self.assertEqual(state.hc_slots, dict(expected))
            self.assertEqual(state.capacities["hc"].available, 0)
            self.assertEqual(
                sum(state.capacities["hc"].value(item) for item in CapacityState),
                8,
            )
            state.assert_conserved()

    def test_vacancy_candidate_incumbent_succession_and_backfill_are_not_aliases(self) -> None:
        state = runtime()
        for mechanism_id in (24, 106, 107, 111, 114, 115, 124):
            state.apply(state.token(mechanism_id), f"objects-{mechanism_id}", Route.EVIDENCE)
        kinds = {value.kind for value in state.objects.values()}
        self.assertTrue(
            {
                ObjectKind.VACANCY,
                ObjectKind.CANDIDATE,
                ObjectKind.INCUMBENT,
                ObjectKind.SUCCESSION,
                ObjectKind.BACKFILL,
            }.issubset(kinds)
        )
        self.assertEqual(state.succession_incumbent_id, state.identity.owner_id)
        self.assertEqual(state.succession_candidate_id, state.identity.subject_id)
        self.assertEqual(state.backfill_owner_id, state.identity.owner_id)

    def test_promotion_and_backfill_capacity_move_without_minting(self) -> None:
        state = runtime()
        for mechanism_id in (22, 24, 25, 96, 97, 114, 119):
            state.apply(state.token(mechanism_id), f"capacity-{mechanism_id}", Route.EVIDENCE)
        self.assertEqual(state.capacities["d_hc"].snapshot(), (2, 0, 1, 1, 0, 0))
        self.assertEqual(state.capacities["promotion"].snapshot(), (1, 0, 0, 1, 0, 0))
        self.assertEqual(state.capacities["backfill"].snapshot(), (1, 0, 0, 1, 0, 0))

    def test_manager_successor_and_hours_are_consumed_in_order(self) -> None:
        state = runtime()
        for mechanism_id in (121, 124, 125, 127, 128):
            state.apply(state.token(mechanism_id), f"manager-{mechanism_id}", Route.EVIDENCE)
        self.assertTrue(state.manager_successor_accepted)
        self.assertEqual(state.capacities["manager_team"].snapshot(), (3, 1, 0, 2, 0, 0))
        self.assertEqual(state.capacities["manager_hc"].snapshot(), (4, 1, 2, 1, 0, 0))
        self.assertEqual(state.capacities["crisis_hours"].snapshot(), (100, 0, 60, 40, 0, 0))
        self.assertEqual((state.q_crisis_manager_hours, state.q_crisis_delegated_hours), (40, 60))
        self.assertEqual(state.next_cycle_policy, "evidence-adjusted")
        self.assertEqual(state.q_policy_effective_cycle, state.identity.cycle_serial + 1)

    def test_q121_to_q128_publish_real_distinct_role_objects(self) -> None:
        state = runtime()
        for mechanism_id in range(121, 129):
            state.apply(state.token(mechanism_id), f"q-a-{mechanism_id}", Route.EVIDENCE)
        q124 = {
            kind: state.objects[f"{kind.value}:124"]
            for kind in (
                ObjectKind.VACANCY,
                ObjectKind.HC_SLOT,
                ObjectKind.CANDIDATE,
                ObjectKind.INCUMBENT,
                ObjectKind.SUCCESSION,
                ObjectKind.BACKFILL,
            )
        }
        self.assertEqual(q124[ObjectKind.INCUMBENT].person_id, state.identity.subject_id)
        self.assertNotEqual(
            q124[ObjectKind.CANDIDATE].person_id,
            q124[ObjectKind.INCUMBENT].person_id,
        )
        self.assertEqual(q124[ObjectKind.SUCCESSION].candidate_id, state.q_candidate_id)
        self.assertEqual(q124[ObjectKind.SUCCESSION].incumbent_id, state.q_incumbent_id)
        self.assertTrue(
            all(item.identity == state.identity and item.object_revision == 1 for item in q124.values())
        )
        self.assertEqual(
            (
                state.q_vacancy_id,
                state.q_hc_slot_id,
                state.q_succession_id,
                state.q_backfill_id,
            ),
            (
                f"vacancy:{state.identity.case_serial}:124",
                f"hc:{state.identity.case_serial}:124",
                f"succession:{state.identity.case_serial}:124",
                f"backfill:{state.identity.case_serial}:124",
            ),
        )

    def test_q_a_b_c_have_distinct_business_outcomes_without_capacity_minting(self) -> None:
        evidence = runtime()
        political = runtime()
        deferred = runtime()
        for mechanism_id in range(121, 129):
            evidence.apply(evidence.token(mechanism_id), f"qa-{mechanism_id}", Route.EVIDENCE)
            political.apply(political.token(mechanism_id), f"qb-{mechanism_id}", Route.POLITICAL)
            deferred.apply(deferred.token(mechanism_id), f"qc-{mechanism_id}", Route.DEFER)
        self.assertEqual(evidence.q_score_weights, (40, 30, 30))
        self.assertEqual(evidence.q_survey_factors, 6)
        self.assertEqual(evidence.q_survey_credibility, 100)
        self.assertEqual(evidence.q_values_quadrant, "double-high")
        self.assertEqual(political.q_score_components, (90, 35, 20))
        self.assertEqual(political.q_survey_factors, 1)
        self.assertEqual(political.q_survey_credibility, 25)
        self.assertEqual(political.q_values_quadrant, "wild-dog")
        self.assertEqual((political.q_crisis_manager_hours, political.q_crisis_delegated_hours), (100, 0))
        self.assertFalse(deferred.objects)
        self.assertIsNone(deferred.q_vacancy_id)
        self.assertIsNone(deferred.q_policy_effective_cycle)
        for state in (evidence, political, deferred):
            state.assert_conserved()

    def test_q_duplicate_and_all_five_stale_dimensions_are_exact_no_ops(self) -> None:
        state = runtime()
        token = state.token(124)
        state.apply(token, "q124-once", Route.EVIDENCE)
        frozen = state.snapshot()
        duplicate = state.apply(token, "q124-once", Route.POLITICAL)
        stale_revision = state.apply(token, "q124-new-serial", Route.POLITICAL)
        self.assertEqual(duplicate.code, ResultCode.DUPLICATE)
        self.assertEqual(stale_revision.code, ResultCode.STALE)
        self.assertEqual(state.snapshot(), frozen)

        for field, value in (
            ("owner_id", "wrong-owner"),
            ("subject_id", "wrong-subject"),
            ("cycle_serial", 99),
            ("case_serial", 999),
        ):
            candidate = runtime()
            candidate_token = candidate.token(127)
            stale = replace(
                candidate_token,
                identity=replace(candidate_token.identity, **{field: value}),
            )
            before = candidate.snapshot()
            self.assertEqual(
                candidate.apply(stale, f"stale-{field}", Route.EVIDENCE).code,
                ResultCode.STALE,
            )
            self.assertEqual(candidate.snapshot(), before)

    def test_q_capacity_exhaustion_cannot_publish_a_partial_layer_object(self) -> None:
        state = runtime()
        state.apply(state.token(121), "large-team", Route.POLITICAL)
        state.apply(state.token(124), "promotion-risk", Route.POLITICAL)
        self.assertEqual(state.capacities["manager_hc"].available, 0)
        before = state.snapshot()
        with self.assertRaises(SemanticError):
            state.apply(state.token(127), "unfunded-layer", Route.EVIDENCE)
        self.assertEqual(state.snapshot(), before)
        self.assertNotIn("hc-slot:127", state.objects)
        self.assertNotIn("vacancy:127", state.objects)

    def test_release_deadline_is_bounded_and_only_b_uses_the_extension(self) -> None:
        evidence = runtime()
        evidence.apply(evidence.token(116), "release-a", Route.EVIDENCE)
        self.assertEqual(evidence.release_days, 90)
        political = runtime()
        political.apply(political.token(116), "release-b", Route.POLITICAL)
        self.assertEqual(political.release_days, 150)
        deferred = runtime()
        deferred.apply(deferred.token(116), "release-c", Route.DEFER)
        self.assertIsNone(deferred.release_days)

    def test_all_funded_actions_debit_both_ledgers_once(self) -> None:
        state = runtime()
        for mechanism_id in sorted(DUAL_PAYMENT_IDS):
            state.apply(state.token(mechanism_id), f"funded-{mechanism_id}", Route.EVIDENCE)
        total = 5 * len(DUAL_PAYMENT_IDS)
        self.assertEqual(
            state.resources.snapshot(),
            (100 - total, 100 - total, total, total),
        )
        state.assert_conserved()

    def test_jingcha_hc_defense_is_free_on_both_non_defer_routes(self) -> None:
        for route in (Route.EVIDENCE, Route.POLITICAL):
            state = runtime()
            before = state.resources.snapshot()
            state.apply(state.token(23), f"jingcha-{route}", route)
            self.assertEqual(state.resources.snapshot(), before)

    def test_capacity_negative_and_nonconserving_states_are_rejected(self) -> None:
        ledger = CapacityLedger(1)
        ledger.move(CapacityState.AVAILABLE, CapacityState.RESERVED)
        before = ledger.snapshot()
        with self.assertRaises(SemanticError):
            ledger.move(CapacityState.AVAILABLE, CapacityState.OCCUPIED)
        self.assertEqual(ledger.snapshot(), before)
        ledger.available = 1
        with self.assertRaises(SemanticError):
            ledger.assert_conserved()


if __name__ == "__main__":
    unittest.main()
