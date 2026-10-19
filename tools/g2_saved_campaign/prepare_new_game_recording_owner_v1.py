"""Finite source-only amendment: new publisher owner and real PNG-retry worker."""
import argparse, ast, hashlib, importlib.util, json
from pathlib import Path

BASE_SHA = '6ad73cd15b3c1e5264c3af7c4295640d37640e69c02d939c802c690e724cca9b'
CAPTURE_SHA = '20e40e58137ee40ee002e3e6b3cfb670addf12b62c6e2f7f666a4252601759b8'
HELPER_SHA = 'f0e66034173353c37ba3626e423a2e8139f815e3f8dfa938c4219bc41a16b4e2'
ROOTS_AND_CAPTURE = '''    # Execute only the reviewed existing dependency prefix. Its old capture
    # loader is deliberately excluded; both parent and worker receive ROOTS.
    from importlib import util as capture_util
    hotfix_path=P/'hotfix_provider.py'
    hotfix=hotfix_path.read_text(encoding='utf-8')
    delimiter="\\nspec=importlib.util.spec_from_file_location("
    require(hotfix.count(delimiter)==1,'reviewed dependency prefix differs')
    exec(compile(hotfix.split(delimiter,1)[0],str(hotfix_path),'exec'),
        {'__file__':str(hotfix_path),'__name__':'_reviewed_dependency_prefix'})
    capture_path=P/'__CAPTURE_NAME__'
    raw=capture_path.read_bytes()
    require(len(raw)==71575 and hashlib.sha256(raw).hexdigest()=='__CAPTURE_SHA__',
        'exact patched capture source differs')
    capture_spec=capture_util.spec_from_file_location('_new_Game_patched_capture',capture_path)
    capture=capture_util.module_from_spec(capture_spec)
    capture_spec.loader.exec_module(capture)
    require(Path(capture.__file__).resolve()==capture_path.resolve(),
        'worker must use its real patched source path')
    require(capture.decision_publisher_api() is api,'capture uses a different publisher source')
    capture._generation_helpers()  # fail before publisher/OBS if worker dependencies are absent
'''
CHILD_TAIL = '''    import os
    from datetime import datetime, timezone
    require(os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','child bytecode must be disabled')
    profile=read(N/SPEC['profile'])
    capture.validate_profile(profile);capture._control(profile)
    names=('managed_desktop1_placement','xar_autoplayer.bridge.windows_virtual_desktop',
        'win32gui','win32process','psutil','obsws_python.error','websocket','obs_owned_desktop',
        'ck3_mod_acceptance_recorder','ck3_recording_stall_hook','ck3_capture_closed_receipt')
    origins={name:str(Path(importlib.import_module(name).__file__).resolve()) for name in names}
    helper=Path(origins['managed_desktop1_placement'])
    require(hashlib.sha256(helper.read_bytes()).hexdigest()==
        '2f40965ea2af7b010a25750fccaecebb0964d1381d975a8bf4403bdbbae3f493',
        'actual frozen child process helper differs')
    print(json.dumps({'status':'ACTUAL_CHILD_ENV_IMPORT_PREFLIGHT_PASS',
        'machine_id':SPEC['machine_id'],'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'capture_path':str(capture_path.resolve()),'capture_sha256':hashlib.sha256(raw).hexdigest(),
        'same_interpreter':str(Path(sys.executable).resolve()),'module_origins':origins,
        'bytecode_disabled':True,'OBS_or_Game_calls':0,'source_files_copied':0}),flush=True)
'''
PARENT_CHILD = '''    import os,subprocess
    from datetime import datetime, timezone
    child_argv=[sys.executable,str(Path(__file__).resolve()),'--child-import-preflight']
    child=subprocess.run(child_argv,cwd=str(N),env=dict(os.environ),capture_output=True,
        timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=False)
    require(len(child.stdout)<=16384 and len(child.stderr)<=8192,'bounded child preflight output required')
    preflight=N/('ROOT-DISPLAY-CHILD-IMPORT-PREFLIGHT-'+SPEC['generation']+'.json')
    api.atomic(preflight,{'machine_id':SPEC['machine_id'],'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'argv':child_argv,'returncode':child.returncode,'stdout':child.stdout.decode('utf-8'),
        'stderr':child.stderr.decode('utf-8','replace'),'OBS_or_Game_calls':0},new=True)
    require(child.returncode==0,'actual child-env import preflight failed; original receipt retained')
    child_row=json.loads(child.stdout)
    require(child_row.get('status')=='ACTUAL_CHILD_ENV_IMPORT_PREFLIGHT_PASS'
        and child_row.get('machine_id')==SPEC['machine_id']
        and Path(child_row['capture_path']).resolve()==capture_path.resolve()
        and child_row.get('capture_sha256')=='__CAPTURE_SHA__'
        and Path(child_row['same_interpreter']).resolve()==Path(sys.executable).resolve()
        and child_row.get('bytecode_disabled') is True,'exact child-env import readback differs')
'''


def pin(raw, path):
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def plan(source_runtime, target_runtime, output, *, generation, machine_id):
    here=Path(__file__).resolve().parent
    baseline=here/'prepare_new_game_text_generation_v1.py';raw=baseline.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BASE_SHA:raise ValueError('exact base producer required')
    base=module(baseline,'_reviewed_new_Game_base')
    # Keep every original source/input/namespace guard. Stop at its exact first
    # emission statement, so this planning phase cannot write target or review.
    text=raw.decode('utf-8');tree=ast.parse(text)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='emit')
    function=ast.get_source_segment(text,node)
    anchor='    output.mkdir(parents=True)\n'
    if function.count(anchor)!=1:raise ValueError('original emission boundary changed')
    prefix=function.split(anchor,1)[0]
    env=dict(base.__dict__)
    exec(compile(prefix+'    return values, inputs, spec\n',str(baseline)+'[PLAN_ONLY]','exec'),env)
    values,inputs,spec=env['emit'](source_runtime,target_runtime,output,generation=generation,machine_id=machine_id)
    target=Path(target_runtime).resolve();lower=generation.lower();presentation='presentation-'+lower
    manifest=presentation+'/SOURCE-PINS-'+generation+'.json'
    values.pop(manifest)
    projector=module(here/'prepare_capture_latest_retry_v1.py','_reviewed_capture_projector')
    helper=here.parent/'ck3_obs_capture.py';helper_raw=helper.read_bytes()
    if hashlib.sha256(helper_raw).hexdigest()!=HELPER_SHA:raise ValueError('exact qualified mutable-replace helper required')
    capture=projector.project_capture_latest_retry_v1(values[presentation+'/ck3_obs_capture.py'],helper_raw)
    if len(capture)!=71575 or hashlib.sha256(capture).hexdigest()!=CAPTURE_SHA:raise ValueError('qualified capture projection differs')
    capture_name='ck3_obs_capture_png_retry_'+lower+'.py'
    values[presentation+'/'+capture_name]=capture
    owner_path=presentation+'/start_new_game_display.py';owner=values[owner_path].decode()
    old="    import hotfix_provider as provider\n    require(provider.capture.decision_publisher_api() is api,'capture uses a different publisher source')\n"
    if owner.count(old)!=1 or owner.count('provider.capture.launch_recording(')!=1:raise ValueError('original owner seams differ')
    block=ROOTS_AND_CAPTURE.replace('__CAPTURE_NAME__',capture_name).replace('__CAPTURE_SHA__',CAPTURE_SHA)
    owner=owner.replace(old,block+PARENT_CHILD.replace('__CAPTURE_SHA__',CAPTURE_SHA),1).replace('provider.capture.launch_recording(','capture.launch_recording(',1)
    child_function="def child_import_preflight():\n    import hashlib\n    sys.path.insert(0,str(N))\n    api=importlib.import_module(SPEC['api_module']).load_api(N)\n"+block+CHILD_TAIL
    main_anchor="if __name__=='__main__':main()"
    if owner.count(main_anchor)!=1:raise ValueError('original owner entry differs')
    owner=owner.replace(main_anchor,child_function+"\nif __name__=='__main__':\n    if sys.argv[1:]==['--child-import-preflight']:child_import_preflight()\n    else:main()",1)
    values[owner_path]=owner.encode()
    if any((target/name).exists() for name in values):raise ValueError('new target namespace required')
    files=[pin(data,target/name)|{'relative_path':name} for name,data in values.items()]
    values[manifest]=(json.dumps({'machine_id':machine_id,'files':files},indent=2)+'\n').encode()
    for name,data in values.items():
        if name.endswith('.py'):compile(data,name,'exec')
    review={'schema':'xar.new-Game-patched-recording-owner-review/v1',
        'status':'SOURCE_ONLY_SOLE_RUNTIME_APPLY_REQUIRED','machine_id':machine_id,
        'inputs':inputs+[pin(raw,baseline),pin(helper_raw,helper)],'files':files,
        'manifest':pin(values[manifest],target/manifest),'spec':spec,
        'actual_capture':pin(capture,target/presentation/capture_name),
        'child_preflight_receipt':str(target/('ROOT-DISPLAY-CHILD-IMPORT-PREFLIGHT-'+generation+'.json')),
        'review_source_bytes':sum(map(len,values.values())), 'installed_source_bytes':sum(map(len,values.values())),
        'Game_Desktop_Process_calls':0,'runtime_writes':0,
        'required_owner_flow':['exact source pins and actual new Game/placement/profile','reviewed hotfix ROOTS and child PYTHONPATH prefix only',
         'actual same-parent patched capture import, same API and generation-helper preflight',
         'same-interpreter/env child late-import preflight, actual receipt before publisher config/start','new config -> PublisherOwner.start -> new STARTED/binding',
         'new OBS UUID via patched capture -> saved_map pixels separately','original owner retains child handle; STOP after OBS0/unbound then retained publisher0'],
        'no_old_capture_launch':True,'no_dependency_copy':True,'pixel_admitted':False}
    review_raw=(json.dumps(review,ensure_ascii=False,indent=2)+'\n').encode()
    return values,review_raw,review


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source-runtime','target-runtime','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--generation',required=True);p.add_argument('--machine-id',required=True)
    p.add_argument('--emit',action='store_true');a=p.parse_args()
    values,raw,review=plan(a.source_runtime,a.target_runtime,a.output,generation=a.generation,machine_id=a.machine_id)
    if a.emit:
        a.output.mkdir(parents=True,exist_ok=False)
        for name,data in values.items():
            path=a.output/name;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(data)
        with (a.output/'REVIEW.json').open('xb') as stream:stream.write(raw)
    print(json.dumps({'output':str(a.output),'emitted':a.emit,'leaf_count':len(values),
        'source_bytes':sum(map(len,values.values())),'review':pin(raw,a.output/'REVIEW.json'),
        'capture':review['actual_capture'],'owner':next(r for r in review['files'] if r['relative_path'].endswith('/start_new_game_display.py'))}))


if __name__=='__main__':main()
