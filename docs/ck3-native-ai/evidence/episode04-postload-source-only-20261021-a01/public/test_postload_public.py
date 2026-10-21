"""Finite Python counterexamples; no actual Q, SDK, game or native execution."""
from __future__ import annotations
import copy,importlib,json,os,sys,tempfile,time,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'candidate/native-tools'),str(ROOT/'candidate/tools')]
from postload_admission import (MODE,ROOT_SCHEMA,scope_value,validate_qualification,validate_index,file_pin,pin,
    REQUIRED,expected_from_scope)
from postload_models import Expected
from postload_wire import wire_json
from parent_postload_contract import PREFIX_SHA
import postload_root_scope
import ck3_mod_acceptance_cases.r08_parent_postload_controller as controller
from ck3_mod_acceptance_cases.postload_public_models import Binding,Ready

def owner_value() -> dict[str,object]:
    return {'schema':'xar.maintenance.parent_postload.owner-binding.v1',
        'mode':'native_campaign_character_postload_v1','episode_projection':'native_campaign',
        'episode_run_id':None,'original_episode_key_present':False,'pid':123,
        'process_create_time_100ns':134370000000000001,'connection_generation':1,
        'player_character_full_id':33388,'local_player_id':33388,'game_state_identity_witness':0x300000,
        'character':0x200000,'context':0,'controlled_window_id':1,'payment_epoch':1,'native_revision':5,
        'date_raw':53149056,'absolute_day_raw':2214544,'callsite_anchor_rva':0x28f785a}

def scope_document() -> dict[str,object]:
    now=datetime.now(timezone.utc)
    reference={'path':'source-only-placeholder','bytes':1,'sha256':'0'*64}
    return {'schema':ROOT_SCHEMA,'mode':MODE,'machine_id':'synthetic-source-machine',
        'postload_execution_authorized':True,'observed_at_utc':now.isoformat(),
        'expires_at_utc':(now+timedelta(seconds=30)).isoformat(),
        'qualification_sha256':'0'*64,'observer_sha256':'0'*64,'common_output':'synthetic-case-output',
        'snapshot_view_pin':reference,'cash_view_pin':reference,'owner_binding':owner_value(),
        'module_base':0x140000000,'module_size':102518784,'foreign_limit':4096,'capture_ms':30000,
        'cancel_event':'Local\\XAR_POSTLOAD_SYNTHETIC_RUN','public_bundle_index_pin':reference}

def expected_value() -> dict[str,object]:
    return {'machine_id':'synthetic-source-machine','synthetic':False,'pid':123,
        'created':134370000000000001,'entry':0x140000000+0x28f7840,
        'post_pc':0x140000000+0x28f785a,'subject_field_address':0x200000+0x1c0,
        'character':0x200000,'full_id':33388,'context':0,'local_player_id':33388,
        'game_state':0x300000,'date_raw':53149056,'absolute_day':2214544,
        'foreign_limit':4096,'capture_ms':30000,'admission_id':'synthetic-only-model',
        'owner_binding':owner_value()}

class PostloadPublicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary=tempfile.TemporaryDirectory(dir=os.environ.get('POSTLOAD_TEST_TMP'))
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def binding(self) -> Binding:
        return Binding.parse({'schema':'xar.maintenance.parent_postload.binding.v1','machine_id':'synthetic-source-machine',
            'prepared_only':True,'expected':wire_json(expected_value()),'root_scope_sha256':'0'*64})

    def test_RDX_null_and_decimal_birth_preserved_in_independent_root_scope(self) -> None:
        document=scope_document();wire=wire_json(document)
        parsed=scope_value(wire)
        self.assertEqual(parsed.owner['context'],0)
        self.assertEqual(parsed.owner['process_create_time_100ns'],134370000000000001)
        self.assertIn('"process_create_time_100ns": "134370000000000001"',json.dumps(wire))
        self.assertEqual(parsed.owner['callsite_anchor_rva'],0x28f785a)

    def test_missing_null_bool_float_and_old_root_modes_refused(self) -> None:
        for mutation in ('missing','null','numeric-boolean','float','old-mode','future','expired'):
            with self.subTest(mutation=mutation):
                value=scope_document()
                if mutation=='missing':del value['postload_execution_authorized']
                elif mutation=='null':value['postload_execution_authorized']=None
                elif mutation=='numeric-boolean':value['postload_execution_authorized']=1
                elif mutation=='float':value['module_base']=1.0
                elif mutation=='old-mode':value['mode']='player-parent-pointer-read-once-v1'
                elif mutation=='future':value['observed_at_utc']=(datetime.now(timezone.utc)+timedelta(seconds=10)).isoformat()
                else:value['expires_at_utc']=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
                with self.assertRaises(ValueError):scope_value(wire_json(value))

    def test_new_Q_absent_legacy_or_partial_cannot_open_any_file(self) -> None:
        for value in (None,{},
            {'schema':'xar.maintenance.parent_pointer_read.pointer-read-qualification.v1'},
            {'schema':'xar.maintenance.parent_postload.qualification.v1','status':'PARTIAL'}):
            with self.subTest(value=value),patch('postload_admission.verify',side_effect=AssertionError('No input read before schema admission')):
                with self.assertRaises(ValueError):
                    validate_qualification(value,observer={'path':'not-opened','bytes':1,'sha256':'0'*64},typed_root=self.root)

    def test_pin_safe_numbers_reject_bool_float_and_unsafe_integer(self) -> None:
        for value in (True,1.5,1<<53,-1):
            with self.subTest(value=value),self.assertRaises(ValueError):
                file_pin({'path':'x','bytes':value,'sha256':'0'*64})

    def test_expanded_bundle_validates_real_empty_package_and_actual_helper(self) -> None:
        index=ROOT/'PUBLIC-SOURCE-INDEX.prepared-a04.json'
        helper=ROOT/'candidate/native-tools/prepare_parent_postload_admission.py'
        validate_index(pin(index),self_path=helper)
        self.assertEqual((ROOT/'candidate/tools/ck3_mod_acceptance_cases/__init__.py').stat().st_size,0)
        with self.assertRaisesRegex(ValueError,'helper missing'):
            validate_index(pin(index),self_path=self.root/'unbound_helper.py')

    def test_ready_binds_exec_DR0_not_character_data_watch(self) -> None:
        binding=self.binding();expected=expected_value()
        start={'kind':'start','schema':'xar.maintenance.parent_postload.raw.v1','mode':MODE,
            **expected,'entryExact':False,'observation_kind':'parent_postload_execution',
            'breakpoint_kind':'execution','target_record_limit':1,'prefix_sha256':PREFIX_SHA}
        saved=[0,0,0,0,0,0x400]
        arm={'kind':'arm','thread_id':1,'thread_generation':1,'thread_created':134370000000000123,
            'success':True,'readback':True,'saved_debug':saved,
            'armed_debug':[expected['post_pc'],0,0,0,0,0x401]}
        ready={'kind':'ready','census_complete':True}
        raw=self.root/'raw.ndjson'
        def write() -> None:
            raw.write_text(''.join(json.dumps(wire_json(row))+'\n' for row in (start,arm,ready)),encoding='utf-8')
        write()
        sidecar=Ready.parse({'ready':True,'mode':MODE,'armed_thread_count':1,'census_complete':True})
        proof=controller.bind_ready(raw,binding,sidecar)
        self.assertIsNotNone(proof)
        arm['armed_debug']=[expected['subject_field_address'],0,0,0,0,0xb0401]
        write()
        with self.assertRaisesRegex(ValueError,'Actual full watch vector'):controller.bind_ready(raw,binding,sidecar)

    def test_real_standard_Selection_load_no_R10_preload_and_missingQ_zero_SDK(self) -> None:
        # Run this in a fresh Python process in the separate smoke below to
        # prove the normal loader path; here it remains a real loader invocation.
        import ck3_mod_acceptance as entry
        selected=entry.Selection.__new__(entry.Selection)
        selected.adapter_path=ROOT/'candidate/tools/ck3_mod_acceptance_cases/r08_postload_adapter.py'
        selected.locations={'repo_root':Path('D:/workspace/ck3_eternal_recurrence')}
        before=sys.modules.pop('ck3_mod_acceptance_cases.r10_prepare_adapter',None)
        try:
            adapter=selected.load_adapter()
            template=json.loads((ROOT/'CASE-INPUTS.source-only-template-a04.json').read_text())
            context={'case_inputs':template['case_inputs'],'case_contract':{'schema':'xar.e04.r10-common-preparation.v1'}}
            with patch.object(controller,'subprocess') as processes:
                with self.assertRaises(ValueError):adapter.validate_contract(context)
                forbidden=Mock()
                with self.assertRaises(ValueError):adapter.run_case(context,forbidden)
                self.assertEqual(forbidden.mock_calls,[])
                processes.Popen.assert_not_called()
            self.assertIn('ck3_mod_acceptance_cases.r10_prepare_adapter',sys.modules)
        finally:
            if before is not None:sys.modules['ck3_mod_acceptance_cases.r10_prepare_adapter']=before

    def test_unknown_day_is_never_replayed_and_after_only_after_cleanup(self) -> None:
        events: list[str]=[]
        control=self.root/'control';control.mkdir()
        scope_path=self.root/'scope.json';scope_path.write_text(json.dumps(wire_json(scope_document())),encoding='utf-8')
        prepared=self.root/'prepared';prepared.mkdir()
        binding_raw=dict(self.binding().raw);binding_raw['root_scope_sha256']=pin(scope_path)['sha256']
        (prepared/'BINDING.prepared.json').write_text(json.dumps(binding_raw),encoding='utf-8')
        observer=self.root/'never-executed-observer';observer.write_bytes(b'SOURCE ONLY')
        fake=SimpleNamespace(pid=123,poll=lambda:None,wait=lambda **kwargs:0)
        before=controller.Snapshot.parse({'episode_projection':'native_campaign','map_ready':True,'paused':True,
            'played_character':{'character_id':33388},'date_raw':53149056,
            'diagnostics':{'bridge_pid':123,'connection_generation':1}},33388)
        def call(label: str,tool: str,args: dict[str,object]) -> dict[str,object]:
            events.append(label)
            if label=='day-once':raise ValueError('original action result unknown')
            return {'episode_projection':'native_campaign','map_ready':True,'paused':True,
                'played_character':{'character_id':33388},'date_raw':53149080,
                'diagnostics':{'bridge_pid':123,'connection_generation':1}}
        def finish(*args: object,**kwargs: object) -> dict[str,object]:
            events.append('typed-cleanup')
            session=args[0]
            session.stdout.close();session.stderr.close()
            controller.SESSIONS.pop(str(control),None);controller.EVENTS.pop(str(control),None)
            return {'target_postload_qualified':False,'cleanup_complete':True,'full_R08':False}
        with patch.object(controller,'write',return_value={'path':'source-fixture','bytes':1,'sha256':'0'*64}), \
             patch.object(controller,'create_cancel',return_value=1),patch.object(controller,'process_birth',return_value='134370000000000001'), \
             patch.object(controller.subprocess,'Popen',return_value=fake),patch.object(controller,'await_ready',return_value={}), \
             patch.object(controller,'finish',side_effect=finish):
            result=controller.observe(python=sys.executable,tools=ROOT/'candidate/native-tools',observer=pin(observer),
                prepared=prepared,output=control,machine='synthetic-source-machine',scope_pin=pin(scope_path),
                collected_at=time.monotonic(),before=before,deadline_utc=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
                call=call,packet_pin=lambda label:pin(scope_path),guard=lambda:None)
        self.assertEqual(events,['day-once','typed-cleanup','independent-after'])
        self.assertFalse(result['day']['exact_day_verified'])
        self.assertIn('unknown',result['primary_error'])
        self.assertFalse(result['full_R08_qualified'])

    def test_root_false_declarations_refuse_before_process_inspection(self) -> None:
        inspect=Mock(side_effect=AssertionError('no OS observation for missing authorization'))
        with self.assertRaises(ValueError):postload_root_scope.build({},None,inspect=inspect)
        inspect.assert_not_called()

    def test_public_dispatch_preserves_missing_episode_and_same_client_without_legacy_readiness(self) -> None:
        from ck3_mod_acceptance_cases import r08_postload_adapter as adapter
        original={'episode_projection':'native_campaign','map_ready':True,'paused':True,
            'played_character':{'character_id':33388},'date_raw':53149056,
            'diagnostics':{'bridge_pid':123,'connection_generation':1}}
        self.assertNotIn('episode_run_id',controller.Snapshot.parse(original,33388).raw)
        token=object();observed: list[object]=[]
        def run(context: object,held: object) -> dict[str,object]:
            observed.append(held)
            return {'full_R08_qualified':False,'original_episode_key_present':'episode_run_id' in original}
        boundary=SimpleNamespace(validate_contract=lambda context:None,run_case=run)
        # Only admission is a finite structural boundary stub here. Actual new-Q
        # refusal is proved separately through the real standard entry/loader.
        with patch.object(adapter,'actor',return_value=boundary), \
             patch.object(adapter,'common',side_effect=AssertionError('No unrelated readiness queries')):
            result=adapter.run_case({},token)
        self.assertEqual(observed,[token])
        self.assertFalse(result['original_episode_key_present'])
        self.assertFalse(result['full_R08_qualified'])

    def test_numeric_root_declarations_cannot_impersonate_true(self) -> None:
        fields={'schema','machine_id','run_id','execute_after_actual_awaiting','ready_context_pin','runtime_pin',
            'prepared_pin','frozen_argv_pin','bundle_index_pin','helper_pin','qualification_pin','observer_pin',
            'Game_capacity_pin','game_exe_path','root_scope_path','deadline_utc','declarations'}
        value={name:None for name in fields}
        value.update(schema='xar.maintenance.parent_postload.conditional-root-authorization.v1',
            execute_after_actual_awaiting=True,declarations={'one_original_window_only':1,
                'no_replay_unknown':True,'postload_execution_reviewed':True})
        inspect=Mock(side_effect=AssertionError('no process read'))
        with self.assertRaisesRegex(ValueError,'declarations'):postload_root_scope.build(value,None,inspect=inspect)
        inspect.assert_not_called()

    def test_root_scope_checks_actual_machine_before_any_OS_owner_query(self) -> None:
        fields={'schema','machine_id','run_id','execute_after_actual_awaiting','ready_context_pin','runtime_pin',
            'prepared_pin','frozen_argv_pin','bundle_index_pin','helper_pin','qualification_pin','observer_pin',
            'Game_capacity_pin','game_exe_path','root_scope_path','deadline_utc','declarations'}
        ready=self.root/'ready-machine.json';runtime=self.root/'runtime-machine.json'
        ready.write_text('{}',encoding='utf-8');runtime.write_text('{}',encoding='utf-8')
        value={name:None for name in fields}
        value.update(schema='xar.maintenance.parent_postload.conditional-root-authorization.v1',
            machine_id='synthetic-foreign-machine',run_id='SYNTHETIC_ONLY',execute_after_actual_awaiting=True,
            ready_context_pin=pin(ready),runtime_pin=pin(runtime),
            helper_pin=pin(ROOT/'candidate/native-tools/postload_root_scope.py'),
            declarations={'one_original_window_only':True,'no_replay_unknown':True,'postload_execution_reviewed':True})
        inspect=Mock(side_effect=AssertionError('must not query foreign OS owner'))
        with self.assertRaisesRegex(ValueError,'another current machine'):
            postload_root_scope.build(value,None,inspect=inspect,machine_reader=lambda:'synthetic-current-machine')
        inspect.assert_not_called()

    def test_prewatcher_expired_reserve_creates_no_scope_and_never_sleeps(self) -> None:
        ready=self.root/'ready.json';runtime=self.root/'runtime.json'
        ready.write_text(json.dumps({'run_dir':str(self.root/'not-launched')}),encoding='utf-8')
        runtime.write_text('{}',encoding='utf-8')
        auth={'ready_context_pin':pin(ready),'runtime_pin':pin(runtime),
            'deadline_utc':(datetime.now(timezone.utc)+timedelta(seconds=1049)).isoformat()}
        target=self.root/'no-marker.json';sleep=Mock()
        with self.assertRaisesRegex(ValueError,'close reserve'):
            postload_root_scope.wait_awaiting(target,auth,sleep=sleep)
        self.assertFalse(target.exists());sleep.assert_not_called()

    def test_original_hold_uses_real_ready_shape_and_pinned_prepared_startup(self) -> None:
        live=self.root/'actual-shape-run';live.mkdir()
        state=self.root/'prepared-state'
        prepared=self.root/'prepared-shape.json'
        prepared.write_text(json.dumps({'startup':{'mode':'saved_campaign','state_dir':str(state)}}),encoding='utf-8')
        ready={'schema':'source-fixture','run_id':'SYNTHETIC_ONLY','run_dir':str(live),'keeper_root':'synthetic',
            'prepared_case':pin(prepared),'case_inputs':{},'product':'synthetic','case':'synthetic','frozen_argv':{}}
        self.assertNotIn('state_dir',ready)
        source=self.root/'selected-source'
        hold=time.time()+1200
        report={'phase':'hold','state_dir':str(state),'agent_source_root':str(source),
            'hold_until_utc_estimated':hold,'finished_at':None,'error':None}
        path=live/'native-report.json';path.write_text(json.dumps(report),encoding='utf-8')
        self.assertEqual(postload_root_scope.actual_hold(ready,{'repo_root':str(source)}),hold)
        report['state_dir']=str(self.root/'other-state')
        path.write_text(json.dumps(report),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'source/state crossed'):
            postload_root_scope.actual_hold(ready,{'repo_root':str(source)})

    def test_21_case_contract_is_distinct_and_cancel_last(self) -> None:
        self.assertEqual(len(REQUIRED),21)
        self.assertEqual(REQUIRED[-1],'cancel_late')
        self.assertIn('null-context',REQUIRED)
        self.assertIn('other-player-read',REQUIRED)
        self.assertIn('other-player-write',REQUIRED)

if __name__=='__main__':unittest.main(verbosity=2)
