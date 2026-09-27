"""Validate private CK3 1.19.0.6 original-call advantage observations.

This diagnostic never supplies a next-day forecast input: helper return values
are observed only after the game has already produced the current cache.
"""

from __future__ import annotations


_SOURCE = "native_cache_0x2308d50_original_calls"
_ROOT_KEYS = {"schema_version", "source", "requested", "available",
              "failure_flags", "materializations"}
_ROW_KEYS = {"ordinal", "thread_id", "caller_rva", "combat_id", "date_raw", "base_raw",
             "resolved_raw", "complete", "sides"}
_SIDE_KEYS = {"side_index", "roll", "commander_character_id", "roll_raw",
              "commander_raw", "aggregator_raw", "total_raw", "helper_calls",
              "complete"}
_I64_MIN, _I64_MAX = -(2**63), 2**63 - 1


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
    if not isinstance(output, dict) or set(output) != _ROOT_KEYS:
        raise ValueError("advantage component root is malformed")
    if (output["schema_version"] != 1 or type(output["schema_version"]) is not int
            or output["source"] != _SOURCE or output["requested"] is not True
            or type(output["available"]) is not bool
            or not _integer(output["failure_flags"], 0, 2**32 - 1)):
        raise ValueError("advantage component provenance is malformed")
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
            if not isinstance(side, dict) or set(side) != _SIDE_KEYS:
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
