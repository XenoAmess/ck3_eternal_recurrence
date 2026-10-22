"""Narrow, explicit comparison of narration and SentenceBoundary metadata.

The provider's original text is never rewritten. A recognized formatting
difference is reported as such, rather than labeled an exact text match.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import AsyncIterator
from datetime import datetime, timezone
import hashlib
import inspect
import json
import math
from pathlib import Path
import re
from typing import Literal, Protocol, TypedDict, runtime_checkable
from xml.sax.saxutils import escape

MatchStatus = Literal['EXACT', 'LEADING_OPEN_QUOTE_OMITTED']


class SentenceMatchJSON(TypedDict):
    sequence: int
    source_text: str
    reported_text: str
    status: MatchStatus


@dataclass(frozen=True)
class SentenceMatch:
    sequence: int
    source_text: str
    reported_text: str
    status: MatchStatus


def _compare(sequence: int, source: str, reported: str) -> SentenceMatch:
    if not source or not reported:
        raise ValueError('Empty source or reported sentence')
    if source == reported:
        return SentenceMatch(sequence, source, reported, 'EXACT')
    if source.startswith('\u201c') and reported == source[1:]:
        return SentenceMatch(sequence, source, reported, 'LEADING_OPEN_QUOTE_OMITTED')
    raise ValueError('Unrecognized SentenceBoundary text difference at sentence ' + str(sequence))


def reconcile_sentence_texts(source: tuple[str, ...], reported: tuple[str, ...]) -> tuple[SentenceMatch, ...]:
    """Match complete sentences or one omitted U+201C at source index zero.

    No whitespace normalization, punctuation stripping, interior edit, word
    replacement, numeric change, or sentence-count change is permitted.
    """
    if not isinstance(source, tuple) or not isinstance(reported, tuple):
        raise ValueError('Internal sentence collections must be tuples')
    if not 1 <= len(source) <= 1024 or len(source) != len(reported):
        raise ValueError('Source and reported sentence counts must match')
    if any(not isinstance(item, str) for item in (*source, *reported)):
        raise ValueError('Sentence entries must be strings')
    return tuple(_compare(i, expected, actual) for i, (expected, actual) in enumerate(zip(source, reported), 1))


def encode_sentence_matches(matches: tuple[SentenceMatch, ...]) -> list[SentenceMatchJSON]:
    """Convert the internal tuple to the explicit JSON array representation."""
    result: list[SentenceMatchJSON] = []
    for expected_sequence, item in enumerate(matches, 1):
        if type(item.sequence) is not int or item.sequence != expected_sequence:
            raise ValueError('Sentence match sequence must be exact consecutive integers')
        validated = _compare(item.sequence, item.source_text, item.reported_text)
        if item.status != validated.status:
            raise ValueError('Declared text-match status does not describe the actual texts')
        result.append({'sequence': item.sequence, 'source_text': item.source_text,
            'reported_text': item.reported_text, 'status': item.status})
    return result


def decode_sentence_matches(value: object) -> tuple[SentenceMatch, ...]:
    """Validate a persisted JSON array before constructing internal matches."""
    if not isinstance(value, list) or not 1 <= len(value) <= 1024:
        raise ValueError('Expected nonempty bounded JSON sentence-match array')
    result: list[SentenceMatch] = []
    for expected_sequence, raw in enumerate(value, 1):
        if not isinstance(raw, dict) or set(raw) != {'sequence', 'source_text', 'reported_text', 'status'}:
            raise ValueError('Missing, extra, or wrong sentence-match fields')
        sequence: object = raw['sequence']
        source: object = raw['source_text']
        reported: object = raw['reported_text']
        status: object = raw['status']
        if type(sequence) is not int or sequence != expected_sequence:
            raise ValueError('Sequence must be an exact consecutive integer')
        if not isinstance(source, str) or not isinstance(reported, str):
            raise ValueError('Source and reported text must be strings')
        match = _compare(sequence, source, reported)
        if status != match.status:
            raise ValueError('Persisted status does not describe actual text difference')
        result.append(match)
    return tuple(result)


class BoundaryPin(TypedDict):
    path: str
    bytes: int
    sha256: str


class SubtitleUnit(TypedDict):
    id: str
    zh: str
    en: str


class SubtitleGroup(TypedDict):
    start_seconds: float
    end_seconds: float
    zh: str
    en: str


class BoundaryEvent(TypedDict):
    sequence: int
    type: Literal['SentenceBoundary']
    offset_ticks: str
    duration_ticks: str
    text: str


class BoundaryRecord(TypedDict):
    schema: Literal['faith-power-same-stream-boundaries-v1']
    machine_id: str
    observed_at_utc: str
    cue_id: str
    request: BoundaryPin
    audio: BoundaryPin | None
    raw_metadata: BoundaryPin | None
    communicate_source: BoundaryPin
    timebase: str
    status: Literal['complete', 'failed']
    stream_complete: bool
    stream_error: str | None
    actual_wire_calls: int
    events: list[BoundaryEvent]


class BoundaryFields(TypedDict):
    provider_boundaries: BoundaryPin
    subtitle_groups: list[SubtitleGroup]
    sentence_matches: list[SentenceMatchJSON]


class SynthesisSummary(TypedDict):
    measured_narration: BoundaryPin
    failed: int


def validate_wire_text(value: object) -> str:
    if (not isinstance(value, str) or not value.strip()
            or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value) is not None
            or len(escape(value).encode('utf-8')) > 4096):
        raise ValueError('One-wire narration requires unchanged compatible text within the escaped UTF-8 chunk')
    return value


def checked_file_pin(path: Path) -> BoundaryPin:
    if not path.is_file() or path.is_symlink():
        raise ValueError('Expected a regular non-symlink input')
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def parse_file_pin(value: object) -> BoundaryPin:
    if not isinstance(value, dict) or set(value) != {'path', 'bytes', 'sha256'}:
        raise ValueError('Missing or wrong file-pin fields')
    path, size, digest = value['path'], value['bytes'], value['sha256']
    if (not isinstance(path, str) or not Path(path).is_absolute()
            or type(size) is not int or size < 0 or not isinstance(digest, str)
            or re.fullmatch('[0-9a-f]{64}', digest) is None):
        raise ValueError('Invalid file-pin types or format')
    result: BoundaryPin = {'path': path, 'bytes': size, 'sha256': digest}
    if checked_file_pin(Path(path)) != result:
        raise ValueError('Pinned file changed')
    return result


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = item
    return result


def _json(text: str) -> object:
    value: object = json.loads(text, object_pairs_hook=_unique_pairs)
    return value


def _ticks(value: object) -> int:
    if (not isinstance(value, str) or re.fullmatch('0|[1-9][0-9]{0,19}', value) is None
            or int(value) > 18446744073709551615):
        raise ValueError('Ticks require canonical uint64 decimal strings')
    return int(value)


def _events(value: object) -> list[BoundaryEvent]:
    if not isinstance(value, list) or len(value) > 1024:
        raise ValueError('Expected a bounded JSON event array')
    result: list[BoundaryEvent] = []
    previous = -1
    for sequence, raw in enumerate(value, 1):
        if not isinstance(raw, dict) or set(raw) != {'sequence', 'type', 'offset_ticks', 'duration_ticks', 'text'}:
            raise ValueError('Missing or wrong boundary-event fields')
        start, duration = _ticks(raw['offset_ticks']), _ticks(raw['duration_ticks'])
        text = raw['text']
        if (type(raw['sequence']) is not int or raw['sequence'] != sequence
                or raw['type'] != 'SentenceBoundary' or not isinstance(text, str) or not text.strip()
                or start <= previous or duration <= 0 or start + duration > 18446744073709551615):
            raise ValueError('Invalid boundary sequence, text, or clock')
        previous = start
        result.append({'sequence': sequence, 'type': 'SentenceBoundary', 'offset_ticks': str(start),
                       'duration_ticks': str(duration), 'text': text})
    return result


def parse_raw_boundaries(path: Path) -> list[BoundaryEvent]:
    if path.stat().st_size > 1048576:
        raise ValueError('Metadata exceeds one MiB')
    rows: list[BoundaryEvent] = []
    for line in path.read_text('utf-8').splitlines():
        raw = _json(line)
        if not isinstance(raw, dict) or set(raw) != {'type', 'offset', 'duration', 'text'}:
            raise ValueError('Missing or wrong provider metadata fields')
        start, duration = raw['offset'], raw['duration']
        if type(start) is not int or type(duration) is not int:
            raise ValueError('Provider ticks require exact integers')
        text = raw['text']
        if not isinstance(text, str) or raw['type'] != 'SentenceBoundary':
            raise ValueError('Expected SentenceBoundary text')
        rows.append({'sequence': len(rows) + 1, 'type': 'SentenceBoundary',
                     'offset_ticks': str(start), 'duration_ticks': str(duration), 'text': text})
    return _events(rows)


def parse_boundary_record(value: object) -> BoundaryRecord:
    fields = {'schema', 'machine_id', 'observed_at_utc', 'cue_id', 'request', 'audio',
              'raw_metadata', 'communicate_source', 'timebase', 'status', 'stream_complete',
              'stream_error', 'actual_wire_calls', 'events'}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('Missing or wrong boundary-record fields')
    machine, cue, observed = value['machine_id'], value['cue_id'], value['observed_at_utc']
    status, error, calls, complete = value['status'], value['stream_error'], value['actual_wire_calls'], value['stream_complete']
    if (value['schema'] != 'faith-power-same-stream-boundaries-v1' or value['timebase'] != '1/10000000'
            or not isinstance(machine, str) or not machine.strip() or not isinstance(cue, str) or not cue.strip()
            or not isinstance(observed, str) or not observed.endswith('Z')
            or status not in ('complete', 'failed') or type(complete) is not bool
            or type(calls) is not int or not 0 <= calls <= 2
            or (error is not None and (not isinstance(error, str) or not error))):
        raise ValueError('Invalid boundary-record discriminator or types')
    try:
        datetime.strptime(observed, '%Y-%m-%dT%H:%M:%S.%fZ' if '.' in observed else '%Y-%m-%dT%H:%M:%SZ')
    except ValueError as timestamp_error:
        raise ValueError('Invalid UTC observation timestamp') from timestamp_error
    request, source = parse_file_pin(value['request']), parse_file_pin(value['communicate_source'])
    audio = None if value['audio'] is None else parse_file_pin(value['audio'])
    raw = None if value['raw_metadata'] is None else parse_file_pin(value['raw_metadata'])
    events = _events(value['events'])
    if status == 'complete':
        if not complete or error is not None or calls != 1 or audio is None or audio['bytes'] <= 0 or raw is None or not events:
            raise ValueError('Complete stream requires one wire and nonempty audio/metadata')
        if parse_raw_boundaries(Path(raw['path'])) != events:
            raise ValueError('Envelope differs from the original provider JSONL')
    elif complete or not isinstance(error, str):
        raise ValueError('Failed stream requires its error and false completion')
    return {'schema': 'faith-power-same-stream-boundaries-v1', 'machine_id': machine,
            'observed_at_utc': observed, 'cue_id': cue, 'request': request, 'audio': audio,
            'raw_metadata': raw, 'communicate_source': source, 'timebase': '1/10000000',
            'status': 'complete' if status == 'complete' else 'failed', 'stream_complete': complete,
            'stream_error': error, 'actual_wire_calls': calls, 'events': events}


def subtitle_units(value: object, zh: str, en: str) -> tuple[SubtitleUnit, ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 1024:
        raise ValueError('Frozen nonempty subtitle_units are required before synthesis')
    units: list[SubtitleUnit] = []
    for raw in value:
        if not isinstance(raw, dict) or set(raw) != {'id', 'zh', 'en'}:
            raise ValueError('Missing or wrong subtitle-unit fields')
        identifier, chinese, english = raw['id'], raw['zh'], raw['en']
        if (not isinstance(identifier, str) or not identifier.strip() or not isinstance(chinese, str)
                or not chinese.strip() or not isinstance(english, str) or not english.strip()):
            raise ValueError('Subtitle-unit values require nonempty strings')
        units.append({'id': identifier, 'zh': chinese, 'en': english})
    if (len({row['id'] for row in units}) != len(units)
            or ''.join(row['zh'] for row in units) != zh or ''.join(row['en'] for row in units) != en):
        raise ValueError('Subtitle units must exactly concatenate to frozen zh/en')
    return tuple(units)


def boundary_fields(record_pin: object, *, machine_id: str, cue_id: str, audio: object,
                    request: object, units: tuple[SubtitleUnit, ...], speech_seconds: float) -> BoundaryFields:
    pinned = parse_file_pin(record_pin)
    record = parse_boundary_record(_json(Path(pinned['path']).read_text('utf-8')))
    request_pin = parse_file_pin(request)
    invocation = _json(Path(request_pin['path']).read_text('utf-8'))
    if (not isinstance(invocation, dict) or set(invocation) != {'machine_id', 'observed_at_utc', 'evidence_source', 'provider', 'request', 'cue_id'}
            or invocation['machine_id'] != machine_id or invocation['cue_id'] != cue_id
            or invocation['provider'] != {'provider_id': 'edge-tts', 'tool_version': '7.3.1'}):
        raise ValueError('Wrong actual provider invocation envelope')
    payload = invocation['request']
    if (not isinstance(payload, dict) or set(payload) != {'text', 'voice', 'rate', 'pitch', 'volume', 'audio_format', 'cache_salt'}
            or any(not isinstance(item, str) for item in payload.values())
            or any(not payload[key] for key in ('text', 'voice', 'rate', 'pitch', 'volume'))
            or payload['audio_format'] != 'mp3' or payload['text'] != ''.join(unit['zh'] for unit in units)):
        raise ValueError('Provider request differs from exact frozen subtitle units')
    if (record['status'] != 'complete' or record['machine_id'] != machine_id or record['cue_id'] != cue_id
            or record['audio'] != parse_file_pin(audio) or record['request'] != request_pin):
        raise ValueError('Boundary record does not bind this complete cue/audio/request/machine')
    if type(speech_seconds) is not float or not math.isfinite(speech_seconds) or not 0 < speech_seconds <= 3600:
        raise ValueError('Actual finite measured speech duration required')
    matches = reconcile_sentence_texts(tuple(unit['zh'] for unit in units), tuple(row['text'] for row in record['events']))
    groups: list[SubtitleGroup] = []
    speech_end = math.floor(speech_seconds * 10000000)
    events = record['events']
    for index, (unit, event) in enumerate(zip(units, events)):
        start = _ticks(event['offset_ticks'])
        end = min(start + _ticks(event['duration_ticks']), speech_end)
        if index + 1 < len(events):
            end = min(end, _ticks(events[index + 1]['offset_ticks']))
        if not 0 <= start < end <= speech_end:
            raise ValueError('Provider boundary lies outside actual measured audio')
        groups.append({'start_seconds': start / 10000000, 'end_seconds': end / 10000000,
                       'zh': unit['zh'], 'en': unit['en']})
    return {'provider_boundaries': pinned, 'subtitle_groups': groups, 'sentence_matches': encode_sentence_matches(matches)}


@runtime_checkable
class _Wire(Protocol):
    def __call__(self) -> AsyncIterator[object]: ...


@runtime_checkable
class _Save(Protocol):
    def save_sync(self, audio_fname: str, metadata_fname: str) -> None: ...


@runtime_checkable
class _Factory(Protocol):
    def __call__(self, text: str, voice: str, *, rate: str, volume: str, pitch: str,
                 boundary: Literal['SentenceBoundary']) -> object: ...


@dataclass
class _CaptureState:
    inner: _Save | None = None
    actual_wire_calls: int = 0
    audio_bytes: int = 0
    metadata_bytes: int = 0
    event_count: int = 0
    stream_complete: bool = False
    error: str | None = None
    target: Path | None = None
    finished: BoundaryPin | None = None


class SentenceBoundaryCapture:
    """Official provider module seam; public save_sync remains the sole writer."""
    def __init__(self, module: object, *, destination: Path, machine_id: str,
                 communicate_source: object, tool_version: str, limits: object) -> None:
        if tool_version != '7.3.1' or not isinstance(machine_id, str) or not machine_id.strip():
            raise ValueError('Single-wire hook requires the qualified 7.3.1 runtime and machine')
        self.source = parse_file_pin(communicate_source)
        self.producer_source = checked_file_pin(Path(__file__))
        factory: object = getattr(module, 'Communicate', None)
        if not isinstance(factory, _Factory) or checked_file_pin(Path(inspect.getfile(factory))) != self.source:
            raise ValueError('Communicate factory differs from qualified actual source pin')
        if (not isinstance(limits, dict) or set(limits) != {'max_audio_bytes', 'max_metadata_bytes', 'max_events'}
                or any(type(limits[key]) is not int for key in limits)):
            raise ValueError('Missing or wrong sentence_boundary_limits')
        audio, metadata_bytes, events = limits['max_audio_bytes'], limits['max_metadata_bytes'], limits['max_events']
        if (type(audio) is not int or type(metadata_bytes) is not int or type(events) is not int
                or not 1 <= audio <= 16777216 or not 1 <= metadata_bytes <= 1048576 or not 1 <= events <= 1024):
            raise ValueError('Invalid bounded capture limits')
        self.max_audio, self.max_metadata, self.max_events = audio, metadata_bytes, events
        self.factory, self.destination, self.machine_id = factory, destination.resolve(), machine_id
        self.state: _CaptureState | None = None

    @property
    def peak_bytes_per_cue(self) -> int:
        return self.max_audio * 2 + self.max_metadata * 8 + 1048576

    def Communicate(self, text: str, voice: str, *, rate: str, volume: str, pitch: str) -> SentenceBoundaryCapture:
        if self.state is not None and self.state.finished is None:
            raise ValueError('Previous capture has not been finalized; replay refused')
        state = _CaptureState()
        self.state = state
        validate_wire_text(text)
        try:
            inner = self.factory(text, voice, rate=rate, volume=volume, pitch=pitch, boundary='SentenceBoundary')
            wire: object = getattr(inner, '_Communicate__stream', None)
            if not isinstance(inner, _Save) or not isinstance(wire, _Wire):
                raise ValueError('Qualified private wire or public save_sync is unavailable')
            state.inner = inner
            async def guarded_wire() -> AsyncIterator[object]:
                state.actual_wire_calls += 1
                if state.actual_wire_calls != 1:
                    raise ValueError('Automatic transport replay refused; partial evidence retained')
                async for event in wire():
                    if not isinstance(event, dict) or not isinstance(event.get('type'), str):
                        raise ValueError('Malformed actual wire event')
                    if event['type'] == 'audio':
                        data: object = event.get('data')
                        if not isinstance(data, bytes):
                            raise ValueError('Audio chunk must be bytes')
                        state.audio_bytes += len(data)
                        if state.audio_bytes > self.max_audio:
                            raise ValueError('Audio capture limit exceeded')
                    elif event['type'] == 'SentenceBoundary':
                        state.metadata_bytes += len((json.dumps(event) + '\n').encode('utf-8'))
                        state.event_count += 1
                        if state.metadata_bytes > self.max_metadata or state.event_count > self.max_events:
                            raise ValueError('Metadata capture limit exceeded')
                        if set(event) != {'type', 'offset', 'duration', 'text'}:
                            raise ValueError('Missing or wrong actual boundary fields')
                        if type(event['offset']) is not int or type(event['duration']) is not int:
                            raise ValueError('Provider ticks require exact integers')
                    else:
                        raise ValueError('Unexpected qualified wire event')
                    yield event
            setattr(inner, '_Communicate__stream', guarded_wire)
        except Exception as error:
            state.error = repr(error)
            raise
        return self

    def save_sync(self, audio_fname: str) -> None:
        state = self.state
        if state is None or state.inner is None:
            raise ValueError('No actual Communicate instance')
        target = Path(audio_fname).resolve()
        if target.parent != self.destination or target.suffix != '.mp3':
            raise ValueError('Capture output must be an owned fresh MP3 leaf')
        raw = target.with_suffix('.stream.jsonl')
        if state.target is not None or target.exists() or raw.exists() or target.with_suffix('.boundaries.json').exists():
            raise ValueError('Existing capture output or repeated save refused')
        state.target = target
        try:
            state.inner.save_sync(str(target), str(raw))
            if state.actual_wire_calls != 1 or state.audio_bytes <= 0 or not parse_raw_boundaries(raw):
                raise ValueError('Incomplete actual audio/boundary stream')
            state.stream_complete = True
        except Exception as error:
            state.error = repr(error)
            raise

    def finish(self, target: Path, *, cue_id: str, request: object) -> BoundaryPin:
        state = self.state
        if state is None:
            state = _CaptureState(error='Provider did not construct Communicate')
            self.state = state
        if state.finished is not None:
            return parse_file_pin(state.finished)
        raw, envelope = target.with_suffix('.stream.jsonl'), target.with_suffix('.boundaries.json')
        if target.resolve().parent != self.destination or (state.target is not None and state.target != target.resolve()):
            raise ValueError('Capture finalization target differs')
        events: list[BoundaryEvent] = []
        try:
            if raw.is_file():
                events = parse_raw_boundaries(raw)
        except Exception as error:
            state.stream_complete = False
            state.error = repr(error)
        record: BoundaryRecord = {'schema': 'faith-power-same-stream-boundaries-v1',
            'machine_id': self.machine_id, 'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'cue_id': cue_id, 'request': parse_file_pin(request),
            'audio': checked_file_pin(target) if target.is_file() else None,
            'raw_metadata': checked_file_pin(raw) if raw.is_file() else None,
            'communicate_source': self.source, 'timebase': '1/10000000',
            'status': 'complete' if state.stream_complete else 'failed', 'stream_complete': state.stream_complete,
            'stream_error': None if state.stream_complete else (state.error or 'Stream did not complete'),
            'actual_wire_calls': state.actual_wire_calls, 'events': events}
        validated = parse_boundary_record(record)
        with envelope.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(validated, stream, ensure_ascii=False, indent=2)
        parse_boundary_record(_json(envelope.read_text('utf-8')))
        state.finished = checked_file_pin(envelope)
        return state.finished
