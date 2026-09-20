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
from xar_autoplayer.bridge.succession_transition_contract import (
    freeze_succession_expectation_v1,
)


SNAPSHOT_ID = "native:17"
REVISION = 4
NATIVE_REVISION = 17
DATE_RAW = 53_182_008
PLAYER_ID = 12_345


def _council() -> dict[str, object]:
    vacant = {
        "incumbent_character_id": None,
        "task_key": None,
        "task_type": None,
        "target": None,
        "frozen": None,
        "progress": None,
    }
    return {
        "status": "available",
        "coverage_key": "standard_landed_non_nomadic_core_v1",
        "owner_character_id": PLAYER_ID,
        "positions": [
            {
                "position_key": "councillor_chancellor",
                "incumbent_character_id": 40,
                "task_key": "task_foreign_affairs",
                "task_type": "general",
                "target": None,
                "frozen": False,
                "progress": {
                    "kind": "infinite",
                    "current": None,
                    "maximum": None,
                },
            },
            {"position_key": "councillor_court_chaplain", **vacant},
            {"position_key": "councillor_marshal", **vacant},
            {"position_key": "councillor_spymaster", **vacant},
            {
                "position_key": "councillor_steward",
                "incumbent_character_id": 40,
                "task_key": "task_develop_county",
                "task_type": "county",
                "target": {"kind": "province", "province_id": 70},
                "frozen": False,
                "progress": {
                    "kind": "value",
                    "current": {"raw": 2_000_000, "scale": 100_000},
                    "maximum": {"raw": 10_000_000, "scale": 100_000},
                },
            },
        ],
        "auxiliary_vacancies_complete": False,
        "unavailable_reason": None,
    }


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
        "player_health": (
            {"raw": 275_000, "scale": 100_000}
            if available
            else None
        ),
        "player_domain_size": 6 if available else None,
        "player_domain_limit": 7 if available else None,
        "player_targeting_faction_count": 2 if available else None,
        "council": _council() if available else None,
        "primary_title": (
            {"title_id": 90, "tier_raw": 4, "tier_key": "kingdom"}
            if available
            else None
        ),
        "primary_title_succession_character_ids": (
            [88, 77] if available else []
        ),
        "held_title_partition": (
            [
                {
                    "title": {
                        "title_id": 90,
                        "tier_raw": 4,
                        "tier_key": "kingdom",
                    },
                    "first_heir_character_id": 88,
                    "capital_province_id": None,
                    "primary": True,
                },
                {
                    "title": {
                        "title_id": 91,
                        "tier_raw": 2,
                        "tier_key": "county",
                    },
                    "first_heir_character_id": 77,
                    "capital_province_id": 70,
                    "primary": False,
                },
            ]
            if available
            else []
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
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["readiness"]["minimum_alerts_ready"])
        self.assertTrue(result["readiness"]["ready"])
        ruler = result["ruler_state"]["value"]
        self.assertEqual(ruler["gold"]["value"]["raw"], 2_500_000)
        self.assertEqual(ruler["stress_points"]["value"], 120)
        self.assertEqual(ruler["income"]["status"], "available")
        self.assertEqual(ruler["income"]["value"]["raw"], 570_772)
        self.assertEqual(
            ruler["health_band"]["value"],
            {
                "key": "below_fine",
                "health": {"raw": 275_000, "scale": 100_000},
                "below_fine": True,
                "at_or_below_death_chance_dying": False,
            },
        )
        vitals = ruler["vitals"]
        self.assertEqual(vitals["schema"], "xar.ck3.player-vitals/v1")
        self.assertEqual(vitals["status"], "partial")
        self.assertEqual(vitals["health"]["value"]["band"], "below_fine")
        self.assertEqual(vitals["stress"]["value"]["points"], 120)
        self.assertEqual(vitals["legitimacy"]["status"], "unavailable")
        self.assertFalse(vitals["readiness"]["vitals_ready"])
        self.assertEqual(
            vitals["planner_signals"]["succession_preparation_priority"][
                "value"
            ],
            "elevated",
        )
        self.assertTrue(
            vitals["planner_signals"]["avoid_discretionary_stress_gain"][
                "value"
            ]
        )
        self.assertEqual(
            vitals["planner_signals"]["protect_legitimacy_floor"]["status"],
            "unavailable",
        )
        self.assertTrue(result["readiness"]["ruler_health_alert_ready"])
        self.assertTrue(
            result["alerts"]["value"]["ruler_health_below_fine"]["value"]
        )
        self.assertTrue(result["readiness"]["ruler_resources_ready"])
        realm = result["realm_state"]["value"]
        self.assertTrue(result["readiness"]["realm_domain_ready"])
        self.assertEqual(
            realm["domain"]["value"],
            {
                "size": 6,
                "limit": 7,
                "available_capacity": 1,
                "over_limit_by": 0,
            },
        )
        self.assertTrue(result["readiness"]["realm_faction_alert_ready"])
        self.assertTrue(result["readiness"]["realm_council_ready"])
        self.assertEqual(realm["council"]["value"]["status"], "available")
        self.assertEqual(
            realm["faction_alert"]["value"],
            {"targeting_faction_count": 2, "threatened": True},
        )
        self.assertTrue(
            result["alerts"]["value"]["faction_threat"]["value"]
        )
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
        self.assertTrue(result["readiness"]["succession_partition_ready"])
        self.assertEqual(
            succession["partition"]["value"]["risk_state"],
            "split_successors",
        )
        self.assertEqual(
            [
                row["capital_province_id"]
                for row in succession["partition"]["value"]["title_heirs"]
            ],
            [None, 70],
        )
        self.assertTrue(succession["partition"]["value"]["split_risk"])
        self.assertTrue(
            result["alerts"]["value"]["succession_partition_split"]["value"]
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
        context["held_title_partition"] = []
        context["capital_province_id"] = None
        context["council"] = {
            "status": "unavailable",
            "coverage_key": "standard_landed_non_nomadic_core_v1",
            "owner_character_id": PLAYER_ID,
            "positions": [],
            "auxiliary_vacancies_complete": False,
            "unavailable_reason": (
                "outside_standard_landed_non_nomadic_core_scope"
            ),
        }

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
        self.assertEqual(succession["partition"]["status"], "not_applicable")
        self.assertTrue(result["alerts"]["value"]["ruler_landless"]["value"])
        realm = result["realm_state"]["value"]
        self.assertEqual(realm["council"]["status"], "unavailable")
        self.assertFalse(result["readiness"]["realm_council_ready"])
        self.assertEqual(result["status"], "partial")

    def test_optional_root_gaps_preserve_celestial_succession(self) -> None:
        root = _root()
        context = root["campaign_root_context"]
        assert isinstance(context, dict)
        context["government"] = {
            "key": "celestial_government",
            "flags": ["government_is_celestial", "government_is_settled"],
            "native_flag_count": 2,
        }
        context["council"] = {
            "status": "unavailable",
            "coverage_key": "standard_landed_non_nomadic_core_v1",
            "owner_character_id": PLAYER_ID,
            "positions": [],
            "auxiliary_vacancies_complete": False,
            "unavailable_reason": (
                "outside_standard_landed_non_nomadic_core_scope"
            ),
        }
        context["selected_game_rule_tokens"] = []
        context["native_selected_game_rule_token_count"] = 0
        context["readiness"] = {
            "player_identity_ready": True,
            "player_monthly_gold_income_ready": True,
            "player_health_ready": True,
            "player_domain_ready": True,
            "player_targeting_factions_ready": True,
            "primary_title_ready": True,
            "primary_title_succession_ready": True,
            "held_title_partition_ready": True,
            "council_ready": False,
            "capital_ready": True,
            "lieges_ready": True,
            "direct_landed_vassals_ready": True,
            "adjacent_external_province_holders_ready": True,
            "related_character_contexts_ready": True,
            "government_ready": True,
            "selected_game_rule_tokens_ready": False,
            "same_frame_ready": True,
            "ready": False,
        }

        result = build_turn_bundle_v1(_snapshot(), root)

        self.assertEqual(root["status"], "available")
        self.assertFalse(context["readiness"]["ready"])
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["unavailable_reason"])
        self.assertEqual(
            result["realm_state"]["value"]["council"]["status"],
            "unavailable",
        )
        self.assertTrue(result["readiness"]["succession_partition_ready"])
        succession = result["succession_state"]["value"]
        self.assertEqual(
            succession["primary_title_heir_character_id"]["value"],
            88,
        )

        expectation = freeze_succession_expectation_v1(
            result,
            episode_run_id="native-12345-optional-root-gap",
            episode_character_id=PLAYER_ID,
        )
        self.assertEqual(expectation["expectation_state"], "successor_expected")
        self.assertEqual(expectation["expected_successor_character_id"], 88)

    def test_available_title_without_successor_raises_minimum_alert(self) -> None:
        root = _root()
        context = root["campaign_root_context"]
        assert isinstance(context, dict)
        context["primary_title_succession_character_ids"] = []
        context["held_title_partition"][0]["first_heir_character_id"] = None

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
        self.assertEqual(ruler["vitals"]["health"]["status"], "available")
        self.assertEqual(ruler["vitals"]["stress"]["status"], "unavailable")
        self.assertTrue(ruler["vitals"]["readiness"]["health_ready"])
        self.assertFalse(ruler["vitals"]["readiness"]["stress_ready"])
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

    def test_health_bands_follow_stock_strategy_thresholds(self) -> None:
        for raw, key, below_fine, dying_or_worse in (
            (150_000, "dying_or_worse", True, True),
            (150_001, "below_fine", True, False),
            (299_999, "below_fine", True, False),
            (300_000, "fine_or_better", False, False),
        ):
            with self.subTest(raw=raw):
                root = _root()
                context = root["campaign_root_context"]
                assert isinstance(context, dict)
                context["player_health"] = {
                    "raw": raw,
                    "scale": 100_000,
                }
                result = build_turn_bundle_v1(_snapshot(), root)
                band = result["ruler_state"]["value"]["health_band"]["value"]
                self.assertEqual(band["key"], key)
                self.assertEqual(band["below_fine"], below_fine)
                self.assertEqual(
                    band["at_or_below_death_chance_dying"], dying_or_worse
                )

    def test_rejects_malformed_campaign_root_health(self) -> None:
        root = _root()
        context = root["campaign_root_context"]
        assert isinstance(context, dict)
        context["player_health"] = {"raw": 275_000, "scale": 1}

        with self.assertRaises(ValueError):
            build_turn_bundle_v1(_snapshot(), root)

    def test_rejects_malformed_domain_capacity(self) -> None:
        for field, value in (
            ("player_domain_size", -1),
            ("player_domain_limit", 0),
        ):
            with self.subTest(field=field):
                root = _root()
                context = root["campaign_root_context"]
                assert isinstance(context, dict)
                context[field] = value
                with self.assertRaises(ValueError):
                    build_turn_bundle_v1(_snapshot(), root)

    def test_rejects_malformed_targeting_faction_count(self) -> None:
        root = _root()
        context = root["campaign_root_context"]
        assert isinstance(context, dict)
        context["player_targeting_faction_count"] = -1

        with self.assertRaises(ValueError):
            build_turn_bundle_v1(_snapshot(), root)


if __name__ == "__main__":
    unittest.main()
