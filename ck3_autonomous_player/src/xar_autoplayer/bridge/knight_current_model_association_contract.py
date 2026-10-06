"""Independent same-query model identities; no historical Entry-stage inference."""

from __future__ import annotations


def _object(value: object, keys: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"native {name} object is malformed")
    return value


def _nullable_bool(value: object, name: str) -> bool | None:
    if value is not None and type(value) is not bool:
        raise ValueError(f"native {name} must be bool or null")
    return value


def _nullable_int32(value: object, name: str) -> int | None:
    if value is not None and (type(value) is not int or not -(2**31) <= value < 2**31):
        raise ValueError(f"native {name} must be int32 or null")
    return value


def _status_reason(row: dict, name: str) -> None:
    if row["status"] not in {"available", "partial", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    reason = row["unavailable_reason"]
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise ValueError(f"native {name}.unavailable_reason is malformed")
    if row["status"] == "available" and reason is not None:
        raise ValueError(f"native {name}.unavailable_reason must be null")


def normalize_knight_current_model_association_v1(
    value: object, *, name: str, selected_character_id: int | None
) -> dict:
    row = _object(value, {"schema", "read_scope", "selected_character_id",
                         "current_installed", "queue_census"}, name)
    if row["schema"] != "ck3_12003_knight_current_model_association_v1":
        raise ValueError(f"native {name}.schema is malformed")
    if row["read_scope"] != "frozen_current_character_values":
        raise ValueError(f"native {name}.read_scope is malformed")
    identity = _nullable_int32(row["selected_character_id"], name + ".selected_character_id")
    if identity is None or identity < 0 or identity != selected_character_id:
        raise ValueError(f"native {name}.selected_character_id differs from its enclosing selection")
    current_bool_keys = {"carrier_present", "installed_model_present", "owner_present",
                         "owner_matches_selected", "getter_receiver_matches_model_inline"}
    current = _object(row["current_installed"], current_bool_keys |
                      {"status", "context_source", "unavailable_reason"}, name + ".current_installed")
    _status_reason(current, name + ".current_installed")
    if current["context_source"] not in {None, "model_inline", "fallback_static"}:
        raise ValueError(f"native {name}.current_installed.context_source is malformed")
    normalized_current = dict(current)
    for key in current_bool_keys:
        normalized_current[key] = _nullable_bool(current[key], name + ".current_installed." + key)
    queue = _object(row["queue_census"], {"status", "old_count_raw", "pair_count_raw",
                    "first_unread_occurrence", "relevant_occurrences", "unavailable_reason"}, name + ".queue_census")
    _status_reason(queue, name + ".queue_census")
    normalized_queue = dict(queue)
    for key in ("old_count_raw", "pair_count_raw", "first_unread_occurrence"):
        normalized_queue[key] = _nullable_int32(queue[key], name + ".queue_census." + key)
    occurrences = queue["relevant_occurrences"]
    if not isinstance(occurrences, list):
        raise ValueError(f"native {name}.queue_census.relevant_occurrences must be an array")
    comparison_keys = {"old_model_matches_installed", "old_owner_matches_selected",
                       "paired_model_present", "paired_model_matches_old",
                       "paired_model_matches_installed", "paired_owner_matches_selected"}
    normalized_occurrences = []
    prior = -1
    for i, occurrence in enumerate(occurrences):
        occurrence_name = f"{name}.queue_census.relevant_occurrences[{i}]"
        item = _object(occurrence, comparison_keys | {"occurrence"}, occurrence_name)
        index = _nullable_int32(item["occurrence"], occurrence_name + ".occurrence")
        if index is None or index <= prior:
            raise ValueError(f"native {occurrence_name}.occurrence is out of stored order")
        prior = index
        normalized_occurrences.append({"occurrence": index, **{
            key: _nullable_bool(item[key], occurrence_name + "." + key)
            for key in comparison_keys}})
    normalized_queue["relevant_occurrences"] = normalized_occurrences
    return {**row, "current_installed": normalized_current, "queue_census": normalized_queue}
