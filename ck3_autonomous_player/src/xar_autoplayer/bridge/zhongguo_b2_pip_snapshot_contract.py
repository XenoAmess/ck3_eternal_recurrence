"""Strict received-self ZhongGuo B2 PIP snapshot contract.

The public query binds the paused played character as the only subject.  The
owner argument is an equality filter.  The native provider exposes two fixed
allowlists and never accepts a character scope or variable name from callers.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-b2-pip-snapshot-v1"
)
QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-b2-pip-snapshot-v1"
)
QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_B2_PIP_CASE_KIND_V1: Final = "zhongguo.b2.pip"
ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_B2_PIP_SNAPSHOT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-b2-pip-snapshot-v1"
)
ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-b2-pip-snapshot-v1"
)
ZHONGGUO_B2_PIP_SNAPSHOT_V1_ALLOWLIST_ID: Final = (
    "zg361-b2-pip-received-self-v1"
)
ZHONGGUO_B2_PIP_SNAPSHOT_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_B2_PIP_SNAPSHOT_V1_SOURCE_BACKEND_ID: Final = "native-headless"

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS: Final = {"status", "value", "unavailable_reason"}
_GROUP_SPECS: Final[dict[str, dict[str, str]]] = {
    "gate": {
        "owner_character_id": "int",
        "subject_character_id": "int",
        "cycle_serial": "int",
        "case_serial": "int",
        "threshold": "int",
        "negative_component_count": "int",
        "evidence_complete": "bool",
        "status": "int",
        "result_case_serial": "int",
        "result_grade": "int",
        "absolute_grade": "int",
        "kpi_frozen_q100000": "int",
        "governance_q100000": "int",
        "capability_q100000": "int",
        "growth_q100000": "int",
        "superior_q100000": "int",
        "values_q100000": "int",
        "collaboration_q100000": "int",
        "jingcha_q100000": "int",
        "organization_q100000": "int",
    },
    "pip": {
        "owner_character_id": "int",
        "subject_character_id": "int",
        "cycle_serial": "int",
        "case_serial": "int",
        "state": "int",
        "task_kind": "int",
        "task_controllable": "bool",
        "policy_route": "int",
    },
    "response": {
        "subject_response": "int",
        "response_case_serial": "int",
        "response_author_character_id": "int",
        "acknowledgement_receipt_serial": "int",
        "goal_revision_used": "bool",
        "refusal_receipt_serial": "int",
    },
    "support": {
        "capacity_reserved": "bool",
        "owner_capacity_used": "int",
        "support_absent": "bool",
        "hours": "int",
        "attention_units": "int",
        "mentor_character_id": "int",
        "budget_owner_character_id": "int",
        "treasury_budget_allocated": "int",
        "treasury_budget_spent": "int",
        "support_receipt_serial": "int",
        "released": "bool",
        "withheld": "bool",
        "atomic_shortfall": "bool",
    },
    "budget_ledger": {
        "result_case_serial": "int",
        "treasury_penalty_paid": "int",
        "personal_gold_penalty_paid": "int",
        "support_treasury_allocated": "int",
        "support_treasury_spent": "int",
    },
    "d180_ticket": {
        "owner_character_id": "int",
        "subject_character_id": "int",
        "cycle_serial": "int",
        "case_serial": "int",
        "expected_state": "int",
        "due_date_raw": "int",
    },
    "d365_ticket": {
        "owner_character_id": "int",
        "subject_character_id": "int",
        "cycle_serial": "int",
        "case_serial": "int",
        "expected_state": "int",
        "due_date_raw": "int",
    },
    "midpoint": {
        "receipt_serial": "int",
        "resource_delivery_valid": "bool",
        "progress_status": "int",
        "progress_red_code": "int",
        "state": "int",
    },
    "outcome": {
        "code": "int",
        "settlement_receipt_serial": "int",
        "result_cycle_serial": "int",
        "result_case_serial": "int",
        "result_grade": "int",
        "stability_days_observed": "int",
        "independent_review_status": "int",
        "independent_review_red_code": "int",
        "graduation_receipt_serial": "int",
        "failure_receipt_serial": "int",
        "no_support_liability": "bool",
    },
    "next_cycle_evidence": {
        "status": "int",
        "owner_character_id": "int",
        "subject_character_id": "int",
        "source_cycle_serial": "int",
        "source_case_serial": "int",
        "due_cycle_serial": "int",
        "delta": "int",
        "consumed_cycle_serial": "int",
        "consumed_case_serial": "int",
    },
}
_READINESS_KEYS: Final = {
    "player_subject_binding_ready",
    "owner_binding_ready",
    "gate_ready",
    "gate_evidence_ready",
    "pip_identity_ready",
    "response_ready",
    "support_ready",
    "budget_ledger_ready",
    "midpoint_ready",
    "outcome_ready",
    "next_cycle_evidence_ready",
    "d180_ticket_observation_ready",
    "d365_ticket_observation_ready",
    "modifier_observation_ready",
    "same_frame_ready",
    "ready",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
    "executable_sha256": ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256,
    "backend_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_ALLOWLIST_ID,
    "variable_context_for_scope_rva": "0x3329A40",
    "variable_identifier_table_rva": "0x3B971A0",
    "variable_identifier_lookup_rva": "0x3B97020",
    "variable_identifier_name_rva": "0x3B97090",
    "character_storage_slot_rva": "0x570C130",
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
    *_GROUP_SPECS,
    "pip_modifier_present",
    "readiness",
    "unavailable_reason",
    "provenance",
}
_TOP_REASONS: Final = {
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
_FIELD_REASONS: Final = {
    "case_unavailable",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "case_binding_mismatch",
    "product_not_persisted",
    "native_observation_unavailable",
    "not_applicable",
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
    "subject_character_id",
    "owner_character_id",
    "expected_revision",
}
_FINAL_FRAME_KEYS: Final = _FRAME_KEYS | {"build", "source", "binding"}


@dataclass(frozen=True)
class ZhongguoB2PipQueryV1:
    owner_character_id: int
    request_nonce: str


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
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


def validate_b2_pip_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError("request_nonce must be 1-64 ASCII token characters")
    return value


def query_zhongguo_b2_pip_snapshot_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive_int32(owner_character_id, "owner_character_id")
    nonce = validate_b2_pip_request_nonce_v1(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_b2_pip_snapshot_v1_step(
    step: object,
) -> ZhongguoB2PipQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_B2_PIP_SNAPSHOT_V1_STEP_PREFIX
    ).split("-", 1)
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
        nonce = validate_b2_pip_request_nonce_v1(nonce)
        if nonce.encode("ascii").hex() != parts[1]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoB2PipQueryV1(owner, nonce)


def _typed(value: object, name: str, kind: str) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    status = field["status"]
    raw = field["value"]
    reason = field["unavailable_reason"]
    if status == "unavailable":
        if raw is not None or reason not in _FIELD_REASONS:
            raise ValueError(f"{name} has invalid typed unavailability")
    elif status == "available" and reason is None:
        if kind == "int":
            _integer(raw, name, -(2**63), 2**63 - 1)
        elif kind == "bool" and not isinstance(raw, bool):
            raise ValueError(f"{name}.value must be boolean")
    else:
        raise ValueError(f"{name} has invalid typed availability")
    return dict(field)


def _available(field: dict[str, object]) -> bool:
    return field["status"] == "available"


def _unavailable_for(field: dict[str, object], reason: str) -> bool:
    return (
        field["status"] == "unavailable"
        and field["unavailable_reason"] == reason
    )


def _value(field: dict[str, object], name: str) -> object:
    if not _available(field):
        raise ValueError(f"{name} must be available")
    return field["value"]


def _group(value: object, name: str) -> dict[str, object]:
    spec = _GROUP_SPECS[name]
    raw = _exact(value, set(spec), name)
    return {
        key: _typed(raw[key], f"{name}.{key}", kind)
        for key, kind in spec.items()
    }


def _all_available(group: dict[str, object], keys: set[str] | None = None) -> bool:
    selected = keys if keys is not None else set(group)
    return all(_available(group[key]) for key in selected)


def _integer_field_in_range(
    field: dict[str, object], minimum: int, maximum: int
) -> bool:
    value = field["value"]
    return (
        _available(field)
        and isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


def _field_equals(field: dict[str, object], expected: object) -> bool:
    return _available(field) and field["value"] == expected


def _bounded_text(value: object, name: str, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be non-empty text")
    if len(value.encode("utf-8")) > maximum_bytes or any(
        ord(character) < 0x20 for character in value
    ):
        raise ValueError(f"{name} is not bounded plain text")
    return value


def normalize_native_zhongguo_b2_pip_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoB2PipQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    expected_query = ZhongguoB2PipQueryV1(
        _positive_int32(expected_query.owner_character_id, "expected owner"),
        validate_b2_pip_request_nonce_v1(expected_query.request_nonce),
    )
    expected_snapshot_revision = _integer(
        expected_snapshot_revision, "expected_snapshot_revision", 1, 2**64 - 1
    )
    expected_date_raw = _integer(
        expected_date_raw, "expected_date_raw", -(2**31), 2**31 - 1
    )
    expected_player_character_id = _positive_int32(
        expected_player_character_id, "expected_player_character_id"
    )
    frame = _exact(value, _FRAME_KEYS, "zhongguo_b2_pip_snapshot")
    if frame["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if frame["case_kind"] != ZHONGGUO_B2_PIP_CASE_KIND_V1:
        raise ValueError("case_kind binding changed")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request_nonce binding changed")
    if _integer(frame["snapshot_revision"], "snapshot_revision", 1, 2**64 - 1) != expected_snapshot_revision:
        raise ValueError("snapshot revision binding changed")
    if _integer(frame["date_raw"], "date_raw", -(2**31), 2**31 - 1) != expected_date_raw:
        raise ValueError("date binding changed")
    if frame["paused"] is not True:
        raise ValueError("B2 PIP query is not paused")
    player = _positive_int32(frame["player_character_id"], "player_character_id")
    subject = _positive_int32(frame["subject_character_id"], "subject_character_id")
    if player != expected_player_character_id or subject != player:
        raise ValueError("received-self subject binding changed")
    if _positive_int32(frame["requested_owner_character_id"], "requested owner") != expected_query.owner_character_id:
        raise ValueError("owner filter binding changed")

    groups = {name: _group(frame[name], name) for name in _GROUP_SPECS}
    for group_name, field_name in (
        ("gate", "owner_character_id"),
        ("gate", "subject_character_id"),
        ("pip", "owner_character_id"),
        ("pip", "subject_character_id"),
        ("response", "response_author_character_id"),
        ("support", "mentor_character_id"),
        ("support", "budget_owner_character_id"),
        ("next_cycle_evidence", "owner_character_id"),
        ("next_cycle_evidence", "subject_character_id"),
    ):
        character_field = groups[group_name][field_name]
        if _available(character_field) and not _integer_field_in_range(
            character_field, 1, 2**31 - 1
        ):
            raise ValueError(
                f"{group_name}.{field_name} is not a valid character"
            )
    modifier = _typed(frame["pip_modifier_present"], "pip_modifier_present", "bool")
    readiness_raw = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    readiness: dict[str, bool] = {}
    for key in _READINESS_KEYS:
        if not isinstance(readiness_raw[key], bool):
            raise ValueError(f"readiness.{key} must be boolean")
        readiness[key] = readiness_raw[key]
    expected_ready = all(
        readiness[key]
        for key in (
            "player_subject_binding_ready",
            "owner_binding_ready",
            "gate_ready",
            "same_frame_ready",
        )
    )
    if readiness["ready"] is not expected_ready:
        raise ValueError("readiness.ready disagrees with the identity gate")
    provenance = _exact(frame["provenance"], set(_PROVENANCE_VALUES), "provenance")
    if any(provenance[key] != expected for key, expected in _PROVENANCE_VALUES.items()):
        raise ValueError("provenance does not match the frozen exact build")

    status = frame["status"]
    reason = frame["unavailable_reason"]
    if status == "unavailable":
        if reason not in _TOP_REASONS or readiness["ready"]:
            raise ValueError("unavailable frame has an invalid reason/gate")
        expected_same_frame = reason in {
            "case_not_found",
            "case_inconsistent",
            "owner_filter_mismatch",
            "not_received_self",
        }
        if readiness["same_frame_ready"] is not expected_same_frame or any(
            readiness[key]
            for key in _READINESS_KEYS - {"same_frame_ready"}
        ):
            raise ValueError(
                "unavailable frame fabricates component readiness"
            )
        for name, group in groups.items():
            if any(
                field["status"] != "unavailable"
                or field["unavailable_reason"] != "case_unavailable"
                for field in group.values()
            ):
                raise ValueError(f"unavailable frame leaks {name}")
        if modifier["unavailable_reason"] != "case_unavailable":
            raise ValueError("unavailable frame leaks modifier state")
    elif status == "available":
        if reason is not None:
            raise ValueError("available frame has an unavailable reason")
        gate = groups["gate"]
        gate_core = {
            "owner_character_id", "subject_character_id", "cycle_serial",
            "case_serial", "threshold", "negative_component_count",
            "evidence_complete", "status",
        }
        gate_ready = _all_available(gate, gate_core)
        if gate_ready:
            gate_complete = _value(
                gate["evidence_complete"], "gate.evidence_complete"
            )
            gate_status = _integer(
                _value(gate["status"], "gate.status"),
                "gate.status",
                0,
                3,
            )
            gate_ready = (
                _positive_int32(_value(gate["owner_character_id"], "gate.owner"), "gate.owner")
                == expected_query.owner_character_id
                and _positive_int32(_value(gate["subject_character_id"], "gate.subject"), "gate.subject") == player
                and _integer(_value(gate["cycle_serial"], "gate.cycle"), "gate.cycle", 1, 2**63 - 1) >= 1
                and 1 <= _integer(_value(gate["case_serial"], "gate.case"), "gate.case", 1, 999_999) <= 999_999
                and _value(gate["threshold"], "gate.threshold") == 3
                and 0 <= _integer(_value(gate["negative_component_count"], "gate.count"), "gate.count", 0, 10) <= 10
                and 0 <= gate_status <= 3
                and (
                    (gate_complete is True and gate_status != 0)
                    or (gate_complete is False and gate_status == 0)
                )
            )
        if readiness["gate_ready"] is not gate_ready:
            raise ValueError("gate readiness disagrees with frozen gate")
        pip = groups["pip"]
        any_pip = any(
            not _unavailable_for(field, "variable_absent")
            for field in pip.values()
        )
        pip_ready = gate_ready and _all_available(pip)
        if pip_ready:
            pip_ready = (
                _value(pip["owner_character_id"], "pip.owner") == expected_query.owner_character_id
                and _value(pip["subject_character_id"], "pip.subject") == player
                and 1 <= _integer(_value(pip["cycle_serial"], "pip.cycle"), "pip.cycle", 1, 2**63 - 2)
                and 1 <= _integer(_value(pip["case_serial"], "pip.case"), "pip.case", 1, 999_999) <= 999_999
                and _field_equals(
                    pip["cycle_serial"], gate["cycle_serial"]["value"]
                )
                and _field_equals(
                    pip["case_serial"], gate["case_serial"]["value"]
                )
                and 1 <= _integer(_value(pip["state"], "pip.state"), "pip.state", 1, 5) <= 5
                and 1 <= _integer(_value(pip["task_kind"], "pip.task_kind"), "pip.task_kind", 1, 3) <= 3
                and 1 <= _integer(_value(pip["policy_route"], "pip.policy_route"), "pip.policy_route", 1, 2) <= 2
            )
        if readiness["pip_identity_ready"] is not pip_ready:
            raise ValueError("PIP identity readiness disagrees with fields")
        if any_pip and not pip_ready:
            raise ValueError("available frame contains an inconsistent PIP")
        player_binding_ready = (
            _field_equals(gate["subject_character_id"], player)
            and (
                not any_pip
                or _field_equals(pip["subject_character_id"], player)
            )
        )
        owner_binding_ready = (
            _field_equals(
                gate["owner_character_id"], expected_query.owner_character_id
            )
            and (
                not any_pip
                or _field_equals(
                    pip["owner_character_id"],
                    expected_query.owner_character_id,
                )
            )
        )
        if (
            readiness["player_subject_binding_ready"]
            is not player_binding_ready
            or readiness["owner_binding_ready"] is not owner_binding_ready
            or not player_binding_ready
            or not owner_binding_ready
            or readiness["same_frame_ready"] is not True
        ):
            raise ValueError(
                "available frame lacks its same-frame subject/owner binding"
            )

        evidence_names = (
            "governance_q100000",
            "capability_q100000",
            "growth_q100000",
            "superior_q100000",
            "values_q100000",
            "collaboration_q100000",
            "jingcha_q100000",
            "organization_q100000",
        )
        gate_evidence_ready = gate_ready and _all_available(
            gate,
            {
                "result_case_serial",
                "result_grade",
                "absolute_grade",
                "kpi_frozen_q100000",
                *evidence_names,
            },
        )
        if gate_evidence_ready:
            negative_count = int(
                _value(gate["absolute_grade"], "gate.absolute_grade") == 1
            )
            negative_count += int(
                _value(gate["kpi_frozen_q100000"], "gate.kpi") < 0
            )
            negative_count += sum(
                int(_value(gate[name], f"gate.{name}") < 0)
                for name in evidence_names
            )
            gate_evidence_ready = (
                _value(gate["evidence_complete"], "gate.evidence_complete")
                is True
                and _field_equals(
                    gate["result_case_serial"], gate["case_serial"]["value"]
                )
                and _integer_field_in_range(gate["result_grade"], 1, 3)
                and _integer_field_in_range(gate["absolute_grade"], 1, 3)
                and _field_equals(
                    gate["negative_component_count"], negative_count
                )
            )
        if readiness["gate_evidence_ready"] is not gate_evidence_ready:
            raise ValueError(
                "gate evidence readiness disagrees with frozen evidence"
            )

        response = groups["response"]
        response_ready = False
        if pip_ready:
            pip_case = pip["case_serial"]["value"]
            pip_state = pip["state"]["value"]
            response_code = response["subject_response"]["value"]
            pending = (
                pip_state == 1
                and response_code == 0
                and _field_equals(response["response_case_serial"], 0)
                and _unavailable_for(
                    response["response_author_character_id"],
                    "variable_absent",
                )
                and _field_equals(response["refusal_receipt_serial"], 0)
            )
            accepted = (
                pip_state in (2, 3, 4)
                and response_code in (1, 2)
                and _field_equals(response["response_case_serial"], pip_case)
                and _field_equals(
                    response["response_author_character_id"], player
                )
                and _field_equals(response["refusal_receipt_serial"], 0)
            )
            refused = (
                pip_state == 5
                and response_code == 3
                and _field_equals(response["response_case_serial"], pip_case)
                and _field_equals(
                    response["response_author_character_id"], player
                )
                and _field_equals(
                    response["refusal_receipt_serial"], pip_case
                )
            )
            response_ready = (
                _field_equals(
                    response["acknowledgement_receipt_serial"], pip_case
                )
                and _available(response["goal_revision_used"])
                and (pending or accepted or refused)
            )
        if readiness["response_ready"] is not response_ready:
            raise ValueError("response readiness disagrees with PIP receipt")

        support = groups["support"]
        support_ready = False
        if pip_ready:
            reserved = support["capacity_reserved"]["value"]
            absent = support["support_absent"]["value"]
            core_support = (
                _available(support["capacity_reserved"])
                and _available(support["support_absent"])
                and _integer_field_in_range(support["hours"], 0, 12)
                and _integer_field_in_range(
                    support["attention_units"], 0, 1
                )
                and _integer_field_in_range(
                    support["treasury_budget_allocated"], 0, 25
                )
                and _integer_field_in_range(
                    support["treasury_budget_spent"], 0, 25
                )
                and _field_equals(
                    support["support_receipt_serial"],
                    pip["case_serial"]["value"],
                )
            )
            reserved_package = (
                pip["state"]["value"] == 2
                and reserved is True
                and absent is False
                and _field_equals(support["hours"], 12)
                and _field_equals(support["attention_units"], 1)
                and _integer_field_in_range(
                    support["mentor_character_id"], 1, 2**31 - 1
                )
                and _field_equals(
                    support["budget_owner_character_id"],
                    expected_query.owner_character_id,
                )
                and _field_equals(support["treasury_budget_allocated"], 25)
                and _field_equals(support["treasury_budget_spent"], 25)
                and _integer_field_in_range(
                    support["owner_capacity_used"], 1, 2
                )
                and (
                    _unavailable_for(support["released"], "variable_absent")
                    or _field_equals(support["released"], False)
                )
                and (
                    _unavailable_for(support["withheld"], "variable_absent")
                    or _field_equals(support["withheld"], False)
                )
                and (
                    _unavailable_for(
                        support["atomic_shortfall"], "variable_absent"
                    )
                    or _field_equals(support["atomic_shortfall"], False)
                )
            )
            absent_package = (
                pip["state"]["value"] == 2
                and reserved is False
                and absent is True
                and _field_equals(support["hours"], 0)
                and _field_equals(support["attention_units"], 0)
                and _field_equals(support["treasury_budget_allocated"], 0)
                and _field_equals(support["treasury_budget_spent"], 0)
                and (
                    _unavailable_for(support["released"], "variable_absent")
                    or _field_equals(support["released"], False)
                )
                and (
                    (
                        pip["policy_route"]["value"] == 1
                        and (
                            _unavailable_for(
                                support["withheld"], "variable_absent"
                            )
                            or _field_equals(support["withheld"], False)
                        )
                        and _field_equals(
                            support["atomic_shortfall"], True
                        )
                    )
                    or (
                        pip["policy_route"]["value"] == 2
                        and _field_equals(support["withheld"], True)
                        and (
                            _unavailable_for(
                                support["atomic_shortfall"],
                                "variable_absent",
                            )
                            or _field_equals(
                                support["atomic_shortfall"], False
                            )
                        )
                    )
                )
            )
            support_ready = core_support and (
                reserved_package or absent_package
            )
        if readiness["support_ready"] is not support_ready:
            raise ValueError("support readiness disagrees with package ledger")

        ledger = groups["budget_ledger"]
        budget_ledger_ready = (
            pip_ready
            and _field_equals(
                ledger["result_case_serial"], pip["case_serial"]["value"]
            )
            and _integer_field_in_range(
                ledger["treasury_penalty_paid"], 0, 2**63 - 1
            )
            and _integer_field_in_range(
                ledger["personal_gold_penalty_paid"], 0, 2**63 - 1
            )
            and _integer_field_in_range(
                ledger["support_treasury_allocated"], 0, 25
            )
            and _integer_field_in_range(
                ledger["support_treasury_spent"], 0, 25
            )
        )
        if readiness["budget_ledger_ready"] is not budget_ledger_ready:
            raise ValueError("budget readiness disagrees with penalty ledger")

        for ticket_name in ("d180_ticket", "d365_ticket"):
            ticket = groups[ticket_name]
            for key, field in ticket.items():
                expected_reason = "product_not_persisted" if key == "due_date_raw" else "native_observation_unavailable"
                if field["status"] != "unavailable" or field["unavailable_reason"] != expected_reason:
                    raise ValueError(f"{ticket_name}.{key} must remain typed unavailable")
        if (
            readiness["d180_ticket_observation_ready"]
            or readiness["d365_ticket_observation_ready"]
            or readiness["modifier_observation_ready"]
            or modifier["status"] != "unavailable"
            or modifier["unavailable_reason"] != "native_observation_unavailable"
        ):
            raise ValueError("unimplemented ticket/modifier observation was fabricated")

        midpoint = groups["midpoint"]
        midpoint_ready = (
            pip_ready
            and _field_equals(
                midpoint["receipt_serial"], pip["case_serial"]["value"]
            )
            and _available(midpoint["resource_delivery_valid"])
            and _field_equals(midpoint["progress_status"], 0)
            and _field_equals(midpoint["progress_red_code"], 1)
            and _field_equals(midpoint["state"], 2)
        )
        if readiness["midpoint_ready"] is not midpoint_ready:
            raise ValueError("midpoint readiness disagrees with receipt")

        outcome = groups["outcome"]
        outcome_ready = False
        if pip_ready and pip["state"]["value"] in (3, 4):
            pip_case = pip["case_serial"]["value"]
            graduated = (
                pip["state"]["value"] == 3
                and _field_equals(outcome["code"], 1)
                and _field_equals(
                    outcome["graduation_receipt_serial"], pip_case
                )
                and (
                    _field_equals(outcome["failure_receipt_serial"], 0)
                    or _unavailable_for(
                        outcome["failure_receipt_serial"], "variable_absent"
                    )
                )
            )
            failed = (
                pip["state"]["value"] == 4
                and _field_equals(outcome["code"], 2)
                and _field_equals(outcome["failure_receipt_serial"], pip_case)
                and (
                    _field_equals(outcome["graduation_receipt_serial"], 0)
                    or _unavailable_for(
                        outcome["graduation_receipt_serial"],
                        "variable_absent",
                    )
                )
            )
            outcome_ready = (
                _field_equals(outcome["settlement_receipt_serial"], pip_case)
                and _integer_field_in_range(
                    outcome["result_cycle_serial"], 1, 2**63 - 1
                )
                and _integer_field_in_range(
                    outcome["result_case_serial"], 1, 999_999
                )
                and _integer_field_in_range(outcome["result_grade"], 1, 3)
                and _field_equals(outcome["stability_days_observed"], 365)
                and _field_equals(outcome["independent_review_status"], 0)
                and _field_equals(outcome["independent_review_red_code"], 2)
                and (graduated or failed)
            )
        if readiness["outcome_ready"] is not outcome_ready:
            raise ValueError("outcome readiness disagrees with settlement")

        evidence = groups["next_cycle_evidence"]
        next_cycle_evidence_ready = False
        if pip_ready and _integer_field_in_range(evidence["status"], 1, 2):
            pip_cycle = pip["cycle_serial"]["value"]
            pip_case = pip["case_serial"]["value"]
            base = (
                _field_equals(
                    evidence["owner_character_id"],
                    expected_query.owner_character_id,
                )
                and _field_equals(evidence["subject_character_id"], player)
                and _field_equals(evidence["source_cycle_serial"], pip_cycle)
                and _field_equals(evidence["source_case_serial"], pip_case)
                and _field_equals(evidence["due_cycle_serial"], pip_cycle + 1)
                and evidence["delta"]["value"] in (10, -10, -15)
                and _available(evidence["delta"])
            )
            pending_evidence = (
                evidence["status"]["value"] == 1
                and _unavailable_for(
                    evidence["consumed_cycle_serial"], "variable_absent"
                )
                and _unavailable_for(
                    evidence["consumed_case_serial"], "variable_absent"
                )
            )
            consumed_evidence = (
                evidence["status"]["value"] == 2
                and _integer_field_in_range(
                    evidence["consumed_cycle_serial"],
                    evidence["due_cycle_serial"]["value"],
                    2**63 - 1,
                )
                and _field_equals(
                    evidence["consumed_case_serial"], pip_case
                )
            )
            next_cycle_evidence_ready = base and (
                pending_evidence or consumed_evidence
            )
        if (
            readiness["next_cycle_evidence_ready"]
            is not next_cycle_evidence_ready
        ):
            raise ValueError(
                "next-cycle evidence readiness disagrees with receipt"
            )
    else:
        raise ValueError("status must be available or unavailable")
    return {
        **frame,
        **groups,
        "pip_modifier_present": modifier,
        "readiness": readiness,
        "provenance": dict(provenance),
    }


def normalize_zhongguo_b2_pip_snapshot_v1_response(
    value: object,
    *,
    expected_query: ZhongguoB2PipQueryV1,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    final = _exact(value, _FINAL_FRAME_KEYS, "zhongguo_b2_pip_snapshot_response")
    expected_snapshot_id = _bounded_text(expected_snapshot_id, "expected_snapshot_id", 256)
    expected_revision = _integer(expected_revision, "expected_revision", 0, 2**64 - 1)
    expected_native_revision = _integer(expected_native_revision, "expected_native_revision", 1, 2**64 - 1)
    expected_connection_generation = _integer(expected_connection_generation, "expected_connection_generation", 1, 2**64 - 1)
    expected_date_raw = _integer(expected_date_raw, "expected_date_raw", -(2**31), 2**31 - 1)
    expected_player_character_id = _positive_int32(expected_player_character_id, "expected_player_character_id")
    native = normalize_native_zhongguo_b2_pip_snapshot_v1(
        {key: final[key] for key in _FRAME_KEYS},
        expected_query=expected_query,
        expected_snapshot_revision=expected_native_revision,
        expected_date_raw=expected_date_raw,
        expected_player_character_id=expected_player_character_id,
    )
    build = _exact(final["build"], _BUILD_KEYS, "build")
    if build != {
        "version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_VERSION,
        "exe_sha256": ZHONGGUO_B2_PIP_SNAPSHOT_V1_EXECUTABLE_SHA256,
    }:
        raise ValueError("build does not match the frozen exact build")
    source = _exact(final["source"], _SOURCE_KEYS, "source")
    if source != {
        "bridge_version": ZHONGGUO_B2_PIP_SNAPSHOT_V1_BRIDGE_VERSION,
        "game_adapter_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_GAME_ADAPTER_ID,
        "backend_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_SOURCE_BACKEND_ID,
        "consumer_id": ZHONGGUO_B2_PIP_SNAPSHOT_V1_CONSUMER_ID,
        "connection_generation": expected_connection_generation,
        "snapshot_id": expected_snapshot_id,
        "revision": expected_revision,
        "native_revision": expected_native_revision,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
    }:
        raise ValueError("source does not match the paused request binding")
    owner: int | None = None
    if native["status"] == "available":
        owner = _positive_int32(
            _value(native["gate"]["owner_character_id"], "gate.owner"),
            "gate.owner",
        )
    binding = _exact(final["binding"], _BINDING_KEYS, "binding")
    if binding != {
        "request_nonce": expected_query.request_nonce,
        "snapshot_id": expected_snapshot_id,
        "revision": expected_revision,
        "native_revision": expected_native_revision,
        "connection_generation": expected_connection_generation,
        "date_raw": expected_date_raw,
        "paused": True,
        "player_character_id": expected_player_character_id,
        "subject_character_id": expected_player_character_id,
        "owner_character_id": owner,
        "expected_revision": expected_revision,
    }:
        raise ValueError("binding does not match the paused request/result")
    return {**native, "build": dict(build), "source": dict(source), "binding": dict(binding)}
