from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_entry_contract import (
    EXECUTABLE_SHA256,
    QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
)
from xar_autoplayer.strategy import choose_one_life_turn


STEP = "query-war-entry-assessments-v1-1-808"
OTHER_STEP = "query-war-entry-assessments-v1-1-42"


def _declaration(target: int) -> dict[str, object]:
    return {
        "declaration_id": f"{target}-17-0",
        "target_character_id": target,
        "casus_belli_index": 17,
        "casus_belli_key": "county_conquest_cb",
        "configuration_index": 0,
        "claimant_character_id": -1,
        "target_title_ids": [91],
        "source": "native",
    }


def _row(target: int, *, effective_target: int | None = None) -> dict[str, object]:
    return {
        "target_character_id": target,
        "effective_target_character_id": effective_target or target,
        "distance_raw": 2_500_000,
        "actor_power_base_raw": 55_223,
        "actor_network_contribution_raw": 44_777,
        "actor_power_total_raw": 100_000,
        "target_power_base_raw": 58_468,
        "target_network_contribution_raw": 21_532,
        "target_pre_adjustment_total_raw": 80_000,
        "target_adjustment_delta_raw": 5_000,
        "target_power_total_raw": 85_000,
        "actual_power_ratio_raw": 85_000,
        "target_ai_context_actor_entry_raw": 0,
        "actor_ai_context_target_entry_raw": 1,
        "native_flags_raw": 3,
    }


def _payload(
    targets: list[int] | None = None, *, snapshot_revision: int = 5
) -> dict[str, object]:
    selected = targets or [808]
    return {
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": snapshot_revision,
        "date_raw": 53_171_400,
        "actor_character_id": 29_829,
        "requested_target_character_ids": list(selected),
        "assessments": [_row(target) for target in selected],
        "readiness": {
            "actor_identity_ready": True,
            "targets_declarable_ready": True,
            "effective_targets_ready": True,
            "ai_context_ready": True,
            "native_output_ready": True,
            "network_decomposition_ready": True,
            "same_frame_ready": True,
            "ready": True,
        },
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": EXECUTABLE_SHA256,
            "assessment_rva": "0x1878A00",
            "network_collector_rva": "0x1879850",
            "power_leaf": "CCharacter+0x1B8->+0x308",
            "fixed_point_scale": 100_000,
        },
    }


def _result(*, targets: list[int] | None = None) -> dict[str, object]:
    selected = targets or [808]
    return {
        "step": (
            "query-war-entry-assessments-v1-"
            + str(len(selected))
            + "-"
            + "-".join(str(target) for target in selected)
        ),
        "accepted": True,
        "status": "available",
        "query_sequence": 41,
        "war_entry_assessments": _payload(selected),
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
            "active_wars": [],
            "player_armies": [],
        },
    }


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_war_entry_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

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
            "pid": 4545,
            "session_generation": 0,
            "game_version": "1.19.0.6",
            "executable_sha256": EXECUTABLE_SHA256,
            "capabilities": [
                "game.state.snapshot",
                QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot())
    driver._declarable_wars = [_declaration(808), _declaration(42)]
    return driver, endpoint


def _answer(endpoint: _FakeEndpoint) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        endpoint.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": _result(),
            }
        )

    endpoint.send_hook = answer


class WarEntryNativeDriverTests(unittest.TestCase):
    def test_paused_query_is_scope_checked_and_cached_on_exact_frame(self) -> None:
        driver, endpoint = _native_driver()
        _answer(endpoint)
        capabilities = driver.capabilities()
        self.assertTrue(capabilities["war_entry_assessments_query_supported"])
        self.assertIn(STEP, capabilities["action_steps"])
        self.assertIn(OTHER_STEP, capabilities["action_steps"])
        self.assertNotIn(
            "query-war-entry-assessments-v1-2-808-42",
            capabilities["action_steps"],
        )
        self.assertNotIn(
            "query-war-entry-assessments-v1-N",
            capabilities["action_steps"],
        )

        revision = int(driver.take_snapshot()["revision"])
        result = driver.execute_step(STEP, expected_revision=revision)

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["war_entry_assessments"]["assessments"][0][
                "actual_power_ratio_raw"
            ],
            85_000,
        )
        cached = driver.take_snapshot()
        self.assertEqual(cached["war_entry_assessments_status"], "available")
        self.assertEqual(
            cached["war_entry_assessments"]["requested_target_character_ids"],
            [808],
        )

        frozen = copy.deepcopy(driver._war_entry_assessments_query)
        assert isinstance(frozen, dict)
        for field, replacement in {
            "native_revision": 99,
            "snapshot_id": "native:99",
            "revision": 99,
            "connection_generation": 99,
            "episode_run_id": "other",
            "target_character_ids": [42],
        }.items():
            with self.subTest(field=field):
                candidate = copy.deepcopy(frozen)
                candidate["cache_binding"][field] = replacement
                driver._war_entry_assessments_query = candidate
                self.assertIsNone(driver.take_snapshot()["war_entry_assessments"])
        driver._war_entry_assessments_query = frozen
        endpoint.publish(_semantic_snapshot(6))
        self.assertIsNone(driver.take_snapshot()["war_entry_assessments"])

    def test_out_of_scope_target_is_rejected_before_pipe_send(self) -> None:
        driver, endpoint = _native_driver()
        before = len(endpoint.frames)
        with self.assertRaisesRegex(BridgeUnavailableError, "outside current"):
            driver.execute_step(
                "query-war-entry-assessments-v1-1-43",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )
        self.assertEqual(len(endpoint.frames), before)

    def test_multi_target_literal_is_rejected_before_pipe_send(self) -> None:
        driver, endpoint = _native_driver()
        before = len(endpoint.frames)
        with self.assertRaisesRegex(
            UnsupportedStepError, "non-production-bounded"
        ):
            driver.execute_step(
                "query-war-entry-assessments-v1-2-808-42",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )
        self.assertEqual(len(endpoint.frames), before)

    def test_result_target_or_native_revision_drift_is_rejected(self) -> None:
        for mutation in ("target", "revision"):
            driver, endpoint = _native_driver()

            def answer(frame: dict[str, object], *, mutation=mutation) -> None:
                if frame.get("type") != "execute_step":
                    return
                result = _result()
                if mutation == "target":
                    result["war_entry_assessments"]["assessments"][0][
                        "target_character_id"
                    ] = 42
                else:
                    result["war_entry_assessments"]["snapshot_revision"] = 6
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
            with self.subTest(mutation=mutation):
                with self.assertRaises(BridgeUnavailableError):
                    driver.execute_step(
                        STEP,
                        expected_revision=int(driver.take_snapshot()["revision"]),
                    )


class _ServiceDriver:
    def __init__(self, *, advertise: bool = True) -> None:
        self.advertise = advertise
        self.execute_count = 0
        self.snapshot_count = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "war-entry-fixture",
            "source": "fixture",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [STEP, OTHER_STEP],
            "bridge_capabilities": (
                [QUERY_WAR_ENTRY_ASSESSMENTS_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.snapshot_count += 1
        return {
            "format_version": 1,
            "snapshot_id": "war-entry:17",
            "revision": 17,
            "native_revision": 5,
            "date_raw": 53_171_400,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 29_829, "alive": True},
            "declarable_wars": [_declaration(808), _declaration(42)],
            "episode_run_id": "native-29829-test",
            "backend_id": "war-entry-fixture",
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.execute_count += 1
        if step != STEP or expected_revision != 17:
            raise AssertionError("service changed the target order or revision")
        return {**_result(), "backend_id": "war-entry-fixture"}

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("war-entry assessment must not advance time")


class WarEntryServiceAndStrategyTests(unittest.TestCase):
    def test_service_requires_native_capability_and_same_revision(self) -> None:
        unavailable = _ServiceDriver(advertise=False)
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(unavailable).query_war_entry_assessments(
                [808], expected_revision=17
            )
        self.assertEqual(unavailable.execute_count, 0)

        result = GameplayBridgeService(
            _ServiceDriver()
        ).query_war_entry_assessments([808], expected_revision=17)
        self.assertEqual(result["queried_revision"], 17)
        self.assertEqual(result["queried_native_revision"], 5)
        self.assertEqual(result["target_character_ids"], [808])
        self.assertNotIn("win_probability", result)

    def test_service_rejects_multiple_targets_before_snapshot_or_driver(self) -> None:
        driver = _ServiceDriver()
        with self.assertRaisesRegex(ValueError, "exactly 1"):
            GameplayBridgeService(driver).query_war_entry_assessments(
                [808, 42], expected_revision=17
            )
        self.assertEqual(driver.snapshot_count, 0)
        self.assertEqual(driver.execute_count, 0)

    def test_strategy_queries_power_before_life_advance_but_never_declares(self) -> None:
        declaration = _declaration(808)
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [declaration],
            },
            action_steps={
                "query-declarable-wars",
                "query-war-entry-assessments-v1-1-808",
                "declare-war-808-17-0",
                "life-advance",
            },
        )
        self.assertEqual(plan["phase"], "native_war_entry_assessment")
        self.assertEqual(
            plan["selected_step"],
            "query-war-entry-assessments-v1-1-808",
        )

        snapshot = {
            "active_wars": [],
            "player_armies": [],
            "declarable_wars": [declaration],
            "war_entry_assessments": _payload([808]),
        }
        blocked = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot=snapshot,
            action_steps={
                "query-war-entry-assessments-v1-1-808",
                "declare-war-808-17-0",
                "life-advance",
            },
        )
        self.assertEqual(blocked["phase"], "native_war_entry_evidence_required")
        self.assertIsNone(blocked["selected_step"])
        self.assertEqual(blocked["war_entry_assessment"], _row(808))
        eu = blocked["war_entry_expected_utility"]
        self.assertEqual(eu["status"], "native_power_component_ready")
        self.assertTrue(eu["native_power_component_ready"])
        self.assertEqual(
            eu["native_power_component"][
                "conservative_self_power_margin_raw"
            ],
            55_223 - 85_000,
        )
        self.assertEqual(
            eu["native_power_component"]["actual_power_ratio_raw"],
            85_000,
        )
        self.assertIsNone(eu["eu_lower_raw"])
        self.assertIn("combat_forecast", eu["missing_components"])
        self.assertFalse(eu["automatic_declaration_enabled"])

    def test_strategy_uses_same_frame_power_and_network_risk_to_rank_targets(self) -> None:
        risky = _payload([42])
        safe = _payload([808])
        safe_row = safe["assessments"][0]
        safe_row.update(
            {
                "actor_power_base_raw": 90_000,
                "actor_network_contribution_raw": 10_000,
                "actor_power_total_raw": 100_000,
                "target_power_base_raw": 45_000,
                "target_network_contribution_raw": 5_000,
                "target_pre_adjustment_total_raw": 50_000,
                "target_adjustment_delta_raw": 10_000,
                "target_power_total_raw": 60_000,
                "actual_power_ratio_raw": 60_000,
            }
        )
        snapshot = {
            "active_wars": [],
            "player_armies": [],
            "declarable_wars": [_declaration(42), _declaration(808)],
            "war_entry_assessments": safe,
            "native_revision": 5,
            "date_raw": 53_171_400,
            "played_character": {"character_id": 29_829, "alive": True},
        }
        commands = [
            {"index": 1, "command": "save-checkpoint", "ok": True},
            {
                "index": 2,
                "command": OTHER_STEP,
                "ok": True,
                "result": {"war_entry_assessments": risky},
            },
        ]
        plan = choose_one_life_turn(
            commands,
            snapshot=snapshot,
            action_steps={
                STEP,
                OTHER_STEP,
                "declare-war-42-17-0",
                "declare-war-808-17-0",
            },
        )

        # The old CB/title/target-id heuristic would choose 42.  Exact native
        # power instead makes the self-sufficient 808 target the lower-risk
        # diagnostic candidate, while declaration remains disabled.
        self.assertEqual(plan["declaration"]["target_character_id"], 808)
        self.assertEqual(plan["war_entry_assessment"], safe_row)
        component = plan["war_entry_expected_utility"][
            "native_power_component"
        ]
        self.assertEqual(component["conservative_self_power_margin_raw"], 30_000)
        self.assertEqual(component["actor_network_dependency_raw"], 10_000)
        self.assertEqual(component["target_network_support_raw"], 5_000)
        self.assertIsNone(plan["selected_step"])

    def test_strategy_queries_an_alternative_after_native_self_power_deficit(self) -> None:
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [_declaration(42), _declaration(808)],
                "war_entry_assessments": _payload([42]),
                "native_revision": 5,
                "date_raw": 53_171_400,
                "played_character": {
                    "character_id": 29_829,
                    "alive": True,
                },
            },
            action_steps={STEP, OTHER_STEP},
        )

        self.assertEqual(
            plan["phase"], "native_war_entry_assessment_alternative"
        )
        self.assertEqual(plan["selected_step"], STEP)
        self.assertEqual(
            plan["rejected_power_declaration"]["target_character_id"], 42
        )
        self.assertEqual(
            plan["rejected_war_entry_expected_utility"][
                "native_power_component"
            ]["conservative_self_power_margin_raw"],
            55_223 - 85_000,
        )

    def test_strategy_does_not_rank_with_a_stale_history_assessment(self) -> None:
        stale = _payload([42], snapshot_revision=4)
        current = _payload([808], snapshot_revision=5)
        plan = choose_one_life_turn(
            [
                {"index": 1, "command": "save-checkpoint", "ok": True},
                {
                    "index": 2,
                    "command": OTHER_STEP,
                    "ok": True,
                    "result": {"war_entry_assessments": stale},
                },
            ],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [_declaration(42), _declaration(808)],
                "war_entry_assessments": current,
                "native_revision": 5,
                "date_raw": 53_171_400,
                "played_character": {
                    "character_id": 29_829,
                    "alive": True,
                },
            },
            action_steps={STEP},
        )

        self.assertEqual(plan["declaration"]["target_character_id"], 808)
        self.assertEqual(plan["war_entry_assessment"], _row(808))


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class WarEntryMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_war_entry_tool(self) -> None:
        from mcp import Client

        driver = _ServiceDriver()
        server = create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_war_entry_assessments", names)
            result = await client.call_tool(
                "ck3_query_war_entry_assessments",
                {
                    "target_character_ids": [808],
                    "expected_revision": 17,
                },
            )
            rejected = await client.call_tool(
                "ck3_query_war_entry_assessments",
                {
                    "target_character_ids": [808, 42],
                    "expected_revision": 17,
                },
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["target_character_ids"], [808])
        self.assertNotIn("win_probability", payload)
        self.assertTrue(rejected.is_error)
        self.assertEqual(driver.execute_count, 1)
        self.assertEqual(driver.snapshot_count, 2)


if __name__ == "__main__":
    unittest.main()
