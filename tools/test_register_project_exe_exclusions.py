from pathlib import Path
import copy
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import register_project_exe_exclusions as m


class FakeWmi:
    def __init__(self, paths=None, retval=0, append=True, overwrite=False, failure=None):
        self.paths=list(paths or []);self.retval=retval;self.append=append
        self.overwrite=overwrite;self.failure=failure;self.calls=[]
    def read_paths(self):return list(self.paths)
    def add_path(self,path):
        self.calls.append(path)
        if self.failure:raise self.failure
        if self.overwrite:self.paths=[]
        if self.append:self.paths.append(path)
        return self.retval


class RegistrationTest(unittest.TestCase):
    def setUp(self):
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
    def write_metadata(self):
        for name,obj in [('index-test.json',self.index),('model.json',self.model),('target.json',self.target),
                         ('lib.json',{'id':'lib','name':'library','type':'STATIC_LIBRARY','paths':{'source':'.'},'artifacts':[]})]:
            (self.reply/name).write_text(json.dumps(obj))
    def collect(self):return m.collect_manifest(self.repo,self.source,self.build,'Release',['fixture'])
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

if __name__=='__main__':unittest.main()
