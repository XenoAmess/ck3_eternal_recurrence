from __future__ import annotations

import copy
import unittest
from unittest import mock

from test_native_bridge_driver import (
    FakeEndpoint,
    _army,
    _army_strength,
    _hello,
    _snapshot,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class ArmyStrengthQueryDeadline12003Tests(unittest.TestCase):
    def test_late_native_result_diagnostic_and_configured_deadline_preserved(self) -> None:
        army_id = 218_104_048
        rejection = (
            "CK3 army-strength query is unavailable "
            "[worker=failed;native=finish_failed;reader=returned;"
            "wait=1;reclaim=0]"
        )
        scenes = (
            ("default_late_result", 10.0, "query-army-strengths-v1", 31.0, 35.0, None),
            ("larger_configured_result", 45.0, "query-army-strengths-v1", 31.0, 45.0, None),
            ("late_native_diagnostic", 10.0, "query-army-strengths-v1", 31.0, 35.0, rejection),
            ("other_command_deadline", 10.0, "set-speed-1", 0.0, 10.0, None),
        )
        for name, configured, step, completes_at, expected_budget, error in scenes:
            with self.subTest(scene=name):
                endpoint = FakeEndpoint()
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name,
                    endpoint=endpoint,
                    command_timeout_seconds=configured,
                )
                try:
                    endpoint.publish(_hello(
                        "game.state.snapshot",
                        "game.command.query-army-strengths-v1",
                        "game.command.set-speed-1",
                    ))
                    endpoint.publish(_snapshot(
                        2,
                        date_raw=53_288_232,
                        played_character={"character_id": 29_829, "alive": True},
                        player_armies=[_army(army_id, controllable=True)],
                    ))
                    starting = driver.take_snapshot()
                    original_wait = driver.state.wait_for_command_result
                    pending: dict[str, dict[str, object]] = {}
                    virtual_now = [0.0]
                    budgets: list[float] = []

                    def sent(frame: dict[str, object]) -> None:
                        self.assertEqual(frame["type"], "execute_step")
                        self.assertEqual(frame["step"], step)
                        pending[str(frame["request_id"])] = copy.deepcopy(frame)

                    def wait(request_id: str, timeout_seconds: float):
                        budgets.append(timeout_seconds)
                        if virtual_now[0] + timeout_seconds < completes_at:
                            virtual_now[0] += timeout_seconds
                            return None
                        virtual_now[0] = completes_at
                        request = pending.pop(request_id)
                        response: dict[str, object] = {
                            "type": "command_result",
                            "protocol_version": 1,
                            "request_id": request_id,
                            "ok": error is None,
                        }
                        if error is not None:
                            response["error"] = error
                        else:
                            response["result"] = {
                                "step": request["step"],
                                "accepted": True,
                                "status": "available",
                            }
                            if step == "query-army-strengths-v1":
                                response["result"].update({
                                    "query_sequence": 1,
                                    "army_strengths": [
                                        _army_strength(army_id, "player", [])
                                    ],
                                })
                        endpoint.publish(response)
                        return original_wait(request_id, 0.0)

                    endpoint.send_hook = sent
                    with mock.patch.object(
                        driver.state, "wait_for_command_result", side_effect=wait
                    ), mock.patch(
                        "xar_autoplayer.bridge.native_driver.time.monotonic",
                        side_effect=lambda: virtual_now[0],
                    ):
                        if error is not None:
                            with self.assertRaises(BridgeUnavailableError) as raised:
                                driver.execute_step(
                                    step, expected_revision=int(starting["revision"])
                                )
                            self.assertIn(rejection, str(raised.exception))
                            self.assertNotIn("command_result timed out", str(raised.exception))
                        elif step == "query-army-strengths-v1":
                            result = driver.execute_step(
                                step, expected_revision=int(starting["revision"])
                            )
                            self.assertEqual(result["status"], "available")
                            self.assertEqual(result["army_strengths"][0]["army_id"], army_id)
                            self.assertEqual(result["army_strengths"][0]["current_soldiers"], 1200)
                            self.assertEqual(result["queried_snapshot_id"], "native:2")
                            self.assertEqual(driver.take_snapshot()["army_strengths_query_sequence"], 1)
                        else:
                            result = driver._execute_primitive_step(
                                step, expected_revision=int(starting["revision"])
                            )
                            self.assertIs(result["accepted"], True)
                    self.assertEqual(budgets, [expected_budget])
                    self.assertEqual(virtual_now[0], completes_at)
                    self.assertEqual(driver.command_timeout_seconds, configured)
                    self.assertEqual(len(endpoint.frames), 1)
                finally:
                    driver.close()
