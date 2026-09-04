"""Strict project-contribution to metrics postcondition query contract."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Mapping


QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-projects-metrics-postcondition-v1"
)
QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP: Final = (
    "query-zhongguo-projects-metrics-postcondition-v1"
)
QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP}-"
)
_NONCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS = {"status", "value", "unavailable_reason"}
_IDENTITY_KEYS = {
    "owner_character_id", "subject_character_id", "cycle_serial", "case_serial"
}
_READINESS_KEYS = {
    "player_subject_binding_ready", "owner_binding_ready",
    "source_identity_ready", "result_identity_ready", "contribution_ready",
    "metrics_ready", "same_project_case_identity", "receipt_lineage_ready",
    "result_operation_committed", "same_frame_ready", "ready",
}
_CHECKPOINT_STATES = {
    "unavailable",
    "cp26_ready_p3_absent",
    "p3_initialized_source_not_ready",
    "p3_source_ready_result_pending",
    "p3_result_committed",
}


@dataclass(frozen=True)
class ZhongguoProjectsMetricsQueryV1:
    owner_character_id: int
    request_nonce: str


def _positive(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _nonce(value: object) -> str:
    if not isinstance(value, str) or _NONCE.fullmatch(value) is None:
        raise ValueError("request_nonce must be a bounded ASCII token")
    return value


def query_zhongguo_projects_metrics_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_projects_metrics_v1_step(
    step: object,
) -> ZhongguoProjectsMetricsQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_PROJECTS_METRICS_V1_STEP_PREFIX
    ).split("-", 1)
    if len(parts) != 2:
        return None
    try:
        owner = int(parts[0], 10)
        if str(owner) != parts[0] or not parts[1] or len(parts[1]) % 2:
            return None
        nonce = bytes.fromhex(parts[1]).decode("ascii")
        if nonce.encode("ascii").hex() != parts[1]:
            return None
        return ZhongguoProjectsMetricsQueryV1(
            _positive(owner, "owner_character_id"), _nonce(nonce)
        )
    except (UnicodeDecodeError, ValueError):
        return None


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _typed(value: object, name: str, kind: type) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    if field["status"] == "available":
        raw = field["value"]
        if field["unavailable_reason"] is not None or isinstance(raw, bool) or (
            not isinstance(raw, kind)
        ):
            raise ValueError(f"{name} has an invalid available value")
    elif field["status"] == "unavailable":
        if field["value"] is not None or not isinstance(
            field["unavailable_reason"], str
        ):
            raise ValueError(f"{name} has invalid typed unavailability")
    else:
        raise ValueError(f"{name} has invalid status")
    return dict(field)


def _identity(value: object, name: str) -> dict[str, object]:
    raw = _exact(value, _IDENTITY_KEYS, name)
    return {key: _typed(raw[key], f"{name}.{key}", int) for key in raw}


def normalize_native_zhongguo_projects_metrics_v1(
    value: object, *, expected_query: ZhongguoProjectsMetricsQueryV1,
    expected_snapshot_revision: int, expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    keys = {
        "schema_version", "status", "capability", "case_kind",
        "request_nonce", "snapshot_revision", "date_raw", "paused",
        "player_character_id", "requested_owner_character_id", "checkpoint_state",
        "source_identity", "result_identity", "projects_metrics",
        "readiness", "source_backend_id", "provenance", "unavailable_reason",
    }
    frame = _exact(value, keys, "projects_metrics_frame")
    if (
        frame["schema_version"] != 1
        or frame["capability"] != QUERY_ZHONGGUO_PROJECTS_METRICS_V1_CAPABILITY
        or frame["case_kind"] != "zhongguo.projects-metrics.project-correlation"
        or frame["source_backend_id"] != "native-headless"
    ):
        raise ValueError("provider provenance changed")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request nonce changed")
    if (
        frame["snapshot_revision"] != expected_snapshot_revision
        or frame["date_raw"] != expected_date_raw
        or frame["paused"] is not True
        or frame["player_character_id"] != expected_player_character_id
        or frame["requested_owner_character_id"] != expected_query.owner_character_id
        or expected_query.owner_character_id == expected_player_character_id
    ):
        raise ValueError("paused owner/subject binding changed")
    source = _identity(frame["source_identity"], "source_identity")
    result = _identity(frame["result_identity"], "result_identity")
    payload = _exact(
        frame["projects_metrics"],
        {"source_identity", "result_identity", "contribution", "metrics_result"},
        "projects_metrics",
    )
    payload_source = _identity(payload["source_identity"], "projects_metrics.source_identity")
    payload_result = _identity(payload["result_identity"], "projects_metrics.result_identity")
    if payload_source != source or payload_result != result:
        raise ValueError("outer and payload identities disagree")
    contribution_raw = _exact(
        payload["contribution"],
        {"identity", "receipt_id", "receipt_revision", "value", "provider_observed"},
        "contribution",
    )
    if contribution_raw["provider_observed"] is not True:
        raise ValueError("contribution is not provider observed")
    contribution = {
        "identity": _identity(contribution_raw["identity"], "contribution.identity"),
        "receipt_id": _typed(contribution_raw["receipt_id"], "contribution.receipt_id", int),
        "receipt_revision": _typed(contribution_raw["receipt_revision"], "contribution.receipt_revision", int),
        "value": _typed(contribution_raw["value"], "contribution.value", int),
        "provider_observed": True,
    }
    metrics_raw = _exact(
        payload["metrics_result"],
        {"identity", "source_contribution_receipt_id",
         "source_contribution_receipt_revision", "metrics_revision",
         "dictionary_key", "provider_observed"},
        "metrics_result",
    )
    if metrics_raw["provider_observed"] is not True:
        raise ValueError("metrics result is not provider observed")
    metrics = {
        "identity": _identity(metrics_raw["identity"], "metrics_result.identity"),
        "source_contribution_receipt_id": _typed(
            metrics_raw["source_contribution_receipt_id"],
            "metrics_result.source_contribution_receipt_id", int,
        ),
        "source_contribution_receipt_revision": _typed(
            metrics_raw["source_contribution_receipt_revision"],
            "metrics_result.source_contribution_receipt_revision", int,
        ),
        "metrics_revision": _typed(
            metrics_raw["metrics_revision"], "metrics_result.metrics_revision", int
        ),
        "dictionary_key": _typed(
            metrics_raw["dictionary_key"], "metrics_result.dictionary_key", str
        ),
        "provider_observed": True,
    }
    readiness_raw = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(item, bool) for item in readiness_raw.values()):
        raise ValueError("readiness values must be boolean")
    expected_ready = all(readiness_raw[key] for key in _READINESS_KEYS - {"ready"})
    if readiness_raw["ready"] is not expected_ready:
        raise ValueError("readiness aggregate disagrees")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("invalid provider status")
    checkpoint_state = frame["checkpoint_state"]
    if (
        not isinstance(checkpoint_state, str)
        or checkpoint_state not in _CHECKPOINT_STATES
    ):
        raise ValueError("invalid projects/metrics checkpoint state")
    if frame["status"] == "available":
        if (
            frame["unavailable_reason"] is not None
            or checkpoint_state == "unavailable"
        ):
            raise ValueError("available provider has an unavailable reason")
        source_keys = (
            "player_subject_binding_ready",
            "owner_binding_ready",
            "source_identity_ready",
            "contribution_ready",
            "same_frame_ready",
        )
        if not all(readiness_raw[key] is True for key in source_keys):
            raise ValueError("available provider lacks its direct CP26 source")
        if checkpoint_state == "cp26_ready_p3_absent" and any(
            readiness_raw[key] is True
            for key in (
                "result_identity_ready",
                "metrics_ready",
                "same_project_case_identity",
                "receipt_lineage_ready",
                "result_operation_committed",
                "ready",
            )
        ):
            raise ValueError("CP26/P3-absent state exposes a P3 result")
        if (
            checkpoint_state == "p3_result_committed"
            and readiness_raw["ready"] is not True
        ):
            raise ValueError("committed checkpoint is not ready")
    elif (
        not isinstance(frame["unavailable_reason"], str)
        or checkpoint_state != "unavailable"
    ):
        raise ValueError("unavailable provider lacks reason/state")
    return {
        **frame,
        "source_identity": source,
        "result_identity": result,
        "projects_metrics": {
            "source_identity": payload_source,
            "result_identity": payload_result,
            "contribution": contribution,
            "metrics_result": metrics,
        },
        "readiness": dict(readiness_raw),
    }


def bind_projects_metrics_event_snapshots_v1(
    business_query: Mapping[str, object], source_event: Mapping[str, object],
    result_event: Mapping[str, object],
) -> dict[str, object]:
    """Bind a normalized business read to two normalized event snapshots."""

    business = dict(business_query)
    source_binding = source_event.get("binding")
    result_binding = result_event.get("binding")
    binding = business.get("binding")
    if not all(isinstance(item, Mapping) for item in (
        source_binding, result_binding, binding
    )):
        raise ValueError("source/result/business binding is missing")
    generation = binding.get("connection_generation")  # type: ignore[union-attr]
    _positive(generation, "connection_generation")
    if any(
        item.get("connection_generation") != generation
        for item in (source_binding, result_binding)
    ):
        raise ValueError("source/result connection generation drifted")
    if binding.get("snapshot_id") != result_binding.get("snapshot_id") or (
        binding.get("native_revision") != result_binding.get("native_revision")
    ):
        raise ValueError("business query is not bound to the result snapshot")
    business["binding"] = {
        **dict(binding),
        "source_snapshot_id": source_binding.get("snapshot_id"),
        "result_snapshot_id": result_binding.get("snapshot_id"),
        "source_revision": source_binding.get("revision"),
        "result_revision": result_binding.get("revision"),
        "source_native_revision": source_binding.get("native_revision"),
        "result_native_revision": result_binding.get("native_revision"),
    }
    return business
