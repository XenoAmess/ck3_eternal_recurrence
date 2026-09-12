from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.turn_bundle_contract import (
    TURN_BUNDLE_V1_SCHEMA,
    build_turn_bundle_v1,
)


SNAPSHOT_ID = "native:17"
REVISION = 4
NATIVE_REVISION = 17
DATE_RAW = 53_182_008
PLAYER_ID = 12_345


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": SNAPSHOT_ID,
        "revision": REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "backend_id": "native-headless",
        "played_character": {
            "character_id": PLAYER_ID,
            "alive": True,
            "stress_points": 120,
        },
        "played_character_gold": {"raw": 2_500_000, "scale": 100_000},
        "active_event": None,
        "pending_character_interaction": None,
        "active_wars": [
            {
                "war_id": 20,
                "player_side": "defender",
                "primary_opponent_character_id": 77,
                "player_relative_war_score": -12,
            },
            {
                "war_id": 10,
                "player_side": "attacker",
                "primary_opponent_character_id": 66,
                "player_relative_war_score": 35,
            },
        ],
    }


def _root(*, available: bool = True) -> dict[str, object]:
    context: dict[str, object] = {
        "status": "available" if available else "unavailable",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "player_character_id": PLAYER_ID if available else None,
        "player_character_alive": True if available else None,
        "player_monthly_gold_income": (
            {"raw": 570_772, "scale": 100_000}
            if available
            else None
        ),
        "primary_title": (
            {"title_id": 90, "tier_raw": 4, "tier_key": "kingdom"}
            if available
            else None
        ),
        "primary_title_succession_character_ids": (
            [88, 77] if available else []
        ),
        "capital_province_id": 70 if available else None,
        "top_liege_character_id": PLAYER_ID if available else None,
        "independent": True if available else None,
        "direct_landed_vassal_character_ids": [40] if available else [],
        "adjacent_external_province_holder_character_ids": (
            [50] if available else []
        ),
        "related_character_contexts": (
            [
                {
                    "character_id": 40,
                    "relationship_role": "direct_landed_vassal",
                    "top_liege_character_id": PLAYER_ID,
                },
                {
                    "character_id": 50,
                    "relationship_role": (
                        "adjacent_external_province_holder"
                    ),
                    "top_liege_character_id": 99,
                },
            ]
            if available
            else []
        ),
        "government": (
            {"key": "feudal_government", "flags": [], "native_flag_count": 0}
            if available
            else None
        ),
        "unavailable_reason": None if available else "state_changed",
    }
    return {
        "status": context["status"],
        "query_sequence": 9,
        "binding": {
            "snapshot_id": SNAPSHOT_ID,
            "revision": REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "expected_revision": REVISION,
        },
        "campaign_root_context": context,
    }


class TurnBundleV1Tests(unittest.TestCase):
    def test_available_bundle_preserves_successor_order_and_minimum_alerts(
        self,
    ) -> None:
        result = build_turn_bundle_v1(_snapshot(), _root())

        self.assertEqual(result["schema"], TURN_BUNDLE_V1_SCHEMA)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["readiness"]["minimum_alerts_ready"])
        self.assertFalse(result["readiness"]["ready"])
        ruler = result["ruler_state"]["value"]
        self.assertEqual(ruler["gold"]["value"]["raw"], 2_500_000)
        self.assertEqual(ruler["stress_points"]["value"], 120)
        self.assertEqual(ruler["income"]["status"], "available")
        self.assertEqual(ruler["income"]["value"]["raw"], 570_772)
        self.assertTrue(result["readiness"]["ruler_resources_ready"])
        realm = result["realm_state"]["value"]
        self.assertEqual(
            realm["adjacent_holder_top_liege_character_ids"], [99]
        )
        succession = result["succession_state"]["value"]
        self.assertEqual(
            succession["ordered_primary_title_successor_character_ids"],
            [88, 77],
        )
        self.assertEqual(
            succession["primary_title_heir_character_id"]["value"], 88
        )
        self.assertFalse(
            succession["no_primary_title_heir_alert"]["value"]
        )
        self.assertTrue(
            result["alerts"]["value"][
                "ruler_stress_at_or_above_100"
            ]["value"]
        )
        self.assertEqual(
            [row["war_id"] for row in result["war_state"]["value"]["wars"]],
            [10, 20],
        )

    def test_landless_state_is_not_applicable_instead_of_unknown(self) -> None:
        root = _root()
        context = root["campaign_root_context"]
        assert isinstance(context, dict)
        context["primary_title"] = None
        context["primary_title_succession_character_ids"] = []
        context["capital_province_id"] = None

        result = build_turn_bundle_v1(_snapshot(), root)

        ruler = result["ruler_state"]["value"]
        succession = result["succession_state"]["value"]
        self.assertEqual(ruler["primary_title"]["status"], "not_applicable")
        self.assertEqual(
            succession["primary_title_heir_character_id"]["status"],
            "not_applicable",
        )
        self.assertEqual(
            succession["no_primary_title_heir_alert"]["status"],
            "not_applicable",
        )
        self.assertTrue(result["alerts"]["value"]["ruler_landless"]["value"])

    def test_available_title_without_successor_raises_minimum_alert(self) -> None:
        root = _root()
        context = root["campaign_root_context"]
        assert isinstance(context, dict)
        context["primary_title_succession_character_ids"] = []

        result = build_turn_bundle_v1(_snapshot(), root)
        succession = result["succession_state"]["value"]

        self.assertTrue(
            succession["no_primary_title_heir_alert"]["value"]
        )
        self.assertEqual(
            succession["primary_title_heir_character_id"][
                "unavailable_reason"
            ],
            "no_observed_primary_title_successor",
        )

    def test_unavailable_root_remains_typed_and_clears_every_domain(self) -> None:
        result = build_turn_bundle_v1(_snapshot(), _root(available=False))

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], "state_changed")
        for domain in (
            "ruler_state",
            "realm_state",
            "succession_state",
            "pending_state",
            "war_state",
            "alerts",
        ):
            self.assertEqual(result[domain]["status"], "unavailable")
        self.assertFalse(any(result["readiness"].values()))

    def test_rejects_cross_frame_character_and_war_identity_drift(self) -> None:
        drifted_binding = _root()
        drifted_binding["binding"]["revision"] = REVISION + 1
        wrong_character = _snapshot()
        wrong_character["played_character"]["character_id"] = PLAYER_ID + 1
        duplicate_wars = _snapshot()
        duplicate_wars["active_wars"][1]["war_id"] = 20

        for snapshot, root in (
            (_snapshot(), drifted_binding),
            (wrong_character, _root()),
            (duplicate_wars, _root()),
        ):
            with self.subTest(), self.assertRaises(ValueError):
                build_turn_bundle_v1(snapshot, root)

    def test_missing_optional_snapshot_observations_stay_explicit(self) -> None:
        snapshot = copy.deepcopy(_snapshot())
        snapshot.pop("played_character_gold")
        snapshot["played_character"].pop("stress_points")
        snapshot.pop("active_event")
        snapshot.pop("pending_character_interaction")
        snapshot.pop("active_wars")

        result = build_turn_bundle_v1(snapshot, _root())

        ruler = result["ruler_state"]["value"]
        self.assertEqual(ruler["gold"]["status"], "unavailable")
        self.assertFalse(result["readiness"]["ruler_resources_ready"])
        self.assertEqual(ruler["stress_points"]["status"], "unavailable")
        self.assertEqual(
            result["pending_state"]["value"]["active_event"]["status"],
            "unavailable",
        )
        self.assertEqual(result["war_state"]["status"], "unavailable")
        self.assertFalse(result["readiness"]["war_summary_ready"])

    def test_rejects_malformed_campaign_root_income(self) -> None:
        root = _root()
        context = root["campaign_root_context"]
        assert isinstance(context, dict)
        context["player_monthly_gold_income"] = {
            "raw": 570_772,
            "scale": 1,
        }

        with self.assertRaises(ValueError):
            build_turn_bundle_v1(_snapshot(), root)


if __name__ == "__main__":
    unittest.main()
