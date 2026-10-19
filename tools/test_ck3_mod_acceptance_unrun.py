"""One focused compound over actual allocated-only metadata, without game/SDK."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from datetime import datetime,timezone
import argparse,hashlib,json
import ck3_mod_acceptance_unrun as subject
from ck3_mod_acceptance_allocate import read_failed_runtime_release,current_screen_absent

def need(value,message):
    if not value:raise AssertionError(message)

def allocator_original_checks(bundle,machine,keeper_stamps):
    """Exercise the real pinned triplet and its three association boundaries."""
    argv=subject._allocator_argv(bundle,machine,keeper_stamps)
    if 'allocator_intent' not in bundle:return {'allocator_evidence_form':'command-result'}
    originals={key:subject._read(bundle[key]['path']) for key in
        ('allocator_intent','allocator_process','allocator_exit')}
    actual_read=subject._read
    def refuses(key,field,value,expected):
        def changed(path):
            row=actual_read(path)
            if Path(path).resolve()==Path(bundle[key]['path']).resolve():row={**row,field:value}
            return row
        with patch.object(subject,'_read',side_effect=changed):
            try:subject._allocator_argv(bundle,machine,keeper_stamps)
            except ValueError as error:need(expected in str(error),(expected,str(error)))
            else:raise AssertionError('Unrelated allocator original admitted: '+field)
    refuses('allocator_exit','pid',originals['allocator_process']['pid']+1,'intent/process/wait0')
    refuses('allocator_process','argv',argv+['--unrelated'],'intent/process/wait0')
    refuses('allocator_exit','completed_at_utc',originals['allocator_intent']['at_utc'],'wait time')
    # Exercise the pre-existing combined receipt contract with an in-memory
    # unit fixture only; no historical command-result is created or rewritten.
    combined={'allocator_result':bundle['allocator_exit']}
    fixture={'machine_id':machine,'argv':argv,'exit_code':0,'shell':False,
             'finished_at_utc':originals['allocator_exit']['completed_at_utc']}
    with patch.object(subject,'_read',return_value=fixture):
        need(subject._allocator_argv(combined,machine,keeper_stamps)==argv,'Combined allocator receipt compatibility failed')
    return {'allocator_evidence_form':'original-intent-process-popen-wait',
        'pid_argv_time_mismatch_rejected':True,'combined_receipt_compatibility':True}

def release_stage_checks():
    """Synthetic contract branches only; the main consumer reads real originals."""
    task='unrun-release-fixture';seq=12
    keeper={'task_id':task,'thread_exited':True,'last_sequence':10}
    done={'ok':True,'event':{'task_id':task,'resources':[],'sequence':seq,'kind':'completed'},
          'task':{'task_id':task,'state':'done','resources':[],'last_sequence':seq}}
    direct_source={'schema':'xar-screen-release-canonical-reconstruction-v1',
        'source_event_stream':'synthetic-only','source_event_byte_offset':100,
        'source_event_raw_sha256':'a'*64,'event':deepcopy(done['event']),'task':deepcopy(done['task'])}
    status=deepcopy(done);status['event'].update(kind='status',sequence=11)
    def invoke(cas=done,final=done,first=direct_source,last=direct_source,stop=keeper,release=done):
        return subject._release_stages(stop,cas,final,first,last,release,task)
    need(invoke()=='direct-completed','Single canonical completed branch rejected')
    need(invoke(cas=status)=='status-then-completed','Original strict two-stage branch rejected')
    rejected=0
    def refuses(expected,**kwargs):
        nonlocal rejected
        try:invoke(**kwargs)
        except ValueError as error:need(expected in str(error),(expected,str(error)));rejected+=1
        else:raise AssertionError('Invalid release stage admitted: '+repr(kwargs))
    for event_key,bad in (('task_id','other-task'),('resources',['ck3-screen:acquired'])):
        for key in ('cas','final'):
            wrong=deepcopy(done);wrong['event'][event_key]=bad
            refuses('CAS task/resources',**{key:wrong})
    for badseq in (10,11,13):
        wrong=deepcopy(done);wrong['event']['sequence']=badseq
        refuses('CAS then admin DONE',cas=wrong)
    wrong=deepcopy(status);wrong['event']['sequence']=seq
    refuses('CAS then admin DONE',cas=wrong)
    for key,bad in (('source_event_byte_offset',101),('source_event_raw_sha256','b'*64),
                    ('source_event_stream','different-original'),('schema','other-schema')):
        wrong=deepcopy(direct_source);wrong[key]=bad
        refuses('CAS then admin DONE',first=wrong)
    wrong=deepcopy(done);wrong['event']['different_original_event']=True
    refuses('CAS then admin DONE',cas=wrong)
    wrong=deepcopy(done);wrong['task']['different_original_task']=True
    refuses('CAS then admin DONE',cas=wrong)
    for key,bad in (('state','waiting'),('resources',['ck3-screen:acquired']),('last_sequence',13)):
        wrong=deepcopy(done);wrong['task'][key]=bad
        refuses('CAS then admin DONE',cas=wrong,final=wrong,release=wrong)
    refuses('CAS then admin DONE',stop={**keeper,'last_sequence':seq})
    refuses('CAS then admin DONE',release={**done,'different_release':True})
    line=lambda value:(json.dumps(value,separators=(',',':'))+'\n').encode()
    one=line(done['event']);two=line(status['event'])+one
    direct=subject._journal_events(one,100,seq,seq)
    need(len(direct)==1 and direct[seq]==(100,one,done['event']),
         'One original journal event/offset/bytes not preserved')
    separate=subject._journal_events(two,100,11,seq)
    need(len(separate)==2 and separate[seq][0]==100+len(line(status['event'])),
         'Two-stage journal event offsets differ')
    for raw,release_seq,done_seq,expected in ((one+one,seq,seq,'Duplicate original'),
            (one,11,seq,'Exact original'),(one,seq,13,'Exact original')):
        try:subject._journal_events(raw,100,release_seq,done_seq)
        except ValueError as error:need(expected in str(error),(expected,str(error)));rejected+=1
        else:raise AssertionError('Missing/duplicate journal event admitted')
    return {'synthetic_two_stage_and_direct_completed_branches_passed':True,
        'synthetic_mixed_original_wrong_sequence_task_resources_and_lease_rejections':rejected,
        'one_or_two_exact_journal_event_offsets_preserved':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--task-bus-root',type=Path,required=True);p.add_argument('--receipt',type=Path);a=p.parse_args()
    bundle=subject._read(a.bundle);live=Path(bundle['ready']['path']).parent
    freeze=subject._read(bundle['frozen']['path']);keeper=Path(bundle['keeper']['path']).parent
    release=read_failed_runtime_release(Path(bundle['admin_done']['path']))
    bus_script=a.task_bus_root/'bin/codex_task_bus.py'
    bus=current_screen_absent(Path(freeze['lease_anchor']),a.task_bus_root,
        freeze['files'][str(bus_script.resolve())]['sha256'],None)
    def invoke(path=a.bundle,packet=None):
        return subject.validate_allocated_unrun(live,freeze,path,keeper,release,bus if packet is None else packet)
    verdict=invoke()
    keeper_ready=subject._read(bundle['keeper_ready']['path']);keeper_report=subject._read(bundle['keeper']['path'])
    allocator_checks=allocator_original_checks(bundle,bundle['machine_id'],
        [datetime.fromisoformat(keeper_ready['at_utc']),datetime.fromisoformat(keeper_report['at_utc'])])
    need(verdict['mode']=='previous-shared-allocated-unrun-idle','Allocated-only closure mode differs')
    need(verdict['failure_cleanup']['typed_normal_exit_proven'] is False,'Unexpected normal exit credit')
    need(verdict['failure_cleanup']['original_host_exit_code'] is None,'Unexpected host exit code')
    need('counter' in bundle and 'counter' not in verdict['failure_cleanup']['original_evidence'],
         'Mutable counter leaked into predecessor original evidence')
    def refuses(expected,call):
        try:call()
        except ValueError as error:need(expected in str(error),(expected,str(error)))
        else:raise AssertionError('Unsafe actual branch was admitted: '+expected)
    for key,value in (('state','waiting'),('resources',['ck3-screen:acquired']),('last_sequence',release['task']['last_sequence']+1)):
        wrong=deepcopy(bus);next(row for row in wrong['tasks'] if row['task_id']==freeze['screen_task'])[key]=value
        refuses('Current allocated-unrun task readback differs',lambda:invoke(packet=wrong))
    exists=Path.exists
    with patch.object(Path,'exists',lambda path: True if path==live/'host-started.json' else exists(path)):
        refuses('host/native/control/Save',invoke)
    original=subject._read
    def alive(path):
        value=original(path)
        if Path(path).resolve()==Path(bundle['keeper']['path']).resolve():value={**value,'thread_exited':False}
        return value
    with patch.object(subject,'_read',side_effect=alive):refuses('keeper STOP/wait0',invoke)
    release_checks=release_stage_checks()
    result={'test':'actual_canonical_list_allocated_unrun_and_unsafe_state_resources_sequence_rejected',
        'passed':1,'machine_id':bundle['machine_id'],'run_id':bundle['run_id'],
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'canonical_public_method':'ck3_mod_acceptance_allocate.current_screen_absent',
        'canonical_list_source':subject.pin(bus_script),
        'actual_list_task':next(row for row in bus['tasks'] if row['task_id']==freeze['screen_task']),
        'parsed_packet_canonical_json_sha256':hashlib.sha256(json.dumps(bus,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
        'original_task_fields_all_exact':True,'only_declared_derived_extras':['age_seconds','stale'],
        'unsafe_state_resources_last_sequence_rejected':True,
        'SDK_or_game':False,'normal_exit_credit':False,'actual_process_inventory_scanned_once':True,
        **allocator_checks,**release_checks}
    if a.receipt:
        with a.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps({'receipt':subject.pin(a.receipt),'passed':1,'actual_canonical_list':True}))
    else:print(json.dumps(result))
if __name__=='__main__':main()
