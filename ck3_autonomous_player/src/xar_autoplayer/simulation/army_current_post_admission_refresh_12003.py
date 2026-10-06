"""Conditional raw arithmetic through 24DF4C3, with no callback invocation.

Every admitted original occurrence contributes independently to both sums.
Observed Army caches remain observations, never substitutes for raw ArRg40.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


NUMERIC_FRONTIER_STAGE_12003 = 'post24df4c3_pre24df4c7'
NUMERIC_24_STAGE_12003 = 'post24df452_pre24df455'
_LIMIT_FLAGS = (
    'actual_refresh_execution_ready', 'actual_next_occurrence_ready',
    'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready',
)
_CACHE_FIELDS = (
    'actual_army_24_raw_i32', 'actual_army_28_raw_i64',
    'actual_army_20_raw_u8', 'actual_army_21_raw_u8',
    'actual_army_30_raw_u8', 'actual_army_31_raw_u8',
)


def _wrap(value: int, bits: int) -> int:
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def _references_ready(references: Mapping) -> bool:
    count = references['count_raw_i32']
    rows = references['occurrences']
    return (count is not None and count >= 0 and len(rows) == count
            and [row['native_index'] for row in rows] == list(range(count))
            and all(row['raw_full_id_u32'] is not None for row in rows))


def _selected(resolution: Mapping) -> bool:
    return resolution['selected_object_ready'] is True and resolution['object_identity'] is not None


def _derive_arrg(row: Mapping) -> dict:
    resolution = row['arrg_resolution']
    result = {
        'native_index': row['native_index'], 'raw_full_id_u32': row['raw_full_id_u32'],
        'arrg_resolution': deepcopy(resolution), 'magic_14_raw_u32': row['magic_14_raw_u32'],
        'identity_valid': None, 'numeric_24_inputs_ready': False,
        'numeric_28_inputs_ready': False, 'ready': False,
        'numeric_24_contribution_i32': None, 'numeric_28_contribution_i64': None,
        'current_38_raw_i32': row['current_38_raw_i32'], 'value_40_raw_i64': row['value_40_raw_i64'],
        'missing_inputs': [],
    }
    if row['raw_full_id_u32'] is None:
        result['missing_inputs'].append('original_arrg_reference_unavailable')
    elif not _selected(resolution):
        result['missing_inputs'].append('arrg_selected_operand_unavailable')
    elif row['magic_14_raw_u32'] is None:
        result['missing_inputs'].append('arrg_magic14_unavailable')
    elif row['magic_14_raw_u32'] != 0x41725267:
        result['identity_valid'] = False
    elif resolution['selected_full_id_u32'] is None:
        result['missing_inputs'].append('arrg_selected_full_id10_unavailable')
    else:
        result['identity_valid'] = resolution['selected_full_id_u32'] != 0xFFFFFFFF
    if result['identity_valid'] is False:
        result.update(numeric_24_inputs_ready=True, numeric_28_inputs_ready=True,
                      numeric_24_contribution_i32=0, numeric_28_contribution_i64=0)
    elif result['identity_valid'] is True:
        for raw, ready, contribution, reason in (
                ('current_38_raw_i32', 'numeric_24_inputs_ready', 'numeric_24_contribution_i32',
                 'arrg_current38_unavailable'),
                ('value_40_raw_i64', 'numeric_28_inputs_ready', 'numeric_28_contribution_i64',
                 'arrg_value40_unavailable')):
            if row[raw] is not None:
                result[ready] = True
                result[contribution] = row[raw]
            else:
                result['missing_inputs'].append(reason)
    result['ready'] = result['numeric_24_inputs_ready'] and result['numeric_28_inputs_ready']
    return result


def _sum_occurrences(rows: list, *, bits: int, count: int | None,
                     prerequisite: bool) -> tuple[int | None, int | None, int]:
    field = 'numeric_24_contribution_i32' if bits == 32 else 'numeric_28_contribution_i64'
    suffix = 'i32' if bits == 32 else 'i64'
    running = 0
    prefix = 0 if prerequisite and count is not None and count >= 0 else None
    prefix_count = 0
    prefix_open = prefix is not None
    complete = prerequisite and count is not None and count >= 0 and len(rows) == count
    for row in rows:
        before = running if complete else None
        value = row[field]
        if row['native_index'] != prefix_count:
            prefix_open = False
            complete = False
        if value is None:
            complete = False
            prefix_open = False
        elif complete:
            running = _wrap(running + value, bits)
        if prefix_open:
            prefix = _wrap(prefix + value, bits)
            prefix_count += 1
        row['numeric_' + ('24' if bits == 32 else '28') + '_running_before_' + suffix] = before
        row['numeric_' + ('24' if bits == 32 else '28') + '_running_after_' + suffix] = running if complete else None
    return running if complete else None, prefix, prefix_count


def _derive_army(row: Mapping) -> dict:
    references = row['original_arrg_references']
    rows = [_derive_arrg(arrg) for arrg in row['arrg_occurrences']]
    count = references['count_raw_i32']
    selected = _selected(row['original_army_resolution'])
    raw_ready = _references_ready(references)
    coverage = (count is not None and count >= 0 and len(rows) == count
                and [arrg['native_index'] for arrg in rows] == list(range(count)))
    prerequisite = selected and raw_ready and coverage
    ready24 = prerequisite and all(arrg['numeric_24_inputs_ready'] for arrg in rows)
    ready28 = prerequisite and all(arrg['numeric_28_inputs_ready'] for arrg in rows)
    value24, prefix24, prefix24_count = _sum_occurrences(
        rows, bits=32, count=count, prerequisite=selected and count is not None and count >= 0)
    value28, prefix28, prefix28_count = _sum_occurrences(
        rows, bits=64, count=count, prerequisite=selected and count is not None and count >= 0)
    missing = []
    if not selected:
        missing.append('original_army_selected_operand_unavailable')
    if count is not None and count < 0:
        missing.append('negative_original_arrg_count_not_modeled_as_empty')
    elif not raw_ready or not coverage:
        missing.append('complete_original_arrg_references_and_occurrences')
    missing.extend({'arrg_native_index': arrg['native_index'], 'reason': reason}
                   for arrg in rows for reason in arrg['missing_inputs'])
    result = {
        'native_index': row['native_index'], 'raw_full_id_u32': row['raw_full_id_u32'],
        'original_army_resolution': deepcopy(row['original_army_resolution']),
        'original_army_selection_ready': selected,
        'original_arrg_references': deepcopy(references), 'arrg_occurrences': rows,
        'arrg_rows_ready': raw_ready and coverage and all(arrg['identity_valid'] is not None for arrg in rows),
        'numeric_24_inputs_ready': ready24, 'numeric_28_inputs_ready': ready28,
        'ready': ready24 and ready28,
        'prospective_army_24_i32': value24 if ready24 else None,
        'prospective_army_28_i64': value28 if ready28 else None,
        'numeric_24_known_prefix_i32': prefix24,
        'numeric_28_known_prefix_i64': prefix28,
        'numeric_24_known_prefix_occurrence_count': prefix24_count,
        'numeric_28_known_prefix_occurrence_count': prefix28_count,
        'last_verified_stage': NUMERIC_FRONTIER_STAGE_12003 if ready24 and ready28
                               else NUMERIC_24_STAGE_12003 if ready24 else None,
        'independently_verified_numeric_writes': (
            ([{'destination': 'army24', 'write_rva': '0x24df452'}] if ready24 else [])
            + ([{'destination': 'army28', 'write_rva': '0x24df4c3'}] if ready28 else [])),
        'unavailable_reason': None if ready24 and ready28 else 'post_admission_numeric_inputs_incomplete',
        'missing_inputs': missing,
    }
    result.update({field: row[field] for field in _CACHE_FIELDS})
    result.update({flag: False for flag in _LIMIT_FLAGS})
    return result


def project_current_post_admission_refresh_12003(
        raw_normalized: Mapping | None, source_provenance: object = None) -> dict:
    """Compute each numeric destination independently from the exact raw list."""
    result = {
        'schema_version': 1, 'source': 'source_bound_current_post_admission_refresh_inputs',
        'stage': 'observed_current_post_admission_refresh_inputs',
        'projection_stage': NUMERIC_FRONTIER_STAGE_12003,
        'source_contract_game_version': '1.20.0.3',
        'status': 'unavailable', 'ready': False, 'unavailable_reason': None,
        'raw_roster_references_ready': False, 'original_army_selections_ready': False,
        'numeric_24_inputs_ready': False, 'numeric_28_inputs_ready': False,
        'source_operands_ready': False, 'conditional_numeric_frontier_ready': False,
        'last_verified_stage': None, 'occurrences': [], 'original_roster': None,
        'source_provenance': deepcopy(source_provenance),
        'observed_current_post_admission_refresh_inputs': deepcopy(dict(raw_normalized))
            if raw_normalized is not None else None,
        'native_calls_executed': 0, 'native_writes_executed': 0,
        'actual_post_stage_observed': False, 'future_tick_ready': False,
        'missing_inputs': [],
    }
    result.update({flag: False for flag in _LIMIT_FLAGS})
    if raw_normalized is None:
        result.update(unavailable_reason='current_post_admission_refresh_inputs_unavailable',
                      missing_inputs=['current_post_admission_refresh_inputs_v1'])
        return result
    if (raw_normalized['source'] != 'native_current_post_admission_refresh_inputs'
            or raw_normalized['stage'] != 'observed_current_post_admission_refresh_inputs'
            or raw_normalized['projection_stage'] != NUMERIC_FRONTIER_STAGE_12003):
        raise ValueError('Refresh input must retain its genuine current native source and bounded stage')
    original = raw_normalized['original_roster']
    raw_ready = _references_ready(original)
    count = original['count_raw_i32']
    rows = [_derive_army(row) for row in raw_normalized['occurrences']]
    coverage = (count is not None and count >= 0 and len(rows) == count
                and [row['native_index'] for row in rows] == list(range(count)))
    selected = raw_ready and coverage and all(row['original_army_selection_ready'] for row in rows)
    ready24 = raw_ready and coverage and all(row['numeric_24_inputs_ready'] for row in rows)
    ready28 = raw_ready and coverage and all(row['numeric_28_inputs_ready'] for row in rows)
    ready = selected and ready24 and ready28
    missing = [{'army_native_index': row['native_index'], 'input': item}
               for row in rows for item in row['missing_inputs']]
    if not raw_ready or not coverage:
        missing.append('complete_original_roster_references_and_occurrences')
    result.update(
        status='available' if ready else 'partial' if raw_normalized['manager_loaded'] else 'unavailable',
        ready=ready, unavailable_reason=None if ready else 'post_admission_numeric_inputs_incomplete',
        raw_roster_references_ready=raw_ready, original_army_selections_ready=selected,
        numeric_24_inputs_ready=ready24, numeric_28_inputs_ready=ready28,
        source_operands_ready=ready, conditional_numeric_frontier_ready=ready,
        original_roster=deepcopy(original), occurrences=rows, missing_inputs=missing,
        last_verified_stage=NUMERIC_FRONTIER_STAGE_12003 if ready
                            else NUMERIC_24_STAGE_12003 if ready24 else None,
    )
    return result


def validate_current_post_admission_refresh_declared_12003(raw: Mapping) -> dict:
    """Compare producer readiness with branch-demand derivation, never its cache."""
    projected = project_current_post_admission_refresh_12003(raw)

    def same(declared, derived, fields, name):
        for field in fields:
            if declared[field] != derived[field]:
                raise ValueError(f'{name}.{field} disagrees with actual raw source inputs')

    same(raw, projected, ('ready', 'raw_roster_references_ready', 'original_army_selections_ready',
                         'numeric_24_inputs_ready', 'numeric_28_inputs_ready', 'source_operands_ready'),
         'post_admission_refresh')
    for observed, derived in zip(raw['occurrences'], projected['occurrences']):
        same(observed, derived, ('ready', 'arrg_rows_ready', 'numeric_24_inputs_ready',
                                'numeric_28_inputs_ready'), 'army_occurrence')
        for observed_arrg, derived_arrg in zip(observed['arrg_occurrences'], derived['arrg_occurrences']):
            same(observed_arrg, derived_arrg, ('ready', 'identity_valid', 'numeric_24_inputs_ready',
                                             'numeric_28_inputs_ready'), 'arrg_occurrence')
    return projected
