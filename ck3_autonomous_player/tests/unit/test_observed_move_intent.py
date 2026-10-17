"""Portable actual-receipt projection for the public Strategy source.

The JSON beside this file carries compact completed P44 receipts and exact
SHA provenance. The test imports the package under test normally; no runtime
tree or machine-specific path is required.
"""
import copy
import json
from pathlib import Path
import unittest

from xar_autoplayer import strategy


FIXTURE = json.loads((Path(__file__).parents[1] / "fixtures" / "portable_observed_move_fixture.json").read_text(encoding="utf-8"))
TAIL = json.loads((Path(__file__).parents[1] / "fixtures" / "portable_observed_move_history_tail.json").read_text(encoding="utf-8"))


class ObservedMovePortable(unittest.TestCase):
    def setUp(self):
        self.snapshot = copy.deepcopy(FIXTURE["snapshot_457"])
        self.original = copy.deepcopy(FIXTURE["original_failed_move_row"])
        self.evidence = copy.deepcopy(FIXTURE["observed_intent_evidence"])
        self.rows = [self.original, {"index": self.original["index"] + 1,
                                     "command": "reconcile-observed-move-intent",
                                     "ok": False, "result": self.evidence}]

    def proof(self, rows=None, snapshot=None):
        return strategy._active_native_move_intent(
            self.rows if rows is None else rows,
            self.snapshot if snapshot is None else snapshot,
            army_id=167772577, target_province_id=2621)

    def test_actual_failed_move_and_fresh_semantic_bind_to_observed_intent(self):
        self.assertEqual(self.original["ok"], False)
        self.assertEqual(self.evidence["native_ack_verified"], False)
        proof = self.proof()
        self.assertEqual(proof["status"], "active")
        self.assertFalse(proof["native_ack_verified"])
        army = next(a for a in self.snapshot["player_armies"] if a["army_id"] == 167772577)
        relief = strategy._primary_defender_siege_relief_assessment(
            self.snapshot, commands=self.rows,
            active_wars=self.snapshot["active_wars"],
            controlled_armies=[army], pursuit_army=army)
        self.assertEqual(relief["status"], "active_move_intent")
        self.assertFalse(relief["move_intent"]["native_ack_verified"])

    def test_wrong_ownership_frame_route_or_ack_is_rejected(self):
        mutations = (
            lambda s, e: e.update(native_ack_verified=True),
            lambda s, e: e.update(accepted=True),
            lambda s, e: e.update(new_move_submissions=1),
            lambda s, e: e.update(original_native_request_id=""),
            lambda s, e: e.update(observed_army_route=[2619]),
            lambda s, e: e["source_frame"].update(native_revision=6286),
            lambda s, e: e["observed_frame"].update(episode_run_id="wrong"),
            lambda s, e: s["diagnostics"].update(bridge_pid=99999),
            lambda s, e: s["player_armies"][0].update(route_province_ids=[2619]),
            lambda s, e: s.update(date_raw=e["source_frame"]["date_raw"] + 24 * 90),
            lambda s, e: s.update(paused=False),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                snapshot = copy.deepcopy(self.snapshot)
                evidence = copy.deepcopy(self.evidence)
                mutate(snapshot, evidence)
                rows = [copy.deepcopy(self.original),
                        {"command": "reconcile-observed-move-intent", "ok": False,
                         "result": evidence}]
                self.assertIsNone(self.proof(rows, snapshot))

    def test_newer_move_and_wrong_original_are_not_hidden(self):
        newer = self.rows + [{"command": "move-army-167772577-to-2619", "ok": False}]
        self.assertIsNone(self.proof(newer))
        wrong = copy.deepcopy(self.rows)
        wrong[0]["command"] = "move-army-167772577-to-2619"
        self.assertIsNone(self.proof(wrong))

    def test_same_game_sdk_rebind_and_arrival_keep_ack_unknown(self):
        snapshot = copy.deepcopy(FIXTURE["snapshot_462"])
        snapshot.update(revision=2, native_revision=6287, snapshot_id="native:6287")
        snapshot["diagnostics"]["connection_generation"] += 1
        self.assertFalse(self.proof(snapshot=snapshot)["native_ack_verified"])
        snapshot["diagnostics"]["bridge_pid"] += 1
        self.assertIsNone(self.proof(snapshot=snapshot))
        arrival = copy.deepcopy(self.snapshot)
        army = next(a for a in arrival["player_armies"] if a["army_id"] == 167772577)
        army.update(current_province_id=2621, move_target_province_id=None,
                    route_province_ids=[], route_read_status="complete_empty",
                    army_state="sieging", army_state_code=3)
        arrival["date_raw"] += 24
        observed = strategy._observed_native_move_intent(
            self.rows, arrival, army_id=167772577,
            target_province_id=2621, arrived=True)
        self.assertEqual(observed["status"], "arrived")
        self.assertFalse(observed["native_ack_verified"])

    def test_actual_sparse_history_ordinary_choose_then_synthetic_clock(self):
        # The placeholder count retains flattened row indexes; placeholders
        # are not evidence. Only the twelve rows in TAIL are actual history.
        self.assertFalse(TAIL["inert_prefix_is_actual_history"])
        history = [{"command": "history-elided-offline-fixture", "ok": False}
                   for _ in range(TAIL["inert_prefix_count"])]
        history.extend(copy.deepcopy(TAIL["actual_rows"]))
        cap = FIXTURE["capabilities_2"]
        query = FIXTURE["route_query_451"]["selected_step"]
        steps = list(cap["action_steps"]) + [query]
        snapshot = copy.deepcopy(FIXTURE["snapshot_462"])
        first = strategy.choose_one_life_turn(
            history, snapshot=snapshot, action_steps=steps,
            bridge_capabilities=cap["bridge_capabilities"],
            battle_speed_readiness=cap.get("battle_speed_readiness"))
        self.assertEqual(first["phase"], "native_war_route_contact_horizon")
        self.assertEqual(first["selected_step"], query)
        self.assertFalse(first["move_intent"]["native_ack_verified"])
        synthetic = copy.deepcopy(FIXTURE["route_query_451"]["result"])
        synthetic.update(query_sequence=670, snapshot_revision=6286,
                         queried_snapshot_id="native:6286", queried_revision=304,
                         queried_native_revision=6286)
        synthetic["route_contact_horizon"].update(snapshot_revision=6286,
                                                  date_raw=53297328)
        history.append({"command": query, "ok": True, "result": synthetic})
        enemy_ids = synthetic["route_contact_horizon"]["hostile_army_ids"]
        advance = strategy.advance_route_contact_window_step(
            167772577, 2621, enemy_ids, horizon_days=3)
        second = strategy.choose_one_life_turn(
            history, snapshot=snapshot, action_steps=steps + [advance],
            bridge_capabilities=cap["bridge_capabilities"],
            battle_speed_readiness=cap.get("battle_speed_readiness"))
        self.assertEqual(second["phase"], "native_war_route_contact_horizon_progress")
        self.assertEqual(second["selected_step"], advance)
        self.assertTrue(second["route_audit"]["contact_horizon"]["one_day_contact_free"])


if __name__ == "__main__":
    unittest.main()
