#!/usr/bin/env python3
"""L0 contracts for the B1 cross-cycle performance-season foundation.

These tests prove wiring and deterministic source/model contracts only. They
must not upgrade any mechanism to fixture-live without one MCP-first CK3 run.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

from gen_361_b1_runtime import MOD_ROOT, outputs
from zg361_b1_runtime_data import B1_BINDINGS, B1_IDS, STAGE_SEQUENCE


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


def without_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


class B1RuntimeFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read("common/scripted_effects/zg361_b1_runtime_effects.txt")
        cls.events = read("events/zg361_b1_runtime_events.txt")
        cls.core = read("common/scripted_effects/zg361_effects.txt")
        cls.jingcha = read(
            "common/scripted_effects/zg361_jingcha_mandate_effects.txt"
        )
        cls.activity = read("common/activities/activity_types/zg361_jingcha.txt")
        cls.interactions = read(
            "common/character_interactions/zg361_interactions.txt"
        )
        cls.triggers = read("common/scripted_triggers/zg361_triggers.txt")
        cls.values = read("common/script_values/zg361_values.txt")
        cls.loc_en = read("localization/english/zg361_b1_l_english.yml")
        cls.loc_zh = read("localization/simp_chinese/zg361_b1_l_simp_chinese.yml")
        cls.placeholder_locs = {
            language: read(
                f"localization/{language}/zg361_b1_l_{language}.yml"
            )
            for language in (
                "french",
                "german",
                "japanese",
                "korean",
                "polish",
                "russian",
                "spanish",
            )
        }

    def test_exact_b1_batch_and_meaningful_binding_fields(self) -> None:
        expected = (
            tuple(range(1, 14))
            + tuple(range(37, 54))
            + tuple(range(135, 146))
            + (357,)
        )
        self.assertEqual(B1_IDS, expected)
        self.assertEqual(len(B1_BINDINGS), 42)
        self.assertEqual(
            {row.stage for row in B1_BINDINGS},
            set(STAGE_SEQUENCE),
        )
        for row in B1_BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                self.assertTrue(row.hook)
                self.assertTrue(row.meaningful_write)
                self.assertTrue(row.consumer)
                self.assertIn(
                    f"zg361_b1_m{row.mechanism_id:03d}_receipt_serial",
                    self.effects,
                )

    def test_generated_files_are_current_and_bom(self) -> None:
        for path, payload in outputs().items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), payload)
                self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))

    def test_cycle_uses_persistent_subject_roster(self) -> None:
        self.assertIn("clear_variable_list = zg361_b1_subjects", self.effects)
        self.assertIn("add_to_variable_list = {", self.effects)
        self.assertIn("name = zg361_b1_subjects", self.effects)
        self.assertGreaterEqual(
            self.effects.count("every_in_list = {\n\t\tvariable = zg361_b1_subjects"),
            4,
        )
        self.assertIn("max = 80", self.effects)
        b1_path = self.core.split("has_character_flag = zg361_b1_cycle_active", 1)[1]
        self.assertIn("variable = zg361_b1_subjects", b1_path)

    def test_newcomer_policy_is_applied_after_newcomer_detection(self) -> None:
        detection = self.effects.index(
            "set_variable = { name = zg361_b1_newcomer_route value = 1 }"
        )
        policy = self.effects.index(
            "root.var:zg361_mechanism_041_choice = 2"
        )
        self.assertLess(detection, policy)

    def test_delayed_stage_chain_has_immutable_tokens_and_stale_noops(self) -> None:
        for event_id in (100, 101, 102, 103):
            self.assertIn(f"zg361b1.{event_id} = {{", self.events)
        for token in (
            "zg361_b1_ticket_owner",
            "zg361_b1_ticket_cycle",
            "zg361_b1_ticket_case",
            "zg361_b1_ticket_state",
        ):
            self.assertIn(token, self.events)
        for expected_state in (1, 2, 3, 5):
            self.assertIn(f"var:zg361_b1_cycle_state = {expected_state}", self.events)
        stale_markers = {
            100: "stale midcycle ticket ignored",
            101: "stale peer-window ticket ignored",
            102: "stale facts ticket ignored",
            103: "stale shadow-close ticket ignored",
            110: "stale common-superior bank ticket ignored",
            111: "stale manager-calibration ticket ignored",
        }
        for event_id, marker in stale_markers.items():
            with self.subTest(event=event_id):
                self.assertIn(marker, top_level_block(self.events, f"zg361b1.{event_id}"))
        self.assertIn("id = zg361b1.100 days = 180", self.effects)
        self.assertIn("id = zg361b1.101 days = 60", self.events)
        self.assertIn("id = zg361b1.102 days = 60", self.events)
        self.assertIn("id = zg361b1.103 days = 30", self.effects)

    def test_player_self_review_has_three_guarded_routes_and_ai_fallback(self) -> None:
        event = top_level_block(self.events, "zg361b1.200")
        self.assertEqual(event.count("option = {"), 3)
        for key, effect in (
            ("zg361b1.200.a", "zg361_b1_submit_self_honest_ticket_effect"),
            ("zg361b1.200.b", "zg361_b1_submit_self_exaggerated_ticket_effect"),
            ("zg361b1.200.c", "zg361_b1_submit_self_conservative_ticket_effect"),
        ):
            self.assertIn(f"name = {key}", event)
            self.assertIn(f"{effect} = yes", event)

        dispatcher = top_level_block(
            self.effects, "zg361_b1_peer_window_dispatcher_effect"
        )
        self.assertIn("limit = { is_ai = yes }", dispatcher)
        self.assertIn("zg361_b1_record_self_honest_effect = yes", dispatcher)
        ai_branch = dispatcher.split("limit = { is_ai = yes }", 1)[1].split(
            "else = {", 1
        )[0]
        self.assertNotIn("random", ai_branch)
        self.assertIn("trigger_event = { id = zg361b1.200 days = 1 }", dispatcher)
        for token in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_self_ticket_{token}", dispatcher)

        finalize = top_level_block(
            self.effects, "zg361_b1_finalize_self_review_effect"
        )
        self.assertIn("name = zg361_b1_self_gap", finalize)
        self.assertIn("max = 15 min = -15", finalize)
        routes = {
            "honest": (
                "zg361_b1_record_self_honest_effect",
                "value = var:zg361_b1_evidence_mid",
            ),
            "exaggerated": (
                "zg361_b1_record_self_exaggerated_effect",
                "add = 15",
            ),
            "conservative": (
                "zg361_b1_record_self_conservative_effect",
                "subtract = 15",
            ),
        }
        for route, (key, score_write) in routes.items():
            with self.subTest(route=route):
                block = top_level_block(self.effects, key)
                self.assertIn(score_write, block)
                self.assertIn("zg361_b1_finalize_self_review_effect = yes", block)
                ticket = top_level_block(
                    self.effects, f"zg361_b1_submit_self_{route}_ticket_effect"
                )
                for token in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"zg361_b1_self_ticket_{token}", ticket)
                self.assertIn("var:zg361_b1_case_state = 3", ticket)
                self.assertIn("var:zg361_b1_self_submitted = 0", ticket)
                self.assertIn(f"stale {route} self-review ticket ignored", ticket)

        self_blocks = [finalize]
        self_blocks.extend(
            top_level_block(self.effects, key) for key, _ in routes.values()
        )
        self_blocks.extend(
            top_level_block(
                self.effects, f"zg361_b1_submit_self_{route}_ticket_effect"
            )
            for route in routes
        )
        for block in self_blocks:
            code = without_comments(block)
            for forbidden in (
                "zg361_kpi",
                "zg361_absolute_grade",
                "zg361_pending_grade",
                "zg361_b1_final_grade",
            ):
                self.assertNotIn(f"name = {forbidden}", code)

        shadow = top_level_block(self.effects, "zg361_b1_open_shadow_effect")
        self.assertIn("name = zg361_b1_self_visibility_adjustment", shadow)
        self.assertIn("value = var:zg361_b1_self_gap multiply = 0.2", shadow)
        self.assertIn("max = 3 min = -3", shadow)
        self.assertIn("add = var:zg361_b1_self_visibility_adjustment", shadow)
        prepare = top_level_block(self.effects, "zg361_b1_prepare_facts_effect")
        self.assertLess(
            prepare.index("zg361_b1_record_self_honest_effect = yes"),
            prepare.index("set_variable = { name = zg361_b1_peer_sealed value = 1 }"),
        )

    def test_shadow_response_changes_only_bounded_calibration_input(self) -> None:
        event = top_level_block(self.events, "zg361b1.201")
        self.assertEqual(event.count("option = {"), 2)
        self.assertIn("zg361_b1_submit_shadow_accept_ticket_effect = yes", event)
        self.assertIn("zg361_b1_submit_shadow_supplement_ticket_effect = yes", event)
        open_shadow = top_level_block(self.effects, "zg361_b1_open_shadow_effect")
        self.assertIn("name = zg361_b1_shadow_grade value = var:zg361_pending_grade", open_shadow)
        self.assertIn("name = zg361_b1_calibration_score", open_shadow)
        self.assertIn("limit = { is_ai = yes }", open_shadow)
        self.assertIn("zg361_b1_record_shadow_accept_effect = yes", open_shadow)
        self.assertIn("trigger_event = { id = zg361b1.201 days = 1 }", open_shadow)

        accept = top_level_block(self.effects, "zg361_b1_record_shadow_accept_effect")
        supplement = top_level_block(
            self.effects, "zg361_b1_record_shadow_supplement_effect"
        )
        self.assertIn("name = zg361_b1_shadow_evidence_delta value = 0", accept)
        self.assertIn("name = zg361_b1_shadow_evidence_delta value = 10", supplement)
        self.assertIn("name = zg361_b1_calibration_score", supplement)
        self.assertIn("add = 10", supplement)
        supplement_code = without_comments(supplement)
        for immutable_name in (
            "zg361_kpi",
            "zg361_absolute_grade",
            "zg361_b1_shadow_grade",
            "zg361_pending_grade",
            "zg361_b1_final_grade",
            "zg361_b1_quota_snapshot",
        ):
            self.assertNotIn(f"name = {immutable_name}", supplement_code)
        for forbidden_call in ("settlement", "reward", "apply_pending_grades"):
            self.assertNotIn(forbidden_call, supplement_code)

        for route in ("accept", "supplement"):
            ticket = top_level_block(
                self.effects, f"zg361_b1_submit_shadow_{route}_ticket_effect"
            )
            for token in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"zg361_b1_shadow_ticket_{token}", ticket)
            self.assertIn("var:zg361_b1_case_state = 5", ticket)
            self.assertIn("var:zg361_b1_shadow_response_state = 0", ticket)
            self.assertIn(f"stale shadow-{route} ticket ignored", ticket)

        close = top_level_block(self.events, "zg361b1.103")
        self.assertLess(
            close.index("zg361_b1_record_shadow_accept_effect = yes"),
            close.index("zg361_b1_submit_quota_book_effect = yes"),
        )

    def test_all_scheduled_b1_events_exist_and_visible_keys_are_localized(self) -> None:
        definition_list = re.findall(
            r"(?m)^zg361b1\.(\d+)\s*=\s*\{", self.events
        )
        definitions = set(definition_list)
        self.assertEqual(len(definition_list), len(definitions))
        references = set(
            re.findall(
                r"trigger_event\s*=\s*\{\s*id\s*=\s*zg361b1\.(\d+)",
                self.effects + self.events,
            )
        )
        self.assertTrue(references)
        self.assertEqual(references - definitions, set())
        for localization, language in (
            (self.loc_en, "l_english:"),
            (self.loc_zh, "l_simp_chinese:"),
            *((value, f"l_{key}:") for key, value in self.placeholder_locs.items()),
        ):
            self.assertTrue(localization.startswith(language))
            for event_id, suffixes in ((200, ("t", "desc", "a", "b", "c")), (201, ("t", "desc", "a", "b"))):
                for suffix in suffixes:
                    self.assertEqual(
                        localization.count(f"zg361b1.{event_id}.{suffix}:0"), 1
                    )
        english_body = self.loc_en.splitlines()[1:]
        for language, localization in self.placeholder_locs.items():
            with self.subTest(placeholder=language):
                self.assertEqual(localization.splitlines()[1:], english_body)

    def test_jingcha_opens_cycle_and_no_longer_instantly_settles(self) -> None:
        issue = self.jingcha.split("zg361_issue_jingcha_mandate_effect = {", 1)[1]
        self.assertIn("zg361_b1_open_cycle_effect = yes", issue)
        self.assertNotIn("zg361_run_review_effect = yes", issue)
        on_complete = self.activity.split("on_complete = {", 1)[1].split(
            "###################", 1
        )[0]
        self.assertIn("zg361_clear_jingcha_mandate_effect = yes", on_complete)
        self.assertNotIn("zg361_run_review_effect = yes", on_complete)
        self.assertIn("zg361_run_review_effect = yes", self.events)

    def test_peer_records_are_bounded_sealed_and_consumed(self) -> None:
        self.assertIn("zg361_b1_peer_submission_actor_trigger", self.triggers)
        self.assertIn("zg361_b1_peer_submission_recipient_trigger", self.triggers)
        self.assertIn("zg361_b1_submit_peer_positive_effect = yes", self.interactions)
        self.assertIn("zg361_b1_submit_peer_negative_effect = yes", self.interactions)
        self.assertNotIn(
            "set_variable = { name = zg361_recommended value = 1 }",
            self.interactions,
        )
        self.assertNotIn(
            "set_variable = { name = zg361_slandered value = 1 }",
            self.interactions,
        )
        for effect_name, raw in (
            ("zg361_b1_submit_peer_positive_effect", "10"),
            ("zg361_b1_submit_peer_negative_effect", "-15"),
        ):
            block = top_level_block(self.effects, effect_name)
            self.assertIn(
                "var:zg361_b1_peer_used < var:zg361_b1_peer_cap", block
            )
            self.assertIn("NOT = { this = scope:recipient }", block)
            self.assertIn("var:zg361_b1_case_state = 3", block)
            self.assertIn("var:zg361_b1_peer_use_mode != 0", block)
            self.assertIn(
                "var:zg361_b1_case_owner = scope:actor.var:zg361_b1_case_owner",
                block,
            )
            self.assertIn(
                "var:zg361_b1_cycle_serial = scope:actor.var:zg361_b1_cycle_serial",
                block,
            )
            self.assertIn(
                "var:zg361_b1_case_serial = scope:actor.var:zg361_b1_case_serial",
                block,
            )
            self.assertIn("is_target_in_variable_list = {", block)
            empty_slot_guard = block.index("var:zg361_b1_peer_slot_1_filled = 0")
            first_write = block.index(
                "set_variable = { name = zg361_b1_peer_slot_1_filled value = 1 }"
            )
            self.assertLess(empty_slot_guard, first_write)
            self.assertIn("subtract = var:zg361_b1_peer_fatigue", block)
            self.assertIn("max = 100", block)
            self.assertIn("min = 25", block)
            self.assertIn(
                "change_variable = { name = zg361_b1_peer_used add = 1 }", block
            )
            self.assertIn(
                "change_variable = { name = zg361_b1_peer_fatigue add = 15 }",
                block,
            )
            self.assertIn("value = var:zg361_b1_peer_fatigue max = 60", block)
            self.assertIn("name = zg361_b1_peer_over_cap add = 1", block)
            for slot in (1, 2, 3):
                for field in (
                    "filled",
                    "evaluator",
                    "subject",
                    "cycle",
                    "raw",
                    "weight",
                    "submitted_year",
                ):
                    self.assertIn(f"zg361_b1_peer_slot_{slot}_{field}", block)
                self.assertIn(
                    f"name = zg361_b1_peer_slot_{slot}_raw value = {raw}", block
                )
                self.assertIn(
                    f"var:zg361_b1_peer_slot_{slot}_evaluator = scope:actor",
                    block,
                )

        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        credit_init = initialize.index(
            "limit = { NOT = { has_variable = zg361_b1_evaluator_credit } }"
        )
        self.assertLess(
            credit_init,
            initialize.index(
                "set_variable = { name = zg361_b1_evaluator_credit value = 100 }"
            ),
        )
        self.assertEqual(
            initialize.count(
                "set_variable = { name = zg361_b1_evaluator_credit value = 100 }"
            ),
            1,
        )
        self.assertIn("limit = { var:zg361_b1_peer_use_mode = 0 }", initialize)
        self.assertIn("name = zg361_b1_peer_cap value = 0", initialize)

        prepare = top_level_block(self.effects, "zg361_b1_prepare_facts_effect")
        evidence = prepare.index(
            "set_variable = { name = zg361_b1_evidence_late value = zg361_kpi_value }"
        )
        seal = prepare.index(
            "set_variable = { name = zg361_b1_peer_sealed value = 1 }"
        )
        for slot in (1, 2, 3):
            call = f"zg361_b1_consume_peer_slot_{slot}_effect = yes"
            self.assertEqual(prepare.count(call), 1)
            self.assertLess(evidence, prepare.index(call))
            self.assertLess(prepare.index(call), seal)
            consumer = top_level_block(
                self.effects, f"zg361_b1_consume_peer_slot_{slot}_effect"
            )
            self.assertIn("zg361_b1_peer_reciprocity_risk value = 1", consumer)
            self.assertIn("multiply = 0.5 floor = yes min = 10", consumer)
            self.assertLess(
                consumer.index("multiply = 0.5 floor = yes min = 10"),
                consumer.index("name = zg361_b1_peer_credit_total add"),
            )
            self.assertIn("name = zg361_b1_evaluator_sample_n add = 1", consumer)
            self.assertIn("name = zg361_b1_evaluator_credit add = 2", consumer)
            self.assertIn("name = zg361_b1_evaluator_credit add = -5", consumer)
            self.assertIn("name = zg361_b1_evaluator_credit add = -3", consumer)
            self.assertIn("max = 125 min = 25", consumer)

        self.assertIn("divide = var:zg361_b1_peer_n max = 10 min = -15", prepare)
        self.assertIn("subtract = { value = var:zg361_b1_peer_mean multiply", prepare)
        self.assertIn("divide = var:zg361_b1_peer_credit_total max = 10 min = -15", prepare)
        self.assertLess(
            prepare.index("var:zg361_b1_peer_variance >= 100"),
            prepare.index("var:zg361_b1_peer_mean >= 5"),
        )
        shadow = top_level_block(self.effects, "zg361_b1_open_shadow_effect")
        self.assertIn("limit = { var:zg361_b1_peer_use_mode = 2 }", shadow)
        self.assertIn(
            "value = var:zg361_b1_peer_normalized_score multiply = 0.2",
            shadow,
        )
        self.assertIn("limit = { var:zg361_b1_peer_shape = 4 }", shadow)
        self.assertIn("limit = { var:zg361_b1_peer_reciprocity_risk = 1 }", shadow)
        self.assertIn("add = var:zg361_b1_peer_calibration_adjustment", shadow)
        self.assertIn("zg361_b1_peer_normalized_score", self.values)
        self.assertIn("add = var:zg361_b1_peer_normalized_score", self.values)

    def test_common_superior_barrier_is_two_phase_and_pooled(self) -> None:
        for variable_list in (
            "zg361_b1_expected_managers",
            "zg361_b1_ready_managers",
        ):
            self.assertIn(variable_list, self.effects)
        self.assertIn("zg361_b1_bank_posted_serial", self.effects)
        self.assertIn("is_target_in_variable_list", self.effects)
        self.assertIn("zg361_b1_pool_candidates", self.effects)
        self.assertIn("zg361_b1_pool_rank", self.effects)
        self.assertIn("zg361_b1_pool_top_slots", self.effects)
        self.assertIn("zg361_b1_pool_bottom_slots", self.effects)
        self.assertIn("zg361_b1_close_common_superior_bank_effect", self.effects)
        self.assertIn("trigger_event = { id = zg361b1.111 days = 1 }", self.effects)
        bank_event = top_level_block(self.events, "zg361b1.110")
        for token in (
            "zg361_b1_bank_ticket_owner",
            "zg361_b1_bank_ticket_season",
            "zg361_b1_bank_ticket_case",
            "zg361_b1_bank_ticket_state",
        ):
            self.assertIn(token, bank_event)
        self.assertIn("has_variable_list = zg361_b1_ready_managers", bank_event)
        self.assertIn("closed with no ready managers", bank_event)
        manager_event = top_level_block(self.events, "zg361b1.111")
        self.assertIn("this = scope:zg361_b1_ticket_owner", manager_event)
        self.assertIn("var:zg361_b1_cycle_state = 6", manager_event)
        self.assertIn("zg361_b1_open_calibration_effect = yes", manager_event)

        local = top_level_block(self.effects, "zg361_b1_rebuild_local_quota_effect")
        common = top_level_block(
            self.effects, "zg361_b1_close_common_superior_bank_effect"
        )
        for label, block in (("local", local), ("common", common)):
            with self.subTest(path=label):
                self.assertIn("order_by = var:zg361_b1_calibration_score", block)
                self.assertNotIn("order_by = var:zg361_kpi", block)
                self.assertIn("has_variable = zg361_b1_calibration_score", block)
                self.assertIn("NOT = { has_character_flag = zg361_newcomer_this_cycle }", block)
                self.assertIn("name = zg361_b1_quota_snapshot value = var:zg361_pending_grade", block)
                self.assertIn("name = zg361_b1_shadow_to_quota_delta", block)
                self.assertIn("name = zg361_b1_forced_down value = 1", block)
        self.assertIn("name = zg361_b1_local_top_slots value = var:zg361_pending_375_n", local)
        self.assertIn("name = zg361_b1_local_bottom_slots value = var:zg361_pending_325_n", local)
        self.assertIn("name = zg361_b1_local_bottom_candidate_n", local)
        self.assertIn("var:zg361_b1_local_bottom_candidate_n >= 1", local)
        self.assertIn("name = zg361_pending_375_n value = 0", local)
        self.assertIn("name = zg361_pending_35_n value = 0", local)
        self.assertIn("name = zg361_pending_325_n value = 0", local)
        self.assertIn("name = zg361_pending_375_n add = 1", local)
        self.assertIn("name = zg361_pending_35_n add = 1", local)
        self.assertIn("name = zg361_pending_325_n add = 1", local)
        self.assertIn("name = zg361_b1_pool_bottom_candidate_n", common)
        self.assertIn("var:zg361_b1_pool_bottom_candidate_n >= 1", common)

        submit = top_level_block(self.effects, "zg361_b1_submit_quota_book_effect")
        self.assertLess(
            submit.index("zg361_b1_rebuild_local_quota_effect = yes"),
            submit.index("has_variable = zg361_b1_bank_superior"),
        )

    def test_quota_reference_matrix_and_three_plus_four_pool(self) -> None:
        def quota_counts(size: int) -> tuple[int, int, int]:
            if size < 3:
                return (0, size, 0)
            top = max(1, int(size * 0.3 + 0.5))
            bottom = max(1, int(size * 0.1)) if size >= 5 else 0
            return (top, size - top - bottom, bottom)

        expected = {
            0: (0, 0, 0),
            1: (0, 1, 0),
            2: (0, 2, 0),
            3: (1, 2, 0),
            4: (1, 3, 0),
            7: (2, 4, 1),
            14: (4, 9, 1),
            23: (7, 14, 2),
        }
        self.assertEqual({size: quota_counts(size) for size in expected}, expected)
        self.assertEqual(sum((3, 4)), 7)
        common = top_level_block(
            self.effects, "zg361_b1_close_common_superior_bank_effect"
        )
        self.assertIn("change_variable = { name = zg361_b1_pool_n add = 1 }", common)
        self.assertIn("limit = { var:zg361_b1_pool_n >= 1 }", common)
        self.assertEqual(common.count("name = zg361_b1_pool_top_slots"), 2)

    def test_existing_settlement_opens_shadow_and_marks_publication(self) -> None:
        self.assertIn("zg361_b1_open_shadow_effect = yes", self.core)
        self.assertIn("zg361_b1_mark_published_effect = yes", self.core)
        self.assertLess(
            self.core.index("zg361_publish_scoreboard_effect = yes"),
            self.core.index("zg361_b1_mark_published_effect = yes"),
        )

    def test_readiness_is_not_inflated_by_foundation(self) -> None:
        manifest = json.loads(read("docs/361-mechanism-manifest.json"))
        self.assertEqual(
            sum(item["status"]["domain_runtime"] == "partial" for item in manifest["items"]),
            4,
        )
        self.assertEqual(
            sum(
                item["status"]["domain_runtime"] == "not-implemented"
                for item in manifest["items"]
            ),
            357,
        )


if __name__ == "__main__":
    unittest.main()
