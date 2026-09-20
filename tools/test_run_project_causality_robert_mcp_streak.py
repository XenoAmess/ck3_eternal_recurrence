#!/usr/bin/env python3
"""Offline tests for the MCP-only Robert streak target policy."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


RUNNER = Path(__file__).with_name(
    "run_project_causality_robert_mcp_streak.py"
)
SPEC = importlib.util.spec_from_file_location("robert_streak_runner", RUNNER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import Robert streak runner")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def declaration(
    target: int,
    declaration_id: str,
    *,
    cb: str = "claim_cb",
) -> dict[str, object]:
    return {
        "declaration_id": declaration_id,
        "target_character_id": target,
        "casus_belli_key": cb,
        "target_title_ids": [target + 1000],
    }


def assessment(
    target: int,
    *,
    actor: int,
    target_base: int,
    target_pre: int,
    target_total: int,
    distance: int = 1,
) -> dict[str, object]:
    return {
        "target_character_id": target,
        "effective_target_character_id": target,
        "actor_power_base_raw": actor,
        "target_power_base_raw": target_base,
        "target_network_contribution_raw": target_pre - target_base,
        "target_pre_adjustment_total_raw": target_pre,
        "target_power_total_raw": target_total,
        "distance_raw": distance,
    }


class RobertStreakTargetPolicyTests(unittest.TestCase):
    def test_negative_native_adjustment_cannot_turn_stronger_target_into_zero(self) -> None:
        declarations = [
            declaration(10, "10-1--1"),
            declaration(20, "20-1--1"),
        ]
        assessments = {
            10: assessment(
                10,
                actor=6_000,
                target_base=10_000,
                target_pre=10_000,
                target_total=0,
            ),
            20: assessment(
                20,
                actor=6_000,
                target_base=3_000,
                target_pre=3_000,
                target_total=3_000,
            ),
        }
        chosen, ranked = runner._rank_declaration_candidates(
            declarations, assessments
        )
        self.assertEqual(20, chosen["target_character_id"])
        self.assertEqual(10_000, ranked[1]["conservative_target_power_raw"])
        self.assertTrue(chosen["safe_overmatch"])

    def test_no_overmatch_chooses_lowest_current_native_risk(self) -> None:
        declarations = [
            declaration(10, "10-2--1", cb="minor_religious_war"),
            declaration(20, "20-3--1"),
        ]
        assessments = {
            10: assessment(
                10,
                actor=6_000,
                target_base=8_000,
                target_pre=8_000,
                target_total=8_000,
            ),
            20: assessment(
                20,
                actor=6_000,
                target_base=7_000,
                target_pre=7_000,
                target_total=7_000,
            ),
        }
        chosen, _ = runner._rank_declaration_candidates(
            declarations, assessments
        )
        self.assertEqual(20, chosen["target_character_id"])
        self.assertEqual("least_risk_until_failure", chosen["risk_class"])

    def test_equal_risk_prefers_claim_before_religious_war(self) -> None:
        declarations = [
            declaration(10, "10-2--1", cb="minor_religious_war"),
            declaration(10, "10-3--1", cb="claim_cb"),
        ]
        assessments = {
            10: assessment(
                10,
                actor=9_000,
                target_base=4_000,
                target_pre=4_000,
                target_total=4_000,
            )
        }
        chosen, _ = runner._rank_declaration_candidates(
            declarations, assessments
        )
        self.assertEqual("10-3--1", chosen["declaration_id"])

    def test_declaration_requires_quiet_paused_map(self) -> None:
        ready = {
            "map_ready": True,
            "paused": True,
            "active_event": None,
            "pending_character_interaction": None,
        }
        self.assertTrue(runner._snapshot_ready_for_declaration(ready))
        self.assertFalse(
            runner._snapshot_ready_for_declaration(
                {**ready, "active_event": {"event_id": "health.3001"}}
            )
        )
        self.assertFalse(
            runner._snapshot_ready_for_declaration(
                {**ready, "pending_character_interaction": {"type": "hook"}}
            )
        )

    def test_only_exact_route_timeline_failure_is_recoverable(self) -> None:
        recoverable = {
            "is_error": True,
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Error executing tool ck3_auto_turn: native gameplay "
                        "step failed: CK3 route arrival timeline is "
                        "unavailable (role=hostile, army_id=70, "
                        "path=hostile_active, stage=route_duration_read)"
                    ),
                }
            ],
        }
        self.assertTrue(
            runner._is_route_contact_timeline_unavailable(recoverable)
        )
        self.assertFalse(
            runner._is_route_contact_timeline_unavailable(
                {
                    "is_error": True,
                    "content": [
                        {
                            "type": "text",
                            "text": "native gameplay movement mutation failed",
                        }
                    ],
                }
            )
        )
        self.assertFalse(
            runner._is_route_contact_timeline_unavailable(
                {
                    **recoverable,
                    "is_error": False,
                }
            )
        )

    def test_vanished_war_requires_absolute_player_score_endpoint(self) -> None:
        self.assertEqual(
            runner._terminal_vanished_war_outcome(
                {"player_relative_war_score": -100, "player_side": "defender"}
            ),
            "player_defeat",
        )
        self.assertEqual(
            runner._terminal_vanished_war_outcome(
                {"player_relative_war_score": 100, "player_side": "defender"}
            ),
            "player_victory",
        )
        self.assertIsNone(
            runner._terminal_vanished_war_outcome(
                {"player_relative_war_score": -99}
            )
        )
        self.assertIsNone(
            runner._terminal_vanished_war_outcome(
                {"player_relative_war_score": True}
            )
        )


if __name__ == "__main__":
    unittest.main()
