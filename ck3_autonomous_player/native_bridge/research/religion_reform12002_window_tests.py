"""Compile actual current Rite draft window reader fixtures; no game operations."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    native = Path(__file__).resolve().parent.parent
    root = native.parent.parent
    output = a.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    installed = subprocess.run([str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / 'VC/Auxiliary/Build/vcvars64.bat'
    sources = [native/'src'/n for n in ('ck3_12002.cpp', 'religion_reform12002_window.cpp', 'religion_reform12002_window_test.cpp')]
    pins = sources+[native/'include/xar_bridge/religion_reform12002_window.hpp']
    runs=[]
    for mode in ('Od','O2'):
        target=output/mode; target.mkdir(exist_ok=True)
        temp=target/'tmp'; temp.mkdir(exist_ok=True)
        executable=target/'religion-reform-window-test.exe'
        command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/'+mode,'/W4','/WX',
            '/utf-8','/I'+str(native/'include'),*map(str,sources),'/Fe:'+str(executable)])
        batch=target/'build.cmd'
        batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+command+'\nexit /b %errorlevel%\n',encoding='utf-8')
        build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=target,
            env=dict(os.environ,TEMP=str(temp),TMP=str(temp)),capture_output=True,text=True,encoding='utf-8',errors='replace')
        (target/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
        if build.returncode:raise RuntimeError('Compile failed: '+str(target/'build.log'))
        run=subprocess.run([str(executable),str(target)],cwd=target,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (target/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Fixture failed: '+str(target/'test.log'))
        wires={f.name:json.loads(f.read_text(encoding='utf-8')) for f in target.glob('*.json')}
        opened=wires['visible-current-draft.json']; hidden=wires['hidden-window.json']; absent=wires['absent-window.json']
        if not(opened['source_rite_id']==0x83000003 and opened['draft_observed'] and
            hidden['available'] and hidden['source_rite_id'] is None and not hidden['draft_observed'] and
            absent['available'] and not absent['present'] and 'window' not in opened):
            raise ValueError('Actual C++ wire scope/absence/full-ref mismatch')
        runs.append({'mode':mode,'returncode':run.returncode,'stdout':run.stdout.strip(),
            'actual_wire_cases':len(wires),'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest()})
        print(mode,run.stdout.strip())
    receipt={'status':'GREEN','readiness':'static-ready library','live_verified':False,'local_ck3_touched':False,
        'actual_reader':True,'actual_serializer':True,'runs':runs,
        'source_sha256':{str(f.relative_to(root)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output/'result.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return 0
if __name__=='__main__':raise SystemExit(main())
