"""Portable B intermediate values; completed relative JSON only, no raw/game/SDK."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def need(value, reason):
    if not value:
        raise ValueError(reason)


def read(relative, expected=None):
    path = (HERE / relative).resolve(strict=True)
    need(path.is_relative_to(HERE.resolve()) and path.suffix in {'.json', '.py'}, 'relative bounded JSON/code leaf')
    raw = path.read_bytes()
    need(len(raw) < 2097152, 'small input leaf only')
    if expected:
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'input exact bytes/SHA mismatch')
    return json.loads(raw) if path.suffix == '.json' else raw


def module(relative, name):
    path = HERE / relative
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def field_changes(left, right, fields):
    return {key: {'before': left.get(key), 'after': right.get(key)} for key in fields if left.get(key) != right.get(key)}


def verify():
    manifest = read('manifest.json')
    for pin in manifest['files']:
        read(pin['path'], pin)
    child = read('child-cap/B-child-partial-result.json')
    need(child['status'] == 'PASS_B_CHILD_FULL_BRANCH_PARTIAL_ONLY', 'preserved child evidence projection status')
    legacy = module('child-cap/code/verify_child_partial.py', 'B_intermediate_source_projection')
    # Reuse the already frozen complete-source projection in this package root.
    # This expands only relative JSON leaves; the previous child pair is not rerun.
    legacy.HERE = HERE
    reader = module('child-cap/code/paired_snapshot_reader.py', 'B_intermediate_reader')
    pure = module('child-cap/code/paired_window_pure.py', 'B_intermediate_pure_window')
    frozen = read('child-cap/code/frozen-cohort.json')
    window = read('inputs/growth-window.json')
    read('inputs/growth-before/observation.json', window['before_observation'])
    read('inputs/growth-after/observation.json', window['after_observation'])
    left, left_view = legacy.observed('inputs/growth-before', reader, frozen)
    right, right_view = legacy.observed('inputs/growth-after', reader, frozen)
    computed = pure.window(left, right)
    need(computed == window['actual_window'], 'growth entire actual_window must recompute equal original')
    need(computed['pair_dates_raw'] == [53149056, 53149080], 'actual +26/+27 dates')
    need(left_view['regiment_arm'] == right_view['regiment_arm'] and left_view['record_arm'] == right_view['record_arm'], 'split cohort membership stable')
    need(set(left_view['regiments']) == set(right_view['regiments']) and set(left_view['records']) == set(right_view['records']), 'entire27/37 identity stable')
    for collection in ('regiments', 'records'):
        need(all(row['maximum_soldiers'] == right_view[collection][key]['maximum_soldiers'] for key, row in left_view[collection].items()), 'all individual maxima preserved')
    need(computed['both_stationary_positive_before_after'] is True, 'both required stationary positive sources')
    need(computed['main_window_success'] is False and computed['child_window_success'] is False, 'this is not a new stock-write qualification')
    deltas, roles = {}, {}
    for public_id in ('0', '204'):
        old, new = left_view['arms'][public_id], right_view['arms'][public_id]
        need(all(old[key] == new[key] for key in ('public_id', 'native_carmy_id', 'owner', 'commander', 'province',
                                                 'stock', 'capacity', 'monthly', 'scales', 'last_supply_update_storage',
                                                 'last_supply_update_raw', 'grace_storage', 'grace_raw')), 'role/source/site/stock/anchors changed in integer window')
        deltas[public_id] = new['current_soldiers'] - old['current_soldiers']
        roles[public_id] = {'before': old, 'after': new, 'integer_current_net': deltas[public_id]}
    need(deltas == {'0': 7, '204': 3}, 'actual Main+7 / child+3 endpoints')
    integer_rows, cache_rows, other_rows = [], [], []
    for key, old in left_view['records'].items():
        new = right_view['records'][key]
        integer = field_changes(old, new, ('current_soldiers', 'effective_current_soldiers'))
        cache_keys = [field for field in set(old) | set(new) if 'prepared' in field or 'can_' in field or 'allowed' in field]
        cache = field_changes(old, new, sorted(cache_keys))
        other_keys = [field for field in set(old) | set(new) if field not in {'current_soldiers', 'effective_current_soldiers'} and field not in cache_keys]
        other = field_changes(old, new, sorted(other_keys))
        identity = json.loads(key)
        if integer:
            integer_rows.append({'identity': identity, 'arm_public': left_view['record_arm'][key], 'integer_fields': integer,
                                 'original_entire_before': old, 'original_entire_after': new})
        if cache:
            cache_rows.append({'identity': identity, 'arm_public': left_view['record_arm'][key], 'cache_or_permission_fields': cache})
        if other:
            other_rows.append({'identity': identity, 'other_fields': other})
    need(len(integer_rows) == 6, 'actual six DATA integer-grow rows')
    net = sum(row['integer_fields'].get('current_soldiers', {'before': 0, 'after': 0})['after']
              - row['integer_fields'].get('current_soldiers', {'before': 0, 'after': 0})['before'] for row in integer_rows)
    need(net == 10, 'six persistent DATA current net+10 independently summed')
    return {'schema': 'ck3.e04.B.intermediate-portable-values.v1', 'status': 'PASS_B_INTERMEDIATE_CHILD_CAP_AND_INTEGER_GROWTH_ONLY',
            'run': 'R0175-a02', 'episode_run_id': reader.EPISODE, 'start_raw': reader.START, 'absolute_end_raw': reader.END,
            'rest_anchor_raw': 53148576, 'local31_absolute_END_raw': 53149320, 'budget_reset': False,
            'preserved_child_cap_case': {'result': 'child-cap/B-child-partial-result.json', 'child_success': True, 'Main_success_in_that_window': False},
            'integer_window': {'actual_pair': computed, 'roles': roles, 'whole_current_before': 6679, 'whole_current_after': 6689,
                               'whole_current_net': 10, 'individual_FullIDs_and_maxima_preserved': True,
                               'DATA_integer_grow_rows': integer_rows, 'DATA_cache_or_permission_changes': cache_rows,
                               'other_DATA_changes': other_rows,
                               'Regiment_entire_row_diffs': computed['Regiment_entire_row_diffs'],
                               'full27_and37_entire_source_arrays_relative': ['inputs/growth-before/observation.json', 'inputs/growth-after/observation.json']},
            'observed_world_changed_paths': reader.changes(left_view['active_wars'], right_view['active_wars'], '/active_wars'),
            'Root_world_review_original': 'inputs/root-review-growth.json',
            'Main_positive_stock_write_full_qualification_return_merge_London_B_terminal_final_raw_result': None,
            'applied_refill_death_payment_ledger_producer_PC_or_B_C_winner': None,
            'integer_growth_not_inferred_from_prepared_or_permission_changes': True,
            'ABC_complete_comparison_or_media_clean_human_credit': 0}


def main():
    try:
        print(json.dumps(verify(), indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({'status': 'STOP_B_INTERMEDIATE_SOURCE_OR_NUMERIC_GATE', 'error': str(exc)}, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
