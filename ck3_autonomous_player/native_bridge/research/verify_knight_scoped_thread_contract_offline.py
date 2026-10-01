"""Pure thread-role regressions from an existing immutable native trace.

The unmodified original is run through the pure validator only. All mutants
are explicitly offline fixtures, not new native/game evidence. No game, screen,
provider, Rakaly, compiler or native DLL executes.
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


def require(passed: bool, why: str) -> None:
    if not passed:
        raise ValueError(why)


def identity(path: Path) -> dict:
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest().upper()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--baseline-pure', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    source = SOURCE_ROOT / 'src/xar_autoplayer/simulation/knight_causal_save_projection.py'
    pins = {}
    for label, path in [('trace', args.trace), ('baseline', args.baseline_pure),
                        ('pure', source), ('test', Path(__file__))]:
        target = args.output_dir / (label + '-exact' + path.suffix)
        with target.open('xb') as f:
            f.write(path.read_bytes())
        pins[label] = {'original': identity(path), 'exact_copy': identity(target)}
    wrapper = json.loads(args.trace.read_text(encoding='utf-8-sig'))
    require(wrapper['result'] == 'CALL_COMPLETED' and wrapper['body']['accepted'] is True,
            'input must be an original accepted native trace')
    managed = wrapper['body']['managed_trace']
    journal, checkpoint, trace = (managed[k] for k in ('scoped_transition_chain', 'managed_checkpoint', 'trace'))
    victim, related = journal['character_ids']
    spec = importlib.util.spec_from_file_location('xar_autoplayer.simulation.frozen_before_thread_repair', args.baseline_pure)
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    try:
        baseline.validate_scoped_journal(journal, checkpoint, victim, related)
    except ValueError as error:
        require('every record same identity/date/thread' in str(error), 'baseline failure must reproduce original thread predicate')
        baseline_error = str(error)
    else:
        raise ValueError('original baseline did not reproduce the observed thread rejection')
    cases = []

    def positive(name, j, c, t, synthetic=True):
        result = validate_scoped_journal(j, c, victim, related, t)
        require(result['thread_contract']['status'] == 'ORIGINAL_THREAD_ROLES_CHECKED', name)
        require(result['global_bundle_complete'] is False and
                result['full_mutable_transition_bundle_complete'] is False and
                result['sole_cause_proven'] is False, 'global/sole cause limits must stay false')
        cases.append({'name': name, 'pass': True,
                      'kind': 'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH' if synthetic else 'ORIGINAL_R0144_PURE_REPLAY_ONLY',
                      'thread_contract': result['thread_contract'],
                      'death_commit_tuple_closed': result['death_commit_tuple_closed'],
                      'death_artifact_tuple_closed': result['death_artifact_tuple_closed'],
                      'case_native_death_execution_path_closed': result['case_native_death_execution_path_closed'],
                      'gaps': result['gaps']})
        return result

    original = positive('real R0144 original two-thread tuple', journal, checkpoint, trace, False)
    require(original['death_commit_tuple_closed'] is False and original['death_artifact_tuple_closed'] is False and
            original['case_native_death_execution_path_closed'] is False,
            'thread repair must not close the outstanding death date/artifact/path gates')
    same = copy.deepcopy(journal)
    same_trace = copy.deepcopy(trace)
    for row in same['records'][1:-1]:
        row['thread_id'] = checkpoint['before']['thread_id']
    for row in same_trace['records'][2:6]:
        row['global_rng']['owner_thread_token'] = checkpoint['before']['thread_id']
    positive('synthetic coherent single executor remains valid', same, checkpoint, same_trace)
    worker = original['thread_contract']['phase_executor_thread_id']
    owner = checkpoint['before']['thread_id']

    def negative(name, mutate, expected=None):
        j, c, t = copy.deepcopy((journal, checkpoint, trace))
        mutate(j, c, t)
        try:
            validate_scoped_journal(j, c, victim, related, t)
        except (ValueError, KeyError, TypeError) as error:
            if expected:
                require(expected in str(error), name + ': wrong failure ' + str(error))
            cases.append({'name': name, 'pass': True, 'kind': 'OFFLINE_SYNTHETIC_MUTANT_NOT_GAME_TRUTH',
                          'rejection_type': type(error).__name__, 'rejection': str(error)})
        else:
            raise ValueError('negative case was admitted: ' + name)

    for value in (0, True, -1, 0x100000000):
        negative('invalid phase executor ' + repr(value), lambda j,c,t,v=value:
                 [r['global_rng'].update(owner_thread_token=v) for r in t['records'][2:6]], 'original phase executor')
    negative('missing original phase token', lambda j,c,t:t['records'][2]['global_rng'].pop('owner_thread_token'))
    negative('mixed original phase executors', lambda j,c,t:t['records'][5]['global_rng'].update(owner_thread_token=worker+1))
    for index in (4, 129, 164, 165, 177, 181, 182):
        negative('process branch GUI-owner mutant row ' + str(index), lambda j,c,t,i=index:
                 j['records'][i].update(thread_id=owner), 'all actual process branches')
    negative('third engine thread', lambda j,c,t:j['records'][25].update(thread_id=worker+123))
    negative('boolean process thread', lambda j,c,t:j['records'][25].update(thread_id=True))
    for index in (0, len(journal['records'])-1):
        negative('wrong managed endpoint owner row '+str(index), lambda j,c,t,i=index:j['records'][i].update(thread_id=worker))
        negative('wrong managed endpoint date row '+str(index), lambda j,c,t,i=index:j['records'][i].update(native_date_raw=53146860))
    negative('checkpoint owner mismatch', lambda j,c,t:c['after'].update(thread_id=worker))
    negative('nonincreasing pump epoch', lambda j,c,t:c['after'].update(pump_epoch=c['before']['pump_epoch']))
    negative('not +24', lambda j,c,t:c['after'].update(date_raw=c['before']['date_raw']+48))
    negative('unpaused checkpoint', lambda j,c,t:c['before'].update(paused=False))
    for field, value in [('combat_id',16777219),('managed_daily_sequence_token',1),('capture_failure_flags',1),
                         ('native_date_raw',53146848),('phase_day',99),('boundary','UNKNOWN')]:
        negative('ring phase changed '+field, lambda j,c,t,k=field,v=value:t['records'][3].update({k:v}))
    negative('ring phase edge swap', lambda j,c,t:t['records'].__setitem__(slice(2,4),t['records'][2:4][::-1]))
    negative('ring before date changed', lambda j,c,t:t['records'][0].update(native_date_raw=53146872))
    negative('ring global false upgrade', lambda j,c,t:t['readiness'].update(full_mutable_transition_bundle_complete=True))
    for field,value in [('side_index',1),('phase_day',22),('native_date_raw',53146848),('invocation',1)]:
        negative('scoped phase edge changed '+field,lambda j,c,t,k=field,v=value:j['records'][1].update({k:v}))
    for field,value in [('combat_id',16777219),('failure_flags',1),('native_event_load_index',10),
                        ('parent_invocation',999),('side_index',0),('boundary','unknown_enter'),('invocation',True)]:
        negative('typed callback changed '+field,lambda j,c,t,k=field,v=value:j['records'][5].update({k:v}))
    negative('full character identity mismatch',lambda j,c,t:j['records'][4]['characters'][0].update(observed_character_id=33438), 'all typed character identities')
    negative('managed token mismatch',lambda j,c,t:j.update(managed_daily_sequence_token=1),'same managed daily token')
    negative('truncated journal',lambda j,c,t:j.update(truncated=True),'no truncated/failure journal')
    negative('missing invocation return',lambda j,c,t:j['records'][6].update(boundary='phase_after'))
    negative('parent pair escapes ancestor interval',lambda j,c,t:
             [j['records'][i].update(parent_invocation=2) for i in (9,18)],'same-thread actual parent invocation')
    negative('effect depth mismatch',lambda j,c,t:j['records'][5].update(depth=2),'effect depth and side ancestry')
    negative('post-phase branch invented parent',lambda j,c,t:
             [j['records'][i].update(parent_invocation=1) for i in (181,182)],'post-phase standalone branch')
    negative('duplicate paused endpoint',lambda j,c,t:j['records'][177].update(boundary='arm_paused'))
    negative('noncontiguous sequence',lambda j,c,t:j['records'][9].update(sequence=900))
    try:
        validate_scoped_journal(journal, checkpoint, victim, related)
    except ValueError as error:
        require('original phase trace required' in str(error),'missing phase trace must fail explicitly')
        cases.append({'name':'no implicit worker fallback without original phase trace','pass':True,
                      'kind':'OFFLINE_MISSING_EVIDENCE_NEGATIVE','rejection':str(error)})
    else:
        raise ValueError('missing phase trace was admitted')
    result = {'schema_version':1,'kind':'OFFLINE_PURE_THREAD_CONTRACT_NOT_NEW_GAME_TRUTH',
              'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS',
              'interpreter':sys.executable,'argv':sys.argv,'source_pins':pins,'baseline_rejection':baseline_error,
              'original_projection':original,'cases':cases,'pass_count':len(cases),
              'limits':['Original R0144 strict RED is immutable and not rewritten.',
                        'Only paused/phase/process thread roles are repaired; death date/artifact/expiry/trait gates unchanged.',
                        'No full causal, 13-domain, sole cause, global mutable bundle or video approval is claimed.']}
    target=args.output_dir/'scoped-thread-contract-offline-verification-a01.json'
    with target.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({'status':'PASS','cases':len(cases),'receipt':identity(target)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
