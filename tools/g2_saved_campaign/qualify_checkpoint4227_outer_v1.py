"""Exact C10 outer-dispatch qualification; no Game, SDK or Native access."""
from __future__ import annotations
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types

sys.dont_write_bytecode = True
MACHINE = 'xenoamess-full-tower-eb9d2c1186'
T = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
P = T.parent.parent / 'p51-fresh1066-v20261019-prepare01/c10-save4226-failure82'
KIND = 'checkpoint4226_source_bound_before_native_save'


def pin(path):
    b = Path(path).read_bytes()
    return {'path': str(Path(path).resolve()), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def bind_dispatcher(original, helper):
    require = lambda ok: None if ok else (_ for _ in ()).throw(ValueError('actual unused dispatcher differs'))
    require(hashlib.sha256(original).hexdigest() == '244bdb96be41b08c6441bb250d6aad8fad935f5e7a79a2f12e530202fe48c17b')
    suffix = f'''

recover_before_checkpoint4226 = recover_zero_rpc_preflight
async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={{"repair_kind":{KIND!r}}}:
        source=Path(__file__).with_name("root_c10_checkpoint4226_clear.py")
        payload=source.read_bytes()
        if len(payload)!={helper['bytes']} or hashlib.sha256(payload).hexdigest()!={helper['sha256']!r}:
            raise ValueError("reviewed SAVE4226 finite helper differs")
        scope={{}}
        exec(compile(payload,str(source),"exec"),scope)
        return await scope["recover"](queue,session,request,path,env)
    return await recover_before_checkpoint4226(queue,session,request,path,env)
'''
    value = original + suffix.encode('utf-8')
    compile(value, '<finite-dispatcher>', 'exec')
    return value


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require_output = args.output.resolve()
    if require_output.exists():
        raise FileExistsError('create-only software review')
    require_output.mkdir(parents=True)
    helper_source = Path(__file__).with_name('checkpoint4226_predispatch_clear_v1.py')
    helper = pin(helper_source)
    original_dispatch = T / 'root_saved_campaign_preflight.py'
    dispatcher = bind_dispatcher(original_dispatch.read_bytes(), helper)
    (require_output / 'root_c10_checkpoint4226_clear.py').write_bytes(helper_source.read_bytes())
    (require_output / 'root_saved_campaign_preflight.py').write_bytes(dispatcher)
    candidate_path = require_output / 'root_saved_campaign_preflight.py'
    module = types.ModuleType('root_saved_campaign_preflight')
    module.__file__ = str(candidate_path)
    exec(compile(dispatcher, str(candidate_path), 'exec'), module.__dict__)
    prior = sys.modules.get(module.__name__)
    sys.modules[module.__name__] = module
    queue_source = T / 'root_p37c10_sdk_queue.py'
    tree = ast.parse(queue_source.read_text(encoding='utf-8-sig'))
    original_state = json.loads((P / 'ROOT-CUMULATIVE-LOOP-STATE.json').read_bytes())
    original_gov = json.loads((P / 'ROOT-GOVERNANCE-RESULT-STATE.json').read_bytes())
    original_halt = json.loads((P / 'ROOT-CURRENT-HALT-P37.json').read_bytes())
    original_row = json.loads((T / 'p37-responses/4226-1-result.json').read_bytes())
    command = {'sequence': 4227, 'command': 'clear_zero_rpc_preflight_rejection', 'arguments': {'repair_kind': KIND}}
    results = []

    class StopFixture(BaseException):
        pass

    class AdmissionEnded(Exception):
        pass

    class RecordingPaused(Exception):
        pass

    for label in ('actual_outer_positive', 'foreign_checkpoint_rejected', 'foreign_actor_rejected'):
        writes = {}; calls = {'Native': 0, 'SDK': 0, 'guard': 0, 'halt': 0}
        Q = Path('qualification-only-Q')
        inbox = T / 'p37-requests'; outbox = T / 'p37-responses'
        current_request_path = inbox / '4227-1-result.json'
        state = copy.deepcopy(original_state)
        if label == 'foreign_checkpoint_rejected':
            state['pending_checkpoint']['save_sequence'] = 4225
        if label == 'foreign_actor_rejected':
            state['before']['actor_character_id'] = 31254

        def read(path, limit=262144):
            path = Path(path)
            if path in writes:
                return copy.deepcopy(writes[path])
            if path == current_request_path:
                return copy.deepcopy(command)
            if path == Q / 'ROOT-CUMULATIVE-LOOP-STATE.json':
                return copy.deepcopy(state)
            if path == Q / 'ROOT-GOVERNANCE-RESULT-STATE.json':
                return copy.deepcopy(original_gov)
            if path == T / 'ROOT-CURRENT-HALT-P37.json':
                return copy.deepcopy(original_halt)
            data = path.read_bytes()
            if len(data) > limit:
                raise ValueError('fixture small-source limit')
            return json.loads(data)

        def atomic(path, value, *, replace=False, limit=262144):
            path = Path(path)
            raw = json.dumps(value).encode()
            if len(raw) > limit or path in writes and not replace:
                raise ValueError('fixture original atomic contract')
            writes[path] = copy.deepcopy(value)

        async def sleep(_):
            raise StopFixture()

        env = {'__name__': 'actual_c10_outer_qualification', 'N': T, 'R': T.parent, 'Q': Q,
            'INBOX': inbox, 'OUTBOX': outbox, 'read': read, 'atomic': atomic,
            'now': lambda: datetime.now(timezone.utc), 'asyncio': types.SimpleNamespace(sleep=sleep),
            'SEMANTIC': 'ck3_take_semantic_snapshot_private_v1', 'METRICS': 'ck3_get_runtime_metrics_private_v1',
            'AdmissionEnded': AdmissionEnded, 'RecordingPaused': RecordingPaused,
            'pending_request_paths': lambda *a, **kw: [current_request_path],
            'preserve_first_exception': lambda *a, **kw: 'qualification-first-exception', 'print': lambda *a, **kw: None}
        fresh = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FreshQueue')
        functions = [next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'run_request_loop')]
        functions += [n for n in fresh.body if isinstance(n, ast.FunctionDef)
            and n.name in ('consume_sequence', 'persist_loop_state', 'halt_request')]
        exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), str(queue_source), 'exec'), env)
        class FakeQueue:
            def guard(self, **kwargs):
                calls['guard'] += 1
        for name in ('consume_sequence', 'persist_loop_state', 'halt_request'):
            setattr(FakeQueue, name, env[name])
        queue = FakeQueue()
        queue.next_sequence = 4227
        queue.full_loop_state = copy.deepcopy(state)
        queue.governance_result_state = copy.deepcopy(original_gov['state'])
        queue.lifestyle_pending_focus = copy.deepcopy(original_gov.get('pending_focus'))
        queue.result_classifier_pin = copy.deepcopy(original_gov['classifier'])
        queue.current_attempt = {'request': original_row['request'], 'row': original_row,
            'response': str(outbox / '4226-1-result.json')}
        queue.halted = copy.deepcopy(queue.current_attempt)
        queue.halt_cause = {'error_type': 'RuntimeError', 'message': 'SDK error'}
        queue.held_control = None
        queue.launch = {'pid': 153556, 'creation_filetime': 134368602545256920}
        try:
            asyncio.run(env['run_request_loop'](queue, object()))
        except StopFixture:
            pass
        output = writes[outbox / '4227-1-result.json']
        if label == 'actual_outer_positive':
            expected = copy.deepcopy(original_state); expected['pending_checkpoint'] = None
            assert queue.full_loop_state == expected and queue.halted is None and queue.current_attempt is None
            assert queue.next_sequence == 4228 and output['status'] == 'source_bound_predispatch_checkpoint_cleared'
            assert writes[Q / 'ROOT-GOVERNANCE-RESULT-STATE.json'] == original_gov
            assert output['Game_or_Native_or_SDK_RPC_calls'] == 0
        else:
            assert queue.full_loop_state == state and queue.halted is not None
            assert 'client_error' in output and 'denied' in output['client_error']
            assert not any(p.name == 'CHECKPOINT4226-PREDISPATCH-CLEAR-INTENT.json' for p in writes)
        assert calls['Native'] == calls['SDK'] == 0
        results.append({'case': label, 'PASS': True, 'calls': calls,
            'actual_original_outer_dispatch': True, 'actual_original_consume_persist_halt': True})
    if prior is None:
        sys.modules.pop(module.__name__, None)
    else:
        sys.modules[module.__name__] = prior
    receipt = {'schema': 'xar.c10.checkpoint4227-outer-qualification/v1', 'machine_id': MACHINE,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'SOFTWARE_ONLY_3_CASES_PASS',
        'helper': helper, 'dispatcher_original': pin(original_dispatch),
        'dispatcher_candidate': pin(candidate_path), 'queue_source': pin(queue_source),
        'packet': pin(P / 'FROZEN.json'), 'results': results, 'Game_or_RPC_or_process_calls': 0,
        'live_runtime_writes': 0, 'actual_recovery_completed': False,
        'fixture_scope': 'Actual run_request_loop + original consume/persist/halt; process/storage guard remains fixture-only'}
    (require_output / 'QUALIFICATION.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': receipt['status'], 'receipt': pin(require_output / 'QUALIFICATION.json')}))


if __name__ == '__main__':
    main()
