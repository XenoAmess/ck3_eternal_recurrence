"""Unexecuted candidate tests: copy into the repository tests/unit after integration."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.faction_county_culture_inputs_v1 import (
    normalize_county_culture_relation_v1,
    project_player_faction_county_culture_context_v1,
)
from xar_autoplayer.bridge.player_faction_alerts_contract import normalize_player_faction_alerts_v1
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.strategy import _general_war_entry_faction_context


COUNTY_TITLE_ID = 50_331_649


def _relation(county: int | None = 16_777_217, target: int | None = 33_554_433) -> dict[str, object]:
    ready = county is not None and target is not None
    return {
        "county_culture_id": county,
        "target_culture_id": target,
        "same_culture_as_target": county == target if ready else None,
        "culture_relation_status": "available" if ready else "unavailable",
    }


def _county_row() -> dict[str, object]:
    return {
        "county_title_id": COUNTY_TITLE_ID,
        "capital_province_id": 181,
        "holder_character_id": 16_777_217,
        "county_opinion": {"raw": -23, "scale": 1},
        "native_county_join_score": {"raw": 3_100_000, "scale": 100_000},
        "can_add_county": True,
        "removal_queued": False,
        "native_leave_score_threshold": {"raw": 5, "scale": 1},
        "opinion_status": "available",
        "native_final_status": "available",
    }


def _frame(culture: dict[str, object] | None) -> dict[str, object]:
    value = json.loads((PROJECT_ROOT / "tests/fixtures/native_12002/governance/faction-alerts.json").read_text(encoding="utf-8"))
    value["provenance"] = {
        "game_version": CK3_12003.game_version,
        "executable_sha256": CK3_12003.executable_sha256,
        "backend_id": CK3_12003.backend_id("player-faction-alerts-v1"),
    }
    county = _county_row()
    if culture is not None:
        county.update(culture)
    value["targeting_factions"][1]["county_member_observations"] = [county]
    # Keep this integration fixture focused on one populist county. The stock
    # fixture also has the same county under peasant_faction; a separate case
    # below verifies that distinct faction/county relations are not merged.
    value["targeting_factions"][2]["county_member_title_ids"] = []
    return value


def _normalize(frame: dict[str, object]) -> dict[str, object]:
    return normalize_player_faction_alerts_v1(
        frame,
        expected_date_raw=frame["date_raw"],
        expected_snapshot_revision=frame["snapshot_revision"],
        expected_game_version=CK3_12003.game_version,
        expected_executable_sha256=CK3_12003.executable_sha256,
    )


class FactionCountyCultureInputsV1Tests(unittest.TestCase):
    def test_full_generation_ids_with_same_slot_are_different(self) -> None:
        value = _relation(16_777_217, 33_554_433)
        self.assertEqual(value["county_culture_id"] & 0xFFFFFF, value["target_culture_id"] & 0xFFFFFF)
        normalized = normalize_county_culture_relation_v1(value, field="county")
        self.assertIs(normalized["same_culture_as_target"], False)

    def test_zero_and_signed_full_ids_survive_without_truthiness(self) -> None:
        for county, target in ((0, 0), (0, 1), (-(2**31), 2**31 - 1), (-2, -2)):
            with self.subTest(county=county, target=target):
                value = _relation(county, target)
                self.assertEqual(normalize_county_culture_relation_v1(value, field="county"), value)

    def test_partial_failure_retains_one_resolved_identity(self) -> None:
        for value in (_relation(0, None), _relation(None, -2), _relation(None, None)):
            with self.subTest(value=value):
                self.assertEqual(normalize_county_culture_relation_v1(value, field="county"), value)
                normalized = _normalize(_frame(value))
                self.assertTrue(normalized["readiness"]["alert_ready"])
                row = normalized["targeting_factions"][1]["county_member_observations"][0]
                self.assertEqual(row["native_county_join_score"], {"raw": 3_100_000, "scale": 100_000})
                self.assertIs(row["can_add_county"], True)
                self.assertIs(row["removal_queued"], False)

    def test_legacy_row_shape_is_preserved_and_culture_is_not_ready(self) -> None:
        normalized = _normalize(_frame(None))
        self.assertEqual(normalized["targeting_factions"][1]["county_member_observations"][0], _county_row())
        context = project_player_faction_county_culture_context_v1(normalized)
        row = context["rows"][0]
        self.assertIs(row["relation_input_ready"], False)
        self.assertIsNone(row["same_culture_as_target"])
        self.assertEqual(row["unavailable_reason"], "culture_fields_not_published")

    def test_missing_county_material_is_not_a_complete_empty_input(self) -> None:
        frame = _frame(None)
        del frame["targeting_factions"][1]["county_member_observations"]
        context = project_player_faction_county_culture_context_v1(_normalize(frame))
        self.assertEqual(context["county_row_count"], 1)
        self.assertEqual(context["status"], "unavailable")
        self.assertEqual(context["rows"][0]["unavailable_reason"], "county_member_observation_not_published")

    def test_no_county_members_do_not_claim_an_observed_culture_relation(self) -> None:
        frame = _frame(_relation())
        for faction in frame["targeting_factions"]:
            faction["county_member_title_ids"] = []
            faction.pop("county_member_observations", None)
        context = project_player_faction_county_culture_context_v1(_normalize(frame))
        self.assertEqual(context["status"], "not_applicable")
        self.assertIs(context["relation_input_ready"], False)
        self.assertEqual(context["rows"], [])

    def test_consumer_exposes_input_without_changing_existing_strategy_context(self) -> None:
        complete = _normalize(_frame(_relation()))
        partial = _normalize(_frame(_relation(0, None)))
        root = {"player_targeting_faction_count": complete["targeting_faction_count"]}
        first = _general_war_entry_faction_context(root, complete)
        second = _general_war_entry_faction_context(root, partial)
        first_culture = first.pop("county_culture_context")
        second_culture = second.pop("county_culture_context")
        self.assertEqual(first, second)
        self.assertIs(first_culture["relation_input_ready"], True)
        self.assertIs(second_culture["relation_input_ready"], False)
        self.assertEqual(first_culture["snapshot_revision"], complete["snapshot_revision"])
        self.assertEqual(first_culture["date_raw"], complete["date_raw"])
        self.assertEqual(first_culture["player_character_id"], complete["player_character_id"])
        self.assertEqual(first_culture["provenance"], complete["provenance"])
        self.assertEqual(first_culture["rows"][0]["target_character_id"], complete["player_character_id"])

    def test_mixed_available_and_unavailable_rows_report_partial(self) -> None:
        frame = _frame(_relation())
        faction = frame["targeting_factions"][1]
        extra = copy.deepcopy(faction["county_member_observations"][0])
        extra["county_title_id"] = COUNTY_TITLE_ID + 1
        extra.update(_relation(None, 0))
        faction["county_member_title_ids"].append(COUNTY_TITLE_ID + 1)
        faction["county_member_observations"].append(extra)
        context = project_player_faction_county_culture_context_v1(_normalize(frame))
        self.assertEqual(context["status"], "partial")
        self.assertEqual(context["available_relation_count"], 1)
        self.assertEqual(context["county_row_count"], 2)
        self.assertIs(context["relation_input_ready"], False)

    def test_same_county_in_distinct_factions_keeps_both_relations(self) -> None:
        frame = _frame(_relation())
        sibling = frame["targeting_factions"][2]
        sibling["county_member_title_ids"] = [COUNTY_TITLE_ID]
        sibling["county_member_observations"] = [
            copy.deepcopy(frame["targeting_factions"][1]["county_member_observations"][0])
        ]
        context = project_player_faction_county_culture_context_v1(_normalize(frame))
        self.assertEqual(context["county_row_count"], 2)
        self.assertEqual([row["county_title_id"] for row in context["rows"]], [COUNTY_TITLE_ID, COUNTY_TITLE_ID])
        self.assertNotEqual(context["rows"][0]["faction_id"], context["rows"][1]["faction_id"])

    def test_rejects_invalid_wire_and_inconsistent_availability(self) -> None:
        invalid = (
            ("county_culture_id", True),
            ("target_culture_id", False),
            ("county_culture_id", -1),
            ("target_culture_id", -(2**31) - 1),
            ("target_culture_id", 2**31),
            ("county_culture_id", "0"),
            ("county_culture_id", 0.0),
            ("same_culture_as_target", 0),
            ("same_culture_as_target", "false"),
            ("same_culture_as_target", True),
            ("same_culture_as_target", None),
            ("county_culture_id", None),
            ("culture_relation_status", "unsupported_build"),
            ("culture_relation_status", None),
            ("culture_relation_status", "unavailable"),
        )
        for field, replacement in invalid:
            with self.subTest(field=field, replacement=replacement):
                value = _relation()
                value[field] = replacement
                with self.assertRaises(ValueError):
                    _normalize(_frame(value))
        for field in _relation():
            with self.subTest(missing_field=field):
                value = _relation()
                del value[field]
                with self.assertRaises(ValueError):
                    _normalize(_frame(value))
        value = _relation(None, 0)
        value["same_culture_as_target"] = False
        with self.assertRaises(ValueError):
            _normalize(_frame(value))


if __name__ == "__main__":
    unittest.main()
