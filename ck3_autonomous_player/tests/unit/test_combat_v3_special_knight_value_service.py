"""One new real V3 service-return route, with unchanged forecast readiness."""
from copy import deepcopy
import unittest

from test_combat_phase_inputs_v3_bridge import _fixture_result, _McpV3Driver
from xar_autoplayer.bridge.service import GameplayBridgeService

OBSERVATIONS = {}
EXACT_SHA = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"


def current_knight_service_source():
    backend = _fixture_result()
    for army in backend["combat_simulation_inputs"]["base_inputs"]["armies"]:
        leaf = army["knights"]
        leaf.update(loaded_damage_multiplier=50, loaded_toughness_multiplier=10)
        for member in leaf["members"]:
            member["effectiveness_context"] = {
                "schema": "ck3_12003_knight_effectiveness_context_v1",
                "status": "available", "character_id": 29829,
                "modifier_indices": list(range(0xC1, 0xCA)),
                "modifier_raw": [member["knight_effectiveness_raw"]-100000] + [0]*8,
                "operand_raw": [100000, 0, 0, 1100000, 1200000,
                                1300000, 1400000, 1500000, 1600000],
                "scale": 100000, "unavailable_reason": None,
            }
    return backend


class ExactCurrentKnightDriver(_McpV3Driver):
    def take_snapshot(self):
        snapshot = super().take_snapshot()
        snapshot["diagnostics"]["hello"].update(
            game_version="1.20.0.3", executable_sha256=EXACT_SHA)
        return snapshot


class CombatV3SpecialKnightServiceTests(unittest.TestCase):
    def test_real_service_attaches_raw_value_and_keeps_original_forecast_flags(self):
        backend = current_knight_service_source()
        original = deepcopy(backend)
        driver = ExactCurrentKnightDriver(backend)
        result = GameplayBridgeService(driver).query_combat_simulation_inputs_v3(
            2596, 2597, [357, 33554657], [83886341], expected_revision=4)
        self.assertEqual(driver.execute_count, 1)
        self.assertNotIn("current_special_knight_initial_value", backend)
        value = result["current_special_knight_initial_value"]
        self.assertGreater(value["observed_member_count"], 0)
        self.assertTrue(value["all_observed_member_inputs_ready"])
        self.assertEqual(value["ready_member_count"], value["observed_member_count"])
        self.assertEqual(value["target_province_id"], 2596)
        member = value["members_in_query_order"][0]
        normalized_member = result["combat_simulation_inputs"]["base_inputs"]["armies"][member["army_index"]]["knights"]["members"][member["member_index"]]
        self.assertEqual(member["selected_character_full_id"], 29829)
        self.assertEqual(member["current_observation"]["effective_damage_raw"],
                         normalized_member["effective_damage_raw"])
        self.assertEqual(member["calculation_ledger"]["selected_source"]["observation"],
                         normalized_member["effectiveness_context"])
        self.assertEqual(member["read_stage"], "frozen_current_character_values")
        provenance = value["source_provenance"]
        self.assertEqual(provenance["source_method"], "query_combat_simulation_inputs_v3")
        self.assertEqual(provenance["query_sequence"], result["query_sequence"])
        for field in ("snapshot_id", "revision", "native_revision", "date_raw",
                      "paused", "backend_id", "game_version", "executable_sha256"):
            self.assertEqual(provenance[field], result["source"][field])
        self.assertEqual((provenance["revision"], provenance["native_revision"]), (4, 5))
        self.assertEqual(provenance["executable_sha256"], EXACT_SHA)

        completeness = result["combat_simulation_inputs"]["completeness"]
        for field in ("base_input_observation_ready", "phase_raw_observation_ready",
                      "offline_exact_state_refs_ready", "phase_event_inputs_ready",
                      "input_observation_ready", "monte_carlo_ready", "transition_fidelity_gate",
                      "planner_usable", "active_attack_allowed", "missing_observation_domains",
                      "missing_required_domains"):
            self.assertEqual(result[field], completeness[field])
        self.assertEqual(result["status"], backend["status"])
        for field in ("monte_carlo_ready", "transition_fidelity_gate",
                      "planner_usable", "active_attack_allowed"):
            self.assertFalse(result[field])
        self.assertFalse(value["full_entry_ready"])
        self.assertFalse(value["native_write_performed"])
        self.assertEqual(backend, original)
        OBSERVATIONS.update(source=deepcopy(result["source"]),
                            value=value, returned_status=result["status"],
                            original_completeness=deepcopy(completeness),
                            execute_count=driver.execute_count)


if __name__ == "__main__":
    unittest.main()
