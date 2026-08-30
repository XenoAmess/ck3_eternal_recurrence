#!/usr/bin/env python3
"""L0 contracts for the B1 cross-cycle performance-season foundation.

These tests prove wiring and deterministic source/model contracts only. They
must not upgrade any mechanism to fixture-live without one MCP-first CK3 run.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from gen_361_b1_runtime import MOD_ROOT, outputs
from zg361_b1_runtime_data import B1_BINDINGS, B1_IDS, STAGE_SEQUENCE


def read(relative: str) -> str:
    return (MOD_ROOT / relative).read_text(encoding="utf-8-sig")


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
        # Four manager stage tickets, one common-superior close ticket and one
        # manager-root reset ticket each expose an explicit stale no-op.
        self.assertEqual(self.events.count("stale "), 6)
        self.assertIn("id = zg361b1.100 days = 180", self.effects)
        self.assertIn("id = zg361b1.101 days = 60", self.events)
        self.assertIn("id = zg361b1.102 days = 60", self.events)
        self.assertIn("id = zg361b1.103 days = 30", self.effects)

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
        for slot in (1, 2, 3):
            self.assertIn(f"zg361_b1_peer_slot_{slot}_evaluator", self.effects)
            self.assertIn(f"zg361_b1_peer_slot_{slot}_raw", self.effects)
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
        bank_event = self.events.split("zg361b1.110 = {", 1)[1]
        for token in (
            "zg361_b1_bank_ticket_owner",
            "zg361_b1_bank_ticket_season",
            "zg361_b1_bank_ticket_case",
            "zg361_b1_bank_ticket_state",
        ):
            self.assertIn(token, bank_event)
        self.assertIn("has_variable_list = zg361_b1_ready_managers", bank_event)
        self.assertIn("closed with no ready managers", bank_event)
        manager_event = self.events.split("zg361b1.111 = {", 1)[1]
        self.assertIn("this = scope:zg361_b1_ticket_owner", manager_event)
        self.assertIn("var:zg361_b1_cycle_state = 6", manager_event)
        self.assertIn("zg361_b1_open_calibration_effect = yes", manager_event)

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
