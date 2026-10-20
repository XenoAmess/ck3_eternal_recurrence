"""C23 true-custody cold controls, composed only in RAM.

No export, Task, Game, Driver or SAVE operation exists in this producer. Actual
new Game/recording admissions remain the responsibility of the frozen stages.
"""
import ast
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

OWN=Path(__file__).resolve().parent
REPO=OWN.parents[1]
MACHINE='xenoamess-full-tower-eb9d2c1186'
LABEL='Native30 continuous hotspot tracking and idle realm overview'
COMMIT='330d6e67c99eb22a60919b2bf7666c1ed0ca1b71'
ROWS_SHA='f16995df275525a39ceacf3825f38f5f9a508a67970d59e83cb3bb43e7f7fdb4'
ANCHOR=REPO/'_runtime/source23-integration16/SOURCE23-CANONICAL-ANCHOR.json'
ANCHOR_SHA='aa5880db457ba6b892fa24c11a4afe15f5a7ee1d28cd37b1e566a4ac75b67e39'
PINS={
 'prepare_c22_normal_warm_controls_v1.py':'8314a789be4f30a75bdaa51d90200e94ff39399786a29a8e19563fe75ae3e6cf',
 'prepare_canonical_c17_outer_sources_v1.py':'e0713f8a56e3a2be280d140d4f3246d35af84222990bc353d6b268a7d1049ffe',
 'canonical_c17_outer_binding_v1.py':'e4d45ed0e48f8ed9d30269592bcde5cc64948e983b194320a286316e20a1300a',
 'prepare_c19_canonical_controls_v1.py':'c30470805d70ae52cb50a37f969a6b3ec6c85ea69135051a7889e8fc7ee5c4f3',
 'prepare_full_batch_timing_sources_v1.py':'112d4154a4ac39261749c2be0be0097f1b8c188b7905cbd97091dc89765ef1a8',
 'full_batch_timing_v1.py':'197e4308b7d0f5a70a8c3474ec0b58581997f3e60bfc2d8414c668dae07c8e0b',
 'full_lifecycle_timing_v1.py':'dcbb92b3852123a24dac29f35f182eea6a731a46104d1837478c2990052a32ca'}
NATIVE_PINS={
 'export_native30_functional_artifact_views_v1.py':'c414dde8b9557837feaa27591fab38f2ab2a606ef8792bc21e1731955b072d99',
 'native30_functional09_artifact11_transition_v1.py':'1df6088a521f2de2f9d72d6686d161a87a28cd74a6cb35bbc59e02013e0b4442',
 'native29_to30_export_contract_v1.py':'d348b59cdf68a2da0928ccfc4034006c0c42618fe341ad0ca1c7dac1bbfa7554',
 'export_native30_immutable_sdk_views_v1.py':'90ccd7a5c12d90101217391857d793715fdaebcb98a3e374e6a5d4b3776f9369',
 'native30_export_adapter_v1.py':'2d4074379371ed91bc38ff0fc532521e277ba2795faad1fd8e9c6dd2593c5298',
 'export_immutable_sdk_views_v1.py':'8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432',
 'native30_resume_fixture_chain_v1.py':'d9e5dc3c22f3b1fc58f1ab7b93de4f7ccb480c3ed938fdc6b2375d11a814f555'}
MAP17=[('P37C17','P37C23'),('p37c17','p37c23'),('_c17','_c23'),('-C17','-C23'),
 ('SDKC17','SDKC23'),('xar.c17.','xar.c23.'),('C17-canonical-origin','C23-canonical-origin'),
 ('C17-CANONICAL-OWNER','C23-CANONICAL-OWNER'),('ROOT-C17-SDKOWNER','ROOT-C23-SDKOWNER')]
MAP22=[('P37C22','P37C23'),('p37c22','p37c23'),('_c22','_c23'),('-C22','-C23'),('SDKC22','SDKC23'),
 ('P37C16','P37C23'),('p37c16','p37c23'),('_c16','_c23'),('-C16','-C23'),('SDKC16','SDKC23'),
 ('NATIVE29','NATIVE30')]
HELPER_NAME='root_c23_source_abort_checkpoint_inputs.py'
HELPER_SHA='cdc3d000e253f22db9c70a0314dab040878e731d5abf44a751a06166bc2370c9'
KIND='EXACT_C22_STORAGE_SCHEMA_ABORT_SAVE10480_FOR_C23'


def require(ok,why):
    if not ok:raise ValueError('C23 full-enabled cold source denied: '+why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def read_document(ref,limit=262144):
    require(isinstance(ref,dict) and type(ref.get('path')) is str
        and Path(ref['path']).is_absolute() and type(ref.get('bytes')) is int
        and 0<ref['bytes']<=limit,'bounded pinned JSON reference required')
    with Path(ref['path']).open('rb') as stream:raw=stream.read(limit+1)
    require(len(raw)==ref['bytes'] and sha(raw)==ref.get('sha256'),'pinned JSON source differs')
    value=json.loads(raw);require(isinstance(value,dict),'JSON object required')
    return value


def load_tool(name):
    path=OWN/name
    require(sha(path.read_bytes())==PINS[name],'reviewed outer tool changed: '+name)
    # Existing finite producers use their exact sibling imports. They produce
    # strings only; no stage main, Task or Windows process API is called here.
    if str(OWN) not in sys.path:sys.path.insert(0,str(OWN))
    module=importlib.import_module(path.stem)
    require(Path(module.__file__).resolve()==path.resolve(),'foreign outer producer import')
    return module


def source23_binding(ref):
    """Historical parent authority retained for the already-run initial cross."""
    require(isinstance(ref,dict) and ref.get('bytes')==7206 and ref.get('sha256')==ANCHOR_SHA,'actual parent Source23 anchor required')
    anchor=read_document(ref,16384)
    require(anchor.get('schema')=='xar.source23.canonical-git-anchor/v1' and anchor.get('machine_id')==MACHINE
        and anchor.get('commit')==COMMIT and anchor.get('complete_rows_JSON',{}).get('sha256')==ROWS_SHA,
        'historical Source23 parent authority differs')
    return {'commit':COMMIT,'complete_file_count':1456,'rows_sha256':ROWS_SHA,'actual_filesystem_epoch_authority':False}


def business_binding(ref):
    path=OWN/'c23_source_abort_checkpoint_inputs_v1.py'
    require(sha(path.read_bytes())==HELPER_SHA,'actual business/frontier helper pin changed')
    spec=importlib.util.spec_from_file_location('_exact_C23_business_helper',path)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    anchor=helper.validate_business_anchor(read_document(ref,65536))
    read_document(anchor['source_plan'],131072)
    return {'anchor':ref,'commit':anchor['commit'],'tree':anchor['tree'],'parent':anchor['parent'],
        'complete_file_count':anchor['source_file_count'],'complete_source_bytes':anchor['source_bytes'],
        'rows':anchor['complete_rows_JSON'],'actual_filesystem_epoch_authority':False,'plan':anchor['source_plan']}


def native_transition(inputs):
    require(isinstance(inputs,dict) and set(inputs)=={'base_freeze_ref','base_native_ref','capacity_ref','machine_id'}
        and inputs['machine_id']==MACHINE,'four actual Native09+11 transition refs required')
    tools_root=OWN.parent
    if str(tools_root) not in sys.path:sys.path.insert(0,str(tools_root))
    def check():
        for name,digest in NATIVE_PINS.items():
            path=OWN/name;require(sha(path.read_bytes())==digest,'Native09+11 dependency pin changed: '+name)
            for alias in (path.stem,'g2_saved_campaign.'+path.stem):
                module=sys.modules.get(alias)
                require(module is None or Path(module.__file__).resolve()==path.resolve(),
                    'foreign cached Native transition dependency: '+name)
    check()
    loader=importlib.import_module('g2_saved_campaign.export_native30_functional_artifact_views_v1')
    check()
    transition=loader.read_native_transition_v1(**inputs,source_fixture=False)
    check() # Includes dependencies imported lazily during the actual validator.
    require(transition.source_fixture is False and transition.target_native['native_build_label']==LABEL,
        'synthetic or unrelated Native transition cannot qualify public source')
    metadata=transition.manifest_metadata
    require(metadata.get('qualification_kind')=='artifact_plus_closed09_functional_only'
        and metadata.get('runtime_admitted') is False and metadata.get('actual_loaded_provider_issued') is False,
        'artifact/function qualification is metadata, never runtime loaded custody')
    return transition


def mapped(name,pairs):
    for old,new in pairs:name=name.replace(old,new)
    return name


def swap(text,old,new):
    require(text.count(old)==1,'one exact source seam required: '+old[:100])
    position=text.index(old)
    result=text.replace(old,new,1)
    require(result[:position]+old+result[position+len(new):]==text,'source seam inverse differs')
    return result


def assert_true_graph(graph):
    expected={'root_native30_supervisor_c23.py':'prepare_supervisor','launch_sdk_p37c23_owner.py':'receive_entry',
        'root_p37c23_sdk_queue.py':'receive_entry','root_p37c23_mcp_entry.py':'receive_entry'}
    for name,function in expected.items():
        calls=[n for n in ast.walk(ast.parse(graph[name])) if isinstance(n,ast.Call)
            and isinstance(n.func,ast.Name) and n.func.id==function]
        require(len(calls)==1 and any(k.arg=='enabled' and isinstance(k.value,ast.Constant)
            and k.value.value is True for k in calls[0].keywords),'missing/disabled canonical role: '+name)
    require('canonical.factory.pre_native_resume' in graph['root_native30_supervisor_c23.py'].decode()
        and 'canonical.maybe_create_owner(generation)' in graph['root_native30_supervisor_c23.py'].decode()
        and 'owned_stdio(_canonical, stdio,' in graph['root_p37c23_sdk_queue.py'].decode()
        and '_canonical.install_service(service)' in graph['root_p37c23_mcp_entry.py'].decode(),
        'same-holder actual supervisor -> owner -> Queue -> stock App chain required')


EXTERNAL_IMPORT_PINS={
 'root_battle_epoch_credit':(9706,'a2a7c6f15afc6f78284dc86ca073cdd1fe933a9ece0602e3da6878e172838ae2'),
 'root_checkpoint_bootstrap_v2':(3266,'83f3d83a194b40739715d1f1aca66a0055a5dab6804666795bbf4e6c6449e422'),
 'root_committed_contact_credit':(9939,'f532cd68e57183f775e9e3291153a2aaf88b5ac7c371f6f42328ea9e26922072'),
 'root_native22_supervisor':(33499,'da7d2adc8393f5c4558c86ef06e62642efa2829a04d8c04aa07384033b718b59'),
 'root_p37_checkpoint_bootstrap':(1731,'3b447e5e174d412abbea0172961d362dc6b58610b4ba3bfbe95252ef55d9ca1a'),
 'root_p37_checkpoint_cadence':(7065,'a017eded18ca03733700fd61b10cace8981e5379e73dbe99b4d281fb97e4ae87'),
 'root_p37_clean_classifier_install':(6346,'66886d41d07e374b038051d7eee85a0fdb364eddc3292a1a5fd407997e4dceca'),
 'root_p37_halt_pending_watch':(9519,'c4e82c4e713bc24183416b92170bcf39a3ae470478fec7e13b03d5db5fbe2df5'),
 'root_p37_known_owner_recovery':(33417,'c818380740e0f552ce37be893b63c9ce7cb782755cf8bc58a779e95f5543278f'),
 'root_p37_known_pause_recovery_control':(19608,'156ce88d23edbeb7ec519056d2c840f962807373ca47206e54657229f27bcd06'),
 'root_p37_loading_readiness':(5881,'a52bc0dadf33b3edf6e98d2096dc8a4e853ef97bc0c330745bd58762d8078127'),
 'root_p37_pending_requests':(1071,'126e8698b7c0305c69a08ce7607c5cc2749ba21d4e489f20118b8b5481a05da5'),
 'root_p37_readonly_scope':(5009,'772c816fdb52ca8de1ae0c2c1244664b6b8dc55bcfe84fa29e90dc1eb6cab126'),
 'root_p37_reinforcement_recovery':(8520,'3ae23f9188eef22b7dbc2124e6fc2db2506fb3eeb98d7c127f895845ed269fb1'),
 'root_p37_robert_identity':(2808,'f617a93d6c0ce2fdedf5adae7618d1da7f8056af3224c61755527683d5483406'),
 'root_prewar_v2_diagnostics':(2681,'5d6db4855fec8b955939b3474f833fa267f8653f3cd54ce047065673b79549bc'),
 'root_saved_campaign_preflight':(20998,'6edccc9352b3ced85942a1e25e9761c29c1fd97d114aba859bc82b1b1df446e4'),
 'root_zero_day_frontend':(6140,'f06648b572d11b524ad9c4ea8a9fb68615da86b15b2363b481da9cae83942a48'),
 'root_decision_text_api_c23':(4271,'cd23b26b55d4f83552060ef522ced45d85953a0097ab066e38a3aadcc6dd2de1'),
 'root_p37c23_overlay_relay':(3031,'19d912202370a9cdb7f3c0d83e9aa2871276c219264641732b39786b62c922fc'),
 'root_continuous_segment_auto_c23':(297,'92067c1fbf9f1c38a8a68100016afd2fc937ad2806bf126b3705872b09262994'),
 'root_p37c23_compact_decision_feed':(7776,'70a05a7da171c9b93f15dc107e44cfef5819ccee152504f8950194de917ba560'),
 'p51_decision_text_shutdown_c23':(4533,'0c8c5e53270f9e80c1bede2d0b389cfc9d360c1bf85bb70e0686c2942da44260')}
LEGACY_DENIED=('recovery_read','collect_original','observe_original_start')


def local_import_closure(graph):
    names={n[:-3] for n in graph};rows=[];legacy=[]
    for name,raw in graph.items():
        tree=ast.parse(raw)
        for node in ast.walk(tree):
            if not isinstance(node,ast.ImportFrom) or not node.module or not node.module.startswith(('root_','p51_','launch_')):continue
            if node.module in {'root_pending_declaration_recovery','root_warm_prepare'}:
                require(name=='root_p37c23_sdk_queue.py','legacy missing import escaped historical Queue classes')
                context=next(((c.name,f.name) for c in tree.body if isinstance(c,ast.ClassDef)
                    for f in c.body if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef))
                    and f.lineno<=node.lineno<=f.end_lineno),None)
                require(context in {('FreshQueue',n) for n in LEGACY_DENIED}
                    | {('WarmQueue','preflight'),('PerformanceQueue','preflight')},'unproved legacy missing import')
                legacy.append([node.module,*context]);continue
            require(node.module in names or node.module in EXTERNAL_IMPORT_PINS,'unclosed local import: '+node.module)
            rows.append([name,node.lineno,node.module,'graph' if node.module in names else 'pinned_external'])
    classes={n.name:n for n in ast.parse(graph['root_p37c23_sdk_queue.py']).body if isinstance(n,ast.ClassDef)}
    require([ast.unparse(x) for x in classes['CleanRobertMainMenuQueue'].bases]==['SavedCampaignSemanticQueue']
        and [ast.unparse(x) for x in classes['SavedCampaignSemanticQueue'].bases]==['SavedCampaignVisualQueue']
        and [ast.unparse(x) for x in classes['SavedCampaignVisualQueue'].bases]==['FreshQueue'],
        'actual cold base MRO includes a legacy warm preflight')
    cold=ast.parse(graph['root_p37c23_cold_resume.py'])
    denied={n.name for n in ast.walk(cold) if isinstance(n,ast.AsyncFunctionDef)
        and n.name in LEGACY_DENIED and len(n.body)==1 and isinstance(n.body[0],ast.Raise)}
    require(denied==set(LEGACY_DENIED),'C23 cold legacy recovery entries must explicitly refuse')
    return {'imports':rows,'legacy_missing':legacy,'legacy_runtime_denied':list(LEGACY_DENIED),
        'external_source_pins':EXTERNAL_IMPORT_PINS,'startup_admitted':False}


def external_import_guard_source():
    return '\n_C23_EXTERNAL_IMPORT_PINS='+repr(EXTERNAL_IMPORT_PINS)+'''\n
def _check_c23_external_imports(root, policy):
    refs=policy.get('external_import_source_pins')
    require(isinstance(refs,dict) and set(refs)==set(_C23_EXTERNAL_IMPORT_PINS), 'all frozen external algorithms must be explicitly pinned')
    entries={str(Path(p).resolve(strict=True)):h for p,h in policy['entry_source_pins']}
    for name,(size,digest) in _C23_EXTERNAL_IMPORT_PINS.items():
        ref=refs[name];path=(root/(name+'.py')).resolve(strict=True)
        require(Path(ref['path']).resolve(strict=True)==path and ref.get('bytes')==size
            and ref.get('sha256')==digest and entries.get(str(path))==digest, 'external import pin differs: '+name)
        with path.open('rb') as stream:raw=stream.read(1048577)
        require(len(raw)==size and hashlib.sha256(raw).hexdigest()==digest, 'external algorithm changed: '+name)
        module=sys.modules.get(name)
        require(module is None or Path(module.__file__).resolve(strict=True)==path, 'foreign cached external algorithm: '+name)
'''


def transform_cold_feeder_source(raw,*,source_ref):
    """Freeze timing algorithms before then-actual five-reference admission.

    The caller supplies its independently qualified C23 cold feeder bytes. This
    function changes neither namespace nor admission data and grants no right
    to start it. Following/restart has no reconstructed monotonic origin.
    """
    require(type(raw) is bytes and isinstance(source_ref,dict)
        and source_ref.get('bytes')==len(raw) and source_ref.get('sha256')==sha(raw),
        'exact independently frozen feeder input bytes required')
    timing=load_tool('prepare_full_batch_timing_sources_v1.py')
    result,changes=timing.transform_feeder(raw,enabled=True)
    return result,{'source_only':True,'source_input':source_ref,'source_output_bytes':len(result),
        'source_output_sha256':sha(result),'exact_inverse_hunks':len(changes),
        'FULL_lifecycle_enabled':True,'new_publish_start':'before original atomic publish',
        'validated_receipt_end':'after original successful result_for validation',
        'following_or_restart_origin':None,'actual_five_refs_bound':False,'startup_admitted':False}


def _compose_source_graph(*,full_timing=True):
    require(type(full_timing) is bool,'explicit FULL timing policy required')
    current=load_tool('prepare_c22_normal_warm_controls_v1.py')
    canonical=load_tool('prepare_canonical_c17_outer_sources_v1.py')
    prior=load_tool('prepare_c19_canonical_controls_v1.py')
    timing=load_tool('prepare_full_batch_timing_sources_v1.py')
    # Start from the true enabled graph; timing.build_sources() is forbidden.
    template,creator_hunks=canonical.build_sources(enabled=True,native_build_label=LABEL)
    def port(text,pairs):return canonical.prior.prior.port(text,pairs)
    graph={mapped(n,MAP17):port(b.decode(),MAP17).encode() for n,b in template.items()}
    before,current_report=current._source_graph_v1()
    current_ported={mapped(n,MAP22):port(b.decode(),MAP22).encode() for n,b in before.items()}
    # Current seven controls carry all adopted Queue/entry/planner safeguards.
    # Keep the reviewed cold factory rather than the fixed same-Game warm one.
    for name,raw in current_ported.items():
        if not name.endswith('_warm_resume.py'):graph[name]=raw
    # The qualified09+11 artifact is the original immutable DLL, not a renamed
    # Native29 staging copy. Preserve every source/hash/RVA/path guard and bind
    # only its actual filename; no alias or binary write is introduced here.
    binder=graph['root_native_build_binding_p37c23.py'].decode()
    binder=swap(binder,"dll.name.lower() != 'native.dll'","dll.name.lower() != 'xar_ck3_bridge.dll'")
    graph['root_native_build_binding_p37c23.py']=binder.encode()
    supervisor=graph['root_native30_supervisor_c23.py'].decode()
    supervisor=swap(supervisor,'dll.name.lower() != "native.dll"','dll.name.lower() != "xar_ck3_bridge.dll"')
    supervisor=swap(supervisor,'explicit native.dll and qualified injector EXE are required',
        'explicit qualified Native30 artifact DLL and injector EXE are required')
    supervisor=swap(supervisor,'    sys.path.insert(0, str(repo / "tools"))\n'
        '    from g2_saved_campaign.sdk_process_custody import RetainedProcessGeneration\n',
        '    if canonical is None:\n        sys.path.insert(0, str(repo / "tools"))\n'
        '    else:\n        sys.path.insert(0, str(canonical.tools_root))\n        canonical.tools()\n'
        '    from g2_saved_campaign.sdk_process_custody import RetainedProcessGeneration\n'
        '    if canonical is not None:\n        canonical.tools()\n')
    graph['root_native30_supervisor_c23.py']=supervisor.encode()
    seams={}
    for oldname,changes in creator_hunks.items():
        name=mapped(oldname,MAP17)
        if name not in current_ported:continue
        text=graph[name].decode();original=text
        # A frozen hunk can be an indented/incomplete statement, so it cannot
        # be parsed as a module by the whole-file namespace porter. Its finite
        # namespace substitution is inverse-checked; the completed module is
        # compiled below. No unreviewed current-source text is mapped this way.
        for old,new in changes:
            a,b=mapped(old,MAP17),mapped(new,MAP17)
            require(mapped(a,[(y,x) for x,y in reversed(MAP17)])==old
                and mapped(b,[(y,x) for x,y in reversed(MAP17)])==new,'creator hunk namespace inverse differs')
            text=swap(text,a,b)
        graph[name]=text.encode();seams[name]=len(changes)
    queue=graph['root_p37c23_sdk_queue.py'].decode()
    queue=swap(queue,'from root_p37c23_warm_resume import make_normal_source_warm_queue_v1',
        'from root_p37c23_cold_resume import make_normal_checkpoint_cold_queue_v1')
    queue=swap(queue,"FreshQueue = make_normal_source_warm_queue_v1(CleanRobertMainMenuQueue, globals(), admission_path=N/'ROOT-P37C23-SOURCE-RESUME-ADMISSION.json')",
        "FreshQueue = make_normal_checkpoint_cold_queue_v1(CleanRobertMainMenuQueue, globals(), admission_path=N/'ROOT-P37C23-COLD-RESUME-ADMISSION.json')")
    queue=swap(queue,"admission_getter=lambda queue: queue._normal_source_warm['admission'].get('control_timing')",
        'admission_getter=lambda queue: None')
    wal_source=current.checked_bytes(current.C21,8570,current.C21_SHA)
    wal=next(ast.literal_eval(n.value) for n in ast.parse(wal_source).body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='WAL_HUNK' for t in n.targets))
    require(len(wal.encode())==313 and queue.count(wal)==1,'retained exact313B strict optional WAL seam missing')
    graph['root_p37c23_sdk_queue.py']=queue.encode()
    owner=graph['launch_sdk_p37c23_owner.py'].decode()
    owner=owner.replace('ROOT-P37C23-SOURCE-RESUME-ADMISSION.json','ROOT-P37C23-COLD-RESUME-ADMISSION.json')
    owner=swap(owner,'from root_p37c23_warm_resume import current_recording_inputs_v1',
        'from root_p37c23_cold_resume import current_recording_inputs_v1')
    owner=swap(owner,'from root_native29_supervisor_c23 import validate_sdk_process_pair',
        'from root_native30_supervisor_c23 import validate_sdk_process_pair')
    graph['launch_sdk_p37c23_owner.py']=owner.encode()
    cold=graph['root_p37c23_cold_resume.py'].decode()
    cold=swap(cold,'    from root_checkpoint6397_cold_contract_c23 import validate_rollback\n','')
    old="""    if admission.get('old_sdk_closure_kind') == 'EXACT_C16_NORMAL_CHECKPOINT_FOR_C17':
        from root_c23_normal_checkpoint_inputs import validate_saved_seed
        validate_saved_seed(admission, seed, original, save, saved_semantic, gov,
            projector=project_checkpoint_seed, checked=checked)
    else:
        validate_rollback(admission, seed, gov, checkpoint_saved=checkpoint_saved)"""
    new="""    require(admission.get('old_sdk_closure_kind') == 'EXACT_C22_STORAGE_SCHEMA_ABORT_SAVE10480_FOR_C23',
        'only the saved-checkpoint source-schema-abort authority is supported')
    from root_c23_source_abort_checkpoint_inputs import validate_saved_seed
    validate_saved_seed(admission, seed, original, save, saved_semantic, gov, checked=checked)"""
    cold=swap(cold,old,new)
    old="""            from root_checkpoint6397_cold_contract_c23 import validate_sdk_interruption
            sdk_closed = (validate_sdk_interruption(admission, old)
                if admission.get('old_sdk_closure_kind') == 'EXACT_C15_INTERRUPTED_F90'
                else env['sdk_pair_closed'](old))"""
    cold=swap(cold,old,"            sdk_closed = env['sdk_pair_closed'](old)")
    cold=swap(cold,'            freeze = checked(admission[\'sdk_freeze\'], 2*1024**2)\n',
        "            freeze = checked(admission['sdk_freeze'], 2*1024**2)\n"
        '            from root_c23_source_abort_checkpoint_inputs import validate_frozen_business\n'
        '            validate_frozen_business(admission, freeze, checked)\n')
    wrapper="""def current_recording_inputs_v1(admission):
    from root_c23_source_abort_checkpoint_inputs import current_recording_inputs_v1 as validate_recording
    return validate_recording(admission, checked)


"""
    cold=swap(cold,'def make_normal_checkpoint_cold_queue_v1(base, env, *, admission_path):',
        wrapper+'def make_normal_checkpoint_cold_queue_v1(base, env, *, admission_path):')
    denial=''.join('        async def '+name+'(self, *args, **kwargs):\n'
        '            raise ValueError("C23 cold legacy recovery unavailable; no RPC or request replay admitted")\n\n'
        for name in LEGACY_DENIED)
    cold=swap(cold,'    class NormalCheckpointColdQueue(base):\n',
        '    class NormalCheckpointColdQueue(base):\n'+denial)
    cold=swap(cold,"            api = load_api(env['N'])\n",
        "            recording = current_recording_inputs_v1(admission)\n            api = load_api(env['N'])\n")
    cold=swap(cold,"require(started_reference(env['N'], api) == admission['publisher_started']",
        "require(started_reference(env['N'], api) == admission['publisher_started'] == recording['binding']['publisher_started']\n"
        "                and self.record_job.resolve() == recording['root']\n"
        "                and self.args.first_frame_admission.resolve() == recording['first_path']")
    graph['root_p37c23_cold_resume.py']=cold.encode()
    boot=graph['root_checkpoint_bootstrap_c23.py'].decode()
    start="    if close.get('old_sdk_closure_kind') == 'EXACT_C15_INTERRUPTED_F90':\n"
    block="""    if close.get('old_sdk_closure_kind') == 'EXACT_C15_INTERRUPTED_F90':
        from root_checkpoint6397_cold_contract_c23 import validate_sdk_interruption
        validate_sdk_interruption(close, sdk)
    else:
        require(sdk.get('normal') is True and sdk.get('machine_id') == MACHINE
            and sdk.get('launcher_exit_code') == 0 and len(sdk.get('processes', [])) == 2
            and all(p.get('exit_code') == 0 and p.get('kernel_exit_observed') is True
                and p.get('observation_error') is None for p in sdk['processes']), 'normal actual SDK kernel closure required')"""
    replacement="""    require(sdk.get('normal') is True and sdk.get('machine_id') == MACHINE
        and sdk.get('launcher_exit_code') == 0 and len(sdk.get('processes', [])) == 2
        and all(p.get('exit_code') == 0 and p.get('kernel_exit_observed') is True
            and p.get('observation_error') is None for p in sdk['processes']), 'normal actual SDK kernel closure required')"""
    boot=swap(boot,block,replacement)
    block="""    if close.get('old_sdk_closure_kind') == 'EXACT_C15_INTERRUPTED_F90':
        from root_checkpoint6397_cold_contract_c23 import validate_abnormal_closure
        validate_abnormal_closure(close)
    else:
        from root_c23_normal_checkpoint_inputs import validate_normal_closure
        validate_normal_closure(close, checked)"""
    boot=swap(boot,block,"    from root_c23_source_abort_checkpoint_inputs import validate_source_abort_closure\n"
        '    validate_source_abort_closure(close, checked)')
    graph['root_checkpoint_bootstrap_c23.py']=boot.encode()
    graph.pop('root_checkpoint6397_cold_contract_c23.py')
    graph.pop('root_c23_normal_checkpoint_inputs.py')
    graph[HELPER_NAME]=(OWN/'c23_source_abort_checkpoint_inputs_v1.py').read_bytes()
    require(sha(graph[HELPER_NAME])==HELPER_SHA,'finite source-abort helper pin differs')
    outer,records=prior.outer_helper(graph['root_c23_canonical_outer.py'].decode())
    outer=swap(outer,"        self.policy = checked(self.freeze['canonical_preload_policy'])\n",
        "        self.policy = checked(self.freeze['canonical_preload_policy'])\n"
        '        _check_c23_external_imports(self.root, self.policy)\n')
    outer+=external_import_guard_source()
    graph['root_c23_canonical_outer.py']=outer.encode()
    # Original lifecycle semantics are kept. FULL receipts may carry bounded
    # timing; the optional segmented control probe is explicitly not enabled.
    graph['root_p37c23_sdk_queue.py'],_=timing.transform_queue(graph['root_p37c23_sdk_queue.py'],enabled=full_timing)
    graph['root_p37c23_automatic_natural_succession_handoff.py'],_=timing.transform_handoff(graph['root_p37c23_automatic_natural_succession_handoff.py'])
    for name in ('full_batch_timing_v1.py','full_lifecycle_timing_v1.py'):graph[name]=(OWN/name).read_bytes()
    assert_true_graph(graph)
    closure=local_import_closure(graph)
    for name,raw in graph.items():compile(raw,name,'exec')
    require(sum(map(len,graph.values()))<=2621440,'complete generated RAM graph exceeds participation cap')
    return graph,{'source_only':True,'source_fixture':True,'canonical_enabled':True,
        'FULL_wall_and_rows':full_timing,'control_probe_enabled':False,'WAL_policy_default':False,
        'WAL_explicit_child_policy':{'enable_driver_state_wal_v1':True},
        'retained_WAL_hunk_bytes':313,'original_creator_hunk_counts':seams,
        'cold_feeder_timing_entry':'transform_cold_feeder_source(raw, source_ref=exact_frozen_ref)',
        'FULL_publish_to_receipt_active_in_this_graph':False,
        'before_continuous_play':'runtime must bind then-actual cold feeder five refs and adopt lifecycle-enabled transformed feeder; no local sum substitutes for full wall',
        'source_abort_kind':KIND,'saved_frontier':{'completed_cycles':4753,'date_raw':53274624,'checkpoint_saved_count':74,'next_sequence':10481},
        'classifier_sha256':current_report['classifier_sha256'],
        'actual_runtime_admitted':False,'outputs_materialized':False,
        'new_Game_recording_publisher_Root_refs_required':True,
        'local_import_closure':closure,
        'same_holder_pre_native_resume_owner_Queue_stock_App':True,
        'entry_source_pins_after_all_edits':[(n,sha(b)) for n,b in sorted(graph.items())]}


def build_sources(*,native_transition_inputs,business_anchor_ref,frontier_ref,actual_cold_refs=None,full_timing=True):
    """Public source freeze. Missing new identities remain a runtime admission block.

    The supervisor source must exist before creating the new Game. Therefore
    this source-only API can return bytes before new-Game receipts exist; it
    never returns a startup/adoption permission or creates an output itself.
    """
    business=business_binding(business_anchor_ref)
    transition=native_transition(native_transition_inputs)
    require(isinstance(frontier_ref,dict) and frontier_ref.get('bytes')==9089 and frontier_ref.get('sha256')==
        '312165ea447d2b1e94be0d0b7e0b749a8892f59b1034feb93df90a880f326fce','exact F99 frontier reference required')
    frontier=read_document(frontier_ref,16384)
    require(frontier.get('machine_id')==MACHINE and frontier.get('date_raw')==53274624
        and frontier.get('completed_cycles')==4753 and frontier.get('next_sequence')==10481
        and frontier.get('new_SDK_pair_published') is False,'F99 saved boundary differs')
    graph,report=_compose_source_graph(full_timing=full_timing)
    report.update(source_fixture=False,business=business,native_transition_metadata=transition.manifest_metadata,
        frontier=frontier_ref,actual_cold_refs=actual_cold_refs,
        startup_admitted=False,actual_Runtime_H='NOTRUN',actual_new_Game_identity='not issued by this producer')
    return graph,report
