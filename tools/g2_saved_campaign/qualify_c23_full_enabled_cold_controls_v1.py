"""Three current cross-package checks. No Native, Task or filesystem fixtures."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prepare_c23_full_enabled_cold_controls_v1 as p
import c23_source_abort_checkpoint_inputs_v1 as finite

T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
P=T.parent.parent/'p51-fresh1066-v20261019-prepare01'
ABORT_REF={'path':str(P/'c22-source22-warm99/C22-WARM-ABORT-CLOSED99.json'),'bytes':9089,'sha256':finite.ABORT_SHA}


def ref(path,limit=262144):
    path=Path(path)
    with path.open('rb') as stream:raw=stream.read(limit+1)
    if len(raw)>limit:raise ValueError('test bounded metadata only')
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def fn(source,name):
    nodes=[n for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    if len(nodes)!=1:raise ValueError('one exact function required: '+name)
    return nodes[0]


def class_method(source,cls,name):
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name==cls)
    return next(n for n in node.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)


def actual_frontier_fixture():
    """Real small immutable rows, with a RAM-only future wrapper/prelaunch envelope.

    The history_rows value is a synthetic lower bound for testing, not an actual
    serialized Driver history-length observation. No Driver body is opened.
    """
    abort=p.read_document(ABORT_REF,16384);sources=abort['sources']
    hashed=p.read_document(sources['Driver_hash_only'])
    close={'machine_id':p.MACHINE,'old_sdk_closure_kind':p.KIND,'old_Game':copy.deepcopy(finite.OLD_GAME),
        'source_abort_index':ABORT_REF,'sdk_closed':ref(T/'ROOT-P37C20-OWNER-CLOSED.json'),
        'old_sdk_pair':ref(T/'ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37C20.json'),
        'Game_exit':sources['Game_exit'],'driver_state':hashed['closed_Driver'],
        'original_command_history_preserved':True,'history_rows':5268,
        'checkpoint':abort['actual_saved_checkpoint']}
    oldq=T/'p37-queue-closed-C20-before-C22-10481'
    admission={'old_sdk_closure_kind':p.KIND,'old_Game':copy.deepcopy(finite.OLD_GAME),
        'next_sequence':10481,'source_abort_index':ABORT_REF,
        'original_state':sources['closed_state'],'governance':ref(oldq/'ROOT-GOVERNANCE-RESULT-STATE.json'),
        'save_response':sources['SAVE10480_response'],
        'saved_semantic_response':ref(T/'p37-responses/10479-1-result.json')}
    memory={}
    def add(path,value):
        raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
        item={'path':str(path),'bytes':len(raw),'sha256':p.sha(raw)}
        memory[str(path)]=(item,value);return item
    closeref=add(p.REPO/'_runtime/C23-RAM-ONLY-final-driver-close.json',close)
    admission['cold_prelaunch']=add(p.REPO/'_runtime/C23-RAM-ONLY-prelaunch.json',{'final_driver_close':closeref})
    def checked(item,limit=262144):
        if item['path'] in memory:
            expected,value=memory[item['path']]
            if item!=expected or item['bytes']>limit:raise ValueError('RAM fixture envelope differs')
            return copy.deepcopy(value)
        return p.read_document(item,limit)
    docs=[checked(admission[k]) for k in ('original_state','save_response','saved_semantic_response','governance')]
    return admission,close,docs,checked,memory


class C23Cross(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph,cls.report=p._compose_source_graph(full_timing=True)

    def test_01_current_Source23_true_graph_and_preserved_Queue_algorithms(self):
        binding=p.source23_binding({'path':str(p.ANCHOR),'bytes':7206,'sha256':p.ANCHOR_SHA})
        self.assertEqual((binding['commit'],binding['complete_file_count'],binding['rows_sha256']),
            (p.COMMIT,1456,p.ROWS_SHA))
        self.assertFalse(binding['actual_filesystem_epoch_authority'])
        p.assert_true_graph(self.graph)
        self.assertLess(sum(map(len,self.graph.values())),2621440)
        canonical=p.load_tool('prepare_canonical_c17_outer_sources_v1.py')
        current=p.load_tool('prepare_c22_normal_warm_controls_v1.py')
        before,_=current._source_graph_v1()
        original=canonical.prior.prior.port(before['root_p37c22_sdk_queue.py'].decode(),p.MAP22)
        actual=self.graph['root_p37c23_sdk_queue.py'].decode()
        # Timing adds scalar observations only. Remove precisely those nodes,
        # then compare the real original service call and complete FULL logic.
        call=class_method(actual,'FreshQueue','call');oldcall=class_method(original,'FreshQueue','call')
        class RemoveScalarObservation(ast.NodeTransformer):
            def visit_Expr(self,node):
                if (isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name)
                    and node.value.func.id=='_record_full_rpc_row_v1'):return None
                return self.generic_visit(node)
        call=RemoveScalarObservation().visit(call)
        self.assertEqual(ast.dump(call,include_attributes=False),ast.dump(oldcall,include_attributes=False))
        full=class_method(actual,'FreshQueue','full_loop');oldfull=class_method(original,'FreshQueue','full_loop')
        full.decorator_list=[n for n in full.decorator_list if not (isinstance(n,ast.Call)
            and isinstance(n.func,ast.Name) and n.func.id=='_full_rows_v1')]
        class RemoveReceiptScalars(ast.NodeTransformer):
            def visit_Expr(self,node):
                x=node.value
                if (isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='update'
                    and isinstance(x.func.value,ast.Name) and x.func.value.id=='result'
                    and len(x.args)==1 and isinstance(x.args[0],ast.Call)
                    and isinstance(x.args[0].func,ast.Name) and x.args[0].func.id=='_current_full_row_fields_v1'):return None
                return self.generic_visit(node)
        full=RemoveReceiptScalars().visit(full)
        self.assertEqual(ast.dump(full,include_attributes=False),ast.dump(oldfull,include_attributes=False))
        for name in ('root_p37c23_sdk_queue.py','root_p37c23_mcp_entry.py','root_native30_supervisor_c23.py'):
            for node in ast.walk(ast.parse(self.graph[name])):
                if isinstance(node,ast.ImportFrom) and node.module:
                    self.assertFalse(any(s in node.module for s in ('c16','c17','c22','6397')))
        bad=dict(self.graph)
        bad['root_native30_supervisor_c23.py']=bad['root_native30_supervisor_c23.py'].replace(b'prepare_supervisor(N, enabled=True)',b'prepare_supervisor(N, enabled=False)')
        with self.assertRaises(ValueError):p.assert_true_graph(bad)
        self.assertIn('admission_getter=lambda queue: None',actual)
        self.assertIn("driver_state_restore_kind') == 'cold_checkpoint'",self.graph['root_p37c23_cold_resume.py'].decode())
        self.assertIn("if flag != '--private-active-scheme-sway-completion-execution-query'",self.graph['root_p37c23_cold_resume.py'].decode())
        timing=p.load_tool('prepare_full_batch_timing_sources_v1.py')
        feeder_path=timing.T/timing.FEEDER
        frozen=ref(feeder_path,131072)
        self.assertEqual(frozen['sha256'],timing.FEEDER_SHA)
        # This old immutable input is a timing algorithm fixture only. No C17
        # or warm admission becomes a C23 cold admission by this transformation.
        candidate,fields=p.transform_cold_feeder_source(feeder_path.read_bytes(),source_ref=frozen)
        self.assertTrue(fields['FULL_lifecycle_enabled']);self.assertIsNone(fields['following_or_restart_origin'])
        self.assertFalse(fields['startup_admitted']);self.assertFalse(fields['actual_five_refs_bound'])
        self.assertIn(b'.before_publish(sequence)',candidate)
        self.assertIn(b'.after_receipt(sequence)',candidate)

    def test_02_explicit_WAL_policy_actual_Queue_Stdio_and_revoke_join(self):
        outer=self.graph['root_c23_canonical_outer.py'].decode()
        tree=ast.parse(outer);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='OuterBindingV1')
        selected=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('child_env','revoke','close')]
        scope={'require':p.require}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='ActualOuterMethods',bases=[],keywords=[],body=selected,decorator_list=[])],type_ignores=[])),'actual-C23-outer-methods','exec'),scope)
        C=scope['ActualOuterMethods']
        # The exact Queue WAL AST executes, followed by its actual stdio model
        # environment. No subprocess, stream or SDK constructor is invoked.
        queue=ast.parse(self.graph['root_p37c23_sdk_queue.py'])
        main=fn(self.graph['root_p37c23_sdk_queue.py'],'main')
        wal_index=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='wal_value' for t in n.targets))
        nodes=main.body[wal_index:wal_index+2]
        self.assertIsInstance(nodes[1],ast.If)
        walcode=compile(ast.Module(body=nodes,type_ignores=[]),'actual-C23-Queue-WAL','exec')
        sys.path.insert(0,str(p.REPO/'tools/.venv/Lib/site-packages'))
        from mcp import StdioServerParameters
        for enabled in (False,True):
            with self.subTest(policy=enabled):
                obj=C();obj.wal_enabled=enabled;obj.dependency_root=Path('Z:/RAM-ONLY-frozen-dependencies')
                owner_env=obj.child_env({'XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1':'untrusted-existing-value'})
                child={};s={'os':types.SimpleNamespace(environ=owner_env),'child_env':child}
                exec(walcode,s)
                params=StdioServerParameters(command='RAM-ONLY-direct-base-python',args=['-B','-S','RAM-ONLY-entry.py'],env=child)
                app_env=obj.child_env(params.env)
                self.assertEqual(app_env.get('XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1'),'1' if enabled else None)
                self.assertEqual(set(child),{'XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1'} if enabled else set())
        init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
        pos=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Attribute) and t.attr=='wal_enabled' for t in n.targets))
        policycode=compile(ast.Module(body=init.body[pos:pos+2],type_ignores=[]),'actual-policy-strictbool','exec')
        with self.assertRaises(ValueError):exec(policycode,{'self':types.SimpleNamespace(policy={'enable_driver_state_wal_v1':'1'}),'require':p.require})
        events=[]
        origin=types.SimpleNamespace(revoke_before_close=lambda:events.append('revoke'))
        thread=types.SimpleNamespace(join=lambda timeout:events.append(('join',timeout)),is_alive=lambda:False)
        obj=C();obj.factory=types.SimpleNamespace(origin=origin,close=lambda:events.append('factory.close'))
        obj.server_thread=thread;obj.revoked=False;obj.plan=None;obj.result=None
        obj.close();self.assertEqual(events,['revoke',('join',10),'factory.close'])
        obj.revoked=False;thread.is_alive=lambda:True;events.clear()
        with self.assertRaises(ValueError):obj.close()
        self.assertNotIn('factory.close',events)

    def test_03_exact_F99_saved_frontier_and_unknown_new_identities(self):
        admission,close,docs,checked,memory=actual_frontier_fixture()
        original,save,semantic,gov=docs
        self.assertEqual(finite.validate_source_abort_closure(close,checked)['next_sequence'],10481)
        self.assertTrue(finite.validate_saved_seed(admission,copy.deepcopy(original),original,save,semantic,gov,checked=checked))
        for key,bad in (('old_sdk_closure_kind','EXACT_C15_INTERRUPTED_F90'),('old_Game',{'pid':115472,'creation_filetime':134368811928524228})):
            changed=copy.deepcopy(close);changed[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):finite.validate_source_abort_closure(changed,checked)
        changed=copy.deepcopy(original);changed['counts']['checkpoint_saved']+=1
        with self.assertRaises(ValueError):finite.validate_saved_seed(admission,changed,original,save,semantic,gov,checked=checked)
        with self.assertRaises((KeyError,ValueError)):finite.current_recording_inputs_v1(admission,checked)
        # New identities are deliberate RAM fixtures. They do not run the real
        # live verify_segment and cannot authorize Task/Game/recording adoption.
        sid='22222222-3333-4444-8555-666666666666';root=T/'recordings'/sid
        game={'pid':777777,'creation_filetime':134369300000000001,'creation_date':'RAM-FIXTURE'}
        def add(path,value):
            raw=json.dumps(value,sort_keys=True).encode();r={'path':str(path),'bytes':len(raw),'sha256':p.sha(raw)}
            memory[str(path)]=(r,value);return r
        pub=add(T/'RAM-ONLY-new-publisher/STARTED.json',{'RAM_FIXTURE':True})
        request=add(root/'requested.json',{'session_id':sid,'receipt_root':str(root),'worker_pid':888888,'worker_creation_filetime':134369300000000002})
        job=add(root/'job.json',{'session_id':sid,'receipt_root':str(root),'pid':game['pid'],
            'game_creation_filetime':game['creation_filetime'],'decision_text_publisher_receipt':pub})
        started=add(root/'started.json',{'state':'recording','game_pid':game['pid'],'game_creation_filetime':game['creation_filetime']})
        first=add(T/'ROOT-SAVED-MAP-RECORDING-ADMITTED-C23-RAM-FIXTURE.json',{'status':'GREEN','machine_id':p.MACHINE,
            'game_pid':game['pid'],'game_creation_filetime':game['creation_filetime'],'recorder_session_id':sid,
            'recording_job_root':str(root),'publisher_started':pub})
        binding=add(T/'C23-RAM-ONLY-recording-binding.json',{'schema':'xar.C23-actual-cold-recording-binding/v1',
            'machine_id':p.MACHINE,'status':'ACTUAL_NEW_RECORDING_READY','Game_pid':game['pid'],
            'Game_creation_filetime':game['creation_filetime'],'session_id':sid,
            'request':request,'job':job,'started':started,'first_frame_admission':first,'publisher_started':pub})
        new={**admission,'new_Game':game,'recording_binding':binding,'queue_source':{'path':str(T/'root_p37c23_sdk_queue.py')}}
        self.assertEqual(finite.current_recording_inputs_v1(new,checked)['root'],root)
        new['new_Game']=finite.OLD_GAME
        with self.assertRaises(ValueError):finite.current_recording_inputs_v1(new,checked)
        with self.assertRaises(ValueError):p.build_sources(native_transition_inputs=None,business_anchor_ref={'path':str(p.ANCHOR),'bytes':7206,'sha256':p.ANCHOR_SHA},frontier_ref=ABORT_REF)

    def test_04_Source24_parameter_cross_full_rows_and_runtime_guard(self):
        # Root authorized one additional metadata cross after selecting the
        # camera SDK successor. These synthetic rows/anchor are not Source24
        # actual Git/export or loaded authority, and are never written.
        files=[{'relative':f'RAM-FIXTURE/{i}.py','bytes':41000,'sha256':'b'*64,
            'git_blob_sha1':'c'*40,'git_mode':'100644'} for i in range(1456)]
        raw=json.dumps(files,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        anchor={'schema':'xar.source24.canonical-git-anchor/v1','machine_id':p.MACHINE,
            'status':'CANONICAL_REF_CREATED_NOT_DEPLOYED','execution_owner':'Root','root_direct_execution_release':True,
            'parent':p.COMMIT,'commit':'a'*40,'tree':'d'*40,'source_file_count':1456,
            'source_bytes':sum(r['bytes'] for r in files),'complete_rows_JSON':{'bytes':len(raw),'sha256':p.sha(raw)},
            'actual_loaded_provider':False,'Native30_bound':False}
        planref={'path':str(p.REPO/'_runtime/Source24-RAM-ONLY-plan.json'),'bytes':2,'sha256':p.sha(b'{}')}
        anchor['source_plan']=planref
        encoded=json.dumps(anchor,sort_keys=True).encode()
        aref={'path':str(p.REPO/'_runtime/Source24-RAM-ONLY-anchor.json'),'bytes':len(encoded),'sha256':p.sha(encoded)}
        def checked(item,limit=262144):
            if item==aref:return copy.deepcopy(anchor)
            if item==planref:return {}
            raise ValueError('unknown RAM-only Source24 reference')
        admission={'business_anchor':aref,'business_source_commit':anchor['commit']}
        freeze={'machine_id':p.MACHINE,'business_source_commit':anchor['commit'],
            'source_file_count':len(files),'source_bytes':anchor['source_bytes'],'files':files}
        self.assertEqual(finite.validate_frozen_business(admission,freeze,checked)['commit'],anchor['commit'])
        with patch.object(p,'read_document',checked):
            self.assertEqual(p.business_binding(aref)['parent'],p.COMMIT)
            with self.assertRaises(ValueError):p.build_sources(native_transition_inputs=None,business_anchor_ref=aref,frontier_ref=ABORT_REF)
        changed=copy.deepcopy(freeze);changed['files'][0]['sha256']='e'*64
        with self.assertRaises(ValueError):finite.validate_frozen_business(admission,changed,checked)
        changed=copy.deepcopy(anchor);changed['parent']='0'*40
        with self.assertRaises(ValueError):finite.validate_business_anchor(changed)
        cold=self.graph['root_p37c23_cold_resume.py'].decode()
        self.assertIn('validate_frozen_business(admission, freeze, checked)',cold)
        self.assertNotIn("admission['business_source_commit'] == '330d6e",cold)


    def test_05_local_import_closure_and_explicit_legacy_refusal(self):
        import asyncio,io
        graph=self.graph;closure=p.local_import_closure(graph)
        self.assertEqual(len(closure['external_source_pins']),23)
        self.assertEqual(len(closure['legacy_missing']),5)
        owner=graph['launch_sdk_p37c23_owner.py'].decode()
        self.assertEqual(owner.count('from root_native30_supervisor_c23 import validate_sdk_process_pair'),1)
        self.assertNotIn('root_native29_supervisor_c23',owner)
        bad=dict(graph);bad['root_p37c23_mcp_entry.py']+=b'\nfrom root_missing_alias import unsafe\n'
        with self.assertRaises(ValueError):p.local_import_closure(bad)
        cold=ast.parse(graph['root_p37c23_cold_resume.py'])
        for name in p.LEGACY_DENIED:
            node=next(n for n in ast.walk(cold) if isinstance(n,ast.AsyncFunctionDef) and n.name==name)
            scope={};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-cold-denial','exec'),scope)
            with self.assertRaises(ValueError):asyncio.run(scope[name](object(),None,{}))
        # Actual generated guard, RAM file facade only: a missing/wrong external
        # source pin cannot be replaced by an alias or entry-list membership.
        raw=b'RAM-only source';digest=p.sha(raw)
        class MemoryPath:
            def __init__(self,value):self.value=str(value)
            def __truediv__(self,name):return MemoryPath(self.value+'/'+name)
            def resolve(self,strict=True):return self
            def __str__(self):return self.value
            def __eq__(self,other):return isinstance(other,MemoryPath) and str(self)==str(other)
            def open(self,mode):return io.BytesIO(raw)
        scope={'Path':MemoryPath,'hashlib':hashlib,'sys':types.SimpleNamespace(modules={}), 'require':p.require}
        exec(p.external_import_guard_source(),scope)
        scope['_C23_EXTERNAL_IMPORT_PINS']={'root_memory':(len(raw),digest)}
        policy={'external_import_source_pins':{'root_memory':{'path':'RAM/root_memory.py','bytes':len(raw),'sha256':digest}},
            'entry_source_pins':[['RAM/root_memory.py',digest]]}
        scope['_check_c23_external_imports'](MemoryPath('RAM'),policy)
        policy['external_import_source_pins']['root_memory']['sha256']='0'*64
        with self.assertRaises(ValueError):scope['_check_c23_external_imports'](MemoryPath('RAM'),policy)
        with self.assertRaises(ValueError):scope['_check_c23_external_imports'](MemoryPath('RAM'),{})


if __name__=='__main__':unittest.main(verbosity=2)
