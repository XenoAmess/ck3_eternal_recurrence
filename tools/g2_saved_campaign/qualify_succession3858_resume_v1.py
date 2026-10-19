"""Actual outer partial-control path, six closed prefix results, simulated AUTO."""
import ast
import asyncio
import copy
import importlib.util
import io
import json
import sys
sys.dont_write_bytecode = True
import types
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

REPO = Path('Z:/ck3_mod_rewrite')
N = Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T = N / 'robert30-v20261019-campaign01/runtime'
F = N / 'p51-fresh1066-v20261019-prepare01/c7-succession3858-ui-failure78'
sys.path[:0] = [str(REPO), str(N / 'sdk-v20261019-candidate/src06'), str(T)]
spec = importlib.util.spec_from_file_location('tested3858', REPO / 'tools/g2_saved_campaign/succession3858_pending_ui_resume_v1.py')
leaf = importlib.util.module_from_spec(spec); spec.loader.exec_module(leaf)
original_checked = leaf.checked
ui_bytes = (REPO / 'tools/g2_saved_campaign/p51_resident_successor_adoption_v1.py').read_bytes()
def checked(path, digest):
    if Path(path) == T / 'root_p37_succession3858_ui_contract.py':
        assert __import__('hashlib').sha256(ui_bytes).hexdigest() == digest
        return ui_bytes
    return original_checked(path, digest)
leaf.checked = checked
read = lambda p, *unused: json.loads(Path(p).read_text(encoding='utf-8-sig'))
state = read(F / 'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json')
failed = read(F / 'p37-responses/3858-1-result.json')
first = read(leaf.OLD / 'p37-responses/3851-1-result.json')['result']['structured_content']
request = {'sequence': 3859, 'command': 'recover_partial_life_advance',
           'arguments': {'recovery_kind': 'ordinary_campaign_succession', 'repair_kind': leaf.KIND}}
path = T / 'p37-requests/3859-1-result.json'
class Done(Exception): pass
class RecordingPaused(Exception): pass
class Queue:
    def __init__(self):
        self.next_sequence = 3859; self.held_control = None
        self.full_loop_state = copy.deepcopy(state)
        self.halted = {'request': failed['request'], 'row': failed, 'response': str(T / 'p37-responses/3858-1-result.json')}
        self.current_attempt = copy.deepcopy(self.halted)
        self.launch = {'pid': 153556, 'pipe': first['diagnostics']['pipe_name']}
        self.job = {'game_creation_filetime': 134368602545256920}
        self.expected_lifecycle_binding = first['succession_lifecycle']
        self.last_guard_observation = {}; self.halt_cause = None
    def guard(self, **kwargs): pass
    def call_budget(self, tool): return 1
    def persist_loop_state(self): raise AssertionError('prefix fixture cannot claim full tail commit')
def decoded(row):
    if row.get('client_error'): raise ValueError(row['client_error'])
    return row['result']['structured_content']

async def run():
    writes, relays, calls = {}, [], []
    def atomic(p, value, **kwargs): writes[str(p)] = copy.deepcopy(value)
    env = {'N': T, 'Q': T / 'p37-queue', 'INBOX': T / 'p37-requests', 'OUTBOX': T / 'p37-responses',
           'SEMANTIC': 'ck3_take_semantic_snapshot_private_v1', 'REPLY_RESERVE': 262144,
           'atomic': atomic, 'decoded': decoded, 'now': lambda: datetime.now(timezone.utc),
           'read': lambda p,*a: request if Path(p) == path else read(p,*a),
           'display_projection': lambda r,b: {'sequence': r['request']['sequence']}}
    def pending(*args, **kwargs):
        return [] if kwargs.get('held_control') == path.name else [path]
    env['pending_request_paths'] = pending
    bad = Queue(); bad.halted['response'] = 'wrong-original'
    try: leaf.validate(bad, request, path, env)
    except ValueError: pass
    else: raise AssertionError('wrong failed original was accepted')
    q = Queue()
    leaf.validate(q, request, path, env)
    relay = types.ModuleType('root_p37c6_overlay_relay')
    relay.relay_compact = lambda p,v: relays.append(str(p))
    relay.error_projection = lambda r: {'error': r.get('client_error')}
    sys.modules[relay.__name__] = relay
    pause = types.ModuleType('root_p37_known_pause_recovery_control')
    pause.process_birth_filetime = lambda pid: 134368602545256920
    pause_tree = ast.parse((T / 'root_p37_known_pause_recovery_control.py').read_text(encoding='utf-8-sig'))
    pause_node = [n for n in pause_tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'recover'][-1]
    exec(compile(ast.Module(body=[pause_node], type_ignores=[]), '<original-cached-partial-dispatch>', 'exec'), pause.__dict__)
    sys.modules[pause.__name__] = pause
    installed = types.ModuleType('root_p37_succession3858_resume'); installed.recover = leaf.recover
    sys.modules[installed.__name__] = installed
    succession = types.ModuleType('root_p37_succession_recovery')
    exec(compile(leaf.transform_unused_succession((T / 'root_p37_succession_recovery.py').read_bytes()),
                 '<actual-unused-succession-plus-finite-branch>', 'exec'), succession.__dict__)
    sys.modules[succession.__name__] = succession
    tree = ast.parse((T / 'root_p37c7_sdk_queue.py').read_text(encoding='utf-8-sig'))
    methods = {}
    partial = []
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name in {'consume_sequence', 'halt_request'}:
                methods.setdefault(node.name, node)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == 'recover_partial_life_advance': partial.append(node)
    async def sleep(_): raise Done()
    env.update({'asyncio': types.SimpleNamespace(sleep=sleep), 'AdmissionEnded': Done,
                'RecordingPaused': RecordingPaused,
                'preserve_first_exception': lambda *a,**kw: 'software-only-original-halt', '__name__': '_actual_C7_source'})
    for name,node in [*methods.items(), ('recover_partial_life_advance', partial[-1])]:
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(T / 'root_p37c7_sdk_queue.py'), 'exec'), env)
        setattr(Queue, name, env[name])
    outer = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'run_request_loop')
    exec(compile(ast.Module(body=[outer], type_ignores=[]), str(T / 'root_p37c7_sdk_queue.py'), 'exec'), env)
    class Session:
        async def call_tool(self, tool, args, **kwargs):
            calls.append([q.next_sequence - 1, tool, args])
            raise RuntimeError('SIMULATED_NEW_UI_AUTO_NOT_EXECUTED')
    captured = io.StringIO()
    with redirect_stdout(captured):
        try: await env['run_request_loop'](q, Session())
        except Done: pass
    if calls != [[3860, 'ck3_auto_turn', {}]]:
        print(json.dumps({'halt': writes.get(str(T / 'ROOT-CURRENT-HALT-P37.json'))}))
    assert calls == [[3860, 'ck3_auto_turn', {}]], calls
    assert q.halted['request']['sequence'] == 3860
    assert q.full_loop_state == state and q.next_sequence == 3861
    audit = writes[str(T / 'p37-queue/AUTOMATIC-SUCCESSION-HANDOFF-001839-RESUME3859.json')]
    assert [r['sequence'] for r in audit['calls'][:-1]] == list(leaf.PREFIX)
    assert all(r['new_RPC_calls'] == 0 for r in audit['calls'][:-1])
    assert not any(p.endswith(('3851-1-result.json','3853-1-result.json','3858-1-result.json')) for p in relays)
    print(json.dumps({'schema': 'xar.succession3858-prefix-qualification/v1', 'machine_id': leaf.MACHINE,
       'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'PASS_SOFTWARE_PREFIX_NOT_LIVE_OR_COMPLETE_TAIL',
       'actual_outer_partial_small_env_and_cached_dynamic_dispatch_AST': True,
       'original_prefix_supplied_zero_RPC': list(leaf.PREFIX), 'original_prefix_display_replay': False,
       'next_simulated_unique_call': calls, 'old_directClose_or_logicalContinue_replayed': False,
       'new_unknown_retained': 3860, 'original1839_state_preserved': True,
       'wrong_failed_original_rejected': True, 'actual_Game_RPC_or_runtime_writes': 0}))

asyncio.run(run())
