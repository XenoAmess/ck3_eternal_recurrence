"""Consume exact native Sway completion packets without accessing CK3."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.active_scheme_sway_completion_private_transport import (
    query_active_scheme_sway_completion_private_v1,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_sway_completion"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CompletionPacketDriver:
    """Correlate request_id only; all other wire fields come from C++."""

    allow_private_active_scheme_sway_completion_query = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        native = packet["result"]["sway_completion"]
        revision = native["snapshot_revision"]
        self.snapshot = {
            "snapshot_id": f"native:{revision}", "revision": revision + 1,
            "native_revision": revision, "date_raw": native["date_raw"],
            "paused": True, "map_ready": True,
            "played_character": {"character_id": native["actor_character_id"], "alive": True},
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }
        self.sent: list[dict[str, object]] = []
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        packet = deepcopy(self.packet)
        packet["request_id"] = request_id
        return packet


def query(driver: CompletionPacketDriver) -> dict[str, object]:
    native = driver.packet["result"]["sway_completion"]
    return query_active_scheme_sway_completion_private_v1(
        driver, expected_revision=driver.snapshot["revision"],
        target_character_id=native["target_character_id"],
        scheme_instance_id=native["scheme_instance_id"],
    )


class SwayCompletion12002WireTest(unittest.TestCase):
    def test_actual_native_packets_preserve_current_terminal_absence_and_nullable_chance_facts(self) -> None:
        provenance = load_fixture("provenance.json")
        outputs = []
        for name in provenance["payload_sha256"]:
            with self.subTest(packet=name):
                packet = load_fixture(name)
                native = packet["result"]["sway_completion"]
                driver = CompletionPacketDriver(packet)
                actual = query(driver)
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(actual["queried_native_revision"], native["snapshot_revision"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-sway-completion-v1-private")
                self.assertEqual(request["expected_revision"], native["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], native["snapshot_revision"])
                for key in ("actor_character_id", "target_character_id", "scheme_instance_id"):
                    self.assertEqual(request[key], native[key])
                self.assertNotIn("terminal", actual)
                outputs.append(actual)
        self.assertTrue(outputs)
        self.assertTrue(any(row["native_terminal_state_observed"] for row in outputs))
        self.assertTrue(any(row["native_success_chance_observed"] for row in outputs))
        self.assertTrue(any(not row["instance_present"] and row["available"] for row in outputs))
        self.assertTrue(any(row["storage_slot_reused"] for row in outputs))
        self.assertTrue(any(not row["available"] for row in outputs))
        for row in outputs:
            self.assertFalse(row["terminal_cause_observed"])
            self.assertEqual(row["terminal_cause"], "unknown")
            if row["native_terminal_state_observed"]:
                self.assertEqual(row["native_status_raw"], 1)
                self.assertEqual(row["native_status_key"], "invalidated")
                self.assertIsNone(row["native_success_chance_raw"])
            if not row["instance_present"]:
                self.assertFalse(row["native_terminal_state_observed"])
            if row["native_success_chance_observed"]:
                self.assertIsInstance(row["native_success_chance_raw"], int)
                self.assertEqual(row["native_success_chance_scale"], 100000)
                self.assertEqual(row["native_success_chance_unit"], "percent")

    def test_completion_query_is_disabled_before_sending_a_packet(self) -> None:
        first = next(iter(load_fixture("provenance.json")["payload_sha256"]))
        driver = CompletionPacketDriver(load_fixture(first))
        driver.allow_private_active_scheme_sway_completion_query = False
        with self.assertRaises(UnsupportedStepError):
            query(driver)
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
