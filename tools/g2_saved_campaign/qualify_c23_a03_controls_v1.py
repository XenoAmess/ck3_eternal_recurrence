"""Focused A03 graph/attempt/phase/SPEC qualification, with no runtime writes."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(OWN))
import prepare_c23_a03_full_enabled_cold_controls_v1 as p
import prepare_adopt_c23_a03_v1 as adoption

N=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T=N/'robert30-v20261019-campaign01/runtime'
O=N/'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100'


def actual_ref(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path).resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def actual_attempt():
    return {'cold_attempt':{'attempt_id':'a03','nonce':'1'*32,'task_nonce':'2'*32,
        'execution_owner':'Root','root_direct_execution_release':True,
        'prior_failure_a01':actual_ref(O/'C23-FIRST-SUPERVISOR-LAUNCH-FAILED-CLOSED.json'),
        'prior_failure_a02':{
            'supervisor_closed':actual_ref(T/'ROOT-FRESH-SUPERVISOR-CLOSED-C23-A02.json'),
            'Task_closed':actual_ref(O/'tasks/spec-supervisor-a02/CLOSED.json'),
            'Task_unregistered':actual_ref(O/'SUPERVISOR-A02-CLOSED-UNREGISTERED.json'),
            'kernel':actual_ref(O/'POST-A02-FAILED-LAUNCH-CK3-KERNEL.json')}}}


def method(raw,cls,name):
    tree=ast.parse(raw);node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
    return next(n for n in node.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)


def dump(node):return ast.dump(node,include_attributes=False)


class A03Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph,cls.report=p._compose_source_graph(full_timing=True)
        cls.old,cls.old_report=p.predecessor()._compose_source_graph(full_timing=True)

    def test_01_complete_graph_original_algorithms_and_new_helper(self):
        self.assertEqual(len(self.graph),len(self.old))
        p.predecessor().assert_true_graph(self.graph)
        closure=p.predecessor().local_import_closure(self.graph)
        self.assertEqual(len(closure['external_source_pins']),23)
        self.assertEqual(self.report['retained_WAL_hunk_bytes'],313)
        self.assertTrue(self.report['WAL_explicit_child_policy']['enable_driver_state_wal_v1'])
        self.assertNotIn(p.OLD_HELPER,self.graph)
        self.assertEqual(self.graph[p.HELPER],p.helper_source())
        self.assertNotEqual(p.sha(self.graph[p.HELPER]),p.predecessor().HELPER_SHA)
        for name in ('call','full_loop'):
            cls='FreshQueue'
            # Namespace and metadata changes are outside these business algorithms.
            self.assertEqual(dump(method(self.graph['root_p37c23_sdk_queue.py'],cls,name)),
                dump(method(self.old['root_p37c23_sdk_queue.py'],cls,name)))
        for name,data in self.graph.items():
            compile(data,name,'exec')
            self.assertNotIn(b'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json',data)
            for old in p.METADATA:self.assertNotIn(old.encode(),data)
        sup=self.graph['root_native30_supervisor_c23.py']
        for stem in p.ATTEMPT_NAMES:self.assertIn((stem+'-A03.').encode(),sup)
        self.assertIn(b'ROOT-ACTUAL-GAME-LAUNCH-C23.json',sup)
        self.assertIn(b'known_preload_phase(canonical)',sup)
        self.assertIn(b'old C23 stop/exit marker present; a03 cannot clear or reuse it',sup)

    def test_02_exact_actual_two_failed_predecessors_and_independent_nonce(self):
        value=actual_attempt();args=argparse.Namespace(attempt='a03',attempt_nonce='1'*32,task_nonce='2'*32)
        self.assertEqual(p.validate_attempt(args,value,adoption.checked),value['cold_attempt'])
        for key,bad in [('attempt_id','a02'),('execution_owner','foreign'),
                ('root_direct_execution_release',False),('task_nonce','1'*32)]:
            changed=copy.deepcopy(value);changed['cold_attempt'][key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):
                p.validate_attempt(args,changed,adoption.checked)
        for key in p.A02:
            changed=copy.deepcopy(value);changed['cold_attempt']['prior_failure_a02'][key]['sha256']='0'*64
            with self.subTest(source=key),self.assertRaises(ValueError):
                p.validate_attempt(args,changed,adoption.checked)
        changed=copy.deepcopy(value);old='f6995c1cb9b74721b8e834ef8096e423'
        changed['cold_attempt']['nonce']=old
        with self.assertRaises(ValueError):
            p.validate_attempt(argparse.Namespace(attempt='a03',attempt_nonce=old,task_nonce='2'*32),
                changed,adoption.checked)

    def test_03_known_phase_projection_uses_no_OS_and_preserves_unknown(self):
        no_os=types.SimpleNamespace(observe_process=lambda *a:(_ for _ in ()).throw(AssertionError('OS read')),
            observe_modules=lambda *a:(_ for _ in ()).throw(AssertionError('module query')))
        canonical=types.SimpleNamespace(factory=types.SimpleNamespace(facade=no_os))
        missing=p.known_preload_phase(canonical)
        self.assertEqual(missing['before'],{'pid':'unknown','creation_filetime':'unknown'})
        self.assertEqual(missing['after'],{'pid':'unknown','creation_filetime':'unknown'})
        self.assertFalse(missing['additional_OS_reads'])
        phase={'stage':'preload_mem_image','status':'unavailable',
            'before':{'pid':198888,'creation_filetime':134369342403215399,'executable':'not copied'},
            'error':'RAM phase example'}
        no_os._preload_mapping_phase_v1=phase
        projected=p.known_preload_phase(canonical)
        self.assertEqual(projected['before'],{'pid':198888,'creation_filetime':134369342403215399})
        self.assertEqual(projected['after']['pid'],'unknown')
        self.assertEqual(projected['error'],'RAM phase example')
        self.assertNotIn('executable',projected['before'])
        self.assertEqual(phase['before']['executable'],'not copied')
        no_os._preload_mapping_phase_v1={'before':{'pid':True,'creation_filetime':-1}}
        self.assertEqual(p.known_preload_phase(canonical)['before'],missing['before'])

    def test_04_source25_only_anchor_and_unchanged_saved_frontier_functions(self):
        scope={};exec(compile(p.helper_source(),p.HELPER,'exec'),scope)
        anchor={'schema':'xar.source25.canonical-git-anchor/v1','machine_id':p.MACHINE,
            'status':'CANONICAL_REF_CREATED_NOT_DEPLOYED','execution_owner':'Root',
            'root_direct_execution_release':True,'parent':p.PARENT,'commit':'a'*40,'tree':'b'*40,
            'source_file_count':1458,'source_bytes':59210000,
            'complete_rows_JSON':{'bytes':400000,'sha256':'c'*64},
            'actual_loaded_provider':False,'Native30_bound':False}
        self.assertEqual(scope['validate_business_anchor'](anchor),anchor)
        for key,bad in [('schema','xar.source24.canonical-git-anchor/v1'),('parent','0'*40),
                ('actual_loaded_provider',True)]:
            changed=copy.deepcopy(anchor);changed[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):scope['validate_business_anchor'](changed)
        old=ast.parse((OWN/'c23_source_abort_checkpoint_inputs_v1.py').read_bytes())
        new=ast.parse(p.helper_source())
        previous={n.name:n for n in old.body if isinstance(n,ast.FunctionDef)}
        current={n.name:n for n in new.body if isinstance(n,ast.FunctionDef)}
        for name in ('validate_source_abort_closure','validate_saved_seed','current_recording_inputs_v1','content_ref'):
            self.assertEqual(dump(current[name]),dump(previous[name]))

    def test_05_original_max8_and_16KiB_limits_without_materialization(self):
        chain=(OWN/'canonical_native_provider_chain_v1.py').read_bytes();tree=ast.parse(chain)
        wanted={'_verified_entry_sources','consume_private_bootstrap_args_v1'}
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
        memory={str(T/name):data for name,data in self.graph.items()}
        class MemoryPath:
            def __init__(self,value):self.value=str(value)
            def is_absolute(self):return True
            def resolve(self,strict=True):
                if self.value not in memory:raise FileNotFoundError(self.value)
                return self
            def open(self,mode):
                import io
                return io.BytesIO(memory[self.value])
            def __str__(self):return self.value
        contract=types.SimpleNamespace(_require=p.require,_sha=lambda v:isinstance(v,str) and len(v)==64)
        scope={'Path':MemoryPath,'hashlib':hashlib,'contract':contract,'json':json}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'original-entry-and-private-limits','exec'),scope)
        six=[[str(T/name),p.sha(self.graph[name])] for name in sorted(p.SIX)]
        self.assertEqual(len(scope['_verified_entry_sources'](six)),6)
        for bad in (six+six[:3],[],[[path,'0'*64] for path,digest in six]):
            with self.assertRaises(ValueError):scope['_verified_entry_sources'](bad)
        consume=scope['consume_private_bootstrap_args_v1']
        self.assertEqual(consume(['python','--xar-private-preload','{}'],enabled=True),
            (['python'],{}))
        with self.assertRaises(ValueError):consume(['python','--xar-private-preload','x'*16385],enabled=True)
        self.assertEqual(consume(['python','--xar-private-preload','{}'],enabled=False),
            (['python','--xar-private-preload','{}'],None))

    def test_06_original_SPEC_RAM_adapter_preserves_owner_contract(self):
        path=OWN/'interactive_task_owner_v1.py'
        spec=importlib.util.spec_from_file_location('_a03_qualify_original_owner',path)
        owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
        original_windows=owner.Windows
        class Windows:
            def current(self):
                return {'loaded_module':sys.executable,'sid':'S-1-5-21-RAM','session':1}
            def file_id(self,path):return {'volume_serial':'RAM','file_id':'RAM'}
        owner.Windows=Windows
        try:
            value=adoption._ram_spec(owner,root=O/'tasks/RAM-ONLY-spec-supervisor-a03',
                stage=T/'root_native30_supervisor_c23.py',
                stage_raw=self.graph['root_native30_supervisor_c23.py'],
                bootstrap=T/'interactive_task_owner_c17.py',cwd=T,
                screen=T/'ROOT-SCREEN-ADMITTED-C23-A03.json',
                clean=T/'ROOT-CLEAN-SOURCE-FROZEN-C23-A03.json',
                config=T/'ROOT-LAUNCH-CONFIG-C23-A03.json',attempt='1'*32,task='2'*32,
                dependency_root=OWN.parent/'.venv/Lib/site-packages')
        finally:owner.Windows=original_windows
        self.assertEqual(value['nonce'],'2'*32)
        self.assertEqual(value['task_name'],'XARG2ManagedOwner-'+('2'*32))
        self.assertEqual(value['stage_sha256'],p.sha(self.graph['root_native30_supervisor_c23.py']))
        self.assertEqual(value['env'],{'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(OWN.parent/'.venv/Lib/site-packages')})
        self.assertEqual(value['stage_args'][-4:],['--attempt-nonce','1'*32,'--task-nonce','2'*32])
        self.assertFalse((O/'tasks/RAM-ONLY-spec-supervisor-a03').exists())

    def test_07_prepare_compose_real_A02_values_with_future_RAM_envelopes(self):
        # Future anchor/full/BASE are deliberately RAM fixtures. Actual A02
        # sources/metadata, new graph, feeder, and original SPEC algorithm are
        # consumed; no fixture is written or presented as runtime authority.
        def memory_ref(name,value):
            data=adoption.enc(value)
            return {'path':str(O/('RAM-ONLY-'+name+'.json')),'bytes':len(data),'sha256':p.sha(data)}
        oldfreeze=json.loads((T/'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json').read_bytes())
        base=copy.deepcopy(oldfreeze);base.pop('canonical_preload_policy')
        base.update(source_root=str(N/'sdk-v20261019-candidate/src20'),business_source_commit='a'*40)
        full={'machine_id':p.MACHINE,'review_at_utc':'2026-10-20T06:30:00+00:00',
            'approved_output_roots':[str(T),str(O)],'retained_other_reservations':1,
            'disk_reserve_bytes':1,'effective_project_quota':999999999999}
        fullref=memory_ref('full',full);baseref=memory_ref('base',base)
        business={'commit':'a'*40,'complete_file_count':base['source_file_count'],
            'complete_source_bytes':base['source_bytes']}
        prior=actual_attempt()['cold_attempt']
        plan={'schema':'xar.C23-A03-prepare-plan/v1','machine_id':p.MACHINE,
            'execution_owner':'Root','root_direct_execution_release':True,
            'observed_at_utc':'2026-10-20T05:00:00+00:00','attempt_nonce':'1'*32,'task_nonce':'2'*32,
            'runtime_root':str(T),'output_root':str(O),'task_root':str(O/'tasks/spec-supervisor-a03'),
            'compact_base_ref':baseref,'business_anchor_ref':memory_ref('anchor',{}),
            'full_storage_ref':fullref,'live_storage_ref':fullref,
            'closed_consumers_ref':memory_ref('closure',{}),'native_transition_inputs':{},'frontier_ref':{},
            'feeder_producer_ref':actual_ref(OWN/'prepare_c23_a03_feeder_v1.py'),
            'native_renderer_ref':memory_ref('native-renderer',{}),
            'bootstrap_ref':actual_ref(T/'interactive_task_owner_c17.py'),
            'screen_admission_ref':memory_ref('screen',{}),
            'prior_failure_a01':prior['prior_failure_a01'],'prior_failure_a02':prior['prior_failure_a02']}
        planref=memory_ref('plan',plan)
        memory={planref['path']:plan,baseref['path']:base,fullref['path']:full}
        original_checked=adoption.checked;original_load=adoption.load
        def checked(item,cap=adoption.MAX):
            if item['path'] in memory:return copy.deepcopy(memory[item['path']])
            return original_checked(item,cap)
        class Windows:
            def current(self):return {'loaded_module':sys.executable,'sid':'S-1-5-21-RAM','session':1}
            def file_id(self,path):return {'volume_serial':'RAM','file_id':'RAM'}
        def load(item,name):
            if name=='_a03_native_renderer':
                native=json.loads((T/'ROOT-NATIVE30-NATIVE-PIN-C23.json').read_bytes())
                native['storage_admission']=fullref
                return types.SimpleNamespace(compose_native_session_v1=lambda **kw:(adoption.enc(native),{}))
            module=original_load(item,name)
            if name=='_a03_original_owner_source':module.Windows=Windows
            return module
        with patch.object(adoption,'checked',checked),patch.object(adoption,'load',load),\
                patch.object(adoption,'_actual_closure',lambda plan:None),\
                patch.object(adoption,'_full',lambda plan:copy.deepcopy(full)),\
                patch.object(p,'business_binding',lambda ref:copy.deepcopy(business)),\
                patch.object(p,'build_sources',lambda **kw:(dict(self.graph),dict(self.report))):
            changes,outputs,quote=adoption.compose(planref)
        final_path=T/'ROOT-FINAL-SDK-FREEZE-P37C23-A03.json'
        final=json.loads(outputs[final_path]);policy_path=T/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A03.json'
        self.assertEqual(final,{**base,'canonical_preload_policy':adoption.target_ref(policy_path,outputs[policy_path])})
        policy=json.loads(outputs[policy_path])
        self.assertEqual((len(policy['entry_source_pins']),len(policy['canonical_entry_source_pins'])),(44,6))
        self.assertIn(str(T/p.HELPER),[path for path,digest in policy['entry_source_pins']])
        self.assertNotIn(str(T/p.OLD_HELPER),[path for path,digest in policy['entry_source_pins']])
        self.assertEqual(len(changes),10)
        self.assertEqual(quote['new_source_logical'],440134)
        self.assertLessEqual(quote['runtime_prepare_peak_upper'],2097152)
        spec=json.loads(outputs[O/'tasks/spec-supervisor-a03/SPEC.json'])
        self.assertEqual(spec['env']['PYTHONPATH'],policy['dependency_root'])
        self.assertFalse(final_path.exists())
        self.assertFalse((O/'tasks/spec-supervisor-a03').exists())


if __name__=='__main__':unittest.main(verbosity=2)

