"""Validated JSON boundary shared by the new background refusal protocol."""
from __future__ import annotations
import math,re,subprocess
from typing import Literal, TypeAlias, TypedDict

JsonValue: TypeAlias = None | bool | int | float | str | list['JsonValue'] | dict[str,'JsonValue']
JsonObject: TypeAlias = dict[str,JsonValue]

class FilePin(TypedDict):
    path: str
    bytes: int
    sha256: str

class ProcessGeneration(TypedDict):
    pid: int
    birth_filetime: str

class PreviousRefusalClosure(TypedDict):
    mode: Literal['previous-shared-background-supervisor-admission-refused']
    actual_process_inventory: JsonObject
    failure_cleanup: JsonObject

def json_value(value: object) -> JsonValue:
    if value is None or type(value) in (str,bool,int):
        if value is None or isinstance(value,(str,bool,int)):return value
    if type(value) is float and isinstance(value,float) and math.isfinite(value):return value
    if isinstance(value,list):return [json_value(item) for item in value]
    if isinstance(value,dict):
        out: JsonObject={}
        for key,item in value.items():
            if not isinstance(key,str):raise ValueError('JSON object key must be string')
            out[key]=json_value(item)
        return out
    raise ValueError('Value is outside the finite JSON type domain')

def json_object(value: object) -> JsonObject:
    result=json_value(value)
    if not isinstance(result,dict):raise ValueError('JSON metadata object required')
    return result

def file_pin(value: object) -> FilePin:
    row=json_object(value)
    path,size,digest=row.get('path'),row.get('bytes'),row.get('sha256')
    if not isinstance(path,str) or not path or type(size) is not int or not isinstance(size,int) or size<0:
        raise ValueError('Exact file path/byte-count required')
    if not isinstance(digest,str) or re.fullmatch('[0-9a-f]{64}',digest) is None:
        raise ValueError('Exact file SHA256 required')
    return FilePin(path=path,bytes=size,sha256=digest)

def previous_refusal(value: object) -> PreviousRefusalClosure:
    row=json_object(value)
    if row.get('mode')!='previous-shared-background-supervisor-admission-refused':raise ValueError('Refusal closure mode')
    inventory=json_object(row.get('actual_process_inventory'))
    cleanup=json_object(row.get('failure_cleanup'))
    if inventory.get('blockers')!=[]:raise ValueError('Unresolved process inventory')
    file_pin(cleanup.get('close'))
    evidence=json_object(cleanup.get('original_evidence'))
    for item in evidence.values():file_pin(item)
    if (cleanup.get('administrative_resource_admission_only') is not True
            or cleanup.get('typed_normal_exit_proven') is not False
            or cleanup.get('original_host_exit_code') is not None
            or cleanup.get('original_ck3_exit_code') is not None):
        raise ValueError('Administrative refusal cannot invent normal/game exit')
    for name in ('host_started','native_session_started','game_started','normal_close_qualified','business_pass'):
        if cleanup.get(name) is not False:raise ValueError('Refusal cannot invent host/business credit')
    return PreviousRefusalClosure(mode='previous-shared-background-supervisor-admission-refused',
        actual_process_inventory=inventory,failure_cleanup=cleanup)

def text_field(row: JsonObject, key: str) -> str:
    value=row.get(key)
    if not isinstance(value,str) or not value:raise ValueError('Nonempty string required: '+key)
    return value

def object_field(row: JsonObject, key: str) -> JsonObject:
    return json_object(row.get(key))

def strings_field(row: JsonObject, key: str) -> list[str]:
    value=row.get(key)
    if not isinstance(value,list) or not value:raise ValueError('Nonempty string list required: '+key)
    result: list[str]=[]
    for item in value:
        if not isinstance(item,str) or not item:raise ValueError('String list required: '+key)
        result.append(item)
    return result

def environment(value: object) -> dict[str,str]:
    row=json_object(value)
    result: dict[str,str]={}
    for key,item in row.items():
        if not isinstance(item,str):raise ValueError('Environment string required')
        result[key]=item
    return result

def process_handle(process: 'subprocess.Popen[bytes]') -> int:
    # The original retained Popen handle, never a reopened PID handle.
    value=getattr(process,'_handle',None)
    if not isinstance(value,int) or isinstance(value,bool) or value<=0:
        raise ValueError('Original Windows Popen handle unavailable')
    return value
