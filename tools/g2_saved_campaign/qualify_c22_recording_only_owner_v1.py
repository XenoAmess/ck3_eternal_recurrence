"""RAM-only C22 source/owner qualification. No OBS/Game/Task calls."""
import ast, ctypes, hashlib, importlib.util, json, os, subprocess, sys, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[2]
PRODUCER=REPO/'tools/g2_saved_campaign/prepare_c22_recording_only_owner_v1.py'
PLAN=REPO/'docs/ck3-native-ai/evidence/c22-recording-only-owner-source-plan-2026-10-20.json'
spec=importlib.util.spec_from_file_location('_C22_recording_recipe',PRODUCER)
recipe=importlib.util.module_from_spec(spec); spec.loader.exec_module(recipe)
FILES,MANIFEST=recipe.compose()
CAPTURE=FILES[recipe.P/recipe.CAPTURE]; STAGE=FILES[recipe.P/recipe.STAGE]

def function(raw,name):
    return next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name==name)

class Tests(unittest.TestCase):
    def test_capture_inverse_and_retry_preserved(self):
        original=recipe.BASE.read_bytes()
        self.assertEqual(ast.dump(function(original,'_replace_mutable_latest')),
                         ast.dump(function(CAPTURE,'_replace_mutable_latest')))
        calls=[n for n in ast.walk(ast.parse(CAPTURE)) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Name) and n.func.id=='advance_growth_deadline_v1']
        self.assertEqual(len(calls),2)
        damaged=original.replace(b'previous, changed = 0, time.monotonic()',b'previous, changed = 1, time.monotonic()',1)
        with patch.object(Path,'read_bytes',lambda p:damaged if p==recipe.BASE else saved_read(p)):
            with self.assertRaises(ValueError): recipe.compose()

    def test_pause_resume_and_real_stall(self):
        node=function(CAPTURE,'advance_growth_deadline_v1'); scope={}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-new-capture-helper','exec'),scope)
        advance=scope[node.name]
        state=advance(100,0.0,False,current=100,now=120.0,output_active=True,output_paused=True,error_message='stall')
        self.assertEqual(state,(100,120.0,True))
        state=advance(*state,current=100,now=150.0,output_active=True,output_paused=False,error_message='stall')
        self.assertEqual(state,(100,150.0,False))
        with self.assertRaisesRegex(RuntimeError,'stall'):
            advance(*state,current=100,now=181.0,output_active=True,output_paused=False,error_message='stall')
        with self.assertRaises(RuntimeError):
            advance(100,0.0,False,current=100,now=120.0,output_active=True,output_paused=None,error_message='stall')

    def owner_fixture(self,*,child_error=False,publication_error=False):
        g={'__file__':str(recipe.P/recipe.STAGE),'__name__':'_C22_fixture'}
        exec(compile(STAGE,str(recipe.P/recipe.STAGE),'exec'),g)
        calls=[]; writes={}; T=recipe.T; game=g['GAME']; pub=g['PUB']
        request={'session_id':'0f89dc70-fada-4f53-bd78-7c32d50f431f','worker_pid':123,
          'worker_creation_filetime':123456,'worker_executable':sys.executable,
          'receipt_root':str(T/'recordings/0f89dc70-fada-4f53-bd78-7c32d50f431f')}
        ref={'path':'retained-publisher-started','bytes':1,'sha256':'a'*64}
        capref={'path':str(recipe.P/recipe.CAPTURE),'bytes':len(CAPTURE),'sha256':hashlib.sha256(CAPTURE).hexdigest()}
        manifest={'capture':capref,'publisher_started':ref,'old_capture_closed':{'path':'old-capture-closed'}}
        launch={'pid':game[0],'creation_filetime':game[1]}
        placement={**launch,'status':'GREEN','hwnd':44,'target_desktop_id':'desktop1'}
        closed={'session_id':request['session_id'],'inputs_unbound':True,
                'engine_close':{'actual_exit_code':0,'normal_exit_proven':True,'forced_process_calls':0}}
        old={**closed,'session_id':'2b8912a6-757d-46a4-a8ae-b7702a730a90'}
        def read(p):
            p=Path(p)
            if p.name=='ROOT-ACTUAL-GAME-LAUNCH-C16.json': return launch
            if p.name=='ROOT-GAME-PLACEMENT-C16.json': return placement
            if p.name=='ROOT-OBS-PROFILE-C22.json': return {'continuous':True,'recording_root':str(T/'recordings'),'profile_name':'ManagedWindowCapture-new'}
            if p.name=='ROOT-OBS-PROFILE-C16.json': return {'profile_name':'ManagedWindowCapture-old'}
            if str(p)=='old-capture-closed': return old
            if p.name=='capture_closed.json': return closed
            raise AssertionError('unexpected fixture read '+str(p))
        class Call:
            def __init__(self,fn): self.fn=fn
            def __call__(self,*a): return self.fn(*a)
        def exitcode(h,p): p._obj.value=0; return 1
        class Generation:
            def __init__(self,pid,exe,*,creation_filetime):
                calls.append('retain-worker'); self.handle=77
                self.kernel=SimpleNamespace(WaitForSingleObject=Call(lambda *a:(calls.append('wait-worker') or 0)),GetExitCodeProcess=Call(exitcode))
            def __enter__(self): return self
            def __exit__(self,*a): calls.append('release-worker')
        def atomic(p,value,*,new):
            calls.append('write-'+p.name)
            if publication_error and p.name=='ROOT-OBS-RECORDING-REQUESTED-C22.json': raise PermissionError('fixture publication failure')
            if p in writes: raise FileExistsError(str(p))
            writes[p]=value
        def launch_recording(*a,**kw):
            calls.append('launch-recording'); self.assertEqual(kw['decision_publisher_receipt'],Path(ref['path']))
            return dict(request)
        def identity(pid):
            calls.append('read-live-identity'); return {'creation_filetime':pub[1] if pid==pub[0] else game[1]}
        api=SimpleNamespace(atomic=atomic,read_text_binding=lambda *a,**kw:{},process_identity=identity)
        apimodule=SimpleNamespace(started_reference=lambda *a:ref)
        capture=SimpleNamespace(launch_recording=launch_recording,_generation_helpers=lambda:(Generation,))
        def child(*a,**kw):
            calls.append('actual-child-import-slot')
            row={'status':'ACTUAL_CHILD_ENV_IMPORT_PREFLIGHT_PASS','machine_id':g['M'],'capture':capref,
                'bytecode_disabled':True,'same_interpreter':str(Path(sys.executable).resolve()),
                'module_origins':{n:'frozen-origin' for n in g['NAMES']}}
            return SimpleNamespace(returncode=1 if child_error else 0,stdout=json.dumps(row).encode(),stderr=b'')
        g.update(setup=lambda:(manifest,apimodule,api,capture),read=read,
          verified=lambda r:Path(r['path']),pin=lambda p:{'path':str(p),'bytes':1,'sha256':'b'*64})
        argv=['stage','--game-launch',str(T/'ROOT-ACTUAL-GAME-LAUNCH-C16.json'),
              '--placement',str(T/'ROOT-GAME-PLACEMENT-C16.json'),'--obs-profile',str(T/'ROOT-OBS-PROFILE-C22.json'),
              '--job-root',str(T/'recordings'),'--ffprobe','existing-ffprobe.exe',
              '--source-manifest',str(T/'ROOT-RECORDING-ONLY-SOURCE-PINS-C22.json')]
        with patch.object(sys,'argv',argv),patch.object(subprocess,'run',child),\
             patch.object(Path,'exists',lambda p:False),\
             patch.object(Path,'is_file',lambda p:p.name in ('capture_closed.json','completed.json')):
            if child_error:
                with self.assertRaisesRegex(ValueError,'child import preflight failed'): g['main']()
                self.assertNotIn('launch-recording',calls)
                return calls,writes
            code=g['main']()
        self.assertEqual(code,1 if publication_error else 0)
        self.assertLess(calls.index('actual-child-import-slot'),calls.index('launch-recording'))
        self.assertLess(calls.index('launch-recording'),calls.index('wait-worker'))
        self.assertIn('release-worker',calls)
        result=writes[T/'ROOT-RECORDING-ONLY-OWNER-CLOSED-C22.json']
        self.assertEqual(result['normal'],not publication_error)
        self.assertEqual(result['Game_stop_calls'],0); self.assertEqual(result['publisher_stop_calls'],0)
        return calls,writes

    def test_owner_borrows_publisher_and_waits_original_worker(self): self.owner_fixture()
    def test_failed_child_never_launches(self): self.owner_fixture(child_error=True)
    def test_publication_failure_still_retains_worker(self): self.owner_fixture(publication_error=True)

saved_read=Path.read_bytes

def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): raise SystemExit(1)
    outputs=[{'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for p,b in FILES.items()]
    plan={'schema':'xar.C22-recording-only-source-plan/v1','machine_id':recipe.MACHINE,
      'status':'SOURCE_QUALIFIED_RUNTIME_NOT_STARTED','sources':{'recipe':recipe.pin(PRODUCER),'qualifier':recipe.pin(Path(__file__))},
      'actual_capture_baseline':recipe.pin(recipe.BASE),'canonical_pause_recipe':MANIFEST['pause_recipe'],
      'canonical_pause_helper':MANIFEST['pause_helper'],'runtime_outputs':outputs,
      'source_manifest':MANIFEST,'qualification':{'focused_cases':result.testsRun,'passed':True,'real_OBS_Game_Task_calls':0,'scratch_files':0},
      'source_cap':32768,'runtime_prepare_cap':393216,'max_stage_bytes':12288,
      'runtime_logical_upper':221184,'runtime_allocation_upper':294912,'max_atomic_upper':98304,
      'profile_prepare_pending':'old completed2b portable config exact rename card before new profile prepare',
      'required_runtime_outputs':['ROOT-RECORDING-ONLY-SOURCE-PINS-C22.json','ROOT-OBS-PROFILE-C22.json'],
      'Task':{'role':'display_owner','root':'P/c22-source22-warm99/tasks/spec-recording_owner',
        'bootstrap':'T/interactive_task_owner_c20.py','bootstrap_sha256':'af9a4e8e512c14e8745a0908ff3a0618497757459a96a55d7bb5b40509285dfd',
        'stop_path':None,'new_task_registration_or_run_admitted':False},
      'no_new_Game_or_publisher':True,'old_recording_UUID_not_reused':True,'first_pixels_still_required':True,
      'materialized_runtime_outputs':False,'media_cap_reset':False,'observer_media_body_read_or_hash_calls':0}
    encoded=json.dumps(plan,ensure_ascii=False,separators=(',',':')).encode()
    gross=PRODUCER.stat().st_size+Path(__file__).stat().st_size+len(encoded)
    if gross>32768: raise ValueError('complete source32KiB quote exceeded: '+str(gross))
    with PLAN.open('xb') as f: f.write(encoded)
    print(json.dumps({'plan':recipe.pin(PLAN),'source_gross':gross,'runtime_outputs':outputs}),flush=True)

if __name__=='__main__': main()
