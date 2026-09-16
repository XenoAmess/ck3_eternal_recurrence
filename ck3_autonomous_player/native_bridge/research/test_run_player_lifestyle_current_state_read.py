"""Focused acceptance-shape test for the LIFE2 private paused readback."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from run_player_lifestyle_current_state_read import (
    PRIVATE_STEP,
    run_owned_paused_life2_current_state_read,
)


def paused_frame(date_raw: int = 53_178_312) -> dict[str, object]:
    return {
        "snapshot_id": "native:3", "native_revision": 3,
        "date_raw": date_raw, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29_829, "alive": True},
    }


def typed_state() -> dict[str, object]:
    # Keys and presence values follow LIFE2's exact serializer fixture.
    return {
        "private_build": True, "advertised": False, "status": "available",
        "snapshot_id": "native:3", "public_revision": 3,
        "native_revision": 3, "proof_epoch": 3,
        "date_raw": 53_178_312, "player_character_id": 29_829,
        "current_focus": {
            "presence": "present", "key": "stewardship_wealth_focus",
            "lifestyle_key": "stewardship_lifestyle"},
        "current_lifestyle_progress": {
            "presence": "present", "lifestyle_key": "stewardship_lifestyle",
            "xp_total_raw": 0, "xp_within_level_raw": 0,
            "xp_per_level": 1000, "unspent_perk_points": 0,
            "used_perk_points": 0},
        "owned_perk_keys": [],
        "legal_focus_candidates": {
            "status": "unavailable", "reason": "lifestyle_window_unavailable", "items": []},
        "legal_perk_candidates": {
            "status": "unavailable", "reason": "lifestyle_window_unavailable", "items": []},
        "readiness": {
            "current_focus_ready": True, "lifestyle_progress_ready": True,
            "owned_perks_ready": True, "legal_focus_candidates_ready": False,
            "legal_perk_candidates_ready": False, "same_frame_ready": True},
    }


class FakeEndpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, frame: dict[str, object]) -> None:
        self.sent.append(frame)


class FakeState:
    def __init__(self, endpoint: FakeEndpoint, state: dict[str, object]) -> None:
        self.endpoint = endpoint
        self.state = state
        self.frames = [paused_frame(), paused_frame()]

    def semantic_snapshot(self) -> dict[str, object]:
        return self.frames.pop(0)

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        if timeout_seconds <= 0 or self.endpoint.sent[-1]["request_id"] != request_id:
            raise RuntimeError("fake request binding lost")
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": PRIVATE_STEP, "private_build": True,
                "advertised": False, "status": "available",
                "episode_run_id": "native-29829-example",
                "snapshot": self.state,
            },
        }


class Life2ReadbackTest(unittest.TestCase):
    def read(self, state: dict[str, object], *, after_date: int | None = None):
        endpoint = FakeEndpoint()
        driver = type("FakeDriver", (), {})()
        driver.endpoint = endpoint
        driver.state = FakeState(endpoint, state)
        if after_date is not None:
            driver.state.frames[1] = paused_frame(after_date)
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / "life2-read.json"
            result = run_owned_paused_life2_current_state_read(
                driver, "native-29829-example", {"native_commit": "exact-fixture"}, artifact)
            self.assertEqual(json.loads(artifact.read_text(encoding="utf-8"))["status"],
                             result["status"])
        return result, endpoint.sent

    def test_zero_values_are_observed_without_final_legality_or_action(self) -> None:
        result, sent = self.read(typed_state())
        self.assertEqual(result["status"], "state_observed_final_candidates_unavailable")
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["step"], PRIVATE_STEP)
        self.assertEqual(sent[0]["expected_snapshot_id"], "native:3")
        self.assertEqual(sent[0]["expected_player_character_id"], 29_829)
        self.assertEqual(result["observed"]["lifestyle_progress"]["unspent_perk_points"], 0)
        self.assertEqual(result["observed"]["final_candidates"], "unavailable_not_queried")

    def test_real_typed_progress_absence_is_evidence_insufficient(self) -> None:
        state = typed_state()
        state["current_lifestyle_progress"] = {"presence": "absent"}
        result, _ = self.read(state)
        self.assertEqual(result["status"], "typed_absent_progress_evidence_insufficient")

    def test_unknown_progress_cannot_be_promoted_to_ready(self) -> None:
        state = typed_state()
        state["current_lifestyle_progress"]["xp_total_raw"] = None
        result, _ = self.read(state)
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["issue"], "life2_present_progress_or_points_unknown")

    def test_independent_paused_frame_drift_is_red(self) -> None:
        result, _ = self.read(typed_state(), after_date=53_178_313)
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["issue"], "life2_read_changed_or_drifted_paused_frame")


if __name__ == "__main__":
    unittest.main()
