"""Check actual compiled offline publisher JSON and meaningful integrity mutants."""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.simulation.knight_variable_monitor_projection import validate_owner_return_compression, validate_variable_monitor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture-stdout', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    objects = []
    for line in args.fixture_stdout.read_text(encoding='utf-8').splitlines():
        if line.startswith('{'):
            objects.append(json.loads(line))
    ordinary = next(row['scoped_variable_monitor'] for row in objects if row.get('kind') == 'OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH')
    nulls = next(row['scoped_variable_monitor'] for row in objects if row.get('kind') == 'OFFLINE_DEAD_NULL_COMPRESSION_FIXTURE_NOT_GAME_TRUTH')
    cases = []

    def case(name, monitor, should_pass, *, full=False):
        error = None
        try:
            if full:
                result = validate_variable_monitor(monitor, character_ids=[101, 201], expected_monitor_token=17,
                                                   before_date_raw=53146848, after_date_raw=53146872)
                assert result['whole_game_mutable_bundle_complete'] is False
            else:
                result = validate_owner_return_compression(monitor)
            if result is not None and not full:
                assert result['writer_calls_coalesced'] == 0
        except (ValueError, KeyError, AssertionError) as exc:
            error = str(exc)
        assert (error is None) is should_pass, (name, error)
        cases.append({'case': name, 'expected_pass': should_pass, 'actual_pass': error is None, 'error': error,
                      'kind': 'COMPILED_OFFLINE_FIXTURE_OR_SYNTHETIC_MUTANT_NOT_GAME_TRUTH'})

    case('actual compiled dead-null publisher shape', copy.deepcopy(nulls), True)
    case('actual normal fixture full projection remains valid', copy.deepcopy(ordinary), True, full=True)
    compressed = next(index for index, row in enumerate(nulls['records']) if row['owner_observation_count'] > 1)
    for field, value in [('observed', True), ('observed', nulls['owner_return_compression']['observed'] + 1),
                         ('retained', 0), ('coalesced', 0), ('capacity', 256), ('writer_calls_coalesced', 1),
                         ('aggregate_bounds_are_not_per_call_chronology', False)]:
        mutant = copy.deepcopy(nulls)
        mutant['owner_return_compression'][field] = value
        case('bad compression top ' + field + '=' + repr(value), mutant, False)
    for field, value in [('dead', False), ('full_identity_matches', False), ('owner_token', 8),
                         ('container_token', 8), ('owner_observation_count', True), ('owner_state_epoch', 0),
                         ('owner_observation_first_call_index', -1), ('owner_observation_last_call_index', 2**64),
                         ('thread_id', 0), ('native_scope_words', [4, 999]), ('native_root_scope_token', 0), ('caller_token', 0)]:
        mutant = copy.deepcopy(nulls)
        mutant['records'][compressed][field] = value
        case('bad compressed row ' + field, mutant, False)
    mutant = copy.deepcopy(nulls)
    mutant['records'][compressed]['value']['read'] = True
    case('null does not become known absent', mutant, False)
    mutant = copy.deepcopy(ordinary)
    writer = next(row for row in mutant['records'] if row['boundary'] == 'variable_write_enter')
    writer['owner_observation_count'] = 1
    case('setter edge cannot aggregate', mutant, False)
    legacy = copy.deepcopy(ordinary)
    legacy.pop('owner_return_compression')
    assert validate_owner_return_compression(legacy) is None
    cases.append({'case': 'legacy raw missing additive metadata stays unpublished', 'expected_pass': True, 'actual_pass': True,
                  'kind': 'OFFLINE_SYNTHETIC_LEGACY_SHAPE_NOT_GAME_TRUTH'})
    data = args.fixture_stdout.read_bytes()
    out = {'schema': 'ck3.scoped-monitor.compression-offline-integrity/v1', 'status': 'PASS',
           'fixture': {'path': str(args.fixture_stdout.resolve()), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest().upper()},
           'argv': sys.argv, 'python': sys.executable, 'cases': cases, 'case_count': len(cases),
           'boundary': 'Compiled offline fixture and synthetic integrity mutants only; no historical/live run closed.'}
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(out, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': 'PASS', 'cases': len(cases), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
