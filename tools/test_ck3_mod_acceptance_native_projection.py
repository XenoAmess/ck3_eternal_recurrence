"""Portable predecessor projection checks; synthetic files only."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(1,str(Path.cwd()/'tools'))
spec=importlib.util.spec_from_file_location('acceptance_projection_under_test',HERE/'ck3_mod_acceptance_allocate.py')
allocation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(allocation)


class NativeProjectionTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.previous=Path(temporary.name)/'synthetic-run';self.previous.mkdir()
        self.freeze={'run_id':self.previous.name}
        self.native=self.previous/'native-report.json'
        self.host=self.previous/'host-original-process-exit.json'
        self.path=self.previous/'native-cleanup-projection.actual.json'
        self.report={'finished_at':'actual','managed_session_thread_finished':True,'cleanup_ok':True,'status':'RED',
            'session':{'report':{'finished_at':'actual','process_exit_code':1,'shutdown':{
                'ok':True,'cleanup_proven':True,'tree_gone':True,'job_active_processes_final':0,
                'contract_errors':[],'final_ck3_inventory':{'tasklist_returncode':0,'tasklist_pids':[],
                    'wmi_pids':[],'native_pids':[],'processes':[]},'control_files_absent':{'ck3.json':True}}}}}
        self.native.write_text(json.dumps(self.report),encoding='utf-8')
        self.host.write_text(json.dumps({'run_id':self.freeze['run_id'],'pid':123,'returncode':1,
            'actual_original_popen_wait':True}),encoding='utf-8')
        self.value={'schema':'lyd.native-cleanup-field-projection.v1','run_id':self.freeze['run_id'],
            'original_native_report':allocation.pin(self.native),'original_host_exit':allocation.pin(self.host),
            'projection':self.report}
        self.write(self.value)

    def write(self,value):
        self.path.write_text(json.dumps(value),encoding='utf-8')

    def test_projection_avoids_native_body_read_and_preserves_red_cleanup_guards(self):
        read_json=allocation.read_json;read_bytes=Path.read_bytes
        def bounded_json(path):
            self.assertNotEqual(Path(path).resolve(),self.native.resolve(),'native JSON must not be decoded')
            return read_json(path)
        def bounded_bytes(path):
            self.assertNotEqual(path.resolve(),self.native.resolve(),'native bytes must not be read or hashed')
            return read_bytes(path)
        with patch.object(allocation,'read_json',side_effect=bounded_json),patch.object(Path,'read_bytes',bounded_bytes):
            report,original,projection=allocation.previous_native_cleanup(self.previous,self.freeze)
            closure=allocation.previous_session_closure(self.previous,self.freeze,report,original)
            self.assertEqual(closure,{'mode':'previous-shared-managed-session'})
            self.assertEqual(report['status'],'RED')
            self.assertEqual(original,self.value['original_native_report'])
            self.assertEqual(projection,allocation.pin(self.path))
            wrong=copy.deepcopy(self.value)
            wrong['projection']['session']['report']['shutdown']['job_active_processes_final']=1
            self.write(wrong)
            report,original,_=allocation.previous_native_cleanup(self.previous,self.freeze)
            with self.assertRaisesRegex(ValueError,'closure unproven'):
                allocation.previous_session_closure(self.previous,self.freeze,report,original)

    def test_crossed_projection_bindings_reject_and_absence_keeps_legacy_report(self):
        variants=[]
        wrong=copy.deepcopy(self.value);wrong['run_id']='other';variants.append(wrong)
        wrong=copy.deepcopy(self.value);wrong['original_native_report']['path']=str(self.previous/'other.json');variants.append(wrong)
        wrong=copy.deepcopy(self.value);wrong['original_native_report']['bytes']+=1;variants.append(wrong)
        wrong=copy.deepcopy(self.value);wrong['original_native_report']['sha256']='invalid';variants.append(wrong)
        wrong=copy.deepcopy(self.value);wrong['original_host_exit']['path']=str(self.previous/'other-host.json');variants.append(wrong)
        wrong=copy.deepcopy(self.value);wrong['original_host_exit']['sha256']='0'*64;variants.append(wrong)
        for wrong in variants:
            with self.subTest(binding=wrong):
                self.write(wrong)
                with self.assertRaises(ValueError):
                    allocation.previous_native_cleanup(self.previous,self.freeze)
        self.write(self.value)
        self.host.write_text(json.dumps({'run_id':'other','returncode':1,'actual_original_popen_wait':True}),encoding='utf-8')
        self.value['original_host_exit']=allocation.pin(self.host);self.write(self.value)
        with self.assertRaisesRegex(ValueError,'original host wait differs'):
            allocation.previous_native_cleanup(self.previous,self.freeze)
        self.path.unlink()
        with patch.object(allocation,'read_json',wraps=allocation.read_json) as reader:
            report,original,projection=allocation.previous_native_cleanup(self.previous,self.freeze)
        reader.assert_called_once_with(self.native)
        self.assertEqual(report,self.report);self.assertIsNone(original);self.assertIsNone(projection)


if __name__=='__main__':
    unittest.main(verbosity=2)
