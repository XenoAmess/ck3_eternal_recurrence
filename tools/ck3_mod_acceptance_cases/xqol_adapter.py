"""QOL defense and same-live Song UI business, using one shared runtime client."""
from __future__ import annotations
import copy, hashlib, json, time
from pathlib import Path
from ck3_mod_acceptance_prepare import restore_prepared_profile, write_json, pin
from .xqol_scope import parse_song_scope, parse_steppe_scope, parse_d0_frames

DATA=Path(__file__).with_name('xqol_original_plans.json')
SONG_MARKERS={'begin':'ZQD120QUAL: SCOPE BEGIN actual_song_actor_D0',
    'pass':'ZQD120QUAL: TEST PASS actual_song_actor_D0','end':'ZQD120QUAL: SCOPE END actual_song_actor_D0',
    'fail':'ZQD120QUAL: TEST FAIL actual_song_actor_D0'}
STEPPE_MARKERS={'begin':'ZQD120STEPPEQUAL: SCOPE BEGIN actual_steppe_actor_D0',
    'pass':'ZQD120STEPPEQUAL: TEST PASS actual_steppe_actor_D0','end':'ZQD120STEPPEQUAL: SCOPE END actual_steppe_actor_D0',
    'fail':'ZQD120STEPPEQUAL: TEST FAIL actual_steppe_actor_D0'}

def require(value,message):
    if not value:raise ValueError(message)

def plans(context,binding=None):
    data=json.loads(DATA.read_text(encoding='utf-8-sig'))
    def render(value):
        if isinstance(value,dict):
            if set(value)=={'$runtime_game'}:return context['shared_game'][value['$runtime_game']]
            if set(value)=={'$qol_scope_binding'}:
                return binding[value['$qol_scope_binding']] if binding is not None else value
            return {k:render(v) for k,v in value.items()}
        if isinstance(value,list):return [render(v) for v in value]
        return value
    return render(data)

def validate_contract(context):
    contract=context['case_contract']
    require(len(contract['required_markers'])==23 and len(contract['forbidden_markers'])==5,
            'Original QOL23/forbidden5 contract is mandatory')
    require(contract['required_exact_count']==1 and contract['forbidden_exact_count']==0 and
            contract['natural_game_day_limit']==33 and contract['original_final_plan_step_count']==6,
            'Original count/day/final6 contract changed')
    from .xqol_ui import STAGES
    require(contract['gui25_order']==STAGES,'Original25 business checkpoint order changed')
    budgets=context['case_spec']['budgets']
    require(budgets=={'command_timeout':300,'readiness_timeout':400,'timeout':3000,
                     'poll_interval':0.05,'hold_seconds':1800},'Original QOL budgets changed')

def prepare_case(context):
    validate_contract(context)
    original=plans(context)
    restore_context={**context,'case_contract':original['startup_contract']}
    result=restore_prepared_profile(restore_context,context['case_inputs']['beforelaunch_inventory'])
    require(len(result['files'])==47,'Original qualified QOL before-launch47 input count changed')
    require(result['files']['mod-content/product/descriptor.mod']['sha256']==
            json.loads(Path(context['case_inputs']['beforelaunch_inventory']).read_text(encoding='utf-8-sig'))['files']['mod-content/product/descriptor.mod']['sha256'],
            'Exact formal product descriptor changed')
    handler=pin(Path(__file__));handler['function']='admit_startup_event'
    dependencies=[pin(p) for p in (Path(__file__).with_name('xqol_scope.py'),DATA,
        Path(__file__).parent.parent/'ck3_mod_acceptance_prepare.py',Path(__file__).with_name('__init__.py'))]
    startup_hook=Path(context['output'])/'frontend-fixture-startup-case-contract.json'
    write_json(startup_hook,{'schema':'ck3-frontend-fixture-startup-case-contract-v1','state_dir':context['state_dir'],
                            'handler':handler,'dependencies':dependencies})
    return {'startup':{'mode':'fixture','state_dir':result['state_dir'],
                'fixture_start_policy':result['fixture_start_policy'],
                'startup_case_contract':pin(startup_hook),
                'frontend_rules_plan':context['case_inputs'].get('frontend_rules_plan')},
            'profile':result,'original_plans':pin(DATA),'formal_files_unchanged':27,
            'byte_exact_original_profile_files':45,'outer_descriptor_path_changes':2,
            'business_pass':False,'startup_case_hook_required':True}

def scope_proof(raw):
    song=parse_song_scope(raw,{'scope_name':'xqol_startup_actor','markers':SONG_MARKERS})
    steppe=parse_steppe_scope(raw,{'scope_name':'xqol_steppe_startup_actor','markers':STEPPE_MARKERS})
    require(song is not None and steppe is not None,'Both actual Song and Steppe scope proofs are required')
    require(song['end_line']<steppe['begin_line'] and song['runtime_character_id']!=steppe['runtime_character_id'],
            'Original actual Song scope must precede a distinct actual Steppe actor')
    return {'song':song,'steppe':steppe}

def admit_startup_event(context,snapshot,event_context):
    """Pure product qualification hook; the shared host owns any actual selection."""
    raw=(Path(context['state_dir'])/'profile/logs/debug.log').read_bytes()
    proof=scope_proof(raw)
    played=snapshot.get('played_character',{})
    require(played.get('character_id')==proof['steppe']['runtime_character_id'] and
            played.get('alive') is True and played.get('source')=='native',
            'Startup intro is not bound to the actual Steppe scope actor')
    event=snapshot.get('active_event')
    require(isinstance(event,dict) and event.get('source')=='native' and type(event.get('instance_id')) is int and
            event['instance_id']==1 and event.get('option_count')==1,'Original sole first native intro contract changed')
    options=event.get('options')
    require(isinstance(options,list) and len(options)==1 and options[0].get('enabled') is True and
            options[0].get('option_number')==1 and options[0].get('index')==0,
            'Original first intro must expose enabled public option1/native index0')
    packet=event_context;typed=packet.get('current_event_window_context',{})
    identity=typed.get('root_scope',{}).get('typed_identity',{})
    typed_options=typed.get('options')
    require(packet.get('status')=='available' and packet.get('current_event_window_context_ready') is True and
            typed.get('schema')=='current-event-window-context-v1' and typed.get('schema_version')==1 and
            typed.get('status')=='available' and typed.get('window_match_count')==1 and
            typed.get('current_event_instance_id')==1 and typed.get('snapshot_revision')==snapshot['native_revision'] and
            typed.get('date_raw')==snapshot['date_raw'] and identity.get('status')=='available' and
            identity.get('kind')=='character' and identity.get('character_id')==played['character_id'],
            'Actual typed intro context differs from the original scope-bound event')
    require(isinstance(typed_options,list) and len(typed_options)==1 and all(typed_options[0].get(k)==v for k,v in
            {'rendered_index':0,'native_option_index':0,'shown':True,'enabled':True,'fallback':False,'cancel':False}.items()),
            'Actual typed intro sole option is not enabled native index0')
    return {'event_instance_id':event['instance_id'],'option_number':1,
            'proof':proof,'business_pass':False}

def owned_hegemony_ids(root_packet, frame, song_id):
    """Query only real current held hegemony IDs; this does not prove their keys."""
    require(type(song_id) is int and song_id > 0 and
            frame.get('played_character', {}).get('character_id') == song_id and
            type(frame.get('date_raw')) is int and frame.get('paused') is True and
            frame.get('active_event') is None,
            'Original Song title proof requires its actual full paused event-free frame')
    root = root_packet.get('campaign_root_context', {})
    require(root_packet.get('campaign_root_context_ready') is True and
            type(root.get('player_character_id')) is int and root['player_character_id'] == song_id and
            type(root.get('date_raw')) is int and root['date_raw'] == frame['date_raw'] and
            root.get('government', {}).get('key') == 'celestial_government' and root.get('independent') is True,
            'Actual original Song government/independence/player/date is not proved')
    held = root.get('held_title_partition')
    require(isinstance(held, list), 'Actual Song owned-title partition is unavailable')
    ids = []
    for row in held:
        if not isinstance(row, dict) or not isinstance(row.get('title'), dict):
            continue
        title = row['title']
        if title.get('tier_raw') != 6 and title.get('tier_key') != 'hegemony':
            continue
        title_id = title.get('title_id')
        require(type(title_id) is int and 1 <= title_id <= 2**31 - 1 and
                type(title.get('tier_raw')) is int and title['tier_raw'] == 6 and
                title.get('tier_key') == 'hegemony' and title_id not in ids,
                'Actual held hegemony must have a unique full TitleID and exact tier')
        ids.append(title_id)
    require(ids, 'Original has_title=h_china requires a current owned hegemony')
    return ids

def prove_original_song_holding(root_packet, holder_packets, frame, song_id):
    """Prove original has_title=h_china from actual public title-holder keys.

    The shared current provider must expose title_holder.title_key. Neither
    primary-title identity, GUI debug mode nor historical IDs substitute for it.
    """
    ids = owned_hegemony_ids(root_packet, frame, song_id)
    require(isinstance(holder_packets, list) and holder_packets,
            'Current native title-holder key observations are required')
    seen = []
    matches = []
    observations = []
    for packet in holder_packets:
        holder = packet.get('title_holder') if isinstance(packet, dict) else None
        require(isinstance(holder, dict) and holder.get('schema') == 'xar.ck3.title-holder.v1' and
                type(holder.get('schema_version')) is int and holder['schema_version'] == 1 and
                holder.get('available') is True and holder.get('status') == 'available' and
                holder.get('title_key_available') is True and holder.get('title_key_status') == 'available' and
                holder.get('title_key_unavailable_reason') is None,
                'Current public title-holder observation is unavailable')
        title_id = holder.get('title_id')
        title_key = holder.get('title_key')
        require(type(title_id) is int and title_id in ids and title_id not in seen and
                isinstance(title_key, str) and title_key and title_key.isascii() and title_key.strip() == title_key,
                'Actual title-holder must expose its owned full ID and canonical stable key')
        seen.append(title_id)
        require(type(holder.get('actor_character_id')) is int and holder['actor_character_id'] == song_id and
                type(holder.get('holder_character_id')) is int and holder['holder_character_id'] == song_id and
                holder.get('holder_is_player') is True and holder.get('holder_in_player_realm') is True and
                type(holder.get('date_raw')) is int and holder['date_raw'] == frame['date_raw'] and
                type(holder.get('title_tier_raw')) is int and holder['title_tier_raw'] == 6 and
                holder.get('title_tier_key') == 'hegemony',
                'Native current hegemony holder differs from the actual Song actor/date')
        observations.append({'title_id': title_id, 'title_key': title_key})
        if title_key == 'h_china':
            matches.append(holder)
    require(len(matches) == 1, 'Actual native h_china key is not uniquely proved among owned hegemonies')
    holder = matches[0]
    held = root_packet['campaign_root_context']['held_title_partition']
    matching = [row for row in held if isinstance(row, dict) and isinstance(row.get('title'), dict) and
                row['title'].get('title_id') == holder['title_id']]
    require(len(matching) == 1, 'Actual h_china full ID is not unique in the owned partition')
    return {'title_key': holder['title_key'], 'title_id': holder['title_id'], 'holder_character_id': song_id,
            'held_not_required_primary': True, 'native_holder': holder, 'held_partition_row': matching[0],
            'queried_owned_hegemony_keys': observations}


def projection(frame):
    return {key:value for key,value in {
        'actor':frame['played_character']['character_id'],'pid':frame['diagnostics']['bridge_pid'],
        'generation':frame['diagnostics']['connection_generation'],'date_raw':frame['date_raw'],
        'source':frame['source'],'backend_id':frame['backend_id']}.items()}

def counts(client,contract,complete=False):
    raw=client.log_bytes(); lines=raw.splitlines()
    count=lambda literal:sum(literal.encode() in line for line in lines)
    required={m:count(m) for m in contract['required_markers']}
    forbidden={m:count(m) for m in contract['forbidden_markers']}
    require(not any(forbidden.values()) and all(n<=1 for n in required.values()),
            'Original business FAIL/reject or duplicate marker exists')
    for markers in (SONG_MARKERS,STEPPE_MARKERS):
        require({k:count(m) for k,m in markers.items()}=={'begin':1,'pass':1,'end':1,'fail':0},
                'Original actual scope markers changed or failed')
    if complete:require(all(n==1 for n in required.values()),'Original23 required exact-once markers incomplete')
    return {'required':required,'forbidden':forbidden,'debug_bytes':len(raw),
            'debug_sha256':hashlib.sha256(raw).hexdigest()}

def verify_day(row,client,previous):
    require(row.get('ok') is True and not row.get('error') and row.get('finished_at'), 'Actual day failed; never replay')
    result=row['result']
    require(result.get('requested_days')==1 and result.get('requested_interval_complete') is True and
            result.get('event_boundary') is None,'Original natural day/event boundary proof failed')
    before=client.validate_frame(result['before']);after=client.validate_frame(result['after'])
    elapsed=result.get('elapsed_hours')
    require(type(elapsed) is int and 24<=elapsed<48 and after['date_raw']-before['date_raw']==elapsed,
            'Original 24h interval proof failed')
    require(projection(before)==projection(previous),'Actual day before-frame differs from the last proven paused frame')
    return after

def post_d1(client,row,initial,contract):
    report=client.guard();rows=report['steps'];ids=[r['id'] for r in rows]
    require(len(ids)==len(set(ids)) and all(r.get('finished_at') for r in rows),'Duplicate/in-flight actual control row')
    days=[r for r in rows if r.get('kind')=='advance_day' or isinstance(r.get('result'),dict) and 'requested_days' in r['result']]
    require(len(days)==1 and days[0]==row,'Only the original first natural day may precede continuation')
    after=verify_day(row,client,initial)
    values=[r.get('after_snapshot') or r.get('result') for r in reversed(rows) if
            isinstance(r.get('after_snapshot') or r.get('result'),dict) and 'map_ready' in (r.get('after_snapshot') or r.get('result'))]
    require(values and projection(client.validate_frame(values[0]))==projection(after),'Latest native paused D1 differs')
    consumed={Path(p).resolve() for p in report.get('control_plans',[])}
    require(not list((client.live/'controls').glob('*.pending')),'An unconsumed control plan is pending')
    declared=set();byid={r['id']:r for r in rows};control_hashes={}
    for path in sorted((client.live/'controls').glob('*.json')):
        require(path.resolve() in consumed,'Original consumed control plan declaration missing')
        raw=path.read_bytes();steps=json.loads(raw)['steps']
        for step in steps:
            require(step['id'] not in declared and step['id'] in byid and byid[step['id']].get('finished_at'),
                    'Consumed plan has duplicated/missing/unfinished actual row')
            declared.add(step['id'])
        control_hashes[str(path)]=hashlib.sha256(raw).hexdigest()
    observation=counts(client,contract)
    lines=client.log_bytes().splitlines();count=lambda m:sum(m.encode() in line for line in lines)
    diagnostics={kind:{answer:count('ZQD20DIAG: '+kind+' '+answer) for answer in ('yes','no')}
                 for kind in ('forced_contract_setup_guard','postbreak_forced_flag','postbreak_not_allied')}
    require(all(v=={'yes':1,'no':0} for v in diagnostics.values()),'Original post-D1 retention/isolation diagnostic failed')
    require(all(count(m)==1 for m in ('ZQAREL: TEST PASS reverse_contracts_setup','ZQA: TEST PASS defense_fixture_setup')),
            'Both original fixture setup assertions must pass exactly once')
    return {'actual_first_day_row':row,'initial_native_identity':projection(initial),
            'current_native_identity':projection(after),'diagnostics':diagnostics,'counts':observation,
            'actual_control_plan_hashes':control_hashes,'budget':{'already_proven':1,'total_days_max':33,
                'remaining_days_max':32,'controller_timeout_max':1500,'single_day_timeout':300},'business_pass':False}

def run_case(context,client):
    validate_contract(context)
    contract=context['case_contract'];report=client.guard()
    proof=scope_proof(client.log_bytes())
    ready=client.validate_frame(report['readiness'],require_event_free=False)
    require(ready['played_character']['character_id']==proof['steppe']['runtime_character_id'],'Actual scope/native actor mismatch')
    # Initial first-event handling belongs to the shared startup hook. It must
    # have completed before these original D0 initial IDs are submitted.
    require(ready.get('active_event') is None,'Shared startup hook did not clear the legally qualified intro')
    binding={'runtime_character_id':proof['steppe']['runtime_character_id'],
        'bridge_pid':ready['diagnostics']['bridge_pid'],'connection_generation':ready['diagnostics']['connection_generation'],
        'date_raw':ready['date_raw']}
    original=plans(context,binding)
    initial_rows=client.execute_plan(original['initial']['steps'],'qol-original-initial2')
    initial=client.validate_frame(initial_rows[0]['result'])
    require(initial['played_character']['character_id']==proof['steppe']['runtime_character_id'], 'Original D0 actor changed')
    d0_rows=client.execute_plan(original['d0']['steps'],'qol-original-d0-diagnostics')
    require(len(d0_rows)==4,'Original D0 diagnostic four-row contract changed')
    require(projection(client.validate_frame(d0_rows[0]['result']))==projection(initial) and
            projection(client.validate_frame(d0_rows[-1]['result']))==projection(initial), 'D0 diagnostic changed actor/date')
    d0={'proof':proof,'actual_rows':d0_rows,'frames':parse_d0_frames(client.log_bytes(),proof['steppe']['runtime_character_id'])}
    client.checkpoint('actual-d0-gate',d0)
    started=time.monotonic();previous=initial;days=[];marker_counts=counts(client,contract)
    for day in range(1,34):
        require(time.monotonic()-started<1500,'Original defense controller1500s bound elapsed')
        row=client.advance_day(days=1,timeout=300)
        previous=verify_day(row,client,previous);days.append(row)
        marker_counts=counts(client,contract)
        if day==1:
            client.checkpoint('actual-post-d1-gate',post_d1(client,row,initial,contract))
        client.checkpoint('actual-day-'+str(day).zfill(3),{'proven_days':day,'actual_row':row,'counts':marker_counts,'original_day_limit':33})
        if all(v==1 for v in marker_counts['required'].values()):break
    counts(client,contract,complete=True)
    final=client.execute_plan(original['final6']['steps'],'qol-original-final6')
    require(len(final)==6 and all(r.get('ok') is True and not r.get('error') for r in final),'Original strict final6 failed')
    client.checkpoint('actual-original-final6-results',{'rows':final,'proven_days':len(days),'original23_verified':True,'product_pass':False})
    steppe_binding=client._binding
    root=client.root_checkpoint('qol-real-song-switch',{'action':'Root normal GUI Switch Character to the original true Song actor',
        'expected_song_character_id':proof['song']['runtime_character_id'],'original_song_scope_proof':proof['song'],
        'prior_steppe_character_id':proof['steppe']['runtime_character_id'],'same_pid':steppe_binding[0],
        'same_generation':steppe_binding[1],'final6':pin(client.output/'actual-original-final6-results.json')})
    require(root.get('switch_character_gui_reviewed') is True and root.get('evidence'), 'Original true Song Switch GUI evidence required')
    from ck3_mod_acceptance import check_pin
    for row in root['evidence']:check_pin(Path(row['path']),row)
    song_row=client.execute_plan([{'id':'qol-defense-song-ui-map','tool':'ck3_take_snapshot',
        'args':{'include_native_command_history':False},'fresh_revision':True}], 'qol-defense-song-ui-map')[0]
    song=client.validate_frame(song_row['result'],allow_actor_change=True)
    require(song['played_character']['character_id']==proof['song']['runtime_character_id'] and
            song['date_raw']==previous['date_raw'] and client._binding[:2]==steppe_binding[:2],
            'Actual Root GUI handoff did not produce the original true Song actor/date/owner')
    root_rows=client.execute_plan([{'id':'qol-actual-song-root-after-root-gui','tool':'ck3_query_campaign_root_context_v1','fresh_revision':True}],
                                 'qol-actual-song-root-after-root-gui')
    root_frame = client.validate_frame(root_rows[0]['after_snapshot'])
    require(projection(root_frame) == projection(song), 'Song root readback changed actual owner/actor/date')
    title_ids = owned_hegemony_ids(root_rows[0]['result'], root_frame, proof['song']['runtime_character_id'])
    holder_rows = []
    for ordinal, title_id in enumerate(title_ids, 1):
        phase = 'qol-actual-song-owned-hegemony-' + str(ordinal)
        rows = client.execute_plan([{'id': phase, 'tool': 'ck3_query_title_holder_v1',
            'args': {'title_id': title_id}, 'fresh_revision': True}], phase)
        require(len(rows) == 1 and rows[0].get('ok') is True, 'Actual owned hegemony holder query failed')
        holder_frame = client.validate_frame(rows[0]['after_snapshot'])
        require(projection(holder_frame) == projection(song), 'Song title holder readback changed actual owner/actor/date')
        holder_rows.append(rows[0])
        holder = rows[0]['result'].get('title_holder', {})
        if holder.get('title_key') == 'h_china':
            break
    title_proof = prove_original_song_holding(root_rows[0]['result'], [row['result'] for row in holder_rows],
                                             holder_frame, proof['song']['runtime_character_id'])
    client.checkpoint('actual-original-song-h-china-title-proof', {'proof': title_proof,
        'campaign_root_row': root_rows[0], 'title_holder_rows': holder_rows})
    readonly=client.execute_plan(original['readonly9']['steps'],'qol-original-real-song-readonly9')
    require(len(readonly)==9 and readonly[0].get('ok') is True and readonly[-1].get('ok') is True,'Original readonly9 endpoints failed')
    client.validate_frame(readonly[0]['result']);client.validate_frame(readonly[-1]['result'])
    client.checkpoint('actual-original-readonly9-results',{'rows':readonly,'optional_query_gaps':[r['id'] for r in readonly if not r.get('ok')],
                                                          'product_pass':False})
    client.checkpoint('root-same-live-required-ui-awaiting',{'run_id':client.frozen['run_id'],'reviewer':'/root',
        **client._process,'original_hold_deadline':client._hold,'scope_proof':proof,'original_gui25_required':True})
    from .xqol_ui import Controller
    ui=Controller(context,client).run()
    result={'case_contract_qualified':True,'gui_contract_qualified':ui['gui_contract_qualified'],
        'proven_days':len(days),'counts':marker_counts,'scope_proof':proof,'original_final6':True,'original_readonly9':True,
        'gui25':ui,'business_pass':False,'normal_close_still_required':True}
    client.checkpoint('qol-case-result',result)
    return result

def verify_case(context):
    validate_contract(context)
    path=Path(context['output'])/'qol-case-result.json'
    if not path.is_file():return {'case_contract_qualified':False,'gui_contract_qualified':False,'business_pass':False,'reason':'No completed original QOL case evidence'}
    result=json.loads(path.read_text(encoding='utf-8-sig'))
    require(result.get('original_final6') is True and result.get('original_readonly9') is True and
            1<=result.get('proven_days',0)<=33,'Original actual QOL phase evidence missing')
    require(all(n==1 for n in result['counts']['required'].values()) and not any(result['counts']['forbidden'].values()),
            'Original23/forbidden5 evidence is not exact')
    result['business_pass']=False
    return result
