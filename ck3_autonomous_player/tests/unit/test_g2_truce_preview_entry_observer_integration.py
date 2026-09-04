from __future__ import annotations

from pathlib import Path
import unittest

from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.service import GameplayBridgeService


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"
BRIDGE_CPP = NATIVE / "src" / "bridge.cpp"
NATIVE_DRIVER = ROOT / "src" / "xar_autoplayer" / "bridge" / "native_driver.py"
SERVICE = ROOT / "src" / "xar_autoplayer" / "bridge" / "service.py"
MCP = ROOT / "src" / "xar_autoplayer" / "bridge" / "mcp_server.py"
CMAKE = NATIVE / "CMakeLists.txt"


class _DiagnosticDriver:
    def __init__(self) -> None:
        self.value = {
            "backend_id": "fixture",
            "private_observers": {
                "g2_truce_preview_entry_observer_v1": {
                    "private_build": True,
                    "read_only": True,
                    "advertised": False,
                }
            },
        }

    def diagnostics(self) -> dict[str, object]:
        return self.value

    def capabilities(self) -> dict[str, object]:
        return {"backend_id": "fixture", "bridge_capabilities": []}


class G2TrucePreviewEntryObserverIntegrationTest(unittest.TestCase):
    def test_native_protocol_preserves_private_observer_diagnostics(self) -> None:
        state = NativeProtocolState(r"\\.\pipe\xar-test")
        state.ingest(
            {
                "type": "hello",
                "protocol_version": 1,
                "pid": 123,
                "capabilities": ["bridge.identity", "bridge.heartbeat"],
            }
        )
        state.ingest(
            {
                "type": "heartbeat",
                "protocol_version": 1,
                "sequence": 1,
                "g2_truce_preview_entry_observer_v1": {
                    "private_build": True,
                    "read_only": True,
                    "advertised": False,
                    "accepted_count": 0,
                },
            }
        )
        diagnostics = state.diagnostics()
        self.assertEqual(
            diagnostics["private_observers"][
                "g2_truce_preview_entry_observer_v1"
            ]["accepted_count"],
            0,
        )
        self.assertNotIn(
            "g2_truce_preview_entry_observer_v1",
            diagnostics["hello"]["capabilities"],
        )

    def test_service_diagnostics_path_is_read_only_and_private(self) -> None:
        diagnostics = GameplayBridgeService(_DiagnosticDriver()).bridge_diagnostics()
        observer = diagnostics["private_observers"][
            "g2_truce_preview_entry_observer_v1"
        ]
        self.assertTrue(observer["private_build"])
        self.assertTrue(observer["read_only"])
        self.assertFalse(observer["advertised"])

    def test_shared_wiring_installs_production_hook_without_public_action(self) -> None:
        cmake = CMAKE.read_text(encoding="utf-8")
        bridge = BRIDGE_CPP.read_text(encoding="utf-8")
        driver = NATIVE_DRIVER.read_text(encoding="utf-8")
        service = SERVICE.read_text(encoding="utf-8")
        mcp = MCP.read_text(encoding="utf-8")
        option = "XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1"
        self.assertIn(option, cmake)
        self.assertRegex(cmake, rf"(?s)option\(\s*{option}.*?\sOFF\s*\)")
        self.assertIn("src/g2_truce_preview_entry_observer_v1.cpp", cmake)
        self.assertIn("xar_ck3_g2_truce_preview_entry_observer_v1_test", cmake)
        self.assertIn("g2_truce_preview_entry_observer_v1.hpp", bridge)
        self.assertIn(
            "constexpr bool kG2TrucePreviewEntryObserverEnabledV1 = true",
            bridge,
        )
        observer_header = (
            NATIVE / "include" / "xar_bridge" /
            "g2_truce_preview_entry_observer_v1.hpp"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "kG2TrucePreviewEntryObserverInstalledByDefaultV1 = true",
            observer_header,
        )
        self.assertIn('"private_build\\":true,\\"read_only\\":true,\\"advertised\\":false', bridge)
        self.assertIn("g2_truce_preview_entry_observer_enabled", bridge)
        self.assertIn('"private_observers"', driver)
        self.assertIn("def bridge_diagnostics", service)
        self.assertIn("return service.bridge_diagnostics()", mcp)
        # The private observer is diagnostic-only: it must not be in the hello
        # capability list or become a routable gameplay step.
        capability_lines = [
            line for line in bridge.splitlines() if 'capabilities' in line
        ]
        self.assertTrue(capability_lines)
        self.assertTrue(
            all("g2_truce_preview_entry_observer" not in line
                for line in capability_lines)
        )

    def test_private_preview_heartbeat_leaves_child_open_for_common_terminator(self) -> None:
        bridge = BRIDGE_CPP.read_text(encoding="utf-8")
        cmake = CMAKE.read_text(encoding="utf-8")
        heartbeat = bridge.split(
            "std::string HeartbeatFrame(std::uint64_t sequence) {", 1
        )[1].split("\n}\n\nvoid AppendInt32Array", 1)[0]
        preview = heartbeat.split(
            "#if defined(XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1)"
        )[2].split("#endif", 1)[0]

        # Every optional heartbeat object is closed by the next optional
        # prefix or by HeartbeatFrame's common `}}` terminator. Closing the
        # preview object here adds a third `}` in the leaf-context-only build;
        # NativePipeTransport then rejects every heartbeat while continuing
        # to accept the following state snapshots.
        self.assertIn(
            'result += "},\\\"g2_truce_preview_entry_observer_v1\\\":{";',
            preview,
        )
        self.assertNotIn("result += '}'", preview)
        self.assertTrue(heartbeat.rstrip().endswith('result += "}}";\n  return result;'))
        self.assertRegex(
            cmake,
            r"(?s)if\(XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1 OR\s+"
            r"XAR_CK3_ENABLE_G2_TRUCE_LEAF_CONTEXT_CAPTURE_V2\).*?"
            r"XAR_CK3_ENABLE_G2_TRUCE_PREVIEW_ENTRY_OBSERVER_V1=1",
        )


if __name__ == "__main__":
    unittest.main()
