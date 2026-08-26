from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge import loaded_feature_manifest_contract as contract
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.loaded_feature_manifest_contract import (
    LOADED_FEATURE_MANIFEST_V1_BACKEND_ID,
    LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
    LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
    QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
    QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
    normalize_loaded_feature_manifest_v1,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_loaded_feature_manifest_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


NATIVE_REVISION = 31
PUBLIC_REVISION = 7
DATE_RAW = 53_182_016
STEP = QUERY_LOADED_FEATURE_MANIFEST_V1_STEP
UNAVAILABLE_REASONS = (
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "feature_root_unavailable",
    "feature_counter_mismatch",
    "feature_registry_drift",
    "script_dlc_set_unavailable",
    "script_dlc_key_invalid",
    "state_changed",
    "internal_error",
)


def _readiness(ready: bool) -> dict[str, bool]:
    return {
        "effective_feature_flags_ready": ready,
        "script_dlc_keys_ready": ready,
        "entitlements_ready": False,
        "same_frame_ready": ready,
        "actionable_ready": ready,
    }


def _provenance() -> dict[str, str]:
    return {
        "feature_root_slot_rva": "0x576CC68",
        "feature_bitset_rva": "root+0x2B0",
        "feature_enum_table_rva": "0x42F7850..0x42F7900",
        "script_dlc_set_rva": "0x5762590",
        "backend_id": LOADED_FEATURE_MANIFEST_V1_BACKEND_ID,
    }


def _feature_items() -> list[dict[str, object]]:
    return [
        {
            "native_index": index,
            "cstring_id": cstring_id,
            "key": key,
            "enabled": index % 3 == 0,
        }
        for index, (cstring_id, key) in enumerate(
            contract._FEATURE_DEFINITIONS
        )
    ]


def _frame(
    status: str = "available",
    *,
    unavailable_reason: str = "state_changed",
) -> dict[str, object]:
    available = status == "available"
    reason = None if available else unavailable_reason
    return {
        "schema": "loaded-feature-manifest-v1",
        "schema_version": 1,
        "status": status,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "unavailable_reason": reason,
        "build": {
            "version": LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
            "exe_sha256": LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
        },
        "effective_feature_flags": {
            "status": "available" if available else "unavailable",
            "unavailable_reason": reason,
            "native_count": 44 if available else None,
            "items": _feature_items() if available else None,
        },
        "script_dlc_keys": {
            "status": "available" if available else "unavailable",
            "unavailable_reason": reason,
            "enumerated_count": 3 if available else None,
            "keys": (
                ["dlc_001", "dlc_002", "expansion_001"]
                if available
                else None
            ),
        },
        "entitlements": {
            "status": "unavailable",
            "unavailable_reason": "store_verdict_provenance_unclosed",
            "items": None,
        },
        "readiness": _readiness(available),
        "provenance": _provenance(),
    }


def _native_result(status: str = "available") -> dict[str, object]:
    return {
        "step": STEP,
        "accepted": True,
        "status": status,
        "query_sequence": 12,
        "snapshot_revision": NATIVE_REVISION,
        "loaded_feature_manifest": _frame(status),
        "backend_id": "native-headless",
    }


_MIRROR_KEYS = (
    "schema",
    "schema_version",
    "date_raw",
    "unavailable_reason",
    "build",
    "effective_feature_flags",
    "script_dlc_keys",
    "entitlements",
    "readiness",
    "provenance",
)


def _driver_result(status: str = "available") -> dict[str, object]:
    result = _native_result(status)
    frame = result["loaded_feature_manifest"]
    assert isinstance(frame, dict)
    for key in _MIRROR_KEYS:
        result[key] = copy.deepcopy(frame[key])
    readiness = frame["readiness"]
    assert isinstance(readiness, dict)
    result.update(
        {
            "loaded_feature_manifest_ready": readiness["actionable_ready"],
            "queried_snapshot_id": "loaded-feature-fixture:7",
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
        }
    )
    return result


def _semantic_snapshot(
    revision: int = NATIVE_REVISION,
    *,
    paused: bool = True,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.10.16",
            "date_raw": DATE_RAW,
            "speed": 1,
            "paused": paused,
            "map_ready": True,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {"character_id": 12345, "alive": True},
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class LoadedFeatureManifestV1ContractTests(unittest.TestCase):
    def test_available_preserves_exact_flags_and_sorted_script_keys(self) -> None:
        normalized = normalize_loaded_feature_manifest_v1(
            _frame(),
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(normalized["status"], "available")
        self.assertEqual(
            normalized["effective_feature_flags"]["native_count"], 44
        )
        self.assertEqual(
            normalized["effective_feature_flags"]["items"][0]["key"],
            "garments_of_the_hre",
        )
        self.assertEqual(
            normalized["script_dlc_keys"]["keys"],
            ["dlc_001", "dlc_002", "expansion_001"],
        )
        self.assertFalse(normalized["readiness"]["entitlements_ready"])
        self.assertTrue(normalized["readiness"]["actionable_ready"])

    def test_all_native_unavailable_stages_are_typed(self) -> None:
        for reason in UNAVAILABLE_REASONS:
            with self.subTest(reason=reason):
                normalized = normalize_loaded_feature_manifest_v1(
                    _frame("unavailable", unavailable_reason=reason),
                    expected_date_raw=DATE_RAW,
                    expected_snapshot_revision=NATIVE_REVISION,
                )
                self.assertEqual(normalized["unavailable_reason"], reason)
                self.assertIsNone(
                    normalized["effective_feature_flags"]["items"]
                )
                self.assertIsNone(normalized["script_dlc_keys"]["keys"])
                self.assertFalse(
                    normalized["readiness"]["actionable_ready"]
                )

    def test_schema_registry_sort_count_and_entitlements_are_strict(self) -> None:
        mutations = {
            "extra": lambda row: row.__setitem__("extra", None),
            "schema": lambda row: row.__setitem__("schema", "wrong"),
            "revision": lambda row: row.__setitem__(
                "snapshot_revision", NATIVE_REVISION + 1
            ),
            "date": lambda row: row.__setitem__("date_raw", DATE_RAW + 1),
            "build": lambda row: row["build"].__setitem__(
                "version", "1.19.0.7"
            ),
            "registry": lambda row: row["effective_feature_flags"][
                "items"
            ][0].__setitem__("cstring_id", 1),
            "enabled_type": lambda row: row["effective_feature_flags"][
                "items"
            ][0].__setitem__("enabled", 1),
            "script_order": lambda row: row["script_dlc_keys"].__setitem__(
                "keys", ["expansion_001", "dlc_001", "dlc_002"]
            ),
            "script_count": lambda row: row["script_dlc_keys"].__setitem__(
                "enumerated_count", 99
            ),
            "entitlements": lambda row: row["entitlements"].__setitem__(
                "status", "available"
            ),
            "readiness": lambda row: row["readiness"].__setitem__(
                "entitlements_ready", True
            ),
            "provenance": lambda row: row["provenance"].__setitem__(
                "script_dlc_set_rva", "0x0"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    normalize_loaded_feature_manifest_v1(
                        frame,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_loaded_feature_v1_fixture"
        self.frames: list[dict[str, object]] = []
        self.on_frame = None
        self.on_disconnect = None
        self.send_hook = None

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        assert self.on_frame is not None
        self.on_frame(frame)

    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)

    def close(self) -> None:
        return None

    def transport_error(self) -> str | None:
        return None


def _native_driver(
    *, paused: bool = True
) -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=0.1,
    )
    endpoint.publish(
        {
            "type": "hello",
            "protocol_version": 1,
            "bridge_version": "0.1.0",
            "pid": 7878,
            "session_generation": 0,
            "game_version": LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
            "expected_ck3_version": LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
            "executable_sha256": LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
            "capabilities": [
                "game.state.snapshot",
                QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
            ],
        }
    )
    endpoint.publish(_semantic_snapshot(paused=paused))
    return driver, endpoint


def _answer_with(endpoint: _FakeEndpoint, result_factory) -> None:
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        endpoint.publish(
            {
                "type": "command_result",
                "protocol_version": 1,
                "request_id": frame["request_id"],
                "ok": True,
                "result": result_factory(),
            }
        )

    endpoint.send_hook = answer


class LoadedFeatureManifestV1NativeDriverTests(unittest.TestCase):
    def test_singleton_action_is_advertised_only_while_paused(self) -> None:
        driver, _endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(
            capabilities["loaded_feature_manifest_v1_query_supported"]
        )
        self.assertIn(STEP, capabilities["action_steps"])
        self.assertEqual(
            _action_steps(
                [QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY], paused=True
            ),
            [STEP],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY], paused=False
            ),
            [],
        )

    def test_driver_normalizes_available_and_unavailable(self) -> None:
        for status in ("available", "unavailable"):
            with self.subTest(status=status):
                driver, endpoint = _native_driver()
                _answer_with(
                    endpoint, lambda selected=status: _native_result(selected)
                )
                result = driver.execute_step(
                    STEP,
                    expected_revision=int(driver.take_snapshot()["revision"]),
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(
                    result["loaded_feature_manifest_ready"],
                    status == "available",
                )
                self.assertEqual(result["build"]["version"], "1.19.0.6")
                self.assertEqual(
                    result["queried_native_revision"], NATIVE_REVISION
                )

    def test_driver_rejects_envelope_and_frame_drift(self) -> None:
        driver, endpoint = _native_driver()

        def wrong_status() -> dict[str, object]:
            result = _native_result()
            result["status"] = "unavailable"
            return result

        _answer_with(endpoint, wrong_status)
        with self.assertRaisesRegex(BridgeUnavailableError, "disagrees"):
            driver.execute_step(
                STEP,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = _native_driver()

        def drift() -> dict[str, object]:
            result = _native_result()
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            return result

        _answer_with(endpoint, drift)
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            driver.execute_step(
                STEP,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )


class _ServiceDriver:
    def __init__(
        self,
        status: str = "available",
        *,
        advertise: bool = True,
        drift: bool = False,
        mirror_drift: bool = False,
        build_drift: bool = False,
    ) -> None:
        self.status = status
        self.advertise = advertise
        self.drift = drift
        self.mirror_drift = mirror_drift
        self.build_drift = build_drift
        self.calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [STEP] if self.advertise else [],
            "bridge_capabilities": (
                [QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.calls += 1
        revision = (
            PUBLIC_REVISION + 1
            if self.drift and self.calls > 1
            else PUBLIC_REVISION
        )
        return {
            "format_version": 1,
            "snapshot_id": f"loaded-feature-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-12345-fixture",
            "diagnostics": {
                "hello": {
                    "game_version": LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
                    "expected_ck3_version": (
                        LOADED_FEATURE_MANIFEST_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        "A" * 64
                        if self.build_drift
                        else LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
                    ),
                }
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step != STEP or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed loaded-feature binding")
        result = _driver_result(self.status)
        if self.mirror_drift:
            result["schema"] = "wrong"
        return result

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("loaded-feature observation must not advance")


class LoadedFeatureManifestV1ServiceTests(unittest.TestCase):
    def test_facade_and_service_return_exact_build_binding(self) -> None:
        result = _ck3_query_loaded_feature_manifest_v1(
            GameplayBridgeService(_ServiceDriver()), PUBLIC_REVISION
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(result["scope"], "exact-loaded-feature-manifest")
        self.assertEqual(result["binding"]["revision"], PUBLIC_REVISION)
        self.assertEqual(
            result["binding"]["native_revision"], NATIVE_REVISION
        )
        self.assertEqual(result["build"]["version"], "1.19.0.6")
        self.assertEqual(
            result["effective_feature_flags"]["native_count"], 44
        )
        self.assertEqual(
            result["entitlements"]["unavailable_reason"],
            "store_verdict_provenance_unclosed",
        )

    def test_service_returns_typed_unavailable(self) -> None:
        result = GameplayBridgeService(
            _ServiceDriver("unavailable")
        ).query_loaded_feature_manifest_v1(
            expected_revision=PUBLIC_REVISION
        )

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], "state_changed")
        self.assertFalse(result["loaded_feature_manifest_ready"])
        self.assertIsNone(result["effective_feature_flags"]["items"])
        self.assertIsNone(result["script_dlc_keys"]["keys"])

    def test_service_rejects_capability_revision_build_and_frame_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_loaded_feature_manifest_v1(
                expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_loaded_feature_manifest_v1(
                expected_revision=PUBLIC_REVISION - 1
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "mirrors disagree"):
            GameplayBridgeService(
                _ServiceDriver(mirror_drift=True)
            ).query_loaded_feature_manifest_v1(
                expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "build mirror"):
            GameplayBridgeService(
                _ServiceDriver(build_drift=True)
            ).query_loaded_feature_manifest_v1(
                expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_loaded_feature_manifest_v1(
                expected_revision=PUBLIC_REVISION
            )


class _HybridNative:
    def __init__(self) -> None:
        self.expected_revision = None

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [
                QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
            ]
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.expected_revision = expected_revision
        return _driver_result()


class _HybridDelegate:
    def take_snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "hybrid:7",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "backend_revisions": {"fast": 23},
        }


class LoadedFeatureManifestV1HybridTests(unittest.TestCase):
    def test_hybrid_forwards_to_native_revision_and_rebinds_public_frame(self) -> None:
        native = _HybridNative()
        driver = object.__new__(ConfiguredHybridFallbackDriver)
        driver.native = native
        driver._delegate = _HybridDelegate()

        result = driver.execute_step(STEP, expected_revision=PUBLIC_REVISION)

        self.assertEqual(native.expected_revision, 23)
        self.assertEqual(result["queried_snapshot_id"], "hybrid:7")
        self.assertEqual(result["queried_revision"], PUBLIC_REVISION)
        self.assertEqual(result["queried_native_revision"], NATIVE_REVISION)


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class LoadedFeatureManifestV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_loaded_feature_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_loaded_feature_manifest_v1", names)
            result = await client.call_tool(
                "ck3_query_loaded_feature_manifest_v1",
                {"expected_revision": PUBLIC_REVISION},
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertEqual(
            payload["effective_feature_flags"]["native_count"], 44
        )
        self.assertEqual(payload["build"]["version"], "1.19.0.6")


if __name__ == "__main__":
    unittest.main()
