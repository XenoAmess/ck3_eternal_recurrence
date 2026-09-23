from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.combat_phase_event_trace_contract import (
    QUERY_COMBAT_PHASE_EVENT_TRACE_V1_CAPABILITY,
    _STOCK_KEYS,
    normalize_combat_phase_event_trace_v1,
    parse_query_combat_phase_event_trace_v1_step,
    query_combat_phase_event_trace_v1_step,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.driver import UnsupportedStepError


def available_trace() -> dict[str, object]:
    rows = []
    for index, key in enumerate(_STOCK_KEYS):
        rows.append({
            "global_load_index": index,
            "type_load_index": index if index < 4 else index - 4,
            "event_key": key,
            "event_type": "commander" if index < 4 else "knight",
            "empty_effect": index in {0, 4},
            "selector_role_applicable": index < 4,
            "trigger_valid": False,
            "chance_evaluated_for_differential": True,
            "selector_would_evaluate_chance": False,
            "chance_raw": 0,
            "int_weight": 0,
            "positive_weight": False,
            "selector_eligible": False,
        })
    return {
        "combat_id": 738197508,
        "date_raw": 53192304,
        "target_province_id": 2638,
        "phase_raw": 0,
        "phase": "maneuver",
        "phase_day": 1,
        "evaluator_probe_ready": True,
        "production_trace_ready": False,
        "same_paused_frame_stable": True,
        "real_combat_side_scope": True,
        "all_scope_teardowns_complete": True,
        "unavailable_reason": "production_trace_gates_not_closed",
        "missing_production_readers": ["managed_daily_before_after_transition_driver"],
        "cadence": {"period_days": 5, "current_phase_fires_events": False},
        "global_rng_unchanged_by_probe": True,
        "characters": [{
            "character_id": 29829,
            "side_index": 0,
            "ordered_army_commander": True,
            "selected_side_commander": True,
            "ordered_knight": False,
            "event_rows": rows,
        }],
    }


class CombatPhaseEventTraceQueryTest(unittest.TestCase):
    def test_full_generation_literal(self) -> None:
        self.assertEqual(
            query_combat_phase_event_trace_v1_step(738197508),
            "query-combat-phase-event-trace-v1-738197508",
        )
        for malformed in (
            "query-combat-phase-event-trace-v1-0",
            "query-combat-phase-event-trace-v1-01",
            "query-combat-phase-event-trace-v1-1-extra",
            "query-combat-phase-event-trace-v1-2147483648",
        ):
            self.assertIsNone(parse_query_combat_phase_event_trace_v1_step(malformed))

    def test_ready_evaluator_does_not_claim_transition_or_odds(self) -> None:
        trace = available_trace()
        self.assertIs(
            normalize_combat_phase_event_trace_v1(trace, combat_id=738197508),
            trace,
        )
        for mutation in (
            lambda row: row.update(production_trace_ready=True),
            lambda row: row["characters"][0]["event_rows"].pop(),
            lambda row: row["characters"][0]["event_rows"][1].update(event_key="mod_added"),
            lambda row: row.update(combat_id=738197509),
        ):
            changed = copy.deepcopy(trace)
            mutation(changed)
            with self.assertRaises(ValueError):
                normalize_combat_phase_event_trace_v1(
                    changed, combat_id=738197508,
                )

    def test_unavailable_does_not_invent_character_rows(self) -> None:
        trace = available_trace()
        trace.update({
            "evaluator_probe_ready": False,
            "characters": [],
            "unavailable_reason": "combat_not_found",
        })
        self.assertIs(
            normalize_combat_phase_event_trace_v1(trace, combat_id=738197508),
            trace,
        )
        trace["characters"] = available_trace()["characters"]
        with self.assertRaises(ValueError):
            normalize_combat_phase_event_trace_v1(trace, combat_id=738197508)

    def test_service_preserves_read_only_evaluator_boundary(self) -> None:
        class Driver:
            calls = 0
            capability = True

            def take_snapshot(self) -> dict[str, object]:
                return {
                    "paused": True, "revision": 3,
                    "snapshot_id": "native:3", "date_raw": 53192304,
                }

            def capabilities(self) -> dict[str, object]:
                return {"bridge_capabilities": [
                    QUERY_COMBAT_PHASE_EVENT_TRACE_V1_CAPABILITY,
                ] if self.capability else []}

            def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
                self.calls += 1
                if expected_revision != 3:
                    raise AssertionError("wrong paused revision")
                return {
                    "step": step, "accepted": True,
                    "status": "evaluator_probe_available",
                    "query_sequence": 1,
                    "combat_phase_event_trace": available_trace(),
                    "backend_id": "native-headless",
                }

        driver = Driver()
        service = GameplayBridgeService(driver)
        result = service.query_combat_phase_event_trace_v1(
            738197508, expected_revision=3,
        )
        self.assertEqual(driver.calls, 1)
        self.assertIs(result["production_trace_ready"], False)
        self.assertIs(result["qualified_win_probability_available"], False)
        driver.capability = False
        with self.assertRaises(UnsupportedStepError):
            service.query_combat_phase_event_trace_v1(738197508)
        self.assertEqual(driver.calls, 1)


if __name__ == "__main__":
    unittest.main()
