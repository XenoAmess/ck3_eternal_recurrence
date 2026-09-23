from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer.strategy import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    _primary_defender_siege_forecast_ingress,
    _provisional_defense_research_assessment,
    query_combat_simulation_inputs_v3_step,
    query_route_contact_horizon_step,
)

from ck3_autonomous_player.tests.unit.test_gameplay_bridge import (
    _army,
    _army_strength,
    _preview_row,
    _route_contact_row,
    _snapshot,
    _war,
)


FIXTURES = Path(__file__).parents[1] / "fixtures" / "combat"


class ProvisionalDefenseCanaryTests(unittest.TestCase):
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
                               hostile_ids=(21,), contact_free=True),
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
                               hostile_ids=(21,), contact_free=False),
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


if __name__ == "__main__":
    unittest.main()
