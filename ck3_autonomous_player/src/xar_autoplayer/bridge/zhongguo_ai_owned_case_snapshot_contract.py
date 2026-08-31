"""Closed contract for a ZhongGuo B1 case owned by an AI manager.

The request selects one owner/subject pair.  Native code, rather than caller
data, proves that the owner is a living celestial AI ruler of duke rank or
higher and that the subject is the owner's direct landed subject.  The wire
does not expose an arbitrary CK3 variable reader.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-ai-owned-case-snapshot-v1"
)
QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-ai-owned-case-snapshot-v1"
)
QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CASE_KIND: Final = (
    "zhongguo.b1.performance"
)
ZHONGGUO_AI_OWNED_CASE_KIND_V1: Final = (
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CASE_KIND
)
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-ai-owned-case-snapshot-v1"
)
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-ai-owned-case-snapshot-v1"
)
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_ALLOWLIST_ID: Final = (
    "zg361-b1-ai-owned-case-v1"
)
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID: Final = (
    "native-headless"
)
ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1: Final = (
    "authorized_ai_background"
)

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_STABLE_KEY_RE: Final = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z"
)
_TYPED_FIELD_KEYS: Final = {"status", "value", "unavailable_reason"}
_ELIGIBILITY_KEYS: Final = {
    "owner_character_id",
    "owner_alive",
    "owner_is_ai",
    "primary_title_id",
    "primary_title_tier_raw",
    "primary_title_tier_key",
    "government_key",
    "subject_immediate_liege_character_id",
    "subject_is_direct_subject",
    "authorized",
}
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
_STAGE_KEYS: Final = {"state", "key", "active"}
_ROUTE_KEYS: Final = {
    "kind",
    "visible_event_allowed",
    "owner_is_ai",
    "manager_eligible",
    "direct_subject_eligible",
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
_READINESS_KEYS: Final = {
    "owner_eligibility_ready",
    "case_identity_ready",
    "stage_ready",
    "route_ready",
    "receipt_ready",
    "same_frame_ready",
    "ready",
}
_FIELD_UNAVAILABLE_REASONS: Final = {
    "case_unavailable",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "stage_inconsistent",
    "no_operation_recorded",
    "unknown_allowlisted_operation",
    "receipt_not_recorded",
    "receipt_inconsistent",
    "not_applicable",
}
_TOP_LEVEL_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "owner_is_played_character",
    "owner_eligibility_unavailable",
    "owner_not_alive",
    "owner_not_ai",
    "owner_not_celestial",
    "owner_not_landed_duke_plus",
    "subject_not_direct_subject",
    "case_not_found",
    "owner_filter_mismatch",
    "variable_identifier_unavailable",
    "variable_context_unavailable",
    "state_changed",
    "internal_error",
    "subject_not_found",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION,
    "executable_sha256": (
        ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
    ),
    "backend_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
    "variable_context_for_scope_rva": "0x3329A40",
    "character_storage_slot_rva": "0x570C130",
    "primary_title_rva": "0x25F3350",
    "immediate_liege_rva": "0x2613480",
    "government_rva": "0x26165B0",
    "is_human_player_rva": "0x28BCEB0",
}
_FRAME_KEYS: Final = {
    "schema_version",
    "status",
    "case_kind",
    "request_nonce",
    "snapshot_revision",
    "date_raw",
    "paused",
    "player_character_id",
    "requested_owner_character_id",
    "subject_character_id",
    "owner_eligibility",
    "case",
    "stage",
    "route",
    "policy",
    "operation",
    "receipt",
    "readiness",
    "unavailable_reason",
    "provenance",
}
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
    "owner_character_id",
    "subject_character_id",
    "expected_revision",
}
_FINAL_FRAME_KEYS: Final = _FRAME_KEYS | {"build", "source", "binding"}

_TITLE_TIER_KEYS: Final = {
    3: "duchy",
    4: "kingdom",
    5: "empire",
    6: "hegemony",
}
_STAGE_KEYS_BY_STATE: Final = {
    1: "targets_open",
    2: "midcycle_open",
    3: "evidence_open",
    4: "facts_frozen",
    5: "shadow_open",
    6: "quota_ready",
    7: "calibration_open",
    8: "published",
}


@dataclass(frozen=True)
class ZhongguoAiOwnedCaseQueryV1:
    owner_character_id: int
    subject_character_id: int
    request_nonce: str


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive signed int32")
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


def validate_ai_owned_case_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError(
            "request_nonce must be 1-64 ASCII token characters"
        )
    return value


def _validated_query(
    value: ZhongguoAiOwnedCaseQueryV1,
) -> ZhongguoAiOwnedCaseQueryV1:
    owner = _positive_int32(
        value.owner_character_id, "owner_character_id"
    )
    subject = _positive_int32(
        value.subject_character_id, "subject_character_id"
    )
    if owner == subject:
        raise ValueError("owner_character_id and subject_character_id differ")
    return ZhongguoAiOwnedCaseQueryV1(
        owner_character_id=owner,
        subject_character_id=subject,
        request_nonce=validate_ai_owned_case_request_nonce_v1(
            value.request_nonce
        ),
    )


def query_zhongguo_ai_owned_case_snapshot_v1_step(
    owner_character_id: object,
    subject_character_id: object,
    request_nonce: object,
) -> str:
    query = _validated_query(
        ZhongguoAiOwnedCaseQueryV1(
            owner_character_id=owner_character_id,  # type: ignore[arg-type]
            subject_character_id=subject_character_id,  # type: ignore[arg-type]
            request_nonce=request_nonce,  # type: ignore[arg-type]
        )
    )
    nonce_hex = query.request_nonce.encode("ascii").hex()
    return (
        f"{QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP_PREFIX}"
        f"{query.owner_character_id}-{query.subject_character_id}-{nonce_hex}"
    )


def parse_query_zhongguo_ai_owned_case_snapshot_v1_step(
    step: object,
) -> ZhongguoAiOwnedCaseQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_STEP_PREFIX
    ).split("-", 2)
    if len(parts) != 3:
        return None
    try:
        owner = int(parts[0], 10)
        subject = int(parts[1], 10)
        if str(owner) != parts[0] or str(subject) != parts[1]:
            return None
        if not parts[2] or len(parts[2]) % 2:
            return None
        nonce = bytes.fromhex(parts[2]).decode("ascii")
        query = _validated_query(
            ZhongguoAiOwnedCaseQueryV1(owner, subject, nonce)
        )
        if nonce.encode("ascii").hex() != parts[2]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return query


def _exact_object(
    value: object, fields: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _typed_field(
    value: object, name: str, *, value_kind: type
) -> dict[str, object]:
    field = _exact_object(value, _TYPED_FIELD_KEYS, name)
    status = field["status"]
    raw = field["value"]
    reason = field["unavailable_reason"]
    if status == "available":
        if reason is not None:
            raise ValueError(f"{name} available field has a reason")
        if value_kind is int:
            _integer(raw, name, minimum=-(2**63), maximum=2**63 - 1)
        elif value_kind is bool:
            if not isinstance(raw, bool):
                raise ValueError(f"{name}.value must be boolean")
        elif value_kind is str:
            if (
                not isinstance(raw, str)
                or _STABLE_KEY_RE.fullmatch(raw) is None
            ):
                raise ValueError(f"{name}.value must be a bounded stable key")
        else:  # pragma: no cover - programmer error
            raise AssertionError(value_kind)
    elif status == "unavailable":
        if raw is not None or reason not in _FIELD_UNAVAILABLE_REASONS:
            raise ValueError(f"{name} has a malformed unavailable field")
    else:
        raise ValueError(f"{name} has an unknown typed status")
    return dict(field)


def _typed_group(
    value: object,
    fields: set[str],
    kinds: dict[str, type],
    name: str,
) -> dict[str, dict[str, object]]:
    group = _exact_object(value, fields, name)
    return {
        key: _typed_field(group[key], f"{name}.{key}", value_kind=kind)
        for key, kind in kinds.items()
    }


def _available(field: dict[str, object]) -> bool:
    return field["status"] == "available"


def _value(field: dict[str, object], name: str) -> object:
    if not _available(field):
        raise ValueError(f"{name} must be available")
    return field["value"]


def _all_available(
    group: dict[str, dict[str, object]], fields: set[str]
) -> bool:
    return all(_available(group[key]) for key in fields)


def _all_unavailable_with_reason(
    group: dict[str, dict[str, object]], fields: set[str], reason: str
) -> bool:
    return all(
        not _available(group[key])
        and group[key]["unavailable_reason"] == reason
        for key in fields
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


def normalize_native_zhongguo_ai_owned_case_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoAiOwnedCaseQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Validate the exact-build native semantic frame and its cross-links."""

    expected_query = _validated_query(expected_query)
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
        expected_player_character_id, "expected_player_character_id"
    )
    frame = _exact_object(
        value, _FRAME_KEYS, "zhongguo_ai_owned_case_snapshot"
    )
    if frame["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if frame["case_kind"] != ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CASE_KIND:
        raise ValueError("case_kind is outside the fixed B1 product")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request nonce binding changed")
    revision = _integer(
        frame["snapshot_revision"],
        "snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    if revision != expected_snapshot_revision:
        raise ValueError("snapshot revision binding changed")
    date_raw = _integer(
        frame["date_raw"],
        "date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    if date_raw != expected_date_raw or frame["paused"] is not True:
        raise ValueError("snapshot is not the expected paused frame")
    player = _positive_int32(
        frame["player_character_id"], "player_character_id"
    )
    if player != expected_player_character_id:
        raise ValueError("played character binding changed")
    owner = _positive_int32(
        frame["requested_owner_character_id"],
        "requested_owner_character_id",
    )
    subject = _positive_int32(
        frame["subject_character_id"], "subject_character_id"
    )
    if owner != expected_query.owner_character_id:
        raise ValueError("owner request binding changed")
    if subject != expected_query.subject_character_id:
        raise ValueError("subject request binding changed")

    eligibility = _typed_group(
        frame["owner_eligibility"],
        _ELIGIBILITY_KEYS,
        {
            "owner_character_id": int,
            "owner_alive": bool,
            "owner_is_ai": bool,
            "primary_title_id": int,
            "primary_title_tier_raw": int,
            "primary_title_tier_key": str,
            "government_key": str,
            "subject_immediate_liege_character_id": int,
            "subject_is_direct_subject": bool,
            "authorized": bool,
        },
        "owner_eligibility",
    )
    case = _typed_group(
        frame["case"],
        _CASE_KEYS,
        {
            "owner_character_id": int,
            "subject_character_id": int,
            "cycle_serial": int,
            "case_serial": int,
            "state": int,
            "active": bool,
            "revision": int,
            "timeline_serial": int,
            "feedback_revision": int,
        },
        "case",
    )
    stage = _typed_group(
        frame["stage"],
        _STAGE_KEYS,
        {"state": int, "key": str, "active": bool},
        "stage",
    )
    route = _typed_group(
        frame["route"],
        _ROUTE_KEYS,
        {
            "kind": str,
            "visible_event_allowed": bool,
            "owner_is_ai": bool,
            "manager_eligible": bool,
            "direct_subject_eligible": bool,
        },
        "route",
    )
    policy = _typed_group(
        frame["policy"],
        _POLICY_KEYS,
        {"policy_id": str, "choice": int},
        "policy",
    )
    operation = _typed_group(
        frame["operation"],
        _OPERATION_KEYS,
        {
            "operation_id": int,
            "operation_key": str,
            "hook": str,
            "pre_state": int,
            "post_state": int,
        },
        "operation",
    )
    receipt_raw = _exact_object(frame["receipt"], _RECEIPT_KEYS, "receipt")
    receipt_status = receipt_raw["status"]
    if receipt_status not in {"recorded", "not_recorded", "unavailable"}:
        raise ValueError("receipt.status is invalid")
    receipt = {
        "status": receipt_status,
        **{
            key: _typed_field(
                receipt_raw[key], f"receipt.{key}", value_kind=kind
            )
            for key, kind in {
                "key": str,
                "owner_character_id": int,
                "subject_character_id": int,
                "cycle_serial": int,
                "case_serial": int,
                "state": int,
                "choice": int,
            }.items()
        },
    }
    readiness_raw = _exact_object(
        frame["readiness"], _READINESS_KEYS, "readiness"
    )
    if any(
        not isinstance(readiness_raw[key], bool) for key in _READINESS_KEYS
    ):
        raise ValueError("readiness must contain booleans")
    readiness = {key: bool(readiness_raw[key]) for key in _READINESS_KEYS}
    component_ready = all(
        readiness[key] for key in _READINESS_KEYS if key != "ready"
    )
    if readiness["ready"] is not component_ready:
        raise ValueError("readiness.ready disagrees with its component gate")
    provenance = _exact_object(
        frame["provenance"], set(_PROVENANCE_VALUES), "provenance"
    )
    if provenance != _PROVENANCE_VALUES:
        raise ValueError("provenance does not match the frozen exact ABI")

    status = frame["status"]
    unavailable_reason = frame["unavailable_reason"]
    semantic_groups = (
        (eligibility, _ELIGIBILITY_KEYS),
        (case, _CASE_KEYS),
        (stage, _STAGE_KEYS),
        (route, _ROUTE_KEYS),
        (policy, _POLICY_KEYS),
        (operation, _OPERATION_KEYS),
        (
            receipt,
            _RECEIPT_KEYS - {"status"},
        ),
    )
    if status == "unavailable":
        if unavailable_reason not in _TOP_LEVEL_UNAVAILABLE_REASONS:
            raise ValueError("unavailable frame has an unknown reason")
        if receipt_status != "unavailable" or any(
            not _all_unavailable_with_reason(group, fields, "case_unavailable")
            for group, fields in semantic_groups
        ):
            raise ValueError("unavailable frame leaks case semantics")
        expected_same_frame = unavailable_reason in {
            "case_not_found",
            "owner_filter_mismatch",
        }
        expected_readiness = {
            key: False for key in _READINESS_KEYS
        }
        expected_readiness["same_frame_ready"] = expected_same_frame
        if readiness != expected_readiness:
            raise ValueError("unavailable readiness disagrees with native flow")
        return {
            **frame,
            "owner_eligibility": eligibility,
            "case": case,
            "stage": stage,
            "route": route,
            "policy": policy,
            "operation": operation,
            "receipt": receipt,
            "readiness": readiness,
            "provenance": dict(provenance),
        }
    if status != "available" or unavailable_reason is not None:
        raise ValueError("available frame has a malformed status")
    if owner == player:
        raise ValueError("an available AI-owned case cannot be player-owned")

    eligibility_ready = _all_available(eligibility, _ELIGIBILITY_KEYS)
    if eligibility_ready:
        eligibility_values = {
            key: _value(eligibility[key], f"owner_eligibility.{key}")
            for key in _ELIGIBILITY_KEYS
        }
        title_tier = eligibility_values["primary_title_tier_raw"]
        eligibility_ready = (
            eligibility_values["owner_character_id"] == owner
            and eligibility_values["owner_alive"] is True
            and eligibility_values["owner_is_ai"] is True
            and isinstance(eligibility_values["primary_title_id"], int)
            and not isinstance(eligibility_values["primary_title_id"], bool)
            and eligibility_values["primary_title_id"] > 0
            and title_tier in _TITLE_TIER_KEYS
            and eligibility_values["primary_title_tier_key"]
            == _TITLE_TIER_KEYS.get(title_tier)
            and eligibility_values["government_key"]
            == "celestial_government"
            and eligibility_values["subject_immediate_liege_character_id"]
            == owner
            and eligibility_values["subject_is_direct_subject"] is True
            and eligibility_values["authorized"] is True
        )
    if not eligibility_ready:
        raise ValueError("available frame lacks authorized AI-owner evidence")

    case_ready = _all_available(case, _CASE_KEYS)
    if case_ready:
        case_values = {
            key: _value(case[key], f"case.{key}") for key in _CASE_KEYS
        }
        case_ready = (
            case_values["owner_character_id"] == owner
            and case_values["subject_character_id"] == subject
            and case_values["cycle_serial"] > 0
            and case_values["case_serial"] > 0
            and case_values["revision"] > 0
            and case_values["timeline_serial"] > 0
            and case_values["feedback_revision"] > 0
        )
    if not case_ready:
        raise ValueError("available frame lacks its exact case identity")

    stage_state = _value(stage["state"], "stage.state")
    stage_active = _value(stage["active"], "stage.active")
    if (
        stage_state != case_values["state"]
        or stage_active is not case_values["active"]
    ):
        raise ValueError("stage projection does not match the case")
    expected_stage_key = _STAGE_KEYS_BY_STATE.get(stage_state)
    stage_consistent = expected_stage_key is not None and (
        (stage_state < 8 and stage_active is True)
        or (stage_state == 8 and stage_active is False)
    )
    if stage_consistent:
        if not _available(stage["key"]) or (
            _value(stage["key"], "stage.key") != expected_stage_key
        ):
            raise ValueError("stage key does not match the case state")
    elif (
        _available(stage["key"])
        or stage["key"]["unavailable_reason"] != "stage_inconsistent"
    ):
        raise ValueError("inconsistent stage is not typed as unavailable")

    expected_route = {
        "kind": ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1,
        "visible_event_allowed": False,
        "owner_is_ai": True,
        "manager_eligible": True,
        "direct_subject_eligible": True,
    }
    if not _all_available(route, _ROUTE_KEYS) or any(
        _value(route[key], f"route.{key}") != expected
        for key, expected in expected_route.items()
    ):
        raise ValueError("route is not the authorized AI-background route")

    operation_id = (
        _value(operation["operation_id"], "operation.operation_id")
        if _available(operation["operation_id"])
        else None
    )
    policy_choice = (
        _value(policy["choice"], "policy.choice")
        if _available(policy["choice"])
        else None
    )
    semantic_operation = operation_id == 39 and policy_choice == 1
    no_operation = operation_id == 0
    if semantic_operation:
        if (
            not _available(policy["policy_id"])
            or _value(policy["policy_id"], "policy.policy_id")
            != "mechanism_039"
            or not _available(operation["operation_key"])
            or _value(operation["operation_key"], "operation.operation_key")
            != "roster_lock"
            or not _available(operation["hook"])
            or _value(operation["hook"], "operation.hook")
            != "roster_lock"
        ):
            raise ValueError("operation is outside the B1 semantic allowlist")
    else:
        semantic_reason = (
            "no_operation_recorded"
            if no_operation
            else "unknown_allowlisted_operation"
        )
        for field, name in (
            (policy["policy_id"], "policy.policy_id"),
            (operation["operation_key"], "operation.operation_key"),
            (operation["hook"], "operation.hook"),
        ):
            if _available(field) or field["unavailable_reason"] != semantic_reason:
                raise ValueError(f"{name} has an invalid negative projection")

    receipt_fields = _RECEIPT_KEYS - {"status"}
    receipt_ready = False
    if receipt_status == "recorded":
        if not semantic_operation or not _all_available(
            receipt, receipt_fields
        ):
            raise ValueError("recorded receipt lacks its allowlisted operation")
        receipt_values = {
            key: _value(receipt[key], f"receipt.{key}")
            for key in receipt_fields
        }
        expected_receipt_identity = {
            "key": "roster_lock",
            "owner_character_id": owner,
            "subject_character_id": subject,
            "cycle_serial": case_values["cycle_serial"],
            "case_serial": case_values["case_serial"],
            "choice": 1,
        }
        if any(
            receipt_values[key] != expected
            for key, expected in expected_receipt_identity.items()
        ) or receipt_values["state"] <= 0:
            raise ValueError("receipt identity does not match the case")
        if (
            not _available(operation["pre_state"])
            or not _available(operation["post_state"])
            or _value(operation["pre_state"], "operation.pre_state")
            != receipt_values["state"]
            or _value(operation["post_state"], "operation.post_state")
            != receipt_values["state"]
        ):
            raise ValueError("receipt does not match the operation state")
        receipt_ready = True
    elif receipt_status == "not_recorded":
        if not no_operation or not _all_unavailable_with_reason(
            receipt, receipt_fields, "receipt_not_recorded"
        ):
            raise ValueError("not-recorded receipt has invented semantics")
        for field in (operation["pre_state"], operation["post_state"]):
            if (
                _available(field)
                or field["unavailable_reason"] != "receipt_not_recorded"
            ):
                raise ValueError("not-recorded operation invented state")
        receipt_ready = True
    else:
        if no_operation:
            raise ValueError("operation zero must have a not-recorded receipt")
        if not _all_unavailable_with_reason(
            receipt, receipt_fields, "receipt_inconsistent"
        ):
            raise ValueError("unavailable receipt leaks inconsistent values")
        for field in (operation["pre_state"], operation["post_state"]):
            if (
                _available(field)
                or field["unavailable_reason"] != "receipt_inconsistent"
            ):
                raise ValueError("inconsistent operation state is malformed")

    computed_readiness = {
        "owner_eligibility_ready": eligibility_ready,
        "case_identity_ready": case_ready,
        "stage_ready": stage_consistent,
        "route_ready": True,
        "receipt_ready": receipt_ready,
        "same_frame_ready": True,
        "ready": (
            eligibility_ready
            and case_ready
            and stage_consistent
            and receipt_ready
        ),
    }
    if readiness != computed_readiness:
        raise ValueError("readiness disagrees with native semantic facts")

    return {
        **frame,
        "owner_eligibility": eligibility,
        "case": case,
        "stage": stage,
        "route": route,
        "policy": policy,
        "operation": operation,
        "receipt": receipt,
        "readiness": readiness,
        "provenance": dict(provenance),
    }


def normalize_zhongguo_ai_owned_case_snapshot_v1_response(
    value: object,
    *,
    expected_query: ZhongguoAiOwnedCaseQueryV1,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Validate the public service frame and every binding mirror."""

    expected_query = _validated_query(expected_query)
    final_frame = _exact_object(
        value,
        _FINAL_FRAME_KEYS,
        "zhongguo_ai_owned_case_snapshot_response",
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
        expected_player_character_id, "expected_player_character_id"
    )
    native_frame = normalize_native_zhongguo_ai_owned_case_snapshot_v1(
        {key: final_frame[key] for key in _FRAME_KEYS},
        expected_query=expected_query,
        expected_snapshot_revision=expected_native_revision,
        expected_date_raw=expected_date_raw,
        expected_player_character_id=expected_player_character_id,
    )
    build = _exact_object(final_frame["build"], _BUILD_KEYS, "build")
    if build != {
        "version": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_VERSION,
        "exe_sha256": (
            ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
        ),
    }:
        raise ValueError("build does not match the frozen exact build")
    source = _exact_object(final_frame["source"], _SOURCE_KEYS, "source")
    expected_source = {
        "bridge_version": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
        "game_adapter_id": (
            ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
        ),
        "backend_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
        "consumer_id": ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CONSUMER_ID,
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
    binding = _exact_object(
        final_frame["binding"], _BINDING_KEYS, "binding"
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
        "owner_character_id": expected_query.owner_character_id,
        "subject_character_id": expected_query.subject_character_id,
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
