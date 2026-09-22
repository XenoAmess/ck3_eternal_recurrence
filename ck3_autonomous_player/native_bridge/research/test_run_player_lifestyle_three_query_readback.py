"""Focused no-CK3 shape tests for the bounded private M4 readback entry."""

from __future__ import annotations

import copy
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from run_player_lifestyle_current_state_read import PRIVATE_STEP as STATE_STEP
from run_player_lifestyle_current_state_read import _frame as life2_frame
from run_player_lifestyle_three_query_readback import (
    FOCUS_STEP,
    PERK_STEP,
    _frame,
    _query,
    _verify_ordinary_profile,
    run_three_queries,
)
from test_run_player_lifestyle_current_state_read import typed_state


EPISODE = "native-29829-example"


def paused_frame() -> dict[str, object]:
    return {
        "snapshot_id": "native:3",
        "native_revision": 3,
        "date_raw": 53_178_312,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29_829, "alive": True},
        "episode_run_id": EPISODE,
    }


class FakeEndpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)


class FakeState:
    def __init__(self, endpoint: FakeEndpoint) -> None:
        self.endpoint = endpoint
        self.frame = paused_frame()
        self.focus_status = "observed_native_legal"
        self.perk_status = "available"

    def semantic_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.frame)

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object]:
        request = self.endpoint.sent[-1]
        if request["request_id"] != request_id or timeout_seconds <= 0:
            raise RuntimeError("fake native read binding lost")
        step = request["step"]
        result: dict[str, object] = {
            "step": step,
            "private_build": True,
            "advertised": False,
            "episode_run_id": EPISODE,
        }
        if step == STATE_STEP:
            result.update(status="available", snapshot=typed_state())
        elif step == PERK_STEP:
            snapshot = typed_state()
            snapshot["legal_perk_candidates"] = {
                "status": self.perk_status,
                "scope": "policy_target",
                "items": [{"key": "cutting_corners_perk", "lifestyle_key": "stewardship_lifestyle"}],
            }
            snapshot["readiness"]["legal_perk_candidates_ready"] = (
                self.perk_status == "available"
            )
            result.update(
                status="available",
                formal_precondition_status="permitted",
                snapshot=snapshot,
            )
        elif step == FOCUS_STEP:
            result.update(
                status=self.focus_status,
                read_only=True,
                policy_scoped=True,
                target_key="stewardship_wealth_focus",
                snapshot_id="native:3",
                native_legal=self.focus_status == "observed_native_legal",
                scanned_database_rows=16,
            )
        else:
            raise RuntimeError("test sent an unexpected step")
        return {
            "type": "command_result",
            "protocol_version": 1,
            "request_id": request_id,
            "ok": True,
            "result": result,
        }


class FakeDriver:
    def __init__(self) -> None:
        self.endpoint = FakeEndpoint()
        self.state = FakeState(self.endpoint)

    def take_internal_semantic_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()


class LifeThreeQueryTest(unittest.TestCase):
    def test_preflight_verifies_ordinary_xar_off_profile(self) -> None:
        spec = object()
        expected = {"environment_sha256": "profile-bound"}
        with patch(
            "xar_autoplayer.environment.verify_profile", return_value=expected
        ) as verify:
            self.assertIs(_verify_ordinary_profile(spec), expected)
        verify.assert_called_once_with(spec, xar_enabled="xar_off")

    def manifest(self) -> dict[str, object]:
        return {
            "expected_actor_id": 29_829,
            "expected_date_raw": 53_178_312,
            "episode_run_id": EPISODE,
            "bounds": {"native_query_seconds": 20},
        }

    def test_three_read_only_queries_preserve_one_independent_frame(self) -> None:
        driver = FakeDriver()
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver,
                self.manifest(),
                Path(temp),
                deadline=time.monotonic() + 120,
            )
            self.assertTrue((Path(temp) / "paused-life2-current-state.json").exists())
            self.assertTrue((Path(temp) / f"{PERK_STEP}.json").exists())
            self.assertTrue((Path(temp) / f"{FOCUS_STEP}.json").exists())
        self.assertEqual(result["status"], "three_queries_observed")
        self.assertEqual(result["gameplay_actions"], 0)
        self.assertFalse(result["date_advanced"])
        self.assertEqual(
            [item["step"] for item in driver.endpoint.sent],
            [STATE_STEP, PERK_STEP, FOCUS_STEP],
        )
        self.assertEqual(result["starting_frame"], result["ending_frame"])
        self.assertEqual(
            _frame(driver.take_internal_semantic_snapshot())["episode_run_id"], EPISODE
        )
        self.assertNotIn("episode_run_id", life2_frame(driver.state.semantic_snapshot()))

    def test_formal_unavailable_is_not_legal_candidate_evidence(self) -> None:
        driver = FakeDriver()
        driver.state.perk_status = "unavailable"
        with tempfile.TemporaryDirectory() as temp:
            result = run_three_queries(
                driver,
                self.manifest(),
                Path(temp),
                deadline=time.monotonic() + 120,
            )
        self.assertEqual(result["status"], "evidence_insufficient")
        self.assertEqual(result["steps"][1]["status"], "native_unavailable")

    def test_independent_frame_drift_is_red(self) -> None:
        driver = FakeDriver()
        source = _frame(driver.take_internal_semantic_snapshot())
        original_wait = driver.state.wait_for_command_result

        def drift(request_id: str, timeout_seconds: float) -> dict[str, object]:
            reply = original_wait(request_id, timeout_seconds)
            driver.state.frame["date_raw"] += 1
            return reply

        driver.state.wait_for_command_result = drift
        result = _query(driver, step=FOCUS_STEP, source_frame=source, timeout_seconds=20)
        self.assertEqual(result["status"], "red")
        self.assertEqual(result["issue"], "paused_frame_drift")

    def test_action_step_is_rejected_before_transport(self) -> None:
        driver = FakeDriver()
        source = _frame(driver.take_internal_semantic_snapshot())
        with self.assertRaisesRegex(RuntimeError, "non-read-only"):
            _query(driver, step="private-submit-player-lifestyle-perk-v1", source_frame=source, timeout_seconds=20)
        self.assertEqual(driver.endpoint.sent, [])


if __name__ == "__main__":
    unittest.main()
