"""Risk gates for a bounded, single war-route order."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from xar_autoplayer.errors import AgentError
from xar_autoplayer.exact_war_move_stop import (
    SCHEMA, check_before, check_checkpoint, check_poststate, read_contract,
    validate_contract,
)


def contract() -> dict[str, object]:
    return {
        "schema": SCHEMA, "date_raw": 53157816, "war_id": 16777237,
        "army_id": 16777450, "origin_province_id": 2634,
        "target_province_id": 2640, "source_save_sha256": "a" * 64,
        "source_driver_sha256": "b" * 64,
    }


def frame(*, moving: bool = False, revision: int = 1) -> dict[str, object]:
    army = {
        "army_id": 16777450, "controllable": True,
        "current_province_id": 2634,
        "move_target_province_id": 2640 if moving else None,
        "route_province_ids": [2634, 2640] if moving else [],
    }
    return {
        "snapshot_id": f"native:{revision}", "revision": revision,
        "native_revision": revision, "date_raw": 53157816,
        "paused": True, "map_ready": True, "one_life_terminal": False,
        "episode_run_id": "native-1", "episode_character_id": 77,
        "active_wars": [{"war_id": 16777237, "allied_armies": [copy.deepcopy(army)]}],
        "player_armies": [army],
    }


def candidate(step: str, *, phase: str = "native_war_general_battle_distant_route_start") -> dict[str, object]:
    return {
        "snapshot_id": "native:1", "revision": 1, "selected_step": step,
        "plan": {
            "phase": phase, "selected_step": step, "source_war_id": 16777237,
            "contact_recheck_required_before_each_day": True,
            "future_contact_authorized": False,
            "general_battle_forecast_used_for_decision": True,
        },
    }


def ack() -> dict[str, object]:
    return {
        "step": "move-army-16777450-to-2640", "status": "submitted", "accepted": True,
        "war_action": {
            "status": "moving", "army_id": 16777450,
            "target_province_id": 2640, "submitted_date_raw": 53157816,
        },
    }


class ExactWarMoveStopTests(unittest.TestCase):
    def test_bound_contract_and_prelude(self) -> None:
        value = contract()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "stop.json"
            raw = json.dumps(value).encode()
            path.write_bytes(raw)
            self.assertEqual(read_contract(path, hashlib.sha256(raw).hexdigest()), value)
            with self.assertRaises(AgentError):
                read_contract(path, "0" * 64)
        before = frame()
        before["_semantic"] = {"active_wars": before["active_wars"], "player_armies": before["player_armies"]}
        self.assertFalse(check_before(candidate("query-army-strengths-v1"), before, value))
        self.assertFalse(check_before(candidate("preview-move-army-16777450-to-2640"), before, value))
        self.assertTrue(check_before(candidate("move-army-16777450-to-2640"), before, value))
        for selected in ("life-advance", "move-army-16777450-to-2639"):
            with self.subTest(selected=selected), self.assertRaises(AgentError):
                check_before(candidate(selected), before, value)
        with self.assertRaises(AgentError):
            check_before(candidate("move-army-16777450-to-2640", phase="fixture"), before, value)

    def test_ack_alone_or_stale_postframe_cannot_stop(self) -> None:
        value = contract()
        before = frame()
        after = frame(moving=True, revision=2)
        proof = check_poststate(before, ack(), after, value)
        self.assertEqual(proof["remaining_route_province_ids"], [2640])
        for changed in (frame(revision=2), frame(moving=True), frame(moving=True, revision=2)):
            if changed["snapshot_id"] == after["snapshot_id"]:
                changed["date_raw"] += 24
            with self.assertRaises(AgentError):
                check_poststate(before, ack(), changed, value)
        wrong = frame(moving=True, revision=2)
        wrong["player_armies"][0]["route_province_ids"] = [2634, 2641]
        with self.assertRaises(AgentError):
            check_poststate(before, ack(), wrong, value)
        with self.assertRaises(AgentError):
            check_poststate(before, {**ack(), "accepted": False}, after, value)

    def test_checkpoint_must_retain_date_war_and_route(self) -> None:
        value = validate_contract(contract())
        saved = frame(moving=True, revision=3)
        self.assertEqual(
            check_checkpoint({"date_raw": value["date_raw"]}, saved, value)["status"],
            "checkpoint_verified",
        )
        saved["active_wars"] = []
        with self.assertRaises(AgentError):
            check_checkpoint({"date_raw": value["date_raw"]}, saved, value)


if __name__ == "__main__":
    unittest.main()
