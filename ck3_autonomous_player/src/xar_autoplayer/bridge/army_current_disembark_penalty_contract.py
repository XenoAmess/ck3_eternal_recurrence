"""Exact .3/.4 observed signed native remaining landing days.

The named source chain establishes the genuine CArmy receiver.
The direct getter defines no clamp/sentinel. Days do not prove native active
status or an expiry predicate, and current days do not predict a future route.
"""
from __future__ import annotations

from copy import deepcopy
from .version_identity import CK3_12003, CK3_12004, require_exact_native_build

LEAF = "current_disembark_penalty_v1"
SOURCE = "native_current_disembark_penalty_days_12003"
_KEYS = {"schema_version", "source", "status", "remaining_days", "unavailable_reason"}


def normalize_current_disembark_penalty_v1(value: object) -> dict[str, object]:
    # Present-only entry: old-wire omission never invokes this function.
    if type(value) is not dict or value.keys() != _KEYS:
        raise ValueError(f"native {LEAF} schema is malformed")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError(f"native {LEAF}.schema_version is malformed")
    if value["source"] != SOURCE:
        raise ValueError(f"native {LEAF}.source is malformed")
    status, days, reason = value["status"], value["remaining_days"], value["unavailable_reason"]
    if status == "available":
        if type(days) is not int or not -(2**31) <= days <= 2**31 - 1 or reason is not None:
            raise ValueError(f"native available {LEAF} requires a signed int32 observation")
    elif status == "unavailable":
        if days is not None or type(reason) is not str or not reason:
            raise ValueError(f"native unavailable {LEAF} requires a null operand and a reason")
    else:
        raise ValueError(f"native {LEAF}.status is malformed")
    return deepcopy(value)


def project_current_disembark_penalty_v1(
    raw: dict[str, object] | None, *, source_provenance: dict[str, object],
) -> dict[str, object]:
    """Pure observed-current input; no native active/expiry inference."""
    result = {
        "schema_version": 1,
        "source": "source_bound_current_disembark_penalty_days_12003",
        "status": "unavailable",
        "current_disembark_days_ready": False,
        "remaining_days": None,
        "unavailable_reason": "current_disembark_penalty_not_published",
        "source_provenance": deepcopy(source_provenance),
        "observed_current_disembark_penalty": deepcopy(raw),
        "future_route_landing_days_ready": False,
    }
    if raw is None:
        return result
    if require_exact_native_build(
        source_provenance.get("game_version"),
        source_provenance.get("executable_sha256"),
    ) not in (CK3_12003, CK3_12004):
        raise ValueError("current landing input requires its exact .3/.4 source")
    normalized = normalize_current_disembark_penalty_v1(raw)
    result.update(
        status=normalized["status"],
        current_disembark_days_ready=normalized["status"] == "available",
        remaining_days=normalized["remaining_days"],
        unavailable_reason=normalized["unavailable_reason"],
    )
    return result
