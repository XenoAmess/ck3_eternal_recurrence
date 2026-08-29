from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_center_map_on_landed_title_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.title_map_navigation_contract import (
    CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY,
    CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
    TITLE_MAP_NAVIGATION_V1_BACKEND_ID,
    TITLE_MAP_NAVIGATION_V1_COMPLETION_PREDICATE,
    TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
    TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
    normalize_native_title_map_navigation_v1_result,
    normalize_title_map_navigation_v1_result,
    validate_landed_title_key,
)


STEP = CENTER_MAP_ON_LANDED_TITLE_V1_STEP
CAPABILITY = CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
NATIVE_REVISION = 17
PUBLIC_REVISION = 4
DATE_RAW = 53_182_008
PLAYER_CHARACTER_ID = 12_345
FIXTURE_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "title_map_navigation_v1_static.json"
)


def _title(title_key: str) -> dict[str, object]:
    if title_key == "b_kaifeng":
        title_id, tier_raw, tier_key = 16_777_219, 1, "barony"
        bounds_extent = [1_632, -947, 1_632, -947]
        map_x_adjustment = 0
    else:
        title_id, tier_raw, tier_key = 16_777_218, 2, "county"
        bounds_extent = [1_600, -1_000, 1_674, -895]
        map_x_adjustment = 5
    return {
        "key": title_key,
        "title_id": title_id,
        "tier_raw": tier_raw,
        "tier_key": tier_key,
        "anchor_kind": "title_bounds_center",
        "capital_province_id": 9_822,
        "bounds_extent": bounds_extent,
        "map_x_adjustment": map_x_adjustment,
    }


def _source() -> dict[str, object]:
    return {
        "game_version": TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
        "executable_sha256": TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
        "backend_id": TITLE_MAP_NAVIGATION_V1_BACKEND_ID,
    }


def _result(
    title_key: str = "c_bianzhou",
    *,
    status: str = "centered",
    binding: dict[str, object],
) -> dict[str, object]:
    already = status == "already_centered"
    return {
        "schema_version": 1,
        "step": STEP,
        "accepted": True,
        "status": status,
        "title": _title(title_key),
        "binding": copy.deepcopy(binding),
        "native_action_ack": {
            "sequence": None if already else 9,
            "status": "not_needed" if already else "dispatched",
        },
        "camera_center": {
            "status": status,
            "postcondition_verified": True,
            "expected_position_xyz": [1_632.0, 0.0, -947.0],
            "current_state": [1_632.0, 0.0, -947.0, 0.75, 0.0, 1.0],
            "target_state": [1_632.0, 0.0, -947.0, 0.75, 0.0, 1.0],
            "zoom_index": 3,
            "expected_zoom_value": 0.75,
            "settled": True,
            "target_write_blocked": False,
            "completion_predicate": (
                TITLE_MAP_NAVIGATION_V1_COMPLETION_PREDICATE
            ),
        },
        "source": _source(),
    }


def _native_binding() -> dict[str, object]:
    return {
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": NATIVE_REVISION,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
    }


def _public_binding(
    *,
    revision: int = PUBLIC_REVISION,
    snapshot_id: str | None = None,
) -> dict[str, object]:
    return {
        "snapshot_id": snapshot_id or f"title-map-fixture:{revision}",
        "revision": revision,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "episode_run_id": "native-12345-fixture",
        "connection_generation": 2,
    }


def _raw_result(
    title_key: str = "c_bianzhou",
    *,
    status: str = "centered",
) -> dict[str, object]:
    return {
        **_result(title_key, status=status, binding=_native_binding()),
        "backend_id": "native-headless",
    }


class TitleMapNavigationV1ContractTests(unittest.TestCase):
    def test_static_fixture_is_explicitly_non_live_and_strictly_valid(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(fixture["evidence_level"], "static-ready")
        self.assertIs(fixture["live_claim"], False)
        self.assertEqual(len(fixture["cases"]), 2)
        for case in fixture["cases"]:
            with self.subTest(case=case["name"]):
                result = case["result"]
                normalized = normalize_title_map_navigation_v1_result(
                    result,
                    expected_title_key=case["title_key"],
                    expected_binding=result["binding"],
                )
                self.assertEqual(normalized, result)

    def test_title_key_is_canonical_utf8_and_byte_bounded(self) -> None:
        self.assertEqual(validate_landed_title_key("c_bianzhou"), "c_bianzhou")
        self.assertEqual(
            len(validate_landed_title_key("c_" + "a" * 1_022).encode("utf-8")),
            1_024,
        )
        for invalid in (
            None,
            True,
            7,
            "",
            "汴州",
            "c_Bianzhou",
            "county_bianzhou",
            "c_bian-zhou",
            "c_" + "a" * 1_023,
            "c_\ud800",
        ):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(ValueError):
                    validate_landed_title_key(invalid)

    def test_native_and_public_result_parsers_accept_both_success_states(self) -> None:
        for status, key in (
            ("centered", "c_bianzhou"),
            ("already_centered", "b_kaifeng"),
        ):
            with self.subTest(status=status):
                native = normalize_native_title_map_navigation_v1_result(
                    _raw_result(key, status=status),
                    expected_title_key=key,
                    expected_snapshot_id=f"native:{NATIVE_REVISION}",
                    expected_native_revision=NATIVE_REVISION,
                    expected_date_raw=DATE_RAW,
                )
                self.assertEqual(native["status"], status)
                public = _result(
                    key,
                    status=status,
                    binding=_public_binding(),
                )
                normalized = normalize_title_map_navigation_v1_result(
                    public,
                    expected_title_key=key,
                    expected_binding=_public_binding(),
                )
                self.assertEqual(normalized, public)

    def test_result_parser_rejects_schema_binding_and_postcondition_drift(self) -> None:
        mutations = {
            "extra_root": lambda row: row.__setitem__("extra", True),
            "wrong_key": lambda row: row["title"].__setitem__(
                "key", "c_luoyang"
            ),
            "zero_title": lambda row: row["title"].__setitem__("title_id", 0),
            "tier_pair": lambda row: row["title"].__setitem__(
                "tier_key", "duchy"
            ),
            "anchor_kind": lambda row: row["title"].__setitem__(
                "anchor_kind", "capital_province"
            ),
            "capital_provenance": lambda row: row["title"].__setitem__(
                "capital_province_id", 0
            ),
            "bounds_shape": lambda row: row["title"].__setitem__(
                "bounds_extent", [1_600, -1_000, 1_674]
            ),
            "bounds_inverted": lambda row: row["title"].__setitem__(
                "bounds_extent", [1_675, -1_000, 1_674, -895]
            ),
            "bounds_center_mismatch": lambda row: row["title"].__setitem__(
                "bounds_extent", [1_600, -1_000, 1_676, -895]
            ),
            "map_x_adjustment": lambda row: row["title"].__setitem__(
                "map_x_adjustment", 6
            ),
            "binding": lambda row: row["binding"].__setitem__(
                "date_raw", DATE_RAW + 1
            ),
            "ack": lambda row: row["native_action_ack"].__setitem__(
                "status", "not_needed"
            ),
            "camera_status": lambda row: row["camera_center"].__setitem__(
                "status", "already_centered"
            ),
            "camera_unverified": lambda row: row["camera_center"].__setitem__(
                "postcondition_verified", False
            ),
            "zoom_index": lambda row: row["camera_center"].__setitem__(
                "zoom_index", -1
            ),
            "zoom_value_mismatch": lambda row: row[
                "camera_center"
            ].__setitem__("expected_zoom_value", 0.5),
            "zoom_value_nan": lambda row: row["camera_center"].__setitem__(
                "expected_zoom_value", float("nan")
            ),
            "expected_position_nan": lambda row: row[
                "camera_center"
            ].__setitem__(
                "expected_position_xyz", [float("nan"), 0.0, -947.0]
            ),
            "current_state_shape": lambda row: row[
                "camera_center"
            ].__setitem__("current_state", [1_632.0, 0.0, -947.0]),
            "current_state_not_settled": lambda row: row[
                "camera_center"
            ]["current_state"].__setitem__(5, 0.5),
            "expected_position_mismatch": lambda row: row[
                "camera_center"
            ]["expected_position_xyz"].__setitem__(0, 1_633.0),
            "settled_false": lambda row: row["camera_center"].__setitem__(
                "settled", False
            ),
            "target_write_blocked": lambda row: row[
                "camera_center"
            ].__setitem__("target_write_blocked", True),
            "predicate": lambda row: row["camera_center"].__setitem__(
                "completion_predicate", "two-equal-pixels"
            ),
            "build": lambda row: row["source"].__setitem__(
                "executable_sha256", "A" * 64
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                result = _result(binding=_public_binding())
                mutate(result)
                with self.assertRaises(ValueError):
                    normalize_title_map_navigation_v1_result(
                        result,
                        expected_title_key="c_bianzhou",
                        expected_binding=_public_binding(),
                    )

        no_capital = _result(binding=_public_binding())
        no_capital["title"]["capital_province_id"] = None
        normalized = normalize_title_map_navigation_v1_result(
            no_capital,
            expected_title_key="c_bianzhou",
            expected_binding=_public_binding(),
        )
        self.assertIsNone(normalized["title"]["capital_province_id"])

    def test_bounds_center_uses_native_int32_wrap_and_toward_zero_rules(
        self,
    ) -> None:
        cases = (
            (
                [2_147_483_640, -2_147_483_648, 2_147_483_647, -2_147_483_647],
                0,
                [-4.0, 0.0, 0.0],
            ),
            (
                [0, 0, 0, 0],
                -2_147_483_648,
                [-2_147_483_648.0, 0.0, 0.0],
            ),
        )
        for bounds, adjustment, expected in cases:
            with self.subTest(bounds=bounds, adjustment=adjustment):
                result = _result(binding=_public_binding())
                result["title"]["bounds_extent"] = bounds
                result["title"]["map_x_adjustment"] = adjustment
                result["camera_center"]["expected_position_xyz"] = expected
                for state_name in ("current_state", "target_state"):
                    tail = result["camera_center"][state_name][3:]
                    result["camera_center"][state_name] = expected + tail
                normalized = normalize_title_map_navigation_v1_result(
                    result,
                    expected_title_key="c_bianzhou",
                    expected_binding=_public_binding(),
                )
                self.assertEqual(
                    normalized["camera_center"]["expected_position_xyz"],
                    expected,
                )


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_title_map_navigation_v1_fixture"
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


def _hello(*, advertise: bool = True) -> dict[str, object]:
    capabilities = ["game.state.snapshot"]
    if advertise:
        capabilities.append(CAPABILITY)
    return {
        "type": "hello",
        "protocol_version": 1,
        "bridge_version": "0.1.0",
        "pid": 6_767,
        "session_generation": 0,
        "game_version": TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
        "expected_ck3_version": TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
        "executable_sha256": TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
        "expected_ck3_sha256": TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
        "capabilities": capabilities,
    }


def _semantic_snapshot(
    revision: int = NATIVE_REVISION,
    *,
    paused: bool = True,
    map_ready: bool = True,
    date_raw: int = DATE_RAW,
) -> dict[str, object]:
    return {
        "type": "state_snapshot",
        "protocol_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "state": {
            "phase": "map_hud",
            "date": "1066.10.16",
            "date_raw": date_raw,
            "speed": 1,
            "paused": paused,
            "map_ready": map_ready,
            "history": [],
            "active_event": None,
            "pending_character_interaction": None,
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


def _native_driver(
    *,
    advertise: bool = True,
    paused: bool = True,
    map_ready: bool = True,
    timeout: float = 0.05,
) -> tuple[NativeHeadlessGameplayDriver, _FakeEndpoint]:
    endpoint = _FakeEndpoint()
    driver = NativeHeadlessGameplayDriver(
        endpoint.pipe_name,
        endpoint=endpoint,
        command_timeout_seconds=timeout,
    )
    endpoint.publish(_hello(advertise=advertise))
    endpoint.publish(
        _semantic_snapshot(paused=paused, map_ready=map_ready)
    )
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


def _execute_frames(endpoint: _FakeEndpoint) -> list[dict[str, object]]:
    return [
        frame for frame in endpoint.frames if frame.get("type") == "execute_step"
    ]


class TitleMapNavigationV1NativeDriverTests(unittest.TestCase):
    def test_capability_is_projected_but_never_becomes_an_action_step(self) -> None:
        driver, _endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertIn(CAPABILITY, capabilities["bridge_capabilities"])
        self.assertNotIn(STEP, capabilities["action_steps"])
        self.assertEqual(_action_steps([CAPABILITY], paused=True), [])

    def test_typed_driver_sends_fixed_step_and_separate_title_key(self) -> None:
        driver, endpoint = _native_driver()
        _answer_with(endpoint, _raw_result)
        revision = int(driver.take_snapshot()["revision"])
        result = driver.center_map_on_landed_title_v1(
            "c_bianzhou",
            expected_revision=revision,
        )

        command = _execute_frames(endpoint)[0]
        self.assertEqual(
            set(command),
            {
                "type",
                "protocol_version",
                "request_id",
                "step",
                "expected_revision",
                "title_key",
            },
        )
        self.assertEqual(command["step"], STEP)
        self.assertEqual(command["title_key"], "c_bianzhou")
        self.assertEqual(command["expected_revision"], NATIVE_REVISION)
        self.assertEqual(result["status"], "centered")
        self.assertEqual(result["binding"]["revision"], revision)
        self.assertEqual(
            result["binding"]["native_revision"], NATIVE_REVISION
        )
        self.assertEqual(
            result["binding"]["connection_generation"], 1
        )
        self.assertTrue(result["binding"]["episode_run_id"])
        self.assertNotIn("backend_id", result)

    def test_generic_step_cannot_bypass_the_typed_request(self) -> None:
        driver, endpoint = _native_driver()
        with self.assertRaisesRegex(UnsupportedStepError, "typed driver"):
            driver.execute_step(
                STEP,
                expected_revision=int(driver.take_snapshot()["revision"]),
            )
        self.assertEqual(_execute_frames(endpoint), [])

    def test_preflight_rejects_invalid_state_revision_and_capability(self) -> None:
        cases = (
            ("unpaused", {"paused": False}, BridgeUnavailableError),
            ("map", {"map_ready": False}, BridgeUnavailableError),
        )
        for label, kwargs, error_type in cases:
            with self.subTest(label=label):
                driver, endpoint = _native_driver(**kwargs)
                with self.assertRaises(error_type):
                    driver.center_map_on_landed_title_v1(
                        "c_bianzhou",
                        expected_revision=int(
                            driver.take_snapshot()["revision"]
                        ),
                    )
                self.assertEqual(_execute_frames(endpoint), [])

        driver, endpoint = _native_driver(
            advertise=False,
            paused=False,
            map_ready=False,
        )
        with self.assertRaisesRegex(
            UnsupportedStepError, "capability_not_available"
        ):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou",
                expected_revision=NATIVE_REVISION,
            )
        self.assertEqual(_execute_frames(endpoint), [])

        driver, endpoint = _native_driver()
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou",
                expected_revision=int(driver.take_snapshot()["revision"]) - 1,
            )
        self.assertEqual(_execute_frames(endpoint), [])

    def test_typed_rejections_remain_distinguishable(self) -> None:
        for rejection in ("title_key_not_found", "title_not_centerable"):
            with self.subTest(rejection=rejection):
                driver, endpoint = _native_driver()

                def answer(frame: dict[str, object]) -> None:
                    if frame.get("type") == "execute_step":
                        endpoint.publish(
                            {
                                "type": "command_result",
                                "protocol_version": 1,
                                "request_id": frame["request_id"],
                                "ok": False,
                                "error": rejection,
                            }
                        )

                endpoint.send_hook = answer
                with self.assertRaises(BridgeUnavailableError) as rejected:
                    driver.center_map_on_landed_title_v1(
                        "c_bianzhou",
                        expected_revision=int(
                            driver.take_snapshot()["revision"]
                        ),
                    )
                self.assertEqual(
                    getattr(rejected.exception, "native_error", None),
                    rejection,
                )

    def test_timeout_unknown_rejection_malformed_result_and_drift_are_red(self) -> None:
        driver, _endpoint = _native_driver(timeout=0.01)
        with self.assertRaisesRegex(BridgeUnavailableError, "timed out"):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = _native_driver()

        def unknown(frame: dict[str, object]) -> None:
            if frame.get("type") == "execute_step":
                endpoint.publish(
                    {
                        "type": "command_result",
                        "protocol_version": 1,
                        "request_id": frame["request_id"],
                        "ok": False,
                        "error": "untyped_failure_text",
                    }
                )

        endpoint.send_hook = unknown
        with self.assertRaisesRegex(BridgeUnavailableError, "unknown rejection"):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = _native_driver()

        def malformed() -> dict[str, object]:
            value = _raw_result()
            value["camera_center"]["postcondition_verified"] = False
            return value

        _answer_with(endpoint, malformed)
        with self.assertRaisesRegex(BridgeUnavailableError, "malformed"):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

        driver, endpoint = _native_driver()

        def drift() -> dict[str, object]:
            value = _raw_result()
            endpoint.publish(_semantic_snapshot(NATIVE_REVISION + 1))
            return value

        _answer_with(endpoint, drift)
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            driver.center_map_on_landed_title_v1(
                "c_bianzhou",
                expected_revision=int(driver.take_snapshot()["revision"]),
            )

    def test_configured_hybrid_rebinds_public_revision_without_visual_fallback(
        self,
    ) -> None:
        starting = {
            "format_version": 1,
            **_public_binding(),
            "paused": True,
            "map_ready": True,
            "history": [],
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "backend_revisions": {"fast": 2, "baseline": 0},
            "diagnostics": {
                "connection_generation": 2,
                "hello": {
                    "expected_ck3_version": (
                        TITLE_MAP_NAVIGATION_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

        class NativeStub:
            def __init__(self) -> None:
                self.calls: list[tuple[str, int]] = []

            def capabilities(self) -> dict[str, object]:
                return {"bridge_capabilities": [CAPABILITY]}

            def center_map_on_landed_title_v1(
                self, title_key: str, *, expected_revision: int
            ) -> dict[str, object]:
                self.calls.append((title_key, expected_revision))
                return _result(
                    title_key,
                    binding={
                        **_public_binding(
                            revision=2,
                            snapshot_id="native-public:2",
                        ),
                    },
                )

        class DelegateStub:
            def take_snapshot(self) -> dict[str, object]:
                return copy.deepcopy(starting)

        native = NativeStub()
        wrapper = object.__new__(ConfiguredHybridFallbackDriver)
        wrapper.native = native
        wrapper._delegate = DelegateStub()
        result = wrapper.center_map_on_landed_title_v1(
            "c_bianzhou",
            expected_revision=PUBLIC_REVISION,
        )

        self.assertEqual(native.calls, [("c_bianzhou", 2)])
        self.assertEqual(result["binding"], _public_binding())
        self.assertEqual(result["source"], _source())


class _ServiceDriver:
    def __init__(
        self,
        *,
        advertise: bool = True,
        paused: bool = True,
        map_ready: bool = True,
        drift: bool = False,
        malformed: bool = False,
        build_drift: bool = False,
        malicious_action_projection: bool = False,
    ) -> None:
        self.advertise = advertise
        self.paused = paused
        self.map_ready = map_ready
        self.drift = drift
        self.malformed = malformed
        self.build_drift = build_drift
        self.malicious_action_projection = malicious_action_projection
        self.snapshot_calls = 0
        self.typed_calls: list[tuple[str, int]] = []
        self.generic_calls: list[tuple[str, int | None]] = []

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": (
                [STEP] if self.malicious_action_projection else []
            ),
            "bridge_capabilities": [CAPABILITY] if self.advertise else [],
        }

    def take_snapshot(self) -> dict[str, object]:
        self.snapshot_calls += 1
        revision = (
            PUBLIC_REVISION + 1
            if self.drift and self.snapshot_calls > 1
            else PUBLIC_REVISION
        )
        binding = _public_binding(revision=revision)
        return {
            "format_version": 1,
            **binding,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "paused": self.paused,
            "map_ready": self.map_ready,
            "history": [],
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "diagnostics": {
                "connection_generation": binding[
                    "connection_generation"
                ],
                "hello": {
                    "game_version": TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
                    "expected_ck3_version": (
                        TITLE_MAP_NAVIGATION_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        "A" * 64
                        if self.build_drift
                        else TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
                    ),
                },
            },
        }

    def center_map_on_landed_title_v1(
        self,
        title_key: str,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        self.typed_calls.append((title_key, expected_revision))
        result = _result(title_key, binding=_public_binding())
        if self.malformed:
            result["camera_center"]["postcondition_verified"] = False
        return result

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.generic_calls.append((step, expected_revision))
        return {"accepted": True}

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("title-map navigation must not wait for revision")


class TitleMapNavigationV1ServiceTests(unittest.TestCase):
    def test_official_facade_and_service_return_exact_public_binding(self) -> None:
        driver = _ServiceDriver()
        result = _ck3_center_map_on_landed_title_v1(
            GameplayBridgeService(driver),
            "c_bianzhou",
            PUBLIC_REVISION,
        )
        self.assertEqual(driver.typed_calls, [("c_bianzhou", PUBLIC_REVISION)])
        self.assertEqual(result["binding"], _public_binding())
        self.assertEqual(
            result["title"]["bounds_extent"],
            [1_600, -1_000, 1_674, -895],
        )

    def test_generic_service_step_is_rejected_even_if_backend_projects_it(self) -> None:
        driver = _ServiceDriver(malicious_action_projection=True)
        service = GameplayBridgeService(driver)
        with self.assertRaisesRegex(UnsupportedStepError, "typed MCP facade"):
            service.execute_step(STEP, expected_revision=PUBLIC_REVISION)
        self.assertEqual(driver.generic_calls, [])

    def test_service_rejects_preflight_result_and_binding_failures(self) -> None:
        unsupported_driver = _ServiceDriver(
            advertise=False,
            paused=False,
            map_ready=False,
        )
        cases = (
            (
                "unsupported",
                unsupported_driver,
                UnsupportedStepError,
                "capability_not_available",
            ),
            (
                "unpaused",
                _ServiceDriver(paused=False),
                BridgeUnavailableError,
                "paused",
            ),
            (
                "map",
                _ServiceDriver(map_ready=False),
                BridgeUnavailableError,
                "map-ready",
            ),
            (
                "build",
                _ServiceDriver(build_drift=True),
                BridgeUnavailableError,
                "build mirror",
            ),
            (
                "malformed",
                _ServiceDriver(malformed=True),
                BridgeUnavailableError,
                "malformed",
            ),
            (
                "drift",
                _ServiceDriver(drift=True),
                BridgeUnavailableError,
                "crossed",
            ),
        )
        for label, driver, error_type, message in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(error_type, message):
                    GameplayBridgeService(
                        driver
                    ).center_map_on_landed_title_v1(
                        "c_bianzhou",
                        expected_revision=PUBLIC_REVISION,
                    )
        self.assertEqual(unsupported_driver.snapshot_calls, 0)

        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).center_map_on_landed_title_v1(
                "c_bianzhou",
                expected_revision=PUBLIC_REVISION - 1,
            )
        for invalid_revision in (True, -1, 2**64, 1.5, None):
            with self.subTest(invalid_revision=invalid_revision):
                with self.assertRaises(ValueError):
                    GameplayBridgeService(
                        _ServiceDriver()
                    ).center_map_on_landed_title_v1(
                        "c_bianzhou",
                        expected_revision=invalid_revision,
                    )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class TitleMapNavigationV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_only_the_typed_tool(self) -> None:
        from mcp import Client

        driver = _ServiceDriver(malicious_action_projection=True)
        server = create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            self.assertIn("ck3_center_map_on_landed_title_v1", tools)
            schema = tools[
                "ck3_center_map_on_landed_title_v1"
            ].input_schema
            self.assertEqual(
                set(schema["required"]), {"title_key", "expected_revision"}
            )
            result = await client.call_tool(
                "ck3_center_map_on_landed_title_v1",
                {
                    "title_key": "c_bianzhou",
                    "expected_revision": PUBLIC_REVISION,
                },
            )
            generic = await client.call_tool(
                "ck3_execute_step",
                {
                    "step": STEP,
                    "expected_revision": PUBLIC_REVISION,
                },
            )

        self.assertFalse(result.is_error)
        self.assertEqual(
            result.structured_content["status"], "centered"
        )
        self.assertEqual(
            result.structured_content["title"]["key"], "c_bianzhou"
        )
        self.assertTrue(generic.is_error)
        self.assertEqual(driver.generic_calls, [])

    async def test_typed_tool_fails_closed_when_native_capability_is_absent(
        self,
    ) -> None:
        from mcp import Client

        driver = _ServiceDriver(
            advertise=False,
            paused=False,
            map_ready=False,
        )
        server = create_server(driver)
        async with Client(server) as client:
            result = await client.call_tool(
                "ck3_center_map_on_landed_title_v1",
                {
                    "title_key": "c_bianzhou",
                    "expected_revision": PUBLIC_REVISION,
                },
            )

        self.assertTrue(result.is_error)
        self.assertEqual(driver.snapshot_calls, 0)
        self.assertEqual(driver.typed_calls, [])
        self.assertEqual(driver.generic_calls, [])


if __name__ == "__main__":
    unittest.main()
