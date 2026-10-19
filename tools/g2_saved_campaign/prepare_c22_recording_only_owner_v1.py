"""Pure C22 new-segment recipe; reuse the live C16 publisher, never restart it."""
import ast
import hashlib
import importlib.util
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
T=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime')
P=T/'presentation-c16'
MACHINE='xenoamess-full-tower-eb9d2c1186'
BASE=P/'ck3_obs_capture_png_retry_c16.py'
BASE_SHA='20e40e58137ee40ee002e3e6b3cfb670addf12b62c6e2f7f666a4252601759b8'
CAPTURE='ck3_obs_capture_png_retry_pause_c22.py'
STAGE='start_recording_segment_c22.py'

STAGE_SOURCE=r'''"""C22 recording-only custody. Borrows Game/publisher; owns only its new worker."""
import argparse, ctypes, hashlib, importlib, importlib.util, json, os, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
P=Path(__file__).resolve().parent; T=P.parent
M='xenoamess-full-tower-eb9d2c1186'
GAME=(30852,134368995759027619); PUB=(53688,134368999873257432)
CAPTURE='ck3_obs_capture_png_retry_pause_c22.py'
MANIFEST=T/'ROOT-RECORDING-ONLY-SOURCE-PINS-C22.json'
NAMES=('managed_desktop1_placement','xar_autoplayer.bridge.windows_virtual_desktop',
 'win32gui','win32process','psutil','obsws_python.error','websocket','obs_owned_desktop',
 'ck3_mod_acceptance_recorder','ck3_recording_stall_hook','ck3_capture_closed_receipt')
def require(ok,why):
 if not ok: raise ValueError('C22 recording-only owner: '+why)
def read(path):
 b=Path(path).read_bytes(); require(len(b)<=131072,'finite metadata/source'); return json.loads(b)
def pin(path):
 path=Path(path); b=path.read_bytes(); require(len(b)<=131072,'finite source pin')
 return {'path':str(path.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def verified(ref):
 require(pin(ref['path'])==ref,'exact frozen source differs'); return Path(ref['path'])
def setup():
 manifest=read(MANIFEST)
 require(manifest['machine_id']==M and manifest['generation']=='C22_RECORDING_ONLY','source identity')
 for ref in manifest['files']: verified(ref)
 require(manifest['capture']['path']==str((P/CAPTURE).resolve()),'capture must use its real C16 sibling path')
 require(verified(manifest['capture'])==P/CAPTURE,'capture source path')
 require(verified(manifest['stage'])==Path(__file__).resolve(),'actual stage source path')
 sys.path.insert(0,str(T)); api_module=importlib.import_module('root_decision_text_api_c16'); api=api_module.load_api(T)
 hotfix=P/'hotfix_provider.py'; text=hotfix.read_text(encoding='utf-8')
 delimiter='\nspec=importlib.util.spec_from_file_location('
 require(text.count(delimiter)==1,'existing dependency prefix')
 exec(compile(text.split(delimiter,1)[0],str(hotfix),'exec'),{'__file__':str(hotfix),'__name__':'_C22_recording_dependencies'})
 spec=importlib.util.spec_from_file_location('_C22_recording_capture',P/CAPTURE)
 capture=importlib.util.module_from_spec(spec); spec.loader.exec_module(capture)
 require(Path(capture.__file__).resolve()==P/CAPTURE and capture.decision_publisher_api() is api,'same physical capture/API')
 capture._generation_helpers()
 return manifest,api_module,api,capture
def child_import_preflight():
 manifest,api_module,api,capture=setup()
 require(os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','child bytecode disabled')
 profile=read(T/'ROOT-OBS-PROFILE-C22.json'); capture.validate_profile(profile); capture._control(profile)
 origins={name:str(Path(importlib.import_module(name).__file__).resolve()) for name in NAMES}
 require(hashlib.sha256(Path(origins['managed_desktop1_placement']).read_bytes()).hexdigest()==
  '2f40965ea2af7b010a25750fccaecebb0964d1381d975a8bf4403bdbbae3f493','original generation helper')
 print(json.dumps({'status':'ACTUAL_CHILD_ENV_IMPORT_PREFLIGHT_PASS','machine_id':M,
  'utc':datetime.now(timezone.utc).isoformat(),'capture':pin(P/CAPTURE),
  'same_interpreter':str(Path(sys.executable).resolve()),'module_origins':origins,
  'bytecode_disabled':True,'OBS_Game_calls':0}),flush=True)
def wait_worker(generation):
 k=generation.kernel
 k.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
 k.GetExitCodeProcess.restype=ctypes.c_int
 while True:
  state=k.WaitForSingleObject(generation.handle,1000)
  require(state in (0,258),'retained worker wait unknown')
  if state==0: break
 code=ctypes.c_uint32()
 if not k.GetExitCodeProcess(generation.handle,ctypes.byref(code)): raise ctypes.WinError(ctypes.get_last_error())
 return code.value
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('game-launch','placement','obs-profile','job-root','ffprobe','source-manifest'):
  parser.add_argument('--'+name,type=Path,required=True)
 a=parser.parse_args()
 require(a.source_manifest.resolve()==MANIFEST,'exact source manifest')
 manifest,api_module,api,capture=setup()
 require(a.game_launch.resolve()==T/'ROOT-ACTUAL-GAME-LAUNCH-C16.json'
  and a.placement.resolve()==T/'ROOT-GAME-PLACEMENT-C16.json'
  and a.obs_profile.resolve()==T/'ROOT-OBS-PROFILE-C22.json','explicit source/profile paths')
 launch,placement,profile=map(read,(a.game_launch,a.placement,a.obs_profile))
 require((launch['pid'],launch['creation_filetime'])==GAME
  and (placement['pid'],placement['creation_filetime'])==GAME and placement['status']=='GREEN','same Game source tuple')
 require(profile.get('continuous') is True and Path(profile['recording_root']).resolve()==a.job_root.resolve()
  and a.job_root.resolve()==T/'recordings','new continuous profile/root')
 require(profile['profile_name']!=read(T/'ROOT-OBS-PROFILE-C16.json')['profile_name'],'new owned profile UUID')
 old=read(verified(manifest['old_capture_closed']))
 require(old['session_id']=='2b8912a6-757d-46a4-a8ae-b7702a730a90' and old['inputs_unbound'] is True
  and old['engine_close']['actual_exit_code']==0 and old['engine_close']['normal_exit_proven'] is True
  and old['engine_close']['forced_process_calls']==0,'normal old segment closure')
 outputs={key:T/name for key,name in {
  'requested':'ROOT-OBS-RECORDING-REQUESTED-C22.json','current':'ROOT-CURRENT-OBS-RECORDING-REQUESTED-C22.json',
  'started':'ROOT-RECORDING-ONLY-OWNER-STARTED-C22.json','closed':'ROOT-RECORDING-ONLY-OWNER-CLOSED-C22.json',
  'preflight':'ROOT-RECORDING-CHILD-IMPORT-PREFLIGHT-C22.json'}.items()}
 require(not any(p.exists() for p in outputs.values()),'create-only new segment; no launch retry')
 argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--child-import-preflight']
 child=subprocess.run(argv,cwd=str(T),env=dict(os.environ),capture_output=True,timeout=30,
  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=False)
 require(len(child.stdout)<=16384 and len(child.stderr)<=8192,'bounded child import result')
 api.atomic(outputs['preflight'],{'machine_id':M,'utc':datetime.now(timezone.utc).isoformat(),
  'argv':argv,'returncode':child.returncode,'stdout':child.stdout.decode('utf-8'),
  'stderr':child.stderr.decode('utf-8','replace'),'OBS_Game_calls':0},new=True)
 require(child.returncode==0,'actual child import preflight failed; no launch')
 row=json.loads(child.stdout)
 require(row['status']=='ACTUAL_CHILD_ENV_IMPORT_PREFLIGHT_PASS' and row['machine_id']==M
  and row['capture']==manifest['capture'] and row['bytecode_disabled'] is True
  and Path(row['same_interpreter']).resolve()==Path(sys.executable).resolve()
  and set(row['module_origins'])==set(NAMES),'actual child source/environment result')
 reference=api_module.started_reference(T,api)
 require(reference==manifest['publisher_started'],'same original publisher STARTED ref')
 publisher=api.read_text_binding(reference,game={'pid':GAME[0],'creation_filetime':GAME[1],
  'hwnd':placement['hwnd'],'desktop_id':placement['target_desktop_id']})
 actual=api.process_identity(PUB[0]); require(actual['creation_filetime']==PUB[1],'exact live borrowed publisher')
 require(api.process_identity(GAME[0])['creation_filetime']==GAME[1],'exact live Game')
 request=capture.launch_recording(a.obs_profile,a.job_root,GAME[0],placement['hwnd'],None,
  launch_receipt=a.game_launch,ffprobe=a.ffprobe,placement_receipt=a.placement,
  decision_publisher_receipt=Path(reference['path']),continuous=True)
 require(request['session_id']!=old['session_id'],'new recording UUID')
 print(json.dumps({'state':'C22_new_recording_requested','request':request,'publisher_borrowed':reference,
  'pixel_admitted':False,'new_Game_publisher_calls':0}),flush=True)
 ProcessGeneration=capture._generation_helpers()[0]
 failure=None
 with ProcessGeneration(request['worker_pid'],Path(request['worker_executable']),
     creation_filetime=request['worker_creation_filetime']) as worker:
  try:
   request.update(generation='C22_RECORDING_ONLY',capture_admission_stage='saved_map',map_ready_claimed=False)
   api.atomic(outputs['requested'],request,new=True); api.atomic(outputs['current'],request,new=True)
   api.atomic(outputs['started'],{'machine_id':M,'utc':datetime.now(timezone.utc).isoformat(),
    'status':'NEW_RECORDING_WORKER_HANDLE_RETAINED','request':request,
    'publisher_started':reference,'publisher_borrowed':True,'Game_restarted':False,
    'source_manifest':pin(MANIFEST),'first_pixels_admitted':False},new=True)
  except BaseException as error:
   failure=repr(error)[:2048]
   print(json.dumps({'metadata_publication_error':failure,'worker_retained_until_original_close':True}),flush=True)
  finally:
   # The Task Job continues to own the worker. Never exit early and force it
   # merely because publication failed; Root may inspect stdout and STOP it.
   code=wait_worker(worker)
  job=Path(request['receipt_root']); cap_path=job/'capture_closed.json'; done_path=job/'completed.json'
  closed=read(cap_path) if cap_path.is_file() else None
  normal=code==0 and failure is None and closed is not None and done_path.is_file()
  if normal:
   normal=(closed.get('session_id')==request['session_id'] and closed.get('inputs_unbound') is True
    and closed.get('engine_close',{}).get('actual_exit_code')==0
    and closed.get('engine_close',{}).get('normal_exit_proven') is True
    and closed.get('engine_close',{}).get('forced_process_calls')==0)
  api.atomic(outputs['closed'],{'machine_id':M,'utc':datetime.now(timezone.utc).isoformat(),
   'normal':normal,'worker_pid':request['worker_pid'],'worker_creation_filetime':request['worker_creation_filetime'],
   'worker_exit_code':code,'kernel_exit_observed':True,'recording_job_root':str(job),
   'capture_closed':pin(cap_path) if cap_path.is_file() else None,
   'completed':pin(done_path) if done_path.is_file() else None,'metadata_error':failure,
   'publisher_stop_calls':0,'Game_stop_calls':0,'observer_media_body_read_or_hash_calls':0},new=True)
 return 0 if normal else 1
if __name__=='__main__':
 if sys.argv[1:]==['--child-import-preflight']: child_import_preflight()
 else: raise SystemExit(main())
'''

def require(ok, why):
    if not ok: raise ValueError('C22 recording recipe: '+why)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def pin(path):
    raw=path.read_bytes()
    require(len(raw)<=131072,'finite source/metadata pin')
    return {'path':str(path.resolve()),'bytes':len(raw),'sha256':sha(raw)}

def compose():
    original=BASE.read_bytes()
    require(len(original)==71575 and sha(original)==BASE_SHA,'exact original C16 PNG-retry source')
    producer=REPO/'tools/g2_saved_campaign/prepare_obs_pause_aware_capture_v1.py'
    require(pin(producer)=={'path':str(producer.resolve()),'bytes':6231,
      'sha256':'1eb24b011e03c70bcf50be94617eb46193a3a162c4e0084861f24bf4a35712a0'},'exact committed canonical pause recipe')
    spec=importlib.util.spec_from_file_location('_canonical_pause_recipe',producer)
    pause=importlib.util.module_from_spec(spec); spec.loader.exec_module(pause)
    helper=pause.HELPER.read_bytes()
    require(len(helper)==1566 and sha(helper)==pause.HELPER_SHA,'exact pure pause-growth helper')
    node=next(n for n in ast.parse(helper).body if isinstance(n,ast.FunctionDef) and n.name=='advance_growth_deadline_v1')
    inline=ast.get_source_segment(helper.decode(),node)
    patches=(('class FileGrowthWatch:',inline+'\n\n\nclass FileGrowthWatch:'),*pause.PATCHES)
    canonical=(REPO/'tools/ck3_obs_capture.py').read_bytes()
    require(len(canonical)==71770 and sha(canonical)==pause.CANDIDATE_SHA,'exact adopted canonical pause-aware source')
    canonical_inverse=canonical.decode()
    for old,new in reversed(patches):
        require(canonical_inverse.count(new)==1,'canonical inverse pause seam')
        canonical_inverse=canonical_inverse.replace(new,old,1)
    require(len(canonical_inverse.encode())==69656 and sha(canonical_inverse.encode())==pause.BASE_SHA,
      'same committed pause hunks must independently recover the reviewed f0e6 baseline')
    candidate=original.decode()
    for old,new in patches:
        require(candidate.count(old)==1,'one exact pause seam in PNG retry source')
        candidate=candidate.replace(old,new,1)
    inverse=candidate
    for old,new in reversed(patches):
        require(inverse.count(new)==1,'one inverse pause seam')
        inverse=inverse.replace(new,old,1)
    require(inverse.encode()==original,'PNG/source bytes changed outside pause hunks')
    capture=candidate.encode(); stage=STAGE_SOURCE.encode()
    require(len(capture)==73689 and len(stage)<=12288,'single-copy source quote')
    for name,raw in ((CAPTURE,capture),(STAGE,stage)): compile(raw,str(P/name),'exec')
    files={P/CAPTURE:capture,P/STAGE:stage}
    outputs={str(path):{'path':str(path.resolve()),'bytes':len(raw),'sha256':sha(raw)} for path,raw in files.items()}
    supports=[T/'root_decision_text_api_c16.py',P/'hotfix_provider.py',P/'ck3_mod_acceptance_recorder.py',
      P/'obs_owned_desktop.py',P/'g2_saved_campaign/decision_text_publisher.py',
      P/'g2_saved_campaign/decision_text_view.py',P/'g2_saved_campaign/decision_text_admission.py',
      P/'g2_saved_campaign/automatic_continuity.py']
    import json
    binding=json.loads((T/'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C16.json').read_bytes())
    manifest={'schema':'xar.C22-recording-only-source/v1','machine_id':MACHINE,
      'generation':'C22_RECORDING_ONLY','capture':outputs[str(P/CAPTURE)],'stage':outputs[str(P/STAGE)],
      'files':[*outputs.values(),*[pin(path) for path in supports]],
      'publisher_started':binding['publisher_started'],
      'old_capture_closed':pin(T/'recordings/2b8912a6-757d-46a4-a8ae-b7702a730a90/capture_closed.json'),
      'original_capture':pin(BASE),'pause_recipe':pin(producer),'pause_helper':pin(pause.HELPER),
      'new_Game_publisher_calls':0,'runtime_admitted':False}
    return files,manifest
