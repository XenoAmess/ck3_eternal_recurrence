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

from gen_361_b1_runtime import (
    EFFECT_BLOCK_COUNTS,
    EFFECT_SPLIT_KEY,
    HEADER,
    MOD_ROOT,
    generated,
    outputs,
    render_effects,
)
from zg361_b1_quota_model import compute_quota
from zg361_b1_runtime_data import B1_BINDINGS, B1_IDS, STAGE_SEQUENCE


def read(relative: str) -> str:
    return (MOD_ROOT / relative).read_text(encoding="utf-8-sig")


B1_EFFECT_FILES = (
    "common/scripted_effects/zg361_b1_runtime_effects.txt",
    "common/scripted_effects/zg361_b1_runtime_effects_part2.txt",
)


def read_b1_effects() -> str:
    return "\n".join(read(relative) for relative in B1_EFFECT_FILES)


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
        cls.effect_parts = tuple(read(relative) for relative in B1_EFFECT_FILES)
        cls.effects = "\n".join(cls.effect_parts)
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
        cls.case_kernel_triggers = read(
            "common/scripted_triggers/zg361_case_kernel_triggers.txt"
        )
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

    def test_effect_split_boundary_uniqueness_counts_and_identity(self) -> None:
        keys_by_part = tuple(
            tuple(re.findall(r"(?m)^(zg361_b1_[A-Za-z0-9_]+)\s*=\s*\{", part))
            for part in self.effect_parts
        )
        self.assertEqual(tuple(map(len, keys_by_part)), EFFECT_BLOCK_COUNTS)
        self.assertEqual(keys_by_part[1][0], EFFECT_SPLIT_KEY)
        self.assertNotIn(EFFECT_SPLIT_KEY, keys_by_part[0])
        all_keys = keys_by_part[0] + keys_by_part[1]
        self.assertEqual(len(all_keys), 78)
        self.assertEqual(len(set(all_keys)), 78)

        bodies = []
        for relative in B1_EFFECT_FILES:
            payload = (MOD_ROOT / relative).read_bytes()
            text = payload.decode("utf-8-sig")
            self.assertTrue(text.startswith(HEADER), relative)
            bodies.append(text.removeprefix(HEADER))
        reconstructed = generated(
            bodies[0].rstrip() + "\n\n" + bodies[1].lstrip()
        )
        self.assertEqual(reconstructed, render_effects())

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

    def test_delayed_event_variable_lists_have_loader_visible_write_anchors(self) -> None:
        """Freeze the Jomini event/list registration boundary seen in live CK3.

        A write that exists only in a scripted effect does not satisfy the
        loader when a loaded event directly reads the same variable list.
        CK3 1.19.0.6 also ignores an event-root write hidden behind
        ``always = no`` or reverted before its consumer. A ``flag:`` enum is
        not an object setter for a list consumed as character scopes. The
        event-root character must therefore be saved as a temporary scope,
        remain in the list through the business read, be excluded from
        character-only work, and only then restore membership and container
        existence.
        """

        subjects = top_level_block(self.events, "zg361b1.103")
        subject_target = "zg361_b1_subjects"
        subject_had = f"{subject_target}_event_loader_had_list"
        subject_anchor_name = f"{subject_target}_event_loader_anchor"
        subject_anchor = f"scope:{subject_anchor_name}"
        subject_add = (
            f"add_to_variable_list = {{ name = {subject_target} "
            f"target = {subject_anchor} }}"
        )
        subject_remove = (
            f"remove_list_variable = {{ name = {subject_target} "
            f"target = {subject_anchor} }}"
        )
        subject_clear = f"clear_variable_list = {subject_target}"
        subject_record = (
            f"\t\tsave_temporary_scope_as = {subject_anchor_name}\n"
            f"\t\tremove_character_flag = {subject_had}\n"
            f"\t\tif = {{\n"
            f"\t\t\tlimit = {{ has_variable_list = {subject_target} }}\n"
            f"\t\t\tadd_character_flag = {subject_had}\n"
            f"\t\t}}\n"
            f"\t\t{subject_add}"
        )
        subject_cleanup = re.compile(
            rf"{re.escape(subject_remove)}\s+"
            rf"if = \{{\s+"
            rf"limit = \{{ NOT = \{{ has_character_flag = {subject_had} \}} \}}\s+"
            rf"{re.escape(subject_clear)}\s+"
            rf"\}}\s+remove_character_flag = {subject_had}"
        )
        self.assertNotIn("always = no", subjects)
        self.assertNotIn(f"target = flag:{subject_anchor_name}", subjects)
        self.assertIn(subject_record, subjects)
        self.assertIn(
            "variable = zg361_b1_subjects\n"
            "\t\t\t\t\tlimit = { NOT = { this = "
            f"{subject_anchor} }} }}",
            subjects,
        )
        subject_read = subjects.index("variable = zg361_b1_subjects")
        subject_first_cleanup = subjects.index(subject_remove)
        self.assertLess(subjects.index(subject_add), subject_read)
        self.assertLess(subject_read, subject_first_cleanup)
        self.assertLess(
            subject_first_cleanup,
            subjects.index("zg361_b1_submit_quota_book_effect = yes"),
        )
        self.assertEqual(subjects.count(subject_add), 1)
        self.assertEqual(subjects.count(subject_remove), 3)
        self.assertEqual(subjects.count(subject_clear), 3)
        self.assertEqual(len(subject_cleanup.findall(subjects)), 3)

        ready = top_level_block(self.events, "zg361b1.110")
        ready_target = "zg361_b1_ready_managers"
        ready_had = f"{ready_target}_event_loader_had_list"
        ready_anchor_name = f"{ready_target}_event_loader_anchor"
        ready_anchor = f"scope:{ready_anchor_name}"
        ready_add = (
            f"add_to_variable_list = {{ name = {ready_target} "
            f"target = {ready_anchor} }}"
        )
        ready_remove = (
            f"remove_list_variable = {{ name = {ready_target} "
            f"target = {ready_anchor} }}"
        )
        ready_clear = f"clear_variable_list = {ready_target}"
        ready_record = (
            f"\t\tsave_temporary_scope_as = {ready_anchor_name}\n"
            f"\t\tremove_character_flag = {ready_had}\n"
            f"\t\tif = {{\n"
            f"\t\t\tlimit = {{ has_variable_list = {ready_target} }}\n"
            f"\t\t\tadd_character_flag = {ready_had}\n"
            f"\t\t}}\n"
            f"\t\t{ready_add}"
        )
        ready_business_gate = (
            f"\t\t\t\t\tlimit = {{\n"
            f"\t\t\t\t\t\thas_character_flag = {ready_had}\n"
            f"\t\t\t\t\t\thas_variable_list = {ready_target}\n"
            f"\t\t\t\t\t}}"
        )
        ready_cleanup = re.compile(
            rf"{re.escape(ready_remove)}\s+"
            rf"if = \{{\s+"
            rf"limit = \{{ NOT = \{{ has_character_flag = {ready_had} \}} \}}\s+"
            rf"{re.escape(ready_clear)}\s+"
            rf"\}}\s+remove_character_flag = {ready_had}"
        )
        self.assertNotIn("always = no", ready)
        self.assertNotIn(f"target = flag:{ready_anchor_name}", ready)
        self.assertIn(ready_record, ready)
        self.assertIn(ready_business_gate, ready)
        ready_gate = ready.index(ready_business_gate)
        ready_close_cleanup = ready.index(ready_remove, ready_gate)
        ready_close = ready.index("zg361_b1_close_common_superior_bank_effect = yes")
        self.assertLess(ready.index(ready_add), ready_gate)
        self.assertLess(ready_gate, ready_close_cleanup)
        self.assertLess(ready_close_cleanup, ready_close)
        self.assertIn(
            f"{ready_remove}\n"
            f"\t\t\t\t\tremove_character_flag = {ready_had}\n"
            "\t\t\t\t\tzg361_b1_close_common_superior_bank_effect = yes",
            ready,
        )
        self.assertEqual(ready.count(ready_add), 1)
        self.assertEqual(ready.count(ready_remove), 4)
        self.assertEqual(ready.count(ready_clear), 3)
        self.assertEqual(len(ready_cleanup.findall(ready)), 3)

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
                self.assertIn("var:zg361_b1_case_subject = this", ticket)
                self.assertIn("var:zg361_b1_case_state = 3", ticket)
                self.assertIn("var:zg361_b1_case_active = 1", ticket)
                self.assertIn("var:zg361_b1_roster_included = 1", ticket)
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
        self.assertIn(
            "value = var:zg361_b1_self_gap multiply = -0.2 round = yes max = 0 min = -3",
            shadow,
        )
        self.assertIn(
            "value = var:zg361_b1_self_gap multiply = 0.1 round = yes max = 0 min = -2",
            shadow,
        )
        self.assertNotIn(
            "value = var:zg361_b1_self_gap multiply = 0.2", shadow
        )
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
        self.assertIn(
            "name = zg361_b1_shadow_new_evidence_baseline_score value = var:zg361_b1_evidence_late",
            open_shadow,
        )
        self.assertIn(
            "name = zg361_b1_shadow_new_evidence_observed_score value = zg361_kpi_value",
            supplement,
        )
        self.assertIn(
            "subtract = var:zg361_b1_shadow_new_evidence_baseline_score max = 10 min = -10",
            supplement,
        )
        self.assertNotIn("subtract = var:zg361_b1_evidence_mid", supplement)
        self.assertNotIn("subtract = var:zg361_b1_evidence_late", supplement)
        self.assertIn("NOT = { var:zg361_b1_shadow_evidence_delta = 0 }", supplement)
        self.assertIn("name = zg361_b1_shadow_evidence_object_available value = 1", supplement)
        self.assertIn("name = zg361_b1_shadow_evidence_revision value = 1", supplement)
        self.assertIn("name = zg361_b1_shadow_new_evidence_source value = 1", supplement)
        self.assertIn("name = zg361_b1_shadow_new_evidence value = 1", supplement)
        self.assertIn("name = zg361_b1_calibration_score", supplement)
        self.assertIn("add = var:zg361_b1_shadow_evidence_delta", supplement)
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
            self.assertIn("var:zg361_b1_case_subject = this", ticket)
            self.assertIn("var:zg361_b1_case_state = 5", ticket)
            self.assertIn("var:zg361_b1_case_active = 1", ticket)
            self.assertIn("var:zg361_b1_roster_included = 1", ticket)
            self.assertIn("var:zg361_b1_shadow_response_state = 0", ticket)
            self.assertIn(f"stale shadow-{route} ticket ignored", ticket)

        close = top_level_block(self.events, "zg361b1.103")
        self.assertLess(
            close.index("zg361_b1_record_shadow_accept_effect = yes"),
            close.index("zg361_b1_submit_quota_book_effect = yes"),
        )

    def test_blind_named_list_uses_a_real_character_anchor_only_as_container(self) -> None:
        blind = top_level_block(
            self.effects, "zg361_b1_freeze_blind_named_diff_effect"
        )
        list_name = "zg361_b1_blind_named_candidates"
        anchor = "zg361_b1_blind_named_manager"

        # add_to_list/list is an event-target list.  Mixing in variable-list
        # existence or clear effects recreates the loader warning and does not
        # initialize the transient character container.
        self.assertNotIn(f"has_variable_list = {list_name}", blind)
        self.assertNotIn(f"clear_variable_list = {list_name}", blind)
        anchor_save = blind.index(f"save_temporary_scope_as = {anchor}")
        anchor_add = blind.index(f"add_to_list = {list_name}", anchor_save)
        subject_walk = blind.index("every_in_list = {", anchor_add)
        self.assertLess(anchor_save, anchor_add)
        self.assertLess(anchor_add, subject_walk)
        self.assertEqual(blind.count(f"add_to_list = {list_name}"), 2)

        # The manager object keeps even a zero-candidate list loadable, but it
        # must not receive a blind/named rank or advance either cursor.
        exclusion = f"limit = {{ NOT = {{ this = scope:{anchor} }} }}"
        reader = f"\n\t\tlist = {list_name}\n"
        self.assertEqual(blind.count(reader), 2)
        self.assertEqual(blind.count(exclusion), 2)
        self.assertNotIn("change_variable", blind[anchor_add:subject_walk])

        # Keep the anchor until both ordered readers have completed, then
        # remove that exact character unconditionally.
        cleanup = (
            f"scope:{anchor} = {{\n"
            f"\t\tremove_from_list = {list_name}\n"
            "\t}"
        )
        self.assertEqual(blind.count(cleanup), 1)
        self.assertGreater(blind.index(cleanup), blind.rindex(reader))

    def test_135_shadow_routes_have_stable_objects_and_honest_receipts(self) -> None:
        open_shadow = top_level_block(self.effects, "zg361_b1_open_shadow_effect")
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        supplement = top_level_block(
            self.effects, "zg361_b1_record_shadow_supplement_effect"
        )
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )

        for field in ("owner", "subject", "cycle", "case", "state"):
            with self.subTest(object="shadow", field=field):
                self.assertIn(f"zg361_b1_shadow_object_{field}", open_shadow)
            with self.subTest(object="supplement", field=field):
                self.assertIn(
                    f"zg361_b1_shadow_evidence_object_{field}", supplement
                )

        # A exposes the non-final object, B reveals the same frozen object only
        # at publication, and C is represented solely by the policy choice.
        self.assertIn("root.var:zg361_b1_m135_mode != 3", open_shadow)
        self.assertIn("root.var:zg361_b1_m135_mode = 1", open_shadow)
        self.assertIn("name = zg361_b1_shadow_reveal_state value = 1", open_shadow)
        self.assertIn(
            "root.var:zg361_b1_m135_mode = 2 var:zg361_b1_shadow_object_available = 1",
            publish,
        )
        self.assertIn("name = zg361_b1_shadow_reveal_state value = 2", publish)
        self.assertEqual(
            open_shadow.count(
                "set_variable = { name = zg361_b1_m135_receipt_serial"
            ),
            1,
        )
        self.assertIn(
            "name = zg361_b1_m135_receipt_serial value = var:zg361_b1_shadow_object_case",
            open_shadow,
        )
        self.assertLess(
            open_shadow.index("root.var:zg361_b1_m135_mode != 3"),
            open_shadow.index("name = zg361_b1_m135_receipt_serial"),
        )
        self.assertIn("remove_variable = zg361_b1_m135_receipt_serial", initialize)
        for prefix in (
            "zg361_b1_shadow_object",
            "zg361_b1_shadow_evidence_object",
        ):
            for field in ("owner", "subject", "cycle", "case", "state"):
                with self.subTest(reset=prefix, field=field):
                    self.assertRegex(
                        initialize,
                        rf"(?:remove_variable = {prefix}_{field}|"
                        rf"set_variable = \{{ name = {prefix}_{field} value = 0 \}})",
                    )

        # The supplement packet is created only for a non-zero observation,
        # is immediately consumed, and cannot itself mutate a frozen grade.
        self.assertIn("name = zg361_b1_shadow_evidence_object_state value = 2", supplement)
        self.assertIn("name = zg361_b1_shadow_evidence_consumed value = 1", supplement)
        self.assertIn("add = var:zg361_b1_shadow_evidence_delta", supplement)
        self.assertIn(
            "var:zg361_b1_shadow_new_evidence = 1 var:zg361_b1_shadow_evidence_delta < 0",
            publish,
        )
        self.assertIn("name = zg361_b1_feedback_debt value = 1", publish)
        supplement_code = without_comments(supplement)
        for forbidden in (
            "name = zg361_kpi",
            "name = zg361_absolute_grade",
            "name = zg361_pending_grade",
            "name = zg361_b1_shadow_grade",
            "name = zg361_b1_final_grade",
        ):
            self.assertNotIn(forbidden, supplement_code)

    def test_136_huddle_host_and_attendee_namespaces_do_not_collide(self) -> None:
        prepare = top_level_block(
            self.effects, "zg361_b1_prepare_bank_huddle_effect"
        )
        finalize = top_level_block(
            self.effects, "zg361_b1_finalize_huddle_diff_effect"
        )

        for prefix in ("zg361_b1_huddle_host", "zg361_b1_huddle_attendee"):
            for field in ("owner", "subject", "cycle", "case", "state"):
                with self.subTest(prefix=prefix, field=field):
                    self.assertIn(f"{prefix}_{field}", prepare)

        legacy_singletons = re.compile(
            r"\bzg361_b1_huddle_(?:object_available|owner|subject|cycle|case|"
            r"state|id|attending|route|seat|ack_posted|ack_n|attendee_n|"
            r"manager_[1-4])\b"
        )
        self.assertIsNone(legacy_singletons.search(prepare + finalize))

        # Route C and a bank with fewer than three managers must leave neither
        # a stale object nor a stale success receipt behind.
        self.assertIn("remove_variable = zg361_b1_m136_receipt_serial", prepare)
        for prefix in ("zg361_b1_huddle_host", "zg361_b1_huddle_attendee"):
            for field in ("owner", "subject", "cycle", "case"):
                with self.subTest(reset=prefix, field=field):
                    self.assertRegex(
                        prepare,
                        rf"(?:remove_variable = {prefix}_{field}|"
                        rf"set_variable = \{{ name = {prefix}_{field} value = 0 \}})",
                    )
        self.assertIn("var:zg361_b1_bank_m136_mode != 3", prepare)
        self.assertIn("var:zg361_b1_ready_manager_n >= 3", prepare)
        self.assertEqual(
            prepare.count(
                "set_variable = { name = zg361_b1_m136_receipt_serial"
            ),
            1,
        )
        self.assertIn(
            "name = zg361_b1_m136_receipt_serial value = var:zg361_b1_huddle_host_case",
            prepare,
        )

    def test_136_huddle_routes_order_and_real_diff_consumer_are_frozen(self) -> None:
        prepare = top_level_block(
            self.effects, "zg361_b1_prepare_bank_huddle_effect"
        )
        finalize = top_level_block(
            self.effects, "zg361_b1_finalize_huddle_diff_effect"
        )

        # Manager arrival order is frozen once and is the sole seat order;
        # manager-local case serials are not a globally unique tie breaker.
        self.assertIn(
            "name = zg361_b1_bank_ready_order value = root.var:zg361_b1_ready_manager_n",
            self.effects,
        )
        self.assertIn(
            "order_by = { value = var:zg361_b1_bank_ready_order multiply = -1 }",
            prepare,
        )
        self.assertNotIn("order_by = var:zg361_b1_case_serial", prepare)
        self.assertIn("name = zg361_b1_huddle_attendee_seat", prepare)

        # A freezes one boundary recommendation per attendee; B freezes the
        # whole preallocation. Both are later compared with the formal book.
        self.assertIn("root.var:zg361_b1_bank_m136_mode = 1", prepare)
        self.assertIn("max = 1", prepare)
        self.assertIn("name = zg361_b1_huddle_attendee_boundary_case_n", prepare)
        self.assertIn("name = zg361_b1_huddle_attendee_preallocation_top", prepare)
        self.assertIn("name = zg361_b1_huddle_attendee_preallocation_middle", prepare)
        self.assertIn("name = zg361_b1_huddle_attendee_preallocation_bottom", prepare)
        self.assertIn(
            "name = zg361_b1_huddle_attendee_cycle value = root.var:zg361_b1_huddle_host_cycle",
            prepare,
        )
        self.assertIn(
            "name = zg361_b1_huddle_attendee_case value = root.var:zg361_b1_huddle_host_case",
            prepare,
        )
        self.assertIn(
            "order_by = { value = var:zg361_b1_calibration_score multiply = 1000 subtract = var:zg361_b1_roster_frozen_order }",
            prepare,
        )

        for field in ("owner", "subject", "cycle", "case", "state"):
            with self.subTest(finalizer="attendee", field=field):
                self.assertIn(f"var:zg361_b1_huddle_attendee_{field}", finalize)
            with self.subTest(finalizer="host", field=field):
                self.assertIn(f"var:zg361_b1_huddle_host_{field}", finalize)
        self.assertIn(
            "var:zg361_b1_huddle_host_id = prev.var:zg361_b1_huddle_attendee_id",
            finalize,
        )
        for relation in (
            "var:zg361_b1_huddle_host_owner = this",
            "var:zg361_b1_huddle_host_subject = this",
            "var:zg361_b1_huddle_host_cycle = prev.var:zg361_b1_huddle_attendee_cycle",
            "var:zg361_b1_huddle_host_case = prev.var:zg361_b1_huddle_attendee_case",
            "var:zg361_b1_huddle_host_state = 1",
        ):
            self.assertIn(relation, finalize)
        self.assertIn("name = zg361_b1_huddle_assignment_state value = 2", finalize)
        self.assertIn("name = zg361_b1_huddle_grade_diff", finalize)
        self.assertIn("name = zg361_b1_huddle_attendee_ack_posted value = 1", finalize)
        self.assertIn("name = zg361_b1_huddle_host_state value = 2", finalize)

    def test_137_agenda_header_and_item_objects_are_isolated(self) -> None:
        build = top_level_block(
            self.effects, "zg361_b1_build_agenda_and_attention_effect"
        )
        finalize = top_level_block(
            self.effects, "zg361_b1_finalize_agenda_audit_effect"
        )
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )

        for prefix in ("zg361_b1_agenda_header", "zg361_b1_agenda_item"):
            for field in ("owner", "subject", "cycle", "case", "state"):
                with self.subTest(prefix=prefix, field=field):
                    self.assertIn(f"{prefix}_{field}", build)
                    self.assertIn(f"var:{prefix}_{field}", finalize)

        legacy_singletons = re.compile(
            r"\bzg361_b1_agenda_object_(?:available|owner|subject|cycle|case|state)\b"
        )
        self.assertIsNone(legacy_singletons.search(build + finalize))

        for field in ("owner", "subject", "cycle", "case"):
            with self.subTest(reset="header", field=field):
                self.assertRegex(
                    build,
                    rf"(?:remove_variable = zg361_b1_agenda_header_{field}|"
                    rf"set_variable = \{{ name = zg361_b1_agenda_header_{field} value = 0 \}})",
                )
            with self.subTest(reset="item", field=field):
                self.assertRegex(
                    initialize,
                    rf"(?:remove_variable = zg361_b1_agenda_item_{field}|"
                    rf"set_variable = \{{ name = zg361_b1_agenda_item_{field} value = 0 \}})",
                )
        self.assertIn("name = zg361_b1_agenda_header_state value = 0", build)
        self.assertIn("name = zg361_b1_agenda_item_state value = 0", initialize)

    def test_137_agenda_routes_have_stable_order_real_consumers_and_no_fake_receipt(self) -> None:
        build = top_level_block(
            self.effects, "zg361_b1_build_agenda_and_attention_effect"
        )
        finalize = top_level_block(
            self.effects, "zg361_b1_finalize_agenda_audit_effect"
        )
        pending = top_level_block(
            self.effects, "zg361_b1_open_pending_slots_effect"
        )
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )

        self.assertIn("var:zg361_b1_m137_mode != 3", build)
        self.assertIn("zg361_b1_agenda_header_object_available value = 1", build)
        self.assertIn("zg361_b1_agenda_item_object_available value = 1", build)
        self.assertEqual(
            build.count(
                "set_variable = { name = zg361_b1_m137_receipt_serial"
            ),
            1,
        )
        self.assertIn(
            "name = zg361_b1_m137_receipt_serial value = var:zg361_b1_agenda_item_case",
            build,
        )
        self.assertLess(
            build.index("root.var:zg361_b1_m137_mode != 3"),
            build.index("name = zg361_b1_m137_receipt_serial"),
        )
        self.assertIn("remove_variable = zg361_b1_m137_receipt_serial", initialize)

        # A uses frozen roster rotation. B may privilege only explicitly
        # strategic/allied cases and uses roster order as its deterministic tie.
        self.assertIn("var:zg361_b1_agenda_mode = 1", build)
        self.assertIn("var:zg361_b1_roster_frozen_order subtract", build)
        self.assertIn("var:zg361_b1_agenda_mode = 2", build)
        self.assertNotIn("var:zg361_b1_role_code >= 1", build)
        self.assertIn("var:zg361_b1_role_code >= 3", build)
        self.assertIn("has_relation_friend = scope:zg361_b1_agenda_manager", build)
        self.assertIn(
            "value = var:zg361_b1_calibration_score multiply = 1000 subtract = var:zg361_b1_roster_frozen_order",
            build,
        )
        self.assertIn("order_by = var:zg361_b1_agenda_sort_key", build)

        # Attention is the gameplay consumer: only reviewed items enter the
        # pending/milestone consumer. The finalizer closes reviewed and skipped
        # items separately and records an auditable header summary.
        self.assertIn("var:zg361_b1_attention_consumed = 1", pending)
        for reset in (
            "zg361_b1_agenda_reviewed_n",
            "zg361_b1_agenda_changed_n",
            "zg361_b1_agenda_review_minutes",
            "zg361_b1_agenda_skipped_n",
        ):
            self.assertIn(f"name = {reset} value = 0", finalize)
        self.assertIn("name = zg361_b1_agenda_item_state value = 2", finalize)
        self.assertIn("name = zg361_b1_agenda_item_state value = 3", finalize)
        self.assertIn("name = zg361_b1_agenda_header_state value = 2", finalize)
        self.assertIn("name = zg361_b1_agenda_skipped value = 1", finalize)

    def test_138_local_and_bank_rounding_objects_never_share_state(self) -> None:
        exact = top_level_block(
            self.effects, "zg361_b1_compute_exact_quota_effect"
        )
        local = top_level_block(
            self.effects, "zg361_b1_rebuild_local_quota_effect"
        )
        bank = top_level_block(
            self.effects, "zg361_b1_close_common_superior_bank_effect"
        )

        self.assertIn("ROUNDING_SCOPE = 1", local)
        self.assertIn("ROUNDING_SCOPE = 2", bank)
        self.assertIn(
            "zg361_b1_quota_rounding_work_scope value = $ROUNDING_SCOPE$", exact
        )
        self.assertIn(
            "zg361_b1_quota_rounding_work_route value = var:zg361_b1_m138_mode",
            exact,
        )
        self.assertIn(
            "zg361_b1_quota_rounding_work_route value = var:zg361_b1_bank_m138_mode",
            exact,
        )

        for prefix in (
            "zg361_b1_quota_rounding_local",
            "zg361_b1_quota_rounding_bank",
        ):
            for field in ("owner", "subject", "cycle", "case", "state"):
                with self.subTest(prefix=prefix, field=field):
                    self.assertIn(f"{prefix}_{field}", exact)
            for field in ("owner", "subject", "cycle", "case"):
                with self.subTest(reset=prefix, field=field):
                    self.assertRegex(
                        exact,
                        rf"(?:remove_variable = {prefix}_{field}|"
                        rf"set_variable = \{{ name = {prefix}_{field} value = 0 \}})",
                    )
            self.assertIn(f"name = {prefix}_state value = 0", exact)
            self.assertIn(f"name = {prefix}_state value = 1", exact)

        ambiguous_singletons = re.compile(
            r"\bzg361_b1_quota_rounding_(?:object_available|owner|subject|cycle|"
            r"case|state|route|team_n|team_[12]|remainder_team|affected_team)\b"
        )
        self.assertIsNone(ambiguous_singletons.search(exact + local + bank))

    def test_138_rounding_routes_feed_stable_allocation_and_terminal_receipts(self) -> None:
        exact = top_level_block(
            self.effects, "zg361_b1_compute_exact_quota_effect"
        )
        local = top_level_block(
            self.effects, "zg361_b1_rebuild_local_quota_effect"
        )
        bank = top_level_block(
            self.effects, "zg361_b1_close_common_superior_bank_effect"
        )

        for prefix in (
            "zg361_b1_quota_rounding_local",
            "zg361_b1_quota_rounding_bank",
        ):
            self.assertIn(f"name = {prefix}_rotation_cursor", exact)
            self.assertIn(f"name = {prefix}_chair", exact)
            self.assertIn(f"name = {prefix}_blackbox_risk value = 1", exact)

        # A rotates the remainder owner; B records explicit chair discretion.
        # C creates no object, and therefore cannot leave a terminal receipt.
        self.assertGreaterEqual(
            exact.count("var:zg361_b1_quota_rounding_work_route != 3"), 2
        )
        self.assertGreaterEqual(
            exact.count("var:zg361_b1_quota_rounding_work_route = 2"), 2
        )
        self.assertIn("remove_variable = zg361_b1_m138_receipt_serial", exact)
        self.assertIn(
            "var:zg361_b1_m138_mode != 3 var:zg361_b1_quota_rounding_local_object_available = 1",
            local,
        )
        self.assertIn(
            "var:zg361_b1_bank_m138_mode != 3 var:zg361_b1_quota_rounding_bank_object_available = 1",
            bank,
        )
        self.assertIn(
            "name = zg361_b1_quota_rounding_local_state value = 2", local
        )
        self.assertIn(
            "name = zg361_b1_quota_rounding_bank_state value = 2", bank
        )
        self.assertIn("name = zg361_b1_quota_rounding_local_operation_seal", local)
        self.assertIn("name = zg361_b1_quota_rounding_bank_operation_seal", bank)
        self.assertLess(
            local.index("name = zg361_b1_quota_rounding_local_operation_seal"),
            local.index("name = zg361_b1_quota_rounding_local_state value = 2"),
        )
        self.assertLess(
            bank.index("name = zg361_b1_quota_rounding_bank_operation_seal"),
            bank.index("name = zg361_b1_quota_rounding_bank_state value = 2"),
        )
        self.assertEqual(
            local.count(
                "set_variable = { name = zg361_b1_m138_receipt_serial"
            ),
            1,
        )
        self.assertEqual(
            bank.count(
                "set_variable = { name = zg361_b1_m138_receipt_serial"
            ),
            1,
        )
        self.assertIn(
            "name = zg361_b1_m138_receipt_serial value = var:zg361_b1_quota_rounding_local_case",
            local,
        )
        self.assertIn(
            "name = zg361_b1_m138_receipt_serial value = var:zg361_b1_quota_rounding_bank_case",
            bank,
        )
        self.assertLess(
            local.index("name = zg361_b1_quota_rounding_local_state value = 2"),
            local.index("name = zg361_b1_m138_receipt_serial"),
        )
        self.assertLess(
            bank.index("name = zg361_b1_quota_rounding_bank_state value = 2"),
            bank.index("name = zg361_b1_m138_receipt_serial"),
        )

        # The selected bank remainder team changes the real rank key; source
        # size and frozen roster order finish the deterministic tie-break.
        self.assertIn(
            "var:zg361_b1_case_owner = root.var:zg361_b1_quota_rounding_bank_remainder_team",
            bank,
        )
        self.assertIn("name = zg361_b1_quota_rounding_team_priority", bank)
        self.assertIn("name = zg361_b1_quota_pool_tie_key", bank)
        self.assertIn(
            "var:zg361_b1_quota_rounding_team_priority multiply = 1000", bank
        )
        self.assertIn(
            "var:zg361_b1_quota_pool_subject_source_size multiply = 100", bank
        )
        self.assertIn("subtract = var:zg361_b1_roster_frozen_order", bank)
        self.assertIn("order_by = var:zg361_b1_quota_pool_tie_key", bank)
        self.assertIn(
            "name = zg361_b1_quota_rounding_bank_tie_consumer_active value = 1",
            bank,
        )

    def test_140_reorg_routes_have_one_complete_replay_safe_owner_object(self) -> None:
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        additions = top_level_block(
            self.effects, "zg361_b1_audit_locked_roster_additions_effect"
        )

        for field in ("owner", "subject", "cycle", "case", "state"):
            with self.subTest(field=field):
                self.assertIn(f"zg361_b1_reorg_object_{field}", additions)
        for field in ("owner", "subject", "cycle", "case"):
            with self.subTest(reset=field):
                self.assertRegex(
                    initialize,
                    rf"(?:remove_variable = zg361_b1_reorg_object_{field}|"
                    rf"set_variable = \{{ name = zg361_b1_reorg_object_{field} value = 0 \}})",
                )
        self.assertIn("name = zg361_b1_reorg_object_available value = 0", initialize)
        self.assertIn("name = zg361_b1_reorg_object_state value = 0", initialize)
        self.assertIn("remove_variable = zg361_b1_reorg_quota_owner", initialize)
        self.assertIn("remove_variable = zg361_b1_m140_receipt_serial", initialize)

        # A preserves the archived manager/case tuple. B explicitly opens a new
        # manager tuple. C never falls through either allocation branch.
        self.assertIn("scope:zg361_b1_roster_add_manager.var:zg361_b1_m140_mode != 3", additions)
        self.assertIn("scope:zg361_b1_roster_add_manager.var:zg361_b1_m140_mode = 1", additions)
        self.assertIn("scope:zg361_b1_roster_add_manager.var:zg361_b1_m140_mode = 2", additions)
        self.assertIn("name = zg361_b1_reorg_route value = 1", additions)
        self.assertIn("name = zg361_b1_reorg_route value = 2", additions)
        self.assertIn(
            "var:zg361_b1_reorg_object_cycle = var:zg361_b1_reorg_archive_cycle",
            additions,
        )
        self.assertIn("var:zg361_b1_reorg_archive_subject = this", additions)

        replay_prefix = additions.split(
            "has_variable = zg361_b1_reorg_archive_case", 1
        )[1].split(
            "set_variable = { name = zg361_b1_reorg_replay_detected value = 1 }",
            1,
        )[0]
        for field in ("owner", "subject", "cycle", "case", "state"):
            with self.subTest(replay=field):
                self.assertIn(f"zg361_b1_reorg_object_{field}", replay_prefix)

    def test_140_zero_day_observation_is_not_a_fake_segment_or_receipt(self) -> None:
        additions = top_level_block(
            self.effects, "zg361_b1_audit_locked_roster_additions_effect"
        )
        local = top_level_block(
            self.effects, "zg361_b1_rebuild_local_quota_effect"
        )

        self.assertNotIn(
            "name = zg361_b1_reorg_allocation_evidence_count value = 4",
            additions,
        )
        self.assertEqual(
            additions.count(
                "name = zg361_b1_reorg_allocation_evidence_count value = 3"
            ),
            2,
        )
        self.assertEqual(
            additions.count("name = zg361_b1_reorg_new_observation_n value = 1"),
            2,
        )
        self.assertEqual(
            additions.count(
                "name = zg361_b1_reorg_new_evidence_segment_available value = 0"
            ),
            2,
        )
        self.assertIn("name = zg361_b1_reorg_service_days value = 0", additions)

        # One occupied cohort slot is terminally receipted once per A/B route;
        # the 0-day live snapshot remains an observation, never a fourth fact.
        terminal_receipts = re.findall(
            r"name = zg361_b1_reorg_allocation_occupied_slots value = 1.*?"
            r"name = zg361_b1_reorg_allocation_receipt_state value = 1.*?"
            r"name = zg361_b1_m140_receipt_serial",
            additions,
            re.DOTALL,
        )
        self.assertEqual(len(terminal_receipts), 2)
        self.assertEqual(
            additions.count(
                "set_variable = { name = zg361_b1_m140_receipt_serial"
            ),
            2,
        )
        self.assertEqual(
            additions.count(
                "name = zg361_b1_m140_receipt_serial value = var:zg361_b1_reorg_object_case"
            ),
            2,
        )

        # The frozen owner is not audit-only: it is an eligibility guard for
        # the real local quota cohort, preventing old and new books both taking it.
        self.assertIn("has_variable = zg361_b1_reorg_quota_owner", local)
        self.assertIn("var:zg361_b1_reorg_quota_owner = root", local)

    def test_001_013_defer_modes_create_policy_debt_not_domain_objects(self) -> None:
        freeze = top_level_block(
            self.effects, "zg361_b1_freeze_001_013_policy_effect"
        )
        self.assertIn("name = zg361_b1_policy_debt_cycle_n value = 0", freeze)
        self.assertIn("name = zg361_b1_policy_next_review_serial", freeze)
        self.assertIn("add = 1", freeze)
        for mechanism_id in range(1, 14):
            key = f"{mechanism_id:03d}"
            with self.subTest(mechanism=key):
                self.assertIn(f"name = zg361_b1_m{key}_mode value = 1", freeze)
                self.assertIn(f"zg361_mechanism_{key}_choice", freeze)
                self.assertIn(f"var:zg361_b1_m{key}_mode = 3", freeze)
                self.assertIn(f"zg361_b1_m{key}_policy_debt_serial", freeze)

        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        for mechanism_id in range(1, 14):
            self.assertIn(
                f"remove_variable = zg361_b1_m{mechanism_id:03d}_receipt_serial",
                initialize,
            )
        open_cycle = top_level_block(self.effects, "zg361_b1_open_cycle_effect")
        for mechanism_id in (9, 10, 11, 13):
            self.assertIn(
                f"remove_variable = zg361_b1_m{mechanism_id:03d}_receipt_serial",
                open_cycle,
            )
        for object_id in (
            "zg361_b1_checkin_id",
            "zg361_b1_self_review_id",
            "zg361_b1_self_evidence_id",
            "zg361_b1_evidence_sheet_id",
            "zg361_b1_conflict_case_id",
            "zg361_b1_recusal_reviewer",
        ):
            self.assertIn(f"remove_variable = {object_id}", initialize)
        self.assertIn("root.var:zg361_b1_m003_mode = 3", initialize)
        self.assertIn("name = zg361_b1_checkin_available value = 0", initialize)
        self.assertIn("root.var:zg361_b1_m004_mode = 3", initialize)
        self.assertIn("name = zg361_b1_self_review_available value = 0", initialize)
        self.assertIn("root.var:zg361_b1_m007_mode = 3", initialize)
        self.assertIn("name = zg361_b1_peer_cap value = 0", initialize)
        self.assertIn("root.var:zg361_b1_m008_mode = 3", initialize)
        self.assertIn("name = zg361_b1_peer_use_mode value = 0", initialize)
        for default_abi in (
            "name = zg361_b1_disclosure_policy_available value = 1",
            "name = zg361_b1_disclosure_policy_id value = var:zg361_b1_case_serial",
            "name = zg361_b1_disclosure_self_mode value = 3",
            "name = zg361_b1_disclosure_team_mode value = 2",
            "name = zg361_b1_disclosure_evaluator_identity_mode value = 1",
            "name = zg361_b1_disclosure_blackbox_risk value = 0",
        ):
            self.assertIn(default_abi, initialize)
        self.assertIn("root.var:zg361_b1_m013_mode = 2", initialize)
        self.assertIn("name = zg361_b1_disclosure_self_mode value = 1", initialize)
        self.assertIn("name = zg361_b1_disclosure_team_mode value = 0", initialize)
        self.assertIn("name = zg361_b1_disclosure_blackbox_risk value = 1", initialize)
        self.assertIn("root.var:zg361_b1_m013_mode = 3", initialize)
        self.assertIn("name = zg361_b1_disclosure_policy_available value = 0", initialize)
        self.assertIn("remove_variable = zg361_b1_disclosure_policy_id", initialize)

        open_calibration = top_level_block(
            self.effects, "zg361_b1_open_calibration_effect"
        )
        for mechanism_id in (9, 10, 12):
            self.assertNotIn(
                f"set_variable = {{ name = zg361_b1_m{mechanism_id:03d}_receipt_serial",
                open_calibration,
            )
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        self.assertIn("limit = { var:zg361_b1_m013_mode != 3 }", publish)
        liability = top_level_block(
            self.effects, "zg361_b1_consume_manager_liabilities_as_subject_effect"
        )
        self.assertIn("var:zg361_b1_policy_debt_due_year <= current_year", liability)
        self.assertIn("multiply = -2", liability)
        self.assertIn("max = 0 min = -20", liability)

    def test_001_006_have_frozen_facts_and_bounded_score_consumers(self) -> None:
        classifier = top_level_block(
            self.effects, "zg361_b1_classify_function_effect"
        )
        for marker in (
            "vassal_contract_has_flag = celestial_military_appointment",
            "has_council_position = councillor_marshal",
            "has_council_position = councillor_steward",
            "is_governor = yes",
            "zg361_b1_function_code value = 4",
            "zg361_b1_function_code value = 3",
            "zg361_b1_function_code value = 2",
            "zg361_b1_function_code value = 1",
        ):
            self.assertIn(marker, classifier)

        facts = top_level_block(
            self.effects, "zg361_b1_finalize_subject_facts_effect"
        )
        evidence_fields = (
            "governance",
            "capability",
            "growth",
            "superior",
            "values",
            "collaboration",
            "jingcha",
            "organization",
        )
        for field in evidence_fields:
            self.assertIn(
                f"zg361_b1_evidence_{field} value = var:zg361_evidence_{field}",
                facts,
            )
            self.assertIn(f"var:zg361_b1_evidence_{field}", facts)
        self.assertIn("var:zg361_b1_evidence_sum_check = var:zg361_kpi", facts)
        self.assertIn("name = zg361_b1_goal_score_adjustment", facts)
        self.assertIn("name = zg361_b1_role_weighted_score", facts)
        self.assertIn("name = zg361_b1_baseline_state_delta", facts)
        self.assertIn("name = zg361_b1_difficulty_score_adjustment", facts)

        shadow = top_level_block(self.effects, "zg361_b1_open_shadow_effect")
        for adjustment in (
            "zg361_b1_self_visibility_adjustment",
            "zg361_b1_peer_calibration_adjustment",
            "zg361_b1_goal_score_adjustment",
            "zg361_b1_role_score_adjustment",
            "zg361_b1_evidence_window_adjustment",
            "zg361_b1_difficulty_score_adjustment",
            "zg361_b1_manager_liability_adjustment",
        ):
            self.assertIn(f"add = var:{adjustment}", shadow)

        midcycle = top_level_block(
            self.effects, "zg361_b1_midcycle_dispatcher_effect"
        )
        self.assertIn("limit = { var:zg361_b1_checkin_available = 1 }", midcycle)
        self.assertIn(
            "random_character_war = { save_temporary_scope_as = zg361_b1_midcycle_crisis_war }",
            midcycle,
        )
        self.assertIn(
            "name = zg361_b1_crisis_war value = scope:zg361_b1_midcycle_crisis_war",
            midcycle,
        )
        self.assertIn("name = zg361_b1_goal_old_target", midcycle)
        self.assertIn("name = zg361_b1_goal_new_target", midcycle)

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
        for legacy_signal in (
            "zg361_recommended",
            "zg361_slandered",
            "zg361_slander_backfire",
        ):
            self.assertNotIn(legacy_signal, self.values)
        for effect_name, raw in (
            ("zg361_b1_submit_peer_positive_effect", "10"),
            ("zg361_b1_submit_peer_negative_effect", "-15"),
        ):
            block = top_level_block(self.effects, effect_name)
            self.assertIn("zg361_b1_prepare_shared_war_peer_task_effect = yes", block)
            self.assertIn("var:zg361_b1_peer_common_task_found = 1", block)
            self.assertIn("var:zg361_b1_peer_common_task_kind = 1", block)
            self.assertNotIn(
                "common_task_id value = var:zg361_b1_case_serial", block
            )
            self.assertIn(
                "var:zg361_b1_peer_used < var:zg361_b1_peer_cap", block
            )
            self.assertIn("NOT = { this = scope:recipient }", block)
            self.assertIn("var:zg361_b1_case_state = 3", block)
            self.assertGreaterEqual(
                block.count("var:zg361_b1_case_subject = this"), 2
            )
            self.assertGreaterEqual(block.count("var:zg361_b1_case_active = 1"), 2)
            self.assertGreaterEqual(
                block.count("var:zg361_b1_roster_included = 1"), 2
            )
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
                    "performance",
                    "collaboration",
                    "values",
                    "example_id",
                    "common_task_id",
                    "common_task_kind",
                    "common_task_owner",
                    "common_task_cycle",
                    "common_task_case",
                    "common_task_attacker",
                    "common_task_defender",
                    "invitation_source",
                    "anonymous",
                    "contribution_weight",
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
        for identity in (
            "var:zg361_b1_case_owner = root",
            "var:zg361_b1_case_subject = this",
            "var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial",
            "var:zg361_b1_case_serial = root.var:zg361_b1_case_serial",
            "var:zg361_b1_case_state = 3",
            "var:zg361_b1_case_active = 1",
            "var:zg361_b1_roster_included = 1",
        ):
            self.assertIn(identity, prepare)
        evidence = prepare.index(
            "set_variable = { name = zg361_b1_evidence_late value = var:zg361_b1_owner_bound_kpi }"
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
            self.assertIn("var:zg361_b1_case_owner = root", consumer)
            self.assertIn("var:zg361_b1_case_subject = this", consumer)
            self.assertIn(
                "var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial",
                consumer,
            )
            self.assertIn(
                "var:zg361_b1_case_serial = root.var:zg361_b1_case_serial",
                consumer,
            )
            self.assertIn("var:zg361_b1_case_state = 3", consumer)
            self.assertIn("var:zg361_b1_case_active = 1", consumer)
            self.assertIn("var:zg361_b1_roster_included = 1", consumer)
            self.assertIn(
                f"var:zg361_b1_peer_slot_{slot}_subject = this", consumer
            )
            self.assertIn(
                f"var:zg361_b1_peer_slot_{slot}_cycle = var:zg361_b1_cycle_serial",
                consumer,
            )
            self.assertIn(
                f"var:zg361_b1_peer_slot_{slot}_common_task_kind = 1", consumer
            )
            self.assertIn(
                f"var:zg361_b1_peer_slot_{slot}_common_task_owner = root", consumer
            )
            self.assertIn(
                f"var:zg361_b1_peer_slot_{slot}_common_task_cycle = var:zg361_b1_cycle_serial",
                consumer,
            )
            self.assertIn(
                f"var:zg361_b1_peer_slot_{slot}_common_task_case = var:zg361_b1_case_serial",
                consumer,
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
            "value = var:zg361_b1_peer_normalized_score multiply = var:zg361_b1_peer_effective_weight_percent divide = 100",
            shadow,
        )
        self.assertIn(
            "name = zg361_b1_peer_effective_weight_percent", prepare
        )
        self.assertIn("multiply = 5 max = var:zg361_b1_peer_total_weight_cap", prepare)
        self.assertIn("limit = { var:zg361_b1_peer_shape = 4 }", shadow)
        self.assertIn("limit = { var:zg361_b1_peer_reciprocity_risk = 1 }", shadow)
        self.assertIn("add = var:zg361_b1_peer_calibration_adjustment", shadow)
        self.assertIn("zg361_b1_peer_normalized_score", self.values)
        self.assertIn("add = var:zg361_b1_peer_normalized_score", self.values)

    def test_peer_common_task_is_a_real_same_side_war_or_submission_is_rejected(self) -> None:
        task = top_level_block(
            self.effects, "zg361_b1_prepare_shared_war_peer_task_effect"
        )
        self.assertIn("random_character_war = {", task)
        self.assertIn("scope:actor = { is_attacker_in_war = prev }", task)
        self.assertIn("scope:recipient = { is_attacker_in_war = prev }", task)
        self.assertIn("scope:actor = { is_defender_in_war = prev }", task)
        self.assertIn("scope:recipient = { is_defender_in_war = prev }", task)
        self.assertIn("save_temporary_scope_as = zg361_b1_peer_common_war", task)
        for field in ("owner", "cycle", "case", "serial_cursor"):
            self.assertIn(f"zg361_b1_peer_task_{field}", task)
        self.assertIn("scope:zg361_b1_peer_common_war.primary_attacker", task)
        self.assertIn("scope:zg361_b1_peer_common_war.primary_defender", task)
        task_code = without_comments(task)
        self.assertNotIn(
            "name = zg361_b1_peer_common_task_serial value = var:zg361_b1_case_serial",
            task_code,
        )

    def test_009_012_calibration_writes_are_guarded_atomic_and_recusal_safe(self) -> None:
        recusal = top_level_block(
            self.effects, "zg361_b1_freeze_conflict_recusals_effect"
        )
        for token in (
            "var:zg361_b1_case_owner = scope:zg361_b1_conflict_manager",
            "var:zg361_b1_case_subject = this",
            "var:zg361_b1_cycle_serial = scope:zg361_b1_conflict_manager.var:zg361_b1_cycle_serial",
            "var:zg361_b1_case_serial = scope:zg361_b1_conflict_manager.var:zg361_b1_case_serial",
            "var:zg361_b1_case_state = 5",
            "var:zg361_b1_case_active = 1",
            "var:zg361_b1_roster_included = 1",
            "root.var:zg361_b1_m012_mode != 3",
        ):
            self.assertIn(token, recusal)
        self.assertIn("name = zg361_b1_recusal_actor", recusal)
        self.assertIn("name = zg361_b1_recusal_reviewer", recusal)
        self.assertIn("root.var:zg361_b1_m012_mode = 1", recusal)
        self.assertIn("name = zg361_b1_recusal_active value = 1", recusal)

        swap = top_level_block(
            self.effects, "zg361_b1_apply_atomic_calibration_swap_effect"
        )
        self.assertIn("var:zg361_b1_m009_mode != 3", swap)
        self.assertIn("var:zg361_b1_cycle_state = 7", swap)
        self.assertIn(
            "NOT = { var:zg361_b1_m009_receipt_serial = var:zg361_b1_case_serial }",
            swap,
        )
        self.assertEqual(swap.count("var:zg361_b1_recusal_active = 0"), 2)
        self.assertIn("var:zg361_b1_calibration_swap_candidate_n = 2", swap)
        self.assertIn(
            "scope:zg361_b1_calibration_promote_subject.var:zg361_b1_calibration_score > scope:zg361_b1_calibration_demote_subject.var:zg361_b1_calibration_score",
            swap,
        )
        self.assertEqual(
            swap.count("set_variable = { name = zg361_pending_grade value ="), 2
        )
        self.assertIn("change_variable = { name = zg361_b1_calibration_attention add = -1 }", swap)
        self.assertIn("change_variable = { name = zg361_b1_quota_book_version add = 1 }", swap)
        for count_field in ("top", "middle", "bottom"):
            self.assertIn(f"zg361_b1_calibration_before_{count_field}", swap)
            self.assertIn(f"zg361_b1_calibration_after_{count_field}", swap)
            self.assertIn(f"zg361_b1_calibration_remaining_{count_field}", swap)
        self.assertIn("var:zg361_b1_m009_mode = 2", swap)
        self.assertIn("name = zg361_b1_calibration_quick_close value = 1", swap)
        self.assertIn("name = zg361_b1_calibration_assignment_n add = 1", swap)
        self.assertIn("name = zg361_b1_calibration_one_grade_check value = 1", swap)
        self.assertIn(
            "name = zg361_b1_calibration_quick_close_blocked value = 1", swap
        )
        self.assertIn("name = zg361_b1_publication_blocked value = 1", swap)

        protection = top_level_block(
            self.effects, "zg361_b1_apply_bottom_protection_effect"
        )
        self.assertIn("var:zg361_b1_m010_mode = 1", protection)
        self.assertGreaterEqual(protection.count("var:zg361_b1_recusal_active = 0"), 3)
        self.assertIn("NOT = { has_character_flag = zg361_newcomer_this_cycle }", protection)
        self.assertIn("var:zg361_b1_bottom_protection_candidate_n = 2", protection)
        self.assertEqual(
            protection.count("set_variable = { name = zg361_pending_grade value ="),
            2,
        )
        self.assertIn("add_prestige = -25", protection)
        self.assertIn("name = zg361_b1_protection_debt_state value = 1", protection)
        self.assertIn("value = current_year add = 1", protection)
        self.assertIn("var:zg361_b1_m010_mode = 2", protection)
        self.assertIn("name = zg361_b1_bottom_edge_candidate_n", protection)
        self.assertIn("name = zg361_b1_resentment_risk value = 1", protection)
        self.assertIn("name = zg361_b1_attrition_risk value = 1", protection)
        self.assertIn(
            "name = zg361_b1_bottom_edge_blocked_newcomer_protection value = 1",
            protection,
        )

        oversight = top_level_block(
            self.effects, "zg361_b1_prepare_skip_level_return_effect"
        )
        self.assertIn("var:zg361_b1_m011_mode = 1", oversight)
        self.assertIn("var:zg361_b1_skip_level_return_count = 0", oversight)
        self.assertIn("name = zg361_b1_publication_blocked value = 1", oversight)
        self.assertIn("trigger_event = { id = zg361b1.124 days = 1 }", oversight)
        self.assertIn("var:zg361_b1_m011_mode = 2", oversight)
        self.assertIn("name = zg361_b1_oversight_owner value = this", oversight)
        self.assertIn("name = zg361_b1_oversight_improper_route_risk value = 1", oversight)
        self.assertIn("name = zg361_b1_oversight_override_executed value = 1", oversight)
        self.assertIn("name = zg361_b1_skip_level_book_owner value = root", oversight)
        self.assertEqual(
            oversight.count("set_variable = { name = zg361_pending_grade value ="),
            2,
        )
        self.assertGreaterEqual(
            oversight.count("var:zg361_b1_recusal_active = 0"), 2
        )
        open_calibration = top_level_block(
            self.effects, "zg361_b1_open_calibration_effect"
        )
        self.assertIn(
            "limit = { var:zg361_b1_calibration_quick_close_blocked = 0 }",
            open_calibration,
        )
        self.assertIn("B quick-close assignment/quota mismatch", open_calibration)
        continuation = top_level_block(self.events, "zg361b1.124")
        for token in ("owner", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_oversight_ticket_{token}", continuation)
        self.assertIn("var:zg361_b1_skip_level_return_count = 1", continuation)
        continuation_code = without_comments(continuation)
        for forbidden in ("zg361_pending_grade", "zg361_b1_final_grade", "zg361_last_grade"):
            self.assertNotIn(f"name = {forbidden}", continuation_code)

    def test_post_recusal_grade_writers_share_one_frozen_acl_boundary(self) -> None:
        recusal = top_level_block(
            self.effects, "zg361_b1_freeze_conflict_recusals_effect"
        )
        self.assertIn("name = zg361_b1_grade_write_acl_frozen value = 1", recusal)
        for authority in (1, 2, 3):
            self.assertIn(
                f"name = zg361_b1_grade_write_authority value = {authority}",
                recusal,
            )
        self.assertIn("name = zg361_b1_grade_write_reviewer", recusal)

        pending_open = top_level_block(
            self.effects, "zg361_b1_open_pending_slots_effect"
        )
        pending_resolve = top_level_block(
            self.effects, "zg361_b1_resolve_pending_subject_effect"
        )
        reopen_gate = top_level_block(
            self.effects, "zg361_b1_prepare_reopen_gate_effect"
        )
        for block in (pending_open, pending_resolve, reopen_gate):
            self.assertIn("var:zg361_b1_recusal_active = 0", block)

        rerank = top_level_block(
            self.effects, "zg361_b1_rerank_frozen_quota_book_effect"
        )
        for field in (
            "zg361_b1_rerank_fixed_top",
            "zg361_b1_rerank_fixed_middle",
            "zg361_b1_rerank_fixed_bottom",
            "zg361_b1_rerank_target_top",
            "zg361_b1_rerank_target_middle",
            "zg361_b1_rerank_target_bottom",
        ):
            self.assertIn(field, rerank)
        self.assertIn("var:zg361_b1_recusal_active = 1", rerank)
        self.assertIn("var:zg361_b1_recusal_active = 0", rerank)
        self.assertIn(
            "subtract = var:zg361_b1_rerank_fixed_bottom min = 0", rerank
        )

        finish = top_level_block(
            self.effects, "zg361_b1_finish_calibration_effect"
        )
        self.assertIn("zg361_apply_pending_grades_effect = yes", finish)
        self.assertNotIn("id = zg361.10", finish)
        self.assertNotIn("zg361_b1_open_calibration_legacy_unused_effect", self.effects)
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        self.assertIn("name = zg361_b1_recusal_post_grade", publish)
        self.assertIn("name = zg361_b1_recusal_lock_match value = 1", publish)

    def test_012_replacement_reviewer_independently_rescores_and_commits(self) -> None:
        recusal = top_level_block(
            self.effects, "zg361_b1_freeze_conflict_recusals_effect"
        )
        self.assertIn("NOT = { var:zg361_b1_bank_superior = this }", recusal)
        self.assertIn("NOT = { this = root.var:zg361_b1_bank_superior }", recusal)
        self.assertIn(
            "name = zg361_b1_recusal_post_recommendation value = 0", recusal
        )

        review = top_level_block(
            self.effects, "zg361_b1_apply_recusal_replacement_reviews_effect"
        )
        for token in (
            "var:zg361_b1_case_owner = scope:zg361_b1_recusal_review_manager",
            "var:zg361_b1_case_subject = this",
            "var:zg361_b1_cycle_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_cycle_serial",
            "var:zg361_b1_case_serial = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial",
            "var:zg361_b1_case_state = 5",
            "var:zg361_b1_case_active = 1",
            "var:zg361_b1_roster_included = 1",
            "var:zg361_b1_recusal_active = 1",
            "var:zg361_b1_grade_write_acl_frozen = 1",
            "scope:zg361_b1_recusal_review_manager.var:zg361_b1_m012_mode = 1",
        ):
            self.assertIn(token, review)

        # Named replacement is distinct from manager, subject, and the recused
        # actor.  A one-person/small cohort instead takes the explicit abstract
        # authority-3 branch; neither path silently falls back to the manager.
        for token in (
            "var:zg361_b1_grade_write_authority = 2",
            "var:zg361_b1_recusal_replacement_kind = 1",
            "var:zg361_b1_grade_write_reviewer = var:zg361_b1_recusal_reviewer",
            "NOT = { var:zg361_b1_grade_write_reviewer = scope:zg361_b1_recusal_review_manager }",
            "NOT = { var:zg361_b1_grade_write_reviewer = this }",
            "NOT = { var:zg361_b1_grade_write_reviewer = var:zg361_b1_recusal_actor }",
            "var:zg361_b1_grade_write_authority = 3",
            "var:zg361_b1_recusal_replacement_kind = 2",
            "NOT = { has_variable = zg361_b1_grade_write_reviewer }",
            "NOT = { has_variable = zg361_b1_recusal_reviewer }",
        ):
            self.assertIn(token, review)

        # The replacement action recomputes from the identity-blind frozen
        # score, rather than copying the manager's already forced grade.
        self.assertIn(
            "name = zg361_b1_recusal_review_base_score value = var:zg361_b1_blind_score",
            review,
        )
        self.assertIn("var:zg361_b1_recusal_review_score >= 50", review)
        self.assertIn("var:zg361_b1_recusal_review_score < 0", review)
        for grade in (1, 2, 3):
            self.assertIn(
                f"name = zg361_b1_recusal_review_recommended_grade value = {grade}",
                review,
            )
        self.assertIn(
            "name = zg361_b1_recusal_post_recommendation value = var:zg361_b1_recusal_review_recommended_grade",
            review,
        )

        # A changed recommendation is a two-sided write only.  The peer must be
        # unrecused and in the target band, so grade counts remain exact without
        # editing the three count variables.  No target slot is an explicit
        # quota-blocked terminal, never a one-sided write.
        self.assertEqual(
            review.count("set_variable = { name = zg361_pending_grade value ="), 2
        )
        self.assertGreaterEqual(review.count("var:zg361_b1_recusal_active = 0"), 2)
        self.assertIn("name = zg361_b1_recusal_review_partner_n value = 0", review)
        self.assertIn("zg361_b1_recusal_review_partner_n = 1", review)
        self.assertIn("name = zg361_b1_recusal_review_quota_blocked value = 1", review)
        self.assertIn("name = zg361_b1_recusal_review_state value = 3", review)
        self.assertIn(
            "change_variable = { name = zg361_b1_quota_book_version add = 1 }",
            review,
        )
        for count_field in ("zg361_pending_375_n", "zg361_pending_35_n", "zg361_pending_325_n"):
            self.assertNotIn(count_field, review)

        # The receipt itself is the full owner/subject/cycle/case/state tuple;
        # the same tuple appears in the pre-write NOT guard, making double-click
        # and an old case deterministic no-ops.
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_recusal_review_receipt_{field}", review)
        self.assertIn(
            "var:zg361_b1_recusal_review_receipt_owner = scope:zg361_b1_recusal_review_manager",
            review,
        )
        self.assertIn(
            "var:zg361_b1_recusal_review_receipt_subject = this", review
        )
        self.assertIn(
            "var:zg361_b1_recusal_review_receipt_cycle = scope:zg361_b1_recusal_review_manager.var:zg361_b1_cycle_serial",
            review,
        )
        self.assertIn(
            "var:zg361_b1_recusal_review_receipt_case = scope:zg361_b1_recusal_review_manager.var:zg361_b1_case_serial",
            review,
        )
        self.assertIn("var:zg361_b1_recusal_review_receipt_state = 2", review)

        open_calibration = top_level_block(
            self.effects, "zg361_b1_open_calibration_effect"
        )
        freeze_at = open_calibration.index(
            "zg361_b1_freeze_conflict_recusals_effect = yes"
        )
        replacement_at = open_calibration.index(
            "zg361_b1_apply_recusal_replacement_reviews_effect = yes"
        )
        manager_swap_at = open_calibration.index(
            "zg361_b1_apply_atomic_calibration_swap_effect = yes"
        )
        self.assertLess(freeze_at, replacement_at)
        self.assertLess(replacement_at, manager_swap_at)

    def test_successful_appeal_updates_evaluator_credit_once_through_frozen_adapter(self) -> None:
        self.assertIn("zg361_b1_on_appeal_corrected_effect = yes", self.core)
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        for field in (
            "result_owner",
            "result_subject",
            "result_cycle",
            "result_case",
            "b1_owner",
            "b1_subject",
            "b1_cycle",
            "b1_case",
            "original_grade",
            "m008_mode",
        ):
            self.assertIn(f"zg361_b1_result_adapter_{field}", publish)

        appeal = top_level_block(
            self.effects, "zg361_b1_on_appeal_corrected_effect"
        )
        for token in (
            "var:zg361_b1_result_adapter_b1_subject = this",
            "var:zg361_b1_result_adapter_b1_state = 8",
            "var:zg361_b1_result_adapter_original_grade = 1",
            "var:zg361_result_case_state = 5",
            "var:zg361_result_grade = 2",
            "var:zg361_result_appeal_outcome = 1",
            "var:zg361_result_refund_posted_serial = var:zg361_result_case_serial",
            "var:zg361_b1_result_adapter_m008_mode != 3",
        ):
            self.assertIn(token, appeal)
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_peer_appeal_receipt_{field}", appeal)
        self.assertIn("NOT = {", appeal)
        self.assertNotIn("name = zg361_pending_grade", without_comments(appeal))
        self.assertNotIn("name = zg361_last_grade", without_comments(appeal))
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        self.assertNotIn("remove_variable = zg361_b1_result_adapter", initialize)

        for slot in (1, 2, 3):
            self.assertIn(
                f"zg361_b1_result_adapter_peer_slot_{slot}_evaluator", publish
            )
            consumer = top_level_block(
                self.effects, f"zg361_b1_apply_appeal_credit_slot_{slot}_effect"
            )
            self.assertIn(
                f"var:zg361_b1_result_adapter_peer_slot_{slot}_raw < 0",
                consumer,
            )
            self.assertEqual(
                consumer.count(
                    "change_variable = { name = zg361_b1_evaluator_overturn_n add = 1 }"
                ),
                1,
            )
            self.assertIn("name = zg361_b1_evaluator_credit add = -5", consumer)
            self.assertIn("var:zg361_b1_result_adapter_m008_mode = 1", consumer)
            self.assertIn("name = zg361_b1_evaluator_credit add = 2", consumer)
            self.assertIn("max = 125 min = 25", consumer)
            self.assertIn("zg361_b1_evaluator_overturn_rate", consumer)

    def test_357_external_receipt_requires_real_quota_and_linked_final_result(self) -> None:
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        for required in (
            "has_variable = zg361_b1_m357_receipt_serial",
            "var:zg361_b1_m357_receipt_serial = var:zg361_b1_case_serial",
            "has_variable = zg361_b1_result_adapter_result_case",
            "var:zg361_b1_result_adapter_result_case = var:zg361_result_case_serial",
            "var:zg361_b1_result_adapter_b1_state = 8",
            "zg361_b1_m357_external_absolute_grade",
            "zg361_b1_m357_external_final_grade",
            "zg361_b1_m357_external_final_reason",
            "zg361_b1_m357_external_forced_down",
            "zg361_b1_m357_external_receipt_id",
            "zg361_b1_m357_external_receipt_hash",
        ):
            self.assertIn(required, publish)
        adapter = publish.index(
            "set_variable = { name = zg361_b1_result_adapter_result_case"
        )
        reason = publish.index(
            "set_variable = { name = zg361_b1_final_reason"
        )
        receipt = publish.index(
            "set_variable = { name = zg361_b1_m357_external_receipt_owner"
        )
        self.assertLess(adapter, receipt)
        self.assertLess(reason, receipt)
        self.assertNotIn("zg361_we_submit_al_357_359_receipts_effect", publish)
        self.assertNotIn("external_stage_receipts_verified", publish)

    def test_360_source_requires_full_published_agenda_and_exact_357_receipts(self) -> None:
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        producer_call = "zg361_b1_publish_m360_cohort_source_effect = yes"
        self.assertIn(producer_call, publish)
        self.assertGreater(
            publish.index(producer_call),
            publish.index(
                "set_variable = { name = zg361_b1_m357_external_receipt_hash"
            ),
        )
        self.assertLess(
            publish.index(producer_call),
            publish.index("remove_character_flag = zg361_b1_cycle_active"),
        )

        source = top_level_block(
            self.effects, "zg361_b1_publish_m360_cohort_source_effect"
        )
        for required in (
            "has_variable_list = zg361_b1_processing_subjects",
            "var:zg361_b1_cycle_state = 8",
            "var:zg361_b1_closure_state = 4",
            "var:zg361_b1_processing_n = var:zg361_b1_agenda_n",
            "var:zg361_b1_agenda_hash = var:zg361_b1_agenda_new_hash",
            "var:zg361_b1_agenda_mode != 3",
            "var:zg361_b1_agenda_header_state = 2",
            "var:zg361_b1_m360_work_agenda_closed_n = var:zg361_b1_agenda_n",
            "var:zg361_b1_quota_conservation_valid = 1",
            "var:zg361_b1_quota_recount_bottom = var:zg361_pending_325_n",
            "var:zg361_pending_325_n >= 1",
            "var:zg361_pending_325_n <= 6",
            "var:zg361_b1_case_state = 8",
            "var:zg361_b1_case_active = 0",
            "limit = { var:zg361_b1_absolute_grade < 2 }",
            "var:zg361_b1_m137_receipt_serial = var:zg361_b1_case_serial",
            "var:zg361_b1_m357_external_receipt_state = 8",
            "var:zg361_b1_m357_external_receipt_id > 0",
            "var:zg361_b1_m357_external_receipt_hash > 0",
            "var:zg361_b1_m357_external_result_case = var:zg361_b1_result_adapter_result_case",
            "var:zg361_b1_result_adapter_result_cycle = var:zg361_b1_cycle_serial",
            "var:zg361_b1_result_adapter_b1_state = 8",
            "var:zg361_b1_m360_work_forced_count = var:zg361_pending_325_n",
            "var:zg361_b1_m360_work_abs_c = 0",
        ):
            self.assertIn(required, source)

        self.assertIn(
            "value = { value = var:zg361_b1_case_serial multiply = 1000 }",
            source,
        )
        self.assertIn(
            "add = { value = prev.var:zg361_b1_roster_frozen_order multiply = prev.var:zg361_b1_processing_order }",
            source,
        )
        self.assertIn(
            "var:zg361_b1_m360_work_member_hash = var:zg361_b1_agenda_new_hash",
            source,
        )
        self.assertIn(
            "name = zg361_b1_m360_source_member_hash value = var:zg361_b1_m360_work_member_hash",
            source,
        )
        self.assertIn(
            "name = zg361_b1_m360_source_agenda_hash value = var:zg361_b1_agenda_new_hash",
            source,
        )
        self.assertIn(
            "name = zg361_b1_m360_source_all_meet_receipt_serial value = var:zg361_b1_case_serial",
            source,
        )
        self.assertIn("name = zg361_b1_m360_source_id", source)
        self.assertIn("name = zg361_b1_m360_source_hash", source)
        self.assertIn("add = var:zg361_b1_m360_work_m357_hash_sum", source)
        self.assertIn(
            "order_by = { value = var:zg361_b1_processing_order multiply = -1 }",
            source,
        )

    def test_360_source_has_six_bounded_exact_forced_c_slots_without_defaults(self) -> None:
        source = top_level_block(
            self.effects, "zg361_b1_publish_m360_cohort_source_effect"
        )
        self.assertIn(
            "limit = { var:zg361_b1_final_grade = 1 var:zg361_b1_forced_down = 1 }",
            source,
        )
        slot_fields = (
            "character",
            "processing_order",
            "m357_receipt_id",
            "m357_receipt_hash",
            "b1_owner",
            "b1_subject",
            "b1_cycle",
            "b1_case",
            "result_owner",
            "result_subject",
            "result_cycle",
            "result_case",
        )
        for slot in range(1, 7):
            with self.subTest(slot=slot):
                self.assertIn(
                    f"limit = {{ root.var:zg361_b1_m360_work_slot = {slot} }}",
                    source,
                )
                for field in slot_fields:
                    self.assertIn(
                        f"name = zg361_b1_m360_source_forced_{slot}_{field}",
                        source,
                    )
                    self.assertIn(
                        f"remove_variable = zg361_b1_m360_source_forced_{slot}_{field}",
                        source,
                    )
        self.assertEqual(
            source.count("name = zg361_b1_m360_source_available value = 1"), 1
        )
        self.assertEqual(
            source.count("name = zg361_b1_m360_source_sealed value = 1"), 1
        )
        self.assertNotIn("name = zg361_b1_m360_source_available value = 0", source)
        self.assertNotIn("name = zg361_b1_m360_source_quota value = 0", source)
        self.assertNotIn("name = zg361_b1_m360_source_forced_count value = 0", source)

    def test_360_source_distinguishes_wait_ready_na_and_invalid_without_fake_payload(self) -> None:
        source = top_level_block(
            self.effects, "zg361_b1_publish_m360_cohort_source_effect"
        )
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        # Status does not exist before the mark call; the caller sees WAIT by
        # absence rather than by a made-up status or business tuple.
        self.assertNotIn("zg361_b1_m360_source_status", publish.split(
            "zg361_b1_publish_m360_cohort_source_effect = yes", 1
        )[0])
        self.assertIn("name = zg361_b1_m360_source_status value = 1", source)
        self.assertIn("name = zg361_b1_m360_source_status value = 2", source)
        self.assertIn("name = zg361_b1_m360_source_status value = 3", source)
        for reason in (1, 2, 3, 4, 101, 102, 103, 104, 105):
            self.assertIn(
                f"name = zg361_b1_m360_source_reason value = {reason}", source
            )
        self.assertIn("var:zg361_b1_agenda_mode = 3", source)
        self.assertIn("var:zg361_pending_325_n = 0", source)
        self.assertIn("var:zg361_pending_325_n > 6", source)
        self.assertIn("name = zg361_b1_m360_work_missing_fields value = 1", source)
        self.assertIn("name = zg361_b1_m360_work_tuple_mismatch value = 1", source)
        self.assertIn("remove_variable = zg361_b1_m360_source_reason", source)
        # Only READY materializes product IDs and business payload.
        self.assertEqual(source.count("name = zg361_b1_m360_source_id"), 1)
        self.assertEqual(source.count("name = zg361_b1_m360_source_hash"), 1)
        self.assertEqual(
            source.count("name = zg361_b1_m360_source_available value = 1"), 1
        )

    def test_band_order_and_feedback_debt_have_next_cycle_consumers(self) -> None:
        band = top_level_block(self.effects, "zg361_b1_freeze_band_order_effect")
        self.assertIn("var:zg361_pending_grade = 2", band)
        self.assertNotIn("var:zg361_pending_grade = 3", band)
        self.assertNotIn("var:zg361_pending_grade = 1", band)
        self.assertEqual(
            band.count("order_by = var:zg361_b1_band_order_sort_key"), 1
        )
        self.assertIn(
            "value = var:zg361_b1_calibration_score multiply = 1000000", band
        )
        self.assertIn(
            "subtract = { value = var:zg361_b1_roster_frozen_order multiply = 1000 }",
            band,
        )
        self.assertIn("subtract = var:zg361_b1_case_serial", band)
        self.assertEqual(
            band.count("name = zg361_b1_band_order value = root.var:zg361_b1_band_cursor"),
            1,
        )
        band_code = without_comments(band)
        self.assertNotIn("name = zg361_pending_grade", band_code)
        self.assertNotIn("add_prestige", band_code)
        midcycle = top_level_block(
            self.effects, "zg361_b1_midcycle_dispatcher_effect"
        )
        self.assertIn("var:zg361_b1_previous_band_order >= 1", midcycle)
        self.assertIn("name = zg361_b1_coaching_priority", midcycle)
        self.assertIn("name = zg361_b1_opportunity_grant", midcycle)

        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        self.assertIn("var:zg361_b1_final_grade < var:zg361_b1_shadow_grade", publish)
        self.assertIn("root.var:zg361_b1_m135_mode != 3", publish)
        self.assertIn("name = zg361_b1_feedback_debt_open_n add = 1", publish)
        self.assertIn("name = zg361_b1_feedback_debt_due_year", publish)
        liability = top_level_block(
            self.effects, "zg361_b1_consume_manager_liabilities_as_subject_effect"
        )
        self.assertIn("var:zg361_b1_feedback_debt_due_year <= current_year", liability)
        self.assertIn("multiply = -5", liability)
        self.assertIn("name = zg361_b1_feedback_debt_open_n value = 0", liability)

    def test_141_direct_manager_owns_atomic_conserved_swap_and_terminal_receipt(self) -> None:
        prepare = top_level_block(
            self.effects, "zg361_b1_prepare_bank_must_review_effect"
        )
        consume = top_level_block(
            self.effects, "zg361_b1_consume_must_review_effect"
        )
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_must_review_object_{field}", prepare)
        self.assertIn(
            "name = zg361_b1_must_review_object_owner value = scope:zg361_b1_must_review_manager",
            prepare,
        )
        self.assertIn("var:zg361_b1_must_review_route = 2", consume)
        self.assertIn("var:zg361_pending_grade = 2", consume)
        self.assertIn("var:zg361_pending_grade = 3", consume)
        self.assertIn("name = zg361_pending_grade value = 3", consume)
        self.assertIn("name = zg361_pending_grade value = 2", consume)
        for field in (
            "before_top",
            "before_middle",
            "before_bottom",
            "after_top",
            "after_middle",
            "after_bottom",
            "subject_before",
            "subject_after",
            "peer_before",
            "peer_after",
            "book_version_before",
            "book_version_after",
            "conservation_valid",
            "swap_executed",
        ):
            self.assertIn(f"zg361_b1_must_review_{field}", consume)
        self.assertEqual(
            consume.count(
                "change_variable = { name = zg361_b1_quota_book_version add = 1 }"
            ),
            1,
        )
        self.assertIn("name = zg361_b1_must_review_manager_link_state value = 3", consume)
        self.assertIn("name = zg361_b1_must_review_object_state value = 3", consume)
        self.assertIn("name = zg361_b1_must_review_object_state value = 2", publish)
        self.assertIn("name = zg361_b1_must_review_credit_delta value = -1", publish)
        self.assertIn("name = zg361_b1_must_review_credit_delta value = 1", publish)

    def test_142_pending_and_deferred_objects_are_separate_and_watchdog_closes_barrier(self) -> None:
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        opened = top_level_block(self.effects, "zg361_b1_open_pending_slots_effect")
        deferred = opened.split(
            "else_if = {\n\t\tlimit = { var:zg361_b1_m142_mode = 2 }", 1
        )[1].split("\n\tif = {\n\t\tlimit = { var:zg361_b1_m142_mode = 1", 1)[0]
        self.assertNotIn("zg361_b1_pending_object_", deferred)
        self.assertNotIn("zg361_b1_pending_held_band", deferred)
        self.assertNotIn("zg361_b1_pending_frozen_reward", deferred)
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_pending_next_cycle_object_{field}", deferred)
            self.assertIn(f"zg361_b1_pending_next_cycle_object_{field}", initialize)
        self.assertIn(
            "name = zg361_b1_pending_next_cycle_object_cycle value = { value = var:zg361_b1_cycle_serial add = 1 }",
            deferred,
        )
        self.assertIn(
            "name = zg361_b1_pending_next_cycle_object_state value = 2",
            initialize,
        )
        self.assertIn("zg361_b1_pending_carried_adjustment", initialize)
        self.assertIn("zg361_b1_pending_self_safe_current_final_unchanged", opened)
        self.assertIn("zg361_b1_pending_self_safe_next_cycle_evidence", opened)
        self.assertIn(
            "name = zg361_b1_pending_open_date value = current_date", opened
        )
        self.assertIn(
            "name = zg361_b1_pending_deadline_days value = 30", opened
        )
        self.assertNotIn("zg361_b1_pending_due_date", opened)
        watchdog = top_level_block(self.events, "zg361b1.125")
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_pending_object_{field}", watchdog)
        self.assertIn("name = zg361_b1_pending_object_state value = 5", watchdog)
        self.assertIn("name = zg361_b1_pending_open_n add = -1", watchdog)
        self.assertIn("name = zg361_b1_pending_open_n value = 0", watchdog)
        self.assertIn("zg361_b1_prepare_reopen_gate_effect = yes", watchdog)

    def test_143_full_cohort_batch_has_stable_result_and_distinct_next_cycle_consumer(self) -> None:
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        prepare = top_level_block(self.effects, "zg361_b1_prepare_reopen_gate_effect")
        resolve = top_level_block(
            self.effects, "zg361_b1_resolve_reopen_batch_effect"
        )
        callback = top_level_block(self.events, "zg361b1.122")
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_reopen_batch_{field}", prepare)
            self.assertIn(f"zg361_b1_reopen_object_{field}", prepare)
        self.assertIn("variable = zg361_b1_processing_subjects", prepare)
        self.assertIn(
            "var:zg361_b1_reopen_processed_n = var:zg361_b1_reopen_batch_expected_n",
            resolve,
        )
        self.assertIn("order_by = var:zg361_b1_reopen_stable_order_key", resolve)
        self.assertIn(
            "value = var:zg361_b1_reopen_late_evidence_magnitude multiply = 1000000",
            callback,
        )
        self.assertIn("subtract = var:zg361_b1_reopen_object_case", callback)
        self.assertIn("name = zg361_b1_reopen_batch_result value = 2", resolve)
        self.assertIn("name = zg361_b1_reopen_batch_result value = 3", resolve)
        self.assertIn(
            "name = zg361_b1_m143_receipt_serial value = var:zg361_b1_reopen_batch_case",
            resolve,
        )
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_reopen_next_cycle_object_{field}", callback)
            self.assertIn(f"zg361_b1_reopen_next_cycle_object_{field}", initialize)
        self.assertIn("zg361_b1_reopen_carried_adjustment", initialize)
        self.assertNotEqual(
            "zg361_b1_pending_next_cycle_object", "zg361_b1_reopen_next_cycle_object"
        )
        projection_a = top_level_block(
            self.effects, "zg361_b1_materialize_reopen_a_self_safe_effect"
        )
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_reopen_self_a_{field}", projection_a)
        self.assertIn(
            "name = zg361_b1_reopen_self_a_case value = var:zg361_b1_case_serial",
            projection_a,
        )
        self.assertIn("zg361_b1_reopen_self_a_result", projection_a)
        self.assertIn("zg361_b1_reopen_self_a_reason", projection_a)
        self.assertEqual(
            resolve.count("zg361_b1_materialize_reopen_a_self_safe_effect = yes"),
            1,
        )
        symmetric = top_level_block(
            self.effects, "zg361_b1_apply_symmetric_reopen_effect"
        )
        self.assertEqual(
            symmetric.count("zg361_b1_materialize_reopen_a_self_safe_effect = yes"),
            1,
        )
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_reopen_self_b_{field}", callback)
        self.assertIn(
            "name = zg361_b1_reopen_self_b_case value = var:zg361_b1_case_serial",
            callback,
        )
        self.assertIn(
            "name = zg361_b1_reopen_self_b_next_cycle_evidence value = 1",
            callback,
        )
        self.assertIn("zg361_b1_reopen_self_b_target_cycle", callback)

    def test_144_independent_review_and_consensus_freeze_real_identities(self) -> None:
        record = top_level_block(
            self.effects, "zg361_b1_record_named_dissent_effect"
        )
        finalize = top_level_block(
            self.effects, "zg361_b1_finalize_named_dissent_effect"
        )
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_dissent_object_{field}", record)
            self.assertIn(f"zg361_b1_consensus_{field}", record)
        self.assertIn(
            "NOT = { var:zg361_b1_dissent_reviewer = scope:zg361_b1_dissent_finalize_manager }",
            finalize,
        )
        self.assertIn("NOT = { var:zg361_b1_dissent_reviewer = this }", finalize)
        self.assertIn("var:zg361_b1_dissent_reviewer = { is_alive = yes }", finalize)
        self.assertIn("zg361_b1_dissent_review_attention_receipt_id", record)
        self.assertIn("name = zg361_b1_dissent_review_attention_consumed value = 1", finalize)
        self.assertIn("name = zg361_b1_dissent_object_state value = 3", finalize)
        self.assertIn("name = zg361_b1_dissent_review_attention_consumed value = 0", finalize)
        for slot in range(1, 5):
            self.assertIn(f"zg361_b1_consensus_manager_{slot}", record)
        self.assertIn("zg361_b1_huddle_host_attendee_n", record)
        self.assertIn("name = zg361_b1_consensus_state value = 2", finalize)

    def test_145_only_middle_receives_finite_non_compensation_consumers(self) -> None:
        band = top_level_block(self.effects, "zg361_b1_freeze_band_order_effect")
        policy = top_level_block(
            self.effects, "zg361_b1_freeze_135_145_policy_effect"
        )
        midcycle = top_level_block(self.effects, "zg361_b1_midcycle_dispatcher_effect")
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        previous_object_guard = initialize[
            initialize.index("name = zg361_b1_previous_band_object_available value = 0") :
            initialize.index("name = zg361_b1_previous_final_grade value = 0")
        ]
        self.assertIn("trigger_if = {", previous_object_guard)
        self.assertIn("trigger_else = { always = no }", previous_object_guard)
        for field in ("available", "id", "owner", "subject", "cycle", "case", "state"):
            self.assertIn(
                f"has_variable = zg361_b1_band_order_object_{field}",
                previous_object_guard,
            )
        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_band_order_batch_{field}", band)
            self.assertIn(f"zg361_b1_band_order_object_{field}", band)
        self.assertIn("var:zg361_pending_grade = 2", band)
        self.assertNotIn("var:zg361_pending_grade = 3", band)
        self.assertNotIn("var:zg361_pending_grade = 1", band)
        self.assertIn("name = zg361_b1_band_order_batch_state value = 3", band)
        self.assertIn("name = zg361_b1_band_opportunity_capacity value = 1", band)
        self.assertIn("name = zg361_b1_band_opportunity_capacity value = 2", band)
        self.assertIn("zg361_b1_band_self_public_opportunity_selected", band)
        self.assertIn("zg361_b1_band_self_public_coaching_selected", band)
        self.assertIn("zg361_b1_band_self_private_opportunity_selected", band)
        self.assertIn("name = zg361_b1_band_self_appeal_evidence value = 1", band)
        self.assertIn("name = zg361_b1_band_order_blackbox_risk value = 1", band)
        self.assertIn("var:zg361_b1_previous_band_order_use_mode = 1", midcycle)
        self.assertIn("var:zg361_b1_previous_band_order_use_mode = 2", midcycle)
        self.assertIn("name = zg361_b1_opportunity_project_available value = 1", midcycle)
        self.assertIn("name = zg361_b1_previous_band_object_state value = 2", midcycle)
        self.assertIn("has_variable = zg361_mechanism_145_choice", policy)
        self.assertIn(
            "name = zg361_b1_m145_mode value = var:zg361_mechanism_145_choice",
            policy,
        )
        self.assertIn(
            "name = zg361_b1_band_order_mode value = var:zg361_b1_m145_mode",
            band,
        )
        self.assertNotIn("zg361_mechanism_145_choice", band)
        open_cycle = top_level_block(self.effects, "zg361_b1_open_cycle_effect")
        self.assertLess(
            open_cycle.index("zg361_b1_freeze_135_145_policy_effect = yes"),
            open_cycle.index("zg361_b1_initialize_subject_case_effect = yes"),
        )
        forbidden = re.compile(
            r"(?i)(?:add_gold|gold\s*=|salary|compensation|bonus|dividend|reward)"
        )
        self.assertIsNone(forbidden.search(without_comments(band)))

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
        for label, block, order_key in (
            ("local", local, "zg361_b1_calibration_score"),
            ("common", common, "zg361_b1_quota_pool_tie_key"),
        ):
            with self.subTest(path=label):
                self.assertIn(f"order_by = var:{order_key}", block)
                self.assertNotIn("order_by = var:zg361_kpi", block)
                self.assertIn("has_variable = zg361_b1_calibration_score", block)
                self.assertIn("NOT = { has_character_flag = zg361_newcomer_this_cycle }", block)
                self.assertIn("name = zg361_b1_quota_snapshot value = var:zg361_pending_grade", block)
                self.assertIn("name = zg361_b1_shadow_to_quota_delta", block)
                self.assertIn("name = zg361_b1_forced_down value = 1", block)
        self.assertIn(
            "zg361_b1_compute_exact_quota_effect = { COHORT_SIZE = var:zg361_b1_local_candidate_n ROUNDING_SCOPE = 1 }",
            local,
        )
        self.assertIn("name = zg361_b1_local_top_slots value = var:zg361_b1_quota_top_slots", local)
        self.assertIn("name = zg361_b1_local_middle_slots value = var:zg361_b1_quota_middle_slots", local)
        self.assertIn("name = zg361_b1_local_bottom_slots value = var:zg361_b1_quota_bottom_slots", local)
        self.assertIn("var:zg361_b1_roster_included = 1", local)
        self.assertIn("name = zg361_b1_local_bottom_candidate_n", local)
        self.assertIn("var:zg361_b1_local_bottom_candidate_n >= 1", local)
        self.assertIn("name = zg361_pending_375_n value = 0", local)
        self.assertIn("name = zg361_pending_35_n value = 0", local)
        self.assertIn("name = zg361_pending_325_n value = 0", local)
        self.assertIn("name = zg361_pending_375_n add = 1", local)
        self.assertIn("name = zg361_pending_35_n add = 1", local)
        self.assertIn("name = zg361_pending_325_n add = 1", local)
        self.assertIn("name = zg361_b1_unique_pool_bottom_candidate_n", common)
        self.assertIn("var:zg361_b1_unique_pool_bottom_candidate_n >= 1", common)

        submit = top_level_block(self.effects, "zg361_b1_submit_quota_book_effect")
        self.assertLess(
            submit.index("zg361_b1_rebuild_local_quota_effect = yes"),
            submit.index("has_variable = zg361_b1_bank_superior"),
        )

    def test_quota_reference_matrix_and_three_plus_four_pool(self) -> None:
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
        self.assertEqual(
            {
                size: (
                    compute_quota(size).effective_counts.top,
                    compute_quota(size).effective_counts.middle,
                    compute_quota(size).effective_counts.bottom,
                )
                for size in expected
            },
            expected,
        )
        self.assertEqual(sum((3, 4)), 7)
        exact = top_level_block(
            self.effects, "zg361_b1_compute_exact_quota_effect"
        )
        for token in (
            "zg361_b1_quota_top_raw_numerator",
            "zg361_b1_quota_middle_raw_numerator",
            "zg361_b1_quota_bottom_raw_numerator",
            "zg361_b1_quota_top_floor",
            "zg361_b1_quota_middle_floor",
            "zg361_b1_quota_bottom_floor",
            "zg361_b1_quota_top_remainder",
            "zg361_b1_quota_middle_remainder",
            "zg361_b1_quota_bottom_remainder",
            "zg361_b1_quota_top_award",
            "zg361_b1_quota_middle_award",
            "zg361_b1_quota_bottom_award",
            "zg361_b1_quota_conservation_check",
        ):
            self.assertIn(token, exact)
        self.assertIn("var:zg361_b1_quota_cohort_size < 3", exact)
        for formula in (
            "value = var:zg361_b1_quota_cohort_size multiply = 3",
            "value = var:zg361_b1_quota_cohort_size multiply = 6",
            "name = zg361_b1_quota_bottom_raw_numerator value = var:zg361_b1_quota_cohort_size",
            "value = var:zg361_b1_quota_top_raw_numerator divide = 10 floor = yes",
            "value = var:zg361_b1_quota_middle_raw_numerator divide = 10 floor = yes",
            "value = var:zg361_b1_quota_bottom_raw_numerator divide = 10 floor = yes",
            "subtract = var:zg361_b1_quota_top_floor",
            "subtract = var:zg361_b1_quota_middle_floor",
            "subtract = var:zg361_b1_quota_bottom_floor",
        ):
            self.assertIn(formula, exact)
        self.assertNotIn("multiply = 0.3", exact)
        self.assertNotIn("multiply = 0.1", exact)
        self.assertNotIn("round = yes", exact)
        self.assertIn(
            "var:zg361_b1_quota_top_remainder >= var:zg361_b1_quota_middle_remainder",
            exact,
        )
        self.assertIn("23=7/14/2", exact)
        common = top_level_block(
            self.effects, "zg361_b1_close_common_superior_bank_effect"
        )
        self.assertIn("var:zg361_b1_unique_pool_three_n = 1", common)
        self.assertIn("var:zg361_b1_unique_pool_four_n = 1", common)
        self.assertIn(
            "scope:zg361_b1_pool_three_manager.var:zg361_b1_quota_function_code = scope:zg361_b1_pool_four_manager.var:zg361_b1_quota_function_code",
            common,
        )
        self.assertIn("var:zg361_b1_unique_pool_n = 7", common)
        self.assertIn(
            "COHORT_SIZE = var:zg361_b1_unique_pool_n", common
        )
        self.assertIn("order_by = var:zg361_b1_quota_pool_tie_key", common)
        self.assertIn(
            "value = var:zg361_b1_calibration_score multiply = 10000", common
        )
        self.assertNotIn("order_by = var:zg361_kpi", common)
        for field in (
            "zg361_b1_quota_pool_top_raw_numerator",
            "zg361_b1_quota_pool_middle_raw_numerator",
            "zg361_b1_quota_pool_bottom_raw_numerator",
            "zg361_b1_quota_pool_top_floor",
            "zg361_b1_quota_pool_middle_floor",
            "zg361_b1_quota_pool_bottom_floor",
            "zg361_b1_quota_pool_top_remainder",
            "zg361_b1_quota_pool_middle_remainder",
            "zg361_b1_quota_pool_bottom_remainder",
            "zg361_b1_quota_pool_top_award",
            "zg361_b1_quota_pool_middle_award",
            "zg361_b1_quota_pool_bottom_award",
            "zg361_b1_quota_pool_rounding_method",
            "zg361_b1_quota_pool_conservation_check",
        ):
            self.assertIn(field, common)

    def test_delayed_review_prunes_unavailable_weak_subjects_before_reads(self) -> None:
        prune = top_level_block(
            self.effects, "zg361_b1_prune_unavailable_subjects_effect"
        )
        for token in (
            "variable = zg361_b1_subjects",
            "limit = { exists = this }",
            "name = zg361_b1_available_subjects",
            "clear_variable_list = zg361_b1_subjects",
            "name = zg361_b1_subject_n value = list_size:zg361_b1_subjects",
            "name = zg361_b1_m040_review_vacancy_n add = var:zg361_b1_roster_pruned_n",
            "name = zg361_b1_roster_amendment_n add = var:zg361_b1_roster_pruned_n",
            "name = zg361_b1_roster_reopen_required value = 1",
        ):
            self.assertIn(token, prune)
        self.assertLess(
            prune.index("limit = { exists = this }"),
            prune.index("clear_variable_list = zg361_b1_subjects"),
        )

        midcycle_event = top_level_block(self.events, "zg361b1.100")
        self.assertLess(
            midcycle_event.index(
                "zg361_b1_prune_unavailable_subjects_effect = yes"
            ),
            midcycle_event.index("zg361_b1_midcycle_dispatcher_effect = yes"),
        )

    def test_roster_change_receipts_are_real_and_consumed_by_denominator(self) -> None:
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        kernel = initialize.split(
            "zg361_case_kernel_record_operation_effect = {", 1
        )[1]
        for token in (
            "OWNER_VAR = zg361_b1_case_owner",
            "SUBJECT_VAR = zg361_b1_case_subject",
            "CYCLE_VAR = zg361_b1_cycle_serial",
            "CASE_VAR = zg361_b1_case_serial",
            "STATE_VAR = zg361_b1_case_state",
            "ACTIVE_VAR = zg361_b1_case_active",
            "OPERATION_ID = 39",
        ):
            self.assertIn(token, kernel)
        audit = top_level_block(
            self.effects, "zg361_b1_audit_frozen_roster_effect"
        )
        for field in (
            "zg361_b1_roster_change_before",
            "zg361_b1_roster_change_after",
            "zg361_b1_roster_change_reason",
            "zg361_b1_roster_change_actor",
            "zg361_b1_roster_change_approver",
            "zg361_b1_roster_change_year",
            "zg361_b1_roster_change_version",
        ):
            self.assertIn(field, audit)
        self.assertLess(
            audit.index("zg361_b1_roster_change_before value = 1"),
            audit.index("zg361_b1_roster_included value = 0"),
        )
        local = top_level_block(
            self.effects, "zg361_b1_rebuild_local_quota_effect"
        )
        self.assertLess(
            local.index("zg361_b1_audit_frozen_roster_effect = yes"),
            local.index("COHORT_SIZE = var:zg361_b1_local_candidate_n"),
        )
        self.assertIn("zg361_b1_roster_change_reason value = 1", audit)
        self.assertIn("zg361_b1_roster_change_reason value = 2", audit)
        self.assertIn("zg361_b1_roster_change_reason value = 3", audit)
        self.assertIn("name = zg361_b1_quota_rebuilt_for_roster value = 1", local)
        self.assertIn("name = zg361_b1_roster_reopen_required value = 0", local)

        additions = top_level_block(
            self.effects, "zg361_b1_audit_locked_roster_additions_effect"
        )
        prepare = top_level_block(self.effects, "zg361_b1_prepare_facts_effect")
        self.assertLess(
            prepare.index("zg361_b1_audit_locked_roster_additions_effect = yes"),
            prepare.index("variable = zg361_b1_subjects"),
        )
        for marker in (
            "is_target_in_variable_list = {",
            "target = scope:zg361_b1_roster_add_subject",
            "var:zg361_b1_roster_backfill_needed >= 1",
            "var:zg361_b1_subject_n < 80",
            "name = zg361_b1_roster_change_before value = 0",
            "name = zg361_b1_roster_change_after value = 1",
            "name = zg361_b1_roster_change_reason value = 4",
            "name = zg361_b1_roster_change_reason value = 5",
            "zg361_b1_initialize_subject_case_effect = yes",
            "name = zg361_b1_case_state value = 3",
            "name = zg361_b1_subjects",
        ):
            self.assertIn(marker, additions)
        self.assertIn("name = zg361_b1_roster_included value = 1", initialize)

    def test_gray_leaver_freezes_roster_identity_but_not_employment_state(self) -> None:
        open_cycle = top_level_block(self.effects, "zg361_b1_open_cycle_effect")
        for policy_marker in (
            "name = zg361_b1_m040_mode value = 1",
            "has_variable = zg361_mechanism_040_choice",
            "name = zg361_b1_m040_mode value = var:zg361_mechanism_040_choice",
            "name = zg361_b1_m040_gray_used value = 0",
            "name = zg361_b1_m040_frozen_leaver_n value = 0",
            "name = zg361_b1_m040_hc_vacancy_n value = 0",
            "name = zg361_b1_m040_review_vacancy_n value = 0",
        ):
            self.assertIn(policy_marker, open_cycle)

        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        for marker in (
            "name = zg361_b1_roster_included value = 1",
            "name = zg361_b1_roster_employment_state value = 1",
            "name = zg361_b1_leaver_route value = 0",
            "name = zg361_b1_leaver_quota_source value = 0",
            "name = zg361_b1_leaver_receipt_state value = 0",
            "name = zg361_b1_roster_frozen_title value = primary_title",
            "zg361_b1_snapshot_owner_bound_kpi_effect = yes",
        ):
            self.assertIn(marker, initialize)

        audit = top_level_block(
            self.effects, "zg361_b1_audit_frozen_roster_effect"
        )
        # The once-only gate is the live employment state, not removal from the
        # D+0 denominator.  Alive A/B leavers therefore remain included.
        self.assertIn("var:zg361_b1_roster_employment_state = 1", audit)
        employment_write = audit.index(
            "set_variable = { name = zg361_b1_roster_employment_state value = 2 }"
        )
        self.assertLess(
            employment_write,
            audit.index(
                "change_variable = { name = zg361_b1_m040_hc_vacancy_n add = 1 }"
            ),
        )
        self.assertIn("name = zg361_b1_leaver_route value = 1", audit)
        self.assertIn("name = zg361_b1_leaver_route value = 2", audit)
        self.assertIn("name = zg361_b1_m040_gray_used value = 1", audit)
        self.assertIn("name = zg361_b1_m040_gray_subject value = prev", audit)
        self.assertIn("name = zg361_b1_m040_frozen_leaver_n add = 1", audit)
        self.assertIn("name = zg361_b1_m040_review_vacancy_n add = 1", audit)
        # Only death/explicit route C opens a review vacancy and removes the
        # row.  The separate HC vacancy cannot authorize an N+1 quota row.
        route_c = audit.split(
            "# Death and explicit C create a review vacancy.", 1
        )[1]
        self.assertIn("name = zg361_b1_roster_included value = 0", route_c)
        self.assertIn("name = zg361_b1_leaver_route value = 3", route_c)

        additions = top_level_block(
            self.effects, "zg361_b1_audit_locked_roster_additions_effect"
        )
        self.assertIn("var:zg361_b1_m040_frozen_leaver_n = 0", additions)
        self.assertIn(
            "name = zg361_b1_roster_backfill_needed value = var:zg361_b1_roster_amendment_n",
            additions,
        )

    def test_departed_kpi_and_result_remain_bound_to_the_frozen_owner(self) -> None:
        snapshot = top_level_block(
            self.effects, "zg361_b1_snapshot_owner_bound_kpi_effect"
        )
        for identity in (
            "var:zg361_b1_case_owner = root",
            "var:zg361_b1_case_subject = this",
            "var:zg361_b1_cycle_serial = root.var:zg361_b1_cycle_serial",
            "var:zg361_b1_case_serial = root.var:zg361_b1_case_serial",
            "liege = root",
        ):
            self.assertIn(identity, snapshot)
        for component in (
            "governance",
            "capability",
            "growth",
            "superior",
            "values",
            "collaboration",
            "jingcha",
            "organization",
        ):
            self.assertIn(f"zg361_b1_owner_bound_evidence_{component}", snapshot)

        materialize = top_level_block(
            self.effects, "zg361_b1_materialize_departed_kpi_effect"
        )
        self.assertIn("var:zg361_b1_roster_employment_state = 2", materialize)
        self.assertIn(
            "OR = { var:zg361_b1_leaver_route = 1 var:zg361_b1_leaver_route = 2 }",
            materialize,
        )
        self.assertIn(
            "var:zg361_b1_owner_bound_snapshot_owner = root", materialize
        )
        self.assertIn(
            "name = zg361_kpi value = var:zg361_b1_owner_bound_kpi",
            materialize,
        )
        self.assertNotIn("zg361_compute_kpi_effect = yes", materialize)

        settle = top_level_block(
            self.effects, "zg361_b1_apply_departed_grade_effect"
        )
        self.assertIn("zg361_freeze_result_case_effect = yes", settle)
        self.assertIn("name = zg361_last_grade value = var:zg361_pending_grade", settle)
        self.assertIn("name = zg361_result_delivery_method value = 5", settle)
        for forbidden in (
            "add_character_modifier",
            "remove_treasury",
            "remove_short_term_gold",
            "change_merit",
            "add_opinion",
            "zg361_b2_on_result_frozen_effect",
        ):
            self.assertNotIn(forbidden, settle)

    def test_gray_leaver_uses_one_existing_c_at_the_final_seal(self) -> None:
        gray = top_level_block(
            self.effects, "zg361_b1_apply_final_gray_leaver_effect"
        )
        for exact_guard in (
            "var:zg361_b1_m040_mode = 2",
            "var:zg361_b1_m040_gray_used = 1",
            "var:zg361_b1_case_owner = scope:zg361_b1_m040_manager",
            "var:zg361_b1_case_subject = this",
            "var:zg361_b1_case_state = 7",
            "var:zg361_b1_case_active = 1",
            "var:zg361_b1_roster_included = 1",
            "var:zg361_b1_roster_employment_state = 2",
            "var:zg361_b1_leaver_route = 2",
        ):
            self.assertIn(exact_guard, gray)
        self.assertIn("limit = { var:zg361_pending_325_n >= 1 }", gray)
        self.assertIn("name = zg361_b1_leaver_quota_source value = 1", gray)
        self.assertIn("name = zg361_b1_leaver_quota_source value = 2", gray)
        self.assertIn("name = zg361_b1_leaver_quota_source value = 3", gray)
        self.assertIn("name = zg361_b1_leaver_swap_partner", gray)
        self.assertIn("name = zg361_grade_reason_override value = 9", gray)
        self.assertIn("name = zg361_grade_reason_override value = 10", gray)
        self.assertEqual(gray.count("remove_variable = zg361_calibration_reason"), 2)
        self.assertIn("name = zg361_b1_forced_down value = 0", gray)
        self.assertIn("name = zg361_b1_leaver_receipt_state value = 2", gray)
        self.assertIn("name = zg361_b1_leaver_receipt_state value = 3", gray)
        self.assertIn("zg361_b1_verify_frozen_quota_conservation_effect = yes", gray)
        # The operation swaps two assignments; it never edits the three quota
        # totals, so 23 remains exactly 7/14/2 and small zero-C cohorts block.
        for count_field in (
            "zg361_pending_375_n",
            "zg361_pending_35_n",
            "zg361_pending_325_n",
        ):
            self.assertNotIn(f"name = {count_field} value", gray)
            self.assertNotIn(f"name = {count_field} add", gray)

        finish = top_level_block(
            self.effects, "zg361_b1_finish_calibration_effect"
        )
        apply_gray = finish.index("zg361_b1_apply_final_gray_leaver_effect = yes")
        self.assertLess(apply_gray, finish.index("zg361_b1_freeze_band_order_effect = yes"))
        self.assertLess(apply_gray, finish.index("zg361_b1_pay_frozen_pending_rewards_effect = yes"))
        self.assertLess(apply_gray, finish.index("zg361_apply_pending_grades_effect = yes"))

    def test_departed_subject_crosses_review_settlement_and_scoreboard_projection(self) -> None:
        run_review = top_level_block(self.core, "zg361_run_review_effect")
        b1_review = run_review.split(
            "# B1 uses the roster frozen at D+0.", 1
        )[1].split("\n\telse = {", 1)[0]
        self.assertIn("variable = zg361_b1_subjects", b1_review)
        self.assertIn("zg361_b1_materialize_departed_kpi_effect = yes", b1_review)
        self.assertIn("add_to_list = zg361_cohort", b1_review)

        apply_grades = top_level_block(
            self.core, "zg361_apply_pending_grades_effect"
        )
        b1_settle = apply_grades.split(
            "has_character_flag = zg361_b1_cycle_active", 1
        )[1].split("\n\telse = {", 1)[0]
        self.assertIn("variable = zg361_b1_subjects", b1_settle)
        self.assertIn("zg361_b1_apply_departed_grade_effect = yes", b1_settle)

        publish = top_level_block(self.core, "zg361_publish_scoreboard_effect")
        self.assertEqual(publish.count("variable = zg361_b1_subjects"), 2)
        self.assertIn("add_to_list = zg361_scoreboard_candidates", publish)
        self.assertIn("add_to_list = zg361_scoreboard_recipients", publish)
        self.assertIn("var:zg361_b1_roster_included = 1", publish)

    def test_departed_subject_is_not_carried_into_the_next_cycle(self) -> None:
        open_cycle = top_level_block(self.effects, "zg361_b1_open_cycle_effect")
        clear = open_cycle.index("clear_variable_list = zg361_b1_subjects")
        rebuild = open_cycle.index("every_vassal = {", clear)
        initialize = open_cycle.index("zg361_b1_initialize_subject_case_effect = yes", rebuild)
        self.assertLess(clear, rebuild)
        self.assertLess(rebuild, initialize)

        published = top_level_block(
            self.effects, "zg361_b1_mark_published_effect"
        )
        self.assertIn("name = zg361_b1_case_state value = 8", published)
        self.assertIn("name = zg361_b1_case_active value = 0", published)
        self.assertIn("remove_character_flag = zg361_b1_cycle_active", published)

    def test_newcomer_protection_preserves_exact_top_and_bottom_counts(self) -> None:
        blocks = (
            top_level_block(self.effects, "zg361_b1_rebuild_local_quota_effect"),
            top_level_block(self.effects, "zg361_b1_close_common_superior_bank_effect"),
            top_level_block(self.effects, "zg361_b1_rerank_frozen_quota_book_effect"),
        )
        for block in blocks:
            with self.subTest(block=block.split(" =", 1)[0]):
                bottom_write = block.index(
                    "set_variable = { name = zg361_pending_grade value = 1 }"
                )
                top_write = block.index(
                    "set_variable = { name = zg361_pending_grade value = 3 }",
                    bottom_write,
                )
                self.assertLess(bottom_write, top_write)
                self.assertIn("newcomer_bottom_exception", block)
                self.assertIn("newcomer_forced_bottom", block)
                self.assertIn("limit = { var:zg361_pending_grade = 2 }", block)

        # Negative fixtures freeze the edge that once lost a TOP when newcomer
        # protection overwrote an already-promoted subject.  They include all-
        # newcomer and insufficient-incumbent cohorts at both reference sizes.
        def assign(size: int, newcomer_indexes: set[int]) -> tuple[int, int, int, int]:
            counts = compute_quota(size).effective_counts
            grades = [2] * size
            bottom_assigned = 0
            for index in range(size - 1, -1, -1):
                if index not in newcomer_indexes and bottom_assigned < counts.bottom:
                    grades[index] = 1
                    bottom_assigned += 1
            forced_newcomers = 0
            for index in range(size - 1, -1, -1):
                if grades[index] == 2 and bottom_assigned < counts.bottom:
                    grades[index] = 1
                    bottom_assigned += 1
                    forced_newcomers += int(index in newcomer_indexes)
            top_assigned = 0
            for index in range(size):
                if grades[index] == 2 and top_assigned < counts.top:
                    grades[index] = 3
                    top_assigned += 1
            return (
                grades.count(3),
                grades.count(2),
                grades.count(1),
                forced_newcomers,
            )

        for size, newcomers in (
            (7, set(range(7))),
            (14, set(range(13))),
            (23, set(range(23))),
            (23, {0, 1, 2, 3, 4, 5, 6}),
        ):
            with self.subTest(size=size, newcomers=len(newcomers)):
                expected = compute_quota(size).effective_counts
                top, middle, bottom, forced = assign(size, newcomers)
                self.assertEqual(
                    (top, middle, bottom),
                    (expected.top, expected.middle, expected.bottom),
                )
                self.assertEqual(
                    forced > 0,
                    size - len(newcomers) < expected.bottom,
                )

    def test_one_slot_trade_creates_bilateral_next_cycle_one_shot_debt(self) -> None:
        trade = top_level_block(
            self.effects, "zg361_b1_execute_unique_pool_trade_effect"
        )
        self.assertIn("var:zg361_b1_unique_pool_trade_used = 0", trade)
        self.assertIn("name = zg361_b1_quota_trade_slots value = 1", trade)
        self.assertIn("name = zg361_b1_quota_trade_band value = 3", trade)
        self.assertIn("change_variable = { name = zg361_pending_375_n add = -1 }", trade)
        self.assertIn("change_variable = { name = zg361_pending_375_n add = 1 }", trade)
        self.assertIn("change_variable = { name = zg361_pending_35_n add = 1 }", trade)
        self.assertIn("change_variable = { name = zg361_pending_35_n add = -1 }", trade)
        self.assertEqual(trade.count("change_variable = { name = zg361_b1_quota_book_version add = 1 }"), 2)
        for field in (
            "zg361_b1_quota_debt_creditor",
            "zg361_b1_quota_debt_debtor",
            "zg361_b1_quota_debt_approver",
            "zg361_b1_quota_debt_liability",
            "zg361_b1_quota_debt_source_trade",
            "zg361_b1_quota_credit_creditor",
            "zg361_b1_quota_credit_debtor",
            "zg361_b1_quota_credit_due_cycle",
            "zg361_b1_quota_credit_source_trade",
            "zg361_b1_quota_credit_liability",
        ):
            self.assertIn(field, trade)
        self.assertIn("NOT = { var:zg361_b1_quota_credit_state = 1 }", trade)
        self.assertGreaterEqual(
            trade.count("value = { value = var:zg361_b1_cycle_serial add = 1 }"),
            2,
        )
        settle = top_level_block(
            self.effects, "zg361_b1_settle_due_debt_effect"
        )
        self.assertIn("var:zg361_b1_quota_debt_state = 1", settle)
        self.assertIn(
            "var:zg361_b1_cycle_serial >= var:zg361_b1_quota_debt_due_cycle",
            settle,
        )
        self.assertIn("name = zg361_b1_quota_debt_state value = 2", settle)
        for reciprocal_identity in (
            "var:zg361_b1_quota_credit_creditor = this",
            "var:zg361_b1_quota_credit_due_cycle = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_due_cycle",
            "var:zg361_b1_quota_credit_source_trade = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_source_trade",
            "var:zg361_b1_quota_credit_liability = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_liability",
        ):
            self.assertIn(reciprocal_identity, settle)
        self.assertGreaterEqual(
            settle.count(
                "var:zg361_b1_quota_credit_source_trade = scope:zg361_b1_debt_manager.var:zg361_b1_quota_debt_source_trade"
            ),
            2,
        )
        self.assertIn("one-shot quota responsibility debt settled", settle)
        self.assertGreaterEqual(
            trade.count("name = zg361_b1_forced_down value = 0"), 2
        )
        self.assertIn("var:zg361_absolute_grade > 2", trade)
        self.assertIn("var:zg361_absolute_grade > 3", trade)
        self.assertGreaterEqual(
            settle.count("name = zg361_b1_forced_down value = 0"), 2
        )
        self.assertGreaterEqual(
            settle.count("name = zg361_b1_forced_down value = 1"), 2
        )
        for block in (trade, settle):
            self.assertIn("var:zg361_b1_case_subject = this", block)
            self.assertIn("var:zg361_b1_case_active = 1", block)
            self.assertIn("var:zg361_b1_roster_included = 1", block)

    def test_agenda_attention_and_overtime_are_conserved_consumers(self) -> None:
        open_cycle = top_level_block(self.effects, "zg361_b1_open_cycle_effect")
        self.assertIn("name = zg361_b1_agenda_rotation_start value = 1", open_cycle)
        self.assertIn("name = zg361_b1_agenda_rotation_start add = 1", open_cycle)
        self.assertIn(
            "var:zg361_b1_agenda_rotation_start > var:zg361_b1_subject_n",
            open_cycle,
        )
        self.assertIn("name = zg361_b1_roster_frozen_order", open_cycle)
        block = top_level_block(
            self.effects, "zg361_b1_build_agenda_and_attention_effect"
        )
        self.assertIn("clear_variable_list = zg361_b1_agenda_subjects", block)
        self.assertIn("name = zg361_b1_agenda_order", block)
        self.assertIn("name = zg361_b1_agenda_version", block)
        self.assertIn("name = zg361_b1_agenda_mode", block)
        self.assertIn("name = zg361_b1_agenda_rotation_distance", block)
        self.assertIn(
            "var:zg361_b1_roster_frozen_order subtract = scope:zg361_b1_agenda_manager.var:zg361_b1_agenda_rotation_start",
            block,
        )
        self.assertIn("add = scope:zg361_b1_agenda_manager.var:zg361_b1_subject_n", block)
        self.assertIn("name = zg361_b1_attention_total_seats", block)
        self.assertIn(
            "value = var:zg361_b1_processing_n max = 3",
            block,
        )
        self.assertNotIn("value = var:zg361_b1_agenda_n min = 3", block)
        self.assertIn("name = zg361_b1_attention_evidence_serial", block)
        self.assertIn("name = zg361_b1_attention_consumed value = 1", block)
        self.assertIn("name = zg361_b1_pending_candidate value = 1", block)
        self.assertIn("name = zg361_b1_attention_displaced value = 1", block)
        self.assertIn("name = zg361_b1_attention_overtime_minutes value = 10", block)
        self.assertIn("add_prestige = -25", block)
        self.assertIn("add_stress = 10", block)
        self.assertIn(
            "subtract = var:zg361_b1_attention_spent_minutes min = 0",
            block,
        )
        self.assertNotIn(
            "subtract = var:zg361_b1_attention_spent_minutes max = 0",
            block,
        )
        code = without_comments(block)
        self.assertNotIn("set_variable = { name = zg361_pending_grade", code)

    def test_multi_subject_pending_has_kernel_deadline_and_success_failure(self) -> None:
        open_pending = top_level_block(
            self.effects, "zg361_b1_open_pending_slots_effect"
        )
        self.assertIn("variable = zg361_b1_processing_subjects", open_pending)
        self.assertIn(
            "every_in_list = {\n\t\t\tvariable = zg361_b1_processing_subjects",
            open_pending,
        )
        # The only max=1 is the deterministic one-peer MIDDLE reservation for
        # each independently processed TOP subject; it does not cap subjects.
        self.assertEqual(
            len(re.findall(r"(?m)^\s*max = 1\s*$", open_pending)), 1
        )
        self.assertIn("change_variable = { name = zg361_b1_pending_open_n add = 1 }", open_pending)
        self.assertIn("zg361_b1_pending_fallback_middle_available", open_pending)
        self.assertIn("zg361_b1_pending_target_score", open_pending)
        for field in (
            "zg361_b1_pending_milestone",
            "zg361_b1_pending_verifier",
            "zg361_b1_pending_deadline_cycle",
            "zg361_b1_pending_frozen_reward",
            "zg361_b1_pending_held_band",
            "zg361_b1_pending_fallback_band",
        ):
            self.assertIn(field, open_pending)
        self.assertIn("zg361_case_kernel_schedule_deadline_effect = {", open_pending)
        self.assertIn("EVENT = zg361b1.121", open_pending)
        deadline = top_level_block(self.events, "zg361b1.121")
        self.assertIn("zg361_case_kernel_expire_deadline_effect = {", deadline)
        for token in (
            "OWNER_VAR = zg361_b1_case_owner",
            "SUBJECT_VAR = zg361_b1_case_subject",
            "CYCLE_VAR = zg361_b1_cycle_serial",
            "CASE_VAR = zg361_b1_case_serial",
            "STATE_VAR = zg361_b1_case_state",
            "ACTIVE_VAR = zg361_b1_case_active",
        ):
            self.assertIn(token, deadline)
        self.assertIn("name = zg361_b1_pending_observed_score value = zg361_kpi_value", deadline)
        self.assertIn("name = zg361_b1_pending_observation_recorded value = 1", deadline)
        self.assertIn("var:zg361_b1_case_subject = this", deadline)
        self.assertIn("var:zg361_b1_case_active = 1", deadline)
        self.assertIn("var:zg361_b1_roster_included = 1", deadline)
        self.assertIn("stale pending milestone ticket ignored", deadline)
        resolve = top_level_block(
            self.effects, "zg361_b1_resolve_pending_subject_effect"
        )
        self.assertIn("name = zg361_b1_pending_resolution value = 1", resolve)
        self.assertIn("name = zg361_b1_pending_resolution value = 2", resolve)
        self.assertNotIn("name = zg361_b1_pending_resolution value = 3", resolve)
        self.assertIn("name = zg361_b1_pending_reward_due value = var:zg361_b1_pending_frozen_reward", resolve)
        self.assertIn("var:zg361_b1_pending_observed_score >= var:zg361_b1_pending_target_score", resolve)
        self.assertIn("var:zg361_b1_pending_observation_recorded = 1", resolve)
        self.assertIn(
            "change_variable = { name = zg361_b1_pending_fallback_middle_available add = 1 }",
            resolve,
        )
        self.assertIn("name = zg361_b1_forced_down value = 1", resolve)
        self.assertIn(
            "change_variable = { name = zg361_b1_pending_reward_book_version add = 1 }",
            resolve,
        )
        self.assertIn(
            "change_variable = { name = zg361_b1_quota_book_version add = 1 }",
            resolve,
        )
        self.assertNotIn("add_prestige = 25", resolve)
        failure = resolve.split("else = {", 1)[1]
        self.assertEqual(
            failure.count("name = zg361_pending_grade value = 3"), 1
        )
        self.assertEqual(
            failure.count("name = zg361_pending_grade value = 2"), 1
        )
        self.assertIn("zg361_b1_pending_fallback_subject = {", failure)
        continuation = top_level_block(self.events, "zg361b1.123")
        self.assertIn("var:zg361_b1_pending_open_n = 0", continuation)
        self.assertIn("var:zg361_b1_case_active = 1", continuation)
        self.assertIn("var:zg361_b1_roster_included = 1", continuation)
        self.assertIn("stale pending continuation ticket ignored", continuation)

    def test_pending_publishes_stable_subjects_then_revises_each_resolved_row(self) -> None:
        initialize = top_level_block(
            self.effects, "zg361_b1_initialize_subject_case_effect"
        )
        refresh = top_level_block(
            self.effects, "zg361_b1_refresh_individual_publications_effect"
        )
        opened = top_level_block(self.effects, "zg361_b1_open_pending_slots_effect")
        resolved = top_level_block(
            self.effects, "zg361_b1_resolve_pending_subject_effect"
        )
        reopened = top_level_block(
            self.effects, "zg361_b1_apply_symmetric_reopen_effect"
        )
        finished = top_level_block(
            self.effects, "zg361_b1_finish_calibration_effect"
        )
        notice = top_level_block(self.events, "zg361b1.126")

        for field in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"zg361_b1_local_publish_object_{field}", initialize)
            self.assertIn(f"zg361_b1_local_publish_object_{field}", refresh)
        for token in (
            "variable = zg361_b1_processing_subjects",
            "var:zg361_b1_pending_state = 1",
            "var:zg361_b1_pending_reservation_state = 1",
            "name = zg361_b1_local_publish_object_state value = 1",
            "name = zg361_b1_local_publish_object_state value = 2",
            "name = zg361_b1_local_publish_grade value = var:zg361_pending_grade",
            "name = zg361_b1_local_publish_revision add = 1",
            "name = zg361_b1_local_publish_receipt",
            "name = zg361_b1_local_publish_published_n add = 1",
            "name = zg361_b1_local_publish_waiting_n add = 1",
            "name = zg361_b1_local_publish_conservation_valid value = 1",
        ):
            self.assertIn(token, refresh)
        self.assertIn(
            "var:zg361_b1_local_publish_expected_n >= {", refresh
        )
        self.assertIn(
            "var:zg361_b1_local_publish_expected_n <= {", refresh
        )
        self.assertNotIn(
            "var:zg361_b1_local_publish_expected_n = {", refresh
        )
        # Local publication is informational: it neither pays nor applies the
        # final grade modifier before the cohort-wide reward seal closes.
        refresh_code = without_comments(refresh)
        self.assertNotIn("add_prestige", refresh_code)
        self.assertNotIn("zg361_apply_grade_effect", refresh_code)
        self.assertNotIn("zg361_apply_pending_grades_effect", refresh_code)

        self.assertIn(
            "name = zg361_b1_local_publish_update_kind value = 1", opened
        )
        self.assertIn(
            "zg361_b1_refresh_individual_publications_effect = yes", opened
        )
        resolve_refresh = resolved.index(
            "zg361_b1_refresh_individual_publications_effect = yes"
        )
        resolve_barrier = resolved.index("var:zg361_b1_pending_open_n = 0")
        self.assertLess(resolve_refresh, resolve_barrier)
        self.assertIn(
            "name = zg361_b1_local_publish_update_kind value = 2", resolved
        )
        self.assertIn(
            "name = zg361_b1_local_publish_update_kind value = 3", reopened
        )
        self.assertGreater(
            reopened.index("zg361_b1_refresh_individual_publications_effect = yes"),
            reopened.index("zg361_b1_rerank_frozen_quota_book_effect = yes"),
        )
        self.assertIn(
            "name = zg361_b1_local_publish_update_kind value = 4", finished
        )
        self.assertLess(
            finished.index("zg361_b1_refresh_individual_publications_effect = yes"),
            finished.index("zg361_apply_pending_grades_effect = yes"),
        )

        self.assertIn("is_ai = no", notice)
        self.assertIn("has_game_rule = zg361_on", notice)
        self.assertIn("this = scope:zg361_b1_local_publish_notice_subject", notice)
        self.assertIn(
            "var:zg361_b1_local_publish_object_owner = scope:zg361_b1_local_publish_notice_owner",
            notice,
        )
        self.assertIn(
            "var:zg361_b1_local_publish_revision = scope:zg361_b1_local_publish_notice_revision",
            notice,
        )
        self.assertIn("zg361b1.126.reopened", notice)
        self.assertIn("zg361b1.126.appended", notice)

    def test_symmetric_reopen_is_pre_reward_single_use_and_reseals(self) -> None:
        gate = top_level_block(
            self.effects, "zg361_b1_prepare_reopen_gate_effect"
        )
        self.assertIn("name = zg361_b1_sealed_board_hash", gate)
        self.assertIn("name = zg361_b1_sealed_board_checksum", gate)
        self.assertIn("name = zg361_b1_reward_snapshot_hash", gate)
        self.assertIn("name = zg361_b1_reward_snapshot_checksum", gate)
        self.assertIn(
            "value = var:zg361_b1_case_serial multiply = 100000 add = var:zg361_b1_quota_book_version",
            gate,
        )
        self.assertIn("name = zg361_b1_pending_reward_expected_n value = 0", gate)
        self.assertIn("name = zg361_b1_pending_reward_expected_n add = 1", gate)
        self.assertIn("trigger_event = { id = zg361b1.122 days = 30 }", gate)
        self.assertIn("zg361_b1_reopen_ticket_reward_hash", gate)
        self.assertIn("zg361_b1_reopen_ticket_book_version", gate)
        self.assertIn("name = zg361_b1_reopen_baseline_score value = zg361_kpi_value", gate)
        self.assertIn("zg361_b1_agenda_order multiply", gate)
        self.assertNotRegex(gate, r"(?m)^\s*max = 1\s*$")
        resolver = top_level_block(
            self.effects, "zg361_b1_resolve_reopen_batch_effect"
        )
        self.assertIn("max = 1", resolver)
        self.assertIn("var:zg361_b1_reopen_pending_n = 0", resolver)

        # The old weighted sum has real assignment collisions.  It remains a
        # display checksum, while stale authorization is now revision-sealed.
        board_a = (3, 1, 2, 2, 2, 2, 3)
        board_b = (2, 3, 1, 2, 2, 2, 3)
        self.assertNotEqual(board_a, board_b)
        self.assertEqual(
            sum((index + 1) * grade for index, grade in enumerate(board_a)),
            sum((index + 1) * grade for index, grade in enumerate(board_b)),
        )
        self.assertNotIn(
            "name = zg361_b1_sealed_board_hash\n\t\t\t\t\tadd =",
            gate,
        )
        event = top_level_block(self.events, "zg361b1.122")
        for token in ("owner", "subject", "cycle", "case", "state", "hash"):
            self.assertIn(f"zg361_b1_reopen_ticket_{token}", event)
        self.assertIn("var:zg361_b1_case_subject = this", event)
        self.assertIn("var:zg361_b1_case_active = 1", event)
        self.assertIn("var:zg361_b1_roster_included = 1", event)
        self.assertIn(
            "var:zg361_pending_grade = var:zg361_b1_reopen_sealed_grade",
            event,
        )
        self.assertIn(
            "var:zg361_b1_quota_book_version = scope:zg361_b1_reopen_ticket_book_version",
            event,
        )
        self.assertIn("var:zg361_b1_reward_snapshot_hash = scope:zg361_b1_reopen_ticket_reward_hash", event)
        self.assertIn("name = zg361_b1_reopen_observed_score value = zg361_kpi_value", event)
        self.assertIn(
            "subtract = var:zg361_b1_reopen_baseline_score",
            event,
        )
        self.assertNotIn("subtract = var:zg361_b1_evidence_late", event)
        self.assertIn("name = zg361_b1_reopen_observation_recorded value = 1", event)
        self.assertIn("stale post-seal batch ticket ignored", event)
        reopen = top_level_block(
            self.effects, "zg361_b1_apply_symmetric_reopen_effect"
        )
        self.assertIn("var:zg361_b1_reopen_count = 0", reopen)
        self.assertIn("var:zg361_b1_rewards_issued = 0", reopen)
        self.assertIn("var:zg361_b1_pending_rewards_committed = 0", reopen)
        self.assertIn("zg361_b1_reopen_late_evidence_magnitude >= 10", reopen)
        self.assertIn("name = zg361_b1_reopen_polarity value = -1", reopen)
        self.assertIn("name = zg361_b1_reopen_polarity value = 1", reopen)
        self.assertIn("name = zg361_b1_reopen_source_board_hash", reopen)
        self.assertIn("name = zg361_b1_reopen_source_book_version", reopen)
        self.assertIn("name = zg361_b1_reopen_new_board_hash", reopen)
        self.assertIn("name = zg361_b1_reopen_new_book_version", reopen)
        self.assertIn("name = zg361_b1_reopen_receipt_subject", reopen)
        self.assertIn("name = zg361_b1_reopen_subject_old_grade", reopen)
        self.assertIn("name = zg361_b1_reopen_subject_new_grade", reopen)
        self.assertIn("name = zg361_b1_reopen_subject_calibration_before", reopen)
        self.assertIn("name = zg361_b1_reopen_subject_calibration_after", reopen)
        rerank = top_level_block(
            self.effects, "zg361_b1_rerank_frozen_quota_book_effect"
        )
        self.assertIn("name = zg361_b1_quota_snapshot value = var:zg361_pending_grade", rerank)
        self.assertIn("name = zg361_b1_shadow_to_quota_delta", rerank)
        self.assertIn("name = zg361_b1_forced_down value = 1", rerank)
        self.assertIn(
            "change_variable = { name = zg361_b1_quota_book_version add = 1 }",
            rerank,
        )
        self.assertIn("zg361_b1_agenda_order multiply", reopen)
        self.assertNotIn("reopen_source_board_hash add = var:zg361_b1_reopen_polarity", reopen)
        self.assertIn("name = zg361_b1_closure_state value = 3", reopen)
        finish = top_level_block(self.effects, "zg361_b1_finish_calibration_effect")
        self.assertIn("name = zg361_b1_finalization_board_hash", finish)
        self.assertIn("name = zg361_b1_finalization_reward_hash", finish)
        self.assertIn("name = zg361_b1_pending_rewards_committed value = 1", finish)
        self.assertIn(
            "var:zg361_b1_pending_rewards_paid_n = var:zg361_b1_pending_reward_expected_n",
            finish,
        )
        self.assertIn("publication withheld", finish)
        pay = top_level_block(
            self.effects, "zg361_b1_pay_frozen_pending_rewards_effect"
        )
        self.assertIn("var:zg361_b1_finalization_board_hash = var:zg361_b1_sealed_board_hash", pay)
        self.assertIn("var:zg361_b1_finalization_reward_hash = var:zg361_b1_reward_snapshot_hash", pay)
        self.assertIn("add_prestige = 25", pay)
        self.assertNotIn("name = zg361_b1_pending_rewards_paid_n value = 0", pay)
        publish = top_level_block(self.effects, "zg361_b1_mark_published_effect")
        self.assertIn("name = zg361_b1_rewards_issued value = 1", publish)
        self.assertIn("name = zg361_b1_closure_state value = 4", publish)

    def test_management_authority_is_duke_plus_while_subject_self_is_rank_neutral(self) -> None:
        open_cycle = top_level_block(self.effects, "zg361_b1_open_cycle_effect")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", open_cycle)
        celestial = top_level_block(
            self.triggers, "zg361_is_celestial_liege_trigger"
        )
        self.assertIn("highest_held_title_tier >= tier_duchy", celestial)
        self.assertIn("is_landed = yes", celestial)
        self.assertIn("is_alive = yes", celestial)
        reviewable = top_level_block(
            self.triggers, "zg361_is_reviewable_vassal_trigger"
        )
        self.assertIn("liege = { zg361_is_celestial_liege_trigger = yes }", reviewable)
        self.assertNotIn("tier_duchy", reviewable)
        self.assertNotIn("highest_held_title_tier", reviewable)
        self.assertIn(
            "zg361_case_kernel_subject_self_guard_trigger",
            self.case_kernel_triggers,
        )
        for event_id in (200, 201):
            visible = top_level_block(self.events, f"zg361b1.{event_id}")
            self.assertNotIn("tier_duchy", visible)
            self.assertNotIn("zg361_is_celestial_liege_trigger", visible)

    def test_every_generated_top_level_block_is_brace_balanced(self) -> None:
        for source in (self.effects, self.events):
            code = without_comments(source)
            self.assertEqual(code.count("{"), code.count("}"))
            keys = re.findall(r"(?m)^([A-Za-z0-9_.]+)\s*=\s*\{", source)
            for key in keys:
                with self.subTest(key=key):
                    block = top_level_block(source, key)
                    self.assertTrue(block.endswith("}"))

    def test_existing_settlement_opens_shadow_and_marks_publication(self) -> None:
        self.assertIn("zg361_b1_open_shadow_effect = yes", self.core)
        self.assertIn("zg361_b1_mark_published_effect = yes", self.core)
        self.assertLess(
            self.core.index("zg361_publish_scoreboard_effect = yes"),
            self.core.index("zg361_b1_mark_published_effect = yes"),
        )

    def test_readiness_is_not_inflated_by_foundation(self) -> None:
        manifest = json.loads(read("docs/361-mechanism-manifest.json"))
        by_id = {int(item["id"]): item for item in manifest["items"]}
        self.assertEqual(set(B1_IDS) - set(by_id), set())
        self.assertEqual(
            {by_id[item_id]["status"]["domain_runtime"] for item_id in B1_IDS},
            {"partial"},
        )


if __name__ == "__main__":
    unittest.main()
