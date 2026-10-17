"""Optional passive raw selector4 getter child; no currency or payment claim.

Only the containing exact-build payment normalizer admits runtime envelopes.
This module validates literal evidence and derives read-only slot comparisons.
"""
from copy import deepcopy

KEY = 'raw_resource4_getter_v1'
ENTRY = 0x28b9490
TEXT_BEGIN, TEXT_END = 0x1000, 0x43d9848


def _payment():
    from . import war_payment_observations_v1
    return war_payment_observations_v1


def _frame(f):
    p = _payment()
    p.fields(f, optional_u32='character_full_id character_magic',
             optional_u64='extension context physical_4a0_bits', u32='failed_reads')
    attempted = ['character_full_id', 'character_magic', 'extension']
    if f['extension']:
        attempted.append('context')
        if f['context']:
            attempted.append('physical_4a0_bits')
    p.need(f['failed_reads'] == sum(f[k] is None for k in attempted),
           'raw4 frame failure count is inconsistent')
    p.need((bool(f['extension']) or f['context'] is None)
           and (bool(f['extension']) and bool(f['context']) or f['physical_4a0_bits'] is None),
           'raw4 frame invented a skipped branch value')


def validate_child(v, outer):
    """Validate raw records without promoting failed/mismatched reads."""
    p = _payment()
    p.fields(v, u32='schema_version', unsigned='source_entry_rva latest_sequence oldest_sequence overwritten publication_failures',
             strings='capture_origin resource_name payment_attribution', boolean='read_complete', nested='records')
    p.need(v['schema_version'] == 1 and v['source_entry_rva'] == ENTRY
           and v['capture_origin'] == 'native_entry_detour' and v['resource_name'] == 'unknown'
           and v['payment_attribution'] == 'unclosed', 'raw4 source/attribution was relabeled')
    rows = v['records']
    p.need(isinstance(rows, list) and len(rows) <= 128, 'raw4 ring exceeds capacity')
    latest=v['latest_sequence']
    p.need(v['oldest_sequence'] == (max(1, latest-127) if latest else 0)
           and v['overwritten'] == max(0, latest-128), 'raw4 ring bounds disagree')
    seq=[]
    for r in rows:
        p.fields(r, unsigned='journal_sequence character out_pointer caller_return_absolute module_base raw_return_bits',
                 i32='raw_selector', optional_u64='caller_return_rva out64_bits', u32='output_failed_reads',
                 boolean='original_called original_returned',
                 nested='entry_event returned_event session_entry session_return natural_parent_metadata natural_return_metadata before after')
        p.need(r['raw_selector'] == 4, 'raw4 child contains a different selector')
        for key in ('entry_event','returned_event'):p.event(r[key])
        for key in ('session_entry','session_return'):p.session(r[key])
        for key in ('natural_parent_metadata','natural_return_metadata'):p.natural(r[key])
        for key in ('before','after'):_frame(r[key])
        pc,base=r['caller_return_absolute'],r['module_base']
        expected=pc-base if base and pc>=base and TEXT_BEGIN<=pc-base<TEXT_END else None
        p.need(r['caller_return_rva'] == expected, 'raw4 caller lacks exact image provenance')
        p.need(r['output_failed_reads'] == int(r['out64_bits'] is None), 'raw4 output read failure is inconsistent')
        seq.append(r['journal_sequence'])
    p.need(all(n>0 for n in seq) and seq==sorted(set(seq)), 'raw4 ordinals are malformed')
    p.need(not seq or v['oldest_sequence']<=seq[0]<=seq[-1]<=latest, 'raw4 retained ordinals exceed bounds')
    if v['read_complete']:
        p.need(len(seq)==min(latest,128) and (not seq or seq==list(range(v['oldest_sequence'],latest+1))),
               'raw4 complete ring contains missing records')
    else:p.need(not rows, 'raw4 unreadable copy exposes partial records')
    p.need(not outer['sampling']['clear_completed'] or not latest, 'raw4 survived a completed clear')
    return deepcopy(v)


def qualified_reads(normalized_journal):
    """Derive native physical/default-zero reads from an already normalized journal.

    Empty result is no qualified natural observation; it is not proof of absence.
    No amount, paid flag, resource name or economic cadence is inferred.
    """
    p=_payment();j=normalized_journal;v=j.get(KEY)
    if v is None:return []
    validate_child(v,j)
    s=j['sampling']
    if not (j['installed'] and not j['install_failure_flags'] and j['read_complete']
            and s['available'] and s['capture_enabled'] and not s['busy'] and not s['active_captures']
            and v['read_complete'] and not v['overwritten'] and not v['publication_failures']):return []
    out=[]
    for r in v['records']:
        a,b=r['before'],r['after'];cur=j['current_session']
        if not (r['original_called'] and r['original_returned'] and r['out_pointer']
                and r['raw_return_bits']==r['out_pointer'] and not r['output_failed_reads']
                and r['out64_bits'] is not None and r['caller_return_rva'] is not None
                and p.before(r['entry_event'],r['returned_event'])
                and p.same_session(r['session_entry'],r['session_return']) and p.same_session(r['session_entry'],cur)
                and a==b and not a['failed_reads'] and a['character_full_id'] is not None
                and a['character_full_id']!=0xffffffff and a['character_full_id']==cur['player_character_full_id']
                and a['character_magic']==0x43686172 and r['character']):continue
        physical=bool(a['extension'] and a['context'])
        expected=a['physical_4a0_bits'] if physical else 0
        if r['out64_bits']!=expected:continue
        bits=r['out64_bits']
        out.append(dict(journal_sequence=r['journal_sequence'],caller_return_rva=r['caller_return_rva'],
                        character_full_id=a['character_full_id'],context=a['context'],out64_bits=bits,
                        out64_signed=bits if bits<1<<63 else bits-(1<<64),
                        read_branch='physical_context_4a0' if physical else 'default_zero_missing_extension_or_context'))
    return out


def consume_raw4_getter_observations(value, *, snapshot, machine_id):
    """Public pure consumer: admit the enclosing production frame before deriving reads."""
    j=_payment().normalize_journal(value,snapshot=snapshot,machine_id=machine_id)
    return dict(journal=j,qualified_raw4_reads=qualified_reads(j),
                evidence_scope='natural_entry_raw_getter_read_only',
                resource_name='unknown',payment_attribution='unclosed')
