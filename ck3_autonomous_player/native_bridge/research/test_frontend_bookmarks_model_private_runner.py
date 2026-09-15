"""Focused controlled Bookmarks query test: one read-only step, real RED modes."""

from __future__ import annotations

import unittest

from run_frontend_gui_route_v1_live_acceptance import (
    _call_private_bookmarks_model,
)


class FakeEndpoint:
    def __init__(self, *, failure: bool = False) -> None:
        self.sent: list[dict[str, object]] = []
        self.failure = failure

    def send(self, frame: dict[str, object]) -> None:
        if self.failure:
            raise RuntimeError("pipe unavailable")
        self.sent.append(frame)


class FakeState:
    def __init__(self, status: str) -> None:
        self.status = status

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object] | None:
        assert 0 < timeout_seconds <= 15
        if self.status == "timeout":
            return None
        if self.status == "native-red":
            return {
                "type": "command_result",
                "request_id": request_id,
                "ok": False,
                "error": "application-main frontend executor rejected request",
            }
        return {
            "type": "command_result",
            "request_id": request_id,
            "ok": True,
            "result": {
                "step": "probe-frontend-bookmark-model-v1",
                "status": "identity_ready",
                "private_scope": "exact-build-bookmarks-model-v1",
            },
        }


class FakeDriver:
    def __init__(self, status: str, *, send_failure: bool = False) -> None:
        self.endpoint = FakeEndpoint(failure=send_failure)
        self.state = FakeState(status)


class PrivateBookmarksModelRunnerTest(unittest.TestCase):
    def test_only_fixed_read_only_native_step_is_submitted(self) -> None:
        driver = FakeDriver("ok")
        call = _call_private_bookmarks_model(driver, 20.0)
        self.assertFalse(call["is_error"])
        self.assertTrue(call["envelope_valid"])
        self.assertEqual(len(driver.endpoint.sent), 1)
        request = driver.endpoint.sent[0]
        self.assertEqual(request["step"], "probe-frontend-bookmark-model-v1")
        self.assertEqual(request["expected_revision"], 0)
        self.assertNotIn("character_id", request)

    def test_native_rejection_and_timeout_remain_distinct(self) -> None:
        rejected = _call_private_bookmarks_model(FakeDriver("native-red"), 20.0)
        self.assertTrue(rejected["is_error"])
        self.assertEqual(
            rejected["raw_frame"]["error"],
            "application-main frontend executor rejected request",
        )
        self.assertNotIn("timed_out", rejected)
        timed_out = _call_private_bookmarks_model(FakeDriver("timeout"), 20.0)
        self.assertTrue(timed_out["is_error"])
        self.assertTrue(timed_out["timed_out"])
        self.assertTrue(timed_out["submitted"])

    def test_pipe_failure_is_unexecuted(self) -> None:
        failed = _call_private_bookmarks_model(
            FakeDriver("ok", send_failure=True), 20.0
        )
        self.assertTrue(failed["is_error"])
        self.assertFalse(failed["submitted"])


if __name__ == "__main__":
    unittest.main()
