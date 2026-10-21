"""New postload qualification and RootScope; no transport, process or SDK action."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import re
from postload_models import Expected,FilePin,PostloadOwnerBinding
from postload_wire import decode_fields,numeric32,safe_integer,wire_json
import postload_owner_binding as owner

MODE='player-parent-postload-execution-once-v1'
Q_SCHEMA='xar.maintenance.parent_postload.qualification.v1'
ROOT_SCHEMA='xar.maintenance.parent_postload.root-scope.v1'
INDEX_SCHEMA='xar.e04.postload.public-source-bundle.v1'
TYPED=('postload_models.py','postload_wire.py','postload_owner_binding.py','parent_postload_contract.py')
REQUIRED=('foreign257_then_target','created_thread','foreign4096_limit','timeout','restore-fault',
 'readback-fault','continue-fault','default-off','missing-ack','bad-schema','occupied-dr','occupied-tf',
 'context-drift','fullid-drift','magic-drift','session-drift','null-context','other-player-read',
 'other-player-write','null-admission','cancel_late')
Object=dict[str,object]

def need(condition: bool,message: str) -> None:
    if not condition:raise ValueError('postload admission: '+message)

def obj(value: object,label: str='object') -> Object:
    if not isinstance(value,dict) or type(value) is not dict:raise ValueError(label+' object required')
    result: Object={}
    for key,item in value.items():
        if not isinstance(key,str) or type(key) is not str:raise ValueError(label+' string keys')
        result[key]=item
    return result

def text(value: object,label: str) -> str:
    if not isinstance(value,str) or type(value) is not str or not value:raise ValueError(label+' nonempty string')
    return value

def rows(value: object,label: str) -> list[Object]:
    if not isinstance(value,list) or type(value) is not list:raise ValueError(label+' list required')
    return [obj(item,label) for item in value]

def strings(value: object,label: str) -> list[str]:
    if not isinstance(value,list) or type(value) is not list:raise ValueError(label+' list required')
    return [text(item,label) for item in value]

def file_pin(value: object) -> FilePin:
    row=obj(value,'pin');need(set(row)=={'path','bytes','sha256'},'exact pin fields')
    digest=text(row['sha256'],'SHA');need(re.fullmatch('[0-9a-f]{64}',digest) is not None,'lowercase SHA')
    return FilePin(path=text(row['path'],'pin path'),bytes=safe_integer(row['bytes'],'pin bytes'),sha256=digest)

def pin(path: Path) -> FilePin:
    data=path.read_bytes()
    return FilePin(path=str(path.resolve()),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def verify(value: object,maximum: int=5*1024*1024,*,allow_empty: bool=False) -> Path:
    ref=file_pin(value);path=Path(ref['path']).resolve()
    need((0<=ref['bytes'] if allow_empty else 0<ref['bytes'])
        and ref['bytes']<=maximum and path.stat().st_size==ref['bytes'],'bounded pin size')
    data=path.read_bytes()
    need(len(data)==ref['bytes'] and hashlib.sha256(data).hexdigest()==ref['sha256'],'pin content changed')
    return path

def read(value: object,maximum: int=65536) -> Object:
    return obj(json.loads(verify(value,maximum).read_bytes()),'pinned JSON')

def utc(value: object) -> datetime:
    result=datetime.fromisoformat(text(value,'UTC').replace('Z','+00:00'))
    need(result.tzinfo is not None and result.utcoffset() is not None,'timezone required')
    return result

@dataclass(frozen=True)
class Qualification:
    machine: str
    observer: FilePin
    target: FilePin
    sources: tuple[FilePin,...]

def validate_qualification(value: object,*,observer: FilePin,typed_root: Path) -> Qualification:
    q=obj(value,'qualification')
    fields={'schema','status','mode','machine_id','observer_pin','target_pin','source_pins',
        'SYSTEM_receipt_pin','cold_suite_pin','Root_acceptance_pin'}
    need(set(q)==fields and q['schema']==Q_SCHEMA and q['mode']==MODE
         and q['status']=='SELECTED_POSTLOAD_EXECUTION_COLD_PASS',
         'new actual postload qualification required; entry17/pointer21/partial are ineligible')
    machine=text(q['machine_id'],'Q machine')
    observed=file_pin(q['observer_pin']);target=file_pin(q['target_pin'])
    need(observed==observer,'observer/Q exact pin');verify(observed);verify(target)
    source_list=tuple(file_pin(row) for row in rows(q['source_pins'],'Q sources'))
    by_name: dict[str,FilePin]={}
    for ref in source_list:
        name=Path(ref['path']).name
        need(name not in by_name,'ambiguous native source basename')
        by_name[name]=ref;verify(ref,1024*1024)
    need(set(TYPED)|{'cold_observer.cpp','parent_postload_execution_once.inc','parent_postload_capture.inc',
        'parent_postload_cold_target.cpp','parent_postload_cold_call.asm'}<=set(by_name),'complete postload native source scope')
    for name in TYPED:
        actual=pin(typed_root/name);qualified=by_name[name]
        need(actual['bytes']==qualified['bytes'] and actual['sha256']==qualified['sha256'],'typed peer differs from new native Q: '+name)
    system=read(q['SYSTEM_receipt_pin'],5*1024*1024)
    need(system.get('status')=='verified' and system.get('system_token_sid')=='S-1-5-18'
        and system.get('admin_token') is True and system.get('missing_requested_paths')==[], 'actual SYSTEM readback')
    verified=strings(system.get('verified_requested_paths'),'SYSTEM paths')
    files=rows(system.get('files'),'SYSTEM files')
    for ref in (observed,target):
        path=Path(ref['path']).resolve()
        need(any(Path(name).resolve()==path for name in verified),'SYSTEM exact requested path')
        need(any(Path(text(row.get('path'),'SYSTEM path')).resolve()==path
            and row.get('sha256')==ref['sha256'] for row in files),'SYSTEM exact executable SHA')
    suite=read(q['cold_suite_pin'],1024*1024)
    need(suite.get('schema')=='xar.maintenance.parent_postload.cold.suite.v1' and suite.get('mode')==MODE
        and suite.get('machine_id')==machine and suite.get('status')=='SELECTED_CASES_COMPLETED_NOT_QUALIFICATION',
        'new cold suite, not self qualification')
    cases=strings(suite.get('selected_cases'),'selected cases')
    need(cases==list(REQUIRED),'all 21 cases exactly, cancel_late last')
    case_names=[]
    for ref in rows(suite.get('cases'),'case pins'):
        case=read(ref,1024*1024)
        need(case.get('schema')=='xar.maintenance.parent_postload.cold.case.v1'
            and case.get('status')=='PASS' and case.get('machine_id')==machine,'actual postload case proof')
        case_names.append(text(case.get('case'),'case name'))
    need(case_names==cases,'all exact ordered case pins')
    acceptance=read(q['Root_acceptance_pin'],1024*1024)
    need(set(acceptance)=={'schema','mode','accepted','machine_id','observer_sha256','target_sha256',
        'source_pins','cold_suite_sha256','accepted_cases'},'exact Root acceptance')
    need(acceptance['schema']=='xar.maintenance.parent_postload.root-cold-acceptance.v1'
        and acceptance['mode']==MODE and acceptance['accepted'] is True and acceptance['machine_id']==machine,
        'independent actual Root cold acceptance required')
    need(acceptance['observer_sha256']==observed['sha256'] and acceptance['target_sha256']==target['sha256']
        and acceptance['source_pins']==q['source_pins']
        and acceptance['cold_suite_sha256']==file_pin(q['cold_suite_pin'])['sha256']
        and strings(acceptance['accepted_cases'],'accepted cases')==cases,'Root source/EXE/suite binding')
    return Qualification(machine,observed,target,source_list)

@dataclass(frozen=True)
class Scope:
    raw: Object
    machine: str
    owner: PostloadOwnerBinding
    module_base: int
    module_size: int
    cancel: str
    snapshot: FilePin
    cash: FilePin
    bundle: FilePin

def scope_value(value: object,*,now: datetime|None=None) -> Scope:
    row=decode_fields(value)
    fields={'schema','mode','machine_id','postload_execution_authorized','observed_at_utc','expires_at_utc',
        'qualification_sha256','observer_sha256','common_output','snapshot_view_pin','cash_view_pin',
        'owner_binding','module_base','module_size','foreign_limit','capture_ms','cancel_event','public_bundle_index_pin'}
    need(set(row)==fields and row['schema']==ROOT_SCHEMA and row['mode']==MODE
        and row['postload_execution_authorized'] is True,'explicit separate postload Root scope')
    issued,expires=utc(row['observed_at_utc']),utc(row['expires_at_utc'])
    current=now if now is not None else datetime.now(timezone.utc)
    need(issued<=current<expires and 0<(expires-issued).total_seconds()<=30,'Root scope expired/invalid lifetime')
    actual_owner=owner.validate(row['owner_binding'])
    module=row['module_base'];size=row['module_size']
    if not isinstance(module,int) or type(module) is not int:raise ValueError('decoded module integer')
    if not isinstance(size,int) or type(size) is not int:raise ValueError('decoded module size integer')
    need(0<module<=0x7ffffffff000 and size==102518784 and module+size<=0x7ffffffff000,'qualified game module span')
    need(numeric32(row['foreign_limit'],'foreign limit')==4096 and numeric32(row['capture_ms'],'capture ms')==30000,
        'fixed one-record 30s/4096 opportunity')
    cancel=text(row['cancel_event'],'cancel event')
    need(re.fullmatch(r'Local\\XAR_POSTLOAD_[A-Za-z0-9_]{1,100}',cancel) is not None,'run-bound cancel namespace')
    return Scope(row,text(row['machine_id'],'scope machine'),actual_owner,module,size,cancel,
        file_pin(row['snapshot_view_pin']),file_pin(row['cash_view_pin']),file_pin(row['public_bundle_index_pin']))

def packet(ref: FilePin,*,tool: str,common: Path,machine: str) -> Object:
    row=read(ref,3*1024*1024)
    for key in ('is_error','common_row_ok','common_row_error','machine_id','body','common_original','request'):
        need(key in row,'original common field missing: '+key)
    need(row['machine_id']==machine and row['is_error'] is False and row['common_row_ok'] is True
        and row['common_row_error'] is None,'actual common successful row')
    request=obj(row['request'],'request');need(request.get('tool')==tool,'actual original tool')
    arguments=obj(request.get('arguments'),'arguments')
    if tool!='ck3_take_snapshot':need(arguments.get('payment_sampling')=='query','readonly paired cash only')
    original=obj(row['common_original'],'original')
    need(original.get('pointer')=='/rows/0/result','exact original row pointer')
    reference=file_pin({key:original[key] for key in ('path','bytes','sha256')})
    path=verify(reference,3*1024*1024)
    need(path.is_relative_to(common.resolve()),'original common result outside same case output')
    saved=read(reference,3*1024*1024);saved_rows=rows(saved.get('rows'),'actual rows')
    need(len(saved_rows)==1 and saved_rows[0].get('id')==request.get('request_id')
        and saved_rows[0].get('ok') is True and saved_rows[0].get('result')==row['body'],'actual original row/body')
    return obj(row['body'],'body')

def validate_index(ref: FilePin,*,self_path: Path) -> None:
    index=read(ref)
    need(set(index)=={'schema','files','modules'} and index['schema']==INDEX_SCHEMA,'postload immutable source index')
    found=False;paths: set[Path]=set()
    for row in rows(index['files'],'source index'):
        source=file_pin(row);path=verify(source,1024*1024,allow_empty=True)
        need(path not in paths,'duplicate source path');paths.add(path)
        if path==self_path.resolve():found=True
    need(found,'executed admission helper missing from immutable source index')

def expected_from_scope(scope: Scope,snapshot: Object,cash: Object) -> Expected:
    journal=obj(cash.get('war_payment_observations_v1'),'original payment journal')
    leaf=obj(cash.get('current_raw_context_v1'),'original primary Character DTO')
    actual=owner.qualify(owner.ORDINARY,None,snapshot,journal,leaf,
        expected_game_state=scope.owner['game_state_identity_witness'],
        expected_local_player_id=scope.owner['local_player_id'])
    need(actual==scope.owner,'independent fresh owner join differs')
    return Expected(machine_id=scope.machine,synthetic=False,pid=actual['pid'],created=actual['process_create_time_100ns'],
        entry=scope.module_base+0x28f7840,post_pc=scope.module_base+0x28f785a,
        subject_field_address=actual['character']+0x1c0,character=actual['character'],
        full_id=actual['player_character_full_id'],context=actual['context'],local_player_id=actual['local_player_id'],
        game_state=actual['game_state_identity_witness'],date_raw=actual['date_raw'],absolute_day=actual['absolute_day_raw'],
        foreign_limit=4096,capture_ms=30000,admission_id='',owner_binding=actual)
