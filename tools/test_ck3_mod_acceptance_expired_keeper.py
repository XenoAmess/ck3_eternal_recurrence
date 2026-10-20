"""Offline failed-live resource recovery, preserving unknown keeper/CK3 exits."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ck3_mod_acceptance_allocate as allocation


class ExpiredKeeperResourceClosureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.machine = 'desktop-test-abc'
        self.run = self.root/(self.machine+'--vanilla--R0215'); self.run.mkdir()
        self.keeper = self.root/'keeper'; self.keeper.mkdir()
        self.state = self.root/'state'; self.state.mkdir()
        self.task_id = 'screen-a220'
        self.freeze = dict(run_id=self.run.name, screen_task=self.task_id, state_dir=str(self.state),
            identity_allocation=dict(machine_id=self.machine, state_root=str(self.root/'ids')),
            argv=['python','-B','-X','utf8',str(self.root/'host.py')], runtime_manifest={'source':'original'})
        frozen = self.write(self.run/'frozen-argv.json', self.freeze)
        prepared = self.write(self.root/'prepared.json', dict(startup={'state_dir':str(self.state)},
                                                           runtime_manifest=self.freeze['runtime_manifest']))
        refs = dict(frozen_argv=frozen, prepared_case=prepared)
        refs['ready_context'] = self.write(self.run/'ready-context.json', dict(run_id=self.run.name,
            run_dir=str(self.run), keeper_root=str(self.keeper), prepared_case=prepared, frozen_argv=frozen))
        refs['host_started'] = self.write(self.run/'host-started.json', dict(run_id=self.run.name,
            pid=11, create_time=1.5, supervisor_pid=14, actual_popen_retained=True, argv=self.freeze['argv']))
        refs['host_exit'] = self.write(self.run/'host-original-process-exit.json', dict(run_id=self.run.name,
            pid=11, returncode=0, actual_original_popen_wait=True, normal_ck3_exit_inferred=False))
        refs['host_supervisor'] = self.write(self.run/'host-supervisor-started.json', dict(pid=15,
            argv=['launcher.py','--supervise','--run-root',str(self.run),'--keeper-root',str(self.keeper)]))
        self.bus_dir = self.root/'bus'
        refs['keeper_process'] = self.write(self.run/'keeper-process.json', dict(pid=12,create_time=2.5,
            argv=['keeper.py','--root',str(self.keeper),'--task',self.task_id,'--bus-dir',str(self.bus_dir)]))
        refs['retained_identity'] = self.write(self.run/'case-output/retained-current-process-identity.json',
                                              dict(pid=13,create_time=3.5))
        refs['normal_close'] = self.write(self.run/'case-output/normal-close-result.json',
            dict(normal_close_qualified=False, business_pass=False,
                 retained_handle=dict(pid=13,create_time=3.5,actual_retained_os0=False)))
        self.handover_path = self.root/'handover.json'
        self.handover = dict(machine_id=self.machine, observed_at_utc='2026-10-20T01:57:10+00:00',
            keeper_final_report_exists=False, normal_close_qualified=False,
            leaves=[dict(path=refs[key]['path'],source_machine_id=self.machine,
                         source_sha256=refs[key]['sha256'],bytes=refs[key]['bytes'])
                    for key in ('host_exit','normal_close')])
        refs['handover_snapshot'] = self.write(self.handover_path,self.handover)
        self.prior = dict(schema='codex.task_bus.v1',task_id=self.task_id,sequence=7124,
                          state='running',resources=['ck3-screen:acquired'],timestamp_utc='2026-10-19T17:26:35+00:00')
        self.event = dict(schema='codex.task_bus.v1',task_id=self.task_id,sequence=7127,
            kind='status',state='waiting',resources=[],timestamp_utc='2026-10-20T01:50:29+00:00',
            retirement=dict(kind='expired-own-claim-released',prior_sequence=7124,business_status='unresolved_red'))
        self.task = dict(schema='codex.task_bus.v1',task_id=self.task_id,last_sequence=7127,state='waiting',resources=[])
        self.release_path = self.root/'release.json'
        self.bundle = dict(schema='ck3-mod-acceptance-failed-live-resource-closure-v1',run_id=self.run.name,
            keeper_root=str(self.keeper),machine_id=self.machine,observed_at_utc='2026-10-20T02:30:00+00:00',
            closure_kind='expired-keeper-missing-final-report',keeper_final_report_missing=True,
            normal_close_qualified=False,typed_normal_exit_proven=False,business_pass=False,release_pass=False,
            original_evidence=refs)
        self.close_path = self.root/'closure.json'; self.seal_bus()
        self.bus = {'tasks':[self.task]}; self.live=set(); self.blockers=[]
        class MissingProcess(Exception):pass
        def process(pid):
            if pid not in self.live: raise MissingProcess()
            return SimpleNamespace(create_time=lambda:{11:1.5,12:2.5,13:3.5}[pid])
        self.psutil=SimpleNamespace(Process=process,NoSuchProcess=MissingProcess,
            pid_exists=lambda pid:pid in self.live,process_iter=lambda fields:[])

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value)+'\n',encoding='utf-8')
        return allocation.pin(path)

    def save(self):self.write(self.close_path,self.bundle)

    def seal_bus(self):
        old=(json.dumps(self.prior)+'\n').encode('utf-8'); raw=(json.dumps(self.event)+'\n').encode('utf-8')
        self.bus_dir.mkdir(exist_ok=True);(self.bus_dir/'events.jsonl').write_bytes(old+raw)
        task_pin=self.write(self.bus_dir/'tasks'/(self.task_id+'.json'),self.task)
        value=dict(schema='xar-screen-release-canonical-reconstruction-v1',source_event_stream=str(self.bus_dir/'events.jsonl'),
            source_event_byte_offset=len(old),source_event_bytes=len(raw),source_event_raw_utf8=raw.decode('utf-8'),
            source_event_raw_sha256=hashlib.sha256(raw).hexdigest(),event=self.event,actual_task_pin=task_pin,
            task=self.task,release_confirmed_by_canonical_readback=True)
        self.bundle['original_evidence']['release']=self.write(self.release_path,value)
        self.bundle['retired_prior_event']=dict(byte_offset=0,bytes=len(old),sha256=hashlib.sha256(old).hexdigest())
        self.save()

    def check(self):
        original=allocation.read_json
        def bounded(path):
            if Path(path).name in ('native-report.json','xar_checkpoint.ck3'):raise AssertionError('Heavy source body read')
            return original(path)
        with patch.dict(sys.modules,{'psutil':self.psutil}),patch.object(allocation,'read_json',side_effect=bounded),\
             patch.object(allocation,'runtime_process_inventory',return_value={'blockers':self.blockers}):
            return allocation.previous_failed_live_resource_closure(self.run,self.freeze,self.close_path,
                                                                   self.keeper,self.release_path,self.bus)

    def test_host_zero_and_missing_keeper_admit_only_resources(self):
        result=self.check(); proof=result['failure_cleanup']
        self.assertEqual(result['mode'],'previous-shared-failed-live-expired-keeper-resource-closed')
        self.assertEqual((proof['retired_prior_sequence'],proof['retirement_sequence']),(7124,7127))
        self.assertEqual(proof['original_host_exit_code'],0)
        for key in ('normal_close_qualified','typed_normal_exit_proven','business_pass','release_pass',
                    'original_keeper_wait_proven','keeper_thread_exit_proven','actual_retained_os0'):
            self.assertIs(proof[key],False)
        self.assertIsNone(proof['original_ck3_exit_code']); self.assertIsNone(proof['native_cleanup_qualified'])

    def test_original_identities_and_supervisors_must_be_absent(self):
        for pid in (11,12,13,14,15):
            with self.subTest(pid=pid):
                self.live={pid}
                with self.assertRaisesRegex(ValueError,'still present'):self.check()

    def test_current_runtime_and_screen_owners_block_admission(self):
        self.blockers=[{'pid':999,'name':'ck3.exe'}]
        with self.assertRaisesRegex(ValueError,'still running'):self.check()
        self.blockers=[]; self.bus['tasks'].append({'resources':['ck3-screen:acquired']})
        with self.assertRaisesRegex(ValueError,'screen owner'):self.check()

    def test_retirement_must_bind_exact_expired_prior_sequence_and_negative_status(self):
        for change in ({'prior_sequence':7123},{'business_status':'GREEN'},{'kind':'normal-close'}):
            with self.subTest(change=change):
                self.event['retirement']=dict(kind='expired-own-claim-released',prior_sequence=7124,business_status='unresolved_red')
                self.event['retirement'].update(change);self.seal_bus()
                with self.assertRaisesRegex(ValueError,'retirement'):self.check()

    def test_fresh_prior_claim_is_not_expired_recovery(self):
        self.prior['timestamp_utc']='2026-10-20T01:49:00+00:00';self.seal_bus()
        with self.assertRaisesRegex(ValueError,'exact expired claim'):self.check()

    def test_canonical_event_stream_mutation_is_rejected(self):
        raw=(self.bus_dir/'events.jsonl').read_bytes().replace(b'waiting',b'running')
        (self.bus_dir/'events.jsonl').write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'canonical event stream'):self.check()

    def test_current_task_must_remain_exact_retired_epoch(self):
        self.task['last_sequence']=7128
        with self.assertRaisesRegex(ValueError,'current bus task'):self.check()

    def test_cross_machine_or_frozen_run_is_rejected(self):
        self.bundle['machine_id']='other';self.save()
        with self.assertRaisesRegex(ValueError,'identity'):self.check()

    def test_handover_must_pin_actual_negative_original(self):
        self.handover['leaves'][0]['source_sha256']='0'*64
        self.bundle['original_evidence']['handover_snapshot']=self.write(self.handover_path,self.handover);self.save()
        with self.assertRaisesRegex(ValueError,'handover source pin'):self.check()

    def test_existing_keeper_report_is_not_bypassed(self):
        self.write(self.keeper/'report.json',{})
        with self.assertRaisesRegex(ValueError,'replace existing keeper evidence'):self.check()

    def test_normal_credit_cannot_be_upgraded(self):
        self.bundle['normal_close_qualified']=True;self.save()
        with self.assertRaisesRegex(ValueError,'negative qualification'):self.check()

    def test_stale_process_controls_reject_resource_admission(self):
        self.write(self.state/'control/ck3.json',{})
        with self.assertRaisesRegex(ValueError,'controls remain'):self.check()

    def test_public_allocate_reaches_validated_retirement_without_keeper_report_or_closed_lease(self):
        script=self.root/'dummy.py';script.write_text('pass',encoding='utf-8')
        bus_script=self.bus_dir/'bin/codex_task_bus.py';bus_script.parent.mkdir();bus_script.write_text('pass',encoding='utf-8')
        selection=SimpleNamespace(prepared_path=self.root/'prepared-new.json',context=None,
            runtime={'allocation':dict(lease_repo=str(self.root),screen_keeper=allocation.pin(script),
                                      task_bus=allocation.pin(bus_script),task_prefix='new-screen-'),
                     'reviewed_launcher':allocation.pin(script)},
            locations={'repo_root':self.root},runtime_path=self.root/'runtime.json',state_dir=self.root/'next/state',
            preflight=lambda:{'blockers':[]})
        args=SimpleNamespace(attempt='a01',keeper_output=self.root/'new-keeper',previous_release=self.release_path,
            previous_live=self.run,previous_keeper=self.keeper,previous_failure_close=self.close_path,
            first_machine_bootstrap=None,latest_screen_release=None)
        class RouteReached(Exception):pass
        with patch.object(allocation,'path_at',side_effect=lambda p,b:Path(p)),\
             patch.object(allocation,'actual_machine_binding',return_value=self.freeze['identity_allocation']),\
             patch.object(allocation,'shared_bus_history',return_value=([],[])),\
             patch.object(allocation,'current_screen_absent',return_value=self.bus),\
             patch.object(allocation,'closed_lease',side_effect=AssertionError('Missing keeper must not be invented')),\
             patch.object(allocation,'require_latest_screen_release',side_effect=RouteReached),\
             patch.dict(sys.modules,{'psutil':self.psutil}),\
             patch.object(allocation,'runtime_process_inventory',return_value={'blockers':[]}):
            with self.assertRaises(RouteReached):allocation.allocate_and_keep(selection,args)
            self.bundle.pop('closure_kind');self.save()
            with self.assertRaises(FileNotFoundError):allocation.allocate_and_keep(selection,args)


if __name__=='__main__':unittest.main(verbosity=2)
