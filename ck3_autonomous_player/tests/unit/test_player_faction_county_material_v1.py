from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.player_faction_alerts_contract import (
    normalize_player_faction_alerts_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12003


COUNTY_TITLE_ID = 50_331_649


def _frame(*, latest_build: bool = True) -> dict[str, object]:
    frame = json.loads(
        (
            PROJECT_ROOT
            / "tests/fixtures/native_12002/governance/faction-alerts.json"
        ).read_text(encoding="utf-8")
    )
    if latest_build:
        frame["provenance"] = {
            "game_version": CK3_12003.game_version,
            "executable_sha256": CK3_12003.executable_sha256,
            "backend_id": CK3_12003.backend_id("player-faction-alerts-v1"),
        }
    return frame


def _county_row(county_title_id: int = COUNTY_TITLE_ID) -> dict[str, object]:
    return {
        "county_title_id": county_title_id,
        "capital_province_id": 181,
        "holder_character_id": 16_777_217,
        "county_opinion": {"raw": -23, "scale": 1},
        "native_county_join_score": {"raw": -3_100_000, "scale": 100_000},
        "can_add_county": False,
        "removal_queued": False,
        "native_leave_score_threshold": {"raw": -25, "scale": 1},
        "opinion_status": "available",
        "native_final_status": "available",
    }


def _with_observations(rows: object) -> dict[str, object]:
    frame = _frame()
    frame["targeting_factions"][1]["county_member_observations"] = rows
    return frame


def _normalize(frame: dict[str, object]) -> dict[str, object]:
    return normalize_player_faction_alerts_v1(
        frame,
        expected_date_raw=frame["date_raw"],
        expected_snapshot_revision=frame["snapshot_revision"],
        expected_game_version=frame["provenance"]["game_version"],
        expected_executable_sha256=frame["provenance"]["executable_sha256"],
    )


class PlayerFactionCountyMaterialV1Tests(unittest.TestCase):
    def test_legacy_12002_rows_keep_their_shape_without_new_observation_key(self) -> None:
        frame = _frame(latest_build=False)
        normalized = _normalize(frame)

        self.assertEqual(normalized["targeting_factions"], frame["targeting_factions"])
        self.assertTrue(normalized["readiness"]["alert_ready"])
        self.assertTrue(
            all(
                "county_member_observations" not in row
                for row in normalized["targeting_factions"]
            )
        )

    def test_material_preserves_signed_values_and_false_native_results(self) -> None:
        frame = _with_observations([_county_row()])
        normalized = _normalize(frame)
        row = normalized["targeting_factions"][1]["county_member_observations"][0]

        self.assertEqual(row, _county_row())
        self.assertIs(row["can_add_county"], False)
        self.assertIs(row["removal_queued"], False)
        self.assertEqual(normalized["planner_projection"], frame["planner_projection"])
        self.assertEqual(normalized["readiness"], frame["readiness"])

    def test_zero_values_remain_available_material(self) -> None:
        row = _county_row()
        for name in (
            "county_opinion",
            "native_county_join_score",
            "native_leave_score_threshold",
        ):
            row[name]["raw"] = 0
        normalized = _normalize(_with_observations([row]))

        self.assertEqual(
            normalized["targeting_factions"][1]["county_member_observations"],
            [row],
        )

    def test_unavailable_material_preserves_null_fields_and_status(self) -> None:
        for status in ("unavailable", "unsupported_build"):
            with self.subTest(status=status):
                row = _county_row()
                for name in (
                    "capital_province_id",
                    "holder_character_id",
                    "county_opinion",
                    "native_county_join_score",
                    "can_add_county",
                    "removal_queued",
                    "native_leave_score_threshold",
                ):
                    row[name] = None
                row["opinion_status"] = status
                row["native_final_status"] = status
                normalized = _normalize(_with_observations([row]))

                self.assertEqual(
                    normalized["targeting_factions"][1]["county_member_observations"],
                    [row],
                )

    def test_present_empty_vector_is_preserved_without_changing_old_readiness(self) -> None:
        normalized = _normalize(_with_observations([]))

        self.assertEqual(
            normalized["targeting_factions"][1]["county_member_observations"], []
        )
        self.assertTrue(normalized["readiness"]["alert_ready"])

    def test_independent_getter_results_survive_partial_native_failure(self) -> None:
        row = _county_row()
        row["capital_province_id"] = None
        row["holder_character_id"] = None
        row["native_county_join_score"] = None
        row["can_add_county"] = None
        row["native_final_status"] = "unavailable"
        normalized = _normalize(_with_observations([row]))

        self.assertEqual(
            normalized["targeting_factions"][1]["county_member_observations"],
            [row],
        )
        self.assertEqual(row["opinion_status"], "available")
        self.assertIs(row["removal_queued"], False)
        self.assertEqual(row["native_leave_score_threshold"], {"raw": -25, "scale": 1})

    def test_partial_ordered_material_matches_existing_county_member_ids(self) -> None:
        frame = _with_observations([_county_row(COUNTY_TITLE_ID + 1)])
        frame["targeting_factions"][1]["county_member_title_ids"].append(
            COUNTY_TITLE_ID + 1
        )
        normalized = _normalize(frame)

        self.assertEqual(
            normalized["targeting_factions"][1]["county_member_observations"],
            [_county_row(COUNTY_TITLE_ID + 1)],
        )

    def test_signed_native_storage_limits_are_preserved(self) -> None:
        for sign in (-1, 1):
            with self.subTest(sign=sign):
                row = _county_row()
                int32_edge = -(2**31) if sign < 0 else 2**31 - 1
                int64_edge = -(2**63) if sign < 0 else 2**63 - 1
                row["county_opinion"]["raw"] = int32_edge
                row["native_leave_score_threshold"]["raw"] = int32_edge
                row["native_county_join_score"]["raw"] = int64_edge
                normalized = _normalize(_with_observations([row]))

                self.assertEqual(
                    normalized["targeting_factions"][1]["county_member_observations"],
                    [row],
                )

    def test_rejects_material_with_wrong_wire_shape_or_scalar_type(self) -> None:
        invalid_values = (
            ("county_title_id", 0),
            ("capital_province_id", -1),
            ("holder_character_id", True),
            ("county_opinion", {"raw": -23, "scale": 100_000}),
            ("county_opinion", {"raw": 2**31, "scale": 1}),
            ("native_county_join_score", {"raw": -1, "scale": 1}),
            ("native_county_join_score", {"raw": -(2**63) - 1, "scale": 100_000}),
            ("native_leave_score_threshold", {"raw": True, "scale": 1}),
            ("can_add_county", 0),
            ("removal_queued", "false"),
            ("opinion_status", "unknown"),
            ("native_final_status", None),
        )
        for name, value in invalid_values:
            with self.subTest(name=name, value=value):
                row = _county_row()
                row[name] = value
                with self.assertRaises(ValueError):
                    _normalize(_with_observations([row]))
        for vector in (None, {}, [_county_row() | {"extra": None}]):
            with self.subTest(vector=vector):
                with self.assertRaises(ValueError):
                    _normalize(_with_observations(vector))
        row = _county_row()
        del row["opinion_status"]
        with self.assertRaises(ValueError):
            _normalize(_with_observations([row]))

    def test_rejects_foreign_duplicate_or_reordered_county_material(self) -> None:
        for rows in (
            [_county_row(COUNTY_TITLE_ID + 2)],
            [_county_row(), _county_row()],
            [_county_row(COUNTY_TITLE_ID + 1), _county_row()],
        ):
            with self.subTest(rows=rows):
                frame = _with_observations(rows)
                frame["targeting_factions"][1]["county_member_title_ids"].append(
                    COUNTY_TITLE_ID + 1
                )
                with self.assertRaisesRegex(ValueError, "county_member_title_ids order"):
                    _normalize(frame)


if __name__ == "__main__":
    unittest.main()
