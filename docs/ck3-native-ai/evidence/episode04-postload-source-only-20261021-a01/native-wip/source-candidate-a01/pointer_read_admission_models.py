"""Typed views constructed only after runtime checks of retained JSON fields."""
from typing import TypedDict,cast
from pointer_read_wire import decode_fields,numeric32
from pointer_read_models import JsonObject,FilePin,PointerOwnerBinding,file_pin,object_value,u64

def text(value: object,name: str) -> str:
    if type(value) is not str:raise ValueError(name+' must be string')
    return cast(str,value)

def flag(value: object,name: str) -> bool:
    if type(value) is not bool:raise ValueError(name+' must be boolean')
    return cast(bool,value)

def objects(value: object,name: str) -> list[JsonObject]:
    if type(value) is not list:raise ValueError(name+' must be list')
    return [object_value(item,name) for item in value]

def strings(value: object,name: str) -> list[str]:
    if type(value) is not list:raise ValueError(name+' must be list')
    return [text(item,name) for item in value]

class RootScope(TypedDict):
    schema: str
    mode: str
    machine_id: str
    readwatch_authorized: bool
    observed_at_utc: str
    expires_at_utc: str
    qualification_sha256: str
    observer_sha256: str
    common_output: str
    snapshot_view_pin: FilePin
    cash_view_pin: FilePin
    owner_binding: PointerOwnerBinding
    module_base: int
    module_size: int
    foreign_limit: int
    capture_ms: int
    cancel_event: str

def scope_value(value: object) -> RootScope:
    from pointer_read_owner_binding import validate
    r=decode_fields(value)
    return RootScope(schema=text(r.get('schema'),'schema'),mode=text(r.get('mode'),'mode'),
        machine_id=text(r.get('machine_id'),'machine'),readwatch_authorized=flag(r.get('readwatch_authorized'),'authorization'),
        observed_at_utc=text(r.get('observed_at_utc'),'issued'),expires_at_utc=text(r.get('expires_at_utc'),'expiry'),
        qualification_sha256=text(r.get('qualification_sha256'),'Q sha'),observer_sha256=text(r.get('observer_sha256'),'observer sha'),
        common_output=text(r.get('common_output'),'common output'),snapshot_view_pin=file_pin(r.get('snapshot_view_pin')),
        cash_view_pin=file_pin(r.get('cash_view_pin')),owner_binding=validate(r.get('owner_binding')),
        module_base=u64(r.get('module_base'),'module base'),module_size=u64(r.get('module_size'),'module size'),
        foreign_limit=numeric32(r.get('foreign_limit'),'limit'),capture_ms=numeric32(r.get('capture_ms'),'capture'),cancel_event=text(r.get('cancel_event'),'cancel'))

class Qualification(TypedDict):
    schema: str
    status: str
    mode: str
    machine_id: str
    observer_pin: FilePin
    source_pins: list[FilePin]
    SYSTEM_receipt_pin: FilePin
    cold_suite_pin: FilePin
    Root_acceptance_pin: FilePin

def qualification_value(value: object) -> Qualification:
    r=object_value(value,'Q')
    return Qualification(schema=text(r.get('schema'),'schema'),status=text(r.get('status'),'status'),mode=text(r.get('mode'),'mode'),
        machine_id=text(r.get('machine_id'),'machine'),observer_pin=file_pin(r.get('observer_pin')),
        source_pins=[file_pin(p) for p in objects(r.get('source_pins'),'source pins')],
        SYSTEM_receipt_pin=file_pin(r.get('SYSTEM_receipt_pin')),cold_suite_pin=file_pin(r.get('cold_suite_pin')),
        Root_acceptance_pin=file_pin(r.get('Root_acceptance_pin')))

class ColdSuite(TypedDict):
    schema: str
    mode: str
    machine_id: str
    selected_cases: list[str]
    cases: list[FilePin]

def suite_value(value: object) -> ColdSuite:
    r=object_value(value,'cold suite')
    return ColdSuite(schema=text(r.get('schema'),'schema'),mode=text(r.get('mode'),'mode'),machine_id=text(r.get('machine_id'),'machine'),
        selected_cases=strings(r.get('selected_cases'),'selected cases'),cases=[file_pin(p) for p in objects(r.get('cases'),'cases')])

class Acceptance(TypedDict):
    mode: str
    accepted: bool
    observer_sha256: str
    source_pins: list[FilePin]
    cold_suite_sha256: str
    accepted_cases: list[str]
    machine_id: str

def acceptance_value(value: object) -> Acceptance:
    r=object_value(value,'Root acceptance')
    return Acceptance(mode=text(r.get('mode'),'mode'),accepted=flag(r.get('accepted'),'accepted'),
        observer_sha256=text(r.get('observer_sha256'),'observer sha'),source_pins=[file_pin(p) for p in objects(r.get('source_pins'),'source pins')],
        cold_suite_sha256=text(r.get('cold_suite_sha256'),'suite sha'),accepted_cases=strings(r.get('accepted_cases'),'accepted cases'),machine_id=text(r.get('machine_id'),'machine'))

class Request(TypedDict):
    request_id: str
    tool: str
    arguments: JsonObject

class OriginalRef(FilePin):
    pointer: str

class CommonPacket(TypedDict):
    machine_id: str
    is_error: bool
    common_row_ok: bool
    common_row_error: object
    body: JsonObject
    common_original: OriginalRef
    request: Request

def packet_value(value: object) -> CommonPacket:
    r=object_value(value,'common packet')
    if 'common_row_error' not in r:raise ValueError('common row error presence required; null is preserved')
    original=object_value(r.get('common_original'),'original ref')
    base=file_pin({k:original.get(k) for k in ('path','bytes','sha256')})
    ref=OriginalRef(**base,pointer=text(original.get('pointer'),'original pointer'))
    request=object_value(r.get('request'),'request')
    return CommonPacket(machine_id=text(r.get('machine_id'),'machine'),is_error=flag(r.get('is_error'),'is error'),
        common_row_ok=flag(r.get('common_row_ok'),'row ok'),common_row_error=r.get('common_row_error'),body=object_value(r.get('body'),'body'),
        common_original=ref,request=Request(request_id=text(request.get('request_id'),'request id'),tool=text(request.get('tool'),'tool'),
        arguments=object_value(request.get('arguments'),'arguments')))
