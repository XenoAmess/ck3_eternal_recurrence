"""Compile the actual child-house preview reader with synthetic owning objects."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

NATIVE = Path(__file__).resolve().parent.parent

def run(build: Path) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    temporary = build / 'tmp'
    temporary.mkdir(exist_ok=True)
    os.environ['TEMP'] = str(temporary)
    os.environ['TMP'] = str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    env = _visual_studio_environment()
    compiler = shutil.which('cl.exe', path=env.get('PATH'))
    if not compiler:
        raise RuntimeError('MSVC unavailable')
    source_names = ['ck3_12002_family_obligations_lineage.cpp',
                    'ck3_12002_family_value.cpp',
                    'ck3_12002_family_obligations_lineage_test.cpp']
    suites = []
    for mode, flags in [('Od', ['/Od', '/MDd']), ('O2', ['/O2', '/MD'])]:
        output = build / f'family-lineage-{mode}.exe'
        command = [compiler, '/nologo', '/std:c++20', '/W4', '/WX',
                   '/permissive-', '/EHsc', '/DNOMINMAX',
                   '/DXAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1',
                   *flags, f'/I{NATIVE / "include"}',
                   *[str(NATIVE / 'src' / name) for name in source_names],
                   f'/Fe:{output}']
        compiled = subprocess.run(command, cwd=build, env=env, capture_output=True, text=True)
        (build / f'compile-{mode}.log').write_text(compiled.stdout + compiled.stderr, encoding='utf-8')
        if compiled.returncode:
            raise RuntimeError(f'{mode} compile RED: {compiled.stdout}{compiled.stderr}')
        tested = subprocess.run([str(output)], cwd=build, env=env, capture_output=True, text=True)
        (build / f'run-{mode}.log').write_text(tested.stdout + tested.stderr, encoding='utf-8')
        if tested.returncode:
            raise RuntimeError(f'{mode} fixture RED: {tested.stdout}{tested.stderr}')
        suites.append({'mode': mode, 'status': 'GREEN', 'output': tested.stdout.strip(),
                       'executable_sha256': hashlib.sha256(output.read_bytes()).hexdigest()})
    result = {'status': 'GREEN', 'readiness': 'static-ready', 'live_verified': False,
              'process_access': False, 'suites': suites,
              'sources': {name: hashlib.sha256((NATIVE / 'src' / name).read_bytes()).hexdigest()
                          for name in source_names}}
    (build / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().build_root.resolve()), indent=2))
