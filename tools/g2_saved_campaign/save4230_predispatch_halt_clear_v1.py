"""Finite direct-SAVE4230 pre-driver halt clear; no state/SAVE rewrite or RPC."""
from pathlib import Path
import hashlib
import json

MACHINE='xenoamess-full-tower-eb9d2c1186'
KIND='direct_SAVE4230_before_driver_identity_guard'
PACK=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c10b-save4230-failure83')
PINS={
 'FROZEN.json':(10549,'9b726cb9f3526597da17fe1ef25df52f747ab93b1ad89fafb3941550c14a4a9d'),
 'ROOT-CUMULATIVE-LOOP-STATE.json':(5747,'fe6c76f5372989f9fbbeb53ecbda5fda9024f43e0f41d24f60a62b9b7e45c8cf'),
 'ROOT-GOVERNANCE-RESULT-STATE.json':(2353,'435b509829c3ffaa8caf9e4d2bd78540ee53de84a880d5920f317fe39de7c6bd'),
 'ROOT-CURRENT-HALT-P37.json':(683,'e3b876f82eeef49e717e7225e64130b02358366ee1cf64582c98d15787ccbe47'),
 'OS-IDENTITY-ONCE.json':(1641,'4d7e43d914a167e5dc1a7d6951686bca4d661dd5b37d8a143e0d3a1f5881f7eb')}

def require(ok,why):
 if not ok:raise ValueError('SAVE4230 metadata clear denied: '+why)

def exact(path,size,sha):
 raw=Path(path).read_bytes()
 require(len(raw)==size and size<=65536 and hashlib.sha256(raw).hexdigest()==sha,'exact frozen bytes changed')
 return json.loads(raw)

async def recover(queue,session,request,path,env):
 require(request=={'sequence':4231,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':KIND}}
  and Path(path).resolve()==(env['INBOX']/'4231-1-result.json').resolve(),'one exact new local control')
 frozen={name:exact(PACK/name,*pin) for name,pin in PINS.items()}
 require(frozen['FROZEN.json']['machine_id']==MACHINE and queue.next_sequence==4231
  and getattr(queue,'held_control',None) is None,'exact current C10B control boundary')
 state=frozen['ROOT-CUMULATIVE-LOOP-STATE.json'];gov=frozen['ROOT-GOVERNANCE-RESULT-STATE.json']
 require(queue.full_loop_state==state and state['completed_cycles']==2010 and state['before']=={
  'snapshot_id':'native:3262','revision':2,'native_revision':3262,'date_raw':53189040,
  'actor_character_id':40526,'episode_run_id':'native-40526-1bec95182886'}
  and all(state.get(k) is None for k in ('pending_cycle','pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt')),
  'no queue pending; exact same-date played successor state')
 for name in ('ROOT-CUMULATIVE-LOOP-STATE.json','ROOT-GOVERNANCE-RESULT-STATE.json'):
  target=env['Q']/name;raw=target.read_bytes()
  require(len(raw)==PINS[name][0] and hashlib.sha256(raw).hexdigest()==PINS[name][1],'current state/governance bytes differ')
 source=env['OUTBOX']/'4230-1-result.json'
 row=exact(source,557,'304fc226472b4e8334fc21c8ca3e03e79accfbe4dce22eea4c0046b85dc1832d')
 result=row['result'];req=row['request']
 require(req.get('sequence')==4230 and req.get('tool')=='ck3_save_checkpoint' and req.get('arguments')=={'expected_revision':2}
  and result.get('is_error') is True and result.get('result_type')=='complete' and result.get('structured_content') is None
  and len(result.get('content',[]))==1 and result['content'][0].get('text')==
   "Error executing tool ck3_save_checkpoint: cold checkpoint lineage requires the canonical App's internal native projection",
  'only the source-proven before-driver exception')
 require(all(isinstance(x,dict) and x.get('request')==req and x.get('row')==row
  and Path(x.get('response','')).resolve()==source.resolve() for x in (queue.current_attempt,queue.halted))
  and env['read'](env['N']/'ROOT-CURRENT-HALT-P37.json',16384)==frozen['ROOT-CURRENT-HALT-P37.json'],
  'retained original halt/attempt4230')
 require(queue.launch.get('pid')==153556 and queue.launch.get('creation_filetime')==134368602545256920,'actual retained Game tuple')
 src=env['N'].parent.parent/'sdk-v20261019-candidate/src09/xar_autoplayer'
 for relative,sha in (('bridge/successor_ui_app_owner_v1.py','c61ffbdc6afb762946d2e16839a9ac737739255f641d706ee85cc8fbc1d71481'),
  ('successor_ui_checkpoint_lineage_v1.py','f050caf7dd7634e34c095e89269f9ea0523a241e2533bca7671296dd5b14c89c')):
  require(hashlib.sha256((src/relative).read_bytes()).hexdigest()==sha,'audited pre-driver source differs')
 queue.guard(reserve=False)
 marker=env['Q']/'SAVE4230-PREDISPATCH-METADATA-CLEARED.json'
 require(not marker.exists(),'finite control already attempted')
 queue.consume_sequence(request)
 queue.halted=queue.halt_cause=queue.current_attempt=queue.held_control=None
 outcome={'schema':'xar.c10b.direct-save4230-metadata-clear/v1','machine_id':MACHINE,
  'observed_at_utc':env['now']().isoformat(),'status':'source_bound_direct_SAVE_predispatch_halt_cleared',
  'original_SAVE_response':str(source),'original_SAVE_replayed':False,'Game_SDK_Native_RPC_calls':0,
  'completed_cycles':2010,'date_raw':53189040,'next_sequence':queue.next_sequence,
  'loop_and_governance_bytes_unchanged':True,'new_checkpoint_or_ordinary_credit':0,
  'next_SAVE_requires_corrected_C10C_App_warm':True}
 env['atomic'](marker,outcome,limit=16384)
 env['atomic'](env['N']/'ROOT-CURRENT-HALT-P37.json',outcome,replace=True,limit=16384)
 env['atomic'](env['OUTBOX']/Path(path).name,{'request':request,**outcome},limit=16384)
 return outcome
