"""Root-only Runtime31 Source31 arrival / Source32 disembark and phase-effect / current household incremental build.

Default writes the exact frozen-source plan and response files. --execute runs
only selected new fixture source generators, compiles declared recursive-layout
owners/new production leaves plus the explicit new fixture targets at BelowNormal,
then archives and links. It never runs fixtures, consumers or CK3.
"""
from __future__ import annotations

import argparse
import ctypes
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

MIG = Path('Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration')
FIRSTS = ()


def norm(value):
    return str(value).replace('\\', '/').lower()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def utc():
    return datetime.now(timezone.utc).isoformat()


def owner_key(row):
    # Added producers have their own owner, never their compiler-template key.
    return row.get('original_owner') or row.get('original_object') or row.get('qualified_parent_object') or row.get('qualified_object') or row['object_path']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--source-metadata', type=Path)
    parser.add_argument('--parent-receipt', type=Path, default=MIG / 'entry-live-fix30/ROOT-PARENT-RUNTIME-INCREMENTAL-DLL.json')
    parser.add_argument('--ownership-inputs', type=Path, required=True)
    parser.add_argument('--target-recipes', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--resume-from', type=Path, help='Same source attempt: reuse successful compiler/archive receipts; preserve earlier RED artifacts')
    parser.add_argument('--resume-invalidate-cpp', action='append', default=[],
        help='Root-confirmed changed CPP across a source repair; only these owners are recompiled')
    parser.add_argument('--jobs', type=int, default=64)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.jobs <= 64:
        parser.error('--jobs must be 1..64')
    parent_receipt = read(args.parent_receipt)
    lineage_path = Path(parent_receipt['actual_object_lineage']['path'])
    commands_path = Path(parent_receipt['actual_compile_commands']['path'])
    lineage = read(lineage_path)
    commands = read(commands_path)
    parent_plan_path = Path(lineage['joint_build_plan'])
    parent_plan = read(parent_plan_path)
    ownership = read(args.ownership_inputs)
    target_recipes = read(args.target_recipes)
    owners = [(row['target'], row['cpp'], False) for row in ownership['affected']]
    owners.extend((row['target'], row['cpp'], True) for row in ownership.get('new_production_owners', []))
    native = args.source_root.resolve() / 'ck3_autonomous_player/native_bridge'
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    objects = lineage['objects']
    command_rows = {(row['target'], norm(row['object_path'])): row for row in commands['rows']}
    original_databases = {}
    retained_plans = {}
    def projected_command_argv(value):
        if isinstance(value, list):
            return list(value)
        if isinstance(value, dict):
            return projected_command_argv(value.get('arguments') or value.get('argv') or value['command'])
        count = ctypes.c_int()
        splitter = ctypes.windll.shell32.CommandLineToArgvW
        splitter.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        splitter.restype = ctypes.POINTER(ctypes.c_wchar_p)
        parts = splitter(value, ctypes.byref(count))
        if not parts:
            raise OSError('Could not split actual retained projected compiler command')
        try:
            return [parts[index] for index in range(count.value)]
        finally:
            free = ctypes.windll.kernel32.LocalFree
            free.argtypes = [ctypes.c_void_p]
            free.restype = ctypes.c_void_p
            free(parts)
    def retained_command(template):
        key = (template['target'], norm(template['object_path']))
        if key in command_rows:
            return command_rows[key]
        reference = template['compiler_command_reference']
        if 'build_plan' in reference:
            path = reference['build_plan']
            if path not in retained_plans:
                retained_plans[path] = read(path)
            retained = retained_plans[path]
            output = reference.get('replacement_object') or template['object_path']
            for group in ('extra_production_sources_at_compile', 'changes', 'inherited_changes'):
                rows = retained.get(group, [])
                if isinstance(rows, dict):
                    rows = rows.values()
                for held in rows:
                    if norm(held.get('replacement_object') or held.get('output_object')) != norm(output):
                        continue
                    if held.get('production_compile_owner', template['target']) != template['target']:
                        continue
                    projected = held.get('projected_compile_command') or held.get('argv')
                    if projected:
                        return {'argv': projected_command_argv(projected), 'original_database': path,
                            'retained_command_reference': reference, 'retained_plan_group': group}
            raise KeyError('Actual retained build-plan replacement owner not found: ' + str(reference))
        database = reference['database']
        if database not in original_databases:
            original_databases[database] = read(database)
        for held in original_databases[database]:
            if norm(held.get('output', '')) != norm(reference['output']):
                continue
            argv = held.get('arguments')
            if argv is None:
                count = ctypes.c_int()
                splitter = ctypes.windll.shell32.CommandLineToArgvW
                splitter.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
                splitter.restype = ctypes.POINTER(ctypes.c_wchar_p)
                parts = splitter(held['command'], ctypes.byref(count))
                if not parts:
                    raise OSError('Could not split retained compiler command')
                try:
                    argv = [parts[index] for index in range(count.value)]
                finally:
                    free = ctypes.windll.kernel32.LocalFree
                    free.argtypes = [ctypes.c_void_p]
                    free.restype = ctypes.c_void_p
                    free(parts)
            return {'argv': argv, 'original_database': database}
        raise KeyError('Declared original compile owner not found: ' + str(reference))
    current = {(row['target'], row['cpp']): row for row in objects}
    runtime_template = current[('xar_ck3_12002_runtime', 'src/ck3_12002_army.cpp')]
    resume_rows = {}
    invalidated_cpp = {norm(value) for value in args.resume_invalidate_cpp}
    previous = None
    if args.resume_from:
        previous = read(args.resume_from / 'BUILD-PLAN.json')
        if previous['source_head'] != args.expected_head and not invalidated_cpp:
            raise ValueError('Cross-head repair resume requires its exact changed CPP list')
        for row in previous['production_changes'] + previous['new_fixture_compile_inputs']:
            receipt = Path(row.get('reused_green_receipt') or args.resume_from / 'logs' / (row['label'] + '.json'))
            if receipt.is_file() and Path(row['output_object']).is_file() and read(receipt).get('exit_code') == 0 and norm(row['cpp']) not in invalidated_cpp:
                resume_rows[(row['target'], row['original_owner'])] = (row, str(receipt))
    includes = ['/I' + str(path) for path in (args.source_root.resolve(), native / 'include', native / 'include/xar_bridge', native / 'src', native / 'research')]

    def project(target, cpp, ordinal, row=None, fixture=False, source_path=None, generated=False, additional_includes=(), additional_definitions=(), template_row=None):
        template = row or template_row or runtime_template
        held = retained_command(template)
        argv = projected_command_argv(held)
        obj = output / 'objects' / target / f'{ordinal:02d}-{Path(cpp).name}.obj'
        obj.parent.mkdir(parents=True, exist_ok=True)
        source = Path(source_path) if source_path else native / cpp
        if not generated and not source.is_file():
            raise FileNotFoundError(source)
        projected = [argv[0], *includes, *('/I' + str(value) for value in additional_includes)]
        saw_source = False
        for value in argv[1:]:
            lower = value.lower()
            if lower.startswith(('/fo', '/fd')):
                continue
            if fixture and lower in ('-dxar_ck3_bridge_exports', '/dxar_ck3_bridge_exports'):
                continue
            if lower.endswith(('.cpp', '.cxx', '.cc')):
                value = str(source)
                saw_source = True
            # All qualified fallback include roots and exact feature defines stay.
            projected.append(value)
        if not saw_source:
            raise ValueError('No source in retained compiler argv: ' + cpp)
        projected.extend(['/Fo' + str(obj), '/Fd' + str(obj.with_suffix('.pdb'))])
        if fixture:
            projected.extend(['/UNDEBUG', '/WX', '/utf-8', '/Gy', '/DNOMINMAX', '/DWIN32_LEAN_AND_MEAN', '/DUNICODE', '/D_UNICODE'])
        projected.extend('/D' + value for value in additional_definitions)
        original = owner_key(row) if row else 'new:' + target + ':' + cpp
        value = {'target': target, 'cpp': cpp, 'original_owner': original,
            'original_object': row.get('original_object') if row else None,
            'qualified_parent_object': row['object_path'] if row else None,
            'template_original_owner': owner_key(template),
            'retained_command_source': held.get('original_database', str(commands_path)),
            'template_actual_compiler_receipt': template.get('actual_compiler_receipt'),
            'output_object': str(obj), 'argv': projected,
            'cwd': 'C:/codex-ck3-background/migration4-complete-domain-build/strict07/cache-observers'
                if target == 'xar_ck3_bridge' and cpp == 'src/realm_law_governance_snapshot_v1.cpp' else str(output),
            'label': f'{ordinal:02d}-' + target + '-' + Path(cpp).name,
            'physical_compiled_source': str(source), 'source_head': args.expected_head,
            'header_source_basis': str(args.source_root.resolve()),
            'qualified_fallback_roots_preserved': True, 'compile_required': True,
            'generated_source': generated}
        reused = resume_rows.get((target, original))
        if reused:
            old, receipt = reused
            value.update(output_object=old['output_object'], reused_green_receipt=receipt, compile_required=False,
                physical_compiled_source=old['physical_compiled_source'], source_head=old['source_head'],
                header_source_basis=old['header_source_basis'], retained_actual_compiler_argv=old.get('retained_actual_compiler_argv', old['argv']),
                reuse_basis='Actual GREEN compiler receipt; CPP outside Root-confirmed changed-source/header dependency list.')
        return value

    changes = []
    replacements = {}
    extras = []
    for ordinal, (target, cpp, new) in enumerate(owners, 1):
        row = None if new else current[(target, cpp)]
        declared_new = next((item for item in ownership.get('new_production_owners', [])
            if item['target'] == target and item['cpp'] == cpp), None) if new else None
        reference = declared_new.get('template_command_reference') if declared_new else None
        template_row = current[(reference['target'], reference['cpp'])] if reference else None
        value = project(target, cpp, ordinal, row, template_row=template_row)
        changes.append(value)
        if new:
            extras.append(value['output_object'])
        else:
            replacements[norm(row['object_path'])] = value['output_object']
    bridge_objects = [replacements.get(norm(value), value) for value in parent_plan['final_dll_object_paths']]
    runtime_objects = [replacements.get(norm(value), value) for value in parent_plan['final_runtime_object_paths']] + extras
    fixtures = []
    generator_steps = []
    generated_outputs = []
    fixture_recipes = {}
    for recipe in target_recipes['targets']:
        target = recipe['target']
        target_output = output / 'generated' / target
        target_output.mkdir(parents=True, exist_ok=True)
        context = {'source_root': str(args.source_root.resolve()), 'native': str(native),
            'output_dir': str(target_output), 'python': sys.executable}
        def expand(value):
            return value.format(**context)
        fixture_recipes[target] = {**recipe,
            'link_extra_libraries': [expand(value) for value in recipe.get('link_extra_libraries', [])]}
        generator_steps += [{**row, 'label': target + '-' + row['label'],
            'argv': [expand(value) for value in row['argv']], 'cwd': expand(row['cwd'])}
            for row in recipe.get('generator_steps', [])]
        generated_outputs += [expand(value) for value in recipe.get('generated_outputs', [])]
        for row in recipe['fixture_sources']:
            fixture_template = recipe.get('fixture_compile_template_owner')
            fixtures.append(project(target, row['cpp'], len(changes) + len(fixtures) + 1,
                fixture=True, source_path=expand(row['path']) if row.get('path') else None,
                generated=row.get('generated', False),
                additional_includes=[expand(value) for value in recipe.get('fixture_include_dirs', [])],
                additional_definitions=recipe.get('fixture_compile_definitions', []),
                template_row=current[(fixture_template['target'], fixture_template['cpp'])] if fixture_template else None))
    binaries = output / 'binaries'
    binaries.mkdir(exist_ok=True)
    runtime = binaries / 'xar_ck3_12002_runtime.lib'
    archive_required = True
    archive_reused_receipt = None
    if previous:
        archive_receipt = Path(previous.get('runtime_library_reused_receipt') or args.resume_from / 'logs/runtime-archive.json')
        previous_runtime = Path(previous['runtime_library_path'])
        if archive_receipt.is_file() and previous_runtime.is_file() and read(archive_receipt).get('exit_code') == 0 and not any(row['compile_required'] for row in changes if row['target'] == 'xar_ck3_12002_runtime'):
            runtime = previous_runtime
            archive_required = False
            archive_reused_receipt = str(archive_receipt)

    def response(name, values):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(subprocess.list2cmdline([value]) for value in values) + '\n', encoding='utf-8')
        return str(path)

    archive = [('/out:' + str(runtime)) if value.lower().startswith('/out:') else '@' + response('runtime.rsp', runtime_objects) if value.startswith('@') else value for value in parent_plan['runtime_archive_command']]
    libraries = [str(runtime) if norm(value) == norm(parent_plan['runtime_library_path']) else value for value in parent_plan['link_libraries_at_build']]
    response('CMakeFiles/dll.rsp', bridge_objects + libraries)
    dll = ['--intdir=' + str(output / 'dll-link') if value.startswith('--intdir=') else
        '@CMakeFiles/dll.rsp' if value.startswith('@') else
        '/out:' + str(binaries / 'xar_ck3_bridge.dll') if value.lower().startswith('/out:') else
        '/implib:' + str(binaries / 'xar_ck3_bridge.lib') if value.lower().startswith('/implib:') else
        '/pdb:' + str(binaries / 'xar_ck3_bridge.pdb') if value.lower().startswith('/pdb:') else value
        for value in parent_plan['dll_link_command']]
    dll_path = binaries / 'xar_ck3_bridge.dll'
    dll_link_required = True
    dll_reused_receipt = None
    if previous and previous['source_head'] == args.expected_head and not any(row['compile_required'] for row in changes):
        receipt = Path(previous.get('dll_reused_receipt') or args.resume_from / 'logs/dll-link.json')
        old_dll = Path(previous.get('dll_path') or next(value[5:] for value in previous['dll_link_command'] if value.lower().startswith('/out:')))
        same_bridge = [norm(value) for value in bridge_objects] == [norm(value) for value in previous['final_dll_object_paths']]
        same_runtime = [norm(value) for value in runtime_objects] == [norm(value) for value in previous['final_runtime_object_paths']]
        if same_bridge and same_runtime and not archive_required and receipt.is_file() and old_dll.is_file() and read(receipt).get('exit_code') == 0:
            dll_link_required = False
            dll_reused_receipt = str(receipt)
            dll_path = old_dll
    linker = next(value for value in dll if value.lower().endswith('link.exe'))
    protocol = next(row['object_path'] for row in objects if row['target'] == 'xar_bridge_protocol')
    protocol_lib = next(value for value in libraries if norm(value).endswith('/xar_bridge_protocol.lib'))
    fixture_links = []
    fixture_groups = {}
    for fixture in fixtures:
        fixture_groups.setdefault(fixture['target'], []).append(fixture['output_object'])
    for target, fixture_objects in fixture_groups.items():
        recipe = fixture_recipes[target]
        scope = recipe['link_scope']
        if scope == 'whole_bridge':
            inputs = [*fixture_objects, *bridge_objects, *libraries]
        elif scope == 'runtime_protocol':
            inputs = [*fixture_objects, str(runtime), protocol_lib]
        elif scope == 'standalone':
            inputs = list(fixture_objects)
        else:
            raise ValueError('Unsupported declared fixture link scope: ' + scope)
        inputs += recipe.get('link_extra_libraries', [])
        fixture_links.append({'target': target, 'link_scope': scope, 'argv': [linker, '/nologo',
            '@' + response('CMakeFiles/' + target + '.rsp', inputs),
            '/out:' + str(binaries / (target + '.exe')), '/pdb:' + str(binaries / (target + '.pdb')),
            '/machine:x64', '/OPT:REF', '/INCREMENTAL:NO'], 'cwd': str(output)})
    env_added = dict(parent_plan.get('compiler_environment_added', {}))
    env_added['CL'] = subprocess.list2cmdline(includes) + ' ' + env_added.get('CL', '')
    plan = {'schema': 'xar.functional-batch.actual-runtime31-incremental-build/v1',
        'source_root': str(args.source_root.resolve()), 'source_head': args.expected_head,
        'source_metadata': str(args.source_metadata) if args.source_metadata else None,
        'qualified_parent_receipt': str(args.parent_receipt), 'parent_plan': str(parent_plan_path),
        'parent_actual_object_lineage': str(lineage_path), 'parent_actual_compile_commands': str(commands_path),
        'parent_mixed_source_input_binding': parent_receipt['runtime_input_binding']['path'],
        'ownership_inputs': str(args.ownership_inputs), 'target_recipes': str(args.target_recipes),
        'generator_steps': generator_steps, 'generated_outputs': generated_outputs,
        'retained_generated_sources': [held for recipe in target_recipes['targets'] for held in recipe.get('held_generated_sources', [])],
        'subprocess_priority': 'BelowNormal', 'jobs': args.jobs,
        'selection': 'Actual717 canonical30 owner graph reselects Source31/32 Army and phase-effect changed header/CPP consumers. All717 mixed qualified owners retained or replaced exactly; no new production owner; only Army source31/32 modes, phase-effect and current-household new whole modes are prepared.',
        'affected_owner_include_chains': ownership['affected'],
        'parent_actual_owner_count': len(objects), 'actual_owner_count_after': len(objects) + len(extras),
        'production_owner_input_count': len(changes), 'production_compile_count': sum(row['compile_required'] for row in changes),
        'new_production_owner_count': len(extras), 'fixture_compile_count': sum(row['compile_required'] for row in fixtures),
        'production_changes': changes, 'new_fixture_compile_inputs': fixtures,
        'final_dll_object_paths': bridge_objects, 'final_runtime_object_paths': runtime_objects,
        'qualified_protocol_object': protocol, 'link_libraries_at_build': libraries,
        'runtime_archive_command': archive, 'runtime_archive_required': archive_required,
        'runtime_library_path': str(runtime), 'fresh_runtime_library_path': str(runtime),
        'runtime_library_reused_receipt': archive_reused_receipt,
        'dll_link_command': dll, 'dll_linker_response_argument': '@CMakeFiles/dll.rsp',
        'dll_link_required': dll_link_required, 'dll_path': str(dll_path),
        'dll_reused_receipt': dll_reused_receipt,
        'fixture_link_commands': fixture_links, 'compiler_environment_added': env_added,
        'msvc_environment_bootstrap': parent_plan['msvc_environment_bootstrap'],
        'msvc_environment_keys_exported': ['INCLUDE', 'LIB', 'LIBPATH', 'PATH'],
        'candidate_on': 66, 'candidate_off': 51, 'feature_flag_changes': 0,
        'resume_from': str(args.resume_from) if args.resume_from else None,
        'resume_source_head': previous['source_head'] if previous else None,
        'resume_invalidated_cpp': args.resume_invalidate_cpp,
        'resumed_green_input_count': sum(not row['compile_required'] for row in changes + fixtures),
        'build_executed': bool(args.execute), 'native_first': 'AUTHORED_NOTRUN',
        'registered_consumers_first': 'AUTHORED_NOTRUN', 'old_fixture_executions': 0, 'game_operations': 0}
    write(output / 'BUILD-PLAN.json', plan)
    summary = {'plan': str(output / 'BUILD-PLAN.json'), 'production_compile_count': plan['production_compile_count'],
        'fixture_compile_count': plan['fixture_compile_count'], 'bridge_objects': len(bridge_objects),
        'runtime_objects': len(runtime_objects), 'protocol_objects': 1,
        'runtime_archive_required': archive_required, 'dll_link_required': dll_link_required,
        'resumed_green_input_count': plan['resumed_green_input_count'],
        'new_fixture_targets': list(fixture_groups), 'fixture_generator_steps': len(generator_steps),
        'jobs': args.jobs, 'priority': 'BelowNormal', 'execute': args.execute}
    print(json.dumps(summary))
    if not args.execute:
        return
    environment = os.environ.copy()
    priority = subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 0
    for stage in generator_steps:
        begin = utc()
        generated = subprocess.run(stage['argv'], cwd=stage['cwd'], env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=priority)
        log = output / 'logs' / (stage['label'] + '.log')
        log.parent.mkdir(exist_ok=True)
        log.write_bytes(generated.stdout)
        write(log.with_suffix('.json'), {'exit_code': generated.returncode, 'start_utc': begin,
            'end_utc': utc(), 'log': str(log), 'source_head': args.expected_head, 'stage': stage['label']})
        if generated.returncode:
            write(output / 'BUILD-RESULT.json', {'status': 'RED', 'phase': stage['label'],
                'exit_code': generated.returncode, 'source_head': args.expected_head, 'game_operations': 0})
            raise SystemExit(1)
    for path in plan['generated_outputs']:
        if not Path(path).is_file():
            raise FileNotFoundError('Frozen phase generator did not produce ' + path)
    activation = output / 'activate-msvc.cmd'
    activation.write_text('@echo off\ncall "' + plan['msvc_environment_bootstrap'] + '" >nul && "' + sys.executable + '" -B -X utf8 "' + str(Path(__file__).resolve()) + '" --export-msvc-env\n', encoding='utf-8')
    captured = subprocess.run(['cmd.exe', '/d', '/c', str(activation)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, creationflags=priority)
    if captured.returncode:
        (output / 'msvc-bootstrap-error.log').write_bytes(captured.stderr)
        write(output / 'BUILD-RESULT.json', {'status': 'RED', 'phase': 'msvc-bootstrap', 'exit_code': captured.returncode, 'source_head': args.expected_head})
        raise SystemExit(1)
    environment.update(json.loads(captured.stdout.decode('utf-8')))
    environment.update(env_added)

    def run(row, label):
        start, start_utc = time.time(), utc()
        result = subprocess.run(row['argv'], cwd=row['cwd'], env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=priority)
        log = output / 'logs' / (label + '.log')
        log.parent.mkdir(exist_ok=True)
        log.write_bytes(result.stdout)
        receipt = {'exit_code': result.returncode, 'start_utc': start_utc, 'end_utc': utc(),
            'seconds': time.time() - start, 'log': str(log), 'source_head': args.expected_head,
            'output_object': row.get('output_object'), 'original_owner': row.get('original_owner')}
        write(log.with_suffix('.json'), receipt)
        return receipt

    all_inputs = changes + fixtures
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [(row, pool.submit(run, row, row['label'])) for row in all_inputs if row['compile_required']]
        results = [(row, job.result()) for row, job in futures]
    failed = [receipt for row, receipt in results if receipt['exit_code']]
    if failed:
        write(output / 'BUILD-RESULT.json', {'status': 'RED', 'phase': 'compile', 'source_head': args.expected_head,
            'compiled_inputs': len(results), 'failed_count': len(failed), 'failures': failed, 'native_first': 'NOTRUN', 'game_operations': 0})
        print(json.dumps({'status': 'RED', 'phase': 'compile', 'failed_count': len(failed), 'result': str(output / 'BUILD-RESULT.json')}))
        raise SystemExit(1)
    link_steps = []
    if archive_required:
        link_steps.append(('runtime-archive', {'argv': archive, 'cwd': str(output)}))
    if dll_link_required:
        link_steps.append(('dll-link', {'argv': dll, 'cwd': str(output)}))
    link_steps += [(row['target'] + '-link', row) for row in fixture_links]
    for label, row in link_steps:
        receipt = run(row, label)
        if receipt['exit_code']:
            write(output / 'BUILD-RESULT.json', {'status': 'RED', 'phase': label, 'source_head': args.expected_head, 'failure': receipt, 'native_first': 'NOTRUN', 'game_operations': 0})
            print(json.dumps({'status': 'RED', 'phase': label, 'result': str(output / 'BUILD-RESULT.json')}))
            raise SystemExit(1)
    write(output / 'BUILD-RESULT.json', {'status': 'GREEN', 'exit_code': 0, 'source_head': args.expected_head,
        'production_compile_count': plan['production_compile_count'], 'fixture_compile_count': plan['fixture_compile_count'],
        'resumed_green_input_count': plan['resumed_green_input_count'], 'runtime_archive_invocations': int(archive_required),
        'runtime_library_path': str(runtime), 'runtime_library_reused_receipt': archive_reused_receipt,
        'dll_link_invocations': int(dll_link_required), 'dll_path': str(dll_path),
        'dll_reused_receipt': dll_reused_receipt, 'fixture_link_invocations': len(fixture_links),
        'native_first': 'NOTRUN', 'registered_consumers_first': 'NOTRUN', 'game_operations': 0})
    print(json.dumps({'status': 'GREEN', 'result': str(output / 'BUILD-RESULT.json')}))


if __name__ == '__main__':
    if sys.argv[1:] == ['--export-msvc-env']:
        print(json.dumps({key: os.environ.get(key, '') for key in ('INCLUDE', 'LIB', 'LIBPATH', 'PATH')}))
    else:
        main()
