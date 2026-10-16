"""Offline focused contract for a current-frame route timeline failure."""
import copy
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
from xar_autoplayer import strategy
ACTUAL = json.loads((HERE.parent / "fixtures" / "p28_land_route_timeline_actual_projection.json").read_text("utf8"))
HALT = "halt-army-402653503"
ONE_DAY = "life-advance-one-day"


def facts():
    s = copy.deepcopy(ACTUAL["snapshot"])
    r = copy.deepcopy(ACTUAL["result"])
    q = r["step"]
    return s, r, q, [{"index": 9500, "command": q, "ok": False, "result": r}]


def choose(s, q, rows, pending=None, steps=frozenset({HALT, ONE_DAY})):
    return strategy._land_route_timeline_unavailable_halt_or_watch_plan(
        rows, s, s["player_armies"][0], query_step=q, pending_halt=pending,
        available_steps=set(steps), war_summary=[])


class TestLandTimeline(unittest.TestCase):
    def test_actual_p30_ack_and_independent_suffix_remain_pending(self):
        fixture = json.loads((HERE.parent / "fixtures" /
            "p30_land_halt_actual_projection.json").read_text("utf8"))
        body = fixture["halt_body"]
        snapshot = fixture["independent_snapshot"]
        rows = [{"index": 1, "command": body["selected_step"], "ok": True,
                 "result": body["result"]}]
        pending = strategy._pending_unsafe_route_halt(
            rows, snapshot, army_id=body["result"]["war_action"]["army_id"])
        self.assertTrue(pending["suffix_cancellation_observed"])
        self.assertTrue(pending["current_edge_retained"])
        self.assertFalse(pending["postcondition_verified"])
        self.assertEqual(snapshot["player_armies"][0]["route_province_ids"], [5966])
        self.assertFalse(fixture["actual_safe_contact_or_battle_result_claimed"])

    def test_actual_537_542_halts_before_any_time(self):
        s, r, q, rows = facts()
        p = choose(s, q, rows)
        self.assertEqual(p["selected_step"], HALT)
        self.assertEqual(p["phase"], "native_war_land_route_timeline_unavailable_halt_submit")
        self.assertIs(p["halt_intent"]["contact_free_proven"], False)
        self.assertEqual(s["player_armies"][0]["route_province_ids"], [5966, 5969])
        self.assertEqual(len(strategy.parse_query_route_contact_horizon_step(q)[2]), 13)

    def test_exact_synthetic_fresh_partial_halt_allows_one_day_only(self):
        s, r, q, rows = facts()
        old = s["native_revision"]
        s["native_revision"] = old + 1
        s["revision"] += 1
        s["snapshot_id"] = f"native:{old + 1}"
        a = s["player_armies"][0]
        a["route_province_ids"] = [5966]
        a["move_target_province_id"] = 5966
        # Exact new full-hostile query is independently unavailable on the
        # post-Halt publication. No old query lease is reused.
        q = strategy.query_route_contact_horizon_step(a["army_id"], 5966,
                strategy.parse_query_route_contact_horizon_step(q)[2])
        r["step"] = q
        for name, value in (("queried_snapshot_id", s["snapshot_id"]),
                ("queried_revision", s["revision"]),
                ("queried_native_revision", s["native_revision"])):
            r[name] = value
        r["readonly_unavailable_evidence"]["same_frame_readback"] = {
            "starting_frame": {"native_revision": s["native_revision"]},
            "ending_frame": {"native_revision": s["native_revision"]}}
        original_halt = {
            "status": "halt_submitted", "army_id": a["army_id"],
            "submitted_date_raw": s["date_raw"], "submitted_native_revision": old,
            "submitted_connection_generation": s["diagnostics"]["connection_generation"],
            "submitted_episode_run_id": s["episode_run_id"],
            "owner_character_id": a["owner_character_id"],
            "original_current_province_id": a["current_province_id"],
            "original_move_target_province_id": 5969,
            "original_route_province_ids": [5966, 5969],
            "postcondition_verified": False}
        rows = [{"index": 9501, "command": HALT, "ok": True,
                 "result": {"step": HALT, "accepted": True,
                            "war_action": original_halt}},
                {"index": 9502, "command": q, "ok": False, "result": r}]
        pending = strategy._pending_unsafe_route_halt(rows, s, army_id=a["army_id"])
        self.assertTrue(pending["suffix_cancellation_observed"])
        p = choose(s, q, rows, pending)
        self.assertEqual(p["selected_step"], ONE_DAY)
        self.assertEqual(p["route_timeline_unavailable_watch"]["contact_status"], "unknown")
        self.assertIs(p["route_timeline_unavailable_watch"]["war_or_material_credit"], False)

    def test_wrong_or_incomplete_proof_never_advances(self):
        for mutation in ("stale_revision", "extra_enemy", "missing_enemy", "modal",
                         "event", "combat", "retreat", "wrong_error", "wrong_readback",
                         "unknown_hostile_identity", "missing_halt_cap", "rejected_halt"):
            with self.subTest(mutation=mutation):
                s, r, q, rows = facts()
                steps = {HALT, ONE_DAY}
                a = s["player_armies"][0]
                if mutation == "stale_revision": s["revision"] += 1
                if mutation == "extra_enemy": s["active_wars"][0]["enemy_armies"].append({"army_id": 3333, "retreating": False})
                if mutation == "missing_enemy": s["active_wars"][0]["enemy_armies"] = s["active_wars"][0]["enemy_armies"][1:]
                if mutation == "modal": s["top_exclusive_modal_choice_hint"] = {"status": "present"}
                if mutation == "event": s["active_event"] = {"instance_id": 7}
                if mutation == "combat": a["in_combat"] = True
                if mutation == "retreat": a["retreating"] = True
                if mutation == "wrong_error": r["readonly_unavailable_evidence"]["native_command_result"]["error"] = "some other native failure"
                if mutation == "wrong_readback": r["readonly_unavailable_evidence"]["same_frame_readback"]["ending_frame"] = {"native_revision": 999}
                if mutation == "unknown_hostile_identity": s["active_wars"][0]["enemy_armies"][0]["army_id"] = None
                if mutation == "missing_halt_cap": steps.remove(HALT)
                if mutation == "rejected_halt": rows.insert(0,{"index": 9499,"command": HALT,"ok": False,"error": "CK3 halt-army command validation failed"})
                self.assertIsNone(choose(s, q, rows, steps=steps))

    def test_no_partial_observation_no_one_day(self):
        s, r, q, rows = facts()
        pending = {"army_id": 402653503, "suffix_cancellation_observed": True,
                   "current_edge_retained": True, "postcondition_verified": False}
        self.assertIsNone(choose(s, q, rows, pending))  # route still has two edges
        s["player_armies"][0]["route_province_ids"] = [5966]
        self.assertIsNone(choose(s, q, rows, pending))  # query target still 5969


# Synthetic native validator rejection tests: no real rejection is claimed.
from xar_autoplayer.bridge import native_driver as driver_mod


class TestHaltValidatorDeferred(unittest.TestCase):
    def _drive(self, *, native_error="CK3 halt-army command validation failed",
               route_change=False, owner_change=False, bad_request=False):
        start, query_result, query_step, query_rows = facts()
        current = copy.deepcopy(start)
        if route_change:
            current["player_armies"][0]["route_province_ids"] = [5966]
        if owner_change:
            current["diagnostics"]["bridge_pid"] += 1
        request = {"type": "execute_step", "protocol_version": 1,
                   "request_id": "synthetic-halt-1", "step": HALT,
                   "expected_revision": start["native_revision"]}
        if bad_request:
            request["step"] = "halt-army-123"
        # Actual AUTO537 failed command_result has no `step`; the request
        # carries it. Preserve this real wire shape for a synthetic Halt error.
        response = copy.deepcopy(ACTUAL["result"]["readonly_unavailable_evidence"]["native_command_result"])
        self.assertNotIn("step", response)
        response["request_id"] = "synthetic-halt-1"
        response["error"] = native_error
        error = driver_mod._NativeCommandRejectedError(
            native_error, native_request_id="synthetic-halt-1",
            native_request_frame=request, native_command_result_frame=response)
        obj = object.__new__(driver_mod.NativeHeadlessGameplayDriver)
        frames = iter((start,current))
        obj.take_snapshot = lambda: next(frames)
        obj._h3937_date_hold_active = lambda *_: False
        def rejected(*args, **kwargs):
            raise error
        obj._execute_primitive_step = rejected
        return obj, start, current, query_step, query_rows

    def test_typed_validator_rejection_leads_to_exact_one_day_risk_watch(self):
        obj, start, current, q, rows = self._drive()
        deferred = obj._execute_native_war_step(HALT, expected_revision=start["revision"])
        self.assertIs(deferred["accepted"], False)
        self.assertIs(deferred["business_submission"], False)
        self.assertEqual(deferred["war_action"]["route_province_ids"], [5966,5969])
        rows.append({"index": 9501, "command": HALT, "ok": True, "result": deferred})
        p = choose(current, q, rows)
        self.assertEqual(p["selected_step"], ONE_DAY)
        self.assertEqual(p["phase"], "native_war_land_halt_validator_rejected_one_day_watch")
        self.assertIs(p["route_timeline_unavailable_watch"]["halt_accepted"], False)
        self.assertIs(p["route_timeline_unavailable_watch"]["contact_free_proven"], False)
        self.assertIs(p["route_timeline_unavailable_watch"]["war_or_material_credit"], False)
        # Any newly observed route/frame change revokes this old rejection.
        current["revision"] += 1
        self.assertIsNone(choose(current, q, rows))

    def test_only_exact_native_validator_rejection_is_typed(self):
        for mutation in ("different_error", "route_change", "owner_change", "bad_request"):
            with self.subTest(mutation=mutation):
                obj, start, current, q, rows = self._drive(
                    native_error="CK3 halt-army command queue rejected" if mutation=="different_error" else "CK3 halt-army command validation failed",
                    route_change=mutation=="route_change",
                    owner_change=mutation=="owner_change",
                    bad_request=mutation=="bad_request")
                with self.assertRaises(driver_mod.BridgeUnavailableError):
                    obj._execute_native_war_step(HALT, expected_revision=start["revision"])

    def test_public_execute_step_records_typed_zero_submit_once(self):
        obj, start, current, q, rows = self._drive()
        deferred = obj._execute_native_war_step(HALT, expected_revision=start["revision"])
        captured = []
        recorder = object.__new__(driver_mod.NativeHeadlessGameplayDriver)
        recorder._execute_step_unrecorded = lambda step, expected_revision=None: deferred
        recorder._record_command = lambda step, **kw: captured.append((step,kw)) or None
        returned = recorder.execute_step(HALT, expected_revision=start["revision"])
        self.assertEqual(returned, deferred)
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][0], HALT)
        self.assertIs(captured[0][1]["ok"], True)  # handler completed; accepted is False
        self.assertIs(captured[0][1]["result"]["business_submission"], False)

    def test_validator_deferred_cannot_be_replayed_or_relabeled_halt_ack(self):
        obj, start, current, q, rows = self._drive()
        deferred = obj._execute_native_war_step(HALT, expected_revision=start["revision"])
        rows.append({"index": 9501, "command": HALT, "ok": True, "result": deferred})
        self.assertIsNone(strategy._pending_unsafe_route_halt(rows,current,army_id=402653503))
        self.assertIsNone(choose(current,q,rows,steps={HALT}))
        deferred["halt_rejection_evidence"]["native_command_result"]["error"] = "unknown error"
        self.assertIsNone(choose(current,q,rows))

if __name__ == "__main__":
    unittest.main()
