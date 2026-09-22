from __future__ import annotations

import copy
from types import SimpleNamespace
import unittest

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_minor_religious_war_defenders_private_v1,
)
from xar_autoplayer.bridge.minor_religious_war_defenders_private_transport import (
    STEP_PREFIX,
    query_minor_religious_war_defenders_private_v1,
)


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native-frame-49",
        "revision": 14,
        "native_revision": 49,
        "date_raw": 53_144_328,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 29_829, "alive": True},
        "declarable_wars": [],
        "active_wars": [],
    }


def _payload() -> dict[str, object]:
    return {
        "status": "available",
        "native_revision": 49,
        "date_raw": 53_144_328,
        "declaration": {
            "target_character_id": 31_549,
            "casus_belli_index": 7,
            "casus_belli_key": "minor_religious_war",
            "configuration_index": 0,
            "claimant_character_id": 29_829,
            "target_title_ids": [1234],
            "defender_faith_can_join_source": True,
        },
        "actor_character_id": 29_829,
        "primary_defender_character_id": 31_549,
        "actor_power_base_raw": 5_000_000,
        "actor_power_total_raw": 6_000_000,
        "primary_defender_power_base_raw": 900_000,
        "primary_defender_power_total_raw": 2_000_000,
        "prospective_joiner_base_power_raw": 3_750_000,
        "primary_plus_joiner_base_power_raw": 4_650_000,
        "primary_total_plus_joiner_base_power_raw": 5_750_000,
        "power_scale": 100_000,
        "prospective_joiners": [
            {"character_id": 16_777_219, "base_power_raw": 1_250_000},
            {"character_id": 33_554_436, "base_power_raw": 2_500_000},
        ],
    }


class _Endpoint:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, frame: dict[str, object]) -> None:
        self.sent.append(copy.deepcopy(frame))


class _State:
    def __init__(self, endpoint: _Endpoint, payload: dict[str, object]) -> None:
        self.endpoint = endpoint
        self.payload = payload

    def wait_for_command_result(
        self, request_id: str, timeout_seconds: float
    ) -> dict[str, object]:
        assert timeout_seconds > 0
        request = self.endpoint.sent[-1]
        assert request["request_id"] == request_id
        return {
            "type": "command_result",
            "protocol_version": 1,
            "request_id": request_id,
            "ok": True,
            "result": {
                "step": request["step"],
                "accepted": True,
                "status": "available",
                "private_build": True,
                "read_only": True,
                "advertised": False,
                "backend_id": "native-headless",
                "minor_religious_war_defenders": copy.deepcopy(self.payload),
            },
        }


class _Driver:
    def __init__(self, payload: dict[str, object], *, enabled: bool = True) -> None:
        self.allow_private_minor_religious_war_defenders_query = enabled
        self.endpoint = _Endpoint()
        self.state = _State(self.endpoint, payload)
        self.snapshot = _snapshot()

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)


class MinorReligiousWarDefendersPrivateTransportTest(unittest.TestCase):
    def test_reads_full_generation_ids_and_same_frame_power(self) -> None:
        driver = _Driver(_payload())
        result = query_minor_religious_war_defenders_private_v1(
            driver,
            target_character_id=31_549,
            expected_revision=14,
            timeout_seconds=1,
        )
        self.assertEqual(
            driver.endpoint.sent[0]["step"], STEP_PREFIX + "31549"
        )
        self.assertEqual(driver.endpoint.sent[0]["expected_revision"], 49)
        readback = result["minor_religious_war_defenders"]
        self.assertEqual(
            [row["character_id"] for row in readback["prospective_joiners"]],
            [16_777_219, 33_554_436],
        )
        self.assertEqual(
            readback["primary_total_plus_joiner_base_power_raw"], 5_750_000
        )
        self.assertFalse(result["advertised"])

    def test_rejects_disabled_or_inconsistent_power(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            query_minor_religious_war_defenders_private_v1(
                _Driver(_payload(), enabled=False),
                target_character_id=31_549,
                expected_revision=14,
            )
        changed = _payload()
        changed["prospective_joiner_base_power_raw"] = 1
        with self.assertRaisesRegex(
            BridgeUnavailableError, "power totals disagree"
        ):
            query_minor_religious_war_defenders_private_v1(
                _Driver(changed),
                target_character_id=31_549,
                expected_revision=14,
            )

    def test_rejects_frame_drift(self) -> None:
        driver = _Driver(_payload())
        calls = 0

        def snapshot() -> dict[str, object]:
            nonlocal calls
            calls += 1
            value = _snapshot()
            if calls > 1:
                value["date_raw"] = 53_144_352
            return value

        driver.take_snapshot = snapshot  # type: ignore[method-assign]
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            query_minor_religious_war_defenders_private_v1(
                driver,
                target_character_id=31_549,
                expected_revision=14,
            )

    def test_mcp_private_seam_calls_driver_without_public_registration(self) -> None:
        calls: list[dict[str, int]] = []

        class Driver:
            def query_minor_religious_war_defenders_private_v1(
                self, *, target_character_id: int, expected_revision: int
            ) -> dict[str, object]:
                calls.append({"target": target_character_id,
                              "revision": expected_revision})
                return {"advertised": False}

        result = _ck3_query_minor_religious_war_defenders_private_v1(
            SimpleNamespace(driver=Driver()), 31_549, 14
        )
        self.assertEqual(calls, [{"target": 31_549, "revision": 14}])
        self.assertFalse(result["advertised"])


if __name__ == "__main__":
    unittest.main()
