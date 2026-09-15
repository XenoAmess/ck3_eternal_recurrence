from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.coat_of_arms_source_probe_contract import (  # noqa: E402
    COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256,
    COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
    PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY,
    PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
    encode_coat_of_arms_source_transport_v2,
)
from xar_autoplayer.bridge.coat_of_arms_source_upload_v2 import (  # noqa: E402
    COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError  # noqa: E402
from xar_autoplayer.bridge.mcp_server import (  # noqa: E402
    _ck3_abort_coat_of_arms_source_upload_v2,
    _ck3_append_coat_of_arms_source_chunk_v2,
    _ck3_begin_coat_of_arms_source_upload_v2,
    _ck3_commit_coat_of_arms_source_upload_v2,
    create_server,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402


def _binding(generation: int = 3) -> dict[str, object]:
    return {
        "mode": "frontend",
        "revision": 0,
        "connection_generation": generation,
        "bridge_pid": 4242,
    }


def _capabilities(generation: int = 3) -> dict[str, object]:
    return {
        "format_version": 1,
        "backend_id": "native-headless",
        "mode": "native-headless",
        "source": "injected-dll-named-pipe",
        "snapshot": False,
        "visual_fallback": False,
        "bridge_capabilities": [PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY],
        "diagnostics": {
            "connected": True,
            "semantic_state_available": False,
            "connection_generation": generation,
            "bridge_pid": 4242,
            "hello": {
                "pid": 4242,
                "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                "game_adapter_status": "ready",
                "expected_ck3_version": COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
                "expected_ck3_sha256": (
                    COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256
                ),
                "ck3_build_match": True,
                "capabilities": [PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY],
            },
        },
    }


class _Driver:
    def __init__(self) -> None:
        self.generation = 3
        self.calls: list[tuple[str, int, bool]] = []

    def capabilities(self) -> dict[str, object]:
        return copy.deepcopy(_capabilities(self.generation))

    def take_snapshot(self) -> dict[str, object]:
        raise AssertionError("frontend upload must not request a snapshot")

    def probe_coat_of_arms_source_transport_v2(
        self,
        source: str,
        *,
        expected_revision: int,
        apply: bool,
    ) -> dict[str, object]:
        self.calls.append((source, expected_revision, apply))
        encoded = encode_coat_of_arms_source_transport_v2(source)
        return {
            "schema": "coat-of-arms-source-probe-v1",
            "schema_version": 1,
            "step": PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
            "status": "applied" if apply else "detected",
            "detected": True,
            "designer_observed": True,
            "clipboard_written": True,
            "clipboard_readback_matched": True,
            "apply_requested": apply,
            "paste_invoked": apply,
            "applied": apply,
            "candidate_index": 123,
            "preview_coat_of_arms_handle": 456,
            "active_coat_of_arms_index": 123 if apply else 789,
            "reason": None,
            "source_sha256": encoded.source_sha256,
            "source_bytes": encoded.source_bytes,
            "binding": _binding(self.generation),
        }


def _payload() -> bytes:
    value = (
        b"coat_of_arms = {\r\n"
        + b" colored_emblem = { depth = 1 }\r\n" * 4_200
        + b"}\r\n"
    )
    assert len(value) > 128 * 1024
    return value


def _metadata(payload: bytes) -> dict[str, object]:
    return {
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "expected_revision": 0,
        "apply": True,
        "expected_game_version": COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
        "expected_executable_sha256": (
            COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256
        ),
    }


def _send(
    service: GameplayBridgeService,
    payload: bytes,
) -> tuple[dict[str, object], dict[str, object]]:
    chunks = [
        payload[offset : offset + COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES]
        for offset in range(0, len(payload), COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES)
    ]
    metadata = _metadata(payload)
    receipt = _ck3_begin_coat_of_arms_source_upload_v2(
        service,
        len(payload),
        str(metadata["source_sha256"]),
        len(chunks),
        "base64",
        0,
        True,
        COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
        COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256,
    )
    for index, chunk in enumerate(chunks):
        progress = _ck3_append_coat_of_arms_source_chunk_v2(
            service,
            str(receipt["upload_id"]),
            int(receipt["generation"]),
            index,
            len(chunks),
            "base64",
            len(chunk),
            hashlib.sha256(chunk).hexdigest(),
            base64.b64encode(chunk).decode("ascii"),
            str(metadata["source_sha256"]),
            0,
            True,
            COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
            COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256,
        )
    return receipt, progress


class CoatOfArmsSourceUploadV2BridgeTests(unittest.TestCase):
    def test_large_upload_invokes_native_once_only_after_commit(self) -> None:
        payload = _payload()
        driver = _Driver()
        service = GameplayBridgeService(driver)
        receipt, progress = _send(service, payload)
        self.assertEqual(progress["status"], "ready")
        self.assertEqual(driver.calls, [])

        result = _ck3_commit_coat_of_arms_source_upload_v2(
            service,
            str(receipt["upload_id"]),
            int(receipt["generation"]),
            int(receipt["chunk_count"]),
            str(receipt["source_sha256"]),
            0,
            True,
            COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
            COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256,
        )
        self.assertEqual(result["status"], "committed")
        self.assertEqual(result["upload"]["received_bytes"], len(payload))
        self.assertEqual(result["result"]["source_sha256"], receipt["source_sha256"])
        self.assertEqual(driver.calls, [(payload.decode("ascii"), 0, True)])

    def test_binding_drift_fails_before_native_apply(self) -> None:
        driver = _Driver()
        service = GameplayBridgeService(driver)
        receipt, _ = _send(service, _payload())
        driver.generation += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "revision binding"):
            _ck3_commit_coat_of_arms_source_upload_v2(
                service,
                str(receipt["upload_id"]),
                int(receipt["generation"]),
                int(receipt["chunk_count"]),
                str(receipt["source_sha256"]),
                0,
                True,
                COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
                COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256,
            )
        self.assertEqual(driver.calls, [])

    def test_abort_facade_never_calls_native(self) -> None:
        payload = b"coat_of_arms = {}\r\n"
        driver = _Driver()
        service = GameplayBridgeService(driver)
        metadata = _metadata(payload)
        receipt = _ck3_begin_coat_of_arms_source_upload_v2(
            service,
            len(payload),
            str(metadata["source_sha256"]),
            1,
            "base64",
            0,
            True,
            COAT_OF_ARMS_SOURCE_V1_GAME_VERSION,
            COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256,
        )
        aborted = _ck3_abort_coat_of_arms_source_upload_v2(
            service,
            str(receipt["upload_id"]),
            int(receipt["generation"]),
        )
        self.assertEqual(aborted["status"], "aborted")
        self.assertEqual(driver.calls, [])


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CoatOfArmsSourceUploadV2McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_four_closed_v2_schemas(self) -> None:
        from mcp import Client

        async with Client(create_server(_Driver())) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            expected = {
                "ck3_begin_coat_of_arms_source_upload_v2": 8,
                "ck3_append_coat_of_arms_source_chunk_v2": 13,
                "ck3_commit_coat_of_arms_source_upload_v2": 8,
                "ck3_abort_coat_of_arms_source_upload_v2": 2,
            }
            for name, required_count in expected.items():
                self.assertIn(name, tools)
                self.assertEqual(
                    len(tools[name].input_schema["required"]),
                    required_count,
                )
                self.assertFalse(
                    tools[name].input_schema["additionalProperties"]
                )

    async def test_official_client_transfers_over_128_kib_without_truncation(
        self,
    ) -> None:
        from mcp import Client

        payload = _payload()
        chunks = [
            payload[
                offset : offset
                + COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES
            ]
            for offset in range(
                0,
                len(payload),
                COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES,
            )
        ]
        digest = hashlib.sha256(payload).hexdigest()
        driver = _Driver()
        async with Client(create_server(driver)) as client:
            begun = await client.call_tool(
                "ck3_begin_coat_of_arms_source_upload_v2",
                {
                    "total_bytes": len(payload),
                    "source_sha256": digest,
                    "chunk_count": len(chunks),
                    "chunk_encoding": "base64",
                    "expected_revision": 0,
                    "apply": True,
                    "expected_game_version": (
                        COAT_OF_ARMS_SOURCE_V1_GAME_VERSION
                    ),
                    "expected_executable_sha256": (
                        COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256
                    ),
                },
            )
            self.assertFalse(begun.is_error)
            receipt = begun.structured_content
            for index, chunk in enumerate(chunks):
                appended = await client.call_tool(
                    "ck3_append_coat_of_arms_source_chunk_v2",
                    {
                        "upload_id": receipt["upload_id"],
                        "generation": receipt["generation"],
                        "chunk_index": index,
                        "chunk_count": len(chunks),
                        "chunk_encoding": "base64",
                        "chunk_bytes": len(chunk),
                        "chunk_sha256": hashlib.sha256(chunk).hexdigest(),
                        "chunk_base64": base64.b64encode(chunk).decode(
                            "ascii"
                        ),
                        "source_sha256": digest,
                        "expected_revision": 0,
                        "apply": True,
                        "expected_game_version": (
                            COAT_OF_ARMS_SOURCE_V1_GAME_VERSION
                        ),
                        "expected_executable_sha256": (
                            COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256
                        ),
                    },
                )
                self.assertFalse(appended.is_error)
            committed = await client.call_tool(
                "ck3_commit_coat_of_arms_source_upload_v2",
                {
                    "upload_id": receipt["upload_id"],
                    "generation": receipt["generation"],
                    "chunk_count": len(chunks),
                    "source_sha256": digest,
                    "expected_revision": 0,
                    "apply": True,
                    "expected_game_version": (
                        COAT_OF_ARMS_SOURCE_V1_GAME_VERSION
                    ),
                    "expected_executable_sha256": (
                        COAT_OF_ARMS_SOURCE_V1_EXECUTABLE_SHA256
                    ),
                },
            )
            self.assertFalse(committed.is_error)
            result = committed.structured_content
            self.assertEqual(result["upload"]["received_bytes"], len(payload))
            self.assertEqual(result["result"]["source_sha256"], digest)
            self.assertEqual(driver.calls, [(payload.decode("ascii"), 0, True)])


if __name__ == "__main__":
    unittest.main()
