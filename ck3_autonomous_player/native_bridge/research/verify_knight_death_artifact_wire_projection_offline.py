"""Regress pure artifact admission against actual compiled publisher fixtures.

No CK3, desktop, provider, or native function executes. A null full-path mutant
inherits its three artifact words from an actual null publisher row, but remains
synthetic test data. The original fixture bytes and every result are preserved.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
SOURCE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE_ROOT / 'src'))
from xar_autoplayer.simulation.knight_causal_save_projection import validate_scoped_journal

FIELDS = ('requested_death_artifact_token', 'requested_death_artifact_id', 'requested_artifact_id_read')


def metadata(path: Path) -> dict:
    data = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest().upper()}


def load_fixture(path: Path, kind: str) -> dict:
    matches = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('{'):
            value = json.loads(line)
            if value.get('kind') == kind:
                matches.append(value)
    if len(matches) != 1:
        raise ValueError(f'expected exactly one compiled offline fixture {kind}')
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publisher-fixture', type=Path, required=True,
                        help='Actual compiled OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH stdout')
    parser.add_argument('--null-publisher-fixture', type=Path, required=True,
                        help='Actual compiled OFFLINE_COMMIT_PRODUCER_FIXTURE_NOT_GAME_TRUTH stdout')
    parser.add_argument('--baseline-pure', type=Path, required=True,
                        help='Exact unmodified pre-fix pure module, used to demonstrate regression')
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='New create-only external test output directory')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    source = SOURCE_ROOT / 'src/xar_autoplayer/simulation/knight_causal_save_projection.py'
    pins = {}
    for label, path in (('publisher', args.publisher_fixture), ('null_publisher', args.null_publisher_fixture),
                        ('baseline', args.baseline_pure), ('pure', source), ('test', Path(__file__))):
        target = args.output_dir / (label + '-exact' + path.suffix)
        with target.open('xb') as f:
            f.write(path.read_bytes())
        pins[label] = {'original': metadata(path), 'exact_copy': metadata(target)}
    fixture = load_fixture(args.publisher_fixture, 'OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH')
    null_fixture = load_fixture(args.null_publisher_fixture, 'OFFLINE_COMMIT_PRODUCER_FIXTURE_NOT_GAME_TRUTH')
    journal = fixture['scoped_transition_chain']
    victim, related = journal['character_ids']
    checkpoint = {'before': {'combat_id': journal['combat_id'],
                            'managed_daily_sequence_token': journal['managed_daily_sequence_token'],
                            'date_raw': journal['records'][0]['native_date_raw'],
                            'thread_id': journal['records'][0]['thread_id']},
                  'after': {'date_raw': journal['records'][-1]['native_date_raw']}}
    spec = importlib.util.spec_from_file_location('xar_autoplayer.simulation.artifact_before_fixture', args.baseline_pure)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    original = baseline.validate_scoped_journal(journal, checkpoint, victim, related)
    assert original['death_commit_tuple_closed'] is True
    assert original['death_artifact_tuple_closed'] is False
    cases = []

    def run(name: str, candidate: dict, closed: bool, kind: str = 'pending', synthetic: bool = True) -> dict:
        actual = validate_scoped_journal(candidate, checkpoint, victim, related)
        assert actual['death_commit_tuple_closed'] is True
        assert actual['death_artifact_tuple_closed'] is closed, name
        assert actual['death_artifact_tuple_kind'] == kind, name
        assert actual['global_bundle_complete'] is False
        assert actual['full_mutable_transition_bundle_complete'] is False
        assert actual['sole_cause_proven'] is False
        cases.append({'name': name, 'pass': True,
                      'kind': 'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH' if synthetic else fixture['kind'],
                      'actual_projection': actual})
        return actual

    run('original compiled publisher nonnull full ID51: old false, repaired closed', journal, True, 'verified-full-id', False)
    null_rows = [r for r in null_fixture['scoped_transition_chain']['records']
                 if r['boundary'].startswith('death_commit') and r.get(FIELDS[0]) == 'process-local-0x0']
    assert len(null_rows) == 2 and all(tuple(r[k] for k in FIELDS) == ('process-local-0x0', -1, False) for r in null_rows)
    null_journal = copy.deepcopy(journal)
    for row in null_journal['records']:
        if row['boundary'].startswith('death_'):
            for key in FIELDS:
                row[key] = null_rows[0][key]
    run('synthetic full path with independently published exact null tuple', null_journal, True, 'verified-null')

    def mutant(name: str, fields: dict | None = None, *, null: bool = False,
               remove: str | None = None, boundary: str | None = None) -> None:
        trial = copy.deepcopy(null_journal if null else journal)
        for row in trial['records']:
            if row['boundary'].startswith('death_') and (boundary is None or row['boundary'] == boundary):
                if remove:
                    row.pop(remove, None)
                if fields:
                    row.update(fields)
        run(name, trial, False)

    mutant('nonnull original pointer without actual ID read stays pending', {FIELDS[2]: False})
    mutant('missing real publisher field stays pending', remove=FIELDS[2])
    mutant('old nonexistent alias cannot replace real publisher field',
           {'requested_death_artifact_read': True}, remove=FIELDS[2])
    mutant('commit return artifact token mismatch stays pending', {FIELDS[0]: 'process-local-0x1234'}, boundary='death_commit_return')
    mutant('enqueue return full-ID mismatch stays pending', {FIELDS[1]: 52}, boundary='death_enqueue_return')
    mutant('read marker integer1 is not boolean true', {FIELDS[2]: 1}, boundary='death_commit_return')
    mutant('null tuple with nonnull full-ID stays pending', {FIELDS[1]: 51}, null=True)
    mutant('null tuple with ID-read true stays pending', {FIELDS[2]: True}, null=True)
    mutant('noncanonical pointer string stays pending', {FIELDS[0]: 'UNKNOWN'})
    mutant('nonnull invalid full-ID sentinel stays pending', {FIELDS[1]: 0xFFFFFFFF})
    mutant('artifact ID boolean is not an integer full-ID', {FIELDS[1]: True})
    wrong = copy.deepcopy(journal)
    wrong['managed_daily_sequence_token'] += 1
    try:
        validate_scoped_journal(wrong, checkpoint, victim, related)
    except ValueError as error:
        assert 'same managed daily token' in str(error)
        cases.append({'name': 'original daily-token guard still rejects', 'pass': True,
                      'kind': 'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH', 'error': str(error)})
    else:
        raise AssertionError('daily token guard was weakened')

    result = {'schema_version': 1, 'kind': 'OFFLINE_ARTIFACT_WIRE_REGRESSION_NOT_GAME_TRUTH',
              'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'PASS',
              'source_pins': pins, 'baseline_projection': original, 'cases': cases,
              'pass_count': len(cases), 'null_word_source_rows': null_rows,
              'limits': ['The null full request/queue/commit path is an explicitly synthetic mutant, not a live run.',
                         'Tuple admission does not independently compare a saved artifact object; same-run saved consistency is a separate semantic check.',
                         'No R0142 current-after verifier was run. Runtime source and DLL remain separately frozen.'],
              'interpreter': sys.executable, 'argv': sys.argv}
    target = args.output_dir / 'artifact-wire-projection-offline-verification-a01.json'
    with target.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': 'PASS', 'cases': len(cases), 'receipt': metadata(target)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
