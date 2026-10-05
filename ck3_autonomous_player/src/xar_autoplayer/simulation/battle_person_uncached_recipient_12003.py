"""Exact current absent-1C8/cache440-zero recipient, without native writes.

Source-first: battle-person-uncached-recipient-inputs-12003.md. Temporary
record maps below are computed outputs, never observations of cached430/458.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping

from .battle_person_absent_recipient_12003 import (
    _Demand, NativeAbsentRecipientResult12003,
    compute_absent_recipient_from_native_inputs_12003,
)
from .battle_trait_numeric_inputs_12003 import (
    SOURCE_EXE_SHA256_12003,
    native_wrap32_12003, native_wrap64_12003,
)


@dataclass(slots=True)
class _Record:
    key: int
    key_id: int
    value: int
    priority: int
    kind: int


def native_uncached_fixed_mul_q_12003(a: int, b: int) -> int:
    """9D20/DEC0 divide the signed max operand in the decomposed branch."""
    a, b = native_wrap64_12003(a), native_wrap64_12003(b)
    bound = 3037000499
    def trunc_q(value: int) -> int:
        return (abs(value) // 100000) * (-1 if value < 0 else 1)
    if -bound <= a <= bound and -bound <= b <= bound:
        return trunc_q(native_wrap64_12003(a * b))
    lo, hi = min(a, b), max(a, b)
    quotient = trunc_q(hi)
    remainder = native_wrap64_12003(hi - native_wrap64_12003(quotient * 100000))
    return native_wrap64_12003(native_wrap64_12003(quotient * lo)
                             + trunc_q(native_wrap64_12003(remainder * lo)))


class _Reducer:
    """2BFD580/2BFDEC0 ordered state, including rejected tie-group removal."""
    def __init__(self, demand: _Demand, raw: Mapping[str, object]) -> None:
        self.demand, self.raw = demand, raw
        self.groups: dict[int, list[_Record]] = {2: [], 1: []}
        self.seeds: list[_Record] = []
        self.thresholds = {1: (4, 0), 2: (4, 0)}
        self.trace: list[dict[str, object]] = []

    def sort(self, kind: int) -> None:
        self.groups[kind].sort(key=lambda r: (r.priority, -r.value, -r.key_id))

    def remove(self, kind: int, key: int) -> None:
        self.groups[kind][:] = [r for r in self.groups[kind] if r.key != key]
        self.sort(kind)

    def append(self, candidate: _Record) -> None:
        seed = next((r for r in self.seeds if r.key == candidate.key), None)
        value = candidate.value
        if seed is not None and seed.kind == candidate.kind:
            boost = self.demand.q64(self.raw.get('seed_boost_multiplier_q64'),
                                    'seed_boost_multiplier_q64')
            if boost is not None:
                value = native_wrap64_12003(value + native_uncached_fixed_mul_q_12003(seed.value, boost))
        self.groups[candidate.kind].append(_Record(
            candidate.key, candidate.key_id, value, candidate.priority, candidate.kind))
        self.sort(candidate.kind)

    def offer(self, key: int, key_id: int, kind: int, value: int, priority: int,
              source: str) -> bool:
        item = {'source': source, 'key_object': key, 'kind': kind,
                'value_q64': value, 'priority_u8': priority}
        self.trace.append(item)
        if kind == 0:
            item.update(accepted=False, branch='kind0_skip')
            return False
        candidate = _Record(key, key_id, value, priority, kind)
        if priority == 1:
            self.seeds.append(candidate)
        existing = next((r for k in (2, 1) for r in self.groups[k] if r.key == key), None)
        cap = self.demand.integer(self.raw.get('cap_i32'), 'cap_i32')
        if cap is None:
            item.update(accepted=False, branch='capacity_unavailable')
            return False
        room = len(self.groups[kind]) < native_wrap32_12003(cap)
        if existing is not None and existing.priority == 1 and priority != 1 and (
                room or kind == existing.kind):
            self.remove(existing.kind, key)
            self.append(candidate)
            item.update(accepted=True, branch='replace_seed')
            return True
        threshold_priority, threshold_value = self.thresholds[kind]
        if threshold_priority < priority or (
                threshold_priority == priority and threshold_value >= value):
            item.update(accepted=False, branch='cached_threshold_reject')
            return False
        worst = self.groups[kind][-1] if not room and self.groups[kind] else None
        if worst is not None and (worst.priority < priority or (
                worst.priority == priority and worst.value >= value)):
            if (worst.priority != priority or worst.value != value or worst.key == key):
                item.update(accepted=False, branch='worst_reject')
                return False
            # D842's removal order is swap-last, followed by stable sort.
            rows, index = self.groups[kind], 0
            while index < len(rows):
                if rows[index].priority == priority and rows[index].value == value:
                    rows[index] = rows[-1]
                    rows.pop()
                else:
                    index += 1
            self.sort(kind)
            self.thresholds[kind] = (priority, value)
            item.update(accepted=False, branch='invalidate_equal_group')
            return False
        if existing is not None:
            if existing.priority < priority or (
                    existing.priority == priority and existing.value >= value):
                item.update(accepted=False, branch='existing_reject')
                return False
            if existing.kind == kind:
                existing.value, existing.priority = value, priority
                self.sort(kind)
                item.update(accepted=True, branch='in_place_no_seed_boost')
                return True
            self.remove(existing.kind, key)
        if worst is not None:
            self.remove(kind, worst.key)
        self.append(candidate)
        item.update(accepted=True, branch='append')
        return True


def _family(demand: _Demand, raw: Mapping[str, object], value: object,
            path: str) -> list[tuple[int, int, int, int]]:
    """42149A0 stable signed-ID keys then 42148C0 strict positive lookup."""
    if not isinstance(value, Mapping):
        demand.gap(path)
        return []
    rows: list[tuple[int, int, int, int]] = []
    for kind, name in ((1, 'first'), (2, 'second')):
        vector = value.get(name)
        count = demand.count(vector, path + '.' + name)
        if count is None:
            continue
        if count < 0:
            demand.gap(path + '.' + name + '.negative_count_address_view')
            continue
        for index in range(count):
            rp = path + '.' + name + '.records[' + str(index) + ']'
            row = demand.item(vector.get('records'), index, path + '.' + name + '.records')
            if not isinstance(row, Mapping):
                demand.gap(rp)
                continue
            marker = demand.integer(row.get('marker_u8'), rp + '.marker_u8')
            if marker is None:
                continue
            if marker == 2:
                key = demand.word64(row.get('key_object'), rp + '.key_object')
                key_id = demand.integer(row.get('key_id_i32'), rp + '.key_id_i32')
            else:
                key = demand.word64(raw.get('fallback_key_object'), 'fallback_key_object')
                key_id = demand.integer(raw.get('fallback_key_id_i32'), 'fallback_key_id_i32')
            q64 = demand.q64(row.get('value_q64'), rp + '.value_q64')
            if key is not None and key_id is not None and q64 is not None:
                rows.append((key, native_wrap32_12003(key_id), kind, q64))
    keys = sorted([(r[0], r[1]) for r in rows], key=lambda r: r[1])
    unique: list[tuple[int, int]] = []
    for row in keys:
        if not unique or unique[-1][0] != row[0]:
            unique.append(row)
    out = []
    for key, key_id in unique:
        selected_kind, selected_value = 0, 0
        for row_key, _, kind, q64 in rows:
            if row_key == key and q64 > selected_value:
                selected_kind, selected_value = kind, q64
        out.append((key, key_id, selected_kind, selected_value))
    return out


def compute_uncached_recipient_from_native_inputs_12003(
    payload: Mapping[str, object] | None,
) -> NativeAbsentRecipientResult12003:
    raw = payload if isinstance(payload, Mapping) else {}
    demand = _Demand()
    ledger: dict[str, object] = {
        'source_exe_sha256': SOURCE_EXE_SHA256_12003,
        'source_path': 'absent1C8/2BFB4C0/440zero/2BFA420', 'input_frame': 'current',
        'raw_input_families': deepcopy(raw), 'native_write_performed': False,
        'stage_start_baseline_supplied': False, 'actual_entry_effectiveness_ready': False,
    }
    carrier = raw.get('carrier_present')
    if carrier is True:
        return NativeAbsentRecipientResult12003(None, None, False, False, 'not_applicable', (), ledger)
    if carrier is not False:
        demand.gap('carrier_present')
        return NativeAbsentRecipientResult12003(None, None, None, False, 'partial', tuple(demand.missing), ledger)
    cache = demand.integer(raw.get('associated_cache_440'), 'associated_cache_440')
    if cache is not None and native_wrap32_12003(cache) != 0:
        return NativeAbsentRecipientResult12003(None, None, False, False, 'not_applicable', (), ledger)
    reducer = _Reducer(demand, raw)
    positive: dict[int, int] = {}
    negative: dict[int, int] = {}
    objects: dict[int, Mapping[str, object]] = {}
    for pair in _family(demand, raw, raw.get('seed_family'), 'seed_family'):
        reducer.offer(*pair, 1, 'seed_definition_648')
    contexts = raw.get('active_context')
    context_count: int | None = None
    for name, priority in (('active_objects', None), ('removed_objects', 2)):
        vector = raw.get(name)
        count = demand.count(vector, name)
        if count is None:
            continue
        if count < 0:
            demand.gap(name + '.negative_count_address_view')
            continue
        for index in range(count):
            path = name + '.entries[' + str(index) + ']'
            row = demand.item(vector.get('entries'), index, name + '.entries')
            if not isinstance(row, Mapping):
                demand.gap(path)
                continue
            pointer = demand.word64(row.get('object'), path + '.object')
            if pointer is None:
                continue
            objects[pointer] = row
            pairs = _family(demand, raw, row.get('intrinsic_family'), path + '.intrinsic_family')
            if not pairs:
                continue
            multiplier = None
            selected_priority = priority
            if priority is None:
                if context_count is None:
                    context_count = demand.count(contexts, 'active_context')
                matched = None
                for ci in range(max(context_count or 0, 0)):
                    cr = demand.item(contexts.get('entries'), ci, 'active_context.entries')
                    if not isinstance(cr, Mapping):
                        demand.gap('active_context.entries[' + str(ci) + ']')
                        continue
                    cp = demand.word64(cr.get('object'), 'active_context.entries[' + str(ci) + '].object')
                    if cp == pointer:
                        matched = cr
                        break
                if matched is None:
                    continue
                flag = demand.integer(matched.get('flag_u8'), 'active_context.matched.flag_u8')
                if flag is None:
                    continue
                selected_priority = 0 if flag == 4 else 3
                operand = 'active_flag4_multiplier_q64' if flag == 4 else 'active_other_multiplier_q64'
                multiplier = demand.q64(raw.get(operand), operand)
            for key, key_id, kind, q64 in pairs:
                if priority is None:
                    if multiplier is None:
                        continue
                    q64 = native_uncached_fixed_mul_q_12003(q64, multiplier)
                if reducer.offer(key, key_id, kind, q64, selected_priority, path):
                    (positive if priority is None else negative)[key] = pointer

    materialized: dict[int, _Record] = {}
    for kind in (2, 1):
        for row in reducer.groups[kind]:
            materialized[row.key] = row
    map430, map458 = [], []
    links_trace = []
    def linked(key: int, table: Mapping[int, int], prefix: str) -> tuple[int | None, bool]:
        pointer = table.get(key)
        if pointer is None:
            pointer = demand.word64(raw.get(prefix + '_fallback_object'), prefix + '_fallback_object')
            magic = demand.integer(raw.get(prefix + '_fallback_magic_u32'), prefix + '_fallback_magic_u32')
        else:
            magic = demand.integer(objects[pointer].get('magic_u32'), prefix + '.selected_object.magic_u32')
        return pointer, magic == 0x4744624F if magic is not None else False
    for row in materialized.values():
        index = len(map430)
        value = native_wrap64_12003(-row.value) if row.kind == 2 else row.value
        map430.append({'bucket_index': index, 'key_object': row.key,
                       'trait_id_u32': row.key_id & 0xFFFFFFFF, 'value_q64': value})
        pp, pv = linked(row.key, positive, 'positive')
        np, nv = linked(row.key, negative, 'negative') if pv else (negative.get(row.key), False)
        if pv and nv:
            current = next((r for r in reducer.groups[row.kind] if r.key == row.key), None)
            if current is not None and current.priority == 2:
                pp = demand.word64(raw.get('positive_fallback_object'), 'positive_fallback_object')
                pm = demand.integer(raw.get('positive_fallback_magic_u32'), 'positive_fallback_magic_u32')
                pv = pm == 0x4744624F if pm is not None else False
            else:
                np = raw.get('negative_fallback_object')
                nv = False
        if pv and pp is not None:
            map458.append({'bucket_index': len(map458), 'key_object': row.key, 'value_u64': pp})
        links_trace.append({'key_object': row.key, 'kind': row.kind,
                            'positive_object': pp, 'positive_valid': pv,
                            'negative_object': np, 'negative_valid': nv})
    derived = deepcopy(raw.get('downstream_inputs'))
    if not isinstance(derived, dict):
        demand.gap('downstream_inputs')
        derived = {}
    derived.update(carrier_present=False, associated_cache_440=1,
                   cached_map_430={'count': len(map430), 'entries': map430},
                   cached_map_458={'count': len(map458), 'entries': map458})
    downstream = compute_absent_recipient_from_native_inputs_12003(derived)
    # cache440=1 above selects shared pure arithmetic over our temporary maps;
    # it is local adapter state, never wire data or a native cache observation.
    for missing in downstream.missing_inputs:
        demand.gap('downstream_inputs.' + missing)
    ready = not demand.missing and downstream.calculation_ready
    ledger.update(reducer_trace=tuple(reducer.trace),
                  kind2_records=tuple(vars_record(r) for r in reducer.groups[2]),
                  kind1_records=tuple(vars_record(r) for r in reducer.groups[1]),
                  seed_records=tuple(vars_record(r) for r in reducer.seeds),
                  cached_thresholds=deepcopy(reducer.thresholds),
                  derived_temporary_map430=tuple(map430), derived_temporary_map458=tuple(map458),
                  link_selection=tuple(links_trace), downstream=downstream.ledger)
    return NativeAbsentRecipientResult12003(
        downstream.value_q64 if ready else None,
        downstream.summed_q64 if ready else None, True, ready,
        'computed' if ready else 'partial', tuple(demand.missing), ledger)


def vars_record(row: _Record) -> Mapping[str, int]:
    return {'key_object': row.key, 'key_id_i32': row.key_id,
            'value_q64': row.value, 'priority_u8': row.priority, 'kind': row.kind}
