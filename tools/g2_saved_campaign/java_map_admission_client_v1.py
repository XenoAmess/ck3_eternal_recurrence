"""Source-bound Java map production, followed by the frozen Python consumers.

The response bytes are produced by the local Java service. This module never
calls the Python map builder and has no local-production fallback. HTTP success
does not grant Game, warm, ledger or other runtime qualification.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import http.client
import inspect
import math
from pathlib import Path
import time
from typing import Literal, Protocol, runtime_checkable

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, ExactRefV1, JsonObject, SavedFrameV1, _exact_native_json_v1,
    exact_read, integer, need, parse_frame, parse_json, parse_ref, record, rows,
    text, utc,
)

REQUEST_SCHEMA_V1 = 'xar.java-campaign-map-compose-request/v1'
PRODUCER_V1 = 'java-quarkus-map-admission/v1'
PRODUCER_VERSION_V1 = '0.1.0'
SERVICE_EVIDENCE_SCHEMA_V1 = 'xar.java-map-service-running/v1'
CALL_SCHEMA_V1 = 'xar.java-map-admission-http-call/v1'
COMPOSE_PATH_V1 = '/v1/map-admissions/compose'
MAX_REQUEST_BYTES_V1 = 65536
MAX_RESPONSE_BYTES_V1 = 16384
UINT64_MAX_V1 = (1 << 64)-1
PID_MAX_V1 = (1 << 32)-1
TransportKindV1 = Literal['stdlib-http-loopback/v1', 'injected-test/v1']
CallStatusV1 = Literal['completed', 'transport_failed', 'http_rejected', 'response_rejected']


@runtime_checkable
class JavaMapRuntimeReaderV1(BasisReaderV1, Protocol):
    def process_identity(self, pid: int) -> JsonObject: ...


@dataclass(frozen=True, slots=True)
class JavaProcessIdentityV1:
    pid: int
    creation_filetime: str
    executable: str

    def __post_init__(self) -> None:
        integer(self.pid, 1, PID_MAX_V1)
        _decimal_uint64(self.creation_filetime)
        need(Path(self.executable).is_absolute(), 'absolute observed Java process image')

    def to_wire(self) -> JsonObject:
        return {'pid': self.pid, 'creation_filetime': self.creation_filetime,
                'executable': self.executable}


@runtime_checkable
class ParsedMapAdmissionV1(Protocol):
    @property
    def machine_id(self) -> str: ...
    @property
    def game_pid(self) -> int: ...
    @property
    def game_creation_filetime(self) -> int: ...
    @property
    def recording_session_id(self) -> str: ...
    @property
    def actual_initial_frame(self) -> SavedFrameV1: ...
    @property
    def observed_at_utc(self) -> str | None: ...

    def require_native_launch_v1(self, launch: object) -> None: ...


@runtime_checkable
class FrozenMapConsumerV1(Protocol):
    __file__: str | None

    def parse_campaign_map_admission_v1(self, value: object, *,
        expected_machine_id: str) -> ParsedMapAdmissionV1: ...


@dataclass(frozen=True, slots=True)
class JavaMapServiceV1:
    port: int
    producer_version: str
    service_evidence_ref: ExactRefV1
    program_ref: ExactRefV1
    source_refs: tuple[ExactRefV1, ...]
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        integer(self.port, 1, 65535)
        need(self.producer_version == PRODUCER_VERSION_V1, 'explicit Java API implementation version')
        for reference in (self.service_evidence_ref, self.program_ref, *self.source_refs):
            need(isinstance(reference, ExactRefV1), 'typed exact Java evidence/source reference')
            parse_ref(reference.to_wire())
        need(type(self.source_refs) is tuple and bool(self.source_refs)
             and len({str(Path(ref.path).resolve()).casefold() for ref in self.source_refs}) == len(self.source_refs),
             'nonempty unique Java implementation source inventory')
        need(type(self.timeout_seconds) is float and math.isfinite(self.timeout_seconds)
             and 0 < self.timeout_seconds <= 120, 'finite explicit HTTP timeout')

    @property
    def url(self) -> str:
        return f'http://127.0.0.1:{self.port}{COMPOSE_PATH_V1}'


@dataclass(frozen=True, slots=True)
class HttpResponseV1:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    body_complete: bool = True

    def __post_init__(self) -> None:
        integer(self.status, 100, 599)
        need(type(self.headers) is tuple and len(self.headers) <= 100, 'bounded original HTTP headers')
        for pair in self.headers:
            need(type(pair) is tuple and len(pair) == 2 and all(type(item) is str for item in pair),
                 'exact HTTP header pairs')
        need(type(self.body) is bytes and len(self.body) <= MAX_RESPONSE_BYTES_V1+1
             and type(self.body_complete) is bool, 'bounded original HTTP response or overflow prefix')


class MapHttpTransportV1(Protocol):
    def post(self, *, port: int, body: bytes, timeout_seconds: float) -> HttpResponseV1: ...


class LoopbackHttpTransportV1:
    def post(self, *, port: int, body: bytes, timeout_seconds: float) -> HttpResponseV1:
        integer(port, 1, 65535)
        need(type(body) is bytes and 0 < len(body) <= MAX_REQUEST_BYTES_V1, 'bounded original request bytes')
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout_seconds)
        try:
            connection.request('POST', COMPOSE_PATH_V1, body=body,
                headers={'Content-Type': 'application/json; charset=utf-8',
                         'Accept': 'application/json', 'Connection': 'close'})
            response = connection.getresponse()
            payload = response.read(MAX_RESPONSE_BYTES_V1+1)
            return HttpResponseV1(response.status, tuple(response.getheaders()), payload,
                                  body_complete=len(payload) <= MAX_RESPONSE_BYTES_V1)
        finally:
            connection.close()


@dataclass(frozen=True, slots=True)
class HttpCallEvidenceV1:
    machine_id: str
    observed_at_utc: str
    completed_at_utc: str
    url: str
    status: CallStatusV1
    transport_kind: TransportKindV1
    elapsed_ns: int
    request_bytes: int
    request_sha256: str
    response_bytes: int | None
    response_sha256: str | None
    http_status: int | None
    response_headers: tuple[tuple[str, str], ...]
    service_evidence_ref: ExactRefV1
    program_ref: ExactRefV1
    source_refs: tuple[ExactRefV1, ...]
    consumer_source_ref: ExactRefV1
    error: str | None
    process_before: JavaProcessIdentityV1 | None = None
    process_after: JavaProcessIdentityV1 | None = None
    response_complete: bool | None = None

    def to_wire(self) -> JsonObject:
        return {'schema': CALL_SCHEMA_V1, 'machine_id': self.machine_id,
            'observed_at_utc': self.observed_at_utc, 'completed_at_utc': self.completed_at_utc,
            'method': 'POST', 'url': self.url, 'status': self.status,
            'transport_kind': self.transport_kind,
            'actual_HTTP_call': self.transport_kind == 'stdlib-http-loopback/v1',
            'producer': PRODUCER_V1, 'producer_version': PRODUCER_VERSION_V1,
            'request_schema': REQUEST_SCHEMA_V1, 'elapsed_ns': str(self.elapsed_ns),
            'request': {'bytes': self.request_bytes, 'sha256': self.request_sha256},
            'response': None if self.response_bytes is None else
                {'bytes': self.response_bytes, 'sha256': self.response_sha256,
                 'complete': self.response_complete,
                 'scope': 'original-body' if self.response_complete else 'bounded-overflow-prefix'},
            'http_status': self.http_status,
            'response_headers': [[name, value] for name, value in self.response_headers],
            'service_evidence_ref': self.service_evidence_ref.to_wire(),
            'program_ref': self.program_ref.to_wire(),
            'source_refs': [reference.to_wire() for reference in self.source_refs],
            'consumer_source_ref': self.consumer_source_ref.to_wire(), 'error': self.error,
            'process_identity_source': 'original-kernel-process-identity/v1'
                if self.transport_kind == 'stdlib-http-loopback/v1' else 'injected-test/v1',
            'Java_process_before': None if self.process_before is None else self.process_before.to_wire(),
            'Java_process_after': None if self.process_after is None else self.process_after.to_wire(),
            'scope': 'Java metadata production and frozen map parser validation only; no warm/Game/ledger qualification',
            'Python_map_builder_calls': 0, 'Python_fallback_used': False}


@dataclass(frozen=True, slots=True)
class JavaMapCompositionV1:
    raw_admission_bytes: bytes
    http_call: HttpCallEvidenceV1


class JavaMapAdmissionErrorV1(RuntimeError):
    def __init__(self, message: str, *, http_call: HttpCallEvidenceV1,
                 response_body: bytes | None) -> None:
        super().__init__(message)
        self.http_call = http_call
        self.response_body = response_body


def _decimal_uint64(value: object) -> str:
    result = text(value)
    need(result.isascii() and result.isdecimal() and result[0] != '0'
         and str(int(result)) == result and int(result) <= UINT64_MAX_V1,
         'canonical nonzero decimal uint64 identity')
    return result


def _observed_process(value: object) -> JavaProcessIdentityV1:
    process = record(value, {'pid', 'creation_filetime', 'executable'})
    return JavaProcessIdentityV1(integer(process['pid'], 1, PID_MAX_V1),
        _decimal_uint64(process['creation_filetime']), text(process['executable']))


def _require_current_process(expected: JavaProcessIdentityV1, *,
    reader: JavaMapRuntimeReaderV1) -> JavaProcessIdentityV1:
    current = _observed_process(reader.process_identity(expected.pid))
    need(current.pid == expected.pid and current.creation_filetime == expected.creation_filetime
         and str(Path(current.executable).resolve()).casefold() == str(Path(expected.executable).resolve()).casefold(),
         'actual live Java PID, kernel birth and executable still match Root evidence')
    return current


def _validate_source_binding(service: JavaMapServiceV1, *, machine_id: str,
    reader: JavaMapRuntimeReaderV1, consumer: FrozenMapConsumerV1,
    consumer_source_ref: ExactRefV1, injected_transport: bool) -> JavaProcessIdentityV1:
    need(isinstance(consumer, FrozenMapConsumerV1), 'actual frozen owner consumer')
    expected_path = Path(consumer_source_ref.path).resolve()
    consumer_file = consumer.__file__
    if not isinstance(consumer_file, str):
        raise ValueError('frozen consumer module source unavailable')
    need(Path(consumer_file).resolve() == expected_path,
         'frozen consumer module origin matches its actual source pin')
    function_path = inspect.getsourcefile(consumer.parse_campaign_map_admission_v1)
    need(function_path is not None and Path(function_path).resolve() == expected_path,
         'frozen parser function origin matches its actual source pin')
    exact_read(reader, consumer_source_ref, 262144)
    need(isinstance(reader, JavaMapRuntimeReaderV1), 'read-only original process identity capability')
    if not injected_transport:
        identity_source = inspect.getsourcefile(reader.process_identity)
        need(identity_source is not None and Path(identity_source).resolve() == expected_path,
             'production Java process observations use the original frozen kernel reader')
    evidence = record(parse_json(exact_read(reader, service.service_evidence_ref, 65536)),
        {'schema', 'machine_id', 'observed_at_utc', 'status', 'producer', 'producer_version',
         'url', 'program_ref', 'source_refs', 'process'})
    need(evidence['schema'] == SERVICE_EVIDENCE_SCHEMA_V1 and evidence['machine_id'] == machine_id
         and evidence['status'] == 'ACTUAL_RUNNING' and evidence['producer'] == PRODUCER_V1
         and evidence['producer_version'] == service.producer_version and evidence['url'] == service.url,
         'Root actual Java service identity, endpoint and implementation version')
    utc(evidence['observed_at_utc'])
    need(parse_ref(evidence['program_ref']) == service.program_ref
         and tuple(parse_ref(value) for value in rows(evidence['source_refs'])) == service.source_refs,
         'Root actual program/deployment manifest and complete implementation source inventory')
    # The manifest is the small, exact measured deployment closure. Its JAR
    # members were hashed by the original owner; do not rehash every JAR here.
    manifest = record(parse_json(exact_read(reader, service.program_ref, 1048576)))
    need(manifest.get('machine_id') == machine_id
         and tuple(parse_ref(value) for value in rows(manifest.get('source_refs'))) == service.source_refs,
         'exact fast-JAR manifest binds the admitted machine and implementation source inventory')
    for reference in service.source_refs:
        exact_read(reader, reference, 1048576)
    return _require_current_process(_observed_process(evidence['process']), reader=reader)


def _header(response: HttpResponseV1, name: str) -> str:
    values = [value for key, value in response.headers if key.casefold() == name.casefold()]
    need(len(values) == 1, 'single required Java HTTP header: '+name)
    return values[0]


def _validate_response(response: HttpResponseV1, *, consumer: FrozenMapConsumerV1,
    machine_id: str, observed_at_utc: str, native_launch: object,
    recording_session_id: str, actual_initial_frame: SavedFrameV1) -> None:
    content_type = _header(response, 'Content-Type').split(';')
    need(content_type[0].strip().casefold() == 'application/json'
         and all(part.strip().casefold() in ('charset=utf-8', 'charset="utf-8"')
                 for part in content_type[1:]), 'Java response is original UTF8 JSON')
    need(_header(response, 'X-Xar-Producer') == PRODUCER_V1
         and _header(response, 'X-Xar-Producer-Version') == PRODUCER_VERSION_V1
         and _header(response, 'X-Xar-Contract-Revision') == REQUEST_SCHEMA_V1,
         'actual HTTP response reports the admitted Java implementation contract')
    need(response.body_complete and 0 < len(response.body) <= MAX_RESPONSE_BYTES_V1,
         'complete original Java map response within the actual frozen Queue limit')
    row = record(parse_json(response.body), {'machine_id', 'status', 'reviewer', 'game_pid',
        'game_creation_filetime', 'Game_map_visible', 'decision_text_visible',
        'recording_session_id', 'actual_initial_frame', 'schema', 'observed_at_utc'})
    parsed = consumer.parse_campaign_map_admission_v1(row, expected_machine_id=machine_id)
    need(isinstance(parsed, ParsedMapAdmissionV1), 'typed actual frozen map parser result')
    parsed.require_native_launch_v1(native_launch)
    need(parsed.machine_id == machine_id and parsed.recording_session_id == recording_session_id
         and parsed.actual_initial_frame == actual_initial_frame
         and parsed.observed_at_utc == observed_at_utc,
         'Java map preserves actual machine, native generation, frame, session and Root observation')


def compose_campaign_map_admission_via_java_v1(*, service: JavaMapServiceV1,
    machine_id: str, observed_at_utc: str, native_launch: object,
    recording_session_id: str, actual_initial_frame: SavedFrameV1,
    game_map_visible: Literal[True], decision_text_visible: Literal[True],
    consumer: FrozenMapConsumerV1, consumer_source_ref: ExactRefV1,
    reader: JavaMapRuntimeReaderV1, transport: MapHttpTransportV1 | None = None) -> JavaMapCompositionV1:
    """Call Java once, validate its unchanged bytes with the actual frozen owner.

    ``transport`` is a negative-test seam. Its evidence is explicitly tagged as
    injected and cannot claim an actual Java HTTP invocation. Root uses None.
    Source/input failures occur before HTTP; all call failures carry evidence.
    """
    need(isinstance(service, JavaMapServiceV1), 'typed Java map service configuration')
    text(machine_id); utc(observed_at_utc); text(recording_session_id)
    need(game_map_visible is True and decision_text_visible is True, 'actual Root-reviewed Game and decision pixels')
    need(isinstance(actual_initial_frame, SavedFrameV1), 'typed actual initial frame')
    frame = parse_frame(actual_initial_frame.to_wire())
    launch = record(native_launch)
    pid = integer(launch.get('pid'), 1, PID_MAX_V1)
    birth = integer(launch.get('creation_filetime'), 1, UINT64_MAX_V1)
    process_before = _validate_source_binding(service, machine_id=machine_id, reader=reader,
        consumer=consumer, consumer_source_ref=consumer_source_ref, injected_transport=transport is not None)
    request = {'schema': REQUEST_SCHEMA_V1, 'machine_id': machine_id,
        'observed_at_utc': observed_at_utc, 'native_launch': {'pid': pid, 'creation_filetime': birth},
        'recording_session_id': recording_session_id, 'actual_initial_frame': frame.to_wire(),
        'game_map_visible': True, 'decision_text_visible': True}
    request_bytes = _exact_native_json_v1(request)
    need(0 < len(request_bytes) <= MAX_REQUEST_BYTES_V1, 'bounded exact Python-to-Java JSON bytes')
    kind: TransportKindV1 = 'stdlib-http-loopback/v1' if transport is None else 'injected-test/v1'
    actual_transport: MapHttpTransportV1 = LoopbackHttpTransportV1() if transport is None else transport
    started = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter_ns()
    response: HttpResponseV1 | None = None
    try:
        response = actual_transport.post(port=service.port, body=request_bytes,
            timeout_seconds=service.timeout_seconds)
        need(isinstance(response, HttpResponseV1), 'typed HTTP transport response')
    except Exception as error:
        elapsed = time.perf_counter_ns()-tick
        process_after: JavaProcessIdentityV1 | None = None
        detail = type(error).__name__+': '+str(error)
        try:
            process_after = _require_current_process(process_before, reader=reader)
        except Exception as identity_error:
            detail += '; post-call Java identity unavailable/rejected: '+str(identity_error)
        evidence = HttpCallEvidenceV1(machine_id, started, datetime.now(timezone.utc).isoformat(),
            service.url, 'transport_failed', kind, elapsed, len(request_bytes),
            hashlib.sha256(request_bytes).hexdigest(), None, None, None, (),
            service.service_evidence_ref, service.program_ref, service.source_refs,
            consumer_source_ref, detail[:4096], process_before, process_after)
        raise JavaMapAdmissionErrorV1('Java map HTTP call failed; Python fallback is forbidden',
            http_call=evidence, response_body=None) from error
    elapsed = time.perf_counter_ns()-tick
    evidence = HttpCallEvidenceV1(machine_id, started, datetime.now(timezone.utc).isoformat(),
        service.url, 'completed', kind, elapsed, len(request_bytes), hashlib.sha256(request_bytes).hexdigest(),
        len(response.body), hashlib.sha256(response.body).hexdigest(), response.status, response.headers,
        service.service_evidence_ref, service.program_ref, service.source_refs, consumer_source_ref, None,
        process_before, None, response.body_complete)
    try:
        current_process = _require_current_process(process_before, reader=reader)
        evidence = replace(evidence, process_after=current_process)
    except Exception as error:
        failed = replace(evidence, status='response_rejected',
            error='Post-call Java kernel identity rejected: '+str(error))
        raise JavaMapAdmissionErrorV1('Java service generation changed or exited during HTTP; Python fallback is forbidden',
            http_call=failed, response_body=response.body) from error
    if response.status != 200:
        failed = replace(evidence, status='http_rejected', error='HTTP '+str(response.status))
        raise JavaMapAdmissionErrorV1('Java map producer rejected the request; Python fallback is forbidden',
            http_call=failed, response_body=response.body)
    try:
        _validate_response(response, consumer=consumer, machine_id=machine_id,
            observed_at_utc=observed_at_utc, native_launch=native_launch,
            recording_session_id=recording_session_id, actual_initial_frame=frame)
    except Exception as error:
        failed = replace(evidence, status='response_rejected',
            error=(type(error).__name__+': '+str(error))[:4096])
        raise JavaMapAdmissionErrorV1('Java map response failed the frozen consumer contract; Python fallback is forbidden',
            http_call=failed, response_body=response.body) from error
    return JavaMapCompositionV1(response.body, evidence)
