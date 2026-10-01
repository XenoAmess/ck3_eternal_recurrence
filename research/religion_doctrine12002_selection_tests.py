#!/usr/bin/env python3
"""Run one O2 fixture through actual popup producer and selection observer."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parent.parent;native=root/'ck3_autonomous_player/native_bridge'
    output=a.output_dir.resolve();output.mkdir(parents=True,exist_ok=True);temp=output/'tmp';temp.mkdir(exist_ok=True)
    vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
    vcvars=Path(installed)/'VC/Auxiliary/Build/vcvars64.bat'
    sources=[native/'src'/name for name in ('ck3_12002.cpp','ck3_12002_religion_context.cpp',
        'religion_reform12002_window.cpp','religion_doctrine12002_intrinsic.cpp','religion_doctrine12002_choices.cpp',
        'religion_doctrine12002_tenet_rows.cpp','religion_reform12002_choices.cpp',
        'religion_doctrine12002_selection.cpp','religion_doctrine12002_selection_test.cpp')]
    pins=sources+[native/'include/xar_bridge'/name for name in ('religion_doctrine12002_selection.hpp',
        'religion_reform12002_choices.hpp','religion_reform12002_window.hpp')]
    executable=output/'doctrine-selection-test.exe'
    command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/O2','/W4','/WX','/utf-8',
        '/I'+str(native/'include'),*map(str,sources),'/Fe:'+str(executable)])
    batch=output/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+
        command+'\nexit /b %errorlevel%\n',encoding='utf-8')
    env=dict(os.environ,TEMP=str(temp),TMP=str(temp))
    build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=output,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (output/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
    if build.returncode:raise RuntimeError('Compile failed: '+str(output/'build.log'))
    run=subprocess.run([str(executable),str(output)],cwd=output,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (output/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
    if run.returncode:raise RuntimeError('Fixture failed: '+str(output/'test.log'))
    wires={path.name:json.loads(path.read_text(encoding='utf-8')) for path in output.glob('*-selection.json')}
    assert wires['current-selection.json']['selectable_doctrine_keys']==['known_"信']
    assert wires['current-selection.json']['rows'][2]['native_should_display'] is False
    assert wires['current-selection.json']['rows'][3]['selection_blocker']=='blocked_by_native_can_pick'
    assert wires['prophet-selection.json']['rows'][1]['selectable'] is True
    assert wires['closed-selection.json']['unavailable_reason']=='current_draft_not_visible'
    assert wires['empty-selection.json']['selection_ready'] and wires['empty-selection.json']['rows']==[]
    assert not wires['changed-selection.json']['available'] and wires['changed-selection.json']['rows']==[]
    assert not wires['missing-prophet-selection.json']['selection_ready']
    result={'status':'GREEN','readiness':'static-ready','live_verified':False,'local_ck3_touched':False,
        'actual_popup_producer':True,'actual_selection_observer':True,'actual_serializer':True,
        'compiler':'MSVC /O2 /W4 /WX','checks':15,'actual_wire_cases':len(wires),'stdout':run.stdout.strip(),
        'fixture_executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
        'source_sha256':{str(path.relative_to(root)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest() for path in pins},
        'wire_sha256':{name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in wires}}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
