"""Compose the exact local200 pointer correction; never call Game/MCP."""
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
import sys

from prepare_c3_life_opening_classifier_v1 import pinned
from c4_cold_semantic_pointer_repair200_v1 import PINS


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime-root', type=Path, required=True)
    p.add_argument('--frozen', type=Path, required=True)
    p.add_argument('--output-root', type=Path, required=True)
    args = p.parse_args(); root = args.runtime_root.resolve(strict=True)
    freeze_raw, _ = pinned(root / 'ROOT-FINAL-SDK-FREEZE-P37C4.json', limit=2*1024**2)
    sys.path.insert(0, json.loads(freeze_raw)['source_root'])
    frozen, frozen_pin = pinned(args.frozen, expected='ae3e2e231dd9f5450b3e6e2569f26b3a515c01e0dbfb7c24c5ba69f94fffd613')
    frozen = json.loads(frozen)
    retained = {}; values = {}
    for relative, digest in PINS.items():
        entry = next(x for x in frozen['sources'] if Path(x['original_path']).resolve() == (root / relative).resolve())
        ref = {'path': entry['frozen_path'], 'bytes': entry['bytes'], 'sha256': entry['sha256']}
        raw, _ = pinned(Path(ref['path']), expected=digest)
        retained[relative] = ref; values[relative] = json.loads(raw)
    old, old_pin = pinned(root / 'root_saved_campaign_preflight.py', expected='353c93a6de3896859618b417db223b2f94849fb88313b439c226c004396b2289')
    leaf, leaf_pin = pinned(Path(__file__).with_name('c4_cold_semantic_pointer_repair200_v1.py'))
    tree = ast.parse(old); target = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'recover_zero_rpc_preflight'][-1]
    lines = old.decode().splitlines(keepends=True)
    lines[target.lineno-1] = lines[target.lineno-1].replace('async def recover_zero_rpc_preflight(', 'async def recover_before_c4_pointer200(', 1)
    digest = hashlib.sha256(leaf).hexdigest()
    changed = ''.join(lines) + f'''

async def recover_zero_rpc_preflight(queue, session, request, path, env):
    if request.get("arguments") == {{"repair_kind": "saved61_cold_semantic_pointer198"}}:
        source = Path(__file__).with_name("root_c4_cold_semantic_pointer_repair.py")
        payload = source.read_bytes()
        if len(payload) > 32768 or hashlib.sha256(payload).hexdigest() != {digest!r}:
            raise ValueError("reviewed C4 source-pointer repair differs")
        scope = {{}}
        exec(compile(payload, str(source), "exec"), scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue, session, request, path, env,
            retained={retained!r}, birth_reader=process_birth_filetime)
    return await recover_before_c4_pointer200(queue, session, request, path, env)
'''
    expected = copy.deepcopy(tree)
    [n for n in expected.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'recover_zero_rpc_preflight'][-1].name = 'recover_before_c4_pointer200'
    if [ast.dump(n) for n in expected.body] != [ast.dump(n) for n in ast.parse(changed).body[:-1]]:
        raise AssertionError('Existing recovery guards changed')
    args.output_root.mkdir(parents=True, exist_ok=False)
    control = args.output_root / 'root_saved_campaign_preflight.py'; control.write_text(changed, encoding='utf-8')
    (args.output_root / 'root_c4_cold_semantic_pointer_repair.py').write_bytes(leaf)
    queue_raw, queue_pin = pinned(root / 'root_p37c4_sdk_queue.py', limit=1024**2)
    frame_scope = {}; selected = []
    queue_tree = ast.parse(queue_raw)
    selected.append(next(n for n in queue_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'frame'))
    writes = []
    env = {'N': root, 'Q': root / 'p37-queue', 'OUTBOX': root / 'p37-responses', 'INBOX': root / 'p37-requests',
        'SEMANTIC': 'ck3_take_semantic_snapshot_private_v1', 'CAPABILITIES': 'ck3_get_capabilities',
        'decoded': lambda row: row['result']['structured_content'], 'now': lambda: datetime.now(timezone.utc),
        'atomic': lambda file, value, **kw: writes.append((str(file), copy.deepcopy(value)))}
    for name in ('consume_sequence', 'persist_loop_state'):
        selected.append(next(n for n in ast.walk(queue_tree) if isinstance(n, ast.FunctionDef) and n.name == name))
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(root / 'root_p37c4_sdk_queue.py'), 'exec'), env)
    state = values['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json']; gov = values['p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json']
    sem, cap = [values[f'p37-responses/{s:04}-1-result.json'] for s in (198,199)]
    wrong = str(root / 'p37-responses/0197-1-result.json'); correct = str(root / 'p37-responses/0198-1-result.json')
    class FakeQueue(SimpleNamespace):
        consume_sequence = env['consume_sequence']; persist_loop_state = env['persist_loop_state']
        def guard(self): pass
    def make():
        return FakeQueue(next_sequence=200, halted=None, held_control=None, full_loop_state=copy.deepcopy(state),
            launch={'pid':153556,'creation_filetime':134368602545256920}, initial_frame=state['before'],
            expected_lifecycle_binding=state['actual_saved_checkpoint']['succession_lifecycle'],
            semantic=copy.deepcopy(sem['result']['structured_content']), current_attempt={'request':cap['request'],
                'row':copy.deepcopy(cap),'response':str(root / 'p37-responses/0199-1-result.json')},
            _saved61_cold={'phase':'ready','semantic_response':wrong,'opening':state['before']},
            cold_semantic_response_path=wrong, result_classifier_pin=gov['classifier'],
            governance_result_state=gov['state'], lifestyle_pending_focus=gov['pending_focus'],
            capabilities_verified=True,cold_readiness_verified=True,checkpoint_bootstrap_verified=True)
    from c4_cold_semantic_pointer_repair200_v1 import recover
    request = {'sequence':200,'command':'clear_zero_rpc_preflight_rejection',
        'arguments':{'repair_kind':'saved61_cold_semantic_pointer198'}}
    class NoRPC:
        async def call_tool(self,*a,**kw): raise AssertionError('No RPC allowed')
    q = make(); receipt = asyncio.run(recover(q, NoRPC(), request, env['INBOX']/ '0200-1-result.json', env,
        retained=retained,birth_reader=lambda pid:134368602545256920))
    expected_state = copy.deepcopy(state); expected_state['before_metrics_response'] = correct
    expected_state['cold_session_opening']['semantic_response'] = correct
    if q.full_loop_state != expected_state or q.next_sequence != 201 or len(writes) != 6:
        raise AssertionError('Live source repair changed more than two state pointers')
    if q._saved61_cold['semantic_response'] != correct or q.cold_semantic_response_path != correct:
        raise AssertionError('In-memory cold pointers not corrected')
    negative = []
    for name in ('wrong_birth','pending','unknown_CAP','wrong_semantic','already_corrected'):
        q = make(); birth = lambda pid:134368602545256920
        if name == 'wrong_birth': birth = lambda pid:1
        elif name == 'pending': q.full_loop_state['pending_cycle'] = {'global_turn':75}
        elif name == 'unknown_CAP': q.current_attempt['row']['client_error'] = 'unknown'
        elif name == 'wrong_semantic': q.semantic['date_raw'] += 24
        else: q._saved61_cold['semantic_response'] = correct
        before = len(writes)
        try: asyncio.run(recover(q,NoRPC(),request,env['INBOX']/'0200-1-result.json',env,retained=retained,birth_reader=birth))
        except ValueError:
            if len(writes) != before or q.next_sequence != 200: raise AssertionError('Negative mutated/consumed')
            negative.append(name)
        else: raise AssertionError('Bad source repair accepted')
    proof = {'schema':'xar.c4-cold-source200-software-qualification/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':[frozen_pin,old_pin,leaf_pin,queue_pin],
        'control':{'path':str(control),'bytes':control.stat().st_size,'sha256':hashlib.sha256(control.read_bytes()).hexdigest()},
        'leaf':{'path':str(args.output_root/'root_c4_cold_semantic_pointer_repair.py'),'bytes':len(leaf),'sha256':digest},
        'original_control_AST_unchanged_except_final_name':True,'actual_consume_persist_composition':True,
        'only_two_state_pointer_fields_changed':True,'negative_cases_rejected':negative,'receipt':receipt,
        'new_Game_MCP_Native_calls':0,'runtime_files_mutated':0,'live_adopted':False}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','control':proof['control'],'leaf':proof['leaf']}))


if __name__=='__main__': main()
