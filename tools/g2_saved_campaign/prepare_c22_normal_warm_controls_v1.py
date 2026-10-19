"""Source22/C22 normal warm controls. RAM bytes only; no launch or export."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
MACHINE='xenoamess-full-tower-eb9d2c1186'
T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
N=T.parent.parent
C21=REPO/'tools/g2_saved_campaign/prepare_c21_normal_warm_controls_v1.py'
C21_SHA='8f2adeb492396af1c62f990b0cc958b3e0beb4ac972a41fac87320bb02fdfe48'
PORT=REPO/'_runtime/compose_C18_warm_controls93.py'
PORT_SHA='2bbdee3dc30521aca2b4f774d75b8f1df9e73b5816be3d3d6d880dac20e63fa6'
ANCHOR=REPO/'_runtime/source22-integration16/SOURCE22-CANONICAL-ANCHOR.json'
ANCHOR_SHA='dc5dc51909fa5f93635d8d63cbea5f7b71c5a9e38af6bcae51c55eb523a997c9'
PLAN=REPO/'docs/ck3-native-ai/evidence/source22-wal-clock-diagnostic-source-plan-2026-10-20.json'
PLAN_SHA='48ecb6b2e5c8162d965efd30ed925838b92b2fb519870ceba6131d265905ac89'
COMMIT='0722bef48d412ed5e49d0109177493846d988745'
ROWS_SHA='7290b3370b64335b27ff375713dd92de331b0ca114bf99440014d40404593a85'
OLD_RECORD='2b8912a6-757d-46a4-a8ae-b7702a730a90'
PAIRS=(('P37C21','P37C22'),('p37c21','p37c22'),('-C21','-C22'),
 ('SDKC21','SDKC22'),('p51_resident_successor_adoption_c21','p51_resident_successor_adoption_c22'))

# Embedded in the factory so the owner can use exactly the same bounded input
# reader before spawning Queue. No new runtime helper or provider is introduced.
RECORD_HELPER='''def current_recording_inputs_v1(admission):
    from uuid import UUID
    binding=checked(admission['recording_binding'],65536);b=admission['boundary']
    require(binding.get('schema')=='xar.C22-actual-recording-binding/v1'
        and binding.get('machine_id')==MACHINE and binding.get('status')=='ACTUAL_NEW_RECORDING_READY'
        and (b['Game_pid'],b['Game_creation_filetime'])==(30852,134368995759027619)
        and binding.get('Game_pid')==b['Game_pid']
        and binding.get('Game_creation_filetime')==b['Game_creation_filetime'],
        'explicit actual new recording and same Game required')
    requested=checked(binding['request'],16384);job=checked(binding['job'],65536)
    started=checked(binding['started'],32768);first=checked(binding['first_frame_admission'],32768)
    checked(binding['publisher_started'],65536)
    previous=checked(binding['previous_capture_closed'],65536)
    sid=str(UUID(binding['session_id']))
    root=Path(requested['receipt_root']).resolve();first_path=Path(binding['first_frame_admission']['path']).resolve()
    session_root=Path(admission['queue_source']['path']).resolve().parent
    require(previous.get('schema')=='xar.ck3.capture-closed-before-media-hash/v1'
        and previous.get('session_id')=='2b8912a6-757d-46a4-a8ae-b7702a730a90'
        and previous.get('game_pid')==b['Game_pid']
        and previous.get('game_creation_filetime')==b['Game_creation_filetime']
        and previous.get('inputs_unbound') is True
        and (previous.get('engine_close') or {}).get('actual_exit_code')==0
        and (previous.get('engine_close') or {}).get('normal_exit_proven') is True
        and (previous.get('engine_close') or {}).get('forced_process_calls')==0,
        'old recording normal capture closure required; no old firstgate reuse')
    require(sid==binding['session_id'] and sid!=previous['session_id']
        and root.is_relative_to(session_root/'recordings') and root.name==sid
        and all(x.get('session_id')==sid for x in (requested,job))
        and Path(job['receipt_root']).resolve()==root
        and Path(binding['job']['path']).resolve()==root/'job.json'
        and Path(binding['started']['path']).resolve()==root/'started.json'
        and type(requested.get('worker_pid')) is int and requested['worker_pid']>0
        and type(requested.get('worker_creation_filetime')) is int and requested['worker_creation_filetime']>0,
        'new UUID/request/worker/job source differs')
    require(job.get('pid')==b['Game_pid'] and job.get('game_creation_filetime')==b['Game_creation_filetime']
        and started.get('game_pid')==b['Game_pid'] and started.get('game_creation_filetime')==b['Game_creation_filetime']
        and started.get('state')=='recording' and first.get('status')=='GREEN'
        and first.get('machine_id')==MACHINE and first.get('game_pid')==b['Game_pid']
        and first.get('game_creation_filetime')==b['Game_creation_filetime']
        and first.get('recorder_session_id')==sid and Path(first['recording_job_root']).resolve()==root
        and first_path.is_relative_to(session_root)
        and first_path!=session_root/'ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json'
        and first.get('publisher_started')==job.get('decision_text_publisher_receipt')==binding['publisher_started'],
        'new recording/firstgate/same publisher identity differs')
    return {'binding':binding,'requested':requested,'job':job,'started':started,'first':first,
        'root':root,'first_path':first_path}


'''


def require(ok,reason):
    if not ok:raise ValueError('C22 controls denied: '+reason)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def checked_bytes(path,size,digest):
    raw=path.read_bytes()
    require(len(raw)==size and sha(raw)==digest,'frozen input differs: '+str(path))
    return raw


def checked_document(ref,limit=262144):
    require(isinstance(ref,dict) and type(ref.get('path')) is str
        and Path(ref['path']).is_absolute() and type(ref.get('bytes')) is int
        and 0<ref['bytes']<=limit,'bounded pinned metadata reference required')
    path=Path(ref['path'])
    with path.open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)==ref['bytes'] and sha(raw)==ref.get('sha256'),'actual recording input pin differs')
    value=json.loads(raw);require(isinstance(value,dict),'metadata object required')
    return value


def business_binding_v1():
    anchor=json.loads(checked_bytes(ANCHOR,4874,ANCHOR_SHA))
    plan=json.loads(checked_bytes(PLAN,11133,PLAN_SHA))
    require(anchor.get('schema')=='xar.source22.canonical-git-anchor/v1'
        and anchor.get('machine_id')==plan.get('machine_id')==MACHINE
        and anchor.get('status')=='CANONICAL_REF_CREATED_NOT_DEPLOYED'
        and anchor.get('commit')==COMMIT and anchor.get('parent')=='f19864de1cc073eed62617faad2307c57ad45a97'
        and anchor.get('tree')=='fd5e2d942f214effc56dd67aa30f4a6d4d011763'
        and anchor.get('ref')=='refs/heads/campaign/robert-v20261019-c22-wal-clock-diag-warm-01'
        and anchor.get('source_file_count')==1449 and anchor.get('source_bytes')==59095358
        and anchor.get('complete_rows_JSON')=={'bytes':372481,'sha256':ROWS_SHA}
        and anchor.get('Source21_anchor_created') is False and anchor.get('Native30_bound') is False,
        'actual Source22 complete Git anchor differs')
    require(anchor.get('source_plan')=={'path':str(PLAN),'bytes':11133,'sha256':PLAN_SHA},
        'actual Source22 plan pairing differs')
    return {'anchor':{'path':str(ANCHOR),'bytes':4874,'sha256':ANCHOR_SHA},
        'plan':{'path':str(PLAN),'bytes':11133,'sha256':PLAN_SHA},'commit':COMMIT,
        'file_count':1449,'source_bytes':59095358,'rows_sha256':ROWS_SHA,
        'Native30_bound':False,'clock_root_cause':'UNKNOWN; diagnostic only',
        'source_root':str(N/'sdk-v20261019-candidate/src18'),
        'reference_source_root':str(N/'sdk-v20261019-candidate/reference-c22/src'),
        'output_root':str(N/'p51-fresh1066-v20261019-prepare01/c22-source22-warm99/immutable-source-export')}


def _replace_once(text,old,new):
    require(text.count(old)==1,'one exact recording source seam required')
    return text.replace(old,new,1)


def _source_graph_v1():
    business=business_binding_v1()
    checked_bytes(C21,8570,C21_SHA)
    spec=importlib.util.spec_from_file_location('_exact_C21_control_source_predecessor',C21)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    before,old_report=old._source_graph_v1()
    raw=checked_bytes(PORT,6120,PORT_SHA)
    text=raw.decode().replace('P37C18oldReadyQueue','P37C22oldReadyQueue').replace('P37C17oldReadyQueue','P37C21oldReadyQueue')
    scope={'__name__':'C22_namespace_port_only','__file__':str(PORT)}
    exec(compile(text,str(PORT),'exec'),scope);scope['PAIRS']=PAIRS
    graph={scope['mapped'](name):scope['port'](data.decode()).encode() for name,data in before.items()}
    # Namespace inverse is verified by the frozen port before these explicit
    # recording-only changes. WAL forwarding remains byte-identical.
    queue=graph['root_p37c22_sdk_queue.py'].decode()
    require(queue.count(old.WAL_HUNK)==1,'original strict optional WAL hunk changed')
    owner=graph['launch_sdk_p37c22_owner.py'].decode()
    owner=_replace_once(owner,"    requested=read(N/'ROOT-CURRENT-OBS-RECORDING-REQUESTED-C16.json')\n",
        "    from root_p37c22_warm_resume import current_recording_inputs_v1\n"
        "    recording=current_recording_inputs_v1(read(N/'ROOT-P37C22-SOURCE-RESUME-ADMISSION.json'))\n"
        "    requested=recording['requested']\n")
    owner=_replace_once(owner,"'--first-frame-admission',str(N/'ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json'),",
        "'--first-frame-admission',str(recording['first_path']),")
    graph['launch_sdk_p37c22_owner.py']=owner.encode()
    factory=graph['root_p37c22_warm_resume.py'].decode()
    factory=_replace_once(factory,'def make_normal_source_warm_queue_v1(base,env,*,admission_path):',
        RECORD_HELPER+'def make_normal_source_warm_queue_v1(base,env,*,admission_path):')
    factory=_replace_once(factory,"            api=load_api(env['N'])\n",
        "            recording=current_recording_inputs_v1(admission)\n            api=load_api(env['N'])\n")
    factory=_replace_once(factory,"""            require(started_reference(env['N'],api)==admission['retained_C16_publisher_started']
                and self.record_job.resolve()==Path(admission['retained_recording_job']).resolve()
                and self.args.first_frame_admission.resolve()==Path(admission['retained_first_frame_admission']).resolve()
""", """            require(started_reference(env['N'],api)==recording['binding']['publisher_started']
                and self.record_job.resolve()==recording['root']
                and self.args.first_frame_admission.resolve()==recording['first_path']
""")
    factory=_replace_once(factory,"'retained C16 publisher/recording and exact Game required'",
        "'actual current recording/publisher and exact retained Game required'")
    factory=_replace_once(factory,
        "and isinstance(admission['business_source_commit'],str) and len(admission['business_source_commit'])==40",
        "and admission['business_source_commit']=='0722bef48d412ed5e49d0109177493846d988745'\n"
        "                and freeze['source_file_count']==1449 and len(freeze['files'])==1449\n"
        "                and freeze['source_bytes']==59095358")
    factory=_replace_once(factory,"'old_result_replayed':False,'retained_C16_publisher_started':resume['admission']['retained_C16_publisher_started']",
        "'old_result_replayed':False,'publisher_started':current_recording_inputs_v1(resume['admission'])['binding']['publisher_started'],"
        "'recording_binding':resume['admission']['recording_binding']")
    graph['root_p37c22_warm_resume.py']=factory.encode()
    for name,data in graph.items():compile(data,name,'exec')
    require(len(graph)==7 and graph['root_p37c22_sdk_queue.py'].decode().count(old.WAL_HUNK)==1,
        'seven controls or WAL seam differs')
    return graph,{'business':business,'predecessor_control_producer':{'path':str(C21),'bytes':8570,'sha256':C21_SHA},
        'old_45_protected_constants_verified_before_explicit_recording_hunks':old_report['protected_constants'],
        'explicit_recording_exceptions':['old CURRENT-REQUESTED C16 literal in owner','old C16 firstgate literal in owner',
            'retained_C16_publisher_started metadata key/reason replaced by explicit current-recording binding'],
        'WAL_hunk_preserved_bytes':len(old.WAL_HUNK.encode()),'classifier_sha256':old.CLASSIFIER_SHA,
        'physical_Game_API_score_publisher_source_generation':'C16','recording_generation':'then actual new UUID and Root firstgate',
        'runtime_admitted':False,'outputs_materialized':False}


def _recording_reader_v1(factory_source,read_document):
    scope={'checked':read_document,'require':require,'MACHINE':MACHINE,'Path':Path}
    node=next(n for n in ast.parse(factory_source).body if isinstance(n,ast.FunctionDef)
        and n.name=='current_recording_inputs_v1')
    exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-C22-recording-inputs','exec'),scope)
    return scope['current_recording_inputs_v1']


def compose(*, recording_binding_ref, boundary):
    """Future public entry: actual new recording refs mandatory, RAM bytes only."""
    require(isinstance(recording_binding_ref,dict) and isinstance(boundary,dict),
        'unknown new recording refs or clean boundary cannot produce a runtime candidate')
    graph,report=_source_graph_v1()
    reader=_recording_reader_v1(graph['root_p37c22_warm_resume.py'],checked_document)
    observed=reader({'recording_binding':recording_binding_ref,'boundary':boundary,
        'queue_source':{'path':str(T/'root_p37c22_sdk_queue.py')}})
    return graph,{**report,'actual_recording_binding':recording_binding_ref,
        'actual_new_recording_session':observed['binding']['session_id'],
        'actual_firstgate':observed['binding']['first_frame_admission'],
        'actual_publisher_started':observed['binding']['publisher_started'],
        'separate_clean_postclose_source_freeze_Task_and_runtime_admissions_required':True}
