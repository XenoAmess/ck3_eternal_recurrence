from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
)


REQUEST = {
    "subject_public_cunit_id": 18,
    "character_id": 34333,
    "regiment_id": 61,
    "expected_played_character_id": 29829,
    "expected_war_id": 4,
    "expected_native_carmy_id": 18,
    "expected_combat_id": 16777218,
    "expected_province_id": 2633,
    "expected_date_raw": 53146368,
    "expected_revision": 3,
    "expected_native_revision": 3,
    "expected_snapshot_id": "native:3",
}


def frame(revision: int = 3) -> dict[str, object]:
    return {
        "paused": True,
        "snapshot_id": "native:3",
        "revision": revision,
        "native_revision": 3,
        "date_raw": 53146368,
        "episode_run_id": "fixture",
        "diagnostics": {"connection_generation": 1},
        "played_character": {"character_id": 29829},
        "active_wars": [{"war_id": 4}],
        "player_armies": [{
            "army_id": 18,
            "controllable": True,
            "in_combat": True,
            "current_province_id": 2633,
        }],
    }


def raw_result() -> dict[str, object]:
    return {
        "step": "query-current-battle-knight-v1-18-34333-61",
        "accepted": True,
        "status": "available",
        "query_sequence": 1,
        "snapshot_revision": 3,
        "current_battle_knight": {
            "schema": "current-battle-knight-v1",
            "observed_date_raw": 53146368,
            "combat_id": 16777218,
            "province_id": 2633,
            "subject_public_cunit_id": 18,
            "native_carmy_id": 18,
            "character_id": 34333,
            "regiment_id": 61,
            "current_effective_prowess": 11,
            "knight_effectiveness_raw": 100000,
            "province_evaluated_damage_raw": 11000000,
            "province_evaluated_toughness_raw": 2200000,
            "stored_combat_entry_damage_raw": 15000000,
            "stored_combat_entry_toughness_raw": 3000000,
            "scale": 100000,
            "paired_generation_ids_verified": True,
            "double_sample_stable": True,
            "province_evaluation_fresh": True,
        },
    }


class FakeNative:
    def __init__(self, *, drift: bool = False, bad_row: bool = False) -> None:
        self.snapshots = [frame(), frame()]
        if drift:
            self.snapshots[1]["native_revision"] = 4
        self.result = raw_result()
        if bad_row:
            self.result["current_battle_knight"]["character_id"] = 34332
        self.calls: list[dict[str, object]] = []

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshots.pop(0))

    def _execute_primitive_step(self, step: str, **kwargs: object) -> dict[str, object]:
        self.calls.append({"step": step, **kwargs})
        return copy.deepcopy(self.result)

    def query_current_battle_knight_v1(self, **kwargs: object) -> dict[str, object]:
        return NativeHeadlessGameplayDriver.query_current_battle_knight_v1(
            self, **kwargs
        )


class CurrentBattleKnightPortTests(unittest.TestCase):
    def test_native_exact_request_and_distinct_fresh_stats(self) -> None:
        fake = FakeNative()
        result = fake.query_current_battle_knight_v1(**REQUEST)
        self.assertEqual(result["queried_revision"], 3)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0]["expected_revision"], 3)
        self.assertEqual(fake.calls[0]["request_fields"]["expected_war_id"], 4)
        self.assertEqual(
            result["current_battle_knight"]["province_evaluated_damage_raw"],
            11000000,
        )
        self.assertEqual(
            result["current_battle_knight"]["stored_combat_entry_damage_raw"],
            15000000,
        )

    def test_stale_revision_rejects_before_submission(self) -> None:
        fake = FakeNative()
        with self.assertRaises(BridgeUnavailableError):
            fake.query_current_battle_knight_v1(
                **{**REQUEST, "expected_revision": 4}
            )
        self.assertEqual(fake.calls, [])

    def test_wrong_character_and_frame_drift_reject(self) -> None:
        with self.assertRaises(BridgeUnavailableError):
            FakeNative(bad_row=True).query_current_battle_knight_v1(**REQUEST)
        with self.assertRaises(BridgeUnavailableError):
            FakeNative(drift=True).query_current_battle_knight_v1(**REQUEST)

    def test_hybrid_preserves_wrapper_and_native_revisions(self) -> None:
        native = FakeNative()

        class Hybrid:
            def __init__(self) -> None:
                self.native = native
                self.snapshots = [frame(4), frame(4)]

            def take_snapshot(self) -> dict[str, object]:
                return copy.deepcopy(self.snapshots.pop(0))

        hybrid = Hybrid()
        result = ConfiguredHybridFallbackDriver.query_current_battle_knight_v1(
            hybrid, **{**REQUEST, "expected_revision": 4}
        )
        self.assertEqual(result["queried_revision"], 4)
        self.assertEqual(result["queried_native_revision"], 3)
        self.assertEqual(native.calls[0]["expected_revision"], 3)


if __name__ == "__main__":
    unittest.main()
