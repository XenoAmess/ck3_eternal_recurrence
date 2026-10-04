from __future__ import annotations

import copy
import unittest

from test_battle_current_condition import DATE, SUBJECT, _normalized_frame, _raw_frame
from xar_autoplayer.bridge.active_combat_retreat_contract import (
    ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE,
    normalize_active_combat_retreat_v1_preview,
    order_active_combat_retreat_v1_step,
    preview_active_combat_retreat_v1_step,
)
from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_runner import run_frozen_main_tick
from xar_autoplayer.simulation.battle_current_retreat_policy import assess_current_battle_retreat
from xar_autoplayer.simulation.combat_core import DrawState


def _preview(frame: dict) -> dict:
    target, revision, token = 2579, 7, "fixture_current_retreat_token_0001"
    raw = {
        "schema_version": 1, "contract_stage": ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE,
        "step": preview_active_combat_retreat_v1_step(SUBJECT, target),
        "status": "available", "unavailable_reason": None, "action_ready": True,
        "source_binding": {
            "snapshot_id": "fixture-current-retreat", "revision": revision,
            "native_revision": frame["snapshot_revision"], "date_raw": DATE,
            "episode_run_id": "fixture-current-retreat", "connection_generation": 1,
        },
        "battle_control_snapshot": copy.deepcopy(frame), "target_province_id": target,
        "target_preview": {
            "status": "available", "unavailable_reason": None,
            "provenance": "planner_selected_exact_native_route_preview",
            "army_id": SUBJECT, "origin_province_id": frame["province_id"],
            "target_province_id": target, "route_province_ids": [target],
            "previewed_date_raw": DATE, "move_mode": 1,
            "eta_date_raw": DATE + 24, "movement_days": 1, "candidate_token": token,
            "order_step": order_active_combat_retreat_v1_step(
                SUBJECT, expected_snapshot_revision=revision,
                expected_combat_id=frame["combat_id"], expected_side_index=0,
                expected_scope="full_side", target_province_id=target,
                candidate_token=token,
            ),
        },
        "backend_id": "fixture",
    }
    for key in (
        "selected_public_cunit_id", "selected_native_carmy_id", "selected_owner_character_id",
        "combat_id", "combat_province_id", "side_index", "side_scope",
        "affected_public_cunit_ids_in_stored_order",
        "unaffected_same_side_public_cunit_ids_in_stored_order",
    ):
        raw[key] = copy.deepcopy(frame[key])
    return normalize_active_combat_retreat_v1_preview(
        raw, expected_selected_public_cunit_id=SUBJECT,
        expected_target_province_id=target, expected_snapshot_revision=revision,
    )


class BattleCurrentRetreatPolicyTests(unittest.TestCase):
    def test_observed_owner_loss_budget_and_native_route_proposal(self):
        frame = _normalized_frame(1)
        tick = run_frozen_main_tick(adapt_current_battle_condition(frame), draw_state=DrawState(0, 0))
        # Existing production arithmetic: own 1.25 hard soldiers, caller budget 1.
        self.assertEqual(tick["sides"][0]["losses"]["new_hard_casualties_raw"], 125_000)
        decision = assess_current_battle_retreat(
            frame, frozen_main_tick=tick, maximum_next_tick_hard_loss_raw=100_000,
            retreat_preview=_preview(frame),
        )
        self.assertEqual(decision["recommendation"], "order_active_combat_retreat")
        self.assertEqual(decision["selected_owner_next_tick_hard_loss_raw"], 125_000)
        self.assertTrue(decision["budget_exceeded"])
        self.assertEqual(decision["retreat_order_arguments"], {
            "selected_public_cunit_id": SUBJECT, "expected_revision": 7,
            "expected_combat_id": frame["combat_id"], "expected_side_index": 0,
            "expected_scope": "full_side", "target_province_id": 2579,
            "candidate_token": "fixture_current_retreat_token_0001",
        })
        self.assertIsNone(decision["win_probability"])
        self.assertIsNone(decision["retreat_loss_raw"])
        self.assertFalse(decision["complete_transition"])
        boundary = assess_current_battle_retreat(
            frame, frozen_main_tick=tick, maximum_next_tick_hard_loss_raw=125_000,
        )
        self.assertEqual(boundary["recommendation"], "continue_one_observed_day")
        self.assertFalse(boundary["budget_exceeded"])
        self.assertEqual(boundary["observation_days"], 1)

    def test_missing_current_loss_requests_real_inputs_without_count_proxy(self):
        raw = _raw_frame(1)
        raw.pop("current_loss_inputs_v1")
        frame = normalize_battle_control_snapshot_v1(
            raw, expected_subject_public_cunit_id=SUBJECT,
            expected_observed_date_raw=DATE, expected_snapshot_revision=5,
        )
        tick = run_frozen_main_tick(adapt_current_battle_condition(frame), draw_state=DrawState(0, 0))
        self.assertEqual(tick["status"], "partial")
        self.assertTrue(frame["legality"]["legal_now"])
        self.assertGreater(frame["attacker"]["derived_current_fighting_raw"], 0)
        decision = assess_current_battle_retreat(
            frame, frozen_main_tick=tick, maximum_next_tick_hard_loss_raw=100_000,
        )
        self.assertEqual(decision["recommendation"], "query_current_battle_inputs")
        self.assertIn("current_loss_inputs_v1", decision["required_inputs"])
        self.assertEqual(decision["proposed_tool"], "ck3_query_battle_control_snapshot_v1")
        self.assertIsNone(decision["selected_owner_next_tick_hard_loss_raw"])
        self.assertIsNone(decision["retreat_order_arguments"])
        self.assertIsNone(decision["budget_exceeded"])


if __name__ == "__main__":
    unittest.main()
