"""Exercise actual law source, shared action and independent receipt offline."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def run(root: Path, build: Path) -> None:
    build.mkdir(parents=True, exist_ok=True)
    vswhere = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    found = subprocess.run([str(vswhere), '-latest', '-products', '*', '-requires',
                            'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property',
                            'installationPath'], check=True, capture_output=True, text=True)
    vcvars = Path(found.stdout.strip()) / 'VC/Auxiliary/Build/vcvars64.bat'
    capture = build / 'capture-msvc.cmd'
    capture.write_text(f'@call "{vcvars}" >nul\n@set\n', encoding='utf-8')
    captured = subprocess.run([r'C:\Windows\System32\cmd.exe', '/d', '/c', str(capture)],
                              check=True, capture_output=True, text=True, encoding='mbcs')
    env = os.environ.copy()
    for line in captured.stdout.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            env[key.upper()] = value
    compiler = shutil.which('cl.exe', path=env['PATH'])
    bridge = root / 'ck3_autonomous_player/native_bridge'
    sources = ['ck3_12002_realm_law_source_adapter', 'ck3_12002_realm_law_source_adapter_test',
               'ck3_12002_realm_law_active_collection', 'ck3_12002_realm_law_candidate_collection',
               'ck3_12002_realm_law_final_terms', 'ck3_12002_realm_law_enact_command_v1',
               'ck3_12002_realm_law_components',
               'realm_law_governance_snapshot_v1', 'realm_law_governance_source_adapter_v1',
               'realm_law_enact_action_v1', 'realm_law_native_binder_v1']
    # New provider calls no legacy reader; shared key/failure mapper definitions
    # remain in their original compilation units for both executable versions.
    sources += ['realm_law_active_collection_11906']
    results = []
    for name, flag in [('normal', '/Od'), ('optimized', '/O2')]:
        output = build / f'realm-law-source-12002-{name}.exe'
        compile_result = subprocess.run([compiler, '/nologo', '/std:c++20', '/W4', '/WX',
            '/permissive-', '/EHsc', '/UNDEBUG', flag, f'/I{bridge / "include"}',
            *[str(bridge / f'src/{stem}.cpp') for stem in sources], f'/Fe:{output}'],
            cwd=build, env=env, text=True, capture_output=True, encoding='mbcs')
        (build / f'{name}-compile.log').write_text(compile_result.stdout + compile_result.stderr, encoding='utf-8')
        print(compile_result.stdout, end='')
        compile_result.check_returncode()
        result = subprocess.run([str(output)], cwd=build, env=env, text=True,
                                capture_output=True, encoding='mbcs')
        (build / f'{name}-run.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        print(result.stdout, end='')
        result.check_returncode()
        results.append({'mode': name, 'w4_wx': True, 'exit_code': result.returncode})
    (build / 'result.json').write_text(json.dumps({'schema': 'law-source-offline-result-v1',
        'ck3_access': False, 'results': results}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--build-root', type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.build_root.resolve())
