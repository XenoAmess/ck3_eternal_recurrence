"""One focused synthetic failure/identity/no-camera regression for the new gate."""
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace as NS
import argparse,json,sys,tempfile,unittest
from unittest.mock import Mock
p=argparse.ArgumentParser(add_help=False)
p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--candidate-tools',type=Path)
a,rest=p.parse_known_args()
sys.path[:0]=[str(a.repo/'tools'),str(a.repo/'ck3_autonomous_player/src')]
if a.candidate_tools:sys.path.insert(0,str(a.candidate_tools))
import ck3_mod_acceptance_cases
if a.candidate_tools:
    ck3_mod_acceptance_cases.__path__.insert(0,str(a.candidate_tools/'ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases import r04_county_entry as county


class BeforeMoveFrame(unittest.TestCase):
    def test_wrong_identity_timeout_and_valid_review_preserve_move_and_camera_boundaries(self):
        for mode in ('wrong-date','no-signal','valid-review'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                output=Path(directory);tick=NS(now=0.)
                signal=output/'before-move-frame-reviewed.json'
                class Client:
                    selection=NS(run_dir=Path('synthetic-run'))
                    guard=Mock()
                    def checkpoint(self,name,value):
                        path=output/(name+'.json')
                        with path.open('x',encoding='utf-8') as stream:json.dump(value,stream)
                        if name=='before-move-frame-awaiting' and mode!='no-signal':
                            binding={k:value[k] for k in ('machine_id','run_id','bridge_pid','date_raw')}
                            if mode=='wrong-date':binding['date_raw']+=24
                            review_ref={}
                            if mode=='valid-review':
                                now=datetime.now(timezone.utc).isoformat()
                                image=output/'synthetic-original.fixture';image.write_bytes(b'synthetic pixels; never a live screenshot')
                                original=county.pin(image)
                                capture=dict(schema='xar.e04.owned-client-original-frame.v1',machine_id='synthetic-machine',
                                    run_id='synthetic-run',pid=30,recording_started=False,observed_at_utc=now,
                                    source={'owned_ck3_pid':30,'owned_ck3_create_time':3.5},
                                    desktop_original=original,client_original=original,synthetic_only=True)
                                capture_path=output/'synthetic-capture.json';capture_path.write_text(json.dumps(capture),encoding='utf-8')
                                review=dict(schema='xar.e04.owned-client-root-review.v1',machine_id='synthetic-machine',
                                    run_id='synthetic-run',reviewer='/root',root_reviewed_window_only=True,
                                    root_reviewed_no_hover=True,content='map-context',reviewed_at_utc=now,
                                    capture=county.pin(capture_path),client_original=original,synthetic_only=True)
                                review_path=output/'synthetic-review.json';review_path.write_text(json.dumps(review),encoding='utf-8')
                                review_ref=county.pin(review_path)
                            signal.write_text(json.dumps({**binding,'frame_reviewed':True,'review_receipt':review_ref}),encoding='utf-8')
                        return path
                Client.output=output
                client=Client();io=NS(client=client,context={'machine_id':'synthetic-machine'},
                    settings={'deadline_unix_seconds':4102444800})
                frame=dict(date_raw=1000,diagnostics={'bridge_pid':30})
                result={'Move_attempts':0,'actual_binding':{'create_time':3.5}}
                settings=NS(before_move_frame_required=True,camera_timeout_seconds=1,
                    normal_close_reserve=900,cleanup_save_reserve=120,one_day_timeout=120)
                def sleep(seconds):tick.now+=seconds
                call=lambda:county.await_before_move_frame(io,frame,result,settings,
                    _time=lambda:0.,_monotonic=lambda:tick.now,_sleep=sleep)
                if mode=='wrong-date':
                    with self.assertRaisesRegex(ValueError,'machine/run/PID/date'):call()
                elif mode=='no-signal':
                    with self.assertRaisesRegex(TimeoutError,'no Move submitted'):call()
                else:
                    proof=call()
                    self.assertEqual(proof['status'],'ACTUAL_BEFORE_MOVE_FRAME_REVIEW_CONSUMED')
                    self.assertFalse(proof['camera_started']);self.assertFalse(proof['Move_submitted'])
                self.assertEqual(result['Move_attempts'],0)
                self.assertFalse((output/'before-action-camera-started.json').exists())
                self.assertTrue(all(c.kwargs['reserve']==1140 for c in client.guard.call_args_list))


if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest])
