"""Exact-day speed admission keeps the native stop and tactical exclusions."""

from pathlib import Path
import sys
import json
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver, BridgeUnavailableError, WAR_OBJECTIVE_ASSAULT_CAPABILITY,
    _TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES,
    _life_advance_timeline_policy,
    _noncombat_generic_exact_day_speed_five_ready,
)

from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from xar_autoplayer.bridge.service import GameplayBridgeService


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



class NativeCampaignProjectionSpeedFiveTest(unittest.TestCase):
    """Use real protocol ingestion and the native_campaign producer branch."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def make_driver(
        self, *, assault: bool,
    ) -> tuple[NativeHeadlessGameplayDriver, FakeEndpoint]:
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint,
            state_dir=Path(self.temp.name) / ("yes" if assault else "no"),
            command_timeout_seconds=0.1, episode_projection="native_campaign",
        )
        self.addCleanup(driver.close)
        capabilities = ["game.state.snapshot", *_TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES]
        if assault:
            capabilities.append(WAR_OBJECTIVE_ASSAULT_CAPABILITY)
        endpoint.publish(_hello(*capabilities))
        endpoint.publish(_snapshot(
            played_character={"character_id": 31254, "alive": True, "source": "native"},
            active_wars=[], player_armies=[],
        ))
        return driver, endpoint

    def ready(self, snapshot: dict[str, object]) -> bool:
        return _noncombat_generic_exact_day_speed_five_ready(
            snapshot, exact_one_day=True, result_step="life-advance-one-day",
            bridge_capabilities=set(_TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES),
            available_action_steps={"set-speed-1", "set-speed-5"},
        )

    def test_native_campaign_true_reaches_service_json_and_speed_guard(self) -> None:
        driver, _ = self.make_driver(assault=True)
        service = GameplayBridgeService(driver)
        internal = driver.take_internal_semantic_snapshot()
        public = service.snapshot(include_native_command_history=False)
        self.assertIs(internal["war_objective_assault_supported"], True)
        self.assertEqual(internal["episode_projection"], "native_campaign")
        round_trip = json.loads(json.dumps(public))
        self.assertIs(type(round_trip["war_objective_assault_supported"]), bool)
        self.assertTrue(self.ready(round_trip))
        self.assertNotIn("one_life_terminal", round_trip)
        self.assertEqual(round_trip["player_armies"], [])

    def test_missing_capability_stays_false_after_json_and_snapshot_spoof(self) -> None:
        driver, _ = self.make_driver(assault=False)
        actual = driver.take_internal_semantic_snapshot()
        self.assertIs(actual["war_objective_assault_supported"], False)
        self.assertFalse(self.ready(json.loads(json.dumps(actual))))
        for spoof in (True, 1, "true", None):
            with self.subTest(spoof=spoof):
                supplied = {**driver.state.semantic_snapshot(),
                            "war_objective_assault_supported": spoof}
                projected = driver._with_one_life_episode(supplied)
                self.assertIs(projected["war_objective_assault_supported"], False)
                self.assertFalse(self.ready(projected))

    def test_hello_withdrawal_cannot_reuse_supported_flag(self) -> None:
        driver, endpoint = self.make_driver(assault=True)
        self.assertIs(driver.take_internal_semantic_snapshot()["war_objective_assault_supported"], True)
        endpoint.publish(_hello("game.state.snapshot", *_TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES))
        with self.assertRaises(BridgeUnavailableError):
            driver.take_internal_semantic_snapshot()
        endpoint.publish(_snapshot(
            revision=2, played_character={"character_id": 31254, "alive": True, "source": "native"},
            active_wars=[], player_armies=[],
        ))
        current = driver.take_internal_semantic_snapshot()
        self.assertIs(current["war_objective_assault_supported"], False)
        self.assertFalse(self.ready(current))

    def test_unknown_capability_identifier_is_not_support(self) -> None:
        driver, endpoint = self.make_driver(assault=False)
        endpoint.publish(_hello("game.state.snapshot", "game.state.war-objective-assault-unknown"))
        endpoint.publish(_snapshot(
            revision=2, played_character={"character_id": 31254, "alive": True, "source": "native"},
            active_wars=[], player_armies=[],
        ))
        current = driver.take_internal_semantic_snapshot()
        self.assertIs(current["war_objective_assault_supported"], False)
        self.assertFalse(self.ready(current))

    def test_real_projection_does_not_bypass_other_speed_guards(self) -> None:
        driver, _ = self.make_driver(assault=True)
        actual = driver.take_internal_semantic_snapshot()
        self.assertTrue(self.ready(actual))
        for key, value in (
            ("active_event", {"instance_id": 42}),
            ("pending_character_interaction", {"instance_id": 7}),
            ("paused", False), ("map_ready", False),
            ("war_objective_assault_supported", 1),
            ("war_objective_assault_supported", "true"),
            ("active_wars", None),
            ("top_exclusive_modal_choice_hint", {"status": "present"}),
        ):
            with self.subTest(key=key, value=value):
                self.assertFalse(self.ready({**actual, key: value}))


if __name__ == "__main__":
    unittest.main()
