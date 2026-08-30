#!/usr/bin/env python3
"""L0 product-wiring contracts for the first B2 CK3 vertical slice.

These tests prove generated Paradox source, hook placement, deterministic
receipts and negative/stale guards.  They do not claim a CK3 live run or raise
the readiness recorded by the phase-two program.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

from gen_361_b2_runtime import INTERFACE_IDS, MOD_ROOT, WIRED_IDS, outputs
from zg361_b2_runtime_data import B2_BINDINGS


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
        cls.effects = read("common/scripted_effects/zg361_b2_runtime_effects.txt")
        cls.events = read("events/zg361_b2_runtime_events.txt")
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
        self.assertEqual(len(rendered), 11)
        for path, payload in rendered.items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), payload)
                self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
                if path.suffix in {".txt", ".yml"} and path.suffix == ".txt":
                    self.assertIn(
                        b"# GENERATED FILE \xe2\x80\x94 edit tools/gen_361_b2_runtime.py",
                        payload,
                    )
        self.assertNotIn("zg361_case_kernel", self.effects + self.events)

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
        self.assertIn("limit = { is_ai = yes }", pip)
        self.assertIn("zg361_b2_accept_pip_effect = yes", pip)
        resolve = top_level_block(self.effects, "zg361_b2_resolve_pip_due_effect")
        self.assertIn("zg361_result_cycle_serial > var:zg361_b2_pip_cycle", resolve)
        self.assertIn("zg361_b2_pip_graduation_receipt", resolve)
        self.assertIn("zg361_b2_m017_open_disposition_effect = yes", resolve)
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

    def test_no_later_feedback_or_full_pip_batches_are_claimed(self) -> None:
        combined = self.effects + self.events
        for mechanism_id in (
            *range(146, 157),
            *range(181, 192),
        ):
            self.assertNotIn(f"zg361_b2_m{mechanism_id:03d}_", combined)


if __name__ == "__main__":
    unittest.main()
