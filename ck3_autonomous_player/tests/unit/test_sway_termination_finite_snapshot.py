"""One focused regression for termination reads using finite paused snapshots.

The native result and transport endpoint are synthetic. This executes the real
shared read transport and normalizer; it grants no native or game qualification.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.active_scheme_sway_completion_termination_private_transport import (
    query_active_scheme_sway_completion_termination_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12004


class _FiniteTerminationDriver:
    allow_private_active_scheme_sway_completion_termination_query = True

    def __init__(self) -> None:
        self.endpoint = self
        self.state = self
        self.finite_reads = 0
        self.requests: list[dict[str, object]] = []
        self.snapshot = {
            "snapshot_id": "synthetic:finite-sway-termination",
            "revision": 17, "native_revision": 701, "date_raw": 53220000,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True},
            "active_event": None, "pending_character_interaction": None,
            "one_life_terminal_reason": None,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12004.game_version,
                "expected_ck3_sha256": CK3_12004.executable_sha256,
            }},
        }
        self.native = {
            "schema": "xar.ck3.sway-completion-termination.v1",
            "available": True, "unavailable_reason": "", "read_only": True,
            "observer_attached": True, "actor_character_id": 29829,
            "target_character_id": 34333, "scheme_instance_id": 134217986,
            "after_sequence": 0, "earliest_sequence": 0, "latest_sequence": 0,
            "retention_gap": False, "session_records_only": True,
            "material_effect_observed": False, "records": [],
        }

    def take_snapshot(self) -> dict[str, object]:
        raise AssertionError("termination query exported full command history")

    def take_snapshot_without_native_command_history(self) -> dict[str, object]:
        self.finite_reads += 1
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout_seconds: float):
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": "query-sway-completion-termination-v1-private",
                "accepted": True, "status": "available", "private_build": True,
                "read_only": True, "advertised": False, "backend_id": "native-headless",
                "snapshot_revision": self.snapshot["native_revision"],
                "date_raw": self.snapshot["date_raw"],
                "build_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "sway_completion_termination": deepcopy(self.native),
            },
        }


class SwayTerminationFiniteSnapshotTest(unittest.TestCase):
    def test_actor_and_transport_bookends_omit_full_history(self) -> None:
        driver = _FiniteTerminationDriver()
        result = query_active_scheme_sway_completion_termination_private_v1(
            driver, expected_revision=17, target_character_id=34333,
            scheme_instance_id=134217986,
        )

        self.assertEqual(driver.finite_reads, 3)
        self.assertEqual(len(driver.requests), 1)
        self.assertEqual(driver.requests[0]["expected_revision"], 701)
        self.assertEqual(driver.requests[0]["expected_snapshot_revision"], 701)
        self.assertEqual(result["queried_revision"], 17)
        self.assertEqual(result["queried_native_revision"], 701)
        self.assertEqual({key: result[key] for key in driver.native}, driver.native)
        self.assertIsNot(result["records"], driver.native["records"])


if __name__ == "__main__":
    unittest.main()
