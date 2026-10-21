"""Shared validated boundary shapes. JSON is untrusted until converted here."""
from typing import TypedDict,cast
from pointer_read_wire import decode_fields,U64_FIELDS,numeric32,safe_integer

JsonObject=dict[str,object]

class FilePin(TypedDict):
    path: str
    bytes: int
    sha256: str

class PointerOwnerBinding(TypedDict):
    schema: str
    mode: str
    episode_projection: str
    episode_run_id: None
    original_episode_key_present: bool
    pid: int
    process_create_time_100ns: int
    connection_generation: int
    player_character_full_id: int
    local_player_id: int
    game_state_identity_witness: int
    character: int
    context: int
    controlled_window_id: int
    payment_epoch: int
    native_revision: int
    date_raw: int
    absolute_day_raw: int
    callsite_anchor_rva: int

class Expected(TypedDict):
    machine_id: str
    synthetic: bool
    pid: int
    created: int
    entry: int
    post_pc: int
    watch_address: int
    character: int
    full_id: int
    context: int
    local_player_id: int
    game_state: int
    date_raw: int
    absolute_day: int
    foreign_limit: int
    capture_ms: int
    admission_id: str
    owner_binding: PointerOwnerBinding | None

class Normalized(TypedDict):
    target_post_read_retained: bool
    target_post_read_qualified: bool
    admitted_context_unchanged: bool
    foreign_count: int
    cleanup_complete: bool
    reason: str
    window_complete: bool
    full_R08: bool
    paid_maintenance_raw: None
    payer: None
    cadence: None
    entryExact: bool
    observation_kind: str
    synthetic: bool

class RawRow(TypedDict, total=False):
    kind: str
    schema: str
    mode: str
    thread_id: int
    thread_generation: int
    thread_created: int
    RIP: int
    RAX: int
    RBP: int
    RDX: int
    RCX: int
    R8: int
    R9: int
    RSP: int
    DR6: int
    exception_address: int
    watch_address: int
    saved_debug: list[int]
    armed_debug: list[int]
    debug: list[int]
    restored_generation: bool
    reason: str
    date_before: int
    day_before: int
    eflags: int

def object_value(value: object,name: str) -> JsonObject:
    if type(value) is not dict or not all(type(k) is str for k in value):
        raise ValueError(name+' must be a JSON object with string keys')
    return cast(JsonObject,value)

def u64(value: object,name: str) -> int:
    if type(value) is not int or not 0<=value<1<<64:
        raise ValueError(name+' must be an exact unsigned integer')
    return cast(int,value)

def file_pin(value: object) -> FilePin:
    row=object_value(value,'pin')
    if set(row)!={'path','bytes','sha256'} or type(row['path']) is not str or not row['path']:
        raise ValueError('exact file pin shape')
    safe_integer(row['bytes'],'pin bytes')
    sha=row['sha256']
    if type(sha) is not str or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
        raise ValueError('exact file pin digest')
    return cast(FilePin,row)

def expected_value(value: object) -> Expected:
    row=decode_fields(value)
    if set(row)!=set(Expected.__annotations__):raise ValueError('exact expected model')
    for key in set(row)-{'machine_id','synthetic','admission_id','owner_binding'}:
        if key in U64_FIELDS:u64(row[key],key)
        else:numeric32(row[key],key)
    if type(row['machine_id']) is not str or not row['machine_id'] or type(row['synthetic']) is not bool:
        raise ValueError('expected machine/synthetic type')
    if type(row['admission_id']) is not str:raise ValueError('expected admission identifier')
    if row['owner_binding'] is not None:
        from pointer_read_owner_binding import validate
        validate(row['owner_binding'])
    return cast(Expected,row)

def raw_rows_value(value: object) -> list[RawRow]:
    if type(value) is not list or not 2<=len(value)<=4096:raise ValueError('bounded raw row list')
    numeric={'thread_id','thread_generation','thread_created','RIP','RAX','RBP','RDX','RCX','R8','R9','RSP',
        'target_record_limit','DR6','exception_address','watch_address','qpc','eflags','count','flags_before','flags_after',
        'full_id_before','full_id_after','magic_before','magic_after','death_before','death_after',
        'context_before','context_after','return_before','return_after','state_before','state_after',
        'date_before','date_after','day_before','day_after','loaded_context','capture_count','foreign_count'}
    decoded: list[JsonObject]=[]
    for item in value:
        row=decode_fields(item)
        decoded.append(row)
        if type(row.get('kind')) is not str:raise ValueError('raw kind type')
        for key in numeric & row.keys():
            if key=='qpc':
                qpc_value=row[key]
                if not isinstance(qpc_value,int) or type(qpc_value) is not int or not -(1<<63)<=qpc_value<(1<<63):raise ValueError('decoded signed QPC')
            elif key in U64_FIELDS:u64(row[key],key)
            else:numeric32(row[key],key)
        for key in ('saved_debug','armed_debug','debug'):
            if key in row:
                vector=row[key]
                if type(vector) is not list or len(vector)!=6:raise ValueError('six-register debug vector')
                for number in vector:u64(number,'debug element')
    return cast(list[RawRow],decoded)
