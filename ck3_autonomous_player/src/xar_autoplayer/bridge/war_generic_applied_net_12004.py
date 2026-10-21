"""Offline generic positive wallet NET evidence for exact CK3 1.20.0.4.

No observer, SDK, game, registry or process access. RuntimeIdentity contains
caller-supplied observations from the existing frozen public binding and
OpenProcess/EnumProcessModules path; this module never invents those observations.
Financial evidence survives missing strict runtime/date qualification.
"""
from __future__ import annotations

from dataclasses import dataclass
import builtins
import hashlib
import json
import os
from pathlib import Path
from typing import Literal, NoReturn, TypedDict

U64 = (1 << 64) - 1
EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
STATIC_A05 = "e107fbe8f6d1df3d9edec1f67f53bcd8a5bd0f6d9f83515318a0ef2f33af84bb"
TERMS = ("value_2c0", "value_2c8", "value_28", "value_30")
DATE32_SOURCES = {
    "war_payment_window_12004.cpp": "2f862af8cb83a13c420b8c28b12b82a3379fa678a7c168b1f85ab8b6f04fae83",
    "army_natural_phase_scope_12004.cpp": "011d4c84ea39d700a6d91ce9f95a1014de06ab9696b41ac93183ad485bb7ba0c",
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("generic applied NET: " + message)


def obj(value: object, name: str) -> dict[str, object]:
    # The sole dynamic JSON-object boundary; values remain object until checked.
    if not isinstance(value, dict):
        raise ValueError(name + " must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(name + " key must be text")
        result[key] = item
    return result


def req(row: dict[str, object], key: str) -> object:
    if key not in row:
        raise ValueError("missing " + key)
    return row[key]


def num(value: object, name: str, low: int = 0, high: int = U64) -> int:
    if not isinstance(value, int) or type(value) is not int or not low <= value <= high:
        raise ValueError(name + " must be an exact bounded integer")
    return value


def dec(value: object, name: str) -> int:
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise ValueError(name + " must be a canonical decimal string")
    number = int(value)
    need(str(number) == value and number <= U64, name + " decimal range")
    return number


def flag(row: dict[str, object], key: str, expected: bool) -> None:
    need(req(row, key) is expected, key + " bool differs")


def seq(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(name + " must be an array")
    return [item for item in value]


def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        need(key not in result, "duplicate JSON field " + key)
        result[key] = value
    return result


def bad_constant(value: str) -> NoReturn:
    raise ValueError("nonfinite JSON number " + value)


def parse_json(payload: bytes) -> object:
    value: object = json.loads(payload, object_pairs_hook=pairs, parse_constant=bad_constant)
    return value


class PinWire(TypedDict):
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class FilePin:
    path: str
    bytes: int
    sha256: str

    def read(self, maximum: int = 1048576) -> builtins.bytes:
        need(isinstance(self.path, str) and bool(self.path), "pin path")
        num(self.bytes, "pin bytes", 0, maximum)
        need(isinstance(self.sha256, str) and len(self.sha256) == 64
             and all(c in "0123456789abcdef" for c in self.sha256), "pin SHA")
        path = Path(self.path)
        need(path.stat().st_size == self.bytes, "pin stat size")
        with path.open("rb") as stream:
            payload = stream.read(maximum + 1)
        need(len(payload) == self.bytes and hashlib.sha256(payload).hexdigest() == self.sha256,
             "pin bytes/SHA")
        return payload

    def wire(self) -> PinWire:
        return PinWire(path=self.path, bytes=self.bytes, sha256=self.sha256)


@dataclass(frozen=True)
class SourceBinding:
    machine_id: str
    evidence: FilePin
    journal_pointer: str
    static_source_a05: FilePin


@dataclass(frozen=True)
class Session:
    pid: int
    birth: int
    generation: int
    window: int
    game_state: int
    actor: int
    epoch: int | None
    revision: int
    date: int | None
    day: int | None

    def identity(self) -> tuple[int, int, int, int, int, int, int | None]:
        return (self.pid, self.birth, self.generation, self.window,
                self.game_state, self.actor, self.epoch)


def session(value: object) -> Session:
    row = obj(value, "session")
    flag(row, "same_owned_process_no_load_window", True)
    epoch = req(row, "loaded_game_epoch")
    date = req(row, "native_date_raw")
    day = req(row, "absolute_day_raw")
    return Session(
        num(req(row, "pid"), "PID", 1, (1 << 32) - 1),
        num(req(row, "process_create_time_100ns"), "birth", 1),
        num(req(row, "connection_generation"), "generation", 1),
        num(req(row, "controlled_window_id"), "window", 1),
        num(req(row, "game_state_identity_witness"), "GameState", 1),
        num(req(row, "player_character_full_id"), "actor", 1, (1 << 32) - 2),
        None if epoch is None else num(epoch, "load epoch", 1),
        num(req(row, "snapshot_revision"), "revision", 1),
        None if date is None else num(date, "observed date"),
        None if day is None else num(day, "observed day", 0, (1 << 32) - 1))


def pointer(root: object, path: str) -> object:
    need(isinstance(path, str) and (path == "" or path.startswith("/")), "JSON pointer")
    value = root
    if path:
        for part in path[1:].split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            value = req(obj(value, "JSON pointer parent"), key)
    return value


@dataclass(frozen=True)
class RuntimeIdentity:
    """Normalized existing OS and frozen-public facts, not new native fields.

    Both FileIDs are (volume serial, file index) canonical u64 strings.
    The producer wait is the actual build owner record, with source_pins.
    Missing observations remain None at the Date32Window boundary.
    """
    pid: int
    created: str
    frozen_bridge: FilePin
    loaded_bridge: FilePin
    frozen_file_id: tuple[str, str]
    loaded_file_id: tuple[str, str]
    original_build_wait: FilePin
    os_loaded_module_receipt: FilePin | None = None
    build_output_receipt: FilePin | None = None


@dataclass(frozen=True)
class Date32Window:
    before_owner: object
    after_owner: object
    runtime: RuntimeIdentity | None = None


class Date32Pending(ValueError):
    """Actor may catch locally; limited financial evidence remains available."""


def owner(value: object) -> tuple[Session, int]:
    row = obj(value, "public owner binding")
    need(req(row, "schema") == "xar.maintenance.parent_postload.owner-binding.v1",
         "existing public owner schema")
    result = Session(
        num(req(row, "pid"), "owner PID", 1, (1 << 32) - 1),
        dec(req(row, "process_create_time_100ns"), "owner birth"),
        dec(req(row, "connection_generation"), "owner generation"),
        dec(req(row, "controlled_window_id"), "owner window"),
        dec(req(row, "game_state_identity_witness"), "owner GameState"),
        num(req(row, "player_character_full_id"), "owner actor", 1, (1 << 32) - 2),
        None, dec(req(row, "native_revision"), "owner revision"),
        num(req(row, "date_raw"), "owner date32", 0, (1 << 32) - 1),
        num(req(row, "absolute_day_raw"), "owner day32", 0, (1 << 32) - 1))
    need(all((result.birth, result.generation, result.window, result.game_state, result.revision)),
         "nonzero public owner identities")
    return result, dec(req(row, "character"), "owner Character")


def validate_date32_window(window: Date32Window, entry: Session, returned: Session,
                           character: int, current: Session) -> None:
    """Validate actual outer frames; their revisions may bracket the callback."""
    before, first_character = owner(window.before_owner)
    after, last_character = owner(window.after_owner)
    need(first_character == last_character == character, "outer Character changed")
    need(before.identity() == after.identity() == entry.identity() == returned.identity() == current.identity(),
         "outer process/session/player/GameState changed")
    need(entry.revision == returned.revision and before.revision <= entry.revision
         <= current.revision <= after.revision,
         "callback revision is not inside actual outer frames")
    for label, low, middle, high, final in (
        ("date32", before.date, entry.date, after.date, returned.date),
        ("day32", before.day, entry.day, after.day, returned.day)):
        lo = num(low, label, 0, (1 << 32) - 1)
        mid = num(middle, label, 0, (1 << 32) - 1)
        hi = num(high, label, 0, (1 << 32) - 1)
        observed = num(current.date if label == "date32" else current.day, label, 0, (1 << 32) - 1)
        need(mid == final and lo <= mid <= observed <= hi,
             label + " outside the same ordered window")


def receipt_pin(value: object, label: str) -> FilePin:
    row = obj(value, label)
    need(set(row) == {"path", "bytes", "sha256"}, label + " exact pin fields")
    path, sha = req(row, "path"), req(row, "sha256")
    if not isinstance(path, str) or not isinstance(sha, str):
        raise ValueError(label + " pin text")
    return FilePin(path, num(req(row, "bytes"), label + " bytes"), sha)


def same_pin(first: FilePin, second: FilePin) -> bool:
    return (os.path.normcase(str(Path(first.path).resolve()))
            == os.path.normcase(str(Path(second.path).resolve()))
            and first.bytes == second.bytes and first.sha256 == second.sha256)


def runtime_date32(runtime: RuntimeIdentity | None, current: Session, machine: str) -> RuntimeProof:
    if runtime is None or runtime.os_loaded_module_receipt is None or runtime.build_output_receipt is None:
        raise Date32Pending("pinned actual OS loaded-new-DLL receipt and build-output DLL receipt required")
    need(num(runtime.pid, "OS PID", 1, (1 << 32) - 1) == current.pid
         and dec(runtime.created, "OS birth") == current.birth, "OS process changed")
    need(type(runtime.frozen_file_id) is tuple and type(runtime.loaded_file_id) is tuple
         and len(runtime.frozen_file_id) == len(runtime.loaded_file_id) == 2, "two-part FileID")
    for value in (*runtime.frozen_file_id, *runtime.loaded_file_id):
        dec(value, "FileID")
    need(runtime.frozen_file_id == runtime.loaded_file_id, "loaded FileID differs from frozen")
    need(same_pin(runtime.frozen_bridge, runtime.loaded_bridge), "loaded/frozen bridge differs")
    build = obj(parse_json(runtime.original_build_wait.read()), "original date32 build")
    need(req(build, "machine_id") == machine, "date32 producer machine")
    flag(build, "original_Popen", True)
    flag(build, "original_wait", True)
    num(req(build, "pid"), "build PID", 1, (1 << 32) - 1)
    dec(req(build, "created"), "build birth")
    need(num(req(build, "returncode"), "build return") == 0, "date32 build failed")
    # Actual post-build sidecar; standard native-msvc reports remain unchanged.
    output = obj(parse_json(runtime.build_output_receipt.read()), "actual build output")
    need(req(output, "schema") == "xar.date32.build-output.v1"
         and req(output, "machine_id") == machine, "output schema/machine")
    need(same_pin(receipt_pin(req(output, "producer_original_wait"), "output producer"),
                  runtime.original_build_wait), "output producer differs from original wait")
    dll = receipt_pin(req(output, "bridge_DLL"), "actual output bridge DLL")
    need(same_pin(dll, runtime.frozen_bridge), "actual output DLL differs from frozen bridge")
    gate_pin = receipt_pin(req(output, "actual_SYSTEM_gate"), "actual SYSTEM gate")
    gate = obj(parse_json(gate_pin.read()), "actual SYSTEM readback")
    need(req(gate, "machine_id") == machine, "SYSTEM gate machine")
    flag(gate, "actual_SYSTEM_verified", True)
    need(same_pin(receipt_pin(req(gate, "bridge_DLL"), "SYSTEM bridge"), dll),
         "SYSTEM gate and output DLL differ")
    argv = seq(req(build, "argv"), "build argv")
    need(all(isinstance(x, str) for x in argv), "build argv text")
    arguments = [str(x) for x in argv]
    need(arguments.count("--build-dir") == arguments.count("--source-dir") == 1, "exact build/source argument")
    build_index, source_index = arguments.index("--build-dir") + 1, arguments.index("--source-dir") + 1
    need(max(build_index, source_index) < len(arguments), "missing build/source directory")
    build_dir = Path(arguments[build_index]).resolve()
    source_dir = Path(arguments[source_index]).resolve()
    wait_path = Path(runtime.original_build_wait.path).resolve()
    gate_path = Path(gate_pin.path).resolve()
    need(Path(dll.path).resolve().parent == build_dir
         and len(wait_path.parents) >= 2 and len(gate_path.parents) >= 2
         and wait_path.parents[1] == gate_path.parents[1] == build_dir.parent,
         "output/producer do not share the actual build root")
    source_values = seq(req(build, "source_pins"), "build source manifest")
    need(len(source_values) == 1, "date32 producer binds one exact4770 manifest")
    manifest_pin = receipt_pin(source_values[0], "source manifest")
    need(same_pin(receipt_pin(req(output, "source_manifest"), "output source manifest"), manifest_pin),
         "output source manifest differs from original producer")
    need(Path(manifest_pin.path).resolve() == source_dir / "SOURCE-MANIFEST.actual.json",
         "actual producer source manifest path")
    manifest = obj(parse_json(manifest_pin.read(4 * 1024 * 1024)), "compiled source manifest")
    need(req(manifest, "schema") == "xar.r08.date32.exact4770-source.v1"
         and req(manifest, "machine_id") == machine, "compiled manifest identity")
    sources = seq(req(manifest, "source_inputs"), "manifest sources")
    need(len(sources) == 4770, "exact date32 source closure")
    found: dict[str, str] = {}
    for source_value in sources:
        row = obj(source_value, "manifest source")
        name_value = req(row, "destination_relative_path")
        need(isinstance(name_value, str), "source destination text")
        name = Path(str(name_value)).name
        if name in DATE32_SOURCES:
            source = receipt_pin(req(row, "source"), "date32 source")
            need(name not in found, "duplicate date32 source")
            found[name] = source.sha256
    need(found == DATE32_SOURCES, "actual build does not bind both exact date32 repairs")
    # A pinned OS sidecar retains only normal EnumProcessModules/FileID facts.
    # This is not a field added to the native SDK or a claim that it exists now.
    observed = obj(parse_json(runtime.os_loaded_module_receipt.read()), "actual OS module observation")
    need(req(observed, "machine_id") == machine
         and num(req(observed, "pid"), "observed PID", 1, (1 << 32) - 1) == current.pid
         and dec(req(observed, "created"), "observed birth") == current.birth, "OS receipt process differs")
    need(dec(req(observed, "module_base"), "observed module base") > 0, "OS module base absent")
    need(same_pin(receipt_pin(req(observed, "module"), "OS observed module"), runtime.loaded_bridge),
         "OS receipt DLL differs from loaded bridge")
    ids = seq(req(observed, "file_id"), "OS FileID")
    need(len(ids) == 2 and tuple(dec(x, "observed FileID") for x in ids)
         == tuple(dec(x, "declared FileID") for x in runtime.loaded_file_id), "OS receipt FileID differs")
    runtime.frozen_bridge.read(64 * 1024 * 1024)
    return RuntimeProof(pid=runtime.pid, created=runtime.created,
        frozen_bridge=runtime.frozen_bridge.wire(), loaded_bridge=runtime.loaded_bridge.wire(),
        frozen_file_id=list(runtime.frozen_file_id), loaded_file_id=list(runtime.loaded_file_id),
        original_build_wait=runtime.original_build_wait.wire(),
        os_loaded_module_receipt=runtime.os_loaded_module_receipt.wire(),
        build_output_receipt=runtime.build_output_receipt.wire(), compiled_source_manifest=manifest_pin.wire())


class RuntimeProof(TypedDict):
    pid: int
    created: str
    frozen_bridge: PinWire
    loaded_bridge: PinWire
    frozen_file_id: list[str]
    loaded_file_id: list[str]
    original_build_wait: PinWire
    os_loaded_module_receipt: PinWire
    build_output_receipt: PinWire
    compiled_source_manifest: PinWire


class CallbackProof(TypedDict):
    journal_sequence: str
    account_character: str
    account_character_full_id: int
    wallet_wrapper: str
    context: str
    context_terms_raw: dict[str, str]
    applied_net_raw: str
    before_balance_bits: str
    after_balance_bits: str
    parent_return_rva: str
    callback_pid: int
    callback_birth: str
    callback_generation: str
    callback_revision: str
    observed_date_raw: str | None
    observed_day_raw: int | None
    entry_event_sequence: str
    returned_event_sequence: str
    event_clock: str
    event_thread: int


class AppliedNetProof(TypedDict):
    schema: Literal["xar.generic-wallet.applied-positive-net.v1"]
    machine_id: str
    source: PinWire
    source_pointer: str
    static_source: PinWire
    status: Literal["POSITIVE_APPLIED_NET_PROVED", "NO_GENERIC_CALLBACK_EVIDENCE"]
    callbacks: list[CallbackProof]
    date_qualified: bool
    date_status: Literal["NOT_REQUESTED", "PENDING", "QUALIFIED"]
    date_diagnostic: str | None
    paid_maintenance_raw: None
    payer: None
    cadence: None
    full_R08: Literal[False]
    runtime_evidence: RuntimeProof | None


def event(value: object) -> tuple[int, int, int]:
    row = obj(value, "callback event")
    return (num(req(row, "clock_identity"), "event clock", 1),
            num(req(row, "sequence"), "event sequence", 1),
            num(req(row, "thread_id"), "event thread", 1, (1 << 32) - 1))


def callback(row: dict[str, object], current: Session) -> tuple[CallbackProof, Session, Session]:
    for key in ("original_called", "original_returned", "clock_thread_order_matches", "session_matches"):
        flag(row, key, True)
    flag(row, "tls_depth_exceeded", False)
    entry = session(req(row, "session_entry"))
    returned = session(req(row, "session_return"))
    need(entry.identity() == returned.identity() == current.identity(), "callback session changed")
    need((entry.revision, entry.date, entry.day) == (returned.revision, returned.date, returned.day)
         and entry.revision <= current.revision, "callback revision/date changed")
    e, z = event(req(row, "entry_event")), event(req(row, "returned_event"))
    need(e[0] == z[0] and e[2] == z[2] and e[1] < z[1], "callback event clock/thread/order")
    before, after = obj(req(row, "before"), "before wallet"), obj(req(row, "after"), "after wallet")
    for frame in (before, after):
        flag(frame, "capture_complete", True)
        need(num(req(frame, "failed_reads"), "failed reads") == 0, "incomplete wallet")
    identity = ("character", "character_id", "character_magic", "character_extension", "wrapper")
    for frame in (before, after):
        for key in identity:
            num(req(frame, key), key)
    need(all(req(before, k) == req(after, k) for k in identity), "account identity changed")
    character = num(req(before, "character"), "Character", 1)
    actor = num(req(before, "character_id"), "account FullID", 1, (1 << 32) - 2)
    extension = num(req(before, "character_extension"), "extension", 1, U64 - 0xF8)
    wrapper = num(req(before, "wrapper"), "wrapper", 1)
    need(num(req(before, "character_magic"), "Character magic") == 0x43686172
         and actor == current.actor and wrapper == extension + 0xF8
         and num(req(row, "receiver"), "receiver", 1) == wrapper
         and num(req(row, "second_pointer"), "account argument", 1) == character, "personal account alias")
    balances = [num(req(f, "wrapper_balance_bits"), "wallet bits") for f in (before, after)]
    need(all(num(req(f, "personal_gold_bits"), "personal bits") == balances[i]
             for i, f in enumerate((before, after))), "wrapper is not observed personal slot")
    amount = num(req(row, "amount_raw"), "positive ADD amount", 1, (1 << 63) - 1)
    need(balances[1] == (balances[0] + amount) & U64, "actual balance change differs")
    context = obj(req(row, "generic_wallet_context_v1"), "generic context")
    need(num(req(context, "schema_version"), "context version") == 1
         and num(req(context, "source_entry_rva"), "source entry") == 0x28A6D10
         and num(req(context, "source_wallet_return_rva"), "wallet return") == 0x28A6D7C
         and req(context, "attribution_scope") == "raw_source_context_and_unwind_parent_only"
         and req(context, "maintenance_attribution") == "unclosed", "generic source differs")
    frames = [obj(req(context, key), "context " + key) for key in ("before", "after")]
    values: list[tuple[int, ...]] = []
    contexts: list[int] = []
    for frame in frames:
        flag(frame, "capture_complete", True)
        flag(frame, "context_stable", True)
        need(num(req(frame, "failed_reads"), "context reads") == 0, "context incomplete")
        first = num(req(frame, "context_identity_before"), "context before", 1)
        need(first == num(req(frame, "context_identity_after"), "context after", 1), "context identity drift")
        contexts.append(first)
        values.append(tuple(num(req(frame, k), k, -(1 << 63), (1 << 63) - 1) for k in TERMS))
    need(contexts[0] == contexts[1] and values[0] == values[1], "four-slot endpoints changed")
    raw = values[0][0] - values[0][1] - values[0][2] - values[0][3]
    computed = (raw + (1 << 63)) % (1 << 64) - (1 << 63)
    need(computed == amount == num(req(context, "before_computed_add_raw"), "formula amount", -(1 << 63), (1 << 63) - 1), "four-slot formula differs")
    flag(context, "before_formula_matches_amount", True)
    flag(context, "context_values_stable", True)
    trace = obj(req(context, "parent_trace"), "actual unwind")
    flag(trace, "capture_succeeded", True)
    flag(trace, "truncated", False)
    flag(trace, "parent_in_same_image", True)
    base = num(req(trace, "module_base"), "image base", 1, U64 - 102518784)
    need(num(req(trace, "module_image_size"), "image size") == 102518784, "exact .4 image")
    addresses = [num(x, "unwind address", 1) for x in seq(req(trace, "frames_absolute"), "unwind frames")]
    need(0 < len(addresses) < 32 and len(addresses) == num(req(trace, "reported_frame_count"), "frame count"), "incomplete unwind")
    matches = [i for i, x in enumerate(addresses) if x == base + 0x28A6D7C]
    need(len(matches) == 1 and num(req(trace, "caller_match_count"), "caller count") == 1, "ambiguous wallet caller")
    index = matches[0] + 1
    need(index < len(addresses) and addresses[index] == base + 0x28F7939
         and num(req(trace, "parent_return_absolute"), "unwind parent") == addresses[index]
         and num(req(trace, "parent_return_rva"), "parent RVA") == 0x28F7939, "settlement unwind parent differs")
    proof = CallbackProof(
        journal_sequence=str(num(req(row, "journal_sequence"), "journal sequence", 1)),
        account_character=str(character), account_character_full_id=actor,
        wallet_wrapper=str(wrapper), context=str(contexts[0]),
        context_terms_raw={k: str(v) for k, v in zip(TERMS, values[0])},
        applied_net_raw=str(amount), before_balance_bits=str(balances[0]), after_balance_bits=str(balances[1]),
        parent_return_rva=str(0x28F7939), callback_pid=entry.pid, callback_birth=str(entry.birth),
        callback_generation=str(entry.generation), callback_revision=str(entry.revision),
        observed_date_raw=None if entry.date is None else str(entry.date), observed_day_raw=entry.day,
        entry_event_sequence=str(e[1]), returned_event_sequence=str(z[1]), event_clock=str(e[0]), event_thread=e[2])
    return proof, entry, returned


def consume_positive_applied_net(journal: object, binding: SourceBinding, *,
                                strict_date32: Date32Window | None = None) -> AppliedNetProof:
    """Return observed NET only; absent callbacks never imply zero expense."""
    need(isinstance(binding.machine_id, str) and bool(binding.machine_id), "machine ID")
    original = parse_json(binding.evidence.read())
    need(pointer(original, binding.journal_pointer) == journal, "input differs from pinned original")
    need(binding.static_source_a05.sha256 == STATIC_A05, "exact adopted a05 source required")
    binding.static_source_a05.read(16384)
    row = obj(journal, "payment journal")
    need(req(row, "machine_id") == binding.machine_id
         and req(row, "game_version") == "1.20.0.4"
         and num(req(row, "steam_build_id"), "Steam build", 0, (1 << 32) - 1) == 25734779
         and str(req(row, "executable_sha256")).lower() == EXE, "exact source/machine")
    for key in ("installed", "controlled_window_admitted", "read_complete"):
        flag(row, key, True)
    for key in ("install_failure_flags", "overwritten", "publication_failures"):
        need(num(req(row, key), key) == 0, "lost/incomplete journal")
    need(req(row, "balance_boundary") == "whole_original_callback_entry_return"
         and req(row, "maintenance_attribution") == "unclosed", "callback scope promoted")
    current = session(req(row, "current_session"))
    sampling = obj(req(row, "sampling"), "sampling")
    flag(sampling, "available", True)
    flag(sampling, "capture_enabled", True)
    flag(sampling, "busy", False)
    need(num(req(sampling, "active_captures"), "active captures") == 0, "capture still active")
    num(req(sampling, "epoch"), "sampling epoch", 1)
    records = seq(req(row, "records"), "records")
    need(len(records) <= 512 and len(records) == num(req(sampling, "retained_records"), "retained"), "retention count")
    numbers = [num(req(obj(x, "record"), "journal_sequence"), "record sequence", 1) for x in records]
    need(numbers == sorted(set(numbers)), "duplicate/unordered journal")
    if numbers:
        need(num(req(row, "oldest_sequence"), "oldest", 1) <= numbers[0] <= numbers[-1]
             <= num(req(row, "latest_sequence"), "latest", 1), "journal bounds")
    callbacks: list[CallbackProof] = []
    pending: str | None = None
    runtime_evidence: RuntimeProof | None = None
    for value in records:
        item = obj(value, "record")
        kind = num(req(item, "kind"), "callback kind", 0, 4)
        caller = num(req(item, "caller_return_rva"), "callback caller")
        if kind != 2 or caller != 0x28A6D7C:
            continue
        proof, entry, returned = callback(item, current)
        callbacks.append(proof)
        if strict_date32 is not None:
            try:
                validate_date32_window(strict_date32, entry, returned,
                                       int(proof["account_character"]), current)
                runtime_evidence = runtime_date32(strict_date32.runtime, entry, binding.machine_id)
            except (ValueError, OSError) as exc:
                pending = type(exc).__name__ + ": " + str(exc)
    qualified = bool(callbacks) and strict_date32 is not None and pending is None
    status: Literal["POSITIVE_APPLIED_NET_PROVED", "NO_GENERIC_CALLBACK_EVIDENCE"] = (
        "POSITIVE_APPLIED_NET_PROVED" if callbacks else "NO_GENERIC_CALLBACK_EVIDENCE")
    date_status: Literal["NOT_REQUESTED", "PENDING", "QUALIFIED"] = (
        "QUALIFIED" if qualified else "NOT_REQUESTED" if strict_date32 is None else "PENDING")
    return AppliedNetProof(schema="xar.generic-wallet.applied-positive-net.v1",
        machine_id=binding.machine_id, source=binding.evidence.wire(), source_pointer=binding.journal_pointer,
        static_source=binding.static_source_a05.wire(), status=status, callbacks=callbacks,
        date_qualified=qualified, date_status=date_status, date_diagnostic=pending,
        paid_maintenance_raw=None, payer=None, cadence=None, full_R08=False,
        runtime_evidence=runtime_evidence if qualified else None)


def require_strict_date32(proof: AppliedNetProof) -> None:
    if proof["date_qualified"] is not True:
        raise Date32Pending(proof["date_diagnostic"] or proof["date_status"])
