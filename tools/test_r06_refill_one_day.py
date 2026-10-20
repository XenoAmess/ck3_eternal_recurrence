"""Focused public R06 ownership, finite observer and no-replay boundaries."""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
from datetime import datetime,timezone
import sys
import unittest
import argparse
import hashlib
import tempfile

REPO=Path(__file__).resolve().parents[1]
_parser=argparse.ArgumentParser(add_help=False)
_parser.add_argument('--scratch-root',type=Path)
_test_args,_remaining=_parser.parse_known_args()
sys.argv=[sys.argv[0],*_remaining]
sys.path[:0]=[str(REPO/'tools'),str(REPO/'ck3_autonomous_player/src')]
from ck3_mod_acceptance_cases import r06_refill_one_day as r06
from ck3_mod_acceptance_cases import r10_prepare_adapter as prep


def settings():
    return dict(scene_root='synthetic-scene',capacity_admission={},producer={},
        expected_source_save_sha256='a'*64,expected_start_date_raw=1000,source_province_id=6,
        actor_id=12,army_id=0,native_carmy_id=0,driver_limit_bytes=1024*1024,
        profile_limit_bytes=1024*1024,deadline_utc='2100-01-01T00:00:00Z',prefix='test-refill')


class R06BoundaryTests(unittest.TestCase):
    def test_same_path_rebuilt_observer_is_rejected_at_final_launch_boundary(self):
        with tempfile.TemporaryDirectory(dir=_test_args.scratch_root) as directory:
            path=Path(directory)/'observer.fixture'
            path.write_bytes(b'qualified original observer')
            producer=dict(observer_exe=str(path),observer_exe_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            verified=r06.verify_observer_bytes(path,producer)
            self.assertTrue(verified['actual_payload_rehashed_here'])
            path.write_bytes(b'rebuilt different observer')
            prepared=Path(directory)/'prepared.json';prepared.write_text('{}',encoding='utf-8')
            probe=r06.Probe.__new__(r06.Probe)
            probe.process=None;probe.path=prepared;probe.repo=REPO;probe.output=Path(directory)/'launch'
            claim=Mock()
            with patch.object(r06.subprocess,'Popen') as launch:
                with self.assertRaisesRegex(ValueError,'SHA differs from qualified Q/SYSTEM'):
                    probe.start(lambda:r06.verify_observer_bytes(path,producer),claim)
            launch.assert_not_called();claim.assert_not_called()
            self.assertFalse(getattr(probe,'launch_claimed',False))

    def test_camera_wait_does_not_extend_admission_ttl_or_reach_exe_launch(self):
        now=datetime.now(timezone.utc)
        expected=dict(machine_id='m',run_id='r',bridge_pid=1,process_creation_filetime=2,date_raw=100)
        sample=dict(observed_at_utc=now.isoformat(),complete=True,unresolved=[],os_list_count=1,generations=[[1,1001]])
        census=dict(machine_id='m',run_id='r',pid=1,process_creation_FILETIME=2,snapshots=[sample]*3)
        value=dict(**expected,schema='xar.r06.public_worker_source_admission.v1',observed_at_utc=now.isoformat(),
            maximum_owned_threads=2,birth_reserve_generations=1,thread_census={},latest_thread_snapshot=sample,
            actual_module=dict(pid=1,process_created_filetime=2,complete_module_metadata_enumeration=True,module={'path':'C:/bridge/xar_ck3_bridge.dll'}),
            native_qualification={'sha256':'q'},native_tree='t')
        producer=dict(carrier_module_path='C:/bridge/xar_ck3_bridge.dll',qualification={'sha256':'q'})
        with patch.object(r06,'checked',return_value=census):
            self.assertEqual(r06.validate_admission(value,expected=expected,producer=producer,native_tree='t'),2)
        with tempfile.TemporaryDirectory(dir=_test_args.scratch_root) as directory:
            prepared=Path(directory)/'prepared.json';prepared.write_text('{}',encoding='utf-8')
            probe=r06.Probe.__new__(r06.Probe)
            probe.prepared={'maximum_owned_threads':2,'native_argv':['not-launched']}
            probe.process=None;probe.path=prepared;probe.repo=REPO;probe.output=Path(directory)/'launch'
            claim=Mock()
            with patch.object(r06,'checked',return_value=value),patch.object(r06.time,'time',return_value=now.timestamp()+301), \
                 patch.object(r06,'verify_producer') as production,patch.object(r06,'verify_observer_bytes') as exe, \
                 patch.object(r06.subprocess,'Popen') as launch:
                with self.assertRaisesRegex(ValueError,'admission expired'):
                    probe.start(lambda:r06.revalidate_before_launch(probe,{'same_pin':'as_before_camera'},
                        expected=expected,producer=producer,native_tree='t'),claim)
            production.assert_not_called();exe.assert_not_called();launch.assert_not_called();claim.assert_not_called()
            self.assertFalse(getattr(probe,'launch_claimed',False))

    def test_settings_are_finite_and_reject_extra_or_two_days(self):
        self.assertEqual(r06.settings(settings()).one_day_timeout,20)
        for change in ({'maximum_actual_days':2},{'one_day_timeout':30},{'observer_total_timeout_seconds':100},
                       {'ready_timeout_seconds':float('nan')}):
            with self.assertRaises(ValueError):r06.settings({**settings(),**change})

    def test_r04_r06_are_mutually_exclusive_before_either_route(self):
        with self.assertRaisesRegex(ValueError,'mutually exclusive'):
            prep.validate_contract(dict(case_contract={'schema':'xar.e04.r10-common-preparation.v1'},
                case_inputs={'r04_county_entry':{},'r06_refill_one_day':settings()}))

    def test_wrong_selected_normal_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'normal save'):
            r06.validate_contract(dict(case_inputs={'r06_refill_one_day':settings()},saved_campaign={
                'sha256':'b'*64,'date_raw':1000,'player_id':12}))

    def test_same_passed_caseclient_is_dispatched_once(self):
        context=dict(case_contract={'schema':'xar.e04.r10-common-preparation.v1'},
            case_inputs=dict(army_id=0,war_id=1,goal_province_id=13,staging_province_id=6,
                director_scope_revision='test',normal_checkpoint_receipt={'sha256':'a'*64},r06_refill_one_day=settings()),
            shared_game={'version':'1.20.0.4','exe_sha256':'b'*64},saved_campaign={},run_id='test-run')
        client=NS(retain_process=Mock(),_process={'pid':30},checkpoint=Mock())
        frame=dict(diagnostics={'bridge_pid':30,'connection_generation':2},played_character={'character_id':12},episode_run_id=None)
        relay=NS(client=NS(snapshot=Mock(return_value=frame)))
        with patch('ck3_live_run_id.current_machine_id',return_value='test-machine'), \
             patch('ck3_mod_acceptance_cases.r08_writer_common_adapter.retained_creation_filetime',return_value=35), \
             patch.object(prep,'CommonRequestRelay',return_value=relay),patch.object(prep,'small_json',return_value={}), \
             patch.object(prep,'collect_ready_t0',return_value={'readiness':{}}), \
             patch.object(r06,'run_case',return_value={'actual_days':1}) as actor:
            value=prep.run_case(context,client)
        actor.assert_called_once_with(context,client)
        self.assertEqual(value['r06_refill_one_day']['actual_days'],1)
        self.assertFalse(value['business_pass'])

    def test_packet_32mib_exception_is_one_exact_path(self):
        original=Mock(return_value=({},{}));prepare=NS(read=original)
        target=Path('selected/army-packet.json').resolve()
        r06.prepare_inputs(prepare,{},target)
        prepare.read(target);self.assertEqual(original.call_args.args[1],32*1024*1024)
        prepare.read(Path('other/army-packet.json'));self.assertEqual(original.call_args.args[1],2*1024*1024)

    def test_expired_observer_rejects_resume_arm_and_modal_mutation(self):
        probe=NS(process=NS(poll=lambda:0),remaining=lambda:0,paired=Mock())
        call=Mock();context={'command_timeout':120};guard=r06.guarded_call(probe,call,context)
        for tool,args in [('ck3_execute_step',{'step':'resume-map'}),
                          ('ck3_execute_step',{'step':'research-arm-tactical-daily-sentinel-v1-x'}),
                          ('ck3_select_event_option',{})]:
            with self.assertRaisesRegex(ValueError,'no new Arm'):guard('x',tool,args)
        call.assert_not_called();probe.paired.assert_not_called()

    def test_post_exit_readonly_requires_actual_pair_and_restores_timeout(self):
        probe=NS(process=NS(poll=lambda:0),remaining=lambda:0,paired=Mock(side_effect=ValueError('not paired')))
        call=Mock();context={'command_timeout':120};guard=r06.guarded_call(probe,call,context)
        with self.assertRaisesRegex(ValueError,'not paired'):guard('x','ck3_take_snapshot',{})
        call.assert_not_called()
        probe.paired=Mock(return_value={});guard('x','ck3_take_snapshot',{})
        self.assertEqual(context['command_timeout'],120);call.assert_called_once()

    def test_unknown_public_result_is_not_retried(self):
        client=NS(execute_plan=Mock(side_effect=TimeoutError('unknown original result')))
        queue=r06.OriginalRows(client)
        with self.assertRaises(TimeoutError):queue.execute_plan([{'tool':'ck3_execute_step','args':{}}],'one')
        self.assertEqual(client.execute_plan.call_count,1)

    def test_native_episode_alias_is_not_promoted(self):
        original=dict(snapshot_id='s',revision=1,native_revision=2,date_raw=1000,
                      episode_projection='native_campaign',episode_run_id=None)
        before=dict(frame=original,query=dict(queried_snapshot_id='s',queried_revision=1,
            queried_native_revision=2,queried_date_raw=1000,queried_episode_run_id='managed-alias'))
        originals=NS(frames={('s',1):original},queries={'full':{'after_snapshot':original}})
        native,packet=r06.native_inputs(before,originals,{'public_control_name':'full'})
        self.assertIsNone(native['episode_run_id']);self.assertIsNone(packet['queried_episode_run_id'])
        self.assertEqual(before['query']['queried_episode_run_id'],'managed-alias')

    def test_stale_or_incomplete_root_admission_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity'):
            r06.validate_admission({},expected={'machine_id':'m'},producer={},native_tree='tree')

    def test_exit_before_ready_cannot_release_a_day(self):
        import time
        probe=r06.Probe.__new__(r06.Probe)
        probe.started=time.monotonic();probe.a=NS(ready_timeout_seconds=1)
        probe.output=REPO/'tools'/'not-a-real-r06-observer-output'
        probe.process=NS(poll=lambda:1)
        with self.assertRaisesRegex(ValueError,'before READY'):probe.ready()

    def test_unknown_launch_restoration_blocks_save(self):
        with self.assertRaisesRegex(ValueError,'Save withheld'):
            r06.require_restored_for_save(NS(launch_claimed=True,restored=False))
        r06.require_restored_for_save(NS(launch_claimed=True,restored=True))
        r06.require_restored_for_save(None)

    def test_no_qualification_receipt_cannot_be_replaced_by_settings_boolean(self):
        with self.assertRaisesRegex(ValueError,'producer fields'):
            r06.verify_producer({'production_bytes_qualified':True},machine_id='m',native_tree='t')

    def test_os_union_and_fourth_snapshot_require_separate_birth_reserve(self):
        expected=dict(machine_id='m',run_id='r',bridge_pid=1,process_creation_filetime=2,date_raw=100)
        sample=lambda n:dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),complete=True,unresolved=[],os_list_count=n,generations=[[i,1000+i] for i in range(1,n+1)])
        census=dict(machine_id='m',run_id='r',pid=1,process_creation_FILETIME=2,snapshots=[sample(64)]*3)
        value=dict(**expected,schema='xar.r06.public_worker_source_admission.v1',observed_at_utc=datetime.now(timezone.utc).isoformat(),
            maximum_owned_threads=66,birth_reserve_generations=1,thread_census={},latest_thread_snapshot=sample(65),
            actual_module=dict(pid=1,process_created_filetime=2,complete_module_metadata_enumeration=True,module={'path':'C:/bridge/xar_ck3_bridge.dll'}),
            native_qualification={'sha256':'q'},native_tree='t')
        producer=dict(carrier_module_path='C:/bridge/xar_ck3_bridge.dll',qualification={'sha256':'q'})
        with patch.object(r06,'checked',return_value=census):
            self.assertEqual(r06.validate_admission(value,expected=expected,producer=producer,native_tree='t'),66)
            with self.assertRaisesRegex(ValueError,'birth reserve'):
                r06.validate_admission({**value,'maximum_owned_threads':65},expected=expected,producer=producer,native_tree='t')

    def test_other_native_tree_cannot_use_qualified_receipt(self):
        p={k:{} for k in ('qualification','build_result','SYSTEM_receipt','cold_result')}
        p.update(source_dir='s',observer_exe='x',observer_exe_sha256='h',native_build_source_head='head',native_tree='other',
                 carrier_module_path='d',carrier_source_epoch=20261018,cmake_defines=r06.FLAGS)
        q=dict(machine_id='m',production_bytes_qualified=True,focused_cold_qualified=True,native_build_source_head='head',native_tree='other')
        with patch.object(r06,'checked',side_effect=[q,{}, {}, {}]):
            with self.assertRaisesRegex(ValueError,'native source/tree'):
                r06.verify_producer(p,machine_id='m',native_tree='current')

    def test_runtime_must_use_same_actual_q_and_dll_path(self):
        p=dict(qualification={'sha256':'q'},carrier_module_path='C:/bridge/xar_ck3_bridge.dll')
        selection=NS(manifest={'qualification':{'actual_producer':p['qualification'],'native_tree':'t'}},
                     paths={'dll':p['carrier_module_path']})
        r06.verify_runtime(selection,p,'t')
        selection.manifest['qualification']['actual_producer']={'sha256':'other'}
        with self.assertRaisesRegex(ValueError,'shared runtime'):r06.verify_runtime(selection,p,'t')


if __name__=='__main__':unittest.main()
