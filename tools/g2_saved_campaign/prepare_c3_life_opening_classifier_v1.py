"""Prepare the exact C3 warm LIFE opening view without changing T0 or guards."""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

CANONICAL_SHA = 'f857613afc0872bffeb6d772025afa0feb76e259d8478e14ccf79f8e7732ecbc'
AUTO117_SHA = '5d4b455ef083484755d7910bab7036de972961a321e943ceaaef79e8c2024de3'
SEM111_SHA = '6450bd8ca1b1002a02a9cbb8f5c2c26d34d0d009f27b4bb1c400643b85fa5246'
LIMIT = 262144


def pinned(path, *, expected=None, limit=LIMIT):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) > limit or expected is not None and digest != expected:
        raise ValueError('Exact bounded source differs: ' + str(path))
    return raw, {'path': str(path), 'bytes': len(raw), 'sha256': digest}


def load_functions(raw, namespace, filename):
    selected = []
    for node in ast.parse(raw.decode('utf-8-sig')).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('classify_'):
            selected.append(node)
        elif isinstance(node, ast.Assign) and all(isinstance(target, ast.Name) and target.id.isupper()
                                                 for target in node.targets):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            selected.append(node)
    exec(compile(ast.Module(body=selected, type_ignores=[]), filename, 'exec'), namespace)


def transform(raw, t0, warm, planning):
    tree = ast.parse(raw.decode('utf-8-sig'))
    dispatchers = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == 'classify_auto_result_credit_v1']
    last = dispatchers[-1]
    lines = raw.decode('utf-8-sig').splitlines(keepends=True)
    index = last.lineno - 1
    if 'def classify_auto_result_credit_v1(' not in lines[index]:
        raise ValueError('Exact final dispatcher header required')
    lines[index] = lines[index].replace('def classify_auto_result_credit_v1(',
        'def classify_before_c3_warm_life_opening_v1(', 1)
    suffix = f'''

C3_T0_MAP_FRAME = {t0!r}
C3_WARM_LIFE_FRAME = {warm!r}
C3_WARM_PLANNING_FRAME = {planning!r}

def classify_auto_result_credit_v1(body, *, state=None, pending_focus=None, initial_frame=None, game_pid=None):
    plan = body.get("plan") if isinstance(body, dict) and isinstance(body.get("plan"), dict) else {{}}
    if (initial_frame == C3_T0_MAP_FRAME and isinstance(plan.get("initial_lifestyle_focus_existing"), dict)
            and body.get("selected_step") == "query-campaign-root-context-v1"):
        if game_pid != 214568 or body.get("planning_source_frame") != C3_WARM_PLANNING_FRAME:
            raise ValueError("C3 warm LIFE opening belongs to another actual Game or source frame")
        initial_frame = dict(C3_WARM_LIFE_FRAME)
    return classify_before_c3_warm_life_opening_v1(body, state=state, pending_focus=pending_focus,
        initial_frame=initial_frame, game_pid=game_pid)
'''
    result = (''.join(lines) + suffix).encode()
    if len(result) > LIMIT:
        raise ValueError('Finite existing classifier source limit exceeded')
    after = ast.parse(result.decode('utf-8-sig'))
    original = copy.deepcopy(tree)
    expected_last = [node for node in original.body if isinstance(node, ast.FunctionDef)
                     and node.name == 'classify_auto_result_credit_v1'][-1]
    expected_last.name = 'classify_before_c3_warm_life_opening_v1'
    if [ast.dump(node) for node in after.body[:len(original.body)]] != [ast.dump(node) for node in original.body]:
        raise AssertionError('An original classifier guard or function changed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    freeze_raw, freeze_pin = pinned(root / 'ROOT-FINAL-SDK-FREEZE-P37C.json', limit=1024**2)
    sys.path.insert(0, json.loads(freeze_raw)['source_root'])
    source, source_pin = pinned(root / 'root_p37_canonical_result_classifier.py', expected=CANONICAL_SHA)
    queue_source, queue_pin = pinned(root / 'root_p37c3_sdk_queue.py', limit=1024**2)
    auto_raw, auto_pin = pinned(root / 'p37-responses/0117-1-result.json', expected=AUTO117_SHA)
    sem_raw, sem_pin = pinned(root / 'p37-responses/0111-1-result.json', expected=SEM111_SHA)
    map_raw, map_pin = pinned(root / 'ROOT-CAMPAIGN-MAP-ADMITTED.json')
    launch_raw, launch_pin = pinned(root / 'ROOT-ACTUAL-GAME-LAUNCH.json')
    bound_raw, bound_pin = pinned(root / 'p37-queue/ROOT-COMPLETED-MET-WARM-BOUND.json')
    pair_raw, pair_pin = pinned(root / 'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C3.json')
    gov_raw, gov_pin = pinned(root / 'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json')
    launch, mapping, bound, governance = map(json.loads, (launch_raw, map_raw, bound_raw, gov_raw))
    sem = json.loads(sem_raw)['result']['structured_content']
    body = json.loads(auto_raw)['result']['structured_content']
    warm = bound['fresh_frame']
    t0 = mapping['actual_initial_frame']
    planning = body['planning_source_frame']
    if (launch.get('pid') != 214568 or launch.get('creation_filetime') != 134368503807325674
            or mapping.get('game_creation_filetime') != launch['creation_filetime']
            or bound.get('machine_id') != 'xenoamess-full-tower-eb9d2c1186'
            or sem.get('date_raw') != warm['date_raw'] or warm['date_raw'] != 53144760
            or warm.get('actor_character_id') != 31254
            or any(sem.get(key) != warm[key] for key in ('snapshot_id', 'revision', 'native_revision', 'episode_run_id'))
            or (sem.get('played_character') or {}).get('character_id') != 31254
            or (sem.get('diagnostics') or {}).get('bridge_pid') != launch['pid']
            or any(planning.get(key) != warm[key] for key in warm)
            or planning.get('bridge_pid') != 214568 or planning.get('connection_generation') != 4
            or governance.get('completed_cycles') != 49
            or (governance.get('pending_cycle') or {}).get('auto_sequence') != 117):
        raise ValueError('Only this actually observed C3 same-Game warm opening may be adapted')
    changed = transform(source, t0, warm, planning)
    scopes = []
    for payload in (source, changed):
        scope = {'Path': Path, 'json': json, 'hashlib': hashlib, 'ast': ast, 'copy': copy}
        load_functions(queue_source, scope, str(root / 'root_p37c3_sdk_queue.py'))
        load_functions(payload, scope, str(root / 'root_p37_canonical_result_classifier.py'))
        scopes.append(scope)
    old, new = [scope['classify_auto_result_credit_v1'] for scope in scopes]
    call = {'state': governance['state'], 'pending_focus': governance.get('pending_focus'),
            'initial_frame': t0, 'game_pid': 214568}
    try:
        old(copy.deepcopy(body), **copy.deepcopy(call))
    except ValueError as error:
        if 'opening actor/date/episode' not in str(error):
            raise
        original_refusal = str(error)
    else:
        raise AssertionError('Original mismatch must reproduce')
    actual = new(copy.deepcopy(body), **copy.deepcopy(call))
    expected = old(copy.deepcopy(body), **{**copy.deepcopy(call), 'initial_frame': copy.deepcopy(warm)})
    if actual != expected or actual[0].get('existing_focus_verified') is not True:
        raise AssertionError('Original effect classifier result changed')
    mutations = []
    for name in ('wrong_game', 'wrong_source_date', 'wrong_episode', 'missing_focus', 'negative_XP', 'wrong_result_date'):
        bad, arguments = copy.deepcopy(body), copy.deepcopy(call)
        if name == 'wrong_game': arguments['game_pid'] += 1
        elif name == 'wrong_source_date': bad['planning_source_frame']['date_raw'] += 24
        elif name == 'wrong_episode': bad['initial_lifestyle_focus_gate']['episode_run_id'] = 'foreign'
        elif name == 'missing_focus': bad['plan']['initial_lifestyle_focus_existing']['current_focus']['presence'] = 'absent'
        elif name == 'negative_XP': bad['plan']['initial_lifestyle_focus_existing']['current_lifestyle_progress']['xp_total_raw'] = -1
        else: bad['result']['date_raw'] += 24
        try:
            new(bad, **arguments)
        except ValueError:
            mutations.append(name)
        else:
            raise AssertionError('Malformed original effect or source admitted: ' + name)
    # One prior C3 query demonstrates exact fall-through outside the LIFE view.
    other_raw, other_pin = pinned(root / 'p37-responses/0115-1-result.json')
    other = json.loads(other_raw)['result']['structured_content']
    if old(copy.deepcopy(other), **copy.deepcopy(call)) != new(copy.deepcopy(other), **copy.deepcopy(call)):
        raise AssertionError('Non-LIFE classifier behavior changed')
    args.output_root.mkdir(parents=True, exist_ok=False)
    candidate = args.output_root / 'root_c3_warm_life_opening_classifier.py'
    candidate.write_bytes(changed)
    retained_governance = args.output_root / 'INPUT-governance-original.json'
    with retained_governance.open('xb') as stream:
        stream.write(gov_raw)
    result = {'schema': 'xar.c3-warm-life-opening-classifier-qualification/v1',
        'machine_id': bound['machine_id'], 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': [source_pin, queue_pin, auto_pin, sem_pin, map_pin, launch_pin, bound_pin, pair_pin, gov_pin, other_pin, freeze_pin],
        'candidate': {'path': str(candidate.resolve()), 'bytes': len(changed), 'sha256': hashlib.sha256(changed).hexdigest()},
        'retained_governance_input': {'path': str(retained_governance.resolve()),
            'bytes': len(gov_raw), 'sha256': hashlib.sha256(gov_raw).hexdigest()},
        'old_refusal_reproduced': original_refusal, 'original_functions_AST_unchanged_except_dispatcher_name': True,
        'original_effect_result_with_actual_warm_frame_identical': True,
        'wrong_inputs_rejected': mutations, 'non_LIFE_actual115_identical': True,
        'same_Game': {'pid': launch['pid'], 'creation_filetime': launch['creation_filetime'],
            'birth_binding_scope': 'actual retained C3 owner and SEM/pair pins; pure classifier API carries PID only'},
        'T0_map_and_month_anchor_mutated': False, 'new_Game_Native_MCP_calls': 0,
        'runtime_files_mutated': 0, 'live_adopted': False,
        'expected_observation': actual[0]}
    receipt = args.output_root / 'QUALIFICATION.json'
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': result['candidate'], 'qualification': str(receipt), 'status': 'PASS'}))


if __name__ == '__main__':
    main()
