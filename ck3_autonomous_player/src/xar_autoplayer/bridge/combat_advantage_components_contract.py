"""Validate private CK3 1.19.0.6 original-call advantage observations.

This diagnostic never supplies a next-day forecast input: helper return values
are observed only after the game has already produced the current cache.
"""

from __future__ import annotations


_SOURCE = "native_cache_0x2308d50_original_calls"
_ROOT_KEYS = {"schema_version", "source", "requested", "available",
              "failure_flags", "materializations"}
_ROOT_KEYS_WITH_DIAGNOSTIC = _ROOT_KEYS | {"first_aggregator_failure"}
_ROW_KEYS = {"ordinal", "thread_id", "caller_rva", "combat_id", "date_raw", "base_raw",
             "resolved_raw", "complete", "sides"}
_SIDE_KEYS = {"side_index", "roll", "commander_character_id", "roll_raw",
              "commander_raw", "aggregator_raw", "total_raw", "helper_calls",
              "complete"}
_SIDE_KEYS_WITH_CALLS = _SIDE_KEYS | {"nested_aggregator_calls",
                                "primary_aggregator_calls"}
_FAILURE_KEYS = {"gate", "thread_id", "caller_rva", "caller_address",
                 "side_index", "expected_side_index", "helper_calls",
                 "value_present"}
_I64_MIN, _I64_MAX = -(2**63), 2**63 - 1
_FINISH_STEP = "experimental-combat-phase-event-trace-finish-v1"


def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def _sum_i64(*values: int) -> int | None:
    total = 0
    for value in values:
        total += value
        if not _integer(total, _I64_MIN, _I64_MAX):
            return None
    return total


def normalize_runtime_advantage_components_v1(
    managed_result: object, *, combat_id: int,
) -> dict[str, object] | None:
    """Return a checked private diagnostic, or None for an older result.

    Every numeric identity is checked again across the C++/JSON boundary.
    Even an available observation remains retrospective and forecast_usable=False.
    """
    if not isinstance(managed_result, dict):
        raise ValueError("managed trace is malformed")
    if "advantage_components" not in managed_result:
        return None
    output = managed_result["advantage_components"]
    if not isinstance(output, dict) or set(output) not in (
        _ROOT_KEYS, _ROOT_KEYS_WITH_DIAGNOSTIC,
    ):
        raise ValueError("advantage component root is malformed")
    has_diagnostic = "first_aggregator_failure" in output
    if (output["schema_version"] != 1 or type(output["schema_version"]) is not int
            or output["source"] != _SOURCE or output["requested"] is not True
            or type(output["available"]) is not bool
            or not _integer(output["failure_flags"], 0, 2**32 - 1)):
        raise ValueError("advantage component provenance is malformed")
    if has_diagnostic:
        failure = output["first_aggregator_failure"]
        if not isinstance(failure, dict) or set(failure) != _FAILURE_KEYS:
            raise ValueError("advantage first-failure shape is malformed")
        gate = failure["gate"]
        if (not _integer(gate, 0, 5)
                or not _integer(failure["thread_id"], 0, 2**32 - 1)
                or not _integer(failure["caller_rva"], 0, 2**32 - 1)
                or not _integer(failure["caller_address"], 0, 2**64 - 1)
                or not _integer(failure["side_index"], -(2**31), 2**31 - 1)
                or not _integer(failure["expected_side_index"], -1, 1)
                or not _integer(failure["helper_calls"], 0, 2)
                or type(failure["value_present"]) is not bool):
            raise ValueError("advantage first-failure values are malformed")
        if ((gate == 0) != ((output["failure_flags"] & 64) == 0)):
            raise ValueError("advantage first-failure gate contradicts flag")
        if gate == 0 and failure != {
            "gate": 0, "thread_id": 0, "caller_rva": 0,
            "caller_address": 0, "side_index": -1,
            "expected_side_index": -1, "helper_calls": 0,
            "value_present": False,
        }:
            raise ValueError("advantage empty first-failure invented a call")
        if gate != 0 and (failure["thread_id"] == 0 or
                          failure["caller_address"] == 0):
            raise ValueError("advantage first-failure lacks caller identity")
    rows = output["materializations"]
    if not isinstance(rows, list) or len(rows) > 8:
        raise ValueError("advantage component materializations are unbounded")
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != _ROW_KEYS:
            raise ValueError("advantage component row is malformed")
        if (not _integer(row["ordinal"], index, index)
                or not _integer(row["thread_id"], 1, 2**32 - 1)
                or not _integer(row["caller_rva"], 1, 2**32 - 1)
                or not _integer(row["combat_id"], combat_id, combat_id)
                or not _integer(row["date_raw"], -(2**31), 2**31 - 1)
                or type(row["complete"]) is not bool
                or any(not _integer(row[key], _I64_MIN, _I64_MAX)
                       for key in ("base_raw", "resolved_raw"))):
            raise ValueError("advantage component row identity is malformed")
        sides = row["sides"]
        if not isinstance(sides, list) or len(sides) != 2:
            raise ValueError("advantage component side pair is malformed")
        for side_index, side in enumerate(sides):
            if not isinstance(side, dict) or set(side) != (
                _SIDE_KEYS_WITH_CALLS if has_diagnostic else _SIDE_KEYS
            ):
                raise ValueError("advantage component side is malformed")
            if (not _integer(side["side_index"], -1, 1)
                    or not _integer(side["roll"], -(2**31), 2**31 - 1)
                    or not _integer(side["commander_character_id"], -(2**31), 2**31 - 1)
                    or not _integer(side["helper_calls"], 0, 2)
                    or type(side["complete"]) is not bool
                    or any(not _integer(side[key], _I64_MIN, _I64_MAX)
                           for key in ("roll_raw", "commander_raw",
                                       "aggregator_raw", "total_raw"))):
                raise ValueError("advantage component side value is malformed")
            if side["complete"]:
                if (side["side_index"] != side_index
                        or side["helper_calls"] != 2
                        or side["roll_raw"] != side["roll"] * 100000
                        or _sum_i64(side["roll_raw"], side["commander_raw"],
                                    side["aggregator_raw"]) != side["total_raw"]):
                    raise ValueError("advantage component side arithmetic differs")
            if has_diagnostic:
                nested = side["nested_aggregator_calls"]
                primary = side["primary_aggregator_calls"]
                if (not _integer(nested, 0, 1) or not _integer(primary, 0, 1)
                        or (side["complete"] and primary != 1)):
                    raise ValueError("advantage aggregator call classification differs")
        if row["complete"]:
            if (not all(side["complete"] for side in sides)
                    or _sum_i64(row["base_raw"], sides[0]["total_raw"],
                                -sides[1]["total_raw"]) != row["resolved_raw"]):
                raise ValueError("advantage cache arithmetic differs")
    computed_available = (bool(rows) and output["failure_flags"] == 0
                          and all(row["complete"] for row in rows))
    if output["available"] is not computed_available:
        raise ValueError("advantage availability contradicts evidence")
    checkpoint = managed_result.get("managed_checkpoint")
    if not isinstance(checkpoint, dict):
        raise ValueError("advantage checkpoint is missing")
    gates = ("recoverable_checkpoint_created", "exact_one_day_observed",
             "boundary_dates_match_checkpoint", "detours_uninstalled")
    if any(type(checkpoint.get(key)) is not bool for key in gates):
        raise ValueError("advantage checkpoint gates are malformed")
    return {
        **output,
        "diagnostic_observation_complete": (
            computed_available and all(checkpoint[key] for key in gates)
        ),
        "forecast_usable": False,
        "validation_status": "live_validation_pending",
    }


def normalize_experimental_advantage_components_response_v1(
    frame: object, *, combat_id: int,
) -> dict[str, object] | None:
    """Validate the private finish envelope and its optional original-call row."""
    if not isinstance(frame, dict) or frame.get("type") != "command_result":
        raise ValueError("experimental advantage response is malformed")
    if (not _integer(frame.get("protocol_version"), 1, 1)
            or frame.get("ok") is not True):
        raise ValueError("experimental advantage response protocol failed")
    result = frame.get("result")
    if (not isinstance(result, dict) or result.get("step") != _FINISH_STEP
            or result.get("accepted") is not True
            or result.get("private_build") is not True
            or result.get("production_trace_ready") is not False
            or not _integer(result.get("combat_id"), combat_id, combat_id)
            or not _integer(result.get("managed_daily_sequence_token"), 1, 2**64 - 1)
            or result.get("status") not in {
                "bounded_trace_available", "trace_unavailable",
            }):
        raise ValueError("experimental advantage response boundary differs")
    diagnostic = normalize_runtime_advantage_components_v1(
        result.get("managed_trace"), combat_id=combat_id,
    )
    if diagnostic is None:
        return None
    if (diagnostic["diagnostic_observation_complete"] !=
            (result["status"] == "bounded_trace_available")):
        raise ValueError("experimental advantage response status differs")
    return {
        "combat_id": combat_id,
        "managed_daily_sequence_token": result["managed_daily_sequence_token"],
        **diagnostic,
    }
