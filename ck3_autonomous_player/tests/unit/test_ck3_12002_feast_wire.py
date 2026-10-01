"""Actual C++ Feast wire through Python; no game process or pipe is used."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
FIXTURES = ROOT / "native_bridge" / "research" / "fixtures"

from xar_autoplayer.bridge.activity_feast_stage5_start_private_transport import (
    INPUT_STEP, POST_STEP, query_activity_feast_hosted_post_private_v1,
)
from xar_autoplayer.bridge.activity_feast_terminal_outcome_v1 import (
    normalize_activity_feast_terminal_outcome_v1,
)
from xar_autoplayer.bridge.activity_stage5_feast_full_cost_private_transport import (
    STEP as COST_STEP, query_activity_stage5_feast_full_cost_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


def actual_wire(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FixtureDriver:
    allow_private_activity_stage5_feast_full_cost_query = True
    allow_private_activity_feast_stage5_start_query = True

    def __init__(self, payload: dict[str, object], *, legacy: bool = False):
        self.payload = payload
        self.endpoint = self
        self.state = self
        self.requests: list[dict[str, object]] = []
        self.snapshot = {
            "snapshot_id": "offline-feast:" + str(payload["snapshot_revision"]),
            "revision": 5,
            "native_revision": payload["snapshot_revision"],
            "date_raw": payload["date_raw"],
            "paused": True,
            "map_ready": True,
            "played_character": {
                "character_id": payload["actor_character_id"], "alive": True,
            },
        }
        if not legacy:
            self.snapshot["diagnostics"] = {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }}

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        step = self.requests[-1]["step"]
        key = {
            COST_STEP: "activity_stage5_feast_full_cost",
            POST_STEP: "activity_feast_hosted_post",
            INPUT_STEP: "activity_feast_stage5_start_inputs",
        }[step]
        # Only the endpoint's existing outer envelope is supplied here.
        # The payload is passed unchanged from the real C++ serializer output.
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": step, "accepted": True, "status": "available",
                "private_build": True, "read_only": True,
                "advertised": False, "backend_id": "native-headless",
                key: self.payload,
            },
        }


def observed_post(payload: dict[str, object], *, legacy: bool = False) -> dict[str, object]:
    return query_activity_feast_hosted_post_private_v1(
        FixtureDriver(payload, legacy=legacy), expected_revision=5,
    )


def outcome(post: dict[str, object]) -> dict[str, object]:
    return normalize_activity_feast_terminal_outcome_v1(
        post, activity_id=16777234, actor_character_id=29829,
    )


class FeastWire12002Tests(unittest.TestCase):
    def test_actual_fullcost_reader_and_serializer_keep_negative_cost_and_canstart(self):
        payload = actual_wire("ck3_12002_feast_fullcost_wire.json")
        driver = FixtureDriver(payload)
        result = query_activity_stage5_feast_full_cost_private_v1(
            driver, expected_revision=5,
        )
        self.assertEqual(result["resources"], payload["resources"])
        self.assertEqual(result["resources"]["gold"]["configured_cost_raw"], 18500000)
        self.assertEqual(result["resources"]["piety"]["configured_cost_raw"], -100000)
        self.assertEqual(result["resources"]["barter_goods"]["resource_index"], 8)
        self.assertEqual(result["actor_gold_raw"], 134000000)
        self.assertIs(result["final_can_start"], False)
        self.assertEqual(result["final_can_start_failure_display"],
                         payload["final_can_start_failure_display"])
        self.assertEqual(result["exact_ck3_build"], "1.20.0.2")
        self.assertEqual(result["exe_sha256"], CK3_12002.executable_sha256)
        self.assertEqual([row["step"] for row in driver.requests], [COST_STEP])

    def test_actual_hosted_serializer_distinguishes_ongoing_completed_invalidated(self):
        wires = actual_wire("ck3_12002_feast_hosted_post_wire.json")
        for payload, status in zip(wires, ("ongoing", "completed", "invalidated"), strict=True):
            with self.subTest(status=status):
                post = observed_post(payload)
                self.assertEqual(post["hosted_activities"], payload["hosted_activities"])
                self.assertEqual(post["balances"], payload["balances"])
                terminal = outcome(post)
                self.assertEqual(terminal["status"], status)
                self.assertIs(terminal["terminal_flags_observed"], True)
                self.assertIs(terminal["native_completed"], status == "completed")
                self.assertIs(terminal["native_invalidated"], status == "invalidated")
                self.assertEqual(terminal["exact_ck3_build"], "1.20.0.2")
                self.assertEqual(terminal["exe_sha256"], CK3_12002.executable_sha256)

    def test_activity_disappearing_after_creation_keeps_terminal_unknown(self):
        payload = deepcopy(actual_wire("ck3_12002_feast_hosted_post_wire.json")[1])
        payload["hosted_activities"] = []
        terminal = outcome(observed_post(payload))
        self.assertEqual(terminal["status"], "unknown")
        self.assertEqual(terminal["unknown_reason"], "activity_not_observed")
        self.assertIsNone(terminal["native_completed"])
        self.assertIsNone(terminal["native_invalidated"])

    def test_legacy_identity_rows_do_not_acquire_completion_from_hello(self):
        payload = deepcopy(actual_wire("ck3_12002_feast_hosted_post_wire.json")[1])
        row = payload["hosted_activities"][0]
        for key in ("terminal_flags_observed", "native_completed", "native_invalidated"):
            del row[key]
        # The historical shape remains a valid read in both adapters. Neither
        # hello alone supplies missing lifecycle fields.
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                post = observed_post(payload, legacy=legacy)
                self.assertEqual(post["exact_ck3_build"], "1.19.0.6" if legacy else "1.20.0.2")
                terminal = outcome(post)
                self.assertEqual(terminal["status"], "unknown")
                self.assertEqual(terminal["unknown_reason"], "terminal_flags_unobserved")

    def test_overlapping_native_flags_are_preserved_without_exclusivity_assumption(self):
        # This deterministic transport case makes no claim that the overlap is
        # reachable in CK3; the native source has not proved mutual exclusion.
        payload = deepcopy(actual_wire("ck3_12002_feast_hosted_post_wire.json")[1])
        payload["hosted_activities"][0]["native_invalidated"] = True
        terminal = outcome(observed_post(payload))
        self.assertEqual(terminal["status"], "completed_and_invalidated")
        self.assertIs(terminal["native_completed"], True)
        self.assertIs(terminal["native_invalidated"], True)


if __name__ == "__main__":
    unittest.main()
