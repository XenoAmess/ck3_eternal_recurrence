"""Full-slot negative-proof gate for the proposed H2743 border-raid input."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))

from xar_autoplayer.bridge.h2743_border_raid_pair_scan_v1 import (  # noqa: E402
    EXE_SHA256,
    SCHEMA,
    WAR_VALUES_SHA256,
    project_border_raid_pair_from_full_war_storage,
)


FRAME = {
    "snapshot_id": "native:3",
    "revision": 4,
    "native_revision": 3,
    "date_raw": 53217264,
    "episode_run_id": "native-29829-2bc2d599f7f9",
    "connection_generation": 1,
    "checkpoint_sha256": "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9",
    "war_id": 16777231,
    "primary_attacker_character_id": 30097,
    "primary_defender_character_id": 29829,
    "casus_belli_key": "individual_county_de_jure_cb",
    "casus_belli_database_index": 17,
    "target_title_ids": [2128],
}


def _sample(*, border: bool = False) -> dict[str, object]:
    slots: list[dict[str, object]] = [
        {"slot_index": index, "state": "empty"} for index in range(17)
    ]
    slots[4] = {"slot_index": 4, "state": "ended", "war_id": 16777220}
    slots[15] = {
        "slot_index": 15, "state": "active", "war_id": 16777231,
        "primary_attacker_character_id": 30097,
        "primary_defender_character_id": 29829,
        "casus_belli_database_index": 17,
        "casus_belli_key": "individual_county_de_jure_cb",
        "primary_attacker_in_participants": True,
    }
    if border:
        slots[16] = {
            "slot_index": 16, "state": "active", "war_id": 16777232,
            "primary_attacker_character_id": 30097,
            "primary_defender_character_id": 29829,
            "casus_belli_database_index": 99,
            "casus_belli_key": "fp2_border_raid",
            "primary_attacker_in_participants": True,
        }
    return {
        "schema": SCHEMA, "frame": copy.deepcopy(FRAME),
        "exe_sha256": EXE_SHA256,
        "war_values_sha256": WAR_VALUES_SHA256,
        "storage_capacity": 17, "slots": slots,
    }


class BorderRaidPairScanTests(unittest.TestCase):
    def test_complete_negative_and_positive_stay_candidate_only(self) -> None:
        for border in (False, True):
            with self.subTest(border=border):
                first = _sample(border=border)
                result = project_border_raid_pair_from_full_war_storage(
                    FRAME, first, copy.deepcopy(first))
                self.assertEqual(result["status"], "structural_candidate_only")
                self.assertIs(result["border_raid_pair_candidate"], border)
                self.assertIs(result["native_condition_observed"], False)
                self.assertIsNone(result["evaluated_days"])
                self.assertIsNone(result["recommended_outcome"])
                self.assertIsNone(result["action_literal"])

    def test_truncation_generation_and_target_drift_refuse_false(self) -> None:
        for mutation in (
            lambda sample: sample["slots"].pop(),
            lambda sample: sample["slots"][15].update(war_id=16777230),
            lambda sample: sample["slots"][15].update(primary_attacker_character_id=123),
            lambda sample: sample["slots"][15].update(primary_attacker_in_participants=False),
            lambda sample: sample["slots"][1].update(slot_index=True),
        ):
            with self.subTest(mutation=mutation):
                sample = _sample()
                mutation(sample)
                result = project_border_raid_pair_from_full_war_storage(
                    FRAME, sample, copy.deepcopy(sample))
                self.assertEqual(result["status"], "unavailable")
                self.assertIsNone(result["border_raid_pair_candidate"])
                self.assertIsNone(result["action_literal"])

    def test_two_scans_must_match_all_war_rows(self) -> None:
        first = _sample()
        second = _sample(border=True)
        result = project_border_raid_pair_from_full_war_storage(
            FRAME, first, second)
        self.assertEqual(result["reason"], "full_war_storage_scan_drift")
        self.assertIsNone(result["border_raid_pair_candidate"])

    def test_border_raid_with_different_primary_pair_does_not_match(self) -> None:
        sample = _sample(border=True)
        sample["slots"][16]["primary_defender_character_id"] = 43703
        result = project_border_raid_pair_from_full_war_storage(
            FRAME, sample, copy.deepcopy(sample))
        self.assertEqual(result["status"], "structural_candidate_only")
        self.assertIs(result["border_raid_pair_candidate"], False)

    def test_wrong_frame_or_build_stays_unavailable(self) -> None:
        sample = _sample()
        sample["exe_sha256"] = "0" * 64
        self.assertEqual(
            project_border_raid_pair_from_full_war_storage(
                FRAME, sample, copy.deepcopy(sample))["status"], "unavailable")
        changed = copy.deepcopy(FRAME)
        changed["war_id"] += 1
        self.assertEqual(
            project_border_raid_pair_from_full_war_storage(
                changed, _sample(), _sample())["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
