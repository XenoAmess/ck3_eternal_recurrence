import ast
import asyncio
import copy
import importlib.util
import io
import json
import sys
import types
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

REPO = Path('Z:/ck3_mod_rewrite')
N = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T = N / 'robert30-v20261019-campaign01/runtime'
F = N / 'p51-fresh1066-v20261019-prepare01/c7-succession3851-failure77'
sys.path[:0] = [str(REPO), str(N / 'sdk-v20261019-candidate/src06'), str(T)]
spec = importlib.util.spec_from_file_location('resume3851_tested', REPO / 'tools/g2_saved_campaign/succession3851_first_semantic_resume_v1.py')
leaf = importlib.util.module_from_spec(spec); spec.loader.exec_module(leaf)
read = lambda p, *unused: json.loads(Path(p).read_text(encoding='utf-8-sig'))
state = read(F / 'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json')
row = read(F / 'p37-responses/3851-1-result.json')
request = {'sequence': 3852, 'command': 'recover_known_owner_1024', 'arguments': {'repair_kind': leaf.KIND}}
path = T / 'p37-requests/3852-1-result.json'

class Done(Exception): pass
class RecordingPaused(Exception): pass
class Queue:
    def __init__(self):
        self.next_sequence = 3852; self.held_control = None
        self.full_loop_state = copy.deepcopy(state)
        self.halted = {'request': row['request'], 'row': row, 'response': str(T / 'p37-responses/3851-1-result.json')}
        self.current_attempt = copy.deepcopy(self.halted)
        self.launch = {'pid': 153556, 'pipe': row['result']['structured_content']['diagnostics']['pipe_name']}
        self.job = {'game_creation_filetime': 134368602545256920}
        self.expected_lifecycle_binding = row['result']['structured_content']['succession_lifecycle']
        self.last_guard_observation = {}; self.halt_cause = None
    def guard(self, **kw): pass
    def call_budget(self, tool): return 1
    def persist_loop_state(self): raise AssertionError('no business tail commit before simulated Continue')

def decoded(r):
    if r.get('client_error'):
        raise ValueError(r['client_error'])
    return r['result']['structured_content']

async def run():
    writes = {}; relays = []; calls = []
    def atomic(p, value, **kw):
        writes[str(p)] = copy.deepcopy(value)
    env = {'N': T, 'Q': T / 'p37-queue', 'INBOX': T / 'p37-requests',
           'OUTBOX': T / 'p37-responses', 'SEMANTIC': row['request']['tool'],
           'REPLY_RESERVE': 262144, 'read': read, 'decoded': decoded,
           'now': lambda: datetime.now(timezone.utc), 'atomic': atomic,
           'display_projection': lambda r,b: {'actual_original_source': r['request']['sequence']}}
    q = Queue()
    env['pending_request_paths'] = lambda *a, **kw: []
    leaf.validate(q, request, path, env)
    negatives = []
    for name, mutate in [
        ('different_Game', lambda q: q.launch.update(pid=1)),
        ('queue_pending', lambda q: q.full_loop_state.update(pending_cycle={'stage': 'auto_unsettled'})),
        ('wrong_old_response', lambda q: q.halted.update(response='other.json')),
        ('wrong_next_sequence', lambda q: setattr(q, 'next_sequence', 3853)),
    ]:
        bad = Queue(); mutate(bad)
        try: leaf.validate(bad, request, path, env)
        except ValueError: negatives.append(name)
        else: raise AssertionError('negative accepted: ' + name)
    relay = types.ModuleType('root_p37c6_overlay_relay')
    relay.relay_compact = lambda p, value: relays.append((str(p), value))
    relay.error_projection = lambda r: {'qualification_error': r.get('client_error')}
    sys.modules['root_p37c6_overlay_relay'] = relay
    helper = types.ModuleType('root_p37_succession3851_resume')
    async def resumed(q, s, r, p, e, **kw):
        return await leaf.recover(q,s,r,p,e,birth_reader=lambda pid: 134368602545256920)
    helper.recover = resumed
    sys.modules[helper.__name__] = helper
    owner_source = (T / 'root_p37_known_owner_recovery.py').read_bytes()
    owner = types.ModuleType('root_p37_known_owner_recovery')
    exec(compile(leaf.transform_unused_known_owner(owner_source), '<actual-unused-owner-plus-finite-branch>', 'exec'), owner.__dict__)
    sys.modules[owner.__name__] = owner
    queue_tree = ast.parse((T / 'root_p37c7_sdk_queue.py').read_text(encoding='utf-8-sig'))
    wanted = {'consume_sequence', 'halt_request'}
    methods = {}
    for cls in (n for n in queue_tree.body if isinstance(n, ast.ClassDef)):
        for item in cls.body:
            if isinstance(item, ast.FunctionDef) and item.name in wanted and item.name not in methods:
                methods[item.name] = item
    loop = next(n for n in queue_tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'run_request_loop')
    async def sleep(_): raise Done()
    class Session:
        async def call_tool(self, tool, args, **kw):
            calls.append((q.next_sequence - 1, tool, args))
            raise RuntimeError('SIMULATED_NEXT_UNIQUE_CONTINUE_NOT_EXECUTED')
    fake_read = lambda p, *a: request if Path(p) == path else read(p, *a)
    def pending(*a, **kw):
        if kw.get('held_control') == path.name: return []
        return [path]
    env.update({'read': fake_read, 'pending_request_paths': pending,
                'asyncio': types.SimpleNamespace(sleep=sleep), 'RecordingPaused': RecordingPaused,
                'AdmissionEnded': Done, 'preserve_first_exception': lambda *a, **kw: 'qualification-source-only',
                '__name__': '_actual_queue_loop_qualification'})
    # Original AST outer dispatch and halt are used. All writes are captured in
    # memory, every session call is simulated; no runtime files are modified.
    for name, node in methods.items():
        ns = dict(env)
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual-C7-method>', 'exec'), ns)
        setattr(Queue, name, ns[name])
    exec(compile(ast.Module(body=[loop], type_ignores=[]), '<actual-C7-run-request-loop>', 'exec'), env)
    captured = io.StringIO()
    with redirect_stdout(captured):
        try: await env['run_request_loop'](q, Session())
        except Done: pass
    if calls != [(3853, 'ck3_auto_turn', {})]:
        print(json.dumps({'diagnostic_halt': writes.get(str(T / 'ROOT-CURRENT-HALT-P37.json')),
                          'diagnostic_audit': writes.get(str(T / 'p37-queue/AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3852.json'))}))
    assert calls == [(3853, 'ck3_auto_turn', {})], calls
    assert relays[0][0].endswith('3851-1-result.json')
    assert q.full_loop_state == state
    assert q.next_sequence == 3854
    assert q.halted['request']['sequence'] == 3853
    assert writes[str(T / 'p37-queue/AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3852.json')]['calls'][0]['sequence'] == 3851
    print(json.dumps({'schema': 'xar.succession3851-prefix-qualification/v1',
       'machine_id': leaf.MACHINE, 'observed_at_utc': datetime.now(timezone.utc).isoformat(),
       'status': 'PASS_SOFTWARE_PREFIX_NOT_LIVE_OR_COMPLETE_HANDOFF',
       'source_package_sha256': leaf.FROZEN_SHA, 'original_handoff_sha256': leaf.SOURCE_SHA,
       'actual_halt_output': captured.getvalue(),
       'actual_outer_dispatch_consume_halt_AST': True, 'original3851_RPC_calls': 0,
       'simulated_following_calls': calls, 'negative_cases_rejected': negatives,
       'original_state_preserved_through_simulated_next_Continue_failure': True,
       'original_source_full_AST_except_two_provider_imports_and_audit_basename': True,
       'runtime_writes_or_real_MCP_calls': 0}, ensure_ascii=False))

asyncio.run(run())
