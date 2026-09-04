#!/usr/bin/env python3
"""Focused tests for the independent promotion/compensation action cell."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
)
from xar_autoplayer.bridge.zhongguo_promotion_compensation_postcondition_contract import (  # noqa: E402
    QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
)
from zg361_phase2_promotion_compensation_action_cell import (  # noqa: E402
    IMPLEMENTATION_READINESS,
    PromotionCompensationActionCellError,
    run_promotion_compensation_gameplay_action_cell,
)


OWNER = 100
SUBJECT = 200
CYCLE = 14
CASE = 14_007
SOURCE_REVISION = 80
RESULT_REVISION = 83
SOURCE_NATIVE_REVISION = 800
RESULT_NATIVE_REVISION = 803
SOURCE_INSTANCE = 4_001
RESULT_INSTANCE = 4_002
GENERATION = 4
DATE_RAW = 730_122
RECEIPT = CASE


def _available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def _identity(revision: int, *, subject: int = SUBJECT) -> dict[str, object]:
    return {
        "owner_character_id": _available(OWNER),
        "subject_character_id": _available(subject),
        "cycle_serial": _available(CYCLE),
        "case_serial": _available(CASE),
        "revision": _available(revision),
    }


def _character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def _scalar_scope() -> dict[str, object]:
    return {
        "status": "available",
        "typed_identity": {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        },
    }


class _FakeService:
    def __init__(self) -> None:
        self.at_result = False
        self.selected = False
        self.provider_option = 1
        self.provider_subject = SUBJECT
        self.choice_receipt = RECEIPT
        self.compensation_receipt = RECEIPT
        self.result_generation = GENERATION
        self.missing_capability: str | None = None
        self.provider_calls = 0

    def capabilities(self) -> dict[str, object]:
        bridge = [
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
            QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
            "game.command.select-event-option-N",
        ]
        if self.missing_capability in bridge:
            bridge.remove(self.missing_capability)
        return {"bridge_capabilities": bridge, "action_steps": []}

    def snapshot(self) -> dict[str, object]:
        result = self.at_result
        return {
            "snapshot_id": "promo:result" if result else "promo:source",
            "revision": RESULT_REVISION if result else SOURCE_REVISION,
            "native_revision": (
                RESULT_NATIVE_REVISION if result else SOURCE_NATIVE_REVISION
            ),
            "date_raw": DATE_RAW + (1 if result else 0),
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": OWNER},
            "diagnostics": {
                "connection_generation": (
                    self.result_generation if result else GENERATION
                )
            },
            "active_event": {
                "instance_id": RESULT_INSTANCE if result else SOURCE_INSTANCE,
                "option_count": 3,
            },
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        snapshot = self.snapshot()
        source = not self.at_result
        expected_instance = SOURCE_INSTANCE if source else RESULT_INSTANCE
        if event_instance_id != expected_instance:
            raise ValueError("wrong fake event instance")
        saved_scopes: list[dict[str, object]] = []
        if source:
            saved_scopes = [
                {
                    "name": "zg361_pp_prompt_owner",
                    "scope": _character_scope(OWNER),
                },
                {
                    "name": "zg361_pp_prompt_subject",
                    "scope": _character_scope(SUBJECT),
                },
                *[
                    {"name": name, "scope": _scalar_scope()}
                    for name in (
                        "zg361_pp_prompt_case",
                        "zg361_pp_prompt_cycle",
                        "zg361_pp_prompt_mechanism",
                        "zg361_pp_prompt_state",
                    )
                ],
            ]
        return {
            "status": "available",
            "binding": {
                "snapshot_id": snapshot["snapshot_id"],
                "revision": expected_revision,
                "native_revision": snapshot["native_revision"],
                "date_raw": snapshot["date_raw"],
                "event_instance_id": event_instance_id,
            },
            "current_event_window_context": {
                "status": "available",
                "event_definition_key": "zg361pp.147" if source else "zg361comp.1",
                "current_event_instance_id": event_instance_id,
                "snapshot_revision": snapshot["native_revision"],
                "date_raw": snapshot["date_raw"],
                "root_scope": _character_scope(OWNER),
                "saved_scopes": saved_scopes,
                "options": [
                    {
                        "rendered_index": index,
                        "native_option_index": index,
                        "shown": True,
                        "enabled": True,
                    }
                    for index in range(3)
                ],
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                    "option_presentation_ready": True,
                },
            },
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selected = True
        return {
            "step": f"select-event-option-{option_number}",
            "accepted": True,
            "status": "submitted",
            "event_instance_id": event_instance_id,
            "option_number": option_number,
            "expected_revision": expected_revision,
        }

    def query_zhongguo_promotion_compensation_postcondition_v1(
        self, request_nonce: str, *, expected_revision: int
    ) -> dict[str, object]:
        self.provider_calls += 1
        snapshot = self.snapshot()
        readiness = {
            key: True
            for key in (
                "player_owner_binding_ready",
                "portfolio_subject_binding_ready",
                "source_identity_ready",
                "result_identity_ready",
                "frozen_case_identity_ready",
                "promotion_choice_receipt_ready",
                "compensation_receipt_posted",
                "same_case_identity_ready",
                "revision_binding_ready",
                "receipt_serials_ready",
                "same_frame_ready",
                "ready",
            )
        }
        return {
            "schema_version": 1,
            "status": "available",
            "capability": QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY,
            "source_backend_id": "native-headless",
            "request_nonce": request_nonce,
            "snapshot_revision": RESULT_NATIVE_REVISION,
            "date_raw": snapshot["date_raw"],
            "paused": True,
            "player_character_id": OWNER,
            "subject_character_id": self.provider_subject,
            "promotion_compensation": {
                "source_identity": _identity(
                    3, subject=self.provider_subject
                ),
                "result_identity": _identity(
                    4, subject=self.provider_subject
                ),
                "frozen_case": {
                    "identity": _identity(4, subject=self.provider_subject),
                    "frozen": True,
                },
                "promotion_choice": {
                    "identity": _identity(3, subject=self.provider_subject),
                    "option_number": _available(self.provider_option),
                    "receipt_serial": _available(self.choice_receipt),
                    "active": _available(True),
                    "consumed": _available(True),
                },
                "compensation_receipt": {
                    "identity": _identity(4, subject=self.provider_subject),
                    "operation_id": _available(82),
                    "option_number": _available(3),
                    "receipt_serial": _available(self.compensation_receipt),
                    "active": _available(True),
                    "consumed": _available(True),
                    "posted": _available(True),
                },
            },
            "readiness": readiness,
            "unavailable_reason": None,
            "binding": {
                "request_nonce": request_nonce,
                "snapshot_id": snapshot["snapshot_id"],
                "revision": expected_revision,
                "native_revision": snapshot["native_revision"],
                "connection_generation": self.result_generation,
                "date_raw": snapshot["date_raw"],
                "paused": True,
                "player_character_id": OWNER,
                "subject_character_id": self.provider_subject,
                "owner_character_id": OWNER,
                "expected_revision": expected_revision,
            },
        }


def _advance(
    service: _FakeService,
    request: object,
    ack: object,
) -> dict[str, object]:
    if not service.selected:
        raise ValueError("selection was not submitted")
    service.at_result = True
    return {
        "result": "GREEN",
        "result_event_definition_key": "zg361comp.1",
        "action_ack_is_business_postcondition": False,
        "request": copy.deepcopy(request),
        "ack": copy.deepcopy(ack),
    }


class PromotionCompensationActionCellTests(unittest.TestCase):
    def test_green_requires_request_provider_and_receipt_lineage(self) -> None:
        service = _FakeService()
        result = run_promotion_compensation_gameplay_action_cell(
            service, advance_to_result=_advance
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["implementation_readiness"], IMPLEMENTATION_READINESS)
        self.assertFalse(result["production_live"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertEqual(result["action_request"]["option_number"], 1)
        self.assertEqual(result["action_request"]["subject_character_id"], SUBJECT)
        self.assertTrue(all(result["checks"].values()))
        self.assertEqual(result["business_postcondition"]["result"], "GREEN")
        self.assertEqual(service.provider_calls, 1)

    def test_ack_only_transition_is_rejected_before_provider_query(self) -> None:
        service = _FakeService()

        def ack_only(_service: object, _request: object, ack: object) -> object:
            return ack

        with self.assertRaises(PromotionCompensationActionCellError) as caught:
            run_promotion_compensation_gameplay_action_cell(
                service, advance_to_result=ack_only  # type: ignore[arg-type]
            )
        self.assertEqual(
            caught.exception.reason_code,
            "transition_driver_did_not_reach_result_event",
        )
        self.assertFalse(
            caught.exception.evidence["action_ack_is_business_postcondition"]
        )
        self.assertEqual(service.provider_calls, 0)

    def test_provider_choice_must_match_the_action_request(self) -> None:
        service = _FakeService()
        service.provider_option = 2
        with self.assertRaises(PromotionCompensationActionCellError) as caught:
            run_promotion_compensation_gameplay_action_cell(
                service, advance_to_result=_advance
            )
        self.assertIn(
            "promotion_choice_matches_action_request",
            caught.exception.reason_code,
        )

    def test_provider_subject_and_receipt_must_remain_joined(self) -> None:
        for mutation in ("subject", "receipt"):
            with self.subTest(mutation=mutation):
                service = _FakeService()
                if mutation == "subject":
                    service.provider_subject = SUBJECT + 1
                else:
                    service.compensation_receipt = RECEIPT + 1
                with self.assertRaises(PromotionCompensationActionCellError) as caught:
                    run_promotion_compensation_gameplay_action_cell(
                        service, advance_to_result=_advance
                    )
                self.assertIn("provider/action lineage failed", caught.exception.reason_code)

    def test_connection_generation_drift_is_rejected(self) -> None:
        service = _FakeService()
        service.result_generation = GENERATION + 1
        with self.assertRaises(PromotionCompensationActionCellError) as caught:
            run_promotion_compensation_gameplay_action_cell(
                service, advance_to_result=_advance
            )
        self.assertEqual(
            caught.exception.reason_code, "source_result_snapshot_lineage_drifted"
        )

    def test_default_off_provider_capability_blocks_before_action(self) -> None:
        service = _FakeService()
        service.missing_capability = (
            QUERY_ZHONGGUO_PROMOTION_COMPENSATION_V1_CAPABILITY
        )
        with self.assertRaises(PromotionCompensationActionCellError) as caught:
            run_promotion_compensation_gameplay_action_cell(
                service, advance_to_result=_advance
            )
        self.assertEqual(
            caught.exception.reason_code, "mcp_capability_profile_incomplete"
        )
        self.assertFalse(service.selected)


if __name__ == "__main__":
    unittest.main()
