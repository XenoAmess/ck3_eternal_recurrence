"""Strict subject-side career-HC postcondition query contract for M360 route B.

The route-B product receipt and the career headcount ledger are read from the
same paused native frame.  The contract deliberately does not treat an event
option acknowledgement as either observation.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final


QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY: Final = (
    "game.command.query-zhongguo-career-hc-workforce-postcondition-v1"
)
QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP: Final = (
    "query-zhongguo-career-hc-workforce-postcondition-v1"
)
QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP_PREFIX: Final = (
    f"{QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP}-"
)
ZHONGGUO_CAREER_HC_WORKFORCE_V1_CASE_KIND: Final = (
    "zhongguo.career-hc.workforce.route-b-no-hc-debit"
)
ZHONGGUO_CAREER_HC_WORKFORCE_V1_BACKEND_ID: Final = (
    "ck3-1.19.0.6-native-zhongguo-career-hc-workforce-postcondition-v1"
)

_NONCE_RE: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")
_TYPED_KEYS: Final = {"status", "value", "unavailable_reason"}
_IDENTITY_KEYS: Final = {
    "owner_character_id",
    "subject_character_id",
    "cycle_serial",
    "case_serial",
}
_RECEIPT_KEYS: Final = _IDENTITY_KEYS | {
    "state",
    "choice",
    "provider_observed",
}
_PARTITION_KEYS: Final = {
    "authorized",
    "available",
    "reserved",
    "occupied",
    "frozen",
    "reclaimed",
    "conserved",
    "provider_observed",
}
_ROUTE_COST_KEYS: Final = {"manager_cost_total", "provider_observed"}
_READINESS_KEYS: Final = {
    "player_subject_binding_ready",
    "owner_binding_ready",
    "m360_identity_ready",
    "m360_route_b_receipt_ready",
    "career_hc_partition_ready",
    "career_hc_conservation_ready",
    "route_b_manager_cost_zero_ready",
    "same_frame_ready",
    "ready",
}
_FRAME_KEYS: Final = {
    "schema_version",
    "status",
    "capability",
    "case_kind",
    "source_backend_id",
    "request_nonce",
    "snapshot_revision",
    "date_raw",
    "paused",
    "player_character_id",
    "subject_character_id",
    "requested_owner_character_id",
    "m360_identity",
    "m360_receipt",
    "career_hc_partition",
    "route_b_cost",
    "readiness",
    "unavailable_reason",
}


@dataclass(frozen=True)
class ZhongguoCareerHcWorkforceQueryV1:
    owner_character_id: int
    request_nonce: str


def _exact(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} must contain exactly the v1 fields")
    return value


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= 2**63 - 1
    ):
        raise ValueError(f"{name} must be an integer in range")
    return value


def _positive(value: object, name: str) -> int:
    result = _integer(value, name, minimum=1)
    if result > 2**31 - 1:
        raise ValueError(f"{name} must be a positive signed CharacterID")
    return result


def _nonce(value: object) -> str:
    if not isinstance(value, str) or _NONCE_RE.fullmatch(value) is None:
        raise ValueError("request_nonce must be a bounded ASCII token")
    return value


def query_zhongguo_career_hc_workforce_v1_step(
    owner_character_id: object, request_nonce: object
) -> str:
    owner = _positive(owner_character_id, "owner_character_id")
    nonce = _nonce(request_nonce)
    return (
        f"{QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP_PREFIX}"
        f"{owner}-{nonce.encode('ascii').hex()}"
    )


def parse_query_zhongguo_career_hc_workforce_v1_step(
    step: object,
) -> ZhongguoCareerHcWorkforceQueryV1 | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP_PREFIX
    ):
        return None
    parts = step.removeprefix(
        QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP_PREFIX
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
        return ZhongguoCareerHcWorkforceQueryV1(
            _positive(owner, "owner_character_id"), _nonce(nonce)
        )
    except (UnicodeDecodeError, ValueError):
        return None


def _typed_integer(value: object, name: str) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    if field["status"] == "available":
        _integer(field["value"], f"{name}.value")
        if field["unavailable_reason"] is not None:
            raise ValueError(f"{name} available value has an unavailable reason")
    elif field["status"] == "unavailable":
        if field["value"] is not None or not isinstance(
            field["unavailable_reason"], str
        ):
            raise ValueError(f"{name} has invalid typed unavailability")
    else:
        raise ValueError(f"{name} has invalid status")
    return dict(field)


def _typed_boolean(value: object, name: str) -> dict[str, object]:
    field = _exact(value, _TYPED_KEYS, name)
    if field["status"] == "available":
        if not isinstance(field["value"], bool) or field["unavailable_reason"] is not None:
            raise ValueError(f"{name} has an invalid available boolean")
    elif field["status"] == "unavailable":
        if field["value"] is not None or not isinstance(
            field["unavailable_reason"], str
        ):
            raise ValueError(f"{name} has invalid typed unavailability")
    else:
        raise ValueError(f"{name} has invalid status")
    return dict(field)


def _available(field: dict[str, object], name: str) -> int | bool:
    if field["status"] != "available":
        raise ValueError(f"{name} must be available for a GREEN frame")
    value = field["value"]
    assert isinstance(value, (int, bool))
    return value


def _identity(value: object, name: str) -> dict[str, dict[str, object]]:
    raw = _exact(value, _IDENTITY_KEYS, name)
    return {
        key: _typed_integer(raw[key], f"{name}.{key}") for key in raw
    }


def normalize_native_zhongguo_career_hc_workforce_v1(
    value: object,
    *,
    expected_query: ZhongguoCareerHcWorkforceQueryV1,
    expected_snapshot_revision: int,
    expected_date_raw: int,
    expected_player_character_id: int,
) -> dict[str, object]:
    """Normalize one exact, closed provider frame.

    Available frames are deliberately opinionated: only M360 route B is a
    valid result, and its six career-HC buckets must be non-negative and sum
    exactly to authorized headcount in that same frame.
    """

    frame = _exact(value, _FRAME_KEYS, "career_hc_workforce_frame")
    if (
        frame["schema_version"] != 1
        or frame["capability"]
        != QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY
        or frame["case_kind"] != ZHONGGUO_CAREER_HC_WORKFORCE_V1_CASE_KIND
        or frame["source_backend_id"]
        != ZHONGGUO_CAREER_HC_WORKFORCE_V1_BACKEND_ID
    ):
        raise ValueError("provider provenance changed")
    if frame["request_nonce"] != expected_query.request_nonce:
        raise ValueError("request nonce changed")
    if (
        frame["snapshot_revision"] != expected_snapshot_revision
        or frame["date_raw"] != expected_date_raw
        or frame["paused"] is not True
        or frame["player_character_id"] != expected_player_character_id
        or frame["subject_character_id"] != expected_player_character_id
        or frame["requested_owner_character_id"]
        != expected_query.owner_character_id
        or expected_query.owner_character_id == expected_player_character_id
    ):
        raise ValueError("paused received-self binding changed")

    identity = _identity(frame["m360_identity"], "m360_identity")
    receipt_raw = _exact(frame["m360_receipt"], _RECEIPT_KEYS, "m360_receipt")
    receipt = {
        key: _typed_integer(receipt_raw[key], f"m360_receipt.{key}")
        for key in _IDENTITY_KEYS | {"state", "choice"}
    }
    if not isinstance(receipt_raw["provider_observed"], bool):
        raise ValueError("M360 receipt provider_observed must be boolean")
    partition_raw = _exact(
        frame["career_hc_partition"], _PARTITION_KEYS, "career_hc_partition"
    )
    partition = {
        key: _typed_integer(partition_raw[key], f"career_hc_partition.{key}")
        for key in {
            "authorized", "available", "reserved", "occupied", "frozen",
            "reclaimed",
        }
    }
    partition["conserved"] = _typed_boolean(
        partition_raw["conserved"], "career_hc_partition.conserved"
    )
    if not isinstance(partition_raw["provider_observed"], bool):
        raise ValueError("career HC provider_observed must be boolean")
    cost_raw = _exact(frame["route_b_cost"], _ROUTE_COST_KEYS, "route_b_cost")
    cost = {
        "manager_cost_total": _typed_integer(
            cost_raw["manager_cost_total"], "route_b_cost.manager_cost_total"
        ),
        "provider_observed": cost_raw["provider_observed"],
    }
    if not isinstance(cost["provider_observed"], bool):
        raise ValueError("route-B cost provider_observed must be boolean")

    readiness = _exact(frame["readiness"], _READINESS_KEYS, "readiness")
    if any(not isinstance(flag, bool) for flag in readiness.values()):
        raise ValueError("readiness values must be boolean")
    expected_ready = all(readiness[key] for key in _READINESS_KEYS - {"ready"})
    if readiness["ready"] is not expected_ready:
        raise ValueError("readiness aggregate disagrees")
    if frame["status"] not in {"available", "unavailable"}:
        raise ValueError("invalid provider status")
    if frame["status"] == "unavailable":
        if not isinstance(frame["unavailable_reason"], str):
            raise ValueError("unavailable provider lacks reason")
    else:
        if frame["unavailable_reason"] is not None or readiness["ready"] is not True:
            raise ValueError("available provider is not ready")
        if not all(
            observed is True
            for observed in (
                receipt_raw["provider_observed"],
                partition_raw["provider_observed"],
                cost_raw["provider_observed"],
            )
        ):
            raise ValueError("available result is not fully provider observed")
        identity_values = {
            key: _available(field, f"m360_identity.{key}")
            for key, field in identity.items()
        }
        receipt_values = {
            key: _available(field, f"m360_receipt.{key}")
            for key, field in receipt.items()
        }
        if any(
            receipt_values[key] != identity_values[key]
            for key in _IDENTITY_KEYS
        ):
            raise ValueError("M360 identity and receipt disagree")
        if (
            identity_values["owner_character_id"]
            != expected_query.owner_character_id
            or identity_values["subject_character_id"]
            != expected_player_character_id
            or receipt_values["state"] != 4
            or receipt_values["choice"] != 2
        ):
            raise ValueError("provider did not observe the requested route-B case")
        partition_values = {
            key: _available(field, f"career_hc_partition.{key}")
            for key, field in partition.items()
        }
        authorized = partition_values["authorized"]
        bucket_sum = sum(
            int(partition_values[key])
            for key in ("available", "reserved", "occupied", "frozen", "reclaimed")
        )
        if (
            authorized != bucket_sum
            or partition_values["conserved"] is not True
            or _available(cost["manager_cost_total"], "route_b_cost.manager_cost_total")
            != 0
        ):
            raise ValueError("route-B career-HC conservation is not GREEN")

    return {
        **frame,
        "m360_identity": identity,
        "m360_receipt": {
            **receipt,
            "provider_observed": receipt_raw["provider_observed"],
        },
        "career_hc_partition": {
            **partition,
            "provider_observed": partition_raw["provider_observed"],
        },
        "route_b_cost": cost,
        "readiness": dict(readiness),
    }


__all__ = [
    "QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_CAPABILITY",
    "QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP",
    "QUERY_ZHONGGUO_CAREER_HC_WORKFORCE_V1_STEP_PREFIX",
    "ZHONGGUO_CAREER_HC_WORKFORCE_V1_BACKEND_ID",
    "ZHONGGUO_CAREER_HC_WORKFORCE_V1_CASE_KIND",
    "ZhongguoCareerHcWorkforceQueryV1",
    "normalize_native_zhongguo_career_hc_workforce_v1",
    "parse_query_zhongguo_career_hc_workforce_v1_step",
    "query_zhongguo_career_hc_workforce_v1_step",
]
