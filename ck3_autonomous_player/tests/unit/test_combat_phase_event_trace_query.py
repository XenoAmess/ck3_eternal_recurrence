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
    normalize_experimental_counter_output_response_v1,
    normalize_runtime_counter_output_diagnostic_v1,
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


def managed_counter_trace() -> dict[str, object]:
    return {
        "schema_version": 1,
        "managed_checkpoint": {
            "recoverable_checkpoint_created": True,
            "exact_one_day_observed": True,
            "boundary_dates_match_checkpoint": True,
            "detours_uninstalled": True,
        },
        "trace": {
            "schema_version": 1,
            "status": "captured",
            "failure_flags": 0,
            "readiness": {
                "bounded_capture_complete": True,
                "runtime_counter_output_pair_complete": True,
            },
            "runtime_counter_output": {
                "source": "native_resolve_counter_classes_after_0x23caf20",
                "requested": True,
                "pair_complete": True,
                "count": 2,
                "hook_calls": 2,
                "target_calls": 2,
                "first_failure_gate": 0,
                "sides": [
                    {
                        "side_index": side_index,
                        "countered_entry_count": 18,
                        "countering_entry_count": 14,
                        "context_raw": 125000,
                        "class_count": 2,
                        "capacity": 2,
                        "retention_raw": [87500, 100000],
                    }
                    for side_index in (0, 1)
                ],
            },
        },
    }


def experimental_counter_response() -> dict[str, object]:
    return {
        "type": "command_result", "protocol_version": 1, "ok": True,
        "result": {
            "step": "experimental-combat-phase-event-trace-finish-v1",
            "accepted": True, "private_build": True,
            "production_trace_ready": False,
            "status": "bounded_trace_available",
            "managed_daily_sequence_token": 109,
            "combat_id": 738197508,
            "managed_trace": managed_counter_trace(),
        },
    }


class CombatPhaseEventTraceQueryTest(unittest.TestCase):
    def test_experimental_counter_response_keeps_private_boundary(self) -> None:
        response = experimental_counter_response()
        diagnostic = normalize_experimental_counter_output_response_v1(
            response, combat_id=738197508,
        )
        self.assertEqual(diagnostic["combat_id"], 738197508)
        self.assertIs(diagnostic["forecast_usable"], False)
        del response["result"]["managed_trace"]["trace"]["runtime_counter_output"]
        self.assertIsNone(normalize_experimental_counter_output_response_v1(
            response, combat_id=738197508,
        ))

    def test_experimental_counter_response_rejects_status_or_scope_spoof(self) -> None:
        mutations = (
            lambda response: response["result"].update(production_trace_ready=True),
            lambda response: response["result"].update(combat_id=738197509),
            lambda response: response["result"].update(status="trace_unavailable"),
            lambda response: response["result"].update(managed_daily_sequence_token=True),
            lambda response: response["result"].update(step="query-combat-phase-event-trace-v1-738197508"),
        )
        for mutate in mutations:
            response = experimental_counter_response()
            mutate(response)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                normalize_experimental_counter_output_response_v1(
                    response, combat_id=738197508,
                )

    def test_counter_output_absent_is_compatible_with_old_managed_trace(self) -> None:
        trace = managed_counter_trace()
        del trace["trace"]["runtime_counter_output"]
        self.assertIsNone(normalize_runtime_counter_output_diagnostic_v1(trace))

    def test_counter_output_is_diagnostic_even_with_complete_synthetic_pair(self) -> None:
        trace = managed_counter_trace()
        diagnostic = normalize_runtime_counter_output_diagnostic_v1(trace)
        self.assertIsNotNone(diagnostic)
        self.assertIs(diagnostic["diagnostic_observation_complete"], True)
        self.assertIs(diagnostic["forecast_usable"], False)
        self.assertEqual(diagnostic["validation_status"], "live_validation_pending")
        self.assertEqual(diagnostic["sides"], trace["trace"]["runtime_counter_output"]["sides"])
        self.assertEqual(diagnostic["hook_diagnostic"], {
            "hook_calls": 2, "target_calls": 2, "first_failure_gate": 0,
        })

    def test_earlier_counter_output_wire_remains_readable(self) -> None:
        trace = managed_counter_trace()
        output = trace["trace"]["runtime_counter_output"]
        for key in ("hook_calls", "target_calls", "first_failure_gate"):
            del output[key]
        self.assertIsNone(normalize_runtime_counter_output_diagnostic_v1(
            trace)["hook_diagnostic"])

    def test_counter_output_partial_capture_remains_diagnostic(self) -> None:
        trace = managed_counter_trace()
        output = trace["trace"]["runtime_counter_output"]
        output["pair_complete"] = False
        output["count"] = 1
        output["sides"].pop()
        trace["trace"]["failure_flags"] = 1 << 20
        trace["trace"]["status"] = "failed"
        trace["trace"]["readiness"]["bounded_capture_complete"] = False
        trace["trace"]["readiness"]["runtime_counter_output_pair_complete"] = False
        diagnostic = normalize_runtime_counter_output_diagnostic_v1(trace)
        self.assertIs(diagnostic["diagnostic_observation_complete"], False)
        self.assertIs(diagnostic["forecast_usable"], False)

    def test_counter_output_sequence_failure_codes_remain_diagnostic(self) -> None:
        for gate in (3, 31, 32, 33):
            trace = managed_counter_trace()
            output = trace["trace"]["runtime_counter_output"]
            output.update(pair_complete=False, count=0, sides=[],
                          first_failure_gate=gate)
            trace["trace"]["failure_flags"] = 1 << 20
            trace["trace"]["status"] = "failed"
            trace["trace"]["readiness"]["bounded_capture_complete"] = False
            trace["trace"]["readiness"]["runtime_counter_output_pair_complete"] = False
            with self.subTest(gate=gate):
                diagnostic = normalize_runtime_counter_output_diagnostic_v1(trace)
                self.assertEqual(diagnostic["hook_diagnostic"]["first_failure_gate"], gate)
                self.assertIs(diagnostic["forecast_usable"], False)

    def test_counter_output_rejects_forged_pair_or_vector(self) -> None:
        mutations = (
            lambda trace: trace["trace"]["runtime_counter_output"]["sides"][1].update(side_index=0),
            lambda trace: trace["trace"]["runtime_counter_output"]["sides"][1].update(class_count=3),
            lambda trace: trace["trace"]["runtime_counter_output"]["sides"][1]["retention_raw"].append(10),
            lambda trace: trace["trace"]["runtime_counter_output"]["sides"][0].update(capacity=1),
            lambda trace: trace["trace"]["runtime_counter_output"].update(count=1),
            lambda trace: trace["trace"]["runtime_counter_output"].update(requested=False),
            lambda trace: trace["trace"]["runtime_counter_output"].update(hook_calls=1),
            lambda trace: trace["trace"]["runtime_counter_output"].update(target_calls=3),
            lambda trace: trace["trace"]["runtime_counter_output"].update(first_failure_gate=6),
            lambda trace: trace["trace"]["readiness"].update(runtime_counter_output_pair_complete=False),
            lambda trace: trace["trace"].update(failure_flags=1 << 20),
            lambda trace: trace["managed_checkpoint"].update(detours_uninstalled=None),
            lambda trace: trace["trace"]["runtime_counter_output"]["sides"][0]["retention_raw"].__setitem__(0, True),
        )
        for mutate in mutations:
            trace = managed_counter_trace()
            mutate(trace)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                normalize_runtime_counter_output_diagnostic_v1(trace)

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
