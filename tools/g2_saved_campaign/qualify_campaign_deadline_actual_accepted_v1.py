"""Compare final C3 deadline classifier against actual sealed normal122/month126."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    review = args.candidate_root.resolve(strict=True)
    freeze, fp = pinned(root / 'ROOT-FINAL-SDK-FREEZE-P37C.json', limit=1024**2)
    sys.path.insert(0, json.loads(freeze)['source_root'])
    queue, qp = pinned(root / 'root_p37c3_sdk_queue.py', limit=1024**2)
    old, op = pinned(root / 'root_p37c3_crown_priority_classifier.py',
        expected='9da4445b22bf49c616ad190023655911a102c76d225c3052c662e58292c23a11')
    new, np = pinned(review / 'root_c3_native_deadline_classifier.py',
        expected='d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991')
    functions = []
    for payload in (old, new):
        namespace = {'Path': Path, 'ast': ast, 'json': json, 'hashlib': hashlib, 'copy': copy}
        load_functions(queue, namespace, str(root / 'root_p37c3_sdk_queue.py'))
        load_functions(payload, namespace, str(root / 'root_p37c3_crown_priority_classifier.py'))
        if payload == new:
            f = namespace['classify_clock_advance_v1']
            f.__code__ = f.__code__.replace(co_filename=str(review / 'root_c3_native_deadline_classifier.py'))
        functions.append(namespace['classify_auto_result_credit_v1'])
    mapping, mp = pinned(root / 'ROOT-CAMPAIGN-MAP-ADMITTED.json')
    parameters = {'initial_frame': json.loads(mapping)['actual_initial_frame'], 'game_pid': 214568,
        'state': {'council_pending': None, 'construction_actions': {}}, 'pending_focus': None}
    cases = []
    for sequence, days in ((122, 8), (126, 4)):
        raw, rp = pinned(root / f'p37-responses/{sequence:04}-1-result.json')
        body = json.loads(raw)['result']['structured_content']
        previous, current = [f(copy.deepcopy(body), **copy.deepcopy(parameters)) for f in functions]
        if previous != current or current[0]['actual_elapsed_days'] != days:
            raise AssertionError('Actual accepted observation changed')
        if not all(a['result'].get('accepted') is True for a in body['result']['actions']):
            raise AssertionError('The original case is not wholly accepted')
        cases.append({'original': rp, 'actual_elapsed_days': days, 'all_actions_accepted': True,
            'full_dispatcher_result_identical': True, 'observation': current[0]})
    proof = {'schema': 'xar.c3-deadline-actual-accepted-regression/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'sources': [fp, qp, op, np, mp],
        'actual_cases': cases, 'new_Game_Native_MCP_calls': 0, 'runtime_mutations': 0,
        'candidate_bytes_unchanged': True}
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'output': str(args.output)}))


if __name__ == '__main__':
    main()
