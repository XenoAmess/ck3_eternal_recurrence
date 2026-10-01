#!/usr/bin/env python3
"""Build actual Faith final numeric getter wrapper once with MSVC O2."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    native = root / 'ck3_autonomous_player/native_bridge'
    output = a.output_dir.resolve()
    target = output / 'O2'
    target.mkdir(parents=True, exist_ok=True)
    temp = target / 'tmp'
    temp.mkdir(exist_ok=True)
    vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    installed = subprocess.run([str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed) / 'VC/Auxiliary/Build/vcvars64.bat'
    sources = [native / 'src' / n for n in ('ck3_12002.cpp', 'religion_doctrine12002_numeric.cpp',
        'religion_doctrine12002_numeric_final.cpp', 'religion_doctrine12002_numeric_final_test.cpp')]
    pins = sources + [native / 'src/religion_doctrine12002_numeric_test.cpp',
        native / 'include/xar_bridge/religion_doctrine12002_numeric.hpp',
        native / 'include/xar_bridge/religion_doctrine12002_numeric_final.hpp',
        native / 'include/xar_bridge/ck3_12002_religion_context.hpp']
    exe = target / 'numeric-final-test.exe'
    command = subprocess.list2cmdline(['cl.exe', '/nologo', '/std:c++20', '/EHsc', '/O2', '/W4', '/WX',
        '/utf-8', '/I'+str(native / 'include'), *map(str, sources), '/Fe:'+str(exe)])
    batch = target / 'build.cmd'
    batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+
                     command+'\nexit /b %errorlevel%\n', encoding='utf-8')
    build = subprocess.run(['cmd.exe', '/d', '/c', str(batch)], cwd=target,
        env=dict(os.environ, TEMP=str(temp), TMP=str(temp)), capture_output=True, text=True,
        encoding='utf-8', errors='replace')
    (target / 'build.log').write_text(build.stdout+build.stderr, encoding='utf-8')
    if build.returncode:
        raise RuntimeError('Compile failed: '+str(target / 'build.log'))
    run = subprocess.run([str(exe), str(target)], cwd=target, capture_output=True, text=True,
                         encoding='utf-8', errors='replace')
    (target / 'test.log').write_text(run.stdout+run.stderr, encoding='utf-8')
    if run.returncode:
        raise RuntimeError('Fixture failed: '+str(target / 'test.log'))
    wires = {f.name:json.loads(f.read_text(encoding='utf-8')) for f in target.glob('*.json')}
    baseline = wires['final-threshold-versus-adjustment.json']
    if not (baseline['available'] and baseline['current_rite_id'] == 0 and
            baseline['main_rite_id'] == 0x82000002 and baseline['faith_id'] == 0x83000003 and
            baseline['main_rite_adjustment_raw'] == 500000 and baseline['native_define_raw'] == 2500000 and
            baseline['final_heresy_threshold_raw'] == 3000000 and baseline['final_heresy_threshold'] == 30 and
            baseline['source'] == 'faith_main_rite' and wires['known-zero-final.json']['final_heresy_threshold'] == 0 and
            wires['known-zero-final.json']['value_state'] == 'value' and
            wires['legal-absent-faith.json']['available'] and
            wires['legal-absent-faith.json']['value_state'] == 'legal_absent_faith' and
            wires['legal-absent-main-rite.json']['value_state'] == 'legal_absent_main_rite' and
            not wires['native-threshold-unavailable.json']['available'] and not wires['state-changed.json']['available']):
        raise ValueError('Actual final native output lost final/adjustment/zero/absence/failure distinction')
    result = {'status':'GREEN', 'readiness':'static-ready', 'local_ck3_touched':False, 'live_verified':False,
        'actual_provider':True, 'actual_native_callback':True, 'actual_serializer':True,
        'old_numeric_main_executed':False, 'compiler':'MSVC /O2 /W4 /WX',
        'runs':[{'mode':'O2', 'returncode':run.returncode, 'stdout':run.stdout.strip(),
            'actual_wire_cases':len(wires), 'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
            'wire_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob('*.json')}}],
        'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output / 'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(run.stdout.strip())
    print('PASS actual JSON packets='+str(len(wires)))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
