"""Typed contract for the allowlisted ZhongGuo B1 case snapshot query.

The wire intentionally exposes one semantic product profile.  Callers cannot
name CK3 variables or request arbitrary script values.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-case-snapshot-v1"
)
QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-case-snapshot-v1"
)
QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_CASE_SNAPSHOT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-case-snapshot-v1"
)
ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-case-snapshot-v1"
)
ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID: Final = "native-headless"
ZHONGGUO_CASE_SNAPSHOT_V1_ALLOWLIST_ID: Final = (
    "zg361-b1-performance-case-v1"
)
ZHONGGUO_B1_PERFORMANCE_CASE_KIND: Final = "zhongguo.b1.performance"
ZHONGGUO_CASE_KINDS_V1: Final = frozenset(
    {ZHONGGUO_B1_PERFORMANCE_CASE_KIND}
)

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_STABLE_KEY_RE: Final = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z"
)
_STEP_KIND_TOKEN: Final = {ZHONGGUO_B1_PERFORMANCE_CASE_KIND: "b1"}
_TOKEN_CASE_KIND: Final = {value: key for key, value in _STEP_KIND_TOKEN.items()}

_TYPED_FIELD_KEYS: Final = {"status", "value", "unavailable_reason"}
_CASE_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "active",
    "revision",
    "timeline_serial",
    "feedback_revision",
}
_POLICY_KEYS: Final = {"policy_id", "choice"}
_OPERATION_KEYS: Final = {
    "operation_id",
    "operation_key",
    "hook",
    "pre_state",
    "post_state",
}
_RECEIPT_KEYS: Final = {
    "status",
    "key",
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "choice",
}
_DEADLINE_KEYS: Final = {
    "status",
    "target_character_id",
    "owner_character_id",
    "cycle_serial",
    "case_serial",
    "expected_state",
    "days",
    "pending",
    "expired",
    "open_date_raw",
    "due_date_raw",
    "on_due_operation",
}
_READINESS_KEYS: Final = {
    "player_binding_ready",
    "case_identity_ready",
    "policy_ready",
    "operation_ready",
    "receipt_ready",
    "deadline_identity_ready",
    "deadline_due_date_ready",
    "same_frame_ready",
    "ready",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
    "executable_sha256": ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    "backend_id": ZHONGGUO_CASE_SNAPSHOT_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
    "variable_context_for_scope_rva": "0x3329A40",
    "variable_identifier_table_rva": "0x3B971A0",
    "variable_identifier_lookup_rva": "0x3B97020",
    "variable_identifier_name_rva": "0x3B97090",
    "character_storage_slot_rva": "0x570C130",
}
_PROVENANCE_KEYS: Final = set(_PROVENANCE_VALUES)
_FRAME_KEYS: Final = {
    "schema_version",
    "status",
    "case_kind",
    "request_nonce",
    "snapshot_revision",
    "date_raw",
    "paused",
    "player_character_id",
    "subject_character_id",
    "requested_owner_character_id",
    "case",
    "policy",
    "operation",
    "receipt",
    "deadline",
    "readiness",
    "unavailable_reason",
    "provenance",
}
_TOP_LEVEL_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "subject_not_found",
    "case_not_found",
    "player_binding_mismatch",
    "owner_filter_mismatch",
    "variable_identifier_unavailable",
    "variable_context_unavailable",
    "state_changed",
    "internal_error",
}
_FIELD_UNAVAILABLE_REASONS: Final = {
    "case_unavailable",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "no_operation_recorded",
    "unknown_allowlisted_operation",
    "receipt_not_recorded",
    "receipt_inconsistent",
    "deadline_not_scheduled",
    "deadline_inconsistent",
    "due_date_not_persisted_by_product",
    "not_applicable",
}
_FINAL_FRAME_KEYS: Final = _FRAME_KEYS | {"build", "source", "binding"}
_BUILD_KEYS: Final = {"version", "exe_sha256"}
_SOURCE_KEYS: Final = {
    "bridge_version",
    "game_adapter_id",
    "backend_id",
    "consumer_id",
    "connection_generation",
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "paused",
    "player_character_id",
}
_BINDING_KEYS: Final = {
    "request_nonce",
    "snapshot_id",
    "revision",
    "native_revision",
    "connection_generation",
    "date_raw",
    "paused",
    "player_character_id",
    "subject_character_id",
    "owner_character_id",
    "expected_revision",
}


@dataclass(frozen=True)
class ZhongguoCaseQueryV1:
    case_kind: str
    subject_character_id: int
    owner_character_id: int | None
    request_nonce: str


def validate_zhongguo_case_kind_v1(value: object) -> str:
    if not isinstance(value, str) or value not in ZHONGGUO_CASE_KINDS_V1:
        raise ValueError(
            "case_kind must be an allowlisted ZhongGuo v1 case kind"
        )
    return value


def validate_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError(
            "request_nonce must be 1-64 ASCII token characters"
        )
    return value


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive signed int32")
    return value


def _optional_positive_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _positive_int32(value, name)


def query_zhongguo_case_snapshot_v1_step(
    case_kind: object,
    subject_character_id: object,
    owner_character_id: object,
    request_nonce: object,
) -> str:
    kind = validate_zhongguo_case_kind_v1(case_kind)
    subject = _positive_int32(subject_character_id, "subject_character_id")
    owner = _optional_positive_int32(
        owner_character_id, "owner_character_id"
    )
    nonce = validate_request_nonce_v1(request_nonce)
    nonce_hex = nonce.encode("ascii").hex()
    return (
        f"{QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP_PREFIX}"
        f"{_STEP_KIND_TOKEN[kind]}-{subject}-{owner or 0}-{nonce_hex}"
    )


def parse_query_zhongguo_case_snapshot_v1_step(
    step: object,
) -> ZhongguoCaseQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    tail = step.removeprefix(QUERY_ZHONGGUO_CASE_SNAPSHOT_V1_STEP_PREFIX)
    parts = tail.split("-", 3)
    if len(parts) != 4 or parts[0] not in _TOKEN_CASE_KIND:
        return None
    try:
        subject = int(parts[1], 10)
        owner_raw = int(parts[2], 10)
        if str(subject) != parts[1] or str(owner_raw) != parts[2]:
            return None
        subject = _positive_int32(subject, "subject_character_id")
        owner = (
            None
            if owner_raw == 0
            else _positive_int32(owner_raw, "owner_character_id")
        )
        if not parts[3] or len(parts[3]) % 2 != 0:
            return None
        nonce = bytes.fromhex(parts[3]).decode("ascii")
        nonce = validate_request_nonce_v1(nonce)
        if nonce.encode("ascii").hex() != parts[3]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoCaseQueryV1(
        case_kind=_TOKEN_CASE_KIND[parts[0]],
        subject_character_id=subject,
        owner_character_id=owner,
        request_nonce=nonce,
    )


def _exact_object(
    value: object, fields: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _integer(
    value: object, name: str, *, minimum: int, maximum: int
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} must be an integer in range")
    return value


def _typed_field(
    value: object,
    name: str,
    *,
    value_kind: str,
) -> dict[str, object]:
    field = _exact_object(value, _TYPED_FIELD_KEYS, name)
    status = field.get("status")
    raw = field.get("value")
    reason = field.get("unavailable_reason")
    if status == "unavailable":
        if raw is not None or reason not in _FIELD_UNAVAILABLE_REASONS:
            raise ValueError(f"{name} has an invalid typed unavailable value")
        return dict(field)
    if status != "available" or reason is not None:
        raise ValueError(f"{name} has an invalid availability status")
    if value_kind == "int":
        _integer(raw, name, minimum=-(2**63), maximum=2**63 - 1)
    elif value_kind == "bool":
        if not isinstance(raw, bool):
            raise ValueError(f"{name}.value must be boolean")
    elif value_kind == "string":
        if not isinstance(raw, str) or _STABLE_KEY_RE.fullmatch(raw) is None:
            raise ValueError(f"{name}.value must be a bounded stable key")
    else:  # pragma: no cover - internal contract programmer error
        raise AssertionError(value_kind)
    return dict(field)


def _typed_group(
    value: object,
    fields: set[str],
    kinds: dict[str, str],
    name: str,
) -> dict[str, object]:
    group = _exact_object(value, fields, name)
    return {
        field: _typed_field(group[field], f"{name}.{field}", value_kind=kind)
        for field, kind in kinds.items()
    }


def _typed_available(field: dict[str, object]) -> bool:
    return field["status"] == "available"


def _typed_value(field: dict[str, object], name: str) -> object:
    if not _typed_available(field):
        raise ValueError(f"{name} must be available")
    return field["value"]


def _all_typed_available(
    group: dict[str, object], fields: set[str] | tuple[str, ...]
) -> bool:
    return all(
        isinstance(group[field], dict) and _typed_available(group[field])
        for field in fields
    )


def _all_typed_unavailable(
    group: dict[str, object], fields: set[str] | tuple[str, ...]
) -> bool:
    return all(
        isinstance(group[field], dict) and not _typed_available(group[field])
        for field in fields
    )


def _bounded_text(value: object, name: str, *, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(f"{name} must be valid UTF-8") from error
    if len(encoded) > maximum_bytes or any(
        ord(character) < 0x20 for character in value
    ):
        raise ValueError(f"{name} must be bounded text without controls")
    return value


def normalize_native_zhongguo_case_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoCaseQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Validate the native semantic frame without inventing absent values."""

    expected_query = ZhongguoCaseQueryV1(
        case_kind=validate_zhongguo_case_kind_v1(expected_query.case_kind),
        subject_character_id=_positive_int32(
            expected_query.subject_character_id,
            "expected_query.subject_character_id",
        ),
        owner_character_id=_optional_positive_int32(
            expected_query.owner_character_id,
            "expected_query.owner_character_id",
        ),
        request_nonce=validate_request_nonce_v1(expected_query.request_nonce),
    )
    expected_snapshot_revision = _integer(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    expected_date_raw = _integer(
        expected_date_raw,
        "expected_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_player_character_id = _positive_int32(
        expected_player_character_id,
        "expected_player_character_id",
    )

    frame = _exact_object(value, _FRAME_KEYS, "zhongguo_case_snapshot")
    if frame.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if frame.get("case_kind") != expected_query.case_kind:
        raise ValueError("case_kind binding changed")
    if frame.get("request_nonce") != expected_query.request_nonce:
        raise ValueError("request_nonce binding changed")
    revision = _integer(
        frame.get("snapshot_revision"),
        "snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    if revision != expected_snapshot_revision:
        raise ValueError("snapshot revision binding changed")
    date_raw = _integer(
        frame.get("date_raw"),
        "date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    if date_raw != expected_date_raw:
        raise ValueError("date binding changed")
    if frame.get("paused") is not True:
        raise ValueError("native ZhongGuo query is not paused")
    player = _positive_int32(
        frame.get("player_character_id"), "player_character_id"
    )
    if player != expected_player_character_id:
        raise ValueError("player identity binding changed")
    subject = _positive_int32(
        frame.get("subject_character_id"), "subject_character_id"
    )
    if subject != expected_query.subject_character_id:
        raise ValueError("subject identity binding changed")
    requested_owner = _optional_positive_int32(
        frame.get("requested_owner_character_id"),
        "requested_owner_character_id",
    )
    if requested_owner != expected_query.owner_character_id:
        raise ValueError("owner filter binding changed")

    case = _typed_group(
        frame.get("case"),
        _CASE_KEYS,
        {
            "owner_character_id": "int",
            "subject_character_id": "int",
            "cycle_serial": "int",
            "case_serial": "int",
            "state": "int",
            "active": "bool",
            "revision": "int",
            "timeline_serial": "int",
            "feedback_revision": "int",
        },
        "case",
    )
    policy = _typed_group(
        frame.get("policy"),
        _POLICY_KEYS,
        {"policy_id": "string", "choice": "int"},
        "policy",
    )
    operation = _typed_group(
        frame.get("operation"),
        _OPERATION_KEYS,
        {
            "operation_id": "int",
            "operation_key": "string",
            "hook": "string",
            "pre_state": "int",
            "post_state": "int",
        },
        "operation",
    )
    receipt_raw = _exact_object(frame.get("receipt"), _RECEIPT_KEYS, "receipt")
    if receipt_raw.get("status") not in {
        "recorded",
        "not_recorded",
        "unavailable",
    }:
        raise ValueError("receipt.status is invalid")
    receipt = {
        "status": receipt_raw["status"],
        **{
            field: _typed_field(
                receipt_raw[field],
                f"receipt.{field}",
                value_kind=kind,
            )
            for field, kind in {
                "key": "string",
                "owner_character_id": "int",
                "subject_character_id": "int",
                "cycle_serial": "int",
                "case_serial": "int",
                "state": "int",
                "choice": "int",
            }.items()
        },
    }
    deadline_raw = _exact_object(
        frame.get("deadline"), _DEADLINE_KEYS, "deadline"
    )
    if deadline_raw.get("status") not in {
        "pending",
        "expired",
        "not_scheduled",
        "unavailable",
    }:
        raise ValueError("deadline.status is invalid")
    deadline = {
        "status": deadline_raw["status"],
        **{
            field: _typed_field(
                deadline_raw[field],
                f"deadline.{field}",
                value_kind=kind,
            )
            for field, kind in {
                "target_character_id": "int",
                "owner_character_id": "int",
                "cycle_serial": "int",
                "case_serial": "int",
                "expected_state": "int",
                "days": "int",
                "pending": "bool",
                "expired": "bool",
                "open_date_raw": "int",
                "due_date_raw": "int",
                "on_due_operation": "string",
            }.items()
        },
    }
    readiness_raw = _exact_object(
        frame.get("readiness"), _READINESS_KEYS, "readiness"
    )
    readiness: dict[str, bool] = {}
    for key in _READINESS_KEYS:
        flag = readiness_raw.get(key)
        if not isinstance(flag, bool):
            raise ValueError(f"readiness.{key} must be boolean")
        readiness[key] = flag
    expected_ready = all(
        readiness[key]
        for key in _READINESS_KEYS
        if key != "ready"
    )
    if readiness["ready"] is not expected_ready:
        raise ValueError("readiness.ready does not equal the component gate")

    provenance = _exact_object(
        frame.get("provenance"), _PROVENANCE_KEYS, "provenance"
    )
    if any(
        provenance.get(key) != expected
        for key, expected in _PROVENANCE_VALUES.items()
    ):
        raise ValueError("provenance does not match the frozen exact build")

    status = frame.get("status")
    reason = frame.get("unavailable_reason")
    if status == "available":
        if (
            reason is not None
            or not readiness["player_binding_ready"]
            or not readiness["case_identity_ready"]
        ):
            raise ValueError("available frame lacks a valid case identity")
    elif status == "unavailable":
        if reason not in _TOP_LEVEL_UNAVAILABLE_REASONS or readiness["ready"]:
            raise ValueError("unavailable frame has an invalid reason/gate")
    else:
        raise ValueError("status must be available or unavailable")

    case_ready = _all_typed_available(case, _CASE_KEYS)
    if readiness["case_identity_ready"] is not case_ready:
        raise ValueError("case identity readiness disagrees with typed fields")
    if case_ready:
        case_owner = _positive_int32(
            _typed_value(case["owner_character_id"], "case.owner_character_id"),
            "case.owner_character_id",
        )
        case_subject = _positive_int32(
            _typed_value(
                case["subject_character_id"], "case.subject_character_id"
            ),
            "case.subject_character_id",
        )
        if case_subject != subject:
            raise ValueError("available case subject does not match the request")
        if case_owner != player:
            raise ValueError("available case owner does not match the player")
        if requested_owner is not None and case_owner != requested_owner:
            raise ValueError("available case owner does not match the filter")
        for field in (
            "cycle_serial",
            "case_serial",
            "state",
            "revision",
            "timeline_serial",
            "feedback_revision",
        ):
            _integer(
                _typed_value(case[field], f"case.{field}"),
                f"case.{field}",
                minimum=1,
                maximum=2**63 - 1,
            )

    policy_ready = _all_typed_available(policy, _POLICY_KEYS)
    operation_ready = _all_typed_available(operation, _OPERATION_KEYS)
    if readiness["policy_ready"] is not policy_ready:
        raise ValueError("policy readiness disagrees with typed fields")
    if readiness["operation_ready"] is not operation_ready:
        raise ValueError("operation readiness disagrees with typed fields")
    if policy_ready:
        policy_values = {
            key: _typed_value(policy[key], f"policy.{key}")
            for key in _POLICY_KEYS
        }
        if policy_values != {"policy_id": "mechanism_039", "choice": 1}:
            raise ValueError("policy is outside the B1 v1 semantic allowlist")
    if operation_ready:
        if not policy_ready:
            raise ValueError("a recorded operation must expose its policy")
        operation_values = {
            key: _typed_value(operation[key], f"operation.{key}")
            for key in _OPERATION_KEYS
        }
        if (
            operation_values["operation_id"] != 39
            or operation_values["operation_key"] != "roster_lock"
            or operation_values["hook"] != "roster_lock"
        ):
            raise ValueError("operation is outside the B1 v1 semantic allowlist")
        for field in ("pre_state", "post_state"):
            _integer(
                operation_values[field],
                f"operation.{field}",
                minimum=1,
                maximum=2**63 - 1,
            )

    receipt_fields = _RECEIPT_KEYS - {"status"}
    receipt_available = _all_typed_available(receipt, receipt_fields)
    receipt_unavailable = _all_typed_unavailable(receipt, receipt_fields)
    receipt_status = receipt["status"]
    receipt_ready = (
        receipt_status == "recorded" and receipt_available
    ) or (receipt_status == "not_recorded" and receipt_unavailable)
    if receipt_status == "unavailable" and not receipt_unavailable:
        raise ValueError("unavailable receipt contains invented values")
    if readiness["receipt_ready"] is not receipt_ready:
        raise ValueError("receipt readiness disagrees with typed fields")
    if operation_ready is not (receipt_status == "recorded"):
        raise ValueError("operation and receipt availability disagree")
    if receipt_status == "recorded":
        receipt_values = {
            key: _typed_value(receipt[key], f"receipt.{key}")
            for key in receipt_fields
        }
        if receipt_values["key"] != "roster_lock":
            raise ValueError("receipt key is outside the B1 v1 allowlist")
        if case_ready and (
            receipt_values["owner_character_id"] != case_owner
            or receipt_values["subject_character_id"] != case_subject
            or receipt_values["cycle_serial"]
            != _typed_value(case["cycle_serial"], "case.cycle_serial")
            or receipt_values["case_serial"]
            != _typed_value(case["case_serial"], "case.case_serial")
        ):
            raise ValueError("receipt identity does not match the case")
        for field in (
            "owner_character_id",
            "subject_character_id",
        ):
            _positive_int32(receipt_values[field], f"receipt.{field}")
        for field in ("cycle_serial", "case_serial", "state", "choice"):
            _integer(
                receipt_values[field],
                f"receipt.{field}",
                minimum=1,
                maximum=2**63 - 1,
            )
        if receipt_values["choice"] != 1:
            raise ValueError("receipt choice is outside the B1 v1 allowlist")
        if operation_ready and (
            receipt_values["state"] != operation_values["pre_state"]
            or operation_values["pre_state"]
            != operation_values["post_state"]
            or receipt_values["choice"] != policy_values["choice"]
        ):
            raise ValueError("receipt does not match the recorded operation")

    deadline_fields = _DEADLINE_KEYS - {"status"}
    deadline_unavailable = _all_typed_unavailable(deadline, deadline_fields)
    deadline_status = deadline["status"]
    deadline_identity_ready = deadline_status == "not_scheduled"
    if deadline_status in {"pending", "expired"}:
        identity_fields = deadline_fields - {
            "open_date_raw",
            "due_date_raw",
        }
        deadline_identity_ready = _all_typed_available(
            deadline, identity_fields
        )
    elif deadline_status == "unavailable" and not deadline_unavailable:
        raise ValueError("unavailable deadline contains invented values")
    elif deadline_status == "not_scheduled" and not deadline_unavailable:
        raise ValueError("unscheduled deadline contains invented values")
    if readiness["deadline_identity_ready"] is not deadline_identity_ready:
        raise ValueError("deadline identity readiness disagrees with fields")

    due_date_ready = False
    if deadline_status in {"pending", "expired"}:
        due_date_ready = _typed_available(deadline["due_date_raw"])
    elif deadline_status == "not_scheduled":
        due_date_ready = True
    if readiness["deadline_due_date_ready"] is not due_date_ready:
        raise ValueError("deadline due-date readiness disagrees with fields")

    if deadline_status in {"pending", "expired"} and deadline_identity_ready:
        deadline_values = {
            key: _typed_value(deadline[key], f"deadline.{key}")
            for key in deadline_fields - {
                "open_date_raw",
                "due_date_raw",
            }
        }
        if deadline_values["on_due_operation"] != "resolve_pending_milestone":
            raise ValueError("deadline operation is outside the B1 v1 allowlist")
        if deadline_values["target_character_id"] != subject:
            raise ValueError("deadline target does not match the subject")
        if case_ready and (
            deadline_values["owner_character_id"] != case_owner
            or deadline_values["cycle_serial"]
            != _typed_value(case["cycle_serial"], "case.cycle_serial")
            or deadline_values["case_serial"]
            != _typed_value(case["case_serial"], "case.case_serial")
        ):
            raise ValueError("deadline identity does not match the case")
        if deadline_values["pending"] is not (deadline_status == "pending"):
            raise ValueError("deadline pending flag disagrees with status")
        if deadline_values["expired"] is not (deadline_status == "expired"):
            raise ValueError("deadline expired flag disagrees with status")
        for field in ("target_character_id", "owner_character_id"):
            _positive_int32(deadline_values[field], f"deadline.{field}")
        for field in (
            "cycle_serial",
            "case_serial",
            "expected_state",
            "days",
        ):
            _integer(
                deadline_values[field],
                f"deadline.{field}",
                minimum=1,
                maximum=2**63 - 1,
            )
        open_date_raw: int | None = None
        if _typed_available(deadline["open_date_raw"]):
            open_date_raw = _integer(
                _typed_value(
                    deadline["open_date_raw"], "deadline.open_date_raw"
                ),
                "deadline.open_date_raw",
                minimum=-(2**31),
                maximum=2**31 - 1,
            )
        if due_date_ready:
            due_date_raw = _integer(
                _typed_value(
                    deadline["due_date_raw"], "deadline.due_date_raw"
                ),
                "deadline.due_date_raw",
                minimum=-(2**31),
                maximum=2**31 - 1,
            )
            if open_date_raw is not None and due_date_raw < open_date_raw:
                raise ValueError("deadline due date precedes its open date")

    if status == "unavailable":
        if not (
            _all_typed_unavailable(case, _CASE_KEYS)
            and _all_typed_unavailable(policy, _POLICY_KEYS)
            and _all_typed_unavailable(operation, _OPERATION_KEYS)
            and receipt_status == "unavailable"
            and deadline_status == "unavailable"
        ):
            raise ValueError("unavailable frame contains invented case data")

    return {
        **frame,
        "case": case,
        "policy": policy,
        "operation": operation,
        "receipt": receipt,
        "deadline": deadline,
        "readiness": readiness,
        "provenance": dict(provenance),
    }


def normalize_zhongguo_case_snapshot_v1_response(
    value: object,
    *,
    expected_query: ZhongguoCaseQueryV1,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Validate the public MCP/service frame and every binding mirror."""

    final_frame = _exact_object(
        value, _FINAL_FRAME_KEYS, "zhongguo_case_snapshot_response"
    )
    expected_snapshot_id = _bounded_text(
        expected_snapshot_id, "expected_snapshot_id", maximum_bytes=256
    )
    expected_revision = _integer(
        expected_revision,
        "expected_revision",
        minimum=0,
        maximum=2**64 - 1,
    )
    expected_native_revision = _integer(
        expected_native_revision,
        "expected_native_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    expected_connection_generation = _integer(
        expected_connection_generation,
        "expected_connection_generation",
        minimum=1,
        maximum=2**64 - 1,
    )
    expected_date_raw = _integer(
        expected_date_raw,
        "expected_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_player_character_id = _positive_int32(
        expected_player_character_id,
        "expected_player_character_id",
    )

    native_frame = normalize_native_zhongguo_case_snapshot_v1(
        {key: final_frame[key] for key in _FRAME_KEYS},
        expected_query=expected_query,
        expected_snapshot_revision=expected_native_revision,
        expected_date_raw=expected_date_raw,
        expected_player_character_id=expected_player_character_id,
    )

    build = _exact_object(final_frame.get("build"), _BUILD_KEYS, "build")
    if build != {
        "version": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_VERSION,
        "exe_sha256": ZHONGGUO_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    }:
        raise ValueError("build does not match the frozen exact build")

    source = _exact_object(final_frame.get("source"), _SOURCE_KEYS, "source")
    expected_source = {
        "bridge_version": ZHONGGUO_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
        "game_adapter_id": ZHONGGUO_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID,
        "backend_id": ZHONGGUO_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
        "consumer_id": ZHONGGUO_CASE_SNAPSHOT_V1_CONSUMER_ID,
        "connection_generation": expected_connection_generation,
        "snapshot_id": expected_snapshot_id,
        "revision": expected_revision,
        "native_revision": expected_native_revision,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
    }
    if source != expected_source:
        raise ValueError("source does not match the paused request binding")

    actual_owner: int | None = None
    if native_frame["status"] == "available":
        case = native_frame["case"]
        assert isinstance(case, dict)  # normalized above
        owner_field = case["owner_character_id"]
        assert isinstance(owner_field, dict)  # normalized above
        actual_owner = _positive_int32(
            _typed_value(owner_field, "case.owner_character_id"),
            "case.owner_character_id",
        )

    binding = _exact_object(
        final_frame.get("binding"), _BINDING_KEYS, "binding"
    )
    expected_binding = {
        "request_nonce": expected_query.request_nonce,
        "snapshot_id": expected_snapshot_id,
        "revision": expected_revision,
        "native_revision": expected_native_revision,
        "connection_generation": expected_connection_generation,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
        "subject_character_id": expected_query.subject_character_id,
        "owner_character_id": actual_owner,
        "expected_revision": expected_revision,
    }
    if binding != expected_binding:
        raise ValueError("binding does not match the paused request/result")

    return {
        **native_frame,
        "build": dict(build),
        "source": dict(source),
        "binding": dict(binding),
    }
