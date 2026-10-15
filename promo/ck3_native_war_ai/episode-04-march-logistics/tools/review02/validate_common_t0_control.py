"""Portable offline common-T0 pairing checks; explicit archive only, no runtime calls."""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
REPO=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(REPO),str(REPO/'ck3_autonomous_player/src')]
from xar_autoplayer.bridge.war_payment_observations_v1 import normalize_journal,JOURNAL_KEY
ARCHIVE=None
PREFIXES={}
MACHINE_ID=None
SOURCE=None
T0=END=ACTOR=UNIT=None

def resolve(value):
    need(ARCHIVE is not None,'explicit archive root required')
    need(isinstance(value,(str,Path)) and bool(str(value)),'explicit archive path required')
    text=str(value).replace('\\','/')
    for source,target in sorted(PREFIXES.items(),key=lambda p:len(p[0]),reverse=True):
        source=source.replace('\\','/').rstrip('/')
        if text==source or text.startswith(source+'/'):
            text=target.rstrip('/')+text[len(source):];break
    # Foreign absolute paths require an explicit prefix mapping, including on POSIX.
    need(not (len(text)>1 and text[1]==':') and not text.startswith('/'),
         'absolute evidence path requires an explicit archive prefix map')
    result=(ARCHIVE/text).resolve()
    need(result.is_relative_to(ARCHIVE),'archive path escapes declared root')
    return result

def configure(manifest,archive_root):
    global ARCHIVE,PREFIXES,MACHINE_ID,SOURCE
    ARCHIVE=Path(archive_root).resolve()
    need(ARCHIVE.is_absolute() and ARCHIVE.is_dir(),'explicit existing archive root required')
    need(manifest.get('schema')=='xar.e04.same-t0-pair-input.v2','unsupported pairing manifest')
    MACHINE_ID=manifest.get('machine_id')
    need(isinstance(MACHINE_ID,str) and bool(MACHINE_ID),'archive machine identity required')
    PREFIXES=manifest.get('archive_prefix_map',{})
    need(isinstance(PREFIXES,dict) and all(isinstance(k,str) and isinstance(v,str)
         and v and not Path(v).is_absolute() and ':' not in v for k,v in PREFIXES.items()),'invalid archive prefix map')
    SOURCE=manifest.get('source_contract')
    need(isinstance(SOURCE,dict) and isinstance(SOURCE.get('source_head'),str)
         and len(SOURCE['source_head'])==40,'explicit source commit pin required')
    for key in ('executable_sha256','bridge_dll_sha256'):
        need(isinstance(SOURCE.get(key),str) and len(SOURCE[key])==64,'exact source hash pin required')
    need(SOURCE.get('game_version')=='1.20.0.4' and SOURCE.get('steam_build')==25734779,'unsupported exact game build')

def distinct_windows(control,treatment):
    need(control['window_identity']!=treatment['window_identity'],'arms share process/window identity')
    need(control['binding']['run_id']!=treatment['binding']['run_id'] and
         (control['binding']['pid'],control['binding']['create_filetime'])!=
         (treatment['binding']['pid'],treatment['binding']['create_filetime']),
         'two loaded arms require independent run and process identities')

def need(ok,message):
    if not ok:raise ValueError(message)

def read(path,limit=16*1024*1024):
    path=resolve(path);need(path.suffix.lower()=='.json','only bounded JSON evidence may be opened')
    need(path.stat().st_size<=limit,'file exceeds bounded JSON read')
    raw=path.read_bytes();return json.loads(raw.decode('utf-8-sig'))

def packet(path,tool=None):
    row=read(path)
    need(row.get('machine_id')==MACHINE_ID and row.get('is_error') is False,'response machine/error mismatch')
    if tool:need(row.get('request',{}).get('tool')==tool,'wrong response tool')
    need(isinstance(row.get('body'),dict),'response has no complete body')
    return row

def frame(path,binding,date,stationary=False):
    need(resolve(path).parent==(resolve(binding['run_dir'])/'responses').resolve(),'snapshot is outside this actual run')
    row=packet(path,'ck3_take_snapshot');s=row['body'];d=s.get('diagnostics') or {};a=s.get('played_character') or {}
    need(d.get('bridge_pid')==binding['pid'] and d.get('connection_generation')==binding['generation']
        and s.get('episode_run_id')==binding['episode'] and a.get('character_id')==ACTOR and a.get('alive') is True,
        'fresh snapshot process/actor/episode mismatch')
    need(s.get('paused') is True and s.get('map_ready') is True and s.get('date_raw')==date,'fresh paused date mismatch')
    armies=[a for a in s.get('player_armies',[]) if a.get('army_id')==UNIT]
    need(len(armies)==1 and armies[0].get('owner_character_id')==ACTOR and armies[0].get('controllable') is True,'actual Army identity differs')
    army=armies[0]
    need(not army.get('in_combat') and not army.get('retreating'),'battle/retreat confounds controlled branch')
    if stationary:
        need(army.get('current_province_id')==2624 and army.get('route_read_status')=='complete_empty'
            and army.get('route_source_count')==0 and army.get('route_province_ids')==[]
            and army.get('move_target_province_id') is None and army.get('army_state')!='embarked',
            'control did not independently stay at2624 without route/boarding')
    return s,army

def payment(path,before_path,binding,date,epoch,window):
    need(resolve(path).parent==(resolve(binding['run_dir'])/'responses').resolve(),'cash is outside this actual run')
    source=packet(path,'ck3_query_war_cash_current_resources_private_v1');s,_=frame(before_path,binding,date)
    body=source['body'];args=source['request']['arguments']
    need(args.get('payment_sampling')=='query' and args.get('expected_revision')==s['revision'],'cash request/frame mismatch')
    need(body['snapshot_revision']==s['native_revision'] and body['date_raw']==date,'cash nativeframe differs')
    j=normalize_journal(body[JOURNAL_KEY],snapshot=s,machine_id=MACHINE_ID)
    control=body.get('war_payment_control_v1')
    need(isinstance(control,dict) and control.get('requested')=='query' and control.get('accepted') is True,'cash query control rejected')
    c=j['current_session'];p=j['sampling'];n=j['natural_journal_status']
    need(c['pid']==binding['pid'] and c['process_create_time_100ns']==binding['create_filetime']
        and c['connection_generation']==binding['generation'] and c['controlled_window_id']==window
        and c['player_character_full_id']==ACTOR and p['epoch']==epoch,'own-window cash binding differs')
    need(j['installed'] and not j['install_failure_flags'] and j['controlled_window_admitted']
        and p['available'] and p['capture_enabled'] and not p['busy'] and not p['active_captures']
        and j['read_complete'] and not j['overwritten'] and not j['publication_failures']
        and n['read_complete'] and not n['overwritten_records'] and not n['failed_appends'],'journal lost/partial/off')
    need(n['retained_records']<=56 and p['retained_records']<=384,'ring stopline exceeded')
    return j,body

def ordinary(path,binding,date):
    need(resolve(path).parent==(resolve(binding['run_dir'])/'responses').resolve(),'ordinary response is outside this actual run')
    p=packet(path,'ck3_query_army_strengths');body=p['body'];ev=p.get('army_history_evidence')
    need(isinstance(ev,dict) and ev.get('full_result_preserved') is True
        and ev.get('request_id')==p['request']['request_id'] and ev.get('query_sequence')==body['query_sequence']
        and ev.get('army_strengths_profile')==body.get('army_strengths_profile')=='ordinary_core_v1',
        'ordinary exact envelope reference missing')
    ref=ev['raw_result_reference'];path=resolve(ref['path']);need(path.suffix.lower()=='.json','reference must name JSON, never save/raw')
    need(ref.get('kind')=='complete-driver-army-query-result-json-v1' and ref.get('wire_bytes_preserved') is False
        and 0<ref['bytes']<=16*1024*1024,'ordinary reference invalid')
    need(path.stat().st_size==ref['bytes'],'ordinary actual size differs before bounded read')
    raw=path.read_bytes();need(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'new control reference integrity differs')
    result=json.loads(raw.decode('utf-8'))
    need(result.get('queried_date_raw')==date and result.get('queried_connection_generation')==binding['generation']
        and result.get('queried_episode_run_id')==binding['episode']
        and result.get('query_sequence')==body['query_sequence'] and result.get('army_strengths_query_scope',{}).get('army_ids')==[UNIT]
        and result.get('queried_revision')==ev.get('queried_revision')==body['source']['revision']
        and result.get('queried_native_revision')==ev.get('queried_native_revision')==body['source']['native_revision'],
        'ordinary source belongs to other query/window')
    rows=result.get('army_strengths');need(isinstance(rows,list) and len(rows)==1 and rows[0]['army_id']==UNIT,'ordinary Army subset differs')
    return rows[0]

def validate_baseline(arm,freeze,control=True):
    binding={key:arm.get(key) for key in ('pid','create_filetime','generation','episode','run_id','run_dir')}
    need(all(value is not None for value in binding.values()),'future runtime binding still pending')
    historical=freeze['existing_treatment']
    need((binding['pid'],binding['create_filetime'])!=(historical['PID'],historical['create_filetime']),'control/replay must be a new process identity')
    prepared=read(arm['prepared']);origin=prepared['checkpoint']['source']['save'];seed=freeze['T0']['save']
    need(prepared.get('machine_id')==MACHINE_ID and prepared.get('target_build')=={'version':SOURCE['game_version'],'steam_build':SOURCE['steam_build'],'exe_sha256':SOURCE['executable_sha256']}
        and prepared.get('game',{}).get('sha256')==SOURCE['executable_sha256']
        and prepared.get('bridge_dll',{}).get('sha256')==SOURCE['bridge_dll_sha256'],'prepared exact source/build differs')
    need(resolve(binding['run_dir']).name==binding['run_id']
        and resolve(binding['run_dir']).parent.resolve()==resolve(arm['assets_root']).resolve()
        and resolve(prepared['assets_root']).resolve()==resolve(arm['assets_root']).resolve()
        and resolve(arm['driver_state_path']).resolve()==(resolve(prepared['state_dir'])/'native-session/driver-state.json').resolve(),
        'actual prepared/run/state paths differ')
    need((origin['sha256'],origin['bytes'])==(seed['sha256'],seed['size']),'arm was not prepared from exact immutable commonT0 seed')
    identity=read(arm['identity_receipt'])
    need(identity.get('machine_id')==MACHINE_ID and identity.get('source_head')==SOURCE['source_head']
        and identity.get('process_creation_filetime_100ns')==binding['create_filetime']
        and identity.get('run_id')==binding['run_id'] and identity.get('pid')==binding['pid']
        and identity.get('connection_generation')==binding['generation'] and identity.get('episode_run_id')==binding['episode']
        and identity.get('actual_runtime_character_full_id')==ACTOR and identity.get('initial_date_raw')==T0
        and identity.get('stable_character_intent',{}).get('historical_id')==freeze['fresh_campaign_origin']['history_id']
        and identity.get('stable_character_intent',{}).get('bookmark_character_name_key')==freeze['fresh_campaign_origin']['normal_robert_key'],'new runtime normalRobert source binding differs')
    s,unit=frame(arm['t0_snapshot'],binding,T0)
    need(s.get('active_wars')==freeze['T0']['active_wars'],'independent active-war T0 differs')
    need(unit['current_province_id']==2624 and unit['move_target_province_id']==1033
        and unit['route_read_status']=='complete_nonempty' and unit['route_source_count']==4
        and unit['route_province_ids']==[1036,8653,1034,1033],'independent loaded T0 route differs')
    r=ordinary(arm['t0_ordinary_response'],binding,T0);m=r['current_movement_progress']
    need(m['normalized_edge_progress']==freeze['T0']['progress'] and m.get('loaded_movement_lock_cutoff')==freeze['T0']['cutoff']
        and r['current_soldiers']==1196 and r['maximum_soldiers']==1196 and r['current_supply_raw']==30000000,'loaded actual military T0 differs')
    admission=read(arm['admission']);session=admission['session'];epoch=admission['sampling']['epoch'];window=session['controlled_window_id']
    need(admission['machine_id']==MACHINE_ID and session['pid']==binding['pid']
        and session['process_create_time_100ns']==binding['create_filetime'] and session['connection_generation']==binding['generation'],
        'new arm admission differs')
    j,cash=payment(arm['baseline_cash'],arm['baseline_cash_before_snapshot'],binding,T0,epoch,window)
    need(cash['current_treasury']==freeze['T0']['treasury'],'independent initial treasury differs from savedT0')
    if control:
        need(resolve(arm['halt_response']).parent==(resolve(binding['run_dir'])/'responses').resolve(),'Halt source outside own run')
        halted=packet(arm['halt_response'],'ck3_execute_step')
        need(halted['request']['arguments'].get('step')=='halt-army-18' and halted['body'].get('accepted') is True,'not one actual accepted native Halt')
        after,_=frame(arm['after_halt_snapshot'],binding,T0,stationary=True)
        need(resolve(arm['after_halt_snapshot'])!=resolve(arm['halt_response']),'Halt submission cannot substitute independent route read')
    return {'binding':binding,'epoch':epoch,'window':window,'latest_sequence':j['latest_sequence'],
        'window_identity':[MACHINE_ID,binding['run_id'],binding['pid'],binding['create_filetime'],binding['generation'],window]}

def validate_days(arm,baseline,control=True):
    paths=arm.get('daily_summaries') or [];need(len(paths)==21,'exact21 daily summaries still pending')
    previous=baseline['latest_sequence'];positive=[];generations=set()
    for day,path in enumerate(paths,1):
        summary=read(path);date=T0+24*day
        need(summary['day']==day and summary['date_raw']==date and summary['starting_date_raw']==date-24
            and summary['run_id']==baseline['binding']['run_id'] and summary['PID']==baseline['binding']['pid']
            and summary['create_filetime']==baseline['binding']['create_filetime'] and summary['episode']==baseline['binding']['episode']
            and summary['window']==baseline['window'] and summary['payment_epoch']==baseline['epoch'],'day summary belongs to other arm/date')
        clock=summary['clock']
        need(clock['state']=='triggered' and clock['starting_date_raw']==date-24 and clock['target_date_raw']==date
            and clock['completed_daily_ticks']==1 and clock['overshoot_days']==0 and clock['pause_observed'] is True,'day exactclock failed')
        overrides=(arm.get('day_source_overrides') or {}).get(str(day)) or {}
        arm_paths=([overrides['arm_response']] if overrides.get('arm_response') else
            [p for p in summary['responses_this_day'] if Path(p).name.endswith('-05-arm.json')])
        clock_paths=([overrides['clock_response']] if overrides.get('clock_response') else
            [p for p in summary['responses_this_day'] if '-09-clock-query-' in Path(p).name])
        need(len(arm_paths)==len(clock_paths)==1,'one original arm/status source required')
        for p in arm_paths+clock_paths:
            need(resolve(p).parent==(resolve(baseline['binding']['run_dir'])/'responses').resolve(),'clock source outside own run')
        arm_packet=packet(arm_paths[0],'ck3_execute_step');status_packet=packet(clock_paths[0],'ck3_execute_step')
        need(status_packet['request']['arguments']['step']=='research-query-tactical-daily-sentinel-v1'
            and status_packet['body']['tactical_daily_sentinel']==clock,'derived clock differs from original status')
        from xar_autoplayer.bridge.native_driver import (_normalize_tactical_daily_sentinel_status as norm,
            _validate_tactical_daily_sentinel_arm as valid_arm,_validate_tactical_daily_sentinel_stop as valid_stop)
        armed=norm(arm_packet['body']['tactical_daily_sentinel']);actual_clock=norm(clock)
        arm_step=f'research-arm-tactical-daily-sentinel-v1-{date-24}-to-{date}-speed-5-mode-terminal-a-0'
        need(arm_packet['request']['arguments']['step']==arm_step,'source is not this actual day Arm')
        valid_arm(arm_packet['body'],armed,arm_step=arm_step,starting_date_raw=date-24,target_date_raw=date,
            speed=5,mode='terminal_or_sentinel',watch_army_ids=(),sentinel_scope='exact_one_day')
        valid_stop(actual_clock,arm_status=armed,starting_date_raw=date-24,target_date_raw=date,ending_date_raw=date,
            elapsed_days=1,speed=5,mode='terminal_or_sentinel',watch_army_ids=())
        need(clock['generation'] not in generations,'sentinel generation reused within this arm')
        generations.add(clock['generation'])
        cashpath=Path(summary['cash_source_response']);match=re_query_suffix(cashpath)
        before=cashpath.with_name(cashpath.name.replace(match,'-before-'+match.rsplit('-',1)[1]))
        j,_=payment(cashpath,before,baseline['binding'],date,baseline['epoch'],baseline['window'])
        seq=[r['journal_sequence'] for r in j['records'] if r['journal_sequence']>previous]
        need(j['latest_sequence']>=previous and len(seq)==j['latest_sequence']-previous
            and (not seq or (seq[0]==previous+1 and seq[-1]==j['latest_sequence'])),'within-arm sequence gap')
        current=[q for q in j['qualified_boarding_debits'] if q['writer_sequence']>previous]
        if control:need(not current,'stationary control produced a qualified boarding debit; preserve conflict')
        positive.extend({'day':day,**q} for q in current);previous=j['latest_sequence']
        finalpaths=([overrides['final_snapshot']] if overrides.get('final_snapshot') else
            [p for p in summary['responses_this_day'] if Path(p).name.endswith('-12-final.json')])
        need(len(finalpaths)==1,'one independent final snapshot required')
        _,route=frame(finalpaths[0],baseline['binding'],date,stationary=control)
        need(summary['actual_route_state']==route,'derived route does not match original response')
    return {'days':21,'end_date_raw':END,'positive_boarding_callbacks':positive,
        'same_epoch_sequence_checked_within_this_arm_only':True,'stationary_control_observed':control,
        'zero_total_expenses_or_free_boarding_proved':False,'maintenance_attribution':'unclosed'}

def re_query_suffix(path):
    name=path.stem
    for suffix in ('-query-0','-query-1'):
        if name.endswith(suffix):return suffix
    raise ValueError('cash response explicit same-request suffix missing')

def check(manifest,phase,archive_root):
    global T0,END,ACTOR,UNIT
    configure(manifest,archive_root)
    pin=manifest['common_t0_freeze']
    freeze_path=resolve(pin['path']);need(freeze_path.suffix.lower()=='.json','freeze must be JSON')
    need(freeze_path.stat().st_size<=1024*1024,'freeze exceeds bounded projection size')
    raw=freeze_path.read_bytes()
    need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'frozen T0 projection pin differs')
    freeze=json.loads(raw.decode('utf-8-sig'))
    need(freeze['machine_id']==MACHINE_ID,'frozen evidence belongs to another archive machine')
    T0=freeze['T0']['date_raw'];END=T0+21*24;ACTOR=freeze['T0']['actor'];UNIT=freeze['T0']['U']
    need(manifest.get('machine_id')==MACHINE_ID,'manifest archive machine differs')
    control=validate_baseline(manifest['control'],freeze,True)
    result={'control_baseline':'PASS','control_window_identity':control['window_identity'],
        'common_seed_sha_from_receipt':freeze['T0']['save']['sha256'],
        'original_R01_new_start':'R0171 lineage, not R0172/R0173 load','R01_full_commander_ABCgoal_freeze':'pending separate actual inputs',
        'original_R07_full_qualified':False,'original_R07_remaining':['<=7day window','avoid economic settlement','stationaryT0 then newMove']}
    if phase=='baseline':return result
    result['control']=validate_days(manifest['control'],control,True)
    mode=manifest.get('mode')
    if mode=='saved_t0_continuation_control':
        result['treatment']=freeze['existing_treatment']
        result['pair_scope']='21day control replay vs historical treatment savedT0 continuation; historical treatment did not load9ab3'
    elif mode=='two_new_loaded_arms':
        treatment=validate_baseline(manifest['treatment'],freeze,False)
        distinct_windows(control,treatment)
        result['treatment']=validate_days(manifest['treatment'],treatment,False)
        need(result['treatment']['positive_boarding_callbacks'],'new treatment has no actual qualified boarding debit')
        result['pair_scope']='two fresh independent processes loaded identical receipt-bound9ab3 seed'
    else:raise ValueError('explicit pairing mode required')
    result['matched_seed_no_boarding_control']='PASS'
    result['numeric_epoch_equal_is_not_shared_epoch']=True
    result['cross_window_sequence_comparison_performed']=False
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive-root',type=Path,required=True);parser.add_argument('--manifest',required=True)
    parser.add_argument('--phase',choices=['baseline','pair'],default='baseline');parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        archive=args.archive_root.resolve()
        manifest_path=(archive/args.manifest).resolve()
        need(not Path(args.manifest).is_absolute() and manifest_path.is_relative_to(archive),'manifest must be archive-relative')
        need(manifest_path.stat().st_size<=1024*1024,'manifest exceeds bounded JSON')
        result=check(json.loads(manifest_path.read_text(encoding='utf-8-sig')),args.phase,archive);code=0
    except (ValueError,KeyError,TypeError,OSError) as error:
        result={'result':'BLOCKED_OR_REJECTED','error_type':type(error).__name__,'reason':str(error),
            'new_control_observed':False,'original_R07_full_qualified':False};code=2
    result.update(archive_machine_id=MACHINE_ID,at_utc=datetime.now(timezone.utc).isoformat(),
        original_save_video_body_opened_or_hashed=False,game_SDK_desktop_calls=0)
    with args.output.open('x',encoding='utf-8') as h:json.dump(result,h,ensure_ascii=False,indent=2)
    print(json.dumps({'output':str(args.output),'exit_code':code,'result':result.get('result','checks_passed')},ensure_ascii=False));return code

if __name__=='__main__':raise SystemExit(main())
