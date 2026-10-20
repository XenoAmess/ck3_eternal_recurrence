"""Public actor failure convergence; fake queue is not native qualification."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import sys
import tempfile
import unittest

sys.path[:0]=[str(Path(__file__).resolve().parent),
    str(Path(__file__).resolve().parents[1]/'ck3_autonomous_player/src')]
from ck3_mod_acceptance_cases import r08_writer_one_day as actor
from ck3_mod_acceptance_cases import r08_writer_common_adapter as bridge
from xar_autoplayer.bridge.army_observer_research_sampling_control import FAMILIES


class CleanupIntegration(unittest.TestCase):
    def test_real_actor_primary_payment_error_still_runs_independent_off_without_false_save_or_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);requests=[];closed=[]
            def checkpoint(name,value):
                (root/(name+'.json')).write_text(json.dumps(value),encoding='utf8')
            client=SimpleNamespace(output=root,normal_close=lambda reason:closed.append(reason),checkpoint=checkpoint)
            config=dict(scene_root=str(root),source_head='1'*40,native_build_source_head='2'*40,
                build_dir=str(root/'build'),machine_execution_gate={},actor_id=3,expected_start_date_raw=100,
                expected_source_save_sha256='3'*64,profile_limit_bytes=1000,driver_limit_bytes=2000,
                deadline_utc=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat(),prefix='r08-integration',
                payment_enable_once_authorized=False,natural_phase_enable_once_authorized=False)
            context=dict(repo_root=str(root),run_id='test-run',case_inputs={'r08_writer_one_day':config})
            idle=dict(state='idle',generation=0,starting_date_raw=0,target_date_raw=0,last_observed_date_raw=0,
                trigger_date_raw=0,speed=0,mode='decision_epoch',army_count=0,combat_count=0,
                completed_daily_ticks=0,intermediate_pause_count=0,trigger_flags=0,trigger_reasons=[],
                signed_date_delta_from_target_raw=0,overshoot_days=-1,pause_wrapper_called=False,
                pause_observed=False,terminal_observed=False,abnormal=False)
            row=dict(installed=True,available=True,capture_enabled=False,busy=False,clear_completed=True,
                epoch=1,active_captures=0,retained_records=0,qualified_records=0,status='disabled',readiness='off')
            class Packets:
                def __init__(self,*args,**kwargs):pass
                def request(self,name,tool,args):
                    requests.append((name,tool,args))
                    if tool==bridge.CASH_TOOL:
                        raise ValueError('synthetic transport error preserved before payment response')
                    if tool=='ck3_take_snapshot':
                        return dict(episode_run_id=None,episode_projection='native_campaign',paused=True,
                            map_ready=True,played_character={'character_id':3},revision=1,date_raw=100),{}
                    if tool=='ck3_execute_step':
                        return ({'tactical_daily_sentinel':idle} if 'query-tactical' in args['step'] else {}),{}
                    if tool in ('ck3_set_army_observer_research_sampling_v1','ck3_query_army_observer_research_sampling_v1'):
                        step=('query' if tool.startswith('ck3_query') else 'disable')+'-army-observer-research-sampling-v1'
                        return dict(step=step,accepted=True,status='completed',backend_id='native-headless',
                            army_observer_research_sampling_v1={family:dict(row) for family in FAMILIES}),{}
                    raise AssertionError('Unexpected tool '+tool)
            with patch.object(actor.subprocess,'check_output',return_value='1'*40), \
                 patch('ck3_live_run_id.current_machine_id',return_value='machine-test'), \
                 patch.object(bridge,'CommonPackets',Packets), \
                 patch.object(actor,'load_controller',return_value=SimpleNamespace()):
                result=actor.run_case(context,client)
            # No payment normalizer, cleanup helper or clock normalizer was mocked.
            terminal=json.loads((root/'R08-WRITER-TERMINAL.json').read_bytes())
            self.assertIn('transport error',result['error'])
            self.assertEqual(result['status'],'STOPPED_ERROR_PRESERVED_NO_REPLAY')
            self.assertTrue(result['cleanup']['clock_quiescent'])
            self.assertTrue(result['cleanup']['army_families_OFFclear'])
            self.assertFalse(terminal['OFFclear']);self.assertFalse(terminal['Save'])
            self.assertFalse(terminal['full_R08_qualified']);self.assertEqual(terminal['actual_days'],0)
            cash=[args['payment_sampling'] for _,tool,args in requests if tool==bridge.CASH_TOOL]
            self.assertEqual(cash,['query','disable','query'])
            self.assertEqual(sum(tool=='ck3_set_army_observer_research_sampling_v1' for _,tool,_ in requests),1)
            self.assertEqual(sum(tool=='ck3_query_army_observer_research_sampling_v1' for _,tool,_ in requests),1)
            self.assertFalse(any(tool=='ck3_save_checkpoint' for _,tool,_ in requests))
            self.assertFalse(any('advance' in args.get('step','') or 'arm-tactical' in args.get('step','') for _,_,args in requests))
            self.assertFalse((root/'r08-before-observer-awaiting.json').exists())
            self.assertFalse((root/'r08-writer-control').exists())
            with self.assertRaises(ValueError):client.normal_close('unproved payment OFF')
            self.assertEqual(closed,[])


if __name__=='__main__':unittest.main()
