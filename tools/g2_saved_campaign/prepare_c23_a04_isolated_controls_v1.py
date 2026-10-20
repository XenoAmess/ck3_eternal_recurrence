"""A04 isolated controls, RAM-only. No files, junction, Game or Task are created."""
import ast
import hashlib
import json
from pathlib import Path
import sys
OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(OWN))
import prepare_c23_a03_full_enabled_cold_controls_v1 as prior
MACHINE=prior.MACHINE
OLD_RUNTIME=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
NEW_RUNTIME=OLD_RUNTIME.with_name('runtime-a04')
OLD_POLICY_SHA='66b58de84d8e773ef5d37636c1402f836aa52b6f0489e76f2ed327f1d4c63159'


def require(ok,why):
    if not ok:raise ValueError('A04 isolated source denied: '+why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def ref(path):
    raw=Path(path).read_bytes()
    require(len(raw)<=1048576,'bounded exact source required')
    return {'path':str(Path(path).resolve()),'bytes':len(raw),'sha256':sha(raw)}


def dependency_outer(raw):
    return prior.swap(raw,
        b'        if str(self.dependency_root) not in sys.path:\n            site.addsitedir(str(self.dependency_root))\n',
        b'        site.addsitedir(str(self.dependency_root))\n')


def a04_guard():
    return b'''
def _validate_a04_attempt(args,config):
    value=validate_attempt(args,config,_a03_checked)
    index=_a03_checked(value['prior_failure_a03'])
    require(index.get('schema')=='xar.C23-A03-sdk-import-failure-closed/v1'
        and index.get('machine_id')==MACHINE and index.get('execution_owner')=='Root'
        and index.get('root_direct_execution_release') is True
        and index.get('status')=='A03_SDK_IMPORT_FAILURE_CLOSED_NO_RPC'
        and index.get('MCPApp_created') is False and index.get('Game_RPC_calls')==0
        and index.get('SAVE10480_unchanged') is True,'exact actual A03 no-RPC failure closure required')
    refs=index['source_refs']
    closed=_a03_checked(refs['supervisor_closed']);game=_a03_checked(refs['Game_exit'])
    task=_a03_checked(refs['supervisor_Task_CLOSED']);removed=_a03_checked(refs['Task_unregistered'])
    require(closed.get('machine_id')==game.get('machine_id')==task.get('machine_id')==MACHINE
        and (closed.get('keeper') or {}).get('thread_exited') is True
        and game.get('kernel_signaled') is True and type(game.get('exit_code')) is int
        and task.get('job_active_after_stage')==0 and task.get('forced_remaining_cleanup') is False,
        'actual A03 supervisor/Game/Task closure required')
    if 'stdout' in removed:
        require(removed.get('returncode')==0 and isinstance(removed['stdout'],str)
            and len(removed['stdout'])<=16384,'actual pinned unregister wrapper failed')
        removed=json.loads(removed['stdout'])
    actual=removed.get('actual') or (removed.get('unregister') or {}).get('actual') or {}
    require(actual.get('absent_after') is True,'actual A03 Task unregister required')
    require(args.attempt_nonce not in {closed.get('attempt_nonce'),closed.get('task_nonce')}
        and args.task_nonce not in {closed.get('attempt_nonce'),closed.get('task_nonce')},
        'A04 nonces cannot reuse A03 attempt or Task')
    return value
'''


def build_sources(*,new_runtime_root=NEW_RUNTIME):
    """Quote small source clones only; state is an explicit future shared alias."""
    new=Path(new_runtime_root).resolve();old=OLD_RUNTIME.resolve(strict=True)
    require(new==NEW_RUNTIME.resolve() and not new.exists(),'new isolated runtime-a04 must be absent')
    policy_raw=(old/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A03.json').read_bytes()
    require(sha(policy_raw)==OLD_POLICY_SHA,'actual deployed A03 policy required')
    policy=json.loads(policy_raw);raws={};oldpins={}
    for path,digest in policy['entry_source_pins']:
        path=Path(path).resolve(strict=True)
        raw=path.read_bytes();require(sha(raw)==digest,'A03 frozen complete source changed')
        if path.parent==old:raws[path.name]=raw;oldpins[path.name]=ref(path)
    require(len(raws)==41,'actual A03 runtime41 source closure required')
    for name in ('root_p37c23_same_game_loop_feeder100.py','root_continuity_window_c23_100.py',
            'launch_c23_feeder100.py','root_p37c11_prisoner_epoch_classifier.py'):
        raws[name]=(old/name).read_bytes();oldpins[name]=ref(old/name)
    # Complete ordinary sibling imports from exact existing sources. Missing
    # legacy imports remain runtime-denied by the unchanged cold adapter.
    todo=list(raws)
    while todo:
        name=todo.pop()
        for node in ast.walk(ast.parse(raws[name])):
            modules=([node.module] if isinstance(node,ast.ImportFrom) and node.level==0
                else [a.name for a in node.names] if isinstance(node,ast.Import) else [])
            for module in modules:
                if not module or '.' in module:continue
                path=old/(module+'.py')
                if path.is_file() and path.name not in raws:
                    require(len(raws)<256,'bounded local source closure exceeded')
                    raws[path.name]=path.read_bytes();oldpins[path.name]=ref(path);todo.append(path.name)
    graph,report=prior._compose_source_graph()
    for name,data in graph.items():
        require(data==raws[name],'actual deployed A03 control differs from admitted producer')
        data=data.replace(b'C23-A03',b'C23-A04')
        if name=='root_c23_canonical_outer.py':data=dependency_outer(data)
        if name=='root_native30_supervisor_c23.py':
            data=prior.swap(data,b"args.attempt=='a03'",b"args.attempt=='a04'")
            data=prior.swap(data,b"value.get('attempt_id')=='a03'",b"value.get('attempt_id')=='a04'")
            data=prior.swap(data,b'def _validate_a03_attempt(args,config):\n    return validate_attempt(args,config,_a03_checked)\n',a04_guard())
            data=data.replace(b'_validate_a03_attempt(args, config)',b'_validate_a04_attempt(args, config)')
            data=data.replace(b'choices=("a03",)',b'choices=("a04",)').replace(b'"attempt_id":"a03"',b'"attempt_id":"a04"')
        compile(data,name,'exec');raws[name]=data
    feeder='root_p37c23_same_game_loop_feeder100.py'
    raws[feeder]=prior.swap(raws[feeder],b'ROOT-FINAL-SDK-FREEZE-P37C23-A03.json',b'ROOT-FINAL-SDK-FREEZE-P37C23-A04.json')
    for name in raws:
        if name not in graph:compile(raws[name],name,'exec')
    allocation=sum(((len(b)+4095)//4096)*4096 for b in raws.values())
    fresh=[n for n,b in raws.items() if sha(b)!=oldpins[n]['sha256']]
    fresh_allocation=sum(((len(raws[n])+4095)//4096)*4096 for n in fresh)
    return raws,{'schema':'xar.C23-A04-isolated-source-quote/v1','machine_id':MACHINE,
        'old_runtime':str(old),'new_runtime':str(new),'source_files':len(raws),
        'source_logical_bytes':sum(map(len,raws.values())),'source_allocation_upper':allocation,
        'fresh_source_names':sorted(fresh),'fresh_source_allocation_upper':fresh_allocation,
        'immutable_hardlink_names':sorted(set(raws)-set(fresh)),
        'hardlinks_require_same_volume_exact_FileID_SHA_and_no_inplace_writes':True,
        'sources':[{'relative':n,'bytes':len(b),'sha256':sha(b),'A03_original':oldpins[n]} for n,b in sorted(raws.items())],
        'future_state_alias':{'path':str(new/'state'),'exact_target':str(old/'state'),
            'requires_actual_A03_consumers_closed':True,'must_verify_resolved_path_and_file_identity':True,
            'large_input_bytes_copied':0,'alias_created':False},
        'future_metadata':{'RootFinal':'ROOT-FINAL-SDK-FREEZE-P37C23-A04.json',
            'policy':'ROOT-C23-CANONICAL-PRELOAD-POLICY-A04.json',
            'five_supervisor_attempt_outputs':'C23-A04','canonical_generation':'P37C23'},
        'actual_runtime_admitted':False,'outputs_created':0,'Task_Game_RPC_calls':0,
        'Source25_export_operations':0,'Native_Driver_SAVE_business_bytes_changed':0}


if __name__=='__main__':
    _,report=build_sources()
    print(json.dumps(report,ensure_ascii=False))

