"""Focused production enqueue tests with the selected host's actual pure predicates."""
from pathlib import Path
from unittest import mock
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent
QUEUE = Path(__file__).with_name('ck3_mod_acceptance_queue.py')
HOST = REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
TOOLS = QUEUE.parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FailureShutdownQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(TOOLS))
        cls.queue = load(QUEUE, '_targeted_failure_shutdown_queue')
        source = HOST.read_text(encoding='utf-8-sig')
        names = {'finished_native_process_exit_zero_proof', 'finished_native_exit_zero_proof',
                 'finished_native_failure_shutdown_proof'}
        nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name in names]
        if {node.name for node in nodes} != names or len(nodes) != 3:
            raise ValueError('Real selected host dependency closure missing')
        cls.host_source = '\n\n'.join(ast.get_source_segment(source,node) for node in nodes)+'\n'

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='queue-failure-shutdown-')
        self.addCleanup(temp.cleanup)
        self.live = Path(temp.name).resolve()
        (self.live/'controls').mkdir()
        self.host = self.live/'actual_host_predicates.py'
        self.host.write_text(self.host_source, encoding='utf-8', newline='\n')
        self.pipe = r'\\.\pipe\queue-failure-shutdown-test'
        self.frozen = {'argv':['python', str(self.host), '--agent-source-root', str(self.live),
                              '--bridge-pipe', self.pipe, '--control-plan-dir', str(self.live/'controls')],
                       'state_dir':str(self.live), 'source_root':str(self.live), 'run_id':self.live.name,
                       'files':{str(self.host):self.queue.pin(self.host)}}
        shutdown = {'ok':True, 'cleanup_proven':True, 'tree_gone':True, 'ck3_pid':2088, 'ck3_exit_code':0,
                    'job_active_processes_final':0, 'contract_errors':[], 'watchdog_state_after':'absent',
                    'nonce':'a'*32, 'ck3_creation_date':'20261011121213.120782+000',
                    'control_files_absent':{'session.stop':True},
                    'final_ck3_inventory':{'tasklist_returncode':0, 'tasklist_pids':[], 'wmi_pids':[],
                                           'native_pids':[], 'processes':[]}}
        native = {'kind':'ck3_native_headless_session', 'mode':'native-headless', 'format_version':1,
                  'ok':True, 'error':None, 'exit_reason':'process_exit', 'process_exit_code':0,
                  'pid':2088, 'pipe':self.pipe, 'started_at':'2026-10-11T12:12:13+00:00',
                  'finished_at':'2026-10-11T12:30:00+00:00', 'shutdown':shutdown}
        self.report = {'fixture_only':False, 'error':'preserved campaign pause readback failure',
                       'managed_session_done':True, 'managed_session_thread_finished':True,
                       'pipe':self.pipe, 'session':{'error':None, 'report':native}, 'phase':'hold',
                       'state_dir':str(self.live), 'agent_source_root':str(self.live),
                       'hold_until_utc_estimated':200.0, 'steps':[],
                       'mcp_tools':{'tools':[{'name':'readonly', 'inputSchema':{'type':'object'}}]}}
        self.patchers = [mock.patch.object(self.queue,'frozen_run',return_value=(self.frozen,{'keeper_root':str(self.live)})),
                        mock.patch.object(self.queue,'live_lease',return_value={'lease':{'task_id':'same-owner'}}),
                        mock.patch.object(self.queue,'stable_report',side_effect=lambda _:self.report),
                        mock.patch.object(self.queue.time,'time',return_value=100.0)]
        for patcher in self.patchers:
            patcher.start(); self.addCleanup(patcher.stop)

    def enqueue(self, flag=True, *, include=True):
        step = {'id':'new-lifecycle-only', 'kind':'finish_hold'}
        if include:
            step['failure_shutdown'] = flag
        plan = self.live/'plan.json'
        plan.write_text(json.dumps({'steps':[step]}),encoding='utf-8')
        return self.queue.enqueue(self.live, plan, 'new-lifecycle-only.json')

    def test_explicit_failure_uses_real_host_proof_and_once_publication(self):
        before = copy.deepcopy(self.report)
        result = self.enqueue()
        self.assertEqual(result['status'],'QUEUED_ONCE_ACK_NOT_BUSINESS_PASS')
        self.assertIs(result['business_pass'],False)
        self.assertEqual(self.report,before)
        self.assertIsNone(self.queue.native_zero_proof(self.frozen,self.report))
        proof = self.queue.native_zero_proof(self.frozen,self.report,failure_shutdown=True)
        self.assertEqual(proof['status'],'failure_shutdown_lifecycle_only')
        self.assertIs(proof['normal_close_qualified'],False)
        self.assertEqual(proof['process_exit_zero_proof']['pid'],2088)
        claims = list((self.live/'control-once-ledger').iterdir())
        with self.assertRaisesRegex(ValueError,'already exists'):
            self.enqueue()
        self.assertEqual(list((self.live/'control-once-ledger').iterdir()),claims)

    def test_default_and_false_preserve_error_rejection_before_claim(self):
        for include in (False,True):
            with self.subTest(include=include), self.assertRaisesRegex(ValueError,'native-zero predicate'):
                self.enqueue(False,include=include)
        self.assertFalse((self.live/'control-once-ledger').exists())

    def test_failure_requires_thread_and_native_cleanup_exit_zero(self):
        original = copy.deepcopy(self.report)
        changes = [('thread',False),('exit',1),('cleanup',False),('error',None)]
        for kind,value in changes:
            self.report = copy.deepcopy(original)
            if kind=='thread': self.report['managed_session_thread_finished']=value
            elif kind=='exit': self.report['session']['report']['process_exit_code']=value
            elif kind=='cleanup': self.report['session']['report']['shutdown']['cleanup_proven']=value
            else: self.report['error']=value
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError,'native-zero predicate'):
                self.enqueue()
            self.assertFalse((self.live/'control-once-ledger').exists())

    def test_nonliteral_failure_flags_reject_before_claim(self):
        for flag in (1,'true',None):
            with self.subTest(flag=flag), self.assertRaisesRegex(ValueError,'literal boolean'):
                self.enqueue(flag)
        self.assertFalse((self.live/'control-once-ledger').exists())

    def test_legacy_normal_exit_route_remains_accepted(self):
        self.report['error']=None
        self.report['managed_session_thread_finished']=False
        result = self.enqueue(include=False)
        self.assertEqual(result['status'],'QUEUED_ONCE_ACK_NOT_BUSINESS_PASS')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--queue',type=Path)
    parser.add_argument('--host',type=Path)
    parser.add_argument('--tools',type=Path)
    args=parser.parse_args()
    QUEUE=args.queue or QUEUE
    HOST=args.host or HOST
    TOOLS=args.tools or TOOLS
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(FailureShutdownQueue)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
