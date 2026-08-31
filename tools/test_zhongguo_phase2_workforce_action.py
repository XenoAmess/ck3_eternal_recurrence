#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest


from zhongguo_phase2_workforce_action import (
    M360ActionBinding,
    WorkforceActionCellBlocked,
    WorkforceActionCellError,
    prove_m360_postcondition,
    run_m360_action_and_postcondition,
    submit_m360_route_action,
)


OWNER = 200
SUBJECT = 100
CYCLE = 40
CASE = 36040


def available(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def unavailable(reason: str) -> dict[str, object]:
    return {"status": "unavailable", "value": None, "unavailable_reason": reason}


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


def event_context(key: str, *, owner: int = OWNER, subject: int = SUBJECT) -> dict[str, object]:
    return {
        "event_definition_key": key,
        "root_scope": character_scope(owner),
        "saved_scopes": [
            {"name": "zg361_we_al_owner", "name_identifier": 1, "scope": character_scope(owner)},
            {"name": "zg361_we_al_subject", "name_identifier": 2, "scope": character_scope(subject)},
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "resolved_name": f"localized route {index + 1}",
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


def identity_group(owner: int, subject: int, cycle: int, case: int, state: int) -> dict[str, object]:
    return {
        "owner_character_id": available(owner),
        "subject_character_id": available(subject),
        "cycle_serial": available(cycle),
        "case_serial": available(case),
        "state": available(state),
    }


def cohort(index: int, route: str) -> dict[str, object]:
    quota = (1, 2, 1)[index]
    forced, exception, cost, approved = (
        (0, quota, quota, True) if route == "A" else (quota, 0, 0, False)
    )
    return {
        "cohort_id": available(10 + index),
        "manager_character_id": available(300 + index),
        "member_count": available((8, 9, 7)[index]),
        "quota": available(quota),
        "forced_count": available(forced),
        "exception_count": available(exception),
        "manager_cost": available(cost),
        "partition_verified": available(True),
        "approval_verified": available(approved),
    }


def history_slot(index: int) -> dict[str, object]:
    base = 1000 + index * 20
    return {
        "owner_character_id": available(OWNER),
        "subject_character_id": available(SUBJECT),
        "cycle_serial": available(CYCLE - 2 + index),
        "case_serial": available(CASE - 2 + index),
        "m357_receipt_id": available(base + 1),
        "m357_receipt_hash": available(base + 2),
        "m358_receipt_id": available(base + 3),
        "m358_receipt_hash": available(base + 4),
        "m359_receipt_id": available(base + 5),
        "m359_receipt_hash": available(base + 6),
    }


def workforce_response(route: str) -> dict[str, object]:
    route_number = {"A": 1, "B": 2, "C": 3}[route]
    receipt = {
        **identity_group(OWNER, SUBJECT, CYCLE, CASE, 4),
        "choice": available(route_number),
    }
    if route in {"A", "B"}:
        cohorts = [cohort(index, route) for index in range(3)]
        totals = {
            key: sum(int(row[key]["value"]) for row in cohorts)
            for key in (
                "member_count",
                "quota",
                "forced_count",
                "exception_count",
                "manager_cost",
            )
        }
        collective = {
            "phase": "route_a_exception" if route == "A" else "route_b_forced",
            **identity_group(OWNER, SUBJECT, CYCLE, CASE, 4),
            "submission_active": available(False),
            "submission_sealed": available(True),
            "submission_consumed": available(True),
            "settled": available(True),
            "route": available(route_number),
            "cohort_count": available(3),
            "total_members": available(totals["member_count"]),
            "total_quota": available(totals["quota"]),
            "forced_count": available(totals["forced_count"]),
            "exception_count": available(totals["exception_count"]),
            "manager_cost_total": available(totals["manager_cost"]),
        }
        debt = {}
    else:
        collective_keys = (
            "submission_active", "submission_sealed", "submission_consumed",
            "owner_character_id", "subject_character_id", "cycle_serial",
            "case_serial", "state", "collective_case_serial",
            "submitted_cycle_serial", "cohort_count", "settlement_id",
            "settlement_hash", "settled", "route", "total_members",
            "total_quota", "forced_count", "exception_count",
            "manager_cost_total",
        )
        collective = {
            "phase": "route_c_debt",
            **{key: unavailable("not_applicable") for key in collective_keys},
        }
        cohorts = [
            {"cohort_id": unavailable("not_applicable")}
            for _ in range(3)
        ]
        debt = {
            **identity_group(OWNER, SUBJECT, CYCLE, CASE, 4),
            "open": available(True),
            "consumed": available(False),
            "due_cycle_serial": available(CYCLE + 1),
        }
    charter = {
        "status": "ready",
        **identity_group(OWNER, SUBJECT, CYCLE, CASE, 5),
        "evidence_count": available(3),
        "evidence_ready": available(True),
        "evidence_consumed": available(False),
        "prepared_report_id": available(91),
        "prepared_charter_id": available(92),
        "adopted_cycle_serial": available(CYCLE),
        "effective_cycle_serial": available(CYCLE + 1),
    }
    return {
        "schema_version": 1,
        "status": "available",
        "case_kind": "zhongguo.workforce-collective",
        "player_character_id": SUBJECT,
        "subject_character_id": SUBJECT,
        "requested_owner_character_id": OWNER,
        "al_case": {
            **identity_group(OWNER, SUBJECT, CYCLE, CASE, 5),
            "active": available(True),
            "revision": available(8),
        },
        "m360_receipt": receipt,
        "collective": collective,
        "cohorts": cohorts,
        "route_c_debt": debt,
        "history": {
            "status": "three_cycle",
            "count": available(3),
            "effective_count": 3,
            "slots": [history_slot(index) for index in range(3)],
        },
        "charter_gate": charter,
        "readiness": {
            "m360_receipt_projection_ready": True,
            "collective_lifecycle_ready": True,
            "cohort_conservation_ready": True,
            "route_conservation_ready": True,
            "history_ledger_ready": True,
            "history_order_ready": True,
            "three_cycle_ready": True,
            "charter_gate_lifecycle_ready": True,
            "same_frame_ready": True,
            "ready": True,
        },
    }


class FakeOwnerService:
    def __init__(self) -> None:
        self.event_key = "zg361we.360"
        self.event_id = 3601
        self.revision = 10
        self.selected: list[tuple[int, int, int]] = []

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "owner",
            "revision": self.revision,
            "native_revision": self.revision + 100,
            "date_raw": 9000,
            "paused": True,
            "map_ready": True,
            "speed": 1,
            "played_character": {"character_id": OWNER},
            "active_event": {
                "instance_id": self.event_id,
                "option_count": 3,
                "options": [
                    {"option_number": number, "enabled": True}
                    for number in (1, 2, 3)
                ],
            },
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_instance_id != self.event_id or expected_revision != self.revision:
            raise AssertionError("event query binding changed")
        return {
            "status": "available",
            "current_event_window_context": event_context(self.event_key),
        }

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        self.selected.append((option_number, int(event_instance_id), int(expected_revision)))
        self.event_key = "zg361we.361"
        self.event_id += 1
        self.revision += 1
        return {"accepted": True, "status": "submitted", "option_number": option_number}

    def query_zhongguo_workforce_collective_snapshot_v1(self, *args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("owner-side ACK must not call received-self provider")

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        raise AssertionError(f"owner-side action unexpectedly executed {step}")


class FakeSubjectService:
    def __init__(
        self,
        responses: list[dict[str, object]],
        *,
        player: int = SUBJECT,
        active_event: bool = False,
        advance_after_resume: bool = False,
    ) -> None:
        self.responses = responses
        self.player = player
        self.active = active_event
        self.advance_after_resume = advance_after_resume
        self.revision = 20
        self.date_raw = 9000
        self.paused = True
        self.speed = 1
        self.queries: list[tuple[str, int, int, bool]] = []
        self.steps: list[str] = []

    def snapshot(self) -> dict[str, object]:
        if not self.paused and self.advance_after_resume:
            self.date_raw += 1
            self.advance_after_resume = False
            self.revision += 1
        return {
            "snapshot_id": "subject",
            "revision": self.revision,
            "native_revision": self.revision + 100,
            "date_raw": self.date_raw,
            "paused": self.paused,
            "map_ready": True,
            "speed": self.speed,
            "played_character": {"character_id": self.player},
            "active_event": (
                {"instance_id": 777, "option_count": 1, "options": [{"option_number": 1, "enabled": True}]}
                if self.active
                else None
            ),
        }

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.queries.append((request_nonce, expected_revision, owner_character_id, self.paused))
        index = min(len(self.queries) - 1, len(self.responses) - 1)
        return copy.deepcopy(self.responses[index])

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict[str, object]:
        self.steps.append(step)
        if expected_revision != self.revision:
            raise AssertionError("timeline revision binding changed")
        self.revision += 1
        if step == "set-speed-1":
            self.speed = 1
        elif step == "resume-map":
            self.paused = False
            self.advance_after_resume = True
        elif step == "pause-map":
            self.paused = True
        else:
            raise AssertionError(f"unexpected step {step}")
        return {"accepted": True, "status": "submitted", "step": step}

    def query_current_event_window_context_v1(self, *args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("subject proof must not inspect/select unrelated events")

    def select_event_option(self, *args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("subject proof must not select an event option")


class WorkforcePhase2ActionTests(unittest.TestCase):
    def test_owner_side_submits_all_three_native_routes_without_claiming_receipt(self) -> None:
        for route, expected_option in (("A", 1), ("B", 2), ("C", 3)):
            with self.subTest(route=route):
                service = FakeOwnerService()
                result = submit_m360_route_action(
                    service, route=route, settle_polls=0, poll_interval_s=0
                )
                self.assertEqual(result["result"], "ACKED")
                self.assertFalse(result["business_receipt_claimed"])
                self.assertEqual(service.selected, [(expected_option, 3601, 10)])
                self.assertTrue(result["post_ack_event"]["observed"])

    def test_subject_side_proves_route_receipt_collective_history_and_charter(self) -> None:
        for route in ("A", "B", "C"):
            with self.subTest(route=route):
                service = FakeSubjectService([workforce_response(route)])
                result = prove_m360_postcondition(
                    service,
                    route=route,
                    owner_character_id=OWNER,
                    subject_character_id=SUBJECT,
                    settle_polls=0,
                    poll_interval_s=0,
                )
                self.assertEqual(result["result"], "GREEN")
                self.assertFalse(result["action_ack_used_as_receipt"])
                self.assertEqual(result["postcondition"]["history_cycles"], [38, 39, 40])
                self.assertEqual(result["postcondition"]["charter_status"], "ready")
                self.assertTrue(all(query[3] for query in service.queries))

    def test_join_requires_explicit_owner_to_subject_rebind(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary)
            with self.assertRaisesRegex(
                WorkforceActionCellBlocked, "owner-to-subject player rebind"
            ):
                run_m360_action_and_postcondition(
                    FakeOwnerService(),
                    route="A",
                    subject_service_factory=None,
                    evidence_directory=evidence,
                )
            gate = json.loads(
                (evidence / "workforce_m360_route_a_gate.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                gate["identity_transition"]["reason"],
                "received_self_provider_requires_subject_player_rebind",
            )
            self.assertEqual(gate["result"], "RED")

    def test_join_succeeds_only_after_runner_supplies_exact_subject_session(self) -> None:
        bindings: list[M360ActionBinding] = []

        def subject_factory(binding: M360ActionBinding) -> FakeSubjectService:
            bindings.append(binding)
            return FakeSubjectService([workforce_response("B")])

        with tempfile.TemporaryDirectory() as temporary:
            result = run_m360_action_and_postcondition(
                FakeOwnerService(),
                route="B",
                subject_service_factory=subject_factory,
                evidence_directory=Path(temporary),
            )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(bindings[0].owner_character_id, OWNER)
        self.assertEqual(bindings[0].subject_character_id, SUBJECT)

    def test_option_ack_cannot_mask_a_wrong_business_receipt(self) -> None:
        wrong = workforce_response("B")
        service = FakeSubjectService([wrong])
        with self.assertRaisesRegex(
            WorkforceActionCellError, "receipt choice disagrees"
        ):
            prove_m360_postcondition(
                service,
                route="A",
                owner_character_id=OWNER,
                subject_character_id=SUBJECT,
                settle_polls=0,
                poll_interval_s=0,
            )

    def test_received_self_provider_rejects_owner_bound_postcondition(self) -> None:
        service = FakeSubjectService([workforce_response("A")], player=OWNER)
        with self.assertRaisesRegex(
            WorkforceActionCellBlocked, "must run while subject"
        ):
            prove_m360_postcondition(
                service,
                route="A",
                owner_character_id=OWNER,
                subject_character_id=SUBJECT,
                settle_polls=0,
                poll_interval_s=0,
            )
        self.assertEqual(service.queries, [])

    def test_bounded_maturation_requeries_only_after_pausing(self) -> None:
        not_reached = {"status": "unavailable", "case_kind": "zhongguo.workforce-collective"}
        service = FakeSubjectService(
            [not_reached, workforce_response("C")],
            advance_after_resume=True,
        )
        result = prove_m360_postcondition(
            service,
            route="C",
            owner_character_id=OWNER,
            subject_character_id=SUBJECT,
            settle_polls=0,
            max_timeline_steps=1,
            timeline_timeout_s=1,
            poll_interval_s=0,
        )
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(service.steps, ["resume-map", "pause-map"])
        self.assertTrue(all(query[3] for query in service.queries))
        self.assertEqual(len(result["timeline_steps"]), 1)

    def test_bounded_maturation_never_clicks_an_unrelated_event(self) -> None:
        service = FakeSubjectService(
            [{"status": "unavailable"}], active_event=True
        )
        with self.assertRaisesRegex(
            WorkforceActionCellBlocked, "blocked by an active event"
        ):
            prove_m360_postcondition(
                service,
                route="C",
                owner_character_id=OWNER,
                subject_character_id=SUBJECT,
                settle_polls=0,
                max_timeline_steps=1,
                timeline_timeout_s=1,
                poll_interval_s=0,
            )
        self.assertEqual(service.steps, [])


if __name__ == "__main__":
    unittest.main()
