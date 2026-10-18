"""Synthetic endpoints; actual Service, stop producer/validator and Sway consumers."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_ordinary_sway_quiet_observation_v1 import SourceDriver, seed, service, ACTOR, DATE
from test_native_bridge_driver import _tactical_sentinel_status
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge import ordinary_sway_quiet_observation_v1 as quiet
from xar_autoplayer.bridge.ordinary_sway_hold_observation_v1 import KEY, observe_sway_after_stationary_hold_v1
from xar_autoplayer.bridge.ordinary_sway_service_v1 import INPUT, STATE_FILE, project_ordinary_sway_input_v1
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import war_objective_hold_sentinel_advance_step
from xar_autoplayer.strategy import _battle_sentinel_advance_validation
from xar_autoplayer.sway_formal_consumer import LEDGER_FILE, read_sway_ledger


def plan(driver):
    frame = driver.frame
    target = frame["date_raw"] + 24
    return {"snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
        "planning_source_frame": GameplayBridgeService._observed_planning_source_frame(frame),
        INPUT: project_ordinary_sway_input_v1(frame, None),
        "plan": {"selected_step": war_objective_hold_sentinel_advance_step(61, 10, 2635, target),
                 "phase": "native_war_stationary_objective_hold_sentinel", "war_id": 61,
                 "subject_army_id": 10, "objective_province_id": 2635,
                 "absolute_target_date_raw": target, "watch_army_ids": [10]}}


class HoldDriver(SourceDriver):
    def __init__(self, path):
        super().__init__(path)
        self.frame.update(active_event=None, pending_character_interaction=None, one_life_terminal=False)
        self.frame["player_armies"][0].update(controllable=True, army_state="regular",
            current_province_id=2635, move_target_province_id=None, route_province_ids=[])
        self.frame["active_wars"] = [{"war_id": 61, "war_objective_province_ids": [2635]}]
        self.corrupt = None

    def execute_step(self, step, *, expected_revision):
        self.calls.append("original-hold")
        assert expected_revision == self.frame["revision"] and step == plan(self)["plan"]["selected_step"]
        start = deepcopy(self.frame)
        self.frame["date_raw"] += 24
        self.frame["revision"] += 1
        self.frame["native_revision"] += 1
        self.frame["snapshot_id"] = "hold:" + str(self.frame["native_revision"])
        args = dict(generation=7, starting_date_raw=start["date_raw"], target_date_raw=self.frame["date_raw"],
                    speed=3, mode="decision_epoch", army_count=1, combat_count=0)
        armed = _tactical_sentinel_status(state="armed", observed_date_raw=start["date_raw"], **args)
        stopped = _tactical_sentinel_status(state="triggered", observed_date_raw=self.frame["date_raw"],
            completed_daily_ticks=1, trigger_flags=1, trigger_reasons=["date_deadline"],
            overshoot_days=0, pause_wrapper_called=True, pause_observed=True, **args)
        request = (61, 10, 2635, self.frame["date_raw"])
        scope = lambda frame: native._battle_sentinel_stationary_objective_hold_state(
            frame, (10,), war_id=61, subject_army_id=10, objective_province_id=2635)
        result = native._battle_sentinel_step_result(step=step, starting=start, ending=self.frame,
            target_date_raw=request[3], speed=3, status_mode="decision_epoch",
            sentinel_scope="stationary_objective_hold", watch_army_ids=(10,), arm_status=armed,
            sentinel_status=stopped, actions=[], progress_status="postcondition", cleanup_error=None,
            objective_hold_request=request, objective_hold_admission=scope(start),
            objective_hold_post_stop=scope(self.frame), player_decision_boundary=None,
            player_decision_boundary_cancel=None)
        assert _battle_sentinel_advance_validation(result)["valid"]
        if self.corrupt:
            self.corrupt(result, self.frame)
        return result


class HoldObservationTests(unittest.TestCase):
    def test_real_auto_hold_then_due_named_gain_keeps_original_planning_source(self):
        with tempfile.TemporaryDirectory(prefix="sway-hold-") as temp:
            path = Path(temp); seed(path); driver = HoldDriver(path)
            cues = []
            with patch.object(GameplayBridgeService, "_plan_turn_internal", lambda _: plan(driver)):
                first = service(driver).auto_turn(before_submit=lambda cue: cues.append(deepcopy(cue)))
                self.assertEqual(first[KEY]["new_game_days"], 0)
                self.assertEqual(first["planning_source_frame"]["date_raw"], DATE)
                self.assertEqual(first["result"]["ending_date_raw"], DATE + 24)
                self.assertLess(driver.calls.index("original-hold"), driver.calls.index("completion"))
                count = driver.calls.count("completion")
                second = service(driver).auto_turn()
                self.assertNotIn(KEY, second)
                self.assertEqual(driver.calls.count("completion"), count)
                driver.frame["date_raw"] = DATE + 30 * 24  # Explicit synthetic later frame.
                driver.value = 25
                gained = service(driver).auto_turn()
                witness = read_sway_ledger(path)["resolved"]["first_named_gain_intervention"]
                self.assertTrue(witness["incremental_named_gain_observed"])
                self.assertFalse(witness["next_turn_consumed"])
                self.assertEqual(witness["source_date_raw"], DATE + 31 * 24)
                self.assertEqual(gained[KEY]["schedule_window"], "after_verified_stationary_objective_hold")
                self.assertEqual(driver.calls.count("original-hold"), 3)
                self.assertEqual(driver.calls.count("completion"), 2)
                self.assertEqual(cues[0]["snapshot_id"], "quiet:7")

    def test_bad_identity_fourtuple_invalidated_boundary_and_cleanup_do_not_read_sway(self):
        changes = [
            lambda r, f: r.update(connection_generation=3),
            lambda r, f: f["diagnostics"].update(connection_generation=3),
            *[lambda r, f, key=key: r.update({key: "foreign" if key == "snapshot_id" else r[key] + 1})
              for key in ("snapshot_id", "revision", "native_revision")],
            lambda r, f: f.update(date_raw=f["date_raw"] + 24),
            lambda r, f: r["war_objective_hold_post_stop"].update(status="invalidated"),
            lambda r, f: r["war_objective_hold_admission"].update(status="invalidated"),
            lambda r, f: r.update(player_decision_boundary={"kind": "active_event"}),
            lambda r, f: r["managed_failure_cleanup"].update(attempted=True),
            lambda r, f: f["player_armies"][0].update(in_combat=True),
            lambda r, f: f["player_armies"][0].update(retreating=True),
            lambda r, f: f["active_wars"][0].update(war_objective_province_ids=[2636]),
            lambda r, f: f.update(one_life_terminal=True),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)), tempfile.TemporaryDirectory(prefix="sway-hold-") as temp:
                path = Path(temp); seed(path); driver = HoldDriver(path); driver.corrupt = change
                original = plan(driver); frozen = deepcopy(original)
                result = driver.execute_step(original["plan"]["selected_step"], expected_revision=original["revision"])
                outcome = {"status": "executed", "selected_step": result["step"], "result": result}
                returned = observe_sway_after_stationary_hold_v1(service(driver), original, outcome)
                self.assertIs(returned, outcome)
                self.assertEqual(original, frozen)
                self.assertNotIn("completion", driver.calls)
                self.assertFalse((path / STATE_FILE).exists())

    def test_inactive_pending_monthly_and_terminal_add_zero_snapshots(self):
        for gate in ("empty", "pending", "monthly", "terminal", "disabled"):
            with self.subTest(gate=gate), tempfile.TemporaryDirectory(prefix="sway-hold-") as temp:
                path = Path(temp); driver = HoldDriver(path)
                if gate != "empty": seed(path)
                if gate in ("pending", "terminal"):
                    ledger = read_sway_ledger(path)
                    if gate == "pending": ledger["pending"] = {"action_id": "unknown"}
                    else: ledger["resolved"]["terminal_intervention"] = {"instance_terminal_outcome_observed": True}
                    (path / LEDGER_FILE).write_text(json.dumps(ledger), encoding="utf-8")
                if gate == "monthly":
                    (path / STATE_FILE).write_text(json.dumps({"actor_character_id": ACTOR,
                        "last_observation_attempt_action_id": "original-once", "last_check_date_raw": DATE,
                        "next_check_date_raw": DATE + 30 * 24}), encoding="utf-8")
                if gate == "disabled":
                    driver.allow_private_active_scheme_sway_completion_query = False
                    driver.allow_private_active_scheme_sway_outcome_opinion_query = False
                original = plan(driver)
                result = driver.execute_step(original["plan"]["selected_step"], expected_revision=original["revision"])
                outcome = {"status": "executed", "selected_step": result["step"], "result": result}
                driver.calls.clear()
                self.assertIs(observe_sway_after_stationary_hold_v1(service(driver), original, outcome), outcome)
                self.assertEqual(driver.calls, [])

    def test_schedule_persist_failure_keeps_completed_hold_and_never_replays(self):
        with tempfile.TemporaryDirectory(prefix="sway-hold-") as temp:
            path = Path(temp); seed(path); driver = HoldDriver(path)
            with patch.object(GameplayBridgeService, "_plan_turn_internal", lambda _: plan(driver)), \
                 patch.object(quiet, "_finish", side_effect=OSError("synthetic optional state write")):
                returned = service(driver).auto_turn()
            self.assertEqual(returned["status"], "executed")
            self.assertEqual(returned["result"]["elapsed_days"], 1)
            self.assertEqual(returned[KEY]["status"], "unavailable")
            self.assertFalse(returned[KEY]["request_retried"])
            self.assertEqual(driver.calls.count("original-hold"), 1)


if __name__ == "__main__":
    unittest.main()
