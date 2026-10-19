"""One focused compound over actual allocated-only metadata, without game/SDK."""
from pathlib import Path
from copy import deepcopy
from tempfile import TemporaryDirectory
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
    # Both pins are genuine. Substituting the administrative DONE for the CAS
    # must still be rejected; a later closed task alone is not the CAS sequence.
    with TemporaryDirectory(prefix='unrun-compound-') as td:
        wrong=deepcopy(bundle);wrong['CAS_release']=wrong['admin_done'];path=Path(td)/'wrong-cas.json'
        path.write_text(json.dumps(wrong),encoding='utf-8')
        refuses('CAS then admin DONE',lambda:invoke(path))
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
        **allocator_checks}
    if a.receipt:
        with a.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps({'receipt':subject.pin(a.receipt),'passed':1,'actual_canonical_list':True}))
    else:print(json.dumps(result))
if __name__=='__main__':main()
