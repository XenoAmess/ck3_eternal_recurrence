"""Same-frame no-op removal, exercised through the actual native day clock.

All observations use an in-memory protocol provider; no CK3, disk state, or
timing benchmark is involved. Revision counters may differ by the removed
command; the native Arm/Resume/Status and exact paused day must stay intact.
"""
from copy import deepcopy
import inspect
import json
from pathlib import Path
import sys
import textwrap
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.exact_day_speed_configuration_v1 import (
    _binding, prepare_exact_day_speed_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004
from test_exact_day_native_clock_paused_next_frame import ClockProvider


OLD = '''            speed_step = f"set-speed-{speed}"
            speed_result = self._execute_composite_primitive(speed_step, current)
            actions.append({"step": speed_step, "result": speed_result})
            current = self._wait_for_life_advance_snapshot(
                self.take_internal_semantic_snapshot(),
                lambda snapshot: snapshot.get("speed") == speed,
                timeout_seconds=self.command_timeout_seconds,
            )
            if current.get("speed") != speed:
                raise BridgeUnavailableError("exact-day clock did not observe its speed")'''
NEW = '''            from .exact_day_speed_configuration_v1 import prepare_exact_day_speed_v1
            current = prepare_exact_day_speed_v1(
                self, current, speed=speed, actions=actions)'''


def clock_method(candidate):
    source = inspect.getsource(nd.NativeHeadlessGameplayDriver._advance_exact_day_with_sentinel)
    if NEW in source:
        source = source.replace(NEW, OLD, 1)
    if source.count(OLD) != 1:
        raise ValueError("exact-day source anchor changed")
    if candidate:
        source = source.replace(OLD, NEW, 1)
    namespace = dict(vars(nd))
    exec(compile(textwrap.dedent(source), "<exact-day-clock-software-pair>", "exec"), namespace)
    return namespace["_advance_exact_day_with_sentinel"]


def frame(speed=5):
    return {
        "backend_id": "native-headless", "source": "injected-dll-named-pipe",
        "revision": 7, "native_revision": 6, "snapshot_id": "native:6",
        "date_raw": 53202744, "speed": speed, "paused": True, "map_ready": True,
        "played_character": {"character_id": 40526, "alive": True},
        "episode_character_id": 40526, "episode_run_id": "synthetic-episode",
        "local_player_id": 1, "diagnostics": {
            "connected": True, "bridge_pid": 4242, "connection_generation": 1,
            "hello": {"ck3_build_match": True,
                      "expected_ck3_version": CK3_12004.game_version,
                      "expected_ck3_sha256": CK3_12004.executable_sha256},
        },
    }


class SpeedDriver:
    command_timeout_seconds = 0.1

    def __init__(self, current, error=None):
        self.current = current
        self.error = error
        self.calls = []

    def take_internal_semantic_snapshot(self):
        self.calls.append("snapshot")
        return self.current

    def _execute_composite_primitive(self, step, starting):
        self.calls.append(step)
        if self.error is not None:
            raise self.error
        self.current = {**self.current, "speed": int(step.rsplit("-", 1)[1])}
        return {"step": step, "accepted": True}

    def _wait_for_life_advance_snapshot(self, current, predicate, **options):
        self.calls.append("speed-wait")
        if not predicate(current):
            raise ValueError("synthetic speed mismatch")
        return current


class BoundClockProvider(ClockProvider):
    arm_speed_error = False

    def publish(self, message):
        if message.get("type") == "state_snapshot":
            message["state"]["local_player_id"] = 1
        if (self.arm_speed_error and message.get("type") == "command_result"
                and message.get("result", {}).get("tactical_daily_sentinel", {}).get("state") == "armed"):
            message["result"]["tactical_daily_sentinel"]["speed"] = 2
        super().publish(message)


def connected_driver(start_speed, arm_speed_error=False):
    provider = BoundClockProvider()
    provider.speed = start_speed
    provider.arm_speed_error = arm_speed_error
    driver = nd.NativeHeadlessGameplayDriver(
        provider.pipe_name, endpoint=provider,
        command_timeout_seconds=0.1, life_advance_timeout_seconds=0.1)
    provider.publish({
        "type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
        "pid": 4242, "session_generation": 0,
        "ck3_build_match": True, "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
        "capabilities": ["game.state.snapshot", "game.command.pause-map",
            "game.command.resume-map", *[f"game.command.set-speed-{i}" for i in range(1, 6)],
            "game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1",
            "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N"],
    })
    provider.publish_state()
    return provider, driver


class SameSpeedConfigurationTests(unittest.TestCase):
    def test_complete_same_frame_skips_only_setter_and_speed_wait(self):
        original = frame()
        before = deepcopy(original)
        driver = SpeedDriver(deepcopy(original))
        actions = []
        result = prepare_exact_day_speed_v1(driver, original, speed=5, actions=actions)
        self.assertIs(result, driver.current)
        self.assertEqual(driver.calls, ["snapshot"])
        self.assertEqual(len(actions), 1)
        audit = json.loads(json.dumps(actions, allow_nan=False))[0]
        self.assertEqual(audit["step"], "set-speed-5")
        observed = audit["result"]
        self.assertEqual({key: observed[key] for key in ("status", "submitted", "accepted", "observed_speed",
            "source_snapshot_id", "source_native_revision", "source_date_raw")},
            {"status": "already_observed", "submitted": False, "accepted": None, "observed_speed": 5,
             "source_snapshot_id": original["snapshot_id"], "source_native_revision": original["native_revision"],
             "source_date_raw": original["date_raw"]})
        proof = observed["observation_proof"]
        self.assertEqual(proof["starting_speed"], proof["revalidated_speed"])
        self.assertIs(proof["observation_only"], True)
        binding = proof["same_frame_binding"]
        self.assertEqual(binding, {"revision": 7, "native_revision": 6, "date_raw": 53202744,
            "actor_character_id": 40526, "episode_character_id": 40526, "local_player_id": 1,
            "bridge_pid": 4242, "connection_generation": 1, "snapshot_id": "native:6",
            "episode_run_id": "synthetic-episode", "backend_id": "native-headless",
            "source": "injected-dll-named-pipe", "paused": True, "map_ready": True,
            "actor_alive": True, "connected": True, "build": {
                "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256}})
        driver.current["diagnostics"]["connection_generation"] = 99
        self.assertEqual(actions[0]["result"]["observation_proof"]["same_frame_binding"]["connection_generation"], 1)
        self.assertEqual(original, before)

    def test_different_speed_preserves_original_path(self):
        driver = SpeedDriver(frame(1))
        actions = []
        result = prepare_exact_day_speed_v1(driver, frame(1), speed=5, actions=actions)
        self.assertEqual(driver.calls, ["set-speed-5", "snapshot", "speed-wait"])
        self.assertEqual(result["speed"], 5)
        self.assertEqual(actions, [{"step": "set-speed-5", "result": {
            "step": "set-speed-5", "accepted": True}}])

    def test_incomplete_foreign_and_wrong_typed_start_never_skip(self):
        cases = [{"backend_id": "foreign"}, {"snapshot_id": "native:99"},
                 {"revision": True}, {"speed": True}, {"speed": "5"},
                 {"local_player_id": None}, {"episode_run_id": ""}]
        for changes in cases:
            with self.subTest(changes=changes):
                original = {**frame(), **changes}
                driver = SpeedDriver(frame())
                prepare_exact_day_speed_v1(driver, original, speed=5, actions=[])
                self.assertEqual(driver.calls, ["set-speed-5", "snapshot", "speed-wait"])

    def test_stale_foreign_and_build_changed_fresh_frame_preserve_rejection(self):
        cases = [{"revision": 8}, {"native_revision": 8, "snapshot_id": "native:8"},
                 {"episode_run_id": "foreign"}, {"backend_id": "foreign"},
                 {"diagnostics": {**frame()["diagnostics"], "bridge_pid": 7777}},
                 {"diagnostics": {**frame()["diagnostics"], "hello": {"ck3_build_match": False}}}]
        for changes in cases:
            with self.subTest(changes=changes):
                error = BridgeUnavailableError("native gameplay revision mismatch")
                driver = SpeedDriver({**frame(), **changes}, error)
                actions = []
                with self.assertRaises(BridgeUnavailableError) as caught:
                    prepare_exact_day_speed_v1(driver, frame(), speed=5, actions=actions)
                self.assertIs(caught.exception, error)
                self.assertEqual(driver.calls, ["snapshot", "set-speed-5"])
                self.assertEqual(actions, [])
        for changes in ({"local_player_id": None}, {"episode_run_id": ""}, {"revision": True}):
            with self.subTest(missing_start=changes):
                driver = SpeedDriver(frame(), BridgeUnavailableError("original setter refusal"))
                actions = []
                with self.assertRaisesRegex(BridgeUnavailableError, "original setter refusal"):
                    prepare_exact_day_speed_v1(driver, {**frame(), **changes}, speed=5, actions=actions)
                self.assertEqual(driver.calls, ["set-speed-5"])
                self.assertEqual(actions, [])

    def test_changed_or_unavailable_fresh_speed_rejects_without_command(self):
        for speed in (1, True, "5", None):
            with self.subTest(speed=speed):
                driver = SpeedDriver(frame(speed))
                with self.assertRaisesRegex(BridgeUnavailableError, "no resume"):
                    prepare_exact_day_speed_v1(driver, frame(), speed=5, actions=[])
                self.assertEqual(driver.calls, ["snapshot"])

    def run_clock(self, candidate, start_speed, target_speed, arm_error=False):
        provider, driver = connected_driver(start_speed, arm_error)
        try:
            starting = driver.take_internal_semantic_snapshot()
            self.assertIsNotNone(_binding(starting), "synthetic native frame must qualify the fast path")
            actions = []
            with patch.object(nd.NativeHeadlessGameplayDriver, "_advance_exact_day_with_sentinel", clock_method(candidate)):
                with patch.object(driver, "_wait_for_life_advance_snapshot", wraps=driver._wait_for_life_advance_snapshot) as wait:
                    if arm_error:
                        with self.assertRaises(BridgeUnavailableError):
                            driver._advance_exact_day_with_sentinel(starting, speed=target_speed, actions=actions)
                        result = None
                    else:
                        result = driver._advance_exact_day_with_sentinel(starting, speed=target_speed, actions=actions)
                    calls = wait.call_count
            commands = [row["step"] for row in provider.frames if row.get("type") == "execute_step"]
            return commands, calls, result, actions
        finally:
            driver.close()

    def test_real_clock_same_speed_keeps_arm_resume_status_and_exact_paused_day(self):
        for speed in (1, 5):
            with self.subTest(speed=speed):
                old = self.run_clock(False, speed, speed)
                new = self.run_clock(True, speed, speed)
                self.assertEqual(old[0][0], f"set-speed-{speed}")
                self.assertEqual(old[0][1:], new[0])
                self.assertEqual(old[1] - new[1], 1)
                self.assertEqual(new[0][1:], ["resume-map", "research-query-tactical-daily-sentinel-v1"])
                self.assertEqual(old[2][1], new[2][1])
                for field in ("date_raw", "paused", "speed", "map_ready", "played_character"):
                    self.assertEqual(old[2][0][field], new[2][0][field])
                self.assertTrue(new[2][0]["paused"])
                self.assertEqual(new[2][1]["stopped"]["completed_daily_ticks"], 1)
                self.assertEqual(new[2][1]["stopped"]["overshoot_days"], 0)
                self.assertEqual([row["step"] for row in old[3]], [row["step"] for row in new[3]])
                self.assertIsNone(new[3][0]["result"]["accepted"])

    def test_observation_row_matches_real_route_and_window_four_row_consumers(self):
        # Canonical consumers, not a copied speed predicate. Route data is the
        # existing closed classifier fixture; window fields are synthetic.
        tools = Path(__file__).resolve().parents[3] / "tools/g2_saved_campaign"
        sys.path.insert(0, str(tools))
        from route_contact_exact_day_outcome import classify_route_contact_horizon_one_day_v1
        from route_window_advance_outcome import classify_route_contact_window_advance_v1
        from xar_autoplayer.bridge.route_contact_window_contract import (
            advance_route_contact_window_step, parse_advance_route_contact_window_step)
        data = json.loads((tools / "fixtures/route10416_closed_classifier_inputs_v1.json").read_text(encoding="utf-8"))
        body = deepcopy(data["actual_three"]["body"])
        binding = body["planning_source_frame"]
        start = frame(3)
        for name in ("revision", "native_revision", "snapshot_id", "date_raw", "episode_run_id"):
            start[name] = binding[name]
        start["played_character"]["character_id"] = start["episode_character_id"] = binding["actor_character_id"]
        for name in ("bridge_pid", "connection_generation"):
            start["diagnostics"][name] = binding[name]
        rows = []
        speed_driver = SpeedDriver(deepcopy(start))
        prepare_exact_day_speed_v1(speed_driver, start, speed=3, actions=rows)
        self.assertEqual(speed_driver.calls, ["snapshot"])
        body["result"]["actions"].insert(0, rows[0])
        def bound(candidate, **kwargs):
            self.assertEqual(candidate["planning_source_frame"], binding)
            return deepcopy(binding)
        route = classify_route_contact_horizon_one_day_v1(body, bind_gameplay_frame=bound,
            initial_frame=binding, game_pid=binding["bridge_pid"])
        self.assertEqual(len(body["result"]["actions"]), 4)
        self.assertFalse(route["primitive_accepted"])
        self.assertFalse(route["action_credit"])
        self.assertEqual(route["actual_elapsed_days"], 1)
        # Build a lawful two-day frozen-route window, reusing only fixture IDs.
        window = deepcopy(body)
        plan, result = window["plan"], window["result"]
        horizon = plan["route_audit"]["contact_horizon"]
        subject, target, enemies = horizon["subject_army_id"], horizon["target_province_id"], horizon["hostile_army_ids"]
        step = advance_route_contact_window_step(subject, target, enemies, horizon_days=2)
        window["selected_step"] = plan["selected_step"] = result["step"] = step
        plan["route_contact_window_days"] = 2
        end = start["date_raw"] + 48
        watches = sorted({row["army_id"] for war in result["war_progress_before"]["wars"]
            for side in ("player_armies", "enemy_armies") for row in war[side]
            if side == "player_armies" or row.get("retreating") is not True})
        result.update(source="native-tactical-daily-sentinel-composite", sentinel_scope="route_contact_window",
            stop_kind="decision_epoch", terminal_reached=False, one_life_terminal=False, played_character_alive=True,
            player_decision_boundary=None, player_decision_boundary_cancel=None,
            played_character_id=binding["actor_character_id"], episode_character_id=binding["actor_character_id"],
            episode_run_id=binding["episode_run_id"], bridge_pid=binding["bridge_pid"],
            connection_generation=binding["connection_generation"], native_revision=binding["native_revision"] + 2,
            ending_date_raw=end, ending_date={"date_raw": end}, target_date_raw=end, elapsed_days=2,
            requested_horizon_days=2, completed_daily_ticks=2, overshoot_days=0,
            timeline_policy="terminal_or_sentinel", sentinel_mode="terminal_or_sentinel",
            route_contact_window_context_basis="frozen_current_routes", watch_army_ids=watches,
            route_contact_window={"status": "available", "context_basis": "frozen_current_routes", "horizon_days": 2,
                "window_start_date_raw": start["date_raw"], "window_end_date_raw": end,
                "contact_free": True, "missing": [], "conflicts": [], "contact_free_whole_days": 2},
            managed_failure_cleanup={"attempted": False, "error": None})
        result["war_progress_after"]["date_raw"] = end
        arm, stopped = result["exact_day_native_clock"]["armed"], result["exact_day_native_clock"]["stopped"]
        for value in (arm, stopped):
            value.update(target_date_raw=end, army_count=len(watches))
        stopped.update(last_observed_date_raw=end, trigger_date_raw=end, completed_daily_ticks=2)
        arm_step = (f"research-arm-tactical-daily-sentinel-v1-{start['date_raw']}-to-{end}-speed-3-"
                    f"mode-terminal-a-{len(watches)}-" + "-".join(map(str, watches)))
        result["actions"][1]["step"] = result["actions"][1]["result"]["step"] = arm_step
        result["actions"][1]["result"]["tactical_daily_sentinel"] = arm
        result["actions"][3]["result"]["tactical_daily_sentinel"] = stopped
        result.update(armed_tactical_daily_sentinel=arm, tactical_daily_sentinel=stopped,
            sentinel_generation=arm["generation"], trigger_reasons=stopped["trigger_reasons"],
            intermediate_pause_count=stopped["intermediate_pause_count"])
        credit = classify_route_contact_window_advance_v1(window, bind_gameplay_frame=bound,
            parse_advance_step=parse_advance_route_contact_window_step,
            validate_sentinel_stop=nd._validate_tactical_daily_sentinel_stop,
            initial_frame=binding, game_pid=binding["bridge_pid"])
        self.assertEqual(len(result["actions"]), 4)
        self.assertEqual(credit["actual_elapsed_days"], 2)
        self.assertFalse(credit["primitive_accepted"])
        self.assertFalse(credit["business_success_inferred"])
        commands, _, observed, clock_rows = self.run_clock(True, 3, 3)
        self.assertEqual(len(commands), 3)
        self.assertEqual(len(clock_rows), 4)
        self.assertIsNone(clock_rows[0]["result"]["accepted"])
        self.assertEqual(observed[1]["stopped"]["completed_daily_ticks"], 1)

    def test_real_clock_different_speed_keeps_original_protocol(self):
        old = self.run_clock(False, 1, 5)
        new = self.run_clock(True, 1, 5)
        self.assertEqual(old[0], new[0])
        self.assertEqual(old[1], new[1])
        self.assertEqual(old[2][1], new[2][1])

    def test_actual_arm_speed_mismatch_still_rejects_before_resume(self):
        for candidate in (False, True):
            commands, _, _, _ = self.run_clock(candidate, 5, 5, True)
            self.assertNotIn("resume-map", commands)
            self.assertEqual(sum(step.startswith("research-arm-") for step in commands), 1)

    def test_public_stale_revision_rejection_is_unchanged(self):
        for candidate in (False, True):
            provider, driver = connected_driver(5)
            try:
                before = driver.take_snapshot()
                with patch.object(nd.NativeHeadlessGameplayDriver, "_advance_exact_day_with_sentinel", clock_method(candidate)):
                    with self.assertRaises(BridgeUnavailableError):
                        driver.execute_step("life-advance-one-day", expected_revision=before["revision"] + 1)
                self.assertEqual([row for row in provider.frames
                                  if row.get("type") == "execute_step"], [])
            finally:
                driver.close()


if __name__ == "__main__":
    unittest.main()
