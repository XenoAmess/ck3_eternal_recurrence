#!/usr/bin/env python3
"""Offline source contract for the HC-workforce Route-B reachability audit."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_zhongguo_acceptance.py"
SEED = ROOT / "tools" / "zg361_phase2_seed_contract.json"
FIXTURE_GUI = (
    ROOT
    / "tools"
    / "fixtures"
    / "zg361_phase2_workforce_action"
    / "common"
    / "scripted_guis"
    / "zga_phase2_workforce_guis.txt"
)
STAGE_11 = (
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_phase2_central_009_stage11_workforce_endgame_effects.txt"
)
RESUME_EVENT = (
    ROOT
    / "mod_zhongguo_style"
    / "events"
    / "zg361_phase2_central_003_m360_resume_events.txt"
)
RESUME = (
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_workforce_endgame_005_m360_central_source_effects.txt"
)
B1_EFFECTS = (
    ROOT
    / "mod_zhongguo_style"
    / "common"
    / "scripted_effects"
    / "zg361_b1_runtime_effects.txt"
)
B1_EVENTS = ROOT / "mod_zhongguo_style" / "events" / "zg361_b1_runtime_events.txt"
CHECKPOINT = ROOT / "tools" / "zg361_phase2_hc_workforce_route_b_checkpoint.py"
WORKFORCE_ACTION = ROOT / "tools" / "zhongguo_phase2_workforce_action.py"
AUDIT = (
    ROOT
    / "docs"
    / "phase2-promo"
    / "zg361-hc-workforce-route-b-production-choreography-audit-2026-09-04.md"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def function_block(source: str, name: str) -> str:
    start = source.index(f"def {name}(")
    next_definition = source.find("\ndef ", start + 1)
    return source[start:] if next_definition < 0 else source[start:next_definition]


def ordered(source: str, tokens: tuple[str, ...]) -> bool:
    positions = [source.find(token) for token in tokens]
    return all(position >= 0 for position in positions) and positions == sorted(
        positions
    )


class RouteBProductionChoreographyAuditTests(unittest.TestCase):
    def test_registered_seed_is_selector_seed_not_workforce_checkpoint(self) -> None:
        seed = json.loads(SEED.read_text(encoding="utf-8-sig"))
        self.assertEqual(seed["status"], "ready")
        self.assertEqual(seed["source"]["bytes"], 57_377_787)
        self.assertEqual(
            seed["source"]["sha256"],
            "8e6ceb97e97cd6b9185ebbcce38b42fc087e0b800cd5e321037c9f29a79e45b9",
        )
        self.assertEqual(seed["saved_state"]["date_raw"], 53_147_016)
        self.assertEqual(seed["saved_state"]["played_character_id"], 29_037)
        self.assertEqual(
            seed["domain_query_matrix"]["workforce_owner_character_id"], 32_904
        )
        limitations = " ".join(seed["provenance"]["limitations"])
        self.assertIn("do not prove the four domain providers ready", limitations)
        self.assertIn("not yet wholly ready", limitations)

    def test_capture_producer_waits_without_timeline_progress(self) -> None:
        runner = read(RUNNER)
        capture = function_block(
            runner, "run_phase2_hc_workforce_route_b_checkpoint_capture_scenario"
        )
        wait = function_block(runner, "wait_for_phase2_exact_event")
        self.assertTrue(
            ordered(
                capture,
                (
                    "install_phase2_workforce_action_fixture(",
                    "_save_phase2_workforce_checkpoint(",
                    "_restore_phase2_workforce_checkpoint(",
                    "wait_for_phase2_exact_event(",
                    "select_typed_fixture_player_transition(",
                    "expected_definition_key=M360_EVENT_DEFINITION_KEY",
                    "freeze_route_b_pre_action_checkpoint(",
                ),
            )
        )
        self.assertIn("without timeline input", wait)
        for forbidden in ("resume_map", "set_speed", "execute_step("):
            self.assertNotIn(forbidden, wait)
            self.assertNotIn(forbidden, capture)

    def test_fixture_requires_a_ready_ai_owned_source(self) -> None:
        fixture = read(FIXTURE_GUI)
        for token in (
            "var:zg361_case_al_state = 4",
            "var:zg361_case_al_active = 1",
            "var:zg361_we_al_external_stage_receipts_verified = 1",
            "NOT = { has_variable = zg361_we_m360_event_queued }",
            "is_ai = yes",
            "var:zg361_p2c_m360_source_status = 1",
            "var:zg361_p2c_m360_source_subject = root",
            "var:zg361_p2c_m360_resume_pending = 1",
            "var:zg361_p2c_m360_resume_subject = root",
            "trigger_event = zga_phase2_workforce.1",
        ):
            self.assertIn(token, fixture)

    def test_central_prepares_then_arms_a_durable_d1_resume_boundary(self) -> None:
        stage = read(STAGE_11)
        awaiting_branch = stage[
            stage.index("zg361_b2_submit_completed_al_receipts_effect = {") :
        ]
        self.assertTrue(
            ordered(
                awaiting_branch,
                (
                    "zg361_b2_submit_completed_al_receipts_effect = {",
                    "zg361_p2c_prepare_m360_source_effect = yes",
                    "limit = { var:zg361_p2c_m360_source_status = 1 }",
                    "zg361_p2c_schedule_m360_resume_effect = yes",
                ),
            )
        )
        self.assertNotIn(
            "zg361_we_resume_m360_from_central_source_effect", stage
        )
        resume_event = read(RESUME_EVENT)
        self.assertIn("zg361p2c.7 = {", resume_event)
        self.assertIn("id = zg361p2c.7 days = 1", read(STAGE_11))
        self.assertIn(
            "scope:zg361_p2c_m360_resume_ticket_subject = {",
            resume_event,
        )
        self.assertIn(
            "zg361_we_resume_m360_from_central_source_effect = {",
            resume_event,
        )
        self.assertIn("EXPECTED_CHOICE = 2", resume_event)

    def test_resume_routes_ai_before_it_can_queue_the_player_event(self) -> None:
        resume = read(RESUME)
        resume = resume[resume.index("zg361_we_resume_m360_from_central_source_effect = {") :]
        self.assertTrue(
            ordered(
                resume,
                (
                    "$TICKET_OWNER$ = { is_ai = yes }",
                    "zg361_we_materialize_m360_route_a_from_central_effect",
                    "set_variable = { name = zg361_we_m360_event_queued value = 1 }",
                    "$TICKET_OWNER$ = { trigger_event = { id = zg361we.360 } }",
                ),
            )
        )

    def test_b1_fixed_time_anchors_are_preserved(self) -> None:
        effects = read(B1_EFFECTS)
        events = read(B1_EVENTS)
        self.assertIn("trigger_event = { id = zg361b1.100 days = 180 }", effects)
        self.assertIn("trigger_event = { id = zg361b1.101 days = 60 }", events)
        self.assertIn("trigger_event = { id = zg361b1.102 days = 60 }", events)
        self.assertIn("trigger_event = { id = zg361b1.200 days = 1 }", effects)
        self.assertIn("trigger_event = { id = zg361b1.201 days = 1 }", effects)
        self.assertIn("trigger_event = { id = zg361b1.103 days = 30 }", effects)
        self.assertIn("trigger_event = { id = zg361b1.110 days = 1 }", effects)
        self.assertIn("trigger_event = { id = zg361b1.111 days = 1 }", effects)

    def test_b4_seal_requires_eight_current_cycle_facts_not_m361_maturity(self) -> None:
        checkpoint = read(CHECKPOINT)
        start = checkpoint.index("WORKFORCE_REQUIRED_FACTS: Final = (")
        end = checkpoint.index("\n)", start)
        facts = [
            line.strip().strip(",").strip('"')
            for line in checkpoint[start:end].splitlines()[1:]
            if line.strip().startswith('"')
        ]
        self.assertEqual(len(facts), 8)
        action = read(WORKFORCE_ACTION)
        for token in (
            'history.get("status") == "three_cycle"',
            'history.get("effective_count") == 3',
            "slot_cycles[0] < slot_cycles[1] < slot_cycles[2] == cycle",
            'charter.get("status") == "ready"',
            '("evidence_count", 3)',
            '("effective_cycle_serial", cycle + 1)',
            "require_m361_charter: bool = True",
            "if not require_m361_charter:",
        ):
            self.assertIn(token, action)
        self.assertIn("require_m361_charter=False", checkpoint)
        self.assertIn('"provider_seal_scope": "m360_current_cycle_route_b"', checkpoint)

    def test_audit_keeps_the_live_boundary_explicit(self) -> None:
        audit = read(AUDIT)
        for token in (
            "reachability blocker resolved offline",
            "workforce_collective_ready=false",
            "typed WAIT `360411`",
            "ACK must retain",
            "8 current-cycle fact groups",
            "Remaining unknowns",
            "static-ready-live-pending",
        ):
            self.assertIn(token, audit)


if __name__ == "__main__":
    unittest.main()
