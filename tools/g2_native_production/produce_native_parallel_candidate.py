"""Source-only Root candidate; future explicit entry: python producer.py manifest.json.
Schema xar.native.parallel.production/v1. No command parser, root replacement,
ambient environment, automatic latest selection, retry or runtime credit.
Each final argv, owner tuple, job environment and private writable scope is
explicitly admitted. Root chooses 1..64 workers with current CPU, memory,
storage and aggregate reservations. First error closes dispatch; every started
direct child is waited, including timeout kill/wait results. Descendant cleanup
is never inferred. Archive/link require all actual compile verifications.
Source12 is an immutable predecessor; this file neither imports nor edits it.
"""
from __future__ import annotations
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

HEAD = 'c05f9cd00650c9a4bfe029c2dc3a6dd32b4ff98f'
ENV = ('CL', '_CL_', 'INCLUDE', 'LIB', 'LIBPATH', 'PATH', 'TMP', 'TEMP')
INCLUDE_FLAGS = ('/I', '-I', '/FI', '/external:I', '/FU', '/AI')
ROLES = {'tool', 'option', 'option_value', 'source_operand', 'input_operand', 'defaultlib', 'wholearchive', 'responsefile'}
DEADLINE = None

class UnknownAdmission(RuntimeError):
    pass

def need(ok, why):
    if not ok:
        raise UnknownAdmission(why)

def clock():
    need(DEADLINE is None or datetime.now(timezone.utc) < DEADLINE, 'build deadline')

def positive(value, why):
    need(type(value) in (int, float) and math.isfinite(value) and value > 0, why)
    return value

def json_object(pairs):
    result = {}
    for k, v in pairs:
        need(k not in result, 'duplicate JSON key: ' + k)
        result[k] = v
    return result

def json_float(value):
    result = float(value)
    need(math.isfinite(result), 'nonfinite JSON number: ' + value)
    return result

def json_constant(value):
    raise UnknownAdmission('nonfinite JSON constant: ' + value)

def load_bound(path, limit=33554432):
    p = Path(path)
    with p.open('rb') as f:
        raw = f.read(limit + 1)
    need(len(raw) <= limit, 'oversized input: ' + str(p))
    obj = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=json_object,
                     parse_float=json_float, parse_constant=json_constant)
    return obj, hashlib.sha256(raw).hexdigest()

def load(path, limit=33554432):
    return load_bound(path, limit)[0]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while b := f.read(1048576):
            clock()
            h.update(b)
    return h.hexdigest()

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def abs_path(value):
    p = Path(value)
    need(p.is_absolute(), 'absolute path: ' + str(value))
    return p.resolve()

def key(value, cwd=None):
    p = Path(value)
    if not p.is_absolute():
        need(cwd is not None, 'unanchored path')
        p = Path(cwd) / p
    return os.path.normcase(str(p.resolve()))

def inside(value, roots):
    p = abs_path(value)
    return any(p.is_relative_to(abs_path(r)) for r in roots)

def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
        f.write('\n')

def error_data(e):
    return {'error_type': type(e).__name__, 'error': str(e), 'diagnostics': getattr(e, '__notes__', [])}

def failure_receipt(path, value, original):
    try:
        write(path, value)
    except BaseException as diagnostic:
        original.add_note('Failure receipt write failed: ' + str(path) + ': ' +
                          type(diagnostic).__name__ + ': ' + str(diagnostic))

def receipt(path, status, mh):
    r = load(path, 2097152)
    need(r.get('status') == status and r.get('manifest_sha256') == mh, 'receipt/manifest: ' + str(path))
    return r

def opt(argv, flag):
    values = []
    for i, t in enumerate(argv):
        probe, wanted = (t.upper(), flag.upper()) if flag.endswith(':') else (t, flag)
        if probe == wanted:
            need(i + 1 < len(argv), 'option value: ' + flag)
            values.append(argv[i + 1])
        elif probe.startswith(wanted):
            values.append(t[len(flag):])
    need(len(values) == 1 and values[0], 'one exact option: ' + flag)
    return values[0]

def option_present(argv, flag):
    return any((t.upper().startswith(flag.upper()) if flag.endswith(':') else t.startswith(flag)) for t in argv)

def environment(j, policy):
    need(policy['old_environment_inferred'] is False and policy['msvc_x64_cxx20_verified'] is True,
         'new environment only; formal toolchain not verified')
    need(policy['effective_write_paths_verified'] is True, 'CL/_CL_ write scope not reviewed')
    settings = j['environment']
    need(isinstance(settings, dict) and all(n in settings for n in ENV), 'complete explicit job environment')
    need(len({n.casefold() for n in settings}) == len(settings), 'Windows environment names unique')
    need(all(settings[n]['state'] in ('unset', 'empty') for n in ('CL', '_CL_')), 'no implicit CL/_CL_ flags or writes')
    need(canonical_sha(settings) == policy['job_environment_sha256'][j['job_id']], 'Root job environment binding')
    need(policy['token_roles_verified'] is True and canonical_sha(j['token_roles']) ==
         policy['job_token_roles_sha256'][j['job_id']], 'Root explicit token roles binding')
    env = {}
    for n, r in settings.items():
        need(isinstance(n, str) and n and '=' not in n and '\0' not in n, 'environment name')
        state = r['state']
        need(state in ('unset', 'empty', 'value'), 'environment state')
        if state != 'unset':
            value = '' if state == 'empty' else r['value']
            need(isinstance(value, str) and '\0' not in value, 'environment value')
            env[n] = value
    need(all(env.get(n) and key(env[n]) == key(j[n.lower()]) and inside(env[n], [j['job_root']])
             for n in ('TMP', 'TEMP')), 'private admitted TMP/TEMP')
    return env

def common(j, root, policy=None):
    argv = j['argv']
    need(isinstance(argv, list) and argv and all(isinstance(t, str) and '\0' not in t for t in argv), 'final argv')
    roles = j['token_roles']
    need(isinstance(roles, list) and len(roles) == len(argv) and all(v in ROLES for v in roles)
         and roles[0] == 'tool' and roles.count('tool') == 1, 'complete explicit argv token roles')
    need(Path(argv[0]).is_file() and Path(argv[0]).is_absolute() and sha(argv[0]) == j['tool_sha256'], 'exact tool bytes')
    jr = abs_path(j['job_root'])
    need(inside(jr, [root]) and key(jr) != key(root) and not jr.exists(), 'new private job root')
    need(all(inside(j[v], [jr]) for v in ('cwd', 'output', 'tmp', 'temp')), 'private cwd/output/temp scope')
    positive(j['timeout_seconds'], 'finite timeout')
    positive(j['memory_reserve_bytes'], 'job memory reservation')
    positive(j['output_reserve_bytes'], 'job output reservation')
    for r in j['mappings']:
        i = r['argv_index']
        need(type(i) is int and 0 <= i < len(argv)
             and argv[i] == r['final'], 'original/final token mapping')
        if not isinstance(r['original'], str):
            role = r.get('policy_added_role')
            need(r['original'] is None and policy and role in ('pdb', 'deps') and
                 policy['policy_added_write_roles'].get(role) is True, 'admitted new output token only')
            field, flag = ('pdb_file', '/Fd') if role == 'pdb' else ('dependencies_file', '/sourceDependencies')
            need(argv[i] == flag + j[field] or (argv[i] == j[field] and i > 0 and argv[i - 1] == flag), 'private added output binding')
    write_argv = ['/' + t[1:] if t.startswith('-') else t for t in argv]
    for flag in ('/Fo', '/Fd', '/Fa', '/Fi', '/FR', '/Fr', '/Fp', '/OUT:', '/PDB:', '/IMPLIB:', '/ILK:', '/MAP:'):
        if option_present(write_argv, flag):
            need(inside(abs_path(opt(write_argv, flag)), [jr]), 'private writable option: ' + flag)
    need(not Path(j['output']).exists(), 'existing output; no overwrite/retry')

def admit_compile(j, root, policy, sdk):
    common(j, root, policy)
    argv, source = j['argv'], abs_path(j['source'])
    flags = policy['required_compile_flags_by_target'][j['target']]
    rules = policy['compile_flag_rules_by_target'][j['target']]
    need(isinstance(flags, list) and flags and all(isinstance(v, str) and v in argv for v in flags), 'actual required target flags')
    need(rules and any({'/std:', '-std:'}.issubset(v.get('prefixes', [])) for v in rules), 'Root explicit standard conflict policy')
    need(any({'/MD', '-MD', '/MT', '-MT'}.issubset(v['prefixes']) for v in rules), 'Root explicit runtime conflict policy')
    for rule in rules:
        prefixes, allowed, count = rule['prefixes'], rule['allowed'], rule.get('count', 1)
        need(prefixes and all(isinstance(v, str) and v for v in prefixes) and allowed and type(count) is int and count == 1, 'Root compile flag conflict rule')
        observed = [v for v in argv if any(v.lower().startswith(p.lower()) for p in prefixes)]
        need(len(observed) == count and observed[0] in allowed, 'conflicting/missing target option')
    need(inside(source, [sdk]) and source.is_file() and sha(source) == j['source_sha256'], 'selected source bytes')
    i = j['source_arg_index']
    need(type(i) is int and 0 <= i < len(argv) and argv[i] == str(source), 'source token')
    need(sum(t in ('/c', '-c') for t in argv) == 1 and all(j['token_roles'][n] == 'option' for n, t in enumerate(argv) if t in ('/c', '-c')), 'single compile-only flag')
    need(not any(t.lower().startswith(('/link', '-link', '/ld', '-ld', '/fe', '-fe', '/fm', '-fm', '/doc', '-doc', '/ifcoutput', '-ifcoutput', '/analyze:log', '-analyze:log', '/yc', '-yc', '/yu', '-yu', '-o'))
                 for t in argv), 'no implicit link or unsupported output switch')
    valued = {'/I', '-I', '/FI', '/Fo', '/Fd', '/Fa', '/Fi', '/FR', '/Fr', '/Fp', '/D', '-D', '/U', '-U', '/AI', '/FU',
              '/sourceDependencies', '/external:I', '/reference', '/headerUnit:angle', '/headerUnit:quote'}
    values = {n + 1 for n, token in enumerate(argv[:-1]) if token in valued}
    need(all(j['token_roles'][n] == 'option_value' and j['token_roles'][n - 1] == 'option' for n in values), 'real valued option roles')
    cpp = [n for n, token in enumerate(argv) if n not in values and not token.startswith(('/', '-'))
           and token.lower().endswith(('.cpp', '.cxx', '.cc', '.c++', '.c', '.ixx', '.cppm'))]
    need(cpp == [i] and [n for n, role in enumerate(j['token_roles']) if role == 'source_operand'] == [i],
         'unique genuine CPP operand, not an option value')
    need(not any(t.startswith(('/Tp', '/Tc')) for t in argv), 'explicit bare source; no attached source selector')
    need(not any(t.startswith('@') for t in argv), 'compile argv complete; no hidden rsp')
    need(key(opt(argv, '/Fo'), j['cwd']) == key(j['output']), '/Fo binding')
    need(key(opt(argv, '/Fd'), j['cwd']) == key(j['pdb_file']), 'private /Fd binding')
    need(key(opt(argv, '/sourceDependencies'), j['cwd']) == key(j['dependencies_file']), 'sourceDependencies binding')
    need(all(inside(j[v], [j['job_root']]) and not Path(j[v]).exists()
             for v in ('dependencies_file', 'pdb_file')), 'private new dependency/PDB outputs')
    mapped = {r['argv_index'] for r in j['mappings']}
    need(i in mapped and set(j['include_indices']).issubset(mapped), 'source/include mappings')
    need(all(type(n) is int and 0 <= n < len(argv) and j['token_roles'][n] == 'option' and
             any(argv[n] == flag or (argv[n].startswith(flag) and len(argv[n]) > len(flag)) for flag in INCLUDE_FLAGS)
             for n in j['include_indices']), 'explicit supported include flag roles')
    need(all(n + 1 in mapped and j['token_roles'][n + 1] == 'option_value' for n in j['include_indices']
             if argv[n] in INCLUDE_FLAGS), 'separate include path role/mapping')
    kind = j['recipe_kind']
    need(kind in ('actual_full_argv', 'derived203_new_policy', 'fresh_environment_policy'), 'recipe provenance')
    if kind != 'actual_full_argv':
        field = 'derived203_admitted_indices' if kind == 'derived203_new_policy' else 'fresh_admitted_indices'
        need(j['index'] in policy[field] and j['old_actual_recipe_claimed'] is False, 'explicit new recipe policy')
    d = j['dependencies']
    need(d['policy'] in ('exact', 'fresh_capture') and d['allowed_roots'], 'dependency policy')
    if d['policy'] == 'fresh_capture':
        need(j['index'] in policy['fresh_dependency_admitted_indices'], 'fresh dependency admission')

def dependencies(j, header, header_sha, policy, abi):
    packet = load(j['dependencies_file'])
    spec = j['dependencies']
    need(spec['required'] is True and spec['accepted_versions'] == policy['accepted_dependency_versions'] and
         packet['Version'] in spec['accepted_versions'], 'Root accepted sourceDependencies Version')
    need(spec['source_sha256'] == j['source_sha256'] and sha(j['source']) == j['source_sha256'], 'source unchanged after compile')
    need(key(spec['mailbox_header']['path']) == key(header) and spec['mailbox_header']['sha256'] == header_sha and
         sha(header) == header_sha, 'mailbox header unchanged after compile')
    expected_consumer = j['index'] in policy['known_mailbox_consumer_indices']
    need(type(spec['requires_mailbox_header']) is bool and spec['requires_mailbox_header'] == expected_consumer,
         'Root selected actual consumer requirement')
    d = packet['Data']
    need(key(d['Source'], j['cwd']) == key(j['source']), 'Data.Source')
    includes = d['Includes']
    need(isinstance(includes, list) and all(isinstance(v, str) for v in includes), 'Data.Includes')
    paths = [abs_path(v) if Path(v).is_absolute() else (Path(j['cwd']) / v).resolve() for v in includes]
    need(all(key(v) == key(header) for v in paths if v.name.casefold() == header.name.casefold()), 'mixed mailbox header definition')
    need(all(inside(v, j['dependencies']['allowed_roots']) for v in paths), 'dependency root')
    actual_keys = {key(v) for v in paths}
    for item in abi:
        name = Path(item['path']).name.casefold()
        if name in ('main_thread_query_mailbox_v1.hpp', 'ck3_12002_semantic_adapter.hpp'):
            need(all(key(v) == key(item['path']) for v in paths if v.name.casefold() == name), 'mixed mandatory ABI header')
            need(j['index'] not in item.get('known_required_owner_indices', []) or key(item['path']) in actual_keys, 'known ABI consumer missing header')
    need(not expected_consumer or key(header) in actual_keys, 'known actual consumer positively includes selected header')
    need(all(key(v) in actual_keys for v in spec.get('required_includes', [])), 'required includes')
    if j['dependencies']['policy'] == 'exact':
        expected = j['dependencies']['expected']
        need(actual_keys == {key(r['path']) for r in expected}, 'exact include set')
        need(all(sha(r['path']) == r['sha256'] for r in expected), 'include freeze bytes')
    return {'Version': packet['Version'], 'Source': d['Source'], 'Includes': includes,
            'actual_mailbox_consumer': key(header) in actual_keys, 'include_sha256': [sha(v) for v in paths]}

def expanded(j, mh):
    out, roles, rsp = [], [], {key(r['path']): r for r in j.get('responsefiles', [])}
    for t, role in zip(j['argv'][1:], j['token_roles'][1:]):
        if not t.startswith('@'):
            out.append(t)
            roles.append(role)
        else:
            need(role == 'responsefile', 'rsp token role')
            path = abs_path(t[1:])
            need(key(path) in rsp, 'undeclared rsp')
            r = rsp[key(path)]
            q = receipt(r['receipt'], 'EXACT_RESPONSEFILE_TOKENS_VERIFIED', mh)
            need(key(q['path']) == key(path) and sha(path) == q['raw_sha256'] and
                 canonical_sha(r['tokens']) == q['ordered_tokens_sha256'] and
                 canonical_sha(r['token_roles']) == q['ordered_token_roles_sha256'], 'rsp bytes/tokens/roles')
            need(all(isinstance(v, str) and not v.startswith('@') for v in r['tokens']), 'complete nonnested rsp tokens')
            need(len(r['token_roles']) == len(r['tokens']) and all(v in ROLES - {'tool', 'responsefile'}
                 for v in r['token_roles']), 'complete expanded token roles')
            out.extend(r['tokens'])
            roles.extend(r['token_roles'])
    return out, roles

def inputs(j, mh):
    tokens, roles = expanded(j, mh)
    actual = []
    bindings = {v['token_index']: v for v in j.get('defaultlib_bindings', [])}
    seen = []
    for n, (t, role) in enumerate(zip(tokens, roles)):
        if t.upper().startswith('/WHOLEARCHIVE:'):
            need(role == 'wholearchive', 'WHOLEARCHIVE role')
            actual.append(key(t[len('/WHOLEARCHIVE:'):], j['cwd']))
        elif t.upper().startswith('/DEFAULTLIB:'):
            need(role == 'defaultlib' and n in bindings, 'DEFAULTLIB explicit actual binding')
            v = bindings[n]
            need(v['token'] == t and sha(abs_path(v['path'])) == v['sha256'], 'DEFAULTLIB bound file bytes')
            actual.append(key(v['path']))
            seen.append(n)
        elif t.startswith(('/', '-')):
            need(role in ('option', 'option_value'), 'option token cannot become a file input')
        elif role == 'input_operand':
            need(t.lower().endswith(('.obj', '.lib')), 'explicit input operand')
            actual.append(key(t, j['cwd']))
        else:
            need(role in ('option', 'option_value'), 'unexpected archive/link token role')
    need(len(bindings) == len(j.get('defaultlib_bindings', [])) and set(seen) == set(bindings), 'exact DEFAULTLIB bindings')
    if seen:
        q = receipt(j['defaultlib_binding_receipt'], 'ADMITTED_EXACT_DEFAULTLIB_BINDINGS', mh)
        need(q['job_id'] == j['job_id'] and q['bindings'] == j['defaultlib_bindings'] and
             q['actual_search_binding_verified'] is True and
             q['job_environment_sha256'] == canonical_sha(j['environment']), 'Root actual DEFAULTLIB search binding')
    need(actual == [key(v) for v in j['inputs']], 'ordered archive/link inputs')
    need(key(opt(tokens, '/OUT:'), j['cwd']) == key(j['output']), '/OUT binding')
    for flag in ('/OUT:', '/PDB:', '/IMPLIB:', '/ILK:', '/MAP:'):
        if option_present(tokens, flag):
            need(inside(abs_path(opt(tokens, flag)), [j['job_root']]), 'expanded writable scope')

def selected_owners(m, mh, jobs, retained):
    r = receipt(m['selected_owner_admission'], 'ADMITTED_SELECTED_OWNER_MAPPING', mh)
    lineage, mapping = m['selected_owner_lineage'], m['selected_owner_map']
    need(lineage['native_owner_label'] == 'Native88' and
         sha(abs_path(lineage['result_path'])) == lineage['result_sha256'], 'selected actual Native88 lineage')
    need(sha(abs_path(mapping['path'])) == mapping['sha256'], 'selected Source12 mapping bytes')
    need(r['selected_owner_lineage'] == lineage and r['selected_owner_map'] == mapping and
         r['native86_indices_substituted'] is False, 'Root selected lineage/map admission')
    need(r['compile_indices'] == [j['index'] for j in jobs] and
         r['retained_indices'] == [j['index'] for j in retained], 'exact selected rebuild/retain owners')
    owners = r['owners']
    need(isinstance(owners, list) and len(owners) == 917 and all(type(v['index']) is int for v in owners), 'selected owner tuples')
    bound = {v['index']: v['owner_tuple'] for v in owners}
    need(len(bound) == 917 and set(bound) == set(range(1, 918)), 'selected all917 owner identity')
    need(all(isinstance(j['owner_tuple'], (dict, list)) and j['owner_tuple'] and
             bound[j['index']] == j['owner_tuple'] for j in jobs + retained), 'exact per-job owner tuple')
    mapping = {v['index']: v for v in r['candidate_compile_inputs']}
    need(len(mapping) == len(r['candidate_compile_inputs']) and set(mapping) == {j['index'] for j in jobs}, 'exact candidate compile bindings')
    for j in jobs:
        v = mapping[j['index']]
        need(v['target'] == j['target'] and key(v['source']) == key(j['source']) and v['source_sha256'] == j['source_sha256'] and
             v['source_mapping_rule_ref'] == j['source_mapping_rule_ref'] and
             v['original_native88_source_ref'] == j['original_native88_source_ref'], 'actual owner to candidate CPP binding')

def parallel_admission(a):
    p = a['parallel_policy']
    workers = a['max_parallel_stages']
    need(type(workers) is int and 1 <= workers <= 64 and p['max_parallel_stages'] == workers, 'Root explicit 1..64 workers')
    positive(p['aggregate_memory_reserve_bytes'], 'aggregate memory reservation')
    positive(p['aggregate_output_reserve_bytes'], 'aggregate output reservation')
    positive(p['cleanup_wait_seconds'], 'finite child cleanup wait')
    need(p['cleanup_wait_seconds'] <= 60, 'child cleanup wait bound')
    positive(p['max_observation_age_seconds'], 'finite CPU observation age')
    need(type(p['logical_processors']) is int and p['logical_processors'] > 0 and
         type(p['cpu_parallel_limit']) is int and workers <= p['cpu_parallel_limit'] <= 64, 'admitted CPU limit')
    need(p['allow_oversubscription'] is True or p['cpu_parallel_limit'] <= p['logical_processors'], 'CPU oversubscription not admitted')
    cpu_current(p)
    need(a['exclusive_output_owner_verified'] is True, 'Root exclusive output custody')
    return p

def cpu_current(p):
    observed = datetime.fromisoformat(p['observed_at_utc'])
    need(observed.tzinfo is not None and 0 <= (datetime.now(timezone.utc) - observed).total_seconds()
         <= p['max_observation_age_seconds'], 'fresh admitted CPU observation')
    need(os.cpu_count() == p['logical_processors'], 'actual CPU observation changed')

def budget(a, root, active_memory=0, active_output=0, next_job=None):
    clock()
    p = a['parallel_policy']
    cpu_current(p)
    more_memory = 0 if next_job is None else next_job['memory_reserve_bytes']
    more_output = 0 if next_job is None else next_job['output_reserve_bytes']
    need(active_memory + more_memory <= p['aggregate_memory_reserve_bytes'] and
         active_output + more_output <= p['aggregate_output_reserve_bytes'], 'aggregate in-flight reservation')
    started, used, count = time.monotonic(), 0, 0
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            clock()
            count += 1
            need(time.monotonic() - started < 10 and count <= 20000, 'output census bound')
            try:
                s = (Path(directory) / name).stat(follow_symlinks=False)
            except FileNotFoundError:
                continue
            need(not (getattr(s, 'st_file_attributes', 0) & 0x400), 'output reparse point')
            if name in names:
                used += s.st_size
    need(used + active_output + more_output + a['checkpoint_reserve_bytes'] <= a['max_output_bytes'], 'aggregate output/checkpoint reserve')
    free = {v: shutil.disk_usage(v).free for v in a['volume_free_min_bytes']}
    anchor = abs_path(root).anchor.casefold()
    need(any(abs_path(v).anchor.casefold() == anchor for v in free), 'output volume explicitly admitted')
    need(all(free[v] >= n + (active_output + more_output if abs_path(v).anchor.casefold() == anchor else 0)
             for v, n in a['volume_free_min_bytes'].items()), 'volume/system plus in-flight reserve')
    class Memory(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in ('total', 'available', 'page', 'free_page', 'virtual', 'free_virtual', 'extended')]
    mem = Memory()
    mem.length = ctypes.sizeof(mem)
    need(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)), 'memory observation')
    need(mem.available >= a['min_free_memory_bytes'] + active_memory + more_memory, 'aggregate memory plus system reserve')
    clock()
    return {'output_bytes': used, 'volume_free_bytes': free, 'free_memory_bytes': mem.available,
            'active_memory_reserve_bytes': active_memory, 'active_output_reserve_bytes': active_output,
            'next_memory_reserve_bytes': more_memory, 'next_output_reserve_bytes': more_output}

class Dispatch:
    def __init__(self):
        self.lock = threading.Lock()
        self.stopped = threading.Event()
        self.first_error = None
        self.first_job = None

    def fail_locked(self, error, job):
        if self.first_error is None:
            self.first_error, self.first_job = error, job
        elif error is not self.first_error:
            self.first_error.add_note('Secondary ' + str(job) + ': ' + type(error).__name__ + ': ' + str(error))
        self.stopped.set()

    def fail(self, error, job):
        with self.lock:
            self.fail_locked(error, job)

def prepare_job(j):
    jr = abs_path(j['job_root'])
    jr.mkdir(parents=True, exist_ok=False)
    paths = [j['cwd'], j['tmp'], j['temp'], str(Path(j['output']).parent)]
    for field in ('dependencies_file', 'pdb_file'):
        if field in j:
            paths.append(str(Path(j[field]).parent))
    for v in paths:
        Path(v).mkdir(parents=True, exist_ok=True)
    return jr / 'stage'

def stage(j, control, cap, env, cleanup_seconds):
    base = prepare_job(j)
    result = {'status': 'NOT_STARTED', 'job_id': j['job_id'], 'argv': j['argv'], 'cwd': j['cwd'],
              'shell': False, 'automatic_retry': False, 'timeout_seconds': j['timeout_seconds'],
              'capacity': cap, 'environment_source': 'Root_admitted_settings_only',
              'environment_settings': j['environment'], 'actual_environment': env,
              'process_started': False, 'pid': None, 'exit_code': None, 'exit_observed': False,
              'direct_child_reaped': False, 'descendant_cleanup_proven': False}
    write(base.with_suffix('.request.json'), result)
    process = None
    try:
        with base.with_suffix('.stdout').open('xb') as out, base.with_suffix('.stderr').open('xb') as err:
            with control.lock:
                need(not control.stopped.is_set(), 'not started after first error')
                clock()
                remaining = (DEADLINE - datetime.now(timezone.utc)).total_seconds()
                timeout = min(j['timeout_seconds'], remaining)
                positive(timeout, 'actual bounded process timeout')
                result['actual_timeout_seconds'] = timeout
                try:
                    process = subprocess.Popen(j['argv'], cwd=j['cwd'], env=env, shell=False,
                                               stdout=out, stderr=err, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                except BaseException as original:
                    control.fail_locked(original, j['job_id'])
                    raise
                result.update(process_started=True, pid=process.pid, status='RUNNING')
            try:
                code = process.wait(timeout=timeout)
                if code != 0:
                    raise UnknownAdmission('actual nonzero process exit: ' + str(code))
                need(Path(j['output']).is_file(), 'actual process exit with missing output')
            except BaseException as original:
                control.fail(original, j['job_id'])
                raise
            result.update(status='PROCESS_EXIT_OBSERVED', exit_code=code, exit_observed=True, direct_child_reaped=True)
    except BaseException as original:
        control.fail(original, j['job_id'])
        result.update(status='FAILED_OR_TIMEOUT_NO_RETRY', **error_data(original))
        cleanup_errors = []
        if process is not None:
            try:
                if process.poll() is None:
                    process.kill()
            except BaseException as e:
                cleanup_errors.append(error_data(e))
            try:
                code = process.wait(timeout=cleanup_seconds)
                result.update(exit_code=code, exit_observed=True, direct_child_reaped=True)
            except BaseException as e:
                cleanup_errors.append(error_data(e))
        result['cleanup_errors'] = cleanup_errors
        result['status'] = 'FAILED_OR_TIMEOUT_CHILD_OBSERVED' if result['direct_child_reaped'] else 'STOPPED_CHILD_STATE_UNPROVED'
        if not result['process_started']:
            result['status'] = 'NOT_STARTED_NO_RETRY'
        failure_receipt(base.with_suffix('.result.json'), result, original)
        raise
    write(base.with_suffix('.result.json'), result)
    clock()
    return base

def file_ref(path):
    return {'path': str(abs_path(path)), 'sha256': sha(path)}

def actual_stage(j, base):
    result = load(base.with_suffix('.result.json'), 2097152)
    need(result['exit_observed'] is True and result['exit_code'] == 0 and result['direct_child_reaped'] is True
         and type(result['pid']) is int and result['pid'] > 0, 'actual child exit proof')
    return {'argv': j['argv'], 'cwd': j['cwd'], 'pid': result['pid'], 'exit_code': result['exit_code'],
            'request_ref': file_ref(base.with_suffix('.request.json')), 'result_ref': file_ref(base.with_suffix('.result.json'))}

def compile_worker(j, header, header_sha, policy, context, control, cap, env, cleanup_seconds):
    try:
        base = stage(j, control, cap, env, cleanup_seconds)
        proof = dependencies(j, header, header_sha, policy, context['abi_inputs'])
        digest = sha(j['output'])
        need(all(sha(v['path']) == v['sha256'] for v in context['abi_inputs']), 'ABI inputs unchanged after compile')
        need(all(sha(v['path']) == v['sha256'] for v in context['compile_configuration_refs']), 'CMake/config inputs unchanged after compile')
        value = {'status': 'COMPILE_VERIFIED_NEW_ENVIRONMENT', 'job_id': j['job_id'], 'index': j['index'],
                 'owner_tuple': j['owner_tuple'], 'recipe_kind': j['recipe_kind'], 'dependencies': proof,
                 'object': j['output'], 'source': j['source'], 'source_sha256': j['source_sha256'], **context,
                 'actual_stage': actual_stage(j, base), 'raw_dependencies_ref': file_ref(j['dependencies_file']),
                 'object_sha256': digest, 'old_actual_recipe_claimed': j.get('old_actual_recipe_claimed')}
        write(base.with_suffix('.verified.json'), value)
        value['verified_ref'] = file_ref(base.with_suffix('.verified.json'))
        return value
    except BaseException as original:
        control.fail(original, j['job_id'])
        if Path(j['job_root']).is_dir():
            failure_receipt(Path(j['job_root']) / 'verification-error.json',
                            {'status': 'FAILED_NO_RETRY', 'job_id': j['job_id'], **error_data(original)}, original)
        raise

def compile_all(jobs, header, header_sha, policy, context, a, root, environments):
    control, active, verified, errors = Dispatch(), {}, {}, []
    next_index = 0
    p = a['parallel_policy']

    def harvest(future):
        j = active[future]
        try:
            verified[j['index']] = future.result()
        except BaseException as original:
            control.fail(original, j['job_id'])
            errors.append({'job_id': j['job_id'], **error_data(original)})
            if not future.done():
                return
        need(future.done(), 'result observation without settled future')
        del active[future]

    pool = ThreadPoolExecutor(max_workers=a['max_parallel_stages'], thread_name_prefix='native-compile')
    shutdown_observed = False
    try:
        try:
            while next_index < len(jobs) or active:
                for future in [v for v in active if v.done()]:
                    harvest(future)
                if control.stopped.is_set() and not active:
                    break
                clock()
                if not control.stopped.is_set() and next_index < len(jobs) and len(active) < a['max_parallel_stages']:
                    j = jobs[next_index]
                    memory = sum(v['memory_reserve_bytes'] for v in active.values())
                    output = sum(v['output_reserve_bytes'] for v in active.values())
                    fits = (memory + j['memory_reserve_bytes'] <= p['aggregate_memory_reserve_bytes'] and
                            output + j['output_reserve_bytes'] <= p['aggregate_output_reserve_bytes'])
                    if fits:
                        cap = budget(a, root, memory, output, j)
                        with control.lock:
                            if not control.stopped.is_set():
                                future = pool.submit(compile_worker, j, header, header_sha, policy, context, control, cap,
                                                     environments[j['job_id']], p['cleanup_wait_seconds'])
                                active[future] = j
                                next_index += 1
                                continue
                    elif not active:
                        raise UnknownAdmission('job cannot fit aggregate admission')
                if active:
                    wait(tuple(active), timeout=0.2, return_when=FIRST_COMPLETED)
        except BaseException as original:
            control.fail(original, 'scheduler')
            errors.append({'job_id': 'scheduler', **error_data(original)})
    finally:
        try:
            # No Future.cancel and no pretend cancellation: every submitted worker finishes.
            for future in tuple(active):
                harvest(future)
        except BaseException as original:
            control.fail(original, 'harvest')
        try:
            pool.shutdown(wait=True, cancel_futures=False)
            shutdown_observed = True
        except BaseException as original:
            control.fail(original, 'shutdown')
        try:
            for future in tuple(active):
                if future.done():
                    harvest(future)
        except BaseException as original:
            control.fail(original, 'post-shutdown observation')
    summary = {'submitted_job_ids': [j['job_id'] for j in jobs[:next_index]],
               'undispatched_job_ids': [j['job_id'] for j in jobs[next_index:]],
               'verified_indices': sorted(verified), 'errors': errors, 'all_submitted_futures_settled': not active,
               'unsettled_job_ids': [j['job_id'] for j in active.values()], 'shutdown_wait_observed': shutdown_observed,
               'automatic_retry': False, 'first_error_job': control.first_job, 'descendant_cleanup_proven': False}
    if control.first_error is not None:
        control.first_error.scheduler_summary = summary
        failure_receipt(root / 'COMPILE-SCHEDULER.json', dict(status='STOPPED_OR_UNKNOWN', **summary), control.first_error)
        raise control.first_error
    need(len(verified) == len(jobs), 'all compile jobs actual verified')
    write(root / 'COMPILE-SCHEDULER.json', dict(status='ALL_COMPILES_ACTUAL_VERIFIED', **summary))
    return verified

def source_admission(m, mh, head):
    f, digest = load_bound(m['sdk_freeze_receipt'], 2097152)
    sdk = abs_path(f['source_root'])
    need(f['status'] == 'FROZEN_SOURCE_INPUT' and f['source_head'] == head and f['tree_verified'] is True,
         'complete immutable source freeze')
    need(f['contract'] == 'Root_normalized_source_qualification/v1', 'normalized qualification, not raw SDK schema')
    actual = f['actual_freeze_evidence']
    need(sha(abs_path(actual['path'])) == actual['sha256'] and actual['exit_code'] == 0 and
         actual['complete'] is True and actual['all5_verified'] is True and len(actual['all5_evidence_refs']) == 5 and
         all(isinstance(v, str) and v for v in actual['all5_evidence_refs']), 'actual freeze exit/complete/all5 evidence')
    header = sdk / 'ck3_autonomous_player/native_bridge/include/xar_bridge/main_thread_query_mailbox_v1.hpp'
    need(sha(header) == f['mailbox_header_sha256'], 'selected mailbox header bytes')
    if head == HEAD:
        need(f['sdk_name'] == 'SDK90' and sdk.name.casefold() == 'ck3-sdk90', 'default SDK90 freeze')
    else:
        selected = receipt(m['RootExplicitSelection'], 'ADMITTED_EXPLICIT_SOURCE_SELECTION', mh)
        a = receipt(m['source_admission'], 'ADMITTED_SOURCE_INPUT', mh)
        need(selected['automatic_latest'] is False and selected['source_head'] == head and
             selected['sdk_name'] == f['sdk_name'] and key(selected['source_root']) == key(sdk) and
             selected['sdk_freeze_sha256'] == digest, 'explicit selected head/root/freeze')
        need(a['scope'] == 'source-input' and a['source_head'] == head and
             key(a['approved_source_root']) == key(sdk) and a['sdk_freeze_sha256'] == digest and
             a['max_input_bytes'] > 0, 'separate selected source admission')
        review = datetime.fromisoformat(a['review_at_utc'])
        need(review.tzinfo is not None and datetime.now(timezone.utc) < review, 'source admission expired')
    return sdk, header, f['mailbox_header_sha256'], digest, f

def private_scopes(stages):
    roots = [abs_path(j['job_root']) for j in stages]
    need(len({key(v) for v in roots}) == len(roots), 'unique job roots')
    need(all(not left.is_relative_to(right) and not right.is_relative_to(left)
             for i, left in enumerate(roots) for right in roots[i + 1:]), 'job roots never overlap')
    scopes = [j[v] for j in stages for v in ('cwd', 'tmp', 'temp')]
    need(len({key(v) for v in scopes}) == len(scopes), 'private cwd/TMP/TEMP')
    outputs = [j['output'] for j in stages if j.get('kind') != 'archive_inspection']
    outputs += [j[v] for j in stages for v in ('dependencies_file', 'pdb_file') if v in j]
    outputs += [str(Path(j['job_root']) / ('stage' + suffix)) for j in stages
                for suffix in ('.request.json', '.stdout', '.stderr', '.result.json', '.verified.json')]
    need(len({key(v) for v in outputs}) == len(outputs), 'unique object/dependency/PDB/result outputs')
    need(all(not Path(v).exists() for v in outputs), 'new outputs only')

def admit_inspection(archive, root):
    j = archive['inspection_job']
    common(j, root)
    need(j['kind'] == 'archive_inspection' and j['archive_job_id'] == archive['job_id'] and
         j['expected_member_indices'] == archive['member_indices'], 'archive inspection owner binding')
    need(key(j['argv'][0]) == key(archive['argv'][0]) and j['tool_sha256'] == archive['tool_sha256'], 'same Root selected library tool')
    need(len(j['argv']) == 4 and j['argv'][1].upper() == '/NOLOGO' and j['argv'][2].upper() == '/LIST' and
         key(j['argv'][3]) == key(archive['output']) and j['token_roles'] == ['tool', 'option', 'option', 'input_operand'], 'explicit bounded /NOLOGO /LIST')
    need(j['inputs'] == [archive['output']] and key(j['output']) == key(Path(j['job_root']) / 'stage.stdout'), 'inspection raw stdout output')
    need(isinstance(j['stdout_encoding'], str) and j['stdout_encoding'], 'Root explicit listing encoding')

def inspect_archive(archive, objects, control, a, root, environments):
    j = archive['inspection_job']
    base = stage(j, control, budget(a, root, next_job=j), environments[j['job_id']], a['parallel_policy']['cleanup_wait_seconds'])
    names = j['expected_member_basenames']
    expected = archive['member_indices']
    need(names == [Path(objects[i]).name for i in expected], 'expected unique member basename mapping')
    lookup = {Path(objects[i]).name.casefold(): i for i in expected}
    need(len(lookup) == len(expected), 'unique archive member basenames')
    lines = base.with_suffix('.stdout').read_text(encoding=j['stdout_encoding'], errors='strict').splitlines()
    actual = []
    for line in lines:
        value = line.strip()
        if not value:
            continue
        name = Path(value).name.casefold()
        need(name in lookup, 'unknown actual /LIST member or banner: ' + value)
        actual.append({'actual_member': value, 'index': lookup[name], 'object': objects[lookup[name]]})
    need([v['index'] for v in actual] == expected, 'actual ordered archive member coverage')
    result = {'archive_job_id': archive['job_id'], 'library': file_ref(archive['output']), 'ordered_members': actual,
              'actual_inspection': actual_stage(j, base), 'stdout_ref': file_ref(base.with_suffix('.stdout')),
              'stderr_ref': file_ref(base.with_suffix('.stderr'))}
    write(base.with_suffix('.verified.json'), result)
    result['verified_ref'] = file_ref(base.with_suffix('.verified.json'))
    return result

def retained_actual(r, qualification):
    e = r['actual_evidence']
    need(qualification['actual_evidence'] == e, 'retained actual evidence admitted')
    for name in ('command', 'lineage', 'dependency'):
        row = e[name]
        need(row['index'] == r['index'] and row['owner_tuple'] == r['owner_tuple'], 'retained actual owner row')
    command, lineage = e['command'], e['lineage']
    need(command['exit_code'] == 0 and type(command['pid']) is int and command['pid'] > 0 and
         command['argv'] and command['source_head'] == lineage['source_head'], 'retained actual compile exit/provenance')
    need(key(lineage['object']) == key(r['object']) and lineage['object_sha256'] == r['sha256'] and
         lineage['source_head'] and lineage['sdk_source_root'] and lineage['header_head'], 'retained original source/header identity')
    need(sha(lineage['source']) == lineage['source_sha256'], 'retained source original bytes')
    for ref in e['raw_refs']:
        need(sha(abs_path(ref['path'])) == ref['sha256'], 'retained original evidence bytes')
    need(e['raw_refs'] and e['candidate_compatibility_ref'] == r['qualification_receipt'], 'retained candidate compatibility receipt')
    return e

def actual_packets(root, m, context, jobs, retained, verified, retained_evidence, archives, link_actual, link_inputs):
    rows = {name: {} for name in ('command', 'lineage', 'dependency')}
    for j in jobs:
        v = verified[j['index']]
        common_row = {'index': j['index'], 'target': j['target'], 'owner_tuple': j['owner_tuple'], 'source_head': v['source_head'],
                      'sdk_source_root': v['sdk_source_root'], 'header_head': v['header_head'], 'header_bytes': v['abi_inputs'],
                      'verified_ref': v['verified_ref']}
        rows['command'][j['index']] = dict(common_row, **v['actual_stage'])
        rows['lineage'][j['index']] = dict(common_row, object=v['object'], object_sha256=v['object_sha256'],
                                        source=v['source'], source_sha256=v['source_sha256'], raw_dependencies_ref=v['raw_dependencies_ref'])
        rows['dependency'][j['index']] = dict(common_row, **v['dependencies'], raw_dependencies_ref=v['raw_dependencies_ref'])
    for r in retained:
        for name in rows:
            rows[name][r['index']] = retained_evidence[r['index']][name]
    need(all(set(v) == set(range(1, 918)) for v in rows.values()), 'whole917 actual packet owner closure')
    refs = {}
    inventory = [{'index': j['index'], 'owner_tuple': j['owner_tuple'], 'selected_baseline_ref': m['selected_owner_lineage'],
                  'mapping_ref': m['selected_owner_map']} for j in sorted(jobs + retained, key=lambda v: v['index'])]
    packets = {'ACTUAL-OWNER-INVENTORY.json': {'items': inventory},
               'ACTUAL-COMPILE-COMMANDS.json': {'rows': [rows['command'][i] for i in range(1, 918)]},
               'ACTUAL-OBJECT-LINEAGE.json': {'objects': [rows['lineage'][i] for i in range(1, 918)]},
               'ACTUAL-DEPENDENCY-VERIFICATION.json': {'rows': [rows['dependency'][i] for i in range(1, 918)]},
               'ACTUAL-ARCHIVE-MEMBERS.json': {'archives': archives}, 'ACTUAL-LINK-INPUTS.json': link_inputs,
               'ACTUAL-LINK-RESULT.json': link_actual}
    for name, body in packets.items():
        write(root / name, {'source_head': context['source_head'], 'evidence_kind': 'actual_production', **body})
        refs[name] = file_ref(root / name)
    need(sha(m['sdk_freeze_receipt']) == context['sdk_freeze_sha256'], 'source qualification unchanged')
    refs['source_freeze'] = {'path': str(abs_path(m['sdk_freeze_receipt'])), 'sha256': context['sdk_freeze_sha256']}
    fresh = m['mode'] == 'rebuild917' and not retained and len(verified) == 917
    consumers = {v['path']: [i for i, row in rows['dependency'].items() if key(v['path']) in {key(p, rows['command'][i]['cwd']) for p in row['Includes']}]
                 for v in context['abi_inputs'] if Path(v['path']).name.casefold() in ('main_thread_query_mailbox_v1.hpp', 'ck3_12002_semantic_adapter.hpp')}
    need(not fresh or (len(consumers) == 2 and all(consumers.values())), 'each mandatory ABI header needs actual consumer')
    need(not fresh or all(v['source_head'] == context['source_head'] and key(v['sdk_source_root']) == key(context['sdk_source_root'])
                         for v in rows['lineage'].values()), 'fresh whole declared source identity')
    canonical = {'schema': 'xar.native.production.actual/v1', **context, 'objects': packets['ACTUAL-OBJECT-LINEAGE.json']['objects'],
                 'all_cpp_at_new_head': fresh, 'all_cpp_compiled_at_new_head': fresh,
                 'all_cpp_compiled_at_declared_source_head': fresh, 'candidate_header_compatibility_verified': True,
                 'actual_packets': refs, 'actual_header_consumer_indices': consumers, 'runtime_credit': False}
    write(root / 'NATIVE-CANONICAL.json', canonical)
    refs['native_canonical'] = file_ref(root / 'NATIVE-CANONICAL.json')
    return refs, fresh

def run(path):
    global DEADLINE
    need(os.name == 'nt', 'Windows production environment')
    m, mh = load_bound(path)
    head = m.get('source_head', HEAD)
    need(m['schema'] == 'xar.native.parallel.production/v1' and isinstance(head, str) and
         len(head) == 40 and all(c in '0123456789abcdef' for c in head), 'manifest pin/schema')
    sdk, header, header_sha, freeze_hash, frozen = source_admission(m, mh, head)
    abi = m['abi_inputs']
    need(abi and frozen['abi_inputs'] == abi and all(inside(v['path'], [sdk]) and sha(v['path']) == v['sha256'] for v in abi), 'frozen changed header/ABI inputs')
    for name in ('main_thread_query_mailbox_v1.hpp', 'ck3_12002_semantic_adapter.hpp'):
        exact = sdk / ('ck3_autonomous_player/native_bridge/include/xar_bridge/' + name)
        need(sum(key(v['path']) == key(exact) for v in abi) == 1, 'mandatory exact ABI header')
    context = {'source_head': head, 'sdk_source_root': str(sdk), 'header_head': head, 'abi_inputs': abi, 'sdk_freeze_sha256': freeze_hash}
    a = receipt(m['build_admission'], 'ADMITTED', mh)
    need(a['scope'] == 'native-production' and a['source_head'] == head and a['sdk_freeze_sha256'] == freeze_hash,
         'independent production admission; no sourceprep budget/expiry extension')
    DEADLINE = datetime.fromisoformat(a['deadline_utc'])
    need(DEADLINE.tzinfo is not None, 'timezone-aware build deadline')
    clock()
    root = abs_path(m['output_root'])
    render = abs_path(m['render_output_root'])
    need(not root.is_relative_to(render) and not render.is_relative_to(root) and inside(path, [render]), 'separate metadata/build roots')
    for name in ('sdk_freeze_receipt', 'build_admission', 'environment_policy', 'archive_link_policy', 'selected_owner_admission'):
        need(inside(m[name], [render]), 'Root final receipt metadata scope: ' + name)
    need(key(root) == key(a['approved_output_root']) and not root.exists(), 'fresh admitted output root')
    for field in ('max_output_bytes', 'checkpoint_reserve_bytes', 'min_free_memory_bytes'):
        positive(a[field], 'finite reservation: ' + field)
    need(a['volume_free_min_bytes'], 'machine-specific volume/system reservations')
    for n in a['volume_free_min_bytes'].values():
        positive(n, 'finite volume floor')
    pp = parallel_admission(a)
    policy = receipt(m['environment_policy'], 'ADMITTED_NEW_ENVIRONMENT', mh)
    need(policy['source_head'] == head and policy['sdk_freeze_sha256'] == freeze_hash, 'environment/freeze')
    refs = policy['compile_configuration_refs']
    need(isinstance(refs, list) and refs and any(v['kind'] == 'cmake' and Path(v['path']).name == 'CMakeLists.txt' and inside(v['path'], [sdk]) for v in refs)
         and any(v['kind'] == 'config' for v in refs), 'actual selected CMake/config references')
    need(all(sha(abs_path(v['path'])) == v['sha256'] for v in refs), 'actual CMake/config input bytes')
    context['compile_configuration_refs'] = refs
    need(isinstance(policy['accepted_dependency_versions'], list) and policy['accepted_dependency_versions'], 'Root supported dependency versions')
    closure = receipt(m['archive_link_policy'], 'ADMITTED_EXACT_ARCHIVE_LINK_CLOSURE', mh)
    need(closure['source_head'] == head and closure['selected_inputs_complete'] is True, 'archive/link closure')
    jobs, retained = m['compile_jobs'], m['retained_objects']
    need((m['mode'] == 'rebuild426_retain491' and len(jobs) == 426 and len(retained) == 491) or
         (m['mode'] == 'rebuild917' and len(jobs) == 917 and not retained), 'owner mode')
    ids = [j['index'] for j in jobs + retained]
    for v in abi:
        known = v.get('known_required_owner_indices', [])
        need(all(type(i) is int for i in known) and len(set(known)) == len(known) and set(known).issubset({j['index'] for j in jobs}), 'real ABI required owners')
    need(all(type(i) is int for i in ids) and len(set(ids)) == 917 and set(ids) == set(range(1, 918)), 'all917 exactly once')
    selected_owners(m, mh, jobs, retained)
    owner_admission = receipt(m['selected_owner_admission'], 'ADMITTED_SELECTED_OWNER_MAPPING', mh)
    need(owner_admission['known_mailbox_consumer_indices'] == policy['known_mailbox_consumer_indices'], 'selected actual consumer list')
    known = policy['known_mailbox_consumer_indices']
    need(all(type(i) is int for i in known) and len(set(known)) == len(known) and set(known).issubset({j['index'] for j in jobs}), 'affected consumers must compile')
    need(m['mode'] != 'rebuild917' or all(j['dependencies']['policy'] == 'fresh_capture' for j in jobs), 'all917 fresh dependency outputs')
    stages = jobs + m['archives'] + [j['inspection_job'] for j in m['archives']] + [m['link']]
    job_ids = [j['job_id'] for j in stages]
    need(all(isinstance(v, str) and v for v in job_ids) and len(set(job_ids)) == len(job_ids), 'unique explicit job IDs')
    private_scopes(stages)
    objects, hashes, environments, retained_evidence = {}, {}, {}, {}
    for r in retained:
        q = receipt(r['qualification_receipt'], 'ADMITTED_RETAIN_FOR_THIS_BUILD', mh)
        need(q['candidate_source_head'] == head and key(q['object']) == key(r['object']) and
             q['object_sha256'] == r['sha256'] and sha(r['object']) == r['sha256'], 'retain identity')
        need(all(q.get(k) is True for k in ('complete_recipe_and_environment', 'actual_dependencies_verified',
             'candidate_header_compatibility_verified', 'selected_archive_link_ownership_verified')) and
             q['automatic_no_header_reuse'] is False, 'complete retain qualification')
        objects[r['index']], hashes[key(r['object'])] = r['object'], r['sha256']
        retained_evidence[r['index']] = retained_actual(r, q)
    for j in jobs:
        admit_compile(j, root, policy, sdk)
        objects[j['index']] = j['output']
    need(len({Path(v).name.casefold() for v in objects.values()}) == 917, 'whole917 genuinely unique object basenames')
    consumed = []
    for j in m['archives']:
        need(j['kind'] == 'archive' and j['inputs'] == [objects[i] for i in j['member_indices']], 'exact archive members')
        consumed.extend(j['member_indices'])
    link = m['link']
    need(link['kind'] == 'link', 'selected link stage')
    consumed.extend(link['direct_object_indices'])
    need(len(consumed) == 917 and set(consumed) == set(range(1, 918)), 'archive/direct owner coverage')
    need(all(objects[i] in link['inputs'] for i in link['direct_object_indices']) and
         all(j['output'] in link['inputs'] for j in m['archives']), 'selected objects/archives')
    for j in m['archives'] + [link]:
        common(j, root)
        inputs(j, mh)
    for j in m['archives']:
        admit_inspection(j, root)
    for j in stages:
        environments[j['job_id']] = environment(j, policy)
        need(j['memory_reserve_bytes'] <= pp['aggregate_memory_reserve_bytes'] and
             j['output_reserve_bytes'] <= pp['aggregate_output_reserve_bytes'], 'each stage fits aggregate policy')
    budget(a, root)
    root.mkdir()
    write(root / 'MANIFEST-REF.json', {'manifest': str(abs_path(path)), 'sha256': mh, 'source_head': head,
          'max_parallel_stages': a['max_parallel_stages'], 'sourceprep_authorization_reused': False})
    verified, archive_actual, link_actual, link_inputs, settled = {}, [], None, None, None
    try:
        verified = compile_all(jobs, header, header_sha, policy, context, a, root, environments)
        settled = True
        need(set(verified) == {j['index'] for j in jobs}, 'ALL actual verified compile owners before archive/link')
        for j in jobs:
            hashes[key(j['output'])] = verified[j['index']]['object_sha256']
        control = Dispatch()
        for j in m['archives'] + [link]:
            inputs(j, mh)
            expected = {key(r['path']): r['sha256'] for r in j['immutable_inputs']}
            for v in j['inputs']:
                need(Path(v).is_file() and key(v) in hashes.keys() | expected.keys() and
                     sha(v) == (hashes[key(v)] if key(v) in hashes else expected[key(v)]), 'selected input bytes')
            cap = budget(a, root, next_job=j)
            selected_inputs = [{'path': str(abs_path(v)), 'sha256': sha(v)} for v in j['inputs']]
            base = stage(j, control, cap, environments[j['job_id']], pp['cleanup_wait_seconds'])
            hashes[key(j['output'])] = sha(j['output'])
            actual = actual_stage(j, base)
            value = {'status': 'STAGE_VERIFIED', 'job_id': j['job_id'], 'actual_stage': actual,
                     'output_ref': file_ref(j['output']), 'ordered_inputs': selected_inputs}
            if j['kind'] == 'archive':
                value['actual_members'] = inspect_archive(j, objects, control, a, root, environments)
                archive_actual.append(value)
            else:
                tokens, roles = expanded(j, mh)
                link_inputs = {'actual_stage': actual, 'expanded_tokens': tokens, 'token_roles': roles, 'ordered_inputs': selected_inputs}
                link_actual = dict(value, dll_path=j['output'], dll_sha256=hashes[key(j['output'])])
            write(base.with_suffix('.verified.json'), value)
        need(sha(path) == mh, 'manifest original bytes unchanged')
        packet_refs, fresh = actual_packets(root, m, context, jobs, retained, verified, retained_evidence, archive_actual, link_actual, link_inputs)
        budget(a, root)
        write(root / 'RESULT.json', {'status': 'BUILD_OUTPUTS_VERIFIED_NO_RUNTIME_CREDIT', 'manifest_sha256': mh,
              'source_head': head, 'owners': 917, 'mode': m['mode'], 'actual_compile_verified': len(verified),
              'actual_new_dependency_outputs': len(verified),
              'actual_packets': packet_refs, 'all_cpp_at_new_head': fresh, 'all_cpp_compiled_at_declared_source_head': fresh,
              'individually_qualified_retained': len(retained), 'Game_or_SDK_started': False, 'automatic_retry': False})
    except BaseException as original:
        scheduler = getattr(original, 'scheduler_summary', {})
        failure_receipt(root / 'RESULT.json', {'status': 'STOPPED_OR_UNKNOWN_NO_RETRY', **error_data(original),
              'manifest_sha256': mh, 'original_stage_files_retained': True, 'archive_link_continuation': False,
              'all_submitted_futures_settled_before_return': scheduler.get('all_submitted_futures_settled', settled),
              'unsettled_job_ids': scheduler.get('unsettled_job_ids'), 'descendant_cleanup_proven': False}, original)
        raise

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    args = parser.parse_args()
    try:
        run(args.manifest)
    except BaseException as original:
        print(json.dumps({'status': 'STOPPED_OR_UNKNOWN_NO_RETRY', **error_data(original), 'automatic_retry': False}, allow_nan=False))
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
