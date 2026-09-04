#!/usr/bin/env python3
"""Static contract for the product-only path to the real zg361.50 source."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
MOD = ROOT / "mod_zhongguo_style"
CONTRACT = json.loads(
    (TOOLS / "zg361_phase2_incident_source_choreography_contract.json").read_text(
        encoding="utf-8-sig"
    )
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def top_level_block(source: str, key: str) -> str:
    marker = f"{key} = {{"
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing top-level block {key}")
    opening = source.find("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated top-level block {key}")


class IncidentSourceProductionChoreographyTests(unittest.TestCase):
    def test_frozen_seed_and_real_provider_start_are_exact(self) -> None:
        seed = json.loads(
            (TOOLS / "zg361_phase2_seed_contract.json").read_text(
                encoding="utf-8-sig"
            )
        )
        expected = CONTRACT["canonical_seed"]
        self.assertEqual(seed["status"], expected["status"])
        self.assertEqual(seed["source"]["bytes"], expected["bytes"])
        self.assertEqual(seed["source"]["sha256"], expected["sha256"])
        self.assertEqual(seed["saved_state"]["date_raw"], expected["date_raw"])
        self.assertEqual(
            seed["saved_state"]["played_character_id"],
            expected["played_character_id"],
        )
        self.assertEqual(
            seed["domain_query_matrix"]["incident_owner_character_id"],
            expected["incident_owner_character_id"],
        )
        observed = CONTRACT["retained_live_provider_evidence"]["b1_case"]
        self.assertEqual(observed["owner_character_id"], 32904)
        self.assertEqual(observed["subject_character_id"], 29037)
        self.assertEqual(observed["cycle_serial"], 1)
        self.assertEqual(observed["case_serial"], 1)
        self.assertEqual(observed["state"], 1)
        self.assertTrue(observed["active"])
        self.assertEqual(observed["stage_key"], "targets_open")
        self.assertEqual(observed["receipt_key"], "roster_lock")

    def test_generated_b1_timeline_reaches_real_settlement(self) -> None:
        effects_1 = text(
            MOD / "common" / "scripted_effects" / "zg361_b1_runtime_effects.txt"
        )
        effects_2 = text(
            MOD
            / "common"
            / "scripted_effects"
            / "zg361_b1_runtime_effects_part2.txt"
        )
        events = text(MOD / "events" / "zg361_b1_runtime_events.txt")
        generator = text(MOD / "tools" / "gen_361_b1_runtime.py")

        opened = top_level_block(effects_1, "zg361_b1_open_cycle_effect")
        self.assertIn("trigger_event = { id = zg361b1.100 days = 180 }", opened)
        event_100 = top_level_block(events, "zg361b1.100")
        event_101 = top_level_block(events, "zg361b1.101")
        event_102 = top_level_block(events, "zg361b1.102")
        event_103 = top_level_block(events, "zg361b1.103")
        self.assertIn("trigger_event = { id = zg361b1.101 days = 60 }", event_100)
        self.assertIn("trigger_event = { id = zg361b1.102 days = 60 }", event_101)
        self.assertIn("zg361_run_review_effect = yes", event_102)
        self.assertIn("zg361_b1_submit_quota_book_effect = yes", event_103)
        shadow = top_level_block(effects_1, "zg361_b1_open_shadow_effect")
        self.assertIn("trigger_event = { id = zg361b1.103 days = 30 }", shadow)

        for token in (
            "trigger_event = { id = zg361b1.110 days = 335 }",
            "trigger_event = { id = zg361b1.110 days = 1 }",
            "trigger_event = { id = zg361b1.111 days = 1 }",
        ):
            self.assertIn(token, effects_1)
            self.assertIn(token, generator)
        for token in (
            "DAYS = 30\n\t\t\t\t\tEVENT = zg361b1.121",
            "trigger_event = { id = zg361b1.125 days = 31 }",
            "trigger_event = { id = zg361b1.123 days = 1 }",
            "trigger_event = { id = zg361b1.122 days = 30 }",
            "trigger_event = { id = zg361b1.124 days = 1 }",
            "trigger_event = { id = zg361b1.126 days = 1 }",
        ):
            self.assertIn(token, effects_2)
            self.assertIn(token, generator)
        finish = top_level_block(effects_2, "zg361_b1_finish_calibration_effect")
        self.assertIn("zg361_apply_pending_grades_effect = yes", finish)

    def test_only_exact_authored_player_cards_are_allowlisted(self) -> None:
        events = text(MOD / "events" / "zg361_b1_runtime_events.txt")
        allowed = {
            row["event_definition_key"]: row["option_number"]
            for row in CONTRACT["allowed_player_choreography"]
        }
        self.assertEqual(
            allowed,
            {"zg361b1.200": 3, "zg361b1.201": 1, "zg361b1.126": 1},
        )
        event_200 = top_level_block(events, "zg361b1.200")
        event_201 = top_level_block(events, "zg361b1.201")
        event_126 = top_level_block(events, "zg361b1.126")
        self.assertEqual(event_200.count("option = {"), 3)
        self.assertIn("name = zg361b1.200.c", event_200)
        self.assertIn("zg361_b1_submit_self_conservative_ticket_effect = yes", event_200)
        self.assertEqual(event_201.count("option = {"), 2)
        self.assertIn("name = zg361b1.201.a", event_201)
        self.assertIn("zg361_b1_submit_shadow_accept_ticket_effect = yes", event_201)
        self.assertEqual(event_126.count("option = {"), 1)
        self.assertIn("name = zg361b1.126.a", event_126)

    def test_real_grade_325_delivery_preserves_received_self_identity(self) -> None:
        effects = text(MOD / "common" / "scripted_effects" / "zg361_effects.txt")
        events = text(MOD / "events" / "zg361_events.txt")
        apply_grade = top_level_block(effects, "zg361_apply_grade_effect")
        grade_325 = top_level_block(effects, "zg361_grade_325_apply_effect")
        notice = top_level_block(events, "zg361.50")

        self.assertIn("var:zg361_pending_grade = 1", apply_grade)
        self.assertIn("zg361_grade_325_apply_effect = yes", apply_grade)
        self.assertIn(
            "var:zg361_result_case_owner = { save_scope_as = zg361_notice_prompt_owner }",
            grade_325,
        )
        self.assertIn("save_scope_as = zg361_notice_prompt_subject", grade_325)
        self.assertIn("trigger_event = { id = zg361.50 days = 1 }", grade_325)
        for token in (
            "is_ai = no",
            "this = scope:zg361_notice_prompt_subject",
            "var:zg361_result_case_owner = scope:zg361_notice_prompt_owner",
            "var:zg361_result_case_state = 1",
            "var:zg361_result_grade = 1",
            "name = zg361.50.a",
        ):
            self.assertIn(token, notice)

    def test_reachability_and_no_fabricated_fix_are_explicit(self) -> None:
        reachability = CONTRACT["reachability"]
        self.assertTrue(reachability["production_graph_to_grade_settlement_intact"])
        self.assertFalse(reachability["played_character_grade_325_observed"])
        self.assertFalse(reachability["played_character_grade_325_guaranteed"])
        self.assertEqual(
            reachability["status"],
            "conditional-product-reachable-live-candidate-unproven",
        )
        self.assertFalse(reachability["product_defect_proven"])
        self.assertFalse(CONTRACT["production_fix"]["implemented"])
        self.assertEqual(
            CONTRACT["production_effect_change"]["files_added_or_modified"], []
        )
        self.assertFalse(CONTRACT["no_launch"]["ck3_started"])
        self.assertFalse(CONTRACT["no_launch"]["shared_runner_modified"])
        self.assertFalse(CONTRACT["no_launch"]["b3_artifact_modified"])
        self.assertTrue(CONTRACT["strict_target_capture"]["must_remain_unselected"])
        forbidden = " ".join(CONTRACT["forbidden"])
        for token in ("fixture", "console", "rebind", "ACK", "synthetic"):
            self.assertIn(token, forbidden)


if __name__ == "__main__":
    unittest.main()
