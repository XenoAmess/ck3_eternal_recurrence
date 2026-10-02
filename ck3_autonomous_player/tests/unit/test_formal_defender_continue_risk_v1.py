"""Current route and siege clocks cannot become a war-exit probability."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))

from xar_autoplayer.formal_defender_continue_risk_v1 import (  # noqa: E402
    observe_defender_continue_risk_v1,
)

EVIDENCE = ROOT / "docs" / "autonomous-agent-progress" / "coordination" / "war-requests" / "evidence"
R0271 = EVIDENCE / "WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.r0271-blocker-excerpt.json"
H2743 = EVIDENCE / "WAR-ROBERT-H2743-EXIT-20260928.local-h2743-options.json"


def _r0271_inputs() -> tuple[dict[str, object], dict[str, object]]:
    excerpt = json.loads(R0271.read_text(encoding="utf-8"))
    plan = excerpt["first_blocker"]["plan"]
    frame = plan["formal_defender_exit_observation"]["frame"]
    route = plan["route_contact_horizon"]
    subject = route["subject_route"]
    offsite = route["hostile_routes"][1]
    contact = {
        "source_frame": frame,
        "source_sha256": excerpt["source_formal_report_sha256"],
        "subject_army_id": subject["army_id"],
        "target_province_id": route["target_province_id"],
        "horizon_start_date_raw": route["horizon_start_date_raw"],
        "horizon_end_date_raw": route["horizon_end_date_raw"],
        "one_day_contact_free": route["one_day_contact_free"],
        "conflicts": route["conflicts"],
        "first_waypoint_arrival_date_raw": subject["arrival_date_raws"][0],
        "subject_target_arrival_date_raw": subject["arrival_date_raws"][-1],
        "offsite_target_arrivals": [{
            "army_id": offsite["army_id"],
            "arrival_date_raw": offsite["arrival_date_raws"][-1],
        }],
    }
    return frame, contact


class FormalDefenderContinueRiskTests(unittest.TestCase):
    def test_r0271_one_day_bound_does_not_authorize_seven_day_waypoint(self) -> None:
        frame, contact = _r0271_inputs()
        result = observe_defender_continue_risk_v1(frame=frame, contact=contact)
        self.assertEqual(result["current_score"]["player_relative_war_score"], -21)
        self.assertEqual(result["contact"]["contact_free_through_raw"], 53219184)
        self.assertTrue(result["contact"]["first_waypoint_outside_proven_window"])
        self.assertEqual(
            result["contact"]["offsite_target_arrival_order"],
            "listed_offsite_hostile_may_precede_target_entry",
        )
        self.assertIn("offsite_hostile_may_join_by_target_entry", result["blockers"])
        self.assertIsNone(result["continuation_loss_upper_raw"])
        self.assertIsNone(result["continuation_win_probability"])
        self.assertFalse(result["material_comparison_ready"])
        self.assertIsNone(result["action_literal"])

    def test_h2743_one_day_siege_is_timer_estimate_without_loss_bound(self) -> None:
        excerpt = json.loads(H2743.read_text(encoding="utf-8"))
        observed = excerpt["frame"]
        frame = {
            "snapshot_id": observed["snapshot_id_before_and_after"],
            "revision": observed["queried_public_revision"],
            "native_revision": observed["queried_native_revision"],
            "date_raw": observed["date_raw"],
            "episode_run_id": observed["episode_run_id"],
            "connection_generation": observed["queried_connection_generation"],
            "played_character_id": observed["actor_character_id"],
            "war_id": observed["war_id"],
            "player_relative_war_score": observed["player_relative_war_score"],
        }
        siege = {
            "source_frame": frame,
            "source_sha256": excerpt["source"]["read_only_result_sha256"],
            "province_id": 2628,
            "besieging_army_ids": [50331920],
            "remaining_days_estimate": 1,
        }
        result = observe_defender_continue_risk_v1(frame=frame, siege=siege)
        self.assertEqual(result["siege"]["completion_estimate_raw"], 53217288)
        self.assertFalse(result["siege"]["completion_upper_bound_proven"])
        self.assertEqual(result["contact"]["status"], "typed_unavailable")
        self.assertIsNone(result["continuation_loss_upper_raw"])
        self.assertIsNone(result["recommended_outcome"])

    def test_cross_frame_contact_rejected_even_with_same_war_and_date(self) -> None:
        frame, contact = _r0271_inputs()
        crossed = copy.deepcopy(contact)
        crossed["source_frame"]["native_revision"] -= 1
        with self.assertRaisesRegex(ValueError, "contact crossed native frame"):
            observe_defender_continue_risk_v1(frame=frame, contact=crossed)

    def test_siege_clock_for_another_province_cannot_join_route_envelope(self) -> None:
        frame, contact = _r0271_inputs()
        siege = {
            "source_frame": frame,
            "source_sha256": contact["source_sha256"],
            "province_id": 2628,
            "besieging_army_ids": [50331920],
            "remaining_days_estimate": 1,
        }
        with self.assertRaisesRegex(ValueError, "crossed provinces"):
            observe_defender_continue_risk_v1(
                frame=frame, contact=contact, siege=siege,
            )


if __name__ == "__main__":
    unittest.main()
