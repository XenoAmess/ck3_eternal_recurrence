"""Prepare exact2-production-TU Native verification metadata. Never launches a process.

An external Native declaration is required. This module checks its consistency;
it cannot grant SDK qualification, resource permission, or execution credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time


JSON_LIMIT = 2 * 1024 * 1024
SOURCE_LIMIT = 4 * 1024 * 1024
CLASS_LIMIT = 16 * 1024 * 1024
VM = ['-J-Xmx192m', '-J-XX:ActiveProcessorCount=1']
PROFILE = 'two-prod-one-test-explicit-methods'
IDENTIFIER = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*\Z')
FQN = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+\Z')


class RecipeError(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, str(detail)
        super().__init__(code + ': ' + self.detail)


def need(ok, code, detail):
    if not ok:
        raise RecipeError(code, detail)


def absolute(value):
    need(isinstance(value, str) and value and value.isascii() and not any(c in value for c in '\r\n\x00";'),
         'UNSAFE_PATH', repr(value))
    path = Path(value)
    need(path.is_absolute() and '..' not in path.parts, 'UNSAFE_PATH', value)
    need(not path.is_symlink() and path.resolve() == path.absolute(), 'UNSAFE_PATH', value)
    return path


def raw(path, limit=JSON_LIMIT):
    path = absolute(str(path))
    try:
        with path.open('rb') as stream:
            data = stream.read(limit + 1)
    except OSError as problem:
        raise RecipeError('MISSING_INPUT', str(path)) from problem
    need(len(data) <= limit, 'BOUNDED_INPUT', str(path))
    return data


def pin(path, limit=JSON_LIMIT):
    path = absolute(str(path))
    data = raw(path, limit)
    return dict(path=path.as_posix(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def checked(row, limit=JSON_LIMIT):
    need(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'PIN_MISMATCH', 'pin fields')
    need(type(row['bytes']) is int and row['bytes'] >= 0 and isinstance(row['sha256'], str)
         and re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is not None, 'PIN_MISMATCH', row['path'])
    actual = pin(row['path'], limit)
    need((actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256']), 'PIN_MISMATCH', row['path'])
    return actual


def same_pin(left, right):
    return (isinstance(left, dict) and isinstance(right, dict)
            and {'path', 'bytes', 'sha256'} <= left.keys() and {'path', 'bytes', 'sha256'} <= right.keys()
            and isinstance(left['path'], str) and isinstance(right['path'], str)
            and Path(left['path']) == Path(right['path']) and left['bytes'] == right['bytes']
            and left['sha256'] == right['sha256'])


def document(path):
    try:
        value = json.loads(raw(path))
    except (UnicodeError, json.JSONDecodeError) as problem:
        raise RecipeError('REQUEST_SCHEMA', str(path)) from problem
    need(isinstance(value, dict), 'REQUEST_SCHEMA', str(path))
    return value


def contains_pin(value, expected):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            if same_pin({key: value[key] for key in ('path', 'bytes', 'sha256')}, expected):
                return True
        return any(contains_pin(item, expected) for item in value.values())
    return isinstance(value, list) and any(contains_pin(item, expected) for item in value)


def tokens(row):
    checked(row)
    try:
        result = [json.loads(line) for line in raw(row['path']).decode('utf-8-sig').splitlines() if line.strip()]
    except (UnicodeError, json.JSONDecodeError) as problem:
        raise RecipeError('TEMPLATE_PROFILE', 'one JSON string per argfile line') from problem
    need(result and all(isinstance(item, str) and item and not any(c in item for c in '\r\n\x00')
                        for item in result), 'TEMPLATE_PROFILE', 'argfile tokens')
    need(not any(item.startswith(('@', '-J')) for item in result), 'TEMPLATE_PROFILE', 'nested/VM argfile token')
    return result


def cp(arguments):
    need(arguments.count('-cp') == 1 or arguments.count('--class-path') == 1,
         'TEMPLATE_PROFILE', 'one classpath')
    key = '-cp' if '-cp' in arguments else '--class-path'
    entries = arguments[arguments.index(key) + 1].split(';')
    for entry in entries:
        path = absolute(entry)
        need(path.exists(), 'MISSING_INPUT', entry)
    return entries


def source(row, class_name):
    need(isinstance(row, dict), 'REQUEST_SCHEMA', 'exactly one source pin, not a TU list')
    actual = checked(row, SOURCE_LIMIT)
    need(isinstance(class_name, str) and FQN.fullmatch(class_name), 'REQUEST_SCHEMA', 'class FQN')
    path = Path(actual['path'])
    need(path.suffix == '.java' and path.stem == class_name.rsplit('.', 1)[1], 'REQUEST_SCHEMA', 'one matching Java TU')
    try:
        text = raw(path, SOURCE_LIMIT).decode('utf-8-sig')
    except UnicodeError as problem:
        raise RecipeError('REQUEST_SCHEMA', 'source UTF-8') from problem
    package = re.search(r'^\s*package\s+([\w.]+)\s*;', text, re.M)
    need(package is not None and package[1] == class_name.rsplit('.', 1)[0], 'REQUEST_SCHEMA', 'source package')
    return actual


def production_entries(request):
    entries = request.get('production_sources')
    need(isinstance(entries, list) and len(entries) == 2, 'UNSUPPORTED_PROFILE', 'exactly two ordered production TUs')
    pins, paths, names = [], set(), set()
    for entry in entries:
        need(isinstance(entry, dict) and set(entry) == {'source', 'class_name', 'source_ready'},
             'REQUEST_SCHEMA', 'production entry fields')
        selected = source(entry['source'], entry['class_name'])
        path = absolute(selected['path']).resolve()
        need(path not in paths and entry['class_name'] not in names, 'REQUEST_SCHEMA', 'duplicate production path/class')
        paths.add(path)
        names.add(entry['class_name'])
        checked(entry['source_ready'])
        need(contains_pin(document(entry['source_ready']['path']), selected), 'REQUEST_SCHEMA', 'production SourceReady must bind paired source')
        pins.append(selected)
    return pins


def produced_relative(request, name):
    for entry in request['production_sources']:
        top = entry['class_name']
        if name == top:
            return top.replace('.', '/') + '.class'
        if name.startswith(top + '.') or name.startswith(top + '$'):
            nested = name[len(top) + 1:].replace('.', '$')
            if nested:
                return top.replace('.', '/') + '$' + nested + '.class'
    return None


def successful(actual, config_pin, config, verified, actual_pin):
    need(actual.get('phase') == 'prod' and actual.get('exit_code') == 0 and type(actual.get('exit_code')) is int
         and actual.get('error') is None and actual.get('timeout') is False and actual.get('pins_unchanged') is True,
         'PRODUCTION_NOT_VERIFIED', 'successful original prod ACTUAL required')
    need(same_pin(actual.get('config', {}), config_pin) and actual.get('command') == config['phases']['prod']['command'],
         'PRODUCTION_NOT_VERIFIED', 'ACTUAL config/command')
    classes = actual.get('classes')
    need(isinstance(classes, list) and 0 < len(classes) <= 1024, 'OUTPUT_MANIFEST', 'class manifest')
    for row in classes:
        checked(row, CLASS_LIMIT)
    need(verified.get('phase') == 'prod' and same_pin(verified.get('actual', {}), actual_pin)
         and verified.get('classes') == classes, 'PRODUCTION_NOT_VERIFIED', 'VERIFIED actual/classes')
    return classes


def template_jar_pin(config, jar):
    rows = [row for row in config.get('pins', []) if isinstance(row, dict)
            and isinstance(row.get('path'), str) and Path(row['path']) == Path(jar)]
    need(rows and all(same_pin(row, rows[0]) for row in rows),
         'TEMPLATE_PROFILE', 'original standalone JUnit jar pin required')
    return checked(rows[0], CLASS_LIMIT)


def templates(request):
    rows = request.get('templates')
    keys = {'prod_config', 'prod_args', 'test_config', 'test_args', 'junit_args'}
    need(isinstance(rows, dict) and set(rows) == keys, 'TEMPLATE_PROFILE', 'five original metadata pins')
    for row in rows.values():
        checked(row)
    pc, tc = document(rows['prod_config']['path']), document(rows['test_config']['path'])
    pt, tt, jt = (tokens(rows[name]) for name in ('prod_args', 'test_args', 'junit_args'))
    need(len(pt) == 13 and pt[:7] == ['--release', '21', '-Xlint:all,-try', '-Werror', '-proc:none', '-implicit:none', '-sourcepath']
         and pt[8] == '-cp' and pt[10] == '-d' and pt[12].endswith('.java'), 'TEMPLATE_PROFILE', 'production748 profile')
    need(len(tt) == 15 and tt[:9] == ['--release', '21', '-encoding', 'UTF-8', '-proc:none', '-Xlint:all,-try', '-Werror', '-implicit:none', '-sourcepath']
         and tt[10] == '-cp' and tt[12] == '-d' and tt[14].endswith('.java'), 'TEMPLATE_PROFILE', 'tests750 profile')
    need(len(jt) >= 11 and jt[0].startswith('-Djava.io.tmpdir=')
         and jt[1:5] == ['-jar', jt[2], 'execute', '--class-path']
         and jt[6:9] == ['--disable-banner', '--details=summary', '--fail-if-no-tests']
         and jt[9].startswith('--reports-dir=')
         and all(re.fullmatch(r'--select-method=[\w.$]+#[\w$]+', item) for item in jt[10:]),
         'TEMPLATE_PROFILE', 'explicit-method JUnit750 profile')
    for conf, phase, row in ((pc, 'prod', rows['prod_args']), (tc, 'test', rows['test_args']), (tc, 'junit', rows['junit_args'])):
        spec = conf.get('phases', {}).get(phase, {})
        need(same_pin(spec.get('args', {}), row) and spec.get('timeout_seconds') == 30,
             'TEMPLATE_PROFILE', phase + ' args/timeout')
        command = spec.get('command', [])
        expected = ['C:/jdk-21/bin/java.exe', '@' + row['path']] if phase == 'junit' else ['C:/jdk-21/bin/javac.exe', *VM, '@' + row['path']]
        need(command == expected, 'TEMPLATE_PROFILE', phase + ' direct command')
    base = cp(pt)
    need(len(base) == 316 and cp(tt)[2:] == base and cp(jt)[2:] == base, 'TEMPLATE_PROFILE', 'literal316 tail')
    need(cp(tt)[0] == cp(jt)[1] and cp(tt)[1] == jt[2], 'TEMPLATE_PROFILE', '750 prefix ordering')
    template_jar_pin(tc, jt[2])
    return pc, tc, pt, tt, jt, base


def fixture_contract(request, sdk):
    fixture = request.get('fixture', {'requires_JNA': False})
    need(isinstance(fixture, dict) and type(fixture.get('requires_JNA')) is bool,
         'SDK_QUALIFICATION', 'explicit fixture metadata')
    if not fixture['requires_JNA']:
        need(set(fixture) == {'requires_JNA'} and sdk.get('fixture', fixture) == fixture,
             'SDK_QUALIFICATION', 'noJNA fixture declaration')
        return False
    need(set(fixture) == {'requires_JNA', 'basis', 'helper'} and sdk.get('fixture') == fixture,
         'SDK_QUALIFICATION', 'Native-declared JNA profile pins required')
    checked(fixture['basis'])
    checked(fixture['helper'])
    basis = document(fixture['basis']['path'])
    profile = basis.get('fixture', basis.get('fixture308', {}))
    properties = profile.get('effective_fixture_properties', {})
    need(basis.get('requires_JNA') is True and profile.get('Windows_JNA_required') is True
         and set(properties) == {'java.io.tmpdir', 'jna.tmpdir'},
         'SDK_QUALIFICATION', 'existing bounded Native JNA fixture contract')
    root = absolute(profile.get('task_root'))
    need(root.is_dir(), 'SDK_QUALIFICATION', 'existing source fixture root')
    for value in properties.values():
        path = absolute(value)
        need(path.is_dir() and path.is_relative_to(root), 'SDK_QUALIFICATION', 'source fixture temp within owned root')
    return True


def load_request(path):
    request_pin = pin(path)
    request = document(path)
    expected = {'schema', 'profile', 'output_root', 'production_sources', 'test_source', 'test_ready',
                'test_class', 'methods', 'templates', 'sdk_declaration'}
    need('sdk_declaration' in request, 'SDK_DECLARATION_REQUIRED', 'Native issuer declaration pin')
    need(set(request) in (expected, expected | {'fixture'}) and request.get('schema') == 'xar.verification-recipe-request/v2', 'REQUEST_SCHEMA', 'request fields')
    need(request.get('profile') == PROFILE, 'UNSUPPORTED_PROFILE', request.get('profile'))
    methods = request.get('methods')
    need(isinstance(methods, list) and 0 < len(methods) <= 64 and all(isinstance(m, str) and IDENTIFIER.fullmatch(m) for m in methods)
         and len(set(methods)) == len(methods), 'INVALID_SELECTOR', 'unique simple explicit method names')
    root = absolute(request['output_root'])
    need(root.drive.upper() == 'D:' and root.parent.is_dir(), 'UNSAFE_PATH', 'isolated D output with existing parent')
    prods = production_entries(request)
    test = source(request['test_source'], request['test_class'])
    checked(request['test_ready'])
    need(contains_pin(document(request['test_ready']['path']), test), 'REQUEST_SCHEMA', 'test_ready must bind selected source')
    original = templates(request)
    declaration = request.get('sdk_declaration')
    need(isinstance(declaration, dict), 'SDK_DECLARATION_REQUIRED', 'Native issuer declaration pin')
    checked(declaration)
    sdk = document(declaration['path'])
    need(sdk.get('schema') == 'xar.native-sdk-declaration/v2' and sdk.get('issuer') == '/root/native_continue'
         and isinstance(sdk.get('scope'), str) and bool(sdk['scope'].strip()), 'SDK_QUALIFICATION', 'Native declaration identity')
    declared = sdk.get('sources', {}).get('production')
    need(isinstance(declared, list) and len(declared) == 2 and all(same_pin(left, right) for left, right in zip(declared, prods))
         and same_pin(sdk.get('sources', {}).get('test', {}), test), 'SDK_QUALIFICATION', 'ordered selected source binding')
    for key in ('sdk_config', 'sdk_args', 'sdk_actual', 'sdk_verified'):
        checked(sdk.get(key, {}))
    sdk_config = document(sdk['sdk_config']['path'])
    need(same_pin(sdk_config.get('phases', {}).get('prod', {}).get('args', {}), sdk['sdk_args']), 'SDK_QUALIFICATION', 'SDK config argfile')
    need(cp(tokens(sdk['sdk_args'])) == original[5] == sdk.get('sdk_entries'), 'SDK_QUALIFICATION', 'SDK literal ordered tail')
    successful(document(sdk['sdk_actual']['path']), sdk['sdk_config'], sdk_config,
               document(sdk['sdk_verified']['path']), sdk['sdk_actual'])
    families = sdk.get('families')
    need(isinstance(families, dict) and len(families) <= 512 and isinstance(sdk.get('required_families'), dict), 'SDK_QUALIFICATION', 'named family declarations')
    need(all(produced_relative(request, name) is None for name in families),
         'SDK_QUALIFICATION', 'co-produced family cannot bind old SDK support')
    for phase in ('production', 'test'):
        required = sdk['required_families'].get(phase)
        need(isinstance(required, list) and required and len(required) <= 256 and len(set(required)) == len(required), 'SDK_QUALIFICATION', phase + ' required families')
        for name in required:
            need(isinstance(name, str) and FQN.fullmatch(name), 'SDK_QUALIFICATION', 'family FQN')
            if produced_relative(request, name) is not None:
                continue
            need(name in families, 'MISSING_FAMILY', phase + ':' + name)
            row = families[name]
            need(isinstance(row, dict) and set(row) == {'index', 'root', 'relative', 'pin'}, 'SDK_QUALIFICATION', name)
            index, relative = row['index'], row['relative']
            need(type(index) is int and 0 <= index < 316 and row['root'] == original[5][index], 'SDK_QUALIFICATION', name + ':index/root')
            need(isinstance(relative, str) and relative.endswith('.class') and not Path(relative).is_absolute()
                 and '..' not in Path(relative).parts, 'SDK_QUALIFICATION', name + ':relative')
            checked(row['pin'], CLASS_LIMIT)
            need(Path(row['pin']['path']) == Path(row['root']) / relative, 'SDK_QUALIFICATION', name + ':class pin')
            first = next((i for i, entry in enumerate(original[5]) if Path(entry).is_dir() and (Path(entry) / relative).is_file()), None)
            need(first == index, 'SDK_QUALIFICATION', name + ':first directory hit')
    fixture_contract(request, sdk)
    return request_pin, request, root, original, sdk


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    return pin(path)


def write_args(path, values):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(''.join(json.dumps(value) + '\n' for value in values))
    return pin(path)


def guard(command, argfile, values):
    # Exact return schema of Native javac_argfile_guard430; Native revalidates it.
    return dict(argfile=argfile, argfile_VM_tokens=0, direct_VM_options=command[1:3], compiler_tokens=len(values), Java_started=False)


def input_pins(request_pin, request, sdk, original):
    rows = [request_pin, *(entry['source'] for entry in request['production_sources']), request['test_source'],
            *(entry['source_ready'] for entry in request['production_sources']), request['test_ready'], request['sdk_declaration'],
            *request['templates'].values(), *(sdk[key] for key in ('sdk_config', 'sdk_args', 'sdk_actual', 'sdk_verified')),
            *(row['pin'] for row in sdk['families'].values()), template_jar_pin(original[1], original[4][2])]
    if fixture_contract(request, sdk):
        rows.extend(request['fixture'][key] for key in ('basis', 'helper'))
    # Jar bytes are immutable inputs; directory class contents are covered by named declarations.
    rows.extend(pin(entry, CLASS_LIMIT * 16) for entry in sdk['sdk_entries'] if Path(entry).is_file())
    return list({row['path']: checked(row, max(JSON_LIMIT, row['bytes'])) for row in rows}.values())


def prepare_production(request_path):
    started = time.perf_counter()
    request_pin, request, root, original, sdk = load_request(request_path)
    need(not root.exists(), 'OUTPUT_EXISTS', root)
    pins = input_pins(request_pin, request, sdk, original)
    destination = root / 'production'
    output, empty, argfile = destination / 'classes', destination / 'empty-source', destination / 'PROD.args'
    values = list(original[2])
    values[7], values[11] = empty.as_posix(), output.as_posix()
    values[12:] = [entry['source']['path'] for entry in request['production_sources']]
    root.mkdir()
    destination.mkdir()
    output.mkdir()
    empty.mkdir()
    argument_pin = write_args(argfile, values)
    command = ['C:/jdk-21/bin/javac.exe', *VM, '@' + argfile.as_posix()]
    config = dict(source_ready=request['production_sources'][0]['source_ready'], source_readies=[entry['source_ready'] for entry in request['production_sources']],
                  pins=pins + [argument_pin], methods=[], expected_class=None, reports=None,
                  qualifiedDirectAndSamePackageFamilies={name: sdk['families'][name] for name in sdk['required_families']['production'] if produced_relative(request, name) is None},
                  coherentProductionFamilies={name: produced_relative(request, name) for phase in ('production', 'test') for name in sdk['required_families'][phase] if produced_relative(request, name) is not None},
                  CP316LiteralRetained=True, source_only_compile_compatibility=True, current_runtime_source_or_loaded_parity=False,
                  phases=dict(prod=dict(command=command, args=argument_pin, guard=guard(command, argument_pin, values),
                                        sources=[entry['source'] for entry in request['production_sources']], output=output.as_posix(), timeout_seconds=30)),
                  productionTUs=2, TestRUN=0, GameGETAdoption=0)
    config_pin = write_json(destination / 'CONFIG.json', config)
    return write_json(destination / 'PREPARED-READY.json', dict(schema='xar.verification-recipe-prepared/v2', stage='production',
                      status='METADATA_PREPARED_NOT_EXECUTED', request=request_pin, config=config_pin, args=[argument_pin],
                      sources=[entry['source'] for entry in request['production_sources']], ordered_CP_sha256=hashlib.sha256(';'.join(original[5]).encode()).hexdigest(),
                      prepare_seconds=time.perf_counter() - started, Java_started=False, resource_grant=False, Native_approval=False))


def prepare_tests(production_ready_pin, actual_pin, verified_pin):
    started = time.perf_counter()
    checked(production_ready_pin)
    ready = document(production_ready_pin['path'])
    need(ready.get('schema') == 'xar.verification-recipe-prepared/v2' and ready.get('stage') == 'production', 'REQUEST_SCHEMA', 'production Prepared-READY')
    checked(ready['request'])
    request_pin, request, root, original, sdk = load_request(ready['request']['path'])
    need(Path(production_ready_pin['path']) == root / 'production' / 'PREPARED-READY.json', 'UNSAFE_PATH', 'production Ready location')
    checked(ready['config'])
    config = document(ready['config']['path'])
    for row in config['pins']:
        checked(row, max(JSON_LIMIT, row['bytes']))
    checked(actual_pin)
    checked(verified_pin)
    actual = document(actual_pin['path'])
    expected_sources = [entry['source'] for entry in request['production_sources']]
    need(type(actual.get('source_TUs')) is int and actual['source_TUs'] == 2
         and config['phases']['prod']['sources'] == expected_sources and config.get('productionTUs') == 2,
         'PRODUCTION_NOT_VERIFIED', 'one coherent two-TU production invocation required')
    classes = successful(actual, ready['config'], config, document(verified_pin['path']), actual_pin)
    output = root / 'production' / 'classes'
    found = list(output.rglob('*.class'))
    need(len(found) <= 1024 and {p.resolve() for p in found} == {absolute(row['path']).resolve() for row in classes}
         and len(classes) == len({row['path'] for row in classes}), 'OUTPUT_MANIFEST', 'exact production output leaves')
    required_outputs = {entry['class_name'].replace('.', '/') + '.class' for entry in request['production_sources']}
    required_outputs.update(relative for phase in ('production', 'test') for name in sdk['required_families'][phase]
                            if (relative := produced_relative(request, name)) is not None)
    manifest = {absolute(row['path']): row for row in classes}
    need(all(path.is_relative_to(output) for path in manifest) and all(output / relative in manifest for relative in required_outputs),
         'OUTPUT_MANIFEST', 'both top-level and required co-produced nested families')
    destination = root / 'tests'
    need(not destination.exists(), 'OUTPUT_EXISTS', destination)
    jar = original[4][2]
    jar_pin = template_jar_pin(original[1], jar)
    pins = input_pins(request_pin, request, sdk, original) + [production_ready_pin, ready['config'], actual_pin, verified_pin, jar_pin, *classes]
    requires_jna = fixture_contract(request, sdk)
    test_output, empty, reports, tmp = (destination / name for name in ('classes-test', 'empty-source', 'reports', 'tmp'))
    jna_tmp = destination / 'jna-tmp'
    properties = {'java.io.tmpdir': tmp.as_posix()}
    if requires_jna:
        properties['jna.tmpdir'] = jna_tmp.as_posix()
    test_cp = [output.as_posix(), jar, *original[5]]
    run_cp = [test_output.as_posix(), output.as_posix(), *original[5]]
    tt = list(original[3])
    tt[9], tt[11], tt[13], tt[14] = empty.as_posix(), ';'.join(test_cp), test_output.as_posix(), request['test_source']['path']
    jt = list(original[4][:10])
    jt[0], jt[5], jt[9] = '-Djava.io.tmpdir=' + tmp.as_posix(), ';'.join(run_cp), '--reports-dir=' + reports.as_posix()
    if requires_jna:
        jt.insert(1, '-Djna.tmpdir=' + jna_tmp.as_posix())
    jt.extend('--select-method=' + request['test_class'] + '#' + method for method in request['methods'])
    destination.mkdir()
    for path in (test_output, empty, reports, tmp):
        path.mkdir()
    if requires_jna:
        jna_tmp.mkdir()
    tap, jap = write_args(destination / 'TEST.args', tt), write_args(destination / 'JUNIT.args', jt)
    command = ['C:/jdk-21/bin/javac.exe', *VM, '@' + tap['path']]
    origins = {}
    for name in sdk['required_families']['test']:
        relative = produced_relative(request, name)
        if relative is not None:
            origins[name] = dict(index=0, root=output.as_posix(), relative=relative, pin=manifest[output / relative])
        else:
            row = sdk['families'][name]
            origins[name] = {**row, 'index': row['index'] + 2}
    java_command = ['C:/jdk-21/bin/java.exe', *(['-Xmx128m', '-XX:ActiveProcessorCount=1'] if requires_jna else []), '@' + jap['path']]
    test_config = dict(source_ready=request['test_ready'], pins=pins + [tap, jap], methods=request['methods'], expected_class=request['test_class'],
                       reports=reports.as_posix(), named_current_API_families=origins, only_new_selectors=True, old_methods_RUN=0, actual_prod=actual_pin,
                       phases=dict(test=dict(command=command, args=tap, guard=guard(command, tap, tt), sources=[request['test_source']], output=test_output.as_posix(), timeout_seconds=30),
                                   junit=dict(command=java_command, args=jap, timeout_seconds=30)),
                       fixture=dict(Windows_JNA_required=requires_jna, task_root=root.as_posix(), effective_fixture_properties=properties, Java_started=False),
                       classpath_base316_literal=True, CP_test=318, CP_run=318, production_compile=0)
    config_pin = write_json(destination / 'CONFIG.json', test_config)
    return write_json(destination / 'PREPARED-READY.json', dict(schema='xar.verification-recipe-prepared/v2', stage='tests', status='METADATA_PREPARED_NOT_EXECUTED',
                      request=request_pin, config=config_pin, args=[tap, jap], source=request['test_source'], actual_prod=actual_pin,
                      selected_methods=request['methods'], prepare_seconds=time.perf_counter() - started, Java_started=False, resource_grant=False, Native_approval=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='stage', required=True)
    prod = sub.add_parser('production')
    prod.add_argument('--request', required=True)
    test = sub.add_parser('tests')
    for name in ('production-ready', 'actual', 'verified'):
        test.add_argument('--' + name, required=True, help='JSON pin object, not an executable command')
    args = parser.parse_args()
    try:
        result = prepare_production(args.request) if args.stage == 'production' else prepare_tests(
            json.loads(args.production_ready), json.loads(args.actual), json.loads(args.verified))
        print(json.dumps(result))
    except RecipeError as problem:
        print(json.dumps(dict(error=problem.code, detail=problem.detail, Java_started=False)))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
