"""Strict Python projection of the Council22 steward action contract.

The native helper ACK only proves invocation.  A successful result requires
the independently captured, later paused-frame receipt produced by the native
runtime glue.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import copy
import re
from typing import Final

from .council_composition_candidates_contract import STEWARD_POSITION_KEY


ASSIGN_COUNCILLOR_V1_CAPABILITY: Final = "game.action.assign-councillor-v1"
ASSIGN_COUNCILLOR_V1_STEP: Final = "assign-councillor-v1"
QUERY_ASSIGN_COUNCILLOR_RECEIPT_V1_STEP: Final = (
    "query-assign-councillor-receipt-v1"
)
ASSIGN_COUNCILLOR_V1_RESULT_SCHEMA: Final = (
    "xar.ck3.assign-councillor-result/v1"
)

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_ACK_FIELDS: Final = {
    "status",
    "failure",
    "action_request_id",
    "pre_snapshot_id",
    "pre_public_revision",
    "pre_native_revision",
    "pre_date_raw",
    "owner_character_id",
    "position_key",
    "active_task_id",
    "candidate_character_id",
    "had_incumbent",
    "previous_incumbent_character_id",
    "route",
    "native_helper_invoked",
    "queue_acceptance_observed",
    "verification_pending",
    "native_reason_key",
}
_RECEIPT_FIELDS: Final = {
    "status",
    "rejected_action_failure",
    "action_request_id",
    "post_snapshot_id",
    "post_public_revision",
    "post_native_revision",
    "post_date_raw",
    "owner_character_id",
    "position_key",
    "incumbent_character_id",
    "incumbent_identity_round_trip",
    "postcondition_verified",
    "reason",
}
_FAILURES: Final = {
    "none",
    "request_contract_invalid",
    "exact_build_mismatch",
    "private_candidate_not_admitted",
    "application_main_thread_required",
    "callbacks_unavailable",
    "observation_unavailable",
    "not_paused",
    "snapshot_binding_mismatch",
    "position_outside_coverage",
    "active_task_identity_unavailable",
    "incumbent_identity_unavailable",
    "candidate_equals_incumbent",
    "final_legality_unavailable",
    "candidate_not_in_exact_collection",
    "candidate_identity_mismatch",
    "candidate_already_councillor",
    "candidate_is_guest",
    "pending_character_interaction",
    "incumbent_cannot_be_replaced",
    "state_changed_before_submit",
    "native_helper_not_invoked",
}
_POSTCONDITION_FAILURE_REASONS: Final = {
    "invalid_ack",
    "post_observation_unavailable",
    "no_new_paused_frame",
    "owner_or_position_changed",
    "active_task_changed",
    "candidate_not_observed_as_incumbent",
}


@dataclass(frozen=True, slots=True)
class AssignCouncillorRequestV1:
    request_id: str
    position_key: str
    expected_snapshot_id: str
    expected_public_revision: int
    expected_native_revision: int
    expected_date_raw: int
    expected_owner_character_id: int
    candidate_character_id: int
    expected_has_incumbent: bool
    expected_incumbent_character_id: int

    def as_wire_fields(self) -> dict[str, object]:
        return asdict(self)


def _integer(value: object, label: str, minimum: int, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{label} must be an integer in [{minimum}, {maximum}]")
    return value


def _positive_int32(value: object, label: str) -> int:
    return _integer(value, label, 1, 2**31 - 1)


def _uint64(value: object, label: str, *, positive: bool = False) -> int:
    return _integer(value, label, 1 if positive else 0, 2**64 - 1)


def _int32(value: object, label: str) -> int:
    return _integer(value, label, -(2**31), 2**31 - 1)


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _token(value: object, label: str, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    if not isinstance(value, str) or _TOKEN.fullmatch(value) is None:
        raise ValueError(f"{label} is invalid")
    return value


def build_assign_councillor_request_v1(
    observation: object,
    *,
    candidate_character_id: object,
    request_id: object,
) -> AssignCouncillorRequestV1:
    """Bind the selected native-legal row to its exact Council19 frame."""

    if not isinstance(observation, dict):
        raise ValueError("council observation must be an object")
    snapshot = observation.get("snapshot")
    position = observation.get("position")
    candidates = observation.get("candidates")
    readiness = observation.get("readiness")
    if not (
        isinstance(snapshot, dict)
        and snapshot.get("paused") is True
        and isinstance(position, dict)
        and position.get("position_key") == STEWARD_POSITION_KEY
        and isinstance(candidates, list)
        and observation.get("candidate_collection_complete") is True
        and isinstance(readiness, dict)
        and readiness.get("ready") is True
    ):
        raise ValueError("council observation is not a complete paused frame")
    candidate_id = _positive_int32(
        candidate_character_id, "candidate_character_id"
    )
    matches = [
        row
        for row in candidates
        if isinstance(row, dict) and row.get("character_id") == candidate_id
    ]
    expected_route = "assign" if position.get("vacant") is True else "replace"
    if (
        len(matches) != 1
        or matches[0].get("eligible") is not True
        or matches[0].get("action_route") != expected_route
        or position.get("action_route") != expected_route
    ):
        raise ValueError("candidate is not one exact native-legal action row")
    incumbent = position.get("incumbent_character_id")
    has_incumbent = position.get("vacant") is False
    expected_incumbent = (
        _positive_int32(incumbent, "incumbent_character_id")
        if has_incumbent
        else -1
    )
    if (not has_incumbent and incumbent is not None) or candidate_id == incumbent:
        raise ValueError("council incumbent binding is invalid")
    return AssignCouncillorRequestV1(
        request_id=_token(request_id, "request_id"),
        position_key=STEWARD_POSITION_KEY,
        expected_snapshot_id=_token(
            snapshot.get("snapshot_id"), "expected_snapshot_id"
        ),
        expected_public_revision=_uint64(
            snapshot.get("public_revision"),
            "expected_public_revision",
            positive=True,
        ),
        expected_native_revision=_uint64(
            snapshot.get("native_revision"),
            "expected_native_revision",
            positive=True,
        ),
        expected_date_raw=_int32(snapshot.get("date_raw"), "expected_date_raw"),
        expected_owner_character_id=_positive_int32(
            observation.get("owner_character_id"),
            "expected_owner_character_id",
        ),
        candidate_character_id=candidate_id,
        expected_has_incumbent=has_incumbent,
        expected_incumbent_character_id=expected_incumbent,
    )


def normalize_assign_councillor_ack_v1(
    value: object, *, expected_request: AssignCouncillorRequestV1
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _ACK_FIELDS:
        raise ValueError("assign-councillor ACK must contain exactly the v1 fields")
    failure = value.get("failure")
    if failure not in _FAILURES:
        raise ValueError("assign-councillor ACK failure is invalid")
    status = value.get("status")
    request_id = _token(
        value.get("action_request_id"), "ACK action_request_id"
    )
    if (
        request_id != expected_request.request_id
        or value.get("position_key") != expected_request.position_key
        or value.get("candidate_character_id")
        != expected_request.candidate_character_id
    ):
        raise ValueError("assign-councillor ACK request binding disagrees")
    helper = _bool(value.get("native_helper_invoked"), "native_helper_invoked")
    queue_observed = _bool(
        value.get("queue_acceptance_observed"), "queue_acceptance_observed"
    )
    pending = _bool(value.get("verification_pending"), "verification_pending")
    had_incumbent = _bool(value.get("had_incumbent"), "had_incumbent")
    previous = _int32(
        value.get("previous_incumbent_character_id"),
        "previous_incumbent_character_id",
    )
    native_reason = _token(
        value.get("native_reason_key"), "native_reason_key", allow_empty=True
    )
    if status == "native_helper_invoked_verification_pending":
        route = "replace_incumbent" if expected_request.expected_has_incumbent else "assign_vacant"
        if not (
            failure == "none"
            and value.get("pre_snapshot_id") == expected_request.expected_snapshot_id
            and value.get("pre_public_revision") == expected_request.expected_public_revision
            and value.get("pre_native_revision") == expected_request.expected_native_revision
            and value.get("pre_date_raw") == expected_request.expected_date_raw
            and value.get("owner_character_id") == expected_request.expected_owner_character_id
            and _positive_int32(value.get("active_task_id"), "active_task_id")
            and had_incumbent is expected_request.expected_has_incumbent
            and previous == expected_request.expected_incumbent_character_id
            and value.get("route") == route
            and helper is True
            and queue_observed is False
            and pending is True
            and native_reason == ""
        ):
            raise ValueError("verification-pending ACK is internally inconsistent")
    elif status == "rejected_before_submit":
        if not (
            failure != "none"
            and value.get("pre_snapshot_id") == ""
            and value.get("pre_public_revision") == 0
            and value.get("pre_native_revision") == 0
            and value.get("pre_date_raw") == 0
            and value.get("owner_character_id") == -1
            and value.get("active_task_id") == -1
            and had_incumbent is False
            and previous == -1
            and value.get("route") == "none"
            and helper is False
            and queue_observed is False
            and pending is False
        ):
            raise ValueError("rejected ACK is internally inconsistent")
    else:
        raise ValueError("assign-councillor ACK status is invalid")
    return copy.deepcopy(value)


def normalize_assign_councillor_receipt_v1(
    value: object, *, expected_ack: dict[str, object]
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _RECEIPT_FIELDS:
        raise ValueError(
            "assign-councillor receipt must contain exactly the v1 fields"
        )
    if value.get("action_request_id") != expected_ack.get(
        "action_request_id"
    ):
        raise ValueError("assign-councillor receipt request binding disagrees")
    status = value.get("status")
    failure = value.get("rejected_action_failure")
    if failure not in _FAILURES:
        raise ValueError("assign-councillor receipt failure is invalid")
    verified = _bool(
        value.get("postcondition_verified"), "postcondition_verified"
    )
    round_trip = _bool(
        value.get("incumbent_identity_round_trip"),
        "incumbent_identity_round_trip",
    )
    reason = _token(value.get("reason"), "receipt reason", allow_empty=True)
    if status == "applied":
        if not (
            expected_ack.get("status")
            == "native_helper_invoked_verification_pending"
            and failure == "none"
            and _token(value.get("post_snapshot_id"), "post_snapshot_id")
            != expected_ack.get("pre_snapshot_id")
            and _uint64(value.get("post_public_revision"), "post_public_revision", positive=True)
            > int(expected_ack["pre_public_revision"])
            and _uint64(value.get("post_native_revision"), "post_native_revision", positive=True)
            > int(expected_ack["pre_native_revision"])
            and _int32(value.get("post_date_raw"), "post_date_raw")
            >= int(expected_ack["pre_date_raw"])
            and value.get("owner_character_id") == expected_ack.get("owner_character_id")
            and value.get("position_key") == STEWARD_POSITION_KEY
            and value.get("incumbent_character_id") == expected_ack.get("candidate_character_id")
            and round_trip is True
            and verified is True
            and reason == ""
        ):
            raise ValueError("applied receipt is internally inconsistent")
    elif status == "postcondition_failed":
        if not (
            expected_ack.get("status")
            == "native_helper_invoked_verification_pending"
            and failure == "none"
            and verified is False
            and reason in _POSTCONDITION_FAILURE_REASONS
        ):
            raise ValueError("failed receipt is internally inconsistent")
    elif status == "rejected":
        if not (
            expected_ack.get("status") == "rejected_before_submit"
            and failure == expected_ack.get("failure")
            and verified is False
            and reason == "action_rejected"
        ):
            raise ValueError("rejected receipt is internally inconsistent")
    else:
        raise ValueError("assign-councillor receipt status is invalid")
    return copy.deepcopy(value)


__all__ = [
    "ASSIGN_COUNCILLOR_V1_CAPABILITY",
    "ASSIGN_COUNCILLOR_V1_RESULT_SCHEMA",
    "ASSIGN_COUNCILLOR_V1_STEP",
    "QUERY_ASSIGN_COUNCILLOR_RECEIPT_V1_STEP",
    "AssignCouncillorRequestV1",
    "build_assign_councillor_request_v1",
    "normalize_assign_councillor_ack_v1",
    "normalize_assign_councillor_receipt_v1",
]
