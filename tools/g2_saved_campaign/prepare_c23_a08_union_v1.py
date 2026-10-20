"""Finite A08 RAM projection; preserve consumed A07 and original campaign score."""
import ast
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
sys.path.insert(0, str(OWN))
import prepare_c23_a07_union_v1 as previous

prior = previous.prior
MACHINE, O, T0 = previous.MACHINE, previous.O, previous.T0
U7, U8 = previous.U7, previous.U7.with_name('runtime-a08')
T5, HELPER = U8, previous.HELPER
UNION_PIN, ADOPTER_PIN = previous.UNION_PIN, previous.ADOPTER_PIN
PREVIOUS_PIN = (13512, '81d5609effb8c8c84d3138647eaba849aa814590a534e6520b198ba1d2443d76')
PREPARED = O / 'A07-PREPARED01.json'
PREPARED_PIN = (32683, '04e50510ffc23135f8ea53adeb76cc1ce09a4dcc02fe14ced5365e8979f6daca')
INDEX = O / 'A07-SOURCE-POSTPROCESS-FAILURE-INDEX01.json'
INDEX_PIN = (4401, 'c9dadda8deba605681410586faec17eed9ce9c9b908b88dfc021dd057d24d6c8')
NEXT_PIN = (120, '309a9ddcc9435a4622b7a2f3a9ec41a4544bb84bfbe85cdd09a7dac5b41c88a4')
require, exact = previous.require, previous.exact


def score_source():
    return f'''
def _a08_campaign_score(root,alias_required=True):
    original=Path({str(T0 / 'campaign-score')!r})
    anchor_ref={{'path':str(original/'CAMPAIGN-ANCHOR.json'),'bytes':1314,'sha256':'46f702dcb9fccbb08b5cc950ee9ceedb4c8303d10782bdf53bdbc043f9630215'}}
    anchor=_a03_checked(anchor_ref)
    require(anchor.get('machine_id')==MACHINE and anchor.get('campaign_id')=='robert-first30-v20261019'
        and anchor.get('founder_character_id')==31254 and anchor.get('start_date_raw')==53144328
        and anchor.get('endpoint_date_raw')==53407128 and anchor.get('fixed_across_ruler_and_sdk_changes') is True,
        'original1066 fixed campaign anchor required')
    launch=_a03_checked(anchor['game_launch']);response=_a03_checked(anchor['founding_ordinary_response'],131072)
    result=response.get('result') or {{}};body=result.get('structured_content') or {{}};frame=body.get('after_snapshot') or {{}}
    require(launch.get('machine_id')==MACHINE and (launch.get('pid'),launch.get('creation_filetime'))
        ==(anchor.get('game_pid'),anchor.get('game_creation_filetime'))==(214568,134368503807325674)
        and result.get('is_error') is False and body.get('postcondition_verified') is True
        and frame.get('date_raw')==53144328 and frame.get('paused') is True and frame.get('map_ready') is True
        and (frame.get('played_character') or {{}}).get('character_id')==31254,'actual original1066 founding sources required')
    identity=original.stat();require(identity.st_ino==281474988852728,'original score directory FileID changed')
    if alias_required:
        alias=Path(root)/'campaign-score';actual=alias.stat()
        require(alias.resolve(strict=True)==original.resolve(strict=True)
            and (actual.st_ino,actual.st_dev)==(identity.st_ino,identity.st_dev),'same-FileID whole campaign-score alias required')
    paths=sorted((original/'months').glob('*.json'))
    require([p.name for p in paths]==['month-%03d.json'%i for i in range(179)],'original179 monthly slots required')
    rows=[]
    for i,path in enumerate(paths):
        with path.open('rb') as stream:data=stream.read(32769)
        require(0<len(data)<=32768,'bounded original monthly sample required');item=json.loads(data)
        require(item.get('machine_id')==MACHINE and item.get('month_index')==i
            and item.get('baseline_date_raw')==53144328 and item.get('endpoint_date_raw')==53407128
            and item.get('campaign_anchor')=={{k:anchor.get(k) for k in ('campaign_id','founder_character_id','founding_house_id','founding_dynasty_id')}},
            'original monthly fixed identity differs')
        rows.append([path.name,len(data),hashlib.sha256(data).hexdigest()])
    cursor_ref={{'path':str(original/'LATEST-PERSISTED.json'),'bytes':578,'sha256':'ec05f3b1a6b715dd79765c044c5a323a568e12a75e7571b0798ece0075ba24f5'}}
    cursor=_a03_checked(cursor_ref)
    require(cursor.get('machine_id')==MACHINE and cursor.get('campaign_id')==anchor['campaign_id']
        and cursor.get('last_month_index')==178 and cursor.get('next_sample_index')==179
        and cursor['sample']['sha256']==rows[-1][2],'original monthly cursor differs')
    return {{'anchor':anchor_ref,'founding_launch':anchor['game_launch'],'founding_response':anchor['founding_ordinary_response'],
        'original_directory':str(original),'FileID':str(identity.st_ino),'volume':str(identity.st_dev),'monthly_slots':179,
        'monthly_rows_sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),
        'cursor':cursor_ref,'path':str(Path(root)/'campaign-score'),'must_verify_same_FileID':True,'body_bytes_copied':0}}

'''.encode('utf-8')


def campaign_score_guard(*, alias_required=False):
    scope = {**vars(prior), 'MACHINE': MACHINE, '_a03_checked': prior.checked}
    exec(compile(score_source(), 'A08-original-score-static-contract', 'exec'), scope)
    return scope['_a08_campaign_score'](U8, alias_required)


def actual_graph():
    exact(previous.__file__, PREVIOUS_PIN)
    prepared = json.loads(exact(PREPARED, PREPARED_PIN))
    require(prepared.get('machine_id') == MACHINE and prepared.get('complete44_actual_readback') is True
        and prepared.get('canonical6_original_max8_verifier_passed') is True and len(prepared['outputs']) == 119,
        'actual prepared A07 complete119 required')
    quote = prior.checked(prepared['quote'], 262144)
    profile = prior.checked(next(r for r in prepared['outputs'] if Path(r['path']) == U7 / 'ROOT-OBS-PROFILE-C23.json'))
    config = Path(profile['config_root'])
    mutable = {config / 'basic/profiles' / profile['profile_name'] / 'basic.ini',
        config / 'basic/scenes' / (profile['collection_name'] + '.json')}
    rows, values, observations = {}, {}, []
    for row in prepared['outputs']:
        path = Path(row['path']).resolve();require(path not in rows, 'unique prepared119 paths')
        data = prior.raw(path, 524288)
        if path in mutable:
            observations.append({'historical_prepared': row, 'current': prior.ref(path), 'body_reused': False})
        elif path == U7 / 'NEXT-SEQUENCE-P37.json':
            exact(path, NEXT_PIN);values[path] = data
        else:
            require((len(data), prior.sha(data)) == (row['bytes'], row['sha256']), 'immutable A07 leaf differs: ' + str(path))
            values[path] = data
        rows[path] = row
    require(len(values) == 117 and len(observations) == 2, '116 immutable, consumed NEXT, two observed OBS configs required')
    index = json.loads(exact(INDEX, INDEX_PIN))
    require(index.get('machine_id') == MACHINE and index.get('actual_SEM10481_complete') is True
        and index.get('CAP_FULL_submitted') is False and index.get('new_game_day_credit') == 0
        and index.get('NEXT') == json.loads(values[U7 / 'NEXT-SEQUENCE-P37.json']), 'actual consumed SEM frontier required')
    for row in index['actual_facts']:exact(row['path'], (row['bytes'], row['sha256']), 32768)
    return values, quote, rows, observations


def guard_source():
    return score_source() + f'''
def _validate_a08_attempt(args,config):
    value=_validate_a07_attempt(args,config);reference=value['prior_failure_a07']
    require((reference.get('bytes'),reference.get('sha256'))=={INDEX_PIN!r},'actual A07 postprocess failure index required')
    index=_a03_checked(reference)
    require(index.get('machine_id')==MACHINE and index.get('actual_SEM10481_complete') is True
        and index.get('CAP_FULL_submitted') is False and index.get('new_game_day_credit')==0,'actual SEM complete without CAP/FULL credit required')
    next_ref={{'path':str(Path({str(U7)!r})/'NEXT-SEQUENCE-P37.json'),'bytes':{NEXT_PIN[0]},'sha256':{NEXT_PIN[1]!r}}}
    require(_a03_checked(next_ref)==index['NEXT'] and index['NEXT']['next_sequence']==10482
        and index['NEXT'].get('failed_request_registered_without_readmission') is True
        and read(N/'NEXT-SEQUENCE-P37.json')['next_sequence']==10482,'consumed10481 cannot be replayed or reset')
    require(len(index['actual_facts'])==12,'twelve actual A07 facts required')
    for row in index['actual_facts']:_a03_checked(row,32768)
    rows={{Path(r['path']).name:r for r in index['actual_facts']}}
    closed=_a03_checked(rows['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A07.json']);game=_a03_checked(rows['ROOT-ACTUAL-GAME-EXIT-C23.json'])
    sdk=_a03_checked(rows['ROOT-P37C23-OWNER-CLOSED.json'])
    require(closed['machine_id']==game['machine_id']==sdk['machine_id']==MACHINE
        and (game['pid'],game['creation_filetime'])==(244624,134369509365547275)
        and game['kernel_signaled'] is True and game['exit_code']==1
        and closed['cleanup_classification']=='FORCED_OWNED_GAME_CLEANUP'
        and closed['owned_cleanup']['job_active_processes_final']==0 and closed['owned_cleanup']['cleanup_proven'] is True
        and sdk['normal'] is False and {{p['role']:p['exit_code'] for p in sdk['processes']}}=={{'sdk_queue':1,'sdk_application':0}},'actual A07 forced closure')
    nonces={{closed['attempt_nonce'],closed['task_nonce']}}
    for role,code in (('supervisor',1),('display',0)):
        task=_a03_checked(next(r for r in index['actual_facts'] if Path(r['path']).name=='CLOSED.json'
            and Path(r['path']).parent.name=='spec-'+role+'-a07'))
        wrapper=_a03_checked(rows['ROOT-A07-'+role+'-UNREGISTER01.json']);operation=json.loads(wrapper['stdout']);actual=operation.get('actual') or {{}}
        require(task['machine_id']==wrapper['machine_id']==operation['machine_id']==MACHINE
            and task['child_exit_code']==task['bootstrap_exit_code']==code and task['job_active_after_stage']==0
            and wrapper['returncode']==0 and operation['operation']=='unregister'
            and operation['task_name']=='XARG2ManagedOwner-'+task['nonce']
            and actual['absent_after'] is True and actual['instances']==0,'actual Task absence')
        nonces.add(task['nonce'])
    wrapper=_a03_checked(rows['ROOT-A07-SCREEN-RELEASE01.json']);release=json.loads(wrapper['stdout'])
    require(wrapper.get('returncode')==0 and release.get('ok') is True and release['task'].get('resources')==[]
        and release['task'].get('state')=='done' and release['task'].get('last_sequence')==7621,'actual A07 screen release required')
    require(args.attempt_nonce not in nonces and args.task_nonce not in nonces,'A08 needs independent attempt and Task nonces')
    _a08_campaign_score(N)
    return value

'''.encode('utf-8')


def bridge_source():
    return "def validate_post_sem_driver(pre,close,checked,verify_current_stat=True):\n    ref=pre.get('post_sem_driver_review')\n    require(isinstance(ref,dict) and (ref.get('bytes'),ref.get('sha256'))==(8024,'1447501126fce982da6d11b2561ce4bd1cc504e18ee8b3b533e3bc3885ba2f4b'),'actual Driver review02')\n    r=checked(ref,16384);old=checked(r['original_prelaunch'],16384);s=Path(r['driver_state']['path']).stat()\n    require(r['machine_id']==MACHINE and r['reviewer']=='/root' and r['SDK_normal'] is False and r['Game_normal'] is False\n        and r['new_day_credit']==r['Game_RPC_calls']==0 and r['history_rows']==5269 and r['history_key']=='command_history'\n        and r['last_history_row']['command']=='restore-checkpoint' and r['last_history_row']['ok'] is True,'actual post-SEM review')\n    require(pre['final_driver_close']==old['final_driver_close'] and close['driver_state']==old['driver_state']\n        and pre['driver_state']==r['driver_state'] and pre['checkpoint']==r['checkpoint']==r['last_checkpoint']==close['checkpoint']\n        and pre['validation']==r['canonical_validation']==old['validation']\n        and pre['sidecars']==[x['ref'] for x in r['sidecars']]==close['sidecars']\n        and (not verify_current_stat or (s.st_size,s.st_mtime_ns,str(s.st_ino))==(r['driver_stat']['size'],r['driver_stat']['mtime_ns'],r['driver_stat']['FileID'])),'historical close/current Driver bridge')\n    checked(r['A07_failure_index'],16384)\n    return True\n\ndef historical_saved_basis_view(admission):\n    require(admission.get('next_sequence')==10482,'actual A08 admission must retain10482')\n    pre=checked(admission['cold_prelaunch'],16384);r=checked(pre['post_sem_driver_review'],16384)\n    require((pre['post_sem_driver_review']['bytes'],pre['post_sem_driver_review']['sha256'])==(8024,'1447501126fce982da6d11b2561ce4bd1cc504e18ee8b3b533e3bc3885ba2f4b'),'actual reviewed history basis')\n    index=checked(r['A07_failure_index'],16384)\n    prior_root=Path(r['original_prelaunch']['path']).parent\n    next_ref={'path':str(prior_root/'NEXT-SEQUENCE-P37.json'),'bytes':120,'sha256':'309a9ddcc9435a4622b7a2f3a9ec41a4544bb84bfbe85cdd09a7dac5b41c88a4'}\n    sem=checked({'path':str(prior_root/'p37-responses/10481-1-result.json'),'bytes':56338,'sha256':'eb547732eea7d4beabac277617203706486a6bf313675976a131fb72018f77c5'},65536)\n    require((r['A07_failure_index']['bytes'],r['A07_failure_index']['sha256'])==(4401,'c9dadda8deba605681410586faec17eed9ce9c9b908b88dfc021dd057d24d6c8')\n        and index['machine_id']==MACHINE and index['actual_SEM10481_complete'] is True and index['CAP_FULL_submitted'] is False\n        and index['NEXT']==checked(next_ref,16384) and index['NEXT']['next_sequence']==10482\n        and sem['request']=={'sequence':10481,'tool':'ck3_take_semantic_snapshot_private_v1','arguments':{}}\n        and sem['result']['is_error'] is False and sem['result']['result_type']=='complete','actual consumed10481 proof')\n    return {**admission,'next_sequence':10481}\n"


def build_sources():
    values, quote, rows, mutable = actual_graph()
    names = [Path(r['path']).relative_to(previous.U6).as_posix() for r in quote['sources']['actual_source_rows']]
    require(len(names) == len(set(names)) == 89, 'exact actual89 source names required')
    source = {name: values[(U7 / name).resolve()].replace(b'C23-A07', b'C23-A08') for name in names}
    require((len(source[HELPER]), prior.sha(source[HELPER])) == (17637, 'bae312f0fb07d370252ecc5714666fe1790a4db33bca32599e0e9bcb56d64a8e'), 'strict Source26 helper unchanged')
    s = source['root_native30_supervisor_c23.py']
    for before, after, count in (("args.attempt=='a07'", "args.attempt=='a08'", 1),
        ("value.get('attempt_id')=='a07'", "value.get('attempt_id')=='a08'", 1),
        ('choices=("a07",)', 'choices=("a08",)', 1), ('"attempt_id":"a07"', '"attempt_id":"a08"', 2),
        ('_validate_a07_attempt(args, config)', '_validate_a08_attempt(args, config)', 1)):
        s = prior.swap(s, before, after, count)
    source['root_native30_supervisor_c23.py'] = prior.swap(s, 'def main(args):', guard_source().decode() + 'def main(args):', 1)
    b = source['root_checkpoint_bootstrap_c23.py']
    b = prior.swap(b, "close['driver_state'] == pre['driver_state']", "(close['driver_state'] == pre['driver_state'] or validate_post_sem_driver(pre,close,checked))", 1)
    source['root_checkpoint_bootstrap_c23.py'] = prior.swap(b, 'def verify_cold_profile(spec):', bridge_source() + '\n\ndef verify_cold_profile(spec):', 1)
    b = source['root_p37c23_cold_resume.py']
    b = prior.swap(b, "close['driver_state'] == pre['driver_state']", "(close['driver_state'] == pre['driver_state'] or validate_post_sem_driver(pre,close,checked,verify_current_stat=False))", 1)
    b = prior.swap(b, 'validate_saved_seed(admission, seed,', 'validate_saved_seed(historical_saved_basis_view(admission), seed,', 1)
    source['root_p37c23_cold_resume.py'] = prior.swap(b, 'def cold_inputs(admission):', 'from root_checkpoint_bootstrap_c23 import validate_post_sem_driver,historical_saved_basis_view\n\ndef cold_inputs(admission):', 1)
    for name, data in source.items():compile(data, name, 'exec')
    return source, {'schema':'xar.C23-A08-actual-A07-source-adapter/v1','machine_id':MACHINE,
        'source_count':86,'private_creator_count':3,'feeder':{},'actual_source_rows':[rows[(U7/name).resolve()] for name in names],
        'immutable_prepared_rows_verified':116,'consumed_NEXT':prior.ref(U7/'NEXT-SEQUENCE-P37.json'),
        'mutable_OBS_config_observations':mutable,'A07_failure_index':prior.ref(INDEX),'new_runtime_root':str(U8),'new_day_credit':0}


def state_guard(plan):
    pre=prior.checked(plan['cold_prelaunch_ref'],65536);review=prior.checked(plan['driver_review_ref'],65536)
    old=prior.checked(prior.ref(T0/'ROOT-C23-COLD-PRELAUNCH.json'),65536)
    require(pre.get('machine_id')==review.get('machine_id')==MACHINE and pre.get('status')=='EXACT_CLOSED_CHECKPOINT_COLD_INPUT_VALIDATED'
        and pre.get('post_sem_driver_review')==plan['driver_review_ref']
        and (plan['driver_review_ref']['bytes'],plan['driver_review_ref']['sha256'])==(8024,'1447501126fce982da6d11b2561ce4bd1cc504e18ee8b3b533e3bc3885ba2f4b')
        and review['driver_state']==pre['driver_state'] and review['checkpoint']==pre['checkpoint']==old['checkpoint']
        and [r['ref'] for r in review['sidecars']]==pre['sidecars'] and review['A07_failure_index']==prior.ref(INDEX),'actual post-SEM Driver cold review required')
    driver=Path(pre['driver_state']['path']);st=driver.stat();ds=review['driver_stat']
    require(driver.resolve()==(T0/'state/native-session/driver-state.json').resolve()
        and (st.st_size,st.st_mtime_ns,str(st.st_ino))==(ds['size'],ds['mtime_ns'],str(ds['FileID']))
        and st.st_size==pre['driver_state']['bytes'],'reviewed Driver stat changed')
    save=Path(pre['checkpoint']['path']);ss=save.stat()
    require((ss.st_size,ss.st_mtime_ns,ss.st_ino)==(116203629,1792449304215108900,281474988852756),'original SAVE changed')
    for row in pre['sidecars']:
        value=prior.checked(row,32768);require(value.get('pending') is None,'unresolved saved sidecar pending')
    with driver.open('rb') as stream:prefix=stream.read(4096)
    start=prefix.index(b'"last_checkpoint":')+len(b'"last_checkpoint":')
    checkpoint,_=json.JSONDecoder().raw_decode(prefix[start:].decode())
    require(checkpoint==pre['checkpoint'] and (U7/'state').resolve(strict=True)==(T0/'state').resolve(strict=True),'actual saved Driver checkpoint or state alias differs')
    return {'machine_id':MACHINE,'driver_review':plan['driver_review_ref'],'cold_prelaunch':plan['cold_prelaunch_ref'],
        'Driver_prefix_bytes_read':4096,'large_input_hash_bytes_read':0,'future_alias':str(U8/'state'),'exact_target':str(T0/'state')}


def compose(plan, *, display_values, display_review, companion_values):
    text=exact(prior.__file__,UNION_PIN).decode();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='compose')
    source=ast.get_source_segment(text,node).replace('C23-A05','C23-A08').replace('C23-A04','C23-A07')
    source=source.replace("'a05'","'a08'").replace('spec-supervisor-a05','spec-supervisor-a08')
    source=source.replace('2026-10-20T06:30:00+00:00','2026-10-20T10:30:00+00:00')
    before="prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'))"
    source=prior.swap(source.encode(),before,before[:-1]+',prior_failure_a07=ref(INDEX))',1).decode()
    source=prior.swap(source.encode(),"T5/name:raw(T4/name)","T5/name:(cold_prelaunch_bytes if name=='ROOT-C23-COLD-PRELAUNCH.json' else raw(T4/name))",1).decode()
    pre=prior.raw(plan['cold_prelaunch_ref']['path'],65536);prior.checked(plan['cold_prelaunch_ref'],65536)
    scope={**vars(prior),'__file__':__file__,'T4':U7,'T5':U8,'INDEX':INDEX,'build_sources':build_sources,
        'state_guard':lambda:state_guard(plan),'cold_prelaunch_bytes':pre}
    exec(compile(source,'A08-original-complete-union-projection','exec'),scope)
    outputs,quote=scope['compose'](plan,display_values=display_values,display_review=display_review,companion_values=companion_values)
    quote.update(campaign_score_junction=campaign_score_guard(),actual_A07_failure_index=prior.ref(INDEX),
        original_union_source=prior.ref(prior.__file__),previous_A07_adapter_source=prior.ref(previous.__file__),
        consumed_semantic_sequence=10481,new_first_sequence=10482,once_only_predecessor_Task_retained=True)
    quote['prerequisite_directories'].append(str(U8/'campaign-score'))
    quote['campaign_score_junction']['metadata_in_FS_upper']=4096
    return outputs,quote


def compose_plan(plan_ref):
    plan=prior.checked(plan_ref,131072);require(prior.ref(__file__)==plan['union_producer'],'actual reviewed A08 adapter required')
    path=Path(plan['display_producer']['path']).resolve()
    require(path==OWN/'prepare_c23_a08_display_v1.py' and prior.ref(path)==plan['display_producer'],'actual reviewed A08 display required')
    display=prior._module(path,'_a08_exact_display_RAM');values,review,companion=display.compose(plan['display'])
    outputs,quote=compose(plan,display_values=values,display_review=review,companion_values=companion)
    quote.update(adopter=prior.ref(__file__),input_plan=plan_ref,original_adopter_source=prior.ref(OWN/'adopt_c23_a05_union_v1.py'))
    return plan,outputs,quote


def metadata_source(source):
    data=prior.swap(source.encode(),"'next_sequence':10481","'next_sequence':10482",3)
    data=prior.swap(data,".get('next_sequence')==10481",".get('next_sequence')==10482",1)
    data=prior.swap(data,'helper.validate_saved_seed(basis,','helper.validate_saved_seed(historical_saved_basis_view(basis),',1)
    return prior.swap(data,'helper.validate_saved_seed(admission,','helper.validate_saved_seed(historical_saved_basis_view(admission),',1).decode()


def metadata_scope(scope,runtime):
    pre=prior.ref(runtime/'ROOT-C23-COLD-PRELAUNCH.json')
    require((pre['bytes'],pre['sha256'])==(4832,'8fb2c818faabc0d474c29934d793845e07c38e3dc2951f60f6de580302a72e72'),'actual A08 prelaunch')
    scope['COLD_PRE_PIN']=(pre['bytes'],pre['sha256'])
    scope['historical_saved_basis_view']=prior._module(runtime/'root_checkpoint_bootstrap_c23.py','_a08_checked_bootstrap_metadata').historical_saved_basis_view


def adopt(plan_ref,quote_ref,card_ref):
    path=OWN/'adopt_c23_a05_union_v1.py';text=exact(path,ADOPTER_PIN).decode();module=prior._module(path,'_a08_original_adopter_helpers_RAM')
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='adopt')
    source=ast.get_source_segment(text,node).replace('A05','A08').replace('a05','a08')
    extra="""score = runtime / 'campaign-score'
    result = subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(score),str(union.T0/'campaign-score')],capture_output=True)
    require(result.returncode == 0, 'exact whole campaign-score junction creation failed')
    campaign_score_guard(alias_required=True)
    actual = []"""
    source=prior.swap(source.encode(),'actual = []',extra,1).decode()
    source=prior.swap(source.encode(),"'state_same_FileID': True", "'state_same_FileID': True, 'campaign_score_same_FileID': True",1).decode()
    seam="exec(compile(source, 'A08-actual-saved-basis', 'exec'), scope)"
    source=prior.swap(source.encode(),seam,'source=metadata_source(source)\n    '+seam,1).decode()
    source=prior.swap(source.encode(),"_, basis_report = scope['saved_basis'](runtime_root=runtime)","metadata_scope(scope,runtime)\n    _, basis_report = scope['saved_basis'](runtime_root=runtime)",1).decode()
    bridge=types.SimpleNamespace(MACHINE=MACHINE,T5=U8,T0=T0,O=O,checked=prior.checked,ref=prior.ref,raw=prior.raw,_module=prior._module)
    scope={**vars(module),'compose':compose_plan,'union':bridge,'campaign_score_guard':campaign_score_guard,'metadata_source':metadata_source,'metadata_scope':metadata_scope}
    exec(compile(source,'A08-original-create-only-adopter-projection','exec'),scope)
    return scope['adopt'](plan_ref,quote_ref,card_ref)


def cold_owner(inputs):
    text=exact(prior.__file__,UNION_PIN).decode();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='cold_owner')
    source=ast.get_source_segment(text,node).replace('A05','A08').replace('a05','a08')
    seam="exec(compile(source,'A08-finite-cold-metadata-RAM','exec'),scope)"
    source=prior.swap(source.encode(),seam,'source=metadata_source(source)\n    '+seam,1).decode()
    source=prior.swap(source.encode(),"return scope['compose'](inputs)","metadata_scope(scope,T5)\n    return scope['compose'](inputs)",1).decode()
    scope={**vars(prior),'T5':U8,'metadata_source':metadata_source,'metadata_scope':metadata_scope}
    exec(compile(source,'A08-existing-cold-owner-projection','exec'),scope)
    return scope['cold_owner'](inputs)
