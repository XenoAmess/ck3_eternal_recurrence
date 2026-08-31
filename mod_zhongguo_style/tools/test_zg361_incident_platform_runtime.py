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
ILLEGAL_TRIGGER_ARITHMETIC_RHS = re.compile(
    r"(?:\b(?:root\.)?var:[^\s{}=<>]+|\bscope:[^\s{}=<>]+|\$[A-Z0-9_]+\$)"
    r"\s*(?:=|>=|<=|>|<)\s*\{\s*value\s*="
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(source: str, name: str) -> str:
    # Older callers passed the assignment token as part of ``name``.  Match
    # the exact left-hand symbol either way so prefix names cannot collide.
    symbol = re.sub(r"\s*=\s*$", "", name)
    match = re.search(rf"(?m)^{re.escape(symbol)}\s*=", source)
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
        cls.values = text(gen.VALUES_PATH)
        cls.core_values = text(MOD_ROOT / "common/script_values/zg361_values.txt")

    def test_generator_check_and_utf8_bom(self) -> None:
        gen.write_outputs(check=True)
        for path, payload in gen.outputs().items():
            self.assertTrue(path.read_bytes().startswith(gen.BOM), path)
            self.assertEqual(path.read_bytes(), payload, path)

    def test_trigger_arithmetic_never_uses_a_value_block_rhs(self) -> None:
        self.assertIsNone(
            ILLEGAL_TRIGGER_ARITHMETIC_RHS.search(self.effects),
            "CK3 scripted-effect loader treats RHS value/add/multiply as triggers",
        )
        due = block(self.effects, "zg361_ip_m192_consume_due_debt_effect")
        self.assertIn("save_temporary_scope_value_as", due)
        self.assertIn("debt_id = scope:zg361_ip_expected_debt_id", due)

    def test_balanced_effect_and_event_braces(self) -> None:
        for source in (self.effects, self.events, self.values):
            without_strings = re.sub(r'"(?:\\.|[^"\\])*"', "", source)
            self.assertEqual(without_strings.count("{"), without_strings.count("}"))

    def test_only_observed_world_or_resource_facts_create_an_incident(self) -> None:
        capture = block(self.effects, "zg361_ip_capture_real_incident_effect")
        for fact in (
            "is_at_war = yes",
            "gold < 0",
            "government_has_flag = government_has_treasury treasury < 0",
            "capital_county = { county_control <= 50 }",
        ):
            self.assertIn(fact, capture)
        for token in (
            "zg361_ip_probe_result value = 0",
            "zg361_ip_probe_source_kind value = 0",
            "zg361_ip_probe_consequence_kind value = 0",
            "zg361_ip_probe_world_consequence",
            "zg361_ip_probe_resource_consequence",
            "zg361_ip_incident_serial add = 1",
        ):
            self.assertIn(token, capture)
        self.assertNotIn("random", capture.lower())
        self.assertNotIn("chance", capture.lower())
        self.assertNotIn("root = { is_at_war = yes }", capture)
        self.assertRegex(
            capture,
            r"limit = \{\s*is_at_war = yes\s*"
            r"capital_county = \{ county_control <= 50 \}\s*\}",
        )

    def test_probe_freezes_real_manager_treasury_without_zero_fill(self) -> None:
        capture = block(self.effects, "zg361_ip_capture_real_incident_effect")
        freeze = (
            "set_variable = { name = zg361_ip_probe_manager_treasury "
            "value = root.treasury }"
        )
        self.assertEqual(capture.count(freeze), 1)
        self.assertNotIn(
            "name = zg361_ip_probe_manager_treasury value = 0",
            capture,
        )

        # A cache hit is ready only when all three resource facts from the
        # original probe frame exist.  This makes variable presence the
        # provider's explicit readiness provenance and rejects partial rows.
        cache_guard = capture[: capture.index("else_if = {")]
        for variable in (
            "zg361_ip_probe_subject_gold",
            "zg361_ip_probe_manager_treasury",
            "zg361_ip_probe_capital_control",
        ):
            self.assertIn(f"has_variable = {variable}", cache_guard)

        fresh_probe = capture[capture.index("else_if = {") :]
        freeze_at = fresh_probe.index(freeze)
        self.assertEqual(
            fresh_probe[:freeze_at].count(
                "government_has_flag = government_has_treasury"
            ),
            1,
        )
        subject_at = fresh_probe.index(
            "name = zg361_ip_probe_subject_gold value = gold"
        )
        treasury_at = fresh_probe.index(
            "name = zg361_ip_probe_manager_treasury value = root.treasury"
        )
        control_at = fresh_probe.index(
            "name = zg361_ip_probe_capital_control "
            "value = capital_county.county_control"
        )
        classification_at = fresh_probe.index("is_at_war = yes")
        self.assertLess(subject_at, treasury_at)
        self.assertLess(treasury_at, control_at)
        self.assertLess(control_at, classification_at)

    def test_no_incident_is_exact_na_and_never_opens_a_case(self) -> None:
        for domain in gen.DOMAINS:
            entry = block(self.effects, f"zg361_ip_open_{domain.slug}_case_on_subject_effect")
            capture_at = entry.index("zg361_ip_capture_real_incident_effect = yes")
            open_at = entry.index(f"zg361_case_{domain.slug}_open_effect = yes")
            na_at = entry.index(f"zg361_ip_mark_{domain.slug}_not_applicable_effect = yes")
            self.assertLess(capture_at, open_at)
            self.assertLess(open_at, na_at)
            self.assertIn("var:zg361_ip_capture_status = 1", entry[:open_at])
            self.assertIn("var:zg361_ip_capture_status = 0", entry[open_at:na_at])
            na = block(self.effects, f"zg361_ip_mark_{domain.slug}_not_applicable_effect")
            self.assertNotIn(f"zg361_case_{domain.slug}_open_effect", na)
            self.assertNotIn("zg361_case_kernel", na)
            for exact_zero in (
                "var:zg361_ip_probe_result = 0",
                "var:zg361_ip_probe_source_kind = 0",
                "var:zg361_ip_probe_consequence_kind = 0",
                f"name = zg361_ip_{domain.slug}_final_applicable value = 0",
                f"name = zg361_ip_{domain.slug}_final_kpi_staged value = 0",
            ):
                self.assertIn(exact_zero, na)

    def test_all_37_operations_require_the_same_real_incident_tuple(self) -> None:
        for mechanism_id in range(192, 229):
            domain = gen.DOMAIN_BY_ID[mechanism_id]
            body = block(self.effects, f"zg361_ip_m{mechanism_id:03d}_apply_effect")
            receipt_at = body.index("zg361_case_kernel_record_operation_effect")
            guard = body[:receipt_at]
            for token in (
                "var:zg361_ip_incident_active = 1",
                "var:zg361_ip_incident_owner = $TICKET_OWNER$",
                "var:zg361_ip_incident_subject = $TICKET_SUBJECT$",
                "var:zg361_ip_incident_cycle = $TICKET_CYCLE$",
                f"var:zg361_ip_{domain.slug}_input_incident_serial = var:zg361_ip_incident_serial",
                f"var:zg361_ip_{domain.slug}_input_source_kind = var:zg361_ip_incident_source_kind",
                f"var:zg361_ip_{domain.slug}_input_consequence_kind = var:zg361_ip_incident_consequence_kind",
            ):
                self.assertIn(token, guard, (mechanism_id, token))

    def test_business_objects_and_policy_debts_keep_incident_provenance(self) -> None:
        for mechanism_id in range(192, 229):
            prefix = f"zg361_ip_m{mechanism_id:03d}"
            route = gen._route_assignment(mechanism_id)
            for lane in ("object", "debt"):
                self.assertIn(f"{prefix}_{lane}_incident_serial", route)
                self.assertIn(f"{prefix}_{lane}_incident_source_kind", route)
                self.assertIn(f"{prefix}_{lane}_incident_consequence_kind", route)

    def test_next_cycle_kpi_is_read_only_staged_and_consumed_once(self) -> None:
        value = block(self.values, "zg361_ip_next_cycle_kpi_value")
        consumer = block(self.effects, "zg361_ip_consume_due_kpi_inputs_effect")
        self.assertNotIn("set_variable", value)
        self.assertNotIn("change_variable", value)
        self.assertNotIn("zg361_kpi_value", self.effects)
        for domain in gen.DOMAINS:
            dp = f"zg361_ip_{domain.slug}"
            finalizer = block(self.effects, f"zg361_ip_finalize_{domain.slug}_effect")
            self.assertEqual(value.count(f"add = var:{dp}_kpi_score"), 1)
            self.assertIn(f"var:{dp}_kpi_pending = 1", value)
            self.assertIn(f"var:{dp}_kpi_consumed = 0", value)
            self.assertIn(f"has_variable = {dp}_kpi_due_offset", value)
            self.assertIn(f"var:{dp}_kpi_due_offset = 1", value)
            self.assertIn(f"var:{dp}_kpi_due_cycle > var:{dp}_kpi_origin_cycle", value)
            self.assertIn(
                f"var:zg361_b1_cycle_serial >= prev.var:{dp}_kpi_due_cycle",
                value,
            )
            self.assertIn(
                f"var:zg361_review_serial >= prev.var:{dp}_kpi_origin_cycle",
                value,
            )
            self.assertIn(
                f"name = {dp}_kpi_due_cycle value = var:zg361_case_{domain.slug}_cycle_serial",
                finalizer,
            )
            self.assertIn(f"name = {dp}_kpi_due_cycle add = 1", finalizer)
            self.assertIn(f"name = {dp}_kpi_due_offset value = 1", finalizer)
            self.assertIn(f"name = {dp}_kpi_pending value = 0", consumer)
            self.assertIn(f"name = {dp}_kpi_consumed value = 1", consumer)
            self.assertIn(f"name = {dp}_kpi_receipt_serial add = 1", consumer)
            self.assertIn(f"name = {dp}_kpi_consumed_score value = var:{dp}_kpi_score", consumer)
            self.assertIn(f"name = {dp}_kpi_consumed_due_cycle value = var:{dp}_kpi_due_cycle", consumer)

        organization = block(self.core_values, "zg361_kpi_organization_evidence_value")
        authoritative = block(self.core_values, "zg361_kpi_value")
        self.assertEqual(organization.count("add = zg361_ip_next_cycle_kpi_value"), 1)
        self.assertNotIn("zg361_ip_next_cycle_kpi_value", authoritative)
        expected_components = (
            "governance", "capability", "growth", "superior", "values",
            "collaboration", "jingcha", "organization",
        )
        self.assertEqual(
            re.findall(r"\badd\s*=\s*zg361_kpi_([a-z_]+)_evidence_value", authoritative),
            list(expected_components),
        )

        # The official legacy review serial is incremented only after KPI
        # freeze, so review_serial == origin means the prospective cycle is
        # origin+1.  Active B1 already exposes that prospective serial.
        def eligible(*, b1: bool, b1_cycle: int, review: int, origin: int, due: int) -> bool:
            exact_next = due == origin + 1
            return exact_next and (b1_cycle >= due if b1 else review >= origin)

        self.assertFalse(eligible(b1=True, b1_cycle=7, review=7, origin=7, due=8))
        self.assertTrue(eligible(b1=True, b1_cycle=8, review=7, origin=7, due=8))
        self.assertFalse(eligible(b1=False, b1_cycle=0, review=6, origin=7, due=8))
        self.assertTrue(eligible(b1=False, b1_cycle=0, review=7, origin=7, due=8))
        self.assertFalse(eligible(b1=False, b1_cycle=0, review=7, origin=7, due=7))
        self.assertFalse(eligible(b1=False, b1_cycle=0, review=8, origin=7, due=9))

    def test_route_c_penalties_stage_an_exact_aggregate_instead_of_mutating_kpi(self) -> None:
        stage = block(self.effects, "zg361_ip_stage_policy_debt_kpi_effect")
        consumer = block(self.effects, "zg361_ip_consume_due_kpi_inputs_effect")
        value = block(self.values, "zg361_ip_next_cycle_kpi_value")
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", stage)
        self.assertIn("liege = $DEBT_OWNER$", stage)
        self.assertIn("var:zg361_review_serial >= $DEBT_DUE_CYCLE$", stage)
        self.assertIn("$DEBT_DUE_CYCLE$ > $DEBT_CYCLE$", stage)
        self.assertIn("zg361_ip_policy_kpi_origin_cycle value = $DEBT_DUE_CYCLE$", stage)
        self.assertIn("zg361_ip_policy_kpi_due_cycle value = $DEBT_DUE_CYCLE$", stage)
        self.assertIn("zg361_ip_policy_kpi_due_cycle add = 1", stage)
        self.assertIn("zg361_ip_policy_kpi_due_offset value = 1", stage)
        self.assertIn("var:zg361_ip_policy_kpi_origin_cycle = $DEBT_DUE_CYCLE$", stage)
        self.assertIn("zg361_ip_policy_kpi_score add = -1", stage)
        self.assertIn("zg361_ip_policy_kpi_entry_count add = 1", stage)
        self.assertEqual(value.count("add = var:zg361_ip_policy_kpi_score"), 1)
        self.assertIn("has_variable = zg361_ip_policy_kpi_origin_cycle", value)
        self.assertIn("has_variable = zg361_ip_policy_kpi_due_cycle", value)
        self.assertIn("has_variable = zg361_ip_policy_kpi_due_offset", value)
        self.assertIn("var:zg361_ip_policy_kpi_due_offset = 1", value)
        self.assertIn("var:zg361_ip_policy_kpi_due_cycle > var:zg361_ip_policy_kpi_origin_cycle", value)
        self.assertIn(
            "var:zg361_b1_cycle_serial >= prev.var:zg361_ip_policy_kpi_due_cycle",
            value,
        )
        self.assertIn(
            "var:zg361_review_serial >= prev.var:zg361_ip_policy_kpi_origin_cycle",
            value,
        )
        self.assertIn("zg361_ip_policy_kpi_pending value = 0", consumer)
        self.assertIn("zg361_ip_policy_kpi_consumed value = 1", consumer)
        self.assertIn("zg361_ip_policy_kpi_receipt_serial add = 1", consumer)
        self.assertIn(
            "var:zg361_ip_kpi_consumer_cycle >= var:zg361_ip_policy_kpi_due_cycle",
            consumer,
        )
        self.assertIn("zg361_ip_policy_kpi_consumed_origin_cycle", consumer)
        self.assertIn("zg361_ip_policy_kpi_consumed_due_cycle", consumer)

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
            self.assertNotIn("zg361_kpi_value", finalizer)
            self.assertIn(f"name = zg361_ip_{domain.slug}_kpi_pending value = 1", finalizer)
            self.assertIn(f"name = zg361_ip_{domain.slug}_kpi_due_cycle", finalizer)
            self.assertIn(f"name = zg361_ip_{domain.slug}_final_kpi_staged value = 1", finalizer)

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
            for field in ("owner", "subject", "cycle", "case", "state", "type_code", "id", "consumer_contract", "consumed", "escalation_count"):
                self.assertIn(f"{prefix}_debt_{field}", route_c)
            self.assertIn(f"id = zg361ip.{gen.DEBT_EVENT[mechanism_id]} days = 365", route_c)
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

    def test_initial_dispatch_calls_bind_loader_required_ticket_state(self) -> None:
        for domain in gen.DOMAINS:
            case = f"zg361_case_{domain.slug}"
            entry = block(self.effects, f"zg361_ip_open_{domain.slug}_case_on_subject_effect")
            dispatch_at = entry.index(f"zg361_ip_{domain.slug}_dispatch_01_effect")
            dispatch = entry[dispatch_at : dispatch_at + 500]
            self.assertIn(f"TICKET_OWNER = var:{case}_owner", dispatch, domain.code)
            self.assertIn(f"TICKET_SUBJECT = var:{case}_subject", dispatch, domain.code)
            self.assertIn(f"TICKET_CYCLE = var:{case}_cycle_serial", dispatch, domain.code)
            self.assertIn(f"TICKET_CASE = var:{case}_case_serial", dispatch, domain.code)
            self.assertIn("TICKET_STATE = 1", dispatch, domain.code)
            dispatcher = block(self.effects, f"zg361_ip_{domain.slug}_dispatch_01_effect")
            self.assertIn("_done_state = $TICKET_STATE$", dispatcher, domain.code)

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
        self.assertEqual(self.events.count("hidden = yes"), 14 + len(gen.DEBT_EVENT))

    def test_every_route_c_debt_has_exact_due_repayment_escalation_and_idempotency(self) -> None:
        for mechanism_id in range(192, 229):
            prefix = f"zg361_ip_m{mechanism_id:03d}"
            due = block(self.effects, f"{prefix}_consume_due_debt_effect")
            domain = gen.DOMAIN_BY_ID[mechanism_id]
            state = domain.stage_for(mechanism_id)
            for field in ("owner", "subject", "cycle", "case", "state", "type_code", "id", "consumer_contract", "due_cycle", "open", "consumed", "escalation_count"):
                self.assertIn(f"{prefix}_debt_{field}", due, (mechanism_id, field))
            self.assertIn(f"{prefix}_debt_type_code = {mechanism_id}", due)
            self.assertIn(f"{prefix}_debt_consumer_contract = {mechanism_id}", due)
            self.assertIn(f"{prefix}_debt_state = {state}", due)
            self.assertIn(f"{prefix}_debt_owner = var:{prefix}_done_owner", due)
            self.assertIn(f"{prefix}_debt_subject = var:{prefix}_done_subject", due)
            self.assertIn(f"{prefix}_debt_cycle = var:{prefix}_done_cycle", due)
            self.assertIn(f"{prefix}_debt_case = var:{prefix}_done_case", due)
            self.assertNotIn("zg361_kpi_value", due)
            self.assertIn("zg361_ip_stage_policy_debt_kpi_effect", due)
            self.assertIn(f"MECHANISM_ID = {mechanism_id}", due)
            self.assertIn(f"DEBT_DUE_CYCLE = var:{prefix}_debt_due_cycle", due)
            self.assertIn(f"{prefix}_debt_kpi_staged value = 1", due)
            self.assertIn(f"change_variable = {{ name = zg361_ip_{domain.slug}_policy_debt add = -1 }}", due)
            self.assertIn(f"{prefix}_debt_open value = 0", due)
            self.assertIn(f"{prefix}_debt_consumed value = 1", due)
            self.assertIn(f"{prefix}_debt_escalation_count < 2", due)
            self.assertIn(f"id = zg361ip.{gen.DEBT_EVENT[mechanism_id]} days = 365", due)
            self.assertIn(f"debt_blocked_reason value = {80000 + mechanism_id}", due)
            self.assertIn("zg361_ip_debt_status value = 2", due)
            event = block(self.events, f"zg361ip.{gen.DEBT_EVENT[mechanism_id]} =")
            self.assertIn("hidden = yes", event)
            self.assertIn(f"{prefix}_consume_due_debt_effect = yes", event)

    def test_debt_repayment_conserves_open_count_and_cross_owner_is_fail_closed(self) -> None:
        for domain in gen.DOMAINS:
            representative = domain.first_id
            prefix = f"zg361_ip_m{representative:03d}"
            due = block(self.effects, f"{prefix}_consume_due_debt_effect")
            identity = due.index(f"{prefix}_debt_owner = var:{prefix}_done_owner")
            settlement = due.index(f"change_variable = {{ name = zg361_ip_{domain.slug}_policy_debt add = -1 }}")
            self.assertLess(identity, settlement)
            self.assertLess(settlement, due.index(f"{prefix}_debt_open value = 0"))
            self.assertIn(f"{prefix}_debt_subject = this", due)
            self.assertIn("zg361_is_celestial_liege_trigger = yes", due)
            self.assertIn(f"debt_red_code value = {81000 + representative}", due)

    def test_dual_payer_paths_are_atomic_and_conserved(self) -> None:
        on_call = block(self.effects, "zg361_ip_m193_apply_effect")
        hazard = block(self.effects, "zg361_ip_m209_apply_effect")
        platform = block(self.effects, "zg361_ip_m220_apply_effect")
        for body, owner in (
            (on_call, "zg361_case_x_owner"),
            (hazard, "zg361_case_y_owner"),
        ):
            self.assertIn(f"var:{owner} = {{ government_has_flag = government_has_treasury treasury >= 6 gold >= 4 }}", body)
            self.assertIn(f"var:{owner} = {{ remove_treasury = 6 remove_short_term_gold = 4 }}", body)
            self.assertIn("add_gold = 10", body)
            self.assertIn("recipient_credit value = 10", body)
            self.assertIn("ledger_status value = 2", body)
            self.assertIn("ledger_status value = 3", body)
        self.assertIn("treasury >= var:zg361_ip_m220_treasury_cost", platform)
        self.assertIn("gold >= var:zg361_ip_m220_personal_cost", platform)
        self.assertIn("remove_short_term_gold = var:zg361_ip_m220_personal_cost", platform)
        self.assertIn("treasury_paid value = var:zg361_ip_m220_treasury_cost", platform)
        self.assertIn("personal_paid value = var:zg361_ip_m220_personal_cost", platform)
        self.assertIn("cost_debt value = var:zg361_ip_m220_showback_cost", platform)
        debit = platform.index("remove_treasury = var:zg361_ip_m220_treasury_cost")
        precheck = platform.index("treasury >= var:zg361_ip_m220_treasury_cost")
        self.assertLess(precheck, debit)
        self.assertEqual(self.effects.count("remove_short_term_gold ="), 3)
        self.assertIsNone(
            re.search(r"(?<!short_term_)\bremove_gold\s*=", self.effects),
            "CK3 1.19.0.6 does not register the bare remove_gold effect",
        )

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
