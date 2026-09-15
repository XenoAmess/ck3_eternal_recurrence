from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.council_assign_councillor_action_contract import (
    ASSIGN_COUNCILLOR_V1_CAPABILITY,
    ASSIGN_COUNCILLOR_V1_STEP,
    build_assign_councillor_request_v1,
    normalize_assign_councillor_ack_v1,
    normalize_assign_councillor_receipt_v1,
)
from xar_autoplayer.bridge.council_composition_candidates_contract import (
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _action_steps,
)
from xar_autoplayer.native_auto_run import (
    _council_assignment_postcondition_issue,
)


def _observation(*, incumbent=800, incumbent_skill=10):
    vacant = incumbent is None
    route = "assign" if vacant else "replace"
    return {
        "snapshot": {
            "snapshot_id": "native:7",
            "public_revision": 7,
            "native_revision": 9,
            "date_raw": 1000,
            "paused": True,
        },
        "owner_character_id": 707,
        "position": {
            "position_key": "councillor_steward",
            "incumbent_character_id": incumbent,
            "incumbent_main_skill": (
                None
                if vacant
                else {"key": "stewardship", "value": incumbent_skill}
            ),
            "vacant": vacant,
            "action_route": route,
        },
        "candidate_collection_complete": True,
        "candidates": [
            {
                "character_id": 901,
                "native_collection_ordinal": 3,
                "eligible": True,
                "eligibility_reason": "native_candidate_provider_accepted",
                "main_skill": {"key": "stewardship", "value": 20},
                "action_route": route,
            }
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


def _ack(request):
    return {
        "status": "native_helper_invoked_verification_pending",
        "failure": "none",
        "action_request_id": request.request_id,
        "pre_snapshot_id": request.expected_snapshot_id,
        "pre_public_revision": request.expected_public_revision,
        "pre_native_revision": request.expected_native_revision,
        "pre_date_raw": request.expected_date_raw,
        "owner_character_id": request.expected_owner_character_id,
        "position_key": request.position_key,
        "active_task_id": 333,
        "candidate_character_id": request.candidate_character_id,
        "had_incumbent": request.expected_has_incumbent,
        "previous_incumbent_character_id": (
            request.expected_incumbent_character_id
        ),
        "route": (
            "replace_incumbent"
            if request.expected_has_incumbent
            else "assign_vacant"
        ),
        "native_helper_invoked": True,
        "queue_acceptance_observed": False,
        "verification_pending": True,
        "native_reason_key": "",
    }


def _receipt(ack):
    return {
        "status": "applied",
        "rejected_action_failure": "none",
        "action_request_id": ack["action_request_id"],
        "post_snapshot_id": "native:8",
        "post_public_revision": 8,
        "post_native_revision": 10,
        "post_date_raw": 1000,
        "owner_character_id": ack["owner_character_id"],
        "position_key": "councillor_steward",
        "incumbent_character_id": ack["candidate_character_id"],
        "incumbent_identity_round_trip": True,
        "postcondition_verified": True,
        "reason": "",
    }


def _query_result(observation):
    return {
        "step": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
        "accepted": True,
        "status": "available",
        "query_sequence": 3,
        "snapshot_revision": 9,
        "council_composition_candidates": copy.deepcopy(observation),
        "backend_id": "native-headless",
        "council_composition_candidates_ready": True,
        "queried_snapshot_id": "native:7",
        "queried_revision": 7,
        "queried_native_revision": 9,
    }


def _snapshot(observation):
    return {
        "snapshot_id": "native:7",
        "revision": 7,
        "native_revision": 9,
        "date_raw": 1000,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 707, "alive": True},
        "native_command_history": [
            {"command": "save-checkpoint", "ok": True},
            {
                "command": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                "ok": True,
                "result": _query_result(observation),
            },
        ],
    }


class _FormalDriver:
    def __init__(self, observation):
        self.observation = observation
        self.snapshot = _snapshot(observation)
        self.calls = []

    def capabilities(self):
        return {
            "format_version": 1,
            "backend_id": "native-headless",
            "snapshot": True,
            "wait_for_change": True,
            "bridge_capabilities": [
                QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
                ASSIGN_COUNCILLOR_V1_CAPABILITY,
            ],
            "action_steps": [
                QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                ASSIGN_COUNCILLOR_V1_STEP,
                "life-advance",
            ],
        }

    def take_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def execute_step(self, step, *, expected_revision=None):
        raise AssertionError(f"untyped execution used for {step}")

    def assign_councillor_v1(
        self, observation, *, candidate_character_id, expected_revision
    ):
        self.calls.append(
            (copy.deepcopy(observation), candidate_character_id, expected_revision)
        )
        return {
            "step": ASSIGN_COUNCILLOR_V1_STEP,
            "accepted": True,
            "status": "applied",
            "progress_status": "postcondition",
            "backend_id": "native-headless",
        }


class _NativeActionHarness:
    command_timeout_seconds = 1.0

    def __init__(self, observation):
        self.observation = observation
        self.current = _snapshot(observation)
        self.calls = []
        self.ack = None

    def take_snapshot(self):
        return copy.deepcopy(self.current)

    def capabilities(self):
        return _FormalDriver(self.observation).capabilities()

    def _execute_primitive_step(self, step, **kwargs):
        self.calls.append((step, copy.deepcopy(kwargs)))
        if step == ASSIGN_COUNCILLOR_V1_STEP:
            fields = kwargs["request_fields"]
            self.assert_request_fields = copy.deepcopy(fields)
            request = build_assign_councillor_request_v1(
                self.observation,
                candidate_character_id=fields["candidate_character_id"],
                request_id=kwargs["protocol_request_id"],
            )
            self.ack = _ack(request)
            return {
                "step": step,
                "accepted": True,
                "status": self.ack["status"],
                "query_sequence": 10,
                "snapshot_revision": 9,
                "council_assign_councillor_ack": copy.deepcopy(self.ack),
                "backend_id": "native-headless",
            }
        self.current = {
            **self.current,
            "snapshot_id": "native:8",
            "revision": 8,
            "native_revision": 10,
        }
        return {
            "step": step,
            "accepted": True,
            "status": "applied",
            "query_sequence": 11,
            "snapshot_revision": 10,
            "council_assign_councillor_receipt": _receipt(self.ack),
            "backend_id": "native-headless",
        }

    def _wait_for_snapshot(self, snapshot, predicate, *, timeout_seconds):
        return self.take_snapshot()


class CouncilAssignCouncillorContractTests(unittest.TestCase):
    def test_native_capability_projects_formal_action_step_only_when_paused(self):
        self.assertIn(
            ASSIGN_COUNCILLOR_V1_STEP,
            _action_steps([ASSIGN_COUNCILLOR_V1_CAPABILITY], paused=True),
        )
        self.assertNotIn(
            ASSIGN_COUNCILLOR_V1_STEP,
            _action_steps([ASSIGN_COUNCILLOR_V1_CAPABILITY], paused=False),
        )

    def test_request_ack_and_receipt_remain_distinct(self):
        request = build_assign_councillor_request_v1(
            _observation(),
            candidate_character_id=901,
            request_id="council-1",
        )
        ack = normalize_assign_councillor_ack_v1(
            _ack(request), expected_request=request
        )
        self.assertTrue(ack["verification_pending"])
        self.assertFalse(ack["queue_acceptance_observed"])
        receipt = normalize_assign_councillor_receipt_v1(
            _receipt(ack), expected_ack=ack
        )
        self.assertEqual(receipt["status"], "applied")

    def test_helper_ack_cannot_be_relabelled_applied(self):
        request = build_assign_councillor_request_v1(
            _observation(incumbent=None),
            candidate_character_id=901,
            request_id="council-2",
        )
        invalid = _ack(request)
        invalid["status"] = "applied"
        with self.assertRaisesRegex(ValueError, "status is invalid"):
            normalize_assign_councillor_ack_v1(
                invalid, expected_request=request
            )

    def test_formal_auto_turn_uses_typed_assignment_executor(self):
        observation = _observation()
        driver = _FormalDriver(observation)
        result = GameplayBridgeService(driver).auto_turn()
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["selected_step"], ASSIGN_COUNCILLOR_V1_STEP)
        self.assertEqual(len(driver.calls), 1)
        self.assertEqual(driver.calls[0][1:], (901, 7))

    def test_native_driver_uses_distinct_submit_and_receipt_requests(self):
        observation = _observation()
        harness = _NativeActionHarness(observation)
        result = (
            NativeHeadlessGameplayDriver._assign_councillor_v1_unrecorded(
                harness,
                observation,
                candidate_character_id=901,
                expected_revision=7,
            )
        )
        self.assertEqual(
            [row[0] for row in harness.calls],
            [
                ASSIGN_COUNCILLOR_V1_STEP,
                "query-assign-councillor-receipt-v1",
            ],
        )
        self.assertNotIn("request_id", harness.assert_request_fields)
        self.assertEqual(result["status"], "applied")
        self.assertEqual(result["progress_status"], "postcondition")

    def test_native_auto_run_requires_receipt_to_match_public_frame(self):
        request = build_assign_councillor_request_v1(
            _observation(), candidate_character_id=901, request_id="council-3"
        )
        ack = _ack(request)
        receipt = _receipt(ack)
        result = {
            "council_assign_councillor_ack": ack,
            "council_assign_councillor_receipt": receipt,
        }
        after = {
            "paused": True,
            "snapshot_id": "native:8",
            "revision": 8,
            "native_revision": 10,
            "date_raw": 1000,
            "played_character": {"character_id": 707},
        }
        self.assertIsNone(
            _council_assignment_postcondition_issue(
                ASSIGN_COUNCILLOR_V1_STEP, result, after
            )
        )
        stale = {**after, "snapshot_id": "native:7"}
        self.assertEqual(
            _council_assignment_postcondition_issue(
                ASSIGN_COUNCILLOR_V1_STEP, result, stale
            ),
            "receipt_or_public_binding_mismatch",
        )


if __name__ == "__main__":
    unittest.main()
