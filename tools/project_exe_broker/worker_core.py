"""Data-only protected broker core. No repository import, subprocess, Git or shell.

Native handles/ACL/publication and sealed WMI factory are supplied only by the fixed
protected bootstrap. The authorized owner/caller is the producer trust boundary.
"""
from __future__ import annotations

import base64
from contextlib import ExitStack
import hashlib
import json
import ntpath
import re
import struct
import uuid

POLICY_SCHEMA = 'xar.project-exe-broker.policy.v1'
REQUEST_SCHEMA = 'xar.project-exe-broker.request.v1'
RECEIPT_SCHEMA = 'xar.project-exe-broker.receipt.v1'
MANIFEST_SCHEMA = 'xar.project-exe-exclusions.v1'
SYSTEM_SID = 'S-1-5-18'
SETTINGS = ('ExclusionPath', 'ExclusionExtension', 'ExclusionProcess')
REQUEST_KEYS = {'schema', 'request_id', 'installation_id', 'expected_policy_sha256',
                'producer_kind', 'manifest_b64', 'manifest_sha256'}
POLICY_KEYS = {'broker_schema', 'installation_id', 'owner_sid', 'repo_root', 'repo_common_dir',
               'allowed_external_source_roots', 'allowed_build_roots', 'forbidden_roots',
               'inbox_dir', 'frozen_dir', 'receipts_dir', 'runtime_root', 'runtime_manifest_sha256',
               'max_request_bytes', 'max_files', 'max_requests_per_run', 'request_budget_seconds', 'run_budget_seconds'}
KINDS = ('cmake-file-api-v2', 'msvc-explicit-command-v1')
FILE_LIMIT = 256 * 1024 * 1024
SOURCE_LIMIT = 16 * 1024 * 1024
META_LIMIT = 4 * 1024 * 1024
BLOCKED_NAMES = {'python.exe', 'pythonw.exe', 'cmake.exe', 'cl.exe', 'link.exe',
                 'steam.exe', 'steamservice.exe', 'ck3.exe', 'conhost.exe', 'consent.exe',
                 'cmd.exe', 'power' + 'shell.exe', 'pw' + 'sh.exe', 'msbuild.exe'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode_json(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def strict_json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('JSON float/nonfinite value is not supported')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_float=reject, parse_constant=reject)


def exact_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + ' keys are not the exact known schema')


def hex_sha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Lowercase SHA256 required')
    return value


def canonical_uuid(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ValueError('Canonical lowercase UUID required')
    return value


def absolute(path):
    if not isinstance(path, str) or not path or any(c in path for c in ('\x00', '*', '?', '%')):
        raise ValueError('Explicit local absolute path required')
    path = path.replace('/', '\\')
    drive, tail = ntpath.splitdrive(path)
    if not re.fullmatch('[A-Za-z]:', drive) or not tail.startswith('\\') or ':' in tail:
        raise ValueError('UNC/device/ADS/relative paths are forbidden')
    return ntpath.normpath(path)


def key(path):
    return ntpath.normcase(absolute(path))


def within(path, root):
    path, root = key(path), key(root)
    return path == root or path.startswith(root.rstrip('\\') + '\\')


def joined(root, operand):
    if not isinstance(operand, str) or '\x00' in operand or any(c in operand for c in ('*', '?', '%')):
        raise ValueError('Invalid producer path operand')
    return absolute(operand if ntpath.isabs(operand) else ntpath.join(root, operand))


def parse_policy(raw):
    policy = strict_json(raw)
    exact_keys(policy, POLICY_KEYS, 'Policy')
    if policy['broker_schema'] != POLICY_SCHEMA:
        raise ValueError('Unknown policy schema')
    canonical_uuid(policy['installation_id'])
    if not isinstance(policy['owner_sid'], str) or not re.fullmatch(r'S-1-5-21-\d+-\d+-\d+-\d+', policy['owner_sid']):
        raise ValueError('Actual local owner SID required')
    hex_sha(policy['runtime_manifest_sha256'])
    for name in ('repo_root', 'repo_common_dir', 'inbox_dir', 'frozen_dir', 'receipts_dir', 'runtime_root'):
        absolute(policy[name])
    if key(policy['repo_common_dir']) != key(ntpath.join(policy['repo_root'], '.git')):
        raise ValueError('Main common Git directory must be the bound repository .git')
    for name in ('allowed_external_source_roots', 'allowed_build_roots', 'forbidden_roots'):
        values = policy[name]
        if not isinstance(values, list) or not values or len(values) > 32:
            raise ValueError('Bounded nonempty policy root list required')
        for value in values:
            absolute(value)
    for name in ('inbox_dir', 'frozen_dir', 'receipts_dir'):
        if not within(policy[name], policy['runtime_root']):
            raise ValueError('Fixed broker data directories must remain in protected installation')
    bounds = {'max_request_bytes': (1024, 4 * 1024 * 1024), 'max_files': (1, 1024),
              'max_requests_per_run': (1, 16), 'request_budget_seconds': (1, 120), 'run_budget_seconds': (1, 600)}
    for name, (low, high) in bounds.items():
        if type(policy[name]) is not int or not low <= policy[name] <= high:
            raise ValueError('Policy limit is not an allowed finite integer')
    return policy


class Claim:
    def __init__(self, policy, safety, deadline):
        self.policy, self.safety, self.deadline = policy, safety, deadline
        self.stack = ExitStack()
        self.leases = {}
        self.input_pins = []

    def close(self):
        self.stack.close()

    def budget(self):
        if self.safety.clock() >= self.deadline:
            raise TimeoutError('Request deadline reached; no new Add')

    def lease(self, path, *, owner=None, directory=False):
        self.budget()
        path = absolute(path)
        identity = (key(path), directory)
        if identity not in self.leases:
            factory = self.safety.lock_dir(path) if directory else self.safety.lock_file(path, owner_sid=owner)
            held = self.stack.enter_context(factory)
            if key(held.path) != key(path):
                raise ValueError('Handle final path differs from requested path')
            if not held.file_id:
                raise ValueError('Native stable file identity is missing')
            if owner is not None:
                if held.owner_sid != owner or getattr(held, 'owner_write_scope_verified', None) is not True:
                    raise PermissionError('Request owner/actual exclusive ordinary-writer ACL is unverified')
            self.leases[identity] = held
        held = self.leases[identity]
        held.revalidate()
        return held

    def read(self, path, limit=META_LIMIT, expected=None):
        held = self.lease(path)
        raw = held.read_bytes(limit)
        if not isinstance(raw, bytes) or len(raw) > limit:
            raise ValueError('Native locked read exceeded bound')
        held.revalidate()
        record = {'path': absolute(path), 'size': len(raw), 'sha256': sha(raw)}
        if expected is not None and (record['size'], record['sha256']) != (expected['size'], expected['sha256']):
            raise ValueError('Current locked file bytes differ from declared producer pin')
        self.input_pins.append(record)
        return raw

    def json_pin(self, proof):
        exact_keys(proof, {'path', 'sha256'}, 'Metadata pin')
        hex_sha(proof['sha256'])
        raw = self.read(proof['path'])
        if sha(raw) != proof['sha256']:
            raise ValueError('Producer metadata SHA mismatch')
        return strict_json(raw)

    def revalidate_all(self):
        self.budget()
        for held in self.leases.values():
            held.revalidate()
        self.budget()

    def scope(self, path, *, source=False):
        path = absolute(path)
        if any(within(path, root) for root in self.policy['forbidden_roots']) or within(path, self.policy['runtime_root']):
            raise ValueError('System/ProgramFiles/interpreter/broker scope is forbidden')
        if 'compilerid' in key(path) or ntpath.basename(path).casefold() in BLOCKED_NAMES:
            raise ValueError('CompilerId or third-party/system tool is forbidden')
        if not source and not any(within(path, root) for root in self.policy['allowed_build_roots']):
            raise ValueError('Build/output is outside configured project build roots')
        return path

    def bind_repo(self, repo):
        repo = self.scope(repo, source=True)
        git_entry = ntpath.join(repo, '.git')
        common = absolute(self.policy['repo_common_dir'])
        self.lease(common, directory=True)
        if key(repo) == key(self.policy['repo_root']):
            if not self.safety.is_dir(git_entry):
                raise ValueError('Main .git is not its bound directory')
            self.lease(git_entry, directory=True)
            return {'repo': repo, 'common_dir': common, 'mode': 'main'}
        if self.safety.is_dir(git_entry):
            raise ValueError('Foreign repository directory is not a registered linked worktree')
        text = self.read(git_entry, 4096).decode('utf-8').strip()
        if not text.startswith('gitdir: ') or '\n' in text:
            raise ValueError('Linked worktree .git text is malformed')
        admin = joined(repo, text[8:])
        worktrees = ntpath.join(common, 'worktrees')
        if key(ntpath.dirname(admin)) != key(worktrees):
            raise ValueError('Linked worktree is not registered in bound common directory')
        self.lease(admin, directory=True)
        common_text = self.read(ntpath.join(admin, 'commondir'), 4096).decode('utf-8').strip()
        backlink = self.read(ntpath.join(admin, 'gitdir'), 4096).decode('utf-8').strip()
        if key(joined(admin, common_text)) != key(common) or key(joined(admin, backlink)) != key(git_entry):
            raise ValueError('Linked worktree/common-dir association is not bidirectional')
        return {'repo': repo, 'common_dir': common, 'mode': 'registered-linked-worktree'}

    def source_root(self, manifest, *, direct=False):
        repo = self.bind_repo(manifest['repo'])
        source = self.scope(manifest['source_dir'], source=True)
        expected = ntpath.join(repo['repo'], 'ck3_autonomous_player', 'native_bridge')
        label = manifest.get('external_candidate')
        in_bound_worktree = direct and within(source, repo['repo'])
        if key(source) != key(expected) and not in_bound_worktree:
            # Direct producer source_dir is the actual source common parent;
            # it can be C:/ across a worktree and CROOT fixture. Each direct
            # source operand below is independently bound, never by this parent.
            if (not isinstance(label, str) or not label.strip() or
                    (not direct and not any(within(source, root) for root in self.policy['allowed_external_source_roots']))):
                raise ValueError('Source must be linked project native_bridge or explicitly named allowed external candidate')
        self.lease(source, directory=True)
        return source, repo

    def source_operand(self, path, source):
        path = self.scope(path, source=True)
        project_scope = within(path, source) or within(path, self.policy['repo_root'])
        external_scope = any(within(path, root) for root in self.policy['allowed_external_source_roots'])
        if not (project_scope or external_scope):
            raise ValueError('Declared source operand is outside project source/candidate scope')
        self.read(path, SOURCE_LIMIT)
        return path


def fingerprint(claim, path, *, expected=None):
    path = claim.scope(path)
    if ntpath.splitext(path)[1].casefold() != '.exe':
        raise ValueError('Only exact EXE file outputs are allowed')
    raw = claim.read(path, FILE_LIMIT, expected)
    if len(raw) < 64 or raw[:2] != b'MZ':
        raise ValueError('Output is not DOS/PE EXE')
    offset = struct.unpack_from('<I', raw, 60)[0]
    if offset < 64 or offset + 24 > len(raw) or raw[offset:offset+4] != b'PE\0\0':
        raise ValueError('Output has invalid PE signature')
    machine, sections = struct.unpack_from('<HH', raw, offset+4)
    optional_size, flags = struct.unpack_from('<HH', raw, offset+20)
    if (machine not in (0x14c, 0x8664, 0xaa64) or not sections or not flags & 2 or flags & 0x2000
            or optional_size < 2 or offset + 24 + optional_size + sections * 40 > len(raw)):
        raise ValueError('Output is non-executable PE/DLL or unsupported header')
    magic = struct.unpack_from('<H', raw, offset+24)[0]
    if magic != (0x10b if machine == 0x14c else 0x20b):
        raise ValueError('PE architecture/optional header mismatch')
    return {'path': path, 'size': len(raw), 'sha256': sha(raw)}


def validate_files(manifest, policy):
    files = manifest.get('files')
    if not isinstance(files, list) or not 1 <= len(files) <= policy['max_files']:
        raise ValueError('Manifest must declare bounded actual EXE outputs')
    identities = set()
    for row in files:
        if not isinstance(row, dict) or set(row) not in ({'path', 'size', 'sha256'}, {'path', 'size', 'sha256', 'target', 'target_id'}):
            raise ValueError('EXE fingerprint fields are malformed')
        if type(row['size']) is not int or not 64 <= row['size'] <= FILE_LIMIT:
            raise ValueError('EXE size is malformed')
        hex_sha(row['sha256'])
        identity = key(row['path'])
        if identity in identities:
            raise ValueError('Duplicate declared EXE output')
        identities.add(identity)


def validate_cmake(claim, manifest):
    exact_keys(manifest, {'schema', 'repo', 'source_dir', 'build_dir', 'configuration', 'requested_targets',
                         'external_candidate', 'cmake_index', 'cmake_codemodel', 'target_provenance', 'files'}, 'CMake manifest')
    source, repo_identity = claim.source_root(manifest)
    claim.read(ntpath.join(source, 'CMakeLists.txt'), SOURCE_LIMIT)
    build = claim.scope(manifest['build_dir'])
    claim.lease(build, directory=True)
    configuration = manifest['configuration']
    requested = manifest['requested_targets']
    if not isinstance(configuration, str) or not isinstance(requested, list) or not requested or not all(isinstance(x, str) and x for x in requested):
        raise ValueError('CMake configuration/selected-target declaration is malformed')
    reply = ntpath.join(build, '.cmake', 'api', 'v1', 'reply')
    claim.lease(reply, directory=True)
    indexes = [r for r in claim.safety.list_files(reply) if r.get('is_file') is True and re.fullmatch(r'index-[^\\/]+\.json', ntpath.basename(r['path']))]
    if not indexes or len(indexes) > 4096:
        raise ValueError('Missing/unbounded actual CMake index metadata')
    latest = max(indexes, key=lambda r: r['mtime_ns'])
    if key(latest['path']) != key(manifest['cmake_index']['path']):
        raise ValueError('Manifest is not the current CMake index')
    index = claim.json_pin(manifest['cmake_index'])
    models = [r for r in index.get('objects', []) if r.get('kind') == 'codemodel' and r.get('version', {}).get('major') == 2]
    if len(models) != 1:
        raise ValueError('Exactly one CMake codemodel-v2 required')
    model_path = joined(reply, models[0]['jsonFile'])
    if not within(model_path, reply) or key(model_path) != key(manifest['cmake_codemodel']['path']):
        raise ValueError('CMake model path does not match actual index')
    model = claim.json_pin(manifest['cmake_codemodel'])
    if key(model['paths']['source']) != key(source) or key(model['paths']['build']) != key(build):
        raise ValueError('CMake source/build identity mismatch')
    configs = [c for c in model['configurations'] if c.get('name') in (configuration, '')]
    if len(configs) != 1:
        raise ValueError('CMake configuration is not unique')
    rows = configs[0]['targets']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 4096:
        raise ValueError('CMake target graph is not bounded')
    by_id = {r['id']: r for r in rows}
    by_name = {r['name']: r['id'] for r in rows}
    if len(by_id) != len(rows) or len(by_name) != len(rows):
        raise ValueError('Duplicate CMake target identity')
    if requested != ['all'] and any(name not in by_name for name in requested):
        raise ValueError('Selected CMake target is absent')
    pending = list(by_id) if requested == ['all'] else [by_name[name] for name in requested]
    visited, found, provenance = set(), [], []
    while pending:
        claim.budget()
        identity = pending.pop()
        if identity in visited:
            continue
        visited.add(identity)
        row = by_id[identity]
        target_path = joined(reply, row['jsonFile'])
        if not within(target_path, reply):
            raise ValueError('CMake target metadata escapes reply directory')
        raw = claim.read(target_path)
        target = strict_json(raw)
        if target.get('id') != identity or target.get('name') != row['name']:
            raise ValueError('CMake target identity mismatch')
        pending.extend(d['id'] for d in target.get('dependencies', []) if d['id'] in by_id)
        if target.get('type') != 'EXECUTABLE':
            continue
        if target.get('imported') or target.get('isGeneratorProvided') or 'compilerid' in row['name'].casefold():
            raise ValueError('Imported/generator/CompilerId executable is forbidden')
        target_source = joined(source, target['paths']['source'])
        if not within(target_source, source):
            raise ValueError('CMake executable source escapes named project source')
        for item in target.get('sources', []):
            claim.source_operand(joined(source, item['path']), source)
        for artifact in target.get('artifacts', []):
            output = joined(build, artifact['path'])
            if ntpath.splitext(output)[1].casefold() != '.exe':
                continue
            if not within(output, build):
                raise ValueError('CMake EXE output escapes named build')
            try:
                record = fingerprint(claim, output)
            except FileNotFoundError:
                continue  # All-target metadata can include actual not-yet-built targets.
            record.update(target=target['name'], target_id=identity)
            found.append(record)
        provenance.append({'path': target_path, 'sha256': sha(raw), 'target': target['name'],
                           'target_id': identity, 'source': target_source})
    unique = {key(r['path']): r for r in found}
    fresh_files = sorted(unique.values(), key=lambda r: r['path'])
    if fresh_files != manifest['files'] or provenance != manifest['target_provenance']:
        raise ValueError('CMake selected-target source/output/provenance differs from current locked graph')
    return repo_identity


def option_paths(argv, prefix):
    paths = []
    for index, value in enumerate(argv):
        operand = None
        if value.casefold() == prefix and index + 1 < len(argv):
            operand = argv[index+1]
        elif value.casefold().startswith(prefix) and len(value) > len(prefix):
            operand = value[len(prefix):]
        if operand:
            paths.append(absolute(operand))
    return paths


def validate_msvc(claim, manifest):
    exact_keys(manifest, {'schema', 'repo', 'source_dir', 'build_dir', 'external_candidate', 'command_provenance', 'files'}, 'MSVC manifest')
    source, repo_identity = claim.source_root(manifest, direct=True)
    build = claim.scope(manifest['build_dir'])
    claim.lease(build, directory=True)
    proof = manifest['command_provenance']
    exact_keys(proof, {'kind', 'argv', 'return_code', 'sources', 'objects', 'source_commands', 'declaration_boundary'}, 'MSVC proof')
    argv = proof['argv']
    if proof['kind'] != 'msvc-explicit-command' or type(proof['return_code']) is not int or proof['return_code'] != 0:
        raise ValueError('Unknown/unsuccessful direct producer')
    if not isinstance(argv, list) or not argv or len(argv) > 4096 or not all(isinstance(x, str) for x in argv):
        raise ValueError('Actual compiler argv data is malformed')
    tool = ntpath.basename(argv[0]).casefold()
    if tool not in ('cl.exe', 'link.exe'):
        raise ValueError('Only actual CL/link producer data is known; no command execution')
    declared = option_paths(argv, '/fe' if tool == 'cl.exe' else '/out:')
    commands = [{'argv': argv, 'return_code': 0}] if tool == 'cl.exe' else proof['source_commands']
    if not isinstance(commands, list) or not commands or len(commands) > 4096:
        raise ValueError('Actual successful linker source command chain required')
    inputs, objects = [], []
    for command in commands:
        exact_keys(command, {'argv', 'return_code'}, 'Actual source command')
        args = command['argv']
        if type(command['return_code']) is not int or command['return_code'] != 0 or not isinstance(args, list) or not args or not all(isinstance(x, str) for x in args) or ntpath.basename(args[0]).casefold() != 'cl.exe':
            raise ValueError('Invalid actual CL source producer')
        for value in args[1:]:
            if ntpath.splitext(value)[1].casefold() not in ('.cpp', '.cc', '.cxx', '.c'):
                continue
            path = absolute(value)
            if not within(path, source):
                raise ValueError('MSVC source is outside declared project source')
            bound_source = within(path, repo_identity['repo'])
            named_external = isinstance(manifest['external_candidate'], str) and bool(manifest['external_candidate'].strip())
            candidate_source = named_external and any(within(path, root) for root in claim.policy['allowed_external_source_roots'])
            if not (bound_source or candidate_source):
                raise ValueError('Each actual MSVC source must belong to bound worktree or named allowed candidate')
            raw = claim.read(claim.source_operand(path, source), SOURCE_LIMIT)
            inputs.append({'path': path, 'size': len(raw), 'sha256': sha(raw)})
        if tool == 'link.exe':
            if '/c' not in [a.casefold() for a in args]:
                raise ValueError('Linker source producer is not actual CL/c')
            outputs = option_paths(args, '/fo')
            if not outputs:
                raise ValueError('CL/c exact absolute object output required')
            for path in outputs:
                if ntpath.splitext(path)[1].casefold() != '.obj' or not within(path, build):
                    raise ValueError('CL/c object is outside named build')
                raw = claim.read(path, FILE_LIMIT)
                objects.append({'path': path, 'size': len(raw), 'sha256': sha(raw)})
    if not inputs or inputs != proof['sources'] or objects != proof['objects']:
        raise ValueError('Current locked direct source/object pins differ from producer data')
    if tool == 'link.exe':
        linked = [absolute(a) for a in argv[1:] if ntpath.splitext(a)[1].casefold() == '.obj']
        if not linked or any(key(p) not in {key(r['path']) for r in objects} for p in linked):
            raise ValueError('Linked object lacks its actual successful source producer')
    outputs = []
    for item in manifest['files']:
        path = absolute(item['path'])
        if not within(path, build) or key(path) not in {key(p) for p in declared}:
            raise ValueError('EXE is not a declared output of this exact MSVC producer')
        outputs.append(fingerprint(claim, path, expected=item))
    if outputs != manifest['files']:
        raise ValueError('Current locked MSVC outputs differ from actual declared bytes')
    return repo_identity


def settings(client):
    value = client.read_settings()
    exact_keys(value, SETTINGS, 'Actual settings readback')
    if not all(isinstance(value[k], list) and all(isinstance(p, str) for p in value[k]) for k in SETTINGS):
        raise ValueError('Administrative settings view is malformed/unknown')
    return value


def settings_keys(value, field):
    return {ntpath.normcase(ntpath.normpath(p)) for p in value[field]}


def readback(receipt, after):
    before = receipt['before_settings']
    receipt['after_settings'], receipt['after'] = after, after['ExclusionPath']
    observed, prior = settings_keys(after, 'ExclusionPath'), settings_keys(before, 'ExclusionPath')
    requested = {key(r['path']) for r in receipt['files']}
    receipt['verified_requested_paths'] = [r['path'] for r in receipt['files'] if key(r['path']) in observed]
    receipt['missing_requested_paths'] = [r['path'] for r in receipt['files'] if key(r['path']) not in observed]
    receipt['observed_prior_settings_preserved'] = prior <= observed
    receipt['observed_extensions_unchanged'] = set(before['ExclusionExtension']) == set(after['ExclusionExtension'])
    receipt['observed_processes_unchanged'] = set(before['ExclusionProcess']) == set(after['ExclusionProcess'])
    fulfilled = requested <= observed and prior <= observed and receipt['observed_extensions_unchanged'] and receipt['observed_processes_unchanged']
    receipt['partial_mutation'] = bool((requested - prior) & observed) and not fulfilled
    return fulfilled


def register_claim(claim, receipt, client_factory):
    claim.revalidate_all()
    client = None
    stage = 'before-readback'
    try:
        client = client_factory()
        before = settings(client)
        receipt['before_settings'], receipt['before'] = before, before['ExclusionPath']
        known = settings_keys(before, 'ExclusionPath')
        for row in receipt['files']:
            stage = 'pre-call-file-validation'
            claim.revalidate_all()
            if key(row['path']) in known:
                receipt['calls'].append({'path': row['path'], 'method': 'already-present', 'return_value': None})
                continue
            call = {'path': row['path'], 'method': 'Add', 'return_value': None, 'return_value_available': False}
            receipt['calls'].append(call)
            stage = 'Add-invocation'
            try:
                response = client.add_path(row['path'])
            except Exception as error:
                call.update(call_error=str(error), call_error_type=type(error).__name__)
                raise
            if isinstance(response, dict):
                call.update(response)
                value = response.get('return_value')
            else:
                value = response
                call.update(return_value=value, return_object_absent=value is None)
            if value is not None and type(value) is not int:
                raise ValueError('Provider ReturnValue is not nullable integer')
            call['return_value_available'] = value is not None
            if value is not None and value != 0:
                stage = 'Add-return-value'
                raise RuntimeError('WMI Add nonzero ReturnValue')
            if value is None:
                stage = 'post-call-readback'
                actual = settings(client)
                call['fresh_readback'] = actual
                readback(receipt, actual)
                observed = settings_keys(actual, 'ExclusionPath')
                if not (known | {key(row['path'])}) <= observed or not receipt['observed_extensions_unchanged'] or not receipt['observed_processes_unchanged']:
                    raise RuntimeError('Nullable-return fresh readback incomplete; no next Add')
                known = observed
            else:
                known.add(key(row['path']))
        stage = 'final-readback'
        if not readback(receipt, settings(client)):
            raise RuntimeError('Final exact paths/prior/Extension/Process readback incomplete')
        receipt.update(status='verified', verification_source='same SYSTEM/admin client actual fresh readback')
    except Exception as error:
        receipt.update(status='settings_failed', error=str(error), error_type=type(error).__name__, error_stage=stage)
        if client is not None and receipt['before_settings'] is not None:
            try:
                fulfilled = readback(receipt, settings(client))
                if fulfilled and stage in ('Add-invocation', 'Add-return-value', 'post-call-readback', 'final-readback'):
                    receipt.update(status='verified', verification_source='same SYSTEM/admin actual readback after preserved call error')
            except Exception as read_error:
                receipt['after_read_error'] = str(read_error)
    return receipt


def process_request(path, policy_bytes, safety, client_factory, runtime_guard, *, run_deadline=None):
    policy = parse_policy(policy_bytes)
    policy_sha = sha(policy_bytes)
    token = safety.token_identity()
    receipt = {'schema': MANIFEST_SCHEMA, 'broker_schema': RECEIPT_SCHEMA, 'status': 'settings_failed',
               'admin_token': token.get('admin') is True, 'system_token_sid': token.get('sid'),
               'before': None, 'after': None, 'before_settings': None, 'after_settings': None,
               'calls': [], 'files': [], 'settings_success_is_runtime_trust': False,
               'exclusion_types_written': ['ExclusionPath exact files']}
    claim = Claim(policy, safety, min(safety.clock() + policy['request_budget_seconds'], run_deadline or float('inf')))
    claimed = False
    protected_runtime_ok = False
    request_id, request_sha = None, None
    stage = 'runtime-and-token'
    try:
        if token.get('sid') != SYSTEM_SID or token.get('admin') is not True:
            raise PermissionError('Actual SYSTEM SID/admin token required; no WMI connected')
        proof = runtime_guard(policy, policy_sha)
        if (proof.get('runtime_verified') is not True or proof.get('protected_code') is not True
                or proof.get('runtime_manifest_sha256') != policy['runtime_manifest_sha256']):
            raise PermissionError('Protected runtime/code ACL/seal is unverified; no WMI connected')
        protected_runtime_ok = True
        path = absolute(path)
        if key(ntpath.dirname(path)) != key(policy['inbox_dir']):
            raise ValueError('Request path is outside fixed local owner inbox')
        name = ntpath.basename(path)
        if not name.endswith('.request.json'):
            raise ValueError('Request filename is unknown')
        request_id = canonical_uuid(name[:-13])
        stage = 'owner-request-snapshot'
        held = claim.lease(path, owner=policy['owner_sid'])
        raw = held.read_bytes(policy['max_request_bytes'])
        held.revalidate()
        if not isinstance(raw, bytes) or len(raw) > policy['max_request_bytes']:
            raise ValueError('Request bytes exceed bound')
        request_sha = sha(raw)
        destination = ntpath.join(policy['receipts_dir'], request_id + '.receipt.json')
        marker = ntpath.join(policy['frozen_dir'], request_id + '.claim.json')
        hash_marker = ntpath.join(policy['frozen_dir'], request_sha + '.hash-claim.json')
        rejected_marker = ntpath.join(policy['frozen_dir'], request_id + '.rejected.json')
        if safety.exists(destination) or safety.exists(marker) or safety.exists(hash_marker) or safety.exists(rejected_marker):
            receipt.update(error='Request UUID/hash already claimed; no automatic replay', error_stage='dedup', deduplicated=True)
            return receipt
        request = strict_json(raw)
        exact_keys(request, REQUEST_KEYS, 'Request')
        if encode_json(request) != raw:
            raise ValueError('Request must use the fixed canonical UTF8/newline encoding')
        if (request['schema'] != REQUEST_SCHEMA or canonical_uuid(request['request_id']) != request_id
                or request['installation_id'] != policy['installation_id'] or request['expected_policy_sha256'] != policy_sha
                or request['producer_kind'] not in KINDS):
            raise ValueError('Request installation/policy/UUID/known producer mismatch')
        if not isinstance(request['manifest_b64'], str):
            raise ValueError('Canonical manifest base64 required')
        manifest_raw = base64.b64decode(request['manifest_b64'], validate=True)
        if base64.b64encode(manifest_raw).decode('ascii') != request['manifest_b64'] or len(manifest_raw) > policy['max_request_bytes']:
            raise ValueError('Manifest encoding/bound mismatch')
        if sha(manifest_raw) != hex_sha(request['manifest_sha256']):
            raise ValueError('Exact manifest body SHA mismatch')
        manifest = strict_json(manifest_raw)
        if not isinstance(manifest, dict) or manifest.get('schema') != MANIFEST_SCHEMA:
            raise ValueError('Unknown manifest schema')
        receipt['broker_identity'] = {'installation_id': policy['installation_id'], 'owner_sid': policy['owner_sid'],
            'request_id': request_id, 'request_sha256': request_sha, 'manifest_bytes_sha256': sha(manifest_raw),
            'policy_sha256': policy_sha, 'runtime_manifest_sha256': policy['runtime_manifest_sha256'],
            'runtime_verified': True, 'protected_code': True, 'request_owner_sid': held.owner_sid, 'actual_token_sid': token['sid']}
        safety.publish_new(marker, encode_json({'request_id': request_id, 'request_sha256': request_sha}), private=True)
        claimed = True
        safety.publish_new(hash_marker, encode_json({'request_id': request_id, 'request_sha256': request_sha}), private=True)
        safety.publish_new(ntpath.join(policy['frozen_dir'], request_sha + '.request.json'), raw, private=True)
        stage = 'producer-validation'
        validate_files(manifest, policy)
        if request['producer_kind'] == 'cmake-file-api-v2':
            if 'command_provenance' in manifest:
                raise ValueError('Producer kind disagrees with manifest')
            repo_identity = validate_cmake(claim, manifest)
        else:
            if 'command_provenance' not in manifest:
                raise ValueError('Producer kind disagrees with manifest')
            repo_identity = validate_msvc(claim, manifest)
        receipt.update(files=manifest['files'], manifest_sha256=sha(json.dumps(manifest, sort_keys=True).encode()),
                       source_identity=repo_identity, input_pins=claim.input_pins)
        claim.revalidate_all()
        stage = 'settings-readback-and-Add'
        register_claim(claim, receipt, client_factory)
    except Exception as error:
        receipt.update(status='settings_failed', error=str(error), error_type=type(error).__name__, error_stage=stage)
    finally:
        try:
            if claimed:
                safety.publish_new(ntpath.join(policy['receipts_dir'], request_id + '.receipt.json'), encode_json(receipt), private=False)
            elif protected_runtime_ok and request_id is not None and receipt.get('deduplicated') is not True:
                # Permanently retain a private failed identity so preserved
                # malformed/unowned requests cannot occupy every future slot.
                # No caller receipt/verified identity is invented before claim.
                safety.publish_new(ntpath.join(policy['frozen_dir'], request_id + '.rejected.json'),
                    encode_json({'request_id': request_id, 'request_sha256': request_sha,
                                 'status': 'rejected-before-claim', 'error': receipt.get('error'),
                                 'error_stage': receipt.get('error_stage')}), private=True)
        finally:
            claim.close()
    return receipt


def run_once(policy_bytes, safety, client_factory, runtime_guard):
    policy = parse_policy(policy_bytes)
    deadline = safety.clock() + policy['run_budget_seconds']
    candidates = [r for r in safety.list_files(policy['inbox_dir']) if r.get('is_file') is True
                  and re.fullmatch(r'[0-9a-f-]{36}\.request\.json', ntpath.basename(r['path']))]
    candidates.sort(key=lambda r: (r['mtime_ns'], r['path']))
    results = []
    for row in candidates:
        if safety.clock() >= deadline:
            break
        if len(results) >= policy['max_requests_per_run']:
            break
        try:
            identity = canonical_uuid(ntpath.basename(row['path'])[:-13])
        except (ValueError, AttributeError):
            continue
        # Assets remain append-only. Completed/crashed claims must not occupy
        # every queue slot forever or cause another Add when Task.Run repeats.
        if (safety.exists(ntpath.join(policy['receipts_dir'], identity + '.receipt.json')) or
                safety.exists(ntpath.join(policy['frozen_dir'], identity + '.claim.json')) or
                safety.exists(ntpath.join(policy['frozen_dir'], identity + '.rejected.json'))):
            continue
        results.append(process_request(row['path'], policy_bytes, safety, client_factory, runtime_guard, run_deadline=deadline))
    return results
