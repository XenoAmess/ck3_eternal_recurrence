from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer.strategy import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    _primary_defender_siege_forecast_ingress,
    _primary_defender_siege_relief_assessment,
    _provisional_defense_research_assessment,
    _siege_forecast_participant_partition,
    choose_one_life_turn,
    query_combat_simulation_inputs_v3_step,
    query_route_contact_horizon_step,
)
from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
from xar_autoplayer.m5_war_cash_resource_v1 import observe_active_war_cash_resource_v1
from xar_autoplayer.simulation.general_battle_forecast import forecast_fixed_contact
from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input

from ck3_autonomous_player.tests.unit.test_gameplay_bridge import (
    _army,
    _army_strength,
    _preview_row,
    _route_contact_row,
    _snapshot,
    _war,
)


FIXTURES = Path(__file__).parents[1] / "fixtures" / "combat"
R0265_REPORT = (
    Path(__file__).parents[3] / "docs" / "autonomous-agent-progress"
    / "coordination" / "war-requests" / "evidence"
    / "WAR-ROBERT-H2825-SIEGE-PARTITION-20260928.r0265-formal-report.json"
)


class ProvisionalDefenseCanaryTests(unittest.TestCase):
    def _r0321_two_defender_inputs(self):
        frame, rows = self._r0271_replay_inputs()
        frame["episode_run_id"] = "native-29829-r0321-test"
        frame["played_character_id"] = 29829
        frame["played_character_gold"] = {"raw": 100_000_000, "scale": 100_000}
        second = frame["active_wars"][0]["enemy_armies"][1]
        second.update({
            "current_province_id": 2629, "army_state": "sieging",
            "army_state_code": 3, "move_target_province_id": None,
            "route_province_ids": [],
        })
        full = rows[1]["result"]["route_contact_horizon"]
        full["hostile_routes"][1].update({
            "current_province_id": 2629,
            "route_province_ids": [], "arrival_date_raws": [],
        })
        rows[1]["result"]["queried_episode_run_id"] = frame["episode_run_id"]
        route = rows[0]["result"]["route_preview"]["route_province_ids"]
        first_hop = route[0]
        rows.append(_preview_row(
            4, army_id=83886367, origin=2610, target=first_hop,
            date_raw=frame["date_raw"], route=[first_hop],
        ))
        rows.append(_route_contact_row(
            5, army_id=83886367, origin=2610, target=first_hop,
            date_raw=frame["date_raw"], route=[first_hop],
            hostile_ids=(50331920, 83886484), contact_free=True,
            episode_run_id=frame["episode_run_id"],
            hostile_provinces={50331920: 2629, 83886484: 2629},
        ))
        query_step = query_combat_simulation_inputs_v3_step(
            2629, route[-2], [83886367], [50331920, 83886484]
        )
        rows.append({
            "index": 6, "command": query_step, "ok": True,
            "result": {
                "step": query_step, "accepted": True, "status": "available",
                "queried_snapshot_id": frame["snapshot_id"],
                "queried_revision": frame["revision"],
                "queried_native_revision": frame["native_revision"],
            },
        })
        frame.update({
            "combat_simulation_inputs_v3": {"completeness": {}},
            "combat_simulation_inputs_v3_status": "available",
            "combat_simulation_inputs_v3_target_province_id": 2629,
            "combat_simulation_inputs_v3_attacker_entry_province_id": route[-2],
            "combat_simulation_inputs_v3_attacker_army_ids": [83886367],
            "combat_simulation_inputs_v3_defender_army_ids": [50331920, 83886484],
            "combat_simulation_inputs_v3_queried_snapshot_id": frame["snapshot_id"],
            "combat_simulation_inputs_v3_queried_revision": frame["revision"],
        })
        step = f"move-army-83886367-to-{first_hop}"
        actions = {step}
        return frame, rows, actions, step

    def _r0321_cash_package(self, frame, step):
        source_frame = observed_frame(frame)
        war_id = 16777231
        quote_source = "synthetic-exact-selected-step-price"

        def amount(raw, source):
            return {
                "raw": raw, "scale": 100_000, "source": source,
                "source_frame": dict(source_frame), "war_id": war_id,
            }

        receipt = observe_active_war_cash_resource_v1(
            snapshot=frame, war_id=war_id,
            inputs={
                "source_frame": dict(source_frame), "war_id": war_id,
                "pending_war_cash_raw": amount(1_000_000, "synthetic-pending"),
                "immediate_war_action_cost_raw": amount(0, quote_source),
                "future_war_cost_upper_raw": amount(2_000_000, "synthetic-one-day-upkeep"),
                "future_risk_budget_raw": amount(1_000_000, "synthetic-risk"),
                "policy_minimum_gold_reserve_raw": amount(5_000_000, "synthetic-policy"),
                "horizon_days": 1,
                "future_bound_assumptions": ["synthetic one-day bound"],
            },
        )
        return {
            "schema": "xar.ck3.war-first-hop-cash-bound.v1",
            "source_frame": dict(source_frame), "connection_generation": 1,
            "war_cash_resource": receipt,
            "selected_step_quote": {
                "status": "native_selected_step_bound",
                "source_frame": dict(source_frame), "connection_generation": 1,
                "war_id": war_id, "army_id": 83886367,
                "origin_province_id": 2610,
                "target_province_id": int(step.rsplit("-", 1)[-1]),
                "selected_step": step, "source_kind": "native_selected_step_price",
                "source": quote_source, "upper_bound_raw": 0,
            },
        }

    def test_r0321_synthetic_two_defender_route_reads_before_cash_without_move(self):
        frame, rows, actions, move_step = self._r0321_two_defender_inputs()
        first_hop = 2614
        short_preview_step = f"preview-move-army-83886367-to-{first_hop}"
        short_contact_step = query_route_contact_horizon_step(
            83886367, first_hop, (50331920, 83886484)
        )
        actions.update((short_preview_step, short_contact_step))
        full_horizon = rows[1]["result"]["route_contact_horizon"]
        self.assertEqual(
            full_horizon["subject_route"]["arrival_date_raws"][0]
            - frame["date_raw"], 168,
        )
        self.assertEqual(
            full_horizon["horizon_end_date_raw"] - frame["date_raw"], 24,
        )
        short_preview, short_contact = rows[2:4]
        rows = [rows[0], rows[1], rows[4]]

        def plan(current_frame=frame, current_rows=rows):
            with (
                mock.patch("xar_autoplayer.strategy.plan_raiktor_formal_exit",
                           return_value=None),
                mock.patch("xar_autoplayer.strategy._choose_one_life_turn_core",
                           return_value={"phase": "native_war_no_safe_exact_route",
                                         "selected_step": None}),
                mock.patch(
                    "xar_autoplayer.strategy._provisional_defense_research_assessment",
                    return_value={"status": "same_frame_encounter_scope_mismatch"},
                ),
            ):
                return choose_one_life_turn(
                    current_rows, snapshot=current_frame, action_steps=actions,
                    bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
                )

        first = plan()
        self.assertEqual(first["selected_step"], short_preview_step, first)
        self.assertFalse(first["active_attack_allowed"])
        failed_preview = {"index": 7, "command": short_preview_step, "ok": False}
        self.assertIsNone(plan(current_rows=rows + [failed_preview])["selected_step"])

        rows.append(short_preview)
        second = plan()
        self.assertEqual(second["selected_step"], short_contact_step, second)
        self.assertFalse(second["active_attack_allowed"])
        failed_contact = {"index": 8, "command": short_contact_step, "ok": False}
        self.assertIsNone(plan(current_rows=rows + [failed_contact])["selected_step"])

        rows.append(short_contact)
        without_cash = plan()
        self.assertIsNone(without_cash["selected_step"], without_cash)
        self.assertFalse(without_cash["active_attack_allowed"])
        frame["native_revision"] += 1
        stale = plan()
        self.assertNotEqual(stale["selected_step"], move_step, stale)
        frame["native_revision"] -= 1
        frame["war_first_hop_cash_bound_v1"] = self._r0321_cash_package(
            frame, move_step
        )
        admitted = plan()
        self.assertEqual(admitted["selected_step"], move_step, admitted)
        self.assertFalse(admitted["active_attack_allowed"])

    def test_r0321_cash_and_two_horizons_allow_only_contact_free_first_hop(self):
        frame, rows, actions, step = self._r0321_two_defender_inputs()

        def plan(current_frame=frame, current_rows=rows, current_actions=actions,
                 provisional=None):
            with mock.patch(
                "xar_autoplayer.strategy._provisional_defense_research_assessment",
                return_value=provisional or {
                    "status": "same_frame_encounter_scope_mismatch"
                },
            ):
                return _primary_defender_siege_forecast_ingress(
                    {"phase": "native_war_no_safe_exact_route", "selected_step": None},
                    commands=current_rows, snapshot=current_frame,
                    action_steps=current_actions,
                    bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
                )

        blocked = plan()
        self.assertEqual(blocked["phase"], "native_war_siege_forecast_inputs_observed")
        self.assertIsNone(blocked["selected_step"])
        frame["war_first_hop_cash_bound_v1"] = self._r0321_cash_package(frame, step)
        admitted = plan()
        self.assertEqual(admitted["selected_step"], step, admitted)
        self.assertEqual(admitted["phase"],
                         "native_war_siege_forecast_unavailable_first_hop_move")
        self.assertFalse(admitted["active_attack_allowed"])
        self.assertEqual(admitted["forecast_status"], "research_only")
        self.assertTrue(admitted["daily_recheck_required"])
        multi = {"status": "multi_defender_research_only", "planner_usable": False}
        self.assertEqual(plan(provisional=multi)["selected_step"], step)
        self.assertIsNone(plan(provisional={**multi, "planner_usable": True})["selected_step"])
        self.assertIsNone(plan(provisional={"status": "provisional_admissible"})["selected_step"])

        for change in (
            lambda f, r, a: r[1]["result"]["route_contact_horizon"].update(
                horizon_end_date_raw=f["date_raw"] + 48),
            lambda f, r, a: r[3]["result"]["route_contact_horizon"].update(
                one_day_contact_free=False),
            lambda f, r, a: r[3]["result"]["route_contact_horizon"].update(
                horizon_end_date_raw=f["date_raw"] + 48),
            lambda f, r, a: r[3]["result"]["route_contact_horizon"]
                ["hostile_routes"][1].update(current_province_id=3719),
            lambda f, r, a: r[4]["result"].update(accepted=False),
            lambda f, r, a: r.pop(2),
            lambda f, r, a: r.pop(3),
            lambda f, r, a: a.clear(),
            lambda f, r, a: f.update(active_event={"event_id": 1}),
            lambda f, r, a: f["war_first_hop_cash_bound_v1"]
                ["selected_step_quote"].update(selected_step="move-army-83886367-to-2629"),
            lambda f, r, a: f["war_first_hop_cash_bound_v1"]
                ["selected_step_quote"].update(connection_generation=2),
            lambda f, r, a: f["war_first_hop_cash_bound_v1"]
                ["selected_step_quote"].update(source="unbound-fee"),
            lambda f, r, a: f["war_first_hop_cash_bound_v1"]
                ["war_cash_resource"].update(horizon_days=0),
            lambda f, r, a: f["war_first_hop_cash_bound_v1"]
                ["war_cash_resource"].update(observed_treasury_raw=0),
            lambda f, r, a: (
                f["played_character_gold"].update(raw=1_000_000),
                f["war_first_hop_cash_bound_v1"]["war_cash_resource"]
                    .update(observed_treasury_raw=1_000_000),
            ),
        ):
            f, r, a = copy.deepcopy(frame), copy.deepcopy(rows), set(actions)
            change(f, r, a)
            result = plan(f, r, a)
            self.assertIsNone(result["selected_step"], result)
            self.assertIsNot(result.get("active_attack_allowed"), True)

    def test_r0321_formal_plan_requires_cash_and_never_uses_first_hop_as_attack(self):
        frame, rows, actions, step = self._r0321_two_defender_inputs()
        baseline = {"phase": "native_war_no_safe_exact_route", "selected_step": None}

        def formal(current_frame=frame, current_rows=rows):
            with (
                mock.patch("xar_autoplayer.strategy.plan_raiktor_formal_exit",
                           return_value=None),
                mock.patch("xar_autoplayer.strategy._choose_one_life_turn_core",
                           return_value=baseline),
                mock.patch(
                    "xar_autoplayer.strategy._provisional_defense_research_assessment",
                    return_value={"status": "multi_defender_research_only",
                                  "planner_usable": False},
                ),
            ):
                return choose_one_life_turn(
                    current_rows, snapshot=current_frame, action_steps=actions,
                    bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
                )

        without_cash = formal()
        self.assertIsNone(without_cash["selected_step"], without_cash)
        self.assertFalse(without_cash["active_attack_allowed"])
        frame["war_first_hop_cash_bound_v1"] = self._r0321_cash_package(frame, step)
        safe = formal()
        self.assertEqual(safe["selected_step"], step, safe)
        self.assertFalse(safe["active_attack_allowed"])
        self.assertTrue(safe["daily_recheck_required"])

        # Even with a complete cash package, an adjacent target is a battle.
        # Rebind the synthetic V3 query to that exact direct-contact edge.
        direct_frame, direct_rows = copy.deepcopy(frame), copy.deepcopy(rows)
        direct_rows[0]["result"]["route_preview"]["route_province_ids"] = [2629]
        direct_horizon = direct_rows[1]["result"]["route_contact_horizon"]
        direct_horizon["subject_route"]["route_province_ids"] = [2629]
        direct_horizon["subject_route"]["arrival_date_raws"] = [
            direct_frame["date_raw"] + 24
        ]
        direct_horizon["one_day_contact_free"] = False
        direct_horizon["conflicts"] = [
            {"hostile_army_id": 50331920, "province_id": 2629}
        ]
        direct_step = query_combat_simulation_inputs_v3_step(
            2629, 2610, [83886367], [50331920, 83886484]
        )
        direct_frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 2610
        direct_rows[4]["command"] = direct_step
        direct_rows[4]["result"]["step"] = direct_step
        direct = formal(direct_frame, direct_rows)
        self.assertIsNone(direct["selected_step"], direct)
        self.assertFalse(direct["active_attack_allowed"])

    def _r0271_replay_inputs(self):
        report = json.loads(R0265_REPORT.with_name(
            "WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0271-blocker-excerpt.json"
        ).read_text(encoding="utf-8"))
        plan = report["first_blocker"]["plan"]
        observed = plan["route_contact_horizon"]
        date_raw = observed["date_raw"]
        frame = self._frame(date_raw=date_raw)
        player = _army(
            83886367, soldiers=2332, province_id=2610, controllable=True,
            army_state="regular", army_state_code=1,
            route_province_ids=[], in_combat=False, retreating=False,
        )
        siege = _army(
            50331920, soldiers=1436, province_id=2629, controllable=False,
            army_state="sieging", army_state_code=3,
            route_province_ids=[], in_combat=False, retreating=False,
        )
        approaching = _army(
            83886484, soldiers=311, province_id=3719, controllable=False,
            move_target_province_id=2629, army_state="moving", army_state_code=7,
            route_province_ids=[8652, 1038, 1036, 2629],
            in_combat=False, retreating=False,
        )
        frame["player_armies"] = [player]
        frame["active_wars"] = [_war(
            war_id=16777231, allied_armies=[player],
            enemy_armies=[siege, approaching], score=-21,
            player_side="defender", player_is_primary_war_leader=True,
            war_objective_province_ids=[2610],
        )]
        frame["army_strengths"] = [
            _army_strength(83886367, "player", [16777231], current=2332),
            _army_strength(50331920, "active_war_enemy", [16777231], current=1436),
            _army_strength(83886484, "active_war_enemy", [16777231], current=311),
        ]
        route = plan["route_preview"]["route_province_ids"]
        preview = _preview_row(
            1, army_id=83886367, origin=2610, target=2629,
            date_raw=date_raw, route=route,
        )
        contact = _route_contact_row(
            2, army_id=83886367, origin=2610, target=2629,
            date_raw=date_raw, route=route,
            hostile_ids=(50331920, 83886484), contact_free=True,
        )
        contact["result"]["route_contact_horizon"] = copy.deepcopy(observed)
        contact["result"]["route_contact_horizon"]["snapshot_revision"] = 90
        return frame, [preview, contact]

    def test_r0271_earlier_hostile_arrival_allows_only_bounded_first_hop(self):
        frame, rows = self._r0271_replay_inputs()
        steps = {
            "preview-move-army-83886367-to-2614",
            query_route_contact_horizon_step(
                83886367, 2614, (50331920, 83886484)
            ),
            "move-army-83886367-to-2614",
        }

        def plan():
            return _primary_defender_siege_forecast_ingress(
                {"phase": "native_war_stationary_objective_hold_sentinel",
                 "selected_step": "war-objective-hold-sentinel"},
                commands=rows, snapshot=frame, action_steps=steps,
                bridge_capabilities=set(),
            )

        first = plan()
        self.assertEqual(first["selected_step"], "preview-move-army-83886367-to-2614", first)
        self.assertEqual(first["participant_partition"]["reason"],
                         "offsite_hostile_may_join_by_target_entry")
        self.assertFalse(first["active_attack_allowed"])
        rows.append(_preview_row(
            3, army_id=83886367, origin=2610, target=2614,
            date_raw=frame["date_raw"], route=[2614],
        ))
        second = plan()
        self.assertEqual(second["selected_step"],
                         query_route_contact_horizon_step(
                             83886367, 2614, (50331920, 83886484)))
        short_contact = _route_contact_row(
            4, army_id=83886367, origin=2610, target=2614,
            date_raw=frame["date_raw"], route=[2614],
            hostile_ids=(50331920, 83886484), contact_free=True,
            hostile_provinces={50331920: 2629, 83886484: 3719},
        )
        rows.append(short_contact)
        third = plan()
        self.assertEqual(third["phase"], "native_war_siege_uncertain_first_hop_move")
        self.assertEqual(third["selected_step"], "move-army-83886367-to-2614")
        self.assertEqual(third["forecast_status"], "participant_scope_unresolved")
        self.assertTrue(third["daily_recheck_required"])
        self.assertFalse(third["active_attack_allowed"])

        short_contact["result"]["route_contact_horizon"]["conflicts"] = [
            {"hostile_army_id": 83886484, "province_id": 2614}
        ]
        self.assertIsNone(plan()["selected_step"])
        short_contact["result"]["route_contact_horizon"]["conflicts"] = []
        short_contact["result"]["route_contact_horizon"]["one_day_contact_free"] = False
        self.assertIsNone(plan()["selected_step"])
        short_contact["result"]["route_contact_horizon"]["one_day_contact_free"] = True
        short_contact["result"]["route_contact_horizon"]["hostile_routes"][1]["current_province_id"] = 2629
        self.assertIsNone(plan()["selected_step"])
        short_contact["result"]["route_contact_horizon"]["hostile_routes"][1]["current_province_id"] = 3719
        short_contact["result"]["route_contact_horizon"]["date_raw"] += 24
        self.assertEqual(plan()["selected_step"],
                         query_route_contact_horizon_step(
                             83886367, 2614, (50331920, 83886484)))
        short_contact["result"]["route_contact_horizon"]["date_raw"] -= 24
        rows[1]["result"]["route_contact_horizon"]["hostile_routes"][1]["current_province_id"] = 2629
        mismatch = plan()
        self.assertIsNone(mismatch["selected_step"])
        self.assertEqual(mismatch["participant_partition"]["reason"],
                         "war_contact_position_mismatch")

    def test_r0265_route_only_partitions_if_war_row_positions_agree(self):
        report = json.loads(R0265_REPORT.read_text(encoding="utf-8"))
        plan = report["first_blocker"]["plan"]
        relief = plan["siege_relief"]
        contact = plan["route_contact_horizon"]
        war = {"enemy_armies": [
            {"army_id": 50331920, "current_province_id": 2629,
             "army_state": "sieging", "army_state_code": 3},
            {"army_id": 83886484, "current_province_id": 3660,
             "army_state": "moving", "army_state_code": 7},
        ]}
        result = _siege_forecast_participant_partition(
            war, relief["army_strength_balance"], contact,
            army_id=relief["army_id"], target_province_id=relief["target_province_id"],
        )
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["defender_army_ids"], [50331920])
        self.assertEqual(result["offsite_hostile_army_ids"], [83886484])
        self.assertEqual(result["subject_target_arrival_date_raw"], 53218680)
        self.assertEqual(result["offsite_target_arrivals"][0]["target_arrival_date_raw"],
                         53219928)
        # The R0265 candidate label was polluted by a local variable collision;
        # the separate R0264 war row puts this moving army at 3660.  A supplied
        # war row that instead puts it at the target must still fail the
        # same-frame contact position check.
        war["enemy_armies"][1]["current_province_id"] = 2629
        mismatch = _siege_forecast_participant_partition(
            war, relief["army_strength_balance"], contact,
            army_id=relief["army_id"], target_province_id=relief["target_province_id"],
        )
        self.assertEqual(mismatch["reason"], "war_contact_position_mismatch")

    def test_offsite_hostile_is_not_target_defender_and_cannot_authorize_contact(self):
        frame = self._frame()
        moving = _army(
            22, soldiers=311, province_id=40, controllable=False,
            army_state="moving", army_state_code=7,
            route_province_ids=[33, 32], in_combat=False, retreating=False,
        )
        frame["active_wars"][0]["enemy_armies"].append(moving)
        frame["army_strengths"].append(
            _army_strength(22, "active_war_enemy", [95], current=311,
                           base_power_raw=311_000_000)
        )
        candidate = _primary_defender_siege_relief_assessment(
            frame, commands=[], active_wars=frame["active_wars"],
            controlled_armies=frame["player_armies"],
            pursuit_army=frame["player_armies"][0],
        )
        self.assertEqual(candidate["enemy_army_id"], 21)
        self.assertEqual(candidate["target_province_id"], 32)
        preview = _preview_row(
            1, origin=30, target=32, date_raw=frame["date_raw"], route=[31, 32]
        )
        contact = _route_contact_row(
            2, origin=30, target=32, date_raw=frame["date_raw"],
            route=[31, 32], hostile_ids=(21, 22), contact_free=True,
            hostile_provinces={21: 32, 22: 40},
        )
        horizon = contact["result"]["route_contact_horizon"]
        horizon["hostile_routes"][1].update({
            "current_province_id": 40,
            "route_province_ids": [33, 32],
            "arrival_date_raws": [frame["date_raw"] + 72, frame["date_raw"] + 120],
        })
        balance = {
            "friendly_army_ids": [11], "enemy_army_ids": [21, 22]
        }
        partition = _siege_forecast_participant_partition(
            frame["active_wars"][0], balance, horizon,
            army_id=11, target_province_id=32,
        )
        self.assertEqual(partition["status"], "available")
        self.assertEqual(partition["defender_army_ids"], [21])
        self.assertEqual(partition["offsite_hostile_army_ids"], [22])
        self.assertEqual(partition["subject_target_arrival_date_raw"],
                         frame["date_raw"] + 48)

        steps = {
            query_route_contact_horizon_step(11, 32, (21, 22)),
            query_combat_simulation_inputs_v3_step(32, 31, [11], [21]),
        }
        result = _primary_defender_siege_forecast_ingress(
            {"phase": "native_war_no_safe_exact_route", "selected_step": None},
            commands=[preview, contact], snapshot=frame, action_steps=steps,
            bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
        )
        self.assertEqual(result["phase"], "native_war_siege_forecast_inputs_query")
        self.assertEqual(result["selected_step"],
                         query_combat_simulation_inputs_v3_step(32, 31, [11], [21]))
        self.assertFalse(result["active_attack_allowed"])

        horizon["hostile_routes"][1]["arrival_date_raws"][1] = frame["date_raw"] + 24
        blocked = _siege_forecast_participant_partition(
            frame["active_wars"][0], balance, horizon,
            army_id=11, target_province_id=32,
        )
        self.assertEqual(blocked["reason"], "offsite_hostile_may_join_by_target_entry")

    def test_offsite_hostile_keeps_immediate_contact_blocked(self):
        frame = self._frame()
        frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 30
        frame["active_wars"][0]["enemy_armies"].append(_army(
            22, soldiers=311, province_id=40, controllable=False,
            army_state="moving", army_state_code=7,
            route_province_ids=[32], in_combat=False, retreating=False,
        ))
        frame["army_strengths"].append(
            _army_strength(22, "active_war_enemy", [95], current=311,
                           base_power_raw=311_000_000)
        )
        preview = _preview_row(
            1, origin=30, target=32, date_raw=frame["date_raw"], route=[32]
        )
        contact = _route_contact_row(
            2, origin=30, target=32, date_raw=frame["date_raw"],
            route=[32], hostile_ids=(21, 22), contact_free=False,
            hostile_provinces={21: 32, 22: 40},
        )
        contact["result"]["route_contact_horizon"]["hostile_routes"][1].update({
            "current_province_id": 40,
            "route_province_ids": [32],
            "arrival_date_raws": [frame["date_raw"] + 72],
        })
        with mock.patch(
            "xar_autoplayer.strategy._provisional_defense_research_assessment",
            return_value={"status": "provisional_admissible"},
        ):
            plan = _primary_defender_siege_forecast_ingress(
                {"phase": "native_war_no_safe_exact_route", "selected_step": None},
                commands=[preview, contact, self._query_row(30)], snapshot=frame,
                action_steps={"move-army-11-to-32"},
                bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
            )
        self.assertEqual(plan["phase"], "native_war_siege_forecast_observation_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertFalse(plan["active_attack_allowed"])
        with mock.patch(
            "xar_autoplayer.strategy._qualified_siege_forecast_move",
            return_value={"status": "ready", "assessment_sha256": "E" * 64},
        ):
            qualified = _primary_defender_siege_forecast_ingress(
                {"phase": "native_war_no_safe_exact_route", "selected_step": None},
                commands=[preview, contact, self._query_row(30)], snapshot=frame,
                action_steps={"move-army-11-to-32"},
                bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
            )
        self.assertEqual(qualified["phase"], "native_war_siege_forecast_observation_blocked")
        self.assertEqual(qualified["required_observation"],
                         "one-day-target-entry-horizon-and-complete-participants")
        self.assertIsNone(qualified["selected_step"])
        self.assertFalse(qualified["active_attack_allowed"])

    def _frame(self, *, date_raw: int = 53_215_920):
        player = _army(
            11, soldiers=2_327, province_id=30, controllable=True,
            army_state="regular", army_state_code=1,
            route_province_ids=[], in_combat=False, retreating=False,
        )
        enemy = _army(
            21, soldiers=1_488, province_id=32, controllable=False,
            army_state="sieging", army_state_code=3,
            route_province_ids=[], in_combat=False, retreating=False,
        )
        war = _war(
            war_id=95, allied_armies=[player], enemy_armies=[enemy],
            score=-12, player_side="defender",
            player_is_primary_war_leader=True,
            war_objective_province_ids=[30],
        )
        frame = {
            **_snapshot(90), "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "native_revision": 90, "date_raw": date_raw,
            "diagnostics": {"connection_generation": 1},
            "episode_run_id": None, "active_wars": [war],
            "player_armies": [player], "army_strengths_status": "available",
            "army_strengths": [
                _army_strength(11, "player", [95], current=2_327,
                               base_power_raw=2_327_000_000),
                _army_strength(21, "active_war_enemy", [95], current=1_488,
                               base_power_raw=1_488_000_000),
            ],
            "combat_simulation_inputs_v3": {"completeness": {}},
            "combat_simulation_inputs_v3_status": "available",
            "combat_simulation_inputs_v3_target_province_id": 32,
            "combat_simulation_inputs_v3_attacker_army_ids": [11],
            "combat_simulation_inputs_v3_defender_army_ids": [21],
            "combat_simulation_inputs_v3_queried_snapshot_id": "session:90",
            "combat_simulation_inputs_v3_queried_revision": 90,
        }
        frame["war_termination_options"] = [{
            "war_id": 95,
            "queried_snapshot_id": "session:90",
            "queried_revision": 90,
            "queried_native_revision": 90,
            "queried_connection_generation": 1,
            "episode_run_id": None,
            "options": {
                "victory": {"available": False, "terms_observable": True},
                "white_peace": {"available": False, "terms_observable": True},
                "surrender": {"available": True, "terms_observable": False},
            },
        }]
        return frame

    def _query_row(self, entry: int, *, index: int = 3):
        step = query_combat_simulation_inputs_v3_step(32, entry, [11], [21])
        return {
            "index": index, "command": step, "ok": True,
            "result": {
                "step": step, "accepted": True, "status": "available",
                "queried_snapshot_id": "session:90",
                "queried_revision": 90, "queried_native_revision": 90,
            },
        }

    def _plan(self, frame, rows):
        steps = {
            "preview-move-army-11-to-32",
            "preview-move-army-11-to-31",
            "move-army-11-to-32", "move-army-11-to-31",
            query_route_contact_horizon_step(11, 32, (21,)),
            query_route_contact_horizon_step(11, 31, (21,)),
        }
        return _primary_defender_siege_forecast_ingress(
            {"phase": "native_war_no_safe_exact_route", "selected_step": None},
            commands=rows, snapshot=frame, action_steps=steps,
            bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
        )

    def test_under_two_to_one_model_admits_only_contact_free_first_hop(self):
        frame = self._frame()
        frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 31
        rows = [
            _preview_row(1, origin=30, target=32,
                         date_raw=frame["date_raw"], route=[31, 32]),
            _route_contact_row(2, origin=30, target=32,
                               date_raw=frame["date_raw"], route=[31, 32],
                               hostile_ids=(21,), contact_free=True,
                               hostile_provinces={21: 32}),
            self._query_row(31),
        ]
        with mock.patch(
            "xar_autoplayer.strategy._provisional_defense_research_assessment",
            return_value={"status": "provisional_admissible",
                          "model_resolved_win_wilson_low": 0.99},
        ) as trial:
            preview = self._plan(frame, rows)
            self.assertEqual(preview["selected_step"], "preview-move-army-11-to-31")
            rows.append(_preview_row(4, origin=30, target=31,
                                     date_raw=frame["date_raw"], route=[31]))
            contact = self._plan(frame, rows)
            self.assertEqual(contact["selected_step"],
                             query_route_contact_horizon_step(11, 31, (21,)))
            rows.append(_route_contact_row(
                5, origin=30, target=31, date_raw=frame["date_raw"],
                route=[31], hostile_ids=(21,), contact_free=True,
            ))
            move = self._plan(frame, rows)
        self.assertEqual(move["selected_step"], "move-army-11-to-31")
        self.assertEqual(move["phase"], "native_war_provisional_defense_short_move")
        self.assertFalse(move["active_attack_allowed"])
        self.assertEqual(move["forecast_status"], "provisional_trial")
        self.assertEqual(trial.call_count, 3)

    def test_immediate_contact_needs_current_model_and_exact_target_conflict(self):
        frame = self._frame()
        frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 30
        rows = [
            _preview_row(1, origin=30, target=32,
                         date_raw=frame["date_raw"], route=[32]),
            _route_contact_row(2, origin=30, target=32,
                               date_raw=frame["date_raw"], route=[32],
                               hostile_ids=(21,), contact_free=False,
                               hostile_provinces={21: 32}),
            self._query_row(30),
        ]
        with mock.patch(
            "xar_autoplayer.strategy._provisional_defense_research_assessment",
            return_value={"status": "provisional_admissible"},
        ):
            move = self._plan(frame, rows)
        self.assertEqual(move["phase"], "native_war_provisional_defense_contact_move")
        self.assertEqual(move["selected_step"], "move-army-11-to-32")
        self.assertTrue(move["active_attack_allowed"])
        with mock.patch(
            "xar_autoplayer.strategy._provisional_defense_research_assessment",
            return_value={"status": "model_risk_budget_exceeded"},
        ):
            blocked = self._plan(frame, rows)
        self.assertIsNone(blocked["selected_step"])

    def test_two_defender_one_day_contact_cannot_consume_research_canary(self):
        frame = self._frame()
        frame["active_wars"][0]["enemy_armies"].append(_army(
            22, soldiers=311, province_id=32, controllable=False,
            army_state="sieging", army_state_code=3,
            route_province_ids=[], in_combat=False, retreating=False,
        ))
        frame["army_strengths"].append(
            _army_strength(22, "active_war_enemy", [95], current=311)
        )
        frame["diagnostics"]["hello"] = {
            "ck3_build_match": True,
            "expected_ck3_sha256":
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        }
        frame["succession_lifecycle"] = {
            "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
        }
        frame["combat_simulation_inputs_v3_attacker_entry_province_id"] = 30
        frame["combat_simulation_inputs_v3_defender_army_ids"] = [21, 22]
        frame["combat_simulation_inputs_v3"] = {
            "completeness": {"input_observation_ready": True},
            "base_inputs": {
                "target_province_id": 32,
                "scenario": {
                    "attacker_entry_province_id": 30,
                    "attacker_army_ids": [11],
                    "defender_army_ids": [21, 22],
                    "attacker_side": "player_or_allied",
                    "defender_side": "enemy",
                    "actual_route_dependency": False,
                },
            },
        }
        preview = _preview_row(
            1, origin=30, target=32, date_raw=frame["date_raw"], route=[32],
        )
        contact = _route_contact_row(
            2, origin=30, target=32, date_raw=frame["date_raw"],
            route=[32], hostile_ids=(21, 22), contact_free=False,
            hostile_provinces={21: 32, 22: 32},
        )
        query = self._query_row(30)
        query_step = query_combat_simulation_inputs_v3_step(32, 30, [11], [21, 22])
        query["command"] = query_step
        query["result"]["step"] = query_step
        rows = [preview, contact, query]
        forecast = {
            "status": "estimated", "input_sha256": "A" * 64,
            "advantage_input": {}, "simulator_build": "test-only",
            "sample_count": 512, "player_wins": 512, "player_losses": 0,
            "no_resolution": 0, "resolved_win_wilson95": {"lower": 0.99},
            "player_p90_hard_loss_raw": 0,
            "player_p90_hard_loss_fraction": 0.0,
            "player_stack_wipe_probability": 0.0,
            "commander_or_knight_death_probability": None,
            "missing_required_domains": [],
        }

        def plan():
            return _primary_defender_siege_forecast_ingress(
                {"phase": "native_war_no_safe_exact_route", "selected_step": None},
                commands=rows, snapshot=frame,
                action_steps={"move-army-11-to-32"},
                bridge_capabilities={QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY},
            )

        with mock.patch(
            "xar_autoplayer.strategy.forecast_fixed_contact", return_value=forecast,
        ):
            blocked = plan()
        self.assertEqual(blocked["provisional_forecast"]["status"],
                         "multi_defender_research_only", blocked)
        self.assertIsNone(blocked["selected_step"])
        self.assertFalse(blocked["active_attack_allowed"])

        # Defence in depth: a stale or mistaken admissible result still cannot
        # enter the one-day contact action when two defenders are observed.
        with mock.patch(
            "xar_autoplayer.strategy._provisional_defense_research_assessment",
            return_value={"status": "provisional_admissible"},
        ):
            misclassified = plan()
        self.assertIsNone(misclassified["selected_step"])
        self.assertFalse(misclassified["active_attack_allowed"])

    def test_existing_frozen_live_input_runs_provisional_model_without_native_planner_gate(self):
        fixture = json.loads(
            (FIXTURES / "live_rev4_player_attacks_357.json").read_text(encoding="utf-8")
        )
        frame = {
            "diagnostics": {"hello": {
                "ck3_build_match": True,
                "expected_ck3_sha256": fixture["executable_sha256"],
            }},
            "succession_lifecycle": {
                "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
            },
            "combat_simulation_inputs_v3": {
                "completeness": {"input_observation_ready": True,
                                 "monte_carlo_ready": False},
                "base_inputs": fixture["combat_simulation_inputs"],
            },
            "snapshot_id": fixture["capture"]["snapshot_id"],
            "revision": fixture["capture"]["revision"],
            "native_revision": fixture["capture"]["native_revision"],
            "date_raw": fixture["capture"]["date_raw"],
        }
        result = _provisional_defense_research_assessment(
            frame, target_province_id=2581, entry_province_id=2587,
            attacker_army_id=83_886_341, defender_army_ids=(357,),
            friendly_current_soldiers=1_482,
        )
        self.assertEqual(result["sample_count"], 512)
        self.assertFalse(result["calibrated_win_probability_available"])
        self.assertIn(result["status"],
                      {"provisional_admissible", "model_risk_budget_exceeded"})

    def test_two_exact_target_defenders_keep_full_ordered_forecast_scope(self):
        fixture = json.loads(
            (FIXTURES / "live_rev4_player_attacks_357.json").read_text(encoding="utf-8")
        )
        base = copy.deepcopy(fixture["combat_simulation_inputs"])
        second = copy.deepcopy(base["armies"][1])
        second["army_id"] = 358
        second["native_carmy_id"] += 1
        if second["commander"]["character_id"] is not None:
            second["commander"]["character_id"] += 100_000
        for regiment in second["regiments"]:
            regiment["regiment_id"] += 100_000_000
        for knight in second["knights"]["members"]:
            knight["character_id"] += 100_000
            knight["source_regiment_id"] += 100_000_000
            knight["army_id"] = second["native_carmy_id"]
        base["armies"].append(second)
        base["scenario"]["defender_army_ids"] = [357, 358]
        frame = {
            "diagnostics": {"hello": {
                "ck3_build_match": True,
                "expected_ck3_sha256": fixture["executable_sha256"],
            }},
            "succession_lifecycle": {
                "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
            },
            "combat_simulation_inputs_v3": {
                "completeness": {"input_observation_ready": True},
                "base_inputs": base,
            },
            **fixture["capture"],
        }
        freeze_combat_simulation_input(base, capture=fixture["capture"])
        forecast = forecast_fixed_contact(
            frame["combat_simulation_inputs_v3"],
            target_province_id=2581, attacker_entry_province_id=2587,
            attacker_army_ids=(83_886_341,), defender_army_ids=(357, 358),
            capture=fixture["capture"], sample_count=16, horizon_days=4,
        )
        self.assertEqual(forecast["status"], "estimated", forecast)
        exact = _provisional_defense_research_assessment(
            frame, target_province_id=2581, entry_province_id=2587,
            attacker_army_id=83_886_341, defender_army_ids=(357, 358),
            friendly_current_soldiers=1_482,
        )
        self.assertEqual(exact["status"], "multi_defender_research_only", exact)
        self.assertFalse(exact["planner_usable"])
        self.assertEqual(exact["sample_count"], 512)
        self.assertFalse(exact["calibrated_win_probability_available"])
        reversed_roster = _provisional_defense_research_assessment(
            frame, target_province_id=2581, entry_province_id=2587,
            attacker_army_id=83_886_341, defender_army_ids=(358, 357),
            friendly_current_soldiers=1_482,
        )
        self.assertEqual(reversed_roster["status"], "same_frame_encounter_scope_mismatch")

    def test_complete_base_survives_unavailable_v3_phase_for_provisional_trial(self):
        fixture = json.loads(
            (FIXTURES / "live_rev4_player_attacks_357.json").read_text(encoding="utf-8")
        )
        frame = {
            "diagnostics": {"hello": {
                "ck3_build_match": True,
                "expected_ck3_sha256": fixture["executable_sha256"],
            }},
            "succession_lifecycle": {
                "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
            },
            "combat_simulation_inputs_v3": {
                "schema_version": 3,
                "contract_stage": "production_exact_132_refs",
                "completeness": {"input_observation_ready": False},
                "base_inputs": fixture["combat_simulation_inputs"],
                "phase_event_inputs": {"status": "unavailable"},
            },
            "snapshot_id": fixture["capture"]["snapshot_id"],
            "revision": fixture["capture"]["revision"],
            "native_revision": fixture["capture"]["native_revision"],
            "date_raw": fixture["capture"]["date_raw"],
        }
        result = _provisional_defense_research_assessment(
            frame, target_province_id=2581, entry_province_id=2587,
            attacker_army_id=83_886_341, defender_army_ids=(357,),
            friendly_current_soldiers=1_482,
        )
        self.assertIn(result["status"],
                      {"provisional_admissible", "model_risk_budget_exceeded"})
        self.assertEqual(result["advantage_input"]["fallback_reason"],
                         "phase_event_inputs_unavailable")


if __name__ == "__main__":
    unittest.main()
