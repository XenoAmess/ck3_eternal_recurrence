from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.combat_advantage_components_contract import (
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
                     "complete": True},
                    {"side_index": 1, "roll": 1,
                     "commander_character_id": 28801, "roll_raw": 100000,
                     "commander_raw": 50000, "aggregator_raw": 25000,
                     "total_raw": 175000, "helper_calls": 2,
                     "complete": True},
                ],
            }],
        },
    }


class AdvantageComponentsContractTest(unittest.TestCase):
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

        for mutation in (change_side, change_cache, change_combat,
                         change_roll, change_order, change_available,
                         change_source):
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


if __name__ == "__main__":
    unittest.main()
