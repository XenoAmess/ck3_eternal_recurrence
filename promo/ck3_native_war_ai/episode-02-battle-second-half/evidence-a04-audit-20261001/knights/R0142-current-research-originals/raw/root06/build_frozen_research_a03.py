"""Fresh Release build from an explicitly frozen independent research commit."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

PYTHON = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
CMAKE = Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
CTEST = CMAKE.with_name('ctest.exe')
NINJA = CMAKE.parent.parent.parent / 'Ninja/ninja.exe'

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--attempt', required=True, type=Path)
    parser.add_argument('--targets-json', required=True, type=Path)
    args = parser.parse_args()
    checkout = args.source.resolve()
    source = checkout / 'ck3_autonomous_player/native_bridge'
    run = args.attempt.resolve()
    require(not run.exists(), 'New build attempt already exists')
    run.mkdir(parents=True)
    build = run / 'build'
    started = time.monotonic()
    def write(name, value):
        with (run / name).open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    def phase(name, argv, cwd=source):
        write(name + '-argv.json', {'argv': argv, 'cwd': str(cwd), 'at_utc': datetime.now(timezone.utc).isoformat()})
        with (run / (name + '-stdout.bin')).open('xb') as out, (run / (name + '-stderr.bin')).open('xb') as err:
            result = subprocess.run(argv, cwd=cwd, stdout=out, stderr=err)
        write(name + '-result.json', {'returncode': result.returncode, 'at_utc': datetime.now(timezone.utc).isoformat(),
              'stdout': identity(run / (name + '-stdout.bin')), 'stderr': identity(run / (name + '-stderr.bin'))})
        print(name + ' returncode=' + str(result.returncode), flush=True)
        require(result.returncode == 0, name + ' failed; original stdout/stderr preserved')
    require(Path(sys.executable).resolve() == PYTHON.resolve(), 'Verified interpreter required')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=checkout, text=True)
    require(head == args.source_commit and not status.strip(), 'Source must match clean frozen commit')
    compiler = shutil.which('cl')
    require(compiler and CMAKE.is_file() and NINJA.is_file(), 'Verified vcvars compiler/toolchain unavailable')
    spec = importlib.util.spec_from_file_location('_frozen_native_build', source / 'tools/build_fresh.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    fingerprint = helper.native_bridge_source_fingerprint(source)
    targets = json.loads(args.targets_json.read_text(encoding='utf-8'))
    require(isinstance(targets, dict) and targets.get('build_targets') and targets.get('ctest_regex'), 'Reviewed target list required')
    write('source-and-environment.json', {'source_commit': head, 'source': str(checkout), 'source_fingerprint_sha256': fingerprint,
          'python': identity(PYTHON), 'python_version': sys.version, 'compiler': identity(compiler), 'cmake': identity(CMAKE),
          'ninja': identity(NINJA), 'targets_input': identity(args.targets_json), 'targets': targets,
          'no_game_launched': True, 'no_master_intake': True, 'configuration': 'Release',
          'process_environment_overrides': {'PYTHONUTF8': '0', 'PYTHONIOENCODING': 'utf-8', 'VSLANG': '1033'}})
    os.environ['VSLANG'] = '1033'
    executable = Path('C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe')
    executable_identity = identity(executable)
    require(executable_identity['bytes'] == 95206008 and executable_identity['sha256'] ==
            '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86',
            'Actual native regression executable differs from reviewed CK3 exact build')
    write('exact-executable-regression-input.json', {'executable': executable_identity, 'game_launched': False})
    phase('configure', [str(CMAKE), '-S', str(source), '-B', str(build), '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release',
          '-DXAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1=ON', '-DCMAKE_MAKE_PROGRAM=' + str(NINJA),
          '-DPython3_EXECUTABLE=' + str(PYTHON), '-DXAR_CK3_EXECUTABLE_PATH=' + str(executable)])
    mode = helper.repair_ninja_msvc_dependency_prefix(build, Path(compiler))
    write('dependency-prefix.json', {'mode': mode})
    phase('build', [str(CMAKE), '--build', str(build), '--parallel', '4', '--target',
                   'xar_ck3_bridge', 'xar_ck3_bridge_injector', *targets['build_targets']])
    phase('ctest', [str(CTEST), '--test-dir', str(build), '--output-on-failure', '--output-junit', str(run / 'ctest-junit.xml'),
                   '-R', targets['ctest_regex']])
    import xml.etree.ElementTree as ET
    junit = ET.parse(run / 'ctest-junit.xml').getroot()
    cases = list(junit.iter('testcase'))
    expected = targets.get('expected_ctest_names', [])
    require(expected and len(expected) == len(set(expected)), 'Exact expected CTest names required')
    require(len(cases) == len(expected) and {case.get('name') for case in cases} == set(expected),
            'Actual CTest names/count differ; do not treat no tests as PASS')
    require(all(case.get('status') == 'run' and not any(child.tag in {'failure', 'error', 'skipped'} for child in case)
                for case in cases), 'A focused native test failed/skipped/disabled')
    write('exact-test-result.json', {'expected_names': expected, 'actual_names': [case.get('name') for case in cases],
          'test_count': len(cases), 'all_ran_without_failure_or_skip': True, 'junit': identity(run / 'ctest-junit.xml'),
          'does_not_prove_live_game_or_ui': True})
    phase('trace-dll-static-verifier', [str(PYTHON), '-X', 'utf8=0', '-B', str(source / 'tools/verify_private_combat_trace_dll.py'),
          '--dll', str(build / 'xar_ck3_bridge.dll'), '--cmake-cache', str(build / 'CMakeCache.txt')])
    require(helper.native_bridge_source_fingerprint(source) == fingerprint, 'Native source changed during build')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip() == head, 'HEAD changed during build')
    write('candidate-manifest.json', {'schema': 'ck3.e2.six-gap-native-research-candidate/v1',
          'status': 'RELEASE_BUILD_OFFLINE_CHECKS_PASSED_LIVE_PENDING', 'source_commit': head, 'source': str(checkout),
          'source_fingerprint_sha256': fingerprint, 'exact_executable': executable_identity,
          'dll': identity(build / 'xar_ck3_bridge.dll'),
          'injector': identity(build / 'xar_ck3_bridge_injector.exe'), 'targets': targets,
          'build_does_not_prove_real_ui_or_causal_chain': True, 'human_movie_signoff': False,
          'duration_seconds': round(time.monotonic() - started, 3)})
    print('Frozen Release candidate built; exact-build live research remains pending.', flush=True)

if __name__ == '__main__':
    main()
