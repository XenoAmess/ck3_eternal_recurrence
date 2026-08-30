#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static contract tests for the phase-3 AA/AG/AJ CK3 runtime package.

Passing this suite proves deterministic generated structure only.  It is not a
CK3 parser result, paused snapshot, MCP result, or live gameplay evidence.
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

import gen_361_phase3_metrics_delivery_runtime as gen


EFFECTS_PATH = MOD_ROOT / "common" / "scripted_effects" / "zg361_phase3_metrics_delivery_runtime_effects.txt"
EVENTS_PATH = MOD_ROOT / "events" / "zg361_phase3_metrics_delivery_runtime_events.txt"
SPEC_PATH = MOD_ROOT / "docs" / "361-phase3-metrics-delivery-runtime-spec.md"
EXPECTED_IDS = set(range(229, 242)) | set(range(301, 312)) | set(range(334, 345))


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


def loc_rows(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in read(path).splitlines()[1:]:
        match = re.match(r'\s*([^:]+):0\s+"(.*)"\s*$', line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


class GeneratorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)
        cls.events = read(EVENTS_PATH)
        cls.spec = read(SPEC_PATH)
        cls.specs = gen.by_id()

    def test_readiness_is_honest(self) -> None:
        self.assertEqual(gen.READINESS, "ck3-script-static-ready-not-live")
        self.assertIn("No CK3 parser/paused/live evidence is claimed", self.effects)

    def test_exact_id_coverage(self) -> None:
        self.assertEqual(set(self.specs), EXPECTED_IDS)
        self.assertEqual(len(gen.MECHANISMS), 35)
        self.assertEqual(sum(map(len, gen.DOMAIN_ORDER.values())), 35)

    def test_domain_ranges(self) -> None:
        self.assertEqual({mid for mid, spec in self.specs.items() if spec.domain == "aa"}, set(range(229, 242)))
        self.assertEqual({mid for mid, spec in self.specs.items() if spec.domain == "ag"}, set(range(301, 312)))
        self.assertEqual({mid for mid, spec in self.specs.items() if spec.domain == "aj"}, set(range(334, 345)))

    def test_unique_semantic_fields(self) -> None:
        self.assertEqual(len({spec.field for spec in gen.MECHANISMS}), 35)

    def test_outputs_are_exactly_independent_package(self) -> None:
        outputs = gen.outputs()
        self.assertEqual(len(outputs), 11)
        self.assertEqual({path.name for path in outputs}, {
            "zg361_phase3_metrics_delivery_runtime_effects.txt",
            "zg361_phase3_metrics_delivery_runtime_events.txt",
            *(f"zg361_phase3_metrics_delivery_l_{language}.yml" for language in gen.LANGUAGES),
        })

    def test_generator_check_mode_is_green(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOLS / "gen_361_phase3_metrics_delivery_runtime.py"), "--check"],
            cwd=MOD_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GREEN", result.stdout)

    def test_all_sources_and_outputs_have_bom(self) -> None:
        paths = [TOOLS / "gen_361_phase3_metrics_delivery_runtime.py", Path(__file__), SPEC_PATH, *gen.outputs()]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.read_bytes().startswith(gen.BOM))

    def test_generated_script_braces_balance(self) -> None:
        for path in (EFFECTS_PATH, EVENTS_PATH):
            with self.subTest(path=path):
                payload = read(path)
                self.assertEqual(payload.count("{"), payload.count("}"))

    def test_every_id_has_consumer_three_routes_and_event(self) -> None:
        for mid in sorted(EXPECTED_IDS):
            with self.subTest(mid=mid):
                self.assertIn(f"zg361_p3_m{mid}_consume_effect = {{", self.effects)
                self.assertIn(f"zg361p3.{mid} = {{", self.events)
                for letter in "abc":
                    self.assertIn(f"zg361_p3_m{mid}_route_{letter}_effect = {{", self.effects)
                    self.assertIn(f"name = zg361p3.{mid}.{letter}", block(self.events, f"zg361p3.{mid}"))

    def test_route_count_is_exact(self) -> None:
        route_defs = re.findall(r"^zg361_p3_m(\d+)_route_([abc])_effect = \{$", self.effects, re.MULTILINE)
        consumer_defs = re.findall(r"^zg361_p3_m(\d+)_consume_effect = \{$", self.effects, re.MULTILINE)
        event_defs = re.findall(r"^zg361p3\.(\d+) = \{$", self.events, re.MULTILINE)
        self.assertEqual(len(route_defs), 105)
        self.assertEqual({int(mid) for mid, _ in route_defs}, EXPECTED_IDS)
        self.assertEqual({int(mid) for mid in consumer_defs}, EXPECTED_IDS)
        self.assertEqual({int(mid) for mid in event_defs}, EXPECTED_IDS)

    def test_each_event_has_exactly_three_options(self) -> None:
        for mid in sorted(EXPECTED_IDS):
            with self.subTest(mid=mid):
                event = block(self.events, f"zg361p3.{mid}")
                self.assertEqual(event.count("\n\toption = {"), 3)
                self.assertIn("is_ai = no", event)
                self.assertIn(f"EXPECTED_STATE = {self.specs[mid].state}", event)

    def test_event_root_is_frozen_owner(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                event = block(self.events, f"zg361p3.{spec.mid}")
                self.assertIn(f"this = scope:zg361_p3_{spec.domain}_owner", event)
                for name in ("owner", "subject", "cycle", "case"):
                    self.assertIn(f"exists = scope:zg361_p3_{spec.domain}_{name}", event)

    def test_event_references_are_all_defined(self) -> None:
        referenced = {int(mid) for mid in re.findall(r"trigger_event = \{ id = zg361p3\.(\d+) \}", self.effects + self.events)}
        defined = {int(mid) for mid in re.findall(r"^zg361p3\.(\d+) = \{$", self.events, re.MULTILINE)}
        self.assertEqual(referenced, defined)

    def test_each_route_uses_full_five_tuple_guard(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                with self.subTest(mid=spec.mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                    self.assertIn("zg361_case_kernel_full_guard_trigger", route)
                    for token in ("OWNER_VAR", "SUBJECT_VAR", "CYCLE_VAR", "CASE_VAR", "STATE_VAR", "ACTIVE_VAR"):
                        self.assertIn(token, route)
                    for token in ("EXPECTED_OWNER", "EXPECTED_SUBJECT", "EXPECTED_CYCLE", "EXPECTED_CASE"):
                        self.assertIn(token, route)
                    self.assertIn(f"EXPECTED_STATE = {spec.state}", route)

    def test_cross_route_receipt_is_mutually_exclusive(self) -> None:
        for spec in gen.MECHANISMS:
            names_by_route = []
            for letter in "abc":
                route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                for choice in (1, 2, 3):
                    self.assertIn(f"EXPECTED_CHOICE = {choice}", route)
                names = tuple(
                    re.search(rf"RECEIPT_{kind}_VAR = (zg361_p3_m{spec.mid}_receipt_[a-z]+)", route).group(1)
                    for kind in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE", "CHOICE")
                )
                names_by_route.append(names)
            with self.subTest(mid=spec.mid):
                self.assertEqual(len(set(names_by_route)), 1)

    def test_operation_order_is_atomic(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                with self.subTest(mid=spec.mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                    precheck = route.index(f"var:zg361_p3_{spec.domain}_operation_used <")
                    record = route.index("zg361_case_kernel_record_operation_effect")
                    semantic = route.index(f"name = zg361_p3_{spec.field}")
                    consumer = route.index(f"zg361_p3_m{spec.mid}_consume_effect = yes")
                    self.assertLess(precheck, record)
                    self.assertLess(record, semantic)
                    self.assertLess(semantic, consumer)
                    if spec.mid in gen.STAGE_LAST[spec.domain]:
                        self.assertLess(consumer, route.index(f"zg361_case_{spec.domain}_advance_"))

    def test_typed_red_idempotent_and_stale_are_explicit(self) -> None:
        for spec in gen.MECHANISMS:
            for choice, letter in enumerate("abc", 1):
                with self.subTest(mid=spec.mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                    self.assertIn(f"name = zg361_p3_last_red_code value = {spec.mid * 10 + choice}", route)
                    self.assertIn("value = 4 } # typed RED; no receipt/business/resource write", route)
                    self.assertIn("value = 2 } # idempotent no-op", route)
                    self.assertIn("value = 3 } } # stale no-op", route)

    def test_every_write_has_frozen_tuple_and_provenance(self) -> None:
        for spec in gen.MECHANISMS:
            for choice, letter in enumerate("abc", 1):
                route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    for name in ("owner", "subject", "cycle", "case", "state"):
                        self.assertIn(f"name = zg361_p3_m{spec.mid}_write_{name}", route)
                    self.assertIn(f"name = zg361_p3_m{spec.mid}_provenance_case", route)
                    self.assertIn(f"name = zg361_p3_m{spec.mid}_provenance_choice value = {choice}", route)

    def test_each_consumer_is_guarded_and_idempotent(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                consumer = block(self.effects, f"zg361_p3_m{spec.mid}_consume_effect")
                self.assertGreaterEqual(consumer.count("trigger_if = {"), 2)
                for name in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"has_variable = zg361_p3_m{spec.mid}_write_{name}", consumer)
                    self.assertIn(f"has_variable = zg361_p3_m{spec.mid}_consumed_{name}", consumer)
                    self.assertIn(f"name = zg361_p3_m{spec.mid}_consumed_{name}", consumer)
                self.assertIn(f"value = var:zg361_p3_{spec.field}", consumer)
                self.assertIn(f"name = zg361_p3_m{spec.mid}_visible_provenance_case", consumer)

    def test_only_stage_barriers_advance_and_require_complete_stage(self) -> None:
        for spec in gen.MECHANISMS:
            same_stage = [item.mid for item in gen.MECHANISMS if item.domain == spec.domain and item.state == spec.state]
            for letter in "abc":
                route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    if spec.mid in gen.STAGE_LAST[spec.domain]:
                        self.assertEqual(route.count(f"zg361_case_{spec.domain}_advance_{gen.STAGE_LAST[spec.domain][spec.mid]:02d}_effect"), 1)
                        advance_prefix = route[: route.index(f"zg361_case_{spec.domain}_advance_")]
                        for stage_mid in same_stage:
                            self.assertIn(f"zg361_p3_m{stage_mid}_receipt_choice", advance_prefix)
                    else:
                        self.assertNotIn(f"zg361_case_{spec.domain}_advance_", route)

    def test_stage_graphs_have_all_edges_once_per_route(self) -> None:
        for domain, barriers in gen.STAGE_LAST.items():
            for mid, edge in barriers.items():
                with self.subTest(domain=domain, mid=mid):
                    for letter in "abc":
                        route = block(self.effects, f"zg361_p3_m{mid}_route_{letter}_effect")
                        self.assertIn(f"zg361_case_{domain}_advance_{edge:02d}_effect", route)

    def test_launch_freezes_owner_subject_cycle_and_case(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            with self.subTest(domain=domain):
                launch = block(self.effects, f"zg361_p3_{domain}_launch_effect")
                self.assertIn(f"zg361_case_{domain}_open_effect = yes", launch)
                self.assertIn(f"var:zg361_case_{domain}_owner = {{ save_scope_as = zg361_p3_{domain}_owner }}", launch)
                self.assertIn(f"save_scope_as = zg361_p3_{domain}_subject", launch)
                self.assertIn(f"name = zg361_p3_{domain}_cycle", launch)
                self.assertIn(f"name = zg361_p3_{domain}_case", launch)

    def test_player_and_authorized_ai_paths_are_separate(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            launch = block(self.effects, f"zg361_p3_{domain}_launch_effect")
            ai = block(self.effects, f"zg361_p3_{domain}_run_authorized_ai_effect")
            with self.subTest(domain=domain):
                self.assertIn("is_ai = no zg361_is_celestial_liege_trigger = yes", launch)
                self.assertIn("is_ai = yes zg361_is_celestial_liege_trigger = yes", launch)
                self.assertIn("is_ai = yes zg361_is_celestial_liege_trigger = yes", ai)
                self.assertNotIn("trigger_event", ai)
                for mid in gen.DOMAIN_ORDER[domain]:
                    self.assertEqual(ai.count(f"zg361_p3_m{mid}_route_a_effect"), 1)

    def test_counts_and_barons_have_assessed_only_adapter(self) -> None:
        forbidden = ("_open_effect", "record_operation", "_advance_", "reserve", "PIP", "hc_slot", "calibrat")
        for domain in gen.DOMAIN_ORDER:
            with self.subTest(domain=domain):
                subject_read = block(self.effects, f"zg361_p3_{domain}_subject_read_effect")
                self.assertIn("zg361_case_kernel_subject_self_guard_trigger", subject_read)
                for token in forbidden:
                    self.assertNotIn(token, subject_read)

    def test_domain_operation_capacity_is_conserved(self) -> None:
        for domain, order in gen.DOMAIN_ORDER.items():
            init = block(self.effects, f"zg361_p3_{domain}_initialize_effect")
            with self.subTest(domain=domain):
                self.assertIn(f"name = zg361_p3_{domain}_operation_total value = {len(order)}", init)
                self.assertIn(f"name = zg361_p3_{domain}_operation_used value = 0", init)
                for mid in order:
                    for letter in "abc":
                        route = block(self.effects, f"zg361_p3_m{mid}_route_{letter}_effect")
                        self.assertIn(f"change_variable = {{ name = zg361_p3_{domain}_operation_used add = 1 }}", route)

    def test_aa_sample_slot_precheck_precedes_record(self) -> None:
        for letter in "ab":
            route = block(self.effects, f"zg361_p3_m240_route_{letter}_effect")
            self.assertLess(route.index("var:zg361_p3_aa_sample_used <"), route.index("record_operation"))
            self.assertIn("zg361_p3_aa_sample_used add = 1", route)
        route_c = block(self.effects, "zg361_p3_m240_route_c_effect")
        self.assertNotIn("zg361_p3_aa_sample_used add = 1", route_c)
        self.assertIn("zg361_p3_aa_sample_queue add = 1", route_c)

    def test_basis_point_splits_are_conserved(self) -> None:
        for mid in (234, 235, 238, 241, 342, 344):
            for letter in "abc":
                with self.subTest(mid=mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{mid}_route_{letter}_effect")
                    self.assertRegex(route, rf"m{mid}_(?:share_total|blocker_total) value = 10000")

    def test_ag_matrix_weights_and_hc_are_conserved(self) -> None:
        for letter in "abc":
            dual = block(self.effects, f"zg361_p3_m304_route_{letter}_effect")
            hats = block(self.effects, f"zg361_p3_m306_route_{letter}_effect")
            hc = block(self.effects, f"zg361_p3_m308_route_{letter}_effect")
            self.assertIn("m304_parent_weight_total value = 10000", dual)
            self.assertIn("m304_goal_share_total value = 10000", dual)
            self.assertIn("m304_dual_signature value = 1", dual)
            self.assertIn("m306_weight_total value = 100", hats)
            self.assertIn("zg361_p3_ag_hc_total value = 100", hc)

    def test_ag_visibility_consumes_only_management_capacity(self) -> None:
        for letter in "ab":
            route = block(self.effects, f"zg361_p3_m309_route_{letter}_effect")
            self.assertLess(route.index("management_capacity_remaining >= 10"), route.index("record_operation"))
            self.assertIn("management_capacity_remaining subtract = 10", route)
            self.assertIn("visibility_gain value = 10", route)
        route_c = block(self.effects, "zg361_p3_m309_route_c_effect")
        self.assertIn("visibility_debt add = 10", route_c)

    def test_reorg_history_owner_does_not_drift(self) -> None:
        for letter in "abc":
            route = block(self.effects, f"zg361_p3_m310_route_{letter}_effect")
            self.assertIn("m310_historical_owner value = $TICKET_OWNER$", route)
            self.assertIn("m310_mapped_owner value = $TICKET_OWNER$", route)
        self.assertIn("m311_old_target_locked value = 1", block(self.effects, "zg361_p3_m311_route_a_effect"))

    def test_aj_emergency_and_change_tax_prechecks_are_atomic(self) -> None:
        emergency = block(self.effects, "zg361_p3_m335_route_a_effect")
        self.assertLess(emergency.index("emergency_used <"), emergency.index("record_operation"))
        self.assertIn("emergency_used add = 1", emergency)
        for letter in "ab":
            change = block(self.effects, f"zg361_p3_m337_route_{letter}_effect")
            self.assertLess(change.index("capacity_remaining >= 10"), change.index("record_operation"))
            self.assertIn("capacity_remaining subtract = 10", change)
        waiver = block(self.effects, "zg361_p3_m337_route_c_effect")
        self.assertLess(waiver.index("disaster_waiver_used = 0"), waiver.index("record_operation"))
        self.assertIn("policy_debt add = 10", waiver)

    def test_aj_wip_and_capacity_conserve(self) -> None:
        normal = block(self.effects, "zg361_p3_m340_route_a_effect")
        self.assertLess(normal.index("wip_used < var:zg361_p3_aj_wip_limit"), normal.index("record_operation"))
        for letter in "abc":
            route = block(self.effects, f"zg361_p3_m340_route_{letter}_effect")
            self.assertIn("capacity_remaining subtract = 20", route)
            self.assertIn("capacity_reserved add = 20", route)
            self.assertIn("wip_used add = 1", route)
        self.assertIn("exception_signed value = 1", block(self.effects, "zg361_p3_m340_route_b_effect"))
        self.assertIn("hidden_wip_debt add = 1", block(self.effects, "zg361_p3_m340_route_c_effect"))

    def test_aj_carryover_is_net_zero_current_and_charges_next(self) -> None:
        expected = {"a": 10, "b": 5, "c": 0}
        for letter, carry_hours in expected.items():
            route = block(self.effects, f"zg361_p3_m341_route_{letter}_effect")
            with self.subTest(route=letter):
                self.assertLess(route.index("capacity_reserved >= 10"), route.index("record_operation"))
                self.assertIn("capacity_reserved subtract = 10", route)
                self.assertIn("capacity_remaining add = 10", route)
                self.assertIn(f"m341_transfer_hours value = {carry_hours}", route)
                if carry_hours:
                    self.assertIn(f"next_capacity_remaining subtract = {carry_hours}", route)
                    self.assertIn(f"next_capacity_reserved add = {carry_hours}", route)
                else:
                    self.assertNotIn("next_capacity_remaining subtract", route)
                    self.assertNotIn("next_capacity_reserved add", route)

    def test_aj_signatures_and_value_credit(self) -> None:
        for letter in "abc":
            triangle = block(self.effects, f"zg361_p3_m338_route_{letter}_effect")
            accept = block(self.effects, f"zg361_p3_m343_route_{letter}_effect")
            value = block(self.effects, f"zg361_p3_m344_route_{letter}_effect")
            self.assertIn("m338_tradeoff_signed value = 1", triangle)
            for signer in ("proposer", "executor", "acceptor"):
                self.assertIn(f"m343_{signer}_signed value = 1", accept)
            self.assertLess(value.index("value_credit_remaining = 10000"), value.index("record_operation"))
            self.assertIn("m344_share_total value = 10000", value)
            self.assertIn("value_credit_remaining value = 0", value)

    def test_localization_has_nine_language_key_parity(self) -> None:
        rows = {
            language: loc_rows(MOD_ROOT / "localization" / language / f"zg361_phase3_metrics_delivery_l_{language}.yml")
            for language in gen.LANGUAGES
        }
        expected_keys = {
            key
            for mid in EXPECTED_IDS
            for key in (f"zg361p3.{mid}.t", f"zg361p3.{mid}.desc", f"zg361p3.{mid}.a", f"zg361p3.{mid}.b", f"zg361p3.{mid}.c")
        }
        for language, mapping in rows.items():
            with self.subTest(language=language):
                self.assertEqual(set(mapping), expected_keys)
        self.assertNotEqual(rows["simp_chinese"], rows["english"])

    def test_seven_daily_languages_are_exact_english_placeholders(self) -> None:
        english = loc_rows(MOD_ROOT / "localization" / "english" / "zg361_phase3_metrics_delivery_l_english.yml")
        for language in ("french", "german", "japanese", "korean", "polish", "russian", "spanish"):
            with self.subTest(language=language):
                path = MOD_ROOT / "localization" / language / f"zg361_phase3_metrics_delivery_l_{language}.yml"
                self.assertEqual(read(path).splitlines()[0], f"l_{language}:")
                self.assertEqual(loc_rows(path), english)

    def test_spec_maps_all_ids_once_and_states_static_boundary(self) -> None:
        table_ids = [int(mid) for mid in re.findall(r"\| (?:AA|AG|AJ) \| (\d{3}) / \d", self.spec)]
        self.assertEqual(set(table_ids), EXPECTED_IDS)
        self.assertEqual(len(table_ids), 35)
        self.assertIn("CK3 script static-ready", self.spec)
        self.assertIn("没有中央 `on_action`", self.spec)
        self.assertIn("没有 MCP named action/query", self.spec)
        self.assertIn("没有 CK3 parser/error.log", self.spec)
        self.assertIn("其余七语仍是英文结构占位", self.spec)


if __name__ == "__main__":
    unittest.main(verbosity=2)
