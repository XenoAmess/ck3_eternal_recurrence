"""Pure isolated fixtures. No actual lease, bus, process, CK3 or native calls."""
from pathlib import Path
import ast
import copy
from typing import get_type_hints
from ck3_mod_acceptance_background_types import CONTROL_QUEUE_MODULE_ORDER_V1, FilePin
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

CANDIDATE = Path(__file__).resolve().parents[1]

def pin(path: Path) -> FilePin:
    raw=path.read_bytes()
    return FilePin(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def load(path: Path, name: str) -> types.ModuleType:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise ValueError('Fixture module loader unavailable')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class InprocessQueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='lyd-pure-queue-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve()
        self.helpers=self.root/'selected-tools';self.helpers.mkdir()
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            file=name+'.py'
            shutil.copyfile(CANDIDATE/'tools'/file,self.helpers/file)
        self.queue=self.helpers/'ck3_mod_acceptance_queue.py'
        files={str(path.resolve()):pin(path)for path in self.helpers.iterdir()}
        self.live=self.root/'live';self.live.mkdir()
        self.controls=self.live/'controls';self.controls.mkdir()
        self.keeper=self.root/'keeper';self.keeper.mkdir()
        self.state=self.root/'state';self.state.mkdir()
        self.source=self.root/'source';self.source.mkdir()
        self.frozen={'files':files,'run_id':'pure-fixture-run','state_dir':str(self.state),'source_root':str(self.source),
                     'argv':['python','host.py','--agent-source-root',str(self.source),'--bridge-pipe','pure-pipe','--control-plan-dir',str(self.controls)]}
        self.report={'state_dir':str(self.state),'agent_source_root':str(self.source),'pipe':'pure-pipe','phase':'hold',
                     'hold_until_utc_estimated':time.time()+1000,'steps':[],
                     'mcp_tools':{'tools':[{'name':'fixture_readonly_query','inputSchema':{'type':'object','properties':{},'additionalProperties':False}}]}}
        (self.live/'native-report.json').write_text(json.dumps(self.report),encoding='utf-8')
        self.client_module=load(CANDIDATE/'tools/ck3_mod_acceptance_client.py','pure_selected_case_client')
        self.bundle=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
        self.module=self.bundle['module']
        self.module.frozen_run=lambda *a,**k:(self.frozen,{'keeper_root':str(self.keeper)})
        self.lease_calls=[]
        def lease(*args,**kwargs):
            self.lease_calls.append((args,kwargs))
            return {'lease':{'task_id':'pure-task','sequence':1}}
        self.module.live_lease=lease
        self.client=self.client_module.CaseClient.__new__(self.client_module.CaseClient)
        self.client.selection=types.SimpleNamespace(locations={'python':Path(sys.executable),'repo_root':self.root},
            runtime_environment={},runtime={'control_queue':pin(self.queue)},runtime_path=self.root/'runtime.json')
        self.client.frozen=self.frozen;self.client.live=self.live
        self.client.output=self.root/'case-output';self.client.output.mkdir()
        self.client._queue_library=self.bundle
        self.client.guard=lambda *a,**k:self.report
        self.client.remaining=lambda:1000
        self.steps=[{'id':'pure-step','tool':'fixture_readonly_query','args':{},'fresh_revision':False}]
        self.rows=[{'id':'pure-step','ok':True,'finished_at':'fixture-only','result':{'fixture':True}}]
        self.await_calls=[]
        def await_steps(*args):self.await_calls.append(args);return self.rows
        self.client.await_steps=await_steps

    def test_01_complete_selected_modules_do_not_import_main_siblings(self):
        poisoned={name:types.ModuleType('poisoned_'+name)for name in CONTROL_QUEUE_MODULE_ORDER_V1}
        with patch.dict(sys.modules,poisoned):
            bundle=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
            self.assertIs(bundle['module'].live_lease,bundle['modules']['ck3_mod_acceptance_keeper'].live_lease)
            self.assertIs(bundle['module'].frozen_run,bundle['modules']['ck3_mod_acceptance_launcher'].frozen_run)
            for name,module in poisoned.items():self.assertIs(sys.modules[name],module)
        self.assertEqual(Path(bundle['module'].__file__),self.queue)
        modules=bundle['modules']
        self.assertIs(modules['ck3_mod_acceptance_steam_gate'].ProcessIdentity,
                      modules['steam_offline_state_contract'].ProcessIdentity)
        self.assertIs(modules['steam_offline_native_provider_v1'].ProcessIdentity,
                      modules['steam_offline_state_contract'].ProcessIdentity)
        self.assertIs(get_type_hints(modules['steam_offline_state_contract'].parse_result)['return'],
                      modules['steam_offline_state_contract'].ProbeResult)

    def test_02_cached_code_still_checks_exact_frozen_bytes(self):
        keeper=self.helpers/'ck3_mod_acceptance_keeper.py'
        keeper.write_bytes(keeper.read_bytes()+b'\n# fixture mutation\n')
        with self.assertRaisesRegex(ValueError,'bytes changed'):
            self.client_module.load_pinned_control_queue(self.queue,self.frozen,self.bundle)
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('no binding failure fallback')):
            with self.assertRaisesRegex(ValueError,'queue failed'):
                self.client.execute_plan(self.steps,'changed-sibling')
        ack=json.loads((self.client.output/'changed-sibling.stdout.log').read_bytes())
        self.assertEqual(ack['status'],'BLOCKED_NEVER_REPLAY')
        self.assertFalse(list(self.controls.iterdir()))

    def test_03_direct_ack_original_refs_rows_and_no_queue_subprocess(self):
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('queue subprocess forbidden in direct fixture')):
            rows=self.client.execute_plan(self.steps,'direct')
        self.assertIs(rows,self.rows)
        self.assertEqual(len(self.lease_calls),2)
        self.assertTrue(all('deadline'in kwargs for _,kwargs in self.lease_calls))
        ack=json.loads((self.client.output/'direct.stdout.log').read_bytes())
        self.assertEqual(ack['status'],'QUEUED_ONCE_ACK_NOT_BUSINESS_PASS')
        self.assertFalse(ack['business_pass'])
        self.assertEqual(ack['published'],pin(self.controls/'direct.json'))
        self.assertEqual(ack['plan'],pin(self.client.output/'plans/direct.json'))
        self.assertEqual((self.controls/'direct.json').read_bytes(),(self.client.output/'plans/direct.json').read_bytes())
        result=json.loads((self.client.output/'direct.queue-result.json').read_bytes())
        self.assertEqual(result['execution_mode'],'IN_PROCESS_PINNED_QUEUE_LIBRARY')
        self.assertFalse(result['argv_executed']);self.assertEqual(result['exit_code'],0)
        self.assertEqual(len(self.await_calls),1)

    def test_04_initial_lease_refusal_never_publishes_or_falls_back(self):
        count=[]
        def refused(*a,**k):count.append(1);raise RuntimeError('actual lease refused fixture')
        self.module.live_lease=refused
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('no failure fallback')):
            with self.assertRaisesRegex(ValueError,'queue failed'):
                self.client.execute_plan(self.steps,'refused')
        self.assertEqual(len(count),1);self.assertFalse(list(self.controls.iterdir()))
        self.assertFalse((self.live/'control-once-ledger').exists());self.assertFalse(self.await_calls)
        ack=json.loads((self.client.output/'refused.stdout.log').read_bytes())
        self.assertEqual(ack['status'],'BLOCKED_NEVER_REPLAY')

    def test_05_second_lease_refusal_preserves_claim_and_never_retries(self):
        count=[]
        def lease(*a,**k):
            count.append(1)
            if len(count)==2:raise RuntimeError('lease changed before publish fixture')
            return {'lease':{'sequence':1}}
        self.module.live_lease=lease
        with patch.object(self.client_module.subprocess,'run',side_effect=AssertionError('no failure fallback')):
            with self.assertRaisesRegex(ValueError,'queue failed'):
                self.client.execute_plan(self.steps,'second-refused')
            with self.assertRaises(FileExistsError):
                self.client.execute_plan(self.steps,'second-refused')
        self.assertEqual(len(count),2)
        self.assertFalse(list(self.controls.glob('*.json')))
        self.assertTrue(list((self.live/'control-once-ledger').glob('step-*.json')))
        self.assertFalse(self.await_calls)

    def test_06_legacy_selection_happens_before_submit_and_only_once(self):
        # Test a fresh once-only name for each legitimate eligibility mismatch.
        scenarios=('environment','python','old-api','legacy-error')
        for reason in scenarios:
            with self.subTest(reason=reason):
                old_python=self.client.selection.locations['python']
                old_environment=self.client.selection.runtime_environment
                original_deadline=self.module.enqueue_deadline
                if reason in ('environment','legacy-error'):
                    selected='selected-value'if os.environ.get('LYD_PURE_TEST_REQUIRED_ENV')!='selected-value'else'other-selected-value'
                    self.client.selection.runtime_environment={'LYD_PURE_TEST_REQUIRED_ENV':selected}
                elif reason=='python':self.client.selection.locations['python']=self.root/'different-python.exe'
                else:del self.module.enqueue_deadline
                try:
                    with patch.object(self.client_module.subprocess,'run',return_value=types.SimpleNamespace(returncode=2 if reason=='legacy-error'else 0))as called:
                        if reason=='legacy-error':
                            with self.assertRaisesRegex(ValueError,'queue failed'):self.client.execute_plan(self.steps,'legacy-'+reason)
                        else:self.client.execute_plan(self.steps,'legacy-'+reason)
                    self.assertEqual(called.call_count,1)
                    record=json.loads((self.client.output/('legacy-'+reason+'.queue-result.json')).read_bytes())
                    self.assertEqual(record['execution_mode'],'LEGACY_QUEUE_SUBPROCESS')
                    self.assertTrue(record['argv_executed']);self.assertTrue(record['legacy_reasons'])
                    self.assertEqual(called.call_args.kwargs['env'].get('LYD_PURE_TEST_REQUIRED_ENV'),
                                     os.environ.get('LYD_PURE_TEST_REQUIRED_ENV')if reason not in ('environment','legacy-error')else selected)
                finally:
                    self.client.selection.locations['python']=old_python
                    self.client.selection.runtime_environment=old_environment
                    self.module.enqueue_deadline=original_deadline
        self.assertFalse(self.lease_calls)

    def test_07_each_git_and_bus_process_gets_remaining_original_deadline(self):
        module=load(CANDIDATE/'promo/ck3_native_war_ai/integration/screen_bus_lease.py','pure_deadline_screen_lease')
        results=[types.SimpleNamespace(stdout='a'*40+'\n'),types.SimpleNamespace(stdout='')]
        with patch.object(module.time,'monotonic',side_effect=[100,102]),patch.object(module.subprocess,'run',side_effect=results)as calls:
            self.assertEqual(module.checkout_head(self.root,deadline=105),'a'*40)
        self.assertEqual([c.kwargs['timeout']for c in calls.call_args_list],[5,3])
        body=json.dumps({'schema':'codex.task_bus.v1','ok':True}).encode()
        with patch.object(module,'checked_cli_pair'),patch.object(module.time,'monotonic',return_value=103),patch.object(module.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=body,stderr=b''))as calls:
            self.assertTrue(module.call_bus(self.root/'source',self.root,'A'*64,'list',deadline=105)['ok'])
        self.assertEqual(calls.call_args.kwargs['timeout'],2)
        with patch.object(module,'checked_cli_pair'),patch.object(module.time,'monotonic',return_value=105),patch.object(module.subprocess,'run')as calls:
            with self.assertRaises(TimeoutError):module.call_bus(self.root/'source',self.root,'A'*64,'list',deadline=105)
        calls.assert_not_called()

    def test_08_expiry_after_final_cas_read_refuses_publication(self):
        plan=self.root/'late-plan.json';plan.write_text(json.dumps({'steps':self.steps}),encoding='utf-8')
        clock=[100];calls=[]
        def lease(*a,**k):
            calls.append(k)
            if len(calls)==2:clock[0]=150
            return {'lease':{'sequence':1}}
        self.module.live_lease=lease
        with patch.object(self.module.time,'monotonic',side_effect=lambda:clock[0]):
            with self.assertRaises(TimeoutError):self.module.enqueue(self.live,plan,'late.json',deadline=150)
        self.assertEqual(len(calls),2);self.assertFalse((self.controls/'late.json').exists())
        self.assertTrue(list((self.live/'control-once-ledger').glob('step-*.json')))

    def test_09_cli_default_and_optional_deadline_share_original_enqueue(self):
        for timeout,expected in ((None,None),('7',107)):
            argv=['--live',str(self.live),'--plan',str(self.root/'unused-plan'),'--name','cli.json']
            if timeout is not None:argv.extend(['--timeout-seconds',timeout])
            with patch.object(self.module,'enqueue',return_value={'fixture_only':True})as enqueue,patch.object(self.module.time,'monotonic',return_value=100),contextlib.redirect_stdout(io.StringIO())as output:
                self.assertEqual(self.module.main(argv),0)
            self.assertEqual(enqueue.call_args.kwargs['deadline'],expected)
            self.assertEqual(json.loads(output.getvalue()),{'fixture_only':True})

    def tearDown(self) -> None:
        # Release only this test's selected modules; public/importing peers stay.
        for name, module in tuple(sys.modules.items()):
            if not name.startswith('_selected_control_queue_') or not isinstance(module,types.ModuleType):
                continue
            location=getattr(module,'__file__',None)
            if isinstance(location,str) and Path(location).parent==self.helpers:
                if sys.modules.get(name) is module:
                    del sys.modules[name]

    def test_10_shared_closure_matches_actual_launcher_required_pins(self) -> None:
        raw=(CANDIDATE/'tools/ck3_mod_acceptance_launcher.py').read_text(encoding='utf-8-sig')
        function=next(node for node in ast.parse(raw).body
                      if isinstance(node,ast.FunctionDef) and node.name=='frozen_run')
        groups=[node.iter for node in ast.walk(function)
                if isinstance(node,ast.For) and isinstance(node.iter,ast.Name)
                and node.iter.id=='CONTROL_QUEUE_MODULE_ORDER_V1']
        self.assertEqual(len(groups),1)
        launcher=self.bundle['modules']['ck3_mod_acceptance_launcher']
        self.assertIs(launcher.frozen_run.__globals__['CONTROL_QUEUE_MODULE_ORDER_V1'],
                      launcher.CONTROL_QUEUE_MODULE_ORDER_V1)
        self.assertEqual(launcher.CONTROL_QUEUE_MODULE_ORDER_V1,CONTROL_QUEUE_MODULE_ORDER_V1)
        filenames=[name+'.py' for name in launcher.CONTROL_QUEUE_MODULE_ORDER_V1]
        self.assertEqual(len(CONTROL_QUEUE_MODULE_ORDER_V1),len(set(CONTROL_QUEUE_MODULE_ORDER_V1)))
        self.assertEqual(set(filenames),{name+'.py' for name in CONTROL_QUEUE_MODULE_ORDER_V1})
        self.assertEqual(set(self.bundle['modules']),set(CONTROL_QUEUE_MODULE_ORDER_V1))

    def test_11_each_helper_requires_present_exact_runtime_pin(self) -> None:
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            key=str(self.helpers/(name+'.py'))
            for mode in ('missing','boolean_bytes','float_bytes','wrong_sha'):
                with self.subTest(module=name,mode=mode):
                    frozen=copy.deepcopy(self.frozen)
                    if mode=='missing':
                        del frozen['files'][key]
                    elif mode=='boolean_bytes':
                        frozen['files'][key]['bytes']=True
                    elif mode=='float_bytes':
                        frozen['files'][key]['bytes']=float(frozen['files'][key]['bytes'])
                    else:
                        frozen['files'][key]['sha256']='0'*64
                    with self.assertRaises(ValueError):
                        self.client_module.load_pinned_control_queue(self.queue,frozen,self.bundle)

    def test_12_changed_transitive_closure_never_executes_or_reuses_cache(self) -> None:
        source=self.helpers/'steam_offline_native_profiles.py'
        source.write_bytes(source.read_bytes()+b'\nraise AssertionError("new closure must not execute")\n')
        frozen=copy.deepcopy(self.frozen)
        frozen['files'][str(source)]=pin(source)
        before={name:sys.modules[name] for name in
                (module.__name__ for module in self.bundle['modules'].values())}
        with self.assertRaisesRegex(ValueError,'closure changed'):
            self.client_module.load_pinned_control_queue(self.queue,frozen,self.bundle)
        for name,module in before.items():
            self.assertIs(sys.modules[name],module)

    def test_13_unknown_sibling_import_rolls_back_only_owned_registry(self) -> None:
        original=self.queue.read_bytes()
        retained_name='_selected_control_queue_unrelated_retained_fixture'
        retained=types.ModuleType(retained_name)
        for foreign in ('ck3_mod_acceptance_unpinned_fixture','steam_offline_unpinned_fixture'):
            with self.subTest(module=foreign):
                self.queue.write_bytes(original+('\nimport '+foreign+'\n').encode())
                frozen=copy.deepcopy(self.frozen)
                frozen['files'][str(self.queue)]=pin(self.queue)
                poisoned={name:types.ModuleType('poisoned_'+name)
                          for name in (*CONTROL_QUEUE_MODULE_ORDER_V1,foreign)}
                poisoned[retained_name]=retained
                with patch.dict(sys.modules,poisoned):
                    before={name:module for name,module in sys.modules.items()
                            if name.startswith('_selected_control_queue_')}
                    with self.assertRaisesRegex(ImportError,'Unpinned selected queue sibling import'):
                        self.client_module.load_pinned_control_queue(self.queue,frozen)
                    after={name:module for name,module in sys.modules.items()
                           if name.startswith('_selected_control_queue_')}
                    self.assertEqual(before,after)
                    for name,module in poisoned.items():
                        self.assertIs(sys.modules[name],module)

    def test_14_identical_closure_has_independent_private_module_instances(self) -> None:
        second=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
        closure=hashlib.sha256(json.dumps(self.bundle['refs'],sort_keys=True,
                              separators=(',',':')).encode('utf-8')).hexdigest()
        self.assertEqual(self.bundle['refs'],second['refs'])
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            original,rebound=self.bundle['modules'][name],second['modules'][name]
            self.assertIsNot(original,rebound)
            self.assertNotEqual(original.__name__,rebound.__name__)
            self.assertIn(closure,original.__name__)
            self.assertIn(closure,rebound.__name__)
            self.assertIs(sys.modules[original.__name__],original)
            self.assertIs(sys.modules[rebound.__name__],rebound)
        second['module'].fixture_mutable_state=['second only']
        self.assertFalse(hasattr(self.bundle['module'],'fixture_mutable_state'))
        self.assertIs(self.client_module.load_pinned_control_queue(
            self.queue,self.frozen,self.bundle),self.bundle)

    def test_15_namespace_collision_preserves_previous_binding(self) -> None:
        import secrets
        with patch.object(secrets,'token_hex',return_value='f'*32):
            first=self.client_module.load_pinned_control_queue(self.queue,self.frozen)
            before={module.__name__:module for module in first['modules'].values()}
            with self.assertRaisesRegex(ValueError,'namespace collision'):
                self.client_module.load_pinned_control_queue(self.queue,self.frozen)
            for name,module in before.items():
                self.assertIs(sys.modules[name],module)

    def test_16_base_exception_rolls_back_all_new_private_modules(self) -> None:
        self.queue.write_bytes(self.queue.read_bytes()+b'\nraise SystemExit("synthetic module refusal")\n')
        frozen=copy.deepcopy(self.frozen)
        frozen['files'][str(self.queue)]=pin(self.queue)
        before={name:module for name,module in sys.modules.items()
                if name.startswith('_selected_control_queue_')}
        with self.assertRaisesRegex(SystemExit,'synthetic module refusal'):
            self.client_module.load_pinned_control_queue(self.queue,frozen)
        after={name:module for name,module in sys.modules.items()
               if name.startswith('_selected_control_queue_')}
        self.assertEqual(before,after)

    def test_17_loader_public_annotations_resolve_to_shared_binding(self) -> None:
        from ck3_mod_acceptance_background_types import ControlQueueBindingV1
        hints=get_type_hints(self.client_module.load_pinned_control_queue)
        self.assertIs(hints['return'],ControlQueueBindingV1)
        binding_hints=get_type_hints(ControlQueueBindingV1)
        self.assertEqual(set(binding_hints),{'refs','module','modules'})
        self.assertEqual(binding_hints['module'],types.ModuleType)

    def test_18_keyed_pins_do_not_override_an_explicit_declared_path(self) -> None:
        # The real allocator stores bytes/sha256 under the absolute path key.
        keyed = copy.deepcopy(self.frozen)
        keyed['files'] = {key: {'bytes': row['bytes'], 'sha256': row['sha256']}
                          for key, row in keyed['files'].items()}
        roundtrip = json.loads(json.dumps(keyed))
        rebound = self.client_module.load_pinned_control_queue(self.queue, roundtrip)
        self.assertEqual(rebound['refs'], self.bundle['refs'])
        self.assertIs(self.client_module.load_pinned_control_queue(
            self.queue, roundtrip, self.bundle), self.bundle)
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            key = str(self.helpers / (name + '.py'))
            for wrong in ('another-selected-source.py', None, True):
                for cached in (False, True):
                    with self.subTest(helper=name, declared_path=wrong, cached=cached):
                        frozen = copy.deepcopy(self.frozen)
                        frozen['files'][key]['path'] = wrong
                        with self.assertRaises(ValueError):
                            self.client_module.load_pinned_control_queue(
                                self.queue, frozen, self.bundle if cached else None)

if __name__ == '__main__':
    unittest.main()
