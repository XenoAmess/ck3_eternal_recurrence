#!/usr/bin/env python3
"""One MSVC O2 run of the real Character personal-parameter producer/serializer."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parent.parent;native=root/'ck3_autonomous_player/native_bridge'
    output=a.output_dir.resolve();target=output/'O2';target.mkdir(parents=True,exist_ok=True)
    temp=target/'tmp';temp.mkdir(exist_ok=True)
    vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
    sources=[native/'src'/n for n in ('ck3_12002.cpp','religion_doctrine12002_tenet_rows.cpp','religion_doctrine12002_personal_parameters.cpp','religion_doctrine12002_personal_parameters_test.cpp')]
    pins=sources+[native/'include/xar_bridge/religion_doctrine12002_personal_parameters.hpp',native/'include/xar_bridge/religion_doctrine12002_tenet_rows.hpp',native/'include/xar_bridge/religion_doctrine12002_tenet.hpp',native/'include/xar_bridge/ck3_12002_religion_context.hpp']
    exe=target/'personal-parameters-test.exe'
    command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/O2','/W4','/WX','/utf-8','/I'+str(native/'include'),*map(str,sources),'/Fe:'+str(exe)])
    batch=target/'build.cmd';batch.write_text('@echo off\ncall "'+str(Path(installed)/'VC/Auxiliary/Build/vcvars64.bat')+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+command+'\nexit /b %errorlevel%\n',encoding='utf-8')
    build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=target,env=dict(os.environ,TEMP=str(temp),TMP=str(temp)),capture_output=True,text=True,encoding='utf-8',errors='replace')
    (target/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
    if build.returncode:raise RuntimeError('Compile failed: '+str(target/'build.log'))
    run=subprocess.run([str(exe),str(target)],cwd=target,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (target/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
    if run.returncode:raise RuntimeError('Fixture failed: '+str(target/'test.log'))
    wires={f.name:json.loads(f.read_text(encoding='utf-8')) for f in target.glob('*.json')}
    current=wires['current-personal-flags.json'];values={row['key']:row['value'] for row in current['parameters']}
    assert current['available'] and current['source']=='character_personal_tenets' and current['played_character_id']==0x03000004
    assert current['supported_keys_complete'] and current['personal_parameters_complete']
    assert values['tenet_ritual_hospitality_free_guest_recruitment'] is True and values['tenet_adaptive_study_rite_bonus'] is True
    assert values['meditation_mechanics_active'] is False and values['tenet_adoptionism_adoption_personal_active'] is False
    for name,has_extension in [('extension-absent.json',False),('known-empty-personal.json',True)]:
        wire=wires[name];assert wire['available'] and wire['has_character_extension'] is has_extension
        assert wire['personal_tenet_keys']==[] and len(wire['parameters'])==4 and all(row['value'] is False for row in wire['parameters'])
    for name,reason in [('registry-unavailable.json','parameter_registry_unavailable'),('key-unavailable.json','parameter_key_unavailable'),('state-changed.json','state_changed')]:
        wire=wires[name];assert not wire['available'] and wire['unavailable_reason']==reason
        assert wire['parameters']==[] and not wire['supported_keys_complete'] and not wire['personal_parameters_complete']
    result={'status':'GREEN','readiness':'static-ready','local_ck3_touched':False,'live_verified':False,'actual_provider':True,'actual_serializer':True,'compiler':'MSVC /O2 /W4 /WX','runs':[{'mode':'O2','stdout':run.stdout.strip(),'returncode':run.returncode,'actual_wire_cases':len(wires),'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'wire_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob('*.json')}}],'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(run.stdout.strip());print('PASS actual JSON packets='+str(len(wires)));return 0
if __name__=='__main__':raise SystemExit(main())
