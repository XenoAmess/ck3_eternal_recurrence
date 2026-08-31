#!/usr/bin/env python3
"""Unit tests for the MCP-first ZhongGuo B2 PIP action cell."""

from __future__ import annotations

import copy
import unittest

from zg361_phase2_b2_action_cell import (
    B2PipActionCellError,
    run_b2_pip_gameplay_action_cell,
)


PLAYER = 100
OWNER = 200
CYCLE = 7
CASE = 903
DATE_RAW = 730_121
EVENT_INSTANCE = 4_002


def _available(value: object) -> dict[str, object]:
    return {
        "status": "available",
        "value": value,
        "unavailable_reason": None,
    }


def _unavailable(reason: str = "variable_absent") -> dict[str, object]:
    return {
        "status": "unavailable",
        "value": None,
        "unavailable_reason": reason,
    }


def _character_scope(character_id: int) -> dict[str, object]:
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


def _scalar_scope() -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 9,
        "type_key": "value",
        "subtype": 0,
        "typed_identity": {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        },
    }


class _FakeClock:
    def __init__(self) -> None:
        self.now = 10.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class _FakeService:
    option_names = (
        "Accept the plan and its support.",
        "Revise the goal once, then begin.",
        "Refuse, and let only the next cycle judge it.",
    )

    def __init__(self) -> None:
        self.selected = False
        self.selected_option: int | None = None
        self.ack_accepted = True
        self.apply_effect = True
        self.keep_event_after_ack = False
        self.post_unavailable = False
        self.event_definition = "zg361b2.40"
        self.owner_scope_id = OWNER
        self.subject_scope_id = PLAYER
        self.root_scope_id = PLAYER
        self.option_names_override: tuple[str, str, str] | None = None
        self.pip_owner = OWNER
        self.pip_subject = PLAYER
        self.pip_cycle = CYCLE
        self.pip_case = CASE
        self.post_case = CASE
        self.calls: list[tuple[object, ...]] = []

    def _state(self) -> str:
        if not self.selected or not self.apply_effect:
            return "pending"
        return {1: "accept", 2: "negotiate", 3: "refuse"}[
            int(self.selected_option)
        ]

    def snapshot(self) -> dict[str, object]:
        state = self._state()
        changed = self.selected
        active_event: dict[str, object] | None = {
            "instance_id": EVENT_INSTANCE,
            "option_count": 3,
        }
        if changed and not self.keep_event_after_ack:
            active_event = None
        result = {
            "snapshot_id": f"fake:b2:{'post' if changed else 'pre'}",
            "revision": 11 if changed else 10,
            "native_revision": 101 if changed else 100,
            "date_raw": DATE_RAW,
            "paused": True,
            "played_character": {"character_id": PLAYER},
            "diagnostics": {"connection_generation": 8},
            "active_event": active_event,
            "state": state,
        }
        self.calls.append(("snapshot", state))
        return result

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        self.calls.append(("event_context", event_instance_id, expected_revision))
        snapshot = self.snapshot()
        names = self.option_names_override or self.option_names
        saved = [
            {
                "name": "zg361_b2_pip_prompt_owner",
                "scope": _character_scope(self.owner_scope_id),
            },
            {
                "name": "zg361_b2_pip_prompt_subject",
                "scope": _character_scope(self.subject_scope_id),
            },
        ]
        saved.extend(
            {"name": name, "scope": _scalar_scope()}
            for name in (
                "zg361_b2_pip_prompt_cycle",
                "zg361_b2_pip_prompt_case",
                "zg361_b2_pip_prompt_state",
            )
        )
        options = [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "resolved_name": name,
            }
            for index, name in enumerate(names)
        ]
        return {
            "status": "available",
            "current_event_window_context": {
                "status": "available",
                "event_definition_key": self.event_definition,
                "current_event_instance_id": EVENT_INSTANCE,
                "snapshot_revision": snapshot["native_revision"],
                "date_raw": DATE_RAW,
                "root_scope": _character_scope(self.root_scope_id),
                "saved_scopes": saved,
                "options": options,
                "readiness": {
                    "event_definition_identity_ready": True,
                    "root_scope_ready": True,
                    "saved_scopes_ready": True,
                    "option_presentation_ready": True,
                },
            },
        }

    def _b2_response(self, nonce: str) -> dict[str, object]:
        snapshot = self.snapshot()
        state = self._state()
        if self.post_unavailable and self.selected:
            return {
                "status": "unavailable",
                "case_kind": "zhongguo.b2.pip",
                "unavailable_reason": "case_not_found",
                "request_nonce": nonce,
            }
        response_code = {
            "pending": 0,
            "accept": 1,
            "negotiate": 2,
            "refuse": 3,
        }[state]
        state_code = {
            "pending": 1,
            "accept": 2,
            "negotiate": 2,
            "refuse": 5,
        }[state]
        goal_revision = state == "negotiate"
        current_case = self.post_case if self.selected else self.pip_case
        response_author = (
            _unavailable() if state == "pending" else _available(PLAYER)
        )
        response_case = 0 if state == "pending" else current_case
        refusal_receipt = current_case if state == "refuse" else 0
        return {
            "schema_version": 1,
            "status": "available",
            "case_kind": "zhongguo.b2.pip",
            "request_nonce": nonce,
            "snapshot_revision": snapshot["native_revision"],
            "date_raw": DATE_RAW,
            "paused": True,
            "player_character_id": PLAYER,
            "subject_character_id": PLAYER,
            "requested_owner_character_id": OWNER,
            "gate": {
                "owner_character_id": _available(self.pip_owner),
                "subject_character_id": _available(self.pip_subject),
                "cycle_serial": _available(self.pip_cycle),
                "case_serial": _available(current_case),
                "status": _available(1),
            },
            "pip": {
                "owner_character_id": _available(self.pip_owner),
                "subject_character_id": _available(self.pip_subject),
                "cycle_serial": _available(self.pip_cycle),
                "case_serial": _available(current_case),
                "state": _available(state_code),
            },
            "response": {
                "subject_response": _available(response_code),
                "response_case_serial": _available(response_case),
                "response_author_character_id": response_author,
                "acknowledgement_receipt_serial": _available(current_case),
                "goal_revision_used": _available(goal_revision),
                "refusal_receipt_serial": _available(refusal_receipt),
            },
            "readiness": {
                "player_subject_binding_ready": True,
                "owner_binding_ready": True,
                "gate_ready": True,
                "pip_identity_ready": True,
                "response_ready": True,
                "same_frame_ready": True,
                "ready": True,
            },
            "unavailable_reason": None,
            "binding": {
                "snapshot_id": snapshot["snapshot_id"],
                "revision": snapshot["revision"],
                "native_revision": snapshot["native_revision"],
                "connection_generation": 8,
                "date_raw": DATE_RAW,
                "paused": True,
                "player_character_id": PLAYER,
                "subject_character_id": PLAYER,
                "owner_character_id": OWNER,
                "expected_revision": snapshot["revision"],
            },
        }

    def query_zhongguo_b2_pip_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.calls.append(
            ("b2_query", request_nonce, expected_revision, owner_character_id)
        )
        return copy.deepcopy(self._b2_response(request_nonce))

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self.calls.append(
            ("select", option_number, event_instance_id, expected_revision)
        )
        if self.ack_accepted:
            self.selected = True
            self.selected_option = option_number
        return {
            "step": f"select-event-option-{option_number}",
            "accepted": self.ack_accepted,
            "status": "submitted" if self.ack_accepted else "rejected",
            "event_instance_id": event_instance_id,
            "option_number": option_number,
            "option_index": option_number - 1,
        }


class B2PipActionCellTests(unittest.TestCase):
    def _run(
        self, service: _FakeService, action: str = "accept"
    ) -> dict[str, object]:
        clock = _FakeClock()
        return run_b2_pip_gameplay_action_cell(
            service,
            owner_character_id=OWNER,
            action=action,
            timeout_s=0.2,
            poll_interval_s=0.05,
            clock=clock.monotonic,
            sleeper=clock.sleep,
        )

    def test_all_three_authored_responses_require_provider_postcondition(self) -> None:
        expected = {
            "accept": (1, 2, 1, False, 0),
            "negotiate": (2, 2, 2, True, 0),
            "refuse": (3, 5, 3, False, CASE),
        }
        for action, (
            option_number,
            state,
            response_code,
            goal_revision,
            refusal_receipt,
        ) in expected.items():
            with self.subTest(action=action):
                service = _FakeService()
                result = self._run(service, action)
                self.assertEqual(result["result"], "GREEN")
                self.assertTrue(result["mcp_only"])
                self.assertFalse(result["ocr_used"])
                self.assertFalse(result["ack_is_postcondition"])
                self.assertTrue(result["postcondition_query_green"])
                self.assertEqual(result["option_number"], option_number)
                before = result["precondition"]["identity"]
                after = result["postcondition"]["identity"]
                self.assertEqual(
                    tuple(before[key] for key in (
                        "owner_character_id",
                        "subject_character_id",
                        "cycle_serial",
                        "case_serial",
                    )),
                    tuple(after[key] for key in (
                        "owner_character_id",
                        "subject_character_id",
                        "cycle_serial",
                        "case_serial",
                    )),
                )
                self.assertEqual(before["state"], 1)
                self.assertEqual(after["state"], state)
                response = result["postcondition"]["response"]
                self.assertEqual(response["subject_response"]["value"], response_code)
                self.assertIs(
                    response["goal_revision_used"]["value"], goal_revision
                )
                self.assertEqual(
                    response["refusal_receipt_serial"]["value"],
                    refusal_receipt,
                )
                self.assertIn(
                    ("select", option_number, EVENT_INSTANCE, 10),
                    service.calls,
                )

    def test_simplified_chinese_option_semantics_are_supported(self) -> None:
        service = _FakeService()
        service.option_names_override = (
            "接受计划及配套支持。",
            "修改一次目标，然后开始执行。",
            "拒绝，并只让下一轮评价此事。",
        )
        self.assertEqual(self._run(service, "negotiate")["result"], "GREEN")

    def test_wrong_event_definition_fails_before_option_submission(self) -> None:
        service = _FakeService()
        service.event_definition = "zg361b2.50"
        with self.assertRaisesRegex(B2PipActionCellError, "wrong active event"):
            self._run(service)
        self.assertFalse(any(call[0] == "select" for call in service.calls))

    def test_option_text_drift_fails_before_option_submission(self) -> None:
        service = _FakeService()
        service.option_names_override = (
            "Do something else",
            service.option_names[1],
            service.option_names[2],
        )
        with self.assertRaisesRegex(B2PipActionCellError, "semantic text changed"):
            self._run(service)
        self.assertFalse(any(call[0] == "select" for call in service.calls))

    def test_event_owner_scope_mismatch_fails_closed(self) -> None:
        service = _FakeService()
        service.owner_scope_id = OWNER + 1
        with self.assertRaisesRegex(B2PipActionCellError, "owner scope differs"):
            self._run(service)
        self.assertFalse(any(call[0] == "select" for call in service.calls))

    def test_provider_identity_mismatch_fails_before_action(self) -> None:
        service = _FakeService()
        service.pip_subject = PLAYER + 1
        with self.assertRaisesRegex(B2PipActionCellError, "played character"):
            self._run(service)
        self.assertFalse(any(call[0] == "select" for call in service.calls))

    def test_rejected_ack_is_not_a_postcondition(self) -> None:
        service = _FakeService()
        service.ack_accepted = False
        with self.assertRaises(B2PipActionCellError) as caught:
            self._run(service)
        self.assertIn("ACK was not accepted", str(caught.exception))
        self.assertFalse(caught.exception.evidence["postcondition_query_green"])
        self.assertEqual(caught.exception.evidence["result"], "RED")

    def test_accepted_ack_without_state_change_times_out_red(self) -> None:
        service = _FakeService()
        service.apply_effect = False
        with self.assertRaises(B2PipActionCellError) as caught:
            self._run(service)
        self.assertIn("timed out", str(caught.exception))
        self.assertTrue(
            caught.exception.evidence["selection_submission"]["accepted"]
        )
        self.assertFalse(caught.exception.evidence["postcondition_query_green"])

    def test_old_event_that_never_clears_times_out_red(self) -> None:
        service = _FakeService()
        service.keep_event_after_ack = True
        with self.assertRaisesRegex(B2PipActionCellError, "timed out"):
            self._run(service)

    def test_unavailable_postcondition_case_fails_red(self) -> None:
        service = _FakeService()
        service.post_unavailable = True
        with self.assertRaisesRegex(B2PipActionCellError, "available PIP case"):
            self._run(service)

    def test_postcondition_cannot_switch_to_another_case(self) -> None:
        service = _FakeService()
        service.post_case = CASE + 1
        with self.assertRaisesRegex(B2PipActionCellError, "immutable case identity"):
            self._run(service)

    def test_bad_arguments_fail_without_touching_service(self) -> None:
        service = _FakeService()
        with self.assertRaises(ValueError):
            run_b2_pip_gameplay_action_cell(
                service, owner_character_id=OWNER, action="invented"
            )
        with self.assertRaises(ValueError):
            run_b2_pip_gameplay_action_cell(
                service,
                owner_character_id=OWNER,
                request_nonce_prefix="not a token",
            )
        self.assertEqual(service.calls, [])


if __name__ == "__main__":
    unittest.main()
