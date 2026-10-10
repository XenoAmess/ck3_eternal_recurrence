"""Portable native-zero extraction contract tests using actual shared host functions."""
import argparse
import ast
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent
QUEUE = Path(__file__).with_name('ck3_mod_acceptance_queue.py')
HOST = REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
PREDICATES = {'finished_native_process_exit_zero_proof','finished_native_exit_zero_proof'}


def require(ok,message):
    if not ok:
        raise ValueError(message)


def ref(path):
    raw = path.read_bytes()
    return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def check_pin(value):
    require(ref(Path(value['path'])) == {key:value[key] for key in ('bytes','sha256')},'Actual pinned host fixture changed')


class NativeZeroExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = HOST.read_text(encoding='utf-8-sig')
        tree = ast.parse(source)
        cls.original_nodes = [node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in PREDICATES]
        require(len(cls.original_nodes)==2 and {node.name for node in cls.original_nodes}==PREDICATES,
                'Actual shared host predicate dependency closure missing')
        cls.host_source = '\n\n'.join(ast.get_source_segment(source,node) for node in cls.original_nodes)+'\n'
        queue_tree = ast.parse(QUEUE.read_bytes())
        queue_nodes = [node for node in queue_tree.body if isinstance(node,ast.FunctionDef) and node.name=='native_zero_proof']
        require(len(queue_nodes)==1,'Actual queue extraction function missing')
        namespace = {'ast':ast,'copy':copy,'datetime':datetime,'Path':Path,'re':re,'require':require,'check_pin':check_pin}
        exec(compile(ast.Module(body=queue_nodes,type_ignores=[]),str(QUEUE),'exec'),namespace)
        cls.prove = staticmethod(namespace['native_zero_proof'])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ck3-native-zero-extraction-')
        self.addCleanup(self.temporary.cleanup)
        self.host = Path(self.temporary.name)/'selected_actual_host_predicates.py'
        self.host.write_text(self.host_source,encoding='utf-8',newline='\n')
        self.frozen = {'argv':['python',str(self.host),'--agent-source-root',str(self.host.parent)],
                       'files':{str(self.host.resolve()):ref(self.host)}}
        pipe = r'\\.\pipe\native-zero-extraction-test'
        shutdown = {'ok':True,'cleanup_proven':True,'tree_gone':True,'ck3_pid':2088,'ck3_exit_code':0,
                    'job_active_processes_final':0,'contract_errors':[],'watchdog_state_after':'absent',
                    'nonce':'a'*32,'ck3_creation_date':'20261010145226.556415+000',
                    'control_files_absent':{'session.stop':True},
                    'final_ck3_inventory':{'tasklist_returncode':0,'tasklist_pids':[],'wmi_pids':[],
                                           'native_pids':[],'processes':[]}}
        native = {'kind':'ck3_native_headless_session','mode':'native-headless','format_version':1,
                  'ok':True,'error':None,'exit_reason':'process_exit','process_exit_code':0,'pid':2088,'pipe':pipe,
                  'started_at':'2026-10-10T14:52:26+00:00','finished_at':'2026-10-10T15:20:00+00:00',
                  'shutdown':shutdown}
        self.report = {'fixture_only':False,'error':None,'managed_session_done':True,
                       'managed_session_thread_finished':True,'pipe':pipe,'session':{'error':None,'report':native}}

    def test_actual_host_dependency_is_executed(self):
        proof = self.prove(self.frozen,self.report)
        self.assertIsNotNone(proof)
        self.assertEqual(proof['pid'],2088)
        self.assertEqual(proof['process_exit_code'],0)
        self.assertEqual(proof['shutdown']['ck3_exit_code'],0)
        self.assertEqual(proof['reason'],'finished_native_process_exit_zero_cleanup_proven')
        self.assertIs(proof['alive_or_business_credit'],False)

    def test_top_level_error_still_rejects_normal_zero(self):
        self.report['error'] = 'preserved actual failure'
        self.assertIsNone(self.prove(self.frozen,self.report))

    def test_native_zero_cannot_replace_retained_os_nonzero(self):
        self.report['session']['report']['shutdown']['ck3_exit_code'] = 7
        self.assertIsNone(self.prove(self.frozen,self.report))

    def test_boolean_exit_code_does_not_mean_integer_zero(self):
        self.report['session']['report']['process_exit_code'] = False
        self.assertIsNone(self.prove(self.frozen,self.report))

    def test_crossed_native_pid_is_rejected(self):
        self.report['session']['report']['shutdown']['ck3_pid'] = 2089
        self.assertIsNone(self.prove(self.frozen,self.report))

    def test_missing_dependency_is_rejected_before_exec(self):
        wrappers = [node for node in self.original_nodes if node.name=='finished_native_exit_zero_proof']
        self.host.write_text(ast.unparse(wrappers[0])+'\n',encoding='utf-8',newline='\n')
        self.frozen['files'][str(self.host.resolve())] = ref(self.host)
        with self.assertRaisesRegex(ValueError,'dependency closure'):
            self.prove(self.frozen,self.report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--queue',type=Path)
    parser.add_argument('--host',type=Path)
    parser.add_argument('--dependency-only',action='store_true')
    args = parser.parse_args()
    QUEUE = args.queue or QUEUE
    HOST = args.host or HOST
    suite = unittest.TestSuite([NativeZeroExtraction('test_actual_host_dependency_is_executed')]) if args.dependency_only else unittest.defaultTestLoader.loadTestsFromTestCase(NativeZeroExtraction)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
