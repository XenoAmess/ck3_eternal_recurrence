"""Three bounded software checks; recording documents are RAM fixtures, not admission."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from g2_saved_campaign import prepare_c22_normal_warm_controls_v1 as p

NEW_SID='11111111-2222-4333-8444-555555555555'
GAME_BIRTH=134368995759027619


def dump(node):return ast.dump(node,include_attributes=False)


def normalized(source):
    class Inverse(ast.NodeTransformer):
        def mapped(self,value):
            for old,new in p.PAIRS:value=value.replace(new,old)
            return value
        def visit_Constant(self,node):
            if isinstance(node.value,str):node.value=self.mapped(node.value)
            return node
        def visit_ImportFrom(self,node):
            if node.module:node.module=self.mapped(node.module)
            return node
        def visit_ClassDef(self,node):
            if node.name=='P37C22oldReadyQueue':node.name='P37C21oldReadyQueue'
            return self.generic_visit(node)
        def visit_Name(self,node):
            if node.id=='P37C22oldReadyQueue':node.id='P37C21oldReadyQueue'
            return node
    return Inverse().visit(ast.parse(source))


def function(source,name):
    return next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)


def methods(source):
    make=function(source,'make_normal_source_warm_queue_v1')
    cls=next(n for n in make.body if isinstance(n,ast.ClassDef))
    return {n.name:n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}


def fixture():
    """Only the new metadata pairing layer is exercised; no live verifier is stubbed."""
    root=p.T/'recordings'/NEW_SID
    values={}
    def add(path,value):
        raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
        ref={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        values[str(path)]=(ref,value)
        return ref
    pub=add(p.T/'decision-text-publisher-c16/STARTED.json',
        {'RAM_FIXTURE':True,'publisher':{'pid':53688,'creation_filetime':134368999873257432}})
    request=add(root/'requested.json',{'session_id':NEW_SID,'receipt_root':str(root),
        'worker_pid':123456,'worker_creation_filetime':134369000000000001})
    job=add(root/'job.json',{'session_id':NEW_SID,'receipt_root':str(root),'pid':30852,
        'game_creation_filetime':GAME_BIRTH,'decision_text_publisher_receipt':pub})
    started=add(root/'started.json',{'state':'recording','game_pid':30852,'game_creation_filetime':GAME_BIRTH})
    first=add(p.T/'ROOT-SAVED-MAP-RECORDING-ADMITTED-C22-RAM-FIXTURE.json',
        {'status':'GREEN','machine_id':p.MACHINE,'game_pid':30852,'game_creation_filetime':GAME_BIRTH,
         'recorder_session_id':NEW_SID,'recording_job_root':str(root),'publisher_started':pub})
    previous=add(p.T/'recordings'/p.OLD_RECORD/'capture_closed.json',
        {'schema':'xar.ck3.capture-closed-before-media-hash/v1','session_id':p.OLD_RECORD,
         'game_pid':30852,'game_creation_filetime':GAME_BIRTH,'inputs_unbound':True,
         'engine_close':{'actual_exit_code':0,'normal_exit_proven':True,'forced_process_calls':0}})
    binding=add(p.T/'ROOT-C22-RECORDING-BINDING-RAM-FIXTURE.json',
        {'schema':'xar.C22-actual-recording-binding/v1','machine_id':p.MACHINE,
         'status':'ACTUAL_NEW_RECORDING_READY','Game_pid':30852,'Game_creation_filetime':GAME_BIRTH,
         'session_id':NEW_SID,'request':request,'job':job,'started':started,
         'first_frame_admission':first,'publisher_started':pub,'previous_capture_closed':previous})
    admission={'recording_binding':binding,'boundary':{'Game_pid':30852,'Game_creation_filetime':GAME_BIRTH},
        'queue_source':{'path':str(p.T/'root_p37c22_sdk_queue.py')}}
    def read(ref,limit=262144):
        expected,value=values[ref['path']]
        if ref!=expected or ref['bytes']>limit:raise ValueError('RAM fixture pin differs')
        return copy.deepcopy(value)
    return admission,values,read


class C22Source(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph,cls.report=p._source_graph_v1()
        spec=importlib.util.spec_from_file_location('_qualification_C21_predecessor',p.C21)
        cls.old=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.old)
        cls.before,_=cls.old._source_graph_v1()

    def test_01_actual_Source22_and_unchanged_five_controls(self):
        actual=p.checked_document({'path':str(p.T/'ROOT-FINAL-SDK-FREEZE-P37C22.json'),
            'bytes':449181,'sha256':'07fe7edd6bf76cf7a3c2c438de9d13178ced61c00f1d701b748745f4bc33e443'},524288)
        self.assertEqual(actual['business_source_commit'],p.COMMIT)
        self.assertEqual((actual['source_file_count'],actual['source_bytes'],len(actual['files'])),(1449,59095358,1449))
        self.assertEqual(Path(actual['source_root']),Path(self.report['business']['source_root']))
        self.assertFalse(actual['clean_campaign']);self.assertTrue(actual['prior_campaign_state_or_credits_inherited'])
        self.assertEqual(Path(self.report['business']['reference_source_root']).parts[-2:],('reference-c22','src'))
        self.assertEqual(self.report['old_45_protected_constants_verified_before_explicit_recording_hunks'],45)
        self.assertEqual(self.report['classifier_sha256'],'0bff8fae24c072d5f05285ba62c503dfed408f8095690fb8dffec16fe72ec28b')
        for name,source in self.graph.items():
            compile(source,name,'exec')
            oldname=name
            for old,new in p.PAIRS:oldname=oldname.replace(new,old)
            if not (name.startswith('launch_sdk_') or name.endswith('_warm_resume.py')):
                with self.subTest(name=name):self.assertEqual(dump(normalized(source)),dump(ast.parse(self.before[oldname])))
        queue=self.graph['root_p37c22_sdk_queue.py'].decode()
        self.assertEqual(queue.count(self.old.WAL_HUNK),1)
        # Same original strict optional env policy, without re-running old child-process tests.
        hunk=ast.parse(self.old.WAL_HUNK.strip().splitlines()[0]+'\n')
        self.assertIsInstance(hunk.body[0],ast.Assign)
        factory=self.graph['root_p37c22_warm_resume.py'].decode()
        oldfactory=self.before['root_p37c21_warm_resume.py'].decode()
        for name in ('normal_warm_inputs','require','checked'):
            self.assertEqual(dump(function(factory,name)),dump(function(oldfactory,name)))
        new_methods=methods(factory);old_methods=methods(oldfactory)
        for name in ('call','check_before'):
            self.assertEqual(dump(normalized(ast.unparse(new_methods[name])).body[0]),dump(old_methods[name]))
        self.assertEqual([n.module for n in ast.walk(ast.parse(factory)) if isinstance(n,ast.ImportFrom)
            and n.module=='root_continuous_segment_auto_c16'],['root_continuous_segment_auto_c16'])
        self.assertIn('self.job,self.record_started,self.first=verify_segment(',factory)
        self.assertIn("and freeze['source_file_count']==1449 and len(freeze['files'])==1449",factory)
        owner=self.graph['launch_sdk_p37c22_owner.py'].decode()
        for name in ('read','sha','write','verify_prepared_inputs'):
            self.assertEqual(dump(normalized(ast.unparse(function(owner,name))).body[0]),
                dump(function(self.before['launch_sdk_p37c21_owner.py'].decode(),name)))

    def test_02_new_recording_pairing_and_foreign_or_old_rejected(self):
        admission,values,read=fixture()
        reader=p._recording_reader_v1(self.graph['root_p37c22_warm_resume.py'],read)
        got=reader(admission)
        self.assertEqual(got['binding']['session_id'],NEW_SID)
        self.assertEqual(got['root'],p.T/'recordings'/NEW_SID)
        binding_key=admission['recording_binding']['path']
        binding=values[binding_key][1]
        cases=[(binding,'session_id',p.OLD_RECORD),
               (binding,'Game_creation_filetime',GAME_BIRTH+1),
               (binding,'machine_id','foreign-machine'),
               (values[binding['started']['path']][1],'state','closed'),
               (values[binding['first_frame_admission']['path']][1],'recorder_session_id',p.OLD_RECORD),
               (values[binding['previous_capture_closed']['path']][1]['engine_close'],'normal_exit_proven',False)]
        for target,key,bad in cases:
            original=target[key];target[key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):reader(admission)
            target[key]=original
        original=binding['first_frame_admission']
        binding['first_frame_admission']={**original,'path':str(p.T/'ROOT-SAVED-MAP-RECORDING-ADMITTED-C16.json')}
        with self.assertRaises((KeyError,ValueError)):reader(admission)
        binding['first_frame_admission']=original

    def test_03_public_source_chain_requires_explicit_new_recording(self):
        with self.assertRaises(ValueError):p.compose(recording_binding_ref=None,boundary={})
        admission,values,read=fixture()
        # Only JSON reading is RAM-injected. Real Source22 anchor, real predecessor,
        # namespace port, factory function extraction and public source chain run.
        with patch.object(p,'checked_document',read):
            graph,report=p.compose(recording_binding_ref=admission['recording_binding'],boundary=admission['boundary'])
        self.assertEqual(graph,self.graph)
        self.assertEqual(report['actual_new_recording_session'],NEW_SID)
        self.assertFalse(report['runtime_admitted']);self.assertFalse(report['outputs_materialized'])
        self.assertTrue(report['separate_clean_postclose_source_freeze_Task_and_runtime_admissions_required'])
        self.assertEqual(report['business']['commit'],p.COMMIT)
        self.assertEqual(report['business']['rows_sha256'],p.ROWS_SHA)
        self.assertFalse(report['business']['Native30_bound'])
        self.assertIn('UNKNOWN',report['business']['clock_root_cause'])


if __name__=='__main__':unittest.main(verbosity=2)
