"""Detached exact-F93 fixture; no runtime writes, Game query or process API."""
import ast,asyncio,copy,hashlib,importlib.util,json,sys,types
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

P=Path(__file__).with_name('c17_alliance9421_not_sent_v1.py')
s=importlib.util.spec_from_file_location('alliance9421_candidate',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NOW=datetime.now(timezone.utc)
QUEUE=m.T/'root_p37c17_sdk_queue.py'
RAW=QUEUE.read_bytes();assert hashlib.sha256(RAW).hexdigest()==m.QUEUE_SHA
TREE=ast.parse(RAW)
REDUCER=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='frame')
ENTRY=next(n for c in TREE.body if isinstance(c,ast.ClassDef) and c.name=='ColdReadyQueue'
 for n in c.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover_partial_life_advance')
# Execute only the actual pure reducer and original lazy-entry method. Its env
# expression is unchanged; fixture supplies no extra keys and no fake reducer.
SCOPE={'__file__':str(QUEUE),'Path':Path,'hashlib':hashlib}
MODULE=ast.Module(body=[REDUCER,ast.ClassDef(name='ActualEntry',bases=[],keywords=[],body=[ENTRY],decorator_list=[])],type_ignores=[])
exec(compile(ast.fix_missing_locations(MODULE),str(QUEUE),'exec'),SCOPE)
ActualEntry=SCOPE['ActualEntry']
FREEZE=json.loads((m.T/'ROOT-FINAL-SDK-FREEZE-P37C17.json').read_bytes())
sys.path.insert(0,FREEZE['source_root'])

def fixture(*,bad_date=False,failed_sem=False):
 v=m.evidence();state=copy.deepcopy(v['state']);gov=copy.deepcopy(v['governance']);store={};writes=[];calls=[]
 launch=json.loads((m.T/'ROOT-ACTUAL-GAME-LAUNCH-C16.json').read_bytes())
 body={'map_ready':True,'paused':True,'one_life_terminal':False,'played_character':{'character_id':40526,'alive':True},
  'episode_run_id':'native-40526-1bec95182886','snapshot_id':'native:2669','native_revision':2669,'revision':884,
  'date_raw':53244000+(24 if bad_date else 0),'campaign_goal':copy.deepcopy(state['campaign_goal_anchor']),
  'succession_lifecycle':copy.deepcopy(state['actual_saved_checkpoint']['succession_lifecycle']),
  'diagnostics':{'bridge_pid':30852,'pipe_name':launch['pipe'],'connection_generation':2,'hello':{'pid':30852,
   'connection_generation':2,'ck3_build_match':True,'game_adapter_status':'ready','game_adapter_id':'ck3-1.20.0.4-msvc-x64'}}}
 def read(path,*args):
  path=Path(path)
  return copy.deepcopy(store[path] if path in store else json.loads(path.read_bytes()))
 def atomic(path,value,**kwargs):store[Path(path)]=copy.deepcopy(value);writes.append(str(path))
 def digest(path):
  path=Path(path)
  return hashlib.sha256(json.dumps(store[path],sort_keys=True).encode()).hexdigest() if path in store else hashlib.sha256(path.read_bytes()).hexdigest()
 def decoded(row):
  r=row['result']
  if r['is_error']:raise ValueError('fixture SEM rejected')
  return r['structured_content']
 class Queue(ActualEntry):
  def __init__(self):
   self.launch=launch;self.job={'game_creation_filetime':134368995759027619};self.next_sequence=9422
   self.full_loop_state=copy.deepcopy(state);self.checkpoint_bootstrap_verified=True
   self.expected_lifecycle_binding=copy.deepcopy(body['succession_lifecycle'])
   self.halted={'request':v['auto9421']['request'],'row':v['auto9421'],'response':str(m.T/'p37-responses/9421-1-result.json')}
   self.current_attempt=self.halted;self.held_control='9400-1-result.json'
  def guard(self):pass
  def call_budget(self,tool):return 1
  def consume_sequence(self,r):
   if r['sequence']!=self.next_sequence:raise ValueError('sequence differs')
   self.next_sequence+=1;return r['sequence']
  def persist_loop_state(self):
   atomic(m.T/'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json',self.full_loop_state)
   atomic(m.T/'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json',{**gov,'pending_cycle':self.full_loop_state['pending_cycle']})
 class Session:
  async def call_tool(self,tool,args,**kw):
   calls.append((tool,args))
   if tool!=m.SEM or args!={}:raise AssertionError('unexpected Native/business tool')
   return types.SimpleNamespace(model_dump=lambda **kw:{'is_error':failed_sem,'result_type':'complete','structured_content':body})
 SCOPE.update(Q=m.T/'p37-queue',OUTBOX=m.T/'p37-responses',INBOX=m.T/'p37-requests',read=read,atomic=atomic,
  now=lambda:NOW,SEMANTIC=m.SEM,REPLY_RESERVE=262144,decoded=decoded)
 # Capture exactly what the real method constructs; its only fixture seam is
 # the imported dispatcher, where the OS birth reader is explicitly injected.
 captured=[]
 async def dispatch(q,session,request,path,env):
  captured.append(env)
  assert set(env)=={'INBOX','OUTBOX','Q','SEMANTIC','REPLY_RESERVE','atomic','read','decoded','now','sha256'}
  return await m.recover(q,session,request,path,env,birth_reader=lambda p:134368995759027619)
 dispatcher=types.ModuleType('root_p37_known_pause_recovery_control');dispatcher.recover=dispatch
 sys.modules[dispatcher.__name__]=dispatcher
 env={'Q':m.T/'p37-queue','OUTBOX':m.T/'p37-responses','INBOX':m.T/'p37-requests','read':read,'atomic':atomic,
  'now':lambda:NOW,'sha256':digest,'SEMANTIC':m.SEM,'REPLY_RESERVE':262144,'decoded':decoded}
 request={'sequence':9422,'command':'recover_partial_life_advance','arguments':{'recovery_kind':m.KIND}}
 return Queue(),Session(),request,env,state,gov,store,calls

def main(output):
 dispatch=(m.T/'root_p37_known_pause_recovery_control.py').read_bytes();sources=m.build_sources(dispatch)
 relay=types.ModuleType('root_p37c16_overlay_relay');relay.relay_compact=lambda *a:None;relay.error_projection=lambda r:r
 sys.modules['root_p37c16_overlay_relay']=relay
 q,s,r,e,b,g,store,calls=fixture();read_bytes=Path.read_bytes
 # Original env's inline sha256 reads the in-memory atomic output through the
 # detached fixture filesystem; immutable input reads keep their real bytes.
 with patch.object(Path,'read_bytes',lambda path:json.dumps(store[path],sort_keys=True).encode() if path in store else read_bytes(path)):
  result=asyncio.run(q.recover_partial_life_advance(s,r,e['INBOX']/'9422-1-result.json'))
 expected=copy.deepcopy(b);expected.update(before=q.full_loop_state['before'],before_metrics_response=str(e['OUTBOX']/'9423-1-result.json'),pending_cycle=None)
 assert q.full_loop_state==expected and calls==[(m.SEM,{})] and q.next_sequence==9424 and q.halted is None
 assert store[e['Q']/'ROOT-GOVERNANCE-RESULT-STATE.json']=={**g,'pending_cycle':None}
 assert result['ordinary_cycle_credit']==result['new_alliance_native_queries']==result['new_world_actions']==0
 for mode in ('wrong_birth','wrong_date','SEM_error'):
  q,s,r,e,b,g,store,calls=fixture(bad_date=mode=='wrong_date',failed_sem=mode=='SEM_error')
  try:asyncio.run(m.recover(q,s,r,e['INBOX']/'9422-1-result.json',e,birth_reader=lambda p:1 if mode=='wrong_birth' else 134368995759027619))
  except ValueError:pass
  else:raise AssertionError(mode+' accepted')
  assert q.full_loop_state==b and q.halted is not None and len(calls)==(0 if mode=='wrong_birth' else 1)
 bad=copy.deepcopy(m.evidence()['family']);bad['resolved']['source_pending']['recipient_character_id']=40695
 try:m.material_tuple(bad)
 except ValueError:pass
 else:raise AssertionError('nonself source accepted')
 proof={'machine_id':m.MACHINE,'observed_at_utc':NOW.isoformat(),'status':'SOURCE_QUALIFIED_WAITING_ROOT_RELEASE',
  'producer':{'path':str(P.resolve()),'bytes':P.stat().st_size,'sha256':hashlib.sha256(P.read_bytes()).hexdigest()},
  'qualifier':{'path':str(Path(__file__).resolve()),'bytes':Path(__file__).stat().st_size,'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
  'sources':{name:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in sources.items()},
   'supersedes_failed_qualification':{'path':'_runtime/c17-alliance9421-qualified93.json','sha256':'0b9262e94e40492b3c9da73a3caf4b9d78f9fb900722089a0ea3dab43aa1d714','reason':'old fixture injected frame missing from real Queue recovery env; no runtime install/RPC'},
   'actual_entry_env_keys':sorted(e),'actual_frame_reducer_ast_sha256':hashlib.sha256(ast.dump(REDUCER,include_attributes=False).encode()).hexdigest(),
   'checks':['actual closed F93 guards','actual Queue recovery method/env expression and actual frame reducer with frozen SDK lifecycle normalizer; one SEM positive','wrong birth before RPC reject','wrong date/SEM error retain intent','nonself tuple reject','original dispatcher inverse bytes'],
  'D_writes':0,'Game_Native_MCP_Task_calls':0,'fixture_calls_are_in_memory_only':True}
 with output.open('x',encoding='utf8',newline='\n') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(json.dumps(proof))

if __name__=='__main__':main(Path(sys.argv[1]))
