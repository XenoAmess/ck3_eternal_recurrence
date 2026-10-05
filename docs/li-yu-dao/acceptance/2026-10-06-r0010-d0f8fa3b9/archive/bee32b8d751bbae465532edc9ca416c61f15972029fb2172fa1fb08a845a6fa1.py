"""ROOT-only immutable-reference preparation. Does not bind, release, or send."""
from pathlib import Path
import argparse, ast, hashlib, json, math, re

ROOT = Path(__file__).resolve().parent
EXTERNAL = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
PYTHON = 'C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
BASE = EXTERNAL / 'r9-lyd-claim-consumption-source-author-20261005-001/actual-source-ready-006-001'
BASE_PROVIDER = BASE / 'unbound-bundle-010/verifier.py'
BASE_PROVIDER_SHA = '81132c4a52f377ad0efaaa37c9aad532002748488cf9b515f3a5bc4a2b577b0f'
BASE_BINDER = BASE / 'bind_verifier.py'
BASE_BINDER_SHA = '7f70b295ad0f381ea19ae20b41b8296841ebde9b96ce75001e461492dfb0bcc2'
BASE_EMITTER_SHA = 'dbd43c930650f7c17defbcc7a5341d5f7ecb3c58b6696d367ef5f4cc1a90f0f0'
CONTRACT_SHA = 'e0a96aa39626df166270d3d5467a8e4d57cec77d7577cebcced03983feba5fa3'
HOST_SHA = 'f567bff41d03b6c59d195df8ff62ecab1a523962de3217d397c5264d1ed2d89b'
OLD_HEAD = '54457b371e947edb86903c2ebd578034f02695db'
KEY = 'lyd_c2_propose_join_interaction'
IDENTITY_FIELDS = {'game_pid','process_create_time','actor_id','recipient_id','interaction_key','action'}
FIELDS = {'schema','source_revision','source_ready','production_manifest','production_root','native_profile',
    'ordinary_contract','host_module','process_identity','claim','packet','native_result','unknown',
    'before_save','before_checkpoint_sdk','after_save','after_checkpoint_sdk','first_query_sdk',
    'first_query_frame_sdk','current_query_sdk','current_query_frame_sdk','bound_output','flow_output',
    'operator_id','next_intent_id'}
SOURCE_FIELDS = {'author_index','provider','binder','emitter','source_record','source_readback'}

def need(ok, message):
    if not ok: raise ValueError(message)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def jread(raw):
    def pairs(items):
        value={}
        for key,item in items:
            need(key not in value,'duplicate JSON field');value[key]=item
        return value
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def exact(value, keys, label):
    need(isinstance(value,dict) and set(value)==set(keys),'closed '+label+' shape differs')
    return value

def readref(ref, cache, *, sized=False):
    exact(ref,('path','bytes','sha256') if sized else ('path','sha256'),'immutable reference')
    need(isinstance(ref['path'],str) and Path(ref['path']).is_absolute(),'absolute immutable path required')
    need(isinstance(ref['sha256'],str) and re.fullmatch('[0-9a-f]{64}',ref['sha256']),'full lowercase SHA required')
    raw=Path(ref['path']).read_bytes()
    need(sha(raw)==ref['sha256'],'immutable bytes differ')
    if sized: need(type(ref['bytes']) is int and ref['bytes']==len(raw),'immutable size differs')
    cache[str(Path(ref['path']).resolve())]=ref['sha256']
    return raw

def pointer(value, path):
    need(isinstance(path,str) and path.startswith('/'),'explicit process receipt JSON pointer required')
    for token in path[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~')
        need(isinstance(value,dict) and token in value,'actual process receipt field missing')
        value=value[token]
    return value

def astparts(raw):
    tree=ast.parse(raw)
    functions={node.name:ast.dump(node,include_attributes=False) for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
    constants={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError):pass
    return functions,constants

def unchanged_consumption_functions(candidate_raw):
    base_raw=BASE_PROVIDER.read_bytes();need(sha(base_raw)==BASE_PROVIDER_SHA,'frozen006 provider differs')
    before_functions,before_constants=astparts(base_raw);functions,constants=astparts(candidate_raw)
    need(functions==before_functions,'consumption/query/once functions changed: separate product review required')
    allowed={'PINNED_SOURCE_RECORD_REF','PINNED_SOURCE_SUMMARY','RUNTIME_ROWS'}
    need(set(constants)==set(before_constants),'provider constant inventory differs')
    for name,value in before_constants.items():
        if name not in allowed:need(constants[name]==value,'protected provider constant differs: '+name)
    need(constants.get('PINNED_ROOT_BINDING') is None,'source-ready provider is already process-bound')
    return constants

def checked_source(request,cache):
    ready=exact(request['source_ready'],SOURCE_FIELDS,'reviewed source-ready references')
    index_raw=readref(ready['author_index'],cache);index=jread(index_raw)
    need(isinstance(index.get('files'),list),'actual source-ready INDEX has no file rows')
    base=Path(ready['author_index']['path']).parent.resolve();indexed={}
    for row in index['files']:
        exact(row,('path','bytes','sha256'),'source-ready INDEX row')
        path=(base/row['path']).resolve();need(base in path.parents,'source-ready INDEX path escapes')
        raw=readref({'path':str(path),'bytes':row['bytes'],'sha256':row['sha256']},cache,sized=True)
        need(str(path) not in indexed,'duplicate source-ready INDEX target');indexed[str(path)]=sha(raw)
    values={name:readref(ref,cache,sized=name=='source_record') for name,ref in ready.items() if name!='author_index'}
    for name in ('provider','binder','emitter','source_readback'):
        need(indexed.get(str(Path(ready[name]['path']).resolve()))==ready[name]['sha256'],'source-ready file not bound by author INDEX: '+name)
    constants=unchanged_consumption_functions(values['provider'])
    need(constants['PINNED_SOURCE_RECORD_REF']==ready['source_record'],'provider source record is not explicit actual reference')
    record=jread(values['source_record']);summary=jread(values['source_readback'])
    need(summary==constants['PINNED_SOURCE_SUMMARY'],'provider source summary differs from indexed actual readback')
    need(record.get('source',{}).get('head')==request['source_revision']==summary.get('source',{}).get('head'),
         'source record/readback/new HEAD differ')
    need(summary.get('status')=='ACTUAL_FROZEN_SOURCE_PINS_MATCH','actual source readback is not qualified')
    binder_baseline=BASE_BINDER.read_bytes();need(sha(binder_baseline)==BASE_BINDER_SHA,'frozen006 binder differs')
    binder_functions,_=astparts(values['binder']);baseline_binder_functions,_=astparts(binder_baseline)
    need(set(binder_functions)==set(baseline_binder_functions),'binder function inventory differs')
    for name,value in baseline_binder_functions.items():
        if name!='load_template':need(binder_functions[name]==value,'protected binder function differs: '+name)
    # The reviewed successor may only change its explicit local template path.
    path_node=ast.parse(values['binder']);load=next(n for n in path_node.body if isinstance(n,ast.FunctionDef) and n.name=='load_template')
    old_load=next(n for n in ast.parse(binder_baseline).body if isinstance(n,ast.FunctionDef) and n.name=='load_template')
    need(len(load.body)==len(old_load.body) and isinstance(load.body[0],ast.Assign),'load_template shape differs')
    path_assignment=load.body[0]
    need(len(path_assignment.targets)==1 and isinstance(path_assignment.targets[0],ast.Name) and path_assignment.targets[0].id=='p',
         'binder template path assignment differs')
    rhs=path_assignment.value
    need(isinstance(rhs,ast.BinOp) and isinstance(rhs.op,ast.Div) and isinstance(rhs.left,ast.Name) and rhs.left.id=='ROOT'
         and isinstance(rhs.right,ast.Constant) and isinstance(rhs.right.value,str),'binder explicit local template path required')
    actual_template=(Path(ready['binder']['path']).parent/rhs.right.value).resolve()
    need(actual_template==Path(ready['provider']['path']).resolve(),'binder does not load the reviewed provider')
    load.body[0]=old_load.body[0]
    need(ast.dump(load,include_attributes=False)==ast.dump(old_load,include_attributes=False),'binder template loader logic changed')
    need(sha(values['emitter'])==BASE_EMITTER_SHA,'actual evidence emitter changed: separate review required')
    prod=jread(readref(request['production_manifest'],cache))
    need(prod.get('git_sha')==request['source_revision'] and prod.get('files')==constants['RUNTIME_ROWS'],
         'new actual production manifest differs from reviewed provider runtime rows')
    root=Path(request['production_root']).resolve();need(root.is_absolute(),'absolute production root required')
    for row in prod['files']:
        path=(root/row['path']).resolve();need(root in path.parents,'production runtime path escapes')
        readref({'path':str(path),'bytes':row['size'],'sha256':row['sha256']},cache,sized=True)
    return constants,summary

def sdk(ref,cache):
    receipt=jread(readref(ref,cache))
    need(receipt.get('isError') is False and isinstance(receipt.get('structuredContent'),dict),'actual SDK error/unknown is not success')
    return receipt['structuredContent']

def process_values(process, receipt):
    exact(process,('game_pid','process_create_time','process_create_filetime','receipt','receipt_fields'),'actual process identity')
    need(type(process['game_pid']) is int and 0<process['game_pid']<2**32,'actual PID must be positive uint32')
    creation=process['process_create_time'];need(type(creation) in (int,float) and math.isfinite(creation) and creation>0,'actual process creation time missing')
    need(type(process['process_create_filetime']) is int and 0<process['process_create_filetime']<2**64,'actual raw FILETIME must be positive uint64')
    fields=exact(process['receipt_fields'],('game_pid','process_create_time','process_create_filetime'),'process receipt selectors')
    for name in fields:
        actual=pointer(receipt,fields[name]);need(type(actual) is type(process[name]) and actual==process[name],'actual process receipt field differs: '+name)
    return process

def shape(request):
    exact(request,FIELDS,'R10 preparation request')
    need(request['schema']=='ck3-r10-repeated-join-flow-preparation-v1','R10 schema differs')
    unresolved=[]
    def scan(value,prefix):
        if value is None:unresolved.append(prefix)
        elif isinstance(value,dict):
            for key,item in value.items():scan(item,prefix+'.'+key)
    for key in FIELDS-{'schema','native_result','unknown','first_query_frame_sdk','current_query_frame_sdk'}:
        scan(request[key],key)
    return sorted(unresolved)

def validate(request):
    pending=shape(request);need(not pending,'actual ROOT inputs remain NULL: '+','.join(pending))
    head=request['source_revision']
    need(isinstance(head,str) and re.fullmatch('[0-9a-f]{40}',head) and head!=OLD_HEAD,'actual new reviewed R10 HEAD required')
    cache={};constants,summary=checked_source(request,cache)
    need(request['ordinary_contract']['sha256']==CONTRACT_SHA and request['host_module']['sha256']==HOST_SHA,'stable contract/host source differs')
    readref(request['ordinary_contract'],cache);readref(request['host_module'],cache)
    profile=jread(readref(request['native_profile'],cache))
    base={'schema_version','guard_profile','guard_profile_sha256','userdir','evidence_directory','game_version','state_directory','dll','injector'}
    exact(profile,base|({'normal_exit_source_inventory'} if 'normal_exit_source_inventory' in profile else set()),'native profile')
    need(type(profile['schema_version']) is int and profile['schema_version']==1 and profile['game_version']=='1.20.0.3','actual native profile version differs')
    if 'normal_exit_source_inventory' in profile:readref(profile['normal_exit_source_inventory'],cache)
    for name in ('dll','injector'):
        readref(profile[name],cache)
        target=summary['actual_release_targets'][name]
        need(profile[name]['sha256']==target['sha256'] and Path(profile[name]['path']).resolve()==Path(target['path']).resolve(),'profile/new Release target differs')
    guard=jread(readref({'path':profile['guard_profile'],'sha256':profile['guard_profile_sha256'].lower()},cache))
    process=request['process_identity'];process_receipt=jread(readref(process['receipt'],cache))
    process_values(process,process_receipt);creation=process['process_create_time']
    target=guard.get('target',{})
    need(type(target.get('pid')) is int and target['pid']==process['game_pid'] and
         type(target.get('process_create_time')) is type(creation) and target['process_create_time']==creation,'guard process identity differs')
    claim=jread(readref(request['claim'],cache));identity=exact(claim.get('action_identity'),IDENTITY_FIELDS,'six stable once identity')
    need(identity['game_pid']==process['game_pid'] and identity['process_create_time']==creation and identity['interaction_key']==KEY and identity['action']=='initiate_ordinary','actual same-process claim identity differs')
    need(claim.get('schema')=='ck3-ordinary-interaction-once-claim-v1' and claim.get('status')=='claimed_result_unknown_no_retry','actual immutable UNKNOWN claim required')
    for name in ('actor_id','recipient_id'):need(type(identity[name]) is int and 0<identity[name]<2**32-1,'actual full character ID differs')
    need(identity['actor_id']==31254 and identity['recipient_id']==65866,'reviewed first-join product scope differs')
    binding=claim['binding'];provenance=claim['host_provenance']
    need(provenance['profile_sha256']==request['native_profile']['sha256'] and provenance['guard_profile_sha256']==profile['guard_profile_sha256'].lower() and provenance['process_create_time']==creation,'claim original host provenance differs')
    for name in ('packet','native_result','unknown'):
        if request[name] is not None:readref(request[name],cache)
    need(request['native_result'] is not None or request['unknown'] is not None,'actual native receipt or explicit transport-unknown sidecar required')
    packet=Path(request['claim']['path']).with_suffix('.packet.bin')
    need(Path(request['packet']['path']).resolve()==packet.resolve(),'claim packet path differs')
    # SDK flags are observations only; native pending and UNKNOWN remain pending/UNKNOWN.
    before=sdk(request['before_checkpoint_sdk'],cache);after=sdk(request['after_checkpoint_sdk'],cache)
    for receipt,key in ((before,'before_save'),(after,'after_save')):
        readref(request[key],cache);checkpoint=receipt.get('result',{}).get('checkpoint',{})
        need(checkpoint.get('status')=='saved' and checkpoint.get('sha256')==request[key]['sha256'],'actual immutable checkpoint SDK/save differs')
    query=sdk(request['first_query_sdk'],cache);current=sdk(request['current_query_sdk'],cache)
    for receipt,ref in ((query,request['first_query_frame_sdk']),(current,request['current_query_frame_sdk'])):
        own=receipt.get('snapshot_after',receipt.get('snapshot'))
        need((ref is None)==isinstance(own,dict),'query snapshot requires exactly its own frame or explicit same-frame SDK')
        frame=own if ref is None else sdk(ref,cache).get('snapshot_after',{})
        need(isinstance(frame,dict) and frame,'actual query frame is missing')
        result=receipt.get('result',{});qc=result.get('character_interaction_ordinary_context',{})
        need(all(type(frame.get(name)) is int and frame[name]>0 for name in ('revision','native_revision','date_raw')),
             'actual query frame integers are missing')
        diagnostics=frame.get('diagnostics',{})
        need(type(diagnostics.get('bridge_pid')) is int and diagnostics['bridge_pid']==identity['game_pid'] and
             type(diagnostics.get('connection_generation')) is int and diagnostics['connection_generation']>0 and
             type(qc.get('connection_generation')) is int and qc['connection_generation']==diagnostics['connection_generation'],
             'actual query process/generation frame differs')
        need(result.get('step')=='query-character-interaction-ordinary-v1' and result.get('accepted') is True and
             result.get('status')=='available' and result.get('read_only') is True and
             qc.get('schema')=='ck3-character-interaction-ordinary-context-v1' and qc.get('status')=='available' and
             qc.get('read_only') is True and qc.get('business_postcondition_verified') is False,'actual readonly query terms differ')
        for flag in ('source_code_pins_verified','actor_binding_verified','recipient_binding_verified','owner_thread_verified','tls_verified','frame_verified'):
            need(qc.get(flag) is True,'actual query proof missing: '+flag)
        need(receipt.get('profile_sha256')==provenance['profile_sha256'] and receipt.get('session_id')==provenance['session_id'] and receipt.get('pipe_name')==provenance['pipe_name'],'actual query profile/session/pipe differs')
        for name,want in (('queried_revision',frame.get('revision')),('queried_native_revision',frame.get('native_revision')),('queried_snapshot_id',frame.get('snapshot_id'))):
            need(type(result.get(name)) is type(want) and result.get(name)==want,'actual query exact frame differs: '+name)
        need(qc.get('ready_to_initiate') is True and qc.get('shown') is True and qc.get('can_send') is True and qc.get('active_event_present') is False and qc.get('incoming_interaction_present') is False,'fresh actual CanSend context required')
        for name,want in (('player_character_id',identity['actor_id']),('recipient_id',identity['recipient_id']),('game_pid',identity['game_pid']),('snapshot_revision',frame.get('native_revision')),('date_raw',frame.get('date_raw'))):
            need(type(qc.get(name)) is type(want) and qc.get(name)==want,'actual query full identity differs: '+name)
        need(qc.get('interaction_key')==KEY and frame.get('paused') is True and frame.get('map_ready') is True,'actual query is not the scoped paused map')
    need(query['result']['queried_revision']==binding['revision'] and query['result']['queried_native_revision']==binding['native_revision'],'actual original query differs from original claim')
    current_own=current.get('snapshot_after',current.get('snapshot'))
    current_frame=current_own if isinstance(current_own,dict) else sdk(request['current_query_frame_sdk'],cache)['snapshot_after']
    need(current['result']['queried_native_revision']>=after['snapshot_after']['native_revision'] and
         current_frame['date_raw']>=after['snapshot_after']['date_raw'],'fresh CanSend predates consumed JOIN save')
    for name in ('operator_id','next_intent_id'):need(isinstance(request[name],str) and request[name].strip(),'explicit ROOT '+name+' required')
    for name in ('bound_output','flow_output'):
        path=Path(request[name]);need(path.is_absolute() and EXTERNAL in path.resolve().parents and not path.exists(),'fresh external '+name+' required')
    for path,digest in cache.items():need(sha(Path(path).read_bytes())==digest,'reference changed during readonly check')
    return {'cache':cache,'identity':identity,'summary':summary}

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as file:json.dump(value,file,ensure_ascii=False,indent=2);file.write('\n')

def prepare(request):
    checked=validate(request);out=Path(request['flow_output']);out.mkdir(exist_ok=False)
    bind={'schema':'lyd.first-join.verifier-bind-request.v3','source_revision':request['source_revision'],
        'production_manifest':request['production_manifest'],'production_root':request['production_root'],
        'native_profile':request['native_profile'],'fresh_query_sdk':request['first_query_sdk'],
        'fresh_query_frame_sdk':request['first_query_frame_sdk'],'ordinary_contract':request['ordinary_contract'],
        'source_pin_record':request['source_ready']['source_record'],'consumption_mode':'FINAL_JOIN','output':request['bound_output']}
    write(out/'BIND-REQUEST.json',bind)
    common={'schema':'lyd.first-join.actual-observation.v2','reader_version':'lyd-join-save-consumption-verifier-v2',
        'parser_sha256':'6c1ba1006cd0dd5055c11115701b60a74562b0f23d91b756a3d9322e7d055cb7',
        'source_revision':request['source_revision'],'production_manifest':request['production_manifest']}
    for role in ('before','after'):
        before=role=='before'
        write(out/(role.upper()+'-OBSERVATION.json'),dict(common,role=role,save=request[role+'_save'],
            checkpoint_sdk=request[role+'_checkpoint_sdk'],fresh_query_sdk=request['first_query_sdk'] if before else None,
            fresh_query_frame_sdk=request['first_query_frame_sdk'] if before else None,
            release_context_sdk=None if before else request['current_query_sdk'],
            release_context_frame_sdk=None if before else request['current_query_frame_sdk']))
    write(out/'ROOT-CLI.json',{'bind_argv':[PYTHON,'-B',request['source_ready']['binder']['path'],str(out/'BIND-REQUEST.json')],
        'emit_argv_template':[PYTHON,'-B',request['source_ready']['emitter']['path'],None],
        'release_argv_template':None,'binder_executed':False,'emitter_executed':False,'release_executed':False,'MCP_calls':0})
    write(out/'PREPARED.json',{'schema':'ck3-r10-repeated-join-flow-prepared-v1','status':'REFERENCES_PREPARED_CONSUMPTION_NOT_VERIFIED',
        'source_revision':request['source_revision'],'source_ready':request['source_ready'],'actual_six_once_identity':checked['identity'],
        'actual_process_receipt':request['process_identity'],'observed_reference_sha256':checked['cache'],
        'original_claim_unmodified':True,'old_R9_unknown_success_credit':False,'actual_consumption_verified':False,
        'registry_enabled':False,'host_release_called':False,'permit_written':False,'MCP_calls':0})
    rows=[{'path':p.name,'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())} for p in sorted(out.iterdir()) if p.is_file()]
    write(out/'INDEX.json',{'schema':'ck3-r10-root-flow-preparation-index-v1','files':rows})
    return {'output':str(out),'index_sha256':sha((out/'INDEX.json').read_bytes()),'status':'REFERENCES_PREPARED_CONSUMPTION_NOT_VERIFIED'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--prepare',action='store_true',help='Only write request/observation files; never run their commands')
    args=parser.parse_args();request=jread(args.request.read_bytes())
    if args.prepare:result=prepare(request)
    else:
        pending=shape(request)
        result={'status':'PENDING_ROOT_ACTUAL_INPUTS','pending_fields':pending} if pending else dict(validate(request),status='READONLY_REFERENCES_PRESENT_CONSUMPTION_NOT_VERIFIED')
    print(json.dumps(result,ensure_ascii=False,indent=2))
