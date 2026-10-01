"""Read only R0140 original files; keep failed research outcome and no-day scope."""
import datetime,hashlib,importlib.util,json,pathlib,shutil,subprocess
import sys
sys.dont_write_bytecode=True

BASE=pathlib.Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-selector-causality-research-attempt-01')
E=pathlib.Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a04/scoped-ui-research-attempt-01')
OUT=BASE/'R0140-failed-UI-monitor-diagnostic-attempt-03'
S=pathlib.Path('C:/w/e2cap1001b/ck3_autonomous_player/src/xar_autoplayer/simulation')
RAKALY=pathlib.Path('D:/workspace/ck3_native_war_ai_promo_work/episode01-effect-save-attempt-008/rakaly-0.8.19-x86_64-pc-windows-msvc/rakaly.exe')

def identity(p):
    p=pathlib.Path(p)
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest().upper()
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha}
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def write(p,o):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
def mod(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    OUT.mkdir(exist_ok=False);checks=[];sources=[]
    def gate(name,ok):
        checks.append({'name':name,'pass':bool(ok)})
        if not ok:raise ValueError(name)
    def bound(o):
        p=pathlib.Path(o['path']);a=identity(p)
        gate('original SHA '+str(p),a['bytes']==o['bytes'] and a['sha256']==o['sha256'].upper())
        return p
    def exact(p,label):
        target=OUT/label;shutil.copyfile(p,target);sources.append({'original':identity(p),'exact_copy':identity(target)})
    begin_path,end_path,save_path=(E/(n+'.json') for n in ('variable-monitor-begin','failed-ui-monitor-end','before-pre-ui-checkpoint-saved-pair'))
    begin,end,saved=map(read,(begin_path,end_path,save_path))
    for p in (begin_path,end_path,save_path,pathlib.Path(__file__),S/'knight_variable_monitor_projection.py',S/'knight_causal_save_projection.py'):
        exact(p,p.name)
    gate('same original frozen config',begin['source_binding']==end['source_binding']==saved['source_binding'])
    config_path=bound(saved['source_binding']);config=read(config_path);exact(config_path,'current-run-bindings-exact.json')
    gate('actual source commit/DLL pin',config['source_commit']=='0bb40ba1495c4bb15f24e152799d1f62eb1a2420' and identity(config['bridge_dll'])['sha256']=='405040213C99F1FBC73AC2C9236EDBED7E2DD416289F87431D687FB366D167D3')
    gate('failed before UI no day markers',end['research_status']=='RED_UI_ADMISSION_NO_DAY_ADVANCE' and end['day_advance_count']==0 and end['normal_research_lifecycle_complete'] is False and not (E/'one-day-intent.json').exists() and not (E/'one-day-finished.json').exists())
    connections=[]
    for name,w,status in (('begin',begin,'armed'),('abort-finish',end,'drained')):
        receipt=read(bound(w['native_receipt']['response']));request=read(bound(w['native_receipt']['request']))
        exact(pathlib.Path(w['native_receipt']['response']['path']),name+'-native-response-exact.json')
        exact(pathlib.Path(w['native_receipt']['request']['path']),name+'-native-request-exact.json')
        gate(name+' exact original additive body',receipt['result']=='CALL_COMPLETED' and receipt['body']==w['native_envelope'] and receipt['body']['accepted'] is True and receipt['body']['status']==status and receipt['body']['scoped_variable_monitor']==w['scoped_variable_monitor'] and w['exact_payload_path']==['scoped_variable_monitor'])
        gate(name+' same original token/scope',request['action']=='private_phase_trace' and request['monitor_sequence_token']==config['monitor_sequence_token'] and w['scoped_variable_monitor']['character_ids']==[config['victim_id'],config['killer_id']])
        c=tuple(receipt['driver_state'][key] for key in ('pipe_name','connection_generation','bridge_pid'));connections.append(c)
        session=config['native_session_binding']
        gate(name+' source session/date',all(w['source_values'][k]==v for k,v in session.items()) and w['source_values']['paused'] is True and w['source_values']['date_raw']==config['before_date_raw'])
    initial,final=begin['scoped_variable_monitor'],end['scoped_variable_monitor']
    gate('arm/drain flags and uninstall',initial['detours_uninstalled'] is False and final['detours_uninstalled'] is True and final['failure_flags']==0 and final['truncated'] is False)
    gate('all actual paused rows flags0/date',all(r['failure_flags']==0 and r['date_raw']==config['before_date_raw'] for r in final['records']))
    gate('actual initial rows exact retained prefix',final['records'][:len(initial['records'])]==initial['records'])
    gate('seven definition prearm stable and distinct',initial['prearmed_event_definitions']==final['prearmed_event_definitions'] and len(final['prearmed_event_definitions'])==7 and len({p['compiled_immediate_root_token'] for p in final['prearmed_event_definitions']})==7)
    pure=mod('frozen_monitor',S/'knight_variable_monitor_projection.py')
    same_thread_error=None
    try:pure.validate_variable_monitor(final,character_ids=final['character_ids'],expected_monitor_token=config['monitor_sequence_token'],before_date_raw=config['before_date_raw'],after_date_raw=config['before_date_raw'],expected_thread=final['records'][0]['thread_id'])
    except ValueError as e:same_thread_error=str(e)
    gate('reproduced actual overly strict old same-thread gate',same_thread_error=='variable monitor: every record same declared window')
    projection=pure.validate_variable_monitor(final,character_ids=final['character_ids'],expected_monitor_token=config['monitor_sequence_token'],before_date_raw=config['before_date_raw'],after_date_raw=config['before_date_raw'],expected_thread=None)
    gate('zero actual writers and house calls',projection['actual_write_pairs']==[] and projection['original_house_predicate_pairs']==[])
    raw=bound(saved['immutable']);sr=read(bound(saved['save']['response']));sreq=read(bound(saved['save']['request']));snap=read(bound(saved['snapshot']['response']))
    connections.append(tuple(sr['driver_state'][key] for key in ('pipe_name','connection_generation','bridge_pid')))
    gate('original saved receipt exact actor/date/hash',sr['result']=='CALL_COMPLETED' and sr['body']==saved['save_body'] and sr['body']['accepted'] is True and sr['body']['checkpoint']['status']=='saved' and sr['body']['checkpoint']['episode_run_id']==config['native_session_binding']['episode_run_id'] and sr['body']['checkpoint']['date_raw']==config['before_date_raw'] and sr['body']['checkpoint']['sha256'].upper()==identity(raw)['sha256'])
    gate('checkpoint original expected revision',sreq['tool']=='ck3_save_checkpoint' and sreq['arguments']['expected_revision']==snap['body']['revision'] and all(saved['source_values'][k]==snap['body'][k] for k in ('date_raw','paused','revision','native_revision','snapshot_id')))
    gate('monitor/save same real process connection',len(set(connections))==1 and connections[0][1:]==(config['native_session_binding']['connection_generation'],config['native_session_binding']['bridge_pid']))
    gate('pinned original Rakaly',identity(RAKALY)['sha256']=='E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D')
    melted=OUT/'before-preUI-melted.ck3';argv=[str(RAKALY),'melt',str(raw),'--unknown-key','stringify','--format','ck3','--out',str(melted)]
    write(OUT/'melt-command.json',{'argv':argv,'raw':identity(raw),'rakaly':identity(RAKALY)})
    stdout,stderr=OUT/'melt.stdout.bin',OUT/'melt.stderr.bin'
    with stdout.open('xb') as o,stderr.open('xb') as e:process=subprocess.run(argv,stdout=o,stderr=e,check=False)
    write(OUT/'melt-process.json',{'returncode':process.returncode,'stdout':identity(stdout),'stderr':identity(stderr)})
    gate('actual strict decoder exit0/stderr empty',process.returncode==0 and stderr.stat().st_size==0 and melted.is_file())
    import importlib,sys;sys.path.insert(0,str(S.parents[1]));parsed=importlib.import_module('xar_autoplayer.simulation.knight_causal_save_projection');text=melted.read_text(encoding='utf-8-sig');states=[]
    for cid in final['character_ids']:
        char=parsed.character_snapshot(text,cid)
        path=OUT/(str(cid)+'-preUI-exact.txt');path.write_text(char.pop('raw_block')+'\n',encoding='utf-8',newline='\n');char['exact_extract']=identity(path)
        matches=[]
        for variables in parsed.find_key_blocks(char['entries'],'variables'):
            rows=parsed.one(variables['entries'],'data')
            if rows is None:continue
            for row in rows:
                if isinstance(row['value'],list) and parsed.one(row['value'],'flag')=='"signature_weapon"':
                    matches.append({'path':variables['path'],'full_saved_row':row['value']})
        gate(str(cid)+' unique saved signature row',len(matches)<=1)
        char['signature_weapon_saved_state']={'present':bool(matches),'row':matches[0] if matches else None,'evidence_level':'strict same-run pre-UI saved endpoint'}
        states.append(char)
    report={'schema_version':1,'kind':'R0140_ACTUAL_FAILED_PRE_UI_MONITOR_DIAGNOSTIC','research_status':'RED_UI_ADMISSION_NO_DAY_ADVANCE',
        'created_at_utc':datetime.datetime.now(datetime.UTC).isoformat(),'checks':checks,'sources':sources,
        'raw_original_save':identity(raw),'melted':identity(melted),'native_connection':connections[0],
        'actual_prearmed_definitions':final['prearmed_event_definitions'],'actual_original_monitor_records':final['records'],
        'original_monitor_projection_without_invalid_cross_thread_assumption':projection,'strict_saved_initial_states':states,
        'old_same_thread_rejection':same_thread_error,
        'actual_initial_native_signature':{str(cid):[r for r in final['records'] if r['character_id']==cid and r['boundary']=='original_owner_return'] for cid in final['character_ids']},
        'day_advanced':False,'six_gap_evidence_closed':False,'whole_game_mutable_bundle_complete':False,'sole_cause_proven':False,
        'initial_arm_values_are_character_state':False,'cached_final_owner_values_reread':False,
        'limits':['Seven source-bound prearmed roots are not seven actually executed notifications.','No write is published in this observed failed admission window; coverage remains only the two-character signature setter contract.','33437 native original getter reports read=true/present=false. 34120 has no native getter here, so native initial state is unobserved.','Single saved endpoint gives initial character/variable state only; no post-UI checkpoint, RNG equality, day transition or full case closure.'],
        'game_calls':0,'desktop_inputs':0,'master_intake':False}
    dest=OUT/'R0140-monitor-initial-state-diagnostic-a03.json';write(dest,report)
    print(json.dumps({'receipt':identity(dest),'saved_initial_states':[{'cid':c['character_id'],'life':c['status'],'signature':c['signature_weapon_saved_state']} for c in states],'actual_write_count':0,'old_gate_error':same_thread_error}))

if __name__=='__main__':main()
