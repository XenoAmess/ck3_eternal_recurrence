"""Typed source at a natural residual writer; no loss or whole-army inference."""
from __future__ import annotations

_KEYS={
 'parent_kind','invocation_token','native_thread_id','nesting_depth','parent_invocation_token',
 'allocator_caller_return_rva','enclosing_parent_kind','allocator_entry_rva',
 'observed_continuation_rva','requested_budget','flags_raw','request_source','army_id',
 'native_carmy_id','matching_roster_occurrence','receiver_identity_matches',
 'array_header_matches','writer_full_id_in_actual_array','source_complete','capture_failure_flags',
}
def _integer(v,label,bits=32,unsigned=False,optional=False):
    if optional and v is None:return None
    lo,hi=(0,2**bits-1) if unsigned else (-(2**(bits-1)),2**(bits-1)-1)
    if type(v) is not int or not lo<=v<=hi:raise ValueError(label+' integer width mismatch')
    return v

def normalize_actual_residual_parent_v1(value:object,name='residual_parent_context_v1')->dict:
    if not isinstance(value,dict) or set(value)!=_KEYS:raise ValueError(name+' schema mismatch')
    out=dict(value)
    for key in ('invocation_token','parent_invocation_token','allocator_caller_return_rva'):
        out[key]=_integer(value[key],name+'.'+key,64,True,key!='invocation_token')
    for key in ('parent_kind','native_thread_id','nesting_depth','enclosing_parent_kind',
                'allocator_entry_rva','observed_continuation_rva','capture_failure_flags'):
        out[key]=_integer(value[key],name+'.'+key,32,True,key=='enclosing_parent_kind')
    out['requested_budget']=_integer(value['requested_budget'],name+'.requested_budget')
    out['flags_raw']=_integer(value['flags_raw'],name+'.flags_raw',8,True)
    for key in ('army_id','native_carmy_id','matching_roster_occurrence'):
        out[key]=_integer(value[key],name+'.'+key,optional=True)
    for key in ('receiver_identity_matches','array_header_matches','writer_full_id_in_actual_array','source_complete'):
        if type(value[key]) is not bool:raise ValueError(name+'.'+key+' must be bool')
    if (out['parent_kind']!=4 or out['allocator_entry_rva']!=0x2A957E0 or
            out['observed_continuation_rva']!=0x2A957E8 or
            out['request_source'] not in {'unknown','county_entry','periodic_callback'}):
        raise ValueError(name+' source mismatch')
    if out['source_complete']:
        if (out['capture_failure_flags'] or not all(out[k] for k in
                ('invocation_token','native_thread_id','nesting_depth','receiver_identity_matches',
                 'array_header_matches','writer_full_id_in_actual_array')) or
                any(out[k] is None or out[k]==-1 for k in ('army_id','native_carmy_id')) or
                out['matching_roster_occurrence'] is None or out['matching_roster_occurrence']<0):
            raise ValueError(name+' complete source lacks actual identity/membership')
        pc=out['allocator_caller_return_rva']
        if out['request_source']=='county_entry':
            if pc!=0x24E2630 or out['flags_raw']!=0:raise ValueError(name+' county call mismatch')
        elif out['request_source']=='periodic_callback':
            if pc is None or not 0x24E3410<pc<0x24E3A3C or out['enclosing_parent_kind']!=1:
                raise ValueError(name+' periodic call mismatch')
        else:raise ValueError(name+' unknown cannot be complete')
    return out
