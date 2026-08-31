#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static contract tests for the E/I/J/R credit/project CK3 package.

GREEN proves generated CK3-script structure and deterministic invariants only.
It is not CK3 parser, paused-snapshot, MCP, fixture-live or production evidence.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
MOD_ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gen_361_credit_project_runtime as gen
import zg361_phase3_credit_project_model as model


EFFECTS_PATH = MOD_ROOT / "common" / "scripted_effects" / "zg361_credit_project_runtime_effects.txt"
EVENTS_PATH = MOD_ROOT / "events" / "zg361_credit_project_runtime_events.txt"
SPEC_PATH = MOD_ROOT / "docs" / "361-phase3-credit-project-ck3-runtime-spec.md"
EXPECTED_IDS = set(range(26, 32)) | set(range(54, 69)) | set(range(129, 135))
DEBT_IDENTITY = ("owner", "subject", "cycle", "case", "state")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if match is None:
        raise AssertionError(f"missing block {name}")
    start = match.start()
    depth = 0
    opened = False
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
            opened = True
        elif text[index] == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start : index + 1]
    raise AssertionError(f"unbalanced block {name}")


def option_block(event: str, name: str) -> str:
    """Return the anonymous option block carrying one exact localization key."""

    for match in re.finditer(r"(?m)^\toption = \{", event):
        start = match.start()
        depth = 0
        opened = False
        for index in range(start, len(event)):
            if event[index] == "{":
                depth += 1
                opened = True
            elif event[index] == "}":
                depth -= 1
                if opened and depth == 0:
                    candidate = event[start : index + 1]
                    if f"name = {name}" in candidate:
                        return candidate
                    break
    raise AssertionError(f"missing option {name}")


def loc_rows(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in read(path).splitlines()[1:]:
        match = re.match(r'\s*([^:]+):0\s+"(.*)"\s*$', line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


class RegistryAndGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)
        cls.events = read(EVENTS_PATH)
        cls.spec = read(SPEC_PATH)
        cls.specs = gen.by_id()

    def test_readiness_is_honest(self) -> None:
        self.assertEqual(gen.READINESS, "ck3-script-static-ready-not-live")
        self.assertIn("No CK3 parser, paused snapshot or live evidence is claimed", self.effects)
        self.assertIn("没有启动 CK3", self.spec)
        self.assertNotIn("production-live", gen.READINESS)

    def test_exact_twenty_seven_ids_match_committed_python_contract(self) -> None:
        self.assertEqual(set(self.specs), EXPECTED_IDS)
        self.assertEqual(len(gen.MECHANISMS), 27)
        self.assertEqual(set(model.MECHANISM_BINDINGS), EXPECTED_IDS)
        self.assertEqual({mid for order in gen.DOMAIN_ORDER.values() for mid in order}, EXPECTED_IDS)

    def test_exact_domain_ranges(self) -> None:
        expected = {
            "e": set(range(26, 32)),
            "i": set(range(54, 62)),
            "j": set(range(62, 69)),
            "r": set(range(129, 135)),
        }
        for domain, ids in expected.items():
            with self.subTest(domain=domain):
                self.assertEqual({spec.mid for spec in gen.MECHANISMS if spec.domain == domain}, ids)

    def test_execution_order_and_stage_graph_are_frozen(self) -> None:
        self.assertEqual(gen.DOMAIN_ORDER["e"], (30, 26, 27, 31, 28, 29))
        self.assertEqual(gen.DOMAIN_ORDER["i"], (61, 54, 56, 57, 58, 59, 55, 60))
        self.assertEqual(gen.DOMAIN_ORDER["j"], (63, 62, 65, 64, 66, 67, 68))
        self.assertEqual(gen.DOMAIN_ORDER["r"], (131, 129, 134, 130, 132, 133))
        self.assertEqual(gen.NEXT_DOMAIN, {"e": "i", "i": "j", "j": "r", "r": None})
        self.assertEqual(gen.STAGE_LAST["e"], {26: 1, 31: 2, 28: 3, 29: 4})
        self.assertEqual(gen.STAGE_LAST["r"], {131: 1, 134: 2, 130: 3, 132: 4, 133: 5})

    def test_outputs_are_exactly_the_independent_package(self) -> None:
        outputs = gen.outputs()
        self.assertEqual(len(outputs), 11)
        self.assertEqual(
            {path.name for path in outputs},
            {
                "zg361_credit_project_runtime_effects.txt",
                "zg361_credit_project_runtime_events.txt",
                *(f"zg361_credit_project_l_{language}.yml" for language in gen.LANGUAGES),
            },
        )
        for path in outputs:
            self.assertNotIn("scoreboard", str(path))
            self.assertNotIn("b1_runtime", str(path))
            self.assertNotIn("b2_runtime", str(path))
            self.assertNotIn("case_kernel", path.name)

    def test_generator_check_mode_is_green(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOLS / "gen_361_credit_project_runtime.py"), "--check"],
            cwd=MOD_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GREEN", result.stdout)

    def test_all_owned_sources_and_outputs_have_bom(self) -> None:
        paths = [TOOLS / "gen_361_credit_project_runtime.py", Path(__file__), SPEC_PATH, *gen.outputs()]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.read_bytes().startswith(gen.BOM))

    def test_generated_script_braces_balance(self) -> None:
        for path in (EFFECTS_PATH, EVENTS_PATH):
            with self.subTest(path=path):
                text = read(path)
                self.assertEqual(text.count("{"), text.count("}"))

    def test_debt_reads_are_existence_gated_before_comparison(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_cp_m{spec.mid}_consume_due_policy_debt_effect")
            with self.subTest(mid=spec.mid):
                stem = f"zg361_cp_m{spec.mid}_debt"
                for field in (*DEBT_IDENTITY, "mechanism", "due_cycle", "status", "audit_state", "business_object_created"):
                    self.assertLess(
                        consumer.index(f"has_variable = {stem}_{field}"),
                        consumer.index(f"var:{stem}_{field}"),
                    )


class ReceiptAndConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)
        cls.events = read(EVENTS_PATH)
        cls.specs = gen.by_id()

    def test_exact_route_consumer_and_event_counts(self) -> None:
        routes = re.findall(r"^zg361_cp_m(\d+)_route_([abc])_effect = \{$", self.effects, re.MULTILINE)
        consumers = re.findall(r"^zg361_cp_m(\d+)_consume_effect = \{$", self.effects, re.MULTILINE)
        debt_consumers = re.findall(
            r"^zg361_cp_m(\d+)_consume_due_policy_debt_effect = \{$", self.effects, re.MULTILINE
        )
        events = re.findall(r"^zg361cp\.(\d+) = \{$", self.events, re.MULTILINE)
        self.assertEqual(len(routes), 81)
        self.assertEqual(len(consumers), 27)
        self.assertEqual(len(debt_consumers), 27)
        self.assertEqual(self.effects.count("zg361_cp_consume_due_policy_debts_effect = {"), 1)
        self.assertEqual(len(events), 30)
        self.assertEqual({int(mid) for mid, _ in routes}, EXPECTED_IDS)
        self.assertEqual({int(mid) for mid in consumers}, EXPECTED_IDS)
        self.assertEqual({int(mid) for mid in debt_consumers}, EXPECTED_IDS)
        self.assertEqual({int(mid) for mid in events}, EXPECTED_IDS | set(gen.QUEUE_EVENTS.values()))

    def test_every_player_event_has_three_routes_and_full_guard(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                event = block(self.events, f"zg361cp.{spec.mid}")
                self.assertEqual(event.count("\n\toption = {"), 3)
                self.assertIn("is_ai = no", event)
                self.assertIn("zg361_is_celestial_liege_trigger = yes", event)
                self.assertIn(f"EXPECTED_STATE = {spec.state}", event)
                for name in ("owner", "subject", "cycle", "case"):
                    self.assertIn(f"exists = scope:zg361_cp_{spec.domain}_{name}", event)

    def test_every_route_has_five_tuple_guard_and_six_field_receipt(self) -> None:
        for spec in gen.MECHANISMS:
            for choice, letter in enumerate("abc", 1):
                with self.subTest(mid=spec.mid, route=letter):
                    route = block(self.effects, f"zg361_cp_m{spec.mid}_route_{letter}_effect")
                    self.assertIn("zg361_case_kernel_full_guard_trigger", route)
                    for token in ("OWNER_VAR", "SUBJECT_VAR", "CYCLE_VAR", "CASE_VAR", "STATE_VAR", "ACTIVE_VAR"):
                        self.assertIn(token, route)
                    for token in ("EXPECTED_OWNER", "EXPECTED_SUBJECT", "EXPECTED_CYCLE", "EXPECTED_CASE"):
                        self.assertIn(token, route)
                    self.assertIn(f"EXPECTED_STATE = {spec.state}", route)
                    for name in ("owner", "subject", "cycle", "case", "state", "choice"):
                        self.assertIn(f"zg361_cp_m{spec.mid}_receipt_{name}", route)
                    self.assertIn(f"CHOICE = {choice}", route)

    def test_receipt_is_mutually_exclusive_across_routes(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                route = block(self.effects, f"zg361_cp_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    for choice in (1, 2, 3):
                        self.assertIn(f"EXPECTED_CHOICE = {choice}", route)
                    self.assertIn("NOT = {", route)
                    self.assertIn(f"RECEIPT_CHOICE_VAR = zg361_cp_m{spec.mid}_receipt_choice", route)

    def test_a_and_b_preflight_precede_receipt_business_write_and_consumer(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "ab":
                route = block(self.effects, f"zg361_cp_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    preflight = route.index(f"var:zg361_cp_{spec.domain}_operation_used <")
                    receipt = route.index("zg361_case_kernel_record_operation_effect")
                    business = route.index(f"name = zg361_cp_{spec.field}")
                    write = route.index(f"name = zg361_cp_m{spec.mid}_write_owner")
                    consumer = route.index(f"zg361_cp_m{spec.mid}_consume_effect = yes")
                    self.assertLess(preflight, receipt)
                    self.assertLess(receipt, business)
                    self.assertLess(business, write)
                    self.assertLess(write, consumer)

    def test_c_preflight_precedes_receipt_and_exact_debt_without_business_write(self) -> None:
        for spec in gen.MECHANISMS:
            route = block(self.effects, f"zg361_cp_m{spec.mid}_route_c_effect")
            stem = f"zg361_cp_m{spec.mid}_debt"
            with self.subTest(mid=spec.mid):
                preflight = route.index(f"var:zg361_cp_{spec.domain}_operation_used <")
                receipt = route.index("zg361_case_kernel_record_operation_effect")
                debt = route.index(f"name = {stem}_owner")
                self.assertLess(preflight, receipt)
                self.assertLess(receipt, debt)
                self.assertIn(f"name = zg361_cp_{spec.field} value = 3", route)
                self.assertNotIn(f"name = zg361_cp_m{spec.mid}_write_owner", route)
                self.assertNotIn(f"zg361_cp_m{spec.mid}_consume_effect = yes", route)
                self.assertNotIn(f"zg361_cp_m{spec.mid}_provenance_choice", route)
                business_names = {
                    name
                    for choice in (1, 2)
                    for name in re.findall(r"name = (zg361_cp_[a-z0-9_]+)", "\n".join(gen.business_effects(spec, choice)))
                }
                business_names -= {
                    f"zg361_cp_{spec.field}",
                    f"zg361_cp_{spec.domain}_operation_used",
                }
                for name in business_names:
                    self.assertNotIn(f"name = {name}", route)
                business_reads = {
                    name
                    for choice in (1, 2)
                    for name in re.findall(r"zg361_cp_[a-z0-9_]+", "\n".join(gen.resource_checks(spec, choice)))
                }
                business_reads -= {
                    f"zg361_cp_{spec.domain}_operation_total",
                    f"zg361_cp_{spec.domain}_operation_used",
                }
                for name in business_reads:
                    self.assertNotIn(name, route)

    def test_statuses_make_red_idempotent_and_stale_explicit(self) -> None:
        for spec in gen.MECHANISMS:
            for choice, letter in enumerate("abc", 1):
                route = block(self.effects, f"zg361_cp_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    self.assertIn(f"name = zg361_cp_last_red_code value = {spec.mid * 10 + choice}", route)
                    self.assertIn("value = 4 } # typed RED; no receipt, business or resource write", route)
                    self.assertIn("value = 2 } # idempotent no-op", route)
                    self.assertIn("value = 3 } } # stale no-op", route)

    def test_every_write_has_immediate_downstream_consumer(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_cp_m{spec.mid}_consume_effect")
            with self.subTest(mid=spec.mid):
                for name in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"has_variable = zg361_cp_m{spec.mid}_write_{name}", consumer)
                    self.assertIn(f"name = zg361_cp_m{spec.mid}_consumed_{name}", consumer)
                self.assertIn(f"value = var:zg361_cp_{spec.field}", consumer)
                self.assertIn(f"zg361_cp_m{spec.mid}_visible_provenance_case", consumer)
                for letter in "ab":
                    route = block(self.effects, f"zg361_cp_m{spec.mid}_route_{letter}_effect")
                    self.assertEqual(route.count(f"zg361_cp_m{spec.mid}_consume_effect = yes"), 1)

    def test_a_and_b_are_isolated_from_policy_debt(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "ab":
                route = block(self.effects, f"zg361_cp_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    self.assertNotIn(f"zg361_cp_m{spec.mid}_debt_", route)
                    self.assertNotIn("zg361_cp_policy_debt_open_n", route)
                    self.assertNotIn("zg361_cp_portfolio_deferred", route)
                    self.assertIn(f"name = zg361_cp_m{spec.mid}_write_owner", route)
                    self.assertIn(f"zg361_cp_m{spec.mid}_consume_effect = yes", route)

    def test_each_c_route_freezes_one_exact_next_cycle_debt(self) -> None:
        for spec in gen.MECHANISMS:
            route = block(self.effects, f"zg361_cp_m{spec.mid}_route_c_effect")
            stem = f"zg361_cp_m{spec.mid}_debt"
            with self.subTest(mid=spec.mid):
                expected_values = {
                    "owner": "$TICKET_OWNER$",
                    "subject": "$TICKET_SUBJECT$",
                    "cycle": "$TICKET_CYCLE$",
                    "case": "$TICKET_CASE$",
                    "state": str(spec.state),
                }
                for field, value in expected_values.items():
                    setter = f"set_variable = {{ name = {stem}_{field} value = {value} }}"
                    self.assertEqual(route.count(setter), 1)
                self.assertEqual(route.count(f"name = {stem}_mechanism value = {spec.mid}"), 1)
                self.assertEqual(
                    route.count(f"name = {stem}_due_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }}"),
                    1,
                )
                self.assertEqual(route.count(f"name = {stem}_status value = 1"), 1)
                self.assertEqual(route.count(f"name = {stem}_audit_state value = 1"), 1)
                self.assertEqual(route.count(f"name = {stem}_business_object_created value = 0"), 1)
                self.assertEqual(route.count("name = zg361_cp_policy_debt_open_n add = 1"), 1)
                self.assertEqual(route.count("name = zg361_cp_portfolio_deferred value = 1"), 1)
                self.assertEqual(route.count("name = zg361_cp_deferred_cleanup_status value = 1"), 1)

    def test_c_duplicate_receipt_is_a_no_op_and_cannot_open_a_second_debt(self) -> None:
        for spec in gen.MECHANISMS:
            route = block(self.effects, f"zg361_cp_m{spec.mid}_route_c_effect")
            with self.subTest(mid=spec.mid):
                self.assertEqual(route.count("name = zg361_cp_policy_debt_open_n add = 1"), 1)
                self.assertEqual(route.count("value = 2 } # idempotent no-op"), 1)
                self.assertIn("EXPECTED_CHOICE = 3", route)

    def test_only_stage_barriers_advance_after_all_stage_receipts(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                route = block(self.effects, f"zg361_cp_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    if spec.mid in gen.STAGE_LAST[spec.domain]:
                        edge = gen.STAGE_LAST[spec.domain][spec.mid]
                        self.assertEqual(route.count(f"zg361_case_{spec.domain}_advance_{edge:02d}_effect"), 1)
                        before = route[: route.index(f"zg361_case_{spec.domain}_advance_{edge:02d}_effect")]
                        for item in gen.MECHANISMS:
                            if item.domain == spec.domain and item.state == spec.state:
                                self.assertIn(f"zg361_cp_m{item.mid}_receipt_choice", before)
                    else:
                        self.assertNotIn(f"zg361_case_{spec.domain}_advance_", route)

    def test_domains_chain_e_i_j_r_and_finalize_once(self) -> None:
        for domain, next_domain in gen.NEXT_DOMAIN.items():
            final_mid = gen.DOMAIN_ORDER[domain][-1]
            for letter in "abc":
                route = block(self.effects, f"zg361_cp_m{final_mid}_route_{letter}_effect")
                expected = (
                    f"trigger_event = {{ id = zg361cp.{gen.QUEUE_EVENTS[domain]} days = 1 }}"
                    if next_domain
                    else "zg361_cp_finalize_portfolio_effect = yes"
                )
                self.assertEqual(route.count(expected), 1)

    def test_player_windows_and_cross_domain_edges_are_d_plus_one_queued(self) -> None:
        for domain, order in gen.DOMAIN_ORDER.items():
            for mid in order[:-1]:
                with self.subTest(mid=mid):
                    event = block(self.events, f"zg361cp.{mid}")
                    self.assertEqual(event.count("days = 1"), 3)
        for domain, event_id in gen.QUEUE_EVENTS.items():
            with self.subTest(domain=domain):
                queued = block(self.events, f"zg361cp.{event_id}")
                self.assertIn("hidden = yes", queued)
                self.assertIn(f"zg361_cp_{gen.NEXT_DOMAIN[domain]}_launch_effect = yes", queued)
                self.assertIn(f"var:zg361_case_{domain}_active = 0", queued)


class PolicyDebtLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)
        cls.events = read(EVENTS_PATH)

    def test_each_due_consumer_strongly_validates_debt_receipt_choice_and_due_cycle(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_cp_m{spec.mid}_consume_due_policy_debt_effect")
            stem = f"zg361_cp_m{spec.mid}_debt"
            receipt = f"zg361_cp_m{spec.mid}_receipt"
            with self.subTest(mid=spec.mid):
                for field in DEBT_IDENTITY:
                    self.assertIn(f"has_variable = {stem}_{field}", consumer)
                    self.assertIn(f"has_variable = {receipt}_{field}", consumer)
                    self.assertIn(f"var:{receipt}_{field} = var:{stem}_{field}", consumer)
                for field in ("mechanism", "due_cycle", "status", "audit_state", "business_object_created"):
                    self.assertIn(f"has_variable = {stem}_{field}", consumer)
                self.assertIn(f"var:{stem}_owner = root", consumer)
                self.assertIn(f"var:{stem}_subject = this", consumer)
                self.assertIn(f"var:{stem}_mechanism = {spec.mid}", consumer)
                self.assertIn(f"var:{stem}_status = 1", consumer)
                self.assertIn(f"var:{stem}_audit_state = 1", consumer)
                self.assertIn(f"var:{stem}_business_object_created = 0", consumer)
                self.assertIn(f"var:{receipt}_choice = 3", consumer)
                self.assertIn(f"root.var:zg361_review_serial = var:{stem}_due_cycle", consumer)

    def test_due_consumer_writes_one_real_next_review_sink_and_auditable_settlement(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_cp_m{spec.mid}_consume_due_policy_debt_effect")
            stem = f"zg361_cp_m{spec.mid}_debt"
            with self.subTest(mid=spec.mid):
                self.assertEqual(consumer.count("name = zg361_b2_management_debt add = 1"), 1)
                self.assertIn(f"name = {stem}_status value = 2", consumer)
                self.assertIn(f"name = {stem}_audit_state value = 3", consumer)
                self.assertIn(f"name = {stem}_settled_by value = root", consumer)
                self.assertIn(
                    f"name = {stem}_settled_cycle value = root.var:zg361_review_serial",
                    consumer,
                )
                self.assertIn(f"name = {stem}_performance_sink value = 1", consumer)
                self.assertEqual(consumer.count("name = zg361_cp_policy_debt_open_n add = -1"), 1)
                self.assertEqual(consumer.count("name = zg361_cp_policy_debt_settled_n add = 1"), 1)

    def test_exact_settled_replay_is_audit_only_and_sink_is_not_reapplied(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_cp_m{spec.mid}_consume_due_policy_debt_effect")
            stem = f"zg361_cp_m{spec.mid}_debt"
            with self.subTest(mid=spec.mid):
                self.assertIn("Exact settled replay is audit-only", consumer)
                self.assertIn(f"var:{stem}_status = 2", consumer)
                self.assertIn(f"var:{stem}_settled_by = root", consumer)
                self.assertIn(f"name = {stem}_consumer_status value = 2", consumer)
                self.assertEqual(consumer.count("name = zg361_b2_management_debt add = 1"), 1)

    def test_future_stale_cross_owner_and_corrupt_pending_debts_fail_closed(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_cp_m{spec.mid}_consume_due_policy_debt_effect")
            stem = f"zg361_cp_m{spec.mid}_debt"
            with self.subTest(mid=spec.mid):
                self.assertIn(f"root.var:zg361_review_serial < var:{stem}_due_cycle", consumer)
                self.assertIn(f"name = {stem}_consumer_status value = 5", consumer)
                self.assertIn("stale/cross-owner/corrupt identity: fail closed", consumer)
                self.assertIn(f"name = {stem}_consumer_status value = 3", consumer)
                self.assertGreaterEqual(
                    consumer.count("name = zg361_cp_policy_debt_consumer_blocked value = 1"),
                    2,
                )
                self.assertIn(f"name = zg361_cp_last_red_code value = {60000 + spec.mid}", consumer)

    def test_aggregate_calls_every_debt_consumer_once(self) -> None:
        aggregate = block(self.effects, "zg361_cp_consume_due_policy_debts_effect")
        self.assertEqual(aggregate.count("remove_variable = zg361_cp_policy_debt_consumer_blocked"), 1)
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                self.assertEqual(
                    aggregate.count(f"zg361_cp_m{spec.mid}_consume_due_policy_debt_effect = yes"),
                    1,
                )
        cleanup = aggregate.index("zg361_cp_settle_deferred_portfolio_effect = yes")
        self.assertEqual(aggregate.count("zg361_cp_settle_deferred_portfolio_effect = yes"), 1)
        for spec in gen.MECHANISMS:
            self.assertLess(
                aggregate.index(f"zg361_cp_m{spec.mid}_consume_due_policy_debt_effect = yes"),
                cleanup,
            )
        self.assertIn("NOT = { has_variable = zg361_cp_policy_debt_consumer_blocked }", aggregate)

    def test_public_adapter_consumes_due_debts_before_it_may_open_a_portfolio(self) -> None:
        entry = block(self.effects, "zg361_cp_open_portfolio_effect")
        due = entry.index("zg361_cp_consume_due_policy_debts_effect = yes")
        launch = entry.index("zg361_cp_e_launch_effect = yes")
        self.assertLess(due, launch)
        self.assertEqual(entry.count("zg361_cp_consume_due_policy_debts_effect = yes"), 1)
        self.assertIn("zg361_cp_policy_debt_consumer_blocked", entry)

    def test_first_c_makes_later_player_business_routes_unavailable(self) -> None:
        for spec in gen.MECHANISMS:
            event = block(self.events, f"zg361cp.{spec.mid}")
            for letter in "ab":
                option = option_block(event, f"zg361cp.{spec.mid}.{letter}")
                with self.subTest(mid=spec.mid, route=letter):
                    self.assertIn("has_variable = zg361_cp_portfolio_deferred", option)
                    self.assertIn("var:zg361_cp_portfolio_deferred = 0", option)
            c_option = option_block(event, f"zg361cp.{spec.mid}.c")
            self.assertNotIn("var:zg361_cp_portfolio_deferred = 0", c_option)

    def test_deferred_ai_continues_with_c_without_opening_gui(self) -> None:
        for domain, ids in gen.DOMAIN_ORDER.items():
            ai = block(self.effects, f"zg361_cp_{domain}_run_authorized_ai_effect")
            with self.subTest(domain=domain):
                self.assertIn("has_variable = zg361_cp_portfolio_deferred", ai)
                self.assertIn("var:zg361_cp_portfolio_deferred = 1", ai)
                self.assertNotIn("trigger_event", ai)
                for mid in ids:
                    self.assertIn(f"zg361_cp_m{mid}_route_c_effect", ai)

    def test_same_cycle_deferred_finalize_only_proves_frozen_conservation(self) -> None:
        finalizer = block(self.effects, "zg361_cp_finalize_portfolio_effect")
        self.assertIn("var:zg361_cp_portfolio_deferred = 1", finalizer)
        self.assertIn(
            "zg361_cp_final_deferred_capacity_check value = { value = var:zg361_cp_capacity_available "
            "add = var:zg361_cp_capacity_spent add = var:zg361_cp_capacity_remaining }",
            finalizer,
        )
        self.assertIn("var:zg361_cp_final_deferred_capacity_check = 100", finalizer)
        self.assertIn("zg361_cp_final_deferred value = 1", finalizer)
        self.assertIn("zg361_cp_final_conservation_ok value = 1", finalizer)
        self.assertNotRegex(
            finalizer,
            r"(?:set|change)_variable = \{ name = zg361_cp_(?:capacity_(?:available|remaining|reserved|spent)"
            r"|project_active|project_slot_used|project_object_|report_object_)",
        )

    def test_due_cleanup_is_exact_once_identity_bound_and_releases_only_existing_project(self) -> None:
        cleanup = block(self.effects, "zg361_cp_settle_deferred_portfolio_effect")
        for field in (
            "zg361_cp_portfolio_deferred",
            "zg361_cp_deferred_cleanup_status",
            "zg361_cp_policy_debt_open_n",
            "zg361_cp_portfolio_closed",
            "zg361_cp_historical_owner",
            "zg361_cp_portfolio_subject",
            "zg361_cp_portfolio_cycle",
            "zg361_cp_project_active",
            "zg361_cp_capacity_available",
            "zg361_cp_capacity_remaining",
            "zg361_cp_capacity_reserved",
            "zg361_cp_capacity_spent",
            "zg361_cp_project_slot_used",
        ):
            self.assertIn(f"has_variable = {field}", cleanup)
        for check in (
            "var:zg361_cp_portfolio_deferred = 1",
            "var:zg361_cp_deferred_cleanup_status = 1",
            "var:zg361_cp_policy_debt_open_n = 0",
            "var:zg361_cp_portfolio_closed = 1",
            "var:zg361_cp_historical_owner = root",
            "var:zg361_cp_portfolio_subject = this",
            "root.var:zg361_review_serial = { value = var:zg361_cp_portfolio_cycle add = 1 }",
        ):
            self.assertIn(check, cleanup)
        self.assertIn("limit = { var:zg361_cp_project_active = 1 }", cleanup)
        self.assertEqual(
            cleanup.count("change_variable = { name = zg361_cp_capacity_available add = var:zg361_cp_capacity_remaining }"),
            1,
        )
        self.assertEqual(cleanup.count("name = zg361_cp_capacity_remaining value = 0"), 1)
        self.assertEqual(cleanup.count("name = zg361_cp_project_active value = 0"), 1)
        self.assertEqual(cleanup.count("name = zg361_cp_project_slot_used value = 0"), 1)
        self.assertEqual(cleanup.count("name = zg361_cp_project_object_status value = 3"), 1)
        self.assertEqual(cleanup.count("name = zg361_cp_deferred_cleanup_status value = 2"), 1)
        self.assertIn("name = zg361_cp_deferred_cleanup_settled_by value = root", cleanup)
        self.assertIn(
            "name = zg361_cp_deferred_cleanup_settled_cycle value = root.var:zg361_review_serial",
            cleanup,
        )
        self.assertIn("name = zg361_cp_policy_debt_consumer_blocked value = 1", cleanup)
        self.assertIn("name = zg361_cp_last_red_code value = 60999", cleanup)

    def test_portfolio_init_does_not_erase_open_or_settled_debt_counts(self) -> None:
        init = block(self.effects, "zg361_cp_initialize_portfolio_effect")
        self.assertIn("name = zg361_cp_portfolio_deferred value = 0", init)
        for counter in ("zg361_cp_policy_debt_open_n", "zg361_cp_policy_debt_settled_n"):
            with self.subTest(counter=counter):
                self.assertIn(f"has_variable = {counter}", init)
                self.assertEqual(init.count(f"name = {counter} value = 0"), 1)


class RoleAndLedgerInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)

    def test_public_entry_is_duke_plus_manager_and_direct_subject_only(self) -> None:
        entry = block(self.effects, "zg361_cp_open_portfolio_effect")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", entry)
        self.assertIn("$SUBJECT$ = { zg361_is_reviewable_vassal_trigger = yes liege = root }", entry)
        self.assertIn("$SUBJECT$ = {", entry)
        self.assertIn("zg361_cp_consume_due_policy_debts_effect = yes", entry)
        self.assertIn("zg361_cp_e_launch_effect = yes", entry)
        self.assertNotIn("zg361_cp_initialize_portfolio_effect = yes", entry)
        self.assertNotIn("trigger_event", entry)
        self.assertEqual(len(re.findall(r"(?m)^zg361_cp_open_portfolio_effect = \{", self.effects)), 1)
        self.assertEqual(self.effects.count("# Public manager-scope ABI."), 1)

    def test_replay_cannot_reset_an_active_or_same_cycle_portfolio(self) -> None:
        entry = block(self.effects, "zg361_cp_open_portfolio_effect")
        self.assertIn("zg361_cp_portfolio_cycle = root.var:zg361_review_serial", entry)
        for domain in "eijr":
            self.assertIn(f"has_variable = zg361_case_{domain}_active", entry)
            self.assertIn(f"var:zg361_case_{domain}_active = 0", entry)
        launch = block(self.effects, "zg361_cp_e_launch_effect")
        opened = launch.index("zg361_case_e_open_effect = yes")
        initialized = launch.index("zg361_cp_initialize_portfolio_effect = yes")
        self.assertLess(opened, initialized)

    def test_authorized_ai_is_silent_and_player_events_are_separate(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            ai = block(self.effects, f"zg361_cp_{domain}_run_authorized_ai_effect")
            launch = block(self.effects, f"zg361_cp_{domain}_launch_effect")
            with self.subTest(domain=domain):
                self.assertIn("is_ai = yes zg361_is_celestial_liege_trigger = yes", ai)
                self.assertNotIn("trigger_event", ai)
                self.assertIn("is_ai = no zg361_is_celestial_liege_trigger = yes", launch)
                self.assertIn("trigger_event", launch)

    def test_count_and_baron_path_is_assessed_read_only(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            read_adapter = block(self.effects, f"zg361_cp_{domain}_subject_read_effect")
            with self.subTest(domain=domain):
                self.assertIn("zg361_case_kernel_subject_self_guard_trigger", read_adapter)
                self.assertIn("subject_seen_revision", read_adapter)
                self.assertNotIn("open_effect", read_adapter)
                self.assertNotIn("capacity_reserved", read_adapter)
                self.assertNotIn("promotion", read_adapter)

    def test_project_slot_and_capacity_have_real_reserve_spend_release(self) -> None:
        init = block(self.effects, "zg361_cp_initialize_portfolio_effect")
        self.assertIn("zg361_cp_capacity_total value = 100", init)
        self.assertIn("zg361_cp_project_slot_total value = 1", init)
        for choice, letter in enumerate("ab", 1):
            route = block(self.effects, f"zg361_cp_m30_route_{letter}_effect")
            amount = (40, 60)[choice - 1]
            self.assertIn(f"capacity_available >= {amount}", route)
            self.assertIn(f"capacity_reserved value = {amount}", route)
            self.assertIn(f"capacity_available subtract = {amount}", route)
            self.assertIn("resource_winner_n value = 1", route)
        for mid in (66, 132):
            combined = "".join(block(self.effects, f"zg361_cp_m{mid}_route_{letter}_effect") for letter in "ab")
            self.assertIn("capacity_available add = var:zg361_cp_capacity_remaining", combined)
            self.assertIn("project_slot_used value = 0", combined)
        finalizer = block(self.effects, "zg361_cp_finalize_portfolio_effect")
        self.assertIn("final_capacity_check", finalizer)
        self.assertIn("final_attention_check", finalizer)
        self.assertIn("final_promotion_check", finalizer)
        self.assertIn("final_share_total = 10000", finalizer)
        self.assertIn("final_conservation_ok value = 1", finalizer)

    def test_delivery_reporting_and_visibility_are_separate(self) -> None:
        for letter in "ab":
            effort = block(self.effects, f"zg361_cp_m26_route_{letter}_effect")
            report = block(self.effects, f"zg361_cp_m54_route_{letter}_effect")
            self.assertIn("zg361_cp_hard_output add", effort)
            self.assertIn("zg361_cp_visibility_points add", effort)
            self.assertIn("zg361_cp_capacity_remaining subtract", report)
            self.assertIn("zg361_cp_report_packet_hard_output value = 0", report)
            self.assertNotIn("zg361_cp_hard_output add", report)

    def test_all_contribution_mutations_conserve_ten_thousand(self) -> None:
        for letter in "ab":
            signed = block(self.effects, f"zg361_cp_m27_route_{letter}_effect")
            claim = block(self.effects, f"zg361_cp_m28_route_{letter}_effect")
            forward = block(self.effects, f"zg361_cp_m56_route_{letter}_effect")
            self.assertIn("signed_share_total value = 10000", signed)
            self.assertIn("claimed_share_total value = 10000", signed)
            self.assertIn("claim_transfer_total value = 0", claim)
            self.assertIn("claim_audit_total value = 0", claim)
            self.assertIn("claimed_share_total value = 10000", claim)
            self.assertIn("forward_delta_total value = 0", forward)
            self.assertIn("report_share_total value = 10000", forward)
        reversed_claim = block(self.effects, "zg361_cp_m28_route_b_effect")
        self.assertIn("claimed_subject_bps subtract = 500", reversed_claim)
        self.assertIn("claimed_subject_bps add = 500", reversed_claim)
        self.assertIn("claimed_manager_bps add = 500", reversed_claim)
        self.assertIn("claimed_manager_bps subtract = 500", reversed_claim)

    def test_cross_department_evidence_is_an_actor_and_a_consumer(self) -> None:
        init = block(self.effects, "zg361_cp_initialize_portfolio_effect")
        self.assertIn("zg361_cp_cross_reviewer value = scope:zg361_cp_cross_candidate", init)
        self.assertIn("zg361_cp_cross_reviewer_valid value = 1", init)
        self.assertIn("position = 0", init)
        entry = block(self.effects, "zg361_cp_open_portfolio_effect")
        self.assertIn("NOT = { this = $SUBJECT$ }", entry)
        signed = block(self.effects, "zg361_cp_m27_route_a_effect")
        self.assertIn("var:zg361_cp_cross_reviewer_valid = 1", signed)
        for token in (
            "zg361_cp_contribution_signer_cross",
            "zg361_cp_cross_evidence_attached",
            "zg361_cp_report_cross_recipient",
            "zg361_cp_idea_owner",
            "zg361_cp_duplicate_role_owner",
            "zg361_cp_shared_metric_dependency_cross",
        ):
            self.assertIn(token, self.effects)

    def test_signature_route_and_attention_are_three_different_ledgers(self) -> None:
        signed = "".join(block(self.effects, f"zg361_cp_m57_route_{letter}_effect") for letter in "ab")
        routed = "".join(block(self.effects, f"zg361_cp_m58_route_{letter}_effect") for letter in "ab")
        read = "".join(block(self.effects, f"zg361_cp_m55_route_{letter}_effect") for letter in "ab")
        self.assertIn("report_signed value = 1", signed)
        self.assertIn("report_seen_count value = 0", routed)
        self.assertNotIn("attention_free subtract", routed)
        self.assertIn("var:zg361_cp_report_routed = 1", read)
        self.assertIn("attention_free subtract", read)
        self.assertIn("visibility_points add", read)

    def test_report_build_consumes_the_frozen_policy(self) -> None:
        events = read(EVENTS_PATH)
        event = block(events, "zg361cp.54")
        for choice, letter in enumerate("ab", 1):
            route = block(self.effects, f"zg361_cp_m54_route_{letter}_effect")
            hours = (1, 4)[choice - 1]
            self.assertIn(f"var:zg361_cp_report_policy = {choice}", route)
            self.assertIn(f"var:zg361_cp_report_policy_hours = {hours}", route)
            option = option_block(event, f"zg361cp.54.{letter}")
            self.assertIn("has_variable = zg361_cp_report_policy", option)
        c_option = option_block(event, "zg361cp.54.c")
        self.assertNotIn("has_variable = zg361_cp_report_policy", c_option)

    def test_matrix_handoff_preserves_historical_owner(self) -> None:
        for letter in "ab":
            weights = block(self.effects, f"zg361_cp_m63_route_{letter}_effect")
            self.assertIn("matrix_weight_total value = 100", weights)
        handoff = block(self.effects, "zg361_cp_m64_route_a_effect")
        self.assertIn("handoff_old_signed value = 1", handoff)
        self.assertIn("handoff_new_signed value = 1", handoff)
        self.assertIn("handoff_finalized value = 1", handoff)
        self.assertIn("active_manager value = var:zg361_cp_successor_manager", handoff)
        self.assertNotIn("historical_owner value", handoff)
        consumer = block(self.effects, "zg361_cp_m64_consume_effect")
        self.assertIn("visible_historical_owner value = var:zg361_cp_historical_owner", consumer)

    def test_duplicate_role_promotion_and_shared_metric_have_unique_owners(self) -> None:
        for letter in "ab":
            role = block(self.effects, f"zg361_cp_m67_route_{letter}_effect")
            metric = block(self.effects, f"zg361_cp_m134_route_{letter}_effect")
            self.assertIn("duplicate_role_owner_count value = 1", role)
            self.assertIn("duplicate_transition_terminal value = 1", role)
            self.assertIn("shared_metric_owner_count value = 1", metric)
            self.assertIn("shared_metric_assignment_locked value = 1", metric)
        promotion = block(self.effects, "zg361_cp_m129_route_b_effect")
        self.assertIn("promotion_slot_free subtract = 1", promotion)
        self.assertIn("promotion_slot_used add = 1", promotion)
        self.assertIn("promotion_awarded value = 1", promotion)

    def test_pip_dump_stop_loss_and_postmortem_have_real_consumers(self) -> None:
        transfer = block(self.effects, "zg361_cp_m130_route_b_effect")
        self.assertIn("transfer_pip_disclosed value = 1", transfer)
        self.assertIn("transfer_trial_success value = 1", transfer)
        self.assertIn("transfer_source_accountability value = 0", transfer)
        self.assertIn("transfer_source_manager value = $TICKET_OWNER$", transfer)
        self.assertIn("transfer_destination_manager value = var:zg361_cp_cross_reviewer", transfer)
        stop = block(self.effects, "zg361_cp_m132_route_a_effect")
        self.assertIn("stop_judgement value = 1", stop)
        self.assertIn("stop_individual_separate value = 1", stop)
        weak_stop = block(self.effects, "zg361_cp_m132_route_b_effect")
        self.assertIn("stop_judgement value = 2", weak_stop)
        self.assertIn("project_active value = 0", weak_stop)
        self.assertIn("capacity_available add = var:zg361_cp_capacity_remaining", weak_stop)
        post = block(self.effects, "zg361_cp_m133_route_b_effect")
        self.assertIn("postmortem_blanket_penalty value = 0", post)
        self.assertIn("postmortem_stop_judgement_used value = var:zg361_cp_stop_judgement", post)
        consumer = block(self.effects, "zg361_cp_m133_consume_effect")
        self.assertIn("postmortem_learning_consumed value = 1", consumer)

    def test_b2_is_read_only_optional_pip_input(self) -> None:
        history = "".join(block(self.effects, f"zg361_cp_m68_route_{letter}_effect") for letter in "ab")
        self.assertIn("has_variable = zg361_b2_pip_state", history)
        self.assertNotRegex(history, r"(?:set|change|remove)_variable = \{ name = zg361_b2_")

    def test_project_is_a_stable_versioned_object_not_a_receipt_alias(self) -> None:
        expected_owners = {
            "a": "$TICKET_SUBJECT$",
            "b": "var:zg361_cp_cross_reviewer",
        }
        for letter, owner in expected_owners.items():
            creator = block(self.effects, f"zg361_cp_m30_route_{letter}_effect")
            with self.subTest(route=letter):
                self.assertIn("project_object_manager value = $TICKET_OWNER$", creator)
                self.assertIn(f"project_object_owner value = {owner}", creator)
                self.assertIn("project_object_subject value = $TICKET_SUBJECT$", creator)
                self.assertIn("project_object_cycle value = $TICKET_CYCLE$", creator)
                self.assertIn("project_object_origin_case value = $TICKET_CASE$", creator)
                self.assertIn("project_object_version value = 1", creator)
                self.assertIn("project_object_deadline_cycle add = 2", creator)
        for spec in gen.MECHANISMS:
            if spec.mid == 30:
                continue
            route = block(self.effects, f"zg361_cp_m{spec.mid}_route_a_effect")
            with self.subTest(mid=spec.mid):
                self.assertLess(route.index("project_object_manager = $TICKET_OWNER$"), route.index("record_operation"))
                self.assertLess(route.index("project_object_subject = $TICKET_SUBJECT$"), route.index("record_operation"))
                self.assertIn("project_object_version add = 1", route)

    def test_report_packet_has_its_own_identity_version_and_project_link(self) -> None:
        creator = block(self.effects, "zg361_cp_m54_route_a_effect")
        for token in (
            "report_object_owner value = $TICKET_OWNER$",
            "report_object_subject value = $TICKET_SUBJECT$",
            "report_object_cycle value = $TICKET_CYCLE$",
            "report_object_case value = $TICKET_CASE$",
            "report_object_version value = 1",
            "report_object_deadline_cycle add = 1",
            "report_project_origin_case value = var:zg361_cp_project_object_origin_case",
        ):
            self.assertIn(token, creator)
        for mid in (56, 57, 58, 59, 55, 60):
            route = block(self.effects, f"zg361_cp_m{mid}_route_a_effect")
            self.assertLess(route.index("report_object_case = $TICKET_CASE$"), route.index("record_operation"))
            self.assertIn("report_object_version add = 1", route)

    def test_every_consumer_publishes_project_identity_version_deadline_and_status(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_cp_m{spec.mid}_consume_effect")
            with self.subTest(mid=spec.mid):
                for source in (
                    "zg361_cp_project_object_manager",
                    "zg361_cp_project_object_owner",
                    "zg361_cp_project_object_subject",
                    "zg361_cp_project_object_origin_case",
                    "zg361_cp_project_object_version",
                    "zg361_cp_project_object_deadline_cycle",
                    "zg361_cp_project_object_status",
                ):
                    self.assertIn(f"has_variable = {source}", consumer)
                    self.assertIn(f"value = var:{source}", consumer)
        finalizer = block(self.effects, "zg361_cp_finalize_portfolio_effect")
        self.assertIn("project_object_version = 27", finalizer)
        self.assertIn("report_object_version = 7", finalizer)


class LocalizationAndBoundaryTests(unittest.TestCase):
    def test_localization_keysets_match_and_seven_languages_are_english_placeholders(self) -> None:
        paths = {
            language: MOD_ROOT / "localization" / language / f"zg361_credit_project_l_{language}.yml"
            for language in gen.LANGUAGES
        }
        rows = {language: loc_rows(path) for language, path in paths.items()}
        expected_keys = {
            key
            for mid in EXPECTED_IDS
            for key in (f"zg361cp.{mid}.t", f"zg361cp.{mid}.desc", *(f"zg361cp.{mid}.{letter}" for letter in "abc"))
        }
        for language, mapping in rows.items():
            with self.subTest(language=language):
                self.assertEqual(set(mapping), expected_keys)
                self.assertEqual(len(mapping), 135)
        for language in set(gen.LANGUAGES) - {"english", "simp_chinese"}:
            self.assertEqual(rows[language], rows["english"])
        self.assertNotEqual(rows["simp_chinese"], rows["english"])
        for mid in EXPECTED_IDS:
            with self.subTest(mid=mid, route="c"):
                self.assertEqual(rows["english"][f"zg361cp.{mid}.c"], gen.DEFER_ROUTE_EN)
                self.assertEqual(rows["simp_chinese"][f"zg361cp.{mid}.c"], gen.DEFER_ROUTE_CN)

    def test_generated_headers_and_namespace_are_stable(self) -> None:
        effects = read(EFFECTS_PATH)
        events = read(EVENTS_PATH)
        self.assertTrue(effects.startswith(gen.HEADER))
        self.assertTrue(events.startswith(gen.HEADER + "namespace = zg361cp"))

    def test_runtime_spec_names_scope_role_and_non_live_boundary(self) -> None:
        spec = read(SPEC_PATH)
        for text in ("026–031", "054–061", "062–068", "129–134", "owner + subject + cycle + case + state", "static-ready"):
            self.assertIn(text, spec)
        self.assertIn("伯爵和男爵可以作为 SUBJECT", spec)
        self.assertIn("法、德、日、韩、波、俄、西文件使用英文结构占位", spec)
        self.assertIn("不新增 on_action", spec)
        self.assertIn("tools/mechanism_acceptance/acceptance_*.json", spec)
        self.assertIn("docs/361-phase2-full-implementation-program.md", spec)
        self.assertIn("C 全部是纯 `policy.defer`", spec)
        self.assertIn("zg361_b2_management_debt", spec)
        self.assertIn("恰好等于", spec)
        self.assertIn("zg361_cp_settle_deferred_portfolio_effect", spec)
        self.assertIn("同周期 finalizer 不释放容量", spec)

    def test_no_out_of_scope_generated_mechanism_ids(self) -> None:
        effects = read(EFFECTS_PATH)
        events = read(EVENTS_PATH)
        defined = {int(mid) for mid in re.findall(r"^zg361_cp_m(\d+)_consume_effect = \{$", effects, re.MULTILINE)}
        event_ids = {int(mid) for mid in re.findall(r"^zg361cp\.(\d+) = \{$", events, re.MULTILINE)}
        self.assertEqual(defined, EXPECTED_IDS)
        self.assertEqual(event_ids, EXPECTED_IDS | set(gen.QUEUE_EVENTS.values()))
        self.assertNotIn("zg361_scoreboard", effects)
        self.assertNotIn("zg361_b1_", effects)


if __name__ == "__main__":
    unittest.main(verbosity=2)
