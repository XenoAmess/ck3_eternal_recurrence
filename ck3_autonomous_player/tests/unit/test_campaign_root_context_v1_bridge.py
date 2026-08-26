from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.campaign_root_context_contract import (
    CAMPAIGN_ROOT_CONTEXT_V1_BACKEND_ID,
    CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256,
    CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
    normalize_campaign_root_context_v1,
)
from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_campaign_root_context_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


NATIVE_REVISION = 17
PUBLIC_REVISION = 4
DATE_RAW = 53_182_008
PLAYER_CHARACTER_ID = 12345
STEP = QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
UNAVAILABLE_REASONS = (
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "player_identity_unavailable",
    "player_character_generation_mismatch",
    "primary_title_unavailable",
    "capital_unavailable",
    "lieges_unavailable",
    "government_flags_unavailable",
    "selected_game_rule_tokens_unavailable",
    "state_changed",
    "internal_error",
)


def _readiness(ready: bool) -> dict[str, bool]:
    return {
        "player_identity_ready": ready,
        "primary_title_ready": ready,
        "capital_ready": ready,
        "lieges_ready": ready,
        "government_ready": ready,
        "selected_game_rule_tokens_ready": ready,
        "same_frame_ready": ready,
        "ready": ready,
    }


def _provenance() -> dict[str, str]:
    return {
        "game_version": CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
        "executable_sha256": (
            CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
        ),
        "backend_id": CAMPAIGN_ROOT_CONTEXT_V1_BACKEND_ID,
        "primary_title_rva": "0x25F3350",
        "capital_province_rva": "0x2606760",
        "immediate_liege_rva": "0x2613480",
        "top_liege_rva": "0x2613600",
        "government_rva": "0x26165B0",
        "selected_game_rule_service_slot_rva": "0x5754B48",
    }


def _frame(
    status: str = "available",
    *,
    unavailable_reason: str = "state_changed",
) -> dict[str, object]:
    available = status == "available"
    return {
        "schema_version": 1,
        "status": status,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "local_player_id": 0 if available else None,
        "player_character_id": PLAYER_CHARACTER_ID if available else None,
        "player_character_alive": True if available else None,
        "primary_title": (
            {
                "title_id": 67_890,
                "tier_raw": 6,
                "tier_key": "hegemony",
            }
            if available
            else None
        ),
        "capital_province_id": 42 if available else None,
        "immediate_liege_character_id": None,
        "top_liege_character_id": (
            PLAYER_CHARACTER_ID if available else None
        ),
        "independent": True if available else None,
        "government": (
            {
                "key": "feudal_government",
                "flags": [
                    "government_is_feudal",
                    "government_is_settled",
                    "government_is_settled",
                ],
                "native_flag_count": 3,
            }
            if available
            else None
        ),
        "selected_game_rule_tokens": (
            ["1453_end_date", "normal_difficulty", "normal_difficulty"]
            if available
            else []
        ),
        "native_selected_game_rule_token_count": 3 if available else 0,
        "readiness": _readiness(available),
        "unavailable_reason": None if available else unavailable_reason,
        "provenance": _provenance(),
    }


def _native_result(status: str = "available") -> dict[str, object]:
    return {
        "step": STEP,
        "accepted": True,
        "status": status,
        "query_sequence": 9,
        "snapshot_revision": NATIVE_REVISION,
        "campaign_root_context": _frame(status),
        "backend_id": "native-headless",
    }


def _driver_result(status: str = "available") -> dict[str, object]:
    result = _native_result(status)
    frame = result["campaign_root_context"]
    assert isinstance(frame, dict)
    for key in (
        "schema_version",
        "date_raw",
        "local_player_id",
        "player_character_id",
        "player_character_alive",
        "primary_title",
        "capital_province_id",
        "immediate_liege_character_id",
        "top_liege_character_id",
        "independent",
        "government",
        "selected_game_rule_tokens",
        "native_selected_game_rule_token_count",
        "readiness",
        "unavailable_reason",
        "provenance",
    ):
        result[key] = copy.deepcopy(frame[key])
    readiness = frame["readiness"]
    assert isinstance(readiness, dict)
    result.update(
        {
            "campaign_root_context_ready": readiness["ready"],
            "queried_snapshot_id": "campaign-root-fixture:4",
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
            "played_character": {
                "character_id": PLAYER_CHARACTER_ID,
                "alive": True,
            },
            "one_life_settlement": None,
            "active_wars": [],
            "player_armies": [],
        },
    }


class CampaignRootContextV1ContractTests(unittest.TestCase):
    def test_available_preserves_lexical_multiplicity_and_hegemony(self) -> None:
        normalized = normalize_campaign_root_context_v1(
            _frame(),
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(normalized["status"], "available")
        self.assertEqual(normalized["local_player_id"], 0)
        self.assertEqual(normalized["primary_title"]["tier_key"], "hegemony")
        self.assertEqual(
            normalized["government"]["flags"].count(
                "government_is_settled"
            ),
            2,
        )
        self.assertEqual(
            normalized["selected_game_rule_tokens"].count(
                "normal_difficulty"
            ),
            2,
        )
        self.assertTrue(normalized["readiness"]["ready"])

    def test_available_distinguishes_every_legal_absence(self) -> None:
        frame = _frame()
        frame["primary_title"] = None
        frame["capital_province_id"] = None
        frame["government"] = None

        normalized = normalize_campaign_root_context_v1(
            frame,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(normalized["status"], "available")
        self.assertIsNone(normalized["primary_title"])
        self.assertIsNone(normalized["capital_province_id"])
        self.assertIsNone(normalized["immediate_liege_character_id"])
        self.assertIsNone(normalized["government"])
        self.assertTrue(normalized["readiness"]["ready"])

    def test_every_unavailable_stage_is_typed_and_carries_bindings(self) -> None:
        for reason in UNAVAILABLE_REASONS:
            with self.subTest(reason=reason):
                normalized = normalize_campaign_root_context_v1(
                    _frame("unavailable", unavailable_reason=reason),
                    expected_date_raw=DATE_RAW,
                    expected_snapshot_revision=NATIVE_REVISION,
                )
                self.assertEqual(normalized["status"], "unavailable")
                self.assertEqual(normalized["unavailable_reason"], reason)
                self.assertEqual(
                    normalized["snapshot_revision"], NATIVE_REVISION
                )
                self.assertEqual(normalized["date_raw"], DATE_RAW)
                self.assertIsNone(normalized["player_character_id"])
                self.assertEqual(normalized["selected_game_rule_tokens"], [])
                self.assertFalse(normalized["readiness"]["ready"])
                self.assertEqual(normalized["provenance"], _provenance())

    def test_title_tier_pair_covers_all_six_native_values(self) -> None:
        tiers = {
            1: "barony",
            2: "county",
            3: "duchy",
            4: "kingdom",
            5: "empire",
            6: "hegemony",
        }
        for tier_raw, tier_key in tiers.items():
            with self.subTest(tier_raw=tier_raw):
                frame = _frame()
                frame["primary_title"] = {
                    "title_id": 67_890,
                    "tier_raw": tier_raw,
                    "tier_key": tier_key,
                }
                normalized = normalize_campaign_root_context_v1(
                    frame,
                    expected_date_raw=DATE_RAW,
                    expected_snapshot_revision=NATIVE_REVISION,
                )
                self.assertEqual(
                    normalized["primary_title"]["tier_key"], tier_key
                )

    def test_vassal_liege_chain_is_distinct_and_atomic(self) -> None:
        frame = _frame()
        frame["immediate_liege_character_id"] = 22_222
        frame["top_liege_character_id"] = 33_333
        frame["independent"] = False

        normalized = normalize_campaign_root_context_v1(
            frame,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertFalse(normalized["independent"])
        self.assertEqual(normalized["immediate_liege_character_id"], 22_222)
        self.assertEqual(normalized["top_liege_character_id"], 33_333)

    def test_schema_binding_sort_count_and_provenance_are_strict(self) -> None:
        mutations = {
            "extra_key": lambda row: row.__setitem__("extra", None),
            "revision": lambda row: row.__setitem__(
                "snapshot_revision", NATIVE_REVISION + 1
            ),
            "date": lambda row: row.__setitem__("date_raw", DATE_RAW + 24),
            "readiness": lambda row: row["readiness"].__setitem__(
                "capital_ready", False
            ),
            "tier_pair": lambda row: row["primary_title"].__setitem__(
                "tier_key", "empire"
            ),
            "flags_order": lambda row: row["government"].__setitem__(
                "flags", ["government_is_settled", "government_is_feudal"]
            ),
            "flags_count": lambda row: row["government"].__setitem__(
                "native_flag_count", 99
            ),
            "tokens_order": lambda row: row.__setitem__(
                "selected_game_rule_tokens",
                ["normal_difficulty", "1453_end_date", "normal_difficulty"],
            ),
            "tokens_count": lambda row: row.__setitem__(
                "native_selected_game_rule_token_count", 99
            ),
            "provenance": lambda row: row["provenance"].__setitem__(
                "government_rva", "0x0"
            ),
            "independent": lambda row: row.__setitem__("independent", False),
            "top_liege": lambda row: row.__setitem__(
                "top_liege_character_id", 33_333
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                frame = _frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    normalize_campaign_root_context_v1(
                        frame,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

        unavailable = _frame("unavailable")
        unavailable["capital_province_id"] = 42
        with self.assertRaisesRegex(ValueError, "invented root state"):
            normalize_campaign_root_context_v1(
                unavailable,
                expected_date_raw=DATE_RAW,
                expected_snapshot_revision=NATIVE_REVISION,
            )


class _FakeEndpoint:
    def __init__(self) -> None:
        self.pipe_name = r"\\.\pipe\xar_campaign_root_context_v1_fixture"
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
    *,
    paused: bool = True,
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
            "pid": 6767,
            "session_generation": 0,
            "game_version": CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
            "expected_ck3_version": CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
            "executable_sha256": (
                CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
            ),
            "capabilities": [
                "game.state.snapshot",
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
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


class CampaignRootContextV1NativeDriverTests(unittest.TestCase):
    def test_singleton_action_is_advertised_only_while_paused(self) -> None:
        driver, _endpoint = _native_driver()
        capabilities = driver.capabilities()
        self.assertTrue(capabilities["campaign_root_context_v1_query_supported"])
        self.assertIn(STEP, capabilities["action_steps"])
        self.assertEqual(
            _action_steps(
                [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY],
                paused=True,
            ),
            [STEP],
        )
        self.assertEqual(
            _action_steps(
                [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY],
                paused=False,
            ),
            [],
        )

    def test_driver_normalizes_available_and_unavailable_results(self) -> None:
        for status in ("available", "unavailable"):
            with self.subTest(status=status):
                driver, endpoint = _native_driver()
                _answer_with(
                    endpoint,
                    lambda selected=status: _native_result(selected),
                )
                snapshot = driver.take_snapshot()
                result = driver.execute_step(
                    STEP,
                    expected_revision=int(snapshot["revision"]),
                )
                self.assertEqual(result["status"], status)
                self.assertEqual(
                    result["campaign_root_context_ready"],
                    status == "available",
                )
                self.assertEqual(result["date_raw"], DATE_RAW)
                self.assertEqual(result["provenance"], _provenance())
                self.assertEqual(
                    result["queried_native_revision"], NATIVE_REVISION
                )

    def test_driver_rejects_malformed_envelope_and_frame_drift(self) -> None:
        driver, endpoint = _native_driver()

        def wrong_envelope() -> dict[str, object]:
            result = _native_result()
            result["status"] = "unavailable"
            return result

        _answer_with(endpoint, wrong_envelope)
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
                [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY]
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
            "snapshot_id": f"campaign-root-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-12345-fixture",
            "diagnostics": {
                "hello": {
                    "game_version": CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
                    "expected_ck3_version": (
                        CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION
                    ),
                    "expected_ck3_sha256": (
                        "A" * 64
                        if self.build_drift
                        else CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
                    ),
                }
            },
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step != STEP or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed campaign-root query binding")
        result = _driver_result(self.status)
        if self.mirror_drift:
            result["top_liege_character_id"] = 999
        return result

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("campaign-root observation must not advance")


class CampaignRootContextV1ServiceTests(unittest.TestCase):
    def test_official_facade_forwards_the_required_revision(self) -> None:
        result = _ck3_query_campaign_root_context_v1(
            GameplayBridgeService(_ServiceDriver()),
            PUBLIC_REVISION,
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["binding"]["expected_revision"], PUBLIC_REVISION
        )

    def test_service_returns_available_with_exact_build_source_binding(self) -> None:
        result = GameplayBridgeService(
            _ServiceDriver()
        ).query_campaign_root_context_v1(
            expected_revision=PUBLIC_REVISION,
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(result["scope"], "exact-campaign-root-context")
        self.assertEqual(
            set(result["build"]), {"version", "exe_sha256"}
        )
        self.assertEqual(result["build"]["version"], _provenance()["game_version"])
        self.assertEqual(
            result["build"]["exe_sha256"],
            _provenance()["executable_sha256"],
        )
        self.assertEqual(
            set(result["source"]),
            {
                "game_version",
                "executable_sha256",
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "paused",
                "backend_id",
            },
        )
        self.assertEqual(
            set(result["binding"]),
            {
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "expected_revision",
            },
        )
        self.assertEqual(result["binding"]["revision"], PUBLIC_REVISION)
        self.assertEqual(
            result["binding"]["native_revision"], NATIVE_REVISION
        )
        self.assertEqual(
            result["binding"]["expected_revision"], PUBLIC_REVISION
        )
        self.assertEqual(result["government"]["native_flag_count"], 3)
        self.assertEqual(
            result["native_selected_game_rule_token_count"], 3
        )

    def test_service_returns_typed_unavailable_without_fabricating_absent(self) -> None:
        result = GameplayBridgeService(
            _ServiceDriver("unavailable")
        ).query_campaign_root_context_v1(
            expected_revision=PUBLIC_REVISION,
        )

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], "state_changed")
        self.assertFalse(result["campaign_root_context_ready"])
        self.assertIsNone(result["player_character_id"])
        self.assertIsNone(result["primary_title"])
        self.assertEqual(result["selected_game_rule_tokens"], [])
        self.assertEqual(result["build"]["version"], "1.19.0.6")
        self.assertEqual(result["binding"]["date_raw"], DATE_RAW)

    def test_service_rejects_capability_revision_build_and_binding_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_campaign_root_context_v1(
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_campaign_root_context_v1(
                expected_revision=PUBLIC_REVISION - 1,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "mirrors disagree"):
            GameplayBridgeService(
                _ServiceDriver(mirror_drift=True)
            ).query_campaign_root_context_v1(
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "build mirror"):
            GameplayBridgeService(
                _ServiceDriver(build_drift=True)
            ).query_campaign_root_context_v1(
                expected_revision=PUBLIC_REVISION,
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_campaign_root_context_v1(
                expected_revision=PUBLIC_REVISION,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class CampaignRootContextV1McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_campaign_root_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_campaign_root_context_v1", names)
            result = await client.call_tool(
                "ck3_query_campaign_root_context_v1",
                {"expected_revision": PUBLIC_REVISION},
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["player_character_id"], PLAYER_CHARACTER_ID)
        self.assertEqual(payload["primary_title"]["tier_key"], "hegemony")
        self.assertEqual(payload["build"]["version"], "1.19.0.6")
        self.assertEqual(
            payload["binding"]["expected_revision"], PUBLIC_REVISION
        )


if __name__ == "__main__":
    unittest.main()
