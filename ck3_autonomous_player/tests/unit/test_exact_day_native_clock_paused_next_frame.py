"""One synthetic provider regression for the real +7-day polling failure.

The fake game advances seven days without an armed native deadline. When the
deadline is armed, it publishes only the next paused day: no running frame is
available to the production resume helper. No CK3 process or save is used.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class ClockProvider:
    pipe_name = r"\\.\pipe\synthetic-exact-day-native-deadline"

    def __init__(self) -> None:
        self.on_frame = None
        self.frames: list[dict[str, object]] = []
        self.date_raw = 53_288_256
        self.revision = 1
        self.speed = 1
        self.armed = False
        self.paused = True
        self.target = None
        self.clock = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame

    def publish(self, frame: dict[str, object]) -> None:
        self.on_frame(frame)

    def close(self) -> None:
        pass

    def transport_error(self) -> None:
        return None

    def publish_state(self) -> None:
        self.publish({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{self.revision}", "revision": self.revision,
            "state": {
                "phase": "map_hud", "date": "synthetic",
                "date_raw": self.date_raw, "speed": self.speed,
                "paused": self.paused, "map_ready": True, "history": [],
                "active_event": None, "pending_character_interaction": None,
                "played_character": {"character_id": 29829, "alive": True},
                "played_character_gold": None, "played_character_prestige": None,
                "played_character_piety": None, "one_life_settlement": None,
                "active_wars": [], "player_armies": [],
            },
        })

    def send(self, request: dict[str, object]) -> None:
        self.frames.append(request)
        if request.get("type") != "execute_step":
            return
        step = str(request["step"])
        result = {"step": step, "accepted": True, "status": "submitted"}
        if step.startswith("set-speed-"):
            self.speed = int(step.rsplit("-", 1)[1])
            self.revision += 1
        elif step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            # These are native protocol fields, not an invocation of the code
            # under test. The provider admits only the date-only clock shape.
            if not step.endswith("-mode-terminal-a-0") or not self.paused:
                raise AssertionError("clock was not armed while the fake game was paused")
            parts = step.split("-to-", 1)
            self.target = int(parts[1].split("-speed-", 1)[0])
            if self.target != self.date_raw + 24:
                raise AssertionError("native deadline must precede the second daily tick")
            self.armed = True
            self.clock = {
                "state": "armed", "generation": 37,
                "starting_date_raw": self.date_raw, "target_date_raw": self.target,
                "last_observed_date_raw": self.date_raw, "trigger_date_raw": 0,
                "speed": self.speed, "mode": "terminal_or_sentinel",
                "army_count": 0, "combat_count": 0, "completed_daily_ticks": 0,
                "intermediate_pause_count": 0, "trigger_flags": 0,
                "trigger_reasons": [], "signed_date_delta_from_target_raw": 0,
                "overshoot_days": -1, "pause_wrapper_called": False,
                "pause_observed": False, "terminal_observed": False, "abnormal": False,
            }
            result.update(status="available", tactical_daily_sentinel=dict(self.clock))
        elif step == "resume-map":
            self.date_raw += 24 if self.armed else 7 * 24
            self.paused = self.armed
            self.revision += 1
            if self.armed:
                self.clock.update({
                    "state": "triggered", "last_observed_date_raw": self.date_raw,
                    "trigger_date_raw": self.date_raw, "completed_daily_ticks": 1,
                    "trigger_flags": 1, "trigger_reasons": ["date_deadline"],
                    "overshoot_days": 0, "pause_wrapper_called": True,
                    "pause_observed": True,
                })
        elif step == "research-query-tactical-daily-sentinel-v1":
            result.update(status="available", tactical_daily_sentinel=dict(self.clock))
        elif step == "pause-map":
            self.paused = True
            self.revision += 1
        else:
            raise AssertionError(f"unexpected provider command {step}")
        self.publish({
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": result,
        })
        self.publish_state()


class ExactDayNativeClockPausedNextFrameTests(unittest.TestCase):
    def test_real_resume_accepts_native_paused_next_day_after_arm(self) -> None:
        provider = ClockProvider()
        driver = NativeHeadlessGameplayDriver(
            provider.pipe_name, endpoint=provider,
            command_timeout_seconds=0.1, life_advance_timeout_seconds=0.1,
        )
        try:
            provider.publish({
                "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
                "pid": 4242, "session_generation": 0,
                "capabilities": [
                    "game.state.snapshot", "game.command.pause-map", "game.command.resume-map",
                    *[f"game.command.set-speed-{speed}" for speed in range(1, 6)],
                    "game.command.research-arm-tactical-daily-sentinel-v1-N",
                    "game.command.research-query-tactical-daily-sentinel-v1",
                    "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
                ],
            })
            provider.publish_state()
            before = driver.take_snapshot()
            result = driver.execute_step(
                "life-advance-one-day", expected_revision=before["revision"]
            )
            commands = [row["step"] for row in provider.frames
                        if row.get("type") == "execute_step"]
            self.assertEqual(len(commands), 4)
            self.assertEqual(commands[0], "set-speed-1")
            self.assertTrue(commands[1].endswith("-mode-terminal-a-0"))
            self.assertEqual(commands[2], "resume-map")
            self.assertEqual(commands[3], "research-query-tactical-daily-sentinel-v1")
            self.assertEqual(result["elapsed_days"], 1)
            self.assertEqual(result["ending_date_raw"] - result["starting_date_raw"], 24)
            self.assertTrue(result["paused"])
            self.assertEqual(result["exact_day_native_clock"]["stopped"]["generation"], 37)
            self.assertEqual(result["exact_day_native_clock"]["stopped"]["trigger_reasons"], ["date_deadline"])
            self.assertNotIn("pause-map", commands)
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
