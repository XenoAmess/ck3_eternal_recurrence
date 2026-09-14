from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import (
    _ck3_change_steward_develop_county_task_v1,
    create_server,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.steward_develop_county_action_contract import (
    CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_CAPABILITY,
    CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_TRANSPORT_CAPABILITY,
    STEWARD_DEVELOP_COUNTY_ACTION_V1_BACKEND_ID,
    STEWARD_DEVELOP_COUNTY_ACTION_V1_CONTRACT_STAGE,
    STEWARD_DEVELOP_COUNTY_ACTION_V1_EXECUTABLE_SHA256,
    STEWARD_DEVELOP_COUNTY_ACTION_V1_GAME_VERSION,
    ChangeStewardDevelopCountyRequestV1,
    build_change_steward_develop_county_request_v1,
    normalize_change_steward_develop_county_ack_v1,
    normalize_change_steward_develop_county_receipt_v1,
)
from xar_autoplayer.bridge.steward_develop_county_contract import (
    QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY,
    QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP,
    STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_BACKEND_ID,
    STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CONTRACT_STAGE,
)


PUBLIC_REVISION = 7
NATIVE_REVISION = 31
DATE_RAW = 53_182_016
PLAYER = 32_904
STEWARD = 32_910
COUNTY = 1_048_577
PROVINCE = 2_586


def _request() -> ChangeStewardDevelopCountyRequestV1:
    return build_change_steward_develop_county_request_v1(
        request_id="steward-dev-fixture-1",
        councillor_character_id=STEWARD,
        task_key="task_develop_county",
        target_county_title_id=COUNTY,
        expected_revision=PUBLIC_REVISION,
        replace_existing_task=True,
    )


def _exact_build() -> dict[str, str]:
    return {
        "game_version": STEWARD_DEVELOP_COUNTY_ACTION_V1_GAME_VERSION,
        "executable_sha256": (
            STEWARD_DEVELOP_COUNTY_ACTION_V1_EXECUTABLE_SHA256
        ),
        "backend_id": STEWARD_DEVELOP_COUNTY_ACTION_V1_BACKEND_ID,
    }


def _ack(
    request: ChangeStewardDevelopCountyRequestV1,
    *,
    submitted: bool,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_stage": STEWARD_DEVELOP_COUNTY_ACTION_V1_CONTRACT_STAGE,
        "status": (
            "submitted_verification_pending"
            if submitted
            else "rejected_before_submit"
        ),
        "verification_pending": submitted,
        "request_id": request.request_id,
        "pre_snapshot_revision": PUBLIC_REVISION if submitted else 0,
        "pre_native_snapshot_revision": NATIVE_REVISION if submitted else 0,
        "councillor_character_id": STEWARD,
        "task_key": "task_develop_county",
        "target_county_title_id": COUNTY,
        "submitted_target_province_id": PROVINCE if submitted else -1,
        "replaced_existing_task": submitted,
        "failure_class": "none" if submitted else "native_command_dispatch",
        "rejection_reason": None if submitted else "native_command_abi_not_certified",
        "native_reason_key": None,
        "exact_build": _exact_build(),
    }


def _candidate_frame() -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_stage": STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CONTRACT_STAGE,
        "status": "available",
        "unavailable_reason": None,
        "snapshot_revision": NATIVE_REVISION,
        "observed_date_raw": DATE_RAW,
        "player_character_id": PLAYER,
        "steward_character_id": STEWARD,
        "task_key": "task_develop_county",
        "shown": True,
        "valid": True,
        "task_failure_reason": None,
        "steward_increase_development_value_raw": 1_000,
        "current_gold_raw": 50_000,
        "no_ai_increase_development": False,
        "has_active_improve_development_directive": False,
        "target_selection_mode": "engine_random_unscored",
        "candidates": [
            {
                "county_title_id": COUNTY,
                "capital_province_id": PROVINCE,
                "holder_character_id": PLAYER,
                "is_player_capital": True,
                "directly_held_by_player": True,
                "native_legal": True,
                "development_level_raw": 12,
                "development_progress_raw": 4_000,
                "monthly_development_rate_raw": 250,
                "max_development_level_raw": 100,
                "terrain_key": "plains",
                "same_culture_as_player": True,
                "cultural_acceptance_threshold_passed": True,
            }
        ],
        "same_frame_stable": True,
        "readiness": True,
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": (
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
            ),
            "backend_id": STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_BACKEND_ID,
            "reader_mode": "contract_fixture_pending_live_reader",
            "next_reverse_engineering_entry": (
                "task_develop_county_native_candidate_enumerator_and_final_"
                "legality_call"
            ),
        },
    }


class StewardDevelopCountyActionContractTests(unittest.TestCase):
    def test_public_request_has_fixed_task_and_no_province_injection(self) -> None:
        request = _request()
        self.assertEqual(request.task_key, "task_develop_county")
        self.assertFalse(hasattr(request, "target_province_id"))
        with self.assertRaises(ValueError):
            build_change_steward_develop_county_request_v1(
                request_id="steward-dev-fixture-2",
                councillor_character_id=STEWARD,
                task_key="task_collect_taxes",
                target_county_title_id=COUNTY,
                expected_revision=PUBLIC_REVISION,
                replace_existing_task=False,
            )

    def test_ack_never_claims_application_and_receipt_is_separate(self) -> None:
        request = _request()
        ack = normalize_change_steward_develop_county_ack_v1(
            _ack(request, submitted=True), expected_request=request
        )
        self.assertEqual(ack["status"], "submitted_verification_pending")
        self.assertNotIn("success", ack)
        self.assertNotIn("applied", ack)
        receipt = {
            "schema_version": 1,
            "status": "applied",
            "request_id": request.request_id,
            "reason": None,
            "post_snapshot_revision": PUBLIC_REVISION + 1,
            "post_native_snapshot_revision": NATIVE_REVISION + 1,
            "post_observed_date_raw": DATE_RAW,
            "councillor_character_id": STEWARD,
            "active_task_key": "task_develop_county",
            "target_county_title_id": COUNTY,
            "target_province_id": PROVINCE,
            "progress_kind": "value",
            "progress_current_raw": 0,
            "progress_max_raw": 100_000,
            "progress_frozen": False,
            "postcondition_verified": True,
        }
        normalized = normalize_change_steward_develop_county_receipt_v1(
            receipt, expected_ack=ack
        )
        self.assertTrue(normalized["postcondition_verified"])
        stale = copy.deepcopy(receipt)
        stale["post_snapshot_revision"] = PUBLIC_REVISION
        with self.assertRaises(ValueError):
            normalize_change_steward_develop_county_receipt_v1(
                stale, expected_ack=ack
            )

    def test_rejected_ack_maps_only_to_rejected_receipt(self) -> None:
        request = _request()
        ack = normalize_change_steward_develop_county_ack_v1(
            _ack(request, submitted=False), expected_request=request
        )
        receipt = {
            "schema_version": 1,
            "status": "rejected",
            "request_id": request.request_id,
            "reason": "native_command_abi_not_certified",
            "post_snapshot_revision": 0,
            "post_native_snapshot_revision": 0,
            "post_observed_date_raw": 0,
            "councillor_character_id": -1,
            "active_task_key": "",
            "target_county_title_id": None,
            "target_province_id": None,
            "progress_kind": "",
            "progress_current_raw": None,
            "progress_max_raw": None,
            "progress_frozen": None,
            "postcondition_verified": False,
        }
        self.assertEqual(
            normalize_change_steward_develop_county_receipt_v1(
                receipt, expected_ack=ack
            )["status"],
            "rejected",
        )


class _ActionDriver:
    def __init__(self, *, submitted: bool = False) -> None:
        self.submitted = submitted
        self.last_request: ChangeStewardDevelopCountyRequestV1 | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "source": "named-pipe",
            "snapshot": True,
            "wait_for_change": False,
            "action_steps": [QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP],
            "bridge_capabilities": [
                QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY,
                CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_TRANSPORT_CAPABILITY,
            ],
        }

    def take_snapshot(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "snapshot_id": "steward-development-action-fixture:7",
            "revision": PUBLIC_REVISION,
            "native_revision": NATIVE_REVISION,
            "source": "named-pipe",
            "backend_id": "native-headless",
            "date_raw": DATE_RAW,
            "paused": True,
            "episode_run_id": "native-32904-action-fixture",
        }

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        if (
            step != QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP
            or expected_revision != PUBLIC_REVISION
        ):
            raise AssertionError("unexpected fixture step")
        frame = _candidate_frame()
        return {
            "step": step,
            "accepted": True,
            "status": "available",
            "query_sequence": 1,
            "snapshot_revision": NATIVE_REVISION,
            "steward_develop_county_candidates": frame,
            "backend_id": "native-headless",
            "steward_develop_county_candidates_ready": True,
            "queried_snapshot_id": "steward-development-action-fixture:7",
            "queried_revision": PUBLIC_REVISION,
            "queried_native_revision": NATIVE_REVISION,
        }

    def change_steward_develop_county_task_v1(
        self,
        request: ChangeStewardDevelopCountyRequestV1,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        if expected_revision != PUBLIC_REVISION:
            raise AssertionError("action lost its public revision binding")
        self.last_request = request
        return _ack(request, submitted=self.submitted)

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        raise AssertionError("action ACK fixture must not wait or make a receipt")


class StewardDevelopCountyActionServiceTests(unittest.TestCase):
    def test_transport_returns_typed_rejection_while_production_is_unadvertised(
        self,
    ) -> None:
        driver = _ActionDriver(submitted=False)
        result = _ck3_change_steward_develop_county_task_v1(
            GameplayBridgeService(driver),
            STEWARD,
            COUNTY,
            PUBLIC_REVISION,
            True,
        )
        self.assertEqual(result["status"], "rejected_before_submit")
        self.assertEqual(result["failure_class"], "native_command_dispatch")
        self.assertFalse(result["verification_pending"])
        self.assertIsNotNone(driver.last_request)

    def test_unadvertised_production_capability_cannot_return_submitted_ack(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            BridgeUnavailableError, "production capability is unadvertised"
        ):
            _ck3_change_steward_develop_county_task_v1(
                GameplayBridgeService(_ActionDriver(submitted=True)),
                STEWARD,
                COUNTY,
                PUBLIC_REVISION,
                True,
            )


@unittest.skipIf(
    importlib.util.find_spec("mcp") is None,
    "optional MCP SDK not installed",
)
class StewardDevelopCountyActionMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_lists_and_returns_rejected_ack_only(self) -> None:
        from mcp import Client

        server = create_server(_ActionDriver(submitted=False))
        async with Client(server) as client:
            listed = await client.list_tools()
            self.assertIn(
                "ck3_change_steward_develop_county_task_v1",
                {tool.name for tool in listed.tools},
            )
            result = await client.call_tool(
                "ck3_change_steward_develop_county_task_v1",
                {
                    "councillor_character_id": STEWARD,
                    "target_county_title_id": COUNTY,
                    "expected_revision": PUBLIC_REVISION,
                    "replace_existing_task": True,
                },
            )

        self.assertFalse(result.is_error)
        self.assertEqual(
            result.structured_content["status"], "rejected_before_submit"
        )


if __name__ == "__main__":
    unittest.main()
