"""Portable six-case lease regression plus producer/legacy scope boundaries.

Derived from the frozen P07 focused strategy tests; fixture Native envelopes
are explicit offline reconstructions and carry no game/action credit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import xar_autoplayer.strategy as candidate


class RouteFailureLeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.step = candidate.query_route_contact_horizon_step(
            318767248, 2635,
            [218103869, 268435608, 285212675, 369099120,
             402653372, 419430694, 452984965, 452985060],
        )
        self.frame = {
            "snapshot_id": "native:142", "revision": 2,
            "native_revision": 142, "date_raw": 53328720,
            "played_character": {"character_id": 40526},
            "episode_run_id": "native-40526-c7a6edcc32b8",
            "diagnostics": {"connection_generation": 5, "bridge_pid": 249712},
        }
        self.result = {
            "schema": "xar.route-contact-readonly-unavailable.v1",
            "step": self.step, "status": "unavailable", "accepted": False,
            "route_contact_horizon": None,
            "unavailable_reason": "native_complete_contact_route_unavailable",
            "queried_snapshot_id": "native:142", "queried_revision": 2,
            "queried_native_revision": 142,
            "queried_connection_generation": 5,
            "queried_episode_run_id": self.frame["episode_run_id"],
            "queried_date_raw": 53328720,
            "queried_actor_character_id": 40526,
            "queried_bridge_pid": 249712,
            "readonly_unavailable_evidence": {
                "same_frame_readback": {
                    "starting_frame": {"native_revision": 142},
                    "ending_frame": {"native_revision": 142},
                },
            },
        }

    def _review(self, result: dict[str, object], *, strategy=candidate):
        history = [{"index": 1, "command": self.step, "ok": False,
                    "result": result}]
        return strategy._current_frame_route_contact_query_failure(
            history, self.frame, self.step,
        )

    def test_exact_typed_unavailable_becomes_current_frame_rejection(self):
        self.assertEqual(self._review(self.result)["scope_status"], "current_frame")
        self.assertEqual(self._review(self.result)["status"], "unavailable")

    def test_stale_native_revision_cannot_claim_current_frame(self):
        stale = dict(self.result, queried_native_revision=141)
        self.assertIsNone(self._review(stale))

    def test_other_unavailable_reason_cannot_claim_exact_route_failure(self):
        other = dict(self.result, unavailable_reason="some_other_failure")
        self.assertEqual(self._review(other)["scope_status"], "unknown_frame")

    def test_other_game_pid_cannot_claim_current_frame(self):
        other = dict(self.result, queried_bridge_pid=249713)
        self.assertEqual(self._review(other)["scope_status"], "unknown_frame")

    def test_drifting_native_readback_cannot_claim_current_frame(self):
        other = dict(self.result, readonly_unavailable_evidence={
            "same_frame_readback": {
                "starting_frame": {"native_revision": 142},
                "ending_frame": {"native_revision": 143},
            },
        })
        self.assertEqual(self._review(other)["scope_status"], "unknown_frame")

    def test_no_horizon_is_never_contact_free(self):
        self.assertIsNone(self.result["route_contact_horizon"])
        self.assertEqual(self._review(self.result)["status"], "unavailable")


    def test_driver_produced_fixture_is_current_frame_unavailable(self):
        import json
        body = json.loads((Path(__file__).parent / "fixtures/route_contact_typed_unavailable_v1.json").read_text(encoding="utf-8"))["body"]
        result = body["result"]
        source = body["planning_source_frame"]
        frame = {
            "snapshot_id": source["snapshot_id"], "revision": source["revision"],
            "native_revision": source["native_revision"], "date_raw": source["date_raw"],
            "played_character": {"character_id": source["actor_character_id"]},
            "episode_run_id": source["episode_run_id"],
            "diagnostics": {"connection_generation": source["connection_generation"], "bridge_pid": source["bridge_pid"]},
        }
        row = {"index": 1, "command": body["selected_step"], "ok": False, "result": result}
        review = candidate._current_frame_route_contact_query_failure([row], frame, body["selected_step"])
        self.assertEqual(review["scope_status"], "current_frame")
        self.assertEqual(review["status"], "unavailable")
        self.assertIsNone(result["route_contact_horizon"])

    def test_expired_generation_episode_and_date_do_not_latch_current_frame(self):
        for key, value in (("queried_connection_generation", 4), ("queried_episode_run_id", "old")):
            with self.subTest(key=key):
                self.assertIsNone(self._review(dict(self.result, **{key: value})))
        review = self._review(dict(self.result, queried_date_raw=self.frame["date_raw"] - 24))
        self.assertEqual(review["scope_status"], "unknown_frame")

    def test_unknown_failure_remains_guarded(self):
        row = {"index": 1, "command": self.step, "ok": False, "error": "unknown"}
        review = candidate._current_frame_route_contact_query_failure([row], self.frame, self.step)
        self.assertEqual(review["scope_status"], "unknown_frame")


if __name__ == "__main__":
    unittest.main()
