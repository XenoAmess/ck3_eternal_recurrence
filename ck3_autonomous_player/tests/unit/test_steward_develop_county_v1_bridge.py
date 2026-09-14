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
    _ck3_query_steward_develop_county_candidates_v1,
    create_server,
)
from xar_autoplayer.bridge.native_driver import _action_steps
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.steward_develop_county_contract import (
    QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY,
    QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP,
    STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_BACKEND_ID,
    STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CONTRACT_STAGE,
    STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_EXECUTABLE_SHA256,
    normalize_steward_develop_county_candidates_v1,
)


NATIVE_REVISION = 31
PUBLIC_REVISION = 7
DATE_RAW = 53_182_016
STEP = QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP


def _provenance() -> dict[str, str]:
    return {
        "game_version": "1.19.0.6",
        "executable_sha256": (
            STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_EXECUTABLE_SHA256
        ),
        "backend_id": STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_BACKEND_ID,
        "reader_mode": "contract_fixture_pending_live_reader",
        "next_reverse_engineering_entry": (
            "task_develop_county_native_candidate_enumerator_and_final_"
            "legality_call"
        ),
    }


def _candidate() -> dict[str, object]:
    return {
        "county_title_id": 1_048_577,
        "capital_province_id": 1_048_611,
        "holder_character_id": 32_904,
        "is_player_capital": True,
        "directly_held_by_player": True,
        "native_legal": True,
        "development_level_raw": 14,
        "development_progress_raw": 35_000,
        "monthly_development_rate_raw": 1_250,
        "max_development_level_raw": 100,
        "terrain_key": "farmlands",
        "same_culture_as_player": True,
        "cultural_acceptance_threshold_passed": True,
    }


def _frame(status: str = "available") -> dict[str, object]:
    available = status == "available"
    return {
        "schema_version": 1,
        "contract_stage": (
            STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CONTRACT_STAGE
        ),
        "status": status,
        "unavailable_reason": None if available else "reader_not_implemented",
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "player_character_id": 32_904 if available else None,
        "steward_character_id": 32_910 if available else None,
        "task_key": "task_develop_county",
        "shown": True if available else None,
        "valid": True if available else None,
        "task_failure_reason": None,
        "steward_increase_development_value_raw": 50_000 if available else None,
        "current_gold_raw": 120_000 if available else None,
        "no_ai_increase_development": False if available else None,
        "has_active_improve_development_directive": False if available else None,
        "target_selection_mode": "engine_random_unscored",
        "candidates": [_candidate()] if available else [],
        "same_frame_stable": available,
        "readiness": available,
        "provenance": _provenance(),
    }


def _driver_result(status: str = "available") -> dict[str, object]:
    frame = _frame(status)
    return {
        "step": STEP,
        "accepted": True,
        "status": status,
        "query_sequence": 12,
        "snapshot_revision": NATIVE_REVISION,
        "steward_develop_county_candidates": frame,
        "backend_id": "native-headless",
        "steward_develop_county_candidates_ready": frame["readiness"],
        "queried_snapshot_id": "steward-development-fixture:7",
        "queried_revision": PUBLIC_REVISION,
        "queried_native_revision": NATIVE_REVISION,
    }


class StewardDevelopCountyContractTests(unittest.TestCase):
    def test_available_frame_preserves_native_legal_candidate(self) -> None:
        normalized = normalize_steward_develop_county_candidates_v1(
            _frame(),
            expected_observed_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertTrue(normalized["readiness"])
        self.assertEqual(normalized["steward_character_id"], 32_910)
        self.assertEqual(
            normalized["candidates"][0]["capital_province_id"], 1_048_611
        )
        self.assertEqual(
            normalized["target_selection_mode"], "engine_random_unscored"
        )

    def test_unavailable_contract_does_not_invent_partial_observation(self) -> None:
        frame = _frame("unavailable")
        frame["observed_date_raw"] = None
        normalized = normalize_steward_develop_county_candidates_v1(
            frame,
            expected_observed_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(normalized["unavailable_reason"], "reader_not_implemented")
        self.assertFalse(normalized["readiness"])
        self.assertEqual(normalized["candidates"], [])

    def test_schema_identity_and_native_legality_are_strict(self) -> None:
        mutations = {
            "extra": lambda row: row.__setitem__("extra", None),
            "revision": lambda row: row.__setitem__(
                "snapshot_revision", NATIVE_REVISION + 1
            ),
            "task": lambda row: row.__setitem__("task_key", "task_collect_taxes"),
            "selection": lambda row: row.__setitem__(
                "target_selection_mode", "invented_score"
            ),
            "illegal_row": lambda row: row["candidates"][0].__setitem__(
                "native_legal", False
            ),
            "partial_unavailable": lambda row: row.__setitem__(
                "player_character_id", 32_904
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                frame = _frame(
                    "unavailable" if name == "partial_unavailable" else "available"
                )
                mutate(frame)
                with self.assertRaises(ValueError):
                    normalize_steward_develop_county_candidates_v1(
                        frame,
                        expected_observed_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

    def test_action_step_is_paused_only(self) -> None:
        capabilities = [
            QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY
        ]
        self.assertIn(
            STEP,
            _action_steps(capabilities, paused=True),
        )
        self.assertNotIn(
            STEP,
            _action_steps(capabilities, paused=False),
        )


class _ServiceDriver:
    def __init__(
        self,
        status: str = "available",
        *,
        advertise: bool = True,
        drift: bool = False,
    ) -> None:
        self.status = status
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
                [QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY]
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
            "snapshot_id": f"steward-development-fixture:{revision}",
            "revision": revision,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-32904-fixture",
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if step != STEP or expected_revision != PUBLIC_REVISION:
            raise AssertionError("service changed steward development binding")
        return copy.deepcopy(_driver_result(self.status))

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("query must not advance CK3")


class StewardDevelopCountyServiceTests(unittest.TestCase):
    def test_facade_and_service_return_exact_binding(self) -> None:
        result = _ck3_query_steward_develop_county_candidates_v1(
            GameplayBridgeService(_ServiceDriver()), PUBLIC_REVISION
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            result["scope"], "exact-steward-develop-county-candidates"
        )
        self.assertEqual(result["binding"]["revision"], PUBLIC_REVISION)
        self.assertEqual(result["build"]["version"], "1.19.0.6")
        self.assertEqual(
            result["steward_develop_county_candidates"]["candidates"][0][
                "county_title_id"
            ],
            1_048_577,
        )

    def test_service_preserves_typed_unavailable(self) -> None:
        result = GameplayBridgeService(
            _ServiceDriver("unavailable")
        ).query_steward_develop_county_candidates_v1(
            expected_revision=PUBLIC_REVISION
        )

        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["steward_develop_county_candidates_ready"])
        self.assertEqual(
            result["steward_develop_county_candidates"]["unavailable_reason"],
            "reader_not_implemented",
        )

    def test_service_rejects_capability_revision_and_frame_drift(self) -> None:
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                _ServiceDriver(advertise=False)
            ).query_steward_develop_county_candidates_v1(
                expected_revision=PUBLIC_REVISION
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "revision mismatch"):
            GameplayBridgeService(
                _ServiceDriver()
            ).query_steward_develop_county_candidates_v1(
                expected_revision=PUBLIC_REVISION - 1
            )
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed"):
            GameplayBridgeService(
                _ServiceDriver(drift=True)
            ).query_steward_develop_county_candidates_v1(
                expected_revision=PUBLIC_REVISION
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class StewardDevelopCountyMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_client_lists_and_calls_tool(self) -> None:
        from mcp import Client

        server = create_server(_ServiceDriver("unavailable"))
        async with Client(server) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            self.assertIn(
                "ck3_query_steward_develop_county_candidates_v1", names
            )
            result = await client.call_tool(
                "ck3_query_steward_develop_county_candidates_v1",
                {"expected_revision": PUBLIC_REVISION},
            )

        self.assertFalse(result.is_error)
        payload = result.structured_content
        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(
            payload["steward_develop_county_candidates"][
                "unavailable_reason"
            ],
            "reader_not_implemented",
        )


if __name__ == "__main__":
    unittest.main()
