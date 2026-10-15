"""Strict cold data-watch evidence consumer; no attachment or game access."""
from pathlib import Path
import argparse
import copy
import datetime as dt
import hashlib
import json
import sys

OFFSETS=(704,712,40,48)
def require(ok,message):
    if not ok:raise ValueError(message)
def integer(value,name,minimum=0,maximum=(1<<64)-1):
    require(type(value) is int and minimum<=value<=maximum,name+' exact integer/range')
    return value
def consume(rows):
    require(type(rows) is list and len(rows)>=2,'Raw rows missing')
    start=rows[0];terminal=rows[-1]
    require(start['kind']=='start' and start['schema']=='xar.maintenance.writer_pc.cold.v1','Raw schema/source mismatch')
    require(start['synthetic'] is True and start['CK3_observed'] is False and start['maintenance_attribution']=='unclosed','Cold source cannot become game producer')
    require(start['field_offsets']==list(OFFSETS) and start['DR7_write_len8_mask']==0x99990055,'Wrong4field write/LEN8 declaration')
    for offset in start['field_offsets']:integer(offset,'declared offset')
    integer(start['DR7_write_len8_mask'],'declared DR7')
    module_base=integer(start['module_base'],'module base',1);module_size=integer(start['module_size'],'module size',1)
    context=integer(start['context'],'context',1,0x7ffffffff000);character=integer(start['character'],'character',1,0x7ffffffff000);full_id=integer(start['full_id'],'fullID',1,(1<<31)-1)
    require(context%8==0,'Unaligned context')
    integer(start['pid'],'PID',1);integer(start['created'],'create',1)
    last=start['initial_values'];require(type(last) is list and len(last)==4,'Initial4values missing');last=list(last)
    for x in last:integer(x,'initial value',-(1<<63),(1<<63)-1)
    arms={};restores={};exited=set();hits=[];events={};event_masks={};qpc=0
    for row in rows[1:-1]:
        kind=row['kind']
        if kind=='arm':
            tid=integer(row['thread_id'],'thread',1);require(row['success'] is True,'Thread not actually armed')
            require(tid not in arms and type(row['saved_debug']) is list and len(row['saved_debug'])==6 and type(row['armed_debug']) is list and len(row['armed_debug'])==6,'Arm state cardinality/duplicate')
            for item in row['saved_debug']+row['armed_debug']:integer(item,'debug register')
            require(row['armed_debug'][:4]==[context+x for x in OFFSETS] and row['armed_debug'][5]&0xffff00ff==0x99990055,'Wrong live DR slots/RW/LEN8')
            require(row['saved_debug'][:4]==[0]*4 and row['saved_debug'][5]&0xffff00ff==0,'Occupied debug state was stolen')
            arms[tid]=row
        elif kind=='thread_exited':exited.add(integer(row['thread_id'],'retired thread',1))
        elif kind=='restore':
            tid=integer(row['thread_id'],'restore thread',1);require(tid in arms and tid not in exited and row['readback'] is True and row['debug']==arms[tid]['saved_debug'],'Original live DR exact readback not restored');restores[tid]=row
        elif kind=='raw_field_write_trap':
            tid=integer(row['thread_id'],'writer thread',1);require(tid in arms and tid not in exited,'Unarmed/retired writer thread')
            for key in ['offset','address','full_id','context','character']:integer(row[key],key)
            slot=integer(row['slot'],'slot',0,3);require(row['offset']==OFFSETS[slot] and row['address']==context+OFFSETS[slot] and row['address']%8==0,'Wrong raw field/address')
            require(row['full_id']==full_id and row['context']==context and row['character']==character and row['context_identity_stable'] is True,'Wrong source object identity')
            ordinal=integer(row['event_ordinal'],'event ordinal',1);hitordinal=integer(row['slot_hit_ordinal'],'slot-hit ordinal',1)
            require(hitordinal==len(hits)+1 and ordinal>=max(events,default=0),'Event/slot ordinal invalid')
            require(slot not in events.setdefault(ordinal,set()),'Repeated slot in one debug event');events[ordinal].add(slot)
            current_qpc=integer(row['qpc'],'qpc',1);require(current_qpc>=qpc,'Raw event QPC reverses');qpc=current_qpc
            integer(row['RIP_after'],'RIP_after',1)
            if module_base<=row['RIP_after']<module_base+module_size:require(integer(row['RIP_after_rva'],'mapped postRIP')==row['RIP_after']-module_base,'PostRIP image mapping differs')
            else:require(row['RIP_after_rva'] is None,'Foreign postRIP falsely mapped into exact game/source image')
            require(row['writer_instruction_start'] is None,'Data trap afterPC forged into decoded instruction start')
            require(row['before_basis']=='last_observed_sample_not_atomic_preinstruction','Old value falsely declared atomic')
            before=integer(row['before_raw'],'before',-(1<<63),(1<<63)-1);after=integer(row['after_raw'],'after',-(1<<63),(1<<63)-1)
            require(before==last[slot] and row['after_read_complete'] is True and row['same_value_write'] is (before==after),'Raw observed value/stability mismatch')
            mask=integer(row['DR6'],'DR6')&15;require(mask&(1<<slot)!=0,'Slot did not physically trap in DR6')
            require(ordinal not in event_masks or event_masks[ordinal]==mask,'Conflicting same-event DR6 masks');event_masks[ordinal]=mask
            require(row['synthetic'] is True and row['known_producer'] is False and row['military_attribution']=='unclosed','Synthetic evidence promoted to known game producer')
            require(type(row['registers']) is dict and set(row['registers'])=={'rax','rbx','rcx','rdx','r8','r9','r10','r11','rsi','rdi','rbp','rsp'},'Raw source registers missing')
            for register,value in row['registers'].items():integer(value,register)
            last[slot]=after;hits.append(row)
        else:raise ValueError('Unexpected raw kind '+str(kind))
    require(terminal['kind']=='terminal' and terminal['cleanup_complete'] is True and terminal['restored'] is True and terminal['detached'] is True and terminal['pending_event'] is False,'Cleanup/continue/detach not fully proved')
    for ordinal,slots in events.items():require(sum(1<<slot for slot in slots)==event_masks[ordinal],'Multi-slot DR6 event fields missing')
    require(integer(terminal['hit_count'],'terminal slot-hit count')==len(hits) and integer(terminal['data_event_count'],'data events')>=len(events),'Slot and debug-event counts conflated')
    require(terminal['observation_thread_admission_complete'] is True and terminal['full_window_all_writes_covered'] is False,'Observation admission failure or false global completeness')
    require(terminal['known_producer'] is False and terminal['military_attribution']=='unclosed' and terminal['CK3_observed'] is False,'Cold terminal elevated to business source')
    require(set(arms)-exited==set(restores),'Missing live-thread restore record')
    return dict(raw_slot_hits=len(hits),recorded_data_events=len(events),unique_offsets=sorted({x['offset'] for x in hits}),same_value_write_count=sum(x['same_value_write'] for x in hits),writer_threads=sorted({x['thread_id'] for x in hits}),maintenance_attribution='unclosed',known_producer=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(not args.output.exists(),'Append-only consumer output exists')
    results=[];positive=None
    for mode in ['four-writes','same-value','new-worker','timeout','changed-context']:
        raw=args.run_root/mode/'observer.raw.ndjson';rows=[json.loads(x) for x in raw.read_text().splitlines()];result=consume(rows)
        require(result['raw_slot_hits']==(4 if mode in ('four-writes','same-value','new-worker') else 0),'Expected actual trap count differs')
        if mode=='same-value':require(result['same_value_write_count']==4,'Actual same-value4writes absent')
        if mode=='new-worker':
            owned=json.loads((args.run_root/mode/'RESULT.actual.json').read_bytes());require(result['writer_threads']==[owned['actual_target_result']['worker_tid']] and result['writer_threads'][0]!=owned['actual_target_result']['main_tid'],'New worker actual raw evidence absent')
        results.append(dict(mode=mode,result=result,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest()))
        if mode=='four-writes':positive=rows
    require(positive is not None,'Actual base evidence absent')
    mutations=[]
    def negative(label,change):
        value=copy.deepcopy(positive);change(value)
        try:consume(value)
        except (ValueError,TypeError,KeyError,IndexError):mutations.append(dict(name=label,rejected=True));return
        raise RuntimeError('Malformed counterexample accepted '+label)
    first=next(i for i,x in enumerate(positive) if x['kind']=='raw_field_write_trap')
    arm=next(i for i,x in enumerate(positive) if x['kind']=='arm')
    restore=next(i for i,x in enumerate(positive) if x['kind']=='restore')
    negative('postRIP_as_instruction_start',lambda r:r[first].__setitem__('writer_instruction_start',r[first]['RIP_after']))
    negative('wrong_write_length',lambda r:r[arm]['armed_debug'].__setitem__(5,0x11110055))
    negative('wrong_offset',lambda r:r[first].__setitem__('offset',41))
    negative('unaligned_address',lambda r:r[first].__setitem__('address',r[first]['address']+1))
    negative('object_fullID_mismatch',lambda r:r[first].__setitem__('full_id',31255))
    negative('fake_known_producer',lambda r:r[first].__setitem__('known_producer',True))
    negative('synthetic_as_CK3',lambda r:r[0].__setitem__('CK3_observed',True))
    negative('military_closed',lambda r:r[-1].__setitem__('military_attribution','closed'))
    negative('restore_flag_without_readback',lambda r:r[restore].__setitem__('readback',False))
    negative('restored_wrong_DR7',lambda r:r[restore]['debug'].__setitem__(5,1))
    negative('detach_failed',lambda r:r[-1].__setitem__('detached',False))
    negative('pending_event_left',lambda r:r[-1].__setitem__('pending_event',True))
    negative('thread_admission_failed',lambda r:r[-1].__setitem__('observation_thread_admission_complete',False))
    negative('falsely_global_complete',lambda r:r[-1].__setitem__('full_window_all_writes_covered',True))
    negative('atomic_before_fabricated',lambda r:r[first].__setitem__('before_basis','atomic_preinstruction'))
    negative('DR6_did_not_hit',lambda r:r[first].__setitem__('DR6',0))
    negative('slotcount_as_eventordinal',lambda r:r[first].__setitem__('slot_hit_ordinal',10))
    negative('float_as_address',lambda r:r[first].__setitem__('address',float(r[first]['address'])))
    negative('float_as_offset',lambda r:r[first].__setitem__('offset',float(r[first]['offset'])))
    negative('float_as_fullid',lambda r:r[first].__setitem__('full_id',float(r[first]['full_id'])))
    negative('wrong_postRIP_rva',lambda r:r[first].__setitem__('RIP_after_rva',r[first]['RIP_after_rva']+1))
    negative('bool_as_address',lambda r:r[first].__setitem__('address',True))
    negative('raw_registers_missing',lambda r:r[first].__setitem__('registers',{}))
    negative('drop_live_restore',lambda r:r.pop(restore))
    report=dict(schema='xar.maintenance.writer_pc.cold.strict-consumer.v1',status='PASS',observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),python_optimization=sys.flags.optimize,actual_owned_cases=results,malformed_counterexamples=mutations,negative_case_count=len(mutations),no_runtime_actions=True,known_producer=False,maintenance_attribution='unclosed')
    with args.output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(dict(status='PASS',actual_owned_cases=len(results),negative_cases=len(mutations),optimization=sys.flags.optimize,known_producer=False)))

if __name__=='__main__':main()
