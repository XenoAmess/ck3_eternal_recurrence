"""Compile both planner ABI fixtures using caller-owned memory only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / 'tools'))
    import run_native_msvc
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = run_native_msvc.child_environment(output)
    vs = run_native_msvc.visual_studio_installation(None, env)
    env, native_tools = run_native_msvc.initialize_msvc(vs, output, env)
    native = root / 'ck3_autonomous_player/native_bridge'
    core = native / 'src/activity_planner_diag_v1.cpp'
    rows = []
    for optimization in ('Od', 'O2'):
        for version, name in (
            ('1.19.0.6', 'activity_planner_diag_v1_test'),
            ('1.20.0.2', 'ck3_12002_feast_planner_diag_test'),
        ):
            cell = output / optimization / version
            cell.mkdir(parents=True, exist_ok=True)
            source = native / ('src/' + name + '.cpp')
            exe = cell / (name + '.exe')
            command = [native_tools['cl'], '/nologo', '/std:c++20', '/EHsc',
                '/W4', '/WX', '/utf-8', '/' + optimization,
                '/I' + str(native / 'include'), str(core), str(source),
                '/Fe' + str(exe)]
            built = subprocess.run(command, cwd=cell, env=env, capture_output=True)
            (cell / 'compile.log').write_bytes(built.stdout + built.stderr)
            row = {'version': version, 'optimization': optimization,
                'compile_returncode': built.returncode,
                'source_sha256': {str(path.relative_to(root)):
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (core, source)}}
            if built.returncode == 0:
                result = subprocess.run([str(exe)], cwd=cell, env=env,
                    capture_output=True)
                (cell / 'test.log').write_bytes(result.stdout + result.stderr)
                row.update(test_returncode=result.returncode,
                    stdout=result.stdout.decode('utf-8', errors='replace'))
            rows.append(row)
            print(json.dumps(row))
    success = all(row.get('test_returncode') == 0 for row in rows)
    report = {'schema': 'xar.feast-planner-abi-fixtures.v1',
        'status': 'GREEN' if success else 'RED',
        'local_ck3_contacted': False, 'game_started': False, 'results': rows}
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n',
        encoding='utf-8')
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
