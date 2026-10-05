"""Actual current task/position operands on the existing person observation.

Task-owner merged aggregates and native emitted declaration rows have distinct
roles. This module preserves native values and only adapts already evaluated
rows into the adopted context primitive; it evaluates no ScriptValue.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, WeightedModifierRow12003,
)

if TYPE_CHECKING:
    from xar_autoplayer.simulation.battle_context_evaluated_rows_12003 import EvaluatedContextModifier12003

_BRANCH_RVAS = {"owned_passive": "291ded0", "councillor_position_task": "291dce0"}
_KINDS = {"task_owner", "position_passive", "position_scoped", "councillor_task"}


def _object(value: object, field: str, keys: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{field} has a malformed schema")
    return value


def _integer(value: object, field: str, minimum: int, maximum: int, *, optional: bool = False):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{field} is outside its native integer domain")
    return value


def _i32(value: object, field: str, *, optional: bool = False):
    return _integer(value, field, -(2**31), 2**31-1, optional=optional)


def _i64(value: object, field: str, *, optional: bool = False):
    return _integer(value, field, -(2**63), 2**63-1, optional=optional)


def _boolean(value: object, field: str, *, optional: bool = False):
    if value is None and optional:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a native Boolean")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _properties(value: object, field: str):
    if value is None:
        return None
    row = _object(value, field, {"count", "keys_u16", "values_q64"})
    count = _i32(row["count"], field+".count", optional=True)
    result = {"count": count}
    for key, minimum, maximum in (("keys_u16", 0, 65535), ("values_q64", -(2**63), 2**63-1)):
        values = row[key]
        if values is not None:
            if not isinstance(values, list):
                raise ValueError(f"{field}.{key} must be a native-order array or null")
            values = [_integer(item, f"{field}.{key}[{i}]", minimum, maximum)
                      for i, item in enumerate(values)]
        result[key] = values
    return result


def _properties_ready(value: dict | None) -> bool:
    return value is not None and value["count"] is not None and value["count"] >= 0 and (
        value["keys_u16"] is not None and value["values_q64"] is not None and
        len(value["keys_u16"]) == value["count"] == len(value["values_q64"]))


def _context(value: object, field: str):
    if value is None:
        return None
    context = _object(value, field, {"aggregate_properties", "weighted_count", "weighted_rows"})
    rows = context["weighted_rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(f"{field}.weighted_rows must be a native-order array or null")
        normalized = []
        for i, item in enumerate(rows):
            name = f"{field}.weighted_rows[{i}]"
            item = _object(item, name, {"native_index", "weight_q64", "properties"})
            normalized.append({"native_index": _i32(item["native_index"], name+".native_index"),
                               "weight_q64": _i64(item["weight_q64"], name+".weight_q64", optional=True),
                               "properties": _properties(item["properties"], name+".properties")})
        rows = normalized
    return {"aggregate_properties": _properties(context["aggregate_properties"], field+".aggregate_properties"),
            "weighted_count": _i32(context["weighted_count"], field+".weighted_count", optional=True),
            "weighted_rows": rows}


def _modifier(value: object, field: str, *, evaluated: bool):
    properties_key = "properties" if evaluated else "declared_properties"
    keys = {"contributor_kind", "scope_root_character_id_raw", "scope_saved_character_id_raw",
            "declaration_scale_q64", properties_key, "modifier_flags_raw", "source_provenance"}
    keys |= {"task_native_index", "declaration_native_index"} if evaluated else {"native_index"}
    row = _object(value, field, keys)
    kind = row["contributor_kind"]
    if kind not in _KINDS:
        raise ValueError(f"{field}.contributor_kind is unknown")
    result = {"contributor_kind": kind,
              "declaration_scale_q64": _i64(row["declaration_scale_q64"], field+".declaration_scale_q64", optional=True),
              properties_key: _properties(row[properties_key], field+"."+properties_key),
              "modifier_flags_raw": _integer(row["modifier_flags_raw"], field+".modifier_flags_raw", 0, 2**64-1, optional=True),
              "source_provenance": _string(row["source_provenance"], field+".source_provenance")}
    for key in ("scope_root_character_id_raw", "scope_saved_character_id_raw"):
        result[key] = _i32(row[key], field+"."+key, optional=True)
    for key in (("task_native_index", "declaration_native_index") if evaluated else ("native_index",)):
        result[key] = _i32(row[key], field+"."+key)
    return result


def _task(value: object, field: str):
    keys = {"native_index", "task_id_raw", "resolved_task_id_raw", "used_native_default", "frozen_raw",
            "incumbent_character_id_raw", "owner_character_id_raw", "task_type_present",
            "original_position_type_present", "native_gate_allowed", "terminal_task_type_present",
            "declarations", "owner_aggregate_properties_ready", "owner_aggregate_properties"}
    task = _object(value, field, keys)
    result = {"native_index": _i32(task["native_index"], field+".native_index"),
              "task_id_raw": _i32(task["task_id_raw"], field+".task_id_raw"),
              "frozen_raw": _integer(task["frozen_raw"], field+".frozen_raw", 0, 255, optional=True)}
    for key in ("resolved_task_id_raw", "incumbent_character_id_raw", "owner_character_id_raw"):
        result[key] = _i32(task[key], field+"."+key, optional=True)
    for key in ("used_native_default", "task_type_present", "original_position_type_present",
                "native_gate_allowed", "terminal_task_type_present"):
        result[key] = _boolean(task[key], field+"."+key, optional=True)
    declarations = task["declarations"]
    if declarations is not None:
        if not isinstance(declarations, list):
            raise ValueError(f"{field}.declarations must be a native-order array or null")
        declarations = [_modifier(row, f"{field}.declarations[{i}]", evaluated=False)
                        for i, row in enumerate(declarations)]
    result["declarations"] = declarations
    result["owner_aggregate_properties"] = _properties(task["owner_aggregate_properties"], field+".owner_aggregate_properties")
    ready = _boolean(task["owner_aggregate_properties_ready"], field+".owner_aggregate_properties_ready")
    if ready and not _properties_ready(result["owner_aggregate_properties"]):
        raise ValueError(f"{field} marks missing owner-aggregate properties ready")
    result["owner_aggregate_properties_ready"] = ready
    return result


def _task_metadata_ready(task: dict, *, councillor: bool = False) -> bool:
    required = ("resolved_task_id_raw", "used_native_default", "frozen_raw",
                "incumbent_character_id_raw", "owner_character_id_raw",
                "task_type_present", "original_position_type_present")
    if any(task[key] is None for key in required):
        return False
    return not (councillor and task["frozen_raw"] == 0 and task["task_type_present"]
                and task["native_gate_allowed"] is None)


def _branch(value: object, field: str, branch: str):
    row = _object(value, field, {"status", "complete_no_contribution", "vectors_ready", "evaluated_rows",
        "prefix_before", "prefix_source", "aggregate_properties_after", "aggregate_source", "unavailable_reason"})
    status = row["status"]
    ready = _boolean(row["vectors_ready"], field+".vectors_ready")
    if status not in {"available", "partial", "unavailable"} or ready != (status == "available"):
        raise ValueError(f"{field} vector availability disagrees")
    rows = row["evaluated_rows"]
    if rows is not None:
        if not isinstance(rows, list):
            raise ValueError(f"{field}.evaluated_rows must be a native-order array or null")
        rows = [_modifier(item, f"{field}.evaluated_rows[{i}]", evaluated=True) for i, item in enumerate(rows)]
    if ready and (rows is None or any(not _properties_ready(item["properties"]) for item in rows)):
        raise ValueError(f"{field} marks unknown evaluated properties ready")
    none = _boolean(row["complete_no_contribution"], field+".complete_no_contribution", optional=True)
    if none is True and (not ready or rows != []):
        raise ValueError(f"{field} complete none must have known empty evaluated rows")
    reason = row["unavailable_reason"]
    if (ready and reason is not None) or (not ready and (not isinstance(reason, str) or not reason)):
        raise ValueError(f"{field} vector availability reason disagrees")
    prefix = _context(row["prefix_before"], field+".prefix_before")
    after = _properties(row["aggregate_properties_after"], field+".aggregate_properties_after")
    rva = _BRANCH_RVAS[branch]
    for operand, source, value, actual_label in (
        ("prefix_before", "prefix_source", prefix, "actual_before_"+rva),
        ("aggregate_properties_after", "aggregate_source", after, "actual_after_"+rva),
    ):
        if row[source] != ("unobserved" if value is None else actual_label):
            raise ValueError(f"{field}.{source} must identify the actual {operand} stage")
    return {"status": status, "complete_no_contribution": none, "vectors_ready": ready,
            "evaluated_rows": rows, "prefix_before": prefix, "prefix_source": row["prefix_source"],
            "aggregate_properties_after": after, "aggregate_source": row["aggregate_source"],
            "unavailable_reason": reason}


def normalize_current_context_task_position_inputs(
    value: object, field: str = "current_context_task_position_inputs", *, expected_character_id: int | None = None,
) -> dict | None:
    """Normalize the optional actual section; null and absent callers stay distinct."""
    if value is None:
        return None
    row = _object(value, field, {"schema_version", "status", "character_id", "raw_task_inputs_ready",
        "branch_vectors_ready", "owner_council_present", "ordered_owned_tasks", "councillor_task_link_present",
        "councillor_task", "owned_passive", "councillor_position_task", "unavailable_reason"})
    if isinstance(row["schema_version"], bool) or row["schema_version"] != 1:
        raise ValueError(f"{field}.schema_version must be1")
    actor = _i32(row["character_id"], field+".character_id")
    if expected_character_id is not None and actor != expected_character_id:
        raise ValueError(f"{field}.character_id disagrees with the enclosing observation")
    raw_ready = _boolean(row["raw_task_inputs_ready"], field+".raw_task_inputs_ready")
    vectors_ready = _boolean(row["branch_vectors_ready"], field+".branch_vectors_ready")
    owner_present = _boolean(row["owner_council_present"], field+".owner_council_present", optional=True)
    link_present = _boolean(row["councillor_task_link_present"], field+".councillor_task_link_present", optional=True)
    tasks = row["ordered_owned_tasks"]
    if tasks is not None:
        if not isinstance(tasks, list):
            raise ValueError(f"{field}.ordered_owned_tasks must be a native-order array or null")
        tasks = [_task(item, f"{field}.ordered_owned_tasks[{i}]") for i, item in enumerate(tasks)]
        if any(task["native_index"] != i for i, task in enumerate(tasks)):
            raise ValueError(f"{field}.ordered_owned_tasks loses native stored order")
    councillor = None if row["councillor_task"] is None else _task(row["councillor_task"], field+".councillor_task")
    if owner_present is False and tasks != []:
        raise ValueError(f"{field} observed null council must have known empty task input")
    if link_present is False and councillor is not None:
        raise ValueError(f"{field} observed absent task link has a task object")
    if raw_ready and (owner_present is None or tasks is None or link_present is None or
                      (link_present and councillor is None) or
                      any(not _task_metadata_ready(task) for task in (tasks or [])) or
                      (councillor is not None and not _task_metadata_ready(councillor, councillor=True))):
        raise ValueError(f"{field} marks unknown raw task inputs ready")
    branches = {key: _branch(row[key], field+"."+key, key) for key in _BRANCH_RVAS}
    if vectors_ready != all(branch["vectors_ready"] for branch in branches.values()):
        raise ValueError(f"{field} branch vector readiness disagrees")
    status = row["status"]
    if status not in {"available", "partial", "unavailable"} or ((status == "available") != (raw_ready and vectors_ready)):
        raise ValueError(f"{field} observation availability disagrees")
    reason = row["unavailable_reason"]
    if (status == "available" and reason is not None) or (status != "available" and
            (not isinstance(reason, str) or not reason)):
        raise ValueError(f"{field} observation availability reason disagrees")
    return {"schema_version": 1, "status": status, "character_id": actor,
            "raw_task_inputs_ready": raw_ready, "branch_vectors_ready": vectors_ready,
            "owner_council_present": owner_present, "ordered_owned_tasks": tasks,
            "councillor_task_link_present": link_present, "councillor_task": councillor,
            **branches, "unavailable_reason": reason}


def _property_input(value: dict | None) -> PropertyContainer12003 | None:
    if value is None:
        return None
    return PropertyContainer12003(
        keys_u16=None if value["keys_u16"] is None else tuple(value["keys_u16"]),
        values_q64=None if value["values_q64"] is None else tuple(value["values_q64"]), count=value["count"])


def _context_input(value: dict | None) -> NativeModifierContext12003 | None:
    if value is None:
        return None
    rows = value["weighted_rows"]
    return NativeModifierContext12003(aggregate_properties=_property_input(value["aggregate_properties"]),
        weighted_rows=None if rows is None else tuple(WeightedModifierRow12003(
            properties=_property_input(row["properties"]), weight_q64=row["weight_q64"],
            native_index=row["native_index"]) for row in rows), weighted_count=value["weighted_count"])


def _context_ready(value: dict | None) -> bool:
    if value is None or not _properties_ready(value["aggregate_properties"]):
        return False
    rows, count = value["weighted_rows"], value["weighted_count"]
    return rows is not None and count is not None and count >= 0 and len(rows) == count and all(
        row["weight_q64"] is not None and _properties_ready(row["properties"]) for row in rows)


@dataclass(frozen=True, slots=True)
class TaskPositionBranchInputs12003:
    branch: str
    observed_source: Mapping | None
    raw_task_inputs_ready: bool
    branch_vectors_ready: bool
    causal_context_operands_ready: bool
    prefix_before_branch: NativeModifierContext12003 | None
    emitted_modifiers: tuple[EvaluatedContextModifier12003, ...] | None
    aggregate_properties_after: PropertyContainer12003 | None
    missing_inputs: tuple[str, ...]

    @property
    def contribution_observation_ready(self) -> bool:
        return self.branch_vectors_ready


def parse_task_position_branch_inputs_12003(
    normalized: Mapping | None, *, branch: str,
) -> TaskPositionBranchInputs12003:
    """Expose actual evaluated operands without re-scaling or appending context.

    Raw registry/gate and owner-aggregate observation remains useful when a
    branch's emitted rows or causal prefix/postaggregate are unobserved.
    """
    if branch not in _BRANCH_RVAS:
        raise ValueError("branch must be owned_passive or councillor_position_task")
    if normalized is None:
        return TaskPositionBranchInputs12003(branch, None, False, False, False, None, None, None,
                                            ("current_context_task_position_inputs",))
    source = normalized[branch]
    missing = []
    if not normalized["raw_task_inputs_ready"]:
        missing.append("raw_task_inputs")
    if not source["vectors_ready"]:
        missing.append(branch+".evaluated_rows:"+source["unavailable_reason"])
    if not _context_ready(source["prefix_before"]):
        missing.append(branch+".actual_prefix_before")
    if not _properties_ready(source["aggregate_properties_after"]):
        missing.append(branch+".actual_aggregate_properties_after")
    rows = source["evaluated_rows"]
    emitted = None
    if rows is not None:
        emitted = ()
    if rows:
        from xar_autoplayer.simulation.battle_context_evaluated_rows_12003 import EvaluatedContextModifier12003
        emitted = tuple(EvaluatedContextModifier12003(
            properties=_property_input(row["properties"]), source_provenance={
                "branch": branch, "character_id": normalized["character_id"],
                **{key: row[key] for key in ("task_native_index", "contributor_kind", "declaration_native_index",
                    "scope_root_character_id_raw", "scope_saved_character_id_raw", "declaration_scale_q64",
                    "modifier_flags_raw", "source_provenance")},
                "properties_are_native_evaluated_scaled": True, "declaration_scale_reapplied": False,
            }) for row in rows)
    return TaskPositionBranchInputs12003(branch, normalized, normalized["raw_task_inputs_ready"],
        source["vectors_ready"], normalized["raw_task_inputs_ready"] and source["vectors_ready"] and _context_ready(source["prefix_before"])
        and _properties_ready(source["aggregate_properties_after"]),
        _context_input(source["prefix_before"]), emitted,
        _property_input(source["aggregate_properties_after"]), tuple(missing))
