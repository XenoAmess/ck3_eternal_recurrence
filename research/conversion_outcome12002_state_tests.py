#!/usr/bin/env python3
"""Build actual outcome state provider and serializer against fixture-owned objects."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True); a = p.parse_args()
    root = Path(__file__).resolve().parent.parent; native = root/'ck3_autonomous_player/native_bridge'
    output = a.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    installed = subprocess.run([str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'],
        capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(installed)/'VC/Auxiliary/Build/vcvars64.bat'
    sources = [native/'src'/n for n in ('ck3_12002.cpp', 'conversion_outcome12002_state.cpp',
                                     'conversion_outcome12002_state_test.cpp')]
    pins = sources + [native/'include/xar_bridge/conversion_outcome12002_state.hpp',
        native/'include/xar_bridge/ck3_12002_religion_conversion_gates.hpp',
        native/'include/xar_bridge/ck3_12002_religion_context.hpp']
    runs = []
    for mode in ('Od', 'O2'):
        target = output/mode; target.mkdir(exist_ok=True)
        temp = target/'tmp'; temp.mkdir(exist_ok=True)
        executable = target/'conversion-outcome-state-test.exe'
        command = subprocess.list2cmdline(['cl.exe', '/nologo', '/std:c++20', '/EHsc', '/'+mode,
            '/W4', '/WX', '/utf-8', '/I'+str(native/'include'), *map(str, sources), '/Fe:'+str(executable)])
        batch = target/'build.cmd'
        batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+
                         command+'\nexit /b %errorlevel%\n', encoding='utf-8')
        environment = dict(os.environ, TEMP=str(temp), TMP=str(temp))
        build = subprocess.run(['cmd.exe', '/d', '/c', str(batch)], cwd=target, env=environment,
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
        (target/'build.log').write_text(build.stdout+build.stderr, encoding='utf-8')
        if build.returncode: raise RuntimeError('Compile failed: '+str(target/'build.log'))
        run = subprocess.run([str(executable), str(target)], cwd=target, capture_output=True,
                             text=True, encoding='utf-8', errors='replace')
        (target/'test.log').write_text(run.stdout+run.stderr, encoding='utf-8')
        if run.returncode: raise RuntimeError('Fixture failed: '+str(target/'test.log'))
        wire = {f.name: json.loads(f.read_text(encoding='utf-8')) for f in target.glob('*.json')}
        before, after = wire['before-actual-state.json'], wire['after-actual-state.json']
        assert before['knowledge_level_raw'] == 25_000 and after['knowledge_level_raw'] == 60_001
        assert before['target_rite_id'] == after['target_rite_id'] and before['capture_epoch'] != after['capture_epoch']
        assert before['spiritual_fulfillment_raw'] == 70_000 and before['baseline_spiritual_fulfillment_raw'] == -10_000
        assert after['spiritual_fulfillment_raw'] == -5_000 and after['baseline_spiritual_fulfillment_raw'] == 8_000
        assert before['faith_conversion_recently_converted']['remaining_updates'] == 63
        assert before['recent_convert']['timed'] is False and before['recent_convert']['expiry_counter_raw'] == -1
        assert after['conversion_memory_recently_created']['present'] is False
        assert after['conversion_memory_recently_created']['expiry_counter_raw'] is None
        assert not before['is_conversion_gain'] and before['flag_expiry_unit'] == 'native_flag_updates'
        zero = wire['zero-empty-flags.json']
        assert zero['available'] and zero['knowledge_level_raw'] == zero['spiritual_fulfillment_raw'] == 0
        missing = wire['flags-unavailable.json']
        assert not missing['available'] and missing['recent_convert']['present'] is None
        assert wire['target-zero.json']['target_rite_id'] == 0
        runs.append({'mode': mode, 'status': 'GREEN', 'stdout': run.stdout.strip(),
            'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
            'wire_sha256': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob('*.json')}})
        print(mode, run.stdout.strip())
    result = {'status': 'GREEN', 'readiness': 'static-ready', 'actual_provider': True,
        'actual_serializer': True, 'native_callbacks': 'fixture', 'local_ck3_touched': False,
        'conversion_submitted': False, 'live_verified': False, 'compiler': 'MSVC /W4 /WX /Od and /O2',
        'runs': runs, 'source_sha256': {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest() for f in pins}}
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
