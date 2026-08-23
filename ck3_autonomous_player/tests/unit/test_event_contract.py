from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    CallbackGameplayDriver,
    DevelopmentReportDriver,
)
from xar_autoplayer.bridge.event_contract import (
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
    parse_event_option_step,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.strategy import choose_one_life_turn


class EventContractTests(unittest.TestCase):
    def test_native_option_count_expands_to_backend_neutral_options(self) -> None:
        event = normalize_active_event(
            {"instance_id": 731, "option_count": 3},
            default_source="native",
        )

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event["instance_id"], 731)
        self.assertEqual(event["option_count"], 3)
        self.assertEqual(
            [option["option_number"] for option in event["options"]],
            [1, 2, 3],
        )
        self.assertEqual(
            [option["index"] for option in event["options"]],
            [0, 1, 2],
        )

    def test_ocr_option_shape_maps_without_losing_visible_text(self) -> None:
        event = normalize_active_event(
            {
                "title": "A Difficult Choice",
                "options": [
                    {"option_number": 1, "visible_text": "Pay gold"},
                    {
                        "option_number": 2,
                        "visible_text": "Gain prestige",
                        "strategy_score": 50,
                    },
                ],
            },
            default_source="vision",
        )

        assert event is not None
        self.assertEqual(event["option_count"], 2)
        self.assertEqual(event["options"][1]["label"], "Gain prestige")
        self.assertEqual(choose_event_option_number(event), 2)

    def test_step_number_is_one_based_while_command_index_is_zero_based(self) -> None:
        self.assertEqual(event_option_step(1), "select-event-option-1")
        self.assertEqual(parse_event_option_step("select-event-option-3"), 3)
        self.assertIsNone(parse_event_option_step("select-event-option-0"))

    def test_planner_uses_native_primitive_before_life_plan(self) -> None:
        plan = choose_one_life_turn(
            [],
            snapshot={
                "source": "native",
                "active_event": {"instance_id": 91, "option_count": 2},
            },
            action_steps={
                "pause-map",
                "set-speed-5",
                "select-event-option-1",
                "select-event-option-2",
            },
        )

        self.assertEqual(plan["phase"], "active_event")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        self.assertEqual(plan["active_event"]["selected_option_index"], 0)

    def test_planner_visual_event_fallback_remains_explicit(self) -> None:
        plan = choose_one_life_turn(
            [],
            snapshot={
                "source": "vision",
                "active_event": {
                    "instance_id": None,
                    "option_count": None,
                    "options": [],
                },
            },
            action_steps={"resolve-current-event"},
        )

        self.assertEqual(plan["phase"], "active_event_visual_fallback")
        self.assertEqual(plan["selected_step"], "resolve-current-event")

    def test_service_selects_typed_event_option_with_revision(self) -> None:
        calls: list[tuple[str, int | None]] = []
        snapshot = {
            "snapshot_id": "native:17",
            "revision": 17,
            "source": "native",
            "history": [],
            "active_event": {"instance_id": 812, "option_count": 2},
        }
        driver = CallbackGameplayDriver(
            backend_id="native-fixture",
            snapshot=lambda: snapshot,
            execute=lambda step, revision: calls.append((step, revision))
            or {"accepted": True},
            action_steps=(
                "select-event-option-1",
                "select-event-option-2",
            ),
        )
        service = GameplayBridgeService(driver)

        result = service.select_event_option(
            2,
            event_instance_id=812,
            expected_revision=17,
        )

        self.assertEqual(calls, [("select-event-option-2", 17)])
        self.assertEqual(result["option_number"], 2)
        self.assertEqual(result["option_index"], 1)

    def test_service_resolver_uses_highest_scored_enabled_option(self) -> None:
        calls: list[str] = []
        driver = CallbackGameplayDriver(
            backend_id="fixture",
            snapshot=lambda: {
                "snapshot_id": "vision:4",
                "revision": 4,
                "source": "vision",
                "history": [],
                "active_event": {
                    "instance_id": None,
                    "options": [
                        {"option_number": 1, "strategy_score": -20},
                        {"option_number": 2, "strategy_score": 80},
                    ],
                },
            },
            execute=lambda step, _revision: calls.append(step) or {"ok": True},
            action_steps=(
                "select-event-option-1",
                "select-event-option-2",
            ),
        )

        result = GameplayBridgeService(driver).resolve_active_event()

        self.assertEqual(calls, ["select-event-option-2"])
        self.assertEqual(result["option_index"], 1)
        self.assertEqual(
            result["ordinary_events"][0]["selected_option_number"], 2
        )

    def test_existing_vision_interruption_projects_an_active_event(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = (
                Path(temporary)
                / "runs"
                / "20260823T000000Z-dev-session-event-fixture"
            )
            run.mkdir(parents=True)
            (run / "report.json").write_text(
                json.dumps(
                    {
                        "run_id": run.name,
                        "finalized": False,
                        "commands": [
                            {
                                "command": "auto-run 1",
                                "ok": False,
                                "result": {
                                    "turns": [
                                        {
                                            "command": "auto-turn",
                                            "ok": False,
                                            "error": (
                                                "AgentError: ordinary event "
                                                "interrupted war advance"
                                            ),
                                        }
                                    ]
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            snapshot = DevelopmentReportDriver(Path(temporary)).take_snapshot()

        self.assertEqual(snapshot["active_event"]["source"], "vision")
        self.assertIsNone(snapshot["active_event"]["instance_id"])
        self.assertEqual(snapshot["active_event"]["options"], [])


if __name__ == "__main__":
    unittest.main()
