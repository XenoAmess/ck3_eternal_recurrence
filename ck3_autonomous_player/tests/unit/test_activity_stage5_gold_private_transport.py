"""No-launch contract for the default-off stage-5 named Gold read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_stage5_gold_private_transport import (
    SCHEMA, STEP, parse_activity_stage5_gold_payload_v1,
    query_activity_stage5_gold_private_v1,
    serialize_activity_stage5_gold_request_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
        "date_raw": 53219928, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
    }


def payload() -> dict[str, object]:
    return {
        "schema": SCHEMA, "snapshot_revision": 4,
        "date_raw": 53219928, "actor_character_id": 29829,
        "activity_key": "activity_feast", "planning_stage": 5,
        "normal_refresh_sequence": 17,
        "configured_cost": {
            "resource": "gold", "raw": 10_000_000, "scale": 100000,
            "source": "CostBreakdown.GetCost",
        },
        "resource_value": {
            "resource": "gold", "raw": 15_000_000, "scale": 100000,
            "source": "CCharacter.GetGold",
        },
        "final_can_start": None, "raw_slot12_resource_mapping": None,
        "read_only": True, "raw_pointer_fields_persisted": False,
    }


class Driver:
    allow_private_activity_stage5_gold_query = True

    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []
        self.reply = payload()
        self.after = snapshot()
        self.ok = True
        self.endpoint = self
        self.state = self

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": self.ok,
            "error": "native_activity_stage5_gold_red:no_normal_refresh"
            if not self.ok else None,
            "result": {
                "step": STEP, "accepted": True, "status": "available",
                "private_build": True, "read_only": True,
                "advertised": False, "backend_id": "native-headless",
                "activity_stage5_gold_cost": self.reply,
            } if self.ok else None,
        }

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot() if not self.sent else self.after)


class ActivityStage5GoldPrivateTransportTest(unittest.TestCase):
    def test_serializes_exact_request_and_copies_named_values(self) -> None:
        driver = Driver()
        result = query_activity_stage5_gold_private_v1(driver, expected_revision=5)
        request = driver.sent[0]
        self.assertEqual(set(request), {
            "type", "protocol_version", "request_id", "step",
            "expected_revision", "expected_date_raw",
            "expected_actor_character_id", "expected_activity_key",
            "expected_planning_stage",
        })
        self.assertEqual(request["step"], STEP)
        self.assertEqual(request["expected_revision"], 4)
        self.assertEqual(request["expected_date_raw"], 53219928)
        self.assertEqual(request["expected_actor_character_id"], 29829)
        self.assertEqual(request["expected_activity_key"], "activity_feast")
        self.assertEqual(request["expected_planning_stage"], 5)
        self.assertEqual(result["configured_cost"]["raw"], 10_000_000)
        self.assertEqual(result["resource_value"]["raw"], 15_000_000)
        self.assertEqual(result["normal_refresh_sequence"], 17)
        self.assertEqual(result["total_cost_state"], "unknown")
        self.assertIsNone(result["final_can_start"])
        self.assertEqual(result["queried_snapshot_id"], "native:4")
        driver.reply["configured_cost"]["raw"] = 0
        self.assertEqual(result["configured_cost"]["raw"], 10_000_000)

    def test_rejects_unmapped_or_invented_gold_and_final(self) -> None:
        for field, value in (
            ("normal_refresh_sequence", 0),
            ("final_can_start", True),
            ("raw_slot12_resource_mapping", "gold"),
            ("planning_stage", 2),
            ("snapshot_revision", 3),
        ):
            with self.subTest(field=field):
                changed = payload()
                changed[field] = value
                with self.assertRaises(BridgeUnavailableError):
                    parse_activity_stage5_gold_payload_v1(
                        changed, expected_native_revision=4,
                        expected_date_raw=53219928,
                        expected_actor_character_id=29829,
                    )
        for field, value in (
            ("scale", 1), ("source", "raw_slot12"),
            ("raw", True), ("raw", 2**63),
        ):
            with self.subTest(field=field, value=value):
                changed = payload()
                changed["configured_cost"][field] = value
                with self.assertRaises(BridgeUnavailableError):
                    parse_activity_stage5_gold_payload_v1(
                        changed, expected_native_revision=4,
                        expected_date_raw=53219928,
                        expected_actor_character_id=29829,
                    )

    def test_native_red_and_crossed_frame_remain_red(self) -> None:
        driver = Driver()
        driver.ok = False
        with self.assertRaisesRegex(BridgeUnavailableError, "no_normal_refresh"):
            query_activity_stage5_gold_private_v1(driver, expected_revision=5)
        driver = Driver()
        driver.after["native_revision"] = 5
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            query_activity_stage5_gold_private_v1(driver, expected_revision=5)

    def test_default_off_and_invalid_revision_do_not_send(self) -> None:
        driver = Driver()
        driver.allow_private_activity_stage5_gold_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_stage5_gold_private_v1(driver, expected_revision=5)
        self.assertEqual(driver.sent, [])
        driver.allow_private_activity_stage5_gold_query = True
        with self.assertRaises(ValueError):
            query_activity_stage5_gold_private_v1(driver, expected_revision=True)
        self.assertEqual(driver.sent, [])
        with self.assertRaises(ValueError):
            serialize_activity_stage5_gold_request_v1(
                "x", expected_native_revision=True,
                expected_date_raw=53219928,
                expected_actor_character_id=29829,
            )


if __name__ == "__main__":
    unittest.main()
