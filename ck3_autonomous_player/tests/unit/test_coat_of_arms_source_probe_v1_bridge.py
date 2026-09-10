from __future__ import annotations

import base64
import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from xar_autoplayer.bridge.coat_of_arms_source_probe_contract import (
    COAT_OF_ARMS_SOURCE_V1_MAX_BYTES,
    PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY,
    PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
    coat_of_arms_source_frontend_binding_from_capabilities,
    encode_coat_of_arms_source_v1,
    normalize_coat_of_arms_source_v1_result,
    normalize_native_coat_of_arms_source_v1_result,
    validate_coat_of_arms_source_probe_apply,
)
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_probe_coat_of_arms_source_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
    _coat_of_arms_source_probe_binding_from_snapshot,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


PUBLIC_REVISION = 7
NATIVE_REVISION = 17
SOURCE = "coat_of_arms={ pattern=\"pattern_solid.dds\" color1=blue }"


def _binding() -> dict[str, object]:
    return {
        "mode": "gameplay",
        "snapshot_id": "native:17",
        "revision": PUBLIC_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": 53_246_712,
        "episode_run_id": "coa-probe-fixture",
        "connection_generation": 3,
        "bridge_pid": 4242,
    }


def _frontend_binding() -> dict[str, object]:
    return {
        "mode": "frontend",
        "revision": 0,
        "connection_generation": 3,
        "bridge_pid": 4242,
    }


def _frontend_snapshot_binding() -> dict[str, object]:
    return {
        "mode": "frontend_snapshot",
        "snapshot_id": "native:3",
        "revision": 4,
        "native_revision": 3,
        "date_raw": 53_144_328,
        "connection_generation": 3,
        "bridge_pid": 4242,
    }


def _frontend_snapshot() -> dict[str, object]:
    binding = _frontend_snapshot_binding()
    return {
        "format_version": 1,
        "snapshot_id": binding["snapshot_id"],
        "revision": binding["revision"],
        "native_revision": binding["native_revision"],
        "date_raw": binding["date_raw"],
        "episode_run_id": None,
        "played_character": None,
        "diagnostics": {
            "connection_generation": binding["connection_generation"],
            "bridge_pid": binding["bridge_pid"],
        },
    }


def _frontend_capabilities() -> dict[str, object]:
    return {
        "format_version": 1,
        "backend_id": "native-headless",
        "mode": "native-headless",
        "source": "injected-dll-named-pipe",
        "snapshot": False,
        "visual_fallback": False,
        "bridge_capabilities": [
            PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY
        ],
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
                "capabilities": [
                    PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY
                ],
            },
        },
    }


def _snapshot() -> dict[str, object]:
    binding = _binding()
    return {
        "format_version": 1,
        "snapshot_id": binding["snapshot_id"],
        "revision": binding["revision"],
        "native_revision": binding["native_revision"],
        "date_raw": binding["date_raw"],
        "episode_run_id": binding["episode_run_id"],
        "diagnostics": {
            "connection_generation": binding["connection_generation"],
            "bridge_pid": binding["bridge_pid"],
        },
    }


def _public_result(
    source: str = SOURCE,
    *,
    status: str = "detected",
    detected: bool = True,
    designer_observed: bool = True,
    clipboard_written: bool = True,
    clipboard_readback_matched: bool = True,
    apply_requested: bool = False,
    paste_invoked: bool = False,
    applied: bool = False,
    reason: str | None = None,
    binding: dict[str, object] | None = None,
) -> dict[str, object]:
    encoded = encode_coat_of_arms_source_v1(source)
    return {
        "schema": "coat-of-arms-source-probe-v1",
        "schema_version": 1,
        "step": PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
        "status": status,
        "detected": detected,
        "designer_observed": designer_observed,
        "clipboard_written": clipboard_written,
        "clipboard_readback_matched": clipboard_readback_matched,
        "apply_requested": apply_requested,
        "paste_invoked": paste_invoked,
        "applied": applied,
        "candidate_index": 123,
        "preview_coat_of_arms_handle": 456,
        "active_coat_of_arms_index": 789,
        "reason": reason,
        "source_sha256": encoded.source_sha256,
        "source_bytes": encoded.source_bytes,
        "binding": copy.deepcopy(binding or _binding()),
    }


class _ServiceDriver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, bool]] = []
        self.result = _public_result()
        self.snapshot = _snapshot()

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "coa-probe-fixture",
            "source": "fixture",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [],
            "bridge_capabilities": [
                PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY
            ],
        }

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshot)

    def probe_coat_of_arms_source_v1(
        self, source: str, *, expected_revision: int, apply: bool
    ) -> dict[str, object]:
        self.calls.append((source, expected_revision, apply))
        return copy.deepcopy(self.result)

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        raise AssertionError("coat-of-arms probe must use its typed method")

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("coat-of-arms probe is same-revision")


class _FrontendServiceDriver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, bool]] = []
        self.capability_rows = [_frontend_capabilities()]

    def capabilities(self) -> dict[str, object]:
        if len(self.capability_rows) > 1:
            return copy.deepcopy(self.capability_rows.pop(0))
        return copy.deepcopy(self.capability_rows[0])

    def take_snapshot(self) -> dict[str, object]:
        raise AssertionError("frontend probing must not request a snapshot")

    def probe_coat_of_arms_source_v1(
        self, source: str, *, expected_revision: int, apply: bool
    ) -> dict[str, object]:
        self.calls.append((source, expected_revision, apply))
        return _public_result(binding=_frontend_binding())

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        raise AssertionError("frontend probing must use its typed method")

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("frontend probing is capability-bound")


class CoatOfArmsSourceProbeV1ContractTests(unittest.TestCase):
    def test_native_hook_bootstraps_before_gameplay_snapshot_gate(self) -> None:
        bridge_source = (
            PROJECT_ROOT / "native_bridge" / "src" / "bridge.cpp"
        ).read_text(encoding="utf-8")
        worker = bridge_source.index("DWORD WINAPI WorkerMain(void *) noexcept")
        install = bridge_source.index(
            "InstallCoatOfArmsDesignerProbeHookV1(", worker
        )
        gameplay_lifetime = bridge_source.index(
            "WarEntryApplicationMainMailboxWorkerLifetime mailbox_lifetime",
            worker,
        )
        self.assertLess(worker, install)
        self.assertLess(install, gameplay_lifetime)

        maybe_install = bridge_source.index(
            "void MaybeInstall(const xar::game::Snapshot &snapshot) noexcept"
        )
        lifetime_destructor = bridge_source.index(
            "~WarEntryApplicationMainMailboxWorkerLifetime()", maybe_install
        )
        self.assertNotIn(
            "InstallCoatOfArmsDesignerProbeHookV1(",
            bridge_source[maybe_install:lifetime_destructor],
        )

    def test_probe_never_enters_planner_action_steps(self) -> None:
        self.assertEqual(
            _action_steps([PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY]),
            [],
        )

    def test_apply_requires_an_explicit_boolean(self) -> None:
        self.assertFalse(validate_coat_of_arms_source_probe_apply(False))
        self.assertTrue(validate_coat_of_arms_source_probe_apply(True))
        for invalid in (None, 0, 1, "false"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_coat_of_arms_source_probe_apply(invalid)

    def test_frontend_binding_requires_connected_exact_native_hello(self) -> None:
        self.assertEqual(
            coat_of_arms_source_frontend_binding_from_capabilities(
                {"backends": [_frontend_capabilities()]}
            ),
            _frontend_binding(),
        )
        disconnected = _frontend_capabilities()
        disconnected["diagnostics"]["connected"] = False
        wrong_build = _frontend_capabilities()
        wrong_build["diagnostics"]["hello"]["expected_ck3_sha256"] = (
            "0" * 64
        )
        for invalid in (disconnected, wrong_build):
            with self.assertRaises(ValueError):
                coat_of_arms_source_frontend_binding_from_capabilities(
                    invalid
                )

    def test_frontend_snapshot_binding_omits_episode_but_keeps_revision(self) -> None:
        self.assertEqual(
            _coat_of_arms_source_probe_binding_from_snapshot(
                _frontend_snapshot()
            ),
            _frontend_snapshot_binding(),
        )
        unexpected_episode = _frontend_snapshot_binding()
        unexpected_episode["episode_run_id"] = "not-allowed"
        with self.assertRaises(ValueError):
            normalize_coat_of_arms_source_v1_result(
                _public_result(binding=unexpected_episode),
                expected_source=encode_coat_of_arms_source_v1(SOURCE),
                expected_binding=_frontend_snapshot_binding(),
                expected_apply=False,
            )

    def test_ascii_source_identity_and_128_kib_limit(self) -> None:
        encoded = encode_coat_of_arms_source_v1("coa={ color1=blue }")
        self.assertEqual(encoded.source_bytes, len("coa={ color1=blue }"))
        self.assertEqual(encoded.source_base64, "Y29hPXsgY29sb3IxPWJsdWUgfQ==")
        self.assertEqual(len(encoded.source_sha256), 64)
        self.assertEqual(
            encode_coat_of_arms_source_v1(
                "x" * COAT_OF_ARMS_SOURCE_V1_MAX_BYTES
            ).source_bytes,
            COAT_OF_ARMS_SOURCE_V1_MAX_BYTES,
        )
        for invalid in (
            None,
            b"source",
            "",
            "coa={\0}",
            "蓝色",
            "x" * (COAT_OF_ARMS_SOURCE_V1_MAX_BYTES + 1),
            "\ud800",
        ):
            with self.subTest(invalid=type(invalid).__name__):
                with self.assertRaises(ValueError):
                    encode_coat_of_arms_source_v1(invalid)

    def test_source_line_endings_are_canonical_windows_crlf(self) -> None:
        lf = encode_coat_of_arms_source_v1("coa = {\n color1 = blue\n}\n")
        crlf = encode_coat_of_arms_source_v1(
            "coa = {\r\n color1 = blue\r\n}\r\n"
        )
        legacy_cr = encode_coat_of_arms_source_v1(
            "coa = {\r color1 = blue\r}\r"
        )

        self.assertEqual(lf, crlf)
        self.assertEqual(lf, legacy_cr)
        self.assertEqual(lf.source, "coa = {\r\n color1 = blue\r\n}\r\n")
        self.assertEqual(
            base64.b64decode(lf.source_base64),
            lf.source.encode("ascii"),
        )
        self.assertEqual(lf.source_bytes, len(lf.source.encode("ascii")))

    def test_public_envelope_is_exact_and_semantically_bound(self) -> None:
        encoded = encode_coat_of_arms_source_v1(SOURCE)
        normalized = normalize_coat_of_arms_source_v1_result(
            _public_result(),
            expected_source=encoded,
            expected_binding=_binding(),
            expected_apply=False,
        )
        self.assertTrue(normalized["detected"])
        self.assertTrue(normalized["designer_observed"])

        unavailable = _public_result(
            status="unavailable",
            detected=False,
            designer_observed=False,
            clipboard_written=False,
            clipboard_readback_matched=False,
            reason="designer_not_observed",
        )
        self.assertEqual(
            normalize_coat_of_arms_source_v1_result(
                unavailable,
                expected_source=encoded,
                expected_binding=_binding(),
                expected_apply=False,
            )["reason"],
            "designer_not_observed",
        )

        malformed_rows = []
        extra = _public_result()
        extra["extra"] = True
        malformed_rows.append(extra)
        wrong_hash = _public_result()
        wrong_hash["source_sha256"] = "0" * 64
        malformed_rows.append(wrong_hash)
        impossible = _public_result(designer_observed=False)
        malformed_rows.append(impossible)
        unexplained = _public_result(
            detected=False,
            designer_observed=False,
            reason=None,
        )
        malformed_rows.append(unexplained)
        moved = _public_result()
        moved["binding"]["revision"] = PUBLIC_REVISION + 1
        malformed_rows.append(moved)
        for malformed in malformed_rows:
            with self.subTest(fields=sorted(malformed)):
                with self.assertRaises(ValueError):
                    normalize_coat_of_arms_source_v1_result(
                        malformed,
                        expected_source=encoded,
                        expected_binding=_binding(),
                        expected_apply=False,
                    )

    def test_native_envelope_rejects_source_or_revision_drift(self) -> None:
        encoded = encode_coat_of_arms_source_v1(SOURCE)
        raw = {
            "step": PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
            "accepted": True,
            "status": "not_detected",
            "query_sequence": 1,
            "snapshot_revision": NATIVE_REVISION,
            "coat_of_arms_probe": {
                "schema": "xar.ck3.coat-of-arms-designer-probe.v1",
                "schema_version": 1,
                "status": "not_detected",
                "date_raw": _binding()["date_raw"],
                "source_bytes": encoded.source_bytes,
                "designer_observed": True,
                "clipboard_written": True,
                "clipboard_readback_matched": True,
                "detected": False,
                "apply_requested": False,
                "paste_invoked": False,
                "applied": False,
                "candidate_index": 0,
                "preview_coat_of_arms_handle": 0,
                "active_coat_of_arms_index": 789,
                "reason": "engine_did_not_detect_coat_of_arms",
                "provenance": {
                    "backend_id": (
                        "ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1"
                    ),
                },
            },
            "backend_id": "native-headless",
        }
        self.assertFalse(
            normalize_native_coat_of_arms_source_v1_result(
                raw,
                expected_source=encoded,
                expected_native_revision=NATIVE_REVISION,
                expected_date_raw=_binding()["date_raw"],
                expected_apply=False,
            )["detected"]
        )
        malformed_rows = []
        wrong_bytes = copy.deepcopy(raw)
        wrong_bytes["coat_of_arms_probe"]["source_bytes"] += 1
        malformed_rows.append(wrong_bytes)
        malformed_rows.append(
            {**raw, "snapshot_revision": NATIVE_REVISION + 1}
        )
        malformed_rows.append({**raw, "accepted": False})
        for malformed in malformed_rows:
            with self.assertRaises(ValueError):
                normalize_native_coat_of_arms_source_v1_result(
                    malformed,
                    expected_source=encoded,
                    expected_native_revision=NATIVE_REVISION,
                    expected_date_raw=_binding()["date_raw"],
                    expected_apply=False,
                )

    def test_service_and_facade_preserve_source_and_revision(self) -> None:
        driver = _ServiceDriver()
        result = _ck3_probe_coat_of_arms_source_v1(
            GameplayBridgeService(driver),
            SOURCE,
            PUBLIC_REVISION,
            False,
        )
        self.assertTrue(result["detected"])
        self.assertEqual(driver.calls, [(SOURCE, PUBLIC_REVISION, False)])
        self.assertEqual(result["binding"], _binding())

        with self.assertRaises(PreSubmissionRevisionMismatchError):
            GameplayBridgeService(driver).probe_coat_of_arms_source_v1(
                SOURCE,
                expected_revision=PUBLIC_REVISION - 1,
                apply=False,
            )
        driver.result["source_bytes"] += 1
        with self.assertRaisesRegex(
            BridgeUnavailableError, "result is malformed"
        ):
            GameplayBridgeService(driver).probe_coat_of_arms_source_v1(
                SOURCE,
                expected_revision=PUBLIC_REVISION,
                apply=False,
            )

    def test_service_frontend_uses_stable_capabilities_without_snapshot(self) -> None:
        driver = _FrontendServiceDriver()
        result = GameplayBridgeService(driver).probe_coat_of_arms_source_v1(
            SOURCE,
            expected_revision=0,
            apply=False,
        )
        self.assertEqual(result["binding"], _frontend_binding())
        self.assertEqual(driver.calls, [(SOURCE, 0, False)])

        drifted = _FrontendServiceDriver()
        changed = _frontend_capabilities()
        changed["diagnostics"]["connection_generation"] = 4
        drifted.capability_rows.append(changed)
        with self.assertRaisesRegex(
            BridgeUnavailableError, "crossed its revision binding"
        ):
            GameplayBridgeService(
                drifted
            ).probe_coat_of_arms_source_v1(
                SOURCE,
                expected_revision=0,
                apply=False,
            )

    def test_service_accepts_ruler_designer_frontend_snapshot_binding(self) -> None:
        driver = _ServiceDriver()
        driver.snapshot = _frontend_snapshot()
        driver.result = _public_result(
            binding=_frontend_snapshot_binding()
        )
        result = GameplayBridgeService(driver).probe_coat_of_arms_source_v1(
            SOURCE,
            expected_revision=4,
            apply=False,
        )
        self.assertEqual(result["binding"], _frontend_snapshot_binding())
        self.assertEqual(driver.calls, [(SOURCE, 4, False)])

    def test_native_driver_sends_source_base64_and_apply(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        snapshot = _snapshot()
        driver.take_snapshot = lambda: copy.deepcopy(snapshot)
        calls: list[dict[str, object]] = []
        encoded = encode_coat_of_arms_source_v1(SOURCE)

        def execute(
            step: str,
            *,
            expected_revision: int,
            required_capability: str,
            request_fields: dict[str, object],
            allow_frontend_revision_zero: bool,
        ) -> dict[str, object]:
            calls.append(
                {
                    "step": step,
                    "expected_revision": expected_revision,
                    "required_capability": required_capability,
                    "request_fields": dict(request_fields),
                    "allow_frontend_revision_zero": (
                        allow_frontend_revision_zero
                    ),
                }
            )
            return {
                "step": PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
                "accepted": True,
                "status": "applied",
                "query_sequence": 1,
                "snapshot_revision": NATIVE_REVISION,
                "coat_of_arms_probe": {
                    "schema": "xar.ck3.coat-of-arms-designer-probe.v1",
                    "schema_version": 1,
                    "status": "applied",
                    "date_raw": _binding()["date_raw"],
                    "source_bytes": encoded.source_bytes,
                    "designer_observed": True,
                    "clipboard_written": True,
                    "clipboard_readback_matched": True,
                    "detected": True,
                    "apply_requested": True,
                    "paste_invoked": True,
                    "applied": True,
                    "candidate_index": 123,
                    "preview_coat_of_arms_handle": 456,
                    "active_coat_of_arms_index": 123,
                    "reason": None,
                    "provenance": {
                        "backend_id": (
                            "ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1"
                        ),
                    },
                },
                "backend_id": "native-headless",
            }

        driver._execute_primitive_step = execute
        result = driver.probe_coat_of_arms_source_v1(
            SOURCE,
            expected_revision=PUBLIC_REVISION,
            apply=True,
        )
        self.assertTrue(result["detected"])
        self.assertTrue(result["applied"])
        self.assertEqual(
            calls,
            [
                {
                    "step": PROBE_COAT_OF_ARMS_SOURCE_V1_STEP,
                    "expected_revision": PUBLIC_REVISION,
                    "required_capability": (
                        PROBE_COAT_OF_ARMS_SOURCE_V1_CAPABILITY
                    ),
                    "request_fields": {
                        "source_base64": encoded.source_base64,
                        "apply": True,
                    },
                    "allow_frontend_revision_zero": False,
                }
            ],
        )

    def test_native_driver_frontend_sends_revision_zero_without_snapshot(self) -> None:
        driver = object.__new__(NativeHeadlessGameplayDriver)
        driver.capabilities = lambda: copy.deepcopy(_frontend_capabilities())

        def no_snapshot() -> dict[str, object]:
            raise AssertionError("frontend driver must not request a snapshot")

        driver.take_snapshot = no_snapshot
        calls: list[dict[str, object]] = []
        encoded = encode_coat_of_arms_source_v1(SOURCE)

        def execute(
            step: str,
            *,
            expected_revision: int,
            required_capability: str,
            request_fields: dict[str, object],
            allow_frontend_revision_zero: bool,
        ) -> dict[str, object]:
            calls.append(
                {
                    "expected_revision": expected_revision,
                    "allow_frontend_revision_zero": (
                        allow_frontend_revision_zero
                    ),
                }
            )
            return {
                "step": step,
                "accepted": True,
                "status": "detected",
                "query_sequence": 2,
                "snapshot_revision": 0,
                "coat_of_arms_probe": {
                    "schema": "xar.ck3.coat-of-arms-designer-probe.v1",
                    "schema_version": 1,
                    "status": "detected",
                    "date_raw": 0,
                    "source_bytes": encoded.source_bytes,
                    "designer_observed": True,
                    "clipboard_written": True,
                    "clipboard_readback_matched": True,
                    "detected": True,
                    "apply_requested": False,
                    "paste_invoked": False,
                    "applied": False,
                    "candidate_index": 123,
                    "preview_coat_of_arms_handle": 456,
                    "active_coat_of_arms_index": 789,
                    "reason": None,
                    "provenance": {
                        "backend_id": (
                            "ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1"
                        ),
                    },
                },
                "backend_id": "native-headless",
            }

        driver._execute_primitive_step = execute
        result = driver.probe_coat_of_arms_source_v1(
            SOURCE,
            expected_revision=0,
            apply=False,
        )
        self.assertEqual(result["binding"], _frontend_binding())
        self.assertEqual(
            calls,
            [
                {
                    "expected_revision": 0,
                    "allow_frontend_revision_zero": True,
                }
            ],
        )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CoatOfArmsSourceProbeV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_closed_schema_and_calls_tool(self) -> None:
        from mcp import Client

        driver = _ServiceDriver()
        async with Client(create_server(driver)) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            tool = tools["ck3_probe_coat_of_arms_source_v1"]
            self.assertEqual(
                set(tool.input_schema["required"]),
                {"source", "expected_revision", "apply"},
            )
            self.assertFalse(tool.input_schema["additionalProperties"])
            result = await client.call_tool(
                "ck3_probe_coat_of_arms_source_v1",
                {
                    "source": SOURCE,
                    "expected_revision": PUBLIC_REVISION,
                    "apply": False,
                },
            )
            self.assertFalse(result.is_error)
            self.assertTrue(result.structured_content["detected"])
            rejected = await client.call_tool(
                "ck3_probe_coat_of_arms_source_v1",
                {
                    "source": SOURCE,
                    "expected_revision": PUBLIC_REVISION,
                    "apply": False,
                    "unexpected": True,
                },
            )
            self.assertTrue(rejected.is_error)


if __name__ == "__main__":
    unittest.main()
