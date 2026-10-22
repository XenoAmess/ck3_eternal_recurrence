"""Nine portable, authored exact-tree source-binding consumers.

The five-file Native tree and its build/FileAPI/Defender records are test data.
They do not represent a Native build, OS readback, game or runtime qualification.
Production modules are loaded only by setUpClass, so static discovery is inert.
Set CK3_NATIVE_EXACT_TREE_TEST_SCRATCH to an approved temporary parent when a
local work package requires a bounded scratch root. Only its unique child is
created and cleaned up. No existing project checkout is modified.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import ClassVar, Protocol, TypedDict, runtime_checkable
import unittest


class Signature(TypedDict):
    bytes: int
    sha256: str


class FilePin(Signature):
    path: str


JSONObject = dict[str, object]


@runtime_checkable
class PublicAPI(Protocol):
    NATIVE_PREFIX: str
    HOST_RELATIVE: str
    FORBIDDEN_OLD_FLAGS: tuple[str, ...]

    def pin(self, path: Path) -> FilePin: ...
    def sig(self, raw: bytes) -> Signature: ...
    def qualify_native(
        self, path: Path, root: Path, commit: str, machine: str,
        previous_dll: FilePin, previous_manifest: JSONObject,
        native_source_checkout_binding: Path | None = None,
        native_shared_python_host_delta: Path | None = None,
    ) -> object: ...


@runtime_checkable
class BindingAPI(Protocol):
    SCHEMA: str

    def qualified_native_source_checkout(
        self, binding_path: Path | None, *, root: Path, runtime_commit: str,
        native_commit: str, machine: str, qualified_native_ref: FilePin,
        qualification: JSONObject, snapshot_ref: FilePin, snapshot: JSONObject,
        native_shared_python_host_delta: Path | None = None,
    ) -> object: ...


@runtime_checkable
class CompiledInputsAPI(Protocol):
    def compiled_inputs(self, qualification: JSONObject, snapshot: JSONObject) -> object: ...


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def object_fields(value: object) -> JSONObject:
    """Validate the legacy module's dynamic mapping boundary before use."""
    if not isinstance(value, dict):
        raise ValueError('Production consumer did not return an object')
    result: JSONObject = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError('Production object key must be text')
        result[key] = item
    return result


def load_module(filename: str, module_name: str) -> object:
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError('Production source module not found: ' + filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_apis() -> tuple[PublicAPI, BindingAPI, CompiledInputsAPI]:
    """Protocols describe only the legacy calls used here; no implementation stub."""
    public = load_module('ck3_mod_acceptance_build_runtime.py', 'exact_tree_test_public')
    binding = load_module('ck3_mod_acceptance_native_source_binding.py', 'exact_tree_test_binding')
    compiled = load_module('ck3_mod_acceptance_shared_python_host_delta.py', 'exact_tree_test_compiled')
    if not isinstance(public, PublicAPI) or not isinstance(binding, BindingAPI) or not isinstance(compiled, CompiledInputsAPI):
        raise ValueError('Production modules do not implement the required narrow interfaces')
    require(public.NATIVE_PREFIX == 'ck3_autonomous_player/native_bridge/'
            and public.HOST_RELATIVE == public.NATIVE_PREFIX + 'research/run_ck3_12002_mcp_live.py',
            'Unexpected production canonical paths')
    return public, binding, compiled


def pin(path: Path) -> FilePin:
    path = path.resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def signature(raw: bytes) -> Signature:
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(path: Path, value: object) -> FilePin:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2) + '\n').encode('utf-8'))
    return pin(path)


_active_scratch: Path | None = None


def git(repo: Path, *args: str) -> str:
    scratch = _active_scratch
    if scratch is None or not repo.resolve().is_relative_to(scratch):
        raise ValueError('Git mutations are restricted to this unique authored scratch')
    return subprocess.run(['git', *args], cwd=repo, capture_output=True,
                          text=True, check=True).stdout.strip()


@dataclass
class AuthoredInputs:
    repo: Path
    native: Path
    native_commit: str
    worktree: Path
    wnative: Path
    evidence: Path
    machine: str
    contents: dict[str, bytes]
    snapshot: JSONObject
    snapshot_ref: FilePin
    qualification: JSONObject
    qpath: Path
    qref: FilePin
    manifest: JSONObject
    dll_ref: FilePin
    runtime_commit: str
    exact: JSONObject


def make_authored_inputs(scratch: Path, public: PublicAPI, compiled: CompiledInputsAPI,
                         *, same_root: bool = False, fixture_cmake: bool = False,
                         wire_consumer: bool = False, host_test_companion: bool = False) -> AuthoredInputs:
    """Extracted fixture setup; every path/pin is rebuilt in this scratch."""
    repo = scratch / 'r'
    repo.mkdir()
    template = scratch / 'empty-template'
    template.mkdir()
    git(repo, 'init', '--initial-branch=main', '--template=' + str(template))
    for key, value in [('user.name', 'Authored exact-tree fixture'), ('user.email', 'fixture@example.invalid'),
                       ('core.longpaths', 'true'), ('core.autocrlf', 'false')]:
        git(repo, 'config', key, value)
    native = repo / public.NATIVE_PREFIX
    host_relative = 'research/run_ck3_12002_mcp_live.py'
    contents = {'CMakeLists.txt': b'# authored fixture\n', 'src/body.cpp': b'int n;\n',
                'include/pin.hpp': b'#pragma once\n', 'research/other.py': b'OTHER = 0\n',
                host_relative: b'HOST = 0\n'}
    if wire_consumer:
        contents['research/refill_add_live_12004/consume_live_refill_add.py'] = b'CONSUMER = 0\n'
    if host_test_companion:
        contents['research/test_ck3_12002_mcp_live.py'] = b'TEST = 0\n'
    fixture_name = 'xar_ck3_12004_player_pilgrimage_traits_test' if fixture_cmake else 'authored_finite'
    if fixture_cmake:
        contents['cmake/player_pilgrimage_traits_12004.cmake'] = (
            b'if(BUILD_TESTING)\n  add_executable(xar_ck3_12004_player_pilgrimage_traits_test\n'
            b'    src/body.cpp)\n  target_link_libraries(xar_ck3_12004_player_pilgrimage_traits_test PRIVATE\n'
            b'    xar_ck3_12002_runtime)\nendif()\n')
    for relative, raw in contents.items():
        path = native / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'Authored Native fixture, not a real build')
    native_commit = git(repo, 'rev-parse', 'HEAD')
    worktree = scratch / 'w'
    git(repo, 'worktree', 'add', '--detach', str(worktree), native_commit)
    # Keep the original definition's authored host successor, then construct
    # the independent runtime history with its exact original Native bytes.
    (repo / public.HOST_RELATIVE).write_bytes(b'HOST = 1\n')
    git(repo, 'add', public.HOST_RELATIVE)
    git(repo, 'commit', '-m', 'Authored sole shared-host successor')
    wnative = native if same_root else worktree / public.NATIVE_PREFIX
    evidence = scratch / 'e'
    evidence.mkdir()
    machine = 'authored-fixture-machine'
    snapshot: JSONObject = {'machine_id': machine, 'root_commit': native_commit,
        'Root_native_source_base': str(wnative), 'snapshot_native_base': str(wnative),
        'source_count': len(contents), 'files': [{'native_relative': relative, **signature(raw)} for relative, raw in contents.items()]}
    snapshot_ref = write(evidence / 'snapshot.json', snapshot)
    verification_ref = write(evidence / 'source-verification.json', {
        'machine_id': machine, 'root_commit': native_commit, 'source_manifest': snapshot_ref,
        'all_snapshot_files_exactly_verified': len(contents), 'all_original_inputs_still_exactly_verified': len(contents), 'authored_fixture': True})
    profile: JSONObject = {'machine_id': machine, 'repository_default_flags_changed': False,
        'flags': {name: 'OFF' for name in public.FORBIDDEN_OLD_FLAGS}, 'authored_fixture': True}
    profile_ref = write(evidence / 'profile.json', profile)
    build = evidence / 'build'
    build.mkdir()
    dll, exe = build / 'authored-native.bin', build / 'authored-finite.bin'
    dll.write_bytes(b'AUTHORED NEVER EXECUTED NATIVE DATA')
    exe.write_bytes(b'AUTHORED NEVER EXECUTED FINITE DATA')
    dll_ref, exe_ref = pin(dll), pin(exe)
    log_ref = write(evidence / 'authored-log.json', {'scope': 'AUTHORED fixture data, no process ran'})
    execution: JSONObject = {'machine_id': machine, 'original_wait_returncode': 0, 'stopped_reason': None,
        'started_at_utc': '2026-01-01T00:00:00Z', 'finished_at_utc': '2026-01-01T00:00:01Z',
        'game_started_or_attached': False, 'actual_live_business_qualified': False, 'log': log_ref, 'authored_fixture': True}
    if fixture_cmake:
        protocol = build / 'xar_bridge_protocol.lib'
        protocol.write_bytes(b'AUTHORED archive data; never linked')
        production_rsp = build / 'production.rsp'
        production_rsp.write_text(str(protocol), encoding='utf-8')
        execution['response_files'] = [pin(production_rsp)]
        fixture_rsp = build / 'fixture.rsp'
        fixture_rsp.write_text('/OUT:' + str(exe) + ' ' + str(protocol), encoding='utf-8')
        write(evidence / 'fixture-link.json', dict(execution, source_commit=native_commit,
            argv=['C:/authored/link.exe', '@' + str(fixture_rsp)], response_files=[pin(fixture_rsp)]))
    build_receipt = write(evidence / 'build-receipt.json', execution)
    finite_receipt = write(evidence / 'finite-receipt.json', dict(execution, argv=[str(exe)]))
    fixture: JSONObject = {'target': fixture_name, 'executable': exe_ref, 'execution': finite_receipt}
    prod_target: JSONObject = {'id': 'p', 'name': 'xar_ck3_bridge', 'type': 'MODULE_LIBRARY',
        'sources': [{'path': 'src/body.cpp', 'compileGroupIndex': 0}], 'compileGroups': [], 'artifacts': [{'path': dll.name}]}
    fixture_target: JSONObject = {'id': 'f', 'name': fixture_name, 'type': 'EXECUTABLE',
        'sources': [], 'compileGroups': [], 'artifacts': [{'path': exe.name}]}
    api = evidence / 'api'
    api.mkdir()
    write(api / 'prod.json', prod_target)
    write(api / 'fixture.json', fixture_target)
    model: JSONObject = {'paths': {'source': str(wnative), 'build': str(build)},
        'configurations': [{'targets': [{'id': 'p', 'jsonFile': 'prod.json'}, {'id': 'f', 'jsonFile': 'fixture.json'}]}]}
    model_ref = write(api / 'codemodel.json', model)
    index_ref = write(api / 'index.json', {'authored_fixture': True})
    commands_ref = write(evidence / 'commands.json', [{'file': str(wnative / 'src/body.cpp'),
        'directory': str(build), 'command': 'AUTHORED NOT RUN'}])
    scope: JSONObject = {'machine_id': machine, 'snapshot': snapshot_ref, 'no_fixture_in_production': True,
        'codemodel': model_ref, 'index': index_ref, 'compile_commands': commands_ref,
        'production_TUs': {'xar_ck3_bridge': 1}, 'requested_EXEs': [fixture_name], 'targets': [prod_target, fixture_target]}
    scope_ref = write(evidence / 'scope.json', scope)
    defender_manifest = {'files': [{'path': str(exe), 'size': exe_ref['bytes'], 'sha256': exe_ref['sha256']}]}
    dm = write(evidence / 'defender-manifest.json', defender_manifest)
    dr = write(evidence / 'defender-receipt.json', {'status': 'verified', 'admin_token': True,
        'authored_fixture_not_OS_readback': True,
        'manifest_sha256': hashlib.sha256(json.dumps(defender_manifest, sort_keys=True).encode()).hexdigest(),
        'missing_requested_paths': [], 'verified_requested_paths': [str(exe)]})
    defender_ref = write(evidence / 'defender-binding.json', {'machine_id': machine, 'status': 'verified',
        'exact_executable_count': 1, 'manifest': dm, 'receipt': dr, 'authored_fixture_not_OS_readback': True})
    freeze_ref = write(evidence / 'freeze.json', {'machine_id': machine, 'root_commit': native_commit,
        'no_fixture_target_in_production_dependency_closure': True, 'repository_default_flags_changed': False,
        'game_started_or_attached': False, 'original_DLL': dll_ref, 'published_DLL': dll_ref,
        'build_execution': build_receipt, 'source_manifest': snapshot_ref, 'source_verification': verification_ref,
        'profile': profile_ref, 'scope': scope_ref, 'authored_fixture': True})
    delivery_ref = write(evidence / 'delivery.json', {'machine_id': machine, 'actual_live_business_qualified': False,
        'all_original_build_and_fixture_Popen_waits_recorded': True, 'authored_fixture': True,
        'snapshot': snapshot_ref, 'profile': profile_ref, 'scope': scope_ref, 'source_verification': verification_ref,
        'production_freeze': freeze_ref, 'published_dll': dll_ref, 'Defender_settings_verified': defender_ref,
        'finite_tests': [{'name': fixture_name, 'execution': finite_receipt, 'exe': exe_ref}]})
    qualification: JSONObject = {'schema': 'ck3-qualified-native-build-v1', 'machine_id': machine,
        'observed_at_utc': '2026-01-01T00:00:02Z', 'source_commit': native_commit,
        'actual_live_business_qualified': False, 'authored_fixture': True, 'delivery': delivery_ref,
        'snapshot': snapshot_ref, 'profile': profile_ref, 'configured_scope': scope_ref,
        'source_verification': verification_ref, 'production_freeze': freeze_ref, 'original_dll': dll_ref,
        'published_dll': dll_ref, 'production_build_receipt': build_receipt, 'defender_binding': defender_ref,
        'fixture_results': [fixture]}
    qpath = evidence / 'Q.authored.json'
    qref = write(qpath, qualification)
    manifest: JSONObject = {'capabilities': {'authored': {'actual_production_freeze': freeze_ref}}}
    if same_root:
        # Authored metadata models the real old direct Root source path. The
        # current committed Root has the sole host successor; no process ran.
        runtime_commit = git(repo, 'rev-parse', 'HEAD')
        return AuthoredInputs(repo, native, native_commit, worktree, wnative, evidence, machine, contents,
            snapshot, snapshot_ref, qualification, qpath, qref, manifest, dll_ref, runtime_commit, {})
    git(repo, 'checkout', '--orphan', 'runtime-exact')
    (repo / public.HOST_RELATIVE).write_bytes(contents[host_relative])
    (repo / 'runtime-only.txt').write_bytes(b'Independent authored runtime history\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-m', 'Authored nonancestor runtime with exact Native tree')
    runtime_commit = git(repo, 'rev-parse', 'HEAD')
    status = subprocess.run(['git', 'merge-base', '--is-ancestor', native_commit, runtime_commit], cwd=repo)
    require(status.returncode == 1, 'Fixture must really have unrelated history')
    exact: JSONObject = {'schema': 'ck3-native-worktree-exact-tree-source-binding-v1', 'machine_id': machine,
        'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'runtime_repo_root': str(repo),
        'runtime_source_commit': runtime_commit, 'native_source_repo_root': str(worktree),
        'native_source_commit': native_commit, 'native_source_base': str(wnative),
        'native_subtree_tree_id': git(repo, 'rev-parse', native_commit + ':' + public.NATIVE_PREFIX.rstrip('/')),
        'common_git_directory': str(repo / '.git'), 'qualified_native': qref, 'snapshot': snapshot_ref,
        'native_compile_commit_is_ancestor': False, 'compiled_inputs': object_fields(compiled.compiled_inputs(qualification, snapshot))}
    git(repo, 'gc', '--prune=now')
    return AuthoredInputs(repo, native, native_commit, worktree, wnative, evidence, machine, contents,
        snapshot, snapshot_ref, qualification, qpath, qref, manifest, dll_ref, runtime_commit, exact)


class ExactTree(unittest.TestCase):
    temporary: ClassVar[tempfile.TemporaryDirectory[str]]
    data: ClassVar[AuthoredInputs]
    public: ClassVar[PublicAPI]
    binding: ClassVar[BindingAPI]

    @classmethod
    def setUpClass(cls) -> None:
        global _active_scratch
        cls.public, cls.binding, compiled = load_apis()
        parent = os.environ.get('CK3_NATIVE_EXACT_TREE_TEST_SCRATCH')
        cls.temporary = tempfile.TemporaryDirectory(prefix='ck3-exact-native-tree-', dir=parent)
        _active_scratch = Path(cls.temporary.name).resolve()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.data = make_authored_inputs(_active_scratch, cls.public, compiled)

    @classmethod
    def tearDownClass(cls) -> None:
        global _active_scratch
        _active_scratch = None

    def proof(self, value: JSONObject | None = None) -> Path:
        path = self.data.evidence / 'new-case-proof.json'
        write(path, self.data.exact if value is None else value)
        return path

    def consume(self, value: JSONObject | None = None, host_delta: Path | None = None) -> JSONObject:
        return object_fields(self.binding.qualified_native_source_checkout(self.proof(value), root=self.data.repo,
            runtime_commit=self.data.runtime_commit, native_commit=self.data.native_commit, machine=self.data.machine,
            qualified_native_ref=self.data.qref, qualification=self.data.qualification, snapshot_ref=self.data.snapshot_ref,
            snapshot=self.data.snapshot, native_shared_python_host_delta=host_delta))

    def test_01_old_explicit_schema_still_rejects_real_nonancestor(self) -> None:
        old = {key: value for key, value in self.data.exact.items() if key not in {'native_compile_commit_is_ancestor', 'compiled_inputs'}}
        old['schema'] = self.binding.SCHEMA
        with self.assertRaisesRegex(ValueError, 'must be an ancestor'):
            self.consume(old)

    def test_02_new_explicit_helper_returns_verified_false_ancestry(self) -> None:
        result = self.consume()
        self.assertIs(result['native_compile_commit_is_ancestor'], False)
        self.assertEqual(result['nonancestor_exact_tree_binding'], self.public.pin(self.proof()))

    def test_03_complete_public_qualifier_consumes_new_context(self) -> None:
        path = self.proof()
        result = object_fields(self.public.qualify_native(self.data.qpath, self.data.repo, self.data.runtime_commit,
            self.data.machine, self.data.dll_ref, self.data.manifest, path))
        self.assertIs(result['native_compile_commit_is_ancestor'], False)
        self.assertEqual(result['nonancestor_exact_tree_binding'], self.public.pin(path))
        self.assertEqual(result['native_files'], {self.public.NATIVE_PREFIX + 'src/body.cpp': self.public.sig(self.data.contents['src/body.cpp'])})
        self.assertEqual(result['compile_commit'], self.data.native_commit)

    def test_04_ancestry_declaration_cannot_be_true_or_integer_zero(self) -> None:
        for value in (True, 0):
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(ValueError, 'truthfully identify'):
                    self.consume(dict(self.data.exact, native_compile_commit_is_ancestor=value))

    def test_05_cpp_or_python_git_difference_is_not_exempt(self) -> None:
        for relative in ('src/body.cpp', 'research/other.py'):
            with self.subTest(relative=relative):
                path = self.data.native / relative
                before = path.read_bytes()
                try:
                    path.write_bytes(before + b'\n')
                    git(self.data.repo, 'add', self.public.NATIVE_PREFIX + relative)
                    git(self.data.repo, 'commit', '-m', 'Authored forbidden Native mismatch')
                    changed = git(self.data.repo, 'rev-parse', 'HEAD')
                    proof = dict(self.data.exact, runtime_source_commit=changed)
                    with self.assertRaisesRegex(ValueError, 'different Native Git trees'):
                        self.binding.qualified_native_source_checkout(self.proof(proof), root=self.data.repo,
                            runtime_commit=changed, native_commit=self.data.native_commit, machine=self.data.machine,
                            qualified_native_ref=self.data.qref, qualification=self.data.qualification,
                            snapshot_ref=self.data.snapshot_ref, snapshot=self.data.snapshot)
                finally:
                    git(self.data.repo, 'reset', '--hard', self.data.runtime_commit)

    def test_06_clean_index_flags_cannot_hide_raw_drift(self) -> None:
        relative = self.public.NATIVE_PREFIX + 'include/pin.hpp'
        path = self.data.repo / relative
        before = path.read_bytes()
        git(self.data.repo, 'update-index', '--assume-unchanged', relative)
        try:
            path.write_bytes(before + b'// changed bytes\n')
            self.assertEqual(git(self.data.repo, 'status', '--porcelain', '--untracked-files=all'), '')
            with self.assertRaisesRegex(ValueError, 'raw pin differs'):
                self.consume()
        finally:
            path.write_bytes(before)
            git(self.data.repo, 'update-index', '--no-assume-unchanged', relative)

    def test_07_compiled_fingerprint_or_bool_count_cannot_be_substituted(self) -> None:
        cases: list[tuple[str, object]] = [('unique_production_source_count', True), ('production_source_set_sha256', '0' * 64)]
        for key, value in cases:
            with self.subTest(key=key):
                proof = copy.deepcopy(self.data.exact)
                compiled = object_fields(proof['compiled_inputs'])
                compiled[key] = value
                proof['compiled_inputs'] = compiled
                with self.assertRaisesRegex(ValueError, 'count/fingerprint invalid|differ from actual'):
                    self.consume(proof)

    def test_08_shared_host_delta_cannot_be_combined(self) -> None:
        with self.assertRaisesRegex(ValueError, 'cannot allow any shared-host'):
            self.consume(host_delta=self.data.evidence / 'not-read-contract.json')

    def test_09_original_ancestor_tree_binding_still_passes(self) -> None:
        git(self.data.repo, 'checkout', '--detach', self.data.native_commit)
        try:
            proof = {key: value for key, value in self.data.exact.items() if key not in {'native_compile_commit_is_ancestor', 'compiled_inputs'}}
            proof.update(schema=self.binding.SCHEMA, runtime_source_commit=self.data.native_commit)
            result = object_fields(self.binding.qualified_native_source_checkout(self.proof(proof), root=self.data.repo,
                runtime_commit=self.data.native_commit, native_commit=self.data.native_commit, machine=self.data.machine,
                qualified_native_ref=self.data.qref, qualification=self.data.qualification,
                snapshot_ref=self.data.snapshot_ref, snapshot=self.data.snapshot))
            self.assertNotIn('nonancestor_exact_tree_binding', result)
        finally:
            git(self.data.repo, 'checkout', 'runtime-exact')
            git(self.data.repo, 'reset', '--hard', self.data.runtime_commit)


if __name__ == '__main__':
    unittest.main(verbosity=2)
