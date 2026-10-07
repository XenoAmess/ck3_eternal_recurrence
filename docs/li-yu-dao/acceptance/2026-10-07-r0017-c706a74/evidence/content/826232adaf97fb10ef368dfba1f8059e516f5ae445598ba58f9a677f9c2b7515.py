"""Write one ROOT-reviewed I4 arguments file from fresh original SDK receipts. Never enqueue."""
from pathlib import Path
from hashlib import sha256
import argparse,json,re,sys
sys.dont_write_bytecode=True
HEAD='c706a74f9d00dd842b7edce8901fb3417344fd9c'
HERE=Path(__file__).resolve().parent
DECISIONS={'lyd_study_decision','lyd_change_school_decision','lyd_c2_cancel_proposal_decision','lyd_c2_propose_detach_decision'}
def need(ok,message):
    if not ok:raise ValueError(message)
def ref(path):
    p=Path(path).resolve();b=p.read_bytes();return {'path':p.as_posix(),'bytes':len(b),'sha256':sha256(b).hexdigest()}
def read(path,digest):
    r=ref(path);need(r['sha256']==digest,'Actual bytes differ: '+r['path']);return json.loads(Path(path).read_bytes()),r
def exact_descriptor(row):
    need(type(row) is dict and set(row)=={'path','bytes','sha256'},'Actual exact ref3 required')
    actual=ref(row['path']);need(Path(actual['path']).resolve()==Path(row['path']).resolve() and actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'],'Actual descriptor differs');return json.loads(Path(row['path']).read_bytes())
def original_sdk(path,digest):
    wrapper,r=read(path,digest);need(not wrapper.get('isError'),'SDK error is not an action input');candidates=[]
    for x in wrapper.get('content',[]):
        if x.get('type')=='text' and isinstance(x.get('text'),str):
            try:b=json.loads(x['text'])
            except ValueError:continue
            if isinstance(b,dict) and b.get('schema')=='ck3.native-profile-receipt.v1':candidates.append(b)
    need(len(candidates)==1,'One original native-profile JSON text required')
    b=candidates[0];need(wrapper.get('structuredContent',b)==b,'SDK structured content differs from original JSON')
    return b,r
def source_event_definition(key):
    need(re.fullmatch(r'lyd\.(?:1(?:[0-2][0-9]|3[0-5])|10|11|12|13|14|200|228)',key) is not None,'I4/C2 source event outside reviewed scope')
    source=json.loads((HERE/'SOURCE-BINDING.actual.json').read_bytes())
    rel='events/lyd_c2_consent_events.txt' if key in {'lyd.200','lyd.228'} else 'events/lyd_events.txt'
    row=next(x for x in source['selected_files'] if x['relative_path']==rel)['actual_export']
    need(ref(row['path'])==row,'Frozen actual event source differs')
    t=Path(row['path']).read_text(encoding='utf-8-sig');m=re.search(r'(?m)^'+re.escape(key)+r'\s*=\s*\{',t)
    need(m is not None,'Exact source definition missing');start=m.start();depth=0;quoted=False;comment=False;escape=False
    for i in range(t.find('{',start),len(t)):
        c=t[i]
        if comment:
            if c=='\n':comment=False
            continue
        if quoted:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':quoted=False
            continue
        if c=='#':comment=True
        elif c=='"':quoted=True
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return t[start:i+1]
    raise ValueError('Incomplete exact source definition')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--consumer-source',required=True,type=Path);p.add_argument('--consumer-index-sha256',required=True)
    p.add_argument('--request-author',required=True,type=Path);p.add_argument('--request-author-sha256',required=True)
    p.add_argument('--prepared',required=True,type=Path);p.add_argument('--prepared-sha256',required=True)
    p.add_argument('--session-id',required=True)
    p.add_argument('--snapshot-sdk',required=True,type=Path);p.add_argument('--snapshot-sdk-sha256',required=True)
    p.add_argument('--query-sdk',type=Path);p.add_argument('--query-sdk-sha256')
    p.add_argument('--mode',required=True,choices=['snapshot','open-decisions','query-decision','select-decision','confirm-decision','query-event','select-event','save','G2','G3','simulation'])
    p.add_argument('--decision-key',choices=sorted(DECISIONS));p.add_argument('--event-definition')
    p.add_argument('--source-option-key');p.add_argument('--native-index',type=int)
    p.add_argument('--simulation-action',choices=['pause','resume','speed_5'])
    p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    need((a.query_sdk is None)==(a.query_sdk_sha256 is None),'Query path/hash supplied together')
    index,indexref=read(a.consumer_source/'INDEX.json',a.consumer_index_sha256)
    need(ref(a.request_author)['sha256']==a.request_author_sha256,'Actual frozen request author differs')
    need(index['source_revision']==HEAD,'Actual R17 consumer must bind approved HEAD')
    meta=exact_descriptor(index['actual_metadata']);meta_tools=exact_descriptor(meta['metadata'])
    if isinstance(meta_tools,dict):meta_tools=meta_tools['tools']
    tools={x['name']:x for x in meta_tools}
    prepared,preparedref=read(a.prepared,a.prepared_sha256)
    need(prepared['source_revision']==HEAD,'PREPARED actual source differs')
    profile=exact_descriptor(prepared['profile']);guard=exact_descriptor(prepared['guard'])
    need(a.prepared.resolve()==Path(index['run_root']).resolve()/'PREPARED.json','Actual current run PREPARED required')
    need(len(profile)==10,'Frozen final10 profile required')
    body,snapshotref=original_sdk(a.snapshot_sdk,a.snapshot_sdk_sha256)
    need(body['session_id']==a.session_id and body['profile_sha256']==prepared['profile']['sha256'],'Fresh original session/profile differs')
    need(body.get('status')=='native_snapshot_verified','Original snapshot tool receipt required')
    s=body['snapshot'];rev=s['revision'];native=s['native_revision'];actor=s['played_character']['character_id']
    need(type(rev) is int and rev>0 and rev==native+1 and s['snapshot_id']=='native:'+str(native),'Actual public/native snapshot frame differs')
    need(type(s['date_raw']) is int and type(actor) is int and actor>0,'Actual actor/date required')
    need(s['paused'] is True or (a.mode=='simulation' and a.simulation_action=='pause') or a.mode=='snapshot','Actual paused state required except explicit pause/current snapshot')
    need(type(a.session_id) is str and a.session_id,'Actual new session required')
    q=None;qref=None
    if a.query_sdk is not None:
        qbody,qref=original_sdk(a.query_sdk,a.query_sdk_sha256)
        need(qbody['session_id']==a.session_id and qbody['profile_sha256']==body['profile_sha256'],'Query actual session/profile differs')
        q=qbody['result']
        if qbody.get('status')=='native_event_query_verified':
            need(q['queried_revision']==rev and q['queried_native_revision']==native and q['queried_snapshot_id']==s['snapshot_id'] and q['date_raw']==s['date_raw'],'Fresh event query not same actual snapshot frame/date')
        elif qbody.get('status')=='native_decision_query_observed':
            need(q['game_pid']==guard['target']['pid'] and q['native_revision']==native and q['date_raw']==s['date_raw'] and q['played_character_id']==actor,'Fresh decision query PID/native frame/date/actor differs')
            need(type(q['connection_generation']) is int and q['connection_generation']>0,'Actual decision query generation required')
        else:raise ValueError('Exact original event/decision query tool receipt required')
    args={'expected_revision':rev};mode=a.mode
    if mode=='snapshot':tool='ck3_take_profile_native_snapshot_v1';args={}
    elif mode=='open-decisions':tool='ck3_open_profile_decisions_v1'
    elif mode in ['query-decision','select-decision','confirm-decision']:
        need(a.decision_key is not None,'Explicit source decision key required');args['decision_key']=a.decision_key
        tool={'query-decision':'ck3_query_profile_decision_item_v1','select-decision':'ck3_select_profile_decision_item_v1','confirm-decision':'ck3_confirm_profile_decision_outcome_v1'}[mode]
        if mode!='query-decision':
            need(q is not None and q['available'] is True and q['matching_row_count']==1 and q['row_context_reference_key']==actor,'Fresh actual decision admission/actor required')
        if mode=='confirm-decision':
            need(q['detail_root_visible'] is True and q['detail_definition_matches_target'] is True and q['detail_actor_binding_verified'] is True and q['detail_actor_reference_key']==actor and q['detail_decision_key']==a.decision_key,'Actual detail/source/actor differs')
            need(a.event_definition is not None,'Expected source event must be explicit')
            if a.decision_key=='lyd_change_school_decision':need(a.event_definition=='lyd.10','School opens first page10')
            elif a.decision_key=='lyd_c2_cancel_proposal_decision':need(a.event_definition=='lyd.228','C2 cancel expects228')
            elif a.decision_key=='lyd_c2_propose_detach_decision':need(a.event_definition=='lyd.200','C2 detach expects200')
            else:need(a.event_definition in {'lyd.'+str(n) for n in range(100,136)},'Actual current-school source event100..135 required')
            args.update(expected_outcome='event_window',expected_event_definition_key=a.event_definition)
    elif mode=='query-event':
        active=s.get('active_event');need(type(active) is dict and type(active.get('instance_id')) is int and active['instance_id']>=0,'Snapshot actual active event instance required')
        need(a.event_definition is not None,'Explicit intended source event required for read-only observation')
        source_event_definition(a.event_definition)
        args['event_instance_id']=active['instance_id'];tool='ck3_query_profile_event_window_v1'
    elif mode=='select-event':
        need(q is not None,'Fresh original event query required; do not infer event from label alone')
        c=q['current_event_window_context'];need(a.event_definition==c['event_definition_key'],'Exact current definition differs')
        need(c['root_scope']['typed_identity']['character_id']==actor,'Actual event root differs')
        need(type(c['current_event_instance_id']) is int and c['current_event_instance_id']>=0,'Actual event instance required')
        args['event_instance_id']=c['current_event_instance_id'];tool='ck3_query_profile_event_window_v1'
        if mode=='select-event':
            need(type(a.native_index) is int and a.native_index>=0 and a.source_option_key,'ROOT explicit key/index review required')
            definition=source_event_definition(a.event_definition)
            need(re.search(r'\bname\s*=\s*'+re.escape(a.source_option_key)+r'(?=\s|\})',definition) is not None,'Option key not in exact frozen source definition')
            options=[x for x in c['options'] if x['native_option_index']==a.native_index]
            need(len(options)==1 and options[0]['shown'] is True and options[0]['enabled'] is True,'Actual indexed option must be shown+enabled')
            args['option_number']=a.native_index+1;tool='ck3_select_profile_event_option_v1'
    elif mode=='simulation':
        need(a.simulation_action is not None,'Explicit bounded simulation action required');args['action']=a.simulation_action;tool='ck3_set_profile_simulation_v1'
    else:tool={'save':'ck3_save_profile_checkpoint_v1','G2':'ck3_query_profile_confucian_assembly_predicates_v1','G3':'ck3_query_profile_confucian_religious_title_v1'}[mode]
    schema=tools[tool]['inputSchema'];need(set(schema.get('required',[]))<=set(args)<=set(schema.get('properties',{})),'Current actual metadata argument shape differs')
    out=a.output.resolve();need(out.is_relative_to(Path(index['run_root']).resolve()) and not out.exists(),'Fresh output inside actual current run required')
    out.mkdir(parents=True,exist_ok=False)
    def put(name,v):
        with (out/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
    put('ARGUMENTS.actual.json',args)
    argv=[sys.executable,'-B','-X','utf8',str(a.request_author),'--consumer-source',str(a.consumer_source),'--consumer-index-sha256',a.consumer_index_sha256,'--tool',tool,'--arguments',str(out/'ARGUMENTS.actual.json'),'--output',str(out/'REQUEST.actual.json')]
    put('AUTHOR-REQUEST-ARGV.json',{'argv':argv,'executed':False})
    put('RESULT.source-only.json',{'status':'ONE_ARGUMENT_FILE_AUTHORED_NOT_ENQUEUED','source_head':HEAD,'prepared':preparedref,'consumer_index':indexref,'snapshot_SDK':snapshotref,'fresh_query_SDK':qref,'actual_frame':{'actor':actor,'date_raw':s['date_raw'],'public_revision':rev,'native_revision':native,'snapshot_id':s['snapshot_id'],'wallet':{k:s['played_character_'+k] for k in ['gold','piety','prestige']}},'tool':tool,'arguments':ref(out/'ARGUMENTS.actual.json'),'ROOT_reviewed_source_option_key':a.source_option_key,'ROOT_reviewed_native_index':a.native_index,'source_key_to_index_association':'Explicit ROOT review; native options do not publish localization/source keys, so no automatic ordinal inference.','future_enqueued':False,'SDK_calls':0,'game_calls':0,'save_body_reads':0,'formal_credit':None})
    print(json.dumps({'arguments':ref(out/'ARGUMENTS.actual.json'),'request_author_argv':ref(out/'AUTHOR-REQUEST-ARGV.json'),'executed':False}));return 0
if __name__=='__main__':raise SystemExit(main())
