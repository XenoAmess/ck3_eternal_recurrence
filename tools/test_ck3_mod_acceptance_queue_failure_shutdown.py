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
from jsonschema.exceptions import ValidationError

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

    def enqueue(self, flag=True, *, include=True, terminal_cleanup=False):
        step = {'id':'new-lifecycle-only', 'kind':'finish_hold'}
        if include:
            step['failure_shutdown'] = flag
        plan = self.live/'plan.json'
        plan.write_text(json.dumps({'steps':[step]}),encoding='utf-8')
        return self.queue.enqueue(self.live, plan, 'new-lifecycle-only.json', terminal_cleanup=terminal_cleanup)

    def test_ended_keeper_can_finish_actual_proved_cleanup_without_claiming_a_lease(self):
        self.frozen['screen_task'] = 'ended-keeper'
        (self.live/'report.json').write_text(json.dumps({'task_id':'ended-keeper',
            'thread_exited':True, 'entry_error':'checkout changed'}), encoding='utf-8')
        with mock.patch('psutil.process_iter', return_value=[]), mock.patch.object(
                self.queue, 'live_lease', side_effect=ValueError('keeper already ended')) as lease:
            result = self.enqueue(terminal_cleanup=True)
        lease.assert_not_called()
        self.assertIsNone(result['lease'])
        self.assertIs(result['terminal_cleanup']['normal_close_qualified'], False)
        self.assertEqual(result['terminal_cleanup']['native_failure_cleanup'][
            'process_exit_zero_proof']['pid'], 2088)
        self.assertTrue((self.live/'controls/new-lifecycle-only.json').is_file())

    def test_terminal_cleanup_refuses_game_commands_and_a_current_ck3(self):
        self.frozen['screen_task'] = 'ended-keeper'
        (self.live/'report.json').write_text(json.dumps({'task_id':'ended-keeper',
            'thread_exited':True}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'no game commands'):
            self.queue.terminal_cleanup_evidence(self.live, self.frozen, self.report,
                [{'id':'advance', 'kind':'advance_day', 'days':1}])
        process = mock.Mock(info={'name':'ck3.exe'})
        with mock.patch('psutil.process_iter', return_value=[process]), self.assertRaisesRegex(
                ValueError, 'while a CK3 process exists'):
            self.enqueue(terminal_cleanup=True)
        self.assertFalse((self.live/'control-once-ledger').exists())

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


class StoppedKeeperExitQueue(unittest.TestCase):
    """Actual publisher + original SDK contract; all process data is software-only."""
    @classmethod
    def setUpClass(cls):
        FailureShutdownQueue.setUpClass.__func__(cls)

    def setUp(self):
        FailureShutdownQueue.setUp(self)
        self.frozen['screen_task'] = 'original-stopped-owner'
        (self.live / 'case-output').mkdir()
        runtime = self.live / 'runtime'
        runtime.mkdir()
        sdk = self.live / 'ck3_autonomous_player/src/xar_autoplayer/bridge'
        sdk.mkdir(parents=True)
        indexed = {}
        for name in ('normal_exit_process_observer_v1', 'normal_exit_contract_v1',
                'normal_exit_public_wire_v2', 'normal_exit_host_terminal_v1', 'version_identity'):
            path = sdk / (name + '.py')
            path.write_bytes((TOOLS.parent / 'ck3_autonomous_player/src/xar_autoplayer/bridge' / path.name).read_bytes())
            reference = self.queue.pin(path)
            indexed[path.relative_to(self.live).as_posix()] = {key:reference[key] for key in ('bytes','sha256')}
        self.dump(runtime / 'source-index.json', {'schema':'ck3-common-source-index-v1','files':indexed})
        self.dump(runtime / 'manifest.json', {'schema':'software-original-runtime-fixture'})
        self.frozen['runtime_manifest'] = self.queue.pin(runtime/'manifest.json')
        self.frozen['files'][str(runtime/'source-index.json')] = self.queue.pin(runtime/'source-index.json')
        capabilities = ['game.command.normal-exit-application-v1']
        self.report['capabilities'] = {'bridge_capabilities':capabilities, 'diagnostics':{
            'pipe_name':self.pipe,'connected':True,'protocol_version':1,'bridge_pid':2088,
            'connection_generation':1,'hello':{'type':'hello','protocol_version':1,'pid':2088,
            'connection_generation':1,'capabilities':capabilities,'expected_ck3_version':'1.21.0',
            'expected_ck3_sha256':'2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc',
            'ck3_build_match':True,'game_adapter_id':'ck3-1.21.0-msvc-x64'}}}
        self.report['mcp_tools']['tools'] += [
            {'name':'ck3_query_normal_exit_context_v1','inputSchema':{'type':'object','additionalProperties':False}},
            {'name':'ck3_request_normal_exit_v1','inputSchema':{'type':'object'}},
            {'name':'ck3_observe_normal_exit_v1','inputSchema':{'type':'object','additionalProperties':False}}]
        self.intent = 'new-cleanup-intent'
        self.review = self.live/'cleanup-review.json'
        self.originals = {
            'frozen_argv':self.live/'frozen-argv.json','ready_context':self.live/'ready-context.json',
            'manual_quit':self.live/'case-output/manual-quit-awaiting.json',
            'normal_quit':self.live/'case-output/normal-quit-awaiting.json',
            'automation_failure':self.live/'case-output/normal-quit-typed-automation-failure-preserved.json',
            'keeper_report':self.live/'report.json','keeper_stop':self.live/'ROOT_STOP_REQUIRED.json'}
        self.dump(self.originals['frozen_argv'], {'software_fixture_only':True})
        self.dump(self.originals['ready_context'], {'software_fixture_only':True})
        common = {'run_id':self.live.name,'reviewer':'/root','pid':2088,
            'create_time':99.125,'original_hold_deadline':200.0}
        self.dump(self.originals['manual_quit'], {**common,'status':'MANUAL_QUIT_AWAITING_ORIGINAL_DEADLINE'})
        self.dump(self.originals['normal_quit'], {**common,'original_typed_exit_already_observed':False,
            'screen_task':self.frozen['screen_task'],'keeper_root':str(self.live)})
        self.dump(self.originals['automation_failure'], {'automation_replayed':False,'business_pass':False,
            'original_hold_deadline':200.0,'error':'ValueError: Original screen keeper no longer owns this held scene'})
        self.dump(self.originals['keeper_report'], {'task_id':self.frozen['screen_task'],'thread_exited':True,
            'entry_error':"RuntimeError('checkout changed')"})
        self.dump(self.originals['keeper_stop'], {'task_id':self.frozen['screen_task'],
            'reason':'Keeper failed; stop live actions'})
        self.dump(self.live/'qualification-wait.stderr', None, raw=b'Ran 7 tests in 0.01s\n\nOK\n')
        self.dump(self.live/'qualification-wait.json', {'actual_original_popen_wait':True,'returncode':0,
            'argv':['python',Path(__file__).resolve().as_posix(),'--queue',QUEUE.resolve().as_posix()],
            'stderr':self.queue.pin(self.live/'qualification-wait.stderr')})
        self.dump(self.live/'qualification.json', {'schema':'ck3-stopped-keeper-exit-software-v1',
            'queue_source':self.queue.pin(QUEUE),'test_source':self.queue.pin(Path(__file__)),
            'original_wait':self.queue.pin(self.live/'qualification-wait.json')})
        self.review_value = {'schema':'ck3-stopped-keeper-normal-exit-review-v1','reviewer':'/root',
            'run_id':self.live.name,'pid':2088,'birth_filetime':'134395395825978194',
            'original_hold_deadline':200.0,'originals':{key:self.queue.pin(path) for key,path in self.originals.items()},
            'software_qualification':self.queue.pin(self.live/'qualification.json')}
        self.dump(self.review,self.review_value)
        self.write_intent()

    def dump(self,path,value,*,raw=None):
        path.write_bytes(raw if raw is not None else json.dumps(value).encode())

    def write_intent(self):
        self.dump(self.live/'case-output'/ (self.intent+'-once.json'), {
            'schema':'ck3-stopped-keeper-normal-exit-once-v1','review':self.queue.pin(self.review),
            'pid':2088,'birth_filetime':'134395395825978194'})

    def publish(self,step,*,name='new-cleanup-intent-001.json',review=True):
        plan=self.live/'new-plan.json'
        self.dump(plan,{'steps':[step]})
        return self.queue.enqueue(self.live,plan,name,stopped_keeper_exit_review=self.review if review else None,
            stopped_keeper_exit_intent=self.intent if review else None)

    def query(self):
        return {'id':self.intent+'-001','tool':'ck3_query_normal_exit_context_v1','args':{}}

    def test_default_stopped_keeper_remains_blocked_and_reviewed_query_keeps_originals(self):
        originals={str(path):path.read_bytes() for path in self.originals.values()}
        with mock.patch.object(self.queue,'live_lease',side_effect=ValueError('ended keeper')) as lease:
            with self.assertRaisesRegex(ValueError,'ended keeper'):
                self.publish(self.query(),review=False)
            result=self.publish(self.query())
            self.assertEqual(lease.call_count,1)
        self.assertIsNone(result['lease'])
        self.assertIs(result['stopped_keeper_exit']['lease_renewed'],False)
        self.assertIs(result['business_pass'],False)
        self.assertEqual(originals,{str(path):path.read_bytes() for path in self.originals.values()})
        self.assertEqual(json.loads((self.live/'controls'/ (self.intent+'-001.json')).read_bytes())['steps'],[self.query()])

    def test_closed_sdk_contract_refuses_business_advance_save_and_bad_exit_arguments_before_claim(self):
        for step in ({'id':self.intent+'-001','kind':'advance_day','days':1},
                     {'id':self.intent+'-001','tool':'readonly','args':{}},
                     {'id':self.intent+'-001','tool':'ck3_request_normal_exit_v1','args':{'action':'save'}},
                     {'id':self.intent+'-001','tool':'ck3_observe_normal_exit_v1','args':{'pid':2088}}):
            with self.subTest(step=step),self.assertRaises((ValueError, ValidationError)):
                self.publish(step)
            self.assertFalse((self.live/'control-once-ledger').exists())

    def test_review_identity_deadline_types_and_keeper_originals_are_strict(self):
        for key,value in (('pid',True),('pid',2088.0),('pid',2089),('birth_filetime',134395395825978194),
                ('birth_filetime','0134395395825978194'),('original_hold_deadline',201.0),('reviewer','other'),
                ('run_id','foreign-run')):
            changed={**self.review_value,key:value}
            self.dump(self.review,changed)
            self.write_intent()
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                self.publish(self.query())
            self.assertFalse((self.live/'control-once-ledger').exists())
        self.dump(self.review,self.review_value)
        self.write_intent()
        self.dump(self.originals['keeper_stop'],{'task_id':'replaced','reason':'different'})
        with self.assertRaisesRegex(ValueError,'changed'):
            self.publish(self.query())
        self.assertFalse((self.live/'control-once-ledger').exists())

    def test_expired_hold_or_nonzero_qualification_never_claims(self):
        with mock.patch.object(self.queue.time,'time',return_value=200.0),self.assertRaisesRegex(ValueError,'deadline'):
            self.publish(self.query())
        waited=self.queue.read_json(self.live/'qualification-wait.json')
        waited['returncode']=1
        self.dump(self.live/'qualification-wait.json',waited)
        qual=self.queue.read_json(self.live/'qualification.json')
        qual['original_wait']=self.queue.pin(self.live/'qualification-wait.json')
        self.dump(self.live/'qualification.json',qual)
        self.review_value['software_qualification']=self.queue.pin(self.live/'qualification.json')
        self.dump(self.review,self.review_value)
        self.write_intent()
        with self.assertRaisesRegex(ValueError,'wait zero'):
            self.publish(self.query())
        self.assertFalse((self.live/'control-once-ledger').exists())

    def test_recheck_after_claim_refuses_changed_stop_and_preserves_unknown_claims(self):
        original=self.queue.claim_plan
        def changed(*args):
            result=original(*args)
            self.dump(self.originals['keeper_stop'],{'changed_after_claim':True})
            return result
        with mock.patch.object(self.queue,'claim_plan',side_effect=changed),self.assertRaisesRegex(ValueError,'changed'):
            self.publish(self.query())
        self.assertFalse(any((self.live/'controls').glob('*.json')))
        self.assertTrue(list((self.live/'control-once-ledger').glob('*.json')))
        self.assertTrue(list((self.live/'controls').glob('pending-*.tmp')))

    def test_previous_published_confirm_or_unknown_ledger_prevents_replay(self):
        confirm={'id':self.intent+'-002','tool':'ck3_request_normal_exit_v1',
            'args':{'action':'confirm_desktop','expected_revision':'1','expected_exit_context_signature':'a'*64},
            'fresh_revision':False}
        self.dump(self.live/'controls/old-confirm.json',{'steps':[confirm]})
        with self.assertRaisesRegex(ValueError,'already published or UNKNOWN'):
            self.publish(confirm,name=self.intent+'-002.json')
        (self.live/'controls/old-confirm.json').unlink()
        (self.live/'control-once-ledger').mkdir()
        self.dump(self.live/'control-once-ledger/unknown.json',{'outcome':'unknown'})
        with self.assertRaisesRegex(ValueError,'UNKNOWN claims'):
            self.queue._cleanup_no_previous_dispatch_v1(self.live,self.report)
        self.assertEqual(self.report['steps'],[])

    def test_review_replacement_after_claim_preserves_claim_without_publication(self):
        original=self.queue.claim_plan
        def changed(*args):
            result=original(*args)
            # Same semantics with different original bytes still cannot replace
            # the Root-reviewed admission between the two publication guards.
            self.review.write_text(json.dumps(self.review_value,indent=4),encoding='utf-8')
            return result
        with mock.patch.object(self.queue,'claim_plan',side_effect=changed),self.assertRaisesRegex(ValueError,'admission changed'):
            self.publish(self.query())
        self.assertFalse(any((self.live/'controls').glob('*.json')))
        self.assertTrue(list((self.live/'control-once-ledger').glob('*.json')))

    def test_original_sdk_claim_blocks_entry_even_without_host_or_queue_rows(self):
        self.queue._cleanup_no_sdk_claim_v1(self.live)
        directory=self.live/'native-session/normal-exit-map-requests'
        directory.mkdir(parents=True)
        self.dump(directory/'original-confirm.claim.json',{'status':'claimed_result_unknown_no_retry'})
        with self.assertRaisesRegex(ValueError,'confirmation claim exists'):
            self.queue._cleanup_no_sdk_claim_v1(self.live)
        self.assertEqual(self.report['steps'],[])
        self.assertFalse((self.live/'control-once-ledger').exists())

    def test_finish_uses_actual_host_predicate_but_never_claims_normal_business(self):
        result=self.publish({'id':self.intent+'-finish','kind':'finish_hold','failure_shutdown':True},
            name=self.intent+'-finish.json')
        self.assertIs(result['stopped_keeper_exit']['normal_close_qualified'],False)
        self.assertIsNone(result['lease'])
        # Same content/name cannot be repeated, even though the held scene remains.
        with self.assertRaisesRegex(ValueError,'already exists'):
            self.publish({'id':self.intent+'-finish','kind':'finish_hold','failure_shutdown':True},
                name=self.intent+'-finish.json')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--queue',type=Path)
    parser.add_argument('--host',type=Path)
    parser.add_argument('--tools',type=Path)
    args=parser.parse_args()
    QUEUE=args.queue or QUEUE
    HOST=args.host or HOST
    TOOLS=args.tools or TOOLS
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(FailureShutdownQueue),
        unittest.defaultTestLoader.loadTestsFromTestCase(StoppedKeeperExitQueue)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
