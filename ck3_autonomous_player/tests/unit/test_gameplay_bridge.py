from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeGameplayStepExecutor,
    CallbackGameplayDriver,
    DevelopmentReportDriver,
    HybridGameplayDriver,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


def _snapshot(revision: int = 0, history: list[dict[str, object]] | None = None):
    return {
        "format_version": 1,
        "snapshot_id": f"session:{revision}",
        "revision": revision,
        "source": "fixture",
        "history": history or [],
        "phase": "map_hud",
    }


def _army(
    army_id: int,
    *,
    soldiers: int | None,
    province_id: int,
    controllable: bool,
    move_target_province_id: int | None = None,
) -> dict[str, object]:
    return {
        "army_id": army_id,
        "owner_character_id": 707 if controllable else 808,
        "soldiers": soldiers,
        "current_province_id": province_id,
        "move_target_province_id": move_target_province_id,
        "controllable": controllable,
    }


def _war(
    *,
    allied_armies: list[dict[str, object]],
    enemy_armies: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "war_id": 88,
        "player_side": "attacker",
        "player_relative_war_score": 17,
        "allied_armies": allied_armies,
        "enemy_armies": enemy_armies,
    }


class GameplayBridgeTests(unittest.TestCase):
    def test_hybrid_routes_supported_steps_to_fast_backend(self) -> None:
        calls: list[tuple[str, str]] = []
        fast = CallbackGameplayDriver(
            backend_id="native",
            snapshot=lambda: _snapshot(3),
            execute=lambda step, revision: calls.append(("fast", step))
            or {"step": step, "expected_revision": revision},
            action_steps=("life-advance",),
            source="injected-dll",
            latency="realtime",
        )
        vision = CallbackGameplayDriver(
            backend_id="vision",
            snapshot=lambda: _snapshot(3),
            execute=lambda step, revision: calls.append(("vision", step))
            or {"step": step, "expected_revision": revision},
            action_steps=("life-advance", "marriage-review"),
            source="ocr-keyboard-mouse",
        )
        hybrid = HybridGameplayDriver(fast, vision)
        revision = int(hybrid.take_snapshot()["revision"])

        self.assertEqual(
            hybrid.execute_step(
                "life-advance", expected_revision=revision
            )["backend_id"],
            "native",
        )
        self.assertEqual(
            hybrid.execute_step(
                "marriage-review", expected_revision=revision
            )["backend_id"],
            "vision",
        )
        self.assertEqual(calls, [("fast", "life-advance"), ("vision", "marriage-review")])

    def test_hybrid_does_not_replay_a_failed_supported_fast_action(self) -> None:
        vision_calls: list[str] = []

        def fail(_step: str, _revision: int | None):
            raise RuntimeError("native action failed after dispatch")

        fast = CallbackGameplayDriver(
            backend_id="native",
            snapshot=lambda: _snapshot(),
            execute=fail,
            action_steps=("life-advance",),
        )
        vision = CallbackGameplayDriver(
            backend_id="vision",
            snapshot=lambda: _snapshot(),
            execute=lambda step, _revision: vision_calls.append(step) or {},
            action_steps=("life-advance",),
        )

        with self.assertRaisesRegex(RuntimeError, "after dispatch"):
            HybridGameplayDriver(fast, vision).execute_step("life-advance")
        self.assertEqual(vision_calls, [])

    def test_hybrid_merges_fast_state_with_baseline_history_and_revisions(self) -> None:
        calls: list[tuple[str, int | None]] = []
        history = [
            {
                "command": "save-checkpoint",
                "ok": True,
                "result": {"final_screen": "map_hud"},
            }
        ]
        fast = CallbackGameplayDriver(
            backend_id="data-mod",
            snapshot=lambda: {
                **_snapshot(7, []),
                "phase": None,
                "total_days": 389_742,
            },
            execute=lambda step, revision: calls.append((step, revision)) or {},
            action_steps=(),
        )
        vision = CallbackGameplayDriver(
            backend_id="vision-session",
            snapshot=lambda: _snapshot(3, history),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("dynasty-review",),
        )
        hybrid = HybridGameplayDriver(fast, vision)

        snapshot = hybrid.take_snapshot()
        self.assertEqual(snapshot["backend_id"], "hybrid")
        self.assertEqual(snapshot["total_days"], 389_742)
        self.assertEqual(snapshot["history"], history)
        self.assertEqual(snapshot["phase"], "map_hud")
        self.assertEqual(snapshot["backend_revisions"], {"fast": 7, "baseline": 3})

        result = hybrid.execute_step(
            "dynasty-review", expected_revision=int(snapshot["revision"])
        )
        self.assertEqual(result["backend_id"], "vision-session")
        self.assertEqual(calls, [("dynasty-review", 3)])

    def test_service_reuses_existing_one_life_planner(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="fixture",
            snapshot=lambda: _snapshot(),
            execute=lambda _step, _revision: {},
            action_steps=(),
        )
        plan = GameplayBridgeService(driver).plan_turn()
        self.assertIsNone(plan["plan"]["selected_step"])
        self.assertEqual(plan["plan"]["required_step"], "save-checkpoint")
        self.assertEqual(plan["snapshot_id"], "session:0")

    def test_partial_native_backend_keeps_advancing_at_capability_gap(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(
                4,
                [
                    {
                        "command": "save-checkpoint",
                        "ok": True,
                        "result": {"checkpoint": {"status": "saved"}},
                    }
                ],
            ),
            execute=lambda _step, _revision: {},
            action_steps=("save-checkpoint", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["required_step"], "dynasty-review")
        self.assertEqual(plan["deferred_phase"], "current_life_family")

    def test_planner_prioritizes_pending_native_character_interaction(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(6),
                "pending_character_interaction": {
                    "instance_id": 72,
                    "sender_character_id": 501,
                    "auto_accept_notification": False,
                },
            },
            execute=lambda _step, _revision: {},
            action_steps=("accept-pending-character-interaction",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["selected_step"], "accept-pending-character-interaction"
        )
        self.assertEqual(plan["pending_character_interaction"]["instance_id"], 72)

    def test_native_war_planner_raises_when_no_player_army_exists(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(7),
                "active_wars": [_war(allied_armies=[], enemy_armies=[])],
                "player_armies": [],
            },
            execute=lambda _step, _revision: {},
            action_steps=("raise-troops-default",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_raise")
        self.assertEqual(plan["selected_step"], "raise-troops-default")

    def test_native_war_planner_chases_largest_visible_enemy(self) -> None:
        player = _army(
            11, soldiers=1_700, province_id=20, controllable=True
        )
        smaller = _army(
            21, soldiers=800, province_id=31, controllable=False
        )
        larger = _army(
            22, soldiers=2_400, province_id=32, controllable=False
        )
        step = "move-army-11-to-32"
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(8),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[smaller, larger],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(step,),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], step)
        self.assertEqual(plan["pursuit"]["target_army_id"], 22)
        self.assertEqual(plan["pursuit"]["target_province_id"], 32)

    def test_native_war_planner_uses_stable_enemy_when_soldiers_unknown(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy_22 = _army(
            22, soldiers=None, province_id=42, controllable=False
        )
        enemy_21 = _army(
            21, soldiers=None, province_id=41, controllable=False
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy_22, enemy_21],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "move-army-11-to-41")
        self.assertEqual(plan["pursuit"]["target_army_id"], 21)

    def test_native_war_planner_advances_after_unobservable_move_ack(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "war_action": {"status": "move_submitted"}
                },
            }
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9, history),
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[enemy])
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit_progress")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_native_war_planner_disbands_residual_postwar_army(self) -> None:
        player = _army(
            71, soldiers=1_100, province_id=50, controllable=True
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(10),
                "active_wars": [],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("disband-army-71",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_postwar_disband")
        self.assertEqual(plan["selected_step"], "disband-army-71")

    def test_typed_war_service_routes_exact_native_commands(self) -> None:
        player = _army(
            81, soldiers=1_300, province_id=50, controllable=True
        )
        enemy = _army(
            91, soldiers=1_900, province_id=60, controllable=False
        )
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(14),
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[enemy])
                ],
                "player_armies": [player],
            },
            execute=lambda step, revision: calls.append((step, revision))
            or {"status": "submitted"},
            action_steps=(
                "raise-troops-default",
                "move-army-81-to-60",
                "disband-army-81",
            ),
        )
        service = GameplayBridgeService(driver)

        state = service.war_state()
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["active_wars"][0]["war_id"], 88)
        service.raise_troops_default(expected_revision=14)
        service.move_army(81, 60, expected_revision=14)
        service.disband_army(81, expected_revision=14)

        self.assertEqual(
            calls,
            [
                ("raise-troops-default", 14),
                ("move-army-81-to-60", 14),
                ("disband-army-81", 14),
            ],
        )

    def test_service_auto_turn_plans_and_executes_one_supported_step(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(11),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("save-checkpoint",),
        )

        result = GameplayBridgeService(driver).auto_turn()

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["selected_step"], "save-checkpoint")
        self.assertEqual(calls, [("save-checkpoint", 11)])

    def test_service_auto_turn_ends_native_one_life_on_player_death(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(12),
                "played_character": {"character_id": 707, "alive": False},
            },
            execute=lambda step, revision: calls.append((step, revision))
            or {"terminal": True, "continue_as_heir_after_death": False},
            action_steps=("death-terminal",),
        )

        result = GameplayBridgeService(driver).auto_turn()

        self.assertEqual(result["selected_step"], "death-terminal")
        self.assertTrue(result["result"]["terminal"])
        self.assertEqual(calls, [("death-terminal", 12)])

    def test_bridge_driver_adapts_to_backend_neutral_runner(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="mcp",
            snapshot=lambda: _snapshot(12),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("life-advance",),
        )
        executor = BridgeGameplayStepExecutor(driver, expected_revision=lambda: 12)
        self.assertEqual(executor.execute_step("life-advance")["backend_id"], "mcp")
        self.assertEqual(calls, [("life-advance", 12)])

    def test_development_report_driver_reads_without_starting_ck3(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            run = state / "runs" / "20260823T000000Z-dev-session-fixture"
            run.mkdir(parents=True)
            (run / "report.json").write_text(
                json.dumps(
                    {
                        "run_id": run.name,
                        "process": {"pid": 123},
                        "finalized": False,
                        "commands": [
                            {
                                "command": "life-advance",
                                "ok": True,
                                "result": {"final_screen": "map_hud"},
                            },
                            {
                                "command": "auto-run 2",
                                "ok": True,
                                "result": {
                                    "final_screen": "unchanged",
                                    "turns": [
                                        {
                                            "command": "auto-turn",
                                            "ok": True,
                                            "result": {"final_screen": "map_running"},
                                        },
                                        {
                                            "command": "auto-turn",
                                            "ok": False,
                                            "error": "fixture stop",
                                        },
                                    ],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            driver = DevelopmentReportDriver(state)

            snapshot = driver.take_snapshot()
            self.assertEqual(snapshot["revision"], 2)
            self.assertEqual(snapshot["phase"], "map_running")
            self.assertEqual(snapshot["backend_id"], "vision-report")
            with self.assertRaises(UnsupportedStepError):
                driver.execute_step("life-advance")

    def test_native_mcp_driver_receives_isolated_profile_save_dir(self) -> None:
        from xar_autoplayer.bridge.mcp_server import load_driver

        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            with mock.patch(
                "xar_autoplayer.bridge.mcp_server.NativeHeadlessGameplayDriver"
            ) as factory:
                driver = load_driver(
                    "native-headless",
                    state_dir=state_dir,
                    pipe_name=r"\\.\pipe\xar_save_fixture",
                )

        self.assertIs(driver, factory.return_value)
        factory.assert_called_once_with(
            r"\\.\pipe\xar_save_fixture",
            state_dir=state_dir,
            save_dir=state_dir / "profile" / "save games",
        )

@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class GameplayMcpServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_mcp_client_lists_and_calls_ck3_tools(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server

        driver = CallbackGameplayDriver(
            backend_id="native-fixture",
            snapshot=lambda: {
                **_snapshot(4),
                "active_event": {"instance_id": 44, "option_count": 2},
                "pending_character_interaction": {
                    "instance_id": 52,
                    "sender_character_id": 901,
                    "auto_accept_notification": False,
                },
                "active_wars": [
                    _war(
                        allied_armies=[
                            _army(
                                81,
                                soldiers=1_300,
                                province_id=50,
                                controllable=True,
                            )
                        ],
                        enemy_armies=[
                            _army(
                                91,
                                soldiers=1_900,
                                province_id=60,
                                controllable=False,
                            )
                        ],
                    )
                ],
                "player_armies": [
                    _army(
                        81,
                        soldiers=1_300,
                        province_id=50,
                        controllable=True,
                    )
                ],
            },
            execute=lambda step, revision: {
                "step": step,
                "expected_revision": revision,
                **(
                    {
                        "checkpoint": {
                            "status": "saved",
                            "name": "xar_checkpoint.ck3",
                            "path": "C:/fixture/xar_checkpoint.ck3",
                            "size": 123,
                            "sha256": "a" * 64,
                            "date_raw": 53_171_424,
                        }
                    }
                    if step == "save-checkpoint"
                    else (
                        {
                            "checkpoint": {
                                "status": "restored",
                                "name": "xar_checkpoint.ck3",
                                "path": "C:/fixture/xar_checkpoint.ck3",
                                "size": 123,
                                "sha256": "a" * 64,
                                "date_raw": 53_171_424,
                            },
                            "restored_date": {"date_raw": 53_171_424},
                        }
                        if step == "restore-checkpoint"
                        else {}
                    )
                ),
            },
            action_steps=(
                "life-advance",
                "save-checkpoint",
                "restore-checkpoint",
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "raise-troops-default",
                "move-army-81-to-60",
                "disband-army-81",
                "select-event-option-1",
                "select-event-option-2",
            ),
            source="named-pipe",
            latency="realtime",
        )
        server = create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            self.assertEqual(
                {tool.name for tool in listed.tools},
                {
                    "ck3_get_capabilities",
                    "ck3_get_bridge_diagnostics",
                    "ck3_take_snapshot",
                    "ck3_plan_turn",
                    "ck3_auto_turn",
                    "ck3_execute_step",
                    "ck3_save_checkpoint",
                    "ck3_restore_checkpoint",
                    "ck3_reply_pending_character_interaction",
                    "ck3_get_war_state",
                    "ck3_raise_troops_default",
                    "ck3_move_army",
                    "ck3_disband_army",
                    "ck3_select_event_option",
                    "ck3_resolve_active_event",
                    "ck3_wait_for_change",
                },
            )
            snapshot = await client.call_tool("ck3_take_snapshot", {})
            self.assertFalse(snapshot.is_error)
            self.assertEqual(snapshot.structured_content["revision"], 4)
            action = await client.call_tool(
                "ck3_execute_step",
                {"step": "life-advance", "expected_revision": 4},
            )
            self.assertFalse(action.is_error)
            self.assertEqual(action.structured_content["backend_id"], "native-fixture")
            self.assertEqual(action.structured_content["expected_revision"], 4)
            automatic = await client.call_tool("ck3_auto_turn", {})
            self.assertFalse(automatic.is_error)
            self.assertEqual(
                automatic.structured_content["selected_step"],
                "select-event-option-1",
            )
            checkpoint = await client.call_tool(
                "ck3_save_checkpoint",
                {"expected_revision": 4},
            )
            self.assertFalse(checkpoint.is_error)
            self.assertEqual(
                checkpoint.structured_content["checkpoint"]["name"],
                "xar_checkpoint.ck3",
            )
            self.assertEqual(
                checkpoint.structured_content["checkpoint"]["date_raw"],
                53_171_424,
            )
            restored = await client.call_tool(
                "ck3_restore_checkpoint",
                {"expected_revision": 4},
            )
            self.assertFalse(restored.is_error)
            self.assertEqual(
                restored.structured_content["checkpoint"]["status"],
                "restored",
            )
            self.assertEqual(
                restored.structured_content["restored_date"]["date_raw"],
                53_171_424,
            )
            interaction = await client.call_tool(
                "ck3_reply_pending_character_interaction",
                {
                    "accept": True,
                    "interaction_instance_id": 52,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(interaction.is_error)
            self.assertTrue(interaction.structured_content["accepted"])
            self.assertEqual(
                interaction.structured_content["sender_character_id"], 901
            )
            war_state = await client.call_tool("ck3_get_war_state", {})
            self.assertFalse(war_state.is_error)
            self.assertEqual(war_state.structured_content["status"], "active")
            raised = await client.call_tool(
                "ck3_raise_troops_default", {"expected_revision": 4}
            )
            self.assertFalse(raised.is_error)
            moved = await client.call_tool(
                "ck3_move_army",
                {
                    "army_id": 81,
                    "target_province_id": 60,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(moved.is_error)
            self.assertEqual(moved.structured_content["army_id"], 81)
            disbanded = await client.call_tool(
                "ck3_disband_army",
                {"army_id": 81, "expected_revision": 4},
            )
            self.assertFalse(disbanded.is_error)
            event_action = await client.call_tool(
                "ck3_select_event_option",
                {
                    "option_number": 2,
                    "event_instance_id": 44,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(event_action.is_error)
            self.assertEqual(event_action.structured_content["option_number"], 2)
            self.assertEqual(event_action.structured_content["option_index"], 1)


if __name__ == "__main__":
    unittest.main()
