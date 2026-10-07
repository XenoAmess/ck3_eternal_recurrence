"""Optional exact4 loaded phase-event role comparisons for the V2 roster.

This leaf compares a loaded role operand with a conditional requested role.
It observes neither native candidate admission nor trigger/selection/effects.
No actual CombatSide or in-battle condition is required.
"""

from __future__ import annotations

import copy


PHASE_EVENT_ROLE_COMPATIBILITY_LEAF = "phase_event_role_compatibility_v1"
PHASE_EVENT_ROLE_COMPATIBILITY_SCOPE = "v2_roster_loaded_event_role_condition"
PHASE_EVENT_ROLE_COMPATIBILITY_CK3_SHA256 = (
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
)
_ROOT_KEYS = {
    "schema_version", "scope", "status", "source_ck3_sha256",
    "loaded_registry_source_closed", "role_compare_source_closed",
    "native_candidate_admission_observed", "complete_phase_effects_ready",
    "unavailable_reason", "loaded_registry", "occurrences",
}
_REGISTRY_KEYS = {"status", "count_raw", "rows", "unavailable_reason"}
_ROW_KEYS = {"loaded_row_index", "role_operand_raw", "status", "unavailable_reason"}
_OCCURRENCE_KEYS = {
    "occurrence_index", "character_id", "source_public_cunit_id",
    "source_native_carmy_id", "source_regiment_id", "encounter_role",
    "phase_role", "requested_role_raw", "native_role_argument_source_closed",
    "conditions",
}
_CONDITION_KEYS = {"loaded_row_index", "role_compatible", "unavailable_reason"}


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


def _reason(value: object, name: str) -> str | None:
    if value is not None and (type(value) is not str or not value):
        raise ValueError(f"{name} must be a nonempty string or null")
    return value


def _status_reason(row: dict[str, object], name: str, statuses: tuple[str, ...]) -> str:
    status = row["status"]
    if status not in statuses:
        raise ValueError(f"{name} status is malformed")
    reason = _reason(row["unavailable_reason"], f"{name}.unavailable_reason")
    if (status == "available") != (reason is None):
        raise ValueError(f"{name} status/reason differs")
    return status


def _expected_occurrences(armies: list[dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for army in armies:
        source = {
            "source_public_cunit_id": army["army_id"],
            "source_native_carmy_id": army["native_carmy_id"],
            "encounter_role": army["encounter_role"],
        }
        commander = army.get("commander")
        if isinstance(commander, dict) and commander.get("status") == "available":
            result.append({
                **source, "occurrence_index": len(result),
                "character_id": commander["character_id"],
                "source_regiment_id": None, "phase_role": "commander",
            })
        knights = army.get("knights")
        members = knights.get("members") if isinstance(knights, dict) else None
        for knight in members if isinstance(members, list) else []:
            result.append({
                **source, "occurrence_index": len(result),
                "character_id": knight["character_id"],
                "source_regiment_id": knight["source_regiment_id"],
                "phase_role": "knight",
            })
    return result


def _unavailable(reason: str) -> dict[str, object]:
    reason = f"phase_event_role_compatibility_fragment_invalid: {reason}"
    return {
        "schema_version": 1, "scope": PHASE_EVENT_ROLE_COMPATIBILITY_SCOPE,
        "status": "unavailable",
        "source_ck3_sha256": PHASE_EVENT_ROLE_COMPATIBILITY_CK3_SHA256,
        "loaded_registry_source_closed": False, "role_compare_source_closed": False,
        "native_candidate_admission_observed": False, "complete_phase_effects_ready": False,
        "unavailable_reason": reason,
        "loaded_registry": {
            "status": "unavailable", "count_raw": None, "rows": [],
            "unavailable_reason": reason,
        },
        "occurrences": [],
    }


def normalize_phase_event_role_compatibility_v1(
    value: object, *, armies: list[dict[str, object]],
) -> dict[str, object] | None:
    """Preserve partial/unavailable role conditions without changing V2 gates."""
    if value is None:
        return None
    try:
        root = _object(value, _ROOT_KEYS, "root")
        if type(root["schema_version"]) is not int or root["schema_version"] != 1:
            raise ValueError("schema_version must be 1")
        if root["scope"] != PHASE_EVENT_ROLE_COMPATIBILITY_SCOPE:
            raise ValueError("scope is malformed")
        if root["source_ck3_sha256"] != PHASE_EVENT_ROLE_COMPATIBILITY_CK3_SHA256:
            raise ValueError("source is not the exact actual4 executable")
        status = _status_reason(root, "root", ("available", "partial", "unavailable"))
        for field in ("loaded_registry_source_closed", "role_compare_source_closed"):
            if type(root[field]) is not bool:
                raise ValueError(f"{field} must be bool")
        for field in ("native_candidate_admission_observed", "complete_phase_effects_ready"):
            if root[field] is not False:
                raise ValueError(f"{field} must remain false")
        registry = _object(root["loaded_registry"], _REGISTRY_KEYS, "loaded_registry")
        registry_status = _status_reason(
            registry, "loaded_registry", ("available", "partial", "unavailable"),
        )
        count = _nullable_integer(registry["count_raw"], "count_raw", -(2**31), 2**31 - 1)
        rows = registry["rows"]
        if not isinstance(rows, list):
            raise ValueError("loaded_registry.rows must be a list")
        if rows and (count is None or count < 0 or len(rows) != count):
            raise ValueError("loaded registry rows differ from observed count")
        if registry_status == "available" and (count is None or count < 0 or len(rows) != count):
            raise ValueError("available registry count is incomplete")
        if registry_status == "partial" and count is None:
            raise ValueError("partial registry must retain its observed count")
        all_rows_observed = registry_status == "available"
        for index, raw_row in enumerate(rows):
            row = _object(raw_row, _ROW_KEYS, f"rows[{index}]")
            if _integer(row["loaded_row_index"], "loaded_row_index", 0, 2**31 - 1) != index:
                raise ValueError("loaded row order/index differs")
            row_status = _status_reason(row, f"rows[{index}]", ("available", "unavailable"))
            role = _nullable_integer(row["role_operand_raw"], "role_operand_raw", 0, 0xFFFFFFFF)
            if (row_status == "available") != (role is not None):
                raise ValueError("loaded row operand/status differs")
            if role is not None and not root["loaded_registry_source_closed"]:
                raise ValueError("loaded role operand lacks source closure")
            all_rows_observed = all_rows_observed and row_status == "available"
        if registry_status == "available" and not all_rows_observed:
            raise ValueError("available registry contains an unavailable row")
        occurrences = root["occurrences"]
        expected = _expected_occurrences(armies)
        if not isinstance(occurrences, list) or len(occurrences) != len(expected):
            raise ValueError("occurrences differ from the complete V2 role roster")
        all_conditions_observed = True
        for index, (raw_occurrence, source) in enumerate(zip(occurrences, expected, strict=True)):
            occurrence = _object(raw_occurrence, _OCCURRENCE_KEYS, f"occurrences[{index}]")
            _integer(occurrence["occurrence_index"], "occurrence_index", 0, 2**31 - 1)
            _integer(occurrence["source_public_cunit_id"], "source_public_cunit_id", -(2**31), 2**31 - 1)
            _integer(occurrence["character_id"], "character_id", 0, 0xFFFFFFFF)
            for field in ("source_native_carmy_id", "source_regiment_id"):
                _nullable_integer(occurrence[field], field, 0, 2**31 - 1)
            if any(occurrence[field] != observed for field, observed in source.items()):
                raise ValueError(f"occurrences[{index}] changes V2 role provenance")
            requested = 0 if source["phase_role"] == "commander" else 1
            if _integer(occurrence["requested_role_raw"], "requested_role_raw", 0, 0xFFFFFFFF) != requested:
                raise ValueError("requested role differs from conditional commander0/knight1")
            caller_closed = occurrence["native_role_argument_source_closed"]
            if type(caller_closed) is not bool:
                raise ValueError("native role caller source flag must be bool")
            if source["phase_role"] == "knight" and caller_closed is not True:
                raise ValueError("the actual knight caller argument must remain source-closed")
            # Actual Commander47 closes implicit EDX0. Retain old conditional
            # false packets; true attributes the caller argument, not this
            # roster Character's current Side membership or native admission.
            conditions = occurrence["conditions"]
            if not isinstance(conditions, list) or len(conditions) != len(rows):
                raise ValueError("conditions differ from the loaded row list")
            for row_index, (raw_condition, row) in enumerate(zip(conditions, rows, strict=True)):
                condition = _object(raw_condition, _CONDITION_KEYS, "condition")
                if _integer(condition["loaded_row_index"], "condition index", 0, 2**31 - 1) != row_index:
                    raise ValueError("condition order/index differs")
                compatible = condition["role_compatible"]
                reason = _reason(condition["unavailable_reason"], "condition reason")
                if compatible is not None and type(compatible) is not bool:
                    raise ValueError("role_compatible must be bool or null")
                if (compatible is None) != (reason is not None):
                    raise ValueError("condition result/reason differs")
                if compatible is not None:
                    if (not root["role_compare_source_closed"]
                            or row["role_operand_raw"] is None
                            or row["status"] != "available"):
                        raise ValueError("role result lacks observed source-closed operands")
                    if compatible is not (row["role_operand_raw"] == requested):
                        raise ValueError("role result differs from unsigned native role comparison")
                else:
                    all_conditions_observed = False
        complete = (root["loaded_registry_source_closed"] and root["role_compare_source_closed"]
                    and all_rows_observed and all_conditions_observed)
        if status == "available" and not complete:
            raise ValueError("available role fragment is incomplete")
        return copy.deepcopy(root)
    except (ValueError, KeyError, TypeError) as error:
        return _unavailable(str(error))


def compatible_loaded_row_indices(occurrence: dict[str, object]) -> list[int]:
    """Project observed compatible rows; unknown rows are retained in the leaf."""
    return [
        condition["loaded_row_index"]
        for condition in occurrence["conditions"]
        if condition["role_compatible"] is True
    ]


def source_qualified_role_row_indices(occurrence: dict[str, object]) -> list[int] | None:
    """Rows compatible with a source-closed role argument, not a participant."""
    if occurrence["native_role_argument_source_closed"] is not True:
        return None
    return compatible_loaded_row_indices(occurrence)
