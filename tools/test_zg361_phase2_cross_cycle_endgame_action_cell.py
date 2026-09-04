#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
BRIDGE_RESEARCH = ROOT / "ck3_autonomous_player" / "native_bridge" / "research"
sys.path.insert(0, str(TOOLS))

from zg361_phase2_cross_cycle_endgame_action_cell import (  # noqa: E402
    CrossCycleEndgameCellError,
    EndgameSubjectProofSession,
    run_cross_cycle_endgame_action_cell,
)
from zg361_phase2_cross_cycle_endgame_preflight import (  # noqa: E402
    CrossCycleEndgamePreflightError,
    preflight_cross_cycle_endgame_action_cell,
)


OWNER = 29037
SUBJECT = 29038
CYCLE = 16
CASE = 16056
SOURCE_DATE = 9000
RESULT_DATE = 9010
CHECKPOINT_SHA = "A" * 64
LINEAGE = "phase2-endgame-unit-lineage"


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def event_context(key: str, event_id: int, revision: int, date_raw: int) -> dict[str, object]:
    return {
        "status": "available",
        "event_definition_key": key,
        "current_event_instance_id": event_id,
        "snapshot_revision": revision,
        "date_raw": date_raw,
        "root_scope": character_scope(OWNER),
        "saved_scopes": [
            {
                "name": "zg361_we_al_owner",
                "name_identifier": 1,
                "scope": character_scope(OWNER),
            },
            {
                "name": "zg361_we_al_subject",
                "name_identifier": 2,
                "scope": character_scope(SUBJECT),
            },
            {"name": "zg361_we_al_cycle", "name_identifier": 3, "scope": {}},
            {"name": "zg361_we_al_case", "name_identifier": 4, "scope": {}},
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "resolved_name": f"endgame option {index + 1}",
            }
            for index in range(3)
        ],
        "readiness": {
            "event_definition_identity_ready": True,
            "root_scope_ready": True,
            "saved_scopes_ready": True,
            "option_presentation_ready": True,
        },
    }


def source_restore() -> dict[str, object]:
    return {
        "schema_version": 1,
        "result": "GREEN",
        "span_id": "phase2_cross_cycle_endgame",
        "handler": "capture_cross_cycle_endgame",
        "checkpoint": {
            "path": "Z:/fixture/endgame.ck3",
            "bytes": 4096,
            "sha256": "B" * 64,
            "save_lineage_id": LINEAGE,
        },
        "expected": {
            "event_definition_key": "zg361we.356",
            "owner_character_id": OWNER,
            "player_character_id": OWNER,
            "date_raw": SOURCE_DATE,
        },
        "restore_receipt": {
            "result": "GREEN",
            "provider_observed": True,
            "checkpoint_sha256": "B" * 64,
            "save_lineage_id": LINEAGE,
            "event_definition_key": "zg361we.356",
            "owner_character_id": OWNER,
            "player_character_id": OWNER,
            "date_raw": SOURCE_DATE,
            "fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        },
        "fixture_used": False,
        "console_used": False,
    }


def identity_group(state: int | None = None) -> dict[str, object]:
    result = {
        "owner_character_id": available(OWNER),
        "subject_character_id": available(SUBJECT),
        "cycle_serial": available(CYCLE),
        "case_serial": available(CASE),
    }
    if state is not None:
        result["state"] = available(state)
    return result


class FakeOwnerService:
    def __init__(self, *, advertise: bool = True) -> None:
        self.advertise = advertise
        self.stage = "source"
        self.revision = 10
        self.native_revision = 110
        self.date_raw = SOURCE_DATE
        self.event_id = 3561
        self.selections: list[tuple[int, int, int]] = []

    def capabilities(self) -> dict[str, object]:
        values = [
            "game.command.query-current-event-window-context-v1",
            "game.command.select-event-option-N",
            "game.command.query-zhongguo-workforce-collective-snapshot-v1",
        ]
        return {"bridge_capabilities": values if self.advertise else values[:-1]}

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": f"owner:{self.stage}:{self.revision}",
            "revision": self.revision,
            "native_revision": self.native_revision,
            "date_raw": self.date_raw,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": OWNER},
            "active_event": {"instance_id": self.event_id, "option_count": 3},
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_instance_id != self.event_id or expected_revision != self.revision:
            raise AssertionError("event query crossed its fake frame")
        key = "zg361we.356" if self.stage == "source" else "zg361we.361"
        return {
            "status": "available",
            "current_event_window_context": event_context(
                key, self.event_id, self.native_revision, self.date_raw
            ),
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.selections.append((option_number, event_instance_id, expected_revision))
        return {"accepted": True, "status": "submitted"}

    def complete(self) -> None:
        self.stage = "result"
        self.revision = 15
        self.native_revision = 115
        self.date_raw = RESULT_DATE
        self.event_id = 3611


class FakeSubjectService:
    def __init__(self, *, due_cycle: int = CYCLE + 1, status: str = "ready") -> None:
        self.due_cycle = due_cycle
        self.status = status
        self.queries: list[dict[str, object]] = []

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "subject:result:30",
            "revision": 30,
            "native_revision": 130,
            "date_raw": RESULT_DATE,
            "paused": True,
            "map_ready": True,
            "played_character": {"character_id": SUBJECT},
            "active_event": None,
        }

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.queries.append(
            {
                "request_nonce": request_nonce,
                "expected_revision": expected_revision,
                "owner_character_id": owner_character_id,
            }
        )
        ready = self.status == "ready"
        consumed = self.status == "consumed"
        return {
            "schema_version": 1,
            "status": "available",
            "player_character_id": SUBJECT,
            "subject_character_id": SUBJECT,
            "requested_owner_character_id": OWNER,
            "binding": {
                "snapshot_id": "subject:result:30",
                "revision": 30,
                "native_revision": 130,
                "date_raw": RESULT_DATE,
                "player_character_id": SUBJECT,
                "subject_character_id": SUBJECT,
                "owner_character_id": OWNER,
            },
            "al_case": identity_group(5),
            "m360_receipt": {**identity_group(4), "choice": available(3)},
            "route_c_debt": {
                **identity_group(4),
                "open": available(True),
                "consumed": available(False),
                "due_cycle_serial": available(self.due_cycle),
            },
            "charter_gate": {
                "status": self.status,
                **identity_group(5),
                "evidence_count": available(3),
                "evidence_ready": available(ready),
                "evidence_consumed": available(consumed),
                "prepared_charter_id": available(36101),
                "adopted_cycle_serial": available(CYCLE),
                "effective_cycle_serial": available(CYCLE + 1),
            },
            "readiness": {"ready": True},
        }


def completion(service: FakeOwnerService, _binding: object) -> dict[str, object]:
    service.complete()
    return {
        "result": "GREEN",
        "m360_route": "C",
        "action_ack_only": False,
        "fixture_used": False,
        "console_used": False,
        "result_checkpoint": {
            "bytes": 8192,
            "sha256": CHECKPOINT_SHA,
            "save_lineage_id": LINEAGE,
            "event_definition_key": "zg361we.361",
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "player_character_id": OWNER,
            "date_raw": RESULT_DATE,
        },
    }


def subject_session(
    result: object, *, due_cycle: int = CYCLE + 1
) -> EndgameSubjectProofSession:
    return EndgameSubjectProofSession(
        service=FakeSubjectService(due_cycle=due_cycle),
        transition_receipt={
            "result": "GREEN",
            "provider_observed": True,
            "action_ack_only": False,
            "from_player_character_id": OWNER,
            "to_player_character_id": SUBJECT,
            "date_raw": RESULT_DATE,
            "restored_checkpoint_sha256": CHECKPOINT_SHA,
            "save_lineage_id": LINEAGE,
            "typed_event_fixture_used": True,
            "business_state_fixture_used": False,
            "console_used": False,
            "generic_character_rebind_used": False,
        },
    )


class CrossCycleEndgameActionCellTests(unittest.TestCase):
    def test_preflight_is_read_only_and_keeps_live_pending(self) -> None:
        service = FakeOwnerService()
        result = preflight_cross_cycle_endgame_action_cell(
            service,
            source_checkpoint_restore=source_restore(),
            completion_executor=completion,
            subject_session_factory=subject_session,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["readiness"], "static-ready-live-pending")
        self.assertFalse(result["action_executed"])
        self.assertFalse(result["live_proof_claimed"])
        self.assertEqual(service.selections, [])
        self.assertEqual(result["source"]["owner_character_id"], OWNER)
        self.assertEqual(result["source"]["subject_character_id"], SUBJECT)

    def test_green_requires_visible_result_and_subject_provider_business_state(self) -> None:
        service = FakeOwnerService()
        result = run_cross_cycle_endgame_action_cell(
            service,
            source_checkpoint_restore=source_restore(),
            completion_executor=completion,
            subject_session_factory=subject_session,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertTrue(result["result_event_visible"])
        self.assertTrue(result["provider_observed_postcondition"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertFalse(result["fixture_evidence_is_live"])
        self.assertEqual(
            result["result_event_context"]["event_definition_key"],
            "zg361we.361",
        )
        self.assertEqual(
            result["postcondition"]["carried_debt"],
            {
                "origin_cycle_serial": CYCLE,
                "carried_into_cycle_serial": CYCLE + 1,
                "open": True,
                "consumed": False,
            },
        )
        self.assertEqual(
            result["postcondition"]["default_change"]["charter_id"],
            36101,
        )
        self.assertEqual(service.selections, [(1, 3561, 10)])

    def test_ack_only_completion_is_rejected(self) -> None:
        service = FakeOwnerService()

        def ack_only(fake: FakeOwnerService, binding: object) -> dict[str, object]:
            value = completion(fake, binding)
            value["action_ack_only"] = True
            return value

        with self.assertRaises(CrossCycleEndgameCellError) as caught:
            run_cross_cycle_endgame_action_cell(
                service,
                source_checkpoint_restore=source_restore(),
                completion_executor=ack_only,
                subject_session_factory=subject_session,
            )
        self.assertEqual(caught.exception.reason_code, "completion_transition_not_green")

    def test_result_checkpoint_mismatch_is_rejected_before_query(self) -> None:
        service = FakeOwnerService()

        def wrong_checkpoint(result: object) -> EndgameSubjectProofSession:
            session = subject_session(result)
            receipt = dict(session.transition_receipt)
            receipt["restored_checkpoint_sha256"] = "C" * 64
            return EndgameSubjectProofSession(session.service, receipt)

        with self.assertRaises(CrossCycleEndgameCellError) as caught:
            run_cross_cycle_endgame_action_cell(
                service,
                source_checkpoint_restore=source_restore(),
                completion_executor=completion,
                subject_session_factory=wrong_checkpoint,
            )
        self.assertEqual(
            caught.exception.reason_code, "subject_proof_transition_not_green"
        )

    def test_wrong_owner_transition_is_typed_red(self) -> None:
        service = FakeOwnerService()

        def wrong_owner(result: object) -> EndgameSubjectProofSession:
            session = subject_session(result)
            receipt = dict(session.transition_receipt)
            receipt["from_player_character_id"] = OWNER + 99
            return EndgameSubjectProofSession(session.service, receipt)

        with self.assertRaises(CrossCycleEndgameCellError) as caught:
            run_cross_cycle_endgame_action_cell(
                service,
                source_checkpoint_restore=source_restore(),
                completion_executor=completion,
                subject_session_factory=wrong_owner,
            )
        self.assertEqual(
            caught.exception.reason_code, "subject_transition_owner_mismatch"
        )

    def test_generic_character_rebind_is_typed_red(self) -> None:
        service = FakeOwnerService()

        def generic_rebind(result: object) -> EndgameSubjectProofSession:
            session = subject_session(result)
            receipt = dict(session.transition_receipt)
            receipt["generic_character_rebind_used"] = True
            return EndgameSubjectProofSession(session.service, receipt)

        with self.assertRaises(CrossCycleEndgameCellError) as caught:
            run_cross_cycle_endgame_action_cell(
                service,
                source_checkpoint_restore=source_restore(),
                completion_executor=completion,
                subject_session_factory=generic_rebind,
            )
        self.assertEqual(
            caught.exception.reason_code, "generic_character_rebind_forbidden"
        )

    def test_wrong_next_cycle_debt_is_provider_red(self) -> None:
        service = FakeOwnerService()
        with self.assertRaises(CrossCycleEndgameCellError) as caught:
            run_cross_cycle_endgame_action_cell(
                service,
                source_checkpoint_restore=source_restore(),
                completion_executor=completion,
                subject_session_factory=lambda result: subject_session(
                    result, due_cycle=CYCLE + 2
                ),
            )
        self.assertEqual(
            caught.exception.reason_code,
            "endgame_business_postcondition_not_green",
        )
        self.assertIn("debt_due_next_cycle", caught.exception.evidence["failed_checks"])

    def test_preflight_rejects_missing_workforce_capability(self) -> None:
        with self.assertRaises(CrossCycleEndgamePreflightError) as caught:
            preflight_cross_cycle_endgame_action_cell(
                FakeOwnerService(advertise=False),
                source_checkpoint_restore=source_restore(),
                completion_executor=completion,
                subject_session_factory=subject_session,
            )
        self.assertEqual(caught.exception.reason_code, "required_capability_missing")
        self.assertFalse(caught.exception.evidence["action_executed"])

    def test_contract_records_runner_seam_acl_gap_and_live_boundaries(self) -> None:
        contract = json.loads(
            (TOOLS / "zg361_phase2_cross_cycle_endgame_action_contract.json").read_text(
                encoding="utf-8"
            )
        )
        provider_abi = json.loads(
            (
                BRIDGE_RESEARCH
                / "zhongguo_workforce_collective_snapshot_v1_abi.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(contract["readiness"], "static-ready-live-pending")
        self.assertTrue(
            contract["current_audit"]["formal_runner_integration_modified"]
        )
        self.assertEqual(
            provider_abi["subject_acl"]["scope"], "paused_played_character_only"
        )
        self.assertFalse(
            contract["service_contract"]["same_player_same_frame_join_supported"]
        )
        self.assertEqual(
            len(contract["current_audit"]["why_live_pending"]), 3
        )


if __name__ == "__main__":
    unittest.main()
