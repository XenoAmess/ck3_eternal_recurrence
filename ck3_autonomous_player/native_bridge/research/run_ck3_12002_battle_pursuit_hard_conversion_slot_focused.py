"""Run one production pursuit-conversion slot case; reuse six closed objects."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def require(condition: object, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def load_helper(path: Path):
    spec = importlib.util.spec_from_file_location('pursuit_slot_msvc', path)
    require(spec is not None and spec.loader is not None, 'MSVC bootstrap import failed')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project-root', 'header-projection-root', 'production-root',
                 'fixture-root', 'reuse-object-dir', 'build-dir'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--reuse-new-object-dir', type=Path)
    args = parser.parse_args()
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    report = {'status': 'RED', 'cases': 1, 'actual': 0, 'old_cases_run': 0,
              'game_calls': 0, 'window_operations': 0, 'registered_calls': 0}
    try:
        prior_root = args.reuse_new_object_dir or args.reuse_object_dir
        prior_path = prior_root.resolve() / 'RESULT.json'
        prior = json.loads(prior_path.read_text(encoding='utf-8'))
        require(prior.get('compile_exit') == 0 and prior.get('link_exit') == 0,
                'reuse requires the prior strict compile/link GREEN')
        production = args.production_root.resolve()
        fixture = args.fixture_root.resolve()
        native = fixture / 'ck3_autonomous_player/native_bridge/src/ck3_12002_battle_pursuit_hard_conversion_slot_test.cpp'
        battle = production / 'ck3_autonomous_player/native_bridge/src/ck3_12002_battle.cpp'
        serializer = production / 'ck3_autonomous_player/native_bridge/src/battle_control_snapshot_v1_mailbox.cpp'
        sources = [native, serializer] if args.reuse_new_object_dir else [native, battle]
        includes = [root / 'ck3_autonomous_player/native_bridge/include' for root in
                    (args.header_projection_root.resolve(), production, args.project_root.resolve())]
        helper_path = args.project_root.resolve() / 'tools/run_native_msvc.py'
        helper = load_helper(helper_path)
        environment = helper.child_environment(output)
        environment, compiler = helper.initialize_msvc(
            helper.visual_studio_installation(None, environment), output, environment)
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        cl = compiler['cl']
        prefix = [cl, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX', '/O2',
                  '/DNDEBUG', '/utf-8', '/DNOMINMAX', '/DWIN32_LEAN_AND_MEAN',
                  '/DUNICODE', '/D_UNICODE', '/Gy',
                  *['/I' + str(path) for path in includes]]
        prior_pins = {str(Path(row['path']).resolve()): row['sha256']
                      for row in prior['source_pins']}
        reused = []
        for row in prior['compile_commands']:
            source = Path(row['source']).resolve()
            replaced_stems = ({'ck3_12002_battle_pursuit_hard_conversion_slot_test',
                               'battle_control_snapshot_v1_mailbox'}
                              if args.reuse_new_object_dir else
                              {'ck3_12002_battle_phase_transition_inputs_test', 'ck3_12002_battle'})
            if source.stem in replaced_stems:
                continue
            require(prior_pins.get(str(source)) == pin(source)['sha256'],
                    'reused production source differs from the closed compile')
            require(Path(row['object_path']).is_file(), 'closed production object missing')
            reused.append(dict(row, reused=True))
        require(len(reused) == 6, 'focused slot test must reuse exactly six production objects')

        def compile_one(source: Path) -> dict:
            obj = output / (source.stem + '.obj')
            log = output / (source.stem + '.compile.log')
            command = prefix + ['/c', str(source), '/Fo' + str(obj)]
            compiled = subprocess.run(command, cwd=output, env=environment,
                                      capture_output=True, timeout=180, creationflags=flags)
            log.write_bytes(compiled.stdout + compiled.stderr)
            return {'source': str(source), 'object_path': str(obj), 'command': command,
                    'exit_code': compiled.returncode, 'log': pin(log)}

        with ThreadPoolExecutor(max_workers=2) as pool:
            compiled = list(pool.map(compile_one, sources))
        report.update(compile_commands=compiled + reused, compile_parallelism=2,
                      recompiled_translation_units=2, reused_production_objects=6,
                      reuse_receipt=pin(prior_path), compiler_helper=pin(helper_path),
                      recompile_reason=('actual mixed-current-DTO serializer harness AV'
                                        if args.reuse_new_object_dir else 'new corrected binding'),
                      source_pins=[pin(Path(row['source'])) for row in compiled + reused],
                      include_paths=[str(path) for path in includes])
        report['compile_exit'] = next((row['exit_code'] for row in compiled
                                       if row['exit_code'] != 0), 0)
        require(report['compile_exit'] == 0, 'strict focused compile failed')
        executable = output / 'battle-pursuit-hard-conversion-slot-focused.exe'
        link = [str(Path(cl).parent / 'link.exe'), '/nologo', '/OPT:REF',
                *[row['object_path'] for row in compiled + reused],
                '/OUT:' + str(executable), 'kernel32.lib', 'user32.lib']
        linked = subprocess.run(link, cwd=output, env=environment, capture_output=True,
                                timeout=60, creationflags=flags)
        (output / 'link.log').write_bytes(linked.stdout + linked.stderr)
        report.update(link_command=link, link_exit=linked.returncode,
                      link_log=pin(output / 'link.log'))
        require(linked.returncode == 0, 'strict focused link failed')
        wire_dir = output / 'wire'
        wire_dir.mkdir(exist_ok=True)
        run = subprocess.run([str(executable), str(wire_dir)], cwd=output,
                             env=environment, capture_output=True, timeout=30,
                             creationflags=flags)
        (output / 'run.log').write_bytes(run.stdout + run.stderr)
        report.update(native_exit=run.returncode, run_log=pin(output / 'run.log'),
                      executable=pin(executable))
        require(run.returncode == 0, 'one production binding/current-loss case failed')
        wire = wire_dir / 'pursuit_hard_conversion_slot.json'
        report.update(status='GREEN', native_json=pin(wire))
    except Exception as error:
        report['error'] = repr(error)
    report['elapsed_seconds'] = time.monotonic() - started
    (output / 'RESULT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'result': str(output / 'RESULT.json')}, indent=2))
    return 0 if report['status'] == 'GREEN' else 1


if __name__ == '__main__':
    raise SystemExit(main())
