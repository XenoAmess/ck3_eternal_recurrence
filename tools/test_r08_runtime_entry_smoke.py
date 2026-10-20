"""Real Python/MCP entry and native-send smoke; no pipe, SDK, host or game.

CI: python -B -X utf8 tools/test_r08_runtime_entry_smoke.py
Deployment gate: same command --runtime ACTUAL_FROZEN_RUNTIME_JSON
The latter must use the complete generated runtime environment, unmodified.
"""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile
import unittest

parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--repo',type=Path)
parser.add_argument('--runtime',type=Path)
parser.add_argument('--host-path',type=Path)
parser.add_argument('--host-patch',type=Path)
parser.add_argument('--payment-path',type=Path)
parser.add_argument('--actor-path',type=Path)
parser.add_argument('--scratch-root',type=Path)
opts,rest=parser.parse_known_args()
sys.argv=[sys.argv[0],*rest]
REPO=(opts.repo or Path(__file__).resolve().parents[1]).resolve()

# Executed with -c from a fresh external cwd. No sys.path insertions, runpy,
# import shim, payment normalizer patch or environment repair in this child.
CHILD=r'''
import asyncio, hashlib, importlib.util, inspect, json, re, sys
from pathlib import Path
from types import SimpleNamespace
repo=Path(sys.argv[1]).resolve()
if sys.argv[3]=='bootstrap':
    spec=importlib.util.spec_from_file_location('r08_real_host_smoke',sys.argv[2])
    host=importlib.util.module_from_spec(spec)
    if len(sys.argv)>4 and sys.argv[4]:
        # Apply the author's exact unified patch in memory; no large source copy.
        relative='ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
        patch=Path(sys.argv[4]).read_text(encoding='utf-8').splitlines(keepends=True)
        base=Path(sys.argv[2]).read_text(encoding='utf-8').splitlines(keepends=True)
        out=[];cursor=0;i=0;selected=False;hunks=0
        while i<len(patch):
            line=patch[i]
            if line.startswith('--- '): selected=line.strip()=='--- a/'+relative
            if selected and line.startswith('@@ '):
                m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',line)
                assert m,line
                start=int(m[1])-1;assert start>=cursor
                out.extend(base[cursor:start]);cursor=start;i+=1;hunks+=1
                while i<len(patch) and not patch[i].startswith(('@@ ','--- ')):
                    row=patch[i]
                    if row.startswith((' ','-')):
                        assert base[cursor]==row[1:],(cursor,row,base[cursor])
                        cursor+=1
                    if row.startswith((' ','+')): out.append(row[1:])
                    i+=1
                continue
            i+=1
        assert hunks>0,'candidate patch contains no actual host hunk'
        out.extend(base[cursor:]);source=''.join(out)
        host.__dict__['__candidate_source_sha256__']=hashlib.sha256(source.encode('utf-8')).hexdigest()
        exec(compile(source,sys.argv[2],'exec'),host.__dict__)
    else: spec.loader.exec_module(host)
    host.clean_imports(repo)
if len(sys.argv)>5 and (sys.argv[5] or sys.argv[3]=='legacy-import-negative-control'):
    import xar_autoplayer.bridge
    path=Path(sys.argv[5]) if sys.argv[5] else repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py'
    name='xar_autoplayer.bridge.war_payment_observations_v1'
    spec=importlib.util.spec_from_file_location(name,path)
    payment=importlib.util.module_from_spec(spec);sys.modules[name]=payment
    source=path.read_text(encoding='utf-8')
    if sys.argv[3]=='legacy-import-negative-control':
        source=source.replace('from ck3_live_run_id import','from tools.ck3_live_run_id import')
        assert source.count('from tools.ck3_live_run_id import')==2
    exec(compile(source,str(path),'exec'),payment.__dict__)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.version_identity import CK3_12004
import xar_autoplayer.bridge.native_driver as source
assert Path(source.__file__).resolve()==repo/'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
sent=[]
class NativeBoundaryReached(BaseException): pass
def send(value):
    sent.append(value)
    raise NativeBoundaryReached()
frame=dict(revision=3,native_revision=5,paused=True,map_ready=True,
    played_character={'alive':True,'character_id':7},
    diagnostics={'hello':{'expected_ck3_version':CK3_12004.game_version,
                         'expected_ck3_sha256':CK3_12004.executable_sha256}})
# Never run its constructor: that would own real native transport.
driver=object.__new__(NativeHeadlessGameplayDriver)
driver.command_timeout_seconds=1
driver.allow_private_war_cash_query=True
driver.endpoint=SimpleNamespace(send=send)
driver.take_snapshot_without_native_command_history=lambda:frame
driver.take_snapshot=lambda:frame
server=create_server(driver)
out=[]
for mode in ('query','enable','disable'):
    sent.clear()
    args={'expected_revision':3,'payment_sampling':mode}
    if mode=='enable': args['payment_window_contract']='same_owned_process_no_load_v1'
    try:
        result=server.call_tool('ck3_query_war_cash_current_resources_private_v1',args)
        if inspect.isawaitable(result): result=asyncio.run(result)
        raise AssertionError('tool returned without reaching native-send boundary')
    except NativeBoundaryReached:
        assert len(sent)==1
        value=sent[0]
        assert value['step']=='query-war-cash-current-resources-v1'
        assert value['type']=='execute_step' and value['expected_revision']==5
        assert value['war_payment_sampling']==mode
        assert type(value['war_payment_machine_id']) is str and value['war_payment_machine_id']
        assert ('war_payment_window_contract' in value)==(mode=='enable')
        out.append({'mode':mode,'native_send_count':1,'request':value})
    except Exception as error:
        print(json.dumps({'error':type(error).__name__+': '+str(error),'native_send_count':len(sent)}))
        raise SystemExit(2)
# Public schema guard must reject misuse before reaching the same endpoint.
sent.clear()
try:
    result=server.call_tool('ck3_query_war_cash_current_resources_private_v1',
        {'expected_revision':3,'payment_sampling':'query','payment_window_contract':'same_owned_process_no_load_v1'})
    if inspect.isawaitable(result): result=asyncio.run(result)
    raise AssertionError('invalid control contract accepted')
except Exception as error:
    assert 'window contract' in str(error) or 'enable alone' in str(error),str(error)
assert sent==[]
print(json.dumps({'boundary_modes':out,'invalid_control_native_sends':0,'native_transport_replaced':True}))
'''

class RuntimeEntrySmoke(unittest.TestCase):
    def child(self,parts,python=None,bootstrap=True,legacy_import=False):
        env={**os.environ,'PYTHONPATH':os.pathsep.join(map(str,parts)),
             'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'}
        with tempfile.TemporaryDirectory(dir=opts.scratch_root) as cwd:
            self.assertNotEqual(Path(cwd).resolve(),REPO)
            host=opts.host_path or REPO/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
            result=subprocess.run([python or sys.executable,'-B','-X','utf8','-c',CHILD,str(REPO),str(host),
                'legacy-import-negative-control' if legacy_import else 'bootstrap' if bootstrap else 'skip-bootstrap',
                str(opts.host_patch or ''),str(opts.payment_path or '')],
                cwd=cwd,env=env,text=True,capture_output=True,timeout=45)
        return result

    def test_full_declared_environment_reaches_registered_tool_native_boundary(self):
        if opts.runtime:
            runtime=json.loads(opts.runtime.read_bytes())
            self.assertEqual(Path(runtime['repo_root']).resolve(),REPO)
            parts=[Path(x) if Path(x).is_absolute() else opts.runtime.parent/x
                   for x in runtime['runtime_environment']['PYTHONPATH']]
            python=runtime['python']
        else:
            # R0222 import environment: host must establish its own package root.
            # Actual deployment must additionally pass --runtime unchanged.
            parts=[REPO/'ck3_autonomous_player/src',REPO/'tools']
            python=None
        result=self.child(parts,python)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        value=json.loads(result.stdout)
        self.assertEqual([x['mode'] for x in value['boundary_modes']],['query','enable','disable'])
        self.assertTrue(all(x['native_send_count']==1 for x in value['boundary_modes']))
        self.assertEqual(value['invalid_control_native_sends'],0)

    def test_published_r0222_missing_repository_root_is_detected_before_native_send(self):
        result=self.child([REPO/'ck3_autonomous_player/src',REPO/'tools'],bootstrap=False,legacy_import=True)
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        value=json.loads(result.stdout)
        self.assertIn("No module named 'tools'",value['error'])
        self.assertEqual(value['native_send_count'],0)

    def test_complete_environment_positive_control_reaches_native_boundary(self):
        result=self.child([REPO/'ck3_autonomous_player/src',REPO/'tools',REPO],bootstrap=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

PARENT_CHILD=r'''
import copy,importlib.util,json,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
repo=Path(sys.argv[1]).resolve()
if sys.argv[2]:
    import xar_autoplayer.bridge
    name='xar_autoplayer.bridge.war_payment_observations_v1'
    spec=importlib.util.spec_from_file_location(name,sys.argv[2]);payment=importlib.util.module_from_spec(spec)
    sys.modules[name]=payment;spec.loader.exec_module(payment)
from xar_autoplayer.bridge import war_payment_observations_v1 as payment
from ck3_live_run_id import current_machine_id
from xar_autoplayer.bridge.version_identity import CK3_12004
import ck3_mod_acceptance_cases
if sys.argv[3]:
    name='ck3_mod_acceptance_cases.r08_writer_one_day'
    spec=importlib.util.spec_from_file_location(name,sys.argv[3]);actor=importlib.util.module_from_spec(spec)
    sys.modules[name]=actor;spec.loader.exec_module(actor)
    # Candidate will be installed at this exact module path; preserve unchanged
    # sibling controller lookup without copying or substituting the controller.
    actor.__file__=str(repo/'tools/ck3_mod_acceptance_cases/r08_writer_one_day.py')
else:
    from ck3_mod_acceptance_cases import r08_writer_one_day as actor
fixture=repo/'ck3_autonomous_player/tests/unit/fixtures/war_payment_compiled_12004_a06.json'
case=next(x for x in json.loads(fixture.read_bytes()) if x['case']=='controlled_window_personal')
j=copy.deepcopy(case['value'].get(payment.JOURNAL_KEY,case['value']));j['machine_id']=current_machine_id()
s=j['current_session'];date=s['native_date_raw']&0xffffffff
if date>=1<<31:date-=1<<32
frame=dict(revision=s['snapshot_revision']+1,native_revision=s['snapshot_revision'],date_raw=date,
    paused=True,map_ready=True,episode_run_id=None,episode_projection='native_campaign',
    played_character={'character_id':s['player_character_full_id'],'alive':True},
    diagnostics={'bridge_pid':s['pid'],'connection_generation':s['connection_generation'],
    'hello':{'expected_ck3_version':CK3_12004.game_version,'expected_ck3_sha256':CK3_12004.executable_sha256}})
seen=[];collected=[];out=Path.cwd()
class Client:
    output=out
    selection=SimpleNamespace(locations={'python':sys.executable})
    def normal_close(self,value):raise AssertionError('offline test must not close game')
    def checkpoint(self,name,value):
        path=out/(name+'.json');path.write_text(json.dumps(value),encoding='utf-8');return path
    def validate_frame(self,*args,**kwargs):pass
    def execute_plan(self,steps,name,**kwargs):
        step=steps[0];seen.append(step['tool'])
        if step['tool']=='ck3_take_snapshot':body=copy.deepcopy(frame)
        elif step['tool']=='ck3_query_war_cash_current_resources_private_v1':
            if step['args'].get('payment_sampling')!='query':raise RuntimeError('offline stop: cleanup has no live transport')
            body={payment.JOURNAL_KEY:copy.deepcopy(j),payment.CONTROL_KEY:
                {'requested':'query','accepted':True,'reason':'already_enabled'}}
        else:raise RuntimeError('offline stop: cleanup has no live transport')
        rows=[{'id':step['id'],'ok':True,'result':body}]
        (out/(name+'.actual-results.json')).write_text(json.dumps({'rows':rows}),encoding='utf-8')
        return rows
def collect(*args,**kwargs):
    collected.append(True);raise RuntimeError('offline stop after actual actor payment normalization')
actor.bridge.collect_current_context=collect
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
settings=dict(scene_root=str(out),source_head=head,native_build_source_head='2'*40,build_dir=str(out),
    machine_execution_gate={},actor_id=frame['played_character']['character_id'],expected_start_date_raw=date,
    expected_source_save_sha256='3'*64,profile_limit_bytes=1,driver_limit_bytes=1,
    deadline_utc='2100-01-01T00:00:00Z',prefix='r08-parent-smoke',payment_enable_once_authorized=False)
result=actor.run_case({'repo_root':str(repo),'output':str(out),'run_id':'OFFLINE-SMOKE',
    'case_inputs':{'r08_writer_one_day':settings}},Client())
print(json.dumps({'actual_actor_payment_normalization_reached_next_boundary':bool(collected),
    'result_error':result.get('error'),'full_R08_qualified':result['full_R08_qualified'],'queue_tools':seen}))
raise SystemExit(0 if collected else 2)
'''

class ActorParentRuntimeSmoke(unittest.TestCase):
    def test_actual_script_parent_environment_reaches_after_payment_normalization(self):
        env={**os.environ,'PYTHONPATH':os.pathsep.join(map(str,[REPO/'ck3_autonomous_player/src',REPO/'tools'])),
            'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'}
        with tempfile.TemporaryDirectory(dir=opts.scratch_root) as cwd:
            script=Path(cwd)/'actual_actor_parent_smoke.py'
            script.write_text(PARENT_CHILD,encoding='utf-8')
            result=subprocess.run([sys.executable,'-B','-X','utf8',str(script),str(REPO),
                str(opts.payment_path or ''),str(opts.actor_path or '')],cwd=cwd,env=env,
                text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        value=json.loads(result.stdout)
        self.assertTrue(value['actual_actor_payment_normalization_reached_next_boundary'])
        self.assertFalse(value['full_R08_qualified'])

if __name__=='__main__':unittest.main()
