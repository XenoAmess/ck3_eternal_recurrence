"""The actual P18 typed failure must not become a prediction or a retry loop."""
from pathlib import Path
import copy
import json
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import strategy
from xar_autoplayer.bridge import battle_reader_watch_v1 as watch
from xar_autoplayer.bridge import native_driver as driver
from xar_autoplayer.bridge.service import GameplayBridgeService


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/battle_reader_p18_actual_projection.json"


def actual():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def next_day(snapshot):
    answer = copy.deepcopy(snapshot)
    answer["date_raw"] += 24
    answer["revision"] += 1
    answer["native_revision"] += 1
    answer["snapshot_id"] = "native:" + str(answer["native_revision"])
    return answer


def error_for(snapshot, step):
    raw = copy.deepcopy(actual()["unavailable"])
    raw["native_request"]["step"] = step
    raw["native_request"]["expected_revision"] = snapshot["native_revision"]
    return driver._NativeCommandRejectedError(
        raw["native_command_result"]["error"],
        native_request_id=raw["native_request"]["request_id"],
        native_request_frame=raw["native_request"],
        native_command_result_frame=raw["native_command_result"],
    )


def clock(before, after):
    return {"command": "life-advance-one-day", "ok": True, "result": {
        "step": "life-advance-one-day", "starting_date_raw": before["date_raw"],
        "ending_date_raw": after["date_raw"],
        "war_progress_before": driver._war_progress_summary(before),
        "war_progress_after": driver._war_progress_summary(after),
    }}


def select(snapshot, rows):
    return watch.select_watch(snapshot, rows, command=strategy._effective_command,
                              result=strategy._effective_command_result)


class BattleReaderUnavailableWatch(unittest.TestCase):
    def setUp(self):
        fixture = actual()
        self.snapshot, self.dto = fixture["semantic"], fixture["unavailable"]
        self.step = self.dto["step"]
        self.rows = [{"command": self.step, "ok": False, "result": self.dto}]

    def test_actual_native_failure_uses_one_read_and_keeps_raw_evidence(self):
        calls = []
        def reject(*args, **kwargs):
            calls.append((args, kwargs))
            raise error_for(self.snapshot, self.step)
        fake = SimpleNamespace(
            take_snapshot=lambda **kwargs: copy.deepcopy(self.snapshot),
            take_internal_semantic_snapshot=lambda: copy.deepcopy(self.snapshot),
            capabilities=lambda: {"bridge_capabilities": []}, _execute_primitive_step=reject,
        )
        result = driver.NativeHeadlessGameplayDriver._execute_battle_control_snapshot_v1_query(
            fake, self.step, expected_revision=self.snapshot["revision"],
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(result, self.dto)
        self.assertIsNone(result["battle_control_snapshot"])
        self.assertFalse(result["prediction_ready"])
        self.assertFalse(result["retreat_authorized"])
        recorded = []
        recorder = SimpleNamespace(_execute_step_unrecorded=lambda *args, **kwargs: result,
                                   _record_command=lambda *args, **kwargs: recorded.append(kwargs))
        driver.NativeHeadlessGameplayDriver.execute_step(recorder, self.step)
        self.assertFalse(recorded[0]["ok"])
        executed = GameplayBridgeService._execute_planned_turn_without_unhandled_capture(
            SimpleNamespace(execute_step=lambda *args, **kwargs: result),
            {"plan": {"selected_step": self.step}, "revision": self.snapshot["revision"],
             "snapshot_id": self.snapshot["snapshot_id"]},
        )
        self.assertEqual(executed["status"], "executed")
        self.assertIs(executed["result"], result)

    def test_ordinary_planner_selects_existing_exact_day_without_retreat(self):
        state = strategy._battle_control_turn_state(self.rows, self.snapshot,
                                                    self.snapshot["player_armies"])
        self.assertEqual(state["status"], "reader_unavailable_hands_off")
        plan = strategy.choose_one_life_turn(
            self.rows, snapshot=self.snapshot,
            action_steps={self.step, "life-advance-one-day", "set-speed-1", "resume-map", "pause-map"},
            bridge_capabilities=set(watch.CLOCK_CAPABILITIES),
        )
        self.assertEqual(plan["selected_step"], "life-advance-one-day")
        self.assertFalse(plan["prediction_ready"])
        self.assertFalse(plan["retreat_authorized"])

    def test_requery_next_day_then_cooldown_and_expiry(self):
        day1 = next_day(self.snapshot)
        self.rows.append(clock(self.snapshot, day1))
        self.assertIsNone(select(day1, self.rows))
        dto = watch.observe_unavailable(error_for(day1, self.step), self.step, day1, day1)
        self.rows.append({"command": self.step, "ok": False, "result": dto})
        self.assertTrue(select(day1, self.rows)["cooldown_active"])
        before = day1
        for _ in range(29):
            after = next_day(before)
            self.rows.append(clock(before, after))
            before = after
        state = select(before, self.rows)
        self.assertTrue(state["cooldown_active"])
        self.assertEqual(state["next_query_date_raw"], day1["date_raw"] + 720)
        after = next_day(before)
        self.rows.append(clock(before, after))
        self.assertIsNone(select(after, self.rows))

    def test_cooldown_invalidates_on_combat_exit_or_participant_change(self):
        for changed in ("subject", "enemy"):
            with self.subTest(changed=changed):
                snapshot = copy.deepcopy(self.snapshot)
                if changed == "subject":
                    row = next(a for a in snapshot["player_armies"] if a["army_id"] == 285213008)
                else:
                    row = next(a for w in snapshot["active_wars"] for a in w["enemy_armies"]
                               if a.get("in_combat") and a.get("current_province_id") == 2629)
                row["in_combat"] = False
                self.assertIsNone(select(snapshot, self.rows))

    def test_changed_frame_or_incomplete_query_preserves_error(self):
        changed = copy.deepcopy(self.snapshot)
        changed["revision"] += 1
        self.assertIsNone(watch.observe_unavailable(error_for(self.snapshot, self.step),
                                                    self.step, self.snapshot, changed))
        bad = copy.deepcopy(self.dto)
        bad["native_command_result"]["typed_query_failure_v1"]["executor_finish"] = False
        with self.assertRaises(ValueError):
            watch.validate_unavailable(bad)

    def test_public_army_zero_remains_legal(self):
        snapshot = copy.deepcopy(self.snapshot)
        for army in snapshot["player_armies"] + [a for w in snapshot["active_wars"] for a in w["allied_armies"]]:
            if army["army_id"] == 285213008:
                army["army_id"] = 0
        step = "query-battle-control-snapshot-v1-0"
        dto = watch.observe_unavailable(error_for(snapshot, step), step, snapshot, snapshot)
        self.assertIsNotNone(dto)
        self.assertEqual(dto["scope_key"]["subject_army_id"], 0)


if __name__ == "__main__":
    unittest.main()
