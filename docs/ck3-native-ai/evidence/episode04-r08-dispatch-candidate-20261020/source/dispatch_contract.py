"""Candidate pure projection. It opens no process/file and grants no live credit."""
import json

CALL_RVA=0x3F90A6F
SOURCE_SHA='426e7b7c3e47980c4975bff0745518c9539d7bd06ae6f7f44d973789a7f3c11e'
REGISTERS={'rbx','rcx','rax','rdx','r8','r9','rsp'}

def need(ok,message):
    if not ok:raise ValueError(message)

def integer(value):
    need(type(value) is int and 0<=value<2**64,'Exact uint64 required')
    return value

def project(rows,expected_owner):
    need(type(rows) is list and rows and len(rows)<=1027,'Bounded original rows required')
    start=rows[0]
    need(start['kind']=='start' and start['schema']=='xar.maintenance.dispatch_call.v1'
         and start['mode']=='single_pre_call_execution_breakpoint','Dedicated dispatch mode required')
    need(start['source_sha256']==SOURCE_SHA and start['callsite_rva']==CALL_RVA
         and start['maximum_records']==1 and start['DR7_execution_mask']==1,'Fixed source/budget required')
    need(start['job_is_payer'] is False,'A generic job is not payer evidence')
    need(json.dumps(start['owner_binding'],sort_keys=True)==json.dumps(expected_owner,sort_keys=True),
         'Original independent Root owner binding differs')
    need(expected_owner['mode']=='native_campaign_owned_no_load_v2'
         and expected_owner['episode_run_id'] is None,'Native ordinary owner required')
    need(start['pid']==expected_owner['pid'] and start['created']==expected_owner['process_create_time_100ns'],
         'Original process creation differs')
    base,size=integer(start['module_base']),integer(start['module_size'])
    need(base>0 and size==102518784 and base+size<2**64,'Exact loaded image size required')
    active={};generations={};restored=set();captures=[];issues=[];terminal=None
    for row in rows[1:]:
        kind=row['kind']
        if kind=='arm':
            tid=integer(row['thread_id']);generation=integer(row['thread_generation'])
            need(tid>0 and tid not in active and generation==generations.get(tid,0)+1,'Thread generation not owned')
            generations[tid]=generation
            saved,armed=row['saved_debug'],row['armed_debug']
            need(len(saved)==len(armed)==6 and all(type(x) is int for x in saved+armed),'Debug vector absent')
            good=(row['success'] is True and saved[:4]==[0]*4 and saved[5]&0xffff00ff==0
                  and armed[:4]==[base+CALL_RVA,0,0,0] and armed[5]&0xffff00ff==1)
            active[tid]=(generation,saved,good)
            if not good:issues.append('unqualified_arm')
        elif kind=='thread_exited':
            tid=integer(row['thread_id']);integer(row['thread_generation']);need(tid in active and row['thread_generation']==active[tid][0],'Unowned thread exit')
            del active[tid]
        elif kind=='restore':
            tid=integer(row['thread_id']);integer(row['thread_generation']);need(tid in active and row['thread_generation']==active[tid][0],'Stale restore generation')
            if row['readback'] is True and row['debug']==active[tid][1]:restored.add((tid,active[tid][0]))
        elif kind=='dispatch_call_pre_instruction':
            need(not captures,'Only the first execution fault is retained')
            tid=integer(row['thread_id']);integer(row['thread_generation']);need(tid in active and row['thread_generation']==active[tid][0],'Unowned dispatch generation')
            need(row['RIP']==base+CALL_RVA and row['RIP_rva']==CALL_RVA
                 and integer(row['DR6'])&15==1 and row['DR6']&0xe000==0,'Not the unique pre-CALL execution fault')
            registers=row['registers'];reads=row['reads'];clock=row['clock']
            need(set(registers)==REGISTERS,'Actual ABI registers missing')
            for value in registers.values():integer(value)
            for value in reads.values():integer(value)
            for key in ('state_before','state_after','date_before','date_after','day_before','day_after'):integer(clock[key])
            stable=(row['first_read_complete'] is True and row['second_read_complete'] is True
                and reads['job_plus38_first']==reads['job_plus38_second']==registers['rcx']>0
                and reads['dispatch_vptr_first']==reads['dispatch_vptr_second']==registers['rax']>0
                and reads['vtable_plus10_first']==reads['vtable_plus10_second']>0)
            target=reads['vtable_plus10_first']
            same=stable and base<=target<base+size
            need(row['target_same_image'] is same and row['target_rva']==(target-base if same else None),'Target source mapping relabelled')
            clock_good=(clock['read_complete'] is True and
                clock['state_before']==clock['state_after']==expected_owner['game_state_identity_witness']
                and clock['date_before']==clock['date_after'] and clock['day_before']==clock['day_after']
                and expected_owner['date_raw']<=clock['date_before']<=expected_owner['date_raw']+24
                and expected_owner['absolute_day_raw']<=clock['day_before']<=expected_owner['absolute_day_raw']+1)
            good=(active[tid][2] and stable and same and clock_good
                  and row['source_anchor_matches'] is True and row['owner_identity_stable'] is True)
            need(row['physical_dispatch_source_qualified'] is good,'Physical capture flag contradicted')
            need(all(row[key] is None for key in ('payer','calendar_producer','cadence','paid_maintenance_raw')),
                 'Dispatch source promoted to business attribution')
            captures.append(dict(record=row,physical_source_complete=good))
        elif kind=='unresolved_cleanup_hold':
            issues.append('unresolved_live_cleanup_hold')
        elif kind=='terminal':
            need(row is rows[-1] and terminal is None,'Original terminal not last')
            integer(row['capture_count']);need(row['known_payer_or_cadence'] is False,'Terminal business scope elevated')
            terminal=row
        else:raise ValueError('Unexpected dedicated raw row kind')
    missing=[(tid,value[0]) for tid,value in active.items() if (tid,value[0]) not in restored]
    clean=(terminal is not None and terminal['restored'] is True and terminal['detached'] is True
        and terminal['pending_event'] is False and terminal['process_exited'] is False
        and terminal['cleanup_complete'] is True and terminal['observation_thread_admission_complete'] is True
        and terminal['capture_count']==len(captures) and not missing and not issues)
    return dict(schema='xar.maintenance.dispatch_call.projection.v1',
        source_decode_target_candidate_available=bool(clean and captures and captures[0]['physical_source_complete']),
        captures=captures,cleanup_proved=clean,issues=issues,missing_restores=missing,
        paid_maintenance_raw=None,payer=None,calendar_producer=None,cadence=None,
        binary_or_live_qualification_granted=False)
