"""Independent JSON/raw review only. Never imports runner/consumer or executes native code."""
from pathlib import Path
import collections, datetime, hashlib, json

ROOT = Path(__file__).resolve().parent.parent
LANE = Path(__file__).resolve().parent
MACHINE = 'desktop-3fevhd2-1c74096080'
REFUSALS = {'default-off','missing-ack','bad-schema','occupied-dr','occupied-tf'}
FAULTS = {'restore-fault','readback-fault','continue-fault'}
SPECIAL_PARTIAL = {'foreign4096_limit','timeout','cancel_late','fullid-drift','magic-drift','session-drift'}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def read(path, limit=65536):
    path = Path(path)
    before = path.stat()
    need(0 <= before.st_size <= limit, 'bounded input '+str(path))
    data = path.read_bytes()
    after = path.stat()
    need((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
         and len(data)==before.st_size, 'input changed '+str(path))
    return data, dict(path=str(path.resolve()),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def document(path, limit=65536):
    data, ref = read(path, limit)
    return json.loads(data), ref

def referenced(ref, limit=65536):
    value, actual = document(ref['path'], limit)
    need(actual==ref, 'reference changed '+ref['path'])
    return value

def identity(row):
    return int(row['tid']),int(row['created'])

def six(values):
    return type(values) is list and len(values)==6 and all(type(v) is int and 0<=v<2**64 for v in values)

cap, cap_pin = document(ROOT/'capacity/PARENT-DR-COLD-ONLY30-2015.actual-a05.json')
need(cap_pin['sha256']=='b314de0c4932fdbb730d54ff3f0a17376a6442bcd295a10873ab1e3f0866f165', 'actual cap')
need(cap['admitted'] is True and cap['cold_execution_admitted'] is True
     and cap['machine_id']==MACHINE and cap['independent_cold_review_ceiling_bytes']==131072,
     'bounded actual review admission')
need(Path(cap['independent_cold_review_subroot']).resolve()==LANE.resolve(), 'review root')
need(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(cap['hard_deadline_utc'].replace('Z','+00:00')), 'deadline')
suite, suite_pin = document(ROOT/'cold-a01/SELECTED-COLD.actual.json')
need(suite_pin['sha256']=='283358b05236d5ae92b74fd671587ea5635dd8f54759f0f940af8656b9a6b7fa', 'actual suite')
need(suite['machine_id']==MACHINE and len(suite['selected_cases'])==17
     and len(set(suite['selected_cases']))==17 and suite['selected_cases'][-1]=='cancel_late', 'exact17/order')
need(suite['execution_DR_qualified'] is False and suite['full_R08'] is False, 'suite does not self-qualify')
recipe, recipe_pin = document(ROOT/'control-metadata-a01/PARENT-DR-NATIVE-RECIPE.prepared-a03.json')
need(recipe['selected_cases']==suite['selected_cases'], 'recipe selected order')
manifest, manifest_pin = document(recipe['source_manifest'])
need(manifest_pin['sha256']=='fbefc43570ccb9880b9d4362688eea732cb6e3d49813864a2866c0647fae68c7', 'actual p02 manifest')
root_system, root_system_pin = document(ROOT/'ROOT-ACTUAL-SYSTEM-REVIEW.actual-a01.json')
need(root_system_pin['sha256']=='a21289adcd8ae8e950e8722c7c34ede5b21d0174bae9529534c9b351bd88db66', 'Root SYSTEM review')
runner_wait, runner_wait_pin = document(ROOT/'cold-execution-a02/ORIGINAL-WAIT.actual-a01.json')
need(runner_wait['pid']==32500 and runner_wait['creation_time_100ns']==134369989956828136
     and runner_wait['original_Popen'] is True and runner_wait['original_wait'] is True
     and runner_wait['exit_code']==0 and runner_wait['machine_id']==MACHINE, 'actual retained suite wait')
expected_exes={Path(row['path']).name:str(Path(row['path']).resolve()) for row in cap['selected_project_EXEs']}
summaries=[]
for name, case_ref in zip(suite['selected_cases'],suite['cases']):
    case = referenced(case_ref)
    need(case['case']==name and case['status']=='PASS' and case['machine_id']==MACHINE, 'case identity '+name)
    directory=Path(case_ref['path']).parent
    waits={};wait_refs={};popens={};popen_refs={}
    for role in ('target','observer'):
        waits[role],wait_refs[role]=document(directory/(role+'.ORIGINAL-WAIT.actual.json'))
        popens[role],popen_refs[role]=document(directory/(role+'.POPEN.actual.json'))
        w,p=waits[role],popens[role]
        need(w['machine_id']==p['machine_id']==MACHINE and w['original_Popen'] is True
             and w['original_wait'] is True and w['pid']==p['pid'] and w['created']==p['created']
             and w['created']>0, 'original identity/wait '+name+'/'+role)
        exe='maintenance_parent_entry_cold_target.exe' if role=='target' else 'maintenance_parent_entry_observer.exe'
        need(str(Path(p['argv'][0]).resolve())==expected_exes[exe], 'exact executable path '+name+'/'+role)
        need(w['exit_code']==case[role+'_original_exit'], 'case/wait exit '+name+'/'+role)
    need(waits['target']['exit_code']==0, 'target actual completion '+name)
    result,result_pin=document(directory/'target.result.json')
    calls,calls_pin=document(directory/'target.calls.json')
    need(result==case['actual_target_result']==calls, 'actual target/calls/result '+name)
    need(result['synthetic'] is True and result['real_CK3_call'] is False
         and result['return_failures']==0 and result['audit_failures']==0, 'declared real function ABI/audit '+name)
    expected_counts=(257,1) if name=='foreign257_then_target' or name in FAULTS else (4096,1) if name in {'foreign4096_limit','cancel_late'} else (0,0) if name=='timeout' or name in REFUSALS else (0,1)
    need((result['foreign_body_calls'],result['target_body_calls'])==expected_counts
         and result['actual_body_calls']==sum(expected_counts), 'actual native body count '+name)
    rows=[];raw_pin=None;raw_data=b''
    if case['raw']:
        raw_data,raw_pin=read(case['raw']['path'],1048576)
        need(raw_pin==case['raw'] and raw_data.endswith(b'\n'), 'exact complete raw '+name)
        rows=[json.loads(line) for line in raw_data.splitlines()]
    kinds=collections.Counter(row['kind'] for row in rows)
    start=rows[0] if rows else None
    terminals=[row for row in rows if row['kind']=='terminal']
    if rows:
        need(start['kind']=='start' and start['machine_id']==MACHINE and start['synthetic'] is True
             and start['owner_binding'] is None and start['pid']==waits['target']['pid']
             and start['created']==waits['target']['created'], 'native raw target incarnation '+name)
        need(len(terminals)==1 and rows[-1] is terminals[0], 'one final terminal '+name)
        terminal=terminals[0]
        need(all(terminal.get(k) is True for k in ('restored','detached','cleanup_complete'))
             and terminal['pending_event'] is False and terminal['process_exited'] is False,
             'actual restore/continue/detach terminal '+name)
    else:
        terminal=None
        need(name in {'default-off','missing-ack','bad-schema'}, 'unexpected missing raw '+name)
    arms={}; retired=set(); restored={}; unarmed={}
    for row in rows:
        kind=row['kind']
        if kind=='arm':
            if row['success'] is False:
                need(name in REFUSALS and row['saved_debug']==[] and row['readback'] is True
                     and six(row['armed_debug']), 'zero-mutation refusal diagnostic '+name)
                continue
            need(row['success'] is True and row['readback'] is True and six(row['saved_debug'])
                 and six(row['armed_debug']), 'actual arm vector '+name)
            key=(row['thread_id'],row['thread_generation'])
            need(key not in arms and row['thread_created']>0, 'unique armed generation '+name)
            need(row['armed_debug'][0]==start['entry'] and row['armed_debug'][1:4]==[0,0,0]
                 and row['armed_debug'][5]&0xffff00ff==1, 'DR0 exact execute site '+name)
            arms[key]=(row['thread_created'],row['saved_debug'])
        elif kind=='thread_exited':
            retired.add((row['thread_id'],row['thread_generation']))
        elif kind=='restore' and row['readback'] is True and row['equal_original'] is True:
            key=(row['thread_id'],row['thread_generation'])
            need(key in arms and row['debug']==arms[key][1], 'restore full6 original '+name)
            restored[key]=row['debug']
        elif kind=='cleanup_thread_unarmed':
            need(row['readback'] is True and six(row['debug']), 'unarmed cleanup readback '+name)
            unarmed[(row['thread_id'],row['thread_created'])]=row['debug']
    before,before_pin=document(directory/'target.initial-debug.json')
    after,after_pin=document(directory/'target.after-debug.json')
    audit=referenced(case['independent_audit'])
    need(before==audit['before'] and after==audit['after'], 'independent original audit inputs '+name)
    need(all(row['complete'] is True and six(row['dr']) for row in before+after), 'complete all6 audit '+name)
    bmap={identity(row):row for row in before};amap={identity(row):row for row in after}
    need(len(bmap)==len(before) and len(amap)==len(after), 'unique full TID/birth census '+name)
    checked=[]
    for key,row in bmap.items():
        if key in amap:
            need(row['dr']==amap[key]['dr'], 'preexisting full6 changed '+name+'/'+str(key))
            checked.append(dict(tid=key[0],created=key[1],original_and_after_full6=row['dr']))
    owned_checked=[]
    for key,(birth,saved) in arms.items():
        if key in retired:
            continue
        peer=(key[0],birth)
        need(peer in amap and amap[peer]['dr']==saved and key in restored, 'live owned full6/restore '+name+'/'+str(key))
        if peer in bmap:
            need(bmap[peer]['dr']==saved, 'independent before equals actual saved6 '+name)
        owned_checked.append(dict(tid=key[0],generation=key[1],created=birth,saved_and_after_full6=saved))
    if name in REFUSALS:
        need(not arms and not any(kinds[k] for k in ('parent_entry','restore','foreign_resume','ready','cleanup_owned_execution'))
             and waits['observer']['exit_code'] in (1,2), 'zero actual arm/action refusal '+name)
    else:
        known=set(bmap)|{(tid,birth) for (tid,generation),(birth,saved) in arms.items()}|set(unarmed)
        need(not(set(amap)-known), 'unexplained live thread generation '+name)
        for key,debug in unarmed.items():
            if key in amap:
                need(amap[key]['dr']==debug, 'independent unarmed6 mismatch '+name)
        need(waits['observer']['exit_code']==(1 if name in SPECIAL_PARTIAL else 0), 'expected exact native exit '+name)
    entries=[row for row in rows if row['kind']=='parent_entry']
    resumes=[row for row in rows if row['kind']=='foreign_resume']
    if resumes:
        need(all(row['RIP_unchanged'] is True and row['DR0_retained'] is True
                 and row['RF_once'] is True and row['TF'] is False
                 and (row['thread_id'],row['thread_generation']) in arms for row in resumes), 'actual RF/noTF resume '+name)
    for row in entries:
        need(row['RIP']==start['entry'] and row['RDX']==start['character']
             and row['R9']==0xc001d00d12345678 and row['parent_return_observed'] is False,
             'actual retained entry and declared fixture cookie '+name)
    consumer=case['native_consumer']
    if name=='foreign257_then_target' or name in FAULTS:
        need(terminal['foreign_count']==257 and len(entries)==1 and consumer['target_entry_qualified'] is True, 'RF257 target result '+name)
    if name=='created_thread':
        need(result['worker_tid']>0 and any(key[0]==result['worker_tid'] for key in arms)
             and len(entries)==1 and entries[0]['thread_id']==result['worker_tid'], 'actual created worker capture')
    if name=='foreign4096_limit':
        need(terminal['foreign_count']==4096 and not entries and terminal['reason']=='foreign_limit', '4096 honest partial')
    if name=='timeout':
        need(terminal['reason']=='timeout' and terminal['foreign_count']==0 and not entries, 'zero-hit timeout')
    if name=='occupied-dr':
        need(result['occupied_warmup_calls']==1, 'actual occupied warmup exactly once')
        main=next(row for row in before if row['tid']==result['main_tid'])
        need(main['dr'][0]==0x12345000 and main['dr'][4]==0xffff0ff0
             and main['dr'][5]&0x401==0x401, 'actual requested occupied DR baseline')
    if name=='occupied-tf':
        main=next(row for row in before if row['tid']==result['main_tid'])
        need(main['eflags']&0x100 and amap[identity(main)]['eflags']&0x100
             and result['target_owned_TF_hold'] is True and result['occupied_warmup_calls']==0,
             'independent TF remains set before target-owned release')
    if name=='context-drift':
        need(len(entries)==1 and entries[0]['admitted_context_unchanged'] is False
             and consumer['target_entry_qualified'] is True, 'context diagnostic is not prefiltered')
    if name in {'fullid-drift','magic-drift','session-drift'}:
        need(len(entries)==1 and entries[0]['entry_owner_clock_qualified'] is False
             and consumer['target_entry_retained'] is True and consumer['target_entry_qualified'] is False,
             'drift retained without false qualification '+name)
    fault_pin=None
    if name in FAULTS:
        hold,fault_pin=document(directory/'ACTUAL-NATIVE-FAULT-HOLD.actual.json')
        need(hold['fault']==name.split('-')[0] and hold['injected_native_API_seam'] is True
             and hold['real_OS_fault_proven'] is False and kinds['unresolved_cleanup_hold']>0,
             'actual synthetic API fault hold '+name)
        n=hold['raw_prefix']['bytes']
        need(hashlib.sha256(raw_data[:n]).hexdigest()==hold['raw_prefix']['sha256'], 'actual held prefix retained '+name)
        for role in ('target','observer'):
            identity_row=hold[role+'_original_Popen']
            need(all(identity_row[k]==waits[role][k] for k in ('pid','created')), 'same original held then waited '+name)
    late=[]
    if name=='cancel_late':
        late=[row for row in rows if row.get('owned_late_event') is True]
        need(late and not entries and terminal['reason']=='cancel', 'actual late owned cancellation')
        for row in late:
            key=(row['thread_id'],row['thread_generation'])
            need(key in arms and row['thread_created']==arms[key][0] and row['RIP']==start['entry'], 'late exact owned generation/site')
    summaries.append(dict(case=name,CASE=case_ref,original_waits=wait_refs,original_popens=popen_refs,
        target_pid=waits['target']['pid'],target_created=waits['target']['created'],observer_pid=waits['observer']['pid'],
        observer_created=waits['observer']['created'],target_exit=waits['target']['exit_code'],observer_exit=waits['observer']['exit_code'],
        raw=raw_pin,raw_row_counts=dict(kinds),native_terminal=terminal,target_result=result_pin,actual_calls=calls_pin,
        actual_body_calls=result['actual_body_calls'],foreign_body_calls=result['foreign_body_calls'],target_body_calls=result['target_body_calls'],
        native_ABI_four_args_and_return_failures=result['return_failures'],occupied_warmup_calls=result['occupied_warmup_calls'],
        before_debug=before_pin,after_debug=after_pin,original_audit=case['independent_audit'],
        independently_compared_existing_full6=checked,independently_compared_owned_full6=owned_checked,
        retired_generations=[list(k) for k in sorted(retired)],unarmed_rows=len(unarmed),
        target_retained=consumer.get('target_entry_retained') if consumer else False,
        target_qualified=consumer.get('target_entry_qualified') if consumer else False,
        actual_native_fault_hold=fault_pin,owned_late_events=late))

value=dict(schema='xar.e04.parent-dr.actual17-independent-review.v1',machine_id=MACHINE,
    observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='INDEPENDENT_REVIEW_PASS_RECOMMEND_STANDALONE_EXECUTION_COLD_ACCEPTANCE',
    capacity=cap_pin,source_manifest=manifest_pin,producer_recipe=recipe_pin,Root_actual_SYSTEM_review=root_system_pin,
    suite=suite_pin,original_runner_wait=runner_wait_pin,actual_cases=17,case_order=suite['selected_cases'],
    cases=summaries,all34_child_original_waits_verified=True,all_native_full6_audits_independently_verified=True,
    no_register_masking=True,occupied_DR_warmup_actual=1,occupied_TF_before_and_after_preserved=True,
    all_seventeen_executed=True,cancel_late_last_and_actual_owned_late_observed=True,
    known_native_fault_seams='restore/readback/continue actual injected API seams; held original Popen then cleanup and wait, not proof of spontaneous OS failures',
    ABI_scope='Real synthetic declared four-argument function executed; body counters, per-call captured arguments and return assertion zero failures. No CK3 prototype or actual parent return capture qualification.',
    qualification_scope='Recommend Root acceptance only for this exact standalone parent-entry execution-DR cold binary/source set. Root must separately issue qualification/adoption.',
    qualification_not_self_issued=True,real_CK3=False,public_live_qualification=False,paid_maintenance_raw=None,payer=None,cadence=None,full_R08=False,
    old_attempt='Old p01 ten PASS, occupied-dr FAIL, later six unexecuted and missing original target wait remain unchanged. New p02 is independent; Python mock suites are not counted as native cold.',
    reviewer_execution=dict(native_EXE=0,SDK=0,DR_API=0,game=0,Steam_probe=0,source_edits=0,consumer_or_selector_reruns=0),
    reviewer_checker_correction='Initial metadata-only check incorrectly expected observer exit0 for three retained-but-unqualified drift cases. Corrected to exit1 with raw target_read_incomplete below; no native result changed or replayed.',
    raw_handling='Exact original final raw hashes/rows read for independent audit; no raw copies, no EXE bodies read or rehashed.',
    retention=dict(reason='Independent exact17 cold and full6/wait provenance for next Root adoption',review_by_utc='2026-10-22T19:45:00Z'))
payload=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
existing=sum(p.stat().st_size for p in LANE.rglob('*') if p.is_file())
top=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
need(existing+len(payload)<=131072 and top+len(payload)<=31457280, 'actual bounded review write')
output=LANE/'INDEPENDENT-ACTUAL-17-COLD-REVIEW.actual-a01.json'
with output.open('xb') as stream:
    stream.write(payload)
print(json.dumps(dict(path=str(output),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),lane_bytes=existing+len(payload),top_bytes=top+len(payload))))
