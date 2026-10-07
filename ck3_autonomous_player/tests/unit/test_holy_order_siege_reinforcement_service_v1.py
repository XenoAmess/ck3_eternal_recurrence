"""One NEW Service compound; native world/callback outcomes are synthetic."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.hire_holy_order import normalize_hire_holy_order_v1
from xar_autoplayer.bridge.player_holy_order_context_private_transport import normalize_player_holy_order_context_v1
from xar_autoplayer.bridge.war_contract import HIRE_HOLY_ORDER_V1_CAPABILITY, HIRE_HOLY_ORDER_V1_STEP


class _SyntheticCurrentWorld:
    def __init__(self, *, can_hire=True):
        self.can_hire, self.submitted = can_hire, False
        self.calls = []
        self.before = {
            "snapshot_id": "synthetic:10", "revision": 10, "native_revision": 9,
            "date_raw": 53288448, "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True},
            "active_wars": [{"war_id": 44}], "player_armies": [],
            "played_character_gold": {"raw": 1000000, "scale": 100000},
            "played_character_prestige": {"raw": 300000, "scale": 100000},
            "played_character_piety": {"raw": 1000000, "scale": 100000},
            "diagnostics": {"hello": {"game_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256}},
        }
        self.after = {**deepcopy(self.before), "snapshot_id": "synthetic:11", "revision": 11,
            "native_revision": 10, "played_character_piety": {"raw": 800000, "scale": 100000},
            "player_armies": [{"army_id": 218104222, "owner_character_id": 4444,
                "controllable": True, "current_province_id": 460, "soldiers": 500}]}

    def capabilities(self):
        return {"backend_id": "native-headless", "action_steps": [HIRE_HOLY_ORDER_V1_STEP],
                "bridge_capabilities": [HIRE_HOLY_ORDER_V1_CAPABILITY]}

    def take_snapshot(self):
        return deepcopy(self.after if self.submitted else self.before)

    def query_player_holy_order_context_private_v1(self, *, expected_revision):
        snapshot = self.take_snapshot()
        self.calls.append(("holy_query", expected_revision))
        if expected_revision != snapshot["revision"]:
            raise AssertionError("consumer must use the current public revision")
        association = {"available": True, "unavailable_reason": None, "applies_to_player": self.submitted,
                       "rows": []}
        if self.submitted:
            # Two genuine source occurrences point to the same generation-zero
            # CArmy. A public army's literal owner need not equal its employer.
            association["rows"] = [{"regiment_id": ident, "available": True,
                "unavailable_reason": None, "regiment_resolved": True,
                "native_carmy_id": 0, "native_carmy_resolved": True,
                "combat_id": None, "combat_resolved": False} for ident in (8, 9)]
        raw = {"schema": "ck3_12004_player_holy_order_context_v1", "read_only": True,
            "game_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
            "available": True, "unavailable_reason": None, "capture_epoch": 100 + snapshot["revision"],
            "date_raw": snapshot["date_raw"], "played_character_id": 29829, "raw_scale": 100000,
            "queried_snapshot_id": snapshot["snapshot_id"], "queried_revision": snapshot["revision"],
            "queried_native_revision": snapshot["native_revision"], "snapshot_revision": snapshot["native_revision"],
            "rows": [{"holy_order_id": 0, "rite_id": 152, "is_military": True,
                "founder_id": 4444, "patron_id": 4444, "employer_id": 29829 if self.submitted else None,
                "leased_title_ids": [], "military_terms": {
                    "available": True, "unavailable_reason": None, "resource_scale": 100000,
                    "can_hire": self.can_hire and not self.submitted, "can_afford": True,
                    "can_hire_reasons_available": True,
                    "can_hire_reason_literal": "already hired" if self.submitted else "" if self.can_hire else "no qualifying war",
                    "can_afford_reasons_available": True, "can_afford_reason_literal": "",
                    "resource_costs_raw": [0, 0, 200000, 0, 0, 0, 0, 0, 0, 0],
                    "troop_strength": {"available": True, "unavailable_reason": None, "current_soldiers": 450},
                    "troop_association": association}}]}
        # Exercise the production strict domain normalizer rather than hand
        # building a planner observation in command history.
        return normalize_player_holy_order_context_v1(raw, snapshot=snapshot)

    def hire_holy_order_v1(self, *, holy_order_id, expected_revision):
        self.calls.append(("hire", holy_order_id, expected_revision))
        if holy_order_id != 0 or expected_revision != 10:
            raise AssertionError("typed normal action must retain full ID0 and public revision")
        context = self.query_player_holy_order_context_private_v1(expected_revision=expected_revision)
        raw = {"step": HIRE_HOLY_ORDER_V1_STEP, "game_version": CK3_12004.game_version,
            "executable_sha256": CK3_12004.executable_sha256, "read_only": False,
            "command_sequence": 1, "snapshot_revision": 9, "date_raw": self.before["date_raw"],
            "accepted": True, "status": "submitted_verification_pending", "holy_order_hire": {
                "schema": "ck3_12004_holy_order_hire_action_v1", "status": "submitted",
                "snapshot_revision": 9, "date_raw": self.before["date_raw"], "holy_order_id": 0,
                "actor_character_id": 29829, "native_hire_mode": 3, "holy_order_resolved": True,
                "native_command_validation_observable": True, "native_command_valid": True,
                "command_submitted": True, "verification_pending": True, "after_state_observed": False,
                "prior_employer_character_id": None, "unavailable_reason": None, "prior_context": context}}
        ack = normalize_hire_holy_order_v1(raw, snapshot=self.before, expected_holy_order_id=0)
        self.submitted = True
        return ack

    def query_army_strengths(self, *, army_ids, expected_revision):
        self.calls.append(("armies", list(army_ids), expected_revision))
        return {"army_strengths": [{"status": "available", "army_id": 218104222,
            "native_carmy_id": 0, "current_soldiers": 500}]}

    def query_war_cash_current_resources_private_v1(self, *, expected_revision):
        self.calls.append(("cash", expected_revision))
        return {"military_expenses": {"current": {"status": "available", "gold_raw": 0},
                                      "all_raised": {"status": "available", "gold_raw": 100000}},
                "player_monthly_net_income": {"raw": 250000, "scale": 100000}}


class HolyOrderSiegeReinforcementServiceV1Tests(unittest.TestCase):
    def test_new_service_siege_choice_normal_hire_independent_post_and_next_formal(self):
        base = {"policy": "one-life-turn-v1", "phase": "native_war_siege_exit_blocked",
            "selected_step": None, "siege_state": {"status": "insufficient_strength",
                "province_id": 2592, "player_army_besieging": True, "garrison_size": 1000,
                "besieging_strength": 600}, "pursuit": {"war_id": 44}}
        # The old counter's exact decision is an input, not reimplemented or
        # replayed. This single compound tests only the new two Service hooks.
        with patch('xar_autoplayer.bridge.service.choose_one_life_turn', return_value=deepcopy(base)), \
             patch.object(GameplayBridgeService, '_strategy_state_dir', return_value=None), \
             patch.object(GameplayBridgeService, '_prepare_succession_transition_v1', side_effect=lambda snapshot, steps: snapshot):
            denied = _SyntheticCurrentWorld(can_hire=False)
            denied_plan = GameplayBridgeService(denied).plan_turn()
            self.assertIsNone(denied_plan["plan"]["selected_step"])
            self.assertFalse(any(call[0] == "hire" for call in denied.calls))
            allowed = _SyntheticCurrentWorld()
            service = GameplayBridgeService(allowed)
            planned = service.plan_turn()
            self.assertEqual(planned["plan"]["selected_step"], HIRE_HOLY_ORDER_V1_STEP)
            self.assertEqual(planned["plan"]["holy_order_hire_proposal"]["holy_order_id"], 0)
            outcome = service._execute_planned_turn(planned)
            result = outcome["result"]
            self.assertFalse(result["holy_order_hire"]["after_state_observed"])
            receipt = result["holy_order_reinforcement_postcondition"]
            self.assertTrue(receipt["employer_observed"])
            self.assertTrue(receipt["usable_army_observed"])
            self.assertEqual(len(receipt["troop_association"]["rows"]), 2)
            self.assertEqual(len(receipt["material_armies"]), 1)
            self.assertEqual(receipt["material_armies"][0]["owner_character_id"], 4444)
            self.assertEqual(receipt["observed_stock_delta_raw"]["piety"], 200000)
            self.assertTrue(receipt["unchanged_date_quote_delta_match"])
            self.assertEqual(receipt["actor_expenses"]["military_expenses"]["current"]["gold_raw"], 0)
            self.assertEqual(receipt["next_formal"]["selected_step"], "preview-move-army-218104222-to-2592")
            self.assertFalse(receipt["full_hire_loop_complete"])
            self.assertEqual(sum(call[0] == "hire" for call in allowed.calls), 1)
            # Once employed, the real post query's CanHire=false remains valid;
            # the next ordinary planning turn does not submit another hire.
            second = service.plan_turn()
            self.assertIsNone(second["plan"]["selected_step"])
            self.assertEqual(sum(call[0] == "hire" for call in allowed.calls), 1)
            output = os.environ.get("XAR_HO_SIEGE_CASE_OUTPUT")
            if output:
                Path(output).write_text(json.dumps({
                    "synthetic_world_and_callback_outcomes": True,
                    "production_service_hooks_and_domain_normalizers": True,
                    "denied_plan": denied_plan, "selected_plan": planned,
                    "outcome": outcome, "next_turn_plan": second,
                    "ordinary_driver_calls": allowed.calls,
                }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == '__main__':
    unittest.main()
