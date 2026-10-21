"""Offline synthetic and actual-host-producer checks for the Native32 contract."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import unittest

from observer_journal_v1 import (
    AllNativeObservedHistoryV1, ExpectedGameV1, RequestedIdsV1, SCHEMA, STEP,
    encode_result_v1, encode_selection_v1, execute_pairs_v1, parse_journal_v1,
    parse_selection_v1, require_runtime_qualification_v1, result_payload_v1,
)

EXPECTED = ExpectedGameV1("fixture-only-no-runtime-admission", 123, 456)
HIGH = (1 << 53) + 19


def event_v1(kind: int, seq: int, *, missing: bool = False,
        retired: bool = False) -> dict[str, object]:
    absent = missing or retired
    return {"seq": str(seq), "qpc": str(100 + seq), "thread": 7, "kind": kind,
        "role": 0 if absent else 1, "invocation": "50",
        "identity_epoch": "0" if absent else "1", "connection": "0" if absent else "2",
        "attributed": 0 if absent else 1, "request_id": "" if absent else "old-request",
        "desired_paused": 0, "token": {"pointer": "0" if absent else str(HIGH),
            "incarnation": "0" if absent else "5"},
        "parent": {"pointer": "0", "incarnation": "0"}, "caller_rva": "9", "aux": "0",
        "identity_qualified": 0 if absent else 1, "queue_accepted": 0, "payload_valid": 1,
        "player_bits": 91, "command_paused": 1, "native_sequence": 501,
        "scalar_valid": 1, "game": str(HIGH + 512), "jomini": str(HIGH + 1024),
        "date_bits": 53274624, "paused": 0, "observed_object": str(HIGH),
        "observed_secondary": str(HIGH + 0x18),
        "retired_at_sequence": "1" if retired else "0",
        "lookup_outcome": "retired_same_address" if retired else "missing" if missing else "active"}


def frame_v1(events: list[dict[str, object]]) -> dict[str, object]:
    newest = int(str(events[-1]["seq"])) if events else 0
    return {"type": "command_result", "protocol_version": 1, "request_id": "journal-fixture",
        "ok": True, "result": {"step": STEP, "accepted": True, "status": "passive_observation_only",
        "drain_fence": False, "observer_schema": SCHEMA,
        "lifetime_coverage": "observed_clone_and_primary_delete_slots_only",
        "scalar_samples_are_snapshots": False, "query_is_tail": True,
        "retirement_diagnostics": "bounded_recent_addresses_only",
        "payload_samples": "entry_observation_not_return_readback",
        "qpc_frequency": "1000", "snapshot_qpc": "9999", "process_id": 123,
        "process_birth": "456", "image_base": "5368709120", "attached": 1,
        "readable": 1, "newest": str(newest), "oldest_retained": "1",
        "returned_count": len(events), "first_returned": str(newest - len(events) + 1),
        "coverage_gaps": 64 if any(e.get("lookup_outcome") != "active" for e in events) else 0,
        "lost": "0", "live_registry": 0, "events": events}}


def result_row_v1(frame: dict[str, object]) -> dict[str, object]:
    raw = frame["result"]
    if not isinstance(raw, dict):
        raise ValueError("fixture result object missing")
    result: dict[str, object] = {}
    for key, value in raw.items():
        if type(key) is not str:
            raise ValueError("fixture text key required")
        result[key] = value
    return result


def parse_frame_v1(frame: dict[str, object]) -> object:
    return parse_journal_v1(frame, request_id="journal-fixture", expected=EXPECTED)


def verify_host_fixture_v1(executable: Path) -> int:
    """Execute only an explicitly supplied host fixture; never discover a Game."""
    done = subprocess.run([str(executable.resolve(strict=True))], check=False,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if done.returncode:
        raise ValueError("host fixture failed: " + done.stderr.decode("utf-8", errors="replace"))
    lines = done.stdout.decode("utf-8").splitlines()
    if len(lines) != 3:
        raise ValueError("three actual C++ producer frames required")
    miss_count = retired_count = 0
    for line, request_id in zip(lines,
            ("retired-fixture", "missing-fixture", "journal-fixture"), strict=True):
        raw: object = json.loads(line)
        journal = parse_journal_v1(raw, request_id=request_id, expected=EXPECTED)
        for event in journal.events:
            if event.lookup_outcome in ("missing", "retired_same_address"):
                if event.identity_qualified or event.token.pointer or event.attributed:
                    raise ValueError("actual C++ address-only observation grants identity")
            if event.lookup_outcome == "missing" and event.kind.value == 8:
                if event.native_sequence != 501 or event.player_bits != 91 or not event.command_paused:
                    raise ValueError("actual C++ Return lost observed entry payload")
                miss_count += 1
            if event.lookup_outcome == "retired_same_address":
                retired_count += 1
        # Any pairs here remain historical observer pairs, never current request credit.
        summary = result_payload_v1(journal, AllNativeObservedHistoryV1(), EXPECTED)
        if summary["current_failed_request_completion_proven"] is not False:
            raise ValueError("completion proof was widened")
    if not miss_count or not retired_count:
        raise ValueError("actual C++ producer did not cover both lookup failures")
    return len(lines)


class ContractTests(unittest.TestCase):
    def test_empty_ids_and_explicit_history_differ(self) -> None:
        journal = parse_journal_v1(frame_v1([event_v1(7, 1), event_v1(8, 2)]),
            request_id="journal-fixture", expected=EXPECTED)
        self.assertEqual(execute_pairs_v1(journal, RequestedIdsV1(())), ())
        self.assertEqual(len(execute_pairs_v1(journal, AllNativeObservedHistoryV1())), 1)
        self.assertEqual(len(execute_pairs_v1(journal, RequestedIdsV1(("old-request",)))), 1)
        self.assertEqual(execute_pairs_v1(journal, RequestedIdsV1(("different",))), ())

    def test_missing_and_retired_never_pair(self) -> None:
        for kwargs in ({"missing": True}, {"retired": True}):
            journal = parse_journal_v1(frame_v1([event_v1(7, 2, **kwargs), event_v1(8, 3, **kwargs)]),
                request_id="journal-fixture", expected=EXPECTED)
            self.assertEqual(execute_pairs_v1(journal, AllNativeObservedHistoryV1()), ())
            self.assertEqual(journal.events[-1].native_sequence, 501)

    def test_forged_identity_on_miss_rejected(self) -> None:
        for field, bad in (("identity_qualified", 1), ("attributed", 1),
                ("connection", "2"), ("role", 1), ("identity_epoch", "1"),
                ("request_id", "old-request"), ("parent", {"pointer": "5", "incarnation": "7"}),
                ("token", {"pointer": "5", "incarnation": "7"})):
            with self.subTest(field=field):
                event = event_v1(7, 2, retired=True)
                event[field] = bad
                with self.assertRaises(ValueError):
                    parse_frame_v1(frame_v1([event]))

    def test_u64_text_roundtrip_and_bad_types(self) -> None:
        frame = frame_v1([event_v1(7, 1), event_v1(8, 2)])
        journal = parse_journal_v1(json.loads(json.dumps(frame)),
            request_id="journal-fixture", expected=EXPECTED)
        payload = result_payload_v1(journal, AllNativeObservedHistoryV1(), EXPECTED)
        decoded: object = json.loads(encode_result_v1(payload))
        self.assertEqual(decoded, payload)
        self.assertEqual(payload["native_observed_execute_pairs"][0]["pointer"], str(HIGH))
        for bad in (True, 1.0, 1, "01", "-1", "+1", str(1 << 64), None):
            event = event_v1(7, 1)
            event["observed_object"] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                parse_frame_v1(frame_v1([event]))

    def test_exact_fields_and_bits(self) -> None:
        for missing in ("observed_object", "observed_secondary", "lookup_outcome", "identity_qualified"):
            event = event_v1(7, 1)
            del event[missing]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                parse_frame_v1(frame_v1([event]))
        for bad in (True, 1.0, None):
            event = event_v1(7, 1)
            event["native_sequence"] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                parse_frame_v1(frame_v1([event]))
        event = event_v1(7, 1)
        event["qualified"] = 1
        with self.assertRaises(ValueError):
            parse_frame_v1(frame_v1([event]))

    def test_unqualified_and_payload_mismatch_cannot_pair(self) -> None:
        for field, bad in (("identity_qualified", 0), ("payload_valid", 0),
                ("native_sequence", 502), ("player_bits", 92),
                ("invocation", "51"), ("identity_epoch", "2"), ("connection", "3")):
            events = [event_v1(7, 1), event_v1(8, 2)]
            events[1][field] = bad
            journal = parse_journal_v1(frame_v1(events), request_id="journal-fixture", expected=EXPECTED)
            self.assertEqual(execute_pairs_v1(journal, AllNativeObservedHistoryV1()), ())

    def test_selection_json_roundtrip(self) -> None:
        for selection in (RequestedIdsV1(()), RequestedIdsV1(("old-request",)),
                AllNativeObservedHistoryV1()):
            self.assertEqual(parse_selection_v1(json.loads(json.dumps(encode_selection_v1(selection)))), selection)
        for bad in ({}, {"mode": "all-native-observed-history", "request_ids": []},
                {"mode": "request-ids", "request_ids": None},
                {"mode": "request-ids", "request_ids": [True]},
                {"mode": "request-ids", "request_ids": ["x", "x"]}):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                parse_selection_v1(bad)

    def test_schema_identity_and_false_proofs(self) -> None:
        original = frame_v1([])
        for field, bad in (("observer_schema", "xar.ck3.time-command-observer31/v1"),
                ("process_birth", "457"), ("process_id", True), ("drain_fence", True)):
            frame = copy.deepcopy(original)
            row = result_row_v1(frame)
            row[field] = bad
            frame["result"] = row
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_frame_v1(frame)
        journal = parse_journal_v1(original, request_id="journal-fixture", expected=EXPECTED)
        payload = result_payload_v1(journal, AllNativeObservedHistoryV1(), EXPECTED)
        for field in ("drain_fence", "automatic_recovery_allowed",
                "current_failed_request_completion_proven", "protocol_connection_binding_verified",
                "absence_is_nonexecution_proof", "runtime_admission_granted"):
            self.assertIs(payload.get(field), False)
        with self.assertRaises(ValueError):
            require_runtime_qualification_v1()


if __name__ == "__main__":
    unittest.main()
