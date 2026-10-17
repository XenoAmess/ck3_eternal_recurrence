"""Bounded, source-specific raw payment consumer; no inferred maintenance costs."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from .nonwar_private_build import private_native_build_identity
from .version_identity import CK3_12004, require_exact_native_build

JOURNAL_KEY = 'war_payment_observations_v1'
CONTROL_KEY = 'war_payment_control_v1'
WINDOW_CONTRACT = 'same_owned_process_no_load_v1'
MODES = ('enable', 'disable', 'query')
U64 = (1 << 64) - 1


def need(condition, message):
    if not condition:
        raise ValueError('war payment ' + message)


def integer(value, bits=64, signed=False):
    low = -(1 << (bits - 1)) if signed else 0
    high = (1 << (bits - 1)) - 1 if signed else (1 << bits) - 1
    return type(value) is int and low <= value <= high


def fields(value, *, unsigned='', u32='', u8='', signed='', i32='', boolean='',
           optional_u64='', optional_u32='', optional_u8='', optional_signed='',
           optional_boolean='', nested='', strings=''):
    groups = [(unsigned, lambda x:integer(x)), (u32, lambda x:integer(x,32)),
              (u8, lambda x:integer(x,8)), (signed, lambda x:integer(x,64,True)),
              (i32, lambda x:integer(x,32,True)), (boolean, lambda x:type(x) is bool),
              (optional_u64, lambda x:x is None or integer(x)),
              (optional_u32, lambda x:x is None or integer(x,32)),
              (optional_u8, lambda x:x is None or integer(x,8)),
              (optional_signed, lambda x:x is None or integer(x,64,True)),
              (optional_boolean, lambda x:x is None or type(x) is bool),
              (strings, lambda x:type(x) is str)]
    keys = set(nested.split())
    for names, _ in groups:
        keys.update(names.split())
    need(isinstance(value, dict) and set(value) == keys, 'schema fields are malformed')
    for names, valid in groups:
        for key in names.split():
            need(valid(value[key]), key + ' has a malformed scalar')


def event(value):
    fields(value, unsigned='clock_identity sequence', optional_u32='thread_id')


def session(value):
    fields(value, u32='pid', unsigned='process_create_time_100ns connection_generation controlled_window_id game_state_identity_witness',
           optional_u64='loaded_game_epoch snapshot_revision native_date_raw',
           optional_u32='player_character_full_id absolute_day_raw', boolean='same_owned_process_no_load_window')


def frame(value):
    fields(value, unsigned='character wrapper',
           optional_u32='character_id character_magic land_id land_magic army_id army_magic requested_unit_id province_magic province_id',
           optional_u64='character_extension personal_gold_bits wrapper_balance_bits', optional_u8='army_1d4',
           boolean='capture_complete', u32='failed_reads')


def natural(value):
    fields(value, boolean='observed', u8='phase', unsigned='actual_entry_rva primary_manager game_state',
           optional_u64='session_identity date_raw', optional_u32='absolute_day_raw', nested='entry_event')
    need(value['phase'] in (0,1,2), 'natural phase is unknown to this schema')
    event(value['entry_event'])


GENERIC_CONTEXT_KEY = 'generic_wallet_context_v1'
GENERIC_CONTEXT_ENTRY_RVA = 0x28a6d10
GENERIC_CONTEXT_WALLET_RETURN_RVA = 0x28a6d7c
GENERIC_CONTEXT_VALUES = ('value_2c0', 'value_2c8', 'value_28', 'value_30')


def generic_context_snapshot(value):
    fields(value, optional_u64='context_identity_before context_identity_after',
           optional_signed='value_2c0 value_2c8 value_28 value_30',
           boolean='capture_complete context_stable', u32='failed_reads')
    input_identity, returned_identity = value['context_identity_before'], value['context_identity_after']
    stable = bool(input_identity and returned_identity and input_identity == returned_identity)
    need(value['context_stable'] == stable, 'generic context identity stability is inconsistent')
    if not input_identity:
        need(all(value[key] is None for key in GENERIC_CONTEXT_VALUES),
             'generic context has values without an input context identity')
    complete = stable and value['failed_reads'] == 0 and all(value[key] is not None for key in GENERIC_CONTEXT_VALUES)
    need(value['capture_complete'] == complete, 'generic context completeness is inconsistent')


def generic_context_trace(value):
    fields(value, unsigned='module_base',
           u32='module_image_size reported_frame_count caller_match_count',
           boolean='capture_succeeded truncated parent_in_same_image',
           optional_u64='parent_return_absolute parent_return_rva', nested='frames_absolute')
    frames = value['frames_absolute']
    need(isinstance(frames, list) and len(frames) <= 32 and all(integer(frame) and frame != 0 for frame in frames),
         'generic context parent frames are malformed')
    captured = 1 <= value['reported_frame_count'] <= 32
    need(value['capture_succeeded'] == captured
         and (len(frames) == value['reported_frame_count'] if captured else not frames),
         'generic context parent capture count is inconsistent')
    need(value['truncated'] == (captured and value['reported_frame_count'] == 32),
         'generic context parent truncation is inconsistent')
    base = value['module_base']
    known_caller = base + GENERIC_CONTEXT_WALLET_RETURN_RVA if base and base <= U64-GENERIC_CONTEXT_WALLET_RETURN_RVA else None
    matches = [index for index, frame in enumerate(frames) if known_caller is not None and frame == known_caller]
    need(value['caller_match_count'] == len(matches), 'generic context parent caller count is inconsistent')
    parent = frames[matches[0]+1] if len(matches) == 1 and matches[0]+1 < len(frames) else None
    need(value['parent_return_absolute'] == parent, 'generic context parent address is inconsistent')
    same_image = (parent is not None and bool(base) and value['module_image_size'] > GENERIC_CONTEXT_WALLET_RETURN_RVA
                  and parent >= base and parent-base < value['module_image_size'])
    need(value['parent_in_same_image'] == same_image
         and value['parent_return_rva'] == (parent-base if same_image else None),
         'generic context parent image provenance is inconsistent')


def generic_wallet_context(value, payment_record):
    """Retain raw source values and an unwind parent without attributing a cost."""
    fields(value, u32='schema_version', unsigned='source_entry_rva source_wallet_return_rva',
           strings='attribution_scope maintenance_attribution',
           optional_signed='before_computed_add_raw', optional_boolean='before_formula_matches_amount',
           boolean='context_values_stable', nested='before after parent_trace')
    need(value['schema_version'] == 1 and value['source_entry_rva'] == GENERIC_CONTEXT_ENTRY_RVA
         and value['source_wallet_return_rva'] == GENERIC_CONTEXT_WALLET_RETURN_RVA
         and value['attribution_scope'] == 'raw_source_context_and_unwind_parent_only'
         and value['maintenance_attribution'] == 'unclosed', 'generic context source or attribution scope is malformed')
    need(payment_record['kind'] == 2 and payment_record['caller_return_rva'] == GENERIC_CONTEXT_WALLET_RETURN_RVA,
         'generic context belongs to a different wallet call')
    for key in ('before', 'after'):
        generic_context_snapshot(value[key])
    generic_context_trace(value['parent_trace'])
    first, last = value['before'], value['after']
    computed = None
    if first['capture_complete']:
        raw = first['value_2c0']-first['value_2c8']-(first['value_28']+first['value_30'])
        computed = (raw+(1 << 63)) % (1 << 64)-(1 << 63)
    need(value['before_computed_add_raw'] == computed
         and value['before_formula_matches_amount'] == (computed == payment_record['amount_raw'] if computed is not None else None),
         'generic context source arithmetic is inconsistent')
    stable = (first['capture_complete'] and last['capture_complete']
              and first['context_identity_before'] == last['context_identity_before']
              and all(first[key] == last[key] for key in GENERIC_CONTEXT_VALUES))
    need(value['context_values_stable'] == stable, 'generic context values stability is inconsistent')


def record(value):
    has_generic_context = isinstance(value, dict) and GENERIC_CONTEXT_KEY in value
    fields(value, unsigned='journal_sequence receiver second_pointer caller_return_rva parent_transition_army parent_gateway_character parent_transition_caller parent_gateway_caller raw_return_bits',
           u8='kind', signed='amount_raw parent_gateway_amount',
           i32='resource_kind_raw component_raw parent_gateway_resource parent_gateway_component',
           boolean='original_called original_returned clock_thread_order_matches session_matches natural_parent_matches same_character_after same_wrapper_after personal_wrapper_matches_character source_boarding_call_chain_matches tls_depth_exceeded',
           nested='entry_event returned_event parent_transition_entry parent_gateway_entry natural_parent_metadata natural_return_metadata session_entry session_return before after'
                  + (' '+GENERIC_CONTEXT_KEY if has_generic_context else ''))
    need(value['kind'] in range(5), 'record kind is malformed')
    for key in ('entry_event','returned_event','parent_transition_entry','parent_gateway_entry'):
        event(value[key])
    for key in ('natural_parent_metadata','natural_return_metadata'):
        natural(value[key])
    for key in ('session_entry','session_return'):
        session(value[key])
    for key in ('before','after'):
        frame(value[key])
    if has_generic_context:
        generic_wallet_context(value[GENERIC_CONTEXT_KEY], value)


def valid_event(e):
    return bool(e['clock_identity'] and e['sequence'] and e['thread_id'] is not None)


def same_event(a,b):
    return valid_event(a) and valid_event(b) and a == b


def before(a,b):
    return (valid_event(a) and valid_event(b) and a['clock_identity'] == b['clock_identity']
            and a['thread_id'] == b['thread_id'] and a['sequence'] < b['sequence'])


def same_session(a,b):
    base = ('pid','process_create_time_100ns','connection_generation','player_character_full_id','loaded_game_epoch')
    if (not a['pid'] or not a['process_create_time_100ns'] or not a['connection_generation']
            or a['player_character_full_id'] is None or any(a[k] != b[k] for k in base)):
        return False
    if a['loaded_game_epoch']:
        return True
    return bool(a['same_owned_process_no_load_window'] and b['same_owned_process_no_load_window']
                and a['controlled_window_id'] and a['controlled_window_id'] == b['controlled_window_id']
                and a['game_state_identity_witness'] and a['game_state_identity_witness'] == b['game_state_identity_witness'])


def complete(r,current):
    return (r['original_called'] and r['original_returned'] and not r['tls_depth_exceeded']
            and r['before']['capture_complete'] and r['after']['capture_complete']
            and r['before']['failed_reads'] == r['after']['failed_reads'] == 0
            and before(r['entry_event'],r['returned_event'])
            and same_session(r['session_entry'],r['session_return'])
            and same_session(r['session_entry'],current))


def same_character(a,b):
    return bool(a['character'] and a['character'] == b['character']
                and a['character_id'] is not None and a['character_id'] != 0xffffffff
                and a['character_id'] == b['character_id']
                and a['character_magic'] == b['character_magic'] == 0x43686172
                and a['character_extension'] and a['character_extension'] == b['character_extension'])


def natural_matches(r,n,current):
    p,q,s = r['natural_parent_metadata'],r['natural_return_metadata'],n['metadata']
    if not (p['observed'] and q['observed'] and s['observed'] and p['phase'] == q['phase'] == s['phase'] == 2
            and p['actual_entry_rva'] == q['actual_entry_rva'] == s['actual_entry_rva'] == 0x2a9a570
            and p['primary_manager'] and p['primary_manager'] == q['primary_manager'] == s['primary_manager']
            and p['game_state'] and p['game_state'] == q['game_state'] == s['game_state']
            and same_event(p['entry_event'],q['entry_event']) and same_event(p['entry_event'],s['entry_event'])
            and before(s['entry_event'],r['entry_event']) and before(r['returned_event'],n['returned_event'])
            and n['original_called'] and n['original_returned']
            and p['date_raw'] is not None and p['date_raw'] == q['date_raw'] == s['date_raw'] == n['returned_date_raw']
            and p['absolute_day_raw'] is not None
            and p['absolute_day_raw'] == q['absolute_day_raw'] == s['absolute_day_raw'] == n['returned_absolute_day_raw']):
        return False
    if current['loaded_game_epoch']:
        return p['session_identity'] == q['session_identity'] == s['session_identity'] == current['loaded_game_epoch']
    return (current['same_owned_process_no_load_window'] and current['game_state_identity_witness'] == p['game_state']
            and p['session_identity'] is None and q['session_identity'] is None and s['session_identity'] is None)


def expected_debits(j):
    """Rejoin raw entry/return evidence; native qualification flags are not proof."""
    current,sampling,ns = j['current_session'],j['sampling'],j['natural_journal_status']
    if not (j['installed'] and not j['install_failure_flags'] and j['machine_id']
            and (current['loaded_game_epoch'] is not None or j['controlled_window_admitted'])
            and same_session(current,current) and j['read_complete'] and sampling['available']
            and sampling['capture_enabled'] and not sampling['busy'] and not sampling['active_captures']
            and not j['overwritten'] and not j['publication_failures'] and ns['read_complete']
            and not ns['overwritten_records'] and not ns['failed_appends']):
        return []
    result=[]
    for w in j['records']:
        personal,land = w['kind'] == 3,w['kind'] == 4
        a,b = w['before'],w['after']
        if not ((personal or land) and w['amount_raw'] > 0 and complete(w,current) and same_character(a,b)
                and a['character_id'] == current['player_character_full_id']
                and a['wrapper'] and a['wrapper'] == b['wrapper'] == w['receiver']
                and w['second_pointer'] == a['character']
                and a['wrapper_balance_bits'] is not None and b['wrapper_balance_bits'] is not None
                and w['caller_return_rva'] == (0x28b99b2 if personal else 0x28b9a6d)):
            continue
        if personal and (a['character_extension'] > U64-0xf8 or a['wrapper'] != a['character_extension']+0xf8):
            continue
        if land and not (a['land_id'] is not None and a['land_id'] != 0xffffffff and a['land_id'] == b['land_id']
                         and a['land_magic'] == b['land_magic'] == 0x4c616e64):
            continue
        gateways=[r for r in j['records'] if r['kind']==1 and same_event(r['entry_event'],w['parent_gateway_entry'])]
        transitions=[r for r in j['records'] if r['kind']==0 and same_event(r['entry_event'],w['parent_transition_entry'])]
        if len(gateways) != 1 or len(transitions) != 1:
            continue
        g,t = gateways[0],transitions[0]
        c,d = t['before'],t['after']
        if not (complete(g,current) and complete(t,current) and g['caller_return_rva']==0x24e8f40
                and t['caller_return_rva']==0x2a9a8c5 and same_character(g['before'],g['after'])
                and all(g['before'][k]==a[k] for k in ('character','character_id','character_extension'))
                and g['receiver']==a['character'] and g['resource_kind_raw']==(0 if personal else 3)
                and g['component_raw']==3 and g['amount_raw']==w['amount_raw']
                and all(w[dest]==g[src] for dest,src in (
                    ('parent_gateway_character','receiver'),('parent_gateway_caller','caller_return_rva'),
                    ('parent_gateway_resource','resource_kind_raw'),('parent_gateway_component','component_raw'),
                    ('parent_gateway_amount','amount_raw')))
                and w['parent_transition_army']==g['parent_transition_army']==t['receiver']
                and w['parent_transition_caller']==g['parent_transition_caller']==t['caller_return_rva']
                and same_event(g['parent_transition_entry'],t['entry_event'])
                and before(t['entry_event'],g['entry_event']) and before(g['entry_event'],w['entry_event'])
                and before(w['returned_event'],g['returned_event']) and before(g['returned_event'],t['returned_event'])
                and c['army_id'] is not None and c['army_id'] != 0xffffffff and c['army_id']==d['army_id']
                and c['army_magic'] is not None and c['army_magic']==d['army_magic']
                and c['requested_unit_id'] is not None and c['requested_unit_id']==d['requested_unit_id']
                and c['province_id'] is not None and c['province_id']==d['province_id']
                and c['province_magic']==d['province_magic']==0x50726f76 and c['army_1d4']==0):
            continue
        if not any(all(natural_matches(r,n,current) for r in (w,g,t)) for n in j['natural_parent_returns']):
            continue
        if (a['wrapper_balance_bits']-w['amount_raw']) & U64 != b['wrapper_balance_bits']:
            continue
        result.append(dict(writer_sequence=w['journal_sequence'],transition_sequence=t['journal_sequence'],
            gateway_sequence=g['journal_sequence'],account_kind=0 if personal else 3,payer_character_id=a['character_id'],
            land_id=a['land_id'] if land else None,requested_amount_raw=w['amount_raw'],
            entry_balance_bits=a['wrapper_balance_bits'],returned_balance_bits=b['wrapper_balance_bits'],
            returned_balance_matches_requested_sub=True))
    return result


def normalize_journal(value, *, snapshot: Mapping[str,object], machine_id: str):
    raw4_key = "raw_resource4_getter_v1"
    has_raw4 = isinstance(value, dict) and raw4_key in value
    fields(value, u32='schema_version steam_build_id install_failure_flags',
           boolean='installed controlled_window_admitted read_complete',
           unsigned='latest_sequence oldest_sequence overwritten publication_failures',
           strings='machine_id executable_sha256 game_version session_basis balance_boundary maintenance_attribution',
           nested='current_session sampling natural_journal_status records natural_parent_returns qualified_boarding_debits'
                  + (' '+raw4_key if has_raw4 else ''))
    need(value['schema_version']==1 and value['steam_build_id']==25734779
         and require_exact_native_build(value['game_version'],value['executable_sha256']) == CK3_12004
         and private_native_build_identity(snapshot)==CK3_12004,'journal lacks the exact .4 source')
    need(value['machine_id'] in ('',machine_id),'journal belongs to another machine')
    need(value['balance_boundary']=='whole_original_callback_entry_return' and value['maintenance_attribution']=='unclosed',
         'callback balances were promoted into maintenance attribution')
    session(value['current_session']);s=value['sampling'];ns=value['natural_journal_status']
    fields(s,boolean='available capture_enabled busy clear_completed',unsigned='epoch active_captures retained_records qualified_records')
    need(s['busy']==bool(s['active_captures']) and s['qualified_records']<=s['retained_records']
         and s['retained_records']<=512,'sampling counters are inconsistent')
    need(not s['clear_completed'] or (not s['capture_enabled'] and not s['busy'] and not s['retained_records']),
         'cleared sampling still retains evidence')
    fields(ns,boolean='read_complete',unsigned='retained_records overwritten_records failed_appends')
    need(isinstance(value['records'],list) and len(value['records'])<=512,'journal exceeds bounded record capacity')
    for r in value['records']:record(r)
    seq=[r['journal_sequence'] for r in value['records']]
    need(all(n>0 for n in seq) and seq==sorted(set(seq)),'journal retention ordinals are invalid')
    need(not seq or (0<value['oldest_sequence']<=seq[0]<=seq[-1]<=value['latest_sequence']),
         'journal sequence bounds are inconsistent')
    parents=value['natural_parent_returns']
    need(isinstance(parents,list) and len(parents)<=64,'natural journal exceeds bounded record capacity')
    for n in parents:
        fields(n,boolean='original_called original_returned',unsigned='raw_return_bits',
               optional_u64='returned_date_raw',optional_u32='returned_absolute_day_raw',nested='metadata returned_event')
        natural(n['metadata']);event(n['returned_event'])
    claims=value['qualified_boarding_debits']
    need(isinstance(claims,list) and len(claims)<=512,'qualified debit vector is malformed')
    for q in claims:
        fields(q,unsigned='writer_sequence transition_sequence gateway_sequence entry_balance_bits returned_balance_bits',
               u32='payer_character_id',i32='account_kind',signed='requested_amount_raw',optional_u32='land_id',
               boolean='returned_balance_matches_requested_sub')
    current=value['current_session']
    basis=('source_proved_epoch' if current['loaded_game_epoch'] is not None else
           'same_owned_process_no_load_window' if value['controlled_window_admitted'] else 'unqualified')
    need(value['session_basis']==basis,'session basis was relabeled')
    if value['controlled_window_admitted'] or current['loaded_game_epoch'] is not None or claims:
        actor=snapshot.get('played_character');need(isinstance(actor,Mapping),'current actor is absent')
        diagnostics=snapshot.get('diagnostics') or {}
        pid=diagnostics.get('bridge_pid');generation=diagnostics.get('connection_generation')
        need(type(pid) is int and type(generation) is int and current['pid']==pid and current['connection_generation']==generation
             and current['player_character_full_id']==actor.get('character_id')
             and current['snapshot_revision']==snapshot.get('native_revision')
             and current['native_date_raw'] is not None and type(snapshot.get('date_raw')) is int
             and (current['native_date_raw'] & 0xffffffff)==(snapshot['date_raw'] & 0xffffffff)
             and value['machine_id']==machine_id and same_session(current,current),
             'admitted journal does not match this paused process/player/frame')
    need(claims==expected_debits(value),'qualified debit vector disagrees with complete raw parent/amount/return evidence')
    if has_raw4:
        from .war_payment_raw4_getter_v1 import validate_child
        validate_child(value[raw4_key],value)
    return deepcopy(value)


def payment_request_fields(payment_sampling, payment_window_contract):
    if payment_sampling is None:
        need(payment_window_contract is None,'window contract requires explicit enable')
        return None
    need(type(payment_sampling) is str and payment_sampling in MODES,'sampling mode must be enable, disable or query')
    need(payment_window_contract == (WINDOW_CONTRACT if payment_sampling=='enable' else None),
         'enable alone requires the exact no-load window contract')
    from tools.ck3_live_run_id import current_machine_id
    result={'war_payment_sampling':payment_sampling,'war_payment_machine_id':current_machine_id()}
    if payment_sampling=='enable':result['war_payment_window_contract']=WINDOW_CONTRACT
    return result


def normalize_payment_extras(result, *, snapshot, payment_sampling):
    if JOURNAL_KEY not in result and CONTROL_KEY not in result:
        need(payment_sampling is None,'explicit observer control returned no evidence')
        return {}
    from tools.ck3_live_run_id import current_machine_id
    need(JOURNAL_KEY in result,'observer control returned no raw journal')
    output={JOURNAL_KEY:normalize_journal(result[JOURNAL_KEY],snapshot=snapshot,machine_id=current_machine_id())}
    if payment_sampling is None:
        need(CONTROL_KEY not in result,'unsolicited observer control result')
    else:
        c=result.get(CONTROL_KEY)
        fields(c,strings='requested reason',boolean='accepted')
        need(c['requested']==payment_sampling and bool(c['reason']),'control result belongs to another request')
        if c['accepted'] and payment_sampling=='enable':
            j=output[JOURNAL_KEY];s=j['sampling']
            need(c['reason'] in ('enabled_controlled_no_load_window','already_enabled')
                 and j['controlled_window_admitted'] and j['installed'] and not j['install_failure_flags']
                 and s['available'] and s['capture_enabled'] and s['epoch']>0,
                 'accepted enable lacks its actual admitted window')
        if c['accepted'] and payment_sampling=='disable':
            j=output[JOURNAL_KEY];s=j['sampling']
            need(c['reason']=='disabled' and not j['controlled_window_admitted'] and s['available']
                 and not s['capture_enabled'] and not s['busy'] and s['clear_completed'],
                 'accepted disable did not finish clearing')
        output[CONTROL_KEY]=deepcopy(c)
    return output
