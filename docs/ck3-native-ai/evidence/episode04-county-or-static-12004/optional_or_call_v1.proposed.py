"""Offline optional DTO candidate; no runtime imports."""
from __future__ import annotations

LEGS={
 'first':(0x2C09580,0x2C096A8,'fd0a0853141ff6a35107e3ab65eef6851291d98662217dd15bacdf438edaf263'),
 'second':(0x2C09780,0x2C096B7,'a11bce0eeacba0b0577f8e6007a9b9b5f5efbbd1f42b7513c0ff3c33327b7353'),
}
_FLAGS=('hook_installed','scope_entered','scope_complete','scope_same_thread','arguments_observed')
_OPTIONAL_FLAGS=('argument_identity_matched','identity_before_after_match','returned')
_ACTUAL=('actual_native_caller_return_rva','receiver_full_id','actor_full_id','returned')
_KEYS={'schema_version','source','return_basis','leg','native_entry_rva','native_body_sha256',
       'status','unavailable_reason','call_count','parent_stage_index',*_FLAGS,*_OPTIONAL_FLAGS,
       *_ACTUAL,'additional_native_calls','inner_callee_results_observed'}

def _need(ok,why):
    if not ok:raise ValueError(why)

def _uint(value,bits):
    return type(value) is int and 0<=value<1<<bits

def _identity(value):
    return value is None or (isinstance(value,str) and value.startswith('native:')
        and value[7:].isascii() and value[7:].isdecimal() and 0<int(value[7:])<1<<64
        and str(int(value[7:]))==value[7:])

def unobserved_or_call_v1(leg):
    """Unknown observation is not zero natural calls and is never false AL."""
    _need(type(leg) is str and leg in LEGS,'unknown OR leg')
    entry,_,body=LEGS[leg]
    row=dict(schema_version=1,source='native_original_county_relation_OR_call_12004',
        return_basis='original_AL_u8',leg=leg,native_entry_rva=entry,native_body_sha256=body,
        status='unavailable',unavailable_reason='OR_observation_not_installed_or_absent',
        call_count=None,parent_stage_index=None,actual_native_caller_return_rva=None,
        receiver_full_id=None,actor_full_id=None,returned=None,
        argument_identity_matched=None,identity_before_after_match=None,
        additional_native_calls=0,inner_callee_results_observed=False,**{k:False for k in _FLAGS})
    if leg=='first':row['auxiliary_identity']=None
    return row

def normalize_optional_or_call_v1(value,*,parent_relation=None):
    """Preserve independently captured outer relation AL; do not infer an OR AL."""
    if value is None:return None
    _need(isinstance(value,dict) and type(value.get('leg')) is str and value['leg'] in LEGS,'OR leaf/leg malformed')
    leg=value['leg'];entry,caller,body=LEGS[leg]
    _need(set(value)==(_KEYS|({'auxiliary_identity'} if leg=='first' else set())),
          'strict OR leaf keys malformed; second has no auxiliary/R8 semantic')
    _need(type(value['schema_version']) is int and value['schema_version']==1
          and value['source']=='native_original_county_relation_OR_call_12004'
          and value['return_basis']=='original_AL_u8' and type(value['native_entry_rva']) is int
          and value['native_entry_rva']==entry and value['native_body_sha256']==body,
          'OR source/body/AL basis malformed')
    for key in (*_FLAGS,'inner_callee_results_observed'):
        _need(type(value[key]) is bool,'OR flags must be bool')
    _need(value['inner_callee_results_observed'] is False,'inner H/G/gate results are unobserved')
    _need(type(value['additional_native_calls']) is int and value['additional_native_calls']==0,
          'OR observation must add no native calls')
    for key in _OPTIONAL_FLAGS:
        _need(value[key] is None or type(value[key]) is bool,'OR optional flags must be bool or null')
    for key in ('call_count','receiver_full_id','actor_full_id'):
        _need(value[key] is None or _uint(value[key],32),'OR uint32 malformed')
    _need(value['parent_stage_index'] is None or (type(value['parent_stage_index']) is int
          and 0<=value['parent_stage_index']<3),'OR parent stage malformed')
    _need(value['actual_native_caller_return_rva'] is None
          or _uint(value['actual_native_caller_return_rva'],64),'OR caller width malformed')
    if leg=='first':_need(_identity(value['auxiliary_identity']),'first OR opaque auxiliary malformed')
    status=value['status']
    if status in ('available','not_called'):
        _need(all(value[k] is True for k in ('hook_installed','scope_entered','scope_complete','scope_same_thread'))
              and value['parent_stage_index'] is not None,'OR natural parent scope incomplete')
    if status=='available':
        _need(value['unavailable_reason'] is None and value['call_count']==1
              and value['actual_native_caller_return_rva']==caller
              and all(value[k] is True for k in ('arguments_observed','argument_identity_matched','identity_before_after_match'))
              and all(value[k] is not None for k in ('receiver_full_id','actor_full_id','returned')),
              'available OR requires one complete original natural call/AL')
        if leg=='first' and value['receiver_full_id']==value['actor_full_id']:
            _need(value['returned'] is False,'first OR same FullID has source-proven false return')
        if parent_relation is not None:
            _need(parent_relation.get('status')=='available'
                  and type(parent_relation.get('returned')) is bool,'actual parent relation not qualified')
            for key in ('receiver_full_id','actor_full_id'):
                _need(value[key]==parent_relation.get(key),'OR natural argument identity differs from parent')
            if leg=='first':
                _need(value['auxiliary_identity']==parent_relation.get('auxiliary_identity'),
                      'first OR natural auxiliary differs from parent')
    elif status=='not_called':
        _need(value['unavailable_reason']=='no_natural_call_in_complete_parent_scope'
              and value['call_count']==0 and value['arguments_observed'] is False
              and all(value[k] is None for k in (*_ACTUAL,'argument_identity_matched','identity_before_after_match'))
              and (leg!='first' or value['auxiliary_identity'] is None),
              'not-called requires actual complete zero-call scope, with no invented arguments/AL')
    else:
        _need(status=='unavailable' and isinstance(value['unavailable_reason'],str)
              and bool(value['unavailable_reason']),'unknown OR requires an unavailable reason')
    return dict(value)

def explain_optional_or_call_v1(value,*,parent_relation=None):
    leaf=normalize_optional_or_call_v1(value,parent_relation=parent_relation)
    outer=(parent_relation.get('returned') if isinstance(parent_relation,dict)
           and parent_relation.get('status')=='available'
           and type(parent_relation.get('returned')) is bool else None)
    out=dict(status='unknown',reason='optional_OR_call_absent',actual_or_returned=None,
             outer_relation_returned=outer,inner_callee_results=None)
    if leaf is None:return out
    out['reason']=leaf['unavailable_reason']
    if leaf['status']=='not_called':
        out.update(status='observed',reason='no_natural_call_in_complete_parent_scope')
    elif leaf['status']=='available':
        out.update(status='observed',reason='original_OR_AL_observed',actual_or_returned=leaf['returned'])
        if (type(outer) is bool and ((leaf['returned'] is True and outer is False)
                or (leaf['leg']=='second' and leaf['returned'] is False and outer is True))):
            out.update(status='unavailable',reason='source_return_contradiction')
    return out

def focused_self_check():
    for leg in LEGS:
        unknown=unobserved_or_call_v1(leg)
        _need(normalize_optional_or_call_v1(unknown)['call_count'] is None,'unknown count')
        _need(explain_optional_or_call_v1(unknown)['actual_or_returned'] is None,'unknown AL')
    _need(explain_optional_or_call_v1(None)['actual_or_returned'] is None,'absent AL')
    return {'focused_groups':1,'status':'GREEN','production_consumer_executed':False,
            'SDK_Driver_native_build_EXE_calls':0}

if __name__=='__main__':
    import json,sys
    if sys.argv[1:]!=['--self-check']:raise SystemExit('Only --self-check is supported; candidate has no runtime CLI')
    print(json.dumps(focused_self_check()))
