"""Exercise a selected host's actual static profile phase, then stop before game.

The diagnostic profile is derived from explicitly inventoried prepared inputs.
It is never selected for launch and does not modify the actual run's userdir.
"""
from __future__ import annotations

import argparse
import builtins
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def pin(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return pin(path)


def dryrun(runtime_path: Path, argv_path: Path, output: Path) -> dict:
    runtime=json.loads(runtime_path.read_bytes())
    manifest_path=Path(runtime['manifest']['path'])
    if any(pin(manifest_path)[key]!=runtime['manifest'][key] for key in ('bytes','sha256')):
        raise ValueError('Selected runtime manifest pin differs')
    manifest=json.loads(manifest_path.read_bytes())
    host=Path(runtime['paths']['host'])
    if any(pin(host)[key]!=manifest['host'][key] for key in ('bytes','sha256')):
        raise ValueError('Selected runtime host pin differs')
    frozen=json.loads(argv_path.read_bytes())
    original_state=Path(frozen['state_dir']).resolve()
    startup=json.loads((original_state/'preparation.json').read_bytes())
    preparation_ref=startup['preparation']
    preparation_path=Path(preparation_ref['path'])
    if any(pin(preparation_path)[key]!=preparation_ref[key] for key in ('bytes','sha256')):
        raise ValueError('Actual preparation reference changed')
    preparation=json.loads(preparation_path.read_bytes())
    output.mkdir(parents=True,exist_ok=False)
    state=output/'diagnostic-state'
    profile=state/'profile';profile.mkdir(parents=True)
    copied=[]
    for relative in startup['profile_files']:
        source=(original_state/'profile'/relative).resolve()
        destination=(profile/relative).resolve()
        if not source.is_relative_to(original_state/'profile') or not destination.is_relative_to(profile):
            raise ValueError('Declared diagnostic profile path escapes its root')
        raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=startup['profile_input_sha256'][relative]:
            raise ValueError('Actual prepared profile input changed: '+relative)
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(raw);copied.append(relative)
        if relative in preparation.get('files',{}):
            preparation['files'][relative]['path']=str(destination)
    preparation.update(state_dir=str(state),profile_dir=str(profile),
        static_diagnostic_derivation={'source_preparation':pin(preparation_path),'launch_authority':False})
    derived=write(output/'derived-preparation.json',preparation)
    startup.update(profile_dir=str(profile),preparation=derived,
        static_diagnostic_derivation={'source_startup':pin(original_state/'preparation.json'),'launch_authority':False})
    write(state/'preparation.json',startup)
    argv=list(frozen['argv'])
    host_position=argv.index('--agent-source-root')-1
    argv=argv[host_position+1:]
    replacements={'--agent-source-root':runtime['paths']['source_root'],
        '--state-dir':str(state),'--output':str(output/'never-run-native-report.json'),
        '--game-dir':runtime['game_dir'],'--bridge-dll':runtime['paths']['dll'],
        '--bridge-injector':runtime['paths']['injector']}
    for flag,value in replacements.items():
        if argv.count(flag)!=1:raise ValueError('Actual frozen host CLI differs: '+flag)
        argv[argv.index(flag)+1]=str(value)
    spec=importlib.util.spec_from_file_location('_selected_host_static_preflight',host)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    boundary={}
    def execute_definitions_only(code,namespace):
        builtins.exec(code,namespace)
        def stop_before_game():
            boundary['actual_wrapper_profile_phase_returned']=True
            return 0
        namespace['main']=stop_before_game
    module.exec=execute_definitions_only
    old_argv=sys.argv
    try:
        sys.argv=[str(host),*argv]
        result=module.main()
    finally:
        sys.argv=old_argv
    if result!=0 or boundary.get('actual_wrapper_profile_phase_returned') is not True:
        raise ValueError('Actual host did not finish its static profile phase')
    receipt_path=state/'normal-exit-binding/RESULT.actual.json'
    static_receipt=json.loads(receipt_path.read_bytes())
    if static_receipt.get('game_started') is not False or static_receipt['verification']['static_sources_verified'] is not True:
        raise ValueError('Actual static profile receipt is incomplete')
    result={'schema':'ck3-selected-host-static-preflight-v1','status':'PASS',
        'runtime':pin(runtime_path),'manifest':pin(manifest_path),'host':pin(host),
        'original_frozen_argv':pin(argv_path),'actual_profile_input_count':len(copied),
        'derived_diagnostic_state':str(state),'actual_static_profile_receipt':pin(receipt_path),
        **boundary,'underlying_host_definitions_executed':True,'underlying_host_main_executed':False,
        'actual_run_profile_modified':False,'game_started':False,'normal_exit_qualified':False,
        'business_pass':False}
    write(output/'RESULT.actual.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',required=True,type=Path)
    parser.add_argument('--frozen-argv',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    try:
        result=dryrun(args.runtime,args.frozen_argv,args.output)
    except Exception as error:
        print(json.dumps({'status':'RED','error':type(error).__name__+': '+str(error),
                          'game_started':False,'business_pass':False},ensure_ascii=False))
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
