from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.zhongguo_ai_owned_case_action import (  # noqa: E402
    run_zhongguo_ai_owned_case_background_action,
)
from xar_autoplayer.bridge.zhongguo_ai_owned_case_snapshot_contract import (  # noqa
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
)


OWNER = 72_001
SUBJECT = 72_002
PLAYER = 32_904


def _available(value: object) -> dict[str, object]:
    return {
        "status": "available",
        "value": value,
        "unavailable_reason": None,
    }


def _snapshot(
    revision: int,
    date_raw: int,
    *,
    active_event_id: int | None = None,
) -> dict[str, object]:
    return {
        "snapshot_id": f"native:{revision}",
        "revision": revision,
        "native_revision": revision + 100,
        "date_raw": date_raw,
        "paused": True,
        "map_ready": True,
        "played_character": {
            "character_id": PLAYER,
            "alive": True,
        },
        "active_event": (
            None
            if active_event_id is None
            else {
                "instance_id": active_event_id,
                "option_count": 2,
            }
        ),
    }


def _unavailable_response(
    revision: int,
    *,
    reason: str = "case_not_found",
) -> dict[str, object]:
    return {
        "status": "unavailable",
        "unavailable_reason": reason,
        "binding": {
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "paused": True,
            "revision": revision,
        },
        "readiness": {"ready": False},
    }


def _recorded_response(
    revision: int,
    *,
    cycle_serial: int = 7,
    case_serial: int = 903,
    tier: int = 3,
    tier_key: str = "duchy",
    visible_event_allowed: bool = False,
) -> dict[str, object]:
    return {
        "status": "available",
        "unavailable_reason": None,
        "binding": {
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "paused": True,
            "revision": revision,
        },
        "readiness": {"ready": True},
        "owner_eligibility": {
            "owner_character_id": _available(OWNER),
            "owner_alive": _available(True),
            "owner_is_ai": _available(True),
            "primary_title_tier_raw": _available(tier),
            "primary_title_tier_key": _available(tier_key),
            "government_key": _available("celestial_government"),
            "subject_immediate_liege_character_id": _available(OWNER),
            "subject_is_direct_subject": _available(True),
            "authorized": _available(True),
        },
        "case": {
            "owner_character_id": _available(OWNER),
            "subject_character_id": _available(SUBJECT),
            "cycle_serial": _available(cycle_serial),
            "case_serial": _available(case_serial),
        },
        "route": {
            "kind": _available("authorized_ai_background"),
            "visible_event_allowed": _available(visible_event_allowed),
            "owner_is_ai": _available(True),
            "manager_eligible": _available(True),
            "direct_subject_eligible": _available(True),
        },
        "policy": {
            "policy_id": _available("mechanism_039"),
            "choice": _available(1),
        },
        "operation": {
            "operation_id": _available(39),
            "operation_key": _available("roster_lock"),
            "hook": _available("roster_lock"),
            "pre_state": _available(1),
            "post_state": _available(1),
        },
        "receipt": {
            "status": "recorded",
            "key": _available("roster_lock"),
            "owner_character_id": _available(OWNER),
            "subject_character_id": _available(SUBJECT),
            "cycle_serial": _available(cycle_serial),
            "case_serial": _available(case_serial),
            "state": _available(1),
            "choice": _available(1),
        },
    }


class _FakeService:
    def __init__(
        self,
        snapshots: list[dict[str, object]],
        provider_responses: list[dict[str, object]],
        *,
        acknowledgement: dict[str, object] | None = None,
    ) -> None:
        if len(snapshots) != len(provider_responses):
            raise ValueError("one provider response is required per snapshot")
        self.snapshots = copy.deepcopy(snapshots)
        self.provider_responses = copy.deepcopy(provider_responses)
        self.index = 0
        self.execute_calls: list[tuple[str, int | None]] = []
        self.provider_calls: list[tuple[int, int, str, int | None]] = []
        self.event_query_calls: list[tuple[int, int]] = []
        self.acknowledgement = acknowledgement or {
            "step": "life-advance",
            "accepted": True,
            "status": "submitted",
        }

    def capabilities(self) -> dict[str, object]:
        return {
            "action_steps": ["life-advance"],
            "bridge_capabilities": [
                QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
            ],
        }

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshots[self.index])

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        self.execute_calls.append((step, expected_revision))
        if self.index + 1 >= len(self.snapshots):
            raise RuntimeError("fake timeline exhausted")
        self.index += 1
        return copy.deepcopy(self.acknowledgement)

    def query_zhongguo_ai_owned_case_snapshot_v1(
        self,
        owner_character_id: int,
        subject_character_id: int,
        request_nonce: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        self.provider_calls.append(
            (
                owner_character_id,
                subject_character_id,
                request_nonce,
                expected_revision,
            )
        )
        return copy.deepcopy(self.provider_responses[self.index])

    def query_current_event_window_context_v1(
        self,
        event_instance_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]:
        self.event_query_calls.append((event_instance_id, expected_revision))
        return {
            "status": "available",
            "event_definition_key": "unrelated.player.event.1",
        }


class ZhongguoAiOwnedCaseActionTests(unittest.TestCase):
    def test_green_requires_fresh_provider_receipt_not_action_ack(self) -> None:
        service = _FakeService(
            [
                _snapshot(10, 53_147_016),
                _snapshot(11, 53_147_040),
                _snapshot(12, 53_147_064),
            ],
            [
                _unavailable_response(10),
                _unavailable_response(11),
                _recorded_response(12),
            ],
            acknowledgement={
                "step": "life-advance",
                "accepted": False,
                "status": "synthetic_ack_not_authoritative",
            },
        )

        report = run_zhongguo_ai_owned_case_background_action(
            service,
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            max_advance_steps=2,
            max_elapsed_days=2,
        )

        self.assertEqual("GREEN", report["result"])
        self.assertTrue(report["gameplay_action_executed"])
        self.assertTrue(report["background_business_complete"])
        self.assertFalse(report["action_ack_is_business_postcondition"])
        self.assertEqual(
            "new_allowlisted_roster_lock_receipt",
            report["terminal_condition"],
        )
        self.assertEqual(2, len(service.execute_calls))
        self.assertEqual(3, len(service.provider_calls))
        self.assertTrue(
            report["timeline_actions"][-1]["business_postcondition"]
        )

    def test_ack_without_provider_postcondition_remains_red(self) -> None:
        service = _FakeService(
            [
                _snapshot(20, 53_147_016),
                _snapshot(21, 53_147_040),
                _snapshot(22, 53_147_064),
            ],
            [
                _unavailable_response(20),
                _unavailable_response(21),
                _unavailable_response(22),
            ],
        )

        report = run_zhongguo_ai_owned_case_background_action(
            service,
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            max_advance_steps=2,
            max_elapsed_days=2,
        )

        self.assertEqual("RED", report["result"])
        self.assertTrue(report["gameplay_action_executed"])
        self.assertFalse(report["background_business_complete"])
        self.assertEqual(
            "ai_owned_case_producer_seed_unreachable",
            report["terminal_condition"],
        )

    def test_county_or_lower_owner_is_rejected_before_advancing(self) -> None:
        service = _FakeService(
            [_snapshot(30, 53_147_016)],
            [_recorded_response(30, tier=2, tier_key="county")],
        )

        report = run_zhongguo_ai_owned_case_background_action(
            service,
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            max_advance_steps=1,
            max_elapsed_days=1,
        )

        self.assertEqual("RED", report["result"])
        self.assertEqual("initial_provider_blocked", report["terminal_condition"])
        self.assertIn("duke_plus", report["failure_reason"])
        self.assertEqual([], service.execute_calls)

    def test_visible_event_is_queried_and_never_selected(self) -> None:
        service = _FakeService(
            [
                _snapshot(40, 53_147_016),
                _snapshot(41, 53_147_040, active_event_id=913),
            ],
            [
                _unavailable_response(40),
                _recorded_response(41),
            ],
        )

        report = run_zhongguo_ai_owned_case_background_action(
            service,
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            max_advance_steps=1,
            max_elapsed_days=1,
        )

        self.assertEqual("RED", report["result"])
        self.assertEqual(
            "player_visible_event_interrupted", report["terminal_condition"]
        )
        self.assertEqual([(913, 41)], service.event_query_calls)
        self.assertEqual(1, len(service.provider_calls))
        self.assertEqual(
            "unrelated.player.event.1",
            report["current_event_observation"]["event_definition_key"],
        )

    def test_existing_receipt_is_only_idempotent_when_explicitly_requested(
        self,
    ) -> None:
        strict_service = _FakeService(
            [
                _snapshot(50, 53_147_016),
                _snapshot(51, 53_147_040),
            ],
            [
                _recorded_response(50),
                _recorded_response(51),
            ],
        )
        strict = run_zhongguo_ai_owned_case_background_action(
            strict_service,
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            max_advance_steps=1,
            max_elapsed_days=1,
        )
        self.assertEqual("RED", strict["result"])
        self.assertEqual(
            "ai_owned_case_transition_unobserved",
            strict["terminal_condition"],
        )

        idempotent_service = _FakeService(
            [_snapshot(60, 53_147_016)],
            [_recorded_response(60)],
        )
        idempotent = run_zhongguo_ai_owned_case_background_action(
            idempotent_service,
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            max_advance_steps=1,
            max_elapsed_days=1,
            require_transition=False,
        )
        self.assertEqual("GREEN", idempotent["result"])
        self.assertFalse(idempotent["gameplay_action_executed"])
        self.assertTrue(idempotent["background_business_complete"])
        self.assertEqual([], idempotent_service.execute_calls)

    def test_visible_route_claim_is_rejected(self) -> None:
        service = _FakeService(
            [_snapshot(70, 53_147_016)],
            [_recorded_response(70, visible_event_allowed=True)],
        )
        report = run_zhongguo_ai_owned_case_background_action(
            service,
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            max_advance_steps=1,
            max_elapsed_days=1,
        )
        self.assertEqual("RED", report["result"])
        self.assertIn("visible_event_allowed", report["failure_reason"])
        self.assertEqual([], service.execute_calls)


if __name__ == "__main__":
    unittest.main()
