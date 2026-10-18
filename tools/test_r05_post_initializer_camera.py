"""One focused file-only coordination case; no host, camera, SDK or game."""
from pathlib import Path
from types import SimpleNamespace
import argparse,hashlib,importlib.util,json,sys,tempfile,unittest


class CameraWait(unittest.TestCase):
    def test_explicit_success_default_no_wait_and_original_timeout_bounds(self):
        p=REPO/'tools/ck3_mod_acceptance_cases/r05_initialize_observe_adapter.py'
        spec=importlib.util.spec_from_file_location('r05_camera_adapter_under_test',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        from ck3_live_run_id import current_machine_id
        machine=current_machine_id();run='synthetic-same-case';settings={
            'normal_close_reserve_seconds':40,'cleanup_save_reserve_seconds':60,'deadline_unix_seconds':2000}
        init={'machine_id':machine,'pid':42,'natural_days_advanced':0,
              'assessment':{'status':'prepared_low_stock','low_stock_observed':True,
                            'physical_soldiers_unchanged':True,'actual_after_stock_raw':0},
              'independent_after':{'pid':42,'current_supply_raw':0,
                                   'machine_independent_frame':{'date_raw':1234,'episode_run_id':run}}}
        class Clock:
            elapsed=0
            def time(self):return 1000+self.elapsed
            def monotonic(self):return self.elapsed
            def sleep(self,n):self.elapsed+=n
        class Client:
            def __init__(self,output,clock,hold=2000):
                self.output=output;self.clock=clock;self._hold=hold;self.saved=[];self.guards=[]
                self.selection=SimpleNamespace(run_dir=Path(run))
            def remaining(self):return self._hold-self.clock.time()
            def guard(self,*,reserve):
                self.guards.append(reserve)
                if self.remaining()<=reserve:raise ValueError('original hold guard expired')
            def checkpoint(self,name,value):self.saved.append((name,value))
            def execute_plan(self,*a,**k):raise AssertionError('camera wait must not call SDK')
        self.assertIsNone(module.post_initializer_camera_settings(None))
        self.assertIsNone(module.post_initializer_camera_settings({'enabled':False}))
        self.assertIsNone(module.await_post_initializer_camera({},object(),{}, {},None))
        self.assertEqual(module.post_initializer_camera_settings({'enabled':True,'maximum_wait_seconds':900}), {'maximum_wait_seconds':900})
        with self.assertRaises(ValueError):module.post_initializer_camera_settings({'enabled':True,'maximum_wait_seconds':901})
        option=module.post_initializer_camera_settings({'enabled':True,'maximum_wait_seconds':2})
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            root=Path(temporary);receipt=root/'actual-start.json';raw=b'{"operation":"StartRecording","synthetic":true}\n';receipt.write_bytes(raw)
            signal={'machine_id':machine,'run_id':run,'bridge_pid':42,'date_raw':1234,
                    'camera_started':True,'start_receipt':{'path':receipt.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}}
            marker=root/'post-initializer-camera-started.actual.json';marker.write_text(json.dumps(signal),encoding='utf8')
            clock=Clock();client=Client(root,clock)
            accepted=module.await_post_initializer_camera({'machine_id':machine},client,settings,init,option,
                _time=clock.time,_monotonic=clock.monotonic,_sleep=clock.sleep)
            self.assertTrue(accepted['camera_started']);self.assertTrue(accepted['coordination_only'])
            self.assertFalse(accepted['video_or_R05_PASS_inferred']);self.assertEqual(clock.elapsed,0)
            awaiting=client.saved[0][1];self.assertEqual(awaiting['stock_raw'],0)
            self.assertEqual(awaiting['original_hold_unix_seconds'],2000)
            self.assertEqual(awaiting['signal_path'],str(marker));self.assertEqual(len(client.saved),2)
            signal['date_raw']+=1;marker.write_text(json.dumps(signal),encoding='utf8')
            clock=Clock();client=Client(root,clock)
            with self.assertRaisesRegex(ValueError,'machine/run/PID/date'):
                module.await_post_initializer_camera({'machine_id':machine},client,settings,init,option,
                    _time=clock.time,_monotonic=clock.monotonic,_sleep=clock.sleep)
            marker.unlink()
            clock=Clock();client=Client(root,clock)
            with self.assertRaisesRegex(ValueError,'wait timed out'):
                module.await_post_initializer_camera({'machine_id':machine},client,settings,init,option,
                    _time=clock.time,_monotonic=clock.monotonic,_sleep=clock.sleep)
            self.assertEqual(clock.elapsed,2);self.assertEqual(len(client.saved),1)
            clock=Clock();client=Client(root,clock,hold=1100.5)
            with self.assertRaisesRegex(ValueError,'reserve exhausted'):
                module.await_post_initializer_camera({'machine_id':machine},client,settings,init,option,
                    _time=clock.time,_monotonic=clock.monotonic,_sleep=clock.sleep)
            self.assertEqual(clock.elapsed,0)
            bad={**init,'assessment':{**init['assessment'],'low_stock_observed':False}}
            with self.assertRaisesRegex(ValueError,'prepared low stock'):
                module.await_post_initializer_camera({'machine_id':machine},Client(root,Clock()),settings,bad,option)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--dependencies-root',type=Path);p.add_argument('--scratch-root',type=Path,required=True)
    a=p.parse_args();REPO=a.repo_root.resolve();deps=(a.dependencies_root or REPO).resolve();SCRATCH=a.scratch_root.resolve()
    if not SCRATCH.is_dir():raise ValueError('explicit existing scratch root required')
    sys.path[:0]=[str(REPO/'tools'),str(deps/'tools'),str(deps/'ck3_autonomous_player/src')]
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CameraWait))
    raise SystemExit(0 if result.wasSuccessful() else 1)
