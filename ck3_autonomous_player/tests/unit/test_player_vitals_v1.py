from __future__ import annotations

from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.player_vitals_contract import (
    PLAYER_VITALS_V1_SCHEMA,
    build_player_vitals_v1,
)


def _component(
    status: str,
    value: object = None,
    reason: str | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "value": value,
        "unavailable_reason": reason,
    }


def _health(raw: int = 275_000) -> dict[str, object]:
    band = (
        "dying_or_worse"
        if raw <= 150_000
        else "below_fine"
        if raw < 300_000
        else "fine_or_better"
    )
    return _component(
        "available",
        {
            "key": band,
            "health": {"raw": raw, "scale": 100_000},
            "below_fine": raw < 300_000,
            "at_or_below_death_chance_dying": raw <= 150_000,
        },
    )


def _succession(
    *, no_heir: bool = False, split: bool = True
) -> dict[str, object]:
    return {
        "no_primary_title_heir_alert": _component("available", no_heir),
        "partition": _component("available", {"split_risk": split}),
    }


def _build(
    *,
    health: object | None = None,
    stress: object | None = None,
    succession: object | None = None,
    legitimacy: object | None = None,
) -> dict[str, object]:
    return build_player_vitals_v1(
        turn_bundle_binding={
            "snapshot_id": "native:17",
            "native_revision": 17,
            "date_raw": 53_182_008,
        },
        character_id=12_345,
        health_band=_health() if health is None else health,
        stress_points=(
            _component("available", 120) if stress is None else stress
        ),
        succession_state=(
            _succession() if succession is None else succession
        ),
        legitimacy=legitimacy,
    )


class PlayerVitalsV1Tests(unittest.TestCase):
    def test_missing_legitimacy_preserves_live_health_stress_and_signals(self) -> None:
        result = _build()

        self.assertEqual(result["schema"], PLAYER_VITALS_V1_SCHEMA)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(
            result["binding"],
            {
                "character_id": 12_345,
                "snapshot_id": "native:17",
                "snapshot_revision": 17,
                "date_raw": 53_182_008,
            },
        )
        self.assertEqual(
            result["health"]["value"],
            {
                "raw": 275_000,
                "scale": 100_000,
                "band": "below_fine",
                "below_fine": True,
                "at_or_below_death_chance_dying": False,
            },
        )
        self.assertEqual(
            result["stress"]["value"],
            {
                "points": 120,
                "at_or_above_first_break_threshold": True,
            },
        )
        self.assertEqual(result["legitimacy"]["status"], "unavailable")
        self.assertTrue(result["readiness"]["health_ready"])
        self.assertTrue(result["readiness"]["stress_ready"])
        self.assertFalse(
            result["readiness"]["legitimacy_classification_ready"]
        )
        self.assertFalse(result["readiness"]["vitals_ready"])
        signals = result["planner_signals"]
        self.assertEqual(
            signals["succession_preparation_priority"]["value"],
            "elevated",
        )
        self.assertTrue(
            signals["avoid_discretionary_stress_gain"]["value"]
        )
        self.assertEqual(
            signals["protect_legitimacy_floor"]["status"],
            "unavailable",
        )

    def test_dying_ruler_with_no_heir_or_split_is_critical(self) -> None:
        result = _build(
            health=_health(150_000),
            succession=_succession(no_heir=True, split=False),
        )

        self.assertEqual(
            result["planner_signals"]["succession_preparation_priority"][
                "value"
            ],
            "critical",
        )

    def test_fine_health_and_low_stress_keep_minimum_signals_normal(self) -> None:
        result = _build(
            health=_health(300_000),
            stress=_component("available", 99),
        )

        signals = result["planner_signals"]
        self.assertEqual(
            signals["succession_preparation_priority"]["value"], "normal"
        )
        self.assertFalse(
            signals["avoid_discretionary_stress_gain"]["value"]
        )

    def test_health_and_succession_signal_survive_missing_stress(self) -> None:
        result = _build(
            stress=_component(
                "unavailable",
                reason="played_character_stress_unavailable",
            )
        )

        self.assertEqual(result["health"]["status"], "available")
        self.assertEqual(
            result["planner_signals"]["succession_preparation_priority"][
                "value"
            ],
            "elevated",
        )
        self.assertEqual(result["stress"]["status"], "unavailable")
        self.assertEqual(
            result["planner_signals"]["avoid_discretionary_stress_gain"][
                "status"
            ],
            "unavailable",
        )

    def test_engine_legitimacy_floor_closes_full_readiness(self) -> None:
        result = _build(
            legitimacy=_component(
                "available",
                {
                    "raw": 0,
                    "scale": 100_000,
                    "type_key": "mandate_legitimacy",
                    "current_level": 0,
                    "at_floor_level": True,
                },
            )
        )

        self.assertEqual(result["status"], "available")
        self.assertTrue(result["readiness"]["vitals_ready"])
        self.assertTrue(
            result["planner_signals"]["protect_legitimacy_floor"]["value"]
        )

    def test_engine_proven_not_applicable_is_classified_without_balance(self) -> None:
        result = _build(
            legitimacy=_component(
                "not_applicable",
                reason="no_applicable_legitimacy_type",
            )
        )

        self.assertEqual(result["status"], "available")
        self.assertFalse(result["readiness"]["legitimacy_balance_ready"])
        self.assertTrue(
            result["readiness"]["legitimacy_classification_ready"]
        )
        self.assertFalse(result["readiness"]["vitals_ready"])
        self.assertFalse(
            result["planner_signals"]["protect_legitimacy_floor"]["value"]
        )

    def test_unready_succession_closes_only_its_planner_signal(self) -> None:
        result = _build(
            succession={
                "no_primary_title_heir_alert": _component(
                    "unavailable", reason="succession_unavailable"
                ),
                "partition": _component("available", {"split_risk": True}),
            }
        )

        signals = result["planner_signals"]
        self.assertEqual(
            signals["succession_preparation_priority"]["status"],
            "unavailable",
        )
        self.assertTrue(
            signals["avoid_discretionary_stress_gain"]["value"]
        )

    def test_rejects_binding_and_health_cutoff_drift(self) -> None:
        malformed_health = _health()
        malformed_health["value"]["below_fine"] = False
        with self.assertRaisesRegex(ValueError, "frozen cutoffs"):
            _build(health=malformed_health)
        with self.assertRaisesRegex(ValueError, "snapshot_id"):
            build_player_vitals_v1(
                turn_bundle_binding={
                    "snapshot_id": "",
                    "native_revision": 17,
                    "date_raw": 53_182_008,
                },
                character_id=12_345,
                health_band=_health(),
                stress_points=_component("available", 0),
                succession_state=_succession(),
            )


if __name__ == "__main__":
    unittest.main()
