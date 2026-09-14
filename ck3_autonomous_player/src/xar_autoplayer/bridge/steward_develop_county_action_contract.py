"""Typed v1 contract for assigning the steward to Develop County.

The public request is intentionally small.  CK3-owned identities and legality
remain bound by the native same-frame observation; callers cannot inject a
province, an arbitrary task, or a script effect.  An ACK proves only command
submission.  A receipt is a distinct, later paused-frame observation.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
import re
from typing import Final


CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_CAPABILITY: Final = (
    "game.command.change-steward-develop-county-task-v1"
)
CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_TRANSPORT_CAPABILITY: Final = (
    "game.contract.change-steward-develop-county-task-v1-fail-closed"
)
CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_STEP: Final = (
    "change-steward-develop-county-task-v1"
)
STEWARD_DEVELOP_COUNTY_ACTION_V1_GAME_VERSION: Final = "1.19.0.6"
STEWARD_DEVELOP_COUNTY_ACTION_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
STEWARD_DEVELOP_COUNTY_ACTION_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-steward-develop-county-action-v1"
)
STEWARD_DEVELOP_COUNTY_ACTION_V1_CONTRACT_STAGE: Final = (
    "exact_build_action_seam_pending_command_abi_certification"
)
STEWARD_DEVELOP_COUNTY_ACTION_V1_TASK_KEY: Final = "task_develop_county"

_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_STABLE_KEY = re.compile(r"[a-z0-9_]+\Z")
_FAILURE_CLASSES: Final = {
    "none",
    "request_contract",
    "snapshot_binding",
    "councillor_binding",
    "task_or_target_legality",
    "native_command_dispatch",
}
_ACK_FIELDS: Final = {
    "schema_version",
    "contract_stage",
    "status",
    "verification_pending",
    "request_id",
    "pre_snapshot_revision",
    "pre_native_snapshot_revision",
    "councillor_character_id",
    "task_key",
    "target_county_title_id",
    "submitted_target_province_id",
    "replaced_existing_task",
    "failure_class",
    "rejection_reason",
    "native_reason_key",
    "exact_build",
}
_EXACT_BUILD_FIELDS: Final = {
    "game_version",
    "executable_sha256",
    "backend_id",
}
_RECEIPT_FIELDS: Final = {
    "schema_version",
    "status",
    "request_id",
    "reason",
    "post_snapshot_revision",
    "post_native_snapshot_revision",
    "post_observed_date_raw",
    "councillor_character_id",
    "active_task_key",
    "target_county_title_id",
    "target_province_id",
    "progress_kind",
    "progress_current_raw",
    "progress_max_raw",
    "progress_frozen",
    "postcondition_verified",
}


@dataclass(frozen=True, slots=True)
class ChangeStewardDevelopCountyRequestV1:
    request_id: str
    councillor_character_id: int
    task_key: str
    target_county_title_id: int
    expected_revision: int
    replace_existing_task: bool


def _integer(
    value: object,
    label: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{label} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _positive_int32(value: object, label: str) -> int:
    return _integer(value, label, minimum=1, maximum=2**31 - 1)


def _uint64(value: object, label: str, *, positive: bool = False) -> int:
    return _integer(
        value,
        label,
        minimum=1 if positive else 0,
        maximum=2**64 - 1,
    )


def _int32(value: object, label: str) -> int:
    return _integer(value, label, minimum=-(2**31), maximum=2**31 - 1)


def _int64(value: object, label: str) -> int:
    return _integer(value, label, minimum=-(2**63), maximum=2**63 - 1)


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be null or a non-empty string")
    return value


def build_change_steward_develop_county_request_v1(
    *,
    request_id: str,
    councillor_character_id: int,
    task_key: str,
    target_county_title_id: int,
    expected_revision: int,
    replace_existing_task: bool,
) -> ChangeStewardDevelopCountyRequestV1:
    """Build the fixed-task public request without exposing native location."""

    if not isinstance(request_id, str) or _REQUEST_ID.fullmatch(request_id) is None:
        raise ValueError("request_id is invalid")
    if task_key != STEWARD_DEVELOP_COUNTY_ACTION_V1_TASK_KEY:
        raise ValueError("task_key must be task_develop_county")
    return ChangeStewardDevelopCountyRequestV1(
        request_id=request_id,
        councillor_character_id=_positive_int32(
            councillor_character_id, "councillor_character_id"
        ),
        task_key=task_key,
        target_county_title_id=_positive_int32(
            target_county_title_id, "target_county_title_id"
        ),
        expected_revision=_uint64(
            expected_revision, "expected_revision", positive=True
        ),
        replace_existing_task=_bool(
            replace_existing_task, "replace_existing_task"
        ),
    )


def _normalize_exact_build(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != _EXACT_BUILD_FIELDS:
        raise ValueError("exact_build must contain exactly the v1 fields")
    expected = {
        "game_version": STEWARD_DEVELOP_COUNTY_ACTION_V1_GAME_VERSION,
        "executable_sha256": (
            STEWARD_DEVELOP_COUNTY_ACTION_V1_EXECUTABLE_SHA256
        ),
        "backend_id": STEWARD_DEVELOP_COUNTY_ACTION_V1_BACKEND_ID,
    }
    if value != expected:
        raise ValueError("exact_build does not match the frozen build")
    return expected


def normalize_change_steward_develop_county_ack_v1(
    value: object,
    *,
    expected_request: ChangeStewardDevelopCountyRequestV1,
) -> dict[str, object]:
    """Validate an ACK without treating submission as a game-state change."""

    if not isinstance(expected_request, ChangeStewardDevelopCountyRequestV1):
        raise TypeError("expected_request must be a typed v1 request")
    if not isinstance(value, dict) or set(value) != _ACK_FIELDS:
        raise ValueError("steward develop-county ACK has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("contract_stage")
        != STEWARD_DEVELOP_COUNTY_ACTION_V1_CONTRACT_STAGE
        or value.get("request_id") != expected_request.request_id
        or value.get("councillor_character_id")
        != expected_request.councillor_character_id
        or value.get("task_key") != expected_request.task_key
        or value.get("target_county_title_id")
        != expected_request.target_county_title_id
    ):
        raise ValueError("steward develop-county ACK binding disagrees")
    exact_build = _normalize_exact_build(value.get("exact_build"))
    pending = _bool(value.get("verification_pending"), "verification_pending")
    replaced = _bool(
        value.get("replaced_existing_task"), "replaced_existing_task"
    )
    failure_class = value.get("failure_class")
    if failure_class not in _FAILURE_CLASSES:
        raise ValueError("failure_class is invalid")
    rejection_reason = _optional_string(
        value.get("rejection_reason"), "rejection_reason"
    )
    native_reason_key = _optional_string(
        value.get("native_reason_key"), "native_reason_key"
    )
    status = value.get("status")
    pre_revision = _uint64(
        value.get("pre_snapshot_revision"), "pre_snapshot_revision"
    )
    pre_native_revision = _uint64(
        value.get("pre_native_snapshot_revision"),
        "pre_native_snapshot_revision",
    )
    submitted_province = _int32(
        value.get("submitted_target_province_id"),
        "submitted_target_province_id",
    )
    if status == "submitted_verification_pending":
        if (
            pending is not True
            or failure_class != "none"
            or rejection_reason is not None
            or native_reason_key is not None
            or pre_revision != expected_request.expected_revision
            or pre_native_revision <= 0
            or submitted_province <= 0
        ):
            raise ValueError("submitted ACK is internally inconsistent")
    elif status == "rejected_before_submit":
        if (
            pending is not False
            or failure_class == "none"
            or rejection_reason is None
            or pre_revision != 0
            or pre_native_revision != 0
            or submitted_province != -1
            or replaced is not False
        ):
            raise ValueError("rejected ACK is internally inconsistent")
    else:
        raise ValueError("ACK status is invalid")
    return {
        **copy.deepcopy(value),
        "verification_pending": pending,
        "replaced_existing_task": replaced,
        "exact_build": exact_build,
    }


def normalize_change_steward_develop_county_receipt_v1(
    value: object,
    *,
    expected_ack: dict[str, object],
) -> dict[str, object]:
    """Validate one independent later-frame receipt against its ACK."""

    if not isinstance(expected_ack, dict):
        raise TypeError("expected_ack must be a normalized ACK")
    if not isinstance(value, dict) or set(value) != _RECEIPT_FIELDS:
        raise ValueError("steward develop-county receipt has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("request_id") != expected_ack.get("request_id")
    ):
        raise ValueError("receipt request binding disagrees")
    status = value.get("status")
    verified = _bool(
        value.get("postcondition_verified"), "postcondition_verified"
    )
    reason = _optional_string(value.get("reason"), "reason")
    post_revision = _uint64(
        value.get("post_snapshot_revision"), "post_snapshot_revision"
    )
    post_native_revision = _uint64(
        value.get("post_native_snapshot_revision"),
        "post_native_snapshot_revision",
    )
    _int32(value.get("post_observed_date_raw"), "post_observed_date_raw")
    councillor = _int32(
        value.get("councillor_character_id"), "councillor_character_id"
    )
    active_task_key = value.get("active_task_key")
    if not isinstance(active_task_key, str):
        raise ValueError("active_task_key must be a string")
    target_title = value.get("target_county_title_id")
    target_province = value.get("target_province_id")
    progress_current = value.get("progress_current_raw")
    progress_max = value.get("progress_max_raw")
    progress_frozen = value.get("progress_frozen")
    progress_kind = value.get("progress_kind")
    if not isinstance(progress_kind, str):
        raise ValueError("progress_kind must be a string")
    if target_title is not None:
        target_title = _positive_int32(target_title, "target_county_title_id")
    if target_province is not None:
        target_province = _positive_int32(target_province, "target_province_id")
    if progress_current is not None:
        progress_current = _int64(progress_current, "progress_current_raw")
    if progress_max is not None:
        progress_max = _int64(progress_max, "progress_max_raw")
    if progress_frozen is not None:
        progress_frozen = _bool(progress_frozen, "progress_frozen")

    ack_status = expected_ack.get("status")
    if status == "rejected":
        if (
            ack_status != "rejected_before_submit"
            or verified is not False
            or reason != expected_ack.get("rejection_reason")
            or post_revision != 0
            or post_native_revision != 0
            or councillor != -1
            or active_task_key
            or target_title is not None
            or target_province is not None
            or progress_kind
            or progress_current is not None
            or progress_max is not None
            or progress_frozen is not None
        ):
            raise ValueError("rejected receipt is internally inconsistent")
    elif status == "applied":
        if (
            ack_status != "submitted_verification_pending"
            or verified is not True
            or reason is not None
            or post_revision <= int(expected_ack["pre_snapshot_revision"])
            or post_native_revision
            <= int(expected_ack["pre_native_snapshot_revision"])
            or councillor != expected_ack.get("councillor_character_id")
            or active_task_key != STEWARD_DEVELOP_COUNTY_ACTION_V1_TASK_KEY
            or target_title != expected_ack.get("target_county_title_id")
            or target_province
            != expected_ack.get("submitted_target_province_id")
            or progress_kind != "value"
            or progress_current is None
            or progress_max is None
            or progress_frozen is None
        ):
            raise ValueError("applied receipt is internally inconsistent")
    elif status == "postcondition_failed":
        if (
            ack_status != "submitted_verification_pending"
            or verified is not False
            or reason is None
        ):
            raise ValueError(
                "postcondition-failed receipt is internally inconsistent"
            )
    else:
        raise ValueError("receipt status is invalid")
    return copy.deepcopy(value)


__all__ = [
    "CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_CAPABILITY",
    "CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_STEP",
    "CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_TRANSPORT_CAPABILITY",
    "STEWARD_DEVELOP_COUNTY_ACTION_V1_BACKEND_ID",
    "STEWARD_DEVELOP_COUNTY_ACTION_V1_CONTRACT_STAGE",
    "STEWARD_DEVELOP_COUNTY_ACTION_V1_EXECUTABLE_SHA256",
    "STEWARD_DEVELOP_COUNTY_ACTION_V1_GAME_VERSION",
    "STEWARD_DEVELOP_COUNTY_ACTION_V1_TASK_KEY",
    "ChangeStewardDevelopCountyRequestV1",
    "build_change_steward_develop_county_request_v1",
    "normalize_change_steward_develop_county_ack_v1",
    "normalize_change_steward_develop_county_receipt_v1",
]
