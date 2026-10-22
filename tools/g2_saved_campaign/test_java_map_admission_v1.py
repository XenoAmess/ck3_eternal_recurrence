"""Real Java HTTP producer -> Python client -> all existing map consumers.

The service is started and source-bound by its external owner. Missing service
evidence is a hard error; these tests never substitute a Python HTTP server or
produce a successful map locally. Synthetic Game/ledger inputs remain in RAM.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
from typing import Literal
import unittest
from unittest.mock import patch

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, SavedFrameV1, _exact_native_json_v1,
    integer, parse_json, parse_ref, record, rows, text,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1
from tools.g2_saved_campaign import java_map_admission_client_v1 as java_client
from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner

SERVICE_ENV_V1 = 'XAR_JAVA_MAP_SERVICE_EVIDENCE'
UINT64_MAX_V1 = (1 << 64) - 1
OBSERVED_V1 = '2026-10-22T12:00:00+00:00'
ORIGINAL_PYTHON_BUILDER_V1 = owner.build_campaign_map_admission_v1


def _reference_v1(path: Path) -> ExactRefV1:
    raw = path.read_bytes()
    return ExactRefV1(str(path.resolve()), len(raw), hashlib.sha256(raw).hexdigest())


class _PinnedSourcesV1(owner.LocalBasisReaderV1):
    """Measured source bytes survive the existing RAM fixture's Path.open seam.

    Current native file identities are checked again at every cached read. This
    adapter is confined to the pre-existing in-memory consumer fixture.
    """
    def __init__(self, references: tuple[ExactRefV1, ...]) -> None:
        self.reader = owner.LocalBasisReaderV1()
        self.actual_stat: Callable[[str], FileStatIdentityV1] = self.reader.stat
        self.raw: dict[str, bytes] = {}
        self.identities: dict[str, FileStatIdentityV1] = {}
        for reference in references:
            before = self.actual_stat(reference.path)
            raw = Path(reference.path).read_bytes()
            if (len(raw) != reference.bytes or hashlib.sha256(raw).hexdigest() != reference.sha256
                    or self.actual_stat(reference.path) != before):
                raise ValueError('actual Java fixture source changed during measurement')
            self.raw[reference.path] = raw
            self.identities[reference.path] = before

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        integer(limit, 1, 1048576)
        if reference.bytes > limit or self.actual_stat(reference.path) != self.identities[reference.path]:
            raise ValueError('bounded stable actual fixture source required')
        raw = self.raw[reference.path]
        if len(raw) != reference.bytes or hashlib.sha256(raw).hexdigest() != reference.sha256:
            raise ValueError('exact cached actual fixture source required')
        return raw

    def stat(self, path: str) -> FileStatIdentityV1:
        return self.actual_stat(path)



class _ResponseTransportV1:
    def __init__(self, response: java_client.HttpResponseV1 | None = None) -> None:
        self.response = response
        self.calls = 0

    def post(self, *, port: int, body: bytes, timeout_seconds: float) -> java_client.HttpResponseV1:
        self.calls += 1
        if self.response is None:
            raise OSError('explicit injected network failure, never actual HTTP credit')
        return self.response


class JavaMapAdmissionHttpTests(unittest.TestCase):
    service: java_client.JavaMapServiceV1
    consumer: java_client.FrozenMapConsumerV1
    consumer_ref: ExactRefV1
    reader: owner.LocalBasisReaderV1
    machine_id: str
    http_calls: list[JsonObject]

    @classmethod
    def setUpClass(cls) -> None:
        evidence_value = os.environ.get(SERVICE_ENV_V1)
        if not evidence_value:
            raise RuntimeError(SERVICE_ENV_V1 + ' must name an actual source-bound Java service; no skip/fallback')
        evidence_path = Path(evidence_value).resolve(strict=True)
        if evidence_path.stat().st_size > 65536:
            raise ValueError('bounded actual Java service evidence required')
        evidence = record(parse_json(evidence_path.read_bytes()))
        cls.machine_id = text(evidence.get('machine_id'))
        from tools.ck3_live_run_id import current_machine_id
        if cls.machine_id != current_machine_id():
            raise ValueError('actual service belongs to another or unverified machine')
        url = text(evidence.get('url'))
        prefix, suffix = 'http://127.0.0.1:', java_client.COMPOSE_PATH_V1
        if not url.startswith(prefix) or not url.endswith(suffix):
            raise ValueError('exact loopback Java compose endpoint required')
        port = int(url[len(prefix):-len(suffix)])
        if not isinstance(owner, java_client.FrozenMapConsumerV1):
            raise TypeError('actual original map consumer capability required')
        cls.consumer = owner
        cls.consumer_ref = _reference_v1(Path(owner.__file__))
        cls.service = java_client.JavaMapServiceV1(port, text(evidence.get('producer_version')),
            _reference_v1(evidence_path), parse_ref(evidence.get('program_ref')),
            tuple(parse_ref(value) for value in rows(evidence.get('source_refs'))))
        cls.reader = owner.LocalBasisReaderV1()
        cls.http_calls = []

    @classmethod
    def tearDownClass(cls) -> None:
        print(json.dumps({'schema': 'xar.java-map-http-integration-summary/v1',
            'machine_id': cls.machine_id, 'service_evidence_ref': cls.service.service_evidence_ref.to_wire(),
            'program_ref': cls.service.program_ref.to_wire(), 'consumer_source_ref': cls.consumer_ref.to_wire(),
            'actual_client_HTTP_calls': len(cls.http_calls), 'actual_http_calls': cls.http_calls,
            'Game_native_RPC_or_campaign_ledger_writes': 0, 'service_left_running_for_Root': True},
            ensure_ascii=False, allow_nan=False))

    def _frame_v1(self) -> SavedFrameV1:
        return SavedFrameV1('native:1', 2, 1, 53279400, 40526, 'java-http-test-episode')

    def _request_v1(self) -> JsonObject:
        return {'schema': java_client.REQUEST_SCHEMA_V1, 'machine_id': self.machine_id,
            'observed_at_utc': OBSERVED_V1,
            'native_launch': {'pid': 200332, 'creation_filetime': 134371375868945259},
            'recording_session_id': 'session', 'actual_initial_frame': self._frame_v1().to_wire(),
            'game_map_visible': True, 'decision_text_visible': True}

    def _compose_v1(self, *, birth: int = 134371375868945259, observed: str = OBSERVED_V1,
            session: str = 'session', transport: java_client.MapHttpTransportV1 | None = None,
            service: java_client.JavaMapServiceV1 | None = None) -> java_client.JavaMapCompositionV1:
        result = java_client.compose_campaign_map_admission_via_java_v1(
            service=self.service if service is None else service,
            machine_id=self.machine_id, observed_at_utc=observed,
            native_launch={'pid': 200332, 'creation_filetime': birth}, recording_session_id=session,
            actual_initial_frame=self._frame_v1(), game_map_visible=True, decision_text_visible=True,
            consumer=self.consumer, consumer_source_ref=self.consumer_ref,
            reader=self.reader, transport=transport)
        if transport is None:
            self.http_calls.append(result.http_call.to_wire())
            self.assertEqual(result.http_call.transport_kind, 'stdlib-http-loopback/v1')
        return result

    def _post_rejected_v1(self, raw: bytes) -> None:
        response = java_client.LoopbackHttpTransportV1().post(port=self.service.port,
            body=raw, timeout_seconds=10.0)
        self.assertEqual(response.status, 400, response.body)
        rejection = record(parse_json(response.body))
        self.assertEqual(set(rejection), {'schema', 'status', 'error'})
        self.assertEqual(rejection['schema'], 'xar.java-contract-error/v1')
        self.assertEqual(rejection['status'], 'rejected')
        self.assertIsInstance(rejection['error'], str)

    def test_real_HTTP_uint64_domain_and_exact_python_canonical_bytes(self) -> None:
        for birth in (1, (1 << 53) + 1, 134371375868945259, 1 << 63, UINT64_MAX_V1):
            with self.subTest(birth=birth):
                expected = ORIGINAL_PYTHON_BUILDER_V1(machine_id=self.machine_id,
                    observed_at_utc=OBSERVED_V1, native_launch={'pid': 200332, 'creation_filetime': birth},
                    recording_session_id='session', actual_initial_frame=self._frame_v1(),
                    game_map_visible=True, decision_text_visible=True)
                with patch.object(owner, 'build_campaign_map_admission_v1',
                        side_effect=AssertionError('Java HTTP production cannot fall back to Python')):
                    result = self._compose_v1(birth=birth)
                self.assertEqual(result.raw_admission_bytes, expected)
                value = record(parse_json(result.raw_admission_bytes))
                self.assertIs(type(value['game_creation_filetime']), int)
                self.assertEqual(value['game_creation_filetime'], birth)
                self.assertNotIsInstance(value['game_creation_filetime'], str)

    def test_real_HTTP_unicode_control_escaping_and_UTC_preserve_original_bytes(self) -> None:
        session = '罗贝尔 😀 \\ quote" newline\n control\x1f'
        for observed in ('2026-10-22T12:00:00Z', OBSERVED_V1, '2026-10-22 12:00:00+00:00',
                '20261022T120000Z', '2026-W43-4T12:00:00+00:00',
                '2026-10-22T12:00:00.123456789+00:00', '2026-10-22T12:00:00-00:00'):
            with self.subTest(observed=observed):
                expected = ORIGINAL_PYTHON_BUILDER_V1(machine_id=self.machine_id,
                    observed_at_utc=observed, native_launch={'pid': 200332, 'creation_filetime': 134371375868945259},
                    recording_session_id=session, actual_initial_frame=self._frame_v1(),
                    game_map_visible=True, decision_text_visible=True)
                self.assertEqual(self._compose_v1(observed=observed, session=session).raw_admission_bytes, expected)

    def test_real_HTTP_wrong_missing_null_empty_and_unknown_request_fields_reject(self) -> None:
        baseline = self._request_v1()
        invalid_replacements: tuple[object, ...] = (None, [])
        for field in baseline:
            for replacement in invalid_replacements:
                with self.subTest(field=field, replacement=replacement):
                    self._post_rejected_v1(_exact_native_json_v1({**baseline, field: replacement}))
            missing = dict(baseline); del missing[field]
            with self.subTest(missing=field): self._post_rejected_v1(_exact_native_json_v1(missing))
        self._post_rejected_v1(_exact_native_json_v1({**baseline, 'unknown': 1}))
        for field, wrong in (('game_map_visible', 1), ('decision_text_visible', False),
                ('schema', 'unknown-schema'), ('machine_id', ''), ('recording_session_id', '')):
            with self.subTest(field=field, wrong=wrong):
                self._post_rejected_v1(_exact_native_json_v1({**baseline, field: wrong}))
        for wrong_birth in (str(UINT64_MAX_V1), True, 1.0, 0, -1, UINT64_MAX_V1 + 1):
            with self.subTest(birth=wrong_birth):
                # json.dumps intentionally sends the malformed scalar unchanged.
                raw = json.dumps({**baseline, 'native_launch': {'pid': 200332,
                    'creation_filetime': wrong_birth}}, ensure_ascii=False).encode()
                self._post_rejected_v1(raw)
        for wrong_pid in (True, 1.0, '200332', 0, 1 << 32):
            with self.subTest(pid=wrong_pid):
                self._post_rejected_v1(json.dumps({**baseline, 'native_launch': {
                    'pid': wrong_pid, 'creation_filetime': 134371375868945259}}).encode())

    def test_real_HTTP_duplicate_keys_frame_source_fields_and_caps(self) -> None:
        baseline = self._request_v1()
        raw = _exact_native_json_v1(baseline)
        duplicate = raw.replace(b'"schema":', b'"schema":"duplicate","schema":', 1)
        self._post_rejected_v1(duplicate)
        frame = self._frame_v1().to_wire()
        for field, wrong in (('native_revision', True), ('revision', 1.0),
                ('actor_character_id', '40526'), ('date_raw', None), ('snapshot_id', 'native:2'),
                ('unknown', 1)):
            with self.subTest(field=field, wrong=wrong):
                self._post_rejected_v1(json.dumps({**baseline,
                    'actual_initial_frame': {**frame, field: wrong}}).encode())
        padded = raw + b' ' * (java_client.MAX_REQUEST_BYTES_V1 - len(raw))
        response = java_client.LoopbackHttpTransportV1().post(port=self.service.port,
            body=padded, timeout_seconds=10.0)
        self.assertEqual(response.status, 200, response.body)
        with patch.object(owner, 'build_campaign_map_admission_v1',
                side_effect=AssertionError('a Java rejection cannot fall back')):
            with self.assertRaises(java_client.JavaMapAdmissionErrorV1) as rejected:
                self._compose_v1(session='中' * 6000)
        self.assertEqual(rejected.exception.http_call.status, 'http_rejected')
        self.assertEqual(rejected.exception.http_call.transport_kind, 'stdlib-http-loopback/v1')
        self.assertEqual(rejected.exception.http_call.http_status, 400)

    def test_client_response_source_caps_and_failure_never_fall_back(self) -> None:
        valid = self._compose_v1()
        headers = valid.http_call.response_headers
        malformed: tuple[bytes, ...] = (b'{}', b'null', b'[]', b'\xff',
            valid.raw_admission_bytes.replace(b'"game_creation_filetime":134371375868945259',
                b'"game_creation_filetime":"134371375868945259"'),
            valid.raw_admission_bytes.replace(b'"schema":', b'"schema":"duplicate","schema":', 1))
        for raw in malformed:
            with self.subTest(body=raw[:80]):
                transport = _ResponseTransportV1(java_client.HttpResponseV1(200, headers, raw))
                with patch.object(owner, 'build_campaign_map_admission_v1', side_effect=AssertionError('no fallback')):
                    with self.assertRaises(java_client.JavaMapAdmissionErrorV1) as rejected:
                        self._compose_v1(transport=transport)
                self.assertEqual(rejected.exception.http_call.status, 'response_rejected')
                self.assertEqual(rejected.exception.http_call.transport_kind, 'injected-test/v1')
                self.assertEqual(transport.calls, 1)
        bad_headers = tuple((name, 'wrong-version' if name.casefold() == 'x-xar-producer-version' else value)
            for name, value in headers)
        for changed_headers in (bad_headers,
                tuple(pair for pair in headers if pair[0].casefold() != 'x-xar-producer'),
                headers + (('X-Xar-Producer-Version', '0.1.0'),),
                tuple((name, 'text/plain' if name.casefold() == 'content-type' else value)
                    for name, value in headers)):
            transport = _ResponseTransportV1(java_client.HttpResponseV1(200, changed_headers, valid.raw_admission_bytes))
            with self.assertRaises(java_client.JavaMapAdmissionErrorV1): self._compose_v1(transport=transport)
        network_failure = _ResponseTransportV1()
        with self.assertRaises(java_client.JavaMapAdmissionErrorV1) as failed:
            self._compose_v1(transport=network_failure)
        self.assertEqual(failed.exception.http_call.status, 'transport_failed')
        self.assertEqual(failed.exception.http_call.transport_kind, 'injected-test/v1')
        for changed in (replace(self.service, service_evidence_ref=replace(self.service.service_evidence_ref, bytes=65537)),
                replace(self.service, program_ref=replace(self.service.program_ref, sha256='0' * 64)),
                replace(self.service, source_refs=(replace(self.service.source_refs[0], bytes=1048577),
                    *self.service.source_refs[1:]))):
            transport = _ResponseTransportV1()
            with self.subTest(source=changed), self.assertRaises(ValueError):
                self._compose_v1(service=changed, transport=transport)
            self.assertEqual(transport.calls, 0)
        transport = _ResponseTransportV1()
        with patch.object(self, 'consumer_ref', replace(self.consumer_ref, bytes=262145)):
            with self.assertRaises(ValueError): self._compose_v1(transport=transport)
        self.assertEqual(transport.calls, 0)
        overflow = java_client.HttpResponseV1(200, headers,
            b'x' * (java_client.MAX_RESPONSE_BYTES_V1 + 1), body_complete=False)
        with self.assertRaises(java_client.JavaMapAdmissionErrorV1) as oversized:
            self._compose_v1(transport=_ResponseTransportV1(overflow))
        self.assertEqual(oversized.exception.http_call.status, 'response_rejected')
        self.assertFalse(oversized.exception.http_call.response_complete)
        self.assertEqual(oversized.exception.response_body, overflow.body)
        with self.assertRaises(ValueError):
            java_client.HttpResponseV1(200, headers,
                b'x' * (java_client.MAX_RESPONSE_BYTES_V1 + 2), body_complete=False)

    def test_real_Java_producer_original_Queue_feeder_reducer_all_three_closed_lineages(self) -> None:
        from tools.g2_saved_campaign import test_current_saved_campaign_cold_v1 as fixtures
        from tools.g2_saved_campaign import test_current_saved_basis_v1 as basis_fixture
        from tools.g2_saved_campaign import test_current_saved_continuity_v1 as continuity_fixture
        cached = _PinnedSourcesV1((self.consumer_ref, self.service.service_evidence_ref, self.service.program_ref,
            *self.service.source_refs))
        calls: list[java_client.HttpCallEvidenceV1] = []

        def java_publisher(*, machine_id: str, observed_at_utc: str, native_launch: object,
                recording_session_id: str, actual_initial_frame: SavedFrameV1,
                game_map_visible: Literal[True], decision_text_visible: Literal[True]) -> bytes:
            result = java_client.compose_campaign_map_admission_via_java_v1(service=self.service,
                machine_id=machine_id, observed_at_utc=observed_at_utc, native_launch=native_launch,
                recording_session_id=recording_session_id, actual_initial_frame=actual_initial_frame,
                game_map_visible=game_map_visible, decision_text_visible=decision_text_visible,
                consumer=self.consumer, consumer_source_ref=self.consumer_ref, reader=cached)
            # The old producer is an independent differential oracle only. The
            # returned bytes always remain the original actual Java response.
            expected = ORIGINAL_PYTHON_BUILDER_V1(machine_id=machine_id, observed_at_utc=observed_at_utc,
                native_launch=native_launch, recording_session_id=recording_session_id,
                actual_initial_frame=actual_initial_frame, game_map_visible=game_map_visible,
                decision_text_visible=decision_text_visible)
            self.assertEqual(result.raw_admission_bytes, expected)
            self.assertEqual(result.http_call.transport_kind, 'stdlib-http-loopback/v1')
            calls.append(result.http_call)
            return result.raw_admission_bytes

        names = ('test_emitted_qualify_accepts_actual_owner_and_keeps_role_caps',
            'test_emitted_qualify_readiness_projection_to_actual_reducer',
            'test_emitted_qualify_full_pre_dispatch_failure_whole_queue_to_actual_reducer')
        with patch.object(owner, 'build_campaign_map_admission_v1', side_effect=java_publisher), \
                patch.object(fixtures, 'MACHINE', self.machine_id), \
                patch.object(basis_fixture, 'MACHINE', self.machine_id), \
                patch.object(continuity_fixture, 'MACHINE', self.machine_id):
            suite = unittest.TestSuite(fixtures.CurrentSavedFeederSourceClosureTests(name) for name in names)
            result = unittest.TestResult()
            suite.run(result)
        self.assertEqual(result.testsRun, 3)
        self.assertEqual(result.skipped, [])
        self.assertEqual(result.expectedFailures, [])
        self.assertEqual(result.unexpectedSuccesses, [])
        self.assertTrue(result.wasSuccessful(), repr(result.failures + result.errors))
        self.assertEqual(len(calls), 3)
        self.http_calls.extend(call.to_wire() for call in calls)


if __name__ == '__main__':
    unittest.main()
