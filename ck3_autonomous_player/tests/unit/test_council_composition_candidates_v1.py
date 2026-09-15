from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.council_composition_candidates_contract import (
    ASSIGN_COUNCILLOR_V1_CAPABILITY,
    COUNCIL_COMPOSITION_CANDIDATES_V1_SCHEMA,
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
    build_council_composition_candidates_request_v1,
    normalize_council_composition_candidates_v1,
)
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_council_composition_candidates_v1,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.strategy import choose_one_life_turn


def _snapshot(
    *,
    revision: int = 7,
    native_revision: int = 9,
    date_raw: int = 1000,
    paused: bool = True,
):
    return {
        "format_version": 1,
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "source": "fixture",
        "backend_id": "native-headless",
        "diagnostics": {"connection_generation": 1},
        "episode_run_id": "episode:1",
        "paused": paused,
        "map_ready": True,
        "active_event": None,
        "pending_character_interaction": None,
        "active_wars": [],
        "player_armies": [],
        "played_character": {
            "character_id": 707,
            "alive": True,
            "betrothed_id": None,
            "primary_spouse_id": 808,
            "spouse_ids": [808],
        },
    }


def _payload(
    *,
    revision: int = 7,
    native_revision: int = 9,
    date_raw: int = 1000,
    incumbent_character_id: int | None = None,
    incumbent_main_skill: int = 12,
    candidates: list[tuple[int, int, int]] | None = None,
):
    vacant = incumbent_character_id is None
    route = "assign" if vacant else "replace"
    if candidates is None:
        candidates = [(901, 1, 16), (902, 0, 16), (903, 2, 21)]
    return {
        "snapshot": {
            "snapshot_id": f"native:{revision}",
            "public_revision": revision,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "paused": True,
        },
        "owner_character_id": 707,
        "position": {
            "position_key": "councillor_steward",
            "incumbent_character_id": incumbent_character_id,
            "incumbent_main_skill": (
                None
                if vacant
                else {"key": "stewardship", "value": incumbent_main_skill}
            ),
            "vacant": vacant,
            "action_route": route,
        },
        "candidate_collection_complete": True,
        "candidates": [
            {
                "character_id": character_id,
                "native_collection_ordinal": ordinal,
                "eligible": True,
                "eligibility_reason": "native_candidate_provider_accepted",
                "main_skill": {"key": "stewardship", "value": skill},
                "action_route": route,
            }
            for character_id, ordinal, skill in candidates
        ],
        "readiness": {
            "identity_ready": True,
            "candidate_collection_ready": True,
            "incumbent_ready": True,
            "incumbent_main_skill_ready": True,
            "candidate_legality_ready": True,
            "main_skill_ready": True,
            "action_route_ready": True,
            "same_frame_ready": True,
            "ready": True,
        },
    }


def _result(payload: dict[str, object]):
    snapshot = payload["snapshot"]
    assert isinstance(snapshot, dict)
    return {
        "step": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": 3,
        "snapshot_revision": snapshot["native_revision"],
        "council_composition_candidates": copy.deepcopy(payload),
        "council_composition_candidates_ready": True,
        "backend_id": "native-headless",
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": snapshot["public_revision"],
        "queried_native_revision": snapshot["native_revision"],
    }


class _Driver:
    def __init__(self, snapshot, result, *, council_management=False):
        self._snapshot = snapshot
        self._result = result
        self._council_management = council_management
        self.calls: list[tuple[str, int | None]] = []

    def capabilities(self):
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "snapshot": True,
            "wait_for_change": True,
            "bridge_capabilities": [
                QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY
            ] + (
                [ASSIGN_COUNCILLOR_V1_CAPABILITY]
                if self._council_management
                else []
            ),
            "action_steps": [
                QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP
            ],
        }

    def take_snapshot(self):
        return copy.deepcopy(self._snapshot)

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        return copy.deepcopy(self._result)

    def wait_for_change(self, after_revision, *, timeout_seconds):
        return self.take_snapshot()


class _NativeQueryHarness:
    def __init__(self, snapshot, payload):
        self._snapshot = snapshot
        self._payload = payload
        self.calls: list[dict[str, object]] = []

    def take_snapshot(self):
        return copy.deepcopy(self._snapshot)

    def _execute_primitive_step(
        self,
        step,
        *,
        expected_revision,
        required_capability,
        request_fields,
    ):
        self.calls.append(
            {
                "step": step,
                "expected_revision": expected_revision,
                "required_capability": required_capability,
                "request_fields": copy.deepcopy(request_fields),
            }
        )
        return {
            "step": step,
            "accepted": True,
            "status": "available",
            "query_sequence": 3,
            "snapshot_revision": self._snapshot["native_revision"],
            "council_composition_candidates": copy.deepcopy(self._payload),
            "backend_id": "native-headless",
        }


class CouncilCompositionContractTests(unittest.TestCase):
    def test_request_and_available_payload_are_exact_frame_bound(self):
        request = build_council_composition_candidates_request_v1(
            expected_snapshot_id="native:7",
            public_revision=7,
            native_revision=9,
            date_raw=1000,
            owner_character_id=707,
        )
        self.assertEqual(request["position_key"], "councillor_steward")
        normalized = normalize_council_composition_candidates_v1(
            _payload(),
            expected_snapshot_id="native:7",
            expected_public_revision=7,
            expected_native_revision=9,
            expected_date_raw=1000,
            expected_owner_character_id=707,
        )
        self.assertTrue(normalized["readiness"]["ready"])

    def test_partial_enrichment_and_route_drift_fail_closed(self):
        partial = _payload()
        partial["readiness"]["main_skill_ready"] = False
        with self.assertRaisesRegex(ValueError, "complete readiness"):
            normalize_council_composition_candidates_v1(
                partial,
                expected_snapshot_id="native:7",
                expected_public_revision=7,
                expected_native_revision=9,
                expected_date_raw=1000,
                expected_owner_character_id=707,
            )

        incumbent_unready = _payload(incumbent_character_id=800)
        incumbent_unready["position"]["incumbent_main_skill"] = None
        with self.assertRaisesRegex(ValueError, "ready together"):
            normalize_council_composition_candidates_v1(
                incumbent_unready,
                expected_snapshot_id="native:7",
                expected_public_revision=7,
                expected_native_revision=9,
                expected_date_raw=1000,
                expected_owner_character_id=707,
            )

        invalid_skill = _payload(
            incumbent_character_id=800,
            incumbent_main_skill=-1,
        )
        with self.assertRaisesRegex(ValueError, "integer in"):
            normalize_council_composition_candidates_v1(
                invalid_skill,
                expected_snapshot_id="native:7",
                expected_public_revision=7,
                expected_native_revision=9,
                expected_date_raw=1000,
                expected_owner_character_id=707,
            )
        drift = _payload()
        drift["candidates"][0]["action_route"] = "replace"
        with self.assertRaisesRegex(ValueError, "disagrees with position"):
            normalize_council_composition_candidates_v1(
                drift,
                expected_snapshot_id="native:7",
                expected_public_revision=7,
                expected_native_revision=9,
                expected_date_raw=1000,
                expected_owner_character_id=707,
            )

    def test_full_character_ids_and_non_unique_ordinals_follow_native_contract(self):
        payload = _payload(candidates=[(-2, 0, 16), (0, 0, 16)])
        payload["owner_character_id"] = 0
        normalized = normalize_council_composition_candidates_v1(
            payload,
            expected_snapshot_id="native:7",
            expected_public_revision=7,
            expected_native_revision=9,
            expected_date_raw=1000,
            expected_owner_character_id=0,
        )
        self.assertEqual(
            [row["character_id"] for row in normalized["candidates"]],
            [-2, 0],
        )

        invalid = _payload(candidates=[(-1, 0, 16)])
        with self.assertRaisesRegex(ValueError, "valid full CharacterID"):
            normalize_council_composition_candidates_v1(
                invalid,
                expected_snapshot_id="native:7",
                expected_public_revision=7,
                expected_native_revision=9,
                expected_date_raw=1000,
                expected_owner_character_id=707,
            )

    def test_action_step_projection_handles_game_query_namespace(self):
        self.assertEqual(
            _action_steps(
                [QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY],
                paused=True,
            ),
            [QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP],
        )
        self.assertNotIn(
            ASSIGN_COUNCILLOR_V1_CAPABILITY,
            _action_steps([ASSIGN_COUNCILLOR_V1_CAPABILITY], paused=True),
        )

    def test_native_driver_binds_primitive_request_and_projects_ready_result(self):
        harness = _NativeQueryHarness(_snapshot(), _payload())
        execute_query = (
            NativeHeadlessGameplayDriver
            ._execute_council_composition_candidates_v1_query
        )
        result = execute_query(harness, expected_revision=7)
        self.assertEqual(
            harness.calls,
            [
                {
                    "step": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                    "expected_revision": 7,
                    "required_capability": (
                        QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY
                    ),
                    "request_fields": {
                        "expected_snapshot_id": "native:7",
                        "public_revision": 7,
                        "native_revision": 9,
                        "date_raw": 1000,
                        "owner_character_id": 707,
                        "position_key": "councillor_steward",
                    },
                }
            ],
        )
        self.assertTrue(result["council_composition_candidates_ready"])
        self.assertEqual(result["queried_snapshot_id"], "native:7")


class CouncilCompositionFormalConsumerTests(unittest.TestCase):
    def _plan(
        self,
        rows,
        *,
        date_raw=1000,
        paused=True,
        bridge_capabilities=(
            QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
            ASSIGN_COUNCILLOR_V1_CAPABILITY,
        ),
    ):
        return choose_one_life_turn(
            rows,
            snapshot=_snapshot(date_raw=date_raw, paused=paused),
            action_steps=(
                QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                "life-advance",
            ),
            bridge_capabilities=bridge_capabilities,
        )

    def test_query_only_capability_does_not_change_existing_turn(self):
        rows = [{"command": "save-checkpoint", "ok": True}]
        for paused in (True, False):
            with self.subTest(paused=paused):
                baseline = self._plan(
                    rows,
                    paused=paused,
                    bridge_capabilities=(),
                )
                query_only = self._plan(
                    rows,
                    paused=paused,
                    bridge_capabilities=(
                        QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
                    ),
                )
                self.assertEqual(query_only, baseline)

    def test_query_only_vacancy_history_does_not_block_existing_turn(self):
        query = {
            "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
            "ok": True,
            "result": _result(_payload()),
        }
        rows = [{"command": "save-checkpoint", "ok": True}, query]
        baseline = self._plan(rows, bridge_capabilities=())
        query_only = self._plan(
            rows,
            bridge_capabilities=(
                QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
            ),
        )
        self.assertEqual(query_only, baseline)
        self.assertNotEqual(
            query_only.get("phase"),
            "council_composition_action_unavailable",
        )

    def test_two_history_queries_are_consumed_only_with_both_capabilities(self):
        stale = _result(
            _payload(
                revision=6,
                native_revision=8,
                date_raw=976,
                incumbent_character_id=800,
                incumbent_main_skill=21,
            )
        )
        current = _result(
            _payload(
                incumbent_character_id=800,
                incumbent_main_skill=21,
            )
        )
        rows = [
            {"command": "save-checkpoint", "ok": True},
            {
                "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                "ok": True,
                "result": stale,
            },
            {
                "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                "ok": True,
                "result": current,
            },
        ]
        query_only = self._plan(
            rows,
            bridge_capabilities=(
                QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
            ),
        )
        self.assertNotIn("council_observation_consumed", query_only)

        managed = self._plan(rows)
        self.assertTrue(managed["council_observation_consumed"])
        self.assertEqual(
            managed["council_decision"]["reason_code"],
            "incumbent_not_outperformed",
        )

    def test_formal_auto_turn_rejects_empty_backend_id_history(self):
        malformed = _result(_payload())
        malformed["backend_id"] = ""
        observed_snapshot = _snapshot()
        observed_snapshot["native_command_history"] = [
            {"command": "save-checkpoint", "ok": True},
            {
                "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                "ok": True,
                "result": malformed,
            },
        ]
        driver = _Driver(
            observed_snapshot,
            _result(_payload()),
            council_management=True,
        )
        result = GameplayBridgeService(driver).auto_turn()
        self.assertEqual(result["status"], "executed")
        self.assertEqual(
            result["selected_step"],
            QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
        )
        self.assertEqual(
            driver.calls,
            [(QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP, 7)],
        )

    def test_formal_planner_queries_before_any_council_decision(self):
        plan = self._plan(
            [{"command": "save-checkpoint", "ok": True}]
        )
        self.assertEqual(plan["phase"], "council_composition_query")
        self.assertEqual(
            plan["selected_step"],
            QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
        )

    def test_vacancy_selects_deterministic_candidate_but_never_submits(self):
        result = _result(_payload())
        plan = self._plan(
            [
                {"command": "save-checkpoint", "ok": True},
                {
                    "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                    "ok": True,
                    "result": result,
                },
            ]
        )
        self.assertEqual(plan["phase"], "council_composition_action_unavailable")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_capability"], ASSIGN_COUNCILLOR_V1_CAPABILITY)
        self.assertEqual(
            plan["council_decision"]["selected_candidate"]["character_id"],
            903,
        )

    def test_vacancy_tie_break_ignores_diagnostic_ordinal(self):
        result = _result(
            _payload(candidates=[(902, 0, 16), (901, 5, 16), (903, 1, 16)])
        )
        plan = self._plan(
            [
                {"command": "save-checkpoint", "ok": True},
                {
                    "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                    "ok": True,
                    "result": result,
                },
            ]
        )
        self.assertEqual(
            plan["council_decision"]["selected_candidate"]["character_id"],
            901,
        )

    def test_occupied_position_keeps_better_or_equal_incumbent(self):
        result = _result(
            _payload(incumbent_character_id=800, incumbent_main_skill=21)
        )
        plan = self._plan(
            [
                {"command": "save-checkpoint", "ok": True},
                {
                    "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                    "ok": True,
                    "result": result,
                },
            ]
        )
        self.assertEqual(plan["phase"], "current_life_family")
        self.assertEqual(plan["selected_step"], "dynasty-review")
        self.assertTrue(plan["council_observation_consumed"])
        self.assertEqual(
            plan["council_decision"]["reason_code"],
            "incumbent_not_outperformed",
        )

    def test_occupied_position_replaces_only_for_explicit_positive_delta(self):
        result = _result(
            _payload(incumbent_character_id=800, incumbent_main_skill=20)
        )
        plan = self._plan(
            [
                {"command": "save-checkpoint", "ok": True},
                {
                    "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                    "ok": True,
                    "result": result,
                },
            ]
        )
        self.assertEqual(plan["phase"], "council_composition_action_unavailable")
        self.assertEqual(plan["council_decision"]["outcome"], "REPLACE_REQUIRED")
        self.assertEqual(
            plan["council_decision"]["selected_candidate"]["character_id"],
            903,
        )

    def test_stale_no_change_observation_is_never_reused(self):
        result = _result(_payload(incumbent_character_id=800))
        plan = self._plan(
            [
                {"command": "save-checkpoint", "ok": True},
                {
                    "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                    "ok": True,
                    "result": result,
                },
            ],
            date_raw=1000 + 24,
        )
        self.assertEqual(
            plan.get("selected_step"),
            QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
        )

    def test_service_and_mcp_preserve_explicit_request_binding(self):
        payload = _payload()
        driver = _Driver(_snapshot(), _result(payload))
        service = GameplayBridgeService(driver)
        response = service.query_council_composition_candidates_v1(
            expected_snapshot_id="native:7",
            public_revision=7,
            native_revision=9,
            date_raw=1000,
            owner_character_id=707,
        )
        self.assertEqual(response["schema"], COUNCIL_COMPOSITION_CANDIDATES_V1_SCHEMA)
        self.assertEqual(
            driver.calls,
            [(QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP, 7)],
        )

        mocked = mock.Mock()
        mocked.query_council_composition_candidates_v1.return_value = {"ok": True}
        self.assertEqual(
            _ck3_query_council_composition_candidates_v1(
                mocked,
                "native:7",
                7,
                9,
                1000,
                707,
            ),
            {"ok": True},
        )
        mocked.query_council_composition_candidates_v1.assert_called_once_with(
            expected_snapshot_id="native:7",
            public_revision=7,
            native_revision=9,
            date_raw=1000,
            owner_character_id=707,
            position_key="councillor_steward",
        )

    def test_explicit_service_query_without_capability_is_unsupported(self):
        driver = _Driver(_snapshot(), _result(_payload()))
        driver.capabilities = lambda: {
            "format_version": 1,
            "backend_id": "native-headless",
            "snapshot": True,
            "wait_for_change": True,
            "bridge_capabilities": [],
            "action_steps": [],
        }
        with self.assertRaises(UnsupportedStepError):
            GameplayBridgeService(
                driver
            ).query_council_composition_candidates_v1(
                expected_snapshot_id="native:7",
                public_revision=7,
                native_revision=9,
                date_raw=1000,
                owner_character_id=707,
            )
        self.assertEqual(driver.calls, [])

    def test_formal_auto_turn_executes_query_then_blocks_before_fake_action(self):
        payload = _payload()
        query_result = _result(payload)
        query_snapshot = _snapshot()
        query_snapshot["native_command_history"] = [
            {"command": "save-checkpoint", "ok": True}
        ]
        query_driver = _Driver(
            query_snapshot,
            query_result,
            council_management=True,
        )
        queried = GameplayBridgeService(query_driver).auto_turn()
        self.assertEqual(queried["status"], "executed")
        self.assertEqual(
            queried["selected_step"],
            QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
        )

        observed_snapshot = _snapshot()
        observed_snapshot["native_command_history"] = [
            {
                "command": "save-checkpoint",
                "ok": True,
            },
            {
                "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                "ok": True,
                "result": query_result,
            },
        ]
        blocked_driver = _Driver(
            observed_snapshot,
            query_result,
            council_management=True,
        )
        blocked = GameplayBridgeService(blocked_driver).auto_turn()
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(
            blocked["plan"]["required_capability"],
            ASSIGN_COUNCILLOR_V1_CAPABILITY,
        )
        self.assertEqual(blocked_driver.calls, [])


if __name__ == "__main__":
    unittest.main()
