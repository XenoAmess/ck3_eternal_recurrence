"""Strict contract for journal-backed, post-battle transition observation."""

from __future__ import annotations

from .battle_task_position_context_contract import normalize_current_context_task_position_inputs

from .public_unit_contract import (
    public_cunit_id as _public_cunit_id,
    public_cunit_ids as _public_cunit_ids,
)

from .battle_context_source_inputs_contract import normalize_current_context_source_inputs

import copy
from typing import Final


QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY: Final = (
    "game.command.query-battle-terminal-transition-v1"
)
QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX: Final = (
    "query-battle-terminal-transition-v1-"
)
BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE: Final = (
    "production_exact_battle_terminal_transition"
)

_TOP_FIELDS: Final = {
    "schema_version",
    "contract_stage",
    "status",
    "unavailable_reason",
    "battle_terminal_transition_ready",
    "snapshot_revision",
    "observed_date_raw",
    "prior_combat_id",
    "subject_public_cunit_id",
    "terminal_journal",
    "prior",
    "removal",
    "subject",
    "successor",
}
_TOP_OPTIONAL_EXTENSION_FIELDS: Final = {
    "character_observations", "pending_death_queue",
}
_JOURNAL_FIELDS: Final = {
    "requested_after_sequence",
    "oldest_available_sequence",
    "latest_sequence",
    "event_sequence",
    "event_status",
}
_PRIOR_FIELDS: Final = {
    "combat_id",
    "terminal_kind",
    "terminal_date_raw",
    "suppress_normal_result_envelopes",
    "phase_raw",
    "phase_day",
    "winner_raw",
    "finalized_before",
    "daily_guard_raw",
    "province_id",
    "battle_result_id",
    "wipe_raw",
    "attacker_primary_participant_character_id",
    "defender_primary_participant_character_id",
    "attacker_public_cunit_ids_in_stored_order",
    "defender_public_cunit_ids_in_stored_order",
    "battle_warscore",
}
_PRIOR_OPTIONAL_EXTENSION_FIELDS: Final = {
    "hard_loss_inputs", "side_loss_inputs_in_native_order",
    "side_final_results_in_native_order", "character_result_rows_in_native_order",
    "character_custody_in_observed_order",
}
_SIDE_LOSS_FIELDS: Final = {
    "side_index",
    "baseline_raw_q100000",
    "stored_current_fighting_raw_q100000",
    "levy_soft_raw_q100000",
    "men_at_arms_soft_raw_q100000",
    "hard_loss_raw_q100000",
}
_HARD_LOSS_FIELDS: Final = {
    "losing_side_index",
    "baseline_raw",
    "stored_current_raw",
    "levy_soft_raw",
    "men_at_arms_soft_raw",
    "hard_loss_raw",
}
_WARSCORE_FIELDS: Final = {
    "status",
    "war_id",
    "war_battle_row_index",
    "value_raw_q100000",
    "winner_is_war_attacker",
    "combat_side0_is_war_attacker",
    "attacker_relative_delta_raw_q100000",
}
_WARSCORE_EXTENSION_FIELDS: Final = {
    "denominator_inputs", "selected_cb_battle_scale_raw_q100000"
}
_DENOMINATOR_FIELDS: Final = {"sum_int32", "after_minimum_int32", "participants"}
_DENOMINATOR_PARTICIPANT_FIELDS: Final = {
    "character_id", "buckets_native_add_order_int32"
}
_REMOVAL_FIELDS: Final = {
    "prior_combat_strictly_resolves",
    "prior_province_strictly_resolves",
    "prior_province_contains_prior_combat_id",
    "result_strictly_resolves",
    "result_relevant_player_count",
}
_SUBJECT_FIELDS: Final = {
    "exists",
    "current_province_id",
    "native_carmy_id",
    "combat_backlink_id",
    "active_combat_id",
    "movement_or_retreat_state_raw",
    "move_target_province_id",
    "route_province_ids_in_stored_order",
    "ai_membership_status",
    "coordinator_id",
    "unit_stack_stored_index",
    "subunit_stored_index",
    "blocked_by_active_combat",
}
_SUCCESSOR_FIELDS: Final = {
    "state",
    "matching_combat_ids_in_native_order",
    "selected_successor_combat_id",
    "participant_overlap_public_cunit_ids_in_prior_order",
}
_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_paused",
    "invalid_request",
    "journal_gap",
    "identity_unavailable",
    "state_changed",
    "bounds_exceeded",
}
_TERMINAL_KINDS: Final = {
    "active_not_terminal",
    "normal_result",
    "no_normal_result",
    "unavailable_after_removal",
}
_SUCCESSOR_STATES: Final = {
    "no_successor",
    "residual_new_combat",
    "subject_missing",
    "subject_retreating",
    "subject_assignment_reopened",
    "unavailable",
}
_AI_MEMBERSHIP_STATUSES: Final = {
    "none",
    "observed",
    "unavailable",
}


def _integer(
    value: object,
    field: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{field} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _positive_int32(value: object, field: str) -> int:
    return _integer(value, field, minimum=1, maximum=2**31 - 1)


def _optional_positive_int32(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _positive_int32(value, field)


def _full_component_id(value: object, field: str) -> int:
    result = _integer(value, field, minimum=-(2**31), maximum=2**31 - 1)
    if result == -1:
        raise ValueError(f"{field} must not be the missing-ID sentinel")
    return result


def _optional_full_component_id(value: object, field: str) -> int | None:
    return None if value is None else _full_component_id(value, field)


def _optional_integer(
    value: object,
    field: str,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    if value is None:
        return None
    return _integer(value, field, minimum=minimum, maximum=maximum)


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _optional_boolean(value: object, field: str) -> bool | None:
    if value is None:
        return None
    return _boolean(value, field)


def _exact_dict(
    value: object,
    field: str,
    fields: set[str],
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{field} must contain exactly the v1 fields")
    return value


def _ordered_positive_ids(
    value: object,
    field: str,
    *,
    unique: bool,
) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result = [
        _positive_int32(item, f"{field}[{index}]")
        for index, item in enumerate(value)
    ]
    if unique and len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicate full IDs")
    return result


def _ordered_full_component_ids(
    value: object,
    field: str,
    *,
    unique: bool,
) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result = [
        _full_component_id(item, f"{field}[{index}]")
        for index, item in enumerate(value)
    ]
    if unique and len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicate full IDs")
    return result


def _requested_character_ids(value: object, field: str) -> list[int]:
    if value is None:
        return []
    return list(dict.fromkeys(_ordered_positive_ids(value, field, unique=False)))



def _normalize_raw_numeric_inputs(value: object, field: str) -> dict[str, object] | None:
    """Preserve actual native operands, independently from cached current EC."""
    if value is None:
        return None
    fields = {
        "status", "raw_numeric_inputs_ready", "character_id", "scratch_present",
        "context_source", "base_points", "caps", "prowess_adjustment",
        "category_counts", "scratch_factor_numerator", "scratch_factor_denominator",
        "context", "unavailable_reason",
    }
    if isinstance(value, dict) and "auxiliary_scratch_inputs" in value:
        fields.add("auxiliary_scratch_inputs")
    if isinstance(value, dict) and "nine_cache_byte_inputs" in value:
        fields.add("nine_cache_byte_inputs")
    raw = _exact_dict(value, field, fields)

    def optional_i32(item: object, name: str) -> int | None:
        return _optional_integer(item, name, minimum=-(2**31), maximum=2**31 - 1)

    def array_i32(item: object, name: str, size: int) -> list[int | None]:
        if not isinstance(item, list) or len(item) != size:
            raise ValueError(f"{name} must contain {size} native entries")
        return [optional_i32(v, f"{name}[{i}]") for i, v in enumerate(item)]

    def properties(item: object, name: str) -> tuple[dict[str, object] | None, bool]:
        if item is None:
            return None, False
        p = _exact_dict(item, name, {"count", "keys_u16", "values_q64"})
        count = optional_i32(p["count"], f"{name}.count")
        keys, values = p["keys_u16"], p["values_q64"]
        if keys is not None:
            if not isinstance(keys, list):
                raise ValueError(f"{name}.keys_u16 must be a list or null")
            keys = [_integer(v, f"{name}.keys_u16[{i}]", minimum=0, maximum=65535)
                    for i, v in enumerate(keys)]
        if values is not None:
            if not isinstance(values, list):
                raise ValueError(f"{name}.values_q64 must be a list or null")
            values = [_integer(v, f"{name}.values_q64[{i}]",
                               minimum=-(2**63), maximum=2**63 - 1)
                      for i, v in enumerate(values)]
        for vector in (keys, values):
            if count is not None and vector is not None and len(vector) != max(0, count):
                raise ValueError(f"{name} native count disagrees with copied entries")
        return {"count": count, "keys_u16": keys, "values_q64": values}, (
            count is not None and keys is not None and values is not None)

    context = raw["context"]
    context_complete = False
    if context is not None:
        ctx = _exact_dict(context, f"{field}.context", {
            "aggregate_properties", "weighted_count", "weighted_rows",
        })
        aggregate, aggregate_complete = properties(
            ctx["aggregate_properties"], f"{field}.context.aggregate_properties")
        count = optional_i32(ctx["weighted_count"], f"{field}.context.weighted_count")
        rows = ctx["weighted_rows"]
        rows_complete = rows is not None
        if rows is not None:
            if not isinstance(rows, list):
                raise ValueError(f"{field}.context.weighted_rows must be a list or null")
            if count is not None and len(rows) != max(0, count):
                raise ValueError(f"{field}.context weighted count disagrees")
            copied = []
            for i, row in enumerate(rows):
                row_field = f"{field}.context.weighted_rows[{i}]"
                row = _exact_dict(row, row_field, {"native_index", "properties", "weight_q64"})
                index = _integer(row["native_index"], f"{row_field}.native_index",
                                 minimum=i, maximum=i)
                weight = _optional_integer(row["weight_q64"], f"{row_field}.weight_q64",
                                           minimum=-(2**63), maximum=2**63 - 1)
                prop, prop_complete = properties(row["properties"], f"{row_field}.properties")
                rows_complete = rows_complete and prop_complete and weight is not None
                copied.append({"native_index": index, "properties": prop, "weight_q64": weight})
            rows = copied
        context = {"aggregate_properties": aggregate, "weighted_count": count,
                   "weighted_rows": rows}
        context_complete = aggregate_complete and count is not None and rows_complete
    scratch = _optional_boolean(raw["scratch_present"], f"{field}.scratch_present")
    normalized = {
        **raw,
        "character_id": _positive_int32(raw["character_id"], f"{field}.character_id"),
        "scratch_present": scratch,
        "base_points": array_i32(raw["base_points"], f"{field}.base_points", 6),
        "caps": array_i32(raw["caps"], f"{field}.caps", 6),
        "category_counts": array_i32(raw["category_counts"], f"{field}.category_counts", 4),
        "context": context,
    }
    for key in ("prowess_adjustment", "scratch_factor_numerator", "scratch_factor_denominator"):
        normalized[key] = optional_i32(raw[key], f"{field}.{key}")
    if raw["context_source"] not in {
        "model_inline", "fallback_static", "not_required_no_scratch", "unavailable",
    }:
        raise ValueError(f"{field}.context_source is invalid")
    ready = _boolean(raw["raw_numeric_inputs_ready"], f"{field}.raw_numeric_inputs_ready")
    complete = scratch is False or (scratch is True and context_complete
        and all(v is not None for key in ("base_points", "caps", "category_counts")
                for v in normalized[key])
        and all(normalized[k] is not None for k in (
            "prowess_adjustment", "scratch_factor_numerator", "scratch_factor_denominator")))
    status, reason = raw["status"], raw["unavailable_reason"]
    if status not in {"available", "partial", "unavailable"} or ready is not (status == "available"):
        raise ValueError(f"{field} raw numeric availability disagrees")
    if ready is not complete or (ready and reason is not None) or (
        not ready and (not isinstance(reason, str) or not reason)
    ):
        raise ValueError(f"{field} raw numeric completeness disagrees")
    if "auxiliary_scratch_inputs" in raw:
        normalized["auxiliary_scratch_inputs"] = _normalize_auxiliary_scratch_inputs(
            raw["auxiliary_scratch_inputs"], f"{field}.auxiliary_scratch_inputs", scratch)
    if "nine_cache_byte_inputs" in raw:
        normalized["nine_cache_byte_inputs"] = _normalize_nine_cache_byte_inputs(
            raw["nine_cache_byte_inputs"], f"{field}.nine_cache_byte_inputs", scratch)
    return normalized


def _normalize_auxiliary_scratch_inputs(
    value: object, field: str, scratch_present: bool | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _exact_dict(value, field, {
        "status", "ready", "base430_q64", "base438_q64", "selector_flag_raw",
        "selector_metric_raw", "selected_low_threshold_raw", "selected_high_threshold_raw",
        "prepared430_q64", "prepared438_q64", "copied430_q64", "copied438_q64",
        "ready440_raw", "unavailable_reason",
    })
    out = dict(raw)
    for key in ("base430_q64", "base438_q64", "prepared430_q64", "prepared438_q64",
                "copied430_q64", "copied438_q64"):
        out[key] = _optional_integer(raw[key], f"{field}.{key}",
                                     minimum=-(2**63), maximum=2**63 - 1)
    for key in ("selector_flag_raw", "ready440_raw"):
        out[key] = _optional_integer(raw[key], f"{field}.{key}", minimum=0, maximum=255)
    out["selector_metric_raw"] = _optional_integer(
        raw["selector_metric_raw"], f"{field}.selector_metric_raw",
        minimum=-(2**15), maximum=2**15 - 1)
    for key in ("selected_low_threshold_raw", "selected_high_threshold_raw"):
        out[key] = _optional_integer(raw[key], f"{field}.{key}",
                                     minimum=-(2**31), maximum=2**31 - 1)
    metric, low, high = (out[k] for k in (
        "selector_metric_raw", "selected_low_threshold_raw", "selected_high_threshold_raw"))
    inputs = ("base430_q64", "base438_q64", "selector_flag_raw", "selector_metric_raw",
              "selected_low_threshold_raw", "prepared430_q64", "prepared438_q64",
              "copied430_q64", "copied438_q64", "ready440_raw")
    complete = scratch_present is False or (scratch_present is True
        and all(out[k] is not None for k in inputs)
        and (metric < low or high is not None))
    ready = _boolean(raw["ready"], f"{field}.ready")
    status, reason = raw["status"], raw["unavailable_reason"]
    if status not in {"available", "partial", "unavailable"} or ready is not (status == "available"):
        raise ValueError(f"{field} auxiliary scratch availability disagrees")
    if ready is not complete or (ready and reason is not None) or (
        not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError(f"{field} auxiliary scratch completeness disagrees")
    return out


def _normalize_nine_cache_byte_inputs(
    value: object, field: str, scratch_present: bool | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _exact_dict(value, field, {
        "status", "ready", "model_present", "aggregate_properties", "carrier278_present",
        "carrier278_magic_raw", "linked20_present", "used_native_definition_fallback",
        "selected_definition_present", "selected_definition_magic_raw",
        "selected_definition_keys_u16", "current_cache_present", "current_cache_bytes",
        "unavailable_reason",
    })
    out = dict(raw)
    for key in ("model_present", "carrier278_present", "linked20_present",
                "used_native_definition_fallback", "selected_definition_present", "current_cache_present"):
        out[key] = _optional_boolean(raw[key], f"{field}.{key}")
    for key in ("carrier278_magic_raw", "selected_definition_magic_raw"):
        out[key] = _optional_integer(raw[key], f"{field}.{key}", minimum=0, maximum=2**32 - 1)
    for key, minimum, maximum in (("selected_definition_keys_u16", 0, 65535),
                                  ("current_cache_bytes", -128, 127)):
        items = raw[key]
        if items is not None:
            if not isinstance(items, list) or len(items) != 9:
                raise ValueError(f"{field}.{key} must contain nine native occurrences")
            out[key] = [_integer(item, f"{field}.{key}[{i}]", minimum=minimum, maximum=maximum)
                        for i, item in enumerate(items)]
    properties = raw["aggregate_properties"]
    properties_complete = False
    if properties is not None:
        p = _exact_dict(properties, f"{field}.aggregate_properties", {"count", "keys_u16", "values_q64"})
        count = _optional_integer(p["count"], f"{field}.aggregate_properties.count",
                                  minimum=-(2**31), maximum=2**31 - 1)
        p = dict(p, count=count)
        for key, minimum, maximum in (("keys_u16", 0, 65535), ("values_q64", -(2**63), 2**63 - 1)):
            if p[key] is not None:
                if not isinstance(p[key], list):
                    raise ValueError(f"{field}.aggregate_properties.{key} must be a list or null")
                p[key] = [_integer(item, f"{field}.aggregate_properties.{key}[{i}]",
                                   minimum=minimum, maximum=maximum) for i, item in enumerate(p[key])]
                if count is not None and len(p[key]) != max(0, count):
                    raise ValueError(f"{field}.aggregate_properties native count disagrees")
        properties_complete = count is not None and p["keys_u16"] is not None and p["values_q64"] is not None
        out["aggregate_properties"] = p
    first_magic, second_magic = out["carrier278_magic_raw"], out["selected_definition_magic_raw"]
    optional_complete = out["carrier278_present"] is True and first_magic is not None and (
        first_magic != 0x41495374 or (out["linked20_present"] is not None
        and out["used_native_definition_fallback"] is (out["linked20_present"] is False)
        and out["selected_definition_present"] is True and second_magic is not None
        and (second_magic != 0x4744624F or out["selected_definition_keys_u16"] is not None)))
    complete = scratch_present is False or (scratch_present is True
        and out["model_present"] is True and properties_complete and optional_complete)
    ready = _boolean(raw["ready"], f"{field}.ready")
    status, reason = raw["status"], raw["unavailable_reason"]
    if status not in {"available", "partial", "unavailable"} or ready is not (status == "available"):
        raise ValueError(f"{field} nine-byte input availability disagrees")
    if ready is not complete or (ready and reason is not None) or (
        not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError(f"{field} nine-byte input completeness disagrees")
    return out


def _normalize_title_census_inputs(value: object, field: str) -> dict[str, object] | None:
    if value is None:
        return None
    raw = _exact_dict(value, field, {
        "status", "ready", "character_id", "scratch_present", "model_present",
        "model_owner_present", "model_owner_full_character_id_raw_i32",
        "model_owner_matches_character", "model_magic_raw_u32", "header_source",
        "title_count_raw_i32", "title_occurrences", "unavailable_reason",
    })
    def i32(item: object, name: str) -> int | None:
        return _optional_integer(item, field + "." + name, minimum=-(2**31), maximum=2**31-1)
    result = dict(raw)
    result["character_id"] = _positive_int32(raw["character_id"], field + ".character_id")
    result["scratch_present"] = _boolean(raw["scratch_present"], field + ".scratch_present")
    for key in ("model_present", "model_owner_present", "model_owner_matches_character"):
        result[key] = _optional_boolean(raw[key], field + "." + key)
    for key in ("model_owner_full_character_id_raw_i32", "title_count_raw_i32"):
        result[key] = i32(raw[key], key)
    result["model_magic_raw_u32"] = _optional_integer(raw["model_magic_raw_u32"],
        field + ".model_magic_raw_u32", minimum=0, maximum=2**32-1)
    if raw["header_source"] not in {"landed", "static"}:
        raise ValueError(field + ".header_source is invalid")
    rows_value = raw["title_occurrences"]
    rows = None
    complete = result["title_count_raw_i32"] is not None and result["title_count_raw_i32"] >= 0
    if result["scratch_present"]:
        complete = complete and result["model_present"] is not None
        if result["model_present"] is True:
            complete = complete and result["model_owner_present"] is not None and result["model_owner_matches_character"] is not None
            if result["model_owner_present"] is True:
                complete = complete and result["model_owner_full_character_id_raw_i32"] is not None
            if result["model_owner_matches_character"] is True:
                complete = complete and result["model_magic_raw_u32"] is not None
    if rows_value is not None:
        if not isinstance(rows_value, list):
            raise ValueError(field + ".title_occurrences must be a list or null")
        rows = []
        for i, item in enumerate(rows_value):
            name = f"{field}.title_occurrences[{i}]"
            row = _exact_dict(item, name, {
                "native_row_index", "requested_full_title_id_raw_i32", "resolution",
                "resolved_full_title_id_raw_i32", "qualifier_1d8_raw_u8",
                "qualifier_130_raw_u8", "qualifier_12c_raw_i32", "government_bit14",
                "template_tier_raw_i32",
            })
            row = dict(row)
            if _integer(row["native_row_index"], name + ".native_row_index", minimum=0, maximum=2**31-1) != i:
                raise ValueError(name + " native row order disagrees")
            row["requested_full_title_id_raw_i32"] = _integer(row["requested_full_title_id_raw_i32"],
                name + ".requested_full_title_id_raw_i32", minimum=-(2**31), maximum=2**31-1)
            for key in ("resolved_full_title_id_raw_i32", "qualifier_12c_raw_i32", "template_tier_raw_i32"):
                row[key] = i32(row[key], f"title_occurrences[{i}].{key}")
            for key in ("qualifier_1d8_raw_u8", "qualifier_130_raw_u8"):
                row[key] = _optional_integer(row[key], name + "." + key, minimum=0, maximum=255)
            row["government_bit14"] = _optional_boolean(row["government_bit14"], name + ".government_bit14")
            if row["resolution"] not in {"matched", "fallback", "unavailable"}:
                raise ValueError(name + " resolution is invalid")
            row_complete = row["resolution"] != "unavailable" and row["resolved_full_title_id_raw_i32"] is not None
            demanded = row_complete
            for key, expected in (("qualifier_1d8_raw_u8", 0), ("qualifier_130_raw_u8", 0),
                                  ("qualifier_12c_raw_i32", -1)):
                if demanded:
                    row_complete = row_complete and row[key] is not None
                    demanded = row[key] == expected
            if demanded:
                row_complete = row_complete and row["government_bit14"] is not None
                if row["government_bit14"] is True:
                    row_complete = row_complete and row["template_tier_raw_i32"] is not None
            complete = complete and row_complete
            rows.append(row)
    else:
        complete = False
    if rows is not None and result["title_count_raw_i32"] is not None and len(rows) != max(result["title_count_raw_i32"], 0):
        raise ValueError(field + " occurrence count disagrees")
    result["title_occurrences"] = rows
    ready = _boolean(raw["ready"], field + ".ready")
    if raw["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError(field + " status is invalid")
    if ready != complete or (raw["status"] == "available") != ready:
        raise ValueError(field + " readiness disagrees with demanded census operands")
    reason = raw["unavailable_reason"]
    if ((ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason))):
        raise ValueError(field + " reason disagrees with readiness")
    return result


def _normalize_context_branch_inputs(value: object, field: str) -> dict[str, object] | None:
    """Keep actual readonly291D1D0 operands distinct from final context/EC."""
    if value is None:
        return None
    fields = {
        "status", "ready", "character_id", "flag14", "selected_index",
        "selected_property_block", "group_counts", "group_property_blocks",
        "unavailable_reason",
    }
    if isinstance(value, dict) and "census_inputs" in value:
        fields.add("census_inputs")
    raw = _exact_dict(value, field, fields)

    def properties(item: object, name: str) -> dict[str, object] | None:
        if item is None:
            return None
        block = _exact_dict(item, name, {"count", "keys_u16", "values_q64"})
        count = _optional_integer(block["count"], name + ".count", minimum=-(2**31), maximum=2**31 - 1)
        keys = block["keys_u16"]
        values = block["values_q64"]
        if keys is not None:
            if not isinstance(keys, list):
                raise ValueError(name + ".keys_u16 must be a list or null")
            keys = [_integer(key, name + ".keys_u16", minimum=0, maximum=65535) for key in keys]
        if values is not None:
            if not isinstance(values, list):
                raise ValueError(name + ".values_q64 must be a list or null")
            values = [_integer(v, name + ".values_q64", minimum=-(2**63), maximum=2**63 - 1) for v in values]
        if count is not None:
            expected = max(count, 0)
            if ((keys is not None and len(keys) != expected)
                    or (values is not None and len(values) != expected)):
                raise ValueError(name + " copied arrays disagree with native count")
        return {"count": count, "keys_u16": keys, "values_q64": values}

    def complete(block: dict[str, object] | None) -> bool:
        return block is not None and all(block[key] is not None for key in ("count", "keys_u16", "values_q64"))

    flag = _optional_boolean(raw["flag14"], field + ".flag14")
    selected_index = _optional_integer(raw["selected_index"], field + ".selected_index", minimum=-(2**31), maximum=2**31 - 1)
    selected = properties(raw["selected_property_block"], field + ".selected_property_block")
    counts_value = raw["group_counts"]
    blocks_value = raw["group_property_blocks"]
    if not isinstance(counts_value, list) or len(counts_value) != 7:
        raise ValueError(field + ".group_counts must contain seven native entries")
    if not isinstance(blocks_value, list) or len(blocks_value) != 7:
        raise ValueError(field + ".group_property_blocks must contain seven native entries")
    counts = [_optional_integer(c, field + ".group_counts", minimum=-(2**31), maximum=2**31 - 1) for c in counts_value]
    blocks = [properties(block, field + f".group_property_blocks[{i}]") for i, block in enumerate(blocks_value)]
    ready = _boolean(raw["ready"], field + ".ready")
    consumed_complete = (flag is not None
        and (flag is False or (selected_index is not None and complete(selected)))
        and all(count is not None and (count <= 0 or complete(block)) for count, block in zip(counts, blocks)))
    status, reason = raw["status"], raw["unavailable_reason"]
    if status not in {"available", "partial", "unavailable"}:
        raise ValueError(field + " status is invalid")
    if ready != consumed_complete or (status == "available") != ready:
        raise ValueError(field + " readiness disagrees with consumed native operands")
    if ((ready and reason is not None)
            or (not ready and (not isinstance(reason, str) or not reason))):
        raise ValueError(field + " reason disagrees with readiness")
    result = {"status": status, "ready": ready,
        "character_id": _positive_int32(raw["character_id"], field + ".character_id"),
        "flag14": flag, "selected_index": selected_index,
        "selected_property_block": selected, "group_counts": counts,
        "group_property_blocks": blocks, "unavailable_reason": reason}
    if "census_inputs" in raw:
        result["census_inputs"] = _normalize_title_census_inputs(raw["census_inputs"], field + ".census_inputs")
        census = result["census_inputs"]
        if census is not None and census["character_id"] != result["character_id"]:
            raise ValueError(field + " census receiver disagrees with queried actor")
    return result


def _normalize_current_prior_context_inputs(value: object, field: str) -> dict[str, object] | None:
    """Copy current native provider-prefix sources, independently of final context."""
    if value is None:
        return None
    raw = _exact_dict(value, field, {
        "available", "reason", "character_full_id", "base_property_block",
        "common_property_blocks", "selector", "selected_property_blocks",
    })

    def block(value: object, name: str) -> dict[str, object] | None:
        if value is None:
            return None
        value = _exact_dict(value, name, {"rows"})
        rows = value["rows"]
        if not isinstance(rows, list):
            raise ValueError(name + ".rows must be a list")
        copied = []
        for i, row in enumerate(rows):
            row_name = name + f".rows[{i}]"
            row = _exact_dict(row, row_name, {"key", "value_raw"})
            copied.append({
                "key": _integer(row["key"], row_name + ".key", minimum=0, maximum=65535),
                "value_raw": _integer(row["value_raw"], row_name + ".value_raw",
                                      minimum=-(2**63), maximum=2**63 - 1),
            })
        return {"rows": copied}

    def blocks(value: object, name: str) -> list[dict[str, object] | None] | None:
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError(name + " must be a list or null")
        return [block(item, name + f"[{i}]") for i, item in enumerate(value)]

    base = block(raw["base_property_block"], field + ".base_property_block")
    common = blocks(raw["common_property_blocks"], field + ".common_property_blocks")
    selected = blocks(raw["selected_property_blocks"], field + ".selected_property_blocks")
    selector = _exact_dict(raw["selector"], field + ".selector", {
        "available", "uses_18f8_source", "selected_header_offset",
    })
    selector_available = _boolean(selector["available"], field + ".selector.available")
    uses_18f8 = _optional_boolean(selector["uses_18f8_source"], field + ".selector.uses_18f8_source")
    offset = _optional_integer(selector["selected_header_offset"], field + ".selector.selected_header_offset",
                               minimum=-(2**31), maximum=2**31 - 1)
    if selector_available:
        if uses_18f8 is None or offset != (0x18F8 if uses_18f8 else 0x19A0):
            raise ValueError(field + " native selector/header disagrees")
    elif uses_18f8 is not None or offset is not None:
        raise ValueError(field + " unavailable selector has a selection")
    available = _boolean(raw["available"], field + ".available")
    complete = (base is not None and common is not None and all(item is not None for item in common)
                and selector_available and selected is not None and all(item is not None for item in selected))
    reason = raw["reason"]
    if (available != complete or (available and reason is not None)
            or (not available and (not isinstance(reason, str) or not reason))):
        raise ValueError(field + " availability disagrees with observed prefix sources")
    return {"available": available, "reason": reason,
            "character_full_id": _positive_int32(raw["character_full_id"], field + ".character_full_id"),
            "base_property_block": base, "common_property_blocks": common,
            "selector": {"available": selector_available, "uses_18f8_source": uses_18f8,
                         "selected_header_offset": offset},
            "selected_property_blocks": selected}


def _normalize_pending_death_queue(value: object) -> dict[str, object] | None:
    """Copy current ordered native storage; do not infer callback or commit."""
    if value is None:
        return None
    field = "battle_terminal_transition.pending_death_queue"
    queue = _exact_dict(value, field, {
        "status", "unavailable_reason", "source_state_pointer_present",
        "manager_owner_pointer_present", "execution_mode_raw",
        "data_pointer_present", "capacity_raw", "count_raw", "rows",
    })

    def observed_status(row: dict[str, object], path: str) -> None:
        status, reason = row["status"], row["unavailable_reason"]
        if status == "available":
            if reason is not None:
                raise ValueError(path + " available read has unavailable_reason")
        elif status == "unavailable":
            if type(reason) is not str or not reason:
                raise ValueError(path + " unavailable read needs its reason")
        else:
            raise ValueError(path + ".status is invalid")

    observed_status(queue, field)
    normalized = copy.deepcopy(queue)
    for key in ("source_state_pointer_present", "manager_owner_pointer_present",
                "data_pointer_present"):
        normalized[key] = _optional_boolean(queue[key], field + "." + key)
    normalized["execution_mode_raw"] = _optional_integer(
        queue["execution_mode_raw"], field + ".execution_mode_raw",
        minimum=0, maximum=255,
    )
    for key in ("capacity_raw", "count_raw"):
        normalized[key] = _optional_integer(
            queue[key], field + "." + key,
            minimum=-(2**31), maximum=2**31 - 1,
        )
    if queue["rows"] is None:
        return normalized
    if type(queue["rows"]) is not list:
        raise ValueError(field + ".rows must be a list or null")
    rows = []
    for index, value in enumerate(queue["rows"]):
        path = field + f".rows[{index}]"
        row = _exact_dict(value, path, {
            "status", "unavailable_reason", "row_index",
            "victim_pointer_present", "victim_full_character_id_raw",
            "victim_death_data_pointer_present", "reason_pointer_present",
            "reason_key", "date_object_raw_u64", "killer_pointer_present",
            "killer_full_character_id_raw", "artifact_pointer_present",
            "artifact_full_id_raw",
        })
        observed_status(row, path)
        result = copy.deepcopy(row)
        result["row_index"] = _integer(
            row["row_index"], path + ".row_index", minimum=0, maximum=2**31 - 1,
        )
        for key in ("victim_pointer_present", "victim_death_data_pointer_present",
                    "reason_pointer_present", "killer_pointer_present",
                    "artifact_pointer_present"):
            result[key] = _optional_boolean(row[key], path + "." + key)
        for key in ("victim_full_character_id_raw", "killer_full_character_id_raw",
                    "artifact_full_id_raw"):
            result[key] = _optional_integer(
                row[key], path + "." + key,
                minimum=-(2**31), maximum=2**31 - 1,
            )
        result["date_object_raw_u64"] = _optional_integer(
            row["date_object_raw_u64"], path + ".date_object_raw_u64",
            minimum=0, maximum=2**64 - 1,
        )
        if row["reason_key"] is not None and type(row["reason_key"]) is not str:
            raise ValueError(path + ".reason_key must be a string or null")
        rows.append(result)
    normalized["rows"] = rows
    return normalized


def _normalize_current_stored_context_state(
    value: object, field: str,
) -> dict[str, object] | None:
    """Preserve independently observed current stored descriptors and arrays."""
    if value is None:
        return None
    raw = _exact_dict(value, field, {
        "available", "reason", "character_full_id", "scratch_present",
        "scratch_address", "model_present", "model_address", "context_address",
        "owner_address", "owner_character_full_id", "bound_to_requested_character",
        "pending_raw", "owned_count_raw", "weighted", "key_array", "value_array",
        "reset_input",
    })

    def integer(item: object, name: str, minimum: int, maximum: int) -> int | None:
        return _optional_integer(item, name, minimum=minimum, maximum=maximum)

    def array(item: object, name: str, kind: str) -> dict[str, object] | None:
        if item is None:
            return None
        source = _exact_dict(item, name, {"data_address", "capacity_raw", "count", "items"})
        count = integer(source["count"], name + ".count", -(2**31), 2**31 - 1)
        items = source["items"]
        if items is not None:
            if not isinstance(items, list):
                raise ValueError(name + ".items must be a list or null")
            if count is None or count < 0 or len(items) != count:
                raise ValueError(name + ".items must retain its native active count")
            copied = []
            for index, entry in enumerate(items):
                entry_name = f"{name}.items[{index}]"
                if kind == "weighted":
                    row = _exact_dict(entry, entry_name, {"native_index", "weight_raw", "property_block"})
                    native_index = _integer(row["native_index"], entry_name + ".native_index",
                                            minimum=0, maximum=2**31 - 1)
                    if native_index != index:
                        raise ValueError(entry_name + " native index/order disagrees")
                    block = row["property_block"]
                    if block is not None:
                        block = _exact_dict(block, entry_name + ".property_block", {"key_array", "value_array"})
                        block = {
                            "key_array": array(block["key_array"], entry_name + ".property_block.key_array", "key"),
                            "value_array": array(block["value_array"], entry_name + ".property_block.value_array", "value"),
                        }
                    copied.append({"native_index": native_index,
                                   "weight_raw": integer(row["weight_raw"], entry_name + ".weight_raw", -(2**63), 2**63 - 1),
                                   "property_block": block})
                else:
                    minimum, maximum = (0, 2**16 - 1) if kind == "key" else (-(2**63), 2**63 - 1)
                    copied.append(_integer(entry, entry_name, minimum=minimum, maximum=maximum))
            items = copied
        return {"data_address": integer(source["data_address"], name + ".data_address", 0, 2**64 - 1),
                "capacity_raw": integer(source["capacity_raw"], name + ".capacity_raw", 0, 2**32 - 1),
                "count": count, "items": items}

    available = _boolean(raw["available"], field + ".available")
    reason = raw["reason"]
    if ((available and reason is not None)
            or (not available and (not isinstance(reason, str) or not reason))):
        raise ValueError(field + " current observation availability/reason disagrees")
    result = {"available": available, "reason": reason,
              "character_full_id": _positive_int32(raw["character_full_id"], field + ".character_full_id")}
    for name in ("scratch_present", "model_present", "bound_to_requested_character"):
        result[name] = _optional_boolean(raw[name], field + "." + name)
    for name in ("scratch_address", "model_address", "context_address", "owner_address"):
        result[name] = integer(raw[name], field + "." + name, 0, 2**64 - 1)
    for name in ("owner_character_full_id", "owned_count_raw"):
        result[name] = integer(raw[name], field + "." + name, -(2**31), 2**31 - 1)
    result["pending_raw"] = integer(raw["pending_raw"], field + ".pending_raw", 0, 255)
    result["weighted"] = array(raw["weighted"], field + ".weighted", "weighted")
    result["key_array"] = array(raw["key_array"], field + ".key_array", "key")
    result["value_array"] = array(raw["value_array"], field + ".value_array", "value")
    reset = _exact_dict(raw["reset_input"], field + ".reset_input", {"weighted_count_nonzero"})
    result["reset_input"] = {"weighted_count_nonzero": _optional_boolean(
        reset["weighted_count_nonzero"], field + ".reset_input.weighted_count_nonzero")}
    return result


def _normalize_current_person_state(
    value: object, field: str,
) -> dict[str, object]:
    """Validate independently observed current-person leaves."""
    fields = {"scope", "effective_prowess", "injury_traits"}
    if isinstance(value, dict) and "death_record" in value:
        fields.add("death_record")
    if isinstance(value, dict) and "raw_numeric_inputs" in value:
        fields.add("raw_numeric_inputs")
    if isinstance(value, dict) and "current_context_task_position_inputs" in value:
        fields.add("current_context_task_position_inputs")
    if isinstance(value, dict) and "context_branch_inputs" in value:
        fields.add("context_branch_inputs")
    if isinstance(value, dict) and "current_prior_context_inputs" in value:
        fields.add("current_prior_context_inputs")
    if isinstance(value, dict) and "current_stored_context_state" in value:
        fields.add("current_stored_context_state")
    if isinstance(value, dict) and "current_context_source_inputs" in value:
        fields.add("current_context_source_inputs")
    if isinstance(value, dict) and "carrier_1c8_b70_direct" in value:
        fields.add("carrier_1c8_b70_direct")
    if isinstance(value, dict) and "following_2921a90" in value:
        fields.add("following_2921a90")
    if isinstance(value, dict) and "following_2921a90_conditional" in value:
        fields.add("following_2921a90_conditional")
    state = _exact_dict(value, field, fields)
    if state["scope"] != "current_character":
        raise ValueError(f"{field}.scope must be current_character")
    prowess = _exact_dict(state["effective_prowess"], f"{field}.effective_prowess", {
        "status", "points", "unavailable_reason",
    })
    points = _optional_integer(
        prowess["points"], f"{field}.effective_prowess.points",
        minimum=-(2**31), maximum=2**31 - 1,
    )
    prowess_status = prowess["status"]
    prowess_reason = prowess["unavailable_reason"]
    if prowess_status == "available":
        if points is None or prowess_reason is not None:
            raise ValueError(f"{field} available prowess disagrees")
    elif prowess_status == "unavailable":
        if points is not None or not isinstance(prowess_reason, str) or not prowess_reason:
            raise ValueError(f"{field} unavailable prowess disagrees")
    else:
        raise ValueError(f"{field} prowess status is invalid")
    injury = _exact_dict(state["injury_traits"], f"{field}.injury_traits", {
        "status", "flags", "wounded_rank", "unavailable_reason",
        "wounded_rank_unavailable_reason",
    })
    keys = (
        "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
        "one_eyed", "disfigured", "incapable",
    )
    flags = _exact_dict(injury["flags"], f"{field}.injury_traits.flags", set(keys))
    flags = {
        key: _optional_boolean(flags[key], f"{field}.injury_traits.flags.{key}")
        for key in keys
    }
    observed = sum(flag is not None for flag in flags.values())
    expected_status = "available" if observed == 8 else "partial" if observed else "unavailable"
    injury_reason = injury["unavailable_reason"]
    if (injury["status"] != expected_status
        or (observed == 8 and injury_reason is not None)
        or (observed != 8 and (not isinstance(injury_reason, str) or not injury_reason))):
        raise ValueError(f"{field} injury availability disagrees")
    rank = _optional_integer(
        injury["wounded_rank"], f"{field}.injury_traits.wounded_rank",
        minimum=0, maximum=3,
    )
    wound_flags = [flags[key] for key in keys[:3]]
    matches = [index + 1 for index, flag in enumerate(wound_flags) if flag is True]
    rank_observed = all(flag is not None for flag in wound_flags) and len(matches) <= 1
    expected_rank = (matches[0] if matches else 0) if rank_observed else None
    rank_reason = injury["wounded_rank_unavailable_reason"]
    if (rank != expected_rank
        or (rank_observed and rank_reason is not None)
        or (not rank_observed and (not isinstance(rank_reason, str) or not rank_reason))):
        raise ValueError(f"{field} wounded rank disagrees with observed flags")
    normalized = {
        "scope": "current_character",
        "effective_prowess": {**prowess, "points": points},
        "injury_traits": {**injury, "flags": flags, "wounded_rank": rank},
    }
    if "death_record" in state:
        death_fields = {"status", "reason_key", "unavailable_reason"}
        metadata_fields = {"date_object_raw_u64", "killer_full_character_id_raw",
                           "artifact_full_id_raw"}
        if isinstance(state["death_record"], dict):
            death_fields |= metadata_fields & state["death_record"].keys()
        death = _exact_dict(state["death_record"], f"{field}.death_record", death_fields)
        status, key, reason = (death["status"], death["reason_key"],
                               death["unavailable_reason"])
        if key is not None and type(key) is not str:
            raise ValueError(f"{field}.death_record.reason_key must be a string or null")
        if status == "none":
            if key is not None or reason is not None:
                raise ValueError(f"{field} absent death record disagrees")
        elif status == "available":
            if reason is not None:
                raise ValueError(f"{field} available death record disagrees")
        elif status == "unavailable":
            if key is not None or type(reason) is not str or not reason:
                raise ValueError(f"{field} unavailable death record disagrees")
        else:
            raise ValueError(f"{field} death record status is invalid")
        normalized_death = dict(death)
        for name in metadata_fields & death.keys():
            normalized_death[name] = _optional_integer(
                death[name], f"{field}.death_record.{name}",
                minimum=0 if name == "date_object_raw_u64" else -(2**31),
                maximum=2**64 - 1 if name == "date_object_raw_u64" else 2**31 - 1,
            )
        normalized["death_record"] = normalized_death
    if "raw_numeric_inputs" in state:
        normalized["raw_numeric_inputs"] = _normalize_raw_numeric_inputs(
            state["raw_numeric_inputs"], f"{field}.raw_numeric_inputs")
    if "context_branch_inputs" in state:
        normalized["context_branch_inputs"] = _normalize_context_branch_inputs(
            state["context_branch_inputs"], f"{field}.context_branch_inputs")
    if "current_prior_context_inputs" in state:
        normalized["current_prior_context_inputs"] = _normalize_current_prior_context_inputs(
            state["current_prior_context_inputs"], f"{field}.current_prior_context_inputs")
    if "current_stored_context_state" in state:
        normalized["current_stored_context_state"] = _normalize_current_stored_context_state(
            state["current_stored_context_state"], f"{field}.current_stored_context_state")
    if "current_context_source_inputs" in state:
        normalized["current_context_source_inputs"] = normalize_current_context_source_inputs(
            state["current_context_source_inputs"], f"{field}.current_context_source_inputs")
    if "current_context_task_position_inputs" in state:
        normalized["current_context_task_position_inputs"] = normalize_current_context_task_position_inputs(
            state["current_context_task_position_inputs"], f"{field}.current_context_task_position_inputs")
    if "carrier_1c8_b70_direct" in state:
        from .battle_person_carrier_direct_12004 import normalize_carrier_direct_12004
        normalized["carrier_1c8_b70_direct"] = normalize_carrier_direct_12004(
            state["carrier_1c8_b70_direct"])
    if "following_2921a90" in state:
        from .battle_person_following_2921a90_12004 import normalize_person_following_2921a90_12004
        normalized["following_2921a90"] = normalize_person_following_2921a90_12004(
            state["following_2921a90"])
    if "following_2921a90_conditional" in state:
        from .battle_person_conditional_2921a90_12004 import normalize_person_conditional_2921a90_12004
        normalized["following_2921a90_conditional"] = normalize_person_conditional_2921a90_12004(
            state["following_2921a90_conditional"])
    return normalized


def _normalize_character_custody_rows(
    value: object, field: str, *, allow_current_person_state: bool = False,
) -> list[dict[str, object]] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list or null")
    result = []
    for index, value in enumerate(value):
        fields = {"character_id", "status", "actual_jailer_character_id"}
        if isinstance(value, dict) and "alive" in value:
            fields.add("alive")
        if (allow_current_person_state and isinstance(value, dict)
            and "current_person_state" in value):
            fields.add("current_person_state")
        row = _exact_dict(value, f"{field}[{index}]", fields)
        character_id = _positive_int32(row["character_id"], f"{field} character")
        status = row["status"]
        jailer = _optional_integer(
            row["actual_jailer_character_id"], f"{field} jailer",
            minimum=-1, maximum=2**31 - 1,
        )
        if (status not in {"observed", "none", "unavailable"}
            or (status == "observed" and (jailer is None or jailer <= 0))
            or (status == "none" and jailer != -1)
            or (status == "unavailable" and jailer is not None)):
            raise ValueError(f"{field} custody state disagrees")
        normalized = {"character_id": character_id, "status": status,
                      "actual_jailer_character_id": jailer}
        if "alive" in row:
            normalized["alive"] = _optional_boolean(row["alive"], f"{field} alive")
        if "current_person_state" in row:
            normalized["current_person_state"] = _normalize_current_person_state(
                row["current_person_state"], f"{field}[{index}].current_person_state"
            )
            raw = normalized["current_person_state"].get("raw_numeric_inputs")
            if raw is not None and raw["character_id"] != character_id:
                raise ValueError(f"{field}[{index}] raw numeric CharacterID disagrees")
            task_position = normalized["current_person_state"].get("current_context_task_position_inputs")
            if task_position is not None and task_position["character_id"] != character_id:
                raise ValueError(f"{field}[{index}] task/position CharacterID disagrees")
            branch = normalized["current_person_state"].get("context_branch_inputs")
            if branch is not None and branch["character_id"] != character_id:
                raise ValueError(f"{field}[{index}] context branch CharacterID disagrees")
            prior = normalized["current_person_state"].get("current_prior_context_inputs")
            if prior is not None and prior["character_full_id"] != character_id:
                raise ValueError(f"{field}[{index}] prior context CharacterID disagrees")
            stored = normalized["current_person_state"].get("current_stored_context_state")
            if stored is not None and stored["character_full_id"] != character_id:
                raise ValueError(f"{field}[{index}] stored context CharacterID disagrees")
            sources = normalized["current_person_state"].get("current_context_source_inputs")
            if sources is not None and sources["character_id"] != character_id:
                raise ValueError(f"{field}[{index}] context source CharacterID disagrees")
            carrier = normalized["current_person_state"].get("carrier_1c8_b70_direct")
            if (carrier is not None and carrier["character_id"] is not None
                    and carrier["character_id"] != character_id):
                raise ValueError(f"{field}[{index}] direct carrier CharacterID disagrees")
            following = normalized["current_person_state"].get("following_2921a90")
            if (following is not None and following["character_id"] is not None
                    and following["character_id"] != character_id):
                raise ValueError(f"{field}[{index}] following2921a90 CharacterID disagrees")
            conditional = normalized["current_person_state"].get("following_2921a90_conditional")
            if (conditional is not None and conditional["character_id"] is not None
                    and conditional["character_id"] != character_id):
                raise ValueError(f"{field}[{index}] conditional2921a90 CharacterID disagrees")
        result.append(normalized)
    return result


def query_battle_terminal_transition_v1_step(
    prior_combat_id: int | None,
    subject_public_cunit_id: int | None,
    after_terminal_sequence: int | None = None,
    character_ids: list[int] | None = None,
) -> str:
    """Encode battle context when present and actual requested characters."""
    ids = _requested_character_ids(character_ids, "character_ids")
    if prior_combat_id is None and subject_public_cunit_id is None:
        if not ids or after_terminal_sequence is not None:
            raise ValueError("character-only queries need IDs and no journal cursor")
        return (QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX + "none:characters:"
                + ",".join(map(str, ids)))
    prior_combat_id = _full_component_id(prior_combat_id, "prior_combat_id")
    subject_public_cunit_id = _public_cunit_id(
        subject_public_cunit_id, "subject_public_cunit_id"
    )
    cursor_wire = 0
    if after_terminal_sequence is not None:
        cursor_wire = _integer(
            after_terminal_sequence, "after_terminal_sequence",
            minimum=1, maximum=2**64 - 1,
        )
    step = (f"{QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX}"
            f"{prior_combat_id}-{subject_public_cunit_id}-{cursor_wire}")
    if ids:
        step += ":characters:" + ",".join(map(str, ids))
    return step


def _split_query_battle_terminal_transition_v1_characters(
    step: object,
) -> tuple[str, list[int]] | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX
    ):
        return None
    wire = step.removeprefix(QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX)
    if ":characters:" not in wire:
        return wire, []
    wire, ids_wire = wire.split(":characters:", 1)
    parts = ids_wire.split(",")
    try:
        ids = [int(part) for part in parts]
    except ValueError:
        return None
    if any(not part.isascii() or str(value) != part or not 1 <= value <= 2**31 - 1
           for part, value in zip(parts, ids)):
        return None
    return wire, list(dict.fromkeys(ids))


def parse_query_battle_terminal_transition_v1_step(
    step: object,
) -> tuple[int, int, int | None] | None:
    """Keep the legacy triple while accepting an optional character suffix."""
    split = _split_query_battle_terminal_transition_v1_characters(step)
    if split is None:
        return None
    wire, ids = split
    if wire == "none" and ids:
        return -1, -1, None
    parts = wire.rsplit("-", 2)
    if len(parts) != 3 or any(not part.isascii() for part in parts):
        return None
    try:
        prior_combat_id, subject_public_cunit_id, cursor_wire = map(int, parts)
    except ValueError:
        return None
    if not (
        -(2**31) <= prior_combat_id <= 2**31 - 1 and prior_combat_id != -1
        and str(prior_combat_id) == parts[0]
        and 0 <= subject_public_cunit_id <= 2**31 - 1
        and str(subject_public_cunit_id) == parts[1]
        and 0 <= cursor_wire <= 2**64 - 1 and str(cursor_wire) == parts[2]
    ):
        return None
    return (prior_combat_id, subject_public_cunit_id,
            cursor_wire if cursor_wire > 0 else None)


def parse_query_battle_terminal_transition_v1_character_ids(
    step: object,
) -> list[int] | None:
    """Return first-occurrence character IDs; valid legacy steps return []."""
    if parse_query_battle_terminal_transition_v1_step(step) is None:
        return None
    split = _split_query_battle_terminal_transition_v1_characters(step)
    return None if split is None else split[1]


def _normalize_journal(
    value: object,
    *,
    expected_after_terminal_sequence: int | None,
) -> dict[str, object]:
    journal = _exact_dict(
        value, "battle_terminal_transition.terminal_journal", _JOURNAL_FIELDS
    )
    requested = _optional_integer(
        journal.get("requested_after_sequence"),
        "battle_terminal_transition.terminal_journal.requested_after_sequence",
        minimum=1,
        maximum=2**64 - 1,
    )
    if requested != expected_after_terminal_sequence:
        raise ValueError("terminal journal cursor binding changed")
    oldest = _integer(
        journal.get("oldest_available_sequence"),
        "battle_terminal_transition.terminal_journal.oldest_available_sequence",
        minimum=0,
        maximum=2**64 - 1,
    )
    latest = _integer(
        journal.get("latest_sequence"),
        "battle_terminal_transition.terminal_journal.latest_sequence",
        minimum=0,
        maximum=2**64 - 1,
    )
    event_sequence = _optional_integer(
        journal.get("event_sequence"),
        "battle_terminal_transition.terminal_journal.event_sequence",
        minimum=1,
        maximum=2**64 - 1,
    )
    event_status = journal.get("event_status")
    if event_status not in {"not_observed", "observed"}:
        raise ValueError("terminal journal event_status is invalid")
    if (oldest == 0) is not (latest == 0):
        raise ValueError("terminal journal empty cursor bounds disagree")
    if oldest > latest:
        raise ValueError("terminal journal cursor bounds are reversed")
    if event_status == "observed":
        if event_sequence is None:
            raise ValueError("observed terminal journal event lacks sequence")
        if not oldest <= event_sequence <= latest:
            raise ValueError("terminal event sequence is outside ring bounds")
        if requested is not None and event_sequence <= requested:
            raise ValueError("terminal event does not follow requested cursor")
    elif event_sequence is not None:
        raise ValueError("not-observed terminal journal invented an event")
    return {
        **journal,
        "requested_after_sequence": requested,
        "oldest_available_sequence": oldest,
        "latest_sequence": latest,
        "event_sequence": event_sequence,
        "event_status": event_status,
    }


def _normalize_warscore(value: object) -> dict[str, object]:
    fields = _WARSCORE_FIELDS | (
        _WARSCORE_EXTENSION_FIELDS & value.keys()
        if isinstance(value, dict) else set()
    )
    warscore = _exact_dict(
        value,
        "battle_terminal_transition.prior.battle_warscore",
        fields,
    )
    status = warscore.get("status")
    if status not in {"recorded", "not_recorded_by_native", "unavailable"}:
        raise ValueError("battle warscore status is invalid")
    optional_keys = fields - {"status"}
    if status != "recorded":
        if any(warscore.get(key) is not None for key in optional_keys):
            raise ValueError("non-recorded battle warscore invented native state")
        return dict(warscore)
    war_id = _positive_int32(
        warscore.get("war_id"),
        "battle_terminal_transition.prior.battle_warscore.war_id",
    )
    row_index = _integer(
        warscore.get("war_battle_row_index"),
        "battle_terminal_transition.prior.battle_warscore."
        "war_battle_row_index",
        minimum=0,
        maximum=2**31 - 1,
    )
    value_raw = _integer(
        warscore.get("value_raw_q100000"),
        "battle_terminal_transition.prior.battle_warscore."
        "value_raw_q100000",
        minimum=0,
        maximum=2**63 - 1,
    )
    winner_is_war_attacker = _boolean(
        warscore.get("winner_is_war_attacker"),
        "battle_terminal_transition.prior.battle_warscore."
        "winner_is_war_attacker",
    )
    combat_side0_is_war_attacker = _boolean(
        warscore.get("combat_side0_is_war_attacker"),
        "battle_terminal_transition.prior.battle_warscore."
        "combat_side0_is_war_attacker",
    )
    relative_delta = _integer(
        warscore.get("attacker_relative_delta_raw_q100000"),
        "battle_terminal_transition.prior.battle_warscore."
        "attacker_relative_delta_raw_q100000",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    expected_delta = value_raw if winner_is_war_attacker else -value_raw
    if relative_delta != expected_delta:
        raise ValueError("battle warscore attacker-relative sign is invalid")
    selected_cb_scale = None
    if warscore.get("selected_cb_battle_scale_raw_q100000") is not None:
        selected_cb_scale = _integer(
            warscore["selected_cb_battle_scale_raw_q100000"],
            "battle warscore selected CB battle scale",
            minimum=0,
            maximum=2**63 - 1,
        )
    denominator_inputs = None
    if warscore.get("denominator_inputs") is not None:
        denominator = _exact_dict(
            warscore["denominator_inputs"],
            "battle_terminal_transition.prior.battle_warscore.denominator_inputs",
            _DENOMINATOR_FIELDS,
        )
        participants = denominator["participants"]
        if not isinstance(participants, list) or not 1 <= len(participants) <= 32:
            raise ValueError("battle denominator participant count is invalid")
        normalized_rows = []
        total_unsigned = 0
        for index, item in enumerate(participants):
            row = _exact_dict(
                item,
                f"battle denominator participant {index}",
                _DENOMINATOR_PARTICIPANT_FIELDS,
            )
            character_id = _positive_int32(
                row["character_id"], f"battle denominator character {index}"
            )
            buckets = row["buckets_native_add_order_int32"]
            if not isinstance(buckets, list) or len(buckets) != 8:
                raise ValueError("battle denominator requires eight buckets")
            normalized_buckets = [
                _integer(
                    bucket, f"battle denominator bucket {index}:{slot}",
                    minimum=0, maximum=2**31 - 1,
                )
                for slot, bucket in enumerate(buckets)
            ]
            total_unsigned = (total_unsigned + sum(normalized_buckets)) & 0xFFFFFFFF
            normalized_rows.append({
                "character_id": character_id,
                "buckets_native_add_order_int32": normalized_buckets,
            })
        native_sum = _integer(
            denominator["sum_int32"], "battle denominator native sum",
            minimum=-(2**31), maximum=2**31 - 1,
        )
        expected_sum = total_unsigned if total_unsigned < 2**31 else total_unsigned - 2**32
        after_minimum = _integer(
            denominator["after_minimum_int32"], "battle denominator after minimum",
            minimum=1, maximum=2**31 - 1,
        )
        if native_sum != expected_sum or after_minimum != max(1, native_sum):
            raise ValueError("battle denominator arithmetic disagrees")
        denominator_inputs = {
            "sum_int32": native_sum,
            "after_minimum_int32": after_minimum,
            "participants": normalized_rows,
        }
    normalized = {
        **warscore,
        "war_id": war_id,
        "war_battle_row_index": row_index,
        "value_raw_q100000": value_raw,
        "winner_is_war_attacker": winner_is_war_attacker,
        "combat_side0_is_war_attacker": combat_side0_is_war_attacker,
        "attacker_relative_delta_raw_q100000": relative_delta,
    }
    if "denominator_inputs" in warscore:
        normalized["denominator_inputs"] = denominator_inputs
    if "selected_cb_battle_scale_raw_q100000" in warscore:
        normalized["selected_cb_battle_scale_raw_q100000"] = selected_cb_scale
    return normalized


def _normalize_prior(
    value: object,
    *,
    expected_prior_combat_id: int,
    event_status: str,
) -> dict[str, object]:
    prior_fields = _PRIOR_FIELDS | (
        _PRIOR_OPTIONAL_EXTENSION_FIELDS & value.keys()
        if isinstance(value, dict)
        else set()
    )
    prior = _exact_dict(
        value, "battle_terminal_transition.prior", prior_fields
    )
    combat_id = _full_component_id(
        prior.get("combat_id"), "battle_terminal_transition.prior.combat_id"
    )
    if combat_id != expected_prior_combat_id:
        raise ValueError("prior CombatID binding changed")
    terminal_kind = prior.get("terminal_kind")
    if terminal_kind not in _TERMINAL_KINDS:
        raise ValueError("prior terminal_kind is invalid")
    terminal_date_raw = _optional_integer(
        prior.get("terminal_date_raw"),
        "battle_terminal_transition.prior.terminal_date_raw",
        minimum=0,
        maximum=2**31 - 1,
    )
    suppress = _optional_boolean(
        prior.get("suppress_normal_result_envelopes"),
        "battle_terminal_transition.prior."
        "suppress_normal_result_envelopes",
    )
    phase_raw = _optional_integer(
        prior.get("phase_raw"),
        "battle_terminal_transition.prior.phase_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    phase_day = _optional_integer(
        prior.get("phase_day"),
        "battle_terminal_transition.prior.phase_day",
        minimum=0,
        maximum=2**31 - 1,
    )
    winner_raw = _optional_integer(
        prior.get("winner_raw"),
        "battle_terminal_transition.prior.winner_raw",
        minimum=-1,
        maximum=1,
    )
    finalized_before = _optional_boolean(
        prior.get("finalized_before"),
        "battle_terminal_transition.prior.finalized_before",
    )
    daily_guard_raw = _optional_integer(
        prior.get("daily_guard_raw"),
        "battle_terminal_transition.prior.daily_guard_raw",
        minimum=0,
        maximum=255,
    )
    province_id = _optional_positive_int32(
        prior.get("province_id"),
        "battle_terminal_transition.prior.province_id",
    )
    battle_result_id = _optional_full_component_id(
        prior.get("battle_result_id"),
        "battle_terminal_transition.prior.battle_result_id",
    )
    wipe_raw = _optional_boolean(
        prior.get("wipe_raw"), "battle_terminal_transition.prior.wipe_raw"
    )
    attacker_character = _optional_positive_int32(
        prior.get("attacker_primary_participant_character_id"),
        "battle_terminal_transition.prior."
        "attacker_primary_participant_character_id",
    )
    defender_character = _optional_positive_int32(
        prior.get("defender_primary_participant_character_id"),
        "battle_terminal_transition.prior."
        "defender_primary_participant_character_id",
    )
    attacker_ids_value = prior.get(
        "attacker_public_cunit_ids_in_stored_order"
    )
    defender_ids_value = prior.get(
        "defender_public_cunit_ids_in_stored_order"
    )
    attacker_ids = (
        None
        if attacker_ids_value is None
        else _public_cunit_ids(
            attacker_ids_value,
            "battle_terminal_transition.prior."
            "attacker_public_cunit_ids_in_stored_order",
            unique=True,
        )
    )
    defender_ids = (
        None
        if defender_ids_value is None
        else _public_cunit_ids(
            defender_ids_value,
            "battle_terminal_transition.prior."
            "defender_public_cunit_ids_in_stored_order",
            unique=True,
        )
    )
    if (
        attacker_ids is not None
        and defender_ids is not None
        and set(attacker_ids) & set(defender_ids)
    ):
        raise ValueError("prior terminal side CUnit partitions overlap")
    warscore = _normalize_warscore(prior.get("battle_warscore"))
    hard_loss_inputs = None
    if prior.get("hard_loss_inputs") is not None:
        loss = _exact_dict(
            prior["hard_loss_inputs"],
            "battle_terminal_transition.prior.hard_loss_inputs",
            _HARD_LOSS_FIELDS,
        )
        side_index = _integer(
            loss["losing_side_index"],
            "battle_terminal_transition.prior.hard_loss_inputs.losing_side_index",
            minimum=0,
            maximum=1,
        )
        quantities = {
            key: _integer(
                loss[key],
                f"battle_terminal_transition.prior.hard_loss_inputs.{key}",
                minimum=0,
                maximum=2**63 - 1,
            )
            for key in _HARD_LOSS_FIELDS - {"losing_side_index"}
        }
        if (
            terminal_kind != "normal_result"
            or winner_raw not in (0, 1)
            or side_index != 1 - winner_raw
            or quantities["hard_loss_raw"]
            != max(
                0,
                quantities["baseline_raw"]
                - quantities["stored_current_raw"]
                - quantities["levy_soft_raw"]
                - quantities["men_at_arms_soft_raw"],
            )
        ):
            raise ValueError("terminal hard-loss inputs disagree")
        hard_loss_inputs = {"losing_side_index": side_index, **quantities}

    side_loss_inputs = None
    if prior.get("side_loss_inputs_in_native_order") is not None:
        rows = prior["side_loss_inputs_in_native_order"]
        if not isinstance(rows, list) or len(rows) != 2:
            raise ValueError("terminal side-loss inputs must contain both sides")
        if terminal_kind != "normal_result":
            raise ValueError("terminal side-loss inputs require a normal result")
        side_loss_inputs = []
        for expected_side_index, value in enumerate(rows):
            loss = _exact_dict(
                value,
                "battle_terminal_transition.prior.side_loss_inputs_in_native_order",
                _SIDE_LOSS_FIELDS,
            )
            side_index = _integer(
                loss["side_index"], "terminal side-loss side_index",
                minimum=0, maximum=1,
            )
            quantities = {
                key: _integer(
                    loss[key], f"terminal side-loss {key}",
                    minimum=0, maximum=2**63 - 1,
                )
                for key in _SIDE_LOSS_FIELDS - {"side_index"}
            }
            if (
                side_index != expected_side_index
                or quantities["hard_loss_raw_q100000"] != max(
                    0,
                    quantities["baseline_raw_q100000"]
                    - quantities["stored_current_fighting_raw_q100000"]
                    - quantities["levy_soft_raw_q100000"]
                    - quantities["men_at_arms_soft_raw_q100000"],
                )
            ):
                raise ValueError("terminal side-loss inputs disagree")
            side_loss_inputs.append({"side_index": side_index, **quantities})

    side_final_results = None
    rows = prior.get("side_final_results_in_native_order")
    if rows is not None:
        if terminal_kind != "normal_result" or not isinstance(rows, list) or len(rows) != 2:
            raise ValueError("terminal final-side results require two normal-result sides")
        side_final_results = []
        for index, value in enumerate(rows):
            row = _exact_dict(value, "terminal final-side result", {
                "side_index", "selected_commander_character_id",
                "baseline_raw_q100000", "survivors_raw_q100000",
            })
            if _integer(row["side_index"], "final-side index", minimum=0, maximum=1) != index:
                raise ValueError("terminal final-side order changed")
            commander = _integer(row["selected_commander_character_id"],
                "final-side commander", minimum=-1, maximum=2**31 - 1)
            side_final_results.append({"side_index": index,
                "selected_commander_character_id": commander,
                **{key: _integer(row[key], f"final-side {key}", minimum=0, maximum=2**63 - 1)
                   for key in ("baseline_raw_q100000", "survivors_raw_q100000")}})
    character_rows = None
    rows = prior.get("character_result_rows_in_native_order")
    if rows is not None:
        if terminal_kind != "normal_result" or not isinstance(rows, list):
            raise ValueError("terminal character rows require a normal-result list")
        character_rows = []
        for index, value in enumerate(rows):
            row = _exact_dict(value, "terminal character row", {
                "native_row_index", "left_character_id", "right_character_id",
                "key", "type_raw", "side0", "target_right",
            })
            if _integer(row["native_row_index"], "character row index", minimum=0, maximum=2**31 - 1) != index:
                raise ValueError("terminal character row order changed")
            if row["key"] is not None and not isinstance(row["key"], str):
                raise ValueError("terminal character row key must be owned text")
            character_rows.append({"native_row_index": index, "key": row["key"],
                **{key: _integer(row[key], f"character row {key}", minimum=-1, maximum=2**31 - 1)
                   for key in ("left_character_id", "right_character_id")},
                "type_raw": _integer(row["type_raw"], "character row type", minimum=-(2**31), maximum=2**31 - 1),
                "side0": _optional_boolean(row["side0"], "character row side0"),
                "target_right": _optional_boolean(row["target_right"], "character row target_right")})
            if character_rows[-1]["side0"] is None or character_rows[-1]["target_right"] is None:
                raise ValueError("terminal character row bool is absent")
    rows = prior.get("character_custody_in_observed_order")
    if rows is not None and terminal_kind != "normal_result":
        raise ValueError("terminal custody requires a normal-result list")
    character_custody = _normalize_character_custody_rows(
        rows, "terminal character custody"
    )

    observed_fields = (
        terminal_date_raw,
        suppress,
        phase_raw,
        phase_day,
        winner_raw,
        finalized_before,
        daily_guard_raw,
        province_id,
        attacker_character,
        defender_character,
        attacker_ids,
        defender_ids,
    )
    if event_status == "observed":
        if terminal_kind not in {"normal_result", "no_normal_result"}:
            raise ValueError("observed terminal event has non-terminal kind")
        if any(item is None for item in observed_fields):
            raise ValueError("observed terminal event omitted canonical state")
        expected_suppress = terminal_kind == "no_normal_result"
        if suppress is not expected_suppress:
            raise ValueError("terminal kind disagrees with observed suppress flag")
        if (
            terminal_kind == "no_normal_result"
            and warscore["status"] != "not_recorded_by_native"
        ):
            raise ValueError("no-normal terminal cannot record battle warscore")
    elif terminal_kind == "active_not_terminal":
        current_fields = (
            phase_raw,
            phase_day,
            winner_raw,
            finalized_before,
            daily_guard_raw,
            province_id,
            attacker_character,
            defender_character,
            attacker_ids,
            defender_ids,
        )
        if (
            terminal_date_raw is not None
            or suppress is not None
            or any(item is None for item in current_fields)
        ):
            raise ValueError(
                "active_not_terminal omitted current combat state or invented "
                "a suppress flag"
            )
        if finalized_before is not False or daily_guard_raw != 0:
            raise ValueError("active_not_terminal is finalized or being ticked")
        if battle_result_id is None and wipe_raw is not None:
            raise ValueError("active combat wipe state lacks a strict ResultID")
        if warscore["status"] != "unavailable":
            raise ValueError("active combat invented terminal battle warscore")
    else:
        if terminal_kind != "unavailable_after_removal":
            raise ValueError("unobserved terminal state invented terminal kind")
        removed_fields = (
            terminal_date_raw,
            suppress,
            phase_raw,
            phase_day,
            winner_raw,
            finalized_before,
            daily_guard_raw,
            province_id,
            battle_result_id,
            wipe_raw,
            attacker_character,
            defender_character,
            attacker_ids,
            defender_ids,
        )
        if any(item is not None for item in removed_fields):
            raise ValueError("removed unobserved terminal state invented data")
        if warscore["status"] != "unavailable":
            raise ValueError("unobserved terminal state invented battle warscore")
    normalized = {
        **prior,
        "combat_id": combat_id,
        "terminal_kind": terminal_kind,
        "terminal_date_raw": terminal_date_raw,
        "suppress_normal_result_envelopes": suppress,
        "phase_raw": phase_raw,
        "phase_day": phase_day,
        "winner_raw": winner_raw,
        "finalized_before": finalized_before,
        "daily_guard_raw": daily_guard_raw,
        "province_id": province_id,
        "battle_result_id": battle_result_id,
        "wipe_raw": wipe_raw,
        "attacker_primary_participant_character_id": attacker_character,
        "defender_primary_participant_character_id": defender_character,
        "attacker_public_cunit_ids_in_stored_order": attacker_ids,
        "defender_public_cunit_ids_in_stored_order": defender_ids,
        "battle_warscore": warscore,
    }
    if "hard_loss_inputs" in prior:
        normalized["hard_loss_inputs"] = hard_loss_inputs
    if "side_loss_inputs_in_native_order" in prior:
        normalized["side_loss_inputs_in_native_order"] = side_loss_inputs
    for key, result in (
        ("side_final_results_in_native_order", side_final_results),
        ("character_result_rows_in_native_order", character_rows),
        ("character_custody_in_observed_order", character_custody),
    ):
        if key in prior:
            normalized[key] = result
    return normalized


def _normalize_removal(value: object) -> dict[str, object]:
    removal = _exact_dict(
        value, "battle_terminal_transition.removal", _REMOVAL_FIELDS
    )
    prior_resolves = _boolean(
        removal.get("prior_combat_strictly_resolves"),
        "battle_terminal_transition.removal."
        "prior_combat_strictly_resolves",
    )
    province_resolves = _optional_boolean(
        removal.get("prior_province_strictly_resolves"),
        "battle_terminal_transition.removal."
        "prior_province_strictly_resolves",
    )
    province_contains = _optional_boolean(
        removal.get("prior_province_contains_prior_combat_id"),
        "battle_terminal_transition.removal."
        "prior_province_contains_prior_combat_id",
    )
    result_resolves = _optional_boolean(
        removal.get("result_strictly_resolves"),
        "battle_terminal_transition.removal.result_strictly_resolves",
    )
    relevant_count = _optional_integer(
        removal.get("result_relevant_player_count"),
        "battle_terminal_transition.removal.result_relevant_player_count",
        minimum=0,
        maximum=2**31 - 1,
    )
    if province_resolves is not True and province_contains is not None:
        raise ValueError("unresolved prior Province invented membership")
    if result_resolves is not True and relevant_count is not None:
        raise ValueError("unresolved ResultID invented relevant-player count")
    return {
        **removal,
        "prior_combat_strictly_resolves": prior_resolves,
        "prior_province_strictly_resolves": province_resolves,
        "prior_province_contains_prior_combat_id": province_contains,
        "result_strictly_resolves": result_resolves,
        "result_relevant_player_count": relevant_count,
    }


def _normalize_subject(value: object) -> dict[str, object]:
    subject = _exact_dict(
        value, "battle_terminal_transition.subject", _SUBJECT_FIELDS
    )
    exists = _boolean(
        subject.get("exists"), "battle_terminal_transition.subject.exists"
    )
    normalized: dict[str, object] = {**subject, "exists": exists}
    positive_fields = (
        "current_province_id",
        "native_carmy_id",
        "move_target_province_id",
        "coordinator_id",
    )
    for key in positive_fields:
        normalized[key] = _optional_positive_int32(
            subject.get(key), f"battle_terminal_transition.subject.{key}"
        )
    for key in ("combat_backlink_id", "active_combat_id"):
        normalized[key] = _optional_full_component_id(
            subject.get(key), f"battle_terminal_transition.subject.{key}"
        )
    normalized["movement_or_retreat_state_raw"] = _optional_integer(
        subject.get("movement_or_retreat_state_raw"),
        "battle_terminal_transition.subject.movement_or_retreat_state_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    route_value = subject.get("route_province_ids_in_stored_order")
    normalized["route_province_ids_in_stored_order"] = (
        None
        if route_value is None
        else _ordered_positive_ids(
            route_value,
            "battle_terminal_transition.subject."
            "route_province_ids_in_stored_order",
            unique=False,
        )
    )
    ai_membership_status = subject.get("ai_membership_status")
    if ai_membership_status not in _AI_MEMBERSHIP_STATUSES:
        raise ValueError("subject AI membership status is invalid")
    normalized["ai_membership_status"] = ai_membership_status
    for key in ("unit_stack_stored_index", "subunit_stored_index"):
        normalized[key] = _optional_integer(
            subject.get(key),
            f"battle_terminal_transition.subject.{key}",
            minimum=0,
            maximum=2**31 - 1,
        )
    normalized["blocked_by_active_combat"] = _optional_boolean(
        subject.get("blocked_by_active_combat"),
        "battle_terminal_transition.subject.blocked_by_active_combat",
    )
    optional_values = [
        normalized[key]
        for key in _SUBJECT_FIELDS - {"exists", "ai_membership_status"}
    ]
    if not exists and any(item is not None for item in optional_values):
        raise ValueError("missing subject invented current native state")
    membership_values = (
        normalized["coordinator_id"],
        normalized["unit_stack_stored_index"],
        normalized["subunit_stored_index"],
    )
    if not exists and ai_membership_status != "none":
        raise ValueError("missing subject has AI membership")
    if ai_membership_status == "observed":
        if any(item is None for item in membership_values):
            raise ValueError("observed subject AI membership is incomplete")
    elif any(item is not None for item in membership_values):
        raise ValueError("unobserved subject invented AI membership identity")
    if (
        normalized["blocked_by_active_combat"] is True
        and normalized["active_combat_id"] is None
    ):
        raise ValueError("active-combat blocker lacks strict CombatID")
    return normalized


def _normalize_successor(
    value: object,
    *,
    prior: dict[str, object],
    subject: dict[str, object],
) -> dict[str, object]:
    successor = _exact_dict(
        value, "battle_terminal_transition.successor", _SUCCESSOR_FIELDS
    )
    state = successor.get("state")
    if state not in _SUCCESSOR_STATES:
        raise ValueError("battle successor state is invalid")
    matching = _ordered_full_component_ids(
        successor.get("matching_combat_ids_in_native_order"),
        "battle_terminal_transition.successor."
        "matching_combat_ids_in_native_order",
        unique=True,
    )
    selected = _optional_full_component_id(
        successor.get("selected_successor_combat_id"),
        "battle_terminal_transition.successor.selected_successor_combat_id",
    )
    overlap = _public_cunit_ids(
        successor.get("participant_overlap_public_cunit_ids_in_prior_order"),
        "battle_terminal_transition.successor."
        "participant_overlap_public_cunit_ids_in_prior_order",
        unique=True,
    )
    if selected is not None and selected not in matching:
        raise ValueError("selected successor is absent from native matches")
    attacker = prior.get("attacker_public_cunit_ids_in_stored_order")
    defender = prior.get("defender_public_cunit_ids_in_stored_order")
    if isinstance(attacker, list) and isinstance(defender, list):
        prior_order = [*attacker, *defender]
        overlap_positions = [
            prior_order.index(item) if item in prior_order else -1
            for item in overlap
        ]
        if -1 in overlap_positions or overlap_positions != sorted(
            overlap_positions
        ):
            raise ValueError("successor overlap is not a prior-order subset")
    if state == "residual_new_combat" and (
        selected is None
        or not matching
        or not overlap
        or subject.get("exists") is not True
        or subject.get("active_combat_id") != selected
        or subject.get("blocked_by_active_combat") is not True
    ):
        raise ValueError("residual successor lacks exact identity overlap")
    if state != "residual_new_combat" and (
        selected is not None or overlap
    ):
        raise ValueError("non-residual successor invented a selection")
    if state == "subject_missing" and (
        subject.get("exists") is not False or matching
    ):
        raise ValueError("subject-missing successor disagrees with subject")
    movement_state = subject.get("movement_or_retreat_state_raw")
    movement_state = movement_state if isinstance(movement_state, int) else 0
    if state == "subject_retreating" and (
        subject.get("exists") is not True
        or subject.get("active_combat_id") is not None
        or subject.get("blocked_by_active_combat") is not False
        or movement_state <= 0
    ):
        raise ValueError("retreating successor lacks independent retreat state")
    if state == "subject_assignment_reopened" and (
        subject.get("exists") is not True
        or subject.get("blocked_by_active_combat") is not False
        or subject.get("active_combat_id") is not None
        or movement_state > 0
        or subject.get("ai_membership_status") != "observed"
        or matching
    ):
        raise ValueError("assignment-reopened successor lacks observed membership")
    if state == "no_successor" and (
        subject.get("exists") is not True
        or subject.get("ai_membership_status") != "none"
        or subject.get("active_combat_id") is not None
        or subject.get("blocked_by_active_combat") is True
        or movement_state > 0
        or matching
        or selected is not None
        or overlap
    ):
        raise ValueError("no-successor state lacks complete negative evidence")
    return {
        **successor,
        "state": state,
        "matching_combat_ids_in_native_order": matching,
        "selected_successor_combat_id": selected,
        "participant_overlap_public_cunit_ids_in_prior_order": overlap,
    }


def normalize_battle_terminal_transition_v1(
    value: object,
    *,
    expected_prior_combat_id: int | None,
    expected_subject_public_cunit_id: int | None,
    expected_after_terminal_sequence: int | None,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
    expected_character_ids: list[int] | None = None,
) -> dict[str, object]:
    """Normalize one journal-backed frame without inferring terminal kind."""

    character_only = (expected_prior_combat_id in (None, -1)
                      and expected_subject_public_cunit_id in (None, -1))
    if character_only:
        expected_prior_combat_id = expected_subject_public_cunit_id = -1
    else:
        expected_prior_combat_id = _full_component_id(
            expected_prior_combat_id, "expected_prior_combat_id"
        )
        expected_subject_public_cunit_id = _public_cunit_id(
            expected_subject_public_cunit_id, "expected_subject_public_cunit_id"
        )
    if expected_after_terminal_sequence is not None:
        expected_after_terminal_sequence = _integer(
            expected_after_terminal_sequence,
            "expected_after_terminal_sequence",
            minimum=1,
            maximum=2**64 - 1,
        )
    expected_observed_date_raw = _integer(
        expected_observed_date_raw,
        "expected_observed_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_snapshot_revision = _integer(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    fields = _TOP_FIELDS | (
        _TOP_OPTIONAL_EXTENSION_FIELDS & value.keys()
        if isinstance(value, dict) else set()
    )
    frame = _exact_dict(value, "battle_terminal_transition", fields)
    observations = _normalize_character_custody_rows(
        frame.get("character_observations"), "character_observations",
        allow_current_person_state=True,
    )
    if expected_character_ids is not None:
        expected_ids = _requested_character_ids(
            expected_character_ids, "expected_character_ids"
        )
        observed_ids = [] if observations is None else [
            row["character_id"] for row in observations
        ]
        if observed_ids != expected_ids:
            raise ValueError("character observation request binding changed")
    character_extension = (
        {"character_observations": observations}
        if "character_observations" in frame else {}
    )
    if "pending_death_queue" in frame:
        character_extension["pending_death_queue"] = _normalize_pending_death_queue(
            frame["pending_death_queue"])
    if frame.get("schema_version") != 1:
        raise ValueError("battle_terminal_transition.schema_version must be 1")
    if (
        frame.get("contract_stage")
        != BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE
    ):
        raise ValueError("battle_terminal_transition.contract_stage is invalid")
    status = frame.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError("battle_terminal_transition.status is invalid")
    ready = _boolean(
        frame.get("battle_terminal_transition_ready"),
        "battle_terminal_transition.battle_terminal_transition_ready",
    )
    if ready is not (status == "available" and not character_only):
        raise ValueError("battle terminal transition readiness disagrees with status")
    revision = _integer(
        frame.get("snapshot_revision"),
        "battle_terminal_transition.snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    observed_date_raw = _integer(
        frame.get("observed_date_raw"),
        "battle_terminal_transition.observed_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    if character_only:
        prior_combat_id = _integer(frame.get("prior_combat_id"),
            "battle_terminal_transition.prior_combat_id", minimum=-1, maximum=-1)
        subject_public_cunit_id = _integer(frame.get("subject_public_cunit_id"),
            "battle_terminal_transition.subject_public_cunit_id", minimum=-1, maximum=-1)
    else:
        prior_combat_id = _full_component_id(
            frame.get("prior_combat_id"), "battle_terminal_transition.prior_combat_id"
        )
        subject_public_cunit_id = _public_cunit_id(
            frame.get("subject_public_cunit_id"),
            "battle_terminal_transition.subject_public_cunit_id",
        )
    if revision != expected_snapshot_revision:
        raise ValueError("battle terminal transition revision binding changed")
    if observed_date_raw != expected_observed_date_raw:
        raise ValueError("battle terminal transition date binding changed")
    if prior_combat_id != expected_prior_combat_id:
        raise ValueError("battle terminal transition CombatID binding changed")
    if subject_public_cunit_id != expected_subject_public_cunit_id:
        raise ValueError("battle terminal transition CUnitID binding changed")

    reason = frame.get("unavailable_reason")
    if character_only and status == "available":
        journal = _normalize_journal(
            frame.get("terminal_journal"),
            expected_after_terminal_sequence=expected_after_terminal_sequence,
        )
        if (reason is not None or not observations
            or journal["requested_after_sequence"] is not None
            or journal["event_status"] != "not_observed"
            or journal["event_sequence"] is not None
            or any(frame.get(key) is not None
                   for key in ("prior", "removal", "subject", "successor"))):
            raise ValueError("character-only observation invented battle context")
        return {**copy.deepcopy(frame), **character_extension,
                "terminal_journal": journal}
    if status == "unavailable":
        if reason not in _UNAVAILABLE_REASONS:
            raise ValueError("battle terminal unavailable_reason is invalid")
        journal = _normalize_journal(
            frame.get("terminal_journal"),
            expected_after_terminal_sequence=expected_after_terminal_sequence,
        )
        if (
            journal["event_status"] != "not_observed"
            or journal["event_sequence"] is not None
        ):
            raise ValueError("unavailable transition invented terminal event")
        if any(
            frame.get(key) is not None
            for key in ("prior", "removal", "subject", "successor")
        ):
            raise ValueError("unavailable terminal transition invented native state")
        return {**copy.deepcopy(frame), **character_extension,
                "terminal_journal": journal}
    if reason is not None:
        raise ValueError("available terminal transition has unavailable_reason")

    journal = _normalize_journal(
        frame.get("terminal_journal"),
        expected_after_terminal_sequence=expected_after_terminal_sequence,
    )
    prior = _normalize_prior(
        frame.get("prior"),
        expected_prior_combat_id=expected_prior_combat_id,
        event_status=str(journal["event_status"]),
    )
    removal = _normalize_removal(frame.get("removal"))
    subject = _normalize_subject(frame.get("subject"))
    successor = _normalize_successor(
        frame.get("successor"), prior=prior, subject=subject
    )
    if (
        prior["terminal_kind"] == "active_not_terminal"
        and removal["prior_combat_strictly_resolves"] is not True
    ):
        raise ValueError("active_not_terminal does not strictly resolve")
    if (
        prior["terminal_kind"] == "unavailable_after_removal"
        and removal["prior_combat_strictly_resolves"] is not False
    ):
        raise ValueError("unavailable_after_removal still strictly resolves")
    return {
        **frame,
        **character_extension,
        "unavailable_reason": None,
        "snapshot_revision": revision,
        "observed_date_raw": observed_date_raw,
        "prior_combat_id": prior_combat_id,
        "subject_public_cunit_id": subject_public_cunit_id,
        "terminal_journal": journal,
        "prior": prior,
        "removal": removal,
        "subject": subject,
        "successor": successor,
    }
