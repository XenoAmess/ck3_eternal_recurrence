from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


FIXTURE_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "fixtures"
    / "combat_simulation_inputs_v2_available.json"
)
STEP = (
    "query-combat-simulation-inputs-v2-5-2-a-1-16777217-d-1-16777218"
)


class FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_combat_simulation_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _fixture_result() -> dict[str, object]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return copy.deepcopy(payload["result"])


def _partial_fixture_result() -> dict[str, object]:
    result = _fixture_result()
    resolution = result["combat_simulation_inputs"]["counter_resolutions"][0]
    resolution.update(
        {
            "status": "unavailable",
            "countered_modifier_owner_character_id": None,
            "countering_modifier_owner_character_id": None,
            "context_scale_raw": None,
            "damage_retention_by_class_raw": None,
            "unavailable_reason": "counter_context_scale_unavailable",
        }
    )
    result["combat_simulation_inputs"]["completeness"].update(
        {
            "input_observation_ready": False,
            "missing_required_domains": [
                "counter_resolutions",
                "damage_to_casualty_allocation",
                "pursuit_transition",
                "battle_end_and_retreat_transition",
                "phase_event_rng_and_effects",
            ],
        }
    )
    result["status"] = "partial"
    return result


def _army(
    army_id: int,
    *,
    controllable: bool,
    province_id: int,
) -> dict[str, object]:
    return {
        "army_id": army_id,
        "owner_character_id": 707 if controllable else 808,
        "soldiers": 1_000,
        "current_province_id": province_id,
        "move_target_province_id": None,
        "controllable": controllable,
    }


def _war() -> dict[str, object]:
    player = _army(16_777_217, controllable=True, province_id=2)
    enemy = _army(16_777_218, controllable=False, province_id=5)
    return {
        "war_id": 16_777_217,
        "player_side": "attacker",
        "primary_opponent_character_id": 808,
        "player_is_primary_war_leader": True,
        "enemy_primary_default_raise_province_id": None,
        "player_relative_war_score": 0,
        "allied_armies": [player],
        "enemy_armies": [enemy],
        "war_objective_province_ids": [],
        "objective_province_states": [],
        "targeted_title_ids": [],
    }


def _hello() -> dict[str, object]:
    return {
        "type": "hello",
        "protocol_version": 1,
        "bridge_version": "0.1.0",
        "pid": 4242,
        "session_generation": 0,
        "game_version": "1.19.0.6",
        "executable_sha256": "a" * 64,
        "capabilities": [
            "game.state.snapshot",
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
        ],
    }


def _snapshot(
    revision: int = 5,
    *,
    paused: bool = True,
) -> dict[str, object]:
    player = _army(16_777_217, controllable=True, province_id=2)
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.9.15",
            "date_raw": 53_171_400,
            "speed": 1,
            "paused": paused,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 707, "alive": True},
            "one_life_settlement": None,
            "active_wars": [_war()],
            "player_armies": [player],
        },
    }


def _native_driver() -> tuple[NativeHeadlessGameplayDriver, FakeEndpoint]:
    endpoint = FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(_hello())
    endpoint.publish(_snapshot())
    return driver, endpoint


def _answer_with(
    endpoint: FakeEndpoint,
    result_factory,
) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        result = result_factory()
        result["step"] = frame["step"]
        endpoint.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": result,
            }
        )

    endpoint.send_hook = answer


class CombatSimulationInputsNativeDriverTests(unittest.TestCase):
    def test_dynamic_query_is_atomic_cached_and_not_advertised_as_action(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertNotIn(
            QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
            capabilities["action_steps"],
        )
        self.assertFalse(
            any(
                step.startswith("query-combat-simulation-inputs-v2-")
                for step in capabilities["action_steps"]
            )
        )
        _answer_with(endpoint, _fixture_result)
        revision = int(driver.take_snapshot()["revision"])

        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(result["status"], "available")
        self.assertFalse(
            result["combat_simulation_inputs"]["completeness"][
                "monte_carlo_ready"
            ]
        )
        cached_snapshot = driver.take_snapshot()
        self.assertEqual(
            cached_snapshot["combat_simulation_inputs_target_province_id"], 5
        )
        self.assertEqual(
            cached_snapshot[
                "combat_simulation_inputs_attacker_entry_province_id"
            ],
            2,
        )
        self.assertEqual(
            cached_snapshot["combat_simulation_inputs_attacker_army_ids"],
            [16_777_217],
        )
        self.assertEqual(
            cached_snapshot["combat_simulation_inputs_defender_army_ids"],
            [16_777_218],
        )
        self.assertEqual(
            cached_snapshot["combat_simulation_inputs_status"], "available"
        )

        cached = copy.deepcopy(driver._combat_simulation_inputs_query)
        assert isinstance(cached, dict)
        cases = {
            "native_revision": 999,
            "snapshot_id": "native:other",
            "revision": 999,
            "connection_generation": 999,
            "episode_run_id": "native-other",
            "target_province_id": 6,
            "attacker_entry_province_id": 3,
            "attacker_army_ids": [16_777_218],
            "defender_army_ids": [16_777_217],
        }
        for key, changed in cases.items():
            with self.subTest(binding=key):
                candidate = copy.deepcopy(cached)
                candidate["cache_binding"][key] = changed
                driver._combat_simulation_inputs_query = candidate
                self.assertIsNone(
                    driver.take_snapshot()["combat_simulation_inputs"]
                )

    def test_revision_pause_and_encounter_scope_fail_before_native_wire(self) -> None:
        driver, endpoint = _native_driver()
        _answer_with(endpoint, _fixture_result)
        revision = int(driver.take_snapshot()["revision"])
        execute_count = lambda: sum(
            frame.get("type") == "execute_step" for frame in endpoint.frames
        )

        before = execute_count()
        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(STEP, expected_revision=revision + 1)
        self.assertEqual(execute_count(), before)

        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(
                "query-combat-simulation-inputs-v2-5-2-a-1-16777217-d-1-99",
                expected_revision=revision,
            )
        self.assertEqual(execute_count(), before)

        endpoint.publish(_snapshot(6, paused=False))
        current_revision = int(driver.take_snapshot()["revision"])
        with self.assertRaises(BridgeUnavailableError):
            driver.execute_step(STEP, expected_revision=current_revision)
        self.assertEqual(execute_count(), before)

    def test_malformed_native_schema_scale_and_status_are_rejected(self) -> None:
        def extra_key() -> dict[str, object]:
            result = _fixture_result()
            result["combat_simulation_inputs"]["unexpected"] = True
            return result

        def wrong_scale() -> dict[str, object]:
            result = _fixture_result()
            result["combat_simulation_inputs"]["armies"][0]["owner"][
                "scale"
            ] = 1
            return result

        def null_available_field() -> dict[str, object]:
            result = _fixture_result()
            result["combat_simulation_inputs"]["armies"][0]["regiments"][0][
                "effective_stats"
            ]["damage_raw"] = None
            return result

        def status_disagreement() -> dict[str, object]:
            result = _fixture_result()
            result["status"] = "partial"
            return result

        for name, mutation in {
            "extra-key": extra_key,
            "wrong-scale": wrong_scale,
            "available-null": null_available_field,
            "status-disagreement": status_disagreement,
        }.items():
            with self.subTest(case=name):
                driver, endpoint = _native_driver()
                _answer_with(endpoint, mutation)
                revision = int(driver.take_snapshot()["revision"])
                with self.assertRaises(BridgeUnavailableError):
                    driver.execute_step(STEP, expected_revision=revision)


class _McpCombatDriver:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.result = copy.deepcopy(result or _fixture_result())

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "combat-fixture",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": [
                QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY
            ],
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "snapshot_id": "combat-fixture:4",
            "revision": 4,
            "native_revision": 5,
            "source": "named-pipe",
            "backend_id": "combat-fixture",
            "paused": True,
            "date_raw": 53_171_400,
            "active_wars": [_war()],
            "player_armies": [
                _army(16_777_217, controllable=True, province_id=2)
            ],
            "diagnostics": {
                "hello": {
                    "game_version": "1.19.0.6",
                    "executable_sha256": "a" * 64,
                }
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step != STEP or expected_revision != 4:
            raise AssertionError(
                "MCP did not preserve hypothetical-contact revision"
            )
        return {**copy.deepcopy(self.result), "backend_id": "combat-fixture"}

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("combat query must not wait or advance time")


class CombatSimulationInputsServiceTests(unittest.TestCase):
    def test_hybrid_fallback_rebinds_native_query_to_paired_revision(self) -> None:
        native, endpoint = _native_driver()
        _answer_with(endpoint, _fixture_result)
        fallback = _McpCombatDriver()
        driver = ConfiguredHybridFallbackDriver(
            native,
            fallback,
            fallback,
        )
        service = GameplayBridgeService(driver)
        revision = int(driver.take_snapshot()["revision"])

        result = service.query_combat_simulation_inputs(
            5,
            2,
            [16_777_217],
            [16_777_218],
            expected_revision=revision,
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(result["queried_revision"], revision)
        self.assertTrue(result["input_observation_ready"])

    def test_partial_observation_is_not_upgraded_to_simulation_ready(self) -> None:
        service = GameplayBridgeService(
            _McpCombatDriver(_partial_fixture_result())
        )

        result = service.query_combat_simulation_inputs(
            5,
            2,
            [16_777_217],
            [16_777_218],
            expected_revision=4,
        )

        self.assertEqual(result["status"], "partial")
        self.assertFalse(result["input_observation_ready"])
        self.assertFalse(result["monte_carlo_ready"])
        self.assertEqual(
            result["missing_required_domains"][0], "counter_resolutions"
        )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CombatSimulationInputsMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_calls_hypothetical_contact_tool(self) -> None:
        from mcp import Client

        server = create_server(_McpCombatDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            self.assertIn(
                "ck3_query_combat_simulation_inputs",
                {tool.name for tool in listed.tools},
            )
            result = await client.call_tool(
                "ck3_query_combat_simulation_inputs",
                {
                    "target_province_id": 5,
                    "attacker_entry_province_id": 2,
                    "attacker_army_ids": [16_777_217],
                    "defender_army_ids": [16_777_218],
                    "expected_revision": 4,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertTrue(payload["input_observation_ready"])
        self.assertFalse(payload["monte_carlo_ready"])
        self.assertEqual(
            payload["missing_required_domains"],
            [
                "damage_to_casualty_allocation",
                "pursuit_transition",
                "battle_end_and_retreat_transition",
                "phase_event_rng_and_effects",
            ],
        )
        self.assertNotIn("win_probability", payload)


if __name__ == "__main__":
    unittest.main()
