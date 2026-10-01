"""Compile nonwar obligations wire and real owner-mailbox/provider fixtures."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys

NATIVE = Path(__file__).resolve().parent.parent
ROOT = NATIVE.parents[1]
FLAGS = ['/DXAR_CK3_ENABLE_G2_M5_FAMILY_OBLIGATIONS_PRIVATE_QUERY_V1',
         '/DXAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1']
SOURCES = {
    'wire': ['ck3_12002_family_obligations_wire.cpp',
             'ck3_12002_family_obligations_wire_test.cpp'],
    'mailbox': ['ck3_12002_family_obligations_wire.cpp',
                'ck3_12002_family_obligations_mailbox.cpp',
                'ck3_12002_family_obligations_lineage.cpp',
                'ck3_12002_family_obligations_break.cpp',
                'ck3_12002_family_obligations_break_penalty.cpp',
                'ck3_12002_family_value.cpp', 'ck3_12002_phase_character.cpp',
                'ck3_12002_phase_definitions.cpp', 'ck3_12002_query_mailbox.cpp',
                'main_thread_query_mailbox_v1.cpp', 'protocol.cpp',
                'ck3_12002_family_obligations_mailbox_test.cpp'],
}


def run(build: Path) -> dict:
    build.mkdir(parents=True, exist_ok=True)
    sys.pycache_prefix = str(build / '.python-cache')
    sys.path.insert(0, str(ROOT / 'tools'))
    from run_native_msvc import child_environment, visual_studio_installation, initialize_msvc
    env = child_environment(build)
    env, toolchain = initialize_msvc(visual_studio_installation(None, env), build, env)

    def suite(name: str, mode: str) -> dict:
        work = build / name / mode
        work.mkdir(parents=True, exist_ok=True)
        executable = work / f'family-obligations-{name}.exe'
        wire = work / f'{name}-native-wire.json'
        optimize = ['/Od', '/MDd'] if mode == 'Od' else ['/O2', '/MD']
        command = [toolchain['cl'], '/nologo', '/std:c++20', '/W4', '/WX',
                   '/permissive-', '/EHsc', '/DNOMINMAX', *FLAGS, *optimize,
                   f'/I{NATIVE / "include"}',
                   *[str(NATIVE / 'src' / source) for source in SOURCES[name]],
                   f'/Fe:{executable}', '/link', 'user32.lib']
        compiled = subprocess.run(command, cwd=work, env=env, capture_output=True)
        (work / 'compile.log').write_bytes(compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError(f'{name}/{mode} compile RED: '
                               f'{(compiled.stdout + compiled.stderr).decode("mbcs", "replace")}')
        tested = subprocess.run([str(executable), str(wire)], cwd=work,
                                env=env, capture_output=True)
        (work / 'run.log').write_bytes(tested.stdout + tested.stderr)
        if tested.returncode:
            raise RuntimeError(f'{name}/{mode} fixture RED: '
                               f'{(tested.stdout + tested.stderr).decode("utf-8", "replace")}')
        observation = json.loads(wire.read_text(encoding='utf-8'))['result']
        assert observation['kind'] == 'ck3_12002_family_obligations_private_v1'
        assert observation['query_status'] == 'available'
        assert observation['read_only'] and not observation['advertised']
        if name == 'mailbox':
            preview = observation['native_child_house_preview']
            assert preview['status'] == 'available' and preview['house_id'] == 0x01000001
            assert preview['selected_matrilineal_option'] is True
            assert preview['effective_matrilineal_if_accepted'] is False
        else:
            assert observation['alliance_obligations']['status'] == 'deferred_by_owner'
            penalty = observation['betrothal_break_terms']['outcome_resource_penalty']
            assert penalty['stock_prestige_effect_raw'] == -8000000
            assert not penalty['effects_complete']
        return {'suite': name, 'mode': mode, 'status': 'GREEN',
                'output': tested.stdout.decode('utf-8').strip(),
                'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                'wire_path': str(wire),
                'wire_sha256': hashlib.sha256(wire.read_bytes()).hexdigest()}

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(suite, name, mode)
                   for name in SOURCES for mode in ('Od', 'O2')]
        suites = [future.result() for future in futures]
    source_names = sorted({source for sources in SOURCES.values() for source in sources})
    result = {'status': 'GREEN', 'readiness': 'static-ready',
              'local_ck3_touched': False, 'live_verified': False,
              'war_reader_executed': False,
              'source': 'actual nonwar lineage/break reader, owner mailbox and serializer; fixture-owned callbacks/objects',
              'suites': suites,
              'sources': {name: hashlib.sha256((NATIVE / 'src' / name).read_bytes()).hexdigest()
                          for name in source_names}}
    (build / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().build_root.resolve()), indent=2))
