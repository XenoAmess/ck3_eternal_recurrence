"""One compound actual-base replay; no game/runtime operation."""

import copy
import json
from pathlib import Path
from unittest import TestCase, mock

from xar_autoplayer.bridge.combat_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY,
    combat_simulation_encounter_scope,
    normalize_combat_simulation_inputs,
)
from xar_autoplayer.bridge.combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
)
from xar_autoplayer.strategy import _general_battle_forecast_ingress


FIXTURE = Path(__file__).parents[1] / "fixtures/combat/live_814_12003_general_battle_v2.json"


class GeneralBattleV2Actual814Test(TestCase):
    def test_actual_base_and_missing_or_stale_frame(self):
        saved = json.loads(FIXTURE.read_text(encoding="utf-8"))
        original = copy.deepcopy(saved)
        frame = saved["frame"]
        base = frame["combat_simulation_inputs"]
        scope = combat_simulation_encounter_scope(frame, [218104048], [134218098])
        normalized = normalize_combat_simulation_inputs(
            base, expected_target_province_id=2606,
            expected_attacker_entry_province_id=8756, expected_encounter_scope=scope,
        )
        self.assertTrue(normalized["completeness"]["input_observation_ready"])
        self.assertFalse(normalized["completeness"]["monte_carlo_ready"])
        frame["combat_simulation_inputs"] = normalized
        command = {
            "index": 1, "command": saved["query_result_binding"]["step"],
            "ok": True, "result": saved["query_result_binding"],
        }
        expected_query = "query-combat-simulation-inputs-v2-2606-8756-a-1-218104048-d-1-134218098"

        def call(current, *, history=None, capabilities=None):
            return _general_battle_forecast_ingress(
                saved["baseline"], commands=[command] if history is None else history,
                snapshot=current,
                action_steps={"preview-move-army-218104048-to-2618"},
                bridge_capabilities=(
                    {QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY}
                    if capabilities is None else capabilities
                ),
            )

        # Route metadata is an actual earlier clip. Mock only its helper seams;
        # the production V2 frame/partition/native/public/history checks run.
        def preview(*args, **kwargs):
            return saved["route_preview"] if kwargs["target_province_id"] == 2606 else None

        with (
            mock.patch("xar_autoplayer.strategy._fresh_move_route_preview", side_effect=preview),
            mock.patch("xar_autoplayer.strategy._fresh_route_contact_horizon", return_value=saved["route_contact_horizon"]),
        ):
            # Run the actual production model and unchanged admission once.
            plan = call(frame)
            self.actual_plan = plan
            forecast = plan["battle_forecast"]
            self.assertEqual(forecast["status"], "estimated")
            self.assertEqual(forecast["sample_count"], 256)
            self.assertEqual(forecast["horizon_days"], 120)
            self.assertFalse(forecast["native_parity"])
            self.assertEqual(forecast["advantage_input"]["source"], "generic_commander_and_stock_static_approximation")
            self.assertEqual(forecast["advantage_input"]["fallback_reason"], "native_phase_not_in_payload")
            self.assertIn("phase_events_disabled", forecast["assumptions"])
            self.assertIn("future_daily_effective_stat_refresh_unmodeled", forecast["assumptions"])
            self.assertIsNone(forecast["commander_or_knight_death_probability"])
            self.assertEqual(forecast["capture"]["native_revision"], 31)
            self.assertEqual(plan["encounter"]["defender_army_ids"], [134218098])
            if plan["contact_admission"]["admitted"]:
                self.assertEqual(plan["phase"], "native_war_general_battle_short_preview")
                self.assertEqual(plan["selected_step"], "preview-move-army-218104048-to-2618")
            else:
                self.assertEqual(plan["phase"], "native_war_general_battle_model_rejected")
                self.assertIsNone(plan["selected_step"])

            with mock.patch("xar_autoplayer.strategy.forecast_fixed_contact") as model:
                for altered in (
                    {**frame, "combat_simulation_inputs": None},
                    {**frame, "native_revision": 32},
                    {**frame, "revision": 33},
                    {**frame, "combat_simulation_inputs_attacker_entry_province_id": 2619},
                    {**frame, "combat_simulation_inputs_defender_army_ids": [134218099]},
                ):
                    query = call(altered)
                    self.assertEqual(query["phase"], "native_war_general_battle_inputs_query")
                    self.assertEqual(query["selected_step"], expected_query)
                self.assertEqual(call(frame, history=[])["selected_step"], expected_query)
                self.assertIsNone(call(frame, history=[], capabilities=set())["selected_step"])
                preferred = call(frame, capabilities={QUERY_COMBAT_SIMULATION_INPUTS_CAPABILITY, QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY})
                self.assertEqual(preferred["selected_step"], expected_query.replace("-v2-", "-v3-"))
                model.assert_not_called()

            missing = copy.deepcopy(frame)
            missing["combat_simulation_inputs"]["armies"][0]["regiments"][0]["effective_stats"]["damage_raw"] = None
            rejected = call(missing)
            self.assertEqual(rejected["phase"], "native_war_general_battle_model_rejected")
            self.assertEqual(rejected["battle_forecast"]["status"], "model_unavailable")
            self.assertIsNone(rejected["selected_step"])
            partial = copy.deepcopy(frame)
            partial["combat_simulation_inputs"]["completeness"]["input_observation_ready"] = False
            rejected = call(partial)
            self.assertEqual(rejected["battle_forecast"]["status"], "input_or_encounter_mismatch")
            self.assertIsNone(rejected["selected_step"])

        # The fixture's current raw values and false Monte Carlo gate survive.
        self.assertEqual(json.loads(FIXTURE.read_text(encoding="utf-8")), original)
        self.assertFalse(base["completeness"]["monte_carlo_ready"])
        self.assertNotIn("schema_version", base)
        self.assertNotIn("phase_event_inputs", base)
