from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.native_driver import _fresh_preview_first_hop_steps
from xar_autoplayer.bridge.war_contract import (
    MOVE_ARMY_CAPABILITY,
    PREVIEW_MOVE_ARMY_CAPABILITY,
    QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
    move_army_step,
    preview_move_army_step,
    query_route_contact_horizon_step,
)


ARMY_ID = 18
TARGET_ID = 30
FIRST_HOP_ID = 21
HOSTILE_ID = 24
CAPABILITIES = {
    MOVE_ARMY_CAPABILITY,
    PREVIEW_MOVE_ARMY_CAPABILITY,
    QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,
}
ADVERTISED = {
    move_army_step(ARMY_ID, TARGET_ID),
    preview_move_army_step(ARMY_ID, TARGET_ID),
    query_route_contact_horizon_step(ARMY_ID, TARGET_ID, (HOSTILE_ID,)),
}
EXPECTED = {
    move_army_step(ARMY_ID, FIRST_HOP_ID),
    preview_move_army_step(ARMY_ID, FIRST_HOP_ID),
    query_route_contact_horizon_step(ARMY_ID, FIRST_HOP_ID, (HOSTILE_ID,)),
}


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:3",
        "revision": 4,
        "native_revision": 3,
        "episode_run_id": "run-1",
        "date_raw": 53_144_520,
        "paused": True,
        "map_ready": True,
        "active_event": None,
        "pending_character_interaction": None,
        "diagnostics": {"connection_generation": 2},
        "player_armies": [
            {
                "army_id": ARMY_ID,
                "controllable": True,
                "current_province_id": 20,
            }
        ],
        "active_wars": [
            {"enemy_armies": [{"army_id": HOSTILE_ID, "current_province_id": 30}]}
        ],
    }


def _preview_row() -> dict[str, object]:
    return {
        "index": 1,
        "command": preview_move_army_step(ARMY_ID, TARGET_ID),
        "ok": True,
        "result": {
            "queried_snapshot_id": "native:3",
            "queried_revision": 4,
            "queried_native_revision": 3,
            "queried_connection_generation": 2,
            "queried_episode_run_id": "run-1",
            "route_preview": {
                "status": "available",
                "army_id": ARMY_ID,
                "origin_province_id": 20,
                "target_province_id": TARGET_ID,
                "route_province_ids": [FIRST_HOP_ID, 22, TARGET_ID],
                "previewed_date_raw": 53_144_520,
            },
        },
    }


class NativeFirstHopProjectionTests(unittest.TestCase):
    def _project(
        self,
        snapshot: dict[str, object] | None = None,
        history: list[dict[str, object]] | None = None,
        advertised: set[str] | None = None,
        capabilities: set[str] | None = None,
    ) -> set[str]:
        return _fresh_preview_first_hop_steps(
            _snapshot() if snapshot is None else snapshot,
            [_preview_row()] if history is None else history,
            ADVERTISED if advertised is None else advertised,
            CAPABILITIES if capabilities is None else capabilities,
        )

    def test_same_frame_preview_exposes_only_first_hop(self) -> None:
        projected = self._project()
        self.assertEqual(projected, EXPECTED)
        self.assertNotIn(move_army_step(ARMY_ID, 22), projected)
        self.assertNotIn(move_army_step(ARMY_ID, 99), projected)

    def test_combat_first_hop_is_preview_only_until_typed_retreat_gate(self) -> None:
        snapshot = _snapshot()
        snapshot["player_armies"][0]["in_combat"] = True
        projected = self._project(snapshot=snapshot)
        self.assertEqual(
            projected,
            EXPECTED - {move_army_step(ARMY_ID, FIRST_HOP_ID)},
        )

    def test_route_with_origin_prefix_still_exposes_first_travel_hop(self) -> None:
        row = _preview_row()
        row["result"]["route_preview"]["route_province_ids"].insert(0, 20)
        self.assertEqual(self._project(history=[row]), EXPECTED)

    def test_no_preview_proof_exposes_no_hop(self) -> None:
        self.assertEqual(self._project(history=[]), set())

    def test_successful_restore_invalidates_pre_restore_preview(self) -> None:
        # A replay can reproduce the same native frame identifiers; only
        # history from after the latest successful restore may authorize a hop.
        restored = {"index": 2, "command": "restore-checkpoint", "ok": True}
        self.assertEqual(self._project(history=[_preview_row(), restored]), set())
        post_restore = copy.deepcopy(_preview_row())
        post_restore["index"] = 3
        self.assertEqual(
            self._project(history=[_preview_row(), restored, post_restore]),
            EXPECTED,
        )

    def test_unadvertised_preview_target_cannot_expand_hop(self) -> None:
        self.assertEqual(self._project(advertised=set()), set())

    def test_missing_capability_cannot_expand_hop(self) -> None:
        for missing in CAPABILITIES:
            with self.subTest(missing=missing):
                self.assertEqual(
                    self._project(capabilities=CAPABILITIES - {missing}), set()
                )

    def test_stale_snapshot_revision_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["revision"] = 5
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_stale_snapshot_identity_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["snapshot_id"] = "native:4"
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_stale_native_revision_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["native_revision"] = 4
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_stale_connection_generation_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["diagnostics"] = {"connection_generation": 3}
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_stale_episode_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["episode_run_id"] = "run-2"
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_changed_army_origin_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["player_armies"][0]["current_province_id"] = 21
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_changed_date_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["date_raw"] += 1_440
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_uncontrollable_army_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["player_armies"][0]["controllable"] = False
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_blocking_modal_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["active_event"] = {"event_id": "blocked"}
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_pending_interaction_cannot_expand_hop(self) -> None:
        snapshot = _snapshot()
        snapshot["pending_character_interaction"] = {"interaction_id": 9}
        self.assertEqual(self._project(snapshot=snapshot), set())

    def test_failed_latest_preview_does_not_resurrect_older_proof(self) -> None:
        failed = copy.deepcopy(_preview_row())
        failed["index"] = 2
        failed["ok"] = False
        self.assertEqual(self._project(history=[_preview_row(), failed]), set())

    def test_route_target_mismatch_cannot_expand_hop(self) -> None:
        row = _preview_row()
        row["result"]["route_preview"]["route_province_ids"][-1] = 31
        self.assertEqual(self._project(history=[row]), set())


if __name__ == "__main__":
    unittest.main()
