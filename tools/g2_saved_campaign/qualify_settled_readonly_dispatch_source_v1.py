"""Replay actual local154 admission refusal through old/new owner dispatch only."""
from __future__ import annotations
import argparse
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

from prepare_c3_life_opening_classifier_v1 import pinned
from settled_readonly_dispatch_source_v1 import transform


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-root', type=Path, required=True)
    p.add_argument('--metadata-review', type=Path, required=True)
    p.add_argument('--output-root', type=Path, required=True)
    args = p.parse_args()
    root = args.runtime_root.resolve(strict=True)
    source, source_pin = pinned(root / 'root_p37c3_sdk_queue.py', limit=1024**2)
    changed = transform(source)
    review = args.metadata_review.resolve(strict=True)
    met, met_pin = pinned(review / 'INPUTS/p37-responses/0153-1-result.json',
        expected='b144a3ad7e27c4413e59f05601f9e2eb36be38dfe77bf11dff706c8f3aabda32')
    fail, fail_pin = pinned(review / 'INPUTS/p37-responses/0154-1-result.json',
        expected='bb904b1550f94aa24210f4aac577f01b6dfa711556fd7881a560f3c2d42f6012')
    state_raw, state_pin = pinned(review / 'INPUTS/p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json',
        expected='cf67a0c6f5d266e0bc49800a7242e59fd14ef0071eab89a8f788f1f9d17b5140')
    install, install_pin = pinned(review / 'INPUTS/p37-responses/0148-1-result.json',
        expected='80c9de3c0227bd03dedf14417684856b8d8365a0fa24efc2ef4437060b1b0833')
    clean, clean_pin = pinned(root / 'root_p37_clean_classifier_install.py',
        expected='66886d41d07e374b038051d7eee85a0fdb364eddc3292a1a5fd407997e4dceca')
    failure = json.loads(fail); request = failure['request']; original = json.loads(met)
    proof = request['arguments']['clean_paused_proof']
    proof_raw, proof_pin = pinned(Path(proof['path']), expected=proof['sha256'])
    state = json.loads(state_raw); installed = json.loads(install)['result']['structured_content']
    current = {k: installed[k] for k in ('source', 'sha256')}
    args.output_root.mkdir(parents=True, exist_ok=False)
    candidate = args.output_root / 'root_p37_sdk_queue_settled_readonly_candidate.py'
    candidate.write_bytes(changed)
    tree = ast.parse(source)
    clean_module = ModuleType('root_p37_clean_classifier_install')
    exec(compile(clean, str(root / 'root_p37_clean_classifier_install.py'), 'exec'), clean_module.__dict__)

    class StopAfterOne(BaseException):
        pass
    class RecordingPaused(Exception):
        pass
    class AdmissionEnded(Exception):
        pass
    class NoRPC:
        async def call_tool(self, *a, **kw):
            raise AssertionError('No actual RPC allowed')
    async def no_sleep(*a):
        pass

    def exercise(payload, variant):
        writes = []
        scratch = args.output_root / variant
        scratch.mkdir(exist_ok=False)
        requests = scratch / 'requests'; requests.mkdir()
        outbox = scratch / 'responses'; outbox.mkdir()
        path = requests / '0154-1-result.json'
        path.write_text(json.dumps(request), encoding='utf-8')
        def pending(*a, **kw):
            if pending.called:
                raise StopAfterOne()
            pending.called = True
            return [path]
        pending.called = False
        namespace = {'Path': Path, 'json': json, 'hashlib': hashlib, 'ast': ast,
            'N': root, 'R': root.parent, 'Q': scratch, 'OUTBOX': outbox, 'INBOX': requests,
            'AUTO': 'ck3_auto_turn', 'SAVE': 'ck3_save_checkpoint',
            'SEMANTIC': 'ck3_take_semantic_snapshot_private_v1', 'METRICS': 'root_current_runtime_metrics',
            'RecordingPaused': RecordingPaused, 'AdmissionEnded': AdmissionEnded,
            'asyncio': SimpleNamespace(sleep=no_sleep), 'pending_request_paths': pending,
            'read': lambda file, *args: json.loads(Path(file).read_bytes()),
            'now': lambda: datetime.now(timezone.utc),
            'preserve_first_exception': lambda *a, **kw: 'offline-actual154-qualification',
            'atomic': lambda file, value, **kw: writes.append((str(file), copy.deepcopy(value)))}
        selected = [next(n for n in ast.parse(payload).body if isinstance(n, ast.AsyncFunctionDef)
            and n.name == 'run_request_loop')]
        for name in ('install_result_classifier', 'halt_request'):
            selected.append(next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name == name))
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(candidate), 'exec'), namespace)
        class FakeQueue(SimpleNamespace):
            install_result_classifier = namespace['install_result_classifier']
            halt_request = namespace['halt_request']
            def guard(self, **kw):
                pass
        attempt = {'request': original['request'], 'row': copy.deepcopy(original),
            'response': str(root / 'p37-responses/0153-1-result.json')}
        q = FakeQueue(full_loop_state=copy.deepcopy(state), current_attempt=attempt,
            halted=None, held_control=None, halt_cause=None, next_sequence=154,
            checkpoint_bootstrap_verified=True, result_classifier_pin=copy.deepcopy(current))
        if variant.endswith('unknown'):
            q.current_attempt['row']['client_error'] = 'unknown_read_transport'
        elif variant.endswith('pending'):
            q.full_loop_state['pending_cycle'] = {'global_turn': 59, 'auto_sequence': 153}
        elif variant.endswith('halted'):
            q.halted = copy.deepcopy(attempt)
        before = copy.deepcopy(q.full_loop_state)
        try:
            asyncio.run(namespace['run_request_loop'](q, NoRPC()))
        except StopAfterOne:
            pass
        if q.full_loop_state != before:
            raise AssertionError('No business or state change permitted')
        return {'halted_sequence': q.halted['request']['sequence'], 'halt_cause': q.halt_cause,
            'next_sequence': q.next_sequence, 'full_state_unchanged': q.full_loop_state == before,
            'new_RPC_calls': 0, 'local_writes': len(writes)}

    prior = sys.modules.get('root_p37_clean_classifier_install')
    sys.modules['root_p37_clean_classifier_install'] = clean_module
    try:
        old = exercise(source, 'original-clean')
        new = exercise(changed, 'candidate-clean')
        if (old['halted_sequence'] != 153 or new['halted_sequence'] != 154
                or old['halt_cause'] != new['halt_cause'] or new['halt_cause']['message'] != failure['client_error']):
            raise AssertionError('Actual154 local attribution mismatch not repaired')
        preserved = []
        for kind in ('unknown', 'pending', 'halted'):
            a = exercise(source, 'original-' + kind)
            b = exercise(changed, 'candidate-' + kind)
            if a != b or b['halted_sequence'] != 153:
                raise AssertionError('Unknown/pending original changed: ' + kind)
            preserved.append(kind)
    finally:
        if prior is None:
            sys.modules.pop('root_p37_clean_classifier_install', None)
        else:
            sys.modules['root_p37_clean_classifier_install'] = prior
    result = {'schema': 'xar.settled-readonly-dispatch-source-qualification/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186', 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': [source_pin, met_pin, fail_pin, state_pin, install_pin, clean_pin, proof_pin],
        'candidate': {'path': str(candidate), 'bytes': len(changed), 'sha256': hashlib.sha256(changed).hexdigest()},
        'original_AST_plus_one_guard_only': True, 'actual154_full_dispatch': {'old': old, 'candidate': new},
        'unknown_pending_halted_original_preserved': preserved, 'new_Game_Native_MCP_calls': 0,
        'runtime_mutations': 0, 'live_adopted': False,
        'scope': 'Next owner bootstrap source only; no local-control admission expansion or automatic recovery.'}
    (args.output_root / 'QUALIFICATION.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'candidate': result['candidate']}))


if __name__ == '__main__':
    main()
