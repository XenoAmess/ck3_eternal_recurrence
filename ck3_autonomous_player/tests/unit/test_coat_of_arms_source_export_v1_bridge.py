from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from xar_autoplayer.bridge.coat_of_arms_source_export_contract import (
    EXPORT_COAT_OF_ARMS_SOURCE_V1_CAPABILITY,
    EXPORT_COAT_OF_ARMS_SOURCE_V1_STEP,
    normalize_coat_of_arms_source_export_v1_result,
    normalize_native_coat_of_arms_source_export_v1_result,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.mcp_server import (
    _ck3_export_coat_of_arms_source_v1,
    create_server,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


SOURCE = 'coa={\r\n pattern="pattern_solid.dds"\r\n color1=blue\r\n}\r\n'


def _binding() -> dict[str, object]:
    return {
        "mode": "frontend",
        "revision": 0,
        "connection_generation": 3,
        "bridge_pid": 4242,
    }


def _capabilities(*, advertised: bool = True) -> dict[str, object]:
    bridge_capabilities = (
        [
            EXPORT_COAT_OF_ARMS_SOURCE_V1_CAPABILITY,
            "game.command.probe-coat-of-arms-source-v1",
        ]
        if advertised
        else []
    )
    return {
        "format_version": 1,
        "backend_id": "native-headless",
        "mode": "native-headless",
        "source": "injected-dll-named-pipe",
        "snapshot": False,
        "visual_fallback": False,
        "bridge_capabilities": bridge_capabilities,
        "diagnostics": {
            "connected": True,
            "connection_generation": 3,
            "bridge_pid": 4242,
            "semantic_state_available": False,
            "hello": {
                "pid": 4242,
                "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                "game_adapter_status": "ready",
                "expected_ck3_version": "1.19.0.6",
                "expected_ck3_sha256": (
                    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
                ),
                "ck3_build_match": True,
                "capabilities": bridge_capabilities,
            },
        },
    }


def _native_result() -> dict[str, object]:
    return {
        "step": EXPORT_COAT_OF_ARMS_SOURCE_V1_STEP,
        "accepted": True,
        "status": "exported",
        "query_sequence": 1,
        "snapshot_revision": 0,
        "coat_of_arms_export": {
            "schema": "xar.ck3.coat-of-arms-designer-export.v1",
            "schema_version": 1,
            "status": "exported",
            "date_raw": 0,
            "source_bytes": len(SOURCE.encode("ascii")),
            "designer_observed": True,
            "copy_invoked": True,
            "clipboard_read": True,
            "source": SOURCE,
            "reason": None,
            "provenance": {
                "backend_id": (
                    "ck3-1.19.0.6-native-coat-of-arms-designer-export-v1"
                )
            },
        },
        "backend_id": "native-headless",
    }


def _public_result() -> dict[str, object]:
    encoded = SOURCE.encode("ascii")
    return {
        "schema": "coat-of-arms-source-export-v1",
        "schema_version": 1,
        "step": EXPORT_COAT_OF_ARMS_SOURCE_V1_STEP,
        "status": "exported",
        "designer_observed": True,
        "copy_invoked": True,
        "clipboard_read": True,
        "source": SOURCE,
        "source_sha256": hashlib.sha256(encoded).hexdigest(),
        "source_bytes": len(encoded),
        "reason": None,
        "binding": _binding(),
    }


class _ExportDriver:
    def __init__(self, *, advertised: bool = True) -> None:
        self.advertised = advertised
        self.calls: list[int] = []

    def capabilities(self) -> dict[str, object]:
        return copy.deepcopy(_capabilities(advertised=self.advertised))

    def export_coat_of_arms_source_v1(
        self, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(expected_revision)
        return _public_result()


class CoatOfArmsSourceExportV1Tests(unittest.TestCase):
    def test_native_envelope_binds_exact_source_bytes(self) -> None:
        normalized = normalize_native_coat_of_arms_source_export_v1_result(
            _native_result(),
            expected_native_revision=0,
            expected_date_raw=0,
        )
        self.assertEqual(normalized["source"], SOURCE)
        self.assertEqual(
            normalized["source_sha256"],
            hashlib.sha256(SOURCE.encode("ascii")).hexdigest(),
        )

    def test_public_envelope_is_exact_and_bound(self) -> None:
        normalized = normalize_coat_of_arms_source_export_v1_result(
            _public_result(),
            expected_binding=_binding(),
        )
        self.assertEqual(normalized["status"], "exported")
        malformed = _public_result()
        malformed["source_bytes"] = 1
        with self.assertRaises(ValueError):
            normalize_coat_of_arms_source_export_v1_result(
                malformed,
                expected_binding=_binding(),
            )

    def test_unavailable_result_never_exposes_stale_source(self) -> None:
        unavailable = _public_result()
        unavailable.update(
            status="unavailable",
            designer_observed=True,
            copy_invoked=True,
            clipboard_read=False,
            source=None,
            source_sha256=None,
            source_bytes=0,
            reason="clipboard_read_failed",
        )
        normalized = normalize_coat_of_arms_source_export_v1_result(
            unavailable,
            expected_binding=_binding(),
        )
        self.assertIsNone(normalized["source"])

    def test_service_and_mcp_helper_call_typed_export(self) -> None:
        driver = _ExportDriver()
        service = GameplayBridgeService(driver)
        result = _ck3_export_coat_of_arms_source_v1(service, 0)
        self.assertEqual(result["source"], SOURCE)
        self.assertEqual(driver.calls, [0])

    def test_service_refuses_unadvertised_backend(self) -> None:
        service = GameplayBridgeService(_ExportDriver(advertised=False))
        with self.assertRaises(UnsupportedStepError):
            service.export_coat_of_arms_source_v1(expected_revision=0)


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CoatOfArmsSourceExportV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_export_tool(self) -> None:
        from mcp import Client

        driver = _ExportDriver()
        async with Client(create_server(driver)) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools["ck3_export_coat_of_arms_source_v1"]
            self.assertEqual(
                set(tool.input_schema["required"]),
                {"expected_revision"},
            )
            self.assertFalse(tool.input_schema["additionalProperties"])
            result = await client.call_tool(
                "ck3_export_coat_of_arms_source_v1",
                {"expected_revision": 0},
            )
            self.assertFalse(result.is_error)
            self.assertEqual(result.structured_content["source"], SOURCE)


if __name__ == "__main__":
    unittest.main()
