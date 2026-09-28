"""No-launch check for the private full-cost realm-law paused route."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.realm_law_paused_private_transport import (
    SCHEMA, SLOTS, STEP, query_realm_law_final_terms_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
        "date_raw": 53219928, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
    }


def value() -> dict[str, object]:
    return {
        "schema": SCHEMA, "snapshot_revision": 4,
        "date_raw": 53219928, "actor_character_id": 29829,
        "cost_scale": 100000, "cost_slots": list(SLOTS),
        "groups": [
            {"group_key": "crown_authority", "active_law_key": "crown_authority_1",
             "candidates": [
                 {"law_key": "crown_authority_1", "active": True,
                  "final_status": "already_active", "final_can_enact": False,
                  "native_reason": "", "cost_raw": [0] * 10},
                 {"law_key": "crown_authority_2", "active": False,
                  "final_status": "can_enact", "final_can_enact": True,
                  "native_reason": "", "cost_raw": [0, 20000000] + [0] * 8},
             ]},
            {"group_key": "succession_order_laws", "active_law_key": None,
             "candidates": [
                 {"law_key": "single_heir_succession_law", "active": False,
                  "final_status": "engine_blocked", "final_can_enact": False,
                  "native_reason": "requires authority", "cost_raw": [0] * 10},
             ]},
        ],
    }


class Driver:
    allow_private_realm_law_paused_query = True

    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []
        self.reply = value()
        self.after = snapshot()
        self.endpoint = self
        self.state = self

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": STEP, "accepted": True, "status": "available",
                "private_build": True, "read_only": True,
                "advertised": False, "backend_id": "native-headless",
                "realm_law_final_terms": self.reply,
            },
        }

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot() if not self.sent else self.after)


class RealmLawPrivateTransportTest(unittest.TestCase):
    def test_full_ten_slot_current_frame_read_only(self) -> None:
        driver = Driver()
        result = query_realm_law_final_terms_private_v1(driver, expected_revision=5)
        self.assertEqual(result["groups"][0]["candidates"][1]["cost_raw"][1], 20000000)
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.sent[0]["step"], STEP)
        self.assertEqual(driver.sent[0]["expected_revision"], 4)

    def test_rejects_truncated_cost_and_crossed_frame(self) -> None:
        driver = Driver()
        driver.reply["groups"][0]["candidates"][1]["cost_raw"] = [0] * 6
        with self.assertRaises(BridgeUnavailableError):
            query_realm_law_final_terms_private_v1(driver, expected_revision=5)
        driver = Driver()
        driver.after["date_raw"] += 1
        with self.assertRaises(BridgeUnavailableError):
            query_realm_law_final_terms_private_v1(driver, expected_revision=5)

    def test_default_off_rejects_before_wire(self) -> None:
        driver = Driver()
        driver.allow_private_realm_law_paused_query = False
        with self.assertRaises(UnsupportedStepError):
            query_realm_law_final_terms_private_v1(driver, expected_revision=5)
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
