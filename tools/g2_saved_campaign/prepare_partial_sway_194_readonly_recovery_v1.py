"""Create-only qualification of AUTO194's zero-RPC readonly partial recap."""
from __future__ import annotations
import argparse
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from prepare_c3_life_opening_classifier_v1 import pinned
from partial_sway_194_readonly_recovery_v1 import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--source-review', type=Path, required=True)
    parser.add_argument('--state-freeze', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    root = args.runtime_root.resolve(strict=True)
    review, review_pin = pinned(args.source_review,
        expected='6cf39a4277e95cf660840e2728c201fc779497cc0b16c237c03a99f06cc0d1aa')
    freeze, freeze_pin = pinned(args.state_freeze,
        expected='172fdb55db129166f44d1b95caaf6cedade57deb23bf0eb1d83541d8033c048f')
    met, met_pin = pinned(root / 'p37-responses/0193-1-result.json',
        expected='d40c98fd93f29609f80e4f8ae8990da8e54253dbcfc863a5709cd27c7485a383')
    old, old_pin = pinned(root / 'root_p37_known_owner_recovery.py',
        expected='499c84652fd06750d53cfc8d15ea5a0067beac9d5fd93d47e0a641d2edf08c7d')
    leaf, leaf_pin = pinned(Path(__file__).with_name('partial_sway_194_readonly_recovery_v1.py'), limit=32768)
    queue_raw, queue_pin = pinned(root / 'root_p37c3_sdk_queue.py', limit=1024**2)
    launch, launch_pin = pinned(root / 'ROOT-ACTUAL-GAME-LAUNCH.json')
    admission = {'schema': 'xar.partial-sway194-readonly-admission/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186', 'source_review': review_pin,
        'state_freeze': freeze_pin, 'before_metrics': met_pin}
    meta, retained, original, metrics = validate(admission)
    changed = old.decode().replace('async def recover(queue, session, request, path, env,',
        'async def recover_before_partial194(queue, session, request, path, env,', 1)
    leaf_hash = hashlib.sha256(leaf).hexdigest()
    changed += f'''

async def recover(queue, session, request, path, env, *, birth_reader=None, lifecycle_executor=None):
    if request.get("arguments") == {{"recovery_kind": "partial_sway_readonly_194_zero_rpc"}}:
        import json
        source = Path(__file__).with_name("root_partial_sway194_readonly_recap.py")
        payload = source.read_bytes()
        if len(payload) > 32768 or hashlib.sha256(payload).hexdigest() != {leaf_hash!r}:
            raise ValueError("reviewed194 readonly recovery leaf differs")
        scope = {{}}
        exec(compile(payload, str(source), "exec"), scope)
        if birth_reader is None:
            from root_p37_known_pause_recovery_control import process_birth_filetime
            birth_reader = process_birth_filetime
        return await scope["recover"](queue, session, request, path, env,
            admission={admission!r}, birth_reader=birth_reader)
    return await recover_before_partial194(queue, session, request, path, env,
        birth_reader=birth_reader, lifecycle_executor=lifecycle_executor)
'''
    expected = ast.parse(old)
    for node in expected.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == 'recover':
            node.name = 'recover_before_partial194'
    if [ast.dump(n) for n in expected.body] != [ast.dump(n) for n in ast.parse(changed).body[:-1]]:
        raise AssertionError('Original1024 contracts changed')
    args.output_root.mkdir(parents=True, exist_ok=False)
    candidate = args.output_root / 'root_p37_known_owner_recovery.py'
    candidate.write_text(changed, encoding='utf-8')
    (args.output_root / 'root_partial_sway194_readonly_recap.py').write_bytes(leaf)
    (args.output_root / 'ADMISSION.json').write_text(json.dumps(admission, indent=2)+'\n', encoding='utf-8')
    scope = {'__file__': str(candidate)}
    exec(compile(changed, str(candidate), 'exec'), scope)
    writes = []
    def atomic(path, value, **kwargs):
        writes.append((str(path), copy.deepcopy(value)))
    base = {'atomic': atomic, 'Q': root / 'p37-queue', 'N': root,
        'now': lambda: datetime.now(timezone.utc)}
    tree = ast.parse(queue_raw)
    frame = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'frame')
    consume = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'consume_sequence')
    persist = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'persist_loop_state')
    exec(compile(ast.Module(body=[frame, consume, persist], type_ignores=[]),
        str(root / 'root_p37c3_sdk_queue.py'), 'exec'), base)
    gov = retained['ROOT-GOVERNANCE-RESULT-STATE.json']; state = retained['ROOT-CUMULATIVE-LOOP-STATE.json']

    class FakeQueue(SimpleNamespace):
        consume_sequence = base['consume_sequence']
        persist_loop_state = base['persist_loop_state']
        def guard(self):
            self.guard_calls += 1

    def make_queue():
        return FakeQueue(next_sequence=195, full_loop_state=copy.deepcopy(state),
            halted={'request': original['request'], 'row': copy.deepcopy(original),
                'response': str(root / 'p37-responses/0194-1-result.json')},
            current_attempt=None, held_control=None, halt_cause={'message': 'SDK error'},
            launch=json.loads(launch), job={'game_creation_filetime': 134368503807325674},
            checkpoint_bootstrap_verified=True, guard_calls=0,
            governance_result_state=copy.deepcopy(gov['state']), lifestyle_pending_focus=gov['pending_focus'],
            result_classifier_pin=copy.deepcopy(gov['classifier']))
    env = {**base, 'INBOX': root / 'p37-requests', 'OUTBOX': root / 'p37-responses',
        'decoded': lambda row: row['result']['structured_content']}
    request = {'sequence': 195, 'command': 'recover_known_owner_1024',
        'arguments': {'recovery_kind': 'partial_sway_readonly_194_zero_rpc'}}
    class NoRPC:
        async def call_tool(self, *args, **kwargs):
            raise AssertionError('No RPC may run')
    q = make_queue()
    receipt = asyncio.run(scope['recover'](q, NoRPC(), request, env['INBOX'] / '0195-1-result.json', env,
        birth_reader=lambda pid: 134368503807325674,
        lifecycle_executor=lambda *a, **kw: (_ for _ in ()).throw(AssertionError('No Native lifecycle'))))
    if q.next_sequence != 196 or q.halted is not None or q.full_loop_state['pending_cycle'] is not None:
        raise AssertionError('Local recovery did not finish')
    for field in ('completed_cycles', 'counts', 'before', 'actual_saved_checkpoint', 'campaign_goal_anchor'):
        if q.full_loop_state[field] != state[field]:
            raise AssertionError('Settled credit/source anchor changed')
    if len(writes) != 5 or q.guard_calls != 1:
        raise AssertionError('Original consume/persist path not used')
    negatives = []
    for name in ('wrong_birth', 'wrong_original', 'wrong_counts', 'wrong_pending', 'wrong_live_classifier'):
        q = make_queue(); birth = lambda pid: 134368503807325674
        if name == 'wrong_birth': birth = lambda pid: 1
        elif name == 'wrong_original': q.halted['row']['client_error'] = 'unknown'
        elif name == 'wrong_counts': q.full_loop_state['completed_cycles'] += 1
        elif name == 'wrong_pending': q.full_loop_state['pending_cycle']['auto_sequence'] = 143
        else: q.result_classifier_pin['sha256'] = 'foreign'
        before = len(writes)
        try:
            asyncio.run(scope['recover'](q, NoRPC(), request, env['INBOX'] / '0195-1-result.json', env, birth_reader=birth))
        except ValueError:
            if q.next_sequence != 195 or len(writes) != before:
                raise AssertionError('Negative consumed or wrote')
            negatives.append(name)
        else:
            raise AssertionError('Bad readonly194 accepted: ' + name)
    proof = {'schema': 'xar.partial194-zero-rpc-software-qualification/v1',
        'machine_id': admission['machine_id'], 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': [review_pin, freeze_pin, met_pin, old_pin, leaf_pin, queue_pin, launch_pin],
        'candidate': {'path': str(candidate), 'bytes': candidate.stat().st_size,
            'sha256': hashlib.sha256(candidate.read_bytes()).hexdigest()},
        'leaf': {'path': str(args.output_root / 'root_partial_sway194_readonly_recap.py'),
            'bytes': len(leaf), 'sha256': leaf_hash},
        'original1024_AST_unchanged_except_recover_name': True,
        'actual_original_frame_consume_persist_composition': True, 'negative_cases_rejected': negatives,
        'new_MCP_Native_calls': 0, 'runtime_mutations': 0, 'receipt': receipt, 'live_adopted': False}
    (args.output_root / 'QUALIFICATION.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'candidate': proof['candidate'], 'leaf': proof['leaf']}))


if __name__ == '__main__':
    main()
