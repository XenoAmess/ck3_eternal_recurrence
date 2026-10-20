"""STOP/admission ordering regression with fake callbacks."""
from __future__ import annotations
import sys
import types
import unittest
from textwrap import indent
from unittest.mock import patch
from tools.g2_saved_campaign.patch_observed_halt_close_loop_v1 import patch_observed_halt_close_loop_v1

EARLY = "from root_a10_early_owned_close_v1 import load_plan, execute_once\nearly_plan = load_plan(N, generation, now=now())\nif early_plan is not None:\n    normal_close_requested = True\n\n    def early_stop_owned(h: object, *, require_running: bool=False) -> object:\n        nonlocal cleanup_attempted, cleanup, forced\n        cleanup_attempted = True\n        forced = handle.process.poll() is None\n        cleanup = runtime.stop_tracked(h, require_running=require_running)\n        return cleanup\n    try:\n        early = execute_once(N, early_plan, generation, handle, kernel=kernel_exit, normal_close=request_owned_close, stop_tracked=early_stop_owned, write=write, now=now(), deadline=deadline)\n    except BaseException:\n        if not cleanup_attempted:\n            early_stop_owned(handle, require_running=False)\n        raise\n    normal_exit = early['normal_exit']\n    forced = early['forced_path_used']\n    cleanup_attempted = early['cleanup_attempted']\n    cleanup = early['cleanup']\n    reason = 'Root_observed_halt_early_owned_Game_close'\n    break"
CLEANUP = "if not cleanup_attempted:\n    if generation is not None and kernel_exit(generation) is None:\n        if cleanup_wait_seconds(deadline, GAME_CLOSE_RESERVE_SECONDS) > 0:\n            try:\n                normal_close_requested = True\n                normal_exit = request_owned_close(generation, seconds=GAME_CLOSE_RESERVE_SECONDS, deadline=deadline)\n            except Exception as error:\n                write(N / 'ROOT-NORMAL-CLOSE-UNCONFIRMED-C23.json', {'at_utc': now().isoformat(), 'error': str(error)[:2048], 'submission_repeated': False})\n        forced = kernel_exit(generation) is None\n    else:\n        forced = handle.process.poll() is None\n    cleanup_attempted = True\n    cleanup = runtime.stop_tracked(handle, require_running=False)"

def original_source() -> bytes:
    prefix = """def main(args):
    cleanup_attempted=False
    cleanup=None
    forced=False
    failure=None
    try:
"""
    body = 'while not (N / "STOP-OWNED-GAME-C23").exists():\n'
    body += indent(EARLY + "\nkeeper.require_live()\ntime.sleep(1)\n", "    ")
    suffix = """    except BaseException as error:
        failure=type(error).__name__
        events.append('failure')
    finally:
        events.append('SDK_grace')
"""
    return (prefix + indent(body,"        ") + suffix + indent(CLEANUP+"\n","        ")
        + "    return dict(failure=failure,cleanup_attempted=cleanup_attempted,forced=forced)\n").encode()

class World:
    def __init__(self,case):
        self.case=case
        self.stop=case in {'before','none','invalid','unknown','write_error'}
        self.admission=self.stop and case!='none'
        self.events=[];self.writes={}
        self.normal_calls=0;self.stop_calls=0;self.reads=0;self.sleeps=0;self.running=True
    def load(self,*args,**kwargs):
        self.reads+=1;self.events.append('admission')
        if self.case=='invalid':raise ValueError('invalid admission')
        available=self.admission
        if self.case=='between' and self.reads==1:self.admission=self.stop=True
        return {'admitted':True} if available else None
    def write(self,path,value):
        if path.name in self.writes:raise AssertionError('repeated write')
        if self.case=='write_error' and path.name=='RESULT':raise OSError('unknown result write')
        self.writes[path.name]=value
    def normal(self,*args,**kwargs):
        self.normal_calls+=1;self.events.append('WM_CLOSE')
        if self.normal_calls!=1:raise AssertionError('repeated WM_CLOSE')
        if self.case=='unknown':return None
        self.running=False
        return {'exit_code':0}
    def stop_owned(self,*args,**kwargs):
        self.stop_calls+=1;self.events.append('stop_tracked')
        if self.stop_calls!=1:raise AssertionError('repeated stop')
        if self.case=='unknown':raise OSError('cleanup unknown')
        self.running=False
        return {'cleanup_proven':True}
    def execute(self,root,plan,generation,handle,*,kernel,normal_close,stop_tracked,write,now,deadline):
        write(root/'ATTEMPT',{'once':True})
        normal=normal_close(generation,30,deadline=deadline)
        try:cleanup=stop_tracked(handle,require_running=False)
        except OSError:cleanup=None
        unknown=self.case=='unknown'
        write(root/'RESULT',{'actual_exit_known':not unknown,'normal_exit_qualified':not unknown})
        return dict(normal_exit=normal,forced_path_used=unknown,cleanup_attempted=True,cleanup=cleanup)
    def sleep(self,seconds):
        self.sleeps+=1
        if self.sleeps>3:raise AssertionError('loop did not stop')
        if self.case=='after':self.admission=self.stop=True
    def run(self,raw):
        world=self
        class MemoryPath:
            def __init__(self,name='ROOT'):self.name=name
            def __truediv__(self,name):return MemoryPath(name)
            def exists(self):
                if self.name=='STOP-OWNED-GAME-C23':
                    world.events.append('STOP')
                    return world.stop
                return self.name in world.writes
        module=types.ModuleType('root_a10_early_owned_close_v1')
        module.load_plan=self.load;module.execute_once=self.execute
        env=dict(N=MemoryPath(),events=self.events,generation=object(),
            handle=types.SimpleNamespace(process=types.SimpleNamespace(poll=lambda:None if self.running else 0)),
            runtime=types.SimpleNamespace(stop_tracked=self.stop_owned),write=self.write,
            kernel_exit=lambda generation:None if self.running else {'exit_code':0},
            request_owned_close=self.normal,now=lambda:None,deadline=None,
            keeper=types.SimpleNamespace(require_live=lambda:self.events.append('body')),
            time=types.SimpleNamespace(sleep=self.sleep),cleanup_wait_seconds=lambda *a:30,GAME_CLOSE_RESERVE_SECONDS=30)
        with patch.dict(sys.modules,{module.__name__:module}):
            exec(compile(raw,'supervisor-loop-memory-fixture','exec'),env)
            return env['main'](None)

class LoopRegression(unittest.TestCase):
    def test_seven_stop_and_result_cases(self)->None:
        for kind in ('before','after','between','none','invalid','unknown','write_error'):
            with self.subTest(kind=kind):
                raw=original_source()
                if kind in ('before','after','between'):
                    old=World(kind);old.run(raw)
                    self.assertNotIn('ATTEMPT',old.writes)
                w=World(kind);out=w.run(patch_observed_halt_close_loop_v1(raw))
                self.assertEqual((w.normal_calls,w.stop_calls),(1,1))
                early=kind not in ('none','invalid')
                self.assertEqual('ATTEMPT' in w.writes,early)
                self.assertEqual(w.events.index('stop_tracked')<w.events.index('SDK_grace'),early)
                self.assertEqual('RESULT' in w.writes,early and kind!='write_error')
                expected='ValueError' if kind=='invalid' else 'OSError' if kind=='write_error' else None
                self.assertEqual(out['failure'],expected)
                if kind=='unknown':
                    self.assertEqual(w.writes['RESULT'],{'actual_exit_known':False,'normal_exit_qualified':False})
                if early:self.assertTrue(out['cleanup_attempted'])
    def test_invalid_inputs(self)->None:
        raw=original_source()
        bad=[b'',bytearray(raw),patch_observed_halt_close_loop_v1(raw),raw+raw,
             raw.replace(b'cleanup_attempted = True',b'cleanup_attempted = False',1),
             raw.replace(b'if not cleanup_attempted:',b'if False:')]
        for value in bad:
            with self.assertRaises((ValueError,TypeError)):
                patch_observed_halt_close_loop_v1(value)

if __name__=='__main__':
    unittest.main()
