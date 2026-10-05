from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.player_faction_alerts_contract import (
    PLAYER_FACTION_ALERTS_V1_COUNTY_EXPOSURE_UNAVAILABLE_REASON,
    QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
)
from xar_autoplayer.bridge.version_identity import CK3_12003
from xar_autoplayer.strategy import choose_one_life_turn


def _synthetic_candidate_on_actual_frame(fixture: dict) -> dict:
    """Retain actual root/alert frame; candidate and power are synthetic."""
    frame = fixture["source"]
    actor_power, target_power = 4_000_000_000, 1_000_000_000
    assessment = {
        "target_character_id": 808, "effective_target_character_id": 808,
        "distance_raw": 2_500_000,
        "actor_power_base_raw": actor_power, "actor_network_contribution_raw": 0,
        "actor_power_total_raw": actor_power,
        "target_power_base_raw": target_power, "target_network_contribution_raw": 0,
        "target_pre_adjustment_total_raw": target_power, "target_adjustment_delta_raw": 0,
        "target_power_total_raw": target_power, "actual_power_ratio_raw": 25_000,
        "target_ai_context_actor_entry_raw": 0, "actor_ai_context_target_entry_raw": 0,
        "native_flags_raw": 3,
    }
    return {
        "snapshot_id": frame["snapshot_id"], "revision": frame["revision"],
        "native_revision": frame["native_revision"], "date_raw": frame["date_raw"],
        "paused": True, "played_character": {"character_id": 29829, "alive": True},
        "active_wars": [], "player_armies": [],
        "campaign_root_context": copy.deepcopy(fixture["campaign_root_context"]),
        "declarable_wars": [{
            "declaration_id": "808-17-0", "target_character_id": 808,
            "casus_belli_index": 17, "casus_belli_key": "county_conquest_cb",
            "configuration_index": 0, "claimant_character_id": -1,
            "target_title_ids": [91], "source": "native",
        }],
        "war_entry_assessments": {
            "schema_version": 1, "status": "available",
            "snapshot_revision": frame["native_revision"], "date_raw": frame["date_raw"],
            "actor_character_id": 29829, "requested_target_character_ids": [808],
            "assessments": [assessment],
            "readiness": {key: True for key in (
                "actor_identity_ready", "targets_declarable_ready", "effective_targets_ready",
                "ai_context_ready", "native_output_ready", "network_decomposition_ready",
                "same_frame_ready", "ready",
            )},
            "provenance": {
                "game_version": CK3_12003.game_version,
                "executable_sha256": CK3_12003.executable_sha256,
                "assessment_rva": "0x1A23240", "network_collector_rva": "0x1A24010",
                "power_leaf": "CCharacter+0x1C0->+0x308", "fixed_point_scale": 100_000,
            },
        },
    }


class WarEntryFactionWatchScope12003Test(unittest.TestCase):
    def test_actual_watch_frame_and_changed_danger_unavailable_paths(self) -> None:
        fixture = json.loads((PROJECT_ROOT / "tests/fixtures/faction_watch_current_673_674.json").read_text())
        snapshot = _synthetic_candidate_on_actual_frame(fixture)
        steps = {"declare-war-808-17-0", "life-advance", QUERY_PLAYER_FACTION_ALERTS_V1_STEP}
        checkpoint = {"index": 1, "command": "save-checkpoint", "ok": True}
        alert_result = fixture["faction_query_result"]
        history = [checkpoint, {
            "index": 2, "command": "auto-turn", "ok": True,
            "result": {"auto_turn": {
                "selected_step": QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
                "result": alert_result,
            }},
        }]
        original = copy.deepcopy(fixture)

        watch = choose_one_life_turn(history, snapshot=snapshot, action_steps=steps)
        self.assertEqual(watch["selected_step"], "declare-war-808-17-0")
        self.assertEqual(watch["decision"]["policy"], "general-native-war-entry-battle-prior-v1")
        self.assertEqual(watch["war_entry_faction_context"]["status"], "watch")
        self.assertEqual(watch["war_entry_faction_context"]["snapshot_revision"], 1001)
        self.assertEqual(watch["war_entry_faction_context"]["watch_faction_ids"], [33554465, 50331692])
        self.assertEqual([row["power"]["raw"] for row in watch["war_entry_faction_context"]["factions"]], [3304900, 3879200])
        self.assertEqual([row["power_threshold"]["raw"] for row in watch["war_entry_faction_context"]["factions"]], [7500000, 7500000])
        self.assertFalse(watch["war_entry_faction_context"]["exact_ultimatum_timing_ready"])
        self.assertFalse(watch["prewar_battle_forecast"]["calibrated_probability"])
        self.assertEqual(watch["prewar_battle_forecast"]["sample_count"], 256)

        # Watch permits evaluation; it does not bypass the existing prior budget.
        marginal = copy.deepcopy(snapshot)
        row = marginal["war_entry_assessments"]["assessments"][0]
        row.update({"target_power_base_raw": 2_500_000_000,
                    "target_pre_adjustment_total_raw": 2_500_000_000,
                    "target_power_total_raw": 2_500_000_000, "actual_power_ratio_raw": 62500})
        deferred = choose_one_life_turn(history, snapshot=marginal, action_steps=steps)
        self.assertEqual(deferred["decision"]["outcome"], "NO_DECLARE")
        self.assertEqual(deferred["war_entry_faction_context"]["status"], "watch")
        self.assertFalse(deferred["prewar_forecast_admission"]["admitted"])

        # Synthetic changed native outputs: real nonpeasant danger now grows.
        dangerous = copy.deepcopy(snapshot)
        danger_leaf = copy.deepcopy(alert_result["player_faction_alerts"])
        row = danger_leaf["targeting_factions"][0]
        row.update({"power": {"raw": 8200000, "scale": 100000},
                    "discontent_per_month": {"raw": 300000, "scale": 100000},
                    "months_until_max_discontent": 34,
                    "dangerous_by_stock_rule": True,
                    "danger_reason": "non_peasant_discontent_increasing"})
        danger_leaf["planner_projection"].update({
            "dangerous": True, "dangerous_faction_ids": [33554465],
            "watch_faction_ids": [50331692],
        })
        dangerous["player_faction_alerts"] = danger_leaf
        danger_plan = choose_one_life_turn([checkpoint], snapshot=dangerous, action_steps=steps)
        self.assertEqual(danger_plan["selected_step"], "life-advance")
        self.assertEqual(danger_plan["general_battle_prior_scope_blockers"], ["current_faction_alert_dangerous"])
        self.assertEqual(danger_plan["war_entry_faction_context"]["dangerous_faction_ids"], [33554465])
        self.assertNotIn("prewar_battle_forecast", danger_plan)

        missing = choose_one_life_turn([checkpoint], snapshot=snapshot, action_steps=steps)
        self.assertEqual(missing["selected_step"], QUERY_PLAYER_FACTION_ALERTS_V1_STEP)
        self.assertEqual(missing["war_entry_faction_context"]["status"], "unavailable")
        stale = copy.deepcopy(history)
        old_result = stale[-1]["result"]["auto_turn"]["result"]
        old_result.update({"queried_snapshot_id": "native:845", "queried_revision": 846,
                           "queried_native_revision": 845})
        old_result["player_faction_alerts"].update({"snapshot_revision": 845, "date_raw": 53271912})
        stale_plan = choose_one_life_turn(stale, snapshot=snapshot, action_steps=steps)
        self.assertEqual(stale_plan["selected_step"], QUERY_PLAYER_FACTION_ALERTS_V1_STEP)

        # A current but incomplete result is explicit and is not queried in a loop.
        partial = copy.deepcopy(snapshot)
        partial_leaf = copy.deepcopy(alert_result["player_faction_alerts"])
        partial_leaf["readiness"].update({"county_exposure_ready": False, "alert_ready": False})
        partial_leaf["component_unavailable_reasons"]["county_exposure"] = PLAYER_FACTION_ALERTS_V1_COUNTY_EXPOSURE_UNAVAILABLE_REASON
        partial_leaf["planner_projection"].update({"status": "unavailable", "present": None,
                                                    "dangerous": None, "watch_faction_ids": []})
        partial["player_faction_alerts"] = partial_leaf
        partial_plan = choose_one_life_turn([checkpoint], snapshot=partial, action_steps=steps)
        self.assertEqual(partial_plan["selected_step"], "life-advance")
        self.assertEqual(partial_plan["general_battle_prior_scope_blockers"], ["current_faction_alert_unavailable"])
        self.assertEqual(partial_plan["war_entry_faction_context"]["reason"], "faction_alert_components_unavailable")
        no_query = choose_one_life_turn([checkpoint], snapshot=snapshot, action_steps=steps - {QUERY_PLAYER_FACTION_ALERTS_V1_STEP})
        self.assertEqual(no_query["selected_step"], "life-advance")
        self.assertEqual(no_query["general_battle_prior_scope_blockers"], ["current_faction_alert_unavailable"])
        self.assertEqual(fixture, original)


if __name__ == "__main__":
    unittest.main()
