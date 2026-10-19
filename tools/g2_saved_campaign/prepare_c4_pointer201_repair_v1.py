"""Qualify actual C4 dispatch/halt/CAP/201 source repair with closed payloads only."""
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
import time
from types import ModuleType, SimpleNamespace

from prepare_c3_life_opening_classifier_v1 import pinned
from c4_cold_semantic_pointer_repair_v1 import PINS
from owner_response_json_once_v1 import prepare_success_response_row_v1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, required=True)
    parser.add_argument('--frozen58', type=Path, required=True)
    parser.add_argument('--frozen60', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args(); root = args.runtime_root.resolve(strict=True)
    freeze, _ = pinned(root / 'ROOT-FINAL-SDK-FREEZE-P37C4.json', limit=2*1024**2)
    sys.path.insert(0, json.loads(freeze)['source_root'])
    inputs = []; retained = {}; values = {}
    frozen58, pin58 = pinned(args.frozen58, expected='ae3e2e231dd9f5450b3e6e2569f26b3a515c01e0dbfb7c24c5ba69f94fffd613')
    frozen60, pin60 = pinned(args.frozen60, expected='b51b9386ab8259707f4b4049801ab542b2c0371a4defffb13a25f7ac8d142e95')
    entries = {Path(x['original_path']).resolve(): {'path':x['frozen_path'],'bytes':x['bytes'],'sha256':x['sha256']}
        for x in json.loads(frozen58)['sources']}
    entries.update({Path(x['source']).resolve():{k:x[k] for k in ('path','bytes','sha256')}
        for x in json.loads(frozen60)['refs']})
    for relative, digest in PINS.items():
        ref = entries[(root / relative).resolve()]
        raw, pin = pinned(Path(ref['path']), expected=digest)
        retained[relative] = ref; values[relative] = json.loads(raw); inputs.append(pin)
    old, old_pin = pinned(root/'root_p37_known_owner_recovery.py',expected='0c39687265aa73b165b173e49a02ff1c2f1f340af74f5dd136b184792a3edd5c')
    leaf, leaf_pin = pinned(Path(__file__).with_name('c4_cold_semantic_pointer_repair_v1.py'))
    tree = ast.parse(old); target = [n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover'][-1]
    lines = old.decode().splitlines(keepends=True)
    lines[target.lineno-1] = lines[target.lineno-1].replace('async def recover(', 'async def recover_before_c4_pointer201(',1)
    digest = hashlib.sha256(leaf).hexdigest()
    changed = ''.join(lines) + f'''

async def recover(queue, session, request, path, env, *, birth_reader=None, lifecycle_executor=None):
    if request.get("arguments") == {{"recovery_kind": "saved61_cold_semantic_pointer198_and_relay_halt"}}:
        source = Path(__file__).with_name("root_c4_cold_semantic_pointer_repair201.py")
        payload = source.read_bytes()
        if len(payload) > 32768 or hashlib.sha256(payload).hexdigest() != {digest!r}:
            raise ValueError("reviewed C4 pointer201 leaf differs")
        scope = {{}}
        exec(compile(payload, str(source), "exec"), scope)
        if birth_reader is None:
            from root_p37_known_pause_recovery_control import process_birth_filetime
            birth_reader = process_birth_filetime
        return await scope["recover"](queue, session, request, path, env,
            retained={retained!r}, birth_reader=birth_reader)
    return await recover_before_c4_pointer201(queue, session, request, path, env,
        birth_reader=birth_reader, lifecycle_executor=lifecycle_executor)
'''
    expected = copy.deepcopy(tree)
    [n for n in expected.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover'][-1].name='recover_before_c4_pointer201'
    if [ast.dump(n) for n in expected.body] != [ast.dump(n) for n in ast.parse(changed).body[:-1]]:
        raise AssertionError('Existing owner recovery AST changed')
    args.output_root.mkdir(parents=True,exist_ok=False)
    control = args.output_root/'root_p37_known_owner_recovery.py'; control.write_text(changed,encoding='utf-8')
    (args.output_root/'root_c4_cold_semantic_pointer_repair201.py').write_bytes(leaf)
    queue, queue_pin = pinned(root/'root_p37c4_sdk_queue.py',expected='9832cbdaeeb1a0add22a97d039aa83eb677853f731abebbd15a61e804f6f3b0f',limit=1024**2)
    qt=ast.parse(queue); selected=[]
    for name in ('frame','decoded','consume_sequence','persist_loop_state','halt_request','run_request_loop'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    selected.append(next(n for n in ast.walk(qt) if isinstance(n,ast.AsyncFunctionDef) and n.name=='call'))
    writes=[]; markers=[]; active={}; responses={}
    class Stop(BaseException): pass
    class AdmissionEnded(RuntimeError): pass
    class RecordingPaused(RuntimeError): pass
    async def sleep(_): raise Stop()
    def atomic(path,value,**kw):
        writes.append((str(path),copy.deepcopy(value)))
        responses[str(path)]=copy.deepcopy(value)
    def read(path,*a):
        if Path(path) == active.get('path'): return copy.deepcopy(active['request'])
        return json.loads(Path(path).read_bytes())
    env={'N':root,'Q':args.output_root/'fixture-queue','INBOX':args.output_root/'fixture-inbox','OUTBOX':args.output_root/'fixture-outbox',
        'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','CAPABILITIES':'ck3_get_capabilities',
        'METRICS':'root_current_runtime_metrics','AUTO':'ck3_auto_turn','INITIAL_CAMERA':'root_initialize_campaign_camera_v1',
        'REPLY_RESERVE':512*1024**2+65536,'Path':Path,'copy':copy,'json':json,'time':time,
        'now':lambda:datetime.now(timezone.utc),'atomic':atomic,'read':read,
        'asyncio':SimpleNamespace(sleep=sleep),'AdmissionEnded':AdmissionEnded,'RecordingPaused':RecordingPaused,
        '_owner_response_success_row_once_v1':prepare_success_response_row_v1,
        'atomic_payload_v1':lambda p,b,**kw:atomic(p,json.loads(b),**kw),
        'display_projection':lambda row,body:{'request':row['request'],'result':{'is_error':False,'structured_content':{'status':'fixture_display'}}},
        'pending_request_paths':lambda *a,**kw:[active['path']],
        'preserve_first_exception':lambda *a,**kw:str(root/'ROOT-FIRST-QUEUE-EXCEPTION-P37C4.json')}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'root_p37c4_sdk_queue.py'),'exec'),env)
    class Queue(SimpleNamespace):
        consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state'];halt_request=env['halt_request'];call=env['call']
        def guard(self,**kw): markers.append('original_guard_entry')
        def check_before(self,*a): pass
        def check_after(self,*a): pass
        def call_budget(self,*a): return 1
    state=values['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json']; gov=values['p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json']
    sem=values['p37-responses/0198-1-result.json']; cap=values['p37-responses/0199-1-result.json']
    wrong=str(root/'p37-responses/0197-1-result.json'); correct=str(root/'p37-responses/0198-1-result.json')
    def make():
        return Queue(next_sequence=199,halted=None,held_control=None,full_loop_state=copy.deepcopy(state),
            launch={'pid':153556,'creation_filetime':134368602545256920},initial_frame=state['before'],
            expected_lifecycle_binding=state['actual_saved_checkpoint']['succession_lifecycle'],
            semantic=copy.deepcopy(sem['result']['structured_content']),current_attempt={'request':sem['request'],'row':copy.deepcopy(sem),
                'response':str(root/'p37-responses/0198-1-result.json')},
            _saved61_cold={'phase':'ready','semantic_response':wrong,'opening':state['before']},
            cold_semantic_response_path=wrong,result_classifier_pin=gov['classifier'],governance_result_state=gov['state'],
            lifestyle_pending_focus=gov['pending_focus'],capabilities_verified=True,cold_readiness_verified=True,checkpoint_bootstrap_verified=True)
    class Session:
        calls=0
        async def call_tool(self,tool,arguments,**kw):
            if tool!=env['CAPABILITIES'] or arguments!={}:raise AssertionError('Only closedCAP payload fixture')
            self.calls+=1;return SimpleNamespace(model_dump=lambda **kw:copy.deepcopy(cap['result']))
    owner=ModuleType('root_p37_known_owner_recovery');owner.__file__=str(control)
    exec(compile(changed,str(control),'exec'),owner.__dict__)
    real_recover=owner.recover
    async def recover_with_birth(q,s,r,p,e):
        return await real_recover(q,s,r,p,e,birth_reader=lambda pid:134368602545256920)
    owner.recover=recover_with_birth
    module_names=('root_p37_known_owner_recovery','root_saved_campaign_preflight','root_p37c4_overlay_relay')
    previous={n:sys.modules.get(n) for n in module_names}
    sys.modules['root_p37_known_owner_recovery']=owner
    relay=ModuleType('root_p37c4_overlay_relay');relay.relay_compact=lambda *a:None;relay.error_projection=lambda r:r
    sys.modules['root_p37c4_overlay_relay']=relay
    old200=args.output_root.parent/'c4-source-pointer-repair-review02'/'root_saved_campaign_preflight.py'
    cached=ModuleType('root_saved_campaign_preflight');cached.__file__=str(old200)
    exec(compile(old200.read_bytes(),str(old200),'exec'),cached.__dict__)
    sys.modules['root_saved_campaign_preflight']=cached
    def run(q,session,request):
        active.update(request=request,path=env['INBOX']/f"{request['sequence']:04d}-1-result.json")
        try:asyncio.run(env['run_request_loop'](q,session))
        except Stop:pass
    try:
        q=make(); q.halt_request(ValueError('Foreign cached decision provider'),sem['request'],env['INBOX']/'0198-1-result.json')
        if q.next_sequence!=199 or q.halted['row']!=sem:raise AssertionError('Actual198 post-read halt mismatch')
        session=Session();asyncio.run(q.call(session,cap['request'],env['INBOX']/'0199-1-result.json'))
        if q.next_sequence!=200 or q.halted['row']!=sem:raise AssertionError('Actual CAP call must preserve198 halt')
        # The fixture CAP row has mock timestamps; the live closed row is independently pinned.
        q.current_attempt={'request':cap['request'],'row':copy.deepcopy(cap),'response':str(root/'p37-responses/0199-1-result.json')}
        run(q,session,{'sequence':200,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':'saved61_cold_semantic_pointer198'}})
        if q.next_sequence!=201 or q.halted['row']!=sem:raise AssertionError('Actual200 dispatcher/halt sequence differs')
        before=len(writes)
        request={'sequence':201,'command':'recover_known_owner_1024','arguments':{'recovery_kind':'saved61_cold_semantic_pointer198_and_relay_halt'}}
        run(q,session,request)
        expected_state=copy.deepcopy(state);expected_state['before_metrics_response']=correct;expected_state['cold_session_opening']['semantic_response']=correct
        if q.full_loop_state!=expected_state or q.next_sequence!=202 or q.halted is not None or q.current_attempt is not None:
            raise AssertionError('Actual201 outer dispatch failed or changed credit')
        result=responses[str(env['OUTBOX']/'0201-1-result.json')]['result']['structured_content']
        if result['status']!='cold_semantic_source_pointer_corrected' or session.calls!=1:raise AssertionError('201 triggered fake MCP')
        new_writes=len(writes)-before
        negatives=[]
        for name in ('foreign_halt','pending','unknown_CAP','held_other_control','wrong_Game_birth'):
            q=make();q.next_sequence=201;q.halted={'request':sem['request'],'row':copy.deepcopy(sem),'response':str(root/'p37-responses/0198-1-result.json')}
            q.halt_cause={'error_type':'ValueError','message':'Foreign cached decision provider'}
            q.current_attempt={'request':cap['request'],'row':copy.deepcopy(cap),'response':str(root/'p37-responses/0199-1-result.json')}
            birth=lambda pid:134368602545256920
            if name=='foreign_halt':q.halt_cause['message']='unknown business result'
            elif name=='pending':q.full_loop_state['pending_cycle']={'global_turn':75}
            elif name=='unknown_CAP':q.current_attempt['row']['client_error']='unknown'
            elif name=='held_other_control':q.held_control='0202-1-result.json'
            else:birth=lambda pid:1
            count=len(writes)
            try:asyncio.run(real_recover(q,session,request,env['INBOX']/'0201-1-result.json',env,birth_reader=birth))
            except ValueError:
                if len(writes)!=count or q.next_sequence!=201:raise AssertionError('Negative mutated/consumed')
                negatives.append(name)
            else:raise AssertionError('Unsafe recovery accepted')
    finally:
        for n, prior in previous.items():
            if prior is None:sys.modules.pop(n,None)
            else:sys.modules[n]=prior
    proof={'schema':'xar.c4-pointer201-actual-dispatch-software/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':[pin58,pin60,old_pin,leaf_pin,queue_pin],
        'control':{'path':str(control),'bytes':control.stat().st_size,'sha256':hashlib.sha256(control.read_bytes()).hexdigest()},
        'leaf':{'path':str(args.output_root/'root_c4_cold_semantic_pointer_repair201.py'),'bytes':len(leaf),'sha256':digest},
        'actual_C4_run_request_loop_and_halt_request':True,'actual_C4_CAP_call':True,
        'actual198_post_read_halt_200_rejection_201_repair_order':True,'201_new_RPC_calls':0,
        'mock_closed_CAP_calls':1,'only_two_state_pointer_fields_changed':True,'201_local_writes':new_writes,
        'negative_cases_rejected':negatives,'runtime_files_mutated':0,'live_adopted':False,'result':result}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','control':proof['control'],'leaf':proof['leaf']}))


if __name__=='__main__':main()
