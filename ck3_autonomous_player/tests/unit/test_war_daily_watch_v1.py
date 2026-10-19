"""Offline actual Driver/Protocol tests; no CK3 process, speed change or RPC."""
import copy
from pathlib import Path
import re
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge import native_driver as n
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.war_daily_watch_v1 import select_war_daily_watch_v1
from ck3_autonomous_player.tests.unit.test_exact_day_native_clock_paused_next_frame import ClockProvider
from ck3_autonomous_player.tests.unit.test_native_bridge_driver import _army, _hello, _snapshot, _war


class WarProvider(ClockProvider):
    def __init__(self, fault=None, state="moving"):
        super().__init__()
        self.fault = fault
        self.actor = 29829
        self.event = self.pending = None
        self.hint = {"status": "absent", "owner_verified": True}
        self.player = _army(101, army_state=state, retreating=state == "retreating",
            in_combat=False, route_province_ids=[11], move_target_province_id=11)
        self.player["owner_character_id"] = self.actor
        self.enemy = _army(31, controllable=False, army_state="regular", in_combat=False,
                           retreating=False, route_province_ids=[])
        self.ally = _army(42, controllable=False, army_state="sieging", in_combat=False,
                          retreating=False, route_province_ids=[])
        self.players = [self.player]
        self.war = _war(allied_armies=[self.player, self.ally], enemy_armies=[self.enemy])
        self.timer = None

    def close(self):
        if self.timer is not None:
            self.timer.join()

    def publish_state(self):
        if self.fault == "ending_speed" and self.date_raw == self.target:
            self.speed = 1
        frame = _snapshot(self.revision, date_raw=self.date_raw, speed=self.speed,
            paused=self.paused, active_event=self.event, pending_character_interaction=self.pending,
            played_character={"character_id": self.actor, "alive": True},
            active_wars=[self.war], player_armies=self.players)
        frame["state"]["top_exclusive_modal_choice_hint"] = copy.deepcopy(self.hint)
        self.publish(frame)

    def reply(self, request, result):
        self.publish({"type": "command_result", "protocol_version": 1,
            "request_id": request["request_id"], "ok": True, "result": result})
        self.publish_state()

    def publish(self, frame):
        result = frame.get("result")
        if isinstance(result, dict) and result.get("step") == n._TACTICAL_DAILY_SENTINEL_STATUS_STEP:
            status = result["tactical_daily_sentinel"]
            faults = {"generation": ("generation", 38), "count": ("army_count", 1),
                "speed": ("speed", 1), "no_pause": ("pause_observed", False),
                "no_wrapper": ("pause_wrapper_called", False), "ticks": ("completed_daily_ticks", 2),
                "overshoot": ("overshoot_days", 1)}
            if self.fault in faults:
                key, value = faults[self.fault]
                status[key] = value
        super().publish(frame)

    def send(self, request):
        step = str(request.get("step"))
        if step.startswith(n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX):
            self.frames.append(request)
            match = re.fullmatch(re.escape(n._TACTICAL_DAILY_SENTINEL_ARM_PREFIX)
                + r"(\d+)-to-(\d+)-speed-([1-5])-mode-terminal-a-(\d+)((?:-\d+)*)", step)
            if match is None or not self.paused:
                raise AssertionError("invalid fake Native arm")
            start, target, speed, count = map(int, match.groups()[:4])
            ids = tuple(int(value) for value in match[5].split("-") if value)
            if start != self.date_raw or target != start + 24 or count != len(ids):
                raise AssertionError("not a next-day bound arm")
            self.target, self.armed = target, True
            self.clock = {"state": "armed", "generation": 37,
                "starting_date_raw": start, "target_date_raw": target,
                "last_observed_date_raw": start, "trigger_date_raw": 0,
                "speed": speed, "mode": "terminal_or_sentinel", "army_count": count,
                "combat_count": 1 if self.fault == "arm_combat" else 0,
                "completed_daily_ticks": 0, "intermediate_pause_count": 0,
                "trigger_flags": 0, "trigger_reasons": [], "signed_date_delta_from_target_raw": 0,
                "overshoot_days": -1, "pause_wrapper_called": False, "pause_observed": False,
                "terminal_observed": False, "abnormal": False}
            if self.fault == "arm_unknown":
                self.publish_state()
                return
            self.reply(request, {"step": step, "accepted": True, "status": "available",
                                 "tactical_daily_sentinel": copy.deepcopy(self.clock)})
        elif step.startswith(n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX):
            self.frames.append(request)
            if self.fault == "cancel_unknown":
                return
            if self.fault == "cancel_owner_change":
                self.actor += 1
                self.revision += 1
            self.reply(request, {"step": step, "accepted": True, "status": "canceled"})
            self.armed = False
        elif step == "set-speed-2" and self.fault in {"setter", "prearm_actor", "prearm_roster"}:
            self.frames.append(request)
            if self.fault != "setter":
                self.speed = 2
            if self.fault == "prearm_actor":
                self.actor += 1
            if self.fault == "prearm_roster":
                self.enemy["current_province_id"] += 1
            self.revision += 1
            self.reply(request, {"step": step, "accepted": True, "status": "submitted"})
        elif step == "resume-map" and self.fault in {
                "event", "event_running", "interaction", "modal", "actor", "episode", "connection",
                "resume_unknown", "cancel_unknown", "cancel_owner_change"}:
            self.frames.append(request)
            self.revision += 1
            if self.fault in {"event", "event_running", "cancel_unknown", "cancel_owner_change"}:
                self.event = {"instance_id": 12, "option_count": 1}
            if self.fault == "event_running":
                self.paused = False
            if self.fault == "interaction":
                self.pending = {"instance_id": 123, "sender_character_id": 808,
                                "auto_accept_notification": False}
            if self.fault == "modal":
                self.hint = {"status": "present", "owner_verified": True,
                    "source": "application_main_pump_observed_modal_receiver",
                    "opaque_root_id": "war-modal", "max_observation_age_ms": 2000}
            if self.fault == "actor":
                self.actor += 1
            if self.fault == "resume_unknown":
                self.publish_state()
                return
            self.reply(request, {"step": step, "accepted": True, "status": "submitted"})
        elif step == "resume-map" and self.fault in {"date_before_pause", "date_event_before_pause"}:
            self.frames.append(request)
            self.date_raw += 24
            self.paused = False
            self.revision += 1
            self.clock.update(state="triggered", last_observed_date_raw=self.date_raw,
                trigger_date_raw=self.date_raw, completed_daily_ticks=1, trigger_flags=1,
                trigger_reasons=["date_deadline"], overshoot_days=0,
                pause_wrapper_called=True, pause_observed=True)
            if self.fault == "date_event_before_pause":
                self.event = {"instance_id": 12, "option_count": 1}
            self.reply(request, {"step": step, "accepted": True, "status": "submitted"})
            def paused_publication():
                self.paused = True
                self.revision += 1
                self.publish_state()
            self.timer = threading.Timer(.005, paused_publication)
            self.timer.start()
        else:
            super().send(request)


class WarDailyWatchTests(unittest.TestCase):
    def driver(self, enabled=True, missing=(), **provider_options):
        provider = WarProvider(**provider_options)
        driver = n.NativeHeadlessGameplayDriver(provider.pipe_name, endpoint=provider,
            allow_war_daily_watch_v1=enabled, command_timeout_seconds=.03,
            life_advance_timeout_seconds=.03)
        caps = {"game.state.snapshot", "game.state.pending-character-interaction",
            "game.command.resume-map", "game.command.pause-map",
            *[f"game.command.set-speed-{speed}" for speed in range(1, 6)],
            n._TACTICAL_DAILY_SENTINEL_ARM_CAPABILITY,
            n._TACTICAL_DAILY_SENTINEL_STATUS_CAPABILITY,
            n._TACTICAL_DAILY_SENTINEL_CANCEL_CAPABILITY}
        hello = _hello(*sorted(caps-set(missing)))
        hello.update(ck3_build_match=True, expected_ck3_version=CK3_12004.game_version,
                     expected_ck3_sha256=CK3_12004.executable_sha256)
        provider.publish(hello)
        provider.publish_state()
        self.addCleanup(driver.close)
        return driver, provider

    @staticmethod
    def commands(provider):
        return [row["step"] for row in provider.frames if row.get("type") == "execute_step"]

    def advance(self, driver):
        return driver.execute_step("life-advance-one-day",
                                   expected_revision=driver.take_snapshot()["revision"])

    def selection(self, driver, snapshot=None, **kwargs):
        caps = driver.state.capabilities()
        values = dict(enabled=True, exact_one_day=True, result_step="life-advance-one-day",
            proof_kind=None, bridge_capabilities=set(caps["bridge_capabilities"]),
            action_steps=set(caps["action_steps"]), assault_in_progress=False)
        values.update(kwargs)
        return select_war_daily_watch_v1(snapshot or driver.take_internal_semantic_snapshot(), **values)

    def test_default_off_and_constructor_requires_explicit_boolean(self):
        driver, provider = self.driver(enabled=False)
        result = self.advance(driver)
        self.assertNotIn("war_daily_watch_v1", result)
        self.assertEqual(result["timeline_speed"], 1)
        self.assertTrue(self.commands(provider)[1].endswith("-a-0"))
        with self.assertRaises(ValueError):
            n.NativeHeadlessGameplayDriver(allow_war_daily_watch_v1=1)

    def test_complete_published_roster_speed_two_native_pause_exact_day(self):
        for state in ("moving", "retreating", "sieging", "regular"):
            with self.subTest(state=state):
                driver, provider = self.driver(state=state)
                result = self.advance(driver)
                commands = self.commands(provider)
                self.assertEqual(commands[0], "set-speed-2")
                self.assertTrue(commands[1].endswith("-speed-2-mode-terminal-a-3-31-42-101"))
                self.assertEqual(commands.count("resume-map"), 1)
                self.assertNotIn("pause-map", commands)
                self.assertEqual(result["timeline_policy"], "war_daily_watch_v1")
                self.assertEqual(result["elapsed_days"], 1)
                self.assertTrue(result["paused"])
                self.assertEqual(result["ending_date_raw"]-result["starting_date_raw"], 24)
                self.assertFalse(result["war_daily_watch_v1"]["live_qualification_claimed"])
                self.assertFalse(driver.allow_route_contact_high_speed_ab)

    def test_admission_rejects_unknown_partial_overflow_and_unrelated_scopes(self):
        driver, _ = self.driver()
        original = driver.take_internal_semantic_snapshot()
        self.assertIsNotNone(self.selection(driver, original))
        changes = [
            lambda s: s.update(paused=False), lambda s: s.pop("native_revision"),
            lambda s: s.update(snapshot_id="native:wrong"), lambda s: s.update(one_life_terminal=None),
            lambda s: s.update(active_event={}), lambda s: s.update(pending_character_interaction={}),
            lambda s: s.pop("top_exclusive_modal_choice_hint"),
            lambda s: s["played_character"].update(alive=False),
            lambda s: s.update(episode_character_id=99),
            lambda s: s["diagnostics"].update(connection_generation=0),
            lambda s: s["diagnostics"]["hello"].update(expected_ck3_sha256="0"*64),
            lambda s: s["active_wars"][0].pop("enemy_armies"),
            lambda s: s["active_wars"][0]["enemy_armies"][0].update(in_combat=True),
            lambda s: s["active_wars"][0]["enemy_armies"][0].pop("retreating"),
            lambda s: s["player_armies"][0].update(army_state="embarked"),
            lambda s: s["player_armies"][0].update(army_state={}),
            lambda s: s["player_armies"][0].update(army_state_code=4),
            lambda s: s["player_armies"][0].update(owner_character_id=99),
            lambda s: s["player_armies"].append(copy.deepcopy(s["player_armies"][0])),
            lambda s: s["active_wars"][0]["enemy_armies"].extend([
                {**s["active_wars"][0]["enemy_armies"][0], "army_id": 1000+i} for i in range(64)]),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                value = copy.deepcopy(original)
                change(value)
                self.assertIsNone(self.selection(driver, value))
        for options in ({"enabled": False}, {"exact_one_day": False}, {"result_step": "life-advance"},
                {"proof_kind": "contact_free"}, {"assault_in_progress": True},
                {"bridge_capabilities": set()}, {"action_steps": {"resume-map", "pause-map"}}):
            with self.subTest(options=options):
                self.assertIsNone(self.selection(driver, **options))

    def test_setter_actual_readback_and_prearm_owner_roster_changes_do_not_resume(self):
        for fault in ("setter", "prearm_actor", "prearm_roster", "arm_combat"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                with self.assertRaises(n.BridgeUnavailableError):
                    self.advance(driver)
                self.assertNotIn("resume-map", self.commands(provider))
                self.assertTrue(driver._war_daily_watch_pending_v1)

    def test_native_stop_receipt_fields_remain_mandatory(self):
        for fault in ("generation", "count", "speed", "ending_speed", "no_pause", "no_wrapper", "ticks", "overshoot"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                with self.assertRaises(n.BridgeUnavailableError):
                    self.advance(driver)
                self.assertEqual(self.commands(provider).count("resume-map"), 1)
                self.assertTrue(driver._war_daily_watch_pending_v1)

    def test_date_publication_before_native_pause_does_not_issue_python_pause(self):
        for fault in ("date_before_pause", "date_event_before_pause"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                result = self.advance(driver)
                self.assertEqual(result["elapsed_days"], 1)
                self.assertNotIn("pause-map", self.commands(provider))

    def test_mandatory_same_owner_zero_day_boundary_cancels_same_generation(self):
        for fault in ("event", "event_running", "interaction", "modal"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                try:
                    result = self.advance(driver)
                except Exception as error:
                    raise AssertionError(f"boundary fault={fault}: {error}") from error
                commands = self.commands(provider)
                self.assertEqual(result["elapsed_days"], 0)
                self.assertEqual(result["progress_status"], "boundary_interrupted")
                self.assertEqual(commands.count("resume-map"), 1)
                self.assertIn(n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX+"37", commands)
                self.assertIn("boundary_interrupted", result["exact_day_native_clock"])
                self.assertFalse(driver._war_daily_watch_pending_v1)

    def test_actor_episode_connection_boundaries_stop_without_replay(self):
        for fault in ("actor", "episode", "connection"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                original = driver.take_internal_semantic_snapshot
                def snapshot():
                    value = original()
                    if any(r.get("step") == "resume-map" for r in provider.frames):
                        if fault == "episode":
                            value["episode_run_id"] = "changed"
                        if fault == "connection":
                            value["diagnostics"]["connection_generation"] += 1
                    return value
                with patch.object(driver, "take_internal_semantic_snapshot", side_effect=snapshot):
                    with self.assertRaises(n.BridgeUnavailableError):
                        self.advance(driver)
                commands = self.commands(provider)
                self.assertEqual(commands.count("resume-map"), 1)
                if fault == "connection":
                    self.assertFalse(any(step.startswith(n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX)
                                         for step in commands))

    def test_unknown_resume_or_cancel_is_not_replayed_and_latches_failure(self):
        for fault in ("arm_unknown", "resume_unknown", "cancel_unknown", "cancel_owner_change"):
            with self.subTest(fault=fault):
                driver, provider = self.driver(fault=fault)
                with self.assertRaises(n.BridgeUnavailableError):
                    self.advance(driver)
                before = self.commands(provider)
                self.assertEqual(before.count("resume-map"), 0 if fault == "arm_unknown" else 1)
                self.assertLessEqual(sum(s.startswith(n._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX) for s in before), 1)
                with self.assertRaisesRegex(n.BridgeUnavailableError, "unresolved"):
                    self.advance(driver)
                self.assertEqual(before, self.commands(provider))

    def test_existing_history_persists_unknown_marker_and_blocks_a_restored_candidate(self):
        driver, _ = self.driver(fault="resume_unknown")
        with self.assertRaises(n.StepPostconditionError):
            self.advance(driver)
        rows = copy.deepcopy(driver._command_history)
        self.assertTrue(rows[-1]["result"]["never_replay"])
        restored, provider = self.driver()
        with restored._history_lock:
            restored._command_history = rows
        with self.assertRaisesRegex(n.BridgeUnavailableError, "unresolved"):
            self.advance(restored)
        self.assertEqual(self.commands(provider), [])

    def test_restored_unknown_marker_blocks_generic_day_even_when_candidate_is_disabled(self):
        driver, _ = self.driver(fault="resume_unknown")
        with self.assertRaises(n.StepPostconditionError):
            self.advance(driver)
        rows = copy.deepcopy(driver._command_history)
        restored, provider = self.driver(enabled=False)
        with restored._history_lock:
            restored._command_history = rows
        with self.assertRaisesRegex(n.BridgeUnavailableError, "unresolved"):
            self.advance(restored)
        self.assertEqual(self.commands(provider), [])


if __name__ == "__main__":
    unittest.main()
