"""Logical prior-prefix copy/merge after an explicitly completed empty reset.

Frozen CK3 1.20.0.3 source: v85 empty-destination copy and key-copy contracts,
plus v83 nonempty aggregate insertion. This computes the observed unit-Q
prefix, without constructing allocator state, later trait context or Entries.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from .battle_trait_context_branch_12003 import (
    CurrentPriorContextContribution12003,
    CurrentPriorContextInputs12003,
    CurrentPriorContextPrefixResult12003,
    compose_current_prior_context_prefix_12003,
)
from .battle_trait_numeric_inputs_12003 import (
    PropertyContainer12003,
    native_fixed_mul_q_12003,
    native_wrap32_12003,
    native_wrap64_12003,
)

Q_12003 = 100000


@dataclass(frozen=True, slots=True)
class PreResetCounts12003:
    weighted_row_count_i32: int | None = None
    aggregate_key_count_i32: int | None = None
    aggregate_value_count_i32: int | None = None


@dataclass(frozen=True, slots=True)
class CompletedResetContextState12003:
    admitted_completed: bool | None = None
    active_counts: tuple[int | None, ...] | None = None
    source_provenance: Mapping[str, object] | None = None
    storage_diagnostics: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class MaterializedPriorPrefixResult12003:
    character_full_id: int | None
    status: str
    materialized_prefix_ready: bool
    aggregate_keys_u16: tuple[int, ...] | None
    aggregate_values_q64: tuple[int, ...] | None
    aggregate_key_count_i32: int | None
    aggregate_value_count_i32: int | None
    weighted_rows: tuple[Mapping[str, object], ...] | None
    weighted_count_i32: int | None
    raw_context_projection: Mapping[str, object] | None
    known_partial_context: Mapping[str, object] | None
    contributions: tuple[CurrentPriorContextContribution12003, ...]
    missing_inputs: tuple[str, ...]
    reset_count_effects: Mapping[str, object] | None
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    physical_storage_postimage_ready: bool = False
    full_future_context_ready: bool = False
    actual_game_days_advanced: int = 0

    @property
    def ready(self) -> bool:
        return self.materialized_prefix_ready

    @property
    def context(self) -> Mapping[str, object] | None:
        return self.raw_context_projection


def from_completed_reset_context_state_12003(
    payload: Mapping[str, object] | None,
) -> CompletedResetContextState12003:
    raw = payload if isinstance(payload, Mapping) else {}
    counts = raw.get("active_counts")
    return CompletedResetContextState12003(
        admitted_completed=raw.get("admitted_completed"),
        active_counts=tuple(counts) if isinstance(counts, (list, tuple)) else None,
        source_provenance=deepcopy(raw.get("source_provenance")),
        storage_diagnostics=deepcopy(raw.get("storage_diagnostics")),
    )


def _gap(missing: list[str], path: str) -> None:
    if path not in missing:
        missing.append(path)


def _reset_effects(
    counts: PreResetCounts12003 | Mapping[str, object] | tuple | list | None,
) -> Mapping[str, object] | None:
    if counts is None:
        return None
    if isinstance(counts, Mapping):
        counts = PreResetCounts12003(
            counts.get("weighted_row_count_i32"),
            counts.get("aggregate_key_count_i32"),
            counts.get("aggregate_value_count_i32"),
        )
    elif isinstance(counts, (tuple, list)):
        counts = PreResetCounts12003(*(counts[index] if index < len(counts) else None
                                     for index in range(3)))
    raw = (counts.weighted_row_count_i32, counts.aggregate_key_count_i32,
           counts.aggregate_value_count_i32)
    before = tuple(native_wrap32_12003(value) if type(value) is int else None
                   for value in raw)
    if before[0] is None:
        after = (None, None, None)
        branch = "weighted_count_unavailable"
    elif before[0] != 0:
        after = (0, 0, 0)
        branch = "weighted_nonzero_clear_three_counts"
    else:
        after = before
        branch = "weighted_zero_preserve_three_counts"
    return {
        "before_counts_i32": before, "direct_after_counts_i32": after,
        "branch": branch, "cleanup_completion_inferred": False,
        "capacity_retention_inferred": False,
        "missing_inputs": tuple("pre_reset_counts[" + str(index) + "]"
                                for index, value in enumerate(after) if value is None),
    }


def _block_arrays(
    block: PropertyContainer12003, path: str, missing: list[str],
) -> tuple[tuple[int, ...], tuple[int, ...]] | None:
    if type(block.count) is not int:
        _gap(missing, path + ".count")
        return None
    count = native_wrap32_12003(block.count)
    if count < 0:
        # Native copies store n<0 as n. A row-list projection cannot turn it
        # into an empty array, and must keep the actual count in its ledger.
        _gap(missing, path + ".negative_native_count")
        return None
    if count == 0:
        return (), ()
    keys, values = block.keys_u16, block.values_q64
    valid = True
    for name, sequence in (("keys_u16", keys), ("values_q64", values)):
        if sequence is None or len(sequence) < count:
            _gap(missing, path + "." + name)
            valid = False
            continue
        for index, item in enumerate(sequence[:count]):
            present = type(item) is int
            if name == "keys_u16":
                present = present and 0 <= item <= 65535
            if not present:
                _gap(missing, path + "." + name + "[" + str(index) + "]")
                valid = False
    if not valid:
        return None
    return tuple(keys[:count]), tuple(native_wrap64_12003(value)
                                      for value in values[:count])


def _lower_bound(keys: list[int], key: int) -> int:
    low, high = 0, len(keys)
    while low < high:
        middle = low + (high - low) // 2
        if keys[middle] < key:
            low = middle + 1
        else:
            high = middle
    return low


def _property_projection(keys: tuple | list, values: tuple | list) -> Mapping:
    return {"keys_u16": list(keys), "values_q64": list(values),
            "count": native_wrap32_12003(len(keys))}


def materialize_current_prior_context_prefix_12003(
    prior_inputs: CurrentPriorContextInputs12003 | CurrentPriorContextPrefixResult12003
                  | Mapping[str, object] | None, *,
    completed_reset_state: CompletedResetContextState12003 | Mapping[str, object] | None,
    pre_reset_counts: PreResetCounts12003 | Mapping[str, object] | tuple | list | None = None,
) -> MaterializedPriorPrefixResult12003:
    """Copy/fold this source-ordered prefix, using only fixed weight100000.

    A supplied leaf or typed input goes through the published v83 composer; an
    already composed result is accepted directly. Only explicit completed-reset
    admission with all three active counts zero supplies the empty initial
    logical context. Pre-reset count effects are separate diagnostics.

    The complete ``raw_context_projection`` replaces only ``context`` in an
    explicit six-skill input carrier. Missing prefix operands retain requests
    and a fold of known blocks, but leave that complete projection unavailable.
    """
    prefix = (prior_inputs if isinstance(prior_inputs, CurrentPriorContextPrefixResult12003)
              else compose_current_prior_context_prefix_12003(prior_inputs))
    state = (completed_reset_state
             if isinstance(completed_reset_state, CompletedResetContextState12003)
             else from_completed_reset_context_state_12003(completed_reset_state))
    missing = list(prefix.missing_inputs)
    effects = _reset_effects(pre_reset_counts)
    if state.admitted_completed is not True:
        _gap(missing, "completed_reset_state.admitted_completed")
    counts = state.active_counts
    if counts is None or len(counts) != 3:
        _gap(missing, "completed_reset_state.active_counts")
        actual_counts = None
    else:
        actual_counts = tuple(native_wrap32_12003(value) if type(value) is int else None
                              for value in counts)
        for index, value in enumerate(actual_counts):
            if value is None:
                _gap(missing, "completed_reset_state.active_counts[" + str(index) + "]")
            elif value != 0:
                _gap(missing, "completed_reset_state.nonempty_initial_counts[" + str(index) + "]")
    admitted = state.admitted_completed is True and actual_counts == (0, 0, 0)
    keys: list[int] = []
    values: list[int] = []
    rows: list[Mapping[str, object]] = []
    updates: list[Mapping[str, object]] = []
    requests: list[Mapping[str, object]] = []
    for contribution in prefix.contributions:
        path = (contribution.source_group + "[" + str(contribution.native_index) + "]")
        request = {
            "source_group": contribution.source_group,
            "native_index": contribution.native_index,
            "native_order": contribution.native_order,
            "source_count_i32": contribution.properties.count,
            "weight_q64": contribution.weight_q64,
        }
        arrays = _block_arrays(contribution.properties, path, missing)
        if contribution.weight_q64 != Q_12003:
            _gap(missing, path + ".unit_Q_weight_source_scope")
            request["branch"] = "nonunit_weight_not_in_copy_contract"
        elif arrays is None:
            request["branch"] = "property_input_partial"
        elif not arrays[0]:
            request["branch"] = "source_count_zero_skip"
        elif not admitted:
            request["branch"] = "known_request_initial_state_unavailable"
        else:
            source_keys, source_values = arrays
            row_index = len(rows)
            rows.append({
                "native_index": row_index,
                "properties": _property_projection(source_keys, source_values),
                "weight_q64": Q_12003,
            })
            request["weighted_row_index"] = row_index
            if not keys:
                keys = list(source_keys)
                values = list(source_values)
                request["branch"] = "empty_destination_bulk_copy_unit_Q"
                updates.append({"source_group": contribution.source_group,
                                "native_index": contribution.native_index,
                                "branch": "bulk_copy_including_FFFF",
                                "key_count_i32": native_wrap32_12003(len(keys)),
                                "value_count_i32": native_wrap32_12003(len(values))})
            else:
                request["branch"] = "nonempty_destination_native_index_fold"
                for index, (key, value) in enumerate(zip(source_keys, source_values)):
                    term = native_fixed_mul_q_12003(value, Q_12003)
                    record = {"source_group": contribution.source_group,
                              "native_index": contribution.native_index,
                              "source_property_index": index, "key_u16": key,
                              "source_value_q64": value, "term_q64": term}
                    if key == 65535:
                        record["branch"] = "FFFF_skip_after_term_computation"
                    else:
                        position = _lower_bound(keys, key)
                        if position == len(keys) or keys[position] != key:
                            keys.insert(position, key)
                            values.insert(position, 0)
                            record["branch"] = "key_insert_parallel_zero"
                        else:
                            record["branch"] = "existing_key_add"
                        before = values[position]
                        values[position] = native_wrap64_12003(before + term)
                        record.update({"position": position, "aggregate_before_q64": before,
                                       "aggregate_after_q64": values[position],
                                       "key_count_i32": native_wrap32_12003(len(keys)),
                                       "value_count_i32": native_wrap32_12003(len(values))})
                    updates.append(record)
        requests.append(request)
    ready = admitted and prefix.contributions_ready and not missing
    known = ({"aggregate_properties": _property_projection(keys, values),
              "weighted_rows": deepcopy(rows),
              "weighted_count": native_wrap32_12003(len(rows))} if admitted else None)
    complete = deepcopy(known) if ready else None
    ledger = {
        "source_scope": "completed_empty_reset_current_prior_prefix_unit_Q_logical_postimage",
        "prefix_ledger": deepcopy(prefix.ledger),
        "character_full_id": prefix.character_full_id,
        "completed_reset_admission": state.admitted_completed,
        "supplied_active_counts_i32": actual_counts,
        "completed_reset_source": deepcopy(state.source_provenance),
        "storage_diagnostics": deepcopy(state.storage_diagnostics),
        "reset_count_effects_used_to_infer_cleanup": False,
        "requests": tuple(requests), "aggregate_updates": tuple(updates),
        "known_partial_context_scope":
            "Diagnostic fold of supplied known blocks from the admitted empty state; "
            "unknown blocks may change this postimage, so it is never a full input carrier.",
        "copy_source_count_domain": "paired nonnegative complete property arrays",
        "negative_native_count_clamped_to_zero": False,
        "first_copy_FFFF_preserved": True,
        "nonempty_merge_FFFF_skipped": True,
        "source_order_and_duplicate_keys_preserved": True,
        "new_key_parallel_value_before_add": 0,
        "integer_semantics": "unsigned U16 lower_bound, wrap32 counts, wrap64 Q sums",
        "capacity_used_as_numeric_gate": False,
        "aggregate_and_weighted_rows_double_counted": False,
        "current_final_context_used_as_initial_state": False,
        "physical_allocator_or_pointer_state_constructed": False,
        "full_future_context_ready": False, "Entry_refresh_claim": False,
        "health_RNG_date_claim": False, "actual_game_days_advanced": 0,
        "source_contracts": {
            "A_empty_copy": "790dcaa57b8953791bb74ef49163e541b39837503d0a7aff272621e10396d48c",
            "B_key_copy": "b7084b7314fd83d65a2a636e691c51879b0e2fc9f1392eb57325075261cf4f58",
            "v83_nonempty_fold": "80bf1624500ce37ed914ba80d75a8213b758e0c63a7ae8f1d5239e942cb9917f",
            "C_reset_inputs": "474a9750cde9bea70f1bd49c71e1d6d47f1e61c4546a7ff081faa633b4a9671d",
        },
    }
    return MaterializedPriorPrefixResult12003(
        character_full_id=prefix.character_full_id,
        status="computed" if ready else "partial",
        materialized_prefix_ready=ready,
        aggregate_keys_u16=tuple(keys) if ready else None,
        aggregate_values_q64=tuple(values) if ready else None,
        aggregate_key_count_i32=native_wrap32_12003(len(keys)) if ready else None,
        aggregate_value_count_i32=native_wrap32_12003(len(values)) if ready else None,
        weighted_rows=tuple(deepcopy(rows)) if ready else None,
        weighted_count_i32=native_wrap32_12003(len(rows)) if ready else None,
        raw_context_projection=complete,
        known_partial_context=deepcopy(known) if admitted and not ready else None,
        contributions=prefix.contributions, missing_inputs=tuple(missing),
        reset_count_effects=effects, ledger=ledger,
    )
