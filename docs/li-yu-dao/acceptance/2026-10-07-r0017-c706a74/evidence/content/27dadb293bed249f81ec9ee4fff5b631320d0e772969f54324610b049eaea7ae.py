"""Independent R17 native callback/saved mandate proof. Never rewrites legacy STATE or opens a save.

Missing observed scalars/references produce UNKNOWN. Contradictory authenticated
observations reject. A PASS here qualifies this finite formal chain only;
whole-product and cold-reload acceptance are separate observations.
"""
from pathlib import Path
from datetime import datetime
import copy,hashlib,json,sys
import title_reference_hook as title_hook
import derive_saved_title_reference_v3 as proof
need=proof.need
HEAD='c706a74f9d00dd842b7edce8901fb3417344fd9c'
EVENT_SOURCE_SHA='906c9b689418157bf29bac201c8ca5a2cf1ba99b6802da896caf64ae61213e02'
CONTEXT_SOURCE_SHA='1d9b3a887f13dfeb3a5c1021fd37dc3c9952a9a380d7d6ccc1a3cb7a2dee1823'
REGISTRY_SCHEMA='lyd.r17.formal-native-callback-registry.v1'
POST_SCHEMA='lyd.r17.formal-native-postcommit-registry.v1'
OUTPUT_SCHEMA='lyd.r17.independent-native-formal-qualification.v1'
NAMES={'serial':'lyd_i3b_event_serial','nonce':'lyd_i3b_event_nonce','phase':'lyd_i3b_event_phase'}
def digest(obj):return hashlib.sha256(proof.json_bytes(obj)).hexdigest()
def exact(obj,keys,reason):need(type(obj)is dict and set(obj)==set(keys),reason);return obj
def descriptor_read(desc):return proof.unique_json(proof.artifact(desc,suffix='.json'))
def positive_int(x):return type(x)is int and x>0
def query_pair(pair,provenance):
 exact(pair,{'native_receipt','sdk_result'},'closed original SDK/native pair')
 native=descriptor_read(pair['native_receipt']);sdk=descriptor_read(pair['sdk_result']);title_hook.validate_sdk_native(sdk,native)
 need(native['schema']=='ck3.native-profile-receipt.v1','original native profile schema')
 for key in ('session_id','profile_sha256','pipe_name'):need(native.get(key)==provenance[key],'native provenance differs '+key)
 need(Path(native['receipt_path']).resolve()==Path(pair['native_receipt']['path']).resolve(),'original receipt path differs')
 time=datetime.fromisoformat(native['recorded_at_utc'].replace('Z','+00:00'));need(time.tzinfo is not None,'actual native recorded UTC required')
 return native,time
def character_scope(scope,cid):
 return scope=={'status':'available','raw_type_index':4,'type_key':'character','subtype':0,'typed_identity':{'status':'available','kind':'character','character_id':cid}}
def context_fields(native,expected_event,actor,contract):
 need(native['status']=='native_event_query_verified','actual native event query status')
 r=native['result'];need(r['step']=='query-current-event-window-context-v1' and r['accepted'] is True and r['status']=='available' and r['backend_id']=='native-headless' and r['scope']=='exact-current-event-window','original native exact event query')
 source=exact(r['source'],{'snapshot_id','revision','native_revision','date_raw','paused','backend_id'},'closed original query source')
 need(positive_int(source['revision']) and positive_int(source['native_revision']) and source['snapshot_id']=='native:'+str(source['native_revision']) and type(source['date_raw'])is int and source['paused'] is True and source['backend_id']=='native-headless','actual query frame')
 event=r['current_event_instance_id'];need(positive_int(event),'actual event instance')
 need(r['binding']=={k:source[k] for k in ('snapshot_id','revision','native_revision','date_raw')}|{'expected_revision':source['revision'],'event_instance_id':event},'query binding differs')
 need(r['queried_snapshot_id']==source['snapshot_id'] and r['queried_revision']==source['revision'] and r['queried_native_revision']==source['native_revision'],'query flattened frame differs')
 c=contract.normalize_current_event_window_context_v1(r['current_event_window_context'],expected_event_instance_id=event,expected_date_raw=source['date_raw'],expected_snapshot_revision=source['native_revision'])
 need(c['status']=='available' and c['event_definition_key']==expected_event and c['window_match_count']==1 and r['current_event_window_context_ready'] is True and r['current_event_effect_indicators_ready'] is True,'actual single expected formal event')
 for key,value in c.items():need(key in r and r[key]==value,'native/flattened context drift '+key)
 need(character_scope(c['root_scope'],actor),'actual event root human actor differs')
 actors=[x['scope'] for x in c['saved_scopes'] if x['name']=='lyd_i3b_actor'];need(len(actors)==1 and character_scope(actors[0],actor),'saved formal actor scope differs')
 wrapper={'scope','source','binding'};raw={k:v for k,v in r.items() if k not in wrapper}
 return c,source,raw
def numeric_fields(context,expected,names=NAMES):
 observed={};missing=[]
 for field,name in names.items():
  rows=[r for r in context['saved_scopes'] if r['name']==name];need(len(rows)<=1,'duplicate native scalar '+name)
  if not rows or 'numeric_value' not in rows[0]['scope']:
   observed[field]={'status':'UNKNOWN','scope_name':name,'native_value':None};missing.append('native scalar '+name);continue
  scope=rows[0]['scope'];need(scope['raw_type_index']==1 and scope['type_key']=='value' and scope['subtype']==0,'numeric scope type/subtype')
  n=scope['numeric_value'];exact(n,{'raw_fixed_point','scale','decimal_value','integer_value'},'closed observed numeric payload')
  raw=n['raw_fixed_point'];need(type(raw)is str and re_canonical_signed64(raw),'native exact signed64 raw payload')
  integer=n['integer_value'];need(type(n['scale'])is int and n['scale']==100000 and int(raw)%100000==0 and type(integer)is str and str(int(raw)//100000)==integer and n['decimal_value']==integer,'native formal scalar must be exact integer/scale100000')
  need(type(expected[field])is int and int(integer)==expected[field],'observed native scalar disagrees with actual saved round '+field)
  observed[field]={'status':'ACTUAL_NATIVE_SCALAR_SAVED_ROUND_MATCH','scope_name':name,'native_value':copy.deepcopy(n),'saved_value':expected[field]}
 return observed,missing
def re_canonical_signed64(x):
 try:return str(int(x))==x and -(2**63)<=int(x)<2**63
 except (ValueError,TypeError):return False
def history_query(history,raw):
 rows=[r for r in history if r.get('command')=='query-current-event-window-context-v1' and r.get('result')==raw and r.get('ok') is True]
 need(len(rows)==1 and positive_int(rows[0]['index']),'query not exact unique saved-before native history row')
 return rows[0]['index']
def select_pair(native,query,context,source,history,provenance,converter):
 need(native['status']=='native_gameplay_postcondition_verified' and native['uses_ocr'] is False and native['uses_desktop_input'] is False,'actual native-only selection postcondition')
 before=converter.frame_binding(native['snapshot_before']);after=converter.frame_binding(native['snapshot_after'])
 for k in ('snapshot_id','revision','native_revision','date_raw'):need(before[k]==source[k],'historical query/select starting frame differs '+k)
 for frame in (before,after):
  need(frame['game_pid']==provenance['game_pid'] and frame['connection_generation']==provenance['connection_generation'] and frame['played_character_id']==context['root_scope']['typed_identity']['character_id'],'native selection PID/gen/actor')
 need(after['revision']==before['revision']+1 and after['native_revision']==before['native_revision']+1 and after['snapshot_id']=='native:'+str(after['native_revision']) and after['date_raw']==before['date_raw'],'single native/public callback revision transition')
 need(native['snapshot_before']['paused'] is True and native['snapshot_after']['paused'] is True,'callback paused snapshots required')
 active=native['snapshot_before']['active_event'];need(type(active)is dict and active['source']=='native' and active['instance_id']==context['current_event_instance_id'],'select actual active queried event')
 r=native['result'];need(r['step']=='select-event-option-1' and r['accepted'] is True and r['status']=='submitted' and r['backend_id']=='native-headless' and r['progress_status']=='postcondition','actual native affirmative callback result')
 need(r['event_instance_id']==context['current_event_instance_id'] and r['option_number']==1 and r['option_index']==0,'actual selected source option0')
 options=[x for x in context['options'] if x['native_option_index']==0];need(len(options)==1 and options[0]['shown'] is True and options[0]['enabled'] is True and options[0]['fallback'] is False and options[0]['cancel'] is False,'actual affirmative source option shown/enabled')
 e=r['event_selection'];need(e['postcondition_verified'] is True and e['status'] in ('event_instance_advanced','event_closed') and e['old_event_instance_id']==context['current_event_instance_id'] and e['selected_option_number']==1 and e['selected_native_option_index']==0 and e['bridge_pid']==provenance['game_pid'] and e['connection_generation']==provenance['connection_generation'],'native callback postcondition identity')
 need(e['starting_snapshot_id']==before['snapshot_id'] and e['starting_revision']==before['revision'] and e['ending_snapshot_id']==after['snapshot_id'] and e['ending_revision']==after['revision'],'native callback start/end frame')
 need(r['snapshot_id']==after['snapshot_id'] and r['revision']==after['revision'] and r['paused'] is True and r['active_event']==native['snapshot_after']['active_event'],'public actual selection after frame')
 for field in ('played_character_gold','played_character_prestige','played_character_piety'):
  need(native['snapshot_before'][field]==native['snapshot_after'][field],'formal callback unexpected fee '+field)
 raw={k:v for k,v in r.items() if k not in ('event_instance_id','option_number','option_index')}
 rows=[x for x in history if x.get('command')=='select-event-option-1' and x.get('result')==raw and x.get('ok') is True]
 need(len(rows)==1,'callback not exact unique saved-before command-history row')
 qindex=history_query(history,query)
 need(rows[0]['index']==qindex+1,'query/select must be adjacent actual native history commands')
 return {'before':before,'after':after,'query_history_index':qindex,'select_history_index':rows[0]['index'],'source_native_option':0}
def native_saved_mandate(state,qualified,provenance,cp,converter):
 need(state['stage']=='signed_precommit' and state['round']['phase']==2,'actual signed-precommit stage/phase required')
 after,transition=converter.transition.bind_checkpoint_transition(cp,provenance)
 need(qualified['schema']=='lyd.sdk-checkpoint-qualified-native.v3' and qualified['G2_status']=='BOUND_COMPLETE_NATIVE_OBSERVATION','actual complete G2 qualification required')
 rb=qualified['runtime_binding'];need(rb['source_head']==HEAD and rb['session_id']==provenance['session_id'] and rb['profile_sha256']==provenance['profile_sha256'] and rb['pipe_name']==provenance['pipe_name'] and rb['game_pid']==after['game_pid'] and rb['connection_generation']==after['connection_generation'],'actual qualified source/runtime identity')
 for field,value in (('queried_snapshot_id',after['snapshot_id']),('queried_revision',after['revision']),('queried_native_revision',after['native_revision']),('date_raw',after['date_raw']),('played_character_id',after['played_character_id'])):need(rb[field]==value,'qualified after-frame '+field)
 need(rb['checkpoint']==cp['result']['checkpoint'] and state['checkpoint_sha256']==rb['checkpoint']['sha256'],'qualified saved checkpoint original descriptor')
 si=state['identity'];need(si['actor_id']==after['played_character_id'] and si['pid']==after['game_pid'] and si['session_id']==provenance['session_id'] and si['revision']==after['native_revision'],'saved stage actual identity')
 w=qualified['native_predicates'];need(type(w)is dict and w['complete_current_faith_roster'] is True and w['identity']==si and w['checkpoint_sha256']==state['checkpoint_sha256'],'independently qualified G2 saved full roster binding')
 roster=state['roster'];need(roster['whole_world_living_records_scanned'] is True and roster['faith_classification_complete'] is True and roster['unclassified_living_ids']==[],'complete parsed living roster required')
 members={r['character_id']:r for r in roster['members']};native={r['character_id']:r for r in w['characters']}
 need(len(members)==len(roster['members']) and len(native)==len(w['characters']) and set(members)==set(native)==set(roster['living_faith_ids'])==set(roster['captured_member_ids']),'exact saved/captured/native complete Faith member IDs')
 humans=sorted(i for i,n in native.items() if n['is_ai'] is False);actor=si['actor_id']
 need(humans==[actor] and sorted(w['human_character_ids'])==humans and roster['saved_current_human_ids']==humans and roster['saved_current_human_faith_ids']==humans,'single actual human identity must be proved by complete saved/native topology')
 for cid,row in members.items():
  n=native[cid];need(all(type(n[k])is bool for k in ('alive','adult','imprisoned','incapable','is_ai')) and type(n['learning'])is int and n['alive'] is True,'actual native character predicates')
  elector=n['adult'] and not n['imprisoned'] and not n['incapable'] and n['learning']>=15
  need(row['member_owner_id']==actor and row['member_serial']==state['round']['serial'] and row['was_elector']==int(elector) and row['was_player']==int(not n['is_ai']),'exact saved native elector/human/member stamps')
  if not n['is_ai']:need(row['player_yes']==1,'actual human own412 consent stamp')
 schools=state['schools'];need(type(schools)is list and schools and len({r['rite_id'] for r in schools})==len(schools),'complete unique saved captured schools')
 summaries=[]
 for school in schools:
  selected=[r for r in members.values() if r['member_rite_id']==school['rite_id']]
  electors=[r for r in selected if r['was_elector']==1];yes=sum(r['vote']==1 for r in electors)
  need(school['owner_id']==actor and school['serial']==state['round']['serial'] and school['members_total']==len(selected) and school['total']==len(electors) and school['yes']==yes,'exact saved school/roster native-qualified counts')
  need(str(school['rite_id']) in w['rite_counties'] and school['counties']==w['rite_counties'][str(school['rite_id'])],'actual native county count')
  dormant=school['counties']==0 and not selected;need(school['dormant']==int(dormant),'actual dormant iff no counties and no living members')
  if not dormant:need(electors and 3*yes>=2*len(electors) and school['signed']==1 and school['delegate_id'] in {r['character_id'] for r in electors},'actual signed school/quorum/qualified delegate')
  summaries.append({'rite_id':school['rite_id'],'members':len(selected),'electors':len(electors),'yes':yes,'signed':school['signed'],'delegate':school['delegate_id'],'dormant':dormant})
 return after,transition,{'complete_member_ids':sorted(members),'human_ids':humans,'natural_NPC_votes':{str(i):{'vote':r['vote'],'was_elector':r['was_elector'],'actual_native_is_ai':native[i]['is_ai']} for i,r in members.items() if native[i]['is_ai']},'schools':summaries}
def title_reference_observation(contexts,state):
 actor=state['identity']['actor_id'];captured=state['actor']['lists'].get('lyd_i3b_political_titles')
 if captured is None:return {'status':'UNKNOWN','reason':'actual saved captured political Title list absent','title_type':None}
 candidates=[]
 for event,context in contexts:
  for saved in context['saved_scopes']:
   if saved['name']!='lyd_i3b_title':continue
   scope=saved['scope'];identity=scope['typed_identity']
   if scope['raw_type_index']==5 and scope['type_key']=='landed_title' and scope['subtype']==0 and identity.get('status')=='available' and identity.get('kind')=='landed_title':candidates.append({'event':event,'scope':saved,'full_id':identity['title_id']})
 if not candidates:return {'status':'UNKNOWN','reason':'no actual current-round native full Title payload; no alias guessed','title_type':None}
 need(captured.get('present') is True and type(captured.get('items'))is list and len(captured['items'])==7,'actual complete saved political Title list')
 need(len({r['identity'] for r in captured['items']})==7 and all(r.get('type')=='lt' and type(r.get('identity'))is str and positive_int(int(r['identity'])) and r.get('entries')==[{'key':'type','value':'lt'},{'key':'identity','value':r['identity']}] for r in captured['items']),'actual exact typed Title references, no guessed aliases/duplicates')
 tid=candidates[0]['full_id'];need(all(c['full_id']==tid for c in candidates),'historical round native Title full-ID differs')
 rows=[r for r in captured['items'] if r['identity']==str(tid)];need(len(rows)==1,'observed native full Title absent from exact saved captured list');row=rows[0]
 protected=[r for r in state['protected_titles'] if r['title_id']==tid];need(len(protected)==1 and protected[0]['holder']==actor and protected[0]['AST_sha256']==protected[0]['baseline_AST_sha256'],'authority Title actual entity/holder/full baseline AST protection')
 return {'status':'ROUND_NATIVE_FULL_TITLE_AND_CURRENT_SAVED_REFERENCE_BOUND','title_type':row['type'],'actual_full_id':tid,'source_named_scope':'lyd_i3b_title','observed_native_scopes':candidates,'actual_saved_captured_title_reference':copy.deepcopy(row),'saved_title_AST_sha256':protected[0]['AST_sha256'],'historical_query_frames_retained':True,'observations_rewritten':False}
def qualify_precommit(registry,cp,state,qualified,provenance,reader,converter,export,typed):
 exact(registry,{'schema','source_head','window','callback_pairs','review_query','reference_query'},'closed explicit formal callback registry')
 need(registry['schema']==REGISTRY_SCHEMA and registry['source_head']==HEAD and registry['window']=='B3-signed-precommit' and export['source']['head']==HEAD,'exact R17 signed window/source')
 events=Path(export['source_root'])/'mod_li_yu_dao/events/lyd_i3b_institution_events.txt'
 need(hashlib.sha256(events.read_bytes()).hexdigest()==EVENT_SOURCE_SHA,'actual formal event source differs')
 refs=title_hook.bound_source_refs(reader,converter,export);need(refs['event_context']['sha256']==CONTEXT_SOURCE_SHA,'exact numeric/event source contract')
 modules=proof.load_bound_modules(refs);contract=modules['event_context']
 after,transition,mandate=native_saved_mandate(state,qualified,provenance,cp,converter)
 before=transition['before_binding'];history=cp['snapshot_before']['native_command_history'];actor=state['identity']['actor_id'];round_=state['round']
 exact(registry['callback_pairs'],{'lyd.410','lyd.411','lyd.412','lyd.413'},'complete finite formal callback kinds')
 records=[];contexts=[];missing=[];alltimes=[]
 for event in ('lyd.410','lyd.412','lyd.411','lyd.413'):
  pairs=registry['callback_pairs'][event];need(type(pairs)is list and len(pairs)<=1,'finite single-human explicit actual callback list')
  if not pairs:missing.append('original query/select pair '+event);continue
  for pair in pairs:
   exact(pair,{'query','select'},'closed formal query/select pair')
   query,qt=query_pair(pair['query'],provenance);selection,st=query_pair(pair['select'],provenance);need(qt<=st,'native actual callback chronology')
   context,source,raw=context_fields(query,event,actor,contract)
   expected={'serial':round_['serial'],'nonce':round_['nonce']-(1 if event=='lyd.410' else 0),'phase':1 if event=='lyd.410' else 2}
   numbers,absent=numeric_fields(context,expected);missing.extend(absent)
   bound=select_pair(selection,raw,context,source,history,provenance,converter)
   need(bound['after']['revision']<=before['revision'] and bound['after']['native_revision']<=before['native_revision'] and source['date_raw']<=before['date_raw'],'historical callback may not be future/sameframe rewritten')
   contexts.append((event,context));alltimes.append((bound['query_history_index'],qt,st))
   records.append({'event':event,'actual_query':pair['query'],'actual_selection':pair['select'],'native_scalars':numbers,'actual_callback_frames':bound,'actual_recorded_query_utc':query['recorded_at_utc'],'actual_recorded_select_utc':selection['recorded_at_utc']})
 review,reviewtime=query_pair(registry['review_query'],provenance);context,source,raw=context_fields(review,'lyd.430',actor,contract)
 need(source=={**{k:before[k] for k in ('snapshot_id','revision','native_revision','date_raw')},'paused':True,'backend_id':'native-headless'},'current430 must be exact actual checkpoint-before source frame')
 need(cp['snapshot_before']['active_event']['instance_id']==context['current_event_instance_id'],'current review/save before active event')
 index=history_query(history,raw);need(history[-1]['index']==index,'430 review must be last unchanged before-save native command')
 commit_options=[r for r in context['options'] if r['native_option_index']==0]
 need(len(commit_options)==1 and commit_options[0]['shown'] is True and commit_options[0]['enabled'] is True,'actual current430 confirm guard is not shown/enabled')
 scalars,absent=numeric_fields(context,{'serial':round_['serial'],'nonce':round_['nonce'],'phase':round_['phase']});missing.extend(absent);contexts.append(('lyd.430',context))
 reference_query=None
 if registry['reference_query'] is not None:
  reference_native,reference_time=query_pair(registry['reference_query'],provenance)
  reference_context,reference_source,reference_raw=context_fields(reference_native,'lyd.430',actor,contract)
  need(reference_source['revision']<before['revision'] and reference_source['native_revision']<before['native_revision'] and reference_source['date_raw']<=before['date_raw'] and reference_time<reviewtime,'explicit reference is historical current-round, not forged current frame')
  reference_index=history_query(history,reference_raw)
  reference_scalars,absent=numeric_fields(reference_context,{'serial':round_['serial'],'nonce':round_['nonce']-1,'phase':1});missing.extend(absent)
  contexts.append(('lyd.430-explicit-phase1-reference',reference_context))
  reference_query={'original_pair':registry['reference_query'],'actual_source_frame':reference_source,'native_scalars':reference_scalars,'actual_saved_history_index':reference_index,'projected_as_current_frame':False}
 sortedtimes=sorted(alltimes);need(all(sortedtimes[i][2]<=sortedtimes[i+1][1] for i in range(len(sortedtimes)-1)) and all(st<=reviewtime for _,qt,st in sortedtimes),'actual historical query/select chronological order')
 sequence=[r['event'] for r in sorted(records,key=lambda r:r['actual_callback_frames']['query_history_index'])]
 need(sequence==[event for event in ('lyd.410','lyd.412','lyd.411','lyd.413') if registry['callback_pairs'][event]],'finite single-human source route affirmative callback order')
 need(typed['protection_checks_match'] is True and len(typed['checks'])==87 and all(c['matches'] is True for c in typed['checks']),'complete unchanged87 protection gate')
 need(state['observation_checks_match'] is True and all(c['matches'] is True for c in state['checks']),'all saved/native-qualified signed-stage checks required')
 reference=title_reference_observation(contexts,state)
 if reference['status']=='UNKNOWN':missing.append('independent native full Title reference binding')
 return {'schema':OUTPUT_SCHEMA,'source_head':HEAD,'window':'B3-signed-precommit','qualification_status':'UNKNOWN' if missing else 'FORMAL_NATIVE_CALLBACK_SAVED_MANDATE_PASS','qualification_pass':None if missing else True,'formal_mandate_credit':None if missing else True,'whole_product_pass':None,'actor_id':actor,'actual_round':copy.deepcopy(round_),'actual_checkpoint_sha256':state['checkpoint_sha256'],'identity':copy.deepcopy(state['identity']),'actual_profile_sha256':provenance['profile_sha256'],'actual_before_frame':before,'actual_after_frame':after,'callback_chain':records,'current430_native_scalars':scalars,'current430_query':registry['review_query'],'explicit_historical_reference_query':reference_query,'mandate':mandate,'independent_reference_qualification':reference,'missing_actual_observations':missing,'legacy_formal_event_context_qualification_retained':copy.deepcopy(state['formal_event_context_qualification']),'legacy_native_reference_qualification_retained':copy.deepcopy(state['native_reference_qualification']),'legacy_STATE_unchanged':True,'extra_checkpoint_body_reads':0,'SDK_game_calls':0,'source_artifacts':refs,'original_callback_source':{'path':events.as_posix(),'sha256':EVENT_SOURCE_SHA}}

def replay_certificate(certificate,reader,converter,export):
 refs=exact(certificate['retained_source_artifacts'],{'author_input','initial_state','native_joined_state','qualified_native','typed_protection','checkpoint_receipt','provenance'},'closed original certificate retained tuple')
 inp=descriptor_read(refs['author_input']);need(inp['expected_source_head']==HEAD and inp['window']==certificate['window'],'certificate actual source/input window')
 initial=descriptor_read(refs['initial_state']);state=descriptor_read(refs['native_joined_state']) if refs['native_joined_state'] else initial
 cp=descriptor_read(refs['checkpoint_receipt']);qualified=descriptor_read(refs['qualified_native']);provenance=descriptor_read(refs['provenance']);typed=descriptor_read(refs['typed_protection'])
 for field,key in (('saved_state','initial_state'),('checkpoint_receipt','checkpoint_receipt'),('provenance','provenance')):need(qualified['runtime_binding']['artifact_sha256'][field]==refs[key]['sha256'],'certificate original qualified artifact binding '+field)
 registry=descriptor_read(certificate['original_input_registry'])
 observed=qualify(registry,cp,state,qualified,provenance,reader,converter,export,typed)
 need(all(certificate.get(k)==v for k,v in observed.items()),'certificate content disagrees with authenticated retained observations')
 need(observed['qualification_pass'] is True,'retained certificate independently replayed UNKNOWN')
 return observed

def qualify_postcommit(registry,cp,state,qualified,provenance,reader,converter,export,typed):
 exact(registry,{'schema','source_head','window','signed_precommit','previous_postcommit','action'},'closed explicit postcommit registry')
 need(registry['schema']==POST_SCHEMA and registry['source_head']==HEAD and registry['window'] in ('B4-factory-result','B5-final-protection'),'actual finite postcommit source/window')
 signed=descriptor_read(registry['signed_precommit']);need(signed['schema']==OUTPUT_SCHEMA and signed['source_head']==HEAD and signed['window']=='B3-signed-precommit' and signed['qualification_status']=='FORMAL_NATIVE_CALLBACK_SAVED_MANDATE_PASS' and signed['qualification_pass'] is True,'actual independently PASS signed mandate required')
 replay_certificate(signed,reader,converter,export)
 after,transition=converter.transition.bind_checkpoint_transition(cp,provenance)
 need(state['stage']=='success_postcommit' and state['round']['result_code']==1 and state['round']['serial']==signed['actual_round']['serial'] and state['round']['nonce']==signed['actual_round']['nonce'],'actual success receipt same signed S/N')
 for field in ('actor_id','pid','session_id'):need(state['identity'][field]==signed['identity'][field],'postcommit real mandate identity '+field)
 need(provenance['profile_sha256']==signed['actual_profile_sha256'] and state['identity']['revision']==after['native_revision'] and state['checkpoint_sha256']==cp['result']['checkpoint']['sha256'],'postcommit real profile/checkpoint')
 need(after['revision']>signed['actual_after_frame']['revision'] and after['native_revision']>signed['actual_after_frame']['native_revision'],'postcommit must follow signed checkpoint')
 refs=title_hook.bound_source_refs(reader,converter,export);need(refs['event_context']['sha256']==CONTEXT_SOURCE_SHA,'exact postcommit event contract');modules=proof.load_bound_modules(refs)
 pair=registry['action'];exact(pair,{'query','select'},'exact postcommit source action pair');query,qt=query_pair(pair['query'],provenance);selection,st=query_pair(pair['select'],provenance);need(qt<=st,'actual postcommit query/select times')
 event='lyd.430' if registry['window']=='B4-factory-result' else 'lyd.431';context,source,raw=context_fields(query,event,state['identity']['actor_id'],modules['event_context'])
 names=NAMES if event=='lyd.430' else {'serial':'lyd_i3b_result_event_serial','nonce':'lyd_i3b_result_event_nonce'}
 expected={'serial':signed['actual_round']['serial'],'nonce':signed['actual_round']['nonce'],'phase':2};scalars,missing=numeric_fields(context,expected,names)
 bound=select_pair(selection,raw,context,source,cp['snapshot_before']['native_command_history'],provenance,converter)
 need(bound['after']['revision']<=transition['before_binding']['revision'] and bound['after']['native_revision']<=transition['before_binding']['native_revision'],'postcommit action saved temporal binding')
 if event=='lyd.430':need(source['revision']>=signed['actual_after_frame']['revision'] and source['native_revision']>=signed['actual_after_frame']['native_revision'],'commit must occur after authenticated saved signed checkpoint')
 previous=None
 if event=='lyd.431':
  previous=descriptor_read(registry['previous_postcommit']);need(previous['schema']==OUTPUT_SCHEMA and previous['window']=='B4-factory-result' and previous['qualification_pass'] is True and previous['signed_precommit']==registry['signed_precommit'],'actual independently bound B4 before ACK required')
  replay_certificate(previous,reader,converter,export)
  need(source['revision']>=previous['actual_after_frame']['revision'] and source['native_revision']>=previous['actual_after_frame']['native_revision'],'ACK must follow retained actual B4 save')
  need(cp['snapshot_before']['active_event'] is None,'actual ACK event cleanup absent')
 else:need(registry['previous_postcommit'] is None,'B4 prior-post reference must be NULL')
 need(qualified['schema']=='lyd.sdk-checkpoint-qualified-native.v3' and qualified['runtime_binding']['source_head']==HEAD and qualified['runtime_binding']['checkpoint']==cp['result']['checkpoint'],'actual postcommit native qualified checkpoint source')
 need(qualified['G2_status']=='BOUND_COMPLETE_NATIVE_OBSERVATION','actual postcommit complete G2 required')
 for field,value in (('queried_snapshot_id',after['snapshot_id']),('queried_revision',after['revision']),('queried_native_revision',after['native_revision']),('date_raw',after['date_raw']),('played_character_id',after['played_character_id'])):need(qualified['runtime_binding'][field]==value,'postcommit qualified actual after frame '+field)
 for k in ('session_id','profile_sha256','pipe_name','game_pid','connection_generation'):need(qualified['runtime_binding'][k]==provenance[k],'actual postcommit native provenance '+k)
 g3=qualified['qualified_native_head'];need(g3['status']=='BOUND_NATIVE_TITLE_FIELDS_OBSERVATION','actual G3 complete title fields qualification')
 need(g3['runtime_binding']==qualified['runtime_binding'],'independent G3 runtime binding differs from complete tuple')
 ref=state['result_head_title_reference'];faithref=state['typed_religious_title_reference'];joined=state['saved_faith_head_title_holder_join'];native=state['native_title']
 if not(ref and faithref and joined and native):missing.append('actual saved/native religious Title full join')
 else:
  need(ref['present'] is True and ref['type']==signed['independent_reference_qualification']['title_type'] and ref['tick'] is None and int(ref['identity'])==faithref['full_id'] and faithref['faith_full_id']==state['identity']['faith_id'] and faithref['entity_kind']=='landed_title','actual postcommit typedTitle/savedFaith full-ID and established native type')
  need(joined['status']=='QUALIFIED_SAVED_TITLE_HOLDER_OBSERVATION' and joined['faith_full_id']==state['identity']['faith_id'] and joined['title_full_id']==faithref['full_id'] and joined['title_AST_sha256']==native['AST_sha256'] and joined['holder_full_id']==state['identity']['actor_id'],'actual saved Faith/title holder join')
  # Keep original full title/native/raw doctrine/property checks authoritative.
  graph=g3['native_graph'];need(graph['graph_available'] is True and graph['legal_head_title_absent'] is False and graph['faith_full_id']==state['identity']['faith_id'] and graph['head_title_full_id']==faithref['full_id'] and graph['native_title_holder_absent'] is False and graph['native_title_holder_full_id']==state['identity']['actor_id'],'actual G3 full Faith/Title/holder join')
  need(g3['factory_contract_match'] is True and g3['saved_title_join']['title_id']==faithref['full_id'] and g3['saved_title_join']['AST_sha256']==native['AST_sha256'],'actual native4properties/law and complete saved Title join')
  if previous:need(previous['actual_title_full_id']==faithref['full_id'] and previous['actual_saved_title_AST_sha256']==native['AST_sha256'],'ACK preserves exact actual religious Title fullAST')
 protection=typed['protection_checks_match'] is True and len(typed['checks'])==88 and typed['checks'][-1]['name']=='current_Faith_full_AST_only_declared_factory_delta' and len({c['name'] for c in typed['checks']})==88 and all(c['matches'] is True for c in typed['checks'])
 checks=state['observation_checks_match'] is True and all(c['matches'] is True for c in state['checks'])
 if not protection:missing.append('current87 political/other complete protections are RED')
 if not checks:missing.append('current saved/native postcommit checks are RED')
 status='UNKNOWN' if missing else 'FORMAL_NATIVE_POSTCOMMIT_SAVED_RESULT_PASS'
 return {'schema':OUTPUT_SCHEMA,'source_head':HEAD,'window':registry['window'],'qualification_status':status,'qualification_pass':None if missing else True,'formal_mandate_credit':None if missing else True,'whole_product_pass':None,'actual_round':copy.deepcopy(state['round']),'identity':copy.deepcopy(state['identity']),'actual_checkpoint_sha256':state['checkpoint_sha256'],'actual_before_frame':transition['before_binding'],'actual_after_frame':after,'signed_precommit':registry['signed_precommit'],'previous_postcommit':registry['previous_postcommit'],'actual_action':pair,'actual_action_frames':bound,'actual_action_native_scalars':scalars,'actual_title_full_id':faithref['full_id'] if faithref else None,'actual_saved_title_AST_sha256':native['AST_sha256'] if native else None,'current87_protections_match':protection,'original_protection_check_count':87,'declared_additional_Faith_AST_delta_check':typed['checks'][-1] if len(typed['checks'])==88 else None,'current_saved_native_checks_match':checks,'missing_actual_observations':missing,'legacy_STATE_unchanged':True,'legacy_formal_event_context_qualification_retained':copy.deepcopy(state['formal_event_context_qualification']),'legacy_native_reference_qualification_retained':copy.deepcopy(state['native_reference_qualification']),'source_artifacts':refs,'extra_checkpoint_body_reads':0,'SDK_game_calls':0}

def qualify(registry,cp,state,qualified,provenance,reader,converter,export,typed):
 if registry.get('schema')==REGISTRY_SCHEMA:return qualify_precommit(registry,cp,state,qualified,provenance,reader,converter,export,typed)
 if registry.get('schema')==POST_SCHEMA:return qualify_postcommit(registry,cp,state,qualified,provenance,reader,converter,export,typed)
 raise ValueError('unregistered formal native qualification registry schema')
