"""Root launcher: explicit SDK/segment, hidden watchdog, real dependency imports; default dry-run."""
from __future__ import annotations
import argparse,ast,hashlib,json,os,subprocess,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
from recording_recovery_adapter import atomic,shared_json

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def environment(c):
    profile=shared_json(c.session/'ROOT-OBS-PROFILE.json')
    control=Path(profile['control_dependencies']).resolve(strict=True)
    site=c.dependency_root
    roots=[c.sdk_source,*c.helper_root,control,site,site/'win32',site/'win32/lib',
           site/'Pythonwin',site/'pywin32_system32']
    roots=[str(p.resolve()) for p in roots if p.is_dir()]
    previous=os.environ.get('PYTHONPATH')
    if previous:roots.extend(previous.split(os.pathsep))
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join(dict.fromkeys(roots))
    env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONUTF8']='1'
    return env,roots,control

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['session','initial-recording-request','overlay-source','provider-source',
                 'feeder-template','main-python','base-python','dependency-root','sdk-source']:
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--sdk-prefix',required=True)
    p.add_argument('--helper-root',type=Path,action='append',required=True)
    p.add_argument('--adapter',type=Path,default=Path(__file__).with_name('recording_recovery_adapter.py'))
    p.add_argument('--adapter-sha256',required=True)
    p.add_argument('--launch-root',type=Path)
    p.add_argument('--attach-only',action='store_true')
    p.add_argument('--feeder-stop-marker',type=Path)
    p.add_argument('--start',action='store_true')
    c=p.parse_args()
    for key,value in vars(c).items():
        if isinstance(value,Path) and key not in {'launch_root','feeder_stop_marker'}:setattr(c,key,value.resolve(strict=True))
    if not c.sdk_prefix.startswith('p') or not c.sdk_prefix[1:].isdigit():
        raise ValueError('exact configured pNN SDK prefix required')
    if digest(c.adapter)!=c.adapter_sha256:raise ValueError('reviewed adapter SHA differs')
    env,roots,control=environment(c)
    pins={str(x):digest(x) for x in [c.adapter,c.overlay_source,c.provider_source,c.feeder_template,
                                    c.initial_recording_request,c.session/'ROOT-OBS-PROFILE.json',
                                    c.session/('ROOT-ACTUAL-SDK-PROCESSES-PINNED-'+c.sdk_prefix.upper()+'.json')]}
    # Actual imports, no recording objects or window/process inspection.
    probe=Path(__file__).with_name('probe_actual_dependencies.py')
    dependencies=[]
    for python in [c.main_python,c.base_python]:
        command=[str(python),'-B','-X','utf8',str(probe),'--overlay',str(c.overlay_source),
                 '--provider',str(c.provider_source),'--sdk-source',str(c.sdk_source)]
        result=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,text=True,
                              encoding='utf-8',env=env,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode!=0:raise RuntimeError('actual dependency probe failed: '+result.stderr[-4096:])
        dependencies.append(json.loads(result.stdout))
    argv=[str(c.main_python),'-B','-X','utf8',str(c.adapter),'--session',str(c.session),
          '--sdk-prefix',c.sdk_prefix,'--initial-recording-request',str(c.initial_recording_request),
          '--overlay-source',str(c.overlay_source),'--provider-source',str(c.provider_source),
          '--feeder-template',str(c.feeder_template),'--python',str(c.base_python)]
    if c.attach_only:argv.append('--attach-only')
    if c.feeder_stop_marker:argv.extend(['--feeder-stop-marker',str(c.feeder_stop_marker.resolve())])
    root=c.launch_root or Path(__file__).resolve().parent/'launches'/(c.sdk_prefix+'-'+uuid.uuid4().hex)
    root.mkdir(parents=True,exist_ok=False)
    plan={'status':'READY','at_utc':datetime.now(timezone.utc).isoformat(),'argv':argv,
          'creationflags':'CREATE_NO_WINDOW','PYTHONPATH':roots,'OBS_control_dependencies':str(control),
          'pins':pins,'dependencies':dependencies,'attach_only':c.attach_only,
          'stdout':str(root/'watchdog.stdout.log'),'stderr':str(root/'watchdog.stderr.log'),
          'sdk_prefix':c.sdk_prefix,'recording_request_is_explicit_not_ROOT_CURRENT':True}
    atomic(root/'LAUNCH-PLAN.json',plan,new=True)
    if c.start:
        atomic(root/'LAUNCH-INTENT.json',{'argv':argv,'retry_allowed':False},new=True)
        with (root/'watchdog.stdout.log').open('xb') as stdout,(root/'watchdog.stderr.log').open('xb') as stderr:
            child=subprocess.Popen(argv,cwd=str(c.session),stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                                   env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        atomic(root/'LAUNCH-REQUEST.json',{'pid_returned_by_Popen':child.pid,
               'note':'tools venv redirector PID; overlay uses explicit base interpreter',
               'runtime_qualified':False,'same_game_recording_watchdog_requested':True},new=True)
    print(json.dumps({'status':'requested' if c.start else 'dry_run_ready','root':str(root),'argv':argv}))
if __name__=='__main__':main()
