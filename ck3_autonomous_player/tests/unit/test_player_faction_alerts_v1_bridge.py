from __future__ import annotations

import copy
import importlib.util
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
    _ck3_query_player_faction_alerts_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import (
    ConfiguredHybridFallbackDriver,
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.player_faction_alerts_contract import (
    PLAYER_FACTION_ALERTS_V1_BACKEND_ID,
    PLAYER_FACTION_ALERTS_V1_EXECUTABLE_SHA256,
    QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY,
    QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
    normalize_player_faction_alerts_v1,
    validate_player_faction_war_handoffs_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService


NATIVE_REVISION = 41
PUBLIC_REVISION = 9
DATE_RAW = 53_789_952
PLAYER_ID = 32_904
STEP = QUERY_PLAYER_FACTION_ALERTS_V1_STEP


def _fixed(raw: int) -> dict[str, int]:
    return {"raw": raw, "scale": 100_000}


def _targeting_row(
    faction_id: int,
    *,
    faction_type_key: str = "independence_faction",
    leader_is_human: bool = False,
    faction_at_war: bool = False,
    faction_war_id: int | None = None,
    discontent_per_month_raw: int = 0,
    months_until_max_discontent: int | None = None,
    dangerous: bool = False,
    danger_reason: str = "non_peasant_discontent_not_increasing",
) -> dict[str, object]:
    return {
        "faction_id": faction_id,
        "faction_type_key": faction_type_key,
        "target_character_id": PLAYER_ID,
        "leader_character_id": 33_000 + faction_id,
        "leader_is_human": leader_is_human,
        "special_character_id": None,
        "special_title_id": None,
        "faction_at_war": faction_at_war,
        "faction_war_id": faction_war_id,
        "power": _fixed(9_100_000),
        "power_threshold": _fixed(8_000_000),
        "discontent": _fixed(6_400_000),
        "discontent_per_month": _fixed(discontent_per_month_raw),
        "months_until_max_discontent": months_until_max_discontent,
        "character_member_ids": [33_000 + faction_id, 34_000 + faction_id],
        "county_member_title_ids": [],
        "dangerous_by_stock_rule": dangerous,
        "danger_reason": danger_reason,
    }


def _rows() -> list[dict[str, object]]:
    return [
        _targeting_row(770),
        _targeting_row(
            771,
            discontent_per_month_raw=400_000,
            dangerous=True,
            danger_reason="non_peasant_discontent_increasing",
        ),
        _targeting_row(
            772,
            faction_type_key="peasant_faction",
            discontent_per_month_raw=900_000,
            months_until_max_discontent=12,
            dangerous=True,
            danger_reason="peasant_ultimatum_within_12_months",
        ),
        _targeting_row(
            773,
            faction_at_war=True,
            faction_war_id=9_001,
            leader_is_human=True,
            dangerous=True,
            danger_reason="human_faction_leader",
        ),
    ]


def _county_exposure() -> dict[str, object]:
    return {
        "county_title_id": 441,
        "faction_id": 880,
        "faction_type_key": "populist_faction",
        "target_character_id": 32_000,
        "power": _fixed(8_500_000),
        "power_threshold": _fixed(8_000_000),
        "dangerous_by_stock_rule": True,
        "danger_reason": (
            "player_county_in_powerful_liege_targeting_populist_faction"
        ),
    }


def _provenance() -> dict[str, str]:
    return {
        "game_version": "1.19.0.6",
        "executable_sha256": PLAYER_FACTION_ALERTS_V1_EXECUTABLE_SHA256,
        "backend_id": PLAYER_FACTION_ALERTS_V1_BACKEND_ID,
    }


def _unavailable_projection() -> dict[str, object]:
    return {
        "status": "unavailable",
        "present": None,
        "dangerous": None,
        "dangerous_faction_ids": [],
        "watch_faction_ids": [],
        "war_handoff_faction_ids": [],
        "exposed_county_title_ids": [],
        "exact_ultimatum_timing_ready": False,
    }


def _full_frame() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "player_character_id": PLAYER_ID,
        "targeting_faction_count": 4,
        "targeting_factions": _rows(),
        "county_exposures": [_county_exposure()],
        "planner_projection": {
            "status": "available",
            "present": True,
            "dangerous": True,
            "dangerous_faction_ids": [771, 772],
            "watch_faction_ids": [770],
            "war_handoff_faction_ids": [773],
            "exposed_county_title_ids": [441],
            "exact_ultimatum_timing_ready": False,
        },
        "readiness": {
            "identity_ready": True,
            "targeting_count_ready": True,
            "targeting_rows_ready": True,
            "county_exposure_ready": True,
            "stock_dangerous_predicate_ready": True,
            "same_frame_ready": True,
            "alert_ready": True,
            "exact_ultimatum_timing_ready": False,
        },
        "component_unavailable_reasons": {
            "targeting_rows": None,
            "county_exposure": None,
        },
        "unavailable_reason": None,
        "provenance": _provenance(),
    }


def _partial_frame() -> dict[str, object]:
    frame = _full_frame()
    frame.update(
        {
            "targeting_faction_count": 2,
            "targeting_factions": [],
            "county_exposures": [],
            "planner_projection": _unavailable_projection(),
            "readiness": {
                "identity_ready": True,
                "targeting_count_ready": True,
                "targeting_rows_ready": False,
                "county_exposure_ready": False,
                "stock_dangerous_predicate_ready": False,
                "same_frame_ready": True,
                "alert_ready": False,
                "exact_ultimatum_timing_ready": False,
            },
            "component_unavailable_reasons": {
                "targeting_rows": "targeting_rows_native_reader_not_frozen",
                "county_exposure": "county_exposure_native_reader_not_frozen",
            },
        }
    )
    return frame


def _unavailable_frame() -> dict[str, object]:
    frame = _partial_frame()
    frame.update(
        {
            "status": "unavailable",
            "date_raw": None,
            "player_character_id": None,
            "targeting_faction_count": None,
            "readiness": {key: False for key in frame["readiness"]},
            "component_unavailable_reasons": {
                "targeting_rows": None,
                "county_exposure": None,
            },
            "unavailable_reason": "reader_not_implemented",
        }
    )
    return frame


def _driver_result(frame: dict[str, object]) -> dict[str, object]:
    return {
        "step": STEP,
        "accepted": True,
        "status": frame["status"],
        "query_sequence": 14,
        "snapshot_revision": NATIVE_REVISION,
        "player_faction_alerts": frame,
        "backend_id": "native-headless",
        "player_faction_alerts_ready": frame["readiness"]["alert_ready"],
        "queried_snapshot_id": "faction-alert-fixture:9",
        "queried_revision": PUBLIC_REVISION,
        "queried_native_revision": NATIVE_REVISION,
    }


class PlayerFactionAlertsContractTests(unittest.TestCase):
    def _normalize(self, frame: dict[str, object]) -> dict[str, object]:
        return normalize_player_faction_alerts_v1(
            frame,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

    def test_full_frame_preserves_derived_planner_classes(self) -> None:
        normalized = self._normalize(_full_frame())

        self.assertTrue(normalized["readiness"]["alert_ready"])
        self.assertEqual(
            normalized["planner_projection"]["dangerous_faction_ids"],
            [771, 772],
        )
        self.assertEqual(
            normalized["planner_projection"]["war_handoff_faction_ids"],
            [773],
        )

    def test_component_partial_keeps_count_and_fails_planner_closed(self) -> None:
        normalized = self._normalize(_partial_frame())

        self.assertEqual(normalized["status"], "available")
        self.assertEqual(normalized["targeting_faction_count"], 2)
        self.assertFalse(normalized["readiness"]["alert_ready"])
        self.assertEqual(normalized["planner_projection"]["status"], "unavailable")
        self.assertIsNone(normalized["planner_projection"]["dangerous"])

    def test_zero_targeting_count_can_close_empty_rows_before_county_reader(self) -> None:
        frame = _partial_frame()
        frame["targeting_faction_count"] = 0
        frame["readiness"]["targeting_rows_ready"] = True
        frame["readiness"]["stock_dangerous_predicate_ready"] = True
        frame["component_unavailable_reasons"]["targeting_rows"] = None

        normalized = self._normalize(frame)

        self.assertTrue(normalized["readiness"]["targeting_rows_ready"])
        self.assertFalse(normalized["readiness"]["alert_ready"])
        self.assertEqual(normalized["targeting_factions"], [])
        self.assertEqual(normalized["planner_projection"]["status"], "unavailable")
        self.assertIsNone(normalized["planner_projection"]["present"])
        self.assertIsNone(normalized["planner_projection"]["dangerous"])

    def test_whole_frame_unavailable_carries_no_component_claims(self) -> None:
        normalized = self._normalize(_unavailable_frame())
        self.assertEqual(normalized["status"], "unavailable")
        self.assertTrue(all(not ready for ready in normalized["readiness"].values()))
        self.assertTrue(
            all(
                reason is None
                for reason in normalized["component_unavailable_reasons"].values()
            )
        )

    def test_rejects_schema_fixed_point_identity_and_stock_rule_tampering(self) -> None:
        mutations = {
            "extra": lambda value: value.__setitem__("extra", None),
            "fixed_shape": lambda value: value["targeting_factions"][0]["power"].__setitem__("rounded", 91),
            "fixed_scale": lambda value: value["targeting_factions"][0]["power"].__setitem__("scale", 1_000),
            "target": lambda value: value["targeting_factions"][0].__setitem__("target_character_id", PLAYER_ID + 1),
            "danger": lambda value: value["targeting_factions"][1].__setitem__("dangerous_by_stock_rule", False),
            "peasant_boundary": lambda value: value["targeting_factions"][2].__setitem__("months_until_max_discontent", 13),
            "county_type": lambda value: value["county_exposures"][0].__setitem__("faction_type_key", "liberty_faction"),
            "county_target": lambda value: value["county_exposures"][0].__setitem__("target_character_id", PLAYER_ID),
            "county_power": lambda value: value["county_exposures"][0].__setitem__("power", _fixed(8_000_000)),
            "planner": lambda value: value["planner_projection"]["dangerous_faction_ids"].pop(),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                frame = _full_frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    self._normalize(frame)

    def test_rejects_partial_component_or_planner_guess(self) -> None:
        mutations = {
            "row": lambda value: value.__setitem__("targeting_factions", [_rows()[0]]),
            "missing_reason": lambda value: value["component_unavailable_reasons"].__setitem__("targeting_rows", None),
            "planner_present": lambda value: value["planner_projection"].__setitem__("present", True),
            "fake_ready": lambda value: value["readiness"].__setitem__("alert_ready", True),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                frame = _partial_frame()
                mutate(frame)
                with self.assertRaises(ValueError):
                    self._normalize(frame)

    def test_action_step_is_paused_only(self) -> None:
        capabilities = [QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY]
        self.assertIn(STEP, _action_steps(capabilities, paused=True))
        self.assertNotIn(STEP, _action_steps(capabilities, paused=False))

    def test_war_handoff_identity_must_exist_in_same_frame_active_wars(self) -> None:
        normalized = self._normalize(_full_frame())
        validate_player_faction_war_handoffs_v1(
            normalized, [{"war_id": 9_001}]
        )
        with self.assertRaisesRegex(ValueError, "absent from active_wars"):
            validate_player_faction_war_handoffs_v1(normalized, [])


class _NativeDriverHarness(NativeHeadlessGameplayDriver):
    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = frame

    def take_snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "native-faction-alert-fixture:41",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-32904-fixture",
            "diagnostics": {"connection_generation": 3},
            "active_wars": [{"war_id": 9_001}],
        }

    def _execute_primitive_step(
        self,
        step: str,
        *,
        expected_revision: int,
        required_capability: str,
    ) -> dict[str, object]:
        if (
            step != STEP
            or expected_revision != PUBLIC_REVISION
            or required_capability != QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY
        ):
            raise AssertionError("native dispatch changed the frozen query")
        envelope = _driver_result(self.frame)
        return {
            key: copy.deepcopy(envelope[key])
            for key in (
                "step",
                "accepted",
                "status",
                "query_sequence",
                "snapshot_revision",
                "player_faction_alerts",
                "player_faction_alerts_ready",
                "backend_id",
            )
        }


class PlayerFactionAlertsNativeDriverTests(unittest.TestCase):
    def test_native_dispatch_normalizes_component_partial(self) -> None:
        result = _NativeDriverHarness(
            _partial_frame()
        )._execute_player_faction_alerts_v1_query(
            expected_revision=PUBLIC_REVISION
        )

        self.assertEqual(result["status"], "available")
        self.assertFalse(result["player_faction_alerts_ready"])
        self.assertEqual(result["queried_native_revision"], NATIVE_REVISION)
        self.assertEqual(
            result["player_faction_alerts"]["targeting_faction_count"], 2
        )

    def test_hybrid_routes_query_to_native_without_fallback(self) -> None:
        class Native:
            def capabilities(self) -> dict[str, object]:
                return {
                    "bridge_capabilities": [
                        QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY
                    ]
                }

            def execute_step(
                self, step: str, *, expected_revision: int | None = None
            ) -> dict[str, object]:
                self.called = (step, expected_revision)
                return _driver_result(_partial_frame())

        native = Native()
        wrapper = object.__new__(ConfiguredHybridFallbackDriver)
        wrapper.native = native
        snapshot = {
            "snapshot_id": "hybrid-faction-alert-fixture:9",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "active_wars": [],
            "backend_revisions": {"fast": PUBLIC_REVISION},
        }
        wrapper.take_snapshot = lambda: copy.deepcopy(snapshot)

        result = wrapper.execute_step(STEP, expected_revision=PUBLIC_REVISION)

        self.assertEqual(native.called, (STEP, PUBLIC_REVISION))
        self.assertEqual(result["queried_revision"], PUBLIC_REVISION)
        self.assertFalse(result["player_faction_alerts_ready"])


class _ServiceDriver:
    def __init__(
        self,
        frame: dict[str, object] | None = None,
        *,
        advertise: bool = True,
        drift: bool = False,
    ) -> None:
        self.frame = frame or _partial_frame()
        self.advertise = advertise
        self.drift = drift
        self.snapshot_calls = 0

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [STEP] if self.advertise else [],
            "bridge_capabilities": (
                [QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY]
                if self.advertise
                else []
            ),
        }

    def take_snapshot(self) -> dict[str, object]:
        self.snapshot_calls += 1
        revision = (
            PUBLIC_REVISION + 1
            if self.drift and self.snapshot_calls > 1
            else PUBLIC_REVISION
        )
        return {
            "format_version": 1,
            "snapshot_id": f"faction-alert-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-32904-fixture",
            "active_wars": [{"war_id": 9_001}],
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step != STEP or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed player faction alert binding")
        return copy.deepcopy(_driver_result(self.frame))

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("query must not advance CK3")


class PlayerFactionAlertsServiceTests(unittest.TestCase):
    def test_facade_and_service_preserve_partial_binding(self) -> None:
        result = _ck3_query_player_faction_alerts_v1(
            GameplayBridgeService(_ServiceDriver()), PUBLIC_REVISION
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(result["scope"], "exact-player-faction-alerts")
        self.assertEqual(result["binding"]["revision"], PUBLIC_REVISION)
        self.assertEqual(result["build"]["version"], "1.19.0.6")
        self.assertFalse(result["player_faction_alerts_ready"])
        self.assertEqual(
            result["player_faction_alerts"]["targeting_faction_count"], 2
        )

    def test_service_preserves_full_and_typed_unavailable(self) -> None:
        full = GameplayBridgeService(
            _ServiceDriver(_full_frame())
        ).query_player_faction_alerts_v1(expected_revision=PUBLIC_REVISION)
        unavailable = GameplayBridgeService(
            _ServiceDriver(_unavailable_frame())
        ).query_player_faction_alerts_v1(expected_revision=PUBLIC_REVISION)

        self.assertTrue(full["player_faction_alerts_ready"])
        self.assertEqual(unavailable["status"], "unavailable")
        self.assertFalse(unavailable["player_faction_alerts_ready"])

    def test_service_rejects_capability_revision_and_frame_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_player_faction_alerts_v1(expected_revision=PUBLIC_REVISION)
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(_ServiceDriver()).query_player_faction_alerts_v1(
                expected_revision=PUBLIC_REVISION - 1
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_player_faction_alerts_v1(expected_revision=PUBLIC_REVISION)


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class PlayerFactionAlertsMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver())
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn("ck3_query_player_faction_alerts_v1", names)
            result = await client.call_tool(
                "ck3_query_player_faction_alerts_v1",
                {"expected_revision": PUBLIC_REVISION},
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "available")
        self.assertFalse(payload["player_faction_alerts_ready"])


if __name__ == "__main__":
    unittest.main()
