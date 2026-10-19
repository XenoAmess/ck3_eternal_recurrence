"""Observe one exact Python-rejected alliance query; no query/proposal replay."""
from __future__ import annotations
import ast,copy,hashlib,json,time
from pathlib import Path

MACHINE='xenoamess-full-tower-eb9d2c1186'
ROOT=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T=ROOT/'robert30-v20261019-campaign01/runtime'
F=ROOT/'p51-fresh1066-v20261019-prepare01/c17-alliance9421-failure93'
KIND='c17_alliance9421_native_query_not_sent'
ENTRY='root_p37c17_alliance9421_not_sent.py'
SCHEMA='xar.C17-alliance9421-native-query-not-sent/v1'
STEP='query-observed-first-heir-marriage-alliance-result-v1-private'
SEM='ck3_take_semantic_snapshot_private_v1'
ERROR='Error executing tool ck3_auto_turn: alliance result lacks a bound material proposal'
DISPATCH_SHA='6516da06c567527cb724aefac52337dc3ff33ba86dd49f32f04fb52dfa1286b5'
FROZEN_SHA='8840f19efd6143fbbf805219cec96320495ea77f9e3e2e276471fa198bd7c3e5'
UNUSED_SHA='06002d91957f12292af3f0dc6a6ba409f0d48d49baae4ed8b095072953c3d55c'
QUEUE_SHA='fda55ef263bb5b2a16156ee7b256cc7c5242f400a1c022a67d2f66b9d15e1c73'
TRANSPORT_SHA='4c338e2ed6317dc4c9c3db70e4df80b0fc6581ff65b2f3d441301030f40b3c05'
FRAME_KEYS=('snapshot_id','revision','native_revision','date_raw','actor_character_id','episode_run_id')

def require(ok,why):
 if not ok:raise ValueError('C17 alliance9421 not-sent recovery denied: '+why)

def checked(path,digest,size=None):
 path=Path(path)
 with path.open('rb') as f:raw=f.read(262145)
 require(len(raw)<=262144 and (size is None or len(raw)==size) and hashlib.sha256(raw).hexdigest()==digest,'immutable source changed: '+str(path))
 return json.loads(raw)

def evidence():
 index=checked(F/'FROZEN.json',FROZEN_SHA,8203)
 require(index['machine_id']==MACHINE,'machine source differs')
 values={}
 for name in ('auto9421','plan9421','before9420','state','governance','family'):
  refs=index['sources'][name];r=refs['frozen'];value=checked(r['path'],r['sha256'],r['bytes'])
  original=refs['original'];require(checked(original['path'],original['sha256'],original['bytes'])==value,'current exact source differs: '+name)
  values[name]=value
 unused=checked(F/'CONTINUITY-AND-UNUSED-CONTROL-PROOF.json',UNUSED_SHA,7222)
 require(unused['machine_id']==MACHINE and unused['bounded_sequence_range']==[8892,9421]
  and unused['request_header_count']==530 and unused['recovery_controls']==[],'lazy entry not unused')
 return values

def material_tuple(family):
 resolved=family.get('resolved');p=resolved.get('source_pending') if isinstance(resolved,dict) else None
 require(family.get('schema')=='xar.ck3.first-heir-marriage-formal.v1' and family.get('pending') is None
  and isinstance(p,dict) and p.get('schema')=='xar.ck3.observed-first-heir-marriage-private-action.v1'
  and resolved.get('status')=='marriage' and resolved.get('material_result') is True
  and resolved.get('episode_run_id')=='native-40526-1bec95182886'
  and p.get('played_character_id')==p.get('recipient_character_id')==40526
  and p.get('heir_character_id')==resolved.get('heir_character_id')==40695
  and p.get('candidate_character_id')==resolved.get('candidate_character_id')==76700
  and p.get('preproposal_played_has_recipient_alliance') is None
  and p.get('preproposal_realm_alliance_attempt_if_accepted') is False,
  'only exact current material pair with self-recipient may be reconciled')
 return dict(played_character_id=40526,heir_character_id=40695,candidate_character_id=76700,
  recipient_character_id=40526,status='marriage',material_result=True)

def qualify(queue,request,path,env,birth_reader):
 require(request=={'sequence':9422,'command':'recover_partial_life_advance','arguments':{'recovery_kind':KIND}}
  and path==env['INBOX']/'9422-1-result.json' and queue.next_sequence==9422,'one unused exact control9422 required')
 require(env['Q']==T/'p37-queue' and env['OUTBOX']==T/'p37-responses','actual namespace differs')
 require(queue.launch.get('pid')==30852 and queue.launch.get('creation_filetime')==134368995759027619
  and queue.job.get('game_creation_filetime')==134368995759027619
  and birth_reader(30852)==134368995759027619,'exact Game generation differs')
 require(hashlib.sha256((T/'root_p37c17_sdk_queue.py').read_bytes()).hexdigest()==QUEUE_SHA,'actual Queue changed')
 freeze=env['read'](T/'ROOT-FINAL-SDK-FREEZE-P37C17.json',2*1024**2)
 source=Path(freeze['source_root'])/'xar_autoplayer/bridge/observed_heir_marriage_private_action_v1.py'
 require(freeze['business_source_commit']=='04a87c1ec6fd4a0d59e6237af3158ce797c7cbe4'
  and hashlib.sha256(source.read_bytes()).hexdigest()==TRANSPORT_SHA,'source not the exact pre-Native guard')
 v=evidence();state=v['state'];row=v['auto9421'];plan=v['plan9421'];gov=v['governance']
 require(queue.full_loop_state==state and env['read'](env['Q']/'ROOT-CUMULATIVE-LOOP-STATE.json')==state
  and env['read'](env['Q']/'ROOT-GOVERNANCE-RESULT-STATE.json')==gov,'state/governance differs')
 original=queue.halted;pending=state.get('pending_cycle');wrapper=row['result']
 require(isinstance(original,dict) and original.get('request')==row['request'] and original.get('row')==row
  and Path(original.get('response',''))==env['OUTBOX']/'9421-1-result.json'
  and row['request']['sequence']==9421 and row['request']['tool']=='ck3_auto_turn' and row['request']['arguments']=={}
  and row.get('client_error') is None and wrapper['is_error'] is True and wrapper['result_type']=='complete'
  and wrapper['structured_content'] is None and len(wrapper['content'])==1 and wrapper['content'][0]['type']=='text'
  and wrapper['content'][0]['text']==ERROR,'original completed Python rejection differs')
 selected=plan['result']['structured_content']
 require(plan['game_pid']==30852 and plan['game_creation_date']==queue.launch['creation_date']
  and plan['request']['parent_sequence']==9421 and selected['selected_step']==selected['plan']['selected_step']==STEP
  and selected['plan']['phase']=='first_heir_marriage_actual_alliance_read'
  and selected['snapshot_id']=='native:2668' and selected['revision']==883,'original actual callback differs')
 require(state['completed_cycles']==4262 and isinstance(pending,dict) and pending['global_turn']==4263
  and pending['auto_sequence']==9421 and pending['stage']=='auto_unsettled' and pending['before']==state['before']
  and state['before']['date_raw']==53244000 and state['before']['actor_character_id']==40526
  and state['before']['native_revision']==2668 and state['before']['revision']==883
  and state['before']['episode_run_id']=='native-40526-1bec95182886'
  and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt'))
  and gov['pending_cycle']==pending and queue.checkpoint_bootstrap_verified is True,'one exact unresolved no-query intent required')
 return v,material_tuple(v['family'])

def checked_frame(body,queue,env):
 old=queue.full_loop_state;before=old['before'];d=body.get('diagnostics') or {};h=d.get('hello') or {}
 require(body.get('paused') is True and body.get('map_ready') is True and body.get('one_life_terminal') is False
  and (body.get('played_character') or {}).get('alive') is True
  and d.get('bridge_pid')==h.get('pid')==30852 and d.get('pipe_name')==queue.launch['pipe']
  and d.get('connection_generation')==h.get('connection_generation')==2
  and h.get('ck3_build_match') is True and h.get('game_adapter_status')=='ready'
  and h.get('game_adapter_id')=='ck3-1.20.0.4-msvc-x64','fresh same-connection paused map unproven')
 # ColdReadyQueue's real recovery env does not export frame. Reuse the pure
 # reducer already owned by that exact pinned Queue module, without importing
 # or executing another Queue/main and without extending the caller env.
 scope=queue.recover_partial_life_advance.__func__.__globals__;reducer=scope.get('frame')
 require(Path(scope.get('__file__','')).resolve()==(T/'root_p37c17_sdk_queue.py').resolve()
  and callable(reducer) and reducer.__globals__ is scope,'actual Queue frame reducer unavailable')
 frame=reducer(body,semantic=True,expected_lifecycle=queue.expected_lifecycle_binding)
 require(all(frame[k]==before[k] for k in ('date_raw','actor_character_id','episode_run_id'))
  and frame['native_revision']>=2668 and frame['revision']>=883
  and isinstance(old.get('campaign_goal_anchor'),dict) and body.get('campaign_goal')==old['campaign_goal_anchor'],
  'fresh exact date/actor/episode/Native/goal differs')
 return {k:frame[k] for k in FRAME_KEYS}

async def recover(queue,session,request,path,env,*,birth_reader):
 from root_p37c16_overlay_relay import relay_compact,error_projection
 v,pair=qualify(queue,request,path,env,birth_reader);state=queue.full_loop_state
 audit_path=env['Q']/'ALLIANCE9421-NATIVE-QUERY-NOT-SENT-9422.json'
 require(not audit_path.exists(),'finite recovery already attempted')
 audit=dict(schema=SCHEMA,machine_id=MACHINE,utc=env['now']().isoformat(),original_auto=9421,
  original_pending=copy.deepcopy(state['pending_cycle']),source_tuple=pair,status='attempting',ordinary_cycle_credit=0,
  new_alliance_native_queries=0,new_world_actions=0,new_pause_submissions=0,original_actions_replayed=False,
  family_bytes_unchanged_claimed=False,calls=[])
 def save():env['atomic'](audit_path,audit,replace=True,limit=16384)
 def guard():
  queue.guard();require(birth_reader(30852)==134368995759027619,'Game birth changed')
 guard();queue.consume_sequence(request);queue.held_control=path.name
 env['atomic'](env['Q']/'INFLIGHT-9422.json',{'request':request,'control_only':True,'replay_allowed':False},limit=16384);save()
 try:
  guard();sequence=queue.next_sequence;require(sequence==9423,'only one new SEM9423 may be used')
  child={'sequence':sequence,'tool':SEM,'arguments':{},'source':SCHEMA};inbox=env['INBOX']/'9423-1-result.json';response=env['OUTBOX']/inbox.name
  require(not inbox.exists() and not response.exists(),'SEM already attempted')
  env['atomic'](inbox,child,limit=16384);queue.consume_sequence(child)
  context={**child,'request_file':str(inbox),'at_utc':env['now']().isoformat(),'replay_allowed':False}
  env['atomic'](T/'CURRENT-REQUEST-P37.json',context,replace=True,limit=16384)
  env['atomic'](env['Q']/'INFLIGHT-9423.json',context,limit=16384)
  env['atomic'](env['Q']/'9423-before-action.json',context,limit=16384)
  audit['calls'].append({'sequence':9423,'tool':SEM,'status':'attempted'});save()
  started,mono=env['now']().isoformat(),time.monotonic()
  try:
   reply=await session.call_tool(SEM,{},read_timeout_seconds=queue.call_budget(SEM))
   row={'request':child,'started_at_utc':started,'ended_at_utc':env['now']().isoformat(),
    'elapsed_seconds':time.monotonic()-mono,'result':reply.model_dump(mode='json')}
  except Exception as error:
   row={'request':child,'started_at_utc':started,'ended_at_utc':env['now']().isoformat(),
    'elapsed_seconds':time.monotonic()-mono,'client_error':repr(error),'replay_allowed':False}
  env['atomic'](response,row,limit=env['REPLY_RESERVE']);audit['calls'][0].update(status='received',response=str(response),sha256=env['sha256'](response));save()
  try:body=env['decoded'](row)
  except Exception:
   relay_compact(response,error_projection(row));raise
  actual=checked_frame(body,queue,env);guard()
  family=v['family'];current_family=evidence()['family'];require(current_family==family,'family ledger changed during observation')
  relay_compact(response,{'request':child,'ended_at_utc':row['ended_at_utc'],
   'source':'exact alliance9421 native-query-not-sent fresh semantic; zero action credit',
   'result':{'is_error':False,'structured_content':{k:body[k] for k in ('snapshot_id','revision','native_revision','date_raw','paused','map_ready') if k in body}}})
  env['atomic'](env['Q']/'9423-after-result.json',{'request':str(inbox),'response':str(response),'tool':SEM,'actual_status':body.get('status')},limit=16384)
  changed=copy.deepcopy(state);changed.update(before=actual,before_metrics_response=str(response),pending_cycle=None)
  # All dirty/calendar/SAVE/count/goal/material fields stay exact; only intent and fresh frame move.
  audit.update(status='fresh_paused_observation_verified',fresh_frame=actual,final_semantic_response=str(response),family_bytes_unchanged_claimed=True,mutation_attempted=True);save()
  queue.full_loop_state=changed;queue.persist_loop_state()
  expected_gov={**v['governance'],'pending_cycle':None}
  require(env['read'](env['Q']/'ROOT-GOVERNANCE-RESULT-STATE.json')==expected_gov,'governance changed beyond wrapper intent')
  queue.semantic=queue.reinforcement_semantic=body;queue.reinforcement_frame=actual;queue.reinforcement_frame_response=str(response)
  result={k:audit[k] for k in ('schema','machine_id','ordinary_cycle_credit','new_alliance_native_queries','new_world_actions','new_pause_submissions','original_actions_replayed')}
  result.update(status='native_query_not_sent_observed_pending_cleared',completed_cycles=4262,pending_cycle=None,
   new_MCP_semantic_calls=1,normal_sdk_maintenance_required=True,new_auto_admitted=False,audit=str(audit_path),final_semantic_response=str(response))
  env['atomic'](env['OUTBOX']/path.name,{'request':request,'result':{'is_error':False,'structured_content':result}},limit=16384)
  queue.halted=queue.current_attempt=queue.held_control=None
  env['atomic'](T/'ROOT-CURRENT-HALT-P37.json',result,replace=True,limit=16384)
  audit['status']='completed';save();return result
 except Exception as error:
  audit.update(status='failed_retained',error_type=type(error).__name__,error=str(error)[:1024]);save();raise

def build_sources(dispatch):
 require(hashlib.sha256(dispatch).hexdigest()==DISPATCH_SHA,'unused dispatcher source differs')
 old=dispatch.decode();anchor='async def recover(queue, session, request, path, env, *, birth_reader=process_birth_filetime):\n'
 addition=("    if request.get('arguments') == {'recovery_kind': '"+KIND+"'}:\n"
  "        from root_p37c17_alliance9421_not_sent import recover as recover9421\n"
  "        return await recover9421(queue, session, request, path, env, birth_reader=birth_reader)\n")
 require(old.count(anchor)==1,'unique dispatch seam required');new=old.replace(anchor,anchor+addition,1)
 require(new.replace(anchor+addition,anchor,1)==old,'original dispatch changed');compile(new,'finite-dispatch','exec')
 return {ENTRY:Path(__file__).read_bytes(),'root_p37_known_pause_recovery_control.py':new.encode()}
