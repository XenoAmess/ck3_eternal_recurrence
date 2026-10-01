#!/usr/bin/env python3
"""Compile actual knowledge provider/definition copier/serializer fixtures."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args();root=Path(__file__).resolve().parent.parent
    native=root/'ck3_autonomous_player/native_bridge';output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
    vcvars=Path(installed)/'VC/Auxiliary/Build/vcvars64.bat'
    sources=[native/'src'/name for name in ('ck3_12002.cpp','ck3_12002_religion_context.cpp',
        'religion_doctrine12002_intrinsic.cpp','religion_doctrine12002_choices.cpp','religion_doctrine12002_choices_test.cpp')]
    pins=sources+[native/'include/xar_bridge'/name for name in ('religion_doctrine12002_choices.hpp',
        'religion_doctrine12002_intrinsic.hpp','ck3_12002_religion_context.hpp')]
    runs=[]
    for mode in ('Od','O2'):
        target=output/mode;target.mkdir(exist_ok=True);temp=target/'tmp';temp.mkdir(exist_ok=True)
        exe=target/'doctrine-knowledge-test.exe'
        command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/'+mode,'/W4','/WX','/utf-8',
            '/I'+str(native/'include'),*map(str,sources),'/Fe:'+str(exe)])
        batch=target/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+
            command+'\nexit /b %errorlevel%\n',encoding='utf-8')
        env=dict(os.environ,TEMP=str(temp),TMP=str(temp))
        build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (target/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
        if build.returncode:raise RuntimeError('Compile failed: '+str(target/'build.log'))
        run=subprocess.run([str(exe),str(target)],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (target/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Fixture failed: '+str(target/'test.log'))
        wire={f.name:json.loads(f.read_text(encoding='utf-8')) for f in target.glob('*.json')}
        assert wire['learned-current.json']['learned_rows'][1]['doctrine_key']=='doc"信'
        assert wire['lookup-not-known.json']['definition_found'] and wire['lookup-not-known.json']['native_knows_doctrine'] is False
        assert wire['lookup-absent.json']['available'] and wire['lookup-absent.json']['native_knows_doctrine'] is None
        assert not wire['lookup-registry-unavailable.json']['available']
        assert wire['learned-rite-default.json']['knowledge_source']=='rite_default'
        assert wire['learned-rite-default.json']['learned_rows'][0]['doctrine_key']=='doctrine_c'
        assert wire['learned-empty.json']['available'] and wire['learned-empty.json']['learned_rows']==[]
        assert wire['learned-native-absent-rite.json']['rite_id'] is None
        runs.append({'mode':mode,'stdout':run.stdout.strip(),'actual_wire_cases':len(wire),
            'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
            'wire_sha256':{name:hashlib.sha256((target/name).read_bytes()).hexdigest() for name in wire}})
        print(mode,run.stdout.strip())
    result={'status':'GREEN','readiness':'static-ready','live_verified':False,'local_ck3_touched':False,
        'actual_provider':True,'actual_definition_copier':True,'actual_serializer':True,
        'compiler':'MSVC /W4 /WX /Od and /O2','runs':runs,
        'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return 0
if __name__=='__main__':raise SystemExit(main())
