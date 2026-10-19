"""Focused in-memory C18 source checks, with no new OS children/Native/Game.

The actual src14 supplies all unchanged dependencies. The optional seven M7
leaves and five exact seam edits are imported from an in-memory source overlay.
Only fixture owner epoch reads use the composed source model: there are no C18
disk files from which a real source epoch could yet be qualified.
"""
from __future__ import annotations

import ast
import importlib.abc
import importlib.util
import io
import json
import linecache
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import prepare_c18_m7_cold_sdk_v1 as producer

REPO=producer.REPO
TESTS=REPO/'ck3_autonomous_player/tests/unit'
STATE={}


class MemorySource(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    def __init__(self,changed):
        self.sources={name[:-3].replace('/','.'):(name,raw) for name,raw in changed.items()}
        self.loaded=[]
    def find_spec(self,fullname,path=None,target=None):
        if fullname in self.sources:
            return importlib.util.spec_from_loader(fullname,self,
                origin=str(producer.BASE_ROOT/self.sources[fullname][0]))
        return None
    def create_module(self,spec):return None
    def get_source(self,fullname):return self.sources[fullname][1].decode()
    def exec_module(self,module):
        name,raw=self.sources[module.__name__]
        module.__file__=str(producer.BASE_ROOT/name)
        filename='<C18-inmemory-SDK/'+name+'>'
        linecache.cache[filename]=(len(raw),None,raw.decode().splitlines(keepends=True),filename)
        exec(compile(raw,filename,'exec',dont_inherit=True),module.__dict__)
        self.loaded.append({'module':module.__name__,'relative':name,**producer.exact.pin(raw)})


class C18SeamTests(unittest.TestCase):
    def test_default_runtime_callback_is_zero_work(self):
        from xar_autoplayer import runtime
        self.assertIsNone(runtime._apply_pre_native_resume_v1(object(),object(),None))
        with self.assertRaises(runtime.AgentError):
            runtime._apply_pre_native_resume_v1(SimpleNamespace(resumed=True),object(),lambda *a:None)

    def test_actual_preload_callback_retains_only_original_typed_controller(self):
        from xar_autoplayer import runtime
        import test_native_loaded_provider_custody_v1 as fixture
        facade,target,owner,driver,endpoint=fixture.context()
        resource=fixture.prepare(facade,target)
        config=SimpleNamespace(dll_path=fixture.DLL)
        actual=runtime._apply_pre_native_resume_v1(target,config,lambda p,c:resource)
        self.assertIs(actual,resource)
        self.assertIs(target._native_preload_custody_v1,resource)
        with self.assertRaises(runtime.AgentError):
            runtime._apply_pre_native_resume_v1(target,config,lambda p,c:{'qualified':True})
        resource.close()
        self.assertNotIn(facade.original,facade.closed)

    def test_pre_resume_hook_precedes_both_original_injection_branches(self):
        tree=ast.parse(STATE['changed'][producer.RUNTIME])
        launch=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='launch')
        hooks=[n for n in ast.walk(launch) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Name) and n.func.id=='_apply_pre_native_resume_v1']
        branches=[n for n in ast.walk(launch) if isinstance(n,ast.If)
                  and isinstance(n.test,ast.Name) and n.test.id=='native_bridge_after_saved_load']
        self.assertEqual(len(hooks),1)
        self.assertEqual(len(branches),1)
        self.assertLess(hooks[0].lineno,branches[0].lineno)
        self.assertIn('pre_native_resume',[a.arg for a in launch.args.kwonlyargs])
        self.assertIsNone(launch.args.kw_defaults[-1].value)

    def test_complete_unchanged_WAL_and_speed_dependencies_remain_exact(self):
        changed=STATE['changed'];rows={r['relative']:r for r in STATE['rows']}
        self.assertEqual(len(rows),1452)
        for name in ('bridge/driver_state_wal_v1.py','bridge/exact_day_speed_configuration_v1.py',
                     'bridge/driver_state_history_json.py','native_session.py','bridge/service.py','strategy.py'):
            relative='xar_autoplayer/'+name
            self.assertNotIn(relative,changed)
        self.assertEqual(rows['xar_autoplayer/bridge/driver_state_wal_v1.py']['sha256'],
            '8a738446148f33dd92d0e3489dfb002c675fb50b23e00320df11cbfad855324d')


def qualify():
    producer.exact.require(sys.dont_write_bytecode,'run -B')
    producer.exact.require(not any(n=='xar_autoplayer' or n.startswith('xar_autoplayer.')
        for n in sys.modules),'fresh source-only process required')
    changed,rows,plan=producer.compose()
    STATE.update(changed=changed,rows=rows)
    loader=MemorySource(changed)
    sys.meta_path.insert(0,loader);sys.path.insert(0,str(producer.BASE_ROOT));sys.path.insert(1,str(TESTS))
    temp_before=tempfile.tempdir
    tempfile.tempdir=str(REPO/'_runtime')
    try:
        from xar_autoplayer import successor_ui_pending_ledger_v1 as epoch
        model=epoch.digest(plan['candidate_epoch_inputs'])
        producer.exact.require(model==plan['candidate_epoch_synthetic_source_model'],'epoch source model differs')
        tests=[
            unittest.defaultTestLoader.loadTestsFromTestCase(C18SeamTests),
            unittest.defaultTestLoader.loadTestsFromName('test_player_heir_fixed_dynasty_projection_v1'),
            unittest.defaultTestLoader.loadTestsFromName('test_native_loaded_provider_custody_v1.GuardedIssuerTests'),
            unittest.defaultTestLoader.loadTestsFromName('test_native_loaded_provider_windows_v1.WindowsAdapterContractTests'),
            unittest.defaultTestLoader.loadTestsFromName('test_native_loaded_provider_receiver_v1.ReceiverContractTests'),
            unittest.defaultTestLoader.loadTestsFromName('test_player_heir_candidate_component_v1.OptionalPlayerHeirComponentTests'),
            unittest.defaultTestLoader.loadTestsFromName('test_native_bridge_runtime.NativeBridgeCreateProcessTests'),
            unittest.defaultTestLoader.loadTestsFromName('test_native_bridge_driver.NativeHeadlessGameplayDriverTests.test_disconnect_removes_semantic_state'),
            unittest.defaultTestLoader.loadTestsFromName('test_native_bridge_driver.NativeHeadlessGameplayDriverTests.test_close_does_not_loop_without_driver_state_storage'),
        ]
        output=io.StringIO()
        # The virtual files are intentionally not on disk. This models only
        # the exact proposed digest, never live filesystem source authority.
        with patch.object(epoch,'owner_source_epoch_v1',return_value=model):
            result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.TestSuite(tests))
        print(output.getvalue())
        producer.exact.require(result.wasSuccessful(),'focused composed C18 source tests failed')
        for name,module in list(sys.modules.items()):
            if name=='xar_autoplayer' or name.startswith('xar_autoplayer.'):
                path=getattr(module,'__file__',None)
                if path:
                    producer.exact.require(Path(path).resolve().is_relative_to(producer.BASE_ROOT.resolve()),
                        'dependency imported outside actual src14: '+name)
        plan['qualification']={'kind':'Focused actual src14 plus twelve in-memory leaves; synthetic Native/OS readback fixtures',
            'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'loaded_changed_modules':loader.loaded,'all_unchanged_production_imports_from_actual_src14':True,
            'epoch_fixture_model':{'digest':model,'production_source_authority_qualified':False,
                'scoped_mock':'owner_source_epoch_v1 returns composed-source model solely for detached owner fixture; no DTO/seal/source_verified field is altered.'},
            'new_children':0,'Game_RCP_Native_Task_calls':0,'D_output_or_Git_writes':0,
            'Driver_SAVE_body_reads':0,'actual_H':'unknown','actual_scoring_credit':0}
        plan['status']='FOCUSED_SOURCE_PASS_DEFAULT_OFF_NOT_ADOPTED'
        return plan
    finally:
        tempfile.tempdir=temp_before;sys.meta_path.remove(loader)


if __name__=='__main__':
    report=qualify()
    if len(sys.argv)==2:
        path=Path(sys.argv[1]).resolve()
        producer.exact.require(path.is_relative_to(REPO.resolve()),'small proof must remain in workspace')
        raw=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
        producer.exact.require(len(raw)<=48*1024,'small source proof limit')
        with path.open('xb') as stream:stream.write(raw)
        print(json.dumps({'proof':{'path':str(path),**producer.exact.pin(raw)}}))
    else:print(json.dumps(report,ensure_ascii=False,indent=2))
