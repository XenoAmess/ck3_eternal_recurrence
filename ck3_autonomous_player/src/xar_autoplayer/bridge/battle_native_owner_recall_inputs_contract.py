"""Current native owner-recall operands; separate from a future action timeline."""

from __future__ import annotations

from .public_unit_contract import public_cunit_id


def _integer(value: object, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{field} must be an integer in [{minimum}, {maximum}]")
    return value


def _optional_integer(value: object, field: str, minimum: int, maximum: int) -> int | None:
    return None if value is None else _integer(value, field, minimum, maximum)


def _optional_id(value: object, field: str) -> int | None:
    result = _optional_integer(value, field, -(2**31), 2**31 - 1)
    if result == -1:
        raise ValueError(f"{field} must use null for an absent native ID")
    return result


def _raw_condition(count: int | None, flag: int | None) -> bool | None:
    if count == 0 or flag == 0:
        return False
    if count is None or flag is None:
        return None
    return True


def _unit(value: object, count: int | None) -> dict[str, object]:
    fields = {
        "public_cunit_id", "status", "receiver_owner_character_id", "native_carmy_id",
        "attached_combat_id", "current_province_id", "army_1d4_raw", "army_1ec_raw",
        "first_fallback_raw_condition", "second_fallback_raw_condition",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("native recall unit fields are invalid")
    status = value["status"]
    if status not in {"available", "unit_unresolved", "army_unresolved"}:
        raise ValueError("native recall unit status is invalid")
    result: dict[str, object] = {
        "public_cunit_id": public_cunit_id(value["public_cunit_id"], "native recall public_cunit_id"),
        "status": status,
    }
    for field in ("receiver_owner_character_id", "native_carmy_id", "attached_combat_id", "current_province_id"):
        result[field] = _optional_id(value[field], field)
    for field in ("army_1d4_raw", "army_1ec_raw"):
        result[field] = _optional_integer(value[field], field, 0, 255)
    for field, flag in (("first_fallback_raw_condition", "army_1d4_raw"), ("second_fallback_raw_condition", "army_1ec_raw")):
        expected = _raw_condition(count, result[flag])  # type: ignore[arg-type]
        supplied = value[field]
        if supplied is not None and not isinstance(supplied, bool):
            raise ValueError(f"{field} must be bool or null")
        if supplied is not expected:
            raise ValueError(f"{field} disagrees with native count/byte operands")
        result[field] = supplied
    return result


def _activity_context_match(value: object, owner_id: int) -> dict[str, object]:
    fields = {
        "collection", "prefix_kind", "stored_index", "actor_character_id",
        "status", "unavailable_reason", "e_prefix_admitted", "context_state_raw",
        "context_16_raw", "context_2e_raw", "government_flags_40_raw", "plin_flags_2f0_raw",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("native activity context match fields are invalid")
    if value["collection"] not in {"fallback_d8", "mission_90"}:
        raise ValueError("native activity context collection is invalid")
    if value["prefix_kind"] != "e_1a781a0":
        raise ValueError("native activity context prefix_kind is invalid")
    status = value["status"]
    admitted = value["e_prefix_admitted"]
    reason = value["unavailable_reason"]
    if status == "available":
        if not isinstance(admitted, bool) or reason is not None:
            raise ValueError("available E-prefix requires a bool and no unavailable reason")
    elif status == "unavailable":
        if admitted is not None or not isinstance(reason, str) or not reason:
            raise ValueError("unavailable E-prefix requires null admission and a reason")
    else:
        raise ValueError("native activity context match status is invalid")
    actor_id = _integer(value["actor_character_id"], "actor_character_id", -(2**31), 2**31 - 1)
    if actor_id != owner_id:
        raise ValueError("native activity context match belongs to another owner")
    return {
        "collection": value["collection"],
        "prefix_kind": value["prefix_kind"],
        "stored_index": _integer(value["stored_index"], "stored_index", 0, 2**31 - 1),
        "actor_character_id": actor_id,
        "status": status,
        "unavailable_reason": reason,
        "e_prefix_admitted": admitted,
        "context_state_raw": _optional_integer(value["context_state_raw"], "context_state_raw", -(2**31), 2**31 - 1),
        "context_16_raw": _optional_integer(value["context_16_raw"], "context_16_raw", 0, 255),
        "context_2e_raw": _optional_integer(value["context_2e_raw"], "context_2e_raw", 0, 255),
        "government_flags_40_raw": _optional_integer(value["government_flags_40_raw"], "government_flags_40_raw", 0, 2**64 - 1),
        "plin_flags_2f0_raw": _optional_integer(value["plin_flags_2f0_raw"], "plin_flags_2f0_raw", 0, 2**16 - 1),
    }


def _activity_context(value: object, owner_id: int) -> dict[str, object] | None:
    if value is None:
        return None
    fields = {"schema_version", "status", "unavailable_reason", "membership_observed",
              "matched_contexts_in_native_order"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("native activity context fields are invalid")
    version = _integer(value["schema_version"], "native activity context schema_version", 1, 1)
    status = value["status"]
    reason = value["unavailable_reason"]
    if status == "available":
        if reason is not None:
            raise ValueError("available native activity context reason must be null")
    elif status == "unavailable":
        if not isinstance(reason, str) or not reason:
            raise ValueError("unavailable native activity context requires a reason")
    else:
        raise ValueError("native activity context status is invalid")
    if not isinstance(value["membership_observed"], bool):
        raise ValueError("native activity context membership_observed must be bool")
    matches = value["matched_contexts_in_native_order"]
    if not isinstance(matches, list):
        raise ValueError("matched_contexts_in_native_order must be a list")
    return {
        "schema_version": version,
        "status": status,
        "unavailable_reason": reason,
        "membership_observed": value["membership_observed"],
        "matched_contexts_in_native_order": [_activity_context_match(match, owner_id) for match in matches],
    }


def _owner(value: object) -> dict[str, object]:
    fields = {
        "owner_character_id", "land_318_count_raw", "owner_target_source_title_id",
        "owner_native_recall_target_province_id", "target_status", "owned_cunit_roster_status",
        "raw_inputs_ready", "owned_cunits_in_stored_order",
    }
    if not isinstance(value, dict) or set(value) - {"native_activity_context_v1"} != fields:
        raise ValueError("native recall owner fields are invalid")
    count = _optional_integer(value["land_318_count_raw"], "land_318_count_raw", -(2**31), 2**31 - 1)
    roster = value["owned_cunits_in_stored_order"]
    if not isinstance(roster, list):
        raise ValueError("owned_cunits_in_stored_order must be a list")
    for field in ("target_status", "owned_cunit_roster_status"):
        if not isinstance(value[field], str) or not value[field]:
            raise ValueError(f"{field} must be a nonempty native read status")
    if not isinstance(value["raw_inputs_ready"], bool):
        raise ValueError("owner raw_inputs_ready must be bool")
    owner_id = _optional_id(value["owner_character_id"], "owner_character_id")
    if owner_id is None:
        raise ValueError("owner_character_id is required")
    result: dict[str, object] = {
        "owner_character_id": owner_id,
        "land_318_count_raw": count,
        "owner_target_source_title_id": _optional_id(value["owner_target_source_title_id"], "owner_target_source_title_id"),
        "owner_native_recall_target_province_id": _optional_id(value["owner_native_recall_target_province_id"], "owner_native_recall_target_province_id"),
        "target_status": value["target_status"],
        "owned_cunit_roster_status": value["owned_cunit_roster_status"],
        "raw_inputs_ready": value["raw_inputs_ready"],
        "owned_cunits_in_stored_order": [_unit(unit, count) for unit in roster],
    }
    if "native_activity_context_v1" in value:
        result["native_activity_context_v1"] = _activity_context(value["native_activity_context_v1"], owner_id)
    return result


def normalize_battle_native_owner_recall_inputs_v1(value: object, *, lifecycle_status: str) -> dict[str, object] | None:
    """Preserve absent, numeric zero and a conditional raw selection separately."""
    if value is None:
        return None
    fields = {
        "schema_version", "status", "unavailable_reason", "raw_inputs_ready",
        "native_context_prefix_status", "native_context_prefix_admitted",
        "native_selection_ready", "owners_in_stored_order",
    }
    if not isinstance(value, dict) or set(value) != fields or value["schema_version"] != 1:
        raise ValueError("native_owner_recall_inputs_v1 fields are invalid")
    status = value["status"]
    if status not in {"available", "unavailable"} or lifecycle_status != "available":
        raise ValueError("native owner recall leaf requires available current lifecycle")
    if not isinstance(value["raw_inputs_ready"], bool):
        raise ValueError("native recall raw_inputs_ready must be bool")
    if value["native_context_prefix_status"] != "unobserved_scheduler_context" or value["native_context_prefix_admitted"] is not None or value["native_selection_ready"] is not False:
        raise ValueError("current recall inputs do not publish an observed scheduler selection")
    reason = value["unavailable_reason"]
    if status == "available" and reason is not None:
        raise ValueError("available native recall inputs must have null unavailable_reason")
    if status == "unavailable" and (not isinstance(reason, str) or not reason):
        raise ValueError("unavailable native recall inputs require a reason")
    owners = value["owners_in_stored_order"]
    if not isinstance(owners, list):
        raise ValueError("owners_in_stored_order must be a list")
    if status == "unavailable" and (owners or value["raw_inputs_ready"]):
        raise ValueError("unavailable native recall leaf cannot publish owner operands")
    return {
        "schema_version": 1, "status": status, "unavailable_reason": reason,
        "raw_inputs_ready": value["raw_inputs_ready"],
        "native_context_prefix_status": "unobserved_scheduler_context",
        "native_context_prefix_admitted": None, "native_selection_ready": False,
        "owners_in_stored_order": [_owner(owner) for owner in owners],
    }
