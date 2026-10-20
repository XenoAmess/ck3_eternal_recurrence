"""Explicit compiled-component source reuse, separate from whole-tree rebuilds.

Candidate canonical location: tools/ck3_mod_acceptance_native_component_reuse.py.
This does not change the historical qualified-native-build or linked-worktree
contracts. A caller must consume this distinct selection schema explicitly.
"""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,subprocess

PREFIX='ck3_autonomous_player/native_bridge'
SCHEMA='xar.e04.native-component-current-source-selection.v1'
PYTHON_ROLES={
    'research/run_ck3_12002_mcp_live.py':'current public Python host; not a native compiler TU',
    'research/refill_add_live_12004/consume_live_refill_add.py':'complete retained-proof Python serialization consumer',
    'research/maintenance_writer_cold_12004/run_cold_fixture.py':'finite standalone Python cold controller',
    'research/maintenance_writer_cold_12004/test_run_cold_fixture_selection.py':'Python routing regression test',
}
def require(ok,message):
    if not ok:raise ValueError(message)
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def pin(path):
    path=Path(path);require(path.suffix.lower() not in ('.exe','.dll','.obj','.pdb','.lib'),'Binary body reads are outside source selection')
    require(path.stat().st_size<=1024*1024,'Small source/metadata limit')
    raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def exact(ref):
    require(pin(ref['path'])==ref,'Exact source/metadata reference differs')
    return json.loads(Path(ref['path']).read_bytes())
def git(repo,*args,raw=False):
    result=subprocess.run(['git',*args],cwd=repo,check=True,capture_output=True)
    return result.stdout if raw else result.stdout.decode('utf-8').strip()
def entries(repo,commit):
    result={}
    for row in git(repo,'ls-tree','-r','-l','-z',commit+':'+PREFIX,raw=True).split(b'\0'):
        if not row:continue
        header,path=row.split(b'\t',1);mode,kind,oid,size=header.decode().split()
        require(kind=='blob' and mode in ('100644','100755'),'Unsupported Native tracked input type')
        result[path.decode('utf-8')]=dict(mode=mode,git_blob=oid,bytes=int(size))
    return result
def observe_equivalence(repo,base,current):
    old,new=entries(repo,base),entries(repo,current)
    names=sorted(set(old)|set(new))
    changed=[name for name in names if old.get(name)!=new.get(name)]
    require(changed and set(changed)<=set(PYTHON_ROLES),'Native change exceeds explicitly reviewed Python-only paths')
    old_nonpy={name:value for name,value in old.items() if not name.endswith('.py')}
    new_nonpy={name:value for name,value in new.items() if not name.endswith('.py')}
    require(old_nonpy==new_nonpy,'CXX/CMake/header/ASM/resource or other non-Python Native input changed')
    closure=[dict(native_relative=name,**value) for name,value in sorted(old_nonpy.items())]
    rows=[]
    for name in changed:
        raw=git(repo,'show',current+':'+PREFIX+'/'+name,raw=True)
        rows.append(dict(native_relative=name,role=PYTHON_ROLES[name],before=old.get(name),after=new[name],
            committed_python_bytes=len(raw),committed_python_sha256=hashlib.sha256(raw).hexdigest()))
    return dict(base_commit=base,current_commit=current,compiled_native_tree=git(repo,'rev-parse',base+':'+PREFIX),
        runtime_native_tree=git(repo,'rev-parse',current+':'+PREFIX),
        complete_native_name_status=git(repo,'diff','--name-status',base,current,'--',PREFIX).splitlines(),
        changed_python=rows,nonpy_input_count=len(closure),nonpy_git_blob_map_sha256=hashlib.sha256(encoded(closure)).hexdigest(),
        nonpy_inputs_identical=True,closure=closure,
        proof_scope='Complete immutable Git blob/mode/size equivalence for every non-Python Native input. Not a new compiler run or a full raw working-tree/binary rehash.')
def select_components(repo,current,machine,carrier_ref,writer_ref,equivalence,source_swap_ref):
    repo=Path(repo).resolve()
    require(git(repo,'rev-parse','HEAD')==current and not git(repo,'status','--porcelain','--untracked-files=all'),
            'Actual runtime checkout must be clean at its declared current commit')
    carrier,writer=exact(carrier_ref),exact(writer_ref)
    require(carrier.get('schema')=='xar.e04.a41-coherent-relocation-worker-qualification.v1'
        and carrier.get('machine_id')==machine and carrier.get('production_bytes_qualified') is True
        and carrier.get('focused_cold_qualified') is True,'Actual qualified A41 carrier required')
    require(writer.get('schema')=='xar.e04.r08-a08-standalone-qualification.v1' and writer.get('machine_id')==machine
        and writer.get('status')=='SELECTED_STANDALONE_SCOPE_PASS' and writer.get('compiled_bytes_qualified') is True
        and writer.get('focused_cold_qualified') is True,'Actual separately qualified A08 standalone writer required')
    require(equivalence['current_commit']==current and equivalence['compiled_native_tree']==carrier['native_tree'],
            'Compile/current source layers differ from the observed equivalence')
    require(git(repo,'rev-parse',carrier['native_build_source_head']+':'+PREFIX)==carrier['native_tree'],
            'Original main compilation Native tree differs')
    require(subprocess.run(['git','merge-base','--is-ancestor',carrier['native_build_source_head'],current],cwd=repo).returncode==0,
            'Actual main compile source must precede current runtime')
    actual=observe_equivalence(repo,equivalence['base_commit'],current)
    require(actual==equivalence,'Immutable complete Native equivalence changed')
    swap=exact(source_swap_ref)
    require(swap.get('machine_id')==machine,'Actual source-swap receipt belongs to another machine')
    outputs=[]
    for target in ('xar_ck3_bridge','xar_ck3_bridge_injector','xar_ck3_bridge_host'):
        rows=[row for row in carrier['outputs'] if row['target']==target]
        require(len(rows)==1,'Unique original compiled carrier target required')
        row=dict(rows[0]);path=Path(row['path'])
        require(path.is_file() and not path.is_symlink() and path.stat().st_size==row['bytes'],'Retained compiled artifact stat differs')
        outputs.append(row)
    current_python=[]
    for row in actual['changed_python']:
        path=repo/PREFIX/row['native_relative'];ref=pin(path)
        current_python.append(dict(relative_path=PREFIX+'/'+row['native_relative'],current_worktree_pin=ref,
            current_git_blob=row['after']['git_blob'],role=row['role']))
    cpp=repo/PREFIX/'research/maintenance_writer_cold_12004/cold_observer.cpp'
    require(pin(cpp)['sha256']==writer['source_cpp']['sha256'],'Current standalone CXX differs from actual A08 compile source')
    return dict(schema=SCHEMA,machine_id=machine,observed_at_utc=datetime.now(timezone.utc).isoformat(),
        status='CURRENT_SOURCE_COMPILED_COMPONENT_REUSE_SELECTED_NOT_RECOMPILED',source_head=current,
        runtime_source_head=current,runtime_native_tree=actual['runtime_native_tree'],
        native_tree=carrier['native_tree'],compiled_native_tree=carrier['native_tree'],
        native_build_source_head=carrier['native_build_source_head'],
        carrier_qualification=carrier_ref,writer_qualification=writer_ref,source_swap=source_swap_ref,
        outputs=outputs,all_feature_flags=carrier['all_feature_flags'],
        actual_source_layers=dict(carrier=carrier.get('actual_source_layers',carrier.get('source_layers')),
            original_main_compile_source=carrier['native_build_source_head'],original_carrier_native_tree=carrier['native_tree'],
            standalone_writer_compile_source=writer['native_build_source_head'],
            runtime_public_python_source=current),
        complete_git_equivalence={key:value for key,value in actual.items() if key!='closure'},
        current_python=current_python,
        source_selection_qualified=True,production_bytes_reused_from_actual_A41=True,
        production_bytes_qualified=True,focused_cold_qualified=True,
        binary_payload_rehashed=False,new_compilation=False,whole_native_tree_equal=False,
        current_binary_stat_only=True,public_preflight_and_allocation_still_verify_actual_binary_pins=True,
        ordinary_native_memory_path_qualified=False,full_R08_business_qualified=False,new_live_admission=False,
        scope='Old qualified compiled source and current Python/runtime are separate. This explicit component selection does not satisfy or weaken the old whole-tree build/binding schema.')
