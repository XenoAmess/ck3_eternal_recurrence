#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for the isolated Workforce #276 rehire-history package.

These tests prove deterministic generation and fail-closed CK3 source
contracts.  They do not claim parser, loader, paused-snapshot or live evidence.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

import gen_zg361_workforce_rehire_fact as generator


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = MOD_ROOT / "common/scripted_effects/zg361_workforce_rehire_fact_effects.txt"
EVENTS_PATH = MOD_ROOT / "events/zg361_workforce_rehire_fact_events.txt"
SPEC_PATH = MOD_ROOT / "docs/zg361-workforce-rehire-fact-ck3-runtime-spec.md"


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


class WorkforceRehireFactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = EFFECTS_PATH.read_text(encoding="utf-8-sig")
        cls.events = EVENTS_PATH.read_text(encoding="utf-8-sig")
        cls.spec = SPEC_PATH.read_text(encoding="utf-8-sig")

    def test_01_exactly_seven_frozen_legacy_aliases(self) -> None:
        expected = {
            "rehire_id",
            "rehire_historical_case_id",
            "rehire_historical_case_hash",
            "rehire_historical_cycle",
            "rehire_growth_evidence_id",
            "rehire_growth_evidence_hash",
            "rehire_future_cohort_cycle",
        }
        self.assertEqual(set(generator.LEGACY_ALIAS_TO_FACT), expected)
        self.assertEqual(len(generator.LEGACY_ALIAS_TO_FACT), 7)
        generator.validate_contract()

    def test_02_outputs_are_current_bom_and_isolated(self) -> None:
        rendered = generator.outputs()
        self.assertEqual(len(rendered), 11)
        for path, payload in rendered.items():
            with self.subTest(path=path.name):
                self.assertTrue(path.name.startswith(generator.PREFIX))
                self.assertTrue(payload.startswith(generator.BOM))
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), payload)

    def test_03_ck3_files_are_balanced_and_top_level_unique(self) -> None:
        self.assertEqual(brace_balance(self.effects), 0)
        self.assertEqual(brace_balance(self.events), 0)
        effects = re.findall(r"(?m)^(zg361_workforce_rehire_fact_[a-z0-9_]+) = \{", self.effects)
        self.assertEqual(len(effects), len(set(effects)))
        self.assertEqual(
            set(effects),
            {
                "zg361_workforce_rehire_fact_capture_exit_effect",
                "zg361_workforce_rehire_fact_capture_growth_effect",
                "zg361_workforce_rehire_fact_clear_legacy_envelope_effect",
                "zg361_workforce_rehire_fact_prepare_m276_effect",
                "zg361_workforce_rehire_fact_finalize_m276_effect",
            },
        )
        self.assertEqual(
            re.findall(r"(?m)^(zg361wrf\.[0-9]+) = \{", self.events),
            ["zg361wrf.1"],
        )

    def test_04_all_public_seams_are_parameterless_subject_scope(self) -> None:
        for name in (
            "zg361_workforce_rehire_fact_capture_exit_effect",
            "zg361_workforce_rehire_fact_capture_growth_effect",
            "zg361_workforce_rehire_fact_prepare_m276_effect",
            "zg361_workforce_rehire_fact_finalize_m276_effect",
        ):
            seam = block(self.effects, name)
            self.assertNotRegex(seam, r"\$[A-Z0-9_]+\$")
            self.assertIn("this", seam)
        self.assertNotIn("root.", self.effects.lower())

    def test_05_exit_requires_future_full_canonical_normal_receipt(self) -> None:
        capture = block(self.effects, "zg361_workforce_rehire_fact_capture_exit_effect")
        for field in generator.NORMAL_EXIT_REQUIRED_FIELDS:
            self.assertIn(f"has_variable = {generator.NORMAL_EXIT_PREFIX}_{field}", capture)
        for token in (
            "receipt_active = 1",
            "receipt_sealed = 1",
            "receipt_published = 1",
            "receipt_consumed = 1",
            "receipt_subject = this",
            "receipt_cycle > 0",
            "receipt_case > 0",
            "receipt_exit_class = 1",
            "receipt_normal_exit_confirmed = 1",
            "receipt_forced = 0",
            "receipt_exit_year > 0",
            "receipt_exit_source_kind = 75",
            "receipt_exit_source_state = 3",
            "receipt_exit_reason_code = 1",
            "receipt_neutral_record = 1",
            "receipt_actual_exit = 1",
            "receipt_hc_ledger_settled = 1",
            "receipt_hc_destination_frozen = 1",
            "receipt_hc_conservation_verified = 1",
            "receipt_formal_hc_active_before = 1",
            "receipt_formal_hc_active_after = 0",
            "receipt_native_end_reason = 1",
            "receipt_native_callback_seen = 1",
        ):
            self.assertIn(token, capture)
        for field in ("authorized", "available", "reserved", "occupied", "frozen", "reclaimed"):
            self.assertIn(f"receipt_hc_{field}_before", capture)
            self.assertIn(f"receipt_hc_{field}_after", capture)
            self.assertIn(
                f"exit_hc_{field}_before value = var:zg361_workforce_normal_exit_fact_receipt_hc_{field}_before",
                capture,
            )
            self.assertIn(
                f"exit_hc_{field}_after value = var:zg361_workforce_normal_exit_fact_receipt_hc_{field}_after",
                capture,
            )

    def test_06_normal_exit_requires_old_325_and_conditional_pip_history(self) -> None:
        capture = block(self.effects, "zg361_workforce_rehire_fact_capture_exit_effect")
        for token in (
            "receipt_prior_result_owner = var:zg361_workforce_normal_exit_fact_receipt_owner",
            "receipt_prior_result_subject = this",
            "receipt_prior_result_cycle <= var:zg361_workforce_normal_exit_fact_receipt_cycle",
            "receipt_prior_result_settlement_receipt = var:zg361_workforce_normal_exit_fact_receipt_prior_result_case",
            "receipt_prior_result_grade = 1",
            "receipt_prior_result_hash > 0",
            "receipt_prior_pip_present = 0",
            "receipt_prior_pip_present = 1",
            "receipt_prior_pip_state = 3",
            "receipt_prior_pip_outcome_code = 1",
            "receipt_prior_pip_result_grade = 2",
            "receipt_prior_pip_result_grade = 3",
        ):
            self.assertIn(token, capture)
        for field in generator.NORMAL_EXIT_PIP_REFERENCE_FIELDS:
            self.assertIn(f"has_variable = {generator.NORMAL_EXIT_PREFIX}_{field}", capture)
            self.assertIn(f"NOT = {{ has_variable = {generator.NORMAL_EXIT_PREFIX}_{field} }}", capture)
        self.assertNotIn("m277_", capture)
        self.assertNotIn("zg361_workforce_exit_fact", capture)

    def test_07_failed_pip_exit_is_never_accepted_as_normal(self) -> None:
        capture = block(self.effects, "zg361_workforce_rehire_fact_capture_exit_effect")
        self.assertIn("receipt_exit_class = 1", capture)
        self.assertIn("receipt_normal_exit_confirmed = 1", capture)
        self.assertIn("receipt_forced = 0", capture)
        self.assertIn(
            "misconduct_present value = var:zg361_workforce_normal_exit_fact_receipt_misconduct_present",
            capture,
        )
        for field in generator.NORMAL_EXIT_MISCONDUCT_REFERENCE_FIELDS:
            self.assertIn(f"has_variable = {generator.NORMAL_EXIT_PREFIX}_{field}", capture)
            self.assertIn(f"NOT = {{ has_variable = {generator.NORMAL_EXIT_PREFIX}_{field} }}", capture)
            self.assertIn(f"var:{generator.NORMAL_EXIT_PREFIX}_{field} > 0", capture)
        for token in (
            "receipt_misconduct_present = 0",
            "receipt_misconduct_present = 1",
            "misconduct_case_id value = var:zg361_workforce_normal_exit_fact_receipt_misconduct_case_id",
            "misconduct_case_hash value = var:zg361_workforce_normal_exit_fact_receipt_misconduct_case_hash",
            "misconduct_evidence_id value = var:zg361_workforce_normal_exit_fact_receipt_misconduct_evidence_id",
            "misconduct_evidence_hash value = var:zg361_workforce_normal_exit_fact_receipt_misconduct_evidence_hash",
        ):
            self.assertIn(token, capture)
        self.assertNotIn("misconduct_case_id value = 1", capture)
        self.assertNotIn("misconduct_case_hash value = 1", capture)
        self.assertNotIn("misconduct_evidence_id value = 1", capture)
        self.assertNotIn("misconduct_evidence_hash value = 1", capture)
        self.assertNotIn("exit_class value = 2", self.effects)
        self.assertNotIn("receipt_prior_pip_state = 4", capture)
        self.assertNotIn("receipt_prior_pip_outcome_code = 2", capture)

    def test_08_exit_history_is_immutable_and_exact_replay_only(self) -> None:
        capture = block(self.effects, "zg361_workforce_rehire_fact_capture_exit_effect")
        self.assertIn("state value = 1", capture)
        self.assertIn("status value = 2", capture)
        self.assertIn("red_code value = 27611", capture)
        self.assertIn("exit_receipt_id = var:zg361_workforce_normal_exit_fact_receipt_id", capture)
        self.assertIn(
            "exit_pip_present value = var:zg361_workforce_normal_exit_fact_receipt_prior_pip_present",
            capture,
        )
        self.assertIn("exit_pip_case_id = var:zg361_workforce_normal_exit_fact_receipt_prior_pip_case_id", capture)
        self.assertLess(
            capture.index("limit = { var:zg361_workforce_normal_exit_fact_receipt_prior_pip_present = 1 }"),
            capture.index("exit_pip_case_id value = var:zg361_workforce_normal_exit_fact_receipt_prior_pip_case_id"),
        )
        self.assertIn("exit_observed_year value = var:zg361_workforce_normal_exit_fact_receipt_exit_year", capture)
        self.assertIn("old_result_hash value = var:zg361_workforce_normal_exit_fact_receipt_prior_result_hash", capture)

    def test_calculated_hc_guards_use_comparison_rhs_not_trigger_equality(self) -> None:
        direct_computed_equality = (
            r"(?m)^\s*var:[A-Za-z0-9_]+\s*=\s*\{\s*value\s*="
        )
        for name, fields in (
            (
                "zg361_workforce_rehire_fact_capture_exit_effect",
                (
                    "zg361_workforce_normal_exit_fact_receipt_hc_occupied_after",
                    "zg361_workforce_normal_exit_fact_receipt_hc_frozen_after",
                    "zg361_workforce_normal_exit_fact_receipt_hc_authorized_before",
                    "zg361_workforce_normal_exit_fact_receipt_hc_authorized_after",
                ),
            ),
            (
                "zg361_workforce_rehire_fact_capture_growth_effect",
                (
                    "zg361_workforce_rehire_fact_exit_hc_occupied_after",
                    "zg361_workforce_rehire_fact_exit_hc_frozen_after",
                    "zg361_workforce_rehire_fact_exit_hc_authorized_before",
                    "zg361_workforce_rehire_fact_exit_hc_authorized_after",
                ),
            ),
        ):
            with self.subTest(effect=name):
                source = block(self.effects, name)
                self.assertNotRegex(source, direct_computed_equality)
                for field in fields:
                    self.assertEqual(source.count(f"var:{field} >= {{"), 1)
                    self.assertEqual(source.count(f"var:{field} <= {{"), 1)

    def test_09_growth_requires_full_consumed_probation_receipt(self) -> None:
        growth = block(self.effects, "zg361_workforce_rehire_fact_capture_growth_effect")
        for field in generator.PROBATION_REQUIRED_FIELDS:
            self.assertIn(f"has_variable = {generator.PROBATION_PREFIX}_{field}", growth)
        for token in (
            "probation_fact_state = 4",
            "probation_fact_published = 1",
            "probation_fact_consumed = 1",
            "probation_fact_subject = this",
            "probation_fact_consume_subject = this",
            "probation_fact_outcome_id = var:zg361_workforce_probation_fact_consume_outcome_id",
            "probation_fact_hire_case = var:zg361_workforce_probation_fact_consume_workforce_case",
        ):
            self.assertIn(token, growth)

    def test_10_growth_is_strictly_post_exit_and_external(self) -> None:
        growth = block(self.effects, "zg361_workforce_rehire_fact_capture_growth_effect")
        self.assertIn("rehire_fact_state = 1", growth)
        self.assertIn("rehire_fact_exit_observed_year < current_year", growth)
        self.assertIn("result_delivered_year = current_year", growth)
        self.assertIn("result_delivered_year > var:zg361_workforce_rehire_fact_exit_observed_year", growth)
        self.assertIn(
            "NOT = { var:zg361_workforce_probation_fact_owner = var:zg361_workforce_rehire_fact_exit_owner }",
            growth,
        )
        self.assertIn(
            "NOT = { var:zg361_workforce_probation_fact_hire_case = var:zg361_workforce_rehire_fact_exit_case }",
            growth,
        )

    def test_11_growth_requires_live_settled_result_exactly_matching_canonical(self) -> None:
        growth = block(self.effects, "zg361_workforce_rehire_fact_capture_growth_effect")
        for token in (
            "result_case_owner = var:zg361_workforce_probation_fact_owner",
            "result_cycle_serial = var:zg361_workforce_probation_fact_source_result_cycle",
            "result_case_serial = var:zg361_workforce_probation_fact_source_result_case",
            "result_case_state = var:zg361_workforce_probation_fact_source_result_state",
            "result_settlement_posted_serial = var:zg361_workforce_probation_fact_source_result_settlement_receipt",
            "result_grade = var:zg361_workforce_probation_fact_source_result_grade",
            "result_grade_reason = var:zg361_workforce_probation_fact_source_result_reason",
            "result_kpi_frozen = var:zg361_workforce_probation_fact_source_result_kpi",
            "result_rank_frozen = var:zg361_workforce_probation_fact_source_result_rank",
        ):
            self.assertIn(token, growth)

    def test_12_growth_requires_exact_workforce_269_poststate(self) -> None:
        growth = block(self.effects, "zg361_workforce_rehire_fact_capture_growth_effect")
        for token in (
            "m269_object_consumed = 1",
            "m269_write_owner = var:zg361_workforce_probation_fact_owner",
            "m269_write_subject = this",
            "m269_outcome_settled = 1",
            "m269_outcome_pending = 0",
            "m269_outcome_provenance_locked = 1",
            "m269_last_outcome_id = var:zg361_workforce_probation_fact_outcome_id",
            "m269_consumed_candidate = this",
            "m269_outcome_evidence_id = var:zg361_workforce_probation_fact_outcome_evidence_id",
            "m269_outcome_evidence_hash = var:zg361_workforce_probation_fact_outcome_evidence_hash",
            "m269_final_quality = var:zg361_workforce_probation_fact_outcome_quality",
        ):
            self.assertIn(token, growth)

    def test_13_growth_evidence_never_reuses_exit_receipts(self) -> None:
        growth = block(self.effects, "zg361_workforce_rehire_fact_capture_growth_effect")
        self.assertIn(
            "NOT = { var:zg361_workforce_probation_fact_outcome_evidence_id = var:zg361_workforce_rehire_fact_exit_receipt_id }",
            growth,
        )
        self.assertIn(
            "NOT = { var:zg361_workforce_probation_fact_outcome_evidence_hash = var:zg361_workforce_rehire_fact_exit_receipt_hash }",
            growth,
        )
        self.assertNotIn("zg361_we_ad_external_outcome_", growth)

    def test_14_serials_are_computed_before_commit_without_read_after_write(self) -> None:
        growth = block(self.effects, "zg361_workforce_rehire_fact_capture_growth_effect")
        finalize = block(self.effects, "zg361_workforce_rehire_fact_finalize_m276_effect")
        self.assertIn("next_subject_history_serial", growth)
        self.assertIn("subject_history_serial value = scope:zg361_workforce_rehire_fact_next_subject_history_serial", growth)
        self.assertNotIn("change_variable = { name = zg361_workforce_rehire_fact_subject_history_serial", growth)
        self.assertIn("next_subject_consume_serial", finalize)
        self.assertIn("subject_consume_serial value = scope:zg361_workforce_rehire_fact_next_subject_consume_serial", finalize)
        self.assertNotIn("change_variable = { name = zg361_workforce_rehire_fact_subject_consume_serial", finalize)

    def test_15_current_case_only_sets_future_schedule_not_history(self) -> None:
        prepare = block(self.effects, "zg361_workforce_rehire_fact_prepare_m276_effect")
        self.assertIn("value = { value = var:zg361_case_ad_cycle_serial add = 1 }", prepare)
        self.assertIn("historical_cycle < var:zg361_case_ad_cycle_serial", prepare)
        self.assertIn("NOT = { var:zg361_workforce_rehire_fact_historical_case_id = var:zg361_case_ad_case_serial }", prepare)
        for field in (
            "historical_case_id",
            "historical_case_hash",
            "historical_cycle",
            "growth_evidence_id",
            "growth_evidence_hash",
        ):
            self.assertNotIn(
                f"name = zg361_workforce_rehire_fact_{field} value = var:zg361_case_ad_",
                prepare,
            )

    def test_16_seven_aliases_copy_once_only_from_canonical_history(self) -> None:
        prepare = block(self.effects, "zg361_workforce_rehire_fact_prepare_m276_effect")
        clear = block(self.effects, "zg361_workforce_rehire_fact_clear_legacy_envelope_effect")
        for alias, fact in generator.LEGACY_ALIAS_TO_FACT.items():
            legacy = f"zg361_we_ad_external_{alias}"
            canonical = f"zg361_workforce_rehire_fact_{fact}"
            setter = f"set_variable = {{ name = {legacy} value = var:{canonical} }}"
            with self.subTest(alias=alias):
                self.assertEqual(self.effects.count(setter), 1)
                self.assertIn(setter, prepare)
                self.assertIn(f"remove_variable = {legacy}", clear)

    def test_17_partial_or_foreign_legacy_envelope_is_not_cleared(self) -> None:
        prepare = block(self.effects, "zg361_workforce_rehire_fact_prepare_m276_effect")
        self.assertIn("NOT = {\n                OR = {", prepare)
        self.assertLess(prepare.index("NOT = {\n                OR = {"), prepare.index("legacy_aliases_materialized value = 1"))
        failure = prepare[prepare.index("else = {", prepare.index("submit_m276_rehire_history_effect")) :]
        self.assertIn("clear_legacy_envelope_effect = yes", failure)
        self.assertIn("red_code value = 27632", failure)

    def test_18_internal_legacy_adapter_gets_no_caller_truth(self) -> None:
        prepare = block(self.effects, "zg361_workforce_rehire_fact_prepare_m276_effect")
        self.assertIn("zg361_we_submit_m276_rehire_history_effect", prepare)
        self.assertIn("REHIRE_ID = var:zg361_workforce_rehire_fact_rehire_id", prepare)
        self.assertIn("HISTORY_RETAINED = 1", prepare)
        self.assertIn("MISCONDUCT_HISTORY_RETAINED = 1", prepare)
        self.assertNotIn("$REHIRE_ID$", prepare)
        self.assertNotIn("$HISTORICAL_CASE_ID$", prepare)
        self.assertNotIn("$GROWTH_EVIDENCE_ID$", prepare)

    def test_19_finalize_requires_a_or_b_exact_object_and_receipt_ack(self) -> None:
        finalize = block(self.effects, "zg361_workforce_rehire_fact_finalize_m276_effect")
        for token in (
            "m276_object_consumed = 1",
            "m276_object_owner = var:zg361_workforce_rehire_fact_prepared_owner",
            "m276_object_subject = this",
            "m276_object_cycle = var:zg361_workforce_rehire_fact_prepared_cycle",
            "m276_object_case = var:zg361_workforce_rehire_fact_prepared_case",
            "m276_receipt_choice = 1",
            "m276_receipt_choice = 2",
            "m276_rehire_id = var:zg361_workforce_rehire_fact_rehire_id",
            "m276_old_history_retained = 1",
            "m276_hc_touched = 0",
            "m276_growth_evidence_frozen = 1",
            "m276_history_wipe_attempt = 1",
        ):
            self.assertIn(token, finalize)
        self.assertNotIn("m276_receipt_choice = 3", finalize)

    def test_20_finalize_clears_only_transient_envelope_and_keeps_sources(self) -> None:
        clear = block(self.effects, "zg361_workforce_rehire_fact_clear_legacy_envelope_effect")
        finalize = block(self.effects, "zg361_workforce_rehire_fact_finalize_m276_effect")
        for forbidden in (
            "remove_variable = zg361_workforce_rehire_fact_exit_",
            "remove_variable = zg361_workforce_rehire_fact_historical_",
            "remove_variable = zg361_workforce_rehire_fact_growth_",
            "remove_variable = zg361_workforce_rehire_fact_misconduct_",
            "remove_variable = zg361_workforce_rehire_fact_pip_",
            "remove_variable = zg361_workforce_exit_fact_",
            "remove_variable = zg361_workforce_normal_exit_fact_",
            "remove_variable = zg361_workforce_probation_fact_",
        ):
            self.assertNotIn(forbidden, clear + finalize)
        self.assertLess(finalize.index("clear_legacy_envelope_effect = yes"), finalize.index("consumed value = 1"))
        self.assertLess(finalize.index("consumed value = 1"), finalize.index("state value = 4"))

    def test_21_package_never_changes_hc_gold_or_characters_and_has_no_route_c(self) -> None:
        lowered = (self.effects + self.events).lower()
        for forbidden in (
            "add_gold",
            "remove_courtier",
            "create_character",
            "appoint_court_position",
            "revoke_court_position",
            "zg361_ch_hc_available add",
            "zg361_ch_hc_occupied add",
            "m276_route_c",
            "decision =",
            "ocr",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_22_notice_is_player_subject_only_and_grants_no_authority(self) -> None:
        notice = block(self.events, "zg361wrf.1")
        self.assertIn("type = character_event\n    theme = stewardship", notice)
        self.assertIn("is_ai = no", notice)
        self.assertIn("rehire_fact_state = 4", notice)
        self.assertIn("rehire_fact_consumed = 1", notice)
        self.assertIn("rehire_fact_consume_subject = this", notice)
        for forbidden in ("zg361_is_celestial_liege_trigger", "m276_", "add_gold", "case_kernel"):
            self.assertNotIn(forbidden, notice)

    def test_23_localization_has_zh_en_and_seven_structural_placeholders(self) -> None:
        english_path = MOD_ROOT / "localization/english/zg361_workforce_rehire_fact_l_english.yml"
        chinese_path = MOD_ROOT / "localization/simp_chinese/zg361_workforce_rehire_fact_l_simp_chinese.yml"
        english = english_path.read_text(encoding="utf-8-sig")
        chinese = chinese_path.read_text(encoding="utf-8-sig")
        for key in ("zg361wrf.1.t:0", "zg361wrf.1.desc:0", "zg361wrf.1.a:0"):
            self.assertIn(key, english)
            self.assertIn(key, chinese)
        self.assertIn("旧 3.25", chinese)
        self.assertIn("later real performance evidence", english)
        for language in generator.LANGUAGES[2:]:
            text = (
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_workforce_rehire_fact_l_{language}.yml"
            ).read_text(encoding="utf-8-sig")
            self.assertEqual(text.replace(f"l_{language}:", "l_english:", 1), english)

    def test_24_spec_records_partial_readiness_and_integration_boundary(self) -> None:
        for token in (
            generator.READINESS,
            "四个 ABI 均已有跨事件 caller",
            "六个跨事件 caller 已接",
            "尚无 loader、MCP-first paused snapshot 或实机证据",
            "失败 PIP 撤职",
            "不是正常离职",
            "B2 #075 route A",
            "hc_ledger_settled=1",
            "occupied -> frozen",
            "exit_hc_*",
            "probation 三代有界 ledger",
            "不同 owner growth → 回旧 owner #276",
            "ledger_slot_1_*",
            "ledger_slot_2_*",
            "第四代容量不足明确 RED",
            "settled HC provenance",
            "不得 `remove_variable` 清洗旧案",
            "current ticket cycle + 1",
            "route C",
            "同一 effect",
            "failed-PIP #277 路径",
        ):
            self.assertIn(token, self.spec)


if __name__ == "__main__":
    unittest.main()
