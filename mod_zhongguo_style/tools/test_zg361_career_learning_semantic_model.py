#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 tests for the 312-333 Career/Learning semantic authority."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from zg361_career_learning_semantic_model import (
    EXPECTED_IDS,
    HONEST_READINESS,
    SPECS,
    CareerLearningRuntime,
    CaseIdentity,
    DualLedger,
    RedundancyEvidence,
    ResultCode,
    Route,
    SemanticError,
    validate_specs,
)


IDENTITY = CaseIdentity("celestial-duke", "assessed-count", 17, 901)


def runtime(**kwargs: object) -> CareerLearningRuntime:
    return CareerLearningRuntime(IDENTITY, **kwargs)


class CareerLearningSemanticModelTests(unittest.TestCase):
    def test_registry_is_exact_unique_and_honest(self) -> None:
        validate_specs()
        self.assertEqual(tuple(SPECS), EXPECTED_IDS)
        self.assertEqual(len({row.kind for row in SPECS.values()}), 22)
        self.assertEqual(len({row.consumer_key for row in SPECS.values()}), 22)
        self.assertEqual(HONEST_READINESS, "python-l0-model")
        with self.assertRaisesRegex(SemanticError, "cycle_serial"):
            CaseIdentity("owner", "subject", "17", 1)  # type: ignore[arg-type]

    def test_all_a_and_b_routes_create_and_consume_real_objects(self) -> None:
        for mechanism_id in EXPECTED_IDS:
            for route in (Route.A, Route.B):
                with self.subTest(mechanism_id=mechanism_id, route=route):
                    model = runtime()
                    result = model.apply(model.token(mechanism_id), f"{mechanism_id}-{route.name}", route)
                    self.assertEqual(result.code, ResultCode.APPLIED)
                    obj = model.objects[mechanism_id]
                    spec = SPECS[mechanism_id]
                    self.assertEqual(obj.kind, spec.kind)
                    self.assertEqual(obj.identity, IDENTITY)
                    self.assertEqual(obj.consumer_key, spec.consumer_key)
                    self.assertTrue(obj.consumed)
                    self.assertEqual(obj.consumer_revision, 1)
                    self.assertEqual(obj.route, route)
                    self.assertEqual(obj.state, spec.state_a if route is Route.A else spec.state_b)
                    self.assertEqual(obj.relations["owner"], IDENTITY.owner_id)
                    self.assertEqual(obj.relations["subject"], IDENTITY.subject_id)
                    self.assertGreaterEqual(len(obj.facts), 4)
                    self.assertEqual(model.audit, [(mechanism_id, route, spec.consumer_key)])
                    model.assert_invariants()

    def test_a_and_b_are_semantically_distinct_for_every_mechanism(self) -> None:
        for mechanism_id in EXPECTED_IDS:
            with self.subTest(mechanism_id=mechanism_id):
                a = runtime()
                b = runtime()
                a.apply(a.token(mechanism_id), f"a-{mechanism_id}", Route.A)
                b.apply(b.token(mechanism_id), f"b-{mechanism_id}", Route.B)
                a_obj = a.objects[mechanism_id]
                b_obj = b.objects[mechanism_id]
                signature_a = (
                    a_obj.state,
                    tuple(sorted(a_obj.acl.viewers)),
                    a_obj.acl.leaked,
                    tuple(sorted(a_obj.facts.items())),
                    tuple(sorted(a_obj.relations.items())),
                    a.ledger.treasury,
                    a.ledger.personal,
                    tuple(sorted(a.capacity.available.items())),
                    a.market_trust,
                    a.manager_score,
                    a.performance_credit,
                )
                signature_b = (
                    b_obj.state,
                    tuple(sorted(b_obj.acl.viewers)),
                    b_obj.acl.leaked,
                    tuple(sorted(b_obj.facts.items())),
                    tuple(sorted(b_obj.relations.items())),
                    b.ledger.treasury,
                    b.ledger.personal,
                    tuple(sorted(b.capacity.available.items())),
                    b.market_trust,
                    b.manager_score,
                    b.performance_credit,
                )
                self.assertNotEqual(signature_a, signature_b)

    def test_route_c_creates_due_governance_debt_not_fake_business_success(self) -> None:
        for mechanism_id in EXPECTED_IDS:
            with self.subTest(mechanism_id=mechanism_id):
                model = runtime()
                result = model.apply(model.token(mechanism_id), f"c-{mechanism_id}", Route.C)
                self.assertEqual(result.code, ResultCode.APPLIED)
                self.assertNotIn(mechanism_id, model.objects)
                debt = model.debts[mechanism_id]
                self.assertEqual(debt.identity, IDENTITY)
                self.assertEqual(debt.due_cycle, IDENTITY.cycle_serial + 1)
                self.assertEqual(model.records[mechanism_id].state, "deferred-with-debt")
                if SPECS[mechanism_id].deadline_for(Route.C) is not None:
                    self.assertIn(mechanism_id, model.deadlines)
                else:
                    self.assertIsNone(debt.due_day)
        # #333 is explicitly an unbound *funded* course, not a free loophole.
        model = runtime()
        model.apply(model.token(333), "c-333-funded", Route.C)
        self.assertEqual(model.ledger.payments[333], (18, 6))

    def test_duplicate_and_stale_are_no_mutation_for_all_22(self) -> None:
        for mechanism_id in EXPECTED_IDS:
            with self.subTest(mechanism_id=mechanism_id):
                model = runtime()
                token = model.token(mechanism_id)
                model.apply(token, f"once-{mechanism_id}", Route.A)
                frozen = model.snapshot()
                duplicate = model.apply(token, f"once-{mechanism_id}", Route.B)
                self.assertEqual(duplicate.code, ResultCode.DUPLICATE)
                self.assertEqual(model.snapshot(), frozen)
                stale = model.apply(token, f"stale-{mechanism_id}", Route.B)
                self.assertEqual(stale.code, ResultCode.STALE)
                self.assertEqual(model.snapshot(), frozen)

    def test_wrong_identity_is_stale_before_resources_or_objects(self) -> None:
        for mechanism_id in EXPECTED_IDS:
            with self.subTest(mechanism_id=mechanism_id):
                model = runtime()
                token = replace(
                    model.token(mechanism_id),
                    identity=CaseIdentity("other-duke", "assessed-count", 17, 901),
                )
                frozen = model.snapshot()
                result = model.apply(token, f"wrong-owner-{mechanism_id}", Route.A)
                self.assertEqual(result.code, ResultCode.STALE)
                self.assertEqual(model.snapshot(), frozen)

    def test_dual_payment_negative_paths_are_atomic(self) -> None:
        charged = {
            314: (Route.A,),
            321: (Route.A,),
            323: (Route.A, Route.B),
            326: (Route.A, Route.B),
            330: (Route.A, Route.B),
            333: (Route.A, Route.B, Route.C),
        }
        for mechanism_id, routes in charged.items():
            for route in routes:
                with self.subTest(mechanism_id=mechanism_id, route=route):
                    model = runtime()
                    model.ledger = DualLedger(opening_treasury=0, opening_personal=0)
                    frozen = model.snapshot()
                    with self.assertRaisesRegex(SemanticError, "fully funded"):
                        model.apply(model.token(mechanism_id), f"poor-{mechanism_id}-{route}", route)
                    self.assertEqual(model.snapshot(), frozen)

    def test_capacity_negative_paths_are_atomic(self) -> None:
        cases = {
            312: (Route.A, "hc"),
            318: (Route.A, "application_slots"),
            323: (Route.A, "learning_gold"),
            327: (Route.A, "teaching_hours"),
            328: (Route.A, "community_hours"),
            329: (Route.A, "mentor_hours"),
            331: (Route.A, "protected_hours"),
            332: (Route.A, "succession_slots"),
        }
        for mechanism_id, (route, capacity) in cases.items():
            with self.subTest(mechanism_id=mechanism_id):
                model = runtime()
                model.capacity.opening[capacity] = 0
                model.capacity.available[capacity] = 0
                frozen = model.snapshot()
                with self.assertRaisesRegex(SemanticError, f"insufficient {capacity}"):
                    model.apply(model.token(mechanism_id), f"empty-{mechanism_id}", route)
                self.assertEqual(model.snapshot(), frozen)

        no_crisis = runtime(real_crisis=False)
        frozen = no_crisis.snapshot()
        with self.assertRaisesRegex(SemanticError, "real crisis"):
            no_crisis.apply(no_crisis.token(331), "fake-crisis", Route.A)
        self.assertEqual(no_crisis.snapshot(), frozen)

    def test_every_deadline_has_early_stale_resolve_and_duplicate_paths(self) -> None:
        for mechanism_id, spec in SPECS.items():
            route = next((candidate for candidate in Route if spec.deadline_for(candidate) is not None), None)
            self.assertIsNotNone(route, mechanism_id)
            assert route is not None
            with self.subTest(mechanism_id=mechanism_id, route=route):
                model = runtime()
                model.apply(model.token(mechanism_id), f"deadline-{mechanism_id}", route)
                deadline = model.deadlines[mechanism_id]
                frozen = model.snapshot()
                stale_identity = CaseIdentity("other-duke", IDENTITY.subject_id, 17, 901)
                stale = model.resolve_deadline(mechanism_id, now_day=deadline.due_day, identity=stale_identity)
                self.assertEqual(stale.code, ResultCode.STALE)
                self.assertEqual(model.snapshot(), frozen)
                with self.assertRaisesRegex(SemanticError, "cannot resolve early"):
                    model.resolve_deadline(mechanism_id, now_day=deadline.due_day - 1, identity=IDENTITY)
                self.assertEqual(model.snapshot(), frozen)
                resolved = model.resolve_deadline(mechanism_id, now_day=deadline.due_day, identity=IDENTITY)
                self.assertEqual(resolved.code, ResultCode.RESOLVED)
                settled = model.snapshot()
                duplicate = model.resolve_deadline(mechanism_id, now_day=deadline.due_day + 1, identity=IDENTITY)
                self.assertEqual(duplicate.code, ResultCode.DUPLICATE)
                self.assertEqual(model.snapshot(), settled)

    def test_specific_market_objects_and_consumers(self) -> None:
        assertions = {
            312: ("reporting_manager", "legal_hc", "hire_count"),
            313: ("source_manager", "achievement_refs", "immutable"),
            314: ("offered_official", "lump_sum", "performance_delta"),
            315: ("target_manager", "trial_days", "failed_is_low_grade"),
            316: ("mapped_official", "professional_base", "historical_paid_immutable"),
            317: ("owner", "stage", "access_log_rows"),
            318: ("subject", "formal_limit", "used"),
            319: ("releasing_manager", "release_days", "counteroffer_count"),
            320: ("owner", "same_issue", "original_reason_preserved"),
            321: ("alumnus", "consent", "humiliation_history_immutable"),
            322: ("returnee", "old_case_links", "new_cohort"),
        }
        for mechanism_id, (relation, *facts) in assertions.items():
            with self.subTest(mechanism_id=mechanism_id):
                model = runtime()
                model.apply(model.token(mechanism_id), f"market-{mechanism_id}", Route.A)
                obj = model.objects[mechanism_id]
                self.assertIn(relation, obj.relations)
                for fact in facts:
                    self.assertIn(fact, obj.facts)
                self.assertEqual(obj.consumer_key, SPECS[mechanism_id].consumer_key)

    def test_specific_learning_objects_and_consumers(self) -> None:
        assertions = {
            323: ("learner", "gold_allocated", "hours_allocated"),
            324: ("learner", "completion", "application", "outcome"),
            325: ("training_owner", "practical_score", "test_valid"),
            326: ("delegate", "artifact_adopted", "opportunity_cost"),
            327: ("teacher", "teaching_hours", "teacher_share"),
            328: ("maintainer", "artifacts", "adopting_teams"),
            329: ("mentor", "active_mentor_count", "deadline_unchanged"),
            330: ("target_role_owner", "training_days", "role_identity_conserved"),
            331: ("borrower", "borrowed", "real_crisis"),
            332: ("candidate", "safe_simulation", "real_incident"),
            333: ("bound_official", "training_cost", "monthly_reduction"),
        }
        for mechanism_id, (relation, *facts) in assertions.items():
            with self.subTest(mechanism_id=mechanism_id):
                model = runtime()
                model.apply(model.token(mechanism_id), f"learning-{mechanism_id}", Route.A)
                obj = model.objects[mechanism_id]
                self.assertIn(relation, obj.relations)
                for fact in facts:
                    self.assertIn(fact, obj.facts)
                self.assertEqual(obj.consumer_key, SPECS[mechanism_id].consumer_key)

    def test_acl_is_enforced_and_leak_is_a_real_negative_route(self) -> None:
        confidential = runtime()
        confidential.apply(confidential.token(317), "acl-a", Route.A)
        self.assertTrue(confidential.objects[317].acl.can_view("final-interviewer"))
        self.assertFalse(confidential.objects[317].acl.can_view("source-manager"))
        leaked = runtime()
        leaked.apply(leaked.token(317), "acl-b", Route.B)
        self.assertTrue(leaked.objects[317].acl.can_view("source-manager"))
        self.assertTrue(leaked.objects[317].acl.leaked)
        self.assertLess(leaked.manager_score, confidential.manager_score)

    def test_vacancy_hire_and_mentor_and_succession_relations_are_real(self) -> None:
        vacancy = runtime()
        vacancy.apply(vacancy.token(312), "vacancy", Route.A)
        vacancy.hire_vacancy("candidate-77")
        self.assertEqual(vacancy.objects[312].relations["occupant"], "candidate-77")
        self.assertEqual(vacancy.objects[312].state, "filled")
        with self.assertRaisesRegex(SemanticError, "only once"):
            vacancy.hire_vacancy("candidate-88")

        mentor = runtime(mentor_id="expert-from-other-team")
        mentor.apply(mentor.token(329), "mentor", Route.A)
        self.assertEqual(mentor.objects[329].relations["mentor"], "expert-from-other-team")
        self.assertEqual(mentor.objects[329].relations["mentee"], IDENTITY.subject_id)

        succession = runtime()
        succession.apply(succession.token(332), "succession", Route.A)
        self.assertEqual(succession.objects[332].relations["incumbent"], IDENTITY.owner_id)
        self.assertEqual(succession.objects[332].relations["candidate"], IDENTITY.subject_id)
        self.assertFalse(succession.objects[332].facts["real_incident"])

    def test_completion_application_outcome_and_training_recovery_are_ordered(self) -> None:
        complete_only = runtime()
        complete_only.apply(complete_only.token(324), "course-b", Route.B)
        self.assertTrue(complete_only.objects[324].facts["completion"])
        self.assertFalse(complete_only.objects[324].facts["application"])
        self.assertFalse(complete_only.objects[324].facts["outcome"])
        self.assertEqual(complete_only.performance_credit, 0)

        applied = runtime()
        applied.apply(applied.token(324), "course-a", Route.A)
        self.assertTrue(applied.objects[324].facts["application"])
        self.assertTrue(applied.objects[324].facts["outcome"])
        self.assertEqual(applied.performance_credit, 12)

        recovery = runtime()
        recovery.apply(recovery.token(333), "contract-b", Route.B)
        due = recovery.deadlines[333].due_day
        recovery.resolve_deadline(333, now_day=due, identity=IDENTITY)
        self.assertEqual(recovery.objects[333].facts["recovered"], 18)
        self.assertEqual(recovery.ledger.recoveries[333], (13, 5))
        recovery.ledger.assert_conserved()

        exempt = runtime()
        exempt.apply(exempt.token(333), "contract-b-layoff", Route.B)
        evidence = RedundancyEvidence(
            subject_id=IDENTITY.subject_id,
            reason_code=1,
            treasury_paid=50,
            personal_received=50,
            actual_exit=True,
            hc_released=True,
            state=3,
        )
        exempt.resolve_deadline(
            333,
            now_day=exempt.deadlines[333].due_day,
            identity=IDENTITY,
            redundancy_evidence=evidence,
        )
        self.assertTrue(exempt.objects[333].facts["organization_layoff_exempt"])
        self.assertEqual(exempt.objects[333].facts["outstanding"], 0)
        self.assertNotIn(333, exempt.ledger.recoveries)

    def test_full_a_and_b_portfolios_remain_conserved(self) -> None:
        for route in (Route.A, Route.B):
            with self.subTest(route=route):
                model = runtime()
                for mechanism_id in EXPECTED_IDS:
                    result = model.apply(
                        model.token(mechanism_id),
                        f"portfolio-{route.name}-{mechanism_id}",
                        route,
                    )
                    self.assertEqual(result.code, ResultCode.APPLIED)
                self.assertEqual(len(model.objects), 22)
                self.assertEqual(len(model.audit), 22)
                model.assert_invariants()


if __name__ == "__main__":
    unittest.main()
