"""Strict received-self Workforce collective and rolling-three-cycle contract."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-workforce-collective-snapshot-v1"
)
QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-workforce-collective-snapshot-v1"
)
QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_WORKFORCE_COLLECTIVE_CASE_KIND_V1: Final = (
    "zhongguo.workforce-collective"
)
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-workforce-collective-snapshot-v1"
)
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-workforce-collective-snapshot-v1"
)
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_ALLOWLIST_ID: Final = (
    "zg361-workforce-collective-received-self-v1"
)
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_SOURCE_BACKEND_ID: Final = (
    "native-headless"
)

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS: Final = {"status", "value", "unavailable_reason"}
_FIELD_REASONS: Final = {
    "case_unavailable", "variable_absent", "value_type_mismatch",
    "value_out_of_range", "not_applicable", "lifecycle_not_reached",
    "receipt_not_recorded",
}
_TOP_REASONS: Final = {
    "unsupported_build", "requires_application_main", "requires_paused",
    "map_not_ready", "case_not_found", "case_inconsistent",
    "owner_filter_mismatch", "variable_identifier_unavailable",
    "variable_context_unavailable", "collective_inconsistent",
    "history_inconsistent", "state_changed", "internal_error",
}
_CASE_SPEC: Final = {
    "owner_character_id": "int", "subject_character_id": "int",
    "cycle_serial": "int", "case_serial": "int", "state": "int",
    "active": "bool", "revision": "int",
}
_RECEIPT_SPEC: Final = {
    "owner_character_id": "int", "subject_character_id": "int",
    "cycle_serial": "int", "case_serial": "int", "state": "int",
    "choice": "int",
}
_COLLECTIVE_SPEC: Final = {
    "submission_active": "bool", "submission_sealed": "bool",
    "submission_consumed": "bool", "owner_character_id": "int",
    "subject_character_id": "int", "cycle_serial": "int",
    "case_serial": "int", "state": "int", "collective_case_serial": "int",
    "submitted_cycle_serial": "int", "cohort_count": "int",
    "settlement_id": "int", "settlement_hash": "int", "settled": "bool",
    "route": "int", "total_members": "int", "total_quota": "int",
    "forced_count": "int", "exception_count": "int",
    "manager_cost_total": "int",
}
_COHORT_SPEC: Final = {
    "cohort_id": "int", "manager_character_id": "int",
    "member_count": "int", "member_hash": "int", "quota": "int",
    "forced_count": "int", "exception_count": "int", "manager_cost": "int",
    "partition_verified": "bool", "approval_verified": "bool",
    "b1_cycle_serial": "int", "b1_case_serial": "int",
    "b1_source_id": "int", "b1_source_hash": "int",
    "mg_cycle_serial": "int", "mg_case_serial": "int",
    "mg_snapshot_source_serial": "int", "mg_snapshot_revision": "int",
}
_DEBT_SPEC: Final = {
    "owner_character_id": "int", "subject_character_id": "int",
    "cycle_serial": "int", "case_serial": "int", "state": "int",
    "open": "bool", "consumed": "bool", "due_cycle_serial": "int",
}
_HISTORY_SLOT_SPEC: Final = {
    "owner_character_id": "int", "subject_character_id": "int",
    "cycle_serial": "int", "case_serial": "int",
    "m357_receipt_id": "int", "m357_receipt_hash": "int",
    "m358_receipt_id": "int", "m358_receipt_hash": "int",
    "m359_receipt_id": "int", "m359_receipt_hash": "int",
}
_CHARTER_SPEC: Final = {
    "evidence_count": "int", "evidence_ready": "bool",
    "evidence_consumed": "bool", "owner_character_id": "int",
    "subject_character_id": "int", "cycle_serial": "int",
    "case_serial": "int", "state": "int", "prepared_report_id": "int",
    "prepared_charter_id": "int", "previous_charter_id": "int",
    "previous_version": "int", "adopted_cycle_serial": "int",
    "effective_cycle_serial": "int", "portfolio_status": "int",
    "portfolio_closed": "bool", "terminal_history_accruing": "bool",
    "portfolio_history_cycle_count": "int", "terminal_success": "bool",
}
_READINESS_KEYS: Final = {
    "player_subject_binding_ready", "owner_binding_ready",
    "case_identity_ready", "m360_receipt_projection_ready",
    "collective_lifecycle_ready", "cohort_identity_ready",
    "cohort_conservation_ready", "route_conservation_ready",
    "history_ledger_ready", "history_order_ready", "three_cycle_ready",
    "charter_gate_lifecycle_ready", "same_frame_ready", "ready",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION,
    "executable_sha256": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256,
    "backend_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_ALLOWLIST_ID,
    "variable_context_for_scope_rva": "0x3329A40",
    "variable_identifier_table_rva": "0x3B971A0",
    "variable_identifier_lookup_rva": "0x3B97020",
    "variable_identifier_name_rva": "0x3B97090",
    "character_storage_slot_rva": "0x570C130",
    "subject_allowlist_count": 144,
    "owner_allowlist_count": 31,
    "query_scope": "paused_received_self_al_case_plus_owner_rolling_three_cycle",
}
_FRAME_KEYS: Final = {
    "schema_version", "status", "case_kind", "request_nonce",
    "snapshot_revision", "date_raw", "paused", "player_character_id",
    "subject_character_id", "requested_owner_character_id", "al_case",
    "m360_receipt", "collective", "cohorts", "route_c_debt", "history",
    "charter_gate", "readiness", "unavailable_reason", "provenance",
}
_BUILD_KEYS: Final = {"version", "exe_sha256"}
_SOURCE_KEYS: Final = {
    "bridge_version", "game_adapter_id", "backend_id", "consumer_id",
    "connection_generation", "snapshot_id", "revision", "native_revision",
    "date_raw", "paused", "player_character_id",
}
_BINDING_KEYS: Final = {
    "request_nonce", "snapshot_id", "revision", "native_revision",
    "connection_generation", "date_raw", "paused", "player_character_id",
    "subject_character_id", "owner_character_id", "expected_revision",
}
_FINAL_FRAME_KEYS: Final = _FRAME_KEYS | {"build", "source", "binding"}


@dataclass(frozen=True)
class ZhongguoWorkforceCollectiveQueryV1:
    owner_character_id: int
    request_nonce: str


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in range")
    return value


def _positive(value: object, name: str) -> int:
    return _integer(value, name, 1, 2**31 - 1)


def validate_workforce_collective_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError("request_nonce must be 1-64 ASCII token characters")
    return value


def query_zhongguo_workforce_collective_snapshot_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive(owner_character_id, "owner_character_id")
    nonce = validate_workforce_collective_request_nonce_v1(request_nonce)
    return f"{QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP_PREFIX}{owner}-{nonce.encode('ascii').hex()}"


def parse_query_zhongguo_workforce_collective_snapshot_v1_step(
    step: object,
) -> ZhongguoWorkforceCollectiveQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP_PREFIX):
        return None
    parts = step.removeprefix(QUERY_ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_STEP_PREFIX).split("-", 1)
    if len(parts) != 2:
        return None
    try:
        owner = int(parts[0], 10)
        if str(owner) != parts[0]:
            return None
        owner = _positive(owner, "owner_character_id")
        if not parts[1] or len(parts[1]) % 2:
            return None
        nonce = bytes.fromhex(parts[1]).decode("ascii")
        nonce = validate_workforce_collective_request_nonce_v1(nonce)
        if nonce.encode("ascii").hex() != parts[1]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoWorkforceCollectiveQueryV1(owner, nonce)


def _typed(value: object, name: str, kind: str) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    if field["status"] == "unavailable":
        if field["value"] is not None or field["unavailable_reason"] not in _FIELD_REASONS:
            raise ValueError(f"{name} has invalid typed unavailability")
    elif field["status"] == "available" and field["unavailable_reason"] is None:
        if kind == "int":
            _integer(field["value"], name, -(2**63), 2**63 - 1)
        elif kind == "bool" and not isinstance(field["value"], bool):
            raise ValueError(f"{name}.value must be boolean")
    else:
        raise ValueError(f"{name} has invalid typed availability")
    return dict(field)


def _group(value: object, spec: dict[str, str], name: str) -> dict[str, object]:
    raw = _exact(value, set(spec), name)
    return {key: _typed(raw[key], f"{name}.{key}", kind) for key, kind in spec.items()}


def _available(field: dict[str, object]) -> bool:
    return field["status"] == "available"


def _value(field: dict[str, object], name: str) -> object:
    if not _available(field):
        raise ValueError(f"{name} must be available")
    return field["value"]


def _all_reason(group: dict[str, object], reason: str) -> bool:
    return all(field["status"] == "unavailable" and field["unavailable_reason"] == reason for field in group.values())


def _field(field: dict[str, object], expected: object) -> bool:
    return _available(field) and field["value"] == expected


def _all_available(group: dict[str, object]) -> bool:
    return all(_available(field) for field in group.values())


def _bounded_text(value: object, name: str, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum_bytes or any(ord(c) < 0x20 for c in value):
        raise ValueError(f"{name} must be bounded plain text")
    return value


def normalize_native_zhongguo_workforce_collective_snapshot_v1(
    value: object, *, expected_query: ZhongguoWorkforceCollectiveQueryV1,
    expected_snapshot_revision: int, expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    expected_query = ZhongguoWorkforceCollectiveQueryV1(
        _positive(expected_query.owner_character_id, "expected owner"),
        validate_workforce_collective_request_nonce_v1(expected_query.request_nonce),
    )
    revision = _integer(expected_snapshot_revision, "expected_snapshot_revision", 1, 2**64 - 1)
    date_raw = _integer(expected_date_raw, "expected_date_raw", -(2**31), 2**31 - 1)
    player = _positive(expected_player_character_id, "expected_player_character_id")
    frame = _exact(value, _FRAME_KEYS, "zhongguo_workforce_collective_snapshot")
    if frame["schema_version"] != 1 or frame["case_kind"] != ZHONGGUO_WORKFORCE_COLLECTIVE_CASE_KIND_V1:
        raise ValueError("schema/case kind binding changed")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request_nonce binding changed")
    if _integer(frame["snapshot_revision"], "snapshot_revision", 1, 2**64 - 1) != revision:
        raise ValueError("snapshot revision binding changed")
    if _integer(frame["date_raw"], "date_raw", -(2**31), 2**31 - 1) != date_raw:
        raise ValueError("date binding changed")
    if frame["paused"] is not True:
        raise ValueError("workforce query is not paused")
    if _positive(frame["player_character_id"], "player_character_id") != player or _positive(frame["subject_character_id"], "subject_character_id") != player:
        raise ValueError("received-self subject binding changed")
    if _positive(frame["requested_owner_character_id"], "requested owner") != expected_query.owner_character_id:
        raise ValueError("owner filter binding changed")

    case = _group(frame["al_case"], _CASE_SPEC, "al_case")
    receipt = _group(frame["m360_receipt"], _RECEIPT_SPEC, "m360_receipt")
    collective_raw = _exact(frame["collective"], {"phase", *_COLLECTIVE_SPEC}, "collective")
    phase = collective_raw["phase"]
    if phase not in {"unavailable", "not_reached", "route_a_exception", "route_b_forced", "route_c_debt"}:
        raise ValueError("collective.phase is invalid")
    collective = _group({key: collective_raw[key] for key in _COLLECTIVE_SPEC}, _COLLECTIVE_SPEC, "collective")
    cohorts_raw = frame["cohorts"]
    if not isinstance(cohorts_raw, list) or len(cohorts_raw) != 3:
        raise ValueError("cohorts must contain exactly three fixed slots")
    cohorts = [_group(item, _COHORT_SPEC, f"cohorts[{index}]") for index, item in enumerate(cohorts_raw)]
    debt = _group(frame["route_c_debt"], _DEBT_SPEC, "route_c_debt")
    history_raw = _exact(frame["history"], {"status", "count", "effective_count", "slots"}, "history")
    history_status = history_raw["status"]
    if history_status not in {"unavailable", "empty", "partial", "three_cycle"}:
        raise ValueError("history.status is invalid")
    history_count = _typed(history_raw["count"], "history.count", "int")
    effective_count = _integer(history_raw["effective_count"], "history.effective_count", -1, 3)
    slots_raw = history_raw["slots"]
    if not isinstance(slots_raw, list) or len(slots_raw) != 3:
        raise ValueError("history.slots must contain exactly three fixed slots")
    slots = [_group(item, _HISTORY_SLOT_SPEC, f"history.slots[{index}]") for index, item in enumerate(slots_raw)]
    charter_raw = _exact(frame["charter_gate"], {"status", *_CHARTER_SPEC}, "charter_gate")
    charter_status = charter_raw["status"]
    if charter_status not in {"unavailable", "not_eligible", "awaiting_gate", "ready", "consumed"}:
        raise ValueError("charter_gate.status is invalid")
    charter = _group({key: charter_raw[key] for key in _CHARTER_SPEC}, _CHARTER_SPEC, "charter_gate")
    readiness_raw = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(readiness_raw[key], bool) for key in _READINESS_KEYS):
        raise ValueError("readiness values must be boolean")
    readiness = dict(readiness_raw)
    expected_ready = all(readiness[key] for key in _READINESS_KEYS - {"three_cycle_ready", "ready"})
    if readiness["ready"] is not expected_ready:
        raise ValueError("readiness.ready disagrees with the component gate")
    provenance = _exact(frame["provenance"], set(_PROVENANCE_VALUES), "provenance")
    if provenance != _PROVENANCE_VALUES:
        raise ValueError("provenance does not match the frozen exact build")

    status = frame["status"]
    if status == "unavailable":
        if frame["unavailable_reason"] not in _TOP_REASONS or readiness["ready"] or any(readiness.values()):
            raise ValueError("unavailable frame fabricates readiness")
        groups = [case, receipt, collective, *cohorts, debt, *slots, charter]
        if phase != "unavailable" or history_status != "unavailable" or effective_count != -1 or not all(_all_reason(group, "case_unavailable") for group in groups) or history_count["unavailable_reason"] != "case_unavailable":
            raise ValueError("unavailable frame leaks semantic payload")
    elif status == "available":
        if frame["unavailable_reason"] is not None or not readiness["ready"]:
            raise ValueError("available frame has an invalid gate")
        if not _all_available(case):
            raise ValueError("available frame lacks AL case identity")
        owner, cycle, case_serial = expected_query.owner_character_id, _value(case["cycle_serial"], "case.cycle"), _value(case["case_serial"], "case.serial")
        case_ready = (
            _field(case["owner_character_id"], owner) and _field(case["subject_character_id"], player)
            and isinstance(cycle, int) and cycle >= 1 and isinstance(case_serial, int) and case_serial > 0
            and isinstance(_value(case["state"], "case.state"), int) and 1 <= _value(case["state"], "case.state") <= 8
            and isinstance(_value(case["revision"], "case.revision"), int) and _value(case["revision"], "case.revision") >= 1
        )
        if not case_ready or not readiness["case_identity_ready"] or not readiness["owner_binding_ready"]:
            raise ValueError("AL case readiness disagrees with identity")
        if phase == "not_reached":
            if not _all_reason(receipt, "receipt_not_recorded") or not _all_reason(collective, "lifecycle_not_reached") or not all(_all_reason(c, "lifecycle_not_reached") for c in cohorts) or not _all_reason(debt, "lifecycle_not_reached"):
                raise ValueError("not_reached lifecycle fabricates products")
        else:
            if not _all_available(receipt) or not (_field(receipt["owner_character_id"], owner) and _field(receipt["subject_character_id"], player) and _field(receipt["cycle_serial"], cycle) and _field(receipt["case_serial"], case_serial) and _field(receipt["state"], 4)):
                raise ValueError("M360 receipt identity is inconsistent")
            choice = _value(receipt["choice"], "receipt.choice")
            if choice not in (1, 2, 3):
                raise ValueError("M360 choice is outside A/B/C")
            if phase in {"route_a_exception", "route_b_forced"}:
                expected_choice = 1 if phase == "route_a_exception" else 2
                if choice != expected_choice or not _all_reason(debt, "not_applicable") or not _all_available(collective) or not all(_all_available(c) for c in cohorts):
                    raise ValueError("collective route surface is inconsistent")
                manager_ids = [_value(c["manager_character_id"], "cohort.manager") for c in cohorts]
                cohort_ids = [_value(c["cohort_id"], "cohort.id") for c in cohorts]
                if len(set(manager_ids)) != 3 or len(set(cohort_ids)) != 3:
                    raise ValueError("three cohort identities must be distinct")
                totals = {key: sum(_value(c[key], f"cohort.{key}") for c in cohorts) for key in ("member_count", "quota", "forced_count", "exception_count", "manager_cost")}
                for cohort in cohorts:
                    quota = _value(cohort["quota"], "cohort.quota")
                    member_count = _value(cohort["member_count"], "cohort.members")
                    if not (0 <= quota <= 6 and member_count >= quota and _field(cohort["partition_verified"], True)):
                        raise ValueError("cohort partition is invalid")
                    if phase == "route_a_exception":
                        route_ok = _field(cohort["forced_count"], 0) and _field(cohort["exception_count"], quota) and _field(cohort["manager_cost"], quota) and _field(cohort["approval_verified"], True)
                    else:
                        route_ok = _field(cohort["forced_count"], quota) and _field(cohort["exception_count"], 0) and _field(cohort["manager_cost"], 0) and _field(cohort["approval_verified"], False)
                    evidence_ok = all(isinstance(_value(cohort[key], f"cohort.{key}"), int) and _value(cohort[key], f"cohort.{key}") > 0 for key in ("b1_cycle_serial", "b1_case_serial", "b1_source_id", "b1_source_hash", "mg_cycle_serial", "mg_case_serial", "mg_snapshot_source_serial", "mg_snapshot_revision"))
                    if not route_ok or not evidence_ok:
                        raise ValueError("cohort route/evidence is inconsistent")
                collective_ok = (
                    _field(collective["submission_active"], False) and _field(collective["submission_sealed"], True) and _field(collective["submission_consumed"], True)
                    and _field(collective["owner_character_id"], owner) and _field(collective["subject_character_id"], player)
                    and _field(collective["cycle_serial"], cycle) and _field(collective["case_serial"], case_serial) and _field(collective["state"], 4)
                    and _field(collective["collective_case_serial"], case_serial) and _field(collective["submitted_cycle_serial"], cycle)
                    and _field(collective["cohort_count"], 3) and _value(collective["settlement_id"], "settlement_id") > 0 and _value(collective["settlement_hash"], "settlement_hash") > 0
                    and _field(collective["settled"], True) and _field(collective["route"], choice)
                    and _field(collective["total_members"], totals["member_count"]) and _field(collective["total_quota"], totals["quota"])
                    and 1 <= totals["quota"] <= 6 and _field(collective["forced_count"], totals["forced_count"])
                    and _field(collective["exception_count"], totals["exception_count"]) and _field(collective["manager_cost_total"], totals["manager_cost"])
                )
                if not collective_ok:
                    raise ValueError("collective conservation is inconsistent")
            else:
                if choice != 3 or not _all_reason(collective, "not_applicable") or not all(_all_reason(c, "not_applicable") for c in cohorts) or not _all_available(debt):
                    raise ValueError("route C surface is inconsistent")
                if not (_field(debt["owner_character_id"], owner) and _field(debt["subject_character_id"], player) and _field(debt["cycle_serial"], cycle) and _field(debt["case_serial"], case_serial) and _field(debt["state"], 4) and _field(debt["due_cycle_serial"], cycle + 1) and ((_field(debt["open"], True) and _field(debt["consumed"], False)) or (_field(debt["open"], False) and _field(debt["consumed"], True)))):
                    raise ValueError("route C debt lifecycle is inconsistent")

        if history_status == "empty":
            history_ready = history_count["status"] == "unavailable" and history_count["unavailable_reason"] == "variable_absent" and effective_count == 0 and all(_all_reason(slot, "lifecycle_not_reached") for slot in slots)
            count = 0
        elif history_status in {"partial", "three_cycle"} and _available(history_count):
            count = _value(history_count, "history.count")
            history_ready = isinstance(count, int) and 1 <= count <= 3 and effective_count == count and history_status == ("three_cycle" if count == 3 else "partial")
            previous = 0
            for index, slot in enumerate(slots):
                if index >= count:
                    history_ready = history_ready and _all_reason(slot, "lifecycle_not_reached")
                    continue
                if not _all_available(slot):
                    history_ready = False
                    continue
                cycle_value = _value(slot["cycle_serial"], "history.cycle")
                ids = [_value(slot[f"m{n}_receipt_id"], "receipt.id") for n in (357, 358, 359)]
                hashes = [_value(slot[f"m{n}_receipt_hash"], "receipt.hash") for n in (357, 358, 359)]
                history_ready = history_ready and _field(slot["owner_character_id"], owner) and cycle_value > previous and _value(slot["case_serial"], "history.case") > 0 and all(item > 0 for item in ids + hashes) and len(set(ids)) == 3 and len(set(hashes)) == 3
                previous = cycle_value
            if count == 3:
                tail = slots[2]
                history_ready = (
                    history_ready
                    and _field(tail["subject_character_id"], player)
                    and _field(tail["cycle_serial"], cycle)
                    and _field(tail["case_serial"], case_serial)
                )
        else:
            history_ready, count = False, -1
        if not history_ready or readiness["history_ledger_ready"] is not True or readiness["history_order_ready"] is not True or readiness["three_cycle_ready"] is not (count == 3):
            raise ValueError("rolling history count/order/receipt identity is inconsistent")

        evidence_keys = set(_CHARTER_SPEC) - {"portfolio_status", "portfolio_closed", "terminal_history_accruing", "portfolio_history_cycle_count", "terminal_success"}
        if charter_status in {"not_eligible", "awaiting_gate"}:
            expected_status = "awaiting_gate" if count == 3 else "not_eligible"
            header_absent = all(
                charter[key]["status"] == "unavailable"
                and charter[key]["unavailable_reason"] == "lifecycle_not_reached"
                for key in evidence_keys
            )
            deferred_header = (
                count == 3
                and all(_available(charter[key]) for key in evidence_keys)
                and _field(charter["evidence_count"], 3)
                and _field(charter["evidence_ready"], False)
                and _field(charter["evidence_consumed"], False)
                and _field(charter["owner_character_id"], owner)
                and _field(charter["subject_character_id"], player)
                and _field(charter["cycle_serial"], cycle)
                and _field(charter["case_serial"], case_serial)
                and _field(charter["state"], 5)
            )
            if charter_status != expected_status or not (header_absent or deferred_header):
                raise ValueError("charter pre-gate lifecycle is inconsistent")
        elif charter_status in {"ready", "consumed"}:
            if count != 3 or not all(_available(charter[key]) for key in evidence_keys):
                raise ValueError("charter gate lacks three-cycle evidence")
            charter_ok = (
                _field(charter["evidence_count"], 3)
                and _field(
                    charter["evidence_ready"], charter_status == "ready"
                )
                and _field(charter["evidence_consumed"], charter_status == "consumed")
                and _field(charter["owner_character_id"], owner) and _field(charter["subject_character_id"], player)
                and _field(charter["cycle_serial"], cycle) and _field(charter["case_serial"], case_serial) and _field(charter["state"], 5)
                and _value(charter["prepared_report_id"], "report") > 0 and _value(charter["prepared_charter_id"], "charter") > 0
                and _value(charter["previous_version"], "previous_version") >= 0
                and _field(charter["adopted_cycle_serial"], cycle) and _field(charter["effective_cycle_serial"], cycle + 1)
            )
            if not charter_ok:
                raise ValueError("charter lifecycle is inconsistent")
        else:
            raise ValueError("available frame cannot expose unavailable charter")
        expected_truth = {
            "player_subject_binding_ready": True, "owner_binding_ready": True,
            "case_identity_ready": True, "m360_receipt_projection_ready": True,
            "collective_lifecycle_ready": True, "cohort_identity_ready": True,
            "cohort_conservation_ready": True, "route_conservation_ready": True,
            "history_ledger_ready": True, "history_order_ready": True,
            "three_cycle_ready": count == 3, "charter_gate_lifecycle_ready": True,
            "same_frame_ready": True, "ready": True,
        }
        if readiness != expected_truth:
            raise ValueError("available readiness disagrees with decoded facts")
    else:
        raise ValueError("status must be available or unavailable")
    return {
        **frame, "al_case": case, "m360_receipt": receipt,
        "collective": {"phase": phase, **collective}, "cohorts": cohorts,
        "route_c_debt": debt,
        "history": {"status": history_status, "count": history_count, "effective_count": effective_count, "slots": slots},
        "charter_gate": {"status": charter_status, **charter},
        "readiness": readiness, "provenance": dict(provenance),
    }


def normalize_zhongguo_workforce_collective_snapshot_v1_response(
    value: object, *, expected_query: ZhongguoWorkforceCollectiveQueryV1,
    expected_snapshot_id: str, expected_revision: int,
    expected_native_revision: int, expected_connection_generation: int,
    expected_date_raw: int, expected_player_character_id: int,
) -> dict[str, object]:
    final = _exact(value, _FINAL_FRAME_KEYS, "zhongguo_workforce_collective_snapshot_response")
    snapshot_id = _bounded_text(expected_snapshot_id, "expected_snapshot_id", 256)
    revision = _integer(expected_revision, "expected_revision", 0, 2**64 - 1)
    native_revision = _integer(expected_native_revision, "expected_native_revision", 1, 2**64 - 1)
    generation = _integer(expected_connection_generation, "expected_connection_generation", 1, 2**64 - 1)
    player = _positive(expected_player_character_id, "expected_player_character_id")
    native = normalize_native_zhongguo_workforce_collective_snapshot_v1(
        {key: final[key] for key in _FRAME_KEYS}, expected_query=expected_query,
        expected_snapshot_revision=native_revision, expected_date_raw=expected_date_raw,
        expected_player_character_id=player,
    )
    build = _exact(final["build"], _BUILD_KEYS, "build")
    if build != {"version": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_VERSION, "exe_sha256": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_EXECUTABLE_SHA256}:
        raise ValueError("build does not match the frozen exact build")
    source = _exact(final["source"], _SOURCE_KEYS, "source")
    expected_source = {
        "bridge_version": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_BRIDGE_VERSION,
        "game_adapter_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_GAME_ADAPTER_ID,
        "backend_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_SOURCE_BACKEND_ID,
        "consumer_id": ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_CONSUMER_ID,
        "connection_generation": generation, "snapshot_id": snapshot_id,
        "revision": revision, "native_revision": native_revision,
        "date_raw": expected_date_raw, "paused": True,
        "player_character_id": player,
    }
    if source != expected_source:
        raise ValueError("source does not match the paused request binding")
    binding = _exact(final["binding"], _BINDING_KEYS, "binding")
    owner = expected_query.owner_character_id if native["status"] == "available" else None
    expected_binding = {
        "request_nonce": expected_query.request_nonce, "snapshot_id": snapshot_id,
        "revision": revision, "native_revision": native_revision,
        "connection_generation": generation, "date_raw": expected_date_raw,
        "paused": True, "player_character_id": player,
        "subject_character_id": player, "owner_character_id": owner,
        "expected_revision": revision,
    }
    if binding != expected_binding:
        raise ValueError("binding does not match the paused request/result")
    return {**native, "build": dict(build), "source": dict(source), "binding": dict(binding)}
