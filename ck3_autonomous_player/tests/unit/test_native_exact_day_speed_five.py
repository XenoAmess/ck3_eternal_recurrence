"""Exact-day speed admission keeps the native stop and tactical exclusions."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    _TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES,
    _life_advance_timeline_policy,
    _noncombat_generic_exact_day_speed_five_ready,
)


class NoncombatExactDaySpeedFiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = {
            "paused": True,
            "map_ready": True,
            "active_event": None,
            "pending_character_interaction": None,
            "war_objective_assault_supported": True,
            "top_exclusive_modal_choice_hint": {"status": "absent"},
            "active_wars": [{"war_id": 1}],
            "player_armies": [{
                "controllable": True,
                "in_combat": False,
                "retreating": False,
                "army_state": "moving",
                "army_state_code": 7,
            }],
        }
        self.options = {
            "exact_one_day": True,
            "result_step": "life-advance-one-day",
            "bridge_capabilities": set(_TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES),
            "available_action_steps": {"set-speed-1", "set-speed-5"},
        }

    def ready(self, frame=None, **options) -> bool:
        return _noncombat_generic_exact_day_speed_five_ready(
            self.frame if frame is None else frame,
            **(self.options | options),
        )

    def test_only_native_stopped_generic_one_day_is_admitted(self) -> None:
        self.assertTrue(self.ready())
        self.assertEqual(
            _life_advance_timeline_policy(
                self.frame,
                horizon_days=1,
                exact_one_day=True,
                exact_one_day_proof_kind=None,
                available_action_steps={"set-speed-1", "set-speed-5"},
            ),
            (1, "exact_one_day_unavoidable_contact"),
        )
        self.assertFalse(self.ready(bridge_capabilities=set()))
        self.assertFalse(self.ready(available_action_steps={"set-speed-1"}))
        self.assertFalse(self.ready(result_step="advance-route-contact-horizon-v1"))
        self.assertFalse(self.ready(exact_one_day=False))

    def test_combat_retreat_and_unresolved_army_flags_stay_slow(self) -> None:
        for key, value in (
            ("in_combat", True), ("in_combat", None),
            ("retreating", True), ("retreating", None),
            ("army_state_code", 2),
        ):
            with self.subTest(key=key, value=value):
                army = {**self.frame["player_armies"][0], key: value}
                self.assertFalse(self.ready({**self.frame, "player_armies": [army]}))
        self.assertFalse(self.ready({**self.frame, "player_armies": None}))

    def test_event_modal_assault_and_incomplete_war_stay_slow(self) -> None:
        for key, value in (
            ("active_event", {"instance_id": 42}),
            ("pending_character_interaction", {"instance_id": 5}),
            ("top_exclusive_modal_choice_hint", {"status": "present"}),
            ("war_objective_assault_supported", None),
            ("active_wars", None),
        ):
            with self.subTest(key=key):
                self.assertFalse(self.ready({**self.frame, key: value}))
        siege = {"siege_observable": True, "active_siege": {
            "player_army_besieging": True,
            "assault_observable": True,
            "assault_in_progress": True,
        }}
        war = {"war_id": 1, "objective_province_states": [siege]}
        self.assertFalse(self.ready({**self.frame, "active_wars": [war]}))


if __name__ == "__main__":
    unittest.main()
