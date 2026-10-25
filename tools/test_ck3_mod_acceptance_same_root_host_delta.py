"""Authored source contracts through the real producer and public qualifier.

The inherited miniature Q/File API/Defender rows are explicitly authored data;
these tests never build, execute, register an EXE, or qualify actual live work.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from typing import ClassVar
from uuid import uuid4

import ck3_mod_acceptance_native_source_binding as producer
import test_ck3_mod_acceptance_native_exact_tree_binding as fixture


@dataclass
class WireCase:
    data: fixture.AuthoredInputs
    host_blob: Path
    consumer_blob: Path
    consumer_delta: Path
    host_delta: Path
    host_test_blob: Path | None = None

    def produce(self) -> Path:
        output = self.data.evidence / ('binding-' + uuid4().hex + '.json')
        producer.produce_same_root_host_binding(self.data.repo, self.data.qpath, self.host_delta,
            self.host_blob, output, self.data.machine, noncompiled_consumer_delta=self.consumer_delta,
            original_host_test_blob=self.host_test_blob)
        return output


class SameRootHost(unittest.TestCase):
    temporary: ClassVar[tempfile.TemporaryDirectory[str]]
    data: ClassVar[fixture.AuthoredInputs]
    public: ClassVar[fixture.PublicAPI]
    binding: ClassVar[fixture.BindingAPI]
    delta: ClassVar[dict[str, object]]
    delta_path: ClassVar[Path]
    original: ClassVar[Path]

    @classmethod
    def setUpClass(cls) -> None:
        cls.public, cls.binding, compiled = fixture.load_apis()
        cls.temporary = tempfile.TemporaryDirectory(prefix='ck3-same-root-host-')
        scratch = Path(cls.temporary.name).resolve()
        fixture._active_scratch = scratch
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.data = d = fixture.make_authored_inputs(scratch, cls.public, compiled, same_root=True)
        cls.original = d.evidence / 'original-host.py'
        cls.original.write_bytes(d.contents[producer.HOST_NATIVE_RELATIVE])
        before = producer.host_signature(cls.original.read_bytes())
        after = producer.host_signature((d.repo / producer.HOST_RELATIVE).read_bytes())
        source_delta = fixture.write(d.evidence / 'source-delta.json', {
            'target': producer.HOST_RELATIVE, 'base_source': before,
            'candidate_bytes': after['bytes'], 'candidate_sha256': after['sha256'], 'authored_fixture': True})
        consumer = fixture.write(d.evidence / 'consumer.json', {
            'machine_id': d.machine, 'result': 'PASS', 'original_wait_returncode': 0, 'skipped': 0,
            'pins': {source_delta['path']: {'bytes': source_delta['bytes'], 'sha256': source_delta['sha256']}},
            'authored_fixture_not_actual_tests': True})
        review = fixture.write(d.evidence / 'review.json', {
            'schema': 'ck3-reviewed-canonical-shared-python-host-change-v1', 'machine_id': d.machine,
            'result': 'PASS', 'canonical_repo_relative': producer.HOST_RELATIVE,
            'source_classification': 'shared_host', 'before': before, 'after': after,
            'actual_live_business_qualified': False, 'source_consumer': consumer, 'source_delta': source_delta,
            'authored_fixture_not_actual_review': True})
        qualification = fixture.write(d.evidence / 'shared-host-qualification.json', {
            'machine_id': d.machine, 'source_commit': d.runtime_commit, 'result': 'PASS', 'exit_code': 0,
            'skipped': 0, 'tests_run': 1, 'covered_chains': ['shared_host'],
            'source_pins': [producer.host_pin(d.repo / producer.HOST_RELATIVE)],
            'source_consumer': consumer, 'source_delta': source_delta, 'reviewed_host_change': review,
            'authored_fixture_not_actual_tests': True})
        cls.delta = {'schema': producer.HOST_DELTA_SCHEMA, 'machine_id': d.machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat(),
            'runtime_source_commit': d.runtime_commit, 'native_source_commit': d.native_commit,
            'canonical_repo_relative': producer.HOST_RELATIVE, 'source_classification': 'shared_host',
            'before': before, 'after': after, 'qualified_native': d.qref, 'snapshot': d.snapshot_ref,
            'compiled_inputs': compiled.compiled_inputs(d.qualification, d.snapshot),
            'reviewed_host_change': review, 'shared_host_qualification': qualification}
        cls.delta_path = d.evidence / 'delta.json'
        fixture.write(cls.delta_path, cls.delta)

    @classmethod
    def tearDownClass(cls) -> None:
        fixture._active_scratch = None

    def produce(self) -> Path:
        path = self.data.evidence / ('binding-' + uuid4().hex + '.json')
        producer.produce_same_root_host_binding(self.data.repo, self.data.qpath, self.delta_path,
                                 self.original, path, self.data.machine)
        return path

    def consume(self, path: Path) -> dict[str, object]:
        d = self.data
        return fixture.object_fields(self.public.qualify_native(d.qpath, d.repo, d.runtime_commit,
            d.machine, d.dll_ref, d.manifest, path, self.delta_path))

    def test_01_actual_producer_to_complete_public_qualifier(self) -> None:
        before = {path: producer.host_pin(path) for path in (self.data.qpath, Path(self.data.snapshot_ref['path']),
                  Path(self.data.dll_ref['path']))}
        path = self.produce()
        result = self.consume(path)
        self.assertEqual(result['compile_commit'], self.data.native_commit)
        self.assertEqual(result['source_checkout_binding'], producer.host_pin(path))
        self.assertEqual(result['native_files'], {producer.NATIVE_PREFIX + 'src/body.cpp':
                                                producer.host_signature(self.data.contents['src/body.cpp'])})
        self.assertEqual(before, {path: producer.host_pin(path) for path in before})

    def test_02_same_root_without_opt_in_still_rejects_changed_host(self) -> None:
        d = self.data
        with self.assertRaises(ValueError):
            self.public.qualify_native(d.qpath, d.repo, d.runtime_commit, d.machine, d.dll_ref, d.manifest)

    def test_03_json_roundtrip_retains_exact_public_result(self) -> None:
        result = self.consume(self.produce())
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_04_original_blob_is_exact_git_content(self) -> None:
        path = self.produce()
        value = producer.host_read(path)
        wrong = self.data.evidence / 'wrong-original.py'
        wrong.write_bytes(b'HOST = 999\n')
        value['original_shared_host_blob'] = producer.host_pin(wrong)
        fixture.write(path, value)
        with self.assertRaisesRegex(ValueError, 'actual old Git content'):
            self.consume(path)

    def test_05_other_committed_native_change_is_rejected(self) -> None:
        d = self.data
        changed = d.native / 'research/other.py'
        try:
            changed.write_bytes(b'OTHER = 1\n')
            fixture.git(d.repo, 'add', producer.NATIVE_PREFIX + 'research/other.py')
            fixture.git(d.repo, 'commit', '-m', 'Authored disallowed second Native delta')
            with self.assertRaisesRegex(ValueError, 'exactly the canonical host'):
                self.produce()
        finally:
            fixture.git(d.repo, 'reset', '--hard', d.runtime_commit)

    def test_06_clean_git_cannot_hide_nonhost_raw_change(self) -> None:
        path = self.produce()
        relative = producer.NATIVE_PREFIX + 'include/pin.hpp'
        raw_path = self.data.repo / relative
        before = raw_path.read_bytes()
        fixture.git(self.data.repo, 'update-index', '--assume-unchanged', relative)
        try:
            raw_path.write_bytes(before + b'// hidden\n')
            with self.assertRaisesRegex(ValueError, 'Non-host Native raw input changed'):
                self.consume(path)
        finally:
            raw_path.write_bytes(before)
            fixture.git(self.data.repo, 'update-index', '--no-assume-unchanged', relative)

    def test_07_compiled_count_rejects_boolean_and_fingerprint_change(self) -> None:
        for field, bad in (('unique_production_source_count', True), ('production_source_set_sha256', '0' * 64)):
            with self.subTest(field=field):
                delta = copy.deepcopy(self.delta)
                counts = fixture.object_fields(delta['compiled_inputs'])
                counts[field] = bad
                delta['compiled_inputs'] = counts
                try:
                    fixture.write(self.delta_path, delta)
                    with self.assertRaises(ValueError):
                        self.produce()
                finally:
                    fixture.write(self.delta_path, self.delta)

    def test_08_schema_missing_or_wrong_field_rejected(self) -> None:
        for field, bad in (('original_shared_host_blob', None), ('runtime_source_commit', True),
                           ('schema', 'ck3-native-worktree-source-binding-v1')):
            with self.subTest(field=field):
                path = self.produce()
                value = producer.host_read(path)
                if bad is None:
                    del value[field]
                else:
                    value[field] = bad
                fixture.write(path, value)
                with self.assertRaises(ValueError):
                    self.consume(path)

    def test_09_legacy_delta_schema_cannot_opt_into_same_root(self) -> None:
        try:
            fixture.write(self.delta_path, dict(self.delta, schema='ck3-exact-shared-python-host-delta-v1'))
            with self.assertRaisesRegex(ValueError, 'same-root delta schema'):
                self.produce()
        finally:
            fixture.write(self.delta_path, self.delta)

    def test_10_binding_requires_explicit_delta_argument(self) -> None:
        d = self.data
        with self.assertRaisesRegex(ValueError, 'Explicit reviewed same-root'):
            self.binding.qualified_native_source_checkout(self.produce(), root=d.repo,
                runtime_commit=d.runtime_commit, native_commit=d.native_commit, machine=d.machine,
                qualified_native_ref=d.qref, qualification=d.qualification, snapshot_ref=d.snapshot_ref,
                snapshot=d.snapshot)

    def test_11_alternate_checkout_shared_host_contract_still_works(self) -> None:
        d = self.data
        old_path = d.evidence / 'legacy-worktree-delta.json'
        fixture.write(old_path, dict(self.delta, schema='ck3-exact-shared-python-host-delta-v1'))
        result = fixture.object_fields(producer.host_shared_api().qualify_shared_host_delta(old_path,
            root=d.repo, native_repo=d.worktree, runtime_commit=d.runtime_commit, native_commit=d.native_commit,
            machine=d.machine, qualified_native_ref=d.qref, qualification=d.qualification,
            snapshot_ref=d.snapshot_ref, snapshot=d.snapshot))
        self.assertEqual(result['runtime_host_pin'], producer.host_pin(d.repo / producer.HOST_RELATIVE))

    def test_12_reviewed_consumer_cannot_claim_boolean_zero_wait(self) -> None:
        d = self.data
        consumer_path = d.evidence / 'consumer.json'
        consumer_before = consumer_path.read_bytes()
        review_path = d.evidence / 'review.json'
        review_before = review_path.read_bytes()
        qpath = d.evidence / 'shared-host-qualification.json'
        qbefore = qpath.read_bytes()
        try:
            consumer = producer.host_read(consumer_path)
            consumer['original_wait_returncode'] = False
            fixture.write(consumer_path, consumer)
            review = producer.host_read(review_path)
            review['source_consumer'] = producer.host_pin(consumer_path)
            fixture.write(review_path, review)
            shared = producer.host_read(qpath)
            shared['source_consumer'] = producer.host_pin(consumer_path)
            shared['reviewed_host_change'] = producer.host_pin(review_path)
            fixture.write(qpath, shared)
            delta = dict(self.delta, reviewed_host_change=producer.host_pin(review_path),
                         shared_host_qualification=producer.host_pin(qpath))
            fixture.write(self.delta_path, delta)
            with self.assertRaisesRegex(ValueError, 'original zero wait'):
                self.produce()
        finally:
            consumer_path.write_bytes(consumer_before)
            review_path.write_bytes(review_before)
            qpath.write_bytes(qbefore)
            fixture.write(self.delta_path, self.delta)

    def fixture_case(self) -> tuple[fixture.AuthoredInputs, Path, Path, Path]:
        scratch = self.data.evidence / ('fixture-' + uuid4().hex)
        scratch.mkdir()
        _, _, compiled = fixture.load_apis()
        d = fixture.make_authored_inputs(scratch, self.public, compiled, same_root=True, fixture_cmake=True)
        original = d.evidence / 'old.cmake'
        original.write_bytes(d.contents[producer.FIXTURE_CMAKE_RELATIVE])
        current = d.native / producer.FIXTURE_CMAKE_RELATIVE
        current.write_bytes(original.read_bytes().replace(b'    xar_ck3_12002_runtime)',
                                                        b'    xar_ck3_12002_runtime xar_bridge_protocol)'))
        fixture.git(d.repo, 'add', producer.NATIVE_PREFIX + producer.FIXTURE_CMAKE_RELATIVE)
        fixture.git(d.repo, 'commit', '-m', 'Authored fixture-only link completion')
        d.runtime_commit = fixture.git(d.repo, 'rev-parse', 'HEAD')
        shared_ref = producer.host_parse_pin(self.delta['shared_host_qualification'])
        shared = producer.host_read(Path(shared_ref['path']))
        shared['source_commit'] = d.runtime_commit
        shared['source_pins'] = [producer.host_pin(d.repo / producer.HOST_RELATIVE)]
        shared_new = fixture.write(d.evidence / 'shared-host-qualified.json', shared)
        delta = dict(self.delta, runtime_source_commit=d.runtime_commit, native_source_commit=d.native_commit, qualified_native=d.qref,
            snapshot=d.snapshot_ref, shared_host_qualification=shared_new,
            compiled_inputs=compiled.compiled_inputs(d.qualification, d.snapshot))
        delta_path = d.evidence / 'host-delta.json'
        fixture.write(delta_path, delta)
        old_host = d.evidence / 'old-host.py'
        old_host.write_bytes(d.contents[producer.HOST_NATIVE_RELATIVE])
        return d, original, delta_path, old_host

    def test_13_fixture_link_completion_producer_to_public_consumer(self) -> None:
        d, old_cmake, delta_path, old_host = self.fixture_case()
        binding = d.evidence / 'binding.json'
        producer.produce_same_root_host_binding(d.repo, d.qpath, delta_path, old_host, binding, d.machine,
            original_fixture_cmake_blob=old_cmake, fixture_link_receipt=d.evidence / 'fixture-link.json')
        result = fixture.object_fields(self.public.qualify_native(d.qpath, d.repo, d.runtime_commit,
            d.machine, d.dll_ref, d.manifest, binding, delta_path))
        self.assertEqual(result['compile_commit'], d.native_commit)
        self.assertEqual(result['native_files'], {producer.NATIVE_PREFIX + 'src/body.cpp':
                                                producer.host_signature(d.contents['src/body.cpp'])})

    def test_14_other_cmake_edit_is_rejected(self) -> None:
        d, old_cmake, _, _ = self.fixture_case()
        current = d.native / producer.FIXTURE_CMAKE_RELATIVE
        current.write_bytes(current.read_bytes() + b'add_library(injected src/body.cpp)\n')
        fixture.git(d.repo, 'add', '.')
        fixture.git(d.repo, 'commit', '-m', 'Authored forbidden CMake edit')
        proof = {'schema': 'ck3-exact-fixture-cmake-link-completion-v1',
            'original_blob': producer.host_pin(old_cmake),
            'fixture_link_receipt': producer.host_pin(d.evidence / 'fixture-link.json')}
        with self.assertRaisesRegex(ValueError, 'Only the known fixture'):
            producer.qualify_fixture_cmake_delta(proof, root=d.repo, native_commit=d.native_commit,
                runtime_commit=fixture.git(d.repo, 'rev-parse', 'HEAD'), machine=d.machine,
                qualification=d.qualification, snapshot=d.snapshot)

    def test_15_link_response_must_prove_existing_protocol_archive(self) -> None:
        d, old_cmake, _, _ = self.fixture_case()
        rsp = d.evidence / 'build/fixture.rsp'
        rsp.write_text('/OUT:' + str(d.dll_ref['path']), encoding='utf-8')
        link_path = d.evidence / 'fixture-link.json'
        link = producer.host_read(link_path)
        link['response_files'] = [producer.host_pin(rsp)]
        fixture.write(link_path, link)
        proof = {'schema': 'ck3-exact-fixture-cmake-link-completion-v1',
            'original_blob': producer.host_pin(old_cmake), 'fixture_link_receipt': producer.host_pin(link_path)}
        with self.assertRaisesRegex(ValueError, 'protocol archive'):
            producer.qualify_fixture_cmake_delta(proof, root=d.repo, native_commit=d.native_commit,
                runtime_commit=d.runtime_commit, machine=d.machine, qualification=d.qualification, snapshot=d.snapshot)

    def test_16_fixture_delta_requires_actual_link_receipt(self) -> None:
        d, old_cmake, delta, old_host = self.fixture_case()
        with self.assertRaisesRegex(ValueError, 'supplied together'):
            producer.produce_same_root_host_binding(d.repo, d.qpath, delta, old_host,
                d.evidence / 'refused.json', d.machine, original_fixture_cmake_blob=old_cmake)

    def inactive_case(self) -> tuple[fixture.AuthoredInputs, Path, Path, Path]:
        scratch = self.data.evidence / ('inactive-' + uuid4().hex)
        scratch.mkdir()
        _, _, compiled = fixture.load_apis()
        d = fixture.make_authored_inputs(scratch, self.public, compiled, same_root=True, inactive_cmake=True)
        old_cmake = d.evidence / 'old-CMakeLists.txt'
        old_cmake.write_bytes(d.contents['CMakeLists.txt'])
        current = d.native / 'CMakeLists.txt'
        after = old_cmake.read_bytes()
        for old, new in zip(producer.INACTIVE_CMAKE_BEFORE, producer.INACTIVE_CMAKE_AFTER):
            after = after.replace(old, new)
        current.write_bytes(after)
        fixture.git(d.repo, 'add', producer.NATIVE_PREFIX + 'CMakeLists.txt')
        fixture.git(d.repo, 'commit', '-m', 'Authored inactive prisoner wire relocation')
        d.runtime_commit = fixture.git(d.repo, 'rev-parse', 'HEAD')
        shared_ref = producer.host_parse_pin(self.delta['shared_host_qualification'])
        shared = producer.host_read(Path(shared_ref['path']))
        shared['source_commit'] = d.runtime_commit
        shared['source_pins'] = [producer.host_pin(d.repo / producer.HOST_RELATIVE)]
        shared_new = fixture.write(d.evidence / 'shared-host-qualified.json', shared)
        delta = dict(self.delta, runtime_source_commit=d.runtime_commit, native_source_commit=d.native_commit,
            qualified_native=d.qref, snapshot=d.snapshot_ref, shared_host_qualification=shared_new,
            compiled_inputs=compiled.compiled_inputs(d.qualification, d.snapshot))
        delta_path = d.evidence / 'host-delta.json'
        fixture.write(delta_path, delta)
        old_host = d.evidence / 'old-host.py'
        old_host.write_bytes(d.contents[producer.HOST_NATIVE_RELATIVE])
        proof = d.evidence / 'inactive-proof.json'
        fixture.write(proof, {'schema': 'ck3-exact-inactive-prisoner-cmake-relocation-v1',
            'original_blob': producer.host_pin(old_cmake),
            'configured_cache': producer.host_pin(d.evidence / 'build/CMakeCache.txt'),
            'configure_execution': producer.host_pin(d.evidence / 'configure.json')})
        return d, proof, delta_path, old_host

    def inactive_produce(self, case: tuple[fixture.AuthoredInputs, Path, Path, Path]) -> Path:
        d, proof, delta, old_host = case
        output = d.evidence / ('inactive-binding-' + uuid4().hex + '.json')
        producer.produce_same_root_host_binding(d.repo, d.qpath, delta, old_host, output, d.machine,
                                               inactive_cmake_delta=proof)
        return output

    def test_inactive_cmake_actual_producer_to_complete_public_qualifier(self) -> None:
        case = self.inactive_case()
        d, _, delta, _ = case
        original_q, original_dll = producer.host_pin(d.qpath), producer.host_pin(Path(d.dll_ref['path']))
        output = self.inactive_produce(case)
        result = fixture.object_fields(self.public.qualify_native(d.qpath, d.repo, d.runtime_commit,
            d.machine, d.dll_ref, d.manifest, output, delta))
        self.assertEqual(result['compile_commit'], d.native_commit)
        self.assertEqual(result['native_files'], {producer.NATIVE_PREFIX + 'src/body.cpp':
                                                producer.host_signature(d.contents['src/body.cpp'])})
        self.assertEqual(json.loads(json.dumps(producer.host_read(output))), producer.host_read(output))
        self.assertEqual(original_q, producer.host_pin(d.qpath))
        self.assertEqual(original_dll, producer.host_pin(Path(d.dll_ref['path'])))

    def test_inactive_cmake_without_explicit_proof_retains_real_failure(self) -> None:
        d, _, delta, old_host = self.inactive_case()
        with self.assertRaisesRegex(ValueError, 'exactly the canonical host'):
            producer.produce_same_root_host_binding(d.repo, d.qpath, delta, old_host,
                d.evidence / 'old-route-rejected.json', d.machine)

    def test_inactive_cmake_profile_missing_null_boolean_or_on_is_rejected(self) -> None:
        for bad in (None, True, 'ON', 'OFF '):
            with self.subTest(bad=bad):
                case = self.inactive_case()
                d, proof_path, _, _ = case
                profile_path = Path(producer.host_parse_pin(d.qualification['profile'])['path'])
                profile = producer.host_read(profile_path)
                flags = producer.host_obj(profile['flags'])
                if bad is None:
                    del flags[producer.INACTIVE_CMAKE_FLAGS[0]]
                else:
                    flags[producer.INACTIVE_CMAKE_FLAGS[0]] = bad
                profile['flags'] = flags
                fixture.write(profile_path, profile)
                q = dict(d.qualification, profile=producer.host_pin(profile_path))
                with self.assertRaisesRegex(ValueError, 'qualified prisoner flags'):
                    producer.qualify_inactive_cmake_delta(producer.host_read(proof_path), root=d.repo,
                        native_commit=d.native_commit, runtime_commit=d.runtime_commit, machine=d.machine,
                        qualification=q, snapshot=d.snapshot)

    def test_inactive_cmake_cache_on_missing_or_duplicate_is_rejected(self) -> None:
        for bad in (b':BOOL=ON', b':STRING=OFF', b''):
            with self.subTest(bad=bad):
                case = self.inactive_case()
                d, proof_path, _, _ = case
                proof = producer.host_read(proof_path)
                cache = Path(producer.host_parse_pin(proof['configured_cache'])['path'])
                flag = producer.INACTIVE_CMAKE_FLAGS[1].encode('ascii')
                cache.write_bytes(cache.read_bytes().replace(flag + b':BOOL=OFF', flag + bad))
                proof['configured_cache'] = producer.host_pin(cache)
                fixture.write(proof_path, proof)
                with self.assertRaisesRegex(ValueError, 'cached prisoner flags'):
                    self.inactive_produce(case)

    def test_inactive_cmake_extra_committed_edit_is_rejected(self) -> None:
        case = self.inactive_case()
        d = case[0]
        current = d.native / 'CMakeLists.txt'
        current.write_bytes(current.read_bytes() + b'add_library(injected src/body.cpp)\n')
        fixture.git(d.repo, 'add', '.')
        fixture.git(d.repo, 'commit', '-m', 'Authored extra CMake edit rejected')
        with self.assertRaisesRegex(ValueError, 'exact inactive prisoner'):
            self.inactive_produce(case)

    def test_inactive_cmake_selected_cpp_change_is_rejected(self) -> None:
        case = self.inactive_case()
        d = case[0]
        (d.native / 'src/body.cpp').write_bytes(b'int changed;\n')
        fixture.git(d.repo, 'add', '.')
        fixture.git(d.repo, 'commit', '-m', 'Authored compiled change rejected')
        with self.assertRaisesRegex(ValueError, 'exactly the canonical host'):
            self.inactive_produce(case)

    def test_inactive_cmake_original_configure_identity_and_wait_are_strict(self) -> None:
        for field, bad in (('original_wait_returncode', False), ('source_commit', '0' * 40),
                           ('game_started_or_attached', True)):
            with self.subTest(field=field):
                case = self.inactive_case()
                d, proof_path, _, _ = case
                proof = producer.host_read(proof_path)
                execution_path = Path(producer.host_parse_pin(proof['configure_execution'])['path'])
                execution = producer.host_read(execution_path)
                execution[field] = bad
                fixture.write(execution_path, execution)
                proof['configure_execution'] = producer.host_pin(execution_path)
                fixture.write(proof_path, proof)
                with self.assertRaisesRegex(ValueError, 'actual zero-wait configure'):
                    self.inactive_produce(case)

    def test_inactive_cmake_wire_in_compile_commands_is_rejected(self) -> None:
        case = self.inactive_case()
        d = case[0]
        commands = d.evidence / 'build/compile_commands.json'
        fixture.write(commands, [{'file': str(d.native / 'src/player_prisoner_ransom_wire_v1.cpp'),
                                  'command': 'AUTHORED NOT RUN',
                                  'output': 'CMakeFiles/xar_ck3_bridge.dir/src/wire.cpp.obj'}])
        proof = producer.host_read(case[1])
        scope = producer.host_read(Path(producer.host_parse_pin(d.qualification['configured_scope'])['path']))
        scope['compile_commands'] = producer.host_pin(commands)
        scope_ref = fixture.write(d.evidence / 'changed-scope.json', scope)
        with self.assertRaisesRegex(ValueError, 'actual production compiler commands'):
            producer.qualify_inactive_cmake_delta(proof, root=d.repo, native_commit=d.native_commit,
                runtime_commit=d.runtime_commit, machine=d.machine,
                qualification=dict(d.qualification, configured_scope=scope_ref), snapshot=d.snapshot)

    def test_inactive_cmake_wire_in_production_fileapi_is_rejected(self) -> None:
        case = self.inactive_case()
        d = case[0]
        target = d.evidence / 'api/prod.json'
        row = producer.host_read(target)
        row['sources'] = [{'path': 'src/player_prisoner_ransom_wire_v1.cpp', 'compileGroupIndex': 0}]
        fixture.write(target, row)
        with self.assertRaisesRegex(ValueError, 'actual production File API target'):
            self.inactive_produce(case)

    def wire_case(self, *, host_test: bool = False) -> WireCase:
        scratch = self.data.evidence / ('wire-' + uuid4().hex)
        scratch.mkdir()
        _, _, compiled = fixture.load_apis()
        d = fixture.make_authored_inputs(scratch, self.public, compiled, same_root=True,
            wire_consumer=True, host_test_companion=host_test)
        relative = producer.NATIVE_PREFIX + producer.NONCOMPILED_CONSUMER_RELATIVE
        current = d.repo / relative
        current.write_bytes(b'CONSUMER = 1\n')
        if host_test:
            (d.native / producer.HOST_TEST_COMPANION_RELATIVE).write_bytes(b'TEST = 1\n')
            fixture.git(d.repo, 'add', producer.NATIVE_PREFIX + producer.HOST_TEST_COMPANION_RELATIVE)
        fixture.git(d.repo, 'add', relative)
        fixture.git(d.repo, 'commit', '-m', 'Authored sole refill wire consumer migration')
        d.runtime_commit = fixture.git(d.repo, 'rev-parse', 'HEAD')
        old_host, old_consumer = d.evidence / 'old-host.py', d.evidence / 'old-consumer.py'
        old_host.write_bytes(d.contents[producer.HOST_NATIVE_RELATIVE])
        old_consumer.write_bytes(d.contents[producer.NONCOMPILED_CONSUMER_RELATIVE])
        old_test: Path | None = None
        test_change: producer.WireConsumerContext | None = None
        if host_test:
            old_test = d.evidence / 'old-test.py'
            old_test.write_bytes(d.contents[producer.HOST_TEST_COMPANION_RELATIVE])
            test_change = {'before_blob': producer.host_pin(old_test),
                'after': producer.host_pin(d.native / producer.HOST_TEST_COMPANION_RELATIVE)}
        host_before, host_after = producer.host_signature(old_host.read_bytes()), producer.host_signature((d.repo / producer.HOST_RELATIVE).read_bytes())
        before, after = producer.host_signature(old_consumer.read_bytes()), producer.host_signature(current.read_bytes())
        host_delta = fixture.write(d.evidence / 'host-source-delta.json', {'target': producer.HOST_RELATIVE,
            'base_source': host_before, 'candidate_bytes': host_after['bytes'], 'candidate_sha256': host_after['sha256']})
        reader_delta = fixture.write(d.evidence / 'reader-source-delta.json', {'target': relative,
            'base_source': before, 'candidate_bytes': after['bytes'], 'candidate_sha256': after['sha256']})
        consumer = fixture.write(d.evidence / 'consumer.json', {'machine_id': d.machine, 'result': 'PASS',
            'original_wait_returncode': 0, 'skipped': 0, 'authored_fixture_not_actual_tests': True,
            'pins': {ref['path']: {'bytes': ref['bytes'], 'sha256': ref['sha256']} for ref in (host_delta, reader_delta)}})
        if test_change is not None:
            consumer_value = producer.host_read(Path(consumer['path']))
            pins = producer.host_obj(consumer_value['pins'])
            test_pin = test_change['after']
            pins[test_pin['path']] = {'bytes': test_pin['bytes'], 'sha256': test_pin['sha256']}
            consumer_value['pins'] = pins
            consumer = fixture.write(Path(consumer['path']), consumer_value)
        review = fixture.write(d.evidence / 'host-review.json', {
            'schema': 'ck3-reviewed-canonical-shared-python-host-change-v1', 'machine_id': d.machine,
            'result': 'PASS', 'canonical_repo_relative': producer.HOST_RELATIVE,
            'source_classification': 'shared_host', 'before': host_before, 'after': host_after,
            'actual_live_business_qualified': False, 'source_consumer': consumer, 'source_delta': host_delta})
        if test_change is not None:
            review_value = producer.host_read(Path(review['path']))
            review_value['host_test_change'] = test_change
            review = fixture.write(Path(review['path']), review_value)
        reader_review = fixture.write(d.evidence / 'reader-review.json', {
            'schema': 'ck3-reviewed-refill-wire-consumer-change-v1', 'machine_id': d.machine,
            'result': 'PASS', 'canonical_repo_relative': relative, 'before': before, 'after': after,
            'actual_live_business_qualified': False, 'source_consumer': consumer, 'source_delta': reader_delta})
        reader_proof = fixture.write(d.evidence / 'reader-delta.json', {
            'schema': producer.WIRE_CONSUMER_DELTA_SCHEMA, 'machine_id': d.machine,
            'runtime_source_commit': d.runtime_commit, 'native_source_commit': d.native_commit,
            'canonical_repo_relative': relative, 'before_blob': producer.host_pin(old_consumer),
            'after': producer.host_pin(current), 'source_delta': reader_delta, 'source_consumer': consumer,
            'reviewed_change': reader_review})
        qualification = fixture.write(d.evidence / 'shared-host-qualified.json', {
            'machine_id': d.machine, 'source_commit': d.runtime_commit, 'result': 'PASS', 'exit_code': 0,
            'skipped': 0, 'tests_run': 1, 'covered_chains': ['shared_host'],
            'source_pins': [producer.host_pin(d.repo / producer.HOST_RELATIVE), producer.host_pin(current)],
            'source_consumer': consumer, 'source_delta': host_delta, 'reviewed_host_change': review,
            'noncompiled_consumer_delta': reader_proof, 'authored_fixture_not_actual_tests': True})
        if test_change is not None:
            qualification_value = producer.host_read(Path(qualification['path']))
            qualification_value['host_test_change'] = test_change
            qualification_value['source_pins'] = [producer.host_pin(d.repo / producer.HOST_RELATIVE),
                producer.host_pin(current), test_change['after']]
            qualification = fixture.write(Path(qualification['path']), qualification_value)
        delta_path = d.evidence / 'host-delta.json'
        fixture.write(delta_path, {'schema': producer.HOST_CONSUMER_DELTA_SCHEMA, 'machine_id': d.machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'runtime_source_commit': d.runtime_commit,
            'native_source_commit': d.native_commit, 'canonical_repo_relative': producer.HOST_RELATIVE,
            'source_classification': 'shared_host', 'before': host_before, 'after': host_after,
            'qualified_native': d.qref, 'snapshot': d.snapshot_ref,
            'compiled_inputs': compiled.compiled_inputs(d.qualification, d.snapshot),
            'reviewed_host_change': review, 'shared_host_qualification': qualification,
            'noncompiled_consumer_delta': reader_proof})
        if test_change is not None:
            delta_value = producer.host_read(delta_path)
            delta_value['host_test_change'] = test_change
            fixture.write(delta_path, delta_value)
        return WireCase(d, old_host, old_consumer, Path(reader_proof['path']), delta_path, old_test)

    def test_17_refill_reader_producer_to_complete_public_consumer(self) -> None:
        case = self.wire_case()
        d = case.data
        before = {p: producer.host_pin(p) for p in (d.qpath, Path(d.snapshot_ref['path']), Path(d.dll_ref['path']))}
        binding = case.produce()
        result = fixture.object_fields(self.public.qualify_native(d.qpath, d.repo, d.runtime_commit,
            d.machine, d.dll_ref, d.manifest, binding, case.host_delta))
        self.assertEqual(result['compile_commit'], d.native_commit)
        self.assertEqual(json.loads(json.dumps(result)), result)
        self.assertEqual(before, {p: producer.host_pin(p) for p in before})
        context = producer.qualify_same_root_host(binding, root=d.repo, runtime_commit=d.runtime_commit,
            native_commit=d.native_commit, machine=d.machine, qualified_native_ref=d.qref,
            qualification=d.qualification, snapshot_ref=d.snapshot_ref, snapshot=d.snapshot,
            native_shared_python_host_delta=case.host_delta)
        self.assertEqual(context['noncompiled_replay']['binding'], producer.host_pin(binding))
        self.assertEqual(context['original_research_blobs'],
            {producer.NONCOMPILED_CONSUMER_RELATIVE: producer.host_pin(case.consumer_blob)})

    def test_18_legacy_host_opt_in_cannot_silently_allow_refill_change(self) -> None:
        case = self.wire_case()
        with self.assertRaisesRegex(ValueError, 'exactly the canonical host'):
            producer.produce_same_root_host_binding(case.data.repo, case.data.qpath, case.host_delta,
                case.host_blob, case.data.evidence / 'legacy-binding.json', case.data.machine)

    def test_19_refill_delta_rejects_wrong_path_missing_and_boolean_identity(self) -> None:
        case = self.wire_case()
        original = producer.host_read(case.consumer_delta)
        for field, value in [('canonical_repo_relative', producer.NATIVE_PREFIX + 'research/other.py'),
                             ('native_source_commit', True), ('before_blob', None)]:
            with self.subTest(field=field):
                row = dict(original)
                if value is None:
                    del row[field]
                else:
                    row[field] = value
                fixture.write(case.consumer_delta, row)
                with self.assertRaises(ValueError):
                    case.produce()
        fixture.write(case.consumer_delta, original)

    def test_20_refill_before_blob_must_match_original_git(self) -> None:
        case = self.wire_case()
        case.consumer_blob.write_bytes(b'CONSUMER = 999\n')
        row = producer.host_read(case.consumer_delta)
        row['before_blob'] = producer.host_pin(case.consumer_blob)
        fixture.write(case.consumer_delta, row)
        with self.assertRaisesRegex(ValueError, 'actual regular Git blob'):
            case.produce()

    def test_21_refill_must_not_enter_any_actual_fileapi_target(self) -> None:
        case = self.wire_case()
        target = case.data.evidence / 'api/fixture.json'
        row = producer.host_read(target)
        row['sources'] = [{'path': producer.NONCOMPILED_CONSUMER_RELATIVE}]
        fixture.write(target, row)
        with self.assertRaisesRegex(ValueError, 'actual File API target'):
            case.produce()

    def test_22_refill_must_not_enter_actual_compile_commands(self) -> None:
        case = self.wire_case()
        d = case.data
        scope_ref = producer.host_parse_pin(d.qualification['configured_scope'])
        scope = producer.host_read(Path(scope_ref['path']))
        commands = Path(producer.host_parse_pin(scope['compile_commands'])['path'])
        command_ref = fixture.write(commands, [{'file': str(d.native / 'src/body.cpp'),
            'directory': str(d.evidence / 'build'), 'command': producer.NONCOMPILED_CONSUMER_RELATIVE}])
        # Refresh the authored outer references; a pin failure alone is not this regression.
        scope['compile_commands'] = command_ref
        new_scope = fixture.write(Path(scope_ref['path']), scope)
        d.qualification['configured_scope'] = new_scope
        fixture.write(d.qpath, d.qualification)
        with self.assertRaisesRegex(ValueError, 'compiler command argument'):
            producer.qualify_wire_consumer_delta(producer.host_pin(case.consumer_delta), root=d.repo,
                native_commit=d.native_commit, runtime_commit=d.runtime_commit, machine=d.machine,
                qualification=d.qualification, snapshot=d.snapshot)

    def test_23_refill_review_consumer_rejects_boolean_wait_and_skip(self) -> None:
        case = self.wire_case()
        d = case.data
        proof = producer.host_read(case.consumer_delta)
        consumer_path = Path(producer.host_parse_pin(proof['source_consumer'])['path'])
        original = producer.host_read(consumer_path)
        for key, value in [('original_wait_returncode', False), ('skipped', 1)]:
            with self.subTest(key=key):
                fixture.write(consumer_path, dict(original, **{key: value}))
                row = dict(proof, source_consumer=producer.host_pin(consumer_path))
                fixture.write(case.consumer_delta, row)
                with self.assertRaisesRegex(ValueError, 'zero-skip refill source consumer'):
                    producer.qualify_wire_consumer_delta(producer.host_pin(case.consumer_delta), root=d.repo,
                        native_commit=d.native_commit, runtime_commit=d.runtime_commit, machine=d.machine,
                        qualification=d.qualification, snapshot=d.snapshot)

    def test_24_refill_opt_in_still_rejects_an_unreviewed_third_native_change(self) -> None:
        case = self.wire_case()
        d = case.data
        (d.native / 'research/other.py').write_bytes(b'OTHER = 99\n')
        fixture.git(d.repo, 'add', '.')
        fixture.git(d.repo, 'commit', '-m', 'Authored forbidden third Native path')
        with self.assertRaises(ValueError):
            case.produce()

    def test_25_fixed_host_test_companion_through_complete_public_qualifier(self) -> None:
        case = self.wire_case(host_test=True)
        d = case.data
        binding = case.produce()
        result = fixture.object_fields(self.public.qualify_native(d.qpath, d.repo, d.runtime_commit,
            d.machine, d.dll_ref, d.manifest, binding, case.host_delta))
        self.assertEqual(result['compile_commit'], d.native_commit)
        context = producer.qualify_same_root_host(binding, root=d.repo, runtime_commit=d.runtime_commit,
            native_commit=d.native_commit, machine=d.machine, qualified_native_ref=d.qref,
            qualification=d.qualification, snapshot_ref=d.snapshot_ref, snapshot=d.snapshot,
            native_shared_python_host_delta=case.host_delta)
        self.assertEqual(set(context['original_research_blobs']),
            {producer.NONCOMPILED_CONSUMER_RELATIVE, producer.HOST_TEST_COMPANION_RELATIVE})

    def test_26_host_test_companion_must_be_independently_reviewed(self) -> None:
        case = self.wire_case(host_test=True)
        delta = producer.host_read(case.host_delta)
        review_path = Path(producer.host_parse_pin(delta['reviewed_host_change'])['path'])
        review = producer.host_read(review_path)
        del review['host_test_change']
        delta['reviewed_host_change'] = fixture.write(review_path, review)
        fixture.write(case.host_delta, delta)
        with self.assertRaisesRegex(ValueError, 'exact test companion'):
            case.produce()

    def test_27_host_test_companion_requires_original_git_bytes(self) -> None:
        case = self.wire_case(host_test=True)
        self.assertIsNotNone(case.host_test_blob)
        if case.host_test_blob is None:
            raise AssertionError('Authored host test blob missing')
        case.host_test_blob.write_bytes(b'TEST = 999\n')
        with self.assertRaises(ValueError):
            case.produce()

    def test_28_host_test_companion_cannot_enter_actual_fileapi(self) -> None:
        case = self.wire_case(host_test=True)
        target = case.data.evidence / 'api/fixture.json'
        row = producer.host_read(target)
        row['sources'] = [{'path': producer.HOST_TEST_COMPANION_RELATIVE}]
        fixture.write(target, row)
        with self.assertRaisesRegex(ValueError, 'actual File API target'):
            case.produce()

    def test_29_host_test_companion_cannot_use_an_unexecuted_source_pin(self) -> None:
        case = self.wire_case(host_test=True)
        d = case.data
        delta = producer.host_read(case.host_delta)
        review_path = Path(producer.host_parse_pin(delta['reviewed_host_change'])['path'])
        review = producer.host_read(review_path)
        consumer_path = Path(producer.host_parse_pin(review['source_consumer'])['path'])
        consumer = producer.host_read(consumer_path)
        pins = producer.host_obj(consumer['pins'])
        del pins[str(d.native / producer.HOST_TEST_COMPANION_RELATIVE)]
        consumer['pins'] = pins
        review['source_consumer'] = fixture.write(consumer_path, consumer)
        delta['reviewed_host_change'] = fixture.write(review_path, review)
        with self.assertRaises(ValueError):
            producer.qualify_host_test_companion(delta['host_test_change'], root=d.repo,
                native_commit=d.native_commit, runtime_commit=d.runtime_commit, machine=d.machine,
                qualification=d.qualification, snapshot=d.snapshot, host_delta=delta)


if __name__ == '__main__':
    unittest.main(verbosity=2)
