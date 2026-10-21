"""Validated public boundaries for one post-pointer-read window, not payment."""
from __future__ import annotations
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
from typing import Protocol, runtime_checkable
from pointer_read_models import Expected, FilePin, expected_value
from pointer_read_wire import decode_fields, wire_json

MODE = 'player-parent-pointer-read-once-v1'
SCHEMA = 'xar.maintenance.parent_pointer_read.raw.v2'
INDEX_SCHEMA = 'xar.e04.pointer-read.public-source-bundle.v2'
Object = dict[str, object]
Call = Callable[[str, str, dict[str, object]], Mapping[str, object]]
PinLookup = Callable[[str], FilePin]
CORE_NAMES = frozenset({'CMakeLists.txt','cold_observer.cpp','cold_target.cpp','parent_entry_cold_call.asm',
 'parent_entry_cold_target.cpp','parent_entry_execution_once.inc','parent_pointer_read_capture.inc',
 'parent_pointer_read_cold_call.asm','parent_pointer_read_cold_target.cpp','parent_pointer_read_once.inc',
 'pointer_read_decimal64.hpp','synthetic_write.asm','cold_runner_models.py','consume_parent_pointer_read_actual.py',
 'parent_pointer_read_contract.py','pointer_read_admission_models.py','pointer_read_models.py',
 'pointer_read_owner_binding.py','pointer_read_wire.py','prepare_parent_pointer_read_admission.py','run_parent_pointer_read_cold.py'})


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def object_value(value: object, label: str = 'object') -> Object:
    if not isinstance(value, dict) or type(value) is not dict:
        raise ValueError(label + ': JSON object required')
    result: Object = {}
    for key, item in value.items():
        if not isinstance(key, str) or type(key) is not str:
            raise ValueError(label + ': string key required')
        result[key] = item
    return result


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or type(value) is not str or not value:
        raise ValueError(label + ': nonempty text required')
    return value


def number(value: object, label: str, maximum: int = 0xffffffff, minimum: int = 0) -> int:
    if not isinstance(value, int) or type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(label + ': exact bounded integer required')
    return value


def flag(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(label + ': exact boolean required')
    return value is True


def digest(value: object, label: str) -> str:
    result = text(value, label)
    need(re.fullmatch('[0-9a-f]{64}', result) is not None, label + ': SHA256')
    return result


def file_pin(value: object) -> FilePin:
    row = object_value(value, 'file pin')
    need(set(row) == {'path','bytes','sha256'}, 'Exact file pin keys')
    return FilePin(path=text(row.get('path'),'pin path'), bytes=number(row.get('bytes'),'pin bytes',(1<<53)-1),
                   sha256=digest(row.get('sha256'),'pin SHA'))


def pin(path: Path) -> FilePin:
    data = path.read_bytes()
    return FilePin(path=str(path.resolve()),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def read_pin(value: FilePin, maximum: int = 65536) -> Object:
    ref = file_pin(value)
    path = Path(ref['path'])
    need(0 < ref['bytes'] <= maximum and path.stat().st_size == ref['bytes'], 'Bounded exact pinned input')
    data = path.read_bytes()
    need(len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'], 'Pinned input changed')
    decoded: object = json.loads(data)
    return object_value(decoded, 'pinned JSON')


def utc(value: object, label: str) -> datetime:
    result = datetime.fromisoformat(text(value,label).replace('Z','+00:00'))
    need(result.tzinfo is not None and result.utcoffset() is not None,label + ': timezone')
    return result


@dataclass(frozen=True)
class Settings:
    bundle_index_pin: FilePin
    qualification_pin: FilePin
    observer_pin: FilePin
    root_scope_path: Path
    actor_id: int
    expected_start_date_raw: int
    parent_tools: Path
    prefix: str
    deadline: datetime
    payment_enable_once_authorized: bool
    natural_phase_enable_once_authorized: bool

    @staticmethod
    def parse(context: Mapping[str, object]) -> Settings:
        inputs = object_value(context.get('case_inputs'),'case inputs')
        row = object_value(inputs.get('r08_parent_pointer_read_one_day'),'pointer settings')
        fields = {'bundle_index_pin','qualification_pin','observer_pin','root_scope_path','actor_id',
            'expected_start_date_raw','parent_tools','prefix','deadline_utc',
            'payment_enable_once_authorized','natural_phase_enable_once_authorized'}
        need(set(row) == fields,'Exact pointer settings keys')
        prefix = text(row['prefix'],'prefix')
        need(re.fullmatch(r'r08-pointer-[A-Za-z0-9_-]{1,31}',prefix) is not None,'Bounded request prefix')
        return Settings(file_pin(row['bundle_index_pin']),file_pin(row['qualification_pin']),file_pin(row['observer_pin']),
            Path(text(row['root_scope_path'],'scope path')),number(row['actor_id'],'actor',minimum=1),
            number(row['expected_start_date_raw'],'date',0xffffffff-24,1),Path(text(row['parent_tools'],'tools')).resolve(),
            prefix,utc(row['deadline_utc'],'deadline'),flag(row['payment_enable_once_authorized'],'payment authorization'),
            flag(row['natural_phase_enable_once_authorized'],'natural phase authorization'))

    def budget(self) -> None:
        need((self.deadline-datetime.now(timezone.utc)).total_seconds() >= 1050,
             '900s original close +120s cleanup +30s observation reserve required')


@dataclass(frozen=True)
class Bundle:
    files: dict[Path, FilePin]
    modules: dict[str, Path]

    @staticmethod
    def parse(ref: FilePin) -> Bundle:
        value = read_pin(ref)
        need(set(value) == {'schema','files','modules'} and value['schema'] == INDEX_SCHEMA,'Pointer bundle schema')
        rows = value['files']
        need(isinstance(rows,list) and bool(rows),'Explicit source pins required')
        files: dict[Path,FilePin] = {}
        if isinstance(rows,list):
            for raw in rows:
                item = file_pin(raw)
                path = Path(item['path']).resolve()
                need(path not in files,'Duplicate source path')
                files[path] = item
        modules = {name:Path(text(path,'module path')).resolve() for name,path in object_value(value['modules'],'modules').items()}
        for name,path in modules.items():
            need(path in files and path.name == name + '.py','Module lacks exact source pin')
        return Bundle(files,modules)

    def verify(self) -> None:
        for path,ref in self.files.items():
            need(path.is_file() and path.stat().st_size == ref['bytes'] <= 1048576,'Bounded source peer')
            need(pin(path) == ref,'Source peer content changed: ' + str(path))

    def tools(self, root: Path) -> None:
        for name in CORE_NAMES:
            path = (root/name).resolve()
            need(path in self.files and pin(path) == self.files[path],'Executed tool not bound to index: '+name)


@dataclass(frozen=True)
class Binding:
    raw: Object
    expected: Expected
    expected_wire: Object
    root_scope_sha256: str

    @staticmethod
    def parse(value: object) -> Binding:
        row = object_value(value,'binding')
        need(row.get('schema') == 'xar.maintenance.parent_pointer_read.binding.v2','Raw v2 binding required')
        need(row.get('prepared_only') is True,'Prepared role required')
        wire = object_value(row.get('expected'),'expected wire')
        expected = expected_value(wire)
        need(row.get('machine_id') == expected['machine_id'],'Binding machine differs')
        return Binding(row,expected,wire,digest(row.get('root_scope_sha256'),'scope SHA'))


@dataclass(frozen=True)
class Ready:
    raw: Object
    count: int

    @staticmethod
    def parse(value: object) -> Ready:
        row = object_value(value,'READY')
        need(set(row) == {'ready','mode','armed_thread_count','census_complete'},'Actual native READY four-field schema')
        need(row['ready'] is True and row['census_complete'] is True and row['mode'] == MODE,'Complete pointer READY required')
        return Ready(row,number(row['armed_thread_count'],'armed threads',256,1))


@dataclass(frozen=True)
class Snapshot:
    raw: Object
    date: int
    actor: int
    pid: int
    generation: int
    episode_present: bool

    @staticmethod
    def parse(value: object, actor: int) -> Snapshot:
        row = object_value(value,'snapshot')
        played = object_value(row.get('played_character'),'played character')
        diag = object_value(row.get('diagnostics'),'snapshot diagnostics')
        need(row.get('episode_projection') == 'native_campaign' and row.get('episode_run_id') is None
             and row.get('map_ready') is True and row.get('paused') is True,'Paused ordinary native map required')
        actual = number(played.get('character_id'),'snapshot actor',minimum=1)
        need(actual == actor,'Snapshot owner differs')
        return Snapshot(row,number(row.get('date_raw'),'date',minimum=1),actual,
            number(diag.get('bridge_pid'),'native PID',minimum=1),
            number(diag.get('connection_generation'),'generation',(1<<53)-1,1),'episode_run_id' in row)


@dataclass(frozen=True)
class Collected:
    raw: Object
    before: FilePin
    cash: FilePin
    receipt: FilePin
    actor: int
    date: int
    created: int

    @staticmethod
    def parse(value: object, machine: str) -> Collected:
        row = object_value(value,'same-client collection')
        expected = object_value(row.get('expected'),'collected expected')
        need(expected.get('machine') == machine and row.get('observer_started') is False
             and number(row.get('sampling_actions'),'sampling action count') == 0,'Original collection role/machine')
        # The existing Common producer exposes a Python integer. Preserve its
        # original receipt, validate that exact legacy value, then use wire_json
        # when projecting it into this new mode's decimal-string boundary.
        created = number(expected.get('created'),'legacy retained creation',(1<<64)-1,1)
        return Collected(row,file_pin(row.get('before_response')),file_pin(row.get('cash_response')),
            file_pin(row.get('receipt')),number(expected.get('character_id'),'collected actor',minimum=1),
            number(expected.get('date'),'collected date',minimum=1),created)


@runtime_checkable
class SelectionLike(Protocol):
    @property
    def locations(self) -> Mapping[str, object]: ...


@runtime_checkable
class PublicClient(Protocol):
    output: Path
    selection: SelectionLike
    def guard(self) -> None: ...
    def checkpoint(self, name: str, value: Mapping[str,object]) -> object: ...
    def normal_close(self, disposition: str) -> object: ...


def client_value(value: object) -> PublicClient:
    if not isinstance(value,PublicClient) or not isinstance(value.output,Path) or not isinstance(value.selection,SelectionLike):
        raise ValueError('Original public CaseClient interface unavailable')
    return value


def output_json(value: object) -> bytes:
    return (json.dumps(wire_json(value),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def decoded(value: object) -> Object:
    return decode_fields(value)
