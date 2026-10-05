"""Portable B rest qualification increment, completed relative JSON only."""
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
    need(path.is_relative_to(HERE.resolve()) and path.suffix in {'.json', '.py', '.txt'}, 'relative bounded source leaf')
    raw = path.read_bytes()
    need(len(raw) < 2097152, 'small leaf only, no raw/save opens')
    if expected:
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'raw input pin mismatch: ' + relative)
    return json.loads(raw) if path.suffix == '.json' else raw


def module(relative, name):
    spec = importlib.util.spec_from_file_location(name, HERE / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def verify():
    for pin in read('manifest.json')['files']:
        read(pin['path'], pin)
    previous = read('intermediate/B-intermediate-values.json')
    need(previous['status'] == 'PASS_B_INTERMEDIATE_CHILD_CAP_AND_INTEGER_GROWTH_ONLY', 'preserved historical intermediate')
    qualification = read('inputs/Root-qualification.json')
    need(qualification['status'] == 'ROOT_ACTUAL_B_REST_QUALIFIED'
         and qualification['episode_run_id'] == 'native-33388-23726fbd8a80'
         and qualification['start_raw'] == 53148432 and qualification['absolute_end_raw'] == 53150592,
         'Root actual qualification source bindings')
    read('intermediate/child-cap/inputs/protocol.json', qualification['Root_protocol'])
    read('intermediate/child-cap/inputs/phase0/result.json', qualification['phase0_result'])
    read('intermediate/child-cap/inputs/rest-anchor.json', qualification['rest_anchor'])
    read('intermediate/child-cap/inputs/child-window.json', qualification['child_window'])
    read('inputs/Main-window.json', qualification['main_window'])
    anchor = read('intermediate/child-cap/inputs/rest-anchor.json')
    need(anchor['date_raw'] == 53148576 and anchor['local_max_days'] == 31 and anchor['fixed_global_END'] == 53150592,
         'original +6 /31 /global END unchanged')
    reader = module('intermediate/child-cap/code/paired_snapshot_reader.py', 'B_rest_increment_reader')
    pure = module('intermediate/child-cap/code/paired_window_pure.py', 'B_rest_increment_pure')
    legacy = module('intermediate/child-cap/code/verify_child_partial.py', 'B_rest_increment_projection')
    legacy.HERE = HERE
    frozen = read('intermediate/child-cap/code/frozen-cohort.json')
    window = read('inputs/Main-window.json')
    read('inputs/Main-before/observation.json', window['before_observation'])
    read('inputs/Main-after/observation.json', window['after_observation'])
    left, left_view = legacy.observed('inputs/Main-before', reader, frozen)
    right, right_view = legacy.observed('inputs/Main-after', reader, frozen)
    computed = pure.window(left, right)
    need(computed == window['actual_window'], 'Main original entire actual_window must recompute equal')
    need(computed['pair_dates_raw'] == [53149176, 53149200] and computed['main_window_success'] is True,
         'actual Main +31→32 positive write')
    need(computed['child_window_success'] is False, 'this second pair is Main-only new write')
    need(left_view['regiments'] == right_view['regiments'] and left_view['records'] == right_view['records'], 'Main write complete27/37 entire rows unchanged')
    need(left_view['regiment_arm'] == right_view['regiment_arm'] and left_view['record_arm'] == right_view['record_arm'], 'actual split membership stable')
    main_before, main_after = left_view['arms']['0'], right_view['arms']['0']
    need(main_before['stock'] == 10613988 and main_after['stock'] == 12613988
         and main_after['capacity'] == 30000000 and main_after['monthly'] == 2000000,
         'actual observed Main stock/cap/monthly')
    need(main_before['last_supply_update_raw'] == 53148480 and main_after['last_supply_update_raw'] == 53149200,
         'new actual +188 observed stamp')
    for view in (left_view, right_view):
        need(53148576 <= view['date_raw'] <= 53149320 <= 53150592, 'immutable local31/global END')
        need(all(row['stationary_at_required_site'] and row['monthly'] > 0 for row in view['arms'].values()), 'both sites stationary positive')
        need(sum(row['current_soldiers'] for row in view['arms'].values()) == 6689, 'current6689 preserved at endpoints')
    return {'schema': 'ck3.e04.B.qualified-rest-increment.v1', 'status': 'PASS_B_TWO_REST_NUMERIC_BRANCHES_OBSERVED_NO_TERMINAL',
            'run': 'R0175-a02', 'episode_run_id': reader.EPISODE,
            'start_raw': reader.START, 'absolute_end_raw': reader.END,
            'immutable_rest_anchor_raw': 53148576, 'local31_absolute_END_raw': 53149320, 'budget_reset': False,
            'child_earlier_branch': {'source': 'intermediate/child-cap/B-child-partial-result.json', 'actual_pair_dates_raw': [53148912, 53148936],
                                     'stock_before': 11037716, 'stock_after': 10000000, 'cap': 10000000, 'success': True,
                                     'negative_delta_is_cap_convergence': True},
            'Main_later_branch': {'original_paired_window': 'inputs/Main-window.json', 'actual_window': computed,
                                  'before_role': main_before, 'after_role': main_after, 'stock_net_raw': 2000000, 'success': True,
                                  'entire27_Regiment_and37_DATA_rows_unchanged': True},
            'Root_actual_qualification_original': 'inputs/Root-qualification.json',
            'Root_UI_review_original': 'inputs/Main-UI-receipt.json',
            'world_differences_original': 'inputs/Main-source-diff.json', 'Root_note_original': 'inputs/Root-note.txt',
            'integer_growth_earlier_plus27_source': 'intermediate/B-intermediate-values.json',
            'current_raw': 53149200, 'used_global_days': 32, 'remaining_global_days': 58,
            'latest_full_subjects': right_view['arms'], 'actual_treasury': right_view['gold'],
            'return_merge_London_B_terminal_final_raw_result': None,
            'unobserved_continuous_interval_or_refill_death_payment_applied_ledger_or_B_C_winner': None,
            'ABC_complete_comparison_or_media_clean_human_credit': 0}


def main():
    try:
        print(json.dumps(verify(), indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({'status': 'STOP_B_REST_INCREMENT_SOURCE_OR_NUMERIC_GATE', 'error': str(exc)}, indent=2))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
