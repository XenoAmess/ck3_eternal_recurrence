"""Validated cold-runner boundaries; no native operations or qualification."""
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, NotRequired
import json
from postload_wire import decimal64,numeric32,safe_integer

from postload_models import JsonObject, object_value, u64, FilePin
from postload_common_models import text, flag, objects, strings


@dataclass(frozen=True)
class Options:
    repo: Path
    build_dir: Path
    machine_build_record: Path
    output_root: Path


class Identity(TypedDict):
    pid: int
    created: int


class Ready(TypedDict):
    mode: str
    ready: bool
    census_complete: bool
    armed_thread_count: int


class AuditRow(TypedDict):
    tid: int
    created: int
    complete: bool
    eflags: int
    dr: list[int]


class CheckedGeneration(TypedDict):
    thread_id: int
    thread_generation: int
    created: int


class AuditResult(TypedDict):
    checked_live_owned_generations: list[CheckedGeneration]
    retired_generations: list[list[int]]
    independent_peer_rows: int
    all_required_owned_DR_vectors_equal: bool
    independent_preexisting_TF_preserved_before_target_release: NotRequired[bool]


class BinaryFile(TypedDict):
    path: str
    size: int
    sha256: str


class BuildRecord(TypedDict):
    machine_id: str
    returncode: int
    argv: list[str]
    source_pins: list[FilePin]


class DefenderReport(TypedDict):
    status: str
    receipt: str
    manifest: str
    receipt_sha256: str


class BuildReport(TypedDict):
    build_succeeded: bool
    defender_exclusions: DefenderReport


class SystemReceipt(TypedDict):
    status: str
    admin_token: bool
    system_token_sid: str
    files: list[BinaryFile]
    missing_requested_paths: list[str]
    verified_requested_paths: list[str]
    partial_mutation: bool
    observed_extensions_unchanged: bool
    observed_processes_unchanged: bool
    observed_prior_settings_preserved: bool


class BuildGate(TypedDict):
    machine_id: str
    observed_at_utc: str
    producer: FilePin
    original_build: FilePin
    SYSTEM_receipt: FilePin
    SYSTEM_manifest: FilePin
    files: list[BinaryFile]
    no_CK3_contact: bool


@dataclass(frozen=True)
class TargetResult:
    raw: JsonObject
    return_failures: int
    audit_failures: int
    foreign_body_calls: int
    target_body_calls: int
    actual_body_calls: int
    other_access_calls: int
    loaded_context: int
    post_arithmetic_flags: int
    worker_tid: int


def load_object(path: Path, maximum: int = 262144) -> JsonObject:
    if not 0 <= path.stat().st_size <= maximum:
        raise ValueError('cold object stat cap')
    with path.open('rb') as stream:
        payload = stream.read(maximum + 1)
    if len(payload) > maximum:
        raise ValueError('cold object read cap')
    return object_value(json.loads(payload), 'cold JSON object')


def target_result(value: object) -> TargetResult:
    row = object_value(value, 'actual target result')
    return TargetResult(raw=row,
        return_failures=numeric32(row.get('return_failures'), 'return failures'),
        audit_failures=numeric32(row.get('audit_failures'), 'audit failures'),
        foreign_body_calls=numeric32(row.get('foreign_body_calls'), 'foreign body calls'),
        target_body_calls=numeric32(row.get('target_body_calls'), 'target body calls'),
        actual_body_calls=decimal64(row.get('actual_body_calls'), 'actual body calls'),
        other_access_calls=decimal64(row.get('other_access_calls'), 'other access calls'),
        loaded_context=decimal64(row.get('loaded_context'), 'loaded context'),
        post_arithmetic_flags=numeric32(row.get('post_arithmetic_flags'), 'post arithmetic flags'),
        worker_tid=numeric32(row.get('worker_tid'), 'worker TID'))


def ready_value(value: object) -> Ready:
    row=object_value(value,'actual native READY')
    count=numeric32(row.get('armed_thread_count'),'armed thread count')
    if not count:raise ValueError('Native READY needs a nonempty census')
    return Ready(mode=text(row.get('mode'),'READY mode'),ready=flag(row.get('ready'),'READY flag'),
        census_complete=flag(row.get('census_complete'),'READY census complete'),armed_thread_count=count)


def debug_vector(value: object) -> list[int]:
    if not isinstance(value, list) or len(value) != 6:
        raise ValueError('exact six-register vector')
    return [decimal64(number, 'debug register') for number in value]


def audit_rows(value: object) -> list[AuditRow]:
    return [AuditRow(tid=numeric32(row.get('tid'), 'audit TID'),
        created=decimal64(row.get('created'), 'audit creation'),
        complete=flag(row.get('complete'), 'audit complete'),
        eflags=numeric32(row.get('eflags'), 'audit flags'),
        dr=debug_vector(row.get('dr'))) for row in objects(value, 'independent audits')]


def pin_projection(value: object) -> FilePin:
    row = object_value(value, 'original pin')
    path = text(row.get('path'), 'original path')
    size = safe_integer(row.get('bytes'), 'original bytes')
    sha = text(row.get('sha256'), 'original SHA')
    if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
        raise ValueError('original SHA format')
    return FilePin(path=path, bytes=size, sha256=sha)


def binary_files(value: object) -> list[BinaryFile]:
    result: list[BinaryFile] = []
    for row in objects(value, 'SYSTEM files'):
        pin = pin_projection(dict(path=row.get('path'), bytes=row.get('size'), sha256=row.get('sha256')))
        result.append(BinaryFile(path=pin['path'], size=pin['bytes'], sha256=pin['sha256']))
    return result


def build_record(value: object) -> BuildRecord:
    row = object_value(value, 'original build record')
    return BuildRecord(machine_id=text(row.get('machine_id'), 'build machine'),
        returncode=u64(row.get('returncode'), 'successful build return code'),
        argv=strings(row.get('argv'), 'original build argv'),
        source_pins=[pin_projection(item) for item in objects(row.get('source_pins'), 'build sources')])


def build_report(value: object) -> BuildReport:
    row = object_value(value, 'native build report')
    ex = object_value(row.get('defender_exclusions'), 'exact exclusion report')
    return BuildReport(build_succeeded=flag(row.get('build_succeeded'), 'actual build succeeded'),
        defender_exclusions=DefenderReport(status=text(ex.get('status'), 'exclusion status'),
            receipt=text(ex.get('receipt'), 'SYSTEM receipt path'),
            manifest=text(ex.get('manifest'), 'SYSTEM manifest path'),
            receipt_sha256=text(ex.get('receipt_sha256'), 'SYSTEM receipt SHA')))


def system_receipt(value: object) -> SystemReceipt:
    row = object_value(value, 'actual SYSTEM receipt')
    return SystemReceipt(status=text(row.get('status'), 'SYSTEM status'),
        admin_token=flag(row.get('admin_token'), 'SYSTEM admin token'),
        system_token_sid=text(row.get('system_token_sid'), 'SYSTEM SID'),
        files=binary_files(row.get('files')),
        missing_requested_paths=strings(row.get('missing_requested_paths'), 'missing paths'),
        verified_requested_paths=strings(row.get('verified_requested_paths'), 'verified paths'),
        partial_mutation=flag(row.get('partial_mutation'), 'partial mutation'),
        observed_extensions_unchanged=flag(row.get('observed_extensions_unchanged'), 'extensions unchanged'),
        observed_processes_unchanged=flag(row.get('observed_processes_unchanged'), 'processes unchanged'),
        observed_prior_settings_preserved=flag(row.get('observed_prior_settings_preserved'), 'prior settings preserved'))
