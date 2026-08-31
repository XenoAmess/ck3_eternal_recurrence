#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for the isolated Workforce normal-exit fact producer."""

from __future__ import annotations

from pathlib import Path
import re
import unittest

import gen_zg361_workforce_normal_exit_fact as generator
import gen_zg361_workforce_rehire_fact as rehire_generator


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = MOD_ROOT / "common/scripted_effects/zg361_workforce_normal_exit_fact_effects.txt"
EVENTS_PATH = MOD_ROOT / "events/zg361_workforce_normal_exit_fact_events.txt"
SPEC_PATH = MOD_ROOT / "docs/zg361-workforce-normal-exit-fact-ck3-runtime-spec.md"


def block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if match is None:
        raise AssertionError(f"missing block: {name}")
    start = match.start()
    brace = text.find("{", start)
    depth = 0
    quoted = False
    escaped = False
    for index in range(brace, len(text)):
        char = text[index]
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
                return text[start : index + 1]
    raise AssertionError(f"unclosed block: {name}")


def brace_balance(text: str) -> int:
    total = 0
    quoted = False
    escaped = False
    commented = False
    for char in text:
        if commented:
            if char == "\n":
                commented = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            commented = True
        elif char == '"':
            quoted = True
        elif char == "{":
            total += 1
        elif char == "}":
            total -= 1
            if total < 0:
                return total
    return total


class WorkforceNormalExitFactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = EFFECTS_PATH.read_text(encoding="utf-8-sig")
        cls.events = EVENTS_PATH.read_text(encoding="utf-8-sig")
        cls.spec = SPEC_PATH.read_text(encoding="utf-8-sig")

    def test_01_contract_constants_are_frozen(self) -> None:
        generator.validate_contract()
        self.assertEqual(generator.SOURCE_KIND_M075, 75)
        self.assertEqual(generator.EXIT_CLASS_NORMAL, 1)
        self.assertEqual(generator.EXIT_REASON_VOLUNTARY_PACKAGE, 1)
        self.assertNotEqual(generator.SOURCE_KIND_M075, 277)
        self.assertEqual(generator.READINESS, "ck3-script-static-ready-not-live")

    def test_02_generated_outputs_are_current_bom_and_isolated(self) -> None:
        rendered = generator.outputs()
        self.assertEqual(len(rendered), 11)
        for path, payload in rendered.items():
            with self.subTest(path=path.name):
                self.assertTrue(path.name.startswith(generator.PREFIX))
                self.assertTrue(payload.startswith(generator.BOM))
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), payload)
        self.assertFalse(any("court_positions" in path.parts for path in rendered))

    def test_03_ck3_blocks_balance_and_effect_names_are_unique(self) -> None:
        self.assertEqual(brace_balance(self.effects), 0)
        self.assertEqual(brace_balance(self.events), 0)
        names = re.findall(r"(?m)^(zg361_workforce_normal_exit_fact_[a-z0-9_]+) = \{", self.effects)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            set(names),
            {
                "zg361_workforce_normal_exit_fact_clear_pending_effect",
                "zg361_workforce_normal_exit_fact_begin_from_m075_offer_effect",
                "zg361_workforce_normal_exit_fact_dispatch_native_revoke_effect",
                "zg361_workforce_normal_exit_fact_audit_native_then_accept_m075_effect",
                "zg361_workforce_normal_exit_fact_migrate_hc_partition_effect",
                "zg361_workforce_normal_exit_fact_audit_hc_then_finalize_receipt_effect",
            },
        )

    def test_04_public_entry_accepts_no_caller_truth(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        self.assertNotRegex(begin, r"\$[A-Z0-9_]+\$")
        self.assertIn("this", begin)
        self.assertNotIn("root.", begin.lower())

    def test_05_begin_requires_exact_live_route_a_m075_offer(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        for field in generator.M075_PRE_FIELDS:
            self.assertIn(f"has_variable = {generator.M075_PREFIX}_{field}", begin)
        for token in (
            "m075_state = 1",
            "m075_route = 1",
            "m075_offer_gold = 50",
            "m075_object_route = 1",
            "m075_object_active = 1",
            "m075_object_consumed = 0",
            "b2_case_owner = var:zg361_b2_m075_owner",
            "b2_case_subject = this",
            "b2_case_cycle = var:zg361_b2_m075_cycle",
            "b2_case_serial = var:zg361_b2_m075_case",
            "treasury >= 50",
        ):
            self.assertIn(token, begin)

    def test_06_coerced_refused_or_expired_exit_is_rejected(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        for token in (
            "m075_coercion_evidence = 0",
            "m075_procedural_redundancy = 0",
            "m075_reclassification_due = 0",
            "m075_refused_without_transfer = 0",
            "m075_expired = 0",
        ):
            self.assertIn(token, begin)
        self.assertNotIn("m075_route = 2", begin)

    def test_07_old_325_is_read_from_exact_settled_result_case(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        for field in generator.RESULT_FIELDS:
            self.assertIn(f"has_variable = zg361_result_{field}", begin)
        for token in (
            "result_case_owner = var:zg361_b2_m075_owner",
            "result_cycle_serial = var:zg361_b2_m075_cycle",
            "result_case_serial = var:zg361_b2_m075_case",
            "result_case_state = 3",
            "result_case_state = 5",
            "result_settlement_posted_serial = var:zg361_result_case_serial",
            "result_grade = 1",
            "pending_result_hash",
        ):
            self.assertIn(token, begin)

    def test_08_prior_pip_is_conditional_history_not_eligibility(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        finalize = block(self.effects, f"{generator.PREFIX}_audit_hc_then_finalize_receipt_effect")
        for token in (
            "pip_state = 0",
            "pending_pip_present value = 0",
            "pending_pip_present value = 1",
            "pip_state = 3",
            "pip_outcome_code = 1",
            "pip_outcome_result_grade = 2",
            "pip_outcome_result_grade = 3",
            "receipt_prior_pip_present value = var:zg361_workforce_normal_exit_fact_pending_pip_present",
        ):
            self.assertIn(token, begin + finalize)
        self.assertNotIn("pip_state = 4", begin)
        self.assertNotIn("pip_outcome_code = 2", begin)

    def test_09_failed_pip_277_receipt_is_never_positive_source(self) -> None:
        lowered = self.effects.lower()
        self.assertNotIn("request_closed_pip_exit_effect", lowered)
        self.assertNotIn("submit_m277", lowered)
        self.assertNotIn("receipt_reason_kind", lowered)
        self.assertIn("zg361_workforce_exit_fact_receipt_active = 0", lowered)

    def test_10_existing_long_lived_native_carrier_is_reused(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        for token in (
            generator.EXIT_SLOT_POSITION,
            "workforce_exit_fact_slot_active = 1",
            "workforce_exit_fact_slot_owner = var:zg361_b2_m075_owner",
            f"workforce_exit_fact_slot_position_type_id = {generator.M274_POSITION_TYPE_ID}",
            f"workforce_exit_fact_slot_carrier_type_id = {generator.CAREER_SLOT_TYPE_ID}",
            "has_court_position",
            "is_court_position_employer",
        ):
            self.assertIn(token, begin)

    def test_11_native_revoke_is_delayed_after_committed_intent(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        dispatch = block(self.effects, f"{generator.PREFIX}_dispatch_native_revoke_effect")
        self.assertNotIn("revoke_court_position", begin)
        self.assertIn("request_authorized value = 1", begin)
        self.assertIn(f"id = {generator.NAMESPACE}.{generator.DISPATCH_EVENT_ID} days = 1", begin)
        self.assertIn("request_dispatched value = 1", dispatch)
        self.assertIn(f"revoke_court_position = {generator.EXIT_SLOT_POSITION}", dispatch)

    def test_12_callback_and_no_longer_holder_are_both_required(self) -> None:
        audit = block(self.effects, f"{generator.PREFIX}_audit_native_then_accept_m075_effect")
        for token in (
            "workforce_exit_fact_slot_active = 0",
            "workforce_exit_fact_native_last_end_reason = 1",
            "workforce_exit_fact_native_last_end_owner = var:zg361_workforce_normal_exit_fact_pending_owner",
            "workforce_exit_fact_native_revoked_seen = 1",
            "normal_exit_fact_native_revoke_callback_seen = 1",
            "normal_exit_fact_native_revoke_callback_owner = var:zg361_workforce_normal_exit_fact_pending_owner",
            "normal_exit_fact_native_revoke_callback_subject = this",
            f"NOT = {{ has_court_position = {generator.EXIT_SLOT_POSITION} }}",
            "native_callback_verified value = 1",
            "native_end_reason value = 1",
        ):
            self.assertIn(token, audit)

    def test_13_real_m075_accept_runs_only_after_callback_audit(self) -> None:
        begin = block(self.effects, f"{generator.PREFIX}_begin_from_m075_offer_effect")
        dispatch = block(self.effects, f"{generator.PREFIX}_dispatch_native_revoke_effect")
        audit = block(self.effects, f"{generator.PREFIX}_audit_native_then_accept_m075_effect")
        self.assertNotIn("m075_accept_exit_offer_effect", begin + dispatch)
        self.assertIn("zg361_b2_m075_accept_exit_offer_effect = yes", audit)
        self.assertIn("b2_case_owner = var:zg361_workforce_normal_exit_fact_pending_owner", audit)
        self.assertIn("b2_case_cycle = var:zg361_workforce_normal_exit_fact_pending_cycle", audit)
        self.assertIn("b2_case_serial = var:zg361_workforce_normal_exit_fact_pending_case", audit)
        self.assertLess(audit.index("native_callback_verified value = 1"), audit.index("m075_accept_exit_offer_effect = yes"))

    def test_14_m075_poststate_is_read_only_on_later_frame(self) -> None:
        audit = block(self.effects, f"{generator.PREFIX}_audit_native_then_accept_m075_effect")
        migrate = block(self.effects, f"{generator.PREFIX}_migrate_hc_partition_effect")
        self.assertIn(f"id = {generator.NAMESPACE}.{generator.FINALIZE_EVENT_ID} days = 1", audit)
        for token in (
            "m075_state = 3",
            "m075_treasury_paid = 50",
            "m075_personal_received = 50",
            "m075_neutral_record = 1",
            "m075_actual_exit = 1",
            "m075_hc_released = 1",
            "m075_object_active = 0",
            "m075_object_consumed = 1",
        ):
            self.assertIn(token, migrate)
            self.assertNotIn(token, audit)

    def test_15_hc_claim_is_sealed_only_after_real_partition_settlement(self) -> None:
        migrate = block(self.effects, f"{generator.PREFIX}_migrate_hc_partition_effect")
        finalize = block(self.effects, f"{generator.PREFIX}_audit_hc_then_finalize_receipt_effect")
        self.assertIn("change_variable = { name = zg361_ch_hc_occupied add = -1 }", migrate)
        self.assertIn("change_variable = { name = zg361_ch_hc_frozen add = 1 }", migrate)
        self.assertIn("we_formal_hc_active value = 0", migrate)
        self.assertIn(f"id = {generator.NAMESPACE}.{generator.HC_AUDIT_EVENT_ID} days = 1", migrate)
        self.assertNotIn("receipt_active value = 1", migrate)
        self.assertIn("receipt_source_hc_release_claimed value = 1", finalize)
        self.assertIn("receipt_hc_ledger_settled value = 1", finalize)
        self.assertIn("receipt_hc_destination_frozen value = 1", finalize)
        self.assertIn("receipt_hc_conservation_verified value = 1", finalize)
        self.assertIn("receipt_formal_hc_active_before value = 1", finalize)
        self.assertIn("receipt_formal_hc_active_after value = 0", finalize)
        self.assertIn("ch_hc_occupied = { value = var:zg361_workforce_normal_exit_fact_pending_hc_occupied_before subtract = 1 }", finalize)
        self.assertIn("ch_hc_frozen = { value = var:zg361_workforce_normal_exit_fact_pending_hc_frozen_before add = 1 }", finalize)
        for field in ("authorized", "available", "reserved", "occupied", "frozen", "reclaimed"):
            self.assertIn(f"receipt_hc_{field}_before", finalize)
            self.assertIn(f"receipt_hc_{field}_after", finalize)

    def test_16_receipt_freezes_normal_reason_and_source(self) -> None:
        finalize = block(self.effects, f"{generator.PREFIX}_audit_hc_then_finalize_receipt_effect")
        for token in (
            "receipt_consumed_operation value = 75",
            "receipt_exit_source_kind value = 75",
            "receipt_exit_source_state value = 3",
            "receipt_exit_class value = 1",
            "receipt_exit_reason_code value = 1",
            "receipt_normal_exit_confirmed value = 1",
            "receipt_forced value = 0",
            "receipt_neutral_record value = 1",
            "receipt_actual_exit value = 1",
            "receipt_native_end_reason value = 1",
            "receipt_native_callback_seen value = 1",
        ):
            self.assertIn(token, finalize)

    def test_17_receipt_freezes_result_slot_cost_and_optional_pip(self) -> None:
        finalize = block(self.effects, f"{generator.PREFIX}_audit_hc_then_finalize_receipt_effect")
        for token in (
            "receipt_prior_result_grade value = 1",
            "receipt_prior_result_hash value = var:zg361_workforce_normal_exit_fact_pending_result_hash",
            "receipt_former_slot_id value = var:zg361_workforce_normal_exit_fact_pending_slot_id",
            "receipt_appointment_receipt_id value = var:zg361_workforce_normal_exit_fact_pending_appointment_receipt_id",
            "receipt_displaced_cost_amount value = var:zg361_workforce_normal_exit_fact_pending_cost_amount",
            "receipt_prior_pip_case_id value = var:zg361_workforce_normal_exit_fact_pending_pip_case_id",
        ):
            self.assertIn(token, finalize)

    def test_18_ids_hashes_and_reason_are_producer_derived(self) -> None:
        finalize = block(self.effects, f"{generator.PREFIX}_audit_hc_then_finalize_receipt_effect")
        self.assertIn("next_receipt_serial", finalize)
        self.assertIn("receipt_id value = {", finalize)
        self.assertIn("receipt_hash value = {", finalize)
        self.assertNotRegex(self.effects, r"\$[^$]*(?:ID|HASH|REASON|SUCCESS|CALLBACK)[^$]*\$")

    def test_19_clean_misconduct_history_does_not_invent_references(self) -> None:
        finalize = block(self.effects, f"{generator.PREFIX}_audit_hc_then_finalize_receipt_effect")
        self.assertIn("receipt_misconduct_present value = 0", finalize)
        self.assertNotIn("receipt_misconduct_case_id", self.effects)
        self.assertNotIn("receipt_misconduct_case_hash", self.effects)
        self.assertNotIn("receipt_misconduct_evidence_id", self.effects)
        self.assertNotIn("receipt_misconduct_evidence_hash", self.effects)

    def test_20_receipt_history_is_never_removed(self) -> None:
        for field in generator.RECEIPT_ALWAYS_FIELDS:
            self.assertNotIn(f"remove_variable = {generator.PREFIX}_receipt_{field}", self.effects)
        clear = block(self.effects, f"{generator.PREFIX}_clear_pending_effect")
        self.assertNotIn(f"remove_variable = {generator.PREFIX}_receipt_", clear)

    def test_21_package_does_not_duplicate_b2_payment_or_title_exit(self) -> None:
        for forbidden in (
            "remove_treasury",
            "add_gold",
            "force_step_down_landed_titles",
            "create_character",
            "appoint_court_position",
        ):
            self.assertNotIn(forbidden, self.effects)
        self.assertEqual(self.effects.count("zg361_b2_m075_accept_exit_offer_effect = yes"), 1)

    def test_22_hidden_frames_and_player_only_notice_are_separate(self) -> None:
        for event_id in (
            generator.DISPATCH_EVENT_ID,
            generator.AUDIT_EVENT_ID,
            generator.FINALIZE_EVENT_ID,
            generator.HC_AUDIT_EVENT_ID,
            generator.CAPTURE_EVENT_ID,
        ):
            event = block(self.events, f"{generator.NAMESPACE}.{event_id}")
            self.assertIn("hidden = yes", event)
        notice = block(self.events, f"{generator.NAMESPACE}.{generator.NOTICE_EVENT_ID}")
        self.assertIn("is_ai = no", notice)
        self.assertNotIn("hidden = yes", notice)

    def test_22a_sealed_exit_is_captured_by_rehire_on_d_plus_one(self) -> None:
        finalize = block(self.effects, f"{generator.PREFIX}_audit_hc_then_finalize_receipt_effect")
        capture = block(self.events, f"{generator.NAMESPACE}.{generator.CAPTURE_EVENT_ID}")
        self.assertIn(
            f"id = {generator.NAMESPACE}.{generator.CAPTURE_EVENT_ID} days = 1",
            finalize,
        )
        self.assertIn("receipt_sealed = 1", capture)
        self.assertIn("receipt_consumed = 1", capture)
        self.assertIn(
            f"{generator.REHIRE_CAPTURE_EXIT_EFFECT} = yes",
            capture,
        )

    def test_23_zh_en_and_seven_placeholders_are_loadable(self) -> None:
        for language in generator.LANGUAGES:
            path = MOD_ROOT / "localization" / language / f"{generator.PREFIX}_l_{language}.yml"
            text = path.read_text(encoding="utf-8-sig")
            self.assertTrue(text.startswith(f"l_{language}:"))
            for suffix in ("t", "desc", "a"):
                self.assertIn(f"{generator.NAMESPACE}.{generator.NOTICE_EVENT_ID}.{suffix}:0", text)
        zh = (MOD_ROOT / "localization/simp_chinese" / f"{generator.PREFIX}_l_simp_chinese.yml").read_text(encoding="utf-8-sig")
        en = (MOD_ROOT / "localization/english" / f"{generator.PREFIX}_l_english.yml").read_text(encoding="utf-8-sig")
        self.assertIn("正常离职", zh)
        self.assertIn("Normal-exit", en)

    def test_24_rehire_contract_accepts_the_same_always_and_conditional_abi(self) -> None:
        normal_always = {f"receipt_{field}" for field in generator.RECEIPT_ALWAYS_FIELDS}
        normal_pip = {f"receipt_prior_pip_{field}" for field in generator.PIP_REFERENCE_FIELDS}
        self.assertTrue(set(rehire_generator.NORMAL_EXIT_REQUIRED_FIELDS) <= normal_always)
        self.assertEqual(set(rehire_generator.NORMAL_EXIT_PIP_REFERENCE_FIELDS), normal_pip)
        self.assertIn("receipt_misconduct_present", normal_always)

    def test_25_spec_is_static_honest_and_names_exact_blockers(self) -> None:
        for token in (
            generator.READINESS,
            "B2 #075",
            "route A",
            "core-wired",
            "failed-PIP #277",
            "native revoke callback",
            "unexpected_native_end_seen=1",
            "capture_exit_effect",
            "force_step_down_landed_titles",
            "HC ledger",
            "occupied -> frozen",
            "receipt_hc_ledger_settled = 1",
            "audit_hc_then_finalize_receipt_effect",
            "MCP-first paused snapshot",
            "not live",
        ):
            self.assertIn(token, self.spec)
        self.assertNotIn("hc_ledger_settled=0", self.spec)


if __name__ == "__main__":
    unittest.main()
