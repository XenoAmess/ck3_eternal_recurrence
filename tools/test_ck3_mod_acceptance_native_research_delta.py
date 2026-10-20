"""Focused authored producer-to-complete-consumer research-binding checks.

Set CK3_NATIVE_RESEARCH_TEST_SCRATCH to an approved temporary parent.
The borrowed ordinary fixture constructor creates fake Native/FileAPI/Defender
facts. Its nine business methods are never selected or executed here. Reviewed
research source bytes are test data and are never imported or executed.
"""
from __future__ import annotations

import base64
import copy
import json
import os
from pathlib import Path
import struct
import tempfile
from typing import ClassVar
import unittest
import zlib

import ck3_mod_acceptance_native_research_delta as research
import test_ck3_mod_acceptance_native_exact_tree_binding as fixture


def dependency_log(paths: list[str]) -> bytes:
    raw = bytearray(b'# ninjadeps\n\x04\x00\x00\x00')
    for index, path in enumerate(paths):
        body = path.encode()
        body += b'\x00' * (-len(body) % 4)
        body += struct.pack('<I', ~index & 0xffffffff)
        raw += struct.pack('<I', len(body)) + body
    body = struct.pack('<IQ', 0, 0) + b''.join(struct.pack('<I', n) for n in range(1, len(paths)))
    raw += struct.pack('<I', len(body) | 0x80000000) + body
    return bytes(raw)


def refresh(data: fixture.AuthoredInputs) -> None:
    data.snapshot.update(root_commit=data.native_commit, source_count=len(data.contents),
                         files=[{'native_relative': relative, **fixture.signature(raw)}
                                for relative, raw in data.contents.items()])
    data.snapshot_ref = fixture.write(data.evidence / 'snapshot.json', data.snapshot)
    verification_ref = fixture.write(data.evidence / 'source-verification.json', {
        'machine_id': data.machine, 'root_commit': data.native_commit, 'source_manifest': data.snapshot_ref,
        'all_snapshot_files_exactly_verified': len(data.contents),
        'all_original_inputs_still_exactly_verified': len(data.contents), 'authored_fixture': True})
    q = data.qualification
    scope_path = Path(research.checked(q['configured_scope'])['path'])
    scope = research.read(scope_path)
    scope['snapshot'] = data.snapshot_ref
    scope_ref = fixture.write(scope_path, scope)
    freeze_path = Path(research.checked(q['production_freeze'])['path'])
    freeze = research.read(freeze_path)
    freeze.update(root_commit=data.native_commit, source_manifest=data.snapshot_ref,
                  source_verification=verification_ref, scope=scope_ref)
    freeze_ref = fixture.write(freeze_path, freeze)
    delivery_path = Path(research.checked(q['delivery'])['path'])
    delivery = research.read(delivery_path)
    delivery.update(snapshot=data.snapshot_ref, source_verification=verification_ref,
                    scope=scope_ref, production_freeze=freeze_ref)
    delivery_ref = fixture.write(delivery_path, delivery)
    q.update(source_commit=data.native_commit, snapshot=data.snapshot_ref, configured_scope=scope_ref,
             source_verification=verification_ref, production_freeze=freeze_ref, delivery=delivery_ref)
    data.qref = fixture.write(data.qpath, q)
    data.manifest = {'capabilities': {'authored': {'actual_production_freeze': freeze_ref}}}


class ResearchDelta(unittest.TestCase):
    data: ClassVar[fixture.AuthoredInputs]
    public: ClassVar[fixture.PublicAPI]
    binding: ClassVar[fixture.BindingAPI]
    compiled: ClassVar[fixture.CompiledInputsAPI]
    proof_value: ClassVar[fixture.JSONObject]

    @classmethod
    def setUpClass(cls) -> None:
        cls.public, cls.binding, cls.compiled = fixture.load_apis()
        temporary = tempfile.TemporaryDirectory(prefix='authored-',
            dir=os.environ.get('CK3_NATIVE_RESEARCH_TEST_SCRATCH'))
        cls.addClassCleanup(temporary.cleanup)
        scratch = Path(temporary.name).resolve()
        fixture._active_scratch = scratch
        cls.data = fixture.make_authored_inputs(scratch, cls.public, cls.compiled)
        data = cls.data
        payload: object = json.loads((Path(__file__).resolve().parent / 'test_data/native_research_delta_v1.json').read_text(encoding='utf-8'))
        values = research.fields(payload)
        for label, repo in [('before', data.worktree), ('after', data.repo)]:
            for relative, encoded in research.fields(values[label]).items():
                raw = zlib.decompress(base64.b64decode(research.text(encoded)))
                target = repo / cls.public.NATIVE_PREFIX / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                if label == 'before':
                    data.contents[relative] = raw
            fixture.git(repo, 'add', cls.public.NATIVE_PREFIX)
            fixture.git(repo, 'commit', '-m', 'Authored reviewed research ' + label)
        data.native_commit = fixture.git(data.worktree, 'rev-parse', 'HEAD')
        data.runtime_commit = fixture.git(data.repo, 'rev-parse', 'HEAD')
        fixture.git(data.repo, 'gc', '--prune=now')
        refresh(data)
        build = data.evidence / 'build'
        (build / 'build.ninja').write_bytes(b'# Authored unexecuted graph\n')
        (build / '.ninja_deps').write_bytes(dependency_log(['body.obj', str(data.wnative / 'include/pin.hpp')]))
        delta = research.produce_research_delta(root=data.repo, native_repo=data.worktree,
            runtime_commit=data.runtime_commit, native_commit=data.native_commit,
            qualification=data.qualification, snapshot=data.snapshot)
        cls.proof_value = dict(data.exact, schema=research.SCHEMA,
            runtime_source_commit=data.runtime_commit, native_source_commit=data.native_commit,
            native_subtree_tree_id=fixture.git(data.worktree, 'rev-parse', data.native_commit + ':' + cls.public.NATIVE_PREFIX.rstrip('/')),
            runtime_native_subtree_tree_id=fixture.git(data.repo, 'rev-parse', data.runtime_commit + ':' + cls.public.NATIVE_PREFIX.rstrip('/')),
            qualified_native=data.qref, snapshot=data.snapshot_ref, full_native_tree_equal=False,
            compiled_inputs_equal=True, research_delta=delta,
            compiled_inputs=fixture.object_fields(cls.compiled.compiled_inputs(data.qualification, data.snapshot)))

    @classmethod
    def tearDownClass(cls) -> None:
        fixture._active_scratch = None

    def consume(self, value: fixture.JSONObject | None = None) -> fixture.JSONObject:
        data = self.data
        path = data.evidence / 'research-proof.json'
        fixture.write(path, self.proof_value if value is None else value)
        return fixture.object_fields(self.public.qualify_native(data.qpath, data.repo,
            data.runtime_commit if value is None else research.text(value['runtime_source_commit']),
            data.machine, data.dll_ref, data.manifest, path))

    def test_01_real_producer_to_complete_public_qualifier(self) -> None:
        result = self.consume()
        self.assertIs(result['full_native_tree_equal'], False)
        self.assertIs(result['compiled_inputs_equal'], True)
        self.assertIs(result['native_compile_commit_is_ancestor'], False)
        self.assertEqual(result['compile_commit'], self.data.native_commit)
        self.assertEqual(result['native_files'], {self.public.NATIVE_PREFIX + 'src/body.cpp':
                                                fixture.signature(self.data.contents['src/body.cpp'])})

    def test_02_original_strict_exact_and_default_paths_reject(self) -> None:
        data = self.data
        with self.assertRaisesRegex(ValueError, 'another Root'):
            self.public.qualify_native(data.qpath, data.repo, data.runtime_commit,
                                       data.machine, data.dll_ref, data.manifest)
        strict = {key: value for key, value in self.proof_value.items()
                  if key not in {'runtime_native_subtree_tree_id', 'full_native_tree_equal',
                                 'compiled_inputs_equal', 'research_delta'}}
        strict['schema'] = 'ck3-native-worktree-exact-tree-source-binding-v1'
        with self.assertRaisesRegex(ValueError, 'different Native Git trees'):
            self.consume(strict)

    def test_03_extra_cpp_or_fourth_python_difference_rejects(self) -> None:
        data = self.data
        for relative in ['src/body.cpp', 'research/other.py']:
            with self.subTest(relative=relative):
                try:
                    (data.native / relative).write_bytes(data.contents[relative] + b'\n')
                    fixture.git(data.repo, 'add', self.public.NATIVE_PREFIX + relative)
                    fixture.git(data.repo, 'commit', '-m', 'Authored forbidden extra change')
                    changed = fixture.git(data.repo, 'rev-parse', 'HEAD')
                    proof = dict(self.proof_value, runtime_source_commit=changed,
                        runtime_native_subtree_tree_id=fixture.git(data.repo, 'rev-parse', changed + ':' + self.public.NATIVE_PREFIX.rstrip('/')))
                    with self.assertRaisesRegex(ValueError, 'three reviewed'):
                        self.consume(proof)
                finally:
                    fixture.git(data.repo, 'reset', '--hard', data.runtime_commit)

    def test_04_forged_pin_and_nonliteral_truth_flags_reject(self) -> None:
        for key, value in [('full_native_tree_equal', 0), ('full_native_tree_equal', True),
                           ('compiled_inputs_equal', 1), ('compiled_inputs_equal', False)]:
            with self.subTest(key=key, value=value):
                with self.assertRaisesRegex(ValueError, 'truthfully preserve'):
                    self.consume(dict(self.proof_value, **{key: value}))
        proof = copy.deepcopy(self.proof_value)
        delta = research.fields(proof['research_delta'])
        delta['reviewed_origin_commit'] = '0' * 40
        proof['research_delta'] = delta
        with self.assertRaisesRegex(ValueError, 'Explicit research delta differs'):
            self.consume(proof)
        proof = copy.deepcopy(self.proof_value)
        delta = research.fields(proof['research_delta'])
        exclusion = research.fields(delta['dependency_exclusion'])
        exclusion['dependency_record_count'] = True
        delta['dependency_exclusion'] = exclusion
        proof['research_delta'] = delta
        with self.assertRaisesRegex(ValueError, 'Explicit research delta differs'):
            self.consume(proof)

    def test_05_actual_fileapi_or_compile_command_inclusion_rejects(self) -> None:
        data = self.data
        relative = research.APPROVED[0][0]
        target = data.evidence / 'api/prod.json'
        raw = target.read_bytes()
        try:
            value = research.read(target)
            value['sources'] = [{'path': relative, 'compileGroupIndex': 0}]
            fixture.write(target, value)
            with self.assertRaisesRegex(ValueError, 'FileAPI target'):
                research.produce_research_delta(root=data.repo, native_repo=data.worktree,
                    runtime_commit=data.runtime_commit, native_commit=data.native_commit,
                    qualification=data.qualification, snapshot=data.snapshot)
        finally:
            target.write_bytes(raw)
        commands = data.evidence / 'commands.json'
        raw = commands.read_bytes()
        try:
            changed = copy.deepcopy(data.qualification)
            scope = research.read(Path(research.checked(changed['configured_scope'])['path']))
            scope['compile_commands'] = fixture.write(commands, [{'file': str(data.wnative / relative),
                                                                 'directory': str(data.evidence / 'build'), 'command': 'AUTHORED'}])
            changed['configured_scope'] = fixture.write(data.evidence / 'changed-scope.json', scope)
            with self.assertRaisesRegex(ValueError, 'compile commands'):
                research.produce_research_delta(root=data.repo, native_repo=data.worktree,
                    runtime_commit=data.runtime_commit, native_commit=data.native_commit,
                    qualification=changed, snapshot=data.snapshot)
        finally:
            commands.write_bytes(raw)

    def test_06_real_dependency_record_and_malformed_records_reject(self) -> None:
        deps = self.data.evidence / 'build/.ninja_deps'
        raw = deps.read_bytes()
        try:
            deps.write_bytes(dependency_log(['body.obj', str(self.data.wnative / research.APPROVED[1][0])]))
            with self.assertRaisesRegex(ValueError, 'actual compiler dependencies'):
                self.consume()
            for bad in [raw[:-1], b'# ninjadeps\n\x03\x00\x00\x00', raw[:16] + struct.pack('<I', 7)]:
                deps.write_bytes(bad)
                with self.assertRaises(ValueError):
                    self.consume()
        finally:
            deps.write_bytes(raw)

    def test_07_nonexception_hidden_raw_drift_and_missing_added_test_reject(self) -> None:
        data = self.data
        relative = self.public.NATIVE_PREFIX + 'include/pin.hpp'
        path = data.repo / relative
        raw = path.read_bytes()
        fixture.git(data.repo, 'update-index', '--assume-unchanged', relative)
        try:
            path.write_bytes(raw + b'// hidden drift\n')
            self.assertEqual(fixture.git(data.repo, 'status', '--porcelain'), '')
            with self.assertRaisesRegex(ValueError, 'raw pin differs'):
                self.consume()
        finally:
            path.write_bytes(raw)
            fixture.git(data.repo, 'update-index', '--no-assume-unchanged', relative)
        proof = copy.deepcopy(self.proof_value)
        delta = research.fields(proof['research_delta'])
        delta['paths'] = research.items(delta['paths'])[:1]
        proof['research_delta'] = delta
        with self.assertRaisesRegex(ValueError, 'Explicit research delta differs'):
            self.consume(proof)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ResearchDelta)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
