from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer import strategy
from xar_autoplayer.bridge.war_contract import (
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
    battle_decision_epoch_advance_step,
    war_objective_hold_sentinel_advance_step,
)
from xar_autoplayer.bridge.battle_control_contract import query_battle_control_snapshot_v1_step
from test_gameplay_bridge import _army, _native_war_plan
from test_battle_control_snapshot_v1_bridge import (
    DATE_RAW,
    _battle_frame,
    _battle_query_row,
    _planner_battle_snapshot,
    _rebind_battle_frame,
    _sentinel_advance_row,
)


INVALID_UNITS = (True, False, -1, 2**31, "0", 0.0, None)


def _regular(unit: object = 0, province: int = 2635) -> dict:
    return _army(unit, soldiers=4100, province_id=province, controllable=True,
                 army_state="regular", army_state_code=1, route_province_ids=[])


def _split(original: int, sibling: int) -> dict:
    return {"index": 1, "command": f"split-army-half-{original}", "ok": True,
            "result": {"war_action": {"status": "split_submitted",
                        "source_army_id": original, "sibling_army_id": sibling,
                        "player_army_ids_before": [original]}}}


class PublicCUnitPlannerTests(unittest.TestCase):
    def test_zero_is_selected_in_strongest_tie_and_invalid_handles_are_excluded(self):
        zero = _regular()
        one = _regular(1)
        self.assertIs(strategy._stable_strongest_army([one, zero]), zero)
        for invalid in INVALID_UNITS:
            with self.subTest(invalid=invalid):
                bad = _regular(invalid)
                bad["soldiers"] = 100_000
                self.assertIs(strategy._stable_strongest_army([bad, zero]), zero)
                self.assertIsNone(strategy._stable_strongest_army([bad]))
        self.assertEqual(strategy._public_cunit_int(2**31 - 1), 2**31 - 1)

    def test_production_stationary_hold_binds_zero_without_losing_date_bound(self):
        plan = _native_war_plan(
            player=_regular(), enemies=[], score=30, date_raw=DATE_RAW,
            objective=2635, objective_states=[], occupation_supported=True,
            siege_progress_supported=True,
            steps=(WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, "life-advance"),
            battle_speed_readiness={"decision_sentinel_live_ready": True,
                                   "stationary_objective_hold_sentinel_live_ready": True},
        )
        self.assertEqual(plan["phase"], "native_war_stationary_objective_hold_sentinel")
        self.assertEqual(plan["selected_step"],
                         war_objective_hold_sentinel_advance_step(88, 0, 2635, DATE_RAW + 7 * 24))
        self.assertEqual(plan["watch_army_ids"], [0])

    def test_hold_preserves_nonunit_war_and_province_gates(self):
        baseline = {"phase": "native_war_pursuit_progress", "selected_step": "life-advance",
                    "pursuit": {"target_source": "war_objective_province", "objective_kind": "siege",
                                "war_id": 88, "army_id": 0, "target_province_id": 2635}}
        kwargs = dict(snapshot={"paused": True, "map_ready": True},
                      active_wars=[{"war_id": 88, "war_objective_province_ids": [2635]}],
                      player_armies=[_regular()], war_summary=[], enabled=True,
                      action_available=True, timeline_speed=3, high_speed_ab=False)
        for field in ("war_id", "target_province_id"):
            bad = copy.deepcopy(baseline)
            bad["pursuit"][field] = 0
            self.assertIsNone(strategy._stationary_objective_hold_sentinel_substitution(bad, **kwargs))
        for invalid in INVALID_UNITS:
            bad = copy.deepcopy(baseline)
            bad["pursuit"]["army_id"] = invalid
            self.assertIsNone(strategy._stationary_objective_hold_sentinel_substitution(bad, **kwargs))

    def test_sentinel_history_watch_zero_is_valid_but_wrong_types_are_not(self):
        result = _sentinel_advance_row(1, watch_army_ids=[0])["result"]
        observed = strategy._battle_sentinel_advance_validation(result)
        self.assertTrue(observed["valid"], observed["errors"])
        for invalid in INVALID_UNITS:
            with self.subTest(invalid=invalid):
                bad = copy.deepcopy(result)
                bad["watch_army_ids"] = [invalid]
                self.assertIn("watch_set_invalid", strategy._battle_sentinel_advance_validation(bad)["errors"])

    def test_combat_zero_direct_frame_and_annotation_remain_observed(self):
        base = _battle_frame()
        frame = _rebind_battle_frame(base, subject=0,
                                    native_subject=base["subject_native_carmy_id"],
                                    combat_id=base["combat_id"], province_id=base["province_id"])
        snapshot = _planner_battle_snapshot(frame=frame)
        snapshot["player_armies"][0]["army_id"] = 0
        snapshot["battle_control_snapshot_v1_subject_army_id"] = 0
        snapshot["battle_control_snapshot_v1_queried_native_revision"] = snapshot["native_revision"]
        current, _ = strategy._current_battle_control_frames([], snapshot)
        self.assertIn(0, current)
        comparison = strategy._active_combat_provisional_comparison(snapshot)
        self.assertEqual(comparison["subject_army_id"], 0)
        annotated = strategy._annotate_active_combat_resume_input({"selected_step": "life-advance"}, snapshot)
        self.assertEqual(annotated["active_combat_resume_input"]["subjects"][0]["army_id"], 0)
        self.assertFalse(annotated["active_combat_resume_input"]["used_for_decision"])

    def test_enemy_zero_keeps_route_epoch_without_accepting_bad_handles(self):
        enemy = _army(0, soldiers=1000, province_id=2630, controllable=False,
                      army_state="moving", move_target_province_id=2635,
                      route_province_ids=[2635])
        observed = strategy._enemy_endpoint_observation(enemy, war_id=88, date_raw=DATE_RAW)
        self.assertEqual(observed["enemy_army_id"], 0)
        for invalid in INVALID_UNITS:
            bad = dict(enemy, army_id=invalid)
            self.assertIsNone(strategy._enemy_endpoint_observation(bad, war_id=88, date_raw=DATE_RAW))
        self.assertIsNone(strategy._enemy_endpoint_observation(dict(enemy, move_target_province_id=0),
                                                               war_id=88, date_raw=DATE_RAW))

    def test_production_combat_zero_is_watched_without_removing_readiness_gate(self):
        base = _battle_frame()
        frame = _rebind_battle_frame(base, subject=0,
                                    native_subject=base["subject_native_carmy_id"],
                                    combat_id=base["combat_id"], province_id=base["province_id"])
        snapshot = _planner_battle_snapshot(frame=frame)
        snapshot["player_armies"][0]["army_id"] = 0
        snapshot["battle_control_snapshot_v1_subject_army_id"] = 0
        steps = (query_battle_control_snapshot_v1_step(0), "life-advance", "battle-decision-epoch-advance")
        history = [_battle_query_row(1, frame)]
        plan = strategy.choose_one_life_turn(history, snapshot=snapshot, action_steps=steps,
                                           battle_speed_readiness={"decision_sentinel_live_ready": True})
        self.assertEqual(plan["selected_step"], battle_decision_epoch_advance_step(DATE_RAW + 45 * 24))
        self.assertEqual(plan["watch_army_ids"], [0])
        slow = strategy.choose_one_life_turn(history, snapshot=snapshot, action_steps=steps,
                                           battle_speed_readiness=None)
        self.assertEqual(slow["selected_step"], "life-advance")

    def test_siege_defender_partition_preserves_enemy_zero(self):
        enemy = dict(_regular(0), controllable=False, army_state="sieging")
        observed = strategy._siege_forecast_participant_partition(
            {"enemy_armies": [enemy]}, {"friendly_army_ids": [7], "enemy_army_ids": [0]},
            {"hostile_army_ids": [0], "hostile_routes": [
                {"army_id": 0, "timeline_observable": True, "current_province_id": 2635}]},
            army_id=7, target_province_id=2635)
        self.assertEqual(observed["status"], "available")
        self.assertEqual(observed["defender_army_ids"], [0])

    def test_strength_routing_accepts_zero_but_rejects_malformed_handles(self):
        row = {"army_id": 0, "status": "available", "war_ids": [88], "scope_role": "player",
               "current_soldiers": 1000, "maximum_soldiers": 1000, "ai_base_power_raw": 1000}
        enemy = dict(row, army_id=7, scope_role="active_war_enemy")
        snapshot = {"paused": True, "army_strengths_status": "available", "army_strengths": [row, enemy]}
        balance = strategy._same_frame_army_strength_balance(snapshot, 88)
        self.assertEqual(balance["friendly_army_ids"], [0])
        self.assertIsNone(strategy._same_frame_army_strength_balance(snapshot, 0))
        for invalid in INVALID_UNITS:
            bad = copy.deepcopy(snapshot)
            bad["army_strengths"][0]["army_id"] = invalid
            self.assertIsNone(strategy._same_frame_army_strength_balance(bad, 88))

    def test_route_conjunction_orders_zero_first_and_ignores_invalid_handles(self):
        armies = [dict(_regular(1), move_target_province_id=2635, route_province_ids=None),
                  dict(_regular(0), move_target_province_id=2635, route_province_ids=None),
                  dict(_regular(True), move_target_province_id=2635, route_province_ids=None)]
        observed = strategy._moving_route_contact_horizon_conjunction(
            [], {}, controlled_armies=armies, subject_army_id=2,
            subject_contact_horizon={}, hostile_army_ids=(3,), enemies=[])
        self.assertEqual([row["army_id"] for row in observed["conflicting"]], [0, 1])
        self.assertEqual(sorted([_regular(1), _regular(0)], key=strategy._public_cunit_sort_key)[0]["army_id"], 0)

    def test_exact_split_pair_handles_original_or_sibling_zero(self):
        for original, sibling in ((0, 7), (7, 0)):
            with self.subTest(original=original, sibling=sibling):
                observed = strategy._split_merge_recovery(
                    [_split(original, sibling)], {},
                    controlled_armies=[_regular(original), _regular(sibling)], active_wars=[])
                self.assertEqual(observed["status"], "ready_to_merge")
                self.assertEqual(observed["merge_step"], f"merge-armies-{original}-with-{sibling}")

    def test_split_does_not_infer_pair_from_malformed_public_ids(self):
        for invalid in INVALID_UNITS:
            for field in ("source_army_id", "sibling_army_id", "player_army_ids_before"):
                if invalid is None and field != "player_army_ids_before":
                    continue  # The old optional source/sibling fields remain compatible.
                with self.subTest(invalid=invalid, field=field):
                    row = _split(0, 7)
                    row["result"]["war_action"][field] = [invalid] if field == "player_army_ids_before" else invalid
                    self.assertIsNone(strategy._split_merge_recovery(
                        [row], {}, controlled_armies=[_regular(0), _regular(7)], active_wars=[]))

    def test_regroup_optional_receipt_does_not_turn_malformed_unit_into_missing(self):
        rows = [
            {"command": "query-campaign-root-context-v1", "ok": True,
             "result": {"campaign_root_context": {"status": "available", "date_raw": DATE_RAW,
                        "player_character_id": 707, "capital_province_id": 2635,
                        "readiness": {"ready": True}}}},
            {"command": "preview-move-army-0-to-2635", "ok": True,
             "result": {"route_preview": {"status": "available", "previewed_date_raw": DATE_RAW,
                                           "origin_province_id": 2630}}},
            {"command": "move-army-0-to-2635", "ok": True,
             "result": {"war_action": {"status": "arrived", "army_id": 0,
                        "target_province_id": 2635, "submitted_date_raw": DATE_RAW}}},
        ]
        snapshot = {"date_raw": DATE_RAW, "played_character": {"character_id": 707},
                    "player_armies": [_regular()], "active_wars": [
                        {"war_id": 88, "player_side": "attacker", "player_is_primary_war_leader": True,
                         "war_objective_province_ids": [2630]}]}
        self.assertIsNotNone(strategy._capital_regroup_intent(rows, snapshot, army_id=0, war_id=88))
        legacy = copy.deepcopy(rows)
        legacy[-1]["result"]["war_action"]["army_id"] = None
        self.assertIsNotNone(strategy._capital_regroup_intent(legacy, snapshot, army_id=0, war_id=88))
        for invalid in INVALID_UNITS:
            if invalid is None:
                continue
            bad = copy.deepcopy(rows)
            bad[-1]["result"]["war_action"]["army_id"] = invalid
            self.assertIsNone(strategy._capital_regroup_intent(bad, snapshot, army_id=0, war_id=88))


if __name__ == "__main__":
    unittest.main()
