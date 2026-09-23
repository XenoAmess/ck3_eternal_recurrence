from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.lifestyle_min_policy import choose_min_feudal_lifestyle_action


def _complete_snapshot() -> dict[str, object]:
    return {
        "status": "available",
        "snapshot_id": "native:701",
        "episode_run_id": "native-29829-ee172aa720db",
        "public_revision": 701,
        "native_revision": 9001,
        "proof_epoch": 17,
        "date_raw": 54321000,
        "player_character_id": 32904,
        "current_focus": {
            "presence": "present",
            "key": "stewardship_domain_focus",
            "lifestyle_key": "stewardship_lifestyle",
        },
        "current_lifestyle_progress": {
            "presence": "present",
            "lifestyle_key": "stewardship_lifestyle",
            "unspent_perk_points": 1,
        },
        "owned_perk_keys": ["tax_man_perk"],
        "legal_focus_candidates": {"status": "available", "items": []},
        "legal_perk_candidates": {
            "status": "available",
            "items": [{
                "key": "cutting_corners_perk",
                "lifestyle_key": "stewardship_lifestyle",
            }],
        },
        "readiness": {
            "current_focus_ready": True,
            "lifestyle_progress_ready": True,
            "owned_perks_ready": True,
            "legal_focus_candidates_ready": True,
            "legal_perk_candidates_ready": True,
            "same_frame_ready": True,
        },
    }


def _choose(snapshot: dict[str, object], **kwargs: object) -> dict[str, object]:
    return choose_min_feudal_lifestyle_action(
        snapshot,
        feudal_scope_admitted=True,
        at_peace=True,
        **kwargs,
    )


class LifestyleMinPolicyTests(unittest.TestCase):
    def test_wartime_opt_in_spends_existing_tree_point_but_never_starts_focus(self) -> None:
        snapshot = _complete_snapshot()
        result = choose_min_feudal_lifestyle_action(
            snapshot, feudal_scope_admitted=True, at_peace=False,
            allow_wartime_perk=True,
        )
        self.assertEqual(result["status"], "recommend_action")
        self.assertEqual(
            result["policy_id"], "g2-lifestyle-wartime-stewardship-perk-v1"
        )
        self.assertEqual(result["selected_action"]["kind"], "perk")
        self.assertEqual(result["selected_action"]["target_key"], "cutting_corners_perk")
        self.assertEqual(
            choose_min_feudal_lifestyle_action(
                snapshot, feudal_scope_admitted=True, at_peace=False,
            )["status"], "outside_admitted_scene",
        )
        snapshot["current_focus"] = {"presence": "absent"}
        snapshot["current_lifestyle_progress"] = {"presence": "absent"}
        snapshot["legal_focus_candidates"] = {"status": "available", "items": [{
            "key": "stewardship_wealth_focus",
            "lifestyle_key": "stewardship_lifestyle",
        }]}
        snapshot["target_lifestyle_progress"] = {
            "presence": "present", "lifestyle_key": "stewardship_lifestyle",
            "unspent_perk_points": 0,
        }
        absent = choose_min_feudal_lifestyle_action(
            snapshot, feudal_scope_admitted=True, at_peace=False,
            allow_wartime_perk=True,
        )
        self.assertEqual(absent["status"], "outside_admitted_scene")
        self.assertIsNone(absent["selected_action"])

    def test_feudal_building_perk_generates_one_bound_target(self) -> None:
        result = _choose(_complete_snapshot())
        self.assertEqual(result["status"], "recommend_action")
        action = result["selected_action"]
        self.assertEqual(action["kind"], "perk")
        self.assertEqual(action["target_key"], "cutting_corners_perk")
        self.assertEqual(action["expected"]["expected_player_character_id"], 32904)
        self.assertEqual(
            action["expected"]["expected_episode_run_id"],
            "native-29829-ee172aa720db",
        )

    def test_present_focus_needs_only_windowless_perk_collection(self) -> None:
        snapshot = _complete_snapshot()
        snapshot["legal_focus_candidates"] = {
            "status": "unavailable",
            "reason": "lifestyle_window_unavailable",
            "items": [],
        }
        snapshot["legal_perk_candidates"]["scope"] = "policy_target"
        snapshot["readiness"]["legal_focus_candidates_ready"] = False
        result = _choose(snapshot)
        self.assertEqual(result["status"], "recommend_action")
        self.assertEqual(
            result["selected_action"]["target_key"], "cutting_corners_perk"
        )

    def test_absent_focus_requires_exact_target_progress_source(self) -> None:
        snapshot = _complete_snapshot()
        snapshot["current_focus"] = {"presence": "absent"}
        snapshot["current_lifestyle_progress"] = {"presence": "absent"}
        snapshot["legal_focus_candidates"] = {
            "status": "available",
            "items": [{
                "key": "stewardship_wealth_focus",
                "lifestyle_key": "stewardship_lifestyle",
            }],
        }
        result = _choose(snapshot)
        self.assertEqual(result["status"], "target_progress_source_unavailable")
        self.assertIsNone(result["selected_action"])
        snapshot["target_lifestyle_progress"] = {
            "presence": "present",
            "lifestyle_key": "stewardship_lifestyle",
            "unspent_perk_points": 0,
        }
        result = _choose(snapshot)
        self.assertEqual(result["selected_action"]["kind"], "focus")
        self.assertEqual(result["selected_action"]["target_key"], "stewardship_wealth_focus")

    def test_unknown_candidates_cannot_become_legal_zero_or_noop(self) -> None:
        snapshot = _complete_snapshot()
        snapshot["legal_perk_candidates"] = {
            "status": "unavailable",
            "reason": "lifestyle_window_unavailable",
            "items": [],
        }
        result = _choose(snapshot)
        self.assertEqual(result["status"], "legal_candidates_unavailable")
        self.assertIsNone(result["selected_action"])

    def test_pending_and_unknown_receipt_never_resubmit(self) -> None:
        snapshot = _complete_snapshot()
        for status, expected in (
            ("submitted_verification_pending", "verify_pending_receipt"),
            ("postcondition_failed", "action_state_unknown"),
            ("unexpected_status", "action_state_unknown"),
        ):
            with self.subTest(status=status):
                result = _choose(snapshot, pending_action={"status": status})
                self.assertEqual(result["status"], expected)
                self.assertIsNone(result["selected_action"])

    def test_applied_perk_is_not_selected_again_on_next_turn(self) -> None:
        snapshot = _complete_snapshot()
        snapshot["owned_perk_keys"].append("cutting_corners_perk")
        result = _choose(snapshot, pending_action={"status": "applied"})
        self.assertEqual(result["status"], "consume_applied_receipt")
        self.assertIsNone(result["selected_action"])
        result = _choose(snapshot)
        self.assertEqual(result["status"], "no_legal_minimum")

    def test_missing_scope_and_identity_do_not_schedule_action(self) -> None:
        snapshot = _complete_snapshot()
        result = choose_min_feudal_lifestyle_action(
            snapshot, feudal_scope_admitted=False, at_peace=True
        )
        self.assertEqual(result["status"], "outside_admitted_scene")
        unknown = choose_min_feudal_lifestyle_action(
            snapshot, feudal_scope_admitted=True, at_peace=None
        )
        self.assertEqual(unknown["status"], "scope_observation_unavailable")
        bad = copy.deepcopy(snapshot)
        bad["player_character_id"] = None
        self.assertEqual(_choose(bad)["status"], "observation_unavailable")
        bad = copy.deepcopy(snapshot)
        bad["episode_run_id"] = None
        self.assertEqual(_choose(bad)["status"], "observation_unavailable")


if __name__ == "__main__":
    unittest.main()
