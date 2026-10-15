"""Exact4 original native callback budgets copied at combined writer entry."""
_KEYS={'source_callback_entry_rva','source_writer_return_rva','return_slot_basis',
    'original_supply_budget_soldiers','original_siege_budget_soldiers',
    'combined_siege_raid_budget_soldiers','derived_original_raid_budget_soldiers',
    'siege_raid_capture_complete','capture_failure_flags'}

def normalize_siege_budget_at_writer_v1(value):
    if not isinstance(value,dict) or set(value)!=_KEYS:
        raise ValueError('siege_budget_at_writer_v1 malformed schema')
    if (type(value['source_callback_entry_rva']) is not int or value['source_callback_entry_rva']!=0x24E3410
            or type(value['source_writer_return_rva']) is not int or value['source_writer_return_rva']!=0x24E377C
            or value['return_slot_basis']!='natural_writer_hook_incoming_return_address'):
        raise ValueError('siege_budget_at_writer_v1 source or return-slot basis mismatch')
    out=dict(value)
    for key in ('original_supply_budget_soldiers','original_siege_budget_soldiers',
                'combined_siege_raid_budget_soldiers','derived_original_raid_budget_soldiers'):
        raw=out[key]
        if raw is not None and (type(raw) is not int or not -(1<<31)<=raw<(1<<31)):
            raise ValueError('siege_budget_at_writer_v1 '+key+' must be optional signed int32')
    flags=out['capture_failure_flags']
    if type(flags) is not int or not 0<=flags<1<<32 or type(out['siege_raid_capture_complete']) is not bool:
        raise ValueError('siege_budget_at_writer_v1 capture status malformed')
    siege,combined=out['original_siege_budget_soldiers'],out['combined_siege_raid_budget_soldiers']
    complete=siege is not None and combined is not None
    if out['siege_raid_capture_complete']!=complete:
        raise ValueError('siege_budget_at_writer_v1 completeness differs from captured operands')
    derived=None if not complete else ((combined-siege+(1<<31))%(1<<32))-(1<<31)
    if out['derived_original_raid_budget_soldiers']!=derived:
        raise ValueError('siege_budget_at_writer_v1 raid is not native signed32 difference')
    return out
