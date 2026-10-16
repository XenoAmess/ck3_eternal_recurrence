"""Actual-frame projection and explicit synthetic Native packet replay; no RPC."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.strategy import choose_one_life_turn

FIXTURE = json.loads((Path(__file__).parent / "fixtures/embarked_route_arrival_unavailable_v1.json").read_text(encoding="utf-8"))
SNAPSHOT = FIXTURE["snapshot"]
REQUEST = FIXTURE["native_request"]
RESPONSE = FIXTURE["native_command_result"]
STEP = REQUEST["step"]


class Reader:
    def __init__(self, *, current=None, response=None):
        self.current = copy.deepcopy(SNAPSHOT if current is None else current)
        self.response = copy.deepcopy(RESPONSE if response is None else response)
        self.queries = self.reads = 0
        self.records = []

    def take_internal_semantic_snapshot(self):
        self.reads += 1
        return copy.deepcopy(self.current)

    def _execute_primitive_step(self, step, **kwargs):
        self.queries += 1
        if step != STEP or kwargs.get("internal_semantic_snapshot") is not True:
            raise AssertionError("unexpected transport operation")
        error = self.response["error"] + "; typed_query_failure_v1=" + json.dumps(
            self.response["typed_query_failure_v1"], sort_keys=True, separators=(",", ":"))
        raise native._NativeCommandRejectedError(error,
            native_request_id=REQUEST["request_id"], native_request_frame=REQUEST,
            native_command_result_frame=self.response)

    def _record_command(self, step, **kwargs):
        self.records.append((step, kwargs))


def observe(reader):
    return native.NativeHeadlessGameplayDriver._execute_native_war_step(
        reader, STEP, expected_revision=SNAPSHOT["revision"])


class EmbarkedRouteArrivalUnavailableTests(unittest.TestCase):
    def history(self, result):
        rows = copy.deepcopy(SNAPSHOT["history"])
        rows.append({"index": max([r.get("index", 0) for r in rows] + [0]) + 1,
                     "command": STEP, "ok": False, "result": result})
        return rows

    def plan(self, *, snapshot=None, result=None, actions=None):
        return choose_one_life_turn(self.history(observe(Reader()) if result is None else result),
            snapshot=copy.deepcopy(SNAPSHOT if snapshot is None else snapshot),
            action_steps=[STEP, "life-advance-one-day", "life-advance"] if actions is None else actions)

    def test_production_reader_and_ordinary_planner_use_one_observation_day(self):
        self.assertTrue(FIXTURE["provenance"]["synthetic_native_envelopes"])
        reader = Reader()
        result = observe(reader)
        self.assertEqual((reader.queries, reader.reads), (1, 2))
        self.assertEqual(result["readonly_unavailable_evidence"]["native_command_result"], RESPONSE)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["business_submission"])
        self.assertIsNone(result["route_contact_horizon"])
        reader._execute_step_unrecorded = lambda *a, **k: result
        native.NativeHeadlessGameplayDriver.execute_step(reader, STEP, expected_revision=SNAPSHOT["revision"])
        self.assertIs(reader.records[0][1]["ok"], False)
        plan = self.plan(result=result)
        self.assertEqual(plan["phase"], "native_war_embarked_route_timeline_unavailable_one_day_watch")
        self.assertEqual(plan["selected_step"], "life-advance-one-day")
        watch = plan["route_timeline_unavailable_watch"]
        self.assertEqual(watch["army_id"], 620757086)
        self.assertFalse(watch["contact_free_proven"])
        self.assertFalse(watch["movement_resubmitted"])
        self.assertFalse(watch["war_or_material_credit"])

    def test_foreign_combat_retreat_and_changed_target_do_not_take_fallback(self):
        from xar_autoplayer.strategy import _embarked_route_timeline_unavailable_watch_plan
        result = observe(Reader())
        army = next(a for a in SNAPSHOT["player_armies"] if a["army_id"] == 620757086)
        for update in ({"owner_character_id": 1}, {"in_combat": True}, {"retreating": True},
                       {"army_state": "moving"}, {"move_target_province_id": 1}):
            with self.subTest(update=update):
                altered = dict(army, **update)
                self.assertIsNone(_embarked_route_timeline_unavailable_watch_plan(
                    self.history(result), SNAPSHOT, altered, query_step=STEP,
                    available_steps={"life-advance-one-day"}, war_summary=SNAPSHOT["active_wars"]))

    def test_stale_or_unknown_read_and_missing_one_day_never_authorize_observation(self):
        result = observe(Reader())
        for update in ({"queried_native_revision": 3496}, {"queried_date_raw": 53410008}):
            with self.subTest(update=update):
                self.assertNotEqual(self.plan(result=dict(result, **update))["selected_step"], "life-advance-one-day")
        unknown = copy.deepcopy(result)
        unknown["readonly_unavailable_evidence"]["native_command_result"]["error"] = "CK3 could not build a complete contact route"
        self.assertIsNone(self.plan(result=unknown)["selected_step"])
        self.assertIsNone(self.plan(actions=[STEP, "life-advance"])["selected_step"])

    def test_unfinished_or_exceptional_native_reader_is_not_a_typed_observation(self):
        for key, value in (("executor_finish", False), ("frame_stable", False), ("wait_completed", False)):
            with self.subTest(key=key):
                bad = copy.deepcopy(RESPONSE)
                bad["typed_query_failure_v1"][key] = value
                reader = Reader(response=bad)
                with self.assertRaises(native._NativeCommandRejectedError):
                    observe(reader)
                self.assertEqual((reader.queries, reader.reads), (1, 1))

    def test_actual14_legacy_completed_read_requires_fresh_query_not_time(self):
        from xar_autoplayer.strategy import _current_frame_route_contact_query_failure as review
        source = FIXTURE["provenance"]["p21_blocked_auto14"]
        self.assertTrue(source["error_exactly_matches_reconstructed_native_error"])
        text = "_NativeCommandRejectedError: native gameplay step failed: " + RESPONSE["error"]
        suffix = "; typed_query_failure_v1=" + json.dumps(RESPONSE["typed_query_failure_v1"], sort_keys=True, separators=(",", ":"))
        row = {"index": source["history_index"], "command": STEP, "ok": False, "error": text + suffix}
        frame = dict(source["fresh_frame"], diagnostics=source["fresh_diagnostics"])
        retained = copy.deepcopy(row)
        self.assertIsNone(review([row], frame, STEP))
        normal = choose_one_life_turn([row], snapshot=copy.deepcopy(SNAPSHOT),
            action_steps=[STEP, "life-advance-one-day", "life-advance"])
        self.assertEqual(normal["selected_step"], STEP)
        self.assertEqual(row, retained)
        for error in ("unknown", text + suffix.replace('"executor_finish":true', '"executor_finish":false'),
                      text + suffix.replace('"frame_stable":true', '"frame_stable":false')):
            with self.subTest(error=error):
                self.assertEqual(review([dict(row, error=error)], frame, STEP)["scope_status"], "unknown_frame")
        business = "move-army-620757086-to-5969"
        self.assertIsNotNone(review([dict(row, command=business)], frame, business))


if __name__ == "__main__":
    unittest.main()
