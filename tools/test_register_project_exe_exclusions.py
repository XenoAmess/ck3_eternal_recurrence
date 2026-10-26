from collections.abc import Iterator
from types import SimpleNamespace
from pathlib import Path
import copy
import ast
import json
import os
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

import register_project_exe_exclusions as m


class FakeWmi:
    def __init__(self, paths: list[str] | None = None,
                 retval: int | None | dict[str, object] = 0, append: bool = True,
                 overwrite: bool = False, failure: Exception | None = None) -> None:
        self.paths=list(paths or []);self.retval=retval;self.append=append
        self.overwrite=overwrite;self.failure=failure;self.calls: list[str]=[]
    def read_paths(self) -> list[str]:return list(self.paths)
    def add_path(self,path: str) -> int | None | dict[str, object]:
        self.calls.append(path)
        if self.failure:raise self.failure
        if self.overwrite:self.paths=[]
        if self.append:self.paths.append(path)
        return self.retval


class RegistrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.repo=self.root/'repo'
        self.source=self.repo/'ck3_autonomous_player/native_bridge';self.source.mkdir(parents=True)
        (self.source/'CMakeLists.txt').write_text('project(fakefixture)')
        self.build=self.root/'build';self.reply=self.build/'.cmake/api/v1/reply';self.reply.mkdir(parents=True)
        self.exe=self.build/'fixture.exe';self.exe.write_bytes(b'MZ offline mock executable only')
        (self.build/'unrelated.exe').write_bytes(b'MZ must not be scanned')
        (self.build/'CompilerIdCXX').mkdir();(self.build/'CompilerIdCXX/CMakeCXXCompilerId.exe').write_bytes(b'MZ unrelated probe')
        self.model={'paths':{'source':str(self.source),'build':str(self.build)},'configurations':[{
            'name':'Release','targets':[{'id':'t1','name':'fixture','jsonFile':'target.json'},
                                       {'id':'lib','name':'library','jsonFile':'lib.json'}]}]}
        self.target={'id':'t1','name':'fixture','type':'EXECUTABLE','paths':{'source':'.','build':'.'},
                     'artifacts':[{'path':'fixture.exe'}],'dependencies':[{'id':'lib'}]}
        self.index={'objects':[{'kind':'codemodel','version':{'major':2},'jsonFile':'model.json'}]}
        self.write_metadata()
        self.manifest=self.collect()
    def write_metadata(self) -> None:
        for name,obj in [('index-test.json',self.index),('model.json',self.model),('target.json',self.target),
                         ('lib.json',{'id':'lib','name':'library','type':'STATIC_LIBRARY','paths':{'source':'.'},'artifacts':[]})]:
            (self.reply/name).write_text(json.dumps(obj))
    def collect(self) -> dict[str, object]:return m.collect_manifest(self.repo,self.source,self.build,'Release',['fixture'])
    def register(self,client,manifest=None,admin=True):
        with patch.object(m,'opted_in',return_value=True):
            return m.register_manifest(manifest or self.manifest,self.root/'receipt.json',client=client,admin=admin)
    def test_only_cmake_exact_executable_not_directory_scan(self):
        self.assertEqual([r['path'] for r in self.manifest['files']],[str(self.exe.resolve())])
        self.assertEqual(self.manifest['files'][0]['target'],'fixture')
    def test_default_disabled_does_not_construct_wmi(self):
        with patch.object(m,'opted_in',return_value=False),patch.object(m,'DefenderWmi',side_effect=AssertionError('must not connect')):
            result=m.register_manifest(self.manifest,self.root/'receipt.json')
        self.assertEqual(result['status'],'disabled')
    def test_ci_overrides_opt_in_without_git_query(self):
        with patch.dict(os.environ,{'CI':'true'}),patch.object(m.subprocess,'run',side_effect=AssertionError('must not query git')):
            self.assertFalse(m.opted_in(self.repo))
    def test_add_preserves_old_values_and_readback(self):
        old=r'C:\existing\keep.exe';w=FakeWmi([old]);result=self.register(w)
        self.assertEqual(result['status'],'verified');self.assertEqual(result['before'],[old])
        self.assertEqual(w.calls,[str(self.exe.resolve())]);self.assertIn(old,result['after'])
        self.assertEqual(result['calls'][0]['return_value'],0)
        self.assertFalse(result['settings_success_is_runtime_trust'])
    def test_exact_existing_path_needs_no_add(self):
        w=FakeWmi([str(self.exe.resolve()).upper()]);result=self.register(w)
        self.assertEqual(result['status'],'verified');self.assertEqual(w.calls,[])
    def test_return_value_failure_not_success(self):
        w=FakeWmi(retval=5,append=False);result=self.register(w)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(result['calls'][0]['return_value'],5)
    def test_zero_retval_without_readback_rejected(self):
        result=self.register(FakeWmi(append=False));self.assertEqual(result['status'],'settings_failed')
    def test_wmi_exception_receipt_retained(self):
        result=self.register(FakeWmi(failure=PermissionError('WBEM denied')))
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(result['after'],[])
        self.assertEqual(result['calls'][0]['return_value'],None)
    def test_nonadmin_no_add(self):
        w=FakeWmi([r'C:\keep.exe']);result=self.register(w,admin=False)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(w.calls,[])
    def test_overwriting_existing_settings_is_rejected(self):
        result=self.register(FakeWmi([r'C:\keep.exe'],overwrite=True));self.assertEqual(result['status'],'settings_failed')
    def test_changed_exe_rejected_before_add(self):
        self.exe.write_bytes(b'MZ changed');w=FakeWmi();result=self.register(w)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(w.calls,[])
    def test_forged_file_list_rejected_before_add(self):
        forged=copy.deepcopy(self.manifest);forged['files'][0]['path']=str(self.build/'unrelated.exe')
        w=FakeWmi();result=self.register(w,forged);self.assertEqual(result['status'],'settings_failed');self.assertEqual(w.calls,[])
    def test_other_source_requires_explicit_candidate(self):
        other=self.root/'external';other.mkdir();(other/'CMakeLists.txt').write_text('project(externalfixture)')
        with self.assertRaises(ValueError):m.validate_source(self.repo,other,None)
        m.validate_source(self.repo,other,'episode04 frozen candidate')
    def test_artifact_escape_and_metadata_escape_rejected(self):
        self.target['artifacts']=[{'path':'../outside.exe'}];(self.root/'outside.exe').write_bytes(b'MZ outside')
        self.write_metadata()
        with self.assertRaises(ValueError):self.collect()
    def test_target_source_outside_project_excluded(self):
        self.target['paths']['source']='../../../thirdparty';self.write_metadata()
        self.assertEqual(self.collect()['files'],[])
    def test_receipt_never_overwritten(self):
        (self.root/'receipt.json').write_text('prior receipt')
        client=FakeWmi()
        with self.assertRaises(FileExistsError):self.register(client)
        self.assertEqual(client.calls,[])
        self.assertEqual((self.root/'receipt.json').read_text(),'prior receipt')


class WmiCallTest(unittest.TestCase):
    def test_object_execmethod_and_only_path_force_parameters(self):
        from types import SimpleNamespace as NS
        class Props:
            def __init__(self,names):self.values={name:NS(Name=name,Value=None) for name in names}
            def Item(self,name):return self.values[name]
            def __iter__(self):return iter(self.values.values())
        for force in (False,True):
            params=NS(Properties_=Props(['ExclusionPath']+(['Force'] if force else [])))
            inp=NS(SpawnInstance_=lambda:params)
            pref=NS(Methods_=NS(Item=lambda name:NS(InParameters=inp)))
            returns=Props(['ReturnValue']);returns.Item('ReturnValue').Value=0
            calls=[]
            def execute(method,parameters):
                calls.append((method,parameters))
                return NS(Properties_=returns)
            pref.ExecMethod_=execute
            services=NS(Get=lambda name:pref)
            client=object.__new__(m.DefenderWmi);client.services=services
            self.assertEqual(client.add_path(r'C:\project\target.exe'),0)
            self.assertEqual(calls[0][0],'Add')
            self.assertEqual(params.Properties_.Item('ExclusionPath').Value,(r'C:\project\target.exe',))
            self.assertEqual(set(params.Properties_.values),{'ExclusionPath'}|({'Force'} if force else set()))
            if force:self.assertTrue(params.Properties_.Item('Force').Value)


class HookTest(unittest.TestCase):
    def setUp(self):
        import run_native_msvc as runner
        self.runner=runner;self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'native_bridge';self.source.mkdir()
        (self.source/'CMakeLists.txt').write_text('project(mock)')
        self.build=self.root/'build';self.build.mkdir()
    def args(self,*extra):
        return self.runner.parser().parse_args(['--source-dir',str(self.source),'--build-dir',str(self.build),
                                               '--build',*extra])
    def run_fake(self,success=True,enabled=True):
        from contextlib import ExitStack
        import subprocess
        with ExitStack() as stack:
            stack.enter_context(patch.object(self.runner,'opted_in',return_value=enabled))
            stack.enter_context(patch.object(self.runner,'validate_source'))
            stack.enter_context(patch.object(self.runner,'request_codemodel'))
            stack.enter_context(patch.object(self.runner,'has_codemodel_reply',return_value=True))
            stack.enter_context(patch.object(self.runner,'visual_studio_installation',return_value=self.root))
            stack.enter_context(patch.object(self.runner,'initialize_msvc',return_value=({'TEMP':'mock','PYTHONPYCACHEPREFIX':'mock'}, {'cmake':'fake-cmake','ninja':'fake-ninja','cl':'fake-cl'})))
            stack.enter_context(patch.object(self.runner,'child_environment',return_value={'TEMP':'mock','PYTHONPYCACHEPREFIX':'mock'}))
            stack.enter_context(patch.object(self.runner,'repair_dependency_prefix',return_value='mock'))
            logs=stack.enter_context(patch.object(self.runner,'run_logged',side_effect=None if success else subprocess.CalledProcessError(2,['fake-cmake'])))
            hook=stack.enter_context(patch.object(self.runner,'after_successful_build',return_value={'status':'verified' if enabled else 'disabled'}))
            if success:
                report=self.runner.run(self.args());self.assertTrue(report['build_succeeded']);self.assertEqual(hook.call_count,1)
            else:
                with self.assertRaises(subprocess.CalledProcessError):self.runner.run(self.args())
                self.assertEqual(hook.call_count,0)
            return logs.call_count
    def test_hook_only_after_successful_build(self):self.assertEqual(self.run_fake(),1)
    def test_no_hook_after_failed_build(self):self.run_fake(success=False)
    def test_disabled_still_builds_without_metadata_requirement(self):self.run_fake(enabled=False)
    def test_dynamic_import_from_research_without_tools_search_path(self):
        import importlib.util
        import sys
        tools=str(Path(self.runner.__file__).resolve().parent)
        search=[entry for entry in sys.path if str(Path(entry).resolve()) != tools]
        spec=importlib.util.spec_from_file_location('isolated_native_msvc_environment',self.runner.__file__)
        module=importlib.util.module_from_spec(spec)
        with patch.object(sys,'path',search),patch.dict(sys.modules):
            sys.modules.pop('register_project_exe_exclusions',None)
            spec.loader.exec_module(module)
            self.assertTrue(callable(module.child_environment))
            self.assertEqual(sys.path[0],tools)


class ExtraProvenanceTest(unittest.TestCase):
    setUp=RegistrationTest.setUp
    write_metadata=RegistrationTest.write_metadata
    collect=RegistrationTest.collect
    def test_dll_only_typed_helpers_pass_strict_static_check(self) -> None:
        source=Path(m.__file__).read_text(encoding='utf-8-sig')
        module=ast.parse(source)
        names={'ProjectExeBuildHookResult','NoProjectExecutableReceipt',
               'FailedBuildExclusionReceipt','_write_receipt',
               '_no_project_executable_result','_build_hook_status'}
        selected=[node for node in module.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))
                  and node.name in names]
        self.assertEqual(len(selected),len(names))
        imports=[node for node in module.body if isinstance(node,(ast.Import,ast.ImportFrom))]
        constants=[node for node in module.body if isinstance(node,ast.Assign)
                   and any(isinstance(target,ast.Name) and target.id=='SCHEMA' for target in node.targets)]
        checked=self.root/'dll_hook_types.py'
        checked.write_text(ast.unparse(ast.Module(body=imports+constants+selected,type_ignores=[])),encoding='utf-8')
        environment=os.environ.copy()
        environment['MYPYPATH']=str(Path(m.__file__).resolve().parent)
        result=subprocess.run([sys.executable,'-B','-m','mypy','--strict','--follow-imports=skip',
                               '--no-incremental','--cache-dir',str(self.root/'mypy-cache'),str(checked)],
                              env=environment,capture_output=True,text=True,check=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_dll_only_cmake_target_does_not_dispatch_exe_registration(self) -> None:
        dll=self.build/'fixture.dll'
        dll.write_bytes(b'MZ named DLL artifact; unrelated EXEs stay outside target closure')
        self.target['type']='SHARED_LIBRARY'
        self.target['artifacts']=[{'path':'fixture.dll'}]
        self.write_metadata()
        with patch.object(m,'opted_in',return_value=True), patch.object(
                m,'register_manifest',side_effect=AssertionError('DLL-only target must not dispatch broker or WMI')):
            result=m.after_successful_build(self.repo,self.source,self.build,'Release',['fixture'])
        self.assertEqual(result['status'],'not_applicable')
        receipt=json.loads(Path(result['receipt']).read_text())
        manifest=json.loads(Path(result['manifest']).read_text())
        self.assertEqual(manifest['files'],[])
        self.assertFalse(receipt['broker_called'])
        self.assertFalse(receipt['wmi_called'])
        self.assertIsInstance(receipt['machine_id'],str)
        self.assertTrue(receipt['observed_at_utc'])
        self.assertFalse(receipt['settings_success_is_runtime_trust'])
        self.assertTrue((self.build/'unrelated.exe').is_file())
    def test_dll_target_with_executable_dependency_still_registers(self) -> None:
        self.target['type']='SHARED_LIBRARY'
        self.target['artifacts']=[{'path':'fixture.dll'}]
        self.write_metadata()
        dependency={'id':'lib','name':'library','type':'EXECUTABLE','paths':{'source':'.'},
                    'artifacts':[{'path':'fixture.exe'}]}
        (self.reply/'lib.json').write_text(json.dumps(dependency))
        def register_dependency(manifest: object, receipt_path: Path, *, manifest_bytes: bytes) -> dict[str, str]:
            receipt_path.write_text(json.dumps({'status':'verified'}))
            return {'status':'verified'}
        with patch.object(m,'opted_in',return_value=True), patch.object(
                m,'register_manifest',side_effect=register_dependency) as register:
            result=m.after_successful_build(self.repo,self.source,self.build,'Release',['fixture'])
        self.assertEqual(result['status'],'verified')
        self.assertEqual(register.call_count,1)
        submitted=register.call_args.args[0]
        self.assertEqual([row['path'] for row in submitted['files']],[str(self.exe.resolve())])
    def test_invalid_manifest_provenance_writes_failure_receipt_without_wmi(self):
        with patch.object(m,'opted_in',return_value=True),patch.object(m,'collect_manifest',side_effect=ValueError('bad codemodel')),patch.object(m,'DefenderWmi',side_effect=AssertionError('must not connect')):
            result=m.after_successful_build(self.repo,self.source,self.build,'Release',['fixture'])
        self.assertEqual(result['status'],'settings_failed')
        receipt=json.loads(Path(result['receipt']).read_text())
        self.assertEqual(receipt['calls'],[]);self.assertIsNone(receipt['before'])

class CommandTest(unittest.TestCase):
    write_metadata=RegistrationTest.write_metadata
    collect=RegistrationTest.collect
    register=RegistrationTest.register
    def setUp(self):
        RegistrationTest.setUp(self)
        self.cpp=self.source/'fixture.cpp';self.cpp.write_text('int main() { return 0; }')
        self.argv=[str(self.root/'cl.exe'),'/nologo',str(self.cpp),'/Fe'+str(self.exe)]
        self.command_manifest=m.collect_command_manifest(self.repo,self.source,self.build,self.argv,[self.exe])
    def test_command_explicit_output_registered(self):
        w=FakeWmi();result=self.register(w,self.command_manifest)
        self.assertEqual(result['status'],'verified');self.assertEqual(w.calls,[str(self.exe.resolve())])
    def test_failed_command_or_undeclared_output_rejected(self):
        with self.assertRaises(ValueError):m.collect_command_manifest(self.repo,self.source,self.build,self.argv,[self.exe],return_code=2)
        with self.assertRaises(ValueError):m.collect_command_manifest(self.repo,self.source,self.build,self.argv,[self.build/'unrelated.exe'])
    def test_source_changed_rejects_frozen_command(self):
        self.cpp.write_text('changed after manifest');w=FakeWmi();result=self.register(w,self.command_manifest)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(w.calls,[])
    def test_nonadmin_existing_settings_require_verified_readback(self):
        w=FakeWmi([str(self.exe.resolve())]);result=self.register(w,self.command_manifest,admin=False)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(w.calls,[])
        self.assertTrue(result['admin_required_for_verified_readback']);self.assertIsNone(result['before'])
    def test_explicit_command_source_without_cmake_lists_keeps_exact_pins(self):
        (self.source/'CMakeLists.txt').unlink()
        manifest=m.collect_command_manifest(self.repo,self.source,self.build,self.argv,[self.exe])
        result=self.register(FakeWmi(),manifest)
        self.assertEqual(result['status'],'verified')
        self.assertEqual(manifest['command_provenance']['sources'][0]['path'],str(self.cpp.resolve()))
        candidate=self.root/'external-command';candidate.mkdir()
        cpp=candidate/'declared.cpp';cpp.write_text('int main() { return 0; }')
        argv=[str(self.root/'cl.exe'),str(cpp),'/Fe'+str(self.exe)]
        with self.assertRaises(ValueError):m.collect_command_manifest(self.repo,candidate,self.build,argv,[self.exe])
        frozen=m.collect_command_manifest(self.repo,candidate,self.build,argv,[self.exe],'explicit declared.cpp fixture')
        self.assertEqual(len(frozen['command_provenance']['sources']),1)

class LinkTest(unittest.TestCase):
    setUp=RegistrationTest.setUp
    write_metadata=RegistrationTest.write_metadata
    collect=RegistrationTest.collect
    register=RegistrationTest.register
    def chain(self):
        cpp=self.source/'real_input.cpp';cpp.write_text('int main() { return 0; }')
        obj=self.build/'real_input.obj';obj.write_bytes(b'actual-chain offline mock object')
        source=[{'argv':[str(self.root/'cl.exe'),'/c',str(cpp),'/Fo'+str(obj)],'return_code':0}]
        link=[str(self.root/'link.exe'),str(obj),'/OUT:'+str(self.exe)]
        return cpp,obj,source,link
    def test_actual_cl_c_then_link_out_chain(self):
        cpp,obj,source,link=self.chain()
        manifest=m.collect_command_manifest(self.repo,self.source,self.build,link,[self.exe],source_commands=source)
        result=self.register(FakeWmi(),manifest);self.assertEqual(result['status'],'verified')
        self.assertEqual(manifest['command_provenance']['objects'][0]['path'],str(obj.resolve()))
    def test_link_without_prior_producer_rejected(self):
        cpp,obj,source,link=self.chain()
        with self.assertRaises(ValueError):m.collect_command_manifest(self.repo,self.source,self.build,link,[self.exe])
        source[0]['return_code']=2
        with self.assertRaises(ValueError):m.collect_command_manifest(self.repo,self.source,self.build,link,[self.exe],source_commands=source)
    def test_unknown_object_or_object_changed_rejected(self):
        cpp,obj,source,link=self.chain()
        manifest=m.collect_command_manifest(self.repo,self.source,self.build,link,[self.exe],source_commands=source)
        obj.write_bytes(b'changed object');client=FakeWmi();result=self.register(client,manifest)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(client.calls,[])
        unknown=self.build/'unknown.obj';unknown.write_bytes(b'unknown')
        link.insert(1,str(unknown))
        with self.assertRaises(ValueError):m.collect_command_manifest(self.repo,self.source,self.build,link,[self.exe],source_commands=source)

class ActualComBoundaryTest(unittest.TestCase):
    setUp=RegistrationTest.setUp
    write_metadata=RegistrationTest.write_metadata
    collect=RegistrationTest.collect
    register=RegistrationTest.register
    def com_client(self, return_object):
        from types import SimpleNamespace as NS
        class Props:
            def __init__(self):self.values={'ExclusionPath':NS(Name='ExclusionPath',Value=None)}
            def Item(self,name):return self.values[name]
            def __iter__(self):return iter(self.values.values())
        params=NS(Properties_=Props())
        pref=NS(Methods_=NS(Item=lambda name:NS(InParameters=NS(SpawnInstance_=lambda:params))))
        self.com_calls=[]
        def execute(method,parameters):
            self.com_calls.append((method,parameters));return return_object
        client=object.__new__(m.DefenderWmi)
        pref.ExecMethod_=execute
        client.services=NS(Get=lambda name:pref)
        return client
    def test_none_com_return_requires_fresh_readback_without_fake_zero(self):
        client=self.com_client(None)
        self.assertIsNone(client.add_path(str(self.exe.resolve())))
        self.assertEqual(len(self.com_calls),1)
        w=FakeWmi([r'C:\old\keep.exe'],retval=None)
        result=self.register(w)
        self.assertEqual(result['status'],'verified');self.assertEqual(len(w.calls),1)
        call=result['calls'][0]
        self.assertIsNone(call['return_value']);self.assertTrue(call['return_object_absent'])
        self.assertFalse(call['return_value_available']);self.assertIn(str(self.exe.resolve()),call['fresh_readback'])
    def test_output_decoder_error_preserved_and_readback_verified(self):
        value=self.com_client(object()).add_path(str(self.exe.resolve()))
        self.assertIsNone(value['return_value']);self.assertEqual(value['return_decode_error_type'],'AttributeError')
        result=self.register(FakeWmi(retval=value))
        self.assertEqual(result['status'],'verified');self.assertEqual(result['calls'][0]['return_decode_error_type'],'AttributeError')
        self.assertFalse(result['calls'][0]['return_object_absent'])
    def test_invocation_error_after_mutation_fully_verified_no_retry(self):
        class MutateThenRaise(FakeWmi):
            def add_path(self,path):
                self.calls.append(path);self.paths.append(path);raise RuntimeError('provider error after mutation')
        w=MutateThenRaise([r'C:\old\keep.exe']);result=self.register(w)
        self.assertEqual(result['status'],'verified');self.assertEqual(len(w.calls),1)
        self.assertEqual(result['error_stage'],'Add-invocation');self.assertIn('provider error',result['calls'][0]['call_error'])
        self.assertFalse(result['partial_mutation']);self.assertEqual(result['missing_requested_paths'],[])
    def test_partial_mutation_retained_and_no_next_add(self):
        second=self.build/'second.exe';second.write_bytes(b'MZ second offline mock')
        self.target['artifacts'].append({'path':'second.exe'});self.write_metadata();self.manifest=self.collect()
        class MutateThenRaise(FakeWmi):
            def add_path(self,path):
                self.calls.append(path);self.paths.append(path);raise RuntimeError('provider error after first mutation')
        w=MutateThenRaise([r'C:\old\keep.exe']);result=self.register(w)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(len(w.calls),1)
        self.assertTrue(result['partial_mutation']);self.assertEqual(result['missing_requested_paths'],[str(second.resolve())])
        self.assertTrue(result['observed_prior_settings_preserved'])
    def test_nonadmin_hidden_empty_arrays_are_not_missing_settings(self):
        class HiddenWmi(FakeWmi):
            def read_paths(self):raise AssertionError('non-admin hidden-array read must not be used')
        w=HiddenWmi();result=self.register(w,admin=False)
        self.assertEqual(result['status'],'settings_failed');self.assertEqual(w.calls,[])
        self.assertTrue(result['admin_required_for_verified_readback'])
        self.assertIsNone(result['before']);self.assertIsNone(result['after'])
        self.assertNotIn('missing_requested_paths',result)

def _observed_object(value: object) -> dict[str, object]:
    """Narrow the legacy dynamic JSON receipt at this test boundary."""
    if not isinstance(value, dict):
        raise AssertionError('expected an observed object')
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise AssertionError('expected observed string keys')
        result[key] = item
    return result

def _observed_settings(value: object) -> m.ExclusionSettings:
    settings = _observed_object(value)
    if set(settings) != {'ExclusionPath', 'ExclusionExtension', 'ExclusionProcess'}:
        raise AssertionError('expected all three observed settings')
    return {'ExclusionPath': m.DefenderWmi._array(settings['ExclusionPath'], 'ExclusionPath'),
            'ExclusionExtension': m.DefenderWmi._array(settings['ExclusionExtension'], 'ExclusionExtension'),
            'ExclusionProcess': m.DefenderWmi._array(settings['ExclusionProcess'], 'ExclusionProcess')}

def _observed_calls(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise AssertionError('expected observed calls')
    return [_observed_object(item) for item in value]

def _observed_text(value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError('expected observed text')
    return value

class _SettingsProperties:
    def __init__(self, values: dict[str, object]) -> None:
        from types import SimpleNamespace
        self.values = {key: SimpleNamespace(Name=key, Value=value)
                       for key, value in values.items()}

    def Item(self, name: str) -> SimpleNamespace:
        return self.values[name]

    def __iter__(self) -> Iterator[SimpleNamespace]:
        return iter(self.values.values())

class _SettingsProvider:
    """Controlled COM boundary; the production WMI reader and Add method run."""
    def __init__(self) -> None:
        self.paths: list[str] = [r'C:\old\keep.exe']
        self.extensions: list[str] = ['oldext', 'oldext', 'keep']
        self.processes: list[str] = [r'C:\old\process.exe']
        self.queries: list[str] = []
        self.calls: list[str] = []
        self.read_overrides: dict[int, object] = {}
        self.row_count = 1
        self.change_nonpath: str | None = None
        self.return_value: int | None = 0
        self.bad_return_object = False
        self.raise_after_mutation = False

    def snapshot(self) -> dict[str, object]:
        return {'ExclusionPath': list(self.paths),
                'ExclusionExtension': list(self.extensions),
                'ExclusionProcess': list(self.processes)}

    def ExecQuery(self, query: str) -> list[SimpleNamespace]:
        from types import SimpleNamespace
        self.queries.append(query)
        value = self.read_overrides.get(len(self.queries), self.snapshot())
        if isinstance(value, Exception):
            raise value
        if not isinstance(value, dict):
            raise AssertionError('test read override must be a settings object')
        return [SimpleNamespace(Properties_=_SettingsProperties(value))
                for _ in range(self.row_count)]

    def Get(self, name: str) -> SimpleNamespace:
        from types import SimpleNamespace
        if name != 'MSFT_MpPreference':
            raise AssertionError('unexpected WMI class')
        parameters = SimpleNamespace(Properties_=_SettingsProperties(
            {'ExclusionPath': None, 'Force': None}))
        inputs = SimpleNamespace(SpawnInstance_=lambda: parameters)
        method = SimpleNamespace(InParameters=inputs)
        return SimpleNamespace(
            Methods_=SimpleNamespace(Item=lambda method_name: method),
            ExecMethod_=self.execute)

    def execute(self, method: str, parameters: SimpleNamespace) -> object:
        from types import SimpleNamespace
        if method != 'Add' or set(parameters.Properties_.values) != {'ExclusionPath', 'Force'}:
            raise AssertionError('producer changed the Add setting scope')
        value = parameters.Properties_.Item('ExclusionPath').Value
        if not isinstance(value, tuple) or len(value) != 1 or not isinstance(value[0], str):
            raise AssertionError('expected one exact project path')
        if parameters.Properties_.Item('Force').Value is not True:
            raise AssertionError('expected the existing Force parameter')
        self.calls.append(value[0])
        self.paths.append(value[0])
        if self.change_nonpath == 'ExclusionExtension':
            self.extensions.append('unrequested-change')
        elif self.change_nonpath == 'ExclusionProcess':
            self.processes.append(r'C:\unrequested\process.exe')
        if self.raise_after_mutation:
            raise RuntimeError('controlled provider failure after mutation')
        if self.return_value is None:
            return None
        if self.bad_return_object:
            return object()
        return SimpleNamespace(Properties_=_SettingsProperties({'ReturnValue': self.return_value}))

class ThreeSettingsReadbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RegistrationTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def client(self, provider: _SettingsProvider) -> m.DefenderWmi:
        client = object.__new__(m.DefenderWmi)
        client.services = provider
        client.token_user_sid = 'S-1-5-21-101-102-103-1001'
        client.before_settings = None
        client.after_settings = None
        client.settings_readback_error = None
        client.administrative_token_observed = False
        client.provider_nullable_observed = False
        client.before_property_observations = None
        client.after_property_observations = None
        client.current_property_observations = None
        return client

    def register_default(self, provider: _SettingsProvider, name: str = 'receipt.json') -> dict[str, object]:
        client = self.client(provider)
        def initialize(instance: m.DefenderWmi) -> None:
            instance.__dict__.update(client.__dict__)
        # Keep the real class: its v1 serializer calls DefenderWmi._array.
        # Replace only COM construction, never class-level validation methods.
        with patch.object(m, 'opted_in', return_value=True), \
             patch.object(m.DefenderWmi, '__init__', new=initialize):
            result: object = m.register_manifest(self.fixture.manifest, self.fixture.root / name, admin=True)
        return _observed_object(result)

    def add_second_executable(self) -> None:
        (self.fixture.build / 'second.exe').write_bytes(b'MZ second offline fixture')
        artifacts = self.fixture.target['artifacts']
        if not isinstance(artifacts, list):
            raise AssertionError('expected fixture artifact rows')
        artifacts.append({'path': 'second.exe'})
        self.fixture.write_metadata()
        self.fixture.manifest = self.fixture.collect()

    def test_default_production_reader_add_and_json_roundtrip(self) -> None:
        provider = _SettingsProvider()
        result = self.register_default(provider)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(provider.calls, [str(self.fixture.exe.resolve())])
        self.assertEqual(len(provider.queries), 3)
        self.assertTrue(all(query == 'SELECT ExclusionPath,ExclusionExtension,ExclusionProcess FROM MSFT_MpPreference'
                            for query in provider.queries))
        self.assertEqual(result['before'], [r'C:\old\keep.exe'])
        self.assertEqual(_observed_settings(result['before_settings'])['ExclusionExtension'], ['oldext', 'oldext', 'keep'])
        self.assertEqual(_observed_settings(result['after_settings'])['ExclusionProcess'], [r'C:\old\process.exe'])
        self.assertEqual(set(_observed_settings(result['before_settings'])),
                         {'ExclusionPath', 'ExclusionExtension', 'ExclusionProcess'})
        self.assertEqual(result['settings_readback_schema'], 'xar.project-exe-three-settings-readback/v1')
        self.assertTrue(result['settings_readback_complete'])
        self.assertTrue(result['observed_extensions_unchanged'])
        self.assertTrue(result['observed_processes_unchanged'])
        self.assertIsNone(result['settings_readback_error'])
        self.assertIs(type(result['settings_readback_process_id']), int)
        self.assertEqual(result['settings_readback_process_id'], os.getpid())
        self.assertEqual(result['settings_readback_token_user_sid'], 'S-1-5-21-101-102-103-1001')
        self.assertEqual(json.loads((self.fixture.root / 'receipt.json').read_text()), result)
        self.assertIn(str(self.fixture.exe.resolve()), m.DefenderWmi._array(
            _observed_calls(result['calls'])[0]['fresh_readback'], 'fresh_readback'))

    def test_real_constructor_captures_token_sid_and_closes_handle(self) -> None:
        import sys
        provider = _SettingsProvider()
        calls: list[str] = []
        class Token:
            def Close(self) -> None:
                calls.append('token-close')
        token = Token()
        api = SimpleNamespace(GetCurrentProcess=lambda: 'controlled-process')
        con = SimpleNamespace(TOKEN_QUERY=8)
        security = SimpleNamespace(
            OpenProcessToken=lambda process, access: token,
            GetTokenInformation=lambda handle, kind: ('controlled-sid', 0),
            TokenUser=1, ConvertSidToStringSid=lambda sid: 'S-1-5-21-101-102-103-1001')
        pythoncom = SimpleNamespace(CoInitialize=lambda: calls.append('com-initialize'))
        com_client = SimpleNamespace(GetObject=lambda moniker: provider)
        com = SimpleNamespace(client=com_client)
        modules = {'win32api': api, 'win32con': con, 'win32security': security,
                   'pythoncom': pythoncom, 'win32com': com, 'win32com.client': com_client}
        with patch.dict(sys.modules, modules):
            client = m.DefenderWmi()
        self.assertEqual(client.token_user_sid, 'S-1-5-21-101-102-103-1001')
        self.assertEqual(calls, ['token-close', 'com-initialize'])
        self.assertEqual(client.read_paths(), provider.paths)
        self.assertTrue(client.settings_readback()['settings_readback_complete'])

    def test_null_missing_scalar_and_wrong_element_never_become_empty(self) -> None:
        for field in ('ExclusionPath', 'ExclusionExtension', 'ExclusionProcess'):
            for invalid in (None, '', False, 0, ['valid', 1], [True]):
                with self.subTest(field=field, invalid=invalid):
                    provider = _SettingsProvider()
                    value = provider.snapshot()
                    value[field] = invalid
                    provider.read_overrides[1] = value
                    result = self.register_default(provider, 'invalid-' + str(len(list(self.fixture.root.glob('invalid-*')))) + '.json')
                    self.assertEqual(result['status'], 'settings_failed')
                    self.assertFalse(result['settings_readback_complete'])
                    self.assertIsNone(result['before'])
                    self.assertIsNone(result['before_settings'])
                    self.assertEqual(provider.calls, [])
                    self.assertIsNotNone(result['settings_readback_error'])
            provider = _SettingsProvider()
            value = provider.snapshot()
            del value[field]
            provider.read_overrides[1] = value
            result = self.register_default(provider, 'missing-' + field + '.json')
            self.assertEqual(result['status'], 'settings_failed')
            self.assertEqual(provider.calls, [])
            self.assertFalse(result['settings_readback_complete'])

    def test_zero_or_multiple_preference_objects_do_not_qualify(self) -> None:
        for count in (0, 2):
            provider = _SettingsProvider()
            provider.row_count = count
            result = self.register_default(provider, 'rows-' + str(count) + '.json')
            self.assertEqual(result['status'], 'settings_failed')
            self.assertEqual(provider.calls, [])
            self.assertFalse(result['settings_readback_complete'])

    def test_observed_empty_arrays_are_preserved_as_observed_empty(self) -> None:
        provider = _SettingsProvider()
        provider.paths, provider.extensions, provider.processes = [], [], []
        result = self.register_default(provider)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['before_settings'],
                         {'ExclusionPath': [], 'ExclusionExtension': [], 'ExclusionProcess': []})
        self.assertTrue(result['settings_readback_complete'])

    def test_nonpath_order_and_duplicates_preserved_with_set_comparison(self) -> None:
        provider = _SettingsProvider()
        provider.read_overrides[2] = {
            'ExclusionPath': provider.paths + [str(self.fixture.exe.resolve())],
            'ExclusionExtension': ('keep', 'oldext'),
            'ExclusionProcess': (r'C:\old\process.exe', r'C:\old\process.exe')}
        client = self.client(provider)
        self.assertEqual(client.read_paths(), [r'C:\old\keep.exe'])
        client.read_paths()
        readback = client.settings_readback()
        before, after = readback['before_settings'], readback['after_settings']
        if before is None or after is None:
            raise AssertionError('expected complete observed settings')
        self.assertEqual(before['ExclusionExtension'], ['oldext', 'oldext', 'keep'])
        self.assertEqual(after['ExclusionExtension'], ['keep', 'oldext'])
        self.assertEqual(after['ExclusionProcess'],
                         [r'C:\old\process.exe', r'C:\old\process.exe'])
        self.assertTrue(readback['observed_extensions_unchanged'])
        self.assertTrue(readback['observed_processes_unchanged'])
        extensions = before['ExclusionExtension']
        if extensions is None:
            raise AssertionError('expected observed array in this v1 test')
        extensions.append('must-not-alias')
        actual_before = client.before_settings
        if actual_before is None:
            raise AssertionError('expected original observed settings')
        self.assertEqual(actual_before['ExclusionExtension'], ['oldext', 'oldext', 'keep'])

    def test_each_successful_add_observes_three_settings_before_next_add(self) -> None:
        self.add_second_executable()
        provider = _SettingsProvider()
        result = self.register_default(provider)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(len(provider.queries), 4)
        self.assertEqual(_observed_calls(result['calls'])[0]['fresh_readback'], [r'C:\old\keep.exe', str(self.fixture.exe.resolve())])
        self.assertNotIn(str((self.fixture.build / 'second.exe').resolve()), m.DefenderWmi._array(
            _observed_calls(result['calls'])[0]['fresh_readback'], 'fresh_readback'))
        self.assertEqual(_observed_calls(result['calls'])[1]['fresh_readback'], result['after'])

    def test_nonpath_change_stops_next_add_and_latches_even_after_restore(self) -> None:
        self.add_second_executable()
        for field in ('ExclusionExtension', 'ExclusionProcess'):
            with self.subTest(field=field):
                provider = _SettingsProvider()
                original = provider.snapshot()
                provider.change_nonpath = field
                restored = dict(original)
                restored['ExclusionPath'] = provider.paths + [str(self.fixture.exe.resolve())]
                provider.read_overrides[3] = restored
                result = self.register_default(provider, field + '.json')
                self.assertEqual(result['status'], 'settings_failed')
                self.assertEqual(provider.calls, [str(self.fixture.exe.resolve())])
                self.assertFalse(result['settings_readback_complete'])
                self.assertFalse(result['observed_extensions_unchanged'])
                self.assertFalse(result['observed_processes_unchanged'])
                self.assertIn(field, _observed_text(result['settings_readback_error']))
                self.assertTrue(result['partial_mutation'])
                self.assertEqual(result['missing_requested_paths'], [str((self.fixture.build / 'second.exe').resolve())])
                self.assertEqual(_observed_object(result['after_settings'])[field], original[field])

    def test_read_exception_latches_even_when_followup_observation_succeeds(self) -> None:
        self.add_second_executable()
        provider = _SettingsProvider()
        provider.read_overrides[2] = PermissionError('controlled readback denied')
        result = self.register_default(provider)
        self.assertEqual(result['status'], 'settings_failed')
        self.assertEqual(provider.calls, [str(self.fixture.exe.resolve())])
        self.assertFalse(result['settings_readback_complete'])
        self.assertIn('controlled readback denied', _observed_text(result['settings_readback_error']))
        self.assertEqual(_observed_settings(result['after_settings'])['ExclusionPath'], provider.paths)
        self.assertTrue(result['partial_mutation'])

    def test_nullable_decoder_and_mutate_then_raise_keep_real_readback_semantics(self) -> None:
        for mode in ('null', 'decoder', 'mutate-then-raise'):
            provider = _SettingsProvider()
            provider.return_value = None if mode == 'null' else 0
            provider.bad_return_object = mode == 'decoder'
            provider.raise_after_mutation = mode == 'mutate-then-raise'
            result = self.register_default(provider, mode + '.json')
            self.assertEqual(result['status'], 'verified')
            self.assertEqual(provider.calls, [str(self.fixture.exe.resolve())])
            self.assertTrue(result['settings_readback_complete'])
            self.assertTrue(result['observed_extensions_unchanged'])
            self.assertTrue(result['observed_processes_unchanged'])

    def test_explicit_custom_client_does_not_claim_default_three_array_scope(self) -> None:
        with patch.object(m, 'opted_in', return_value=True):
            result = m.register_manifest(self.fixture.manifest, self.fixture.root / 'receipt.json',
                                         client=FakeWmi(), admin=True)
        self.assertEqual(result['status'], 'verified')
        self.assertNotIn('settings_readback_schema', result)
        self.assertNotIn('before_settings', result)
        self.assertNotIn('settings_readback_process_id', result)



class QualifiedNullableSettingsTest(unittest.TestCase):
    """Real registration producer/reader; controlled successful CIM property metadata."""
    class Provider(_SettingsProvider):
        def __init__(self) -> None:
            super().__init__()
            self.bad_metadata: tuple[str, str, object] | None = None

        def snapshot(self) -> dict[str, object]:
            value = super().snapshot()
            value['ExclusionExtension'] = None
            value['ExclusionProcess'] = None
            return value

        def ExecQuery(self, query: str) -> list[SimpleNamespace]:
            rows = super().ExecQuery(query)
            for row in rows:
                for prop in row.Properties_:
                    prop.CIMType = 8
                    prop.IsArray = True
                if self.bad_metadata is not None:
                    name, key, value = self.bad_metadata
                    setattr(row.Properties_.Item(name), key, value)
            return rows

    def setUp(self) -> None:
        self.fixture = RegistrationTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def add_second_executable(self) -> None:
        (self.fixture.build / 'second.exe').write_bytes(b'MZ second offline fixture')
        artifacts = self.fixture.target['artifacts']
        if not isinstance(artifacts, list):
            raise AssertionError('expected fixture artifact rows')
        artifacts.append({'path': 'second.exe'})
        self.fixture.write_metadata()
        self.fixture.manifest = self.fixture.collect()

    def client(self, provider: _SettingsProvider) -> m.DefenderWmi:
        result = object.__new__(m.DefenderWmi)
        result.services = provider
        result.token_user_sid = 'S-1-5-21-101-102-103-1001'
        result.before_settings = None
        result.after_settings = None
        result.settings_readback_error = None
        result.administrative_token_observed = isinstance(provider, self.Provider)
        result.provider_nullable_observed = False
        result.before_property_observations = None
        result.after_property_observations = None
        result.current_property_observations = None
        return result

    def register_default(self, provider: _SettingsProvider, name: str = 'receipt.json') -> dict[str, object]:
        client = self.client(provider)
        def initialize(instance: m.DefenderWmi) -> None:
            instance.__dict__.update(client.__dict__)
        # Preserve the same real class/method dispatch in v1 and v2 fixtures.
        with patch.object(m, 'opted_in', return_value=True), \
             patch.object(m.DefenderWmi, '__init__', new=initialize):
            value: object = m.register_manifest(self.fixture.manifest, self.fixture.root / name, admin=True)
        return _observed_object(value)

    def test_qualified_nullable_values_roundtrip_and_all_adds(self) -> None:
        self.add_second_executable()
        provider = self.Provider()
        result = self.register_default(provider)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(result['settings_readback_schema'], 'xar.project-exe-three-settings-readback/v2')
        for key in ('before_settings', 'after_settings'):
            value = _observed_object(result[key])
            self.assertIsNone(value['ExclusionExtension'])
            self.assertIsNone(value['ExclusionProcess'])
            self.assertIsInstance(value['ExclusionPath'], list)
        self.assertTrue(result['settings_readback_complete'])
        self.assertTrue(result['observed_extensions_unchanged'])
        self.assertTrue(result['observed_processes_unchanged'])
        self.assertEqual(result['before_property_observations'], result['after_property_observations'])
        self.assertEqual(json.loads((self.fixture.root / 'receipt.json').read_text()), result)

    def test_null_and_empty_array_are_different_and_latch(self) -> None:
        for field in ('ExclusionExtension', 'ExclusionProcess'):
            provider = self.Provider()
            client = self.client(provider)
            client.read_paths()
            change = provider.snapshot()
            change[field] = []
            provider.read_overrides[2] = change
            with self.assertRaisesRegex(RuntimeError, 'non-path exclusion changed'):
                client.read_paths()
            with self.assertRaisesRegex(RuntimeError, 'Earlier Defender settings readback failed'):
                client.read_paths()
            self.assertFalse(client.settings_readback()['settings_readback_complete'])

    def test_qualified_null_rejects_wrong_metadata_and_null_paths(self) -> None:
        for field, key, wrong in [('ExclusionExtension', 'CIMType', True),
                                  ('ExclusionProcess', 'CIMType', 3),
                                  ('ExclusionPath', 'IsArray', 1),
                                  ('ExclusionExtension', 'Name', 'wrong')]:
            provider = self.Provider()
            provider.bad_metadata = (field, key, wrong)
            result = self.register_default(provider, 'bad-meta-' + field + key + '.json')
            self.assertEqual(result['status'], 'settings_failed')
            self.assertEqual(provider.calls, [])
            self.assertFalse(result['settings_readback_complete'])
        provider = self.Provider()
        value = provider.snapshot()
        value['ExclusionPath'] = None
        provider.read_overrides[1] = value
        result = self.register_default(provider, 'null-paths.json')
        self.assertEqual(result['status'], 'settings_failed')
        self.assertEqual(provider.calls, [])

    def test_schema_metadata_does_not_replace_admin_observation(self) -> None:
        provider = self.Provider()
        client = self.client(provider)
        client.administrative_token_observed = False
        with self.assertRaisesRegex(RuntimeError, 'administrative token'):
            client.read_paths()

    def test_actual_versioned_models_and_reader_methods_pass_strict(self) -> None:
        source = ast.parse(Path(m.__file__).read_text(encoding='utf-8-sig'))
        model_names = {'ExclusionSettings', 'NullableExclusionSettings',
                       'ProviderPropertyObservation', 'WmiProperty', 'WmiProperties',
                       'WmiPreferenceRow', 'WmiReadServices', 'DirectSettingsReadbackFields',
                       'DirectSettingsReadbackV1', 'DirectSettingsReadbackV2'}
        alias_names = {'ExclusionField', 'DirectSettingsReadback'}
        models = [copy.deepcopy(node) for node in source.body
                  if isinstance(node, ast.ClassDef) and node.name in model_names]
        aliases = [copy.deepcopy(node) for node in source.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id in alias_names
                           for target in node.targets)]
        self.assertEqual(len(models), len(model_names))
        self.assertEqual(len(aliases), len(alias_names))
        readers = [node for node in source.body if isinstance(node, ast.ClassDef)
                   and node.name == 'DefenderWmi']
        self.assertEqual(len(readers), 1)
        reader = readers[0]
        method_names = {'_array', '_copy', '_same_nonpath', '_v1_settings',
                        '_qualified_nullable_properties', '_preference_rows',
                        'read_settings', 'read_paths', 'settings_readback'}
        methods = [copy.deepcopy(node) for node in reader.body
                   if isinstance(node, ast.FunctionDef) and node.name in method_names]
        self.assertEqual(len(methods), len(method_names))
        initializers = [node for node in reader.body if isinstance(node, ast.FunctionDef)
                        and node.name == '__init__']
        self.assertEqual(len(initializers), 1)
        state_names = {'token_user_sid', 'before_settings', 'after_settings',
                       'administrative_token_observed', 'provider_nullable_observed',
                       'before_property_observations', 'after_property_observations',
                       'current_property_observations', 'settings_readback_error'}
        declarations: list[ast.stmt] = []
        found: set[str] = set()
        for node in ast.walk(initializers[0]):
            if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Attribute)
                    and isinstance(node.target.value, ast.Name) and node.target.value.id == 'self'
                    and node.target.attr in state_names):
                found.add(node.target.attr)
                declarations.append(ast.AnnAssign(
                    target=ast.Name(id=node.target.attr, ctx=ast.Store()),
                    annotation=copy.deepcopy(node.annotation), value=None, simple=1))
        self.assertEqual(found, state_names)
        preference_methods = [node for node in methods if node.name == '_preference_rows']
        self.assertEqual(len(preference_methods), 1)
        services_argument = preference_methods[0].args.args[0]
        self.assertEqual(services_argument.arg, 'services')
        self.assertIsNotNone(services_argument.annotation)
        # Static boundary for the existing dynamic COM constructor: the exact
        # production getter protocol, with no substitute getter implementation.
        declarations.append(ast.AnnAssign(
            target=ast.Name(id='services', ctx=ast.Store()),
            annotation=copy.deepcopy(services_argument.annotation), value=None, simple=1))
        checked_class = ast.parse('class DefenderWmi: pass').body[0]
        if not isinstance(checked_class, ast.ClassDef):
            raise AssertionError('expected class AST')
        checked_class.body = declarations + methods
        imports = [copy.deepcopy(node) for node in source.body
                   if isinstance(node, (ast.Import, ast.ImportFrom))]
        # Preserve real source order: ExclusionField precedes its model uses.
        selected_names = model_names | alias_names
        ordered_models = [copy.deepcopy(node) for node in source.body
                          if (isinstance(node, ast.ClassDef) and node.name in selected_names)
                          or (isinstance(node, ast.Assign) and any(
                              isinstance(target, ast.Name) and target.id in selected_names
                              for target in node.targets))]
        checked = self.fixture.root / 'nullable_reader_types.py'
        checked.write_text(ast.unparse(ast.fix_missing_locations(ast.Module(
            body=imports + ordered_models + [checked_class], type_ignores=[]))), encoding='utf-8')
        environment = os.environ.copy()
        environment['MYPYPATH'] = str(Path(m.__file__).resolve().parent)
        result = subprocess.run([
            sys.executable, '-B', '-m', 'mypy', '--strict', '--follow-imports=skip',
            '--no-incremental', '--cache-dir', os.devnull, str(checked)],
            env=environment, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__=='__main__':unittest.main()
