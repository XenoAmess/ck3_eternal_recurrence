#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.bridge.zhongguo_manager_governance_snapshot_contract import (
    QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY,
)
from zg361_phase2_b3_manager_governance_action_cell import (
    B3ManagerGovernanceActionCellError,
    run_b3_manager_governance_gameplay_action_cell,
)


PLAYER = 100
MANAGER = 200
SUBORDINATE = 300
CYCLE = 7


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def transition(*, green: bool = True) -> dict[str, object]:
    return {
        "result": "GREEN" if green else "RED",
        "gameplay_action_executed": True,
        "gameplay_action_complete": green,
        "background_business_complete": green,
        "action_ack_is_business_postcondition": False,
        "terminal_condition": (
            "new_allowlisted_roster_lock_receipt" if green else "timeout"
        ),
        "provider_observations": [
            {
                "classification": "postcondition",
                "case_identity": [CYCLE, 903],
            }
        ],
    }


def postcondition(*, source_cycle: int = CYCLE) -> dict[str, object]:
    return {
        "status": "available",
        "unavailable_reason": None,
        "binding": {
            "subject_character_id": MANAGER,
            "owner_character_id": PLAYER,
            "subject_binding_kind": "bounded_ai_direct_manager",
            "bounded_ai_manager_dependency": (
                "zg361-bounded-ai-direct-manager-selection-v1"
            ),
        },
        "readiness": {
            "ready": True,
            "distribution_lifecycle_ready": True,
            "component8_lifecycle_ready": True,
        },
        "f_case": {
            "owner_character_id": available(PLAYER),
            "subject_character_id": available(MANAGER),
        },
        "team_snapshot": {"source_cycle": available(source_cycle)},
        "f035": {"receipt": {}},
        "f032": {"receipt": {}},
    }


class FakeService:
    def __init__(self, *, advertise: bool = True, source_cycle: int = CYCLE) -> None:
        self.advertise = advertise
        self.source_cycle = source_cycle
        self.query: dict[str, object] | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": (
                [QUERY_ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_CAPABILITY]
                if self.advertise
                else []
            )
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "fixture:81",
            "revision": 9,
            "native_revision": 81,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": PLAYER},
        }

    def query_zhongguo_manager_governance_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        subject_character_id: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.query = {
            "request_nonce": request_nonce,
            "expected_revision": expected_revision,
            "subject_character_id": subject_character_id,
            "owner_character_id": owner_character_id,
        }
        return postcondition(source_cycle=self.source_cycle)


class B3ManagerGovernanceActionCellTests(unittest.TestCase):
    def test_green_requires_the_dedicated_joined_postcondition(self) -> None:
        service = FakeService()
        calls: list[dict[str, object]] = []

        def execute(_service: object, **kwargs: object) -> dict[str, object]:
            calls.append(dict(kwargs))
            return transition()

        result = run_b3_manager_governance_gameplay_action_cell(
            service,
            manager_character_id=MANAGER,
            subordinate_character_id=SUBORDINATE,
            background_executor=execute,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertFalse(result["fixture_evidence_is_live"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertEqual(result["source_b1_cycle"], CYCLE)
        self.assertEqual(
            calls,
            [
                {
                    "owner_character_id": MANAGER,
                    "subject_character_id": SUBORDINATE,
                    "request_nonce_prefix": "zg361.b3.manager.b1",
                    "require_transition": True,
                }
            ],
        )
        self.assertEqual(
            service.query,
            {
                "request_nonce": "zg361.b3.manager.post",
                "expected_revision": 9,
                "subject_character_id": MANAGER,
                "owner_character_id": PLAYER,
            },
        )

    def test_capability_and_b1_transition_fail_closed(self) -> None:
        with self.assertRaises(B3ManagerGovernanceActionCellError) as missing:
            run_b3_manager_governance_gameplay_action_cell(
                FakeService(advertise=False),
                manager_character_id=MANAGER,
                subordinate_character_id=SUBORDINATE,
                background_executor=lambda *_args, **_kwargs: transition(),
            )
        self.assertEqual(
            missing.exception.reason_code,
            "manager_governance_provider_unavailable",
        )

        with self.assertRaises(B3ManagerGovernanceActionCellError) as failed:
            run_b3_manager_governance_gameplay_action_cell(
                FakeService(),
                manager_character_id=MANAGER,
                subordinate_character_id=SUBORDINATE,
                background_executor=lambda *_args, **_kwargs: transition(
                    green=False
                ),
            )
        self.assertEqual(
            failed.exception.reason_code,
            "manager_subordinate_transition_not_green",
        )

    def test_unjoined_manager_cycle_cannot_turn_green(self) -> None:
        with self.assertRaises(B3ManagerGovernanceActionCellError) as caught:
            run_b3_manager_governance_gameplay_action_cell(
                FakeService(source_cycle=CYCLE - 1),
                manager_character_id=MANAGER,
                subordinate_character_id=SUBORDINATE,
                background_executor=lambda *_args, **_kwargs: transition(),
            )
        self.assertEqual(
            caught.exception.reason_code,
            "manager_governance_postcondition_not_green",
        )
        self.assertIn(
            "team_snapshot_consumes_b1_cycle",
            caught.exception.evidence["failed_checks"],
        )


if __name__ == "__main__":
    unittest.main()
