"""Strict received-self ZhongGuo result-case snapshot contract.

The public query binds the paused played character as the only subject.  The
required owner is an equality filter, never a caller-selected read scope.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-result-case-snapshot-v1"
)
QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-result-case-snapshot-v1"
)
QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_RESULT_CASE_KIND_V1: Final = "zhongguo.result.received-self"
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-result-case-snapshot-v1"
)
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-result-case-snapshot-v1"
)
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_ALLOWLIST_ID: Final = (
    "zg361-result-received-self-v1"
)
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID: Final = "native-headless"

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_FIELD_KEYS: Final = {"status", "value", "unavailable_reason"}
_CASE_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "grade",
}
_NOTICE_KEYS: Final = {
    "absolute_grade",
    "kpi_frozen_q100000",
    "rank_frozen",
    "cohort_n_frozen",
}
_DELIVERY_KEYS: Final = {
    "method",
    "objection_recorded",
    "settlement_posted_serial",
    "appeal_open",
}
_READINESS_KEYS: Final = {
    "player_subject_binding_ready",
    "owner_binding_ready",
    "case_identity_ready",
    "notice_facts_ready",
    "delivery_state_ready",
    "same_frame_ready",
    "ready",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION,
    "executable_sha256": (
        ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256
    ),
    "backend_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_ALLOWLIST_ID,
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
    "notice",
    "delivery",
    "readiness",
    "unavailable_reason",
    "provenance",
}
_TOP_LEVEL_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "case_not_found",
    "case_inconsistent",
    "owner_filter_mismatch",
    "not_received_self",
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
class ZhongguoResultCaseQueryV1:
    owner_character_id: int
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


def validate_result_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError(
            "request_nonce must be 1-64 ASCII token characters"
        )
    return value


def query_zhongguo_result_case_snapshot_v1_step(
    owner_character_id: object,
    request_nonce: object,
) -> str:
    owner = _positive_int32(owner_character_id, "owner_character_id")
    nonce = validate_result_request_nonce_v1(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_result_case_snapshot_v1_step(
    step: object,
) -> ZhongguoResultCaseQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    tail = step.removeprefix(
        QUERY_ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_STEP_PREFIX
    )
    parts = tail.split("-", 1)
    if len(parts) != 2:
        return None
    try:
        owner = int(parts[0], 10)
        if str(owner) != parts[0]:
            return None
        owner = _positive_int32(owner, "owner_character_id")
        if not parts[1] or len(parts[1]) % 2 != 0:
            return None
        nonce = bytes.fromhex(parts[1]).decode("ascii")
        nonce = validate_result_request_nonce_v1(nonce)
        if nonce.encode("ascii").hex() != parts[1]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoResultCaseQueryV1(
        owner_character_id=owner,
        request_nonce=nonce,
    )


def _exact_object(
    value: object, fields: set[str], name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _typed_field(
    value: object, name: str, *, value_kind: str
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
    else:  # pragma: no cover - internal programming error
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


def _available(field: dict[str, object]) -> bool:
    return field["status"] == "available"


def _value(field: dict[str, object], name: str) -> object:
    if not _available(field):
        raise ValueError(f"{name} must be available")
    return field["value"]


def _all_available(group: dict[str, object], fields: set[str]) -> bool:
    return all(
        isinstance(group[field], dict) and _available(group[field])
        for field in fields
    )


def _all_unavailable(group: dict[str, object], fields: set[str]) -> bool:
    return all(
        isinstance(group[field], dict) and not _available(group[field])
        for field in fields
    )


def _bounded_text(value: object, name: str, *, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    encoded = value.encode("utf-8")
    if len(encoded) > maximum_bytes or any(
        ord(character) < 0x20 for character in value
    ):
        raise ValueError(f"{name} must be bounded text without controls")
    return value


def _delivery_matrix_ready(
    *,
    state: int,
    grade: int,
    case_serial: int,
    method: int,
    objection: bool,
    settlement: int,
    appeal: bool,
) -> bool:
    if grade != 1:
        return False
    return (
        (state, method, settlement, appeal, objection)
        == (1, 0, 0, False, False)
        or (state, method, settlement, appeal, objection)
        == (3, 1, case_serial, True, False)
        or (state, method, settlement, appeal, objection)
        == (3, 2, case_serial, True, True)
        or (state, method, settlement, appeal, objection)
        == (2, 3, 0, False, False)
    )


def normalize_native_zhongguo_result_case_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoResultCaseQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    expected_query = ZhongguoResultCaseQueryV1(
        owner_character_id=_positive_int32(
            expected_query.owner_character_id,
            "expected_query.owner_character_id",
        ),
        request_nonce=validate_result_request_nonce_v1(
            expected_query.request_nonce
        ),
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
        expected_player_character_id, "expected_player_character_id"
    )

    frame = _exact_object(
        value, _FRAME_KEYS, "zhongguo_result_case_snapshot"
    )
    if frame.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if frame.get("case_kind") != ZHONGGUO_RESULT_CASE_KIND_V1:
        raise ValueError("case_kind binding changed")
    if frame.get("request_nonce") != expected_query.request_nonce:
        raise ValueError("request_nonce binding changed")
    if _integer(
        frame.get("snapshot_revision"),
        "snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    ) != expected_snapshot_revision:
        raise ValueError("snapshot revision binding changed")
    if _integer(
        frame.get("date_raw"),
        "date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    ) != expected_date_raw:
        raise ValueError("date binding changed")
    if frame.get("paused") is not True:
        raise ValueError("result-case query is not paused")
    player = _positive_int32(
        frame.get("player_character_id"), "player_character_id"
    )
    if player != expected_player_character_id:
        raise ValueError("player identity binding changed")
    subject = _positive_int32(
        frame.get("subject_character_id"), "subject_character_id"
    )
    if subject != player:
        raise ValueError("received-self subject is not the played character")
    requested_owner = _positive_int32(
        frame.get("requested_owner_character_id"),
        "requested_owner_character_id",
    )
    if requested_owner != expected_query.owner_character_id:
        raise ValueError("owner filter binding changed")

    case = _typed_group(
        frame.get("case"),
        _CASE_KEYS,
        {field: "int" for field in _CASE_KEYS},
        "case",
    )
    notice = _typed_group(
        frame.get("notice"),
        _NOTICE_KEYS,
        {field: "int" for field in _NOTICE_KEYS},
        "notice",
    )
    delivery = _typed_group(
        frame.get("delivery"),
        _DELIVERY_KEYS,
        {
            "method": "int",
            "objection_recorded": "bool",
            "settlement_posted_serial": "int",
            "appeal_open": "bool",
        },
        "delivery",
    )
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
        readiness[key] for key in _READINESS_KEYS if key != "ready"
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
        if reason is not None or not all(
            readiness[key]
            for key in (
                "player_subject_binding_ready",
                "owner_binding_ready",
                "case_identity_ready",
            )
        ):
            raise ValueError("available frame lacks its identity bindings")
    elif status == "unavailable":
        if reason not in _TOP_LEVEL_UNAVAILABLE_REASONS or readiness["ready"]:
            raise ValueError("unavailable frame has an invalid reason/gate")
    else:
        raise ValueError("status must be available or unavailable")

    case_ready = _all_available(case, _CASE_KEYS)
    if readiness["case_identity_ready"] is not case_ready:
        raise ValueError("case identity readiness disagrees with typed fields")
    case_values: dict[str, int] = {}
    if case_ready:
        case_values = {
            field: _integer(
                _value(case[field], f"case.{field}"),
                f"case.{field}",
                minimum=-(2**63),
                maximum=2**63 - 1,
            )
            for field in _CASE_KEYS
        }
        if (
            _positive_int32(
                case_values["owner_character_id"],
                "case.owner_character_id",
            )
            != expected_query.owner_character_id
            or case_values["owner_character_id"] == player
            or _positive_int32(
                case_values["subject_character_id"],
                "case.subject_character_id",
            )
            != player
            or case_values["cycle_serial"] < 1
            or not 1 <= case_values["case_serial"] <= 999_999
            or not 1 <= case_values["state"] <= 5
            or not 1 <= case_values["grade"] <= 3
        ):
            raise ValueError("available case identity violates received-self")
    if readiness["player_subject_binding_ready"] is not case_ready:
        raise ValueError("player-subject readiness disagrees with case")
    if readiness["owner_binding_ready"] is not case_ready:
        raise ValueError("owner readiness disagrees with case")

    notice_ready = _all_available(notice, _NOTICE_KEYS)
    if notice_ready:
        notice_values = {
            field: _integer(
                _value(notice[field], f"notice.{field}"),
                f"notice.{field}",
                minimum=-(2**63),
                maximum=2**63 - 1,
            )
            for field in _NOTICE_KEYS
        }
        notice_ready = (
            1 <= notice_values["absolute_grade"] <= 3
            and notice_values["rank_frozen"] >= 1
            and notice_values["cohort_n_frozen"] >= 1
            and notice_values["rank_frozen"]
            <= notice_values["cohort_n_frozen"]
        )
    if readiness["notice_facts_ready"] is not notice_ready:
        raise ValueError("notice readiness disagrees with frozen facts")

    delivery_ready = _all_available(delivery, _DELIVERY_KEYS)
    if delivery_ready:
        method = _integer(
            _value(delivery["method"], "delivery.method"),
            "delivery.method",
            minimum=-(2**63),
            maximum=2**63 - 1,
        )
        settlement = _integer(
            _value(
                delivery["settlement_posted_serial"],
                "delivery.settlement_posted_serial",
            ),
            "delivery.settlement_posted_serial",
            minimum=-(2**63),
            maximum=2**63 - 1,
        )
        objection = _value(
            delivery["objection_recorded"], "delivery.objection_recorded"
        )
        appeal = _value(delivery["appeal_open"], "delivery.appeal_open")
        assert isinstance(objection, bool) and isinstance(appeal, bool)
        delivery_ready = (
            case_ready
            and 0 <= method <= 3
            and 0 <= settlement <= 999_999
            and _delivery_matrix_ready(
                state=case_values["state"],
                grade=case_values["grade"],
                case_serial=case_values["case_serial"],
                method=method,
                objection=objection,
                settlement=settlement,
                appeal=appeal,
            )
        )
    if readiness["delivery_state_ready"] is not delivery_ready:
        raise ValueError("delivery readiness disagrees with product state")

    if status == "unavailable" and not (
        _all_unavailable(case, _CASE_KEYS)
        and _all_unavailable(notice, _NOTICE_KEYS)
        and _all_unavailable(delivery, _DELIVERY_KEYS)
        and not readiness["player_subject_binding_ready"]
        and not readiness["owner_binding_ready"]
        and not readiness["case_identity_ready"]
        and not readiness["notice_facts_ready"]
        and not readiness["delivery_state_ready"]
    ):
        raise ValueError("unavailable result-case leaks semantic fields")

    return {
        **frame,
        "case": case,
        "notice": notice,
        "delivery": delivery,
        "readiness": readiness,
        "provenance": dict(provenance),
    }


def normalize_zhongguo_result_case_snapshot_v1_response(
    value: object,
    *,
    expected_query: ZhongguoResultCaseQueryV1,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    final_frame = _exact_object(
        value,
        _FINAL_FRAME_KEYS,
        "zhongguo_result_case_snapshot_response",
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
    native_frame = normalize_native_zhongguo_result_case_snapshot_v1(
        {key: final_frame[key] for key in _FRAME_KEYS},
        expected_query=expected_query,
        expected_snapshot_revision=expected_native_revision,
        expected_date_raw=expected_date_raw,
        expected_player_character_id=expected_player_character_id,
    )
    build = _exact_object(final_frame.get("build"), _BUILD_KEYS, "build")
    if build != {
        "version": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_VERSION,
        "exe_sha256": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    }:
        raise ValueError("build does not match the frozen exact build")
    source = _exact_object(
        final_frame.get("source"), _SOURCE_KEYS, "source"
    )
    expected_source = {
        "bridge_version": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_BRIDGE_VERSION,
        "game_adapter_id": (
            ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_GAME_ADAPTER_ID
        ),
        "backend_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
        "consumer_id": ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_CONSUMER_ID,
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
        assert isinstance(case, dict)
        owner = case["owner_character_id"]
        assert isinstance(owner, dict)
        actual_owner = _positive_int32(
            _value(owner, "case.owner_character_id"),
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
        "subject_character_id": expected_player_character_id,
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
