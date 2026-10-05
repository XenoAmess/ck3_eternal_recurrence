"""Optional actual Combat geography; outer query retains identity/frame binding.

These retained fields describe this Combat. They do not reconstruct its complete
constructor or determine the geometry of a future player contact.
"""

from __future__ import annotations

from .battle_current_rule_context_contract import normalize_current_rule_context_v1
from .battle_stored_advantage_sources_contract import normalize_stored_advantage_sources_v1
from .battle_current_dynamic_advantage_contract import normalize_current_dynamic_advantage_v1
from .battle_current_dynamic_components_contract import normalize_current_dynamic_components_v1


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
    required = {
        "terrain", "constructor_adjacency_kind_raw", "holding_defender"
    }
    if (not isinstance(value, dict) or not required <= set(value)
            or set(value) - required - {"constructor_rule_effects_v1", "current_rule_context_v1", "stored_advantage_sources_v1", "current_dynamic_advantage_v1", "current_dynamic_components_v1"}):
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
    result = {
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
    if "constructor_rule_effects_v1" in value:
        result["constructor_rule_effects_v1"] = normalize_retained_rule_effects_v1(
            value["constructor_rule_effects_v1"], kind=kind,
            field=f"{field}.constructor_rule_effects_v1",
        )
    if "current_rule_context_v1" in value:
        result["current_rule_context_v1"] = normalize_current_rule_context_v1(
            value["current_rule_context_v1"], holding_defender=holding,
            effects=result.get("constructor_rule_effects_v1"), field=f"{field}.current_rule_context_v1",
        )
    if "stored_advantage_sources_v1" in value:
        result["stored_advantage_sources_v1"] = normalize_stored_advantage_sources_v1(
            value["stored_advantage_sources_v1"], field=f"{field}.stored_advantage_sources_v1",
        )
    if "current_dynamic_advantage_v1" in value:
        result["current_dynamic_advantage_v1"] = normalize_current_dynamic_advantage_v1(
            value["current_dynamic_advantage_v1"], field=f"{field}.current_dynamic_advantage_v1",
        )
    if "current_dynamic_components_v1" in value:
        result["current_dynamic_components_v1"] = normalize_current_dynamic_components_v1(
            value["current_dynamic_components_v1"], field=f"{field}.current_dynamic_components_v1",
        )
    return result


def normalize_retained_rule_effects_v1(
    value: object, *, kind: int | None, field: str,
) -> dict[str, object]:
    """Current loaded whole points; selection does not imply native append."""
    if not isinstance(value, dict) or set(value) != {
        "status", "points_scale", "unavailable_reason", "rows",
    }:
        raise ValueError(f"{field} must contain the loaded rule effect fields")
    status = value["status"]
    reason = value["unavailable_reason"]
    if status not in ("available", "unavailable") or type(value["points_scale"]) is not int or value["points_scale"] != 1:
        raise ValueError(f"{field} status or whole-point scale is invalid")
    if (status == "available" and reason is not None
            or status == "unavailable" and (not isinstance(reason, str) or not reason)):
        raise ValueError(f"{field} availability reason is invalid")
    rows = value["rows"]
    if not isinstance(rows, list) or len(rows) not in (0, 3):
        raise ValueError(f"{field}.rows must be empty or the three source slots")
    if not rows and status == "available":
        raise ValueError(f"{field} available slots are missing")
    if rows and kind not in (0, 1, 2, 3):
        raise ValueError(f"{field} source slots require supported retained kind")
    expected = (
        ("attacker_adjacency", 0, 0xF70 + 8 * kind),
        ("defender_adjacency", 1, 0xFA0 + 8 * kind),
        ("holding_defender", 1, 0xF10),
    ) if rows else ()
    normalized = []
    for row, source in zip(rows, expected):
        if not isinstance(row, dict) or set(row) != {
            "stage", "side_index", "rules_pointer_offset", "status", "key",
            "advantage_points", "unavailable_reason",
        }:
            raise ValueError(f"{field}.rows has invalid source fields")
        if (type(row["side_index"]) is not int or type(row["rules_pointer_offset"]) is not int
                or (row["stage"], row["side_index"], row["rules_pointer_offset"]) != source):
            raise ValueError(f"{field}.rows source does not match retained kind")
        row_status, key, row_reason = row["status"], row["key"], row["unavailable_reason"]
        points = _optional_signed(row["advantage_points"], f"{field}.advantage_points", 32)
        if row_status == "available":
            if not isinstance(key, str) or not key or points is None or row_reason is not None:
                raise ValueError(f"{field}.rows available effect is incomplete")
            if source[0] == "holding_defender" and key != "holding_defender_advantage":
                raise ValueError(f"{field}.rows holding effect key is invalid")
        elif row_status in ("not_selected", "unavailable"):
            if key is not None or points is not None:
                raise ValueError(f"{field}.rows unobserved effect values must be null")
            if row_status == "not_selected":
                if source[0] == "holding_defender" or row_reason is not None:
                    raise ValueError(f"{field}.rows invalid native adjacency skip")
            elif not isinstance(row_reason, str) or not row_reason:
                raise ValueError(f"{field}.rows missing unavailable reason")
        else:
            raise ValueError(f"{field}.rows invalid effect status")
        normalized.append(dict(row))
    if rows and (status == "available") != all(row["status"] != "unavailable" for row in rows):
        raise ValueError(f"{field} availability disagrees with source rows")
    return {"status": status, "points_scale": 1, "unavailable_reason": reason, "rows": normalized}
