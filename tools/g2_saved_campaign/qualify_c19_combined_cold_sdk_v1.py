"""Small cross-package source checks; do not repeat prior M7/WAL matrices."""
import ast
import importlib
import importlib.abc
import importlib.util
import io
import json
import linecache
from pathlib import Path
import sys
import unittest

import prepare_c19_combined_cold_sdk_v1 as producer

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
        name,raw=self.sources[module.__name__];filename='<C19-combined-memory/'+name+'>'
        module.__file__=str(producer.BASE_ROOT/name)
        linecache.cache[filename]=(len(raw),None,raw.decode().splitlines(keepends=True),filename)
        exec(compile(raw,filename,'exec',dont_inherit=True),module.__dict__)
        self.loaded.append({'module':module.__name__,'relative':name,**producer.exact.pin(raw)})


class CombinedSourceSeams(unittest.TestCase):
    def test_both_WAL_fingerprints_match_after_M7_and_inverse_retains_M7(self):
        changed=STATE['changed']
        restored=producer.bounded.reverse_driver_bytes_v1(changed[producer.DRIVER])
        self.assertEqual(producer.bounded.method_fingerprints(restored),producer.bounded.METHODS)
        producer.exact.check_bytes(restored,(1638658,'330caa34eba442c0764c628499e979600bda2d58ea51b365cb4e4829b3db13ed'),
                                   'combined inverse M7 Driver')
        with self.assertRaises(ValueError):producer.bounded.transform_driver_bytes_v1(changed[producer.DRIVER])

    def test_finite_event_loader_exact_inverse_keeps_prior_1003_and_rejects_double_apply(self):
        data=STATE['changed'][producer.M2]
        for old,new in reversed(producer.m2_hunks()):
            self.assertEqual(data.count(new),1);data=data.replace(new,old,1)
        producer.exact.check_bytes(data,producer.M2_BASE,'combined finite loader inverse')
        with self.assertRaises(ValueError):
            producer.exact.transfer_exact_hunks(STATE['changed'][producer.M2],producer.m2_hunks())

    def test_epoch_is_joined_after_final_Driver_and_family_fix_is_not_a_delta(self):
        from xar_autoplayer import successor_ui_pending_ledger_v1 as epoch
        plan=STATE['plan'];rows={r['relative']:r for r in STATE['rows']}
        self.assertEqual(epoch.digest(plan['epoch_inputs']),plan['epoch_source_model'])
        self.assertEqual(plan['epoch_inputs']['bridge/native_driver.py'],
                         producer.exact.sha(STATE['changed'][producer.DRIVER]))
        self.assertNotEqual(plan['epoch_source_model'],'f47e6240d51324e384e9a17c73c6219275cad3f8864ebe5d159e9032ee53ee40')
        self.assertEqual(rows[producer.FAMILY]['sha256'],producer.FAMILY_PIN[1])
        self.assertNotIn(producer.FAMILY,STATE['changed'])

    def test_combined_imports_keep_old_root_without_optional_candidate(self):
        import test_player_heir_candidate_component_v1 as fixture
        from xar_autoplayer.bridge.campaign_root_context_contract import normalize_campaign_root_context_v1
        root=fixture.native_result(False)['campaign_root_context']
        normalized=normalize_campaign_root_context_v1(root,expected_date_raw=root['date_raw'],
            expected_snapshot_revision=root['snapshot_revision'])
        self.assertNotIn('player_heir_candidate_v1',normalized)
        self.assertEqual(normalized['snapshot_revision'],root['snapshot_revision'])

    def test_new_life_gate_does_not_admit_root_queries_or_unproved_multiday_results(self):
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        driver=object.__new__(NativeHeadlessGameplayDriver)
        driver._session_bridge_pid=123;driver._episode_character_id=7;driver._episode_run_id='native-7-synthetic-combined'
        self.assertFalse(driver._route_horizon_wal_eligible_v1('life-advance',{}))
        self.assertFalse(driver._route_horizon_wal_eligible_v1('research-query-campaign-root-context-v1',{}))


def qualify():
    producer.exact.require(sys.dont_write_bytecode,'run -B')
    producer.exact.require(not any(n=='xar_autoplayer' or n.startswith('xar_autoplayer.') for n in sys.modules),
                           'fresh source qualifier required')
    changed,rows,plan=producer.compose()
    STATE.update(changed=changed,rows=rows,plan=plan)
    sys.path.insert(0,str(producer.BASE_ROOT))
    sys.path.insert(1,str(producer.REPO/'ck3_autonomous_player/tests/unit'))
    loader=MemorySource(changed);sys.meta_path.insert(0,loader)
    try:
        for name in sorted(loader.sources):importlib.import_module(name)
        output=io.StringIO()
        result=unittest.TextTestRunner(stream=output,verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(CombinedSourceSeams))
        print(output.getvalue())
        producer.exact.require(result.wasSuccessful(),'combined source seam checks failed')
        for name,module in list(sys.modules.items()):
            if name=='xar_autoplayer' or name.startswith('xar_autoplayer.'):
                path=getattr(module,'__file__',None)
                if path:producer.exact.require(Path(path).resolve().is_relative_to(producer.BASE_ROOT.resolve()),
                    'production import escaped actual source15: '+name)
        producer.exact.require(len(loader.loaded)==15,'all combined leaves must import once')
        plan['qualification']={'kind':'Five new cross-package source checks plus full-base/hash/AST/inverse/compile/import checks',
            'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'prior_57_M7_10_WAL_12_timing_matrices_repeated':False,'loaded_changed_modules':loader.loaded,
            'all_other_production_imports_actual_source15':True,'source_epoch':'Candidate digest model only; no actual C19 filesystem authority or Native qualification.',
            'scratch_files':0,'new_children_Task_Game_Native_RPC':0,'D_Git_output_writes':0,
            'Driver_SAVE_ledger_body_reads':0,'actual_H':'unknown','actual_seconds_saved':None}
        plan['status']='CROSS_PACKAGE_SOURCE_PASS_DEFAULT_OFF_NOT_ADOPTED'
        return plan
    finally:sys.meta_path.remove(loader)


if __name__=='__main__':
    report=qualify()
    if len(sys.argv)==2:
        path=Path(sys.argv[1]).resolve();producer.exact.require(path.is_relative_to(producer.REPO.resolve()),'small proof outside workspace')
        raw=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
        producer.exact.require(len(raw)<=64*1024,'small proof limit')
        with path.open('xb') as stream:stream.write(raw)
        print(json.dumps({'proof':{'path':str(path),**producer.exact.pin(raw)}}))
    else:print(json.dumps(report,indent=2,ensure_ascii=False))
