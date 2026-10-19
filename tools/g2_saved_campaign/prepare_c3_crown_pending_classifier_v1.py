"""Adapt source-proven missing hot-Crown metadata; preserve all receipt guards."""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from prepare_c3_life_opening_classifier_v1 import load_functions, pinned

SOURCE_SHA = '41e348591d7c3dd7f42d39daa71ee7ba8d0b857ca9a399fc5307228b6b126cb0'
AUTO_SHA = 'ce6cc323f7be1c6c2aac637a0c53ca173d0fa2146f6acdff56fd16dc1d3c1ea5'


def transform(raw):
    tree = ast.parse(raw.decode('utf-8-sig'))
    target = [node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name == 'classify_auto_result_credit_v1'][-1]
    lines = raw.decode('utf-8-sig').splitlines(keepends=True)
    index = target.lineno - 1
    lines[index] = lines[index].replace('def classify_auto_result_credit_v1(',
        'def classify_before_c3_pending_crown_v1(', 1)
    suffix = '''

def classify_auto_result_credit_v1(body, *, state=None, pending_focus=None, initial_frame=None, game_pid=None):
    p = body.get("plan", {})
    if (body.get("selected_step") == "verify-realm-law-crown-v1-private"
            and p.get("policy") == "pending-material-publication-v1"
            and p.get("phase") == "pending_material_independent_receipt" and "crown_cold_recovery" not in p):
        m = p.get("pending_material", {}); q = p.get("crown_pending_action", {})
        f = classify_gameplay_start_binding_v1(body, initial_frame=initial_frame, game_pid=game_pid)
        if not (game_pid == 214568 and m.get("domain") == "crown" and m.get("status") == "ready"
                and m.get("same_process") is True and m.get("business_credit") is False and m.get("pending") == q
                and q.get("source_context") == {"bridge_pid": game_pid, "episode_run_id": f["episode_run_id"]}
                and m.get("pre_native_revision") == q.get("pre_native_revision")
                and m.get("observed_native_revision") == f["native_revision"] > q["pre_native_revision"]):
            raise ValueError("C3 Crown priority hot source tuple differs")
        body = {**body, "plan": {**p, "crown_cold_recovery": False}}
    return classify_before_c3_pending_crown_v1(body, state=state, pending_focus=pending_focus,
        initial_frame=initial_frame, game_pid=game_pid)
'''
    changed = (''.join(lines) + suffix).encode()
    if len(changed) > 262144:
        raise ValueError('Existing classifier bound exceeded')
    expected = copy.deepcopy(tree)
    [node for node in expected.body if isinstance(node, ast.FunctionDef)
     and node.name == 'classify_auto_result_credit_v1'][-1].name = 'classify_before_c3_pending_crown_v1'
    after = ast.parse(changed.decode('utf-8-sig'))
    if [ast.dump(node) for node in expected.body] != [ast.dump(node) for node in after.body[:len(expected.body)]]:
        raise AssertionError('An original guard changed')
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    freeze_raw, freeze_pin = pinned(root / 'ROOT-FINAL-SDK-FREEZE-P37C.json', limit=1024**2)
    frozen = json.loads(freeze_raw)
    sdk = Path(frozen['source_root'])
    sys.path.insert(0, str(sdk))
    source_pins = []
    for relative in ('xar_autoplayer/bridge/service.py', 'xar_autoplayer/bridge/pending_material_publication_v1.py',
                     'xar_autoplayer/crown_authority_formal_consumer_v1.py'):
        expected = next(row for row in frozen['files'] if row['relative'] == relative)
        _, ref = pinned(sdk / relative, expected=expected['sha256'], limit=1024**2)
        source_pins.append(ref)
    raw, raw_pin = pinned(root / 'root_p37c3_warm_life_classifier.py', expected=SOURCE_SHA)
    queue, queue_pin = pinned(root / 'root_p37c3_sdk_queue.py', limit=1024**2)
    auto_raw, auto_pin = pinned(root / 'p37-responses/0130-1-result.json', expected=AUTO_SHA)
    gov_raw, gov_pin = pinned(root / 'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json')
    map_raw, map_pin = pinned(root / 'ROOT-CAMPAIGN-MAP-ADMITTED.json')
    launch_raw, launch_pin = pinned(root / 'ROOT-ACTUAL-GAME-LAUNCH.json')
    launch, mapping, governance = map(json.loads, (launch_raw, map_raw, gov_raw))
    if launch.get('pid') != 214568 or launch.get('creation_filetime') != 134368503807325674:
        raise ValueError('Only the retained actual C3 Game is supported')
    body = json.loads(auto_raw)['result']['structured_content']
    changed = transform(raw)
    functions = []
    for payload in (raw, changed):
        scope = {'Path': Path, 'json': json, 'hashlib': hashlib, 'ast': ast, 'copy': copy}
        load_functions(queue, scope, str(root / 'root_p37c3_sdk_queue.py'))
        load_functions(payload, scope, str(root / 'root_p37c3_warm_life_classifier.py'))
        functions.append(scope['classify_auto_result_credit_v1'])
    old, new = functions
    call = {'state': governance['state'], 'pending_focus': governance.get('pending_focus'),
            'initial_frame': mapping['actual_initial_frame'], 'game_pid': launch['pid']}
    try:
        old(copy.deepcopy(body), **copy.deepcopy(call))
    except ValueError as error:
        if 'receipt original ID/target/source/frame mismatch' not in str(error): raise
        refused = str(error)
    else:
        raise AssertionError('Original format mismatch not reproduced')
    projected = copy.deepcopy(body)
    projected['plan']['crown_cold_recovery'] = False
    expected = old(projected, **copy.deepcopy(call))
    actual = new(copy.deepcopy(body), **copy.deepcopy(call))
    if actual != expected or actual[0].get('crown_material_verified') is not True or actual[1]['crown_pending'] is not None:
        raise AssertionError('Original complete Crown verification changed')
    negative = []
    for name in ('wrong_game', 'cold_source', 'extra_source_field', 'wrong_ID', 'wrong_target',
                 'stale_post_revision', 'wrong_debit', 'unverified_effect', 'wrong_episode'):
        bad, parameters = copy.deepcopy(body), copy.deepcopy(call)
        if name == 'wrong_game': parameters['game_pid'] += 1
        elif name == 'cold_source': bad['plan']['pending_material']['same_process'] = False
        elif name == 'extra_source_field': bad['plan']['crown_pending_action']['source_context']['foreign'] = 1
        elif name == 'wrong_ID': bad['result']['submitted_request_id'] = 'crown-formal-foreign'
        elif name == 'wrong_target': bad['result']['effective_law_key'] = 'crown_authority_3'
        elif name == 'stale_post_revision': bad['result']['post_native_revision'] = 53
        elif name == 'wrong_debit': bad['result']['charges'][0]['post_balance_raw'] += 1
        elif name == 'unverified_effect': bad['result']['resources_verified'] = False
        else: bad['plan']['crown_pending_action']['episode_run_id'] = 'foreign'
        try:
            new(bad, **parameters)
        except ValueError:
            negative.append(name)
        else:
            raise AssertionError('Original identity/effect guard was bypassed: ' + name)
    prior_raw, prior_pin = pinned(root / 'p37-responses/0117-1-result.json',
        expected='5d4b455ef083484755d7910bab7036de972961a321e943ceaaef79e8c2024de3')
    prior = json.loads(prior_raw)['result']['structured_content']
    non_crown_call = {**copy.deepcopy(call), 'state': {'council_pending': None, 'construction_actions': {}}, 'pending_focus': None}
    if old(copy.deepcopy(prior), **copy.deepcopy(non_crown_call)) != new(copy.deepcopy(prior), **copy.deepcopy(non_crown_call)):
        raise AssertionError('Prior LIFE repair changed')
    args.output_root.mkdir(parents=True, exist_ok=False)
    candidate = args.output_root / 'root_c3_crown_priority_classifier.py'
    candidate.write_bytes(changed)
    retained_governance = args.output_root / 'INPUT-governance-original.json'
    with retained_governance.open('xb') as stream:
        stream.write(gov_raw)
    result = {'schema': 'xar.c3-crown-priority-compatibility-qualification/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186', 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': [raw_pin, queue_pin, auto_pin, gov_pin, map_pin, launch_pin, prior_pin, freeze_pin] + source_pins,
        'candidate': {'path': str(candidate.resolve()), 'bytes': len(changed), 'sha256': hashlib.sha256(changed).hexdigest()},
        'retained_governance_input': {'path': str(retained_governance.resolve()),
            'bytes': len(gov_raw), 'sha256': hashlib.sha256(gov_raw).hexdigest()},
        'original_refusal': refused, 'original_function_AST_unchanged_except_final_dispatcher_name': True,
        'projection': 'Only a missing crown_cold_recovery flag is false when the source-bound full hot tuple proves it.',
        'Native_receipt_mutated': False, 'original_complete_effect_validation_passed': True,
        'negative_cases_rejected': negative, 'original_LIFE117_behavior_unchanged': True,
        'old_material_observation_with_only_metadata_projection_identical': True,
        'observation': actual[0], 'new_Game_Native_MCP_calls': 0, 'runtime_files_mutated': 0,
        'live_adopted': False,
        'installation': 'Owner copies identical bytes into runtime beside original battle/route helpers, then existing local install/reconsume original130.'}
    (args.output_root / 'QUALIFICATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'candidate': result['candidate'], 'status': 'PASS'}))


if __name__ == '__main__':
    main()
