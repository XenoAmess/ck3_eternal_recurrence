"""Synthetic native frames for the reproduced cleanup-pause rejection.

The rejection text is from the actual native response. All state, identities,
transport and timing below are synthetic; no local game/artifact is required.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class SyntheticEndpoint:
    pipe_name = r"\\.\pipe\synthetic-pause-cleanup-fixture"

    def __init__(self) -> None:
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None
        self.frames: list[dict[str, object]] = []

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        pass

    def transport_error(self) -> None:
        return None


class LifeAdvancePauseMapUnavailableRetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.endpoint = SyntheticEndpoint()
        self.driver = NativeHeadlessGameplayDriver(
            self.endpoint.pipe_name,
            endpoint=self.endpoint,
            command_timeout_seconds=0.1,
        )
        self.endpoint.publish({
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 4242,
            "session_generation": 0,
            "capabilities": [
                "game.state.snapshot", "game.command.pause-map",
                "game.command.resume-map",
                *[f"game.command.set-speed-{speed}" for speed in range(1, 6)],
            ],
        })
        self.date_raw = 53_170_000
        self.revision = 1
        self.speed = 1
        self.pause_count = 0
        self.first_error = "CK3 map state is unavailable"
        self.second_rejected = False
        self.publish_paused_after_second_ack = True
        self._publish(paused=True)
        self.endpoint.send_hook = self._answer

    def tearDown(self) -> None:
        self.driver.close()

    def _publish(self, *, paused: bool) -> None:
        self.endpoint.publish({
            "type": "state_snapshot",
            "protocol_version": 1,
            "snapshot_id": f"native:{self.revision}",
            "revision": self.revision,
            "state": {
                "phase": "map_hud", "date": "synthetic",
                "date_raw": self.date_raw, "speed": self.speed,
                "paused": paused, "map_ready": True, "history": [],
                "active_event": None, "pending_character_interaction": None,
                "played_character": {"character_id": 12345, "alive": True},
                "played_character_gold": None,
                "played_character_prestige": None,
                "played_character_piety": None,
                "one_life_settlement": None,
                # The opaque moving-stack frame selects a one-day timeline.
                # No military command or policy is exercised by this fixture.
                "active_wars": [{
                    "war_id": 61, "player_side": "attacker",
                    "primary_opponent_character_id": 67890,
                    "player_is_primary_war_leader": True,
                    "player_relative_war_score": 0,
                    "targeted_title_ids": [], "war_objective_province_ids": [],
                    "objective_province_states": [],
                    "allied_armies": [], "enemy_armies": [],
                }],
                "player_armies": [{
                    "army_id": 101, "owner_character_id": 12345,
                    "soldiers": 100, "current_province_id": 1000,
                    "move_target_province_id": 1001, "controllable": True,
                    "army_state": "moving", "army_state_code": 7,
                    "route_province_ids": [1001],
                    "in_combat": False, "retreating": False,
                }],
            },
        })

    def _answer(self, request: dict[str, object]) -> None:
        if request.get("type") != "execute_step":
            return
        step = request["step"]
        frame = {
            "type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True,
            "result": {"step": step, "accepted": True, "status": "submitted"},
        }
        if step.startswith("set-speed-"):
            self.speed = int(step.rsplit("-", 1)[1])
            self.endpoint.publish(frame)
            self.revision += 1
            self._publish(paused=True)
        elif step == "resume-map":
            self.endpoint.publish(frame)
            self.date_raw += 24
            self.revision += 1
            self._publish(paused=False)
        elif step == "pause-map":
            self.pause_count += 1
            if self.pause_count == 1 or self.second_rejected:
                frame.pop("result")
                frame.update(ok=False, error=self.first_error)
                self.endpoint.publish(frame)
                self.revision += 1
                self._publish(paused=False)
            else:
                self.endpoint.publish(frame)
                if self.publish_paused_after_second_ack:
                    self.revision += 1
                    self._publish(paused=True)

    def _advance(self) -> dict[str, object]:
        starting = self.driver.take_snapshot()
        return self.driver.execute_step(
            "life-advance", expected_revision=starting["revision"]
        )

    def test_actual_rejection_reaches_existing_retry_and_real_paused_frame(self) -> None:
        result = self._advance()
        self.assertEqual(result["elapsed_days"], 1)
        self.assertTrue(result["paused"])
        self.assertEqual(self.pause_count, 2)
        pause_results = [
            action["result"] for action in result["actions"]
            if action["step"] == "pause-map"
        ]
        self.assertEqual([row["status"] for row in pause_results], ["rejected", "submitted"])
        self.assertFalse(pause_results[0]["accepted"])
        self.assertEqual(pause_results[0]["error"], self.first_error)
        pause_requests = [row for row in self.endpoint.frames if row.get("step") == "pause-map"]
        self.assertGreater(pause_requests[1]["expected_revision"], pause_requests[0]["expected_revision"])
        self.assertTrue(self.driver.take_internal_semantic_snapshot()["paused"])

    def test_second_rejection_retains_existing_two_attempt_bound(self) -> None:
        self.second_rejected = True
        with self.assertRaisesRegex(BridgeUnavailableError, "pause_attempts=2.*second_error"):
            self._advance()
        self.assertEqual(self.pause_count, 2)

    def test_other_native_rejection_is_not_retried(self) -> None:
        self.first_error = "other native rejection"
        with self.assertRaisesRegex(BridgeUnavailableError, "other native rejection"):
            self._advance()
        self.assertEqual(self.pause_count, 1)

    def test_submitted_ack_alone_does_not_complete_cleanup_pause(self) -> None:
        self.publish_paused_after_second_ack = False
        with self.assertRaisesRegex(BridgeUnavailableError, "did not observe the paused map"):
            self._advance()
        self.assertEqual(self.pause_count, 2)
        self.assertFalse(self.driver.take_internal_semantic_snapshot()["paused"])


if __name__ == "__main__":
    unittest.main()
