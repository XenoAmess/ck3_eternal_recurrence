"""Strict received-self ZhongGuo incident terminal snapshot contract.

The paused played character is the only readable subject.  ``profile`` selects
one of three provider-owned fixed allowlists (X/Y/Z); it is never interpolated
into an arbitrary engine variable name.  ``owner_character_id`` is only an
equality filter over the owner target frozen on the played character.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-incident-snapshot-v1"
)
QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP: Final = (
    "query-zhongguo-incident-snapshot-v1"
)
QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP}-"
)
ZHONGGUO_INCIDENT_KIND_V1: Final = "zhongguo.incident.subject-self"
ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION: Final = "1.19.0.6"
ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
ZHONGGUO_INCIDENT_SNAPSHOT_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-incident-snapshot-v1"
)
ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID: Final = (
    "xar-autoplayer-zhongguo-incident-snapshot-v1"
)
ZHONGGUO_INCIDENT_SNAPSHOT_V1_ALLOWLIST_ID: Final = (
    "zg361-incident-terminal-x-y-z-v1"
)
ZHONGGUO_INCIDENT_SNAPSHOT_V1_BRIDGE_VERSION: Final = "0.1.0"
ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_ADAPTER_ID: Final = (
    "ck3-1.19.0.6-msvc-x64"
)
ZHONGGUO_INCIDENT_SNAPSHOT_V1_SOURCE_BACKEND_ID: Final = "native-headless"

_PROFILES: Final = frozenset({"x", "y", "z"})
_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS: Final = {"status", "value", "unavailable_reason"}
_PROBE_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "probe_serial",
    "result",
    "source_kind",
    "consequence_kind",
}
_RESOURCE_KEYS: Final = {
    "subject_personal_gold_q100000",
    "manager_treasury_q100000",
    "capital_control_q100000",
}
_NA_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "reason",
    "probe_serial",
    "receipt_serial",
    "applicable",
    "kpi_staged",
}
_INCIDENT_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
    "state",
    "revision",
    "incident_serial",
    "source_kind",
    "consequence_kind",
    "final_score",
    "applicable",
    "kpi_staged",
}
_TERMINAL_KEYS: Final = {"kind", "na", "incident"}
_KPI_VALUE_KEYS: Final = {
    "pending",
    "consumed",
    "owner_character_id",
    "subject_character_id",
    "origin_cycle",
    "due_cycle",
    "due_offset",
    "case_serial",
    "state",
    "score",
    "incident_serial",
    "source_kind",
    "consequence_kind",
    "receipt_serial",
    "consumed_owner_character_id",
    "consumed_subject_character_id",
    "consumed_origin_cycle",
    "consumed_due_cycle",
    "consumed_cycle",
    "consumed_case_serial",
    "consumed_score",
    "consumed_incident_serial",
}
_KPI_KEYS: Final = _KPI_VALUE_KEYS | {"disposition"}
_READINESS_KEYS: Final = {
    "player_subject_binding_ready",
    "owner_binding_ready",
    "profile_binding_ready",
    "probe_ready",
    "terminal_ready",
    "resource_snapshot_ready",
    "kpi_state_ready",
    "same_frame_ready",
    "ready",
}
_PROVENANCE_VALUES: Final = {
    "game_version": ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION,
    "executable_sha256": ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256,
    "backend_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_BACKEND_ID,
    "consumer_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID,
    "allowlist_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_ALLOWLIST_ID,
    "variable_context_for_scope_rva": "0x3329A40",
    "variable_identifier_table_rva": "0x3B971A0",
    "variable_identifier_lookup_rva": "0x3B97020",
    "variable_identifier_name_rva": "0x3B97090",
    "character_storage_slot_rva": "0x570C130",
    "manager_treasury_source": "not_recorded_by_mod",
}
_FRAME_KEYS: Final = {
    "schema_version",
    "status",
    "case_kind",
    "profile",
    "request_nonce",
    "snapshot_revision",
    "date_raw",
    "paused",
    "player_character_id",
    "subject_character_id",
    "requested_owner_character_id",
    "probe",
    "resources",
    "terminal",
    "kpi",
    "readiness",
    "unavailable_reason",
    "provenance",
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
    "profile",
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
_TOP_REASONS: Final = {
    "unsupported_build",
    "requires_application_main",
    "requires_paused",
    "map_not_ready",
    "incident_not_found",
    "incident_inconsistent",
    "owner_filter_mismatch",
    "not_received_self",
    "variable_identifier_unavailable",
    "variable_context_unavailable",
    "state_changed",
    "internal_error",
}
_FIELD_REASONS: Final = {
    "snapshot_unavailable",
    "variable_absent",
    "value_type_mismatch",
    "value_out_of_range",
    "not_recorded_by_mod",
    "terminal_not_selected",
    "not_applicable",
    "kpi_not_staged",
    "not_yet_consumed",
}
_SOURCE_CONSEQUENCE: Final = {(1, 1), (3, 2), (4, 2), (5, 3)}


@dataclass(frozen=True)
class ZhongguoIncidentQueryV1:
    owner_character_id: int
    profile: str
    request_nonce: str


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
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


def _positive_int32(value: object, name: str) -> int:
    return _integer(value, name, minimum=1, maximum=2**31 - 1)


def _bounded_text(value: object, name: str, *, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    encoded = value.encode("utf-8")
    if len(encoded) > maximum_bytes or any(ord(char) < 0x20 for char in value):
        raise ValueError(f"{name} must be bounded text without controls")
    return value


def validate_incident_request_nonce_v1(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError("request_nonce must be 1-64 ASCII token characters")
    return value


def validate_incident_profile_v1(value: object) -> str:
    if not isinstance(value, str) or value not in _PROFILES:
        raise ValueError("profile must be exactly x, y, or z")
    return value


def query_zhongguo_incident_snapshot_v1_step(
    owner_character_id: object,
    profile: object,
    request_nonce: object,
) -> str:
    owner = _positive_int32(owner_character_id, "owner_character_id")
    profile = validate_incident_profile_v1(profile)
    nonce = validate_incident_request_nonce_v1(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP_PREFIX}"
        f"{owner}-{profile}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_incident_snapshot_v1_step(
    step: object,
) -> ZhongguoIncidentQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP_PREFIX
    ):
        return None
    tail = step.removeprefix(QUERY_ZHONGGUO_INCIDENT_SNAPSHOT_V1_STEP_PREFIX)
    parts = tail.split("-", 2)
    if len(parts) != 3:
        return None
    try:
        owner = int(parts[0], 10)
        if str(owner) != parts[0]:
            return None
        owner = _positive_int32(owner, "owner_character_id")
        profile = validate_incident_profile_v1(parts[1])
        if not parts[2] or len(parts[2]) % 2:
            return None
        nonce = bytes.fromhex(parts[2]).decode("ascii")
        nonce = validate_incident_request_nonce_v1(nonce)
        if nonce.encode("ascii").hex() != parts[2]:
            return None
    except (UnicodeDecodeError, ValueError):
        return None
    return ZhongguoIncidentQueryV1(owner, profile, nonce)


def _typed(value: object, name: str) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    status = field["status"]
    raw = field["value"]
    reason = field["unavailable_reason"]
    if status == "unavailable":
        if raw is not None or reason not in _FIELD_REASONS:
            raise ValueError(f"{name} has an invalid unavailable value")
    elif status == "available":
        if reason is not None:
            raise ValueError(f"{name} available value has a reason")
        _integer(raw, name, minimum=-(2**63), maximum=2**63 - 1)
    else:
        raise ValueError(f"{name} has an invalid status")
    return dict(field)


def _typed_group(
    value: object, keys: set[str], name: str
) -> dict[str, dict[str, object]]:
    group = _exact(value, keys, name)
    return {key: _typed(group[key], f"{name}.{key}") for key in keys}


def _available(field: dict[str, object]) -> bool:
    return field["status"] == "available"


def _value(field: dict[str, object], name: str) -> int:
    if not _available(field):
        raise ValueError(f"{name} must be available")
    return _integer(
        field["value"], name, minimum=-(2**63), maximum=2**63 - 1
    )


def _all_available(group: dict[str, dict[str, object]]) -> bool:
    return all(_available(field) for field in group.values())


def _all_unavailable(group: dict[str, dict[str, object]]) -> bool:
    return all(not _available(field) for field in group.values())


def _validate_kpi(
    kpi: dict[str, object],
    *,
    terminal_kind: str,
    incident: dict[str, dict[str, object]] | None,
) -> bool:
    disposition = kpi["disposition"]
    values = {key: kpi[key] for key in _KPI_VALUE_KEYS}
    assert all(isinstance(field, dict) for field in values.values())
    typed_values = values  # type: ignore[assignment]
    if terminal_kind == "na":
        if disposition != "not_staged" or not _all_unavailable(typed_values):
            raise ValueError("N/A must have an exact not-staged KPI tuple")
        return True
    if disposition == "unavailable":
        if not _all_unavailable(typed_values):
            raise ValueError("unavailable KPI disposition leaks values")
        return False
    if disposition not in {"pending", "consumed"} or incident is None:
        raise ValueError("incident KPI disposition is invalid")
    base = {
        key
        for key in _KPI_VALUE_KEYS
        if not key.startswith("consumed_") and key != "receipt_serial"
    }
    if not all(_available(typed_values[key]) for key in base):
        raise ValueError("staged KPI base tuple is incomplete")
    iv = {key: _value(field, f"incident.{key}") for key, field in incident.items()}
    kv = {key: _value(typed_values[key], f"kpi.{key}") for key in base}
    if (
        kv["owner_character_id"] != iv["owner_character_id"]
        or kv["subject_character_id"] != iv["subject_character_id"]
        or kv["origin_cycle"] != iv["cycle_serial"]
        or kv["due_cycle"] != kv["origin_cycle"] + 1
        or kv["due_offset"] != 1
        or kv["case_serial"] != iv["case_serial"]
        or kv["state"] != iv["state"]
        or kv["score"] != iv["final_score"]
        or kv["incident_serial"] != iv["incident_serial"]
        or kv["source_kind"] != iv["source_kind"]
        or kv["consequence_kind"] != iv["consequence_kind"]
    ):
        raise ValueError("KPI tuple does not join the incident terminal")
    receipt = _KPI_VALUE_KEYS - base
    if disposition == "pending":
        if kv["pending"] != 1 or kv["consumed"] != 0:
            raise ValueError("pending KPI bits are invalid")
        if not all(not _available(typed_values[key]) for key in receipt):
            raise ValueError("pending KPI leaks a consumed receipt")
        return True
    if kv["pending"] != 0 or kv["consumed"] != 1:
        raise ValueError("consumed KPI bits are invalid")
    if not all(_available(typed_values[key]) for key in receipt):
        raise ValueError("consumed KPI receipt is incomplete")
    rv = {key: _value(typed_values[key], f"kpi.{key}") for key in receipt}
    if (
        rv["receipt_serial"] < 1
        or rv["consumed_owner_character_id"] != kv["owner_character_id"]
        or rv["consumed_subject_character_id"] != kv["subject_character_id"]
        or rv["consumed_origin_cycle"] != kv["origin_cycle"]
        or rv["consumed_due_cycle"] != kv["due_cycle"]
        or rv["consumed_cycle"] < kv["due_cycle"]
        or rv["consumed_case_serial"] != kv["case_serial"]
        or rv["consumed_score"] != kv["score"]
        or rv["consumed_incident_serial"] != kv["incident_serial"]
    ):
        raise ValueError("consumed KPI receipt does not join its tuple")
    return True


def normalize_native_zhongguo_incident_snapshot_v1(
    value: object,
    *,
    expected_query: ZhongguoIncidentQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    expected_query = ZhongguoIncidentQueryV1(
        _positive_int32(expected_query.owner_character_id, "expected owner"),
        validate_incident_profile_v1(expected_query.profile),
        validate_incident_request_nonce_v1(expected_query.request_nonce),
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
    frame = _exact(value, _FRAME_KEYS, "zhongguo_incident_snapshot")
    if frame["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if frame["case_kind"] != ZHONGGUO_INCIDENT_KIND_V1:
        raise ValueError("case kind binding changed")
    if frame["profile"] != expected_query.profile:
        raise ValueError("profile binding changed")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("nonce binding changed")
    if _integer(
        frame["snapshot_revision"],
        "snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    ) != expected_snapshot_revision:
        raise ValueError("snapshot revision binding changed")
    if _integer(
        frame["date_raw"],
        "date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    ) != expected_date_raw:
        raise ValueError("date binding changed")
    if frame["paused"] is not True:
        raise ValueError("incident query is not paused")
    player = _positive_int32(frame["player_character_id"], "player")
    subject = _positive_int32(frame["subject_character_id"], "subject")
    owner = _positive_int32(frame["requested_owner_character_id"], "owner")
    if player != expected_player_character_id or subject != player:
        raise ValueError("played-character subject binding changed")
    if owner != expected_query.owner_character_id or owner == player:
        raise ValueError("owner filter binding changed")

    probe = _typed_group(frame["probe"], _PROBE_KEYS, "probe")
    resources = _typed_group(frame["resources"], _RESOURCE_KEYS, "resources")
    terminal = _exact(frame["terminal"], _TERMINAL_KEYS, "terminal")
    kpi_raw = _exact(frame["kpi"], _KPI_KEYS, "kpi")
    kpi: dict[str, object] = {"disposition": kpi_raw["disposition"]}
    kpi.update(
        {key: _typed(kpi_raw[key], f"kpi.{key}") for key in _KPI_VALUE_KEYS}
    )
    readiness_raw = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    readiness: dict[str, bool] = {}
    for key in _READINESS_KEYS:
        flag = readiness_raw[key]
        if not isinstance(flag, bool):
            raise ValueError(f"readiness.{key} must be boolean")
        readiness[key] = flag
    expected_ready = all(
        readiness[key] for key in _READINESS_KEYS if key != "ready"
    )
    if readiness["ready"] is not expected_ready:
        raise ValueError("readiness.ready disagrees with component gates")
    provenance = _exact(
        frame["provenance"], set(_PROVENANCE_VALUES), "provenance"
    )
    if provenance != _PROVENANCE_VALUES:
        raise ValueError("provenance does not match the frozen build")

    status = frame["status"]
    reason = frame["unavailable_reason"]
    if status == "unavailable":
        if reason not in _TOP_REASONS or readiness["ready"]:
            raise ValueError("unavailable frame has an invalid reason")
        if terminal != {"kind": "unavailable", "na": None, "incident": None}:
            raise ValueError("unavailable frame exposes a terminal")
        if not _all_unavailable(probe) or not _all_unavailable(resources):
            raise ValueError("unavailable frame leaks probe/resources")
        if kpi["disposition"] != "unavailable" or not _all_unavailable(
            {key: kpi[key] for key in _KPI_VALUE_KEYS}  # type: ignore[misc]
        ):
            raise ValueError("unavailable frame leaks KPI state")
        return {
            **frame,
            "probe": probe,
            "resources": resources,
            "kpi": kpi,
            "readiness": readiness,
        }
    if status != "available" or reason is not None:
        raise ValueError("status must be typed available or unavailable")
    if not _all_available(probe):
        raise ValueError("available frame has an incomplete probe")
    pv = {key: _value(field, f"probe.{key}") for key, field in probe.items()}
    if (
        pv["owner_character_id"] != owner
        or pv["subject_character_id"] != player
        or pv["cycle_serial"] < 1
        or pv["probe_serial"] < 1
        or pv["result"] not in {0, 1}
    ):
        raise ValueError("probe identity is invalid")
    if readiness["probe_ready"] is not True:
        raise ValueError("available probe is not marked ready")
    if not readiness["player_subject_binding_ready"] or not readiness[
        "owner_binding_ready"
    ]:
        raise ValueError("available frame lacks owner/subject binding")
    if not readiness["profile_binding_ready"] or not readiness[
        "same_frame_ready"
    ]:
        raise ValueError("available frame lacks profile/same-frame binding")

    resource_ready = _all_available(resources)
    if readiness["resource_snapshot_ready"] is not resource_ready:
        raise ValueError("resource readiness disagrees with typed resources")
    # Current producer gap is explicit.  A future mod producer must update the
    # provenance and contract; this field can never silently become zero.
    manager = resources["manager_treasury_q100000"]
    if _available(manager):
        raise ValueError(
            "manager treasury cannot be available under not-recorded provenance"
        )
    if manager["unavailable_reason"] != "not_recorded_by_mod":
        raise ValueError("manager treasury gap is not explicitly typed")

    kind = terminal["kind"]
    na: dict[str, dict[str, object]] | None = None
    incident: dict[str, dict[str, object]] | None = None
    if kind == "na":
        if terminal["incident"] is not None:
            raise ValueError("N/A union contains an incident arm")
        na = _typed_group(terminal["na"], _NA_KEYS, "terminal.na")
        if not _all_available(na):
            raise ValueError("N/A tuple is incomplete")
        nv = {key: _value(field, f"terminal.na.{key}") for key, field in na.items()}
        if (
            pv["result"] != 0
            or pv["source_kind"] != 0
            or pv["consequence_kind"] != 0
            or nv["owner_character_id"] != owner
            or nv["subject_character_id"] != player
            or nv["cycle_serial"] != pv["cycle_serial"]
            or nv["probe_serial"] != pv["probe_serial"]
            or nv["reason"] != 1
            or nv["receipt_serial"] < 1
            or nv["applicable"] != 0
            or nv["kpi_staged"] != 0
        ):
            raise ValueError("N/A tuple is not an exact positive receipt")
    elif kind == "incident":
        if terminal["na"] is not None:
            raise ValueError("incident union contains an N/A arm")
        incident = _typed_group(
            terminal["incident"], _INCIDENT_KEYS, "terminal.incident"
        )
        if not _all_available(incident):
            raise ValueError("incident terminal tuple is incomplete")
        iv = {
            key: _value(field, f"terminal.incident.{key}")
            for key, field in incident.items()
        }
        expected_state = 8 if expected_query.profile == "x" else 6
        if (
            pv["result"] != 1
            or (pv["source_kind"], pv["consequence_kind"])
            not in _SOURCE_CONSEQUENCE
            or iv["owner_character_id"] != owner
            or iv["subject_character_id"] != player
            or iv["cycle_serial"] != pv["cycle_serial"]
            or not 1 <= iv["case_serial"] <= 999_999
            or iv["state"] != expected_state
            or iv["revision"] < 1
            or iv["incident_serial"] < 1
            or iv["source_kind"] != pv["source_kind"]
            or iv["consequence_kind"] != pv["consequence_kind"]
            or not -4 <= iv["final_score"] <= 4
            or iv["applicable"] != 1
            or iv["kpi_staged"] not in {0, 1}
        ):
            raise ValueError("incident terminal does not join its probe")
    else:
        raise ValueError("available terminal must be exactly na or incident")
    if not readiness["terminal_ready"]:
        raise ValueError("available terminal is not marked ready")
    kpi_ready = _validate_kpi(
        kpi, terminal_kind=kind, incident=incident
    )
    if readiness["kpi_state_ready"] is not kpi_ready:
        raise ValueError("KPI readiness disagrees with the typed tuple")
    return {
        **frame,
        "probe": probe,
        "resources": resources,
        "terminal": {"kind": kind, "na": na, "incident": incident},
        "kpi": kpi,
        "readiness": readiness,
    }


def normalize_zhongguo_incident_snapshot_v1_response(
    value: object,
    *,
    expected_query: ZhongguoIncidentQueryV1,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_connection_generation: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Validate the service/MCP response and its same-frame binding."""

    final_frame = _exact(
        value, _FINAL_FRAME_KEYS, "zhongguo_incident_snapshot_response"
    )
    expected_snapshot_id = _bounded_text(
        expected_snapshot_id, "expected_snapshot_id", maximum_bytes=256
    )
    expected_revision = _integer(
        expected_revision, "expected_revision", minimum=0, maximum=2**64 - 1
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
    native = normalize_native_zhongguo_incident_snapshot_v1(
        {key: final_frame[key] for key in _FRAME_KEYS},
        expected_query=expected_query,
        expected_snapshot_revision=expected_native_revision,
        expected_date_raw=expected_date_raw,
        expected_player_character_id=expected_player_character_id,
    )
    build = _exact(final_frame["build"], _BUILD_KEYS, "build")
    if build != {
        "version": ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_VERSION,
        "exe_sha256": ZHONGGUO_INCIDENT_SNAPSHOT_V1_EXECUTABLE_SHA256,
    }:
        raise ValueError("build does not match the frozen exact build")
    source = _exact(final_frame["source"], _SOURCE_KEYS, "source")
    expected_source = {
        "bridge_version": ZHONGGUO_INCIDENT_SNAPSHOT_V1_BRIDGE_VERSION,
        "game_adapter_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_GAME_ADAPTER_ID,
        "backend_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_SOURCE_BACKEND_ID,
        "consumer_id": ZHONGGUO_INCIDENT_SNAPSHOT_V1_CONSUMER_ID,
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
    if native["status"] == "available":
        probe = native["probe"]
        assert isinstance(probe, dict)
        owner_field = probe["owner_character_id"]
        assert isinstance(owner_field, dict)
        actual_owner = _positive_int32(
            _value(owner_field, "probe.owner_character_id"),
            "probe.owner_character_id",
        )
    binding = _exact(final_frame["binding"], _BINDING_KEYS, "binding")
    expected_binding = {
        "request_nonce": expected_query.request_nonce,
        "profile": expected_query.profile,
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
        **native,
        "build": dict(build),
        "source": dict(source),
        "binding": dict(binding),
    }
