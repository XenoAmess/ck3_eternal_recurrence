#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static contract tests for the X/Y/Z CK3 runtime projection."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_incident_platform_runtime as gen


MOD_ROOT = Path(__file__).resolve().parent.parent


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(source: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}", source)
    if match is None:
        raise AssertionError(f"missing block: {name}")
    start = match.start()
    brace = source.index("{", start)
    depth = 0
    quoted = False
    escaped = False
    for index in range(brace, len(source)):
        char = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unclosed block: {name}")


class SourceDataTests(unittest.TestCase):
    def test_exact_scope_and_three_routes(self) -> None:
        gen.validate_source_data()
        expected = set(range(192, 229))
        self.assertEqual(set(gen.ASSIGNMENTS), expected)
        self.assertEqual(set(gen.SCORES), expected)
        self.assertEqual(set(gen.DOMAIN_BY_ID), expected)
        for mechanism_id in expected:
            for values in gen.ASSIGNMENTS[mechanism_id].values():
                self.assertEqual(len(values), 3)

    def test_shared_stage_partition_matches_frozen_domain_graph(self) -> None:
        expected = {
            "X": ((192, 195), (196, 200), (201, 197), (198, 199), (193, 194), (202, 203), (204,)),
            "Y": ((205, 206, 207), (208, 209), (210, 211, 212), (213, 214), (215, 216)),
            "Z": ((217, 218, 219), (220, 221), (222, 223, 224), (225, 226), (227, 228)),
        }
        for domain in gen.DOMAINS:
            actual = tuple(domain.ids_for_stage(stage) for stage in range(1, domain.transitions + 1))
            self.assertEqual(actual, expected[domain.code])

    def test_conserved_share_and_capacity_vectors(self) -> None:
        for route in range(3):
            self.assertEqual(
                gen.ASSIGNMENTS[197]["command_credit"][route]
                + gen.ASSIGNMENTS[197]["responder_credit"][route],
                100,
            )
            self.assertEqual(
                gen.ASSIGNMENTS[205]["toil_hours"][route]
                + gen.ASSIGNMENTS[205]["delivery_hours"][route],
                100,
            )
            self.assertEqual(
                gen.ASSIGNMENTS[207]["debt_budget_hours"][route]
                + gen.ASSIGNMENTS[207]["business_hours"][route],
                100,
            )
            self.assertEqual(
                gen.ASSIGNMENTS[220]["treasury_cost"][route]
                + gen.ASSIGNMENTS[220]["personal_cost"][route],
                gen.ASSIGNMENTS[220]["total_cost"][route],
            )
            self.assertEqual(
                gen.ASSIGNMENTS[221]["platform_share"][route]
                + gen.ASSIGNMENTS[221]["user_share"][route]
                + gen.ASSIGNMENTS[221]["reform_share"][route],
                100,
            )
            self.assertEqual(
                gen.ASSIGNMENTS[226]["contributor_credit"][route]
                + gen.ASSIGNMENTS[226]["maintainer_credit"][route],
                100,
            )
            self.assertEqual(
                gen.ASSIGNMENTS[227]["founder_credit"][route]
                + gen.ASSIGNMENTS[227]["extension_credit"][route]
                + gen.ASSIGNMENTS[227]["maintenance_credit"][route],
                100,
            )
            self.assertEqual(
                gen.ASSIGNMENTS[228]["platform_liability"][route]
                + gen.ASSIGNMENTS[228]["user_liability"][route]
                + gen.ASSIGNMENTS[228]["policy_liability"][route],
                100,
            )

    def test_countermetrics_can_reverse_vanity_routes(self) -> None:
        for route in range(3):
            self.assertLessEqual(
                gen.ASSIGNMENTS[195]["false_alerts"][route],
                gen.ASSIGNMENTS[195]["alert_total"][route],
            )
        full_high = tuple(
            gen.ASSIGNMENTS[218]["customer_score"][route]
            >= gen.ASSIGNMENTS[218]["dual_floor"][route]
            and gen.ASSIGNMENTS[218]["foundation_score"][route]
            >= gen.ASSIGNMENTS[218]["dual_floor"][route]
            for route in range(3)
        )
        self.assertEqual(full_high, (True, False, False))
        self.assertLess(
            gen.ASSIGNMENTS[214]["quality_score"][1],
            gen.ASSIGNMENTS[214]["coverage_percent"][1],
        )


class GeneratedFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = text(gen.EFFECTS_PATH)
        cls.events = text(gen.EVENTS_PATH)

    def test_generator_check_and_utf8_bom(self) -> None:
        gen.write_outputs(check=True)
        for path, payload in gen.outputs().items():
            self.assertTrue(path.read_bytes().startswith(gen.BOM), path)
            self.assertEqual(path.read_bytes(), payload, path)

    def test_balanced_effect_and_event_braces(self) -> None:
        for source in (self.effects, self.events):
            without_strings = re.sub(r'"(?:\\.|[^"\\])*"', "", source)
            self.assertEqual(without_strings.count("{"), without_strings.count("}"))

    def test_every_id_is_one_typed_five_field_operation(self) -> None:
        operation_ids: list[int] = []
        for mechanism_id in range(192, 229):
            body = block(self.effects, f"zg361_ip_m{mechanism_id:03d}_apply_effect")
            operation_ids.extend(int(value) for value in re.findall(r"OPERATION_ID = (\d+)", body))
            self.assertEqual(body.count("zg361_case_kernel_record_operation_effect"), 1)
            for field in ("TICKET_OWNER", "TICKET_SUBJECT", "TICKET_CYCLE", "TICKET_CASE", "TICKET_STATE"):
                self.assertIn(f"{field} = ${field}$", body)
            self.assertIn(f"zg361_ip_m{mechanism_id:03d}_done_cycle", body)
            self.assertIn(f"zg361_ip_m{mechanism_id:03d}_done_case", body)
            self.assertIn("CHOICE = var:zg361_ip_m", body)
        self.assertEqual(operation_ids, list(range(192, 229)))

    def test_each_write_has_a_real_domain_consumer(self) -> None:
        for mechanism_id in range(192, 229):
            domain = gen.DOMAIN_BY_ID[mechanism_id]
            body = block(self.effects, f"zg361_ip_m{mechanism_id:03d}_apply_effect")
            output = f"zg361_ip_m{mechanism_id:03d}_result_score"
            self.assertIn(f"set_variable = {{ name = {output}", body)
            self.assertIn(
                f"change_variable = {{ name = zg361_ip_{domain.slug}_score_delta add = var:{output} }}",
                body,
            )
            self.assertIn(f"set_variable = {{ name = zg361_ip_{domain.slug}_last_consumer value = {mechanism_id} }}", body)
            self.assertTrue(gen._special_consumer(mechanism_id), mechanism_id)
        for domain in gen.DOMAINS:
            finalizer = block(self.effects, f"zg361_ip_finalize_{domain.slug}_effect")
            self.assertIn(f"divide = var:zg361_ip_{domain.slug}_evidence_n", finalizer)
            self.assertIn("change_variable = { name = zg361_kpi_value", finalizer)

    def test_every_id_has_exact_object_consumer_resource_and_deadline_projection(self) -> None:
        for mechanism_id, behavior in gen.BEHAVIORS.items():
            prefix = f"zg361_ip_m{mechanism_id:03d}"
            route = gen._route_assignment(mechanism_id)
            effect = block(self.effects, f"{prefix}_apply_effect")
            self.assertIn(f"{prefix}_object_{behavior.object_type} value = 1", route)
            self.assertIn(f"{prefix}_object_type_code value = {mechanism_id}", route)
            self.assertIn(f"{prefix}_consumer_contract value = {mechanism_id}", route)
            for name in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"{prefix}_object_{name}", route)
            for resource_book in behavior.resource_books:
                self.assertIn(f"{prefix}_resource_{resource_book} value = 1", route)
            if behavior.deadline_cycles:
                self.assertIn(f"{prefix}_object_due_cycle", route)
            self.assertIn(f"{prefix}_consumer_{behavior.consumer_method} value = 1", effect)
            self.assertIn(f"{prefix}_object_consumed value = 1", effect)

    def test_route_c_creates_only_due_policy_debt_not_a_business_object(self) -> None:
        for mechanism_id in range(192, 229):
            prefix = f"zg361_ip_m{mechanism_id:03d}"
            projection = gen._route_assignment(mechanism_id)
            route_c = projection.rsplit("\t\telse = {", 1)[1]
            self.assertIn(f"{prefix}_business_object_created value = 0", route_c)
            self.assertIn(f"{prefix}_debt_due_cycle", route_c)
            self.assertIn(f"{prefix}_debt_open value = 1", route_c)
            self.assertNotIn(f"{prefix}_object_type_code", route_c)
            for semantic_field in gen.ASSIGNMENTS[mechanism_id]:
                self.assertNotIn(f"{prefix}_{semantic_field}", route_c)
            body = block(self.effects, f"{prefix}_apply_effect")
            self.assertIn(f"{prefix}_debt_visible_to_settlement value = 1", body)

    def test_dependent_consumers_reject_stale_or_deferred_predecessor_objects(self) -> None:
        expected = {
            194: (193,), 197: (201,), 198: (197,), 202: (201,), 203: (202,), 204: (196,),
            207: (206,), 208: (206, 207), 211: (210,), 214: (213,), 215: (214,),
            216: (215,), 218: (217,), 219: (218,), 220: (219,), 221: (220,),
            222: (221,), 223: (222,), 224: (223,), 225: (224,), 226: (225,),
            227: (226,), 228: (227,),
        }
        self.assertEqual(expected, gen.CURRENT_OBJECT_DEPENDENCIES)
        for mechanism_id, dependencies in expected.items():
            body = block(self.effects, f"zg361_ip_m{mechanism_id:03d}_apply_effect")
            receipt = body.index("zg361_case_kernel_record_operation_effect")
            for source_id in dependencies:
                source = f"zg361_ip_m{source_id:03d}"
                source_behavior = gen.BEHAVIORS[source_id]
                source_state = gen.DOMAIN_BY_ID[source_id].stage_for(source_id)
                for fragment in (
                    f"has_variable = {source}_object_type_code",
                    f"has_variable = {source}_object_owner",
                    f"has_variable = {source}_object_subject",
                    f"has_variable = {source}_object_cycle",
                    f"has_variable = {source}_object_case",
                    f"has_variable = {source}_consumer_{source_behavior.consumer_method}",
                    f"var:{source}_object_type_code = {source_id}",
                    f"var:{source}_object_owner = $TICKET_OWNER$",
                    f"var:{source}_object_subject = $TICKET_SUBJECT$",
                    f"var:{source}_object_cycle = $TICKET_CYCLE$",
                    f"var:{source}_object_case = $TICKET_CASE$",
                    f"var:{source}_object_state = {source_state}",
                    f"var:{source}_consumer_contract = {source_id}",
                    f"var:{source}_object_consumed = 1",
                    f"var:{source}_consumer_{source_behavior.consumer_method} = 1",
                ):
                    self.assertIn(fragment, body, (source_id, mechanism_id, fragment))
                self.assertLess(body.index(f"has_variable = {source}_object_case"), receipt)
            self.assertIn(f"zg361_ip_m{mechanism_id:03d}_prerequisite_deferred value = 1", body)

    def test_semantic_execution_order_and_full_done_identity_are_frozen(self) -> None:
        self.assertEqual(
            (192, 195, 196, 200, 201, 197, 198, 199, 193, 194, 202, 203, 204),
            gen.EXECUTION_ORDER["X"],
        )
        self.assertLess(gen.EXECUTION_ORDER["X"].index(201), gen.EXECUTION_ORDER["X"].index(197))
        stage_three = block(self.effects, "zg361_ip_x_dispatch_03_effect")
        self.assertLess(stage_three.index("zg361_ip_m201_apply_effect"), stage_three.index("zg361_ip_m197_apply_effect"))
        credit = block(self.effects, "zg361_ip_m197_apply_effect")
        self.assertIn("timeline_revision_used value = var:zg361_ip_m201_timeline_revision", credit)
        for mechanism_id in range(192, 229):
            body = block(self.effects, f"zg361_ip_m{mechanism_id:03d}_apply_effect")
            for name in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"zg361_ip_m{mechanism_id:03d}_done_{name}", body)
            self.assertIn("$TICKET_OWNER$", body)
            self.assertIn("$TICKET_SUBJECT$", body)

    def test_all_stages_have_one_dispatch_transition_and_bound_deadline(self) -> None:
        for domain in gen.DOMAINS:
            for stage in range(1, domain.transitions + 1):
                body = block(self.effects, f"zg361_ip_{domain.slug}_dispatch_{stage:02d}_effect")
                self.assertEqual(body.count(f"zg361_case_{domain.slug}_advance_{stage:02d}_effect"), 1)
                for mechanism_id in domain.ids_for_stage(stage):
                    self.assertEqual(body.count(f"zg361_ip_m{mechanism_id:03d}_apply_effect"), 1)
                    self.assertIn(f"zg361_ip_m{mechanism_id:03d}_done_cycle", body)
                if stage < domain.transitions:
                    self.assertIn("zg361_case_kernel_schedule_deadline_effect", body)
                else:
                    self.assertIn(f"zg361_ip_finalize_{domain.slug}_effect", body)

    def test_delayed_events_expire_frozen_ticket_before_dispatch(self) -> None:
        expected_hidden = 0
        for domain in gen.DOMAINS:
            for state in range(2, domain.final_state):
                expected_hidden += 1
                due = block(self.effects, f"zg361_ip_{domain.slug}_due_{state:02d}_effect")
                self.assertIn("zg361_case_kernel_expire_deadline_effect", due)
                self.assertIn(f"zg361_ip_{domain.slug}_dispatch_{state:02d}_effect", due)
                event_id = domain.event_base + state
                event = block(self.events, f"zg361ip.{event_id} =")
                self.assertIn("hidden = yes", event)
                self.assertIn(f"zg361_ip_{domain.slug}_due_{state:02d}_effect", event)
        self.assertEqual(expected_hidden, 14)
        self.assertEqual(self.events.count("hidden = yes"), 14)

    def test_dual_payer_paths_are_atomic_and_conserved(self) -> None:
        on_call = block(self.effects, "zg361_ip_m193_apply_effect")
        hazard = block(self.effects, "zg361_ip_m209_apply_effect")
        platform = block(self.effects, "zg361_ip_m220_apply_effect")
        for body, owner in (
            (on_call, "zg361_case_x_owner"),
            (hazard, "zg361_case_y_owner"),
        ):
            self.assertIn(f"var:{owner} = {{ government_has_flag = government_has_treasury treasury >= 6 gold >= 4 }}", body)
            self.assertIn(f"var:{owner} = {{ remove_treasury = 6 remove_gold = 4 }}", body)
            self.assertIn("add_gold = 10", body)
            self.assertIn("recipient_credit value = 10", body)
            self.assertIn("ledger_status value = 2", body)
            self.assertIn("ledger_status value = 3", body)
        self.assertIn("treasury >= var:zg361_ip_m220_treasury_cost", platform)
        self.assertIn("gold >= var:zg361_ip_m220_personal_cost", platform)
        self.assertIn("treasury_paid value = var:zg361_ip_m220_treasury_cost", platform)
        self.assertIn("personal_paid value = var:zg361_ip_m220_personal_cost", platform)
        self.assertIn("cost_debt value = var:zg361_ip_m220_showback_cost", platform)
        debit = platform.index("remove_treasury = var:zg361_ip_m220_treasury_cost")
        precheck = platform.index("treasury >= var:zg361_ip_m220_treasury_cost")
        self.assertLess(precheck, debit)

    def test_incident_platform_and_maintenance_domain_specific_consumers_exist(self) -> None:
        expected = {
            198: "net_firefighting_credit",
            204: "severity_fact_used",
            208: "debt_after_repayment",
            216: "retirement_gate_used",
            218: "full_high_eligible",
            220: "cost_debt",
            226: "credit_check",
            228: "liability_check",
        }
        for mechanism_id, fragment in expected.items():
            self.assertIn(fragment, block(self.effects, f"zg361_ip_m{mechanism_id:03d}_apply_effect"))

    def test_permissions_keep_ai_manager_path_and_subject_boundary(self) -> None:
        portfolio = block(self.effects, "zg361_ip_open_portfolio_effect")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", portfolio)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", portfolio)
        self.assertNotIn("is_ai = no", portfolio)
        self.assertIn("zg361_ip_portfolio_cycle", portfolio)
        self.assertIn("NOT = { var:zg361_ip_portfolio_cycle = var:zg361_review_serial }", portfolio)
        for domain in gen.DOMAINS:
            entry = block(self.effects, f"zg361_ip_open_{domain.slug}_case_on_subject_effect")
            self.assertIn(f"zg361_case_{domain.slug}_open_effect = yes", entry)
        self.assertNotIn("subject_open", self.effects)
        self.assertNotIn("highest_held_title_tier", self.effects)

    def test_ai_is_silent_but_player_gets_one_closure_notice_per_domain(self) -> None:
        self.assertEqual(self.events.count("# Player manager closure notice"), 3)
        for domain in gen.DOMAINS:
            event = block(self.events, f"zg361ip.{domain.result_event} =")
            self.assertIn("is_ai = no", event)
            self.assertIn("exists = scope:zg361_ip_result_subject", event)
        self.assertEqual(self.events.count("theme = vassal"), 3)

    def test_projection_adds_no_gui_decision_interaction_or_on_action(self) -> None:
        generated_paths = {path.relative_to(MOD_ROOT).as_posix() for path in gen.outputs()}
        self.assertFalse(any(path.startswith("gui/") for path in generated_paths))
        self.assertFalse(any("decisions" in path for path in generated_paths))
        self.assertFalse(any("interactions" in path for path in generated_paths))
        self.assertFalse(any("on_action" in path for path in generated_paths))
        self.assertNotIn("scripted_widget", self.effects)

    def test_localization_is_complete_and_placeholders_are_honest(self) -> None:
        expected_keys = {"zg361ip.result.ok"}
        expected_keys.update(
            f"zg361ip.{domain.result_event}.{suffix}"
            for domain in gen.DOMAINS
            for suffix in ("t", "desc")
        )
        expected_keys.update(
            f"zg361_ip_m{mechanism_id:03d}_{suffix}"
            for mechanism_id in range(192, 229)
            for suffix in ("name", "result")
        )
        english = gen._loc_rows("english")
        chinese = gen._loc_rows("simp_chinese")
        self.assertEqual(set(english), expected_keys)
        self.assertEqual(set(chinese), expected_keys)
        self.assertNotEqual(english, chinese)
        for language in gen.LANGUAGES:
            rows = gen._loc_rows(language)
            self.assertEqual(set(rows), expected_keys)
            if language not in {"english", "simp_chinese"}:
                self.assertEqual(rows, english)


if __name__ == "__main__":
    unittest.main()
