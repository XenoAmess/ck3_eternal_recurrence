from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
)
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


STEP = (
    "query-combat-simulation-inputs-v3-2596-2597-a-2-357-33554657-"
    "d-1-83886341"
)


def _builder_module():
    path = Path(__file__).with_name(
        "test_combat_phase_inputs_v3_production_contract.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_xar_v3_production_bridge_fixture", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture_result(*, available: bool = True) -> dict[str, object]:
    payload, _scope = _builder_module()._production_payload()
    if not available:
        payload["phase_event_inputs"].update(
            status="unavailable",
            raw=None,
            advantage_model=None,
            unavailable_reason="native_phase_identity_revalidation_failed",
        )
    return {
        "step": STEP,
        "accepted": True,
        "status": "available" if available else "unavailable",
        "query_sequence": 41,
        "combat_simulation_inputs": payload,
    }


def _army(army_id: int, *, controllable: bool) -> dict[str, object]:
    return {
        "army_id": army_id,
        "owner_character_id": 29_829 if controllable else 36_108,
        "soldiers": 1_000,
        "current_province_id": 2596 if controllable else 2597,
        "move_target_province_id": None,
        "controllable": controllable,
    }


def _war() -> dict[str, object]:
    return {
        "war_id": 16_777_290,
        "player_side": "defender",
        "primary_opponent_character_id": 36_108,
        "player_is_primary_war_leader": True,
        "enemy_primary_default_raise_province_id": None,
        "player_relative_war_score": 0,
        "allied_armies": [_army(83_886_341, controllable=True)],
        "enemy_armies": [
            _army(357, controllable=False),
            _army(33_554_657, controllable=False),
        ],
        "war_objective_province_ids": [],
        "objective_province_states": [],
        "targeted_title_ids": [],
    }


def _semantic_snapshot(revision: int = 5) -> dict[str, object]:
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
            "paused": True,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 29_829, "alive": True},
            "one_life_settlement": None,
            "active_wars": [_war()],
            "player_armies": [_army(83_886_341, controllable=True)],
        },
    }


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_combat_phase_v3_fixture"
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


def _native_driver() -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 4343,
            "session_generation": 0,
            "game_version": "1.19.0.6",
            "executable_sha256": "a" * 64,
            "capabilities": [
                "game.state.snapshot",
                QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    return driver, endpoint


def _answer_with(endpoint: _FakeEndpoint, result_factory) -> None:
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


class CombatPhaseInputsV3NativeDriverTests(unittest.TestCase):
    def test_atomic_query_is_normalized_and_cached_only_on_same_frame(self) -> None:
        driver, endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities["combat_simulation_inputs_v3_query_supported"]
        )
        self.assertNotIn(
            QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
            capabilities["action_steps"],
        )
        self.assertNotIn(
            "query-combat-simulation-inputs-v3-N",
            capabilities["action_steps"],
        )
        _answer_with(endpoint, _fixture_result)
        revision = int(driver.take_snapshot()["revision"])

        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(result["status"], "available")
        self.assertTrue(
            result["combat_simulation_inputs"]["completeness"][
                "phase_event_inputs_ready"
            ]
        )
        cached = driver.take_snapshot()
        self.assertEqual(cached["combat_simulation_inputs_v3_status"], "available")
        self.assertEqual(
            cached["combat_simulation_inputs_v3_attacker_army_ids"],
            [357, 33_554_657],
        )
        self.assertIsNone(cached["combat_simulation_inputs"])

        frozen_cache = copy.deepcopy(driver._combat_simulation_inputs_v3_query)
        assert isinstance(frozen_cache, dict)
        for key, replacement in {
            "native_revision": 999,
            "snapshot_id": "native:other",
            "revision": 999,
            "connection_generation": 999,
            "episode_run_id": "native-other",
            "target_province_id": 2598,
            "attacker_entry_province_id": 2596,
            "attacker_army_ids": [357],
            "defender_army_ids": [33_554_657, 83_886_341],
        }.items():
            with self.subTest(cache_binding=key):
                candidate = copy.deepcopy(frozen_cache)
                candidate["cache_binding"][key] = replacement
                driver._combat_simulation_inputs_v3_query = candidate
                self.assertIsNone(
                    driver.take_snapshot()["combat_simulation_inputs_v3"]
                )

        tampered = copy.deepcopy(frozen_cache)
        tampered["combat_simulation_inputs"]["phase_event_inputs"][
            "offline_admission"
        ]["ready"] = False
        driver._combat_simulation_inputs_v3_query = tampered
        self.assertIsNone(driver.take_snapshot()["combat_simulation_inputs_v3"])

        driver._combat_simulation_inputs_v3_query = frozen_cache

        endpoint.publish(_semantic_snapshot(6))
        self.assertIsNone(driver.take_snapshot()["combat_simulation_inputs_v3"])

    def test_malformed_or_status_disagreeing_payload_is_rejected(self) -> None:
        def malformed() -> dict[str, object]:
            result = _fixture_result()
            del result["combat_simulation_inputs"]["phase_event_inputs"][
                "raw"
            ]["characters"][0]["traits_or_groups"]["ambitious"]
            return result

        def disagreement() -> dict[str, object]:
            result = _fixture_result()
            result["status"] = "unavailable"
            return result

        for factory in (malformed, disagreement):
            with self.subTest(factory=factory.__name__):
                driver, endpoint = _native_driver()
                _answer_with(endpoint, factory)
                with self.assertRaises(BridgeUnavailableError):
                    driver.execute_step(STEP, expected_revision=5)


class _McpV3Driver:
    def __init__(
        self,
        result: dict[str, object] | None = None,
        *,
        advertise: bool = True,
    ) -> None:
        self.result = copy.deepcopy(result or _fixture_result())
        self.advertise = advertise
        self.execute_count = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "combat-phase-v3-fixture",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": (
                [QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        state = _semantic_snapshot()["state"]
        return {
            "format_version": 1,
            "snapshot_id": "combat-phase-v3-fixture:4",
            "revision": 4,
            "native_revision": 5,
            "source": "named-pipe",
            "backend_id": "combat-phase-v3-fixture",
            **copy.deepcopy(state),
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
        self.execute_count += 1
        if step != STEP or expected_revision != 4:
            raise AssertionError("MCP changed the v3 request or paused revision")
        return {**copy.deepcopy(self.result), "backend_id": "combat-phase-v3-fixture"}

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("production combat phase query must not advance time")


class CombatPhaseInputsV3ServiceTests(unittest.TestCase):
    def test_service_requires_capability_and_preserves_readiness_boundaries(self) -> None:
        unadvertised = _McpV3Driver(advertise=False)
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(unadvertised).query_combat_simulation_inputs_v3(
                2596,
                2597,
                [357, 33_554_657],
                [83_886_341],
                expected_revision=4,
            )
        self.assertEqual(unadvertised.execute_count, 0)

        result = GameplayBridgeService(_McpV3Driver()).query_combat_simulation_inputs_v3(
            2596,
            2597,
            [357, 33_554_657],
            [83_886_341],
            expected_revision=4,
        )
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["phase_event_inputs_ready"])
        self.assertTrue(result["offline_exact_state_refs_ready"])
        self.assertFalse(result["monte_carlo_ready"])
        self.assertFalse(result["transition_fidelity_gate"])
        self.assertFalse(result["planner_usable"])
        self.assertFalse(result["active_attack_allowed"])
        self.assertEqual(result["missing_observation_domains"], [])
        self.assertEqual(result["loaded_playset_proof"]["status"], "unavailable")
        self.assertFalse(
            result["phase_event_manifest_fidelity"][
                "loaded_playset_verified"
            ]
        )
        self.assertFalse(
            result["phase_event_manifest_fidelity"][
                "ast_evaluator_ready"
            ]
        )
        self.assertEqual(
            result["missing_fidelity_gates"],
            [
                "loaded_playset_verified",
                "ast_evaluator_ready",
                "original_trace_ready",
            ],
        )
        self.assertIn(
            "phase_event_rng_and_effects",
            result["missing_required_domains"],
        )

    def test_episode_bound_playset_proof_closes_only_its_own_fidelity_gate(
        self,
    ) -> None:
        service = GameplayBridgeService(_McpV3Driver())
        verified = {
            "status": "verified",
            "claims": {"loaded_playset_verified": True},
            "proof_sha256": "A" * 64,
        }
        with mock.patch.object(
            service,
            "_loaded_playset_proof_for_snapshot",
            return_value=verified,
        ):
            result = service.query_combat_simulation_inputs_v3(
                2596,
                2597,
                [357, 33_554_657],
                [83_886_341],
                expected_revision=4,
            )

        self.assertEqual(result["loaded_playset_proof"], verified)
        self.assertTrue(
            result["phase_event_manifest_fidelity"][
                "loaded_playset_verified"
            ]
        )
        self.assertEqual(
            result["missing_fidelity_gates"],
            ["ast_evaluator_ready", "original_trace_ready"],
        )
        self.assertFalse(
            result["phase_event_manifest_fidelity"]["ast_evaluator_ready"]
        )
        self.assertFalse(result["transition_fidelity_gate"])
        self.assertFalse(result["planner_usable"])
        self.assertFalse(result["active_attack_allowed"])
        self.assertFalse(
            result["combat_simulation_inputs"]["completeness"]
            ["phase_event_manifest_fidelity"]["loaded_playset_verified"]
        )

    def test_unavailable_slice_is_never_upgraded_to_ready(self) -> None:
        service = GameplayBridgeService(
            _McpV3Driver(_fixture_result(available=False))
        )
        result = service.query_combat_simulation_inputs_v3(
            2596,
            2597,
            [357, 33_554_657],
            [83_886_341],
            expected_revision=4,
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["phase_event_inputs_ready"])
        self.assertFalse(result["offline_exact_state_refs_ready"])
        self.assertFalse(result["monte_carlo_ready"])
        self.assertEqual(
            result["missing_observation_domains"], ["phase_event_inputs"]
        )
        self.assertIn(
            "phase_event_rng_and_effects",
            result["missing_required_domains"],
        )

    def test_hybrid_rebinds_native_result_to_public_same_frame(self) -> None:
        native, endpoint = _native_driver()
        _answer_with(endpoint, _fixture_result)
        fallback = _McpV3Driver()
        driver = ConfiguredHybridFallbackDriver(native, fallback, fallback)
        revision = int(driver.take_snapshot()["revision"])

        result = GameplayBridgeService(driver).query_combat_simulation_inputs_v3(
            2596,
            2597,
            [357, 33_554_657],
            [83_886_341],
            expected_revision=revision,
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(result["queried_revision"], revision)
        self.assertTrue(result["phase_event_inputs_ready"])
        self.assertEqual(fallback.execute_count, 0)

    def test_hybrid_never_falls_back_a_v3_query_when_native_cap_is_absent(
        self,
    ) -> None:
        native, endpoint = _native_driver()
        endpoint.publish(
            {
                "type": "hello",
                "protocol_version": 1,
                "bridge_version": "0.1.0",
                "pid": 4343,
                "session_generation": 0,
                "game_version": "1.19.0.6",
                "executable_sha256": "a" * 64,
                "capabilities": ["game.state.snapshot"],
            }
        )
        endpoint.publish(_semantic_snapshot(revision=5))
        data_fallback = _McpV3Driver()
        visual_fallback = _McpV3Driver()
        driver = ConfiguredHybridFallbackDriver(
            native, data_fallback, visual_fallback
        )

        with self.assertRaises(UnsupportedStepError):
            driver.execute_step(
                STEP, expected_revision=int(driver.take_snapshot()["revision"])
            )

        self.assertEqual(data_fallback.execute_count, 0)
        self.assertEqual(visual_fallback.execute_count, 0)


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CombatPhaseInputsV3McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_production_v3_tool(self) -> None:
        from mcp import Client

        server = create_server(_McpV3Driver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_combat_simulation_inputs_v3", names)
            self.assertNotIn(
                "ck3_query_combat_simulation_inputs_v3_test_only", names
            )
            result = await client.call_tool(
                "ck3_query_combat_simulation_inputs_v3",
                {
                    "target_province_id": 2596,
                    "attacker_entry_province_id": 2597,
                    "attacker_army_ids": [357, 33_554_657],
                    "defender_army_ids": [83_886_341],
                    "expected_revision": 4,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertTrue(payload["phase_event_inputs_ready"])
        self.assertFalse(payload["monte_carlo_ready"])
        self.assertFalse(payload["transition_fidelity_gate"])
        self.assertFalse(payload["active_attack_allowed"])
        self.assertNotIn("win_probability", payload)


if __name__ == "__main__":
    unittest.main()
