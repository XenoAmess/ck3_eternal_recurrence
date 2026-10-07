"""One synthetic actual4-version relief consumer case; no native/game calls.

The model operands are retained historical .3 input, and the schema2 context
and relief geometry are synthetic. They do not represent an actual4 sample.
"""

import copy
import json
from pathlib import Path
from unittest import TestCase

from xar_autoplayer.bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    query_combat_simulation_inputs_step,
)
from xar_autoplayer.bridge.combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    query_combat_simulation_inputs_v3_step,
)
from xar_autoplayer.simulation.battle_v2_constructor_advantage import (
    V2_CONSTRUCTOR_ADVANTAGE_SOURCE,
)
from xar_autoplayer.strategy import _primary_defender_siege_forecast_ingress

from ck3_autonomous_player.tests.unit import test_combat_provisional_defense_canary as canary
from ck3_autonomous_player.tests.unit.test_gameplay_bridge import (
    _army, _army_strength, _preview_row, _route_contact_row, _war,
)


FIXTURE = Path(__file__).parents[1] / "fixtures/combat/live_814_12003_general_battle_v2.json"


class SiegeReliefV2ConstructorConsumer12004Test(TestCase):
    def test_v2_only_query_then_production_relief_forecast_without_complete_mc(self):
        saved = json.loads(FIXTURE.read_text(encoding="utf-8"))
        base = copy.deepcopy(saved["frame"]["combat_simulation_inputs"])
        attacker_id, defender_id = 218104048, 134218098
        target, entry = 2606, 8756
        commanders = {
            army["army_id"]: army["commander"]["character_id"]
            for army in base["armies"]
        }
        base["contextual_advantage"] = {
            "schema_version": 2, "status": "available",
            "scope": "hypothetical_constructor_context", "scale": 100_000,
            "target_province_id": target,
            "partial_context_observation_ready": True,
            "complete_encounter_advantage_ready": False,
            "synthetic_helper_total_match": True,
            "base_constructor_accumulator_raw": -300_000,
            "synthetic_zero_roll_total_raw": -150_000,
            "sides": [
                {"side_index": 0, "ordered_public_cunit_ids": [attacker_id],
                 "selected_commander_character_id": commanders[attacker_id],
                 "commander_dynamic_raw": 100_000, "side_dynamic_raw": 50_000,
                 "target_conditionals_residual_raw": 50_000,
                 "side_total_raw": 200_000},
                {"side_index": 1, "ordered_public_cunit_ids": [defender_id],
                 "selected_commander_character_id": commanders[defender_id],
                 "commander_dynamic_raw": 20_000, "side_dynamic_raw": 20_000,
                 "target_conditionals_residual_raw": 10_000,
                 "side_total_raw": 50_000},
            ],
        }
        frame = canary.ProvisionalDefenseCanaryTests()._frame(date_raw=53288448)
        for key in tuple(frame):
            if key.startswith("combat_simulation_inputs_v3"):
                frame.pop(key)
        frame["diagnostics"]["hello"] = {
            "ck3_build_match": True,
            "expected_ck3_sha256":
                "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
        }
        frame["succession_lifecycle"] = {
            "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
        }
        player = _army(
            attacker_id, soldiers=2327, province_id=entry, controllable=True,
            army_state="regular", army_state_code=1, route_province_ids=[],
            in_combat=False, retreating=False,
        )
        enemy = _army(
            defender_id, soldiers=1488, province_id=target, controllable=False,
            army_state="sieging", army_state_code=3, route_province_ids=[],
            in_combat=False, retreating=False,
        )
        frame["player_armies"] = [player]
        frame["active_wars"] = [_war(
            war_id=95, allied_armies=[player], enemy_armies=[enemy], score=-12,
            player_side="defender", player_is_primary_war_leader=True,
            war_objective_province_ids=[entry],
        )]
        frame["army_strengths"] = [
            _army_strength(attacker_id, "player", [95], current=2327,
                           base_power_raw=2_327_000_000),
            _army_strength(defender_id, "active_war_enemy", [95], current=1488,
                           base_power_raw=1_488_000_000),
        ]
        rows = [
            _preview_row(1, army_id=attacker_id, origin=entry, target=target,
                         date_raw=frame["date_raw"], route=[target]),
            _route_contact_row(2, army_id=attacker_id, origin=entry, target=target,
                               date_raw=frame["date_raw"], route=[target],
                               hostile_ids=(defender_id,), contact_free=False,
                               hostile_provinces={defender_id: target}),
        ]
        step = query_combat_simulation_inputs_step(target, entry, [attacker_id], [defender_id])

        def plan(capabilities=None):
            return _primary_defender_siege_forecast_ingress(
                {"phase": "native_war_no_safe_exact_route", "selected_step": None},
                commands=rows, snapshot=frame,
                action_steps={f"move-army-{attacker_id}-to-{target}"},
                bridge_capabilities=(
                    {QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY}
                    if capabilities is None else capabilities
                ),
            )

        self.assertEqual(plan()["selected_step"], step)
        preferred = plan({QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
                          QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY})
        self.assertEqual(preferred["selected_step"], query_combat_simulation_inputs_v3_step(
            target, entry, [attacker_id], [defender_id],
        ))
        frame.update({
            "combat_simulation_inputs": base,
            "combat_simulation_inputs_status": "available",
            "combat_simulation_inputs_target_province_id": target,
            "combat_simulation_inputs_attacker_entry_province_id": entry,
            "combat_simulation_inputs_attacker_army_ids": [attacker_id],
            "combat_simulation_inputs_defender_army_ids": [defender_id],
            "combat_simulation_inputs_queried_snapshot_id": frame["snapshot_id"],
            "combat_simulation_inputs_queried_revision": frame["revision"],
        })
        rows.append({
            "index": 3, "command": step, "ok": True,
            "result": {"step": step, "accepted": True, "status": "available",
                       "queried_snapshot_id": frame["snapshot_id"],
                       "queried_revision": frame["revision"],
                       "queried_native_revision": frame["native_revision"]},
        })
        result = plan()
        forecast = result["provisional_forecast"]
        self.assertIn(forecast["status"],
                      {"provisional_admissible", "model_risk_budget_exceeded"})
        self.assertEqual(forecast["sample_count"], 512)
        self.assertEqual(forecast["advantage_input"]["source"], V2_CONSTRUCTOR_ADVANTAGE_SOURCE)
        self.assertEqual(forecast["advantage_input"]["zero_roll_raw"], -150_000)
        self.assertFalse(forecast["advantage_input"]["complete_encounter_advantage_ready"])
        self.assertFalse(base["completeness"]["monte_carlo_ready"])
        self.assertFalse(forecast["calibrated_win_probability_available"])
        self.assertIn("phase_event_rng_and_effects", forecast["unmodeled_domains"])
        if forecast["status"] == "provisional_admissible":
            self.assertEqual(result["phase"], "native_war_provisional_defense_contact_move")
            self.assertEqual(result["selected_step"], f"move-army-{attacker_id}-to-{target}")
            self.assertTrue(result["active_attack_allowed"])
        else:
            self.assertIsNone(result["selected_step"])
            self.assertFalse(result["active_attack_allowed"])
