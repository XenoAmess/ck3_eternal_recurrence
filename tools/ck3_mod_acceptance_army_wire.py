"""Recover one already executed Army query from published host wire ranges."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import zlib
from typing import Literal, TypedDict
from ck3_mod_acceptance_background_types import (
    JsonObject, WireEvidenceCodec, WireEvidenceCommit, WireFileIdentity,
    json_object, wire_evidence_codec, wire_evidence_commit,
    wire_file_identity, wire_file_identity_value,
)

MAX_RANGE = 32 * 1024 * 1024
STEP = "query-army-strengths-v1"


class WireBookmark(TypedDict):
    schema: Literal["ck3-army-wire-bookmark-v2"]
    path: str
    wire_evidence_codec: WireEvidenceCodec
    file_identity: WireFileIdentity
    physical_offset: str
    logical_offset: str
    stream_id: str | None
    record_count: int | None


class WireRange(TypedDict):
    begin: str
    end: str
    bytes: int
    sha256: str


class WireLineProof(TypedDict):
    logical_range: WireRange
    member_physical_range: WireRange


class WireProof(TypedDict):
    schema: Literal["ck3-army-wire-range-proof-v2"]
    path: str
    wire_evidence_codec: WireEvidenceCodec
    identity_binding: Literal["native-handle", "legacy-fstat"]
    file_identity_at_read: WireFileIdentity
    physical_range: WireRange
    logical_range: WireRange
    native_request_id: str
    query_sequence: int
    request_line: WireLineProof
    response_line: WireLineProof
    complete_Driver_packet: Literal[False]
    query_reissued: Literal[False]
    source: str


@dataclass(frozen=True)
class _Bookmark:
    path: Path
    codec: WireEvidenceCodec
    identity: WireFileIdentity | None
    legacy_identity: tuple[int, int] | None
    physical: int
    logical: int
    stream_id: str | None
    count: int | None


@dataclass(frozen=True)
class _Record:
    value: JsonObject
    begin: int
    end: int
    physical_begin: int
    physical_end: int
    line: bytes


def need(ok: object, why: str) -> None:
    if not ok:
        raise ValueError(why)


def _integer(value: object, name: str, maximum: int = (1 << 64) - 1) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= maximum:
        raise ValueError(name)
    return value


def _decimal(value: object, name: str) -> int:
    if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        raise ValueError(name)
    return _integer(int(value), name)


def _path(value: object) -> Path:
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise ValueError("absolute original wire path required")
    p = Path(value)
    need(not p.is_symlink(), "wire symlink refused")
    return p.resolve(strict=True)


def _range(begin: int, data: bytes) -> WireRange:
    return WireRange(begin=str(begin), end=str(begin + len(data)),
                     bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def _read(p: Path, begin: int, end: int | None, *,
          identity: WireFileIdentity | None = None,
          legacy: tuple[int, int] | None = None) -> tuple[bytes, WireFileIdentity, int]:
    need(not p.is_symlink(), "wire symlink refused")
    with p.open("rb") as stream:
        before = os.fstat(stream.fileno())
        actual = wire_file_identity(stream.fileno())
        need(stat.S_ISREG(before.st_mode), "regular host wire required")
        need(identity is None or actual == identity, "wire file identity changed")
        need(legacy is None or (before.st_dev, before.st_ino) == legacy,
             "legacy plain fstat identity changed")
        limit = before.st_size if end is None else end
        need(0 <= begin <= limit <= before.st_size and limit - begin <= MAX_RANGE,
             "bounded published wire range required")
        stream.seek(begin)
        raw = stream.read(limit - begin)
        after = os.fstat(stream.fileno())
        need(wire_file_identity(stream.fileno()) == actual and
             after.st_size >= before.st_size and len(raw) == limit - begin,
             "wire replaced/truncated during bounded read")
    return raw, actual, limit


def _one_line(data: bytes) -> JsonObject:
    need(data.endswith(b"\n") and len(data.splitlines(keepends=True)) == 1,
         "one complete JSONL record per gzip member required")
    return json_object(json.loads(data))


def _members(raw: bytes, physical: int, logical: int) -> tuple[bytes, list[_Record]]:
    output = bytearray()
    rows: list[_Record] = []
    position = 0
    while position < len(raw):
        start = position
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        member = bytearray()
        try:
            while position < len(raw) and not decoder.eof:
                chunk = raw[position:position + 65536]
                block = decoder.decompress(chunk, MAX_RANGE - len(output) - len(member) + 1)
                member.extend(block)
                need(len(output) + len(member) <= MAX_RANGE, "wire logical output exceeds bound")
                position += len(chunk) - len(decoder.unused_data)
                need(not decoder.unconsumed_tail, "wire logical output exceeds bound")
        except zlib.error as error:
            raise ValueError("gzip member header/CRC invalid") from error
        need(decoder.eof and position > start, "truncated gzip member refused")
        line = bytes(member)
        value = _one_line(line)
        begin = logical + len(output)
        rows.append(_Record(value, begin, begin + len(line),
                            physical + start, physical + position, line))
        need(len(rows) <= 100000, "wire record count exceeds bound")
        output.extend(member)
    return bytes(output), rows


def _commit(value: object, p: Path) -> WireEvidenceCommit:
    commit = wire_evidence_commit(value)
    need(Path(commit["path"]).resolve(strict=True) == p, "commit wire path differs")
    return commit


def mark(path: str | Path, *, codec: WireEvidenceCodec = "plain",
         commit: object = None) -> WireBookmark:
    selected = wire_evidence_codec(codec)
    p = _path(str(Path(path).absolute()))
    if selected == "gzip-members":
        closed = _commit(commit, p)
        begin = _decimal(closed["last_member_physical_begin"], "member begin")
        end = _decimal(closed["completed_physical_offset"], "physical offset")
        logical = _decimal(closed["logical_bytes"], "logical offset")
        raw, identity, _ = _read(p, begin, end, identity=closed["file_identity"])
        need(hashlib.sha256(raw).hexdigest() == closed["last_member_sha256"],
             "published member hash differs")
        data, rows = _members(raw, begin, 0)
        need(len(rows) == 1 and logical >= len(data), "published boundary is not one complete member")
        stream_id, count = closed["stream_id"], closed["record_count"]
    else:
        need(commit is None, "plain wire cannot use gzip commit")
        with p.open("rb") as stream:
            before = os.fstat(stream.fileno())
            identity = wire_file_identity(stream.fileno())
            need(stat.S_ISREG(before.st_mode), "regular host wire required")
            end = before.st_size
            if end:
                stream.seek(end - 1)
                need(stream.read(1) == b"\n", "wire append in progress; no query submitted")
            need(wire_file_identity(stream.fileno()) == identity and
                 os.fstat(stream.fileno()).st_size >= end, "wire changed during mark")
        logical, stream_id, count = end, None, None
    return WireBookmark(schema="ck3-army-wire-bookmark-v2", path=str(p),
        wire_evidence_codec=selected, file_identity=identity,
        physical_offset=str(end), logical_offset=str(logical),
        stream_id=stream_id, record_count=count)


def _bookmark(value: object) -> _Bookmark:
    row = json_object(value)
    p = _path(row.get("path"))
    if set(row) == {"path", "file_identity", "offset"}:
        old = row["file_identity"]
        need(isinstance(old, list) and len(old) == 2, "legacy plain file identity")
        if not isinstance(old, list) or len(old) != 2:
            raise ValueError("legacy plain file identity")
        legacy = (_integer(old[0], "legacy device", (1 << 128) - 1),
                  _integer(old[1], "legacy inode", (1 << 128) - 1))
        offset = _integer(row["offset"], "legacy plain offset")
        return _Bookmark(p, "plain", None, legacy, offset, offset, None, None)
    need(set(row) == {"schema", "path", "wire_evidence_codec", "file_identity",
         "physical_offset", "logical_offset", "stream_id", "record_count"} and
         row.get("schema") == "ck3-army-wire-bookmark-v2", "wire bookmark schema/fields")
    codec = wire_evidence_codec(row["wire_evidence_codec"])
    identity = wire_file_identity_value(row["file_identity"])
    physical = _decimal(row["physical_offset"], "physical offset")
    logical = _decimal(row["logical_offset"], "logical offset")
    if codec == "gzip-members":
        sid = row["stream_id"]
        if not isinstance(sid, str) or re.fullmatch("[0-9a-f]{32}", sid) is None:
            raise ValueError("wire stream identity")
        count = _integer(row["record_count"], "record count", (1 << 53) - 1)
        need(count > 0, "published record count required")
        return _Bookmark(p, codec, identity, None, physical, logical, sid, count)
    need(physical == logical and row["stream_id"] is None and row["record_count"] is None,
         "plain bookmark coordinates/stream fields")
    return _Bookmark(p, codec, identity, None, physical, logical, None, None)


def recover(bookmark: object, compact: object, *, native_revision: int,
            army_ids: list[int], profile: str,
            end_commit: object = None) -> tuple[JsonObject, WireProof]:
    summary = json_object(compact)
    sequence = _integer(summary.get("query_sequence"), "actual compact query sequence")
    need(summary.get("accepted") is True and sequence > 0, "accepted compact query required")
    need(profile in ("ordinary_core_v1", "observed_history_full_v1") and
         summary.get("army_strengths_profile") == profile, "same actual query profile")
    _integer(native_revision, "actual native revision")
    need(isinstance(army_ids, list) and bool(army_ids) and
         all(type(i) is int and -(1 << 31) <= i < (1 << 31) and i != -1 for i in army_ids) and
         len(set(army_ids)) == len(army_ids), "typed actual Army IDs, including zero")
    boundary = _bookmark(bookmark)
    if boundary.codec == "gzip-members":
        closed = _commit(end_commit, boundary.path)
        end = _decimal(closed["completed_physical_offset"], "physical end")
        logical_end = _decimal(closed["logical_bytes"], "logical end")
        need(closed["stream_id"] == boundary.stream_id and
             closed["file_identity"] == boundary.identity and
             closed["record_count"] >= (boundary.count or 0), "wire commit stream/file/count changed")
        raw, actual, _ = _read(boundary.path, boundary.physical, end, identity=boundary.identity)
        complete, records = _members(raw, boundary.physical, boundary.logical)
        need(logical_end == boundary.logical + len(complete) and
             len(records) == closed["record_count"] - (boundary.count or 0),
             "wire committed logical length/count differs")
        if records:
            last = records[-1]
            need(last.physical_begin == _decimal(closed["last_member_physical_begin"], "last member") and
                 hashlib.sha256(raw[last.physical_begin - boundary.physical:]).hexdigest() ==
                 closed["last_member_sha256"], "final committed member differs")
    else:
        need(end_commit is None, "plain wire cannot use gzip commit")
        raw, actual, _ = _read(boundary.path, boundary.physical, None,
                              identity=boundary.identity, legacy=boundary.legacy_identity)
        raw = raw[:raw.rfind(b"\n") + 1]
        complete, records, position = raw, [], boundary.logical
        for line in complete.splitlines(keepends=True):
            value = json_object(json.loads(line))
            records.append(_Record(value, position, position + len(line), position, position + len(line), line))
            position += len(line)
    responses = []
    for record in records:
        value = record.value
        message = value.get("message")
        if value.get("direction") == "dll-to-python" and isinstance(message, dict):
            result = message.get("result")
            if (message.get("type") == "command_result" and isinstance(result, dict) and
                    result.get("step") == STEP and type(result.get("query_sequence")) is int and
                    result.get("query_sequence") == sequence):
                responses.append(record)
    need(len(responses) == 1, "unique already executed result unavailable; never resubmit")
    response = responses[0]
    message = json_object(response.value["message"])
    request_id = message.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("actual response request ID")
    need(type(message.get("protocol_version")) is int and message["protocol_version"] == 1 and
         message.get("ok") is True, "actual successful protocol response")
    requests = [r for r in records if r.value.get("direction") == "python-to-dll" and
        isinstance(r.value.get("message"), dict) and
        json_object(r.value["message"]).get("type") == "execute_step" and
        json_object(r.value["message"]).get("request_id") == request_id]
    need(len(requests) == 1 and requests[0].begin < response.begin, "unique preceding original request")
    request = requests[0]
    sent, result = json_object(request.value["message"]), json_object(message["result"])
    sent_ids = sent.get("army_ids")
    need(type(sent.get("protocol_version")) is int and sent["protocol_version"] == 1 and
         sent.get("step") == STEP and type(sent.get("expected_revision")) is int and
         sent["expected_revision"] == native_revision and sent.get("army_strengths_profile") == profile and
         isinstance(sent_ids, list) and all(type(i) is int for i in sent_ids) and sent_ids == army_ids,
         "original request scope/profile/native revision differs")
    for key in ("accepted", "status", "query_sequence", "army_strengths_profile", "army_observed_phase_coverage"):
        need(type(result.get(key)) is type(summary.get(key)) and result.get(key) == summary.get(key),
             "native/compact " + key)

    def line_proof(record: _Record) -> WireLineProof:
        data = raw[record.physical_begin - boundary.physical:record.physical_end - boundary.physical]
        return WireLineProof(logical_range=_range(record.begin, record.line),
                             member_physical_range=_range(record.physical_begin, data))

    return result, WireProof(schema="ck3-army-wire-range-proof-v2", path=str(boundary.path),
        wire_evidence_codec=boundary.codec,
        identity_binding="legacy-fstat" if boundary.legacy_identity is not None else "native-handle",
        file_identity_at_read=actual, physical_range=_range(boundary.physical, raw),
        logical_range=_range(boundary.logical, complete), native_request_id=request_id,
        query_sequence=sequence, request_line=line_proof(request), response_line=line_proof(response),
        source="existing shared host wire published physical and logical range",
        complete_Driver_packet=False, query_reissued=False)


def _proof_range(value: object) -> WireRange:
    row = json_object(value)
    need(set(row) == {"begin", "end", "bytes", "sha256"}, "exact wire proof range required")
    begin = _decimal(row["begin"], "proof range begin")
    end = _decimal(row["end"], "proof range end")
    size = _integer(row["bytes"], "proof range bytes", MAX_RANGE)
    digest = row["sha256"]
    if not isinstance(digest, str) or re.fullmatch("[0-9a-f]{64}", digest) is None:
        raise ValueError("wire proof range SHA256")
    need(end >= begin and end - begin == size, "wire proof range extent differs")
    return WireRange(begin=str(begin), end=str(end), bytes=size, sha256=digest)


def read_response_line(proof: object) -> bytes:
    """Re-read one pinned response, retaining compressed and logical domains."""
    row = json_object(proof)
    need(row.get("schema") == "ck3-army-wire-range-proof-v2", "wire response proof schema")
    p = _path(row.get("path"))
    codec = wire_evidence_codec(row.get("wire_evidence_codec"))
    identity = wire_file_identity_value(row.get("file_identity_at_read"))
    need(row.get("identity_binding") in ("native-handle", "legacy-fstat"), "wire identity binding")
    physical = _proof_range(row.get("physical_range"))
    logical = _proof_range(row.get("logical_range"))
    line = json_object(row.get("response_line"))
    need(set(line) == {"logical_range", "member_physical_range"}, "exact response line coordinates")
    logical_line = _proof_range(line["logical_range"])
    member = _proof_range(line["member_physical_range"])
    need(int(physical["begin"]) <= int(member["begin"]) < int(member["end"]) <= int(physical["end"]) and
         int(logical["begin"]) <= int(logical_line["begin"]) < int(logical_line["end"]) <= int(logical["end"]),
         "response line lies outside original recovered range")
    raw, _, _ = _read(p, int(member["begin"]), int(member["end"]), identity=identity)
    need(hashlib.sha256(raw).hexdigest() == member["sha256"], "response member physical SHA differs")
    if codec == "gzip-members":
        data, records = _members(raw, int(member["begin"]), int(logical_line["begin"]))
        need(len(records) == 1, "one response member required")
    else:
        need(member == logical_line, "plain response physical/logical ranges differ")
        data = raw
        _one_line(data)
    need(len(data) == logical_line["bytes"] and
         hashlib.sha256(data).hexdigest() == logical_line["sha256"], "response logical SHA/length differs")
    return data
