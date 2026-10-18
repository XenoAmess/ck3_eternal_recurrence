"""Root-only next-scene argv/binding preparation; never launches a sampler or SDK.

The caller supplies fresh existing MCP business bodies and a separately admitted
new live build. --read-process-identity only reads Win32 process/thread metadata;
it never reads an EXE, CK3 memory, debug registers, or suspends a thread.
"""
from pathlib import Path
import argparse, ctypes, hashlib, json, os, re, sys
from datetime import datetime, timezone

EXE_SHA='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
def need(ok,label):
    if not ok:raise ValueError(label)
def integer(v,lo=0,hi=(1<<64)-1):return type(v) is int and lo<=v<=hi
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(path,limit=2*1024*1024):
    raw=path.read_bytes();need(0<len(raw)<=limit,'bounded '+str(path));return json.loads(raw),{'path':str(path.resolve()),'bytes':len(raw),'sha256':digest(raw)}
def body(value):
    need(type(value) is dict,'JSON object');value=value.get('body',value);need(type(value) is dict,'business body');return value
def validate_source_dir(value):
    need(type(value) is str and bool(value), 'actual source_dir text required')
    path = Path(value)
    need(path.is_absolute() and path.name == 'refill_add_live_12004',
         'absolute fixed-basename source_dir required')
    need(path.is_dir(), 'actual existing source_dir required; no future placeholder')
    return value
def os_identity(pid,tid):
    need(os.name=='nt','Win32 identity reader requires Windows')
    from ctypes import wintypes as w
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.OpenThread.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenThread.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
    k.GetProcessIdOfThread.argtypes=[w.HANDLE];k.GetProcessIdOfThread.restype=w.DWORD
    k.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4;k.GetProcessTimes.restype=w.BOOL
    k.GetThreadTimes.argtypes=k.GetProcessTimes.argtypes;k.GetThreadTimes.restype=w.BOOL
    k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)];k.QueryFullProcessImageNameW.restype=w.BOOL
    process=k.OpenProcess(0x1000,False,pid);need(bool(process),'OpenProcess QUERY_LIMITED_INFORMATION')
    thread=None
    def times(handle,fn):
        values=[w.FILETIME() for _ in range(4)]
        need(bool(fn(handle,*[ctypes.byref(v) for v in values])),'exact Win32 FILETIME read')
        return (int(values[0].dwHighDateTime)<<32)|int(values[0].dwLowDateTime)
    try:
        buffer=ctypes.create_unicode_buffer(32768);size=w.DWORD(len(buffer))
        need(bool(k.QueryFullProcessImageNameW(process,0,buffer,ctypes.byref(size))),'process image name read')
        need(Path(buffer.value).name.lower()=='ck3.exe','owned current process must be ck3.exe')
        created=times(process,k.GetProcessTimes)
        thread=k.OpenThread(0x0800,False,tid);need(bool(thread),'OpenThread QUERY_LIMITED_INFORMATION')
        need(k.GetProcessIdOfThread(thread)==pid,'native owner thread belongs to current PID')
        thread_created=times(thread,k.GetThreadTimes)
        need(times(process,k.GetProcessTimes)==created,'process generation changed during identity read')
        return {'pid':pid,'thread_id':tid,'process_created_filetime':created,
          'thread_created_filetime':thread_created,'image_path':buffer.value,
          'method':'Win32 query-only GetProcessTimes/GetThreadTimes; no float conversion',
          'debug_registers_read_or_written':False}
    finally:
        if thread:k.CloseHandle(thread)
        k.CloseHandle(process)


def select_positive_prepare_target(frame, packet, *, army_id, mode='observed_prepared',
                                   regiment=None, slot=None):
    """Select a conditional positive write; never observe preparation or an ADD.

    Repository dependencies are supplied through the caller's normal package
    path. Duplicate manager/DATA occurrences remain ordered and are not deduped.
    """
    from copy import deepcopy
    from xar_autoplayer.bridge.army_persistent_refill_eligibility_12004 import classify_army_persistent_refill_eligibility_12004
    from xar_autoplayer.bridge.army_scoped_ordered_refill_contract import normalize_scoped_ordered_refill_inputs_v1
    from xar_autoplayer.bridge.army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
    from xar_autoplayer.bridge.army_scoped_ordered_refill_projection import project_scoped_observed_prepared_ordered_refill
    need(integer(army_id, -(1 << 31), (1 << 31)-1) and army_id != -1, 'actual public Army FullID')
    need(mode in ('observed_prepared', 'fixed_chunk0_prepare'), 'explicit ordered entry mode')
    need(packet.get('ordered_refill_entry_mode', mode) == mode, 'same query entry mode')
    need(regiment is None or integer(regiment, 0, 0xFFFFFFFE), 'target full Regi u32')
    need(slot is None or integer(slot, 0, 6), 'target physical slot')
    classified = classify_army_persistent_refill_eligibility_12004(frame, packet, army_id=army_id)
    rows = [r for r in packet['army_strengths'] if r.get('army_id') == army_id]
    need(len(rows) == 1, 'unique same-frame Army')
    row = deepcopy(rows[0])
    family = normalize_scoped_ordered_refill_inputs_v1(row.get('scoped_ordered_refill_inputs_v1'))
    need(family is not None and family['status'] == 'available'
         and family['unavailable_reason'] is None, 'complete scoped family required')
    need(family['subject_army_id'] == army_id
         and family['subject_carmy_id'] == row['native_carmy_id'], 'same scoped full Army identity')
    need(all(len(p['chunks']) == 7 and p['unavailable_reason'] is None
             for p in family['persistent_regiments']), 'all scoped physical seven required')
    row['scoped_ordered_refill_inputs_v1'] = family
    row['regiment_replenishment_records_v1'] = normalize_regiment_replenishment_records_v1(
        row['regiment_replenishment_records_v1'])
    if mode == 'fixed_chunk0_prepare':
        from xar_autoplayer.bridge.army_fixed_chunk0_preparation_contract import normalize_fixed_chunk0_preparation_inputs_v1
        from xar_autoplayer.bridge.army_fixed_chunk0_preparation_projection import project_fixed_chunk0_preparation_family_v1
        from xar_autoplayer.bridge.army_prepare_scoped_ordered_refill_assembly import project_fixed_chunk0_prepare_scoped_ordered_refill_v1
        prep = normalize_fixed_chunk0_preparation_inputs_v1(
            row.get('fixed_chunk0_preparation_inputs_v1'), expected_army_id=army_id,
            expected_carmy_id=row['native_carmy_id'])
        need(prep is not None and prep['ready'] is True
             and prep['referenced_persistent_ids_complete'] is True, 'complete same-row preparation family')
        preparation = project_fixed_chunk0_preparation_family_v1(
            prep, army_id=army_id, native_carmy_id=row['native_carmy_id'])
        need(preparation['preparation_ready'] is True, 'known conditional preparation')
        projection = project_fixed_chunk0_prepare_scoped_ordered_refill_v1(row, preparation)
    else:
        projection = project_scoped_observed_prepared_ordered_refill(row)
    need(projection['ordered_core_ready'] is True and not projection['missing_inputs'],
         'complete shared ordered projection required')
    persistents = {p['persistent_regiment_id']: p for p in family['persistent_regiments']}
    physical = {(p['persistent_regiment_id'], p['chunk_index']): p
                for p in classified['physical_chunks']}
    for occurrence in projection['occurrences']:
        identity = occurrence['persistent_regiment_id']
        if regiment is not None and (identity & 0xFFFFFFFF) != regiment:
            continue
        for write in occurrence['writes']:
            index, qindex, q = write['physical_index'], write['q_ordinal_raw'], write['q']
            if slot is not None and index != slot:
                continue
            # The final shared buffer can overwrite an earlier calculated_q.
            if not integer(q, 1, (1 << 31)-1):
                continue
            need(occurrence['q_buffer'][qindex] == q, 'write/final shared q mismatch')
            chunk = persistents[identity]['chunks'][index]
            if chunk['native_unit_position_eligible'] is not True:
                continue
            data = physical.get((identity, index))
            if data is None:
                continue
            need((chunk['owner_persistent_regiment_id'] == identity
                  == chunk['owner_resolved_full_id']) and identity != -1,
                 'actual full persistent owner identity')
            for key in ('current_soldiers', 'maximum_soldiers', 'state_raw'):
                need(chunk[key] == data[key], 'same-frame scoped/DATA physical '+key)
            need(persistents[identity]['prepared_fraction_raw'] == data['observed_prepared148_raw'],
                 'same-frame observed prepared148')
            arrg, carmy = chunk['army_regiment_id_raw'], row['native_carmy_id']
            need(arrg != -1 and chunk['associated_arrg_resolved_full_id'] == arrg
                 and chunk['associated_arrg_magic_raw'] == 0x41725267,
                 'actual full associated ArRg')
            need(carmy != -1 and chunk['associated_army_raw_full_id'] == carmy
                 == chunk['associated_army_resolved_full_id'], 'actual full associated CArmy')
            need(chunk['associated_unit_raw_full_id'] != -1
                 and chunk['associated_unit_raw_full_id'] == chunk['associated_unit_resolved_full_id'],
                 'actual full associated CUnit')
            aliases = [r for r in classified['DATA_occurrences']
                       if r['persistent_regiment_id'] == identity and r['chunk_index'] == index]
            need(aliases and all(r['army_regiment_id'] == arrg for r in aliases),
                 'complete selected DATA aliases/full ArRg')
            return {'schema': 'xar.ck3.refill_ADD_12004.positive_prepare_target.v1',
                    'ordered_refill_entry_mode': mode, 'input_basis': projection['input_basis'],
                    'conditional_request_only': True, 'actual_preparation_observed': False,
                    'actual_ADD_observed': False, 'regi_full_id_u32': identity & 0xFFFFFFFF,
                    'physical_slot': index, 'arrg_full_id_i32': arrg, 'army_full_id_i32': carmy,
                    'q_index': qindex, 'conditional_shared_q_i32': q,
                    'native_unit_position_eligible': True, 'selected_write': deepcopy(write),
                    'selected_occurrence_stored_index': occurrence['stored_index'],
                    'ordered_occurrences': projection['occurrences'], 'DATA_occurrences': aliases,
                    'selected_eligibility': [data]}
    raise ValueError('no positive shared-q DATA target with actual native position eligibility')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['repo','frame','diagnostics','army-packet','live-build-admission','output-root']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--army-id',type=int,required=True);p.add_argument('--regiment',type=lambda x:int(x,0))
    p.add_argument('--slot',type=int);p.add_argument('--timeout-ms',type=int,default=30000)
    p.add_argument('--ordered-refill-entry-mode',choices=['observed_prepared','fixed_chunk0_prepare'],default='observed_prepared')
    p.add_argument('--read-process-identity',action='store_true',required=True)
    a=p.parse_args();need(not a.output_root.exists(),'fresh output root required')
    need((a.regiment is None or integer(a.regiment,0,0xFFFFFFFE)) and (a.slot is None or integer(a.slot,0,6)),'full Regi u32 and physical slot')
    need(integer(a.timeout_ms,1000,300000),'finite sampler wall timeout')
    sys.path.insert(0,str(a.repo/'tools'));from ck3_live_run_id import current_machine_id
    sys.path.insert(0,str(a.repo/'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge.army_persistent_refill_eligibility_12004 import classify_army_persistent_refill_eligibility_12004
    from xar_autoplayer.bridge.army_scoped_ordered_refill_contract import normalize_scoped_ordered_refill_inputs_v1
    machine=current_machine_id();frame,pf=read(a.frame);diag,pd=read(a.diagnostics);packet,pp=read(a.army_packet)
    frame,diag,packet=body(frame),body(diag),body(packet)
    gate,pg=read(a.live_build_admission);need(gate.get('schema')=='xar.ck3.refill_ADD_12004.live_owner_admission.v1','Root live admission schema')
    need(gate.get('machine_id')==machine and gate.get('exact_executable_sha256')==EXE_SHA,'current-machine exact4 live admission')
    need(gate.get('episode_run_id')==frame.get('episode_run_id'),'Root admission is for this future episode')
    native_campaign_null = frame.get('episode_run_id') is None
    if native_campaign_null:
        need(frame.get('episode_projection') == gate.get('episode_projection') == 'native_campaign',
             'null/absent game episode requires explicit ordinary native campaign admission')
    need(integer(gate.get('scene_sequence'),199) and type(gate.get('scene_run_id')) is str,'R198 explicitly has no observer; bind a later allocated scene')
    need(gate.get('new_live_build_and_SYSTEM_verified') is True and gate.get('next_scene_capacity_and_observer_admitted') is True,'Root actual build/SYSTEM/capacity/window admission required')
    source_dir=validate_source_dir(gate.get('source_dir'))
    need(gate.get('target')=='refill_add_hwprobe_12004','admitted C-source live target')
    worker = gate.get('observer_thread_policy') == 'carrier_owned_target'
    need(gate.get('observer_thread_policy') in (None, 'fixed_tid', 'carrier_owned_target'), 'explicit observer thread policy')
    maximum_threads = gate.get('maximum_owned_threads') if worker else None
    if worker:
        need(integer(maximum_threads, 1, 256), 'explicit finite worker ownership bound')
    definitions = {'XAR_ENABLE_REFILL_ADD_HWPROBE_12004':'ON','XAR_ENABLE_REFILL_STACK_Q_COLD_12004':'OFF','XAR_ENABLE_REFILL_V3_COLD_PROBE_12004':'OFF'}
    if worker:
        definitions.update(XAR_ENABLE_REFILL_CARRIER_THREAD_DISCOVERY_12004='ON', XAR_ENABLE_REFILL_V5_COLD_PROBE_12004='OFF')
    need(gate.get('cmake_defines') == definitions, 'exact admitted live-only compile options')
    need(gate.get('carrier_bridge_source_epoch')==20261018 and type(gate.get('carrier_bridge_source_epoch')) is int and gate.get('carrier_source_and_runtime_verified') is True,'Root actual carrier source/runtime gate')
    module=gate.get('carrier_bridge_module_path');need(type(module) is str and Path(module).is_absolute() and Path(module).name.lower()=='xar_ck3_bridge.dll','actual admitted carrier DLL path')
    exe=Path(gate['observer_exe']);need(exe.name=='refill_add_hwprobe_12004.exe','production observer basename')
    for key in ['source_admission_receipt_sha256','observer_exe_sha256','build_result_sha256','SYSTEM_receipt_sha256']:
        need(type(gate.get(key)) is str and re.fullmatch('[0-9a-f]{64}',gate[key]) is not None,'actual receipt pin '+key)
    fdiag=frame.get('diagnostics') or {};mail=(diag.get('last_heartbeat') or {}).get('main_thread_query_mailbox_v1') or {}
    need(diag.get('connected') is True and diag.get('bridge_pid')==fdiag.get('bridge_pid') and diag.get('connection_generation')==fdiag.get('connection_generation'),'same connected process/generation')
    pid=diag.get('bridge_pid');tid=mail.get('owner_tid')
    need(integer(pid,1,0xFFFFFFFF) and integer(tid,1,0xFFFFFFFF) and mail.get('current_tid')==tid,'verified native main thread, not SDK thread')
    for key in ['installed','ready','stamp_read_success','application_main_observed','paused_main_thread_observed','paused']:
        need(mail.get(key) is True,'fresh mailbox proof '+key)
    need(mail.get('stop') is False and type(mail.get('failure')) is int and mail['failure']==0 and mail.get('date_raw')==frame.get('date_raw'),'same paused date/current mailbox')
    # rng_owner_tid is intentionally diagnostic-only in ReadExecutionStamp.
    positive=select_positive_prepare_target(frame,packet,army_id=a.army_id,mode=a.ordered_refill_entry_mode,regiment=a.regiment,slot=a.slot)
    a.regiment=positive['regi_full_id_u32'];a.slot=positive['physical_slot']
    classified=classify_army_persistent_refill_eligibility_12004(frame,packet,army_id=a.army_id)
    rows=[r for r in packet['army_strengths'] if r.get('army_id')==a.army_id];need(len(rows)==1,'unique current Army row');row=rows[0]
    family=normalize_scoped_ordered_refill_inputs_v1(row.get('scoped_ordered_refill_inputs_v1'))
    need(family is not None and family['subject_army_id']==a.army_id and family['subject_carmy_id']==row['native_carmy_id'],'complete same subject scoped family')
    selected=[r for r in family['persistent_regiments'] if (r['persistent_regiment_id']&0xFFFFFFFF)==a.regiment]
    need(len(selected)==1 and len(selected[0]['chunks'])==7 and selected[0]['unavailable_reason'] is None,'selected complete physical seven')
    chunk=selected[0]['chunks'][a.slot];arrg=chunk['army_regiment_id_raw'];carmy=row['native_carmy_id']
    need((chunk['owner_persistent_regiment_id']&0xFFFFFFFF)==a.regiment and integer(chunk['q_ordinal_raw'],0,6),'selected actual owner/q-index')
    need(integer(arrg,-(1<<31),(1<<31)-1) and arrg!=-1 and chunk['associated_arrg_resolved_full_id']==arrg,'exact associated full ArRg')
    need(chunk['associated_army_raw_full_id']==carmy==chunk['associated_army_resolved_full_id'],'exact associated full CArmy')
    occurrences=[r for r in classified['DATA_occurrences'] if (r['persistent_regiment_id']&0xFFFFFFFF)==a.regiment and r['chunk_index']==a.slot]
    need(occurrences and all(r['army_regiment_id']==arrg for r in occurrences),'selected complete DATA alias association')
    identity=os_identity(pid,tid)
    binding={'schema':('xar.ck3.refill_ADD_12004.owner_binding.v4' if worker else ('xar.ck3.refill_ADD_12004.owner_binding.v3' if native_campaign_null else 'xar.ck3.refill_ADD_12004.owner_binding.v2')),'machine_id':machine,'exact_executable_sha256':EXE_SHA,
      'pid':pid,'process_created_filetime':identity['process_created_filetime'],'thread_id':None if worker else tid,
      'regi_full_id_u32':a.regiment,'physical_slot':a.slot,'arrg_full_id_i32':arrg,'army_full_id_i32':carmy,
      'connection_generation':diag['connection_generation'],'episode_run_id':frame.get('episode_run_id'),
      'carrier_module_path':module,'carrier_source_epoch':20261018,'source_dir':source_dir,
      'source_admission_receipt_sha256':gate['source_admission_receipt_sha256'],
      'observer_build_and_SYSTEM_gate_receipt_sha256':pg['sha256']}
    if native_campaign_null:binding['episode_projection']='native_campaign'
    if worker:
        binding.update(episode_projection=frame.get('episode_projection'), admission_mailbox_thread_id=tid,
            thread_policy='carrier_owned_target', maximum_owned_threads=maximum_threads)
    out=a.output_root.resolve();raw=out/'observer.raw.ndjson';ready=out/'observer.ready.json'
    argv=[str(exe),'--enable','--pid',str(pid),'--thread',str(0 if worker else tid),'--regiment',str(a.regiment),'--slot',str(a.slot),
      '--created',str(identity['process_created_filetime']),'--timeout-ms',str(a.timeout_ms),'--raw',str(raw),'--ready',str(ready),'--machine-id',machine]
    if worker:argv += ['--thread-policy','carrier-owned-target','--max-threads',str(maximum_threads)]
    consume=[sys.executable,'-B','-X','utf8',str(a.repo/'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/consume_live_refill_add.py'),
      '--raw',str(raw),'--binding',str(out/'owner-binding.json'),'--output',str(out/'instruction-item.json')]
    result={'schema':('xar.ck3.refill_ADD_12004.prepared_live_argv.v4' if worker else ('xar.ck3.refill_ADD_12004.prepared_live_argv.v3' if native_campaign_null else 'xar.ck3.refill_ADD_12004.prepared_live_argv.v2')),'machine_id':machine,'observed_at':datetime.now(timezone.utc).isoformat(),
      'input_pins':[pf,pd,pp,pg],'source_dir':source_dir,'positive_prepare_target':positive,'identity':identity,'native_argv':argv,'consume_argv':consume,'DATA_occurrences':occurrences,
      'selected_eligibility':[r for r in classified['physical_chunks'] if (r['persistent_regiment_id']&0xFFFFFFFF)==a.regiment and r['chunk_index']==a.slot],
      'carrier_module_path':module,'carrier_source_epoch':20261018,
      'consume_argv_requires_core_observation':True,'consume_core_observation_argument_name':'--core-observation',
      'Root_admission_authority_verified_here':False,'exe_content_rehashed_here':False,'observer_launched':False,'actual_ADD_observed':False,
      'ready_must_match':{'schema':('xar.ck3.refill_ADD_12004.hwprobe_ready.v4' if worker else 'xar.ck3.refill_ADD_12004.hwprobe_ready.v3'),'machine_id':machine,'pid':pid,'process_created_filetime':identity['process_created_filetime'],
        'thread_id':None if worker else tid,'regi_full_id_u32':a.regiment,'physical_slot':a.slot,'site_0':'0x2A98B88','site_1':'0x2A98B8B','carrier_module_path':module,'carrier_source_epoch':20261018},
      'no_new_MCP_query_required':True,'natural_core_token':None,'full_R06_qualified':False}
    if worker:
        result['ready_must_match'].update(thread_policy='carrier_owned_target', maximum_owned_threads=maximum_threads)
        result.update(consume_argv_requires_core_observation=False, consume_argv_requires_target_core_proof=True,
            consume_core_observation_argument_name=None, consume_full_parent_argument_name='--full-parent-proof',
            observer_thread_policy='carrier_owned_target', maximum_owned_threads=maximum_threads,
            actual_callback_thread_id=None)
        consume += ['--create-target-core-proof', str(out/'target-core-proof.json')]
    out.mkdir(parents=True,exist_ok=False)
    for name,value in [('owner-binding.json',binding),('PREPARED.actual.json',result)]:
        with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'prepared':str(out/'PREPARED.actual.json'),'observer_launched':False,'actual_ADD_observed':False}))
if __name__=='__main__':main()
