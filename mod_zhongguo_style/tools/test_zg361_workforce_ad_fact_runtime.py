#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static L0 contract tests for the independent Workforce AD fact package."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_workforce_ad_fact_runtime as gen


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = MOD_ROOT / "common" / "scripted_effects" / "zg361_workforce_ad_fact_runtime_effects.txt"
EVENTS_PATH = MOD_ROOT / "events" / "zg361_workforce_ad_fact_runtime_events.txt"
SPEC_PATH = MOD_ROOT / "docs" / "361-workforce-ad-fact-runtime-spec.md"

EXPECTED_LEGACY = {
    "zg361_we_ad_external_referral_id",
    "zg361_we_ad_external_referrer",
    "zg361_we_ad_external_referral_relationship",
    "zg361_we_ad_external_referral_evidence_receipt",
    "zg361_we_ad_external_interviewer_1",
    "zg361_we_ad_external_interviewer_2",
    "zg361_we_ad_external_interviewer_3",
    "zg361_we_ad_external_vote_1",
    "zg361_we_ad_external_vote_2",
    "zg361_we_ad_external_vote_3",
    "zg361_we_ad_external_vote_evidence_1",
    "zg361_we_ad_external_vote_evidence_2",
    "zg361_we_ad_external_vote_evidence_3",
    "zg361_we_ad_external_runner_up",
    "zg361_we_ad_external_runner_up_evidence",
    "zg361_we_ad_external_refusal_reason_id",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if not match:
        raise AssertionError(f"missing top-level block {name}")
    start = match.start()
    depth = 0
    opened = False
    for index in range(match.end() - 1, len(text)):
        if text[index] == "{":
            depth += 1
            opened = True
        elif text[index] == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start:index + 1]
    raise AssertionError(f"unbalanced top-level block {name}")


class WorkforceAdFactRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)
        cls.events = read(EVENTS_PATH)
        cls.spec = read(SPEC_PATH) if SPEC_PATH.is_file() else ""

    def test_exact_sixteen_field_mapping(self) -> None:
        self.assertEqual(EXPECTED_LEGACY, set(gen.LEGACY_AD16_MAPPING))
        self.assertEqual(16, len(gen.LEGACY_AD16_MAPPING))
        self.assertEqual(16, len(set(gen.LEGACY_AD16_MAPPING.values())))
        self.assertTrue(all(value.startswith("zg361_wad_") for value in gen.LEGACY_AD16_MAPPING.values()))

    def test_generator_owns_only_new_projection_files(self) -> None:
        rendered = gen.outputs()
        self.assertEqual(11, len(rendered))
        self.assertEqual({EFFECTS_PATH, EVENTS_PATH}, {path for path in rendered if path.suffix == ".txt"})
        for path, payload in rendered.items():
            self.assertTrue(path.name.startswith("zg361_workforce_ad_fact_"))
            self.assertTrue(payload.startswith(gen.BOM))
            self.assertEqual(payload, path.read_bytes(), path)
        self.assertNotIn(
            MOD_ROOT / "tools" / "gen_361_workforce_endgame_runtime.py",
            rendered,
        )

    def test_generated_braces_are_balanced(self) -> None:
        for name, text in (("effects", self.effects), ("events", self.events)):
            self.assertEqual(text.count("{"), text.count("}"), name)

    def test_all_visible_fact_events_have_a_valid_theme(self) -> None:
        for event_id in (1, 11, 12, 13, 20):
            event = block(self.events, f"zg361wad.{event_id}")
            self.assertIn("type = character_event", event)
            self.assertIn("theme = stewardship", event)

    def test_public_entries_are_exact_case_guarded(self) -> None:
        expected = {
            "zg361_wad_begin_referral_source_effect": (1, "zg361_we_m273_object_consumed"),
            "zg361_wad_begin_panel_source_effect": (1, "zg361_we_m271_object_consumed"),
            "zg361_wad_begin_offer_response_source_effect": (4, "zg361_we_m272_object_consumed"),
        }
        for effect_name, (state, predecessor) in expected.items():
            rendered = block(self.effects, effect_name)
            for token in (
                "zg361_case_kernel_full_guard_trigger",
                "OWNER_VAR = zg361_case_ad_owner",
                "SUBJECT_VAR = zg361_case_ad_subject",
                "CYCLE_VAR = zg361_case_ad_cycle_serial",
                "CASE_VAR = zg361_case_ad_case_serial",
                "STATE_VAR = zg361_case_ad_state",
                "ACTIVE_VAR = zg361_case_ad_active",
                f"EXPECTED_STATE = {state}",
                "$TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }",
                "$TICKET_SUBJECT$ = this",
                predecessor,
            ):
                self.assertIn(token, rendered, (effect_name, token))

    def test_sources_use_pending_consumed_and_frozen_tuple(self) -> None:
        for source, state in (("referral", 1), ("panel", 1), ("offer", 4)):
            begin = block(self.effects, f"zg361_wad_begin_{source if source != 'offer' else 'offer_response'}_source_effect")
            for field in gen.SOURCE_ENVELOPES[source]:
                self.assertIn(f"zg361_wad_{source}_source_{field}", begin)
            self.assertIn(f"zg361_wad_{source}_source_state value = {state}", begin)
            self.assertIn(f"zg361_wad_{source}_source_consumed value = 0", begin)
            self.assertIn(f"zg361_wad_{source}_source_retired value = 0", begin)
            self.assertIn(f"remove_variable = zg361_wad_{source}_source_id", begin)
            self.assertIn(f"remove_variable = zg361_wad_{source}_source_hash", begin)
            self.assertRegex(begin, rf"zg361_wad_{source}_source_pending value = [01]")

    def test_referrer_is_real_distinct_and_relational(self) -> None:
        selector = block(self.effects, "zg361_wad_select_real_referrer_effect")
        self.assertIn("ordered_close_family_member = {", selector)
        self.assertIn("ordered_relation = {", selector)
        self.assertIn("type = friend", selector)
        self.assertIn("liege = scope:zg361_wad_referral_owner_scope", selector)
        self.assertGreaterEqual(selector.count("zg361_is_celestial_liege_trigger = yes"), 3)
        self.assertIn("NOT = { var:zg361_wad_referral_source_referrer = this }", selector)
        self.assertIn("referral_source_disposition value = 3", selector)
        self.assertNotIn("create_character", selector)

    def test_referral_receipts_exist_only_after_actor_submission(self) -> None:
        dispatch = block(self.effects, "zg361_wad_dispatch_referral_response_effect")
        submit = block(self.effects, "zg361_wad_submit_referral_effect")
        decline = block(self.effects, "zg361_wad_decline_referral_effect")
        event = block(self.events, "zg361wad.1")
        self.assertIn("is_ai = no", event)
        self.assertIn("this = scope:zg361_wad_referral_actor_scope", event)
        self.assertIn("zg361_wad_submit_referral_effect", event)
        self.assertIn("zg361_wad_decline_referral_effect", event)
        self.assertIn("if = { limit = { is_ai = no } trigger_event = { id = zg361wad.1 } }", dispatch)
        self.assertIn("else = {", dispatch)
        self.assertEqual(3, submit.count("change_variable = { name = zg361_wad_receipt_serial add = 1 }"))
        self.assertLess(submit.index("change_variable = { name = zg361_wad_receipt_serial add = 1 }"), submit.index("referral_source_referral_id value"))
        self.assertLess(submit.index("referral_source_id value"), submit.index("referral_source_pending value = 1"))
        self.assertLess(submit.index("referral_source_hash value"), submit.index("referral_source_pending value = 1"))
        self.assertIn("referral_source_disposition value = 1", submit)
        self.assertIn("referral_source_disposition value = 2", decline)
        self.assertIn("referral_source_id value", decline)
        self.assertIn("referral_source_hash value", decline)
        self.assertNotIn("referral_source_referral_id value", decline)

    def test_panel_requires_three_distinct_celestial_managers(self) -> None:
        freeze = block(self.effects, "zg361_wad_freeze_real_panel_effect")
        for slot in (1, 2, 3):
            selector = block(self.effects, f"zg361_wad_select_panel_slot_{slot}_effect")
            self.assertIn("zg361_is_celestial_liege_trigger = yes", selector)
            self.assertIn("NOT = { this = scope:zg361_wad_panel_subject_scope }", selector)
            self.assertIn("NOT = { this = scope:zg361_wad_panel_referrer_scope }", selector)
            self.assertIn(f"panel_source_interviewer_{slot}", freeze)
        for left, right in ((1, 2), (1, 3), (2, 3)):
            self.assertIn(
                f"NOT = {{ var:zg361_wad_panel_source_interviewer_{left} = var:zg361_wad_panel_source_interviewer_{right} }}",
                freeze,
            )
        self.assertIn("panel_source_disposition value = 3", freeze)
        self.assertEqual(1, freeze.count("remove_variable = zg361_wad_panel_source_interviewer_1"))
        self.assertNotIn("value = this", "\n".join(
            line for line in freeze.splitlines() if "panel_source_interviewer_" in line and "set_variable" in line
        ))

    def test_referrer_recusal_or_real_vote_is_enforced(self) -> None:
        freeze = block(self.effects, "zg361_wad_freeze_real_panel_effect")
        slot_one = block(self.effects, "zg361_wad_select_panel_slot_1_effect")
        self.assertIn("panel_source_referrer_vote_policy = 1", slot_one)
        self.assertIn("panel_source_interviewer_1 value = var:zg361_wad_panel_source_referrer", slot_one)
        self.assertIn("panel_source_referrer_vote_policy = 0", freeze)
        for slot in (1, 2, 3):
            self.assertIn(
                f"NOT = {{ var:zg361_wad_panel_source_interviewer_{slot} = var:zg361_wad_panel_source_referrer }}",
                freeze,
            )
        self.assertIn(
            "trigger_else = { var:zg361_wad_panel_source_interviewer_1 = var:zg361_wad_panel_source_referrer }",
            freeze,
        )

    def test_runner_up_is_a_real_distinct_reviewable_vassal_or_absent(self) -> None:
        freeze = block(self.effects, "zg361_wad_freeze_real_panel_effect")
        self.assertIn("ordered_vassal = {", freeze)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", freeze)
        self.assertIn("NOT = { this = scope:zg361_wad_panel_subject_scope }", freeze)
        for slot in (1, 2, 3):
            self.assertIn(f"NOT = {{ this = scope:zg361_wad_panel_i{slot}_scope }}", freeze)
        exists = freeze.index("limit = { exists = scope:zg361_wad_runner_up_scope }")
        write_character = freeze.index("panel_source_runner_up value = scope:zg361_wad_runner_up_scope")
        allocate = freeze.index("name = zg361_wad_runner_up_receipt_value")
        write_evidence = freeze.index("panel_source_runner_up_evidence value = scope:zg361_wad_runner_up_receipt_value")
        self.assertLess(exists, write_character)
        self.assertLess(write_character, allocate)
        self.assertLess(allocate, write_evidence)
        self.assertIn("panel_runner_up_present value = 0", freeze)

    def test_each_human_interviewer_gets_own_visible_vote_event(self) -> None:
        dispatch = block(self.effects, "zg361_wad_dispatch_next_vote_effect")
        for slot in (1, 2, 3):
            event = block(self.events, f"zg361wad.{10 + slot}")
            self.assertIn("is_ai = no", event)
            self.assertIn("this = scope:zg361_wad_panel_actor_scope", event)
            self.assertIn(f"panel_source_interviewer_{slot} = root", event)
            self.assertIn(f"zg361_wad_submit_panel_vote_{slot}_effect", event)
            self.assertIn(f"trigger_event = {{ id = zg361wad.{10 + slot} }}", dispatch)
            for vote in (1, 2, 3):
                self.assertIn(f"VOTE = {vote}", event)

    def test_each_ai_interviewer_casts_from_own_actor_scope(self) -> None:
        for slot in (1, 2, 3):
            ai = block(self.effects, f"zg361_wad_resolve_ai_panel_vote_{slot}_effect")
            self.assertIn("is_ai = yes", ai)
            self.assertIn("this = scope:zg361_wad_panel_actor_scope", ai)
            self.assertIn("save_temporary_scope_as = zg361_wad_panel_ai_actor_scope", ai)
            self.assertIn(f"zg361_wad_submit_panel_vote_{slot}_effect", ai)
            self.assertIn("VOTER = scope:zg361_wad_panel_ai_actor_scope VOTE = 3", ai)
            self.assertIn("VOTER = scope:zg361_wad_panel_ai_actor_scope VOTE = 2", ai)
            self.assertIn("VOTER = scope:zg361_wad_panel_ai_actor_scope VOTE = 1", ai)

    def test_votes_are_serial_one_shot_actor_bound_receipts(self) -> None:
        finalize = block(self.effects, "zg361_wad_finalize_panel_source_effect")
        for slot in (1, 2, 3):
            vote = block(self.effects, f"zg361_wad_submit_panel_vote_{slot}_effect")
            self.assertIn(f"panel_vote_count = {slot - 1}", vote)
            self.assertIn(f"panel_source_interviewer_{slot} = $VOTER$", vote)
            self.assertIn(f"NOT = {{ has_variable = zg361_wad_panel_source_vote_{slot} }}", vote)
            self.assertIn(f"NOT = {{ has_variable = zg361_wad_panel_source_vote_evidence_{slot} }}", vote)
            self.assertIn("$VOTE$ >= 1", vote)
            self.assertIn("$VOTE$ <= 3", vote)
            self.assertEqual(1, vote.count("change_variable = { name = zg361_wad_receipt_serial add = 1 }"))
            self.assertIn(f"panel_vote_receipt_actor_{slot} value = $VOTER$", vote)
            self.assertIn(
                f"panel_vote_receipt_actor_{slot} = var:zg361_wad_panel_source_interviewer_{slot}",
                finalize,
            )
        self.assertIn("panel_vote_count = 3", finalize)
        self.assertIn("panel_source_pending value = 1", finalize)
        self.assertIn("panel_source_disposition value = 1", finalize)

    def test_offer_refusal_is_subject_owned_and_reason_bounded(self) -> None:
        begin = block(self.effects, "zg361_wad_begin_offer_response_source_effect")
        event = block(self.events, "zg361wad.20")
        accept = block(self.effects, "zg361_wad_accept_offer_effect")
        refuse = block(self.effects, "zg361_wad_refuse_offer_effect")
        self.assertIn("if = { limit = { is_ai = no } trigger_event = { id = zg361wad.20 } }", begin)
        self.assertIn("else = { zg361_wad_accept_offer_effect = { RESPONDENT = this } }", begin)
        self.assertIn("is_ai = no", event)
        self.assertIn("offer_source_subject = this", event)
        self.assertIn("RESPONDENT = this REASON = 1", event)
        self.assertIn("RESPONDENT = this REASON = 2", event)
        self.assertIn("RESPONDENT = this REASON = 3", event)
        self.assertIn("$RESPONDENT$ = this", accept)
        self.assertIn("offer_source_response value = 1", accept)
        self.assertIn("$REASON$ >= 1", refuse)
        self.assertIn("$REASON$ <= 3", refuse)
        self.assertIn("offer_source_refusal_reason_id value = $REASON$", refuse)
        self.assertIn("offer_source_response value = 2", refuse)

    def test_fact_package_never_changes_world_or_workforce_resources(self) -> None:
        forbidden = (
            "create_character",
            "appoint_court_position",
            "replace_court_position",
            "change_liege",
            "add_gold",
            "remove_short_term_gold",
            "zg361_ch_hc_available add",
            "zg361_ch_hc_reserved add",
            "zg361_ch_hc_occupied add",
            "zg361_ch_hc_frozen add",
        )
        for token in forbidden:
            self.assertNotIn(token, self.effects)

    def test_old_external_aliases_are_not_written_or_read(self) -> None:
        for legacy in EXPECTED_LEGACY:
            self.assertNotIn(legacy, self.effects)
            self.assertNotIn(legacy, self.events)
        for source in ("referral", "panel", "offer"):
            self.assertIn(f"zg361_wad_{source}_source_id", self.effects)
            self.assertIn(f"zg361_wad_{source}_source_hash", self.effects)
            self.assertIn(
                f"zg361_we_resume_m{ {'referral': 271, 'panel': 267, 'offer': 274}[source] }_from_{source}_source_effect",
                self.effects,
            )

    def test_localization_is_complete_and_daily_placeholders_are_english(self) -> None:
        expected_keys = {f"zg361wad.{key}" for key in gen.LOCALIZATION_EN}
        for language in gen.LANGUAGES:
            path = MOD_ROOT / "localization" / language / f"zg361_workforce_ad_fact_l_{language}.yml"
            text = read(path)
            self.assertTrue(text.startswith(f"l_{language}:\n"))
            keys = set(re.findall(r"(?m)^ ([^:]+):0 ", text))
            self.assertEqual(expected_keys, keys, language)
            if language not in ("english", "simp_chinese"):
                self.assertEqual(gen.render_localization("english").split(b"\n", 1)[1], path.read_bytes().split(b"\n", 1)[1])

    def test_spec_freezes_core_wiring_and_role_boundary(self) -> None:
        for token in (
            "core-wired static-ready / not live",
            "zg361_wad_begin_referral_source_effect",
            "zg361_wad_begin_panel_source_effect",
            "zg361_wad_begin_offer_response_source_effect",
            "pending=0, consumed=1",
            "pending=0, retired=1",
            "#271 B",
            "#267",
            "伯爵/男爵",
            "公爵及以上",
            "不得把 subject 填进 interviewer",
            "同一 subject 的后续新案",
        ):
            self.assertIn(token, self.spec)


if __name__ == "__main__":
    unittest.main()
