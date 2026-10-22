"""Authored boundary failures and JSON round trips; no game-result credit."""
from __future__ import annotations

from copy import deepcopy
import json
import unittest

from xar_autoplayer.bridge.player_pilgrimage_traits import (
    TRAIT_KEYS, normalize_player_pilgrimage_traits_v1,
)


def context() -> dict[str, object]:
    return {"schema": "ck3_12004_religion_context_v1", "available": True,
            "capture_epoch": 2**53 + 1, "date_raw": 10, "played_character_id": 1}


def observation() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for key in TRAIT_KEYS:
        rows.append({"trait_key": key, "has_track": key != "hajjaj", "present": True,
                     "experience_raw": None if key == "hajjaj" else 0})
    return {"schema": "ck3_12004_player_pilgrimage_traits_v1", "read_only": True,
            "available": True, "unavailable_reason": None, "capture_epoch": str(2**53 + 1),
            "date_raw": 10, "played_character_id": 1, "raw_scale": 100000, "traits": rows}


class PilgrimageTraitContractTests(unittest.TestCase):
    def test_observed_zero_untracked_and_json_roundtrip(self) -> None:
        value = observation()
        parsed = normalize_player_pilgrimage_traits_v1(value, current_context=context())
        assert parsed is not None
        self.assertEqual(parsed, value)
        self.assertEqual(parsed["traits"][0]["experience_raw"], 0)
        self.assertIsNone(parsed["traits"][1]["experience_raw"])
        self.assertEqual(normalize_player_pilgrimage_traits_v1(json.loads(json.dumps(parsed)),
                         current_context=context()), parsed)
        self.assertEqual(parsed["capture_epoch"], "9007199254740993")

    def test_integer_fields_refuse_bool_float_and_unbounded_values(self) -> None:
        for key in ("date_raw", "played_character_id", "raw_scale"):
            for wrong in (True, 1.0, 2**64):
                value = observation(); value[key] = wrong
                with self.subTest(key=key, wrong=wrong), self.assertRaises(ValueError):
                    normalize_player_pilgrimage_traits_v1(value, current_context=context())
        for wrong in (True, 0.0, -1, 10_000_001):
            value = observation()
            rows = value["traits"]
            assert isinstance(rows, list)
            rows[0]["experience_raw"] = wrong
            with self.subTest(xp=wrong), self.assertRaises(ValueError):
                normalize_player_pilgrimage_traits_v1(value, current_context=context())

    def test_exact_fields_order_and_types_are_required(self) -> None:
        for key in observation():
            value = observation(); del value[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                normalize_player_pilgrimage_traits_v1(value, current_context=context())
        for change in ("extra", "row_missing", "wrong_key", "reordered", "tuple", "empty"):
            value = observation()
            rows = value["traits"]
            assert isinstance(rows, list)
            if change == "extra": value["alias"] = rows
            elif change == "row_missing": del rows[0]["experience_raw"]
            elif change == "wrong_key": rows[0]["trait_key"] = "pilgrimage"
            elif change == "reordered": rows.reverse()
            elif change == "tuple": value["traits"] = tuple(rows)
            elif change == "empty": value["traits"] = []
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize_player_pilgrimage_traits_v1(value, current_context=context())

    def test_epoch_is_canonical_decimal_and_preserves_adjacent_uint64(self) -> None:
        for wrong in (2**53 + 1, "09007199254740993", "9007199254740992", "18446744073709551616"):
            value = observation(); value["capture_epoch"] = wrong
            with self.subTest(epoch=wrong), self.assertRaises(ValueError):
                normalize_player_pilgrimage_traits_v1(value, current_context=context())
        owner = context(); owner["capture_epoch"] = True
        with self.assertRaises(ValueError):
            normalize_player_pilgrimage_traits_v1(observation(), current_context=owner)

    def test_absence_has_null_xp_and_known_hajj_track_identity(self) -> None:
        value = observation()
        rows = value["traits"]
        assert isinstance(rows, list)
        rows[0].update(present=False, experience_raw=None)
        parsed = normalize_player_pilgrimage_traits_v1(value, current_context=context())
        assert parsed is not None
        self.assertIs(parsed["traits"][0]["present"], False)
        for field, wrong in (("has_track", True), ("present", 1), ("experience_raw", 0)):
            bad = deepcopy(value)
            bad_rows = bad["traits"]
            assert isinstance(bad_rows, list)
            bad_rows[1][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_player_pilgrimage_traits_v1(bad, current_context=context())

    def test_unavailable_null_and_partial_rows_are_distinct(self) -> None:
        self.assertIsNone(normalize_player_pilgrimage_traits_v1(None, current_context=context()))
        value = observation(); value.update(available=False, unavailable_reason="trait_experience_unavailable")
        rows = value["traits"]
        assert isinstance(rows, list)
        for row in rows: row.update(present=None, experience_raw=None)
        parsed = normalize_player_pilgrimage_traits_v1(value, current_context=context())
        assert parsed is not None
        self.assertFalse(parsed["available"])
        self.assertEqual(json.loads(json.dumps(parsed)), value)
        rows[0]["present"] = True
        with self.assertRaises(ValueError):
            normalize_player_pilgrimage_traits_v1(value, current_context=context())


if __name__ == "__main__":
    unittest.main(verbosity=2)
