from __future__ import annotations

from pathlib import Path
import unittest

from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.service import GameplayBridgeService


ROOT = Path(__file__).resolve().parents[2]
NATIVE = ROOT / "native_bridge"
BRIDGE_CPP = NATIVE / "src" / "bridge.cpp"
NATIVE_DRIVER = ROOT / "src" / "xar_autoplayer" / "bridge" / "native_driver.py"
MCP = ROOT / "src" / "xar_autoplayer" / "bridge" / "mcp_server.py"
CMAKE = NATIVE / "CMakeLists.txt"


def _observer() -> dict[str, object]:
    return {
        "private_build": True,
        "read_only": True,
        "guard": False,
        "public_capability": False,
        "installed": True,
        "publisher_slot_count": 2,
        "publishers": [
            {"ordinal": 1, "path": {"preview": "game"}, "raw_result": 1},
            {
                "ordinal": 2,
                "path": {"preview": "D:/fixture/mod"},
                "raw_result": 1,
            },
        ],
    }


def _physfs_observer() -> dict[str, object]:
    return {
        "private_build": True,
        "read_only": True,
        "guard": False,
        "public_capability": False,
        "installed": True,
        "failure_flags": 0,
        "call_count": 2,
        "success_count": 2,
        "failure_count": 0,
        "row_count": 2,
        "rows": [
            {"ordinal": 1, "path": "game", "raw_result": 1},
            {"ordinal": 2, "path": "D:/fixture/mod", "raw_result": 1},
        ],
    }


class _DiagnosticDriver:
    def diagnostics(self) -> dict[str, object]:
        return {
            "backend_id": "fixture",
            "private_observers": {
                "vfs_mount_lifecycle_observer_v1": _observer(),
                "physfs_mounted_data_observer_v1": _physfs_observer(),
            },
        }

    def capabilities(self) -> dict[str, object]:
        return {"backend_id": "fixture", "bridge_capabilities": []}


class VfsMountLifecycleObserverIntegrationTest(unittest.TestCase):
    def test_protocol_preserves_bounded_ordered_publishers_for_mcp(self) -> None:
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
                "vfs_mount_lifecycle_observer_v1": _observer(),
                "physfs_mounted_data_observer_v1": _physfs_observer(),
            }
        )
        diagnostics = state.diagnostics()
        observer = diagnostics["private_observers"][
            "vfs_mount_lifecycle_observer_v1"
        ]
        self.assertEqual(observer["publisher_slot_count"], 2)
        self.assertEqual(
            [row["ordinal"] for row in observer["publishers"]], [1, 2]
        )
        self.assertNotIn(
            "vfs_mount_lifecycle_observer_v1",
            diagnostics["hello"]["capabilities"],
        )
        physfs = diagnostics["private_observers"][
            "physfs_mounted_data_observer_v1"
        ]
        self.assertEqual(physfs["row_count"], 2)
        self.assertEqual([row["ordinal"] for row in physfs["rows"]], [1, 2])
        self.assertNotIn(
            "physfs_mounted_data_observer_v1",
            diagnostics["hello"]["capabilities"],
        )

    def test_service_keeps_observer_on_private_diagnostics_route(self) -> None:
        diagnostics = GameplayBridgeService(_DiagnosticDriver()).bridge_diagnostics()
        observer = diagnostics["private_observers"][
            "vfs_mount_lifecycle_observer_v1"
        ]
        self.assertTrue(observer["private_build"])
        self.assertTrue(observer["read_only"])
        self.assertFalse(observer["public_capability"])
        physfs = diagnostics["private_observers"][
            "physfs_mounted_data_observer_v1"
        ]
        self.assertTrue(physfs["private_build"])
        self.assertTrue(physfs["read_only"])
        self.assertFalse(physfs["public_capability"])

    def test_shared_wiring_is_bounded_default_off_and_not_an_action(self) -> None:
        cmake = CMAKE.read_text(encoding="utf-8")
        bridge = BRIDGE_CPP.read_text(encoding="utf-8")
        driver = NATIVE_DRIVER.read_text(encoding="utf-8")
        mcp = MCP.read_text(encoding="utf-8")
        option = "XAR_CK3_ENABLE_VFS_MOUNT_LIFECYCLE_OBSERVER_V1"
        self.assertIn(option, cmake)
        self.assertIn("kVfsMountLifecyclePublisherSlotsV1 = 64", (
            NATIVE / "include" / "xar_bridge" /
            "vfs_mount_lifecycle_observer_v1.hpp"
        ).read_text(encoding="utf-8"))
        self.assertIn('result += ",\\\"publisher_slot_count\\\":";', bridge)
        self.assertIn('result += ",\\\"publishers\\\":[";', bridge)
        self.assertIn('"vfs_mount_lifecycle_observer_v1"', driver)
        self.assertIn('"physfs_mounted_data_observer_v1"', driver)
        self.assertIn(
            "XAR_CK3_ENABLE_PHYSFS_MOUNTED_DATA_OBSERVER_V1", cmake
        )
        self.assertIn("kPhysfsMountedDataSlotsV1 = 128", (
            NATIVE / "include" / "xar_bridge" /
            "physfs_mounted_data_observer_v1.hpp"
        ).read_text(encoding="utf-8"))
        self.assertIn("def ck3_get_bridge_diagnostics", mcp)
        self.assertIn("return service.bridge_diagnostics()", mcp)
        capability_lines = [
            line for line in bridge.splitlines() if "capabilities" in line
        ]
        self.assertTrue(capability_lines)
        self.assertTrue(
            all(
                "vfs_mount_lifecycle_observer" not in line
                and "physfs_mounted_data_observer" not in line
                for line in capability_lines
            )
        )


if __name__ == "__main__":
    unittest.main()
