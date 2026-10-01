"""Consume exact JSON emitted by the 1.20 Sway and realm-law C++ fixtures."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.active_scheme_sway_formal_private_transport import (
    query_active_scheme_sway_receipt_private_v1,
    submit_active_scheme_sway_private_v1,
)
from xar_autoplayer.bridge.active_scheme_sway_private_transport import (
    query_active_scheme_sway_target_private_v1,
)
from xar_autoplayer.bridge.realm_law_paused_private_transport import (
    STEP as LAW_STEP, query_realm_law_final_terms_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge" / "research" / "fixtures"


def envelope(name: str) -> dict[str, object]:
    wire = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return wire["result"] if "result" in wire else wire


def paused_frame(value: dict[str, object]) -> dict[str, object]:
    revision = value["snapshot_revision"]
    return {
        "snapshot_id": f"native:{revision}",
        "revision": revision + 1,
        "native_revision": revision,
        "date_raw": value["date_raw"],
        "paused": True,
        "map_ready": True,
        "played_character": {
            "character_id": value["actor_character_id"], "alive": True,
        },
        "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        }},
    }


class FixtureDriver:
    allow_private_active_scheme_sway_query = True
    allow_private_active_scheme_sway_action = True
    allow_private_realm_law_paused_query = True

    def __init__(self, reply: dict[str, object], snapshot: dict[str, object]):
        self.reply = reply
        self.snapshot = snapshot
        self.sent: list[dict[str, object]] = []
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": deepcopy(self.reply),
        }


class SwayLaw12002WireTest(unittest.TestCase):
    def assert_exact_build(self, value: dict[str, object]) -> None:
        self.assertEqual(value["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(value["exe_sha256"], CK3_12002.executable_sha256)

    def test_native_law_costs_and_copied_reasons_survive_python_read(self) -> None:
        # The native fixture emits its actual payload, not the command_result
        # wrapper. Add only the existing transport envelope in this driver.
        value = envelope("ck3_12002_realm_law_final_terms_wire.json")
        reply = {
            "step": LAW_STEP, "accepted": True, "status": "available",
            "private_build": True, "read_only": True, "advertised": False,
            "realm_law_final_terms": value, "backend_id": "native-headless",
        }
        snapshot = paused_frame(value)
        driver = FixtureDriver(reply, snapshot)
        actual = query_realm_law_final_terms_private_v1(
            driver, expected_revision=snapshot["revision"],
        )
        self.assert_exact_build(actual)
        self.assertEqual({key: actual[key] for key in value}, value)
        self.assertEqual(len(actual["cost_slots"]), 10)
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.sent[0]["step"], reply["step"])

    def test_native_sway_legality_and_opinion_survive_python_read(self) -> None:
        reply = envelope("ck3_12002_sway_query_wire.json")
        value = reply["active_scheme_sway"]
        snapshot = paused_frame(value)
        driver = FixtureDriver(reply, snapshot)
        actual = query_active_scheme_sway_target_private_v1(
            driver, expected_revision=snapshot["revision"],
            target_character_id=value["target_character_id"],
        )
        self.assert_exact_build(actual)
        self.assertEqual({key: actual[key] for key in value}, value)
        self.assertEqual(driver.sent[0]["step"], reply["step"])

    def test_native_sway_submit_and_receipt_preserve_the_same_source_build(self) -> None:
        query = envelope("ck3_12002_sway_query_wire.json")
        value = query["active_scheme_sway"]
        snapshot = paused_frame(value)
        read = query_active_scheme_sway_target_private_v1(
            FixtureDriver(query, snapshot), expected_revision=snapshot["revision"],
            target_character_id=value["target_character_id"],
        )
        submitted = envelope("ck3_12002_sway_submit_wire.json")
        native_ack = submitted["active_scheme_sway_formal"]
        actual_ack = submit_active_scheme_sway_private_v1(
            FixtureDriver(submitted, snapshot), readback=read,
            action_id=native_ack["action_id"],
        )
        self.assert_exact_build(actual_ack)
        self.assertEqual({key: actual_ack[key] for key in native_ack}, native_ack)
        received = envelope("ck3_12002_sway_receipt_wire.json")
        native_receipt = received["active_scheme_sway_formal"]
        actual_receipt = query_active_scheme_sway_receipt_private_v1(
            FixtureDriver(received, snapshot),
            target_character_id=value["target_character_id"],
            action_id=native_receipt["action_id"],
            expected_revision=snapshot["native_revision"],
            pre_capture_epoch=native_ack["pre_capture_epoch"],
        )
        self.assert_exact_build(actual_receipt)
        self.assertEqual(
            {key: actual_receipt[key] for key in native_receipt}, native_receipt,
        )

    def test_native_active_sway_progress_preserves_opaque_other_scheme_count(self) -> None:
        reply = envelope("ck3_12002_sway_active_wire.json")
        value = reply["active_scheme_sway"]
        snapshot = paused_frame(value)
        actual = query_active_scheme_sway_target_private_v1(
            FixtureDriver(reply, snapshot), expected_revision=snapshot["revision"],
            target_character_id=value["target_character_id"],
        )
        self.assert_exact_build(actual)
        self.assertEqual({key: actual[key] for key in value}, value)
        self.assertGreater(actual["active_scheme_count"], len(actual["active_sway_instances"]))
        row = actual["active_sway_instances"][0]
        self.assertEqual((row["progress"], row["progress_goal"]), (355, 365))
        self.assertTrue(actual["matching_sway_active"])
        self.assertNotIn("terminal", actual)


if __name__ == "__main__":
    unittest.main()
