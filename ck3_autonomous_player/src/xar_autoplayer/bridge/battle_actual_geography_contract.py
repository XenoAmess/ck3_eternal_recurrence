"""Optional actual Combat geography; outer query retains identity/frame binding.

These retained fields describe this Combat. They do not reconstruct its complete
constructor or determine the geometry of a future player contact.
"""

from __future__ import annotations


def _optional_signed(value: object, field: str, bits: int) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not -(2 ** (bits - 1)) <= value < 2 ** (bits - 1):
        raise ValueError(f"{field} must be a signed int{bits} or null")
    return value


def normalize_actual_geography_v1(
    value: object, *, field: str = "actual_geography_v1"
) -> dict[str, object] | None:
    """Copy genuine retained values without reconstructing an entry province."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {
        "terrain", "constructor_adjacency_kind_raw", "holding_defender"
    }:
        raise ValueError(f"{field} must contain the actual-geography v1 fields")
    terrain = value["terrain"]
    terrain_field = f"{field}.terrain"
    if not isinstance(terrain, dict) or set(terrain) != {
        "status", "key", "combat_width_multiplier_raw", "scale",
        "unavailable_reason",
    }:
        raise ValueError(f"{terrain_field} must contain the existing terrain fields")
    status = terrain["status"]
    if status not in ("available", "unavailable"):
        raise ValueError(f"{terrain_field}.status is invalid")
    scale = terrain["scale"]
    if type(scale) is not int or scale != 100000:
        raise ValueError(f"{terrain_field}.scale must be 100000")
    key = terrain["key"]
    width = _optional_signed(
        terrain["combat_width_multiplier_raw"],
        f"{terrain_field}.combat_width_multiplier_raw",
        64,
    )
    reason = terrain["unavailable_reason"]
    if status == "available":
        if not isinstance(key, str) or not key:
            raise ValueError(f"{terrain_field}.key must be a nonempty native key")
        if width is None or reason is not None:
            raise ValueError(f"{terrain_field} available values are incomplete")
    elif key is not None or width is not None:
        raise ValueError(f"{terrain_field} unavailable values must be null")
    elif not isinstance(reason, str) or not reason:
        raise ValueError(f"{terrain_field}.unavailable_reason must be nonempty")
    kind = _optional_signed(
        value["constructor_adjacency_kind_raw"],
        f"{field}.constructor_adjacency_kind_raw",
        32,
    )
    holding = value["holding_defender"]
    if holding is not None and type(holding) is not bool:
        raise ValueError(f"{field}.holding_defender must be a bool or null")
    return {
        "terrain": {
            "status": status,
            "key": key,
            "combat_width_multiplier_raw": width,
            "scale": scale,
            "unavailable_reason": reason,
        },
        "constructor_adjacency_kind_raw": kind,
        "holding_defender": holding,
    }
