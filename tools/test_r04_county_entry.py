"""Focused regressions for R219 progress, admitted roots and camera wiring.

Synthetic queue/date cases only; they grant no game/native/video qualification.
"""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace as NS
import argparse
import json
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

p=argparse.ArgumentParser(add_help=False)
p.add_argument('--source-repo',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--candidate-tools',type=Path)
a,rest=p.parse_known_args()
sys.path[:0]=[str(a.candidate_tools or a.source_repo/'tools'),str(a.source_repo/'tools'),
              str(a.source_repo/'ck3_autonomous_player/src')]
import ck3_mod_acceptance_cases
if a.candidate_tools:
    ck3_mod_acceptance_cases.__path__.insert(0,str(a.candidate_tools/'ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases import r04_county_entry as county
from ck3_mod_acceptance_camera import camera_paths,validate_camera_paths


def frame(raw=1000):
    return dict(date_raw=raw,paused=True,played_character={'character_id':12,'alive':True},
        diagnostics={'bridge_pid':30,'connection_generation':2},episode_run_id='synthetic-run',
        player_armies=[dict(army_id=0,owner_character_id=12,current_province_id=6,
            route_province_ids=[13],move_target_province_id=13,in_combat=False,retreating=False)])


class R219Regression(unittest.TestCase):
    def test_public_readiness_hook_has_explicit_seven_day_contract(self):
        from ck3_mod_acceptance_cases import r10_prepare_adapter as preparation
        value=dict(scene_root='synthetic-scene',capacity_admission={'synthetic':True},
            expected_source_save_sha256='a'*64,expected_start_date_raw=1000,
            origin_province=6,target_province=13,actor_id=12,army_id=0,native_carmy_id=0,
            capture_after_days=6,max_days=7,driver_limit_bytes=1024,profile_limit_bytes=768,
            deadline_utc='2100-01-01T00:00:00Z',camera_timeout_seconds=900,prefix='synthetic-county')
        self.assertEqual(county.settings(value).max_days,7)
        bad={**value,'capture_after_days':7,'max_days':8}
        with self.assertRaisesRegex(ValueError,'one late observation day'):
            county.settings(bad)
        context=dict(case_contract={'schema':'xar.e04.r10-common-preparation.v1'},
            case_inputs=dict(army_id=0,war_id=1,goal_province_id=13,staging_province_id=6,
                director_scope_revision='synthetic',normal_checkpoint_receipt={'sha256':'a'*64},r04_county_entry=value),
            shared_game={'version':'1.20.0.4','exe_sha256':'b'*64},saved_campaign={})
        client=NS(retain_process=Mock(),_process={'pid':30},checkpoint=Mock())
        relay=NS(client=NS(snapshot=Mock(return_value=frame())))
        with patch('ck3_live_run_id.current_machine_id',return_value='synthetic-machine'), \
             patch('ck3_mod_acceptance_cases.r08_writer_common_adapter.retained_creation_filetime',return_value=35), \
             patch.object(preparation,'CommonRequestRelay',return_value=relay), \
             patch.object(preparation,'small_json',return_value={}), \
             patch.object(preparation,'collect_ready_t0',return_value={'readiness':{}}), \
             patch.object(county,'run_case',return_value={'actual_days':6}) as observe:
            result=preparation.run_case(context,client)
        observe.assert_called_once_with(context,client)
        self.assertEqual(result['r04_county_entry']['actual_days'],6)
        self.assertEqual(result['formal_ABC_completed'],0)
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory);context.update(output=str(output),run_id='synthetic-run')
            with patch('ck3_live_run_id.current_machine_id',return_value='synthetic-machine'):
                missing=preparation.verify_case(context)['r04_county_entry']
                self.assertFalse(missing['present']);self.assertIsNone(missing['actual_days'])
                terminal=dict(machine_id='synthetic-machine',run_id='synthetic-run',actual_days=6,
                              status='STOPPED_ERROR_PRESERVED_NO_REPLAY',Save=True,OFFclear=True)
                (output/'R04-BAYEUX-TERMINAL.json').write_text(json.dumps(terminal),encoding='utf-8')
                actual=preparation.verify_case(context)['r04_county_entry']
                self.assertEqual(actual['actual_days'],6)
                self.assertFalse(actual['R04_entire_card_closed'])
                context['run_id']='other-run'
                with self.assertRaisesRegex(ValueError,'another machine or allocated run'):
                    preparation.verify_case(context)

    def test_late_camera_timeout_keeps_six_completed_days_without_seventh_arm(self):
        current=frame();calls=[];day_rows=[]
        class IO:
            context={'machine_id':'synthetic-machine'}
            client=NS(selection=NS(run_dir=Path('synthetic-run')))
            def exact_day(self,before):
                calls.append(before['frame']['date_raw'])
                current['date_raw']+=24
                return deepcopy(current),{'exact_day_verified':True}
        def before_day(day,current):
            if day==7:raise TimeoutError('late camera Start absent')
        result={'actual_days':0,'days':[]}
        with self.assertRaisesRegex(TimeoutError,'Start absent'):
            county.snapshot_only_to_target(IO(),lambda _:deepcopy(current),army_id=0,actor=12,target=13,
                max_days=7,before_day=before_day,on_day=lambda *row:day_rows.append(row),result=result)
        self.assertEqual(calls,[1000+24*n for n in range(6)])
        self.assertEqual(result['actual_days'],6)
        self.assertEqual([row['day'] for row in result['days']],[1,2,3,4,5,6])
        self.assertEqual(result['days'][-1]['date_raw'],1144)
        self.assertEqual(len(day_rows),6)

    def test_unknown_day_result_is_not_counted_or_replayed(self):
        class IO:
            context={'machine_id':'synthetic-machine'}
            client=NS(selection=NS(run_dir=Path('synthetic-run')))
            exact_day=Mock(side_effect=TimeoutError('original clock unresolved'))
        result={'actual_days':0,'days':[]};io=IO()
        with self.assertRaisesRegex(TimeoutError,'unresolved'):
            county.snapshot_only_to_target(io,lambda _:frame(),army_id=0,actor=12,target=13,max_days=1,
                before_day=lambda *_:None,on_day=Mock(),result=result)
        self.assertEqual(io.exact_day.call_count,1)
        self.assertEqual(result,{'actual_days':0,'days':[]})

    def test_additional_profile_is_counted_once_and_cannot_borrow_driver_room(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);state=root/'state';user=root/'userdirs';driver=root/'Driver'/'run'
            for folder in (state,user/'nested',driver):folder.mkdir(parents=True)
            (state/'x').write_bytes(b'a'*11);(user/'nested'/'y').write_bytes(b'b'*17);(driver/'z').write_bytes(b'c'*23)
            selection=NS(state_dir=state,run_dir=driver)
            cap={'component_additional_roots':{'profile':[str(user),str(user/'nested'),str(state),str(user)]}}
            value=county.runtime_bytes(selection,cap,limit=30,reserve=7,profile_limit=28,extra_roots=[driver/'case-output'])
            self.assertEqual(value['profile']['bytes'],28)
            self.assertEqual(value['profile']['files'],2)
            self.assertEqual(value['driver']['bytes'],23)
            self.assertEqual(value['profile']['body_reads'],0)
            with self.assertRaisesRegex(ValueError,'profile ceiling'):
                county.runtime_bytes(selection,cap,limit=10000,reserve=7,profile_limit=27)
            bad={'component_additional_roots':{'profile':[str(root)]}}
            with self.assertRaisesRegex(ValueError,'overlap'):
                county.runtime_bytes(selection,bad,limit=10000,reserve=7,profile_limit=10000)

    def test_split_roots_require_exact_cap_and_original_retained_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);scene=root/'scene';state=root/'separate-profile';driver=root/'separate-Driver'/'run'
            for folder in (scene,state/'control',driver):folder.mkdir(parents=True)
            (state/'control'/'ck3.json').write_text(json.dumps({'ck3_pid':30}),encoding='utf-8')
            selection=NS(state_dir=state,run_dir=driver)
            future=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
            cap=dict(machine_id='synthetic-machine',admitted=True,budget_status='GREEN',run_id='run',source_head='a'*40,
                scene_root=str(scene),component_roots={'profile':str(state),'driver':str(driver)},
                component_ceiling_bytes={'profile':768,'driver':1024},quota_review_at_utc=future,run_hard_deadline_utc=future)
            args=NS(profile_limit_bytes=768,driver_limit_bytes=1024,deadline_utc=future,capacity_admission={'synthetic':True})
            retained=dict(pid=30,create_time=3.5,retained_synchronize_query_handle_acquired=True)
            report=dict(state_dir=str(state),hold_until_utc_estimated=4102444800)
            result=county.actual_binding(selection,scene,retained,report,cap,machine_id='synthetic-machine',source_head='a'*40,a=args)
            self.assertEqual(result['pid'],30)
            self.assertFalse(Path(result['control_path']).is_relative_to(scene))
            for key,value in [('machine_id','other-machine'),('run_id','other-run')]:
                bad=deepcopy(cap);bad[key]=value
                with self.assertRaisesRegex(ValueError,'capacity required'):
                    county.actual_binding(selection,scene,retained,report,bad,machine_id='synthetic-machine',source_head='a'*40,a=args)
            bad=deepcopy(cap);bad['component_roots']['profile']=str(scene)
            with self.assertRaisesRegex(ValueError,'exactly bind'):
                county.actual_binding(selection,scene,retained,report,bad,machine_id='synthetic-machine',source_head='a'*40,a=args)
            retained['retained_synchronize_query_handle_acquired']=False
            with self.assertRaisesRegex(ValueError,'retained OS'):
                county.actual_binding(selection,scene,retained,report,cap,machine_id='synthetic-machine',source_head='a'*40,a=args)

    def test_camera_old_alias_fails_before_camera_or_move_and_forged_start_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            live=Path(directory);output=live/'county-case';output.mkdir()
            awaiting,signal=camera_paths(output)
            self.assertEqual(validate_camera_paths(awaiting,signal,live=live,output_name='county-case'),(awaiting,signal))
            with self.assertRaisesRegex(ValueError,'before-action-camera'):
                validate_camera_paths(output/'before-entry-window-camera-awaiting.json',signal,live=live,output_name='county-case')
            with self.assertRaisesRegex(ValueError,'basename'):
                validate_camera_paths(*camera_paths(live.parent),live=live,output_name='..')
            (output/'R04-ENTRY-WINDOW-BASELINE.json').write_text('{}',encoding='utf-8')
            signal.write_text(json.dumps(dict(machine_id='wrong-machine',run_id=live.name,bridge_pid=30,date_raw=1000,camera_started=True)),encoding='utf-8')
            class Client:
                selection=NS(run_dir=live)
                guard=Mock()
                def checkpoint(self,name,value):
                    path=output/(name+'.json');path.write_text(json.dumps(value),encoding='utf-8');return path
            Client.output=output
            io=NS(client=Client(),context={'machine_id':'synthetic-machine'},settings={'deadline_unix_seconds':4102444800})
            cfg=NS(camera_timeout_seconds=1,normal_close_reserve=900,cleanup_save_reserve=120,one_day_timeout=120,
                   army_id=0,target_province=13,capture_after_days=6,max_days=7)
            # A pre-existing signal is consumed namespace, even if its ACK says true.
            with self.assertRaisesRegex(ValueError,'already consumed'):
                county.await_day_camera(io,frame(),{'Move_attempts':1},cfg)


if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest])
