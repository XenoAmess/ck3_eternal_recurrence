#!/usr/bin/env python3
"""AF5 action evidence must come from independent state after the real driver."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from test_zg361_phase2_af5_timeline import ScheduledCompensationService, production
from zg361_phase2_af5_action_cell import (
    Af5ActionCellError, QUERY_CAPABILITY, run_af5_terminal_action_cell,
)

ROOT = Path(__file__).resolve().parents[1]
FRAMES = json.loads((ROOT / "ck3_autonomous_player/tests/fixtures/zhongguo_compensation_af5_snapshot_v1.json").read_text(encoding="utf-8"))["frames"]


class ObservedAf5Service(ScheduledCompensationService):
    def __init__(self, *, close_case: bool = True, wrong_case: bool = False) -> None:
        super().__init__()
        self.close_case = close_case
        self.wrong_case = wrong_case
        self.af5_selected = False
        self.provider_queries = []

    def capabilities(self):
        return {"bridge_capabilities": [QUERY_CAPABILITY]}

    def query_current_event_window_context_v1(self, *args, **kwargs):
        result = super().query_current_event_window_context_v1(*args, **kwargs)
        result["current_event_window_context"]["readiness"] = {
            key: True for key in ("event_definition_identity_ready", "root_scope_ready",
                                 "saved_scopes_ready", "option_presentation_ready")
        }
        return result

    def query_zhongguo_compensation_af5_snapshot_v1(self, nonce, *, expected_revision):
        self._require_revision(expected_revision)
        self.provider_queries.append(nonce)
        name = ("immediate_terminal_domain4" if self.af5_selected and self.close_case
                else "pre_action")
        result = copy.deepcopy(FRAMES[name])
        result.update(source_backend_id="native-headless", player_character_id=32904,
                      request_nonce=nonce, snapshot_revision=self.revision, date_raw=self.date_raw)
        for group in ("case", "m299", "m300"):
            result["af5"][group]["identity"]["owner_character_id"]["value"] = 32904
        result["af5"]["portfolio"]["result_identity"]["owner_character_id"]["value"] = 32904
        if self.af5_selected and self.wrong_case:
            result["af5"]["case"]["identity"]["case_serial"]["value"] += 1
        return result

    def select_event_option(self, option_number, *, event_instance_id, expected_revision):
        if option_number != 42:
            return super().select_event_option(option_number,
                event_instance_id=event_instance_id, expected_revision=expected_revision)
        self._require_revision(expected_revision)
        if self.active_instance != 85:
            raise AssertionError("AF5 selection requires the delivered AF5 event")
        self.actions.append("select-event-option-42")
        self.active_instance = None
        self.revision += 1
        self.af5_selected = True
        return {"accepted": True, "status": "submitted"}


def drive(service):
    return production.enter_promotion_source_checkpoint_v1(
        service, pause_on_event_definition_key="zg361comp.1",
        pause_on_event_option_number=42, timeout_seconds=2,
        clock=lambda: service.elapsed, sleeper=service.sleep,
    )


class Af5ActionTests(unittest.TestCase):
    def run_cell(self, service):
        return run_af5_terminal_action_cell(
            service, advance_to_af5=drive, request_nonce="af5.test",
            terminal_timeout_seconds=0.2, clock=lambda: service.elapsed,
            sleeper=service.sleep,
        )

    def test_real_driver_then_exact_selection_then_independent_terminal(self):
        service = ObservedAf5Service()
        result = self.run_cell(service)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(service.actions, ["select-event-option-37", "resume-map", "select-event-option-42"])
        self.assertEqual(service.running_days, 1)
        self.assertTrue(result["terminal_postcondition_verified"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertEqual(result["selected_native_option_index"], 41)
        self.assertEqual(service.provider_queries, ["af5.test.before", "af5.test.after"])

    def test_ack_without_closed_case_keeps_red_and_selection_evidence(self):
        service = ObservedAf5Service(close_case=False)
        with self.assertRaises(Af5ActionCellError) as captured:
            self.run_cell(service)
        evidence = captured.exception.evidence
        self.assertEqual(evidence["failure_stage"], "af5_terminal_observation")
        self.assertEqual(evidence["selected_option_number"], 42)
        self.assertTrue(evidence["selection"]["accepted"])
        self.assertTrue(evidence["provider_observed"])
        self.assertFalse(evidence["terminal_postcondition_verified"])
        self.assertEqual(evidence["advance"]["result"], "GREEN")
        self.assertTrue(service.paused)

    def test_other_case_terminal_cannot_complete_the_selected_case(self):
        with self.assertRaises(Af5ActionCellError) as captured:
            self.run_cell(ObservedAf5Service(wrong_case=True))
        self.assertIn("changed the case identity", captured.exception.evidence["error"])


if __name__ == "__main__":
    unittest.main()
