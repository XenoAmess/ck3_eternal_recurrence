"""Small JSON evidence joins for Review01; media paths are provenance only."""
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path, PurePosixPath

START=53148432
END=53150592
EPISODE='native-33388-1be6dd7a468f'
CHECKPOINT='d052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a'
MAX_FILE=2*1024*1024

def need(value,message):
    if not value: raise ValueError(message)

def dumps(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()

def sha(raw): return hashlib.sha256(raw).hexdigest()

def relative(value):
    p=PurePosixPath(value)
    need(isinstance(value,str) and value and not p.is_absolute() and '..' not in p.parts
         and ':' not in value and '\\' not in value, 'safe package-relative path')
    need(p.suffix in ('.json','.py','.md'), 'JSON/code/knowledge only, never media/save')
    return p

def read_manifest(package):
    manifest=json.loads((package/'manifest.json').read_bytes())
    objects={}; cache={}
    for pin in manifest['files']:
        rel=relative(pin['path']); p=package.joinpath(*rel.parts)
        need(p.resolve().is_relative_to(package.resolve()), 'relative leaf escapes package')
        need(type(pin['bytes']) is int and 0<=pin['bytes']<=MAX_FILE, 'bounded text bytes')
        need(p.is_file() and p.stat().st_size==pin['bytes'], 'exact text size '+pin['path'])
        raw=p.read_bytes(); need(sha(raw)==pin['sha256'], 'exact text SHA '+pin['path'])
        need(pin['path'] not in cache, 'duplicate manifest leaf')
        cache[pin['path']]=raw
        if rel.suffix=='.json': objects[pin['path']]=json.loads(raw)
    return manifest,objects,cache

def get(objects,path):
    need(path in objects,'declared relative JSON source '+path)
    return objects[path]

def recorder(value):
    need(value['state']=='NORMAL_TREE_EMPTY' and value['job']['returncode']==0
         and value['job']['job_active_processes']==0, 'actual closed recorder Job0/return0')
    raw=value['raw']; need(type(raw['bytes']) is int and raw['bytes']>0 and len(raw['sha256'])==64,'terminal raw identity')
    return {'state':value['state'],'worker_job_pid':value['job']['pid'],
            'job_returncode':value['job']['returncode'],'job_active_processes':0,
            'raw_metadata_only':raw,'raw_bytes_opened_or_rehashed':False,
            'machine_audit':None,'Root_encoded_still_review':None,
            'continuous_clean':False,'human_1x_signoff':False}

def deviations(value):
    result=value['sampling_protocol_deviations']
    need(value['descriptive_continuation_only'] is True
         and value['controlled_comparison_eligibility_granted'] is False,'C descriptive only / eligibility not granted')
    need(len(result)>=7,'preserve at least seven actual sampling deviations')
    last=START
    for row in result:
        need(row['planned_max_target_days']==1 and row['actual_days']==2
             and row['overshoot_raw']==24 and row['window_one_day_sampling_eligible'] is False,
             'actual planned1/observed2/overshoot24 window remains ineligible')
        right=row.get('source_after_raw',row.get('actual_date_raw'))
        left=row.get('source_before_raw',right-48)
        need(left>=last and right-left==48 and right<=END,'actual ordered two-day deviation within fixed END')
        last=right
    return result

def observer(package,cache):
    path='code/historical-validate-results.py'
    need(sha(cache[path])=='144613e1ab9a35820323cfa2ca197e784565f02581c808fa35c6dafc8fe084e2',
         'exact reused pure stdlib complete-subject observer')
    spec=importlib.util.spec_from_file_location('review01_historical_observer',package/path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def pointer(obj,text):
    need(isinstance(text,str) and (text=='' or text.startswith('/')),'JSON pointer binding')
    for part in text.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~')
        obj=obj[int(part)] if isinstance(obj,list) else obj[part]
    return obj

def bound(objects,contract,name):
    binding=contract['field_bindings'][name]
    return pointer(get(objects,contract['roles'][binding['role']]),binding['pointer'])

def Main_scope_sources(objects):
    if 'Main-scope-source-map.json' not in objects: return None
    refs=get(objects,'Main-scope-source-map.json')
    approval=get(objects,refs['Root_scope']); policy=get(objects,refs['current_inputs'])
    proof=get(objects,refs['fresh_proof'])
    need(approval['schema']=='ck3.e04.abc.required-cohort-scope/v1'
         and approval['status']=='ROOT_FROZEN_BEFORE_NEXT_RESUME' and approval['actual_new_scope_granted'] is True,
         'this C actual Root Main scope freeze, not a proposed or other-arm scope')
    need(approval['episode_run_id']==EPISODE and approval['start_raw']==START
         and approval['absolute_end_raw']==END,'actual C scope episode and original clock')
    need(approval['required_public_ids']==[0] and approval['required_native_carmy_ids']==[0]
         and approval['required_commander_character_ids']==[27357]
         and approval['required_full_regiments']==27 and approval['required_full_DATA']==37,
         'actual Root Main0/native0/commander27357/full27/37 required scope')
    need(approval['full_native_snapshots_and_roster_preserved_without_projection'] is True
         and approval['no_unknown_value_coerced_to_zero_or_transport'] is True
         and approval['excluded_health'] is None,'actual scope keeps full roster and excluded health unknown')
    need(policy['Root_scope_addendum']['sha256']=='618d42f9d02d4f41065c295e142d44ed2db044482c65fda6e5155b9197da151d'
         and policy['allowed_unassessed_public_ids']==approval['unassessed_current_CUnit_ids']
         and policy['scope_approved_by_Root'] is True and policy['required_public_ids']==[0],
         'new bound current C input matches actual Root scope pin')
    need(proof['actual_raw']==53149848 and proof['paused'] is True
         and proof['foreground_game_pid']==7772,'independent actual +59 paused Main proof')
    return {'refs':refs,'approval':approval,'policy':policy,'proof':proof}

def required_Main_scope(observed,scope_source):
    """Describe actual partial global scope without editing either original body."""
    health=observed['health']; before=observed['before']
    required={0}; roster=before['player_armies']; roster_ids={row['army_id'] for row in roster}
    queried={row['army_id'] for row in health['army_strengths']}
    excluded=sorted(roster_ids-required)
    need(health['accepted'] is True and health['status']=='available','actual required Main health remains available')
    need(queried==required,'explicit health query contains Main0 only, without filtering a failed global query')
    global_status=health.get('scope_status')
    need(global_status in ('available','partial'),'preserve explicit original native global scope status')
    if excluded or global_status=='partial':
        need(scope_source is not None,'actual C Root scope needed for partial/unassessed player CUnits')
        allowed=set(scope_source['approval']['unassessed_current_CUnit_ids'])
        need(set(excluded).issubset(allowed),'new unassessed CUnit has not been reviewed by Root')
    if scope_source is not None:
        expected=scope_source['policy']['expected_complete_cohort']; cohort=observed['cohort']
        need(cohort['mapping']==expected['mapping']=={'0':0},'actual native Main FullID identity')
        actual_reg=[]
        for row in expected['regiments']:
            current=cohort['regiments'][str(row['army_regiment_id'])]
            actual_reg.append({key:current[key] for key in row})
        need(actual_reg==expected['regiments'] and len(actual_reg)==27,'all27 actual original Regiment identity/type/max fields')
        actual_records={key:{'army_regiment_id':json.loads(key)[0],**row} for key,row in cohort['records'].items()}
        projected=[]
        for row in expected['record_identities']:
            key=json.dumps([row['army_regiment_id'],row['record_index'],row['persistent_regiment_id'],row['chunk_index']],separators=(',',':'))
            projected.append({field:actual_records[key][field] for field in row})
        need(projected==expected['record_identities'] and len(projected)==37,'all37 actual DATA identity/max fields')
    return {'kind':'explicit_required_Main_only','required_public_ids':[0],'queried_public_ids':[0],
            'full_roster':roster,'full_roster_public_ids':sorted(roster_ids),'excluded_public_ids':excluded,
            'excluded_health':None,'excluded_health_queried_by_this_request':False,
            'raw_global_scope_status':global_status,'global_scope_partial':global_status=='partial',
            'all_player_health_complete_proved':False,'full_snapshot_filtered_or_mutated':False,
            'raw_health_filtered_or_mutated':False,'unknown_troops_or_transport_type_not_inferred':True}

def linked_scope(objects,cache,Root_review,relative_scope):
    approval=get(objects,relative_scope)
    need(approval['episode_run_id']==EPISODE and approval['start_raw']==START
         and approval['absolute_end_raw']==END,'scope actual C identity/time')
    need(approval['required_public_ids']==[0] and approval['required_native_carmy_ids']==[0]
         and approval['required_commander_character_ids']==[27357]
         and approval['required_full_regiments']==27 and approval['required_full_DATA']==37,
         'scope fixed original Main cohort')
    need(approval['actual_new_scope_granted'] is True and approval['excluded_health'] is None
         and approval['no_unknown_value_coerced_to_zero_or_transport'] is True,
         'scope actual grant with unknown health preserved')
    pin=Root_review['Root_scope_addendum']; raw=cache[relative_scope]
    need(pin['bytes']==len(raw) and pin['sha256']==sha(raw),'latest actual Root basis links exact scope bytes')
    return approval

def report_Main_scope(current,latest,approval):
    """Current geometry comes from its completed report, never the day59 four."""
    scope=current['scope_after']; roster=current['player_after']
    need(latest['episode_run_id']==EPISODE and latest['start_raw']==START
         and latest['absolute_end_raw']==END,'latest Root current C identity/budget')
    need(scope['required_public_ids']==scope['queried_public_ids']==[0]
         and scope['full_roster']==roster,'current report preserves entire native roster')
    ids=sorted(row['army_id'] for row in roster)
    need(scope['full_roster_public_ids']==ids and scope['excluded_public_ids']==[x for x in ids if x!=0],
         'current report role mapping from actual current roster')
    need(scope['raw_global_scope_status']==approval['actual_global_scope_status_preserved']
         and scope['excluded_public_ids']==approval['unassessed_current_CUnit_ids'],
         'current report global status and unknown identities match Root scope')
    need(scope['excluded_health'] is None and scope['excluded_health_queried_by_this_request'] is False
         and scope['all_player_health_complete_proved'] is False
         and scope['full_snapshot_filtered_or_mutated'] is False and scope['raw_health_filtered_or_mutated'] is False,
         'current Main-only report is not full-player health proof')
    need(current['counts_after']=={'regiments':27,'DATA':37}
         and latest['full27reg37DATA_commander27357_and_actual_clocks_reviewed'] is True,
         'actual Root-reviewed full original Main cohort report')
    return scope

def nine_key_scope(approval):
    return {'kind':'required_Main_original_cohort','required_public_ids':[0],
            'required_native_carmy_ids':[0],'required_full_regiments':27,'required_full_DATA':37,
            'global_health_status':approval['actual_global_scope_status_preserved'],
            'unassessed_CUnit_ids':approval['unassessed_current_CUnit_ids'],
            'unassessed_health':None,'all_player_total_soldiers':None}

def normalized_result(objects,cache,endpoint,ds,approval,latest_path):
    mapping=get(objects,'deviation-original-source-map.json')
    terminal_contract=objects.get('terminal/terminal-source-contract.json')
    normalized=[]
    for row in ds:
        right=row.get('source_after_raw',row.get('actual_date_raw')); left=row.get('source_before_raw',right-48)
        relative_source=mapping.get(str(right))
        if relative_source is None and terminal_contract:
            matches=[p for p in terminal_contract['original_terminal_input_map']['files']
                     if p['bytes']==row['underlying_STOP']['bytes'] and p['sha256']==row['underlying_STOP']['sha256']]
            need(len(matches)==1,'new final sampling source uniquely pinned')
            relative_source=terminal_contract['roles'][matches[0]['role']]
        need(relative_source in cache,'each normalized deviation has its original relative STOP')
        normalized.append({'observed_days':[(left-START)/24,(right-START)/24],
            'planned_max_days':row['planned_max_target_days'],'actual_days':row['actual_days'],
            'one_day_eligible':False,'source_pin':{'path':relative_source,'bytes':len(cache[relative_source]),
                                                'sha256':sha(cache[relative_source])}})
    metrics=None; source_sha=None
    if endpoint:
        source_sha=sha(cache[endpoint['source_roles']['Root_terminal']])
        if endpoint['London_stationary_arrival_observed']:
            metrics={'actor_character_id':33388,'public_army_id':0,'native_carmy_id':0,
                'commander_character_id':27357,'regiment_count':27,'DATA_record_count':37,
                'current_soldiers':endpoint['current_soldiers']['terminal'],'maximum_soldiers':endpoint['maximum_soldiers'],
                'current_supply_raw':endpoint['supply_raw']['terminal'],
                'current_supply_capacity_raw':endpoint['terminal_supply_and_clock']['current_supply_capacity_raw'],
                'current_supply_change_monthly_raw':endpoint['terminal_supply_and_clock']['current_supply_change_monthly_raw'],
                'supply_scale':100000,'date_raw':endpoint['first_observed_raw'],
                'current_attrition_fraction_raw':endpoint['terminal_supply_and_clock']['current_attrition_fraction_raw'],
                'current_attrition_fraction_scale':endpoint['terminal_supply_and_clock']['current_attrition_fraction_scale'],
                'treasury_raw':endpoint['gold_raw']['terminal'],'treasury_scale':100000,
                'actual_player_row':next(r for r in endpoint['terminal_player_roster'] if r['army_id']==0),
                'exact_arrival_tick':None}
    return {'closed':True if endpoint else None,'status':endpoint['status'] if endpoint else None,
            'source_sha256':source_sha,'episode_run_id':EPISODE,'common_T0_raw':START,'absolute_END_raw':END,
            'observed_terminal_date_raw':endpoint['first_observed_raw'] if endpoint else None,
            'actual_days_used':endpoint['elapsed_actual_days'] if endpoint else None,
            'sampling_deviations':normalized,'London_endpoint_metrics':metrics,
            'observed_arrival_interval_days':[(x-START)/24 for x in endpoint['arrival_interval_raw']]
                if endpoint and endpoint['arrival_interval_raw'] else None,
            'global_budget_breach':endpoint['global_budget_breach'] if endpoint else None,
            'controlled_comparison_eligibility':'NOT_GRANTED','winner':None,
            'applied_refill_payment_ledger':None,'subject_scope':nine_key_scope(approval)}

def terminal_projection(package,objects,cache,baseline,old_deviations):
    if 'terminal/terminal-source-contract.json' not in objects: return None
    contract=get(objects,'terminal/terminal-source-contract.json')
    need(contract['schema']=='ck3.e04.C.review01.terminal-inputs.v1','terminal source contract schema')
    roles=contract['roles']
    required=['cold_before','cold_health','cold_after','cold_commander','last_not_arrived',
              'last_not_arrived_commander','first_observed','first_observed_commander',
              'independent_endpoint','independent_endpoint_commander','Root_terminal',
              'Root_numeric_acceptance','runtime_closure','S03_sealed','S04_sealed','latest_Root_review','current_Main_scope']
    need(all(name in roles and roles[name] in objects for name in required),'all actual completed terminal JSON roles')
    check=observer(package,cache)
    common={'actor_character_id':33388,'whole_maximum_soldiers':6747,'start_raw':START,
            'initial_gold':{'raw':63754562,'scale':100000},
            'cold_baseline_regiment_rows_sha256':baseline['cold_entire_row_digests']['regiments'],
            'cold_baseline_complete_DATA_rows_sha256':baseline['cold_entire_row_digests']['DATA']}
    local={}; initial_refs={}
    for name in ('before','health','after','commander'):
        key='cold_'+name; local[key]=get(objects,roles[key]); initial_refs[name]=key
    cold=check.observation({'source_refs':initial_refs,'subject_public_ids':[0]},local,common,initial=True)
    observed={}
    for role in ('last_not_arrived','first_observed','independent_endpoint'):
        packet=get(objects,roles[role]); refs={}
        for component in ('before','health','after'):
            key=role+'_'+component; local[key]=packet[component]; refs[component]=key
        key=role+'_commander'; local[key]=get(objects,roles[key]); refs['commander']=key
        observed[role]=check.observation({'source_refs':refs,'subject_public_ids':[0]},local,common)
    last=observed['last_not_arrived']; first=observed['first_observed']; peer=observed['independent_endpoint']
    scope_sources=Main_scope_sources(objects)
    latest=get(objects,roles['latest_Root_review'])
    final_approval=linked_scope(objects,cache,latest,roles['current_Main_scope'])
    final_scope_sources={**scope_sources,'approval':final_approval}
    terminal_scopes={name:required_Main_scope(value,scope_sources if name=='last_not_arrived' else final_scope_sources)
                     for name,value in observed.items()}
    for name in ('first_observed','independent_endpoint'):
        need(terminal_scopes[name]['raw_global_scope_status']==final_approval['actual_global_scope_status_preserved']
             and terminal_scopes[name]['excluded_public_ids']==final_approval['unassessed_current_CUnit_ids'],
             'actual terminal native scope matches fresh Root-linked scope, not historical +59 values')
    for item in (cold,last,first,peer):
        need(item['before']['episode_run_id']==EPISODE,'same actual C episode, not A/B/old warmup')
        need(item['cohort']['mapping']=={'0':0} and item['commanders']=={'0':27357},'actual whole Main0/commander27357')
        need(START<=item['before']['date_raw'],'actual endpoint cannot precede unchanged original T0')
    initial=cold['cohort']['stock']['0']
    need(cold['cohort']['soldiers']==baseline['baseline']['current_soldiers']
         and initial['current_supply_raw']==baseline['baseline']['stock_raw']
         and initial['current_supply_capacity_raw']==baseline['baseline']['capacity_raw'],
         'actual shared cold soldiers/stock/capacity')
    need(first['before']['date_raw']==peer['before']['date_raw'],'independent endpoint actual same date')
    need(first['cohort']==peer['cohort'],'independent complete subject rows/stock/clock equality')
    need(first['before']['player_armies']==peer['before']['player_armies'],'independent same actual roster/currentroute')
    need(first['before']['played_character_gold']==peer['before']['played_character_gold'],'independent actual treasury equality')
    need(START<=last['before']['date_raw']<first['before']['date_raw'],'actual preceding/first-observed interval')
    for collection in ('regiments','records'):
        need(set(cold['cohort'][collection])==set(first['cohort'][collection]),'original27/37 identity preserved')
        need(all(row['maximum_soldiers']==cold['cohort'][collection][key]['maximum_soldiers']
                 for key,row in first['cohort'][collection].items()),'each original maximum preserved')
    arrival=check.stationary_london(first)
    if arrival: need(not check.stationary_london(last) and check.stationary_london(peer),'actual arrival brackets')
    final_deviations=deviations(latest)
    need(final_deviations[:len(old_deviations)]==old_deviations,'old seven deviations never replaced')
    supplied=contract['original_terminal_input_map']['files']
    for row in final_deviations[len(old_deviations):]:
        source=row['underlying_STOP']; matches=[p for p in supplied if p['bytes']==source['bytes']
            and p['sha256']==source['sha256']]
        need(len(matches)==1,'each new sampling deviation needs its original completed STOP JSON')
        stop=get(objects,roles[matches[0]['role']])
        if 'underlying_scope_mismatch_wrapper_STOP' in row:
            wrapper_pin=row['underlying_scope_mismatch_wrapper_STOP']
            wrapper_matches=[p for p in supplied if p['bytes']==wrapper_pin['bytes']
                             and p['sha256']==wrapper_pin['sha256']]
            need(len(wrapper_matches)==1,'original scope-mismatch wrapper has its separate exact source')
            wrapper=get(objects,roles[wrapper_matches[0]['role']])
            need(wrapper['actual_paused'] is None and wrapper['actual_date_raw'] is None
                 and wrapper['blind_retry'] is False and wrapper['no_more_resume'] is True,
                 'original wrapper failure remains pause/date NULL, without blind retry')
            need(row['failed_result_pause_null_preserved'] is True
                 and row['actual_STOP_omits_overshoot_field'] is True
                 and row['Root_actual_raw_delta_manual_review'] is True
                 and stop['actual_paused'] is True and stop['actual_date_raw']==row['source_after_raw']
                 and stop['status']=='STOP_ACTUAL_STATIONARY_ARRIVAL'
                 and row['source_before_raw']==last['before']['date_raw']
                 and row['source_after_raw']==first['before']['date_raw'],
                 'separate actual producer arrival and native interval support Root-reviewed two-day deviation')
        elif row.get('failed_result_pause_null_preserved') is True:
            need(stop['actual_paused'] is None and stop['blind_retry_allowed'] is False,
                 'original failed STOP pause remains NULL, never reclassified as a paused success')
        else:
            need(stop['actual_date_raw']==row['source_after_raw'] and stop['actual_overshoot_raw']==24,
                 'new original STOP matches actual date/overshoot')
    need(bound(objects,contract,'numeric_accepted') is True,'actual Root numeric acceptance required')
    need(bound(objects,contract,'terminal_raw')==first['before']['date_raw'],'Root terminal date source binding')
    need(bound(objects,contract,'runtime_closed') is True,'actual Root all-owned runtime closure required')
    need(bound(objects,contract,'release_resources')==[],'actual release has no owned screen resources')
    status=bound(objects,contract,'terminal_status'); need(isinstance(status,str) and status,'actual Root terminal disposition')
    sealed=recorder(get(objects,roles['S03_sealed']))
    sealed4=recorder(get(objects,roles['S04_sealed']))
    delta={}
    for collection in ('regiments','records'):
        delta[collection]=[{'identity':key,'changed_fields':check.diff_paths(cold['cohort'][collection][key],row),
                            'before':cold['cohort'][collection][key],'after':row}
                           for key,row in first['cohort'][collection].items() if row!=cold['cohort'][collection][key]]
    initial_stock=cold['cohort']['stock']['0']; final_stock=first['cohort']['stock']['0']
    initial_gold=cold['before']['played_character_gold']; final_gold=first['before']['played_character_gold']
    need(initial_gold['scale']==final_gold['scale']==100000,'actual treasury scale')
    need(initial_stock['current_supply_scale']==final_stock['current_supply_scale']==100000,'actual supply scale')
    return {'status':status,'London_stationary_arrival_observed':arrival,
            'first_observed_raw':first['before']['date_raw'],'elapsed_actual_days':(first['before']['date_raw']-START)/24,
            'remaining_actual_days':(END-first['before']['date_raw'])/24,
            'arrival_interval_raw':[last['before']['date_raw'],first['before']['date_raw']] if arrival else None,
            'arrival_interval_open_left_closed_right':True if arrival else None,'exact_arrival_raw':None,
            'deadline_censor':first['before']['date_raw']==END and not arrival,
            'global_budget_breach':first['before']['date_raw']>END,
            'current_soldiers':{'initial':cold['cohort']['soldiers'],'terminal':first['cohort']['soldiers'],
                                'net':first['cohort']['soldiers']-cold['cohort']['soldiers']},
            'maximum_soldiers':first['cohort']['maximum'],'regiment_count':27,'DATA_record_count':37,
            'public_to_native':first['cohort']['mapping'],'actual_commanders':first['commanders'],
            'terminal_player_roster':first['before']['player_armies'],
            'actual_subject_scope':terminal_scopes,'all_player_health_complete_proved':False,
            'supply_raw':{'initial':initial_stock['current_supply_raw'],'terminal':final_stock['current_supply_raw'],
                          'net':final_stock['current_supply_raw']-initial_stock['current_supply_raw'],'scale':100000},
            'initial_supply_and_clock':initial_stock,'terminal_supply_and_clock':final_stock,
            'gold_raw':{'initial':initial_gold['raw'],'terminal':final_gold['raw'],
                        'net':final_gold['raw']-initial_gold['raw'],'scale':100000},
            'gold_net_semantics':'Observed treasury balance difference; travel payment/upkeep/cause unknown.',
            'full_regiment_and_DATA_row_changes':delta,
            'active_war_changed_paths':check.diff_paths(cold['before']['active_wars'],first['before']['active_wars'],'/active_wars'),
            'non_subject_health':first['cohort']['non_subject_health'],'runtime_closure_source':roles['runtime_closure'],
            'runtime_closed':True,'release_resources':[],'S03':sealed,'S04':sealed4,
            'sampling_deviations':final_deviations,'controlled_comparison_eligibility':'NOT_GRANTED',
            'descriptive_only':True,'winner':None,'soldier_application_cause':None,
            'native_exact_event_PTS':None,'continuous_clean':False,'human_1x_signoff':False,
            'source_roles':roles}

def derive(package,objects,cache):
    stage=get(objects,'stage32/C-stage-before-terminal.json')
    baseline=get(objects,'stage32/early-stage/C-intermediate-values.json')
    latest=get(objects,'inputs/Root-day51-review.json'); day51=get(objects,'inputs/day51-source-analysis.json')
    current=day51
    if 'latest-stage-source-map.json' in objects:
        latestmap=get(objects,'latest-stage-source-map.json')
        latest=get(objects,latestmap['latest_Root_review'])
        current=get(objects,latestmap['latest_analysis'])
    need(stage['experiment']['start_raw']==START and stage['experiment']['absolute_end_raw']==END,
         'original common time boundary')
    need(stage['experiment']['checkpoint']['sha256']==CHECKPOINT and stage['experiment']['checkpoint']['bytes']==73795635,
         'original whole checkpoint identity (save bytes not read)')
    need(baseline['episode_run_id']==EPISODE and baseline['actual_actor_id']==33388,'C actual cold identity')
    ds=deviations(latest)
    scoped=Main_scope_sources(objects)
    if 'deviation-original-source-map.json' in objects:
        mapping=get(objects,'deviation-original-source-map.json')
        need(len(mapping)==len(ds),'one original STOP per base sampling deviation')
        for row in ds:
            right=row.get('source_after_raw',row.get('actual_date_raw'))
            stop=get(objects,mapping[str(right)])
            if row.get('failed_result_pause_null_preserved') is True:
                need(stop['actual_paused'] is None and stop['blind_retry_allowed'] is False
                     and scoped is not None and scoped['proof']['actual_raw']==right,
                     'failed original STOP remains pause-null; only separate fresh proof shows actual endpoint pause')
            else:
                need(stop['actual_date_raw']==right and stop['actual_overshoot_raw']==row['overshoot_raw']
                     and stop['actual_paused'] is True and stop['start_raw']==START and stop['absolute_end_raw']==END,
                     'original STOP date/overshoot/pause/budget remain portable')
    need(day51['after_date_raw']==53149656 and day51['required_identity_max_commander_runtime_war_gate_pass'] is True,
         'completed actual +51 report scope')
    need(day51['full_regiment_row_delta']==[] and day51['full_DATA_container_row_delta']==[]
         and day51['material_delta']==[],'actual +49/+51 no own-row/material change')
    need(day51['counts_after']=={'regiments':27,'DATA':37},'reported complete cohort counts')
    main=day51['player_after'][0]
    need(main['army_id']==0 and main['owner_character_id']==33388 and main['current_province_id']==2176
         and main['route_province_ids']==[729,965,686,628,629,1527]
         and main['army_state']=='moving' and main['in_combat'] is False and main['retreating'] is False,
         '+51 camera London is not actual Army London arrival')
    cash=get(objects,'inputs/day31-cash-source-analysis.json')
    need(cash['gold_before']['scale']==cash['gold_after']['scale']==100000,'cash report raw scales')
    cash_delta=cash['gold_after']['raw']-cash['gold_before']['raw']
    need(cash_delta==93767,'observed +31 net treasury value')
    camera=get(objects,'inputs/London-camera-day37-receipt.json')
    need(camera['actual_camera_title']=='b_london' and camera['native_camera_postcondition_verified'] is True,
         'actual typed camera evidence')
    Root38=get(objects,'inputs/Root-day38-camera-review.json')
    need('Root_actual_review_notes' in Root38,'separate later Root camera review source')
    segments={'S01':recorder(get(objects,'inputs/S01-owned-recorder-terminal.json')),
              'S02':recorder(get(objects,'inputs/S02-owned-recorder-terminal.json')),'S03':None,'S04':None}
    segments['S01']['machine_audit']=stage['S01_media']
    if 'inputs/S02-machine-audit.json' in objects:
        audit=get(objects,'inputs/S02-machine-audit.json'); review=get(objects,'inputs/Root-S02-six-encoded-review.json')
        need(audit['state']=='PASS' and audit['source_identity']==segments['S02']['raw_metadata_only'],
             'closed S02 audit joins actual worker terminal raw pin, without reading raw')
        need(review['raw_identity_copied_without_rehash']==audit['source_identity']
             and review['Root_viewed_all_six_originals'] is True and review['human_approval'] is False,
             'actual six Root encoded still reviews, no full-film signoff')
        segments['S02']['machine_audit']={'source':'inputs/S02-machine-audit.json','state':audit['state'],
            'duration_seconds':audit['actual_duration_seconds'],'decoded_frames':audit['decoded_frames'],
            'video_packets':audit['video_packets'],'stream_counts':audit['stream_counts']}
        segments['S02']['Root_encoded_still_review']={'source':'inputs/Root-S02-six-encoded-review.json',
            'rows':review['rows'],'full_film_human_approval':False,'native_exact_event_PTS':None}
    need(current['after_date_raw']==latest['actual_date_raw']
         and current['required_identity_max_commander_runtime_war_gate_pass'] is True,
         'latest completed actual date is JSON value, never inferred from directory name')
    current_scope=None; historical_scope=None
    if scoped:
        approval=linked_scope(objects,cache,latest,scoped['refs']['Root_scope'])
        current_scope=report_Main_scope(current,latest,approval)
        historical_scope={'actual_raw':53149848,'source_map':'Main-scope-source-map.json',
            'proof':scoped['proof'],'historical_report_scope':get(objects,'inputs/day59-source-analysis.json')['scope_after'],
            'does_not_prove_latest_position':True}
    endpoint=terminal_projection(package,objects,cache,baseline,ds)
    if endpoint:
        segments['S03']=endpoint['S03']; segments['S04']=endpoint['S04']; ds=endpoint['sampling_deviations']
    normalization_approval=get(objects,endpoint['source_roles']['current_Main_scope']) if endpoint else scoped['approval']
    normalized=normalized_result(objects,cache,endpoint,ds,normalization_approval,
        endpoint['source_roles']['latest_Root_review'] if endpoint else latestmap['latest_Root_review'])
    gold59=get(objects,'inputs/day59-source-analysis.json'); gold60=get(objects,'inputs/day60-source-analysis.json')
    need(gold59['gold_after']['raw']-gold59['gold_before']['raw']==-1700000,'separate +59 treasury window')
    need(gold60['gold_after']['raw']-gold60['gold_before']['raw']==24723,'separate +60 treasury window')
    A=get(objects,'archived/A-only-observed-values.json')
    B=get(objects,'archived/B-closed-gate-values.json'); Bmerge=get(objects,'archived/B-merge-gate-values.json')
    need(A['A_experiment_closed'] is True and B['B_disposition']=='STOPPED_GATE_INCOMPLETE','archived A/B descriptive dispositions')
    return {'schema':'ck3.e04.C.review01.portable-values.v1',
            'status':'C_CLOSED_DESCRIPTIVE_ENDPOINT' if endpoint else 'C_IN_PROGRESS_DESCRIPTIVE_ONLY',
            'experiment':stage['experiment'],'actual_game_episode':EPISODE,'actual_game_pid_from_cold_receipt':7772,
            'baseline':baseline['baseline'],'cold_entire_row_digests':baseline['cold_entire_row_digests'],
            'route':stage['route'],'day2_supply_change':baseline['day2_supply'],
            'day3_offsite_NPC_change':baseline['day3_offsite'],'day27_integer_change':stage['day27_integer_change'],
            'day31_net_treasury_change':{'before_raw':cash['before_date_raw'],'after_raw':cash['after_date_raw'],
                'initial':cash['gold_before'],'after':cash['gold_after'],'net_raw':cash_delta,'cause':None,
                'semantics':'Observed treasury difference, not travel payment or upkeep application.'},
            'day32_supply_change':stage['day32_supply_change'],
            'day37_camera':{'typed_title':camera['actual_camera_title'],'actual_raw':camera['actual_date_raw'],
                'original_pending_receipt_preserved':True,'later_Root_original_review_source':'inputs/Root-day38-camera-review.json',
                'camera_center_is_not_Army_follow_or_arrival':True},
            'last_completed_preterminal_report':{'actual_raw':current['after_date_raw'],
                'day':(current['after_date_raw']-START)/24,
                'scalars':current['scalars_after'],'clock':current['clock_after'],'gold':current['gold_after'],
                'actual_player_roster':current['player_after'],
                'own_full_regiment_row_differences':current['full_regiment_row_delta'],
                'own_full_DATA_container_row_differences':current['full_DATA_container_row_delta']},
            'sampling_deviations':ds,'controlled_comparison_eligibility':'NOT_GRANTED',
            'current_Main_scope':current_scope,
            'historical_day59_Main_scope':historical_scope,
            'day59_net_treasury_change':{
                'before_raw':gold59['before_date_raw'],'after_raw':gold59['after_date_raw'],
                'gold_before':gold59['gold_before'],'gold_after':gold59['gold_after'],
                'net_raw':gold59['gold_after']['raw']-gold59['gold_before']['raw'],
                'payment_application_ledger':None,
                'UI_price_agreement_does_not_prove_payment':True},
            'day60_net_treasury_change':{'before_raw':gold60['before_date_raw'],'after_raw':gold60['after_date_raw'],
                'gold_before':gold60['gold_before'],'gold_after':gold60['gold_after'],
                'net_raw':24723,'cause':None,'payment_application_ledger':None},
            'failed_initial_query':{'source':'inputs/Root-day55-authored-notes.json',
                'cause':None,'initial_health_pre_snapshot_unavailable_reported_by_Root':True,
                'whole_invocation_absence_not_claimed':True}
                if 'inputs/Root-day55-authored-notes.json' in objects else None,
            'descriptive_continuation_only':True,'recording_segments':segments,
            'terminal':endpoint,'normalized_C_result':normalized,'winner':None,'complete_controlled_ABC_comparison_credit':0,
            'soldier_application_ledger_cause':None,'upkeep_or_travel_payment_cause':None,
            'native_exact_event_PTS':None,'continuous_clean':False,'human_1x_signoff':False,
            'ABC_descriptive_rows':{
                'A':{'status':'CLOSED_OBSERVED_STATIONARY_LONDON','archived_source':'archived/A-only-observed-values.json',
                    'arrival':A['arrival'],'endpoint_values':A['endpoint_values']},
                'B':{'status':B['B_disposition'],'archived_source':'archived/B-closed-gate-values.json',
                    'actual_raw':B['actual_raw'],'days_used':B['days_used'],'remaining_days':B['remaining_days'],
                    'London':None,'deadline_censor':False,'merge_cohort_gate':Bmerge['frozen_whole_cohort_gate'],
                    'commander_preserved':Bmerge['commander_preserved'],'new_regiment_type_or_cause':None},
                'C':{'status':'C_CLOSED_DESCRIPTIVE_ENDPOINT' if endpoint else 'IN_PROGRESS',
                    'controlled_comparison_eligibility':'NOT_GRANTED','terminal':endpoint}},
            'verification_scope':'Exact local text byte pins and stated small report joins; terminal full subject joins only when declared actual sources are present. No raw/save/UI/SDK/bus/Git/process/network access.'}
