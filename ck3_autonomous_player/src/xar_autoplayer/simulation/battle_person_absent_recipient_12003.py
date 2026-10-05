"""Current cached absent-1C8 recipient scalar from actual native operands.

Source-first: docs/ck3-native-ai/battle-person-absent-recipient-12003.md.
This consumes the same current-person query's absent_recipient_inputs leaf.
It never initializes native caches, appends a managed block, reconstructs a
stage-start context, or claims actual Entry effectiveness.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from .battle_trait_numeric_inputs_12003 import (
    SOURCE_EXE_SHA256_12003,
    native_fixed_mul_q_12003,
    native_wrap32_12003,
    native_wrap64_12003,
)


@dataclass(frozen=True, slots=True)
class NativeAbsentRecipientResult12003:
    value_q64: int | None
    summed_q64: int | None
    applicable: bool | None
    calculation_ready: bool
    status: str
    missing_inputs: tuple[str, ...]
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    stage_start_baseline_supplied: bool = False
    full_native_callback_ready: bool = False
    actual_entry_effectiveness_ready: bool = False


class _Demand:
    def __init__(self) -> None:
        self.missing: dict[str, None] = {}

    def gap(self, path: str) -> None:
        self.missing[path] = None

    def integer(self, value: object, path: str) -> int | None:
        if type(value) is int:
            return value
        self.gap(path)
        return None

    def q64(self, value: object, path: str) -> int | None:
        number = self.integer(value, path)
        return native_wrap64_12003(number) if number is not None else None

    def word64(self, value: object, path: str) -> int | None:
        # Native pointer diagnostics may serialize as hexadecimal strings.
        if isinstance(value, str) and value.lower().startswith('0x'):
            try:
                value = int(value, 16)
            except ValueError:
                pass
        number = self.integer(value, path)
        return number & ((1 << 64) - 1) if number is not None else None

    def count(self, row: object, path: str) -> int | None:
        if not isinstance(row, Mapping):
            self.gap(path + '.count')
            return None
        count = self.integer(row.get('count'), path + '.count')
        return native_wrap32_12003(count) if count is not None else None

    def item(self, rows: object, index: int, path: str) -> object:
        if isinstance(rows, (tuple, list)) and index < len(rows):
            return rows[index]
        self.gap(path + '[' + str(index) + ']')
        return None


def _aggregate_25d(
    demand: _Demand, container: object,
) -> tuple[int | None, Mapping[str, object]]:
    """2BFB57D's lower_bound on the supplied actual U16 native order."""
    path = 'aggregate_properties'
    count = demand.count(container, path)
    details: dict[str, object] = {'key_u16': 0x25D, 'count': count}
    if count is None:
        return None, details
    if count == 0:
        details['branch'] = 'native_empty_zero'
        return 0, details
    if count < 0:
        demand.gap(path + '.negative_count_address_view')
        return None, details
    keys = container.get('keys_u16')
    offset, remaining = 0, count
    while remaining > 0:
        half = remaining >> 1
        index = offset + half
        key = demand.integer(demand.item(keys, index, path + '.keys_u16'),
                             path + '.keys_u16[' + str(index) + ']')
        if key is None:
            return None, details
        if (key & 0xFFFF) < 0x25D:
            offset += remaining - half
        remaining = half
    if offset == count:
        details['branch'] = 'native_missing_key_zero'
        return 0, details
    key = demand.integer(demand.item(keys, offset, path + '.keys_u16'),
                         path + '.keys_u16[' + str(offset) + ']')
    if key is None:
        return None, details
    if 0x25D < (key & 0xFFFF):
        details['branch'] = 'native_missing_key_zero'
        return 0, details
    value = demand.q64(demand.item(container.get('values_q64'), offset,
                                   path + '.values_q64'),
                        path + '.values_q64[' + str(offset) + ']')
    details.update(branch='value', native_index=offset, value_q64=value)
    return value, details


def _contains(
    demand: _Demand, row: object, count: int, key: int,
    path: str, *, full_qword: bool,
) -> bool | None:
    if count < 0:
        demand.gap(path + '.negative_count_address_view')
        return None
    values = row.get('values_u64' if full_qword else 'values_u32')
    missing = False
    for index in range(count):
        item_path = path + '.values[' + str(index) + ']'
        raw = demand.item(values, index, path + '.values')
        value = (demand.word64(raw, item_path) if full_qword else
                 demand.integer(raw, item_path))
        if value is None:
            missing = True
        elif (value if full_qword else value & 0xFFFFFFFF) == key:
            return True
    return None if missing else False


def _linked_value(
    demand: _Demand, mapping: object, key: int,
) -> tuple[int | None, bool | None, int | None]:
    """Find the full key in actual occupied entries of the native map.

    Native map keys are unique. BE56C0's pointer-key probe implements this
    equality contract; we do not construct temporary native buckets.
    """
    path = 'cached_map_458'
    count = demand.count(mapping, path)
    if count is None:
        return None, None, None
    # 2BFA1B0 copies none when the cached occupied count is nonpositive.
    if count <= 0:
        return 0, False, None
    entries = mapping.get('entries')
    missing = False
    for index in range(count):
        row_path = path + '.entries[' + str(index) + ']'
        row = demand.item(entries, index, path + '.entries')
        if not isinstance(row, Mapping):
            demand.gap(row_path)
            missing = True
            continue
        row_key = demand.word64(row.get('key_object'), row_path + '.key_object')
        if row_key is None:
            missing = True
        elif row_key == key:
            return demand.word64(row.get('value_u64'), row_path + '.value_u64'), True, index
    return (None, None, None) if missing else (0, False, None)


def compute_absent_recipient_from_native_inputs_12003(
    payload: Mapping[str, object] | None,
) -> NativeAbsentRecipientResult12003:
    """Replay the current 440!=0 branch with conditional actual-input demand.

    Missing operands stay partial. Actual count-zero/map-key absence is legal.
    The uncached derived family is an explicit separate source frontier.
    """
    raw = payload if isinstance(payload, Mapping) else {}
    demand = _Demand()
    ledger: dict[str, object] = {
        'source_exe_sha256': SOURCE_EXE_SHA256_12003,
        'source_path': '291F0A0/absent1C8/2BFB4C0/2BFAC30/2BFA1B0/2BFAD50',
        'input_frame': 'current',
        'receiver': {name: deepcopy(raw.get(name)) for name in (
            'associated_full_id', 'associated_resolved_full_id',
            'associated_used_fallback')},
        'native_write_performed': False,
        'stage_start_baseline_supplied': False,
        'actual_entry_effectiveness_ready': False,
        'managed_range_selection_replayed': False,
        'source_map_order': deepcopy(raw.get('cached_map_430')),
        'source_association_order': deepcopy(raw.get('cached_map_458')),
    }
    carrier = raw.get('carrier_present')
    if carrier is True:
        ledger['branch'] = 'present1C8_uses_actual_carrierA0_outside_this_leaf'
        return NativeAbsentRecipientResult12003(
            None, None, False, False, 'not_applicable', (), ledger)
    if carrier is not False:
        demand.gap('carrier_present')
        return NativeAbsentRecipientResult12003(
            None, None, None, False, 'partial', tuple(demand.missing), ledger)
    cache = demand.integer(raw.get('associated_cache_440'), 'associated_cache_440')
    cache_word = native_wrap32_12003(cache) if cache is not None else None
    if cache_word is None or cache_word == 0:
        ledger['branch'] = 'uncached_2BFA420_derived_families' if cache_word == 0 else 'unknown_cache'
        if cache_word == 0:
            demand.gap('uncached_2BFA420.derived_input_families')
        return NativeAbsentRecipientResult12003(
            None, None, True, False, 'partial', tuple(demand.missing), ledger)

    ledger['branch'] = 'current_cached_440_nonzero'
    mapping = raw.get('cached_map_430')
    count = demand.count(mapping, 'cached_map_430')
    assignments: dict[int, int | None] = {}
    trace: list[Mapping[str, object]] = []
    trait_row = raw.get('trait_ids')
    trait_count = demand.count(trait_row, 'trait_ids') if count is not None and count > 0 else None
    entries = mapping.get('entries') if isinstance(mapping, Mapping) else None
    for index in range(max(count or 0, 0)):
        path = 'cached_map_430.entries[' + str(index) + ']'
        row = demand.item(entries, index, 'cached_map_430.entries')
        if not isinstance(row, Mapping):
            demand.gap(path)
            continue
        key = demand.word64(row.get('key_object'), path + '.key_object')
        trait_id = demand.integer(row.get('trait_id_u32'), path + '.trait_id_u32')
        item: dict[str, object] = {
            'input_index': index, 'bucket_index': row.get('bucket_index'),
            'key_object': key, 'trait_id_u32': trait_id,
        }
        admitted = (_contains(demand, trait_row, trait_count,
                              trait_id & 0xFFFFFFFF, 'trait_ids', full_qword=False)
                    if trait_count is not None and trait_id is not None else None)
        item['trait_admitted'] = admitted
        trace.append(item)
        if admitted is not True or key is None:
            continue
        value = demand.q64(row.get('value_q64'), path + '.value_q64')
        item['cached_value_q64'] = value
        members = raw.get('membership_ids')
        member_count = demand.count(members, 'membership_ids')
        matched = None
        linked = None
        if member_count == 0:
            matched = False
            item['membership_branch'] = 'native_empty_list_skip'
        elif member_count is not None:
            linked, found, linked_index = _linked_value(demand, raw.get('cached_map_458'), key)
            item.update(linked_value_u64=linked, association_found=found,
                        association_input_index=linked_index)
            if linked == 0:
                matched = False
                item['membership_branch'] = 'missing_or_zero_linked_value_skip'
            elif linked is not None:
                matched = _contains(demand, members, member_count, linked,
                                    'membership_ids', full_qword=True)
        item['linked_member'] = matched
        if matched is True:
            multiplier = demand.q64(raw.get('member_multiplier_q64'), 'member_multiplier_q64')
            item['member_multiplier_q64'] = multiplier
            value = (native_fixed_mul_q_12003(value, multiplier)
                     if value is not None and multiplier is not None else None)
        elif matched is None:
            value = None
        item['assigned_value_q64'] = value
        item['replaced_prior_assignment'] = key in assignments
        assignments[key] = value

    base, lookup = _aggregate_25d(demand, raw.get('aggregate_properties'))
    sum_complete = not demand.missing
    lower = demand.q64(raw.get('clamp_lower_q64'), 'clamp_lower_q64')
    upper = demand.q64(raw.get('clamp_upper_q64'), 'clamp_upper_q64')
    summed = base if sum_complete else None
    for value in assignments.values():
        summed = (native_wrap64_12003(summed + value)
                  if summed is not None and value is not None else None)
    result = None
    if summed is not None and lower is not None and upper is not None:
        result = lower if summed < lower else min(summed, upper)
    ready = not demand.missing and count is not None and result is not None
    if not ready:
        result = None
    ledger.update(
        contributions=tuple(trace),
        final_assignments=tuple({'key_object': key, 'value_q64': value}
                                for key, value in assignments.items()),
        key25d_lookup=lookup, base_q64=base, summed_q64=summed,
        clamp_lower_q64=lower, clamp_upper_q64=upper,
        final_value_q64=result,
    )
    return NativeAbsentRecipientResult12003(
        result, summed, True, ready, 'computed' if ready else 'partial',
        tuple(demand.missing), ledger)
