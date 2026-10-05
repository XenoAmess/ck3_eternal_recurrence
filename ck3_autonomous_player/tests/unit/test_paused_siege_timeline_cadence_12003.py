"""Production-path replay of R0047's stationary-siege cadence failure."""

from __future__ import annotations

import unittest

from test_native_bridge_driver import (
    FakeEndpoint,
    _active_siege,
    _army,
    _hello,
    _objective_state,
    _snapshot,
    _war,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver


class PausedSiegeTimelineCadenceTests(unittest.TestCase):
    def test_sparse_running_publication_uses_existing_one_day_siege_cadence(self) -> None:
        # The speed-five +13 frame is the preserved R0047 failure, not a claim
        # that the retained artifact reveals every intermediate publication.
        endpoint = FakeEndpoint()
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint)
        endpoint.publish(_hello(
            "game.state.snapshot", "game.state.active-wars",
            "game.state.player-armies", "game.state.army-routes",
            "game.state.war-objective-siege-progress",
            "game.state.war-objective-assault",
            "game.command.set-speed-1", "game.command.set-speed-3",
            "game.command.set-speed-5", "game.command.resume-map",
            "game.command.pause-map",
        ))
        armies = [_army(
            army_id, province_id=3711, soldiers=None,
            army_state="sieging", army_state_code=3,
            route_province_ids=[], in_combat=False, retreating=False,
        ) for army_id in [268435481, 184549452, 301989997]]
        start_date = 53_265_384
        speed = 1
        current_date = start_date
        native_revision = 33

        def publish(*, paused: bool) -> None:
            nonlocal native_revision
            native_revision += 1
            siege = _active_siege(
                siege_id=486539314, army_id=184549452,
                current_work_raw=25_428_292, total_work_raw=55_000_000,
                progress_raw=46_233, days_left=99,
                assault_observable=True, breach_level=0,
                assault_in_progress=False, can_start_assault=False,
                can_stop_assault=False, assault_daily_progress_raw=0,
                assault_daily_casualties=0,
            )
            war = _war(
                117440524, allied_armies=armies, score=38,
                war_objective_province_ids=[470, 3711, 472],
                objective_province_states=[
                    _objective_state(470, occupant=707),
                    _objective_state(3711, fort_level=6, besieging_strength=5298,
                                     siege_observable=paused, active_siege=siege),
                    _objective_state(472, occupant=707),
                ],
            )
            endpoint.publish(_snapshot(
                native_revision, date_raw=current_date, speed=speed,
                paused=paused, active_wars=[war], player_armies=armies,
            ))

        publish(paused=True)
        self.assertIsNone(driver.state.diagnostics()["last_rejected_state_snapshot"])

        def answer(frame: dict[str, object]) -> None:
            nonlocal speed, current_date
            step = str(frame["step"])
            endpoint.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": {"step": step, "accepted": True, "status": "submitted"},
            })
            if step.startswith("set-speed-"):
                speed = int(step.rsplit("-", 1)[1])
                publish(paused=True)
            elif step == "resume-map":
                # v73's failed fast arm and the Root's working one-day arm.
                current_date += (13 if speed == 5 else 1) * 24
                publish(paused=False)
            elif step == "pause-map":
                publish(paused=True)

        endpoint.send_hook = answer
        result = driver.execute_step("life-advance")
        self.assertLessEqual(result["elapsed_days"], result["requested_horizon_days"])
        self.assertEqual(result["requested_horizon_days"], 1)
        self.assertEqual(result["elapsed_days"], 1)
        self.assertTrue(result["paused"])
        self.assertEqual(result["timeline_speed"], 1)
        self.assertEqual([item["step"] for item in result["actions"]],
                         ["set-speed-1", "resume-map", "pause-map"])
        # The unavailable rich running CSiege row remains a gap, not victory.
        self.assertEqual(result["war_progress_after"]["wars"][0]["war_id"], 117440524)


if __name__ == "__main__":
    unittest.main()
