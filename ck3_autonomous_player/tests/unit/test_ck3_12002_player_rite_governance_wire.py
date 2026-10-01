"""Actual full native Rite governance envelopes through the Python query leaf."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.player_rite_governance_private_transport import (
    normalize_player_rite_governance_v1, query_player_rite_governance_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_rite_governance"


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class MailboxPacketDriver:
    """Keep the actual packet intact except its request correlation nonce."""

    allow_private_player_rite_governance_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_rite_governance"]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
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
        reply = deepcopy(self.frame)
        reply["request_id"] = request_id
        return reply


class PlayerRiteGovernance12002WireTests(unittest.TestCase):
    def observed(self, case: str) -> dict[str, object]:
        packet = actual_packet(case)
        result = packet["result"]
        native = result["player_rite_governance"]
        driver = MailboxPacketDriver(packet)
        actual = query_player_rite_governance_private_v1(
            driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
        )
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertEqual(actual["status"], result["status"])
        self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
        self.assertEqual(actual["queried_revision"], driver.snapshot["revision"])
        self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
        self.assertEqual(actual["query_date_raw"], result["date_raw"])
        self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
        self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
        self.assertEqual(packet["request_id"], 'governance"worker-fixture')
        self.assertEqual(len(driver.sent), 1)
        request = driver.sent[0]
        self.assertEqual(request["step"], "query-player-rite-governance-v1")
        self.assertEqual(request["expected_revision"], result["snapshot_revision"])
        self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
        self.assertNotIn("character_id", request)
        return actual

    def test_actual_distinct_references_and_zero_native_cached_counts(self) -> None:
        actual = self.observed("distinct-zero")
        self.assertIs(actual["all_components_available"], True)
        self.assertEqual(actual["observed_components"], 3)
        state, heads, counts = actual["state_rite"], actual["heads"], actual["organization"]
        self.assertEqual(state["actor_rite_id"], 0)
        self.assertGreater(state["actor_faith_id"], 0x7FFFFFFF)
        self.assertNotEqual(state["actor_rite_id"], state["actor_faith_main_rite_id"])
        self.assertNotEqual(state["player_primary_title"], state["realm_primary_title"])
        self.assertEqual(len({heads[key] for key in (
            "actor_rite_head_character_id", "faith_main_rite_head_character_id",
            "faith_religious_head_title_id", "faith_religious_head_holder_character_id",
        )}), 4)
        self.assertEqual((counts["rite_id"], counts["county_count"], counts["character_follower_count"]),
                         (0, 0, 0))
        source = actual_packet("distinct-zero")["result"]["player_rite_governance"]
        normalized = normalize_player_rite_governance_v1(
            source, snapshot=MailboxPacketDriver(actual_packet("distinct-zero")).snapshot,
        )
        source["state_rite"]["player_primary_title"]["title_id"] = None
        self.assertEqual(normalized["state_rite"]["player_primary_title"]["title_id"], 2382364673)

    def test_actual_legal_absence_remains_available_and_null(self) -> None:
        actual = self.observed("legal-absent")
        self.assertIs(actual["available"], True)
        self.assertEqual(actual["observed_components"], 3)
        self.assertIsNone(actual["state_rite"]["actor_rite_id"])
        realm = actual["state_rite"]["realm_primary_title"]
        self.assertIsNotNone(realm["title_id"])
        self.assertIsNone(realm["state_rite_id"])
        self.assertIsNone(realm["state_faith_id"])
        counts = actual["organization"]
        self.assertIs(counts["available"], True)
        for key in ("rite_id", "county_count", "character_follower_count"):
            self.assertIsNone(counts[key])

    def test_actual_head_getter_failure_keeps_observed_state_and_counts(self) -> None:
        actual = self.observed("heads-unavailable")
        self.assertIs(actual["available"], True)
        self.assertIs(actual["frame_available"], True)
        self.assertEqual(actual["observed_components"], 2)
        self.assertIs(actual["all_components_available"], False)
        self.assertIs(actual["heads"]["available"], False)
        self.assertEqual(actual["heads"]["unavailable_reason"], "rite_head_unavailable")
        self.assertEqual(actual["heads"]["played_character_id"], -1)
        self.assertEqual(actual["heads"]["date_raw"], 0)
        self.assertIs(actual["state_rite"]["available"], True)
        self.assertEqual(actual["state_rite"]["actor_rite_id"], 0)
        self.assertIs(actual["organization"]["available"], True)
        self.assertEqual(actual["organization"]["county_count"], 0)

    def test_actual_all_components_unavailable_retains_the_observed_player_frame(self) -> None:
        actual = self.observed("components-unavailable")
        self.assertEqual(actual["status"], "unavailable")
        self.assertIs(actual["available"], False)
        self.assertIs(actual["frame_available"], True)
        self.assertEqual(actual["observed_components"], 0)
        self.assertEqual(actual["unavailable_reason"], "components_unavailable")
        self.assertEqual(actual["played_character_id"], 50331652)
        self.assertEqual(actual["date_raw"], 53175816)
        self.assertEqual(actual["state_rite"]["played_character_id"], 0xFFFFFFFF)
        for key in ("state_rite", "heads", "organization"):
            self.assertIs(actual[key]["available"], False)
            self.assertEqual(actual[key]["unavailable_reason"], "bindings_unavailable")

    def test_private_permission_disabled_sends_no_query(self) -> None:
        driver = MailboxPacketDriver(actual_packet("distinct-zero"))
        driver.allow_private_player_rite_governance_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_rite_governance_private_v1(driver, expected_revision=driver.snapshot["revision"])
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
