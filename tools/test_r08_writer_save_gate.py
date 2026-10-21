"""Save uncertainty must keep the existing actor close gate shut; no native claim."""
from pathlib import Path
from types import SimpleNamespace
import sys,unittest

sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[1]/'ck3_autonomous_player/src')]
from ck3_mod_acceptance_cases import r08_writer_one_day as actor
from xar_autoplayer.bridge.army_observer_research_sampling_control import FAMILIES
from ck3_mod_acceptance_cases.ordinary_save_contract import obj


class SaveGate(unittest.TestCase):
    def test_unknown_save_or_independent_after_is_never_replayed_and_withholds_quit(self) -> None:
        for failed in ('Save-once','Save-independent-after'):
            with self.subTest(failed=failed):
                calls: list[tuple[str,str,dict[str,object]]]=[];closed: list[str]=[]
                client=SimpleNamespace(_handle=object(),_process={'pid':41},
                    normal_close=lambda why:closed.append(why))
                gate=actor.CloseGate(client)
                idle=dict(state='idle',generation=0,starting_date_raw=0,target_date_raw=0,last_observed_date_raw=0,
                    trigger_date_raw=0,speed=0,mode='decision_epoch',army_count=0,combat_count=0,
                    completed_daily_ticks=0,intermediate_pause_count=0,trigger_flags=0,trigger_reasons=[],
                    signed_date_delta_from_target_raw=0,overshoot_days=-1,pause_wrapper_called=False,
                    pause_observed=False,terminal_observed=False,abnormal=False)
                row=dict(installed=True,available=True,capture_enabled=False,busy=False,clear_completed=True,
                    epoch=1,active_captures=0,retained_records=0,qualified_records=0,status='disabled',readiness='off')
                def call(label: str,tool: str,args: dict[str,object]) -> dict[str,object]:
                    calls.append((label,tool,args))
                    if label==failed:raise TimeoutError('synthetic original result unknown')
                    if tool=='ck3_save_checkpoint':return {'checkpoint':{'status':'saved','date_raw':100}}
                    if tool=='ck3_execute_step':return {'tactical_daily_sentinel':idle}
                    step=('query' if tool.startswith('ck3_query') else 'disable')+'-army-observer-research-sampling-v1'
                    return dict(step=step,accepted=True,status='completed',backend_id='native-headless',
                        army_observer_research_sampling_v1={family:dict(row) for family in FAMILIES})
                def snapshot(label: str) -> dict[str,object]:
                    calls.append((label,'snapshot',{}))
                    if label==failed:raise TimeoutError('synthetic independent endpoint unknown')
                    return dict(revision=1,date_raw=100,native_revision=1,snapshot_id='synthetic-native-1',
                        episode_projection='native_campaign',backend_id='native-headless',
                        source='injected-dll-named-pipe',map_ready=True,paused=True,local_player_id=29829,
                        played_character=dict(character_id=29829,alive=True,source='native'),
                        diagnostics=dict(connected=True,bridge_pid=41,connection_generation=1,
                            pipe_name='synthetic-retained-pipe'),
                        managed_campaign_run_binding=dict(run_id='synthetic-run',state_dir='synthetic-state',
                            bridge_pipe='synthetic-retained-pipe',host_path='synthetic-host',
                            frozen_argv_sha256='a'*64))
                def payment(label: str,mode: str) -> dict[str,object]:
                    calls.append((label,'payment',{'mode':mode}))
                    return {'sampling':dict(available=True,capture_enabled=False,busy=False,clear_completed=True,
                        active_captures=0,retained_records=0)}
                cleanup,errors,days=actor.cleanup_writer_window(call,snapshot,payment,gate,
                    observer_claimed=False,expected_start_date_raw=100)
                self.assertTrue(cleanup['OFFclear']);self.assertFalse(cleanup['Save'])
                self.assertFalse(gate.save_verified);self.assertTrue(errors);self.assertIsNone(days)
                self.assertEqual(sum(tool=='ck3_save_checkpoint' for _,tool,_ in calls),1)
                self.assertEqual(sum(label=='Save-independent-after' for label,_,_ in calls),
                    0 if failed=='Save-once' else 1)
                proof = obj(cleanup['ordinary_save_proof'], 'synthetic unconfirmed proof')
                self.assertEqual(proof['reason_code'], 'TimeoutError')
                expected = ('synthetic original result unknown' if failed=='Save-once'
                    else 'synthetic independent endpoint unknown')
                self.assertIn(expected, str(proof['detail']))
                self.assertEqual('Save_result' in cleanup, failed=='Save-independent-after')
                with self.assertRaisesRegex(ValueError,'Save unproved'):client.normal_close('must not Quit')
                self.assertEqual(closed,[])


if __name__=='__main__':unittest.main()
