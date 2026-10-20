"""A03 cold owner metadata, composed in RAM; no write, gate publication, or RPC."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OWN=Path(__file__).resolve().parent
MACHINE='xenoamess-full-tower-eb9d2c1186'
DEFAULT_RUNTIME=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
FULL_SHA='332fabb30cc6f6a62d2f8974cd6e55d12036425f5b7f02aa8cf56709af6ee42a'
FINAL_PIN=(388118,'45e491d5496e4fe12d77da3d9caba69db68f38ef058a1e0b2dc19701f05891d0')
POLICY_PIN=(18574,'66b58de84d8e773ef5d37636c1402f836aa52b6f0489e76f2ed327f1d4c63159')
COLD_PRE_PIN=(4396,'6bf7d89f212c0bfe4899bfb87091bc866ddf32379f41f71b211f8d601bd2ef1d')
BINDING_NAME='ROOT-C23-A03-ACTUAL-RECORDING-BINDING.json'
ADMISSION_NAME='ROOT-P37C23-COLD-RESUME-ADMISSION.json'
OWNER_PINS_NAME='ROOT-P37C23-OWNER-INPUT-PINS.json'
GATE_NAME='ROOT-C23-SDKOWNER-CREATE-ADMITTED.json'
OUTPUT_NAMES=(BINDING_NAME,ADMISSION_NAME,OWNER_PINS_NAME,GATE_NAME)
FEEDER_NAMES=('root_p37c23_same_game_loop_feeder100.py','root_continuity_window_c23_100.py','launch_c23_feeder100.py')
STOPS=('STOP-OWNED-GAME-C23','EXIT-SDK-P37C23','ROOT-SDK-EXIT-REQUESTED-C23.json',
 'REQUEST-ADMISSION-CLOSED-C23','ROOT-GAME-CLOSE-REQUEST-C23.json')


def require(ok,why):
    if not ok:raise ValueError('A03 cold owner metadata denied: '+why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def enc(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')


def raw(path,limit=1048576):
    path=Path(path)
    require(path.is_file() and not path.is_symlink(),'exact ordinary file required')
    with path.open('rb') as stream:data=stream.read(limit+1)
    require(len(data)<=limit,'bounded named metadata/source read required')
    return data


def ref(path,limit=1048576):
    path=Path(path).resolve(strict=True);data=raw(path,limit)
    return {'path':str(path),'bytes':len(data),'sha256':sha(data)}


def checked(item,limit=262144):
    require(isinstance(item,dict) and set(item)=={'path','bytes','sha256'}
        and type(item['path']) is str and Path(item['path']).is_absolute()
        and type(item['bytes']) is int and 0<item['bytes']<=limit,'bounded exact reference required')
    data=raw(item['path'],limit)
    require((len(data),sha(data))==(item['bytes'],item['sha256']),'actual metadata pin changed')
    value=json.loads(data);require(isinstance(value,dict),'JSON object required')
    return value


def _load(path,digest,name):
    data=raw(path);require(sha(data)==digest,'actual frozen consumer source differs')
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def _stamp(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(result.tzinfo is not None and result.utcoffset().total_seconds()==0,'explicit UTC required')
    return result


def _future_ref(path,value):
    data=enc(value)
    return {'path':str(path),'bytes':len(data),'sha256':sha(data)},data


def _base(runtime):
    """Read only actual small frozen inputs; never open Driver/SAVE bodies."""
    freeze_ref=ref(runtime/'ROOT-FINAL-SDK-FREEZE-P37C23-A03.json',524288)
    require((freeze_ref['bytes'],freeze_ref['sha256'])==FINAL_PIN,'actual deployed A03 final freeze required')
    freeze=checked(freeze_ref,524288)
    policy_ref=freeze['canonical_preload_policy'];policy=checked(policy_ref,32768)
    require((policy_ref['bytes'],policy_ref['sha256'])==POLICY_PIN and policy.get('enable_driver_state_wal_v1') is True,
        'actual A03 full44/six WAL policy required')
    entries={Path(path).resolve(strict=True):digest for path,digest in policy['entry_source_pins']}
    require(len(entries)==44 and len(policy['canonical_entry_source_pins'])==6,'actual complete44/six closure required')
    for path,digest in entries.items():require(sha(raw(path))==digest,'current frozen complete source closure differs')
    helper_path=runtime/'root_c23_a03_source_abort_checkpoint_inputs.py'
    helper=_load(helper_path,entries[helper_path],'_a03_cold_metadata_finite')
    coldpath=runtime/'root_p37c23_cold_resume.py'
    cold=_load(coldpath,entries[coldpath],'_a03_cold_metadata_actual_consumer')
    anchor_ref=freeze['source25_canonical_anchor'];anchor=helper.validate_business_anchor(checked(anchor_ref,65536))
    checked(anchor['source_plan'],131072)
    # This verifies all canonical rows against the actual deployed final freeze.
    helper.validate_frozen_business({'business_anchor':anchor_ref,'business_source_commit':anchor['commit']},freeze,checked)
    pre_ref=ref(runtime/'ROOT-C23-COLD-PRELAUNCH.json',16384)
    require((pre_ref['bytes'],pre_ref['sha256'])==COLD_PRE_PIN,'actual original SAVE10480 cold prelaunch required')
    pre=checked(pre_ref,16384);close=checked(pre['final_driver_close'],16384)
    # Exact helper retains C20 normal pair, abnormal oldGame/C22, and F99.
    abort=helper.validate_source_abort_closure(close,checked)
    original=abort['sources']['closed_state'];save=abort['sources']['SAVE10480_response']
    governance=ref(Path(original['path']).parent/'ROOT-GOVERNANCE-RESULT-STATE.json',16384)
    semantic=ref(runtime/'p37-responses/10479-1-result.json',262144)
    classifier_ref=ref(runtime/'ROOT-P37C20-CLASSIFIER-PIN.json',16384)
    classifier=checked(classifier_ref,16384)
    require(sha(raw(classifier['source'],262144))==classifier['sha256'],'actual retained installed classifier changed')
    seed=checked(original,16384)
    basis={'schema':'xar.c23.normal-checkpoint-cold-queue/v1','machine_id':MACHINE,
        'seed':original,'original_state':original,'governance':governance,'save_response':save,
        'saved_semantic_response':semantic,'cold_prelaunch':pre_ref,
        'old_closed':close['sdk_closed'],'old_sdk_closed':close['sdk_closed'],'old_sdk_pair':close['old_sdk_pair'],
        'old_sdk_closure_kind':close['old_sdk_closure_kind'],'old_Game':close['old_Game'],
        'source_abort_index':close['source_abort_index'],'sdk_freeze':freeze_ref,'business_anchor':anchor_ref,
        'business_source_commit':anchor['commit'],'save_sequence':10480,'next_sequence':10481,
        'current_map_admission':str(runtime/'ROOT-CAMPAIGN-MAP-ADMITTED-C23.json'),
        'classifier_pin':classifier_ref,'cold_resume_helper':ref(coldpath),
        'control_timing_not_enabled':True}
    for key,name in [('queue_source','root_p37c23_sdk_queue.py'),('entry_source','root_p37c23_mcp_entry.py'),
            ('native_binding_source','root_native_build_binding_p37c23.py')]:
        basis[key]=ref(runtime/name)
    helper.validate_saved_seed(basis,seed,checked(original),checked(save),checked(semantic),checked(governance),checked=checked)
    return basis,freeze,policy,entries,helper,cold


def saved_basis(*,runtime_root=DEFAULT_RUNTIME):
    """Available before first-frame receipt; not an admission or new file."""
    runtime=Path(runtime_root).resolve(strict=True)
    old=list(sys.path);sys.path.insert(0,str(runtime))
    try:basis,*_= _base(runtime)
    finally:sys.path[:]=old
    return basis,{'machine_id':MACHINE,'status':'ACTUAL_SAVED_BASIS_VALIDATED_RAM_ONLY',
        'completed_cycles':4753,'saved_date_raw':53274624,'saved_day_credit':5429,'next_sequence':10481,
        'C20_actual_normal_dual_zero_retained':True,'C22_abnormal_failure_preserved':True,
        'Driver_SAVE_body_reads':0,'metadata_outputs_written':0,'SDK_started':False}


def compose(inputs):
    """Return four new metadata bytes and an exact quote; no runtime mutation."""
    require(isinstance(inputs,dict) and inputs.get('schema')=='xar.C23-A03-cold-owner-metadata-input/v1'
        and inputs.get('machine_id')==MACHINE and inputs.get('execution_owner')=='Root'
        and inputs.get('root_direct_execution_release') is True,'explicit actual Root metadata input required')
    at=inputs['observed_at_utc'];require(-10<=(datetime.now(timezone.utc)-_stamp(at)).total_seconds()<=600,'fresh explicit UTC input required')
    runtime=Path(inputs.get('runtime_root',DEFAULT_RUNTIME)).resolve(strict=True)
    require(not any((runtime/name).exists() for name in (*OUTPUT_NAMES,*STOPS)),'new metadata or old stop/exit marker exists')
    require(not (runtime/'p37-queue').exists(),'new SDK queue must remain absent')
    require(checked(ref(runtime/'NEXT-SEQUENCE-P37.json',16384),16384).get('next_sequence')==10481,'monotonic NEXT10481 required')
    full=checked(inputs['full_storage_ref'],32768);live=checked(inputs['live_storage_ref'],32768)
    require(inputs['full_storage_ref']['sha256']==inputs['live_storage_ref']['sha256']==FULL_SHA
        and full==live and full.get('machine_id')==MACHINE and full.get('status')=='ADMITTED'
        and datetime.now(timezone.utc)<_stamp(full['review_at_utc']),'actual current single full332f required')
    require(Path(inputs['live_storage_ref']['path']).resolve()==runtime/'STORAGE-ADMISSION.json','actual shared full location differs')
    require(any(runtime==Path(root).resolve() or runtime.is_relative_to(Path(root).resolve())
        for root in full['approved_output_roots']),'runtime not in canonical approved roots')
    actual_ref=inputs['actual_game'];launch=checked(actual_ref,32768)
    require(Path(actual_ref['path']).resolve()==runtime/'ROOT-ACTUAL-GAME-LAUNCH-C23.json'
        and launch.get('machine_id')==MACHINE and launch.get('old_save_loaded') is True
        and launch.get('load_save_name')=='xar_checkpoint' and launch.get('nonwar_only') is False
        and type(launch.get('pid')) is int and type(launch.get('creation_filetime')) is int,'actual new cold full-enabled Game required')
    old=list(sys.path);sys.path.insert(0,str(runtime))
    try:
        basis,freeze,policy,entries,helper,cold=_base(runtime)
        require(inputs['sdk_freeze']==basis['sdk_freeze'] and inputs['business_anchor']==basis['business_anchor'],
            'caller must bind actual deployed Source25 A03 freeze and complete-row anchor')
        absence=checked(inputs['mod_absence'],32768)
        require(absence.get('machine_id')==MACHINE and absence.get('game_pid')==launch['pid']
            and absence.get('game_creation_filetime')==launch['creation_filetime'],'current Game mod-absence identity required')
        refs=inputs['recording'];require(set(refs)=={'request','job','started','first_frame_admission','publisher_started'},
            'five exact new recording references required')
        request=checked(refs['request'],16384);job=checked(refs['job'],65536)
        started=checked(refs['started'],32768);first=checked(refs['first_frame_admission'],32768)
        checked(refs['publisher_started'],65536)
        require(first.get('reviewer')=='/root' and first.get('status')=='GREEN',
            'Root actual first-frame admission required before owner gate')
        require(job.get('capture_mode')=='game_decision_text' and job.get('continuous') is True
            and all(job.get(key) is None for key in ('duration_seconds','max_output_bytes','deadline_utc')),
            'current continuous game plus decision-text recording required')
        require(job.get('storage',{}).get('admission_sha256')==FULL_SHA,
            'recording job must bind same actual canonical full')
        binding={'schema':'xar.C23-actual-cold-recording-binding/v1','machine_id':MACHINE,
            'observed_at_utc':at,'status':'ACTUAL_NEW_RECORDING_READY','Game_pid':launch['pid'],
            'Game_creation_filetime':launch['creation_filetime'],'session_id':request['session_id'],**refs}
        binding_ref,binding_raw=_future_ref(runtime/BINDING_NAME,binding)
        admission={**basis,'observed_at_utc':at,
            'new_Game':{key:launch[key] for key in ('pid','creation_filetime','creation_date')},
            'publisher_started':refs['publisher_started'],'mod_absence':inputs['mod_absence'],
            'recording_binding':binding_ref,'full_storage_view':inputs['full_storage_ref'],
            'storage_admission':inputs['live_storage_ref'],'review_at_utc':full['review_at_utc'],
            'source_fixture':False,'new_ordinary_cycle_credit':0,'new_game_day_credit':0}
        def overlay(item,limit=262144):
            if item==binding_ref:return binding
            return checked(item,limit)
        recording=helper.current_recording_inputs_v1(admission,overlay)
        seed=checked(admission['seed'])
        helper.validate_saved_seed(admission,seed,checked(admission['original_state']),checked(admission['save_response']),
            checked(admission['saved_semantic_response']),checked(admission['governance']),checked=overlay)
        # Execute only the original pure consumer preflight-input validator;
        # live verify_segment and actual SEM/CAP remain with the created Queue.
        cold.cold_inputs(admission)
        helper.validate_frozen_business(admission,freeze,overlay)
    finally:sys.path[:]=old
    admission_ref,admission_raw=_future_ref(runtime/ADMISSION_NAME,admission)
    sourcepins={str(path.relative_to(runtime)):digest for path,digest in entries.items() if path.is_relative_to(runtime)}
    for name in FEEDER_NAMES:sourcepins[name]=ref(runtime/name)['sha256']
    sourcepins['root_checkpoint_cadence.py']=ref(runtime/'root_checkpoint_cadence.py')['sha256']
    pins={'schema':'xar.C23-owner-input-pins/v1','machine_id':MACHINE,'observed_at_utc':at,
        'sources':sourcepins,'sdk_freeze':basis['sdk_freeze'],'admission':admission_ref,
        'first_frame_admission':refs['first_frame_admission'],'full_storage_view':inputs['full_storage_ref'],
        'source_guards_unchanged':True,'actual_constructor_or_Game_RPC_calls':0}
    pins_ref,pins_raw=_future_ref(runtime/OWNER_PINS_NAME,pins)
    gate={'schema':'xar.c23.sdkowner-create-admission/v1','machine_id':MACHINE,'observed_at_utc':at,
        'execution_owner':'Root','root_direct_execution_release':True,'actual_game':actual_ref,
        'first_frame_admission':refs['first_frame_admission'],'owner_input_pins':pins_ref,
        'sdk_freeze':basis['sdk_freeze'],'business_anchor':basis['business_anchor'],
        'full_storage_view':inputs['full_storage_ref'],'review_at_utc':full['review_at_utc'],
        'single_creator':'existing canonical same-holder supervisor','SDK_not_started_by_builder':True}
    gate_ref,gate_raw=_future_ref(runtime/GATE_NAME,gate)
    outputs={runtime/BINDING_NAME:binding_raw,runtime/ADMISSION_NAME:admission_raw,
        runtime/OWNER_PINS_NAME:pins_raw,runtime/GATE_NAME:gate_raw}
    require(all(len(data)<=65536 for data in outputs.values()),'bounded exact metadata outputs required')
    allocated=sum(((len(data)+4095)//4096)*4096 for data in outputs.values())
    quote={'schema':'xar.C23-A03-cold-owner-metadata-quote/v1','machine_id':MACHINE,'observed_at_utc':at,
        'status':'RAM_READY_NOT_WRITTEN_NO_OWNER_GATE_PUBLISHED','input_sha256':sha(enc(inputs)),
        'source':ref(Path(__file__)),'outputs':[_future_ref(path,json.loads(data))[0] for path,data in outputs.items()],
        'logical_bytes':sum(map(len,outputs.values())),'allocation_upper':allocated,
        'metadata_write_peak_upper':allocated+16384,'publish_order':list(OUTPUT_NAMES),'gate_must_be_last':True,
        'new_Game':admission['new_Game'],'session_id':request['session_id'],'next_sequence':10481,
        'completed_cycles':4753,'saved_game_days':5429,'saved_date_raw':53274624,'checkpoint_saved_count':74,
        'full_storage_view':inputs['full_storage_ref'],'review_at_utc':full['review_at_utc'],
        'first_frame_admission':refs['first_frame_admission'],'recording_binding':binding_ref,
        'C20_actual_normal_dual_zero_retained':True,'C22_abnormal_failure_preserved':True,
        'actual_SEM_CAP_restore':'NOTRUN','first_FULL':'only timed finite feeder after actual cold SEM/CAP',
        'live_verify_segment':'Queue remains responsible','Driver_SAVE_body_reads':0,'Task_SDK_MCP_calls':0}
    return outputs,quote


def main(argv=None):
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('command',choices=('basis','quote'))
    parser.add_argument('--inputs',type=Path);parser.add_argument('--inputs-sha');args=parser.parse_args(argv)
    if args.command=='basis':result=saved_basis()[1]
    else:
        require(args.inputs is not None and args.inputs_sha is not None,'explicit exact input file required')
        item=ref(args.inputs,65536);require(item['sha256']==args.inputs_sha,'CLI input SHA differs')
        result=compose(checked(item,65536))[1]
    print(json.dumps(result,ensure_ascii=False));return 0


if __name__=='__main__':raise SystemExit(main())

