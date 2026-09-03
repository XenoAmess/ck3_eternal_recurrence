#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strong L0 contracts for the generated L/AE/AF CK3 runtime.

These tests verify deterministic source, shared-kernel guards, receipts,
financial conservation, deadlines, and the single-card portfolio adapter.
They are static-ready evidence only; they do not claim CK3 or MCP live proof.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

import gen_361_compensation_runtime as generator
import zg361_phase2_compensation_model as model


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = (
    MOD_ROOT
    / "common"
    / "scripted_effects"
    / "zg361_generated_compensation_runtime_effects.txt"
)
EVENTS_PATH = MOD_ROOT / "events" / "zg361_generated_compensation_runtime_events.txt"
LANGUAGES = (
    "english",
    "simp_chinese",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)
PLACEHOLDER_LANGUAGES = LANGUAGES[2:]
FIVE_FIELDS = ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE")
ILLEGAL_TRIGGER_ARITHMETIC_RHS = re.compile(
    r"(?:\b(?:root\.)?var:[^\s{}=<>]+|\bscope:[^\s{}=<>]+|\$[A-Z0-9_]+\$)"
    r"\s*(?:=|>=|<=|>|<)\s*\{\s*value\s*="
)
NEGATIVE_ADD_GOLD = re.compile(
    r"\badd_gold\s*=\s*(?:-\s*\d+|\{[^\r\n}]*\bsubtract\s*=)"
)
BARE_REMOVE_GOLD = re.compile(r"(?m)^\s*remove_gold\s*=")
SHORT_TERM_GOLD_DEBIT = re.compile(r"(?m)^\s*remove_short_term_gold\s*=")


def top_level_block(text: str, name: str) -> str:
    """Return one brace-balanced top-level CK3 block."""

    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", text)
    if match is None:
        raise AssertionError(f"missing top-level block: {name}")
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
    raise AssertionError(f"unterminated top-level block: {name}")


def code_without_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


def localization_keys(payload: bytes) -> tuple[str, ...]:
    """Return ordered CK3 localization keys, excluding the language header."""

    return tuple(
        match.group(1)
        for line in payload.decode("utf-8-sig").splitlines()
        if (match := re.match(r"^\s+([^\s:]+):\d+\s", line)) is not None
    )


def assert_balanced(test: unittest.TestCase, text: str, label: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for line_number, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0]
        for char in code:
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
                test.assertGreaterEqual(
                    depth, 0, f"{label}:{line_number}: unexpected close brace"
                )
    test.assertFalse(quoted, f"{label}: unterminated quote")
    test.assertEqual(depth, 0, f"{label}: brace imbalance")


class CompensationRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = EFFECTS_PATH.read_text(encoding="utf-8-sig")
        cls.events = EVENTS_PATH.read_text(encoding="utf-8-sig")

    def test_trigger_arithmetic_never_uses_a_value_block_rhs(self) -> None:
        self.assertIsNone(
            ILLEGAL_TRIGGER_ARITHMETIC_RHS.search(self.effects),
            "CK3 scripted-effect loader treats RHS value/add as triggers",
        )

    def test_personal_gold_debits_use_the_ck3_11906_positive_value_effect(self) -> None:
        self.assertIsNone(
            NEGATIVE_ADD_GOLD.search(self.effects),
            "CK3 1.19.0.6 rejects negative add_gold values",
        )
        self.assertIsNone(
            BARE_REMOVE_GOLD.search(self.effects),
            "CK3 1.19.0.6 does not register a bare remove_gold effect",
        )
        self.assertEqual(len(SHORT_TERM_GOLD_DEBIT.findall(self.effects)), 14)

    def test_exact_33_ids_and_frozen_l_ae_af_stage_partitions(self) -> None:
        expected_ids = tuple((*range(82, 92), *range(278, 301)))
        expected_stages = {
            "l": ((82, 83, 84), (85, 86), (87, 88, 89), (90, 91)),
            "ae": (
                (278, 279, 280),
                (281, 282),
                (283, 284, 285),
                (286, 287),
                (288, 289),
            ),
            "af": (
                (290, 291, 292),
                (293, 294),
                (295, 296),
                (297, 298),
                (299, 300),
            ),
        }
        expected_states = {
            "l": ("formula_locked", "funds_reserved", "granted", "held", "settled"),
            "ae": ("payable", "due", "decided", "corrected", "appealed", "closed"),
            "af": (
                "nominated",
                "granted",
                "cliff_reached",
                "vesting",
                "exit_classified",
                "settled",
            ),
        }
        self.assertEqual(generator.EXPECTED_IDS, expected_ids)
        self.assertEqual(tuple(row.mechanism_id for row in generator.MECHANISMS), expected_ids)
        self.assertEqual(len(generator.MECHANISMS), 33)
        self.assertEqual(len(generator.MECHANISM_BY_ID), 33)
        self.assertEqual({row.key: row.stages for row in generator.DOMAINS}, expected_stages)
        self.assertEqual({row.key: row.states for row in generator.DOMAINS}, expected_states)
        self.assertEqual(tuple(sorted(generator.DOMAIN_BY_ID)), expected_ids)
        for row in generator.MECHANISMS:
            with self.subTest(registry=row.mechanism_id):
                oracle = model.MECHANISM_BEHAVIORS[row.mechanism_id]
                self.assertEqual(row.domain, oracle.domain.lower())
                self.assertEqual(row.title_en, oracle.title)
                self.assertEqual(row.behavior, oracle.behavior)
        self.assertEqual(
            generator.STAGE_BY_ID,
            {
                mechanism_id: state
                for domain in generator.DOMAINS
                for state, ids in enumerate(domain.stages, start=1)
                for mechanism_id in ids
            },
        )

    def test_exact_11_outputs_are_current_bom_localized_and_isolated(self) -> None:
        expected = {
            "common/scripted_effects/zg361_generated_compensation_runtime_effects.txt",
            "events/zg361_generated_compensation_runtime_events.txt",
            *(
                f"localization/{language}/zg361_compensation_runtime_l_{language}.yml"
                for language in LANGUAGES
            ),
        }
        rendered = generator.outputs()
        actual = {path.relative_to(MOD_ROOT).as_posix() for path in rendered}
        self.assertEqual(actual, expected)
        self.assertEqual(len(rendered), 11)
        self.assertEqual(sum(path.suffix == ".yml" for path in rendered), 9)
        for path, payload in rendered.items():
            with self.subTest(path=path.relative_to(MOD_ROOT)):
                self.assertTrue(payload.startswith(generator.BOM))
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), payload)

        english_path = (
            MOD_ROOT
            / "localization"
            / "english"
            / "zg361_compensation_runtime_l_english.yml"
        )
        english = rendered[english_path].decode("utf-8-sig")
        chinese_path = (
            MOD_ROOT
            / "localization"
            / "simp_chinese"
            / "zg361_compensation_runtime_l_simp_chinese.yml"
        )
        self.assertNotEqual(rendered[chinese_path].decode("utf-8-sig"), english)
        for language in PLACEHOLDER_LANGUAGES:
            path = (
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_compensation_runtime_l_{language}.yml"
            )
            with self.subTest(placeholder=language):
                self.assertEqual(
                    rendered[path].decode("utf-8-sig"),
                    english.replace("l_english:", f"l_{language}:", 1),
                )

        forbidden_output_fragments = (
            "on_action",
            "scoreboard",
            "case_kernel",
            "b1_",
            "b2_",
        )
        for relative in actual:
            self.assertFalse(
                any(fragment in relative.lower() for fragment in forbidden_output_fragments),
                relative,
            )
        for relative in (
            "tools/gen_361_compensation_runtime.py",
            "tools/test_zg361_compensation_runtime.py",
            "docs/361-compensation-lti-ck3-runtime-spec.md",
        ):
            self.assertTrue((MOD_ROOT / relative).read_bytes().startswith(generator.BOM))

    def test_generator_is_deterministic_and_all_nine_localizations_have_bom_key_parity(self) -> None:
        first = generator.outputs()
        second = generator.outputs()
        self.assertEqual(tuple(first), tuple(second))
        self.assertEqual(first, second)

        expected_keys = (
            "zg361comp.1.t",
            "zg361comp.1.desc",
            *(f"zg361comp.1.l{state}" for state in range(1, 5)),
            *(f"zg361comp.1.ae{state}" for state in range(1, 6)),
            *(f"zg361comp.1.af{state}" for state in range(1, 6)),
            "zg361comp.1.a",
            "zg361comp.1.b",
            "zg361comp.1.c",
            "zg361comp.289.t",
            "zg361comp.289.desc",
            "zg361comp.289.a",
            "zg361comp.289.b",
            "zg361comp.900.t",
            "zg361comp.900.desc",
            "zg361comp.901.t",
            "zg361comp.901.desc",
            "zg361comp.902.t",
            "zg361comp.902.desc",
            "zg361comp.903.t",
            "zg361comp.903.desc",
            "zg361comp.904.t",
            "zg361comp.904.desc",
            "zg361comp.ok",
        )
        localization_paths = [
            MOD_ROOT
            / "localization"
            / language
            / f"zg361_compensation_runtime_l_{language}.yml"
            for language in LANGUAGES
        ]
        self.assertEqual(len(localization_paths), 9)
        for path in localization_paths:
            with self.subTest(language=path.parent.name):
                payload = first[path]
                self.assertTrue(payload.startswith(generator.BOM))
                keys = localization_keys(payload)
                self.assertEqual(keys, expected_keys)
                self.assertEqual(len(keys), len(set(keys)))

    def test_generated_ck3_sources_are_balanced_and_top_level_keys_unique(self) -> None:
        assert_balanced(self, self.effects, "compensation effects")
        assert_balanced(self, self.events, "compensation events")
        for source, label in ((self.effects, "effects"), (self.events, "events")):
            # Some interpolated nested if/AND branches intentionally begin in
            # column zero. Only project effect/event identifiers are top-level
            # keys for the uniqueness contract.
            keys = re.findall(r"(?m)^(zg361_comp_[A-Za-z0-9_]+|zg361comp\.\d+)\s*=\s*\{", source)
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            self.assertEqual(duplicates, [], label)

    def test_openers_and_all_manager_entries_enforce_duke_plus_and_reviewable_subject(self) -> None:
        for domain in generator.DOMAINS:
            with self.subTest(opener=domain.key):
                source = top_level_block(
                    self.effects, f"zg361_comp_open_{domain.key}_case_effect"
                )
                self.assertIn("zg361_is_celestial_liege_trigger = yes", source)
                self.assertIn("zg361_is_reviewable_vassal_trigger = yes", source)
                self.assertIn("liege = root", source)
                self.assertIn(f"zg361_case_{domain.key}_open_effect = yes", source)
                self.assertNotIn("is_ai = no", code_without_comments(source))

        for mechanism_id in generator.EXPECTED_IDS:
            domain = generator.DOMAIN_BY_ID[mechanism_id].key
            state = generator.STAGE_BY_ID[mechanism_id]
            with self.subTest(manager_entry=mechanism_id):
                source = top_level_block(
                    self.effects,
                    f"zg361_comp_m{mechanism_id:03d}_manager_apply_effect",
                )
                self.assertIn("zg361_is_celestial_liege_trigger = yes", source)
                self.assertIn("zg361_is_reviewable_vassal_trigger = yes", source)
                self.assertIn("liege = root", source)
                self.assertIn("EXPECTED_OWNER = root", source)
                self.assertIn(f"EXPECTED_STATE = {state}", source)
                self.assertIn(
                    f"zg361_comp_m{mechanism_id:03d}_core_effect", source
                )
                self.assertNotIn("is_ai = no", code_without_comments(source))
                self.assertNotIn("highest_held_title_tier", source)
                self.assertEqual(domain, generator.MECHANISM_BY_ID[mechanism_id].domain)

    def test_all_33_cores_have_five_field_guards_and_single_use_receipts(self) -> None:
        for mechanism_id in generator.EXPECTED_IDS:
            domain = generator.DOMAIN_BY_ID[mechanism_id].key
            state = generator.STAGE_BY_ID[mechanism_id]
            prefix = f"zg361_comp_m{mechanism_id:03d}"
            with self.subTest(mechanism=mechanism_id):
                source = top_level_block(self.effects, f"{prefix}_core_effect")
                self.assertIn("zg361_case_kernel_full_guard_trigger", source)
                for field in FIVE_FIELDS:
                    self.assertIn(f"{field}_VAR = zg361_case_{domain}_", source)
                    self.assertIn(f"TICKET_{field}", source)
                    self.assertIn(f"{prefix}_receipt_{field.lower()}", source)
                self.assertIn(f"EXPECTED_STATE = {state}", source)
                self.assertEqual(
                    source.count("zg361_case_kernel_record_operation_effect"), 1
                )
                self.assertIn(f"OPERATION_ID = {mechanism_id}", source)
                self.assertIn(f"has_variable = {prefix}_receipt_active", source)
                self.assertIn(f"var:{prefix}_receipt_active = 0", source)
                self.assertIn(
                    f"set_variable = {{ name = {prefix}_receipt_active value = 1 }}",
                    source,
                )
                self.assertEqual(source.count(f"{prefix}_consume_effect = yes"), 1)
                self.assertIn(
                    f"var:{prefix}_receipt_route = scope:zg361_comp_route", source
                )
                self.assertIn(
                    "set_variable = { name = zg361_comp_last_disposition value = 2 }",
                    source,
                )
                self.assertIn(
                    "set_variable = { name = zg361_comp_typed_red value = 3 }",
                    source,
                )

    def test_consumers_publish_one_result_case_correlated_promotion_receipt(self) -> None:
        required_guard = (
            "var:zg361_pp_m147_receipt_serial = var:zg361_comp_result_case"
        )
        for mechanism_id in generator.EXPECTED_IDS:
            with self.subTest(mechanism=mechanism_id):
                source = top_level_block(
                    self.effects, f"zg361_comp_m{mechanism_id:03d}_consume_effect"
                )
                consumed = source.index(
                    f"name = zg361_comp_m{mechanism_id:03d}_consumed value = 1"
                )
                published = source.index(
                    "name = zg361_comp_promotion_receipt_posted value = 1"
                )
                self.assertLess(consumed, published)
                self.assertIn(required_guard, source)
                self.assertIn(
                    "name = zg361_comp_promotion_receipt_serial value = var:zg361_pp_m147_receipt_serial",
                    source,
                )
                self.assertIn(
                    "name = zg361_comp_promotion_receipt_case value = var:zg361_comp_result_case",
                    source,
                )
                self.assertIn(
                    f"name = zg361_comp_promotion_receipt_operation value = {mechanism_id}",
                    source,
                )
                self.assertIn(
                    f"name = zg361_comp_promotion_receipt_revision value = var:zg361_comp_m{mechanism_id:03d}_visible_revision",
                    source,
                )

        for domain in generator.DOMAINS:
            opener = top_level_block(
                self.effects, f"zg361_comp_open_{domain.key}_case_effect"
            )
            self.assertIn(
                "name = zg361_comp_promotion_receipt_active value = 0", opener
            )
            self.assertIn(
                "remove_variable = zg361_comp_promotion_receipt_serial", opener
            )

    def test_every_numbered_write_has_one_guarded_consumer_and_stage_barrier(self) -> None:
        for mechanism_id in generator.EXPECTED_IDS:
            domain = generator.DOMAIN_BY_ID[mechanism_id].key
            state = generator.STAGE_BY_ID[mechanism_id]
            prefix = f"zg361_comp_m{mechanism_id:03d}"
            with self.subTest(mechanism=mechanism_id):
                self.assertEqual(self.effects.count(f"{prefix}_consume_effect = {{"), 1)
                source = top_level_block(self.effects, f"{prefix}_consume_effect")
                for field in FIVE_FIELDS:
                    self.assertIn(f"{field}_VAR = zg361_case_{domain}_", source)
                self.assertIn(f"var:{prefix}_receipt_active = 1", source)
                self.assertIn(f"var:{prefix}_consumed = 0", source)
                self.assertIn(
                    f"set_variable = {{ name = {prefix}_consumed value = 1 }}",
                    source,
                )
                first_write = generator.special_payload(mechanism_id).splitlines()[0].strip()
                self.assertIn(first_write, source)
                barrier = (
                    "zg361_comp_af_try_start_vesting_effect = yes"
                    if domain == "af" and state == 4
                    else f"zg361_comp_{domain}_try_advance_{state:02d}_effect = yes"
                )
                self.assertIn(barrier, source)

        for domain in generator.DOMAINS:
            for state, ids in enumerate(domain.stages, start=1):
                if domain.key == "af" and state == 4:
                    continue
                with self.subTest(stage=f"{domain.key}:{state}"):
                    source = top_level_block(
                        self.effects,
                        f"zg361_comp_{domain.key}_try_advance_{state:02d}_effect",
                    )
                    for mechanism_id in ids:
                        self.assertIn(
                            f"var:zg361_comp_m{mechanism_id:03d}_consumed = 1",
                            source,
                        )
                    self.assertEqual(
                        source.count(
                            f"zg361_case_{domain.key}_advance_{state:02d}_effect"
                        ),
                        1,
                    )

        vesting = top_level_block(
            self.effects, "zg361_comp_af_try_start_vesting_effect"
        )
        self.assertIn("var:zg361_comp_m297_consumed = 1", vesting)
        self.assertIn("var:zg361_comp_m298_consumed = 1", vesting)
        exit_barrier = top_level_block(
            self.effects, "zg361_comp_af_request_exit_effect"
        )
        self.assertIn("EXPECTED_STATE = 4", exit_barrier)
        self.assertEqual(exit_barrier.count("zg361_case_af_advance_04_effect"), 1)

    def test_every_id_has_a_numeric_resource_write_and_a_real_downstream_consumer(self) -> None:
        # This is deliberately stronger than checking a choice string or an
        # operation receipt.  Each producer token is a numeric business fact;
        # the second token is the later calculation, payment, deadline, or
        # projection that actually consumes it.
        contracts = {
            82: ("name = zg361_comp_m082_total_reward", "value = var:zg361_comp_m082_total_reward"),
            83: ("name = zg361_comp_m083_computed_bonus", "value = var:zg361_comp_m083_computed_bonus"),
            84: ("name = zg361_comp_m084_frozen_gross", "var:zg361_comp_bonus_total"),
            85: ("name = zg361_comp_m085_cliff_gap_years", "value = var:zg361_comp_m085_cliff_gap_years"),
            86: ("name = zg361_comp_m086_hold_policy", "var:zg361_comp_m086_route = 1"),
            87: ("name = zg361_comp_m087_position_bps", "value = var:zg361_comp_m087_position_bps"),
            88: ("name = zg361_comp_m088_raise_pool", "value = var:zg361_comp_m088_raise_pool"),
            89: ("name = zg361_comp_m089_cash_raise", "add = var:zg361_comp_m089_cash_raise"),
            90: ("name = zg361_comp_m090_spot_gross", "value = var:zg361_comp_m090_spot_gross"),
            91: ("name = zg361_comp_m091_award_total", "name = zg361_comp_m091_source_spot_gross"),
            278: ("name = zg361_comp_m278_projection_mode", "name = zg361_comp_m278_promised"),
            279: ("name = zg361_comp_m279_amount", "value = var:zg361_comp_m279_amount"),
            280: ("name = zg361_comp_m280_proration_bps", "multiply = var:zg361_comp_m280_proration_bps"),
            281: ("name = zg361_comp_m281_decision", "var:zg361_comp_m281_route = 2"),
            282: ("name = zg361_comp_m282_backpay", "name = zg361_comp_ae_statement_owed add = 4"),
            283: ("name = zg361_comp_m283_cash_raise", "name = zg361_comp_ae_statement_owed add = var:zg361_comp_m283_cash_raise"),
            284: ("name = zg361_comp_m284_next_cycle_delta", "add = var:zg361_comp_ae_next_cycle_base_delta"),
            285: ("name = zg361_comp_m285_subject_raise", "name = zg361_comp_ae_statement_owed add = var:zg361_comp_m285_subject_raise"),
            286: ("name = zg361_comp_m286_statement_delta", "name = zg361_comp_ae_statement_owed add = var:zg361_comp_m286_statement_delta"),
            287: ("name = zg361_comp_m287_visibility_mode", "name = zg361_comp_m287_named_peer_salary_visible"),
            288: ("name = zg361_comp_m288_repair_due", "name = zg361_comp_ae_statement_owed add = var:zg361_comp_m288_repair_due"),
            289: ("name = zg361_comp_m289_outcome", "name = zg361_comp_ae_statement_paid add = 4"),
            290: ("name = zg361_comp_m290_nomination_score", "var:zg361_comp_m290_eligible = 1"),
            291: ("name = zg361_comp_af_grant_base_units", "var:zg361_comp_af_grant_base_units"),
            292: ("name = zg361_comp_m292_risk_kind", "var:zg361_comp_m292_risk_kind = 3"),
            293: ("name = zg361_comp_af_conversion_units", "var:zg361_comp_af_conversion_units"),
            294: ("name = zg361_comp_m294_liquid_value", "multiply = var:zg361_comp_m294_liquidity_bps"),
            295: ("name = zg361_comp_af_cliff_days", "var:zg361_comp_af_cliff_days = 180"),
            296: ("name = zg361_comp_af_cadence_days", "var:zg361_comp_af_cadence_days = 90"),
            297: ("name = zg361_comp_m297_service_bps", "value = var:zg361_comp_m297_service_bps"),
            298: ("name = zg361_comp_m298_organization_gate", "var:zg361_comp_m298_organization_gate = 1"),
            299: ("name = zg361_comp_m299_leaver_class", "name = zg361_comp_af_forfeited_units add = var:zg361_comp_af_unvested_service"),
            300: ("name = zg361_comp_m300_requested_units", "name = zg361_comp_af_repurchased_units add = 10"),
        }
        self.assertEqual(set(contracts), set(generator.EXPECTED_IDS))
        for mechanism_id, (producer, consumer) in contracts.items():
            with self.subTest(mechanism_id=mechanism_id):
                source = top_level_block(
                    self.effects, f"zg361_comp_m{mechanism_id:03d}_consume_effect"
                )
                self.assertIn(producer, source)
                self.assertIn(consumer, self.effects)
                self.assertTrue(
                    all(route.resource_values or not route.materializes_object for route in model.MECHANISM_ROUTE_OUTCOMES[mechanism_id])
                )

    def test_route_c_no_object_contract_matches_the_executable_model(self) -> None:
        expected = {84, 88, 90, 282, 283, 285, 288, 293, 300}
        self.assertEqual(generator.NO_OBJECT_ROUTE3_IDS, expected)
        self.assertEqual(model.NO_OBJECT_ROUTE3_IDS, expected)
        for mechanism_id in expected:
            with self.subTest(mechanism_id=mechanism_id):
                payload = generator.special_payload(mechanism_id)
                self.assertIn(
                    f"name = zg361_comp_m{mechanism_id:03d}_object_materialized value = 0",
                    payload,
                )

    def test_route_dependent_cash_helpers_use_the_frozen_dual_account_amounts(self) -> None:
        expected_helpers = {
            "zg361_comp_l_pay_spot_effect": ("zg361_comp_m090_pay", 7, 3, 10),
            "zg361_comp_l_pay_spot_bounded_effect": ("zg361_comp_m090_bounded", 4, 2, 6),
            "zg361_comp_af_pay_conversion_remainder_effect": ("zg361_comp_m293_cash6", 4, 2, 6),
            "zg361_comp_af_pay_unconverted_bonus_effect": ("zg361_comp_m293_cash10", 7, 3, 10),
        }
        for effect_name, (prefix, treasury, personal, gross) in expected_helpers.items():
            with self.subTest(effect=effect_name):
                source = top_level_block(self.effects, effect_name)
                self.assertIn(f"AMOUNT = {treasury}", source)
                self.assertIn(f"AMOUNT = {personal}", source)
                self.assertIn(f"var:{prefix}_treasury_status = 2", source)
                self.assertIn(f"var:{prefix}_personal_status = 2", source)
                self.assertIn(f"remove_treasury = {treasury}", source)
                self.assertIn(f"remove_short_term_gold = {personal}", source)
                self.assertIn(f"add_gold = {gross}", source)
                self.assertLess(
                    source.index(f"var:{prefix}_personal_status = 2"),
                    source.index(f"remove_treasury = {treasury}"),
                )
                for suffix in ("treasury_payer", "personal_payer", "recipient", "approver"):
                    self.assertIn(f"name = {prefix}_{suffix}", source)

        spot_core = top_level_block(self.effects, "zg361_comp_m090_core_effect")
        self.assertIn("scope:zg361_comp_route = 1", spot_core)
        self.assertIn("zg361_comp_l_pay_spot_effect = yes", spot_core)
        self.assertIn("scope:zg361_comp_route = 2", spot_core)
        self.assertIn("zg361_comp_l_pay_spot_bounded_effect = yes", spot_core)
        conversion_core = top_level_block(self.effects, "zg361_comp_m293_core_effect")
        self.assertIn("zg361_comp_af_pay_conversion_remainder_effect = yes", conversion_core)
        self.assertIn("zg361_comp_af_pay_unconverted_bonus_effect = yes", conversion_core)

    def test_bonus_reserve_settle_refund_and_clawback_use_frozen_sources(self) -> None:
        reserve = top_level_block(self.effects, "zg361_comp_l_reserve_bonus_effect")
        for token in (
            "scope:zg361_comp_route = 1",
            "remove_treasury = 14",
            "remove_short_term_gold = 6",
            "add_gold = 14",
            "scope:zg361_comp_route = 2",
            "remove_treasury = 11",
            "remove_short_term_gold = 5",
            "add_gold = 10",
            "name = zg361_comp_bonus_deferred_treasury_funded",
            "name = zg361_comp_bonus_deferred_personal_funded",
        ):
            self.assertIn(token, reserve)
        deferred = top_level_block(self.effects, "zg361_comp_l_consume_deferred_effect")
        self.assertIn("add_gold = { value = var:zg361_comp_bonus_deferred_unpaid_total }", deferred)
        self.assertIn("add_treasury = { value = var:zg361_comp_bonus_deferred_treasury_funded }", deferred)
        self.assertIn("add_gold = { value = var:zg361_comp_bonus_deferred_personal_funded }", deferred)
        self.assertIn("value = var:zg361_comp_m084_reserve_receipt", deferred)
        clawback = top_level_block(self.effects, "zg361_comp_l_clawback_bonus_effect")
        self.assertIn("gold >= 2", clawback)
        self.assertIn("remove_short_term_gold = 2", clawback)
        self.assertIn("value = var:zg361_comp_bonus_immediate_receipt_serial", clawback)
        clawback_case = top_level_block(self.effects, "zg361_comp_m086_core_effect")
        for suffix in ("owner", "subject", "cycle", "case"):
            self.assertIn(
                f"var:zg361_comp_bonus_immediate_receipt_frozen_{suffix}",
                clawback_case,
            )
            self.assertNotIn(
                f"var:zg361_comp_bonus_immediate_receipt_{suffix} =",
                clawback_case,
            )

    def test_deferred_statement_freezes_amount_and_both_payer_shares_before_deadline(self) -> None:
        freezer = top_level_block(
            self.effects, "zg361_comp_ae_freeze_due_obligation_effect"
        )
        for token in (
            "EXPECTED_STATE = 3",
            "name = zg361_comp_ae_due_frozen_gross value = var:zg361_comp_ae_statement_owed",
            "name = zg361_comp_ae_due_frozen_treasury",
            "name = zg361_comp_ae_due_frozen_personal",
            "name = zg361_comp_ae_due_obligation_treasury_payer",
            "name = zg361_comp_ae_due_obligation_personal_payer",
            "name = zg361_comp_ae_due_obligation_recipient",
            "name = zg361_comp_ae_due_obligation_frozen_case",
        ):
            self.assertIn(token, freezer)
        stage_two = top_level_block(
            self.effects, "zg361_comp_ae_try_advance_02_effect"
        )
        self.assertEqual(
            stage_two.count("zg361_comp_ae_freeze_due_obligation_effect = yes"), 2
        )
        for deadline in ("zg361_comp_ae_due_90_deadline", "zg361_comp_ae_due_180_deadline"):
            self.assertLess(
                stage_two.index("zg361_comp_ae_freeze_due_obligation_effect = yes"),
                stage_two.index(deadline),
            )
        consumer = top_level_block(self.effects, "zg361_comp_ae_consume_due_effect")
        self.assertIn(
            "name = zg361_comp_due_gross value = var:zg361_comp_ae_due_frozen_gross",
            consumer,
        )
        self.assertIn("value = var:zg361_comp_ae_due_frozen_treasury", consumer)
        self.assertIn("value = var:zg361_comp_ae_due_frozen_personal", consumer)
        self.assertNotIn(
            "name = zg361_comp_due_gross value = var:zg361_comp_ae_statement_owed",
            consumer,
        )

    def test_290_nomination_threshold_is_375_and_350_is_a_negative_case(self) -> None:
        source = top_level_block(self.effects, "zg361_comp_m290_consume_effect")
        self.assertEqual(generator.RESULT_GRADE_RATINGS, {1: 325, 2: 350, 3: 375})
        frozen_rating = (
            "set_variable = { name = zg361_comp_m290_rating "
            "value = var:zg361_comp_result_rating }"
        )
        default_ineligible = "set_variable = { name = zg361_comp_m290_eligible value = 0 }"
        eligible = "set_variable = { name = zg361_comp_m290_eligible value = 1 }"
        threshold = (
            "var:zg361_comp_m290_result_grade = 3 "
            "var:zg361_comp_m290_rating = 375"
        )
        for token in (frozen_rating, default_ineligible, threshold, eligible):
            self.assertIn(token, source)
        for field in ("owner", "subject", "cycle", "case", "state", "grade"):
            self.assertIn(
                f"name = zg361_comp_m290_result_{field} "
                f"value = var:zg361_comp_result_{field}",
                source,
            )
        self.assertLess(source.index(frozen_rating), source.index(default_ineligible))
        self.assertLess(source.index(default_ineligible), source.index(threshold))
        self.assertEqual(source.count(eligible), 1)
        self.assertIn("zg361_comp_m290_route = 2", source)
        self.assertIn("zg361_comp_m290_route = 3", source)
        self.assertNotRegex(
            source,
            r"name\s*=\s*zg361_comp_m290_rating\s+value\s*=\s*(?:350|375)",
        )
        eligible_from_frozen_result = lambda grade: (
            grade == 3 and generator.RESULT_GRADE_RATINGS[grade] == 375
        )
        self.assertFalse(
            eligible_from_frozen_result(2),
            "a real frozen 3.50 result must remain ineligible",
        )
        self.assertTrue(eligible_from_frozen_result(3))

    def test_ae_and_af_consume_the_same_frozen_actual_result(self) -> None:
        ae_open = top_level_block(self.effects, "zg361_comp_open_ae_case_effect")
        self.assertIn(
            "name = zg361_comp_ae_frozen_performance_grade "
            "value = var:zg361_comp_result_rating",
            ae_open,
        )
        self.assertNotIn(
            "name = zg361_comp_ae_frozen_performance_grade value = 375",
            ae_open,
        )

        same_rating = {
            285: "name = zg361_comp_m285_frozen_grade value = var:zg361_comp_result_rating",
            289: (
                "name = zg361_comp_m289_frozen_performance_grade "
                "value = var:zg361_comp_ae_frozen_performance_grade"
            ),
            290: "name = zg361_comp_m290_rating value = var:zg361_comp_result_rating",
        }
        for mechanism_id, token in same_rating.items():
            with self.subTest(mechanism_id=mechanism_id):
                source = top_level_block(
                    self.effects, f"zg361_comp_m{mechanism_id:03d}_consume_effect"
                )
                self.assertIn(token, source)

        statement = top_level_block(
            self.effects, "zg361_comp_ae_recalculate_statement_effect"
        )
        self.assertIn("var:zg361_comp_ae_frozen_performance_grade < 375", statement)

        # L's performance-named values are monetary/formula outputs, not a
        # second rating input. They must not smuggle a hard-coded grade/rating.
        for mechanism_id in (82, 83, 91):
            source = top_level_block(
                self.effects, f"zg361_comp_m{mechanism_id:03d}_consume_effect"
            )
            self.assertNotRegex(
                source,
                r"(?:grade|rating)\s+value\s*=\s*(?:350|375)",
            )

    def test_299_good_leaver_does_not_implicitly_accelerate_unvested_service(self) -> None:
        source = top_level_block(self.effects, "zg361_comp_m299_consume_effect")
        self.assertIn(
            "set_variable = { name = zg361_comp_m299_good_leaver_acceleration value = 0 }",
            source,
        )
        self.assertIn(
            "set_variable = { name = zg361_comp_m299_vested_preserved value = var:zg361_comp_af_vested_units }",
            source,
        )
        self.assertIn(
            "name = zg361_comp_af_forfeited_units add = var:zg361_comp_af_unvested_service",
            source,
        )
        self.assertIn(
            "name = zg361_comp_af_forfeited_units add = var:zg361_comp_af_unvested_performance",
            source,
        )
        self.assertIn(
            "set_variable = { name = zg361_comp_af_unvested_service value = 0 }",
            source,
        )
        self.assertIn(
            "set_variable = { name = zg361_comp_af_unvested_performance value = 0 }",
            source,
        )
        self.assertNotRegex(
            source,
            r"name\s*=\s*zg361_comp_af_vested_units\s+add\s*=\s*[^}\n]*unvested",
        )
        self.assertNotRegex(
            source,
            r"zg361_comp_m299_good_leaver_acceleration\s+value\s*=\s*[1-9]",
        )

    def test_ae_has_all_explicit_transitions_and_statement_conservation(self) -> None:
        # payable -> due -> decided -> corrected -> appealed -> closed
        for state, ids in enumerate(
            ((278, 279, 280), (281, 282), (283, 284, 285), (286, 287), (288, 289)),
            start=1,
        ):
            with self.subTest(ae_state=state):
                source = top_level_block(
                    self.effects, f"zg361_comp_ae_try_advance_{state:02d}_effect"
                )
                self.assertIn(f"EXPECTED_STATE = {state}", source)
                for mechanism_id in ids:
                    self.assertIn(
                        f"var:zg361_comp_m{mechanism_id:03d}_consumed = 1", source
                    )
                self.assertEqual(
                    source.count(f"zg361_case_ae_advance_{state:02d}_effect"), 1
                )

        reconciliation = top_level_block(
            self.effects, "zg361_comp_ae_recalculate_statement_effect"
        )
        for mechanism_id in (278, 279, 280):
            self.assertIn(f"var:zg361_comp_m{mechanism_id:03d}_consumed = 1", reconciliation)
        for field, account in (
            ("promised", "payable"),
            ("paid", "paid"),
            ("owed", "owed"),
            ("returned", "returned"),
        ):
            self.assertIn(
                f"name = zg361_comp_m278_{field} value = var:zg361_comp_ae_statement_{account}",
                reconciliation,
            )
        self.assertIn(
            "name = zg361_comp_ae_statement_rhs value = var:zg361_comp_ae_statement_paid",
            reconciliation,
        )
        self.assertIn(
            "name = zg361_comp_ae_statement_rhs add = var:zg361_comp_ae_statement_owed",
            reconciliation,
        )
        self.assertIn(
            "value = 0 subtract = var:zg361_comp_ae_statement_returned",
            reconciliation,
        )
        self.assertIn(
            "var:zg361_comp_ae_statement_rhs = var:zg361_comp_ae_statement_payable",
            reconciliation,
        )
        stage_three = top_level_block(
            self.effects, "zg361_comp_ae_try_advance_03_effect"
        )
        self.assertIn("var:zg361_comp_ae_due_resolved = 1", stage_three)
        self.assertIn("var:zg361_comp_ae_statement_conserved = 1", stage_three)
        stage_five = top_level_block(
            self.effects, "zg361_comp_ae_try_advance_05_effect"
        )
        self.assertIn("var:zg361_comp_ae_appeal_response_recorded = 1", stage_five)
        self.assertIn("var:zg361_comp_ae_statement_conserved = 1", stage_five)
        self.assertIn("zg361_comp_portfolio_case_closed_effect = { DOMAIN = 2 }", stage_five)

    def test_all_cash_receipts_freeze_payers_recipient_approver_and_case_identity(self) -> None:
        self.assertNotIn(
            "government_has_flag = government_has_treasury", self.effects
        )
        self.assertIn("has_treasury = yes", self.effects)
        prefixes = sorted(
            set(
                re.findall(
                    r"name\s*=\s*(zg361_comp_[A-Za-z0-9_]+)_treasury_payer\b",
                    self.effects,
                )
            )
        )
        self.assertGreaterEqual(len(prefixes), 12)
        for prefix in prefixes:
            with self.subTest(receipt=prefix):
                for suffix in (
                    "treasury_payer",
                    "personal_payer",
                    "recipient",
                    "approver",
                    "frozen_owner",
                    "frozen_subject",
                    "frozen_cycle",
                    "frozen_case",
                    "frozen_state",
                ):
                    self.assertRegex(self.effects, rf"name\s*=\s*{re.escape(prefix)}_{suffix}\b")

    def test_300_buyback_is_fifo_atomic_and_70_30_uses_manager_personal_gold(self) -> None:
        for effect_name, prefix in (
            ("zg361_comp_af_pay_buyback_now_effect", "zg361_comp_m300_buyback"),
            ("zg361_comp_af_pay_buyback_later_effect", "zg361_comp_af_buyback_later"),
        ):
            with self.subTest(payment=effect_name):
                source = top_level_block(self.effects, effect_name)
                self.assertIn("AVAILABLE_VAR = zg361_comp_af_treasury_available", source)
                self.assertIn("AVAILABLE_VAR = zg361_comp_af_personal_available", source)
                self.assertIn("AMOUNT = 7", source)
                self.assertIn("AMOUNT = 3", source)
                self.assertIn(f"var:{prefix}_treasury_status = 2", source)
                self.assertIn(f"var:{prefix}_personal_status = 2", source)
                self.assertIn("remove_treasury = 7", source)
                self.assertIn("remove_short_term_gold = 3", source)
                self.assertIn("add_gold = 10", source)
                self.assertLess(
                    source.index(f"var:{prefix}_personal_status = 2"),
                    source.index("remove_treasury = 7"),
                )

        core = top_level_block(self.effects, "zg361_comp_m300_core_effect")
        self.assertEqual(core.count("has_treasury = yes"), 1)
        self.assertNotIn("government_has_flag = government_has_treasury", core)
        self.assertIn("treasury >= 7", core)
        self.assertIn("gold >= 3", core)
        self.assertIn("var:zg361_comp_af_vested_units >= 10", core)
        self.assertIn(
            "var:zg361_comp_af_queue_tail = var:zg361_comp_af_queue_head", core
        )
        consumer = top_level_block(self.effects, "zg361_comp_m300_consume_effect")
        self.assertIn("name = zg361_comp_af_queue_tail add = 1", consumer)
        self.assertIn(
            "name = zg361_comp_af_request_serial value = var:zg361_case_af_owner.var:zg361_comp_af_queue_tail",
            consumer,
        )
        self.assertIn("zg361_comp_af_buyback_90_deadline", consumer)
        delayed = top_level_block(self.effects, "zg361_comp_af_consume_buyback_effect")
        self.assertIn(
            "name = zg361_comp_af_expected_request_serial",
            delayed,
        )
        self.assertIn(
            "var:zg361_comp_af_request_serial = scope:zg361_comp_af_expected_request_serial",
            delayed,
        )
        self.assertIn("treasury >= 7", delayed)
        self.assertIn("gold >= 3", delayed)
        self.assertLess(
            delayed.index("zg361_comp_af_pay_buyback_later_effect = yes"),
            delayed.index("var:zg361_comp_financial_applied = 1"),
        )
        self.assertLess(
            delayed.index("var:zg361_comp_financial_applied = 1"),
            delayed.index("name = zg361_comp_af_vested_units add = -10"),
        )
        self.assertEqual(
            delayed.count("name = zg361_comp_af_vested_units add = -10"), 1
        )
        self.assertEqual(
            delayed.count("name = zg361_comp_af_repurchased_units add = 10"), 1
        )
        self.assertIn("name = zg361_comp_af_buyback_red value = 1", delayed)
        self.assertIn("name = zg361_comp_typed_red value = 4", delayed)
        self.assertIn("name = zg361_comp_af_request_state value = 4", delayed)
        conservation = top_level_block(
            self.effects, "zg361_comp_af_check_conservation_effect"
        )
        for account in (
            "unvested_service",
            "unvested_performance",
            "vested_units",
            "forfeited_units",
            "repurchased_units",
        ):
            self.assertIn(f"var:zg361_comp_af_{account}", conservation)
        self.assertIn(
            "var:zg361_comp_af_unit_accounted = var:zg361_comp_af_total_units",
            conservation,
        )

    def test_every_deadline_schedules_and_expires_with_all_five_identity_fields(self) -> None:
        expected = {
            "l_deferred": ("l", 4, 365, "zg361comp.100"),
            "ae_due_90": ("ae", 3, 90, "zg361comp.210"),
            "ae_due_180": ("ae", 3, 180, "zg361comp.211"),
            "af_vest_30": ("af", 4, 30, "zg361comp.300"),
            "af_vest_90": ("af", 4, 90, "zg361comp.301"),
            "af_vest_180": ("af", 4, 180, "zg361comp.302"),
            "af_vest_365": ("af", 4, 365, "zg361comp.303"),
            "af_vest_730": ("af", 4, 730, "zg361comp.304"),
            "af_buyback_90": ("af", 5, 90, "zg361comp.310"),
        }
        self.assertEqual(generator.DEADLINES, expected)
        for prefix, (domain, state, days, event_id) in expected.items():
            names = generator.deadline_names(prefix)
            with self.subTest(deadline=prefix):
                scheduled = generator.schedule_deadline(prefix)
                for field in FIVE_FIELDS:
                    self.assertIn(f"{field}_VAR = zg361_case_{domain}_", scheduled)
                    self.assertIn(f"TICKET_{field}", scheduled)
                    self.assertIn(
                        f"DEADLINE_{field}_VAR = {names[field.lower()]}", scheduled
                    )
                self.assertIn(f"TICKET_STATE = {state}", scheduled)
                self.assertIn(f"DAYS = {days}", scheduled)
                self.assertIn(f"EVENT = {event_id}", scheduled)
                self.assertIn(f"DEADLINE_OWNER_VAR = {names['owner']}", self.effects)
                event = top_level_block(self.events, event_id)
                self.assertIn("hidden = yes", event)
                self.assertIn("zg361_case_kernel_expire_deadline_effect", event)
                for field in FIVE_FIELDS:
                    self.assertIn(f"{field}_VAR = zg361_case_{domain}_", event)
                    self.assertIn(
                        f"DEADLINE_{field}_VAR = {names[field.lower()]}", event
                    )
                self.assertIn("var:zg361_case_kernel_applied = 1", event)
                self.assertIn(f"stale {prefix} five-field ticket ignored", event)

    def test_portfolio_freezes_only_a_current_delivered_result_for_all_domains(self) -> None:
        snapshot = top_level_block(
            self.effects, "zg361_comp_freeze_current_result_effect"
        )
        opener = top_level_block(
            self.effects, "zg361_comp_portfolio_open_next_effect"
        )
        sources = {
            "owner": "zg361_result_case_owner",
            "cycle": "zg361_result_cycle_serial",
            "case": "zg361_result_case_serial",
            "state": "zg361_result_case_state",
            "grade": "zg361_result_grade",
        }
        for field, source in sources.items():
            with self.subTest(field=field):
                self.assertIn(f"has_variable = {source}", snapshot)
                self.assertIn(f"has_variable = {source}", opener)
                self.assertIn(
                    f"name = zg361_comp_portfolio_result_{field} "
                    f"value = scope:zg361_comp_result_subject_scope.var:{source}",
                    snapshot,
                )
        self.assertIn(
            "name = zg361_comp_portfolio_result_subject "
            "value = scope:zg361_comp_result_subject_scope",
            snapshot,
        )
        self.assertIn("var:zg361_result_case_owner = root", snapshot)
        self.assertIn(
            "var:zg361_result_cycle_serial = root.var:zg361_review_serial", snapshot
        )
        self.assertIn("var:zg361_result_case_state >= 3", snapshot)
        self.assertIn("trigger_else = { always = no }", snapshot)
        for grade, rating in generator.RESULT_GRADE_RATINGS.items():
            with self.subTest(grade=grade):
                self.assertIn(f"var:zg361_result_grade = {grade}", snapshot)
                self.assertIn(
                    f"name = zg361_comp_portfolio_result_rating value = {rating}",
                    snapshot,
                )

        self.assertEqual(opener.count("ordered_vassal = {"), 1)
        self.assertIn("var:zg361_comp_portfolio_domain = 1", opener)
        self.assertIn("NOT = { has_variable = zg361_comp_portfolio_subject }", opener)
        self.assertEqual(opener.count("zg361_comp_freeze_current_result_effect = yes"), 1)
        self.assertIn("var:zg361_result_case_state >= 3", opener)
        self.assertIn(
            "var:zg361_result_cycle_serial = root.var:zg361_review_serial", opener
        )

        portfolio_fields = ("owner", "subject", "cycle", "case", "state", "grade")
        for domain in ("l", "ae", "af"):
            domain_open = top_level_block(
                self.effects, f"zg361_comp_open_{domain}_case_effect"
            )
            self.assertIn("var:zg361_comp_portfolio_result_state >= 3", domain_open)
            self.assertIn(
                "var:zg361_comp_portfolio_result_cycle = var:zg361_review_serial",
                domain_open,
            )
            for field in portfolio_fields:
                with self.subTest(domain=domain, field=field):
                    self.assertIn(
                        f"has_variable = zg361_comp_portfolio_result_{field}",
                        domain_open,
                    )
                    self.assertIn(
                        f"name = zg361_comp_result_{field} "
                        f"value = root.var:zg361_comp_portfolio_result_{field}",
                        domain_open,
                    )
            self.assertIn(
                "name = zg361_comp_result_rating "
                "value = root.var:zg361_comp_portfolio_result_rating",
                domain_open,
            )

        def can_open(
            *, owner_matches: bool, cycle_matches: bool, state: int, grade: int
        ) -> bool:
            return owner_matches and cycle_matches and state >= 3 and grade in {1, 2, 3}

        self.assertTrue(
            can_open(owner_matches=True, cycle_matches=True, state=3, grade=3)
        )
        self.assertFalse(
            can_open(owner_matches=True, cycle_matches=True, state=2, grade=3)
        )
        self.assertFalse(
            can_open(owner_matches=True, cycle_matches=False, state=3, grade=3)
        )
        self.assertFalse(
            can_open(owner_matches=False, cycle_matches=True, state=3, grade=3)
        )

    def test_portfolio_has_one_player_stage_card_and_authorized_ai_is_background(self) -> None:
        opener = top_level_block(
            self.effects, "zg361_comp_portfolio_open_next_effect"
        )
        self.assertIn("has_game_rule = zg361_on", opener)
        self.assertIn("zg361_is_celestial_liege_trigger = yes", opener)
        self.assertIn("has_variable = zg361_review_serial", opener)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", opener)
        self.assertIn("liege = root", opener)
        self.assertIn("order_by = stewardship", opener)
        self.assertIn("position = 0", opener)
        self.assertIn(
            "var:zg361_comp_portfolio_completed_cycle = var:zg361_review_serial",
            opener,
        )
        self.assertIn(
            "name = zg361_comp_portfolio_completed_cycle value = var:zg361_review_serial",
            opener,
        )
        self.assertEqual(
            self.effects.count("add_character_flag = zg361_comp_portfolio_active"), 1
        )
        snapshot = top_level_block(
            self.effects, "zg361_comp_freeze_current_result_effect"
        )
        self.assertIn("name = zg361_comp_portfolio_subject", snapshot)
        self.assertIn("zg361_comp_freeze_current_result_effect = yes", opener)
        self.assertIn("name = zg361_comp_portfolio_domain", opener)

        player_card = top_level_block(self.events, "zg361comp.1")
        self.assertIn("is_ai = no", player_card)
        self.assertNotIn("hidden = yes", player_card)
        self.assertEqual(player_card.count("zg361_comp_portfolio_apply_stage_effect"), 3)
        for route in (1, 2, 3):
            self.assertEqual(player_card.count(f"ROUTE = {route}"), 1)

        ai_card = top_level_block(self.events, "zg361comp.2")
        self.assertIn("hidden = yes", ai_card)
        self.assertIn("is_ai = yes", ai_card)
        self.assertIn("zg361_is_celestial_liege_trigger = yes", ai_card)
        self.assertIn("zg361_comp_portfolio_apply_stage_effect = { ROUTE = 1 }", ai_card)
        self.assertNotIn("title =", ai_card)

        titled_portfolio_cards = []
        for event_name in re.findall(r"(?m)^(zg361comp\.\d+)\s*=\s*\{", self.events):
            source = top_level_block(self.events, event_name)
            if "title =" in source and "zg361_comp_portfolio_apply_stage_effect" in source:
                titled_portfolio_cards.append(event_name)
        self.assertEqual(titled_portfolio_cards, ["zg361comp.1"])

        for mechanism_id in generator.EXPECTED_IDS:
            event_name = f"zg361comp.{mechanism_id}"
            if re.search(rf"(?m)^{re.escape(event_name)}\s*=\s*\{{", self.events):
                source = top_level_block(self.events, event_name)
                self.assertNotIn("_manager_apply_effect", source)
                self.assertNotIn("_core_effect", source)

        subject_appeal = top_level_block(self.events, "zg361comp.289")
        self.assertIn("is_ai = no", subject_appeal)
        self.assertIn("zg361_comp_ae_subject_appeal_response_effect", subject_appeal)
        for forbidden in ("manager_apply", "core_effect", "open_", "advance_"):
            self.assertNotIn(forbidden, subject_appeal)

        notifier = top_level_block(
            self.effects, "zg361_comp_portfolio_notify_owner_effect"
        )
        self.assertIn("save_scope_as = zg361_comp_notify_subject", notifier)
        for domain_number, domain in enumerate(("l", "ae", "af"), start=1):
            self.assertIn(f"scope:zg361_comp_notify_domain = {domain_number}", notifier)
            self.assertIn(f"var:zg361_case_{domain}_owner", notifier)
        self.assertEqual(notifier.count("zg361_comp_portfolio_refresh_effect = yes"), 3)

    def test_player_card_explains_each_stage_and_completion_cards_show_numeric_ledgers(self) -> None:
        player_card = top_level_block(self.events, "zg361comp.1")
        stage_keys = (
            *(f"zg361comp.1.l{state}" for state in range(1, 5)),
            *(f"zg361comp.1.ae{state}" for state in range(1, 6)),
            *(f"zg361comp.1.af{state}" for state in range(1, 6)),
        )
        self.assertIn("first_valid = {", player_card)
        self.assertEqual(player_card.count("triggered_desc = {"), 14)
        for key in stage_keys:
            self.assertIn(f"desc = {key}", player_card)

        english = generator.render_english_localization().decode("utf-8-sig")
        chinese = generator.render_simp_chinese_localization().decode("utf-8-sig")
        for key in stage_keys:
            with self.subTest(localization=key):
                self.assertIn(f" {key}:0 ", english)
                self.assertIn(f" {key}:0 ", chinese)
        for source in (english, chinese):
            for variable in (
                "zg361_comp_bonus_total",
                "zg361_comp_ae_statement_payable",
                "zg361_comp_ae_statement_owed",
                "zg361_comp_m287_visibility_mode",
                "zg361_comp_af_total_units",
                "zg361_comp_m294_current_value",
                "zg361_comp_m294_liquid_value",
                "zg361_comp_m299_leaver_class",
                "zg361_comp_af_repurchased_units",
            ):
                self.assertIn(f"ROOT.MakeScope.Var('{variable}').GetValue", source)
            self.assertNotIn("named_peer_salary", source)

    def test_runtime_claims_only_static_ready_without_live_evidence(self) -> None:
        header = "\n".join(self.effects.splitlines()[:8]).lower()
        self.assertIn("static-ready", header)
        self.assertNotIn("fixture-live", header)
        self.assertNotIn("production-live", header)
        self.assertNotIn("mcp live green", header)


if __name__ == "__main__":
    unittest.main()
