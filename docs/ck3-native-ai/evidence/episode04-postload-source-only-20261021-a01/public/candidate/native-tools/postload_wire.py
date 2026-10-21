"""New-mode JSON boundary: canonical decimal u64 strings, never Number coercion."""
from typing import Mapping

U64_FIELDS=frozenset({'created','thread_created','process_create_time_100ns','connection_generation',
 'game_state_identity_witness','character','context','controlled_window_id','payment_epoch','native_revision',
 'callsite_anchor_rva','entry','post_pc','watch_address','subject_field_address','game_state','module_base','module_size',
 'RIP','RAX','RBP','RDX','RCX','R8','R9','RSP','DR6','exception_address',
 'death_before','death_after','context_before','context_after','return_before','return_after',
 'state_before','state_after','loaded_context','actual_body_calls','other_access_calls'})
VECTOR_FIELDS=frozenset({'saved_debug','armed_debug','debug','dr'})
S64_FIELDS=frozenset({'qpc'})
MAX_SAFE=(1<<53)-1


def decimal64(value: object,name: str) -> int:
    if not isinstance(value,str) or type(value) is not str:
        raise ValueError(name+' requires a canonical decimal string')
    if not value or len(value)>20 or (value!='0' and (value[0]=='0' or not '1'<=value[0]<='9')) or any(c<'0' or c>'9' for c in value):
        raise ValueError(name+' is not canonical unsigned decimal')
    number=int(value)
    if number>=(1<<64):raise ValueError(name+' exceeds u64')
    return number


def encoded64(value: object,name: str) -> str:
    if type(value) is int:
        if not isinstance(value,int) or not 0<=value<(1<<64):raise ValueError(name+' internal u64 bounds')
        return str(value)
    # Already serialized producer subtrees are preserved, but still checked.
    decimal64(value,name)
    if not isinstance(value,str):raise ValueError(name+' string required')
    return value


def decimal_signed64(value: object,name: str) -> int:
    if not isinstance(value,str) or type(value) is not str:raise ValueError(name+' signed decimal string required')
    digits=value[1:] if value.startswith('-') else value
    if not digits or len(digits)>19 or (digits!='0' and digits[0]=='0') or value=='-0' or any(c<'0' or c>'9' for c in digits):
        raise ValueError(name+' noncanonical signed decimal')
    number=int(value)
    if not -(1<<63)<=number<(1<<63):raise ValueError(name+' signed64 bounds')
    return number


def encoded_signed64(value: object,name: str) -> str:
    if isinstance(value,int) and type(value) is int:
        if not -(1<<63)<=value<(1<<63):raise ValueError(name+' internal signed64 bounds')
        return str(value)
    decimal_signed64(value,name)
    if not isinstance(value,str):raise ValueError(name+' string required')
    return value


def row_object(value: object,name: str) -> dict[str,object]:
    if not isinstance(value,dict) or type(value) is not dict:raise ValueError(name+' object required')
    result: dict[str,object]={}
    for key,item in value.items():
        if not isinstance(key,str) or type(key) is not str:raise ValueError(name+' string key required')
        result[key]=item
    return result


def decode_fields(value: object) -> dict[str,object]:
    row=row_object(value,'new pointer wire')
    result: dict[str,object]={}
    for key,item in row.items():
        if key in S64_FIELDS:result[key]=decimal_signed64(item,key)
        elif key in U64_FIELDS:result[key]=decimal64(item,key)
        elif key in VECTOR_FIELDS:
            if not isinstance(item,list) or type(item) is not list:raise ValueError(key+' vector required')
            result[key]=[decimal64(number,key) for number in item]
        elif key=='owner_binding' and item is not None:result[key]=decode_fields(item)
        else:
            if type(item) is int and isinstance(item,int) and abs(item)>MAX_SAFE:raise ValueError(key+' unsafe numeric interface')
            result[key]=item
    return result


def wire_json(value: object,key: str='') -> object:
    if key in S64_FIELDS:return encoded_signed64(value,key)
    if key in U64_FIELDS:return encoded64(value,key)
    if key in VECTOR_FIELDS:
        if not isinstance(value,list):raise ValueError(key+' vector required')
        return [encoded64(item,key) for item in value]
    if isinstance(value,dict):
        row=row_object(value,'owned output')
        return {name:wire_json(item,name) for name,item in row.items()}
    if isinstance(value,list) or isinstance(value,tuple):return [wire_json(item) for item in value]
    if type(value) is int and isinstance(value,int) and abs(value)>MAX_SAFE:raise ValueError('unsafe numeric output')
    if value is None or type(value) in (str,int,bool,float):return value
    raise ValueError('JSON scalar/list/object required')


def numeric32(value: object,name: str) -> int:
    if not isinstance(value,int) or type(value) is not int or not 0<=value<=0xffffffff:
        raise ValueError(name+' requires exact u32 numeric interface')
    return value


def safe_integer(value: object,name: str) -> int:
    if not isinstance(value,int) or type(value) is not int or not 0<=value<=MAX_SAFE:
        raise ValueError(name+' requires exact safe integer')
    return value
