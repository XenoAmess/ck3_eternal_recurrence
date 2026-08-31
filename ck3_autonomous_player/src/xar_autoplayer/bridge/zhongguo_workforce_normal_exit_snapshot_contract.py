"""Strict received-self Workforce normal-exit/HC lifecycle contract.

The provider owns one fixed, player-scope allowlist.  A caller may select only
an expected owner equality filter and a nonce; it cannot choose the subject,
lifecycle stage, variable names, or read scope.  The lifecycle is derived from
the highest complete product tuple and covers the visible #075 offer through
the delayed rehire copy::

    pre -> migrating -> sealed -> rehire_captured

The immutable sealed receipt remains valid after later legitimate HC changes.
Whether the live HC still equals that receipt is therefore an independent
readiness fact, never a prerequisite for receipt validity.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Mapping


QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-workforce-normal-exit-snapshot-v1"
)
QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-workforce-normal-exit-snapshot-v1"
)
QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_WORKFORCE_NORMAL_EXIT_CASE_KIND_V1: Final = (
    "zhongguo.workforce.normal-exit.received-self"
)
ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1: Final = "1.19.0.6"
ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_WORKFORCE_NORMAL_EXIT_BACKEND_ID_V1: Final = (
    "ck3-1.19.0.6-native-zhongguo-workforce-normal-exit-snapshot-v1"
)
ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1: Final = (
    "xar-autoplayer-zhongguo-workforce-normal-exit-snapshot-v1"
)
ZHONGGUO_WORKFORCE_NORMAL_EXIT_ALLOWLIST_ID_V1: Final = (
    "zg361-workforce-normal-exit-received-self-v1"
)
ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1: Final = "0.1.0"
ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_ADAPTER_ID_V1: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_WORKFORCE_NORMAL_EXIT_SOURCE_BACKEND_ID_V1: Final = "native-headless"

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS: Final = {"status", "value", "unavailable_reason"}
_PARTITION_SPEC: Final = {
    "authorized": "int",
    "available": "int",
    "reserved": "int",
    "occupied": "int",
    "frozen": "int",
    "reclaimed": "int",
}
_SOURCE_SPEC: Final = {
    "owner_character_id": "character",
    "subject_character_id": "character",
    "cycle_serial": "int",
    "case_serial": "int",
    "state": "int",
    "route": "int",
    "offer_gold": "int",
    "receipt_serial": "int",
    "object_owner_character_id": "character",
    "object_subject_character_id": "character",
    "object_cycle_serial": "int",
    "object_receipt_case_serial": "int",
    "object_route": "int",
    "object_active": "bool",
    "object_consumed": "bool",
    "consumer_receipt_case_serial": "int",
}
_WORKFLOW_SCALAR_SPEC: Final = {
    "pending": "bool",
    "pending_owner_character_id": "character",
    "pending_subject_character_id": "character",
    "pending_cycle_serial": "int",
    "pending_case_serial": "int",
    "state": "int",
    "pending_hc_migration_authorized": "bool",
    "pending_slot_case_serial": "int",
}
_WORKFLOW_KEYS: Final = set(_WORKFLOW_SCALAR_SPEC) | {"pending_hc_before"}
_CURRENT_HC_SCALAR_SPEC: Final = {
    "formal_active": "bool",
    "formal_case_serial": "int",
}
_CURRENT_HC_KEYS: Final = set(_CURRENT_HC_SCALAR_SPEC) | {"partition"}
_RECEIPT_SCALAR_SPEC: Final = {
    "active": "bool",
    "sealed": "bool",
    "published": "bool",
    "consumed": "bool",
    "consumed_operation": "int",
    "owner_character_id": "character",
    "subject_character_id": "character",
    "cycle_serial": "int",
    "case_serial": "int",
    "state": "int",
    "receipt_id": "int",
    "receipt_hash": "int",
    "hc_ledger_settled": "bool",
    "hc_destination_frozen": "bool",
    "hc_conservation_verified": "bool",
    "formal_hc_active_before": "bool",
    "formal_hc_active_after": "bool",
    "formal_hc_case_serial": "int",
}
_RECEIPT_KEYS: Final = set(_RECEIPT_SCALAR_SPEC) | {"hc_before", "hc_after"}
_REHIRE_SCALAR_SPEC: Final = {
    "state": "int",
    "subject_character_id": "character",
    "exit_owner_character_id": "character",
    "exit_cycle_serial": "int",
    "exit_case_serial": "int",
    "exit_state": "int",
    "exit_receipt_id": "int",
    "exit_receipt_hash": "int",
    "normal_exit_verified": "bool",
    "exit_hc_destination_frozen": "bool",
    "exit_hc_conservation_verified": "bool",
    "exit_formal_hc_active_before": "bool",
    "exit_formal_hc_active_after": "bool",
    "exit_formal_hc_case_serial": "int",
}
_REHIRE_KEYS: Final = set(_REHIRE_SCALAR_SPEC) | {
    "exit_hc_before",
    "exit_hc_after",
}
_READINESS_KEYS: Final = {
    "player_subject_binding_ready",
    "owner_binding_ready",
    "source_object_ready",
    "pending_snapshot_ready",
    "current_hc_partition_ready",
    "migration_delta_ready",
    "sealed_receipt_ready",
    "rehire_capture_ready",
    "current_hc_matches_stage_ready",
    "lifecycle_ready",
    "same_frame_ready",
    "ready",
}
_FIELD_UNAVAILABLE_REASONS: Final = {
    "case_unavailable",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "stage_not_reached",
}
_TOP_UNAVAILABLE_REASONS: Final = {
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
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
    "executable_sha256": ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
    "backend_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_BACKEND_ID_V1,
    "consumer_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1,
    "allowlist_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_ALLOWLIST_ID_V1,
    "variable_context_for_scope_rva": "0x3329A40",
    "variable_identifier_table_rva": "0x3B971A0",
    "variable_identifier_lookup_rva": "0x3B97020",
    "variable_identifier_name_rva": "0x3B97090",
    "character_storage_slot_rva": "0x570C130",
    "subject_allowlist_count": 94,
    "owner_allowlist_count": 0,
    "query_scope": "paused_received_self_workforce_normal_exit_lifecycle",
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
    "subject_character_id",
    "requested_owner_character_id",
    "lifecycle",
    "source",
    "workflow",
    "current_hc",
    "receipt",
    "rehire",
    "readiness",
    "unavailable_reason",
    "provenance",
}
_BUILD_KEYS: Final = {"version", "exe_sha256"}
_SOURCE_BINDING_KEYS: Final = {
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
_FINAL_FRAME_KEYS: Final = _FRAME_KEYS | {"build", "bridge_source", "binding"}


@dataclass(frozen=True)
class ZhongguoWorkforceNormalExitQueryV1:
    owner_character_id: int
    request_nonce: str


def _exact(value: object, fields: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} must be an integer in range")
    return value


def _positive_int32(value: object, name: str) -> int:
    return _integer(value, name, 1, 2**31 - 1)


def validate_workforce_normal_exit_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError("request_nonce must be 1-64 ASCII token characters")
    return value


def query_zhongguo_workforce_normal_exit_snapshot_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive_int32(owner_character_id, "owner_character_id")
    nonce = validate_workforce_normal_exit_request_nonce_v1(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_workforce_normal_exit_snapshot_v1_step(
    step: object,
) -> ZhongguoWorkforceNormalExitQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    tail = step.removeprefix(
        QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP_PREFIX
    )
    parts = tail.split("-", 1)
    if len(parts) != 2:
        return None
    try:
        owner = int(parts[0], 10)
        if str(owner) != parts[0]:
            return None
        owner = _positive_int32(owner, "owner_character_id")
        if not parts[1] or len(parts[1]) % 2:
            return None
        nonce = bytes.fromhex(parts[1]).decode("ascii")
        nonce = validate_workforce_normal_exit_request_nonce_v1(nonce)
        if nonce.encode("ascii").hex() != parts[1]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoWorkforceNormalExitQueryV1(owner, nonce)


def _typed(value: object, name: str, kind: str) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    if field["status"] == "unavailable":
        if (
            field["value"] is not None
            or field["unavailable_reason"] not in _FIELD_UNAVAILABLE_REASONS
        ):
            raise ValueError(f"{name} has invalid typed unavailability")
    elif field["status"] == "available" and field["unavailable_reason"] is None:
        raw = field["value"]
        if kind == "bool":
            if not isinstance(raw, bool):
                raise ValueError(f"{name}.value must be boolean")
        else:
            _integer(raw, f"{name}.value", -(2**63), 2**63 - 1)
            if kind == "character" and not 1 <= raw <= 2**31 - 1:
                raise ValueError(f"{name}.value must be a positive character id")
    else:
        raise ValueError(f"{name} has invalid typed availability")
    return dict(field)


def _typed_group(
    value: object, spec: Mapping[str, str], name: str
) -> dict[str, object]:
    raw = _exact(value, set(spec), name)
    return {key: _typed(raw[key], f"{name}.{key}", kind) for key, kind in spec.items()}


def _partition(value: object, name: str) -> dict[str, object]:
    return _typed_group(value, _PARTITION_SPEC, name)


def _workflow(value: object) -> dict[str, object]:
    raw = _exact(value, _WORKFLOW_KEYS, "workflow")
    result = _typed_group(
        {key: raw[key] for key in _WORKFLOW_SCALAR_SPEC},
        _WORKFLOW_SCALAR_SPEC,
        "workflow",
    )
    result["pending_hc_before"] = _partition(
        raw["pending_hc_before"], "workflow.pending_hc_before"
    )
    return result


def _current_hc(value: object) -> dict[str, object]:
    raw = _exact(value, _CURRENT_HC_KEYS, "current_hc")
    result = _typed_group(
        {key: raw[key] for key in _CURRENT_HC_SCALAR_SPEC},
        _CURRENT_HC_SCALAR_SPEC,
        "current_hc",
    )
    result["partition"] = _partition(raw["partition"], "current_hc.partition")
    return result


def _receipt(value: object) -> dict[str, object]:
    raw = _exact(value, _RECEIPT_KEYS, "receipt")
    result = _typed_group(
        {key: raw[key] for key in _RECEIPT_SCALAR_SPEC},
        _RECEIPT_SCALAR_SPEC,
        "receipt",
    )
    result["hc_before"] = _partition(raw["hc_before"], "receipt.hc_before")
    result["hc_after"] = _partition(raw["hc_after"], "receipt.hc_after")
    return result


def _rehire(value: object) -> dict[str, object]:
    raw = _exact(value, _REHIRE_KEYS, "rehire")
    result = _typed_group(
        {key: raw[key] for key in _REHIRE_SCALAR_SPEC},
        _REHIRE_SCALAR_SPEC,
        "rehire",
    )
    result["exit_hc_before"] = _partition(
        raw["exit_hc_before"], "rehire.exit_hc_before"
    )
    result["exit_hc_after"] = _partition(
        raw["exit_hc_after"], "rehire.exit_hc_after"
    )
    return result


def _available(field: object) -> bool:
    return isinstance(field, dict) and field.get("status") == "available"


def _fields(group: Mapping[str, object]):
    for value in group.values():
        if isinstance(value, dict) and set(value) == _TYPED_KEYS:
            yield value
        elif isinstance(value, dict):
            yield from _fields(value)


def _all_available(group: Mapping[str, object]) -> bool:
    fields = tuple(_fields(group))
    return bool(fields) and all(_available(field) for field in fields)


def _all_unavailable(group: Mapping[str, object]) -> bool:
    fields = tuple(_fields(group))
    return bool(fields) and all(not _available(field) for field in fields)


def _any_available(group: Mapping[str, object]) -> bool:
    return any(_available(field) for field in _fields(group))


def _value(group: Mapping[str, object], key: str, name: str) -> object:
    field = group[key]
    if not _available(field):
        raise ValueError(f"{name}.{key} must be available")
    assert isinstance(field, dict)
    return field["value"]


def _int(group: Mapping[str, object], key: str, name: str) -> int:
    return _integer(_value(group, key, name), f"{name}.{key}", -(2**63), 2**63 - 1)


def _bool(group: Mapping[str, object], key: str, name: str) -> bool:
    raw = _value(group, key, name)
    if not isinstance(raw, bool):
        raise ValueError(f"{name}.{key} must be boolean")
    return raw


def _partition_values(group: Mapping[str, object], name: str) -> dict[str, int]:
    return {key: _int(group, key, name) for key in _PARTITION_SPEC}


def _partition_conserved(values: Mapping[str, int]) -> bool:
    return (
        values["authorized"] >= 1
        and all(values[key] >= 0 for key in _PARTITION_SPEC if key != "authorized")
        and values["authorized"]
        == sum(values[key] for key in _PARTITION_SPEC if key != "authorized")
    )


def _migration_valid(before: Mapping[str, int], after: Mapping[str, int]) -> bool:
    return (
        _partition_conserved(before)
        and _partition_conserved(after)
        and after["authorized"] == before["authorized"]
        and after["available"] == before["available"]
        and after["reserved"] == before["reserved"]
        and after["reclaimed"] == before["reclaimed"]
        and after["occupied"] == before["occupied"] - 1
        and after["frozen"] == before["frozen"] + 1
    )


def _unavailable_only(
    *,
    source: Mapping[str, object],
    workflow: Mapping[str, object],
    current_hc: Mapping[str, object],
    receipt: Mapping[str, object],
    rehire: Mapping[str, object],
) -> bool:
    return all(
        _all_unavailable(group)
        for group in (source, workflow, current_hc, receipt, rehire)
    )


def _derive_available_lifecycle(
    *,
    source: Mapping[str, object],
    workflow: Mapping[str, object],
    current_hc: Mapping[str, object],
    receipt: Mapping[str, object],
    rehire: Mapping[str, object],
    player: int,
    owner: int,
) -> tuple[str, dict[str, bool]]:
    if not all(
        _available(source[key])
        for key in _SOURCE_SPEC
        if key != "consumer_receipt_case_serial"
    ) or not _all_available(current_hc):
        raise ValueError("source and live HC must be complete")

    source_owner = _int(source, "owner_character_id", "source")
    source_subject = _int(source, "subject_character_id", "source")
    cycle = _int(source, "cycle_serial", "source")
    case = _int(source, "case_serial", "source")
    source_state = _int(source, "state", "source")
    source_post = source_state == 3
    if not (
        source_owner == owner
        and source_owner != player
        and source_subject == player
        and cycle > 0
        and case > 0
        and _int(source, "route", "source") == 1
        and _int(source, "offer_gold", "source") == 50
        and _int(source, "receipt_serial", "source") == case
        and _int(source, "object_owner_character_id", "source") == owner
        and _int(source, "object_subject_character_id", "source") == player
        and _int(source, "object_cycle_serial", "source") == cycle
        and _int(source, "object_receipt_case_serial", "source") == case
        and _int(source, "object_route", "source") == 1
        and (
            (
                source_state == 1
                and _bool(source, "object_active", "source")
                and not _bool(source, "object_consumed", "source")
                and not _available(source["consumer_receipt_case_serial"])
            )
            or (
                source_post
                and not _bool(source, "object_active", "source")
                and _bool(source, "object_consumed", "source")
                and _int(source, "consumer_receipt_case_serial", "source") == case
            )
        )
    ):
        raise ValueError("#075 source object is not the canonical route-A tuple")

    live_partition = current_hc["partition"]
    assert isinstance(live_partition, dict)
    live = _partition_values(live_partition, "current_hc.partition")
    if not _partition_conserved(live):
        raise ValueError("live HC partition is not conserved")
    formal_active = _bool(current_hc, "formal_active", "current_hc")
    formal_case = _int(current_hc, "formal_case_serial", "current_hc")
    if formal_case <= 0:
        raise ValueError("live formal HC lineage is absent")

    receipt_touched = _any_available(receipt)
    rehire_touched = _any_available(rehire)
    workflow_state_available = _available(workflow["state"])
    pending_touched = any(
        _available(workflow[key])
        for key in _WORKFLOW_SCALAR_SPEC
        if key not in {"state", "pending_hc_migration_authorized"}
    ) or _any_available(workflow["pending_hc_before"])  # type: ignore[arg-type]

    pending_ready = False
    migration_ready = False
    sealed_ready = False
    rehire_ready = False
    current_matches = False

    if rehire_touched or receipt_touched:
        if not _all_available(receipt):
            raise ValueError("higher sealed stage is partial")
        if not source_post:
            raise ValueError("sealed receipt lacks consumed #075 source")
        if pending_touched or not workflow_state_available or _int(workflow, "state", "workflow") != 4:
            raise ValueError("sealed workflow did not clear the pending tuple")
        for key in _WORKFLOW_SCALAR_SPEC:
            if key != "state" and _available(workflow[key]):
                raise ValueError("sealed workflow retains pending fields")
        if _any_available(workflow["pending_hc_before"]):  # type: ignore[arg-type]
            raise ValueError("sealed workflow retains pending HC")

        receipt_before_group = receipt["hc_before"]
        receipt_after_group = receipt["hc_after"]
        assert isinstance(receipt_before_group, dict)
        assert isinstance(receipt_after_group, dict)
        before = _partition_values(receipt_before_group, "receipt.hc_before")
        after = _partition_values(receipt_after_group, "receipt.hc_after")
        if not (
            _migration_valid(before, after)
            and all(
                _bool(receipt, key, "receipt")
                for key in (
                    "active",
                    "sealed",
                    "published",
                    "consumed",
                    "hc_ledger_settled",
                    "hc_destination_frozen",
                    "hc_conservation_verified",
                    "formal_hc_active_before",
                )
            )
            and not _bool(receipt, "formal_hc_active_after", "receipt")
            and _int(receipt, "consumed_operation", "receipt") == 75
            and _int(receipt, "owner_character_id", "receipt") == owner
            and _int(receipt, "subject_character_id", "receipt") == player
            and _int(receipt, "cycle_serial", "receipt") == cycle
            and _int(receipt, "case_serial", "receipt") == case
            and _int(receipt, "state", "receipt") == 6
            and _int(receipt, "receipt_id", "receipt") > 0
            and _int(receipt, "receipt_hash", "receipt") > 0
            and _int(receipt, "formal_hc_case_serial", "receipt") > 0
        ):
            raise ValueError("sealed normal-exit receipt is inconsistent")
        receipt_formal_case = _int(
            receipt, "formal_hc_case_serial", "receipt"
        )
        migration_ready = True
        sealed_ready = True
        current_matches = (
            live == after and not formal_active and formal_case == receipt_formal_case
        )

        if rehire_touched:
            if not _all_available(rehire):
                raise ValueError("higher rehire stage is partial")
            rehire_before_group = rehire["exit_hc_before"]
            rehire_after_group = rehire["exit_hc_after"]
            assert isinstance(rehire_before_group, dict)
            assert isinstance(rehire_after_group, dict)
            rehire_before = _partition_values(
                rehire_before_group, "rehire.exit_hc_before"
            )
            rehire_after = _partition_values(
                rehire_after_group, "rehire.exit_hc_after"
            )
            if not (
                _int(rehire, "state", "rehire") >= 1
                and _int(rehire, "subject_character_id", "rehire") == player
                and _int(rehire, "exit_owner_character_id", "rehire") == owner
                and _int(rehire, "exit_cycle_serial", "rehire") == cycle
                and _int(rehire, "exit_case_serial", "rehire") == case
                and _int(rehire, "exit_state", "rehire") == 6
                and _int(rehire, "exit_receipt_id", "rehire")
                == _int(receipt, "receipt_id", "receipt")
                and _int(rehire, "exit_receipt_hash", "rehire")
                == _int(receipt, "receipt_hash", "receipt")
                and _bool(rehire, "normal_exit_verified", "rehire")
                and _bool(rehire, "exit_hc_destination_frozen", "rehire")
                and _bool(rehire, "exit_hc_conservation_verified", "rehire")
                and _bool(rehire, "exit_formal_hc_active_before", "rehire")
                and not _bool(rehire, "exit_formal_hc_active_after", "rehire")
                and _int(rehire, "exit_formal_hc_case_serial", "rehire")
                == receipt_formal_case
                and rehire_before == before
                and rehire_after == after
            ):
                raise ValueError("rehire capture does not preserve sealed provenance")
            rehire_ready = True
            lifecycle = "rehire_captured"
        else:
            if not _all_unavailable(rehire):
                raise ValueError("sealed stage leaks partial rehire fields")
            lifecycle = "sealed"
    else:
        if not _all_unavailable(receipt) or not _all_unavailable(rehire):
            raise ValueError("pre-seal stage leaks receipt fields")
        if workflow_state_available and _int(workflow, "state", "workflow") == 3:
            lifecycle = "migrating"
        else:
            lifecycle = "pre"

        if pending_touched:
            expected_pending_keys = {
                "pending",
                "pending_owner_character_id",
                "pending_subject_character_id",
                "pending_cycle_serial",
                "pending_case_serial",
                "pending_slot_case_serial",
            }
            if not all(_available(workflow[key]) for key in expected_pending_keys):
                raise ValueError("pending identity is partial")
            pending_before_group = workflow["pending_hc_before"]
            assert isinstance(pending_before_group, dict)
            if not _all_available(pending_before_group):
                raise ValueError("pending HC before partition is partial")
            before = _partition_values(
                pending_before_group, "workflow.pending_hc_before"
            )
            if not (
                _partition_conserved(before)
                and _bool(workflow, "pending", "workflow")
                and _int(workflow, "pending_owner_character_id", "workflow") == owner
                and _int(workflow, "pending_subject_character_id", "workflow") == player
                and _int(workflow, "pending_cycle_serial", "workflow") == cycle
                and _int(workflow, "pending_case_serial", "workflow") == case
                and _int(workflow, "pending_slot_case_serial", "workflow")
                == formal_case
            ):
                raise ValueError("pending snapshot is not bound to #075/live HC")
            pending_ready = True
        else:
            before = {}
            for key in _WORKFLOW_SCALAR_SPEC:
                if _available(workflow[key]):
                    raise ValueError("workflow state exists without pending identity")
            if _any_available(workflow["pending_hc_before"]):  # type: ignore[arg-type]
                raise ValueError("pending HC exists without pending identity")

        if lifecycle == "migrating":
            if not (
                pending_ready
                and source_post
                and _bool(workflow, "pending_hc_migration_authorized", "workflow")
                and _migration_valid(before, live)
                and not formal_active
            ):
                raise ValueError("migrating stage lacks the occupied-to-frozen delta")
            migration_ready = True
            current_matches = True
        elif source_post:
            if not (
                pending_ready
                and workflow_state_available
                and _int(workflow, "state", "workflow") == 2
                and not _available(workflow["pending_hc_migration_authorized"])
                and live == before
                and formal_active
            ):
                raise ValueError("accepted-before-migration stage is inconsistent")
            current_matches = True
        elif pending_ready:
            if workflow_state_available or _available(
                workflow["pending_hc_migration_authorized"]
            ):
                raise ValueError("pre-migration workflow advanced unexpectedly")
            if live != before or not formal_active:
                raise ValueError("pre-migration HC drifted from the frozen snapshot")
            current_matches = True
        else:
            if source_post:
                raise ValueError("consumed source has no workflow evidence")
            current_matches = False

    readiness = {
        "player_subject_binding_ready": True,
        "owner_binding_ready": True,
        "source_object_ready": True,
        "pending_snapshot_ready": pending_ready,
        "current_hc_partition_ready": True,
        "migration_delta_ready": migration_ready,
        "sealed_receipt_ready": sealed_ready,
        "rehire_capture_ready": rehire_ready,
        "current_hc_matches_stage_ready": current_matches,
        "lifecycle_ready": True,
        "same_frame_ready": True,
        "ready": True,
    }
    return lifecycle, readiness


def normalize_native_zhongguo_workforce_normal_exit_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoWorkforceNormalExitQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    query = ZhongguoWorkforceNormalExitQueryV1(
        _positive_int32(expected_query.owner_character_id, "expected owner"),
        validate_workforce_normal_exit_request_nonce_v1(expected_query.request_nonce),
    )
    revision = _integer(
        expected_snapshot_revision, "expected_snapshot_revision", 1, 2**64 - 1
    )
    date_raw = _integer(expected_date_raw, "expected_date_raw", -(2**31), 2**31 - 1)
    player = _positive_int32(
        expected_player_character_id, "expected_player_character_id"
    )
    frame = _exact(value, _FRAME_KEYS, "workforce_normal_exit_snapshot")
    if frame["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if frame["case_kind"] != ZHONGGUO_WORKFORCE_NORMAL_EXIT_CASE_KIND_V1:
        raise ValueError("case_kind binding changed")
    if frame["request_nonce"] != query.request_nonce:
        raise ValueError("request_nonce binding changed")
    if _integer(frame["snapshot_revision"], "snapshot_revision", 1, 2**64 - 1) != revision:
        raise ValueError("snapshot revision binding changed")
    if _integer(frame["date_raw"], "date_raw", -(2**31), 2**31 - 1) != date_raw:
        raise ValueError("date binding changed")
    if frame["paused"] is not True:
        raise ValueError("normal-exit query is not paused")
    if _positive_int32(frame["player_character_id"], "player_character_id") != player:
        raise ValueError("player identity binding changed")
    if _positive_int32(frame["subject_character_id"], "subject_character_id") != player:
        raise ValueError("received-self subject is not the played character")
    if _positive_int32(
        frame["requested_owner_character_id"], "requested_owner_character_id"
    ) != query.owner_character_id:
        raise ValueError("owner filter binding changed")

    source = _typed_group(frame["source"], _SOURCE_SPEC, "source")
    workflow = _workflow(frame["workflow"])
    current_hc = _current_hc(frame["current_hc"])
    receipt = _receipt(frame["receipt"])
    rehire = _rehire(frame["rehire"])
    readiness_raw = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if not all(isinstance(readiness_raw[key], bool) for key in _READINESS_KEYS):
        raise ValueError("readiness fields must be boolean")
    readiness = {key: bool(readiness_raw[key]) for key in _READINESS_KEYS}
    provenance = _exact(frame["provenance"], set(_PROVENANCE_VALUES), "provenance")
    if any(provenance[key] != expected for key, expected in _PROVENANCE_VALUES.items()):
        raise ValueError("provenance does not match the frozen exact build")

    status = frame["status"]
    reason = frame["unavailable_reason"]
    if status == "unavailable":
        if (
            frame["lifecycle"] != "unavailable"
            or reason not in _TOP_UNAVAILABLE_REASONS
            or readiness["ready"]
            or not _unavailable_only(
                source=source,
                workflow=workflow,
                current_hc=current_hc,
                receipt=receipt,
                rehire=rehire,
            )
        ):
            raise ValueError("unavailable frame leaks lifecycle facts")
    elif status == "available" and reason is None:
        lifecycle, expected_readiness = _derive_available_lifecycle(
            source=source,
            workflow=workflow,
            current_hc=current_hc,
            receipt=receipt,
            rehire=rehire,
            player=player,
            owner=query.owner_character_id,
        )
        if frame["lifecycle"] != lifecycle:
            raise ValueError("lifecycle label is not the highest complete stage")
        if readiness != expected_readiness:
            raise ValueError("readiness does not equal the proven lifecycle facts")
    else:
        raise ValueError("snapshot has invalid top-level status")
    return {
        **frame,
        "source": source,
        "workflow": workflow,
        "current_hc": current_hc,
        "receipt": receipt,
        "rehire": rehire,
        "readiness": readiness,
        "provenance": dict(provenance),
    }


def _bounded_text(value: object, name: str, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum_bytes:
        raise ValueError(f"{name} must be bounded non-empty text")
    return value


def normalize_zhongguo_workforce_normal_exit_snapshot_v1_response(
    value: object,
    *,
    expected_query: ZhongguoWorkforceNormalExitQueryV1,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    final = _exact(value, _FINAL_FRAME_KEYS, "workforce_normal_exit_response")
    snapshot_id = _bounded_text(expected_snapshot_id, "expected_snapshot_id", 256)
    revision = _integer(expected_revision, "expected_revision", 0, 2**64 - 1)
    native_revision = _integer(
        expected_native_revision, "expected_native_revision", 1, 2**64 - 1
    )
    generation = _integer(
        expected_connection_generation, "expected_connection_generation", 1, 2**64 - 1
    )
    normalized = normalize_native_zhongguo_workforce_normal_exit_snapshot_v1(
        {key: final[key] for key in _FRAME_KEYS},
        expected_query=expected_query,
        expected_snapshot_revision=native_revision,
        expected_date_raw=expected_date_raw,
        expected_player_character_id=expected_player_character_id,
    )
    build = _exact(final["build"], _BUILD_KEYS, "build")
    if build != {
        "version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_VERSION_V1,
        "exe_sha256": ZHONGGUO_WORKFORCE_NORMAL_EXIT_EXECUTABLE_SHA256_V1,
    }:
        raise ValueError("build binding changed")
    bridge_source = _exact(
        final["bridge_source"], _SOURCE_BINDING_KEYS, "bridge_source"
    )
    expected_source = {
        "bridge_version": ZHONGGUO_WORKFORCE_NORMAL_EXIT_BRIDGE_VERSION_V1,
        "game_adapter_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_GAME_ADAPTER_ID_V1,
        "backend_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_SOURCE_BACKEND_ID_V1,
        "consumer_id": ZHONGGUO_WORKFORCE_NORMAL_EXIT_CONSUMER_ID_V1,
        "connection_generation": generation,
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
    }
    if bridge_source != expected_source:
        raise ValueError("bridge source binding changed")
    binding = _exact(final["binding"], _BINDING_KEYS, "binding")
    expected_binding = {
        "request_nonce": expected_query.request_nonce,
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "connection_generation": generation,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
        "subject_character_id": expected_player_character_id,
        "owner_character_id": expected_query.owner_character_id,
        "expected_revision": revision,
    }
    if binding != expected_binding:
        raise ValueError("response binding changed")
    return {
        **normalized,
        "build": dict(build),
        "bridge_source": dict(bridge_source),
        "binding": dict(binding),
    }


def query_zhongguo_workforce_normal_exit_snapshot_v1_step_payload(
    owner_character_id: object, request_nonce: object
) -> dict[str, object]:
    query = ZhongguoWorkforceNormalExitQueryV1(
        _positive_int32(owner_character_id, "owner_character_id"),
        validate_workforce_normal_exit_request_nonce_v1(request_nonce),
    )
    return {
        "step": QUERY_ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_STEP,
        "owner_character_id": query.owner_character_id,
        "request_nonce": query.request_nonce,
    }
