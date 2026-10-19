"""Create-only classifier leaf for the exact C3 Native campaign deadline proof."""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import io
import tokenize

from prepare_c3_life_opening_classifier_v1 import load_functions, pinned

SOURCE_SHA = '9da4445b22bf49c616ad190023655911a102c76d225c3052c662e58292c23a11'
AUTO_SHA = 'e5cf5bfc60024f0692cf9cecbc49ded543d294fb57d022a8552aa3877457ea75'
LEAF = 'root_campaign_deadline_clock_credit_v2.py'


def transform(raw, leaf_raw):
    tree = ast.parse(raw.decode('utf-8-sig'))
    old = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'classify_clock_advance_v1']
    if len(old) != 1:
        raise ValueError('One exact original clock required')
    lines = raw.decode('utf-8-sig').splitlines(keepends=True)
    i = old[0].lineno - 1
    lines[i] = lines[i].replace('def classify_clock_advance_v1(', 'def classify_before_native_deadline_v1(', 1)
    # Tokenize first: apparent comments inside embedded source strings are data.
    comments = {t.start[0] for t in tokenize.generate_tokens(io.StringIO(''.join(lines)).readline)
                if t.type == tokenize.COMMENT and not lines[t.start[0]-1][:t.start[1]].strip()}
    base = ''.join(line for number, line in enumerate(lines, 1) if number not in comments)
    digest = hashlib.sha256(leaf_raw).hexdigest()
    suffix = f'''
def classify_clock_advance_v1(body, *, initial_frame=None, game_pid=None):
    if not isinstance(body.get("result"), dict) or "campaign_deadline_native_clock_v1" not in body["result"]:
        return classify_before_native_deadline_v1(body, initial_frame=initial_frame, game_pid=game_pid)
    p = Path(classify_clock_advance_v1.__code__.co_filename).with_name({LEAF!r})
    b = p.read_bytes()
    if len(b) > 32768 or hashlib.sha256(b).hexdigest() != {digest!r}:
        raise ValueError("Native deadline classifier leaf differs")
    n = {{}}
    exec(compile(b, str(p), "exec"), n)
    c = n["classify_deadline_clock_v1"](body, initial_frame=initial_frame, game_pid=game_pid,
        bind=classify_gameplay_start_binding_v1)
    return c if c is not None else classify_before_native_deadline_v1(body, initial_frame=initial_frame, game_pid=game_pid)
'''
    result = (base + suffix).encode()
    expected = copy.deepcopy(tree)
    [n for n in expected.body if isinstance(n, ast.FunctionDef) and n.name == 'classify_clock_advance_v1'][0].name = 'classify_before_native_deadline_v1'
    after = ast.parse(result.decode())
    if len(result) > 262144 or [ast.dump(n) for n in expected.body] != [ast.dump(n) for n in after.body[:-1]]:
        raise AssertionError('Original guard AST changed or bound exceeded')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    freeze, freeze_pin = pinned(root / 'ROOT-FINAL-SDK-FREEZE-P37C.json', limit=1024**2)
    frozen = json.loads(freeze)
    sys.path.insert(0, frozen['source_root'])
    driver = Path(frozen['source_root']) / 'xar_autoplayer/bridge/native_driver.py'
    driver_hash = hashlib.sha256(driver.read_bytes()).hexdigest()
    driver_expected = next(x['sha256'] for x in frozen['files'] if x['relative'] == 'xar_autoplayer/bridge/native_driver.py')
    if driver_hash != driver_expected:
        raise ValueError('Frozen Native validators differ')
    raw, pin = pinned(root / 'root_p37c3_crown_priority_classifier.py', expected=SOURCE_SHA)
    leaf, leaf_pin = pinned(Path(__file__).with_name('campaign_deadline_clock_credit_v1.py'), limit=32768)
    auto, auto_pin = pinned(root / 'p37-responses/0147-1-result.json', expected=AUTO_SHA)
    queue, queue_pin = pinned(root / 'root_p37c3_sdk_queue.py', limit=1024**2)
    gov, gov_pin = pinned(root / 'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json')
    mapping, map_pin = pinned(root / 'ROOT-CAMPAIGN-MAP-ADMITTED.json')
    launch, launch_pin = pinned(root / 'ROOT-ACTUAL-GAME-LAUNCH.json')
    launch = json.loads(launch)
    if launch['pid'] != 214568 or launch['creation_filetime'] != 134368503807325674:
        raise ValueError('Retained Game custody differs')
    changed = transform(raw, leaf)
    args.output_root.mkdir(parents=True, exist_ok=False)
    (args.output_root / LEAF).write_bytes(leaf)
    candidate = args.output_root / 'root_c3_native_deadline_classifier.py'
    candidate.write_bytes(changed)
    # All original adjacent pure helpers resolve in TARGET; only the new leaf resolves in the review directory.
    functions = []
    for payload in (raw, changed):
        scope = {'Path': Path, 'json': json, 'hashlib': hashlib, 'ast': ast, 'copy': copy}
        load_functions(queue, scope, str(root / 'root_p37c3_sdk_queue.py'))
        load_functions(payload, scope, str(root / 'root_p37c3_crown_priority_classifier.py'))
        if payload == changed:
            # This code filename belongs only to the appended clock dispatcher.
            scope['classify_clock_advance_v1'].__code__ = scope['classify_clock_advance_v1'].__code__.replace(co_filename=str(candidate))
        functions.append(scope['classify_auto_result_credit_v1'])
    body = json.loads(auto)['result']['structured_content']
    governance = json.loads(gov)
    parameters = {'state': governance['state'], 'pending_focus': governance.get('pending_focus'),
        'initial_frame': json.loads(mapping)['actual_initial_frame'], 'game_pid': launch['pid']}
    old, new = functions
    try:
        old(copy.deepcopy(body), **copy.deepcopy(parameters))
    except ValueError as error:
        refusal = str(error)
        if 'life-advance original composite/date/source postcondition not verified' not in refusal:
            raise
    else:
        raise AssertionError('Original refusal not reproduced')
    original = copy.deepcopy(body)
    actual = new(body, **copy.deepcopy(parameters))
    if body != original or actual[0]['actual_elapsed_days'] != 8 or actual[0]['rejected_pause_command_succeeded'] is not False:
        raise AssertionError('Raw receipt changed or wrong observed credit')
    accepted_fixture = copy.deepcopy(body)
    accepted_fixture['result']['actions'][2]['result'] = {
        'step': 'pause-map', 'accepted': True, 'status': 'submitted', 'backend_id': 'native-headless'}
    if old(copy.deepcopy(accepted_fixture), **copy.deepcopy(parameters)) != new(copy.deepcopy(accepted_fixture), **copy.deepcopy(parameters)):
        raise AssertionError('Original wholly accepted clock behavior changed')
    mutations = {
        'generation': lambda b: b['result']['campaign_deadline_native_clock_v1']['stopped'].__setitem__('generation', 7),
        'target': lambda b: b['result']['campaign_deadline_native_clock_v1'].__setitem__('target_date_raw', 53145264),
        'ticks': lambda b: b['result']['campaign_deadline_native_clock_v1']['stopped'].__setitem__('completed_daily_ticks', 7),
        'overshoot': lambda b: b['result']['campaign_deadline_native_clock_v1']['stopped'].__setitem__('overshoot_days', 1),
        'pause_not_observed': lambda b: b['result']['campaign_deadline_native_clock_v1']['stopped'].__setitem__('pause_observed', False),
        'wrong_episode': lambda b: b['planning_source_frame'].__setitem__('episode_run_id', 'foreign'),
        'wrong_actor': lambda b: b['planning_source_frame'].__setitem__('actor_character_id', 31255),
        'wrong_date': lambda b: b['result'].__setitem__('ending_date_raw', 53145264),
        'resume_unknown': lambda b: b['result']['actions'][1]['result'].__setitem__('accepted', None),
        'pause_other_error': lambda b: b['result']['actions'][2]['result'].__setitem__('error', 'other'),
        'extra_action': lambda b: b['result']['actions'].append(copy.deepcopy(b['result']['actions'][2])),
        'final_not_paused': lambda b: b['result'].__setitem__('paused', False),
    }
    negatives = []
    for name, mutate in mutations.items():
        bad = copy.deepcopy(body); mutate(bad)
        try:
            new(bad, **copy.deepcopy(parameters))
        except ValueError:
            negatives.append(name)
        else:
            raise AssertionError('Negative accepted: ' + name)
    regressions = []
    for seq in (117, 130):
        prior, prior_pin = pinned(root / f'p37-responses/{seq:04}-1-result.json')
        prior = json.loads(prior)['result']['structured_content']
        call = {**copy.deepcopy(parameters), 'state': {'council_pending': None, 'construction_actions': {}}, 'pending_focus': None}
        if seq == 130:
            # Regression fixture from the retained response, not a claim that overwritten old sidecar survives.
            call['state']['crown_pending'] = copy.deepcopy(prior['plan']['crown_pending_action'])
            call['state']['crown_pending']['game_pid'] = launch['pid']
        if old(copy.deepcopy(prior), **copy.deepcopy(call)) != new(copy.deepcopy(prior), **copy.deepcopy(call)):
            raise AssertionError('Prior behavior changed')
        regressions.append(prior_pin)
    with (args.output_root / 'INPUT-governance-original.json').open('xb') as stream:
        stream.write(gov)
    result = {'schema': 'xar.c3-native-deadline-classifier-qualification/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186', 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': [pin, auto_pin, queue_pin, gov_pin, map_pin, launch_pin, freeze_pin, leaf_pin] + regressions,
        'frozen_native_validator': {'path': str(driver), 'sha256': driver_hash},
        'candidate': {'path': str(candidate), 'bytes': len(changed), 'sha256': hashlib.sha256(changed).hexdigest()},
        'leaf': {'path': str(args.output_root / LEAF), 'bytes': len(leaf), 'sha256': hashlib.sha256(leaf).hexdigest()},
        'original_refusal': refusal, 'original_AST_unchanged_except_clock_name': True,
        'raw_AUTO147_unchanged': body == original, 'observation': actual[0],
        'negative_cases_rejected': negatives, 'LIFE117_Crown130_identical': True,
        'original_allaccepted_clock_fixture_identical': True,
        'new_Game_Native_MCP_calls': 0, 'runtime_mutations': 0, 'live_adopted': False}
    (args.output_root / 'QUALIFICATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'candidate': result['candidate'], 'leaf': result['leaf'], 'status': 'PASS'}))


if __name__ == '__main__':
    main()
