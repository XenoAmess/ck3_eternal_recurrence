"""Optional loaded-role/native-trigger observations for the actual Side Commander.

The consumer exposes current row sets, without chance, selection, effects or a
base forecast/MC gate. Unknown local observations remain distinct from false.
"""

from __future__ import annotations

import copy

from .phase_event_commander_side_identity_contract import _expected_commanders


PHASE_EVENT_COMMANDER_TRIGGER_LEAF = "phase_event_commander_trigger_conditions_v1"
PHASE_EVENT_COMMANDER_TRIGGER_SCOPE = (
    "v2_current_physical_side_commander_loaded_role_trigger_condition"
)
PHASE_EVENT_COMMANDER_TRIGGER_CK3_SHA256 = (
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
)
_UINT32_MAX = 0xFFFFFFFF
_ROOT_KEYS = {
    "schema_version", "scope", "status", "source_ck3_sha256",
    "trigger_source_closed", "native_role_and_trigger_evaluation_observed",
    "complete_phase_effects_ready", "unavailable_reason", "occurrences",
}
_OCCURRENCE_KEYS = {
    "occurrence_index", "character_id", "source_public_cunit_id",
    "source_native_carmy_id", "encounter_role", "requested_role_raw",
    "actual_combat_full_id_raw", "actual_side_index", "current_commander_context_ready",
    "loaded_named_side_key_raw", "conditions", "role_compatible_count",
    "evaluated_count", "admitted_count", "unknown_count",
    "role_trigger_observation_ready", "status", "unavailable_reason",
}
_CONDITION_KEYS = {
    "loaded_row_index", "role_compatible", "native_trigger_valid",
    "role_and_trigger_valid", "unavailable_reason",
}


def _object(value: object, keys: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} keys are malformed")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


def _nullable_integer(value: object, name: str, minimum: int, maximum: int) -> int | None:
    return None if value is None else _integer(value, name, minimum, maximum)


def _boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be bool")
    return value


def _nullable_bool(value: object, name: str) -> bool | None:
    return None if value is None else _boolean(value, name)


def _reason(value: object, name: str) -> str | None:
    if value is not None and (type(value) is not str or not value):
        raise ValueError(f"{name} must be a nonempty string or null")
    return value


def _status_reason(value: dict[str, object], name: str) -> str:
    status = value["status"]
    if status not in ("available", "partial", "unavailable"):
        raise ValueError(f"{name} status is malformed")
    reason = _reason(value["unavailable_reason"], f"{name} reason")
    if (status == "available") != (reason is None):
        raise ValueError(f"{name} status/reason differs")
    return status


def _state(ready: bool, known_count: int) -> str:
    return "available" if ready else "partial" if known_count else "unavailable"


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "schema_version": 1, "scope": PHASE_EVENT_COMMANDER_TRIGGER_SCOPE,
        "status": "unavailable", "source_ck3_sha256": PHASE_EVENT_COMMANDER_TRIGGER_CK3_SHA256,
        "trigger_source_closed": False, "native_role_and_trigger_evaluation_observed": False,
        "complete_phase_effects_ready": False,
        "unavailable_reason": f"phase_event_commander_trigger_fragment_invalid: {reason}",
        "occurrences": [],
    }


def normalize_phase_event_commander_trigger_conditions_v1(
    value: object, *, armies: list[dict[str, object]],
    role_compatibility: dict[str, object] | None,
    commander_side_identity: dict[str, object] | None,
) -> dict[str, object] | None:
    """Validate the additive leaf against its same-query normalized source facts."""
    if value is None:
        return None
    try:
        root = _object(value, _ROOT_KEYS, "root")
        if type(root["schema_version"]) is not int or root["schema_version"] != 1:
            raise ValueError("schema_version must be 1")
        if root["scope"] != PHASE_EVENT_COMMANDER_TRIGGER_SCOPE:
            raise ValueError("scope is malformed")
        if root["source_ck3_sha256"] != PHASE_EVENT_COMMANDER_TRIGGER_CK3_SHA256:
            raise ValueError("source is not the exact actual4 executable")
        root_status = _status_reason(root, "root")
        closed = _boolean(root["trigger_source_closed"], "trigger_source_closed")
        observed = _boolean(root["native_role_and_trigger_evaluation_observed"], "evaluation observed")
        if root["complete_phase_effects_ready"] is not False:
            raise ValueError("complete_phase_effects_ready must remain false")
        expected = _expected_commanders(armies)
        occurrences = root["occurrences"]
        if not isinstance(occurrences, list) or len(occurrences) != len(expected):
            raise ValueError("occurrences differ from the V2 Commander roster")
        if expected and (not isinstance(role_compatibility, dict)
                         or not isinstance(commander_side_identity, dict)):
            raise ValueError("same-query role and Commander identity leaves are unavailable")
        roles = {
            row["occurrence_index"]: row
            for row in (role_compatibility or {}).get("occurrences", [])
            if row["phase_role"] == "commander"
        }
        identities = {
            row["occurrence_index"]: row
            for row in (commander_side_identity or {}).get("occurrences", [])
        }
        registry = (role_compatibility or {}).get("loaded_registry", {})
        count, registry_rows = registry.get("count_raw"), registry.get("rows", [])
        catalog_extent_observed = (
            type(count) is int and count >= 0 and len(registry_rows) == count
        )
        total_evaluated = total_known = 0
        all_ready = True
        for index, (raw_row, source) in enumerate(zip(occurrences, expected, strict=True)):
            row = _object(raw_row, _OCCURRENCE_KEYS, f"occurrences[{index}]")
            status = _status_reason(row, f"occurrences[{index}]")
            _integer(row["occurrence_index"], "occurrence_index", 0, 2**31 - 1)
            _integer(row["character_id"], "character_id", 0, _UINT32_MAX)
            _integer(row["source_public_cunit_id"], "source_public_cunit_id", -(2**31), 2**31 - 1)
            _nullable_integer(row["source_native_carmy_id"], "source_native_carmy_id", -(2**31), 2**31 - 1)
            if any(row[field] != observed_value for field, observed_value in source.items()):
                raise ValueError(f"occurrences[{index}] changes V2 Commander provenance")
            if _integer(row["requested_role_raw"], "requested_role_raw", 0, _UINT32_MAX) != 0:
                raise ValueError("Commander requested role must be 0")
            role = roles.get(source["occurrence_index"])
            identity = identities.get(source["occurrence_index"])
            if role is None or identity is None:
                raise ValueError("same-query source occurrence is unavailable")
            combat = _nullable_integer(row["actual_combat_full_id_raw"], "actual Combat fullID", 0, _UINT32_MAX)
            side = _nullable_integer(row["actual_side_index"], "actual_side_index", 0, 1)
            named_key = _nullable_integer(row["loaded_named_side_key_raw"], "loaded_named_side_key_raw", -(2**31), 2**31 - 1)
            if combat != identity["actual_selected_combat_full_id_raw"] or side != identity["actual_side_index"]:
                raise ValueError("actual Combat/Side differs from the same-query identity observation")
            context_ready = _boolean(row["current_commander_context_ready"], "current Commander context ready")
            context_qualified = (
                closed and role["native_role_argument_source_closed"] is True
                and commander_side_identity["commander_side_identity_source_closed"] is True
                and identity["full_id_equal"] is True and identity["status"] == "available"
                and combat is not None and side is not None and named_key is not None
            )
            if context_ready and not context_qualified:
                raise ValueError("actual Commander trigger context lacks its source facts")
            conditions = row["conditions"]
            source_conditions = role["conditions"]
            if not isinstance(conditions, list) or len(conditions) != len(source_conditions):
                raise ValueError("conditions differ from the same-query loaded role rows")
            compatible_count = evaluated_count = admitted_count = unknown_count = 0
            for raw_condition, source_condition in zip(conditions, source_conditions, strict=True):
                condition = _object(raw_condition, _CONDITION_KEYS, "condition")
                row_index = _integer(condition["loaded_row_index"], "loaded_row_index", 0, 2**31 - 1)
                compatible = _nullable_bool(condition["role_compatible"], "role_compatible")
                trigger = _nullable_bool(condition["native_trigger_valid"], "native_trigger_valid")
                admitted = _nullable_bool(condition["role_and_trigger_valid"], "role_and_trigger_valid")
                reason = _reason(condition["unavailable_reason"], "condition reason")
                if (row_index != source_condition["loaded_row_index"]
                        or compatible is not source_condition["role_compatible"]):
                    raise ValueError("condition changes the same-query loaded role comparison")
                if compatible is False:
                    if trigger is not None or admitted is not False or reason is not None:
                        raise ValueError("role-false row must skip native evaluation and remain false")
                elif compatible is None:
                    if trigger is not None or admitted is not None or reason is None:
                        raise ValueError("unknown role must preserve unknown trigger/admission")
                elif trigger is None:
                    if admitted is not None or reason is None:
                        raise ValueError("unobserved native trigger must remain unknown with a reason")
                elif not context_ready or admitted is not trigger or reason is not None:
                    raise ValueError("native trigger bool requires current context and equal role/trigger truth")
                compatible_count += int(compatible is True)
                evaluated_count += int(trigger is not None)
                admitted_count += int(admitted is True)
                unknown_count += int(admitted is None)
            counts = {
                "role_compatible_count": compatible_count, "evaluated_count": evaluated_count,
                "admitted_count": admitted_count, "unknown_count": unknown_count,
            }
            for field, computed in counts.items():
                if _integer(row[field], field, 0, _UINT32_MAX) != computed:
                    raise ValueError(f"{field} differs from observed conditions")
            ready = _boolean(row["role_trigger_observation_ready"], "role/trigger observation ready")
            if ready != (catalog_extent_observed and unknown_count == 0):
                raise ValueError("role/trigger readiness differs from known conditions/catalog extent")
            known = len(conditions) - unknown_count
            if status != _state(ready, known):
                raise ValueError("occurrence status differs from condition availability")
            total_evaluated += evaluated_count
            total_known += known
            all_ready = all_ready and ready
        if observed != (total_evaluated > 0):
            raise ValueError("evaluation-observed flag differs from actual predicate result count")
        if root_status != _state(all_ready, total_known):
            raise ValueError("root status differs from occurrence condition availability")
        return copy.deepcopy(root)
    except (ValueError, KeyError, TypeError) as error:
        return _unavailable(str(error))


def current_commander_role_trigger_row_sets(occurrence: dict[str, object]) -> dict[str, object]:
    """Project current admitted/rejected/unknown rows; no event selection or policy."""
    conditions = occurrence["conditions"]
    admitted = [row["loaded_row_index"] for row in conditions if row["role_and_trigger_valid"] is True]
    rejected = [row["loaded_row_index"] for row in conditions if row["role_and_trigger_valid"] is False]
    unknown = [row["loaded_row_index"] for row in conditions if row["role_and_trigger_valid"] is None]
    return {
        "occurrence_index": occurrence["occurrence_index"],
        "role_trigger_observation_ready": occurrence["role_trigger_observation_ready"],
        "admitted_row_indices": admitted, "rejected_row_indices": rejected,
        "unknown_row_indices": unknown, "admitted_count": len(admitted),
        "rejected_count": len(rejected), "unknown_count": len(unknown),
    }
