#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Executable semantic tests for the nineteen native B2 mechanisms."""

from __future__ import annotations

import unittest

from zg361_b2_runtime_data import CaseIdentity, PolicyRoute
import zg361_b2_semantic_model as model


def identity(
    *, owner: str = "manager", subject: str = "official", cycle: int = 7, case: int = 11
) -> CaseIdentity:
    return CaseIdentity(owner, subject, cycle, case)


def groups(**overrides: bool) -> dict[str, bool]:
    values = {name: False for name in model.FAIRNESS_DIMENSIONS}
    values.update(overrides)
    return values


class NativeOwnershipAndCaseBookTests(unittest.TestCase):
    def test_exact_native_ids_and_no_feedback_pip_overlap(self) -> None:
        expected = tuple(range(14, 18)) + tuple(range(69, 82)) + (358, 359)
        self.assertEqual(model.NATIVE_B2_IDS, expected)
        self.assertEqual(len(model.NATIVE_B2_IDS), 19)
        self.assertTrue(
            set(model.NATIVE_B2_IDS).isdisjoint(model.DELEGATED_FEEDBACK_PIP_IDS)
        )
        self.assertTrue(model.REFERENCE_ONLY)

    def test_every_native_id_has_stable_a_b_case_and_c_debt_only(self) -> None:
        for mechanism_id in model.NATIVE_B2_IDS:
            with self.subTest(mechanism=mechanism_id):
                for route in (PolicyRoute.A, PolicyRoute.B):
                    book = model.NativeCaseBook()
                    key = identity(case=mechanism_id * 10 + route.value.__len__())
                    opened = book.open(
                        mechanism_id, key, route, initial_state="OPEN"
                    )
                    self.assertTrue(opened.applied)
                    self.assertIn((mechanism_id, key), book.cases)
                    self.assertNotIn((mechanism_id, key), book.debts)
                    case = book.cases[(mechanism_id, key)]
                    token = case.token()
                    self.assertFalse(
                        book.consume(
                            (mechanism_id, key, "STALE", token[3]),
                            new_state="DONE",
                        ).applied
                    )
                    self.assertTrue(book.consume(token, new_state="DONE").applied)
                    self.assertFalse(book.consume(token, new_state="DONE").applied)

                book = model.NativeCaseBook()
                key = identity(case=mechanism_id * 10 + 3)
                opened = book.open(
                    mechanism_id, key, PolicyRoute.C, initial_state="OPEN"
                )
                self.assertEqual(opened.code, "policy-debt-only")
                self.assertNotIn((mechanism_id, key), book.cases)
                self.assertIn((mechanism_id, key), book.debts)
                self.assertFalse(
                    book.open(
                        mechanism_id, key, PolicyRoute.C, initial_state="OPEN"
                    ).applied
                )
                self.assertEqual(book.consume_debt(current_cycle=key.cycle_serial), ())
                self.assertEqual(
                    len(book.consume_debt(current_cycle=key.cycle_serial + 1)), 1
                )

    def test_delegated_feedback_pip_ids_are_rejected(self) -> None:
        book = model.NativeCaseBook()
        for mechanism_id in model.DELEGATED_FEEDBACK_PIP_IDS:
            with self.subTest(mechanism=mechanism_id):
                result = book.open(
                    mechanism_id,
                    identity(case=mechanism_id),
                    PolicyRoute.A,
                    initial_state="OPEN",
                )
                self.assertEqual(result.code, "foreign-owner")


class FormalSettlementTests(unittest.TestCase):
    def test_route_c_is_blocked_before_settlement_and_posts_one_debt(self) -> None:
        book = model.NativeCaseBook()
        gate = model.FormalSettlementGate(book)
        key = identity(case=6901)
        result = gate.authorize(key, PolicyRoute.C)
        self.assertEqual(result.code, "blocked")
        self.assertFalse(gate.decisions[key])
        self.assertNotIn((69, key), book.cases)
        self.assertIn((69, key), book.debts)
        self.assertFalse(gate.authorize(key, PolicyRoute.C).applied)

    def test_routes_a_and_b_authorize_but_do_not_settle_resources(self) -> None:
        for route in (PolicyRoute.A, PolicyRoute.B):
            with self.subTest(route=route):
                book = model.NativeCaseBook()
                gate = model.FormalSettlementGate(book)
                key = identity(case=6900 + (1 if route == PolicyRoute.A else 2))
                self.assertEqual(gate.authorize(key, route).code, "settlement-allowed")
                self.assertTrue(gate.decisions[key])
                self.assertEqual(book.cases[(69, key)].state, "PREPARED")


class ReviewerRotationTests(unittest.TestCase):
    def test_grounded_recusal_replaces_once_and_invalid_reason_spends_nothing(self) -> None:
        key = identity()
        rotation = model.ReviewerRotation(
            key,
            (
                model.ReviewerCandidate(
                    "reviewer-a", conflicts_with=frozenset({key.subject_id})
                ),
                model.ReviewerCandidate("reviewer-b"),
            ),
            PolicyRoute.A,
        )
        self.assertEqual(rotation.assign().code, "independent-assigned")
        self.assertFalse(
            rotation.recuse(party_id=key.owner_id, reason="unsupported").applied
        )
        self.assertFalse(rotation.owner_recusal_used)
        self.assertEqual(
            rotation.recuse(party_id=key.subject_id, reason="documented-rivalry").code,
            "replaced",
        )
        self.assertEqual(rotation.reviewer_id, "reviewer-b")
        self.assertTrue(rotation.subject_recusal_used)
        self.assertFalse(
            rotation.recuse(party_id=key.subject_id, reason="again").applied
        )

    def test_route_b_is_disclosed_self_correction_and_conclusion_is_idempotent(self) -> None:
        rotation = model.ReviewerRotation(
            identity(), (model.ReviewerCandidate("reviewer-a"),), PolicyRoute.B
        )
        self.assertEqual(rotation.assign().code, "self-correction-disclosed")
        self.assertFalse(rotation.independent)
        self.assertEqual(rotation.reviewer_id, rotation.identity.owner_id)
        self.assertTrue(
            rotation.conclude(evidence_revision=2, outcome="UPHELD").applied
        )
        self.assertFalse(
            rotation.conclude(evidence_revision=2, outcome="UPHELD").applied
        )
        self.assertEqual(rotation.conclusion.identity, rotation.identity)


class FairnessDashboardTests(unittest.TestCase):
    def test_route_c_and_incomplete_dimensions_create_no_sample(self) -> None:
        dashboard = model.FairnessDashboard()
        key = identity()
        self.assertFalse(
            dashboard.record(
                key, route=PolicyRoute.C, groups=groups(), bottom=True
            ).applied
        )
        self.assertFalse(
            dashboard.record(
                key,
                route=PolicyRoute.A,
                groups={"newcomer": True},
                bottom=True,
            ).applied
        )
        self.assertEqual(dashboard.samples, {})

    def test_full_denominators_duplicate_guard_and_small_sample_suppression(self) -> None:
        dashboard = model.FairnessDashboard()
        for index in range(6):
            key = identity(subject=f"official-{index}", case=100 + index)
            positive = index < 3
            self.assertTrue(
                dashboard.record(
                    key,
                    route=PolicyRoute.A,
                    groups=groups(
                        newcomer=positive,
                        transfer=positive,
                        kin=False,
                        faction=False,
                        landed=True,
                        governor=False,
                    ),
                    bottom=index % 2 == 0,
                ).applied
            )
            self.assertFalse(
                dashboard.record(
                    key,
                    route=PolicyRoute.A,
                    groups=groups(),
                    bottom=False,
                ).applied
            )
            self.assertTrue(dashboard.resolve(key, corrected=index < 2).applied)
            self.assertFalse(dashboard.resolve(key, corrected=False).applied)
        self.assertIn("newcomer", dashboard.anomalies())
        self.assertIn("transfer", dashboard.anomalies())
        self.assertNotIn("kin", dashboard.anomalies())
        self.assertNotIn("faction", dashboard.anomalies())


class SkipLevelAndMetricTests(unittest.TestCase):
    def test_skip_level_uses_bounded_seat_and_remands_to_next_direct_result(self) -> None:
        pool = model.SkipLevelSeatPool(1)
        key = identity(case=7901)
        other = identity(subject="other", case=7902)
        self.assertTrue(pool.reserve(key))
        self.assertFalse(pool.reserve(key))
        self.assertFalse(pool.reserve(other))
        case = model.SkipLevelCase(key, PolicyRoute.A, "skip-manager")
        self.assertEqual(
            case.resolve(evidence_strength=2, seats=pool).code,
            "remanded-to-direct-manager",
        )
        self.assertFalse(case.direct_grade_write)
        self.assertEqual(pool.reservations, set())
        self.assertFalse(
            case.consume_next_result(identity(owner="other", cycle=8, case=12)).applied
        )
        self.assertEqual(
            case.consume_next_result(identity(cycle=8, case=12)).code,
            "consumed-by-next-direct-result",
        )
        self.assertEqual(case.remand_consumer_case, 12)

    def test_metric_defect_routes_and_later_suppression_liability(self) -> None:
        key = identity(case=8001)
        suppressed = model.MetricDefectCase(
            key, PolicyRoute.B, "defect:8001", 4, "hash:one"
        )
        self.assertEqual(
            suppressed.resolve(supported=True).code,
            "suppressed-evidence-preserved",
        )
        self.assertFalse(
            suppressed.consume_later(
                identity(owner="wrong", cycle=8, case=13), repeated_defect_type=4
            ).applied
        )
        self.assertEqual(
            suppressed.consume_later(
                identity(cycle=8, case=13), repeated_defect_type=4
            ).code,
            "suppression-liability",
        )
        self.assertEqual(suppressed.consumer_case, 13)

        repaired = model.MetricDefectCase(
            identity(case=8002), PolicyRoute.A, "defect:8002", 3, "hash:two"
        )
        self.assertEqual(repaired.resolve(supported=True).code, "repaired")
        self.assertEqual(
            repaired.consume_later(
                identity(cycle=8, case=14), repeated_defect_type=None
            ).code,
            "later-version-verified",
        )
        deferred = model.MetricDefectCase(
            identity(case=8003), PolicyRoute.C, "defect:8003", 2, "hash:three"
        )
        self.assertEqual(deferred.resolve(supported=True).code, "route-c-no-ticket")


class InformationAccessTests(unittest.TestCase):
    def test_acl_changes_visibility_but_never_transfers_grade_authority(self) -> None:
        key = identity()
        ledger = model.InformationAccessLedger(key, key.owner_id)
        self.assertIsNone(
            ledger.read(
                actor_id="intruder",
                role=model.AccessRole.SUBJECT,
                route=PolicyRoute.A,
            )
        )
        subject = ledger.read(
            actor_id=key.subject_id,
            role=model.AccessRole.SUBJECT,
            route=PolicyRoute.A,
        )
        self.assertFalse(subject.raw_evidence)
        central = ledger.read(
            actor_id="central",
            role=model.AccessRole.CENTRAL_REVIEW,
            route=PolicyRoute.B,
        )
        self.assertTrue(central.raw_evidence)
        self.assertFalse(ledger.can_write_grade("central"))
        self.assertFalse(ledger.can_write_grade(key.subject_id))
        self.assertTrue(ledger.can_write_grade(key.owner_id))


if __name__ == "__main__":
    unittest.main()
