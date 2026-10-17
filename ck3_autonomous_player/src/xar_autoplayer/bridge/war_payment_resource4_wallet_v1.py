"""Optional raw resource4 gateway boundaries; no currency, military paid or cadence."""
from copy import deepcopy

KEY = 'resource4_wallet_context_v1'
ENTRY = 0x28b9950

def _payment():
    from . import war_payment_observations_v1
    return war_payment_observations_v1

def validate_context(value, record):
    p = _payment()
    from .war_payment_raw4_getter_v1 import _frame
    p.fields(value, u32='schema_version', unsigned='source_entry_rva',
             strings='resource_name maintenance_attribution balance_boundary', nested='before after')
    p.need(value['schema_version'] == 1 and value['source_entry_rva'] == ENTRY
           and value['resource_name'] == 'unknown' and value['maintenance_attribution'] == 'unclosed'
           and value['balance_boundary'] == 'whole_original_callback_entry_return',
           'resource4 gateway source/attribution was relabeled')
    p.need(record['kind'] == 1 and record['resource_kind_raw'] == 4,
           'resource4 context belongs to another original callback')
    for key in ('before', 'after'):
        _frame(value[key])

def qualified_boundaries(journal):
    """Read-only whole-callback pairs. Failure/change stays literal, never paid0."""
    p = _payment();j = journal;s = j['sampling']
    if not (j['installed'] and not j['install_failure_flags'] and j['read_complete']
            and not j['overwritten'] and not j['publication_failures'] and s['available']
            and s['capture_enabled'] and not s['busy'] and not s['active_captures']):return []
    out=[];cur=j['current_session']
    for r in j['records']:
        v=r.get(KEY)
        if v is None:continue
        validate_context(v,r)
        a,b=v['before'],v['after'];x,y=r['before'],r['after']
        if not (r['original_called'] and r['original_returned'] and not r['tls_depth_exceeded']
                and p.before(r['entry_event'],r['returned_event'])
                and p.same_session(r['session_entry'],r['session_return'])
                and p.same_session(r['session_entry'],cur)
                and r['receiver'] and r['receiver']==x['character']==y['character']
                and not a['failed_reads'] and not b['failed_reads']
                and a['character_full_id'] is not None and a['character_full_id']!=0xffffffff
                and a['character_full_id']==b['character_full_id']==x['character_id']==y['character_id']
                ==cur['player_character_full_id']
                and a['character_magic']==b['character_magic']==x['character_magic']==y['character_magic']==0x43686172
                and a['extension'] and a['extension']==b['extension']==x['character_extension']==y['character_extension']
                and a['context'] and a['context']==b['context'] and a['context']<=p.U64-0x4a0
                and a['physical_4a0_bits'] is not None and b['physical_4a0_bits'] is not None):continue
        before,after=a['physical_4a0_bits'],b['physical_4a0_bits']
        out.append(dict(journal_sequence=r['journal_sequence'],source_entry_rva=ENTRY,
            caller_return_rva=r['caller_return_rva'],resource_kind_raw=4,component_raw=r['component_raw'],
            character=r['receiver'],character_full_id=a['character_full_id'],context=a['context'],
            slot_address=a['context']+0x4a0,before_balance_bits=before,after_balance_bits=after,
            requested_amount_raw=r['amount_raw'],
            boundary_matches_requested_sub_mod64=after==((before-r['amount_raw'])&p.U64),
            entry_event=deepcopy(r['entry_event']),returned_event=deepcopy(r['returned_event']),
            session_entry=deepcopy(r['session_entry']),session_return=deepcopy(r['session_return']),
            balance_boundary='whole_original_callback_entry_return',
            resource_name='unknown',military_paid_raw=None,payer=None,cadence=None,settlement_token=None))
    return out

def consume_resource4_wallet_contexts(value, *, snapshot, machine_id):
    j=_payment().normalize_journal(value,snapshot=snapshot,machine_id=machine_id)
    return dict(journal=j,qualified_resource4_boundaries=qualified_boundaries(j),
                resource_name='unknown',maintenance_attribution='unclosed',
                evidence_scope='existing_gateway_original_callback_boundaries_only')
