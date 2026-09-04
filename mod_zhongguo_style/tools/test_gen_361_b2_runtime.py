#!/usr/bin/env python3
"""L0 product-wiring contracts for the first B2 CK3 vertical slice.

These tests prove generated Paradox source, hook placement, deterministic
receipts and negative/stale guards.  They do not claim a CK3 live run or raise
the readiness recorded by the phase-two program.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unittest

from gen_361_b2_runtime import (
    CORE_IDS,
    DELEGATED_IDS,
    EFFECT_GROUPS,
    EFFECT_HARD_MAX,
    EFFECT_HARD_LIMIT_EXCEPTIONS,
    EFFECT_TARGET_MAX,
    INTERFACE_IDS,
    LEGACY_EFFECT_FILENAME,
    MOD_ROOT,
    PIP_CASE_TUPLE_FIELDS,
    SEMANTIC_IDS,
    WIRED_IDS,
    outputs,
    render_effects,
)
from zg361_b2_runtime_data import B2_BINDINGS
import gen_zg361_workforce_probation_fact as probation_generator


PLACEHOLDER_LANGUAGES = (
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "spanish",
)


def read(relative: str) -> str:
    return (MOD_ROOT / relative).read_text(encoding="utf-8-sig")


def top_level_block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", text)
    assert match is not None, f"missing block {key}"
    start = match.start()
    opening = text.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(text)):
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
    raise AssertionError(f"unterminated block {key}")


class B2CK3RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effect_parts = {
            filename: read(f"common/scripted_effects/{filename}")
            for filename, _names in EFFECT_GROUPS
        }
        cls.effects = "\n\n".join(cls.effect_parts.values())
        cls.events = read("events/zg361_b2_runtime_events.txt")
        cls.probation_effects = "\n\n".join(
            read(f"common/scripted_effects/{group.filename}")
            for group in probation_generator.EFFECT_GROUPS
        )
        cls.core = read("common/scripted_effects/zg361_effects.txt")
        cls.core_events = read("events/zg361_events.txt")
        cls.interactions = read(
            "common/character_interactions/zg361_interactions.txt"
        )
        cls.loc_en = read("localization/english/zg361_b2_l_english.yml")
        cls.loc_zh = read(
            "localization/simp_chinese/zg361_b2_l_simp_chinese.yml"
        )
        cls.placeholders = {
            language: read(
                f"localization/{language}/zg361_b2_l_{language}.yml"
            )
            for language in PLACEHOLDER_LANGUAGES
        }

    def test_scope_is_exactly_nineteen_ids_with_one_interface(self) -> None:
        expected = (
            tuple(range(14, 18))
            + tuple(range(69, 82))
            + (358, 359)
        )
        self.assertEqual(WIRED_IDS, expected)
        self.assertEqual(len(WIRED_IDS), 19)
        self.assertEqual(INTERFACE_IDS, (69,))
        self.assertEqual(SEMANTIC_IDS, expected)
        self.assertTrue(set(SEMANTIC_IDS).isdisjoint(DELEGATED_IDS))
        self.assertEqual(len(set(WIRED_IDS) - set(INTERFACE_IDS)), 18)
        self.assertNotIn(18, WIRED_IDS)
        selected = {
            row.mechanism_id: row
            for row in B2_BINDINGS
            if row.mechanism_id in WIRED_IDS
        }
        self.assertEqual(set(selected), set(WIRED_IDS))
        for mechanism_id, row in selected.items():
            with self.subTest(mechanism=mechanism_id):
                self.assertTrue(row.hook)
                self.assertTrue(row.meaningful_write)
                self.assertTrue(row.consumer)
                self.assertIn(
                    f"zg361_b2_m{mechanism_id:03d}_state", self.effects
                )
                self.assertIn(
                    f"zg361_b2_m{mechanism_id:03d}_receipt_serial",
                    self.effects,
                )

    def test_generator_is_current_deterministic_bom_and_independent(self) -> None:
        rendered = outputs()
        self.assertEqual(len(rendered), 35)
        effects_dir = MOD_ROOT / "common" / "scripted_effects"
        self.assertEqual(
            {
                path.name
                for path in rendered
                if path.parent == effects_dir
            },
            {filename for filename, _names in EFFECT_GROUPS},
        )
        self.assertNotIn(effects_dir / LEGACY_EFFECT_FILENAME, rendered)
        for path, payload in rendered.items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), payload)
                self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
                if path.suffix in {".txt", ".yml"} and path.suffix == ".txt":
                    self.assertIn(
                        b"# GENERATED FILE \xe2\x80\x94 edit tools/gen_361_b2_runtime.py",
                        payload,
                    )
        # B2 remains independent except for #359's deliberately narrow reuse
        # of the canonical PP-U nomination transaction.  No other B2 path may
        # open, advance, settle, or refund a shared-kernel case.
        m359_refund = top_level_block(
            self.effects, "zg361_b2_m359_return_pp_nomination_slot_effect"
        )
        m359_open = top_level_block(
            self.effects, "zg361_b2_m359_open_quota_return_effect"
        )
        self.assertIn(
            "zg361_case_kernel_refund_transaction_effect = {", m359_refund
        )
        self.assertNotIn(
            "zg361_case_kernel",
            self.effects.replace(m359_refund, "").replace(m359_open, "")
            + self.events,
        )

    def test_effects_are_complete_byte_identical_purpose_shards(self) -> None:
        self.assertEqual(len(EFFECT_GROUPS), 25)
        self.assertEqual(EFFECT_HARD_LIMIT_EXCEPTIONS, {})
        self.assertFalse(
            (
                MOD_ROOT
                / "common"
                / "scripted_effects"
                / LEGACY_EFFECT_FILENAME
            ).exists()
        )

        historical_bytes = render_effects()
        self.assertEqual(len(historical_bytes), 261_337)
        self.assertEqual(
            hashlib.sha256(historical_bytes).hexdigest(),
            "f23fff74fd8f45eae9be9c446db71532ef4578d46ffeb602087310222810f8b9",
        )
        historical = historical_bytes.decode("utf-8-sig")
        historical_names = re.findall(
            r"(?m)^(zg361_b2_[a-z0-9_]+_effect)\s*=\s*\{",
            historical,
        )
        configured_names = [
            name for _filename, names in EFFECT_GROUPS for name in names
        ]
        self.assertEqual(len(historical_names), 152)
        self.assertEqual(len(set(historical_names)), 152)
        self.assertEqual(len(configured_names), 152)
        self.assertEqual(len(set(configured_names)), 152)
        self.assertEqual(set(configured_names), set(historical_names))

        for filename, expected_names in EFFECT_GROUPS:
            with self.subTest(filename=filename):
                self.assertGreaterEqual(len(expected_names), 1)
                self.assertLessEqual(len(expected_names), EFFECT_TARGET_MAX)
                self.assertLessEqual(len(expected_names), EFFECT_HARD_MAX)
                part = self.effect_parts[filename]
                actual_names = re.findall(
                    r"(?m)^(zg361_b2_[a-z0-9_]+_effect)\s*=\s*\{",
                    part,
                )
                self.assertEqual(actual_names, list(expected_names))
                for name in expected_names:
                    self.assertEqual(
                        top_level_block(part, name),
                        top_level_block(historical, name),
                    )

    def test_all_scheduled_events_exist_once_and_braces_close(self) -> None:
        definition_list = re.findall(
            r"(?m)^zg361b2\.(\d+)\s*=\s*\{", self.events
        )
        definitions = set(definition_list)
        self.assertEqual(len(definition_list), len(definitions))
        references = set(
            re.findall(
                r"trigger_event\s*=\s*\{\s*id\s*=\s*zg361b2\.(\d+)",
                self.effects + self.events,
            )
        )
        self.assertTrue(references)
        self.assertEqual(references - definitions, set())
        for event_id in definitions:
            top_level_block(self.events, f"zg361b2.{event_id}")
        for effect_name in re.findall(
            r"(?m)^(zg361_b2_[a-z0-9_]+_effect)\s*=\s*\{", self.effects
        ):
            top_level_block(self.effects, effect_name)

    def test_every_native_id_has_open_c_debt_and_terminal_consumer_paths(self) -> None:
        combined = self.effects + self.events
        for mechanism_id in WIRED_IDS:
            key = f"{mechanism_id:03d}"
            with self.subTest(mechanism=mechanism_id):
                self.assertIn(
                    f"zg361_b2_m{key}_open_business_object_effect = yes", combined
                )
                self.assertIn(
                    f"zg361_b2_m{key}_post_policy_debt_effect = yes", combined
                )
                self.assertIn(
                    f"zg361_b2_m{key}_consume_business_object_effect = yes",
                    combined,
                )
        for event_id, mechanism_id in (
            (61, 75),
            (120, 70),
            (121, 72),
            (141, 71),
            (171, 74),
        ):
            block = top_level_block(self.events, f"zg361b2.{event_id}")
            self.assertIn(
                f"zg361_b2_m{mechanism_id:03d}_consume_business_object_effect = yes",
                block,
            )

    def test_visible_events_are_player_only_and_localized_in_nine_files(self) -> None:
        visible = {
            40: ("t", "desc", "a", "b", "c"),
            50: ("t", "desc", "a", "b", "c"),
            60: ("t", "desc", "a", "b"),
            110: ("t", "desc", "a", "b", "c", "d"),
            130: ("t", "desc", "a", "b", "c"),
            131: ("t", "desc", "a", "b", "c"),
            160: ("t", "desc", "a", "b", "c"),
        }
        for event_id in visible:
            block = top_level_block(self.events, f"zg361b2.{event_id}")
            self.assertIn("is_ai = no", block)
        self.assertIn(
            "zg361_is_celestial_liege_trigger = yes",
            top_level_block(self.events, "zg361b2.130"),
        )
        localizations = [self.loc_en, self.loc_zh, *self.placeholders.values()]
        for localization in localizations:
            for event_id, suffixes in visible.items():
                for suffix in suffixes:
                    with self.subTest(event=event_id, suffix=suffix):
                        self.assertEqual(
                            localization.count(
                                f"zg361b2.{event_id}.{suffix}:0"
                            ),
                            1,
                        )
        english_body = self.loc_en.splitlines()[1:]
        for language, localization in self.placeholders.items():
            with self.subTest(placeholder=language):
                self.assertEqual(localization.splitlines()[1:], english_body)
        self.assertNotEqual(self.loc_zh.splitlines()[1:], english_body)

    def test_every_delayed_ticket_has_owner_subject_cycle_case_state_and_stale_noop(self) -> None:
        delayed = {
            61: "exit_deadline",
            100: "pip_deadline",
            120: "retaliation_deadline",
            121: "leak_deadline",
            132: "redelivery_witness",
            140: "skip_deadline",
            141: "factcheck",
            150: "metric_deadline",
            161: "separate_witness",
            162: "separate_deadline",
            171: "redundancy_audit",
        }
        for event_id, prefix in delayed.items():
            block = top_level_block(self.events, f"zg361b2.{event_id}")
            with self.subTest(event=event_id):
                for field in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"zg361_b2_{prefix}_{field}", block)
                self.assertIn("stale", block)
                self.assertIn("else = {", block)
        self.assertIn("id = zg361b2.132 days = 7", self.events)
        self.assertIn("id = zg361b2.161 days = 7", self.events)
        self.assertIn("id = zg361b2.150 days = 90", self.effects)
        self.assertIn("id = zg361b2.162 days = 90", self.effects)
        self.assertIn("id = zg361b2.120 days = 365", self.effects)
        self.assertIn("id = zg361b2.141 days = 30", self.effects)
        self.assertIn("id = zg361b2.171 days = 30", self.effects)

    def test_core_delivery_appeal_refund_and_statement_hooks_are_real(self) -> None:
        freeze = top_level_block(self.core, "zg361_freeze_result_case_effect")
        settle = top_level_block(self.core, "zg361_settle_delivered_325_effect")
        regrade = top_level_block(
            self.core, "zg361_apply_receipted_appeal_regrade_effect"
        )
        self.assertIn("zg361_b2_on_result_frozen_effect = yes", freeze)
        self.assertIn("zg361_b2_on_notice_delivered_effect = yes", settle)
        self.assertLess(
            settle.index("zg361_result_settlement_posted_serial"),
            settle.index("zg361_b2_on_notice_delivered_effect = yes"),
        )
        self.assertIn("zg361_b2_on_appeal_corrected_effect = yes", regrade)
        for resource in ("treasury", "gold", "merit"):
            self.assertIn(f"zg361_result_{resource}_paid", regrade)
            self.assertIn(f"zg361_result_{resource}_refunded", regrade)
        self.assertIn(
            "var:zg361_result_refund_posted_serial = 0",
            top_level_block(self.core, "zg361_appeal_regrade_to_35_effect"),
        )
        appeal = top_level_block(self.core_events, "zg361.4")
        deadline = top_level_block(self.core_events, "zg361.52")
        statement = top_level_block(self.core_events, "zg361.53")
        self.assertIn("zg361_b2_on_appeal_filed_effect = yes", appeal)
        self.assertIn("zg361_b2_on_appeal_upheld_effect = yes", appeal)
        self.assertIn("zg361_b2_on_appeal_expired_effect = yes", deadline)
        self.assertIn("zg361b2.statement.corrected", statement)
        interaction = top_level_block(
            self.interactions, "zg361_appeal_interaction"
        )
        self.assertIn("is_ai = no", interaction)
        self.assertIn("zg361_b2_on_appeal_filed_effect = yes", interaction)
        self.assertIn("zg361_b2_on_appeal_upheld_effect = yes", interaction)

    def test_069_pre_settlement_abi_is_frozen_and_shared_hook_precedes_writes(self) -> None:
        gate = top_level_block(
            self.effects, "zg361_b2_pre_notice_settlement_gate_effect"
        )
        for field in (
            "zg361_b2_case_owner",
            "zg361_b2_case_subject",
            "zg361_b2_case_cycle",
            "zg361_b2_case_serial",
            "zg361_b2_notice_state",
        ):
            self.assertIn(field, gate)
        self.assertIn("zg361_b2_m069_settlement_allowed value = 0", gate)
        self.assertIn("zg361_b2_m069_settlement_allowed value = 1", gate)
        self.assertIn("var:zg361_b2_m069_route = 3", gate)
        self.assertIn("zg361_b2_m069_post_policy_debt_effect = yes", gate)
        for forbidden in (
            "remove_treasury",
            "remove_gold",
            "remove_merit",
            "add_character_modifier = zg361_salary_cut",
        ):
            self.assertNotIn(forbidden, gate)

        settle = top_level_block(self.core, "zg361_settle_delivered_325_effect")
        hook = "zg361_b2_pre_notice_settlement_gate_effect = yes"
        self.assertIn(hook, settle)
        self.assertIn("var:zg361_b2_m069_settlement_allowed = 1", settle)
        first_business_write = min(
            settle.index(token)
            for token in (
                "add_character_modifier = { modifier = zg361_grade_325",
                "zg361_result_salary_cut_active value = 1",
                "remove_treasury = zg361_perf_treasury_penalty_value",
                "remove_short_term_gold = zg361_perf_gold_penalty_value",
                "change_merit = medium_merit_loss",
            )
        )
        self.assertLess(settle.index(hook), first_business_write)
        self.assertIn("zg361_b2_on_notice_delivered_effect = yes", settle)

    def test_016_support_is_atomic_real_and_conserved(self) -> None:
        support = top_level_block(
            self.effects, "zg361_b2_m016_commit_support_effect"
        )
        for required in (
            "zg361_b2_support_mentor",
            "zg361_b2_pip_capacity_used < 2",
            "treasury >= 25",
            "remove_treasury = 25",
            "zg361_b2_pip_support_budget_allocated value = 25",
            "zg361_b2_pip_support_budget_spent value = 25",
            "zg361_b2_pip_support_hours value = 12",
            "zg361_b2_pip_support_attention value = 1",
        ):
            self.assertIn(required, support)
        self.assertLess(support.index("treasury >= 25"), support.index("remove_treasury = 25"))
        self.assertEqual(support.count("remove_treasury = 25"), 1)
        self.assertNotIn("add_gold", support)
        release = top_level_block(
            self.effects, "zg361_b2_release_pip_support_effect"
        )
        self.assertIn("zg361_b2_pip_capacity_used add = -1", release)
        self.assertIn("zg361_b2_pip_support_reserved value = 0", release)

    def test_017_first_low_cannot_skip_directly_to_adverse_disposition(self) -> None:
        opened = top_level_block(
            self.effects, "zg361_b2_m017_open_disposition_effect"
        )
        self.assertIn("zg361_b2_m017_first_low_restricted value = 1", opened)
        self.assertIn("zg361_b2_m017_expedited_evidence", opened)
        event = top_level_block(self.events, "zg361b2.110")
        self.assertGreaterEqual(
            event.count("zg361_b2_m017_first_low_restricted = 0"), 3
        )
        self.assertIn("var:zg361_streak_bottom >= 2", event)
        self.assertIn("var:zg361_streak_bottom >= 3", event)
        self.assertIn("zg361_b2_m017_disposition_receipt", event)

    def test_075_route_c_cannot_open_a_ghost_exit_offer(self) -> None:
        escalation = top_level_block(
            self.effects, "zg361_b2_m071_open_escalation_effect"
        )
        self.assertIn("zg361_b2_m075_open_exit_offer_effect = yes", escalation)
        self.assertIn("var:zg361_b2_m075_object_active = 1", escalation)
        self.assertLess(
            escalation.index("var:zg361_b2_m075_object_active = 1"),
            escalation.index("trigger_event = { id = zg361b2.60 days = 2 }"),
        )
        offer = top_level_block(self.events, "zg361b2.60")
        self.assertIn("var:zg361_b2_m075_object_active = 1", offer)
        self.assertIn("var:zg361_b2_m075_state = 1", offer)

    def test_075_funded_option_starts_canonical_normal_exit_before_accept(self) -> None:
        offer = top_level_block(self.events, "zg361b2.60")
        accept = top_level_block(
            self.effects, "zg361_b2_m075_accept_exit_offer_effect"
        )
        self.assertIn(
            "zg361_workforce_normal_exit_fact_begin_from_m075_offer_effect = yes",
            offer,
        )
        self.assertNotIn("zg361_b2_m075_accept_exit_offer_effect = yes", offer)
        self.assertIn("force_step_down_landed_titles = yes", accept)

    def test_077_rotation_has_real_conflict_recusal_and_history_consumer(self) -> None:
        assign = top_level_block(
            self.effects, "zg361_b2_m077_assign_reviewer_effect"
        )
        for required in (
            "ordered_vassal",
            "NOT = { this = scope:zg361_b2_review_owner }",
            "NOT = { this = scope:zg361_b2_review_subject }",
            "has_relation_friend",
            "has_relation_lover",
            "has_relation_rival",
            "zg361_b2_m077_subject_recusal_effect = yes",
            "zg361_b2_m077_owner_recusal_effect = yes",
        ):
            self.assertIn(required, assign)
        subject_recusal = top_level_block(
            self.effects, "zg361_b2_m077_subject_recusal_effect"
        )
        owner_recusal = top_level_block(
            self.effects, "zg361_b2_m077_owner_recusal_effect"
        )
        for block, token in (
            (subject_recusal, "recusal_subject_used"),
            (owner_recusal, "recusal_owner_used"),
        ):
            self.assertIn(f"zg361_b2_m077_{token} = 0", block)
            self.assertIn(f"zg361_b2_m077_{token} value = 1", block)
            self.assertIn("zg361_b2_m077_pick_replacement_effect = yes", block)
        corrected = top_level_block(
            self.effects, "zg361_b2_on_appeal_corrected_effect"
        )
        upheld = top_level_block(
            self.effects, "zg361_b2_on_appeal_upheld_effect"
        )
        for block in (corrected, upheld):
            self.assertIn("zg361_b2_m077_conclusion_receipt", block)
            self.assertIn("zg361_b2_reviewer_last_case", block)

    def test_write_only_b2_aggregate_ledgers_are_retired(self) -> None:
        combined = self.effects + self.events
        for dead_ledger in (
            "zg361_b2_m072_denied_reads",
            "zg361_b2_m077_reviewer_revision",
            "zg361_b2_quota_reserve",
            "zg361_b2_reviewer_case_n",
        ):
            self.assertNotIn(dead_ledger, combined)

    def test_078_uses_full_cohort_dimensions_and_never_auto_grades(self) -> None:
        baseline = top_level_block(
            self.effects, "zg361_b2_m078_record_cohort_sample_effect"
        )
        outcome = top_level_block(
            self.effects, "zg361_b2_m078_apply_resolved_sample_effect"
        )
        self.assertIn("var:zg361_b2_m078_route != 3", baseline)
        self.assertIn("zg361_b2_fairness_total_n add = 1", baseline)
        for dimension in (
            "newcomer",
            "transfer",
            "kin",
            "faction",
            "landed",
            "governor",
        ):
            self.assertIn(f"zg361_b2_fairness_{dimension}_n", baseline)
            self.assertIn(f"zg361_b2_fairness_{dimension}_corrected_n", outcome)
            self.assertIn(f"zg361_b2_fairness_{dimension}_rate_cross", outcome)
        self.assertIn("zg361_b2_fairness_small_sample value = 1", outcome)
        self.assertIn("zg361_b2_fairness_explanation_task", outcome)
        combined = baseline + outcome
        for forbidden in (
            "zg361_result_grade value",
            "zg361_last_grade value",
            "add_character_modifier = zg361_grade_",
            "zg361_appeal_regrade_to_35_effect",
        ):
            self.assertNotIn(forbidden, combined)

    def test_079_skip_level_remands_but_never_writes_the_grade(self) -> None:
        opened = top_level_block(
            self.effects, "zg361_b2_m079_open_skip_level_effect"
        )
        self.assertIn("zg361_b2_m079_open_business_object_effect = yes", opened)
        self.assertIn("var:zg361_b2_m079_object_active = 1", opened)
        closed = top_level_block(self.events, "zg361b2.140")
        for required in (
            "zg361_b2_m079_manager_rework_required",
            "zg361_b2_m079_remand_active",
            "zg361_b2_m079_no_direct_grade_write",
            "zg361_b2_m079_outcome_receipt",
            "zg361_b2_m079_consume_business_object_effect = yes",
        ):
            self.assertIn(required, closed)
        for forbidden in (
            "zg361_appeal_regrade_to_35_effect",
            "zg361_result_grade value",
            "zg361_last_grade value",
        ):
            self.assertNotIn(forbidden, closed)
        frozen = top_level_block(self.effects, "zg361_b2_on_result_frozen_effect")
        self.assertIn("zg361_b2_m079_remand_consumer_case", frozen)
        self.assertIn("zg361_b2_m079_manager_rework_completed", frozen)

    def test_080_defect_ticket_is_unique_routed_and_consumed_later(self) -> None:
        opened = top_level_block(
            self.effects, "zg361_b2_m080_open_metric_defect_effect"
        )
        self.assertIn("zg361_b2_m080_open_business_object_effect = yes", opened)
        self.assertIn("var:zg361_b2_m080_object_active = 1", opened)
        for field in (
            "zg361_b2_m080_defect_id",
            "zg361_b2_m080_defect_type",
            "zg361_b2_m080_evidence_hash",
            "zg361_b2_m080_evidence_preserved",
        ):
            self.assertIn(field, opened)
        closed = top_level_block(self.events, "zg361b2.150")
        for required in (
            "var:zg361_b2_m080_route = 2",
            "zg361_b2_m080_suppressed",
            "zg361_b2_m080_metric_repaired",
            "zg361_b2_m080_accepted_risk",
            "zg361_b2_m080_outcome_receipt",
            "zg361_b2_m080_consume_business_object_effect = yes",
        ):
            self.assertIn(required, closed)
        frozen = top_level_block(self.effects, "zg361_b2_on_result_frozen_effect")
        self.assertIn("zg361_b2_m080_consumer_case", frozen)
        self.assertIn("zg361_b2_m080_repeated_after_suppression", frozen)

    def test_359_policy_route_and_fresh_redelivery_identity_are_conserved(self) -> None:
        opened = top_level_block(
            self.effects, "zg361_b2_m359_open_quota_return_effect"
        )
        self.assertIn("var:zg361_b2_m359_object_active = 1", opened)
        self.assertIn("var:zg361_b2_m359_route = 1", opened)
        self.assertIn("var:zg361_b2_m359_route = 2", opened)
        self.assertIn("zg361_b2_m359_hidden_rebalance", opened)
        self.assertNotIn("var:zg361_b2_m359_route = 3", opened)
        manager_event = top_level_block(self.events, "zg361b2.130")
        self.assertIn("var:zg361_b2_m359_object_active = 1", manager_event)
        self.assertIn("var:zg361_b2_m359_route = 1", manager_event)
        for required in (
            "has_variable = zg361_pp_m157_nomination_slot_owner",
            "has_variable = zg361_pp_m157_nomination_slot_cycle",
            "has_variable = zg361_pp_m157_nomination_slot_case",
            "has_variable = zg361_pp_m157_nomination_slot_amount",
            "has_variable = zg361_pp_m157_nomination_slot_status",
            "var:zg361_case_u_active = 1",
            "var:zg361_pp_m157_packet_candidate = this",
            "var:zg361_pp_m157_nomination_slot_owner = var:zg361_case_u_owner",
            "var:zg361_pp_m157_nomination_slot_cycle = var:zg361_case_u_cycle_serial",
            "var:zg361_pp_m157_nomination_slot_case = var:zg361_case_u_case_serial",
            "var:zg361_pp_m157_nomination_slot_amount = 1",
            "var:zg361_pp_m157_nomination_slot_status = 1",
            "var:zg361_pp_m157_nomination_slot_status = 2",
            "zg361_b2_m359_return_pp_nomination_slot_effect = yes",
            "NOT = { var:zg361_b2_m359_refund_applied = 1 }",
            "zg361_b2_m359_post_next_cycle_debt_effect = yes",
        ):
            self.assertIn(required, manager_event)

        refund = top_level_block(
            self.effects, "zg361_b2_m359_return_pp_nomination_slot_effect"
        )
        for required in (
            "var:zg361_b2_case_subject = this",
            "var:zg361_b2_m359_route = 1",
            "var:zg361_b2_m359_object_owner = var:zg361_b2_case_owner",
            "var:zg361_b2_m359_object_subject = this",
            "var:zg361_b2_m359_object_cycle = var:zg361_b2_case_cycle",
            "var:zg361_b2_m359_object_receipt_case = var:zg361_b2_case_serial",
            "var:zg361_case_u_owner = var:zg361_b2_case_owner",
            "var:zg361_case_u_subject = this",
            "var:zg361_case_u_cycle_serial = var:zg361_b2_case_cycle",
            "var:zg361_pp_m157_nomination_slot_owner = var:zg361_case_u_owner",
            "var:zg361_pp_m157_nomination_slot_cycle = var:zg361_case_u_cycle_serial",
            "var:zg361_pp_m157_nomination_slot_case = var:zg361_case_u_case_serial",
            "var:zg361_pp_m157_nomination_slot_amount = 1",
            "zg361_case_kernel_refund_transaction_effect = {",
            "AVAILABLE_VAR = zg361_pp_u_nomination_slot_available",
            "RESERVED_VAR = zg361_pp_u_nomination_slot_reserved",
            "SETTLED_VAR = zg361_pp_u_nomination_slot_settled",
            "RECEIPT_AMOUNT_VAR = zg361_pp_m157_nomination_slot_amount",
            "RECEIPT_STATUS_VAR = zg361_pp_m157_nomination_slot_status",
            "var:zg361_case_kernel_applied = 1",
            "zg361_b2_m359_refund_applied value = 0",
            "zg361_b2_m359_refund_applied value = 1",
            "zg361_b2_m359_pp_nomination_status_before",
            "zg361_b2_m359_pp_nomination_status_after",
            "zg361_b2_m359_reserved_consumed value = 1",
        ):
            self.assertIn(required, refund)
        self.assertNotIn("zg361_b2_quota_reserve", refund)
        self.assertNotIn("zg361_b2_m359_consume_reserve_effect", self.effects)
        redelivery = top_level_block(
            self.effects, "zg361_b2_apply_boundary_redelivery_effect"
        )
        self.assertIn(
            "zg361_result_case_serial value = var:zg361_b2_redelivery_case",
            redelivery,
        )
        self.assertIn("zg361_b2_redelivery_original_result_case", redelivery)
        self.assertLess(
            redelivery.index("zg361_result_case_serial value = var:zg361_b2_redelivery_case"),
            redelivery.index("zg361_b2_on_result_frozen_effect = yes"),
        )

    def test_358_359_external_receipts_are_minted_only_by_real_consumers(self) -> None:
        for mechanism_id in (358, 359):
            key = f"{mechanism_id:03d}"
            consumer = top_level_block(
                self.effects,
                f"zg361_b2_m{key}_consume_business_object_effect",
            )
            receipt = (
                f"zg361_b2_m{key}_consumer_receipt_case value = "
                "var:zg361_b2_case_serial"
            )
            publisher = f"zg361_b2_m{key}_publish_workforce_receipt_effect = yes"
            self.assertIn(receipt, consumer)
            self.assertIn(publisher, consumer)
            self.assertLess(consumer.index(receipt), consumer.index(publisher))

        appeal = top_level_block(
            self.effects, "zg361_b2_m358_publish_workforce_receipt_effect"
        )
        for required in (
            "var:zg361_b2_m358_object_consumed = 1",
            "var:zg361_b2_m358_state = 3",
            "var:zg361_b2_m358_route != 3",
            "var:zg361_result_case_state = 4",
            "var:zg361_result_appeal_outcome = 2",
            "var:zg361_result_case_state = 5",
            "var:zg361_result_appeal_outcome = 1",
            "var:zg361_result_refund_posted_serial = var:zg361_result_case_serial",
            "zg361_b2_m358_external_receipt_id",
            "zg361_b2_m358_external_receipt_hash",
        ):
            self.assertIn(required, appeal)

        reflow = top_level_block(
            self.effects, "zg361_b2_m359_publish_workforce_receipt_effect"
        )
        for required in (
            "var:zg361_b2_m359_object_consumed = 1",
            "var:zg361_b2_m359_route != 3",
            "var:zg361_result_case_state = 5",
            "var:zg361_result_appeal_outcome = 1",
            "has_variable = zg361_b2_m359_reserved_consumed",
            "var:zg361_b2_m359_return_route = 1",
            "var:zg361_b2_m359_pp_nomination_owner = var:zg361_b2_case_owner",
            "var:zg361_b2_m359_pp_nomination_cycle = var:zg361_b2_case_cycle",
            "var:zg361_b2_m359_pp_nomination_amount = 1",
            "var:zg361_b2_m359_pp_nomination_status_before = 1",
            "var:zg361_b2_m359_pp_nomination_status_before = 2",
            "var:zg361_b2_m359_pp_nomination_status_after = 3",
            "has_variable = zg361_b2_m359_redelivery_receipt",
            "var:zg361_b2_m359_return_route = 2",
            "has_variable = zg361_b2_m359_debt_added",
            "var:zg361_b2_m359_return_route = 3",
            "zg361_b2_m359_external_receipt_id",
            "zg361_b2_m359_external_receipt_hash",
        ):
            self.assertIn(required, reflow)

    def test_277_publishes_only_a_real_terminal_pip_settlement_tuple(self) -> None:
        producer = top_level_block(
            self.effects, "zg361_b2_publish_workforce_pip_settlement_effect"
        )
        for source in (
            "zg361_b2_pip_owner",
            "zg361_b2_pip_subject",
            "zg361_b2_pip_cycle",
            "zg361_b2_pip_case",
            "zg361_b2_pip_state",
            "zg361_b2_pip_settlement_receipt",
            "zg361_b2_pip_outcome_code",
            "zg361_b2_pip_outcome_result_cycle",
            "zg361_b2_pip_outcome_result_case",
        ):
            self.assertIn(f"has_variable = {source}", producer)
        for terminal_state in (3, 4):
            self.assertIn(
                f"var:zg361_b2_pip_state = {terminal_state}", producer
            )
        self.assertIn(
            "var:zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case",
            producer,
        )
        for field in (
            "pending",
            "consumed",
            "owner",
            "subject",
            "cycle",
            "case",
            "state",
            "case_id",
            "case_hash",
            "closure_receipt_id",
            "closure_receipt_hash",
        ):
            self.assertIn(f"zg361_b2_workforce_pip_{field}", producer)
        self.assertIn("zg361_b2_workforce_pip_pending value = 1", producer)
        self.assertIn("zg361_b2_workforce_pip_consumed value = 0", producer)
        self.assertIn(
            "value = var:zg361_b2_pip_case multiply = 1000 add = 15",
            producer,
        )
        self.assertIn(
            "value = var:zg361_b2_pip_settlement_receipt multiply = 1000 add = 17",
            producer,
        )
        for guard in (
            "var:zg361_b2_pip_cycle > 0",
            "var:zg361_b2_pip_policy_route = 1",
            "var:zg361_b2_pip_policy_route = 2",
            "var:zg361_b2_pip_task_kind > 0",
            "var:zg361_b2_pip_outcome_code = 1",
            "var:zg361_b2_pip_outcome_code = 2",
            "var:zg361_b2_pip_outcome_result_cycle > 0",
            "var:zg361_b2_pip_outcome_result_case > 0",
        ):
            self.assertIn(guard, producer)
        for hash_component in (
            "value = var:zg361_b2_pip_outcome_result_case multiply = 100000",
            "value = var:zg361_b2_pip_outcome_result_cycle multiply = 1000",
            "value = var:zg361_b2_pip_outcome_code multiply = 100",
            "value = var:zg361_b2_pip_state multiply = 10",
            "add = 17",
        ):
            self.assertIn(hash_component, producer)
        self.assertNotIn(
            "value = var:zg361_b2_workforce_pip_case_hash",
            producer,
        )
        self.assertGreaterEqual(
            producer.count("value = var:zg361_b2_pip_case"),
            2,
        )
        self.assertNotIn("zg361_we_", producer)
        for forbidden in (
            "zg361_eliminate_",
            "change_court_position",
            "remove_court_position",
            "headcount",
        ):
            self.assertNotIn(forbidden, producer)

        # The B2 source writer must not read the source it just wrote.  CK3's
        # same-effect read visibility is not a usable sequencing boundary.
        self.assertIn("trigger_event = { id = zg361b2.103 days = 1 }", producer)
        for ticket in (
            "save_scope_as = zg361_b2_probation_handoff_owner",
            "save_scope_as = zg361_b2_probation_handoff_subject",
            "name = zg361_b2_probation_handoff_cycle",
            "name = zg361_b2_probation_handoff_case",
        ):
            self.assertIn(ticket, producer)
        self.assertNotIn(
            "zg361_workforce_probation_fact_publish_from_pip_settlement_effect",
            producer,
        )
        self.assertNotIn(
            "zg361_b2_replay_workforce_probation_fact_handoff_effect = yes",
            producer,
        )

        settlement = top_level_block(
            self.effects, "zg361_b2_settle_pip_outcome_effect"
        )
        self.assertNotIn(
            "zg361_b2_publish_workforce_pip_settlement_effect = yes",
            settlement,
        )
        self.assertLess(
            settlement.index(
                "zg361_b2_pip_settlement_receipt value = var:zg361_b2_pip_case"
            ),
            settlement.index("trigger_event = { id = zg361b2.102 days = 1 }"),
        )
        for ticket in (
            "save_scope_as = zg361_b2_source_publish_owner",
            "save_scope_as = zg361_b2_source_publish_subject",
            "name = zg361_b2_source_publish_cycle",
            "name = zg361_b2_source_publish_case",
        ):
            self.assertIn(ticket, settlement)

        source_event = top_level_block(self.events, "zg361b2.102")
        self.assertEqual(
            source_event.count(
                "zg361_b2_publish_workforce_pip_settlement_effect = yes"
            ),
            1,
        )
        for suffix in ("owner", "subject", "cycle", "case"):
            self.assertIn(f"zg361_b2_source_publish_{suffix}", source_event)
        self.assertIn("stale Workforce source publication ticket ignored", source_event)

    def test_probation_pip_handoff_has_committed_first_read_and_bounded_replay(self) -> None:
        handoff = top_level_block(
            self.effects,
            "zg361_b2_replay_workforce_probation_fact_handoff_effect",
        )
        for source in (
            "zg361_b2_pip_owner",
            "zg361_b2_pip_subject",
            "zg361_b2_pip_cycle",
            "zg361_b2_pip_case",
            "zg361_b2_pip_state",
            "zg361_b2_pip_policy_route",
            "zg361_b2_pip_task_kind",
            "zg361_b2_pip_settlement_receipt",
            "zg361_b2_pip_outcome_code",
            "zg361_b2_pip_outcome_result_cycle",
            "zg361_b2_pip_outcome_result_case",
            "zg361_b2_pip_outcome_result_grade",
        ):
            self.assertIn(f"has_variable = {source}", handoff)
        for source in (
            "pending",
            "consumed",
            "owner",
            "subject",
            "cycle",
            "case",
            "state",
            "case_id",
            "case_hash",
            "closure_receipt_id",
            "closure_receipt_hash",
        ):
            self.assertIn(f"has_variable = zg361_b2_workforce_pip_{source}", handoff)
        for exact in (
            "var:zg361_b2_workforce_pip_pending = 1",
            "var:zg361_b2_workforce_pip_consumed = 0",
            "var:zg361_b2_workforce_pip_owner = var:zg361_b2_pip_owner",
            "var:zg361_b2_workforce_pip_subject = this",
            "var:zg361_b2_workforce_pip_cycle = var:zg361_b2_pip_cycle",
            "var:zg361_b2_workforce_pip_case = var:zg361_b2_pip_case",
            "var:zg361_b2_workforce_pip_state = var:zg361_b2_pip_state",
            "var:zg361_workforce_probation_fact_owner = var:zg361_b2_pip_owner",
            "var:zg361_workforce_probation_fact_subject = this",
            "var:zg361_workforce_probation_fact_state = 2",
            "var:zg361_workforce_probation_fact_awaiting_pip = 1",
            "var:zg361_workforce_probation_fact_source_result_cycle = var:zg361_b2_pip_cycle",
            "var:zg361_workforce_probation_fact_state >= 3",
            "var:zg361_workforce_probation_fact_source_kind = 2",
            "var:zg361_workforce_probation_fact_source_pip_policy_route = var:zg361_b2_pip_policy_route",
            "var:zg361_workforce_probation_fact_source_pip_task_kind = var:zg361_b2_pip_task_kind",
        ):
            self.assertIn(exact, handoff)
        self.assertEqual(
            handoff.count(
                "zg361_workforce_probation_fact_publish_from_pip_settlement_effect = {"
            ),
            1,
        )
        self.assertIn("OWNER = var:zg361_b2_pip_owner", handoff)
        for forbidden in (
            "zg361_workforce_probation_fact_publish_from_result_effect",
            "ATTRIBUTION_BPS_2",
            "ATTRIBUTION_BPS_3",
            "set_variable = { name = zg361_b2_workforce_pip_",
            "set_variable = { name = zg361_workforce_probation_fact_outcome_",
            "3333",
            "3334",
        ):
            self.assertNotIn(forbidden, handoff)

        first = top_level_block(self.events, "zg361b2.103")
        replay = top_level_block(self.events, "zg361b2.104")
        for event in (first, replay):
            self.assertIn("hidden = yes", event)
            self.assertEqual(
                event.count(
                    "zg361_b2_replay_workforce_probation_fact_handoff_effect = yes"
                ),
                1,
            )
            self.assertNotIn("zg361_b2_publish_workforce_pip_settlement_effect", event)
            self.assertNotIn("set_variable = { name = zg361_b2_workforce_pip_", event)
        for suffix in ("owner", "subject", "cycle", "case"):
            self.assertIn(f"zg361_b2_probation_handoff_{suffix}", first)
            self.assertIn(f"zg361_b2_probation_replay_{suffix}", replay)
        self.assertIn("stale probation handoff ticket ignored", first)
        self.assertIn("stale probation handoff replay ignored", replay)
        for ticket in (
            "save_scope_as = zg361_b2_probation_replay_owner",
            "save_scope_as = zg361_b2_probation_replay_subject",
            "name = zg361_b2_probation_replay_cycle",
            "name = zg361_b2_probation_replay_case",
        ):
            self.assertIn(ticket, first)
        self.assertIn("trigger_event = { id = zg361b2.104 days = 1 }", first)
        self.assertNotIn("trigger_event = { id = zg361b2.104", replay)

        probation = top_level_block(
            self.probation_effects,
            "zg361_workforce_probation_fact_publish_from_pip_settlement_effect",
        )
        # First call may commit exactly once from state 2; the actually
        # reachable second call sees state >= 3 and takes the exact-key replay
        # branch.  It cannot execute another canonical signer.
        self.assertIn("var:zg361_workforce_probation_fact_state = 2", probation)
        self.assertIn("var:zg361_workforce_probation_fact_state >= 3", probation)
        self.assertIn("var:zg361_workforce_probation_fact_source_kind = 2", probation)
        self.assertIn("adapter_status value = 2", probation)
        self.assertEqual(
            probation.count(
                "zg361_workforce_probation_fact_publish_canonical_effect = yes"
            ),
            1,
        )
        self.assertNotIn("owner_outcome_serial add = 1", probation)
        signer = top_level_block(
            self.probation_effects,
            "zg361_workforce_probation_fact_publish_canonical_effect",
        )
        self.assertEqual(signer.count("owner_outcome_serial add = 1"), 1)

    def test_b2_does_not_fake_the_blocked_ordinary_result_attribution_hook(self) -> None:
        combined = self.effects + self.events
        self.assertNotIn(
            "zg361_workforce_probation_fact_publish_from_result_effect",
            combined,
        )
        self.assertNotIn("ATTRIBUTION_BPS_2", combined)
        self.assertNotIn("ATTRIBUTION_BPS_3", combined)

    def test_workforce_adapter_reads_but_never_fabricates_357_359_sources(self) -> None:
        adapter = top_level_block(
            self.effects, "zg361_b2_submit_completed_al_receipts_effect"
        )
        for required in (
            "var:zg361_result_case_state = 5",
            "var:zg361_result_appeal_outcome = 1",
            "var:zg361_b1_result_adapter_result_case = var:zg361_b2_case_serial",
            "var:zg361_b1_m357_external_result_case = var:zg361_b2_case_serial",
            "var:zg361_b2_m358_external_receipt_route != 3",
            "var:zg361_b2_m359_external_receipt_route != 3",
            "zg361_we_submit_al_357_359_receipts_effect = {",
            "M357_RECEIPT_ID = var:zg361_b1_m357_external_receipt_id",
            "M358_RECEIPT_ID = var:zg361_b2_m358_external_receipt_id",
            "M359_RECEIPT_ID = var:zg361_b2_m359_external_receipt_id",
            "has_variable = zg361_we_adapter_status",
        ):
            self.assertIn(required, adapter)
        for source in (
            "zg361_b1_m357_external_receipt_id",
            "zg361_b1_m357_external_receipt_hash",
            "zg361_b2_m358_external_receipt_id",
            "zg361_b2_m358_external_receipt_hash",
            "zg361_b2_m359_external_receipt_id",
            "zg361_b2_m359_external_receipt_hash",
        ):
            self.assertNotIn(f"set_variable = {{ name = {source}", adapter)
        self.assertEqual(
            adapter.count("NOT = { var:zg361_b"),
            6,
        )

    def test_interface_069_closes_full_prompt_witness_and_deadline_identity(self) -> None:
        grade = top_level_block(self.core, "zg361_grade_325_apply_effect")
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_notice_prompt_{field}", grade)
        prompt = top_level_block(self.core_events, "zg361.50")
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_notice_prompt_{field}", prompt)
        witness = top_level_block(self.core_events, "zg361.51")
        deadline = top_level_block(self.core_events, "zg361.52")
        for block, prefix in (
            (witness, "zg361_notice_witness"),
            (deadline, "zg361_notice_deadline"),
        ):
            for field in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"{prefix}_{field}", block)
            self.assertIn("stale", block)
        self.assertIn("zg361_result_delivery_witness", prompt)
        self.assertIn("zg361_result_delivery_witness_receipt", witness)
        delivery = top_level_block(
            self.effects, "zg361_b2_m069_record_delivery_effect"
        )
        self.assertIn("zg361_b2_m069_witness", delivery)
        self.assertIn("zg361_b2_m069_witness_receipt", delivery)

    def test_receipts_are_bounded_non_aggravating_and_conservative(self) -> None:
        delivered = top_level_block(
            self.effects, "zg361_b2_on_notice_delivered_effect"
        )
        self.assertIn(
            "var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial",
            delivered,
        )
        corrected = top_level_block(
            self.effects, "zg361_b2_on_appeal_corrected_effect"
        )
        self.assertIn(
            "var:zg361_result_refund_posted_serial = var:zg361_result_case_serial",
            corrected,
        )
        non_aggravation = top_level_block(
            self.effects, "zg361_b2_m358_close_non_aggravation_effect"
        )
        self.assertIn("var:zg361_result_grade >=", non_aggravation)
        for resource in ("treasury", "gold", "merit"):
            self.assertIn(f"var:zg361_result_{resource}_paid <=", non_aggravation)
        exit_effect = top_level_block(
            self.effects, "zg361_b2_m075_accept_exit_offer_effect"
        )
        self.assertIn("treasury >= 50", exit_effect)
        self.assertEqual(exit_effect.count("remove_treasury = 50"), 1)
        self.assertEqual(exit_effect.count("add_gold = 50"), 1)
        self.assertIn("zg361_b2_m075_treasury_paid value = 50", exit_effect)
        self.assertIn("zg361_b2_m075_personal_received value = 50", exit_effect)
        self.assertNotIn("add_treasury", self.effects)

        redundancy = top_level_block(
            self.effects, "zg361_b2_m074_accept_redundancy_effect"
        )
        self.assertIn("treasury >= 50", redundancy)
        self.assertEqual(redundancy.count("remove_treasury = 50"), 1)
        self.assertEqual(redundancy.count("add_gold = 50"), 1)
        self.assertIn("zg361_b2_m074_actual_exit value = 1", redundancy)
        self.assertIn("zg361_b2_m074_hc_released value = 1", redundancy)
        self.assertIn("var:zg361_b2_m074_route = 2", redundancy)
        self.assertIn("zg361_b2_m074_treasury_paid value = 0", redundancy)
        self.assertIn("zg361_b2_m074_unfunded_disguised_exit", redundancy)
        audit = top_level_block(self.events, "zg361b2.171")
        self.assertIn("zg361_b2_m074_treasury_paid = 50", audit)
        self.assertIn("zg361_b2_m074_personal_received = 50", audit)

    def test_appeal_window_and_retaliation_gate_all_dispositions(self) -> None:
        prepare = top_level_block(
            self.effects, "zg361_b2_prepare_adverse_action_effect"
        )
        self.assertIn("var:zg361_result_appeal_open = 1", prepare)
        self.assertIn("adverse action held until base appeal window closes", prepare)
        self.assertIn("var:zg361_b2_retaliation_new_fact = 1", prepare)
        self.assertIn("zg361_b2_m358_open_separate_case_effect = yes", prepare)
        self.assertIn("var:zg361_b2_m070_route = 2", prepare)
        self.assertIn("zg361_b2_adverse_action_allowed value = 1", prepare)
        self.assertIn("zg361_b2_m070_retaliation_action_executed", prepare)
        self.assertIn("zg361_b2_management_debt add = 2", prepare)
        for index, name in enumerate(
            ("purge", "stepdown", "demote", "extend"), start=1
        ):
            block = top_level_block(
                self.core, f"zg361_eliminate_{name}_effect"
            )
            with self.subTest(action=name):
                self.assertIn(
                    f"zg361_b2_pending_adverse_action value = {index}", block
                )
                self.assertIn("zg361_b2_prepare_adverse_action_effect = yes", block)
                self.assertIn("zg361_b2_adverse_action_allowed = 1", block)
                self.assertIn("zg361_b2_finish_adverse_action_effect = yes", block)
                self.assertIn("zg361_b2_cancel_blocked_action_effect = yes", block)
        settle = top_level_block(self.core, "zg361_settle_delivered_325_effect")
        self.assertIn("var:zg361_result_appeal_open = 0", settle)
        expired = top_level_block(
            self.effects, "zg361_b2_on_appeal_expired_effect"
        )
        self.assertIn("trigger_event = { id = zg361.6 days = 1 }", expired)

    def test_pip_quota_and_boundary_writes_have_real_consumers(self) -> None:
        pip = top_level_block(self.effects, "zg361_b2_m015_open_pip_effect")
        self.assertIn("zg361_result_grade = 1", pip)
        self.assertIn("highest_held_title_tier >= tier_county", pip)
        self.assertIn("zg361_b2_pip_gate_threshold value = 3", pip)
        self.assertIn("zg361_b2_pip_gate_evidence_complete value = 0", pip)
        for token in (
            "var:zg361_result_absolute_grade = 1",
            "var:zg361_result_kpi_frozen < 0",
            "var:zg361_result_evidence_governance < 0",
            "var:zg361_result_evidence_capability < 0",
            "var:zg361_result_evidence_growth < 0",
            "var:zg361_result_evidence_superior < 0",
            "var:zg361_result_evidence_values < 0",
            "var:zg361_result_evidence_collaboration < 0",
            "var:zg361_result_evidence_jingcha < 0",
            "var:zg361_result_evidence_organization < 0",
            "zg361_b2_pip_gate_component_count >= var:zg361_b2_pip_gate_threshold",
        ):
            self.assertIn(token, pip)
        self.assertNotIn("zg361_result_grade_reason = 5", pip)
        self.assertIn("limit = { is_ai = yes }", pip)
        self.assertIn("zg361_b2_accept_pip_effect = yes", pip)
        self.assertEqual(
            pip.count("zg361_b2_clear_pip_case_tuple_effect = yes"), 2
        )
        self.assertIn("Route C records only its bounded policy debt", pip)
        phase1_settlement = top_level_block(
            self.core, "zg361_settle_delivered_325_effect"
        )
        self.assertNotIn("modifier = zg361_pip", phase1_settlement)
        self.assertNotIn(
            "remove_character_modifier = zg361_pip",
            top_level_block(self.core, "zg361_apply_grade_effect"),
        )
        resolve = top_level_block(self.effects, "zg361_b2_resolve_pip_due_effect")
        self.assertIn("zg361_result_cycle_serial > var:zg361_b2_pip_cycle", resolve)
        self.assertNotIn("zg361_b2_settle_pip_outcome_effect = yes", resolve)
        self.assertIn("trigger_event = { id = zg361b2.101 days = 1 }", resolve)
        for suffix in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b2_terminal_settlement_{suffix}", resolve)
        self.assertNotIn("zg361_b2_pip_graduation_receipt", resolve)
        terminal_event = top_level_block(self.events, "zg361b2.101")
        self.assertEqual(
            terminal_event.count("zg361_b2_settle_pip_outcome_effect = yes"),
            1,
        )
        for suffix in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b2_terminal_settlement_{suffix}", terminal_event)
        self.assertIn("stale terminal settlement ticket ignored", terminal_event)
        settlement = top_level_block(
            self.effects, "zg361_b2_settle_pip_outcome_effect"
        )
        for token in (
            "zg361_b2_pip_settlement_receipt = var:zg361_b2_pip_case",
            "remove_character_modifier = zg361_pip",
            "zg361_b2_release_pip_support_effect = yes",
            "zg361_b2_pip_graduation_receipt",
            "zg361_b2_pip_failure_receipt",
            "zg361_b2_pip_performance_evidence_delta value = 10",
            "zg361_b2_pip_performance_evidence_delta value = -10",
            "zg361_b2_publish_pip_performance_evidence_effect = yes",
            "zg361_b2_m017_open_disposition_effect = yes",
        ):
            self.assertIn(token, settlement)
        refusal = top_level_block(self.effects, "zg361_b2_refuse_pip_effect")
        self.assertIn(
            "zg361_b2_pip_performance_evidence_delta value = -15", refusal
        )
        self.assertIn("zg361_b2_publish_pip_performance_evidence_effect = yes", refusal)
        consumer = top_level_block(
            self.effects, "zg361_b2_consume_pip_performance_evidence_effect"
        )
        self.assertIn("zg361_evidence_growth add = var:zg361_b2_pip_performance_evidence_delta", consumer)
        self.assertIn("zg361_kpi add = var:zg361_b2_pip_performance_evidence_delta", consumer)
        self.assertIn("zg361_b2_pip_performance_evidence_status value = 2", consumer)
        self.assertIn(
            "zg361_b2_consume_pip_performance_evidence_effect = yes",
            top_level_block(self.core, "zg361_compute_kpi_effect"),
        )

    def test_016_tooltip_first_use_reads_are_nested_behind_presence_gates(self) -> None:
        opened = top_level_block(
            self.effects, "zg361_b2_m016_open_business_object_effect"
        )
        self.assertIn(
            "\tzg361_b2_m016_resolve_policy_effect = yes\n"
            "\tif = {\n"
            "\t\tlimit = { has_variable = zg361_b2_m016_route }\n"
            "\t\tif = {\n"
            "\t\t\tlimit = { var:zg361_b2_m016_route = 3 }",
            opened,
        )

        committed = top_level_block(
            self.effects, "zg361_b2_m016_commit_support_effect"
        )
        self.assertIn(
            "\tif = {\n"
            "\t\tlimit = { has_variable = zg361_b2_m016_object_active }\n"
            "\t\tif = {\n"
            "\t\t\tlimit = { has_variable = zg361_b2_m016_route }\n"
            "\t\t\tif = {\n"
            "\t\t\t\tlimit = {\n"
            "\t\t\t\t\tvar:zg361_b2_m016_object_active = 1",
            committed,
        )

        published = top_level_block(
            self.effects, "zg361_b2_publish_pip_performance_evidence_effect"
        )
        self.assertIn(
            "\tif = {\n"
            "\t\tlimit = { has_variable = zg361_b2_pip_performance_evidence_delta }\n"
            "\t\tif = {\n"
            "\t\t\tlimit = {",
            published,
        )

        # The live fault was isolated to #016.  Preserve the unchanged generic
        # policy kernel for mechanisms that have no matching CK3 evidence.
        m015_opened = top_level_block(
            self.effects, "zg361_b2_m015_open_business_object_effect"
        )
        self.assertNotIn("has_variable = zg361_b2_m015_route", m015_opened)

    def test_016_midpoint_progress_has_a_real_kpi_producer_and_exact_provenance(self) -> None:
        pip = top_level_block(self.effects, "zg361_b2_m015_open_pip_effect")
        for token in (
            "zg361_b2_pip_progress_source_kind value = 1",
            "zg361_b2_pip_progress_source_kind value = 2",
            "zg361_b2_pip_progress_source_kind value = 3",
            "zg361_b2_pip_progress_baseline_owner value = var:zg361_b2_case_owner",
            "zg361_b2_pip_progress_baseline_subject value = this",
            "zg361_b2_pip_progress_baseline_cycle value = var:zg361_b2_case_cycle",
            "zg361_b2_pip_progress_baseline_case value = var:zg361_b2_case_serial",
            "liege = var:zg361_b2_case_owner",
            "zg361_b2_pip_progress_baseline_value value = zg361_kpi_governance_evidence_value",
            "zg361_b2_pip_progress_baseline_value value = zg361_kpi_capability_evidence_value",
            "zg361_b2_pip_progress_baseline_value value = zg361_kpi_collaboration_evidence_value",
            "value = zg361_kpi_governance_evidence_value add = 1",
            "value = zg361_kpi_capability_evidence_value add = 1",
            "value = zg361_kpi_collaboration_evidence_value add = 1",
            "zg361_b2_pip_progress_baseline_status value = 0",
            "zg361_b2_pip_progress_baseline_red_code value = 1",
            "zg361_b2_pip_progress_baseline_status value = 1",
            "zg361_b2_pip_progress_baseline_red_code value = 0",
        ):
            self.assertIn(token, pip)
        # Baron/count subjects remain controllable: only the task-kind branch
        # changes, while every tier receives the same native KPI producer.
        self.assertIn("zg361_b2_pip_progress_baseline_task_kind value = 3", pip)
        self.assertIn("highest_held_title_tier >= tier_county", pip)

        midpoint = top_level_block(
            self.effects, "zg361_b2_record_pip_midpoint_effect"
        )
        for field in (
            "owner",
            "subject",
            "cycle",
            "case",
            "task_kind",
        ):
            self.assertIn(
                f"zg361_b2_pip_midpoint_progress_{field}", midpoint
            )
        for token in (
            "has_variable = zg361_b2_pip_progress_baseline_value",
            "var:zg361_b2_pip_progress_baseline_owner = var:zg361_b2_pip_owner",
            "var:zg361_b2_pip_progress_baseline_subject = this",
            "var:zg361_b2_pip_progress_baseline_cycle = var:zg361_b2_pip_cycle",
            "var:zg361_b2_pip_progress_baseline_case = var:zg361_b2_pip_case",
            "var:zg361_b2_pip_progress_source_kind = var:zg361_b2_pip_progress_baseline_task_kind",
            "liege = var:zg361_b2_pip_owner",
            "zg361_b2_pip_midpoint_progress_current_value value = zg361_kpi_governance_evidence_value",
            "zg361_b2_pip_midpoint_progress_current_value value = zg361_kpi_capability_evidence_value",
            "zg361_b2_pip_midpoint_progress_current_value value = zg361_kpi_collaboration_evidence_value",
            "value = var:zg361_b2_pip_midpoint_progress_current_value subtract = var:zg361_b2_pip_progress_baseline_value",
            "var:zg361_b2_pip_midpoint_progress_current_value >= var:zg361_b2_pip_progress_target_value",
            "zg361_b2_pip_midpoint_progress_status value = 1",
            "zg361_b2_pip_midpoint_progress_red_code value = 0",
        ):
            self.assertIn(token, midpoint)
        # The two facts are adjacent products, not aliases: no support write is
        # used in the KPI delta expression.
        delta_write = midpoint[
            midpoint.index("name = zg361_b2_pip_midpoint_progress_delta") :
            midpoint.index("name = zg361_b2_pip_midpoint_progress_met")
        ]
        self.assertNotIn("support_", delta_write)

    def test_017_due_review_is_signed_by_a_real_independent_manager(self) -> None:
        assign = top_level_block(
            self.effects, "zg361_b2_assign_pip_independent_reviewer_effect"
        )
        for token in (
            "zg361_is_celestial_liege_trigger = yes",
            "is_available = yes",
            "is_imprisoned = no",
            "NOT = { this = scope:zg361_b2_pip_review_owner }",
            "NOT = { this = scope:zg361_b2_pip_review_subject }",
            "NOT = { is_close_family_of = scope:zg361_b2_pip_review_owner }",
            "NOT = { is_close_family_of = scope:zg361_b2_pip_review_subject }",
            "NOT = { has_relation_friend = scope:zg361_b2_pip_review_owner }",
            "order_by = stewardship",
            "zg361_b2_pip_reviewer_assignment_status value = 1",
            "zg361_b2_pip_reviewer_assignment_red_code value = 0",
            "zg361_b2_pip_reviewer_assignment_receipt value = var:zg361_b2_case_serial",
        ):
            self.assertIn(token, assign)
        self.assertNotIn("trigger_event", assign)
        self.assertNotIn("random_", assign)

        due_event = top_level_block(self.events, "zg361b2.100")
        self.assertIn("hidden = yes", due_event)
        self.assertNotIn("option =", due_event)

        resolve = top_level_block(self.effects, "zg361_b2_resolve_pip_due_effect")
        for token in (
            "zg361_b2_pip_independent_review_status value = 0",
            "zg361_b2_pip_independent_review_red_code value = 2",
            "var:zg361_b2_pip_reviewer_assignment_owner = var:zg361_b2_pip_owner",
            "var:zg361_b2_pip_reviewer_assignment_subject = this",
            "var:zg361_b2_pip_reviewer_assignment_cycle = var:zg361_b2_pip_cycle",
            "var:zg361_b2_pip_reviewer_assignment_case = var:zg361_b2_pip_case",
            "var:zg361_b2_pip_midpoint_progress_status = 1",
            "var:zg361_b2_pip_midpoint_progress_red_code = 0",
            "var:zg361_result_case_owner = var:zg361_b2_pip_owner",
            "var:zg361_result_cycle_serial > var:zg361_b2_pip_cycle",
            "var:zg361_result_case_state >= 3",
            "var:zg361_result_grade = var:zg361_last_grade",
            "var:zg361_b2_pip_independent_reviewer = {",
            "zg361_b2_last_pip_review_subject value = root",
            "zg361_b2_pip_independent_review_result_case value = var:zg361_result_case_serial",
            "var:zg361_b2_pip_midpoint_progress_met = 1",
            "zg361_b2_pip_independent_review_status value = 1",
            "zg361_b2_pip_independent_review_status value = 2",
            "zg361_b2_pip_independent_review_red_code value = 0",
            "zg361_b2_pip_independent_review_receipt value = var:zg361_b2_pip_case",
        ):
            self.assertIn(token, resolve)
        self.assertLess(
            resolve.index("var:zg361_b2_pip_independent_reviewer = {"),
            resolve.index("trigger_event = { id = zg361b2.101 days = 1 }"),
        )

        settlement = top_level_block(
            self.effects, "zg361_b2_settle_pip_outcome_effect"
        )
        for token in (
            "trigger_if = {",
            "has_variable = zg361_b2_pip_independent_review_receipt",
            "var:zg361_b2_pip_independent_review_reviewer = var:zg361_b2_pip_independent_reviewer",
            "var:zg361_b2_pip_independent_review_result_cycle > var:zg361_b2_pip_cycle",
            "var:zg361_b2_pip_independent_review_receipt = var:zg361_b2_pip_case",
            "zg361_b2_pip_outcome_result_cycle value = var:zg361_b2_pip_independent_review_result_cycle",
            "zg361_b2_pip_outcome_result_case value = var:zg361_b2_pip_independent_review_result_case",
            "zg361_b2_pip_outcome_result_grade value = var:zg361_b2_pip_independent_review_result_grade",
        ):
            self.assertIn(token, settlement)
        self.assertNotIn(
            "set_variable = { name = zg361_b2_pip_independent_review_status",
            settlement,
        )

    def test_second_pip_resets_author_then_accepts_negotiates_or_refuses(self) -> None:
        reset = top_level_block(
            self.effects, "zg361_b2_clear_pip_case_tuple_effect"
        )
        pip = top_level_block(self.effects, "zg361_b2_m015_open_pip_effect")
        for field in PIP_CASE_TUPLE_FIELDS:
            with self.subTest(reset_field=field):
                self.assertEqual(
                    len(
                        re.findall(
                            rf"(?m)^\s*remove_variable\s*=\s*{re.escape(field)}\s*$",
                            reset,
                        )
                    ),
                    1,
                )
        self.assertEqual(
            len(re.findall(r"(?m)^\s*remove_variable\s*=", reset)),
            len(PIP_CASE_TUPLE_FIELDS),
        )
        self.assertIn(
            "remove_variable = zg361_b2_pip_subject_response_author", reset
        )
        self.assertNotIn("pip_performance_evidence", reset)

        # The reset must run before the replacement identity and before its
        # pending-response zeroes are written.  Therefore a terminal first PIP
        # cannot make the provider see an author on the second pending PIP.
        reset_call = pip.index("zg361_b2_clear_pip_case_tuple_effect = yes")
        owner_write = pip.index(
            "zg361_b2_pip_owner value = var:zg361_b2_case_owner"
        )
        pending_response = pip.index(
            "zg361_b2_pip_subject_response value = 0"
        )
        self.assertLess(reset_call, owner_write)
        self.assertLess(owner_write, pending_response)
        self.assertNotIn(
            "zg361_b2_pip_subject_response_author value",
            pip[reset_call:pending_response],
        )

        stale_first_case = {field: 99 for field in PIP_CASE_TUPLE_FIELDS}
        second_case = dict(stale_first_case)
        for field in PIP_CASE_TUPLE_FIELDS:
            second_case.pop(field, None)
        second_case.update(
            {
                "zg361_b2_pip_case": 100,
                "zg361_b2_pip_state": 1,
                "zg361_b2_pip_subject_response": 0,
                "zg361_b2_pip_subject_response_case": 0,
                "zg361_b2_pip_goal_revision_used": 0,
                "zg361_b2_pip_refusal_receipt": 0,
            }
        )
        self.assertNotIn(
            "zg361_b2_pip_subject_response_author", second_case
        )

        for effect_name, response_code, terminal_state in (
            ("zg361_b2_accept_pip_effect", 1, 2),
            ("zg361_b2_negotiate_pip_effect", 2, 2),
            ("zg361_b2_refuse_pip_effect", 3, 5),
        ):
            action = top_level_block(self.effects, effect_name)
            with self.subTest(action=effect_name):
                self.assertIn("var:zg361_b2_pip_subject_response = 0", action)
                self.assertIn(
                    f"zg361_b2_pip_subject_response value = {response_code}",
                    action,
                )
                self.assertIn(
                    "zg361_b2_pip_subject_response_case value = var:zg361_b2_pip_case",
                    action,
                )
                self.assertIn(
                    "zg361_b2_pip_subject_response_author value = this",
                    action,
                )
                self.assertIn(
                    f"zg361_b2_pip_state value = {terminal_state}", action
                )
                projected = dict(second_case)
                if (
                    projected["zg361_b2_pip_state"] == 1
                    and projected["zg361_b2_pip_subject_response"] == 0
                    and "zg361_b2_pip_subject_response_author" not in projected
                ):
                    projected["zg361_b2_pip_subject_response"] = response_code
                    projected["zg361_b2_pip_subject_response_case"] = projected[
                        "zg361_b2_pip_case"
                    ]
                    projected["zg361_b2_pip_subject_response_author"] = "subject"
                    projected["zg361_b2_pip_state"] = terminal_state
                self.assertEqual(
                    projected["zg361_b2_pip_subject_response"], response_code
                )
                self.assertEqual(
                    projected["zg361_b2_pip_subject_response_case"], 100
                )
                self.assertEqual(
                    projected["zg361_b2_pip_subject_response_author"], "subject"
                )

    def test_route_c_removes_the_complete_pip_tuple(self) -> None:
        pip = top_level_block(self.effects, "zg361_b2_m015_open_pip_effect")
        reset = top_level_block(
            self.effects, "zg361_b2_clear_pip_case_tuple_effect"
        )
        route_c = pip[pip.index("Route C records only its bounded policy debt") :]
        self.assertIn("zg361_b2_clear_pip_case_tuple_effect = yes", route_c)
        for field in (
            "zg361_b2_pip_owner",
            "zg361_b2_pip_subject",
            "zg361_b2_pip_cycle",
            "zg361_b2_pip_case",
            "zg361_b2_pip_state",
            "zg361_b2_pip_task_kind",
            "zg361_b2_pip_task_controllable",
            "zg361_b2_pip_policy_route",
            "zg361_b2_pip_subject_response_author",
            "zg361_b2_pip_support_reserved",
            "zg361_b2_pip_settlement_receipt",
            "zg361_b2_pip_outcome_code",
        ):
            with self.subTest(route_c_field=field):
                self.assertIn(f"remove_variable = {field}", reset)

    def test_pip_evidence_uses_prospective_cycle_and_is_consumed_once(self) -> None:
        producer = top_level_block(
            self.effects, "zg361_b2_publish_pip_performance_evidence_effect"
        )
        consumer = top_level_block(
            self.effects, "zg361_b2_consume_pip_performance_evidence_effect"
        )
        self.assertIn(
            "zg361_b2_pip_performance_evidence_source_cycle value = var:zg361_b2_pip_cycle",
            producer,
        )
        self.assertIn(
            "zg361_b2_pip_performance_evidence_due_cycle value = var:zg361_b2_pip_cycle",
            producer,
        )
        self.assertIn(
            "zg361_b2_pip_performance_evidence_due_cycle add = 1", producer
        )
        for token in (
            "has_character_flag = zg361_b1_cycle_active",
            "root.var:zg361_b1_cycle_serial >= var:zg361_b2_pip_performance_evidence_due_cycle",
            "NOT = { has_character_flag = zg361_b1_cycle_active }",
            "root.var:zg361_review_serial >= var:zg361_b2_pip_performance_evidence_source_cycle",
            "zg361_b2_pip_performance_evidence_consumed_cycle value = var:zg361_b2_pip_performance_evidence_due_cycle",
            "zg361_b2_pip_performance_evidence_consumed_cycle value = root.var:zg361_b1_cycle_serial",
        ):
            self.assertIn(token, consumer)
        self.assertNotIn(
            "root.var:zg361_review_serial >= var:zg361_b2_pip_performance_evidence_due_cycle",
            consumer,
        )

        # Executable truth table for the two engine orderings.  On active B1,
        # the current frozen serial must reach source+1.  On legacy, the next
        # compute still sees review_serial==source because increment happens
        # after compute; the pending receipt itself does not exist earlier.
        def eligible(
            *, active_b1: bool, b1_serial: int, review_serial: int,
            source_cycle: int, pending: bool = True,
        ) -> bool:
            due_cycle = source_cycle + 1
            if not pending:
                return False
            if active_b1:
                return b1_serial >= due_cycle
            return review_serial >= source_cycle

        self.assertFalse(
            eligible(active_b1=True, b1_serial=7, review_serial=7, source_cycle=7)
        )
        self.assertTrue(
            eligible(active_b1=True, b1_serial=8, review_serial=7, source_cycle=7)
        )
        self.assertFalse(
            eligible(
                active_b1=False,
                b1_serial=0,
                review_serial=7,
                source_cycle=7,
                pending=False,
            )
        )
        self.assertTrue(
            eligible(active_b1=False, b1_serial=0, review_serial=7, source_cycle=7)
        )
        self.assertEqual(consumer.count(
            "zg361_b2_pip_performance_evidence_status value = 2"
        ), 1)
        midpoint = top_level_block(self.effects, "zg361_b2_record_pip_midpoint_effect")
        self.assertIn("zg361_b2_pip_midpoint_resource_delivery_valid value = 1", midpoint)
        # RED is the fail-closed initialization; an exact baseline tuple now
        # reaches the real native KPI producer and clears it.
        self.assertIn("zg361_b2_pip_midpoint_progress_status value = 0", midpoint)
        self.assertIn("zg361_b2_pip_midpoint_progress_red_code value = 1", midpoint)
        self.assertIn("zg361_b2_pip_midpoint_progress_status value = 1", midpoint)
        self.assertIn("zg361_b2_pip_midpoint_progress_red_code value = 0", midpoint)
        midpoint_event = top_level_block(self.events, "zg361b2.99")
        for suffix in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b2_pip_{suffix} = scope:zg361_b2_pip_deadline_{suffix}", midpoint_event)
        self.assertIn("zg361_b2_record_pip_midpoint_effect = yes", midpoint_event)
        escalation = top_level_block(
            self.effects, "zg361_b2_publish_evidence_escalation_effect"
        )
        self.assertIn("zg361_b2_m071_evidence_hash", escalation)
        self.assertIn("trigger_event = { id = zg361b2.141 days = 30 }", escalation)
        access = top_level_block(
            self.effects, "zg361_b2_record_case_access_effect"
        )
        self.assertIn("zg361_b2_m072_pre_delivery_reads value = 1", access)
        self.assertIn("zg361_b2_m081_subject_read_receipt", access)
        self.assertIn("trigger_event = { id = zg361b2.121 days = 30 }", access)
        appeal_event = top_level_block(self.core_events, "zg361.4")
        self.assertIn("zg361_b2_m077_quality_bonus", appeal_event)
        skip = top_level_block(
            self.effects, "zg361_b2_m079_open_skip_level_effect"
        )
        self.assertIn("var:zg361_b2_skip_seats_used < 2", skip)
        self.assertIn("zg361_b2_m079_seat_reserved value = 1", skip)
        skip_close = top_level_block(self.events, "zg361b2.140")
        self.assertIn("zg361_b2_m079_release_seat_effect = yes", skip_close)
        rank = top_level_block(self.core, "zg361_rank_cohort_effect")
        kpi = top_level_block(self.core, "zg361_compute_kpi_effect")
        self.assertIn("zg361_b2_apply_due_quota_debt_effect = yes", rank)
        self.assertIn("zg361_b2_consume_management_debt_effect = yes", kpi)
        debt = top_level_block(
            self.effects, "zg361_b2_apply_due_quota_debt_effect"
        )
        self.assertIn("change_variable = { name = zg361_bottom_slots", debt)
        self.assertIn("zg361_b2_quota_debt_consumed_cycle", debt)
        boundary = top_level_block(
            self.effects, "zg361_b2_apply_boundary_redelivery_effect"
        )
        self.assertIn("remove_character_modifier = zg361_grade_35", boundary)
        self.assertIn("zg361_result_settlement_posted_serial value = 0", boundary)
        self.assertIn("zg361_b2_on_result_frozen_effect = yes", boundary)
        self.assertIn("zg361_settle_delivered_325_effect = yes", boundary)
        self.assertIn("zg361_b2_scoreboard_redelivery_dirty", boundary)
        self.assertIn("zg361_b2_m359_redelivery_receipt", boundary)
        quota_open = top_level_block(
            self.effects, "zg361_b2_m359_open_boundary_review_effect"
        )
        self.assertIn("zg361_b2_m359_corrected_grade_before value = 1", quota_open)
        self.assertIn("zg361_b2_m359_boundary_grade_after value = 1", quota_open)

    def test_active_pip_identity_survives_later_result_freezes(self) -> None:
        frozen = top_level_block(self.effects, "zg361_b2_on_result_frozen_effect")
        for mechanism_id in (15, 16, 17):
            variable = f"zg361_b2_m{mechanism_id:03d}_object_active"
            self.assertIn(
                f"limit = {{ has_variable = {variable} }}",
                frozen,
            )
            self.assertIn(
                f"limit = {{ var:{variable} = 1 }}",
                frozen,
            )
            self.assertNotIn(
                f"NOT = {{ has_variable = {variable} }}",
                frozen,
            )
        self.assertIn("limit = { has_variable = zg361_b2_pip_state }", frozen)
        self.assertIn("zg361_b2_pip_lifecycle_clear value = 0", frozen)
        self.assertIn("remove_variable = zg361_b2_pip_lifecycle_clear", frozen)
        for mechanism_id in (15, 16, 17):
            opened = top_level_block(
                self.effects,
                f"zg361_b2_m{mechanism_id:03d}_open_business_object_effect",
            )
            consumed = top_level_block(
                self.effects,
                f"zg361_b2_m{mechanism_id:03d}_consume_business_object_effect",
            )
            for suffix in ("owner", "cycle"):
                self.assertIn(
                    f"zg361_b2_m{mechanism_id:03d}_object_{suffix} value = var:zg361_b2_pip_{suffix}",
                    opened,
                )
                self.assertIn(
                    f"zg361_b2_m{mechanism_id:03d}_object_{suffix} = var:zg361_b2_pip_{suffix}",
                    consumed,
                )
            self.assertIn(
                f"zg361_b2_m{mechanism_id:03d}_object_receipt_case value = var:zg361_b2_pip_case",
                opened,
            )
            self.assertIn(
                f"zg361_b2_m{mechanism_id:03d}_object_receipt_case = var:zg361_b2_pip_case",
                consumed,
            )

    def test_015_first_use_pip_slot_reads_are_existence_safe(self) -> None:
        pip = top_level_block(self.effects, "zg361_b2_m015_open_pip_effect")
        for mechanism_id in (15, 16, 17):
            variable = f"zg361_b2_m{mechanism_id:03d}_object_active"
            self.assertIn(
                f"\tif = {{\n"
                f"\t\tlimit = {{ has_variable = {variable} }}\n"
                f"\t\tif = {{\n"
                f"\t\t\tlimit = {{ var:{variable} = 1 }}",
                pip,
            )
            self.assertNotIn(f"NOT = {{ var:{variable} = 1 }}", pip)
        self.assertIn(
            "\tif = {\n"
            "\t\tlimit = { has_variable = zg361_b2_pip_state }\n"
            "\t\tif = {\n"
            "\t\t\tlimit = {\n"
            "\t\t\t\tOR = {\n"
            "\t\t\t\t\tvar:zg361_b2_pip_state = 1",
            pip,
        )
        self.assertIn(
            "limit = { has_variable = zg361_b2_pip_slot_available }", pip
        )
        self.assertIn("var:zg361_b2_pip_slot_available = 1", pip)
        self.assertIn("remove_variable = zg361_b2_pip_slot_available", pip)

    def test_first_result_optional_state_reads_are_guarded(self) -> None:
        debts = top_level_block(
            self.effects, "zg361_b2_consume_due_policy_debts_effect"
        )
        frozen = top_level_block(self.effects, "zg361_b2_on_result_frozen_effect")
        for mechanism_id in CORE_IDS:
            key = f"{mechanism_id:03d}"
            self.assertIn(
                f"has_variable = zg361_b2_m{key}_policy_debt_active", debts
            )
            opened = top_level_block(
                self.effects, f"zg361_b2_m{key}_open_business_object_effect"
            )
            self.assertIn(
                f"NOT = {{ has_variable = zg361_b2_m{key}_object_active }}",
                opened,
            )
        self.assertIn("has_variable = zg361_b2_m079_remand_active", frozen)
        self.assertIn("has_variable = zg361_b2_m080_state", frozen)

    def test_358_route_b_aggravates_with_an_actual_bounded_receipt(self) -> None:
        aggravate = top_level_block(
            self.effects, "zg361_b2_m358_apply_disclosed_aggravation_effect"
        )
        for required in (
            "var:zg361_b2_m358_route = 2",
            "remove_short_term_gold = 10",
            "zg361_b2_m358_extra_gold_paid",
            "zg361_result_gold_paid add = var:zg361_b2_m358_extra_gold_paid",
            "zg361_b2_m358_aggravation_receipt",
            "zg361_b2_m358_aggravation_disclosed",
        ):
            self.assertIn(required, aggravate)
        upheld = top_level_block(
            self.effects, "zg361_b2_on_appeal_upheld_effect"
        )
        self.assertLess(
            upheld.index("zg361_b2_m358_apply_disclosed_aggravation_effect = yes"),
            upheld.index("zg361_b2_m358_close_non_aggravation_effect = yes"),
        )
        closed = top_level_block(
            self.effects, "zg361_b2_m358_close_non_aggravation_effect"
        )
        self.assertIn("zg361_b2_m358_aggravated value = 1", closed)
        self.assertIn("zg361_b2_m358_retaliation_risk value = 1", closed)

    def test_no_later_feedback_or_full_pip_batches_are_claimed(self) -> None:
        combined = self.effects + self.events
        for mechanism_id in (
            *range(146, 157),
            *range(181, 192),
        ):
            self.assertNotIn(f"zg361_b2_m{mechanism_id:03d}_", combined)


if __name__ == "__main__":
    unittest.main()
