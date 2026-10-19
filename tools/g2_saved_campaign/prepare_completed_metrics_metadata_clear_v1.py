"""Compose and qualify local MET153 metadata recovery without any live RPC."""
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-root', type=Path, required=True)
    p.add_argument('--output-root', type=Path, required=True)
    args = p.parse_args()
    root = args.runtime_root.resolve(strict=True)
    old, old_pin = pinned(root / 'root_saved_campaign_preflight.py',
        expected='45276ddc18cfeb1823f4eb0ff682a1e2b55e883c95384a5db889177a91f53f23', limit=16384)
    leaf, leaf_pin = pinned(Path(__file__).with_name('completed_metrics_metadata_clear_v1.py'), limit=16384)
    old_tree = ast.parse(old)
    changed = old.decode().replace('async def recover_zero_rpc_preflight(',
        'async def recover_zero_rpc_preflight_original(', 1)
    digest = hashlib.sha256(leaf).hexdigest()
    changed += f'''

async def recover_zero_rpc_preflight(queue, session, request, path, env):
    if request.get("arguments") == {{"recovery_kind": "completed_metrics153_metadata154"}}:
        source = Path(__file__).with_name("root_completed_metrics153_metadata_clear.py")
        payload = source.read_bytes()
        if len(payload) > 16384 or hashlib.sha256(payload).hexdigest() != {digest!r}:
            raise ValueError("reviewed MET153 metadata recovery source differs")
        scope = {{}}
        exec(compile(payload, str(source), "exec"), scope)
        return await scope["recover_completed_metadata_v1"](queue, session, request, path, env)
    return await recover_zero_rpc_preflight_original(queue, session, request, path, env)
'''
    expected = copy.deepcopy(old_tree)
    for node in expected.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == 'recover_zero_rpc_preflight':
            node.name = 'recover_zero_rpc_preflight_original'
    actual = ast.parse(changed)
    if [ast.dump(n) for n in expected.body] != [ast.dump(n) for n in actual.body[:-1]]:
        raise AssertionError('Original preflight contracts changed')
    args.output_root.mkdir(parents=True, exist_ok=False)
    candidate = args.output_root / 'root_saved_campaign_preflight.py'
    candidate.write_text(changed, encoding='utf-8')
    (args.output_root / 'root_completed_metrics153_metadata_clear.py').write_bytes(leaf)
    namespace = {'__file__': str(candidate)}
    exec(compile(changed, str(candidate), 'exec'), namespace)
    # Software proof consumes actual source rows, actual original frame(), no fake success bodies.
    queue_source, queue_pin = pinned(root / 'root_p37c3_sdk_queue.py', limit=1024**2)
    frame_node = next(n for n in ast.parse(queue_source).body if isinstance(n, ast.FunctionDef) and n.name == 'frame')
    frame_scope = {}
    exec(compile(ast.Module(body=[frame_node], type_ignores=[]), str(root / 'root_p37c3_sdk_queue.py'), 'exec'), frame_scope)
    source_rows = {}
    from completed_metrics_metadata_clear_v1 import PINS
    pins = []
    for relative, sha in PINS.items():
        raw, ref = pinned(root / relative, expected=sha, limit=16384)
        source_rows[relative] = json.loads(raw); pins.append(ref)
    launch_raw, launch_pin = pinned(root / 'ROOT-ACTUAL-GAME-LAUNCH.json', limit=16384)
    original = source_rows['p37-responses/0153-1-result.json']
    installed = source_rows['p37-responses/0148-1-result.json']['result']['structured_content']
    state = source_rows['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json']
    request = {'sequence': 157, 'command': 'clear_zero_rpc_preflight_rejection',
        'arguments': {'recovery_kind': 'completed_metrics153_metadata154'}}
    writes = []
    env = {'N': root, 'Q': root / 'p37-queue', 'OUTBOX': root / 'p37-responses',
        'METRICS': 'root_current_runtime_metrics', 'CURRENT_HALT_NAME': 'ROOT-CURRENT-HALT-P37.json',
        'decoded': lambda row: row['result']['structured_content'], 'frame': frame_scope['frame'],
        'atomic': lambda path, row, **kwargs: writes.append((str(path), copy.deepcopy(row))),
        'now': lambda: datetime.now(timezone.utc)}

    class FakeQueue(SimpleNamespace):
        def consume_sequence(self, value):
            if value['sequence'] != self.next_sequence:
                raise AssertionError('bad monotonic control')
            self.next_sequence += 1
            return value['sequence']

    def make_queue():
        return FakeQueue(next_sequence=157, full_loop_state=copy.deepcopy(state),
            halted={'request': original['request'], 'row': copy.deepcopy(original),
                'response': str(root / 'p37-responses/0153-1-result.json')},
            halt_cause={'error_type': 'ValueError', 'message': 'classifier install is not a current clean settled boundary'},
            result_classifier_pin={k: installed[k] for k in ('source', 'sha256')},
            launch=json.loads(launch_raw), checkpoint_bootstrap_verified=True,
            current_attempt=None, held_control=None)

    class NoRPC:
        async def call_tool(self, *a, **kw):
            raise AssertionError('No MCP or Native call permitted')

    # Use the exact generated branch; a fake kernel reader replaces only process-birth observation.
    import sys
    prior = sys.modules.get('root_p37_known_pause_recovery_control')
    sys.modules['root_p37_known_pause_recovery_control'] = SimpleNamespace(
        process_birth_filetime=lambda pid: 134368503807325674)
    try:
        q = make_queue()
        result = asyncio.run(namespace['recover_zero_rpc_preflight'](q, NoRPC(), request,
            root / 'p37-requests/0157-1-result.json', env))
        if q.next_sequence != 158 or q.halted is not None or q.full_loop_state != state or len(writes) != 3:
            raise AssertionError('Local recovery changed settled credit or did not clear exactly once')
        negatives = []
        for name in ('wrong_sequence', 'wrong_live_pin', 'pending_cycle', 'original_unknown', 'wrong_cause', 'wrong_birth'):
            q = make_queue()
            if name == 'wrong_sequence': q.next_sequence += 1
            elif name == 'wrong_live_pin': q.result_classifier_pin['sha256'] = 'f857'
            elif name == 'pending_cycle': q.full_loop_state['pending_cycle'] = {'global_turn': 59}
            elif name == 'original_unknown': q.halted['row']['client_error'] = 'unknown'
            elif name == 'wrong_cause': q.halt_cause['message'] = 'unknown'
            else: sys.modules['root_p37_known_pause_recovery_control'].process_birth_filetime = lambda pid: 1
            before = len(writes)
            try:
                asyncio.run(namespace['recover_zero_rpc_preflight'](q, NoRPC(), request,
                    root / 'p37-requests/0157-1-result.json', env))
            except ValueError:
                if len(writes) != before or q.next_sequence != (158 if name == 'wrong_sequence' else 157):
                    raise AssertionError('Negative case mutated state')
                negatives.append(name)
            else:
                raise AssertionError('Bad recovery accepted: ' + name)
    finally:
        if prior is None: sys.modules.pop('root_p37_known_pause_recovery_control', None)
        else: sys.modules['root_p37_known_pause_recovery_control'] = prior
    proof = {'schema': 'xar.c3-met153-metadata-clear-software-qualification/v1',
        'machine_id': 'xenoamess-full-tower-eb9d2c1186', 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': [old_pin, leaf_pin, queue_pin, launch_pin] + pins,
        'candidate': {'path': str(candidate), 'bytes': candidate.stat().st_size,
            'sha256': hashlib.sha256(candidate.read_bytes()).hexdigest()},
        'leaf': {'path': str(args.output_root / 'root_completed_metrics153_metadata_clear.py'),
            'bytes': len(leaf), 'sha256': digest}, 'original_preflight_AST_unchanged_except_name': True,
        'negative_cases_rejected': negatives, 'receipt': result, 'fake_session_call_count': 0,
        'runtime_mutations': 0, 'new_RPC_calls': 0, 'live_adopted': False}
    (args.output_root / 'QUALIFICATION.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'candidate': proof['candidate'], 'leaf': proof['leaf'], 'status': 'PASS'}))


if __name__ == '__main__':
    main()
