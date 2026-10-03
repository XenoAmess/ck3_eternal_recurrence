"""Current-player native devotion, effective current-Rite traits and vow terms."""

from __future__ import annotations

from collections.abc import Mapping


def _identity(value: dict[str, object], current: Mapping[str, object]) -> None:
    for key in ("capture_epoch", "date_raw", "played_character_id"):
        if type(value[key]) is not int or value[key] != current[key]:
            raise ValueError(f"native religion observation differs from current owner: {key}")
    if value["available"]:
        if value["unavailable_reason"] is not None:
            raise ValueError("available religion observation has an unavailable reason")
    elif not isinstance(value["unavailable_reason"], str) or not value["unavailable_reason"]:
        raise ValueError("unavailable religion observation lost its read reason")


def normalize_player_piety_devotion_profile_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    if value is None:
        return None
    raw = ("current_devotion_total_raw", "progress_percent_raw", "progress_numerator_raw",
           "progress_denominator_raw", "level_lower_threshold_raw", "level_upper_threshold_raw")
    numbers = ("effective_level", "effective_cap", "runtime_threshold_count")
    keys = {"schema", "read_only", "available", "unavailable_reason", "capture_epoch",
            "date_raw", "played_character_id", *raw, *numbers,
            "native_terminal_threshold_branch", "raw_scale", "progress_unit", "is_monthly_change"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_player_devotion_profile_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000
            or value["progress_unit"] != "percent" or value["is_monthly_change"] is not False):
        raise ValueError("native devotion profile schema is malformed")
    _identity(value, current_context)
    for key in (*raw, *numbers):
        if value[key] is not None and type(value[key]) is not int:
            raise ValueError(f"native devotion numeric is malformed: {key}")
    terminal = value["native_terminal_threshold_branch"]
    if terminal is not None and type(terminal) is not bool:
        raise ValueError("native devotion terminal branch is malformed")
    if value["available"]:
        required = (*numbers, *raw[:4], "native_terminal_threshold_branch")
        if any(value[key] is None for key in required):
            raise ValueError("available devotion profile lost native values")
        if terminal and any(value[key] is not None for key in raw[4:]):
            raise ValueError("native terminal devotion branch acquired thresholds")
        if not terminal and value["effective_level"] >= 0 and any(value[key] is None for key in raw[4:]):
            raise ValueError("ordinary devotion interval lost native thresholds")
    return dict(value)


def normalize_player_rite_virtue_sin_profile_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    if value is None:
        return None
    keys = {"schema", "read_only", "available", "unavailable_reason", "capture_epoch",
            "date_raw", "played_character_id", "rite_id", "trait_count",
            "num_virtuous_traits", "num_sinful_traits", "traits", "scope", "counts_are_unweighted"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_player_rite_virtue_sin_profile_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or value["scope"] != "current-played-character-current-rite"
            or value["counts_are_unweighted"] is not True):
        raise ValueError("native Rite virtue/sin profile schema is malformed")
    _identity(value, current_context)
    for key in ("rite_id", "trait_count", "num_virtuous_traits", "num_sinful_traits"):
        if value[key] is not None and type(value[key]) is not int:
            raise ValueError(f"native Rite classification integer is malformed: {key}")
    if not isinstance(value["traits"], list):
        raise ValueError("native Rite classification rows are malformed")
    rows = []
    for row in value["traits"]:
        if (not isinstance(row, dict) or set(row) != {"trait_id", "classification",
                "opinion_weight_input_raw", "owner_modifier_scale_input_raw"}
                or type(row["trait_id"]) is not int or type(row["classification"]) is not int
                or row["classification"] not in (0, 1, 2)):
            raise ValueError("native Rite classification row is malformed")
        for key in ("opinion_weight_input_raw", "owner_modifier_scale_input_raw"):
            if row[key] is not None and type(row[key]) is not int:
                raise ValueError(f"native Rite consumer raw input is malformed: {key}")
        rows.append(dict(row))
    if value["available"]:
        if any(value[key] is None for key in ("rite_id", "trait_count", "num_virtuous_traits", "num_sinful_traits")):
            raise ValueError("available Rite classification lost native values")
        if (value["trait_count"] != len(rows)
                or value["num_virtuous_traits"] != sum(row["classification"] == 1 for row in rows)
                or value["num_sinful_traits"] != sum(row["classification"] == 2 for row in rows)):
            raise ValueError("native Rite counts differ from actual unweighted rows")
        if current_context["rite_id"] is not None and value["rite_id"] != current_context["rite_id"]:
            raise ValueError("native Rite classification differs from current Rite")
    return {**value, "traits": rows}


def normalize_player_vow_of_poverty_terms_v1(
    value: object, *, current_context: Mapping[str, object],
) -> dict[str, object] | None:
    if value is None:
        return None
    keys = {"schema", "read_only", "available", "unavailable_reason", "capture_epoch",
            "date_raw", "played_character_id", "decision_id", "is_shown", "can_take",
            "affordable", "costs_raw", "raw_scale", "reasons_available", "can_take_reasons"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "ck3_12003_vow_of_poverty_terms_v1"
            or value["read_only"] is not True or type(value["available"]) is not bool
            or value["decision_id"] != "take_vow_of_poverty_decision"
            or type(value["raw_scale"]) is not int or value["raw_scale"] != 100000
            or type(value["reasons_available"]) is not bool):
        raise ValueError("native vow of poverty terms schema is malformed")
    _identity(value, current_context)
    for key in ("is_shown", "can_take", "affordable"):
        if value[key] is not None and type(value[key]) is not bool:
            raise ValueError(f"native vow of poverty predicate is malformed: {key}")
    costs = value["costs_raw"]
    if not isinstance(costs, dict) or set(costs) != {"gold", "treasury", "prestige", "piety"}:
        raise ValueError("native vow of poverty costs are malformed")
    for raw in costs.values():
        if raw is not None and type(raw) is not int:
            raise ValueError("native vow of poverty cost raw is malformed")
    if value["reasons_available"]:
        if not isinstance(value["can_take_reasons"], str):
            raise ValueError("native vow of poverty final reasons are malformed")
    elif value["can_take_reasons"] is not None:
        raise ValueError("native unavailable vow reasons lost their null")
    if value["available"]:
        if (any(value[key] is None for key in ("is_shown", "can_take", "affordable"))
                or any(raw is None for raw in costs.values()) or not value["reasons_available"]):
            raise ValueError("available vow terms lost native final values")
    return {**value, "costs_raw": dict(costs)}
