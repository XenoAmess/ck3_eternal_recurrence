"""Fail-closed direction checks for the WAR31 serialized truce-slot mapping."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from project_war31_truce_slot_direction import project_direction  # noqa: E402


class War31TruceSlotDirectionTests(unittest.TestCase):
    def test_first_and_second_are_distinct_owner_directions(self) -> None:
        value = project_direction({
            "status": "observed_pair_truce_slots",
            "first_character_id": 29829,
            "second_character_id": 30097,
            "raw_slots": {
                "truce_0": {"date": "1079.11.17", "result": "defeat"},
                "truce_1": {"date": "1079.11.17", "result": "victory"},
            },
        })
        self.assertEqual(
            [(row["slot"], row["owner_character_id"],
              row["toward_character_id"]) for row in value],
            [("truce_0", 29829, 30097), ("truce_1", 30097, 29829)],
        )

    def test_missing_or_unknown_slot_is_not_given_a_direction(self) -> None:
        base = {"status": "observed_pair_truce_slots",
                "first_character_id": 29829,
                "second_character_id": 30097}
        with self.assertRaisesRegex(ValueError, "slots absent"):
            project_direction({**base, "raw_slots": {}})
        with self.assertRaisesRegex(ValueError, "unexpected saved truce slot"):
            project_direction({**base, "raw_slots": {"truce_2": {"date": "1079.11.17"}}})


if __name__ == "__main__":
    unittest.main()
