"""Actual Driver -> Protocol synthetic route trial, with no Native/Game calls."""
import copy
import unittest

from xar_autoplayer.bridge import native_driver as n
from xar_autoplayer.bridge.contact_free_exact_route_speed_trial_v1 import select_v1
from xar_autoplayer.bridge.war_contract import advance_route_contact_horizon_step
from xar_autoplayer.campaign_score_cadence_v1 import date_to_raw
from ck3_autonomous_player.tests.unit.test_exact_day_native_clock_paused_next_frame import ClockProvider
from ck3_autonomous_player.tests.unit.test_native_bridge_driver import _army, _hello, _snapshot, _war


class RouteProvider(ClockProvider):
    def __init__(self, *, date="1066.10.10", fault=None, risky_sibling=False):
        super().__init__()
        self.date_raw = date_to_raw(date)
        self.start_raw = self.date_raw
        self.revision = 40
        self.fault, self.hint, self.event = fault, None, None
        self.player = _army(101, province_id=2603, move_target_province_id=2585,
            army_state="moving", route_province_ids=[2604, 2595, 2585])
        self.enemy = _army(31, province_id=2583, controllable=False, move_target_province_id=2600,
            army_state="moving", route_province_ids=[2594, 2600])
        self.players = [self.player]
        if risky_sibling:
            self.players.append(_army(102, in_combat=True))
        self.war = _war(allied_armies=self.players, enemy_armies=[self.enemy],
            war_objective_province_ids=[2585])

    def publish_state(self):
        if self.fault == "overshoot" and self.date_raw == self.start_raw + 24:
            self.date_raw += 24
            self.clock.update(last_observed_date_raw=self.date_raw, trigger_date_raw=self.date_raw,
                completed_daily_ticks=2, signed_date_delta_from_target_raw=24, overshoot_days=1)
        frame = _snapshot(self.revision, date_raw=self.date_raw, speed=self.speed, paused=self.paused,
            active_wars=[self.war], player_armies=self.players, active_event=self.event,
            played_character={"character_id": 29829, "alive": True})
        if self.hint is not None:
            frame["state"]["top_exclusive_modal_choice_hint"] = copy.deepcopy(self.hint)
        self.publish(frame)

    def publish(self, frame):
        result = frame.get("result")
        if (self.fault == "arm_speed" and isinstance(result, dict)
                and str(result.get("step")).startswith(n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX)):
            frame = copy.deepcopy(frame)
            frame["result"]["tactical_daily_sentinel"]["speed"] = 4
        super().publish(frame)

    def horizon(self):
        return {"status": "available", "date_raw": self.date_raw, "snapshot_revision": self.revision,
            "subject_army_id": 101, "target_province_id": 2585, "hostile_army_ids": [31],
            "subject_route": {"timeline_observable": True, "army_id": 101,
                "current_province_id": 2603, "effective_origin_province_id": 2604,
                "route_province_ids": [2604, 2595, 2585],
                "arrival_date_raws": [self.date_raw+24, self.date_raw+48, self.date_raw+72]},
            "hostile_routes": [{"timeline_observable": True, "army_id": 31,
                "current_province_id": 2583, "effective_origin_province_id": 2594,
                "route_province_ids": [2594, 2600],
                "arrival_date_raws": [self.date_raw+24, self.date_raw+48]}],
            "horizon_start_date_raw": self.date_raw, "horizon_end_date_raw": self.date_raw+24,
            "one_day_contact_free": True, "conflicts": []}

    def send(self, request):
        step = str(request.get("step"))
        if step.startswith("query-route-contact-horizon-"):
            self.frames.append(request)
            self.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": {"step": step, "accepted": True, "status": "available",
                    "query_sequence": 1, "snapshot_revision": self.revision,
                    "route_contact_horizon": self.horizon()}})
        elif step.startswith(n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX):
            self.frames.append(request)
            self.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": {"step": step, "accepted": True, "status": "canceled"}})
        elif step == "resume-map" and self.fault == "modal":
            self.frames.append(request)
            self.hint = {"status": "present", "owner_verified": True,
                "source": "application_main_pump_observed_modal_receiver",
                "opaque_root_id": "synthetic-route-modal", "max_observation_age_ms": 2000}
            self.revision += 1
            self.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": {"step": step, "accepted": True, "status": "submitted"}})
            self.publish_state()
        elif step == "set-speed-5" and self.fault == "setter_speed":
            self.frames.append(request)
            self.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": {"step": step, "accepted": True, "status": "submitted"}})
            self.publish_state()
        else:
            if step == "resume-map" and self.fault == "event":
                self.event = {"instance_id": 1, "option_count": 1}
            super().send(request)


class ContactFreeExactRouteTrialTests(unittest.TestCase):
    def driver(self, *, configured=True, missing=(), **provider_options):
        provider = RouteProvider(**provider_options)
        driver = n.NativeHeadlessGameplayDriver(provider.pipe_name, endpoint=provider,
            command_timeout_seconds=.03, life_advance_timeout_seconds=.03)
        capabilities = {"game.state.snapshot", "game.state.war-objectives", "game.state.army-routes",
            "game.command.query-route-contact-horizon-v1-N", "game.command.resume-map", "game.command.pause-map",
            *[f"game.command.set-speed-{v}" for v in (1, 3, 5)],
            n._TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY, n._TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY,
            n._TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY}
        provider.publish(_hello(*sorted(capabilities-set(missing))))
        provider.publish_state()
        driver.configure_campaign_score_cadence_v1(campaign_id="route-software", start_date="1066.9.15",
            start_date_raw=date_to_raw("1066.9.15"))
        if configured:
            driver.configure_contact_free_exact_route_speed_trial_v1(campaign_id="route-software",
                trial_id="route5-software-pending-live")
        self.addCleanup(driver.close)
        return driver, provider

    def query(self, driver):
        driver.execute_step("query-route-contact-horizon-v1-101-to-2585-h-1-31")
        return advance_route_contact_horizon_step(101, 2585, (31,))

    def advance(self, driver, step):
        return driver.execute_step(step, expected_revision=int(driver.take_snapshot()["revision"]))

    @staticmethod
    def commands(provider):
        return [frame["step"] for frame in provider.frames if frame.get("type") == "execute_step"]

    def test_configuration_is_explicit_idempotent_campaign_bound_and_has_no_native_side_effect(self):
        driver, provider = self.driver(configured=False)
        before = copy.deepcopy(driver.capabilities()["battle_speed_readiness"])
        configured = driver.configure_contact_free_exact_route_speed_trial_v1(campaign_id="route-software", trial_id="trial")
        self.assertFalse(configured["live_ready"])
        self.assertEqual(configured["qualification_status"], "controlled_trial_pending_live")
        self.assertEqual(configured, driver.configure_contact_free_exact_route_speed_trial_v1(
            campaign_id="route-software", trial_id="trial"))
        self.assertEqual(before, driver.capabilities()["battle_speed_readiness"])
        self.assertEqual((driver.route_contact_timeline_speed, driver.route_contact_effective_timeline_speed,
            driver.allow_route_contact_high_speed_ab), (3, 3, False))
        self.assertEqual(self.commands(provider), [])
        for args in ({"campaign_id": "other", "trial_id": "trial"},
                     {"campaign_id": "route-software", "trial_id": "replacement"},
                     {"campaign_id": "route-software", "trial_id": "trial", "speed": 4},
                     {"campaign_id": "route-software", "trial_id": "trial", "speed": True}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                driver.configure_contact_free_exact_route_speed_trial_v1(**args)
        driver.allow_route_contact_high_speed_ab = True
        with self.assertRaisesRegex(ValueError, "global route speed3"):
            driver.configure_contact_free_exact_route_speed_trial_v1(campaign_id="route-software", trial_id="trial")

    def test_real_query_proof_and_exact_clock_change_only_route_speed_and_trial_receipt(self):
        outputs, sequences = [], []
        for configured, expected in ((False, 3), (True, 5)):
            driver, provider = self.driver(configured=configured)
            step = self.query(driver)
            result = self.advance(driver, step)
            outputs.append(result)
            commands = self.commands(provider)
            sequences.append([word.replace(f"speed-{expected}", "speed-N") for word in commands])
            self.assertEqual(result["timeline_speed"], expected)
            self.assertEqual(result["exact_day_native_clock"]["armed"]["army_count"], 0)
            self.assertEqual(result["exact_day_native_clock"]["stopped"]["speed"], expected)
            self.assertEqual(commands.count("resume-map"), 1)
            self.assertNotIn("pause-map", commands)
            self.assertNotIn(step, driver.capabilities()["action_steps"])
            self.assertFalse(driver.allow_route_contact_high_speed_ab)
        self.assertEqual(sequences[0], sequences[1])
        for key in ("step", "starting_date_raw", "ending_date_raw", "elapsed_days", "requested_horizon_days",
                    "paused", "progress_status", "war_progress_before", "war_progress_after", "event_resolution"):
            self.assertEqual(outputs[0][key], outputs[1][key], key)
        self.assertNotIn("contact_free_exact_route_speed_trial_v1", outputs[0])
        proof = outputs[1]["contact_free_exact_route_speed_trial_v1"]
        self.assertEqual((proof["selected_speed"], proof["actual_timeline_speed"], proof["actual_elapsed_days"]), (5, 5, 1))
        self.assertFalse(proof["native_army_watch_claimed"])
        self.assertFalse(proof["live_ready"])
        self.assertFalse(proof["calendar_or_business_credit_inferred"])

    def test_native_cancel_capability_is_required_for_route_five_and_missing_it_keeps_three(self):
        driver, provider = self.driver(missing=(n._TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY,))
        result = self.advance(driver, self.query(driver))
        self.assertEqual(result["timeline_speed"], 3)
        proof = result["contact_free_exact_route_speed_trial_v1"]
        self.assertEqual(proof["selection_status"], "native_clock_or_speed_capability_missing")
        self.assertNotIn("set-speed-5", self.commands(provider))

    def test_one_natural_eligible_attempt_does_not_enable_later_days_or_reset_by_configuration(self):
        driver, provider = self.driver()
        first = self.advance(driver, self.query(driver))
        self.assertEqual(first["timeline_speed"], 5)
        driver.configure_contact_free_exact_route_speed_trial_v1(campaign_id="route-software",
            trial_id="route5-software-pending-live")
        second = self.advance(driver, self.query(driver))
        self.assertEqual(second["timeline_speed"], 3)
        self.assertEqual(second["elapsed_days"], 1)
        proof = second["contact_free_exact_route_speed_trial_v1"]
        self.assertEqual(proof["selection_status"], "controlled_trial_attempt_exhausted")
        self.assertEqual((proof["attempt_limit"], proof["attempts_used"]), (1, 1))
        self.assertEqual(self.commands(provider).count("set-speed-5"), 1)

    def test_stale_frame_and_unsafe_sibling_cannot_bypass_existing_proof_guard(self):
        for risky in (False, True):
            driver, provider = self.driver(risky_sibling=risky)
            step = self.query(driver)
            if not risky:
                provider.revision += 1
                provider.date_raw += 24
                provider.publish_state()
            before = self.commands(provider)
            with self.assertRaises((n.BridgeUnavailableError, n.UnsupportedStepError)):
                self.advance(driver, step)
            self.assertEqual(self.commands(provider), before)

    def test_real_native_speed_and_overshoot_failures_cannot_grant_trial_success_or_repeat_resume(self):
        for fault in ("setter_speed", "arm_speed", "overshoot"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                step = self.query(driver)
                with self.assertRaises(n.BridgeUnavailableError):
                    self.advance(driver, step)
                self.assertEqual(self.commands(provider).count("resume-map"), 1 if fault == "overshoot" else 0)
                self.assertTrue(driver._contact_free_exact_route_speed_trial_consumed_v1)

    def test_real_zero_day_modal_cancel_and_one_day_event_keep_original_liveness_semantics(self):
        for fault in ("modal", "event"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                result = self.advance(driver, self.query(driver))
                self.assertEqual(result["timeline_speed"], 5)
                self.assertEqual(self.commands(provider).count("resume-map"), 1)
                if fault == "modal":
                    self.assertEqual(result["elapsed_days"], 0)
                    self.assertEqual(result["progress_status"], "modal_interrupted")
                    self.assertTrue(result["exact_day_native_clock"]["modal_interrupted"])
                    self.assertTrue(any(s.startswith(n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX)
                        for s in self.commands(provider)))
                else:
                    self.assertEqual(result["elapsed_days"], 1)
                    self.assertEqual(result["active_event"]["instance_id"], 1)
                self.assertFalse(any(s.startswith("select-event-option-") for s in self.commands(provider)))

    def test_trial_cannot_change_unavoidable_or_identity_preference_or_endpoint(self):
        driver, _ = self.driver()
        frame = driver.take_internal_semantic_snapshot()
        for kind in ("unavoidable_current_province_contact", "battle_identity_materialization"):
            selected = select_v1(driver, frame, {"proof_kind": kind}, fallback_speed=1)
            self.assertEqual(selected["selected_speed"], 1)
            self.assertEqual(selected["selection_status"], "not_contact_free")
        for date, days in (("1066.10.14", 1), ("1096.9.14", 1), ("1096.9.15", 0)):
            driver, provider = self.driver(date=date)
            result = self.advance(driver, self.query(driver))
            self.assertEqual(result["elapsed_days"], days)
            self.assertEqual(self.commands(provider).count("resume-map"), days)
            if days == 0:
                self.assertEqual(result["progress_status"], "campaign_endpoint_reached")
                self.assertIsNone(result["contact_free_exact_route_speed_trial_v1"]["actual_timeline_speed"])


if __name__ == "__main__":
    unittest.main()
