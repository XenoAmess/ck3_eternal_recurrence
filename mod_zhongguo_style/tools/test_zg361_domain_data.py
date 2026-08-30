#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 tests for the 38-domain and 361-item phase-two runtime plan."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from gen_361_mechanisms import MOD_ROOT, outputs
from zg361_domain_data import (
    DOMAIN_SPECS,
    PERMISSION_BOUNDARY,
    STALE_GUARD,
    build_runtime_plans,
    domain_for_id,
    validate_domain_graphs,
    validate_runtime_coverage,
)
from zg361_mechanism_data import load_mechanisms
from zg361_operation_registry import (
    DOMAIN_RECIPE_PRIMITIVES,
    MECHANISM_PRIMITIVE_OVERRIDES,
    OperationKind,
    PRIMITIVE_WHITELIST,
    STAGE_DISPATCHER_PRIMITIVES,
    compile_choice_ops,
    render_deadline,
    render_feedback_projection,
    render_transaction,
    render_transition_guard,
)


class DomainRuntimePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mechanisms = load_mechanisms(MOD_ROOT)
        cls.plans = build_runtime_plans(cls.mechanisms)
        cls.by_id = {int(plan["id"]): plan for plan in cls.plans}

    def test_exact_domain_and_id_coverage(self) -> None:
        validate_domain_graphs()
        self.assertEqual(len(DOMAIN_SPECS), 38)
        self.assertEqual(
            [mechanism_id for domain in DOMAIN_SPECS for mechanism_id in domain.ids],
            list(range(1, 362)),
        )
        self.assertEqual([plan["id"] for plan in self.plans], list(range(1, 362)))
        self.assertEqual({domain.phase for domain in DOMAIN_SPECS}, {1, 2, 3, 4})

    def test_every_domain_graph_has_reachable_terminal(self) -> None:
        for domain in DOMAIN_SPECS:
            with self.subTest(domain=domain.code):
                cursor = domain.states[0]
                for old, new, hook in domain.transitions:
                    self.assertEqual(cursor, old)
                    self.assertTrue(hook)
                    cursor = new
                self.assertEqual((cursor,), domain.terminal_states)

    def test_every_mechanism_has_three_typed_routes(self) -> None:
        operation_keys = {domain.operation_key for domain in DOMAIN_SPECS}
        for plan in self.plans:
            with self.subTest(mechanism=plan["id"]):
                self.assertEqual(tuple(plan["choices"]), ("a", "b", "c"))
                self.assertIn(plan["operation_key"], operation_keys)
                for route in plan["choices"].values():
                    self.assertTrue(route["gameplay_effects"])
                    self.assertTrue(route["visible_feedback"])
                    self.assertIn(
                        route["gameplay_effects"][0]["op"], operation_keys
                    )

    def test_defer_routes_have_full_stale_guard(self) -> None:
        for plan in self.plans:
            with self.subTest(mechanism=plan["id"]):
                deadline = plan["choices"]["c"]["deadline"]
                self.assertEqual(deadline["kind"], "scheduled_event")
                self.assertEqual(tuple(deadline["stale_guard"]), STALE_GUARD)
                for choice in ("a", "b"):
                    self.assertEqual(plan["choices"][choice]["deadline"]["kind"], "none")

    def test_permission_boundary_never_promotes_counts_or_barons(self) -> None:
        self.assertIn("duke-or-higher", PERMISSION_BOUNDARY["player_manager"])
        self.assertIn("duke-or-higher", PERMISSION_BOUNDARY["ai_manager"])
        self.assertIn("subject-only", PERMISSION_BOUNDARY["count_baron"])
        for plan in self.plans:
            self.assertEqual(plan["actor_role"], "eligible_manager")
            self.assertIn("duke_or_higher_manager", plan["applicability"])

    def test_compensation_plan_keeps_treasury_and_personal_gold_separate(self) -> None:
        dual_entry = []
        for mechanism, plan in zip(self.mechanisms, self.plans, strict=True):
            if mechanism.profile != "compensation":
                continue
            currencies = {
                transaction["currency"]
                for transaction in plan["choices"]["a"]["transactions"]
            }
            if {"treasury_gold", "personal_gold"}.issubset(currencies):
                dual_entry.append(mechanism.id)
        self.assertTrue(dual_entry)
        self.assertIn(82, dual_entry)
        self.assertIn(278, dual_entry)

    def test_empty_transactions_are_explained(self) -> None:
        for plan in self.plans:
            for choice_name, route in plan["choices"].items():
                with self.subTest(mechanism=plan["id"], choice=choice_name):
                    if not route["transactions"]:
                        self.assertTrue(
                            route["acceptance"]["no_conserved_resource_reason"]
                        )

    def test_mutated_stale_guard_is_rejected(self) -> None:
        plans = copy.deepcopy(self.plans)
        plans[0]["choices"]["c"]["deadline"]["stale_guard"] = ["owner"]
        with self.assertRaisesRegex(ValueError, "incomplete stale guard"):
            validate_runtime_coverage(self.mechanisms, DOMAIN_SPECS, plans)

    def test_foreign_transaction_currency_is_rejected(self) -> None:
        plans = copy.deepcopy(self.plans)
        route = next(
            route
            for plan in plans
            for route in plan["choices"].values()
            if route["transactions"]
        )
        route["transactions"][0]["currency"] = "imaginary_currency"
        with self.assertRaisesRegex(ValueError, "foreign resource"):
            validate_runtime_coverage(self.mechanisms, DOMAIN_SPECS, plans)

    def test_generated_contract_files_partition_361_once(self) -> None:
        rendered = outputs(self.mechanisms)
        domain_path = MOD_ROOT / "tools" / "mechanism_domains" / "domains.json"
        domain_payload = json.loads(rendered[domain_path].decode("utf-8"))
        self.assertEqual(domain_payload["domain_count"], 38)
        self.assertEqual(len(domain_payload["domains"]), 38)
        ids: list[int] = []
        for first_id, last_id in ((1, 120), (121, 240), (241, 361)):
            path = (
                MOD_ROOT
                / "tools"
                / "mechanism_runtime"
                / f"runtime_{first_id:03d}_{last_id:03d}.json"
            )
            payload = json.loads(rendered[path].decode("utf-8"))
            self.assertEqual(payload["id_range"], [first_id, last_id])
            self.assertEqual(payload["count"], last_id - first_id + 1)
            ids.extend(int(item["id"]) for item in payload["items"])
            self.assertTrue(
                all("case.transition" not in item["primitive_recipe"] for item in payload["items"])
            )
        self.assertEqual(ids, list(range(1, 362)))

    def test_plan_and_runtime_readiness_remain_separate(self) -> None:
        manifest = json.loads(
            outputs(self.mechanisms)[
                MOD_ROOT / "docs" / "361-mechanism-manifest.json"
            ].decode("utf-8")
        )
        self.assertEqual(
            sum(item["runtime_plan"]["status"] == "contract-complete" for item in manifest["items"]),
            361,
        )
        self.assertEqual(
            sum(item["status"]["domain_runtime"] == "partial" for item in manifest["items"]),
            193,
        )
        self.assertEqual(
            sum(item["status"]["domain_runtime"] == "not-implemented" for item in manifest["items"]),
            168,
        )
        self.assertEqual(
            manifest["readiness"]["exclusive_counts"],
            {
                "design-only": 0,
                "python-l0": 168,
                "ck3-static-ready": 131,
                "central-wired": 58,
                "ck3-live": 4,
            },
        )

    def test_domain_lookup_matches_catalogue_group(self) -> None:
        for mechanism in self.mechanisms:
            self.assertEqual(domain_for_id(mechanism.id).code, mechanism.group_code)

    def test_all_1083_routes_cross_the_closed_operation_registry(self) -> None:
        compiled_count = 0
        for plan in self.plans:
            for choice in ("a", "b", "c"):
                operations = compile_choice_ops(plan, choice)
                compiled_count += 1
                self.assertIs(operations[0].kind, OperationKind.DOMAIN)
                guard = render_transition_guard(operations[0])
                self.assertEqual(guard["hook"], plan["trigger_hook"])
                self.assertEqual(guard["transition_owner"], "stage_dispatcher")
                feedback_n = 0
                primitive_n = 0
                for operation in operations[1:]:
                    if operation.kind is OperationKind.PRIMITIVE:
                        self.assertIn(operation.operation_key, PRIMITIVE_WHITELIST)
                        primitive_n += 1
                    elif operation.kind is OperationKind.TRANSACTION:
                        self.assertTrue(render_transaction(operation)["receipt_key"])
                    elif operation.kind is OperationKind.DEADLINE:
                        self.assertEqual(
                            tuple(render_deadline(operation)["stale_guard"]),
                            STALE_GUARD,
                        )
                    elif operation.kind is OperationKind.FEEDBACK:
                        self.assertTrue(
                            render_feedback_projection(operation)["feedback"]
                        )
                        feedback_n += 1
                self.assertGreater(primitive_n, 0)
                self.assertGreater(feedback_n, 0)
        self.assertEqual(compiled_count, 361 * 3)

    def test_two_layer_registry_covers_all_38_domain_recipes(self) -> None:
        self.assertEqual(
            set(DOMAIN_RECIPE_PRIMITIVES),
            {domain.operation_key for domain in DOMAIN_SPECS},
        )
        for recipe in DOMAIN_RECIPE_PRIMITIVES.values():
            self.assertIn("case.create", recipe)
            self.assertNotIn("case.transition", recipe)
            self.assertIn("feedback.project", recipe)
        self.assertIn("case.transition", STAGE_DISPATCHER_PRIMITIVES)

    def test_357_is_fact_quota_adapter_and_never_refund_recipe(self) -> None:
        plan = self.by_id[357]
        self.assertEqual(plan["trigger_hook"], "multi_cycle_facts_frozen")
        self.assertEqual(
            (
                plan["choices"]["a"]["allowed_from_states"][0],
                plan["choices"]["a"]["to_state"],
            ),
            ("facts_frozen", "quota_applied"),
        )
        self.assertEqual(plan["adapter_domains"], ["A", "G", "B", "result_case"])
        self.assertTrue(
            all(not route["transactions"] for route in plan["choices"].values())
        )
        self.assertNotIn("transaction.refund", MECHANISM_PRIMITIVE_OVERRIDES[357])
        for choice in ("a", "b", "c"):
            self.assertNotIn(
                "transaction.refund",
                {op.operation_key for op in compile_choice_ops(plan, choice)},
            )


if __name__ == "__main__":
    unittest.main()
