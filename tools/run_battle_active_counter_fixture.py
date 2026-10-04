#!/usr/bin/env python3
"""Run the two offline production active-counter cases against current sources.

Only the fixture and its seven necessary production dependencies are compiled.
The output contains the native wire and the existing Python-consumer result.
This runner does not start CK3 or build the bridge DLL.
"""
from concurrent.futures import ThreadPoolExecutor
import argparse
import sys
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--source-root', type=Path, default=ROOT)
    result.add_argument('--build-dir', type=Path, required=True,
                        help='A new directory for objects, logs, wire and results.')
    result.add_argument('--vs-install', type=Path,
                        default=Path('C:/Program Files/Microsoft Visual Studio/18/Community'))
    return result


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    args = parser().parse_args()
    source_root = args.source_root.resolve()
    RUN = args.build_dir.resolve()
    native = source_root / 'ck3_autonomous_player/native_bridge'
    RUN.mkdir(parents=True, exist_ok=False)
    (RUN / 'wire').mkdir()
    (RUN / 'temp').mkdir()
    sources = [native / 'src' / name for name in (
        'ck3_12002_active_counter_fixture_test.cpp',
        'ck3_12002_combat.cpp',
        'ck3_12002_battle.cpp',
        'ck3_12002_routes.cpp',
        'ck3_12002_battle_journal.cpp',
        'battle_terminal_journal_v1.cpp',
        'ck3_12002_phase_character.cpp',
        'battle_control_snapshot_v1_mailbox.cpp',
    )]
    report = {
        'schema_version': 1, 'status': 'HARNESS-RED', 'readiness': 'research',
        'source_root': source_root.as_posix(),
        'source_pins': [pin(path) for path in sources],
        'production_header_pins': [pin(path) for path in sorted((native / 'include').rglob('*.hpp'))],
        'compile_parallelism': len(sources), 'new_translation_units': len(sources),
        'reused_translation_units': 0, 'reused_dependencies': [],
        'whole_dll_built': False, 'old_fixture_groups_or_cases_run': False,
        'sdk_calls': 0, 'live_game_calls': 0, 'window_operations': 0,
        'shared_product_writes': 0, 'git_actions': 0,
    }
    started = time.perf_counter()
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    env = {key.upper(): value for key, value in os.environ.items()}
    env.update(TEMP=str(RUN / 'temp'), TMP=str(RUN / 'temp'),
               VSLANG='1033', PYTHONDONTWRITEBYTECODE='1')
    try:
        capture_script = RUN / 'capture-environment.cmd'
        capture_script.write_text(
            '@echo off\ncall "' + str(args.vs_install.resolve() / 'VC/Auxiliary/Build/vcvars64.bat') +
            '" >nul\nif errorlevel 1 exit /b %errorlevel%\nset\n',
            encoding='utf-8', newline='\r\n')
        capture = subprocess.run([env.get('COMSPEC', 'cmd.exe'), '/d', '/u', '/c', str(capture_script)],
            cwd=RUN, env=env, capture_output=True, timeout=30, creationflags=flags)
        require(capture.returncode == 0, 'MSVC environment unavailable.')
        for line in capture.stdout.decode('utf-16-le', errors='replace').splitlines():
            if '=' in line and not line.startswith('='):
                key, value = line.split('=', 1)
                env[key.upper()] = value
        compiler = shutil.which('cl.exe', path=env['PATH'])
        require(compiler is not None, 'MSVC compiler missing.')
        includes = [native / 'include']
        prefix = [compiler, '/nologo', '/std:c++20', '/EHsc', '/W4', '/WX', '/O2',
                  '/DNDEBUG', '/utf-8', '/DNOMINMAX', '/DWIN32_LEAN_AND_MEAN',
                  '/DUNICODE', '/D_UNICODE', '/Gy',
                  *['/I' + str(path) for path in includes]]
        report['header_priority'] = [str(path) for path in includes]
        def compile_one(source):
            object_path = RUN / (source.stem + '.obj')
            log = RUN / (source.stem + '.compile.log')
            command = prefix + ['/c', str(source), '/Fo' + str(object_path)]
            result = subprocess.run(command, cwd=RUN, env=env, capture_output=True,
                                    timeout=180, creationflags=flags)
            log.write_bytes(result.stdout + result.stderr)
            return {'source': str(source), 'command': command, 'exit_code': result.returncode,
                    'object_path': str(object_path), 'log': pin(log)}
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            compiled = list(executor.map(compile_one, sources))
        report['compile_commands'] = compiled
        require(all(row['exit_code'] == 0 for row in compiled), 'Strict minimum TUs compile failed.')
        executable = RUN / 'active-counter-control-focused.exe'
        link = [str(Path(compiler).parent / 'link.exe'), '/nologo', '/OPT:REF',
                *[row['object_path'] for row in compiled],
                '/OUT:' + str(executable), 'kernel32.lib', 'user32.lib']
        linked = subprocess.run(link, cwd=RUN, env=env, capture_output=True,
                                timeout=60, creationflags=flags)
        (RUN / 'link.log').write_bytes(linked.stdout + linked.stderr)
        report.update(link_command=link, link_exit=linked.returncode, link_log=pin(RUN / 'link.log'))
        require(linked.returncode == 0, 'Minimum production fixture link failed.')
        report['status'] = 'FIXTURE-RED'
        ran = subprocess.run([str(executable), str(RUN / 'wire')], cwd=RUN, env=env,
                             capture_output=True, timeout=30, creationflags=flags)
        (RUN / 'run.log').write_bytes(ran.stdout + ran.stderr)
        report.update(run_exit=ran.returncode, run_log=pin(RUN / 'run.log'), executable=pin(executable))
        require(ran.returncode == 0, 'New production Control fixture failed.')
        wire_path = RUN / 'wire/active_counter_control_cases.json'
        wire = json.loads(wire_path.read_text(encoding='utf-8'))
        require(wire['actual'] == 0 and len(wire['cases']) == 2, 'Two-case offline marker changed.')
        report.update(status='GREEN', readiness='static-ready', case_count=2,
                      native_json=pin(wire_path),
                      getter_received_raw_by_case=[case['getter_received_first_current_raw']
                                                   for case in wire['cases']])
        report['status'] = 'FIXTURE-RED'
        report['python_consumer'] = consume_current_wire(source_root, RUN, wire_path)
        require(report['python_consumer']['failures'] == 0, 'Existing Python consumer failed.')
        report['status'] = 'GREEN'
    except Exception as error:
        report['error'] = repr(error)
    report['elapsed_seconds'] = time.perf_counter() - started
    out = RUN / 'RESULT.json'
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'receipt': pin(out),
                      'error': report.get('error')}))
    raise SystemExit(0 if report['status'] == 'GREEN' else 1)


def consume_current_wire(source_root, run_dir, wire_path):
    sys.path.insert(0, str(source_root / 'ck3_autonomous_player/src'))
    from xar_autoplayer.bridge import battle_control_contract as contract
    from xar_autoplayer.simulation.active_counter_current_basis import project_current_counter_attack_raw
    data = json.loads(wire_path.read_text(encoding='utf-8'))
    assert data['actual'] == 0 and len(data['cases']) == 2
    outcomes = []
    for case in data['cases']:
        row = {'name': case['name']}
        try:
            frame = case['battle_control_snapshot']
            parent = contract.normalize_battle_control_snapshot_v1(
                frame,
                expected_subject_public_cunit_id=frame['subject_public_cunit_id'],
                expected_observed_date_raw=frame['observed_date_raw'],
                expected_snapshot_revision=frame['snapshot_revision'],
            )
            resume = contract.normalize_active_combat_resume_inputs_v1(
                case['active_combat_resume_inputs_v1'], parent=parent)
            counter = parent['active_counter_inputs_v1']
            assert counter == frame['active_counter_inputs_v1']
            assert resume['observed']['active_counter_inputs_v1'] == counter
            assert parent['battle_control_ready'] is True
            assert resume['input_observation_ready'] is False
            assert case['getter_received_first_current_raw'] == 1_200_001
            if case['expected_counter_available']:
                assert counter['status'] == 'available' and counter['operand_census_complete'] is True
                assert counter['class_count'] == 3
                assert counter['sides'][0]['men_at_arms_entries'][0]['current_fighting_raw'] == 1_200_001
                assert counter['sides'][0]['men_at_arms_entries'][0]['current_chunk_raw'] == 1_200_001
                assert counter['sides'][0]['men_at_arms_entries'][1]['status'] == 'absent'
                assert counter['sides'][0]['men_at_arms_entries'][0]['targets'][1]['effectiveness_raw'] == 0
                for index, context in enumerate(counter['contexts']):
                    assert context['countered_side_index'] == index
                    assert context['countering_side_index'] == 1 - index
                    assert counter['sides'][index]['primary_owner_character_id'] != parent[('attacker', 'defender')[index]]['ordered_armies'][0]['owner_character_id']
                    assert counter['sides'][index]['primary_owner_character_id'] != parent[('attacker', 'defender')[index]]['selected_commander_character_id']
                attacks, retentions = project_current_counter_attack_raw(parent)
                assert len(attacks) == 2 and all(isinstance(value, int) for value in attacks)
                assert len(retentions) == 2 and all(len(values) == 3 for values in retentions)
                row.update(current_counter_attack_raw=list(attacks), retentions_by_side=[list(values) for values in retentions],
                           consumer_result='accepted current-frame conditional counter diagnostic')
            else:
                assert counter['status'] == 'unavailable' and counter['operand_census_complete'] is False
                assert counter['class_count'] is None and counter['sides'] is None and counter['contexts'] is None
                assert counter['unavailable_reason'] == 'counter_current_chunk_unavailable'
                try:
                    project_current_counter_attack_raw(parent)
                except ValueError as error:
                    assert 'complete actual current-frame counter census' in str(error)
                else:
                    raise AssertionError('Existing consumer accepted unavailable counter leaf.')
                row['consumer_result'] = 'unavailable counter rejected by existing consumer; control ready preserved'
            row.update(status='GREEN', getter_received_first_current_raw=case['getter_received_first_current_raw'],
                       active_counter_status=counter['status'], battle_control_ready=parent['battle_control_ready'],
                       input_observation_ready=resume['input_observation_ready'],
                       same_frame_counter_mirror_equal=True)
        except Exception as error:
            row.update(status='RED', error_type=type(error).__name__, error=str(error))
        outcomes.append(row)
    failures = sum(row['status'] != 'GREEN' for row in outcomes)
    result = {
        'schema_version': 1, 'status': 'GREEN' if failures == 0 else 'RED',
        'readiness': 'static-ready' if failures == 0 else 'research',
        'cases_run': 2, 'failures': failures, 'cases': outcomes,
        'native_wire': pin(wire_path),
        'production_normalizer': pin(Path(contract.__file__)),
        'current_counter_consumer': pin(Path(sys.modules[project_current_counter_attack_raw.__module__].__file__)),
        'native_actual': data['actual'], 'old_groups_or_cases_rerun': False,
        'python_product_changes': 0, 'sdk_calls': 0, 'live_queries': 0,
        'window_operations': 0, 'shared_product_writes': 0,
    }
    out = run_dir / 'PYTHON-CONSUMER-RESULT.json'
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return {'status': result['status'], 'cases_run': 2, 'failures': failures,
            'receipt': pin(out)}


if __name__ == '__main__':
    main()
