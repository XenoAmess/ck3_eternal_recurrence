"""Reuse actual C10B outer dispatch for finite direct-SAVE metadata clear."""
import ast,asyncio,copy,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from types import ModuleType,SimpleNamespace
sys.dont_write_bytecode=True
T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
P=T.parent.parent/'p51-fresh1066-v20261019-prepare01/c10b-save4230-failure83'
KIND='direct_SAVE4230_before_driver_identity_guard'
def pin(p):
 b=Path(p).read_bytes();return {'path':str(Path(p).resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
 a.output.mkdir(parents=True,exist_ok=False)
 helper=Path(__file__).with_name('save4230_predispatch_halt_clear_v1.py');hp=pin(helper)
 old=(T/'root_saved_campaign_preflight.py').read_bytes()
 if hashlib.sha256(old).hexdigest()!='9c18bd121786f1ecf6aaeae5c83d4f922a3b5bf1e99236f4be4b1b816043b6a5':raise ValueError('exact unused dispatcher source required')
 suffix=f'''
recover_before4230 = recover_zero_rpc_preflight
async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={{"repair_kind":{KIND!r}}}:
        source=Path(__file__).with_name("root_c10b_save4230_clear.py")
        payload=source.read_bytes()
        if len(payload)!={hp['bytes']} or hashlib.sha256(payload).hexdigest()!={hp['sha256']!r}:
            raise ValueError("reviewed directSAVE4230 helper differs")
        scope={{}}
        exec(compile(payload,str(source),"exec"),scope)
        return await scope["recover"](queue,session,request,path,env)
    return await recover_before4230(queue,session,request,path,env)
'''
 candidate=old+suffix.encode();candidatepath=a.output/'root_saved_campaign_preflight.py';candidatepath.write_bytes(candidate)
 (a.output/'root_c10b_save4230_clear.py').write_bytes(helper.read_bytes())
 module=ModuleType('root_saved_campaign_preflight');module.__file__=str(candidatepath);exec(compile(candidate,str(candidatepath),'exec'),module.__dict__)
 prior=sys.modules.get(module.__name__);sys.modules[module.__name__]=module
 qs=T/'root_p37c10b_sdk_queue.py';tree=ast.parse(qs.read_text(encoding='utf-8-sig'))
 fresh=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FreshQueue')
 funcs=[next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='run_request_loop')]
 funcs += [n for n in fresh.body if isinstance(n,ast.FunctionDef) and n.name in ('consume_sequence','halt_request')]
 state=json.loads((P/'ROOT-CUMULATIVE-LOOP-STATE.json').read_bytes());gov=json.loads((P/'ROOT-GOVERNANCE-RESULT-STATE.json').read_bytes())
 halt=json.loads((P/'ROOT-CURRENT-HALT-P37.json').read_bytes());row=json.loads((T/'p37-responses/4230-1-result.json').read_bytes())
 req={'sequence':4231,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':KIND}}
 results=[]
 class StopFixture(BaseException):pass
 class AdmissionEnded(Exception):pass
 class RecordingPaused(Exception):pass
 try:
  for label in ('exact_direct_SAVE_positive','foreign_pending_rejected'):
   writes={};Q=a.output/label;Q.mkdir()
   for name in ('ROOT-CUMULATIVE-LOOP-STATE.json','ROOT-GOVERNANCE-RESULT-STATE.json'):(Q/name).write_bytes((P/name).read_bytes())
   originalbytes={name:(Q/name).read_bytes() for name in ('ROOT-CUMULATIVE-LOOP-STATE.json','ROOT-GOVERNANCE-RESULT-STATE.json')}
   inbox=T/'p37-requests';outbox=T/'p37-responses';path=inbox/'4231-1-result.json'
   def read(p,*args):
    p=Path(p)
    if p in writes:return copy.deepcopy(writes[p])
    if p==path:return copy.deepcopy(req)
    if p==T/'ROOT-CURRENT-HALT-P37.json':return copy.deepcopy(halt)
    return json.loads(p.read_bytes())
   def atomic(p,v,**kw):
    p=Path(p)
    if p in writes and not kw.get('replace'):raise FileExistsError(p)
    writes[p]=copy.deepcopy(v)
   async def sleep(_):raise StopFixture()
   env={'N':T,'Q':Q,'INBOX':inbox,'OUTBOX':outbox,'read':read,'atomic':atomic,'Path':Path,
    'now':lambda:datetime.now(timezone.utc),'asyncio':SimpleNamespace(sleep=sleep),
    'pending_request_paths':lambda *x,**kw:[path],'AdmissionEnded':AdmissionEnded,'RecordingPaused':RecordingPaused,
    'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','METRICS':'root_current_runtime_metrics',
    'preserve_first_exception':lambda *x,**kw:'fixture-first-exception','print':lambda *x,**kw:None}
   exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),str(qs),'exec'),env)
   class FakeQueue:
    def guard(self,**kw):pass
   FakeQueue.consume_sequence=env['consume_sequence'];FakeQueue.halt_request=env['halt_request']
   q=FakeQueue();q.next_sequence=4231;q.full_loop_state=copy.deepcopy(state)
   if label=='foreign_pending_rejected':q.full_loop_state['pending_checkpoint']={'save_sequence':4230}
   before=copy.deepcopy(q.full_loop_state)
   q.current_attempt={'request':row['request'],'row':row,'response':str(outbox/'4230-1-result.json')}
   q.halted=copy.deepcopy(q.current_attempt);q.halt_cause={};q.held_control=None
   q.launch={'pid':153556,'creation_filetime':134368602545256920}
   try:asyncio.run(env['run_request_loop'](q,object()))
   except StopFixture:pass
   result=writes[outbox/'4231-1-result.json']
   assert q.full_loop_state==before and all((Q/name).read_bytes()==b for name,b in originalbytes.items())
   if label=='exact_direct_SAVE_positive':assert q.halted is None and result['status']=='source_bound_direct_SAVE_predispatch_halt_cleared' and q.next_sequence==4232
   else:assert q.halted is not None and 'denied' in result['client_error']
   results.append({'case':label,'PASS':True,'actual_outer_consume_halt':True,'state_governance_raw_bytes_identical':True,'RPC_calls':0})
 finally:
  if prior is None:sys.modules.pop(module.__name__,None)
  else:sys.modules[module.__name__]=prior
 receipt={'schema':'xar.c10b.SAVE4230-outer-qualification/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
  'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'SOFTWARE_ONLY_2_CASES_PASS','helper':hp,
  'candidate_dispatcher':pin(candidatepath),'queue_source':pin(qs),'packet':pin(P/'FROZEN.json'),'results':results,
  'process_storage_guard':'fixture-only; actual source-bound small receipts use original bytes','live_runtime_writes':0,'Game_SDK_Native_calls':0}
 (a.output/'QUALIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(pin(a.output/'QUALIFICATION.json')))
if __name__=='__main__':main()
