import copy,hashlib,json
from pathlib import Path
import pytest
from verify import EvidenceError,admit_locked,frame,r12,r13,audit_manifest
OUT=Path(__file__).parent
B={'pid':4242,'generation':1,'actor':707,'episode':'synthetic-normal-campaign','army_id':18,'native_carmy_id':18,'process_create_time_100ns':123456}
def f(route,revision):
    return {'snapshot_id':'native:'+str(revision),'revision':revision+1,'native_revision':revision,
        'date_raw':100000,'paused':True,'map_ready':True,'episode_run_id':'synthetic-normal-campaign',
        'played_character':{'character_id':707,'alive':True},'diagnostics':{'bridge_pid':4242,'connection_generation':1},
        'player_armies':[{'army_id':18,'owner_character_id':707,'current_province_id':1036,'controllable':True,
            'route_province_ids':route,'route_read_status':'complete_nonempty' if route else 'complete_empty','route_source_count':len(route),
            'in_combat':False,'retreating':False,'move_target_observable':bool(route),'move_target_province_id':route[-1] if route else None}]}
def observation(route,revision,*,date=100072,province=1036,progress=60001):
    snapshot=f(route,revision);snapshot['date_raw']=date;snapshot['player_armies'][0].update(current_province_id=province,army_state='embarked',army_state_code=4)
    movement={'source':'native_current_route_edge','status':'available' if route else 'not_applicable',
        'normalized_edge_progress':None if not route else {'raw':progress,'scale':100000},
        'loaded_movement_lock_cutoff':{'raw':50000,'scale':100000},'first_route_edge_remaining_duration':None if not route else {'raw':200000,'scale':100000}}
    strength={'step':'query-army-strengths-v1','accepted':True,'status':'available','army_strengths':[{'status':'available','army_id':18,'native_carmy_id':18,'current_movement_progress':movement}],
        'queried_snapshot_id':snapshot['snapshot_id'],'queried_revision':snapshot['revision'],'queried_native_revision':snapshot['native_revision'],'queried_date_raw':date,'queried_connection_generation':1,'queried_episode_run_id':B['episode']}
    return frame(snapshot,strength,B)
def action(step,before):
    if step.startswith('move-army-'):
        pieces=step.split('-');request={'tool':'ck3_move_army','arguments':{'army_id':int(pieces[2]),'target_province_id':int(pieces[4]),'expected_revision':before['snapshot']['revision']}}
    else:request={'tool':'ck3_execute_step','arguments':{'step':step,'expected_revision':before['snapshot']['revision']}}
    return request,{'accepted':True,'step':step,'status':'submitted'}
def preview(before,target,route):return {'accepted':True,'queried_native_revision':before['snapshot']['native_revision'],
    'queried_snapshot_id':before['snapshot']['snapshot_id'],'queried_revision':before['snapshot']['revision'],
    'queried_connection_generation':before['snapshot']['diagnostics']['connection_generation'],'queried_episode_run_id':before['snapshot']['episode_run_id'],
    'route_preview':{'status':'available','army_id':18,'origin_province_id':before['province'],'target_province_id':target,'route_province_ids':route,'previewed_date_raw':before['date']}}

def test_synthetic_locked_halt_requires_applied_prefix_and_actual_arrival():
    locked=observation([8653,1034,1033],42);post=observation([8653],43);arrival=observation([],44,date=100120,province=8653)
    result=r12(locked,post,arrival,*action('halt-army-18',locked))
    assert result['arrival_province']==8653 and result['elapsed_actual_days']==2

@pytest.mark.parametrize('progress,cutoff,qualifies',[(31233,31234,False),(31234,31234,False),(31235,31234,True)])
def test_locked_numeric_boundary_uses_actual_non50000_cutoff(progress,cutoff,qualifies):
    o=observation([8653,1034,1033],42,progress=progress);o['movement']['loaded_movement_lock_cutoff']['raw']=cutoff
    if qualifies:assert admit_locked(o)['cutoff_raw']==31234
    else:
        with pytest.raises(EvidenceError):admit_locked(o)

def test_verifier_refuses_wrong_generic_move_entry_even_with_accepted_ack():
    l,p,f,a,v=r13_scene();request,response=action('move-army-18-to-1034',l)
    request={'tool':'ck3_execute_step','arguments':{'step':'move-army-18-to-1034','expected_revision':l['snapshot']['revision']}}
    with pytest.raises(EvidenceError,match='typed ck3_move_army'):r13(l,p,f,a,v,request,response,1034)

@pytest.mark.parametrize('bad',['equal','null','single','same_front_tail'])
def test_locked_admission_rejects_equal_missing_or_wrong_route_kind(bad):
    o=observation([8653,1034,1033],42)
    if bad=='equal':o['movement']['normalized_edge_progress']['raw']=50000
    elif bad=='null':o['movement']['loaded_movement_lock_cutoff']=None
    elif bad=='single':o['route']=[8653]
    else:o['route']=[8653,1034,8653]
    with pytest.raises(EvidenceError):admit_locked(o)

def test_actual_archived_r11_unlocked_control_does_not_close_locked_card():
    import zipfile
    repo=next(p for p in Path(__file__).resolve().parents if (p/'docs/ck3-native-ai/evidence/episode04-r0173-20261015/manifest.json').exists())
    directory=repo/'docs/ck3-native-ai/evidence/episode04-r0173-20261015'
    manifest=json.loads((directory/'manifest.json').read_bytes());archive=directory/manifest['archive']['path']
    raw=archive.read_bytes()
    assert len(raw)==manifest['archive']['bytes'] and hashlib.sha256(raw).hexdigest()==manifest['archive']['sha256']
    with zipfile.ZipFile(archive) as z:
        b=z.read('day21-summary.json');pin=manifest['files']['day21-summary.json']
    assert len(b)==pin['bytes'] and hashlib.sha256(b).hexdigest()==pin['sha256']
    summary=json.loads(b)
    assert manifest['machine_id']=='desktop-3fevhd2-1c74096080'
    assert summary['actual_movement_progress']['normalized_edge_progress']['raw']==9799
    with pytest.raises(EvidenceError,match='does not exceed'):
        admit_locked({'route':[8653,1034,1033],'movement':summary['actual_movement_progress']})

@pytest.mark.parametrize('bad',['ack_only','cleared','suffix_left','lost_progress','wrong_arrival','not_arrived','late'])
def test_r12_rejects_ack_only_wrong_route_or_missing_actual_endpoint(bad):
    locked=observation([8653,1034,1033],42);post=observation([8653],43);arrival=observation([],44,date=100120,province=8653)
    if bad=='ack_only':post=copy.deepcopy(locked)
    elif bad=='cleared':post['route']=[]
    elif bad=='suffix_left':post['route']=[8653,1034]
    elif bad=='lost_progress':post['movement']['normalized_edge_progress']['raw']=0
    elif bad=='wrong_arrival':arrival['province']=1036
    elif bad=='not_arrived':arrival['route']=[8653]
    else:arrival['date']=100072+24*10
    with pytest.raises(EvidenceError):r12(locked,post,arrival,*action('halt-army-18',locked))

def r13_scene():
    locked=observation([8653,1034,1033],42);post=observation([8653,1034],43)
    first=observation([1034],44,date=100096,province=8653,progress=0);arrival=observation([],45,date=100120,province=1034)
    return locked,post,first,arrival,preview(locked,1034,[8653,1034])

def test_synthetic_r13_reaches_alternate_and_does_not_stop_at_route_submission():
    l,p,f,a,v=r13_scene();result=r13(l,p,f,a,v,*action('move-army-18-to-1034',l),1034)
    assert result['actual_alternate_destination']==1034 and result['first_arrival_province']==8653

@pytest.mark.parametrize('bad',['old_tail','no_branch','changed_front','unchanged_suffix','lost_progress','first_not_reached','only_first_reached','destination_still_moving','preview_frame'])
def test_r13_rejects_tailshortcut_missing_first_edge_or_missing_actual_alt_arrival(bad):
    l,p,f,a,v=r13_scene();alt=1034
    if bad=='old_tail':alt=1033
    elif bad=='no_branch':v['route_preview']['route_province_ids']=[8653,1033,1034]
    elif bad=='changed_front':p['route']=[1034]
    elif bad=='unchanged_suffix':p['route']=[8653,1034,1033]
    elif bad=='lost_progress':p['movement']['normalized_edge_progress']['raw']=0
    elif bad=='first_not_reached':f['province']=1036
    elif bad=='only_first_reached':a['province']=8653
    elif bad=='destination_still_moving':a['route']=[1034]
    else:v['queried_native_revision']=1
    with pytest.raises(EvidenceError):r13(l,p,f,a,v,*action('move-army-18-to-'+str(alt),l),alt)

@pytest.mark.parametrize('bad',['partial_route','count','binding','strength_date','strength_generation'])
def test_full_frame_join_rejects_partial_or_crossed_source(bad):
    o=observation([8653,1034,1033],42);s=copy.deepcopy(o['snapshot']);q=copy.deepcopy(o['strength'])
    if bad=='partial_route':s['player_armies'][0]['route_read_status']='truncated'
    elif bad=='count':s['player_armies'][0]['route_source_count']=1
    elif bad=='binding':s['diagnostics']['bridge_pid']=4243
    elif bad=='strength_date':q['queried_date_raw']+=24
    else:q['queried_connection_generation']=2
    with pytest.raises(EvidenceError):frame(s,q,B)

def test_real_pinned_manifest_reader_fences_one_synthetic_r12_case(tmp_path):
    def keep(name,value):
        p=tmp_path/(name+'.json');b=json.dumps(value).encode();p.write_bytes(b)
        return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    def group(name,o):return {'snapshot':keep(name+'-s',o['snapshot']),'strength':keep(name+'-q',o['strength'])}
    base=observation([],40,date=100000);started=observation([8653,1034,1033],41,date=100000,progress=0)
    locked=observation([8653,1034,1033],42);post=observation([8653],43);arr=observation([],44,date=100120,province=8653)
    initial_req,initial_res=action('move-army-18-to-1033',base);req,res=action('halt-army-18',locked)
    manifest={'machine_id':'desktop-3fevhd2-1c74096080','case':'R12','case_id':'synthetic-R12-only','binding':B,
        'initial_move_count':1,'action_count':1,'owned_evidence_roots':[str(tmp_path.resolve())],'maximum_natural_days':15,
        'session_receipt':keep('owned-session',{'machine_id':'desktop-3fevhd2-1c74096080','pid':4242,'process_create_time_100ns':123456}),
        'baseline':group('base',base),'new_move_post':group('started',started),'locked':group('locked',locked),'post':group('post',post),'arrival':group('arr',arr),
        'initial_target':1033,'initial_preview':keep('preview',preview(base,1033,[8653,1034,1033])),
        'initial_move_request':keep('move-req',initial_req),'initial_move_response':keep('move-res',initial_res),'action_request':keep('halt-req',req),'action_response':keep('halt-res',res)}
    manifest['daily_clock_results']=[keep('clock-'+str(i),{'tactical_daily_sentinel':{'state':'triggered','generation':i,'starting_date_raw':100000+(i-1)*24,
        'target_date_raw':100000+i*24,'trigger_date_raw':100000+i*24,'completed_daily_ticks':1,'abnormal':False,'pause_observed':True,'pause_wrapper_called':True,
        'overshoot_days':0,'trigger_reasons':['date_deadline']}}) for i in range(1,6)]
    assert audit_manifest(manifest)['status']=='ACTUAL-CONSEQUENCE-PASS'
    # The same exact input is usable from another cwd and with relative refs.
    import subprocess,sys
    portable=copy.deepcopy(manifest);portable['owned_evidence_roots']=['.']
    def relative(value):
        if isinstance(value,dict):
            if set(value)=={'path','bytes','sha256'}:value['path']=str(Path(value['path']).relative_to(tmp_path))
            else:
                for child in value.values():relative(child)
        elif isinstance(value,list):
            for child in value:relative(child)
    relative(portable)
    manifest_file=tmp_path/'case.actual.json';manifest_file.write_text(json.dumps(portable),encoding='utf-8')
    elsewhere=tmp_path/'unrelated-cwd';elsewhere.mkdir();audit=tmp_path/'cli-audit.actual.json'
    process=subprocess.run([sys.executable,'-B',str(OUT/'verify.py'),'--manifest',str(manifest_file),'--output',str(audit)],cwd=elsewhere,capture_output=True,text=True)
    assert process.returncode==0,process.stdout+process.stderr
    assert json.loads(audit.read_bytes())['status']=='ACTUAL-CONSEQUENCE-PASS'
    source=Path(manifest['arrival']['snapshot']['path']);source.write_text('{}')
    with pytest.raises(EvidenceError,match='hash changed'):audit_manifest(manifest)
