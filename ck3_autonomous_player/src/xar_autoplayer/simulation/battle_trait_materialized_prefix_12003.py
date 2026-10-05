"""Logical prior-prefix copy/merge from an explicit preparation stage baseline.

Frozen CK3 1.20.0.3 source: v85 empty-destination copy and key-copy contracts,
plus v83 nonempty aggregate insertion. This computes the observed unit-Q
prefix, without constructing allocator state, later trait context or Entries.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from .battle_trait_context_branch_12003 import (
    ContextBranchInputs12003,
    CurrentPriorContextContribution12003,
    CurrentPriorContextInputs12003,
    CurrentPriorContextPrefixResult12003,
    compose_current_prior_context_prefix_12003,
    compose_context_branch_12003,
)
from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003,
    PropertyContainer12003,
    from_raw_numeric_inputs_12003,
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
class PersonStageStartBaseline12003:
    """Caller-supplied logical postreset stage, never a renamed final snapshot.

    ``modeled_new_reset`` projects the direct count stores from explicit entering
    counts. It describes a new conditional numeric model, without asserting
    cleanup completion or historical stage identity. The weighted-zero branch
    still needs its retained aggregate. Physical allocator state is outside it.
    """

    context: NativeModifierContext12003 | Mapping[str, object] | None = None
    character_full_id: int | None = None
    stage: str = "post_291C010_pre_prefix"
    kind: str = "explicit_post_reset_logical_context"
    entering_counts: PreResetCounts12003 | Mapping[str, object] | tuple | list | None = None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class PersonStageContextAssemblyResult12003:
    character_full_id: int | None
    status: str
    assembly_ready: bool
    pre291C204_context: Mapping[str, object] | None
    post291D1D0_context: Mapping[str, object] | None
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    physical_storage_postimage_ready: bool = False
    historical_stage_observed: bool = False
    full_future_context_ready: bool = False
    actual_game_days_advanced: int = 0

    @property
    def ready(self) -> bool:
        return self.assembly_ready

    @property
    def context(self) -> Mapping[str, object] | None:
        return self.post291D1D0_context


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


def _stage_initial_arrays(
    baseline: PersonStageStartBaseline12003 | Mapping[str, object],
    missing: list[str],
) -> tuple[bool, list[int], list[int], Mapping[str, object]]:
    if isinstance(baseline, Mapping):
        baseline = PersonStageStartBaseline12003(
            context=baseline.get("context"),
            character_full_id=baseline.get("character_full_id"),
            stage=baseline.get("stage"), kind=baseline.get("kind"),
            entering_counts=baseline.get("entering_counts"),
            source_provenance=baseline.get("source_provenance"),
        )
    local: list[str] = []
    if baseline.stage != "post_291C010_pre_prefix":
        _gap(local, "stage_start_baseline.stage_post_291C010_pre_prefix")
    if baseline.kind not in ("explicit_post_reset_logical_context", "modeled_new_reset"):
        _gap(local, "stage_start_baseline.kind")
    effects = _reset_effects(baseline.entering_counts)
    after = effects.get("direct_after_counts_i32") if effects else None
    context = baseline.context
    if isinstance(context, Mapping):
        context = from_raw_numeric_inputs_12003({"context": context}).context
    if baseline.kind == "modeled_new_reset":
        if effects is None:
            _gap(local, "stage_start_baseline.entering_counts")
        elif effects["missing_inputs"]:
            for item in effects["missing_inputs"]:
                _gap(local, "stage_start_baseline." + item)
        if context is None and after == (0, 0, 0):
            context = NativeModifierContext12003(PropertyContainer12003((), (), 0), (), 0)
    arrays = None
    if not isinstance(context, NativeModifierContext12003):
        _gap(local, "stage_start_baseline.context")
    else:
        count = context.weighted_count
        if type(count) is not int or native_wrap32_12003(count) != 0:
            _gap(local, "stage_start_baseline.post_reset_weighted_count_zero")
        if context.aggregate_properties is None:
            _gap(local, "stage_start_baseline.aggregate_properties")
        else:
            arrays = _block_arrays(context.aggregate_properties,
                                   "stage_start_baseline.aggregate_properties", local)
        if baseline.kind == "modeled_new_reset" and after is not None and arrays is not None:
            if after != (0, len(arrays[0]), len(arrays[1])):
                _gap(local, "stage_start_baseline.direct_count_postimage")
    for item in local:
        _gap(missing, item)
    ledger = {
        "stage": baseline.stage, "kind": baseline.kind,
        "character_full_id": baseline.character_full_id,
        "input_source": deepcopy(baseline.source_provenance),
        "reset_count_projection": effects,
        "weighted_zero_implies_empty_aggregate": False,
        "current_final_context_used_as_default": False,
        "modeled_new_reset_is_historical_stage_proof": False,
        "native_cleanup_completion_inferred": False,
        "physical_allocator_state_constructed": False,
    }
    return not local, list(arrays[0]) if arrays else [], list(arrays[1]) if arrays else [], ledger


def _fold_property_request(
    keys: list[int], values: list[int], source_keys: tuple[int, ...],
    source_values: tuple[int, ...], weight: int,
    metadata: Mapping[str, object], updates: list[Mapping[str, object]],
) -> str:
    """Shared normal logical postimage of2303120, including23033BC scale."""
    if not keys:
        keys[:] = source_keys
        values[:] = (source_values if weight == Q_12003 else
                     tuple(native_fixed_mul_q_12003(value, weight) for value in source_values))
        updates.append({**metadata, "branch": "bulk_copy_including_FFFF",
                        "weight_q64": weight,
                        "values_scaled": weight != Q_12003,
                        "key_count_i32": native_wrap32_12003(len(keys)),
                        "value_count_i32": native_wrap32_12003(len(values))})
        return "empty_destination_bulk_copy_unit_Q" if weight == Q_12003 else "empty_destination_bulk_copy_scaled_Q"
    for index, (key, value) in enumerate(zip(source_keys, source_values)):
        term = native_fixed_mul_q_12003(value, weight)
        record = {**metadata, "source_property_index": index, "key_u16": key,
                  "source_value_q64": value, "weight_q64": weight, "term_q64": term}
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
    return "nonempty_destination_native_index_fold"


def materialize_current_prior_context_prefix_12003(
    prior_inputs: CurrentPriorContextInputs12003 | CurrentPriorContextPrefixResult12003
                  | Mapping[str, object] | None, *,
    completed_reset_state: CompletedResetContextState12003 | Mapping[str, object] | None = None,
    pre_reset_counts: PreResetCounts12003 | Mapping[str, object] | tuple | list | None = None,
    stage_start_baseline: PersonStageStartBaseline12003 | Mapping[str, object] | None = None,
) -> MaterializedPriorPrefixResult12003:
    """Copy/fold this source-ordered prefix, using only fixed weight100000.

    A supplied leaf or typed input goes through the published v83 composer; an
    already composed result is accepted directly. Only explicit completed-reset
    admission with all three active counts zero supplies the old empty initial
    logical context. An explicit postreset stage baseline also admits the source
    weighted-zero/retained-aggregate branch. Neither asserts a historical stage.

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
    if stage_start_baseline is None and state.admitted_completed is not True:
        _gap(missing, "completed_reset_state.admitted_completed")
    counts = state.active_counts
    if stage_start_baseline is not None:
        actual_counts = None
    elif counts is None or len(counts) != 3:
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
    baseline_ledger = None
    if stage_start_baseline is not None:
        admitted, keys, values, baseline_ledger = _stage_initial_arrays(stage_start_baseline, missing)
        baseline_id = baseline_ledger["character_full_id"]
        if (type(baseline_id) is int and type(prefix.character_full_id) is int
                and baseline_id != prefix.character_full_id):
            _gap(missing, "stage_start_baseline.character_full_id_matches_prefix")
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
            request["branch"] = _fold_property_request(
                keys, values, source_keys, source_values, Q_12003,
                {"source_group": contribution.source_group,
                 "native_index": contribution.native_index}, updates)
        requests.append(request)
    ready = admitted and prefix.contributions_ready and not missing
    known = ({"aggregate_properties": _property_projection(keys, values),
              "weighted_rows": deepcopy(rows),
              "weighted_count": native_wrap32_12003(len(rows))} if admitted else None)
    complete = deepcopy(known) if ready else None
    ledger = {
        "source_scope": "explicit_postreset_current_prior_prefix_unit_Q_logical_postimage",
        "prefix_ledger": deepcopy(prefix.ledger),
        "character_full_id": prefix.character_full_id,
        "completed_reset_admission": state.admitted_completed,
        "supplied_active_counts_i32": actual_counts,
        "completed_reset_source": deepcopy(state.source_provenance),
        "storage_diagnostics": deepcopy(state.storage_diagnostics),
        "reset_count_effects_used_to_infer_cleanup": False,
        "explicit_stage_start_baseline": deepcopy(baseline_ledger),
        "requests": tuple(requests), "aggregate_updates": tuple(updates),
        "known_partial_context_scope":
            "Diagnostic fold of supplied known blocks from the admitted logical state; "
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


def assemble_person_stage_prefix_and_branch_12003(
    prior_inputs: CurrentPriorContextInputs12003 | CurrentPriorContextPrefixResult12003
                  | Mapping[str, object] | None,
    branch_inputs: ContextBranchInputs12003 | Mapping[str, object] | None, *,
    stage_start_baseline: PersonStageStartBaseline12003 | Mapping[str, object],
) -> PersonStageContextAssemblyResult12003:
    """Compose the explicit postreset stage through return from291D1D0.

    Provider base/common/actual-selected requests precede the selected branch
    and positive groups0..6. No current-final baseline is obtained implicitly.
    The returned context is the bounded numeric stage before291C209; later
    preparation, physical allocation and historical frame parity remain open.
    """
    prefix = materialize_current_prior_context_prefix_12003(
        prior_inputs, stage_start_baseline=stage_start_baseline)
    branch = compose_context_branch_12003(branch_inputs)
    missing = list(prefix.missing_inputs)
    for item in branch.missing_inputs:
        _gap(missing, "291D1D0." + item)
    if (type(prefix.character_full_id) is int and type(branch.character_id) is int
            and prefix.character_full_id != branch.character_id):
        _gap(missing, "291D1D0.character_id_matches_prefix")
    before = deepcopy(prefix.raw_context_projection)
    keys: list[int] = []
    values: list[int] = []
    rows: list[Mapping[str, object]] = []
    if before is not None:
        keys = list(before["aggregate_properties"]["keys_u16"])
        values = list(before["aggregate_properties"]["values_q64"])
        rows = deepcopy(before["weighted_rows"])
    updates: list[Mapping[str, object]] = []
    requests: list[Mapping[str, object]] = []
    for contribution in branch.contributions:
        path = "291D1D0." + contribution.source_label
        arrays = _block_arrays(contribution.properties, path, missing)
        weight = native_wrap64_12003(contribution.weight_q64)
        request = {
            "source_label": contribution.source_label,
            "native_order": contribution.native_order,
            "weight_q64": weight,
            "group_count": contribution.group_count,
        }
        if arrays is None:
            request["branch"] = "property_input_partial"
        elif not arrays[0]:
            request["branch"] = "source_count_zero_skip"
        elif before is None:
            request["branch"] = "pre291C204_context_unavailable"
        else:
            source_keys, source_values = arrays
            request["weighted_row_index"] = len(rows)
            rows.append({"native_index": len(rows),
                         "properties": _property_projection(source_keys, source_values),
                         "weight_q64": weight})
            request["branch"] = _fold_property_request(
                keys, values, source_keys, source_values, weight,
                {"source_label": contribution.source_label,
                 "native_order": contribution.native_order}, updates)
        requests.append(request)
    ready = prefix.ready and branch.contributions_ready and not missing
    after = ({"aggregate_properties": _property_projection(keys, values),
              "weighted_rows": deepcopy(rows),
              "weighted_count": native_wrap32_12003(len(rows))} if ready else None)
    ledger = {
        "source_scope": "explicit_post291C010_prefix_then291D1D0_logical_context",
        "stage_order": ("post_291C010_pre_prefix", "provider1530_base",
                        "provider1A48_common", "actual18F8_or19A0_selected",
                        "pre291C204", "291D1D0_selected", "291D1D0_positive_groups0_to6",
                        "post291D1D0_pre291C209"),
        "prefix_ledger": deepcopy(prefix.ledger),
        "branch_ledger": deepcopy(branch.ledger),
        "requests": tuple(requests), "aggregate_updates": tuple(updates),
        "pre291C204_context_ready": prefix.ready,
        "post291D1D0_context_ready": ready,
        "first_copy_FFFF_preserved_and_scaled": True,
        "nonempty_merge_FFFF_skipped": True,
        "nonunit_empty_copy_scale_source": "23033BC..23034A3",
        "current_final_context_used_as_default": False,
        "modeled_new_reset_is_historical_stage_proof": False,
        "native_cleanup_completion_inferred": False,
        "physical_storage_postimage_ready": False,
        "native_write_performed": False,
        "full_future_context_ready": False,
        "later_stage_missing_inputs": ("preA1640", "291E210", "291D460", "291D7E0",
                                      "291DED0", "291DCE0", "post291C2B3_later_suffix"),
        "Entry_refresh_claim": False,
        "actual_game_days_advanced": 0,
    }
    return PersonStageContextAssemblyResult12003(
        prefix.character_full_id, "computed" if ready else "partial", ready,
        before, after, tuple(missing), ledger)
