#!/usr/bin/env python3
"""No-launch static contract for the cross-cycle production choreography."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from zhongguo_phase2_event_choreography import (  # noqa: E402
    PHASE2_EVENT_SEQUENCE_PLANS,
)
from zhongguo_phase2_source_checkpoint_provider import (  # noqa: E402
    CHECKPOINT_REQUIRED_HANDLERS,
)


MOD = ROOT / "mod_zhongguo_style"
EFFECTS = MOD / "common" / "scripted_effects"
EVENTS = MOD / "events"
DOC = (
    ROOT
    / "docs"
    / "phase2-promo"
    / "cross-cycle-endgame-production-choreography-2026-09-04.md"
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


class CrossCycleEndgameProductionChoreographyTests(unittest.TestCase):
    def test_exact_seed_is_subject_facing_restart_base_not_source(self) -> None:
        seed = json.loads(
            (TOOLS / "zg361_phase2_seed_contract.json").read_text(
                encoding="utf-8-sig"
            )
        )
        self.assertEqual(seed["runtime"]["game_version"], "1.19.0.6")
        self.assertEqual(
            seed["runtime"]["executable_sha256"].upper(),
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        )
        self.assertEqual(seed["saved_state"]["played_character_id"], 29037)
        self.assertEqual(
            seed["domain_query_matrix"]["workforce_owner_character_id"], 32904
        )
        self.assertNotEqual(
            seed["saved_state"]["played_character_id"],
            seed["domain_query_matrix"]["workforce_owner_character_id"],
        )
        self.assertIn("zga_phase2_seed.1", seed["provenance"]["real_character_proof"])

    def test_prefix_contract_is_not_a_chronological_order(self) -> None:
        expected_handlers = (
            "capture_promotion_compensation",
            "capture_projects_metrics",
            "capture_incidents_operations",
        )
        self.assertEqual(CHECKPOINT_REQUIRED_HANDLERS[:3], expected_handlers)
        plans = {plan.handler: plan for plan in PHASE2_EVENT_SEQUENCE_PLANS}
        self.assertEqual(
            [plans[handler].source_event for handler in expected_handlers],
            ["zg361pp.147", "zg361cp.26", "zg361.50"],
        )

        pump = _text(EFFECTS / "zg361_phase2_central_010_serial_pump_effects.txt")
        stage_3 = pump.index("var:zg361_p2c_stage = 3")
        stage_4 = pump.index("var:zg361_p2c_stage = 4")
        stage_8 = pump.index("var:zg361_p2c_stage = 8")
        stage_11 = pump.index("var:zg361_p2c_stage = 11")
        self.assertLess(stage_3, stage_4)
        self.assertLess(stage_4, stage_8)
        self.assertLess(stage_8, stage_11)

    def test_b1_publication_freezes_real_central_tuple(self) -> None:
        lifecycle = _text(
            EFFECTS / "zg361_phase2_central_004_lifecycle_hooks_effects.txt"
        )
        for token in (
            "var:zg361_b1_cycle_state = 8",
            "var:zg361_b1_closure_state = 4",
            "set_variable = { name = zg361_p2c_b1_owner value = this }",
            "set_variable = { name = zg361_p2c_cycle value = var:zg361_review_serial }",
            "set_variable = { name = zg361_p2c_subject value = scope:zg361_p2c_selected_subject }",
            "set_variable = { name = zg361_p2c_stage value = 1 }",
            "zg361_p2c_schedule_pump_effect = { DAYS = 2 }",
        ):
            self.assertIn(token, lifecycle)

    def test_m355_is_the_zero_day_owner_facing_predecessor_of_m356(self) -> None:
        m355 = _text(
            EVENTS / "zg361_workforce_endgame_event_009_m355_target_ratchet_events.txt"
        )
        m356 = _text(
            EVENTS / "zg361_workforce_endgame_event_010_m356_outcome_timing_events.txt"
        )
        self.assertIn("zg361we.355 = {", m355)
        self.assertIn("is_ai = no", m355)
        self.assertIn("this = scope:zg361_we_al_owner", m355)
        self.assertIn("EXPECTED_STATE = 1", m355)
        self.assertEqual(m355.count("trigger_event = { id = zg361we.356 }"), 3)
        self.assertNotIn("trigger_event = { id = zg361we.356 days", m355)
        self.assertIn("zg361we.356 = {", m356)
        self.assertIn("this = scope:zg361_we_al_owner", m356)
        self.assertIn("EXPECTED_STATE = 1", m356)

    def test_m356_route_a_waits_for_three_real_external_receipts(self) -> None:
        m356_effects = _text(
            EFFECTS / "zg361_workforce_endgame_056_al_m355_m356_effects.txt"
        )
        handoff = _text(EFFECTS / "zg361_b2_collective_receipt_handoff_effects.txt")
        bridge = _text(
            EFFECTS / "zg361_workforce_endgame_002_al_receipt_bridge_effects.txt"
        )
        for token in (
            "zg361_case_al_advance_01_effect",
            "set_variable = { name = zg361_we_awaiting_al_357_359 value = 1 }",
            "set_variable = { name = zg361_we_portfolio_status value = 5 }",
        ):
            self.assertIn(token, m356_effects)
        for token in (
            "var:zg361_b1_m357_external_receipt_state = 8",
            "var:zg361_b2_m358_external_receipt_state = 3",
            "var:zg361_b2_m358_external_receipt_route != 3",
            "var:zg361_b2_m359_external_receipt_route != 3",
            "zg361_we_submit_al_357_359_receipts_effect",
        ):
            self.assertIn(token, handoff)
        for token in (
            "zg361_case_al_advance_02_effect",
            "zg361_case_al_advance_03_effect",
            "set_variable = { name = zg361_we_al_external_receipt_count value = 3 }",
            "set_variable = { name = zg361_we_al_external_last_operation value = 359 }",
        ):
            self.assertIn(token, bridge)

    def test_stage11_requires_real_handoff_and_three_manager_source(self) -> None:
        stage11 = _text(
            EFFECTS / "zg361_phase2_central_009_stage11_workforce_endgame_effects.txt"
        )
        m360 = _text(
            EVENTS / "zg361_workforce_endgame_event_011a_al_m360_collective_events.txt"
        )
        for token in (
            "zg361_b2_submit_completed_al_receipts_effect",
            "zg361_p2c_prepare_m360_source_effect",
            "zg361_we_resume_m360_from_central_source_effect",
            "zg361_p2c_schedule_pump_effect = { DAYS = 2 }",
        ):
            self.assertIn(token, stage11)
        for token in (
            "var:zg361_p2c_m360_source_cohort_count = 3",
            "var:zg361_p2c_m360_source_total_quota >= 1",
            "var:zg361_p2c_m360_source_total_quota <= 6",
            "NOT = { var:zg361_p2c_m360_source_c1_manager = var:zg361_p2c_m360_source_c2_manager }",
            "EXPECTED_STATE = 4",
        ):
            self.assertIn(token, m360)

    def test_route_c_and_m361_require_third_cycle_history(self) -> None:
        m360_event = _text(
            EVENTS / "zg361_workforce_endgame_event_011a_al_m360_collective_events.txt"
        )
        route_c = _text(
            EFFECTS / "zg361_workforce_endgame_060_al_m360_route_c_effects.txt"
        )
        history = _text(
            EFFECTS / "zg361_workforce_endgame_007_m361_charter_history_gate_effects.txt"
        )
        m361_event = _text(
            EVENTS / "zg361_workforce_endgame_event_011b_al_m361_charter_events.txt"
        )
        self.assertIn("name = zg361we.360.c", m360_event)
        self.assertIn("zg361_we_m360_route_c_effect", m360_event)
        self.assertIn("trigger_event = { id = zg361we.361 }", m360_event)
        self.assertIn(
            "set_variable = { name = zg361_we_m360_debt_due_cycle value = { value = $TICKET_CYCLE$ add = 1 } }",
            route_c,
        )
        self.assertIn("zg361_case_al_advance_04_effect", route_c)
        for token in (
            "var:zg361_we_completed_cycle_ledger_count = 3",
            "var:zg361_we_completed_cycle_ledger_cycle_1 < var:zg361_we_completed_cycle_ledger_cycle_2",
            "var:zg361_we_completed_cycle_ledger_cycle_2 < var:zg361_we_completed_cycle_ledger_cycle_3",
            "var:zg361_we_completed_cycle_ledger_cycle_3 = $TICKET_CYCLE$",
            "set_variable = { name = zg361_we_m361_evidence_ready value = 1 }",
        ):
            self.assertIn(token, history)
        for token in (
            "zg361we.361 = {",
            "this = scope:zg361_we_al_owner",
            "var:zg361_we_m361_evidence_count = 3",
            "var:zg361_we_m361_evidence_consumed = 0",
            "EXPECTED_STATE = 5",
        ):
            self.assertIn(token, m361_event)

    def test_capture_is_save_only_and_subject_proof_is_not_production_closed(self) -> None:
        capture = _text(TOOLS / "zg361_phase2_cross_cycle_endgame_source_capture.py")
        seam = _text(TOOLS / "zg361_phase2_cross_cycle_endgame_live_seam.py")
        self.assertIn("def save_checkpoint(", capture)
        self.assertNotIn("def select_event_option(", capture)
        self.assertNotIn("def execute_step(", capture)
        self.assertIn("DEFAULT_PROGRESS_MAX_DAYS: Final = 730", seam)
        self.assertIn(
            'TRANSITION_FIXTURE_ID: Final = "zg361_phase2_cross_cycle_endgame_rebind"',
            seam,
        )
        self.assertIn('receipt.get("typed_event_fixture_used") is True', seam)
        self.assertIn('receipt.get("business_state_fixture_used") is False', seam)

    def test_document_keeps_readiness_and_ack_boundary_explicit(self) -> None:
        document = _text(DOC)
        for token in (
            "static-ready-live-pending",
            "最短的合格候选是 owner-facing 的 `zg361cp.26`",
            "仅有 registry receipt 不能证明这些条件",
            "第一或第二 cycle 的 `#356`",
            "ACK 只说明输入已提交",
            "played-subject",
            "acceptance-only typed event fixture",
            "readiness 保持 `live-pending`",
        ):
            self.assertIn(token, document)


if __name__ == "__main__":
    unittest.main()
