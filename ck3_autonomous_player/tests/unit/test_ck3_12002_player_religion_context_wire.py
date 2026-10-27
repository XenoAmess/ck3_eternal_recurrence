"""Consume actual new native religion-context output without querying a game."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from collections.abc import Callable
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.player_religion_context_private_transport import (
    normalize_player_religion_context_v1, query_player_religion_context_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError
from xar_autoplayer.bridge.g2_private_query_transport import read_private_g2_native_query_v1
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_context"


def load_fixture(relative: str) -> dict[str, object]:
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


def snapshot(*, revision: int, date_raw: int, actor: int) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}", "revision": revision + 1,
        "native_revision": revision, "date_raw": date_raw,
        "played_character": {"character_id": actor, "alive": True},
        "paused": True, "map_ready": True,
        "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        }},
    }


class MailboxPacketDriver:
    """Only correlate the generated request ID in an actual full native packet."""

    allow_private_player_religion_context_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_religion_context"]
        self.snapshot = snapshot(revision=result["snapshot_revision"],
                                 date_raw=result["date_raw"], actor=native["played_character_id"])
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


class PlayerReligion12002LibraryWireTest(unittest.TestCase):
    def test_five_actual_library_cases_preserve_full_ids_nulls_and_signed_resources(self) -> None:
        current = load_fixture("library/current-zero.json")
        before = snapshot(revision=40, date_raw=current["date_raw"], actor=current["played_character_id"])
        for case in ("current-zero", "signed-values", "legal-absent", "native-default", "faith-unavailable"):
            with self.subTest(case=case):
                native = load_fixture(f"library/{case}.json")
                actual = normalize_player_religion_context_v1(native, snapshot=deepcopy(before))
                self.assertEqual(actual, native)
                self.assertNotEqual(actual["capture_epoch"], before["native_revision"])
        zero = normalize_player_religion_context_v1(current, snapshot=before)
        self.assertEqual(zero["rite_id"], 0)
        self.assertGreater(zero["faith_id"], 0x7FFFFFFF)
        self.assertGreater(zero["religion_id"], 0x7FFFFFFF)
        self.assertNotEqual(zero["rite_id"], zero["faith_main_rite_id"])
        self.assertEqual(zero["faith_fervor_raw"], 0)
        self.assertEqual(zero["spiritual_fulfillment_raw"], 0)
        signed = load_fixture("library/signed-values.json")
        self.assertEqual(signed["faith_fervor_raw"], -123456)
        absent = load_fixture("library/legal-absent.json")
        self.assertTrue(absent["available"])
        self.assertIsNone(absent["rite_id"])
        self.assertIsNotNone(absent["spiritual_fulfillment_raw"])
        failed = load_fixture("library/faith-unavailable.json")
        self.assertFalse(failed["available"])
        self.assertEqual(failed["unavailable_reason"], "faith_unavailable")
        self.assertIsNone(failed["spiritual_fulfillment_raw"])


class PlayerReligion12002MailboxWireTest(unittest.TestCase):
    def test_six_actual_mailbox_packets_reach_the_existing_g2_query_transport(self) -> None:
        outputs = {}
        for case in ("current-zero", "signed-values", "native-default", "legal-absent",
                     "faith-unavailable", "fervor-unavailable"):
            with self.subTest(case=case):
                packet = load_fixture(f"mailbox/{case}.json")
                result = packet["result"]
                native = result["player_religion_context"]
                driver = MailboxPacketDriver(packet)
                actual = query_player_religion_context_private_v1(
                    driver, expected_revision=driver.snapshot["revision"],
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], result["status"])
                self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
                self.assertEqual(actual["query_date_raw"], result["date_raw"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-player-religion-context-v1")
                self.assertEqual(request["protocol_version"], 1)
                self.assertEqual(request["expected_revision"], result["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
                self.assertNotIn("character_id", request)
                outputs[case] = actual
        zero = outputs["current-zero"]
        self.assertEqual(zero["rite_id"], 0)
        self.assertGreater(zero["faith_id"], 0x7FFFFFFF)
        self.assertGreater(zero["religion_id"], 0x7FFFFFFF)
        self.assertEqual(zero["faith_key"], 'faith"信')
        self.assertEqual(zero["faith_fervor_raw"], 0)
        self.assertEqual(zero["spiritual_fulfillment_raw"], 0)
        self.assertEqual(outputs["signed-values"]["faith_fervor_raw"], -123456)
        self.assertTrue(outputs["legal-absent"]["available"])
        self.assertIsNone(outputs["legal-absent"]["faith_id"])
        for case, reason in (("faith-unavailable", "faith_unavailable"),
                             ("fervor-unavailable", "fervor_unavailable")):
            self.assertFalse(outputs[case]["available"])
            self.assertEqual(outputs[case]["status"], "unavailable")
            self.assertEqual(outputs[case]["unavailable_reason"], reason)
            self.assertIsNone(outputs[case]["faith_fervor_raw"])

    def test_private_query_is_disabled_before_sending_a_packet(self) -> None:
        driver = MailboxPacketDriver(load_fixture("mailbox/current-zero.json"))
        driver.allow_private_player_religion_context_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_context_private_v1(driver, expected_revision=driver.snapshot["revision"])
        self.assertEqual(driver.sent, [])


def packet_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Fixture JSON object required")
    return {key: item for key, item in value.items() if isinstance(key, str)}


class PublicationRaceDriver(MailboxPacketDriver):
    """Real protocol state/condition, actual query transport, fixture-owned wire.

    Native world changes are fixture counterfactuals, not a live-game claim.
    No callback or gameplay command is submitted by this backend.
    """

    def __init__(self, mode: str = "success") -> None:
        from xar_autoplayer.bridge.native_driver import NativeProtocolState
        super().__init__(load_fixture("mailbox/current-zero.json"))
        self.mode = mode
        self.protocol = NativeProtocolState("fixture:religion-publication-race")
        self.protocol.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1234,
            "connection_generation": 1, "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": CK3_12002.game_version,
            "expected_ck3_sha256": CK3_12002.executable_sha256,
        })
        self.mutate: Callable[[dict[str, object]], None] | None = None
        self.waited: list[tuple[int, float]] = []
        self.failed_response: dict[str, object] = {}
        for revision in range(1, 11):
            self.protocol.ingest(self.publication(revision))

    def publication(self, revision: int) -> dict[str, object]:
        from test_native_bridge_driver import _snapshot
        native = packet_object(packet_object(self.frame["result"])["player_religion_context"])
        date, actor = native["date_raw"], native["played_character_id"]
        if type(date) is not int or type(actor) is not int:
            raise ValueError("Fixture date/actor integers required")
        return _snapshot(
            revision, date_raw=date,
            played_character={"character_id": actor, "alive": True},
            played_character_piety={"raw": 600000000 if revision == 10 else 550000000, "scale": 100000},
        )

    def take_snapshot(self) -> dict[str, object]:
        current = self.protocol.semantic_snapshot()
        current["episode_projection"] = "native_campaign"
        current["managed_campaign_run_binding"] = {
            "run_id": "fixture-religion-run", "state_dir": "fixture-state",
            "bridge_pipe": "fixture:religion-publication-race", "host_path": "fixture-host",
            "frozen_argv_sha256": "a" * 64,
        }
        if current["native_revision"] == 11 and self.mutate is not None:
            self.mutate(current)
        return current

    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object]:
        if len(self.sent) == 1 or self.mode == "second-red":
            response: dict[str, object] = {
                "type": "command_result", "protocol_version": 1, "request_id": request_id,
                "ok": False, "error": "player_religion_published_frame_changed",
            }
            if self.mode == "unknown-error": response["error"] = "player_religion_native_capture_exception"
            if self.mode == "wrong-request": response["request_id"] = "different-request"
            if self.mode == "wrong-protocol": response["protocol_version"] = True
            if not self.failed_response: self.failed_response = deepcopy(response)
            self.protocol.ingest(response)
            received = self.protocol.wait_for_command_result(request_id, timeout_seconds)
            return received if received is not None else {}
        response = deepcopy(self.frame)
        response["request_id"] = request_id
        result = packet_object(response["result"])
        result["snapshot_revision"] = 11
        response["result"] = result
        self.protocol.ingest(response)
        received = self.protocol.wait_for_command_result(request_id, timeout_seconds)
        return received if received is not None else {}

    def wait_for_change(self, after_revision: int, *, timeout_seconds: float) -> dict[str, object]:
        self.waited.append((after_revision, timeout_seconds))
        if self.mode != "no-publication":
            # Use the actual state_snapshot consumer and actual condition, not a
            # mirror of the consistency predicate or a fabricated return frame.
            self.protocol.ingest(self.publication(11))
        self.protocol.wait_for_public_change(after_revision, timeout_seconds)
        return self.take_snapshot()


class PlayerReligionPublicationConsistencyTest(unittest.TestCase):
    def test_exact_rejected_read_reacquires_a_real_new_publication_once(self) -> None:
        driver = PublicationRaceDriver()
        self.assertEqual(driver.take_snapshot()["revision"], 11)
        result = query_player_religion_context_private_v1(driver, expected_revision=11)
        self.assertEqual(result["queried_revision"], 12)
        self.assertEqual(result["queried_native_revision"], 11)
        trace = packet_object(result["read_consistency_reacquisition"])
        self.assertEqual(trace["original_expected_revision"], 11)
        self.assertEqual(trace["initial_native_revision"], 10)
        self.assertEqual(trace["failed_response"], driver.failed_response)
        self.assertEqual(trace["failed_request_id"], driver.sent[0]["request_id"])
        self.assertEqual(trace["reissued_request_id"], driver.sent[1]["request_id"])
        self.assertNotEqual(trace["failed_request_id"], trace["reissued_request_id"])
        self.assertEqual(json.loads(json.dumps(trace)), trace)
        self.assertEqual([x["expected_revision"] for x in driver.sent], [10, 11])
        self.assertEqual({x["step"] for x in driver.sent}, {"query-player-religion-context-v1"})

    def test_no_publication_unknown_errors_and_second_red_do_not_loop(self) -> None:
        for mode, sends in (("no-publication", 1), ("unknown-error", 1),
                            ("wrong-request", 1), ("wrong-protocol", 1), ("second-red", 2)):
            with self.subTest(mode=mode):
                driver = PublicationRaceDriver(mode)
                with self.assertRaises(BridgeUnavailableError):
                    query_player_religion_context_private_v1(driver, expected_revision=11, timeout_seconds=.01)
                self.assertEqual(len(driver.sent), sends)

    def test_identity_date_pause_event_pending_and_exact_revision_guards_survive(self) -> None:
        changes: list[tuple[str, object]] = [
            ("date_raw", 1), ("paused", False), ("map_ready", False),
            ("native_revision", True), ("native_revision", 11.0),
            ("revision", True), ("revision", 12.0),
            ("played_character", {"character_id": 999, "alive": True}),
            ("active_event", {"event_instance_id": 1}),
            ("pending_character_interaction", {"id": 1}),
            ("managed_campaign_run_binding", None),
        ]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                driver = PublicationRaceDriver()
                def mutate(current: dict[str, object]) -> None:
                    current[field] = value
                driver.mutate = mutate
                with self.assertRaises(BridgeUnavailableError):
                    query_player_religion_context_private_v1(driver, expected_revision=11)
                self.assertEqual(len(driver.sent), 1)

    def test_other_steps_and_stale_initial_input_never_gain_reacquisition(self) -> None:
        driver = PublicationRaceDriver()
        with self.assertRaises(BridgeUnavailableError):
            read_private_g2_native_query_v1(driver, permission="allow_private_player_religion_context_query",
                step="query-current-timeline-blocker-context-v1", expected_revision=11)
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.waited, [])
        driver = PublicationRaceDriver()
        with self.assertRaises(BridgeUnavailableError):
            query_player_religion_context_private_v1(driver, expected_revision=10)
        self.assertEqual(driver.sent, [])

    def test_missing_snapshot_and_pid_generation_build_drift_reject_before_second_send(self) -> None:
        changes: list[tuple[str, object]] = [
            ("pid", 9999), ("pid", True), ("pid", 1234.0),
            ("connection_generation", 2), ("connection_generation", True),
            ("connection_generation", 1.0), ("expected_ck3_sha256", "f" * 64),
        ]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                driver = PublicationRaceDriver()
                def mutate(current: dict[str, object]) -> None:
                    diagnostics = packet_object(current["diagnostics"])
                    hello = packet_object(diagnostics["hello"])
                    hello[field] = value
                    diagnostics["hello"] = hello
                    current["diagnostics"] = diagnostics
                driver.mutate = mutate
                with self.assertRaises(BridgeUnavailableError):
                    query_player_religion_context_private_v1(driver, expected_revision=11)
                self.assertEqual(len(driver.sent), 1)
        driver = PublicationRaceDriver()
        def remove_snapshot(current: dict[str, object]) -> None:
            current.pop("snapshot_id")
        driver.mutate = remove_snapshot
        with self.assertRaises(BridgeUnavailableError):
            query_player_religion_context_private_v1(driver, expected_revision=11)
        self.assertEqual(len(driver.sent), 1)

    def test_original_total_deadline_cannot_be_reset_by_frame_reacquisition(self) -> None:
        driver = PublicationRaceDriver()
        stamps = iter((0.0, 2.0))
        def monotonic() -> float:
            return next(stamps)
        with patch("xar_autoplayer.bridge.g2_private_query_transport.time", new=SimpleNamespace(monotonic=monotonic)):
            with self.assertRaisesRegex(BridgeUnavailableError, "original deadline expired"):
                query_player_religion_context_private_v1(driver, expected_revision=11, timeout_seconds=1.0)
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.waited, [])


if __name__ == "__main__":
    unittest.main()
