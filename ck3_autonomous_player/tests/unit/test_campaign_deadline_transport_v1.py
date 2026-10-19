"""Actual Driver/executor/Protocol fake-wire compound; no live-game credit."""
import copy
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import native_driver as n
from xar_autoplayer.bridge.campaign_deadline_v1 import cap_plan_v1
from xar_autoplayer.bridge.route_contact_window_contract import advance_route_contact_window_step
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import (
    battle_decision_epoch_advance_step, committed_route_sentinel_advance_step,
    war_objective_hold_sentinel_advance_step,
)
from xar_autoplayer.campaign_score_cadence_v1 import date_to_raw
from ck3_autonomous_player.tests.unit.test_native_bridge_driver import (
    FakeEndpoint, _army, _hello, _snapshot, _tactical_sentinel_status, _war,
)


class CampaignDeadlineCompoundTests(unittest.TestCase):
    def driver(self, date="1066.10.10", *, battle=False, overshoot=False):
        endpoint = FakeEndpoint()
        driver = n.NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
            command_timeout_seconds=.2, life_advance_timeout_seconds=.2)
        endpoint.publish(_hello("game.state.snapshot", "game.command.resume-map", "game.command.pause-map",
            *[f"game.command.set-speed-{speed}" for speed in range(1, 6)],
            n._TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY, n._TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY,
            n._TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY))
        start = date_to_raw(date)
        players = [_army(501, in_combat=True)] if battle else []
        wars = [_war(allied_armies=players)] if battle else []
        state = {"revision": 1, "date": start, "speed": 1, "arm": None}

        def publish():
            endpoint.publish(_snapshot(state["revision"], date_raw=state["date"], speed=state["speed"],
                paused=True, active_wars=wars, player_armies=players))
        publish()
        driver.configure_campaign_score_cadence_v1(campaign_id="software-fixture",
            start_date="1066.9.15", start_date_raw=53144328)

        def answer(frame):
            if frame.get("type") != "execute_step":
                return
            step = str(frame["step"])
            result = {"step": step, "accepted": True, "status": "available"}
            if step.startswith(n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX):
                payload = step.removeprefix(n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX).split("-")
                target, speed, mode, count = int(payload[2]), int(payload[4]), payload[6], int(payload[8])
                state["arm"] = _tactical_sentinel_status(state="armed", generation=7,
                    starting_date_raw=start, target_date_raw=target, observed_date_raw=start,
                    speed=speed, mode="decision_epoch" if mode == "decision" else "terminal_or_sentinel",
                    army_count=count, combat_count=1 if battle else 0)
                result["tactical_daily_sentinel"] = state["arm"]
            elif step == n._TACTICAL_DAILY_SENTINEL_STATUS_STEP:
                arm = state["arm"]
                result["tactical_daily_sentinel"] = _tactical_sentinel_status(state="triggered", generation=7,
                    starting_date_raw=start, target_date_raw=arm["target_date_raw"], observed_date_raw=state["date"],
                    speed=arm["speed"], mode=arm["mode"], army_count=arm["army_count"], combat_count=arm["combat_count"],
                    completed_daily_ticks=(state["date"]-start)//24, trigger_flags=1,
                    trigger_reasons=["date_deadline"], overshoot_days=1 if overshoot else 0,
                    pause_wrapper_called=True, pause_observed=True)
            elif step.startswith(n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX):
                result["status"] = "canceled"
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True, "result": result})
            if step.startswith("set-speed-"):
                state["speed"] = int(step[-1]); state["revision"] += 1; publish()
            elif step == "resume-map":
                state["date"] = state["arm"]["target_date_raw"] + (24 if overshoot else 0)
                state["revision"] += 1; publish()
            elif step == "pause-map":
                state["revision"] += 1; publish()
        endpoint.send_hook = answer
        self.addCleanup(driver.close)
        return driver, endpoint

    def steps(self, endpoint):
        return [frame["step"] for frame in endpoint.frames if frame.get("type") == "execute_step"]

    def test_actual_generic_executor_preserves_multi_day_slice_and_clips_month(self):
        for date, days in (("1066.9.16", 29), ("1066.10.10", 5), ("1096.9.12", 3)):
            with self.subTest(date=date):
                driver, endpoint = self.driver(date)
                result = driver.execute_step("life-advance", expected_revision=int(driver.take_snapshot()["revision"]))
                self.assertEqual(result["elapsed_days"], days)
                self.assertEqual(result["requested_horizon_days"], days)
                self.assertEqual(result["ending_date_raw"], result["campaign_deadline_v1"]["target_date_raw"])
                self.assertEqual(result["source"], "native-composite")
                self.assertNotIn("exact_day_native_clock", result)
                self.assertEqual(result["campaign_deadline_native_clock_v1"]["scope"], "campaign_date_deadline")
                self.assertEqual(sum(step.startswith(n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX) for step in self.steps(endpoint)), 1)
                self.assertEqual(self.steps(endpoint).count("resume-map"), 1)
                self.assertNotIn("pause-map", self.steps(endpoint))

    def test_actual_tactical_executor_uses_same_canonical_plan_and_single_arm(self):
        driver, endpoint = self.driver(battle=True)
        frame = driver.take_internal_semantic_snapshot()
        requested = battle_decision_epoch_advance_step(frame["date_raw"] + 15 * 24)
        plan = driver.cap_campaign_advance_plan_v1({"planning_source_frame": frame,
            "plan": {"selected_step": requested, "absolute_target_date_raw": frame["date_raw"] + 15*24}})
        selected = plan["plan"]["selected_step"]
        result = driver.execute_step(selected, expected_revision=int(frame["revision"]))
        self.assertEqual(result["step"], selected)
        self.assertEqual(result["target_date_raw"], date_to_raw("1066.10.15"))
        self.assertEqual(plan["plan"]["absolute_target_date_raw"], result["target_date_raw"])
        self.assertEqual(result["watch_army_ids"], [501])
        self.assertEqual(result["sentinel_scope"], "active_battle")
        self.assertEqual(result["timeline_speed"], 3)
        self.assertEqual(sum(step.startswith(n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX) for step in self.steps(endpoint)), 1)

    def test_public_service_plan_hook_and_ab_mode_identity_are_preserved(self):
        driver, _ = self.driver()
        raw = date_to_raw("1066.10.14")
        step = war_objective_hold_sentinel_advance_step(61, 501, 2635, raw+7*24, timeline_speed=5)
        planned = {"snapshot_id": "native:1", "revision": 1, "planning_source_frame": {"date_raw": raw},
                   "plan": {"selected_step": step, "research_high_speed_ab": True, "timeline_speed": 5,
                            "sentinel_scope": "stationary_objective_hold", "sentinel_mode": "decision_epoch"}}
        service = GameplayBridgeService.__new__(GameplayBridgeService)
        service.driver = driver
        service._plan_turn_internal = lambda: copy.deepcopy(planned)
        with patch("xar_autoplayer.bridge.ordinary_sway_service_v1.stage_ordinary_sway_v1", side_effect=lambda service, plan: plan):
            actual = service.plan_turn()
        self.assertIn(f"until-{raw+24}-speed-5", actual["plan"]["selected_step"])
        # Ordinary Sway's internal fresh plan bypasses public plan_turn; the
        # real common dispatcher must cap it before the presentation hook.
        submitted = []
        intercepted = service._execute_planned_turn_without_unhandled_capture(planned,
            before_submit=lambda value: submitted.append(value) or {"fixture": "intercept_before_native"})
        self.assertEqual(intercepted["status"], "intercepted")
        self.assertEqual(submitted[0]["selected_step"], actual["plan"]["selected_step"])
        self.assertIs(driver.cap_campaign_advance_plan_v1(actual), actual)
        for key in ("research_high_speed_ab", "timeline_speed", "sentinel_scope", "sentinel_mode"):
            self.assertEqual(actual["plan"][key], planned["plan"][key])
        route = committed_route_sentinel_advance_step(501, 2635, raw+3*24, timeline_speed=3)
        window = advance_route_contact_window_step(501, 2635, [601], horizon_days=3)
        for original, expected in ((route, committed_route_sentinel_advance_step(501, 2635, raw+24)),
                                   (window, "life-advance-one-day")):
            result = cap_plan_v1(driver, {"planning_source_frame": {"date_raw": raw}, "plan": {"selected_step": original}})
            self.assertEqual(result["plan"]["selected_step"], expected)

    def test_endpoint_nested_ordinary_advance_never_resumes_or_claims_liveness(self):
        driver, endpoint = self.driver("1096.9.15")
        result = driver.execute_step("life-advance", expected_revision=int(driver.take_snapshot()["revision"]))
        self.assertEqual(result["elapsed_days"], 0)
        self.assertEqual(result["progress_status"], "campaign_endpoint_reached")
        self.assertFalse(result["calendar_progress_verified"])
        self.assertEqual(self.steps(endpoint), [])

    def test_actual_overshoot_is_rejected_and_default_driver_has_no_cap(self):
        driver, endpoint = self.driver(overshoot=True)
        with self.assertRaises(n.BridgeUnavailableError):
            driver.execute_step("life-advance", expected_revision=int(driver.take_snapshot()["revision"]))
        self.assertEqual(self.steps(endpoint).count("resume-map"), 1)
        plain = object.__new__(n.NativeHeadlessGameplayDriver)
        planned = {"plan": {"selected_step": "life-advance"}}
        self.assertIs(plain.cap_campaign_advance_plan_v1(planned), planned)


if __name__ == "__main__":
    unittest.main()
