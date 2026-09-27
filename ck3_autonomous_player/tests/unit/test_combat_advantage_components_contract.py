from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.combat_advantage_components_contract import (
    normalize_experimental_advantage_components_response_v1,
    normalize_runtime_advantage_components_v1,
)


COMBAT_ID = 738197508


def sample() -> dict[str, object]:
    return {
        "schema_version": 1,
        "managed_checkpoint": {
            "recoverable_checkpoint_created": True,
            "exact_one_day_observed": True,
            "boundary_dates_match_checkpoint": True,
            "detours_uninstalled": True,
        },
        "advantage_components": {
            "schema_version": 1,
            "source": "native_cache_0x2308d50_original_calls",
            "requested": True,
            "available": True,
            "failure_flags": 0,
            "first_aggregator_failure": {
                "gate": 0, "thread_id": 0, "caller_rva": 0,
                "caller_address": 0, "side_index": -1,
                "expected_side_index": -1, "helper_calls": 0,
                "value_present": False,
            },
            "materializations": [{
                "ordinal": 0, "thread_id": 420, "caller_rva": 0x27FB4AC,
                "combat_id": COMBAT_ID,
                "date_raw": 53192328, "base_raw": 200000,
                "resolved_raw": 300000, "complete": True,
                "sides": [
                    {"side_index": 0, "roll": 2,
                     "commander_character_id": 29829, "roll_raw": 200000,
                     "commander_raw": 50000, "aggregator_raw": 25000,
                     "total_raw": 275000, "helper_calls": 2,
                     "nested_aggregator_calls": 1,
                     "primary_aggregator_calls": 1,
                     "complete": True},
                    {"side_index": 1, "roll": 1,
                     "commander_character_id": 28801, "roll_raw": 100000,
                     "commander_raw": 50000, "aggregator_raw": 25000,
                     "total_raw": 175000, "helper_calls": 2,
                     "nested_aggregator_calls": 0,
                     "primary_aggregator_calls": 1,
                     "complete": True},
                ],
            }],
        },
    }


class AdvantageComponentsContractTest(unittest.TestCase):
    def test_private_finish_envelope_decodes_new_first_failure(self) -> None:
        managed = sample()
        output = managed["advantage_components"]
        output["available"] = False
        output["failure_flags"] = 64
        output["first_aggregator_failure"] = {
            "gate": 2, "thread_id": 420, "caller_rva": 0x2307A03,
            "caller_address": 0x142307A03, "side_index": 0,
            "expected_side_index": 0, "helper_calls": 0,
            "value_present": True,
        }
        frame = {
            "type": "command_result", "protocol_version": 1, "ok": True,
            "result": {
                "step": "experimental-combat-phase-event-trace-finish-v1",
                "accepted": True, "private_build": True,
                "production_trace_ready": False,
                "status": "trace_unavailable",
                "managed_daily_sequence_token": 109,
                "combat_id": COMBAT_ID, "managed_trace": managed,
            },
        }
        diagnostic = normalize_experimental_advantage_components_response_v1(
            frame, combat_id=COMBAT_ID)
        self.assertEqual(diagnostic["first_aggregator_failure"]["gate"], 2)
        self.assertIs(diagnostic["forecast_usable"], False)
        frame["result"]["status"] = "bounded_trace_available"
        with self.assertRaises(ValueError):
            normalize_experimental_advantage_components_response_v1(
                frame, combat_id=COMBAT_ID)

    def test_old_managed_trace_has_no_optional_diagnostic(self) -> None:
        frame = sample()
        del frame["advantage_components"]
        self.assertIsNone(normalize_runtime_advantage_components_v1(
            frame, combat_id=COMBAT_ID))

    def test_complete_original_pair_is_retrospective_only(self) -> None:
        result = normalize_runtime_advantage_components_v1(
            sample(), combat_id=COMBAT_ID)
        self.assertIs(result["diagnostic_observation_complete"], True)
        self.assertIs(result["forecast_usable"], False)
        self.assertEqual(result["validation_status"], "live_validation_pending")

    def test_historical_103_shape_remains_readable(self) -> None:
        frame = sample()
        output = frame["advantage_components"]
        del output["first_aggregator_failure"]
        for side in output["materializations"][0]["sides"]:
            del side["nested_aggregator_calls"]
            del side["primary_aggregator_calls"]
        output["available"] = False
        output["failure_flags"] = 64
        historical = normalize_runtime_advantage_components_v1(
            frame, combat_id=COMBAT_ID)
        self.assertIs(historical["diagnostic_observation_complete"], False)
        self.assertIs(historical["forecast_usable"], False)

    def test_arithmetic_identity_and_scope_spoofs_are_rejected(self) -> None:
        def change_side(frame):
            frame["advantage_components"]["materializations"][0]["sides"][0]["commander_raw"] += 1

        def change_cache(frame):
            frame["advantage_components"]["materializations"][0]["resolved_raw"] += 1

        def change_combat(frame):
            frame["advantage_components"]["materializations"][0]["combat_id"] += 1

        def change_roll(frame):
            frame["advantage_components"]["materializations"][0]["sides"][0]["roll"] += 1

        def change_order(frame):
            frame["advantage_components"]["materializations"][0]["sides"].reverse()

        def change_available(frame):
            frame["advantage_components"]["available"] = False

        def change_source(frame):
            frame["advantage_components"]["source"] = "paused_residual"

        def change_nested_count(frame):
            frame["advantage_components"]["materializations"][0]["sides"][0]["nested_aggregator_calls"] = 2

        def change_failure_gate(frame):
            frame["advantage_components"]["first_aggregator_failure"]["gate"] = 2

        for mutation in (change_side, change_cache, change_combat,
                         change_roll, change_order, change_available,
                         change_source, change_nested_count,
                         change_failure_gate):
            frame = copy.deepcopy(sample())
            mutation(frame)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                normalize_runtime_advantage_components_v1(
                    frame, combat_id=COMBAT_ID)

    def test_partial_capture_is_not_claimed_available(self) -> None:
        frame = sample()
        component = frame["advantage_components"]
        component["available"] = False
        component["failure_flags"] = 16
        component["materializations"][0]["complete"] = False
        component["materializations"][0]["sides"][1]["complete"] = False
        result = normalize_runtime_advantage_components_v1(
            frame, combat_id=COMBAT_ID)
        self.assertIs(result["diagnostic_observation_complete"], False)
        self.assertIs(result["forecast_usable"], False)

    def test_complete_arithmetic_row_with_helper_failure_is_not_admitted(self) -> None:
        frame = sample()
        component = frame["advantage_components"]
        component["available"] = False
        component["failure_flags"] = 64
        component["first_aggregator_failure"] = {
            "gate": 2, "thread_id": 420, "caller_rva": 0x2307A03,
            "caller_address": 0x142307A03, "side_index": 0,
            "expected_side_index": 0, "helper_calls": 0,
            "value_present": True,
        }
        result = normalize_runtime_advantage_components_v1(
            frame, combat_id=COMBAT_ID)
        self.assertIs(component["materializations"][0]["complete"], True)
        self.assertIs(result["diagnostic_observation_complete"], False)
        self.assertIs(result["forecast_usable"], False)

    def test_first_unexpected_call_requires_precise_caller_and_flag(self) -> None:
        frame = sample()
        output = frame["advantage_components"]
        output["available"] = False
        output["failure_flags"] = 64
        output["first_aggregator_failure"] = {
            "gate": 2, "thread_id": 420, "caller_rva": 0x2307A03,
            "caller_address": 0x142307A03, "side_index": 0,
            "expected_side_index": 0, "helper_calls": 0,
            "value_present": True,
        }
        self.assertIs(normalize_runtime_advantage_components_v1(
            frame, combat_id=COMBAT_ID)["diagnostic_observation_complete"], False)
        output["first_aggregator_failure"]["caller_address"] = 0
        with self.assertRaises(ValueError):
            normalize_runtime_advantage_components_v1(frame, combat_id=COMBAT_ID)


if __name__ == "__main__":
    unittest.main()
