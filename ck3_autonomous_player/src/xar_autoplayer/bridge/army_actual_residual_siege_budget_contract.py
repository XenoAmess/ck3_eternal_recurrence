"""Original combined-stage operands at the natural residual continuation entry."""
from __future__ import annotations

_KEYS={'source_callback_entry_rva','source_allocator_return_rva','return_slot_basis',
       'original_siege_budget_soldiers','combined_siege_raid_budget_soldiers','capture_failure_flags'}

def normalize_residual_siege_budget_v1(value, name='siege_budget_at_allocator_v1'):
    if not isinstance(value,dict) or set(value)!=_KEYS:raise ValueError(name+' schema mismatch')
    if (type(value['source_callback_entry_rva']) is not int or value['source_callback_entry_rva']!=0x24E3410
            or type(value['source_allocator_return_rva']) is not int or value['source_allocator_return_rva']!=0x24E37B3
            or value['return_slot_basis']!='natural_residual_hook_incoming_return_address'):
        raise ValueError(name+' source/basis mismatch')
    flags=value['capture_failure_flags']
    if type(flags) is not int or not 0<=flags<=7:raise ValueError(name+' invalid failure flags')
    for key,bit in (('original_siege_budget_soldiers',2),('combined_siege_raid_budget_soldiers',4)):
        operand=value[key]
        if operand is not None and (type(operand) is not int or not -(1<<31)<=operand<(1<<31)):
            raise ValueError(name+' invalid signed operand')
        expected_missing=bool(flags&1 or flags&bit)
        if (operand is None)!=expected_missing:raise ValueError(name+' operand/failure mismatch')
    return dict(value)
