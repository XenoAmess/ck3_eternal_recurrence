"""ROOT-only R10 immutable input assembler. No game, binder, emitter, or host calls."""
from pathlib import Path
import argparse, ast, hashlib, json, math, re, stat, struct

EXTERNAL=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
RUN=EXTERNAL/'live-attempt-010'
PYTHON='C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
BASELINE={'path':str(EXTERNAL/'r10-first-join-proof-inputs-20261005-003/FLOW-REQUEST.actual.json'),
    'sha256':'2d37f27d55bb953808e2368480131dd0dcfd629b7b2095905f0dfe3a257c58ce'}
IDENTITY_KEYS={'game_pid','process_create_time','actor_id','recipient_id','interaction_key','action'}
FIELDS={'schema','phase','claim','packet','native_result','before_save','before_checkpoint_sdk','after_save',
    'after_checkpoint_sdk','first_query_sdk','first_query_frame_sdk','current_query_sdk','current_query_frame_sdk',
    'bound_index','output','bound_output','flow_output','evidence_output','operator_id','next_intent_id','open_readback'}

def need(ok,message):
    if not ok:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def jread(raw):
    def pairs(items):
        out={}
        for key,value in items:
            need(key not in out,'duplicate JSON field');out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def exact(value,keys,label):
    need(type(value) is dict and set(value)==set(keys),'closed '+label+' differs');return value
def readref(value,cache,*,saved=False):
    exact(value,('path','sha256','bytes') if saved else ('path','sha256'),'artifact reference')
    need(type(value['path']) is str and Path(value['path']).is_absolute(),'absolute actual reference required')
    need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'full lowercase SHA required')
    path=Path(value['path']);raw=path.read_bytes();need(digest(raw)==value['sha256'],'immutable SHA differs: '+str(path))
    if saved:
        need(type(value['bytes']) is int and value['bytes']>0 and len(raw)==value['bytes'],'actual immutable saved size differs')
        need(path.suffix.lower()=='.ck3' and '/userdir/save games/' not in str(path.resolve()).replace(chr(92),'/').lower(),'actual immutable checkpoint path required')
        need(bool(getattr(path.stat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_READONLY),'actual checkpoint is not readonly')
    cache[str(path.resolve())]=value['sha256'];return raw
def plain(value):return {'path':value['path'],'sha256':value['sha256']}
def sdk(value,cache):
    receipt=jread(readref(value,cache));need(receipt.get('isError') is False and type(receipt.get('structuredContent')) is dict,'SDK error/unknown cannot be used as actual success')
    return receipt['structuredContent']
def output_path(value,*,exists=False):
    need(type(value) is str and Path(value).is_absolute(),'explicit absolute output required')
    path=Path(value).resolve();need(EXTERNAL in path.parents,'output must be external')
    need(not any(parent.name.startswith('live-attempt-') for parent in (path,*path.parents)),'helper cannot write within live runtime')
    need(path.exists() is exists,'output existence differs from declared phase');return path
def pointer(value,path):
    need(type(path) is str and path.startswith('/'),'explicit process receipt pointer required')
    for token in path[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~');need(type(value) is dict and token in value,'actual process field absent');value=value[token]
    return value
def source_baseline(cache):
    flow=jread(readref(BASELINE,cache));need(flow['source_revision']=='d0f8fa3b9d444828759443aa018bfd7ad31b398d' and flow['consumption_mode']=='PROPOSAL_OPENED','frozen R10 source baseline differs')
    ready=flow['source_ready'];index=jread(readref(ready['author_index'],cache));root=Path(ready['author_index']['path']).resolve().parent
    for row in index['files']:
        exact(row,('path','bytes','sha256'),'source INDEX row');path=(root/row['path']).resolve();need(root in path.parents,'source payload escapes')
        raw=readref({'path':str(path),'sha256':row['sha256']},cache);need(type(row['bytes']) is int and len(raw)==row['bytes'],'source indexed bytes differ')
    for name in ('provider','binder','emitter','source_readback'):readref(ready[name],cache)
    record=ready['source_record'];exact(record,('path','bytes','sha256'),'source record')
    raw=readref(plain(record),cache);need(type(record['bytes']) is int and len(raw)==record['bytes'],'actual source record bytes differ')
    tree=ast.parse(Path(ready['provider']['path']).read_bytes());constants={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    need(constants['PINNED_SOURCE_RECORD_REF']==record and constants['PINNED_ROOT_BINDING'] is None,'exact source_record literal or source-ready provider differs')
    need(constants['PINNED_SOURCE_SUMMARY']==jread(readref(ready['source_readback'],cache)),'source readback differs')
    for name in ('production_manifest','native_profile','ordinary_contract','host_module'):readref(flow[name],cache)
    need(flow['ordinary_contract']['sha256']=='e0a96aa39626df166270d3d5467a8e4d57cec77d7577cebcced03983feba5fa3' and flow['host_module']['sha256']=='f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b','stable contract/host differs')
    profile=jread(readref(flow['native_profile'],cache));guard=jread(readref({'path':profile['guard_profile'],'sha256':profile['guard_profile_sha256']},cache))
    for name in ('dll','injector'):readref(profile[name],cache)
    oldclaim=jread(readref(flow['claim'],cache));identity=exact(oldclaim['action_identity'],IDENTITY_KEYS,'six stable identity')
    process=flow['process_identity'];receipt=jread(readref(process['receipt'],cache))
    for key,selector in process['receipt_fields'].items():
        actual=pointer(receipt,selector);need(type(actual) is type(process[key]) and actual==process[key],'actual process receipt field differs')
    need(process['game_pid']==guard['target']['pid']==identity['game_pid'] and process['process_create_time']==guard['target']['process_create_time']==identity['process_create_time'],'same process identity differs')
    return flow,identity,oldclaim['host_provenance']
def checkpoint(save_ref,sdk_ref,cache,identity,provenance):
    raw=readref(save_ref,cache,saved=True);sc=sdk(sdk_ref,cache);frame=sc.get('snapshot_after',sc.get('snapshot'));need(type(frame) is dict,'checkpoint actual frame missing')
    result=sc.get('result',{});cp=result.get('checkpoint',{})
    need(result.get('step')=='save-checkpoint' and result.get('accepted') is True and cp.get('status')=='saved' and cp.get('strategy')=='native-autosave-command-v1','actual saved metadata status/strategy differs')
    need(type(cp.get('size')) is int and cp['size']==len(raw)==save_ref['bytes'] and cp.get('sha256')==save_ref['sha256'],'actual save/SDK size/SHA differs')
    need(cp.get('date_raw')==frame.get('date_raw')==result.get('submission',{}).get('date_raw') and result.get('materialization',{}).get('available') is True,'actual saved date/materialization differs')
    for key in ('profile_sha256','session_id','pipe_name'):need(sc.get(key)==provenance[key],'checkpoint actual provenance differs')
    need(frame['diagnostics']['bridge_pid']==identity['game_pid'] and frame['player_character_id']==identity['actor_id'],'checkpoint actual full actor/PID differs')
    return frame
def query(query_ref,frame_ref,cache,identity,provenance):
    sc=sdk(query_ref,cache);own=sc.get('snapshot_after',sc.get('snapshot'))
    need((frame_ref is None)==(type(own) is dict),'query must use own frame or one explicit same-frame SDK')
    frame=own if frame_ref is None else sdk(frame_ref,cache).get('snapshot_after')
    need(type(frame) is dict and frame,'actual query frame missing');r=sc.get('result',{});ctx=r.get('character_interaction_ordinary_context',{})
    need(r.get('step')=='query-character-interaction-ordinary-v1' and r.get('accepted') is True and r.get('status')=='available' and r.get('read_only') is True,'actual ordinary readonly query differs')
    need(ctx.get('schema')=='ck3-character-interaction-ordinary-context-v1' and ctx.get('status')=='available' and ctx.get('read_only') is True and ctx.get('business_postcondition_verified') is False,'query context schema/credit differs')
    for flag in ('shown','can_send','ready_to_initiate','source_code_pins_verified','actor_binding_verified','recipient_binding_verified','owner_thread_verified','tls_verified','frame_verified'):need(ctx.get(flag) is True,'actual query guard absent: '+flag)
    need(ctx.get('active_event_present') is False and ctx.get('incoming_interaction_present') is False,'actual ready query has event/incoming')
    for key,want in (('player_character_id',identity['actor_id']),('recipient_id',identity['recipient_id']),('game_pid',identity['game_pid'])):need(type(ctx.get(key)) is int and ctx[key]==want,'query full identity differs: '+key)
    need(ctx.get('interaction_key')==identity['interaction_key'] and frame.get('paused') is True and frame.get('map_ready') is True,'actual key/paused map differs')
    for key,want in (('queried_revision',frame.get('revision')),('queried_native_revision',frame.get('native_revision')),('queried_snapshot_id',frame.get('snapshot_id'))):need(type(r.get(key)) is type(want) and r[key]==want,'actual query exact public/native frame differs')
    need(type(frame['revision']) is int and type(frame['native_revision']) is int and frame['revision']>0 and frame['native_revision']>0 and frame['snapshot_id']=='native:'+str(frame['native_revision']),'actual canonical frame differs')
    need(type(ctx.get('snapshot_revision')) is int and ctx['snapshot_revision']==frame['native_revision'] and ctx['date_raw']==frame['date_raw'] and ctx['connection_generation']==frame['diagnostics']['connection_generation'] and frame['diagnostics']['bridge_pid']==identity['game_pid'],'actual query frame context differs')
    for key in ('profile_sha256','session_id','pipe_name'):need(sc.get(key)==provenance[key],'query actual provenance differs')
    return frame
def validate(request):
    exact(request,FIELDS,'parameterized ROOT request');need(request['schema']=='lyd.r10.proposal-input-assembly-request.v1' and request['phase'] in ('prepare_bind','finish_emit'),'closed phase/schema differs')
    cache={};flow,identity,provenance=source_baseline(cache)
    claim=jread(readref(request['claim'],cache));need(claim.get('schema')=='ck3-ordinary-interaction-once-claim-v1' and claim.get('status')=='claimed_result_unknown_no_retry','immutable actual once claim required')
    need(exact(claim.get('action_identity'),IDENTITY_KEYS,'six identity')==identity and claim.get('host_provenance')==provenance,'actual same six identity/provenance differs')
    need(type(claim.get('claim_ordinal')) is int and claim['claim_ordinal']>=0 and type(claim.get('request_id')) is str and re.fullmatch('ordinary-interaction-[0-9a-f]{32}',claim['request_id']),'actual requestID/ordinal differs')
    cp=Path(request['claim']['path']);need(cp.resolve().parent==(RUN/'native-state/native-session/ordinary-interaction-actions').resolve(),'claim must be actual R10 host directory')
    need(Path(request['packet']['path']).resolve()==cp.with_suffix('.packet.bin').resolve() and Path(request['native_result']['path']).resolve()==cp.with_suffix('.native-result.json').resolve(),'actual packet/native sidecar path differs')
    packetraw=readref(request['packet'],cache);need(len(packetraw)>=4 and struct.unpack('<I',packetraw[:4])[0]==len(packetraw)-4,'actual compact packet length differs')
    packet=jread(packetraw[4:]);native=jread(readref(request['native_result'],cache));binding=claim['binding']
    need(packet.get('request_id')==native.get('request_id')==claim['request_id'] and packet.get('step')=='initiate-character-interaction-ordinary-v1' and packet.get('interaction_key')==identity['interaction_key'],'actual packet/native request/key differs')
    for key,want in (('recipient_id',identity['recipient_id']),('expected_player_character_id',identity['actor_id']),('expected_game_pid',identity['game_pid']),('expected_revision',binding['native_revision']),('expected_connection_generation',binding['connection_generation'])):need(type(packet.get(key)) is int and packet[key]==want,'actual native wire binding differs: '+key)
    need(native.get('ok') is True and native.get('result',{}).get('status')=='pending','actual pending native receipt required')
    ack=native['result']['character_interaction_ordinary_initiation'];need(ack.get('verification_pending') is True and ack.get('postcondition_verified') is False and ack.get('business_postcondition_verified') is False,'native ACK cannot grant business credit')
    before=checkpoint(request['before_save'],request['before_checkpoint_sdk'],cache,identity,provenance);after=checkpoint(request['after_save'],request['after_checkpoint_sdk'],cache,identity,provenance)
    first=query(request['first_query_sdk'],request['first_query_frame_sdk'],cache,identity,provenance)
    need(first['revision']==binding['revision'] and first['native_revision']==binding['native_revision'] and first['snapshot_id']==binding['snapshot_id'] and first['diagnostics']['connection_generation']==binding['connection_generation'],'first actual query differs from current claim')
    need(first['native_revision']>=before['native_revision'] and first['date_raw']>=before['date_raw'] and after['native_revision']>=first['native_revision'] and after['date_raw']>=first['date_raw'],'actual before/query/opened frame ordering differs')
    if request['current_query_sdk'] is None:need(request['current_query_frame_sdk'] is None and request['phase']=='prepare_bind','actual later release current/frame missing')
    else:
        current=query(request['current_query_sdk'],request['current_query_frame_sdk'],cache,identity,provenance)
        need(current['native_revision']>=after['native_revision'] and current['date_raw']>=after['date_raw'],'actual later current predates opened save')
        need(current['diagnostics']['connection_generation']==first['diagnostics']['connection_generation'],'R10 fixed connection generation differs')
    need(type(request['operator_id']) is str and request['operator_id'].strip(),'explicit ROOT operator required')
    if request['next_intent_id'] is None:need(request['phase']=='prepare_bind','explicit nextintent missing')
    else:
        need(type(request['next_intent_id']) is str and request['next_intent_id'].strip() and request['next_intent_id']!=claim['request_id'] and request['next_intent_id']!=((claim.get('new_intent_lineage') or {}).get('next_intent_id')),'next independent intent reuses prior request/intent')
    output_path(request['output']);output_path(request['flow_output']);output_path(request['evidence_output'])
    output_path(request['bound_output'],exists=request['phase']=='finish_emit')
    for name in ('claim','packet','native_result','before_checkpoint_sdk','after_checkpoint_sdk','first_query_sdk','first_query_frame_sdk','current_query_sdk','current_query_frame_sdk'):
        flow[name]=request[name] if request[name] is not None else ({'path':None,'sha256':None} if name=='current_query_sdk' else None)
    flow['before_save']=plain(request['before_save']);flow['after_save']=plain(request['after_save']);flow['unknown']=None
    for name in ('operator_id','next_intent_id','bound_output','flow_output'):flow[name]=request[name]
    bind={'schema':'lyd.first-join.verifier-bind-request.v3','source_revision':flow['source_revision'],'production_manifest':flow['production_manifest'],'production_root':flow['production_root'],'native_profile':flow['native_profile'],'fresh_query_sdk':request['first_query_sdk'],'fresh_query_frame_sdk':request['first_query_frame_sdk'],'ordinary_contract':flow['ordinary_contract'],'source_pin_record':flow['source_ready']['source_record'],'consumption_mode':'PROPOSAL_OPENED','output':request['bound_output']}
    if request['open_readback'] is not None:readref(request['open_readback'],cache)
    if request['phase']=='prepare_bind':need(request['bound_index'] is None,'future bound INDEX must remain NULL')
    else:
        idx=jread(readref(request['bound_index'],cache));need(Path(request['bound_index']['path']).resolve()==(Path(request['bound_output'])/'INDEX.json').resolve(),'actual bound INDEX path differs')
        exact(idx,('schema','verifier_id','entrypoint','files'),'actual bound INDEX');need(idx['schema']=='ck3-ordinary-interaction-consumption-verifier-bundle-v1' and idx['verifier_id']=='lyd-first-join-actual-save-v1' and idx['entrypoint']=='verifier.py:verify_consumption','actual bound provider identity differs')
        root=Path(request['bound_output']).resolve();seen=set()
        for row in idx['files']:
            exact(row,('path','sha256'),'bound row');need(row['path'] not in seen,'duplicate bound row');seen.add(row['path']);path=(root/row['path']).resolve();need(root in path.parents and not Path(row['path']).is_absolute(),'bound payload escapes');readref({'path':str(path),'sha256':row['sha256']},cache)
        need({'ROOT-BINDING.json','verifier.py','BIND-STATUS.json'}<=seen,'actual bound payload missing')
        record=jread((root/'ROOT-BINDING.json').read_bytes());need(record.get('inputs')==bind and record.get('actual_release') is False and record.get('registry_enabled') is False,'actual ROOT bound inputs/provenance differ')
        cfg=record['actual_binding'];need(cfg['source_pin_record']==bind['source_pin_record'] and cfg['fresh_query_sdk']==bind['fresh_query_sdk'] and cfg['fresh_query_frame_sdk']==bind['fresh_query_frame_sdk'] and cfg['consumption_mode']=='PROPOSAL_OPENED','actual bound first query/source literal differs')
    return {'flow':flow,'bind':bind,'claim':claim,'cache':cache,'before_frame':before,'after_frame':after}
def write(path,value):
    raw=json.dumps(value,ensure_ascii=False,indent=2).encode('utf-8')+b'\n'
    with path.open('xb') as file:file.write(raw)
    return {'path':str(path),'sha256':digest(raw)}
def assemble(request):
    checked=validate(request);flow=checked['flow'];out=Path(request['output']);out.mkdir(exist_ok=False)
    bind_ref=write(out/'BIND-REQUEST.actual.json',checked['bind']);write(out/'FLOW-REQUEST.actual.json',flow)
    common={'schema':'lyd.first-join.actual-observation.v2','reader_version':'lyd-join-save-consumption-verifier-v2','parser_sha256':'6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7','source_revision':flow['source_revision'],'production_manifest':flow['production_manifest']}
    obs={}
    for role in ('before','after'):
        isbefore=role=='before';env=dict(common,role=role,save=request[role+'_save'],checkpoint_sdk=request[role+'_checkpoint_sdk'],fresh_query_sdk=request['first_query_sdk'] if isbefore else None,fresh_query_frame_sdk=request['first_query_frame_sdk'] if isbefore else None,release_context_sdk=None if isbefore else request['current_query_sdk'],release_context_frame_sdk=None if isbefore else request['current_query_frame_sdk']);obs[role]=write(out/(role.upper()+'-OBSERVATION.actual.json'),env)
    bound=request['bound_index'] if request['phase']=='finish_emit' else {'path':str(Path(request['bound_output'])/'INDEX.json'),'sha256':None}
    emit=write(out/'EMIT-REQUEST.actual.json',{'schema':'lyd.first-join.evidence-emission-request.v1','bound_verifier_index':bound,'claim':request['claim'],'before_artifact':obs['before'],'after_artifact':obs['after'],'output':request['evidence_output']})
    write(out/'ROOT-BIND-ARGV.json',{'argv':[PYTHON,'-B',flow['source_ready']['binder']['path'],bind_ref['path']]})
    write(out/'ROOT-EMIT-ARGV.json',{'argv':[PYTHON,'-B',flow['source_ready']['emitter']['path'],emit['path']] if request['phase']=='finish_emit' else None})
    write(out/'REPORT.json',{'status':'ROOT_INPUT_FILES_ONLY_NO_BUSINESS_OR_RUNTIME_CALL','phase':request['phase'],'claim_ordinal':checked['claim']['claim_ordinal'],'request_id':checked['claim']['request_id'],'six_identity':checked['claim']['action_identity'],'source_baseline':BASELINE,'actual_reference_sha256':checked['cache'],'open_readback_provenance':request['open_readback'],'consumption_mode':'PROPOSAL_OPENED','actual_consumption_verified':False,'vote_conditions_added':False,'NPC_NULL_not_coerced':True,'provider_executed':False,'binder_executed':False,'emitter_executed':False,'release_called':False,'MCP_calls':0,'ROOT_later_fresh_query_still_required':True,'finish_phase_does_not_rebind':request['phase']=='finish_emit'})
    for path,want in checked['cache'].items():need(digest(Path(path).read_bytes())==want,'actual reference changed during assembly')
    rows=[{'path':p.name,'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(out.iterdir()) if p.is_file()];idx=write(out/'INDEX.json',{'schema':'lyd.r10.parameterized-proposal-inputs.v1','files':rows})
    return {'output':str(out),'index':idx,'runtime_executed':False}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',type=Path,required=True);parser.add_argument('--assemble',action='store_true');args=parser.parse_args();request=jread(args.request.read_bytes())
    result=assemble(request) if args.assemble else dict(status='READONLY_VALIDATED_NO_RUNTIME_CALL',claim_ordinal=validate(request)['claim']['claim_ordinal'])
    print(json.dumps(result,ensure_ascii=False))
