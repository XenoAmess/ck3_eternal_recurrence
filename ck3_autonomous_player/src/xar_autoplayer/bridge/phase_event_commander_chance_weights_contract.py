"""Optional current Commander compiled chance and native signed weight inputs.

Current numeric row sets do not describe probabilities, a draw, selection,
event fire or effects and do not change the base combat/MC readiness.
"""

from __future__ import annotations

import copy

from .phase_event_commander_side_identity_contract import _expected_commanders


PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_LEAF = "phase_event_commander_chance_weights_v1"
PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_SCOPE = (
    "v2_current_physical_side_commander_loaded_role_trigger_chance_weights"
)
PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_CK3_SHA256 = (
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
)
_ROOT_KEYS = {
    "schema_version", "scope", "status", "source_ck3_sha256", "chance_source_closed",
    "native_chance_evaluation_observed", "complete_phase_effects_ready",
    "unavailable_reason", "occurrences",
}
_OCCURRENCE_KEYS = {
    "occurrence_index", "character_id", "source_public_cunit_id", "source_native_carmy_id",
    "encounter_role", "actual_combat_full_id_raw", "actual_side_index",
    "current_commander_context_ready", "loaded_named_side_key_raw", "conditions",
    "admitted_count", "evaluated_count", "not_admitted_count", "unknown_count",
    "chance_weight_observation_ready", "status", "unavailable_reason",
}
_CONDITION_KEYS = {
    "loaded_row_index", "role_and_trigger_valid", "chance_raw",
    "selection_weight_raw", "unavailable_reason",
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


def _native_weight(chance_raw: int) -> int:
    quotient = abs(chance_raw) // 100_000
    if chance_raw < 0:
        quotient = -quotient
    low32 = quotient & 0xFFFFFFFF
    return low32 - 0x100000000 if low32 >= 0x80000000 else low32


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "schema_version": 1, "scope": PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_SCOPE,
        "status": "unavailable", "source_ck3_sha256": PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_CK3_SHA256,
        "chance_source_closed": False, "native_chance_evaluation_observed": False,
        "complete_phase_effects_ready": False,
        "unavailable_reason": f"phase_event_commander_chance_weights_fragment_invalid: {reason}",
        "occurrences": [],
    }


def normalize_phase_event_commander_chance_weights_v1(
    value: object, *, armies: list[dict[str, object]],
    role_compatibility: dict[str, object] | None,
    commander_trigger_conditions: dict[str, object] | None,
) -> dict[str, object] | None:
    """Preserve source-qualified numeric/skipped/unknown current loaded rows."""
    if value is None:
        return None
    try:
        root = _object(value, _ROOT_KEYS, "root")
        if type(root["schema_version"]) is not int or root["schema_version"] != 1:
            raise ValueError("schema_version must be 1")
        if root["scope"] != PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_SCOPE:
            raise ValueError("scope is malformed")
        if root["source_ck3_sha256"] != PHASE_EVENT_COMMANDER_CHANCE_WEIGHTS_CK3_SHA256:
            raise ValueError("source is not the exact actual4 executable")
        root_status = _status_reason(root, "root")
        closed = _boolean(root["chance_source_closed"], "chance_source_closed")
        observed = _boolean(root["native_chance_evaluation_observed"], "native chance evaluation observed")
        if root["complete_phase_effects_ready"] is not False:
            raise ValueError("complete_phase_effects_ready must remain false")
        expected = _expected_commanders(armies)
        occurrences = root["occurrences"]
        if not isinstance(occurrences, list) or len(occurrences) != len(expected):
            raise ValueError("occurrences differ from the V2 Commander roster")
        if expected and (not isinstance(role_compatibility, dict)
                         or not isinstance(commander_trigger_conditions, dict)):
            raise ValueError("same-query role and current Commander trigger leaves are unavailable")
        triggers = {
            row["occurrence_index"]: row
            for row in (commander_trigger_conditions or {}).get("occurrences", [])
        }
        registry = (role_compatibility or {}).get("loaded_registry", {})
        count, catalog_rows = registry.get("count_raw"), registry.get("rows", [])
        catalog_observed = type(count) is int and count >= 0 and len(catalog_rows) == count
        total_evaluated = total_known = 0
        all_ready = True
        for index, (raw_row, source) in enumerate(zip(occurrences, expected, strict=True)):
            row = _object(raw_row, _OCCURRENCE_KEYS, f"occurrences[{index}]")
            status = _status_reason(row, f"occurrences[{index}]")
            _integer(row["occurrence_index"], "occurrence_index", 0, 2**31 - 1)
            _integer(row["character_id"], "character_id", 0, 0xFFFFFFFF)
            _integer(row["source_public_cunit_id"], "source_public_cunit_id", -(2**31), 2**31 - 1)
            _nullable_integer(row["source_native_carmy_id"], "source_native_carmy_id", -(2**31), 2**31 - 1)
            if any(row[field] != observed_value for field, observed_value in source.items()):
                raise ValueError("occurrence changes V2 Commander provenance")
            trigger = triggers.get(source["occurrence_index"])
            if trigger is None:
                raise ValueError("same-query current Commander trigger occurrence is unavailable")
            _nullable_integer(row["actual_combat_full_id_raw"], "actual Combat fullID", 0, 0xFFFFFFFF)
            _nullable_integer(row["actual_side_index"], "actual_side_index", 0, 1)
            _nullable_integer(row["loaded_named_side_key_raw"], "loaded named Side key", -(2**31), 2**31 - 1)
            for field in ("actual_combat_full_id_raw", "actual_side_index", "loaded_named_side_key_raw"):
                if row[field] != trigger[field]:
                    raise ValueError("chance context changes same-query current trigger facts")
            context_ready = _boolean(row["current_commander_context_ready"], "current Commander context ready")
            if context_ready and (not closed or trigger["current_commander_context_ready"] is not True):
                raise ValueError("chance context lacks source-qualified actual Commander trigger context")
            conditions = row["conditions"]
            source_conditions = trigger["conditions"]
            if not isinstance(conditions, list) or len(conditions) != len(source_conditions):
                raise ValueError("chance conditions differ from same-query trigger rows")
            admitted = evaluated = not_admitted = unknown = 0
            for raw_condition, source_condition in zip(conditions, source_conditions, strict=True):
                condition = _object(raw_condition, _CONDITION_KEYS, "condition")
                row_index = _integer(condition["loaded_row_index"], "loaded_row_index", 0, 2**31 - 1)
                valid = condition["role_and_trigger_valid"]
                if valid is not None:
                    _boolean(valid, "role_and_trigger_valid")
                if (row_index != source_condition["loaded_row_index"]
                        or valid is not source_condition["role_and_trigger_valid"]):
                    raise ValueError("chance condition changes the observed role/trigger truth")
                raw = _nullable_integer(condition["chance_raw"], "chance_raw", -(2**63), 2**63 - 1)
                weight = _nullable_integer(condition["selection_weight_raw"], "selection_weight_raw", -(2**31), 2**31 - 1)
                reason = _reason(condition["unavailable_reason"], "chance reason")
                if (raw is None) != (weight is None):
                    raise ValueError("chance and native weight must be an observed pair or both null")
                if valid is False:
                    if raw is not None or reason is not None:
                        raise ValueError("not-admitted rows must skip chance without invented values")
                    not_admitted += 1
                elif valid is None:
                    if raw is not None or reason is None or reason != source_condition["unavailable_reason"]:
                        raise ValueError("unknown admission must retain its trigger reason and no numeric values")
                    unknown += 1
                else:
                    admitted += 1
                    if raw is None:
                        if reason is None:
                            raise ValueError("demanded unobserved chance requires a local reason")
                        unknown += 1
                    else:
                        if not context_ready or not closed or reason is not None:
                            raise ValueError("observed chance lacks qualified current context")
                        if weight != _native_weight(raw):
                            raise ValueError("weight differs from native signed trunc0/low32 arithmetic")
                        evaluated += 1
            counts = {
                "admitted_count": admitted, "evaluated_count": evaluated,
                "not_admitted_count": not_admitted, "unknown_count": unknown,
            }
            for field, computed in counts.items():
                if _integer(row[field], field, 0, 0xFFFFFFFF) != computed:
                    raise ValueError(f"{field} differs from current chance conditions")
            ready = _boolean(row["chance_weight_observation_ready"], "chance/weight observation ready")
            if ready != (catalog_observed and len(conditions) == count and unknown == 0):
                raise ValueError("chance readiness differs from observed catalog and unknown values")
            known = evaluated + not_admitted
            if status != _state(ready, known):
                raise ValueError("occurrence status differs from known chance/skipped conditions")
            total_evaluated += evaluated
            total_known += known
            all_ready = all_ready and ready
        if observed != (total_evaluated > 0):
            raise ValueError("native evaluation flag differs from observed numeric-pair count")
        if root_status != _state(all_ready, total_known):
            raise ValueError("root status differs from current chance observation availability")
        return copy.deepcopy(root)
    except (ValueError, KeyError, TypeError) as error:
        return _unavailable(str(error))


def current_commander_chance_weight_row_sets(occurrence: dict[str, object]) -> dict[str, object]:
    """Keep signed numerical rows and rejected/unknown rows without probabilities."""
    positive: list[dict[str, int]] = []
    nonpositive: list[dict[str, int]] = []
    not_admitted: list[int] = []
    unknown: list[int] = []
    for row in occurrence["conditions"]:
        if row["role_and_trigger_valid"] is False:
            not_admitted.append(row["loaded_row_index"])
        elif row["chance_raw"] is None:
            unknown.append(row["loaded_row_index"])
        else:
            item = {field: row[field] for field in ("loaded_row_index", "chance_raw", "selection_weight_raw")}
            (positive if row["selection_weight_raw"] > 0 else nonpositive).append(item)
    return {
        "occurrence_index": occurrence["occurrence_index"],
        "chance_weight_observation_ready": occurrence["chance_weight_observation_ready"],
        "positive_rows": positive, "nonpositive_rows": nonpositive,
        "not_admitted_row_indices": not_admitted, "unknown_row_indices": unknown,
    }
