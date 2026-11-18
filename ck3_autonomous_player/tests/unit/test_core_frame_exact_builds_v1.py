"""Actual C++ Core payloads through protocol, Driver and registered MCP.

The fixture endpoint only rebinds the outer request_id to the Driver's actual
request. Prefix values and result fields come unchanged from the Q05 producer.
Metadata projections used to check the legacy branch are software cases only.
No test opens a pipe, starts CK3, or supplies a complete state_snapshot.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock
from mcp.server.mcpserver.exceptions import ToolError

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.core_frame_contract import (
    CORE_FRAME_V1_CAPABILITY, normalize_core_frame_v1, require_core_frame_hello_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.version_identity import CK3_12004, CK3_1210

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/core1210"


def producer_wire(kind: str) -> dict[str, object]:
    value: object = json.loads((FIXTURES / f"producer-{kind}.json").read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or set(value) != {"type", "protocol_version", "request_id", "ok", "result"}
            or value["type"] != "command_result" or value["protocol_version"] != 1
            or value["request_id"] != f"producer-{kind}" or value["ok"] is not True
            or not isinstance(value["result"], dict)):
        raise AssertionError("Expected the actual C++ whole Core command_result")
    return value


def hello1210() -> dict[str, object]:
    # Transport/build metadata only; no Core operands or gameplay state.
    return {"type": "hello", "protocol_version": 1, "pid": 1210, "connection_generation": 1,
        "capabilities": [CORE_FRAME_V1_CAPABILITY], "game_adapter_status": "ready",
        "game_adapter_id": "ck3-1.21.0-msvc-x64", "ck3_build_match": True,
        "expected_ck3_version": CK3_1210.game_version, "expected_ck3_sha256": CK3_1210.executable_sha256}


class ProducerEndpoint:
    def __init__(self, state: NativeProtocolState, wire: dict[str, object]) -> None:
        self.state = state
        self.wire = deepcopy(wire)
        self.requests: list[dict[str, object]] = []

    def send(self, request: dict[str, object]) -> None:
        if (self.requests or set(request) != {"type", "protocol_version", "request_id", "step", "expected_revision"}
                or request["type"] != "execute_step" or request["protocol_version"] != 1
                or request["step"] != "query-core-frame-v1" or type(request["expected_revision"]) is not int
                or request["expected_revision"] != 0):
            raise AssertionError("Only one standalone readonly Core request is allowed")
        self.requests.append(deepcopy(request))
        correlated = deepcopy(self.wire)
        correlated["request_id"] = request["request_id"]
        if correlated["result"] != self.wire["result"]:
            raise AssertionError("Original C++ Core operands changed")
        self.state.ingest(correlated)


def driver_for(wire: dict[str, object], hello: dict[str, object]) -> tuple[NativeHeadlessGameplayDriver, ProducerEndpoint]:
    driver = NativeHeadlessGameplayDriver.__new__(NativeHeadlessGameplayDriver)
    driver.state = NativeProtocolState(r"\\.\pipe\core_exact_build_software_fixture_only")
    driver.state.ingest(deepcopy(hello))
    driver._transport_error = Mock(return_value=None)
    driver._driver_state_lock = threading.RLock()
    driver._request_sequence = 0
    driver.command_timeout_seconds = 0.1
    endpoint = ProducerEndpoint(driver.state, wire)
    driver.endpoint = endpoint
    forbidden = Mock(side_effect=AssertionError("Core diagnostic must never obtain Full state"))
    driver.take_snapshot = forbidden
    driver.take_internal_semantic_snapshot = forbidden
    driver.capabilities = forbidden
    driver.state.semantic_snapshot = forbidden
    return driver, endpoint


class ExactCoreContract(unittest.TestCase):
    def test_actual_cpp_partial_and_unavailable_normalize_without_operand_changes(self) -> None:
        for kind in ("partial", "unavailable"):
            with self.subTest(kind=kind):
                result = producer_wire(kind)["result"]
                self.assertEqual(normalize_core_frame_v1(result, expected_build=CK3_1210), result)
                self.assertIs(result["complete_snapshot"], False)

    def test_actual_hello_requires_exact_florin_identity(self) -> None:
        self.assertEqual(require_core_frame_hello_v1(hello1210()), CK3_1210)
        for field, bad in (("expected_ck3_version", "1.20.0.4"),
                ("expected_ck3_sha256", CK3_12004.executable_sha256),
                ("game_adapter_id", "ck3-1.20.0.4-msvc-x64"), ("ck3_build_match", 1),
                ("game_adapter_status", "unsupported"), ("capabilities", []),
                ("capabilities", CORE_FRAME_V1_CAPABILITY), ("capabilities", [True])):
            with self.subTest(field=field, bad=bad):
                hello = hello1210(); hello[field] = bad
                with self.assertRaises(ValueError):
                    require_core_frame_hello_v1(hello)

    def test_cross_build_schema_adapter_backend_and_hello_are_rejected(self) -> None:
        result = producer_wire("partial")["result"]
        for field, bad in (("schema", "ck3_12004_core_frame_v1"),
                ("game_version", "1.20.0.4"), ("executable_sha256", CK3_12004.executable_sha256),
                ("adapter_id", "ck3-1.20.0.4-msvc-x64"),
                ("backend", "ck3-1.20.0.4-native-headless-main-thread")):
            with self.subTest(field=field):
                bad_result = deepcopy(result); bad_result[field] = bad
                with self.assertRaises(ValueError):
                    normalize_core_frame_v1(bad_result, expected_build=CK3_1210)
        with self.assertRaises(ValueError):
            normalize_core_frame_v1(result, expected_build=CK3_12004)

    def test_partial_boundary_and_exact_scalar_types_are_preserved(self) -> None:
        result = producer_wire("partial")["result"]
        for field, bad in (("complete_snapshot", True), ("status", "ready"),
                ("core_available", 1), ("application_main_observed", 1), ("date_raw", True),
                ("date_raw", 1.5), ("speed", False), ("speed", 6), ("paused", 1),
                ("map_ready", 1), ("has_played_character", 1), ("played_character_alive", 1),
                ("local_player_id", True), ("played_character_id", 2**31),
                ("played_character_id", -1), ("excluded_snapshot_families", [])):
            with self.subTest(field=field, bad=bad):
                bad_result = deepcopy(result); bad_result[field] = bad
                with self.assertRaises(ValueError):
                    normalize_core_frame_v1(bad_result)
        for changed in ({**result, "revision": 1}, {key: value for key, value in result.items() if key != "paused"}):
            with self.assertRaises(ValueError):
                normalize_core_frame_v1(changed)

    def test_unavailable_never_carries_invented_prefix(self) -> None:
        result = producer_wire("unavailable")["result"]
        for field in ("date_raw", "speed", "paused", "map_ready", "local_player_id",
                "has_played_character", "played_character_id", "played_character_alive"):
            bad_result = deepcopy(result); bad_result[field] = 0
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_core_frame_v1(bad_result)

    def test_legacy_branch_software_metadata_projection_is_unchanged(self) -> None:
        # Prefix operands remain the actual producer's. This is an explicit
        # software compatibility case, never a claimed old Native execution.
        result = deepcopy(producer_wire("partial")["result"])
        result.update(schema="ck3_12004_core_frame_v1", game_version=CK3_12004.game_version,
            executable_sha256=CK3_12004.executable_sha256, adapter_id="ck3-1.20.0.4-msvc-x64",
            backend="ck3-1.20.0.4-native-headless-main-thread")
        legacy_hello = {"expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256, "game_adapter_status": "ready",
            "capabilities": [CORE_FRAME_V1_CAPABILITY]}
        self.assertEqual(require_core_frame_hello_v1(legacy_hello), CK3_12004)
        self.assertEqual(normalize_core_frame_v1(result, expected_build=CK3_12004), result)
        with self.assertRaises(ValueError):
            normalize_core_frame_v1(result, expected_build=CK3_1210)

    def test_fixture_provenance_and_raw_cpp_result_shape(self) -> None:
        provenance = json.loads((FIXTURES / "provenance.json").read_text(encoding="utf-8"))
        self.assertIs(provenance["result_payload_changed"], False)
        self.assertIs(provenance["core_values_synthesized"], False)
        self.assertEqual(len(provenance["origin"]["sha256"]), 64)
        for kind in ("partial", "unavailable"):
            raw = (FIXTURES / f"producer-{kind}.json").read_bytes()
            self.assertTrue(raw.endswith(b"\n"))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), provenance["fixtures"][kind]["sha256"])


class PublicCoreConsumer(unittest.IsolatedAsyncioTestCase):
    async def test_real_cpp_partial_through_protocol_driver_service_registered_mcp(self) -> None:
        await self._registered("partial")

    async def test_real_cpp_unavailable_through_protocol_driver_service_registered_mcp(self) -> None:
        await self._registered("unavailable")

    async def _registered(self, kind: str) -> None:
        wire = producer_wire(kind)
        driver, endpoint = driver_for(wire, hello1210())
        server = create_server(driver)
        result = await server.call_tool("ck3_query_core_frame_v1", {})
        self.assertFalse(result.is_error, result.content)
        self.assertEqual(result.structured_content, wire["result"])
        self.assertEqual(json.loads(result.content[0].text), wire["result"])
        self.assertEqual(len(endpoint.requests), 1)
        self.assertEqual(endpoint.wire, wire)
        self.assertIs(driver.state.diagnostics()["semantic_state_available"], False)

    async def test_driver_binds_response_to_actual_hello_build(self) -> None:
        wire = producer_wire("partial")
        legacy_hello = hello1210()
        legacy_hello.update(expected_ck3_version=CK3_12004.game_version,
            expected_ck3_sha256=CK3_12004.executable_sha256,
            game_adapter_id="ck3-1.20.0.4-msvc-x64")
        driver, endpoint = driver_for(wire, legacy_hello)
        with self.assertRaises(BridgeUnavailableError):
            driver.query_core_frame_v1()
        self.assertEqual(len(endpoint.requests), 1)

    async def test_bad_florin_hello_is_refused_before_any_query(self) -> None:
        for field, bad in (("expected_ck3_sha256", CK3_12004.executable_sha256),
                ("game_adapter_id", "wrong"), ("ck3_build_match", False)):
            with self.subTest(field=field):
                hello = hello1210(); hello[field] = bad
                driver, endpoint = driver_for(producer_wire("partial"), hello)
                with self.assertRaises(BridgeUnavailableError):
                    driver.query_core_frame_v1()
                self.assertEqual(endpoint.requests, [])

    async def test_registered_tool_rejects_extra_arguments(self) -> None:
        driver, endpoint = driver_for(producer_wire("partial"), hello1210())
        with self.assertRaisesRegex(ToolError, "Extra inputs are not permitted"):
            await create_server(driver).call_tool("ck3_query_core_frame_v1", {"expected_revision": 1})
        self.assertEqual(endpoint.requests, [])


if __name__ == "__main__":
    unittest.main()
