"""Consume the real event-window CTest wire through registered MCP, without CK3.

This is an explicit CI entry point. Missing native output is an error, never a
skipped test. The existing event-window unittest module keeps its default path.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import unittest

from mcp import Client, ClientSession

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server


MARKER = "SAVED_CHARACTER_SCOPE_NATIVE_JSON="
WIRE_ENV = "XAR_EVENT_SAVED_SCOPE_NATIVE_WIRE"
PAYLOADS = ("0", "43", "16777258", "2147483649")


def object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Expected a string-keyed JSON object")
    return {key: item for key, item in value.items()}


def array_value(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Expected a JSON array")
    return list(value)


def integer_value(value: object) -> int:
    if type(value) is not int:
        raise ValueError("Expected an exact JSON integer")
    return value


@dataclass(frozen=True)
class NativePacket:
    splash: bool
    payload: str
    frame: dict[str, object]


def native_packets(path: Path) -> tuple[NativePacket, ...]:
    packets: list[NativePacket] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        prefix, separator, encoded = line.partition(MARKER)
        if not separator:
            continue
        if not re.fullmatch(r"(?:\d+: )?", prefix):
            raise ValueError("Unexpected CTest wire prefix")
        decoded: object = json.loads(encoded)
        envelope = object_value(decoded)
        if set(envelope) != {"splash", "payload", "frame"}:
            raise ValueError("Unexpected native fixture envelope fields")
        splash, payload = envelope["splash"], envelope["payload"]
        if type(splash) is not bool or not isinstance(payload, str) or payload not in PAYLOADS:
            raise ValueError("Unexpected native fixture case")
        packets.append(NativePacket(splash, payload, object_value(envelope["frame"])))
    expected = {(splash, payload) for splash in (False, True) for payload in PAYLOADS}
    if len(packets) != 8 or {(row.splash, row.payload) for row in packets} != expected:
        raise ValueError("Exactly eight real native fixture cases are required")
    return tuple(packets)


class NativeWireDriver:
    """Only the existing readonly query may consume an actual native frame."""

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = copy.deepcopy(frame)
        self.query_count = 0

    def take_snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "native-scope-fixture-snapshot",
            "revision": 9,
            "native_revision": integer_value(self.frame["snapshot_revision"]),
            "date_raw": integer_value(self.frame["date_raw"]),
            "paused": True,
            "backend_id": "native-headless",
            "active_event": {
                "instance_id": integer_value(self.frame["current_event_instance_id"]),
                "option_count": 3,
            },
        }

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY],
            "action_steps": [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP],
        }

    def execute_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        if step != QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP or expected_revision != 9:
            raise AssertionError("The native fixture driver only permits the bound readonly query")
        self.query_count += 1
        frame = copy.deepcopy(self.frame)
        readiness = object_value(frame["readiness"])
        mirrors = {key: frame[key] for key in (
            "schema", "schema_version", "date_raw", "current_event_instance_id",
            "window_match_count", "unavailable_reason", "event_definition_key",
            "calculated_event_id", "runtime_stats_ordinal", "root_scope", "saved_scopes",
            "options", "readiness", "provenance",
        )}
        return {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": frame["status"],
            "query_sequence": self.query_count,
            "snapshot_revision": integer_value(frame["snapshot_revision"]),
            "current_event_window_context": frame,
            "backend_id": "native-headless",
            "current_event_window_context_ready": readiness["option_presentation_ready"],
            "current_event_effect_indicators_ready": readiness["effect_indicators_ready"],
            "queried_snapshot_id": "native-scope-fixture-snapshot",
            "queried_revision": 9,
            "queried_native_revision": integer_value(frame["snapshot_revision"]),
            **mirrors,
        }


def run_native_consumer(path: Path) -> unittest.TestResult:
    packets = native_packets(path)

    class NativeSavedScopeTests(unittest.IsolatedAsyncioTestCase):
        async def test_all_native_packets_through_registered_mcp(self) -> None:
            for packet in packets:
                with self.subTest(splash=packet.splash, synthetic_payload=packet.payload):
                    driver = NativeWireDriver(packet.frame)
                    async with Client(create_server(driver)) as client:
                        self.assertIsInstance(client.session, ClientSession)
                        reply = await client.session.call_tool(
                            "ck3_query_current_event_window_context_v1",
                            {"event_instance_id": packet.frame["current_event_instance_id"],
                             "expected_revision": 9},
                        )
                    self.assertFalse(reply.is_error)
                    self.assertEqual(driver.query_count, 1)
                    result = object_value(reply.structured_content)
                    self.assertEqual(result["status"], "available")
                    self.assertEqual(result["root_scope"], packet.frame["root_scope"])
                    self.assertEqual(result["saved_scopes"], packet.frame["saved_scopes"])
                    self.assertEqual(result["options"], packet.frame["options"])
                    root = object_value(result["root_scope"])
                    self.assertEqual(object_value(root["typed_identity"])["character_id"], 42)
                    saved = array_value(result["saved_scopes"])
                    self.assertEqual(len(saved), 2)
                    first = object_value(object_value(saved[0])["scope"])
                    self.assertEqual(first["typed_identity"], {
                        "status": "unavailable", "reason": "character_scope_identity_unavailable"})
                    options = [object_value(row) for row in array_value(result["options"])]
                    self.assertEqual([row["rendered_index"] for row in options], [0, 1])
                    self.assertEqual([row["native_option_index"] for row in options], [1, 2])
                    self.assertEqual([row["shown"] for row in options], [True, True])
                    self.assertEqual([row["enabled"] for row in options], [True, False])
                    roundtrip: object = json.loads(json.dumps(result))
                    self.assertEqual(object_value(roundtrip), result)

        async def test_malformed_scopes_are_rejected_by_registered_consumer(self) -> None:
            mutations: list[tuple[str, dict[str, object]]] = []
            root_unavailable = copy.deepcopy(packets[0].frame)
            root_scope = object_value(root_unavailable["root_scope"])
            root_scope["typed_identity"] = {
                "status": "unavailable", "reason": "character_scope_identity_unavailable"}
            root_unavailable["root_scope"] = root_scope
            mutations.append(("required root unavailable", root_unavailable))
            for label, identity in (
                ("unavailable with fabricated ID", {
                    "status": "unavailable", "reason": "character_scope_identity_unavailable",
                    "character_id": 42}),
                ("unknown unavailable reason", {"status": "unavailable", "reason": "unknown"}),
            ):
                frame = copy.deepcopy(packets[0].frame)
                saved = array_value(frame["saved_scopes"])
                row = object_value(saved[0])
                scope = object_value(row["scope"])
                scope["typed_identity"] = identity
                row["scope"] = scope
                saved[0] = row
                frame["saved_scopes"] = saved
                mutations.append((label, frame))
            for label, frame in mutations:
                with self.subTest(label=label):
                    with self.assertRaises(ValueError):
                        normalize_current_event_window_context_v1(
                            frame,
                            expected_event_instance_id=integer_value(frame["current_event_instance_id"]),
                            expected_date_raw=integer_value(frame["date_raw"]),
                            expected_snapshot_revision=integer_value(frame["snapshot_revision"]),
                        )
                    driver = NativeWireDriver(frame)
                    async with Client(create_server(driver)) as client:
                        self.assertIsInstance(client.session, ClientSession)
                        reply = await client.session.call_tool(
                            "ck3_query_current_event_window_context_v1",
                            {"event_instance_id": frame["current_event_instance_id"],
                             "expected_revision": 9},
                        )
                    self.assertTrue(reply.is_error)
                    self.assertEqual(driver.query_count, 1)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeSavedScopeTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun != 2 or result.skipped:
        raise RuntimeError("Both native consumer tests must actually run, with zero skips")
    return result


def main() -> int:
    configured = os.environ.get(WIRE_ENV)
    if not configured:
        raise ValueError(f"{WIRE_ENV} is required; native producer output cannot be skipped")
    return 0 if run_native_consumer(Path(configured)).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
