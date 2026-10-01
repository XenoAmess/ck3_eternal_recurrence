#!/usr/bin/env python3
"""Compile and exercise actual Rite model reader/serializer without CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True); args=parser.parse_args()
    root=Path(__file__).resolve().parents[3]
    native=root/'ck3_autonomous_player/native_bridge'; output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=True)
    vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],
        capture_output=True,text=True,check=True).stdout.strip()
    vcvars=Path(installed)/'VC/Auxiliary/Build/vcvars64.bat'
    sources=[native/'src'/x for x in ('ck3_12002.cpp','religion_reform12002_rite.cpp','religion_reform12002_rite_test.cpp')]
    pins=sources+[native/'include/xar_bridge/religion_reform12002_rite.hpp',
        native/'include/xar_bridge/ck3_12002_religion_context.hpp']
    runs=[]
    for mode in ('Od','O2'):
        target=output/mode; target.mkdir(exist_ok=True); temp=target/'temp';temp.mkdir(exist_ok=True)
        exe=target/'rite-model-test.exe'
        command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/'+mode,
            '/W4','/WX','/utf-8','/I'+str(native/'include'),*map(str,sources),'/Fe:'+str(exe)])
        batch=target/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+command+'\nexit /b %errorlevel%\n',encoding='utf-8')
        env=dict(os.environ,TEMP=str(temp),TMP=str(temp))
        build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (target/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
        if build.returncode:raise RuntimeError('Build failed: '+str(target/'build.log'))
        run=subprocess.run([str(exe),str(target)],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (target/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Fixture failed: '+str(target/'test.log'))
        wire={p.name:json.loads(p.read_text(encoding='utf-8')) for p in target.glob('*.json')}
        current,zero,absent,failed= [wire[x] for x in ('non-main-current.json','main-zero.json','legal-absent.json','divergence-unavailable.json')]
        if not (current['available'] and current['founder_character_id']==0xF3000007 and
                current['faith_heresy_threshold_raw']==8_000_000 and current['current_is_main'] is False and
                zero['head_character_id']==0 and zero['founder_character_id'] is None and
                zero['divergence_to_main_raw']==0 and zero['current_is_main'] is True and
                absent['available'] and absent['rite_id'] is None and not failed['available'] and
                failed['divergence_to_main_raw'] is None and failed['unavailable_reason']=='divergence_unavailable'):
            raise ValueError('Actual C++ JSON lost model value / zero / absence / failure semantics')
        runs.append({'mode':mode,'returncode':run.returncode,'stdout':run.stdout.strip(),
            'actual_wire_cases':len(wire),'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
            'wire_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in target.glob('*.json')}})
        print(mode,run.stdout.strip())
    receipt={'status':'GREEN','readiness':'static-ready','local_ck3_touched':False,'live_verified':False,
        'actual_provider':True,'actual_serializer':True,'compiler':'MSVC /W4 /WX /Od and /O2',
        'runs':runs,'source_sha256':{str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in pins}}
    (output/'result.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
