"""Exact, bounded replay proof for three closed SDK aggregate logs.
No source mutations and no retirement capability. Historical machine stays unknown.
"""
from __future__ import annotations
import argparse
import ctypes
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from typing import BinaryIO, Callable, Iterator, Literal, Protocol, TypeAlias, TypeGuard
from ctypes import wintypes

ROOT = Path("C:/ck3-e04-resume-20261020-a01/r08-old-sdk-exact-replay-2245-a01")
AUTHOR = ROOT / "source-candidate-a01"
BASE = Path("C:/ck3-war-episode04-research-20261004-a01")
LOSS = Path("C:/ck3-e04-resume-20261020-a01/r08-r223-lossless-replacement-2200-a01")
RET = Path("C:/ck3-e04-resume-20261020-a01/r08-r223-exact-retention-2100-a01")
ADMISSION = ROOT / "capacity/OLD-SDK-EXACT-REPLAY-SOURCE4-2245-ADMISSION.actual-a01.json"
ADMISSION_SHA = "b3c17b9654de131cc84993d981b59f551dd5e5c1c20dcfa4ad690ae25fd1e872"
SUPPORT_SHA = "863849c61bae97e6d4a28ce6e7608d36ef06e8fcc453a625f70acb4a709808dd"
RET_SHA = "de1bb3c810fa361cf5f6cd63a9ba25aa5e89c614e6df1b1afc9373cf3af7a249"
if hashlib.sha256((LOSS / "lossless_exact5.py").read_bytes()).hexdigest() != SUPPORT_SHA:
    raise ValueError("Read-only support source changed")
if hashlib.sha256((RET / "retire_exact_duplicates.py").read_bytes()).hexdigest() != RET_SHA:
    raise ValueError("Read-only identity source changed")
sys.path.insert(0, str(LOSS))
import lossless_exact5 as support

Json: TypeAlias = None | bool | int | float | str | list["Json"] | dict[str, "Json"]
Group: TypeAlias = Literal["r165", "r175", "r177"]
CHUNK = 256 * 1024
RESPONSE_LIMIT = 16 * 1024 * 1024
LINE_LIMIT = 64 * 1024 * 1024
RSS_GUARD = 768 * 1024 * 1024
DEADLINE = datetime(2026, 10, 20, 22, 45, tzinfo=timezone.utc)
MACHINE = "desktop-3fevhd2-1c74096080"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_json(value: object) -> TypeGuard[Json]:
    if value is None or type(value) in (bool, int, str):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(is_json(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and is_json(item) for key, item in value.items())
    return False


def parse_json(raw: bytes) -> Json:
    value: object = json.loads(raw)
    need(is_json(value), "JSON type/finite-number domain differs")
    if not is_json(value):
        raise ValueError("JSON type domain differs")
    return value


def obj(value: Json) -> dict[str, Json]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def text(value: Json) -> str:
    if not isinstance(value, str):
        raise ValueError("JSON string required")
    return value


def integer(value: Json) -> int:
    if type(value) is not int:
        raise ValueError("Exact integer required; bool/float rejected")
    need(0 <= value <= 2**53 - 1, "Integer out of safe JSON range")
    return value


def sha(value: Json) -> str:
    result = text(value)
    need(re.fullmatch("[0-9a-f]{64}", result) is not None, "Canonical SHA required")
    return result


def group_value(value: str) -> Group:
    if value == "r165":
        return "r165"
    if value == "r175":
        return "r175"
    if value == "r177":
        return "r177"
    raise ValueError("Unknown exact group")


@dataclass(frozen=True)
class Spec:
    group: Group
    dirname: str
    log_bytes: int
    file_id: str
    mtime_ns: str
    session_bytes: int
    session_sha: str

    @property
    def root(self) -> Path:
        return BASE / self.dirname

    @property
    def log(self) -> Path:
        return self.root / "mcp-calls.jsonl"


SPECS: tuple[Spec, ...] = (
    Spec("r165", "native-live-day15-r0165-a01", 303227579, "281474978776885",
         "1791163961495910000", 12479,
         "a668366bf2f47a436e3e06c7a692b5217407ef058bd62558ebe281bb73411f53"),
    Spec("r175", "native-live-r0175-a02", 191399668, "281474979252586",
         "1791230723943651800", 12425,
         "9305a4086632013f65cc876ffc91a24ea493aadc23492f430bfac8cfc2e5f750"),
    Spec("r177", "native-live-r0177-a01", 287041520, "281474979213274",
         "1791220991103649800", 12427,
         "9f56040c2554cd7285be7b4d7c12042993bd15662d8346bdb319857fb20f8e9a"),
)


def pin(path: Path, maximum: int = 2 * 1024 * 1024) -> dict[str, Json]:
    need(path.stat().st_size <= maximum, "Pin exceeds small-file bound")
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def budget() -> None:
    need(datetime.now(timezone.utc) < DEADLINE, "Hard deadline passed")
    totals = []
    for root, ceiling in ((ROOT, 4 * 1024 * 1024), (AUTHOR, 2 * 1024 * 1024)):
        total = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
        need(total <= ceiling, "Finite metadata budget exceeded")
        totals.append(total)


def write_new(name: str, value: dict[str, Json]) -> dict[str, Json]:
    budget()
    path = AUTHOR / name
    need(path.parent == AUTHOR and path.suffix == ".json", "Exact metadata basename required")
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    need(len(raw) <= 65536, "Receipt too large")
    need(sum(p.stat().st_size for p in AUTHOR.rglob("*") if p.is_file()) + len(raw) <= 2 * 1024 * 1024,
         "Author bound would overflow")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    budget()
    return pin(path)


def validate_plan() -> dict[str, Json]:
    raw = ADMISSION.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == ADMISSION_SHA, "Actual capacity pin changed")
    row = obj(parse_json(raw))
    need(row.get("schema") == "xar.capacity.old-sdk-exact-replay.source4.v1" and
         row.get("machine_id") == MACHINE and row.get("admitted") is True and
         row.get("budget_status") == "GREEN", "Actual admission differs")
    need(row.get("exact_readonly_fullstream_reconstruction_comparison_execution_admitted") is True and
         row.get("retirement_or_delete_execution_admitted") is False, "Phase grant differs")
    need(Path(text(row["author_root"])) == AUTHOR and integer(row["aggregate_ceiling_bytes"]) == 4*1024*1024,
         "Root/budget grant differs")
    sources = row["original_exact_three_inputs"]
    need(isinstance(sources, list), "Exact source list required")
    if not isinstance(sources, list):
        raise ValueError("Exact source list required")
    need(len(sources) == 3, "Exactly three inputs required")
    for source, spec in zip(sources, SPECS, strict=True):
        entry = obj(source)
        identity = obj(entry["current_stat"])
        need(Path(text(entry["path"])) == spec.log and integer(entry["bytes"]) == spec.log_bytes,
             "Exact source path/size differs")
        need(identity["mtime_ns_decimal"] == spec.mtime_ns and
             identity["file_id_decimal"] == spec.file_id and
             identity["device_decimal"] == "13886423844274364792" and
             entry["historical_game_machine_id"] == "unknown", "Source identity/origin differs")
    plan = obj(parse_json((AUTHOR / "SOURCE-PLAN.actual-a01.json").read_bytes()))
    need(plan.get("schema") == "xar.old-sdk-exact-replay.source-plan.v1" and
         plan.get("execution_machine_id") == MACHINE and
         plan.get("origin_machine_id") == "unknown" and plan.get("retire_admitted") is False,
         "Frozen source plan differs")
    return plan


@dataclass(frozen=True)
class Line:
    number: int
    byte_count: int
    sha256: str
    prefix: bytes


@dataclass
class Digest:
    byte_count: int = 0
    line_count: int = 0
    max_line: int = 0
    sha256: str = ""


def iter_lines(stream: BinaryIO, state: Digest, tick: Callable[[], None]) -> Iterator[Line]:
    aggregate = hashlib.sha256()
    current = hashlib.sha256()
    size = 0
    prefix = bytearray()
    number = 0
    while block := stream.read(CHUNK):
        tick()
        need(len(block) <= CHUNK, "Reader chunk bound violated")
        aggregate.update(block)
        state.byte_count += len(block)
        offset = 0
        while offset < len(block):
            end = block.find(b"\n", offset)
            finish = end + 1 if end >= 0 else len(block)
            piece = block[offset:finish]
            current.update(piece)
            size += len(piece)
            need(size <= LINE_LIMIT, "Aggregate line exceeds64MiB")
            if len(prefix) < 4096:
                prefix.extend(piece[:4096-len(prefix)])
            if end >= 0:
                number += 1
                need(size > 1 and number <= 10000, "Empty/excessive aggregate records")
                state.line_count = number
                state.max_line = max(state.max_line, size)
                yield Line(number, size, current.hexdigest(), bytes(prefix))
                current = hashlib.sha256()
                size = 0
                prefix.clear()
            offset = finish
    need(size == 0, "Final aggregate line lacks newline")
    need(number > 0, "Empty aggregate")
    state.sha256 = aggregate.hexdigest()


def request_id(line: Line) -> str:
    match = re.search(rb'"request":\s*\{\s*"request_id":\s*"([^"\\]+)"', line.prefix)
    need(match is not None, "Cannot bind request_id from actual line prefix")
    if match is None:
        raise ValueError("Request prefix missing")
    result = match.group(1).decode("utf-8")
    need(re.fullmatch("[A-Za-z0-9_.-]{1,240}", result) is not None and
         result not in (".", ".."), "Unsafe exact request basename")
    return result


@dataclass(frozen=True)
class Packet:
    original: dict[str, Json]
    request_id: str
    tool: str
    is_error: bool
    sdk_result_presence: Literal["present", "absent"]
    content_presence: Literal["present", "absent"]


def validate_record(value: Json, expected_id: str) -> Packet:
    row = obj(value)
    need({"at", "request", "request_identity", "is_error", "body"} <= set(row),
         "Replay envelope required field missing")
    observed = datetime.fromisoformat(text(row["at"]).replace("Z", "+00:00"))
    need(observed.tzinfo is not None, "Original timestamp needs timezone")
    request = obj(row["request"])
    need(set(request) == {"request_id", "tool", "arguments"} and
         text(request["request_id"]) == expected_id, "Request fields/id differ")
    need(bool(text(request["tool"])) and isinstance(request["arguments"], dict), "Tool/arguments invalid")
    identity = obj(row["request_identity"])
    need(set(identity) == {"path", "bytes", "sha256"}, "Request identity fields differ")
    text(identity["path"])
    integer(identity["bytes"])
    sha(identity["sha256"])
    error_flag = row["is_error"]
    if type(error_flag) is not bool:
        raise ValueError("is_error must be exact bool")
    return Packet(row, expected_id, text(request["tool"]), error_flag,
                  "present" if "sdk_result" in row else "absent",
                  "present" if "content" in row else "absent")


def encoded_record(row: dict[str, Json]) -> Iterator[bytes]:
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False)
    for text_piece in encoder.iterencode(row):
        for offset in range(0, len(text_piece), CHUNK // 4):
            part = text_piece[offset:offset+CHUNK//4].encode("utf-8")
            need(len(part) <= CHUNK, "UTF8 encoder chunk exceeded")
            yield part
    yield b"\n"


class HashSink(Protocol):
    def update(self, data: bytes) -> None: ...


def compare_record(line: Line, row: dict[str, Json], aggregate: HashSink) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    for part in encoded_record(row):
        digest.update(part)
        size += len(part)
        need(size <= LINE_LIMIT, "Rebuilt record exceeds64MiB")
        aggregate.update(part)
    actual = digest.hexdigest()
    need(size == line.byte_count and actual == line.sha256,
         "Exact replay differs line=" + str(line.number) + " original=" + line.sha256 +
         " rebuilt=" + actual + " original_bytes=" + str(line.byte_count) + " rebuilt_bytes=" + str(size))
    return actual, size


def read_held(held: support.Held, maximum: int) -> bytes:
    need(held.identity.bytes <= maximum, "Source exceeds bounded input bytes")
    os.lseek(held.fd, 0, os.SEEK_SET)
    output = bytearray()
    while block := os.read(held.fd, min(CHUNK, maximum + 1 - len(output))):
        output.extend(block)
        need(len(output) <= maximum, "Source changed/overflow")
    need(len(output) == held.identity.bytes, "Source byte count changed")
    return bytes(output)


class MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def rss() -> tuple[int, int]:
    # Narrow ctypes boundary; no pointer/FILETIME is persisted through floating point.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    kernel.K32GetProcessMemoryInfo.restype = wintypes.BOOL
    info = MemoryCounters()
    info.cb = ctypes.sizeof(info)
    if not kernel.K32GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(info), ctypes.sizeof(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    current, peak = int(info.WorkingSetSize), int(info.PeakWorkingSetSize)
    need(current <= RSS_GUARD and peak <= RSS_GUARD, "Observed RSS guard exceeded768MiB")
    return current, peak


def check_session(spec: Spec) -> dict[str, Json]:
    path = spec.root / "session-result.json"
    raw = path.read_bytes()
    need(len(raw) == spec.session_bytes and hashlib.sha256(raw).hexdigest() == spec.session_sha,
         "Exact closed session source differs")
    row = obj(parse_json(raw))
    shutdown = obj(row["shutdown"])
    need(shutdown.get("tree_gone") is True and shutdown.get("cleanup_proven") is True and
         integer(shutdown["job_active_processes_final"]) == 0, "Closed resource proof differs")
    return {"path": str(path), "bytes": len(raw), "sha256": spec.session_sha,
            "origin_machine_id": "unknown", "finished_at": row["finished_at"],
            "shutdown_original_exit_code": shutdown["ck3_exit_code"], "normal_business_exit_claimed": False}


def frozen_checks() -> None:
    row = obj(parse_json((AUTHOR / "SOURCE-FROZEN.actual-a02.json").read_bytes()))
    need(row.get("schema") == "xar.old-sdk-exact-replay.source-frozen.v1" and
         row.get("fixtures_passed") is True and integer(row["actual_mypy_returncode"]) == 0,
         "Actual frozen checks missing")
    for key, path in (("helper", AUTHOR / "replay_sdk_a02.py"), ("plan", AUTHOR / "SOURCE-PLAN.actual-a01.json")):
        need(obj(row[key]) == pin(path), "Frozen helper/plan changed")
    for key in ("fixtures", "mypy_receipt"):
        entry = obj(row[key])
        need(pin(Path(text(entry["path"]))) == entry, "Actual check source changed")
    validate_plan()
    budget()


def run_group(group: Group) -> int:
    frozen_checks()
    need(support.shared.machine_now() == MACHINE, "Current execution machine differs")
    spec = next(item for item in SPECS if item.group == group)
    tag = group + "-a02"
    session = check_session(spec)
    write_new(tag + "-ONCE.actual.json",
              {"schema": "xar.old-sdk-replay.once.v1", "execution_machine_id": MACHINE,
               "origin_machine_id": "unknown", "observed_at_utc": utc(), "group": group,
               "source": str(spec.log), "admission": pin(ADMISSION), "retire_admitted": False})
    api = support.Handles()
    handles: list[support.Held] = []
    index_path = AUTHOR / (tag + "-ordered-index.actual.jsonl.gz")
    state = Digest()
    rebuilt = hashlib.sha256()
    response_count = 0
    request_count = 0
    max_response = 0
    max_rss = 0
    start = time.monotonic()
    error: str | None = None
    unique_ids: set[str] = set()
    source_identity: dict[str, Json] | None = None
    last_tick = 0.0
    def tick() -> None:
        nonlocal last_tick, max_rss
        need(time.monotonic() - start <= 120, "Single-group120s execution bound")
        if time.monotonic() - last_tick >= 1:
            budget()
            _, observed_peak = rss()
            max_rss = max(max_rss, observed_peak)
            last_tick = time.monotonic()
    try:
        log = api.open_exact(spec.log)
        handles.append(log)
        identity = log.identity
        source_identity = identity.to_json()
        need(identity.file_id == spec.file_id and identity.volume_serial == "13886423844274364792" and
             identity.bytes == spec.log_bytes and identity.mtime_ns == spec.mtime_ns,
             "Actual aggregate generation differs")
        os.lseek(log.fd, 0, os.SEEK_SET)
        with os.fdopen(os.dup(log.fd), "rb", buffering=0) as source, index_path.open("xb") as index_file:
            with gzip.GzipFile(filename="", fileobj=index_file, mode="wb", mtime=0) as compressed:
                for line in iter_lines(source, state, tick):
                    rid = request_id(line)
                    response_path = spec.root / "responses" / (rid + ".json")
                    request_path = spec.root / "requests" / (rid + ".json")
                    response = api.open_exact(response_path)
                    request = api.open_exact(request_path)
                    handles.extend((response, request))
                    raw = read_held(response, RESPONSE_LIMIT)
                    packet = validate_record(parse_json(raw), rid)
                    row = packet.original
                    max_response = max(max_response, len(raw))
                    request_raw = read_held(request, 65536)
                    request_identity = obj(row["request_identity"])
                    need(Path(text(request_identity["path"])).resolve(strict=True) == request_path and
                         integer(request_identity["bytes"]) == len(request_raw) and
                         sha(request_identity["sha256"]) == hashlib.sha256(request_raw).hexdigest() and
                         parse_json(request_raw) == row["request"], "Request producer/response fields differ")
                    replay_sha, replay_bytes = compare_record(line, row, rebuilt)
                    api.check(response)
                    api.check(request)
                    index_row: dict[str, Json] = {
                        "line": line.number, "original_line_bytes": line.byte_count,
                        "original_line_sha256": line.sha256, "replayed_line_sha256": replay_sha,
                        "replayed_line_bytes": replay_bytes, "original_at": row["at"],
                        "request_id": rid, "tool": packet.tool, "is_error": packet.is_error,
                        "sdk_result_presence": packet.sdk_result_presence, "content_presence": packet.content_presence,
                        "response_relative_path": str(response_path.relative_to(spec.root)),
                        "response_bytes": len(raw), "response_sha256": hashlib.sha256(raw).hexdigest(),
                        "response_identity": response.identity.to_json(),
                        "request_relative_path": str(request_path.relative_to(spec.root)),
                        "request_bytes": len(request_raw), "request_sha256": hashlib.sha256(request_raw).hexdigest(),
                        "request_identity": request.identity.to_json(), "origin_machine_id": "unknown"}
                    output = (json.dumps(index_row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
                    need(len(output) <= 4096, "Index row metadata bound")
                    compressed.write(output)
                    response_count += 1
                    request_count += 1
                    unique_ids.add(rid)
                    _, peak = rss()
                    max_rss = max(max_rss, peak)
                    del raw, row, request_raw
                    if line.number % 100 == 0:
                        print(json.dumps({"group": group, "actual_verified_lines": line.number,
                                          "peak_rss_bytes": max_rss}), flush=True)
            index_file.flush()
            os.fsync(index_file.fileno())
        need(state.byte_count == spec.log_bytes and state.sha256 == rebuilt.hexdigest(),
             "Complete aggregate bytes/SHA do not match")
        for held in handles:
            api.check(held)
        tick()
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        for held in reversed(handles):
            held.close()
    status = "EXACT_REPLAY_PASS" if error is None else "FAILED_OR_PARTIAL_KEEP_ALL_ORIGINALS"
    result: dict[str, Json] = {
        "schema": "xar.old-sdk-exact-replay.group-result.v1", "execution_machine_id": MACHINE,
        "origin_machine_id": "unknown", "observed_at_utc": utc(), "group": group, "status": status,
        "source_log": str(spec.log), "source_identity": source_identity, "source_bytes_read": state.byte_count,
        "original_sha256": state.sha256 if state.sha256 else None,
        "replayed_sha256": rebuilt.hexdigest(), "actual_line_count": state.line_count,
        "actual_max_line_bytes": state.max_line, "actual_max_response_bytes": max_response,
        "actual_response_records_verified": response_count, "actual_request_records_verified": request_count,
        "unique_response_count": len(unique_ids), "ordered_index": pin(index_path) if index_path.exists() else None,
        "session_source": session, "error": error, "seconds": time.monotonic()-start,
        "source_read_chunk_max_bytes": CHUNK, "single_response_limit_bytes": RESPONSE_LIMIT,
        "line_limit_bytes": LINE_LIMIT, "observed_kernel_peak_wset_bytes": max_rss,
        "RAM_claim": "Source byte limits are not RSS limits; JSON objects inflate. Kernel peak sampled;768MiB guard.",
        "all_source_handles_closed": True, "source_mutations": 0, "large_rebuilt_output_files": 0,
        "retire_admitted": False, "retired_bytes": 0,
        "regeneration_contract": {
            "ordered_index": "gzip JSONL in original order; canonical decimal-string file identities",
            "serializer": "(json.dumps(json.loads(response_bytes),ensure_ascii=False)+newline).encode(utf8)",
            "required": "Verify every response SHA and metadata, replay ordered rows, verify original aggregate SHA/bytes",
            "future_output": "Derived new path only; never impersonate original physical evidence"},
        "future_retirement_gate": "Separate Root purpose/reference release and exact capacity/delete approval required"}
    receipt = write_new(tag + "-RESULT.actual.json", result)
    print(json.dumps({"group": group, "status": status, "result": receipt, "error": error}), flush=True)
    return 0 if error is None else 1


def self_test() -> int:
    request: dict[str, Json] = {"request_id": "fixture-1", "tool": "fixture_only", "arguments": {"id64": "18446744073709551615"}}
    request_raw = json.dumps(request, ensure_ascii=False).encode("utf-8")
    record: dict[str, Json] = {"at": "2026-10-20T00:00:00Z", "request": request,
        "request_identity": {"path": "C:/fixture-1.json", "bytes": len(request_raw),
                             "sha256": hashlib.sha256(request_raw).hexdigest()},
        "is_error": False, "body": {"unicode": "\u6d4b\u8bd5", "array": [None, True, 1, "18446744073709551615"]},
        "sdk_result": None, "content": []}
    cases: list[str] = []
    packet = validate_record(parse_json(json.dumps(record, ensure_ascii=False).encode("utf-8")), "fixture-1")
    row = packet.original
    actual = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    state = Digest()
    lines = list(iter_lines(io.BytesIO(actual + actual), state, lambda: None))
    rebuilt = hashlib.sha256()
    for line in lines:
        compare_record(line, row, rebuilt)
    need(state.line_count == 2 and state.sha256 == rebuilt.hexdigest(), "Order/UTF8/serialization roundtrip failed")
    cases.append("producer-to-consumer unicode/list/null/bool/id64-string roundtrip and duplicate ordered records")
    local: dict[str, Json] = {key: value for key, value in record.items() if key not in ("sdk_result", "content")}
    local["request"] = {"request_id": "fixture-1", "tool": "gameplay_recorder", "arguments": {}}
    local_request_bytes = json.dumps(local["request"], ensure_ascii=False).encode("utf-8")
    local["request_identity"] = {"path": "C:/fixture-1.json", "bytes": len(local_request_bytes),
                                 "sha256": hashlib.sha256(local_request_bytes).hexdigest()}
    local_packet = validate_record(local, "fixture-1")
    local_bytes = (json.dumps(local, ensure_ascii=False) + "\n").encode("utf-8")
    local_line = list(iter_lines(io.BytesIO(local_bytes), Digest(), lambda: None))[0]
    compare_record(local_line, local_packet.original, hashlib.sha256())
    need(local_packet.sdk_result_presence == "absent" and packet.sdk_result_presence == "present" and
         "sdk_result" not in local_packet.original and packet.original["sdk_result"] is None,
         "Absent SDK metadata changed to null")
    need(local_packet.original == local and packet.original == record, "Source domain changed")
    cases.append("local5field recorder and SDK7field nullable metadata distinct; no synthesis")
    invalid_cases: list[tuple[str, dict[str, Json]]] = [
        ("missing body", {k: v for k, v in record.items() if k != "body"}),
        ("wrong bool integer", {**record, "request_identity": {"path": "C:/fixture.json",
            "bytes": True, "sha256": "0"*64}}),
        ("wrong is_error type", {**record, "is_error": 0}),
    ]
    for label, invalid in invalid_cases:
        rejected = False
        try:
            validate_record(invalid, "fixture-1")
        except ValueError:
            rejected = True
        need(rejected, "Invalid fixture accepted: " + label)
        cases.append(label + " rejected")
    rejected = False
    try:
        compare_record(Line(1, len(actual), "0"*64, actual[:4096]), row, hashlib.sha256())
    except ValueError:
        rejected = True
    need(rejected, "Changed aggregate not rejected")
    cases.append("changed aggregate SHA rejected")
    rejected = False
    try:
        list(iter_lines(io.BytesIO(actual[:-1]), Digest(), lambda: None))
    except ValueError:
        rejected = True
    need(rejected, "Truncated aggregate not rejected")
    cases.append("missing trailing newline rejected")
    need(request_id(lines[0]) == "fixture-1", "Exact request prefix binding failed")
    print(json.dumps({"schema": "xar.old-sdk-exact-replay.pure-fixtures.v1",
                      "cases": cases, "case_count": len(cases), "status": "PASS",
                      "origin_machine_id": "synthetic", "real_source_reads": 0}), flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--group", choices=("r165", "r175", "r177"))
    args = parser.parse_args()
    if args.self_test:
        need(args.group is None, "Fixture/run phases separate")
        return self_test()
    need(args.group is not None, "Exact group required")
    return run_group(group_value(args.group))


if __name__ == "__main__":
    raise SystemExit(main())
