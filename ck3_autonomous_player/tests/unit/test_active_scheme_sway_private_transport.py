"""No-launch check for the unadvertised paused sway read path."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.active_scheme_sway_private_transport import (
    SCHEMA, STEP_PREFIX, query_active_scheme_sway_target_private_v1,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
        "date_raw": 53219928, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
    }


class Endpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)


class State:
    def __init__(self, endpoint: Endpoint) -> None:
        self.endpoint = endpoint

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        request = self.endpoint.sent[-1]
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": request["step"], "accepted": True,
                "status": "available", "private_build": True,
                "read_only": True, "advertised": False,
                "backend_id": "native-headless",
                "active_scheme_sway": {
                    "schema": SCHEMA, "snapshot_revision": 4,
                    "capture_epoch": 8085, "container_generation": 17,
                    "date_raw": 53219928, "actor_character_id": 29829,
                    "target_character_id": 32716,
                    "active_scheme_count": 0,
                    "matching_sway_active": False,
                    "native_complete_can_send": True,
                    "native_legal_now": True,
                    "native_failure_classification": "",
                },
            },
        }


class Driver:
    def __init__(self, enabled: bool) -> None:
        self.allow_private_active_scheme_sway_query = enabled
        self.endpoint = Endpoint()
        self.state = State(self.endpoint)

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot())


class SwayPrivateTransportTest(unittest.TestCase):
    def test_paused_read_does_not_submit_action(self) -> None:
        driver = Driver(True)
        result = query_active_scheme_sway_target_private_v1(
            driver, expected_revision=5, target_character_id=32716,
        )
        self.assertTrue(result["native_legal_now"])
        self.assertEqual(len(driver.endpoint.sent), 1)
        self.assertEqual(driver.endpoint.sent[0]["step"], STEP_PREFIX + "32716")
        self.assertEqual(driver.endpoint.sent[0]["expected_revision"], 4)

    def test_default_off_rejects_before_wire(self) -> None:
        driver = Driver(False)
        with self.assertRaises(UnsupportedStepError):
            query_active_scheme_sway_target_private_v1(
                driver, expected_revision=5, target_character_id=32716,
            )
        self.assertEqual(driver.endpoint.sent, [])


if __name__ == "__main__":
    unittest.main()
