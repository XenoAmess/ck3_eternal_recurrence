"""Build and run the real break-betrothal provider with fixture-owned inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
NATIVE = Path(__file__).resolve().parent.parent


def run(build: Path) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    sys.pycache_prefix = str(build / '.python-cache')
    sys.path.insert(0, str(ROOT / 'tools'))
    from run_native_msvc import child_environment, visual_studio_installation, initialize_msvc
    env = child_environment(build)
    env, tools = initialize_msvc(visual_studio_installation(None, env), build, env)
    suites = []
    sources = ['ck3_12002.cpp', 'ck3_12002_context.cpp', 'ck3_12002_commands.cpp',
               'ck3_12002_phase_character.cpp', 'ck3_12002_phase_definitions.cpp', 'ck3_12002_family_value.cpp',
               'ck3_12002_family_obligations_break_penalty.cpp',
               'ck3_12002_family_obligations_break.cpp', 'ck3_12002_family_obligations_break_test.cpp']
    for mode, flags in (('Od', ['/Od', '/MDd']), ('O2', ['/O2', '/MD'])):
        work = build / mode
        work.mkdir(exist_ok=True)
        executable = work / 'family-break-terms.exe'
        command = [tools['cl'], '/nologo', '/std:c++20', '/W4', '/WX', '/permissive-',
                   '/EHsc', '/DNOMINMAX', *flags, f'/I{NATIVE / "include"}',
                   *[str(NATIVE / 'src' / name) for name in sources], f'/Fe:{executable}']
        compiled = subprocess.run(command, cwd=work, env=env, capture_output=True)
        (work / 'compile.log').write_bytes(compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError(f'{mode} compile RED: {(compiled.stdout + compiled.stderr).decode("mbcs", "replace")}')
        executed = subprocess.run([str(executable)], cwd=work, env=env, capture_output=True)
        (work / 'run.log').write_bytes(executed.stdout + executed.stderr)
        if executed.returncode:
            raise RuntimeError(f'{mode} fixture RED: {(executed.stdout + executed.stderr).decode("utf-8", "replace")}')
        suites.append({'mode': mode, 'status': 'GREEN', 'output': executed.stdout.decode().strip(),
                       'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest()})
    result = {'status': 'GREEN', 'readiness': 'static-ready', 'local_ck3_touched': False,
              'live_verified': False, 'source': 'actual native provider / fixture-owned native callbacks',
              'suites': suites}
    (build / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().build_root.resolve()), indent=2))
