#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static contract tests for the isolated Workforce remediation producer."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
MOD_ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import zg361_workforce_remediation_fact_gen as gen  # noqa: E402


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def top_level_block(source: str, name: str) -> str:
    marker = f"{name} = {{"
    start = source.index(marker)
    depth = 0
    quoted = False
    escaped = False
    for index in range(start + len(name) + 3, len(source)):
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
    raise AssertionError(f"unterminated block: {name}")


class WorkforceRemediationFactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects_path = (
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / "zg361_workforce_remediation_fact_effects.txt"
        )
        cls.events_path = (
            MOD_ROOT / "events" / "zg361_workforce_remediation_fact_events.txt"
        )
        cls.spec_path = (
            MOD_ROOT / "docs" / "zg361_workforce_remediation_fact_spec.md"
        )
        cls.effects = text(cls.effects_path)
        cls.events = text(cls.events_path)
        cls.spec = text(cls.spec_path)

    def test_01_generator_owns_only_new_prefixed_package(self) -> None:
        rendered = gen.outputs()
        self.assertEqual(len(rendered), 12)
        for path, payload in rendered.items():
            with self.subTest(path=path):
                self.assertTrue(path.name.startswith(gen.PREFIX))
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), payload)
        self.assertNotIn("361-workforce-external-producer-ledger", "\n".join(map(str, rendered)))
        self.assertNotIn("gen_361_workforce_endgame_runtime.py", "\n".join(map(str, rendered)))

    def test_02_scripts_and_localizations_keep_required_bom(self) -> None:
        rendered = gen.outputs()
        for path, payload in rendered.items():
            if path.suffix in {".txt", ".yml"}:
                with self.subTest(path=path):
                    self.assertTrue(payload.startswith(gen.BOM))
        self.assertFalse(rendered[self.spec_path].startswith(gen.BOM))

    def test_03_open_joins_the_real_m275_b_tuple_without_caller_values(self) -> None:
        opened = top_level_block(
            self.effects, "zg361_workforce_remediation_fact_open_effect"
        )
        required = (
            "zg361_we_m275_business_object_created = 1",
            "zg361_we_m275_object_subject = this",
            "zg361_we_m275_object_state = 4",
            "zg361_we_m275_object_consumed = 1",
            "zg361_we_m275_consumer_resolve_offer_refusal_hc_hold_275 = 1",
            "zg361_we_m275_write_subject = this",
            "zg361_we_m275_write_owner = var:zg361_we_m275_receipt_owner",
            "zg361_we_m275_write_cycle = var:zg361_we_m275_receipt_cycle",
            "zg361_we_m275_write_case = var:zg361_we_m275_receipt_case",
            "zg361_we_m275_receipt_state = 4",
            "zg361_we_m275_receipt_choice = 2",
            "zg361_we_m275_refusal = 1",
            "zg361_we_m275_not_applicable_hired = 0",
            "zg361_we_m275_hold_pending = 1",
            "zg361_we_m275_reason_remediated = 0",
            "zg361_we_m275_refusal_reason_id > 0",
            "zg361_we_m275_hold_due_cycle > var:zg361_we_m275_write_cycle",
            "zg361_is_celestial_liege_trigger = yes",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, opened)
        self.assertNotIn("$TICKET_OWNER$", opened)
        self.assertNotIn("$TICKET_SUBJECT$", opened)
        self.assertNotIn("$RESULT$", opened)
        self.assertNotIn("root.var:", opened)
        self.assertIn("prev.var:zg361_we_m275_write_cycle", opened)

    def test_04_open_freezes_requirement_but_never_a_completion_receipt(self) -> None:
        opened = top_level_block(
            self.effects, "zg361_workforce_remediation_fact_open_effect"
        )
        self.assertIn(
            "zg361_workforce_remediation_fact_owner value = var:zg361_we_m275_write_owner",
            opened,
        )
        self.assertIn(
            "zg361_workforce_remediation_fact_subject value = this", opened
        )
        for field in (
            "cycle",
            "case",
            "reason_id",
            "requirement_id",
            "requirement_code",
            "requirement_status",
            "requirement_due_cycle",
        ):
            self.assertIn(f"zg361_workforce_remediation_fact_{field} value", opened)
        self.assertIn("trigger_event = { id = zg361workforceremediationfact.1 days = 30 }", opened)
        self.assertIn("AI-owned remediation remains open", opened)
        self.assertIn("zg361_workforce_remediation_fact_pending value = 0", opened)
        self.assertIn("zg361_workforce_remediation_fact_consumed value = 0", opened)
        first_requirement = (
            "save_scope_value_as = { name = "
            "zg361_workforce_remediation_fact_ticket_requirement value = 1 }"
        )
        next_requirement = (
            "save_scope_value_as = { name = "
            "zg361_workforce_remediation_fact_ticket_requirement value = { "
            "value = var:zg361_workforce_remediation_fact_serial_counter add = 1 } }"
        )
        self.assertIn(first_requirement, opened)
        self.assertIn(next_requirement, opened)
        for field in ("serial", "requirement_id", "serial_counter"):
            self.assertIn(
                f"zg361_workforce_remediation_fact_{field} value = 1", opened
            )
            self.assertIn(
                f"zg361_workforce_remediation_fact_{field} value = {{ value = "
                "var:zg361_workforce_remediation_fact_serial_counter add = 1 }",
                opened,
            )
        self.assertNotIn(
            "change_variable = { name = "
            "zg361_workforce_remediation_fact_serial_counter",
            opened,
        )
        self.assertNotIn(
            "zg361_workforce_remediation_fact_requirement_id value = "
            "var:zg361_workforce_remediation_fact_serial",
            opened,
        )
        for token in (
            "zg361_workforce_remediation_fact_status = 2",
            "zg361_workforce_remediation_fact_pending = 0",
            "zg361_workforce_remediation_fact_consumed = 1",
            "zg361_workforce_remediation_fact_status = 3",
            "zg361_workforce_remediation_fact_consumed = 0",
            "trigger_else = { always = yes }",
        ):
            self.assertIn(token, opened)
        self.assertNotIn(
            "set_variable = { name = zg361_we_ad_external_m275_remediation_receipt",
            opened,
        )
        self.assertNotIn(
            "set_variable = { name = zg361_we_ad_external_m275_remediated_reason_id",
            opened,
        )

    def test_05_terminal_receipt_binds_five_tuple_result_reason_and_requirement(self) -> None:
        settle = top_level_block(
            self.effects, "zg361_workforce_remediation_fact_settle_effect"
        )
        self.assertIn("$ACTOR$ = var:zg361_workforce_remediation_fact_owner", settle)
        self.assertIn("$ACTOR$ = {", settle)
        self.assertIn("is_ai = no", settle)
        self.assertNotIn("root.var:", settle)
        self.assertIn(
            "prev.var:zg361_workforce_remediation_fact_cycle", settle
        )
        self.assertIn("NOT = { has_variable = zg361_workforce_remediation_fact_receipt_status }", settle)
        for field in (
            "receipt_id",
            "receipt_hash",
            "receipt_serial",
            "receipt_owner",
            "receipt_subject",
            "receipt_cycle",
            "receipt_case",
            "receipt_result",
            "receipt_reason_id",
            "receipt_requirement_id",
        ):
            self.assertIn(f"zg361_workforce_remediation_fact_{field} value", settle)
        result_at = settle.index("zg361_workforce_remediation_fact_result value")
        receipt_at = settle.index("zg361_workforce_remediation_fact_receipt_status value = 1")
        self.assertLess(result_at, receipt_at)
        self.assertIn(
            "receipt_id value = { value = "
            "var:zg361_workforce_remediation_fact_serial multiply = 10",
            settle,
        )
        self.assertIn(
            "receipt_hash value = { value = "
            "var:zg361_workforce_remediation_fact_serial multiply = 10000000",
            settle,
        )
        self.assertIn(
            "save_temporary_scope_value_as = { name = "
            "zg361_workforce_remediation_fact_expected_terminal_status value = { "
            "value = $RESULT$ add = 1 } }",
            settle,
        )
        self.assertIn(
            "save_temporary_scope_value_as = { name = "
            "zg361_workforce_remediation_fact_expected_receipt_id value = { "
            "value = var:zg361_workforce_remediation_fact_serial multiply = 10 "
            "add = $RESULT$ } }",
            settle,
        )
        self.assertNotIn(
            "value = var:zg361_workforce_remediation_fact_receipt_serial", settle
        )
        self.assertNotIn(
            "value = var:zg361_workforce_remediation_fact_receipt_id", settle
        )
        self.assertNotIn("zg361_workforce_remediation_fact_terminal_cycle", settle)
        self.assertIn(
            "result_cycle value = "
            "var:zg361_workforce_remediation_fact_owner.var:zg361_review_serial",
            settle,
        )
        self.assertIn("runtime_status value = 2", settle)
        self.assertIn("last_red_code value = 27522", settle)
        self.assertIn("zg361_workforce_remediation_fact_pending value = 1", settle)
        self.assertIn("zg361_workforce_remediation_fact_consumed value = 0", settle)

    def test_06_legacy_aliases_are_written_once_and_only_after_completion(self) -> None:
        receipt_write = (
            "set_variable = { name = "
            "zg361_we_ad_external_m275_remediation_receipt value = 1 }"
        )
        reason_write = (
            "set_variable = { name = "
            "zg361_we_ad_external_m275_remediated_reason_id value = "
            "var:zg361_workforce_remediation_fact_reason_id }"
        )
        self.assertEqual(self.effects.count(receipt_write), 1)
        self.assertEqual(self.effects.count(reason_write), 1)
        self.assertNotIn("m275_remediation_receipt value = 0", self.effects)
        self.assertNotIn("m275_remediated_reason_id value = 0", self.effects)
        settle = top_level_block(
            self.effects, "zg361_workforce_remediation_fact_settle_effect"
        )
        alias_branch = (
            "if = {\n"
            "\t\t\tlimit = { "
            "scope:zg361_workforce_remediation_fact_requested_result = 1 }\n"
            f"\t\t\t{receipt_write}\n"
            f"\t\t\t{reason_write}\n"
            "\t\t}\n"
            "\t\telse = {\n"
            "\t\t\tremove_variable = "
            "zg361_we_ad_external_m275_remediation_receipt\n"
            "\t\t\tremove_variable = "
            "zg361_we_ad_external_m275_remediated_reason_id\n"
            "\t\t}"
        )
        self.assertIn(alias_branch, settle)
        receipt = settle.index(receipt_write)
        failure_remove = settle.index(
            "remove_variable = zg361_we_ad_external_m275_remediation_receipt"
        )
        marker = settle.index(
            "set_variable = { name = "
            "zg361_workforce_remediation_fact_receipt_status value = 1 }"
        )
        payload_hash = settle.index("zg361_workforce_remediation_fact_receipt_hash value")
        self.assertLess(payload_hash, receipt)
        self.assertLess(receipt, marker)
        self.assertLess(failure_remove, marker)
        self.assertLess(
            marker,
            settle.index("zg361_workforce_remediation_fact_runtime_status value = 1"),
        )

    def test_07_consume_ack_requires_the_real_hc_release_postcondition(self) -> None:
        consume = top_level_block(
            self.effects, "zg361_workforce_remediation_fact_consume_effect"
        )
        first_mutation = consume.index(
            "set_variable = { name = "
            "zg361_workforce_remediation_fact_pending value = 0 }"
        )
        exact_precheck = consume[:first_mutation]
        for token in (
            "zg361_workforce_remediation_fact_pending = 1",
            "zg361_workforce_remediation_fact_consumed = 0",
            "zg361_workforce_remediation_fact_pending = 0",
            "zg361_workforce_remediation_fact_consumed = 1",
            "zg361_workforce_remediation_fact_receipt_owner = var:zg361_workforce_remediation_fact_owner",
            "zg361_workforce_remediation_fact_receipt_subject = this",
            "zg361_workforce_remediation_fact_receipt_cycle = var:zg361_workforce_remediation_fact_cycle",
            "zg361_workforce_remediation_fact_receipt_case = var:zg361_workforce_remediation_fact_case",
            "zg361_workforce_remediation_fact_receipt_result = 1",
            "zg361_workforce_remediation_fact_receipt_reason_id = var:zg361_workforce_remediation_fact_reason_id",
            "zg361_workforce_remediation_fact_receipt_requirement_id = var:zg361_workforce_remediation_fact_requirement_id",
            "zg361_workforce_remediation_fact_receipt_serial = var:zg361_workforce_remediation_fact_serial",
            "zg361_workforce_remediation_fact_receipt_id = scope:zg361_workforce_remediation_fact_consume_expected_receipt_id",
            "zg361_workforce_remediation_fact_receipt_hash = scope:zg361_workforce_remediation_fact_consume_expected_receipt_hash",
            "zg361_we_m275_object_owner = var:zg361_workforce_remediation_fact_owner",
            "zg361_we_m275_object_subject = this",
            "zg361_we_m275_object_cycle = var:zg361_workforce_remediation_fact_cycle",
            "zg361_we_m275_object_case = var:zg361_workforce_remediation_fact_case",
            "zg361_we_m275_hold_pending = 0",
            "zg361_we_m275_reason_remediated = 1",
            "zg361_we_m275_hold_released = 1",
            "zg361_we_m266_hc_reservation_active = 0",
            "zg361_we_ad_hc_flight_pending = 0",
            "zg361_we_ad_external_m275_remediation_receipt = 1",
            "zg361_we_ad_external_m275_remediated_reason_id = var:zg361_workforce_remediation_fact_receipt_reason_id",
        ):
            with self.subTest(token=token):
                self.assertIn(token, exact_precheck)
        self.assertIn("zg361_workforce_remediation_fact_pending value = 0", consume)
        self.assertIn("zg361_workforce_remediation_fact_consumed value = 1", consume)
        self.assertIn("runtime_status value = 2", consume)
        self.assertIn("last_red_code value = 27523", consume)
        self.assertNotIn("else_if = {", consume)
        self.assertNotIn(
            "set_variable = { name = zg361_we_ad_external_m275_remediation_receipt",
            consume,
        )

    def test_08_visible_event_is_exact_player_owner_and_has_both_real_outcomes(self) -> None:
        event = top_level_block(self.events, "zg361workforceremediationfact.1")
        self.assertIn("is_ai = no", event)
        self.assertIn("this = scope:zg361_workforce_remediation_fact_ticket_owner", event)
        for token in ("owner", "subject", "cycle", "case", "reason", "requirement"):
            self.assertIn(
                f"scope:zg361_workforce_remediation_fact_ticket_{token}", event
            )
        self.assertEqual(event.count("zg361_workforce_remediation_fact_settle_effect"), 2)
        self.assertIn("ACTOR = root RESULT = 1", event)
        self.assertIn("ACTOR = root RESULT = 2", event)
        self.assertNotIn("ai_chance", event)
        self.assertIn(
            "zg361_workforce_remediation_fact_serial = "
            "scope:zg361_workforce_remediation_fact_ticket_requirement",
            event,
        )

    def test_09_settle_prechecks_entire_unreleased_hc_lineage_before_writes(self) -> None:
        settle = top_level_block(
            self.effects, "zg361_workforce_remediation_fact_settle_effect"
        )
        first_write = settle.index(
            "set_variable = { name = zg361_workforce_remediation_fact_result value"
        )
        precheck = settle[:first_write]
        for token in (
            "zg361_workforce_remediation_fact_requirement_id = var:zg361_workforce_remediation_fact_serial",
            "zg361_workforce_remediation_fact_serial_counter = var:zg361_workforce_remediation_fact_serial",
            "zg361_we_m275_object_owner = var:zg361_workforce_remediation_fact_owner",
            "zg361_we_m275_object_subject = this",
            "zg361_we_m275_object_cycle = var:zg361_workforce_remediation_fact_cycle",
            "zg361_we_m275_object_case = var:zg361_workforce_remediation_fact_case",
            "zg361_we_m275_write_owner = var:zg361_workforce_remediation_fact_owner",
            "zg361_we_m275_write_subject = this",
            "zg361_we_m275_write_cycle = var:zg361_workforce_remediation_fact_cycle",
            "zg361_we_m275_write_case = var:zg361_workforce_remediation_fact_case",
            "zg361_we_m275_receipt_choice = 2",
            "zg361_we_m275_hold_pending = 1",
            "zg361_we_m275_reason_remediated = 0",
            "zg361_we_m266_hc_reservation_active = 1",
            "zg361_we_m266_hc_receipt = var:zg361_we_m275_hc_lineage_receipt",
            "zg361_we_m275_hc_lineage_receipt = var:zg361_workforce_remediation_fact_case",
            "zg361_ch_hc_reserved >= 1",
            "zg361_we_ad_hc_flight_pending = 1",
            "zg361_we_ad_hc_flight_subject = prev",
            "zg361_we_ad_hc_flight_cycle = prev.var:zg361_workforce_remediation_fact_cycle",
            "zg361_we_ad_hc_flight_case = prev.var:zg361_workforce_remediation_fact_case",
            "NOT = { has_variable = zg361_workforce_remediation_fact_receipt_status }",
        ):
            with self.subTest(token=token):
                self.assertIn(token, precheck)

    def test_10_settle_idempotent_ack_requires_the_full_committed_receipt(self) -> None:
        settle = top_level_block(
            self.effects, "zg361_workforce_remediation_fact_settle_effect"
        )
        replay = settle[settle.index("\n\telse_if = {") :]
        for token in (
            "zg361_workforce_remediation_fact_receipt_status = 1",
            "zg361_workforce_remediation_fact_status = scope:zg361_workforce_remediation_fact_expected_terminal_status",
            "zg361_workforce_remediation_fact_requirement_status = scope:zg361_workforce_remediation_fact_expected_terminal_status",
            "$ACTOR$ = var:zg361_workforce_remediation_fact_owner",
            "zg361_workforce_remediation_fact_result = scope:zg361_workforce_remediation_fact_requested_result",
            "zg361_workforce_remediation_fact_result_cycle >= var:zg361_workforce_remediation_fact_cycle",
            "zg361_workforce_remediation_fact_result_case = var:zg361_workforce_remediation_fact_case",
            "zg361_workforce_remediation_fact_receipt_owner = $ACTOR$",
            "zg361_workforce_remediation_fact_receipt_subject = this",
            "zg361_workforce_remediation_fact_receipt_cycle = var:zg361_workforce_remediation_fact_cycle",
            "zg361_workforce_remediation_fact_receipt_case = var:zg361_workforce_remediation_fact_case",
            "zg361_workforce_remediation_fact_receipt_result = scope:zg361_workforce_remediation_fact_requested_result",
            "zg361_workforce_remediation_fact_receipt_reason_id = var:zg361_workforce_remediation_fact_reason_id",
            "zg361_workforce_remediation_fact_receipt_requirement_id = var:zg361_workforce_remediation_fact_requirement_id",
            "zg361_workforce_remediation_fact_receipt_serial = var:zg361_workforce_remediation_fact_serial",
            "zg361_workforce_remediation_fact_receipt_id = scope:zg361_workforce_remediation_fact_expected_receipt_id",
            "zg361_workforce_remediation_fact_receipt_hash = scope:zg361_workforce_remediation_fact_expected_receipt_hash",
            "runtime_status value = 2",
        ):
            with self.subTest(token=token):
                self.assertIn(token, replay)

    def test_11_trigger_comparisons_never_use_illegal_arithmetic_rhs(self) -> None:
        illegal = re.findall(
            r"(?m)^\s*var:[A-Za-z0-9_.:]+\s*(?:=|>=|<=|>|<)\s*\{\s*value\s*=",
            self.effects,
        )
        self.assertEqual([], illegal)
        self.assertNotIn(
            "var:zg361_workforce_remediation_fact_receipt_id = { value =",
            self.effects,
        )
        self.assertNotIn(
            "var:zg361_workforce_remediation_fact_receipt_hash = { value =",
            self.effects,
        )

    def test_12_nine_language_structure_has_only_zh_and_en_authored(self) -> None:
        keys_by_language: dict[str, set[str]] = {}
        bodies: dict[str, str] = {}
        for language in gen.LANGUAGES:
            path = (
                MOD_ROOT
                / "localization"
                / language
                / f"{gen.PREFIX}_l_{language}.yml"
            )
            body = text(path)
            bodies[language] = body
            keys_by_language[language] = {
                line.strip().split(":", 1)[0]
                for line in body.splitlines()[1:]
                if line.strip()
            }
        baseline = keys_by_language["english"]
        self.assertTrue(baseline)
        self.assertTrue(all(keys == baseline for keys in keys_by_language.values()))
        self.assertNotEqual(bodies["simp_chinese"], bodies["english"])
        english_values = bodies["english"].splitlines()[1:]
        for language in set(gen.LANGUAGES) - {"english", "simp_chinese"}:
            self.assertEqual(bodies[language].splitlines()[1:], english_values)

    def test_13_spec_is_honest_about_static_readiness_and_wired_core_abi(self) -> None:
        self.assertIn("ck3-script-static-ready-not-live", self.spec)
        self.assertIn("zg361_workforce_remediation_fact_open_effect = yes", self.spec)
        self.assertIn("zg361_workforce_remediation_fact_consume_effect = yes", self.spec)
        self.assertIn("#275 route B", self.spec)
        self.assertIn("已经提交后的下一事件/帧", self.spec)
        self.assertIn("最终常量 commit marker", self.spec)
        self.assertIn("exact HC release postcondition", self.spec)
        self.assertIn("refusal_reason_id", self.spec)
        self.assertIn("本包自身不拥有", self.spec)
        self.assertIn("zg361we.5276", self.spec)
        self.assertIn("zg361we.5277", self.spec)
        self.assertIn("core-wired static-ready", self.spec)
        self.assertIn("不得在实机前", self.spec)
        self.assertNotIn("production-live primitive", self.spec)
        self.assertNotIn("fixture-live", self.spec)


if __name__ == "__main__":
    unittest.main()
