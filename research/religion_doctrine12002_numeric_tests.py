#!/usr/bin/env python3
"""Build actual numeric special cache reader/serializer fixture once with MSVC O2."""
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
                                          'religion_doctrine12002_numeric_test.cpp')]
    pins = sources + [native / 'include/xar_bridge/religion_doctrine12002_numeric.hpp',
                      native / 'include/xar_bridge/ck3_12002_religion_context.hpp']
    exe = target / 'numeric-special-test.exe'
    command = subprocess.list2cmdline(['cl.exe', '/nologo', '/std:c++20', '/EHsc', '/O2',
        '/W4', '/WX', '/utf-8', '/I'+str(native / 'include'), *map(str, sources), '/Fe:'+str(exe)])
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
    current = wires['current-versus-main.json']
    current_rows = {p['key']:p for p in current['current_rite']['parameters']}
    main_rows = {p['key']:p for p in current['faith_main_rite']['parameters']}
    zero = wires['known-zero-current.json']['current_rite']['parameters']
    unset = wires['minimum-unset.json']['current_rite']['parameters'][0]
    if not (current['available'] and current['current_rite']['rite_id'] == 0 and
            current['faith_main_rite']['rite_id'] == 0x82000002 and current['faith_id'] == 0x83000003 and
            current['faith_numeric_consumer_source'] == 'faith_main_rite' and
            current_rows['fervor_per_holy_site']['value'] == 0.05 and
            current_rows['bonus_fervor_gain']['value'] == 0.5 and
            current_rows['bonus_heresy_protection']['value'] == 1 and
            current_rows['heresy_threshold']['value'] == -5 and main_rows['heresy_threshold']['value'] == 5 and
            all(p['value'] == 0 and p['state'] == 'value' for p in zero) and
            unset['raw'] == -1 and unset['scale'] == 1 and unset['value'] is None and unset['state'] == 'unset' and
            wires['legal-absent.json']['available'] and wires['legal-absent.json']['current_rite'] is None and
            not wires['faith-unavailable.json']['available'] and not wires['state-changed.json']['available']):
        raise ValueError('Actual output lost number/unit/zero/unset/absence/source semantics')
    result = {'status':'GREEN', 'readiness':'static-ready', 'local_ck3_touched':False, 'live_verified':False,
        'actual_provider':True, 'actual_serializer':True, 'compiler':'MSVC /O2 /W4 /WX',
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
