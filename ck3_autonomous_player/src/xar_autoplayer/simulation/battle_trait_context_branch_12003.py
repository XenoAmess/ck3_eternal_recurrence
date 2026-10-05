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


@dataclass(frozen=True, slots=True)
class CurrentPriorContextInputs12003:
    """Current native provider blocks and actual selected-source observation."""

    available: bool | None = None
    reason: str | None = None
    character_full_id: int | None = None
    base_property_block: PropertyContainer12003 | None = None
    common_property_blocks: tuple[PropertyContainer12003 | None, ...] | None = None
    selector: Mapping[str, object] | None = None
    selected_property_blocks: tuple[PropertyContainer12003 | None, ...] | None = None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CurrentPriorContextContribution12003:
    source_group: str
    native_index: int
    native_order: int | None
    weight_q64: int
    properties: PropertyContainer12003


@dataclass(frozen=True, slots=True)
class CurrentPriorContextPrefixResult12003:
    character_full_id: int | None
    contributions: tuple[CurrentPriorContextContribution12003, ...]
    contributions_ready: bool
    missing_inputs: tuple[str, ...]
    status: str
    ledger: Mapping[str, object]
    full_pre291C204_materialized_context_ready: bool = False
    full_future_context_ready: bool = False
    native_write_performed: bool = False
    actual_game_days_advanced: int = 0

    @property
    def ready(self) -> bool:
        return self.contributions_ready


def _current_prior_block(value: object) -> PropertyContainer12003 | None:
    if isinstance(value, PropertyContainer12003):
        return value
    if not isinstance(value, Mapping):
        return None
    rows = _tuple(value.get("rows"))
    if rows is None:
        return PropertyContainer12003(None, None, None)
    return PropertyContainer12003(
        tuple(row.get("key") if isinstance(row, Mapping) else None for row in rows),
        tuple(row.get("value_raw") if isinstance(row, Mapping) else None for row in rows),
        len(rows),
    )


def from_current_prior_context_inputs_12003(
    payload: Mapping[str, object] | None, *,
    source_provenance: Mapping[str, object] | None = None,
) -> CurrentPriorContextInputs12003:
    """Consume current_person_state.current_prior_context_inputs without writers.

    A null block/group is missing; rows=[] is an observed native count zero.
    Group null entries and every original property row retain their positions.
    """
    raw = payload if isinstance(payload, Mapping) else {}
    common = _tuple(raw.get("common_property_blocks"))
    selected = _tuple(raw.get("selected_property_blocks"))
    selector = raw.get("selector")
    provenance = {
        "carrier_presence": "value" if isinstance(payload, Mapping) else "null_or_absent",
        "available": raw.get("available"),
        "reason": raw.get("reason"),
        "character_full_id": raw.get("character_full_id"),
        "external_source": deepcopy(source_provenance),
    }
    return CurrentPriorContextInputs12003(
        available=raw.get("available"),
        reason=raw.get("reason"),
        character_full_id=raw.get("character_full_id"),
        base_property_block=_current_prior_block(raw.get("base_property_block")),
        common_property_blocks=(
            tuple(_current_prior_block(block) for block in common)
            if common is not None else None),
        selector=deepcopy(selector) if isinstance(selector, Mapping) else None,
        selected_property_blocks=(
            tuple(_current_prior_block(block) for block in selected)
            if selected is not None else None),
        source_provenance=provenance,
    )


def compose_current_prior_context_prefix_12003(
    inputs: CurrentPriorContextInputs12003 | Mapping[str, object] | None,
) -> CurrentPriorContextPrefixResult12003:
    """Return known base/common/actual-selected requests with fixed Q weights.

    This reads the observed selector output, including any native opaque path.
    It does not reimplement equality-find, aggregate math, reset or cleanup.
    The output is a prefix request ledger, never a materialized prior context.
    """
    if not isinstance(inputs, CurrentPriorContextInputs12003):
        inputs = from_current_prior_context_inputs_12003(inputs)
    missing: list[str] = []
    contributions: list[CurrentPriorContextContribution12003] = []
    branches: list[Mapping[str, object]] = []
    if inputs.available is not True:
        _gap(missing, "current_prior_context_inputs.available")

    selector = inputs.selector
    if selector is None:
        _gap(missing, "selector")
    else:
        if selector.get("available") is not True:
            _gap(missing, "selector.available")
        if type(selector.get("uses_18f8_source")) is not bool:
            _gap(missing, "selector.uses_18f8_source")
        if type(selector.get("selected_header_offset")) is not int:
            _gap(missing, "selector.selected_header_offset")

    def append(group: str, index: int, order: int | None,
               block: PropertyContainer12003 | None, path: str) -> None:
        state = _inspect_container(block, path, missing)
        branches.append({
            "source_group": group, "native_index": index,
            "native_order": order, "weight_q64": Q_12003,
            "property_state": state,
            "branch": "native_count_zero_skip" if state == "empty" else
                      "known_weighted_request" if state == "nonempty" else
                      "partial_property_request" if state == "partial" else
                      "source_unavailable",
        })
        if state in ("nonempty", "partial"):
            contributions.append(CurrentPriorContextContribution12003(
                group, index, order, Q_12003, block))

    append("base", 0, 0, inputs.base_property_block, "base_property_block")
    common = inputs.common_property_blocks
    if common is None:
        _gap(missing, "common_property_blocks")
        branches.append({"source_group": "common", "branch": "group_unavailable"})
    else:
        for index, block in enumerate(common):
            append("common", index, index + 1, block,
                   "common_property_blocks[" + str(index) + "]")

    selected = inputs.selected_property_blocks
    if selected is None:
        _gap(missing, "selected_property_blocks")
        branches.append({"source_group": "selected", "branch": "group_unavailable"})
    else:
        selected_start = 1 + len(common) if common is not None else None
        for index, block in enumerate(selected):
            append("selected", index,
                   selected_start + index if selected_start is not None else None,
                   block, "selected_property_blocks[" + str(index) + "]")

    ledger = {
        "source_scope": "current_native_prior_prefix_input_requests",
        "source_api_sha256":
            "56afe4418913f525af97fd2556aeffc99b9eb106eeea7b0a1b1eeb82f3e976b4",
        "character_full_id": inputs.character_full_id,
        "input_source": deepcopy(inputs.source_provenance),
        "carrier_available": inputs.available,
        "carrier_reason": inputs.reason,
        "actual_selector_observation": deepcopy(selector),
        "source_order": ("provider1530_base", "provider1A48_common", "actual18F8_or19A0_selected"),
        "branches": tuple(branches),
        "all_weights_q64": Q_12003,
        "original_provider_row_second_qword_used_as_weight": False,
        "ffff_key_rows_preserved": True,
        "selector_membership_recomputed": False,
        "opaque_native_selector_path_used_as_extra_gate": False,
        "native_order_meaning":
            "Source block ordinal, including empty/missing blocks; group and "
            "native index retained. Selected ordinal unknown if common count missing.",
        "current_final_context_used_as_prior_baseline": False,
        "aggregate_reconstructed": False,
        "reset_counts_or_cleanup_executed": False,
        "full_materialized_context_missing_inputs": (
            "actual_reset_branch_and_materialized_pre_prefix_state",
            "complete_native_aggregate_storage_postimage",
        ),
        "full_pre291C204_materialized_context_ready": False,
        "full_future_context_ready": False,
        "future_trait_changed_provider_or_selector_inferred": False,
        "Entry_refresh_claim": False,
        "health_RNG_date_claim": False,
        "native_write_performed": False,
        "actual_game_days_advanced": 0,
    }
    ready = not missing
    return CurrentPriorContextPrefixResult12003(
        inputs.character_full_id, tuple(contributions), ready, tuple(missing),
        "computed" if ready else "partial", ledger,
    )
