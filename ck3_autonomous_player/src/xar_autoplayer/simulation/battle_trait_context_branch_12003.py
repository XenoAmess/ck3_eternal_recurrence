"""Bounded 291D1D0 preparation contributions from actual native operands.

This module does not obtain a context baseline from current final rows, resolve
business categories, invoke a native writer, or construct full future context.
Source: v82 source-lane INPUT-CONTRACT cd1a0e9b, frozen CK3 1.20.0.3.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003,
    PropertyContainer12003,
    WeightedModifierRow12003,
    from_raw_numeric_inputs_12003,
    native_fixed_mul_q_12003,
    native_wrap32_12003,
    native_wrap64_12003,
)

Q_12003 = 100000


@dataclass(frozen=True, slots=True)
class ContextBranchInputs12003:
    flag14: bool | None = None
    selected_property_block: PropertyContainer12003 | None = None
    group_counts: tuple[int | None, ...] | None = None
    group_property_blocks: tuple[PropertyContainer12003 | None, ...] | None = None
    selected_index: int | None = None
    character_id: int | None = None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ContextBranchContribution12003:
    source_label: str
    native_order: int
    weight_q64: int
    properties: PropertyContainer12003
    group_count: int | None = None


@dataclass(frozen=True, slots=True)
class ContextBranchResult12003:
    character_id: int | None
    contributions: tuple[ContextBranchContribution12003, ...]
    contributions_ready: bool
    missing_inputs: tuple[str, ...]
    status: str
    combined_context: NativeModifierContext12003 | None
    context_combination_ready: bool
    context_missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_future_context_ready: bool = False
    actual_game_days_advanced: int = 0


def _tuple(value: object) -> tuple | None:
    return tuple(value) if isinstance(value, (tuple, list)) else None


def _container(value: object) -> PropertyContainer12003 | None:
    if isinstance(value, PropertyContainer12003):
        return value
    if not isinstance(value, Mapping):
        return None
    return PropertyContainer12003(
        keys_u16=_tuple(value.get("keys_u16")),
        values_q64=_tuple(value.get("values_q64")),
        count=value.get("count"),
    )


def from_context_branch_inputs_12003(
    payload: Mapping[str, object] | None, *,
    source_provenance: Mapping[str, object] | None = None,
) -> ContextBranchInputs12003:
    """Consume C's optional current_person_state.context_branch_inputs leaf."""
    raw = payload if isinstance(payload, Mapping) else {}
    blocks = _tuple(raw.get("group_property_blocks"))
    provenance = {
        "carrier_presence": "value" if isinstance(payload, Mapping) else "null_or_absent",
        "character_id": raw.get("character_id"),
        "status": raw.get("status"),
        "ready": raw.get("ready"),
        "unavailable_reason": raw.get("unavailable_reason"),
        "external_source": deepcopy(source_provenance),
    }
    return ContextBranchInputs12003(
        flag14=raw.get("flag14"),
        selected_property_block=_container(raw.get("selected_property_block")),
        group_counts=_tuple(raw.get("group_counts")),
        group_property_blocks=(
            tuple(_container(block) for block in blocks) if blocks is not None else None),
        selected_index=raw.get("selected_index"),
        character_id=raw.get("character_id"),
        source_provenance=provenance,
    )


def _gap(missing: list[str], path: str) -> None:
    if path not in missing:
        missing.append(path)


def _inspect_container(
    value: PropertyContainer12003 | None, path: str, missing: list[str],
) -> str:
    if value is None:
        _gap(missing, path)
        return "unknown"
    count = value.count
    if type(count) is not int:
        _gap(missing, path + ".count")
        return "unknown"
    if count == 0:
        return "empty"
    if count < 0:
        _gap(missing, path + ".count_native_extent")
        return "partial"
    for field, sequence in (("keys_u16", value.keys_u16), ("values_q64", value.values_q64)):
        if sequence is None or len(sequence) < count:
            _gap(missing, path + "." + field)
            continue
        for index, item in enumerate(sequence[:count]):
            valid = type(item) is int
            if field == "keys_u16":
                valid = valid and 0 <= item <= 65535
            if not valid:
                _gap(missing, path + "." + field + "[" + str(index) + "]")
    return "partial" if any(item.startswith(path) for item in missing) else "nonempty"


def _lower_bound(keys: tuple[int, ...], key: int) -> int:
    low, high = 0, len(keys)
    while low < high:
        middle = low + (high - low) // 2
        if keys[middle] < key:
            low = middle + 1
        else:
            high = middle
    return low


def _combine_context(
    prior: NativeModifierContext12003 | None,
    contributions: tuple[ContextBranchContribution12003, ...],
    contributions_ready: bool,
) -> tuple[NativeModifierContext12003 | None, tuple[str, ...], tuple[Mapping, ...]]:
    missing: list[str] = []
    updates: list[Mapping] = []
    if prior is None:
        return None, ("prior_context_pre291C204",), ()
    if not contributions_ready:
        return None, ("branch_contributions_incomplete",), ()
    _inspect_container(
        prior.aggregate_properties, "prior_context.aggregate_properties", missing)
    count = prior.weighted_count
    rows = prior.weighted_rows
    if type(count) is not int or count < 0:
        _gap(missing, "prior_context.weighted_count")
    elif count > 0 and (rows is None or len(rows) < count):
        _gap(missing, "prior_context.weighted_rows")
    if missing:
        return None, tuple(missing), ()
    aggregate = prior.aggregate_properties
    keys = tuple(aggregate.keys_u16[:aggregate.count]) if aggregate.count else ()
    values = [
        native_wrap64_12003(value) for value in
        (aggregate.values_q64[:aggregate.count] if aggregate.count else ())
    ]
    for contribution in contributions:
        properties = contribution.properties
        for index in range(properties.count):
            key = properties.keys_u16[index]
            position = _lower_bound(keys, key)
            if position == len(keys) or keys[position] != key:
                _gap(missing, "aggregate_new_key_postimage[" + str(key) + "]")
                continue
            term = native_fixed_mul_q_12003(
                properties.values_q64[index], contribution.weight_q64)
            before = values[position]
            values[position] = native_wrap64_12003(before + term)
            updates.append({
                "source_label": contribution.source_label, "key_u16": key,
                "source_value_q64": properties.values_q64[index],
                "weight_q64": contribution.weight_q64, "term_q64": term,
                "aggregate_before_q64": before, "aggregate_after_q64": values[position],
            })
    result_rows = (tuple(rows[:count]) if count else ()) + tuple(
        WeightedModifierRow12003(
            properties=contribution.properties,
            weight_q64=contribution.weight_q64,
            native_index=None,
        ) for contribution in contributions
    )
    result_aggregate = (
        PropertyContainer12003(keys, tuple(values), len(keys)) if not missing else None)
    combined = NativeModifierContext12003(
        aggregate_properties=result_aggregate,
        weighted_rows=result_rows,
        weighted_count=native_wrap32_12003(count + len(contributions)),
    )
    return combined, tuple(missing), tuple(updates)


def compose_context_branch_12003(
    inputs: ContextBranchInputs12003 | Mapping[str, object] | None, *,
    prior_context: NativeModifierContext12003 | Mapping[str, object] | None = None,
) -> ContextBranchResult12003:
    """Project the selected contribution, then positive groups 0..6 in source order.

    An absent baseline keeps contributions available and reports its separate
    input gap. Existing-key aggregate arithmetic reuses the adopted native Q
    primitive; new-key storage postimages remain explicit rather than invented.
    """
    if not isinstance(inputs, ContextBranchInputs12003):
        inputs = from_context_branch_inputs_12003(inputs)
    if isinstance(prior_context, Mapping):
        prior_context = from_raw_numeric_inputs_12003(
            {"context": prior_context}).context
    missing: list[str] = []
    contributions: list[ContextBranchContribution12003] = []
    branches: list[Mapping[str, object]] = []

    def append(label: str, order: int, block: PropertyContainer12003 | None,
               weight: int, group_count: int | None, path: str) -> None:
        state = _inspect_container(block, path, missing)
        branches.append({
            "source_label": label, "native_order": order, "weight_q64": weight,
            "group_count": group_count, "property_state": state,
            "branch": ("property_empty_skip" if state == "empty" else
                       "source_append" if state == "nonempty" else "partial_property"),
        })
        if state in ("nonempty", "partial"):
            contributions.append(ContextBranchContribution12003(
                label, order, weight, block, group_count))

    if inputs.flag14 is True:
        append("selected", 0, inputs.selected_property_block, Q_12003, None,
               "selected_property_block")
    elif inputs.flag14 is False:
        branches.append({"source_label": "selected", "native_order": 0,
                         "branch": "flag14_false_skip"})
    else:
        _gap(missing, "flag14")
        branches.append({"source_label": "selected", "native_order": 0,
                         "branch": "flag14_unknown"})

    for group in range(7):
        raw_count = (
            inputs.group_counts[group] if inputs.group_counts is not None
            and group < len(inputs.group_counts) else None)
        label = "group" + str(group)
        if type(raw_count) is not int:
            _gap(missing, "group_counts[" + str(group) + "]")
            branches.append({"source_label": label, "native_order": group + 1,
                             "branch": "group_count_unknown"})
            continue
        count = native_wrap32_12003(raw_count)
        if count <= 0:
            branches.append({
                "source_label": label, "native_order": group + 1,
                "group_count": count, "branch": "count_nonpositive_skip",
            })
            continue
        block = (
            inputs.group_property_blocks[group]
            if inputs.group_property_blocks is not None
            and group < len(inputs.group_property_blocks) else None)
        append(label, group + 1, block,
               native_wrap64_12003(count * Q_12003), count,
               "group_property_blocks[" + str(group) + "]")

    ready = not missing
    contribution_tuple = tuple(contributions)
    combined, context_missing, updates = _combine_context(
        prior_context, contribution_tuple, ready)
    ledger = {
        "source_scope": "bounded291D1D0_preparation_contribution",
        "source_contract_sha256":
            "cd1a0e9bce574d56a8fe64e2224e08dd873ee304f29f347a4e22af605f8326a8",
        "character_id": inputs.character_id,
        "input_source": deepcopy(inputs.source_provenance),
        "initial_flag14": inputs.flag14,
        "selected_index_diagnostic": inputs.selected_index,
        "branches": tuple(branches),
        "aggregate_updates": updates,
        "group_census_boundary":
            "Prepared counts use fresh per-eligible-record government reads. "
            "Initial flag14 alone does not imply zero groups.",
        "native_category_boundary":
            "Actual contributing categories must be observed as0..6 for the "
            "seven-count projection; unsupported/unknown source records are "
            "producer input gaps, never silently clamped/skipped here.",
        "baseline_stage": "explicit actual pre291C204 context only",
        "current_final_context_used_as_default": False,
        "aggregate_and_rows_double_counted": False,
        "new_key_storage_postimage_constructed": False,
        "native_write_performed": False,
        "full_future_context_ready": False,
        "future_changed_counts_requirement":
            "Explicit actual future records/gate/blocks or source-closed producers",
        "Entry_refresh_claim": False,
        "health_RNG_claim": False,
        "actual_game_days_advanced": 0,
    }
    return ContextBranchResult12003(
        inputs.character_id, contribution_tuple, ready, tuple(missing),
        "computed" if ready else "partial", combined, not context_missing,
        context_missing, ledger,
    )
