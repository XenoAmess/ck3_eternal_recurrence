"""Finite Source25/A03 controls; no writes, process creation, or runtime grant."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

OWN=Path(__file__).resolve().parent
MACHINE='xenoamess-full-tower-eb9d2c1186'
PARENT='6b55531b1d3a44ee73ab13ea40132556030f682e'
OLD_PRODUCER=('prepare_c23_full_enabled_cold_controls_v1.py',37154,'b63eacea6eae778678e7a05f755e033bb426e67da8c0cebc5bb465f3199051d9')
OLD_HELPER='root_c23_source_abort_checkpoint_inputs.py'
HELPER='root_c23_a03_source_abort_checkpoint_inputs.py'
SIX={'root_native30_supervisor_c23.py','root_checkpoint_bootstrap_c23.py',
 'launch_sdk_p37c23_owner.py','root_p37c23_sdk_queue.py','root_p37c23_mcp_entry.py','root_c23_canonical_outer.py'}
ATTEMPT_NAMES=('ROOT-SUPERVISOR-ADMITTED-C23','ROOT-FRESH-PROFILE-PREPARED-C23',
 'ROOT-NATIVE30-GAME-ENVIRONMENT-BOUND-C23','ROOT-SCREEN-KEEPER-C23','ROOT-FRESH-SUPERVISOR-CLOSED-C23')
METADATA=('ROOT-CLEAN-SOURCE-FROZEN-C23.json','ROOT-LAUNCH-CONFIG-C23.json',
 'ROOT-NATIVE30-SDK-BINDING-C23.json','ROOT-PROMO-KEEPER-SOURCE-READY-C23.json','ROOT-OBS-PROFILE-C23.json',
 'ROOT-NATIVE30-NATIVE-PIN-C23.json')
A01=(1975,'4351bc77b2c122722d6b135a4918a6922152245e5578b9400bd8857619545170')
A02={
 'supervisor_closed':(1053,'3e94fe691460b469a1b000527be74dd255a4fd894e4b136744b8723631a8cb77'),
 'Task_closed':(745,'b36b383f68c81c6e59dcafdb8728dd122a1fa70bb4c5bf5af97b369773f15cd4'),
 'Task_unregistered':(2278,'3e0cd654db523b6f423b7ea47f53f7ca7dc1706f591d4f81f4b0a1db6fc78ef6'),
 'kernel':(708,'5d9f10fc0cd3036190a194a4baa64c745a8db59c63a037d5cbbdc83b74585125')}
STOP_NAMES=('STOP-OWNED-GAME-C23','EXIT-SDK-P37C23','ROOT-SDK-EXIT-REQUESTED-C23.json',
 'REQUEST-ADMISSION-CLOSED-C23','ROOT-GAME-CLOSE-REQUEST-C23.json')


def require(ok,why):
    if not ok:raise ValueError('C23 A03 controls denied: '+why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def predecessor():
    name,size,digest=OLD_PRODUCER;path=OWN/name;raw=path.read_bytes()
    require((len(raw),sha(raw))==(size,digest),'exact A02 producer required')
    if str(OWN) not in sys.path:sys.path.insert(0,str(OWN))
    spec=importlib.util.spec_from_file_location('_a03_exact_a02_producer',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def swap(raw,old,new):
    require(type(raw) is bytes and raw.count(old)==1,'one exact finite seam required')
    result=raw.replace(old,new,1)
    require(result.replace(new,old,1)==raw,'finite seam inverse differs')
    return result


def helper_source():
    p=predecessor();raw=(OWN/'c23_source_abort_checkpoint_inputs_v1.py').read_bytes()
    require(sha(raw)==p.HELPER_SHA,'exact historical finite helper required')
    old=raw
    raw=swap(raw,b'xar.source24.canonical-git-anchor/v1',b'xar.source25.canonical-git-anchor/v1')
    raw=swap(raw,b'330d6e67c99eb22a60919b2bf7666c1ed0ca1b71',PARENT.encode())
    raw=raw.replace(b'Source24',b'Source25').replace(b'Source23 parent',b'Source24 parent')
    reverse=raw.replace(b'Source24 parent',b'Source23 parent').replace(b'Source25',b'Source24')
    reverse=reverse.replace(PARENT.encode(),b'330d6e67c99eb22a60919b2bf7666c1ed0ca1b71')
    reverse=reverse.replace(b'xar.source25.canonical-git-anchor/v1',b'xar.source24.canonical-git-anchor/v1')
    require(reverse==old,'new finite helper must retain exact frontier and recording algorithms')
    compile(raw,HELPER,'exec');return raw


def business_binding(ref):
    p=predecessor();scope={}
    exec(compile(helper_source(),HELPER,'exec'),scope)
    anchor=scope['validate_business_anchor'](p.read_document(ref,65536))
    p.read_document(anchor['source_plan'],131072)
    return {'anchor':ref,'commit':anchor['commit'],'tree':anchor['tree'],'parent':anchor['parent'],
        'complete_file_count':anchor['source_file_count'],'complete_source_bytes':anchor['source_bytes'],
        'rows':anchor['complete_rows_JSON'],'actual_filesystem_epoch_authority':False,'plan':anchor['source_plan']}


def validate_attempt(args,config,checked):
    """Exact two failed predecessors. No absent-success-receipt inference."""
    value=config.get('cold_attempt') or {}
    require(args.attempt=='a03' and value.get('attempt_id')=='a03'
        and value.get('execution_owner')=='Root' and value.get('root_direct_execution_release') is True,
        'explicit Root A03 release required')
    attempt=str(args.attempt_nonce);task=str(args.task_nonce)
    require(re.fullmatch('[0-9a-f]{32}',attempt) is not None
        and re.fullmatch('[0-9a-f]{32}',task) is not None
        and value.get('nonce')==attempt and value.get('task_nonce')==task and attempt!=task,
        'independent exact A03 attempt and Task nonce required')
    def pinned(ref,pin):
        require(isinstance(ref,dict) and (ref.get('bytes'),ref.get('sha256'))==pin,
            'exact failed predecessor pin required')
        result=checked(ref,16384)
        require(result.get('machine_id')==MACHINE,'failed predecessor machine differs')
        return result
    failure=pinned(value['prior_failure_a01'],A01)
    require(failure.get('status')=='C23_FIRST_SUPERVISOR_LAUNCH_FAILED_ORIGINAL_CLEANUP_CLOSED'
        and failure.get('new_App_created') is False
        and failure.get('SAVE10480_unchanged_by_Game_execution') is True,'a01 failure scope differs')
    sources=failure['source_refs']
    a01_closed=checked(sources['supervisor_closed'],16384)
    a01_task=checked(sources['Task_closed'],16384)
    a01_removed=checked(sources['Task_unregistered'],16384)
    require((a01_closed.get('failure') or {}).get('message')==
        'CK3 launch contract failed safely: frozen entry source pins required'
        and (a01_closed.get('keeper') or {}).get('thread_exited') is True
        and a01_task.get('child_exit_code')==a01_task.get('bootstrap_exit_code')==1
        and a01_task.get('job_active_after_stage')==0 and a01_task.get('forced_remaining_cleanup') is False
        and (a01_removed.get('actual') or {}).get('absent_after') is True,'a01 Task closure differs')
    refs=value['prior_failure_a02']
    require(isinstance(refs,dict) and set(refs)==set(A02),'four exact a02 failure sources required')
    docs={key:pinned(refs[key],pin) for key,pin in A02.items()}
    closed,prior_task,removed,kernel=(docs[k] for k in A02)
    require(closed.get('attempt_id')=='a02' and closed.get('cleanup_classification')=='LAUNCH_FAILED_HANDLE_NOT_RETURNED'
        and (closed.get('failure') or {}).get('message')==
        'CK3 launch contract failed safely: canonical preload unavailable: OSError:[WinError 299] EnumProcessModulesEx'
        and (closed.get('keeper') or {}).get('thread_exited') is True
        and prior_task.get('child_exit_code')==prior_task.get('bootstrap_exit_code')==1
        and prior_task.get('job_active_after_stage')==0 and prior_task.get('forced_remaining_cleanup') is False
        and (removed.get('unregister') or {}).get('actual',{}).get('absent_after') is True
        and removed.get('Run_replayed') is False and kernel.get('no_live_CK3_in_named_inventory') is True
        and kernel.get('normal_Game_exit_zero_claimed') is False,'a02 actual failed closure differs')
    old={closed.get('attempt_nonce'),prior_task.get('nonce'),a01_task.get('nonce')}
    require(attempt not in old and task not in old,'A03 cannot reuse failed attempt or Task nonce')
    return value


def known_preload_phase(canonical):
    """Project already-read M7 memory only; unknown stays explicit."""
    phase=getattr(getattr(getattr(canonical,'factory',None),'facade',None),'_preload_mapping_phase_v1',None)
    result={'schema':'xar.C23-A03-known-preload-phase/v1',
        'source':'canonical.factory.facade._preload_mapping_phase_v1','stage':'unknown','status':'unknown',
        'before':{'pid':'unknown','creation_filetime':'unknown'},
        'after':{'pid':'unknown','creation_filetime':'unknown'},'additional_OS_reads':False}
    if not isinstance(phase,dict):return result
    for key in ('stage','status','error'):
        value=phase.get(key)
        if isinstance(value,str):result[key]=value[:256]
    for key in ('before','after'):
        row=phase.get(key)
        if isinstance(row,dict):
            for field in ('pid','creation_filetime'):
                value=row.get(field)
                if type(value) is int and value>0:result[key][field]=value
    for key in ('images','last_walk_regions'):
        value=phase.get(key)
        if type(value) is int and value>=0:result[key]=value
    return result


def runtime_attempt_helpers():
    """Embed the exact reviewed pure functions with the original bounded reader."""
    raw=Path(__file__).read_bytes();tree=ast.parse(raw)
    names={'require','validate_attempt','known_preload_phase'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    require({n.name for n in nodes}==names,'exact A03 runtime helper definitions required')
    source='\nMACHINE='+repr(MACHINE)+'\nA01='+repr(A01)+'\nA02='+repr(A02)+'\n'
    source+='\n\n'.join(ast.get_source_segment(raw.decode(),node) for node in nodes)
    source+='''
def _a03_checked(ref,limit=16384):
    if (not isinstance(ref,dict) or type(ref.get('path')) is not str
            or not Path(ref['path']).is_absolute() or type(ref.get('bytes')) is not int
            or not 0<ref['bytes']<=limit):
        raise ValueError('bounded exact A03 predecessor JSON required')
    with Path(ref['path']).open('rb') as stream:raw=stream.read(limit+1)
    if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref.get('sha256'):
        raise ValueError('A03 predecessor source differs')
    value=json.loads(raw)
    if not isinstance(value,dict):raise ValueError('A03 predecessor object required')
    return value

def _validate_a03_attempt(args,config):
    return validate_attempt(args,config,_a03_checked)
'''
    return source.encode()


def _compose_source_graph(*,full_timing=True):
    p=predecessor();graph,report=p._compose_source_graph(full_timing=full_timing)
    require(len(graph)==18 and sha(graph[OLD_HELPER])==p.HELPER_SHA,'exact old18 graph required')
    old_graph=dict(graph);helper=helper_source();graph.pop(OLD_HELPER);graph[HELPER]=helper
    for name,raw in tuple(graph.items()):
        raw=raw.replace(b'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json',b'ROOT-FINAL-SDK-FREEZE-P37C23-A03.json')
        raw=raw.replace(b'root_c23_source_abort_checkpoint_inputs',b'root_c23_a03_source_abort_checkpoint_inputs')
        for old in METADATA:raw=raw.replace(old.encode(),old.replace('-C23.','-C23-A03.').encode())
        graph[name]=raw
    name='root_native30_supervisor_c23.py';raw=graph[name]
    old_guard=p.a02_attempt_guard_source().encode()
    raw=swap(raw,old_guard,runtime_attempt_helpers())
    raw=swap(raw,b'    _validate_a02_attempt(args, config)\n',b'    _validate_a03_attempt(args, config)\n')
    raw=swap(raw,b'choices=("a02",)',b'choices=("a03",)')
    raw=swap(raw,b'    parser.add_argument("--attempt-nonce", required=True)\n',
        b'    parser.add_argument("--attempt-nonce", required=True)\n    parser.add_argument("--task-nonce", required=True)\n')
    raw=raw.replace(b'old C23 stop/exit marker present; a02 cannot clear or reuse it',
        b'old C23 stop/exit marker present; a03 cannot clear or reuse it')
    raw=raw.replace(b'"attempt_id":"a02", "attempt_nonce":args.attempt_nonce,',
        b'"attempt_id":"a03", "attempt_nonce":args.attempt_nonce, "task_nonce":args.task_nonce,')
    for stem in ATTEMPT_NAMES:raw=raw.replace((stem+'-A02.').encode(),(stem+'-A03.').encode())
    raw=swap(raw,b'            "reason": reason, "failure": failure, "cleanup_classification": classification,\n',
        b'            "reason": reason, "failure": failure, "cleanup_classification": classification,\n'
        b'            "known_preload_phase": known_preload_phase(canonical),\n')
    graph[name]=raw
    p.assert_true_graph(graph);closure=p.local_import_closure(graph)
    for name,raw in graph.items():compile(raw,name,'exec')
    require(sum(map(len,graph.values()))<=2621440,'complete A03 graph exceeds original cap')
    report.update(source_fixture=True,attempt_id='a03',finite_helper={'name':HELPER,'bytes':len(helper),'sha256':sha(helper)},
        local_import_closure=closure,prior_failure_pins={'a01':A01,'a02':A02},
        entry_source_pins_after_all_edits=[(n,sha(b)) for n,b in sorted(graph.items())],
        changed_source_names=sorted(n for n,b in graph.items() if old_graph.get(n)!=b),
        actual_runtime_admitted=False,outputs_materialized=False)
    return graph,report


def build_sources(*,native_transition_inputs,business_anchor_ref,frontier_ref,actual_cold_refs=None,full_timing=True):
    p=predecessor();business=business_binding(business_anchor_ref)
    transition=p.native_transition(native_transition_inputs)
    require(isinstance(frontier_ref,dict) and frontier_ref.get('bytes')==9089
        and frontier_ref.get('sha256')=='312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce',
        'exact saved10480 frontier required')
    frontier=p.read_document(frontier_ref,16384)
    require(frontier.get('machine_id')==MACHINE and frontier.get('date_raw')==53274624
        and frontier.get('completed_cycles')==4753 and frontier.get('next_sequence')==10481
        and frontier.get('new_SDK_pair_published') is False,'saved frontier differs')
    graph,report=_compose_source_graph(full_timing=full_timing)
    report.update(source_fixture=False,business=business,native_transition_metadata=transition.manifest_metadata,
        frontier=frontier_ref,actual_cold_refs=actual_cold_refs,startup_admitted=False,
        actual_Runtime_H='NOTRUN',actual_new_Game_identity='not issued by this producer')
    return graph,report

