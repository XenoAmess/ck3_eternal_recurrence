"""Authored source contracts through the real producer and public qualifier.

The inherited miniature Q/File API/Defender rows are explicitly authored data;
these tests never build, execute, register an EXE, or qualify actual live work.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from typing import ClassVar
from uuid import uuid4

import ck3_mod_acceptance_same_root_host_delta as producer
import test_ck3_mod_acceptance_native_exact_tree_binding as fixture


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
        before = producer.signature(cls.original.read_bytes())
        after = producer.signature((d.repo / producer.HOST_RELATIVE).read_bytes())
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
            'source_pins': [producer.pin(d.repo / producer.HOST_RELATIVE)],
            'source_consumer': consumer, 'source_delta': source_delta, 'reviewed_host_change': review,
            'authored_fixture_not_actual_tests': True})
        cls.delta = {'schema': producer.DELTA_SCHEMA, 'machine_id': d.machine,
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
        producer.produce_binding(self.data.repo, self.data.qpath, self.delta_path,
                                 self.original, path, self.data.machine)
        return path

    def consume(self, path: Path) -> dict[str, object]:
        d = self.data
        return fixture.object_fields(self.public.qualify_native(d.qpath, d.repo, d.runtime_commit,
            d.machine, d.dll_ref, d.manifest, path, self.delta_path))

    def test_01_actual_producer_to_complete_public_qualifier(self) -> None:
        before = {path: producer.pin(path) for path in (self.data.qpath, Path(self.data.snapshot_ref['path']),
                  Path(self.data.dll_ref['path']))}
        path = self.produce()
        result = self.consume(path)
        self.assertEqual(result['compile_commit'], self.data.native_commit)
        self.assertEqual(result['source_checkout_binding'], producer.pin(path))
        self.assertEqual(result['native_files'], {producer.NATIVE_PREFIX + 'src/body.cpp':
                                                producer.signature(self.data.contents['src/body.cpp'])})
        self.assertEqual(before, {path: producer.pin(path) for path in before})

    def test_02_same_root_without_opt_in_still_rejects_changed_host(self) -> None:
        d = self.data
        with self.assertRaises(ValueError):
            self.public.qualify_native(d.qpath, d.repo, d.runtime_commit, d.machine, d.dll_ref, d.manifest)

    def test_03_json_roundtrip_retains_exact_public_result(self) -> None:
        result = self.consume(self.produce())
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_04_original_blob_is_exact_git_content(self) -> None:
        path = self.produce()
        value = producer.read(path)
        wrong = self.data.evidence / 'wrong-original.py'
        wrong.write_bytes(b'HOST = 999\n')
        value['original_shared_host_blob'] = producer.pin(wrong)
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
                value = producer.read(path)
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
        result = fixture.object_fields(producer.shared_api().qualify_shared_host_delta(old_path,
            root=d.repo, native_repo=d.worktree, runtime_commit=d.runtime_commit, native_commit=d.native_commit,
            machine=d.machine, qualified_native_ref=d.qref, qualification=d.qualification,
            snapshot_ref=d.snapshot_ref, snapshot=d.snapshot))
        self.assertEqual(result['runtime_host_pin'], producer.pin(d.repo / producer.HOST_RELATIVE))

    def test_12_reviewed_consumer_cannot_claim_boolean_zero_wait(self) -> None:
        d = self.data
        consumer_path = d.evidence / 'consumer.json'
        consumer_before = consumer_path.read_bytes()
        review_path = d.evidence / 'review.json'
        review_before = review_path.read_bytes()
        qpath = d.evidence / 'shared-host-qualification.json'
        qbefore = qpath.read_bytes()
        try:
            consumer = producer.read(consumer_path)
            consumer['original_wait_returncode'] = False
            fixture.write(consumer_path, consumer)
            review = producer.read(review_path)
            review['source_consumer'] = producer.pin(consumer_path)
            fixture.write(review_path, review)
            shared = producer.read(qpath)
            shared['source_consumer'] = producer.pin(consumer_path)
            shared['reviewed_host_change'] = producer.pin(review_path)
            fixture.write(qpath, shared)
            delta = dict(self.delta, reviewed_host_change=producer.pin(review_path),
                         shared_host_qualification=producer.pin(qpath))
            fixture.write(self.delta_path, delta)
            with self.assertRaisesRegex(ValueError, 'original zero wait'):
                self.produce()
        finally:
            consumer_path.write_bytes(consumer_before)
            review_path.write_bytes(review_before)
            qpath.write_bytes(qbefore)
            fixture.write(self.delta_path, self.delta)


if __name__ == '__main__':
    unittest.main(verbosity=2)
