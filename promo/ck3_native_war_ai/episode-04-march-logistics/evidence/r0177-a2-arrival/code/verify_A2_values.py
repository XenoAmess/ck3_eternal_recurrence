"""Verify this portable A-only JSON package using stdlib, never media/game/SDK."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def need(value, message):
    if not value:
        raise ValueError(message)


def verify(package):
    manifest = json.loads((package / 'manifest.json').read_bytes())
    cache = {}
    for pin in manifest['files']:
        relative = Path(pin['path'])
        need(not relative.is_absolute() and '..' not in relative.parts
             and relative.suffix in ('.json', '.py', '.md'), 'relative bounded text artifact only')
        path = package / relative
        need(type(pin['bytes']) is int and 0 <= pin['bytes'] < 1048576
             and path.stat().st_size == pin['bytes'], 'bounded exact file size before read')
        raw = path.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == pin['sha256'], 'manifest exact bytes/SHA: ' + pin['path'])
        need(pin['path'] not in cache, 'unique manifest path')
        cache[pin['path']] = raw
    report = json.loads(cache['A2-endpoint-values.json'])
    objects = {}
    for pin in report['source_pins']:
        raw = cache[pin['path']]
        need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'original source pin')
        need(pin['artifact_id'] not in objects, 'unique source artifact')
        objects[pin['artifact_id']] = json.loads(raw)
    need(hashlib.sha256(cache['code/historical-validate-results.py']).hexdigest()
         == '144613e1ab9a35820323cfa2ca197e784565f02581c808fa35c6dafc8fe084e2', 'exact existing stdlib observer')
    spec = importlib.util.spec_from_file_location('historic_observer', package / 'code/historical-validate-results.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    common = objects['results_parent_template']['common']
    cold = checker.observation({'source_refs': {'before': 'cold_before', 'health': 'cold_health',
        'after': 'cold_after', 'commander': 'cold_commander'}, 'subject_public_ids': [0]}, objects, common, initial=True)
    observations = {}
    for name in ('last_not_arrived', 'first_arrived', 'independent_arrived'):
        refs = {}
        for component in ('before', 'health', 'after'):
            artifact_id = name + '_' + component
            objects[artifact_id] = objects[name][component]
            refs[component] = artifact_id
        refs['commander'] = name + '_commander'
        observations[name] = checker.observation({'source_refs': refs, 'subject_public_ids': [0]}, objects, common)
    last, first, peer = (observations[name] for name in ('last_not_arrived', 'first_arrived', 'independent_arrived'))
    need(not checker.stationary_london(last) and checker.stationary_london(first)
         and checker.stationary_london(peer), 'actual stationary event predicate')
    need(last['before']['date_raw'] == 53149608 and first['before']['date_raw'] == peer['before']['date_raw'] == 53149656,
         'actual observed interval(+49,+51]')
    for value in (cold, last, first, peer):
        need(value['before']['episode_run_id'] == 'native-33388-dc0d8e1d4891', 'single actual A2 episode')
        need(value['cohort']['mapping'] == {'0': 0} and value['commanders'] == {'0': 27357}, 'actual Main0/commander')
    need(first['cohort'] == peer['cohort'], 'independent complete endpoint cohort/stock/clock equality')
    for collection in ('regiments', 'records'):
        need(set(cold['cohort'][collection]) == set(first['cohort'][collection]), 'whole27/37 original identity')
        need(all(row['maximum_soldiers'] == cold['cohort'][collection][key]['maximum_soldiers']
                 for key, row in first['cohort'][collection].items()), 'each original maximum')
        changes = [{'identity': key, 'changed_fields': checker.diff_paths(cold['cohort'][collection][key], row),
                    'before': cold['cohort'][collection][key], 'after': row}
                   for key, row in first['cohort'][collection].items() if row != cold['cohort'][collection][key]]
        need(changes == report['full_regiment_and_DATA_row_changes'][collection], 'full row change report')
    values = report['endpoint_values']
    need(values['current_soldiers'] == {'initial': cold['cohort']['soldiers'], 'terminal': first['cohort']['soldiers'],
         'net': first['cohort']['soldiers'] - cold['cohort']['soldiers']} == {'initial': 6679, 'terminal': 6689, 'net': 10}, 'actual troop net')
    need(values['gold_raw'] == {'initial': cold['before']['played_character_gold']['raw'],
        'terminal': first['before']['played_character_gold']['raw'],
        'net': first['before']['played_character_gold']['raw'] - cold['before']['played_character_gold']['raw'],
        'scale': 100000} == {'initial': 63754562, 'terminal': 62148329, 'net': -1606233, 'scale': 100000}, 'actual net treasury')
    need(values['supply_raw'] == {'initial': cold['cohort']['stock']['0']['current_supply_raw'],
        'terminal': first['cohort']['stock']['0']['current_supply_raw'],
        'net': first['cohort']['stock']['0']['current_supply_raw'] - cold['cohort']['stock']['0']['current_supply_raw'],
        'scale': 100000} == {'initial': 11037716, 'terminal': 10613988, 'net': -423728, 'scale': 100000}, 'actual net stock')
    need(report['initial_supply_and_clock'] == cold['cohort']['stock']['0']
         and report['terminal_supply_and_clock'] == first['cohort']['stock']['0'], 'supply/clocks source rows')
    need(report['active_war_changed_paths'] == checker.diff_paths(cold['before']['active_wars'], first['before']['active_wars'], '/active_wars'), 'retain world changed paths')
    acceptance, sealed, closure = (objects[name] for name in ('Root_numeric_acceptance', 'second_recording_sealed', 'A2_actual_closure'))
    need(acceptance['endpoint_numeric_accepted'] is True and acceptance['actual_raw'] == 53149656, 'Root numeric acceptance')
    need(sealed['state'] == 'NORMAL_TREE_EMPTY' and sealed['job']['returncode'] == 0
         and sealed['job']['job_active_processes'] == 0 and sealed['same_A2'] is True,
         'sealed recorder small metadata only')
    need(sealed['raw'] == report['recording_closure_append']['raw_metadata'], 'worker raw identity reused, raw never opened')
    for field in ('SDK_thread_exited', 'keeper_thread_exited', 'GameJob0', 'native_CK3_inventory_empty',
                  'watchdog_absent', 'first_recorder_closed', 'continuation_job0', 'actual_London_arrival'):
        need(closure[field] is True, 'actual Root runtime closure ' + field)
    need(closure['primary_numeric_ABC_completed'] == 1 and report['numeric_observed_completion']['completed_count'] == 1,
         'A-only1of3 numeric observed completion')
    need(report['A_experiment_closed'] is True and report['second_recording_closed'] is True, 'closed A-only append')
    need(report['arrival']['exact_arrival_raw'] is None and report['results_rows']['B'] is None
         and report['results_rows']['C'] is None and report['ranking'] is None
         and report['numeric_observed_completion']['overall_winner'] is None, 'exact tick/B/C/winner remainNULL')
    need(report['ABC_complete_comparison_credit'] == 0 and report['troop_application_cause'] is None
         and report['maintenance_cost_attribution'] is None and report['film_clean_span_human_credit'] is None,
         'no cause or complete comparison/media shortcut')
    return {'schema': 'ck3.e04.A2.portable-source-check.v1', 'status': 'PASS_A_ONLY_CLOSED_OBSERVED_VALUES',
            'artifact_count': len(cache), 'arrival_interval_raw': [53149608, 53149656], 'exact_arrival_raw': None,
            'soldier_net': 10, 'stock_net_raw': -423728, 'treasury_net_raw': -1606233, 'numeric_observed_completion': '1/3',
            'B': None, 'C': None, 'overall_winner': None, 'ABC_complete_comparison_or_media_clean_human_credit': 0,
            'raw_or_save_or_game_SDK_UI_bus_Git_actions': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    try:
        report = verify(args.package)
    except (ValueError, OSError, KeyError, TypeError, AssertionError) as exc:
        print(json.dumps({'status': 'FAIL_PORTABLE_SOURCE_PACKAGE', 'error': str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
