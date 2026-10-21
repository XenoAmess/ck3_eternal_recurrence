"""One source-bound publication, with explicit guards and retained original owners.

This program is inert without a separately hashed mutation admission. Tests use
isolated data and harmless children; they do not authorize a real publication.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
from typing import Callable

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]
LANE_LIMIT = 262144
SAFE_INTEGER = (1 << 53) - 1


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def obj(value: object, label: str) -> dict[str, object]:
    need(isinstance(value, dict), label + ': object required')
    result: dict[str, object] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            need(isinstance(key, str), label + ': text key required')
            if isinstance(key, str):
                result[key] = item
    return result


def text(value: object, label: str) -> str:
    need(isinstance(value, str) and bool(value), label + ': nonempty text required')
    if isinstance(value, str):
        return value
    raise ValueError(label)


def integer(value: object, label: str) -> int:
    need(type(value) is int, label + ': exact integer required')
    if type(value) is int:
        need(0 <= value <= SAFE_INTEGER, label + ': unsafe integer')
        return value
    raise ValueError(label)


def truth(value: object, label: str) -> None:
    need(value is True, label + ': explicit true required')


def digest(value: object, length: int, label: str) -> str:
    result = text(value, label)
    need(re.fullmatch('[0-9a-f]{' + str(length) + '}', result) is not None, label + ': digest')
    return result


def timestamp(value: object, label: str) -> datetime:
    result = datetime.fromisoformat(text(value, label).replace('Z', '+00:00'))
    need(result.tzinfo is not None and result.utcoffset() is not None, label + ': timezone')
    return result


def now() -> datetime:
    return datetime.now(timezone.utc)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def read_json(path: Path, limit: int = 1048576) -> dict[str, object]:
    need(path.is_file() and path.stat().st_size <= limit, 'JSON file limit: ' + str(path))
    raw = path.read_bytes()
    need(len(raw) <= limit, 'JSON grew beyond limit')
    value: object = json.loads(raw, object_pairs_hook=unique_pairs)
    return obj(value, str(path))


def target_name(value: object) -> str:
    name = text(value, 'target')
    need(not any(c in name for c in ('\\', ':', '\n', '\r', '\0')), 'invalid target syntax')
    parts = name.split('/')
    need(all(p not in ('', '.', '..') for p in parts), 'invalid target components')
    need(not PurePosixPath(name).is_absolute(), 'absolute target')
    return name


@dataclass(frozen=True)
class Pin:
    path: Path
    size: int
    sha256: str

    @staticmethod
    def parse(value: object, label: str) -> Pin:
        row = obj(value, label)
        return Pin(Path(text(row.get('path'), label + '.path')).resolve(),
                   integer(row.get('bytes'), label + '.bytes'),
                   digest(row.get('sha256'), 64, label + '.sha256'))

    def read(self) -> bytes:
        need(self.path.is_file() and self.path.stat().st_size == self.size, 'pin size: ' + str(self.path))
        data = self.path.read_bytes()
        need(len(data) == self.size and sha(data) == self.sha256, 'pin bytes: ' + str(self.path))
        return data


@dataclass(frozen=True)
class Old:
    size: int
    sha256: str
    git_blob: str


@dataclass(frozen=True)
class Item:
    source: Pin
    target: str
    git_blob: str
    old: Old | None

    @staticmethod
    def parse(value: object) -> Item:
        row = obj(value, 'item')
        previous: Old | None = None
        need('old' in row, 'item.old missing')
        if row['old'] is not None:
            old = obj(row['old'], 'item.old')
            previous = Old(integer(old.get('bytes'), 'old.bytes'), digest(old.get('sha256'), 64, 'old.sha'),
                           digest(old.get('git_blob'), 40, 'old.oid'))
        pin = Pin(Path(text(row.get('source'), 'source')).resolve(), integer(row.get('bytes'), 'bytes'),
                  digest(row.get('sha256'), 64, 'sha256'))
        return Item(pin, target_name(row.get('target')), digest(row.get('git_blob'), 40, 'git_blob'), previous)


@dataclass(frozen=True)
class Plan:
    pin: Pin
    machine: str
    worktree: Path
    base: str
    dhead: str
    deadline: datetime
    items: tuple[Item, ...]
    accepted_count: int

    @staticmethod
    def parse(pin: Pin) -> Plan:
        data = pin.read()
        value: object = json.loads(data, object_pairs_hook=unique_pairs)
        row = obj(value, 'plan')
        need(row.get('schema') == 'xar.e04.production-publication.exact-copyplan.v1', 'plan schema')
        raw_items = row.get('items')
        need(isinstance(raw_items, list) and bool(raw_items), 'plan items')
        items: list[Item] = []
        if isinstance(raw_items, list):
            items = [Item.parse(item) for item in raw_items]
        items.append(Item(pin, target_name(row.get('plan_self_target')), blob(data), None))
        need(len({item.target.casefold() for item in items}) == len(items), 'duplicate targets')
        summary = obj(row.get('summary'), 'summary')
        formal = text(summary.get('formal'), 'formal')
        need(re.fullmatch('[1-9][0-9]*/11', formal) is not None, 'formal count')
        return Plan(pin, text(row.get('machine_id'), 'machine'), Path(text(row.get('W'), 'W')).resolve(),
                    digest(row.get('expected_W_and_remote'), 40, 'base'),
                    digest(row.get('D_readonly_expected_HEAD'), 40, 'D head'),
                    timestamp(row.get('hard_deadline_utc'), 'plan deadline'), tuple(items), int(formal.split('/')[0]))


@dataclass(frozen=True)
class Admission:
    pin: Pin
    machine: str
    worktree: Path
    droot: Path
    plan: Pin
    executor: Pin
    deadline: datetime
    ledger: str
    message: str
    base: str
    dhead: str
    override: bool
    original_deadline: datetime | None

    @staticmethod
    def parse(pin: Pin) -> Admission:
        value: object = json.loads(pin.read(), object_pairs_hook=unique_pairs)
        row = obj(value, 'admission')
        truth(row.get('admitted'), 'admitted')
        need(row.get('budget_status') == 'GREEN', 'capacity GREEN required')
        for key in ('W_copy_stage_commit_push_execution_admitted', 'Git_mutation_execution_admitted',
                    'copy_execution_admitted', 'stage_execution_admitted', 'commit_execution_admitted', 'push_execution_admitted'):
            truth(row.get(key), key)
        override = row.get('explicit_plan_deadline_override') is True
        old = timestamp(row.get('plan_hard_deadline_utc'), 'original deadline') if override else None
        return Admission(pin, text(row.get('machine_id'), 'machine'), Path(text(row.get('W'), 'W')).resolve(),
                         Path(text(row.get('D'), 'D')).resolve(), Pin.parse(row.get('exact_plan'), 'exact_plan'),
                         Pin.parse(row.get('executor'), 'executor'), timestamp(row.get('hard_deadline_utc'), 'deadline'),
                         target_name(row.get('central_ledger_target')), text(row.get('commit_message'), 'commit message'),
                         digest(row.get('expected_W_and_remote'), 40, 'cap base'),
                         digest(row.get('D_expected_HEAD'), 40, 'cap Dhead'), override, old)

    def guard(self, plan: Plan, executor: Path, current: datetime | None = None) -> None:
        self.pin.read()
        plan.pin.read()
        need((current or now()) < self.deadline, 'admission expired')
        need(self.machine == plan.machine and self.worktree == plan.worktree, 'machine/W binding')
        need(self.base == plan.base and self.dhead == plan.dhead, 'HEAD binding')
        need(self.executor.path == executor.resolve(), 'executor path binding')
        self.executor.read()
        need(self.plan == plan.pin, 'plan binding')
        if self.deadline > plan.deadline:
            need(self.override and self.original_deadline == plan.deadline, 'explicit historical plan deadline override required')
        need((current or now()) < self.deadline, 'admission expired during pin validation')


def census(root: Path) -> int:
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())


class Recorder:
    def __init__(self, root: Path, machine: str) -> None:
        self.root = root
        self.machine = machine

    def put(self, name: str, value: dict[str, Json]) -> Pin:
        need('/' not in name and '\\' not in name, 'receipt name')
        document: dict[str, Json] = {'machine_id': self.machine, 'observed_at_utc': now().isoformat(), **value}
        data = (json.dumps(document, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
        need(len(data) <= 16384, 'receipt bound')
        need(census(self.root) + len(data) <= LANE_LIMIT, 'executor lane limit')
        self.root.mkdir(parents=True, exist_ok=True)
        destination = self.root / name
        with destination.open('xb') as stream:
            stream.write(data)
        return Pin(destination.resolve(), len(data), sha(data))


def creation_filetime(process: subprocess.Popen[bytes]) -> str:
    need(os.name == 'nt', 'Windows creation identity required')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME))
    kernel.GetProcessTimes.restype = wintypes.BOOL
    handle: object = getattr(process, '_handle', None)
    need(isinstance(handle, int), 'original Popen OS handle absent')
    if not isinstance(handle, int):
        raise ValueError('original process handle')
    created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
    need(bool(kernel.GetProcessTimes(wintypes.HANDLE(handle), ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user))), 'GetProcessTimes failed')
    return str((int(created.dwHighDateTime) << 32) | int(created.dwLowDateTime))


@dataclass(frozen=True)
class Outcome:
    stdout: bytes
    stderr: bytes
    code: int
    pid: int
    created: str | None
    errors: tuple[str, ...]


def own_wait(process: subprocess.Popen[bytes], payload: bytes | None,
             birth: Callable[[subprocess.Popen[bytes]], str],
             started: Callable[[str], None]) -> Outcome:
    """Neither identity/receipt failures nor Ctrl-C can abandon this owner."""
    out, err = b'', b''
    created: str | None = None
    errors: list[str] = []
    input_attempted = False
    try:
        created = birth(process)
        started(created)
        input_attempted = True
        out, err = process.communicate(input=payload, timeout=45)
    except BaseException as exc:
        errors.append(type(exc).__name__ + ': ' + str(exc)[:256])
    finally:
        while process.returncode is None:
            try:
                send = None if input_attempted else payload
                input_attempted = True
                out, err = process.communicate(input=send, timeout=30)
            except subprocess.TimeoutExpired:
                continue
            except BaseException as exc:
                if len(errors) < 12:
                    errors.append(type(exc).__name__ + ': ' + str(exc)[:256])
                try:
                    process.wait(timeout=1)
                except BaseException:
                    pass
                try:
                    time.sleep(0.1)
                except BaseException:
                    pass
        while True:
            try:
                code = process.wait()
                break
            except BaseException as exc:
                if len(errors) < 12:
                    errors.append(type(exc).__name__ + ': ' + str(exc)[:256])
    return Outcome(out, err, code, process.pid, created, tuple(errors))


def parse_batch(data: bytes, items: tuple[Item, ...]) -> str:
    position = 0
    proof: list[str] = []
    for item in items:
        end = data.find(b'\n', position)
        need(end >= position, 'missing blob header')
        fields = data[position:end].decode('ascii').split()
        need(len(fields) == 3, 'invalid blob header')
        oid, kind, length = fields
        need(kind == 'blob' and re.fullmatch('[0-9]+', length) is not None, 'blob header type')
        size = int(length)
        need(size == item.source.size and oid == item.git_blob, 'blob header mismatch: ' + item.target)
        position = end + 1
        payload = data[position:position + size]
        position += size
        need(data[position:position + 1] == b'\n', 'blob terminator')
        position += 1
        need(sha(payload) == item.source.sha256 and blob(payload) == item.git_blob, 'blob content mismatch')
        proof.append(item.target + '\t' + oid + '\t' + sha(payload))
    need(position == len(data), 'unexpected blob tail')
    return sha(('\n'.join(proof) + '\n').encode())


def ledger_check(value: object, count: int) -> None:
    row = obj(value, 'ledger')
    need(integer(row.get('accepted_count'), 'accepted_count') == count, 'ledger count')
    history = row.get('history')
    themes = row.get('themes')
    need(isinstance(history, list) and len(history) == count, 'ledger history length')
    need(isinstance(themes, list) and len(themes) == 11, 'ledger theme length')
    if isinstance(history, list):
        for offset, event in enumerate(history, 1):
            need(integer(obj(event, 'history event').get('accepted_count'), 'event count') == offset, 'ledger history order')
    accepted = 0
    if isinstance(themes, list):
        for theme in themes:
            shots = obj(theme, 'theme').get('accepted_shots')
            need(isinstance(shots, list), 'theme shots list')
            accepted += bool(shots)
    need(accepted == count, 'ledger accepted themes')


class Executor:
    def __init__(self, cap: Admission, plan: Plan, root: Path, executable: Path) -> None:
        self.cap, self.plan, self.root, self.executable = cap, plan, root, executable
        self.records = Recorder(root, cap.machine)
        self.owned: dict[int, subprocess.Popen[bytes]] = {}
        self.counts: dict[str, int] = {'copy': 0, 'stage': 0, 'commit': 0, 'push': 0}
        self.phase = 'not_started'
        self.sequence = 0

    def guard(self) -> None:
        self.cap.guard(self.plan, self.executable)

    def git(self, root: Path, arguments: list[str]) -> list[str]:
        return ['git', '--no-optional-locks', '--no-lazy-fetch', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(root), *arguments]

    def command(self, label: str, argv: list[str], payload: bytes | None = None, mutation: bool = False) -> bytes:
        self.guard()
        self.sequence += 1
        prefix = f'{self.sequence:02d}-{label}'
        environment = os.environ.copy()
        environment.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_LAZY_FETCH='1', PYTHONDONTWRITEBYTECODE='1')
        process: subprocess.Popen[bytes] = subprocess.Popen(argv, cwd=self.cap.worktree, env=environment,
            stdin=subprocess.PIPE if payload is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        self.owned[process.pid] = process

        def started(created: str) -> None:
            self.records.put(prefix + '.CREATED.actual.json', {'argv': list(argv), 'pid': process.pid,
                'creation_filetime_decimal': created, 'mutation': mutation})

        result = own_wait(process, payload, creation_filetime, started)
        self.owned.pop(process.pid)
        self.records.put(prefix + '.ORIGINAL-WAIT.actual.json', {'argv': list(argv), 'pid': result.pid,
            'creation_filetime_decimal': result.created, 'mutation': mutation, 'actual_original_popen_wait': True,
            'returncode': result.code, 'diagnostics': list(result.errors),
            'stdout_bytes': len(result.stdout), 'stdout_sha256': sha(result.stdout),
            'stderr_bytes': len(result.stderr), 'stderr_sha256': sha(result.stderr),
            'stderr_prefix': result.stderr[:1024].decode(errors='replace')})
        need(result.code == 0 and not result.errors, 'command failed, no replay: ' + label)
        return result.stdout

    def claim_phase(self, phase: str) -> None:
        self.guard()
        need(self.counts[phase] == 0, 'mutation phase already attempted')
        self.records.put('ATTEMPT-' + phase + '.actual.json', {'phase': phase, 'attempt': 1,
            'plan_sha256': self.plan.pin.sha256, 'admission_sha256': self.cap.pin.sha256})
        self.counts[phase] = 1
        self.phase = phase

    def run(self) -> None:
        self.guard()
        need(not (self.root / 'CLAIM.actual.json').exists(), 'publication already claimed')
        for item in self.plan.items:
            payload = item.source.read()
            need(blob(payload) == item.git_blob, 'source Git blob')
            target = (self.cap.worktree / item.target).resolve()
            need(target.is_relative_to(self.cap.worktree), 'target escapes W')
        machine_out = self.command('machine', [sys.executable, '-B', str(self.cap.droot / 'tools/ck3_live_run_id.py'), 'machine'])
        need(machine_out.decode().strip() == self.cap.machine, 'actual machine mismatch')
        need(self.command('head', self.git(self.cap.worktree, ['rev-parse', 'HEAD'])).decode().strip() == self.plan.base, 'W HEAD changed')
        need(not self.command('clean', self.git(self.cap.worktree, ['status', '--porcelain=v1', '--untracked-files=all'])), 'W dirty')
        self.remote(self.plan.base, 'initial-remote')
        self.check_d()
        initial = census(self.cap.worktree)
        growth = sum(max(0, item.source.size - ((self.cap.worktree / item.target).stat().st_size if (self.cap.worktree / item.target).is_file() else 0)) for item in self.plan.items)
        need(growth <= 1048576, 'prospective W growth')
        self.records.put('CLAIM.actual.json', {'phase': 'approved_once', 'plan_sha256': self.plan.pin.sha256,
            'admission_sha256': self.cap.pin.sha256, 'items': len(self.plan.items), 'W_before_bytes': initial,
            'prospective_W_positive_upper_bytes': growth, 'maximum_each_mutation': 1})
        self.claim_phase('copy')
        for item in sorted(self.plan.items, key=lambda item: (item.target != '.gitattributes', item.target)):
            self.guard()
            target = self.cap.worktree / item.target
            if target.exists():
                need(item.old is not None, 'unexpected existing target')
                if item.old is not None:
                    old_data = target.read_bytes()
                    need(len(old_data) == item.old.size and sha(old_data) == item.old.sha256 and blob(old_data) == item.old.git_blob, 'old target drift')
            payload = item.source.read()
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('wb' if target.exists() else 'xb') as stream:
                need(stream.write(payload) == len(payload), 'short copy')
            need(target.read_bytes() == payload, 'copy readback')
        need(max(0, census(self.cap.worktree) - initial) <= 1048576, 'actual W growth')
        paths = self.root / 'approved-paths.nul'
        data = b''.join(item.target.encode() + b'\0' for item in self.plan.items)
        need(census(self.root) + len(data) <= LANE_LIMIT, 'pathspec lane cap')
        with paths.open('xb') as stream:
            stream.write(data)
        self.claim_phase('stage')
        self.command('stage', self.git(self.cap.worktree, ['add', '--sparse', '--pathspec-from-file=' + str(paths), '--pathspec-file-nul']), mutation=True)
        staged = self.command('staged-names', self.git(self.cap.worktree, ['diff', '--cached', '--name-only', '-z']))
        need(staged.endswith(b'\0') and set(staged[:-1].decode().split('\0')) == {item.target for item in self.plan.items}, 'staged path set')
        self.verify('stage-blobs', [':' + item.target for item in self.plan.items])
        self.command('diff-check', self.git(self.cap.worktree, ['diff', '--cached', '--check']))
        ledger_check(read_json(self.cap.worktree / self.cap.ledger), self.plan.accepted_count)
        message = self.root / 'commit-message.txt'
        with message.open('xb') as stream:
            stream.write((self.cap.message + '\n').encode())
        self.claim_phase('commit')
        self.command('commit', self.git(self.cap.worktree, ['commit', '--file=' + str(message)]), mutation=True)
        head = self.command('new-head', self.git(self.cap.worktree, ['rev-parse', 'HEAD'])).decode().strip()
        digest(head, 40, 'new HEAD')
        need(head != self.plan.base, 'HEAD unchanged')
        need(self.command('parent', self.git(self.cap.worktree, ['rev-parse', 'HEAD^'])).decode().strip() == self.plan.base, 'unexpected commit parent')
        self.verify('committed-blobs', [head + ':' + item.target for item in self.plan.items])
        need(not self.command('postcommit-clean', self.git(self.cap.worktree, ['status', '--porcelain=v1', '--untracked-files=all'])), 'W dirty after commit')
        self.remote(self.plan.base, 'prepush-remote')
        self.claim_phase('push')
        self.command('push', self.git(self.cap.worktree, ['push', 'origin', 'HEAD:refs/heads/master']), mutation=True)
        self.remote(head, 'final-remote')
        need(not self.command('final-clean', self.git(self.cap.worktree, ['status', '--porcelain=v1', '--untracked-files=all'])), 'final W dirty')
        self.check_d()
        need(not self.owned, 'original owners remain')
        self.phase = 'complete'
        self.records.put('FINAL.actual.json', {'status': 'PUBLISHED_EXACT', 'HEAD': head, 'remote_exact_HEAD': head,
            'base_HEAD': self.plan.base, 'counts': dict(self.counts), 'items': len(self.plan.items),
            'W_clean': True, 'D_clean': True, 'D_HEAD_unchanged': self.plan.dhead, 'owned_processes': [],
            'new_head_CI_green': None, 'new_Game_native_payment_qualification': False})

    def remote(self, head: str, label: str) -> None:
        result = self.command(label, self.git(self.cap.worktree, ['ls-remote', '--heads', 'origin', 'refs/heads/master']))
        need(result.decode().split() == [head, 'refs/heads/master'], 'remote changed; no fetch/rebase/retry')

    def check_d(self) -> None:
        need(self.command('D-head', self.git(self.cap.droot, ['rev-parse', 'HEAD'])).decode().strip() == self.plan.dhead, 'D HEAD changed')
        need(not self.command('D-clean', self.git(self.cap.droot, ['status', '--porcelain=v1', '--untracked-files=no'])), 'D tracked dirty')

    def verify(self, label: str, expressions: list[str]) -> None:
        data = self.command(label, self.git(self.cap.worktree, ['cat-file', '--batch']), ('\n'.join(expressions) + '\n').encode())
        proof = parse_batch(data, self.plan.items)
        self.records.put(label + '.PROOF.actual.json', {'items': len(self.plan.items),
            'ordered_target_oid_sha256_table_sha256': proof, 'each_bytes_oid_sha256_exact': True})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admission', type=Path, required=True)
    parser.add_argument('--admission-sha256', required=True)
    args = parser.parse_args()
    admission_path = Path(args.admission).resolve()
    need(admission_path.is_file() and admission_path.stat().st_size <= 65536, 'admission size')
    admission = Admission.parse(Pin(admission_path, admission_path.stat().st_size,
                                    digest(args.admission_sha256, 64, 'admission SHA')))
    plan = Plan.parse(admission.plan)
    executor = Executor(admission, plan, Path(__file__).resolve().parent, Path(__file__))
    try:
        executor.run()
        return 0
    except BaseException as exc:
        executor.records.put('STOPPED.actual.json', {'status': 'STOPPED_NO_MUTATION_RETRY', 'phase': executor.phase,
            'counts': dict(executor.counts), 'error': type(exc).__name__ + ': ' + str(exc)[:1024],
            'owned_process_ids': list(executor.owned), 'mutation_replayed': False})
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
