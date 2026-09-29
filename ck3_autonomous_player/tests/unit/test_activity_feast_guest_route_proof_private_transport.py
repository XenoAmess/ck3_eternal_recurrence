"""Exact native payload bounds for the private Stage-5 guest proof."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.activity_feast_guest_route_proof_private_transport import (  # noqa: E402
    parse_activity_feast_guest_route_proof_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError  # noqa: E402


class GuestRouteProofTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = {
            "schema": "activity-feast-stage5-guest-route-proof-private-v1",
            "snapshot_revision": 19, "date_raw": 53219928,
            "actor_character_id": 29829,
            "activity_key": "activity_feast", "planning_stage": 5,
            "status": "observed", "candidate_status": "observed",
            "selected_status": "observed", "start_gate_status": "observed",
            "normal_refresh_sequence": 12,
            "source_fingerprint": "0x0123456789abcdef",
            "active_rule_count": 1, "filtered_group_count": 1,
            "selected_row_count": 1, "selected_nonhost_count": 0,
            "selected_nonhost_rows": [],
            "positive_join_count": 0, "timely_positive_join_count": 0,
            "final_can_start": False,
            "pre_invitation_candidate": {
                "character_id": 38293, "planner_join_raw": 75000,
                "travel_days": 3, "arrival_raw": 53220000,
                "planned_start_raw": 53220024,
            },
            "candidate_selected_membership": False,
            "authored_rule_membership": None,
            "native_guest_route_qualified": False,
            "read_only": True, "advertised": False,
        }

    def parse(self, payload: dict[str, object], envelope_status: str = "available") -> dict[str, object]:
        return parse_activity_feast_guest_route_proof_private_v1(
            payload, native_revision=19, date_raw=53219928,
            actor_id=29829, envelope_status=envelope_status,
        )

    def test_selected_empty_does_not_promote_pre_invitation_candidate(self) -> None:
        proof = self.parse(self.payload)
        self.assertEqual(proof["selected_nonhost_rows"], [])
        self.assertEqual(proof["pre_invitation_candidate"]["character_id"], 38293)
        self.assertIs(proof["native_guest_route_qualified"], False)
        empty = copy.deepcopy(self.payload)
        empty["candidate_status"] = "no_qualified_candidate"
        empty["pre_invitation_candidate"] = None
        empty["candidate_selected_membership"] = None
        self.assertIsNone(self.parse(empty)["candidate_selected_membership"])
        empty["candidate_selected_membership"] = False
        with self.assertRaises(BridgeUnavailableError):
            self.parse(empty)

    def test_unavailable_requires_null_observations_and_matching_envelope(self) -> None:
        unavailable = copy.deepcopy(self.payload)
        unavailable.update({
            "status": "unavailable", "candidate_status": "no_normal_refresh",
            "selected_status": "no_normal_refresh",
            "start_gate_status": "planner_unavailable",
        })
        for key in (
            "normal_refresh_sequence", "source_fingerprint", "active_rule_count",
            "filtered_group_count", "selected_row_count", "selected_nonhost_count",
            "selected_nonhost_rows", "positive_join_count",
            "timely_positive_join_count", "final_can_start",
            "pre_invitation_candidate", "candidate_selected_membership",
        ):
            unavailable[key] = None
        self.assertEqual(self.parse(unavailable, "unavailable")["status"], "unavailable")
        with self.assertRaises(BridgeUnavailableError):
            self.parse(unavailable, "available")
        unavailable["selected_nonhost_count"] = 0
        with self.assertRaises(BridgeUnavailableError):
            self.parse(unavailable, "unavailable")


if __name__ == "__main__":
    unittest.main()
